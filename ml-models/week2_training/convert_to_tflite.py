"""
SafeDrive AI - TensorFlow Lite Model Conversion (CORRECTED)
Convert trained MobileNetV2 model to TFLite with Dynamic Range Quantization

Week 2 Task: H1-W2-5
Author: Harrison Daniel Dsouza
"""

import tensorflow as tf
import numpy as np
import os
import json
from pathlib import Path
import config
import dataset_loader

print("=" * 60)
print("SafeDrive AI - TFLite Model Conversion (CORRECTED)")
print("=" * 60)
print()

# ============================================================================
# STEP 1: Load the trained Keras model
# ============================================================================

MODEL_PATH = './models/mobilenetv2_final.h5'
OUTPUT_DIR = './tflite_models'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Loading trained model from: {MODEL_PATH}")
model = tf.keras.models.load_model(MODEL_PATH)
print(f"✅ Model loaded successfully")
print(f"   Input shape: {model.input_shape}")
print(f"   Output shape: {model.output_shape}")
print()

# ============================================================================
# STEP 2: Convert to TFLite with Dynamic Range Quantization
# ============================================================================

print("Converting to TensorFlow Lite with Dynamic Range Quantization...")
print("This approach:")
print("  • Reduces model size by ~75% (weights only)")
print("  • Maintains accuracy (typically <1% loss)")
print("  • Keeps float32 input/output for compatibility")
print("  • Quantizes weights to int8 internally")
print()

# Create TFLite converter
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Enable dynamic range quantization (weights only)
# This is more robust than full integer quantization
converter.optimizations = [tf.lite.Optimize.DEFAULT]

print("Conversion settings:")
print(f"  • Optimization: Dynamic Range Quantization (weights only)")
print(f"  • Input type: float32 (0-1 range)")
print(f"  • Output type: float32 (probabilities)")
print()

# Perform conversion
try:
    tflite_model = converter.convert()
    print("✅ Conversion successful!")
except Exception as e:
    print(f"❌ Conversion failed: {e}")
    exit(1)

print()

# ============================================================================
# STEP 3: Save TFLite model
# ============================================================================

tflite_model_path = os.path.join(
    OUTPUT_DIR, 'mobilenetv2_distraction_classifier.tflite')
with open(tflite_model_path, 'wb') as f:
    f.write(tflite_model)

# Get file sizes for comparison
keras_size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
tflite_size_mb = os.path.getsize(tflite_model_path) / (1024 * 1024)
size_reduction = ((keras_size_mb - tflite_size_mb) / keras_size_mb) * 100

print("Model saved:")
print(f"  • TFLite model: {tflite_model_path}")
print(f"  • Keras model size: {keras_size_mb:.2f} MB")
print(f"  • TFLite model size: {tflite_size_mb:.2f} MB")
print(f"  • Size reduction: {size_reduction:.1f}%")
print()

# ============================================================================
# STEP 4: Validate TFLite model accuracy
# ============================================================================

print("Validating TFLite model accuracy...")
print()

# Load validation dataset
_, val_dataset, _, _ = dataset_loader.prepare_datasets()

# Load TFLite model for inference
interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("TFLite Model Details:")
print(f"  • Input shape: {input_details[0]['shape']}")
print(f"  • Input dtype: {input_details[0]['dtype']}")
print(f"  • Output shape: {output_details[0]['shape']}")
print(f"  • Output dtype: {output_details[0]['dtype']}")
print()

# Test on validation samples
print("Testing on validation samples (this may take 2-3 minutes)...")
num_test_samples = 500  # Test more samples for accurate measurement
correct_predictions = 0
total_samples = 0

for images, labels in val_dataset.take(num_test_samples // config.BATCH_SIZE + 1):
    for i in range(len(images)):
        if total_samples >= num_test_samples:
            break

        # Prepare input (already float32 in [0, 1] range)
        input_data = images[i:i+1].numpy()

        # Run inference
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        # Get output
        output_data = interpreter.get_tensor(output_details[0]['index'])

        # Get prediction
        predicted_class = np.argmax(output_data[0])
        true_class = np.argmax(labels[i].numpy())

        if predicted_class == true_class:
            correct_predictions += 1
        total_samples += 1

    if total_samples >= num_test_samples:
        break

tflite_accuracy = (correct_predictions / total_samples) * 100

print(
    f"TFLite Model Accuracy: {tflite_accuracy:.2f}% ({correct_predictions}/{total_samples} correct)")
print()

# Compare with original Keras model accuracy (from training)
print("Comparing with original Keras model...")
print(f"  • Original validation accuracy: 84.88% (from training)")
print(f"  • TFLite validation accuracy: {tflite_accuracy:.2f}%")

accuracy_difference = abs(84.88 - tflite_accuracy)
if accuracy_difference <= 3.0:
    print(
        f"  • Accuracy difference: {accuracy_difference:.2f}% ✅ (Within acceptable 3% threshold)")
    status = "PASS"
else:
    print(
        f"  • Accuracy difference: {accuracy_difference:.2f}% ⚠️ (Exceeds 3% threshold)")
    status = "WARNING"

print()

# ============================================================================
# STEP 5: Create model metadata file
# ============================================================================

print("Creating model metadata file...")

# Class labels mapping
class_labels = {
    'c0': 'Safe driving',
    'c1': 'Texting - right hand',
    'c2': 'Talking on phone - right hand',
    'c3': 'Texting - left hand',
    'c4': 'Talking on phone - left hand',
    'c5': 'Operating radio',
    'c6': 'Drinking',
    'c7': 'Reaching behind',
    'c8': 'Hair and makeup',
    'c9': 'Talking to passenger'
}

metadata = {
    'model_name': 'SafeDrive AI Distraction Classifier',
    'model_version': '1.0.0',
    'model_architecture': 'MobileNetV2',
    'input_shape': [int(x) for x in input_details[0]['shape']],
    'input_dtype': str(input_details[0]['dtype']),
    'output_shape': [int(x) for x in output_details[0]['shape']],
    'output_dtype': str(output_details[0]['dtype']),
    'num_classes': 10,
    'class_labels': class_labels,
    'preprocessing': {
        'resize': '224x224',
        'normalization': 'Divide by 255.0 to get [0, 1] range',
        'color_space': 'RGB'
    },
    'quantization': {
        'type': 'Dynamic Range (Float16)',
        'input_range': [0.0, 1.0],
        'output_range': [0.0, 1.0],
        'weights': 'int8',
        'activations': 'float32'
    },
    'performance': {
        'keras_model_size_mb': round(float(keras_size_mb), 2),
        'tflite_model_size_mb': round(float(tflite_size_mb), 2),
        'size_reduction_percent': round(float(size_reduction), 1),
        'tflite_accuracy_percent': round(float(tflite_accuracy), 2),
        'accuracy_difference_percent': round(float(accuracy_difference), 2),
        'validation_status': status
    },
    'training_info': {
        'dataset': 'State Farm Distracted Driver Detection',
        'training_samples': 17779,
        'validation_samples': 4645,
        'epochs': 30,
        'final_accuracy': 84.88
    }
}

metadata_path = os.path.join(OUTPUT_DIR, 'model_metadata.json')
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"✅ Metadata saved to: {metadata_path}")
print()

# ============================================================================
# STEP 6: Create integration guide for Sukh
# ============================================================================

integration_guide = f"""# SafeDrive AI - TFLite Model Integration Guide

## Model Information
- **File**: mobilenetv2_distraction_classifier.tflite
- **Size**: {tflite_size_mb:.2f} MB
- **Accuracy**: {tflite_accuracy:.2f}%
- **Input**: 224x224x3 RGB image (float32, range 0-1)
- **Output**: 10 class probabilities (float32, range 0-1)

## Android Integration (React Native)

### 1. Install TensorFlow Lite
```bash
npm install @tensorflow/tfjs @tensorflow/tfjs-react-native
npm install @react-native-community/async-storage
```

### 2. Load Model
```javascript
import * as tf from '@tensorflow/tfjs';
import '@tensorflow/tfjs-react-native';
import {{bundleResourceIO}} from '@tensorflow/tfjs-react-native';

// Wait for TF to be ready
await tf.ready();

// Load the TFLite model
const modelJson = require('./assets/model.json');
const modelWeights = require('./assets/weights.bin');
const model = await tf.loadGraphModel(bundleResourceIO(modelJson, modelWeights));
```

### 3. Preprocess Image
```javascript
// Convert camera frame to tensor
const imageTensor = tf.browser.fromPixels(imageData)
  .resizeNearestNeighbor([224, 224])  // Resize to 224x224
  .toFloat()                          // Convert to float32
  .div(255.0)                         // Normalize to [0, 1]
  .expandDims(0);                     // Add batch dimension
```

### 4. Run Inference
```javascript
const predictions = await model.predict(imageTensor);
const probabilities = await predictions.data();

// Get top prediction
const maxProb = Math.max(...probabilities);
const classIndex = probabilities.indexOf(maxProb);

// Clean up tensors to prevent memory leaks
imageTensor.dispose();
predictions.dispose();
```

### 5. Class Mapping
```javascript
const CLASS_NAMES = {{
  0: 'Safe driving',
  1: 'Texting - right hand',
  2: 'Talking on phone - right hand',
  3: 'Texting - left hand',
  4: 'Talking on phone - left hand',
  5: 'Operating radio',
  6: 'Drinking',
  7: 'Reaching behind',
  8: 'Hair and makeup',
  9: 'Talking to passenger'
}};

const detectedClass = CLASS_NAMES[classIndex];
const confidence = maxProb;

// Trigger alert if distraction detected
if (classIndex !== 0 && confidence > 0.70) {{
  // Not safe driving - trigger alert
  triggerDistractionAlert(detectedClass, confidence);
}}
```

## Performance Targets
- **FPS**: 25-30 FPS on OnePlus 11R 5G
- **Latency**: <40ms per inference
- **Battery**: <20% CPU usage
- **Accuracy**: ~{tflite_accuracy:.0f}%

## Testing Checklist
- [ ] Model loads successfully
- [ ] Inference runs at target FPS (25-30)
- [ ] Predictions are accurate (test with known images)
- [ ] Confidence scores are reasonable (0-1 range)
- [ ] Battery drain is acceptable
- [ ] No memory leaks during extended use
- [ ] Tensor disposal working correctly

## Troubleshooting

### Memory Leaks
Always dispose tensors after use:
```javascript
imageTensor.dispose();
predictions.dispose();
```

### Low FPS
- Check if using GPU delegate
- Reduce input resolution if needed
- Profile with React Native performance monitor

### Incorrect Predictions
- Verify preprocessing (resize, normalize)
- Check image color space (RGB vs BGR)
- Test with State Farm dataset images

## Contact
Questions? Contact Harrison (ML Lead)
"""

integration_guide_path = os.path.join(OUTPUT_DIR, 'INTEGRATION_GUIDE.md')
with open(integration_guide_path, 'w') as f:
    f.write(integration_guide)

print(f"✅ Integration guide saved to: {integration_guide_path}")
print()

# ============================================================================
# STEP 7: Summary
# ============================================================================

print("=" * 60)
if status == "PASS":
    print("✅ TFLite Conversion Complete - READY FOR DEPLOYMENT!")
else:
    print("⚠️ TFLite Conversion Complete - CHECK ACCURACY")
print("=" * 60)
print()
print("Deliverables for Sukh (Mobile Dev):")
print(f"  1. {tflite_model_path}")
print(f"  2. {metadata_path}")
print(f"  3. {integration_guide_path}")
print()
print("Model Quality:")
print(f"  • Size reduction: {size_reduction:.1f}%")
print(f"  • Accuracy: {tflite_accuracy:.2f}% (original: 84.88%)")
print(f"  • Status: {status}")
print()
print("Next Steps:")
print("  • Task H1-W2-6: Test model on OnePlus 11R 5G")
print("  • Coordinate with Sukh for Android integration")
print("  • Document performance benchmarks")
print()
print("=" * 60)
