"""Triade v0.29.0 Grist reconciliation helpers.

This module upgrades the protected rule registry, applies the authored Standard
Shield 1/1 split, and installs derived M-C11 loadout previews.  It owns only
technical realization; all mechanics come from the governed 0.29.0 corpus.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from typing import Any

from m10_equipment import stable_snapshot as equipment_snapshot
from r7_grist import R7Error, assert_integrity, user_table_ref


class V029ReconciliationError(R7Error):
    """Raised when a v0.29.0 migration precondition or proof fails."""


M_C11_FORMULAS = {
    "base_pip_total": {
        "type": "Int",
        "sqlite_type": "INTEGER",
        "widget": "",
        "description": "Derived sum of the equipped revision's base damage-profile pips.",
        "formula": (
            "profile_id = $equipment_revision.chassis_profile.base_martial_profile_id\n"
            "entries = Damage_profile_entries.lookupRecords(profile_id=profile_id)\n"
            "return sum(int(entry.base_pips or 0) for entry in entries)"
        ),
    },
    "m_c11_state": {
        "type": "Choice",
        "sqlite_type": "TEXT",
        "widget": json.dumps({
            "widget": "TextBox",
            "choices": ["unaffected", "applied", "tie_blocked", "missing_profile"],
            "alignment": "left",
            "choiceOptions": {},
        }, separators=(",", ":")),
        "description": "Derived M-C11 application state; tie_blocked remains open under ◇M13.",
        "formula": (
            "if not $equipment_revision or $hand_assignment != 'off_hand':\n"
            "  return 'unaffected'\n"
            "if $equipment_revision.category.category_id != 'weapon':\n"
            "  return 'unaffected'\n"
            "if $equipment_revision.chassis_profile.handedness != 'one_handed':\n"
            "  return 'unaffected'\n"
            "profile_id = $equipment_revision.chassis_profile.base_martial_profile_id\n"
            "entries = Damage_profile_entries.lookupRecords(profile_id=profile_id)\n"
            "pips = [int(entry.base_pips or 0) for entry in entries]\n"
            "if not pips:\n"
            "  return 'missing_profile'\n"
            "top = max(pips)\n"
            "return 'tie_blocked' if pips.count(top) != 1 else 'applied'"
        ),
    },
    "effective_pip_total": {
        "type": "Int",
        "sqlite_type": "INTEGER",
        "widget": "",
        "description": "Derived total after M-C11; blank when the open ◇M13 tie-break is required.",
        "formula": (
            "if $m_c11_state in ('tie_blocked', 'missing_profile'):\n"
            "  return None\n"
            "return $base_pip_total - (1 if $m_c11_state == 'applied' else 0)"
        ),
    },
    "effective_damage_preview": {
        "type": "Text",
        "sqlite_type": "TEXT",
        "widget": "",
        "description": "Read-only flattened preview; canonical damage remains in child rows.",
        "formula": (
            "if $m_c11_state == 'tie_blocked':\n"
            "  return 'BLOCKED: ◇M13'\n"
            "if $m_c11_state == 'missing_profile':\n"
            "  return 'MISSING PROFILE'\n"
            "profile_id = $equipment_revision.chassis_profile.base_martial_profile_id\n"
            "entries = list(Damage_profile_entries.lookupRecords(profile_id=profile_id))\n"
            "entries.sort(key=lambda entry: entry.sort_order)\n"
            "top = max([int(entry.base_pips or 0) for entry in entries] or [0])\n"
            "spent = False\n"
            "parts = []\n"
            "for entry in entries:\n"
            "  pips = int(entry.base_pips or 0)\n"
            "  if $m_c11_state == 'applied' and not spent and pips == top:\n"
            "    pips -= 1\n"
            "    spent = True\n"
            "  if pips > 0:\n"
            "    parts.append('%s %s' % (entry.damage_type.damage_type_id, '+' * pips))\n"
            "return ', '.join(parts)"
        ),
    },
}


def upgrade_ref_rules(
    connection: sqlite3.Connection, seed: list[dict[str, Any]]
) -> dict[str, Any]:
    """Merge the current protected rule seed while preserving existing row IDs."""
    connection.row_factory = sqlite3.Row
    existing = {
        str(row["rule_id"]): dict(row)
        for row in connection.execute("SELECT * FROM Ref_rules")
    }
    seed_ids = {str(row["rule_id"]) for row in seed}
    unexpected = sorted(set(existing) - seed_ids)
    if unexpected:
        raise V029ReconciliationError(
            f"Ref_rules contains IDs absent from the 0.29.0 seed: {unexpected}"
        )
    if len(existing) not in {143, 148}:
        raise V029ReconciliationError(
            f"expected a 143-row adopted or 148-row reconciled registry, found {len(existing)}"
        )

    next_id = int(connection.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM Ref_rules").fetchone()[0])
    added: list[str] = []
    for row in seed:
        rule_id = str(row["rule_id"])
        values = (
            row["sort_order"], row["display_name"], row["description"],
            row["severity"], row["source_reference"], row["sort_order"],
        )
        if rule_id in existing:
            connection.execute(
                "UPDATE Ref_rules SET manualSort=?, display_name=?, description=?, "
                "severity=?, source_reference=?, sort_order=? WHERE rule_id=?",
                (*values, rule_id),
            )
        else:
            connection.execute(
                "INSERT INTO Ref_rules "
                "(id, manualSort, rule_id, display_name, description, severity, "
                "source_reference, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (next_id, row["sort_order"], rule_id, row["display_name"],
                 row["description"], row["severity"], row["source_reference"],
                 row["sort_order"]),
            )
            next_id += 1
            added.append(rule_id)

    rows = list(connection.execute(
        "SELECT rule_id, severity, sort_order FROM Ref_rules ORDER BY sort_order, id"
    ))
    counts = Counter(str(row["severity"]) for row in rows)
    if len(rows) != 148 or counts != Counter({"critical": 86, "high": 48, "medium": 14}):
        raise V029ReconciliationError(
            f"0.29.0 rule registry mismatch: rows={len(rows)}, severities={dict(counts)}"
        )
    if [int(row["sort_order"]) for row in rows] != list(range(1, 149)):
        raise V029ReconciliationError("0.29.0 rule order is not the exact sequence 1..148")
    return {"before_count": len(existing), "after_count": len(rows), "added_rule_ids": added}


def reconcile_equipment(
    connection: sqlite3.Connection,
    current_seed: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Apply the v0.29 Standard Shield record changes and verify exact readback."""
    connection.row_factory = sqlite3.Row
    row = connection.execute(
        "SELECT id, category FROM Equipment WHERE equipment_revision_id='shield.standard@1'"
    ).fetchone()
    if row is None:
        raise V029ReconciliationError("missing shield.standard@1")
    category = connection.execute(
        "SELECT category_id FROM Ref_categories WHERE id=?", (row["category"],)
    ).fetchone()
    if category is None or category[0] != "shield":
        raise V029ReconciliationError("shield.standard@1 is not category shield")

    shield_seed = next(
        item for item in current_seed["Equipment"]
        if item["equipment_revision_id"] == "shield.standard@1"
    )
    connection.execute(
        "UPDATE Equipment SET content_version=?, source_document_ref=?, authoring_notes=? "
        "WHERE equipment_revision_id='shield.standard@1'",
        (shield_seed["content_version"], shield_seed["source_document_ref"],
         shield_seed["authoring_notes"]),
    )
    for source in current_seed["Equipment_text"]:
        if source["equipment_revision_id"] != "shield.standard@1":
            continue
        connection.execute(
            "UPDATE Equipment_text SET text_value=? WHERE equipment_text_id=?",
            (source["text_value"], source["equipment_text_id"]),
        )
    connection.execute(
        "UPDATE Damage_profile_entries SET base_pips=1 "
        "WHERE damage_profile_entry_id='martial.shield_standard.impact'"
    )
    connection.execute(
        "UPDATE Defence_profile_entries SET rating_value=1, rating_unit='pip' "
        "WHERE defence_profile_entry_id='defence.shield_standard.physical'"
    )

    actual = equipment_snapshot(connection)
    if actual != current_seed:
        raise V029ReconciliationError("equipment readback differs from the 0.29.0 seed")
    return {
        "shield_revision": "shield.standard@1",
        "offensive_pips": 1,
        "defence_pips": 1,
        "defence_group": "physical",
        "rating_unit": "pip",
        "pool_total": 2,
    }

def _ensure_formula_column(
    connection: sqlite3.Connection,
    column_id: str,
    spec: dict[str, str],
) -> int:
    table_ref = user_table_ref(connection, "Fixture_loadouts")
    existing = connection.execute(
        "SELECT id FROM _grist_Tables_column WHERE parentId=? AND colId=?",
        (table_ref, column_id),
    ).fetchone()
    if existing is None:
        connection.execute(
            f'ALTER TABLE "Fixture_loadouts" ADD COLUMN "{column_id}" '
            f'{spec["sqlite_type"]}'
        )
        column_ref = int(connection.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM _grist_Tables_column"
        ).fetchone()[0])
        parent_pos = float(connection.execute(
            "SELECT COALESCE(MAX(parentPos), 0) + 1 FROM _grist_Tables_column WHERE parentId=?",
            (table_ref,),
        ).fetchone()[0])
        connection.execute(
            "INSERT INTO _grist_Tables_column "
            "(id,parentId,parentPos,colId,type,widgetOptions,isFormula,formula,label,description) "
            "VALUES (?,?,?,?,?,?,1,?,?,?)",
            (column_ref, table_ref, parent_pos, column_id, spec["type"], spec["widget"],
             spec["formula"], column_id, spec["description"]),
        )
    else:
        column_ref = int(existing[0])
        connection.execute(
            "UPDATE _grist_Tables_column SET type=?, widgetOptions=?, isFormula=1, "
            "formula=?, description=? WHERE id=?",
            (spec["type"], spec["widget"], spec["formula"], spec["description"], column_ref),
        )

    sections = [
        int(row[0]) for row in connection.execute(
            "SELECT id FROM _grist_Views_section WHERE tableRef=?", (table_ref,)
        )
    ]
    for section in sections:
        present = connection.execute(
            "SELECT 1 FROM _grist_Views_section_field WHERE parentId=? AND colRef=?",
            (section, column_ref),
        ).fetchone()
        if present is not None:
            continue
        field_id = int(connection.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM _grist_Views_section_field"
        ).fetchone()[0])
        field_pos = float(connection.execute(
            "SELECT COALESCE(MAX(parentPos), 0) + 1 FROM _grist_Views_section_field "
            "WHERE parentId=?", (section,),
        ).fetchone()[0])
        connection.execute(
            "INSERT INTO _grist_Views_section_field "
            "(id,parentId,parentPos,colRef,width) VALUES (?,?,?,?,?)",
            (field_id, section, field_pos, column_ref, 140),
        )
    return column_ref


def _stable_reference_map(
    connection: sqlite3.Connection, table: str, stable_field: str
) -> dict[int, str]:
    return {
        int(row["id"]): str(row[stable_field])
        for row in connection.execute(f'SELECT id, "{stable_field}" FROM "{table}"')
    }


def derive_loadout_previews(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Calculate deterministic cached values for the four Grist formula columns."""
    equipment_ids = _stable_reference_map(connection, "Equipment", "equipment_revision_id")
    category_ids = _stable_reference_map(connection, "Ref_categories", "category_id")
    chassis_ids = _stable_reference_map(connection, "Chassis_profiles", "chassis_profile_id")
    damage_type_ids = _stable_reference_map(connection, "Ref_damage_types", "damage_type_id")
    equipment = {
        int(row["id"]): dict(row)
        for row in connection.execute(
            "SELECT id, equipment_revision_id, category, chassis_profile FROM Equipment"
        )
    }
    chassis = {
        int(row["id"]): dict(row)
        for row in connection.execute(
            "SELECT id, handedness, base_martial_profile_id FROM Chassis_profiles"
        )
    }
    profiles: dict[str, list[dict[str, Any]]] = {}
    for row in connection.execute(
        "SELECT damage_type, base_pips, profile_id, sort_order "
        "FROM Damage_profile_entries ORDER BY sort_order, id"
    ):
        profiles.setdefault(str(row["profile_id"]), []).append(dict(row))

    output: list[dict[str, Any]] = []
    for loadout in connection.execute(
        "SELECT id, fixture_loadout_id, equipment_revision, hand_assignment "
        "FROM Fixture_loadouts ORDER BY manualSort, id"
    ):
        eq = equipment[int(loadout["equipment_revision"])]
        ch = chassis[int(eq["chassis_profile"])]
        entries = profiles.get(str(ch["base_martial_profile_id"]), [])
        pips = [int(entry["base_pips"] or 0) for entry in entries]
        base_total = sum(pips)
        state = "unaffected"
        if (
            loadout["hand_assignment"] == "off_hand"
            and category_ids[int(eq["category"])] == "weapon"
            and ch["handedness"] == "one_handed"
        ):
            if not pips:
                state = "missing_profile"
            elif pips.count(max(pips)) != 1:
                state = "tie_blocked"
            else:
                state = "applied"

        effective_total = None if state in {"tie_blocked", "missing_profile"} else (
            base_total - (1 if state == "applied" else 0)
        )
        if state == "tie_blocked":
            preview = "BLOCKED: ◇M13"
        elif state == "missing_profile":
            preview = "MISSING PROFILE"
        else:
            top = max(pips or [0])
            spent = False
            parts: list[str] = []
            for entry in entries:
                value = int(entry["base_pips"] or 0)
                if state == "applied" and not spent and value == top:
                    value -= 1
                    spent = True
                if value > 0:
                    parts.append(f'{damage_type_ids[int(entry["damage_type"])]} {"+" * value}')
            preview = ", ".join(parts)
        output.append({
            "id": int(loadout["id"]),
            "fixture_loadout_id": str(loadout["fixture_loadout_id"]),
            "equipment_revision_id": equipment_ids[int(loadout["equipment_revision"])],
            "base_pip_total": base_total,
            "m_c11_state": state,
            "effective_pip_total": effective_total,
            "effective_damage_preview": preview,
        })
    return output


def install_m_c11_previews(connection: sqlite3.Connection) -> dict[str, Any]:
    """Install formula metadata, cache deterministic previews, and verify M-C11."""
    connection.row_factory = sqlite3.Row
    for column_id, spec in M_C11_FORMULAS.items():
        _ensure_formula_column(connection, column_id, spec)
    rows = derive_loadout_previews(connection)
    for row in rows:
        connection.execute(
            "UPDATE Fixture_loadouts SET base_pip_total=?, m_c11_state=?, "
            "effective_pip_total=?, effective_damage_preview=? WHERE id=?",
            (row["base_pip_total"], row["m_c11_state"], row["effective_pip_total"],
             row["effective_damage_preview"], row["id"]),
        )
    off_hand = next(
        row for row in rows
        if row["fixture_loadout_id"] == "fixture.loadout.technical.dagger_off"
    )
    if (
        off_hand["m_c11_state"] != "applied"
        or off_hand["base_pip_total"] != 3
        or off_hand["effective_pip_total"] != 2
        or off_hand["effective_damage_preview"] != "pierce +, slash +"
    ):
        raise V029ReconciliationError(f"Technical off-hand fixture failed M-C11: {off_hand}")
    if any(row["m_c11_state"] == "tie_blocked" for row in rows):
        raise V029ReconciliationError("a current M10 fixture unexpectedly requires ◇M13")
    assert_integrity(connection)
    return {
        "formula_columns": list(M_C11_FORMULAS),
        "loadout_count": len(rows),
        "applied_count": sum(row["m_c11_state"] == "applied" for row in rows),
        "tie_blocked_count": sum(row["m_c11_state"] == "tie_blocked" for row in rows),
        "technical_off_hand": off_hand,
        "rows": rows,
    }
