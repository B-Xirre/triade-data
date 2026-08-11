from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from m10_dependencies import apply_dependencies, load_seed, stable_snapshot  # noqa: E402
from r7_grist import column_metadata, user_table_ref  # noqa: E402


class M10DependencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = (
            REPO_ROOT.parents[1]
            / "deliverables"
            / "Triade - Equipment Authoring-R7.grist"
        )
        if not cls.source.exists():
            raise unittest.SkipTest("R7-complete .grist working copy is unavailable")
        cls.seed = load_seed(REPO_ROOT / "content" / "csv")

    def test_seed_has_locked_m10_dependency_shape(self) -> None:
        self.assertEqual(
            {table: len(rows) for table, rows in self.seed.items()},
            {
                "Chassis_profiles": 5,
                "Integrity_profiles": 1,
                "Integrity_states": 3,
                "Construction_profiles": 2,
            },
        )
        self.assertEqual(
            [row["state_id"] for row in self.seed["Integrity_states"]],
            ["stable", "cracked", "broken_guard"],
        )
        shield = next(
            row for row in self.seed["Construction_profiles"]
            if row["construction_profile_id"] == "construction.shield_standard"
        )
        self.assertEqual(shield["bridge2_mechanism"], "barycentre_well")

    def test_apply_is_stable_id_exact_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "candidate.grist"
            shutil.copy2(self.source, document)
            connection = sqlite3.connect(document)
            connection.row_factory = sqlite3.Row
            try:
                with connection:
                    first = apply_dependencies(connection, self.seed)
                with connection:
                    second = apply_dependencies(connection, self.seed)
                snapshot = stable_snapshot(connection)
                self.assertEqual(snapshot, self.seed)
                self.assertEqual(first["before_counts"], {
                    "Chassis_profiles": 0,
                    "Integrity_profiles": 0,
                    "Integrity_states": 0,
                    "Construction_profiles": 0,
                })
                self.assertEqual(first["after_counts"], second["before_counts"])
                self.assertTrue(first["q_fields_remain_null"])
                self.assertTrue(first["authored_columns_are_data"])
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM Ref_rules").fetchone()[0], 143
                )
                fixture_ref = user_table_ref(connection, "Fixture_coverage")
                self.assertEqual(
                    column_metadata(connection, fixture_ref, "rule_id")["type"],
                    "Ref:Ref_rules",
                )
                for table, fields in {
                    "Chassis_profiles": ("chassis_profile_id", "handedness"),
                    "Integrity_profiles": ("integrity_profile_id",),
                    "Integrity_states": ("integrity_state_row_id", "integrity_profile", "state"),
                    "Construction_profiles": ("construction_profile_id", "integrity_profile"),
                }.items():
                    table_ref = user_table_ref(connection, table)
                    for field in fields:
                        self.assertEqual(
                            column_metadata(connection, table_ref, field)["isFormula"], 0
                        )
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
