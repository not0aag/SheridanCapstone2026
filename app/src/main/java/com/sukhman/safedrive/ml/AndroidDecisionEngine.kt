package com.sukhman.safedrive.ml

class AndroidDecisionEngine {

    companion object {
        private const val DISTRACTION_WINDOW   = 25    // frames
        private const val DROWSY_WINDOW_MS     = 4_000L
    }

    // Mutable + volatile: read on the background inference coroutine (via
    // FrameAnalyzer/Dispatchers.Default), written from Compose/main when the
    // user moves a Settings slider. Same pattern as AlertManager.alertsEnabled.
    @Volatile
    var perclosThreshold: Double = 30.0     // % of window eyes closed
    @Volatile
    var distRateThreshold: Double = 0.40    // fraction of last 25 frames distracted

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

        val isDrowsy = totalElapsedMs >= DROWSY_WINDOW_MS && perclosPct > perclosThreshold
        val isDistracted = distractionRate > distRateThreshold

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
