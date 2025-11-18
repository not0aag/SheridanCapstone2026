# GitHub Issue Template

**To manually create the issue on GitHub:**

1. Go to: https://github.com/not0aag/SheridanCapstone2026/issues/new
2. Copy and paste the content below

---

## Title
Infrastructure: Development tools and CI/CD pipelines

## Labels
`infrastructure`, `enhancement`

## Description

### Overview
This issue tracks the complete development infrastructure for SafeDrive AI Phase 1 prototype, implemented in PR #1.

### Components Delivered

#### 1. Mock API Server (`tools/mock-server/`)
- **Tech Stack:** Express.js 4.18.2, JWT authentication, bcrypt password hashing
- **Endpoints:** 15 routes (auth, trips, incidents, videos, debug)
- **Features:**
  - In-memory database with seed data (3 users, 10 trips, 25 incidents, 8 videos)
  - Configurable response delays (`RESPONSE_DELAY_MS`)
  - Error simulation mode (`ENABLE_ERROR_SIMULATION`)
  - CORS enabled for local development
  - Comprehensive API documentation in README
- **Files:** 15 implementation files (~2000 lines of code)

#### 2. CI/CD Pipelines (`.github/workflows/`)

**Mobile CI** (`mobile-ci.yml`, 103 lines):
- ESLint + TypeScript type checking
- Jest unit tests (Node 18/20 matrix)
- Android build (assembleDebug with Gradle caching)
- iOS build (CocoaPods with caching)
- Codecov integration

**Backend CI** (`backend-ci.yml`, 120 lines):
- Ruff + Black linting
- mypy type checking
- pytest with PostgreSQL service container
- 70% coverage requirement
- Bandit security scanning
- Docker build validation

**ML CI** (`ml-ci.yml`, 158 lines):
- Lint Python notebooks
- Papermill notebook execution tests
- MediaPipe + TensorFlow model validation
- Performance benchmarks (<50ms target)
- TFLite conversion tests
- Graceful handling of missing dependencies

**Documentation CI** (`docs-ci.yml`, 65 lines):
- Markdown linting
- Link validation
- GitHub Pages deployment

#### 3. Automation & Quality Tools

- **Dependabot:** 5 ecosystems (npm mobile, npm mock-server, pip backend, pip ml, github-actions)
  - Weekly updates every Monday at 9 AM
  - Grouped dependency updates
- **PR Template:** 60-line comprehensive template with:
  - Description and type selection
  - Testing checklist
  - Platform-specific sections (mobile/backend/ML)
  - Breaking changes documentation
  - Deployment notes
- **Validation Script:** `scripts/validate-project.cmd` (Windows batch)
  - Pre-push validation
  - Checks for common issues

#### 4. Documentation

- **OpenAPI 3.0.3 Spec:** `docs/api/openapi.yaml` (295 lines)
  - All mock server endpoints documented
  - Request/response schemas
  - Bearer token authentication
  - Development and production servers
- **Integration Test Plan:** `docs/integration-test-plan.md`
  - Strategy for API, mobile E2E, and contract tests
  - Test scenarios and success criteria
  - Deferred to Week 2 (intentional)
- **Mock Server Data Flow:** Added to `docs/architecture/system-architecture.md`
  - Sequence diagram for auth, trips, incidents, videos
  - Comparison table: mock vs. production architecture
  - Endpoint reference and seed data documentation
- **Updated Main README:** CI/CD badges, development tools section

### Status

✅ **Completed:**
- Mock API Server (100%)
- All 4 CI/CD pipelines (100%)
- Automation configuration (100%)
- API specifications (100%)
- Data flow documentation (100%)
- Integration test plan (documented, deferred to Week 2)

⏳ **Deferred to Week 2:**
- Integration test implementation (intentional - infrastructure comes first)

### Testing

All CI/CD workflows are passing:
- ✅ Mobile CI: Lint, test, Android/iOS builds
- ✅ Backend CI: Lint, type-check, pytest, security scan
- ✅ ML CI: Notebook tests, model validation, benchmarks
- ✅ Docs CI: Markdown lint, link check

### Files Changed

- **Added:** 44 files
- **Insertions:** 17,956 lines
- **Deletions:** 1 line

### Related PR

Closes #1

### Next Steps

1. Merge PR #1 to main branch
2. Begin Week 2 work:
   - Implement integration tests (Jest + Detox)
   - Add rate limiting to mock server
   - Create mobile integration guide
   - Setup logging and analytics

---

**Created:** November 18, 2025  
**Owner:** @not0aag (Alen Aiju George)  
**Branch:** `alens-work`
