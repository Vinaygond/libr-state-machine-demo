# LIBR State Machine Demo

This is a small, standalone Python demo of the Lowest Intermediate Balance Rule (LIBR) modeled as a deterministic ledger state machine.

It is designed as a public-safe technical artifact for discussion, testing, and feedback. It does not contain Exit Protocol application code, Django models, OCR logic, report-generation templates, customer data, private workflows, or production infrastructure.

## What It Demonstrates

In a commingled account, a traceable separate-property claim behaves like a one-way ratchet:

```text
traceable_after = min(traceable_before, account_balance_after)
```

Later community deposits can increase the account balance, but they cannot replenish a separate-property claim after the claim has been depleted.

New separate-property deposits are treated separately and can increase the traceable claim, subject to the account balance at that point in the ledger.

## What It Is Not

This is not legal advice.

This is not a substitute for an attorney, forensic accountant, expert witness, or jurisdiction-specific legal analysis.

This is not a claim that a generated output is admissible in court.

This is just a transparent calculation model with synthetic data and regression tests.

## Files

```text
libr.py                         Standalone calculator and CLI
examples/synthetic_ledger.csv   Small synthetic commingled ledger
tests/test_libr.py              Regression tests for core edge cases
hn_post_draft.md                Draft Hacker News post built around this artifact
```

## Run It

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
- `separate_deposit`: amount of this transaction that represents new separate-property funds

## Same-Day Ambiguity

Bank statements often provide dates without reliable timestamps. If a deposit and withdrawal happen on the same day, ordering can change the traceable result.

The demo supports three modes:

- `ledger`: preserve CSV order within each date
- `worst_case`: withdrawals before deposits within each date
- `best_case`: deposits before withdrawals within each date

This does not resolve legal uncertainty. It exposes the calculation range so a reviewer can see the effect of missing timestamp detail.

## Public Repo Strategy

If this folder is split into its own public repository, the recommended repo name is:

```text
libr-state-machine-demo
```

Recommended Hacker News angle:

> I found a weird legal/accounting rule that behaves like a deterministic ledger state machine. I built a tiny Python implementation with synthetic data and tests. I am looking for edge-case feedback.

Avoid framing this as replacing experts, guaranteeing legal outcomes, or producing court-admissible reports.

