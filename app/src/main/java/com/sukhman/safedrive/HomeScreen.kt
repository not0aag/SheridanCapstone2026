package com.sukhman.safedrive

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Home screen - Main entry point for the SafeDrive app
 * Shows trip status and allows starting a new trip
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onStartTrip: () -> Unit,
    onNavigateToSettings: () -> Unit,
    onCalibrate: () -> Unit,
    tripDetector: com.sukhman.safedrive.service.TripDetector,
    tripStatsStore: TripStatsStore,
    alertManager: AlertManager,
    isCalibrated: Boolean = false
) {
    // Seeded from persisted stores so counts survive navigation and app restarts.
    // Re-read on every entry to this screen (LaunchedEffect(Unit) re-runs each time
    // this composable re-enters composition, i.e. whenever the user navigates back here).
    var tripStats by remember {
        mutableStateOf(
            TripStats(
                totalTrips = tripStatsStore.totalTrips,
                totalAlerts = alertManager.totalAlerts,
                tripsToday = tripStatsStore.tripsToday
            )
        )
    }

    LaunchedEffect(Unit) {
        tripStats = tripStats.copy(
            totalTrips = tripStatsStore.totalTrips,
            totalAlerts = alertManager.totalAlerts,
            tripsToday = tripStatsStore.tripsToday
        )
        tripDetector.setListener(object : com.sukhman.safedrive.service.TripDetector.Listener {
            override fun onTripStarted() {
                tripStats = tripStats.copy(isActive = true)
            }

            override fun onTripStopped() {
                tripStats = tripStats.copy(isActive = false)
            }
        })
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("SafeDrive") },
                actions = {
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // App title and description
            Text(
                text = "SafeDrive",
                fontSize = 48.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "AI-Powered Driver Monitoring",
                fontSize = 18.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(48.dp))

            // Trip statistics
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                )
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Trip Statistics",
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSecondaryContainer
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        StatItem(label = "Total Trips", value = tripStats.totalTrips.toString())
                        StatItem(label = "Total Alerts", value = tripStats.totalAlerts.toString())
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        StatItem(label = "Status", value = if (tripStats.isActive) "Active" else "Idle")
                        StatItem(label = "Today", value = "${tripStats.tripsToday} trips")
                    }
                }
            }

            Spacer(modifier = Modifier.height(48.dp))

            // Calibration status chip
            val calibLabel = if (isCalibrated) "Calibrated ✓" else "Not calibrated"
            val calibColor = if (isCalibrated)
                MaterialTheme.colorScheme.tertiary else MaterialTheme.colorScheme.error
            Text(
                text = calibLabel,
                fontSize = 13.sp,
                color = calibColor,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Calibrate button
            OutlinedButton(
                onClick = onCalibrate,
                modifier = Modifier.fillMaxWidth().height(52.dp)
            ) {
                Text(
                    text = if (isCalibrated) "Re-Calibrate" else "Calibrate First (10 sec)",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Start trip button
            Button(
                onClick = onStartTrip,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(64.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Icon(
                    Icons.Default.PlayArrow,
                    contentDescription = null,
                    modifier = Modifier.size(32.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Start Monitoring", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = if (isCalibrated)
                    "Calibrated — ready for monitoring."
                else
                    "Calibrate first so the app learns your eye baseline, then start monitoring.",
                fontSize = 14.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(horizontal = 16.dp)
            )
        }
    }
}

@Composable
fun StatItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onSecondaryContainer
        )
        Text(
            text = label,
            fontSize = 14.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

/**
 * Data class to hold trip statistics
 */
data class TripStats(
    val totalTrips: Int = 0,
    val totalAlerts: Int = 0,
    val tripsToday: Int = 0,
    val isActive: Boolean = false
)
