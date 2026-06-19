# LIBR State Machine Demo

A dependency-free Python reference implementation of the Lowest Intermediate
Balance Rule (LIBR), modeled as a deterministic ledger state machine.

This repository is intentionally narrow. It demonstrates one calculation model
using synthetic data and regression tests. It does not include Exit Protocol
application code, OCR logic, report-generation templates, customer data, private
workflows, or production infrastructure.

It is the public companion artifact for [Exit Protocol](https://exitprotocols.com/)'s engineering note on [LIBR as a deterministic ledger state machine](https://exitprotocols.com/engineering/libr-state-machine/).

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
- A small CLI that prints material trace events or JSON output
- Regression tests for the core edge cases

## Scope Boundary

- **V1 single-claim replay only** — one traceable claim path through one ordered ledger.
- **Multi-claim pro-rata allocation** exists in the private Exit Protocol product and requires separate review; it is not implemented here.
- **Synthetic fixtures only** — for technical inspection and regression testing.

## What It Is Not

This repository is not legal advice, expert testimony, or a court-admissibility
claim.

It is not a substitute for an attorney, forensic accountant, expert witness, or
jurisdiction-specific analysis.

It is not the Exit Protocol production platform. It is a public-safe technical
artifact for review, discussion, and edge-case feedback.

## Repository Structure

```text
libr.py                              Standalone calculator and CLI
examples/synthetic_ledger.csv        Longer SIM-style synthetic commingled ledger
examples/minimal_dip_ledger.csv      Small dip-and-hold fixture used on the engineering page
tests/test_libr.py                   Regression tests for core edge cases
.github/workflows/test.yml            CI regression runner
LICENSE                              MIT license
```

## Quickstart

Requires Python 3.10+ and no third-party packages.

```bash
python libr.py examples/synthetic_ledger.csv
python libr.py examples/minimal_dip_ledger.csv
```

Try same-day ordering modes:

```bash
python libr.py examples/synthetic_ledger.csv --ordering worst_case
python libr.py examples/synthetic_ledger.csv --ordering best_case
```

Emit JSON for scripts or diligence checks:

```bash
python libr.py examples/minimal_dip_ledger.csv --json
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

| Demo mode | Meaning | Exit Protocol strategy alias |
|---|---|---|
| `ledger` | preserve CSV order within each date | neutral |
| `worst_case` | withdrawals before deposits within each date | minimize |
| `best_case` | deposits before withdrawals within each date | maximize |

This does not resolve legal uncertainty. It exposes the calculation range so a
reviewer can see the effect of missing timestamp detail.

## Relationship to Exit Protocol

Exit Protocol uses deterministic LIBR replay inside attorney-reviewable V1
workpapers. This repository isolates the calculation model so developers,
forensic accountants, and diligence reviewers can inspect the state machine
directly.

Public product surfaces:

- Engineering note: https://exitprotocols.com/engineering/libr-state-machine/
- LIBR guide: https://exitprotocols.com/libr/
- Synthetic sample workpaper: https://exitprotocols.com/sample-report/

## Public Discussion Angle

> I found a tracing rule that behaves like a deterministic ledger state machine.
> I built a tiny Python implementation with synthetic data and tests. I am
> looking for edge-case feedback on same-day ordering, overdraft rows, and how
> to present calculation traces for human review.
