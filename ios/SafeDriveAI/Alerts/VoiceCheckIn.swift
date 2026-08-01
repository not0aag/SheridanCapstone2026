import AVFoundation

/// Short spoken lines — the soft, tiered early-warning that precedes a full
/// DROWSY alert, plus the "monitoring has paused" notice. Deliberately a
/// separate, minimal class: AlertPlayer's tone-synthesis and haptic-loop
/// internals are load-bearing and tested indirectly through the app's real
/// alert behavior, so this stays isolated rather than risking any change
/// there.
///
/// Speech is the right channel for everything in here: it reaches a driver
/// whose eyes are — correctly — on the road, and it asks nothing of their
/// hands. Nothing spoken by this class ever instructs the driver to touch
/// the phone.
final class VoiceCheckIn {
    private let synthesizer = AVSpeechSynthesizer()

    /// The default line used to end "Tap to confirm", which was wrong twice
    /// over: the check-in banner has no tap target by design, and telling a
    /// possibly-drowsy driver to reach for a mounted phone is exactly
    /// backwards.
    func speak(_ text: String = "Still with us? Eyes on the road.") {
        guard !synthesizer.isSpeaking else { return }
        let utterance = AVSpeechUtterance(string: text)
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        utterance.voice = AVSpeechSynthesisVoice(language: AVSpeechSynthesisVoice.currentLanguageCode())
        synthesizer.speak(utterance)
    }
}
