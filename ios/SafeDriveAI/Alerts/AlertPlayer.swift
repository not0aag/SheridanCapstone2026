import AVFoundation
import CoreHaptics

/// Audio + haptic alerts, synthesized with AVAudioEngine so no sound assets
/// are needed and volume/urgency are fully controllable.
///
/// The audio session uses `.playback`, so alerts sound even when the ringer
/// switch is on silent — mandatory for a safety app. The engine also runs
/// (silently) for the whole monitoring session: combined with the `audio`
/// background mode, that keeps the process alive if the app is backgrounded.
///
/// Distinct signatures:
///   DROWSY     — low, insistent two-tone klaxon (700/900 Hz), looping. Sounds
///                like an alarm clock: wake up.
///   DISTRACTED — two short high chirps (1400 Hz), repeating at a slower
///                cadence. Sounds like a warning ping: look up.
final class AlertPlayer {
    private let engine = AVAudioEngine()
    private var sourceNode: AVAudioSourceNode?
    private let sampleRate: Double = 44_100

    private var hapticEngine: CHHapticEngine?
    private var hapticLoop: CHHapticAdvancedPatternPlayer?

    var soundEnabled = true

    // Audio-thread state: which alert pattern the render callback synthesizes.
    private enum Pattern { case silent, drowsy, distracted }
    private let patternLock = NSLock()
    private var pattern: Pattern = .silent
    private var sampleClock: Double = 0

    // MARK: Session lifecycle

    func startSession() {
        guard sourceNode == nil else { return }
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playback, mode: .default, options: [.duckOthers])
            try audioSession.setActive(true)

            let format = AVAudioFormat(standardFormatWithSampleRate: sampleRate, channels: 1)!
            let node = AVAudioSourceNode { [weak self] _, _, frameCount, bufferList -> OSStatus in
                self?.render(frameCount: frameCount, bufferList: bufferList) ?? noErr
            }
            engine.attach(node)
            engine.connect(node, to: engine.mainMixerNode, format: format)
            try engine.start()
            sourceNode = node
        } catch {
            print("AlertPlayer: audio start failed: \(error)")
        }
        startHaptics()
    }

    func endSession() {
        setPattern(.silent)
        stopHapticLoop()
        if let node = sourceNode {
            engine.detach(node)
            sourceNode = nil
        }
        engine.stop()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }

    // MARK: Alert control (idempotent; call freely every frame)

    func update(for state: DriverState) {
        switch state {
        case .safe:
            if currentPattern() != .silent {
                setPattern(.silent)
                stopHapticLoop()
            }
        case .drowsy:
            if currentPattern() != .drowsy {
                setPattern(.drowsy)
                startHapticLoop(intensity: 1.0, sharpness: 0.3) // deep rumble
            }
        case .distracted:
            if currentPattern() != .distracted {
                setPattern(.distracted)
                startHapticLoop(intensity: 0.8, sharpness: 0.9) // sharp buzz
            }
        }
    }

    // MARK: Synthesis (audio render thread — no allocation, no locks held long)

    private func render(frameCount: AVAudioFrameCount, bufferList: UnsafeMutablePointer<AudioBufferList>) -> OSStatus {
        patternLock.lock()
        let active = pattern
        patternLock.unlock()

        let buffers = UnsafeMutableAudioBufferListPointer(bufferList)
        for frame in 0..<Int(frameCount) {
            let t = sampleClock / sampleRate
            var sample: Float = 0
            if soundEnabled {
                switch active {
                case .silent:
                    break
                case .drowsy:
                    // 1 Hz klaxon: 0–0.4 s at 700 Hz, 0.5–0.9 s at 900 Hz.
                    let cycle = t.truncatingRemainder(dividingBy: 1.0)
                    if cycle < 0.4 {
                        sample = Float(sin(2 * .pi * 700 * t)) * 0.9
                    } else if cycle >= 0.5 && cycle < 0.9 {
                        sample = Float(sin(2 * .pi * 900 * t)) * 0.9
                    }
                case .distracted:
                    // Every 1.5 s: two 120 ms chirps at 1400 Hz, 180 ms apart.
                    let cycle = t.truncatingRemainder(dividingBy: 1.5)
                    if cycle < 0.12 || (cycle >= 0.3 && cycle < 0.42) {
                        sample = Float(sin(2 * .pi * 1400 * t)) * 0.8
                    }
                }
            }
            for buffer in buffers {
                buffer.mData!.assumingMemoryBound(to: Float.self)[frame] = sample
            }
            sampleClock += 1
        }
        return noErr
    }

    private func setPattern(_ new: Pattern) {
        patternLock.lock()
        pattern = new
        patternLock.unlock()
    }

    private func currentPattern() -> Pattern {
        patternLock.lock()
        defer { patternLock.unlock() }
        return pattern
    }

    // MARK: Haptics

    private func startHaptics() {
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics else { return }
        do {
            hapticEngine = try CHHapticEngine()
            hapticEngine?.resetHandler = { [weak self] in try? self?.hapticEngine?.start() }
            try hapticEngine?.start()
        } catch {
            print("AlertPlayer: haptics unavailable: \(error)")
        }
    }

    private func startHapticLoop(intensity: Float, sharpness: Float) {
        stopHapticLoop()
        guard let hapticEngine else { return }
        do {
            let event = CHHapticEvent(
                eventType: .hapticContinuous,
                parameters: [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: intensity),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: sharpness),
                ],
                relativeTime: 0,
                duration: 1.0
            )
            let player = try hapticEngine.makeAdvancedPlayer(
                with: try CHHapticPattern(events: [event], parameters: [])
            )
            player.loopEnabled = true
            try player.start(atTime: CHHapticTimeImmediate)
            hapticLoop = player
        } catch {
            print("AlertPlayer: haptic loop failed: \(error)")
        }
    }

    private func stopHapticLoop() {
        try? hapticLoop?.stop(atTime: CHHapticTimeImmediate)
        hapticLoop = nil
    }
}
