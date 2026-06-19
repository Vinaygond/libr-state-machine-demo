# Validation Matrix

This document maps regression coverage to reviewable LIBR behaviors. It is for
technical diligence only — not legal advice, expert opinion, or admissibility
analysis.

## Core Invariants

| Invariant | Meaning |
|---|---|
| Trace never exceeds account | After every step, `traceable_after <= max(account_balance_after, 0)` |
| Trace never negative | Traceable balance is floored at zero |
| Non-replenishment | Community deposits do not restore a trace previously reduced by a dip |
| Deterministic replay | Same CSV rows + same ordering mode => same outputs |
| Separate deposits are additive | New `separate_deposit` funds can increase traceable balance, capped by account balance |

## Regression Coverage

| Test / fixture | Scenario | Expected signal |
|---|---|---|
| `test_community_deposit_does_not_replenish_reduced_claim` | Partial dip, later paycheck | Traceable stays below restored account balance |
| `test_zero_balance_exhausts_claim` | Full depletion to zero | `claim exhausted` event recorded |
| `test_new_separate_deposit_can_add_new_traceable_funds` | Second separate deposit | Traceable can rise again from a new funding event |
| `test_same_day_ordering_can_change_traceable_range` | Same-day deposit + withdrawal | `best_case` and `worst_case` diverge |
| `test_overdraft_caps_claim_and_lowest_balance_at_zero` | Balance below zero | Traceable remainder `0.00`; lowest intermediate balance `0.00` |
| `examples/minimal_dip_ledger.csv` | Dip then later salary | Account rises; traceable holds at `$45,000.00` |
| `examples/synthetic_ledger.csv` | Long commingled walkthrough | Traceable remainder `0.00`; exhaustion on `2026-02-07` |
| `examples/expected/*.json` | Golden CLI outputs | Reproducible machine-readable references |

## Reviewer Checklist

1. Run `python -m unittest discover -s tests`.
2. Run `python libr.py examples/minimal_dip_ledger.csv` and confirm traceable remainder `$45,000.00`.
3. Run `python libr.py examples/synthetic_ledger.csv` and confirm exhaustion on the COINBASE row.
4. Compare `--ordering best_case` vs `--ordering worst_case` on a same-day fixture.
5. Inspect `examples/expected/*.json` if you need deterministic output references for scripts or diligence packets.

## Known Limits

- V1 single-claim replay only
- No multi-claim pro-rata allocation
- No opening-balance modeling beyond CSV row replay
- Same-day ordering modes expose ambiguity; they do not resolve legal timestamp uncertainty
- Jurisdiction-specific tracing doctrines may require additional assumptions not modeled here