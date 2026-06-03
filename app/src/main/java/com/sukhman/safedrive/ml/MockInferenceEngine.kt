package com.sukhman.safedrive.ml

import android.graphics.Bitmap
import android.util.Log
import kotlinx.coroutines.delay
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/**
 * Mock inference engine for testing face landmark detection pipeline.
 * Generates synthetic face landmarks for demonstration purposes.
 *
 * This allows testing the full camera-to-ML pipeline without requiring a TFLite model.
 * Replace with FaceMeshInferenceEngine when ready to use real model.
 */
class MockInferenceEngine : InferenceEngine {

    private val TAG = "MockInferenceEngine"
    private var isInitialized = false
    private val random = Random(System.currentTimeMillis())

    // Simulate 68 facial landmarks (common in face detection libraries)
    private val numLandmarks = 68

    override suspend fun initialize() {
        Log.d(TAG, "Initializing mock inference engine")
        delay(500) // Simulate model loading time
        isInitialized = true
        Log.i(TAG, "Mock inference engine initialized (simulated)")
    }

    private var frameCount = 0

    override suspend fun runInference(frame: Bitmap): InferenceResult {
        if (!isInitialized) {
            Log.w(TAG, "Engine not initialized")
            return InferenceResult.NoDetection
        }

        delay(16) // ~60 FPS budget
        frameCount++

        // Every ~8 seconds fire a drowsiness alert, every ~15 seconds a distraction alert.
        // These show off the full alert pipeline during a demo.
        if (frameCount % 240 == 0) {
            Log.w(TAG, "Mock: drowsiness alert")
            return InferenceResult.Drowsiness(0.72f)
        }
        if (frameCount % 450 == 0) {
            Log.w(TAG, "Mock: distraction alert")
            return InferenceResult.Distraction("phone use", 0.91f)
        }

        // 85% of the time return face landmarks, 15% no detection
        return if (random.nextFloat() < 0.85f) {
            val landmarks = generateMockLandmarks(frame.width, frame.height)
            Log.d(TAG, "Mock face detected with ${landmarks.size} landmarks")
            InferenceResult.FaceLandmarks(landmarks)
        } else {
            Log.d(TAG, "Mock: No face detected")
            InferenceResult.NoDetection
        }
    }

    // Returns normalized coordinates in [0, 1] matching MediaPipe Face Mesh convention.
    private fun generateMockLandmarks(width: Int, height: Int): List<FloatArray> {
        val landmarks = mutableListOf<FloatArray>()

        val cx = 0.5f
        val cy = 0.48f
        val fw = 0.38f
        val fh = 0.45f

        // Face contour (17 points)
        for (i in 0 until 17) {
            val angle = (i / 16.0) * Math.PI - Math.PI / 2
            val x = cx + (cos(angle) * fw).toFloat()
            val y = cy + (sin(angle) * fh).toFloat()
            landmarks.add(floatArrayOf(x, y, 0f))
        }

        // Left eyebrow (5 points)
        val leftBrowY = cy - fh * 0.30f
        for (i in 0 until 5) {
            landmarks.add(floatArrayOf(cx - fw * 0.35f + i * fw * 0.15f, leftBrowY, 0f))
        }

        // Right eyebrow (5 points)
        val rightBrowY = cy - fh * 0.30f
        for (i in 0 until 5) {
            landmarks.add(floatArrayOf(cx + fw * 0.05f + i * fw * 0.15f, rightBrowY, 0f))
        }

        // Nose bridge (4 points)
        for (i in 0 until 4) {
            landmarks.add(floatArrayOf(cx, cy - fh * 0.20f + i * fh * 0.15f, 0f))
        }

        // Nose bottom (5 points)
        val noseY = cy + fh * 0.05f
        for (i in 0 until 5) {
            landmarks.add(floatArrayOf(cx - fw * 0.10f + i * fw * 0.05f, noseY, 0f))
        }

        // Left eye (6 points)
        val lEyeX = cx - fw * 0.25f
        val eyeY  = cy - fh * 0.15f
        val ew    = fw * 0.14f
        val eh    = fh * 0.07f
        for (i in 0 until 6) {
            val a = (i / 5.0) * 2 * Math.PI
            landmarks.add(floatArrayOf(lEyeX + (cos(a) * ew).toFloat(), eyeY + (sin(a) * eh).toFloat(), 0f))
        }

        // Right eye (6 points)
        val rEyeX = cx + fw * 0.25f
        for (i in 0 until 6) {
            val a = (i / 5.0) * 2 * Math.PI
            landmarks.add(floatArrayOf(rEyeX + (cos(a) * ew).toFloat(), eyeY + (sin(a) * eh).toFloat(), 0f))
        }

        // Mouth outer (12 points)
        val mouthY = cy + fh * 0.30f
        val mw     = fw * 0.32f
        val mh     = fh * 0.09f
        for (i in 0 until 12) {
            val a = (i / 11.0) * Math.PI - Math.PI / 2
            landmarks.add(floatArrayOf(cx + (cos(a) * mw).toFloat(), mouthY + (sin(a) * mh).toFloat(), 0f))
        }

        // Mouth inner (8 points)
        for (i in 0 until 8) {
            val a = (i / 7.0) * Math.PI - Math.PI / 2
            landmarks.add(floatArrayOf(cx + (cos(a) * mw * 0.8f).toFloat(), mouthY + (sin(a) * mh * 0.6f).toFloat(), 0f))
        }

        // Small random jitter (±0.003 normalized ≈ ±2px on a 720p frame)
        landmarks.forEach { lm ->
            lm[0] += (random.nextFloat() - 0.5f) * 0.006f
            lm[1] += (random.nextFloat() - 0.5f) * 0.006f
        }

        return landmarks
    }

    override fun close() {
        isInitialized = false
        Log.i(TAG, "Mock inference engine closed")
    }
}
