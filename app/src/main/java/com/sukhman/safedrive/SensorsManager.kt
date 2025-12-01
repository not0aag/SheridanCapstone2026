// Explanation: Replace Timber with Android Log and ensure constructor parameter usage
package com.sukhman.safedrive

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log

class SensorsManager(private val context: Context) : SensorEventListener {

    private val sensorManager: SensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val accelerometer: Sensor? = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    private val gyroscope: Sensor? = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)

    var onAccelerometer: ((Float, Float, Float) -> Unit)? = null
    var onGyroscope: ((Float, Float, Float) -> Unit)? = null

    fun start() {
        accelerometer?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
            Log.i("SensorsManager", "Accelerometer listener registered")
        } ?: Log.w("SensorsManager", "Accelerometer not available on this device")

        gyroscope?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
            Log.i("SensorsManager", "Gyroscope listener registered")
        } ?: Log.w("SensorsManager", "Gyroscope not available on this device")
    }

    fun stop() {
        sensorManager.unregisterListener(this)
        Log.i("SensorsManager", "Sensor listeners unregistered")
    }

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_ACCELEROMETER -> {
                val ax = event.values[0]
                val ay = event.values[1]
                val az = event.values[2]
                Log.d("SensorsManager", "Accelerometer: ax=$ax ay=$ay az=$az")
                onAccelerometer?.invoke(ax, ay, az)
                DebugState.accelX = ax
                DebugState.accelY = ay
                DebugState.accelZ = az
            }
            Sensor.TYPE_GYROSCOPE -> {
                val gx = event.values[0]
                val gy = event.values[1]
                val gz = event.values[2]
                Log.d("SensorsManager", "Gyroscope: gx=$gx gy=$gy gz=$gz")
                onGyroscope?.invoke(gx, gy, gz)
                DebugState.gyroX = gx
                DebugState.gyroY = gy
                DebugState.gyroZ = gz
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor, accuracy: Int) {
        Log.d("SensorsManager", "Sensor accuracy changed: ${sensor.name} -> $accuracy")
    }
}
