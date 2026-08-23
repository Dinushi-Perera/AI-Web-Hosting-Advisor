# AI Web Hosting Advisor — Complete Connected Project

This package combines the supplied **Next.js frontend**, **FastAPI backend**, and **MySQL 8 database bundle** into one project without changing application features or business functions. Only integration/configuration files were added or corrected so the three supplied components use the same API and database.

## Project structure

- `frontend/` — supplied Next.js UI
- `backend/` — supplied FastAPI API + Celery worker
- `database/` — supplied complete MySQL 8 schema, views, seed data, reset/validation files
- `docker-compose.yml` — runs the entire stack together
- `.env.example` — local integrated configuration
- `start.sh` / `start.bat` — convenience launchers

## Connections used

Frontend API base:

`http://localhost:8000/api/v1`

Backend database:

`mysql+pymysql://hosting_app:hosting_app_password@mysql:3306/ai_web_hosting_advisor`

MySQL database name:

`ai_web_hosting_advisor`

Redis/Celery:

`redis://redis:6379`

The integrated frontend configuration uses `NEXT_PUBLIC_DEMO_MODE=false` and `NEXT_PUBLIC_AUTH_REQUIRED=true`, so the existing frontend API calls use the FastAPI backend instead of the frontend demo bypass.

## Run everything with Docker

### Windows

Double-click/run:

`start.bat`

Or from PowerShell/CMD:

```bash
copy .env.example .env
docker compose up --build
```

### Linux/macOS

```bash
cp .env.example .env
./start.sh
```

Then open:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

Development admin created by the supplied backend seed script:

- Email: `admin@hostingadvisor.local`
- Password: value of `SEED_ADMIN_PASSWORD` in `.env` (development example is `Admin123!ChangeMe`)

Change all development passwords/secrets before shared or production deployment.

## Database initialization

On the first MySQL container startup, Docker automatically executes:

`database/ai_web_hosting_advisor.sql`

That supplied SQL creates the full `ai_web_hosting_advisor` schema, advanced relational tables, views, constraints, and safe non-secret seed data. The backend then records its Alembic initial revision and runs the supplied Python seed script for the development admin and compatible demo pricing.

To fully reinitialize the database, remove the Docker MySQL volume and start again:

```bash
docker compose down -v
docker compose up --build
```

**Warning:** `down -v` deletes local database/Redis/container storage data.

## Integration notes

- The supplied backend and database enforce **USD-only monetary storage/requests**.
- The supplied frontend files were otherwise preserved, including all existing pages, components, animations, forms, and UI behavior.
- No deployment action is performed by recommendations; the existing system remains a decision-support application.
- PageSpeed remains optional and needs `PAGESPEED_API_KEY` for live PageSpeed evidence.
- Optional LLM functionality remains disabled unless `LLM_ENABLED=true` and `OPENAI_API_KEY` are configured.
