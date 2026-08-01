import Foundation

/// How an active alert is currently being presented.
enum AlertPresentation: Equatable {
    case none
    /// Full-bleed takeover — the opening seconds, when the job is to grab
    /// attention no matter what the driver is doing.
    case takeover
    /// Collapsed to a persistent banner. Still alerting, still audible, but
    /// no longer covering the screen.
    case persistent
}

/// Decides *how loudly and how visibly* an active alert presents over time.
///
/// ## Why this exists
///
/// The first version of the alert screen could only be dismissed by tapping
/// "I'm awake". That is the wrong shape for this product: the driver's hands
/// belong on the wheel, and a phone on a dash mount is not somewhere you
/// reach during an emergency. An alert that *requires* a tap is an alert
/// that either gets ignored or causes the exact distraction it exists to
/// prevent.
///
/// So acknowledgement is optional here. Left completely alone, an alert:
///   1. opens as a full-bleed takeover with the full klaxon,
///   2. after `takeoverMs` collapses on its own to a persistent banner and
///      steps the tone down to a periodic pulse — the driver has been told;
///      continuing to scream at them at full volume adds nothing and buries
///      road noise they need to hear,
///   3. and stops entirely the moment `DetectionEngine` says they're safe.
///
/// This mirrors how production driver-monitoring systems behave: a strong
/// burst, then a persistent-but-liveable reminder, cleared by evidence of
/// alertness rather than by a button.
///
/// Tapping is still *allowed* — for a passenger, or a driver already pulled
/// over — and mutes the tone for `acknowledgeMuteMs`. It cannot mute
/// permanently: if the danger state persists past that window, the tone
/// comes back. Haptics are never suppressed by any of this.
///
/// Pure, frameworkless state machine — same shape as `DistractionTimer` and
/// `DrowsinessTrendWatcher`, testable with synthetic (state, timestamp)
/// pairs and no camera.
final class AlertLifecycle {
    struct Config {
        /// How long the full-bleed takeover holds before collapsing itself.
        var takeoverMs: Int64 = 8_000
        /// How long an explicit acknowledgement mutes the tone before it
        /// re-escalates. Deliberately finite.
        var acknowledgeMuteMs: Int64 = 30_000
    }

    struct Output: Equatable {
        var presentation: AlertPresentation
        /// Tone silenced entirely. Haptics and the visual banner continue.
        var toneMuted: Bool
        /// Tone stepped down from continuous to a periodic pulse.
        var toneAttenuated: Bool
    }

    private let config: Config
    private var alertSinceMs: Int64?
    private var mutedUntilMs: Int64?
    /// Forces the collapsed presentation after an explicit acknowledgement,
    /// independently of how long the alert has actually been running.
    private var acknowledged = false
    private var lastState: DriverState = .safe

    init(config: Config = Config()) {
        self.config = config
    }

    /// Call once per assessment while monitoring.
    @discardableResult
    func ingest(state: DriverState, atMs t: Int64) -> Output {
        // A change of danger state is a genuinely new episode: it re-opens
        // the takeover and drops any earlier acknowledgement, so a
        // distraction alert escalating into drowsiness is never silenced by
        // a tap the driver made about the previous one.
        if state != lastState {
            lastState = state
            alertSinceMs = nil
            mutedUntilMs = nil
            acknowledged = false
        }

        guard state != .safe else {
            alertSinceMs = nil
            mutedUntilMs = nil
            acknowledged = false
            return Output(presentation: .none, toneMuted: false, toneAttenuated: false)
        }

        if alertSinceMs == nil { alertSinceMs = t }
        let elapsed = t - alertSinceMs!

        let collapsed = acknowledged || elapsed >= config.takeoverMs
        let muted = mutedUntilMs.map { t < $0 } ?? false

        return Output(
            presentation: collapsed ? .persistent : .takeover,
            toneMuted: muted,
            // Once the takeover is over the tone always steps down, whether
            // the driver acknowledged or simply waited.
            toneAttenuated: collapsed && !muted
        )
    }

    /// Optional. Collapses the takeover immediately and mutes the tone for a
    /// bounded window.
    func acknowledge(atMs t: Int64) {
        acknowledged = true
        mutedUntilMs = t + config.acknowledgeMuteMs
    }

    func reset() {
        alertSinceMs = nil
        mutedUntilMs = nil
        acknowledged = false
        lastState = .safe
    }
}
