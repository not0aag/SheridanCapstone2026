import SwiftUI

/// The screen the driver lives on. Design rules: state readable in under one
/// second, no interaction needed while driving, one big button.
struct MonitoringView: View {
    @EnvironmentObject private var monitor: DriverMonitor
    @EnvironmentObject private var calibration: CalibrationManager
    @EnvironmentObject private var settings: AppSettings
    @State private var showSettings = false
    @State private var alertPulse = false

    private var isMonitoring: Bool {
        monitor.phase == .monitoring || isPaused
    }
    private var isPaused: Bool {
        if case .paused = monitor.phase { return true }
        return false
    }
    private var isAlerting: Bool {
        isMonitoring && monitor.driverState != .safe
    }

    var body: some View {
        ZStack {
            // Live camera or idle backdrop.
            if isMonitoring {
                CameraPreview(session: monitor.camera.session)
                    .ignoresSafeArea()
                FaceOverlay(geometry: monitor.overlay, state: monitor.driverState)
                    .ignoresSafeArea()
                LinearGradient(
                    colors: [.black.opacity(0.7), .clear, .clear, .black.opacity(0.85)],
                    startPoint: .top, endPoint: .bottom
                )
                .ignoresSafeArea()
                .allowsHitTesting(false)
            } else {
                idleBackdrop
            }

            // Full-screen alert flash.
            if isAlerting {
                Theme.color(for: monitor.driverState)
                    .opacity(alertPulse ? 0.45 : 0.15)
                    .ignoresSafeArea()
                    .allowsHitTesting(false)
                    .onAppear {
                        alertPulse = false
                        withAnimation(.easeInOut(duration: 0.45).repeatForever(autoreverses: true)) {
                            alertPulse = true
                        }
                    }
            }

            VStack(spacing: 0) {
                statusHeader
                Spacer()
                if isAlerting { alertBanner }
                Spacer()
                bottomControls
            }

            if isMonitoring && settings.debugOverlayEnabled {
                VStack {
                    HStack {
                        Spacer()
                        debugOverlay
                    }
                    Spacer()
                }
                .padding(.top, 60)
                .padding(.trailing, 16)
                .allowsHitTesting(false)
            }
        }
    }

    // MARK: Pieces

    private var idleBackdrop: some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "car.front.waves.up.fill")
                .font(.system(size: 72))
                .foregroundStyle(Theme.accent)
            Text("SafeDrive AI")
                .font(.largeTitle.weight(.black))
            Text(calibration.isCalibrated
                 ? "Mount the phone, then start monitoring."
                 : "Calibrate before your first drive.")
                .foregroundStyle(.secondary)
            Spacer()
            Spacer()
        }
    }

    private var statusHeader: some View {
        HStack {
            // Always-visible state pill.
            HStack(spacing: 8) {
                Circle()
                    .fill(headerColor)
                    .frame(width: 10, height: 10)
                Text(headerText)
                    .font(.headline.weight(.bold))
                if isMonitoring && !monitor.faceDetected {
                    Image(systemName: "eye.slash.fill")
                        .foregroundStyle(Theme.warning)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(.ultraThinMaterial, in: Capsule())

            Spacer()

            Button {
                showSettings = true
            } label: {
                Image(systemName: "gearshape.fill")
                    .font(.title3)
                    .padding(12)
                    .background(.ultraThinMaterial, in: Circle())
            }
            .disabled(isAlerting)
        }
        .padding(.horizontal, 20)
        .padding(.top, 8)
        .sheet(isPresented: $showSettings) { SettingsView() }
    }

    private var headerText: String {
        if isPaused { return "Paused — below speed" }
        guard isMonitoring else { return "Ready" }
        if !monitor.windowReady { return "Warming up…" }
        switch monitor.driverState {
        case .safe: return "Monitoring"
        case .drowsy: return "DROWSINESS"
        case .distracted: return "DISTRACTION"
        }
    }

    private var headerColor: Color {
        guard isMonitoring else { return .gray }
        if isPaused || !monitor.windowReady { return .gray }
        return Theme.color(for: monitor.driverState)
    }

    private var alertBanner: some View {
        VStack(spacing: 12) {
            Image(systemName: monitor.driverState == .drowsy
                  ? "zzz" : "eye.trianglebadge.exclamationmark.fill")
                .font(.system(size: 56, weight: .bold))
            Text(monitor.driverState == .drowsy ? "WAKE UP" : "EYES ON THE ROAD")
                .font(.system(size: 46, weight: .black))
                .minimumScaleFactor(0.6)
                .lineLimit(1)
            Text(monitor.driverState == .drowsy
                 ? "Pull over and rest — you are falling asleep."
                 : "You've been looking away from the road.")
                .font(.title3.weight(.semibold))
                .multilineTextAlignment(.center)
        }
        .foregroundStyle(.white)
        .padding(28)
        .frame(maxWidth: .infinity)
        .background(
            Theme.color(for: monitor.driverState).opacity(0.92),
            in: RoundedRectangle(cornerRadius: 24)
        )
        .padding(.horizontal, 20)
        .transition(.scale(scale: 0.9).combined(with: .opacity))
    }

    private var bottomControls: some View {
        VStack(spacing: 14) {
            if isMonitoring, let start = monitor.sessionStart {
                TimelineView(.periodic(from: start, by: 1)) { context in
                    Text(elapsed(from: start, to: context.date))
                        .font(.system(.body, design: .monospaced).weight(.semibold))
                        .foregroundStyle(.white.opacity(0.85))
                }
            }

            if calibration.isCalibrated {
                Button {
                    isMonitoring ? monitor.stopMonitoring() : monitor.startMonitoring()
                } label: {
                    Label(isMonitoring ? "Stop" : "Start Monitoring",
                          systemImage: isMonitoring ? "stop.fill" : "play.fill")
                }
                .buttonStyle(BigButtonStyle(color: isMonitoring ? Theme.danger : Theme.accent))
            } else {
                Button {
                    monitor.startCalibration()
                } label: {
                    Label("Calibrate", systemImage: "person.crop.rectangle.badge.plus")
                }
                .buttonStyle(BigButtonStyle(color: Theme.warning))
            }
        }
        .padding(.horizontal, 24)
        .padding(.bottom, 16)
        .animation(.easeInOut(duration: 0.25), value: isMonitoring)
    }

    /// Live raw signal values for threshold tuning (see handover doc §9).
    /// Never drives a decision — DetectionEngine does that. Toggle in
    /// Settings; off by default.
    private var debugOverlay: some View {
        let d = monitor.debug
        return VStack(alignment: .leading, spacing: 3) {
            debugRow("yaw", format(d.yaw), "pitch", format(d.pitch))
            debugRow("Δhead", format(d.headDelta), "dev", d.headDeviated ? "YES" : "no")
            debugRow("Δgaze", d.gazeDelta.map(format) ?? "—", "readable", d.gazeReadable ? "yes" : "NO")
            debugRow("offRoad", d.offRoad ? "YES" : "no", "", "")
            debugRow("PERCLOS", String(format: "%.0f%%", monitor.perclos * 100),
                      "offRoadRate", String(format: "%.0f%%", monitor.offRoadRate * 100))
            debugRow("ready", monitor.windowReady ? "yes" : "no", "", "")
        }
        .font(.system(size: 11, weight: .medium, design: .monospaced))
        .foregroundStyle(.white.opacity(0.9))
        .padding(10)
        .background(.black.opacity(0.55), in: RoundedRectangle(cornerRadius: 10))
    }

    private func debugRow(_ label1: String, _ value1: String, _ label2: String, _ value2: String) -> some View {
        HStack(spacing: 10) {
            Text("\(label1): \(value1)")
            if !label2.isEmpty { Text("\(label2): \(value2)") }
        }
    }

    private func format(_ v: Float) -> String { String(format: "%.3f", v) }

    private func elapsed(from start: Date, to now: Date) -> String {
        let s = Int(now.timeIntervalSince(start))
        return String(format: "%02d:%02d:%02d", s / 3600, (s % 3600) / 60, s % 60)
    }
}
