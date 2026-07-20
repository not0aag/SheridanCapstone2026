import AVFoundation
import SwiftUI
import UIKit

/// Front-camera capture, tuned for continuous driver monitoring.
///
/// Design goals: portrait-locked mirrored frames that match the on-screen
/// preview exactly (so the landmark overlay lines up), adjustable frame rate
/// for battery control, and every background-continuation option iOS offers.
final class CameraService: NSObject, ObservableObject {
    let session = AVCaptureSession()

    @Published private(set) var isRunning = false
    @Published private(set) var permissionDenied = false

    /// Called on the capture queue for every frame.
    var onFrame: ((CVPixelBuffer, Int64) -> Void)?

    private let output = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "safedrive.camera", qos: .userInitiated)
    private var configured = false

    override init() {
        super.init()
        // Covers "already denied from a previous run": catches a permission
        // that was revoked in Settings between launches, and clears the
        // blocked state if the user grants access in Settings and comes back
        // — start()'s own requestAccess callback only fires for the
        // in-app prompt, not a change made outside the app.
        refreshAuthorizationStatus()
        NotificationCenter.default.addObserver(
            forName: UIApplication.willEnterForegroundNotification, object: nil, queue: .main
        ) { [weak self] _ in
            self?.refreshAuthorizationStatus()
        }
    }

    /// Re-checks the OS permission without prompting or starting the
    /// session. Safe to call anytime the UI needs an up-to-date read.
    func refreshAuthorizationStatus() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized: permissionDenied = false
        case .denied, .restricted: permissionDenied = true
        case .notDetermined: break
        @unknown default: break
        }
    }

    // MARK: Lifecycle

    func start() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            permissionDenied = false
            startSession()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    if granted {
                        self?.permissionDenied = false
                        self?.startSession()
                    } else {
                        self?.permissionDenied = true
                    }
                }
            }
        default:
            permissionDenied = true
        }
    }

    func stop() {
        sessionQueue.async { [self] in
            guard session.isRunning else { return }
            session.stopRunning()
            DispatchQueue.main.async { self.isRunning = false }
        }
    }

    /// 30 fps while on screen; 15 fps when backgrounded to halve battery cost.
    func setFrameRate(_ fps: Int) {
        sessionQueue.async { [self] in
            guard let device = (session.inputs.first as? AVCaptureDeviceInput)?.device,
                  let range = device.activeFormat.videoSupportedFrameRateRanges.first
            else { return }
            let clamped = min(max(Double(fps), range.minFrameRate), range.maxFrameRate)
            do {
                try device.lockForConfiguration()
                let duration = CMTime(value: 1, timescale: CMTimeScale(clamped))
                device.activeVideoMinFrameDuration = duration
                device.activeVideoMaxFrameDuration = duration
                device.unlockForConfiguration()
            } catch {
                print("CameraService: frame rate change failed: \(error)")
            }
        }
    }

    private func startSession() {
        sessionQueue.async { [self] in
            configureIfNeeded()
            guard !session.isRunning else { return }
            session.startRunning()
            DispatchQueue.main.async { self.isRunning = true }
        }
    }

    private func configureIfNeeded() {
        guard !configured else { return }
        session.beginConfiguration()
        defer { session.commitConfiguration(); configured = true }

        // 640×480 is plenty for face landmarks and much cheaper than HD.
        session.sessionPreset = .vga640x480

        // True background capture where iOS allows it (iOS 16+). On devices /
        // configurations where Apple doesn't permit it, this stays false and
        // the app relies on keeping the screen awake instead.
        if session.isMultitaskingCameraAccessSupported {
            session.isMultitaskingCameraAccessEnabled = true
        }

        guard
            let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front),
            let input = try? AVCaptureDeviceInput(device: device),
            session.canAddInput(input)
        else { return }
        session.addInput(input)

        output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
        output.alwaysDiscardsLateVideoFrames = true
        output.setSampleBufferDelegate(self, queue: sessionQueue)
        guard session.canAddOutput(output) else { return }
        session.addOutput(output)

        // Deliver portrait, mirrored buffers so Vision coordinates match what
        // the driver sees in the mirrored preview — the overlay then needs no
        // extra flipping logic.
        if let connection = output.connection(with: .video) {
            if connection.isVideoOrientationSupported { connection.videoOrientation = .portrait }
            if connection.isVideoMirroringSupported { connection.isVideoMirrored = true }
        }
    }
}

extension CameraService: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(
        _ output: AVCaptureOutput,
        didOutput sampleBuffer: CMSampleBuffer,
        from connection: AVCaptureConnection
    ) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let ms = Int64(CMSampleBufferGetPresentationTimeStamp(sampleBuffer).seconds * 1000)
        onFrame?(pixelBuffer, ms)
    }
}

/// Mirrored live preview of the capture session.
struct CameraPreview: UIViewRepresentable {
    let session: AVCaptureSession

    final class PreviewView: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }
        var previewLayer: AVCaptureVideoPreviewLayer { layer as! AVCaptureVideoPreviewLayer }
    }

    func makeUIView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.previewLayer.session = session
        view.previewLayer.videoGravity = .resizeAspectFill
        return view
    }

    func updateUIView(_ uiView: PreviewView, context: Context) {}
}
