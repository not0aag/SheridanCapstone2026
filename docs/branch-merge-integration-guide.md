# Branch Merge & Integration Guide

**Purpose:** Help the SafeDrive AI team (Alen, Neil, Sukhman, Harrison) safely integrate work from separate branches into `main`, including ML model delivery.
**Audience:** Team members with basic Git knowledge.
**Goal:** Produce a clean, tested integration in a single PR without losing work or introducing regressions.

---

## 0. Terminology

- **Feature Branches:** `alens-work`, `neils-branch`, `sukhmans-branch`
- **Integration Branch:** Temporary branch used to combine all work before merging to `main`.
- **Upstream/Main:** The canonical production-ready branch.
- **Fast-Forward Merge:** Merge that just advances a pointer (avoid for multi-author integration).
- **Non-Fast-Forward (Merge Commit):** Keeps history and shows clear integration point (preferred here).

---

## 1. Prerequisites Checklist (Do These FIRST)

Each developer ensures their branch is ready.

### 1.1 Shared Global Checks

- [ ] Local Git configured with correct user name/email.
- [ ] `git fetch --all` completes without errors.
- [ ] No uncommitted changes: `git status` shows clean working tree.
- [ ] All large binary files (ML models) tracked via Git LFS if >50MB.
- [ ] `.env` or secret files NOT committed.

### 1.2 Alen (Infrastructure)

- [ ] Mock server runs: `cd tools/mock-server && npm install && npm start`.
- [ ] OpenAPI spec (`docs/api/openapi.yaml`) matches endpoints.
- [ ] CI/CD workflows green (mobile, backend, ML, docs).
- [ ] Documentation updated (architecture, test plan).

### 1.3 Neil (Backend)

- [ ] Backend starts: `uvicorn app.main:app --reload`.
- [ ] DB migrations apply cleanly (Alembic or equivalent).
- [ ] All endpoints manually tested (auth, trip, incident, video).
- [ ] Requirements pinned (`requirements.txt`).

### 1.4 Sukhman (Mobile)

- [ ] Android build works: `npm run android`.
- [ ] iOS build works: `npm run ios` (on macOS if applicable).
- [ ] ML models placed:
  - Android: `mobile/android/app/src/main/assets/*.tflite`
  - iOS: `mobile/ios/SafeDrive/*.mlmodel`
- [ ] API config uses environment or constant (no hard-coded production secrets).

### 1.5 Harrison (ML)

- [ ] Delivered both models (TFLite + Core ML) to Sukhman.
- [ ] Documented model usage & input shape (`ml/MODEL_DELIVERY.md`).
- [ ] Benchmarks recorded (in `docs/ml_performance_report_w1.md`).

---

## 2. Create Integration Branch

Performed by Alen (or designated integrator).

```bash
# Update local main
git checkout main
git pull origin main

# Create integration branch
git checkout -b integration-week1
```

---

## 3. Merge Branches Sequentially

Merging one branch at a time simplifies conflict resolution.

### 3.1 Merge Alen's Infrastructure

```bash
git merge alens-work --no-ff -m "Merge infrastructure (mock server, CI/CD, docs)"
```

Resolve conflicts if any:

```bash
git status  # See conflicted files
# Edit each conflict, then:
git add <file1> <file2>
git commit  # Finalizes merge
```

### 3.2 Merge Neil's Backend

```bash
git merge neils-branch --no-ff -m "Merge backend (FastAPI, DB, auth, trips)"
```

Common conflict areas:

- `README.md`: Combine backend + infrastructure sections.
- `docs/api/openapi.yaml`: Ensure union of all endpoints.
- `.gitignore`: Keep superset of patterns.

### 3.3 Merge Sukhman's Mobile

```bash
git merge sukhmans-branch --no-ff -m "Merge mobile app (React Native, ML integration)"
```

Possible conflicts:

- `package.json` / `package-lock.json`: Keep all required dependencies; reinstall after.
- Shared docs (add mobile sections without deleting others).
- `.gitattributes` (ensure ML model patterns remain).

### 3.4 (Optional) Merge Harrison's Branch

If ML work exists in a branch:

```bash
git merge harrison-ml --no-ff -m "Merge ML model delivery"
```

---

## 4. Post-Merge Sanity Fixes

Run setup commands to normalize environment.

```bash
# Mobile dependencies
cd mobile
npm install

# Root (if monorepo scripts exist)
cd ..

# Backend dependencies
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Rebuild any generated files:

- Delete `node_modules` if severe package conflicts: `rm -rf node_modules && npm install`.
- Re-run database migrations.

---

## 5. Integration Testing (Manual Smoke Tests)

Execute in order; mark off when passed.

### 5.1 Backend API Smoke

```bash
cd backend
uvicorn app.main:app --reload
# Open http://localhost:8000/docs
# Test: Register, Login, Get Profile
```

Checks:

- [ ] Register returns 201 with JWT.
- [ ] Login returns 200 with JWT.
- [ ] Protected route works with Authorization header.

### 5.2 Mock Server (If Still Used)

```bash
cd tools/mock-server
npm start
# Test endpoints with curl or Postman
```

Checks:

- [ ] `/auth/login` demo user works.
- [ ] `/trips/start` then `/trips/stop` sequence works.
- [ ] `/incidents` logs incident.

### 5.3 Mobile App

```bash
cd mobile
npm start  # Start Metro
npm run android  # or npm run ios
```

Checks:

- [ ] App launches.
- [ ] User registration → login works (target backend OR mock server).
- [ ] Trip start/stop triggers correct UI state.
- [ ] ML models load (log message: "Model loaded").
- [ ] Distraction detection triggers incident.

### 5.4 ML Performance Quick Check

On device/emulator:

- [ ] Drowsiness detection returns a PERCLOS score.
- [ ] Distraction detection classifies a simple scenario (e.g., look away).
- [ ] FPS counter > 30.

### 5.5 Cross-Service Consistency

- [ ] API responses match OpenAPI spec (fields & types).
- [ ] Mobile app doesn't call undefined endpoints.
- [ ] No CORS issues (if backend supplies CORS middleware).

---

## 6. Automated Verification (CI/CD)

Push integration branch to trigger workflows.

```bash
git push origin integration-week1
```

Confirm in GitHub Actions:

- [ ] Mobile CI passes.
- [ ] Backend CI passes.
- [ ] ML CI passes.
- [ ] Docs CI passes.

If failures:

1. Open failing job logs.
2. Identify missing dependency / environment variable.
3. Patch relevant workflow file or code.
4. Commit fix → push again.

---

## 7. Final Clean-Up Before PR

### 7.1 Remove Accidental Files

Run and inspect:

```bash
git ls-files | grep -E "(\.env|\.log|node_modules|venv)"  # Should be empty except allowed patterns
```

Delete accidental commits:

```bash
git rm --cached path/to/file && git commit -m "chore: remove accidental file"
```

### 7.2 Lint & Format (If Scripts Exist)

```bash
# Example:
npm run lint  # Mobile
ruff check .  # Backend Python lint
black .       # Backend formatting (if allowed)
```

### 7.3 Consolidate Documentation

Add a summary section to `README.md` listing integrated components:

- Infrastructure (Mock server + CI/CD)
- Backend (Endpoints + DB)
- Mobile (Trip + ML models)
- ML (Delivered models)

---

## 8. Create Pull Request to Main

```bash
git checkout integration-week1
git push origin integration-week1  # If not pushed already
```

On GitHub:

1. Click "Compare & pull request".
2. Base: `main`, Compare: `integration-week1`.
3. Title: `Week 1 Integration: Infrastructure + Backend + Mobile + ML`.
4. Description: Use template (see below).

**PR Description Template:**

```markdown
## Week 1 Integration

### Included Work

- Infrastructure (Mock server, CI/CD, OpenAPI) – Alen
- Backend (Auth, Trips, Incidents, Video metadata) – Neil
- Mobile (Camera, Trip tracking, ML inference) – Sukhman
- ML Models (Distraction + Drowsiness) – Harrison

### Verification

- [x] Backend API manual tests passed
- [x] Mobile app end-to-end flows tested
- [x] ML inference stable and performant (>30 FPS)
- [x] OpenAPI spec matches deployed endpoints
- [x] CI/CD workflows all green

### Notes

- Integration tests framework planned Week 2.
- Mock server retained for local rapid prototyping.

### Next Steps

1. Switch mobile app completely to real backend.
2. Add integration test automation (Jest, Detox).
3. Implement video storage (S3) and notifications.
```

Request **at least 2 reviews** (cross-team).

---

## 9. Review & Approval Process

Reviewer checklist:

- [ ] No secrets committed.
- [ ] OpenAPI + backend alignment.
- [ ] Mobile API calls point to chosen environment.
- [ ] No massive binary files missing LFS.
- [ ] CI/CD workflows pass reliably.
- [ ] Commit messages meaningful.
- [ ] Conflict markers (e.g., `<<<<<<<`) absent.

Leave comments, request changes if necessary. Authors fix & push.

---

## 10. Merge Strategy

Use **Merge Commit** (NOT squash) to preserve branch history.
After merge:

```bash
git checkout main
git pull origin main
git branch -d integration-week1
git branch -d alens-work neils-branch sukhmans-branch  # local cleanup
```

Delete remote feature branches only if fully obsolete:

```bash
git push origin --delete alens-work
```

(Keep if future incremental work planned.)

---

## 11. Post-Merge Verification

- [ ] Pull fresh main on all machines.
- [ ] Run backend + mobile locally from `main`.
- [ ] Confirm OpenAPI served correctly.
- [ ] Tag release (optional): `git tag v0.1.0 && git push origin v0.1.0`.

---

## 12. Rollback / Hotfix Procedure

If critical bug discovered:

```bash
# Option A: Revert merge commit
git log --oneline  # Copy merge commit hash
git revert <merge-commit-hash> -m 1
git push origin main

# Option B: Hotfix branch
git checkout -b hotfix-critical
# Fix issue
git commit -m "fix: resolve critical post-merge issue"
git push origin hotfix-critical
# Open PR to main
```

Document issue in `docs/INCIDENT_LOG.md` (create if absent).

---

## 13. Common Conflict Patterns & Resolutions

| File Type      | Conflict Cause           | Resolution Strategy                            |
| -------------- | ------------------------ | ---------------------------------------------- |
| `README.md`    | Parallel section edits   | Combine sections; keep all roles clear         |
| `package.json` | Dependency additions     | Merge dependency objects; reinstall            |
| `.gitignore`   | Divergent patterns       | Union of all ignores                           |
| `OpenAPI`      | Endpoint additions       | Merge paths & schemas; validate with tool      |
| `lockfiles`    | Different install states | Prefer integrator's fresh lock after reinstall |

---

## 14. Tooling Tips

- Use `git diff --name-only integration-week1 main` before PR to preview impact.
- Run OpenAPI validation (if script added later) to ensure spec accuracy.
- Consider adding a pre-push hook to block accidental `.env` commits.

---

## 15. FAQ

**Q: Should we squash commits?**  
A: No. Preserve authorship for educational grading/audit.

**Q: Do we delete feature branches after merge?**  
A: Locally yes; remote only if you will not reuse them.

**Q: What if mobile still points to mock server?**  
A: Leave for now; switch base URL in Week 2 when backend stabilizes.

**Q: When do we add integration tests?**  
A: Planned for Week 2 after baseline merge.

---

## 16. Next Iteration Preparation (Week 2+)

Create new branches from updated `main`:

```bash
git checkout main
git pull origin main
git checkout -b week2-video-upload
```

Track upcoming tasks in a `ROADMAP.md` or GitHub Projects board.

---

## 17. Quick Command Reference

```bash
# Create integration branch
git checkout main && git pull origin main && git checkout -b integration-week1

# Merge branches
git merge alens-work --no-ff -m "Merge infrastructure"
git merge neils-branch --no-ff -m "Merge backend"
git merge sukhmans-branch --no-ff -m "Merge mobile"

# Push & open PR
git push origin integration-week1

# After merge cleanup
git checkout main && git pull origin main
git branch -d integration-week1 alens-work neils-branch sukhmans-branch
```

---

## 18. Completion Checklist (Mark Before PR)

- [ ] All feature branches merged into integration branch.
- [ ] Manual smoke tests passed (backend, mobile, mock server, ML models).
- [ ] CI/CD green on integration branch.
- [ ] OpenAPI updated & accurate.
- [ ] No secrets or large binaries untracked.
- [ ] PR description complete & reviewed.

---

**End of Guide**
