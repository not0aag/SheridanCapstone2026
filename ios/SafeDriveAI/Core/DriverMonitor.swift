import Foundation
import Combine
import UIKit

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

    // MARK: Components
    let camera = CameraService()
    let calibration: CalibrationManager
    let settings: AppSettings
    let speedGate = SpeedGate()
    private let tracker = FaceTracker()
    private let engine = DetectionEngine()
    private let alerts = AlertPlayer()
    private let distractionTimer = DistractionTimer()
    private var cancellables = Set<AnyCancellable>()

    init(settings: AppSettings, calibration: CalibrationManager) {
        self.settings = settings
        self.calibration = calibration

        camera.onFrame = { [tracker] pixelBuffer, timestampMs in
            // Capture queue: Vision runs here, results hop to the main actor.
            tracker.process(pixelBuffer: pixelBuffer, timestampMs: timestampMs)
        }
        tracker.onSnapshot = { [weak self] snapshot in
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
        alerts.endSession()
        camera.stop()
        speedGate.stop()
        overlay = nil
        UIApplication.shared.isIdleTimerDisabled = false
    }

    func startCalibration() {
        calibration.begin()
        phase = .calibrating
        camera.start()
        camera.setFrameRate(30)
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

            if distractionTimer.ingest(state: assessment.state, atMs: snapshot.timestampMs) == .fire {
                Task { await sendDistractionAlert() }
            }

        case .idle:
            break
        }
    }

    // MARK: Prolonged-distraction alert

    /// Best-effort: the local audio/haptic alert (AlertPlayer) has already
    /// fired regardless of this call's outcome, so a network failure here
    /// is non-fatal and silently swallowed.
    private func sendDistractionAlert() async {
        guard settings.smsAlertsEnabled else { return }
        _ = try? await APIClient.shared.sendDistractionAlert(latitude: nil, longitude: nil)
    }

    // MARK: Background behaviour

    private func observeLifecycle() {
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
