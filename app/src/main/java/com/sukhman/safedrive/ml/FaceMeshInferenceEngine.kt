package com.sukhman.safedrive.ml

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.support.common.FileUtil
import org.tensorflow.lite.support.image.ImageProcessor
import org.tensorflow.lite.support.image.TensorImage
import org.tensorflow.lite.support.image.ops.ResizeOp
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * TFLite inference engine for face landmark detection.
 *
 * Model: MediaPipe face_landmark.tflite (raw TFLite, not the .task bundle)
 *   Input:  float32[1, 192, 192, 3]  — RGB image normalised to [0, 1]
 *   Output 0: float32[1, 1404]       — 468 landmarks × (x, y, z), flattened
 *   Output 1: float32[1]             — face presence score
 *
 * Download: https://storage.googleapis.com/mediapipe-assets/face_landmark.tflite
 * Place at:  app/src/main/assets/models/face_landmarker.tflite
 */
class FaceMeshInferenceEngine(
    private val context: Context,
    private val modelPath: String = "models/face_landmarker.tflite",
    private val numThreads: Int = 4,
    private val inputSize: Int = 192
) : InferenceEngine {

    private val TAG = "FaceMeshEngine"

    private var interpreter: Interpreter? = null
    private var imageProcessor: ImageProcessor? = null
    private var inputBuffer: ByteBuffer? = null

    // Output 0: shape [1, 1, 1, 1404] — 468 landmarks × 3 floats, nested 4-D
    private val outputLandmarks = Array(1) { Array(1) { Array(1) { FloatArray(1404) } } }
    // Output 1: face presence score (shape [1, 1, 1, 1] — same 4-D nesting as landmarks)
    private val outputScore = Array(1) { Array(1) { Array(1) { FloatArray(1) } } }

    override suspend fun initialize() {
        withContext(Dispatchers.IO) {
            try {
                val model = FileUtil.loadMappedFile(context, modelPath)
                val options = Interpreter.Options().apply {
                    numThreads = this@FaceMeshInferenceEngine.numThreads
                    useNNAPI = true
                }
                interpreter = Interpreter(model, options)

                imageProcessor = ImageProcessor.Builder()
                    .add(ResizeOp(inputSize, inputSize, ResizeOp.ResizeMethod.BILINEAR))
                    .build()

                // float32 per channel, 3 channels (RGB), plus batch dimension handled by TFLite
                inputBuffer = ByteBuffer.allocateDirect(inputSize * inputSize * 3 * 4).apply {
                    order(ByteOrder.nativeOrder())
                }

                Log.i(TAG, "TFLite face mesh model loaded from $modelPath")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to load model", e)
                throw RuntimeException("Cannot load face mesh model: ${e.message}", e)
            }
        }
    }

    override suspend fun runInference(frame: Bitmap): InferenceResult = withContext(Dispatchers.Default) {
        val interp = interpreter ?: return@withContext InferenceResult.NoDetection

        try {
            val buf = preprocessImage(frame)

            val inputs = arrayOf<Any>(buf)
            val outputs = mapOf(
                0 to outputLandmarks,
                1 to outputScore
            )
            interp.runForMultipleInputsOutputs(inputs, outputs)

            if (outputScore[0][0][0][0] < 0.5f) return@withContext InferenceResult.NoDetection

            val flat = outputLandmarks[0][0][0]  // unwrap [1,1,1,1404] → FloatArray(1404)
            val landmarks = (0 until 468).map { i ->
                floatArrayOf(
                    flat[i * 3]     * frame.width,
                    flat[i * 3 + 1] * frame.height,
                    flat[i * 3 + 2]
                )
            }

            Log.d(TAG, "Face detected (score=${outputScore[0]}), ${landmarks.size} landmarks")
            InferenceResult.FaceLandmarks(landmarks)

        } catch (e: Exception) {
            Log.e(TAG, "Inference failed", e)
            InferenceResult.NoDetection
        }
    }

    private fun preprocessImage(bitmap: Bitmap): ByteBuffer {
        val processor = imageProcessor ?: throw IllegalStateException("Processor not initialised")
        val buf = inputBuffer ?: throw IllegalStateException("Input buffer not initialised")

        val tensorImage = TensorImage.fromBitmap(bitmap)
        val processed = processor.process(tensorImage)

        buf.rewind()
        val pixels = IntArray(inputSize * inputSize)
        processed.bitmap.getPixels(pixels, 0, inputSize, 0, 0, inputSize, inputSize)
        for (pixel in pixels) {
            buf.putFloat(((pixel shr 16) and 0xFF) / 255f) // R
            buf.putFloat(((pixel shr 8) and 0xFF) / 255f)  // G
            buf.putFloat((pixel and 0xFF) / 255f)           // B
        }
        buf.rewind()
        return buf
    }

    override fun close() {
        interpreter?.close()
        interpreter = null
        imageProcessor = null
        inputBuffer = null
        Log.i(TAG, "TFLite interpreter closed")
    }
}
