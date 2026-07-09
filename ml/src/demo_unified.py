"""
demo_unified.py — Live webcam demo of the full SafeDrive pipeline

Runs the complete detection stack end-to-end:
    Webcam → MediaPipe → CalibrationEngine → TFLite → DecisionEngine → Overlay

Usage (from repo root):
    safedrive_ml/bin/python3.10 ml/src/demo_unified.py

Optional args:
    --model         path to TFLite model  (default: ml-models/week3_finetuning/tflite_models/class_weights_model_91pct.tflite)
    --cal           path to calibration.json (default: calibration.json)
    --recal         force recalibration even if calibration.json already exists
    --camera-index  force a specific camera device instead of auto-detecting
    --list-cameras  print detected camera devices and exit

Keys during demo:
    R    — force recalibration (delete current calibration and restart)
    Q / ESC — quit

Camera selection:
    Dev machines often have more than one camera device registered — e.g.
    phone-as-webcam apps (Iriun, DroidCam) or virtual cams (OBS, NVIDIA
    Broadcast) alongside the real one, and cv2.VideoCapture(0) has no
    guarantee of picking the physical webcam. This script auto-detects by
    skipping known virtual-camera names and verifying the first frame isn't
    black before use; pass --camera-index to override.
"""

import argparse
import sys
import os
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from safe_drive_detector import SafeDriveDetector, DetectionResult

# Name fragments (case-insensitive) of virtual/phone-as-webcam devices to skip
# during auto-detection — these commonly enumerate before the real webcam and
# show a solid black frame when nothing is actively streaming to them.
_VIRTUAL_CAMERA_NAME_PATTERNS = (
    "iriun", "droidcam", "epoccam", "obs virtual", "virtual camera", "broadcast",
)

_BLACK_FRAME_BRIGHTNESS_THRESHOLD = 10.0  # mean pixel value below this ~= black


def _dshow_device_names():
    """Ordered DirectShow device names (Windows only, matches CAP_DSHOW indices)."""
    if sys.platform != "win32":
        return None
    try:
        from pygrabber.dshow_graph import FilterGraph
        return FilterGraph().get_input_devices()
    except Exception:
        return None


_WARMUP_FRAMES = 15  # real UVC webcams need ~1-1.5s for auto-exposure to ramp up


def _frame_brightness(cap) -> float:
    """Read (and discard) warm-up frames, returning the brightness of the
    last one — a webcam's very first frame after opening is often dark/black
    while auto-exposure is still converging, which looks identical to a dead
    virtual camera if checked immediately."""
    brightness = -1.0
    for _ in range(_WARMUP_FRAMES):
        ok, frame = cap.read()
        brightness = float(np.mean(frame)) if ok and frame is not None else -1.0
    return brightness


def select_camera(explicit_index=None):
    """Open a real camera, skipping virtual/phone-as-webcam devices by name
    and verifying the feed isn't black after auto-exposure warm-up, instead
    of blindly trusting index 0 (see module docstring)."""
    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    names = _dshow_device_names()

    if explicit_index is not None:
        cap = cv2.VideoCapture(explicit_index, backend)
        if not cap.isOpened():
            print(f"[SafeDrive] ERROR: Could not open camera index {explicit_index}.")
            sys.exit(1)
        label = names[explicit_index] if names and explicit_index < len(names) else "unknown"
        print(f"[SafeDrive] Using camera {explicit_index} ({label}) — forced via --camera-index.")
        return cap

    if names:
        print(f"[SafeDrive] Cameras detected: {list(enumerate(names))}")

    candidates = range(len(names)) if names else range(5)
    skipped, probed = [], []
    for i in candidates:
        name = names[i] if names else "unknown"
        if names and any(p in name.lower() for p in _VIRTUAL_CAMERA_NAME_PATTERNS):
            skipped.append((i, name))
            continue
        cap = cv2.VideoCapture(i, backend)
        if not cap.isOpened():
            continue
        brightness = _frame_brightness(cap)
        probed.append((i, name, brightness))
        if brightness > _BLACK_FRAME_BRIGHTNESS_THRESHOLD:
            print(f"[SafeDrive] Using camera {i} ({name}).")
            return cap
        cap.release()

    print("[SafeDrive] ERROR: No working (non-black) camera found.")
    if skipped:
        print(f"[SafeDrive]   Skipped as virtual cameras: {skipped}")
    if probed:
        print(f"[SafeDrive]   Probed and rejected (black): "
              f"{[(i, n, f'{b:.1f}') for i, n, b in probed]}")
    print("[SafeDrive] If you're using a phone-as-webcam app, make sure it's "
          "open and actively streaming. Run with --list-cameras to see all "
          "devices, then --camera-index N to force one.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Colours (BGR)
# ---------------------------------------------------------------------------
GREEN  = (0,   220,  0)
YELLOW = (0,   200, 255)
RED    = (0,    0,  220)
WHITE  = (255, 255, 255)
BLACK  = (0,    0,   0)
CYAN   = (255, 200,   0)
ORANGE = (0,   140, 255)


def _text(img, msg, pos, color=WHITE, scale=0.7, thickness=2):
    cv2.putText(img, msg, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, BLACK, thickness + 2)
    cv2.putText(img, msg, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def draw_calibration(frame, result: DetectionResult):
    h, w = frame.shape[:2]
    pct  = result.calibration_progress

    # Dim overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

    # Title
    _text(frame, "CALIBRATING", (w // 2 - 130, h // 2 - 80),
          color=CYAN, scale=1.4, thickness=3)
    _text(frame, "Look straight ahead at the road",
          (w // 2 - 190, h // 2 - 40), color=WHITE, scale=0.75)

    # Progress bar
    bar_x, bar_y, bar_w, bar_h = 40, h // 2, w - 80, 30
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), WHITE, 2)
    filled = int(pct * bar_w)
    if filled > 0:
        cv2.rectangle(frame, (bar_x, bar_y),
                      (bar_x + filled, bar_y + bar_h), CYAN, -1)

    remaining = max(0.0, 10.0 * (1.0 - pct))
    _text(frame, f"{remaining:.0f}s remaining",
          (w // 2 - 60, h // 2 + 55), color=WHITE, scale=0.8)

    # FPS bottom-right
    _text(frame, f"{result.fps:.0f} FPS",
          (w - 90, h - 15), color=WHITE, scale=0.6, thickness=1)


def draw_detection(frame, result: DetectionResult):
    h, w = frame.shape[:2]

    # --- Alert banner (full-width, top) ---
    if result.alert:
        color = RED if result.alert_type == "DISTRACTED" else ORANGE
        cv2.rectangle(frame, (0, 0), (w, 70), color, -1)
        _text(frame, f"  {result.alert_type}!", (10, 50),
              color=WHITE, scale=1.6, thickness=3)
    else:
        cv2.rectangle(frame, (0, 0), (w, 50), (0, 80, 0), -1)
        _text(frame, "  SAFE", (10, 38), color=GREEN, scale=1.2, thickness=2)

    # --- Left panel: live signals ---
    panel_top = 80
    lh = 32   # line height

    def row(label, value, color=WHITE, y_offset=0):
        y = panel_top + y_offset
        _text(frame, label, (10, y), color=WHITE, scale=0.6, thickness=1)
        _text(frame, value, (160, y), color=color, scale=0.6, thickness=1)

    # EAR
    ear_color = RED if result.ear < 0.20 else (YELLOW if result.ear < 0.28 else GREEN)
    row("EAR:", f"{result.ear:.3f}", color=ear_color, y_offset=0)

    # Head pose
    head_color = RED if result.head_deviated else GREEN
    head_label = "DEVIATED" if result.head_deviated else "FORWARD"
    row("Head:", head_label, color=head_color, y_offset=lh)

    # Classifier
    cls_color = RED if result.classifier_class != 0 else GREEN
    row("Class:", f"{result.classifier_class_name} ({result.classifier_conf:.0%})",
        color=cls_color, y_offset=lh * 2)

    # PERCLOS
    pc_color = RED if result.perclos_pct > 30 else (YELLOW if result.perclos_pct > 15 else GREEN)
    row("PERCLOS:", f"{result.perclos_pct:.0f}%", color=pc_color, y_offset=lh * 3)

    # Face status
    face_color = GREEN if result.face_detected else RED
    face_label = "Detected" if result.face_detected else "NOT DETECTED"
    row("Face:", face_label, color=face_color, y_offset=lh * 4)

    # --- Bottom bar: FPS + reason ---
    cv2.rectangle(frame, (0, h - 40), (w, h), (30, 30, 30), -1)
    _text(frame, f"FPS: {result.fps:.0f}", (10, h - 12),
          color=WHITE, scale=0.6, thickness=1)
    if result.alert:
        _text(frame, result.reason, (100, h - 12),
              color=YELLOW, scale=0.55, thickness=1)

    # Press R hint (bottom right)
    _text(frame, "R=recal  Q=quit", (w - 175, h - 12),
          color=(150, 150, 150), scale=0.5, thickness=1)


def main():
    # Windows consoles default to a legacy codepage (e.g. cp1252) that can't
    # encode characters like the arrows used in some pipeline log messages;
    # force UTF-8 stdout so those prints don't crash the demo mid-run.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="SafeDrive unified demo")
    parser.add_argument(
        "--model",
        default="ml-models/week3_finetuning/tflite_models/class_weights_model_91pct.tflite",
    )
    parser.add_argument("--cal",    default="calibration.json")
    parser.add_argument("--recal",  action="store_true",
                        help="Force recalibration even if calibration.json exists")
    parser.add_argument("--camera-index", type=int, default=None,
                        help="Force a specific camera device instead of auto-detecting")
    parser.add_argument("--list-cameras", action="store_true",
                        help="Print detected camera devices and exit")
    args = parser.parse_args()

    if args.list_cameras:
        names = _dshow_device_names()
        if names:
            for i, n in enumerate(names):
                print(f"{i}: {n}")
        else:
            print("[SafeDrive] Device names unavailable on this platform "
                  "(install pygrabber on Windows); try indices 0-4 with --camera-index.")
        return

    if args.recal and Path(args.cal).exists():
        os.remove(args.cal)
        print(f"[SafeDrive] Deleted {args.cal} — will recalibrate.")

    detector = SafeDriveDetector(model_path=args.model, calibration_path=args.cal)
    cap      = select_camera(explicit_index=args.camera_index)

    print("[SafeDrive] Running — press Q or ESC to quit, R to recalibrate.")

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break

        result = detector.process_frame(frame)

        if result.phase == "CALIBRATING":
            draw_calibration(frame, result)
        else:
            draw_detection(frame, result)

        cv2.imshow("SafeDrive AI", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):     # Q or ESC
            break
        if key == ord("r"):           # R — force recalibrate
            if Path(args.cal).exists():
                os.remove(args.cal)
            detector.close()
            detector = SafeDriveDetector(model_path=args.model, calibration_path=args.cal)
            print("[SafeDrive] Recalibrating...")

    cap.release()
    detector.close()
    cv2.destroyAllWindows()
    print("[SafeDrive] Demo ended.")


if __name__ == "__main__":
    main()
