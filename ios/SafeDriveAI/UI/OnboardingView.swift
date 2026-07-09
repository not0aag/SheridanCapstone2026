import SwiftUI
import AVFoundation

/// Three quick pages: what it does → how to mount → why calibration.
/// Ends by requesting camera permission and handing off to calibration.
struct OnboardingView: View {
    let onFinished: () -> Void
    @State private var page = 0
    @State private var cameraDenied = false

    var body: some View {
        VStack {
            TabView(selection: $page) {
                pageView(
                    icon: "eye.trianglebadge.exclamationmark.fill",
                    title: "Your co-pilot that never blinks",
                    body: "SafeDrive AI watches for drowsiness and distraction using the front camera, and alerts you the moment you're at risk. Everything runs on this phone — nothing is recorded, nothing leaves the device.",
                    tag: 0
                )
                pageView(
                    icon: "car.side.arrowtriangle.up.fill",
                    title: "Mount the phone",
                    body: "Put your iPhone in a dashboard or vent mount with the front camera facing you. Any position works — the app adapts to your setup.",
                    tag: 1
                )
                pageView(
                    icon: "person.crop.rectangle.badge.plus.fill",
                    title: "10 seconds to learn your face",
                    body: "Next, a one-time calibration measures your eyes and natural driving posture. That's what makes alerts accurate for you — not an average driver.",
                    tag: 2
                )
            }
            .tabViewStyle(.page(indexDisplayMode: .always))

            Button(page < 2 ? "Continue" : "Start Calibration") {
                if page < 2 {
                    withAnimation { page += 1 }
                } else {
                    requestCameraThenFinish()
                }
            }
            .buttonStyle(BigButtonStyle())
            .padding(.horizontal, 24)
            .padding(.bottom, 20)
        }
        .alert("Camera access is required", isPresented: $cameraDenied) {
            Button("Open Settings") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("SafeDrive AI cannot monitor you without the front camera. Enable camera access in Settings.")
        }
    }

    private func pageView(icon: String, title: String, body text: String, tag: Int) -> some View {
        VStack(spacing: 28) {
            Spacer()
            Image(systemName: icon)
                .font(.system(size: 80))
                .foregroundStyle(Theme.accent)
            Text(title)
                .font(.largeTitle.weight(.bold))
                .multilineTextAlignment(.center)
            Text(text)
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 8)
            Spacer()
            Spacer()
        }
        .padding(.horizontal, 24)
        .tag(tag)
    }

    private func requestCameraThenFinish() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            onFinished()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async {
                    granted ? onFinished() : (cameraDenied = true)
                }
            }
        default:
            cameraDenied = true
        }
    }
}
