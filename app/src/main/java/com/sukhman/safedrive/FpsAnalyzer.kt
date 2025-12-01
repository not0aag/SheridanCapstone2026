// Explanation: Add an ImageAnalysis analyzer that computes approximate FPS over a 1-second sliding window
// and logs the measured FPS using android.util.Log. This will help verify actual frames processed (useful for camera POC).

package com.sukhman.safedrive

import android.util.Log
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy

class FpsAnalyzer : ImageAnalysis.Analyzer {
    private val frames = java.util.concurrent.atomic.AtomicInteger(0)
    private val windowStart = java.util.concurrent.atomic.AtomicLong(System.currentTimeMillis())

    override fun analyze(image: ImageProxy) {
        try {
            val now = System.currentTimeMillis()
            frames.incrementAndGet()
            val start = windowStart.get()
            val elapsed = now - start
            if (elapsed >= 1000L) {
                val count = frames.getAndSet(0)
                windowStart.set(now)
                val fps = count * 1000.0 / (if (elapsed == 0L) 1.0 else elapsed.toDouble())
                Log.i("FpsAnalyzer", String.format("Approx FPS: %.2f (frames=%d elapsed=%dms)", fps, count, elapsed))
                DebugState.fps = fps
            }
        } finally {
            image.close()
        }
    }
}
