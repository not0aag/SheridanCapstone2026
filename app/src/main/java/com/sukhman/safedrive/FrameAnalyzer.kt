package com.sukhman.safedrive

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Matrix
import android.graphics.Rect
import android.graphics.YuvImage
import android.util.Log
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.sukhman.safedrive.ml.InferenceEngine
import com.sukhman.safedrive.ml.InferenceResult
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong

class FrameAnalyzer(
    private val engine: InferenceEngine,
    private val alertManager: AlertManager? = null,
    private val scope: CoroutineScope
) : ImageAnalysis.Analyzer {

    private val frames = AtomicInteger(0)
    private val windowStart = AtomicLong(System.currentTimeMillis())

    // Ensures only one inference runs at a time.
    // TFLite Interpreter is not thread-safe — concurrent calls crash.
    // With STRATEGY_KEEP_ONLY_LATEST, CameraX drops frames while we're busy anyway.
    private val inferenceRunning = AtomicBoolean(false)

    override fun analyze(image: ImageProxy) {
        try {
            // FPS counter
            val now = System.currentTimeMillis()
            frames.incrementAndGet()
            val elapsed = now - windowStart.get()
            if (elapsed >= 1000L) {
                val count = frames.getAndSet(0)
                windowStart.set(now)
                val fps = count * 1000.0 / elapsed.coerceAtLeast(1L).toDouble()
                DebugState.fps = fps
                Log.d("FrameAnalyzer", "FPS: ${"%.1f".format(fps)}")
            }

            // Drop frame if previous inference hasn't finished — avoids concurrent TFLite calls.
            if (!inferenceRunning.compareAndSet(false, true)) return

            val bitmap = imageProxyToBitmap(image)

            scope.launch {
                try {
                    val result = engine.runInference(bitmap)
                    handleResult(result)
                } catch (e: Exception) {
                    Log.w("FrameAnalyzer", "Inference error: ${e.message}")
                } finally {
                    inferenceRunning.set(false)
                }
            }
        } finally {
            image.close()
        }
    }

    private fun handleResult(result: InferenceResult) {
        when (result) {
            is InferenceResult.NoDetection -> {
                DebugState.faceLandmarks = emptyList()
                DebugState.currentPrediction = "Safe driving"
                DebugState.predictionConfidence = 0f
            }
            is InferenceResult.FaceLandmarks -> {
                DebugState.faceLandmarks = result.landmarks
                DebugState.currentPrediction = "Face tracked"
                DebugState.predictionConfidence = 0f
            }
            is InferenceResult.Distraction -> {
                Log.w("FrameAnalyzer", "DISTRACTION: ${result.label} (${result.confidence})")
                DebugState.faceLandmarks = emptyList()
                DebugState.currentPrediction = result.label
                DebugState.predictionConfidence = result.confidence
                alertManager?.triggerDistractionAlert(result.label, result.confidence)
            }
            is InferenceResult.Drowsiness -> {
                Log.w("FrameAnalyzer", "DROWSINESS: PERCLOS=${result.perclos}")
                DebugState.currentPrediction = "Drowsiness"
                DebugState.predictionConfidence = result.perclos
                alertManager?.triggerDrowsinessAlert(result.perclos)
            }
        }
    }

    fun cancel() {
        scope.cancel()
    }

    private fun imageProxyToBitmap(image: ImageProxy): Bitmap {
        val yBuffer = image.planes[0].buffer
        val uBuffer = image.planes[1].buffer
        val vBuffer = image.planes[2].buffer

        val ySize = yBuffer.remaining()
        val uSize = uBuffer.remaining()
        val vSize = vBuffer.remaining()

        val nv21 = ByteArray(ySize + uSize + vSize)
        yBuffer.get(nv21, 0, ySize)
        vBuffer.get(nv21, ySize, vSize)         // V before U = NV21
        uBuffer.get(nv21, ySize + vSize, uSize)

        val yuvImage = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
        val out = ByteArrayOutputStream()
        yuvImage.compressToJpeg(Rect(0, 0, image.width, image.height), 85, out)
        val bytes = out.toByteArray()
        val bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)

        return rotateBitmap(bmp, image.imageInfo.rotationDegrees)
    }

    private fun rotateBitmap(bitmap: Bitmap, degrees: Int): Bitmap {
        if (degrees == 0) return bitmap
        val matrix = Matrix().apply { postRotate(degrees.toFloat()) }
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }
}
