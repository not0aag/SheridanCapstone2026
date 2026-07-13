import Foundation

enum APIError: Error {
    case notAuthenticated
    case server(status: Int, message: String)
    case transport(Error)
    case decoding(Error)
}

// Request bodies, matching the backend's Pydantic schemas
// (backend/app/routes/users.py, contacts.py, alerts.py).

private struct RegisterRequest: Encodable {
    let email: String
    let password: String
    let fullName: String

    enum CodingKeys: String, CodingKey {
        case email, password
        case fullName = "full_name"
    }
}

private struct LoginRequest: Encodable {
    let email: String
    let password: String
}

private struct ContactRequest: Encodable {
    let name: String
    let phoneNumber: String
    let email: String?

    enum CodingKeys: String, CodingKey {
        case name, email
        case phoneNumber = "phone_number"
    }
}

private struct DistractionAlertRequest: Encodable {
    let latitude: Double?
    let longitude: Double?
}

private struct ErrorDetail: Decodable {
    let detail: String
}

/// The app's only network layer: a minimal URLSession-based REST client for
/// the SafeDrive AI backend. An actor because the JWT (read from Keychain)
/// is accessed from DriverMonitor's MainActor context on a background call.
actor APIClient {
    static let shared = APIClient()

    private let baseURL: URL
    private let session: URLSession
    private let keychain: KeychainStore
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    init(baseURL: URL = AppConfig.backendBaseURL, session: URLSession = .shared, keychain: KeychainStore = .shared) {
        self.baseURL = baseURL
        self.session = session
        self.keychain = keychain

        encoder = JSONEncoder()

        decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let raw = try container.decode(String.self)
            for formatter in Self.dateFormatters where formatter.date(from: raw) != nil {
                return formatter.date(from: raw)!
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unrecognized date: \(raw)")
        }
    }

    // The backend stores naive (no-timezone) UTC timestamps, so responses
    // look like "2026-07-13T21:06:46" or "...46.123456", not RFC 3339 —
    // try both, most specific first.
    private static let dateFormatters: [DateFormatter] = {
        ["yyyy-MM-dd'T'HH:mm:ss.SSSSSS", "yyyy-MM-dd'T'HH:mm:ss"].map { format in
            let formatter = DateFormatter()
            formatter.dateFormat = format
            formatter.timeZone = TimeZone(identifier: "UTC")
            formatter.locale = Locale(identifier: "en_US_POSIX")
            return formatter
        }
    }()

    // MARK: Account

    var isAuthenticated: Bool { keychain.authToken != nil }

    func register(email: String, password: String, fullName: String) async throws -> UserDTO {
        try await post("/users/register", body: RegisterRequest(email: email, password: password, fullName: fullName), authorized: false)
    }

    func login(email: String, password: String) async throws -> TokenResponseDTO {
        let response: TokenResponseDTO = try await post("/users/login", body: LoginRequest(email: email, password: password), authorized: false)
        keychain.authToken = response.accessToken
        return response
    }

    func logout() {
        keychain.authToken = nil
    }

    // MARK: Trusted contacts

    func fetchContacts() async throws -> [EmergencyContactDTO] {
        try await get("/contacts/")
    }

    func addContact(name: String, phoneNumber: String, email: String?) async throws -> EmergencyContactDTO {
        try await post("/contacts/", body: ContactRequest(name: name, phoneNumber: phoneNumber, email: email))
    }

    func deleteContact(id: Int) async throws {
        try await delete("/contacts/\(id)")
    }

    // MARK: Distraction alerts

    func sendDistractionAlert(latitude: Double?, longitude: Double?) async throws -> DistractionAlertDTO {
        try await post("/alerts/distraction", body: DistractionAlertRequest(latitude: latitude, longitude: longitude))
    }

    // MARK: Core request plumbing

    private func get<Response: Decodable>(_ path: String, authorized: Bool = true) async throws -> Response {
        let data = try await perform(path: path, method: "GET", authorized: authorized, jsonBody: nil)
        return try decodeOrThrow(data)
    }

    private func post<Body: Encodable, Response: Decodable>(_ path: String, body: Body, authorized: Bool = true) async throws -> Response {
        let json = try encoder.encode(body)
        let data = try await perform(path: path, method: "POST", authorized: authorized, jsonBody: json)
        return try decodeOrThrow(data)
    }

    private func delete(_ path: String, authorized: Bool = true) async throws {
        _ = try await perform(path: path, method: "DELETE", authorized: authorized, jsonBody: nil)
    }

    private func perform(path: String, method: String, authorized: Bool, jsonBody: Data?) async throws -> Data {
        var request = URLRequest(url: URL(string: baseURL.absoluteString + path)!)
        request.httpMethod = method

        if let jsonBody {
            request.httpBody = jsonBody
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if authorized {
            guard let token = keychain.authToken else { throw APIError.notAuthenticated }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.transport(error)
        }

        guard let http = response as? HTTPURLResponse else {
            throw APIError.transport(URLError(.badServerResponse))
        }
        guard (200..<300).contains(http.statusCode) else {
            // A 401 means the stored token is no longer valid — drop it so
            // the UI can prompt for login again instead of retrying forever.
            if http.statusCode == 401 {
                keychain.authToken = nil
            }
            let message = (try? decoder.decode(ErrorDetail.self, from: data))?.detail ?? "Request failed (\(http.statusCode))"
            throw APIError.server(status: http.statusCode, message: message)
        }
        return data
    }

    private func decodeOrThrow<Response: Decodable>(_ data: Data) throws -> Response {
        do {
            return try decoder.decode(Response.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }
}
