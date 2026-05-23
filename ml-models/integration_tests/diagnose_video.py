"""
Diagnose video predictions - shows detailed per-frame analysis
"""

import cv2
import numpy as np
import tensorflow as tf
import sys
from pathlib import Path

MODEL_PATH = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"

CLASS_NAMES = {
    0: 'Safe Driving',
    1: 'Texting - Right Hand',
    2: 'Phone Call - Right Hand',
    3: 'Texting - Left Hand',
    4: 'Phone Call - Left Hand',
    5: 'Operating Radio',
    6: 'Drinking',
    7: 'Reaching Behind',
    8: 'Hair and Makeup',
    9: 'Talking to Passenger'
}

# Load model
print("Loading model...")
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess_frame(frame):
    """Preprocess for MobileNetV2"""
    resized = cv2.resize(frame, (224, 224))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = (rgb.astype(np.float32) / 127.5) - 1.0
    return np.expand_dims(normalized, axis=0)

def predict(frame):
    """Get prediction with all confidences"""
    input_data = preprocess_frame(frame)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])[0]
    return output_data

if len(sys.argv) < 2:
    print("Usage: python diagnose_video.py <video_path>")
    sys.exit(1)

video_path = sys.argv[1]
print(f"\nAnalyzing: {video_path}\n")

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps if fps > 0 else 0

print(f"Video info:")
print(f"  FPS: {fps:.1f}")
print(f"  Total frames: {total_frames}")
print(f"  Duration: {duration:.1f} seconds\n")

frame_predictions = []
frame_num = 0

print("Analyzing frames...")
print("-" * 90)
print(f"{'Frame':<8} {'Time':<8} {'Top Prediction':<25} {'Conf':<8} {'c0':<8} {'c8':<8}")
print("-" * 90)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Get predictions
    output = predict(frame)
    top_class = np.argmax(output)
    top_conf = output[top_class] * 100

    frame_predictions.append({
        'frame': frame_num,
        'time': frame_num / fps if fps > 0 else 0,
        'predictions': output,
        'top_class': top_class,
        'top_conf': top_conf
    })

    # Print every 5 frames for 10-second video
    if frame_num % 5 == 0 or frame_num == total_frames - 1:
        time_sec = frame_num / fps if fps > 0 else 0
        c0_conf = output[0] * 100
        c8_conf = output[8] * 100

        marker = "⚠️" if top_class == 8 else "✓" if top_class == 0 else "?"

        print(f"{frame_num:<8} {time_sec:<8.1f} {CLASS_NAMES[top_class]:<25} {top_conf:<8.1f} {c0_conf:<8.1f} {c8_conf:<8.1f} {marker}")

    frame_num += 1

cap.release()

print("-" * 90)
print("\nSummary:")
print("=" * 90)

# Count predictions
pred_counts = {i: 0 for i in range(10)}
for pred in frame_predictions:
    pred_counts[pred['top_class']] += 1

print(f"\nPrediction distribution across {len(frame_predictions)} frames:\n")
for class_id, count in pred_counts.items():
    percentage = (count / len(frame_predictions)) * 100
    marker = " ⚠️ PROBLEM!" if class_id == 8 and count > len(frame_predictions) * 0.1 else ""
    print(f"  c{class_id} ({CLASS_NAMES[class_id]:30}): {count:4} frames ({percentage:5.1f}%){marker}")

# Average confidences
avg_c0 = np.mean([p['predictions'][0] for p in frame_predictions]) * 100
avg_c8 = np.mean([p['predictions'][8] for p in frame_predictions]) * 100

print(f"\nAverage confidences across all frames:")
print(f"  c0 (Safe Driving): {avg_c0:.1f}%")
print(f"  c8 (Hair/Makeup):  {avg_c8:.1f}%")

if avg_c8 > avg_c0:
    print(f"\n⚠️  PROBLEM: Model has higher average confidence for c8 than c0!")
    print(f"   This indicates the video content looks more like 'Hair/Makeup' than 'Safe Driving'")
    print(f"\n   Possible reasons:")
    print(f"   1. Driver's hand position near face")
    print(f"   2. Head angle or pose similar to hair/makeup training images")
    print(f"   3. AI-generated video artifacts")
    print(f"   4. Camera angle/framing different from training data")

print("\n" + "=" * 90)
