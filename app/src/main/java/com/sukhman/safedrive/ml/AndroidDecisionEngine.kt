package com.sukhman.safedrive.ml

class AndroidDecisionEngine {

    companion object {
        private const val DISTRACTION_WINDOW   = 25    // frames
        private const val DROWSY_WINDOW_MS     = 4_000L
        private const val PERCLOS_THRESHOLD    = 30.0  // % of window eyes closed
        private const val DIST_RATE_THRESHOLD  = 0.40  // 40% of last 25 frames distracted
    }

    data class Frame(val timestampMs: Long, val eyesClosed: Boolean, val isDistracted: Boolean)

    data class Decision(
        val alert: Boolean,
        val alertType: String,   // "DROWSY", "DISTRACTED", or ""
        val perclosPct: Float,
        val distractionRate: Float
    )

    private val frames = ArrayDeque<Frame>()
    private var firstFrameMs = -1L

    fun addFrame(eyesClosed: Boolean, isDistracted: Boolean) {
        val now = System.currentTimeMillis()
        if (firstFrameMs < 0) firstFrameMs = now
        frames.addLast(Frame(now, eyesClosed, isDistracted))
        prune(now)
    }

    fun getDecision(): Decision {
        if (frames.isEmpty()) return Decision(false, "", 0f, 0f)

        val now = System.currentTimeMillis()
        val totalElapsedMs = if (firstFrameMs > 0) now - firstFrameMs else 0L

        // PERCLOS — all frames in the 4-second window
        val perclosPct = frames.count { it.eyesClosed } * 100f / frames.size

        // Distraction rate — last 25 frames only
        val recent = if (frames.size > DISTRACTION_WINDOW)
            frames.toList().takeLast(DISTRACTION_WINDOW) else frames.toList()
        val distractionRate = if (recent.isNotEmpty())
            recent.count { it.isDistracted }.toFloat() / recent.size else 0f

        val isDrowsy = totalElapsedMs >= DROWSY_WINDOW_MS && perclosPct > PERCLOS_THRESHOLD
        val isDistracted = distractionRate > DIST_RATE_THRESHOLD

        return when {
            isDrowsy    -> Decision(true, "DROWSY",      perclosPct, distractionRate)
            isDistracted -> Decision(true, "DISTRACTED", perclosPct, distractionRate)
            else         -> Decision(false, "",           perclosPct, distractionRate)
        }
    }

    fun reset() { frames.clear(); firstFrameMs = -1L }

    private fun prune(nowMs: Long) {
        val cutoff = nowMs - DROWSY_WINDOW_MS
        while (frames.isNotEmpty() && frames.first().timestampMs < cutoff) frames.removeFirst()
    }
}
