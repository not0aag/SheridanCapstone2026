package com.sukhman.safedrive.ml

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.facelandmarker.FaceLandmarker
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Face landmark engine backed by the MediaPipe Tasks FaceLandmarker.
 *
 * This runs the full MediaPipe pipeline — BlazeFace face detection, face-region
 * crop, then the landmark model — matching what the Python ml/ module gets from
 * mp.solutions.face_mesh. (The landmark model alone, fed a raw full frame,
 * cannot find a face: it is trained on detector-cropped face regions.)
 *
 * Model: models/face_landmarker.task
 * Download: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
 *
 * Emitted landmarks are normalised to [0, 1] relative to the input frame
 * (x, y, z), same convention as ml/src/calibration.py and the UI overlay.
 * The task model returns 478 points — the 468 FaceMesh points used by
 * EarCalculator/HeadPoseMath plus 10 iris points.
 */
class FaceMeshInferenceEngine(
    private val context: Context,
    private val modelPath: String = "models/face_landmarker.task"
) : InferenceEngine {

    private val TAG = "FaceMeshEngine"

    private var landmarker: FaceLandmarker? = null

    override suspend fun initialize() {
        withContext(Dispatchers.IO) {
            try {
                val options = FaceLandmarker.FaceLandmarkerOptions.builder()
                    .setBaseOptions(BaseOptions.builder().setModelAssetPath(modelPath).build())
                    .setRunningMode(RunningMode.IMAGE)
                    .setNumFaces(1)
                    .setMinFaceDetectionConfidence(0.5f)
                    .setMinFacePresenceConfidence(0.5f)
                    .build()
                landmarker = FaceLandmarker.createFromOptions(context, options)
                Log.i(TAG, "FaceLandmarker loaded from $modelPath")
            } catch (e: Throwable) {
                Log.e(TAG, "Failed to load model", e)
                throw RuntimeException("Cannot load face landmarker: ${e.message}", e)
            }
        }
    }

    override suspend fun runInference(frame: Bitmap): InferenceResult = withContext(Dispatchers.Default) {
        val lm = landmarker ?: return@withContext InferenceResult.NoDetection

        try {
            // MediaPipe requires ARGB_8888; CameraX JPEG decode already yields it,
            // but convert defensively in case the source config changes.
            val input = if (frame.config == Bitmap.Config.ARGB_8888) frame
                        else frame.copy(Bitmap.Config.ARGB_8888, false)

            val result = lm.detect(BitmapImageBuilder(input).build())
            val face = result.faceLandmarks().firstOrNull()
                ?: return@withContext InferenceResult.NoDetection

            val landmarks = face.map { floatArrayOf(it.x(), it.y(), it.z()) }

            Log.d(TAG, "Face detected, ${landmarks.size} landmarks")
            InferenceResult.FaceLandmarks(landmarks)

        } catch (e: Exception) {
            Log.e(TAG, "Inference failed", e)
            InferenceResult.NoDetection
        }
    }

    override fun close() {
        landmarker?.close()
        landmarker = null
        Log.i(TAG, "FaceLandmarker closed")
    }
}
