import SwiftUI

/// Settings, in the design's section order: Detection → Alerts →
/// Appearance → Camera, then the app's own extras.
///
/// Built on a real `List` with the system background hidden rather than
/// hand-rolled rows: every control here (toggles, sliders, navigation
/// links) keeps its native behaviour, Dynamic Type and VoiceOver support,
/// and only the surfaces are restyled.
///
/// Reachable two ways — as the Settings tab when parked (`embedded`), and
/// as a sheet from the monitoring screen, which is why the Done button is
/// conditional.
struct SettingsView: View {
    /// True when hosted by the tab bar, where a Done button would be wrong.
    var embedded = false

    @EnvironmentObject private var settings: AppSettings
    @EnvironmentObject private var calibration: CalibrationManager
    @EnvironmentObject private var monitor: DriverMonitor
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.background.ignoresSafeArea()
                content
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(embedded ? .large : .inline)
            .toolbar {
                if !embedded {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Done") { dismiss() }
                    }
                }
            }
        }
    }

    private var content: some View {
        List {
            Section {
                SensitivityRow(
                    title: "Drowsiness",
                    value: $settings.drowsinessSensitivity,
                    detail: "How much eye closure counts as drowsy."
                )
                SensitivityRow(
                    title: "Distraction",
                    value: $settings.distractionSensitivity,
                    detail: "How far your head and eyes must turn from the road."
                )
            } header: {
                sectionHeader("Detection")
            } footer: {
                sectionFooter("Higher sensitivity alerts sooner but may trigger on long blinks. Changes apply immediately, even mid-trip.")
            }
            .listRowBackground(Theme.surface)

            Section {
                Toggle("Sound", isOn: $settings.soundEnabled)
                Toggle("Text trusted contacts", isOn: $settings.smsAlertsEnabled)
                NavigationLink {
                    ContactsView()
                } label: {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Emergency contacts")
                        Text(contactSummary)
                            .font(.sdMeta)
                            .foregroundStyle(Theme.textSecondary)
                    }
                }
            } header: {
                sectionHeader("Alerts")
            } footer: {
                sectionFooter("If you stay distracted for about 10 seconds, SafeDrive opens a prefilled message to your contacts. You always press send yourself — nothing is sent in the background.")
            }
            .listRowBackground(Theme.surface)

            Section {
                SDSegmented(
                    options: AppearanceMode.allCases.map { ($0, $0.label) },
                    selection: $settings.appearanceMode,
                    onChange: { Haptics.tick() }
                )
                .listRowInsets(EdgeInsets())
            } header: {
                sectionHeader("Appearance")
            }
            .listRowBackground(Theme.surface)

            Section {
                LabeledContent("Calibration") {
                    if calibration.isCalibrated {
                        HStack(spacing: 4) {
                            Image(systemName: "checkmark")
                                .font(.system(size: 13, weight: .semibold))
                            Text("Ready")
                        }
                        .foregroundStyle(Theme.safe)
                    } else {
                        Text("Not calibrated")
                            .foregroundStyle(Theme.gold)
                    }
                }
                Button("Redo calibration") {
                    if !embedded { dismiss() }
                    monitor.stopMonitoring()
                    monitor.startCalibration()
                }
                .foregroundStyle(Theme.gold)
            } header: {
                sectionHeader("Camera")
            } footer: {
                sectionFooter("Recalibrate whenever you change where the phone is mounted.")
            }
            .listRowBackground(Theme.surface)

            Section {
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Only monitor above")
                        Spacer()
                        Text(settings.speedThresholdKmh <= 0
                             ? "Off"
                             : "\(Int(settings.speedThresholdKmh)) km/h")
                            .foregroundStyle(Theme.textSecondary)
                            .monospacedDigit()
                    }
                    Slider(value: $settings.speedThresholdKmh, in: 0...40, step: 5)
                        .tint(Theme.gold)
                }
                Toggle("Developer overlay", isOn: $settings.debugOverlayEnabled)
            } header: {
                sectionHeader("Advanced")
            } footer: {
                sectionFooter("The speed gate uses GPS, so monitoring pauses when you're stopped or parked. The developer overlay shows the live camera and raw signal values — for tuning, not for driving with.")
            }
            .listRowBackground(Theme.surface)

            Section {
                NavigationLink {
                    HowItWorksView()
                } label: {
                    Label("How SafeDrive works", systemImage: "questionmark.circle.fill")
                }
                LabeledContent("Version", value: appVersion)
            } header: {
                sectionHeader("About")
            } footer: {
                sectionFooter("SafeDrive analyses every frame on this device and discards it immediately. No video or biometric data is stored or transmitted.")
            }
            .listRowBackground(Theme.surface)
        }
        .listStyle(.insetGrouped)
        .scrollContentBackground(.hidden)
        .tint(Theme.safe) // toggles read as "on and safe", per the design
    }

    private func sectionHeader(_ text: String) -> some View {
        Text(text).sdSectionLabel()
    }

    private func sectionFooter(_ text: String) -> some View {
        Text(text)
            .font(.system(size: 11))
            .foregroundStyle(Theme.textSecondary)
    }

    private var contactSummary: String {
        let count = monitor.contactsStore.contacts.count
        switch count {
        case 0: return "None added yet"
        case 1: return monitor.contactsStore.contacts[0].name
        default: return "\(count) contacts"
        }
    }

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
    }
}

/// A sensitivity slider that snaps its *label* to four named zones with a
/// selection haptic at each boundary, so a continuous 0...1 drag reads as a
/// real dial rather than an arbitrary number. The underlying value stays
/// continuous — the engine reads it every frame.
private struct SensitivityRow: View {
    let title: String
    @Binding var value: Double
    let detail: String

    @State private var labelPulse = false
    @State private var lastZone: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title)
                Spacer()
                Text(zoneLabel(for: value))
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(Theme.textSecondary)
                    .scaleEffect(labelPulse ? 1.15 : 1)
            }
            Slider(value: $value, in: 0...1)
                .tint(Theme.gold)
                .accessibilityLabel("\(title) sensitivity")
                .accessibilityValue(zoneLabel(for: value))
            HStack {
                zoneTick("Relaxed", active: value < 0.25)
                Spacer()
                zoneTick("Standard", active: value >= 0.25 && value < 0.85)
                Spacer()
                zoneTick("Strict", active: value >= 0.85)
            }
            .accessibilityHidden(true)
            Text(detail)
                .font(.sdMeta)
                .foregroundStyle(Theme.textSecondary)
        }
        .padding(.vertical, 4)
        .onAppear { lastZone = zoneLabel(for: value) }
        .onChange(of: value) { newValue in
            let newZone = zoneLabel(for: newValue)
            guard lastZone != nil, lastZone != newZone else {
                lastZone = newZone
                return
            }
            lastZone = newZone
            Haptics.tick()
            withAnimation(Motion.quick) { labelPulse = true }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) {
                withAnimation(Motion.quick) { labelPulse = false }
            }
        }
    }

    private func zoneTick(_ text: String, active: Bool) -> some View {
        Text(text)
            .font(.system(size: 10, weight: .semibold))
            .textCase(.uppercase)
            .tracking(10 * 0.12)
            .foregroundStyle(active ? Theme.textPrimary : Theme.textSecondary)
    }

    private func zoneLabel(for sensitivity: Double) -> String {
        switch sensitivity {
        case ..<0.25: "Relaxed"
        case ..<0.6: "Balanced"
        case ..<0.85: "Alert"
        default: "Strict"
        }
    }
}
