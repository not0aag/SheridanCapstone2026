# SafeDrive AI - TFLite Model Integration Guide

## Model Information
- **File**: mobilenetv2_distraction_classifier.tflite
- **Size**: 2.40 MB
- **Accuracy**: 23.80%
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
import {bundleResourceIO} from '@tensorflow/tfjs-react-native';

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
const CLASS_NAMES = {
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
};

const detectedClass = CLASS_NAMES[classIndex];
const confidence = maxProb;

// Trigger alert if distraction detected
if (classIndex !== 0 && confidence > 0.70) {
  // Not safe driving - trigger alert
  triggerDistractionAlert(detectedClass, confidence);
}
```

## Performance Targets
- **FPS**: 25-30 FPS on OnePlus 11R 5G
- **Latency**: <40ms per inference
- **Battery**: <20% CPU usage
- **Accuracy**: ~24%

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
