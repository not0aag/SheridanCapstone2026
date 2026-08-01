import SwiftUI
import MessageUI

/// The screen the driver lives on during a trip. Design rule: readable in
/// under a second, at arm's length, with no interaction required.
///
/// The camera feed is deliberately *not* shown here. Watching yourself is a
/// distraction, and the privacy banner states plainly what the camera is
/// doing instead. The live preview is still available behind the existing
/// debug toggle for tuning and demos.
struct MonitoringView: View {
    @EnvironmentObject private var monitor: DriverMonitor
    @EnvironmentObject private var settings: AppSettings
    @EnvironmentObject private var contactsStore: LocalContactsStore
    let namespace: Namespace.ID

    @State private var showSettings = false

    private var isPaused: Bool {
        if case .paused = monitor.phase { return true }
        return false
    }
    private var isAlerting: Bool { monitor.driverState != .safe }
    /// Presentation is owned by `DriverMonitor`/`AlertLifecycle`, not by this
    /// view, precisely because it advances on a timer rather than on a tap.
    private var presentation: AlertPresentation { monitor.alertPresentation }

    var body: some View {
        ZStack {
            Theme.background.ignoresSafeArea()

            Aura(size: 288)
                .offset(x: -110, y: -60)

            VStack(spacing: 0) {
                header

                if monitor.monitoringInterrupted {
                    interruptedBanner
                } else if monitor.showCheckInBanner && !isAlerting {
                    checkInBanner
                }

                Spacer(minLength: 0)

                if isAlerting && presentation == .persistent {
                    acknowledgedAlertBanner
                        .padding(.bottom, 20)
                }

                tripReadout

                Spacer(minLength: 0)

                if settings.debugOverlayEnabled { developerPanel }

                privacyBanner

                Button {
                    Haptics.tap(.medium)
                    monitor.stopMonitoring()
                } label: {
                    Label("End trip", systemImage: "stop.fill")
                }
                .buttonStyle(SDButtonStyle(.quiet))
                .padding(.top, 12)
                .padding(.bottom, 12)
            }
            .padding(.horizontal, 24)

            if presentation == .takeover {
                AlertOverlayView(
                    state: monitor.driverState,
                    escalationNote: escalationNote
                ) {
                    monitor.acknowledgeAlert()
                }
                .transition(.opacity)
                .zIndex(1)
            }
        }
        .animation(Motion.alertImpact, value: isAlerting)
        .animation(Motion.springy, value: presentation)
        .onChange(of: monitor.driverState) { newState in
            // One sharp cue marks entry into an alert — layered on top of
            // AlertPlayer's own continuous haptic loop, never a replacement
            // for it. The takeover itself is driven by AlertLifecycle.
            guard newState != .safe else { return }
            Haptics.warning()
            // VoiceOver users get no benefit from a full-screen colour
            // change; announce the alert instead, at the interrupting
            // priority an emergency warrants.
            UIAccessibility.post(
                notification: .announcement,
                argument: newState == .drowsy
                    ? "Drowsiness detected. Pull over safely."
                    : "Distraction detected. Eyes on the road."
            )
        }
        .sheet(isPresented: $showSettings) { SettingsView() }
        .sheet(item: composerBinding) { draft in
            MessageComposerView(draft: draft) { monitor.pendingMessageComposer = nil }
        }
    }

    /// `MFMessageComposeViewController` can't be presented on a device or
    /// simulator that can't send texts — quietly clear the pending draft in
    /// that case rather than presenting a broken sheet.
    private var composerBinding: Binding<MessageDraft?> {
        Binding(
            get: { MFMessageComposeViewController.canSendText() ? monitor.pendingMessageComposer : nil },
            set: { monitor.pendingMessageComposer = $0 }
        )
    }

    // MARK: Header

    private var header: some View {
        HStack {
            // Carries the same matchedGeometryEffect id as the calibration
            // progress ring, so the ring becomes this pill the moment
            // calibration finishes instead of a flat cut between screens.
            StatusPill(label: statusLabel, tone: statusTone)
                .matchedGeometryEffect(id: "statusShape", in: namespace)
                .animation(Motion.springy, value: statusLabel)

            if !monitor.faceDetected && !isPaused {
                Image(systemName: "eye.slash.fill")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(Theme.gold)
                    .accessibilityLabel("Face not visible")
            }

            Spacer()

            SDCircleButton(systemName: "slider.horizontal.3") {
                Haptics.tap()
                showSettings = true
            }
            .accessibilityLabel("Settings")
            .disabled(isAlerting)
        }
        .padding(.top, 8)
    }

    private var statusLabel: String {
        if isPaused { return "Paused" }
        if !monitor.windowReady { return "Warming up" }
        switch monitor.driverState {
        case .safe: return "Monitoring"
        case .drowsy: return "Drowsy"
        case .distracted: return "Distracted"
        }
    }

    private var statusTone: StatusPill.Tone {
        if isPaused || !monitor.windowReady { return .gold }
        switch monitor.driverState {
        case .safe: return .safe
        case .drowsy: return .alert
        case .distracted: return .gold
        }
    }

    // MARK: Trip readout

    private var tripReadout: some View {
        VStack(spacing: 0) {
            Text("Trip duration")
                .sdHeroLabel()

            Group {
                if let start = monitor.sessionStart {
                    TimelineView(.periodic(from: start, by: 1)) { context in
                        Text(elapsed(from: start, to: context.date))
                    }
                } else {
                    Text("00:00")
                }
            }
            .font(.sdTimer)
            .tracking(68 * -0.02)
            .monospacedDigit()
            .foregroundStyle(Theme.textPrimary)
            .minimumScaleFactor(0.6)
            .lineLimit(1)
            .padding(.top, 8)

            HStack(spacing: 12) {
                statCard(
                    label: "Alertness",
                    value: monitor.windowReady ? "\(alertnessPercent)%" : "—",
                    tint: monitor.windowReady && monitor.driverState == .safe ? Theme.safe : nil
                )
                statCard(
                    label: "Events",
                    value: "\(monitor.tripLog.currentTripAlerts)",
                    tint: nil
                )
            }
            .padding(.top, 40)
        }
    }

    /// Share of the rolling window the driver's eyes were open. PERCLOS is
    /// the fraction of that window they were closed, so this is its
    /// complement — the same number the engine acts on, phrased positively.
    private var alertnessPercent: Int {
        Int((1 - min(max(monitor.perclos, 0), 1)) * 100)
    }

    private func statCard(label: String, value: String, tint: Color?) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.system(size: 10, weight: .semibold))
                .textCase(.uppercase)
                .tracking(10 * 0.14)
                .foregroundStyle(Theme.textSecondary)
            Text(value)
                .font(.sdStatValue)
                .monospacedDigit()
                .foregroundStyle(tint ?? Theme.textPrimary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .sdCard()
        .accessibilityElement(children: .combine)
    }

    // MARK: Banners

    private var privacyBanner: some View {
        HStack(spacing: 12) {
            Image(systemName: "camera.fill")
                .font(.sdBody)
            Text("Camera active. Eyes tracked on device only.")
                .font(.sdCaption)
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .foregroundStyle(Theme.onGoldSoft)
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Theme.goldSoft, in: RoundedRectangle(cornerRadius: Theme.Radius.card, style: .continuous))
        .accessibilityElement(children: .combine)
    }

    /// What the takeover collapses into — either on its own after a few
    /// seconds, or immediately if the driver acknowledged. Haptics are still
    /// running and the tone is only stepped down, never off, so this is what
    /// keeps the screen honest about an alert that is still active.
    private var acknowledgedAlertBanner: some View {
        HStack(spacing: 12) {
            Image(systemName: monitor.driverState == .drowsy
                  ? "exclamationmark.triangle.fill" : "eye.trianglebadge.exclamationmark.fill")
                .font(.system(size: 16, weight: .semibold))
            Text(monitor.driverState == .drowsy
                 ? "Still detecting drowsiness — pull over."
                 : "Still detecting distraction — eyes up.")
                .font(.sdCaption.weight(.semibold))
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .foregroundStyle(monitor.driverState == .drowsy ? Theme.onAlert : Theme.goldForeground)
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(
            Theme.color(for: monitor.driverState),
            in: RoundedRectangle(cornerRadius: Theme.Radius.card, style: .continuous)
        )
        .transition(.move(edge: .top).combined(with: .opacity))
        .accessibilityElement(children: .combine)
    }

    /// Shown when the OS has taken the camera — a call, Control Center,
    /// another app. Red, because a driver who believes they're being watched
    /// and isn't isn't merely uninformed, they're worse off than if the app
    /// were closed. Spoken aloud too; see DriverMonitor.observeLifecycle.
    private var interruptedBanner: some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 15))
            Text("Monitoring paused — the camera is in use elsewhere.")
                .font(.sdCaption.weight(.semibold))
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .foregroundStyle(Theme.onAlert)
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Theme.alert, in: RoundedRectangle(cornerRadius: Theme.Radius.card, style: .continuous))
        .padding(.top, 12)
        .transition(.move(edge: .top).combined(with: .opacity))
        .animation(Motion.springy, value: monitor.monitoringInterrupted)
        .accessibilityElement(children: .combine)
    }

    /// A soft, tiered early-warning — below a real alert, not a replacement
    /// for it. Purely informational: requiring a tap here would violate this
    /// screen's own no-interaction rule and would ask a possibly-drowsy
    /// driver to reach for the phone, which is exactly backwards.
    private var checkInBanner: some View {
        HStack(spacing: 12) {
            Image(systemName: "questionmark.circle.fill")
                .font(.sdBody)
            Text("Just checking in — stay focused on the road.")
                .font(.sdCaption.weight(.semibold))
            Spacer(minLength: 0)
        }
        .foregroundStyle(Theme.onGoldSoft)
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Theme.goldSoft, in: RoundedRectangle(cornerRadius: Theme.Radius.card, style: .continuous))
        .padding(.top, 12)
        .transition(.move(edge: .top).combined(with: .opacity))
        .animation(Motion.springy, value: monitor.showCheckInBanner)
        .accessibilityElement(children: .combine)
    }

    /// Only stated when it's actually true — the app never claims an
    /// escalation that isn't wired up. Distraction is the only state with a
    /// contact-notification path (see DistractionTimer).
    private var escalationNote: String? {
        guard monitor.driverState == .distracted,
              settings.smsAlertsEnabled,
              let first = contactsStore.contacts.first
        else { return nil }
        return "Texting \(first.name) if this continues…"
    }

    // MARK: Developer panel

    /// Live camera preview plus raw signal values, for threshold tuning and
    /// demos. Never drives a decision — DetectionEngine does that. Toggled
    /// in Settings; off by default.
    private var developerPanel: some View {
        let d = monitor.debug
        return HStack(alignment: .top, spacing: 12) {
            ZStack {
                CameraPreview(camera: monitor.camera)
                FaceOverlay(geometry: monitor.overlay, state: monitor.driverState)
            }
            .frame(width: 96, height: 128)
            .clipShape(RoundedRectangle(cornerRadius: Theme.Radius.inner, style: .continuous))

            VStack(alignment: .leading, spacing: 3) {
                debugRow("yaw", format(d.yaw), "pitch", format(d.pitch))
                debugRow("Δhead", format(d.headDelta), "dev", d.headDeviated ? "YES" : "no")
                debugRow("Δgaze", d.gazeDelta.map(format) ?? "—", "read", d.gazeReadable ? "yes" : "NO")
                debugRow("offRoad", d.offRoad ? "YES" : "no", "", "")
                debugRow("PERCLOS", String(format: "%.0f%%", monitor.perclos * 100),
                         "rate", String(format: "%.0f%%", monitor.offRoadRate * 100))
                debugRow("ready", monitor.windowReady ? "yes" : "no", "", "")
            }
            .font(.system(size: 11, weight: .medium, design: .monospaced))
            .foregroundStyle(Theme.textSecondary)
            Spacer(minLength: 0)
        }
        .padding(12)
        .sdCard()
        .padding(.bottom, 12)
        .accessibilityHidden(true)
    }

    private func debugRow(_ label1: String, _ value1: String, _ label2: String, _ value2: String) -> some View {
        HStack(spacing: 8) {
            Text("\(label1): \(value1)")
            if !label2.isEmpty { Text("\(label2): \(value2)") }
        }
    }

    private func format(_ v: Float) -> String { String(format: "%.3f", v) }

    private func elapsed(from start: Date, to now: Date) -> String {
        let s = max(Int(now.timeIntervalSince(start)), 0)
        return s >= 3600
            ? String(format: "%d:%02d:%02d", s / 3600, (s % 3600) / 60, s % 60)
            : String(format: "%02d:%02d", s / 60, s % 60)
    }
}
