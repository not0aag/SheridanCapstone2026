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
                        detail: "How quickly eye-closure patterns trigger an alert."
                    )
                    sensitivityRow(
                        title: "Distraction",
                        value: $settings.distractionSensitivity,
                        detail: "How far and how long you can look away before an alert."
                    )
                } header: {
                    Text("Sensitivity")
                } footer: {
                    Text("Changes apply immediately, even while monitoring.")
                }

                Section("Alerts") {
                    Toggle("Alert sounds", isOn: $settings.soundEnabled)
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
                    Text("SafeDrive AI monitors for drowsiness and distraction using the front camera. All analysis runs on-device with Apple's Vision framework. No video or biometric data is stored or transmitted.")
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
        .preferredColorScheme(.dark)
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
