package com.sukhman.safedrive

import android.Manifest
import android.content.pm.PackageManager
import android.hardware.camera2.CaptureRequest
import android.util.Log
import android.util.Range
import android.util.Size
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.camera2.interop.Camera2Interop
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.core.resolutionselector.AspectRatioStrategy
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.sukhman.safedrive.ml.InferenceEngine
import com.sukhman.safedrive.service.DrivingService
import java.util.concurrent.Executors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TripActiveScreen(
    inferenceEngine: InferenceEngine,
    alertManager: AlertManager,
    sensorsManager: SensorsManager,
    locationHelper: LocationHelper,
    tripDetector: com.sukhman.safedrive.service.TripDetector,
    onStopTrip: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

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

    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { perms ->
        hasPermissions = requiredPermissions.all { perms[it] == true }
    }

    var isSensorsActive by remember { mutableStateOf(false) }
    var currentSpeed by remember { mutableStateOf(0.0) }

    // Dedicated executor for CameraX frame delivery — keeps camera off the main thread.
    val analysisExecutor = remember { Executors.newSingleThreadExecutor() }

    // Coroutine scope for ML inference — tied to this screen's lifetime.
    // Cancelled in onDispose so no dangling inference jobs survive screen exit.
    val inferenceScope = remember { CoroutineScope(Dispatchers.Default) }

    // FrameAnalyzer wires camera → TFLite inference → DebugState. Created once.
    val frameAnalyzer = remember { FrameAnalyzer(inferenceEngine, alertManager, inferenceScope) }

    // Request permissions on first launch if not already granted.
    LaunchedEffect(Unit) {
        if (!hasPermissions) launcher.launch(requiredPermissions.toTypedArray())
    }

    // Start sensors + foreground service as soon as permissions become available.
    // Key on hasPermissions so this re-runs the moment the user grants them.
    LaunchedEffect(hasPermissions) {
        if (hasPermissions) {
            DrivingService.start(context)
            sensorsManager.start()
            locationHelper.startLocationUpdates(onLocation = { loc ->
                currentSpeed = loc.speed.toDouble() * 3.6 // m/s → km/h
                tripDetector.onSpeedUpdate(loc.speed.toDouble())
            })
            isSensorsActive = true
        }
    }

    // Auto-dismiss alert banner after 5 seconds.
    LaunchedEffect(DebugState.lastAlertTime) {
        if (DebugState.lastAlertTime > 0L) {
            delay(5000)
            DebugState.lastAlertType = ""
        }
    }

    // Cleanup on screen exit.
    DisposableEffect(Unit) {
        onDispose {
            frameAnalyzer.cancel()   // stop any in-flight inference
            analysisExecutor.shutdown()
            DrivingService.stop(context)
            sensorsManager.stop()
            locationHelper.stop()
            alertManager.clearAlerts()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Active Monitoring") },
                navigationIcon = {
                    IconButton(onClick = onStopTrip) {
                        Icon(Icons.Default.Close, contentDescription = "Stop Trip")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.errorContainer,
                    titleContentColor = MaterialTheme.colorScheme.onErrorContainer
                )
            )
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (hasPermissions) {
                // Camera preview — lifecycle owner captured from composable scope (not ctx cast)
                AndroidView(
                    factory = { ctx ->
                        val previewView = PreviewView(ctx).apply {
                            layoutParams = android.view.ViewGroup.LayoutParams(
                                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                                android.view.ViewGroup.LayoutParams.MATCH_PARENT
                            )
                            scaleType = PreviewView.ScaleType.FILL_CENTER
                            implementationMode = PreviewView.ImplementationMode.PERFORMANCE
                        }

                        val providerFuture = ProcessCameraProvider.getInstance(ctx)
                        providerFuture.addListener({
                            val provider = providerFuture.get()
                            val resolutionSelector = ResolutionSelector.Builder()
                                .setAspectRatioStrategy(AspectRatioStrategy.RATIO_16_9_FALLBACK_AUTO_STRATEGY)
                                .setResolutionStrategy(
                                    ResolutionStrategy(
                                        Size(1280, 720),
                                        ResolutionStrategy.FALLBACK_RULE_CLOSEST_HIGHER_THEN_LOWER
                                    )
                                )
                                .build()
                            val previewBuilder = Preview.Builder()
                                .setResolutionSelector(resolutionSelector)
                            Camera2Interop.Extender(previewBuilder)
                                .setCaptureRequestOption(
                                    CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE,
                                    Range.create(30, 30)
                                )
                            val preview = previewBuilder.build().also {
                                it.setSurfaceProvider(previewView.surfaceProvider)
                            }

                            val analyzer = ImageAnalysis.Builder()
                                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                                .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_YUV_420_888)
                                .setResolutionSelector(resolutionSelector)
                                .build()
                                .also {
                                    it.setAnalyzer(analysisExecutor, frameAnalyzer)
                                }

                            val selector = CameraSelector.Builder()
                                .requireLensFacing(CameraSelector.LENS_FACING_FRONT)
                                .build()

                            try {
                                provider.unbindAll()
                                provider.bindToLifecycle(lifecycleOwner, selector, preview, analyzer)
                                Log.i("TripActive", "Camera bound to lifecycle")
                            } catch (e: Exception) {
                                Log.e("TripActive", "Camera bind failed", e)
                            }
                        }, ContextCompat.getMainExecutor(ctx))

                        previewView
                    },
                    modifier = Modifier.fillMaxSize()
                )

                // Face landmark overlay (reacts to DebugState.faceLandmarks automatically)
                FaceLandmarkOverlay()

                // Face detection badge
                if (DebugState.faceLandmarks.isNotEmpty()) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(top = 16.dp, end = 16.dp)
                            .background(Color(0xCC00AA33), shape = MaterialTheme.shapes.small)
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text("● FACE DETECTED", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }

                // Drowsiness-unavailable notice — face mesh failed to load, so only
                // distraction detection is running this session. Surfaced instead of
                // silently disabling drowsiness alerts with no explanation.
                if (!DebugState.drowsinessAvailable) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.TopStart)
                            .padding(top = 16.dp, start = 16.dp)
                            .background(Color(0xCCE68A00), shape = MaterialTheme.shapes.small)
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text(
                            "⚠ Drowsiness detection unavailable — distraction-only mode",
                            color = Color.White,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                // Alert banner — shown whenever lastAlertType is non-empty
                if (DebugState.lastAlertType.isNotEmpty()) {
                    AlertBanner(
                        alertType = DebugState.lastAlertType,
                        modifier = Modifier.align(Alignment.TopCenter)
                    )
                }

                // Debug sensor overlay (top-left)
                DebugOverlay()

                // Bottom status bar
                TripStatusBar(
                    speed = currentSpeed,
                    fps = DebugState.fps,
                    sensorsActive = isSensorsActive
                )

            } else {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "Camera and Location permissions required",
                            textAlign = TextAlign.Center,
                            fontSize = 18.sp
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { launcher.launch(requiredPermissions.toTypedArray()) }) {
                            Text("Grant Permissions")
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun AlertBanner(alertType: String, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.error)
            .padding(16.dp)
    ) {
        Text(
            text = "ALERT: $alertType",
            color = MaterialTheme.colorScheme.onError,
            fontSize = 18.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.align(Alignment.Center)
        )
    }
}

@Composable
fun BoxScope.TripStatusBar(speed: Double, fps: Double, sensorsActive: Boolean) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .align(Alignment.BottomCenter)
            .padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Black.copy(alpha = 0.7f))
    ) {
        Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp)) {
            // Prediction banner
            val prediction = DebugState.currentPrediction
            val conf = DebugState.predictionConfidence
            val isSafe = prediction == "Safe driving" || prediction == "Face tracked" || prediction == "Initializing..."
            val bannerColor = if (isSafe) Color(0xFF00AA33) else Color(0xFFE53935)
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(bannerColor, shape = RoundedCornerShape(6.dp))
                    .padding(horizontal = 12.dp, vertical = 6.dp),
                contentAlignment = Alignment.Center
            ) {
                val label = if (!isSafe && conf > 0f)
                    "$prediction (${"%.0f".format(conf * 100)}%)"
                else prediction
                Text(label, color = Color.White, fontSize = 14.sp, fontWeight = FontWeight.Bold)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                StatusItem(label = "Speed", value = "${speed.toInt()} km/h")
                StatusItem(label = "FPS", value = String.format("%.1f", fps))
                StatusItem(label = "Sensors", value = if (sensorsActive) "ON" else "OFF")
            }
        }
    }
}

@Composable
fun StatusItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(text = value, color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Text(text = label, color = Color.White.copy(alpha = 0.7f), fontSize = 12.sp)
    }
}
