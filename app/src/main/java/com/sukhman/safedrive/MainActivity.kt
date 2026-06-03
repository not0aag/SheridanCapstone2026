package com.sukhman.safedrive

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.lifecycleScope
import com.sukhman.safedrive.ml.DistractionInferenceEngine
import com.sukhman.safedrive.ml.FaceMeshInferenceEngine
import com.sukhman.safedrive.ml.InferenceEngine
import com.sukhman.safedrive.ml.MockInferenceEngine
import com.sukhman.safedrive.service.TripDetector
import com.sukhman.safedrive.ui.theme.SafeDriveTheme
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private lateinit var sensorsManager: SensorsManager
    private lateinit var locationHelper: LocationHelper
    private lateinit var alertManager: AlertManager
    private val tripDetector = TripDetector()
    private lateinit var inferenceEngine: InferenceEngine

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        sensorsManager = SensorsManager(this)
        locationHelper = LocationHelper(
            this,
            com.google.android.gms.location.LocationServices.getFusedLocationProviderClient(this)
        )
        alertManager = AlertManager(this)

        // Model priority: distraction classifier (team's real model) → face mesh → mock
        inferenceEngine = when {
            modelAssetExists("models/distraction_classifier.tflite") -> {
                Log.i("MainActivity", "distraction_classifier.tflite found — using DistractionInferenceEngine")
                DistractionInferenceEngine(this)
            }
            modelAssetExists("models/face_landmarker.tflite") -> {
                Log.i("MainActivity", "face_landmarker.tflite found — using FaceMeshInferenceEngine")
                FaceMeshInferenceEngine(this)
            }
            else -> {
                Log.i("MainActivity", "No model found — using MockInferenceEngine")
                MockInferenceEngine()
            }
        }

        lifecycleScope.launch {
            try {
                inferenceEngine.initialize()
                Log.i("MainActivity", "Inference engine ready")
            } catch (e: Exception) {
                Log.e("MainActivity", "Inference engine init failed, disabling ML", e)
            }
        }

        setContent {
            SafeDriveTheme {
                SafeDriveNavigation(
                    inferenceEngine = inferenceEngine,
                    alertManager = alertManager,
                    sensorsManager = sensorsManager,
                    locationHelper = locationHelper,
                    tripDetector = tripDetector
                )
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        sensorsManager.stop()
        locationHelper.stop()
        tripDetector.destroy()
        inferenceEngine.close()
        alertManager.destroy()
    }

    private fun modelAssetExists(path: String): Boolean = try {
        assets.open(path).close()
        true
    } catch (_: Exception) {
        false
    }
}
