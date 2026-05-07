import unittest
from decimal import Decimal

from libr import Transaction, calculate_libr, money


def txn(date, description, amount, separate_deposit="0.00", sequence=0):
    return Transaction(
        date=date,
        description=description,
        amount=money(amount),
        separate_deposit=money(separate_deposit),
        sequence=sequence,
    )


class LibrStateMachineTests(unittest.TestCase):
    def test_community_deposit_does_not_replenish_depleted_claim(self):
        result = calculate_libr(
            [
                txn("2026-01-01", "separate deposit", "100.00", "100.00", 0),
                txn("2026-01-02", "large withdrawal", "-90.00", sequence=1),
                txn("2026-01-03", "community paycheck", "500.00", sequence=2),
            ]
        )

        self.assertEqual(result.final_balance, Decimal("510.00"))
        self.assertEqual(result.traceable_remainder, Decimal("10.00"))

    def test_zero_balance_exhausts_claim(self):
        result = calculate_libr(
            [
                txn("2026-01-01", "separate deposit", "100.00", "100.00", 0),
                txn("2026-01-02", "full depletion", "-100.00", sequence=1),
                txn("2026-01-03", "community deposit", "200.00", sequence=2),
            ]
        )

        self.assertEqual(result.traceable_remainder, Decimal("0.00"))
        self.assertEqual(result.exhaustion_step.date, "2026-01-02")

    def test_new_separate_deposit_can_add_new_traceable_funds(self):
        result = calculate_libr(
            [
                txn("2026-01-01", "first separate deposit", "100.00", "100.00", 0),
                txn("2026-01-02", "withdrawal", "-80.00", sequence=1),
                txn("2026-01-03", "second separate deposit", "50.00", "50.00", 2),
            ]
        )

        self.assertEqual(result.final_balance, Decimal("70.00"))
        self.assertEqual(result.traceable_remainder, Decimal("70.00"))

    def test_same_day_ordering_can_change_traceable_range(self):
        transactions = [
            txn("2026-01-01", "separate deposit", "100.00", "100.00", 0),
            txn("2026-01-02", "community deposit", "50.00", sequence=1),
            txn("2026-01-02", "same-day withdrawal", "-80.00", sequence=2),
        ]

        best_case = calculate_libr(transactions, ordering="best_case")
        worst_case = calculate_libr(transactions, ordering="worst_case")

        self.assertEqual(best_case.final_balance, Decimal("70.00"))
        self.assertEqual(worst_case.final_balance, Decimal("70.00"))
        self.assertEqual(best_case.traceable_remainder, Decimal("70.00"))
        self.assertEqual(worst_case.traceable_remainder, Decimal("20.00"))

    def test_invalid_separate_deposit_raises(self):
        with self.assertRaises(ValueError):
            calculate_libr(
                [
                Transaction(
                    date="2026-01-01",
                    description="bad separate deposit",
                    amount=money("-100.00"),
                    separate_deposit=money("100.00"),
                    sequence=0,
                )
                ]
            )


if __name__ == "__main__":
    unittest.main()
