package com.sukhman.safedrive

import android.content.Context
import android.content.SharedPreferences

/**
 * Persists trip counters across app restarts and navigation. "Total trips" is
 * recorded the moment the user presses Start Monitoring — not from TripDetector's
 * GPS-speed gate, which requires 30s of real driving speed and would never fire
 * indoors during a demo. TripDetector's own GPS logic is untouched and still
 * drives the live Active/Idle status shown on Home.
 */
class TripStatsStore(context: Context) {

    companion object {
        private const val PREFS_NAME = "safedrive_trip_stats"
        private const val KEY_TOTAL_TRIPS = "total_trips"
        private const val KEY_TRIPS_TODAY = "trips_today"
        private const val KEY_LAST_TRIP_EPOCH_DAY = "last_trip_epoch_day"
        private const val MS_PER_DAY = 86_400_000L
    }

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var totalTrips: Int = 0
        private set
    var tripsToday: Int = 0
        private set

    private var lastTripEpochDay: Long = -1L

    init { loadFromPrefs() }

    /** Call the moment the user presses Start Monitoring. */
    fun recordTripStarted() {
        val today = System.currentTimeMillis() / MS_PER_DAY
        if (today != lastTripEpochDay) {
            tripsToday = 0
            lastTripEpochDay = today
        }
        totalTrips += 1
        tripsToday += 1
        saveToPrefs()
    }

    private fun saveToPrefs() {
        prefs.edit()
            .putInt(KEY_TOTAL_TRIPS, totalTrips)
            .putInt(KEY_TRIPS_TODAY, tripsToday)
            .putLong(KEY_LAST_TRIP_EPOCH_DAY, lastTripEpochDay)
            .apply()
    }

    private fun loadFromPrefs() {
        totalTrips = prefs.getInt(KEY_TOTAL_TRIPS, 0)
        lastTripEpochDay = prefs.getLong(KEY_LAST_TRIP_EPOCH_DAY, -1L)
        val today = System.currentTimeMillis() / MS_PER_DAY
        tripsToday = if (lastTripEpochDay == today) prefs.getInt(KEY_TRIPS_TODAY, 0) else 0
    }
}
