import Foundation
import simd

enum DriverState: Equatable {
    case safe
    case drowsy
    case distracted
}

/// Pure, frameworkless decision logic. Feed it FaceSnapshots + the calibrated
/// baseline + current thresholds; it returns an Assessment. Fully unit-testable
/// with synthetic data — no camera required.
///
/// ## Signal harmony rules (the core design)
///
/// No single instantaneous signal can raise an alert. Every danger state needs
/// multiple kinds of evidence AND persistence over a time window:
///
/// DROWSY requires BOTH, over a rolling 5 s window:
///   1. PERCLOS — fraction of time the eyes are closed — above threshold, AND
///   2. at least one *sustained* closure ≥ 500 ms (a microsleep signature).
///   Normal blinking produces neither: blinks are ~150 ms and PERCLOS from
///   blinking sits near 5–10 %. Both conditions together mean "eyes are closed
///   often AND for long stretches".
///
/// DISTRACTED requires agreement between head pose and gaze, sustained over a
/// rolling 2.5 s window (> 65 % of frames off-road):
///   - head deviated + gaze deviated            → off-road (both agree)
///   - head deviated + pupils not visible       → off-road (pupils vanish
///     exactly when the eyes leave the camera — corroboration, not absence)
///   - head deviated + gaze still readable & normal → NOT off-road
///   - gaze deviated + head straight            → NOT off-road (glance)
///   - face missing > 700 ms continuously       → off-road (a calibrated,
///     forward-facing driver is always detectable; sustained absence means
///     they turned fully away — brief tracking dropouts are ignored)
///
/// A mirror check (~1 s) fails the 65 %-of-2.5 s persistence test. A quick
/// glance at the radio fails both the head test and persistence.
///
/// Hysteresis: alerts clear at ~70 % of the trigger level, so the state can't
/// flutter on the boundary. Monitoring continues seamlessly after every alert.
final class DetectionEngine {
    struct Thresholds {
        var perclos: Double            // e.g. 0.325
        var headDeviationRad: Float    // e.g. 0.37 (~21°)
        var gazeDeviation: Float       // fraction of eye width, e.g. 0.23
    }

    struct Assessment: Equatable {
        var state: DriverState
        var perclos: Double        // 0...1, for the live UI
        var offRoadRate: Double    // 0...1, for the live UI
        var ready: Bool            // windows filled; alerts armed
    }

    // Window geometry (time-based — device frame rate must not matter).
    static let drowsyWindowMs: Int64 = 5000
    static let microsleepMs: Int64 = 500
    static let distractionWindowMs: Int64 = 2500
    static let offRoadRateThreshold = 0.65
    static let faceLostGraceMs: Int64 = 700
    /// Eyes count as closed below this fraction of the calibrated open aperture.
    static let closureFactor: Float = 0.70
    /// Alerts clear at this fraction of their trigger threshold (hysteresis).
    static let clearFraction = 0.70

    private struct Sample {
        let tMs: Int64
        let eyesClosed: Bool
        let offRoad: Bool
    }

    private var samples: [Sample] = []
    private var firstSampleMs: Int64?
    private var faceLostSinceMs: Int64?
    private var currentState: DriverState = .safe

    func reset() {
        samples.removeAll()
        firstSampleMs = nil
        faceLostSinceMs = nil
        currentState = .safe
    }

    func ingest(
        _ snapshot: FaceSnapshot,
        baseline: CalibrationManager.Baseline,
        thresholds: Thresholds
    ) -> Assessment {
        let t = snapshot.timestampMs
        if firstSampleMs == nil { firstSampleMs = t }

        samples.append(makeSample(snapshot, baseline: baseline, thresholds: thresholds))

        // Time-based pruning to the longest window we track.
        let cutoff = t - Self.drowsyWindowMs
        samples.removeAll { $0.tMs < cutoff }

        // Don't arm alerts until a full drowsiness window of data exists.
        let ready = t - firstSampleMs! >= Self.drowsyWindowMs

        let perclos = fraction(of: samples, matching: \.eyesClosed)
        let (maxClosureMs, _) = longestRun(of: samples, matching: \.eyesClosed)

        let distractionSamples = samples.filter { $0.tMs >= t - Self.distractionWindowMs }
        let offRoadRate = fraction(of: distractionSamples, matching: \.offRoad)

        currentState = nextState(
            ready: ready,
            perclos: perclos,
            maxClosureMs: maxClosureMs,
            offRoadRate: offRoadRate,
            thresholds: thresholds
        )
        return Assessment(state: currentState, perclos: perclos, offRoadRate: offRoadRate, ready: ready)
    }

    // MARK: Per-frame signal fusion

    private func makeSample(
        _ s: FaceSnapshot,
        baseline: CalibrationManager.Baseline,
        thresholds: Thresholds
    ) -> Sample {
        guard s.faceDetected else {
            if faceLostSinceMs == nil { faceLostSinceMs = s.timestampMs }
            let lostLongEnough = s.timestampMs - faceLostSinceMs! >= Self.faceLostGraceMs
            // Eyes unknown while face is lost — never count that as "closed";
            // drowsiness needs positive evidence.
            return Sample(tMs: s.timestampMs, eyesClosed: false, offRoad: lostLongEnough)
        }
        faceLostSinceMs = nil

        let closedThreshold = baseline.openEyeAperture * Self.closureFactor
        let eyesClosed = s.eyeOpenness < closedThreshold

        let headDelta = SIMD2<Float>(s.yaw - baseline.neutralYaw, s.pitch - baseline.neutralPitch)
        let headDeviated = simd_length(headDelta) > thresholds.headDeviationRad

        let offRoad: Bool
        if headDeviated {
            if let gaze = s.gaze, !eyesClosed {
                // Head turned but pupils readable: require gaze to agree.
                let gazeDelta = gaze - SIMD2<Float>(baseline.neutralGazeX, baseline.neutralGazeY)
                offRoad = simd_length(gazeDelta) > thresholds.gazeDeviation
            } else {
                // Pupils not visible while head is turned — corroborates that
                // the eyes have left the camera's view of the road position.
                offRoad = true
            }
        } else {
            // Head forward: gaze alone never counts (glances are normal, and
            // no single signal may trigger an alert on its own).
            offRoad = false
        }
        return Sample(tMs: s.timestampMs, eyesClosed: eyesClosed, offRoad: offRoad)
    }

    // MARK: State machine with hysteresis

    private func nextState(
        ready: Bool,
        perclos: Double,
        maxClosureMs: Int64,
        offRoadRate: Double,
        thresholds: Thresholds
    ) -> DriverState {
        guard ready else { return .safe }

        let drowsyTriggered = perclos > thresholds.perclos && maxClosureMs >= Self.microsleepMs
        let drowsyHolds = perclos > thresholds.perclos * Self.clearFraction
        let distractedTriggered = offRoadRate > Self.offRoadRateThreshold
        let distractedHolds = offRoadRate > Self.offRoadRateThreshold * Self.clearFraction

        switch currentState {
        case .drowsy:
            if drowsyHolds { return .drowsy }
        case .distracted:
            if drowsyTriggered { return .drowsy } // drowsiness outranks
            if distractedHolds { return .distracted }
        case .safe:
            break
        }

        if drowsyTriggered { return .drowsy }
        if distractedTriggered { return .distracted }
        return .safe
    }

    // MARK: Window math

    private func fraction(of samples: [Sample], matching key: KeyPath<Sample, Bool>) -> Double {
        guard !samples.isEmpty else { return 0 }
        return Double(samples.filter { $0[keyPath: key] }.count) / Double(samples.count)
    }

    /// Longest continuous run (in ms) where `key` is true.
    private func longestRun(of samples: [Sample], matching key: KeyPath<Sample, Bool>) -> (Int64, Int) {
        var best: Int64 = 0, bestCount = 0
        var run: (startMs: Int64, count: Int)?
        for sample in samples {
            if sample[keyPath: key] {
                let started = run ?? (startMs: sample.tMs, count: 0)
                let current = (startMs: started.startMs, count: started.count + 1)
                run = current
                let length = sample.tMs - current.startMs
                if length > best { best = length; bestCount = current.count }
            } else {
                run = nil
            }
        }
        return (best, bestCount)
    }
}
