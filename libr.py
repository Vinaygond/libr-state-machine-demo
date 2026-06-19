#!/usr/bin/env python3
"""Dependency-free LIBR state-machine reference implementation.

This public demo models the Lowest Intermediate Balance Rule as a small,
deterministic ledger calculation. It intentionally excludes Exit Protocol
application code, OCR pipelines, report templates, customer data, and private
infrastructure. V1 single-claim replay only; multi-claim pro-rata allocation is
out of scope for this artifact.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Literal


OrderingMode = Literal["ledger", "worst_case", "best_case"]
CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Decimal | str | int) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    date: str
    description: str
    amount: Decimal
    separate_deposit: Decimal = ZERO
    sequence: int = 0

    def validate(self) -> None:
        if not self.date:
            raise ValueError("Transaction date is required")
        if self.separate_deposit < ZERO:
            raise ValueError("separate_deposit cannot be negative")
        if self.separate_deposit > ZERO and self.amount <= ZERO:
            raise ValueError("separate_deposit must be attached to a positive deposit")
        if self.separate_deposit > ZERO and self.separate_deposit > self.amount:
            raise ValueError("separate_deposit cannot exceed transaction amount")


@dataclass(frozen=True)
class Step:
    date: str
    description: str
    amount: Decimal
    separate_deposit: Decimal
    account_balance: Decimal
    traceable_before: Decimal
    traceable_after: Decimal
    event: str


@dataclass(frozen=True)
class Result:
    ordering: OrderingMode
    steps: tuple[Step, ...]

    @property
    def final_balance(self) -> Decimal:
        return self.steps[-1].account_balance if self.steps else ZERO

    @property
    def traceable_remainder(self) -> Decimal:
        return self.steps[-1].traceable_after if self.steps else ZERO

    @property
    def lowest_intermediate_balance(self) -> Decimal:
        if not self.steps:
            return ZERO
        return min(max(step.account_balance, ZERO) for step in self.steps)

    @property
    def exhaustion_step(self) -> Step | None:
        for step in self.steps:
            if step.event == "claim exhausted":
                return step
        return None


def sort_transactions(
    transactions: Iterable[Transaction],
    ordering: OrderingMode = "ledger",
) -> list[Transaction]:
    txns = list(transactions)
    for txn in txns:
        txn.validate()

    if ordering == "ledger":
        return sorted(txns, key=lambda txn: (txn.date, txn.sequence))

    if ordering == "worst_case":
        return sorted(
            txns,
            key=lambda txn: (
                txn.date,
                0 if txn.amount < ZERO else 1,
                txn.sequence,
            ),
        )

    if ordering == "best_case":
        return sorted(
            txns,
            key=lambda txn: (
                txn.date,
                0 if txn.amount >= ZERO else 1,
                txn.sequence,
            ),
        )

    raise ValueError(f"Unknown ordering mode: {ordering}")


def classify_event(
    txn: Transaction,
    traceable_before: Decimal,
    traceable_after: Decimal,
) -> str:
    if txn.separate_deposit > ZERO:
        return "separate deposit added"
    if traceable_after == ZERO and traceable_before > ZERO:
        return "claim exhausted"
    if traceable_after < traceable_before:
        return "claim reduced"
    if txn.amount > ZERO:
        return "community deposit ignored"
    return "no traceable change"


def calculate_libr(
    transactions: Iterable[Transaction],
    ordering: OrderingMode = "ledger",
) -> Result:
    ordered = sort_transactions(transactions, ordering)
    balance = ZERO
    traceable = ZERO
    steps: list[Step] = []

    for txn in ordered:
        traceable_before = traceable
        balance = money(balance + txn.amount)

        if txn.separate_deposit > ZERO:
            traceable = money(traceable + txn.separate_deposit)

        balance_floor = max(balance, ZERO)
        traceable = money(min(traceable, balance_floor))

        steps.append(
            Step(
                date=txn.date,
                description=txn.description,
                amount=txn.amount,
                separate_deposit=txn.separate_deposit,
                account_balance=balance,
                traceable_before=traceable_before,
                traceable_after=traceable,
                event=classify_event(txn, traceable_before, traceable),
            )
        )

    return Result(ordering=ordering, steps=tuple(steps))


def read_csv(path: Path) -> list[Transaction]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"date", "description", "amount", "separate_deposit"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")

        transactions = []
        for sequence, row in enumerate(reader):
            transactions.append(
                Transaction(
                    date=row["date"].strip(),
                    description=row["description"].strip(),
                    amount=money(row["amount"]),
                    separate_deposit=money(row["separate_deposit"]),
                    sequence=sequence,
                )
            )
        return transactions


def format_money(value: Decimal) -> str:
    prefix = "-" if value < ZERO else ""
    value = abs(value)
    return f"{prefix}${value:,.2f}"


def result_to_dict(result: Result) -> dict:
    return {
        "ordering": result.ordering,
        "final_balance": str(result.final_balance),
        "traceable_remainder": str(result.traceable_remainder),
        "lowest_intermediate_balance": str(result.lowest_intermediate_balance),
        "exhaustion_step": (
            {
                "date": result.exhaustion_step.date,
                "description": result.exhaustion_step.description,
                "account_balance": str(result.exhaustion_step.account_balance),
                "traceable_after": str(result.exhaustion_step.traceable_after),
            }
            if result.exhaustion_step
            else None
        ),
        "material_steps": [
            {
                **{key: str(value) if isinstance(value, Decimal) else value for key, value in asdict(step).items()}
            }
            for step in result.steps
            if step.event != "no traceable change"
        ],
    }


def print_result(result: Result) -> None:
    print(f"ordering: {result.ordering}")
    print(f"final account balance: {format_money(result.final_balance)}")
    print(f"traceable remainder: {format_money(result.traceable_remainder)}")
    print(f"lowest intermediate balance: {format_money(result.lowest_intermediate_balance)}")

    if result.exhaustion_step:
        step = result.exhaustion_step
        print(f"claim exhausted on: {step.date} ({step.description})")

    print()
    print("material trace events:")
    for step in result.steps:
        if step.event != "no traceable change":
            print(
                f"{step.date} | {step.event:25} | "
                f"amount={format_money(step.amount):>12} | "
                f"balance={format_money(step.account_balance):>12} | "
                f"traceable={format_money(step.traceable_after):>12} | "
                f"{step.description}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a deterministic LIBR calculation.")
    parser.add_argument("csv_path", type=Path, help="CSV ledger path")
    parser.add_argument(
        "--ordering",
        choices=("ledger", "worst_case", "best_case"),
        default="ledger",
        help="Same-day transaction ordering strategy",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human-readable summary",
    )
    args = parser.parse_args()

    result = calculate_libr(read_csv(args.csv_path), args.ordering)
    if args.json:
        print(json.dumps(result_to_dict(result), indent=2))
    else:
        print_result(result)


if __name__ == "__main__":
    main()
