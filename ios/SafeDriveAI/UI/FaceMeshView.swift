import SwiftUI

/// The glowing face-tracking mesh shown during calibration.
///
/// A direct translation of the design system's `FaceMesh` SVG: same 200×240
/// authoring space, same control points. It is a *stylised guide* — an
/// "align your face here" affordance — and never reflects real landmark
/// positions. Live tracking is drawn by `FaceOverlay`, which reads actual
/// `FaceOverlayGeometry` from the camera; the two are deliberately separate
/// so a decorative change here can never be mistaken for a tracking change.
struct FaceMeshView: View {
    /// The mesh's single color. `Theme.mesh` rather than `Theme.gold`: on
    /// the light warm wash, gold at 1px all but disappears.
    var tone: Color = Theme.mesh
    /// Fades the whole mesh — calibration dims it while no face is found.
    var intensity: Double = 1

    var body: some View {
        ZStack {
            // Contour grid, clipped to the face so lines stop at the jaw.
            ZStack {
                FaceContours()
                    .stroke(tone, lineWidth: 1)
                FaceGridLines()
                    .stroke(tone.opacity(0.4), lineWidth: 1)
            }
            .clipShape(FaceOutline())

            FaceOutline()
                .stroke(tone, lineWidth: 1)

            EyeContour(side: .left)
                .stroke(tone, lineWidth: 1.7)
            EyeContour(side: .right)
                .stroke(tone, lineWidth: 1.7)

            MouthCurve()
                .stroke(tone, lineWidth: 1.4)
            NoseLine()
                .stroke(tone.opacity(0.6), lineWidth: 1.1)

            Pupils()
                .fill(tone)
        }
        .opacity(0.85 * intensity)
        // Two passes: a tight core glow and a wider bloom, which is what
        // gives the mesh its "lit from within" quality rather than a flat
        // drop shadow.
        .shadow(color: tone.opacity(0.55 * intensity), radius: 6)
        .shadow(color: tone.opacity(0.25 * intensity), radius: 16)
        .aspectRatio(200.0 / 240.0, contentMode: .fit)
        .accessibilityHidden(true)
    }
}

// MARK: - Authoring space

/// Every shape below is authored in the SVG's 200×240 space and scaled into
/// whatever rect it's given, so the control points can be read straight off
/// the original paths without conversion.
private enum Mesh {
    static let width: CGFloat = 200
    static let height: CGFloat = 240

    static func transform(in rect: CGRect) -> CGAffineTransform {
        CGAffineTransform(translationX: rect.minX, y: rect.minY)
            .scaledBy(x: rect.width / width, y: rect.height / height)
    }
}

private struct FaceOutline: Shape {
    func path(in rect: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: 100, y: 24))
        p.addCurve(to: CGPoint(x: 157, y: 87),
                   control1: CGPoint(x: 133, y: 24), control2: CGPoint(x: 157, y: 49))
        p.addCurve(to: CGPoint(x: 134, y: 164),
                   control1: CGPoint(x: 157, y: 118), control2: CGPoint(x: 149, y: 145))
        p.addCurve(to: CGPoint(x: 100, y: 188),
                   control1: CGPoint(x: 123, y: 179), control2: CGPoint(x: 112, y: 188))
        // Original path uses a smooth (`s`) segment here; its first control
        // point is the reflection of the previous one about (100,188).
        p.addCurve(to: CGPoint(x: 66, y: 164),
                   control1: CGPoint(x: 88, y: 188), control2: CGPoint(x: 77, y: 179))
        p.addCurve(to: CGPoint(x: 43, y: 87),
                   control1: CGPoint(x: 51, y: 145), control2: CGPoint(x: 43, y: 118))
        p.addCurve(to: CGPoint(x: 100, y: 24),
                   control1: CGPoint(x: 43, y: 49), control2: CGPoint(x: 67, y: 24))
        p.closeSubpath()
        return p.applying(Mesh.transform(in: rect))
    }
}

/// The five horizontal contour lines that sag across the face.
private struct FaceContours: Shape {
    private static let rows: [(start: CGPoint, c1: CGPoint, c2: CGPoint, end: CGPoint)] = [
        (CGPoint(x: 40, y: 76),  CGPoint(x: 80, y: 62),  CGPoint(x: 120, y: 62),  CGPoint(x: 160, y: 76)),
        (CGPoint(x: 36, y: 104), CGPoint(x: 80, y: 92),  CGPoint(x: 120, y: 92),  CGPoint(x: 164, y: 104)),
        (CGPoint(x: 40, y: 132), CGPoint(x: 80, y: 122), CGPoint(x: 120, y: 122), CGPoint(x: 160, y: 132)),
        (CGPoint(x: 46, y: 160), CGPoint(x: 82, y: 151), CGPoint(x: 118, y: 151), CGPoint(x: 154, y: 160)),
        (CGPoint(x: 56, y: 188), CGPoint(x: 86, y: 180), CGPoint(x: 114, y: 180), CGPoint(x: 144, y: 188)),
    ]

    func path(in rect: CGRect) -> Path {
        var p = Path()
        for row in Self.rows {
            p.move(to: row.start)
            p.addCurve(to: row.end, control1: row.c1, control2: row.c2)
        }
        return p.applying(Mesh.transform(in: rect))
    }
}

/// The five vertical lines. Drawn at lower opacity so the horizontals read
/// as the dominant contour direction.
private struct FaceGridLines: Shape {
    private static let columns: [(x: CGFloat, top: CGFloat, bottom: CGFloat)] = [
        (100, 20, 220), (76, 26, 206), (124, 26, 206), (58, 40, 180), (142, 40, 180),
    ]

    func path(in rect: CGRect) -> Path {
        var p = Path()
        for column in Self.columns {
            p.move(to: CGPoint(x: column.x, y: column.top))
            p.addLine(to: CGPoint(x: column.x, y: column.bottom))
        }
        return p.applying(Mesh.transform(in: rect))
    }
}

/// A lens-shaped eye outline: two mirrored curves meeting at the corners.
private struct EyeContour: Shape {
    enum Side { case left, right }
    let side: Side

    func path(in rect: CGRect) -> Path {
        let x0: CGFloat = side == .left ? 68 : 99
        var p = Path()
        p.move(to: CGPoint(x: x0, y: 105))
        p.addCurve(to: CGPoint(x: x0 + 33, y: 105),
                   control1: CGPoint(x: x0 + 8, y: 96), control2: CGPoint(x: x0 + 25, y: 96))
        p.addCurve(to: CGPoint(x: x0, y: 105),
                   control1: CGPoint(x: x0 + 25, y: 114), control2: CGPoint(x: x0 + 8, y: 114))
        p.closeSubpath()
        return p.applying(Mesh.transform(in: rect))
    }
}

private struct MouthCurve: Shape {
    func path(in rect: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: 86, y: 158))
        p.addCurve(to: CGPoint(x: 114, y: 158),
                   control1: CGPoint(x: 94, y: 164), control2: CGPoint(x: 106, y: 164))
        return p.applying(Mesh.transform(in: rect))
    }
}

private struct NoseLine: Shape {
    func path(in rect: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: 94, y: 108))
        p.addLine(to: CGPoint(x: 94, y: 134))
        p.addCurve(to: CGPoint(x: 102, y: 140),
                   control1: CGPoint(x: 94, y: 138), control2: CGPoint(x: 97, y: 140))
        return p.applying(Mesh.transform(in: rect))
    }
}

private struct Pupils: Shape {
    func path(in rect: CGRect) -> Path {
        var p = Path()
        for x in [CGFloat(84), CGFloat(116)] {
            p.addEllipse(in: CGRect(x: x - 3.4, y: 105 - 3.4, width: 6.8, height: 6.8))
        }
        return p.applying(Mesh.transform(in: rect))
    }
}
