"""Convert the canonical distraction classifier to Core ML for the iOS app.

Steps:
1. Verify which Keras .h5 file produced class_weights_model_91pct.tflite
   by comparing outputs on identical random inputs.
2. Convert that .h5 to an .mlpackage with the [-1, 1] image preprocessing
   baked in (scale = 1/127.5, bias = -1), so Swift code can feed camera
   pixel buffers directly without manual normalization.
3. Verify the Core ML model's outputs match the TFLite model's outputs.

Run with the safedrive_ml venv python:
    safedrive_ml/bin/python tools/convert_to_coreml.py
"""

import os
import sys

import numpy as np
import tensorflow as tf
import coremltools as ct

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TFLITE_PATH = os.path.join(
    REPO, "ml-models/week3_finetuning/tflite_models/class_weights_model_91pct.tflite"
)
H5_CANDIDATES = [
    os.path.join(REPO, "ml-models/week3_finetuning/models/best_model_improved.h5"),
    os.path.join(REPO, "ml-models/week3_finetuning/models/mobilenetv2_improved_final.h5"),
]
# Named DistractionModel (not DistractionClassifier) because Xcode generates a
# Swift class from the package name, and DistractionClassifier.swift already
# defines the wrapper class.
OUT_PATH = os.path.join(REPO, "ios/SafeDriveAI/Models/DistractionModel.mlpackage")

CLASS_NAMES = [
    "Safe", "Texting-right", "Phone-right", "Texting-left", "Phone-left",
    "Radio", "Drinking", "Reaching-behind", "Makeup", "Talking-passenger",
]


def tflite_predict(path, batch):
    interp = tf.lite.Interpreter(model_path=path)
    interp.allocate_tensors()
    inp = interp.get_input_details()[0]
    out = interp.get_output_details()[0]
    results = []
    for i in range(batch.shape[0]):
        interp.set_tensor(inp["index"], batch[i : i + 1])
        interp.invoke()
        results.append(interp.get_tensor(out["index"])[0].copy())
    return np.array(results)


def main():
    rng = np.random.default_rng(42)
    # Random inputs already normalized to [-1, 1], as the models expect.
    test_batch = rng.uniform(-1.0, 1.0, size=(8, 224, 224, 3)).astype(np.float32)

    print("Running TFLite reference predictions...")
    tflite_out = tflite_predict(TFLITE_PATH, test_batch)

    source_model, source_path = None, None
    for h5 in H5_CANDIDATES:
        print(f"Testing candidate: {os.path.basename(h5)}")
        model = tf.keras.models.load_model(h5)
        keras_out = model.predict(test_batch, verbose=0)
        max_diff = float(np.abs(keras_out - tflite_out).max())
        agree = (keras_out.argmax(1) == tflite_out.argmax(1)).mean()
        print(f"  max output diff vs tflite: {max_diff:.6f}, argmax agreement: {agree:.0%}")
        # The TFLite export is float16-quantized, so small output drift vs the
        # float32 .h5 is expected. Class agreement is the real requirement.
        if max_diff < 0.05 and agree == 1.0:
            source_model, source_path = model, h5
            break

    if source_model is None:
        sys.exit("ERROR: no .h5 candidate matches the canonical TFLite model.")
    print(f"\nMatched source model: {source_path}")

    print("Converting to Core ML...")
    mlmodel = ct.convert(
        source_model,
        source="tensorflow",
        convert_to="mlprogram",
        inputs=[
            ct.ImageType(
                shape=(1, 224, 224, 3),
                scale=1.0 / 127.5,
                bias=[-1.0, -1.0, -1.0],
                color_layout=ct.colorlayout.RGB,
            )
        ],
        compute_units=ct.ComputeUnit.ALL,
        minimum_deployment_target=ct.target.iOS16,
    )

    mlmodel.short_description = (
        "SafeDrive AI distraction classifier (MobileNetV2, State Farm 10-class). "
        "Secondary confirmation signal only — see integration notes."
    )
    mlmodel.user_defined_metadata["classes"] = ",".join(CLASS_NAMES)
    mlmodel.save(OUT_PATH)
    print(f"Saved: {OUT_PATH}")

    # Parity check: Core ML takes a raw [0, 255] image (PIL), preprocessing is
    # baked in, so rebuild the same test inputs as uint8 images.
    print("\nVerifying Core ML output parity...")
    from PIL import Image

    raw_uint8 = ((test_batch + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
    spec = mlmodel.get_spec()
    spec_in_name = spec.description.input[0].name
    spec_out_name = spec.description.output[0].name
    coreml_out = []
    for i in range(raw_uint8.shape[0]):
        img = Image.fromarray(raw_uint8[i])
        pred = mlmodel.predict({spec_in_name: img})
        coreml_out.append(np.array(pred[spec_out_name]).reshape(-1))
    coreml_out = np.array(coreml_out)

    max_diff = float(np.abs(coreml_out - tflite_out).max())
    agree = (coreml_out.argmax(1) == tflite_out.argmax(1)).mean()
    print(f"Core ML vs TFLite: max diff {max_diff:.6f}, argmax agreement {agree:.0%}")
    for i in range(coreml_out.shape[0]):
        print(
            f"  sample {i}: coreml={CLASS_NAMES[coreml_out[i].argmax()]:>17s} "
            f"({coreml_out[i].max():.3f})  tflite={CLASS_NAMES[tflite_out[i].argmax()]:>17s} "
            f"({tflite_out[i].max():.3f})"
        )
    if agree < 1.0 or max_diff > 0.05:
        sys.exit("ERROR: Core ML output does not match TFLite closely enough.")
    print("\nConversion verified OK.")


if __name__ == "__main__":
    main()
