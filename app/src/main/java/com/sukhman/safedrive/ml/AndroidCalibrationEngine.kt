package com.sukhman.safedrive.ml

import android.content.Context
import android.content.SharedPreferences
import android.util.Log

class AndroidCalibrationEngine(context: Context) {

    companion object {
        private const val TAG = "CalibrationEngine"
        private const val PREFS_NAME = "safedrive_calibration"
        private const val KEY_EAR_THRESHOLD = "ear_threshold"
        private const val KEY_MEAN_OPEN_EAR  = "mean_open_ear"
        private const val KEY_IS_CALIBRATED  = "is_calibrated"
        const val DURATION_SECONDS = 10.0
        const val DEFAULT_EAR_THRESHOLD = 0.23f
    }

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var isCalibrating = false
        private set
    var isCalibrated = false
        private set
    var progress = 0f           // 0.0 → 1.0
        private set
    var earThreshold = DEFAULT_EAR_THRESHOLD
        private set
    var meanOpenEar = 0.31f
        private set

    private val earSamples = mutableListOf<Float>()
    private var startTimeMs = 0L

    init { loadFromPrefs() }

    fun startCalibration() {
        earSamples.clear()
        startTimeMs = System.currentTimeMillis()
        isCalibrating = true
        progress = 0f
        Log.i(TAG, "Calibration started")
    }

    /** Returns true when calibration completes. */
    fun addFrame(ear: Float): Boolean {
        if (!isCalibrating || ear <= 0f) return false
        val elapsed = (System.currentTimeMillis() - startTimeMs) / 1000.0
        progress = (elapsed / DURATION_SECONDS).toFloat().coerceIn(0f, 1f)
        earSamples.add(ear)
        if (elapsed >= DURATION_SECONDS) { finalise(); return true }
        return false
    }

    fun isEyesClosed(ear: Float) = ear in 0.01f..earThreshold

    private fun finalise() {
        isCalibrating = false
        if (earSamples.isEmpty()) { Log.w(TAG, "No samples — using default"); return }

        val sorted = earSamples.sorted()
        val cutoff = (sorted.size * 0.10).toInt()
        val filtered = sorted.drop(cutoff)
        if (filtered.isEmpty()) { Log.w(TAG, "All filtered — using default"); return }

        meanOpenEar = filtered.average().toFloat()
        earThreshold = meanOpenEar * 0.75f
        isCalibrated = true
        progress = 1f
        Log.i(TAG, "Done — mean=$meanOpenEar threshold=$earThreshold (${filtered.size} samples)")
        saveToPrefs()
    }

    private fun saveToPrefs() {
        prefs.edit()
            .putFloat(KEY_EAR_THRESHOLD, earThreshold)
            .putFloat(KEY_MEAN_OPEN_EAR,  meanOpenEar)
            .putBoolean(KEY_IS_CALIBRATED, true)
            .apply()
    }

    private fun loadFromPrefs() {
        isCalibrated = prefs.getBoolean(KEY_IS_CALIBRATED, false)
        if (isCalibrated) {
            earThreshold = prefs.getFloat(KEY_EAR_THRESHOLD, DEFAULT_EAR_THRESHOLD)
            meanOpenEar  = prefs.getFloat(KEY_MEAN_OPEN_EAR,  0.31f)
            Log.i(TAG, "Loaded — threshold=$earThreshold")
        }
    }

    fun reset() {
        prefs.edit().clear().apply()
        isCalibrated = false
        isCalibrating = false
        earThreshold = DEFAULT_EAR_THRESHOLD
        meanOpenEar = 0.31f
        earSamples.clear()
        progress = 0f
    }
}
