import Foundation
import CoreLocation

/// Optional GPS speed gate: when a threshold is set, detection pauses below
/// it (parked, stopped at a light) so the driver can look around freely
/// without alerts. Threshold 0 = feature off, GPS never started.
///
/// ## Fail open, always
///
/// Every uncertain case here resolves to "keep monitoring". If location
/// permission is denied, or no fix has arrived yet, the gate steps aside
/// rather than holding monitoring closed. The earlier version failed the
/// other way: with a threshold set and location denied, `speedKmh` stayed at
/// 0 forever, so the gate reported "too slow" on every frame and the app
/// silently never monitored anything — a safety feature quietly disabling
/// the safety app. Monitoring while parked is a minor annoyance; not
/// monitoring while driving is the whole failure mode this product exists
/// to prevent.
final class SpeedGate: NSObject, ObservableObject {
    @Published private(set) var speedKmh: Double = 0
    /// False when location is denied or restricted, so the UI can explain
    /// why the speed threshold isn't doing anything instead of leaving the
    /// driver to guess.
    @Published private(set) var isLocationAvailable = true
    /// True once a real fix has arrived. Until then the gate stays open.
    @Published private(set) var hasFix = false

    private let manager = CLLocationManager()
    private var active = false

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        refreshAvailability()
    }

    func start() {
        guard !active else { return }
        active = true
        manager.requestWhenInUseAuthorization()
        manager.startUpdatingLocation()
        refreshAvailability()
    }

    func stop() {
        guard active else { return }
        active = false
        manager.stopUpdatingLocation()
        speedKmh = 0
        hasFix = false
    }

    /// True when detection should run. Open unless we positively know the
    /// vehicle is below the threshold.
    func allowsMonitoring(threshold: Double) -> Bool {
        guard threshold > 0 else { return true }        // feature off
        guard isLocationAvailable else { return true }  // can't measure → don't block
        guard hasFix else { return true }               // no fix yet → don't block
        return speedKmh >= threshold
    }

    private func refreshAvailability() {
        let status = manager.authorizationStatus
        let available = status != .denied && status != .restricted
        if isLocationAvailable != available {
            DispatchQueue.main.async { self.isLocationAvailable = available }
        }
    }
}

extension SpeedGate: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        // A negative speed means "unknown" in CoreLocation, not "reversing";
        // treat it as no fix rather than as 0 km/h, which would close the gate.
        guard let speed = locations.last?.speed, speed >= 0 else { return }
        DispatchQueue.main.async {
            self.speedKmh = speed * 3.6
            self.hasFix = true
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        refreshAvailability()
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        // Losing the fix (tunnel, urban canyon) must reopen the gate rather
        // than freeze the last known speed and risk pausing mid-drive.
        DispatchQueue.main.async { self.hasFix = false }
    }
}
