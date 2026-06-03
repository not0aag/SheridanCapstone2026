package com.sukhman.safedrive.ml

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.support.common.FileUtil
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * Real distraction classifier using the team's MobileNetV2 TFLite model.
 *
 * Model: ml-models/week3_finetuning (Harrison's week 3 fine-tuned model, ~91% val accuracy)
 *   Input:  float32[1, 224, 224, 3] — RGB image normalised to [0, 1]
 *   Output: float32[1, 10]          — softmax probabilities for 10 classes
 *
 * Classes (State Farm Distracted Driver dataset):
 *   0 = Safe driving
 *   1 = Texting - right hand
 *   2 = Talking on phone - right hand
 *   3 = Texting - left hand
 *   4 = Talking on phone - left hand
 *   5 = Operating radio
 *   6 = Drinking
 *   7 = Reaching behind
 *   8 = Hair and makeup
 *   9 = Talking to passenger
 *
 * Place the model at: app/src/main/assets/models/distraction_classifier.tflite
 */
class DistractionInferenceEngine(
    private val context: Context,
    private val modelPath: String = "models/distraction_classifier.tflite",
    private val numThreads: Int = 4,
    private val confidenceThreshold: Float = 0.65f
) : InferenceEngine {

    companion object {
        private const val TAG = "DistractionEngine"
        private const val INPUT_SIZE = 224

        private val CLASS_LABELS = mapOf(
            0 to "Safe driving",
            1 to "Texting - right hand",
            2 to "Talking on phone - right",
            3 to "Texting - left hand",
            4 to "Talking on phone - left",
            5 to "Operating radio",
            6 to "Drinking",
            7 to "Reaching behind",
            8 to "Hair & makeup",
            9 to "Talking to passenger"
        )
    }

    private var interpreter: Interpreter? = null
    private val outputBuffer = Array(1) { FloatArray(10) }

    override suspend fun initialize() {
        withContext(Dispatchers.IO) {
            val model = FileUtil.loadMappedFile(context, modelPath)
            val options = Interpreter.Options().apply {
                numThreads = this@DistractionInferenceEngine.numThreads
                useNNAPI = true
            }
            interpreter = Interpreter(model, options)
            Log.i(TAG, "MobileNetV2 distraction model loaded from $modelPath")
        }
    }

    override suspend fun runInference(frame: Bitmap): InferenceResult = withContext(Dispatchers.Default) {
        val interp = interpreter ?: return@withContext InferenceResult.NoDetection

        val inputBuffer = preprocessBitmap(frame)

        outputBuffer[0].fill(0f)
        interp.run(inputBuffer, outputBuffer)

        val probs = outputBuffer[0]
        val topClass = probs.indices.maxByOrNull { probs[it] } ?: 0
        val topConf = probs[topClass]

        Log.d(TAG, "Prediction: class=$topClass (${CLASS_LABELS[topClass]}) conf=${"%.2f".format(topConf)}")

        when {
            topClass == 0 || topConf < confidenceThreshold -> InferenceResult.NoDetection
            else -> InferenceResult.Distraction(
                label = CLASS_LABELS[topClass] ?: "Unknown",
                confidence = topConf
            )
        }
    }

    private fun preprocessBitmap(bitmap: Bitmap): ByteBuffer {
        val scaled = Bitmap.createScaledBitmap(bitmap, INPUT_SIZE, INPUT_SIZE, true)
        val buf = ByteBuffer.allocateDirect(INPUT_SIZE * INPUT_SIZE * 3 * 4).apply {
            order(ByteOrder.nativeOrder())
        }

        val pixels = IntArray(INPUT_SIZE * INPUT_SIZE)
        scaled.getPixels(pixels, 0, INPUT_SIZE, 0, 0, INPUT_SIZE, INPUT_SIZE)
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
        Log.i(TAG, "DistractionInferenceEngine closed")
    }
}
