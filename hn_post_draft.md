# Hacker News Post Draft

## Title

Show HN: A deterministic Python implementation of the Lowest Intermediate Balance Rule

## Body

I built a small Python demo of the Lowest Intermediate Balance Rule, a tracing method used in some commingled-account disputes.

The interesting part, from an engineering perspective, is that the traceable claim behaves like a one-way ledger state machine:

```text
traceable_after = min(traceable_before, account_balance_after)
```

If the account balance falls below the claimed separate-property amount, the claim is capped at that lower balance. Later community deposits can increase the account balance, but they do not replenish the depleted claim.

The repo includes:

- a dependency-free Python calculator
- a synthetic CSV ledger
- tests for zero-balance depletion, same-day ordering ambiguity, multiple separate deposits, and the replenishment fallacy
- CLI modes for `ledger`, `worst_case`, and `best_case` same-day ordering

I am not a lawyer, and this is not legal advice or an admissibility claim. I am sharing it as a narrow technical artifact because the calculation model is surprisingly close to a deterministic financial state machine.

The edge cases I would like feedback on:

- same-day transaction ordering when statements omit timestamps
- multiple separate-property deposits in the same commingled account
- negative balances and overdraft events
- how to expose uncertainty without overstating precision
- whether there are better ways to represent the calculation trace for human review

This came out of a larger private project I am building around forensic financial workflows, but this demo is intentionally standalone and public-safe.

