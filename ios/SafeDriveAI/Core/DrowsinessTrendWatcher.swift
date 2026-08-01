import Foundation

/// Watches PERCLOS trending upward *before* it crosses the real drowsy
/// alert threshold, and fires once (with a cooldown) so the driver gets a
/// gentle check-in earlier than a full alert — a second, softer tier below
/// DetectionEngine's own DROWSY state, not a replacement for it.
///
/// Pure, frameworkless state machine — same shape as DistractionTimer:
/// testable with synthetic (perclos, timestamp) pairs, no camera required.
final class DrowsinessTrendWatcher {
    struct Config {
        /// Fraction of the real alert threshold that counts as "trending up."
        /// e.g. 0.6 means a check-in can fire once PERCLOS reaches 60% of
        /// whatever would trigger a full DROWSY alert.
        var thresholdFraction: Double = 0.6
        /// How long PERCLOS must stay above that fraction before firing —
        /// avoids a single noisy frame triggering a check-in.
        var sustainedMs: Int64 = 2_000
        var cooldownMs: Int64 = 180_000
    }

    enum Trigger: Equatable {
        case none
        case fire
    }

    private let config: Config
    private var aboveSinceMs: Int64?
    private var lastFiredMs: Int64?

    init(config: Config = Config()) {
        self.config = config
    }

    /// Call once per assessment while actively monitoring. `alertThreshold`
    /// is the real PERCLOS threshold that would trigger a full DROWSY alert
    /// (`AppSettings.perclosThreshold`) — the check-in fires at a fraction
    /// of that, never at or above it, so it always precedes the real alert,
    /// never replaces or delays it.
    @discardableResult
    func ingest(perclos: Double, alertThreshold: Double, atMs t: Int64) -> Trigger {
        let trendingThreshold = alertThreshold * config.thresholdFraction
        guard perclos >= trendingThreshold, perclos < alertThreshold else {
            aboveSinceMs = nil
            return .none
        }
        if aboveSinceMs == nil { aboveSinceMs = t }
        guard t - aboveSinceMs! >= config.sustainedMs else { return .none }
        if let last = lastFiredMs, t - last < config.cooldownMs { return .none }
        lastFiredMs = t
        return .fire
    }

    func reset() {
        aboveSinceMs = nil
        lastFiredMs = nil
    }
}
