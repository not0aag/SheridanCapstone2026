import SwiftUI

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
        }
        .animation(.easeInOut(duration: 0.3), value: monitor.phase)
        .animation(.easeInOut(duration: 0.3), value: didOnboard)
        .animation(.easeInOut(duration: 0.3), value: camera.permissionDenied)
        // Presented from the root, not from MonitoringView. `stopMonitoring()`
        // sets `phase = .idle` before publishing the summary, which swaps
        // MonitoringView out for the tab shell — a sheet attached down there
        // would lose its host mid-presentation and never appear. Ending a
        // trip is exactly when the driver expects this, so it has to be
        // hosted by a view that outlives the transition.
        .sheet(item: $monitor.lastTripSummary) { summary in
            TripSummaryView(summary: summary)
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
