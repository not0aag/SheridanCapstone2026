# Solution: Making the Model Work with Different Camera Positions

## Problem Statement
Current model only works with the specific camera angle from State Farm dataset (passenger-side, dashboard level). We need it to work with common phone mount positions: AC vent, dashboard, windshield at various heights.

## Research-Backed Solutions

Based on 2024 research in domain adaptation and viewpoint-invariant learning, here are **three practical solutions**:

---

## Solution 1: Perspective Augmentation (RECOMMENDED - Fastest)

### What It Does
Add perspective transformations during training to simulate different camera angles.

### How It Works
- Takes existing training images
- Applies random perspective warps to simulate:
  - Higher camera positions (windshield mount)
  - Lower camera positions (dashboard mount)
  - Closer/farther distances
  - Slight rotation variations
- Model learns to recognize distractions from multiple viewpoints

### Implementation

```python
# Add to improved_dataset_loader.py

import cv2

def perspective_augmentation(image, label):
    """
    Simulate different camera mount positions through perspective transform
    """
    h, w = image.shape[:2]

    # Randomly choose augmentation strength
    strength = tf.random.uniform([], 0, 0.3)  # 0-30% variation

    # Define perspective transformation
    # Simulates camera at different heights and angles
    pts1 = np.float32([
        [0, 0],
        [w, 0],
        [0, h],
        [w, h]
    ])

    # Random offset to simulate different viewpoints
    offset_top = tf.random.uniform([], -strength * h, strength * h)
    offset_bottom = tf.random.uniform([], -strength * h, strength * h)
    offset_left = tf.random.uniform([], -strength * w, strength * w)
    offset_right = tf.random.uniform([], -strength * w, strength * w)

    pts2 = np.float32([
        [offset_left, offset_top],
        [w + offset_right, offset_top],
        [offset_left, h + offset_bottom],
        [w + offset_right, h + offset_bottom]
    ])

    # Apply perspective transformation
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    augmented = cv2.warpPerspective(image, matrix, (w, h))

    return augmented, label
```

### Training Changes
```python
# In improved_dataset_loader.py, add to augmentation pipeline:

def advanced_augment_image(image, label):
    """Enhanced augmentation with perspective transforms"""

    # Existing augmentations (rotation, flip, brightness, etc.)
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, max_delta=0.3)
    # ... other augmentations

    # NEW: Perspective augmentation (50% chance)
    if tf.random.uniform([]) > 0.5:
        image, label = perspective_augmentation(image, label)

    return image, label
```

### Expected Results
- **Pros:**
  - Quick to implement (~2 hours)
  - No new data needed
  - Should improve angle robustness by 15-25%

- **Cons:**
  - May reduce accuracy slightly (2-3%) due to harder training task
  - Still limited to angle variations similar to training data

### Retraining Required
- Time: 1-2 hours (50 epochs with new augmentation)
- Expected new accuracy: 82-85% (slightly lower but more robust)

---

## Solution 2: Multi-View Data Augmentation (BETTER - More Work)

### What It Does
Collect or generate additional images from different camera positions and add to training set.

### How It Works
**Option 2A: Synthetic Data Generation**
- Use 3D graphics or simulation to create driver images from multiple camera angles
- Generate 1000-2000 synthetic images per class from various viewpoints

**Option 2B: Real Data Collection**
- Record yourself doing all 10 actions from 3-4 different camera positions
- Add as supplementary training data (easier than full dataset)

**Option 2C: Perspective Transform Synthesis**
- Take existing training images
- Apply systematic perspective transformations
- Create 3-5 versions of each image (different simulated angles)
- This 3-5x increases dataset size

### Implementation

```python
# Create synthetic multi-angle dataset

import cv2
import numpy as np
from pathlib import Path

def generate_multi_angle_dataset(source_dir, output_dir, num_angles=4):
    """
    Generate multiple viewpoint versions of each training image
    """
    angles = [
        ('original', None),
        ('high', lambda img: simulate_higher_camera(img)),
        ('low', lambda img: simulate_lower_camera(img)),
        ('close', lambda img: simulate_closer_camera(img)),
    ]

    for angle_name, transform_fn in angles:
        angle_dir = Path(output_dir) / angle_name
        angle_dir.mkdir(parents=True, exist_ok=True)

        for class_idx in range(10):
            class_name = f'c{class_idx}'
            src_class_dir = Path(source_dir) / class_name
            dst_class_dir = angle_dir / class_name
            dst_class_dir.mkdir(exist_ok=True)

            for img_file in src_class_dir.glob('*.jpg'):
                img = cv2.imread(str(img_file))

                if transform_fn:
                    img = transform_fn(img)

                output_path = dst_class_dir / f'{angle_name}_{img_file.name}'
                cv2.imwrite(str(output_path), img)

    print(f"Generated {num_angles}x dataset with multiple camera angles")

def simulate_higher_camera(img):
    """Simulate camera mounted higher (windshield)"""
    h, w = img.shape[:2]
    pts1 = np.float32([[0,0], [w,0], [0,h], [w,h]])
    # Shift perspective as if looking down slightly
    pts2 = np.float32([[0,int(h*0.1)], [w,int(h*0.1)], [0,h], [w,h]])
    M = cv2.getPerspectiveTransform(pts1, pts2)
    return cv2.warpPerspective(img, M, (w, h))

def simulate_lower_camera(img):
    """Simulate camera mounted lower"""
    h, w = img.shape[:2]
    pts1 = np.float32([[0,0], [w,0], [0,h], [w,h]])
    # Shift perspective as if looking up slightly
    pts2 = np.float32([[0,0], [w,0], [0,int(h*0.9)], [w,int(h*0.9)]])
    M = cv2.getPerspectiveTransform(pts1, pts2)
    return cv2.warpPerspective(img, M, (w, h))

def simulate_closer_camera(img):
    """Simulate camera positioned closer"""
    h, w = img.shape[:2]
    # Zoom in by 20%
    crop = 0.1
    cropped = img[int(h*crop):int(h*(1-crop)), int(w*crop):int(w*(1-crop))]
    return cv2.resize(cropped, (w, h))
```

### Expected Results
- **Pros:**
  - Significantly better angle robustness (30-50% improvement)
  - Can target specific camera positions you want to support

- **Cons:**
  - Requires more training time (4-5x longer)
  - May need more epochs to converge
  - Risk of overfitting to synthetic data

### Retraining Required
- Time: 4-6 hours (need more epochs with 3-4x data)
- Expected new accuracy: 83-87% with much better angle robustness

---

## Solution 3: Domain Adaptation Layer (ADVANCED - Best Long-term)

### What It Does
Add a domain adaptation layer that learns to extract viewpoint-invariant features.

### How It Works
- Use Domain Adversarial Neural Network (DANN) approach
- Model learns features that work regardless of camera angle
- Gradient reversal layer makes features "angle-agnostic"

### Implementation

```python
# Add domain adaptation to model architecture

from tensorflow.keras import layers, Model
import tensorflow as tf

@tf.custom_gradient
def gradient_reversal(x):
    """Gradient Reversal Layer for domain adaptation"""
    def grad(dy):
        return -dy
    return x, grad

class GradientReversalLayer(layers.Layer):
    """Custom layer for domain adaptation"""
    def call(self, x):
        return gradient_reversal(x)

def create_domain_adaptive_model(num_classes=10, num_camera_positions=4):
    """
    Model with domain adaptation for camera angle robustness
    """
    # Base model (MobileNetV2)
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False

    inputs = layers.Input(shape=(224, 224, 3))

    # Feature extractor
    features = base_model(inputs, training=False)
    features = layers.GlobalAveragePooling2D()(features)

    # Main task: Distraction classification
    x = layers.Dropout(0.2)(features)
    x = layers.Dense(256, activation='relu')(x)
    main_output = layers.Dense(num_classes, activation='softmax', name='distraction')(x)

    # Domain classifier (learns to identify camera angle)
    # Gradient reversal makes features angle-invariant
    domain_features = GradientReversalLayer()(features)
    domain = layers.Dense(128, activation='relu')(domain_features)
    domain_output = layers.Dense(num_camera_positions, activation='softmax', name='camera_angle')(domain)

    model = Model(inputs=inputs, outputs=[main_output, domain_output])

    return model
```

### Training Changes
```python
# Requires labeled camera angles in dataset

def prepare_domain_adaptive_dataset():
    """
    Prepare dataset with camera angle labels
    """
    # Each image needs:
    # - Distraction label (c0-c9)
    # - Camera angle label (0=original, 1=high, 2=low, 3=close)

    # Return dataset with dual labels
    return train_dataset, val_dataset

# Training
model.compile(
    optimizer='adam',
    loss={
        'distraction': 'categorical_crossentropy',
        'camera_angle': 'categorical_crossentropy'
    },
    loss_weights={
        'distraction': 1.0,  # Main task
        'camera_angle': 0.3  # Auxiliary task (gradient reversed)
    },
    metrics=['accuracy']
)
```

### Expected Results
- **Pros:**
  - Best viewpoint robustness (50-70% improvement)
  - Learns truly angle-invariant features
  - State-of-the-art approach

- **Cons:**
  - Complex to implement (1-2 days)
  - Requires camera angle labels in data
  - More difficult to debug

### Retraining Required
- Time: 6-8 hours (complex architecture needs more tuning)
- Expected accuracy: 84-88% with excellent angle robustness

---

## Recommended Approach for December 4

### Quick Fix (This Week):
**Use Solution 1: Perspective Augmentation**

1. **Today:** Implement perspective augmentation in dataset loader (2 hours)
2. **Tonight:** Retrain model with new augmentation (1-2 hours overnight)
3. **Tomorrow:** Test with actual phone in car at different positions
4. **Document:** Which positions work, expected confidence ranges

### Code to Add Right Now:

```python
# File: ml-models/week3_finetuning/improved_dataset_loader_v2.py

import tensorflow as tf
import cv2
import numpy as np

def random_perspective_transform(image):
    """
    Apply random perspective transform to simulate different camera angles
    Simulates: higher mounts, lower mounts, closer/farther distances
    """
    # Convert to numpy for cv2 operations
    img_np = image.numpy()
    h, w = img_np.shape[:2]

    # Random perspective strength (0-25%)
    strength = np.random.uniform(0.05, 0.25)

    # Source points (original image corners)
    src_pts = np.float32([
        [0, 0],
        [w-1, 0],
        [0, h-1],
        [w-1, h-1]
    ])

    # Destination points (randomly shifted)
    dst_pts = np.float32([
        [np.random.uniform(0, strength*w), np.random.uniform(0, strength*h)],
        [w-1-np.random.uniform(0, strength*w), np.random.uniform(0, strength*h)],
        [np.random.uniform(0, strength*w), h-1-np.random.uniform(0, strength*h)],
        [w-1-np.random.uniform(0, strength*w), h-1-np.random.uniform(0, strength*h)]
    ])

    # Compute and apply perspective transformation
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(img_np, matrix, (w, h),
                                   borderMode=cv2.BORDER_REPLICATE)

    return tf.convert_to_tensor(warped, dtype=tf.float32)

def advanced_augment_image_v2(image, label):
    """
    Enhanced augmentation with perspective transforms for camera angle robustness
    """
    # Existing augmentations
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, max_delta=0.3)
    image = tf.image.random_contrast(image, lower=0.7, upper=1.3)

    # NEW: Perspective augmentation (60% of images)
    if tf.random.uniform([]) > 0.4:
        image = tf.py_function(
            random_perspective_transform,
            [image],
            tf.float32
        )
        image.set_shape([224, 224, 3])

    # Clip values
    image = tf.clip_by_value(image, -1.0, 1.0)

    return image, label
```

### Testing After Retraining:
1. Test in car with AC vent mount
2. Test in car with dashboard mount
3. Test in car with windshield mount (lower third)
4. Document: "Works with [positions], X% confidence"

---

## Long-term Solution (After Demo)

Combine all three approaches:
1. **Perspective augmentation** during training ✓
2. **Collect real data** from multiple angles (10-20 samples per class per angle)
3. **Domain adaptation** for production robustness

Expected final result:
- 85-90% accuracy across all common mount positions
- Production-ready system

---

## Summary: What to Do Now

**For December 4 Demo (Immediate):**
1. ✅ Add perspective augmentation to training (2 hours coding)
2. ✅ Retrain model overnight (automatic, 50 epochs)
3. ✅ Test in car tomorrow with 3 mount positions
4. ✅ Document which positions achieve 70%+ accuracy

**After Demo (Future Work):**
1. Collect multi-angle training data
2. Implement domain adaptation
3. Achieve 85%+ accuracy across all positions

This is honest, achievable, and shows good ML engineering!
