import SwiftUI

@main
struct SafeDriveAIApp: App {
    @StateObject private var settings: AppSettings
    @StateObject private var calibration: CalibrationManager
    @StateObject private var monitor: DriverMonitor

    init() {
        let settings = AppSettings()
        let calibration = CalibrationManager()
        _settings = StateObject(wrappedValue: settings)
        _calibration = StateObject(wrappedValue: calibration)
        _monitor = StateObject(wrappedValue: DriverMonitor(settings: settings, calibration: calibration))
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(settings)
                .environmentObject(calibration)
                .environmentObject(monitor)
                .preferredColorScheme(.dark) // driving app: dark theme always
                .tint(Theme.accent)
        }
    }
}
