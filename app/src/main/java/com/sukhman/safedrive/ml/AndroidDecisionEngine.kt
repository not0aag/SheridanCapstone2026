package com.sukhman.safedrive.ml

class AndroidDecisionEngine {

    companion object {
        private const val DISTRACTION_WINDOW = 25      // frames
        private const val DROWSY_WINDOW_MS   = 4_000L
    }

    // User-tunable via Settings sliders. @Volatile so the inference coroutine
    // always reads the latest value written from the main/Compose thread.
    @Volatile var perclosThreshold:  Double = 30.0   // % of window eyes closed
    @Volatile var distRateThreshold: Double = 0.40   // fraction of last 25 frames classifier non-safe
    @Volatile var headRateThreshold: Double = 0.60   // fraction of last 25 frames head deviated

    data class Frame(
        val timestampMs:  Long,
        val eyesClosed:   Boolean,
        val headDeviated: Boolean,
        val isDistracted: Boolean
    )

    data class Decision(
        val alert:          Boolean,
        val alertType:      String,
        val perclosPct:     Float,
        val headAlertRate:  Float,
        val distractionRate: Float
    )

    private val frames = ArrayDeque<Frame>()
    private var firstFrameMs = -1L

    fun addFrame(eyesClosed: Boolean, headDeviated: Boolean, isDistracted: Boolean) {
        val now = System.currentTimeMillis()
        if (firstFrameMs < 0) firstFrameMs = now
        frames.addLast(Frame(now, eyesClosed, headDeviated, isDistracted))
        prune(now)
    }

    fun getDecision(): Decision {
        if (frames.isEmpty()) return Decision(false, "", 0f, 0f, 0f)

        val now = System.currentTimeMillis()
        val totalElapsedMs = if (firstFrameMs > 0) now - firstFrameMs else 0L

        // PERCLOS — all frames in the 4-second window
        val perclosPct = frames.count { it.eyesClosed } * 100f / frames.size

        // Distraction signals — last 25 frames only
        val recent = if (frames.size > DISTRACTION_WINDOW)
            frames.toList().takeLast(DISTRACTION_WINDOW) else frames.toList()

        val headAlertRate   = if (recent.isNotEmpty()) recent.count { it.headDeviated }.toFloat() / recent.size else 0f
        val distractionRate = if (recent.isNotEmpty()) recent.count { it.isDistracted }.toFloat() / recent.size else 0f

        // DROWSY — gated by minimum 4-second window
        val isDrowsy = totalElapsedMs >= DROWSY_WINDOW_MS && perclosPct > perclosThreshold

        // DISTRACTED — requires BOTH head deviation AND classifier to agree
        val isDistracted = headAlertRate > headRateThreshold && distractionRate > distRateThreshold

        return when {
            isDrowsy     -> Decision(true,  "DROWSY",     perclosPct, headAlertRate, distractionRate)
            isDistracted -> Decision(true,  "DISTRACTED", perclosPct, headAlertRate, distractionRate)
            else         -> Decision(false, "",            perclosPct, headAlertRate, distractionRate)
        }
    }

    fun reset() { frames.clear(); firstFrameMs = -1L }

    private fun prune(nowMs: Long) {
        val cutoff = nowMs - DROWSY_WINDOW_MS
        while (frames.isNotEmpty() && frames.first().timestampMs < cutoff) frames.removeFirst()
    }
}
