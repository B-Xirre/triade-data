from __future__ import annotations

import copy
import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from m10_equipment import (  # noqa: E402
    BRIDGE2_CHOICES,
    M10EquipmentError,
    apply_equipment,
    load_seed,
    stable_snapshot,
)
from r7_grist import column_metadata, user_table_ref  # noqa: E402


class M10EquipmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = (
            REPO_ROOT.parents[1]
            / "deliverables"
            / "Triade - Equipment Authoring-M10-dependencies.grist"
        )
        if not cls.source.exists():
            raise unittest.SkipTest("M10 dependency .grist working copy is unavailable")
        cls.seed = load_seed(REPO_ROOT / "content" / "csv")

    def test_seed_has_locked_m10_equipment_shape(self) -> None:
        self.assertEqual(
            {table: len(rows) for table, rows in self.seed.items()},
            {
                "Equipment": 5,
                "Equipment_text": 20,
                "Equipment_tags": 0,
                "Slot_occupancy": 9,
                "Damage_profile_entries": 9,
                "Defence_profile_entries": 1,
            },
        )
        totals = {}
        for row in self.seed["Damage_profile_entries"]:
            totals[row["profile_id"]] = totals.get(row["profile_id"], 0) + row["base_pips"]
        self.assertEqual(
            totals,
            {
                "martial.maul": 4,
                "martial.dagger": 3,
                "martial.sword_1h": 3,
                "martial.shield_standard": 2,
                "martial.mace_1h": 3,
            },
        )
        self.assertIsNone(self.seed["Defence_profile_entries"][0]["rating_value"])

    def test_apply_is_exact_idempotent_and_preserves_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "candidate.grist"
            shutil.copy2(self.source, document)
            connection = sqlite3.connect(document)
            connection.row_factory = sqlite3.Row
            try:
                with connection:
                    first = apply_equipment(connection, self.seed)
                with connection:
                    second = apply_equipment(connection, self.seed)
                self.assertEqual(stable_snapshot(connection), self.seed)
                self.assertTrue(all(value == 0 for value in first["before_counts"].values()))
                self.assertEqual(first["after_counts"], second["before_counts"])
                self.assertEqual(first["bridge2_choices"], BRIDGE2_CHOICES)
                self.assertEqual(first["bridge2_value"], "barycentre_well")
                self.assertTrue(first["shield_defence_rating_remains_null"])
                self.assertTrue(first["equipment_tags_deferred"])
                self.assertEqual(
                    {
                        table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                        for table in (
                            "Chassis_profiles", "Integrity_profiles", "Integrity_states",
                            "Construction_profiles",
                        )
                    },
                    {
                        "Chassis_profiles": 5,
                        "Integrity_profiles": 1,
                        "Integrity_states": 3,
                        "Construction_profiles": 2,
                    },
                )
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Ref_rules").fetchone()[0], 143)
                metadata = column_metadata(
                    connection,
                    user_table_ref(connection, "Construction_profiles"),
                    "bridge2_mechanism",
                )
                self.assertEqual(json.loads(metadata["widgetOptions"])["choices"], BRIDGE2_CHOICES)
                equipment_ref = user_table_ref(connection, "Equipment")
                self.assertEqual(
                    column_metadata(connection, equipment_ref, "equipment_revision_id")["isFormula"],
                    1,
                )
                self.assertEqual(
                    column_metadata(connection, equipment_ref, "content_version")["isFormula"],
                    0,
                )
            finally:
                connection.close()

    def test_unresolved_reference_is_rejected_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "candidate.grist"
            shutil.copy2(self.source, document)
            seed = copy.deepcopy(self.seed)
            seed["Equipment"][0]["chassis_profile_id"] = "chassis.missing"
            connection = sqlite3.connect(document)
            connection.row_factory = sqlite3.Row
            try:
                with self.assertRaises(M10EquipmentError):
                    with connection:
                        apply_equipment(connection, seed)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Equipment").fetchone()[0], 0)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
