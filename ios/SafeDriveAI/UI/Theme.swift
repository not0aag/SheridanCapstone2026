import SwiftUI
import UIKit

/// "Golden Hour" design tokens — driving at golden hour into dusk. Light
/// theme is warm morning light across the dash (never sterile white); dark
/// theme is a deep cabin at night where every instrument quietly glows.
/// Two moods of one identity, not an inversion.
///
/// Colors are authored in OKLCH (lightness, chroma, hue) because that's the
/// space the palette was designed in: equal steps in L read as equal steps
/// in perceived brightness, which is why the light/dark pairs below are
/// re-tuned lightness/chroma on shared hues rather than different colors.
/// Values are copied verbatim from the design system's token sheet — do not
/// hand-tune a hex here; change the token.
///
/// Rules this palette encodes:
/// - Exactly one accent hue: amber (`gold`). It marks progress, calibration
///   and the active tab. It never decorates.
/// - `safe` (green) means "you're fine". `alert` (red) means "act now".
///   Never mix the two.
/// - No shadows on flat surfaces — use `hairline` 1px rings. Shadows belong
///   only to elevated things (acting buttons, sheets, slider thumbs).
enum Theme {

    // MARK: OKLCH → sRGB

    /// Converts an OKLCH color to sRGB and returns a SwiftUI Color.
    /// `hue` is in degrees, `lightness`/`chroma` as given in the spec
    /// (e.g. oklch(0.78 0.16 72)). Reference: Björn Ottosson's OKLab model.
    ///
    /// Out-of-gamut colors are clamped per channel, which shifts hue slightly
    /// for the most saturated tokens (notably `alert`). That's accepted: the
    /// alternative — proper gamut mapping — would change the designed colors
    /// more than the clamp does at these chroma levels.
    static func oklch(_ lightness: Double, _ chroma: Double, _ hue: Double, opacity: Double = 1) -> Color {
        let h = hue * .pi / 180
        let a = chroma * cos(h)
        let b = chroma * sin(h)

        let l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
        let m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
        let s_ = lightness - 0.0894841775 * a - 1.2914855480 * b

        let l = l_ * l_ * l_
        let m = m_ * m_ * m_
        let s = s_ * s_ * s_

        let r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
        let g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
        let bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

        func gamma(_ c: Double) -> Double {
            let clamped = min(max(c, 0), 1)
            return clamped <= 0.0031308 ? 12.92 * clamped : 1.055 * pow(clamped, 1 / 2.4) - 0.055
        }

        return Color(.sRGB, red: gamma(r), green: gamma(g), blue: gamma(bl), opacity: opacity)
    }

    /// A color that switches between a light- and dark-appearance value,
    /// following whatever trait collection is in effect — system setting by
    /// default, or overridden by `.preferredColorScheme` when the user picks
    /// Light/Dark explicitly in Settings (see AppSettings.appearanceMode).
    static func dynamic(light: Color, dark: Color) -> Color {
        Color(UIColor { traits in
            traits.userInterfaceStyle == .dark ? UIColor(dark) : UIColor(light)
        })
    }

    // MARK: Surfaces

    /// Screen base. Warm off-white by day, deep blue-black cabin at night.
    static let background = dynamic(
        light: oklch(0.985, 0.008, 85),
        dark: oklch(0.16, 0.014, 265)
    )
    /// Cards and list groups — sits one step above `background`.
    static let surface = dynamic(
        light: oklch(1, 0.003, 85),
        dark: oklch(0.215, 0.016, 265)
    )
    /// Quiet buttons and wells — one step above `surface` in dark, one step
    /// *below* in light, so a quiet control always reads as recessed.
    static let surface2 = dynamic(
        light: oklch(0.965, 0.012, 84),
        dark: oklch(0.25, 0.018, 265)
    )
    /// Segmented-control troughs and slider tracks.
    static let muted = dynamic(
        light: oklch(0.955, 0.012, 85),
        dark: oklch(0.26, 0.018, 265)
    )
    /// 1px separators and card rings. Replaces shadows on flat surfaces.
    static let hairline = dynamic(
        light: oklch(0.9, 0.012, 82),
        dark: Color.white.opacity(0.08)
    )

    // MARK: Text

    static let textPrimary = dynamic(
        light: oklch(0.21, 0.015, 65),
        dark: oklch(0.975, 0.004, 85)
    )
    static let textSecondary = dynamic(
        light: oklch(0.55, 0.02, 70),
        dark: oklch(0.68, 0.02, 265)
    )

    // MARK: Accent — amber, the only accent hue in the system

    /// Progress, calibration, the active tab. Never decorative.
    static let gold = dynamic(
        light: oklch(0.78, 0.16, 72),
        dark: oklch(0.84, 0.15, 80)
    )
    /// Fill behind amber info banners.
    static let goldSoft = dynamic(
        light: oklch(0.94, 0.06, 84),
        dark: oklch(0.32, 0.06, 76)
    )
    /// Ink that sits *on* a solid `gold` fill.
    static let goldForeground = dynamic(
        light: oklch(0.25, 0.05, 62),
        dark: oklch(0.18, 0.03, 70)
    )
    /// Text and glyphs on a `goldSoft` banner — deliberately not
    /// `goldForeground`, which is tuned for the far brighter solid fill.
    static let onGoldSoft = dynamic(
        light: oklch(0.35, 0.09, 62),
        dark: oklch(0.88, 0.13, 82)
    )
    /// Stroke for the calibration face mesh and its breathing ring. Burnt
    /// and much darker by day so 1px lines survive on the warm gradient
    /// wash; the ordinary glowing gold at night. Using `gold` in light mode
    /// makes the mesh almost invisible against that wash.
    static let mesh = dynamic(
        light: oklch(0.50, 0.15, 60),
        dark: oklch(0.84, 0.15, 80)
    )

    // MARK: State

    /// Alert-free, good score. "You're fine."
    static let safe = dynamic(
        light: oklch(0.68, 0.15, 155),
        dark: oklch(0.76, 0.16, 158)
    )
    /// Drowsy alert only. "Act now." Identical in both themes — an emergency
    /// shouldn't change temperature with the time of day.
    static let alert = oklch(0.62, 0.22, 27)
    /// Text and glyphs on a solid `alert` fill.
    static let onAlert = oklch(0.99, 0.01, 80)

    // MARK: Primary CTA — ink on paper by day, paper on ink at night

    static let primary = dynamic(
        light: oklch(0.24, 0.02, 60),
        dark: oklch(0.97, 0.005, 85)
    )
    static let primaryForeground = dynamic(
        light: oklch(0.99, 0.008, 85),
        dark: oklch(0.18, 0.015, 265)
    )

    // MARK: Semantic aliases

    /// Safe / calm. Kept as `accent` so existing call sites and the app-wide
    /// `.tint` keep working after the palette swap.
    static var accent: Color { safe }
    /// Distraction — correctable in seconds, so it takes the amber accent
    /// rather than the red reserved for "act now".
    static var warning: Color { gold }
    /// Drowsiness — the only thing in the app allowed to use `alert` red.
    static var danger: Color { alert }

    static func color(for state: DriverState) -> Color {
        switch state {
        case .safe: safe
        case .drowsy: alert
        case .distracted: gold
        }
    }

    // MARK: Corner radii — corners nest, never collide
    //
    // device 49 → sheet 26 → card 18 → control 16 → inner 12. A card inside
    // a sheet uses `card`; a control inside that card uses `control`.
    enum Radius {
        static let sheet: CGFloat = 26
        static let card: CGFloat = 18
        static let control: CGFloat = 16
        static let inner: CGFloat = 12
        /// Onboarding's 74pt app-icon-style square.
        static let icon: CGFloat = 22
    }
}

// MARK: - Typography

/// The type scale, as named roles rather than raw sizes, so a screen never
/// invents its own. SF Pro throughout (the system face) — `.rounded` and
/// other designs are deliberately absent from this system.
///
/// ## Why these are text styles, not point sizes
///
/// The design sheet specifies this scale in points (34 / 28 / 17 / 16 / 15
/// / 13 / 12 / 11). Every one of those lands on an Apple text style at its
/// default size, so the roles below are expressed as text styles instead of
/// `.system(size:)`. That buys Dynamic Type for free: a driver who has
/// bumped their text size — extremely common in the over-50 cohort most
/// exposed to fatigue crashes — gets larger type everywhere, which
/// `.system(size:)` would have silently refused to do.
///
/// The hero numerals are the deliberate exception: they stay at fixed
/// points, because a 68pt timer scaled to accessibility sizes would push
/// the stat cards off screen. They're paired with `minimumScaleFactor` at
/// their call sites instead, the same trade-off Apple's own Clock app makes.
extension Font {
    /// 34pt Bold — onboarding headlines. (`.largeTitle`)
    static let sdDisplay = Font.largeTitle.weight(.bold)
    /// 28pt Bold — screen (large) titles. (`.title`)
    static let sdTitle = Font.title.weight(.bold)
    /// 52pt Semibold — score numerals. Fixed; pair with `.monospacedDigit()`.
    static let sdHeroNumeral = Font.system(size: 52, weight: .semibold)
    /// 68pt Semibold — the trip timer. Fixed; pair with `.monospacedDigit()`.
    static let sdTimer = Font.system(size: 68, weight: .semibold)
    /// 17pt Semibold — the emphasized line in a two-line caption block.
    static let sdLead = Font.headline
    /// Body copy. (`.body`)
    static let sdBody = Font.body
    /// 15pt Medium — list row titles. (`.subheadline`)
    static let sdRow = Font.subheadline.weight(.medium)
    /// 13pt — captions and row detail. (`.footnote`)
    static let sdCaption = Font.footnote
    /// 12pt — the smallest supporting text. (`.caption`)
    static let sdMeta = Font.caption
    /// 11pt Semibold UPPERCASE — section labels. Always applied through the
    /// `.sdSectionLabel()` modifier, which adds the casing and tracking.
    static let sdSectionLabel = Font.caption2.weight(.semibold)
    /// Button labels. (`.body` Semibold)
    static let sdButton = Font.body.weight(.semibold)
    /// 20pt Semibold — the value in a monitoring stat card. (`.title3`)
    static let sdStatValue = Font.title3.weight(.semibold)
    /// 19pt Semibold — trip scores and small stat-card numerals.
    static let sdScore = Font.title3.weight(.semibold)
}

extension View {
    /// 11pt Semibold, uppercase, 0.14em tracking — the system's one and only
    /// section-label treatment.
    func sdSectionLabel() -> some View {
        self.font(.sdSectionLabel)
            .textCase(.uppercase)
            .tracking(11 * 0.14)
            .foregroundStyle(Theme.textSecondary)
    }

    /// Uppercase, wider 0.18em tracking — the label used under hero numerals
    /// (score ring caption, "TRIP DURATION").
    func sdHeroLabel() -> some View {
        self.font(.sdSectionLabel)
            .textCase(.uppercase)
            .tracking(11 * 0.18)
            .foregroundStyle(Theme.textSecondary)
    }

    /// The smallest label in the system — stat-card captions. Uppercase,
    /// 0.1em tracking.
    func sdStatLabel() -> some View {
        self.font(.sdSectionLabel)
            .textCase(.uppercase)
            .tracking(10 * 0.1)
            .foregroundStyle(Theme.textSecondary)
    }

    /// The system's flat-surface treatment: fill + 1px hairline ring, no
    /// shadow. Every card, list group and well goes through this.
    func sdCard(radius: CGFloat = Theme.Radius.card, fill: Color = Theme.surface) -> some View {
        self.background(fill, in: RoundedRectangle(cornerRadius: radius, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: radius, style: .continuous)
                    .strokeBorder(Theme.hairline, lineWidth: 1)
            )
    }
}

/// Light / Dark / follow-system, user-selectable in Settings.
enum AppearanceMode: String, CaseIterable, Identifiable {
    // Declaration order drives the segmented control, which the design
    // specifies as Light · Dark · Auto. Raw values are unchanged, so
    // previously persisted settings still decode.
    case light, dark, system

    var id: String { rawValue }

    /// Order and wording match the design's segmented control: Light · Dark · Auto.
    var label: String {
        switch self {
        case .light: "Light"
        case .dark: "Dark"
        case .system: "Auto"
        }
    }

    /// nil tells SwiftUI to follow the system setting.
    var colorScheme: ColorScheme? {
        switch self {
        case .system: nil
        case .light: .light
        case .dark: .dark
        }
    }
}

/// Named, reused motion curves so timing is consistent across the app
/// instead of re-invented per view. Durations come from the design system's
/// motion table.
enum Motion {
    /// Default spring for low-stakes UI: onboarding, calibration, settings.
    static let springy = Animation.spring(response: 0.45, dampingFraction: 0.75)
    /// Snappy, small-scale feedback (button presses, page dots).
    static let quick = Animation.spring(response: 0.25, dampingFraction: 0.8)
    /// Status-pill dot: 3.6s ease-in-out breathe, opacity .45→.9, scale 1→1.06.
    static let breathe = Animation.easeInOut(duration: 3.6).repeatForever(autoreverses: true)
    /// Ambient aura: 14s drift, ±14pt Y. The design's own cubic-bezier
    /// (.32,.72,0,1) expressed as a SwiftUI timing curve.
    static let drift = Animation.timingCurve(0.32, 0.72, 0, 1, duration: 14)
        .repeatForever(autoreverses: true)
    /// Score ring easing itself open on appear — 900ms, settles without overshoot.
    static let ringOpen = Animation.easeOut(duration: 0.9)
    /// Alert entry: scale 1.04 → 1 + opacity over 220ms. The only abrupt
    /// transition in the app, and deliberately NOT a playful bounce — a
    /// lower damping fraction would read as cheerful, which is wrong for a
    /// drowsiness warning.
    static let alertImpact = Animation.easeOut(duration: 0.22)
    /// Legacy alias kept so older call sites still read correctly.
    static let ambient = breathe
}

/// Thin wrapper over UIKit's feedback generators so call sites read as
/// intent ("Haptics.tick()") rather than boilerplate. Purely View-layer UI
/// feedback — distinct from AlertPlayer's own continuous haptic loop used
/// during an active DROWSY/DISTRACTED alert, which this never touches.
enum Haptics {
    static func tick() {
        UISelectionFeedbackGenerator().selectionChanged()
    }
    static func tap(_ style: UIImpactFeedbackGenerator.FeedbackStyle = .light) {
        UIImpactFeedbackGenerator(style: style).impactOccurred()
    }
    static func success() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }
    static func warning() {
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
    }
}
