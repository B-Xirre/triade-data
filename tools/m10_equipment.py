"""M10 equipment seed validation, Grist migration, and stable-ID exports."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from r7_grist import R7Error, assert_integrity, column_metadata, user_table_ref


class M10EquipmentError(R7Error):
    """Raised when an M10 equipment precondition or proof gate fails."""


TABLE_FILES = {
    "Equipment": "equipment.csv",
    "Equipment_text": "equipment_text.csv",
    "Equipment_tags": "equipment_tags.csv",
    "Slot_occupancy": "slot_occupancy.csv",
    "Damage_profile_entries": "damage_profile_entries.csv",
    "Defence_profile_entries": "defence_profile_entries.csv",
}

HEADERS = {
    "Equipment": (
        "equipment_id", "revision_number", "equipment_revision_id",
        "schema_version", "content_version", "lifecycle_status_id",
        "design_status_id", "category_id", "chassis_profile_id",
        "construction_profile_id", "integrity_profile_id", "demand_tier_id",
        "display_name_key", "short_name_key", "description_key", "flavour_key",
        "accessibility_description_key", "is_doctrinal", "is_transgressive",
        "is_unique", "is_secret", "is_relic", "introduced_in_version",
        "deprecated_in_version", "source_document_ref", "decision_origin",
        "authoring_notes", "content_hash", "approved_by", "approved_at",
        "sort_order",
    ),
    "Equipment_text": (
        "equipment_text_id", "equipment_revision_id", "locale", "text_key",
        "text_kind", "text_value", "revision", "sort_order",
    ),
    "Equipment_tags": (
        "equipment_tag_id", "equipment_revision_id", "tag_id", "sort_order",
    ),
    "Slot_occupancy": (
        "occupancy_id", "equipment_revision_id", "slot_id", "occupancy_role",
        "hand_group", "occupancy_units", "delivery_hook_id",
        "supports_combo_source", "authoring_notes", "sort_order",
    ),
    "Damage_profile_entries": (
        "damage_profile_entry_id", "profile_id", "damage_type_id", "base_pips",
        "pip_budget_group", "primary_status_hook_id", "secondary_status_hook_id",
        "requirement_eligible", "source_layer", "sort_order",
    ),
    "Defence_profile_entries": (
        "defence_profile_entry_id", "defence_profile_id", "scope_kind",
        "damage_group_id", "damage_type_id", "rating_value", "rating_unit",
        "exception_polarity", "condition_expression_id", "narration_fragment_id",
        "sort_order",
    ),
}

EXPECTED_COUNTS = {
    "Equipment": 5,
    "Equipment_text": 20,
    "Equipment_tags": 0,
    "Slot_occupancy": 9,
    "Damage_profile_entries": 9,
    "Defence_profile_entries": 1,
}

STABLE_ID_FIELD = {
    "Equipment": "equipment_revision_id",
    "Equipment_text": "equipment_text_id",
    "Equipment_tags": "equipment_tag_id",
    "Slot_occupancy": "occupancy_id",
    "Damage_profile_entries": "damage_profile_entry_id",
    "Defence_profile_entries": "defence_profile_entry_id",
}

INT_FIELDS = {
    "revision_number", "revision", "sort_order", "occupancy_units", "base_pips",
    "rating_value",
}
BOOL_FIELDS = {
    "is_doctrinal", "is_transgressive", "is_unique", "is_secret", "is_relic",
    "supports_combo_source", "requirement_eligible",
}

BRIDGE2_CHOICES = [
    "edm_damping", "home_well_strengthening", "barycentre_well", "none"
]


def _optional_int(value: str, field: str, row_number: int) -> int | None:
    if value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise M10EquipmentError(
            f"row {row_number} has invalid integer {field}={value!r}"
        ) from exc


def _bool(value: str, field: str, row_number: int) -> bool:
    lowered = value.lower()
    if lowered not in {"true", "false"}:
        raise M10EquipmentError(
            f"row {row_number} has invalid boolean {field}={value!r}"
        )
    return lowered == "true"


def load_seed(seed_dir: Path) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for table, file_name in TABLE_FILES.items():
        with (seed_dir / file_name).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != HEADERS[table]:
                raise M10EquipmentError(
                    f"unexpected columns for {file_name}: {reader.fieldnames}"
                )
            rows: list[dict[str, Any]] = []
            for row_number, source in enumerate(reader, 2):
                row: dict[str, Any] = dict(source)
                for field in INT_FIELDS.intersection(row):
                    row[field] = _optional_int(row[field], field, row_number)
                for field in BOOL_FIELDS.intersection(row):
                    row[field] = _bool(row[field], field, row_number)
                rows.append(row)
        output[table] = rows
    validate_seed(output)
    return output


def validate_seed(seed: dict[str, list[dict[str, Any]]]) -> None:
    for table, expected in EXPECTED_COUNTS.items():
        rows = seed.get(table, [])
        if len(rows) != expected:
            raise M10EquipmentError(f"{table} must contain {expected} rows")
        field = STABLE_ID_FIELD[table]
        ids = [str(row[field]) for row in rows]
        duplicates = [key for key, count in Counter(ids).items() if count > 1]
        if any(not value for value in ids) or duplicates:
            raise M10EquipmentError(f"{table} stable IDs must be unique and non-empty")
        orders = [row["sort_order"] for row in rows]
        if any(value is None for value in orders) or orders != sorted(orders):
            raise M10EquipmentError(f"{table} sort_order must be populated and ordered")

    equipment = {row["equipment_revision_id"]: row for row in seed["Equipment"]}
    expected_revisions = {
        "weapon.maul@1", "weapon.dagger@1", "weapon.sword_1h@1",
        "shield.standard@1", "weapon.mace_1h@1",
    }
    if set(equipment) != expected_revisions:
        raise M10EquipmentError("equipment revision set differs from the locked M10 set")
    for revision_id, row in equipment.items():
        if revision_id != f'{row["equipment_id"]}@{row["revision_number"]}':
            raise M10EquipmentError(f"invalid revision identity {revision_id}")
        expected_version = "0.29.0" if revision_id == "shield.standard@1" else "0.25.0"
        if row["content_version"] != expected_version:
            raise M10EquipmentError(
                f"{revision_id} is not aligned to its source version {expected_version}"
            )
        if row["lifecycle_status_id"] != "candidate" or row["design_status_id"] != "fixture":
            raise M10EquipmentError(f"{revision_id} must be a candidate fixture")
        expected_category = "shield" if revision_id == "shield.standard@1" else "weapon"
        if row["category_id"] != expected_category:
            raise M10EquipmentError(f"{revision_id} has the wrong category")

    texts: dict[str, set[str]] = defaultdict(set)
    for row in seed["Equipment_text"]:
        if row["equipment_revision_id"] not in equipment or row["locale"] != "en-GB":
            raise M10EquipmentError("equipment text has an invalid parent or locale")
        texts[row["equipment_revision_id"]].add(row["text_kind"])
    required_text = {"display_name", "short_name", "description", "accessibility"}
    if any(texts[revision] != required_text for revision in equipment):
        raise M10EquipmentError("each equipment revision must have four reference-locale texts")

    profiles: dict[str, dict[str, int]] = defaultdict(dict)
    for row in seed["Damage_profile_entries"]:
        profiles[row["profile_id"]][row["damage_type_id"]] = row["base_pips"]
        if not row["requirement_eligible"] or row["source_layer"] != "chassis":
            raise M10EquipmentError("M10 base damage rows must be eligible chassis rows")
    expected_profiles = {
        "martial.maul": {"impact": 3, "shatter": 1},
        "martial.dagger": {"pierce": 2, "slash": 1},
        "martial.sword_1h": {"slash": 2, "pierce": 1},
        "martial.shield_standard": {"impact": 1},
        "martial.mace_1h": {"impact": 2, "shatter": 1},
    }
    if dict(profiles) != expected_profiles:
        raise M10EquipmentError("damage profiles differ from P·10.3 / M·2A.9")

    primary_units: dict[str, int] = defaultdict(int)
    active_hooks: dict[str, int] = defaultdict(int)
    for row in seed["Slot_occupancy"]:
        if row["equipment_revision_id"] not in equipment:
            raise M10EquipmentError("slot occupancy references an unknown revision")
        if row["occupancy_role"] in {"primary", "required"}:
            primary_units[row["equipment_revision_id"]] += row["occupancy_units"]
            if row["delivery_hook_id"] != "none":
                active_hooks[row["equipment_revision_id"]] += 1
    if primary_units != {
        "weapon.maul@1": 2, "weapon.dagger@1": 1, "weapon.sword_1h@1": 1,
        "shield.standard@1": 1, "weapon.mace_1h@1": 1,
    } or any(active_hooks[revision] != 1 for revision in equipment):
        raise M10EquipmentError("hand occupancy or delivery-hook count is incorrect")

    defence = seed["Defence_profile_entries"][0]
    if (
        defence["defence_profile_id"] != "defence.shield_standard"
        or defence["scope_kind"] != "group"
        or defence["damage_group_id"] != "physical"
        or defence["rating_value"] != 1
        or defence["rating_unit"] != "pip"
    ):
        raise M10EquipmentError("Standard Shield 1/1 pip split is not source-faithful")

    scalar_fields = {
        "equipment_id", "equipment_revision_id", "lifecycle_status_id",
        "design_status_id", "category_id", "chassis_profile_id",
        "construction_profile_id", "integrity_profile_id", "demand_tier_id",
        "locale", "text_key", "text_kind", "slot_id", "occupancy_role",
        "hand_group", "delivery_hook_id", "profile_id", "damage_type_id",
        "pip_budget_group", "source_layer", "defence_profile_id", "scope_kind",
        "damage_group_id", "exception_polarity",
    }
    for rows in seed.values():
        for row in rows:
            for field in scalar_fields.intersection(row):
                value = row[field]
                if isinstance(value, str) and any(token in value for token in (";", "|", ",")):
                    raise M10EquipmentError(f"scalar field {field} contains a delimited value")


def _id_map(connection: sqlite3.Connection, table: str, field: str) -> dict[str, int]:
    return {
        str(row[field]): int(row["id"])
        for row in connection.execute(f'SELECT id, "{field}" FROM "{table}"')
    }


def _reverse_id_map(connection: sqlite3.Connection, table: str, field: str) -> dict[int, str]:
    return {value: key for key, value in _id_map(connection, table, field).items()}


def _stable_rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    order_column = "manualSort" if table == "Equipment" else "sort_order"
    rows = [dict(row) for row in connection.execute(
        f'SELECT * FROM "{table}" ORDER BY "{order_column}", id'
    )]
    maps = {
        "equipment": _reverse_id_map(connection, "Equipment", "equipment_revision_id"),
        "lifecycle": _reverse_id_map(connection, "Ref_lifecycle_status", "lifecycle_status_id"),
        "design": _reverse_id_map(connection, "Ref_design_status", "design_status_id"),
        "category": _reverse_id_map(connection, "Ref_categories", "category_id"),
        "demand": _reverse_id_map(connection, "Ref_demand_tiers", "demand_tier_id"),
        "chassis": _reverse_id_map(connection, "Chassis_profiles", "chassis_profile_id"),
        "construction": _reverse_id_map(connection, "Construction_profiles", "construction_profile_id"),
        "integrity": _reverse_id_map(connection, "Integrity_profiles", "integrity_profile_id"),
        "tag": _reverse_id_map(connection, "Ref_tags", "tag_id"),
        "slot": _reverse_id_map(connection, "Ref_slots", "slot_id"),
        "hook": _reverse_id_map(connection, "Ref_hooks", "hook_id"),
        "damage_type": _reverse_id_map(connection, "Ref_damage_types", "damage_type_id"),
        "damage_group": _reverse_id_map(connection, "Ref_damage_groups", "damage_group_id"),
    }
    output: list[dict[str, Any]] = []
    for source in rows:
        if table == "Equipment":
            row = {
                "equipment_id": source["equipment_id"],
                "revision_number": source["revision_number"],
                "equipment_revision_id": source["equipment_revision_id"],
                "schema_version": source["schema_version"] or "",
                "content_version": source["content_version"],
                "lifecycle_status_id": maps["lifecycle"].get(source["lifecycle_status"], ""),
                "design_status_id": maps["design"].get(source["design_status"], ""),
                "category_id": maps["category"].get(source["category"], ""),
                "chassis_profile_id": maps["chassis"].get(source["chassis_profile"], ""),
                "construction_profile_id": maps["construction"].get(source["construction_profile"], ""),
                "integrity_profile_id": maps["integrity"].get(source["integrity_profile"], ""),
                "demand_tier_id": maps["demand"].get(source["demand_tier"], ""),
            }
            for field in HEADERS[table][12:]:
                if field == "sort_order":
                    row[field] = source["manualSort"]
                elif field in BOOL_FIELDS:
                    row[field] = bool(source[field])
                else:
                    row[field] = source[field] if source[field] is not None else ""
        elif table == "Equipment_text":
            row = {
                "equipment_text_id": source["equipment_text_id"],
                "equipment_revision_id": maps["equipment"].get(source["equipment_revision"], ""),
                **{field: source[field] for field in HEADERS[table][2:]},
            }
        elif table == "Equipment_tags":
            row = {
                "equipment_tag_id": source["equipment_tag_id"],
                "equipment_revision_id": maps["equipment"].get(source["equipment_revision"], ""),
                "tag_id": maps["tag"].get(source["tag"], ""),
                "sort_order": source["sort_order"],
            }
        elif table == "Slot_occupancy":
            row = {
                "occupancy_id": source["occupancy_id"],
                "equipment_revision_id": maps["equipment"].get(source["equipment_revision"], ""),
                "slot_id": maps["slot"].get(source["slot"], ""),
                "occupancy_role": source["occupancy_role"],
                "hand_group": source["hand_group"],
                "occupancy_units": source["occupancy_units"],
                "delivery_hook_id": maps["hook"].get(source["delivery_hook"], ""),
                "supports_combo_source": bool(source["supports_combo_source"]),
                "authoring_notes": source["authoring_notes"] or "",
                "sort_order": source["sort_order"],
            }
        elif table == "Damage_profile_entries":
            row = {
                "damage_profile_entry_id": source["damage_profile_entry_id"],
                "profile_id": source["profile_id"],
                "damage_type_id": maps["damage_type"].get(source["damage_type"], ""),
                "base_pips": source["base_pips"],
                "pip_budget_group": source["pip_budget_group"],
                "primary_status_hook_id": source["primary_status_hook_id"] or "",
                "secondary_status_hook_id": source["secondary_status_hook_id"] or "",
                "requirement_eligible": bool(source["requirement_eligible"]),
                "source_layer": source["source_layer"],
                "sort_order": source["sort_order"],
            }
        else:
            row = {
                "defence_profile_entry_id": source["defence_profile_entry_id"],
                "defence_profile_id": source["defence_profile_id"],
                "scope_kind": source["scope_kind"],
                "damage_group_id": maps["damage_group"].get(source["damage_group"], ""),
                "damage_type_id": maps["damage_type"].get(source["damage_type"], ""),
                "rating_value": source["rating_value"],
                "rating_unit": source["rating_unit"] or "",
                "exception_polarity": source["exception_polarity"],
                "condition_expression_id": source["condition_expression_id"] or "",
                "narration_fragment_id": source["narration_fragment_id"] or "",
                "sort_order": source["sort_order"],
            }
        output.append(row)
    return output


def stable_snapshot(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    return {table: _stable_rows(connection, table) for table in TABLE_FILES}


def equipment_schema_snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for table in (*TABLE_FILES, "Construction_profiles"):
        table_ref = user_table_ref(connection, table)
        output[table] = {
            "columns": [
                {
                    key: row[key]
                    for key in (
                        "colId", "type", "isFormula", "formula", "displayCol",
                        "visibleCol", "widgetOptions",
                    )
                }
                for row in connection.execute(
                    "SELECT * FROM _grist_Tables_column "
                    "WHERE parentId=? ORDER BY parentPos, id",
                    (table_ref,),
                )
            ],
            "sqlite_schema": [
                {
                    "name": row[1], "type": row[2], "default": row[4],
                    "primary_key": bool(row[5]),
                }
                for row in connection.execute(f'PRAGMA table_info("{table}")')
            ],
        }
    return output


def _make_editable(connection: sqlite3.Connection, table: str) -> None:
    aliases = {
        "Equipment": {
            "lifecycle_status_id": "lifecycle_status", "design_status_id": "design_status",
            "category_id": "category", "demand_tier_id": "demand_tier",
            "chassis_profile_id": "chassis_profile",
            "construction_profile_id": "construction_profile",
            "integrity_profile_id": "integrity_profile",
        },
        "Equipment_text": {"equipment_revision_id": "equipment_revision"},
        "Equipment_tags": {
            "equipment_revision_id": "equipment_revision", "tag_id": "tag"
        },
        "Slot_occupancy": {
            "equipment_revision_id": "equipment_revision", "slot_id": "slot",
            "delivery_hook_id": "delivery_hook",
        },
        "Damage_profile_entries": {"damage_type_id": "damage_type"},
        "Defence_profile_entries": {
            "damage_group_id": "damage_group", "damage_type_id": "damage_type"
        },
    }[table]
    columns = {
        aliases.get(field, field) for field in HEADERS[table]
        if not (
            table == "Equipment"
            and field in {"equipment_revision_id", "sort_order"}
        )
    }
    table_ref = user_table_ref(connection, table)
    for column in columns:
        column_metadata(connection, table_ref, column)
    placeholders = ",".join("?" for _ in columns)
    connection.execute(
        f"UPDATE _grist_Tables_column SET isFormula=0, formula='' "
        f"WHERE parentId=? AND colId IN ({placeholders})",
        (table_ref, *sorted(columns)),
    )


def _insert_rows(
    connection: sqlite3.Connection,
    table: str,
    rows: list[dict[str, Any]],
    transform: Callable[[dict[str, Any]], dict[str, Any]],
) -> None:
    next_id = int(connection.execute(
        f'SELECT COALESCE(MAX(id), 0) + 1 FROM "{table}"'
    ).fetchone()[0])
    for offset, source in enumerate(rows):
        row = {"id": next_id + offset, "manualSort": source["sort_order"], **transform(source)}
        fields = list(row)
        connection.execute(
            f'INSERT INTO "{table}" ({", ".join(fields)}) '
            f'VALUES ({", ".join("?" for _ in fields)})',
            [row[field] for field in fields],
        )


def _migrate_v025_dependencies(connection: sqlite3.Connection) -> None:
    counts = {
        "Chassis_profiles": 5, "Integrity_profiles": 1,
        "Integrity_states": 3, "Construction_profiles": 2,
    }
    for table, expected in counts.items():
        actual = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        if actual != expected:
            raise M10EquipmentError(f"{table} expected {expected} adopted rows, found {actual}")
    shield = connection.execute(
        "SELECT * FROM Construction_profiles WHERE construction_profile_id=?",
        ("construction.shield_standard",),
    ).fetchone()
    if shield is None or shield["bridge2_mechanism"] not in {"", "barycentre_well"}:
        raise M10EquipmentError("Standard Shield Bridge-2 state is not migratable")
    connection.execute(
        "UPDATE Construction_profiles SET bridge2_mechanism=?, authoring_notes=? "
        "WHERE construction_profile_id=?",
        (
            "barycentre_well",
            "Source: M·2A.7 and M·2A.11. Medium uses the barycentre well; remaining unresolved fields stay blank.",
            "construction.shield_standard",
        ),
    )
    connection.execute(
        "UPDATE Integrity_states SET authoring_notes=? WHERE integrity_state_row_id=?",
        (
            "Broken Guard suppresses Discipline Opening-creation. Centralised in M·2A.6 at 0.23.0.",
            "integrity.shield_standard.broken_guard",
        ),
    )
    table_ref = user_table_ref(connection, "Construction_profiles")
    column = column_metadata(connection, table_ref, "bridge2_mechanism")
    options = json.loads(column["widgetOptions"] or "{}")
    options["choices"] = BRIDGE2_CHOICES
    connection.execute(
        "UPDATE _grist_Tables_column SET widgetOptions=? WHERE id=?",
        (json.dumps(options, separators=(",", ":")), column["id"]),
    )


def apply_equipment(
    connection: sqlite3.Connection,
    seed: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    connection.row_factory = sqlite3.Row
    validate_seed(seed)
    _migrate_v025_dependencies(connection)
    if connection.execute("SELECT COUNT(*) FROM Ref_tags").fetchone()[0] != 0:
        raise M10EquipmentError("tag seed expects the protected Ref_tags registry to remain empty")
    before = stable_snapshot(connection)
    for table, rows in before.items():
        if rows and rows != seed[table]:
            raise M10EquipmentError(f"{table} is non-empty and differs from the governed seed")
    for table in TABLE_FILES:
        _make_editable(connection, table)

    ids = {
        "lifecycle": _id_map(connection, "Ref_lifecycle_status", "lifecycle_status_id"),
        "design": _id_map(connection, "Ref_design_status", "design_status_id"),
        "category": _id_map(connection, "Ref_categories", "category_id"),
        "demand": _id_map(connection, "Ref_demand_tiers", "demand_tier_id"),
        "chassis": _id_map(connection, "Chassis_profiles", "chassis_profile_id"),
        "construction": _id_map(connection, "Construction_profiles", "construction_profile_id"),
        "integrity": _id_map(connection, "Integrity_profiles", "integrity_profile_id"),
        "slot": _id_map(connection, "Ref_slots", "slot_id"),
        "hook": _id_map(connection, "Ref_hooks", "hook_id"),
        "damage_type": _id_map(connection, "Ref_damage_types", "damage_type_id"),
        "damage_group": _id_map(connection, "Ref_damage_groups", "damage_group_id"),
    }

    for row in seed["Equipment"]:
        for field, mapping in (
            ("lifecycle_status_id", "lifecycle"), ("design_status_id", "design"),
            ("category_id", "category"), ("demand_tier_id", "demand"),
            ("chassis_profile_id", "chassis"),
            ("construction_profile_id", "construction"),
            ("integrity_profile_id", "integrity"),
        ):
            stable = row[field]
            if stable and stable not in ids[mapping]:
                raise M10EquipmentError(f"unresolved {field}={stable!r}")
    for row in seed["Slot_occupancy"]:
        if row["slot_id"] not in ids["slot"] or row["delivery_hook_id"] not in ids["hook"]:
            raise M10EquipmentError(f"unresolved slot/hook in {row['occupancy_id']}")
    for row in seed["Damage_profile_entries"]:
        if row["damage_type_id"] not in ids["damage_type"]:
            raise M10EquipmentError(
                f"unresolved damage_type_id={row['damage_type_id']!r}"
            )
    for row in seed["Defence_profile_entries"]:
        if row["damage_group_id"] not in ids["damage_group"]:
            raise M10EquipmentError(
                f"unresolved damage_group_id={row['damage_group_id']!r}"
            )
        if row["damage_type_id"] and row["damage_type_id"] not in ids["damage_type"]:
            raise M10EquipmentError(
                f"unresolved damage_type_id={row['damage_type_id']!r}"
            )

    if not before["Equipment"]:
        def equipment_row(source: dict[str, Any]) -> dict[str, Any]:
            row = dict(source)
            row.pop("sort_order")
            for source_field, target_field, mapping, helper in (
                ("lifecycle_status_id", "lifecycle_status", "lifecycle", "gristHelper_Display"),
                ("design_status_id", "design_status", "design", "gristHelper_Display2"),
                ("category_id", "category", "category", "gristHelper_Display3"),
                ("demand_tier_id", "demand_tier", "demand", "gristHelper_Display4"),
                ("chassis_profile_id", "chassis_profile", "chassis", "gristHelper_Display5"),
                ("construction_profile_id", "construction_profile", "construction", "gristHelper_Display6"),
                ("integrity_profile_id", "integrity_profile", "integrity", "gristHelper_Display7"),
            ):
                stable = row.pop(source_field)
                row[target_field] = ids[mapping].get(stable, 0) if stable else 0
                row[helper] = stable or None
            row["approved_at"] = row["approved_at"] or None
            return row
        _insert_rows(connection, "Equipment", seed["Equipment"], equipment_row)

    equipment_ids = _id_map(connection, "Equipment", "equipment_revision_id")
    transforms: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
        "Equipment_text": lambda s: {
            "equipment_text_id": s["equipment_text_id"],
            "equipment_revision": equipment_ids[s["equipment_revision_id"]],
            "locale": s["locale"], "text_key": s["text_key"],
            "text_kind": s["text_kind"], "text_value": s["text_value"],
            "revision": s["revision"], "sort_order": s["sort_order"],
            "gristHelper_Display": s["equipment_revision_id"],
        },
        "Slot_occupancy": lambda s: {
            "occupancy_id": s["occupancy_id"],
            "equipment_revision": equipment_ids[s["equipment_revision_id"]],
            "slot": ids["slot"][s["slot_id"]],
            "gristHelper_Display": s["equipment_revision_id"],
            "gristHelper_Display2": s["slot_id"],
            "occupancy_role": s["occupancy_role"], "hand_group": s["hand_group"],
            "occupancy_units": s["occupancy_units"],
            "delivery_hook": ids["hook"][s["delivery_hook_id"]],
            "gristHelper_Display3": s["delivery_hook_id"],
            "supports_combo_source": s["supports_combo_source"],
            "authoring_notes": s["authoring_notes"], "sort_order": s["sort_order"],
        },
        "Damage_profile_entries": lambda s: {
            "damage_profile_entry_id": s["damage_profile_entry_id"],
            "profile_id": s["profile_id"],
            "damage_type": ids["damage_type"][s["damage_type_id"]],
            "gristHelper_Display": s["damage_type_id"], "base_pips": s["base_pips"],
            "pip_budget_group": s["pip_budget_group"],
            "primary_status_hook_id": s["primary_status_hook_id"],
            "secondary_status_hook_id": s["secondary_status_hook_id"],
            "requirement_eligible": s["requirement_eligible"],
            "source_layer": s["source_layer"], "sort_order": s["sort_order"],
        },
        "Defence_profile_entries": lambda s: {
            "defence_profile_entry_id": s["defence_profile_entry_id"],
            "defence_profile_id": s["defence_profile_id"], "scope_kind": s["scope_kind"],
            "damage_group": ids["damage_group"][s["damage_group_id"]],
            "gristHelper_Display": s["damage_group_id"],
            "damage_type": ids["damage_type"].get(s["damage_type_id"], 0) if s["damage_type_id"] else 0,
            "gristHelper_Display2": s["damage_type_id"] or None,
            "rating_value": s["rating_value"], "rating_unit": s["rating_unit"],
            "exception_polarity": s["exception_polarity"],
            "condition_expression_id": s["condition_expression_id"],
            "narration_fragment_id": s["narration_fragment_id"],
            "sort_order": s["sort_order"],
        },
    }
    for table in ("Equipment_text", "Slot_occupancy", "Damage_profile_entries", "Defence_profile_entries"):
        if not before[table]:
            _insert_rows(connection, table, seed[table], transforms[table])

    after = stable_snapshot(connection)
    if after != seed:
        raise M10EquipmentError("stable-ID readback differs from the governed seed")
    assert_integrity(connection)
    bridge = connection.execute(
        "SELECT bridge2_mechanism FROM Construction_profiles "
        "WHERE construction_profile_id='construction.shield_standard'"
    ).fetchone()[0]
    metadata = column_metadata(
        connection, user_table_ref(connection, "Construction_profiles"), "bridge2_mechanism"
    )
    choices = json.loads(metadata["widgetOptions"])["choices"]
    pip_totals = {
        row["profile_id"]: sum(
            item["base_pips"] for item in after["Damage_profile_entries"]
            if item["profile_id"] == row["profile_id"]
        )
        for row in after["Damage_profile_entries"]
    }
    return {
        "before_counts": {table: len(rows) for table, rows in before.items()},
        "after_counts": {table: len(rows) for table, rows in after.items()},
        "stable_ids_unique": True,
        "stable_reference_readback": True,
        "scalar_authoring": True,
        "bridge2_choices": choices,
        "bridge2_value": bridge,
        "pip_totals": pip_totals,
        "shield_pool_verified": (
            sum(
                row["base_pips"]
                for row in after["Damage_profile_entries"]
                if row["profile_id"] == "martial.shield_standard"
            ) == 1
            and after["Defence_profile_entries"][0]["rating_value"] == 1
            and after["Defence_profile_entries"][0]["rating_unit"] == "pip"
        ),
        "equipment_tags_deferred": len(after["Equipment_tags"]) == 0,
        "sqlite_integrity": "ok",
    }


def export_snapshot(snapshot: dict[str, list[dict[str, Any]]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for table, file_name in TABLE_FILES.items():
        with (output_dir / file_name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADERS[table], lineterminator="\n")
            writer.writeheader()
            for row in snapshot[table]:
                values = {}
                for key in HEADERS[table]:
                    value = row[key]
                    if value is None:
                        values[key] = ""
                    elif isinstance(value, bool):
                        values[key] = str(value).lower()
                    else:
                        values[key] = value
                writer.writerow(values)
