import Foundation

/// Wraps APIClient for the login/registration flow used by the Emergency
/// Alerts feature. There's no other account-related state in the app —
/// monitoring itself is fully on-device and needs no login.
@MainActor
final class AccountManager: ObservableObject {
    @Published private(set) var isAuthenticated: Bool
    @Published var lastErrorMessage: String?

    init() {
        isAuthenticated = false
        Task { await refreshAuthState() }
    }

    func refreshAuthState() async {
        isAuthenticated = await APIClient.shared.isAuthenticated
    }

    func register(email: String, password: String, fullName: String) async -> Bool {
        do {
            _ = try await APIClient.shared.register(email: email, password: password, fullName: fullName)
            return await login(email: email, password: password)
        } catch {
            lastErrorMessage = message(for: error)
            return false
        }
    }

    func login(email: String, password: String) async -> Bool {
        do {
            _ = try await APIClient.shared.login(email: email, password: password)
            isAuthenticated = true
            lastErrorMessage = nil
            return true
        } catch {
            lastErrorMessage = message(for: error)
            isAuthenticated = false
            return false
        }
    }

    func logout() async {
        await APIClient.shared.logout()
        isAuthenticated = false
    }

    private func message(for error: Error) -> String {
        switch error as? APIError {
        case .server(_, let message): return message
        case .notAuthenticated: return "Please log in again."
        case .transport: return "Couldn't reach the server. Check your connection."
        case .decoding, .none: return "Something went wrong. Please try again."
        }
    }
}
