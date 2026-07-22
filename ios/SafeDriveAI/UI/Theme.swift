import SwiftUI
import UIKit

/// "Calm Guardian" design tokens — supportive, not alarming, per the brief.
/// Colors are authored in OKLCH (lightness, chroma, hue) because that's the
/// space the palette was designed in: equal steps in L read as equal steps
/// in perceived brightness, which is why the light/dark pairs below are just
/// re-tuned lightness/chroma on the same hues rather than different colors.
enum Theme {

    // MARK: OKLCH → sRGB

    /// Converts an OKLCH color to sRGB and returns a SwiftUI Color.
    /// `hue` is in degrees, `lightness`/`chroma` as given in the spec
    /// (e.g. oklch(0.7 0.14 60)). Reference: Björn Ottosson's OKLab model.
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

    // MARK: Palette — Calm Guardian

    static let background = dynamic(
        light: oklch(0.97, 0.012, 80),
        dark: oklch(0.20, 0.014, 80)
    )
    static let surface = dynamic(
        light: oklch(0.99, 0.006, 80),
        dark: oklch(0.27, 0.016, 80)
    )
    static let textPrimary = dynamic(
        light: oklch(0.30, 0.02, 80),
        dark: oklch(0.94, 0.01, 80)
    )
    static let textSecondary = dynamic(
        light: oklch(0.50, 0.02, 80),
        dark: oklch(0.72, 0.015, 80)
    )

    /// Safe / calm — sage green.
    static let accent = dynamic(
        light: oklch(0.65, 0.08, 150),
        dark: oklch(0.72, 0.1, 150)
    )
    /// Distracted — warm amber. Correctable in seconds; supportive, not alarming.
    static let warning = dynamic(
        light: oklch(0.7, 0.14, 60),
        dark: oklch(0.75, 0.15, 60)
    )
    /// Drowsy — deeper, more saturated coral-red on the same warm hue family
    /// as amber (not an unrelated red) but pulled toward 30° and given more
    /// chroma/less lightness, so it reads as more urgent than a distraction
    /// alert without breaking the "caring companion" brief.
    static let danger = dynamic(
        light: oklch(0.62, 0.19, 29),
        dark: oklch(0.68, 0.20, 29)
    )

    static func color(for state: DriverState) -> Color {
        switch state {
        case .safe: accent
        case .drowsy: danger
        case .distracted: warning
        }
    }
}

/// Light / Dark / follow-system, user-selectable in Settings.
enum AppearanceMode: String, CaseIterable, Identifiable {
    case system, light, dark

    var id: String { rawValue }

    var label: String {
        switch self {
        case .system: "System"
        case .light: "Light"
        case .dark: "Dark"
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

/// Big rounded primary button used across the app — large tap targets for
/// in-car use.
struct BigButtonStyle: ButtonStyle {
    var color: Color = Theme.accent

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.title3.weight(.bold))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 18)
            .background(color.opacity(configuration.isPressed ? 0.6 : 1))
            .foregroundStyle(.black)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}
