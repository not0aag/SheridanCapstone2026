import ARKit
import simd

/// Converts ARKit's TrueDepth face-tracking anchors into `FaceSnapshot`.
///
/// Why ARKit instead of Vision: Vision's `VNFaceObservation.yaw`/`pitch` is
/// a ~5–8° estimate derived from 2D landmark positions in a single image,
/// and the old gaze signal was a 2D pupil-offset approximation on top of
/// that. `ARFaceAnchor` is built from the TrueDepth camera's structured-
/// light depth data — a real 3D face transform and per-eye 3D gaze, not an
/// estimate from a flat image. That's the same category of upgrade
/// dedicated automotive DMS hardware (IR + 3D sensing) represents over a
/// plain selfie camera, and it's what was diagnosed as the likely cause of
/// the distraction-detection false-negative problem (see the plan this
/// implements, and ios/HANDOVER.md Section 8).
///
/// `FaceSnapshot`'s shape is unchanged from the Vision-based `FaceTracker`,
/// so `DetectionEngine`/`CalibrationManager`/`AppSettings` and their tests
/// don't know or care that the signal source changed. `FaceTracker.swift`
/// itself is untouched and stays available as the fallback path on
/// hardware without a TrueDepth camera (see `CameraService`).
final class ARFaceTracker {
    /// Called on the session's delegate queue with each frame update.
    var onSnapshot: ((FaceSnapshot) -> Void)?

    func process(frame: ARFrame) {
        let timestampMs = Int64(frame.timestamp * 1000)
        guard
            let anchor = frame.anchors.compactMap({ $0 as? ARFaceAnchor }).first,
            anchor.isTracked
        else {
            onSnapshot?(.noFace(timestampMs: timestampMs))
            return
        }
        onSnapshot?(Self.snapshot(from: anchor, frame: frame, timestampMs: timestampMs))
    }

    // MARK: Signal extraction — real 3D data, no 2D estimation

    static func snapshot(from anchor: ARFaceAnchor, frame: ARFrame, timestampMs: Int64) -> FaceSnapshot {
        let (yaw, pitch) = headPose(from: anchor.transform)
        return FaceSnapshot(
            timestampMs: timestampMs,
            faceDetected: true,
            eyeOpenness: eyeOpenness(from: anchor),
            yaw: yaw,
            pitch: pitch,
            gaze: gazeOffset(from: anchor),
            overlay: overlayGeometry(for: anchor, frame: frame)
        )
    }

    /// Real 3D head rotation extracted from the face anchor's transform
    /// matrix. `DetectionEngine` only ever compares this against a
    /// *calibrated baseline* taken with this same formula (never an
    /// absolute real-world angle), so the exact sign/axis convention here
    /// doesn't need to match any external standard — it only needs to
    /// respond consistently and monotonically to actual head rotation.
    private static func headPose(from transform: simd_float4x4) -> (yaw: Float, pitch: Float) {
        let sy = min(max(-transform.columns.2.x, -1), 1)
        let pitch = asin(sy)
        let yaw = atan2(transform.columns.2.y, transform.columns.2.z)
        return (yaw, pitch)
    }

    /// ARKit's own 3D gaze estimate, in face-local space — replaces the old
    /// 2D pupil-offset approximation entirely. Always present while a face
    /// is tracked (unlike 2D pupil landmarks, which could go missing on a
    /// blink), so `DetectionEngine`'s "pupils hidden" corroboration path is
    /// effectively unreachable now — eyesClosed alone gates that branch.
    private static func gazeOffset(from anchor: ARFaceAnchor) -> SIMD2<Float> {
        SIMD2<Float>(anchor.lookAtPoint.x, anchor.lookAtPoint.y)
    }

    /// 1 = fully open, 0 = fully closed — inverse of ARKit's blink blend
    /// shapes, averaged over both eyes. Native to ARKit's face model, not
    /// derived from a landmark bounding-box ratio.
    private static func eyeOpenness(from anchor: ARFaceAnchor) -> Float {
        let left = anchor.blendShapes[.eyeBlinkLeft]?.floatValue ?? 0
        let right = anchor.blendShapes[.eyeBlinkRight]?.floatValue ?? 0
        return 1 - (left + right) / 2
    }

    // MARK: Overlay (cosmetic only — never feeds detection)

    /// Approximates the on-screen face/eye outline from precisely-known
    /// anchor points (the face transform, per-eye transforms) rather than
    /// walking ARKit's full 1220-vertex face mesh, since ARKit doesn't
    /// publish named landmark indices for that mesh the way MediaPipe/
    /// Vision expose eye contours. This is a stylized approximation —
    /// every value `DetectionEngine` actually acts on (yaw/pitch/gaze/
    /// eyeOpenness above) comes straight from ARKit's real 3D data, not
    /// from this projection. Verify the visual alignment on-device; the
    /// projection math here is not guaranteed pixel-perfect.
    private static func overlayGeometry(for anchor: ARFaceAnchor, frame: ARFrame) -> FaceOverlayGeometry? {
        let camera = frame.camera
        let imageSize = camera.imageResolution
        guard imageSize.width > 0, imageSize.height > 0 else { return nil }

        // Mirrored (x flipped) to match the selfie-mirror camera preview —
        // ARKit's raw camera image isn't mirrored the way AVCaptureConnection
        // could mirror it for the old Vision pipeline.
        func project(_ worldPoint: SIMD3<Float>) -> CGPoint {
            let p = camera.projectPoint(worldPoint, orientation: .portrait, viewportSize: imageSize)
            return CGPoint(x: 1 - p.x / imageSize.width, y: p.y / imageSize.height)
        }
        func worldPosition(ofLocal local: simd_float4x4) -> SIMD3<Float> {
            let world = anchor.transform * local
            return SIMD3<Float>(world.columns.3.x, world.columns.3.y, world.columns.3.z)
        }

        let facePos = SIMD3<Float>(anchor.transform.columns.3.x, anchor.transform.columns.3.y, anchor.transform.columns.3.z)
        let leftEyePos = worldPosition(ofLocal: anchor.leftEyeTransform)
        let rightEyePos = worldPosition(ofLocal: anchor.rightEyeTransform)
        let right = SIMD3<Float>(anchor.transform.columns.0.x, anchor.transform.columns.0.y, anchor.transform.columns.0.z)
        let up = SIMD3<Float>(anchor.transform.columns.1.x, anchor.transform.columns.1.y, anchor.transform.columns.1.z)

        func ring(around center: SIMD3<Float>, radius: Float, points: Int) -> [CGPoint] {
            (0..<points).map { i in
                let t = Float(i) / Float(points) * 2 * .pi
                let offset = right * (cos(t) * radius) + up * (sin(t) * radius)
                return project(center + offset)
            }
        }

        let leftEye = ring(around: leftEyePos, radius: 0.012, points: 8)
        let rightEye = ring(around: rightEyePos, radius: 0.012, points: 8)
        let faceContour = ring(around: facePos, radius: 0.09, points: 16)

        let xs = faceContour.map(\.x), ys = faceContour.map(\.y)
        let boundingBox = CGRect(
            x: xs.min() ?? 0, y: ys.min() ?? 0,
            width: (xs.max() ?? 0) - (xs.min() ?? 0),
            height: (ys.max() ?? 0) - (ys.min() ?? 0)
        )

        return FaceOverlayGeometry(
            imageSize: imageSize,
            boundingBox: boundingBox,
            leftEye: leftEye,
            rightEye: rightEye,
            faceContour: faceContour
        )
    }
}
