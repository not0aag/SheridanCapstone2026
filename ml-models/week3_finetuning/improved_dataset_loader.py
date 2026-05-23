"""
Improved dataset loader with advanced augmentation techniques
Target: 92%+ accuracy through better generalization
"""
import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import improved_config as config


def load_driver_mapping():
    """Load driver_imgs_list.csv and create driver-to-image mapping."""
    df = pd.read_csv(config.DRIVER_CSV_PATH)
    print(f"Total images in CSV: {len(df)}")
    print(f"Unique drivers: {df['subject'].nunique()}")
    return df


def split_by_driver(df, train_ratio=0.77):
    """Split dataset by driver to avoid data leakage."""
    unique_drivers = df['subject'].unique()
    np.random.seed(config.SEED)
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
            label = int(class_name[1:])
            labels.append(label)

    print(f"Valid file paths: {len(file_paths)}")
    return file_paths, labels


def preprocess_image(image_path, label):
    """Load and preprocess image for MobileNetV2."""
    image = tf.io.read_file(image_path)
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.resize(image, config.IMG_SIZE)
    
    # MobileNetV2 preprocessing: scale to [-1, 1]
    image = tf.keras.applications.mobilenet_v2.preprocess_input(image)
    
    return image, label


def advanced_augment_image(image, label):
    """
    Advanced data augmentation for better generalization.
    Simulates various real-world conditions.
    """
    # Random rotation (simulates head tilt)
    image = tf.image.rot90(
        image,
        k=tf.random.uniform(shape=[], minval=0, maxval=4, dtype=tf.int32)
    )
    
    # Random horizontal flip
    image = tf.image.random_flip_left_right(image)
    
    # Random brightness (simulates lighting conditions)
    image = tf.image.random_brightness(image, max_delta=0.3)
    
    # Random contrast
    image = tf.image.random_contrast(image, lower=0.7, upper=1.3)
    
    # Random saturation (color variations)
    image = tf.image.random_saturation(image, lower=0.7, upper=1.3)
    
    # Random hue shift
    image = tf.image.random_hue(image, max_delta=0.1)
    
    # Random zoom (simulates camera distance)
    if tf.random.uniform([]) > 0.5:
        image = tf.image.resize_with_crop_or_pad(
            image,
            int(config.IMG_SIZE[0] * 1.2),
            int(config.IMG_SIZE[1] * 1.2)
        )
        image = tf.image.random_crop(image, size=[config.IMG_SIZE[0], config.IMG_SIZE[1], 3])
    
    # Ensure values are still in valid range after augmentation
    image = tf.clip_by_value(image, -1.0, 1.0)
    
    return image, label


def mixup(image1, label1, image2, label2, alpha=0.2):
    """
    Mixup augmentation: blend two images and labels.
    Proven to improve model generalization.
    """
    # Sample mixing ratio
    lam = tf.random.uniform([], 0, alpha)
    
    # Mix images
    mixed_image = lam * image1 + (1 - lam) * image2
    
    # Mix labels (one-hot encoded)
    label1_one_hot = tf.one_hot(label1, config.NUM_CLASSES)
    label2_one_hot = tf.one_hot(label2, config.NUM_CLASSES)
    mixed_label = lam * label1_one_hot + (1 - lam) * label2_one_hot
    
    return mixed_image, mixed_label


def create_dataset(file_paths, labels, is_training=True, use_mixup=False):
    """Create tf.data.Dataset with advanced preprocessing and augmentation."""
    dataset = tf.data.Dataset.from_tensor_slices((file_paths, labels))

    if is_training:
        dataset = dataset.shuffle(buffer_size=2000, seed=config.SEED)

    # Preprocess
    dataset = dataset.map(preprocess_image, num_parallel_calls=tf.data.AUTOTUNE)

    # Apply augmentation only to training set
    if is_training:
        dataset = dataset.map(advanced_augment_image, num_parallel_calls=tf.data.AUTOTUNE)

        # Apply mixup if enabled
        if use_mixup and config.USE_MIXUP:
            # Create a second shuffled dataset for mixup
            dataset2 = tf.data.Dataset.from_tensor_slices((file_paths, labels))
            dataset2 = dataset2.shuffle(buffer_size=2000, seed=config.SEED + 1)
            dataset2 = dataset2.map(preprocess_image, num_parallel_calls=tf.data.AUTOTUNE)
            dataset2 = dataset2.map(advanced_augment_image, num_parallel_calls=tf.data.AUTOTUNE)

            # Zip and apply mixup (creates one-hot labels)
            dataset = tf.data.Dataset.zip((dataset, dataset2))
            dataset = dataset.map(
                lambda x1, x2: mixup(x1[0], x1[1], x2[0], x2[1], config.MIXUP_ALPHA),
                num_parallel_calls=tf.data.AUTOTUNE
            )
        else:
            # No mixup: convert to one-hot for CategoricalCrossentropy
            dataset = dataset.map(
                lambda img, lbl: (img, tf.one_hot(lbl, config.NUM_CLASSES)),
                num_parallel_calls=tf.data.AUTOTUNE
            )
    else:
        # Validation: convert labels to one-hot to match CategoricalCrossentropy
        dataset = dataset.map(
            lambda img, lbl: (img, tf.one_hot(lbl, config.NUM_CLASSES)),
            num_parallel_calls=tf.data.AUTOTUNE
        )

    # Batch and prefetch
    dataset = dataset.batch(config.BATCH_SIZE)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset


def prepare_datasets():
    """Main function to prepare train and validation datasets."""
    print("\n" + "="*60)
    print("LOADING DATASETS WITH ADVANCED AUGMENTATION")
    print("="*60)
    
    df = load_driver_mapping()
    train_df, val_df, train_drivers, val_drivers = split_by_driver(df)
    
    train_paths, train_labels = create_file_paths_and_labels(train_df)
    val_paths, val_labels = create_file_paths_and_labels(val_df)
    
    # Training set with mixup augmentation
    train_dataset = create_dataset(train_paths, train_labels, is_training=True, use_mixup=config.USE_MIXUP)
    
    # Validation set without augmentation
    val_dataset = create_dataset(val_paths, val_labels, is_training=False, use_mixup=False)
    
    print(f"\nDatasets created successfully!")
    print(f"Train batches: ~{len(train_paths) // config.BATCH_SIZE}")
    print(f"Val batches: ~{len(val_paths) // config.BATCH_SIZE}")
    print(f"Mixup enabled: {config.USE_MIXUP}")
    print("="*60 + "\n")
    
    return train_dataset, val_dataset, train_drivers, val_drivers
