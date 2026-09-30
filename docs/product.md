# Product Specification

## Product Overview

This product is a mobile-first personal finance planning application initially designed for people in Argentina. It helps users understand what they own, what money is already committed, what they can safely spend, and how current decisions affect future goals.

The product is not a bank, broker, accounting system, or financial advisor. It does not hold money, execute trades, or recommend assets.

## Target Users

The initial users are individuals who manage money across cash, banks, digital wallets, foreign currencies, debts, and investments. They want useful planning without recording every purchase. They may face irregular income, installments, multiple currencies, or manually managed investments.

## Problem and Value Proposition

Balances alone do not show how much money is truly available. Some money is reserved for obligations or goals, expected income has not arrived, and investments may not be spendable.

The product promise is:

> Show users how much they can actually spend and how each decision changes their future financial goals.

It does this by separating actual data, allocations, forecasts, and assumptions; explaining calculations; and preventing the same money from being counted twice.

## Product Principles

- Planning takes priority over exhaustive expense tracking.
- Consequences are explained without blaming the user.
- Actual values, projections, and assumptions remain visibly distinct.
- Projections are never presented as guaranteed outcomes.
- Calculations favor clarity over unnecessary sophistication.
- Manual entry is minimized where possible without claiming unavailable integrations.
- Financial privacy and strict separation between users are mandatory.
- The product does not provide personalized investment recommendations.

## MVP Features

### Users and authentication

Users register with a normalized email address, use short-lived access tokens
and revocable rotating refresh sessions, and select ARS or USD as their
reference currency. ARS is the default. Passwords are hashed with Argon2id, and
every user-owned resource is isolated from other users. Social login,
multi-factor authentication, and the exact account-recovery flow are outside
the initial requirement or **Pending decision**.

Registration explains invalid email syntax, password-length and confirmation errors before submission. A duplicate email produces an explicit conflict message. The current home prioritizes recorded accounts and balances; profile data and logout are shown in a separate section below. No unavailable financial metric is shown as if it were implemented.

### Financial accounts

Users manually create cash, bank, digital-wallet, foreign-currency, investment, and other accounts in ARS or USD. Cash, bank, digital-wallet, and foreign-currency accounts are liquid by default; investment-account cash and other accounts are non-liquid by default. Investment positions are never liquid. Accounts may record negative balances, including overdrafts; the same overdraft must not also be counted as a separate liability.

Each account records its name, type, currency, current balance, update time, and whether it is liquid and available for spending. Balance updates create historical snapshots. Referenced accounts are archived rather than deleted; archived accounts are excluded from calculations and cannot receive new allocations. An investment account's balance represents cash only, while its positions are valued separately.

The account view shows each signed balance and a separate signed total of active account cash per currency. This total is not net worth or safe-to-spend money. A negative account does not automatically reduce the positive liquid balance of another account in the availability calculation; the shortfall remains visible and is explained.

### Income, commitments, and flexible budgets

Users record one-time or monthly income with an expected date and a status of `PLANNED`, `RECEIVED`, or `CANCELLED`. Only `PLANNED` income dated from today through month end qualifies for the month-end forecast. Overdue planned income is excluded and generates a warning. Expected income is never treated as received money.

Users also record commitments such as rent, services, subscriptions, credit-card payments, debt payments, and installments. Commitment statuses are `PLANNED`, `PARTIALLY_PAID`, `PAID`, and `CANCELLED`. Unpaid planned or partially paid amounts are deducted according to their remaining amount, including when overdue; paid and cancelled commitments are excluded. Monthly recurrence creates period instances idempotently.

Instead of requiring every purchase, the MVP provides a flexible monthly budget. Its initial categories are daily life, activities and entertainment, and unexpected expenses. Users may add categories. Usage is entered as aggregate spending for the month rather than as individual purchases. Remaining flexible budget is the planned amount minus that aggregate spending.

### Goals and allocations

Users create goals for travel, a car, a home, an emergency fund, retirement, or a custom purpose. Goals record a target amount and currency, target date, priority, allocated amount, and planned monthly contribution. Referenced goals are archived instead of deleted.

An allocation references one source account and one goal and reserves money already held in that account. The account, allocation, and goal use the same currency. An allocation does not move or create money. Allocated money remains part of the source account balance but is excluded from spendable money. New allocations cannot exceed that account's unallocated eligible balance, so the same money cannot fund multiple goals. An emergency fund is a goal type, not a separate subsystem.

### Available money

The MVP distinguishes:

- `available_today`: eligible current liquid balances minus existing goal allocations, unpaid commitments due through month end, remaining flexible budget, and planned goal contributions due this month that have not already been allocated.
- `available_until_month_end`: `available_today` plus qualifying expected income due through month end.

Availability is calculated independently for ARS and USD. Results are not clamped to zero; a negative value represents a projected shortfall. Every result explains which balances, allocations, income, commitments, budgets, and planned contributions were considered. Financial dates and month boundaries use `America/Argentina/Cordoba`.

### Scenario simulator

Users can simulate an additional one-time expense or a different recurring monthly contribution. A simulation may show changed availability, affected goals, estimated goal-date changes, or required reassignment. It never changes real records without explicit confirmation. MVP projections use nominal values and do not silently include inflation or investment returns.

### Monthly close

Users update account cash balances and investment prices at month end and receive a summary of actual savings, savings rate, prior-month comparison, net-worth change, goal progress, and differences between plan and outcome. A close requires confirmed received income, paid commitments, aggregate flexible spending, other real inflows and outflows, and internal transfers. Internal transfers and investment purchases are not expenses. A close does not require every purchase to be recorded individually. Once confirmed, a close is locked; correcting it requires an explicit recorded reopen.

### Net worth

Net worth includes account cash balances, separately valued investment positions, manually registered assets, debts, and liabilities. An investment account balance is cash only. A broker total must never be added alongside its positions because that would count the same value twice. Where the available data permits, changes distinguish contributions, withdrawals, asset-value changes, and exchange-rate effects. Reference-currency net worth may combine ARS and USD only with an explicit manually entered exchange rate; a missing rate prevents consolidation.

### Manual investment portfolio

Manual investment tracking is part of the MVP. Users associate positions with investment accounts and record asset name, optional symbol, supported asset type, quantity, currency, average acquisition cost, first acquisition date, current price, and price-update time.

Supported types are stocks, ETFs, CEDEARs, bonds, mutual funds, cryptocurrency, fixed-term deposits, and other manual investments. The MVP may display acquisition cost, estimated value, unrealized absolute and percentage change, and portfolio concentration or distribution. Investment value contributes to net worth but is not automatically spendable. Every displayed value identifies when its price was last updated.

## Primary MVP User Flows

1. Register, select a reference currency, and create accounts.
2. Enter current balances and identify which accounts are liquid.
3. Record expected income, commitments, a flexible monthly budget, and aggregate monthly spending.
4. Create goals and reserve existing money through source-account allocations.
5. Review per-currency, explained `available_today` and `available_until_month_end` values, including any projected shortfall.
6. Add manually priced investment positions, including first acquisition dates, and review estimated portfolio value separately from broker cash.
7. Test a hypothetical expense or contribution without changing real data.
8. Update balances and prices during monthly close and review progress.

## Synthetic Example

The following data is entirely synthetic and illustrates the approved formulas.

Lucia uses the default ARS reference currency and records an eligible liquid ARS bank balance of ARS 800,000. She allocates ARS 250,000 from that account to an ARS travel goal. She has a `PLANNED` ARS 120,000 rent commitment due this month, an ARS 180,000 flexible budget with ARS 60,000 of aggregate spending, and an unallocated ARS 50,000 planned goal contribution due this month. Her remaining flexible budget is ARS 120,000. Her `available_today` is therefore ARS 260,000. A `PLANNED` ARS 900,000 salary dated between today and month end qualifies, so her `available_until_month_end` is ARS 1,160,000. A negative result would remain visible as a shortfall.

Lucia also records USD 100 of cash in an investment account and 10 units of fictional asset `SYNTH`, first acquired on a stated date and manually priced at USD 25 with a price-update timestamp. The USD account cash and the position value are separate net-worth components. A broker total containing both must not be added again. The USD amounts remain separate from ARS availability and require an explicit recorded exchange rate before reference-currency net worth can combine them.

## Post-MVP Vision

The first planned post-MVP product feature is a WhatsApp interface for recording important financial events, asking about availability, allocating money, and running simulations with structured confirmation before changes. It is not included in the MVP.

Later post-MVP work may include legally and commercially verified market-data providers, cited financial news summaries, price alerts, advanced investment transactions and performance, a compound-interest calculator, retirement planning, and proven CSV, bank, wallet, or broker integrations.

These capabilities do not exist in the MVP. No integration may be presented as available before its legal, security, commercial, and technical viability has been verified and a proof of concept has been tested.

## Non-Goals

- Custodying money or storing bank or broker credentials.
- Executing payments or investment trades.
- Providing tax calculations or personalized buy, sell, or hold advice.
- Requiring exhaustive transaction-level expense tracking.
- Real-time market pricing in the MVP.
- MVP support for XIRR, TWR, complex investment lots, automatic dividends, or realized performance across partial sales.
- Microservices or complex infrastructure without a demonstrated need.

## Success Criteria

The MVP succeeds when a user can:

- Build an understandable, currency-aware view of accounts, obligations, goals, investments, and net worth.
- See explained availability without allocated money, expected income, or investment value being mislabeled.
- Plan without entering every purchase.
- Explore supported scenarios without unintentionally changing real data.
- Complete a monthly review using balance and price updates.
- Export and delete their data before public launch.

Numeric adoption, retention, accuracy, and performance targets are **Pending decision**.

## Pending Product Decisions

- Authentication identifier, recovery flow, and session behavior.
- Offline behavior, localization, and accessibility requirements.
- Whether non-investment assets and liabilities require dedicated MVP interfaces.
- Exact success metrics and measurement periods.
- Whether export and deletion are required for private testing or only before public launch.
