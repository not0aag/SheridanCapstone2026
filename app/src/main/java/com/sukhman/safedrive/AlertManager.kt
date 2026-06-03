package com.sukhman.safedrive

import android.content.Context
import android.media.MediaPlayer
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log
import androidx.annotation.RequiresApi

/**
 * Manages alerts for driver distraction and drowsiness detection
 *
 * Features:
 * - Audio alerts (TTS or beep sounds)
 * - Haptic feedback (vibration patterns)
 * - Alert throttling (prevent alert spam)
 * - Configurable alert types and thresholds
 */
class AlertManager(private val context: Context) {

    private val TAG = "AlertManager"

    private var vibrator: Vibrator? = null
    private var mediaPlayer: MediaPlayer? = null

    // Alert throttling
    private var lastDistractionAlertTime = 0L
    private var lastDrowsinessAlertTime = 0L
    private val alertThrottleMs = 3000L // Minimum 3 seconds between similar alerts

    @Volatile
    var alertsEnabled = true

    init {
        vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
            vibratorManager.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }
    }

    /**
     * Trigger distraction alert
     */
    fun triggerDistractionAlert(label: String = "distraction", confidence: Float = 1.0f) {
        if (!alertsEnabled) return

        val now = System.currentTimeMillis()
        if (now - lastDistractionAlertTime < alertThrottleMs) {
            Log.d(TAG, "Distraction alert throttled")
            return
        }

        lastDistractionAlertTime = now

        Log.w(TAG, "DISTRACTION ALERT: $label (confidence: $confidence)")

        // Update debug state for UI
        DebugState.lastAlertType = "DISTRACTION: $label"
        DebugState.lastAlertTime = now

        // Trigger vibration
        vibrate(VibrationType.DISTRACTION)

        // Trigger audio alert
        playAlert(AlertType.DISTRACTION)
    }

    /**
     * Trigger drowsiness alert
     */
    fun triggerDrowsinessAlert(perclos: Float = 0.0f) {
        if (!alertsEnabled) return

        val now = System.currentTimeMillis()
        if (now - lastDrowsinessAlertTime < alertThrottleMs) {
            Log.d(TAG, "Drowsiness alert throttled")
            return
        }

        lastDrowsinessAlertTime = now

        Log.w(TAG, "DROWSINESS ALERT: PERCLOS=$perclos")

        // Update debug state for UI
        DebugState.lastAlertType = "DROWSINESS (PERCLOS: $perclos)"
        DebugState.lastAlertTime = now

        // Trigger vibration
        vibrate(VibrationType.DROWSINESS)

        // Trigger audio alert
        playAlert(AlertType.DROWSINESS)
    }

    /**
     * Vibration patterns
     */
    private enum class VibrationType(val pattern: LongArray) {
        DISTRACTION(longArrayOf(0, 200, 100, 200)), // Short double buzz
        DROWSINESS(longArrayOf(0, 500, 200, 500, 200, 500)) // Long triple buzz
    }

    /**
     * Audio alert types
     */
    private enum class AlertType {
        DISTRACTION,
        DROWSINESS
    }

    /**
     * Trigger vibration with specific pattern
     */
    private fun vibrate(type: VibrationType) {
        try {
            vibrator?.let {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    val effect = VibrationEffect.createWaveform(type.pattern, -1)
                    it.vibrate(effect)
                } else {
                    @Suppress("DEPRECATION")
                    it.vibrate(type.pattern, -1)
                }
                Log.d(TAG, "Vibration triggered: ${type.name}")
            } ?: run {
                Log.w(TAG, "Vibrator not available")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to trigger vibration", e)
        }
    }

    /**
     * Play audio alert
     *
     * For production, you would:
     * - Add audio files to res/raw/ (e.g., distraction_alert.mp3, drowsiness_alert.mp3)
     * - Use MediaPlayer or TextToSpeech for voice alerts
     *
     * For now, we'll use system notification sounds as placeholders
     */
    private fun playAlert(type: AlertType) {
        try {
            // Release previous media player if exists
            mediaPlayer?.release()

            // For POC, use system default notification sound
            val soundUri = android.provider.Settings.System.DEFAULT_NOTIFICATION_URI

            mediaPlayer = MediaPlayer.create(context, soundUri)
            mediaPlayer?.setOnCompletionListener { mp ->
                mp.release()
            }
            mediaPlayer?.start()

            Log.d(TAG, "Audio alert played: ${type.name}")

        } catch (e: Exception) {
            Log.e(TAG, "Failed to play audio alert", e)
        }
    }

    /**
     * Clear all active alerts
     */
    fun clearAlerts() {
        DebugState.lastAlertType = ""
        DebugState.lastAlertTime = 0L
        Log.d(TAG, "Alerts cleared")
    }

    /**
     * Cleanup resources
     */
    fun destroy() {
        try {
            mediaPlayer?.release()
            mediaPlayer = null
            vibrator = null
            Log.i(TAG, "AlertManager destroyed")
        } catch (e: Exception) {
            Log.e(TAG, "Error destroying AlertManager", e)
        }
    }
}
