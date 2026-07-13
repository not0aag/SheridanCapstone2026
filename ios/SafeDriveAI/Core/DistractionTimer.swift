import Foundation

/// Tracks continuous time spent in `.distracted` and fires once past a
/// threshold (default 10 s), with a cooldown between repeat fires so a
/// driver who stays distracted doesn't get re-notified every frame.
/// Pure, frameworkless state machine — testable with synthetic
/// (state, timestamp) pairs, no camera required. Mirrors DetectionEngine's
/// own testing style.
final class DistractionTimer {
    struct Config {
        var thresholdMs: Int64 = 10_000
        var cooldownMs: Int64 = 120_000
    }

    enum Trigger: Equatable {
        case none
        case fire
    }

    private let config: Config
    private var distractedSinceMs: Int64?
    private var lastFiredMs: Int64?

    init(config: Config = Config()) {
        self.config = config
    }

    /// Call once per assessment. Any state other than `.distracted` resets
    /// the clock — including `.drowsy`, since drowsiness already outranks
    /// distraction in DetectionEngine's state machine and represents a
    /// different episode.
    @discardableResult
    func ingest(state: DriverState, atMs t: Int64) -> Trigger {
        guard state == .distracted else {
            distractedSinceMs = nil
            return .none
        }
        if distractedSinceMs == nil {
            distractedSinceMs = t
        }
        guard t - distractedSinceMs! >= config.thresholdMs else { return .none }
        if let last = lastFiredMs, t - last < config.cooldownMs { return .none }
        lastFiredMs = t
        return .fire
    }

    func reset() {
        distractedSinceMs = nil
        lastFiredMs = nil
    }
}
