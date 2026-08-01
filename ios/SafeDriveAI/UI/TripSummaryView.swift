import SwiftUI

/// Shown right after a trip ends — the same "here's how you did" moment a
/// fitness app gives after a workout. Presented as a sheet at the design's
/// 86% detent so the trip you just finished stays visible behind it.
struct TripSummaryView: View {
    let summary: TripSummary
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack(alignment: .top) {
            Theme.background.ignoresSafeArea()

            Aura(size: 224)
                .offset(y: -24)

            VStack(spacing: 0) {
                Text("Trip complete")
                    .sdHeroLabel()
                    .padding(.top, 20)

                ScoreRing(value: summary.safetyScore, size: 168, caption: "Safety score")
                    .padding(.top, 20)

                Text(verdict)
                    .font(.system(size: 15))
                    .lineSpacing(3)
                    .foregroundStyle(Theme.textSecondary)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(.horizontal, 8)
                    .padding(.top, 20)

                HStack(spacing: 10) {
                    StatCard(value: formattedDuration, label: "Duration")
                    StatCard(value: "\(summary.drowsyAlertCount)", label: "Drowsy",
                             tint: summary.drowsyAlertCount > 0 ? Theme.alert : nil)
                    StatCard(value: "\(summary.distractedAlertCount)", label: "Distracted",
                             tint: summary.distractedAlertCount > 0 ? Theme.gold : nil)
                }
                .padding(.top, 24)

                Spacer(minLength: 20)

                Button("Done") {
                    Haptics.tap()
                    dismiss()
                }
                .buttonStyle(SDButtonStyle(.gold))
                .padding(.bottom, 12)
            }
            .padding(.horizontal, 24)
        }
        .presentationDetents([.fraction(0.86)])
        .presentationDragIndicator(.visible)
    }

    /// One warm sentence, chosen from what actually happened. Never
    /// congratulatory about a trip that contained a drowsiness alert.
    private var verdict: String {
        if summary.drowsyAlertCount > 0 {
            return "You showed signs of drowsiness on this drive. Rest properly before the next one."
        }
        if summary.distractedAlertCount > 0 {
            return "A few moments away from the road, but you stayed alert throughout."
        }
        return "Sharp the whole way. No alerts on this trip."
    }

    private var formattedDuration: String {
        let minutes = Int(summary.duration) / 60
        if minutes < 60 { return "\(minutes)m" }
        let hours = minutes / 60
        return minutes % 60 == 0 ? "\(hours)h" : "\(hours)h \(minutes % 60)m"
    }
}
