# Financial Plan

Mobile-first personal finance planning application. The backend currently
provides the FastAPI and PostgreSQL foundation, user registration, JWT access
tokens, rotating refresh-token sessions, and logout. The minimal mobile client
required to complete milestone M1 has not yet been implemented.

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

## Register a user

The current M1 backend slice supports user registration. Passwords must contain
between 15 and 128 characters; Unicode, whitespace, and passphrases are
accepted, and no composition rules are imposed. Only ARS and USD are supported
as reference currencies, with ARS as the default.

```powershell
$body = @{
    email = "learner@example.com"
    password = "synthetic passphrase 2026"
    reference_currency = "ARS"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/api/v1/auth/register `
    -ContentType "application/json" `
    -Body $body
```

The response contains public user data only. It never contains the password or
password hash.

Log in to receive a bearer token:

```powershell
$loginBody = @{
    email = "learner@example.com"
    password = "synthetic passphrase 2026"
} | ConvertTo-Json

$login = Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/api/v1/auth/login `
    -ContentType "application/json" `
    -Body $loginBody

$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me -Headers $headers
Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/api/v1/auth/logout `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{ refresh_token = $login.refresh_token } | ConvertTo-Json)
```

The access JWT expires after 15 minutes. The independent refresh token rotates
on use; PostgreSQL stores only its SHA-256 hash. Logout revokes that refresh
session, while the already-issued access JWT remains usable until it expires.

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
$env:DATABASE_URL = "postgresql+psycopg://financial_plan:replace_with_a_local_password@127.0.0.1:5432/financial_plan"
$env:APP_ENVIRONMENT = "development"
$env:JWT_SECRET_KEY = "replace_with_at_least_32_random_characters"
```

Run the API during development:

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run every backend verification command:

```powershell
uv run alembic upgrade head
uv run pytest --cov=app --cov-report=term-missing
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run alembic current --check-heads
uv run alembic check
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
| `JWT_SECRET_KEY` | Signs access JWTs; required and at least 32 characters. |
| `JWT_ALGORITHM` | Access-token signature algorithm; fixed to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access JWT lifetime; defaults to 15 minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Sliding refresh lifetime; defaults to 20 days. |
| `SESSION_ABSOLUTE_EXPIRE_DAYS` | Maximum family lifetime; defaults to 90 days. |
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
