"""
Test multi-angle model with external images (not from State Farm dataset)

USAGE:
1. Download driving images from internet and save to a folder
2. Run: python test_external_images.py <image_path_or_folder>

Example:
  python test_external_images.py ~/Downloads/driver_texting.jpg
  python test_external_images.py ~/Downloads/test_images/
"""

import cv2
import numpy as np
import tensorflow as tf
import sys
import os
from pathlib import Path

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

class ExternalImageTester:
    def __init__(self, model_path):
        """Load TFLite model"""
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        print(f"✓ Model loaded: {model_path}\n")

    def preprocess_image(self, image):
        """Preprocess image for MobileNetV2"""
        resized = cv2.resize(image, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        # MobileNetV2 expects [-1, 1] range
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)

    def predict(self, image):
        """Get predictions with confidence scores"""
        input_data = self.preprocess_image(image)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

        # Get top 3 predictions
        top3_idx = np.argsort(output_data)[-3:][::-1]

        results = []
        for idx in top3_idx:
            results.append({
                'class': CLASS_NAMES[idx],
                'confidence': output_data[idx] * 100,
                'class_id': idx
            })

        return results

    def test_image(self, image_path):
        """Test a single image"""
        print(f"Testing: {image_path}")

        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"  ✗ Failed to load image\n")
            return

        # Get predictions
        results = self.predict(image)

        # Display results
        print(f"  Top 3 Predictions:")
        for i, result in enumerate(results, 1):
            emoji = "✓" if result['class_id'] == 0 else "⚠"
            print(f"    {i}. {emoji} {result['class']}: {result['confidence']:.1f}%")

        # Overall confidence assessment
        top_conf = results[0]['confidence']
        if top_conf >= 70:
            print(f"  → High confidence prediction")
        elif top_conf >= 40:
            print(f"  → Moderate confidence")
        else:
            print(f"  → Low confidence (model uncertain)")

        print()

    def test_folder(self, folder_path):
        """Test all images in a folder"""
        folder = Path(folder_path)

        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        image_files = [f for f in folder.iterdir()
                      if f.suffix.lower() in image_extensions]

        if not image_files:
            print(f"No images found in {folder_path}")
            return

        print(f"Found {len(image_files)} images in {folder_path}\n")
        print("=" * 70)

        for image_file in sorted(image_files):
            self.test_image(image_file)
            print("-" * 70)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n⚠ Please provide an image path or folder")
        print("\nExample usage:")
        print("  python test_external_images.py ~/Downloads/driver.jpg")
        print("  python test_external_images.py ~/Downloads/test_images/")
        return

    # Model path
    model_path = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"

    if not os.path.exists(model_path):
        print(f"✗ Model not found: {model_path}")
        return

    # Initialize tester
    tester = ExternalImageTester(model_path)

    # Test path
    test_path = Path(sys.argv[1]).expanduser()

    if not test_path.exists():
        print(f"✗ Path not found: {test_path}")
        return

    print("=" * 70)
    print("TESTING MULTI-ANGLE MODEL WITH EXTERNAL IMAGES")
    print("=" * 70)
    print()

    if test_path.is_file():
        tester.test_image(test_path)
    elif test_path.is_dir():
        tester.test_folder(test_path)
    else:
        print(f"✗ Invalid path: {test_path}")

    print("\n" + "=" * 70)
    print("Testing complete!")
    print("=" * 70)
    print()
    print("NOTE: This model was trained on State Farm dataset with specific:")
    print("  - Car interior backgrounds (dashboard, steering wheel)")
    print("  - Camera angles (windshield/dashboard mounted)")
    print("  - Lighting conditions")
    print()
    print("External images may show lower confidence if they differ significantly")
    print("from the training data. The multi-angle training helps with different")
    print("camera positions, but domain differences (car type, lighting, etc.)")
    print("can still affect accuracy.")

if __name__ == "__main__":
    main()
