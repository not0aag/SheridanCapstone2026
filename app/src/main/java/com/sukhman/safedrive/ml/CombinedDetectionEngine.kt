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
        DebugState.drowsinessAvailable = faceMeshAvailable
        distractionEngine.initialize()
        Log.i(TAG, "CombinedDetectionEngine ready (faceMesh=$faceMeshAvailable)")
    }

    override suspend fun runInference(frame: Bitmap): InferenceResult {
        // Always run distraction classifier
        val distractionResult = distractionEngine.runInference(frame)
        val isDistracted = distractionResult is InferenceResult.Distraction

        var earValue = 0f
        var headMetrics: HeadPoseCalculator.HeadMetrics? = null
        var landmarksResult: InferenceResult? = null

        if (faceMeshAvailable) {
            val meshResult = faceMeshEngine.runInference(frame)
            if (meshResult is InferenceResult.FaceLandmarks) {
                landmarksResult = meshResult
                earValue = EarCalculator.compute(meshResult.landmarks)
                headMetrics = HeadPoseCalculator.compute(meshResult.landmarks)
                DebugState.earValue = earValue
                DebugState.eyesClosed = calibrationEngine.isEyesClosed(earValue)
                DebugState.faceLandmarks = meshResult.landmarks
            } else {
                DebugState.faceLandmarks = emptyList()
            }
        }

        // Calibration mode — always tick the timer; collect EAR + head pose when face is visible
        if (calibrationEngine.isCalibrating) {
            val done = calibrationEngine.addFrame(earValue, headMetrics)
            DebugState.calibrationProgress = calibrationEngine.progress
            if (done) DebugState.isCalibrated = true
            return landmarksResult ?: InferenceResult.NoDetection
        }

        // Detection mode
        if (faceMeshAvailable && earValue > 0f) {
            // Face detected — use two-signal approach: BOTH head deviation AND classifier must agree
            val eyesClosed = calibrationEngine.isEyesClosed(earValue)
            val headDeviated = if (headMetrics != null) calibrationEngine.isHeadDeviated(headMetrics) else false
            decisionEngine.addFrame(eyesClosed, headDeviated, isDistracted)
            val decision = decisionEngine.getDecision()
            DebugState.perclosPct = decision.perclosPct

            return when (decision.alertType) {
                "DROWSY"     -> InferenceResult.Drowsiness(decision.perclosPct)
                "DISTRACTED" -> distractionResult
                else         -> InferenceResult.NoDetection
            }
        }

        // Face not detected by face mesh (emulator / no face in frame) — fall back to classifier only
        return distractionResult
    }

    override fun close() {
        faceMeshEngine.close()
        distractionEngine.close()
    }
}
