import SwiftUI

/// The full-bleed alert that interrupts everything.
///
/// Two severities, deliberately not the same color. The design system
/// reserves `alert` red for drowsiness — the "act now" case — so a
/// distraction alert takes the amber accent instead. Both use the identical
/// composition, so the *layout* never has to be re-read under stress; only
/// the temperature changes to grade the severity.
///
/// This view is presentation only. It never touches `DetectionEngine`,
/// `AlertPlayer`, or the camera: audio and haptics are driven by
/// `DriverMonitor` from `driverState` and keep running regardless of what
/// happens here.
struct AlertOverlayView: View {
    let state: DriverState
    /// Shown beneath the button when a trusted contact will actually be
    /// texted if this continues. Nil hides the line entirely — the app
    /// never claims an escalation that isn't wired up.
    var escalationNote: String?
    /// Acknowledges the alert and drops back to the monitoring screen,
    /// where a persistent banner and the alert sound both continue. This
    /// dismisses the takeover, not the warning.
    let onAcknowledge: () -> Void

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var breathing = false
    @State private var entered = false

    private var isDrowsy: Bool { state == .drowsy }

    private var canvas: Color { isDrowsy ? Theme.alert : Theme.gold }
    /// Ink on the canvas: white on red, near-black on amber. Both clear the
    /// design's 4.6:1 floor for the headline.
    private var ink: Color { isDrowsy ? Theme.onAlert : Theme.goldForeground }

    var body: some View {
        ZStack {
            canvas.ignoresSafeArea()

            // White radial wash from the top, so the badge sits in light and
            // the CTA sits in the denser colour at the bottom.
            RadialGradient(
                colors: [.white.opacity(0.28), .clear],
                center: .top, startRadius: 0, endRadius: 460
            )
            .ignoresSafeArea()
            .allowsHitTesting(false)

            VStack(spacing: 0) {
                Spacer()

                // 104pt glass badge. It breathes rather than flashes —
                // a strobing full-screen red is genuinely hazardous to
                // drive by, and the sound already carries the urgency.
                ZStack {
                    Circle()
                        .fill(.white.opacity(0.2))
                        .frame(width: 104, height: 104)
                    Image(systemName: isDrowsy ? "eye.fill" : "eye.trianglebadge.exclamationmark.fill")
                        .font(.system(size: 44, weight: .regular))
                        .foregroundStyle(ink)
                }
                .scaleEffect(breathing ? 1.06 : 1)
                .opacity(breathing ? 0.9 : 0.7)

                Text(isDrowsy ? "WAKE UP" : "EYES ON THE ROAD")
                    .font(.system(size: 52, weight: .bold))
                    .tracking(52 * -0.02)
                    .minimumScaleFactor(0.55)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(ink)
                    .padding(.top, 36)

                Text(isDrowsy
                     ? "Your eyes have been closing. Find a safe place to pull over now."
                     : "You've been looking away from the road. Eyes up.")
                    .font(.sdBody)
                    .lineSpacing(5)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(ink.opacity(0.85))
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: 290) // ≈24 characters per line
                    .padding(.top, 16)

                Spacer()

                VStack(spacing: 12) {
                    Button {
                        Haptics.tap(.medium)
                        onAcknowledge()
                    } label: {
                        Text(isDrowsy ? "I'm awake" : "Got it")
                    }
                    .buttonStyle(AlertAcknowledgeButtonStyle(ink: canvas))

                    if let escalationNote {
                        Text(escalationNote)
                            .font(.sdCaption.weight(.medium))
                            .foregroundStyle(ink.opacity(0.7))
                            .multilineTextAlignment(.center)
                    }
                }
                .padding(.bottom, 12)
            }
            .padding(.horizontal, 28)
        }
        // The one abrupt transition in the app: 1.04 → 1 over 220ms.
        .scaleEffect(entered ? 1 : 1.04)
        .opacity(entered ? 1 : 0)
        .onAppear {
            withAnimation(Motion.alertImpact) { entered = true }
            guard !reduceMotion else { return }
            withAnimation(Motion.breathe) { breathing = true }
        }
        // One element, one announcement — VoiceOver shouldn't have to walk a
        // stack of labels during an emergency.
        .accessibilityElement(children: .contain)
        .accessibilityAddTraits(.isModal)
    }
}

/// White pill on the alert canvas, taking the canvas colour as its ink so
/// one style serves both the red and amber severities.
private struct AlertAcknowledgeButtonStyle: ButtonStyle {
    let ink: Color

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.sdButton)
            .foregroundStyle(ink)
            .frame(maxWidth: .infinity, minHeight: 52)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                    .fill(.white)
            )
            .opacity(configuration.isPressed ? 0.85 : 1)
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}
