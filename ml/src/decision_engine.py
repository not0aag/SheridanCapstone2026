"""
decision_engine.py — DecisionEngine for SafeDrive AI

Sits between raw per-frame signals and the alert output.
Maintains a rolling window of recent frames and only fires when the
evidence is consistent enough over time — preventing single-frame noise
from triggering alerts.

Two independent alert paths:

  DROWSY    — PERCLOS > 30 % of the last 4 seconds had EAR < threshold
               (requires a full 4-second window before it can fire)

  DISTRACTED — head deviated in > 60 % of the last 15 frames
               AND non-safe classifier class in > 40 % of the last 15 frames
               (both signals must agree — neither alone is enough)

Usage:
    engine = DecisionEngine(ear_threshold=0.23)   # value from calibration.json

    # call once per camera frame:
    engine.add_frame(
        timestamp        = time.monotonic(),
        head_deviated    = True,
        classifier_class = 1,
        classifier_conf  = 0.87,
        ear              = 0.19,
    )

    result = engine.get_decision()
    if result["alert"]:
        trigger_alert(result["alert_type"])
"""

from collections import deque


class DecisionEngine:
    """
    Rolling-window distraction and drowsiness decision logic.

    Parameters
    ----------
    ear_threshold : float
        The per-user EAR value below which eyes are considered closed.
        Read from calibration.json → "ear_threshold".
    """

    # -----------------------------------------------------------------------
    # Tunable constants — do not change without re-running real-world tests
    # -----------------------------------------------------------------------
    DISTRACTION_WINDOW   = 25     # number of recent frames for distraction scoring
                                  # 25 frames ≈ 0.8 s at 30 fps — brief mirror
                                  # checks fall below the 60 % threshold, sustained
                                  # phone use does not. Tune in Step 6.
    DROWSY_WINDOW_SECS   = 4.0    # rolling time window for PERCLOS (seconds)
    HEAD_RATE_THRESHOLD  = 0.60   # alert if head deviated in >60 % of distraction window
    DIST_RATE_THRESHOLD  = 0.40   # alert if non-c0 class in >40 % of distraction window
    PERCLOS_THRESHOLD    = 30.0   # alert if >30 % of drowsy window had EAR < threshold

    def __init__(self, ear_threshold: float):
        if ear_threshold <= 0:
            raise ValueError(
                f"ear_threshold must be a positive number, got {ear_threshold!r}. "
                "Read it from calibration.json."
            )
        self._ear_threshold   = ear_threshold
        self._frames          = deque()   # pruned to last DROWSY_WINDOW_SECS
        self._first_timestamp = None      # time of the very first frame ever received

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def add_frame(
        self,
        timestamp:        float,
        head_deviated:    bool,
        classifier_class: int,
        classifier_conf:  float,
        ear:              float,
    ) -> None:
        """
        Record one frame of signals.

        timestamp        — monotonic time in seconds (use time.monotonic())
        head_deviated    — True if head rotation deviated from calibrated baseline
        classifier_class — TFLite top-1 class index (0 = safe, 1-9 = distracted)
        classifier_conf  — confidence of that prediction (0.0 – 1.0)
        ear              — average Eye Aspect Ratio for this frame
        """
        if self._first_timestamp is None:
            self._first_timestamp = timestamp

        self._frames.append({
            "t":             timestamp,
            "head_deviated": head_deviated,
            "class":         classifier_class,
            "conf":          classifier_conf,
            "ear":           ear,
        })

        # Keep only frames within the drowsiness window
        cutoff = timestamp - self.DROWSY_WINDOW_SECS
        while self._frames and self._frames[0]["t"] < cutoff:
            self._frames.popleft()

    def get_decision(self) -> dict:
        """
        Evaluate the current rolling window and return a decision dict:

        {
            "alert":           bool,
            "alert_type":      "DISTRACTED" | "DROWSY" | "NONE",
            "reason":          str,
            "head_alert_rate": float,   # fraction of last 15 frames with head deviation
            "distraction_rate":float,   # fraction of last 15 frames with non-c0 class
            "perclos_pct":     float,   # % of last 4 s with EAR < threshold
        }
        """
        if not self._frames:
            return self._result(False, "NONE", "No frames received", 0.0, 0.0, 0.0)

        # --- Distraction signals: last DISTRACTION_WINDOW frames ---
        dist_frames      = list(self._frames)[-self.DISTRACTION_WINDOW:]
        n                = len(dist_frames)
        head_alert_rate  = sum(1 for f in dist_frames if f["head_deviated"]) / n
        distraction_rate = sum(1 for f in dist_frames if f["class"] != 0) / n

        # --- PERCLOS: all frames currently in deque (pruned to last 4 s) ---
        n_all       = len(self._frames)
        n_closed    = sum(1 for f in self._frames if f["ear"] < self._ear_threshold)
        perclos_pct = (n_closed / n_all * 100.0) if n_all > 0 else 0.0

        # How long has the engine been running in total?
        total_elapsed = self._frames[-1]["t"] - self._first_timestamp

        # ---- Decision (DROWSY takes priority over DISTRACTED) ----

        if (total_elapsed >= self.DROWSY_WINDOW_SECS
                and perclos_pct > self.PERCLOS_THRESHOLD):
            return self._result(
                True, "DROWSY",
                f"Eyes closed {perclos_pct:.0f}% of last "
                f"{self.DROWSY_WINDOW_SECS:.0f}s",
                head_alert_rate, distraction_rate, perclos_pct,
            )

        if (head_alert_rate  > self.HEAD_RATE_THRESHOLD
                and distraction_rate > self.DIST_RATE_THRESHOLD):
            return self._result(
                True, "DISTRACTED",
                f"Head deviated {head_alert_rate:.0%}, "
                f"non-safe class {distraction_rate:.0%} of last {n} frames",
                head_alert_rate, distraction_rate, perclos_pct,
            )

        return self._result(
            False, "NONE", "All clear",
            head_alert_rate, distraction_rate, perclos_pct,
        )

    def reset(self) -> None:
        """Clear all history (e.g. after a red-light stop or recalibration)."""
        self._frames.clear()
        self._first_timestamp = None

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    @staticmethod
    def _result(alert, alert_type, reason,
                head_alert_rate, distraction_rate, perclos_pct) -> dict:
        return {
            "alert":            alert,
            "alert_type":       alert_type,
            "reason":           reason,
            "head_alert_rate":  round(head_alert_rate,  3),
            "distraction_rate": round(distraction_rate, 3),
            "perclos_pct":      round(perclos_pct,       1),
        }
