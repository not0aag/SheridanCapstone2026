import XCTest
import simd
@testable import SafeDriveAI

final class CalibrationManagerTests: XCTestCase {
    private var defaults: UserDefaults!

    override func setUp() {
        super.setUp()
        defaults = UserDefaults(suiteName: "calibration-tests")!
        defaults.removePersistentDomain(forName: "calibration-tests")
    }

    private func snapshot(t: Int64, openness: Float, face: Bool = true) -> FaceSnapshot {
        guard face else { return .noFace(timestampMs: t) }
        return FaceSnapshot(
            timestampMs: t, faceDetected: true, eyeOpenness: openness,
            yaw: 0.12, pitch: -0.04, gaze: SIMD2(0.03, 0.01), overlay: nil
        )
    }

    func testCalibrationDiscardsBlinkFrames() {
        let manager = CalibrationManager(defaults: defaults)
        manager.begin()
        var t: Int64 = 0
        var completed = false
        while !completed && t < 15_000 {
            // Eyes open at 0.30 with a blink (0.06) every 20th frame.
            let openness: Float = (t / 33) % 20 == 0 ? 0.06 : 0.30
            completed = manager.ingest(snapshot(t: t, openness: openness))
            t += 33
        }
        XCTAssertTrue(completed)
        // Blinks fell in the discarded bottom 10 % — open aperture ≈ 0.30.
        XCTAssertEqual(manager.baseline!.openEyeAperture, 0.30, accuracy: 0.01)
        XCTAssertEqual(manager.baseline!.neutralYaw, 0.12, accuracy: 0.001)
    }

    func testCountdownPausesWhenFaceIsLost() {
        let manager = CalibrationManager(defaults: defaults)
        manager.begin()
        // 3 s of face...
        var t: Int64 = 0
        while t < 3000 { manager.ingest(snapshot(t: t, openness: 0.3)); t += 33 }
        let progressBefore = manager.progress
        // ...then 5 s of no face: progress must not advance.
        while t < 8000 { manager.ingest(snapshot(t: t, openness: 0, face: false)); t += 33 }
        XCTAssertEqual(manager.progress, progressBefore, accuracy: 0.02)
        XCTAssertFalse(manager.isFaceSteady)
    }

    func testBaselinePersistsAcrossRelaunch() {
        let manager = CalibrationManager(defaults: defaults)
        manager.begin()
        var t: Int64 = 0
        var completed = false
        while !completed && t < 15_000 {
            completed = manager.ingest(snapshot(t: t, openness: 0.3))
            t += 33
        }
        XCTAssertTrue(completed)

        // Fresh instance on the same store — simulates an app relaunch.
        let relaunched = CalibrationManager(defaults: defaults)
        XCTAssertEqual(relaunched.baseline, manager.baseline)
        XCTAssertTrue(relaunched.isCalibrated)
    }

    func testResetClearsPersistedBaseline() {
        let manager = CalibrationManager(defaults: defaults)
        manager.begin()
        var t: Int64 = 0
        var completed = false
        while !completed && t < 15_000 {
            completed = manager.ingest(snapshot(t: t, openness: 0.3))
            t += 33
        }
        manager.reset()
        XCTAssertFalse(manager.isCalibrated)
        XCTAssertNil(CalibrationManager(defaults: defaults).baseline)
    }
}

final class SignalMathTests: XCTestCase {
    /// Synthetic 6-point eye contour, `height` tall and `width` wide.
    private func eye(width: CGFloat, height: CGFloat, cx: CGFloat = 100, cy: CGFloat = 100) -> [CGPoint] {
        [
            CGPoint(x: cx - width / 2, y: cy),
            CGPoint(x: cx - width / 6, y: cy - height / 2),
            CGPoint(x: cx + width / 6, y: cy - height / 2),
            CGPoint(x: cx + width / 2, y: cy),
            CGPoint(x: cx + width / 6, y: cy + height / 2),
            CGPoint(x: cx - width / 6, y: cy + height / 2),
        ]
    }

    func testOpennessRatio() {
        // 30 tall / 100 wide → 0.30
        XCTAssertEqual(FaceTracker.openness(eyePoints: eye(width: 100, height: 30))!, 0.30, accuracy: 0.001)
        // Nearly shut eye.
        XCTAssertLessThan(FaceTracker.openness(eyePoints: eye(width: 100, height: 3))!, 0.05)
    }

    func testOpennessRejectsDegenerateInput() {
        XCTAssertNil(FaceTracker.openness(eyePoints: []))
        XCTAssertNil(FaceTracker.openness(eyePoints: Array(repeating: CGPoint(x: 5, y: 5), count: 6)))
    }

    func testCenteredPupilGivesZeroGaze() {
        let gaze = FaceTracker.gazeOffset(
            leftEye: eye(width: 100, height: 30),
            rightEye: eye(width: 100, height: 30, cx: 300),
            leftPupil: CGPoint(x: 100, y: 100),
            rightPupil: CGPoint(x: 300, y: 100)
        )
        XCTAssertEqual(simd_length(gaze!), 0, accuracy: 1e-5)
    }

    func testOffsetPupilGivesProportionalGaze() {
        // Pupils 25 px right of center in 100 px-wide eyes → x offset 0.25.
        let gaze = FaceTracker.gazeOffset(
            leftEye: eye(width: 100, height: 30),
            rightEye: eye(width: 100, height: 30, cx: 300),
            leftPupil: CGPoint(x: 125, y: 100),
            rightPupil: CGPoint(x: 325, y: 100)
        )
        XCTAssertEqual(gaze!.x, 0.25, accuracy: 0.001)
        XCTAssertEqual(gaze!.y, 0, accuracy: 0.001)
    }

    func testGazeNilWithoutPupils() {
        XCTAssertNil(FaceTracker.gazeOffset(
            leftEye: eye(width: 100, height: 30), rightEye: eye(width: 100, height: 30, cx: 300),
            leftPupil: nil, rightPupil: nil
        ))
    }
}
