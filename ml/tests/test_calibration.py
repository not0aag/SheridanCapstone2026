"""
test_calibration.py — Unit tests for CalibrationEngine

No camera, no model, no network needed.
All face landmarks are synthetic (hand-crafted numbers that produce known EAR values).

Run with:
    python -m pytest ml/tests/test_calibration.py -v
"""

import json
import math
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Add the src folder to the path so we can import calibration directly
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from calibration import CalibrationEngine, compute_ear, LEFT_EYE, RIGHT_EYE


# ---------------------------------------------------------------------------
# Helpers — synthetic landmark factory
# ---------------------------------------------------------------------------

class _FakeLandmark:
    """Minimal stand-in for a MediaPipe NormalizedLandmark."""
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


def _make_landmarks(nose_x=0.50, nose_y=0.50, target_ear=0.30):
    """
    Return a 468-element list of _FakeLandmark objects.

    The eye landmarks are placed so that compute_ear() returns exactly
    target_ear (within floating-point rounding).

    Math recap:
        EAR = (A + B) / (2 * C)
        We fix C = 0.20 (eye horizontal width in normalised coords).
        So A = B = target_ear * C = target_ear * 0.20
        Each vertical pair is separated by A (= target_ear * 0.20).
    """
    lm = [_FakeLandmark(0.5, 0.5) for _ in range(468)]

    # Nose tip (also a head-pose landmark)
    lm[1]   = _FakeLandmark(nose_x, nose_y)

    # Other head-pose landmarks (realistic relative positions)
    lm[152] = _FakeLandmark(nose_x,        nose_y + 0.15)   # chin
    lm[287] = _FakeLandmark(nose_x - 0.07, nose_y + 0.08)   # left mouth
    lm[57]  = _FakeLandmark(nose_x + 0.07, nose_y + 0.08)   # right mouth

    # --- Left eye: LEFT_EYE = [362, 385, 387, 263, 373, 380] ---
    # pts[0]=362 (left corner), pts[3]=263 (right corner) → horizontal C
    # pts[1]=385, pts[5]=380 → vertical pair A
    # pts[2]=387, pts[4]=373 → vertical pair B
    lcx, lcy = 0.30, 0.45
    v = target_ear * 0.20   # vertical separation = A = B
    lm[362] = _FakeLandmark(lcx - 0.10, lcy)          # left corner
    lm[263] = _FakeLandmark(lcx + 0.10, lcy)          # right corner  (also head-pose)
    lm[385] = _FakeLandmark(lcx,        lcy - v / 2)  # upper-left
    lm[387] = _FakeLandmark(lcx,        lcy - v / 2)  # upper-right
    lm[373] = _FakeLandmark(lcx,        lcy + v / 2)  # lower-right
    lm[380] = _FakeLandmark(lcx,        lcy + v / 2)  # lower-left

    # --- Right eye: RIGHT_EYE = [33, 160, 158, 133, 153, 144] ---
    rcx, rcy = 0.70, 0.45
    lm[33]  = _FakeLandmark(rcx - 0.10, rcy)          # left corner   (also head-pose)
    lm[133] = _FakeLandmark(rcx + 0.10, rcy)          # right corner
    lm[160] = _FakeLandmark(rcx,        rcy - v / 2)
    lm[158] = _FakeLandmark(rcx,        rcy - v / 2)
    lm[153] = _FakeLandmark(rcx,        rcy + v / 2)
    lm[144] = _FakeLandmark(rcx,        rcy + v / 2)

    return lm


def _feed_frames(engine, n, nose_x=0.5, nose_y=0.5, ear=0.30,
                 frame_w=640, frame_h=480):
    """
    Add n frames spread evenly over DURATION_SECONDS + 0.1 s so the engine
    finalises on the last frame. Uses unittest.mock to control time so tests
    run instantly with no real sleeping.
    """
    from unittest.mock import patch
    duration = CalibrationEngine.DURATION_SECONDS
    lm = _make_landmarks(nose_x, nose_y, ear)

    # Spread n frames evenly; last frame lands just past the deadline
    timestamps = [duration * i / max(n - 1, 1) for i in range(n)]
    timestamps[-1] = duration + 0.01   # ensure finalise triggers

    start = 1_000.0  # arbitrary monotonic start
    for t in timestamps:
        with patch("time.monotonic", return_value=start + t):
            engine.add_frame(lm, frame_w, frame_h)


# ---------------------------------------------------------------------------
# Tests: compute_ear (pure function)
# ---------------------------------------------------------------------------

class TestComputeEar:
    def test_known_value(self):
        """Landmarks built for EAR=0.30 should produce EAR≈0.30."""
        lm = _make_landmarks(target_ear=0.30)
        ear = compute_ear(lm, LEFT_EYE)
        assert abs(ear - 0.30) < 1e-6

    def test_higher_ear_open_eyes(self):
        lm = _make_landmarks(target_ear=0.35)
        assert compute_ear(lm, LEFT_EYE) == pytest.approx(0.35, abs=1e-6)

    def test_low_ear_closed_eyes(self):
        lm = _make_landmarks(target_ear=0.05)
        assert compute_ear(lm, LEFT_EYE) == pytest.approx(0.05, abs=1e-6)

    def test_both_eyes_same_landmarks(self):
        """Left and right eye produce the same EAR when landmarks are symmetric."""
        lm = _make_landmarks(target_ear=0.28)
        left  = compute_ear(lm, LEFT_EYE)
        right = compute_ear(lm, RIGHT_EYE)
        assert abs(left - right) < 1e-6


# ---------------------------------------------------------------------------
# Tests: CalibrationEngine lifecycle
# ---------------------------------------------------------------------------

class TestCalibrationLifecycle:
    def test_not_calibrated_at_start(self):
        engine = CalibrationEngine()
        assert not engine.is_calibrated
        assert engine.result is None

    def test_not_calibrated_before_duration(self):
        """Frames fed within the first 9 s should not trigger finalisation."""
        from unittest.mock import patch
        engine = CalibrationEngine()
        lm = _make_landmarks()
        # Simulate 30 frames all within the first 9 seconds
        for i in range(30):
            t = 9.0 * i / 30
            with patch("time.monotonic", return_value=1000.0 + t):
                engine.add_frame(lm, 640, 480)
        assert not engine.is_calibrated

    def test_calibrated_after_duration(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30)
        assert engine.is_calibrated

    def test_progress_increases(self):
        from unittest.mock import patch
        engine = CalibrationEngine()
        lm = _make_landmarks()
        duration = CalibrationEngine.DURATION_SECONDS
        progress_values = []
        for i in range(10):
            t = duration * i / 10
            with patch("time.monotonic", return_value=1000.0 + t):
                progress_values.append(engine.add_frame(lm, 640, 480))
        assert progress_values[0] < progress_values[-1]
        assert progress_values[0] >= 0.0
        assert progress_values[-1] <= 1.0

    def test_progress_stays_at_1_after_completion(self):
        from unittest.mock import patch
        engine = CalibrationEngine()
        _feed_frames(engine, 30)
        lm = _make_landmarks()
        with patch("time.monotonic", return_value=9999.0):
            assert engine.add_frame(lm, 640, 480) == 1.0

    def test_frames_collected_increases(self):
        from unittest.mock import patch
        engine = CalibrationEngine()
        lm = _make_landmarks()
        for i in range(15):
            with patch("time.monotonic", return_value=1000.0 + i * 0.1):
                engine.add_frame(lm, 640, 480)
        assert engine.frames_collected == 15


# ---------------------------------------------------------------------------
# Tests: EAR threshold calculation
# ---------------------------------------------------------------------------

class TestEarThreshold:
    def test_threshold_is_75_percent_of_mean(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30, ear=0.30)
        # No blinks in synthetic data, so mean_open_ear ≈ 0.30
        assert engine.result["mean_open_ear"] == pytest.approx(0.30, abs=0.01)
        assert engine.result["ear_threshold"] == pytest.approx(0.30 * 0.75, abs=0.01)

    def test_blink_frames_are_filtered(self):
        """
        Mix 3 blink frames (EAR=0.05) into 27 open frames (EAR=0.30).
        The bottom-10% cutoff should discard them and keep mean near 0.30.
        """
        from unittest.mock import patch
        engine = CalibrationEngine()
        lm_open  = _make_landmarks(target_ear=0.30)
        lm_blink = _make_landmarks(target_ear=0.05)
        duration = CalibrationEngine.DURATION_SECONDS

        # 27 open frames across first 9 s, 3 blink frames in last second
        open_times  = [duration * i / 27 for i in range(27)]
        blink_times = [9.1, 9.5, duration + 0.01]

        for t in open_times:
            with patch("time.monotonic", return_value=1000.0 + t):
                engine.add_frame(lm_open, 640, 480)
        for t in blink_times:
            with patch("time.monotonic", return_value=1000.0 + t):
                engine.add_frame(lm_blink, 640, 480)

        assert engine.result["mean_open_ear"] > 0.28


# ---------------------------------------------------------------------------
# Tests: baseline nose position
# ---------------------------------------------------------------------------

class TestNoseBaseline:
    def test_baseline_nose_is_median(self):
        """
        Feed 30 frames all with the same nose position — baseline should match.
        """
        engine = CalibrationEngine()
        _feed_frames(engine, 30, nose_x=0.52, nose_y=0.47)
        assert engine.result["baseline_nose"]["x"] == pytest.approx(0.52, abs=1e-4)
        assert engine.result["baseline_nose"]["y"] == pytest.approx(0.47, abs=1e-4)

    def test_baseline_nose_robust_to_outlier(self):
        """
        29 frames at (0.50, 0.50) + 1 outlier at (0.90, 0.10).
        Median should stay near (0.50, 0.50).
        """
        from unittest.mock import patch
        engine = CalibrationEngine()
        lm_normal  = _make_landmarks(nose_x=0.50, nose_y=0.50)
        lm_outlier = _make_landmarks(nose_x=0.90, nose_y=0.10)
        duration = CalibrationEngine.DURATION_SECONDS

        for i in range(29):
            t = duration * i / 29
            with patch("time.monotonic", return_value=1000.0 + t):
                engine.add_frame(lm_normal, 640, 480)
        with patch("time.monotonic", return_value=1000.0 + duration + 0.01):
            engine.add_frame(lm_outlier, 640, 480)

        assert engine.result["baseline_nose"]["x"] == pytest.approx(0.50, abs=0.01)
        assert engine.result["baseline_nose"]["y"] == pytest.approx(0.50, abs=0.01)


# ---------------------------------------------------------------------------
# Tests: result JSON structure
# ---------------------------------------------------------------------------

class TestResultStructure:
    REQUIRED_KEYS = {
        "baseline_nose",
        "baseline_rotation_vector",
        "mean_open_ear",
        "ear_threshold",
        "calibration_timestamp",
        "frames_used",
    }

    def test_all_keys_present(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30)
        assert self.REQUIRED_KEYS.issubset(engine.result.keys())

    def test_baseline_nose_has_x_and_y(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30)
        nose = engine.result["baseline_nose"]
        assert "x" in nose and "y" in nose

    def test_rotation_vector_is_3_elements(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30)
        rvec = engine.result["baseline_rotation_vector"]
        assert len(rvec) == 3

    def test_ear_threshold_less_than_mean(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30)
        assert engine.result["ear_threshold"] < engine.result["mean_open_ear"]

    def test_frames_used_positive(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30)
        assert engine.result["frames_used"] > 0


# ---------------------------------------------------------------------------
# Tests: save and load
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_save_raises_if_not_calibrated(self):
        engine = CalibrationEngine()
        with pytest.raises(RuntimeError):
            engine.save("/tmp/should_not_exist.json")

    def test_save_creates_valid_json(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        engine.save(path)
        with open(path) as f:
            data = json.load(f)
        assert "ear_threshold" in data

    def test_load_returns_same_values(self):
        engine = CalibrationEngine()
        _feed_frames(engine, 30, ear=0.30)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        engine.save(path)
        loaded = CalibrationEngine.load(path)
        assert loaded["mean_open_ear"] == pytest.approx(
            engine.result["mean_open_ear"], abs=1e-4
        )
        assert loaded["ear_threshold"] == pytest.approx(
            engine.result["ear_threshold"], abs=1e-4
        )
