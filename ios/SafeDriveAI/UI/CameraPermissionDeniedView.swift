import SwiftUI

/// Full-screen block shown when camera access is denied or restricted — the
/// app is unusable without it, so this replaces the whole UI rather than
/// degrading one specific screen.
///
/// Deliberately muted: the camera glyph sits on `surface-2`, not amber. The
/// only amber on screen is the CTA, because that's the one thing the user
/// can actually act on.
struct CameraPermissionDeniedView: View {
    var body: some View {
        ZStack(alignment: .topTrailing) {
            Theme.background.ignoresSafeArea()

            Aura(size: 224)
                .offset(x: 40, y: -32)

            VStack(spacing: 0) {
                Spacer()

                Image(systemName: "camera.fill")
                    .font(.system(size: 30, weight: .medium))
                    .foregroundStyle(Theme.textSecondary)
                    .frame(width: 74, height: 74)
                    .background(
                        RoundedRectangle(cornerRadius: Theme.Radius.icon, style: .continuous)
                            .fill(Theme.surface2)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: Theme.Radius.icon, style: .continuous)
                            .strokeBorder(Theme.hairline, lineWidth: 1)
                    )

                Text("Camera access needed")
                    .font(.sdTitle)
                    .tracking(28 * -0.01)
                    .foregroundStyle(Theme.textPrimary)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(.top, 32)

                Text("SafeDrive can't detect drowsiness without the front camera. Turn it on in Settings — footage is never recorded or uploaded.")
                    .font(.sdBody)
                    .lineSpacing(4)
                    .foregroundStyle(Theme.textSecondary)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: 310) // ≈28 characters per line
                    .padding(.top, 12)

                Spacer()

                Button {
                    Haptics.tap()
                    guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
                    UIApplication.shared.open(url)
                } label: {
                    Text("Open Settings")
                }
                .buttonStyle(SDButtonStyle(.gold))
                .padding(.bottom, 16)
            }
            .padding(.horizontal, 32)
        }
    }
}
