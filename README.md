SafeDrive Android (Kotlin) — Week 1

Overview
- This repo contains the SafeDrive Android app prototype (Kotlin + Jetpack Compose).
- Features added for Week 1:
  - CameraX Preview (front camera) with target 1080p request and Camera2 FPS range request (30fps)
  - ImageAnalysis `FpsAnalyzer` to log approximate FPS
  - `SensorsManager` (accelerometer & gyroscope) with start/stop
  - `LocationHelper` (FusedLocationProvider) to request current location

Build & Run (macOS / zsh)

1) Install/point to a supported JDK (OpenJDK 17 recommended):

```bash
# Install with Homebrew (if not already installed)
brew update
brew install openjdk@17

# Set JAVA_HOME for this terminal session
export JAVA_HOME="$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
java -version
```

2) Build the debug APK:

```bash
# from project root
./gradlew clean :app:assembleDebug --stacktrace
```

3) Start an emulator (or connect a physical device with USB debugging enabled)

- Create an AVD (only if you don't have one):
```bash
# List available system images and devices
sdkmanager --list | grep "system-images"
avdmanager list device

# Example: create Pixel_6_API_33 AVD (use a system-image you have installed)
avdmanager create avd -n Pixel_6_API_33 -k "system-images;android-33;google_apis;x86_64" --device "pixel_6"
```

- Start the emulator:

```bash
emulator -avd Pixel_6_API_33 -no-snapshot -gpu swiftshader_indirect &
# wait a moment, then
adb devices -l
```

4) Install & launch the app:

```bash
# install
./gradlew :app:installDebug

# launch
adb shell am start -n com.sukhman.safedrive/.MainActivity
```

5) Grant permissions (if needed):

```bash
adb shell pm grant com.sukhman.safedrive android.permission.CAMERA
adb shell pm grant com.sukhman.safedrive android.permission.RECORD_AUDIO
adb shell pm grant com.sukhman.safedrive android.permission.ACCESS_FINE_LOCATION
```

6) View logs (verify camera binding, FPS logs, sensors, location):

```bash
adb logcat -v time | egrep "Camera|FpsAnalyzer|SensorsManager|LocationHelper|MainActivity"
```

Expected log lines to confirm functionality
- Camera binding: "Camera bound (front, 1080p target, 30fps request)"
- FPS analyzer (approx every second): "FpsAnalyzer: Approx FPS: XX.XX (frames=NN elapsed=1000ms)"
- Sensors: "SensorsManager: Accelerometer: ax=... ay=... az=..." and "Sensor listeners unregistered"
- Location: "LocationHelper" log lines with coordinates or warnings

Notes & Caveats
- Emulators often do not support real camera hardware with full resolution or frame rates. For accurate 1080p@30fps validation use a physical device that supports Camera2.
- The app requests 1080p and 30fps but CameraX will fall back to the best supported configuration if hardware can't satisfy the exact request.

If you'd like me to run the install & logcat here, please either:
- Start an AVD in this environment (so `adb devices` shows a connected emulator), or
- Connect a physical device (and allow USB debugging) so I can run the install and capture logs.

Next steps I can do for you
- Add a short demo screen to record a 5–10s 1080p video (if the device supports it).
- Add an optional FaceMesh/ImageAnalysis hook for Week 2 POC.
- Prepare a short README export or slide-ready notes for your capstone submission.

Contact me with the `adb devices -l` output or tell me to proceed with adding a video recording POC and I’ll implement and build it.

