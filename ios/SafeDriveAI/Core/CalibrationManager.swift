import Foundation
import simd

/// Learns what "alert and looking at the road" means for this driver at this
/// phone mount, over ~10 seconds. Every detection threshold downstream is
/// relative to these values — nothing about the face is hardcoded.
///
/// Captured baseline:
/// - open-eye aperture (bottom 10 % of samples discarded as blinks)
/// - neutral head yaw & pitch
/// - neutral gaze offset
///
/// Persists to UserDefaults and reloads on launch.
final class CalibrationManager: ObservableObject {
    static let durationSeconds: Double = 10

    struct Baseline: Codable, Equatable {
        let openEyeAperture: Float
        let neutralYaw: Float
        let neutralPitch: Float
        let neutralGazeX: Float
        let neutralGazeY: Float
    }

    @Published private(set) var baseline: Baseline?
    @Published private(set) var isCalibrating = false
    @Published private(set) var progress: Double = 0
    /// Samples are only accepted while a face is steadily detected; the
    /// countdown pauses otherwise so a bad calibration can't complete.
    @Published private(set) var isFaceSteady = false

    var isCalibrated: Bool { baseline != nil }

    private var apertureSamples: [Float] = []
    private var yawSamples: [Float] = []
    private var pitchSamples: [Float] = []
    private var gazeSamples: [SIMD2<Float>] = []
    private var collectedMs: Double = 0
    private var lastSampleMs: Int64?

    private let defaults: UserDefaults
    private static let storageKey = "calibration.baseline.v1"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let data = defaults.data(forKey: Self.storageKey),
           let saved = try? JSONDecoder().decode(Baseline.self, from: data) {
            baseline = saved
        }
    }

    // MARK: Session

    func begin() {
        apertureSamples.removeAll()
        yawSamples.removeAll()
        pitchSamples.removeAll()
        gazeSamples.removeAll()
        collectedMs = 0
        lastSampleMs = nil
        progress = 0
        isCalibrating = true
    }

    func cancel() {
        isCalibrating = false
        progress = 0
    }

    /// Feed each frame during calibration. Returns true when complete.
    @discardableResult
    func ingest(_ snapshot: FaceSnapshot) -> Bool {
        guard isCalibrating else { return false }

        guard snapshot.faceDetected else {
            isFaceSteady = false
            lastSampleMs = nil // pause the clock until the face returns
            return false
        }
        isFaceSteady = true

        if let last = lastSampleMs {
            collectedMs += Double(snapshot.timestampMs - last)
        }
        lastSampleMs = snapshot.timestampMs

        apertureSamples.append(snapshot.eyeOpenness)
        yawSamples.append(snapshot.yaw)
        pitchSamples.append(snapshot.pitch)
        if let gaze = snapshot.gaze { gazeSamples.append(gaze) }

        progress = min(collectedMs / (Self.durationSeconds * 1000), 1)
        guard progress >= 1, apertureSamples.count >= 30 else { return false }

        finish()
        return true
    }

    private func finish() {
        isCalibrating = false

        // Discard the lowest 10 % of aperture samples — blinks would drag the
        // open-eye average down and produce an oversensitive threshold.
        let sorted = apertureSamples.sorted()
        let open = sorted.dropFirst(sorted.count / 10)
        let openMean = open.reduce(0, +) / Float(open.count)

        let gazeMean = gazeSamples.isEmpty
            ? SIMD2<Float>.zero
            : gazeSamples.reduce(.zero, +) / Float(gazeSamples.count)

        let result = Baseline(
            openEyeAperture: openMean,
            neutralYaw: mean(yawSamples),
            neutralPitch: mean(pitchSamples),
            neutralGazeX: gazeMean.x,
            neutralGazeY: gazeMean.y
        )
        baseline = result
        if let data = try? JSONEncoder().encode(result) {
            defaults.set(data, forKey: Self.storageKey)
        }
    }

    func reset() {
        baseline = nil
        defaults.removeObject(forKey: Self.storageKey)
    }

    private func mean(_ values: [Float]) -> Float {
        values.isEmpty ? 0 : values.reduce(0, +) / Float(values.count)
    }
}
