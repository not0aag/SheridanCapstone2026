import SwiftUI

/// The 10-second baseline capture. The countdown only advances while a face
/// is steadily detected, so the user physically cannot complete a bad
/// calibration.
///
/// Visually this is the design's calibration screen: a warm gradient wash
/// over the live feed, a glowing face mesh with a breathing ring behind it,
/// and a 68pt progress ring above the two lines of instruction. The wash is
/// nearly opaque on purpose — the mesh is the focal point, and a driver
/// doesn't need to watch themselves to hold still.
struct CalibrationView: View {
    @EnvironmentObject private var monitor: DriverMonitor
    let namespace: Namespace.ID

    var body: some View {
        CalibrationContent(calibration: monitor.calibration, namespace: namespace)
    }
}

private struct CalibrationContent: View {
    @EnvironmentObject private var monitor: DriverMonitor
    @ObservedObject var calibration: CalibrationManager
    let namespace: Namespace.ID

    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var breathing = false

    private var done: Bool { !calibration.isCalibrating && calibration.progress >= 1 }
    private var faceVisible: Bool { monitor.faceDetected }

    /// Ink for everything on the wash. Warm near-black by day, white by
    /// night — this screen sets its own foreground rather than using
    /// `Theme.textPrimary`, because it sits on a gradient, not `background`.
    private var ink: Color {
        colorScheme == .dark ? .white : Theme.oklch(0.24, 0.02, 60)
    }

    var body: some View {
        ZStack {
            // The live feed still runs underneath — it's what's actually
            // being calibrated. The wash sits at 0.9 so it reads as the
            // design's warm gradient with only a ghost of the preview.
            CameraPreview(camera: monitor.camera)
                .ignoresSafeArea()

            warmWash
                .opacity(0.9)
                .ignoresSafeArea()

            GrainOverlay()
                .opacity(0.05)
                .ignoresSafeArea()

            Aura(size: 288)
                .offset(y: -180)

            VStack(spacing: 0) {
                HStack {
                    Spacer()
                    SDCircleButton(
                        systemName: "xmark",
                        tint: ink,
                        background: ink.opacity(colorScheme == .dark ? 0.12 : 0.08)
                    ) {
                        Haptics.tap()
                        monitor.cancelCalibration()
                    }
                    .accessibilityLabel("Cancel calibration")
                }
                .padding(.horizontal, 24)
                .padding(.top, 4)

                Spacer()

                mesh

                Spacer()

                VStack(spacing: 16) {
                    progressRing

                    VStack(spacing: 4) {
                        Text(statusLine)
                            .font(.sdLead)
                            .foregroundStyle(ink)
                            .contentTransition(.opacity)
                        Text(detailLine)
                            .font(.sdCaption)
                            .foregroundStyle(ink.opacity(0.6))
                            .multilineTextAlignment(.center)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .animation(Motion.quick, value: statusLine)
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 24)
            }
        }
        .onChange(of: done) { isDone in
            if isDone { Haptics.success() }
        }
        .onAppear {
            guard !reduceMotion else { return }
            withAnimation(Motion.breathe) { breathing = true }
        }
    }

    // MARK: Pieces

    private var warmWash: some View {
        LinearGradient(
            colors: colorScheme == .dark
                ? [Theme.oklch(0.28, 0.03, 60), Theme.oklch(0.20, 0.02, 265), Theme.oklch(0.14, 0.015, 265)]
                : [Theme.oklch(0.92, 0.06, 82), Theme.oklch(0.86, 0.04, 70), Theme.oklch(0.74, 0.03, 60)],
            startPoint: .top, endPoint: .bottom
        )
    }

    /// Face mesh with the breathing ring behind it. The mesh dims while no
    /// face is found — the same signal that pauses the countdown, so the
    /// pause reads visually instead of looking like a frozen screen.
    private var mesh: some View {
        ZStack {
            Circle()
                .strokeBorder(Theme.mesh.opacity(colorScheme == .dark ? 0.25 : 0.3), lineWidth: 1)
                .frame(width: 240, height: 240)
                .scaleEffect(breathing ? 1.06 : 1)
                .opacity(breathing ? 0.9 : 0.45)

            FaceMeshView(intensity: faceVisible || done ? 1 : 0.45)
                .frame(width: 216, height: 260)
                .animation(Motion.springy, value: faceVisible)
        }
    }

    /// 68pt ring with the remaining seconds inside. This exact shape becomes
    /// the monitoring screen's status pill the moment `phase` flips away
    /// from `.calibrating` in RootView — hence the matched geometry id.
    private var progressRing: some View {
        ZStack {
            Circle()
                .strokeBorder(ink.opacity(0.18), lineWidth: 4)

            Circle()
                .inset(by: 2)
                .trim(from: 0, to: calibration.progress)
                .stroke(Theme.gold, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .opacity(faceVisible || done ? 1 : 0.55)
                .animation(Motion.quick, value: calibration.progress)

            if done {
                Image(systemName: "checkmark")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundStyle(Theme.gold)
            } else {
                Text("\(secondsRemaining)s")
                    .font(.system(size: 13, weight: .medium, design: .monospaced))
                    .monospacedDigit()
                    .foregroundStyle(ink)
            }
        }
        .frame(width: 68, height: 68)
        .animation(Motion.springy, value: done)
        .matchedGeometryEffect(id: "statusShape", in: namespace)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Calibration progress")
        .accessibilityValue(done ? "Complete" : "\(secondsRemaining) seconds remaining")
    }

    private var secondsRemaining: Int {
        Int(ceil((1 - calibration.progress) * CalibrationManager.durationSeconds))
    }

    private var statusLine: String {
        if done { return "Calibration complete" }
        if !faceVisible { return "Face not visible" }
        return "Look at the road ahead"
    }

    private var detailLine: String {
        if done { return "SafeDrive now knows your eyes and posture." }
        if !faceVisible { return "Adjust the mount so your whole face is in view. The timer is paused." }
        return "Hold steady while we learn your eye baseline"
    }
}

/// The design's 5% grain: a 3pt dot lattice that keeps the large gradient
/// from banding on OLED. Drawn once into a Canvas rather than shipped as an
/// image asset.
private struct GrainOverlay: View {
    var body: some View {
        Canvas { context, size in
            let dot = Path(ellipseIn: CGRect(x: 0, y: 0, width: 1, height: 1))
            let color = GraphicsContext.Shading.color(Theme.oklch(0.21, 0.015, 65))
            var y: CGFloat = 0
            while y < size.height {
                var x: CGFloat = 0
                while x < size.width {
                    context.fill(dot.offsetBy(dx: x, dy: y), with: color)
                    x += 3
                }
                y += 3
            }
        }
        .allowsHitTesting(false)
        .accessibilityHidden(true)
    }
}
