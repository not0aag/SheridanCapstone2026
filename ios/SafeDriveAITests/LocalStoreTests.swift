import XCTest
@testable import SafeDriveAI

final class LocalAccountStoreTests: XCTestCase {
    private var suiteName: String!
    private var defaults: UserDefaults!

    override func setUp() {
        super.setUp()
        suiteName = "test.account.\(UUID().uuidString)"
        defaults = UserDefaults(suiteName: suiteName)
    }

    override func tearDown() {
        defaults.removePersistentDomain(forName: suiteName)
        defaults = nil
        suiteName = nil
        super.tearDown()
    }

    func testRegisterThenLoginSucceeds() {
        let store = LocalAccountStore(defaults: defaults)
        XCTAssertFalse(store.hasProfile)
        XCTAssertNoThrow(try store.register(email: "dana@example.com", password: "hunter22", fullName: "Dana Driver"))
        XCTAssertTrue(store.hasProfile)
        XCTAssertTrue(store.login(email: "dana@example.com", password: "hunter22"))
        XCTAssertTrue(store.isLoggedIn)
    }

    func testLoginIsCaseInsensitiveOnEmail() {
        let store = LocalAccountStore(defaults: defaults)
        try? store.register(email: "Dana@Example.com", password: "hunter22", fullName: "Dana")
        XCTAssertTrue(store.login(email: "dana@example.com", password: "hunter22"))
    }

    func testWrongPasswordFails() {
        let store = LocalAccountStore(defaults: defaults)
        try? store.register(email: "dana@example.com", password: "hunter22", fullName: "Dana")
        XCTAssertFalse(store.login(email: "dana@example.com", password: "wrong"))
        XCTAssertFalse(store.isLoggedIn)
    }

    func testDuplicateEmailRegistrationIsRejected() {
        let store = LocalAccountStore(defaults: defaults)
        try? store.register(email: "dana@example.com", password: "hunter22", fullName: "Dana")
        XCTAssertThrowsError(try store.register(email: "dana@example.com", password: "other", fullName: "Dana Again")) { error in
            XCTAssertEqual(error as? LocalAccountStore.RegisterError, .emailAlreadyRegistered)
        }
    }

    func testLogoutClearsSessionButKeepsProfile() {
        let store = LocalAccountStore(defaults: defaults)
        try? store.register(email: "dana@example.com", password: "hunter22", fullName: "Dana")
        _ = store.login(email: "dana@example.com", password: "hunter22")
        store.logout()
        XCTAssertFalse(store.isLoggedIn)
        XCTAssertTrue(store.hasProfile)
    }

    func testProfileAndSessionPersistAcrossInstances() {
        let first = LocalAccountStore(defaults: defaults)
        try? first.register(email: "dana@example.com", password: "hunter22", fullName: "Dana Driver")
        _ = first.login(email: "dana@example.com", password: "hunter22")

        let second = LocalAccountStore(defaults: defaults)
        XCTAssertTrue(second.hasProfile)
        XCTAssertTrue(second.isLoggedIn)
        XCTAssertEqual(second.profile?.fullName, "Dana Driver")
    }
}

@MainActor
final class LocalContactsStoreTests: XCTestCase {
    private var suiteName: String!
    private var defaults: UserDefaults!

    override func setUp() {
        super.setUp()
        suiteName = "test.contacts.\(UUID().uuidString)"
        defaults = UserDefaults(suiteName: suiteName)
    }

    override func tearDown() {
        defaults.removePersistentDomain(forName: suiteName)
        defaults = nil
        suiteName = nil
        super.tearDown()
    }

    func testAddAndList() {
        let store = LocalContactsStore(defaults: defaults)
        XCTAssertTrue(store.list().isEmpty)
        store.add(name: "Sam", phoneNumber: "+15551234567", email: nil)
        store.add(name: "Alex", phoneNumber: "+15557654321", email: "alex@example.com")
        XCTAssertEqual(store.list().count, 2)
        XCTAssertEqual(store.list().first?.name, "Sam")
    }

    func testIdsAreUniqueAndIncrementing() {
        let store = LocalContactsStore(defaults: defaults)
        let first = store.add(name: "Sam", phoneNumber: "+15551234567", email: nil)
        let second = store.add(name: "Alex", phoneNumber: "+15557654321", email: nil)
        XCTAssertNotEqual(first.id, second.id)
        XCTAssertEqual(second.id, first.id + 1)
    }

    func testDelete() {
        let store = LocalContactsStore(defaults: defaults)
        let sam = store.add(name: "Sam", phoneNumber: "+15551234567", email: nil)
        store.add(name: "Alex", phoneNumber: "+15557654321", email: nil)
        store.delete(id: sam.id)
        XCTAssertEqual(store.list().count, 1)
        XCTAssertEqual(store.list().first?.name, "Alex")
    }

    func testIdsStayUniqueAfterDeleteAndReAdd() {
        let store = LocalContactsStore(defaults: defaults)
        let sam = store.add(name: "Sam", phoneNumber: "+1", email: nil)
        store.delete(id: sam.id)
        let alex = store.add(name: "Alex", phoneNumber: "+2", email: nil)
        XCTAssertNotEqual(sam.id, alex.id)
    }

    func testContactsPersistAcrossInstances() {
        let first = LocalContactsStore(defaults: defaults)
        first.add(name: "Sam", phoneNumber: "+15551234567", email: nil)

        let second = LocalContactsStore(defaults: defaults)
        XCTAssertEqual(second.list().count, 1)
        XCTAssertEqual(second.list().first?.name, "Sam")
    }
}
