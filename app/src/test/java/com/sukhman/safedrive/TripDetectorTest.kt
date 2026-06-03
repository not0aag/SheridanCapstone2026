package com.sukhman.safedrive

import com.sukhman.safedrive.service.TripDetector
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class TripDetectorTest {

    private lateinit var detector: TripDetector
    private val events = mutableListOf<String>()

    @Before
    fun setUp() {
        // Use tiny thresholds (3 samples each) so tests run quickly without delay().
        detector = TripDetector(
            speedThresholdMps = 15.0 / 3.6, // 15 km/h
            requiredSecondsAboveThreshold = 3,
            requiredSecondsBelowThreshold = 2
        )
        detector.setListener(object : TripDetector.Listener {
            override fun onTripStarted() { events.add("started") }
            override fun onTripStopped() { events.add("stopped") }
        })
    }

    @Test
    fun `trip starts after sustained speed above threshold`() {
        val fast = 20.0 / 3.6 // 20 km/h > 15 km/h threshold
        repeat(3) { detector.onSpeedUpdate(fast) }

        assertEquals(listOf("started"), events)
    }

    @Test
    fun `trip does not start if speed drops before threshold count`() {
        val fast = 20.0 / 3.6
        repeat(2) { detector.onSpeedUpdate(fast) }    // only 2, need 3
        detector.onSpeedUpdate(0.0)                    // reset counter
        repeat(3) { detector.onSpeedUpdate(fast) }    // start fresh

        // Should fire exactly once (the second sustained run)
        assertEquals(1, events.count { it == "started" })
    }

    @Test
    fun `trip stops after sustained low speed`() {
        val fast = 20.0 / 3.6
        repeat(3) { detector.onSpeedUpdate(fast) }    // trip started
        repeat(2) { detector.onSpeedUpdate(0.0) }     // trip stopped

        assertEquals(listOf("started", "stopped"), events)
    }

    @Test
    fun `no extra events when already in trip and still fast`() {
        val fast = 20.0 / 3.6
        repeat(10) { detector.onSpeedUpdate(fast) }

        assertEquals(1, events.count { it == "started" })
        assertEquals(0, events.count { it == "stopped" })
    }

    @Test
    fun `reset clears state without firing events`() {
        val fast = 20.0 / 3.6
        repeat(3) { detector.onSpeedUpdate(fast) }  // started
        events.clear()

        detector.reset()
        // Resuming fast should fire started again after threshold
        repeat(3) { detector.onSpeedUpdate(fast) }

        assertEquals(listOf("started"), events)
    }
}
