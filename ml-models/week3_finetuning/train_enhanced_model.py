"""
Enhanced Model Training - Better Generalization for AI-Generated Videos
- Aggressive augmentation for better generalization
- Class balancing to fix c0 (safe driving) detection
- Brightness/contrast variations for different lighting
- Noise injection for robustness to AI artifacts
"""

import tensorflow as tf
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
import os

# Configuration
DATASET_PATH = "/Users/harry/datasets/safedrive/imgs/train"
BATCH_SIZE = 16
INITIAL_EPOCHS = 30
FINE_TUNE_EPOCHS = 20
TOTAL_EPOCHS = INITIAL_EPOCHS + FINE_TUNE_EPOCHS
IMG_SIZE = (224, 224)
NUM_CLASSES = 10
VALIDATION_SPLIT = 0.2
LEARNING_RATE_INITIAL = 0.001
LEARNING_RATE_FINE_TUNE = 0.0001

# Enhanced augmentation settings
AUGMENTATION_STRENGTH = 0.3  # Higher = more aggressive

# Class weights to fix c0 bias
CLASS_WEIGHTS = {
    0: 1.2,  # Boost safe driving
    1: 1.0,
    2: 1.0,
    3: 1.0,
    4: 1.0,
    5: 1.0,
    6: 1.0,
    7: 1.0,
    8: 0.9,  # Reduce hair/makeup slightly
    9: 1.1   # Boost talking to passenger (was low)
}

# Logging setup
class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', buffering=1)

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.terminal.flush()
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

log_file = f"enhanced_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = Logger(log_file)

print("\n" + "="*80)
print("ENHANCED MODEL TRAINING - Better Generalization")
print("="*80)
print(f"\nTraining started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Log file: {log_file}\n")

# Enhanced augmentation function
def enhanced_augmentation(image, label):
    """
    Aggressive augmentation for better generalization to AI-generated content
    """
    # Random brightness (simulate different lighting conditions)
    image = tf.image.random_brightness(image, max_delta=0.3)

    # Random contrast (helps with AI-generated videos)
    image = tf.image.random_contrast(image, lower=0.7, upper=1.3)

    # Random saturation (color variations)
    image = tf.image.random_saturation(image, lower=0.7, upper=1.3)

    # Random hue (small color shifts)
    image = tf.image.random_hue(image, max_delta=0.1)

    # Random horizontal flip (mirror view)
    image = tf.image.random_flip_left_right(image)

    # Random rotation removed (tf.contrib deprecated in TF 2.x)
    # Can add back with tfa.image.rotate if needed

    # Add random noise (helps with AI artifacts)
    noise = tf.random.normal(shape=tf.shape(image), mean=0.0, stddev=0.02)
    image = tf.add(image, noise)

    # Random zoom/crop (simulates different camera distances)
    if tf.random.uniform([]) > 0.5:
        # Zoom in slightly
        crop_size = tf.random.uniform([], 0.85, 1.0)
        h = tf.cast(tf.cast(IMG_SIZE[0], tf.float32) * crop_size, tf.int32)
        w = tf.cast(tf.cast(IMG_SIZE[1], tf.float32) * crop_size, tf.int32)
        image = tf.image.random_crop(image, [h, w, 3])
        image = tf.image.resize(image, IMG_SIZE)

    # Clip to valid range
    image = tf.clip_by_value(image, -1.0, 1.0)

    return image, label

# Load and preprocess dataset
print("="*80)
print("LOADING DATASET")
print("="*80 + "\n")

# Create dataset from directory
dataset = tf.keras.preprocessing.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='categorical'
)

val_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=VALIDATION_SPLIT,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='categorical'
)

# Count images per class
class_names = dataset.class_names
print("Class distribution:")
for i, class_name in enumerate(class_names):
    class_path = Path(DATASET_PATH) / class_name
    count = len(list(class_path.glob("*.jpg")))
    print(f"  {class_name}: {count} images (weight: {CLASS_WEIGHTS[i]})")

print(f"\nTotal training batches: {tf.data.experimental.cardinality(dataset).numpy()}")
print(f"Total validation batches: {tf.data.experimental.cardinality(val_dataset).numpy()}")

# MobileNetV2 preprocessing
def preprocess(image, label):
    """MobileNetV2 expects [-1, 1] range"""
    image = tf.cast(image, tf.float32)
    image = (image / 127.5) - 1.0
    return image, label

# Apply preprocessing and augmentation
train_dataset = dataset.map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
train_dataset = train_dataset.map(enhanced_augmentation, num_parallel_calls=tf.data.AUTOTUNE)
train_dataset = train_dataset.prefetch(tf.data.AUTOTUNE)

val_dataset = val_dataset.map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
val_dataset = val_dataset.prefetch(tf.data.AUTOTUNE)

print("\n✓ Dataset loaded and preprocessed with enhanced augmentation\n")

# Build model
print("="*80)
print("BUILDING MODEL")
print("="*80 + "\n")

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(*IMG_SIZE, 3),
    include_top=False,
    weights='imagenet'
)

# Freeze base model initially
base_model.trainable = False

# Build classification head
inputs = tf.keras.Input(shape=(*IMG_SIZE, 3))
x = base_model(inputs, training=False)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dropout(0.2)(x)
x = tf.keras.layers.Dense(256, activation='relu',
                          kernel_regularizer=tf.keras.regularizers.l2(0.00005))(x)
x = tf.keras.layers.Dropout(0.2)(x)
outputs = tf.keras.layers.Dense(NUM_CLASSES, activation='softmax')(x)

model = tf.keras.Model(inputs, outputs)

print(f"✓ Model built with MobileNetV2 base")
print(f"  Total parameters: {model.count_params():,}")
print(f"  Trainable parameters: {sum([tf.keras.backend.count_params(w) for w in model.trainable_weights]):,}\n")

# Compile model
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE_INITIAL),
    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
    metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')]
)

print("✓ Model compiled\n")

# Callbacks
os.makedirs('models', exist_ok=True)
callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        'models/best_model_enhanced.h5',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=8,
        restore_best_weights=True,
        verbose=1
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=4,
        min_lr=1e-7,
        verbose=1
    ),
    tf.keras.callbacks.CSVLogger(f'enhanced_training_history.csv')
]

# PHASE 1: Train classification head
print("\n" + "="*80)
print("PHASE 1: TRAINING CLASSIFICATION HEAD")
print("="*80 + "\n")

history_phase1 = model.fit(
    train_dataset,
    validation_data=val_dataset,
    epochs=INITIAL_EPOCHS,
    callbacks=callbacks,
    class_weight=CLASS_WEIGHTS,  # Apply class weights
    verbose=1
)

if history_phase1.history and 'val_accuracy' in history_phase1.history:
    best_val_acc = max(history_phase1.history['val_accuracy'])
    print(f"\n✓ Phase 1 Best Validation Accuracy: {best_val_acc:.2%}\n")

# PHASE 2: Fine-tune entire model
print("\n" + "="*80)
print("PHASE 2: FINE-TUNING ENTIRE MODEL")
print("="*80 + "\n")

# Unfreeze base model
base_model.trainable = True

# Recompile with lower learning rate
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE_FINE_TUNE),
    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.05),
    metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')]
)

print(f"✓ Base model unfrozen")
print(f"  Trainable parameters: {sum([tf.keras.backend.count_params(w) for w in model.trainable_weights]):,}\n")

history_phase2 = model.fit(
    train_dataset,
    validation_data=val_dataset,
    epochs=FINE_TUNE_EPOCHS,
    callbacks=callbacks,
    class_weight=CLASS_WEIGHTS,  # Apply class weights
    verbose=1
)

if history_phase2.history and 'val_accuracy' in history_phase2.history:
    best_val_acc = max(history_phase2.history['val_accuracy'])
    print(f"\n✓ Phase 2 Best Validation Accuracy: {best_val_acc:.2%}\n")

# Save final model
model.save('models/enhanced_model_final.h5')
print("✓ Final model saved to models/enhanced_model_final.h5\n")

# Convert to TFLite
print("="*80)
print("CONVERTING TO TFLITE")
print("="*80 + "\n")

best_model = tf.keras.models.load_model('models/best_model_enhanced.h5')
converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

os.makedirs('tflite_models', exist_ok=True)
tflite_path = 'tflite_models/enhanced_model.tflite'
with open(tflite_path, 'wb') as f:
    f.write(tflite_model)

tflite_size = os.path.getsize(tflite_path) / (1024 * 1024)
print(f"✓ TFLite model saved: {tflite_path}")
print(f"  Size: {tflite_size:.2f} MB\n")

# Evaluate final model
print("="*80)
print("FINAL EVALUATION")
print("="*80 + "\n")

results = best_model.evaluate(val_dataset, verbose=1)
print(f"\nFinal Validation Accuracy: {results[1]:.2%}")
print(f"Final Top-3 Accuracy: {results[2]:.2%}\n")

print("="*80)
print("TRAINING COMPLETE")
print("="*80)
print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Best model: models/best_model_enhanced.h5")
print(f"TFLite model: {tflite_path}")
print(f"Log file: {log_file}\n")
print("="*80)
