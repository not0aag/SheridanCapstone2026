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
    tripDetector: com.sukhman.safedrive.service.TripDetector
) {
    var tripStats by remember { mutableStateOf(TripStats()) }

    // Monitor trip state
    LaunchedEffect(Unit) {
        tripDetector.setListener(object : com.sukhman.safedrive.service.TripDetector.Listener {
            override fun onTripStarted() {
                tripStats = tripStats.copy(isActive = true, totalTrips = tripStats.totalTrips + 1)
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
                        StatItem(label = "Active Alerts", value = tripStats.totalAlerts.toString())
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

            // Info text
            Text(
                text = "Tap to start real-time driver monitoring with AI-powered distraction and drowsiness detection.",
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
