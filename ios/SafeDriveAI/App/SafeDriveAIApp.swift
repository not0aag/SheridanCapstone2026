import SwiftUI

@main
struct SafeDriveAIApp: App {
    @StateObject private var settings: AppSettings
    @StateObject private var calibration: CalibrationManager
    @StateObject private var monitor: DriverMonitor
    @StateObject private var account: AccountManager
    @StateObject private var contactsStore: LocalContactsStore

    init() {
        let settings = AppSettings()
        let calibration = CalibrationManager()
        _settings = StateObject(wrappedValue: settings)
        _calibration = StateObject(wrappedValue: calibration)
        _monitor = StateObject(wrappedValue: DriverMonitor(settings: settings, calibration: calibration))
        _account = StateObject(wrappedValue: AccountManager())
        _contactsStore = StateObject(wrappedValue: LocalContactsStore())
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(settings)
                .environmentObject(calibration)
                .environmentObject(monitor)
                .environmentObject(monitor.camera)
                .environmentObject(account)
                .environmentObject(contactsStore)
                .preferredColorScheme(.dark) // driving app: dark theme always
                .tint(Theme.accent)
        }
    }
}
