# Product Roadmap

## Roadmap Principles

This roadmap delivers the smallest verifiable planning capability first. Financial rules must be decided and tested before dependent calculations are implemented. Each milestone preserves currency boundaries, user ownership, and the distinction between balances, allocations, forecasts, simulations, and investment values.

Items under Post-MVP are not part of the initial release. A milestone may not claim completion while a required financial rule remains **Pending decision**.

Delivery is backend-first. Backend sub-milestones may be implemented through
the core planning capabilities before mobile work begins. This sequencing does
not remove mobile acceptance criteria: an MVP milestone is complete only after
both its backend behavior and required mobile interface are delivered.

## MVP Milestones

### M0 — Financial rules and repository foundation

**Depends on:** Initial product documentation.

Create the prescribed monorepo layout and development baseline using the approved M0 financial, persistence, tooling, and local-environment decisions. Docker Compose runs FastAPI and PostgreSQL; Expo runs on the host.

**Acceptance criteria:**

- Backend monetary amounts, quantities, prices, and exchange rates use their approved decimal types and `ROUND_HALF_UP` policy.
- Application-generated UUID v4 identifiers map to PostgreSQL `UUID` columns.
- Backend checks use Ruff, mypy, pytest, and pytest-cov; mobile checks use ESLint and `tsc --noEmit`.
- GitHub Actions runs every blocking check on pull requests and pushes to `main`; coverage is reported without an initial threshold.
- Docker Compose starts FastAPI and PostgreSQL, while Expo runs on the host through documented commands.
- Ignored `.env` files and a sanitized `.env.example` support local configuration.
- Only synthetic development and test data is used; no credentials or personal financial records are committed.

**Decisions blocking M0:** None. Exact ports, environment-variable names, package boundaries, and similar implementation details can be chosen during scaffolding without changing approved product or financial behavior.

### M1 — Authentication and user isolation

**Depends on:** M0.

Implement registration, login, logout, secure password storage, reference-currency selection, ownership enforcement for user resources, and the minimal mobile screens for those flows.

**Acceptance criteria:**

- A user can complete the supported authentication flow.
- Passwords are never stored or logged in plain text.
- One user cannot read or modify another user's resources.
- Reference currency supports ARS and USD, defaults to ARS, and is retained for each user.
- The mobile app provides working registration, login, logout, and reference-currency selection screens.

The current authentication identifier, session mechanism, and password-hashing
implementation are defined in `docs/decisions/0002-jwt-refresh-sessions.md`;
ADR 0001 preserves the superseded initial design. Account
recovery remains **Pending decision** and is not required for the initial MVP.

### M2 — Accounts and current balances

**Depends on:** M1 and approved account/currency rules from M0.

Implement ARS and USD accounts, current balances, historical balance snapshots, archive behavior, liquidity/spendability flags, and a minimal mobile account list and editor.

**Acceptance criteria:**

- A user can manage the supported account types and update balances.
- Monetary amounts use `NUMERIC(20,2)` storage and Python `Decimal` calculations.
- Account responses and operations enforce ownership.
- Investment-account balances represent cash only and never include position value.
- Cash, bank, digital-wallet, and foreign-currency accounts default to liquid; investment-account cash and other accounts default to non-liquid.
- Negative balances and overdrafts can be recorded in accounts and their history.
- The account screen shows each signed balance and a signed total per currency, separate from safe-to-spend money.
- Referenced accounts are archived instead of deleted, are excluded from calculations, and cannot receive new allocations.
- Balance updates create historical snapshots.
- The mobile app can list, create, and update accounts and cash balances.
- Negative-balance and account-history behavior match approved rules.

**Current status — partial implementation.** The API supports owned account
creation, paginated active listing, read, signed balance updates, paginated
history, per-currency cash totals, and archival. Balance changes append
snapshots. Mobile supports creation and full-balance updates; home previews five
accounts, while account management uses pages of 50. The displayed total
includes all active accounts in that currency, not just the visible page.
Negative balances and browser-session restoration in development have been
tested. Mobile now displays balance history from the selected account, in
pages of 20 snapshots with Argentina timestamps and retry controls. Account
metadata editing and a dedicated archived-account management view remain to
finish M2. Mobile account removal now requires confirmation and archives the
account, refreshes active totals, and preserves persisted history. Production
web session persistence needs a separate secure-cookie decision. The M3–M9
milestones below are not implemented by this slice.

### M3 — Income, commitments, and flexible budgets

**Depends on:** M2 and approved recurrence/status rules.

Implement one-time and recurring income, commitments and installments, flexible-budget plans and aggregate monthly spending, and their minimal mobile list and editor screens.

**Acceptance criteria:**

- Income supports `PLANNED`, `RECEIVED`, and `CANCELLED`; commitments support `PLANNED`, `PARTIALLY_PAID`, `PAID`, and `CANCELLED`.
- `ONE_TIME` and `MONTHLY` recurrence is supported, and monthly period instances are generated idempotently.
- Financial dates and month boundaries use `America/Argentina/Cordoba`; technical timestamps use UTC.
- Expected income remains distinguishable from received income.
- Users can create monthly flexible budgets and enter aggregate spending without recording every purchase.
- Remaining flexible budget equals planned budget minus aggregate spending for the month.
- The mobile app supports the required income, commitment, budget, and aggregate-spending entries.
- Tests cover idempotent recurrence, partial remaining amounts, overdue records, cancellations, and financial month boundaries.

### M4 — Goals and allocations

**Depends on:** M2 and approved allocation-eligibility rules.

Implement goals, including emergency-fund and retirement goal types, planned contributions, source-account allocations of existing eligible balances, and minimal mobile goal and allocation screens.

**Acceptance criteria:**

- Users can create goals with target details, priority, and planned contribution.
- Allocations do not create or transfer money.
- Every allocation references one source account and one goal, all in the same currency.
- Allocations cannot exceed the source account's unallocated eligible balance or count the same money twice.
- Archived accounts cannot receive new allocations.
- Referenced goals are archived instead of deleted.
- Goal and allocation resources remain isolated by user.
- The mobile app can show goals and create or change valid allocations from a selected source account.

### M5 — Explained available money

**Depends on:** M2–M4 and approved eligibility, status, and timing rules for every formula input.

Implement the approved `available_today` and `available_until_month_end` formulas and a minimal mobile availability screen.

**Acceptance criteria:**

- Each value is calculated independently per currency using the approved deterministic rule.
- The result explains included balances, allocations, commitments, remaining flexible budget, planned contributions, qualifying income, and exclusions.
- Expected income is not presented as current money.
- Only `PLANNED` income dated from today through month end qualifies; overdue planned income is excluded with a warning.
- Planned and partially paid commitments deduct their remaining amounts, including when overdue; paid and cancelled commitments are excluded.
- Investment positions are never spendable; investment-account cash defaults to non-liquid.
- Negative results remain visible as projected shortfalls.
- Final monetary results are rounded to two decimals with `ROUND_HALF_UP` after unrounded intermediate calculations.
- The mobile app presents both values per currency with their explanations.
- Tests cover zero, negative, boundary, precision, rounding, currency mismatch, and double-counting cases.

### M6 — Manual investments and net worth

**Depends on:** M2 and approved investment, valuation, conversion, and net-worth rules.

Implement manual investment accounts and positions, first acquisition dates, price timestamps, permitted portfolio summaries, manually registered assets and liabilities, net-worth presentation, and minimal mobile portfolio and net-worth screens.

**Acceptance criteria:**

- Users can manage every supported manual asset type without market-data integration.
- Displayed investment values show the manual price-update time.
- Investment-account cash and position values are stored and displayed separately.
- Net worth never counts both a broker total and the positions represented by that total.
- Investment quantities use `NUMERIC(28,12)` and prices use `NUMERIC(28,8)`.
- Net worth never silently mixes currencies. Consolidation uses a manually entered `NUMERIC(28,12)` exchange rate; a missing required rate prevents consolidation.
- Availability excludes investment value unless a later explicit rule makes a liquid amount eligible.
- Unsupported advanced performance calculations are absent.
- The mobile app can create and update positions and display portfolio and net-worth summaries.

### M7 — Scenario simulator

**Depends on:** M4–M6 and approved scenario rules.

Implement simulations for an additional one-time expense and a changed recurring monthly contribution, with a minimal mobile simulation screen.

**Acceptance criteria:**

- Results identify affected availability and goals using approved rules.
- Nominal projections do not silently include inflation or investment returns.
- Opening, editing, or discarding a scenario does not mutate real records.
- Any supported application of a scenario requires explicit confirmation.
- The mobile app can enter, review, and discard both supported scenario types.

### M8 — Monthly close

**Depends on:** M3–M7 and approved close and savings rules.

Implement the monthly update and review workflow and its minimal mobile close screen without requiring transaction-level expense history.

**Acceptance criteria:**

- Users can update account cash balances and manual investment prices.
- A close includes confirmed received income, paid commitments, aggregate flexible spending, other real inflows and outflows, and internal transfers.
- Internal transfers and investment purchases are not classified as expenses.
- A confirmed close is locked and requires an explicit recorded reopen before correction.
- The close reports only metrics whose formulas have been approved.
- Results distinguish known contributions, withdrawals, valuation changes, and exchange-rate changes where the data permits.
- Incomplete or stale data is identified according to approved rules.
- The mobile app collects the required close inputs and presents the resulting summary.

### M9 — Release readiness

**Depends on:** M1–M8.

Integrate and polish the mobile screens delivered by M1–M8, then complete security review, operational readiness, documentation, and user-controlled export and deletion required before public launch.

**Acceptance criteria:**

- Domain screens delivered incrementally in M1–M8 work as a coherent Expo/React Native application.
- Automated checks cover domain rules and unauthorized access.
- No secrets, bank credentials, or complete sensitive records appear in code or logs.
- Users can export and delete their data before public availability.
- Deployment, backup, monitoring, recovery, accessibility, and release gates meet documented decisions.

Deployment provider, observability stack, retention policy, numeric quality thresholds, and whether export/deletion block private testing are **Pending decision**.

## Pre-beta authentication and account checklist

M1 authentication V2 is sufficient for local development and continued MVP
feature work. Before inviting external users to a public beta, complete and
verify the following bounded security and account-management capabilities:

1. **Email verification.** Prove ownership with an expiring, single-use token
   and decide whether unverified accounts may sign in or access financial data.
2. **Password recovery.** Return a generic response that does not disclose
   whether an email exists; store only a hash of the random reset token; expire
   and invalidate it after one use; revoke active refresh sessions after reset.
3. **Abuse protection.** Rate-limit registration, login, verification, and
   recovery attempts without exposing account existence.
4. **Authenticated password change.** Require the current password, hash the
   replacement with Argon2id, and revoke previous refresh sessions.
5. **Session management.** Let users inspect and revoke active device sessions
   without exposing raw refresh tokens or unnecessary device information.
6. **Data export and account deletion.** Provide user-controlled export and a
   documented deletion flow before public availability.

Email delivery requires a selected provider, verified sending domain, secure
production secrets, HTTPS callback links, retry behavior, and tests. No email
provider is selected yet, so the implementation must not invent one.

Face ID or device biometrics may later protect local access to an existing
session, but they do not replace backend authentication. Multi-factor
authentication and social login remain optional post-beta improvements unless
risk or user research demonstrates an earlier requirement.

## Dependency Summary

M0 establishes decisions and tooling. M1 provides identity and isolation. M2 supplies balances used by M3 and M4. Availability in M5 depends on accounts, obligations, budgets, and allocations. M6 adds investments and net worth. Scenarios in M7 reuse settled availability and goal rules. Monthly close in M8 depends on the accumulated financial state. Every M1–M8 domain slice includes its minimal mobile interface; M9 integrates and validates the complete MVP for release.

## Post-MVP Roadmap

Post-MVP work is considered only after MVP behavior is stable and each external dependency is verified:

1. A WhatsApp interface with structured confirmation before mutations.
2. CSV import, followed by technically and legally viable bank, wallet, or broker integrations.
3. Automated market data from an authorized provider, with price timing clearly labeled.
4. Price alerts and portfolio-related events.
5. Advanced investment transactions, dividends, fees, taxes, lots, realized returns, XIRR, and TWR after formulas and test cases are approved.
6. Compound-interest and retirement-planning tools with visible assumptions and scenarios.
7. Cited financial news and AI summaries that separate facts, interpretation, and uncertainty.

No provider, API, or integration is selected or available yet. WhatsApp is the fixed first post-MVP product feature; provider selection, legal review, technical proofs of concept, and the order of later items are **Pending decision**.
