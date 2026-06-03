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
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong

// Analyzer that measures FPS and calls the provided InferenceEngine asynchronously.
class FrameAnalyzer(
    private val engine: InferenceEngine,
    private val alertManager: AlertManager? = null
) : ImageAnalysis.Analyzer {

    private val frames = AtomicInteger(0)
    private val windowStart = AtomicLong(System.currentTimeMillis())
    private val scope = CoroutineScope(Dispatchers.Default)

    override fun analyze(image: ImageProxy) {
        try {
            val now = System.currentTimeMillis()
            frames.incrementAndGet()
            val start = windowStart.get()
            val elapsed = now - start
            if (elapsed >= 1000L) {
                val count = frames.getAndSet(0)
                windowStart.set(now)
                val fps = count * 1000.0 / (if (elapsed == 0L) 1.0 else elapsed.toDouble())
                Log.i("FrameAnalyzer", String.format("Approx FPS: %.2f (frames=%d elapsed=%dms)", fps, count, elapsed))
                DebugState.fps = fps
            }

            // Convert ImageProxy to Bitmap for ML inference
            val bitmap = imageProxyToBitmap(image)

            // Call inference asynchronously
            scope.launch {
                try {
                    val result = engine.runInference(bitmap)
                    when (result) {
                        is InferenceResult.NoDetection -> {
                            DebugState.faceLandmarks = emptyList()
                            DebugState.currentPrediction = "Safe driving"
                            DebugState.predictionConfidence = 0f
                        }
                        is InferenceResult.FaceLandmarks -> {
                            DebugState.faceLandmarks = result.landmarks
                            DebugState.currentPrediction = "Face tracked"
                            Log.d("FrameAnalyzer", "Face detected with ${result.landmarks.size} landmarks")
                        }
                        is InferenceResult.Distraction -> {
                            Log.w("FrameAnalyzer", "Distraction detected: ${result.label} (${result.confidence})")
                            DebugState.currentPrediction = result.label
                            DebugState.predictionConfidence = result.confidence
                            alertManager?.triggerDistractionAlert(result.label, result.confidence)
                        }
                        is InferenceResult.Drowsiness -> {
                            Log.w("FrameAnalyzer", "Drowsiness detected: PERCLOS=${result.perclos}")
                            DebugState.currentPrediction = "Drowsiness"
                            alertManager?.triggerDrowsinessAlert(result.perclos)
                        }
                    }
                } catch (e: Exception) {
                    Log.w("FrameAnalyzer", "Inference failed: ${e.message}")
                }
            }
        } finally {
            image.close()
        }
    }

    /**
     * Convert CameraX ImageProxy (YUV_420_888) to Bitmap
     */
    private fun imageProxyToBitmap(image: ImageProxy): Bitmap {
        val yBuffer = image.planes[0].buffer
        val uBuffer = image.planes[1].buffer
        val vBuffer = image.planes[2].buffer

        val ySize = yBuffer.remaining()
        val uSize = uBuffer.remaining()
        val vSize = vBuffer.remaining()

        val nv21 = ByteArray(ySize + uSize + vSize)

        // U and V are swapped
        yBuffer.get(nv21, 0, ySize)
        vBuffer.get(nv21, ySize, vSize)
        uBuffer.get(nv21, ySize + vSize, uSize)

        val yuvImage = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
        val out = ByteArrayOutputStream()
        yuvImage.compressToJpeg(Rect(0, 0, image.width, image.height), 85, out)
        val imageBytes = out.toByteArray()
        val bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)

        // Rotate bitmap if needed (front camera is often rotated)
        return rotateBitmap(bitmap, image.imageInfo.rotationDegrees)
    }

    /**
     * Rotate bitmap by specified degrees
     */
    private fun rotateBitmap(bitmap: Bitmap, degrees: Int): Bitmap {
        if (degrees == 0) return bitmap

        val matrix = Matrix()
        matrix.postRotate(degrees.toFloat())
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }
}

