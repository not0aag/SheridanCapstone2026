import SwiftUI
import MessageUI

/// A prepared but unsent message — the driver reviews and sends it
/// themselves via the native composer; nothing goes out automatically.
struct MessageDraft: Identifiable, Equatable {
    let id = UUID()
    let recipients: [String]
    let body: String
}

/// Thin wrapper over MFMessageComposeViewController — presents Apple's own
/// Messages compose UI pre-filled with recipients and body text. The driver
/// still has to review and tap Send; this never sends on its own.
struct MessageComposerView: UIViewControllerRepresentable {
    let draft: MessageDraft
    let onFinished: () -> Void

    func makeUIViewController(context: Context) -> MFMessageComposeViewController {
        let controller = MFMessageComposeViewController()
        controller.recipients = draft.recipients
        controller.body = draft.body
        controller.messageComposeDelegate = context.coordinator
        return controller
    }

    func updateUIViewController(_ uiViewController: MFMessageComposeViewController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(onFinished: onFinished) }

    final class Coordinator: NSObject, MFMessageComposeViewControllerDelegate {
        let onFinished: () -> Void
        init(onFinished: @escaping () -> Void) { self.onFinished = onFinished }

        func messageComposeViewController(
            _ controller: MFMessageComposeViewController,
            didFinishWith result: MessageComposeResult
        ) {
            onFinished()
        }
    }
}
