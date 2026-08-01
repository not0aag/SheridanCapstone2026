import XCTest
@testable import SafeDriveAI

final class DrowsinessTrendWatcherTests: XCTestCase {
    @discardableResult
    private func run(
        _ watcher: DrowsinessTrendWatcher,
        from: Int64, to: Int64, stepMs: Int64 = 33,
        alertThreshold: Double = 0.3,
        perclos: (Int64) -> Double
    ) -> DrowsinessTrendWatcher.Trigger {
        var last: DrowsinessTrendWatcher.Trigger = .none
        var t = from
        while t <= to {
            let trigger = watcher.ingest(perclos: perclos(t), alertThreshold: alertThreshold, atMs: t)
            if trigger == .fire { last = .fire }
            t += stepMs
        }
        return last
    }

    func testNoFireBelowTrendingThreshold() {
        let watcher = DrowsinessTrendWatcher()
        // 50% of a 0.3 threshold = 0.15, well below the 60% trending fraction.
        let result = run(watcher, from: 0, to: 5_000) { _ in 0.15 }
        XCTAssertEqual(result, .none)
    }

    func testFiresAfterSustainedTrendingPerclos() {
        let watcher = DrowsinessTrendWatcher()
        // 0.2 is 66% of 0.3 — above the 60% trending fraction, below the
        // real alert threshold itself.
        let result = run(watcher, from: 0, to: 2_100) { _ in 0.2 }
        XCTAssertEqual(result, .fire)
    }

    func testNoFireBeforeSustainedDuration() {
        let watcher = DrowsinessTrendWatcher()
        let result = run(watcher, from: 0, to: 1_900) { _ in 0.2 }
        XCTAssertEqual(result, .none)
    }

    func testNeverFiresAtOrAboveRealAlertThreshold() {
        let watcher = DrowsinessTrendWatcher()
        // 0.3 IS the real alert threshold — DetectionEngine's own DROWSY
        // state already owns this, the soft check-in must stay out of the way.
        let result = run(watcher, from: 0, to: 5_000) { _ in 0.3 }
        XCTAssertEqual(result, .none)
    }

    func testDroppingBelowThresholdResetsSustainedClock() {
        let watcher = DrowsinessTrendWatcher()
        _ = run(watcher, from: 0, to: 1_500) { _ in 0.2 }
        _ = run(watcher, from: 1_533, to: 1_600) { _ in 0.05 }
        let result = run(watcher, from: 1_633, to: 3_000) { _ in 0.2 }
        XCTAssertEqual(result, .none) // fresh 2 s window never completes within this range

        let fresh = run(watcher, from: 3_033, to: 5_100) { _ in 0.2 }
        XCTAssertEqual(fresh, .fire)
    }

    func testNoRefireInsideCooldown() {
        let watcher = DrowsinessTrendWatcher()
        let first = run(watcher, from: 0, to: 2_100) { _ in 0.2 }
        XCTAssertEqual(first, .fire)

        let stillCoolingDown = run(watcher, from: 2_133, to: 60_000) { _ in 0.2 }
        XCTAssertEqual(stillCoolingDown, .none)
    }

    func testResetClearsState() {
        let watcher = DrowsinessTrendWatcher()
        _ = run(watcher, from: 0, to: 2_100) { _ in 0.2 }
        watcher.reset()

        let tooSoon = run(watcher, from: 2_133, to: 3_000) { _ in 0.2 }
        XCTAssertEqual(tooSoon, .none)
        let result = run(watcher, from: 3_033, to: 5_100) { _ in 0.2 }
        XCTAssertEqual(result, .fire)
    }
}
