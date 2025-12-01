import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import config


def load_driver_mapping():
    """Load driver_imgs_list.csv and create driver-to-image mapping."""
    df = pd.read_csv(config.DRIVER_CSV_PATH)
    print(f"Total images in CSV: {len(df)}")
    print(f"Unique drivers: {df['subject'].nunique()}")
    print(f"Driver distribution:\n{df['subject'].value_counts()}")
    return df


def split_by_driver(df, train_ratio=0.77):
    """
    Split dataset by driver to avoid data leakage.
    Approximately 20 drivers for train, 6 for validation.
    """
    unique_drivers = df['subject'].unique()
    np.random.seed(42)  # Reproducibility
    np.random.shuffle(unique_drivers)

    n_train = int(len(unique_drivers) * train_ratio)
    train_drivers = unique_drivers[:n_train]
    val_drivers = unique_drivers[n_train:]

    train_df = df[df['subject'].isin(train_drivers)]
    val_df = df[df['subject'].isin(val_drivers)]

    print(f"\nTrain drivers ({len(train_drivers)}): {sorted(train_drivers)}")
    print(f"Val drivers ({len(val_drivers)}): {sorted(val_drivers)}")
    print(f"Train images: {len(train_df)}")
    print(f"Val images: {len(val_df)}")

    return train_df, val_df, train_drivers, val_drivers


def create_file_paths_and_labels(df):
    """Convert dataframe to file paths and labels."""
    file_paths = []
    labels = []

    for _, row in df.iterrows():
        class_name = row['classname']
        img_name = row['img']
        file_path = Path(config.DATASET_PATH) / class_name / img_name

        if file_path.exists():
            file_paths.append(str(file_path))
            # Extract class number from 'c0' -> 0
            label = int(class_name[1:])
            labels.append(label)

    print(f"Valid file paths: {len(file_paths)}")
    return file_paths, labels


def preprocess_image(image_path, label):
    """Load and preprocess image for MobileNetV2."""
    # Read image
    image = tf.io.read_file(image_path)
    image = tf.image.decode_jpeg(image, channels=3)

    # Resize to 224x224 (MobileNetV2 input size)
    image = tf.image.resize(image, config.IMG_SIZE)

    # MobileNetV2 preprocessing: scale to [-1, 1]
    image = tf.keras.applications.mobilenet_v2.preprocess_input(image)

    return image, label


def augment_image(image, label):
    """Apply data augmentation."""
    # Random rotation
    image = tf.image.rot90(
        image,
        k=tf.random.uniform(shape=[], minval=0, maxval=4, dtype=tf.int32)
    )

    # Random flip
    image = tf.image.random_flip_left_right(image)

    # Random brightness
    image = tf.image.random_brightness(image, max_delta=0.2)

    # Random contrast
    image = tf.image.random_contrast(image, lower=0.8, upper=1.2)

    return image, label


def create_dataset(file_paths, labels, is_training=True):
    """Create tf.data.Dataset with preprocessing and augmentation."""
    # Create dataset from file paths
    dataset = tf.data.Dataset.from_tensor_slices((file_paths, labels))

    # Shuffle if training
    if is_training:
        dataset = dataset.shuffle(buffer_size=1000, seed=42)

    # Map preprocessing function
    dataset = dataset.map(
        preprocess_image,
        num_parallel_calls=tf.data.AUTOTUNE
    )

    # Apply augmentation only to training set
    if is_training:
        dataset = dataset.map(
            augment_image,
            num_parallel_calls=tf.data.AUTOTUNE
        )

    # Batch and prefetch
    dataset = dataset.batch(config.BATCH_SIZE)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset


def prepare_datasets():
    """Main function to prepare train and validation datasets."""
    # Load driver mapping
    df = load_driver_mapping()

    # Split by driver
    train_df, val_df, train_drivers, val_drivers = split_by_driver(df)

    # Create file paths and labels
    train_paths, train_labels = create_file_paths_and_labels(train_df)
    val_paths, val_labels = create_file_paths_and_labels(val_df)

    # Create datasets
    train_dataset = create_dataset(train_paths, train_labels, is_training=True)
    val_dataset = create_dataset(val_paths, val_labels, is_training=False)

    print(f"\nDatasets created successfully!")
    print(f"Train batches: ~{len(train_paths) // config.BATCH_SIZE}")
    print(f"Val batches: ~{len(val_paths) // config.BATCH_SIZE}")

    return train_dataset, val_dataset, train_drivers, val_drivers
