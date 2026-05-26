"""
calibration.py — CalibrationEngine for SafeDrive AI

Collects 30 frames of MediaPipe FaceMesh landmarks while the driver looks
straight ahead, then computes:
  - A per-user EAR threshold (eye openness baseline × 0.75)
  - A head-pose baseline (nose position + 3-D rotation vector)

Saves everything to calibration.json. The rest of the pipeline loads that
file on startup so all detection is relative to THIS driver at THIS angle.

Run directly for a live webcam calibration demo:
    python ml/src/calibration.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from scipy.spatial import distance as dist

# ---------------------------------------------------------------------------
# Landmark index constants — must match perclos_demo.py exactly
# ---------------------------------------------------------------------------
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33,  160, 158, 133, 153, 144]

# 6 stable MediaPipe indices used for head-pose estimation via solvePnP
HEAD_POSE_INDICES = [1, 152, 263, 33, 287, 57]

# Generic 3-D face model in millimetres (standard values used across DMS research)
# Order matches HEAD_POSE_INDICES: nose tip, chin, L-eye outer, R-eye outer,
#                                  L-mouth corner, R-mouth corner
FACE_3D_MODEL = np.array([
    [ 0.0,    0.0,    0.0],
    [ 0.0,  -63.6,  -12.5],
    [-43.3,  32.7,  -26.0],
    [ 43.3,  32.7,  -26.0],
    [-28.9, -28.9,  -24.1],
    [ 28.9, -28.9,  -24.1],
], dtype=np.float64)


# ---------------------------------------------------------------------------
# Pure functions (easy to unit-test in isolation)
# ---------------------------------------------------------------------------

def compute_ear(landmarks, eye_indices):
    """
    Eye Aspect Ratio — identical formula to perclos_demo.py.

    EAR = (vertical_A + vertical_B) / (2 * horizontal_C)

    When eyes are wide open EAR ≈ 0.25–0.35.
    When closed EAR ≈ 0.0–0.05.
    """
    pts = np.array([(landmarks[i].x, landmarks[i].y) for i in eye_indices])
    A = dist.euclidean(pts[1], pts[5])
    B = dist.euclidean(pts[2], pts[4])
    C = dist.euclidean(pts[0], pts[3])
    if C < 1e-6:
        return 0.0
    return (A + B) / (2.0 * C)


def compute_head_rotation(landmarks, frame_w, frame_h):
    """
    Estimate head rotation using OpenCV solvePnP.

    Maps 6 known 3-D face model points to their 2-D positions in the frame.
    Returns (rvec, True) on success — rvec is [rx, ry, rz] in radians.
    Returns (None, False) if the solver fails (e.g. face partially off-screen).

    The camera matrix is approximated from frame dimensions (no calibration
    board needed — good enough for relative pose comparison).
    """
    image_pts = np.array(
        [[landmarks[i].x * frame_w, landmarks[i].y * frame_h]
         for i in HEAD_POSE_INDICES],
        dtype=np.float64,
    )

    focal = float(frame_w)
    camera_matrix = np.array([
        [focal,   0,  frame_w / 2.0],
        [0,   focal,  frame_h / 2.0],
        [0,       0,            1.0],
    ], dtype=np.float64)
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    ok, rvec, _ = cv2.solvePnP(
        FACE_3D_MODEL, image_pts, camera_matrix, dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not ok:
        return None, False
    return rvec.flatten().tolist(), True


# ---------------------------------------------------------------------------
# CalibrationEngine
# ---------------------------------------------------------------------------

class CalibrationEngine:
    """
    Feed it one frame of MediaPipe landmarks at a time via add_frame().
    Collects data for DURATION_SECONDS (time-based, not frame-count-based)
    then finalises and sets is_calibrated = True.
    Call save() to write calibration.json.
    """

    DURATION_SECONDS    = 10    # collect for exactly 10 s regardless of FPS
    EAR_THRESHOLD_RATIO = 0.75  # alert threshold = mean_open_ear * this
    EAR_OUTLIER_CUTOFF  = 10    # drop bottom 10 % of EAR samples (blinks)

    def __init__(self):
        self._ear_samples  = []   # one float per frame
        self._nose_samples = []   # one (x, y) tuple per frame
        self._rvec_samples = []   # one [rx,ry,rz] list per frame (if solvePnP ok)
        self._start_time   = None  # set on first frame
        self._frame_count  = 0
        self.is_calibrated = False
        self.result        = None  # populated by _finalise()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_frame(self, landmarks, frame_w, frame_h):
        """
        Process one frame's MediaPipe landmarks.

        landmarks  — the .landmark list from a MediaPipe FaceLandmark result
        frame_w/h  — pixel dimensions of the camera frame

        Returns float: calibration progress from 0.0 → 1.0.
        Returns 1.0 immediately if already calibrated.
        """
        import time

        if self.is_calibrated:
            return 1.0

        now = time.monotonic()
        if self._start_time is None:
            self._start_time = now

        elapsed  = now - self._start_time
        progress = min(elapsed / self.DURATION_SECONDS, 1.0)

        # EAR — average of both eyes
        left_ear  = compute_ear(landmarks, LEFT_EYE)
        right_ear = compute_ear(landmarks, RIGHT_EYE)
        self._ear_samples.append((left_ear + right_ear) / 2.0)

        # Nose position (landmark 1 = nose tip)
        nose = landmarks[1]
        self._nose_samples.append((nose.x, nose.y))

        # Head rotation
        rvec, ok = compute_head_rotation(landmarks, frame_w, frame_h)
        if ok:
            self._rvec_samples.append(rvec)

        self._frame_count += 1

        if elapsed >= self.DURATION_SECONDS:
            self._finalise()

        return progress

    @property
    def frames_collected(self):
        return self._frame_count

    @property
    def elapsed_seconds(self):
        import time
        if self._start_time is None:
            return 0.0
        return min(time.monotonic() - self._start_time, self.DURATION_SECONDS)

    def save(self, path="calibration.json"):
        """Write calibration.json. Raises RuntimeError if not yet done."""
        if not self.is_calibrated:
            raise RuntimeError(
                f"Calibration incomplete — {self.elapsed_seconds:.1f}s elapsed, "
                f"need {self.DURATION_SECONDS}s."
            )
        with open(path, "w") as f:
            json.dump(self.result, f, indent=2)

    @staticmethod
    def load(path="calibration.json"):
        """Load a saved calibration JSON and return it as a dict."""
        with open(path) as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _finalise(self):
        # --- EAR: filter blink outliers then average ---
        cutoff   = np.percentile(self._ear_samples, self.EAR_OUTLIER_CUTOFF)
        filtered = [e for e in self._ear_samples if e >= cutoff]
        mean_open_ear = float(np.mean(filtered))

        # --- Nose: take median across all frames (robust to head movement) ---
        xs, ys = zip(*self._nose_samples)
        baseline_nose = {
            "x": float(np.median(xs)),
            "y": float(np.median(ys)),
        }

        # --- Head rotation: median rotation vector ---
        if self._rvec_samples:
            baseline_rvec = np.median(self._rvec_samples, axis=0).tolist()
        else:
            # solvePnP failed on all frames (e.g. unit-test synthetic data)
            baseline_rvec = [0.0, 0.0, 0.0]

        self.result = {
            "baseline_nose":            baseline_nose,
            "baseline_rotation_vector": baseline_rvec,
            "mean_open_ear":            round(mean_open_ear, 4),
            "ear_threshold":            round(mean_open_ear * self.EAR_THRESHOLD_RATIO, 4),
            "calibration_timestamp":    datetime.now(timezone.utc).isoformat(),
            "frames_used":              len(filtered),
        }
        self.is_calibrated = True


# ---------------------------------------------------------------------------
# Webcam demo — run `python ml/src/calibration.py` to calibrate live
# ---------------------------------------------------------------------------

def run_webcam_calibration(output_path="calibration.json"):
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    engine = CalibrationEngine()

    print(f"[SafeDrive] Starting calibration. Output → {output_path}")
    print("[SafeDrive] Mount your phone, then press SPACE to begin.")
    print("[SafeDrive] Look straight ahead at the road during calibration.")
    print("[SafeDrive] Press Q to quit.")

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as face_mesh:

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[SafeDrive] ERROR: Could not open webcam.")
            sys.exit(1)

        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        collecting = False  # wait for SPACE before counting frames

        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)
            display = frame.copy()

            face_detected = results.multi_face_landmarks is not None

            if collecting and face_detected:
                landmarks = results.multi_face_landmarks[0].landmark
                progress = engine.add_frame(landmarks, frame_w, frame_h)
                remaining = max(0, CalibrationEngine.DURATION_SECONDS - engine.elapsed_seconds)
                label = f"CALIBRATING... {remaining:.0f}s remaining"
                cv2.putText(display, label, (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)
                bar_w = int(progress * (frame_w - 40))
                cv2.rectangle(display, (20, 70), (20 + bar_w, 90), (0, 200, 255), -1)

                if engine.is_calibrated:
                    engine.save(output_path)
                    cv2.putText(display, "CALIBRATION COMPLETE!", (20, 130),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    cv2.imshow("SafeDrive Calibration", display)
                    cv2.waitKey(2000)
                    break

            elif not collecting:
                msg = "Face detected — press SPACE to start" if face_detected \
                      else "No face detected — position your phone"
                color = (0, 255, 0) if face_detected else (0, 0, 255)
                cv2.putText(display, msg, (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            cv2.imshow("SafeDrive Calibration", display)
            key = cv2.waitKey(5) & 0xFF
            if key == ord("q") or key == 27:   # Q or ESC
                break
            if key == ord(" ") and face_detected:
                collecting = True

        cap.release()
        cv2.destroyAllWindows()

    if engine.is_calibrated:
        print(f"[SafeDrive] Saved to {output_path}")
        print(f"  EAR threshold : {engine.result['ear_threshold']}")
        print(f"  Mean open EAR : {engine.result['mean_open_ear']}")
        print(f"  Nose baseline : {engine.result['baseline_nose']}")
    else:
        print("[SafeDrive] Calibration was not completed.")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "calibration.json"
    run_webcam_calibration(out)
