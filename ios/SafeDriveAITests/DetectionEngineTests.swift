import XCTest
import simd
@testable import SafeDriveAI

final class DetectionEngineTests: XCTestCase {
    private let baseline = CalibrationManager.Baseline(
        openEyeAperture: 0.30,
        neutralYaw: 0.10,       // deliberately non-zero: off-center mount
        neutralPitch: -0.05,
        neutralGazeX: 0.02,
        neutralGazeY: 0.01
    )
    private let thresholds = DetectionEngine.Thresholds(
        perclos: 0.325,
        headDeviationRad: 0.37,
        gazeDeviation: 0.23
    )

    /// Synthesizes a frame relative to the calibrated baseline.
    private func snapshot(
        t: Int64,
        eyesOpen: Bool = true,
        yawDelta: Float = 0,
        pitchDelta: Float = 0,
        gazeDelta: SIMD2<Float>? = SIMD2(0, 0),
        face: Bool = true
    ) -> FaceSnapshot {
        guard face else { return .noFace(timestampMs: t) }
        return FaceSnapshot(
            timestampMs: t,
            faceDetected: true,
            eyeOpenness: eyesOpen ? baseline.openEyeAperture : 0.05,
            yaw: baseline.neutralYaw + yawDelta,
            pitch: baseline.neutralPitch + pitchDelta,
            gaze: gazeDelta.map { SIMD2(baseline.neutralGazeX, baseline.neutralGazeY) + $0 },
            overlay: nil
        )
    }

    @discardableResult
    private func run(
        _ engine: DetectionEngine,
        from: Int64, to: Int64, stepMs: Int64 = 33,
        frame: (Int64) -> FaceSnapshot
    ) -> DetectionEngine.Assessment {
        var last: DetectionEngine.Assessment!
        var t = from
        while t <= to {
            last = engine.ingest(frame(t), baseline: baseline, thresholds: thresholds)
            t += stepMs
        }
        return last
    }

    // MARK: Warm-up gate

    func testNoAlertBeforeWindowFills() {
        let engine = DetectionEngine()
        // Eyes shut from the very first frame — still no alert inside 5 s.
        let result = run(engine, from: 0, to: 4900) { self.snapshot(t: $0, eyesOpen: false) }
        XCTAssertEqual(result.state, .safe)
        XCTAssertFalse(result.ready)
    }

    // MARK: Drowsiness — needs PERCLOS AND a sustained closure

    func testSustainedEyeClosureFiresDrowsy() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        let result = run(engine, from: 6033, to: 9000) { self.snapshot(t: $0, eyesOpen: false) }
        XCTAssertEqual(result.state, .drowsy)
    }

    func testNormalBlinkingNeverFiresDrowsy() {
        let engine = DetectionEngine()
        // Aggressive blinker: 150 ms blink every second (PERCLOS ≈ 15 %,
        // no closure ≥ 500 ms). Must stay safe forever.
        let result = run(engine, from: 0, to: 20_000) { t in
            self.snapshot(t: t, eyesOpen: (t % 1000) >= 150)
        }
        XCTAssertEqual(result.state, .safe)
    }

    func testFrequentShortClosuresWithoutMicrosleepStaySafe() {
        let engine = DetectionEngine()
        // 40 % duty cycle of 400 ms closures: PERCLOS well above threshold,
        // but no single closure reaches 500 ms — one signal alone must not fire.
        let result = run(engine, from: 0, to: 15_000) { t in
            self.snapshot(t: t, eyesOpen: (t % 1000) >= 400)
        }
        XCTAssertEqual(result.state, .safe)
        XCTAssertGreaterThan(result.perclos, 0.325)
    }

    func testDrowsyClearsAutomaticallyOnRecovery() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        var result = run(engine, from: 6033, to: 9000) { self.snapshot(t: $0, eyesOpen: false) }
        XCTAssertEqual(result.state, .drowsy)
        result = run(engine, from: 9033, to: 15_000) { self.snapshot(t: $0) }
        XCTAssertEqual(result.state, .safe)
        // And monitoring continues: it can fire again without any reset.
        result = run(engine, from: 15_033, to: 19_000) { self.snapshot(t: $0, eyesOpen: false) }
        XCTAssertEqual(result.state, .drowsy)
    }

    // MARK: Distraction — head and gaze must agree

    func testHeadTurnWithAgreeingGazeFiresDistracted() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        let result = run(engine, from: 6033, to: 9500) { t in
            self.snapshot(t: t, yawDelta: 0.6, gazeDelta: SIMD2(0.35, 0))
        }
        XCTAssertEqual(result.state, .distracted)
    }

    func testHeadTurnWithContradictingGazeStaysSafe() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        // Head cocked but pupils still on the road (e.g. leaning posture):
        // the gaze signal vetoes the head signal.
        let result = run(engine, from: 6033, to: 12_000) { t in
            self.snapshot(t: t, yawDelta: 0.6, gazeDelta: SIMD2(0.02, 0))
        }
        XCTAssertEqual(result.state, .safe)
    }

    func testGazeAloneNeverFiresDistracted() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        // Eyes darting with head straight — glances are normal.
        let result = run(engine, from: 6033, to: 12_000) { t in
            self.snapshot(t: t, gazeDelta: SIMD2(0.4, 0.2))
        }
        XCTAssertEqual(result.state, .safe)
    }

    func testHeadTurnWithPupilsHiddenFiresDistracted() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        // Head turned far enough that Vision loses the pupils: corroboration.
        let result = run(engine, from: 6033, to: 9500) { t in
            self.snapshot(t: t, yawDelta: 0.7, gazeDelta: nil)
        }
        XCTAssertEqual(result.state, .distracted)
    }

    func testMirrorCheckDoesNotFire() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        // 1 s glance to the mirror, then back — fails the 65 % persistence bar.
        _ = run(engine, from: 6033, to: 7000) { t in
            self.snapshot(t: t, yawDelta: 0.6, gazeDelta: SIMD2(0.35, 0))
        }
        let result = run(engine, from: 7033, to: 9000) { self.snapshot(t: $0) }
        XCTAssertEqual(result.state, .safe)
    }

    func testSustainedFaceLossFiresDistracted() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        let result = run(engine, from: 6033, to: 9500) { self.snapshot(t: $0, face: false) }
        XCTAssertEqual(result.state, .distracted)
    }

    func testBriefTrackingDropoutIsIgnored() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        // 400 ms dropout (< 700 ms grace) then normal — must stay safe.
        _ = run(engine, from: 6033, to: 6400) { self.snapshot(t: $0, face: false) }
        let result = run(engine, from: 6433, to: 9000) { self.snapshot(t: $0) }
        XCTAssertEqual(result.state, .safe)
    }

    func testDistractedClearsWhenLookingBack() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        var result = run(engine, from: 6033, to: 9500) { t in
            self.snapshot(t: t, yawDelta: 0.6, gazeDelta: SIMD2(0.35, 0))
        }
        XCTAssertEqual(result.state, .distracted)
        result = run(engine, from: 9533, to: 13_000) { self.snapshot(t: $0) }
        XCTAssertEqual(result.state, .safe)
    }

    // MARK: Priorities & robustness

    func testDrowsyOutranksDistracted() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        // Head down, eyes shut (classic nod-off): both windows trip — drowsy wins.
        let result = run(engine, from: 6033, to: 10_000) { t in
            self.snapshot(t: t, eyesOpen: false, pitchDelta: 0.5, gazeDelta: nil)
        }
        XCTAssertEqual(result.state, .drowsy)
    }

    func testBehaviorIsFrameRateIndependent() {
        // Identical wall-clock scenario at 10 fps and 30 fps → same outcome.
        for step: Int64 in [33, 100] {
            let engine = DetectionEngine()
            _ = run(engine, from: 0, to: 6000, stepMs: step) { self.snapshot(t: $0) }
            let result = run(engine, from: 6000 + step, to: 9500, stepMs: step) { t in
                self.snapshot(t: t, eyesOpen: false)
            }
            XCTAssertEqual(result.state, .drowsy, "failed at \(step) ms/frame")
        }
    }

    func testThresholdChangesApplyMidSession() {
        let engine = DetectionEngine()
        _ = run(engine, from: 0, to: 6000) { self.snapshot(t: $0) }
        // Moderate head turn that the default threshold (0.37) ignores...
        var relaxed = thresholds
        var result: DetectionEngine.Assessment!
        var t: Int64 = 6033
        while t <= 12_000 {
            result = engine.ingest(
                snapshot(t: t, yawDelta: 0.30, gazeDelta: SIMD2(0.35, 0)),
                baseline: baseline, thresholds: relaxed
            )
            t += 33
        }
        XCTAssertEqual(result.state, .safe)
        // ...fires once the user raises sensitivity — no reset, mid-stream.
        relaxed.headDeviationRad = 0.20
        while t <= 16_000 {
            result = engine.ingest(
                snapshot(t: t, yawDelta: 0.30, gazeDelta: SIMD2(0.35, 0)),
                baseline: baseline, thresholds: relaxed
            )
            t += 33
        }
        XCTAssertEqual(result.state, .distracted)
    }
}
