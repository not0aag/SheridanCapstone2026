package com.sukhman.safedrive.ml

import android.graphics.Bitmap

// Simple abstraction for ML inference. Implement this with a TFLite runner later.
interface InferenceEngine {
    suspend fun initialize()
    suspend fun runInference(frame: Bitmap): InferenceResult
    fun close()
}

sealed class InferenceResult {
    data class FaceLandmarks(val landmarks: List<FloatArray>) : InferenceResult() // x,y pairs per landmark
    data class Distraction(val label: String, val confidence: Float) : InferenceResult()
    data class Drowsiness(val perclos: Float) : InferenceResult()
    object NoDetection : InferenceResult()
}

