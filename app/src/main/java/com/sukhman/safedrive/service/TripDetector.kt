package com.sukhman.safedrive.service

import kotlinx.coroutines.*

class TripDetector(
    private val speedThresholdMps: Double = 15.0 / 3.6, // 15 km/h -> m/s
    private val requiredSecondsAboveThreshold: Int = 30,
    private val requiredSecondsBelowThreshold: Int = 10,
    private val scope: CoroutineScope = CoroutineScope(Dispatchers.Default)
) {

    interface Listener {
        fun onTripStarted()
        fun onTripStopped()
    }

    private var listener: Listener? = null
    private var aboveCounter = 0
    private var belowCounter = 0
    private var inTrip = false

    fun setListener(l: Listener) { listener = l }

    // Call this whenever a new speed reading arrives (in meters per second)
    fun onSpeedUpdate(speedMps: Double) {
        if (speedMps >= speedThresholdMps) {
            aboveCounter++
            belowCounter = 0
            if (!inTrip && aboveCounter >= requiredSecondsAboveThreshold) {
                inTrip = true
                listener?.onTripStarted()
            }
        } else {
            belowCounter++
            aboveCounter = 0
            if (inTrip && belowCounter >= requiredSecondsBelowThreshold) {
                inTrip = false
                listener?.onTripStopped()
            }
        }
    }

    fun reset() {
        aboveCounter = 0
        belowCounter = 0
        inTrip = false
    }

    fun destroy() {
        scope.cancel()
    }
}

