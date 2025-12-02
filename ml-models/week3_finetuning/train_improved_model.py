"""
Improved training script targeting 92%+ accuracy
Implements advanced techniques from research
"""
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers
import improved_config as config
import improved_dataset_loader as dataset_loader
import os
from datetime import datetime
import numpy as np


def create_improved_model(num_classes=10):
    """
    Create improved MobileNetV2 model with:
    - L2 regularization
    - Higher dropout
    - Label smoothing
    """
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=config.IMG_SIZE + (3,),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model initially
    base_model.trainable = False
    
    # Build model with regularization
    inputs = keras.Input(shape=config.IMG_SIZE + (3,))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    
    # Stronger regularization
    x = layers.Dropout(config.DROPOUT_RATE)(x)
    x = layers.Dense(
        256,
        activation='relu',
        kernel_regularizer=regularizers.l2(config.L2_REGULARIZATION)
    )(x)
    x = layers.Dropout(config.DROPOUT_RATE)(x)
    
    # Final layer with label smoothing (applied in loss function)
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = keras.Model(inputs, outputs)
    
    print(f"\n{'='*60}")
    print(f"IMPROVED MODEL ARCHITECTURE")
    print(f"{'='*60}")
    print(f"Base model: MobileNetV2 (ImageNet pretrained)")
    print(f"Dropout rate: {config.DROPOUT_RATE}")
    print(f"L2 regularization: {config.L2_REGULARIZATION}")
    print(f"Label smoothing: {config.LABEL_SMOOTHING}")
    print(f"Total layers: {len(model.layers)}")
    print(f"{'='*60}\n")
    
    return model, base_model


def compile_model_with_label_smoothing(model, learning_rate):
    """Compile with label smoothing for better generalization."""
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=keras.losses.CategoricalCrossentropy(
            label_smoothing=config.LABEL_SMOOTHING
        ),
        metrics=[
            'accuracy',
            keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')
        ]
    )
    return model


def create_advanced_callbacks(log_dir):
    """Create callbacks with cosine annealing and better early stopping."""
    callbacks = [
        # TensorBoard
        keras.callbacks.TensorBoard(
            log_dir=log_dir,
            histogram_freq=1,
            write_graph=True
        ),
        
        # Model checkpoint - save best
        keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(config.MODEL_SAVE_PATH, 'best_model_improved.h5'),
            monitor='val_accuracy',
            save_best_only=True,
            mode='max',
            verbose=1
        ),
        
        # Early stopping with more patience
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,  # Increased from 5
            restore_best_weights=True,
            verbose=1
        ),
        
        # Reduce learning rate on plateau
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1
        ),
    ]
    return callbacks


def train_phase_1(model, train_dataset, val_dataset, log_dir):
    """
    Phase 1: Train classification head (frozen backbone)
    30 epochs with aggressive augmentation
    """
    print("\n" + "="*60)
    print("PHASE 1: TRAINING CLASSIFICATION HEAD")
    print(f"Epochs: {config.INITIAL_EPOCHS}")
    print(f"Learning rate: {config.INITIAL_LEARNING_RATE}")
    print("="*60 + "\n")
    
    callbacks = create_advanced_callbacks(log_dir)
    
    history_phase1 = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=config.INITIAL_EPOCHS,
        callbacks=callbacks,
        verbose=config.VERBOSE
    )
    
    # Get best accuracy
    best_val_acc = max(history_phase1.history['val_accuracy'])
    print(f"\n Phase 1 Best Validation Accuracy: {best_val_acc:.2%}\n")
    
    return history_phase1


def train_phase_2(model, base_model, train_dataset, val_dataset, log_dir):
    """
    Phase 2: Fine-tune entire model
    20 additional epochs with lower learning rate
    """
    print("\n" + "="*60)
    print("PHASE 2: FINE-TUNING ENTIRE MODEL")
    print("="*60)
    
    # Unfreeze last 100 layers of base model
    base_model.trainable = True
    for layer in base_model.layers[:-100]:
        layer.trainable = False
    
    print(f"Trainable layers in base model: {sum([1 for l in base_model.layers if l.trainable])}")
    print(f"Total trainable parameters: {model.count_params():,}")
    
    # Recompile with lower learning rate
    model = compile_model_with_label_smoothing(model, config.FINE_TUNE_LEARNING_RATE)
    
    print(f"Learning rate: {config.FINE_TUNE_LEARNING_RATE}")
    print("="*60 + "\n")
    
    callbacks = create_advanced_callbacks(log_dir + "_phase2")
    
    history_phase2 = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=config.FINE_TUNE_EPOCHS,
        initial_epoch=config.INITIAL_EPOCHS,
        callbacks=callbacks,
        verbose=config.VERBOSE
    )
    
    best_val_acc = max(history_phase2.history['val_accuracy'])
    print(f"\n Phase 2 Best Validation Accuracy: {best_val_acc:.2%}\n")
    
    return history_phase2


def evaluate_model(model, val_dataset):
    """Detailed evaluation of final model."""
    print("\n" + "="*60)
    print("FINAL MODEL EVALUATION")
    print("="*60 + "\n")
    
    results = model.evaluate(val_dataset, verbose=1)
    
    print(f"\nFinal Results:")
    print(f"  Validation Loss: {results[0]:.4f}")
    print(f"  Validation Accuracy: {results[1]:.2%}")
    print(f"  Top-3 Accuracy: {results[2]:.2%}")
    
    if results[1] >= 0.92:
        print(f"\n ✅ TARGET ACHIEVED! Accuracy >= 92%")
    else:
        print(f"\n ⚠️ Target not met. Gap: {(0.92 - results[1])*100:.2f}%")
        print(f"  Consider:")
        print(f"    - More training epochs")
        print(f"    - Larger model (EfficientNet)")
        print(f"    - Ensemble methods")
    
    print("="*60 + "\n")
    
    return results


def main():
    """Main training pipeline."""
    print("\n" + "="*80)
    print("SAFEDRIVE AI - IMPROVED MODEL TRAINING")
    print("Target: 92%+ Accuracy (Previous: 84.88%)")
    print("="*80 + "\n")
    
    # Create directories
    os.makedirs(config.MODEL_SAVE_PATH, exist_ok=True)
    os.makedirs(config.LOGS_PATH, exist_ok=True)
    
    # Prepare datasets
    train_dataset, val_dataset, train_drivers, val_drivers = dataset_loader.prepare_datasets()
    
    # Create model
    model, base_model = create_improved_model(num_classes=config.NUM_CLASSES)
    
    # Compile
    model = compile_model_with_label_smoothing(model, config.INITIAL_LEARNING_RATE)
    
    # Create log directory
    log_dir = os.path.join(
        config.LOGS_PATH,
        f"improved_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Phase 1: Train classifier
    history_phase1 = train_phase_1(model, train_dataset, val_dataset, log_dir)
    
    # Phase 2: Fine-tune
    history_phase2 = train_phase_2(model, base_model, train_dataset, val_dataset, log_dir)
    
    # Final evaluation
    final_results = evaluate_model(model, val_dataset)
    
    # Save final model
    final_model_path = os.path.join(config.MODEL_SAVE_PATH, 'mobilenetv2_improved_final.h5')
    model.save(final_model_path)
    print(f"\nFinal model saved to: {final_model_path}")
    
    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print(f"Final Validation Accuracy: {final_results[1]:.2%}")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Set random seeds for reproducibility
    np.random.seed(config.SEED)
    tf.random.set_seed(config.SEED)
    
    # Enable mixed precision for faster training on M4
    # tf.keras.mixed_precision.set_global_policy('mixed_float16')
    
    main()
