# Financial Rules

## Purpose and Authority

This document is the authoritative specification for financial behavior. Implementation must stop rather than guess when a rule is marked **Pending decision**. All examples use synthetic data and illustrate only settled rules unless stated otherwise.

## Core Terms and Invariants

- A **balance** is the recorded cash amount currently held in an account. For an investment account, it excludes the value of investment positions.
- An **allocation** reserves part of one source account's existing eligible balance for one goal. It is neither a transfer nor a second balance.
- A **commitment** is a fixed or expected obligation.
- **Expected income** is forecast data until confirmed as received.
- **Liquid** identifies an account whose money may be eligible for spending.
- **Investment value** is the estimated value of positions held separately from investment-account cash and is not automatically spendable cash.
- A **simulation** is hypothetical and cannot change real records without explicit confirmation.
- Every monetary amount has an explicit currency.
- The same money must never be counted or allocated twice.

## Accounts and Balances

An account records a name, account type, currency, current balance, balance-update timestamp, archive status, and whether it is liquid and available for spending. Supported MVP account types include cash, bank, digital wallet, foreign-currency, investment, and other manual accounts. Cash, bank, digital-wallet, and foreign-currency accounts are liquid by default. Investment-account cash and other accounts are non-liquid by default. Investment positions are never liquid.

An investment account's balance is cash only. Positions associated with it are valued separately; a broker total that includes positions is not an account balance for this product. Account balances may be negative to record an overdraft or amount owed in that account. A negative balance is not a second, independent liability; later net-worth calculations must count it once. Each balance update records a historical snapshot. Referenced accounts are archived instead of deleted; archived accounts are excluded from calculations and cannot receive new allocations.

Creating an account records its initial balance as the first snapshot. Updating a balance replaces the current recorded amount and appends a snapshot, even if the amount is unchanged: the snapshot records that the user confirmed the balance again. A balance update is an absolute amount, not a deposit or withdrawal. Archived accounts cannot receive balance updates.

Balance-history reads are paginated in chronological order by timestamp and snapshot ID. The API returns at most 50 snapshots by default, or up to 100 when requested; clients can request later pages with an offset. Pagination limits each response, but does not discard historical records or reduce database storage.

Active-account lists are paginated separately from balance history. The API returns 50 accounts by default, at most 100 per request, ordered by creation time and ID from newest to oldest; an offset selects later pages. The account cash total still includes every active account, not only the displayed page. The mobile overview previews up to five accounts and the management view displays at most 50 at a time.

The displayed **total account cash balance** is calculated independently for each currency by summing the current signed balances of active accounts once. It includes non-liquid account cash, but excludes archived accounts, historical snapshots, investment positions, other assets, and separate liabilities. It is neither net worth nor available-to-spend money. Individual account balances remain visible alongside the total. For example, an ARS 30,000 wallet and an ARS -20,000 bank account display individually and produce an ARS 10,000 total account cash balance.

## Money, Precision, and Rounding

Financial calculations use Python `Decimal`; binary floating point must never be used for money. PostgreSQL precision is:

- Monetary amounts: `NUMERIC(20,2)`.
- Investment quantities: `NUMERIC(28,12)`.
- Unit prices and average acquisition costs: `NUMERIC(28,8)`.
- Exchange rates: `NUMERIC(28,12)`.

Calculations use `ROUND_HALF_UP`. Intermediate calculations are not rounded. Final monetary results are rounded to two decimal places. Inputs must fit their declared precision and scale; values that do not fit are rejected rather than silently truncated. Percentage display precision and treatment of residual fractions after conversions or allocation changes are **Pending decision**.

Deterministic tests must cover storage limits, high-precision quantities, prices and exchange rates, unrounded intermediate values, midpoint rounding, and final two-decimal results.

## Currencies and Exchange Rates

The MVP supports ARS and USD. A user's default reference currency is ARS and may be changed to USD. Availability remains separate per currency and is never converted or consolidated.

Reference-currency net worth may consolidate ARS and USD only with an explicit manually entered exchange rate. Every conversion records the rate, manual source, quote direction, and timestamp. A missing rate prevents consolidation and must never trigger silent conversion or an assumed parity rate. Rate freshness, correction history, and the user-facing quote convention are **Pending decision**.

## Allocations

Every allocation references one source account and one goal. The source account, allocation, and goal must use the same currency. An eligible source account is active, nonnegative, and marked liquid. Archived accounts cannot receive new allocations. Allocated money remains included in its source account balance and is excluded from money available for spending. A new or increased allocation cannot exceed the source account's unallocated eligible balance. An amount already allocated cannot be allocated again.

Allocation ordering, reallocation behavior, and the treatment of a source account balance falling below its existing allocations are **Pending decision**.

Synthetic example: a user records an ARS 500,000 eligible liquid balance and reserves ARS 150,000 from that account for an ARS emergency-fund goal. The source account's unallocated eligible balance becomes ARS 350,000. Its recorded balance remains ARS 500,000; the allocation is not another asset or a transfer.

## `available_today`

`available_today` is calculated independently for each currency. Inputs from different currencies are never combined for this calculation, even when an exchange rate exists.

For one currency:

```text
available_today =
    eligible current liquid balances
    - existing goal allocations
    - unpaid commitments due through month end
    - remaining flexible budget
    - planned goal contributions due this month that are not already allocated
```

Eligible current liquid balances come from active accounts marked liquid, counting only each positive balance. A negative account balance does not cancel positive money held in another account for this calculation; it remains visible in the account list and signed total account cash balance, with an explicit shortfall warning in the future availability explanation. Archived accounts and investment positions are excluded. Investment-account cash and other accounts default to non-liquid; cash, bank, digital-wallet, and foreign-currency accounts default to liquid. The calculation includes only inputs in the currency being calculated. Expected income is not part of `available_today`. Results are not clamped to zero; a negative result after deductions is a projected shortfall. The explanation must identify every included input and deduction.

Synthetic example: an ARS 30,000 liquid wallet and an ARS -20,000 liquid bank account contribute ARS 30,000 of eligible positive balances to `available_today`, before any allocations, commitments, budgets, or planned contributions are deducted. The signed total account cash balance is ARS 10,000. The negative bank balance must be disclosed, not silently omitted or deducted a second time.

The definition of a planned goal contribution being due and treatment of pending transfers and debts are **Pending decision**.

## `available_until_month_end`

`available_until_month_end` is calculated independently for each currency:

```text
available_until_month_end =
    available_today
    + qualifying expected income due through month end
```

Only `PLANNED` income dated from today through the end of the current financial month qualifies. `RECEIVED` income is already reflected as actual data and is not forecast again. `CANCELLED` income is excluded. Overdue `PLANNED` income is excluded and generates a warning. Only expected income in the currency being calculated is included. Results are not clamped to zero; a negative result is a projected shortfall. The forecast remains visibly different from current cash and explains each qualifying or warned income item.

Rescheduling behavior remains **Pending decision**.

## Income and Commitments

Income uses `PLANNED`, `RECEIVED`, and `CANCELLED` statuses. A commitment uses `PLANNED`, `PARTIALLY_PAID`, `PAID`, and `CANCELLED`. Each records an amount, currency, financial date, and recurrence; commitments may also record remaining installments and a remaining amount. Expected income is never treated as received.

For availability, a `PLANNED` commitment deducts its full remaining amount and a `PARTIALLY_PAID` commitment deducts only its remaining amount. `PAID` and `CANCELLED` commitments are excluded. Overdue `PLANNED` and `PARTIALLY_PAID` commitments remain deducted.

The MVP supports `ONE_TIME` and `MONTHLY` recurrence. Monthly templates create period instances idempotently so rerunning generation cannot duplicate an instance for the same template and period. Cancellation, rescheduling, edits to a template after instance generation, and partial-payment history are **Pending decision**.

## Dates and Time

The MVP financial timezone is `America/Argentina/Cordoba`. Financial dates, the meaning of today, due dates, and month boundaries use this timezone. Technical timestamps are stored in UTC and converted only for presentation or financial-date interpretation.

### First M3 slice: one-time planned records

Approved on 2026-10-01: income and commitment amounts must be strictly positive.
Zero and negative inputs are rejected. Inputs must fit `NUMERIC(20,2)` and have
no more than two decimal places, including trailing zero decimals; they are not
rounded on entry. Decimal strings are the mobile/API money boundary; binary
floating-point inputs are rejected. No calculation requiring rounding is added
by this slice.

Creation accepts past, present, and future valid ISO calendar dates
(`YYYY-MM-DD`, years 0001–9999). These are financial dates, not timestamps.
Only `ONE_TIME` records are created, always `PLANNED`. Neither creation nor
consultation changes account balances or snapshots, receives income, or pays
a commitment. No availability, savings, or projection is calculated.

Month consultation includes the selected month's records and, by default,
all older `PLANNED` records. Earlier pending records remain accessible after
month rollover. Records are ordered by financial date ascending and UUID
ascending, with a default limit of 50, maximum 100, and nonnegative offset.
`include_overdue=false` limits consultation to the selected month. This is a
listing policy only; it does not alter income forecast eligibility or commitment
deductions. The mobile screen displays the current financial month, in pages
of 20 per resource, and labels any date before financial today as overdue.
Future-month creation is accepted and its confirmation explains that it will
appear when that month arrives; the API can consult any supported month.

Received/paid/cancelled transitions, editing, rescheduling, deletion, monthly
recurrence, partial payments, installments, budgets, and financial calculations
are outside this slice. Their existing pending decisions remain unchanged.

### Monthly planning extension (approved 2026-10-01)

This extension supersedes the first slice's one-time-only delivery restriction.
The same strictly positive Decimal amount, currency, date, and `PLANNED` rules
apply to both recurrence types. A monthly template uses the chosen first date;
no occurrence predates it. Its original day remains the anchor. If that day is
missing in a month, the occurrence uses that month's last day. For example,
31 January 2027 repeats on 28 February and 31 March; leap-year February uses 29.

Creation atomically saves the template and first occurrence. Consultation fills
missed months through the current financial month, preserving pending records
after inactivity. A future-month consultation creates only that requested month,
without creating intervening future months. It never advances the elapsed-month
checkpoint. A database unique constraint on template/month and serialized
per-template generation prevent duplicate occurrences, including concurrent reads.
Each occurrence retains its own amount, currency and date; ARS and USD are never
combined. No account balances or snapshots change.

Tu mes navigates past, current and future months, keeping its pages of 20 and
older pending records. Its DD/MM/YYYY input is normalized to ISO at the API.
Templates are immutable in this extension. Editing, stopping/cancelling repeats,
status transitions, payment history and availability calculations remain pending.
A manually retried POST after an ambiguous network failure can create another
template; users should refresh the list before retrying.

## Flexible Monthly Budget

The MVP supplies daily life, activities and entertainment, and unexpected-expense categories, and permits additional categories. Detailed purchase entry is optional. Users enter aggregate flexible spending for the month.

For a flexible budget in one currency:

```text
remaining flexible budget =
    planned flexible budget
    - aggregate flexible spending registered for the month
```

The remaining amount is deducted by `available_today`. Category aggregation, rollover, mid-month changes, correction history, and presentation when aggregate spending exceeds the planned budget are **Pending decision**.

## Goals and Goal Progress

A goal records its name, target amount, currency, target date, priority, current allocated amount, and planned monthly contribution. Emergency funds and retirement are goal types. Every allocation identifies its goal and source account, and all three use the same currency. Cross-currency goal allocations are invalid. Referenced goals are archived instead of deleted.

Goal progress, priority effects, completion criteria, overdue target dates, contribution scheduling, and estimated completion-date calculations are **Pending decision**. Projections must identify assumptions and must not be presented as guaranteed.

## Manual Investments

Each MVP position records an asset name, optional symbol, type, quantity, currency, average acquisition cost, first acquisition date, manually entered current price, price-update timestamp, and associated investment account. Supported types are stock, ETF, CEDEAR, bond, mutual fund, cryptocurrency, fixed-term deposit, and other manual investment.

An associated investment account's balance represents cash only. Position values are calculated and stored conceptually separately from that cash balance. A broker-reported total that includes cash and positions must not be added to either component.

The MVP may calculate total acquisition cost, current estimated value, unrealized absolute and percentage change, and portfolio distribution or concentration. Exact valuation and performance formulas, fee treatment, missing-price behavior, price correction history, fixed-term-deposit liquidity, and handling of zero acquisition cost are **Pending decision**.

Partial sales, realized performance, automatic dividends, taxes, complex lots, XIRR, TWR, and automatic market prices are post-MVP. Every displayed investment value shows its price-update time.

Synthetic example: an investment account has a USD 75.00 cash balance and contains 4 units of fictional asset `DEMO`, with a stated first acquisition date and a manually entered USD 40.00000000 price and timestamp. Cash and position value are separate components. A broker total that already includes both cannot be added again. Intermediate calculations retain their full decimal precision, and a final monetary result is rounded to two decimals using `ROUND_HALF_UP`. The position is not automatically spendable.

## Net Worth

Net worth draws from account cash balances, separately valued investment positions, other manually registered assets, debts, and liabilities. Investment values contribute to net worth even though they are not automatically included in availability. An investment account contributes its cash balance plus its separately valued positions. A broker total that already includes those positions is never added, preventing double counting.

ARS and USD totals remain separate unless reference-currency net worth uses an explicit manually entered exchange rate. The rate, manual source, quote direction, and UTC timestamp are recorded. If a required rate is missing, consolidated net worth is unavailable; separate currency totals remain visible.

The liability sign convention, other-asset eligibility, valuation date, missing or stale valuation behavior, and treatment of unpriced positions are **Pending decision**. Where data permits, changes must distinguish contributions, withdrawals, asset-price movements, and exchange-rate effects; the attribution method is **Pending decision**.

## Monthly Close

A monthly close uses updated account cash balances and investment prices to summarize actual savings, savings rate, previous-month comparison, net-worth change, goal progress, and plan-versus-actual differences. It requires:

- Confirmed received income.
- Paid commitments.
- Aggregate flexible spending for the month.
- Other real inflows and outflows.
- Internal transfers.

Internal transfers and investment purchases are movements of value, not expenses. They must be identified so the close does not reduce savings or count the same value twice. The close does not require every purchase to be recorded individually. A confirmed close is locked. Any correction requires an explicit reopen event that is recorded before changes are allowed.

The formulas for actual savings and savings rate, treatment of investment sales and fees, late updates, correction semantics after reopening, baseline selection, and incomplete-data warnings are **Pending decision**.

## Scenario Calculations

The MVP supports an additional one-time expense and a changed recurring monthly contribution. Results may describe changed availability, affected goals, estimated goal-date changes, or required reassignment. Nominal calculations must not silently introduce inflation or expected investment returns.

Scenario calculation rules, allocation ordering, goal-impact priority, confirmation semantics, and behavior when data is incomplete are **Pending decision**. A scenario remains isolated from real records unless the user explicitly confirms a supported change.

## Validation and Edge Cases

Every approved financial rule requires deterministic tests for normal input, invalid input, boundary and zero values, relevant negative values, decimal precision, rounding, currency mismatch, double-counting prevention, and unauthorized access.

At minimum, the system must reject or stop calculations that would:

- Omit a currency from a monetary amount.
- Use a currency other than ARS or USD in the MVP.
- Mix currencies without an explicit exchange rate.
- Consolidate reference-currency net worth without a required manually entered exchange rate.
- Include an archived account in a calculation or create a new allocation from it.
- Create an allocation whose source account, allocation, and goal currencies differ.
- Allocate more than the unallocated eligible balance of the specified source account.
- Allocate the same money more than once.
- Treat expected income as already received.
- Include overdue `PLANNED` income in the month-end forecast without warning and exclusion.
- Exclude an overdue unpaid commitment from availability.
- Treat a simulation as a real mutation without confirmation.
- Automatically treat investment value as spendable cash.
- Count both a broker total and the investment positions represented by that total in net worth.
- Classify an internal transfer or investment purchase as an expense.
- Modify a confirmed monthly close without first recording an explicit reopen.

Error wording, validation timing, and recovery behavior are **Pending decision**.
## Home cash-flow snapshot (2026-10-01)

The home screen provides a deliberately limited diagnostic, `cash_after_bills`,
not `available_today`. For each currency it sums positive active liquid account
balances once and subtracts every PLANNED commitment due on or before current
financial month end, including overdue commitments. Non-liquid accounts,
archived accounts and investment positions are excluded. Negative active account
balances are disclosed separately as a signed total, not silently netted out.

`forecast_after_bills` adds only PLANNED income dated from financial today through
month end. Older pending income is excluded and counted in a warning. Income is
never included in current cash. Both results may be negative. These values omit
flexible spending, goal allocations and goal contributions and must never be
labelled safe-to-spend. The interface states these omissions beside the result.
There is no consolidation across currencies, return assumption or rounding of
inputs. Results use Decimal and serialize as exact two-decimal strings.

The additional-expense preview subtracts a positive amount in the selected
currency from cash_after_bills only. It runs locally with integer cents, remains
hypothetical and creates no financial record. It does not estimate goal effects.
The snapshot materializes current monthly planning occurrences before summing
all matching records, independently of list pagination. An empty setup is not
presented as financial advice; the user is guided to add balances and major bills.
