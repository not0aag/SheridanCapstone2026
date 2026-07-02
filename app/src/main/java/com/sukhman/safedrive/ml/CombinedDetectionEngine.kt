package com.sukhman.safedrive.ml

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import com.sukhman.safedrive.DebugState

class CombinedDetectionEngine(
    private val context: Context,
    val calibrationEngine: AndroidCalibrationEngine,
    val decisionEngine: AndroidDecisionEngine = AndroidDecisionEngine()
) : InferenceEngine {

    companion object {
        private const val TAG = "CombinedDetector"
    }

    private val faceMeshEngine = FaceMeshInferenceEngine(context)
    private val distractionEngine = DistractionInferenceEngine(context)
    private var faceMeshAvailable = false

    override suspend fun initialize() {
        try {
            faceMeshEngine.initialize()
            faceMeshAvailable = true
            Log.i(TAG, "Face mesh ready")
        } catch (e: Exception) {
            Log.w(TAG, "Face mesh unavailable (${e.message}) — drowsiness disabled")
        }
        distractionEngine.initialize()
        Log.i(TAG, "CombinedDetectionEngine ready (faceMesh=$faceMeshAvailable)")
    }

    override suspend fun runInference(frame: Bitmap): InferenceResult {
        // Always run distraction classifier
        val distractionResult = distractionEngine.runInference(frame)
        val isDistracted = distractionResult is InferenceResult.Distraction

        var earValue = 0f
        var landmarksResult: InferenceResult? = null

        if (faceMeshAvailable) {
            val meshResult = faceMeshEngine.runInference(frame)
            if (meshResult is InferenceResult.FaceLandmarks) {
                landmarksResult = meshResult
                earValue = EarCalculator.compute(meshResult.landmarks)
                DebugState.earValue = earValue
                DebugState.eyesClosed = calibrationEngine.isEyesClosed(earValue)
                DebugState.faceLandmarks = meshResult.landmarks
            } else {
                DebugState.faceLandmarks = emptyList()
            }
        }

        // Calibration mode — collect EAR samples, don't alert
        if (calibrationEngine.isCalibrating) {
            if (earValue > 0f) {
                val done = calibrationEngine.addFrame(earValue)
                DebugState.calibrationProgress = calibrationEngine.progress
                if (done) DebugState.isCalibrated = true
            }
            return landmarksResult ?: InferenceResult.NoDetection
        }

        // Detection mode
        if (faceMeshAvailable && earValue > 0f) {
            val eyesClosed = calibrationEngine.isEyesClosed(earValue)
            decisionEngine.addFrame(eyesClosed, isDistracted)
            val decision = decisionEngine.getDecision()
            DebugState.perclosPct = decision.perclosPct

            return when {
                decision.alertType == "DROWSY"      -> InferenceResult.Drowsiness(decision.perclosPct)
                decision.alertType == "DISTRACTED"  -> distractionResult
                else                                -> distractionResult
            }
        }

        return distractionResult
    }

    override fun close() {
        faceMeshEngine.close()
        distractionEngine.close()
    }
}
