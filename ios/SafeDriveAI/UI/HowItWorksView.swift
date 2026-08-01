import SwiftUI

/// A genuine transparency screen — the same kind of "how your data is
/// used" explanation any privacy-sensitive app should offer a user before
/// they grant camera access, not a demo-only addition.
struct HowItWorksView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 28) {
                stepRow(
                    icon: "camera.fill",
                    title: "Your front camera watches the road with you",
                    detail: "SafeDrive AI uses your phone's TrueDepth camera — the same sensor behind Face ID — to build a real 3D model of your face. It's a depth measurement, not a flat photo, which is what makes head-turn and eye-closure detection accurate at any mounting angle."
                )
                stepRow(
                    icon: "cpu.fill",
                    title: "Everything happens on this phone",
                    detail: "Every frame is analyzed on-device and immediately discarded. Nothing is recorded, nothing is uploaded, and no image or video ever leaves your phone — even the calibration data used to personalize alerts to your face stays local."
                )
                stepRow(
                    icon: "checkmark.seal.fill",
                    title: "Two signals must agree before you're alerted",
                    detail: "A single blink or a quick mirror check never triggers an alert. For drowsiness, both a sustained eye closure and an elevated closure rate over several seconds must be true together. For distraction, your head angle and your gaze direction both have to indicate you're off the road. This is deliberate — it's what keeps the app quiet during normal driving and confident when it does speak up."
                )
                stepRow(
                    icon: "person.crop.circle.badge.checkmark",
                    title: "Calibrated to you, not an average driver",
                    detail: "A one-time 10-second calibration learns your normal eye openness and head position at your specific mount angle. Every threshold after that is relative to your own baseline, not a generic assumption."
                )
            }
            .padding(24)
        }
        .background(Theme.background)
        .navigationTitle("How SafeDrive works")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func stepRow(icon: String, title: String, detail: String) -> some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(Theme.gold)
                .frame(width: 32)
            VStack(alignment: .leading, spacing: 6) {
                Text(title)
                    .font(.headline)
                Text(detail)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }
}
