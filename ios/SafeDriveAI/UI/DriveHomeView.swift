import SwiftUI

/// The Drive tab — what you see parked, before a trip starts.
///
/// This screen has exactly one job: get the driver into a monitored trip in
/// one tap. Everything else on it is status, not controls. Once monitoring
/// begins, `RootView` replaces the whole tab shell with `MonitoringView`,
/// the same way Maps drops its chrome when navigation starts.
struct DriveHomeView: View {
    @EnvironmentObject private var monitor: DriverMonitor
    @EnvironmentObject private var calibration: CalibrationManager

    private var isCalibrated: Bool { calibration.isCalibrated }

    var body: some View {
        ZStack(alignment: .topTrailing) {
            Theme.background.ignoresSafeArea()

            Aura(size: 288)
                .offset(x: 70, y: 40)

            VStack(spacing: 0) {
                SDNavTitle("Drive")
                    .padding(.top, 8)

                Spacer()

                Image(systemName: isCalibrated ? "steeringwheel" : "face.dashed")
                    .font(.system(size: 30, weight: .medium))
                    .foregroundStyle(Theme.goldForeground)
                    .frame(width: 74, height: 74)
                    .background(
                        RoundedRectangle(cornerRadius: Theme.Radius.icon, style: .continuous)
                            .fill(Theme.gold)
                    )
                    .shadow(color: Theme.gold.opacity(0.5), radius: 22, y: 14)

                Text(isCalibrated ? "Ready when you are" : "One quick setup first")
                    .font(.sdTitle)
                    .tracking(28 * -0.01)
                    .foregroundStyle(Theme.textPrimary)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(.top, 28)

                Text(isCalibrated
                     ? "Mount your iPhone so the front camera can see your face, then start the trip."
                     : "A one-time 10-second calibration learns your eyes and posture at this mount angle.")
                    .font(.sdBody)
                    .lineSpacing(5)
                    .foregroundStyle(Theme.textSecondary)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: 300)
                    .padding(.top, 12)

                Spacer()

                if isCalibrated {
                    ListGroup {
                        SDRow(title: "Calibration", detail: "Personalized to your face", last: true) {
                            HStack(spacing: 4) {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 13, weight: .semibold))
                                Text("Ready")
                                    .font(.system(size: 13, weight: .medium))
                            }
                            .foregroundStyle(Theme.safe)
                        }
                    }
                    .padding(.bottom, 16)
                }

                Button {
                    Haptics.tap(.medium)
                    isCalibrated ? monitor.startMonitoring() : monitor.startCalibration()
                } label: {
                    Label(isCalibrated ? "Start trip" : "Calibrate",
                          systemImage: isCalibrated ? "play.fill" : "viewfinder")
                }
                .buttonStyle(SDButtonStyle(.gold))
                .padding(.bottom, 12)
            }
            .padding(.horizontal, 24)
        }
    }
}
