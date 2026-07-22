import Foundation

/// Drives the login/registration flow for the Emergency Alerts feature.
///
/// For the standalone demo build this is backed by an on-device
/// `LocalAccountStore` (UserDefaults) instead of the networked APIClient.
/// The public interface is unchanged, so AccountView needs no edits — flip
/// the store back to `APIClient.shared` to re-enable the server-backed flow.
///
/// The methods stay `async` even though the local store is synchronous, so
/// existing `await account.login(...)` call sites compile unchanged.
@MainActor
final class AccountManager: ObservableObject {
    @Published private(set) var isAuthenticated: Bool
    @Published var lastErrorMessage: String?

    private let store: LocalAccountStore

    init(store: LocalAccountStore = LocalAccountStore()) {
        self.store = store
        // A previously logged-in driver stays logged in across relaunches.
        isAuthenticated = store.isLoggedIn
    }

    func refreshAuthState() async {
        isAuthenticated = store.isLoggedIn
    }

    func register(email: String, password: String, fullName: String) async -> Bool {
        do {
            try store.register(email: email, password: password, fullName: fullName)
            return await login(email: email, password: password)
        } catch {
            lastErrorMessage = "That email is already registered. Try logging in instead."
            return false
        }
    }

    func login(email: String, password: String) async -> Bool {
        guard store.login(email: email, password: password) else {
            lastErrorMessage = store.hasProfile
                ? "Incorrect email or password."
                : "No account yet — tap Sign Up to create one."
            isAuthenticated = false
            return false
        }
        isAuthenticated = true
        lastErrorMessage = nil
        return true
    }

    func logout() async {
        store.logout()
        isAuthenticated = false
    }
}
