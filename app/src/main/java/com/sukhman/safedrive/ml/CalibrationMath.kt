package com.sukhman.safedrive.ml

object CalibrationMath {

    data class Result(val meanOpenEar: Float, val earThreshold: Float, val sampleCount: Int)

    /**
     * Trims the bottom 10% of EAR samples (typically blinks/transition frames) then
     * averages the rest to estimate the user's baseline "eyes open" EAR, and derives
     * a closed-eye threshold at 75% of that baseline. Returns null if there aren't
     * enough samples to produce a result.
     */
    fun compute(samples: List<Float>): Result? {
        if (samples.isEmpty()) return null

        val sorted = samples.sorted()
        val cutoff = (sorted.size * 0.10).toInt()
        val filtered = sorted.drop(cutoff)
        if (filtered.isEmpty()) return null

        val meanOpenEar = filtered.average().toFloat()
        val earThreshold = meanOpenEar * 0.75f
        return Result(meanOpenEar, earThreshold, filtered.size)
    }
}
