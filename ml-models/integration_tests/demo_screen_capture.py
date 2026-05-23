"""
SafeDrive AI - Screen Capture Demo
Analyze YouTube videos or any screen content in real-time!

Perfect for demonstrations when you don't have a car!

USAGE:
    python demo_screen_capture.py

DEMO FLOW:
1. Run this script
2. Play a YouTube video of distracted driving
3. Model analyzes the screen in real-time
4. Perfect for December 4 presentation!

CONTROLS:
    Press 'q' - Quit
    Press 'r' - Reset statistics
    Press 'f' - Toggle fullscreen
"""

import cv2
import numpy as np
import tensorflow as tf
import time
from collections import deque
import mss
import mss.tools

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

class ScreenCaptureDemo:
    def __init__(self, model_path):
        """Initialize the demo system"""
        print("\n" + "="*70)
        print("          SafeDrive AI - SCREEN CAPTURE DEMO")
        print("="*70)

        print("\n[1/2] Loading Distraction Detection Model...")
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        print("      ✓ Model loaded (91.17% accuracy)\n")

        print("[2/2] Initializing Screen Capture...")
        self.sct = mss.mss()
        print("      ✓ Screen capture ready\n")

        # Smoothing
        self.prediction_history = deque(maxlen=10)

        # Statistics
        self.stats = {i: 0 for i in range(10)}
        self.frame_count = 0
        self.start_time = None

        print("="*70)

    def preprocess_frame(self, frame):
        """Preprocess frame for MobileNetV2"""
        resized = cv2.resize(frame, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)

    def predict(self, frame):
        """Get prediction with temporal smoothing"""
        input_data = self.preprocess_frame(frame)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

        pred_class = np.argmax(output_data)
        confidence = output_data[pred_class]

        self.prediction_history.append((pred_class, confidence))

        # Smooth predictions
        if len(self.prediction_history) >= 5:
            recent_preds = [p[0] for p in list(self.prediction_history)[-5:]]
            smoothed_class = max(set(recent_preds), key=recent_preds.count)
            smoothed_conf = np.mean([p[1] for p in list(self.prediction_history)[-5:] if p[0] == smoothed_class])
        else:
            smoothed_class = pred_class
            smoothed_conf = confidence

        return smoothed_class, smoothed_conf * 100

    def draw_overlay(self, frame, pred_class, confidence, fps):
        """Draw professional overlay"""
        h, w = frame.shape[:2]

        # Choose color
        if pred_class == 0:
            color = SAFE_COLOR
            border_color = SAFE_COLOR
        else:
            color = WARNING_COLOR
            border_color = DANGER_COLOR

        # Draw semi-transparent top panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 160), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        # Draw status border
        cv2.rectangle(frame, (10, 10), (w-10, 150), border_color, 3)

        # Title
        cv2.putText(frame, "SafeDrive AI - Live Analysis",
                   (20, 40), cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2)

        # Prediction
        text = CLASS_NAMES[pred_class]
        cv2.putText(frame, text, (20, 80),
                   cv2.FONT_HERSHEY_DUPLEX, 1.2, color, 2)

        # Confidence
        conf_text = f"Confidence: {confidence:.1f}%"
        cv2.putText(frame, conf_text, (20, 115),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Confidence bar
        bar_width = int((w - 240) * (confidence / 100))
        cv2.rectangle(frame, (220, 100), (220 + bar_width, 120), color, -1)
        cv2.rectangle(frame, (220, 100), (w - 20, 120), (100, 100, 100), 2)

        # FPS counter
        cv2.putText(frame, f"FPS: {fps:.1f}", (w - 150, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Instructions at bottom
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h-50), (w, h), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

        instructions = "Press 'q' to quit  |  'r' to reset stats  |  'f' for fullscreen"
        cv2.putText(frame, instructions, (20, h-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        return frame

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {i: 0 for i in range(10)}
        self.frame_count = 0
        self.start_time = time.time()
        print("\n✓ Statistics reset\n")

    def print_stats(self):
        """Print final statistics"""
        if self.frame_count == 0:
            return

        elapsed = time.time() - self.start_time

        print("\n" + "="*70)
        print("                    DEMO SESSION REPORT")
        print("="*70)
        print(f"\n  Session Duration: {int(elapsed)} seconds")
        print(f"  Average FPS: {self.frame_count / elapsed:.1f}")
        print(f"  Total Frames: {self.frame_count}")

        print(f"\n  DETECTION BREAKDOWN:")
        for class_id in sorted(self.stats.keys()):
            count = self.stats[class_id]
            if count > 0:
                percentage = (count / self.frame_count) * 100
                emoji = "✓" if class_id == 0 else "⚠"
                print(f"    {emoji} {CLASS_NAMES[class_id]:30s}: {count:5d} frames ({percentage:5.1f}%)")

        print("\n" + "="*70)

    def run(self):
        """Run the screen capture demo"""
        print("\n" + "="*70)
        print("                    SETUP INSTRUCTIONS")
        print("="*70)
        print("\n  1. Open YouTube and search for 'distracted driving'")
        print("  2. Play a video (suggestions below)")
        print("  3. This window will analyze whatever is on your screen!")
        print("\n  SUGGESTED YOUTUBE SEARCHES:")
        print("    - 'distracted driving dashcam'")
        print("    - 'texting while driving caught on camera'")
        print("    - 'driver using phone compilation'")
        print("\n  TIP: Position the YouTube video to fill most of your screen")
        print("\n" + "="*70)

        print("\n✓ Starting screen capture in 5 seconds...")
        print("  (Open your YouTube video now!)\n")
        time.sleep(5)
        print("✓ Capture LIVE!\n")

        self.start_time = time.time()
        fps = 0
        fps_counter = deque(maxlen=30)
        fullscreen = False

        # Get screen dimensions
        monitor = self.sct.monitors[1]  # Primary monitor

        window_name = 'SafeDrive AI - Screen Analysis (Press Q to quit)'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        try:
            while True:
                frame_start = time.time()

                # Capture screen
                screenshot = self.sct.grab(monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # Resize for better display (optional)
                display_height = 720
                aspect = frame.shape[1] / frame.shape[0]
                display_width = int(display_height * aspect)
                frame_display = cv2.resize(frame, (display_width, display_height))

                # Get prediction
                pred_class, confidence = self.predict(frame_display)

                # Update statistics
                self.stats[pred_class] += 1
                self.frame_count += 1

                # Draw overlay
                frame_display = self.draw_overlay(frame_display, pred_class, confidence, fps)

                # Display
                cv2.imshow(window_name, frame_display)

                # Calculate FPS
                frame_time = time.time() - frame_start
                fps_counter.append(1.0 / frame_time if frame_time > 0 else 0)
                fps = np.mean(fps_counter)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    print("\n✓ Demo stopped by user")
                    break
                elif key == ord('r'):
                    self.reset_stats()
                elif key == ord('f'):
                    fullscreen = not fullscreen
                    if fullscreen:
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                    else:
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

        except KeyboardInterrupt:
            print("\n\n✓ Demo stopped")

        finally:
            cv2.destroyAllWindows()
            self.print_stats()

def main():
    print(__doc__)

    # Model path
    model_path = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"

    import os
    if not os.path.exists(model_path):
        print(f"\n✗ Model not found: {model_path}")
        print("Please run from the integration_tests directory")
        return

    # Check if mss is installed
    try:
        import mss
    except ImportError:
        print("\n✗ Missing required package: mss")
        print("Install with: pip install mss")
        return

    # Initialize and run demo
    demo = ScreenCaptureDemo(model_path)
    demo.run()

if __name__ == "__main__":
    main()
