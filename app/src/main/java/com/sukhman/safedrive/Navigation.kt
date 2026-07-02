package com.sukhman.safedrive

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.sukhman.safedrive.ml.CombinedDetectionEngine

sealed class Screen(val route: String) {
    object Home        : Screen("home")
    object TripActive  : Screen("trip_active")
    object Settings    : Screen("settings")
    object Calibration : Screen("calibration")
}

@Composable
fun SafeDriveNavigation(
    inferenceEngine: CombinedDetectionEngine,
    alertManager: AlertManager,
    sensorsManager: SensorsManager,
    locationHelper: LocationHelper,
    tripDetector: com.sukhman.safedrive.service.TripDetector,
    navController: NavHostController = rememberNavController()
) {
    NavHost(navController = navController, startDestination = Screen.Home.route) {

        composable(Screen.Home.route) {
            HomeScreen(
                onStartTrip          = { navController.navigate(Screen.TripActive.route) },
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) },
                onCalibrate          = { navController.navigate(Screen.Calibration.route) },
                tripDetector         = tripDetector,
                isCalibrated         = DebugState.isCalibrated
            )
        }

        composable(Screen.Calibration.route) {
            CalibrationScreen(
                inferenceEngine       = inferenceEngine,
                onCalibrationComplete = {
                    DebugState.isCalibrated = true
                    navController.popBackStack()
                },
                onCancel = { navController.popBackStack() }
            )
        }

        composable(Screen.TripActive.route) {
            TripActiveScreen(
                inferenceEngine = inferenceEngine,
                alertManager    = alertManager,
                sensorsManager  = sensorsManager,
                locationHelper  = locationHelper,
                tripDetector    = tripDetector,
                onStopTrip      = { navController.popBackStack() }
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                alertManager   = alertManager,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
