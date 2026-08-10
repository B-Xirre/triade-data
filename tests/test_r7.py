from __future__ import annotations

import csv
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from generate_ref_rules import EXPECTED_COUNTS, parse_index, write_seed  # noqa: E402
from r7_grist import export_fixture_coverage, load_seed  # noqa: E402


class R7Tests(unittest.TestCase):
    def test_governed_index_generates_byte_identical_seed(self) -> None:
        index = Path(
            os.environ.get(
                "TRIADE_VALIDATION_RULES_INDEX",
                str(
                    Path(__file__).resolve().parents[3]
                    / "governed"
                    / "TRIADE-Validation_Rules_Index-0_21_0.md"
                ),
            )
        )
        if not index.exists():
            self.skipTest("set TRIADE_VALIDATION_RULES_INDEX to the governed 0.21.0 index")
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            rules = parse_index(index)
            first = temporary / "first.csv"
            second = temporary / "second.csv"
            write_seed(rules, first)
            write_seed(rules, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            seed = load_seed(first)
        self.assertEqual(len(seed), 143)
        self.assertEqual(
            {
                severity: sum(row["severity"] == severity for row in seed)
                for severity in EXPECTED_COUNTS
            },
            EXPECTED_COUNTS,
        )

    def test_reference_export_emits_stable_rule_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            document = temporary / "synthetic.grist"
            connection = sqlite3.connect(document)
            connection.row_factory = sqlite3.Row
            connection.executescript(
                """
                CREATE TABLE _grist_Tables (id INTEGER PRIMARY KEY, tableId TEXT);
                CREATE TABLE _grist_Tables_column (
                  id INTEGER PRIMARY KEY, parentId INTEGER, colId TEXT, type TEXT
                );
                CREATE TABLE Ref_rules (id INTEGER PRIMARY KEY, rule_id TEXT);
                CREATE TABLE Fixture_coverage (
                  id INTEGER PRIMARY KEY,
                  manualSort NUMERIC,
                  fixture_coverage_id TEXT,
                  rule_id INTEGER,
                  gristHelper_Display BLOB
                );
                INSERT INTO _grist_Tables VALUES (17, 'Ref_rules'), (41, 'Fixture_coverage');
                INSERT INTO _grist_Tables_column VALUES (88, 17, 'rule_id', 'Text');
                INSERT INTO _grist_Tables_column VALUES (443, 41, 'rule_id', 'Ref:Ref_rules');
                INSERT INTO Ref_rules VALUES (7, 'P-C8');
                INSERT INTO Fixture_coverage VALUES (1, 1, 'proof-1', 7, 'P-C8');
                """
            )
            destination = temporary / "fixture_coverage.csv"
            export_fixture_coverage(connection, destination)
            connection.close()
            with destination.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(rows, [{"fixture_coverage_id": "proof-1", "rule_id": "P-C8"}])


if __name__ == "__main__":
    unittest.main()
