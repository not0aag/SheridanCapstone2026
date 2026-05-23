"""
MULTIMODAL Distraction Detection System
Combines 3 detection methods for robust performance:
1. Image-based distraction classification (MobileNetV2)
2. Facial landmarks analysis (head pose, gaze direction)
3. Eye tracking (PERCLOS for drowsiness)

This approach is MORE ROBUST than single-modality detection!
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
MODEL_PATH = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"

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
EAR_THRESHOLD = 0.2          # Eye closure threshold
PERCLOS_DROWSY = 30.0        # Drowsy if >30% eye closure
HEAD_TURN_THRESHOLD = 0.15   # Head turned away threshold
GAZE_AWAY_THRESHOLD = 0.12   # Looking away threshold

class MultimodalDetector:
    def __init__(self, model_path):
        print("Initializing Multimodal Distraction Detector...")

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
        """Calculate PERCLOS (Percentage of Eye Closure)"""
        if len(self.ear_history) == 0:
            return 0
        closed_frames = sum(1 for ear in self.ear_history if ear < EAR_THRESHOLD)
        return (closed_frames / len(self.ear_history)) * 100

    def analyze_head_pose(self, landmarks):
        """Analyze head pose - is driver looking away?"""
        # Get nose tip position (normalized)
        nose = landmarks[NOSE_TIP]

        # Head turned left/right if nose x is far from center (0.5)
        horizontal_deviation = abs(nose.x - 0.5)

        # Head tilted up/down if nose y is far from center
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

        # Apply bias correction
        output_data[8] = output_data[8] * 0.7  # Suppress hair/makeup
        output_data[0] = min(output_data[0] * 1.15, 1.0)  # Boost safe driving
        output_data = output_data / np.sum(output_data)

        top_class = np.argmax(output_data)
        confidence = output_data[top_class] * 100

        return top_class, confidence, output_data

    def fuse_detections(self, img_class, img_conf, ear, perclos, looking_away):
        """
        MULTIMODAL FUSION: Combine all signals to determine final distraction state

        Priority logic:
        1. Drowsiness (PERCLOS) - HIGHEST PRIORITY
        2. Looking away (head pose) - HIGH PRIORITY
        3. Eye closure (momentary) - MEDIUM PRIORITY
        4. Image-based distraction - BASE SIGNAL
        """

        # CRITICAL: Drowsiness detected
        if perclos > PERCLOS_DROWSY and len(self.ear_history) >= self.window_size:
            return "DROWSY", 100.0, "Critical: Driver is drowsy"

        # HIGH PRIORITY: Eyes closed (not just drowsy pattern)
        if ear < EAR_THRESHOLD:
            return "EYES CLOSED", 95.0, "Warning: Eyes are closed"

        # HIGH PRIORITY: Looking away from road
        if looking_away:
            return "LOOKING AWAY", 90.0, "Warning: Not watching road"

        # Image-based detection with confidence thresholds
        if img_class == 0 and img_conf >= 50.0:
            return "SAFE", img_conf, CLASS_NAMES[img_class]
        elif img_class != 0 and img_class != 8 and img_conf >= 70.0:
            return "DISTRACTED", img_conf, CLASS_NAMES[img_class]
        elif img_class == 8 and img_conf >= 85.0:
            return "DISTRACTED", img_conf, CLASS_NAMES[img_class]
        else:
            # Low confidence - default to safe if no other indicators
            return "UNCERTAIN", img_conf, CLASS_NAMES[img_class]

    def draw_multimodal_overlay(self, frame, status, confidence, detail, ear, perclos, looking_away, fps):
        """Draw comprehensive overlay"""
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
        cv2.rectangle(frame, (0, 0), (width, 120), (0, 0, 0), -1)
        cv2.putText(frame, "SafeDrive AI - MULTIMODAL Detection", (20, 35),
                   cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)

        # Status
        cv2.rectangle(frame, (20, 50), (width - 20, 110), bg_color, -1)
        cv2.putText(frame, f"{status}: {detail}", (30, 85),
                   cv2.FONT_HERSHEY_DUPLEX, 1.0, color, 2)
        cv2.putText(frame, f"Confidence: {confidence:.1f}%", (30, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Metrics panel (bottom)
        panel_y = height - 150
        cv2.rectangle(frame, (0, panel_y), (width, height), (30, 30, 30), -1)

        # Eye metrics
        eye_status = "CLOSED" if ear < EAR_THRESHOLD else "OPEN"
        eye_color = (0, 0, 255) if ear < EAR_THRESHOLD else (0, 255, 0)
        cv2.putText(frame, f"Eye Status: {eye_status} (EAR: {ear:.3f})", (20, panel_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_color, 2)

        # PERCLOS
        perclos_color = (0, 0, 255) if perclos > PERCLOS_DROWSY else (0, 255, 0)
        cv2.putText(frame, f"PERCLOS: {perclos:.1f}% {'[DROWSY]' if perclos > PERCLOS_DROWSY else ''}",
                   (20, panel_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, perclos_color, 2)

        # Head pose
        pose_status = "AWAY" if looking_away else "FORWARD"
        pose_color = (0, 0, 255) if looking_away else (0, 255, 0)
        cv2.putText(frame, f"Gaze: {pose_status}", (20, panel_y + 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, pose_color, 2)

        # FPS
        cv2.putText(frame, f"FPS: {fps:.1f}", (width - 120, panel_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)

        # Modality indicators
        cv2.putText(frame, "Image + Face + Eyes", (width - 200, panel_y + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        return frame

    def run_webcam(self):
        """Run multimodal detection on webcam"""
        print("Starting multimodal detection...")
        print("\nCombining:")
        print("  ✓ Image-based distraction detection")
        print("  ✓ Facial landmark analysis")
        print("  ✓ Eye tracking (PERCLOS)")
        print("\nPress 'q' to quit\n")

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        fps_start = time.time()
        fps_count = 0
        fps = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

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

                # Update PERCLOS history
                self.ear_history.append(ear)
                if len(self.ear_history) > self.window_size:
                    self.ear_history.pop(0)
                perclos = self.calculate_perclos()

                # Analyze head pose
                looking_away, _, _ = self.analyze_head_pose(landmarks)

            # Get image-based prediction
            img_class, img_conf, _ = self.get_distraction_prediction(frame)

            # MULTIMODAL FUSION
            status, confidence, detail = self.fuse_detections(
                img_class, img_conf, ear, perclos, looking_away
            )

            # Calculate FPS
            fps_count += 1
            if time.time() - fps_start >= 1.0:
                fps = fps_count
                fps_count = 0
                fps_start = time.time()

            # Draw overlay
            frame = self.draw_multimodal_overlay(
                frame, status, confidence, detail, ear, perclos, looking_away, fps
            )

            # Display
            cv2.imshow('SafeDrive AI - Multimodal Detection', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

def main():
    print("\n" + "="*80)
    print("SafeDrive AI - MULTIMODAL Distraction Detection System")
    print("="*80)
    print("\nCombines 3 detection methods for maximum robustness:")
    print("  1. Image-based distraction classification")
    print("  2. Facial landmark analysis (head pose, gaze)")
    print("  3. Eye tracking (PERCLOS drowsiness detection)")
    print("\n" + "="*80 + "\n")

    detector = MultimodalDetector(MODEL_PATH)
    detector.run_webcam()

if __name__ == "__main__":
    main()
