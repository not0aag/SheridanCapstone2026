package com.sukhman.safedrive

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Settings Screen - Configure alert preferences and app settings
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    alertManager: AlertManager,
    onNavigateBack: () -> Unit
) {
    var alertsEnabled by remember { mutableStateOf(alertManager.alertsEnabled) }
    var speedThreshold by remember { mutableStateOf(15) }
    var distractionSensitivity by remember { mutableStateOf(0.5f) }
    var drowsinessSensitivity by remember { mutableStateOf(0.5f) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
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
                .padding(16.dp)
                .verticalScroll(rememberScrollState())
        ) {
            // Alert Settings Section
            Text(
                text = "Alert Settings",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    // Enable/Disable alerts
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("Enable Alerts", fontWeight = FontWeight.Medium)
                            Text(
                                "Audio and vibration warnings",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        Switch(
                            checked = alertsEnabled,
                            onCheckedChange = {
                                alertsEnabled = it
                                alertManager.alertsEnabled = it
                            }
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                    HorizontalDivider()
                    Spacer(modifier = Modifier.height(16.dp))

                    // Distraction sensitivity
                    Text("Distraction Sensitivity", fontWeight = FontWeight.Medium)
                    Text(
                        "Lower = more alerts, Higher = fewer alerts",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Slider(
                        value = distractionSensitivity,
                        onValueChange = { distractionSensitivity = it },
                        valueRange = 0f..1f,
                        enabled = alertsEnabled,
                        modifier = Modifier.padding(vertical = 8.dp)
                    )
                    Text(
                        text = "Level: ${(distractionSensitivity * 100).toInt()}%",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Spacer(modifier = Modifier.height(16.dp))
                    HorizontalDivider()
                    Spacer(modifier = Modifier.height(16.dp))

                    // Drowsiness sensitivity
                    Text("Drowsiness Sensitivity", fontWeight = FontWeight.Medium)
                    Text(
                        "Lower = more alerts, Higher = fewer alerts",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Slider(
                        value = drowsinessSensitivity,
                        onValueChange = { drowsinessSensitivity = it },
                        valueRange = 0f..1f,
                        enabled = alertsEnabled,
                        modifier = Modifier.padding(vertical = 8.dp)
                    )
                    Text(
                        text = "Level: ${(drowsinessSensitivity * 100).toInt()}%",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Trip Detection Section
            Text(
                text = "Trip Detection",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Speed Threshold", fontWeight = FontWeight.Medium)
                    Text(
                        "Minimum speed to start trip detection",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("$speedThreshold km/h", fontSize = 24.sp, fontWeight = FontWeight.Bold)

                        Row {
                            Button(
                                onClick = { if (speedThreshold > 5) speedThreshold -= 5 },
                                modifier = Modifier.size(48.dp),
                                contentPadding = PaddingValues(0.dp)
                            ) {
                                Text("-", fontSize = 20.sp)
                            }
                            Spacer(modifier = Modifier.width(8.dp))
                            Button(
                                onClick = { if (speedThreshold < 50) speedThreshold += 5 },
                                modifier = Modifier.size(48.dp),
                                contentPadding = PaddingValues(0.dp)
                            ) {
                                Text("+", fontSize = 20.sp)
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // About Section
            Text(
                text = "About",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    InfoRow(label = "Version", value = "1.0.0 (Week 1-2 POC)")
                    Spacer(modifier = Modifier.height(8.dp))
                    InfoRow(label = "Build", value = "Debug")
                    Spacer(modifier = Modifier.height(8.dp))
                    InfoRow(label = "ML Engine", value = "MockInferenceEngine")
                    Spacer(modifier = Modifier.height(8.dp))
                    InfoRow(label = "Camera", value = "CameraX (1080p @ 30fps)")
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Reset button
            OutlinedButton(
                onClick = {
                    alertsEnabled = true
                    speedThreshold = 15
                    distractionSensitivity = 0.5f
                    drowsinessSensitivity = 0.5f
                    alertManager.alertsEnabled = true
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Reset to Defaults")
            }
        }
    }
}

@Composable
fun InfoRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, fontWeight = FontWeight.Medium)
    }
}
