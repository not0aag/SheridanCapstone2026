import Foundation

// DTOs mirror the backend's Pydantic response shapes 1:1
// (see backend/app/routes/users.py, contacts.py, alerts.py).

struct UserDTO: Codable {
    let id: Int
    let email: String
    let fullName: String
    let phoneNumber: String?

    enum CodingKeys: String, CodingKey {
        case id, email
        case fullName = "full_name"
        case phoneNumber = "phone_number"
    }
}

struct TokenResponseDTO: Codable {
    let accessToken: String
    let tokenType: String
    let user: UserDTO

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
        case user
    }
}

struct EmergencyContactDTO: Codable, Identifiable {
    let id: Int
    let name: String
    let phoneNumber: String
    let email: String?
    let relationship: String?

    enum CodingKeys: String, CodingKey {
        case id, name, email, relationship
        case phoneNumber = "phone_number"
    }
}

struct DistractionAlertDTO: Codable {
    let id: Int
    let contactsNotified: Int
    let sentAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case contactsNotified = "contacts_notified"
        case sentAt = "sent_at"
    }
}
