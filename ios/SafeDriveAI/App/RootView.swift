import SwiftUI
import MessageUI

/// Top-level routing.
///
/// Two shapes of UI, chosen by what the driver is doing:
/// - **At rest** — a standard tab shell (Drive · Trips · Settings).
/// - **In a trip, or calibrating** — full screen, no chrome. Tabs while
///   driving would invite exactly the interaction this app exists to
///   prevent, so they're removed for the duration, the same way Maps drops
///   its chrome once navigation starts.
struct RootView: View {
    @EnvironmentObject private var monitor: DriverMonitor
    @EnvironmentObject private var camera: CameraService
    @AppStorage("didOnboard") private var didOnboard = false

    /// Shared across CalibrationView and MonitoringView so the calibration
    /// progress ring can morph directly into the monitoring status pill via
    /// matchedGeometryEffect when `monitor.phase` flips, instead of a flat
    /// cut between the two screens.
    @Namespace private var statusTransition

    /// Holds the SwiftUI splash on top a little longer than the native
    /// static launch screen alone would show it for — that one dismisses
    /// the instant the app is interactive, which for a small SwiftUI app is
    /// almost immediately. This makes the brand moment actually register
    /// instead of flashing for a frame or two.
    @State private var showingSplash = true

    private var isDriving: Bool {
        switch monitor.phase {
        case .monitoring, .paused: return true
        case .idle, .calibrating: return false
        }
    }

    var body: some View {
        ZStack {
            Theme.background.ignoresSafeArea()

            if camera.permissionDenied {
                CameraPermissionDeniedView()
            } else if !didOnboard {
                OnboardingView {
                    didOnboard = true
                    monitor.startCalibration()
                }
            } else if monitor.phase == .calibrating {
                CalibrationView(namespace: statusTransition)
            } else if isDriving {
                MonitoringView(namespace: statusTransition)
            } else {
                MainTabView()
            }

            if showingSplash {
                SplashView()
                    .transition(.opacity)
                    .zIndex(10)
            }
        }
        .animation(.easeInOut(duration: 0.3), value: monitor.phase)
        .animation(.easeInOut(duration: 0.3), value: didOnboard)
        .animation(.easeInOut(duration: 0.3), value: camera.permissionDenied)
        .task {
            // The real content underneath is already mounted and ready
            // during this hold — nothing is being blocked or delayed by it,
            // this is purely the brand moment lasting long enough to see.
            try? await Task.sleep(for: .milliseconds(1200))
            withAnimation(.easeOut(duration: 0.35)) { showingSplash = false }
        }
        // Presented from the root, not from MonitoringView. `stopMonitoring()`
        // sets `phase = .idle` before publishing the summary, which swaps
        // MonitoringView out for the tab shell — a sheet attached down there
        // would lose its host mid-presentation and never appear. Ending a
        // trip is exactly when the driver expects this, so it has to be
        // hosted by a view that outlives the transition.
        .sheet(item: $monitor.lastTripSummary) { summary in
            TripSummaryView(summary: summary)
        }
        // Same reasoning: hosted here, not under MonitoringView, so the
        // composer can still present when a driver tests their Trusted
        // Contacts setup from Settings while parked — MonitoringView isn't
        // even in the hierarchy then. DriverMonitor already gates on
        // MFMessageComposeViewController.canSendText() before ever setting
        // this, so by the time it's non-nil it's known presentable.
        .sheet(item: $monitor.pendingMessageComposer) { draft in
            MessageComposerView(draft: draft) { monitor.pendingMessageComposer = nil }
        }
    }
}

/// Drive · Trips · Settings. Amber marks the active tab — the design system
/// permits the accent hue here precisely because it signals position rather
/// than decorating.
private struct MainTabView: View {
    @EnvironmentObject private var monitor: DriverMonitor

    var body: some View {
        TabView {
            DriveHomeView()
                .tabItem { Label("Drive", systemImage: "steeringwheel") }

            TripHistoryView(tripLog: monitor.tripLog)
                .tabItem { Label("Trips", systemImage: "chart.bar.fill") }

            SettingsView(embedded: true)
                .tabItem { Label("Settings", systemImage: "gearshape.fill") }
        }
        .tint(Theme.gold)
    }
}
