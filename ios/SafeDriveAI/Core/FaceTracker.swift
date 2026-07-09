import Foundation
import Vision
import CoreVideo
import simd

/// Everything the detection pipeline needs from one camera frame, extracted
/// with Apple's Vision framework and stripped of Vision types so the engine
/// and its tests stay framework-free.
struct FaceSnapshot {
    let timestampMs: Int64
    let faceDetected: Bool
    /// Eye aperture: eye landmark bounding-box height / width, averaged over
    /// both eyes. Person- and angle-dependent — always compared against the
    /// calibrated baseline, never an absolute constant.
    let eyeOpenness: Float
    /// Head rotation in radians, as measured by Vision.
    let yaw: Float
    let pitch: Float
    /// Pupil offset from eye center, normalized by eye width. nil when pupils
    /// aren't visible (eyes closed / low confidence).
    let gaze: SIMD2<Float>?
    /// Landmark geometry for the on-screen overlay (normalized image
    /// coordinates, origin top-left, mirrored to match the preview).
    let overlay: FaceOverlayGeometry?

    static func noFace(timestampMs: Int64) -> FaceSnapshot {
        FaceSnapshot(timestampMs: timestampMs, faceDetected: false, eyeOpenness: 0,
                     yaw: 0, pitch: 0, gaze: nil, overlay: nil)
    }
}

struct FaceOverlayGeometry: Equatable {
    /// Pixel dimensions of the source frame — needed to replicate the
    /// preview's aspect-fill mapping when drawing the overlay.
    let imageSize: CGSize
    let boundingBox: CGRect
    let leftEye: [CGPoint]
    let rightEye: [CGPoint]
    let faceContour: [CGPoint]
}

/// Runs VNDetectFaceLandmarksRequest on camera frames.
///
/// Why Vision over third-party landmark SDKs: it ships with iOS (zero
/// dependencies), runs on the Neural Engine, and directly reports head
/// yaw/pitch/roll — no manual 3D geometry needed.
final class FaceTracker {
    /// Called on the capture queue with each processed frame.
    var onSnapshot: ((FaceSnapshot) -> Void)?

    private var isProcessing = false

    func process(pixelBuffer: CVPixelBuffer, timestampMs: Int64) {
        // Drop frames if Vision is still busy — stale results are worse than
        // a slightly lower analysis rate.
        guard !isProcessing else { return }
        isProcessing = true
        defer { isProcessing = false }

        let request = VNDetectFaceLandmarksRequest()
        let handler = VNImageRequestHandler(cvPixelBuffer: pixelBuffer, orientation: .up)
        do {
            try handler.perform([request])
        } catch {
            onSnapshot?(.noFace(timestampMs: timestampMs))
            return
        }

        guard let face = request.results?.first, let landmarks = face.landmarks else {
            onSnapshot?(.noFace(timestampMs: timestampMs))
            return
        }

        let width = CGFloat(CVPixelBufferGetWidth(pixelBuffer))
        let height = CGFloat(CVPixelBufferGetHeight(pixelBuffer))
        let imageSize = CGSize(width: width, height: height)

        let leftEyePts = landmarks.leftEye?.pointsInImage(imageSize: imageSize) ?? []
        let rightEyePts = landmarks.rightEye?.pointsInImage(imageSize: imageSize) ?? []

        let openness = Self.averageOpenness(leftEye: leftEyePts, rightEye: rightEyePts)
        let gaze = Self.gazeOffset(
            leftEye: leftEyePts, rightEye: rightEyePts,
            leftPupil: landmarks.leftPupil?.pointsInImage(imageSize: imageSize).first,
            rightPupil: landmarks.rightPupil?.pointsInImage(imageSize: imageSize).first
        )

        let overlay = FaceOverlayGeometry(
            imageSize: imageSize,
            boundingBox: Self.normalizedTopLeft(face.boundingBox),
            leftEye: leftEyePts.map { Self.normalizePoint($0, imageSize: imageSize) },
            rightEye: rightEyePts.map { Self.normalizePoint($0, imageSize: imageSize) },
            faceContour: (landmarks.faceContour?.pointsInImage(imageSize: imageSize) ?? [])
                .map { Self.normalizePoint($0, imageSize: imageSize) }
        )

        onSnapshot?(FaceSnapshot(
            timestampMs: timestampMs,
            faceDetected: true,
            eyeOpenness: openness,
            yaw: face.yaw?.floatValue ?? 0,
            pitch: face.pitch?.floatValue ?? 0,
            gaze: gaze,
            overlay: overlay
        ))
    }

    // MARK: Signal math (static & pure for testability)

    /// Aperture ratio of one eye's landmark cloud: height / width.
    static func openness(eyePoints: [CGPoint]) -> Float? {
        guard eyePoints.count >= 4 else { return nil }
        let xs = eyePoints.map(\.x), ys = eyePoints.map(\.y)
        let w = xs.max()! - xs.min()!
        guard w > 1 else { return nil }
        return Float((ys.max()! - ys.min()!) / w)
    }

    static func averageOpenness(leftEye: [CGPoint], rightEye: [CGPoint]) -> Float {
        let values = [openness(eyePoints: leftEye), openness(eyePoints: rightEye)].compactMap { $0 }
        guard !values.isEmpty else { return 0 }
        return values.reduce(0, +) / Float(values.count)
    }

    /// Pupil displacement from eye center, normalized by eye width and
    /// averaged over both eyes. (0,0) = looking where the eyes point.
    static func gazeOffset(
        leftEye: [CGPoint], rightEye: [CGPoint],
        leftPupil: CGPoint?, rightPupil: CGPoint?
    ) -> SIMD2<Float>? {
        func offset(eye: [CGPoint], pupil: CGPoint?) -> SIMD2<Float>? {
            guard let pupil, eye.count >= 4 else { return nil }
            let xs = eye.map(\.x), ys = eye.map(\.y)
            let w = xs.max()! - xs.min()!
            guard w > 1 else { return nil }
            let center = CGPoint(x: (xs.max()! + xs.min()!) / 2, y: (ys.max()! + ys.min()!) / 2)
            return SIMD2<Float>(Float((pupil.x - center.x) / w), Float((pupil.y - center.y) / w))
        }
        let offsets = [offset(eye: leftEye, pupil: leftPupil),
                       offset(eye: rightEye, pupil: rightPupil)].compactMap { $0 }
        guard !offsets.isEmpty else { return nil }
        return offsets.reduce(.zero, +) / Float(offsets.count)
    }

    // MARK: Coordinate conversion (Vision is bottom-left origin; UI is top-left)

    private static func normalizePoint(_ p: CGPoint, imageSize: CGSize) -> CGPoint {
        CGPoint(x: p.x / imageSize.width, y: 1 - p.y / imageSize.height)
    }

    private static func normalizedTopLeft(_ rect: CGRect) -> CGRect {
        CGRect(x: rect.minX, y: 1 - rect.maxY, width: rect.width, height: rect.height)
    }
}
