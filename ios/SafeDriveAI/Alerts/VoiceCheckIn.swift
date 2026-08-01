import AVFoundation

/// A single spoken check-in line — the soft, tiered early-warning that
/// precedes a full DROWSY alert. Deliberately a separate, minimal class:
/// AlertPlayer's tone-synthesis and haptic-loop internals are load-bearing
/// and tested indirectly through the app's real alert behavior, so this
/// stays isolated rather than risking any change there.
final class VoiceCheckIn {
    private let synthesizer = AVSpeechSynthesizer()

    func speak(_ text: String = "Feeling okay? Tap to confirm.") {
        guard !synthesizer.isSpeaking else { return }
        let utterance = AVSpeechUtterance(string: text)
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        utterance.voice = AVSpeechSynthesisVoice(language: AVSpeechSynthesisVoice.currentLanguageCode())
        synthesizer.speak(utterance)
    }
}
