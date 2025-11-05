# SafeDrive AI: Week 1 ML Performance and Requirements Report

**Date:** November 5, 2025
**Author:** Harrison Daniel Dsouza (ML & AI Specialist)
**Objective:** Document the foundation, performance benchmarks, and core algorithm validation for the Phase 1 Prototype ML components, completing tasks H1-W1-2, H1-W1-3, and H1-W1-5.

## 1. Foundation & Environment Status

The core ML development environment (`safedrive_ml_env`) is fully set up and stable. All required dependencies (MediaPipe, OpenCV, NumPy, SciPy) have been successfully integrated and validated for use with the smartphone's camera feed.

## 2. Face Tracking and Benchmark (H1-W1-2)

**Component:** Real-time face detection and 468-point landmark tracking using MediaPipe Face Mesh.
**Requirement:** Target performance is **25 - 30 Frames Per Second (FPS)** for real-time operation on mobile devices.

| Metric          | Result              | Status        | Notes                                                                                                                                     |
| --------------- | ------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Average FPS** | **62.99 FPS**       | **✓ Success** | Significantly exceeds the target requirement, ensuring high reliability and a generous processing buffer for subsequent detection models. |
| **Model**       | MediaPipe Face Mesh | **Confirmed** | Provides robust, 3D landmark detection across various lighting and face orientations.                                                     |

## 3. Drowsiness Monitoring Validation (H1-W1-5)

**Algorithm:** Percentage of Eyelid Closure Over Time (PERCLOS) calculated via the Eye Aspect Ratio (EAR).
**Validation Goal:** Confirm the ability to detect sustained eye closure and trigger an alert based on a rolling average.

| Validation Point    | Status        | Metric / Threshold                                                                                                                        |
| ------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **EAR Calculation** | **✓ Success** | Confirmed instantaneous detection (beeping) when eyes are closed.                                                                         |
| **EAR Threshold**   | $\approx 0.2$ | Successfully distinguishes between open and closed eyes.                                                                                  |
| **PERCLOS Alert**   | **✓ Success** | The **"DROWSY!"** alert triggers when the closed-eye percentage exceeds the set threshold (for testing, $30\%$ over the last 100 frames). |

This validation confirms the core PERCLOS logic is sound for detecting micro-sleeps and fatigue.

## 4. Distracted Driving Model Requirements (H1-W1-3)

**Goal:** Establish requirements and select an initial lightweight model architecture for classifying driver distraction in real-time.
**Dataset Reference:** State Farm Distracted Driver Detection Dataset.

### A. Distraction Classes

The system will target the following **10 classes of distraction**, which cover primary sources of inattention:

1.  Safe Driving (C0)

2.  Texting - Right (C1)

3.  Talking on Phone - Right (C2)

4.  Texting - Left (C3)

5.  Talking on Phone - Left (C4)

6.  Operating Radio/AC (C5)

7.  Drinking (C6)

8.  Reaching Behind (C7)

9.  Hair and Makeup (C8)

10. Talking to Passenger (C9)

### B. Initial Model Selection

To ensure the model can achieve high speed on a mobile GPU while maintaining sufficient accuracy ($85\%-90\%$), the initial architecture chosen for training is:

-   **Model:** **MobileNetV2**

-   **Rationale:** Known for its inverted residual structure and depthwise separable convolutions, MobileNetV2 delivers efficient, high-performance inference. It is specifically chosen for its small size ($\approx 14$ MB) and low latency, which is essential for real-time video processing across the 10 defined classes on low-power mobile devices.

### C. Training Data Handling and Calculations

To ensure model stability and optimal performance on MobileNetV2, the following requirements are established for the training data (State Farm Dataset):

1. **Input Image Size:** All input images will be uniformly resized to a standard $224 \times 224$ pixels. This size is the standard input requirement for MobileNetV2 and ensures consistent memory usage on mobile devices.

2. **Data Augmentation:** Basic augmentation (rotation, slight zoom, horizontal flip) will be applied to prevent overfitting due to the dataset's high similarity in background context.

3. **Normalization:** All image data will be normalized to the range $[0, 1]$ during preprocessing to match the expected input range of the pre-trained MobileNetV2 weights.

4. **Loss Function:** Categorical Cross-Entropy loss will be used, given the 10 mutually exclusive output classes.

## Summary of Week 1 Achievements

All foundational tasks for the ML component are complete. The project is well-positioned to move into **Week 2: Training and Integration** with a validated face tracking pipeline and a defined model architecture for distraction detection.
