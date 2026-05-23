"""
Train model on multi-angle dataset
This will make the model work with different camera positions:
- Webcam/eye level
- AC vent mounts
- Dashboard mounts
- Windshield mounts
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys
from datetime import datetime

# Setup logging to both file and stdout
class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', buffering=1)  # Line buffering

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.terminal.flush()
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

# Redirect output to log file
log_file = f"multiangle_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
sys.stdout = Logger(log_file)
sys.stderr = sys.stdout

print(f"Training started at {datetime.now()}")
print(f"Logs will be saved to: {log_file}\n")

# Configuration
MULTIANGLE_DATASET_PATH = '/Users/harry/datasets/safedrive/imgs/train_multiangle'
DRIVER_CSV_PATH = '/Users/harry/datasets/safedrive/driver_imgs_list.csv'

IMG_SIZE = (224, 224)
BATCH_SIZE = 16
INITIAL_EPOCHS = 25  # Reduced since we have 4x data
FINE_TUNE_EPOCHS = 15
TOTAL_EPOCHS = INITIAL_EPOCHS + FINE_TUNE_EPOCHS

INITIAL_LEARNING_RATE = 0.001
FINE_TUNE_LEARNING_RATE = 0.00005

DROPOUT_RATE = 0.2
L2_REGULARIZATION = 0.00005
LABEL_SMOOTHING = 0.05

NUM_CLASSES = 10
SEED = 42

print(f"""
{"="*70}
MULTI-ANGLE MODEL TRAINING
{"="*70}
Dataset: {MULTIANGLE_DATASET_PATH}
Total Epochs: {TOTAL_EPOCHS}
Batch Size: {BATCH_SIZE}
{"="*70}
""")

def load_multiangle_dataset():
    """
    Load dataset with all camera angle variants
    """
    print("\nLoading multi-angle dataset...")

    df = pd.read_csv(DRIVER_CSV_PATH)

    # Split by driver (same as before)
    unique_drivers = df['subject'].unique()
    np.random.seed(SEED)
    np.random.shuffle(unique_drivers)

    n_train = int(len(unique_drivers) * 0.77)
    train_drivers = unique_drivers[:n_train]
    val_drivers = unique_drivers[n_train:]

    train_df = df[df['subject'].isin(train_drivers)]
    val_df = df[df['subject'].isin(val_drivers)]

    print(f"Train drivers: {len(train_drivers)}")
    print(f"Val drivers: {len(val_drivers)}")

    # Collect file paths for all angle variants
    train_paths = []
    train_labels = []
    val_paths = []
    val_labels = []

    angle_variants = ['original', 'higher', 'lower', 'closer']

    print("\nProcessing angle variants:")
    for variant in angle_variants:
        print(f"  - {variant}")

        # Training data
        for _, row in train_df.iterrows():
            class_name = row['classname']
            img_name = row['img']
            file_path = Path(MULTIANGLE_DATASET_PATH) / variant / class_name / img_name

            if file_path.exists():
                train_paths.append(str(file_path))
                label = int(class_name[1:])
                train_labels.append(label)

        # Validation data (only use original angle for validation)
        if variant == 'original':
            for _, row in val_df.iterrows():
                class_name = row['classname']
                img_name = row['img']
                file_path = Path(MULTIANGLE_DATASET_PATH) / variant / class_name / img_name

                if file_path.exists():
                    val_paths.append(str(file_path))
                    label = int(class_name[1:])
                    val_labels.append(label)

    print(f"\nTrain images: {len(train_paths)} ({len(train_paths)//len(angle_variants)} × {len(angle_variants)} variants)")
    print(f"Val images: {len(val_paths)}")

    return train_paths, train_labels, val_paths, val_labels

def preprocess_image(image_path, label):
    """Load and preprocess image"""
    image = tf.io.read_file(image_path)
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.resize(image, IMG_SIZE)

    # MobileNetV2 preprocessing
    image = tf.keras.applications.mobilenet_v2.preprocess_input(image)

    return image, label

def augment_image(image, label):
    """Light augmentation (we already have angle variants)"""
    # Random flip
    image = tf.image.random_flip_left_right(image)

    # Random brightness/contrast
    image = tf.image.random_brightness(image, max_delta=0.2)
    image = tf.image.random_contrast(image, lower=0.8, upper=1.2)

    image = tf.clip_by_value(image, -1.0, 1.0)

    # Convert to one-hot for CategoricalCrossentropy
    label_one_hot = tf.one_hot(label, NUM_CLASSES)

    return image, label_one_hot

def create_dataset(file_paths, labels, is_training=True):
    """Create tf.data.Dataset"""
    dataset = tf.data.Dataset.from_tensor_slices((file_paths, labels))

    if is_training:
        dataset = dataset.shuffle(buffer_size=5000, seed=SEED)

    dataset = dataset.map(preprocess_image, num_parallel_calls=tf.data.AUTOTUNE)

    if is_training:
        dataset = dataset.map(augment_image, num_parallel_calls=tf.data.AUTOTUNE)
    else:
        # Validation: just convert to one-hot
        dataset = dataset.map(
            lambda img, lbl: (img, tf.one_hot(lbl, NUM_CLASSES)),
            num_parallel_calls=tf.data.AUTOTUNE
        )

    dataset = dataset.batch(BATCH_SIZE)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset

def create_model(num_classes=10):
    """Create MobileNetV2 model"""
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False

    inputs = layers.Input(shape=(224, 224, 3))

    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    x = layers.Dense(256, activation='relu',
                     kernel_regularizer=regularizers.l2(L2_REGULARIZATION))(x)
    x = layers.Dropout(DROPOUT_RATE)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model = keras.Model(inputs=inputs, outputs=outputs)

    return model, base_model

def main():
    # Load dataset
    train_paths, train_labels, val_paths, val_labels = load_multiangle_dataset()

    train_dataset = create_dataset(train_paths, train_labels, is_training=True)
    val_dataset = create_dataset(val_paths, val_labels, is_training=False)

    # Create model
    print("\nCreating model...")
    model, base_model = create_model()

    # Compile
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=INITIAL_LEARNING_RATE),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=LABEL_SMOOTHING),
        metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')]
    )

    print(f"Model created with {model.count_params():,} parameters")

    # Callbacks
    callbacks = [
        keras.callbacks.ModelCheckpoint(
            filepath='./models/best_model_multiangle.h5',
            monitor='val_accuracy',
            save_best_only=True,
            mode='max',
            verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        ),
    ]

    # Phase 1: Train head
    print("\n" + "="*70)
    print("PHASE 1: TRAINING CLASSIFICATION HEAD")
    print(f"Epochs: {INITIAL_EPOCHS}")
    print("="*70 + "\n")

    history1 = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=INITIAL_EPOCHS,
        callbacks=callbacks,
        verbose=1
    )

    # Phase 2: Fine-tune
    print("\n" + "="*70)
    print("PHASE 2: FINE-TUNING")
    print("="*70 + "\n")

    base_model.trainable = True
    for layer in base_model.layers[:-100]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=FINE_TUNE_LEARNING_RATE),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=LABEL_SMOOTHING),
        metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')]
    )

    history2 = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=FINE_TUNE_EPOCHS,
        callbacks=callbacks,
        verbose=1
    )

    # Final evaluation
    print("\n" + "="*70)
    print("FINAL EVALUATION")
    print("="*70)

    results = model.evaluate(val_dataset)
    print(f"\nFinal Validation Accuracy: {results[1]*100:.2f}%")
    print(f"Final Top-3 Accuracy: {results[2]*100:.2f}%")

    print("\nModel saved to: models/best_model_multiangle.h5")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
