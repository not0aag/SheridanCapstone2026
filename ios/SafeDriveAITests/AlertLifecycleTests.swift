import XCTest
@testable import SafeDriveAI

/// Synthetic (state, timestamp) pairs only — no camera, no audio engine.
final class AlertLifecycleTests: XCTestCase {

    private func makeLifecycle() -> AlertLifecycle {
        AlertLifecycle(config: .init(takeoverMs: 8_000, acknowledgeMuteMs: 30_000))
    }

    func testSafeStateProducesNoAlert() {
        let lifecycle = makeLifecycle()
        let out = lifecycle.ingest(state: .safe, atMs: 0)
        XCTAssertEqual(out.presentation, .none)
        XCTAssertFalse(out.toneMuted)
        XCTAssertFalse(out.toneAttenuated)
    }

    func testAlertOpensAsTakeoverAtFullVolume() {
        let lifecycle = makeLifecycle()
        let out = lifecycle.ingest(state: .drowsy, atMs: 1_000)
        XCTAssertEqual(out.presentation, .takeover)
        XCTAssertFalse(out.toneMuted)
        XCTAssertFalse(out.toneAttenuated, "the opening burst must be the full klaxon")
    }

    /// The core hands-free guarantee: nobody touches anything, and the
    /// takeover still gets out of the driver's way on its own.
    func testTakeoverCollapsesItselfWithoutAnyInteraction() {
        let lifecycle = makeLifecycle()
        lifecycle.ingest(state: .drowsy, atMs: 0)

        let justBefore = lifecycle.ingest(state: .drowsy, atMs: 7_900)
        XCTAssertEqual(justBefore.presentation, .takeover)

        let after = lifecycle.ingest(state: .drowsy, atMs: 8_000)
        XCTAssertEqual(after.presentation, .persistent)
        XCTAssertTrue(after.toneAttenuated, "tone should step down once the takeover ends")
        XCTAssertFalse(after.toneMuted, "stepping down is not silence")
    }

    func testAcknowledgeCollapsesImmediatelyAndMutesTone() {
        let lifecycle = makeLifecycle()
        lifecycle.ingest(state: .drowsy, atMs: 0)
        lifecycle.acknowledge(atMs: 1_000)

        let out = lifecycle.ingest(state: .drowsy, atMs: 1_100)
        XCTAssertEqual(out.presentation, .persistent)
        XCTAssertTrue(out.toneMuted)
    }

    /// An acknowledgement must never be able to silence a real emergency
    /// indefinitely.
    func testMuteExpiresAndToneReturns() {
        let lifecycle = makeLifecycle()
        lifecycle.ingest(state: .drowsy, atMs: 0)
        lifecycle.acknowledge(atMs: 1_000)

        let stillMuted = lifecycle.ingest(state: .drowsy, atMs: 30_000)
        XCTAssertTrue(stillMuted.toneMuted)

        let reEscalated = lifecycle.ingest(state: .drowsy, atMs: 31_000)
        XCTAssertFalse(reEscalated.toneMuted, "tone must return after the mute window")
        XCTAssertTrue(reEscalated.toneAttenuated)
        XCTAssertEqual(reEscalated.presentation, .persistent)
    }

    func testReturningToSafeClearsEverything() {
        let lifecycle = makeLifecycle()
        lifecycle.ingest(state: .drowsy, atMs: 0)
        lifecycle.acknowledge(atMs: 500)

        let cleared = lifecycle.ingest(state: .safe, atMs: 2_000)
        XCTAssertEqual(cleared.presentation, .none)
        XCTAssertFalse(cleared.toneMuted)
    }

    /// After the driver recovers, a fresh episode gets the full treatment
    /// again — the earlier acknowledgement must not carry over.
    func testNewEpisodeAfterRecoveryReopensTakeover() {
        let lifecycle = makeLifecycle()
        lifecycle.ingest(state: .drowsy, atMs: 0)
        lifecycle.acknowledge(atMs: 500)
        lifecycle.ingest(state: .safe, atMs: 2_000)

        let fresh = lifecycle.ingest(state: .drowsy, atMs: 3_000)
        XCTAssertEqual(fresh.presentation, .takeover)
        XCTAssertFalse(fresh.toneMuted)
        XCTAssertFalse(fresh.toneAttenuated)
    }

    /// Acknowledging a distraction alert must not pre-silence a drowsiness
    /// alert that follows it — those are different emergencies.
    func testEscalationToDrowsyIgnoresEarlierAcknowledgement() {
        let lifecycle = makeLifecycle()
        lifecycle.ingest(state: .distracted, atMs: 0)
        lifecycle.acknowledge(atMs: 500)
        XCTAssertTrue(lifecycle.ingest(state: .distracted, atMs: 600).toneMuted)

        let escalated = lifecycle.ingest(state: .drowsy, atMs: 1_000)
        XCTAssertEqual(escalated.presentation, .takeover)
        XCTAssertFalse(escalated.toneMuted, "a new, more severe emergency starts loud")
    }

    func testResetReturnsToCleanState() {
        let lifecycle = makeLifecycle()
        lifecycle.ingest(state: .drowsy, atMs: 0)
        lifecycle.acknowledge(atMs: 100)
        lifecycle.reset()

        let out = lifecycle.ingest(state: .drowsy, atMs: 200)
        XCTAssertEqual(out.presentation, .takeover)
        XCTAssertFalse(out.toneMuted)
    }
}
