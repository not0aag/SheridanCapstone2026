package com.sukhman.safedrive

import android.Manifest
import android.content.pm.PackageManager
import android.hardware.camera2.CaptureRequest
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
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.sukhman.safedrive.ml.AndroidCalibrationEngine
import com.sukhman.safedrive.ml.CombinedDetectionEngine
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import java.util.concurrent.Executors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CalibrationScreen(
    inferenceEngine: CombinedDetectionEngine,
    onCalibrationComplete: () -> Unit,
    onCancel: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    var hasCamera by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA)
                    == PackageManager.PERMISSION_GRANTED
        )
    }
    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> hasCamera = granted }

    val analysisExecutor = remember { Executors.newSingleThreadExecutor() }
    val inferenceScope = remember { CoroutineScope(Dispatchers.Default) }
    val frameAnalyzer = remember { FrameAnalyzer(inferenceEngine, null, inferenceScope) }

    val progress = DebugState.calibrationProgress
    val isComplete = DebugState.isCalibrated && progress >= 1f
    val earValue = DebugState.earValue

    // Kick off calibration once
    var started by remember { mutableStateOf(false) }
    LaunchedEffect(hasCamera) {
        if (hasCamera && !started) {
            started = true
            inferenceEngine.calibrationEngine.startCalibration()
            DebugState.calibrationProgress = 0f
        } else if (!hasCamera) {
            launcher.launch(Manifest.permission.CAMERA)
        }
    }

    // Drive the progress bar from the calibration engine's elapsed time every 100ms
    LaunchedEffect(started) {
        if (!started) return@LaunchedEffect
        while (inferenceEngine.calibrationEngine.isCalibrating) {
            DebugState.calibrationProgress = inferenceEngine.calibrationEngine.progress
            kotlinx.coroutines.delay(100)
        }
    }

    // Navigate away as soon as calibration is marked complete
    LaunchedEffect(isComplete) {
        if (isComplete) {
            kotlinx.coroutines.delay(800)
            onCalibrationComplete()
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            frameAnalyzer.cancel()
            analysisExecutor.shutdown()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Calibration") },
                navigationIcon = {
                    IconButton(onClick = onCancel) {
                        Icon(Icons.Default.Close, contentDescription = "Cancel")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            if (hasCamera) {
                // Camera preview
                AndroidView(
                    factory = { ctx ->
                        val previewView = PreviewView(ctx).apply {
                            layoutParams = android.view.ViewGroup.LayoutParams(
                                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                                android.view.ViewGroup.LayoutParams.MATCH_PARENT
                            )
                            scaleType = PreviewView.ScaleType.FILL_CENTER
                        }

                        val future = ProcessCameraProvider.getInstance(ctx)
                        future.addListener({
                            val provider = future.get()

                            val resSel = ResolutionSelector.Builder()
                                .setAspectRatioStrategy(AspectRatioStrategy.RATIO_16_9_FALLBACK_AUTO_STRATEGY)
                                .setResolutionStrategy(
                                    ResolutionStrategy(Size(1280, 720),
                                        ResolutionStrategy.FALLBACK_RULE_CLOSEST_HIGHER_THEN_LOWER)
                                ).build()

                            val previewBuilder = Preview.Builder().setResolutionSelector(resSel)
                            Camera2Interop.Extender(previewBuilder)
                                .setCaptureRequestOption(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, Range.create(15, 30))
                            val preview = previewBuilder.build().also {
                                it.setSurfaceProvider(previewView.surfaceProvider)
                            }

                            val analyzer = ImageAnalysis.Builder()
                                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                                .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_YUV_420_888)
                                .setResolutionSelector(resSel)
                                .build()
                                .also { it.setAnalyzer(analysisExecutor, frameAnalyzer) }

                            val selector = CameraSelector.Builder()
                                .requireLensFacing(CameraSelector.LENS_FACING_FRONT).build()

                            try {
                                provider.unbindAll()
                                provider.bindToLifecycle(lifecycleOwner, selector, preview, analyzer)
                            } catch (e: Exception) {
                                android.util.Log.e("CalibrationScreen", "Camera bind failed", e)
                            }
                        }, ContextCompat.getMainExecutor(ctx))

                        previewView
                    },
                    modifier = Modifier.fillMaxSize()
                )

                // Face landmark overlay
                FaceLandmarkOverlay()

                // Instruction overlay at the top
                Column(
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .padding(16.dp)
                        .background(Color.Black.copy(alpha = 0.6f), shape = RoundedCornerShape(12.dp))
                        .padding(horizontal = 20.dp, vertical = 12.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = if (isComplete) "Calibration Complete!" else "Look straight ahead",
                        color = if (isComplete) Color(0xFF00CC66) else Color.White,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                    if (!isComplete) {
                        Text(
                            text = "Keep your eyes open naturally",
                            color = Color.White.copy(alpha = 0.8f),
                            fontSize = 13.sp
                        )
                    }
                }

                // Progress card at the bottom
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .align(Alignment.BottomCenter)
                        .padding(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.Black.copy(alpha = 0.75f))
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        val seconds = (AndroidCalibrationEngine.DURATION_SECONDS * (1f - progress)).toInt()
                        Text(
                            text = if (isComplete) "Done! Returning..." else "${seconds}s remaining",
                            color = Color.White,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        LinearProgressIndicator(
                            progress = { progress },
                            modifier = Modifier.fillMaxWidth().height(10.dp),
                            color = if (isComplete) Color(0xFF00CC66) else MaterialTheme.colorScheme.primary,
                            trackColor = Color.White.copy(alpha = 0.2f)
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceEvenly
                        ) {
                            CalibStatusItem(
                                label = "EAR",
                                value = "%.3f".format(earValue),
                                highlight = earValue > 0.15f
                            )
                            CalibStatusItem(
                                label = "Face",
                                value = if (DebugState.faceLandmarks.isNotEmpty()) "Detected" else "Not found",
                                highlight = DebugState.faceLandmarks.isNotEmpty()
                            )
                        }
                    }
                }
            } else {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("Camera permission required", fontSize = 16.sp)
                        Spacer(modifier = Modifier.height(12.dp))
                        Button(onClick = { launcher.launch(Manifest.permission.CAMERA) }) {
                            Text("Grant Permission")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun CalibStatusItem(label: String, value: String, highlight: Boolean) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            color = if (highlight) Color(0xFF66FF99) else Color(0xFFFF6666),
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold
        )
        Text(text = label, color = Color.White.copy(alpha = 0.7f), fontSize = 12.sp)
    }
}
