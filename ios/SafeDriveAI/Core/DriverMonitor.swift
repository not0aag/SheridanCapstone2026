import Foundation
import Combine
import UIKit
import MessageUI
import simd

/// Raw per-frame signal values for the live tuning overlay (Section 9 of the
/// iOS handover doc). Not used for any alert decision — DetectionEngine owns
/// that. This exists purely so thresholds can be tuned by watching real
/// numbers instead of guessing.
struct DebugSignals: Equatable {
    var yaw: Float = 0
    var pitch: Float = 0
    var headDelta: Float = 0
    var headDeviated: Bool = false
    var gazeDelta: Float?
    var gazeReadable: Bool = false
    var offRoad: Bool = false
}

/// Top-level coordinator: camera → FaceTracker → CalibrationManager or
/// DetectionEngine → AlertPlayer, plus screen-awake and background handling.
/// The single ObservableObject the UI talks to.
@MainActor
final class DriverMonitor: ObservableObject {
    enum Phase: Equatable {
        case idle
        case calibrating
        case monitoring
        case paused(reason: String) // e.g. below speed threshold
    }

    // MARK: UI-facing state
    @Published private(set) var phase: Phase = .idle
    @Published private(set) var driverState: DriverState = .safe
    @Published private(set) var faceDetected = false
    @Published private(set) var overlay: FaceOverlayGeometry?
    @Published private(set) var perclos: Double = 0
    @Published private(set) var offRoadRate: Double = 0
    @Published private(set) var windowReady = false
    @Published private(set) var sessionStart: Date?
    @Published private(set) var debug = DebugSignals()
    /// Set the moment a session ends, for the UI to present a trip summary
    /// sheet. Consumed (set back to nil) once shown.
    @Published var lastTripSummary: TripSummary?
    /// True for a few seconds after a tiered early-warning check-in fires —
    /// a soft "feeling okay?" prompt, well below a real DROWSY alert.
    @Published private(set) var showCheckInBanner = false
    /// Set when a prolonged-distraction message is ready to send, for the UI
    /// to present the native SMS composer. The driver still sends it
    /// themselves — this never sends silently in the background.
    @Published var pendingMessageComposer: MessageDraft?
    /// How the current alert should be presented. Advances on its own —
    /// the driver never has to touch the phone to get the full-bleed
    /// takeover out of the way. See AlertLifecycle.
    @Published private(set) var alertPresentation: AlertPresentation = .none
    /// True when monitoring stopped because the OS interrupted the camera
    /// (an incoming call, Control Center, another app taking the camera).
    /// Surfaced so the driver is never left believing they're being watched
    /// when they aren't.
    @Published private(set) var monitoringInterrupted = false

    // MARK: Components
    let camera = CameraService()
    let calibration: CalibrationManager
    let settings: AppSettings
    let contactsStore: LocalContactsStore
    let speedGate = SpeedGate()
    let tripLog = TripLog()
    private let engine = DetectionEngine()
    private let alerts = AlertPlayer()
    private let distractionTimer = DistractionTimer()
    private let drowsinessTrendWatcher = DrowsinessTrendWatcher()
    private let voiceCheckIn = VoiceCheckIn()
    private let alertLifecycle = AlertLifecycle()
    private var cancellables = Set<AnyCancellable>()
    /// Timestamp of the most recent frame, so `acknowledgeAlert()` — which
    /// arrives from a tap, not from the camera — can be placed on the same
    /// clock the lifecycle uses.
    private var lastFrameMs: Int64 = 0

    init(settings: AppSettings, calibration: CalibrationManager, contactsStore: LocalContactsStore) {
        self.settings = settings
        self.calibration = calibration
        self.contactsStore = contactsStore

        camera.onSnapshot = { [weak self] snapshot in
            // Delegate/capture queue: hop to the main actor before touching state.
            Task { @MainActor [weak self] in
                self?.handle(snapshot)
            }
        }

        settings.$soundEnabled
            .sink { [alerts] in alerts.soundEnabled = $0 }
            .store(in: &cancellables)

        observeLifecycle()
    }

    // MARK: Controls

    func startMonitoring() {
        guard calibration.isCalibrated else { return }
        engine.reset()
        distractionTimer.reset()
        drowsinessTrendWatcher.reset()
        alertLifecycle.reset()
        alertPresentation = .none
        monitoringInterrupted = false
        tripLog.startTrip()
        driverState = .safe
        sessionStart = .now
        phase = .monitoring
        camera.start()
        camera.setFrameRate(30)
        alerts.startSession()
        if settings.speedThresholdKmh > 0 { speedGate.start() }
        UIApplication.shared.isIdleTimerDisabled = true // never sleep mid-drive
    }

    func stopMonitoring() {
        phase = .idle
        sessionStart = nil
        driverState = .safe
        alertLifecycle.reset()
        alertPresentation = .none
        monitoringInterrupted = false
        alerts.endSession()
        camera.stop()
        speedGate.stop()
        overlay = nil
        lastTripSummary = tripLog.endTrip()
        UIApplication.shared.isIdleTimerDisabled = false
    }

    func startCalibration() {
        calibration.begin()
        phase = .calibrating
        camera.start()
        camera.setFrameRate(30)
    }

    /// Optional acknowledgement of an active alert. Collapses the takeover
    /// immediately and mutes the *tone* for 30 seconds; haptics and the
    /// on-screen banner continue, and the tone returns if the driver is
    /// still in danger when that window closes. Never required — the alert
    /// steps itself down without this (see AlertLifecycle).
    func acknowledgeAlert() {
        alertLifecycle.acknowledge(atMs: lastFrameMs)
        alertPresentation = .persistent
    }

    func cancelCalibration() {
        calibration.cancel()
        if phase == .calibrating {
            phase = .idle
            camera.stop()
        }
    }

    // MARK: Per-frame pipeline

    private func handle(_ snapshot: FaceSnapshot) {
        faceDetected = snapshot.faceDetected
        overlay = snapshot.overlay
        lastFrameMs = snapshot.timestampMs

        switch phase {
        case .calibrating:
            if calibration.ingest(snapshot) {
                // Done — hold the finished state briefly, then return home.
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { [weak self] in
                    guard let self, self.phase == .calibrating else { return }
                    self.phase = .idle
                    self.camera.stop()
                }
            }

        case .monitoring, .paused:
            guard let baseline = calibration.baseline else { return }

            // Speed gate: pause cleanly below the threshold, resume above it.
            if !speedGate.allowsMonitoring(threshold: settings.speedThresholdKmh) {
                if phase != .paused(reason: "Below speed threshold") {
                    phase = .paused(reason: "Below speed threshold")
                    engine.reset()
                    distractionTimer.reset()
                    drowsinessTrendWatcher.reset()
                    alertLifecycle.reset()
                    alertPresentation = .none
                    driverState = .safe
                    alerts.update(for: .safe)
                }
                return
            }
            if case .paused = phase { phase = .monitoring }

            // Thresholds are read from settings every frame, so slider changes
            // apply instantly — no restart needed.
            let assessment = engine.ingest(snapshot, baseline: baseline, thresholds: .init(
                perclos: settings.perclosThreshold,
                headDeviationRad: settings.headDeviationRadians,
                gazeDeviation: settings.gazeDeviationThreshold
            ))
            driverState = assessment.state
            perclos = assessment.perclos
            offRoadRate = assessment.offRoadRate
            windowReady = assessment.ready
            alerts.update(for: assessment.state)

            // How loudly and how visibly to present it. The takeover
            // collapses and the tone steps down on their own timetable, so
            // a driver with both hands on the wheel is never stuck with a
            // full-screen alarm they can't dismiss.
            let presentation = alertLifecycle.ingest(state: assessment.state, atMs: snapshot.timestampMs)
            alertPresentation = presentation.presentation
            alerts.setTone(muted: presentation.toneMuted, attenuated: presentation.toneAttenuated)

            debug = Self.debugSignals(for: snapshot, baseline: baseline, settings: settings)
            if assessment.ready {
                tripLog.ingest(state: assessment.state, perclos: assessment.perclos, offRoadRate: assessment.offRoadRate)
            }

            if distractionTimer.ingest(state: assessment.state, atMs: snapshot.timestampMs) == .fire {
                Task { await sendDistractionAlert() }
            }

            // Soft early-warning tier — only relevant while still .safe; a
            // real DROWSY alert already outranks and supersedes it.
            if assessment.ready, assessment.state == .safe,
               drowsinessTrendWatcher.ingest(
                   perclos: assessment.perclos,
                   alertThreshold: settings.perclosThreshold,
                   atMs: snapshot.timestampMs
               ) == .fire {
                voiceCheckIn.speak()
                showCheckInBanner = true
                DispatchQueue.main.asyncAfter(deadline: .now() + 6) { [weak self] in
                    self?.showCheckInBanner = false
                }
            }

        case .idle:
            break
        }
    }

    // MARK: Debug overlay

    /// Mirrors DetectionEngine's per-frame fusion math so the overlay shows
    /// exactly what the engine sees. Display-only — never feeds a decision.
    private static func debugSignals(
        for snapshot: FaceSnapshot,
        baseline: CalibrationManager.Baseline,
        settings: AppSettings
    ) -> DebugSignals {
        guard snapshot.faceDetected else { return DebugSignals() }

        let headDeltaVec = SIMD2<Float>(snapshot.yaw - baseline.neutralYaw, snapshot.pitch - baseline.neutralPitch)
        let headDelta = simd_length(headDeltaVec)
        let headDeviated = headDelta > settings.headDeviationRadians

        let closedThreshold = baseline.openEyeAperture * DetectionEngine.closureFactor
        let eyesClosed = snapshot.eyeOpenness < closedThreshold

        var gazeDelta: Float?
        if let gaze = snapshot.gaze {
            gazeDelta = simd_length(gaze - SIMD2<Float>(baseline.neutralGazeX, baseline.neutralGazeY))
        }

        let offRoad: Bool
        if headDeviated {
            if let gazeDelta, !eyesClosed {
                offRoad = gazeDelta > settings.gazeDeviationThreshold
            } else {
                offRoad = true
            }
        } else {
            offRoad = false
        }

        return DebugSignals(
            yaw: snapshot.yaw,
            pitch: snapshot.pitch,
            headDelta: headDelta,
            headDeviated: headDeviated,
            gazeDelta: gazeDelta,
            gazeReadable: snapshot.gaze != nil,
            offRoad: offRoad
        )
    }

    // MARK: Prolonged-distraction alert

    /// Notifies trusted contacts entirely on-device via the native SMS
    /// composer — no backend or Twilio dependency. The local audio/haptic
    /// alert (AlertPlayer) has already fired earlier in the pipeline
    /// regardless, so the driver is warned either way; this is the
    /// additional "let someone else know" step, and the driver still
    /// reviews and sends it themselves (MessageComposerView never
    /// auto-sends) rather than a message going out silently in the
    /// background.
    private func sendDistractionAlert() async {
        guard settings.smsAlertsEnabled else { return }
        let recipients = contactsStore.list().map(\.phoneNumber)
        guard !recipients.isEmpty else { return }
        // Without this, a distraction alert on a device that can't send
        // text (Wi-Fi-only iPad, no SIM/carrier) would silently drop —
        // `pendingMessageComposer` would be set, nothing would ever present
        // it, and nothing would tell the driver why. Better to not even try.
        guard MFMessageComposeViewController.canSendText() else { return }
        pendingMessageComposer = MessageDraft(
            recipients: recipients,
            body: "SafeDrive AI: I may be distracted while driving. This is an automated check-in."
        )
    }

    /// Manual trigger for Trusted Contacts setup — bypasses distraction
    /// detection and the "Text trusted contacts" toggle entirely, so a
    /// driver can confirm their contacts and the message composer actually
    /// work without simulating 10+ seconds of real distracted driving.
    /// Returns false (and sets nothing) if there's no contact to message or
    /// this device can't send text at all — callers use that to explain why
    /// nothing happened rather than presenting a broken sheet.
    @discardableResult
    func sendTestMessage() -> Bool {
        let recipients = contactsStore.list().map(\.phoneNumber)
        guard !recipients.isEmpty, MFMessageComposeViewController.canSendText() else { return false }
        pendingMessageComposer = MessageDraft(
            recipients: recipients,
            body: "This is a test message from SafeDrive AI. If you received this, your trusted contact setup is working."
        )
        return true
    }

    // MARK: Background behaviour

    private func observeLifecycle() {
        // The OS can take the camera away mid-drive — an incoming call,
        // Control Center, another app. ARKit simply stops delivering
        // frames, which used to leave the driver looking at a calm
        // "Monitoring" pill while nothing was actually being monitored.
        // Debounced, because a healthy session start also passes through
        // isRunning == false for a moment.
        camera.$isRunning
            .removeDuplicates()
            .debounce(for: .seconds(2), scheduler: DispatchQueue.main)
            .sink { [weak self] running in
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    let monitoring: Bool
                    switch self.phase {
                    case .monitoring, .paused: monitoring = true
                    case .idle, .calibrating: monitoring = false
                    }
                    let interrupted = monitoring && !running
                    guard interrupted != self.monitoringInterrupted else { return }
                    self.monitoringInterrupted = interrupted
                    // Say it out loud. A banner is no use to someone who is
                    // — correctly — looking at the road.
                    if interrupted {
                        self.voiceCheckIn.speak("SafeDrive monitoring has paused.")
                    }
                }
            }
            .store(in: &cancellables)

        NotificationCenter.default.addObserver(
            forName: UIApplication.didEnterBackgroundNotification, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.phase == .monitoring else { return }
                self.camera.setFrameRate(15) // halve the work while unwatched
            }
        }
        NotificationCenter.default.addObserver(
            forName: UIApplication.willEnterForegroundNotification, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.phase == .monitoring else { return }
                self.camera.setFrameRate(30)
            }
        }
    }
}
