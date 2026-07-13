import XCTest
@testable import SafeDriveAI

final class DistractionTimerTests: XCTestCase {
    @discardableResult
    private func run(
        _ timer: DistractionTimer,
        from: Int64, to: Int64, stepMs: Int64 = 33,
        state: (Int64) -> DriverState
    ) -> DistractionTimer.Trigger {
        var last: DistractionTimer.Trigger = .none
        var t = from
        while t <= to {
            let trigger = timer.ingest(state: state(t), atMs: t)
            if trigger == .fire { last = .fire }
            t += stepMs
        }
        return last
    }

    func testNoFireBeforeTenSeconds() {
        let timer = DistractionTimer()
        let result = run(timer, from: 0, to: 9_900) { _ in .distracted }
        XCTAssertEqual(result, .none)
    }

    func testFiresAtTenSecondsOfContinuousDistraction() {
        let timer = DistractionTimer()
        let result = run(timer, from: 0, to: 10_100) { _ in .distracted }
        XCTAssertEqual(result, .fire)
    }

    func testSafeStateResetsClock() {
        let timer = DistractionTimer()
        // 8 s distracted, then briefly safe, then 8 s more distracted —
        // neither leg alone reaches 10 s, and the reset means they don't add up.
        _ = run(timer, from: 0, to: 8_000) { _ in .distracted }
        _ = run(timer, from: 8_033, to: 8_500) { _ in .safe }
        let result = run(timer, from: 8_533, to: 16_500) { _ in .distracted }
        XCTAssertEqual(result, .none)

        // Confirm it does fire given a fresh, uninterrupted 10 s window.
        let fresh = run(timer, from: 16_533, to: 27_000) { _ in .distracted }
        XCTAssertEqual(fresh, .fire)
    }

    func testDrowsyStateAlsoResetsClock() {
        let timer = DistractionTimer()
        _ = run(timer, from: 0, to: 8_000) { _ in .distracted }
        _ = run(timer, from: 8_033, to: 8_500) { _ in .drowsy }
        let result = run(timer, from: 8_533, to: 16_500) { _ in .distracted }
        XCTAssertEqual(result, .none)
    }

    func testNoRefireInsideCooldown() {
        let timer = DistractionTimer()
        let first = run(timer, from: 0, to: 10_100) { _ in .distracted }
        XCTAssertEqual(first, .fire)

        // Still continuously distracted, but well inside the 2-minute cooldown.
        let stillCoolingDown = run(timer, from: 10_133, to: 60_000) { _ in .distracted }
        XCTAssertEqual(stillCoolingDown, .none)
    }

    func testRefiresOnceCooldownElapsesWhileStillDistracted() {
        let timer = DistractionTimer()
        let first = run(timer, from: 0, to: 10_100) { _ in .distracted }
        XCTAssertEqual(first, .fire)

        let second = run(timer, from: 10_133, to: 130_200) { _ in .distracted }
        XCTAssertEqual(second, .fire)
    }

    func testBehaviorIsFrameRateIndependent() {
        for step: Int64 in [33, 100] {
            let timer = DistractionTimer()
            let result = run(timer, from: 0, to: 10_100, stepMs: step) { _ in .distracted }
            XCTAssertEqual(result, .fire, "failed at \(step) ms/frame")
        }
    }

    func testResetClearsInProgressAndCooldownState() {
        let timer = DistractionTimer()
        _ = run(timer, from: 0, to: 10_100) { _ in .distracted }
        timer.reset()

        // Immediately after reset, a fresh 10 s window is required again,
        // and the prior fire's cooldown must not carry over.
        let tooSoon = run(timer, from: 10_133, to: 15_000) { _ in .distracted }
        XCTAssertEqual(tooSoon, .none)
        let result = run(timer, from: 15_033, to: 25_100) { _ in .distracted }
        XCTAssertEqual(result, .fire)
    }
}
