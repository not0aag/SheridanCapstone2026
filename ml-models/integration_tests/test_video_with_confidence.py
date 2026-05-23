"""
Test Video with Confidence Thresholds
- Only alerts on distractions when confidence is HIGH
- Better safe driving detection
- Shows real-time analysis on downloaded videos
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

class VideoAnalyzer:
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

    def draw_overlay(self, frame, pred_class, confidence, status, all_confidences, fps, frame_num, total_frames):
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
        cv2.putText(frame, "SafeDrive AI - Video Analysis", (20, 35),
                   cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2)

        # Progress bar
        progress = (frame_num / total_frames) if total_frames > 0 else 0
        progress_width = int((width - 40) * progress)
        cv2.rectangle(frame, (20, 50), (width - 20, 65), (50, 50, 50), -1)
        cv2.rectangle(frame, (20, 50), (20 + progress_width, 65), (100, 200, 100), -1)
        progress_text = f"{frame_num}/{total_frames} ({progress*100:.1f}%)"
        cv2.putText(frame, progress_text, (width - 200, 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

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

        # FPS and threshold info
        cv2.putText(frame, f"FPS: {fps:.1f} | Alert: {DISTRACTION_ALERT_THRESHOLD:.0f}% | Safe: {SAFE_DRIVING_THRESHOLD:.0f}%",
                   (20, height - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        return frame

    def analyze_video(self, video_path, save_output=False):
        """Analyze video file with confidence thresholds"""
        video_path = Path(video_path)

        if not video_path.exists():
            print(f"❌ Error: Video file not found: {video_path}")
            return

        print(f"Analyzing video: {video_path.name}")
        print(f"\nSettings:")
        print(f"  Distraction Alert Threshold: >= {DISTRACTION_ALERT_THRESHOLD}%")
        print(f"  Safe Driving Threshold: >= {SAFE_DRIVING_THRESHOLD}%")
        print(f"  Save output: {save_output}")
        print("\nPress 'q' to quit, SPACE to pause\n")

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            print(f"❌ Error: Could not open video file")
            return

        # Video properties
        fps_orig = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps_orig if fps_orig > 0 else 0

        print(f"Video info:")
        print(f"  Resolution: {width}x{height}")
        print(f"  FPS: {fps_orig:.1f}")
        print(f"  Total frames: {total_frames}")
        print(f"  Duration: {duration:.1f} seconds\n")

        # Output video writer
        out = None
        if save_output:
            output_path = video_path.parent / f"{video_path.stem}_analyzed.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps_orig, (width, height))
            print(f"Output will be saved to: {output_path}\n")

        # Statistics
        stats = {
            'safe': 0,
            'alert': 0,
            'uncertain': 0,
            'class_counts': {i: 0 for i in range(10)}
        }

        # Processing
        fps_start_time = time.time()
        fps_frame_count = 0
        fps = 0
        frame_num = 0

        print("Processing video...\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_num += 1

            # Get prediction
            pred_class, confidence, status, all_conf = self.predict(frame)

            # Update statistics
            if status == "SAFE" or status == "SAFE (LOW CONF)":
                stats['safe'] += 1
            elif status == "ALERT":
                stats['alert'] += 1
            else:
                stats['uncertain'] += 1

            stats['class_counts'][pred_class] += 1

            # Calculate FPS
            fps_frame_count += 1
            if time.time() - fps_start_time >= 1.0:
                fps = fps_frame_count
                fps_frame_count = 0
                fps_start_time = time.time()

            # Draw overlay
            frame_display = self.draw_overlay(frame, pred_class, confidence, status, all_conf, fps, frame_num, total_frames)

            # Display
            cv2.imshow('SafeDrive AI - Video Analysis', frame_display)

            # Save frame
            if save_output and out is not None:
                out.write(frame_display)

            # Controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n\nStopped by user")
                break
            elif key == ord(' '):
                cv2.waitKey(0)  # Pause

        # Cleanup
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()

        # Print statistics
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80 + "\n")

        print(f"Frames analyzed: {frame_num}/{total_frames}\n")

        print("Status Distribution:")
        safe_pct = (stats['safe'] / frame_num * 100) if frame_num > 0 else 0
        alert_pct = (stats['alert'] / frame_num * 100) if frame_num > 0 else 0
        uncertain_pct = (stats['uncertain'] / frame_num * 100) if frame_num > 0 else 0

        print(f"  ✓ SAFE:       {stats['safe']:5} frames ({safe_pct:5.1f}%)")
        print(f"  ⚠ ALERT:      {stats['alert']:5} frames ({alert_pct:5.1f}%)")
        print(f"  ? UNCERTAIN:  {stats['uncertain']:5} frames ({uncertain_pct:5.1f}%)\n")

        print("Behavior Distribution:")
        for class_id, count in sorted(stats['class_counts'].items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                pct = (count / frame_num * 100) if frame_num > 0 else 0
                marker = "✓" if class_id == 0 else "⚠"
                print(f"  {marker} c{class_id} ({CLASS_NAMES[class_id]:30}): {count:5} frames ({pct:5.1f}%)")

        if save_output:
            print(f"\n✓ Output saved to: {output_path}")

        print("\n" + "="*80)

def main():
    print("\n" + "="*80)
    print("SafeDrive AI - Video Analysis with Confidence Thresholds")
    print("="*80 + "\n")

    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python {Path(__file__).name} <video_path> [--save]")
        print(f"\nExample:")
        print(f"  python {Path(__file__).name} ~/Downloads/safe_driving.mp4")
        print(f"  python {Path(__file__).name} ~/Downloads/distracted.mp4 --save")
        sys.exit(1)

    video_path = sys.argv[1]
    save_output = '--save' in sys.argv

    analyzer = VideoAnalyzer(MODEL_PATH)
    analyzer.analyze_video(video_path, save_output=save_output)

if __name__ == "__main__":
    main()
