#!/usr/bin/env bash
# run_dev.sh - builds, starts emulator (if needed), installs and runs the SafeDrive debug APK,
# then tails filtered logcat for quick verification.
# Usage: ./run_dev.sh

set -euo pipefail
cd "$(dirname "$0")"

# Prefer Homebrew java 17 if installed
if command -v brew >/dev/null 2>&1 && [ -d "$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home" ]; then
  export JAVA_HOME="$(brew --prefix openjdk@17)/libexec/openjdk.jdk/Contents/Home"
  export PATH="$JAVA_HOME/bin:$PATH"
  echo "Using JAVA_HOME=$JAVA_HOME"
fi

echo "Checking for connected devices..."
adb devices -l | sed -n '1,5p'

DEVICE_COUNT=$(adb devices | sed -n '2,$p' | grep -v "^$" | wc -l | tr -d ' ')
if [ "$DEVICE_COUNT" -eq 0 ]; then
  echo "No device/emulator found. Looking for available AVDs..."
  if command -v emulator >/dev/null 2>&1; then
    AVD_LIST=$(emulator -list-avds || true)
    if [ -z "$AVD_LIST" ]; then
      echo "No AVDs found. Please create an AVD via Android Studio AVD Manager or using avdmanager."
      echo "You can create one like:"
      echo "  avdmanager create avd -n Pixel_6_API_33 -k \"system-images;android-33;google_apis;x86_64\" --device \"pixel_6\""
      exit 1
    fi
    # start the first available AVD
    AVD_NAME=$(echo "$AVD_LIST" | head -n1)
    echo "Starting AVD: $AVD_NAME"
    nohup emulator -avd "$AVD_NAME" -no-snapshot -gpu swiftshader_indirect > /dev/null 2>&1 &
    echo "Waiting for emulator to boot..."
    adb wait-for-device
    # wait until boot complete
    BOOTED=0
    for i in {1..60}; do
      BOOT_COMPLETE=$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r') || true
      if [ "$BOOT_COMPLETE" = "1" ]; then
        BOOTED=1
        break
      fi
      sleep 1
    done
    if [ "$BOOTED" -ne 1 ]; then
      echo "Emulator did not finish booting in time. Proceeding but device may be unavailable."
    else
      echo "Emulator booted."
    fi
  else
    echo "No emulator binary available (emulator). Please open Android Studio and start an AVD or connect a device."
    exit 1
  fi
else
  echo "Device(s) detected. Proceeding to build/install."
fi

# Build the debug APK
echo "Building app (assembleDebug)..."
./gradlew clean :app:assembleDebug --stacktrace

# Install the debug APK
echo "Installing APK..."
./gradlew :app:installDebug

# Launch the app
PKG=com.sukhman.safedrive
ACTIVITY=.MainActivity
echo "Launching $PKG/$ACTIVITY"
adb shell am start -n ${PKG}/${ACTIVITY} || true

# Grant required permissions (for debug builds)
adb shell pm grant ${PKG} android.permission.CAMERA || true
adb shell pm grant ${PKG} android.permission.RECORD_AUDIO || true
adb shell pm grant ${PKG} android.permission.ACCESS_FINE_LOCATION || true

# Tail filtered logcat
echo "Tailing logcat (press Ctrl+C to stop). Filtering tags: Camera, FpsAnalyzer, SensorsManager, LocationHelper, MainActivity"
adb logcat -v time | egrep "Camera|FpsAnalyzer|SensorsManager|LocationHelper|MainActivity"

