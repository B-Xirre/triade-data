from __future__ import annotations

import copy
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from m10_faculties_fixtures import (  # noqa: E402
    M10FacultyFixtureError,
    apply_faculties_fixtures,
    load_seed,
    stable_snapshot,
)
from m10_equipment import load_seed as load_equipment_seed  # noqa: E402
from r7_grist import column_metadata, load_seed as load_rule_seed, user_table_ref  # noqa: E402
from v029_reconciliation import reconcile_equipment, upgrade_ref_rules  # noqa: E402


class M10FacultyFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configured = os.environ.get("TRIADE_M10_ADOPTED_SOURCE")
        cls.source = (
            Path(configured)
            if configured
            else REPO_ROOT.parents[1]
            / "deliverables"
            / "Triade - Equipment Authoring-M10-equipment.grist"
        )
        if not cls.source.exists():
            raise unittest.SkipTest("adopted M10 equipment .grist working copy is unavailable")
        cls.seed = load_seed(REPO_ROOT / "content" / "csv")
        cls.equipment_seed = load_equipment_seed(REPO_ROOT / "content" / "csv")
        cls.rule_seed = load_rule_seed(REPO_ROOT / "content" / "csv" / "ref_rules.csv")

    def prepare_v029_baseline(self, connection: sqlite3.Connection) -> None:
        upgrade_ref_rules(connection, self.rule_seed)
        reconcile_equipment(connection, self.equipment_seed)

    def test_seed_has_source_owned_shape_and_explicit_holds(self) -> None:
        self.assertEqual(
            {table: len(rows) for table, rows in self.seed.items()},
            {
                "Faculties": 5,
                "Faculty_profiles": 0,
                "Fixture_builds": 5,
                "Fixture_stat_weights": 45,
                "Fixture_loadouts": 7,
                "Fixture_encounters": 5,
                "Fixture_coverage": 29,
            },
        )
        self.assertTrue(all(row["base_damage_profile_id"] == "" for row in self.seed["Faculties"]))
        self.assertEqual(
            {row["coverage_kind"] for row in self.seed["Fixture_coverage"]},
            {"proof", "gap"},
        )
        self.assertEqual(
            sum(row["coverage_kind"] == "proof" for row in self.seed["Fixture_coverage"]),
            12,
        )

    def test_apply_is_exact_idempotent_and_preserves_adopted_layers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "candidate.grist"
            shutil.copy2(self.source, document)
            connection = sqlite3.connect(document)
            connection.row_factory = sqlite3.Row
            try:
                with connection:
                    self.prepare_v029_baseline(connection)
                with connection:
                    first = apply_faculties_fixtures(connection, self.seed)
                with connection:
                    second = apply_faculties_fixtures(connection, self.seed)
                self.assertEqual(stable_snapshot(connection), self.seed)
                self.assertTrue(all(value == 0 for value in first["before_counts"].values()))
                self.assertEqual(first["after_counts"], second["before_counts"])
                self.assertEqual(first["coverage_summary"], {"gap": 17, "proof": 12})
                self.assertEqual(
                    first["free_hand_by_build"],
                    {
                        "fixture.build.controller": False,
                        "fixture.build.striker": False,
                        "fixture.build.technical": False,
                        "fixture.build.trickster": True,
                        "fixture.build.war_priest": True,
                    },
                )
                self.assertTrue(first["faculty_profiles_deferred"])
                self.assertTrue(first["fixture_enemy_tables_deferred"])
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Equipment").fetchone()[0], 5)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Ref_rules").fetchone()[0], 148)
                faculty_ref = user_table_ref(connection, "Faculties")
                self.assertEqual(
                    column_metadata(connection, faculty_ref, "faculty_revision_id")["isFormula"],
                    1,
                )
                self.assertEqual(
                    column_metadata(connection, faculty_ref, "content_version")["isFormula"],
                    0,
                )
                build_ref = user_table_ref(connection, "Fixture_builds")
                self.assertEqual(column_metadata(connection, build_ref, "floor_sum")["isFormula"], 1)
                coverage_ref = user_table_ref(connection, "Fixture_coverage")
                metadata = column_metadata(connection, coverage_ref, "rule_id")
                self.assertEqual(metadata["type"], "Ref:Ref_rules")
                self.assertEqual(metadata["isFormula"], 0)
                self.assertEqual(json.loads(metadata["widgetOptions"] or "{}"), {})
            finally:
                connection.close()

    def test_unresolved_reference_is_rejected_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "candidate.grist"
            shutil.copy2(self.source, document)
            seed = copy.deepcopy(self.seed)
            seed["Fixture_loadouts"][0]["equipment_revision_id"] = "weapon.missing@1"
            connection = sqlite3.connect(document)
            connection.row_factory = sqlite3.Row
            try:
                with connection:
                    self.prepare_v029_baseline(connection)
                with self.assertRaises(M10FacultyFixtureError):
                    with connection:
                        apply_faculties_fixtures(connection, seed)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Faculties").fetchone()[0], 0)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Fixture_builds").fetchone()[0], 0)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
