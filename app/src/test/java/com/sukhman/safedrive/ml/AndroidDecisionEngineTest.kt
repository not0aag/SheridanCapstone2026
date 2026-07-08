package com.sukhman.safedrive.ml

import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class AndroidDecisionEngineTest {

    private lateinit var engine: AndroidDecisionEngine

    @Before
    fun setUp() {
        engine = AndroidDecisionEngine()
    }

    @Test
    fun `no alert when eyes open and not distracted`() {
        repeat(5) { engine.addFrame(eyesClosed = false, isDistracted = false, headDeviated = false) }
        val decision = engine.getDecision()
        assertFalse(decision.alert)
        assertEquals("", decision.alertType)
    }

    @Test
    fun `sustained distraction above the default rate threshold triggers DISTRACTED`() {
        // 25-frame window, all distracted AND head deviated -> both rates 1.0, above
        // the default 0.40/0.60 thresholds. DISTRACTED does not require the
        // elapsed-time gate DROWSY does, so no sleep needed.
        repeat(25) { engine.addFrame(eyesClosed = false, isDistracted = true, headDeviated = true) }
        val decision = engine.getDecision()
        assertEquals("DISTRACTED", decision.alertType)
    }

    @Test
    fun `distraction rate below the default threshold does not trigger an alert`() {
        // 5 of 25 frames distracted -> rate 0.2, below the default 0.40 threshold.
        repeat(20) { engine.addFrame(eyesClosed = false, isDistracted = false, headDeviated = true) }
        repeat(5) { engine.addFrame(eyesClosed = false, isDistracted = true, headDeviated = true) }
        val decision = engine.getDecision()
        assertEquals("", decision.alertType)
    }

    @Test
    fun `lowering distRateThreshold makes the same distraction rate fire an alert`() {
        // Same 0.2 distraction rate as the "below threshold" case above, but with a
        // lowered threshold — regression test for the Settings sensitivity slider
        // wiring. Head deviation still needs to clear its own (unchanged) threshold.
        engine.distRateThreshold = 0.1
        repeat(20) { engine.addFrame(eyesClosed = false, isDistracted = false, headDeviated = true) }
        repeat(5) { engine.addFrame(eyesClosed = false, isDistracted = true, headDeviated = true) }
        val decision = engine.getDecision()
        assertEquals("DISTRACTED", decision.alertType)
    }

    @Test
    fun `head deviated alone does not trigger DISTRACTED`() {
        // Brief mirror checks / head movement without classifier agreement must not
        // alert — this is the exact false-positive path ml decision_engine.py guards
        // against ("brief mirror checks (head only)").
        repeat(25) { engine.addFrame(eyesClosed = false, isDistracted = false, headDeviated = true) }
        val decision = engine.getDecision()
        assertEquals("", decision.alertType)
    }

    @Test
    fun `classifier distraction alone does not trigger DISTRACTED`() {
        // Classifier noise without head-deviation agreement must not alert — the
        // other false-positive path ml decision_engine.py guards against
        // ("model noise (classifier only)").
        repeat(25) { engine.addFrame(eyesClosed = false, isDistracted = true, headDeviated = false) }
        val decision = engine.getDecision()
        assertEquals("", decision.alertType)
    }

    @Test
    fun `sustained eye closure past the drowsy window triggers DROWSY`() {
        // DROWSY requires >= 4s of real elapsed time (AndroidDecisionEngine reads
        // System.currentTimeMillis() internally, so this needs an actual sleep).
        engine.addFrame(eyesClosed = true, isDistracted = false, headDeviated = false)
        Thread.sleep(4100)
        // Frames older than the 4s window get pruned, so refresh it post-sleep.
        repeat(3) { engine.addFrame(eyesClosed = true, isDistracted = false, headDeviated = false) }

        val decision = engine.getDecision()
        assertEquals("DROWSY", decision.alertType)
        assertTrue(decision.perclosPct > 30f)
    }

    @Test
    fun `raising perclosThreshold suppresses DROWSY despite full eye closure`() {
        engine.perclosThreshold = 150.0 // above the max possible 100% PERCLOS
        engine.addFrame(eyesClosed = true, isDistracted = false, headDeviated = false)
        Thread.sleep(4100)
        repeat(3) { engine.addFrame(eyesClosed = true, isDistracted = false, headDeviated = false) }

        val decision = engine.getDecision()
        assertEquals("", decision.alertType)
    }

    @Test
    fun `reset clears accumulated frames`() {
        repeat(25) { engine.addFrame(eyesClosed = false, isDistracted = true, headDeviated = true) }
        assertEquals("DISTRACTED", engine.getDecision().alertType)

        engine.reset()

        assertEquals("", engine.getDecision().alertType)
    }
}
