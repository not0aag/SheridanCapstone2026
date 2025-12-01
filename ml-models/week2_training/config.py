import os

# Paths
DATASET_PATH = '/Users/harry/datasets/safedrive/imgs/train'
DRIVER_CSV_PATH = '/Users/harry/datasets/safedrive/driver_imgs_list.csv'
MODEL_SAVE_PATH = './models'
LOGS_PATH = './logs'

# Model hyperparameters
IMG_SIZE = (224, 224)  # MobileNetV2 standard input
BATCH_SIZE = 32
INITIAL_EPOCHS = 20  # Frozen backbone
FINE_TUNE_EPOCHS = 10  # Additional epochs for fine-tuning
TOTAL_EPOCHS = INITIAL_EPOCHS + FINE_TUNE_EPOCHS  # 30 total epochs

# Learning rates
INITIAL_LEARNING_RATE = 0.001  # For frozen backbone
FINE_TUNE_LEARNING_RATE = 0.0001  # For fine-tuning

# Data augmentation parameters
ROTATION_RANGE = 15
WIDTH_SHIFT_RANGE = 0.1
HEIGHT_SHIFT_RANGE = 0.1
ZOOM_RANGE = 0.1
BRIGHTNESS_RANGE = [0.8, 1.2]

# Class names
CLASS_NAMES = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9']
NUM_CLASSES = len(CLASS_NAMES)

# Driver split (20 train, 6 validation)
# These will be populated automatically from the CSV
TRAIN_DRIVERS = []
VAL_DRIVERS = []
