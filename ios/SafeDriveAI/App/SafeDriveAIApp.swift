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
        let contactsStore = LocalContactsStore()
        _settings = StateObject(wrappedValue: settings)
        _calibration = StateObject(wrappedValue: calibration)
        _contactsStore = StateObject(wrappedValue: contactsStore)
        _monitor = StateObject(wrappedValue: DriverMonitor(
            settings: settings, calibration: calibration, contactsStore: contactsStore
        ))
        _account = StateObject(wrappedValue: AccountManager())
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
                .preferredColorScheme(settings.appearanceMode.colorScheme)
                .tint(Theme.accent)
        }
    }
}
