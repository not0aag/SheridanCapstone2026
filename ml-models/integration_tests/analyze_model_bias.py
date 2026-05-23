"""
Analyze if the model has a bias against c0 (Safe Driving)
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

print("\n" + "="*80)
print("ANALYZING MODEL BIAS - Testing All 10 Classes")
print("="*80 + "\n")

# Test 20 random images from EACH class
test_per_class = 20
results_by_class = {}

for true_class in range(10):
    print(f"Testing c{true_class} ({CLASS_NAMES[true_class]})...")

    class_folder = Path(TRAIN_DATA_PATH) / f"c{true_class}"
    images = list(class_folder.glob("*.jpg"))
    test_images = random.sample(images, min(test_per_class, len(images)))

    predictions = []
    confidences = []

    for img_path in test_images:
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        output = predict(image)
        pred_class = np.argmax(output)
        confidence = output[pred_class] * 100

        predictions.append(pred_class)
        confidences.append({
            'predicted': pred_class,
            'confidence': confidence,
            'true_class_conf': output[true_class] * 100
        })

    # Calculate accuracy
    correct = sum(1 for p in predictions if p == true_class)
    accuracy = (correct / len(predictions)) * 100

    # Average confidence when correct
    correct_confs = [c['confidence'] for c in confidences if c['predicted'] == true_class]
    avg_correct_conf = np.mean(correct_confs) if correct_confs else 0

    # Average true class confidence (even when wrong)
    avg_true_conf = np.mean([c['true_class_conf'] for c in confidences])

    results_by_class[true_class] = {
        'accuracy': accuracy,
        'correct_count': correct,
        'total': len(predictions),
        'avg_correct_confidence': avg_correct_conf,
        'avg_true_class_confidence': avg_true_conf,
        'predictions': predictions
    }

print("\n" + "="*80)
print("RESULTS BY CLASS")
print("="*80 + "\n")

print(f"{'Class':<5} {'Name':<30} {'Accuracy':<12} {'Avg Confidence':<18} {'True Class Conf':<18}")
print("-" * 80)

for class_id in range(10):
    r = results_by_class[class_id]
    marker = " ⚠️ LOW!" if r['accuracy'] < 80 else ""

    print(f"c{class_id:<4} {CLASS_NAMES[class_id]:<30} "
          f"{r['accuracy']:>6.1f}% ({r['correct_count']:>2}/{r['total']:<2}) "
          f"{r['avg_correct_confidence']:>9.1f}% "
          f"{r['avg_true_class_confidence']:>9.1f}%{marker}")

print("\n" + "="*80)

# Check if c0 has lower accuracy or confidence
c0_results = results_by_class[0]
avg_other_accuracy = np.mean([results_by_class[i]['accuracy'] for i in range(1, 10)])
avg_other_confidence = np.mean([results_by_class[i]['avg_correct_confidence'] for i in range(1, 10)])

print(f"\nc0 (Safe Driving) Accuracy:      {c0_results['accuracy']:.1f}%")
print(f"Other Classes Average Accuracy:  {avg_other_accuracy:.1f}%")

if c0_results['accuracy'] < avg_other_accuracy - 10:
    print(f"\n⚠️  PROBLEM: c0 accuracy is {avg_other_accuracy - c0_results['accuracy']:.1f}% LOWER than other classes!")
    print(f"   The model has a bias AGAINST detecting safe driving!\n")

    # Show what c0 is being confused with
    print("c0 images are being misclassified as:")
    confusion = {}
    for pred in c0_results['predictions']:
        if pred != 0:
            confusion[pred] = confusion.get(pred, 0) + 1

    for pred_class, count in sorted(confusion.items(), key=lambda x: x[1], reverse=True):
        print(f"  c{pred_class} ({CLASS_NAMES[pred_class]}): {count} images")

print("\n" + "="*80)
