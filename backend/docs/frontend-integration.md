# Supplied Frontend → Backend Contract

Base URL: `http://localhost:8000/api/v1`

| Frontend behavior | Backend |
|---|---|
| Sign in | `POST /auth/login` |
| Register | `POST /auth/register` |
| Current user | `GET /auth/me` |
| Check website | `POST /analysis/check-website` or `/analysis/check-url` |
| Live wizard submit | `POST /analysis/live` |
| Planned wizard submit | `POST /analysis/planned` |
| New idea wizard submit | `POST /analysis/idea` |
| Processing status | `GET /analysis/jobs/{job_id}` |
| SSE progress | `GET /analysis/jobs/{job_id}/events` |
| Cancel analysis | `POST /analysis/jobs/{job_id}/cancel` |
| Projects | `GET /projects` |
| Project | `GET /projects/{id}` |
| Save draft/update | `PATCH /projects/{id}` |
| Start/re-run | `POST /projects/{id}/analysis` |
| Technology | `GET /projects/{id}/technology` |
| Correct detection | `POST /projects/{id}/technology/{detection_id}/feedback` |
| Performance | `GET /projects/{id}/performance` |
| History | `GET /projects/{id}/performance/history` |
| Compare runs | `GET /projects/{id}/performance/compare?from=...&to=...` |
| Workload | `GET /projects/{id}/workload` |
| Recommendation | `GET /projects/{id}/recommendation` |
| Explain | `GET /projects/{id}/recommendation/explanation` |
| Compare architectures | `GET /projects/{id}/recommendation/compare` |
| Missing inputs | `GET /projects/{id}/recommendation/missing-inputs` |
| Recalculate | `POST /projects/{id}/recommendation/recalculate` |
| Cost | `GET /projects/{id}/cost` |
| Pricing table | `GET /pricing` |
| Optimizations | `GET /projects/{id}/optimizations` |
| Mark optimization | `PATCH /optimizations/{id}/status` |
| Generate k6 plan | `POST /projects/{id}/load-test-plan` |
| Download k6 | `GET /load-test-plans/{id}/download` |
| Generate report | `POST /projects/{id}/reports` |
| Project reports | `GET /projects/{id}/reports` |
| Global reports | `GET /reports` |
| PDF | `GET /reports/{id}/pdf` |
| Project history | `GET /projects/{id}/history` |
| Notifications | `GET /notifications` |
| Profile | `GET/PATCH /users/me` |
| Preferences | `GET/PATCH /users/me/preferences` |
| Sessions | `GET/DELETE /users/me/sessions...` |
| Dashboard | `GET /dashboard` |
| Test evidence | `/testing/*` |

## USD-only note

The frontend and backend accept and display **USD only**.
