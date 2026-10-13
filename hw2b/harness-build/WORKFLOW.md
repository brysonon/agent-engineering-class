# Conference Compass Development Workflow

The frozen application requirements are in `../SPEC.md`. All implementation
work stays inside this `harness-build/` folder.

## 1. Plan

Load the Planner role:

```powershell
..\.venv\Scripts\myteam.exe get role planner
```

The planner writes `PLAN.md`. The plan must map every important requirement to
an implementation component and a verification step. No app code is written in
this phase.

## 2. Develop

Load the Developer role:

```powershell
..\.venv\Scripts\myteam.exe get role developer
```

The developer reads the frozen spec and `PLAN.md`, builds the app under `app/`,
and writes `IMPLEMENTATION.md` with actual command results and known limits.

## 3. Review

Load the Reviewer role:

```powershell
..\.venv\Scripts\myteam.exe get role reviewer
```

The reviewer independently checks the app and writes `REVIEW.md`. Findings must
include evidence and acceptance conditions.

## 4. Fix

The Developer role addresses confirmed findings, reruns the affected checks,
and updates `IMPLEMENTATION.md`.

## 5. Verify

The Reviewer role performs final verification. Completion requires passing
tests and build, a validated 37-talk corpus, grounded citations, exact source
excerpts, usable error states, and a written statement of any remaining limits.
