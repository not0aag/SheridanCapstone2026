"""
Debug script to see ALL class probabilities in real-time
This helps understand what the model is "thinking"
"""

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import time

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

print("Loading model...")
interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

print("\nStarting camera...")
print("This will show you ALL probabilities for each class")
print("Press 'q' to quit\n")

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    
    # Get prediction
    resized = cv2.resize(frame, (224, 224))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = rgb.astype(np.float32) / 255.0
    input_tensor = np.expand_dims(normalized, axis=0)
    
    interpreter.set_tensor(input_details[0]['index'], input_tensor)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    
    probabilities = output_data[0]
    predicted_class = np.argmax(probabilities)
    
    # Show ALL probabilities on screen
    y_pos = 30
    for i in range(10):
        prob = probabilities[i]
        color = (0, 255, 0) if i == predicted_class else (255, 255, 255)
        text = f"{CLASS_NAMES[i]}: {prob:.1%}"
        cv2.putText(frame, text, (10, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        y_pos += 25
    
    # Highlight prediction
    cv2.putText(frame, f"PREDICTED: {CLASS_NAMES[predicted_class]}", 
               (10, y_pos + 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow('Debug - All Probabilities', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
