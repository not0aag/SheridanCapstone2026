"""
SafeDrive AI - Professional Static Image Demo
For December 4, 2025 Presentation

Shows model accuracy on actual State Farm dataset images
Demonstrates 87.98% validation accuracy achievement
"""

import cv2
import tensorflow as tf
import numpy as np
import os
import time
from pathlib import Path

# Configuration
TFLITE_MODEL_PATH = "../week3_finetuning/tflite_models/improved_model_87pct.tflite"
DATASET_PATH = "/Users/harry/datasets/safedrive/imgs/train"
DISPLAY_TIME = 3000  # milliseconds per image

# Class names
CLASS_NAMES = {
    0: 'Safe Driving',
    1: 'Texting (Right Hand)',
    2: 'Phone Call (Right)',
    3: 'Texting (Left Hand)',
    4: 'Phone Call (Left)',
    5: 'Operating Radio',
    6: 'Drinking',
    7: 'Reaching Behind',
    8: 'Hair/Makeup',
    9: 'Talking to Passenger'
}

# Colors
GREEN = (0, 255, 0)
RED = (0, 0, 255)
YELLOW = (0, 255, 255)
WHITE = (255, 255, 255)
BLUE = (255, 165, 0)
GRAY = (200, 200, 200)

class StaticImageDemo:
    """Professional demo using State Farm dataset images"""

    def __init__(self):
        print("\n" + "="*70)
        print("SAFEDRIVE AI - PROFESSIONAL DEMO")
        print("="*70)
        print("\nLoading model...")

        # Load TFLite model
        self.interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        print("✓ Model loaded successfully")
        print(f"✓ Model accuracy: 87.98%")
        print("✓ Processes at 60 FPS")
        print("\n" + "="*70)

        self.correct_predictions = 0
        self.total_predictions = 0

    def preprocess_image(self, image):
        """MobileNetV2 preprocessing"""
        resized = cv2.resize(image, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        # MobileNetV2 expects [-1, 1] range
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)

    def predict(self, image):
        """Run prediction"""
        input_tensor = self.preprocess_image(image)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]['index'])

        probabilities = output[0]
        predicted_class = np.argmax(probabilities)
        confidence = probabilities[predicted_class]

        return predicted_class, confidence, probabilities

    def create_display(self, image, true_class, pred_class, confidence):
        """Create professional display with prediction overlay"""

        # Resize image for display
        display_img = cv2.resize(image, (800, 600))

        # Create info panel (right side)
        panel_width = 500
        panel = np.zeros((600, panel_width, 3), dtype=np.uint8)
        panel[:] = (40, 40, 40)  # Dark gray background

        # Title
        cv2.putText(panel, 'SafeDrive AI', (20, 60),
                   cv2.FONT_HERSHEY_DUPLEX, 1.5, YELLOW, 3)

        cv2.putText(panel, 'Distraction Detection System', (20, 95),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)

        # Divider line
        cv2.line(panel, (20, 110), (panel_width-20, 110), GRAY, 2)

        # Ground Truth
        y_pos = 160
        cv2.putText(panel, 'ACTUAL BEHAVIOR:', (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, GRAY, 2)

        cv2.putText(panel, CLASS_NAMES[true_class], (20, y_pos + 40),
                   cv2.FONT_HERSHEY_DUPLEX, 0.9, WHITE, 2)

        # Prediction
        y_pos += 120
        cv2.putText(panel, 'MODEL PREDICTION:', (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, GRAY, 2)

        pred_color = GREEN if pred_class == true_class else RED
        cv2.putText(panel, CLASS_NAMES[pred_class], (20, y_pos + 40),
                   cv2.FONT_HERSHEY_DUPLEX, 0.9, pred_color, 2)

        # Confidence bar
        y_pos += 100
        cv2.putText(panel, f'Confidence: {confidence:.1%}', (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)

        # Draw confidence bar
        bar_width = int(400 * confidence)
        cv2.rectangle(panel, (20, y_pos + 15), (20 + bar_width, y_pos + 35),
                     pred_color, -1)
        cv2.rectangle(panel, (20, y_pos + 15), (420, y_pos + 35),
                     GRAY, 2)

        # Result indicator
        y_pos += 80
        is_correct = (pred_class == true_class)
        result_text = "✓ CORRECT" if is_correct else "✗ INCORRECT"
        result_color = GREEN if is_correct else RED

        cv2.putText(panel, result_text, (20, y_pos),
                   cv2.FONT_HERSHEY_DUPLEX, 1.2, result_color, 3)

        # Statistics
        y_pos += 80
        cv2.line(panel, (20, y_pos - 20), (panel_width-20, y_pos - 20), GRAY, 1)

        cv2.putText(panel, 'SESSION STATS:', (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, GRAY, 1)

        session_acc = (self.correct_predictions / self.total_predictions * 100) if self.total_predictions > 0 else 0
        cv2.putText(panel, f'Samples: {self.total_predictions}', (20, y_pos + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
        cv2.putText(panel, f'Accuracy: {session_acc:.1f}%', (20, y_pos + 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)

        # Model info
        y_pos = 530
        cv2.putText(panel, 'Validation Accuracy: 87.98%', (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLUE, 1)
        cv2.putText(panel, 'Press SPACE=Next  Q=Quit', (20, y_pos + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, YELLOW, 1)

        # Combine image and panel
        combined = np.hstack([display_img, panel])

        return combined

    def run_demo(self, samples_per_class=3):
        """Run the demo with images from dataset"""

        print("\nStarting demo...")
        print(f"Showing {samples_per_class} samples from each of 10 classes")
        print(f"Total images: {samples_per_class * 10}")
        print("\nControls:")
        print("  SPACE - Next image")
        print("  Q     - Quit demo")
        print("\n" + "="*70 + "\n")

        # Collect images from each class
        for class_idx in range(10):
            class_dir = Path(DATASET_PATH) / f'c{class_idx}'

            if not class_dir.exists():
                print(f"Warning: Class directory not found: {class_dir}")
                continue

            img_files = sorted(list(class_dir.glob('*.jpg')))[:samples_per_class]

            for img_file in img_files:
                # Load image
                image = cv2.imread(str(img_file))
                if image is None:
                    continue

                # Predict
                pred_class, confidence, probabilities = self.predict(image)

                # Update statistics
                self.total_predictions += 1
                if pred_class == class_idx:
                    self.correct_predictions += 1

                # Create display
                display = self.create_display(image, class_idx, pred_class, confidence)

                # Show
                cv2.imshow('SafeDrive AI - Professional Demo', display)

                # Wait for key or timeout
                key = cv2.waitKey(DISPLAY_TIME)

                if key == ord('q'):
                    print("\n\nDemo stopped by user")
                    cv2.destroyAllWindows()
                    return
                elif key == ord(' '):
                    # Space bar - continue immediately
                    continue

        cv2.destroyAllWindows()

        # Final statistics
        print("\n" + "="*70)
        print("DEMO COMPLETE")
        print("="*70)
        print(f"\nTotal Samples: {self.total_predictions}")
        print(f"Correct Predictions: {self.correct_predictions}")
        print(f"Demo Accuracy: {self.correct_predictions/self.total_predictions*100:.2f}%")
        print(f"Validation Accuracy: 87.98%")
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    demo = StaticImageDemo()
    demo.run_demo(samples_per_class=3)  # 3 samples × 10 classes = 30 images
