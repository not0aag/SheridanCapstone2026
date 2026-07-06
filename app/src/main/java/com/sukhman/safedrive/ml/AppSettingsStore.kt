package com.sukhman.safedrive.ml

import android.content.Context
import android.content.SharedPreferences

/**
 * Persists the user-tunable detection thresholds set in SettingsScreen so they
 * survive app restarts. Values are applied into the live AndroidDecisionEngine /
 * TripDetector instances at startup; SettingsScreen writes through both the live
 * engine (immediate effect) and this store (persistence), same split as
 * AndroidCalibrationEngine.
 */
class AppSettingsStore(context: Context) {

    companion object {
        private const val PREFS_NAME = "safedrive_settings"
        private const val KEY_PERCLOS_THRESHOLD = "perclos_threshold"
        private const val KEY_DIST_RATE_THRESHOLD = "dist_rate_threshold"
        private const val KEY_SPEED_THRESHOLD_KMH = "speed_threshold_kmh"

        const val DEFAULT_PERCLOS_THRESHOLD = 30.0
        const val DEFAULT_DIST_RATE_THRESHOLD = 0.40
        const val DEFAULT_SPEED_THRESHOLD_KMH = 15
    }

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var perclosThreshold: Double = DEFAULT_PERCLOS_THRESHOLD
        private set
    var distRateThreshold: Double = DEFAULT_DIST_RATE_THRESHOLD
        private set
    var speedThresholdKmh: Int = DEFAULT_SPEED_THRESHOLD_KMH
        private set

    init { loadFromPrefs() }

    fun savePerclosThreshold(value: Double) {
        perclosThreshold = value
        prefs.edit().putFloat(KEY_PERCLOS_THRESHOLD, value.toFloat()).apply()
    }

    fun saveDistRateThreshold(value: Double) {
        distRateThreshold = value
        prefs.edit().putFloat(KEY_DIST_RATE_THRESHOLD, value.toFloat()).apply()
    }

    fun saveSpeedThresholdKmh(value: Int) {
        speedThresholdKmh = value
        prefs.edit().putInt(KEY_SPEED_THRESHOLD_KMH, value).apply()
    }

    fun resetToDefaults() {
        perclosThreshold = DEFAULT_PERCLOS_THRESHOLD
        distRateThreshold = DEFAULT_DIST_RATE_THRESHOLD
        speedThresholdKmh = DEFAULT_SPEED_THRESHOLD_KMH
        prefs.edit().clear().apply()
    }

    private fun loadFromPrefs() {
        perclosThreshold = prefs.getFloat(KEY_PERCLOS_THRESHOLD, DEFAULT_PERCLOS_THRESHOLD.toFloat()).toDouble()
        distRateThreshold = prefs.getFloat(KEY_DIST_RATE_THRESHOLD, DEFAULT_DIST_RATE_THRESHOLD.toFloat()).toDouble()
        speedThresholdKmh = prefs.getInt(KEY_SPEED_THRESHOLD_KMH, DEFAULT_SPEED_THRESHOLD_KMH)
    }
}
