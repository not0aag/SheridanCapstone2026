package com.sukhman.safedrive

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.lifecycleScope
import com.sukhman.safedrive.ml.AndroidCalibrationEngine
import com.sukhman.safedrive.ml.CombinedDetectionEngine
import com.sukhman.safedrive.service.TripDetector
import com.sukhman.safedrive.ui.theme.SafeDriveTheme
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private lateinit var sensorsManager: SensorsManager
    private lateinit var locationHelper: LocationHelper
    private lateinit var alertManager: AlertManager
    private val tripDetector = TripDetector()
    private lateinit var inferenceEngine: CombinedDetectionEngine

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        sensorsManager = SensorsManager(this)
        locationHelper = LocationHelper(
            this,
            com.google.android.gms.location.LocationServices.getFusedLocationProviderClient(this)
        )
        alertManager = AlertManager(this)

        val calibrationEngine = AndroidCalibrationEngine(this)

        // Sync calibration state to DebugState so the UI reflects SharedPreferences on cold start
        DebugState.isCalibrated = calibrationEngine.isCalibrated

        inferenceEngine = CombinedDetectionEngine(this, calibrationEngine)

        lifecycleScope.launch {
            try {
                inferenceEngine.initialize()
                Log.i("MainActivity", "Inference engine ready")
            } catch (e: Exception) {
                Log.e("MainActivity", "Inference engine init failed", e)
            }
        }

        setContent {
            SafeDriveTheme {
                SafeDriveNavigation(
                    inferenceEngine = inferenceEngine,
                    alertManager    = alertManager,
                    sensorsManager  = sensorsManager,
                    locationHelper  = locationHelper,
                    tripDetector    = tripDetector
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
}
