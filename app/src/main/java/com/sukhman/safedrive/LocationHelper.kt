// Explanation: LocationHelper wraps FusedLocationProviderClient to request the current location
// with a single callback. It gracefully handles permission checks and falls back to requesting
// a single high-accuracy update if last known location is null.

package com.sukhman.safedrive

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import androidx.core.app.ActivityCompat
import com.google.android.gms.location.*
import android.util.Log

class LocationHelper(
    private val context: Context,
    private val fusedLocationClient: FusedLocationProviderClient
) {
    private var locationCallback: LocationCallback? = null

    @SuppressLint("MissingPermission")
    fun requestCurrentLocation(onResult: (Location?) -> Unit) {
        if (ActivityCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            Log.w("LocationHelper", "Location permission not granted")
            onResult(null)
            return
        }

        fusedLocationClient.lastLocation.addOnSuccessListener { location: Location? ->
            if (location != null) {
                Log.i("LocationHelper", "Last location: ${location.latitude}, ${location.longitude}")
                onResult(location)
            } else {
                // request a single fresh location
                val req = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L)
                    .setMinUpdateDistanceMeters(1f)
                    .build()

                locationCallback = object : LocationCallback() {
                    override fun onLocationResult(result: LocationResult) {
                        val loc = result.lastLocation
                        if (loc != null) {
                            Log.i("LocationHelper", "New location: ${loc.latitude}, ${loc.longitude}")
                            onResult(loc)
                        } else {
                            Log.w("LocationHelper", "LocationResult returned null lastLocation")
                            onResult(null)
                        }
                        stop()
                    }
                }
                fusedLocationClient.requestLocationUpdates(req, locationCallback as LocationCallback, null)
            }
        }.addOnFailureListener {
            Log.w("LocationHelper", "Failed to get last location: ${it.message}")
            onResult(null)
        }
    }

    fun stop() {
        locationCallback?.let { fusedLocationClient.removeLocationUpdates(it) }
        locationCallback = null
    }
}
