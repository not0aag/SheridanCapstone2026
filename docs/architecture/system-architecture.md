# System Architecture — SafeDrive AI (Phase 1)

```mermaid
flowchart LR
    subgraph Mobile[React Native Mobile App]
      UI[UI/UX]
      Sensors[Device Sensors\nCamera, Accelerometer, Gyro, GPS]
      OnDeviceML[On-Device ML\n(TFLite / Core ML)]
      Alerts[Alerts\nAudio / Visual / Haptic]
      UI --> Alerts
      Sensors --> OnDeviceML
      OnDeviceML --> UI
    end

    subgraph Backend[Backend (FastAPI)]
      API[REST API]
      Auth[JWT Auth]
      Svc[Services: Trips, Incidents, Videos]
      DB[(PostgreSQL)]
      Storage[(AWS S3 — Video Storage)]
      Logs[(Observability\nSentry/CloudWatch)]
      API --> Auth
      API --> Svc
      Svc --> DB
      Svc --> Storage
      API --> Logs
    end

    Mobile <--> |HTTPS / JSON| API
    Mobile --> |Chunked Upload| Storage
    Backend --> Storage

    subgraph Notifications[Notifications]
      SNS[(SES/SNS/Twilio)]
    end

    Svc --> SNS
```

## Key Decisions

- Cross-platform mobile app with React Native; on-device ML for latency and privacy
- FastAPI backend with JWT authentication; PostgreSQL as primary DB
- Video storage in S3 (pre-signed URLs) with H.264 compression
- Observability via structured logging and error tracking

## Data Flow (High Level)

1. Mobile app streams camera frames to on-device ML for face/drowsiness/distraction
2. Trip state machine gates alerts and incident logging
3. Backend manages users, trips, incidents; issues pre-signed URLs for video upload
4. Videos stored in S3; metadata in PostgreSQL
5. Notifications sent via SES/SNS/Twilio upon severe incidents
