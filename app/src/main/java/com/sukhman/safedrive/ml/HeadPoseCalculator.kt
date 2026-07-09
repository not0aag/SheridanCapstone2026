package com.sukhman.safedrive.ml

import kotlin.math.sqrt

object HeadPoseCalculator {
    // Same landmark indices as calibration.py
    private const val NOSE      = 1
    private const val LEFT_EYE  = 263  // outer corner
    private const val RIGHT_EYE = 33   // outer corner

    data class HeadMetrics(val noseDx: Float, val noseDy: Float)

    // Returns nose position normalised by inter-eye distance, relative to eye midpoint.
    // Mirrors how calibration.py records baseline_nose (normalised x/y offset).
    fun compute(landmarks: List<FloatArray>): HeadMetrics? {
        if (landmarks.size < 468) return null
        val nose     = landmarks[NOSE]
        val leftEye  = landmarks[LEFT_EYE]
        val rightEye = landmarks[RIGHT_EYE]

        val midX = (leftEye[0] + rightEye[0]) / 2f
        val midY = (leftEye[1] + rightEye[1]) / 2f
        val iod  = dist(leftEye, rightEye).coerceAtLeast(1f)   // inter-ocular distance

        return HeadMetrics(
            noseDx = (nose[0] - midX) / iod,
            noseDy = (nose[1] - midY) / iod
        )
    }

    // True when current head orientation has moved far enough from calibrated baseline.
    // Threshold 0.20 ≈ 25° deviation — matches HEAD_DEVIATION_THRESHOLD in safe_drive_detector.py
    fun isDeviated(current: HeadMetrics, baseline: HeadMetrics, threshold: Float = 0.20f): Boolean {
        val dx = current.noseDx - baseline.noseDx
        val dy = current.noseDy - baseline.noseDy
        return sqrt(dx * dx + dy * dy) > threshold
    }

    private fun dist(a: FloatArray, b: FloatArray): Float {
        val dx = a[0] - b[0]; val dy = a[1] - b[1]
        return sqrt(dx * dx + dy * dy)
    }
}
