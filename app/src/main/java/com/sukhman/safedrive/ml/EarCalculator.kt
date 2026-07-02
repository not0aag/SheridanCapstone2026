package com.sukhman.safedrive.ml

import kotlin.math.sqrt

object EarCalculator {
    // Same indices as ml/src/calibration.py
    private val LEFT_EYE  = intArrayOf(362, 385, 387, 263, 373, 380)
    private val RIGHT_EYE = intArrayOf(33,  160, 158, 133, 153, 144)

    fun compute(landmarks: List<FloatArray>): Float {
        if (landmarks.size < 468) return 0f
        return (ear(landmarks, LEFT_EYE) + ear(landmarks, RIGHT_EYE)) / 2f
    }

    private fun ear(landmarks: List<FloatArray>, idx: IntArray): Float {
        val p = idx.map { landmarks[it] }
        // EAR = (||p1-p5|| + ||p2-p4||) / (2 * ||p0-p3||)
        val a = dist(p[1], p[5])
        val b = dist(p[2], p[4])
        val c = dist(p[0], p[3])
        return if (c < 1e-6f) 0f else (a + b) / (2f * c)
    }

    private fun dist(a: FloatArray, b: FloatArray): Float {
        val dx = a[0] - b[0]; val dy = a[1] - b[1]
        return sqrt(dx * dx + dy * dy)
    }
}
