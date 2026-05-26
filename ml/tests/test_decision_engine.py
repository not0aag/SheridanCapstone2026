"""
test_decision_engine.py — Unit tests for DecisionEngine

No camera, no model, no network needed.
All tests use synthetic timestamps and hand-crafted frame sequences.

Tests cover every scenario listed in CLAUDE.md Section 4 Step 2,
plus edge cases for the distraction window, PERCLOS window, and pruning.

Run with:
    python -m pytest ml/tests/test_decision_engine.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from decision_engine import DecisionEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EAR_OPEN    = 0.30   # comfortably above any realistic threshold
EAR_CLOSED  = 0.05   # clearly below threshold
THRESHOLD   = 0.25   # ear_threshold passed to DecisionEngine
FPS         = 30     # simulated frame rate


def _engine():
    """Fresh engine with a standard threshold."""
    return DecisionEngine(ear_threshold=THRESHOLD)


def _feed(engine, n, *, t_start=1000.0, fps=FPS,
          head_deviated=False, cls=0, conf=0.9, ear=EAR_OPEN):
    """
    Add n frames at a constant simulated frame rate starting at t_start.
    Returns the timestamp of the last frame added.
    """
    for i in range(n):
        engine.add_frame(
            timestamp        = t_start + i / fps,
            head_deviated    = head_deviated,
            classifier_class = cls,
            classifier_conf  = conf,
            ear              = ear,
        )
    return t_start + (n - 1) / fps


# ---------------------------------------------------------------------------
# CLAUDE.md mandated tests (Section 4, Step 2)
# ---------------------------------------------------------------------------

class TestClaudeMdScenarios:
    """
    The five tests explicitly required by the build spec.
    These must all pass before Step 2 is considered done.
    """

    def test_1_all_safe_no_alert(self):
        """15 frames, all c0, no head deviation → alert=False."""
        engine = _engine()
        _feed(engine, 15, head_deviated=False, cls=0)
        result = engine.get_decision()
        assert result["alert"] is False
        assert result["alert_type"] == "NONE"

    def test_2_distracted_when_both_signals_agree(self):
        """10 frames with head deviation + non-c0 class → DISTRACTED."""
        engine = _engine()
        _feed(engine, 10, head_deviated=True, cls=1, conf=0.85)
        _feed(engine, 5,  t_start=1000.0 + 10/FPS,
              head_deviated=False, cls=0)
        result = engine.get_decision()
        assert result["alert"] is True
        assert result["alert_type"] == "DISTRACTED"

    def test_3_brief_distraction_no_alert(self):
        """3 distracted frames then 12 safe → alert=False (below window threshold)."""
        engine = _engine()
        _feed(engine, 3,  head_deviated=True, cls=2)
        _feed(engine, 12, t_start=1000.0 + 3/FPS,
              head_deviated=False, cls=0)
        result = engine.get_decision()
        assert result["alert"] is False

    def test_4_no_drowsy_before_full_window(self):
        """2 seconds of EAR < threshold → no alert (window not full yet)."""
        engine = _engine()
        _feed(engine, 2 * FPS, ear=EAR_CLOSED)   # only 2 seconds of data
        result = engine.get_decision()
        assert result["alert"] is False

    def test_5_drowsy_after_full_window(self):
        """5 seconds of EAR < threshold → alert=True, type=DROWSY."""
        engine = _engine()
        _feed(engine, 5 * FPS, ear=EAR_CLOSED)
        result = engine.get_decision()
        assert result["alert"] is True
        assert result["alert_type"] == "DROWSY"


# ---------------------------------------------------------------------------
# Distraction logic
# ---------------------------------------------------------------------------

class TestDistraction:
    def test_head_only_no_alert(self):
        """Head deviated in every frame but classifier always says c0 → no alert."""
        engine = _engine()
        _feed(engine, 15, head_deviated=True, cls=0)
        assert engine.get_decision()["alert"] is False

    def test_classifier_only_no_alert(self):
        """Classifier always says texting but head never deviated → no alert."""
        engine = _engine()
        _feed(engine, 15, head_deviated=False, cls=1)
        assert engine.get_decision()["alert"] is False

    def test_exact_head_rate_boundary(self):
        """
        Exactly 60 % head-deviation frames (threshold is > 60 %, not >= 60 %).
        9 deviated + 6 safe = 60 % — should NOT alert.
        """
        engine = _engine()
        _feed(engine, 9,  head_deviated=True,  cls=1)
        _feed(engine, 6,  t_start=1000.0 + 9/FPS,
              head_deviated=False, cls=1)
        result = engine.get_decision()
        assert result["head_alert_rate"] == pytest.approx(9/15, abs=0.001)
        assert result["alert"] is False   # 60 % is NOT > 60 %

    def test_just_above_head_rate_boundary(self):
        """10 deviated out of 15 = 66.7 % > 60 % threshold."""
        engine = _engine()
        _feed(engine, 10, head_deviated=True,  cls=1)
        _feed(engine, 5,  t_start=1000.0 + 10/FPS,
              head_deviated=False, cls=1)
        result = engine.get_decision()
        assert result["head_alert_rate"] == pytest.approx(10/15, abs=0.001)
        assert result["alert"] is True
        assert result["alert_type"] == "DISTRACTED"

    def test_distraction_window_uses_only_last_15_frames(self):
        """
        Feed 5 distracted frames then 15 safe frames (20 total).
        The distraction window should only see the last 15 (all safe) → no alert.
        """
        engine = _engine()
        _feed(engine, 5,  head_deviated=True, cls=1)
        _feed(engine, 15, t_start=1000.0 + 5/FPS,
              head_deviated=False, cls=0)
        result = engine.get_decision()
        assert result["distraction_rate"] == 0.0
        assert result["alert"] is False

    def test_distraction_rate_value(self):
        """7 non-c0 frames out of 15 → distraction_rate ≈ 0.467."""
        engine = _engine()
        _feed(engine, 7,  head_deviated=True, cls=3)
        _feed(engine, 8,  t_start=1000.0 + 7/FPS,
              head_deviated=True, cls=0)
        result = engine.get_decision()
        assert result["distraction_rate"] == pytest.approx(7/15, abs=0.001)

    def test_head_alert_rate_value(self):
        """6 deviated frames out of 10 total → head_alert_rate = 0.6."""
        engine = _engine()
        _feed(engine, 6,  head_deviated=True,  cls=0)
        _feed(engine, 4,  t_start=1000.0 + 6/FPS,
              head_deviated=False, cls=0)
        result = engine.get_decision()
        assert result["head_alert_rate"] == pytest.approx(6/10, abs=0.001)


# ---------------------------------------------------------------------------
# Drowsiness / PERCLOS logic
# ---------------------------------------------------------------------------

class TestDrowsiness:
    def test_perclos_zero_when_eyes_open(self):
        """5 seconds of open eyes → perclos_pct = 0."""
        engine = _engine()
        _feed(engine, 5 * FPS, ear=EAR_OPEN)
        assert engine.get_decision()["perclos_pct"] == pytest.approx(0.0, abs=1.0)

    def test_perclos_100_when_eyes_always_closed(self):
        """5 seconds of EAR < threshold → perclos_pct ≈ 100."""
        engine = _engine()
        _feed(engine, 5 * FPS, ear=EAR_CLOSED)
        assert engine.get_decision()["perclos_pct"] == pytest.approx(100.0, abs=1.0)

    def test_perclos_50_when_alternating(self):
        """
        5 seconds, eyes alternating open/closed every frame → perclos_pct ≈ 50.
        Only the last 4 seconds are in the window.
        """
        engine = _engine()
        for i in range(5 * FPS):
            ear = EAR_CLOSED if i % 2 == 0 else EAR_OPEN
            engine.add_frame(
                timestamp=1000.0 + i / FPS,
                head_deviated=False, classifier_class=0,
                classifier_conf=0.9, ear=ear,
            )
        result = engine.get_decision()
        assert result["perclos_pct"] == pytest.approx(50.0, abs=3.0)

    def test_old_closed_eye_frames_pruned(self):
        """
        3 s of closed eyes, then 5 s of open eyes.
        After 5 s of open eyes the closed-eye frames are outside the 4-second window
        and should no longer count toward PERCLOS.
        """
        engine = _engine()
        # 3 seconds of closed eyes
        last_t = _feed(engine, 3 * FPS, ear=EAR_CLOSED)
        # 5 seconds of open eyes (pushes closed-eye frames out of the 4 s window)
        _feed(engine, 5 * FPS, t_start=last_t + 1/FPS, ear=EAR_OPEN)
        result = engine.get_decision()
        assert result["perclos_pct"] == pytest.approx(0.0, abs=3.0)
        assert result["alert"] is False

    def test_drowsy_requires_full_window(self):
        """
        Even 100 % closed-eye PERCLOS must not alert until 4 seconds have elapsed.
        Feed 3.9 seconds → no alert.
        """
        engine = _engine()
        frames = int(3.9 * FPS)
        _feed(engine, frames, ear=EAR_CLOSED)
        assert engine.get_decision()["alert"] is False

    def test_drowsy_fires_just_after_full_window(self):
        """At exactly 4 seconds of closed eyes the alert should fire."""
        engine = _engine()
        _feed(engine, 4 * FPS + 1, ear=EAR_CLOSED)
        result = engine.get_decision()
        assert result["alert"] is True
        assert result["alert_type"] == "DROWSY"

    def test_drowsy_priority_over_distracted(self):
        """
        When both drowsiness AND distraction thresholds are exceeded,
        DROWSY must be reported (it has higher priority).
        """
        engine = _engine()
        # 5 seconds: head deviated, distracted class, AND eyes closed
        _feed(engine, 5 * FPS,
              head_deviated=True, cls=1, conf=0.9, ear=EAR_CLOSED)
        result = engine.get_decision()
        assert result["alert_type"] == "DROWSY"


# ---------------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------------

class TestResultStructure:
    REQUIRED_KEYS = {
        "alert", "alert_type", "reason",
        "head_alert_rate", "distraction_rate", "perclos_pct",
    }

    def test_all_keys_present_on_empty(self):
        engine = _engine()
        assert self.REQUIRED_KEYS.issubset(engine.get_decision().keys())

    def test_all_keys_present_after_frames(self):
        engine = _engine()
        _feed(engine, 10)
        assert self.REQUIRED_KEYS.issubset(engine.get_decision().keys())

    def test_alert_is_bool(self):
        engine = _engine()
        _feed(engine, 10)
        assert isinstance(engine.get_decision()["alert"], bool)

    def test_alert_type_is_valid_string(self):
        engine = _engine()
        _feed(engine, 10)
        assert engine.get_decision()["alert_type"] in {"DISTRACTED", "DROWSY", "NONE"}

    def test_rates_between_0_and_1(self):
        engine = _engine()
        _feed(engine, 15)
        result = engine.get_decision()
        assert 0.0 <= result["head_alert_rate"]  <= 1.0
        assert 0.0 <= result["distraction_rate"] <= 1.0

    def test_perclos_between_0_and_100(self):
        engine = _engine()
        _feed(engine, 30, ear=EAR_CLOSED)
        result = engine.get_decision()
        assert 0.0 <= result["perclos_pct"] <= 100.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_engine_returns_none(self):
        engine = _engine()
        result = engine.get_decision()
        assert result["alert"] is False
        assert result["alert_type"] == "NONE"

    def test_single_frame(self):
        engine = _engine()
        engine.add_frame(1000.0, False, 0, 0.9, EAR_OPEN)
        result = engine.get_decision()
        assert result["alert"] is False

    def test_invalid_ear_threshold_zero(self):
        with pytest.raises(ValueError):
            DecisionEngine(ear_threshold=0)

    def test_invalid_ear_threshold_negative(self):
        with pytest.raises(ValueError):
            DecisionEngine(ear_threshold=-0.1)

    def test_reset_clears_all_history(self):
        engine = _engine()
        # Build up enough for a DROWSY alert
        _feed(engine, 5 * FPS, ear=EAR_CLOSED)
        assert engine.get_decision()["alert"] is True
        engine.reset()
        assert engine.get_decision()["alert"] is False
        assert engine.get_decision()["perclos_pct"] == 0.0

    def test_high_fps_does_not_change_distraction_window(self):
        """
        At 60 fps the distraction window still covers the last 15 frames,
        which is now 0.25 seconds rather than 0.5 seconds. The window is
        frame-count based, not time-based — this is intentional.
        """
        engine = _engine()
        # 15 distracted frames at 60 fps
        _feed(engine, 15, fps=60, head_deviated=True, cls=1)
        result = engine.get_decision()
        assert result["head_alert_rate"]  == pytest.approx(1.0)
        assert result["distraction_rate"] == pytest.approx(1.0)
        assert result["alert"] is True
        assert result["alert_type"] == "DISTRACTED"
