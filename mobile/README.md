# SafeDrive AI - Mobile App (React Native)

Cross-platform mobile app for iOS and Android with real-time driver safety monitoring.

## Features
- ✅ Front-facing camera integration (30 FPS)
- ✅ Accelerometer and gyroscope sensor monitoring
- ✅ GPS tracking for trip detection
- ✅ Real-time crash detection
- ✅ Trip start/stop based on speed
- ✅ Permission handling for iOS and Android

## Setup

### Prerequisites
- Node.js 18+
- React Native CLI
- Xcode (for iOS)
- Android Studio (for Android)

### Installation
```bash
cd mobile
npm install

# iOS only
cd ios && pod install && cd ..
```

### Run on Android
```bash
npm run android
```

### Run on iOS
```bash
npm run ios
```

## Project Structure
```
mobile/
├── App.tsx                 # Main app component
├── package.json            # Dependencies
├── android/                # Android-specific files
│   └── AndroidManifest.xml # Permissions
├── ios/                    # iOS-specific files
│   └── Info.plist          # Permissions
└── README.md
```

## Permissions
### Android
- Camera
- Fine Location
- High Sampling Rate Sensors
- Storage (for video recording)

### iOS
- Camera
- Location (When In Use)
- Motion Sensors

## Next Steps (May 2026)
1. Integrate TFLite/Core ML models for on-device ML inference
2. Implement alert system (audio, visual, haptic)
3. Add backend API integration for trip sync
4. Implement video recording during trips
5. Build settings and profile screens
6. Add offline data sync with SQLite
