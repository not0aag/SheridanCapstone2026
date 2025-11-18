# Integration Test Plan

**Status:** Deferred to Week 2 (Post-Infrastructure Phase)  
**Owner:** Team  
**Last Updated:** November 18, 2025

---

## Overview

This document outlines the integration testing strategy for SafeDrive AI Phase 1 prototype. Integration tests will verify end-to-end functionality across mobile app, mock API server, and ML components.

## Scope

### In Scope
- Mobile ↔ Mock API Server integration
- Auth flow (register → login → authenticated requests)
- Trip lifecycle (start → log incidents → stop)
- Video upload workflow (request pre-signed URL → metadata storage)
- ML model integration (MediaPipe FaceMesh on mobile)
- Error handling and retry logic

### Out of Scope (Future Phases)
- Production backend integration
- S3 video storage (mock server simulates this)
- PostgreSQL database integration
- Real-time WebSocket notifications

---

## Test Strategy

### 1. API Integration Tests
**Tool:** Jest + Supertest  
**Location:** `tests/integration/api/`

- User registration and authentication
- JWT token validation and expiry
- Trip CRUD operations
- Incident logging
- Video upload simulation

### 2. Mobile Integration Tests
**Tool:** Detox (React Native E2E)  
**Location:** `mobile/e2e/`

- Camera permissions and initialization
- ML model loading and inference
- API client with auth interceptors
- Trip state machine transitions
- Offline mode and data sync

### 3. Mock Server Contract Tests
**Tool:** Pact or OpenAPI validation  
**Location:** `tests/contract/`

- Verify mock server matches `openapi.yaml` specification
- Response schema validation
- Error response consistency

---

## Test Environment

### Mock Server Setup
```bash
cd tools/mock-server
npm install
npm run dev  # Starts on port 3000
```

### Mobile App (Android Emulator)
```bash
cd mobile
npm install
npm run android
```

### Test Data
- Use mock server seed data (3 users, 10 trips, 25 incidents)
- Reset via `POST /debug/reset` between test suites

---

## Test Scenarios

### Scenario 1: New User Registration
1. Mobile app sends POST `/auth/register`
2. Verify 201 response with JWT token
3. Use token to access GET `/users/me`
4. Verify user profile returned

### Scenario 2: Complete Trip Flow
1. Authenticate user
2. Start trip: POST `/trips/start`
3. Log incident: POST `/incidents` (with trip_id)
4. Stop trip: POST `/trips/stop`
5. Verify trip status = "completed"
6. Fetch incidents: GET `/incidents/trip/{tripId}`

### Scenario 3: Video Upload Workflow
1. Request upload URL: POST `/videos/upload`
2. Verify presigned URLs returned
3. Simulate chunk upload (not tested in mock)
4. Fetch video metadata: GET `/videos/{videoId}`

### Scenario 4: Offline Mode
1. Start trip while online
2. Disable network (airplane mode)
3. Log incidents (queued locally)
4. Re-enable network
5. Verify incidents sync to server

### Scenario 5: ML Model Integration
1. Load MediaPipe FaceMesh on app start
2. Process camera frame
3. Detect drowsiness (PERCLOS < threshold)
4. Trigger incident POST `/incidents`
5. Verify incident logged with correct type

---

## Success Criteria

- ✅ 90%+ code coverage for API client
- ✅ All critical user flows tested end-to-end
- ✅ No network errors under normal conditions
- ✅ Graceful degradation when API unavailable
- ✅ ML inference completes within 50ms per frame

---

## Timeline

| Phase | Tasks | Target |
|-------|-------|--------|
| **Week 2** | Setup Jest + Supertest, write API integration tests | Nov 25 |
| **Week 3** | Setup Detox, write mobile E2E tests | Dec 2 |
| **Week 4** | Contract tests, CI integration | Dec 9 |

---

## Current Status (Week 1)

❌ **Not Started** — Intentionally deferred to allow core infrastructure completion.

**Rationale:**
- Mock server and CI/CD pipelines needed first
- Mobile app foundation required before E2E tests
- ML model integration still in POC phase

**Next Actions:**
1. Complete mobile app camera integration (Week 2)
2. Finalize ML model deployment strategy
3. Setup Jest/Detox test environments
4. Write first integration test suite

---

## References

- Mock API Server: `tools/mock-server/README.md`
- API Specification: `docs/api/openapi.yaml`
- Mobile App: `mobile/README.md`
- System Architecture: `docs/architecture/system-architecture.md`

---

## Notes

- Integration tests will run in CI/CD after Week 2
- Use `ENABLE_ERROR_SIMULATION=true` to test error handling
- Mock server delay simulation helps test loading states
- Consider adding integration test badge to main README once implemented
