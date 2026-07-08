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
        private const val KEY_HAS_HEAD_BASELINE = "has_head_baseline"
        private const val KEY_BASELINE_NORMAL_X = "baseline_normal_x"
        private const val KEY_BASELINE_NORMAL_Y = "baseline_normal_y"
        private const val KEY_BASELINE_NORMAL_Z = "baseline_normal_z"
        const val DURATION_SECONDS = 10.0
        const val DEFAULT_EAR_THRESHOLD = 0.23f
        // This proxy's angular scale doesn't match Python's solvePnP-based 0.44 rad —
        // this is a starting point for on-device tuning, not a validated final number.
        const val DEFAULT_HEAD_DEVIATION_THRESHOLD_RAD = 0.35
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
    var baselineHeadNormal: FloatArray? = null
        private set
    @Volatile
    var headDeviationThresholdRad: Double = DEFAULT_HEAD_DEVIATION_THRESHOLD_RAD

    private val earSamples = mutableListOf<Float>()
    private val headNormalSamples = mutableListOf<FloatArray>()
    private var startTimeMs = 0L

    init { loadFromPrefs() }

    fun startCalibration() {
        earSamples.clear()
        headNormalSamples.clear()
        startTimeMs = System.currentTimeMillis()
        isCalibrating = true
        progress = 0f
        Log.i(TAG, "Calibration started")
    }

    /** Returns true when calibration completes. */
    fun addFrame(ear: Float, headNormal: FloatArray?): Boolean {
        if (!isCalibrating || ear <= 0f) return false
        val elapsed = (System.currentTimeMillis() - startTimeMs) / 1000.0
        progress = (elapsed / DURATION_SECONDS).toFloat().coerceIn(0f, 1f)
        earSamples.add(ear)
        if (headNormal != null) headNormalSamples.add(headNormal)
        if (elapsed >= DURATION_SECONDS) { finalise(); return true }
        return false
    }

    fun isEyesClosed(ear: Float) = ear in 0.01f..earThreshold

    /**
     * True if currentNormal deviates from the calibrated baseline by more than
     * headDeviationThresholdRad. Fails closed (returns false) when there's no
     * baseline or no current reading, rather than risking spurious alerts.
     */
    fun isHeadDeviated(currentNormal: FloatArray?): Boolean {
        val baseline = baselineHeadNormal ?: return false
        val current = currentNormal ?: return false
        return HeadPoseMath.angleBetween(baseline, current) > headDeviationThresholdRad.toFloat()
    }

    private fun finalise() {
        isCalibrating = false
        val result = CalibrationMath.compute(earSamples)
        if (result == null) { Log.w(TAG, "No samples — using default"); return }

        meanOpenEar = result.meanOpenEar
        earThreshold = result.earThreshold
        baselineHeadNormal = HeadPoseMath.averageNormal(headNormalSamples)
        isCalibrated = true
        progress = 1f
        Log.i(TAG, "Done — mean=$meanOpenEar threshold=$earThreshold (${result.sampleCount} samples), " +
                "headBaseline=${baselineHeadNormal?.joinToString(",") { "%.3f".format(it) } ?: "none"}")
        saveToPrefs()
    }

    private fun saveToPrefs() {
        val editor = prefs.edit()
            .putFloat(KEY_EAR_THRESHOLD, earThreshold)
            .putFloat(KEY_MEAN_OPEN_EAR,  meanOpenEar)
            .putBoolean(KEY_IS_CALIBRATED, true)
        val head = baselineHeadNormal
        if (head != null) {
            editor.putBoolean(KEY_HAS_HEAD_BASELINE, true)
                .putFloat(KEY_BASELINE_NORMAL_X, head[0])
                .putFloat(KEY_BASELINE_NORMAL_Y, head[1])
                .putFloat(KEY_BASELINE_NORMAL_Z, head[2])
        } else {
            editor.putBoolean(KEY_HAS_HEAD_BASELINE, false)
        }
        editor.apply()
    }

    private fun loadFromPrefs() {
        isCalibrated = prefs.getBoolean(KEY_IS_CALIBRATED, false)
        if (isCalibrated) {
            earThreshold = prefs.getFloat(KEY_EAR_THRESHOLD, DEFAULT_EAR_THRESHOLD)
            meanOpenEar  = prefs.getFloat(KEY_MEAN_OPEN_EAR,  0.31f)
            if (prefs.getBoolean(KEY_HAS_HEAD_BASELINE, false)) {
                baselineHeadNormal = floatArrayOf(
                    prefs.getFloat(KEY_BASELINE_NORMAL_X, 0f),
                    prefs.getFloat(KEY_BASELINE_NORMAL_Y, 0f),
                    prefs.getFloat(KEY_BASELINE_NORMAL_Z, 0f),
                )
            }
            Log.i(TAG, "Loaded — threshold=$earThreshold, headBaseline=${baselineHeadNormal != null}")
        }
    }

    fun reset() {
        prefs.edit().clear().apply()
        isCalibrated = false
        isCalibrating = false
        earThreshold = DEFAULT_EAR_THRESHOLD
        meanOpenEar = 0.31f
        baselineHeadNormal = null
        headDeviationThresholdRad = DEFAULT_HEAD_DEVIATION_THRESHOLD_RAD
        earSamples.clear()
        headNormalSamples.clear()
        progress = 0f
    }
}
