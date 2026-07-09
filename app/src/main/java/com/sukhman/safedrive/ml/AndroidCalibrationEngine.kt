package com.sukhman.safedrive.ml

import android.content.Context
import android.content.SharedPreferences
import android.util.Log

class AndroidCalibrationEngine(context: Context) {

    companion object {
        private const val TAG = "CalibrationEngine"
        private const val PREFS_NAME = "safedrive_calibration"
        private const val KEY_EAR_THRESHOLD  = "ear_threshold"
        private const val KEY_MEAN_OPEN_EAR  = "mean_open_ear"
        private const val KEY_NOSE_DX        = "baseline_nose_dx"
        private const val KEY_NOSE_DY        = "baseline_nose_dy"
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
    var progress = 0f
        private set

    var earThreshold   = DEFAULT_EAR_THRESHOLD; private set
    var meanOpenEar    = 0.31f;                 private set
    var baselineNoseDx = 0f;                    private set
    var baselineNoseDy = 0f;                    private set

    private val earSamples  = mutableListOf<Float>()
    private val noseDxSamples = mutableListOf<Float>()
    private val noseDySamples = mutableListOf<Float>()
    private var startTimeMs = 0L

    init { loadFromPrefs() }

    fun startCalibration() {
        earSamples.clear(); noseDxSamples.clear(); noseDySamples.clear()
        startTimeMs = System.currentTimeMillis()
        isCalibrating = true
        progress = 0f
        Log.i(TAG, "Calibration started")
    }

    /** Call every frame. Timer-based so progress advances even when face isn't detected. */
    fun addFrame(ear: Float, headMetrics: HeadPoseCalculator.HeadMetrics? = null): Boolean {
        if (!isCalibrating) return false
        val elapsed = (System.currentTimeMillis() - startTimeMs) / 1000.0
        progress = (elapsed / DURATION_SECONDS).toFloat().coerceIn(0f, 1f)
        if (ear > 0f) earSamples.add(ear)
        headMetrics?.let { noseDxSamples.add(it.noseDx); noseDySamples.add(it.noseDy) }
        if (elapsed >= DURATION_SECONDS) { finalise(); return true }
        return false
    }

    fun isEyesClosed(ear: Float) = ear in 0.01f..earThreshold

    fun isHeadDeviated(metrics: HeadPoseCalculator.HeadMetrics): Boolean {
        val baseline = HeadPoseCalculator.HeadMetrics(baselineNoseDx, baselineNoseDy)
        return HeadPoseCalculator.isDeviated(metrics, baseline)
    }

    private fun finalise() {
        isCalibrating = false

        // EAR threshold via CalibrationMath (filters bottom 10% blinks, same as calibration.py)
        val result = CalibrationMath.compute(earSamples)
        if (result != null) {
            meanOpenEar  = result.meanOpenEar
            earThreshold = result.earThreshold
        } else {
            Log.w(TAG, "No EAR samples — using default threshold")
        }

        // Head pose baseline — median of collected samples
        if (noseDxSamples.isNotEmpty()) {
            baselineNoseDx = noseDxSamples.sorted()[noseDxSamples.size / 2]
            baselineNoseDy = noseDySamples.sorted()[noseDySamples.size / 2]
        }

        isCalibrated = true
        progress = 1f
        Log.i(TAG, "Done — EAR threshold=$earThreshold nose=($baselineNoseDx,$baselineNoseDy)")
        saveToPrefs()
    }

    private fun saveToPrefs() {
        prefs.edit()
            .putFloat(KEY_EAR_THRESHOLD, earThreshold)
            .putFloat(KEY_MEAN_OPEN_EAR,  meanOpenEar)
            .putFloat(KEY_NOSE_DX,        baselineNoseDx)
            .putFloat(KEY_NOSE_DY,        baselineNoseDy)
            .putBoolean(KEY_IS_CALIBRATED, true)
            .apply()
    }

    private fun loadFromPrefs() {
        isCalibrated = prefs.getBoolean(KEY_IS_CALIBRATED, false)
        if (isCalibrated) {
            earThreshold   = prefs.getFloat(KEY_EAR_THRESHOLD, DEFAULT_EAR_THRESHOLD)
            meanOpenEar    = prefs.getFloat(KEY_MEAN_OPEN_EAR,  0.31f)
            baselineNoseDx = prefs.getFloat(KEY_NOSE_DX,        0f)
            baselineNoseDy = prefs.getFloat(KEY_NOSE_DY,        0f)
            Log.i(TAG, "Loaded — EAR=$earThreshold nose=($baselineNoseDx,$baselineNoseDy)")
        }
    }

    fun reset() {
        prefs.edit().clear().apply()
        isCalibrated = false; isCalibrating = false
        earThreshold = DEFAULT_EAR_THRESHOLD; meanOpenEar = 0.31f
        baselineNoseDx = 0f; baselineNoseDy = 0f
        earSamples.clear(); noseDxSamples.clear(); noseDySamples.clear()
        progress = 0f
    }
}
