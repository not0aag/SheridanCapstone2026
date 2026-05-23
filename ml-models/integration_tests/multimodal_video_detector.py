"""
MULTIMODAL Distraction Detection for Videos
Combines 3 detection methods:
1. Image-based distraction classification (MobileNetV2)
2. Facial landmarks analysis (head pose, gaze direction)
3. Eye tracking (PERCLOS for drowsiness)
"""

import cv2
import numpy as np
import tensorflow as tf
import mediapipe as mp
from scipy.spatial import distance as dist
import sys
import time
from pathlib import Path

# Model path
MODEL_PATH = "../week3_finetuning/tflite_models/class_weights_model_91pct.tflite"

# MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh

# Eye landmarks indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Nose tip for head pose
NOSE_TIP = 1

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
HEAD_TURN_THRESHOLD = 0.15
GAZE_AWAY_THRESHOLD = 0.12

class MultimodalVideoDetector:
    def __init__(self, model_path):
        print("Initializing Multimodal Video Detector...")

        # Load distraction detection model
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

        # History for PERCLOS
        self.ear_history = []
        self.window_size = 100

        print("✓ Model and FaceMesh initialized\n")

    def eye_aspect_ratio(self, landmarks, eye_indices):
        """Calculate Eye Aspect Ratio"""
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

    def analyze_head_pose(self, landmarks):
        """Analyze head pose"""
        nose = landmarks[NOSE_TIP]
        horizontal_deviation = abs(nose.x - 0.5)
        vertical_deviation = abs(nose.y - 0.5)
        is_looking_away = (horizontal_deviation > HEAD_TURN_THRESHOLD or
                          vertical_deviation > GAZE_AWAY_THRESHOLD)
        return is_looking_away, horizontal_deviation, vertical_deviation

    def preprocess_frame(self, frame):
        """Preprocess for MobileNetV2"""
        resized = cv2.resize(frame, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)

    def get_distraction_prediction(self, frame):
        """Get image-based distraction prediction"""
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
        """MULTIMODAL FUSION"""

        # CRITICAL: Drowsiness detected
        if perclos > PERCLOS_DROWSY and len(self.ear_history) >= self.window_size:
            return "DROWSY", 100.0, "Critical: Driver is drowsy"

        # HIGH PRIORITY: Eyes closed
        if ear < EAR_THRESHOLD:
            return "EYES CLOSED", 95.0, "Warning: Eyes are closed"

        # HIGH PRIORITY: Looking away
        if looking_away:
            return "LOOKING AWAY", 90.0, "Warning: Not watching road"

        # Image-based detection
        if img_class == 0 and img_conf >= 50.0:
            return "SAFE", img_conf, CLASS_NAMES[img_class]
        elif img_class != 0 and img_class != 8 and img_conf >= 70.0:
            return "DISTRACTED", img_conf, CLASS_NAMES[img_class]
        elif img_class == 8 and img_conf >= 85.0:
            return "DISTRACTED", img_conf, CLASS_NAMES[img_class]
        else:
            return "UNCERTAIN", img_conf, CLASS_NAMES[img_class]

    def draw_overlay(self, frame, status, confidence, detail, ear, perclos, looking_away, fps, frame_num, total_frames):
        """Draw overlay"""
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
        cv2.rectangle(frame, (0, 0), (width, 140), (0, 0, 0), -1)
        cv2.putText(frame, "SafeDrive AI - MULTIMODAL Detection", (20, 35),
                   cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2)

        # Progress
        progress = (frame_num / total_frames) if total_frames > 0 else 0
        progress_width = int((width - 40) * progress)
        cv2.rectangle(frame, (20, 50), (width - 20, 65), (50, 50, 50), -1)
        cv2.rectangle(frame, (20, 50), (20 + progress_width, 65), (100, 200, 100), -1)
        cv2.putText(frame, f"{frame_num}/{total_frames}", (width - 150, 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Status
        cv2.rectangle(frame, (20, 80), (width - 20, 130), bg_color, -1)
        cv2.putText(frame, f"{status}: {detail}", (30, 110),
                   cv2.FONT_HERSHEY_DUPLEX, 0.9, color, 2)

        # Metrics panel
        panel_y = height - 120
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

        # Head pose
        pose_status = "AWAY" if looking_away else "FORWARD"
        pose_color = (0, 0, 255) if looking_away else (0, 255, 0)
        cv2.putText(frame, f"Gaze: {pose_status}", (20, panel_y + 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, pose_color, 2)

        # FPS and confidence
        cv2.putText(frame, f"FPS: {fps:.1f}", (width - 350, panel_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)
        cv2.putText(frame, f"Conf: {confidence:.1f}%", (width - 350, panel_y + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
        cv2.putText(frame, "Image+Face+Eyes", (width - 350, panel_y + 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        return frame

    def analyze_video(self, video_path, save_output=False):
        """Analyze video with multimodal detection"""
        video_path = Path(video_path)

        if not video_path.exists():
            print(f"❌ Error: Video not found: {video_path}")
            return

        print(f"Analyzing: {video_path.name}")
        print(f"\nMultimodal Detection:")
        print(f"  ✓ Image classification")
        print(f"  ✓ Facial landmarks")
        print(f"  ✓ Eye tracking (PERCLOS)")
        print(f"\nSave output: {save_output}")
        print("\nPress 'q' to quit, SPACE to pause\n")

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            print("❌ Error: Could not open video")
            return

        # Video properties
        fps_orig = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps_orig if fps_orig > 0 else 0

        print(f"Video: {width}x{height}, {fps_orig:.1f} FPS, {total_frames} frames ({duration:.1f}s)\n")

        # Output writer
        out = None
        if save_output:
            output_path = video_path.parent / f"{video_path.stem}_multimodal.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps_orig, (width, height))
            print(f"Output: {output_path}\n")

        # Stats
        stats = {
            'safe': 0,
            'distracted': 0,
            'drowsy': 0,
            'eyes_closed': 0,
            'looking_away': 0,
            'uncertain': 0
        }

        # Processing
        fps_start = time.time()
        fps_count = 0
        fps = 0
        frame_num = 0

        print("Processing...\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_num += 1

            # Process with FaceMesh
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_results = self.face_mesh.process(frame_rgb)

            # Default values
            ear = 1.0
            perclos = 0.0
            looking_away = False

            # Analyze facial features
            if face_results.multi_face_landmarks:
                landmarks = face_results.multi_face_landmarks[0].landmark

                # Calculate EAR
                left_ear = self.eye_aspect_ratio(landmarks, LEFT_EYE)
                right_ear = self.eye_aspect_ratio(landmarks, RIGHT_EYE)
                ear = (left_ear + right_ear) / 2.0

                # Update PERCLOS
                self.ear_history.append(ear)
                if len(self.ear_history) > self.window_size:
                    self.ear_history.pop(0)
                perclos = self.calculate_perclos()

                # Head pose
                looking_away, _, _ = self.analyze_head_pose(landmarks)

            # Get image prediction
            img_class, img_conf, _ = self.get_distraction_prediction(frame)

            # FUSION
            status, confidence, detail = self.fuse_detections(
                img_class, img_conf, ear, perclos, looking_away
            )

            # Update stats
            if status == "SAFE":
                stats['safe'] += 1
            elif status == "DISTRACTED":
                stats['distracted'] += 1
            elif status == "DROWSY":
                stats['drowsy'] += 1
            elif status == "EYES CLOSED":
                stats['eyes_closed'] += 1
            elif status == "LOOKING AWAY":
                stats['looking_away'] += 1
            else:
                stats['uncertain'] += 1

            # Calculate FPS
            fps_count += 1
            if time.time() - fps_start >= 1.0:
                fps = fps_count
                fps_count = 0
                fps_start = time.time()

            # Draw overlay
            frame_display = self.draw_overlay(
                frame, status, confidence, detail, ear, perclos, looking_away, fps, frame_num, total_frames
            )

            # Display
            cv2.imshow('SafeDrive AI - Multimodal Video Analysis', frame_display)

            # Save
            if save_output and out is not None:
                out.write(frame_display)

            # Controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n\nStopped by user")
                break
            elif key == ord(' '):
                cv2.waitKey(0)

        # Cleanup
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()

        # Print stats
        print("\n" + "="*80)
        print("MULTIMODAL ANALYSIS COMPLETE")
        print("="*80 + "\n")

        print(f"Frames analyzed: {frame_num}/{total_frames}\n")

        print("Detection Summary:")
        for status, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                pct = (count / frame_num * 100) if frame_num > 0 else 0
                marker = "✓" if status == "safe" else "⚠"
                print(f"  {marker} {status.upper():15}: {count:5} frames ({pct:5.1f}%)")

        if save_output:
            print(f"\n✓ Saved to: {output_path}")

        print("\n" + "="*80)

def main():
    print("\n" + "="*80)
    print("SafeDrive AI - MULTIMODAL Video Analysis")
    print("="*80)
    print("\nCombines: Image + Facial Landmarks + Eye Tracking\n")

    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python {Path(__file__).name} <video_path> [--save]")
        print(f"\nExample:")
        print(f"  python {Path(__file__).name} ~/Downloads/safe_driving.mp4")
        print(f"  python {Path(__file__).name} ~/Downloads/distracted.mp4 --save")
        sys.exit(1)

    video_path = sys.argv[1]
    save_output = '--save' in sys.argv

    detector = MultimodalVideoDetector(MODEL_PATH)
    detector.analyze_video(video_path, save_output=save_output)

if __name__ == "__main__":
    main()
