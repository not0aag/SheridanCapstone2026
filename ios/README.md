# SafeDrive AI — iOS

On-device driver monitoring: the front camera watches for drowsiness and
distraction and alerts the driver in real time. No internet, no recording,
nothing leaves the phone.

## Run it

Requirements: a Mac with Xcode 15+, an iPhone running iOS 16+.

1. Open `SafeDriveAI.xcodeproj` (already generated and committed — no
   CocoaPods, no packages, no downloads).
2. Signing & Capabilities → select your personal team.
3. Choose your iPhone as the destination and press **Run**.
4. First run on a free personal team: trust the profile on the phone
   (Settings → General → VPN & Device Management).

Unit tests: **Cmd-U** (runs on the simulator; no camera needed).

## Technical choices (and why)

| Concern | Choice | Why |
|---|---|---|
| Face landmarks | **Apple Vision** (`VNDetectFaceLandmarksRequest`) | Ships with iOS, runs on the Neural Engine, reports head yaw/pitch/roll directly, 6-point eye contours + pupils. Zero dependencies → the project builds with no setup. |
| Behaviour analysis | **Derived geometric signals** (head pose + gaze + eye dynamics vs a per-user baseline) | Angle-invariant by construction; an image classifier adds a dependency and an unvalidated failure mode without independent information. |
| Alert audio | **AVAudioEngine synthesis** | No assets, precise control, and the running engine + `audio` background mode keeps monitoring alive when backgrounded. Plays through the silent switch (`.playback`). |
| Persistence | UserDefaults (JSON-encoded baseline) | Calibration is a tiny struct; loads on launch. |

## How detection works

Every frame → `FaceTracker` (Vision) → `FaceSnapshot` (eye aperture, head
yaw/pitch, gaze offset) → `DetectionEngine`:

- **DROWSY** needs BOTH, over a rolling 5 s window: PERCLOS (fraction of time
  eyes closed) above threshold AND at least one continuous closure ≥ 500 ms.
  Blinking satisfies neither.
- **DISTRACTED** needs head pose and gaze to AGREE, off-road in > 65 % of a
  rolling 2.5 s window. Head turned but pupils still on the road → no alert.
  Gaze flick with head forward → no alert. Sustained face loss (> 0.7 s)
  counts as off-road.
- Alerts clear automatically with hysteresis (70 % of trigger level) and
  monitoring continues — no reset, ever.

No single signal can fire an alert; every rule above is enforced by unit
tests in `SafeDriveAITests/`.

All thresholds derive from the 10-second calibration (open-eye aperture,
neutral head pose, neutral gaze) plus the sensitivity sliders, which are read
every frame — changes apply instantly while monitoring.

## Background & screen-lock behaviour (honest notes)

- While monitoring, the screen is kept awake (`isIdleTimerDisabled`) — the
  standard approach for driving apps; the phone is mounted and powered.
- If the app is backgrounded, the audio session keeps the process alive and
  `isMultitaskingCameraAccessEnabled` is set where iOS supports it. On
  devices/configurations where Apple doesn't grant background camera, iOS
  pauses frame delivery until the app returns — a hard OS restriction for
  third-party apps (the required entitlement is restricted). Detection
  resumes automatically on return.

## Project layout

```
SafeDriveAI/
├── App/        SafeDriveAIApp, RootView (onboarding → calibration → monitor)
├── Core/       CameraService, FaceTracker (Vision), CalibrationManager,
│               DetectionEngine (pure logic), DriverMonitor (coordinator),
│               AppSettings, SpeedGate
├── Alerts/     AlertPlayer (synthesized audio + haptics)
└── UI/         MonitoringView, CalibrationView, OnboardingView,
                SettingsView, FaceOverlay, Theme
```

`project.yml` is the XcodeGen spec — only needed if you add/remove files
(`brew install xcodegen && xcodegen`); the generated project is committed.
