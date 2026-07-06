"""
Validates the actual shipped Android model — app/src/main/assets/models/distraction_classifier.tflite —
using the *exact* preprocessing DistractionInferenceEngine.kt applies on-device.

Why this script exists
-----------------------
The shipped model's "~91% val accuracy" claim (see DistractionInferenceEngine.kt's doc
comment) is unverifiable from anything committed in this repo: the model file's
checksum doesn't match any artifact under ml-models/, and ml-models/week3_finetuning/
CURRENT_STATUS.md is frozen at "Epoch 1/30, ~23.5% accuracy" with no later update.

The one fully-documented conversion in this repo — ml-models/week2_training/tflite_models/
model_metadata.json — shows a Keras model at 84.88% val accuracy dropping to 23.8% after
TFLite conversion (`"validation_status": "WARNING"`, `"accuracy_difference_percent": 61.08`).
The cause is a preprocessing mismatch: that metadata documents
`"normalization": "Divide by 255.0 to get [0, 1] range"`, while the Android code
(DistractionInferenceEngine.kt:preprocessBitmap) actually feeds the model
`(channel / 127.5) - 1.0` (i.e. [-1, 1], the standard MobileNetV2 preprocessing).
This script uses the on-device [-1, 1] preprocessing, since that's what the shipped
model is actually being fed at inference time — a mismatch here would explain a
similar accuracy collapse if the *shipped* model happens to expect [0, 1] instead.

Usage
-----
Labeled accuracy check (once you have even 5-10 images per class):
    python validate_tflite.py --data-dir path/to/labeled_images

    Expected layout — one folder per class, folder name starts with the class index
    (matches the common State Farm Distracted Driver `c0`..`c9` convention):
        labeled_images/
          c0_safe/*.jpg
          c1_texting_right/*.jpg
          ...
          c9_talking_passenger/*.jpg

Zero-data fallback — sanity check only, no accuracy number, just eyeball the output:
    python validate_tflite.py --sanity-dir path/to/any_photos

Requires the same environment as ml-models/week2_training (tensorflow==2.14.0) —
no new dependency, reuse that venv:
    cd ml-models/week2_training && python -m venv venv && venv/Scripts/activate
    pip install -r requirements.txt
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = REPO_ROOT / "app" / "src" / "main" / "assets" / "models" / "distraction_classifier.tflite"

INPUT_SIZE = 224

# Must match DistractionInferenceEngine.kt's CLASS_LABELS exactly (index order matters).
CLASS_LABELS = {
    0: "Safe driving",
    1: "Texting - right hand",
    2: "Talking on phone - right",
    3: "Texting - left hand",
    4: "Talking on phone - left",
    5: "Operating radio",
    6: "Drinking",
    7: "Reaching behind",
    8: "Hair & makeup",
    9: "Talking to passenger",
}

CONFIDENCE_THRESHOLD = 0.55  # matches DistractionInferenceEngine.kt

CLASS_DIR_RE = re.compile(r"^c?(\d+)")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def preprocess_image(path: Path) -> np.ndarray:
    """Replicates DistractionInferenceEngine.kt:preprocessBitmap exactly:
    resize to 224x224, RGB, (channel/127.5) - 1.0, float32."""
    img = tf.io.read_file(str(path))
    img = tf.io.decode_image(img, channels=3, expand_animations=False)
    img = tf.image.resize(img, [INPUT_SIZE, INPUT_SIZE], method="bilinear")
    img = tf.cast(img, tf.float32)
    img = (img / 127.5) - 1.0
    return img.numpy()[np.newaxis, ...]  # [1, 224, 224, 3]


def load_interpreter(model_path: Path) -> tf.lite.Interpreter:
    if not model_path.exists():
        sys.exit(f"Model not found: {model_path}")
    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    return interpreter


def predict(interpreter: tf.lite.Interpreter, input_data: np.ndarray) -> tuple[int, float]:
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.set_tensor(input_details[0]["index"], input_data.astype(input_details[0]["dtype"]))
    interpreter.invoke()
    probs = interpreter.get_tensor(output_details[0]["index"])[0]
    top_class = int(np.argmax(probs))
    return top_class, float(probs[top_class])


def run_labeled_validation(interpreter: tf.lite.Interpreter, data_dir: Path) -> None:
    class_dirs = sorted(p for p in data_dir.iterdir() if p.is_dir())
    if not class_dirs:
        sys.exit(f"No class subfolders found under {data_dir}")

    confusion = {true_idx: {pred_idx: 0 for pred_idx in CLASS_LABELS} for true_idx in CLASS_LABELS}
    total = 0
    correct = 0

    for class_dir in class_dirs:
        match = CLASS_DIR_RE.match(class_dir.name)
        if not match:
            print(f"Skipping '{class_dir.name}' — folder name must start with the class index (e.g. c0_safe)")
            continue
        true_idx = int(match.group(1))
        if true_idx not in CLASS_LABELS:
            print(f"Skipping '{class_dir.name}' — class index {true_idx} is out of range 0-9")
            continue

        images = [p for p in class_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS]
        for img_path in images:
            input_data = preprocess_image(img_path)
            pred_idx, confidence = predict(interpreter, input_data)
            confusion[true_idx][pred_idx] += 1
            total += 1
            if pred_idx == true_idx:
                correct += 1
            else:
                print(f"  MISS  {img_path.name}: true={CLASS_LABELS[true_idx]!r} "
                      f"pred={CLASS_LABELS[pred_idx]!r} conf={confidence:.2f}")

    if total == 0:
        sys.exit("No labeled images found — check --data-dir layout in the script docstring.")

    print(f"\n=== Accuracy: {correct}/{total} = {100 * correct / total:.1f}% ===\n")
    print("Confusion matrix (rows=true, cols=predicted):")
    header = "true\\pred".ljust(12) + "".join(f"c{i}".rjust(5) for i in CLASS_LABELS)
    print(header)
    for true_idx in CLASS_LABELS:
        row = f"c{true_idx}".ljust(12) + "".join(str(confusion[true_idx][pred_idx]).rjust(5) for pred_idx in CLASS_LABELS)
        print(row)


def run_sanity_check(interpreter: tf.lite.Interpreter, sanity_dir: Path) -> None:
    images = [p for p in sanity_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS]
    if not images:
        sys.exit(f"No images found under {sanity_dir}")

    print("No labels supplied — printing predictions for manual eyeballing only.\n")
    for img_path in images:
        input_data = preprocess_image(img_path)
        pred_idx, confidence = predict(interpreter, input_data)
        label = CLASS_LABELS[pred_idx] if confidence >= CONFIDENCE_THRESHOLD else "NoDetection (low confidence)"
        print(f"{img_path.name}: {label} (conf={confidence:.2f})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help="Path to the .tflite model")
    parser.add_argument("--data-dir", type=Path, help="Labeled images folder (c0_.../c1_.../... layout)")
    parser.add_argument("--sanity-dir", type=Path, help="Unlabeled images folder for a manual eyeball check")
    args = parser.parse_args()

    interpreter = load_interpreter(args.model)
    print(f"Loaded model: {args.model}")

    if args.data_dir:
        run_labeled_validation(interpreter, args.data_dir)
    elif args.sanity_dir:
        run_sanity_check(interpreter, args.sanity_dir)
    else:
        parser.print_help()
        sys.exit("\nPass --data-dir (labeled) or --sanity-dir (unlabeled) — see script docstring for layout.")


if __name__ == "__main__":
    main()
