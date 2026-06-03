# SafeDrive AI — ML Module

Real-time driver distraction and drowsiness detection running on a smartphone front camera.

---

## Architecture

The pipeline has three stages that run in sequence once per frame.

```
Camera frame
    │
    ▼
MediaPipe FaceMesh  ── 468 facial landmarks (normalized x/y/z)
    │
    ├─▶  CalibrationEngine   (first 10 seconds only)
    │        Collects EAR + head rotation baseline
    │        Writes calibration.json
    │
    ├─▶  EAR calculation     (both eyes, averaged)
    ├─▶  Head deviation      (3-D rotation delta from calibrated baseline)
    └─▶  TFLite classifier   (MobileNetV2, 10 distraction classes)
              │
              ▼
         DecisionEngine      (rolling window — prevents per-frame noise)
              │
              ▼
         DetectionResult     (alert, alert_type, reason, live metrics)
```

### Source files

| File | Purpose |
|------|---------|
| `src/calibration.py` | `CalibrationEngine` — per-user EAR and head-pose baseline, saved to `calibration.json` |
| `src/decision_engine.py` | `DecisionEngine` — rolling-window alert logic, no camera or model required |
| `src/safe_drive_detector.py` | `SafeDriveDetector` — full pipeline wired together; `DetectionResult` dataclass |
| `src/demo_unified.py` | Live webcam demo with HUD overlay |

### Tests

| File | Covers |
|------|--------|
| `tests/test_calibration.py` | `CalibrationEngine` lifecycle, EAR computation, save/load |
| `tests/test_decision_engine.py` | All alert scenarios, boundary conditions, PERCLOS window |

No camera, no model, and no network connection required to run the tests.

---

## Detection logic

### DROWSY
- Fires when EAR < calibrated threshold in **> 30 %** of the past **4 seconds**
- Requires a full 4-second window before it can fire (prevents false alerts on startup)
- Calibrated threshold = `mean_open_ear × 0.75` — set per user during calibration

### DISTRACTED
- Fires when **both** signals agree over the last **25 frames**:
  - Head deviated from calibrated baseline in **> 60 %** of frames
  - TFLite classifier predicted a non-safe class in **> 40 %** of frames
- Requiring both signals prevents false alerts from brief mirror checks (head only) or model noise (classifier only)

DROWSY takes priority when both conditions are met simultaneously.

---

## Running the demo

```bash
# From the repo root, using the project virtualenv:
safedrive_ml/bin/python3.10 ml/src/demo_unified.py

# Force recalibration even if calibration.json already exists:
safedrive_ml/bin/python3.10 ml/src/demo_unified.py --recal

# Custom model or calibration file:
safedrive_ml/bin/python3.10 ml/src/demo_unified.py \
    --model ml-models/week3_finetuning/tflite_models/class_weights_model_91pct.tflite \
    --cal   calibration.json
```

During the demo:
- **R** — force recalibration mid-session
- **Q / ESC** — quit

---

## Running tests

```bash
safedrive_ml/bin/python3.10 -m pytest ml/tests/ -v
```

---

## Model

| Property | Value |
|----------|-------|
| File | `ml-models/week3_finetuning/tflite_models/class_weights_model_91pct.tflite` |
| Architecture | MobileNetV2 (fine-tuned from ImageNet) |
| Input shape | `[1, 224, 224, 3]` |
| Input dtype | `float32` |
| Normalization | `pixel = (pixel / 127.5) − 1.0` → range `[−1, 1]` |
| Color order | RGB (convert from BGR before normalizing) |
| Output | 10-class softmax, index = class |
| Validation accuracy | 91 % on State Farm held-out set |
| File size | 2.7 MB |

### Class mapping

| Index | Label | Description |
|-------|-------|-------------|
| 0 | Safe | Hands on wheel, eyes forward |
| 1 | Texting-R | Texting with right hand |
| 2 | Phone-R | Talking on phone, right hand |
| 3 | Texting-L | Texting with left hand |
| 4 | Phone-L | Talking on phone, left hand |
| 5 | Radio | Operating radio / AC controls |
| 6 | Drinking | Drinking |
| 7 | Reaching | Reaching behind seat |
| 8 | Makeup | Hair and makeup |
| 9 | Passenger | Talking to passenger |

---

## Dependencies

```
mediapipe==0.10.8    # FaceMesh — must pin this version; 0.10.9+ removed mp.solutions
opencv-python        # Frame capture and image preprocessing
tensorflow-macos     # TFLite inference on macOS (2.14.0)
numpy<2.0            # Required by tensorflow-macos 2.14 — NumPy 2.x breaks it
pytest               # Test runner
```

> `tflite-runtime` has no Python 3.10 wheel for macOS. Use `tensorflow-macos` instead.  
> On Android, use the `tflite-runtime` AAR via Gradle.

---

## Training history

| Folder | What was trained | Canonical output |
|--------|-----------------|-----------------|
| `ml-models/week2_training/` | Initial MobileNetV2 on State Farm, driver-based split | Baseline model |
| `ml-models/week3_finetuning/` | Fine-tuning experiments: class weights, multi-angle augmentation, extreme augmentation | `class_weights_model_91pct.tflite` |

The canonical model was produced by `week3_finetuning/train_with_class_weights.py`.

The `week2_training/` scripts establish the driver-based dataset split (splitting by subject ID, not by image) — this prevents data leakage since the State Farm dataset contains multiple images of the same driver.

---

## calibration.json

Generated at runtime, gitignored. Contains:

```json
{
  "baseline_nose": {"x": 0.52, "y": 0.48},
  "baseline_rotation_vector": [0.01, -0.03, 0.00],
  "mean_open_ear": 0.31,
  "ear_threshold": 0.23,
  "calibration_timestamp": "2026-01-15T10:30:00",
  "frames_used": 28
}
```

Delete this file and restart to recalibrate (or press **R** in the demo).
