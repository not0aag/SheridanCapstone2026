import Foundation

/// On-device store for the driver's trusted emergency contacts.
///
/// For the standalone demo build this replaces the networked `/contacts`
/// endpoints: the same `EmergencyContactDTO` the (still-present) APIClient
/// uses is persisted here as JSON in UserDefaults, mirroring
/// CalibrationManager's persistence pattern. To re-enable the server-backed
/// version, point ContactsView/AddContactView back at `APIClient.shared`.
///
/// A locally-incrementing id mirrors the backend's autoincrement primary key,
/// so `EmergencyContactDTO` (which requires a non-optional `id`) is reused
/// unchanged.
@MainActor
final class LocalContactsStore: ObservableObject {
    @Published private(set) var contacts: [EmergencyContactDTO]

    private let defaults: UserDefaults
    private static let contactsKey = "local.contacts.v1"
    private static let nextIdKey = "local.contacts.nextId.v1"

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let data = defaults.data(forKey: Self.contactsKey),
           let saved = try? JSONDecoder().decode([EmergencyContactDTO].self, from: data) {
            contacts = saved
        } else {
            contacts = []
        }
    }

    func list() -> [EmergencyContactDTO] { contacts }

    @discardableResult
    func add(name: String, phoneNumber: String, email: String?) -> EmergencyContactDTO {
        let contact = EmergencyContactDTO(
            id: nextId(),
            name: name,
            phoneNumber: phoneNumber,
            email: email,
            relationship: nil
        )
        contacts.append(contact)
        persist()
        return contact
    }

    func delete(id: Int) {
        contacts.removeAll { $0.id == id }
        persist()
    }

    /// Hands out a monotonically increasing id that survives relaunches, so
    /// ids stay unique even after contacts are deleted and re-added.
    private func nextId() -> Int {
        let next = defaults.object(forKey: Self.nextIdKey) as? Int ?? 1
        defaults.set(next + 1, forKey: Self.nextIdKey)
        return next
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(contacts) {
            defaults.set(data, forKey: Self.contactsKey)
        }
    }
}
