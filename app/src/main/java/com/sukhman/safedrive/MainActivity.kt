package com.sukhman.safedrive

import android.Manifest
import android.content.pm.PackageManager
import android.hardware.camera2.CaptureRequest
import android.os.Bundle
import android.util.Log
import android.util.Range
import android.util.Size
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.camera.camera2.interop.Camera2Interop
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.sukhman.safedrive.ui.theme.SafeDriveTheme

class MainActivity : ComponentActivity() {
    private lateinit var sensorsManager: SensorsManager
    private lateinit var locationHelper: LocationHelper

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        Log.d("MainActivity", "onCreate: starting")

        sensorsManager = SensorsManager(this)
        val fusedClient = com.google.android.gms.location.LocationServices.getFusedLocationProviderClient(this)
        locationHelper = LocationHelper(this, fusedClient)

        setContent {
            SafeDriveTheme {
                Scaffold { innerPadding ->
                    Box(modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding)) {
                        CameraScreen(
                            onStartSensors = { sensorsManager.start() },
                            onStopSensors = { sensorsManager.stop() },
                            onRequestLocation = {
                                // MainActivity handles the actual location callback and logging
                                locationHelper.requestCurrentLocation { loc ->
                                    if (loc != null) Log.i("MainActivity", "Location: ${loc.latitude}, ${loc.longitude}")
                                    else Log.w("MainActivity", "Location was null")
                                }
                            }
                        )

                        // Overlay debug info in top-left
                        DebugOverlay()
                    }
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        sensorsManager.stop()
        locationHelper.stop()
    }
}

@Composable
fun CameraScreen(
    onStartSensors: () -> Unit,
    onStopSensors: () -> Unit,
    onRequestLocation: () -> Unit
) {
    val context = LocalContext.current
    val requiredPermissions = listOf(
        Manifest.permission.CAMERA,
        Manifest.permission.RECORD_AUDIO,
        Manifest.permission.ACCESS_FINE_LOCATION
    )
    var hasPermissions by remember {
        mutableStateOf(requiredPermissions.all { perm ->
            ContextCompat.checkSelfPermission(context, perm) == PackageManager.PERMISSION_GRANTED
        })
    }

    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { perms ->
        hasPermissions = requiredPermissions.all { perms[it] == true }
    }

    LaunchedEffect(Unit) {
        if (!hasPermissions) {
            launcher.launch(requiredPermissions.toTypedArray())
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        if (hasPermissions) {
            // Camera preview goes here
            AndroidView(factory = { ctx ->
                // create the PreviewView used by CameraX
                val previewView = PreviewView(ctx)

                // set layout params (match parent)
                previewView.layoutParams = android.view.ViewGroup.LayoutParams(
                    android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                    android.view.ViewGroup.LayoutParams.MATCH_PARENT
                )

                // Start CameraX using the created PreviewView
                val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                cameraProviderFuture.addListener({
                    val cameraProvider = cameraProviderFuture.get()
                    val previewBuilder = Preview.Builder()
                        .setTargetResolution(Size(1920, 1080)) // request 1080p

                    // Request 30 FPS via Camera2 interop
                    val extender = Camera2Interop.Extender(previewBuilder)
                    extender.setCaptureRequestOption(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, Range.create(30, 30))

                    val preview = previewBuilder.build()
                    preview.setSurfaceProvider(previewView.surfaceProvider)

                    val cameraSelector = CameraSelector.Builder()
                        .requireLensFacing(CameraSelector.LENS_FACING_FRONT)
                        .build()

                    try {
                        cameraProvider.unbindAll()

                        // Build an ImageAnalysis use-case to measure FPS (non-blocking analyzer)
                        val analyzer = ImageAnalysis.Builder()
                            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                            .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_YUV_420_888)
                            .setTargetResolution(Size(1920, 1080))
                            .build()
                        analyzer.setAnalyzer(ContextCompat.getMainExecutor(ctx), FpsAnalyzer())

                        cameraProvider.bindToLifecycle(ctx as androidx.lifecycle.LifecycleOwner, cameraSelector, preview, analyzer)
                        Log.i("Camera", "Camera bound (front, 1080p target, 30fps request)")
                    } catch (e: Exception) {
                        Log.e("Camera", "Failed to bind camera use cases", e)
                    }
                }, ContextCompat.getMainExecutor(ctx))

                previewView
            }, modifier = Modifier
                .fillMaxWidth()
                .weight(1f))

            // Controls
            Row(modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Button(onClick = { onStartSensors() }, modifier = Modifier.weight(1f)) {
                    Text("Start Sensors")
                }
                Button(onClick = { onStopSensors() }, modifier = Modifier.weight(1f)) {
                    Text("Stop Sensors")
                }
                Button(onClick = {
                    onRequestLocation()
                }, modifier = Modifier.weight(1f)) {
                    Text("Get Location")
                }
            }
        } else {
            // Permission explanation UI
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Waiting for permissions...\nPlease allow Camera and Location to continue.")
            }
        }
    }
}
