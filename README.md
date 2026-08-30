<div align="center">

# AI-Driven Web Hosting Advisor

### Performance Auditing · Workload Estimation · AI/ML Infrastructure Recommendation · Cost Optimization

A full-stack decision-support platform that analyses existing websites, planned applications, and new development ideas, then recommends a suitable **VPS**, **Cloud VM**, or **Kubernetes-based architecture** with explainable AI/ML scoring, resource sizing, performance evidence, USD cost ranges, optimization actions, safe load-test plans, and downloadable reports.

![Next.js](https://img.shields.io/badge/Next.js-Frontend-black?logo=nextdotjs)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.x-4479A1?logo=mysql&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Currency](https://img.shields.io/badge/Currency-USD%20Only-2ea44f)
![License](https://img.shields.io/badge/License-MIT-yellow)

</div>

---

## Table of Contents

- [Project Overview](#project-overview)
- [Core Objectives](#core-objectives)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Application Modes](#application-modes)
- [AI/ML System](#aiml-system)
- [Dataset and Data Provenance](#dataset-and-data-provenance)
- [Model Evaluation](#model-evaluation)
- [Recommendation Logic](#recommendation-logic)
- [Frontend](#frontend)
- [Backend](#backend)
- [Database](#database)
- [API Integration](#api-integration)
- [Quick Start with Docker](#quick-start-with-docker)
- [Manual Development Setup](#manual-development-setup)
- [Environment Variables](#environment-variables)
- [PageSpeed Integration](#pagespeed-integration)
- [Load-Test Planner](#load-test-planner)
- [Reports](#reports)
- [Security](#security)
- [Testing](#testing)
- [Reproducing the ML Work](#reproducing-the-ml-work)
- [Common Troubleshooting](#common-troubleshooting)
- [Production Deployment Notes](#production-deployment-notes)
- [Project Scope and Limitations](#project-scope-and-limitations)
- [License](#license)

---

# Project Overview

**AI-Driven Web Hosting Advisor** is a full-stack web application designed to reduce guesswork when selecting web-hosting infrastructure.

A user can provide:

1. an existing live website,
2. details of a planned website, or
3. a new application idea.

The system combines website evidence, performance metrics, workload calculations, operational requirements, budget information, stored provider pricing, deterministic rules, and trained machine-learning models to produce an explainable infrastructure recommendation.

The application is a **decision-support system**. It does **not** automatically deploy infrastructure, resize production servers, change DNS, create Kubernetes clusters, or perform unrestricted load attacks.

### Main recommendation outputs

- Recommended hosting architecture:
  - `VPS`
  - `CLOUD_VM`
  - `KUBERNETES`
- Recommended starting vCPU
- Recommended starting RAM
- Estimated monthly USD cost range
- Confidence level
- Recommendation reasons
- Assumptions
- Alternative architecture comparison
- Technology findings
- Performance findings
- Workload estimate
- Optimization actions
- Database-backed dynamic clarification answers for missing workload inputs
- Safe k6 test plan
- Downloadable report

---

# Core Objectives

The project brings several software-engineering disciplines together in one practical application:

- AI/ML-based infrastructure decision support
- Cloud and VPS architecture planning
- Web performance auditing
- Website technology detection
- Workload and traffic estimation
- Cost-aware recommendation
- Explainable scoring
- Safe load-test planning
- MySQL-based analysis history
- Full-stack application development
- Security-aware URL processing
- Software testing and evaluation

---

# Key Features

## User Experience

- User registration and login
- No application administrator account is required
- User-owned projects and analysis history
- Responsive desktop, tablet, and mobile UI
- Light / Dark / System themes
- Beginner-friendly and advanced information views
- Animated loading/progress states
- Dashboard analytics
- Project history
- Notifications
- Profile and security settings
- Demo showcase
- Accessible forms and keyboard-friendly navigation

## Analysis

- Three analysis modes
- Public URL validation
- Technology detection with evidence and confidence
- PageSpeed/Lighthouse-style performance evidence
- Core Web Vitals representation
- Workload estimation
- Traffic classification
- Resource requirement estimation
- AI/ML hosting prediction
- Rule-based safety and architecture constraints
- Explicit VPS, Cloud VM, and Kubernetes ranking with weighted score contributions and rule adjustments
- Monthly and annual stored-provider cost ranges with full-range budget-fit analysis
- Separate PageSpeed acquisition, Lighthouse lab diagnostics, and CrUX/Core Web Vitals field evidence
- Recommendation confidence
- Optimization suggestions
- Infrastructure architecture visualization
- Input-aware analysis coverage and decision-factor charts
- Nine plain-language validations for each completed project
- Connected report, optimization, feedback, load-test, notification, and audit-history records
- Historical comparison

## AI/ML

- 5,000-row master dataset
- Hosting Recommendation Classification model
- Resource Sizing Regression model
- Multiple candidate model comparison
- Separate validation and untouched test evaluation
- Independent 300-case scenario evaluation
- Full-data production model refit
- Saved `.joblib` artifacts
- Reproducible training scripts
- Executed Jupyter notebook evidence package
- Classification and regression metrics
- Confusion matrices
- ROC/AUC analysis
- Feature importance / coefficient analysis
- Actual-vs-predicted charts
- Residual analysis

## Cost

- **USD only**
- No foreign-exchange workflow
- Stored provider pricing snapshots
- Estimated cost ranges instead of misleading exact bills
- Pricing freshness information
- Budget compatibility
- Compute/database/storage/bandwidth-related cost components where available

## Load Testing

- Safe k6 script generation
- User authorization acknowledgement required
- Risk acknowledgement required
- Server-side URL safety validation
- Configurable test stages
- Conservative VU and duration limits
- Genuine k6 summary output and threshold evidence
- One-click bounded execution without scripts, terminals, downloads, or imports
- PageSpeed/Lighthouse context kept separate from k6 server-load evidence

## Reporting

- Explainable recommendation summary
- Technology findings
- Performance results
- Workload estimate
- Hosting recommendation
- Resource sizing
- Cost estimate
- Alternatives
- Optimization actions
- Assumptions
- Confidence
- Versioned report history
- PDF generation

---

# System Architecture

```mermaid
flowchart TD
    U[User] --> FE[Next.js Frontend]

    FE --> API[FastAPI REST API]
    API --> AUTH[Authentication & Validation]
    API --> JOB[Analysis Job Service]

    JOB --> TECH[Technology Detection]
    JOB --> PERF[PageSpeed / Performance]
    JOB --> WORK[Workload Estimator]
    JOB --> RULES[Rule Engine]
    JOB --> ML1[Hosting Classifier]
    JOB --> ML2[Resource Sizer]
    JOB --> PRICE[USD Pricing Engine]

    RULES --> SCORE[Final Scoring]
    ML1 --> SCORE
    ML2 --> SCORE
    WORK --> SCORE
    PERF --> SCORE
    PRICE --> SCORE

    SCORE --> CONF[Confidence Engine]
    CONF --> OPT[Optimization Engine]
    OPT --> REP[Report Generator]

    API --> DB[(MySQL 8)]
    API --> REDIS[(Redis)]
    REDIS --> CELERY[Celery Worker]

    TECH --> DB
    PERF --> DB
    WORK --> DB
    SCORE --> DB
    REP --> DB
```

## High-level request flow

```text
User
  ↓
Next.js
  ↓
FastAPI
  ↓
Input + security validation
  ↓
Analysis run / background job
  ↓
Technology / Performance / Workload
  ↓
Rules + ML + Cost Fit
  ↓
Resource Sizing
  ↓
Confidence + Explanations
  ↓
Optimization Actions
  ↓
MySQL History
  ↓
Dashboard / Report
```

---

# Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- App Router
- Tailwind CSS
- React Hook Form
- Zod
- TanStack Query
- TanStack Table
- Axios
- Recharts
- Framer Motion
- GSAP
- next-themes
- Lucide React
- React Flow / `@xyflow/react`
- Lottie React
- Sonner
- Zustand
- jsPDF
- React Syntax Highlighter

## Backend

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic v2
- Pydantic Settings
- SQLAlchemy 2.x
- Alembic
- PyMySQL
- httpx
- BeautifulSoup4
- lxml
- tldextract
- dnspython
- python-jose
- passlib / bcrypt
- slowapi
- Redis
- Celery
- scikit-learn
- pandas
- NumPy
- joblib
- Jinja2
- ReportLab
- tenacity
- structlog
- pytest

## Database & Infrastructure

- MySQL 8.x
- Redis 7
- Docker
- Docker Compose
- Celery background worker

## Performance & Testing

- Google PageSpeed Insights API
- Lighthouse-style metrics
- Core Web Vitals
- k6 plan generation
- pytest
- Frontend lint/type checking

---

# Repository Structure

```text
AI-Web-Hosting-Advisor/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── store/
│   │   ├── lib/
│   │   └── constants/
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── workers/
│   │   ├── ml/
│   │   │   └── models/
│   │   │       ├── hosting_classifier_v1_0_0.joblib
│   │   │       ├── resource_sizer_v1_0_0.joblib
│   │   │       └── model_metadata.json
│   │   └── main.py
│   ├── alembic/
│   ├── scripts/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── database/
│   ├── ai_web_hosting_advisor_full.sql
│   ├── seed_database.sql
│   ├── reset_database.sql
│   ├── BACKEND_DATABASE_CONFIG.txt
│   └── mysql_schema_validation.json
│
├── ml/
│   ├── datasets/
│   │   ├── external/
│   │   ├── generated/
│   │   │   ├── hosting_advisor_master_5000.csv
│   │   │   ├── hosting_classifier_5000.csv
│   │   │   └── resource_sizing_5000.csv
│   │   └── validation/
│   │       └── independent_validation_cases_300.csv
│   ├── scripts/
│   │   ├── download_public_sources.py
│   │   ├── generate_dataset.py
│   │   ├── train_models.py
│   │   └── validate_release.py
│   ├── models/
│   ├── results/
│   ├── DATA_PROVENANCE.md
│   └── ML_MODEL_REPORT.md
│
├── docker-compose.yml
├── .env.example
├── start.sh
├── start.bat
└── README.md
```

### Research notebook deliverables

The executed ML research package additionally contains:

```text
notebooks/
├── 01_Hosting_Recommendation_Model_Training_Analysis.ipynb
└── 02_Resource_Sizing_Model_Training_Analysis.ipynb

html/
├── 01_Hosting_Recommendation_Model_Training_Analysis.html
└── 02_Resource_Sizing_Model_Training_Analysis.html

charts/
results/
models/
backend_ready/
MODEL_ARTIFACT_MANIFEST.csv
MODEL_SELECTION_NOTE.md
```

---

# Application Modes

## 1. Live Website

The user enters a public website URL and traffic/budget information.

The system can:

1. validate the URL,
2. perform SSRF checks,
3. connect safely,
4. collect public technology evidence,
5. request PageSpeed performance evidence when configured,
6. estimate workload,
7. run recommendation logic,
8. calculate resource requirements,
9. compare infrastructure options,
10. generate optimization actions and a report.

## 2. Planned Website

For a website that is not deployed yet, the user provides information such as:

- application type
- frontend
- backend
- database
- traffic expectations
- concurrent users
- API intensity
- database intensity
- storage
- growth expectation
- availability
- operational skill
- monthly USD budget

Unavailable live metrics are not fabricated.

## 3. New Development Idea

The user describes a new application idea and its expected features.

The system derives/collects structured requirements and converts them into the same recommendation feature space used by the other two modes.

Before submission, the frontend requests clarification questions from the backend. Answers such as expected concurrency, storage, and database intensity are stored in `project_clarifications`, promoted into the canonical project input, and used by workload estimation, resource sizing, cost comparison, and recommendation confidence.

---

# AI/ML System

The project contains **two required trained machine-learning modules**.

## Model 1 — Hosting Recommendation Classifier

### Purpose

Predict the most suitable infrastructure category:

```text
VPS
CLOUD_VM
KUBERNETES
```

### Main inputs

Examples include:

- project mode
- application type
- monthly users
- expected concurrent users
- requests per user/minute
- estimated RPS
- peak RPS
- USD budget
- storage requirement
- performance score / availability flag
- CDN presence
- database intensity
- API intensity
- real-time requirements
- background jobs
- media intensity
- growth rate
- operational skill
- availability level
- multi-region requirement
- autoscaling requirement
- managed database preference

### Research models compared

The executed notebook compares:

- Logistic Regression
- Decision Tree Classifier
- Random Forest Classifier
- XGBoost Classifier

### Selected production classifier

**Logistic Regression** is selected under the predefined validation Macro-F1 selection rule.

This selection is intentionally transparent: XGBoost is slightly stronger on some untouched-test and cross-validation measurements, while Logistic Regression remains extremely competitive and provides simpler, highly explainable decision boundaries for a decision-support application.

---

## Model 2 — Resource Sizing Regressor

### Purpose

Predict recommended starting resource tiers:

**vCPU**

```text
1, 2, 4, 8, 16, 32
```

**RAM (GB)**

```text
1, 2, 4, 8, 16, 32, 64
```

### Research models compared

- Random Forest Regressor
- XGBoost Regressor

### Selected production resource model

**Random Forest Regressor** is selected using the predefined normalized validation error score.

---

# Dataset and Data Provenance

The main dataset contains exactly:

```text
5,000 rows
```

It is a **hybrid, expert-rule-assisted semi-synthetic dataset** designed for this project's decision problem.

It is not falsely represented as 5,000 manually labelled real-world websites downloaded from the internet.

## Class balance

| Hosting Class | Rows | Share |
|---|---:|---:|
| Cloud VM | 2,000 | 40% |
| VPS | 1,750 | 35% |
| Kubernetes | 1,250 | 25% |
| **Total** | **5,000** | **100%** |

## Data methodology

The dataset combines:

- project-defined application scenarios,
- realistic workload ranges,
- explicit architecture rules,
- controlled boundary variation,
- workload/resource evidence from public data,
- operational-skill and availability requirements,
- budget and cost-aware decision factors.

Public calibration/evidence included in the ML package contains examples based on:

- UCI Computer Hardware data
- Google Cluster Data task-usage/task-event samples
- Alibaba Cluster Trace schema/workload guidance

See:

```text
ml/DATA_PROVENANCE.md
```

for the detailed provenance and methodology.

## Main dataset files

```text
ml/datasets/generated/hosting_advisor_master_5000.csv
ml/datasets/generated/hosting_classifier_5000.csv
ml/datasets/generated/resource_sizing_5000.csv
ml/datasets/validation/independent_validation_cases_300.csv
```

---

# Model Evaluation

## Data usage protocol

All 5,000 rows are accounted for during model development:

```text
3,500 rows → Training
750 rows   → Validation
750 rows   → Untouched Test
-------------------------------
5,000 rows → Total
```

The test set is **not** used to select the candidate model.

After evaluation is complete, each production candidate is refit on **all 5,000 rows**, allowing both:

- academically valid evaluation, and
- full-data production artifacts.

## Hosting classifier — validation comparison

| Model | Validation Accuracy | Validation Macro F1 |
|---|---:|---:|
| **Logistic Regression** | **0.9547** | **0.9567** |
| XGBoost | 0.9467 | 0.9490 |
| Random Forest | 0.9320 | 0.9339 |
| Decision Tree | 0.9173 | 0.9232 |

**Selection rule:** highest validation Macro F1.

**Selected:** Logistic Regression.

## Hosting classifier — untouched test

| Model | Test Accuracy | Test Macro F1 |
|---|---:|---:|
| XGBoost | 0.9507 | 0.9546 |
| **Logistic Regression** | **0.9440** | **0.9479** |
| Random Forest | 0.9320 | 0.9370 |
| Decision Tree | 0.9253 | 0.9316 |

The project keeps Logistic Regression because model selection was fixed before inspecting the untouched test result. The README intentionally reports XGBoost's slightly stronger test result instead of hiding it.

## 5-fold classifier cross-validation

| Model | CV Accuracy Mean | CV Macro F1 Mean |
|---|---:|---:|
| XGBoost | 0.9542 | 0.9571 |
| Logistic Regression | 0.9536 | 0.9560 |
| Random Forest | 0.9336 | 0.9364 |
| Decision Tree | 0.9212 | 0.9260 |

## Independent classifier scenario evidence

| Model | Accuracy | Macro F1 |
|---|---:|---:|
| XGBoost | 0.9933 | 0.9939 |
| Logistic Regression | 0.9733 | 0.9756 |
| Random Forest | 0.9733 | 0.9739 |
| Decision Tree | 0.9633 | 0.9659 |

The independent 300-case file is an additional controlled scenario set, not a claim of a public ground-truth hosting dataset.

---

## Resource model — validation comparison

| Model | vCPU MAE | vCPU R² | RAM MAE | RAM R² | Joint Exact Tier |
|---|---:|---:|---:|---:|---:|
| **Random Forest Regressor** | **0.542** | **0.9931** | **0.901 GB** | **0.9923** | 77.47% |
| XGBoost Regressor | 0.589 | 0.9907 | 1.021 GB | 0.9905 | 78.00% |

Selection uses a normalized error score:

```text
selection_score =
0.5 × (
    vCPU_MAE / 31
    +
    RAM_MAE / 63
)
```

Lower is better.

Therefore, **Random Forest Regressor** is selected.

## Resource model — untouched test

Random Forest Regressor approximately achieves:

```text
vCPU R²          ≈ 0.9827
RAM R²           ≈ 0.9825
vCPU exact tier  ≈ 76.8%
RAM exact tier   ≈ 92.5%
Within one tier  = 100%
```

The application should interpret resource sizing as an explainable starting recommendation, not a guaranteed production capacity value.

---

# Recommendation Logic

The final hosting recommendation is **not** produced by one ML prediction alone.

```text
Structured Input
      ↓
Workload Estimation
      ↓
Hard / Safety Rules
      ↓
ML Hosting Prediction
      ↓
Resource Sizing Model
      ↓
Traffic Fit
      ↓
Budget Fit
      ↓
Scalability Fit
      ↓
Reliability Fit
      ↓
Operational Fit
      ↓
USD Cost Analysis
      ↓
Confidence Calculation
      ↓
Final Explainable Recommendation
```

## Example rule behavior

- Small low-traffic static workloads should not be pushed toward Kubernetes without a clear need.
- Low operational skill reduces Kubernetes suitability.
- High traffic, multi-service architecture, high availability, and advanced operational capability can increase Kubernetes suitability.
- Poor frontend performance with low server workload can trigger an **optimize first** recommendation rather than suggesting a larger server.
- Missing PageSpeed or technology evidence reduces confidence rather than inventing data.

---

# Frontend

The frontend is a production-oriented Next.js application.

## Main routes

```text
/
├── /login
├── /register
├── /forgot-password
├── /reset-password
├── /onboarding
├── /dashboard
├── /projects
├── /projects/new
├── /projects/{id}
├── /projects/{id}/processing
├── /projects/{id}/technology
├── /projects/{id}/performance
├── /projects/{id}/workload
├── /projects/{id}/recommendation
├── /projects/{id}/cost
├── /projects/{id}/load-test
├── /projects/{id}/optimization
├── /projects/{id}/report
├── /projects/{id}/history
├── /analyze/live
├── /analyze/planned
├── /analyze/new-idea
├── /cost
├── /reports
├── /testing
├── /testing/model-evaluation
├── /settings/profile
├── /settings/security
└── /demo-showcase
```

## Frontend behavior

- API requests are centralized under `src/services/`
- Real backend mode:
  ```env
  NEXT_PUBLIC_DEMO_MODE=false
  ```
- Auth route protection:
  ```env
  NEXT_PUBLIC_AUTH_REQUIRED=true
  ```
- Backend URL:
  ```env
  NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
  ```

## Frontend local run

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Windows CMD:

```bat
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Frontend quality commands

```bash
npm run lint
npm run typecheck
npm run build
```

---

# Backend

The backend provides:

- authentication
- project CRUD
- analysis jobs
- URL security checks
- technology detection
- performance integration
- workload estimation
- ML inference
- rule scoring
- resource sizing
- cost estimation
- recommendation explanations
- optimizations
- k6 plans
- reports
- notifications
- project history
- testing evidence

## API base

```text
http://localhost:8000/api/v1
```

## Development URLs

| Service | URL |
|---|---|
| API | `http://localhost:8000` |
| Swagger/OpenAPI | `http://localhost:8000/docs` |
| Health | `http://localhost:8000/health` |
| Readiness | `http://localhost:8000/health/ready` |

## Local backend setup

```bash
cd backend

python -m venv venv
```

Windows:

```bat
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
alembic upgrade head
```

Seed safe application/provider data:

```bash
python scripts/seed.py
```

Start API:

```bash
uvicorn app.main:app --reload
```

Run Celery separately:

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```

For intentionally synchronous local development only:

```env
CELERY_TASK_ALWAYS_EAGER=true
```

Do not use eager mode as a production replacement for background workers.

---

# Database

Database:

```text
ai_web_hosting_advisor
```

Technology:

```text
MySQL 8.x
InnoDB
USD-only monetary data
```

## Database bundle

```text
database/
├── ai_web_hosting_advisor_full.sql
├── seed_database.sql
├── reset_database.sql
├── BACKEND_DATABASE_CONFIG.txt
└── mysql_schema_validation.json
```

The schema supports:

- users
- user preferences and sessions
- projects
- project inputs/features
- analysis runs/jobs/stages
- technology detections/evidence
- performance audits/metrics
- workload estimates/assumptions
- load-test plans/stages
- providers/plans/pricing snapshots
- model metadata and predictions
- rule results
- recommendations/scores/reasons
- resource sizing
- architecture data
- optimization suggestions
- reports and versions
- notifications
- feedback
- testing evidence
- project activity
- audit/history data

## Manual database installation

```bash
mysql -u root -p < database/ai_web_hosting_advisor_full.sql
```

Backend connection example:

```env
DATABASE_URL=mysql+pymysql://hosting_app:YOUR_PASSWORD@localhost:3306/ai_web_hosting_advisor
```

Inside Docker Compose, the hostname is:

```text
mysql
```

Example:

```env
DATABASE_URL=mysql+pymysql://hosting_app:hosting_app_password@mysql:3306/ai_web_hosting_advisor
```

## Reset database — development only

```bash
mysql -u root -p < database/reset_database.sql
```

Or when using Docker:

```bash
docker compose down -v
docker compose up --build
```

> **Warning:** `docker compose down -v` deletes local MySQL, Redis, and container volume data.

---

# API Integration

For a direct local backend process, the frontend can use:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Docker Compose uses `http://localhost:8001/api/v1` by default so it can coexist with a local development server. Override `BACKEND_HOST_PORT` and `DOCKER_PUBLIC_API_BASE_URL` together when needed.

## Important API routes

### Authentication

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

### Website check

```http
POST /api/v1/analysis/check-url
POST /api/v1/analysis/check-website
```

### Analysis creation

```http
POST /api/v1/analysis/live
POST /api/v1/analysis/planned
POST /api/v1/analysis/idea
POST /api/v1/projects/{id}/analysis
```

### Analysis job progress

```http
GET  /api/v1/analysis/jobs/{job_id}
GET  /api/v1/analysis/jobs/{job_id}/events
POST /api/v1/analysis/jobs/{job_id}/cancel
```

### Projects

```http
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{id}
PATCH  /api/v1/projects/{id}
DELETE /api/v1/projects/{id}
```

### Results

The backend exposes routes for:

```text
technology
performance
performance history/comparison
workload
recommendation
recommendation comparison
recommendation explanation
cost
optimizations
load-test plans
reports
history
notifications
user settings
testing/model evaluation
```

Use Swagger for the exact active route schema:

```text
http://localhost:8000/docs
```

---

# Quick Start with Docker

This is the recommended way to run the complete connected application.

## Requirements

Install:

- Docker Desktop / Docker Engine
- Docker Compose plugin
- Git

No local MySQL/Redis installation is required when using Docker.

On the first start, MySQL creates the empty application database and the
backend creates the current ORM schema, records the Alembic head revision, and
inserts the development seed data. Existing Alembic-managed databases receive
normal upgrades. The reference SQL export under `database/` is not imported by
Compose; this avoids applying the current schema twice.

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AI-Web-Hosting-Advisor
```

## 2. Create the root environment file

Linux/macOS:

```bash
cp .env.example .env
```

Windows CMD:

```bat
copy .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

## 3. Change development secrets

At minimum, replace:

```env
JWT_SECRET=replace-with-a-long-random-secret
MYSQL_APP_PASSWORD=replace-this-password
MYSQL_ROOT_PASSWORD=replace-this-root-password
```

## 4. Start the full stack

```bash
docker compose up --build
```

Docker starts:

| Container | Port | Purpose |
|---|---:|---|
| Frontend | 3001 | Next.js UI |
| Backend | 8001 | FastAPI |
| MySQL | 3307 | Relational database / Workbench connection |
| Redis | 6379 | Queue/cache |
| Worker | internal | Celery analysis jobs |

The published ports can be changed with `FRONTEND_HOST_PORT`,
`BACKEND_HOST_PORT`, `MYSQL_HOST_PORT`, and `REDIS_HOST_PORT` in the root
`.env` file. If the backend port changes, update `DOCKER_PUBLIC_API_BASE_URL`
to match before rebuilding the frontend image.

## 5. Open the application

```text
Frontend:      http://localhost:3001
Backend:       http://localhost:8001
Swagger:       http://localhost:8001/docs
Health:        http://localhost:8001/health
Readiness:     http://localhost:8001/health/ready
```

## 6. Create a user

The current application does **not** require or seed an application administrator.

Open:

```text
http://localhost:3001/register
```

Register a normal user account and sign in.

## Stop

```bash
docker compose down
```

## Rebuild

```bash
docker compose up --build
```

## View logs

```bash
docker compose logs -f
```

Backend only:

```bash
docker compose logs -f backend
```

Worker only:

```bash
docker compose logs -f worker
```

---

# Manual Development Setup

Use this only if you prefer to run each service separately.

## Prerequisites

- Node.js LTS
- npm
- Python 3.12+
- MySQL 8.x
- Redis
- Git

Optional:

- Docker Desktop
- MySQL Workbench
- Postman
- Jupyter Notebook
- k6 CLI on the backend host (included in the backend container image)

## 1. Start MySQL

Create/import the database:

```bash
mysql -u root -p < database/ai_web_hosting_advisor_full.sql
```

## 2. Start Redis

Example:

```bash
redis-server
```

Or:

```bash
docker run --rm -p 6379:6379 redis:7-alpine
```

## 3. Backend

```bash
cd backend
python -m venv venv
```

Activate environment and install:

```bash
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

## 4. Celery

New terminal:

```bash
cd backend
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```

## 5. Frontend

New terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

---

# Environment Variables

## Root Docker `.env`

Example:

```env
MYSQL_DATABASE=ai_web_hosting_advisor
MYSQL_USER=hosting_app
MYSQL_PASSWORD=change_this
MYSQL_ROOT_PASSWORD=change_this_root_password

JWT_SECRET=replace_with_a_long_random_secret

PAGESPEED_API_KEY=

OPENROUTER_API_KEY=
LLM_ENABLED=false
OPENROUTER_MODEL=z-ai/glm-5.2:free

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_DEMO_MODE=false
NEXT_PUBLIC_AUTH_REQUIRED=true
```

## Important backend settings

Depending on deployment, the backend can also use:

```env
APP_ENV=development
APP_NAME=AI Web Hosting Advisor

API_V1_PREFIX=/api/v1

DATABASE_URL=mysql+pymysql://hosting_app:password@localhost:3306/ai_web_hosting_advisor

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000

ACCESS_TOKEN_MINUTES=15
REFRESH_TOKEN_DAYS=7
PASSWORD_RESET_MINUTES=30

COOKIE_SECURE=false
COOKIE_SAMESITE=lax

PAGESPEED_API_KEY=
PAGESPEED_CACHE_SECONDS=900

LLM_ENABLED=false
OPENROUTER_API_KEY=
OPENROUTER_MODEL=z-ai/glm-5.2:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

DEFAULT_CURRENCY=USD
PRICING_STALE_DAYS=30

REPORT_STORAGE_DIR=storage/reports
LOAD_TEST_STORAGE_DIR=storage/load_tests
```

### Password reset email — optional

Configure if email-based password reset is required:

```env
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
```

### Important

Never commit real values for:

```text
JWT_SECRET
MYSQL_PASSWORD
MYSQL_ROOT_PASSWORD
PAGESPEED_API_KEY
OPENROUTER_API_KEY
SMTP_PASSWORD
```

---

# PageSpeed Integration

For live website performance evidence, configure:

```env
PAGESPEED_API_KEY=your_real_google_pagespeed_key
```

If no key is configured or the external service is unavailable:

- the application does not invent performance metrics,
- performance evidence is marked unavailable,
- recommendation confidence can be reduced,
- the rest of the analysis can continue where possible.

---

# Load-Test Planner

The system creates a **safe k6 scenario template** from the user-confirmed workload, PageSpeed/Lighthouse evidence, Hosting Recommendation model, and Resource Sizing model. The managed workflow executes only this server-generated GET-only scenario under strict caps; it never executes arbitrary user scripts or unrestricted load.

Before a plan is generated, the backend requires:

- authorization acknowledgement,
- risk acknowledgement,
- safe URL validation,
- target-domain checks,
- configured maximum virtual users,
- configured maximum test duration.

Example generated stages may resemble:

```text
10 VUs → 30 seconds
50 VUs → 60 seconds
100 VUs → 60 seconds
0 VUs → 30 seconds
```

Only run generated scripts against infrastructure you own or have explicit authorization to test.

---

# Reports

Reports can include:

- Executive summary
- Project information
- Technology evidence
- Performance findings
- Core Web Vitals
- Workload estimate
- Hosting recommendation
- Architecture comparison
- Resource sizing
- USD cost range
- Optimization plan
- Load-test plan
- Assumptions
- Warnings
- Confidence

The backend stores an immutable analysis/report snapshot and can render a PDF.

Regeneration should create a new report version rather than silently changing old historical results.

---

# Security

Security controls are part of the backend, not only the UI.

## Authentication

- Password hashing
- JWT-based authentication
- Short-lived access session
- Refresh session support
- httpOnly authentication cookies
- Optional bearer-token support
- Password reset token expiration
- User resource ownership checks

## URL / SSRF protection

Live website analysis rejects or protects against:

- `localhost`
- loopback addresses
- private networks
- link-local networks
- reserved IP ranges
- metadata endpoints
- unsafe URL schemes
- credential-bearing URLs
- DNS rebinding
- redirects to private/internal addresses

## API protection

- Server-side validation
- Rate limiting
- CORS restriction
- Structured error handling
- No raw stack traces returned to users
- No secrets stored as technology evidence
- No production credentials in frontend code

## Load-test safety

- Authorization confirmation
- Risk acknowledgement
- URL checks
- Target host validation
- Conservative limits
- Plan/script generation only

---

# Testing

The project supports multiple levels of testing.

## Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Backend

```bash
cd backend
pytest
```

Test areas include:

- unit tests
- integration tests
- system tests
- URL validation
- cost/scoring logic
- project flow
- database integration
- security validation
- report generation
- all three input modes and every project-detail section
- 15 authenticated project API sections for each live, planned, and idea workflow
- nine input-specific checks covering inputs, technology, performance, workload, recommendation, cost, optimizations, reports, and load-test safety
- clarification persistence and its effect on sizing inputs
- cost, performance, security, and monitoring optimization categories

## Health checks

```text
GET /health
GET /health/ready
```

Readiness verifies important runtime dependencies such as database/Redis and model availability where configured.

## Academic evaluation categories

The project is designed to provide evidence for:

- Unit Testing (UT)
- Integration Testing (IT)
- System Testing (ST)
- User Acceptance Testing (UAT)
- Operational Readiness Testing (ORT)

---

# Reproducing the ML Work

## Integrated ML scripts

From the project root:

```bash
python ml/scripts/generate_dataset.py
python ml/scripts/train_models.py
python ml/scripts/validate_release.py
```

Install ML requirements if needed:

```bash
pip install -r ml/requirements-ml.txt
```

Generated outputs are stored under:

```text
ml/models/
ml/results/
ml/datasets/generated/
```

## Executed Jupyter notebooks

The separate complete research package contains two notebooks:

```text
01_Hosting_Recommendation_Model_Training_Analysis.ipynb
02_Resource_Sizing_Model_Training_Analysis.ipynb
```

Typical notebook environment:

```bash
pip install pandas numpy scikit-learn xgboost matplotlib jupyter joblib
jupyter notebook
```

Then open each notebook and select:

```text
Run All
```

The notebooks generate:

- comparison metrics
- confusion matrices
- class distribution charts
- ROC curves
- feature importance/coefficient charts
- test predictions
- actual-vs-predicted plots
- residual plots
- resource tier analysis
- saved candidate models
- selected production models

## Production artifacts

The backend automatically loads the selected artifacts supplied with this repository:

```text
models/classifier/production/LogisticRegression_full5000.joblib
models/resource/production/RandomForestRegressor_full5000.joblib
```

Docker mounts the repository `models/` directory read-only at `/app/models`. The analysis pipeline stores the classifier version, resource-model provenance, model probabilities, and the exact 26-feature snapshot in MySQL. Configure alternate approved artifacts with `CLASSIFIER_MODEL_PATH` and `RESOURCE_MODEL_PATH`.

---

# Common Troubleshooting

## Frontend cannot connect to backend

Confirm:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_DEMO_MODE=false
```

Check backend:

```text
http://localhost:8000/health
```

Check CORS:

```env
CORS_ORIGINS=http://localhost:3000
```

---

## MySQL connection error

Check:

```bash
docker compose ps
```

Then:

```bash
docker compose logs mysql
```

Inside Docker, use host:

```text
mysql
```

not:

```text
localhost
```

from the backend container.

---

## Redis/Celery analysis remains queued

Check:

```bash
docker compose logs -f worker
```

Confirm:

```env
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
```

---

## ML model unavailable

Check model files:

```text
backend/app/ml/models/hosting_classifier_v1_0_0.joblib
backend/app/ml/models/resource_sizer_v1_0_0.joblib
backend/app/ml/models/model_metadata.json
```

Then open:

```text
http://localhost:8000/health/ready
```

The application can fall back to deterministic logic if an artifact cannot be loaded, but that fallback should be clearly identified and should not be presented as an ML prediction.

---

## PageSpeed unavailable

Set:

```env
PAGESPEED_API_KEY=...
```

Then restart backend:

```bash
docker compose restart backend worker
```

---

## Database needs a complete clean reset

```bash
docker compose down -v
docker compose up --build
```

> This destroys local container database/Redis volume data.

---

## Port already in use

Default ports:

```text
3001 → frontend
8001 → backend
3307 → MySQL
6379 → Redis
```

Override `FRONTEND_HOST_PORT`, `BACKEND_HOST_PORT`, `MYSQL_HOST_PORT`, and `DOCKER_PUBLIC_API_BASE_URL` in `.env` when another application uses these ports.

---

# Production Deployment Notes

## GitHub Container Registry

The repository publishes the application images to GitHub Container Registry (GHCR):

```text
ghcr.io/dinushi-perera/ai-web-hosting-advisor-backend
ghcr.io/dinushi-perera/ai-web-hosting-advisor-frontend
```

The Celery worker uses the backend image. Pushes to `main` publish `latest`, `main`, and a commit-SHA tag. Version tags such as `v1.0.0-build.6` publish the version tag and a commit-SHA tag.

For public packages, pull and start the published images with:

```bash
docker compose pull backend worker frontend
docker compose up -d --no-build
```

For private packages, authenticate first with a GitHub personal access token that has `read:packages` permission:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
docker compose pull backend worker frontend
docker compose up -d --no-build
```

Choose a published version by setting `CONTAINER_TAG` in `.env`:

```env
CONTAINER_REGISTRY=ghcr.io
CONTAINER_NAMESPACE=dinushi-perera
CONTAINER_TAG=v1.0.0-build.6
```

The frontend API URL is embedded during the container build. Set the repository Actions variable `DOCKER_PUBLIC_API_BASE_URL` to the externally reachable backend API URL before publishing production images. If the variable is unset, the workflow uses `http://localhost:8001/api/v1`.

The **Publish GHCR Containers** workflow uses GitHub's built-in token with `packages: write`; no registry password or personal access token is required in repository secrets. Newly created package visibility and access can be managed under the repository or account package settings.

Before deploying beyond local/demo use:

1. Replace all example passwords and secrets.
2. Use a long random `JWT_SECRET`.
3. Set:
   ```env
   COOKIE_SECURE=true
   ```
4. Run behind HTTPS.
5. Restrict CORS to the production frontend domain.
6. Use protected/managed MySQL and Redis where possible.
7. Back up MySQL and verify restores.
8. Replace demo provider pricing with verified USD pricing snapshots.
9. Store real pricing source timestamps.
10. Configure a real PageSpeed API key if live performance evidence is required.
11. Keep optional LLM functionality disabled unless intentionally configured.
12. Use Nginx or a managed reverse proxy.
13. Run API and Celery workers separately.
14. Move generated report/script files to private object storage for multi-instance deployment.
15. Never expose `.env`.
16. Validate all model artifacts before claiming ML-backed inference.

---

# Project Scope and Limitations

The project intentionally focuses on **analysis and recommendation**, not automated infrastructure administration.

It does not:

- automatically deploy servers,
- resize live production instances,
- create Kubernetes clusters,
- automatically change DNS,
- modify a production database,
- guarantee exact future cloud bills,
- execute unrestricted load attacks,
- claim that technology detection is always certain,
- fabricate performance data when PageSpeed is unavailable.

Cloud pricing changes over time. Cost outputs should therefore be interpreted as **stored/estimated USD ranges** with pricing freshness and assumptions.

Resource recommendations are starting points for decision support and should be validated against actual authorized performance/load testing before production use.

---

# GitHub Recommendations

Recommended repository files:

```text
README.md
LICENSE
.gitignore
.env.example
```

Do not commit:

```text
.env
.env.local
venv/
node_modules/
__pycache__/
.pytest_cache/
database volume files
Redis volume files
real secrets
temporary report files
```

Large future ML artifacts can use Git LFS if necessary.

---

# License

This project's original source code is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for the complete terms.

Third-party datasets and external resources remain subject to their own original licenses/terms and should not be re-licensed as project-owned data.

See `ml/DATA_PROVENANCE.md` for dataset/source notes.

---

# Authorized k6 Validation Workflow

Each completed project has a **Load Test** section and the sidebar exposes the same dashboard under **AI Advisor → Load Testing**. The planner uses the stored workload estimate, PageSpeed/Lighthouse context, Hosting Recommendation model, and Resource Sizing model to produce a capped, explainable k6 scenario. Ownership/permission and availability-risk confirmations are mandatory.

1. Open a completed project and select **Load Test**.
2. Review expected concurrency, RPS, peak RPS, architecture, vCPU, and RAM.
3. Confirm authorization and risk, then select **Run test and create report**.
4. The backend validates the public target and approved hostname, creates a GET-only k6 template, pins the validated public host, and invokes the installed k6 binary without a shell.
5. k6 writes the genuine aggregated JSON summary. The backend validates it and stores p50/p90/p95/p99 latency, error rate, RPS, checks, peak VUs, thresholds, and expected-RPS traffic coverage.
6. The dashboard displays the report automatically and saves it in project history, audit history, notifications, testing evidence, comparisons, and final reports.

PageSpeed/Lighthouse and k6 answer different questions. PageSpeed, Lighthouse, and CrUX describe frontend quality and user experience. k6 measures application/server response under simulated traffic. Neither is presented as a substitute for the other.

A passing scenario does not permanently prove production capacity. Resource sizing is marked supported only when actual tested CPU/RAM evidence matches the predicted starting size and the planned workload was reached.

Safety policy is configured with `K6_MAX_VUS`, managed k6 concurrency/duration caps, execution timeout, p95/p99/check/error thresholds, enabled test types, and result-size limits. Only HTTP(S) public targets are accepted; live-project targets must match the analysed host. Private, local, metadata, credential-bearing, unsafe-port, redirect, destructive-path, and cross-host targets are blocked. The generated scenario uses confirmed safe GET paths and never stores credentials.

---

# Academic Context

This project was developed as an individual software-engineering / AI project centered on:

> **An AI-Driven Web Hosting Advisor for Performance Auditing, Load Testing, and Cost-Optimized Infrastructure Recommendations**

The system demonstrates the integration of:

- software engineering,
- artificial intelligence and machine learning,
- cloud architecture,
- relational database design,
- web performance,
- load-test planning,
- security,
- full-stack development,
- testing,
- evaluation,
- explainable decision support.

---

<div align="center">

## AI Web Hosting Advisor

**Analyse → Estimate → Compare → Recommend → Explain → Optimize**

Built with Next.js, FastAPI, MySQL, Redis/Celery, scikit-learn, XGBoost research benchmarking, PageSpeed evidence, k6 planning, and Docker.

</div>
