# SafeDrive AI - ML Pipeline Integration Tests

## Overview
This directory contains end-to-end integration tests for the complete ML pipeline.

## Test: Full Pipeline (Camera → MediaPipe → Distraction Detection)

**File:** `test_full_pipeline.py`

**What it tests:**
1. MediaPipe FaceMesh face detection
2. TFLite distraction model inference
3. Full pipeline performance (FPS, latency)
4. Real-time visualization

### Prerequisites

```bash
# Activate your virtual environment
source ~/safedrive_ml_env/bin/activate

# Ensure you have all dependencies
pip install tensorflow mediapipe opencv-python numpy scipy
```

### How to Run

```bash
cd ml-models/integration_tests
python test_full_pipeline.py
```

### What You'll See

- **Video window** showing:
  - Current FPS
  - Face detection status
  - Detected distraction class
  - Confidence score
  - Alert if distraction detected (>70% confidence)

### Controls

- **Press 's'**: Show performance statistics in terminal
- **Press 'q'**: Quit and see final report

### Expected Performance (Your MacBook M4 Pro)

- **FPS**: 40-60 FPS (should easily exceed 25 FPS target)
- **Inference Time**: 15-25 ms (should be <40 ms target)
- **Face Detection**: Real-time with 468 landmarks
- **Classification**: Accurate distraction detection

### Performance Targets

| Metric | Minimum | Target | Your M4 Expected |
|--------|---------|--------|------------------|
| FPS | 25 | 30+ | 40-60 |
| Inference Latency | <50ms | <40ms | 15-25ms |
| Face Detection | Works | Stable | Excellent |

### Troubleshooting

**"Could not open webcam"**
- Check webcam permissions
- Try different camera index (change `cv2.VideoCapture(0)` to `(1)`)

**Low FPS (<25)**
- Check CPU usage
- Close other applications
- Verify Metal acceleration is working

**Model not found**
- Verify path: `../week2_training/tflite_models/mobilenetv2_distraction_classifier.tflite`
- Run from `ml-models/integration_tests/` directory

### Next Steps After Testing

1. ✅ If performance is good on your Mac → Ready for device testing
2. ⚠️ If FPS < 25 → Optimize model or preprocessing
3. ✅ If accuracy seems good → Ready to hand off to Sukh for Android integration

### Android Device Testing (Next)

After this test passes, coordinate with Sukh to:
1. Test on his OnePlus 11R 5G
2. Measure real mobile performance
3. Validate Android TFLite integration
