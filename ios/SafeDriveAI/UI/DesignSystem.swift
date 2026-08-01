import SwiftUI

/// The Golden Hour component inventory. Every screen composes from these —
/// no screen invents its own card, ring, pill or button. Tokens come from
/// `Theme`; nothing here hardcodes a color.
///
/// Motion here honours Reduce Motion: the breathe and drift loops freeze,
/// while anything with a meaningful end state (the score ring) keeps its
/// final value rather than disappearing.

// MARK: - Aura

/// Ambient warm bloom behind hero moments. One per screen, maximum — it's
/// atmosphere, not decoration, and two of them cancel each other out.
struct Aura: View {
    var size: CGFloat = 260
    var opacity: Double = 0.25

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var drifted = false

    var body: some View {
        Circle()
            .fill(Theme.gold.opacity(opacity))
            .frame(width: size, height: size)
            .blur(radius: size * 0.28)
            // 14s drift, ±14pt Y, with a matching gentle scale.
            .offset(y: drifted ? -14 : 0)
            .scaleEffect(drifted ? 1.05 : 1)
            .allowsHitTesting(false)
            .accessibilityHidden(true)
            .onAppear {
                guard !reduceMotion else { return }
                withAnimation(Motion.drift) { drifted = true }
            }
    }
}

// MARK: - Status pill

/// The always-visible state word plus a breathing dot. The word carries the
/// state on its own — color is never the only signal (see the design's
/// accessibility rules).
struct StatusPill: View {
    enum Tone {
        case safe, gold, alert

        var color: Color {
            switch self {
            case .safe: Theme.safe
            case .gold: Theme.gold
            case .alert: Theme.alert
            }
        }

        /// Text color on the tinted pill. Gold's own value is too light to
        /// read at 11pt on a 15%-alpha fill, so it borrows the banner ink.
        var ink: Color {
            switch self {
            case .safe: Theme.safe
            case .gold: Theme.onGoldSoft
            case .alert: Theme.alert
            }
        }
    }

    let label: String
    var tone: Tone = .safe

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var breathing = false

    var body: some View {
        HStack(spacing: 8) {
            ZStack {
                // Halo: the part that actually breathes, so the solid dot
                // stays legible at a glance while the pill still feels alive.
                Circle()
                    .fill(tone.color)
                    .frame(width: 6, height: 6)
                    .scaleEffect(breathing ? 1.06 : 1)
                    .opacity(breathing ? 0.9 : 0.45)
                Circle()
                    .fill(tone.color)
                    .frame(width: 6, height: 6)
            }
            Text(label)
                .font(.sdSectionLabel)
                .textCase(.uppercase)
                .tracking(11 * 0.12)
        }
        .foregroundStyle(tone.ink)
        .padding(.horizontal, 12)
        .padding(.vertical, 7)
        .background(tone.color.opacity(tone == .gold ? 0.15 : 0.12), in: Capsule())
        .onAppear {
            guard !reduceMotion else { return }
            withAnimation(Motion.breathe) { breathing = true }
        }
    }
}

// MARK: - Score ring

/// Gold→green gradient ring with an amber bloom behind it. One VoiceOver
/// element ("Safety score 92 out of 100"), never a pile of separate labels.
struct ScoreRing: View {
    let value: Int
    var size: CGFloat = 168
    var caption: String = "Safety score"

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var shown = false

    private var stroke: CGFloat { size * (12.0 / 168.0) }
    private var progress: Double { min(max(Double(value) / 100, 0), 1) }

    var body: some View {
        ZStack {
            Circle()
                .fill(Theme.gold.opacity(0.25))
                .padding(size * 0.07)
                .blur(radius: size * 0.13)

            Circle()
                .strokeBorder(Theme.hairline, lineWidth: stroke)

            Circle()
                .inset(by: stroke / 2)
                .trim(from: 0, to: shown ? progress : 0)
                .stroke(
                    LinearGradient(
                        colors: [Theme.gold, Theme.safe],
                        startPoint: .topLeading, endPoint: .bottomTrailing
                    ),
                    style: StrokeStyle(lineWidth: stroke, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))

            VStack(spacing: 4) {
                Text("\(value)")
                    .font(.system(size: size * (52.0 / 168.0), weight: .semibold))
                    .monospacedDigit()
                    .foregroundStyle(Theme.textPrimary)
                Text(caption)
                    .sdHeroLabel()
            }
        }
        .frame(width: size, height: size)
        .onAppear {
            // Reduce Motion keeps the ring's final state — the value is the
            // point of the component; only the reveal is decoration.
            if reduceMotion {
                shown = true
            } else {
                withAnimation(Motion.ringOpen) { shown = true }
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(caption) \(value) out of 100")
    }
}

// MARK: - Buttons

enum SDButtonVariant {
    /// Ink on paper by day, paper on ink at night. The default CTA.
    case solid
    /// Amber. Reserved for the one action a screen actually wants.
    case gold
    /// Recessed. For secondary or destructive-but-calm actions ("End trip").
    case quiet
    /// White on the full-bleed alert screen.
    case onAlert

    var fill: Color {
        switch self {
        case .solid: Theme.primary
        case .gold: Theme.gold
        case .quiet: Theme.surface2
        case .onAlert: .white
        }
    }

    var ink: Color {
        switch self {
        case .solid: Theme.primaryForeground
        case .gold: Theme.goldForeground
        case .quiet: Theme.textPrimary
        case .onAlert: Theme.alert
        }
    }
}

/// 52pt tall, 16pt corners. Elevated variants get a shadow; `quiet` gets a
/// hairline ring instead, per the "no shadows on flat surfaces" rule.
struct SDButtonStyle: ButtonStyle {
    var variant: SDButtonVariant = .solid

    init(_ variant: SDButtonVariant = .solid) {
        self.variant = variant
    }

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.sdButton)
            .foregroundStyle(variant.ink)
            .frame(maxWidth: .infinity, minHeight: 52)
            .background(
                RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                    .fill(variant.fill)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Theme.Radius.control, style: .continuous)
                    .strokeBorder(Theme.hairline, lineWidth: variant == .quiet ? 1 : 0)
            )
            .shadow(
                color: variant == .gold ? Theme.gold.opacity(0.45) : .clear,
                radius: 20, x: 0, y: 10
            )
            .opacity(configuration.isPressed ? 0.85 : 1)
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}

/// Compatibility shim for call sites written against the previous design
/// system. New code should use `SDButtonStyle` directly.
struct BigButtonStyle: ButtonStyle {
    var color: Color?

    init(color: Color? = nil) {
        self.color = color
    }

    func makeBody(configuration: Configuration) -> some View {
        let variant: SDButtonVariant = {
            guard let color else { return .solid }
            // Map the old per-color API onto the new variants.
            return color == Theme.gold ? .gold : .quiet
        }()
        return SDButtonStyle(variant).makeBody(configuration: configuration)
    }
}

// MARK: - List group + row

/// A grouped inset list section: uppercase header, hairline-ringed card,
/// optional footer. Matches iOS's grouped-inset rhythm without inheriting
/// `Form`'s system chrome, which fights this palette.
struct ListGroup<Content: View>: View {
    var header: String?
    var footer: String?
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if let header {
                Text(header)
                    .sdSectionLabel()
                    .padding(.horizontal, 16)
            }
            VStack(spacing: 0) { content }
                .sdCard()
            if let footer {
                Text(footer)
                    .font(.sdMeta)
                    .foregroundStyle(Theme.textSecondary)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(.horizontal, 16)
            }
        }
    }
}

/// One row inside a `ListGroup`. 44pt minimum height — the design's tap
/// target floor, and iOS's.
struct SDRow<Trailing: View>: View {
    let title: String
    var detail: String?
    var last: Bool = false
    @ViewBuilder var trailing: Trailing

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.sdRow)
                        .foregroundStyle(Theme.textPrimary)
                    if let detail {
                        Text(detail)
                            .font(.sdMeta)
                            .foregroundStyle(Theme.textSecondary)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                trailing
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .frame(minHeight: 44)

            if !last {
                Rectangle()
                    .fill(Theme.hairline)
                    .frame(height: 1)
                    .padding(.leading, 16)
            }
        }
    }
}

extension SDRow where Trailing == EmptyView {
    init(title: String, detail: String? = nil, last: Bool = false) {
        self.init(title: title, detail: detail, last: last) { EmptyView() }
    }
}

/// The chevron used on rows that push a new screen.
struct SDDisclosure: View {
    var body: some View {
        Image(systemName: "chevron.right")
            .font(.system(size: 13, weight: .semibold))
            .foregroundStyle(Theme.textSecondary)
    }
}

// MARK: - Stat card

/// The small three-up metric card used on trip summary and trip history.
struct StatCard: View {
    let value: String
    let label: String
    var tint: Color?

    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.sdScore)
                .monospacedDigit()
                .foregroundStyle(tint ?? Theme.textPrimary)
            Text(label)
                .sdStatLabel()
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
        .padding(.horizontal, 6)
        .sdCard(radius: Theme.Radius.control)
    }
}

// MARK: - Slider

/// A labelled sensitivity slider. Wraps the *system* `Slider` deliberately:
/// it brings drag behaviour, Dynamic Type and VoiceOver's adjustable trait
/// for free, and tinting it gold matches the design without reimplementing
/// any of that.
struct SDSlider: View {
    @Binding var value: Double
    var range: ClosedRange<Double> = 0...1
    var step: Double?
    let labels: (String, String, String)
    /// Index 0/1/2 of the label the current value falls under — bolded so
    /// the position is readable without interpreting the track.
    var activeIndex: Int

    var body: some View {
        VStack(spacing: 10) {
            Group {
                if let step {
                    Slider(value: $value, in: range, step: step)
                } else {
                    Slider(value: $value, in: range)
                }
            }
            .tint(Theme.gold)

            HStack {
                labelText(labels.0, index: 0)
                Spacer()
                labelText(labels.1, index: 1)
                Spacer()
                labelText(labels.2, index: 2)
            }
            .accessibilityHidden(true) // the Slider itself is the control
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
    }

    private func labelText(_ text: String, index: Int) -> some View {
        Text(text)
            .font(.system(size: 10, weight: .semibold))
            .textCase(.uppercase)
            .tracking(10 * 0.12)
            .foregroundStyle(index == activeIndex ? Theme.textPrimary : Theme.textSecondary)
    }
}

// MARK: - Segmented control

/// Custom segmented control matching the design's 12pt trough / 9pt thumb.
/// Built from real `Button`s carrying `.isSelected`, so VoiceOver reads it
/// the same way the system control would.
struct SDSegmented<Value: Hashable>: View {
    let options: [(value: Value, label: String)]
    @Binding var selection: Value
    var onChange: (() -> Void)?

    @Namespace private var thumb

    var body: some View {
        HStack(spacing: 4) {
            ForEach(options, id: \.value) { option in
                let isActive = option.value == selection
                Button {
                    guard !isActive else { return }
                    withAnimation(Motion.quick) { selection = option.value }
                    onChange?()
                } label: {
                    Text(option.label)
                        .font(.sdCaption.weight(.medium))
                        .foregroundStyle(isActive ? Theme.textPrimary : Theme.textSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 7)
                        .background {
                            if isActive {
                                RoundedRectangle(cornerRadius: 9, style: .continuous)
                                    .fill(Theme.surface)
                                    .shadow(color: .black.opacity(0.08), radius: 3, y: 1)
                                    .matchedGeometryEffect(id: "segmentThumb", in: thumb)
                            }
                        }
                }
                .buttonStyle(.plain)
                .accessibilityLabel(option.label)
                .accessibilityAddTraits(isActive ? [.isSelected, .isButton] : .isButton)
            }
        }
        .padding(4)
        .background(Theme.muted, in: RoundedRectangle(cornerRadius: Theme.Radius.inner, style: .continuous))
        .padding(12)
    }
}

// MARK: - Sheet grabber

struct SheetGrabber: View {
    var body: some View {
        Capsule()
            .fill(Theme.textPrimary.opacity(0.2))
            .frame(width: 36, height: 5)
            .frame(height: 24)
            .accessibilityHidden(true)
    }
}

// MARK: - Screen scaffolding

/// A large screen title, matching the design's 28pt bold NavBar.
struct SDNavTitle<Trailing: View>: View {
    let title: String
    @ViewBuilder var trailing: Trailing

    var body: some View {
        HStack {
            Text(title)
                .font(.sdTitle)
                .foregroundStyle(Theme.textPrimary)
            Spacer()
            trailing
        }
        .padding(.horizontal, 20)
        .padding(.bottom, 8)
    }
}

extension SDNavTitle where Trailing == EmptyView {
    init(_ title: String) {
        self.init(title: title) { EmptyView() }
    }
}

/// The 36pt translucent circular glyph button used for Settings and Close.
struct SDCircleButton: View {
    let systemName: String
    var tint: Color = Theme.textSecondary
    var background: Color?
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(tint)
                .frame(width: 36, height: 36)
                .background {
                    Circle()
                        .fill(background ?? Theme.surface2)
                        .overlay(Circle().strokeBorder(Theme.hairline, lineWidth: background == nil ? 1 : 0))
                }
                // The glyph is 36pt but the tap target must clear 44pt.
                .contentShape(Circle().inset(by: -4))
        }
        .buttonStyle(.plain)
    }
}
