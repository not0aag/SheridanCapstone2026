"""
SafeDrive AI - TFLite Model Diagnostic Test (FINAL)
Direct test without config dependency
"""

import tensorflow as tf
import numpy as np
from pathlib import Path

print("=" * 60)
print("TFLite Model Diagnostic Test")
print("=" * 60)
print()

# ============================================================================
# Step 1: Set paths manually
# ============================================================================

print("STEP 1: Setting paths...")

# Based on your screenshot, the dataset is at:
DATASET_BASE = "/Users/harry/datasets/safedrive/imgs/train"
train_dir = Path(DATASET_BASE)

print(f"Dataset directory: {train_dir}")
print(f"Exists: {train_dir.exists()}")
print()

if not train_dir.exists():
    print("❌ Directory not found!")
    print("Please update DATASET_BASE in the script")
    exit(1)

# Find test images from each class
test_images = []
for class_idx in range(10):
    class_name = f'c{class_idx}'
    class_dir = train_dir / class_name

    if class_dir.exists():
        # Get first 3 images from this class
        images = list(class_dir.glob('*.jpg'))[:3]
        for img_path in images:
            test_images.append((str(img_path), class_idx))
        print(f"✅ Found {len(images)} images in {class_name}")
    else:
        print(f"❌ Class {class_name} not found")

print()
print(f"Total test images: {len(test_images)}")
print()

if len(test_images) == 0:
    print("❌ No test images found!")
    exit(1)

# ============================================================================
# Step 2: Load models
# ============================================================================

print("STEP 2: Loading models...")
print()

# Load Keras model
print("Loading Keras model...")
keras_model = tf.keras.models.load_model('./models/mobilenetv2_final.h5')
print("✅ Keras model loaded")
print()

# Load TFLite model
print("Loading TFLite model...")
tflite_path = './tflite_models/mobilenetv2_distraction_classifier.tflite'
interpreter = tf.lite.Interpreter(model_path=tflite_path)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("✅ TFLite model loaded")
print(f"   Input: {input_details[0]['shape']} ({input_details[0]['dtype']})")
print(
    f"   Output: {output_details[0]['shape']} ({output_details[0]['dtype']})")
print()

# ============================================================================
# Step 3: Test both models on same images
# ============================================================================

print("STEP 3: Testing models (showing first 10 results)...")
print()

keras_correct = 0
tflite_correct = 0
matches = 0

for i, (img_path, true_class) in enumerate(test_images):
    # Load image
    img = tf.keras.preprocessing.image.load_img(
        img_path, target_size=(224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = img_array / 255.0  # Normalize to [0, 1]
    img_batch = np.expand_dims(img_array, axis=0).astype(np.float32)

    # Keras prediction
    keras_pred = keras_model.predict(img_batch, verbose=0)[0]
    keras_class = np.argmax(keras_pred)
    keras_conf = keras_pred[keras_class]

    # TFLite prediction
    interpreter.set_tensor(input_details[0]['index'], img_batch)
    interpreter.invoke()
    tflite_pred = interpreter.get_tensor(output_details[0]['index'])[0]
    tflite_class = np.argmax(tflite_pred)
    tflite_conf = tflite_pred[tflite_class]

    # Check correctness
    keras_correct += (keras_class == true_class)
    tflite_correct += (tflite_class == true_class)
    matches += (keras_class == tflite_class)

    # Print first 10
    if i < 10:
        keras_match = "✅" if keras_class == true_class else "❌"
        tflite_match = "✅" if tflite_class == true_class else "❌"
        same = "✅ MATCH" if keras_class == tflite_class else "❌ DIFFER"

        img_name = Path(img_path).name
        print(f"Image {i+1}: {img_name}")
        print(f"  True class:     c{true_class}")
        print(
            f"  Keras:  c{keras_class} (conf: {keras_conf:.3f}) {keras_match}")
        print(
            f"  TFLite: c{tflite_class} (conf: {tflite_conf:.3f}) {tflite_match}")
        print(f"  Models: {same}")
        print()

print("=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)
print()
print(f"Total images tested: {len(test_images)}")
print()
print(
    f"Keras Accuracy:  {keras_correct}/{len(test_images)} = {(keras_correct/len(test_images)*100):.2f}%")
print(
    f"TFLite Accuracy: {tflite_correct}/{len(test_images)} = {(tflite_correct/len(test_images)*100):.2f}%")
print(
    f"Models Agree:    {matches}/{len(test_images)} = {(matches/len(test_images)*100):.2f}%")
print()

if matches == len(test_images):
    print("✅ PERFECT: Keras and TFLite predictions match 100%!")
    print("   The conversion is successful.")
    print("   The 23% accuracy issue is in the validation code, not the model.")
elif matches >= len(test_images) * 0.95:
    print("✅ EXCELLENT: Models match >95%")
    print("   Minor differences are acceptable for quantization.")
else:
    print("⚠️ WARNING: Models differ significantly")
    print("   There may be issues with the conversion.")

print()

# ============================================================================
# Step 4: Detailed comparison on one image
# ============================================================================

print("STEP 4: Detailed probability comparison (first image)...")
print()

img_path, true_class = test_images[0]
print(f"Image: {Path(img_path).name}")
print(f"True class: c{true_class}")
print()

# Load and predict
img = tf.keras.preprocessing.image.load_img(img_path, target_size=(224, 224))
img_array = tf.keras.preprocessing.image.img_to_array(img)
img_array = img_array / 255.0
img_batch = np.expand_dims(img_array, axis=0).astype(np.float32)

keras_pred = keras_model.predict(img_batch, verbose=0)[0]
interpreter.set_tensor(input_details[0]['index'], img_batch)
interpreter.invoke()
tflite_pred = interpreter.get_tensor(output_details[0]['index'])[0]

# Compare probabilities
print("Class-by-class probabilities:")
print("Class | Keras     | TFLite    | Difference")
print("------|-----------|-----------|------------")
for i in range(10):
    diff = abs(keras_pred[i] - tflite_pred[i])
    marker = " ⚠️" if diff > 0.05 else ""
    print(
        f"  c{i}  | {keras_pred[i]:.6f} | {tflite_pred[i]:.6f} | {diff:.6f}{marker}")

print()
max_diff = np.max(np.abs(keras_pred - tflite_pred))
avg_diff = np.mean(np.abs(keras_pred - tflite_pred))

print(f"Maximum difference: {max_diff:.6f}")
print(f"Average difference: {avg_diff:.6f}")
print()

if max_diff < 0.01:
    print("✅ Excellent: Differences < 1%")
elif max_diff < 0.05:
    print("✅ Good: Differences < 5%")
elif max_diff < 0.10:
    print("⚠️ Acceptable: Differences < 10%")
else:
    print("❌ Poor: Large differences detected")

print()
print("=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
