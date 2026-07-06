package com.sukhman.safedrive.ml

import org.junit.Assert.*
import org.junit.Test

class CalibrationMathTest {

    @Test
    fun `empty samples returns null`() {
        assertNull(CalibrationMath.compute(emptyList()))
    }

    @Test
    fun `trims bottom 10 percent before averaging`() {
        // 10 samples, bottom 10% (1 sample = 0.10) dropped -> average of the remaining 9.
        val samples = listOf(0.10f, 0.30f, 0.30f, 0.30f, 0.30f, 0.30f, 0.30f, 0.30f, 0.30f, 0.30f)
        val result = CalibrationMath.compute(samples)

        assertNotNull(result)
        assertEquals(9, result!!.sampleCount)
        assertEquals(0.30f, result.meanOpenEar, 0.001f)
    }

    @Test
    fun `threshold is 75 percent of the mean open EAR`() {
        val samples = List(10) { 0.30f }
        val result = CalibrationMath.compute(samples)!!

        assertEquals(0.30f, result.meanOpenEar, 0.001f)
        assertEquals(0.225f, result.earThreshold, 0.001f)
    }

    @Test
    fun `single sample still produces a result`() {
        val result = CalibrationMath.compute(listOf(0.28f))

        assertNotNull(result)
        assertEquals(0.28f, result!!.meanOpenEar, 0.001f)
    }
}
