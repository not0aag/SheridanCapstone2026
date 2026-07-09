import SwiftUI

/// Subtle landmark overlay: face outline + eye contours, drawn over the
/// aspect-fill camera preview. Confirms at a glance that tracking is live;
/// tint follows the driver state.
struct FaceOverlay: View {
    let geometry: FaceOverlayGeometry?
    let state: DriverState

    var body: some View {
        GeometryReader { proxy in
            Canvas { context, size in
                guard let geometry else { return }
                let map = Self.aspectFillMapper(
                    imageSize: geometry.imageSize, viewSize: size
                )
                let color = Theme.color(for: state)

                // Face outline — faint.
                if geometry.faceContour.count > 2 {
                    var path = Path()
                    path.addLines(geometry.faceContour.map(map))
                    context.stroke(path, with: .color(color.opacity(0.35)), lineWidth: 1.5)
                }

                // Eyes — brighter, closed loops.
                for eye in [geometry.leftEye, geometry.rightEye] where eye.count > 2 {
                    var path = Path()
                    path.addLines(eye.map(map))
                    path.closeSubpath()
                    context.stroke(path, with: .color(color.opacity(0.9)), lineWidth: 2)
                }
            }
        }
        .allowsHitTesting(false)
        .animation(nil, value: state) // overlay must never lag the video
    }

    /// Maps normalized (top-left origin) image coordinates onto a view that
    /// shows the image with aspect-fill (same math the preview layer uses).
    static func aspectFillMapper(imageSize: CGSize, viewSize: CGSize) -> (CGPoint) -> CGPoint {
        guard imageSize.width > 0, imageSize.height > 0 else { return { $0 } }
        let scale = max(viewSize.width / imageSize.width, viewSize.height / imageSize.height)
        let drawn = CGSize(width: imageSize.width * scale, height: imageSize.height * scale)
        let offset = CGPoint(x: (viewSize.width - drawn.width) / 2,
                             y: (viewSize.height - drawn.height) / 2)
        return { p in
            CGPoint(x: offset.x + p.x * drawn.width, y: offset.y + p.y * drawn.height)
        }
    }
}
