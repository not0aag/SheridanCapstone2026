import SwiftUI

/// Design tokens. One place to keep the app visually coherent.
enum Theme {
    static let accent = Color(red: 0.20, green: 0.84, blue: 0.50)   // confident green
    static let danger = Color(red: 0.95, green: 0.26, blue: 0.21)   // drowsy red
    static let warning = Color(red: 1.00, green: 0.62, blue: 0.04)  // distracted orange
    static let background = Color(red: 0.05, green: 0.06, blue: 0.08)
    static let surface = Color(red: 0.11, green: 0.12, blue: 0.15)

    static func color(for state: DriverState) -> Color {
        switch state {
        case .safe: accent
        case .drowsy: danger
        case .distracted: warning
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
