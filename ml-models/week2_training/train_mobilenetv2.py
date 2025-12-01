import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import config
import dataset_loader
import os
from datetime import datetime


def create_model(num_classes=10):
    """
    Create MobileNetV2 model with custom classification head.
    Initial training: backbone frozen
    Fine-tuning: last 100 layers unfrozen
    """
    # Load pre-trained MobileNetV2 (without top classification layer)
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=config.IMG_SIZE + (3,),
        include_top=False,
        weights='imagenet'
    )

    # Freeze base model initially
    base_model.trainable = False

    # Add custom classification head
    inputs = keras.Input(shape=config.IMG_SIZE + (3,))

    # Preprocessing is already done in dataset loader
    x = base_model(inputs, training=False)

    # Global average pooling
    x = layers.GlobalAveragePooling2D()(x)

    # Dropout for regularization
    x = layers.Dropout(0.2)(x)

    # Final classification layer
    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model = keras.Model(inputs, outputs)

    print(f"\n{'='*50}")
    print(f"Model created with {num_classes} classes")
    print(f"Base model layers: {len(base_model.layers)}")
    print(f"Base model trainable: {base_model.trainable}")
    print(f"{'='*50}\n")

    return model, base_model


def compile_model(model, learning_rate):
    """Compile model with optimizer, loss, and metrics."""
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=keras.losses.SparseCategoricalCrossentropy(),
        metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(
            k=3, name='top_3_accuracy')]
    )
    return model


def create_callbacks(log_dir):
    """Create training callbacks."""
    callbacks = [
        # TensorBoard for visualization
        keras.callbacks.TensorBoard(
            log_dir=log_dir,
            histogram_freq=1
        ),

        # Model checkpoint - save best model
        keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(config.MODEL_SAVE_PATH, 'best_model.h5'),
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        ),

        # Early stopping
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),

        # Reduce learning rate on plateau
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        )
    ]
    return callbacks


def train_phase_1(model, train_dataset, val_dataset, log_dir):
    """
    Phase 1: Train with frozen backbone.
    """
    print(f"\n{'='*50}")
    print("PHASE 1: Training with frozen backbone")
    print(f"Epochs: {config.INITIAL_EPOCHS}")
    print(f"Learning rate: {config.INITIAL_LEARNING_RATE}")
    print(f"{'='*50}\n")

    callbacks = create_callbacks(log_dir)

    history_phase1 = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=config.INITIAL_EPOCHS,
        callbacks=callbacks,
        verbose=1
    )

    return history_phase1


def train_phase_2(model, base_model, train_dataset, val_dataset, log_dir):
    """
    Phase 2: Fine-tune last 100 layers.
    """
    print(f"\n{'='*50}")
    print("PHASE 2: Fine-tuning last 100 layers")
    print(f"Epochs: {config.INITIAL_EPOCHS} → {config.TOTAL_EPOCHS}")
    print(f"Learning rate: {config.FINE_TUNE_LEARNING_RATE}")
    print(f"{'='*50}\n")

    # Unfreeze base model
    base_model.trainable = True

    # Freeze all layers except last 100
    for layer in base_model.layers[:-100]:
        layer.trainable = False

    # Count trainable parameters
    trainable_count = sum([tf.keras.backend.count_params(w)
                          for w in model.trainable_weights])
    non_trainable_count = sum([tf.keras.backend.count_params(w)
                              for w in model.non_trainable_weights])

    print(f"Trainable params: {trainable_count:,}")
    print(f"Non-trainable params: {non_trainable_count:,}")
    print(f"Total params: {trainable_count + non_trainable_count:,}\n")

    # Recompile with lower learning rate
    model = compile_model(model, config.FINE_TUNE_LEARNING_RATE)

    callbacks = create_callbacks(log_dir)

    history_phase2 = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=config.TOTAL_EPOCHS,  # Changed from FINE_TUNE_EPOCHS
        initial_epoch=config.INITIAL_EPOCHS,
        callbacks=callbacks,
        verbose=1
    )

    return history_phase2


def main():
    """Main training pipeline."""
    # Create directories
    os.makedirs(config.MODEL_SAVE_PATH, exist_ok=True)
    os.makedirs(config.LOGS_PATH, exist_ok=True)

    # Log directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = os.path.join(config.LOGS_PATH, f"run_{timestamp}")

    print("="*50)
    print("SafeDrive AI - MobileNetV2 Training")
    print("="*50)

    # Prepare datasets
    print("\nPreparing datasets...")
    train_dataset, val_dataset, train_drivers, val_drivers = dataset_loader.prepare_datasets()

    # Create model
    print("\nCreating model...")
    model, base_model = create_model(num_classes=config.NUM_CLASSES)

    # Compile model
    model = compile_model(model, config.INITIAL_LEARNING_RATE)

    # Print model summary
    model.summary()

    # Phase 1: Train with frozen backbone
    history_phase1 = train_phase_1(model, train_dataset, val_dataset, log_dir)

    # Phase 2: Fine-tune last 100 layers
    history_phase2 = train_phase_2(
        model, base_model, train_dataset, val_dataset, log_dir)

    # Save final model
    final_model_path = os.path.join(
        config.MODEL_SAVE_PATH, 'mobilenetv2_final.h5')
    model.save(final_model_path)
    print(f"\nFinal model saved to: {final_model_path}")

    # Evaluate on validation set
    print("\nFinal evaluation on validation set:")
    val_loss, val_accuracy, val_top3_accuracy = model.evaluate(val_dataset)
    print(f"Validation Loss: {val_loss:.4f}")
    print(f"Validation Accuracy: {val_accuracy:.4f}")
    print(f"Validation Top-3 Accuracy: {val_top3_accuracy:.4f}")

    print("\n" + "="*50)
    print("Training complete!")
    print("="*50)


if __name__ == "__main__":
    main()
