import SwiftUI
import AVFoundation

/// Three swipeable pages: what it does → how it warns you → where the data
/// stays. Ends by requesting camera permission and handing off to calibration.
///
/// Composition per the design system: 74pt amber icon → 34pt headline →
/// 16pt body capped at ~26 characters per line → spacer → page indicator →
/// full-width CTA. Pages 1–2 use the ink CTA; page 3 turns amber, because
/// it's the one page that actually asks the user for something.
struct OnboardingView: View {
    let onFinished: () -> Void

    @State private var page = 0
    @State private var cameraDenied = false

    private struct Page {
        let icon: String
        let headline: String
        let body: String
    }

    private let pages: [Page] = [
        Page(
            icon: "eye.fill",
            headline: "Your co-pilot that never blinks",
            body: "SafeDrive watches your eyes and posture in real time, so a moment of fatigue never becomes a crash."
        ),
        Page(
            icon: "bell.fill",
            headline: "A nudge before it's too late",
            body: "Escalating sound and haptics wake you the instant drowsiness or distraction is detected."
        ),
        Page(
            icon: "checkmark.shield.fill",
            headline: "Everything stays on your iPhone",
            body: "Video never leaves the device. Only your trip scores are saved, and only for you."
        ),
    ]

    private var isLastPage: Bool { page == pages.count - 1 }

    var body: some View {
        ZStack(alignment: .topTrailing) {
            Theme.background.ignoresSafeArea()

            // The screen's single ambient bloom, bled off the top-right corner.
            Aura(size: 256)
                .offset(x: 64, y: -40)

            VStack(spacing: 0) {
                TabView(selection: $page) {
                    ForEach(pages.indices, id: \.self) { index in
                        pageView(pages[index]).tag(index)
                    }
                }
                .tabViewStyle(.page(indexDisplayMode: .never))
                .onChange(of: page) { _ in Haptics.tick() }

                VStack(alignment: .leading, spacing: 24) {
                    pageIndicator

                    Button {
                        if isLastPage {
                            requestCameraThenFinish()
                        } else {
                            Haptics.tap()
                            withAnimation(Motion.springy) { page += 1 }
                        }
                    } label: {
                        Text(isLastPage ? "Enable camera" : "Continue")
                            .contentTransition(.opacity)
                    }
                    .buttonStyle(SDButtonStyle(isLastPage ? .gold : .solid))
                    .animation(Motion.quick, value: isLastPage)
                }
                .padding(.horizontal, 28)
                .padding(.bottom, 12)
            }
        }
        .alert("Camera access is required", isPresented: $cameraDenied) {
            Button("Open Settings") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("SafeDrive can't monitor you without the front camera. Enable camera access in Settings.")
        }
    }

    private func pageView(_ page: Page) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Spacer().frame(height: 48)

            // 74pt amber square — the same footprint as an app icon, which is
            // why it carries a 22pt continuous radius rather than a circle.
            Image(systemName: page.icon)
                .font(.system(size: 30, weight: .medium))
                .foregroundStyle(Theme.goldForeground)
                .frame(width: 74, height: 74)
                .background(
                    RoundedRectangle(cornerRadius: Theme.Radius.icon, style: .continuous)
                        .fill(Theme.gold)
                )
                .shadow(color: Theme.gold.opacity(0.5), radius: 22, y: 14)

            Text(page.headline)
                .font(.sdDisplay)
                .tracking(34 * -0.02)
                .lineSpacing(-2)
                .foregroundStyle(Theme.textPrimary)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.top, 36)

            Text(page.body)
                .font(.sdBody)
                .lineSpacing(5)
                .foregroundStyle(Theme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: 300, alignment: .leading) // ≈26 characters per line
                .padding(.top, 16)

            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 28)
    }

    /// The active page's dot stretches into a 24pt amber pill rather than
    /// merely changing color — position stays readable without relying on
    /// the accent hue alone.
    private var pageIndicator: some View {
        HStack(spacing: 6) {
            ForEach(pages.indices, id: \.self) { index in
                Capsule()
                    .fill(index == page ? Theme.gold : Theme.textPrimary.opacity(0.15))
                    .frame(width: index == page ? 24 : 6, height: 6)
            }
        }
        .animation(Motion.springy, value: page)
        .accessibilityHidden(true) // TabView already announces the page position
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
