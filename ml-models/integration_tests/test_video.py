"""
Test multi-angle model with video files (no car needed!)

USAGE:
    python test_video.py <video_path>

EXAMPLE:
    python test_video.py ~/Downloads/driver_video.mp4
    python test_video.py https://www.youtube.com/watch?v=VIDEO_ID

This allows you to test the model with:
- Downloaded dashcam videos
- YouTube videos of drivers
- Stock footage of driving scenarios
"""

import cv2
import numpy as np
import tensorflow as tf
import sys
import time
from pathlib import Path
from collections import deque

# Class names
CLASS_NAMES = {
    0: '✓ SAFE DRIVING',
    1: '⚠ TEXTING (Right)',
    2: '⚠ PHONE CALL (Right)',
    3: '⚠ TEXTING (Left)',
    4: '⚠ PHONE CALL (Left)',
    5: '⚠ OPERATING RADIO',
    6: '⚠ DRINKING',
    7: '⚠ REACHING BEHIND',
    8: '⚠ HAIR/MAKEUP',
    9: '⚠ TALKING TO PASSENGER'
}

SAFE_COLOR = (0, 255, 0)      # Green
WARNING_COLOR = (0, 165, 255)  # Orange
DANGER_COLOR = (0, 0, 255)     # Red

class VideoTester:
    def __init__(self, model_path):
        """Load TFLite model"""
        print("Loading model...")
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Smoothing
        self.prediction_history = deque(maxlen=10)

        # Statistics
        self.stats = {i: 0 for i in range(10)}
        self.frame_count = 0

        print("✓ Model loaded\n")

    def preprocess_frame(self, frame):
        """Preprocess frame for MobileNetV2"""
        resized = cv2.resize(frame, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)

    def predict(self, frame):
        """Get prediction with smoothing"""
        input_data = self.preprocess_frame(frame)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

        # Add to history for smoothing
        pred_class = np.argmax(output_data)
        confidence = output_data[pred_class]

        self.prediction_history.append((pred_class, confidence))

        # Get most common prediction from recent frames
        if len(self.prediction_history) >= 5:
            recent_preds = [p[0] for p in list(self.prediction_history)[-5:]]
            smoothed_class = max(set(recent_preds), key=recent_preds.count)
            smoothed_conf = np.mean([p[1] for p in list(self.prediction_history)[-5:] if p[0] == smoothed_class])
        else:
            smoothed_class = pred_class
            smoothed_conf = confidence

        return smoothed_class, smoothed_conf * 100

    def draw_overlay(self, frame, pred_class, confidence):
        """Draw prediction overlay on frame"""
        h, w = frame.shape[:2]

        # Choose color
        color = SAFE_COLOR if pred_class == 0 else WARNING_COLOR

        # Draw semi-transparent overlay at top
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

        # Draw prediction text
        text = CLASS_NAMES[pred_class]
        cv2.putText(frame, text, (20, 50),
                   cv2.FONT_HERSHEY_DUPLEX, 1.2, color, 2)

        # Draw confidence bar
        conf_text = f"Confidence: {confidence:.1f}%"
        cv2.putText(frame, conf_text, (20, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        bar_width = int((w - 40) * (confidence / 100))
        cv2.rectangle(frame, (20, 100), (20 + bar_width, 110), color, -1)
        cv2.rectangle(frame, (20, 100), (w - 20, 110), (100, 100, 100), 2)

        return frame

    def process_video(self, video_path, show_display=True, save_output=False):
        """Process video file"""
        print(f"Opening video: {video_path}")

        # Open video
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            print("✗ Failed to open video")
            return

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"✓ Video loaded: {width}x{height} @ {fps} FPS, {total_frames} frames")
        print(f"Duration: {total_frames/fps:.1f} seconds\n")

        # Optional: Save output video
        out = None
        if save_output:
            output_path = Path(video_path).stem + "_analyzed.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            print(f"✓ Saving output to: {output_path}\n")

        print("Processing video...")
        print("Press 'q' to quit, 's' to show/hide display, SPACE to pause\n")
        print("=" * 70)

        frame_num = 0
        paused = False
        start_time = time.time()

        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_num += 1
                self.frame_count += 1

                # Get prediction
                pred_class, confidence = self.predict(frame)

                # Update statistics
                self.stats[pred_class] += 1

                # Draw overlay
                display_frame = self.draw_overlay(frame.copy(), pred_class, confidence)

                # Save to output video
                if out is not None:
                    out.write(display_frame)

                # Show progress
                if frame_num % 30 == 0:
                    progress = (frame_num / total_frames) * 100
                    print(f"Progress: {progress:.1f}% ({frame_num}/{total_frames} frames) - "
                          f"Current: {CLASS_NAMES[pred_class]}")

            # Display
            if show_display:
                cv2.imshow('SafeDrive AI - Video Analysis', display_frame)

                key = cv2.waitKey(1 if not paused else 0) & 0xFF

                if key == ord('q'):
                    print("\nStopped by user")
                    break
                elif key == ord('s'):
                    show_display = not show_display
                    cv2.destroyAllWindows()
                elif key == ord(' '):
                    paused = not paused
                    print("PAUSED" if paused else "RESUMED")

        # Cleanup
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()

        # Calculate statistics
        elapsed = time.time() - start_time

        print("\n" + "=" * 70)
        print("VIDEO ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"\nProcessing Time: {elapsed:.1f} seconds")
        print(f"Average FPS: {frame_num / elapsed:.1f}")
        print(f"Frames Analyzed: {frame_num}/{total_frames}")

        print("\n" + "=" * 70)
        print("DETECTION STATISTICS")
        print("=" * 70)

        for class_id in sorted(self.stats.keys()):
            count = self.stats[class_id]
            if count > 0:
                percentage = (count / frame_num) * 100
                emoji = "✓" if class_id == 0 else "⚠"
                print(f"{emoji} {CLASS_NAMES[class_id]:30s}: {count:5d} frames ({percentage:5.1f}%)")

        print("\n" + "=" * 70)

def download_youtube_video(url, output_path="temp_video.mp4"):
    """Download YouTube video using yt-dlp (if available)"""
    try:
        import subprocess
        print(f"Downloading video from: {url}")
        result = subprocess.run([
            'yt-dlp', '-f', 'best[height<=720]',
            '-o', output_path, url
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ Downloaded to: {output_path}\n")
            return output_path
        else:
            print("✗ Download failed. Please download manually and provide path.")
            return None
    except FileNotFoundError:
        print("✗ yt-dlp not found. Install with: pip install yt-dlp")
        print("Or download video manually and provide file path.")
        return None

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n⚠ Please provide a video path or URL")
        print("\nExamples:")
        print("  python test_video.py ~/Downloads/dashcam.mp4")
        print("  python test_video.py https://www.youtube.com/watch?v=VIDEO_ID")
        return

    # Model path
    model_path = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"

    if not Path(model_path).exists():
        print(f"✗ Model not found: {model_path}")
        return

    # Initialize tester
    tester = VideoTester(model_path)

    # Get video path
    video_input = sys.argv[1]

    # Check if it's a URL
    if video_input.startswith('http'):
        video_path = download_youtube_video(video_input)
        if video_path is None:
            return
    else:
        video_path = Path(video_input).expanduser()
        if not video_path.exists():
            print(f"✗ Video file not found: {video_path}")
            return

    # Process video
    save_output = '--save' in sys.argv
    show_display = '--no-display' not in sys.argv

    tester.process_video(video_path, show_display=show_display, save_output=save_output)

if __name__ == "__main__":
    main()
