package com.sukhman.safedrive

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.sukhman.safedrive.ml.AppSettingsStore
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
    settingsStore: AppSettingsStore,
    tripStatsStore: TripStatsStore,
    navController: NavHostController = rememberNavController()
) {
    NavHost(navController = navController, startDestination = Screen.Home.route) {

        composable(Screen.Home.route) {
            HomeScreen(
                onStartTrip          = {
                    tripStatsStore.recordTripStarted()
                    navController.navigate(Screen.TripActive.route)
                },
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) },
                onCalibrate          = { navController.navigate(Screen.Calibration.route) },
                tripDetector         = tripDetector,
                tripStatsStore       = tripStatsStore,
                alertManager         = alertManager,
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
                alertManager    = alertManager,
                decisionEngine  = inferenceEngine.decisionEngine,
                tripDetector    = tripDetector,
                settingsStore   = settingsStore,
                onNavigateBack  = { navController.popBackStack() }
            )
        }
    }
}
