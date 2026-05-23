"""
Test Class Weights Model on AI-Generated Videos
Quick comparison script
"""

import cv2
import numpy as np
import tensorflow as tf
import sys
from pathlib import Path

MODEL_PATH = "../week3_finetuning/tflite_models/class_weights_model_91pct.tflite"

CLASS_NAMES = {
    0: 'Safe Driving',
    1: 'Texting - Right',
    2: 'Phone - Right',
    3: 'Texting - Left',
    4: 'Phone - Left',
    5: 'Operating Radio',
    6: 'Drinking',
    7: 'Reaching Behind',
    8: 'Hair/Makeup',
    9: 'Talking Passenger'
}

# Load model
print("Loading class weights model (90.97% accuracy)...")
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
print("✓ Model loaded\n")

def preprocess(frame):
    resized = cv2.resize(frame, (224, 224))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = (rgb.astype(np.float32) / 127.5) - 1.0
    return np.expand_dims(normalized, axis=0)

def predict(frame):
    input_data = preprocess(frame)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])[0]

    top_class = np.argmax(output_data)
    confidence = output_data[top_class] * 100
    return top_class, confidence, output_data

if len(sys.argv) < 2:
    print("Usage: python test_class_weights_model.py <video_path>")
    sys.exit(1)

video_path = Path(sys.argv[1])
print(f"Testing on: {video_path.name}\n")

cap = cv2.VideoCapture(str(video_path))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

stats = {i: 0 for i in range(10)}
frame_num = 0

print("Analyzing...")
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_num += 1
    if frame_num % 5 == 0:  # Sample every 5th frame
        pred_class, conf, _ = predict(frame)
        stats[pred_class] += 1

cap.release()

print("\n" + "="*70)
print("CLASS WEIGHTS MODEL RESULTS")
print("="*70 + "\n")
print(f"Video: {video_path.name}")
print(f"Frames sampled: {sum(stats.values())}/{total_frames}\n")

print("Predictions:")
for class_id, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        pct = (count / sum(stats.values())) * 100
        marker = "✓" if class_id == 0 else "⚠" if class_id == 8 else " "
        print(f"{marker} c{class_id} {CLASS_NAMES[class_id]:25}: {count:4} frames ({pct:5.1f}%)")

# Highlight key classes
print(f"\nKey metrics:")
print(f"  Safe Driving (c0):  {(stats[0]/sum(stats.values())*100):.1f}%")
print(f"  Hair/Makeup (c8):   {(stats[8]/sum(stats.values())*100):.1f}%")

if stats[8] > stats[0] and stats[8] > 10:
    print(f"\n⚠️  WARNING: Still biased toward hair/makeup!")
elif stats[0] > sum(stats.values()) * 0.5:
    print(f"\n✓ Good: Detecting safe driving properly")

print("\n" + "="*70)
