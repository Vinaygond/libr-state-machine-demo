import json
import subprocess
import unittest
from pathlib import Path

from libr import VERSION, calculate_libr, read_csv, result_to_dict


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "examples" / "expected"


class GoldenFixtureTests(unittest.TestCase):
    def _load_expected(self, name: str) -> dict:
        return json.loads((EXPECTED / name).read_text(encoding="utf-8"))

    def _run_cli(self, *args: str) -> dict:
        raw = subprocess.check_output(
            ["python", "libr.py", *args, "--json"],
            cwd=ROOT,
            text=True,
        )
        return json.loads(raw)

    def test_minimal_dip_golden_output_matches_cli(self):
        expected = self._load_expected("minimal_dip_ledger.ledger.json")
        actual = self._run_cli("examples/minimal_dip_ledger.csv")
        self.assertEqual(actual, expected)

    def test_synthetic_golden_output_matches_cli(self):
        expected = self._load_expected("synthetic_ledger.ledger.json")
        actual = self._run_cli("examples/synthetic_ledger.csv")
        self.assertEqual(actual, expected)

    def test_minimal_dip_worst_case_golden_output_matches_cli(self):
        expected = self._load_expected("minimal_dip_ledger.worst_case.json")
        actual = self._run_cli(
            "examples/minimal_dip_ledger.csv",
            "--ordering",
            "worst_case",
        )
        self.assertEqual(actual, expected)

    def test_result_to_dict_matches_direct_calculation(self):
        result = calculate_libr(read_csv(ROOT / "examples" / "minimal_dip_ledger.csv"))
        payload = result_to_dict(result)
        self.assertEqual(payload["traceable_remainder"], "45000.00")
        self.assertEqual(payload["ordering"], "ledger")

    def test_version_is_declared(self):
        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()