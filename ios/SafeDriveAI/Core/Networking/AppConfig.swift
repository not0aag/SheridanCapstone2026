import Foundation

enum AppConfig {
    /// The backend host. Debug builds point at a local dev server (see
    /// backend/README for `uvicorn` setup); Release always requires HTTPS,
    /// matching the production URL already documented in
    /// docs/api/openapi.yaml.
    ///
    /// NOTE: "localhost" only resolves to the Mac when running in the
    /// Simulator. A physical iPhone needs the Mac's actual LAN IP. This is
    /// read from the DEV_BACKEND_HOST build setting (see ios/project.yml)
    /// via Info.plist, so switching networks only needs a project.yml edit
    /// + `xcodegen generate` — no source change or recompile of this file.
    static var backendBaseURL: URL {
        #if DEBUG
        let host = Bundle.main.object(forInfoDictionaryKey: "DEV_BACKEND_HOST") as? String
        return URL(string: "http://\(host ?? "142.55.48.25:8000")")!
        #else
        return URL(string: "https://api.safedriveai.com")!
        #endif
    }
}
