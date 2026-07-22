import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var settings: AppSettings
    @EnvironmentObject private var calibration: CalibrationManager
    @EnvironmentObject private var monitor: DriverMonitor
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    sensitivityRow(
                        title: "Drowsiness",
                        value: $settings.drowsinessSensitivity,
                        detail: "How much eye closure counts as drowsy."
                    )
                    sensitivityRow(
                        title: "Distraction",
                        value: $settings.distractionSensitivity,
                        detail: "How far your head or eyes need to turn from the road."
                    )
                } header: {
                    Text("Sensitivity")
                } footer: {
                    Text("Changes apply immediately, even while monitoring.")
                }

                Section {
                    Picker("Appearance", selection: $settings.appearanceMode) {
                        ForEach(AppearanceMode.allCases) { mode in
                            Text(mode.label).tag(mode)
                        }
                    }
                    .pickerStyle(.segmented)
                } header: {
                    Text("Appearance")
                }

                Section("Alerts") {
                    Toggle("Alert sounds", isOn: $settings.soundEnabled)
                }

                Section {
                    Toggle("Text trusted contacts when distracted", isOn: $settings.smsAlertsEnabled)
                    NavigationLink("Manage Trusted Contacts") { ContactsView() }
                } header: {
                    Text("Emergency Alerts")
                } footer: {
                    Text("When enabled, a text message is sent to your trusted contacts if you're detected as continuously distracted for about 10 seconds. This requires a network connection and a SafeDrive AI account.")
                }

                Section {
                    Toggle("Show debug overlay", isOn: $settings.debugOverlayEnabled)
                } footer: {
                    Text("Shows live yaw/pitch/gaze numbers on the monitoring screen — for tuning thresholds, not for driving with.")
                }

                Section {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("Only monitor above")
                            Spacer()
                            Text(settings.speedThresholdKmh <= 0
                                 ? "Off — always monitor"
                                 : "\(Int(settings.speedThresholdKmh)) km/h")
                                .foregroundStyle(.secondary)
                                .monospacedDigit()
                        }
                        Slider(value: $settings.speedThresholdKmh, in: 0...40, step: 5)
                    }
                } header: {
                    Text("Speed threshold")
                } footer: {
                    Text("Uses GPS. Monitoring pauses when you're stopped or parked, so you can look around freely.")
                }

                Section("Calibration") {
                    if let baseline = calibration.baseline {
                        LabeledContent("Status") {
                            Label("Calibrated", systemImage: "checkmark.seal.fill")
                                .foregroundStyle(Theme.accent)
                        }
                        LabeledContent("Open-eye aperture",
                                       value: String(format: "%.3f", baseline.openEyeAperture))
                    } else {
                        LabeledContent("Status") {
                            Label("Not calibrated", systemImage: "exclamationmark.triangle.fill")
                                .foregroundStyle(Theme.warning)
                        }
                    }
                    Button("Redo calibration") {
                        dismiss()
                        monitor.stopMonitoring()
                        monitor.startCalibration()
                    }
                }

                Section("About") {
                    LabeledContent("Version", value: appVersion)
                    Text("SafeDrive AI monitors for drowsiness and distraction using the front camera. All analysis runs on-device — no video or biometric data is stored or transmitted.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private func sensitivityRow(title: String, value: Binding<Double>, detail: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title)
                Spacer()
                Text(label(for: value.wrappedValue))
                    .foregroundStyle(.secondary)
            }
            Slider(value: value, in: 0...1)
            Text(detail)
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
    }

    private func label(for sensitivity: Double) -> String {
        switch sensitivity {
        case ..<0.25: "Relaxed"
        case ..<0.6: "Balanced"
        case ..<0.85: "Alert"
        default: "Strict"
        }
    }

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
    }
}
