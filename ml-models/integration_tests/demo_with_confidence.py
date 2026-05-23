"""
SafeDrive AI Demo with Confidence Thresholds
- Only alerts on distractions when confidence is HIGH
- Better safe driving detection
"""

import cv2
import numpy as np
import tensorflow as tf
import sys
import time
from pathlib import Path

MODEL_PATH = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"

# CONFIDENCE THRESHOLDS
DISTRACTION_ALERT_THRESHOLD = 70.0  # Only alert if >= 70% confident
SAFE_DRIVING_THRESHOLD = 50.0       # Lower threshold for safe driving

CLASS_NAMES = {
    0: 'Safe Driving',
    1: 'Texting - Right Hand',
    2: 'Phone Call - Right Hand',
    3: 'Texting - Left Hand',
    4: 'Phone Call - Left Hand',
    5: 'Operating Radio',
    6: 'Drinking',
    7: 'Reaching Behind',
    8: 'Hair and Makeup',
    9: 'Talking to Passenger'
}

class SafeDriveDemo:
    def __init__(self, model_path):
        print("Loading model...")
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        print("✓ Model loaded\n")

    def preprocess_frame(self, frame):
        """Preprocess for MobileNetV2"""
        resized = cv2.resize(frame, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)

    def predict(self, frame):
        """Get prediction with confidence-based logic"""
        input_data = self.preprocess_frame(frame)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

        # Get top prediction
        top_class = np.argmax(output_data)
        top_confidence = output_data[top_class] * 100

        # Get c0 (safe driving) confidence
        c0_confidence = output_data[0] * 100

        # CONFIDENCE-BASED DECISION LOGIC:

        # 1. If c0 is above threshold, assume safe driving
        if c0_confidence >= SAFE_DRIVING_THRESHOLD:
            return 0, c0_confidence, "SAFE", output_data

        # 2. If distraction is detected with HIGH confidence, alert
        if top_class != 0 and top_confidence >= DISTRACTION_ALERT_THRESHOLD:
            return top_class, top_confidence, "ALERT", output_data

        # 3. If no strong signal, check if safe driving is close
        if c0_confidence >= 40.0:  # Even lower threshold
            return 0, c0_confidence, "SAFE (LOW CONF)", output_data

        # 4. Otherwise, show top prediction but mark as uncertain
        return top_class, top_confidence, "UNCERTAIN", output_data

    def draw_overlay(self, frame, pred_class, confidence, status, all_confidences, fps):
        """Draw professional overlay"""
        height, width = frame.shape[:2]

        # Status color coding
        if status == "SAFE" or status == "SAFE (LOW CONF)":
            status_color = (0, 255, 0)  # Green
            bg_color = (0, 100, 0)
        elif status == "ALERT":
            status_color = (0, 0, 255)  # Red
            bg_color = (0, 0, 100)
        else:  # UNCERTAIN
            status_color = (0, 165, 255)  # Orange
            bg_color = (50, 50, 50)

        # Top bar
        cv2.rectangle(frame, (0, 0), (width, 80), (0, 0, 0), -1)
        cv2.putText(frame, "SafeDrive AI - Distraction Detection", (20, 35),
                   cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (width - 150, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2)

        # Status banner
        banner_y = 100
        cv2.rectangle(frame, (0, banner_y), (width, banner_y + 100), bg_color, -1)

        # Status text
        cv2.putText(frame, status, (20, banner_y + 35),
                   cv2.FONT_HERSHEY_DUPLEX, 1.2, status_color, 2)

        # Behavior
        behavior_text = CLASS_NAMES[pred_class]
        cv2.putText(frame, behavior_text, (20, banner_y + 75),
                   cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 255, 255), 2)

        # Confidence
        conf_text = f"{confidence:.1f}%"
        cv2.putText(frame, conf_text, (width - 200, banner_y + 75),
                   cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 255, 255), 2)

        # Show top 3 predictions at bottom
        bottom_y = height - 150
        cv2.rectangle(frame, (0, bottom_y), (width, height), (30, 30, 30), -1)

        cv2.putText(frame, "Top Predictions:", (20, bottom_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)

        # Get top 3
        top3_idx = np.argsort(all_confidences)[-3:][::-1]
        y_pos = bottom_y + 60

        for i, idx in enumerate(top3_idx):
            conf = all_confidences[idx] * 100
            name = CLASS_NAMES[idx]

            # Color code
            if idx == 0:
                color = (0, 255, 0)  # Green for safe
            else:
                color = (100, 100, 255) if conf >= DISTRACTION_ALERT_THRESHOLD else (150, 150, 150)

            text = f"{i+1}. {name}: {conf:.1f}%"
            cv2.putText(frame, text, (20, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
            y_pos += 30

        # Threshold info
        cv2.putText(frame, f"Alert Threshold: {DISTRACTION_ALERT_THRESHOLD:.0f}% | Safe Threshold: {SAFE_DRIVING_THRESHOLD:.0f}%",
                   (width - 550, height - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        return frame

    def run_webcam(self):
        """Run with webcam"""
        print("Starting webcam...")
        print(f"\nSettings:")
        print(f"  Distraction Alert Threshold: >= {DISTRACTION_ALERT_THRESHOLD}%")
        print(f"  Safe Driving Threshold: >= {SAFE_DRIVING_THRESHOLD}%")
        print("\nPress 'q' to quit\n")

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        fps_start_time = time.time()
        fps_frame_count = 0
        fps = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Get prediction
            pred_class, confidence, status, all_conf = self.predict(frame)

            # Calculate FPS
            fps_frame_count += 1
            if time.time() - fps_start_time >= 1.0:
                fps = fps_frame_count
                fps_frame_count = 0
                fps_start_time = time.time()

            # Draw overlay
            frame = self.draw_overlay(frame, pred_class, confidence, status, all_conf, fps)

            # Display
            cv2.imshow('SafeDrive AI - Demo', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def run_video(self, video_path):
        """Run with video file"""
        print(f"Loading video: {video_path}")

        cap = cv2.VideoCapture(video_path)
        fps_orig = cap.get(cv2.CAP_PROP_FPS)

        print(f"Video FPS: {fps_orig:.1f}")
        print(f"\nSettings:")
        print(f"  Distraction Alert Threshold: >= {DISTRACTION_ALERT_THRESHOLD}%")
        print(f"  Safe Driving Threshold: >= {SAFE_DRIVING_THRESHOLD}%")
        print("\nPress 'q' to quit, SPACE to pause\n")

        fps_start_time = time.time()
        fps_frame_count = 0
        fps = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Get prediction
            pred_class, confidence, status, all_conf = self.predict(frame)

            # Calculate FPS
            fps_frame_count += 1
            if time.time() - fps_start_time >= 1.0:
                fps = fps_frame_count
                fps_frame_count = 0
                fps_start_time = time.time()

            # Draw overlay
            frame = self.draw_overlay(frame, pred_class, confidence, status, all_conf, fps)

            # Display
            cv2.imshow('SafeDrive AI - Video Analysis', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):
                cv2.waitKey(0)  # Pause

        cap.release()
        cv2.destroyAllWindows()

def main():
    print("\n" + "="*70)
    print("SafeDrive AI - Confidence-Based Distraction Detection")
    print("="*70 + "\n")

    demo = SafeDriveDemo(MODEL_PATH)

    if len(sys.argv) > 1:
        # Video file provided
        video_path = sys.argv[1]
        demo.run_video(video_path)
    else:
        # Use webcam
        demo.run_webcam()

if __name__ == "__main__":
    main()
