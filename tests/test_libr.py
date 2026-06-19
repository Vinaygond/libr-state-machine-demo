import unittest
from decimal import Decimal
from pathlib import Path

from libr import Transaction, calculate_libr, money, read_csv


FIXTURES = Path(__file__).resolve().parents[1] / "examples"


def txn(date, description, amount, separate_deposit="0.00", sequence=0):
    return Transaction(
        date=date,
        description=description,
        amount=money(amount),
        separate_deposit=money(separate_deposit),
        sequence=sequence,
    )


class LibrStateMachineTests(unittest.TestCase):
    def test_community_deposit_does_not_replenish_reduced_claim(self):
        result = calculate_libr(
            [
                txn("2026-01-01", "separate deposit", "100.00", "100.00", 0),
                txn("2026-01-02", "large withdrawal", "-90.00", sequence=1),
                txn("2026-01-03", "community paycheck", "500.00", sequence=2),
            ]
        )

        self.assertEqual(result.final_balance, Decimal("510.00"))
        self.assertEqual(result.traceable_remainder, Decimal("10.00"))

    def test_overdraft_caps_claim_and_lowest_balance_at_zero(self):
        result = calculate_libr(
            [
                txn("2026-01-01", "separate deposit", "100.00", "100.00", 0),
                txn("2026-01-02", "overdraft event", "-150.00", sequence=1),
                txn("2026-01-03", "community deposit", "500.00", sequence=2),
            ]
        )

        self.assertEqual(result.final_balance, Decimal("450.00"))
        self.assertEqual(result.traceable_remainder, Decimal("0.00"))
        self.assertEqual(result.lowest_intermediate_balance, Decimal("0.00"))

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

    def test_minimal_dip_fixture_matches_engineering_page_story(self):
        result = calculate_libr(read_csv(FIXTURES / "minimal_dip_ledger.csv"))

        self.assertEqual(result.final_balance, Decimal("65000.00"))
        self.assertEqual(result.traceable_remainder, Decimal("45000.00"))

        salary_step = result.steps[-1]
        self.assertEqual(salary_step.date, "2024-03-01")
        self.assertEqual(salary_step.account_balance, Decimal("65000.00"))
        self.assertEqual(salary_step.traceable_after, Decimal("45000.00"))
        self.assertEqual(salary_step.event, "community deposit ignored")

    def test_synthetic_fixture_reaches_overdraft_and_zero_traceable_remainder(self):
        result = calculate_libr(read_csv(FIXTURES / "synthetic_ledger.csv"))

        self.assertEqual(result.traceable_remainder, Decimal("0.00"))
        self.assertEqual(result.final_balance, Decimal("16635.38"))
        self.assertEqual(result.lowest_intermediate_balance, Decimal("0.00"))
        self.assertIsNotNone(result.exhaustion_step)
        self.assertEqual(result.exhaustion_step.date, "2026-02-07")
        self.assertEqual(result.exhaustion_step.account_balance, Decimal("-15864.62"))
        self.assertIn("COINBASE", result.exhaustion_step.description)

    def test_overdraft_caps_traceable_at_zero_without_replenishment(self):
        result = calculate_libr(
            [
                txn("2026-01-01", "separate deposit", "1000.00", "1000.00", 0),
                txn("2026-01-02", "overdraft withdrawal", "-1500.00", sequence=1),
                txn("2026-01-03", "community deposit", "800.00", sequence=2),
            ]
        )

        self.assertEqual(result.final_balance, Decimal("300.00"))
        self.assertEqual(result.traceable_remainder, Decimal("0.00"))
        self.assertEqual(result.exhaustion_step.date, "2026-01-02")


if __name__ == "__main__":
    unittest.main()