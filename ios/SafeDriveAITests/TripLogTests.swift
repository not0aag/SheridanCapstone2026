import XCTest
@testable import SafeDriveAI

final class TripLogTests: XCTestCase {
    private var defaults: UserDefaults!

    override func setUp() {
        super.setUp()
        defaults = UserDefaults(suiteName: "trip-log-tests")!
        defaults.removePersistentDomain(forName: "trip-log-tests")
    }

    func testEndTripWithoutStartReturnsNil() {
        let log = TripLog(defaults: defaults)
        XCTAssertNil(log.endTrip())
    }

    func testCountsOnlyTransitionsIntoAlertStates() {
        let log = TripLog(defaults: defaults)
        log.startTrip()
        // Held in .drowsy for 3 frames — should count as ONE alert, not three.
        log.ingest(state: .drowsy, perclos: 0.5, offRoadRate: 0)
        log.ingest(state: .drowsy, perclos: 0.5, offRoadRate: 0)
        log.ingest(state: .drowsy, perclos: 0.5, offRoadRate: 0)
        log.ingest(state: .safe, perclos: 0.1, offRoadRate: 0)
        log.ingest(state: .distracted, perclos: 0.1, offRoadRate: 0.7)

        let summary = log.endTrip()
        XCTAssertEqual(summary?.drowsyAlertCount, 1)
        XCTAssertEqual(summary?.distractedAlertCount, 1)
    }

    func testIngestBeforeStartIsIgnored() {
        let log = TripLog(defaults: defaults)
        log.ingest(state: .drowsy, perclos: 0.9, offRoadRate: 0)
        XCTAssertNil(log.endTrip())
    }

    func testAveragesComputedAcrossSamples() {
        let log = TripLog(defaults: defaults)
        log.startTrip()
        log.ingest(state: .safe, perclos: 0.2, offRoadRate: 0.1)
        log.ingest(state: .safe, perclos: 0.4, offRoadRate: 0.3)
        let summary = log.endTrip()
        XCTAssertEqual(summary?.averagePerclos ?? -1, 0.3, accuracy: 0.001)
        XCTAssertEqual(summary?.averageOffRoadRate ?? -1, 0.2, accuracy: 0.001)
    }

    func testSafetyScoreWeightsDrowsyMoreThanDistracted() {
        XCTAssertEqual(TripLog.safetyScore(drowsy: 0, distracted: 0), 100)
        XCTAssertEqual(TripLog.safetyScore(drowsy: 1, distracted: 0), 85)
        XCTAssertEqual(TripLog.safetyScore(drowsy: 0, distracted: 1), 90)
        XCTAssertGreaterThan(
            TripLog.safetyScore(drowsy: 0, distracted: 1),
            TripLog.safetyScore(drowsy: 1, distracted: 0)
        )
    }

    func testSafetyScoreFloorsAtZero() {
        XCTAssertEqual(TripLog.safetyScore(drowsy: 20, distracted: 20), 0)
    }

    func testTripsPersistAcrossRelaunch() {
        let log = TripLog(defaults: defaults)
        log.startTrip()
        log.ingest(state: .safe, perclos: 0.1, offRoadRate: 0)
        log.endTrip()

        let relaunched = TripLog(defaults: defaults)
        XCTAssertEqual(relaunched.trips.count, 1)
    }

    func testNewestTripFirst() {
        let log = TripLog(defaults: defaults)
        log.startTrip()
        log.endTrip()
        log.startTrip()
        log.endTrip()
        XCTAssertEqual(log.trips.count, 2)
        // Second trip's id should sort first (newest-first insertion).
        XCTAssertGreaterThan(log.trips[0].id, log.trips[1].id)
    }

    func testDeleteTripRemovesAndPersists() {
        let log = TripLog(defaults: defaults)
        log.startTrip()
        let summary = log.endTrip()!
        log.deleteTrip(id: summary.id)
        XCTAssertTrue(log.trips.isEmpty)

        let relaunched = TripLog(defaults: defaults)
        XCTAssertTrue(relaunched.trips.isEmpty)
    }

    func testAggregateStats() {
        let log = TripLog(defaults: defaults)
        log.startTrip()
        log.ingest(state: .drowsy, perclos: 0.5, offRoadRate: 0)
        log.endTrip()
        log.startTrip()
        log.ingest(state: .safe, perclos: 0.1, offRoadRate: 0)
        log.endTrip()

        XCTAssertEqual(log.totalTrips, 2)
        XCTAssertEqual(log.overallAlertRate, 0.5, accuracy: 0.001) // 1 alert / 2 trips
    }
}
