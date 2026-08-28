# CI Pipeline Summary Report

**Verification date:** 2026-08-28  
**Pipeline:** `.github/workflows/ci.yml`  
**Overall local result:** PASS

## Pipeline triggers and controls

- Runs for pushes to `main`, pull requests, and manual dispatches.
- Uses read-only repository contents permission.
- Cancels an older run when a newer run starts for the same Git ref.
- Runs backend and frontend jobs independently, then runs Docker integration only
  after both application jobs pass.

## Quality gates

| Job | Gate | Result verified locally |
|---|---|---|
| Backend | Python 3.12 dependency installation | Configured |
| Backend | Pytest suite and JUnit report | PASS: 58 passed, 1 skipped |
| Frontend | Node.js 22 dependency installation | Configured |
| Frontend | ESLint | PASS |
| Frontend | TypeScript check | PASS |
| Frontend | Vitest suite and JUnit report | PASS: 24 passed |
| Frontend | Next.js production build | PASS |
| Docker | `docker compose config --quiet` | PASS |
| Docker | Backend, worker, and frontend image build | PASS |
| Compose | Full-stack startup with health wait | PASS |
| Compose | Backend `/health/ready` response | PASS: HTTP 200 |
| Compose | Celery worker inspection through Redis | PASS: pong, 1 node online |
| Compose | Frontend `/` response | PASS: HTTP 200 |

## Docker verification

The following application images were built successfully:

| Image | Local size |
|---|---:|
| `ai-web-hosting-advisor-backend:latest` | 235 MB |
| `ai-web-hosting-advisor-worker:latest` | 235 MB |
| `ai-web-hosting-advisor-frontend:latest` | 83.3 MB |

The integration stack contains MySQL 8.4, Redis 7 Alpine, FastAPI, a Celery
worker, and the Next.js frontend. MySQL, Redis, backend, and frontend passed
their configured health checks. The Celery worker also returned `pong` through
Redis with one node online.

## CI artifacts

Each run retains diagnostic output for 14 days:

- `backend-test-results`: backend JUnit XML.
- `frontend-test-results`: frontend JUnit XML.
- `docker-compose-verification`: container state, image inventory, and complete
  Compose logs, including logs collected when an integration step fails.

## Cleanup behavior

The Docker job always executes `docker compose down --volumes --remove-orphans`
after artifact collection. This keeps the hosted CI runner clean even when a
build, startup, health check, or endpoint check fails.

## Continuous delivery release

After a successful CI run caused by a push to `main`, `cd-release.yml` creates
an automatic pre-release tag using `v<frontend-version>-build.<CI-run-number>`.
It publishes a generated-notes GitHub release with a source archive and SHA-256
checksum. Pull-request CI runs never create releases.

The workflow can also be dispatched manually to create a stable semantic tag,
defaulting to the version in `frontend/package.json`. Existing or malformed
tags are rejected to prevent accidental release replacement.
