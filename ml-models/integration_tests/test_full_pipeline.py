"""
SafeDrive AI - Full ML Pipeline Integration Test
Tests: Camera → MediaPipe FaceMesh → Distraction Detection
Author: Harrison Daniel Dsouza
"""

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import time
from collections import deque

# Configuration
TFLITE_MODEL_PATH = "../week2_training/tflite_models/mobilenetv2_distraction_classifier.tflite"
TARGET_FPS = 30
CONFIDENCE_THRESHOLD = 0.70

# Class names
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

class SafeDrivePipeline:
    def __init__(self, model_path):
        # Initialize MediaPipe FaceMesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Load TFLite model
        print(f"Loading TFLite model from: {model_path}")
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        # Get input/output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        print(f"Input shape: {self.input_details[0]['shape']}")
        print(f"Output shape: {self.output_details[0]['shape']}")
        
        # Performance tracking
        self.fps_history = deque(maxlen=30)
        self.inference_times = deque(maxlen=30)
        
    def preprocess_frame(self, frame):
        """Resize and normalize frame for model input"""
        # Resize to 224x224
        resized = cv2.resize(frame, (224, 224))
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        # Normalize to [0, 1]
        normalized = rgb.astype(np.float32) / 255.0
        # Add batch dimension
        input_tensor = np.expand_dims(normalized, axis=0)
        return input_tensor
    
    def predict_distraction(self, frame):
        """Run distraction detection on frame"""
        start_time = time.time()
        
        # Preprocess
        input_tensor = self.preprocess_frame(frame)
        
        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        # Get prediction
        probabilities = output_data[0]
        predicted_class = np.argmax(probabilities)
        confidence = probabilities[predicted_class]
        
        inference_time = (time.time() - start_time) * 1000  # ms
        self.inference_times.append(inference_time)
        
        return predicted_class, confidence, probabilities
    
    def process_frame(self, frame):
        """Full pipeline: Face detection → Distraction classification"""
        frame_start = time.time()
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Face detection
        face_results = self.face_mesh.process(rgb_frame)
        
        face_detected = False
        predicted_class = None
        confidence = 0.0
        
        if face_results.multi_face_landmarks:
            face_detected = True
            # Run distraction detection only if face is detected
            predicted_class, confidence, probabilities = self.predict_distraction(frame)
        
        # Calculate FPS
        fps = 1.0 / (time.time() - frame_start)
        self.fps_history.append(fps)
        
        return face_detected, predicted_class, confidence, fps
    
    def get_stats(self):
        """Get performance statistics"""
        avg_fps = np.mean(self.fps_history) if self.fps_history else 0
        avg_inference = np.mean(self.inference_times) if self.inference_times else 0
        return {
            'avg_fps': avg_fps,
            'avg_inference_ms': avg_inference,
            'min_fps': np.min(self.fps_history) if self.fps_history else 0,
            'max_fps': np.max(self.fps_history) if self.fps_history else 0
        }

def main():
    print("="*60)
    print("SafeDrive AI - Full ML Pipeline Test")
    print("="*60)
    
    # Initialize pipeline
    pipeline = SafeDrivePipeline(TFLITE_MODEL_PATH)
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open webcam")
        return
    
    print("\nStarting pipeline test...")
    print("Press 'q' to quit, 's' to see statistics")
    print("-"*60)
    
    frame_count = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        frame_count += 1
        
        # Process frame
        face_detected, predicted_class, confidence, fps = pipeline.process_frame(frame)
        
        # Display info on frame
        h, w = frame.shape[:2]
        
        # FPS
        cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Face detection status
        face_status = "Face: DETECTED" if face_detected else "Face: NOT DETECTED"
        color = (0, 255, 0) if face_detected else (0, 0, 255)
        cv2.putText(frame, face_status, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Distraction detection
        if face_detected and predicted_class is not None:
            class_name = CLASS_NAMES[predicted_class]
            cv2.putText(frame, f'Class: {class_name}', (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f'Confidence: {confidence:.2%}', (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Alert if distracted
            if predicted_class != 0 and confidence > CONFIDENCE_THRESHOLD:
                cv2.putText(frame, '!!! DISTRACTION ALERT !!!', (10, h - 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        
        # Show frame
        cv2.imshow('SafeDrive AI - Full Pipeline Test', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            stats = pipeline.get_stats()
            print(f"\n--- Performance Stats (Frame {frame_count}) ---")
            print(f"Average FPS: {stats['avg_fps']:.2f}")
            print(f"FPS Range: {stats['min_fps']:.2f} - {stats['max_fps']:.2f}")
            print(f"Avg Inference Time: {stats['avg_inference_ms']:.2f} ms")
            print("-"*60)
    
    # Final statistics
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "="*60)
    print("FINAL PERFORMANCE REPORT")
    print("="*60)
    
    stats = pipeline.get_stats()
    print(f"\nTotal Frames Processed: {frame_count}")
    print(f"\nPerformance Metrics:")
    print(f"  Average FPS: {stats['avg_fps']:.2f}")
    print(f"  Min FPS: {stats['min_fps']:.2f}")
    print(f"  Max FPS: {stats['max_fps']:.2f}")
    print(f"  Avg Inference Time: {stats['avg_inference_ms']:.2f} ms")
    print(f"\nTargets:")
    print(f"  FPS Target: ≥25 FPS {'✓ PASS' if stats['avg_fps'] >= 25 else '✗ FAIL'}")
    print(f"  Latency Target: <40ms {'✓ PASS' if stats['avg_inference_ms'] < 40 else '✗ FAIL'}")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
