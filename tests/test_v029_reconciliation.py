from __future__ import annotations

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

from m10_equipment import load_seed as load_equipment_seed  # noqa: E402
from m10_faculties_fixtures import (  # noqa: E402
    apply_faculties_fixtures,
    load_seed as load_fixture_seed,
)
from r7_grist import column_metadata, load_seed as load_rule_seed, user_table_ref  # noqa: E402
from v029_reconciliation import (  # noqa: E402
    V029ReconciliationError,
    install_m_c11_previews,
    reconcile_equipment,
    upgrade_ref_rules,
)


class V029ReconciliationTests(unittest.TestCase):
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
        seed_dir = REPO_ROOT / "content" / "csv"
        cls.rules = load_rule_seed(seed_dir / "ref_rules.csv")
        cls.equipment = load_equipment_seed(seed_dir)
        cls.fixtures = load_fixture_seed(seed_dir)

    def migrate(self, connection: sqlite3.Connection) -> dict[str, object]:
        rule = upgrade_ref_rules(connection, self.rules)
        equipment = reconcile_equipment(connection, self.equipment)
        fixture = apply_faculties_fixtures(connection, self.fixtures)
        preview = install_m_c11_previews(connection)
        return {"rule": rule, "equipment": equipment, "fixture": fixture, "preview": preview}

    def test_full_migration_is_idempotent_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "candidate.grist"
            shutil.copy2(self.source, document)
            connection = sqlite3.connect(document)
            connection.row_factory = sqlite3.Row
            try:
                with connection:
                    first = self.migrate(connection)
                with connection:
                    second = self.migrate(connection)
                self.assertEqual(first["rule"]["after_count"], 148)
                self.assertEqual(second["rule"]["after_count"], 148)
                self.assertEqual(first["rule"]["added_rule_ids"], [
                    "T-C14", "M-C9", "M-C10", "M-C11", "E-C7"
                ])
                self.assertEqual(second["rule"]["added_rule_ids"], [])
                self.assertEqual(first["equipment"]["pool_total"], 2)
                self.assertEqual(first["fixture"]["coverage_summary"], {"gap": 17, "proof": 12})
                self.assertEqual(first["preview"]["applied_count"], 1)
                self.assertEqual(first["preview"]["tie_blocked_count"], 0)
                off_hand = first["preview"]["technical_off_hand"]
                self.assertEqual(off_hand["base_pip_total"], 3)
                self.assertEqual(off_hand["effective_pip_total"], 2)
                self.assertEqual(off_hand["effective_damage_preview"], "pierce +, slash +")
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Ref_rules").fetchone()[0], 148)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Faculties").fetchone()[0], 5)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM Fixture_coverage").fetchone()[0], 29)
                loadout_ref = user_table_ref(connection, "Fixture_loadouts")
                for column in (
                    "base_pip_total", "m_c11_state", "effective_pip_total",
                    "effective_damage_preview",
                ):
                    self.assertEqual(column_metadata(connection, loadout_ref, column)["isFormula"], 1)
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            finally:
                connection.close()

    def test_tied_highest_off_hand_profile_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "candidate.grist"
            shutil.copy2(self.source, document)
            connection = sqlite3.connect(document)
            connection.row_factory = sqlite3.Row
            try:
                with connection:
                    self.migrate(connection)
                with self.assertRaises(V029ReconciliationError):
                    with connection:
                        connection.execute(
                            "UPDATE Damage_profile_entries SET base_pips=2 "
                            "WHERE damage_profile_entry_id='martial.dagger.slash'"
                        )
                        install_m_c11_previews(connection)
                value = connection.execute(
                    "SELECT base_pips FROM Damage_profile_entries "
                    "WHERE damage_profile_entry_id='martial.dagger.slash'"
                ).fetchone()[0]
                self.assertEqual(value, 1)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
