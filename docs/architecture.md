# System Architecture

## Architecture Goals and Constraints

The system is a mobile-first personal finance planner implemented as a modular monolith. The architecture prioritizes understandable financial rules, strict user isolation, decimal-safe money handling, testability, and the ability to add verified integrations later without coupling the domain to providers.

The initial system uses a Python 3.12-or-later FastAPI backend, an Expo/React Native TypeScript mobile application, PostgreSQL, Docker, and GitHub Actions. It does not require microservices, Redis, queues, Celery, Terraform, Kubernetes, or complex AWS infrastructure.

## System Context

The mobile application is the user-facing client. It sends authenticated requests to the backend. The backend coordinates application use cases, applies pure financial rules, and persists user-owned data in PostgreSQL. During the MVP, accounts, cash balances, income, commitments, aggregate flexible spending, other real inflows and outflows, internal transfers, goals, allocations, investment positions, and investment prices are entered manually.

No bank, broker, wallet, market-data, news, messaging, or other external integration is available in the MVP.

## Modular Monolith

The backend deploys as one application while separating responsibilities internally. Financial domain logic must not depend directly on FastAPI, SQLAlchemy, React Native, PostgreSQL, or an external provider.

Expected repository layout:

```text
backend/
  app/
    api/           HTTP transport and request dependencies
    domain/        Pure financial entities, rules, and calculations
    models/        SQLAlchemy persistence models
    schemas/       Pydantic boundary schemas
    services/      Application use cases and orchestration
    repositories/  Persistence access
    integrations/  Future external-provider adapters
  tests/
mobile/            Expo and React Native application
docs/              Product, financial, roadmap, and architecture specifications
.github/workflows/ Continuous integration and delivery configuration
```

Imports and calls should point inward toward the domain. Transport and persistence adapt data at the boundaries; they do not redefine financial behavior.

## Domain Modules

The modular monolith contains cohesive areas for:

- Identity and user preferences.
- Accounts and balances.
- Income, commitments, and flexible budgets.
- Goals and allocations.
- Available-money calculations.
- Scenarios.
- Monthly close.
- Investments and net worth.

Exact Python package boundaries and rules for cross-module access are **Pending decision**. Modules should be grouped by domain or feature and must avoid catch-all utility packages.

## Backend Responsibilities

- **API layer:** validates transport input, authenticates requests, and invokes application services.
- **Schemas:** define validated data at application boundaries without becoming financial-rule implementations.
- **Services:** coordinate use cases, ownership checks, repositories, and domain operations.
- **Domain:** contains framework-independent entities, value concepts, invariants, and calculations.
- **Repositories:** isolate persistence operations and preserve user scoping.
- **Models:** map persisted state to PostgreSQL through SQLAlchemy.
- **Integrations:** provide boundaries for future verified providers; the directory does not imply that any provider exists.

Endpoint shapes, versioning, error envelopes, and public API contracts are **Pending decision** and are intentionally not specified here. Resource identifiers themselves are application-generated UUID v4 values.

## Mobile Application

The Expo/React Native TypeScript application presents registration, setup, planning, investment, simulation, and monthly-close workflows. Each completed domain milestone includes its minimal usable mobile screen; mobile work is not deferred to a final integration phase. The application must show actual values, forecasts, and assumptions distinctly and provide calculation explanations supplied by approved backend behavior.

Navigation, state management, API-client implementation, offline behavior, localization, accessibility targets, and secure credential storage are **Pending decision**.

## Persistence with PostgreSQL

PostgreSQL is the system of record. SQLAlchemy provides persistence mapping and Alembic manages schema changes. Application-generated UUID v4 identifiers are stored in PostgreSQL `UUID` columns. Every user-owned record is scoped to its owner, and every amount carries either ARS or USD.

Python uses `Decimal`. PostgreSQL stores monetary amounts as `NUMERIC(20,2)`, investment quantities as `NUMERIC(28,12)`, prices as `NUMERIC(28,8)`, and exchange rates as `NUMERIC(28,12)`. Domain calculations use `ROUND_HALF_UP`, do not round intermediate results, and round final monetary results to two decimal places.

The schema must preserve the distinction between account cash balances, allocations, income, commitments, aggregate flexible spending, other inflows and outflows, internal transfers, goals, simulations, and investment positions and valuations. An investment account balance is cash only; positions are separate records and a broker total containing them is not independently added to net worth.

Every allocation references one source account and one goal. The account, allocation, and goal have the same currency, and allocation changes are validated against the active source account's unallocated eligible balance. Archived accounts cannot receive allocations. Allocations must not duplicate balances or imply a transfer. Simulations remain separate from real records until an explicitly confirmed supported action occurs.

Balance changes create historical snapshots. Referenced accounts and goals are archived instead of deleted, and archived accounts are excluded from calculations and new allocations. `MONTHLY` recurrence templates create period instances idempotently. Confirmed monthly closes are locked; an explicit reopen event is recorded before a correction. Detailed table shapes, snapshot correction policy, archival behavior for unreferenced records, and concurrency controls are **Pending decision**.

The first accounts slice persists `financial_accounts` and `account_balance_snapshots` separately. An account stores its current cash balance, currency, liquidity flag, and last balance-update time. Creation and each absolute balance update append a snapshot in the same transaction. Account queries and mutations always include the authenticated user's identifier; archived accounts are hidden from active-account operations. The versioned account API currently supports create, list, read, balance update, balance history, and archive. The mobile account screen covers create, list, and balance update; account metadata editing and archived-account management remain for a later bounded slice.

Technical timestamps are stored in UTC. Financial dates, today, due dates, and month boundaries use `America/Argentina/Cordoba`.

## Core Data Flows

### Record or update financial data

The mobile client submits user-entered data. The API validates its boundary shape and identity. A service verifies ownership and invokes domain validation. A repository persists approved state. The response returns user-scoped data without exposing sensitive records in logs.

### Calculate available money

A service groups the user's relevant inputs by currency. For each currency, the domain calculates `available_today` from active nonnegative liquid balances, allocations, unpaid commitments due through month end, remaining flexible budget, and unallocated planned goal contributions due this month. It then adds only `PLANNED` income dated from today through month end for `available_until_month_end`. Overdue planned income is excluded with a warning; overdue unpaid commitments remain deducted. Negative values remain visible as projected shortfalls. The backend returns each per-currency result with its included and excluded inputs.

### Value investments and net worth

A service loads investment-account cash, manually entered positions, first acquisition dates, prices and timestamps, other assets, liabilities, and any explicit exchange rates. The domain values cash and positions separately and prevents a broker total from duplicating them. Results retain price timing and distinguish investment value from spendable cash.

### Run a scenario

A service creates an isolated hypothetical input, evaluates it through existing domain rules, and returns its effects. No real record changes unless the user explicitly confirms an action supported by a separately defined use case.

### Close a month

A service gathers confirmed received income, paid commitments, aggregate flexible spending, other real inflows and outflows, internal transfers, updated account cash balances, and updated investment prices. The domain excludes internal transfers and investment purchases from expenses, applies only approved savings and comparison rules, and reports incomplete inputs according to the still-pending policy. Confirmation locks the close; correction begins by recording an explicit reopen.

## Authentication, Authorization, and Privacy

Passwords require an appropriate secure hashing algorithm. Every user-resource operation validates ownership. External input is untrusted. Credentials, tokens, complete sensitive records, and bank or broker credentials must not be logged or committed. Production uses managed secret storage. Data export and deletion must exist before public launch.

The MVP uses normalized email identifiers and Argon2id password hashes. Normal
requests use locally verified HS256 access JWTs that expire after 15 minutes.
Random refresh tokens rotate on every use, slide for up to 20 days, and belong
to a device-session family that expires absolutely after 90 days. PostgreSQL
stores only SHA-256 refresh-token hashes. Logout revokes one refresh session;
logout-all revokes every family for the user. These choices and reuse detection
are recorded in `docs/decisions/0002-jwt-refresh-sessions.md`. Recovery flow,
retention policy, and detailed audit requirements remain **Pending decision**.

## Currency and Calculation Boundaries

All monetary operations use the approved decimal types and rounding policy. Availability is calculated independently for ARS and USD and is never converted or combined. The user's default reference currency is ARS and may be changed to USD. Reference-currency net worth may combine currencies only with an explicit manually entered exchange rate whose value, manual source, quote direction, and UTC timestamp are retained. A missing required rate prevents consolidation while separate currency totals remain available. The domain keeps cash balances, allocations, internal transfers, expected income, simulations, and investment market value semantically distinct.

Goal projection, monthly-savings metrics, advanced investment formulas, and remaining net-worth rules remain governed by `financial-rules.md`. Architecture components must not supply fallback financial behavior when a rule is **Pending decision**.

## Docker and Local Development

Docker Compose runs FastAPI and PostgreSQL locally. Expo runs on the host machine and connects to the containerized backend through documented configuration. Local secrets and settings use ignored `.env` files; a sanitized `.env.example` contains placeholders only. Development and test environments may use synthetic data only.

Ports, health checks, volume strategy, synthetic seed-data workflow, and environment-variable names are **Pending decision** but do not block creating the repository scaffold.

## CI/CD and Deployment

GitHub Actions runs on pull requests and pushes to `main`. Backend checks use Ruff for formatting and linting, mypy for static type checking, and pytest with pytest-cov for tests and coverage reporting. Mobile checks use ESLint and `tsc --noEmit`. Every configured check is blocking. Coverage is reported without a blocking threshold initially.

Deployment initially targets a managed cloud environment. Branch protections, artifact strategy, deployment provider, environments, approval gates, rollback process, backups, recovery objectives, logging, and monitoring are **Pending decision**.

## Future Integration Boundaries

The WhatsApp interface is the first planned post-MVP product feature, but it is not part of the MVP. It must enter through an explicit adapter and application services and require structured confirmation before applying changes.

Later bank, wallet, broker, CSV, market-data, and news capabilities follow the same adapter boundary. Provider data must be translated into internal domain concepts, validated as untrusted input, and never become the source of financial rules.

No provider or protocol is selected. An integration requires legal, commercial, security, and technical validation plus a tested proof of concept before product documentation may describe it as available.

## Architecture Decisions Still Pending

Material decisions should be recorded under `docs/decisions/` when they are made. Authentication and mobile session handling are defined in ADRs 0002 and 0003. Remaining topics include package boundaries, API conventions beyond authentication, detailed persistence behavior, deployment, observability, backup, retention, and integration providers.
