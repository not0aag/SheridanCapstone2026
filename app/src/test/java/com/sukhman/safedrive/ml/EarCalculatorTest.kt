package com.sukhman.safedrive.ml

import org.junit.Assert.*
import org.junit.Test

class EarCalculatorTest {

    private val leftEye = intArrayOf(362, 385, 387, 263, 373, 380)
    private val rightEye = intArrayOf(33, 160, 158, 133, 153, 144)

    /**
     * Builds a synthetic 468-point landmark set with both eyes positioned as either
     * wide-open (large vertical spread relative to horizontal width) or closed
     * (near-zero vertical spread), matching the geometry EarCalculator expects:
     * idx = [p0, p1, p2, p3, p4, p5], ear = (dist(p1,p5) + dist(p2,p4)) / (2*dist(p0,p3)).
     */
    private fun buildLandmarks(eyesOpen: Boolean): List<FloatArray> {
        val landmarks = MutableList(468) { floatArrayOf(0f, 0f) }
        val verticalSpread = if (eyesOpen) 2f else 0.05f

        fun placeEye(idx: IntArray, xOffset: Float) {
            landmarks[idx[0]] = floatArrayOf(xOffset + 0f, 0f)   // p0 — left corner
            landmarks[idx[1]] = floatArrayOf(xOffset + 3f, -verticalSpread) // p1 — top-outer lid
            landmarks[idx[2]] = floatArrayOf(xOffset + 7f, -verticalSpread) // p2 — top-inner lid
            landmarks[idx[3]] = floatArrayOf(xOffset + 10f, 0f)  // p3 — right corner
            landmarks[idx[4]] = floatArrayOf(xOffset + 7f, verticalSpread)  // p4 — bottom-inner lid
            landmarks[idx[5]] = floatArrayOf(xOffset + 3f, verticalSpread) // p5 — bottom-outer lid
        }

        placeEye(leftEye, xOffset = 0f)
        placeEye(rightEye, xOffset = 20f)
        return landmarks
    }

    @Test
    fun `open eyes produce a higher EAR than closed eyes`() {
        val openEar = EarCalculator.compute(buildLandmarks(eyesOpen = true))
        val closedEar = EarCalculator.compute(buildLandmarks(eyesOpen = false))

        assertTrue("open EAR ($openEar) should exceed closed EAR ($closedEar)", openEar > closedEar)
    }

    @Test
    fun `EAR matches the expected geometric ratio for a known configuration`() {
        // verticalSpread=2, horizontal width=10 -> ear = (4 + 4) / (2*10) = 0.4
        val ear = EarCalculator.compute(buildLandmarks(eyesOpen = true))
        assertEquals(0.4f, ear, 0.01f)
    }

    @Test
    fun `fewer than 468 landmarks returns zero`() {
        val tooFew = List(100) { floatArrayOf(0f, 0f) }
        assertEquals(0f, EarCalculator.compute(tooFew), 0.0001f)
    }
}
