import SwiftUI

/// The SwiftUI extension of the native launch screen.
///
/// iOS dismisses the actual static `UILaunchScreen` the instant the app
/// becomes interactive — for an app this size that's nearly immediate, too
/// fast to register as a moment. `RootView` holds this on top for a short,
/// fixed duration and then fades it away, so it reads identically to the
/// native launch screen (same background color, same logo, same position)
/// but actually lasts long enough to see.
///
/// Deliberately identical to the native launch screen rather than a
/// different "loading" design — this is not communicating progress or
/// doing real work, it's a continuation of the same brand moment. `Image`
/// reads the same `LaunchLogo` asset the native launch screen uses,
/// including its dark-appearance variant, so the two are visually
/// seamless.
struct SplashView: View {
    var body: some View {
        Color("LaunchBackground")
            .ignoresSafeArea()
            .overlay {
                Image("LaunchLogo")
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(maxWidth: 280)
            }
            .accessibilityHidden(true)
    }
}
