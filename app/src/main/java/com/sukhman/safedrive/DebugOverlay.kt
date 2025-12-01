package com.sukhman.safedrive

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun DebugOverlay() {
    var fps by remember { mutableStateOf(0.0) }
    var ax by remember { mutableStateOf(0f) }
    var ay by remember { mutableStateOf(0f) }
    var az by remember { mutableStateOf(0f) }
    var gx by remember { mutableStateOf(0f) }
    var gy by remember { mutableStateOf(0f) }
    var gz by remember { mutableStateOf(0f) }

    LaunchedEffect(Unit) {
        while (true) {
            fps = DebugState.fps
            ax = DebugState.accelX
            ay = DebugState.accelY
            az = DebugState.accelZ
            gx = DebugState.gyroX
            gy = DebugState.gyroY
            gz = DebugState.gyroZ
            kotlinx.coroutines.delay(500)
        }
    }

    Column(modifier = Modifier
        .background(Color(0x88000000))
        .padding(8.dp)) {
        Text(text = "FPS: ${"%.2f".format(fps)}", color = Color.White)
        Text(text = "Accel: ax=${"%.2f".format(ax)} ay=${"%.2f".format(ay)} az=${"%.2f".format(az)}", color = Color.White)
        Text(text = "Gyro: gx=${"%.2f".format(gx)} gy=${"%.2f".format(gy)} gz=${"%.2f".format(gz)}", color = Color.White)
    }
}
