"""
MULTIMODAL with CALIBRATION
Learns what "forward" means from the first few frames
Then detects deviations from that baseline
"""

import cv2
import numpy as np
import tensorflow as tf
import mediapipe as mp
from scipy.spatial import distance as dist
import sys
import time
from pathlib import Path
from collections import deque

# Model path
MODEL_PATH = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"

# MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh

# Eye landmarks
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Head pose landmarks (for orientation)
NOSE_TIP = 1
LEFT_EYE_CORNER = 263
RIGHT_EYE_CORNER = 33
CHIN = 152
FOREHEAD = 10

# Distraction classes
CLASS_NAMES = {
    0: 'Safe Driving',
    1: 'Texting - Right',
    2: 'Phone - Right',
    3: 'Texting - Left',
    4: 'Phone - Left',
    5: 'Operating Radio',
    6: 'Drinking',
    7: 'Reaching Behind',
    8: 'Hair/Makeup',
    9: 'Talking Passenger'
}

# Thresholds
EAR_THRESHOLD = 0.2
PERCLOS_DROWSY = 30.0
HEAD_DEVIATION_THRESHOLD = 0.08  # Deviation from baseline
CALIBRATION_FRAMES = 30  # First 30 frames to establish baseline

class CalibratedMultimodalDetector:
    def __init__(self, model_path):
        print("Initializing Calibrated Multimodal Detector...")

        # Load model
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Initialize FaceMesh
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # PERCLOS history
        self.ear_history = []
        self.window_size = 100

        # CALIBRATION: Store baseline head pose
        self.baseline_nose_x = None
        self.baseline_nose_y = None
        self.baseline_eye_distance = None
        self.calibration_buffer = deque(maxlen=CALIBRATION_FRAMES)
        self.is_calibrated = False

        print("✓ Initialized with CALIBRATION mode")
        print("  First 30 frames will establish 'forward-looking' baseline\n")

    def eye_aspect_ratio(self, landmarks, eye_indices):
        """Calculate EAR"""
        eye = np.array([(landmarks[i].x, landmarks[i].y) for i in eye_indices])
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def calculate_perclos(self):
        """Calculate PERCLOS"""
        if len(self.ear_history) == 0:
            return 0
        closed_frames = sum(1 for ear in self.ear_history if ear < EAR_THRESHOLD)
        return (closed_frames / len(self.ear_history)) * 100

    def calibrate_head_pose(self, landmarks):
        """
        CALIBRATION: Learn what "forward" looks like
        Stores baseline nose position and eye distance
        """
        nose = landmarks[NOSE_TIP]
        left_eye = landmarks[LEFT_EYE_CORNER]
        right_eye = landmarks[RIGHT_EYE_CORNER]

        # Store this frame's measurements
        self.calibration_buffer.append({
            'nose_x': nose.x,
            'nose_y': nose.y,
            'eye_dist': dist.euclidean((left_eye.x, left_eye.y), (right_eye.x, right_eye.y))
        })

        # Once we have enough frames, calculate baseline
        if len(self.calibration_buffer) >= CALIBRATION_FRAMES and not self.is_calibrated:
            self.baseline_nose_x = np.median([f['nose_x'] for f in self.calibration_buffer])
            self.baseline_nose_y = np.median([f['nose_y'] for f in self.calibration_buffer])
            self.baseline_eye_distance = np.median([f['eye_dist'] for f in self.calibration_buffer])
            self.is_calibrated = True
            print(f"\n✓ CALIBRATION COMPLETE!")
            print(f"  Baseline nose position: ({self.baseline_nose_x:.3f}, {self.baseline_nose_y:.3f})")
            print(f"  This is now 'forward-looking' reference\n")

    def analyze_head_deviation(self, landmarks):
        """
        Analyze head pose RELATIVE to calibrated baseline
        Returns True if significantly deviated from "forward"
        """
        if not self.is_calibrated:
            return False, 0.0, 0.0  # Still calibrating

        nose = landmarks[NOSE_TIP]

        # Calculate deviation from baseline
        horizontal_dev = abs(nose.x - self.baseline_nose_x)
        vertical_dev = abs(nose.y - self.baseline_nose_y)

        # Check if looking away (deviated from baseline)
        is_looking_away = (horizontal_dev > HEAD_DEVIATION_THRESHOLD or
                          vertical_dev > HEAD_DEVIATION_THRESHOLD)

        return is_looking_away, horizontal_dev, vertical_dev

    def preprocess_frame(self, frame):
        """Preprocess for MobileNetV2"""
        resized = cv2.resize(frame, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)

    def get_distraction_prediction(self, frame):
        """Get image-based prediction"""
        input_data = self.preprocess_frame(frame)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

        # Bias correction
        output_data[8] = output_data[8] * 0.7
        output_data[0] = min(output_data[0] * 1.15, 1.0)
        output_data = output_data / np.sum(output_data)

        top_class = np.argmax(output_data)
        confidence = output_data[top_class] * 100

        return top_class, confidence, output_data

    def fuse_detections(self, img_class, img_conf, ear, perclos, looking_away):
        """MULTIMODAL FUSION with calibrated head pose"""

        if perclos > PERCLOS_DROWSY and len(self.ear_history) >= self.window_size:
            return "DROWSY", 100.0, "Critical: Driver is drowsy"

        if ear < EAR_THRESHOLD:
            return "EYES CLOSED", 95.0, "Warning: Eyes are closed"

        # Calibrated head pose detection
        if looking_away and self.is_calibrated:
            return "LOOKING AWAY", 90.0, "Warning: Not watching road (deviated from baseline)"

        # Image-based
        if img_class == 0 and img_conf >= 50.0:
            return "SAFE", img_conf, CLASS_NAMES[img_class]
        elif img_class != 0 and img_class != 8 and img_conf >= 70.0:
            return "DISTRACTED", img_conf, CLASS_NAMES[img_class]
        elif img_class == 8 and img_conf >= 85.0:
            return "DISTRACTED", img_conf, CLASS_NAMES[img_class]
        else:
            return "UNCERTAIN", img_conf, CLASS_NAMES[img_class]

    def draw_overlay(self, frame, status, confidence, detail, ear, perclos, looking_away,
                     h_dev, v_dev, fps, frame_num, total_frames):
        """Draw overlay with calibration info"""
        height, width = frame.shape[:2]

        # Status color
        if status == "SAFE":
            color = (0, 255, 0)
            bg_color = (0, 100, 0)
        elif status in ["DROWSY", "EYES CLOSED", "LOOKING AWAY", "DISTRACTED"]:
            color = (0, 0, 255)
            bg_color = (0, 0, 100)
        else:
            color = (0, 165, 255)
            bg_color = (50, 50, 50)

        # Top bar
        cv2.rectangle(frame, (0, 0), (width, 160), (0, 0, 0), -1)
        cv2.putText(frame, "SafeDrive AI - CALIBRATED Multimodal", (20, 35),
                   cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)

        # Calibration status
        if not self.is_calibrated:
            calib_text = f"CALIBRATING... {len(self.calibration_buffer)}/{CALIBRATION_FRAMES}"
            cv2.putText(frame, calib_text, (20, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        else:
            cv2.putText(frame, "✓ CALIBRATED (baseline locked)", (20, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        # Progress
        progress = (frame_num / total_frames) if total_frames > 0 else 0
        progress_width = int((width - 40) * progress)
        cv2.rectangle(frame, (20, 75), (width - 20, 90), (50, 50, 50), -1)
        cv2.rectangle(frame, (20, 75), (20 + progress_width, 90), (100, 200, 100), -1)

        # Status
        cv2.rectangle(frame, (20, 100), (width - 20, 150), bg_color, -1)
        cv2.putText(frame, f"{status}: {detail}", (30, 130),
                   cv2.FONT_HERSHEY_DUPLEX, 0.8, color, 2)

        # Metrics panel
        panel_y = height - 150
        cv2.rectangle(frame, (0, panel_y), (width, height), (30, 30, 30), -1)

        # Eye metrics
        eye_status = "CLOSED" if ear < EAR_THRESHOLD else "OPEN"
        eye_color = (0, 0, 255) if ear < EAR_THRESHOLD else (0, 255, 0)
        cv2.putText(frame, f"Eyes: {eye_status} (EAR: {ear:.3f})", (20, panel_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_color, 2)

        # PERCLOS
        perclos_color = (0, 0, 255) if perclos > PERCLOS_DROWSY else (0, 255, 0)
        cv2.putText(frame, f"PERCLOS: {perclos:.1f}%", (20, panel_y + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, perclos_color, 2)

        # Head deviation (calibrated)
        if self.is_calibrated:
            pose_status = "AWAY" if looking_away else "FORWARD"
            pose_color = (0, 0, 255) if looking_away else (0, 255, 0)
            cv2.putText(frame, f"Gaze: {pose_status} (H:{h_dev:.3f} V:{v_dev:.3f})",
                       (20, panel_y + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, pose_color, 2)
        else:
            cv2.putText(frame, f"Gaze: CALIBRATING...",
                       (20, panel_y + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)

        # Right side metrics
        cv2.putText(frame, f"FPS: {fps:.1f}", (width - 250, panel_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)
        cv2.putText(frame, f"Conf: {confidence:.1f}%", (width - 250, panel_y + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
        cv2.putText(frame, "Image+Face+Eyes", (width - 250, panel_y + 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        return frame

    def analyze_video(self, video_path, save_output=False):
        """Analyze video with calibrated detection"""
        video_path = Path(video_path)

        if not video_path.exists():
            print(f"❌ Error: Video not found: {video_path}")
            return

        print(f"\n{'='*80}")
        print(f"Analyzing: {video_path.name}")
        print(f"{'='*80}\n")
        print(f"CALIBRATION MODE:")
        print(f"  First {CALIBRATION_FRAMES} frames will learn 'forward-looking' baseline")
        print(f"  Then deviations from that baseline will trigger 'LOOKING AWAY'\n")
        print(f"Save output: {save_output}")
        print(f"\nPress 'q' to quit, SPACE to pause\n")

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            print("❌ Error: Could not open video")
            return

        # Video properties
        fps_orig = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Output writer
        out = None
        if save_output:
            output_path = video_path.parent / f"{video_path.stem}_calibrated.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps_orig, (width, height))

        # Stats
        stats = {'safe': 0, 'distracted': 0, 'drowsy': 0, 'eyes_closed': 0, 'looking_away': 0, 'uncertain': 0}

        fps_start = time.time()
        fps_count = 0
        fps = 0
        frame_num = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_num += 1

            # Process with FaceMesh
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_results = self.face_mesh.process(frame_rgb)

            ear = 1.0
            perclos = 0.0
            looking_away = False
            h_dev = 0.0
            v_dev = 0.0

            if face_results.multi_face_landmarks:
                landmarks = face_results.multi_face_landmarks[0].landmark

                # CALIBRATION phase
                if not self.is_calibrated:
                    self.calibrate_head_pose(landmarks)

                # Calculate EAR
                left_ear = self.eye_aspect_ratio(landmarks, LEFT_EYE)
                right_ear = self.eye_aspect_ratio(landmarks, RIGHT_EYE)
                ear = (left_ear + right_ear) / 2.0

                self.ear_history.append(ear)
                if len(self.ear_history) > self.window_size:
                    self.ear_history.pop(0)
                perclos = self.calculate_perclos()

                # Head deviation (calibrated)
                looking_away, h_dev, v_dev = self.analyze_head_deviation(landmarks)

            # Image prediction
            img_class, img_conf, _ = self.get_distraction_prediction(frame)

            # FUSION
            status, confidence, detail = self.fuse_detections(
                img_class, img_conf, ear, perclos, looking_away
            )

            # Update stats
            stats[status.lower().replace(' ', '_').replace('!', '')] = stats.get(
                status.lower().replace(' ', '_').replace('!', ''), 0) + 1

            # FPS
            fps_count += 1
            if time.time() - fps_start >= 1.0:
                fps = fps_count
                fps_count = 0
                fps_start = time.time()

            # Draw
            frame_display = self.draw_overlay(
                frame, status, confidence, detail, ear, perclos, looking_away,
                h_dev, v_dev, fps, frame_num, total_frames
            )

            cv2.imshow('SafeDrive AI - Calibrated Multimodal', frame_display)

            if save_output and out is not None:
                out.write(frame_display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):
                cv2.waitKey(0)

        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()

        # Print stats
        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*80}\n")
        print(f"Frames: {frame_num}/{total_frames}\n")
        print("Results:")
        for status, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                pct = (count / frame_num * 100) if frame_num > 0 else 0
                print(f"  {status.upper():15}: {count:5} frames ({pct:5.1f}%)")
        if save_output:
            print(f"\n✓ Saved: {output_path}")
        print(f"\n{'='*80}")

def main():
    print("\n" + "="*80)
    print("SafeDrive AI - CALIBRATED Multimodal Detection")
    print("="*80)
    print("\nLearns 'forward-looking' from first 30 frames")
    print("Then detects deviations (looking away)\n")

    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python {Path(__file__).name} <video_path> [--save]")
        sys.exit(1)

    detector = CalibratedMultimodalDetector(MODEL_PATH)
    detector.analyze_video(sys.argv[1], '--save' in sys.argv)

if __name__ == "__main__":
    main()
