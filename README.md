<div align="center">

# 🚗 SafeDrive AI

### Intelligent Driver Safety System

[![Mobile CI](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/mobile-ci.yml/badge.svg)](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/mobile-ci.yml)
[![Backend CI](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/backend-ci.yml)
[![ML CI](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/ml-ci.yml/badge.svg)](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/ml-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Sheridan College Capstone Project 2025-2026**

[Features](#-key-features) • [Tech Stack](#-technology-stack) • [Getting Started](#-getting-started) • [Documentation](#-documentation) • [Team](#-team)

</div>

---

## 📖 About SafeDrive AI

**SafeDrive AI** is an intelligent smartphone-based driver safety system that leverages on-device machine learning to prevent accidents and save lives. The system provides real-time monitoring and alerts for dangerous driving behaviors while maintaining user privacy through edge computing.

### The Problem

Distracted and drowsy driving causes over **3,000 deaths annually** in the United States alone. Traditional solutions require expensive hardware installations or compromise user privacy by processing biometric data in the cloud.

### Our Solution

SafeDrive AI transforms any smartphone into an intelligent driving companion:

- **Privacy-First Architecture**: All biometric processing happens on-device using TensorFlow Lite and Core ML
- **Real-Time Alerts**: Detects dangerous behaviors within 2 seconds and provides immediate audio/visual/haptic feedback
- **Comprehensive Safety Net**: Monitors distraction, drowsiness, and crash events with video evidence
- **Seamless Integration**: Works with existing smartphones—no additional hardware required

---

## ✨ Key Features

### 🎯 Real-Time Distraction Detection (97% Target Accuracy)

- Detects 10 distraction types: phone use, looking away, eating, drinking, smoking, reading, grooming, passenger interaction, and more
- Uses MediaPipe FaceMesh with 468 facial landmarks
- Custom MobileNetV2-based classifier optimized for mobile devices
- Alert latency < 2 seconds

### 😴 Drowsiness Monitoring (PERCLOS Algorithm)

- Continuous eye closure monitoring using Eye Aspect Ratio (EAR)
- PERCLOS (Percentage of Eye Closure) calculation over rolling 60-second windows
- Intelligent alerting with escalating severity (gentle → aggressive warnings)
- Validated against clinical drowsiness benchmarks

### 🚨 Crash Detection with Emergency SOS

- Multi-axis accelerometer monitoring at 50Hz
- Peak G-force detection with intelligent validation to reduce false positives
- Automatic emergency contact notification via SMS/email
- GPS coordinates transmitted to emergency services
- Countdown timer allowing cancellation of false alarms

### 📹 Continuous Video Recording (1080p @ 30fps)

- Circular buffer recording (last 10 minutes retained)
- Automatic incident-triggered saving
- H.264 compression with optimized bitrate
- Secure upload to AWS S3 with intelligent tiering
- GDPR/BIPA compliant storage with automatic deletion policies

### 🔒 On-Device ML Processing (Privacy-First)

- Zero biometric data leaves the device
- iOS: Core ML with Apple Neural Engine acceleration
- Android: TensorFlow Lite with XNNPACK delegate
- Model size: ~3MB per classifier
- Inference time: <40ms per frame (>25 FPS)

### 📊 Trip Analytics & Safety Scoring

- Comprehensive trip summaries with distance, duration, and safety metrics
- Safety score calculation based on incident frequency and severity
- Historical trend analysis
- Shareable trip reports for insurance or fleet management

---

## 🛠️ Technology Stack

<table>
<tr>
<td valign="top" width="33%">

### Mobile Application

- **Framework**: React Native 0.73
- **Language**: TypeScript 5.3
- **Camera**: react-native-vision-camera
- **Sensors**: react-native-sensors
- **State**: Redux Toolkit + RTK Query
- **Navigation**: React Navigation 6
- **Storage**: SQLite + AsyncStorage
- **ML**: TensorFlow Lite (Android), Core ML (iOS)

</td>
<td valign="top" width="33%">

### Backend Services

- **Framework**: FastAPI 0.104
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (python-jose)
- **File Storage**: AWS S3
- **Notifications**: Twilio, AWS SES
- **Monitoring**: Sentry, CloudWatch

</td>
<td valign="top" width="33%">

### Machine Learning

- **Framework**: TensorFlow 2.15
- **Face Detection**: MediaPipe FaceMesh
- **Model Architecture**: MobileNetV2
- **Optimization**: TFLite, Core ML Tools
- **Training**: Jupyter, Python 3.11
- **Datasets**: Custom labeled dataset
- **Performance**: <40ms inference, ~3MB models

</td>
</tr>
</table>

### Infrastructure & DevOps

- **CI/CD**: GitHub Actions
- **Dependency Management**: Dependabot
- **Code Quality**: ESLint, Ruff, Black, mypy
- **Testing**: Jest, pytest, Detox (E2E)
- **Documentation**: OpenAPI 3.0, Mermaid
- **Cloud**: AWS (EC2, RDS, S3)

---

## 📁 Project Structure

```
SafeDriveAI/
├── 📱 mobile/                    # React Native mobile application
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── screens/             # Screen components
│   │   ├── services/            # API clients, ML inference
│   │   ├── hooks/               # Custom React hooks
│   │   ├── navigation/          # Navigation configuration
│   │   ├── store/               # Redux store
│   │   └── utils/               # Helper functions
│   ├── assets/
│   │   ├── models/              # TFLite & Core ML models
│   │   └── images/              # App icons, splash screens
│   ├── android/                 # Android native code
│   ├── ios/                     # iOS native code
│   └── package.json
│
├── 🖥️ backend/                   # FastAPI backend services
│   ├── app/
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── middleware/          # Auth, CORS, etc.
│   │   └── utils/               # Helper functions
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # pytest test suite
│   └── requirements.txt
│
├── 🤖 ml/                        # Machine Learning models
│   ├── src/                     # Training scripts
│   ├── notebooks/               # Jupyter notebooks (POC)
│   ├── models/                  # Trained model artifacts
│   ├── datasets/                # Training datasets (gitignored)
│   ├── docs/                    # ML documentation
│   └── requirements.txt
│
├── 🔧 tools/                     # Development utilities
│   └── mock-server/             # Express.js mock API server
│       ├── routes/              # Mock API endpoints
│       ├── middleware/          # Auth, delay, error simulation
│       └── data/                # Seed data
│
├── 📚 docs/                      # Project documentation
│   ├── api/                     # OpenAPI specification
│   ├── architecture/            # System architecture
│   ├── timeline/                # Project timelines
│   ├── communication/           # Team communication
│   └── schedule/                # Meeting schedules
│
├── 🚀 .github/                   # GitHub configuration
│   ├── workflows/               # CI/CD pipelines
│   ├── dependabot.yml           # Dependency automation
│   └── pull_request_template.md
│
└── 📜 scripts/                   # Utility scripts
    ├── validate-project.cmd     # Pre-push validation
    └── setup_repos.cmd          # Repository setup
```

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

#### For Mobile Development

- **Node.js** 18.x or 20.x (LTS recommended)
- **npm** 9.x or **Yarn** 1.22+
- **React Native CLI**: `npm install -g react-native-cli`
- **Android Studio** (for Android development)
  - Android SDK Platform 33
  - Android SDK Build-Tools 33.0.0
  - Android Emulator
- **Xcode** 15+ (for iOS development, macOS only)
  - iOS 16.0+ SDK
  - CocoaPods: `sudo gem install cocoapods`

#### For Backend Development

- **Python** 3.11 or higher
- **pip** 23+
- **PostgreSQL** 15+
- **Docker** (optional, for containerized development)

#### For ML Development

- **Python** 3.11
- **Jupyter** Lab or Notebook
- **CUDA** 11.8+ (optional, for GPU training)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/not0aag/SheridanCapstone2026.git
cd SheridanCapstone2026
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL database
createdb safedrive_dev

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

**Backend will run at:** `http://localhost:8000`  
**API Documentation:** `http://localhost:8000/docs`

#### 3. Mobile App Setup

```bash
cd mobile

# Install dependencies
npm install

# iOS: Install CocoaPods dependencies (macOS only)
cd ios && pod install && cd ..

# Start Metro bundler
npm start

# In a new terminal, run on Android
npm run android

# Or run on iOS (macOS only)
npm run ios
```

#### 4. Mock API Server (For Mobile Development Without Backend)

```bash
cd tools/mock-server

# Install dependencies
npm install

# Start mock server
npm start
```

**Mock Server runs at:** `http://localhost:3001`

#### 5. ML Development Setup

```bash
cd ml

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch Jupyter
jupyter notebook
```

### Environment Variables

#### Backend `.env`

Create `backend/.env`:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/safedrive_dev
JWT_SECRET=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
S3_BUCKET_NAME=safedrive-videos

TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

SENTRY_DSN=your-sentry-dsn  # Optional
```

#### Mobile `mobile/.env`

Create `mobile/.env`:

```bash
API_URL=http://localhost:8000
# Or use mock server:
# API_URL=http://localhost:3001

ENVIRONMENT=development
```

---

## 📖 Documentation

- **[API Documentation](docs/api/openapi.yaml)** - Complete OpenAPI 3.0 specification
- **[Mock Server Guide](tools/mock-server/README.md)** - Mock API server usage

---

## 👥 Team

<table>
<tr>
<td align="center" width="25%">
<img src="https://via.placeholder.com/150" width="100px;" alt="Alen"/>
<br />
<b>Alen Aiju George</b>
<br />
<i>Project Manager & System Architect</i>
<br />
Infrastructure • Documentation • CI/CD
</td>
<td align="center" width="25%">
<img src="https://via.placeholder.com/150" width="100px;" alt="Harrison"/>
<br />
<b>Harrison Daniel Dsouza</b>
<br />
<i>ML & AI Specialist</i>
<br />
Model Training • Optimization • Validation
</td>
<td align="center" width="25%">
<img src="https://via.placeholder.com/150" width="100px;" alt="Sukhman"/>
<br />
<b>Sukhmanpreet Singh Aulakh</b>
<br />
<i>Mobile Development Lead</i>
<br />
React Native • Camera • Sensors • ML Integration
</td>
<td align="center" width="25%">
<img src="https://via.placeholder.com/150" width="100px;" alt="Neil"/>
<br />
<b>Neil Patrick Saldanha</b>
<br />
<i>Backend & Video Engineer</i>
<br />
FastAPI • PostgreSQL • S3 • Notifications
</td>
</tr>
</table>

---

## 📅 Project Timeline

### Phase 1: Prototype Development

**Duration:** November 5 - December 4, 2025 (4 weeks)

#### Week 1 (Nov 5-11): Foundation ✅

- ML model architecture and initial training
- Infrastructure setup (repos, CI/CD)
- Basic mobile app structure
- Mock API server

#### Week 2 (Nov 12-18): Core Features 🔄

- Distraction detection integration
- Drowsiness monitoring (PERCLOS)
- Backend API implementation
- Database schema and migrations

#### Week 3 (Nov 19-25): Integration & Testing

- End-to-end testing
- Video recording and upload
- Crash detection implementation
- Performance optimization

#### Week 4 (Nov 26-Dec 4): Polish & Demo

- UI/UX refinements
- Documentation completion
- Final demo preparation
- Presentation materials

**Final Presentation:** December 4, 2025

## Quick links

- Documentation home: `docs/`
- API (OpenAPI): `docs/api/openapi.yaml`
- Repo structure & automation: `scripts/setup_repos.cmd`
- Mock API Server: `tools/mock-server/` — [Quick Start](tools/mock-server/README.md)
- ML POC Notebook: `ml/distraction_detection_poc.ipynb`
- Mobile App: `mobile/` — React Native app with camera, sensors, GPS

## Phase 1 (Prototype) — Nov 5 to Dec 4, 2025

Core prototype goals:

- Real-time face detection and tracking (MediaPipe FaceMesh)
- Basic distraction detection (looking away, phone use)
- Drowsiness monitoring (PERCLOS/EAR)
- Crash detection using accelerometer
- Basic video recording (1080p @ 30fps)
- Simple alerting (audio/visual/haptic)
- Backend API for data storage
- Basic mobile UI

---

## 🧪 Development Tools & Workflows

### Mock API Server

For mobile development without backend dependency:

```bash
cd tools/mock-server
npm install
npm start
```

**Features:**

- Complete API implementation matching OpenAPI spec
- JWT authentication with demo users
- Realistic mock data (3 users, 10 trips, 25 incidents, 8 videos)
- Configurable network delays and error simulation
- Video upload support

**Demo Login:**

- Email: `demo@safedrive.ai`
- Password: `Demo123456!`

See [Mock Server README](tools/mock-server/README.md) for complete documentation.

### Pre-Push Validation

Run all checks before pushing code:

```bash
scripts\validate-project.cmd --all
```

**Options:**

- `--all` - Check all components (default)
- `--mobile` - Check mobile app only
- `--backend` - Check backend only
- `--ml` - Check ML code only
- `--mock-server` - Check mock server only

**Checks Performed:**

- Linting (ESLint, Ruff)
- Type checking (TypeScript, mypy)
- Unit tests (Jest, pytest)
- Code formatting (Prettier, Black)

### CI/CD Pipelines

Automated workflows run on every push and PR:

#### Mobile CI (`mobile-ci.yml`)

1. **Lint** - ESLint + Prettier
2. **Type Check** - TypeScript compiler
3. **Test** - Jest unit tests (Node 18/20 matrix)
4. **Build Android** - `assembleDebug` with Gradle caching
5. **Build iOS** - Xcode build with CocoaPods caching
6. **Coverage** - Codecov upload

#### Backend CI (`backend-ci.yml`)

1. **Lint** - Ruff + Black
2. **Type Check** - mypy static analysis
3. **Test** - pytest with PostgreSQL service container
4. **Coverage** - 70% minimum threshold
5. **Security** - Bandit vulnerability scan
6. **Docker** - Build validation

#### ML CI (`ml-ci.yml`)

1. **Lint** - Python notebook linting
2. **Notebook Tests** - Papermill execution
3. **Model Validation** - MediaPipe + TensorFlow checks
4. **Performance** - Inference benchmarks (<50ms target)
5. **Conversion** - TFLite + Core ML export tests

All workflows include dependency caching for 60-80% faster builds.

---

## 🤝 Contributing

We follow a structured branching and review process:

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch (future)
- `alens-work` - Alen's infrastructure and documentation
- `neils-branch` - Neil's backend development
- `sukhmans-branch` - Sukhman's mobile development
- `feature/*` - Individual feature branches

### Contribution Workflow

1. **Create Branch**: `git checkout -b feature/your-feature-name`
2. **Develop**: Write code following style guidelines
3. **Validate**: Run `scripts\validate-project.cmd --all`
4. **Commit**: Use [Conventional Commits](https://www.conventionalcommits.org/)
   ```bash
   git commit -m "feat(mobile): add distraction detection screen"
   git commit -m "fix(backend): resolve JWT token expiration bug"
   git commit -m "docs: update API documentation"
   ```
5. **Push**: `git push origin feature/your-feature-name`
6. **Pull Request**: Use the [PR template](.github/pull_request_template.md)
7. **Review**: Get approval from at least one team member
8. **Merge**: Ensure all CI checks pass before merging

### Code Style Guidelines

- **TypeScript/JavaScript**: ESLint + Prettier
- **Python**: Ruff + Black + mypy
- **Commit Messages**: Conventional Commits format
- **Branch Names**: `feature/`, `fix/`, `docs/`, `chore/`

---

## 🔄 Automated Dependency Updates

Dependabot is configured for automated security and dependency updates:

**Configuration:**

- **Schedule**: Weekly, every Monday at 9:00 AM
- **Ecosystems**: npm (mobile), npm (mock-server), pip (backend), pip (ml), github-actions
- **Strategy**: Grouped updates for minor/patch versions
- **PR Limit**: Maximum 5 PRs per ecosystem
- **Auto-labeling**: `dependencies`, `mobile`, `backend`, `ml`, `github-actions`

See [.github/dependabot.yml](.github/dependabot.yml) for full configuration.

---

## 📊 Performance Metrics & Targets

| Metric               | Target  | Critical Threshold | Current Status          |
| -------------------- | ------- | ------------------ | ----------------------- |
| ML Inference Time    | <40ms   | <100ms             | ✅ 22-38ms (Week 1)     |
| Alert Latency        | <2s     | <5s                | 🔄 In Testing           |
| API Response Time    | <500ms  | <1000ms            | 🔄 Backend WIP          |
| Battery Drain        | <12%/hr | <15%/hr            | 🔄 Optimization Pending |
| Distraction Accuracy | >97%    | >90%               | ✅ 87.3% (Training)     |
| False Positive Rate  | <5%     | <10%               | 🔄 Validation Needed    |
| FPS (Mobile)         | >25     | >15                | ✅ 30-45 FPS            |

---

## 🔒 Security & Privacy

### Privacy-First Architecture

- **On-Device Processing**: All biometric data (facial landmarks, eye tracking) processed locally
- **Zero Cloud Biometrics**: Face data never leaves the device
- **Encrypted Storage**: AES-256 encryption for local databases
- **TLS 1.3**: All API communication encrypted
- **GDPR/BIPA Compliant**: Automatic data deletion policies

### Security Measures

- JWT token authentication with short expiration (24 hours)
- bcrypt password hashing (cost factor 12)
- Input validation and sanitization
- Rate limiting on API endpoints
- SQL injection prevention (parameterized queries)
- XSS protection in mobile WebViews
- Sentry error tracking (no PII logged)

---

## 📱 App Store Deployment (Future)

### iOS App Store

- **Target**: iOS 16.0+
- **Bundle ID**: `com.safedrive.app`
- **Privacy Manifest**: Camera, Location, Sensors
- **TestFlight**: Beta testing program

### Google Play Store

- **Target**: Android 13+ (SDK 33)
- **Package Name**: `com.safedrive.app`
- **Permissions**: Camera, Location, Sensors, Storage
- **Internal Testing**: Closed alpha track

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**Note**: This is an academic capstone project for Sheridan College. Commercial use requires permission.

---

## 🙏 Acknowledgments

- **Sheridan College** - Project supervision and resources
- **MediaPipe** - Open-source face detection framework
- **TensorFlow** - Machine learning infrastructure
- **React Native Community** - Excellent mobile framework and plugins
- **FastAPI** - Modern Python web framework

---

## 📞 Contact & Support

- **Project Lead**: Alen Aiju George - [@not0aag](https://github.com/not0aag)
- **Repository**: [SheridanCapstone2026](https://github.com/not0aag/SheridanCapstone2026)
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/not0aag/SheridanCapstone2026/issues)

---

<div align="center">

**Built with ❤️ by the SafeDrive AI Team | Sheridan College 2025-2026**

[⬆ Back to Top](#-safedrive-ai)

</div>
