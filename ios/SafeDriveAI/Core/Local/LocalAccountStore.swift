import Foundation
import CryptoKit

/// A single driver profile stored on-device.
struct LocalDriverProfile: Codable, Equatable {
    let fullName: String
    let email: String
    let passwordHash: String
}

/// On-device account store for the standalone demo build.
///
/// The account exists only so trusted-contact alerts can be attributed to a
/// driver; with the backend deferred, one local profile replaces the server's
/// user table. Persisted as JSON in UserDefaults, mirroring
/// CalibrationManager's pattern.
///
/// This is deliberately *not* a security boundary — the password check only
/// gates the local UI, and there is no network or multi-user surface — so a
/// plain SHA-256 hash is used instead of the backend's bcrypt. Reconnecting
/// `APIClient.shared` restores real server-side auth.
final class LocalAccountStore {
    enum RegisterError: Error, Equatable {
        case emailAlreadyRegistered
    }

    private let defaults: UserDefaults
    private static let profileKey = "local.account.profile.v1"
    private static let loggedInKey = "local.account.loggedIn.v1"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    var profile: LocalDriverProfile? {
        guard let data = defaults.data(forKey: Self.profileKey),
              let saved = try? JSONDecoder().decode(LocalDriverProfile.self, from: data) else {
            return nil
        }
        return saved
    }

    var hasProfile: Bool { profile != nil }

    /// Whether a session is active. Persisted so a logged-in driver stays
    /// logged in across relaunches (the demo device is single-user).
    var isLoggedIn: Bool { defaults.bool(forKey: Self.loggedInKey) }

    func register(email: String, password: String, fullName: String) throws {
        if let existing = profile, Self.normalize(existing.email) == Self.normalize(email) {
            throw RegisterError.emailAlreadyRegistered
        }
        let newProfile = LocalDriverProfile(
            fullName: fullName,
            email: email,
            passwordHash: Self.hash(password)
        )
        if let data = try? JSONEncoder().encode(newProfile) {
            defaults.set(data, forKey: Self.profileKey)
        }
    }

    @discardableResult
    func login(email: String, password: String) -> Bool {
        guard let profile,
              Self.normalize(profile.email) == Self.normalize(email),
              profile.passwordHash == Self.hash(password) else {
            return false
        }
        defaults.set(true, forKey: Self.loggedInKey)
        return true
    }

    func logout() {
        defaults.set(false, forKey: Self.loggedInKey)
    }

    private static func normalize(_ email: String) -> String {
        email.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }

    private static func hash(_ password: String) -> String {
        SHA256.hash(data: Data(password.utf8))
            .map { String(format: "%02x", $0) }
            .joined()
    }
}
