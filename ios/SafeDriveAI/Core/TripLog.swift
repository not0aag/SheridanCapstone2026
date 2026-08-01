import Foundation

/// One completed monitoring session — what actually happened, not raw
/// per-frame data. Persisted so a driver can see their history across
/// relaunches, same as a fitness app keeps past workouts.
struct TripSummary: Codable, Identifiable, Equatable {
    let id: Int
    let startedAt: Date
    let endedAt: Date
    let drowsyAlertCount: Int
    let distractedAlertCount: Int
    let averagePerclos: Double
    let averageOffRoadRate: Double
    /// 0...100. Starts at 100, loses more for a drowsy alert than a
    /// distraction alert — reflects that a microsleep is a more severe
    /// event than a moment of looking away.
    let safetyScore: Int

    var duration: TimeInterval { endedAt.timeIntervalSince(startedAt) }
}

/// Records what happens during a monitoring session and keeps a persisted
/// history of past trips. Purely observational — reads the same
/// `driverState`/`perclos`/`offRoadRate` values DriverMonitor already
/// publishes every frame; never feeds back into a detection decision.
final class TripLog: ObservableObject {
    /// Newest first.
    @Published private(set) var trips: [TripSummary]

    /// Alerts raised so far in the trip currently in progress, for the live
    /// "Events" readout on the monitoring screen. Purely a display mirror of
    /// the counts already being accumulated below — never read by a
    /// detection decision, and reset by `startTrip()`.
    @Published private(set) var currentTripAlerts = 0

    private let defaults: UserDefaults
    private static let tripsKey = "trip.log.v1"
    private static let nextIdKey = "trip.log.nextId.v1"

    private var currentStart: Date?
    private var lastState: DriverState = .safe
    private var drowsyCount = 0
    private var distractedCount = 0
    private var perclosSamples: [Double] = []
    private var offRoadSamples: [Double] = []

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let data = defaults.data(forKey: Self.tripsKey),
           let saved = try? JSONDecoder().decode([TripSummary].self, from: data) {
            trips = saved
        } else {
            trips = []
        }
    }

    // MARK: Aggregate stats — a real driver's trend over time, not a judge-only view

    var totalTrips: Int { trips.count }
    var totalDrivingTime: TimeInterval { trips.reduce(0) { $0 + $1.duration } }
    var overallAlertRate: Double {
        guard !trips.isEmpty else { return 0 }
        let totalAlerts = trips.reduce(0) { $0 + $1.drowsyAlertCount + $1.distractedAlertCount }
        return Double(totalAlerts) / Double(trips.count)
    }

    // MARK: Session lifecycle

    func startTrip() {
        currentStart = .now
        lastState = .safe
        drowsyCount = 0
        distractedCount = 0
        currentTripAlerts = 0
        perclosSamples = []
        offRoadSamples = []
    }

    /// Call once per assessment while actively monitoring (not while paused
    /// below the speed threshold). Counts a new alert only on the
    /// transition into drowsy/distracted, not every frame it continues to hold.
    func ingest(state: DriverState, perclos: Double, offRoadRate: Double) {
        guard currentStart != nil else { return }
        if state != lastState {
            switch state {
            case .drowsy: drowsyCount += 1; currentTripAlerts += 1
            case .distracted: distractedCount += 1; currentTripAlerts += 1
            case .safe: break
            }
        }
        lastState = state
        perclosSamples.append(perclos)
        offRoadSamples.append(offRoadRate)
    }

    /// Finalizes and persists the current trip. Returns nil if no trip was
    /// in progress (e.g. stopMonitoring called without ever starting one).
    @discardableResult
    func endTrip() -> TripSummary? {
        guard let start = currentStart else { return nil }
        defer { currentStart = nil }

        let summary = TripSummary(
            id: nextId(),
            startedAt: start,
            endedAt: .now,
            drowsyAlertCount: drowsyCount,
            distractedAlertCount: distractedCount,
            averagePerclos: average(perclosSamples),
            averageOffRoadRate: average(offRoadSamples),
            safetyScore: Self.safetyScore(drowsy: drowsyCount, distracted: distractedCount)
        )
        trips.insert(summary, at: 0)
        persist()
        return summary
    }

    func deleteTrip(id: Int) {
        trips.removeAll { $0.id == id }
        persist()
    }

    /// Starts at 100. A drowsy alert (a microsleep actually happened) costs
    /// more than a distraction alert (looked away, caught in time).
    static func safetyScore(drowsy: Int, distracted: Int) -> Int {
        max(0, 100 - drowsy * 15 - distracted * 10)
    }

    private func average(_ values: [Double]) -> Double {
        values.isEmpty ? 0 : values.reduce(0, +) / Double(values.count)
    }

    private func nextId() -> Int {
        let next = defaults.object(forKey: Self.nextIdKey) as? Int ?? 1
        defaults.set(next + 1, forKey: Self.nextIdKey)
        return next
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(trips) {
            defaults.set(data, forKey: Self.tripsKey)
        }
    }
}
