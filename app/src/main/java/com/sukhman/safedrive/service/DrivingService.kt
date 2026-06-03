package com.sukhman.safedrive.service

import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.IBinder

// Background service that signals an active monitoring session.
// Runs as a plain background service (not foreground) so it works on API 36 emulators
// where foreground-service promotion is blocked. The activity stays alive as long as the
// user keeps the screen on; the service is only needed to survive brief screen-off moments.
class DrivingService : Service() {

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    companion object {
        fun start(context: Context) {
            context.startService(Intent(context, DrivingService::class.java))
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, DrivingService::class.java))
        }
    }
}
