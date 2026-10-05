# Release review — 2026-10-05

Scope: changes after merge 319bd84 and the follow-up fixes on
codex/one-time-month-planning. This is a partial planning release, not the full MVP.

## Delivered fixes and capabilities

- Home reads balances, commitments and income in one PostgreSQL statement snapshot.
  Regression tests interleave actual confirmation commits with reads for both
  resources and both reconciliation options.
- The home explanation points to Movimientos and explains already-included cash.
- Generation avoids locks/reinsertion for checkpoint-covered months and stops
  iteration at a stopped plan's boundary. Financial formulas are unchanged.
- Future monthly amount/day changes append versions and preserve completed records.
  Stopping cancels only pending occurrences from the chosen month inclusive.
- Correction records an immutable audit event, inversely adjusts current cash when
  appropriate, and permits reconfirmation. Identical retries do not undo a newer
  confirmation. Concurrent correction/stop/generation tests cover both resources.
- Profile exports complete owned financial history, including archived accounts,
  exact decimal strings and audit history, without authentication secrets.
- Password-confirmed deletion removes owned financial data and sessions atomically.
- Native JSON sharing uses expo-file-system and expo-sharing; temporary exports
  are removed afterwards. Web downloads locally without uploading financial data.

## Verification

Backend tests run against an isolated temporary PostgreSQL database, never the
application database. The temporary database is removed after the checks.
Final results: 270 backend tests passed with 99% coverage and 28 mobile tests
passed. Both Android and web exports completed successfully.
Ruff lint/format, strict mypy, mobile lint/typecheck/tests, Android Hermes export
and web export are checked. Alembic checks schema/model agreement. The migration
preservation test starts at 0006 (the last merge), creates synthetic balances and
snapshots, upgrades through 0008, adds a confirmed income and verifies preservation
after 0009 and an empty-maintenance downgrade/upgrade cycle.

Automated builds do not establish native-device usability, store signing, iOS
share-sheet behavior, production configuration or operational recoverability.

## Dependency audit — remaining release work

The npm audit run reports 22 affected packages (19 high, 3 moderate). These are
transitive dependency chains, not 22 independently demonstrated app exploits.
The xcode consumer of uuid is overridden to 11.1.1, which retains the CommonJS
v4 interface and fixes the published bounds-check issue:
[uuid advisory](https://github.com/advisories/GHSA-w5hq-g745-h8pq).

The remaining root advisories are:

- [braces](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm): <=3.0.3, no patched
  release published at review time; present in Metro/micromatch tooling.
- [node-forge](https://github.com/advisories/GHSA-86w9-cpqp-85rv): <=1.4.0, no patched
  release published at review time; present in Expo CLI/certificate tooling.
- [decode-uri-component](https://github.com/advisories/GHSA-vcc3-ghjq-m6fr): a fixed
  0.5.0 release exists, but directly overriding the CommonJS consumer in
  query-string 7.1.3 breaks its call interface. That override is not retained.
  A compatible Expo Router/dependency update or a maintained tested adapter remains
  required. npm's suggested SDK downgrades are not safe blanket fixes.

Keep development/build tooling out of public hosting and do not serve Metro as a
production server. Validate applicable exposure and choose a compatible upstream
fix before claiming dependency readiness. No advisory is suppressed or presented
as resolved without evidence.

## Outstanding release acceptance

- Test the new sheets, cancellations, corrections, native export/save cancellation
  and deletion on synthetic accounts on real Android/iOS devices.
- Validate production HTTPS, secret management, abuse protection, password recovery,
  backups/restore, deletion retention policy, monitoring and deployment rollback.
- Rehearse migrations on a sanitized representative database copy. Audit-preserving
  migrations intentionally reject destructive downgrade once maintenance history
  exists; rolling back application code must not assume schema/data can be erased.
- Complete the dependency work above. The repository is not declared perfect or
  approved for public production based only on passing local checks.
- Budgets, goals/allocations, full safe-to-spend money, investments/net worth and
  monthly close remain MVP roadmap work; this patch does not silently invent their
  pending financial rules.

Learning exercise: with ARS 100, confirm ARS 20, then replace the recorded balance
with ARS 50 and correct the confirmation. An income correction yields ARS 30;
a payment correction yields ARS 70. Explain why neither restores ARS 100.
