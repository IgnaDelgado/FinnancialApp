# AGENTS.md

## Project Identity

This repository contains a mobile-first personal finance planning application,
initially designed for users in Argentina.

The application is not a bank, broker, accounting system or financial advisor.
It does not custody money, execute trades or recommend buying or selling assets.

Its main purpose is to answer:

1. How much money does the user currently have?
2. How much of that money is already committed or allocated?
3. How much can the user safely spend?
4. How is the user progressing toward financial goals?
5. How would a financial decision affect those goals?
6. How are the user's net worth and investments evolving?

The main product promise is:

> Show users how much they can actually spend and how each decision changes
> their future financial goals.

## Product Principles

- Planning is more important than detailed expense tracking.
- Users are not required to register every small purchase.
- Show consequences instead of blaming users.
- Never count the same money twice.
- Clearly separate actual data, projections and assumptions.
- Never present projections as guaranteed results.
- Prefer understandable calculations over complex financial metrics.
- Minimize manual data entry whenever possible.
- Protect user trust and financial privacy.
- Do not provide personalized investment recommendations.

## MVP Scope

The MVP includes the following modules.

### 1. Authentication and users

- User registration.
- Login and logout.
- Secure password storage.
- Strict separation of data between users.
- User-selected reference currency.

Social login and multi-factor authentication are not required initially.

### 2. Financial accounts

Users can manually create accounts such as:

- Cash.
- Bank account.
- Digital wallet.
- Foreign-currency account.
- Investment account.
- Other manual account.

Each account has:

- Name.
- Account type.
- Currency.
- Current balance.
- Balance update timestamp.
- Whether it is liquid and available for spending.

Every amount must have an explicit currency.

### 3. Income

Users can register:

- Salary.
- Freelance income.
- Bonuses.
- Extra income.
- Other recurring or one-time income.

Income may have:

- Amount.
- Currency.
- Expected date.
- Recurrence.
- Confirmation status.

Expected income must never be treated as already received.

### 4. Commitments

Users can register:

- Rent.
- Services.
- Subscriptions.
- Credit-card payments.
- Debt payments.
- Installments.
- Other fixed or expected obligations.

A commitment may include:

- Amount.
- Currency.
- Due date.
- Recurrence.
- Remaining installments.
- Payment status.

### 5. Flexible monthly budget

The MVP includes a simple monthly flexible budget instead of detailed mandatory
expense tracking.

Initial categories:

- Daily life.
- Activities and entertainment.
- Unexpected expenses.

Users may add additional categories, but granular tracking is optional.

### 6. Goals and allocations

Users can create financial goals such as:

- Travel.
- Car.
- Home.
- Emergency fund.
- Retirement.
- Custom goal.

A goal has:

- Name.
- Target amount.
- Currency.
- Target date.
- Priority.
- Current allocated amount.
- Planned monthly contribution.

Money allocated to a goal remains part of an account balance but is not
available for spending.

The sum of allocations in a currency must never exceed eligible account
balances in that currency.

The same money must never be allocated to multiple goals.

The emergency fund is implemented as a goal type, not as an independent
financial system.

### 7. Available money

The application must distinguish between:

- `available_today`: current liquid money that is not allocated or reserved.
- `available_until_month_end`: a forecast including expected income and pending
  commitments before the end of the month.

The interface must explain which balances, allocations, income and commitments
were included in every calculation.

The definitive formulas and edge cases belong in:

- `docs/financial-rules.md`

Do not implement an unresolved formula. Report the missing decision first.

### 8. Scenario simulator

The MVP supports at least two scenarios:

- An additional one-time expense.
- A different recurring monthly contribution.

The simulator may show:

- New available amount.
- Goals affected.
- Estimated changes to goal completion dates.
- Money that must be reassigned.

Simulations must not modify real user data unless explicitly confirmed.

Initial calculations use nominal values. Inflation and expected investment
returns must not be silently included.

### 9. Monthly close

Users can update account and investment balances at the end of a month.

The application summarizes:

- Actual savings.
- Savings rate.
- Comparison with the previous month.
- Net-worth change.
- Goal progress.
- Differences between the plan and actual outcome.

The application does not require every transaction to be recorded to perform a
monthly close.

### 10. Net worth

Net worth is calculated from:

- Cash and financial account balances.
- Investment portfolio values.
- Other manually registered assets.
- Debts and liabilities.

Net worth changes must distinguish, whenever data allows:

- New user contributions.
- Withdrawals.
- Changes in asset values.
- Changes caused by exchange rates.

Amounts in different currencies must not be added without an explicit exchange
rate and reference currency.

### 11. Manual investment portfolio

Investments are included in the MVP, but market-data integrations are not.

Supported asset types:

- Stock.
- ETF.
- CEDEAR.
- Bond.
- Mutual fund.
- Cryptocurrency.
- Fixed-term deposit.
- Other manually registered investment.

Each manual position has:

- Asset name.
- Symbol, when applicable.
- Asset type.
- Quantity.
- Currency.
- Average acquisition cost.
- Manually entered current price.
- Price update timestamp.
- Associated investment account.

The MVP may calculate:

- Total acquisition cost.
- Current estimated value.
- Unrealized absolute gain or loss.
- Unrealized percentage gain or loss.
- Portfolio distribution.
- Concentration by asset and currency.

The MVP does not initially calculate:

- XIRR.
- TWR.
- Tax obligations.
- Complex lot accounting.
- Automatic dividends.
- Realized performance across partial sales.
- Real-time or automatic market prices.

Investment balances contribute to net worth but are not automatically included
in available-to-spend calculations.

All displayed investment values must indicate when prices were last updated.

## Post-MVP Scope

The following features are part of the long-term product vision but are not part
of the first implementation.

### WhatsApp interface

- Register important financial events through text or audio.
- Ask questions about available money.
- Allocate money to goals.
- Simulate expenses.
- Require structured confirmation before applying changes.

### Automated market data

- Obtain authorized market prices from a provider that permits commercial use.
- Display whether prices are real-time, delayed or end-of-day.
- Never use an unverified data source in production.

### Financial news and AI

- Retrieve news related to followed assets and the user's portfolio.
- Summarize information using cited sources.
- Separate facts, data, interpretation and uncertainty.
- Never invent causes for price movements.
- Never provide buy, sell or hold instructions.

### Price alerts

- Configurable target prices.
- Percentage movements.
- Relevant portfolio news.
- Important financial events.

### Advanced investment tracking

- Buy and sell transactions.
- Dividends.
- Fees and taxes.
- Investment lots.
- Realized returns.
- XIRR and TWR after verified implementations and known test cases.

### Compound-interest calculator

Inputs may include:

- Initial capital.
- Periodic contributions.
- Time horizon.
- Assumed annual return.
- Inflation.
- Fees.
- Currency.

Results must separate contributions from estimated returns and clearly display
all assumptions.

### Retirement planning

Retirement is a long-term goal, not an investment product.

It may include:

- Current age.
- Target retirement age.
- Desired capital or income.
- Current savings.
- Monthly contribution.
- Inflation and return assumptions.
- Associated investment portfolio.
- Conservative, base and optimistic scenarios.

### Future financial integrations

CSV imports, banks, digital wallets and brokers may be considered only after
their legal, technical, security and commercial viability is verified.

Never claim that an integration exists before creating and testing a technical
proof of concept.

## Project Structure

Use this monorepo structure:

- `backend/`: FastAPI backend.
- `backend/app/api/`: HTTP routes and dependencies.
- `backend/app/domain/`: pure financial entities, rules and calculations.
- `backend/app/models/`: SQLAlchemy persistence models.
- `backend/app/schemas/`: Pydantic schemas.
- `backend/app/services/`: application use cases.
- `backend/app/repositories/`: persistence access.
- `backend/app/integrations/`: external provider adapters.
- `backend/tests/`: backend automated tests.
- `mobile/`: Expo and React Native mobile application.
- `docs/`: product, architecture and financial specifications.
- `.github/workflows/`: CI/CD configuration.

Financial domain logic must not depend directly on FastAPI, SQLAlchemy, React
Native or external providers.

## Technical Stack

### Backend

- Python 3.12 or later.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- Alembic.
- PostgreSQL.
- pytest.
- Ruff.
- Static type checking.
- Docker.

### Mobile

- TypeScript.
- React Native.
- Expo.

### Delivery

- GitHub.
- GitHub Actions.
- Docker Compose for local development.
- Managed cloud deployment initially.

Start as a modular monolith.

Do not introduce microservices, Redis, queues, Celery, Terraform, Kubernetes or
complex AWS infrastructure without a demonstrated requirement.

## Money and Currency Rules

- Use Python `Decimal` for monetary calculations.
- Use PostgreSQL `NUMERIC` for monetary columns.
- Never use binary floating point for money.
- Every amount must include a currency.
- Never silently mix currencies.
- Currency conversion requires an explicit exchange rate.
- Record the rate, source and timestamp used for a conversion.
- Rounding rules must be explicit and tested.
- Preserve the difference between balances, allocations and actual transfers.
- Allocating money does not create or move money.
- Simulations do not modify real records.
- Investment market value is different from available cash.

The authoritative specification is:

- `docs/financial-rules.md`

## Security and Privacy

- Never commit credentials, tokens or `.env` files.
- Provide `.env.example` with placeholders only.
- Never use real personal financial information in tests.
- Never log passwords, access tokens or complete sensitive records.
- Never store bank or broker credentials.
- Validate ownership on every user resource.
- Treat all external input as untrusted.
- Hash passwords using an appropriate password-hashing algorithm.
- Use secure secret management in deployed environments.
- Support data export and deletion before a public launch.

## Educational Working Mode

This project is also intended to teach the developer backend, databases,
testing, Docker, CI/CD, mobile development and system design.

Before implementing a complex feature:

1. Read the relevant documentation and existing code.
2. Explain the proposed design.
3. Identify assumptions and alternatives.
4. Explain the concepts the developer should understand.
5. Divide the work into small, verifiable steps.

When reviewing developer-written code:

1. Do not immediately replace it.
2. Explain functional errors.
3. Explain design problems.
4. Identify missing tests and edge cases.
5. Propose the smallest reasonable correction.

After implementing a task:

1. Run relevant tests.
2. Run linting and type checks.
3. Summarize modified files.
4. Explain important decisions.
5. Report assumptions and technical debt.
6. Ask a short question or propose an exercise to verify understanding.

## Coding Conventions

- Use descriptive English identifiers.
- Use `snake_case` for Python functions and variables.
- Use `PascalCase` for classes and React components.
- Add type annotations to public Python functions.
- Keep functions focused on one responsibility.
- Group code by domain or feature.
- Avoid generic catch-all utility modules.
- Avoid premature abstractions.
- Do not add production dependencies without explaining their purpose.
- Do not change unrelated files.
- Do not generate large amounts of code in one task.

## Testing Requirements

Every financial rule requires deterministic tests covering:

- Normal behavior.
- Invalid input.
- Boundary values.
- Zero values.
- Negative values where relevant.
- Decimal precision.
- Rounding.
- Currency mismatch.
- Double-counting prevention.
- Unauthorized resource access.

Use observable test names such as:

- `test_available_money_excludes_goal_allocations`
- `test_rejects_mixed_currencies_without_exchange_rate`
- `test_investment_value_is_excluded_from_spendable_cash`
- `test_allocation_cannot_exceed_eligible_balance`

Use only synthetic fixtures.

## Task Workflow

For each task:

1. Confirm the goal and read relevant files.
2. Plan before changing code.
3. Implement one bounded behavior.
4. Add or update tests.
5. Run verification commands.
6. Review the diff.
7. Explain the result.
8. Make a small commit.

A task is complete only when:

- Required behavior works.
- Tests pass.
- Lint and type checks pass.
- No secrets or personal data are included.
- Documentation matches financial behavior.
- The diff contains no unrelated changes.

## Git Conventions

Use focused branches and Conventional Commits:

- `feat: add manual financial account`
- `feat: add manual investment position`
- `test: cover goal allocation limits`
- `fix: prevent duplicated allocation`
- `docs: define available money calculation`

Pull requests must explain:

- Problem.
- Implemented solution.
- Important decisions.
- Validation performed.
- Screenshots for visible changes.
- Known limitations.

## Required Documentation

Maintain these documents:

- `docs/product.md`: complete product vision and MVP scope.
- `docs/financial-rules.md`: authoritative calculations and financial behavior.
- `docs/architecture.md`: system architecture and technical decisions.
- `docs/roadmap.md`: implementation phases and priorities.
- `docs/decisions/`: architecture decision records when needed.

If documentation and implementation disagree, stop and report the inconsistency
instead of guessing.