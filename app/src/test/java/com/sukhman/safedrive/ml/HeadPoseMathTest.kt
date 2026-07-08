package com.sukhman.safedrive.ml

import org.junit.Assert.*
import org.junit.Test
import kotlin.math.PI

class HeadPoseMathTest {

    /**
     * Builds a synthetic 468-point landmark set with nose tip (1), left-eye-outer
     * (263), and right-eye-outer (33) placed at known 3-D positions so the
     * resulting face normal is predictable.
     */
    private fun buildLandmarks(nose: FloatArray, left: FloatArray, right: FloatArray): List<FloatArray> {
        val landmarks = MutableList(468) { floatArrayOf(0f, 0f, 0f) }
        landmarks[1] = nose
        landmarks[263] = left
        landmarks[33] = right
        return landmarks
    }

    @Test
    fun `known configuration produces the expected face normal direction`() {
        // nose=(0,0,0), left-nose=(1,0,0), right-nose=(0,1,0)
        // cross((1,0,0),(0,1,0)) = (0,0,1) -> normalized (0,0,1)
        val landmarks = buildLandmarks(
            nose = floatArrayOf(0f, 0f, 0f),
            left = floatArrayOf(1f, 0f, 0f),
            right = floatArrayOf(0f, 1f, 0f),
        )
        val normal = HeadPoseMath.computeFaceNormal(landmarks)
        assertNotNull(normal)
        assertArrayEquals(floatArrayOf(0f, 0f, 1f), normal, 0.0001f)
    }

    @Test
    fun `fewer than 468 landmarks returns null`() {
        val tooFew = List(100) { floatArrayOf(0f, 0f, 0f) }
        assertNull(HeadPoseMath.computeFaceNormal(tooFew))
    }

    @Test
    fun `degenerate collinear landmarks return null`() {
        // nose, left, right all on the same line -> zero cross product -> null
        val landmarks = buildLandmarks(
            nose = floatArrayOf(0f, 0f, 0f),
            left = floatArrayOf(1f, 0f, 0f),
            right = floatArrayOf(2f, 0f, 0f),
        )
        assertNull(HeadPoseMath.computeFaceNormal(landmarks))
    }

    @Test
    fun `angleBetween identical vectors is zero`() {
        val v = floatArrayOf(0f, 0f, 1f)
        assertEquals(0f, HeadPoseMath.angleBetween(v, v), 0.0001f)
    }

    @Test
    fun `angleBetween orthogonal vectors is half pi`() {
        val a = floatArrayOf(1f, 0f, 0f)
        val b = floatArrayOf(0f, 1f, 0f)
        assertEquals((PI / 2).toFloat(), HeadPoseMath.angleBetween(a, b), 0.0001f)
    }

    @Test
    fun `angleBetween opposite vectors is pi`() {
        val a = floatArrayOf(0f, 0f, 1f)
        val b = floatArrayOf(0f, 0f, -1f)
        assertEquals(PI.toFloat(), HeadPoseMath.angleBetween(a, b), 0.0001f)
    }

    @Test
    fun `averageNormal of identical vectors returns the same vector`() {
        val v = floatArrayOf(0f, 0f, 1f)
        val avg = HeadPoseMath.averageNormal(listOf(v, v, v))
        assertNotNull(avg)
        assertArrayEquals(v, avg, 0.0001f)
    }

    @Test
    fun `averageNormal of two orthogonal unit vectors bisects them`() {
        val a = floatArrayOf(1f, 0f, 0f)
        val b = floatArrayOf(0f, 1f, 0f)
        val avg = HeadPoseMath.averageNormal(listOf(a, b))
        assertNotNull(avg)
        val expected = 1f / kotlin.math.sqrt(2f)
        assertArrayEquals(floatArrayOf(expected, expected, 0f), avg, 0.001f)
    }

    @Test
    fun `averageNormal of empty list returns null`() {
        assertNull(HeadPoseMath.averageNormal(emptyList()))
    }
}
