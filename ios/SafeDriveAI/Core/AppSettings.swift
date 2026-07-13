import Foundation
import Combine

/// User-tunable settings, persisted to UserDefaults. The detection engine
/// reads derived thresholds from here on every frame, so slider changes take
/// effect immediately — no restart, no re-arming.
final class AppSettings: ObservableObject {
    private let defaults: UserDefaults

    /// 0 (lenient) ... 1 (sensitive). Mapped to a PERCLOS threshold.
    @Published var drowsinessSensitivity: Double {
        didSet { defaults.set(drowsinessSensitivity, forKey: "drowsinessSensitivity") }
    }
    /// 0 (lenient) ... 1 (sensitive). Mapped to head/gaze deviation limits.
    @Published var distractionSensitivity: Double {
        didSet { defaults.set(distractionSensitivity, forKey: "distractionSensitivity") }
    }
    @Published var soundEnabled: Bool {
        didSet { defaults.set(soundEnabled, forKey: "soundEnabled") }
    }
    /// km/h below which monitoring pauses. 0 = always monitor (GPS unused).
    @Published var speedThresholdKmh: Double {
        didSet { defaults.set(speedThresholdKmh, forKey: "speedThresholdKmh") }
    }
    /// Shows live yaw/pitch/gaze numbers on the monitoring screen — for
    /// threshold tuning during development. Off by default so a shipped demo
    /// build never shows raw numbers unless someone opts in.
    @Published var debugOverlayEnabled: Bool {
        didSet { defaults.set(debugOverlayEnabled, forKey: "debugOverlayEnabled") }
    }
    /// Opt-in: text trusted contacts when prolonged distraction is detected.
    /// Defaults to off, since enabling it sends data off-device.
    @Published var smsAlertsEnabled: Bool {
        didSet { defaults.set(smsAlertsEnabled, forKey: "smsAlertsEnabled") }
    }

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        drowsinessSensitivity = defaults.object(forKey: "drowsinessSensitivity") as? Double ?? 0.5
        distractionSensitivity = defaults.object(forKey: "distractionSensitivity") as? Double ?? 0.5
        soundEnabled = defaults.object(forKey: "soundEnabled") as? Bool ?? true
        speedThresholdKmh = defaults.object(forKey: "speedThresholdKmh") as? Double ?? 0
        debugOverlayEnabled = defaults.object(forKey: "debugOverlayEnabled") as? Bool ?? false
        smsAlertsEnabled = defaults.object(forKey: "smsAlertsEnabled") as? Bool ?? false
    }

    // MARK: Derived thresholds (single source of truth for the engine)

    /// PERCLOS threshold: sensitive 0.20 ... lenient 0.45, default 0.325.
    var perclosThreshold: Double { 0.45 - drowsinessSensitivity * 0.25 }

    /// Head deviation (radians) considered "looking away":
    /// sensitive ≈11° ... lenient ≈23°.
    var headDeviationRadians: Float { Float(0.40 - distractionSensitivity * 0.20) }

    /// Gaze offset (fraction of eye width) considered "eyes off road".
    /// Range is kept low because Vision's pupil positions only shift ~0.10–0.15
    /// units for real gaze changes at typical dashboard camera distances.
    var gazeDeviationThreshold: Float { Float(0.15 - distractionSensitivity * 0.07) }
}
