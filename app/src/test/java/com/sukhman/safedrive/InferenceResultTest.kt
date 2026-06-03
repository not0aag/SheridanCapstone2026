package com.sukhman.safedrive

import com.sukhman.safedrive.ml.InferenceResult
import org.junit.Assert.*
import org.junit.Test

class InferenceResultTest {

    @Test
    fun `FaceLandmarks stores landmarks correctly`() {
        val lm = listOf(floatArrayOf(10f, 20f, 0f), floatArrayOf(30f, 40f, 1f))
        val result = InferenceResult.FaceLandmarks(lm)
        assertEquals(2, result.landmarks.size)
        assertEquals(10f, result.landmarks[0][0], 0.001f)
        assertEquals(40f, result.landmarks[1][1], 0.001f)
    }

    @Test
    fun `Distraction stores label and confidence`() {
        val result = InferenceResult.Distraction("phone", 0.87f)
        assertEquals("phone", result.label)
        assertEquals(0.87f, result.confidence, 0.001f)
    }

    @Test
    fun `Drowsiness stores perclos`() {
        val result = InferenceResult.Drowsiness(0.65f)
        assertEquals(0.65f, result.perclos, 0.001f)
    }

    @Test
    fun `NoDetection is a singleton object`() {
        assertSame(InferenceResult.NoDetection, InferenceResult.NoDetection)
    }

    @Test
    fun `sealed class exhaustive when-branching compiles`() {
        val results: List<InferenceResult> = listOf(
            InferenceResult.NoDetection,
            InferenceResult.FaceLandmarks(emptyList()),
            InferenceResult.Distraction("x", 0f),
            InferenceResult.Drowsiness(0f)
        )
        val labels = results.map { r ->
            when (r) {
                is InferenceResult.NoDetection -> "none"
                is InferenceResult.FaceLandmarks -> "face"
                is InferenceResult.Distraction -> "distraction"
                is InferenceResult.Drowsiness -> "drowsiness"
            }
        }
        assertEquals(listOf("none", "face", "distraction", "drowsiness"), labels)
    }
}
