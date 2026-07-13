import Foundation

enum AppConfig {
    /// The backend host. Debug builds point at a local dev server (see
    /// backend/README for `uvicorn` setup); Release always requires HTTPS,
    /// matching the production URL already documented in
    /// docs/api/openapi.yaml.
    ///
    /// NOTE: "localhost" only resolves to the Mac when running in the
    /// Simulator. A physical iPhone needs the Mac's actual LAN IP (find it
    /// with `ipconfig getifaddr en0`) — update the value below if you're
    /// testing on-device and your Mac's IP changes.
    static var backendBaseURL: URL {
        #if DEBUG
        return URL(string: "http://142.55.48.25:8000")!
        #else
        return URL(string: "https://api.safedriveai.com")!
        #endif
    }
}
