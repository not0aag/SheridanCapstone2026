package com.sukhman.safedrive

import android.content.Context
import android.content.SharedPreferences
import android.media.AudioAttributes
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

    companion object {
        private const val PREFS_NAME = "safedrive_alert_stats"
        private const val KEY_TOTAL_ALERTS = "total_alerts"
    }

    private var vibrator: Vibrator? = null
    private var mediaPlayer: MediaPlayer? = null

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    // Alert throttling
    private var lastDistractionAlertTime = 0L
    private var lastDrowsinessAlertTime = 0L
    private val alertThrottleMs = 3000L // Minimum 3 seconds between similar alerts

    @Volatile
    var alertsEnabled = true

    // Persisted count of real (post-throttle) alerts fired this install, read by HomeScreen.
    var totalAlerts: Int = 0
        private set

    init {
        vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
            vibratorManager.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        }
        totalAlerts = prefs.getInt(KEY_TOTAL_ALERTS, 0)
    }

    private fun recordAlertFired() {
        totalAlerts += 1
        prefs.edit().putInt(KEY_TOTAL_ALERTS, totalAlerts).apply()
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
        recordAlertFired()

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
        recordAlertFired()

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
     * Play audio alert.
     *
     * Drowsiness uses the alarm stream (USAGE_ALARM) so it plays even if the device's
     * media volume is turned down — MediaPlayer.create() defaults to STREAM_MUSIC
     * regardless of which system sound URI is passed, which would make a "drowsiness
     * alarm" silent on a device with media volume muted.
     */
    private fun playAlert(type: AlertType) {
        try {
            // Release previous media player if exists
            mediaPlayer?.release()

            val soundUri = when (type) {
                AlertType.DROWSINESS -> android.provider.Settings.System.DEFAULT_ALARM_ALERT_URI
                AlertType.DISTRACTION -> android.provider.Settings.System.DEFAULT_NOTIFICATION_URI
            }
            val audioAttributes = when (type) {
                AlertType.DROWSINESS -> AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
                AlertType.DISTRACTION -> AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
            }

            mediaPlayer = MediaPlayer().apply {
                setAudioAttributes(audioAttributes)
                setDataSource(context, soundUri)
                setOnCompletionListener { mp -> mp.release() }
                prepare()
                start()
            }

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
