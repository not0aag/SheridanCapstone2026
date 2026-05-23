"""
SafeDrive AI - Demo Day Script
Perfect for live demonstrations to professors

HOW TO USE:
1. Sit in front of your webcam (or in a parked car)
2. Run this script
3. Act out different driving scenarios
4. The model will detect distractions in real-time!

DEMO SCENARIOS TO ACT OUT:
- Safe driving: Look forward, hands on imaginary wheel (10 seconds)
- Texting: Hold phone, look down and type (5 seconds)
- Phone call: Hold phone to ear (5 seconds)  
- Drinking: Take sips from water bottle (5 seconds)
- Reaching behind: Turn and reach for something (5 seconds)
"""

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import time
from collections import deque

# Configuration
TFLITE_MODEL_PATH = "../week3_finetuning/tflite_models/multiangle_model_91pct.tflite"
CONFIDENCE_THRESHOLD = 0.60  # Lower threshold for demo sensitivity

# Class names with user-friendly labels
CLASS_NAMES = {
    0: '✓ SAFE DRIVING',
    1: '⚠ TEXTING (Right Hand)',
    2: '⚠ PHONE CALL (Right)',
    3: '⚠ TEXTING (Left Hand)',
    4: '⚠ PHONE CALL (Left)',
    5: '⚠ OPERATING RADIO',
    6: '⚠ DRINKING',
    7: '⚠ REACHING BEHIND',
    8: '⚠ HAIR/MAKEUP',
    9: '⚠ TALKING TO PASSENGER'
}

# Color coding
SAFE_COLOR = (0, 255, 0)      # Green
WARNING_COLOR = (0, 165, 255)  # Orange
DANGER_COLOR = (0, 0, 255)     # Red

class DemoSystem:
    def __init__(self, model_path):
        print("\n" + "="*70)
        print("          SafeDrive AI - LIVE DEMO SYSTEM")
        print("="*70)
        
        # Initialize MediaPipe
        print("\n[1/3] Loading MediaPipe FaceMesh...")
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        print("      ✓ Face detection ready")
        
        # Load TFLite model
        print("\n[2/3] Loading Distraction Detection Model...")
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        print(f"      ✓ Model loaded (Size: 2.4 MB)")
        
        # Initialize tracking
        self.fps_history = deque(maxlen=30)
        self.detection_history = deque(maxlen=10)
        self.distraction_count = 0
        self.safe_count = 0
        self.start_time = time.time()
        
        print("\n[3/3] System Ready!")
        print("="*70)
    
    def preprocess_frame(self, frame):
        """Prepare frame for model - MobileNetV2 preprocessing"""
        resized = cv2.resize(frame, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        # MobileNetV2 expects input in range [-1, 1], not [0, 1]
        normalized = (rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)
    
    def predict(self, frame):
        """Run distraction detection"""
        input_tensor = self.preprocess_frame(frame)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        probabilities = output[0]
        predicted_class = np.argmax(probabilities)
        confidence = probabilities[predicted_class]
        
        return predicted_class, confidence, probabilities
    
    def draw_ui(self, frame, face_detected, predicted_class, confidence, fps):
        """Draw professional demo UI"""
        h, w = frame.shape[:2]
        
        # Semi-transparent overlay for top panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Title
        cv2.putText(frame, 'SafeDrive AI - Live Demo', (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        
        # FPS
        cv2.putText(frame, f'FPS: {int(fps)}', (w - 150, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Face detection status
        if face_detected:
            cv2.circle(frame, (20, 80), 10, SAFE_COLOR, -1)
            cv2.putText(frame, 'Driver Detected', (40, 88),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, SAFE_COLOR, 2)
        else:
            cv2.circle(frame, (20, 80), 10, DANGER_COLOR, -1)
            cv2.putText(frame, 'No Driver', (40, 88),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, DANGER_COLOR, 2)
        
        if face_detected and predicted_class is not None:
            # Current detection
            class_name = CLASS_NAMES[predicted_class]
            is_safe = predicted_class == 0
            color = SAFE_COLOR if is_safe else DANGER_COLOR
            
            # Large status display
            cv2.putText(frame, 'STATUS:', (20, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, class_name, (120, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Confidence bar
            bar_width = 300
            bar_height = 20
            bar_x, bar_y = 20, 140
            
            cv2.rectangle(frame, (bar_x, bar_y), 
                         (bar_x + bar_width, bar_y + bar_height),
                         (100, 100, 100), 2)
            
            fill_width = int(bar_width * confidence)
            cv2.rectangle(frame, (bar_x, bar_y),
                         (bar_x + fill_width, bar_y + bar_height),
                         color, -1)
            
            cv2.putText(frame, f'{confidence:.1%}', (bar_x + bar_width + 10, bar_y + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Alert banner if distracted
            if not is_safe and confidence > CONFIDENCE_THRESHOLD:
                cv2.rectangle(frame, (0, h-80), (w, h), DANGER_COLOR, -1)
                cv2.putText(frame, '!!! DISTRACTION DETECTED !!!',
                           (w//2 - 250, h - 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        # Statistics panel (bottom left)
        elapsed = int(time.time() - self.start_time)
        cv2.putText(frame, f'Session: {elapsed}s', (20, h - 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f'Safe: {self.safe_count}', (20, h - 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, SAFE_COLOR, 1)
        cv2.putText(frame, f'Distractions: {self.distraction_count}', (20, h - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, DANGER_COLOR, 1)
        
        return frame
    
    def run_demo(self):
        """Main demo loop"""
        print("\n" + "="*70)
        print("                    DEMO INSTRUCTIONS")
        print("="*70)
        print("\n  ACT OUT THESE SCENARIOS:")
        print("    1. ✓ Safe Driving - Look forward, hands on wheel")
        print("    2. ⚠ Texting - Look down at phone, type")
        print("    3. ⚠ Phone Call - Hold phone to ear")
        print("    4. ⚠ Drinking - Take sips from bottle")
        print("    5. ⚠ Reaching Behind - Turn and reach back")
        print("\n  CONTROLS:")
        print("    Press 'r' - Reset statistics")
        print("    Press 'q' - Quit demo")
        print("\n" + "="*70)
        print("\nStarting camera in 3 seconds...")
        time.sleep(3)
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("\n❌ ERROR: Could not open camera")
            print("   Fix: Grant camera permissions in System Settings")
            return
        
        # Set camera to 720p for better quality
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        print("✓ Camera started! Demo is LIVE!\n")
        
        while cap.isOpened():
            frame_start = time.time()
            success, frame = cap.read()
            if not success:
                break
            
            # Process frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_results = self.face_mesh.process(rgb_frame)
            
            face_detected = face_results.multi_face_landmarks is not None
            predicted_class = None
            confidence = 0.0
            
            if face_detected:
                predicted_class, confidence, _ = self.predict(frame)
                
                # Track statistics
                if predicted_class == 0:
                    self.safe_count += 1
                elif confidence > CONFIDENCE_THRESHOLD:
                    self.distraction_count += 1
            
            # Calculate FPS
            fps = 1.0 / (time.time() - frame_start)
            self.fps_history.append(fps)
            
            # Draw UI
            frame = self.draw_ui(frame, face_detected, predicted_class, confidence, fps)
            
            # Display
            cv2.imshow('SafeDrive AI - DEMO', frame)
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.distraction_count = 0
                self.safe_count = 0
                self.start_time = time.time()
                print("✓ Statistics reset")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Final report
        avg_fps = np.mean(self.fps_history)
        total_time = int(time.time() - self.start_time)
        
        print("\n" + "="*70)
        print("                    DEMO SESSION REPORT")
        print("="*70)
        print(f"\n  Session Duration: {total_time} seconds")
        print(f"  Average FPS: {avg_fps:.1f}")
        print(f"  Safe Driving Frames: {self.safe_count}")
        print(f"  Distraction Detections: {self.distraction_count}")
        print("\n" + "="*70)

def main():
    try:
        demo = DemoSystem(TFLITE_MODEL_PATH)
        demo.run_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
