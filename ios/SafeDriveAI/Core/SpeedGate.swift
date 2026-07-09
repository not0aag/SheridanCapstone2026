import Foundation
import CoreLocation

/// Optional GPS speed gate: when a threshold is set, detection pauses below it
/// (parked, stopped at a light) so the driver can look around freely without
/// alerts. Threshold 0 = feature off, GPS never started.
final class SpeedGate: NSObject, ObservableObject {
    @Published private(set) var speedKmh: Double = 0

    private let manager = CLLocationManager()
    private var active = false

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
    }

    func start() {
        guard !active else { return }
        active = true
        manager.requestWhenInUseAuthorization()
        manager.startUpdatingLocation()
    }

    func stop() {
        guard active else { return }
        active = false
        manager.stopUpdatingLocation()
        speedKmh = 0
    }

    func allowsMonitoring(threshold: Double) -> Bool {
        threshold <= 0 || speedKmh >= threshold
    }
}

extension SpeedGate: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        let mps = max(locations.last?.speed ?? 0, 0)
        DispatchQueue.main.async { self.speedKmh = mps * 3.6 }
    }
}
