# perclos_demo.py
import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance as dist  # Used for EAR calculation

# MediaPipe Face Mesh setup
mp_face_mesh = mp.solutions.face_mesh

# Eye landmarks indices from MediaPipe FaceMesh (6 points per eye)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def eye_aspect_ratio(landmarks, eye_indices):
    """Calculate EAR for given eye landmarks"""
    # Get normalized coordinates (0 to 1)
    eye = np.array([(landmarks[i].x, landmarks[i].y) for i in eye_indices])

    # Vertical eye distances (p2-p6 and p3-p5)
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # Horizontal eye distance (p1-p4)
    C = dist.euclidean(eye[0], eye[3])

    # EAR formula
    ear = (A + B) / (2.0 * C)
    return ear


def calculate_perclos(ear_history, threshold):
    """Calculate PERCLOS (Percentage of Eyelid Closure)"""
    if len(ear_history) == 0:
        return 0
    closed_frames = sum(1 for ear in ear_history if ear < threshold)
    return (closed_frames / len(ear_history)) * 100


# Parameters
EAR_THRESHOLD = 0.2    # !!! TUNE THIS VALUE if beeping doesn't work !!!
PERCLOS_THRESHOLD = 30  # Drowsy if >80% of the last 100 frames were 'closed'
WINDOW_SIZE = 100      # Analyze last 100 frames (approx. 3-4 seconds)

ear_history = []
frame_count = 0

with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as face_mesh:
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        frame_count += 1

        # Convert BGR to RGB for MediaPipe processing
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image)
        # Convert RGB back to BGR for OpenCV display (Fix #1: COLOR_RGB2BGR)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        avg_ear = 0
        perclos = 0
        eye_status = "OPEN"

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            left_ear = eye_aspect_ratio(landmarks, LEFT_EYE)
            right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE)

            # Fix #2: Corrected variable name from right_right_ear to right_ear
            avg_ear = (left_ear + right_ear) / 2.0

            # --- BEEP AND STATUS LOGIC ---
            if avg_ear < EAR_THRESHOLD:
                print('\a')  # Terminal beep
                eye_status = "CLOSED"

            ear_history.append(avg_ear)
            if len(ear_history) > WINDOW_SIZE:
                ear_history.pop(0)

            perclos = calculate_perclos(ear_history, EAR_THRESHOLD)

            # Draw tracking circle
            h, w, _ = image.shape
            p = landmarks[RIGHT_EYE[0]]
            cv2.circle(image, (int(p.x * w), int(p.y * h)), 5, (255, 0, 0), -1)

        # Display metrics
        cv2.putText(image, f'EAR: {avg_ear:.3f} ({eye_status})',
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(image, f'PERCLOS: {perclos:.1f}%', (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Drowsiness Alert
        if perclos > PERCLOS_THRESHOLD and len(ear_history) >= WINDOW_SIZE:
            cv2.putText(image, 'DROWSY!', (w - 150, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        cv2.imshow('PERCLOS Drowsiness Detection', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
