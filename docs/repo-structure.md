# GitHub Organization & Repository Structure (Plan)

This repository holds the Phase 1 docs. Create a GitHub organization (e.g., `safedrive-ai`) and the following repos:

- safedrive-mobile — React Native app (iOS/Android)
- safedrive-backend — FastAPI + PostgreSQL + AWS S3
- safedrive-ml — notebooks, models (TFLite/Core ML), benchmarks
- safedrive-infra — IaC (IaC option TBD), CI/CD workflows, deployment
- safedrive-docs — documentation (this repo, or move docs here later)

## Automation (optional, requires GitHub CLI `gh`)

Replace ORG with your org name. Run in Windows cmd after authenticating `gh auth login`.

```bat
@echo off
set ORG=safedrive-ai
for %%R in (mobile backend ml infra docs) do (
  echo Creating repo safedrive-%%R in org %ORG% ...
  gh repo create %ORG%/safedrive-%%R --public --confirm --disable-wiki --description "SafeDrive AI %%R"
)
```

## Access & Branching

- Default branch: `main`
- Require PR reviews; enable status checks (lint/tests) before merge
- Protect `main` from force pushes; use squash merges

## Issue Templates

- Bug report, feature request, task template; add labels per team (mobile/ml/backend/infra)
