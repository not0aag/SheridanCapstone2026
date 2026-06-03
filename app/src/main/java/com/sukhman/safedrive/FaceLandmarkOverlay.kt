package com.sukhman.safedrive

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap

@Composable
fun FaceLandmarkOverlay(modifier: Modifier = Modifier) {
    Canvas(modifier = modifier.fillMaxSize()) {
        val landmarks = DebugState.faceLandmarks
        if (landmarks.isNotEmpty()) {
            // Landmarks are normalized [0,1] — scale to canvas pixel space.
            landmarks.forEach { lm ->
                drawCircle(
                    color = Color(0xFF00FF41),
                    radius = 5f,
                    center = Offset(lm[0] * size.width, lm[1] * size.height)
                )
            }
            drawFaceMeshConnections(landmarks, size.width, size.height)
        }
    }
}

private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawFaceMeshConnections(
    landmarks: List<FloatArray>,
    w: Float,
    h: Float
) {
    if (landmarks.size < 68) return

    val lineColor = Color(0xFF00FF41)
    val strokeWidth = 2.5f

    fun offset(i: Int) = Offset(landmarks[i][0] * w, landmarks[i][1] * h)

    fun seg(from: Int, to: Int) {
        if (landmarks.size > maxOf(from, to)) {
            drawLine(lineColor, offset(from), offset(to), strokeWidth, StrokeCap.Round)
        }
    }

    // Face contour
    for (i in 0 until 16) seg(i, i + 1)
    // Left eyebrow
    for (i in 17 until 21) seg(i, i + 1)
    // Right eyebrow
    for (i in 22 until 26) seg(i, i + 1)
    // Nose bridge
    for (i in 27 until 30) seg(i, i + 1)
    // Left eye (closed loop)
    for (i in 36 until 41) seg(i, i + 1); seg(41, 36)
    // Right eye (closed loop)
    for (i in 42 until 47) seg(i, i + 1); seg(47, 42)
    // Mouth outer (closed loop)
    for (i in 48 until 59) seg(i, i + 1); seg(59, 48)
}
