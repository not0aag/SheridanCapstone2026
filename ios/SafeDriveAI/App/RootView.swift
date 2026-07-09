import SwiftUI

struct RootView: View {
    @EnvironmentObject private var monitor: DriverMonitor
    @EnvironmentObject private var calibration: CalibrationManager
    @AppStorage("didOnboard") private var didOnboard = false

    var body: some View {
        ZStack {
            Theme.background.ignoresSafeArea()

            if !didOnboard {
                OnboardingView {
                    didOnboard = true
                    monitor.startCalibration()
                }
            } else if monitor.phase == .calibrating {
                CalibrationView()
            } else {
                MonitoringView()
            }
        }
        .animation(.easeInOut(duration: 0.3), value: monitor.phase)
        .animation(.easeInOut(duration: 0.3), value: didOnboard)
    }
}
