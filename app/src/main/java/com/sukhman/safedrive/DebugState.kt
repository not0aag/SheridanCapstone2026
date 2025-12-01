// ...existing code...
package com.sukhman.safedrive

import kotlin.jvm.Volatile

/**
 * Shared debug state updated by analyzers and sensors so the UI can display current stats
 */
object DebugState {
    @Volatile
    var fps: Double = 0.0

    @Volatile
    var accelX: Float = 0f
    @Volatile
    var accelY: Float = 0f
    @Volatile
    var accelZ: Float = 0f

    @Volatile
    var gyroX: Float = 0f
    @Volatile
    var gyroY: Float = 0f
    @Volatile
    var gyroZ: Float = 0f
}

