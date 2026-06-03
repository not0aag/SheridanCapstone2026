package com.sukhman.safedrive

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.sukhman.safedrive.ml.InferenceEngine

/**
 * Navigation routes for the app
 */
sealed class Screen(val route: String) {
    object Home : Screen("home")
    object TripActive : Screen("trip_active")
    object Settings : Screen("settings")
}

/**
 * Main navigation host for the SafeDrive app
 */
@Composable
fun SafeDriveNavigation(
    inferenceEngine: InferenceEngine,
    alertManager: AlertManager,
    sensorsManager: SensorsManager,
    locationHelper: LocationHelper,
    tripDetector: com.sukhman.safedrive.service.TripDetector,
    navController: NavHostController = rememberNavController()
) {
    NavHost(
        navController = navController,
        startDestination = Screen.Home.route
    ) {
        composable(Screen.Home.route) {
            HomeScreen(
                onStartTrip = {
                    navController.navigate(Screen.TripActive.route)
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                },
                tripDetector = tripDetector
            )
        }

        composable(Screen.TripActive.route) {
            TripActiveScreen(
                inferenceEngine = inferenceEngine,
                alertManager = alertManager,
                sensorsManager = sensorsManager,
                locationHelper = locationHelper,
                tripDetector = tripDetector,
                onStopTrip = {
                    navController.popBackStack()
                }
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                alertManager = alertManager,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
