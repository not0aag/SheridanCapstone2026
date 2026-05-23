"""
Test the model specifically on c0 (Safe Driving) class to diagnose the hair/makeup confusion issue
"""

import cv2
import numpy as np
import tensorflow as tf
from pathlib import Path
import random

MODEL_PATH = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"
TRAIN_DATA_PATH = "/Users/harry/datasets/safedrive/imgs/train"

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

# Load model
print("Loading model...")
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess_image(image):
    """Preprocess for MobileNetV2"""
    resized = cv2.resize(image, (224, 224))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = (rgb.astype(np.float32) / 127.5) - 1.0
    return np.expand_dims(normalized, axis=0)

def predict(image):
    """Get prediction"""
    input_data = preprocess_image(image)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])[0]
    return output_data

# Test on c0 (Safe Driving) images
print("\n" + "="*70)
print("Testing c0 (Safe Driving) Class - Looking for Hair/Makeup Confusion")
print("="*70 + "\n")

c0_folder = Path(TRAIN_DATA_PATH) / "c0"
c0_images = list(c0_folder.glob("*.jpg"))

# Test 50 random safe driving images
test_count = min(50, len(c0_images))
test_images = random.sample(c0_images, test_count)

confusion_matrix = {i: 0 for i in range(10)}
misclassified_as_c8 = []

for i, img_path in enumerate(test_images):
    image = cv2.imread(str(img_path))
    if image is None:
        continue

    output = predict(image)
    predicted_class = np.argmax(output)
    confidence = output[predicted_class] * 100

    confusion_matrix[predicted_class] += 1

    if predicted_class == 8:  # Hair and Makeup
        misclassified_as_c8.append({
            'path': img_path.name,
            'confidence': confidence,
            'c0_confidence': output[0] * 100,
            'c8_confidence': output[8] * 100
        })

    if (i + 1) % 10 == 0:
        print(f"Processed {i + 1}/{test_count} images...")

print("\n" + "="*70)
print("RESULTS")
print("="*70 + "\n")

print(f"Total Safe Driving (c0) images tested: {test_count}\n")
print("Predictions breakdown:")
for class_id, count in confusion_matrix.items():
    percentage = (count / test_count) * 100
    marker = " ⚠️ PROBLEM!" if class_id == 8 and count > 0 else ""
    print(f"  c{class_id} ({CLASS_NAMES[class_id]:30}): {count:3} images ({percentage:5.1f}%){marker}")

print(f"\n{'='*70}")
print(f"c0 (Safe Driving) Accuracy: {(confusion_matrix[0] / test_count) * 100:.1f}%")
print(f"Misclassified as c8 (Hair/Makeup): {confusion_matrix[8]} images ({(confusion_matrix[8] / test_count) * 100:.1f}%)")
print(f"{'='*70}\n")

if misclassified_as_c8:
    print("Examples of c0 images misclassified as c8 (Hair/Makeup):")
    print("-" * 70)
    for item in misclassified_as_c8[:10]:
        print(f"  {item['path']}")
        print(f"    c0 confidence: {item['c0_confidence']:5.1f}%  |  c8 confidence: {item['c8_confidence']:5.1f}%")
        print()
