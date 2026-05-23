"""
Multi-Angle Dataset Generator
Generates synthetic camera viewpoints from State Farm dataset
to enable model to work with different phone mounting positions

Creates 4 versions of each image:
1. Original (baseline)
2. Higher camera angle (windshield mount simulation)
3. Lower camera angle (lower dashboard simulation)
4. Closer camera (AC vent mount simulation)
"""

import cv2
import numpy as np
from pathlib import Path
import os
from tqdm import tqdm

# Paths
SOURCE_DATASET = '/Users/harry/datasets/safedrive/imgs/train'
OUTPUT_DATASET = '/Users/harry/datasets/safedrive/imgs/train_multiangle'

def simulate_higher_camera(img):
    """
    Simulate camera mounted HIGHER (like windshield mount)
    Creates perspective as if looking slightly DOWN at driver
    """
    h, w = img.shape[:2]

    # Source points (original corners)
    pts1 = np.float32([
        [0, 0],
        [w-1, 0],
        [0, h-1],
        [w-1, h-1]
    ])

    # Destination points - compress top, expand bottom
    # This simulates viewing from above
    compression = 0.15  # 15% perspective shift
    pts2 = np.float32([
        [int(w*compression), int(h*compression)],
        [int(w*(1-compression)), int(h*compression)],
        [0, h-1],
        [w-1, h-1]
    ])

    # Apply perspective transform
    M = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    return warped

def simulate_lower_camera(img):
    """
    Simulate camera mounted LOWER (like lower dashboard)
    Creates perspective as if looking slightly UP at driver
    """
    h, w = img.shape[:2]

    pts1 = np.float32([
        [0, 0],
        [w-1, 0],
        [0, h-1],
        [w-1, h-1]
    ])

    # Destination points - expand top, compress bottom
    # This simulates viewing from below
    compression = 0.15
    pts2 = np.float32([
        [0, 0],
        [w-1, 0],
        [int(w*compression), int(h*(1-compression))],
        [int(w*(1-compression)), int(h*(1-compression))]
    ])

    M = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    return warped

def simulate_closer_camera(img):
    """
    Simulate camera positioned CLOSER (like AC vent mount)
    Zooms in by 20% - crops and resizes
    """
    h, w = img.shape[:2]

    # Crop 10% from each edge (20% total zoom)
    crop = 0.1
    cropped = img[
        int(h*crop):int(h*(1-crop)),
        int(w*crop):int(w*(1-crop))
    ]

    # Resize back to original dimensions
    zoomed = cv2.resize(cropped, (w, h))

    return zoomed

def simulate_side_angle(img):
    """
    Simulate slight rotation (different mounting angles)
    """
    h, w = img.shape[:2]

    # Random rotation ±10 degrees
    angle = np.random.uniform(-10, 10)
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    return rotated

def generate_multiangle_dataset():
    """
    Generate multi-angle versions of entire dataset
    """

    print("="*70)
    print("MULTI-ANGLE DATASET GENERATOR")
    print("="*70)
    print(f"\nSource: {SOURCE_DATASET}")
    print(f"Output: {OUTPUT_DATASET}")

    # Create output directory
    output_path = Path(OUTPUT_DATASET)
    output_path.mkdir(parents=True, exist_ok=True)

    # Camera angle variants
    variants = {
        'original': lambda img: img,  # Keep original
        'higher': simulate_higher_camera,
        'lower': simulate_lower_camera,
        'closer': simulate_closer_camera,
    }

    print(f"\nGenerating {len(variants)} camera angle variants:")
    for name in variants.keys():
        print(f"  - {name}")

    total_images = 0

    # Process each class
    for class_idx in range(10):
        class_name = f'c{class_idx}'
        source_class_dir = Path(SOURCE_DATASET) / class_name

        if not source_class_dir.exists():
            print(f"\nWarning: Class {class_name} not found, skipping...")
            continue

        # Get all images for this class
        img_files = list(source_class_dir.glob('*.jpg'))

        print(f"\nProcessing {class_name} ({len(img_files)} images)...")

        # Create variant directories
        for variant_name in variants.keys():
            variant_dir = output_path / variant_name / class_name
            variant_dir.mkdir(parents=True, exist_ok=True)

        # Process each image
        for img_file in tqdm(img_files, desc=f"  {class_name}"):
            # Load original image
            img = cv2.imread(str(img_file))

            if img is None:
                continue

            # Generate each variant
            for variant_name, transform_fn in variants.items():
                # Apply transformation
                transformed = transform_fn(img)

                # Save
                output_file = output_path / variant_name / class_name / img_file.name
                cv2.imwrite(str(output_file), transformed)

                total_images += 1

    print("\n" + "="*70)
    print("DATASET GENERATION COMPLETE")
    print("="*70)
    print(f"\nTotal images generated: {total_images}")
    print(f"Dataset multiplied by: {len(variants)}x")
    print(f"Output location: {OUTPUT_DATASET}")

    # Create summary file
    summary_file = output_path / 'dataset_info.txt'
    with open(summary_file, 'w') as f:
        f.write("Multi-Angle SafeDrive Dataset\n")
        f.write("="*50 + "\n\n")
        f.write(f"Source: {SOURCE_DATASET}\n")
        f.write(f"Total images: {total_images}\n")
        f.write(f"Variants: {len(variants)}\n\n")
        f.write("Camera Angles:\n")
        for name in variants.keys():
            variant_dir = output_path / name
            img_count = len(list(variant_dir.rglob('*.jpg')))
            f.write(f"  {name}: {img_count} images\n")

    print(f"\nSummary saved to: {summary_file}")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    generate_multiangle_dataset()
