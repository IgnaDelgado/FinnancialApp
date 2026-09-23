# Financial Plan

Mobile-first personal finance planning application. Milestone M0-A provides the
FastAPI and PostgreSQL development foundation only; it does not yet include
authentication, financial models, or a mobile client.

## Prerequisites

- Docker with Docker Compose
- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Run with Docker Compose

From the repository root, create the ignored local environment file and start
the services:

```powershell
Copy-Item .env.example .env
docker compose up --build -d --wait
docker compose ps
```

The example password is for local development only. Replace it in `.env` before
using a shared environment.

Verify both endpoints:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

Inspect logs or stop the stack:

```powershell
docker compose logs backend db
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete the
local PostgreSQL volume.

## Run backend checks on the host

From `backend/`, install the locked development environment and configure the
database URL for the Compose PostgreSQL port:

```powershell
uv sync --locked --all-groups
$env:DATABASE_URL = "postgresql+psycopg://financial_plan:replace_with_a_local_password@localhost:5432/financial_plan"
$env:APP_ENVIRONMENT = "development"
```

Run the API during development:

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run every backend verification command:

```powershell
uv run pytest --cov=app --cov-report=term-missing
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run alembic current
```

Create a migration after adding SQLAlchemy models in a later milestone:

```powershell
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `APP_ENVIRONMENT` | Selects `development`, `test`, or `production`. |
| `POSTGRES_DB` | Creates the local Compose database. |
| `POSTGRES_USER` | Creates the local Compose database user. |
| `POSTGRES_PASSWORD` | Sets the local Compose database password. |
| `DATABASE_URL` | SQLAlchemy Psycopg URL injected by Compose or set for host commands. |

Never commit `.env`; only `.env.example` belongs in version control.

`POSTGRES_PASSWORD` initializes a new PostgreSQL volume; changing the variable
does not update the password stored in an existing volume. Preserve volumes
that contain data and change the database role password explicitly. During
initial setup only, an empty local volume can be recreated with
`docker compose down -v`; this command permanently deletes that volume's data.
