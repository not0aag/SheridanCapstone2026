# Phase 1 Timeline (Prototype) — Nov 5 to Dec 4, 2025

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title SafeDrive AI — Phase 1 Gantt
    excludes weekends

    section PM & Architecture (Alen)
    Docs repo & comms         :alen1, 2025-11-05, 2d
    System architecture       :alen2, after alen1, 2d
    API draft (OpenAPI)       :alen3, after alen2, 2d
    Timeline & dependencies   :alen4, 2025-11-07, 1d

    section ML (Harrison)
    Env setup & FaceMesh test :har1, 2025-11-06, 3d
    PERCLOS research          :har2, after har1, 1d
    Face detection POC        :har3, after har1, 3d

    section Mobile (Sukhman)
    RN env & project          :suk1, 2025-11-06, 2d
    Camera lib research       :suk2, after suk1, 2d
    Camera POC 1080p@30fps    :suk3, after suk2, 2d

    section Backend (Neil)
    FastAPI env & DB setup    :neil1, 2025-11-06, 2d
    Schema/ERD                :neil2, after neil1, 1d
    Users CRUD endpoints      :neil3, after neil2, 2d

    section Week 2 Highlights
    Drowsiness POC & classifier: 2025-11-12, 4d
    Camera→ML pipeline        : 2025-11-12, 4d
    Trips/Incidents endpoints : 2025-11-12, 3d

    section Week 3 Highlights
    iOS parity & video record : 2025-11-19, 4d
    Video pipeline & retrieval: 2025-11-19, 3d

    section Week 4 Highlights
    E2E testing & demo prep   : 2025-11-26, 6d
```

## Notes

- Dependencies reflect handoffs (e.g., API draft informs backend and mobile integration)
- Weeks 2–4 are summarized at milestone level; see each team's tracker for details
