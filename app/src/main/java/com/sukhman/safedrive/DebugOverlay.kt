package com.sukhman.safedrive

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun DebugOverlay() {
    // DebugState fields are mutableStateOf — Compose recomposes automatically on each change.
    Column(
        modifier = Modifier
            .background(Color(0x88000000))
            .padding(8.dp)
    ) {
        Text(text = "FPS: ${"%.2f".format(DebugState.fps)}", color = Color.White)
        Text(
            text = "Accel: ax=${"%.2f".format(DebugState.accelX)} ay=${"%.2f".format(DebugState.accelY)} az=${"%.2f".format(DebugState.accelZ)}",
            color = Color.White
        )
        Text(
            text = "Gyro: gx=${"%.2f".format(DebugState.gyroX)} gy=${"%.2f".format(DebugState.gyroY)} gz=${"%.2f".format(DebugState.gyroZ)}",
            color = Color.White
        )
    }
}
