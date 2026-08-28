# Testing and CI

## Run the CI suite locally

Windows PowerShell:

```powershell
.\test-ci.ps1
```

Linux or macOS:

```sh
./test-ci.sh
```

The runner executes backend pytest tests, frontend ESLint, TypeScript checks,
Vitest tests, and a production Next.js build. JUnit reports are written to:

- `backend/test-results/junit.xml`
- `frontend/test-results/junit.xml`

## Backend tests

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest
```

`backend/tests/conftest.py` supplies an isolated in-memory SQLite database and
overrides the FastAPI database dependency. Integration tests therefore do not
read or modify the development MySQL database. The system test remains skipped
locally because it requires deployed MySQL, Redis, worker, k6, and optional
PageSpeed services.

## Frontend tests

```sh
cd frontend
npm test
npm run test:watch
npm run test:ci
```

Vitest uses jsdom and React Testing Library. Tests cover utilities, schemas,
API service contracts, and shared interactive components.

## GitHub Actions

`.github/workflows/ci.yml` runs separate backend and frontend jobs on pushes to
`main`, pull requests, and manual dispatches. Each job uploads its JUnit report
as a 14-day workflow artifact, even when tests fail.
