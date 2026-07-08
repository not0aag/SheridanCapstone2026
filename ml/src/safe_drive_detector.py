"""
safe_drive_detector.py — SafeDriveDetector for SafeDrive AI

Wires together:
  - MediaPipe FaceMesh      (landmark detection, runs every frame)
  - CalibrationEngine       (per-user baseline, first 10 seconds)
  - TFLite classifier       (distraction class from raw frame)
  - DecisionEngine          (temporal alert logic)

The public API is intentionally minimal — one class, one method — so
Sukhman can replicate it in Kotlin with the same contract:

    detector = SafeDriveDetector(model_path="...")
    result   = detector.process_frame(frame_bgr)   # call every frame
    result.alert        → bool
    result.alert_type   → "DISTRACTED" | "DROWSY" | "NONE"
"""

import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from calibration import (
    CalibrationEngine,
    compute_ear,
    compute_head_rotation,
    LEFT_EYE,
    RIGHT_EYE,
)
from decision_engine import DecisionEngine

# TFLite — try lightweight runtime first, fall back to full TensorFlow
try:
    import tflite_runtime.interpreter as _tflite_mod
    _TFLiteInterpreter = _tflite_mod.Interpreter
except ImportError:
    try:
        from tensorflow import lite as _tflite_mod
        _TFLiteInterpreter = _tflite_mod.Interpreter
    except ImportError:
        _TFLiteInterpreter = None

CLASS_NAMES = [
    "Safe", "Texting-R", "Phone-R", "Texting-L", "Phone-L",
    "Radio", "Drinking", "Reaching", "Makeup", "Passenger",
]

# Rotation angle (radians) between current and baseline head pose that
# counts as "looking away". 0.44 rad ≈ 25 degrees.
# Normal driving involves mirror checks and road scanning (~10-15°) which
# should NOT trigger. Intentional phone use / passenger talk is 25-45°+.
# Tune this value in Step 6 using real driving footage.
HEAD_DEVIATION_THRESHOLD = 0.44


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DetectionResult:
    """Everything the demo or mobile app needs from one processed frame."""
    phase:                str    # "CALIBRATING" or "DETECTING"
    calibration_progress: float  # 0.0 → 1.0
    face_detected:        bool
    alert:                bool
    alert_type:           str    # "DISTRACTED" | "DROWSY" | "NONE"
    reason:               str
    head_deviated:        bool
    ear:                  float
    perclos_pct:          float
    classifier_class:     int
    classifier_class_name:str
    classifier_conf:      float
    fps:                  float


# ---------------------------------------------------------------------------
# SafeDriveDetector
# ---------------------------------------------------------------------------

class SafeDriveDetector:
    """
    Main inference class. Create once, call process_frame() every camera frame.

    Parameters
    ----------
    model_path : str
        Path to the TFLite model file.
    calibration_path : str
        Path where calibration.json is read from / written to.
        If the file already exists, calibration is skipped and detection
        begins immediately on the first frame.
    """

    def __init__(self, model_path: str, calibration_path: str = "calibration.json"):
        self._calibration_path = calibration_path
        self._phase            = "CALIBRATING"
        self._baseline_rvec    = None   # numpy (3,1) — set after calibration
        self._decision_engine  = None   # created after calibration
        self._cal_engine       = None

        # MediaPipe
        import mediapipe as mp
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # TFLite model
        self._interpreter     = self._load_tflite(model_path)
        self._input_idx       = None
        self._output_idx      = None
        if self._interpreter is not None:
            self._interpreter.allocate_tensors()
            self._input_idx  = self._interpreter.get_input_details()[0]["index"]
            self._output_idx = self._interpreter.get_output_details()[0]["index"]

        # Calibration — load existing file or start fresh
        cal_file = Path(calibration_path)
        if cal_file.exists():
            self._load_calibration()
        else:
            self._cal_engine = CalibrationEngine()
            print(f"[SafeDrive] No calibration found — starting 10-second calibration.")

        # FPS: rolling average of the last 30 frame timestamps
        self._frame_ts: deque = deque(maxlen=30)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_frame(self, frame_bgr: np.ndarray) -> DetectionResult:
        """
        Process one BGR camera frame (as returned by cv2.VideoCapture.read).
        Returns a DetectionResult populated with all current signals.
        """
        t_now = time.monotonic()
        h, w  = frame_bgr.shape[:2]

        rgb     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_out  = self._face_mesh.process(rgb)
        face_ok = mp_out.multi_face_landmarks is not None

        if not face_ok:
            return self._no_face_result(t_now)

        landmarks = mp_out.multi_face_landmarks[0].landmark

        if self._phase == "CALIBRATING":
            return self._run_calibration(landmarks, w, h, t_now)
        else:
            return self._run_detection(landmarks, frame_bgr, w, h, t_now)

    def close(self):
        """Release MediaPipe resources. Call when done."""
        self._face_mesh.close()

    # ------------------------------------------------------------------
    # Calibration phase
    # ------------------------------------------------------------------

    def _run_calibration(self, landmarks, w, h, t_now) -> DetectionResult:
        progress = self._cal_engine.add_frame(landmarks, w, h)

        if self._cal_engine.is_calibrated:
            self._cal_engine.save(self._calibration_path)
            self._load_calibration()
            print(f"[SafeDrive] Calibration saved -> {self._calibration_path}")

        return DetectionResult(
            phase="CALIBRATING",
            calibration_progress=progress,
            face_detected=True,
            alert=False,
            alert_type="NONE",
            reason="Calibrating — look straight ahead",
            head_deviated=False,
            ear=0.0,
            perclos_pct=0.0,
            classifier_class=0,
            classifier_class_name="Safe",
            classifier_conf=0.0,
            fps=self._fps(t_now),
        )

    def _load_calibration(self):
        """Read calibration.json and initialise detection components."""
        cal = CalibrationEngine.load(self._calibration_path)
        self._baseline_rvec   = np.array(
            cal["baseline_rotation_vector"], dtype=np.float64
        ).reshape(3, 1)
        self._decision_engine = DecisionEngine(ear_threshold=cal["ear_threshold"])
        self._cal_engine      = None
        self._phase           = "DETECTING"
        print(f"[SafeDrive] Calibration loaded — EAR threshold: {cal['ear_threshold']}")

    # ------------------------------------------------------------------
    # Detection phase
    # ------------------------------------------------------------------

    def _run_detection(self, landmarks, frame_bgr, w, h, t_now) -> DetectionResult:
        # EAR
        left_ear  = compute_ear(landmarks, LEFT_EYE)
        right_ear = compute_ear(landmarks, RIGHT_EYE)
        ear       = (left_ear + right_ear) / 2.0

        # Head deviation from calibrated 3-D baseline
        head_deviated = self._head_deviated(landmarks, w, h)

        # TFLite distraction classifier
        cls, conf = self._classify(frame_bgr)

        # Feed signals into the decision engine
        self._decision_engine.add_frame(
            timestamp        = t_now,
            head_deviated    = head_deviated,
            classifier_class = cls,
            classifier_conf  = conf,
            ear              = ear,
        )
        decision = self._decision_engine.get_decision()

        return DetectionResult(
            phase="DETECTING",
            calibration_progress=1.0,
            face_detected=True,
            alert=decision["alert"],
            alert_type=decision["alert_type"],
            reason=decision["reason"],
            head_deviated=head_deviated,
            ear=round(ear, 3),
            perclos_pct=decision["perclos_pct"],
            classifier_class=cls,
            classifier_class_name=CLASS_NAMES[cls] if cls < len(CLASS_NAMES) else str(cls),
            classifier_conf=round(conf, 3),
            fps=self._fps(t_now),
        )

    def _head_deviated(self, landmarks, w, h) -> bool:
        """
        True if the current head rotation deviates from the calibrated
        baseline by more than HEAD_DEVIATION_THRESHOLD radians.
        """
        if self._baseline_rvec is None:
            return False

        rvec, ok = compute_head_rotation(landmarks, w, h)
        if not ok:
            return False

        rvec_arr = np.array(rvec, dtype=np.float64).reshape(3, 1)
        R_base, _ = cv2.Rodrigues(self._baseline_rvec)
        R_curr, _ = cv2.Rodrigues(rvec_arr)

        # Relative rotation between current and baseline poses
        R_rel            = R_curr @ R_base.T
        rvec_rel, _      = cv2.Rodrigues(R_rel)
        deviation_angle  = float(np.linalg.norm(rvec_rel))   # radians

        return deviation_angle > HEAD_DEVIATION_THRESHOLD

    def _classify(self, frame_bgr: np.ndarray):
        """
        Run the TFLite distraction classifier on the raw frame.
        Returns (class_index, confidence). Falls back to (0, 0.0) if no model.
        """
        if self._interpreter is None:
            return 0, 0.0

        resized    = cv2.resize(frame_bgr, (224, 224))
        rgb        = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        batch      = np.expand_dims(normalized, axis=0)   # [1, 224, 224, 3]

        self._interpreter.set_tensor(self._input_idx, batch)
        self._interpreter.invoke()
        output = self._interpreter.get_tensor(self._output_idx)[0]  # [10]

        cls  = int(np.argmax(output))
        conf = float(output[cls])
        return cls, conf

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _no_face_result(self, t_now) -> DetectionResult:
        return DetectionResult(
            phase=self._phase,
            calibration_progress=0.0 if self._phase == "CALIBRATING" else 1.0,
            face_detected=False,
            alert=False,
            alert_type="NONE",
            reason="No face detected",
            head_deviated=False,
            ear=0.0,
            perclos_pct=0.0,
            classifier_class=0,
            classifier_class_name="Safe",
            classifier_conf=0.0,
            fps=self._fps(t_now),
        )

    def _fps(self, t_now: float) -> float:
        self._frame_ts.append(t_now)
        if len(self._frame_ts) < 2:
            return 0.0
        span = self._frame_ts[-1] - self._frame_ts[0]
        return round((len(self._frame_ts) - 1) / span, 1) if span > 0 else 0.0

    @staticmethod
    def _load_tflite(model_path: str):
        if _TFLiteInterpreter is None:
            print("[SafeDrive] WARNING: No TFLite runtime found — classifier disabled.")
            return None
        path = Path(model_path)
        if not path.exists():
            print(f"[SafeDrive] WARNING: Model not found at {model_path} — classifier disabled.")
            return None
        return _TFLiteInterpreter(model_path=str(path))
