# Financial Plan

Mobile-first personal finance planning application. The current implementation
includes a FastAPI/PostgreSQL API and an Expo/React Native client for
authentication and manually recorded financial-account balances.

## Current status

M1 authentication V2 is complete for local development. The backend and mobile
client support registration, login, automatic session restoration, rotating
refresh tokens, current-device logout, global logout, ARS/USD reference-currency
selection, configurable browser CORS, and a responsive mobile-first interface.
Native refresh tokens use SecureStore. Development web previews keep the refresh
token in the tab's `sessionStorage` so F5 can restore the session; production web
does not persist it pending a secure-cookie design. If global logout cannot
reach the server, the local session remains available so the user can retry.

The first M2 slice is implemented: users can create supported manual accounts,
record signed ARS/USD balances (including overdrafts), update the full balance,
and see per-currency totals. Each balance change creates a historical snapshot.
The API enforces ownership, supports account archival, and paginates active
accounts and balance history. The account
management displays pages of 50. Totals include every active account, not just
the visible page, and are not net worth or safe-to-spend money. Goals
and Investments remain clearly marked as coming soon.

Mobile account balance history is now available when selecting an account,
with pages of 20 snapshots, signed currency amounts, Argentina timestamps,
and retry controls. Snapshots are complete balances, not transactions.
The selected account offers confirmed removal through archival: it disappears
from active accounts and totals while its records are retained.
M2 is not yet complete: account-metadata editing and a dedicated archived-account
management view remain. The first part of M3 adds creation and paginated
consultation of one-time and monthly planned income and commitments in Tu mes.
Users select a month and a first date for monthly repetitions. It displays
the selected financial month and older pending records separately by resource.
Amounts are positive ARS/USD decimals; past and future calendar dates are
accepted. These records do not change accounts or calculate available money.
Full income/payment confirmation now selects an account and either updates its
cash balance once or records that the movement is already included. Confirmed
income and paid commitments leave pending calculations; identical retries do not
duplicate balance/history changes. M3 remains partial: monthly repetitions can now be stopped, future amount/day
changes are versioned, and confirmations can be corrected with an auditable
inverse adjustment. Partial payments, one-time edits/cancellations, installments
and budgets remain future work, as do M4–M9. Profile supports complete JSON
export and password-confirmed account/data deletion. The
remaining M2 tasks and milestone order are tracked in
[the roadmap](docs/roadmap.md). Email verification, password recovery, abuse
protection, account security controls, and operational deletion-retention policies
are tracked separately in the
[pre-beta checklist](docs/roadmap.md#pre-beta-authentication-and-account-checklist).

## Prerequisites

- Docker with Docker Compose
- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Node.js 24 and npm (mobile client)

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
between 8 and 128 characters; Unicode, whitespace, and passphrases are
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
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins allowed outside local development. Native apps do not require CORS. |
| `POSTGRES_DB` | Creates the local Compose database. |
| `POSTGRES_USER` | Creates the local Compose database user. |
| `POSTGRES_PASSWORD` | Sets the local Compose database password. |
| `DATABASE_URL` | SQLAlchemy Psycopg URL injected by Compose or set for host commands. |

Never commit `.env`; only `.env.example` belongs in version control.

## Run the mobile client

Start the backend first. Then follow the setup, API-address, and verification
instructions in [`mobile/README.md`](mobile/README.md). The complete guided
walkthrough lives in
[`docs/mobile-authentication-course.md`](docs/mobile-authentication-course.md).

`POSTGRES_PASSWORD` initializes a new PostgreSQL volume; changing the variable
does not update the password stored in an existing volume. Preserve volumes
that contain data and change the database role password explicitly. During
initial setup only, an empty local volume can be recreated with
`docker compose down -v`; this command permanently deletes that volume's data.

### Mobile planning returns 404

Rebuild the backend used by the phone after backend code changes:

```powershell
docker compose up --build -d --no-deps --wait backend
```

The backend now applies database migrations before startup. Keep the database
volume. Check `/openapi.json` on the host/port configured by
`EXPO_PUBLIC_API_URL`: it must include `/api/v1/income` and
`/api/v1/commitments`. Reload Expo Go after updating. A host test server on
another port does not update the Docker server used by the phone.

### Start with a useful month view

Inicio now shows current liquid cash minus registered pending bills through month
end, with a separate expected-income forecast and an additional-expense preview.
The first-use flow asks for cash balances and major bills; daily purchase logging
is optional. Movimientos separates payments and income. Only usable areas appear in
the tab bar. This limited snapshot is not safe-to-spend money: daily budgets,
goal reserves still require the remaining MVP work. Movimientos now lets users mark
full income as received and full commitments as paid, with explicit account
selection and reconciliation. Notifications and budgets remain future work.

Movimientos now separates pending cards from modal forms and collapsed history.
Choose an account on creation; monthly occurrences inherit it automatically.
Existing monthly records can remember the selected account on confirmation.
Saved accounts simplify confirmation, but a scheduled date never changes cash
without the user's explicit receipt/payment confirmation.
