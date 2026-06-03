package com.sukhman.safedrive

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

object DebugState {
    var fps by mutableStateOf(0.0)

    var accelX by mutableStateOf(0f)
    var accelY by mutableStateOf(0f)
    var accelZ by mutableStateOf(0f)

    var gyroX by mutableStateOf(0f)
    var gyroY by mutableStateOf(0f)
    var gyroZ by mutableStateOf(0f)

    var faceLandmarks by mutableStateOf<List<FloatArray>>(emptyList())

    var lastAlertType by mutableStateOf("")
    var lastAlertTime by mutableStateOf(0L)

    // Current inference result label (e.g. "Safe driving", "Texting - right hand")
    var currentPrediction by mutableStateOf("Initializing...")
    var predictionConfidence by mutableStateOf(0f)
}
