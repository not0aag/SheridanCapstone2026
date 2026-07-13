import Foundation
import Security

/// Minimal Keychain wrapper for storing the backend JWT. The app has no
/// other secrets to store, so this is intentionally narrow (get/set/delete
/// a single string under a fixed key) rather than a general-purpose wrapper.
final class KeychainStore {
    static let shared = KeychainStore()

    private let service = "ca.sheridan.capstone.safedriveai"
    private let account = "authToken"

    private init() {}

    var authToken: String? {
        get {
            let query: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrService as String: service,
                kSecAttrAccount as String: account,
                kSecReturnData as String: true,
                kSecMatchLimit as String: kSecMatchLimitOne,
            ]
            var result: AnyObject?
            let status = SecItemCopyMatching(query as CFDictionary, &result)
            guard status == errSecSuccess, let data = result as? Data else { return nil }
            return String(data: data, encoding: .utf8)
        }
        set {
            let query: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrService as String: service,
                kSecAttrAccount as String: account,
            ]
            guard let newValue, let data = newValue.data(using: .utf8) else {
                SecItemDelete(query as CFDictionary)
                return
            }
            SecItemDelete(query as CFDictionary)
            var attributes = query
            attributes[kSecValueData as String] = data
            SecItemAdd(attributes as CFDictionary, nil)
        }
    }
}
