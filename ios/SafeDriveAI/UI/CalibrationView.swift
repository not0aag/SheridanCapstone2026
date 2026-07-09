import SwiftUI

/// Live preview + progress ring. The countdown only advances while a face is
/// steadily detected, so the user physically cannot complete a bad calibration.
struct CalibrationView: View {
    @EnvironmentObject private var monitor: DriverMonitor

    var body: some View {
        CalibrationContent(calibration: monitor.calibration)
    }
}

private struct CalibrationContent: View {
    @EnvironmentObject private var monitor: DriverMonitor
    @ObservedObject var calibration: CalibrationManager

    private var done: Bool { !calibration.isCalibrating && calibration.progress >= 1 }

    var body: some View {
        ZStack {
            CameraPreview(session: monitor.camera.session)
                .ignoresSafeArea()

            FaceOverlay(geometry: monitor.overlay, state: .safe)
                .ignoresSafeArea()

            LinearGradient(
                colors: [.black.opacity(0.75), .clear, .clear, .black.opacity(0.85)],
                startPoint: .top, endPoint: .bottom
            )
            .ignoresSafeArea()
            .allowsHitTesting(false)

            VStack {
                HStack {
                    Button {
                        monitor.cancelCalibration()
                    } label: {
                        Image(systemName: "xmark")
                            .font(.headline)
                            .padding(14)
                            .background(.ultraThinMaterial, in: Circle())
                    }
                    Spacer()
                }
                .padding()

                Text("Calibration")
                    .font(.title2.weight(.bold))

                Spacer()

                // Progress ring around a status glyph — readable in one glance.
                ZStack {
                    Circle()
                        .stroke(.white.opacity(0.15), lineWidth: 10)
                    Circle()
                        .trim(from: 0, to: calibration.progress)
                        .stroke(Theme.accent, style: StrokeStyle(lineWidth: 10, lineCap: .round))
                        .rotationEffect(.degrees(-90))
                        .animation(.linear(duration: 0.2), value: calibration.progress)
                    Image(systemName: done ? "checkmark" : (monitor.faceDetected ? "eye.fill" : "eye.slash.fill"))
                        .font(.system(size: 44, weight: .bold))
                        .foregroundStyle(done ? Theme.accent : (monitor.faceDetected ? .white : Theme.warning))
                        .contentTransition(.opacity) // .symbolEffect needs iOS 17; target is 16
                }
                .frame(width: 150, height: 150)

                Spacer()

                VStack(spacing: 10) {
                    Text(statusLine)
                        .font(.title3.weight(.semibold))
                        .multilineTextAlignment(.center)
                    Text(detailLine)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(24)
            }
        }
    }

    private var statusLine: String {
        if done { return "Calibration complete" }
        if !monitor.faceDetected { return "Face not visible" }
        return "Look at the road ahead"
    }

    private var detailLine: String {
        if done { return "SafeDrive AI now knows your eyes and posture." }
        if !monitor.faceDetected { return "Adjust the mount so your whole face is in view. The timer is paused." }
        return "Sit naturally and keep your eyes open. \(Int(ceil((1 - calibration.progress) * CalibrationManager.durationSeconds)))s remaining."
    }
}
