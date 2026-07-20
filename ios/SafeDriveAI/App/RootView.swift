import SwiftUI

struct RootView: View {
    @EnvironmentObject private var monitor: DriverMonitor
    @EnvironmentObject private var calibration: CalibrationManager
    @EnvironmentObject private var camera: CameraService
    @AppStorage("didOnboard") private var didOnboard = false

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
                CalibrationView()
            } else {
                MonitoringView()
            }
        }
        .animation(.easeInOut(duration: 0.3), value: monitor.phase)
        .animation(.easeInOut(duration: 0.3), value: didOnboard)
        .animation(.easeInOut(duration: 0.3), value: camera.permissionDenied)
    }
}
