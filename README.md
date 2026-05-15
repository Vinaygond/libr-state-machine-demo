# LIBR State Machine Demo

A dependency-free Python reference implementation of the Lowest Intermediate
Balance Rule (LIBR), modeled as a deterministic ledger state machine.

This repository is intentionally narrow. It demonstrates one calculation model
using synthetic data and regression tests. It does not include Exit Protocol
application code, OCR logic, report-generation templates, customer data, private
workflows, or production infrastructure.

## Why This Exists

In commingled-account disputes, a traceable separate-property claim can be
reduced when the account balance falls below the claimed amount. Later community
deposits may increase the account balance, but they do not automatically restore
the depleted separate-property claim.

That behavior is easiest to reason about as a state machine:

```text
provisional_traceable = traceable_before + new_separate_deposit
traceable_after = min(provisional_traceable, max(account_balance_after, 0))
```

The goal of this repo is to make the calculation explicit, inspectable, and
easy to test.

## What It Demonstrates

- Chronological LIBR tracing over a CSV transaction ledger
- Separate-property deposits tracked independently from community deposits
- Claim reduction when the account balance drops below the traceable amount
- Zero-balance and overdraft depletion behavior
- Same-day ordering modes for statements without reliable timestamps
- A small CLI that prints material trace events
- Regression tests for the core edge cases

## What It Is Not

This repository is not legal advice, expert testimony, or a court-admissibility
claim.

It is not a substitute for an attorney, forensic accountant, expert witness, or
jurisdiction-specific analysis.

It is not the Exit Protocol production platform. It is a public-safe technical
artifact for review, discussion, and edge-case feedback.

## Repository Structure

```text
libr.py                         Standalone calculator and CLI
examples/synthetic_ledger.csv   Synthetic commingled-account ledger
tests/test_libr.py              Regression tests for core edge cases
```

## Quickstart

Requires Python 3.10+ and no third-party packages.

```bash
python libr.py examples/synthetic_ledger.csv
```

Try same-day ordering modes:

```bash
python libr.py examples/synthetic_ledger.csv --ordering worst_case
python libr.py examples/synthetic_ledger.csv --ordering best_case
```

Run tests:

```bash
python -m unittest discover -s tests
```

## CSV Format

```csv
date,description,amount,separate_deposit
2023-02-08,INITIAL SEPARATE PROPERTY DEPOSIT,250000.00,250000.00
2023-02-10,POS DEBIT: DoorDash,-106.72,0.00
```

Columns:

- `date`: ISO date, `YYYY-MM-DD`
- `description`: transaction description
- `amount`: positive for deposits, negative for withdrawals
- `separate_deposit`: amount of this transaction that represents new
  separate-property funds

## Same-Day Ambiguity

Bank statements often provide dates without reliable timestamps. If a deposit
and withdrawal happen on the same day, ordering can change the traceable result.

The demo supports three modes:

- `ledger`: preserve CSV order within each date
- `worst_case`: withdrawals before deposits within each date
- `best_case`: deposits before withdrawals within each date

This does not resolve legal uncertainty. It exposes the calculation range so a
reviewer can see the effect of missing timestamp detail.

## Public Scope

This public repo is meant to show the deterministic core of a narrow tracing
method. The larger Exit Protocol product adds document ingestion, evidence
organization, review workflows, report generation, and security controls around
similar calculation primitives.

For product context, see: https://exitprotocols.com
