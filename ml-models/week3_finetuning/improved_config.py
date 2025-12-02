"""
Improved configuration for 92%+ accuracy target
Based on research and best practices for transfer learning
"""
import os

# Paths
DATASET_PATH = '/Users/harry/datasets/safedrive/imgs/train'
DRIVER_CSV_PATH = '/Users/harry/datasets/safedrive/driver_imgs_list.csv'
MODEL_SAVE_PATH = './models'
LOGS_PATH = './logs'

# Model hyperparameters
IMG_SIZE = (224, 224)  # MobileNetV2 standard input
BATCH_SIZE = 16  # Reduced for better gradient estimates
INITIAL_EPOCHS = 30  # Increased from 20 (frozen backbone)
FINE_TUNE_EPOCHS = 20  # Increased from 10
TOTAL_EPOCHS = INITIAL_EPOCHS + FINE_TUNE_EPOCHS  # 50 total epochs

# Learning rates with warm restart
INITIAL_LEARNING_RATE = 0.001
FINE_TUNE_LEARNING_RATE = 0.00005  # Lower for stability

# Advanced data augmentation parameters
ROTATION_RANGE = 20  # Increased from 15
WIDTH_SHIFT_RANGE = 0.15  # Increased from 0.1
HEIGHT_SHIFT_RANGE = 0.15
ZOOM_RANGE = 0.15
BRIGHTNESS_RANGE = [0.7, 1.3]  # Wider range for robustness
SHEAR_RANGE = 0.1  # NEW: simulate camera angle variations
CHANNEL_SHIFT_RANGE = 0.1  # NEW: color variations

# Regularization
DROPOUT_RATE = 0.3  # Increased from 0.2
L2_REGULARIZATION = 0.0001  # NEW: weight decay

# Mixup augmentation (proven to improve generalization)
USE_MIXUP = True
MIXUP_ALPHA = 0.2

# Label smoothing (prevents overconfidence)
LABEL_SMOOTHING = 0.1

# Class names
CLASS_NAMES = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9']
NUM_CLASSES = len(CLASS_NAMES)

# Training settings
SEED = 42  # For reproducibility
VERBOSE = 1

print(f"""
{'='*60}
IMPROVED TRAINING CONFIGURATION
Target: 92%+ Accuracy (Current: 84.88%)
{'='*60}
Total Epochs: {TOTAL_EPOCHS} (Phase 1: {INITIAL_EPOCHS}, Phase 2: {FINE_TUNE_EPOCHS})
Batch Size: {BATCH_SIZE}
Mixup: {USE_MIXUP}
Label Smoothing: {LABEL_SMOOTHING}
{'='*60}
""")
