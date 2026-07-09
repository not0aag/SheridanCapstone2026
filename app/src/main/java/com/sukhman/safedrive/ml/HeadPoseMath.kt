package com.sukhman.safedrive.ml

import kotlin.math.acos
import kotlin.math.sqrt

/**
 * Lightweight head-orientation proxy — no OpenCV/solvePnP dependency.
 *
 * Approximates face-forward direction as the cross product of two edge
 * vectors (nose tip -> each eye-outer corner), instead of a full
 * rotation-vector solve. Landmarks arrive already normalized to [0, 1]
 * (x, y, z on the same scale) from FaceMeshInferenceEngine, so the cross
 * product is taken on them directly.
 */
object HeadPoseMath {
    // Subset of ml/src/calibration.py HEAD_POSE_INDICES: nose tip, L-eye-outer, R-eye-outer
    private const val NOSE_TIP = 1
    private const val LEFT_EYE_OUTER = 263
    private const val RIGHT_EYE_OUTER = 33

    fun computeFaceNormal(landmarks: List<FloatArray>): FloatArray? {
        if (landmarks.size < 468) return null
        val nose = landmarks[NOSE_TIP]
        val left = landmarks[LEFT_EYE_OUTER]
        val right = landmarks[RIGHT_EYE_OUTER]
        return normalize(cross(sub(left, nose), sub(right, nose)))
    }

    /** Angle in radians between two unit vectors via acos(dot), clamped for fp safety. */
    fun angleBetween(a: FloatArray, b: FloatArray): Float {
        val dot = (a[0] * b[0] + a[1] * b[1] + a[2] * b[2]).coerceIn(-1f, 1f)
        return acos(dot)
    }

    /** Averages a set of per-frame unit normals into one baseline unit vector. */
    fun averageNormal(normals: List<FloatArray>): FloatArray? {
        if (normals.isEmpty()) return null
        var sx = 0f; var sy = 0f; var sz = 0f
        for (v in normals) { sx += v[0]; sy += v[1]; sz += v[2] }
        return normalize(floatArrayOf(sx / normals.size, sy / normals.size, sz / normals.size))
    }

    private fun sub(a: FloatArray, b: FloatArray) =
        floatArrayOf(a[0] - b[0], a[1] - b[1], a[2] - b[2])

    private fun cross(a: FloatArray, b: FloatArray) = floatArrayOf(
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    )

    private fun normalize(v: FloatArray): FloatArray? {
        val mag = sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        return if (mag < 1e-6f) null else floatArrayOf(v[0] / mag, v[1] / mag, v[2] / mag)
    }
}
