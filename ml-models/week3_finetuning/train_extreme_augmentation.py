"""
EXTREME Augmentation Training - Fix AI-Generated Video Domain Shift
Trains model to be robust to synthetic/AI-generated content
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers
import improved_config as config
import improved_dataset_loader as dataset_loader
import os
from datetime import datetime
import numpy as np

# Class weights to fix c0/c8 bias
CLASS_WEIGHTS = {
    0: 1.4,  # Strong boost for safe driving
    1: 1.0,
    2: 1.0,
    3: 1.0,
    4: 1.0,
    5: 1.0,
    6: 1.0,
    7: 1.0,
    8: 0.75, # Heavy suppression of hair/makeup
    9: 1.15
}

def extreme_augmentation_layer():
    """
    Create extreme augmentation to simulate AI-generated video characteristics
    """
    data_augmentation = keras.Sequential([
        # Random flip
        layers.RandomFlip("horizontal"),

        # Extreme brightness variations (AI videos have different lighting)
        layers.RandomBrightness(0.4, value_range=(-1, 1)),

        # Extreme contrast (AI videos have different contrast)
        layers.RandomContrast(0.5),

        # Random zoom (simulate different camera distances)
        layers.RandomZoom(0.2, fill_mode='reflect'),

        # Random translation (simulate camera position variations)
        layers.RandomTranslation(0.15, 0.15, fill_mode='reflect'),

        # Add this custom layer for color jitter
    ], name='extreme_augmentation')

    return data_augmentation

def apply_extreme_augmentation(image, label):
    """
    Apply extreme augmentation including color jitter and noise
    """
    # Random saturation
    image = tf.image.random_saturation(image, 0.5, 1.5)

    # Random hue (color shift - AI videos have different colors)
    image = tf.image.random_hue(image, 0.2)

    # Add Gaussian noise (simulates AI artifacts)
    noise = tf.random.normal(shape=tf.shape(image), mean=0.0, stddev=0.08, dtype=tf.float32)
    image = image + noise

    # Random JPEG compression artifacts (simulates video compression)
    if tf.random.uniform([]) > 0.5:
        image = tf.image.adjust_jpeg_quality(image, tf.random.uniform([], 60, 100, dtype=tf.int32))

    # Clip values
    image = tf.clip_by_value(image, -1.0, 1.0)

    return image, label

def create_augmented_model(num_classes=10):
    """
    Model with built-in augmentation layer
    """
    # Base model
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=config.IMG_SIZE + (3,),
        include_top=False,
        weights='imagenet'
    )

    # Freeze base initially
    base_model.trainable = False

    # Build model with augmentation
    inputs = keras.Input(shape=config.IMG_SIZE + (3,))

    # Augmentation layer (only active during training)
    x = extreme_augmentation_layer()(inputs)

    # Base model
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)

    # Stronger regularization
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(
        256,
        activation='relu',
        kernel_regularizer=regularizers.l2(0.0001)
    )(x)
    x = layers.Dropout(0.3)(x)

    # Output
    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model = keras.Model(inputs, outputs)

    return model, base_model

def compile_model(model, learning_rate):
    """Compile with label smoothing"""
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=[
            'accuracy',
            keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')
        ]
    )
    return model

def main():
    print("\n" + "="*80)
    print("EXTREME AUGMENTATION TRAINING - AI Video Domain Adaptation")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load datasets
    print("="*80)
    print("LOADING DATASETS")
    print("="*80 + "\n")

    df = dataset_loader.load_driver_mapping()
    train_df, val_df, _, _ = dataset_loader.split_by_driver(df)

    train_paths, train_labels = dataset_loader.create_file_paths_and_labels(train_df)
    val_paths, val_labels = dataset_loader.create_file_paths_and_labels(val_df)

    # Create datasets
    train_dataset = tf.data.Dataset.from_tensor_slices((train_paths, train_labels))
    train_dataset = train_dataset.shuffle(10000, seed=config.SEED)
    train_dataset = train_dataset.map(dataset_loader.preprocess_image, num_parallel_calls=tf.data.AUTOTUNE)

    # Convert labels to one-hot
    train_dataset = train_dataset.map(
        lambda x, y: (x, tf.one_hot(y, 10)),
        num_parallel_calls=tf.data.AUTOTUNE
    )

    # Apply EXTREME augmentation
    train_dataset = train_dataset.map(apply_extreme_augmentation, num_parallel_calls=tf.data.AUTOTUNE)
    train_dataset = train_dataset.batch(config.BATCH_SIZE)
    train_dataset = train_dataset.prefetch(tf.data.AUTOTUNE)

    # Validation dataset (no augmentation)
    val_dataset = tf.data.Dataset.from_tensor_slices((val_paths, val_labels))
    val_dataset = val_dataset.map(dataset_loader.preprocess_image, num_parallel_calls=tf.data.AUTOTUNE)
    val_dataset = val_dataset.map(
        lambda x, y: (x, tf.one_hot(y, 10)),
        num_parallel_calls=tf.data.AUTOTUNE
    )
    val_dataset = val_dataset.batch(config.BATCH_SIZE)
    val_dataset = val_dataset.prefetch(tf.data.AUTOTUNE)

    print("✓ Datasets loaded with EXTREME augmentation\n")

    # Create model
    print("="*80)
    print("BUILDING MODEL WITH AUGMENTATION LAYER")
    print("="*80 + "\n")

    model, base_model = create_augmented_model()
    model = compile_model(model, config.INITIAL_LEARNING_RATE)

    print(f"Total parameters: {model.count_params():,}")
    print(f"Trainable parameters: {sum([tf.keras.backend.count_params(w) for w in model.trainable_weights]):,}\n")

    # Callbacks
    log_dir = f"logs/extreme_aug_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs('models', exist_ok=True)

    callbacks = [
        keras.callbacks.ModelCheckpoint(
            'models/best_model_extreme_aug.h5',
            monitor='val_accuracy',
            save_best_only=True,
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
            patience=5,
            min_lr=1e-7,
            verbose=1
        ),
        keras.callbacks.TensorBoard(log_dir=log_dir),
        keras.callbacks.CSVLogger('extreme_aug_training.csv')
    ]

    # PHASE 1: Train classification head
    print("\n" + "="*80)
    print("PHASE 1: TRAINING WITH EXTREME AUGMENTATION")
    print(f"Epochs: {config.INITIAL_EPOCHS}")
    print("="*80 + "\n")

    history_phase1 = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=config.INITIAL_EPOCHS,
        callbacks=callbacks,
        class_weight=CLASS_WEIGHTS,
        verbose=1
    )

    best_val_acc = max(history_phase1.history['val_accuracy'])
    print(f"\n✓ Phase 1 Best Accuracy: {best_val_acc:.2%}\n")

    # PHASE 2: Fine-tune entire model
    print("\n" + "="*80)
    print("PHASE 2: FINE-TUNING ENTIRE MODEL")
    print(f"Epochs: {config.FINE_TUNE_EPOCHS}")
    print("="*80 + "\n")

    # Unfreeze base
    base_model.trainable = True

    # Recompile
    model = compile_model(model, config.FINE_TUNE_LEARNING_RATE)

    print(f"Trainable parameters: {sum([tf.keras.backend.count_params(w) for w in model.trainable_weights]):,}\n")

    history_phase2 = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=config.FINE_TUNE_EPOCHS,
        callbacks=callbacks,
        class_weight=CLASS_WEIGHTS,
        verbose=1
    )

    if history_phase2.history and 'val_accuracy' in history_phase2.history:
        best_val_acc = max(history_phase2.history['val_accuracy'])
        print(f"\n✓ Phase 2 Best Accuracy: {best_val_acc:.2%}\n")

    # Save final model
    model.save('models/extreme_aug_final.h5')

    # Convert to TFLite
    print("\n" + "="*80)
    print("CONVERTING TO TFLITE")
    print("="*80 + "\n")

    best_model = keras.models.load_model('models/best_model_extreme_aug.h5')
    converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    os.makedirs('tflite_models', exist_ok=True)
    tflite_path = 'tflite_models/extreme_aug_model.tflite'
    with open(tflite_path, 'wb') as f:
        f.write(tflite_model)

    print(f"✓ TFLite model saved: {tflite_path}")
    print(f"  Size: {os.path.getsize(tflite_path) / (1024*1024):.2f} MB\n")

    # Final evaluation
    print("="*80)
    print("FINAL EVALUATION")
    print("="*80 + "\n")

    results = best_model.evaluate(val_dataset, verbose=1)
    print(f"\nValidation Accuracy: {results[1]:.2%}")
    print(f"Top-3 Accuracy: {results[2]:.2%}\n")

    print("="*80)
    print("TRAINING COMPLETE")
    print("="*80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Best model: models/best_model_extreme_aug.h5")
    print(f"TFLite: {tflite_path}\n")

if __name__ == "__main__":
    main()
