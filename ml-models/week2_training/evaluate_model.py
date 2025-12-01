import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
import config
import dataset_loader
import os


def evaluate_keras_model(model_path):
    """Evaluate Keras model on validation set."""
    print("Loading Keras model...")
    model = tf.keras.models.load_model(model_path)

    # Prepare validation dataset
    df = dataset_loader.load_driver_mapping()
    _, val_df, _, _ = dataset_loader.split_by_driver(df)
    val_paths, val_labels = dataset_loader.create_file_paths_and_labels(val_df)
    val_dataset = dataset_loader.create_dataset(
        val_paths, val_labels, is_training=False)

    # Evaluate
    print("\nEvaluating on validation set...")
    results = model.evaluate(val_dataset, verbose=1)

    print(f"\nValidation Loss: {results[0]:.4f}")
    print(f"Validation Accuracy: {results[1]:.4f}")
    print(f"Validation Top-3 Accuracy: {results[2]:.4f}")

    # Get predictions for confusion matrix
    print("\nGenerating predictions...")
    y_true = []
    y_pred = []

    for images, labels in val_dataset:
        predictions = model.predict(images, verbose=0)
        y_true.extend(labels.numpy())
        y_pred.extend(np.argmax(predictions, axis=1))

    # Classification report
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=config.CLASS_NAMES))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    plot_confusion_matrix(cm, config.CLASS_NAMES)

    return y_true, y_pred


def plot_confusion_matrix(cm, class_names):
    """Plot confusion matrix."""
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix - SafeDrive Distraction Detection')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()

    output_path = os.path.join(config.MODEL_SAVE_PATH, 'confusion_matrix.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Confusion matrix saved to: {output_path}")
    plt.close()


def benchmark_inference_speed():
    """Benchmark TFLite model inference speed on CPU."""
    tflite_path = os.path.join(
        config.MODEL_SAVE_PATH, 'mobilenetv2_int8.tflite')

    print(f"\nBenchmarking TFLite model: {tflite_path}")

    # Load interpreter
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()

    # Create dummy input
    dummy_input = np.random.randint(
        0, 255, size=input_details[0]['shape'], dtype=np.uint8)

    # Warmup
    for _ in range(10):
        interpreter.set_tensor(input_details[0]['index'], dummy_input)
        interpreter.invoke()

    # Benchmark
    import time
    num_runs = 100
    times = []

    for _ in range(num_runs):
        interpreter.set_tensor(input_details[0]['index'], dummy_input)
        start = time.time()
        interpreter.invoke()
        times.append((time.time() - start) * 1000)  # ms

    avg_time = np.mean(times)
    std_time = np.std(times)
    min_time = np.min(times)
    max_time = np.max(times)
    fps = 1000 / avg_time

    print(f"\nInference Benchmarks ({num_runs} runs):")
    print(f"  Average: {avg_time:.2f} ms (±{std_time:.2f} ms)")
    print(f"  Min: {min_time:.2f} ms")
    print(f"  Max: {max_time:.2f} ms")
    print(f"  FPS: {fps:.1f}")
    print(f"\nTarget: <40ms (25+ FPS)")
    print(f"Status: {'✅ PASS' if avg_time < 40 else '❌ FAIL'}")


def main():
    """Main evaluation pipeline."""
    model_path = os.path.join(config.MODEL_SAVE_PATH, 'mobilenetv2_final.h5')

    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        print("Please train the model first using train_mobilenetv2.py")
        return

    # Evaluate Keras model
    y_true, y_pred = evaluate_keras_model(model_path)

    # Benchmark TFLite model
    tflite_path = os.path.join(
        config.MODEL_SAVE_PATH, 'mobilenetv2_int8.tflite')
    if os.path.exists(tflite_path):
        benchmark_inference_speed()
    else:
        print(f"\nTFLite model not found. Run convert_to_tflite.py first.")


if __name__ == "__main__":
    main()
