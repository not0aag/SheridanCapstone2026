import ARKit
import AVFoundation
import SceneKit
import SwiftUI
import UIKit

/// Front-camera capture and face tracking, tuned for continuous driver
/// monitoring.
///
/// Two backends behind one interface (`onSnapshot`):
/// - **ARKit** (`ARFaceTrackingConfiguration`) on any TrueDepth-equipped
///   device (iPhone X, 2017, and later) — real 3D head pose/gaze from the
///   depth sensor. This is the primary path; see `ARFaceTracker.swift` for
///   why it replaced the Vision-only pipeline.
/// - **Vision** (`AVCaptureSession` + `FaceTracker`) as a fallback on
///   hardware without TrueDepth, or the Simulator — same "degrade
///   gracefully, don't crash" pattern Android uses for its MediaPipe
///   native-lib fallback (`CombinedDetectionEngine.kt`).
///
/// Callers (`DriverMonitor`) only ever see `onSnapshot`/`start`/`stop`/
/// `setFrameRate` — which backend is active is an implementation detail.
final class CameraService: NSObject, ObservableObject {
    /// True when the device has a TrueDepth front camera (iPhone X, 2017,
    /// and later) and can run ARKit face tracking. False on older hardware
    /// and in the Simulator, which fall back to the Vision path below.
    let usingARKit = ARFaceTrackingConfiguration.isSupported

    let arSession = ARSession()
    let visionSession = AVCaptureSession()

    @Published private(set) var isRunning = false
    @Published private(set) var permissionDenied = false

    /// Fires for every processed frame, regardless of which backend produced it.
    var onSnapshot: ((FaceSnapshot) -> Void)?

    private let arTracker = ARFaceTracker()
    private let visionTracker = FaceTracker()

    private let visionOutput = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "safedrive.camera", qos: .userInitiated)
    private var visionConfigured = false
    private var wasRunningBeforeBackground = false

    override init() {
        super.init()
        arTracker.onSnapshot = { [weak self] in self?.onSnapshot?($0) }
        visionTracker.onSnapshot = { [weak self] in self?.onSnapshot?($0) }
        arSession.delegateQueue = sessionQueue
        arSession.delegate = self

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
            self?.resumeIfNeeded()
        }
        NotificationCenter.default.addObserver(
            forName: UIApplication.didEnterBackgroundNotification, object: nil, queue: .main
        ) { [weak self] _ in
            // ARKit does not permit background camera access at all (unlike
            // AVCaptureSession's multitasking camera access) — pause fully
            // rather than merely throttling, and resume on foreground.
            self?.pauseARForBackground()
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
        wasRunningBeforeBackground = false
        if usingARKit {
            arSession.pause()
            DispatchQueue.main.async { self.isRunning = false }
        } else {
            sessionQueue.async { [self] in
                guard visionSession.isRunning else { return }
                visionSession.stopRunning()
                DispatchQueue.main.async { self.isRunning = false }
            }
        }
    }

    /// 30 fps while on screen; 15 fps when backgrounded to halve battery
    /// cost — Vision path only. ARKit doesn't expose a configurable capture
    /// frame rate the way AVCaptureDevice did (face tracking runs at a
    /// fixed native rate), so this is a no-op under ARKit; background power
    /// saving there is handled by fully pausing instead (see
    /// `pauseARForBackground`). Kept as a real method either way so
    /// `DriverMonitor`'s existing foreground/background calls don't need
    /// to know which backend is active.
    func setFrameRate(_ fps: Int) {
        guard !usingARKit else { return }
        sessionQueue.async { [self] in
            guard let device = (visionSession.inputs.first as? AVCaptureDeviceInput)?.device,
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
        if usingARKit {
            let configuration = ARFaceTrackingConfiguration()
            configuration.isLightEstimationEnabled = false
            arSession.run(configuration, options: [.resetTracking, .removeExistingAnchors])
            wasRunningBeforeBackground = true
            DispatchQueue.main.async { self.isRunning = true }
        } else {
            sessionQueue.async { [self] in
                configureVisionIfNeeded()
                guard !visionSession.isRunning else { return }
                visionSession.startRunning()
                DispatchQueue.main.async { self.isRunning = true }
            }
        }
    }

    private func pauseARForBackground() {
        guard usingARKit, isRunning else { return }
        wasRunningBeforeBackground = true
        arSession.pause()
        isRunning = false
    }

    private func resumeIfNeeded() {
        guard usingARKit, wasRunningBeforeBackground, !isRunning else { return }
        startSession()
    }

    // MARK: Vision fallback (unsupported hardware / Simulator)

    private func configureVisionIfNeeded() {
        guard !visionConfigured else { return }
        visionSession.beginConfiguration()
        defer { visionSession.commitConfiguration(); visionConfigured = true }

        // 640×480 is plenty for face landmarks and much cheaper than HD.
        visionSession.sessionPreset = .vga640x480

        if visionSession.isMultitaskingCameraAccessSupported {
            visionSession.isMultitaskingCameraAccessEnabled = true
        }

        guard
            let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front),
            let input = try? AVCaptureDeviceInput(device: device),
            visionSession.canAddInput(input)
        else { return }
        visionSession.addInput(input)

        visionOutput.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
        visionOutput.alwaysDiscardsLateVideoFrames = true
        visionOutput.setSampleBufferDelegate(self, queue: sessionQueue)
        guard visionSession.canAddOutput(visionOutput) else { return }
        visionSession.addOutput(visionOutput)

        // Deliver portrait, mirrored buffers so Vision coordinates match what
        // the driver sees in the mirrored preview — the overlay then needs no
        // extra flipping logic.
        if let connection = visionOutput.connection(with: .video) {
            if connection.isVideoOrientationSupported { connection.videoOrientation = .portrait }
            if connection.isVideoMirroringSupported { connection.isVideoMirrored = true }
        }
    }
}

extension CameraService: ARSessionDelegate {
    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        arTracker.process(frame: frame)
    }

    func sessionWasInterrupted(_ session: ARSession) {
        DispatchQueue.main.async { self.isRunning = false }
    }

    func sessionInterruptionEnded(_ session: ARSession) {
        DispatchQueue.main.async { self.resumeIfNeeded() }
    }

    func session(_ session: ARSession, didFailWithError error: Error) {
        DispatchQueue.main.async { self.isRunning = false }
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
        visionTracker.process(pixelBuffer: pixelBuffer, timestampMs: ms)
    }
}

/// Mirrored live preview — an `ARSCNView` bound to the AR session when
/// ARKit face tracking is active, or the old `AVCaptureVideoPreviewLayer`
/// bound to the Vision-fallback session otherwise. ARKit shows the front
/// camera unmirrored by default, so it's flipped for a selfie-mirror feel;
/// the Vision path is mirrored upstream at the capture-connection level
/// instead (see `configureVisionIfNeeded`).
struct CameraPreview: UIViewRepresentable {
    let camera: CameraService

    func makeUIView(context: Context) -> UIView {
        if camera.usingARKit {
            let view = ARSCNView()
            view.session = camera.arSession
            view.automaticallyUpdatesLighting = false
            view.transform = CGAffineTransform(scaleX: -1, y: 1)
            return view
        } else {
            let view = VisionPreviewView()
            view.previewLayer.session = camera.visionSession
            view.previewLayer.videoGravity = .resizeAspectFill
            return view
        }
    }

    func updateUIView(_ uiView: UIView, context: Context) {}

    final class VisionPreviewView: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }
        var previewLayer: AVCaptureVideoPreviewLayer { layer as! AVCaptureVideoPreviewLayer }
    }
}
