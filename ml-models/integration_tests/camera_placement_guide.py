"""
SafeDrive AI - Camera Placement Guide
Shows users how to properly mount their phone for accurate detection

This creates an AR-style overlay to guide users in placing their camera correctly
"""

import cv2
import numpy as np
import mediapipe as mp

# Configuration
GUIDE_DURATION = 10  # seconds to show guide
TARGET_ANGLE = 30  # degrees upward from horizontal

# Colors
GREEN = (0, 255, 0)
YELLOW = (0, 255, 255)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
BLUE = (255, 165, 0)

class CameraPlacementGuide:
    """Guide user to position camera correctly"""

    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def estimate_head_angle(self, landmarks, frame_shape):
        """Estimate if camera is looking up at driver (correct) or straight (incorrect)"""
        h, w = frame_shape[:2]

        # Key landmarks: nose tip, chin, forehead
        nose_tip = landmarks[1]
        chin = landmarks[152]
        forehead = landmarks[10]

        # Calculate vertical position of nose relative to face
        nose_y = nose_tip.y * h
        chin_y = chin.y * h
        forehead_y = forehead.y * h

        face_height = chin_y - forehead_y
        nose_relative = (nose_y - forehead_y) / face_height if face_height > 0 else 0.5

        # If camera is low (dashboard position), nose appears lower in face (correct)
        # If camera is eye-level, nose appears centered (incorrect)
        is_correct_angle = nose_relative > 0.55  # Nose in lower half = good angle

        return is_correct_angle, nose_relative

    def draw_placement_guide(self, frame, face_detected, is_correct_angle=False, nose_relative=0.5):
        """Draw visual guide for camera placement"""
        h, w = frame.shape[:2]

        # Semi-transparent overlay
        overlay = frame.copy()

        # Top banner
        cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Title
        cv2.putText(frame, 'SafeDrive AI - Camera Setup', (20, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, WHITE, 2)

        # Instructions panel
        cv2.rectangle(overlay, (10, 120), (w-10, 400), (40, 40, 40), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        y_pos = 160
        line_height = 40

        cv2.putText(frame, 'CAMERA PLACEMENT INSTRUCTIONS:', (30, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2)
        y_pos += line_height

        # Step 1
        color = GREEN if is_correct_angle else RED
        status = "CORRECT!" if is_correct_angle else "ADJUST POSITION"
        cv2.putText(frame, f'1. Mount phone on WINDSHIELD or CENTER DASH', (30, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
        y_pos += line_height

        cv2.putText(frame, f'2. Position to see driver from front-right angle', (30, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
        y_pos += line_height

        cv2.putText(frame, f'3. Ensure steering wheel + upper body visible', (30, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
        y_pos += line_height

        # Status
        cv2.putText(frame, f'Status: {status}', (30, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Visual diagram
        diagram_y = 450
        diagram_h = 250

        # Draw side view diagram
        cv2.rectangle(overlay, (10, diagram_y), (w-10, diagram_y + diagram_h), (40, 40, 40), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        center_x = w // 2

        # WRONG setup (left side)
        wrong_x = w // 4
        cv2.putText(frame, '✗ WRONG', (wrong_x - 60, diagram_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2)

        # Draw eye-level camera (wrong)
        cv2.rectangle(frame, (wrong_x - 30, diagram_y + 80), (wrong_x - 10, diagram_y + 100), RED, -1)
        cv2.putText(frame, 'Eye Level', (wrong_x - 70, diagram_y + 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, RED, 1)

        # Draw person
        cv2.circle(frame, (wrong_x + 60, diagram_y + 70), 20, WHITE, 2)  # Head
        cv2.line(frame, (wrong_x + 60, diagram_y + 90), (wrong_x + 60, diagram_y + 150), WHITE, 2)  # Body

        # Arrow showing straight view
        cv2.arrowedLine(frame, (wrong_x - 10, diagram_y + 90), (wrong_x + 40, diagram_y + 80), RED, 2)

        # CORRECT setup (right side)
        correct_x = 3 * w // 4
        cv2.putText(frame, '✓ CORRECT', (correct_x - 80, diagram_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 2)

        # Draw dashboard mount (correct)
        cv2.rectangle(frame, (correct_x - 80, diagram_y + 160), (correct_x - 50, diagram_y + 180), GREEN, -1)
        cv2.putText(frame, 'Dashboard', (correct_x - 120, diagram_y + 195),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, GREEN, 1)

        # Draw person
        cv2.circle(frame, (correct_x + 40, diagram_y + 70), 20, WHITE, 2)  # Head
        cv2.line(frame, (correct_x + 40, diagram_y + 90), (correct_x + 40, diagram_y + 150), WHITE, 2)  # Body

        # Arrow showing upward angle (30-40 degrees)
        cv2.arrowedLine(frame, (correct_x - 50, diagram_y + 170), (correct_x + 20, diagram_y + 80), GREEN, 2)
        cv2.putText(frame, '30-40°', (correct_x - 50, diagram_y + 150),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, GREEN, 1)

        # Bottom instructions
        cv2.putText(frame, 'Press SPACE when ready | Press Q to quit', (w//2 - 250, h - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, YELLOW, 2)

        return frame

    def run(self):
        """Run the camera placement guide"""
        cap = cv2.VideoCapture(0)

        print("\n" + "="*70)
        print("SAFEDRIVE AI - CAMERA PLACEMENT GUIDE")
        print("="*70)
        print("\nThis guide will help you position your camera correctly.")
        print("\nFor best results:")
        print("  1. Mount your phone on the dashboard (low position)")
        print("  2. Angle it UPWARD toward the driver's seat")
        print("  3. The camera should 'look up' at the driver, not straight")
        print("\nStarting guide...")
        print("="*70 + "\n")

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            # Flip for mirror view
            frame = cv2.flip(frame, 1)

            # Detect face
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            face_detected = False
            is_correct_angle = False
            nose_relative = 0.5

            if results.multi_face_landmarks:
                face_detected = True
                landmarks = results.multi_face_landmarks[0].landmark
                is_correct_angle, nose_relative = self.estimate_head_angle(landmarks, frame.shape)

            # Draw guide
            frame = self.draw_placement_guide(frame, face_detected, is_correct_angle, nose_relative)

            # Show frame
            cv2.imshow('SafeDrive AI - Camera Setup Guide', frame)

            key = cv2.waitKey(5) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' ') and is_correct_angle:
                print("\n✓ Camera positioned correctly!")
                print("You can now start the demo.\n")
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    guide = CameraPlacementGuide()
    guide.run()
