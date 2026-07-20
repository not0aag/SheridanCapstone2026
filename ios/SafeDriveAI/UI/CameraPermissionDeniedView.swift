import SwiftUI

/// Full-screen block shown when camera access is denied or restricted — the
/// app is unusable without it, so this replaces the whole UI rather than
/// degrading one specific screen.
struct CameraPermissionDeniedView: View {
    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "camera.fill.badge.ellipsis")
                .font(.system(size: 60))
                .foregroundStyle(Theme.warning)
            Text("Camera Access Needed")
                .font(.title2.weight(.bold))
            Text("SafeDrive AI watches the road through your front camera to detect drowsiness and distraction. Enable camera access in Settings to continue.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            Spacer()
            Button {
                guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
                UIApplication.shared.open(url)
            } label: {
                Text("Open Settings")
            }
            .buttonStyle(BigButtonStyle())
            .padding(.horizontal, 24)
            .padding(.bottom, 40)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.background)
    }
}
