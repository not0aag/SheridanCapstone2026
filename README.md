# SafeDrive AI – Sheridan Capstone 2026

## Build Status

[![Mobile CI](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/mobile-ci.yml/badge.svg)](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/mobile-ci.yml)
[![Backend CI](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/backend-ci.yml)
[![ML CI](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/ml-ci.yml/badge.svg)](https://github.com/not0aag/SheridanCapstone2026/actions/workflows/ml-ci.yml)

---

Mission: Build SafeDrive AI — an intelligent smartphone-based driver safety system combining real-time distraction detection, drowsiness monitoring, crash detection, and video recording to prevent accidents and save lives.

This repository currently hosts Phase 1 documentation, plans, and specifications. Implementation work will live in dedicated repositories (mobile, backend, ML, infra) under the GitHub organization once created.

## Team

- Alen Aiju George — Project Manager & System Architect
- Harrison Daniel Dsouza — ML & AI Specialist
- Sukhmanpreet Singh Aulakh — Mobile Development Lead
- Neil Patrick Saldanha — Backend & Video Engineer

## Quick links

- Documentation home: `docs/`
- Architecture: `docs/architecture/system-architecture.md`
- API (OpenAPI): `docs/api/openapi.yaml`
- Timeline (Gantt): `docs/timeline/phase1-timeline.md`
- Communication & meetings: `docs/communication/channels.md`, `docs/schedule/meetings.md`
- Repo structure & automation: `docs/repo-structure.md` and `scripts/setup_repos.cmd`
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

## Development Tools

### Mock API Server

For mobile development without backend dependency:

```bash
cd tools/mock-server
npm install
npm start
```

The mock server runs on **http://localhost:3001** and provides:

- Complete API implementation matching OpenAPI spec
- JWT authentication
- Realistic mock data
- Configurable network delays and error simulation
- Video upload support

See [Mock Server README](tools/mock-server/README.md) for complete documentation.

### Mobile App

React Native app with camera, sensors, and GPS integration:

```bash
cd mobile
npm install

# Run on Android
npm run android

# Run on iOS
npm run ios
```

Features:

- Front-facing camera preview
- Accelerometer monitoring (crash detection)
- GPS tracking for speed and trip detection
- Real-time data display

### ML Proof of Concept

Jupyter notebook demonstrating all ML algorithms:

```bash
cd ml
pip install -r requirements.txt
jupyter notebook distraction_detection_poc.ipynb
```

Includes:

- MediaPipe FaceMesh (468 landmarks)
- EAR drowsiness detection
- Crash detection algorithm
- Model optimization (TFLite/Core ML)
- Performance benchmarking

### Pre-Push Validation

Run all checks before pushing code:

```bash
scripts\validate-project.cmd --all
```

Options:

- `--all` - Check all components (default)
- `--mobile` - Check mobile app only
- `--backend` - Check backend only
- `--ml` - Check ML code only
- `--mock-server` - Check mock server only

This runs:

- Linting (ESLint, Ruff)
- Type checking (TypeScript, mypy)
- Tests (Jest, pytest)
- Code formatting (Black)

## CI/CD Pipelines

Automated testing and build verification runs on every push and PR:

- **Mobile CI**: Lint → TypeScript check → Tests → Android build → iOS build
- **Backend CI**: Lint → Type check → Tests (with PostgreSQL) → Coverage → Security scan → Docker build
- **ML CI**: Lint → Notebook tests → Model validation → Performance benchmarks → Model conversions

All workflows include:

- Dependency caching for faster builds
- Matrix testing across multiple versions
- Artifact uploads for build outputs
- Coverage reporting

See `.github/workflows/` for complete pipeline configurations.

## Contributing

1. Create a feature branch from `develop`
2. Run `scripts\validate-project.cmd --all` before committing
3. Create a pull request with the [PR template](.github/pull_request_template.md)
4. Ensure all CI checks pass
5. Get approval from at least one team member

## Automated Dependency Updates

Dependabot is configured to:

- Check for dependency updates weekly (Mondays at 9 AM)
- Group minor/patch updates to reduce PR noise
- Automatically label PRs by component (mobile, backend, ml)
- Open max 5 PRs per ecosystem

See [.github/dependabot.yml](.github/dependabot.yml) for configuration.

---

**Built with ❤️ by the SafeDrive AI Team | Sheridan College 2025-2026**
