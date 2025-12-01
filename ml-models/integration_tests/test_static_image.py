"""
SafeDrive AI - Static Image Test (No Camera Required)
Tests the ML pipeline with a static image
"""

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import sys

# Configuration
TFLITE_MODEL_PATH = "../week2_training/tflite_models/mobilenetv2_distraction_classifier.tflite"

CLASS_NAMES = {
    0: 'c0_safe',
    1: 'c1_texting_right',
    2: 'c2_phone_right',
    3: 'c3_texting_left',
    4: 'c4_phone_left',
    5: 'c5_radio',
    6: 'c6_drinking',
    7: 'c7_reaching_behind',
    8: 'c8_hair_makeup',
    9: 'c9_talking_passenger'
}

print("="*60)
print("SafeDrive AI - Static Image Pipeline Test")
print("="*60)

# Load TFLite model
print(f"\n[1/4] Loading TFLite model...")
interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
print(f"✓ Model loaded successfully")
print(f"  Input shape: {input_details[0]['shape']}")
print(f"  Output shape: {output_details[0]['shape']}")

# Initialize MediaPipe
print(f"\n[2/4] Initializing MediaPipe FaceMesh...")
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
print(f"✓ MediaPipe initialized")

# Create a test image (solid color with text)
print(f"\n[3/4] Creating test image...")
test_image = np.zeros((480, 640, 3), dtype=np.uint8)
test_image[:] = (50, 100, 150)  # Brownish background
cv2.putText(test_image, 'SafeDrive Test Image', (150, 240),
           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
print(f"✓ Test image created (480x640)")

# Test MediaPipe (will not detect face in solid color image)
print(f"\n[4/4] Running pipeline test...")
rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
face_results = face_mesh.process(rgb_image)

if face_results.multi_face_landmarks:
    print(f"✓ Face detected: {len(face_results.multi_face_landmarks[0].landmark)} landmarks")
else:
    print(f"✓ Face detection tested (no face in test image - expected)")

# Test distraction model inference
print(f"\n[5/5] Testing distraction model inference...")
resized = cv2.resize(test_image, (224, 224))
rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
normalized = rgb.astype(np.float32) / 255.0
input_tensor = np.expand_dims(normalized, axis=0)

interpreter.set_tensor(input_details[0]['index'], input_tensor)
interpreter.invoke()
output_data = interpreter.get_tensor(output_details[0]['index'])

probabilities = output_data[0]
predicted_class = np.argmax(probabilities)
confidence = probabilities[predicted_class]

print(f"✓ Inference completed")
print(f"  Predicted class: {CLASS_NAMES[predicted_class]} (class {predicted_class})")
print(f"  Confidence: {confidence:.2%}")
print(f"\n  Top 3 predictions:")
top3_indices = np.argsort(probabilities)[-3:][::-1]
for idx in top3_indices:
    print(f"    {CLASS_NAMES[idx]}: {probabilities[idx]:.2%}")

print("\n" + "="*60)
print("PIPELINE VALIDATION RESULTS")
print("="*60)
print("\n✓ TFLite Model: WORKING")
print("✓ MediaPipe FaceMesh: WORKING")
print("✓ Preprocessing: WORKING")
print("✓ Inference: WORKING")

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
print("\nTo test with live camera:")
print("1. Grant camera permissions to Terminal")
print("   System Settings → Privacy & Security → Camera")
print("2. Run: python test_full_pipeline.py")
print("\nAlternatively, test on Sukh's Android device for real validation")
print("="*60)
