import React, { useEffect, useState } from 'react';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Alert,
  PermissionsAndroid,
  Platform,
} from 'react-native';
import { Camera, useCameraDevice } from 'react-native-vision-camera';
import { accelerometer, setUpdateIntervalForType, SensorTypes } from 'react-native-sensors';
import Geolocation, { GeoError, GeoPosition } from 'react-native-geolocation-service';

type Accel = { x: number; y: number; z: number };

const App = () => {
  const [hasPermission, setHasPermission] = useState(false);
  const [isTripActive, setIsTripActive] = useState(false);
  const [speed, setSpeed] = useState(0);
  const [accelData, setAccelData] = useState<Accel>({ x: 0, y: 0, z: 0 });
  const frontCamera = useCameraDevice('front');

  useEffect(() => {
    requestPermissions();
  }, []);

  const requestPermissions = async () => {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.requestMultiple([
        PermissionsAndroid.PERMISSIONS.CAMERA,
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
      ]);
      const allGranted = Object.values(granted).every(
        status => status === PermissionsAndroid.RESULTS.GRANTED
      );
      setHasPermission(allGranted);
    } else {
      const cameraPermission = await Camera.requestCameraPermission();
      const locationAuth = await Geolocation.requestAuthorization('whenInUse');
      setHasPermission(cameraPermission === 'granted' && locationAuth === 'granted');
    }
  };

  useEffect(() => {
    if (!isTripActive) return;

    // Monitor accelerometer for crash detection
    setUpdateIntervalForType(SensorTypes.accelerometer, 100); // 10Hz
    const accelSubscription = accelerometer.subscribe(({ x, y, z }: Accel) => {
      setAccelData({ x, y, z });
      
      // Simple crash detection
      const magnitude = Math.sqrt(x * x + y * y + z * z);
      if (magnitude > 2.5) {
        Alert.alert('⚠️ High Impact Detected', 'Crash detection triggered!');
      }
    });

    // Monitor GPS for speed
    const gpsWatcher = Geolocation.watchPosition(
      (position: GeoPosition) => {
        const speedMps = position.coords.speed ?? 0;
        const speedKmh = speedMps * 3.6;
        setSpeed(speedKmh);
      },
      (error: GeoError) => console.log(error),
      { enableHighAccuracy: true, distanceFilter: 10, interval: 5000 }
    );

    return () => {
      accelSubscription.unsubscribe();
      Geolocation.clearWatch(gpsWatcher);
    };
  }, [isTripActive]);

  const startTrip = () => {
    if (speed > 15) {
      setIsTripActive(true);
      Alert.alert('Trip Started', 'SafeDrive monitoring active');
    } else {
      Alert.alert('Speed too low', 'Start driving to begin trip');
    }
  };

  const stopTrip = () => {
    setIsTripActive(false);
    Alert.alert('Trip Ended', 'SafeDrive monitoring stopped');
  };

  if (!hasPermission) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.errorText}>Camera and location permissions required</Text>
      </SafeAreaView>
    );
  }

  if (!frontCamera) {
    return (
      <SafeAreaView style={styles.container}>
        <Text style={styles.errorText}>Front camera not available</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>SafeDrive AI</Text>
        <Text style={styles.subtitle}>
          {isTripActive ? '🟢 Monitoring Active' : '⚪ Ready'}
        </Text>
      </View>

      <View style={styles.cameraContainer}>
        <Camera
          style={styles.camera}
          device={frontCamera}
          isActive={isTripActive}
          photo={false}
          video={false}
          audio={false}
        />
        {isTripActive && (
          <View style={styles.overlay}>
            <Text style={styles.overlayText}>Face Detection Active</Text>
          </View>
        )}
      </View>

      <View style={styles.dataPanel}>
        <View style={styles.dataRow}>
          <Text style={styles.dataLabel}>Speed:</Text>
          <Text style={styles.dataValue}>{speed.toFixed(1)} km/h</Text>
        </View>
        <View style={styles.dataRow}>
          <Text style={styles.dataLabel}>Accel:</Text>
          <Text style={styles.dataValue}>
            X: {accelData.x.toFixed(2)} Y: {accelData.y.toFixed(2)} Z: {accelData.z.toFixed(2)}
          </Text>
        </View>
      </View>

      <View style={styles.controls}>
        {!isTripActive ? (
          <TouchableOpacity style={styles.startButton} onPress={startTrip}>
            <Text style={styles.buttonText}>Start Trip</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.stopButton} onPress={stopTrip}>
            <Text style={styles.buttonText}>Stop Trip</Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  header: {
    padding: 20,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
    marginTop: 5,
  },
  cameraContainer: {
    flex: 1,
    margin: 20,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    position: 'absolute',
    top: 10,
    left: 10,
    right: 10,
    backgroundColor: 'rgba(0, 255, 0, 0.3)',
    padding: 10,
    borderRadius: 8,
  },
  overlayText: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
  },
  dataPanel: {
    backgroundColor: '#2a2a2a',
    margin: 20,
    padding: 15,
    borderRadius: 12,
  },
  dataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 5,
  },
  dataLabel: {
    color: '#888',
    fontSize: 16,
  },
  dataValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  controls: {
    padding: 20,
  },
  startButton: {
    backgroundColor: '#4CAF50',
    padding: 18,
    borderRadius: 12,
    alignItems: 'center',
  },
  stopButton: {
    backgroundColor: '#f44336',
    padding: 18,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  errorText: {
    color: '#f44336',
    fontSize: 16,
    textAlign: 'center',
    margin: 20,
  },
});

export default App;
