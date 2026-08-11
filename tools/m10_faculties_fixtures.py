"""M10 faculty/fixture seed validation, Grist migration, and stable-ID exports."""

from __future__ import annotations

import csv
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from r7_grist import R7Error, assert_integrity, column_metadata, user_table_ref


class M10FacultyFixtureError(R7Error):
    """Raised when an M10 faculty/fixture precondition or proof gate fails."""


TABLE_FILES = {
    "Faculties": "faculties.csv",
    "Faculty_profiles": "faculty_profiles.csv",
    "Fixture_builds": "fixture_builds.csv",
    "Fixture_stat_weights": "fixture_stat_weights.csv",
    "Fixture_loadouts": "fixture_loadouts.csv",
    "Fixture_encounters": "fixture_encounters.csv",
    "Fixture_coverage": "fixture_coverage.csv",
}

HEADERS = {
    "Faculties": (
        "faculty_id", "revision_number", "faculty_revision_id", "schema_version",
        "content_version", "lifecycle_status_id", "design_status_id",
        "faculty_family_id", "faculty_origin", "display_name_key",
        "description_key", "base_damage_profile_id", "delivery_hook_id",
        "gate_node_group_id", "source_document_ref", "decision_origin",
        "authoring_notes", "content_hash", "approved_by", "approved_at",
        "sort_order",
    ),
    "Faculty_profiles": (
        "faculty_profile_entry_id", "faculty_revision_id", "entry_kind",
        "profile_id", "damage_type_id", "base_pips", "skill_revision_id",
        "scope_kind", "region_id", "grant_mode", "source_hook_id",
        "gate_node_group_id", "requirement_eligible", "condition_expression_id",
        "authoring_notes", "sort_order",
    ),
    "Fixture_builds": (
        "fixture_build_id", "fixture_set_id", "display_name", "floor_m",
        "floor_f", "floor_i", "floor_sum", "floor_valid", "home_region_id",
        "intended_fantasy", "design_status_id", "description", "sort_order",
    ),
    "Fixture_stat_weights": (
        "fixture_stat_weight_id", "fixture_set_id", "fixture_build_id",
        "stat_id", "relative_weight", "normalisation_group", "sort_order",
    ),
    "Fixture_loadouts": (
        "fixture_loadout_id", "fixture_set_id", "fixture_build_id",
        "equipment_revision_id", "slot_id", "quantity", "hand_assignment",
        "authoring_notes", "sort_order",
    ),
    "Fixture_encounters": (
        "fixture_encounter_id", "fixture_set_id", "display_name", "zone_count",
        "environment_id", "proof_purpose", "description", "sort_order",
    ),
    "Fixture_coverage": (
        "fixture_coverage_id", "fixture_set_id", "fixture_kind", "fixture_id",
        "rule_id", "system_feature", "expected_assertion", "coverage_kind",
        "gap_status", "notes", "sort_order",
    ),
}

EXPECTED_COUNTS = {
    "Faculties": 5,
    "Faculty_profiles": 0,
    "Fixture_builds": 5,
    "Fixture_stat_weights": 45,
    "Fixture_loadouts": 7,
    "Fixture_encounters": 5,
    "Fixture_coverage": 29,
}

STABLE_ID_FIELD = {
    "Faculties": "faculty_revision_id",
    "Faculty_profiles": "faculty_profile_entry_id",
    "Fixture_builds": "fixture_build_id",
    "Fixture_stat_weights": "fixture_stat_weight_id",
    "Fixture_loadouts": "fixture_loadout_id",
    "Fixture_encounters": "fixture_encounter_id",
    "Fixture_coverage": "fixture_coverage_id",
}

INT_FIELDS = {
    "revision_number", "base_pips", "relative_weight", "quantity", "zone_count",
    "sort_order",
}
FLOAT_FIELDS = {"floor_m", "floor_f", "floor_i", "floor_sum"}
BOOL_FIELDS = {"floor_valid", "requirement_eligible"}


def _optional_int(value: str, field: str, row_number: int) -> int | None:
    if value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise M10FacultyFixtureError(
            f"row {row_number} has invalid integer {field}={value!r}"
        ) from exc


def _optional_float(value: str, field: str, row_number: int) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise M10FacultyFixtureError(
            f"row {row_number} has invalid numeric {field}={value!r}"
        ) from exc


def _optional_bool(value: str, field: str, row_number: int) -> bool | None:
    if value == "":
        return None
    lowered = value.lower()
    if lowered not in {"true", "false"}:
        raise M10FacultyFixtureError(
            f"row {row_number} has invalid boolean {field}={value!r}"
        )
    return lowered == "true"


def load_seed(seed_dir: Path) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for table, file_name in TABLE_FILES.items():
        with (seed_dir / file_name).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != HEADERS[table]:
                raise M10FacultyFixtureError(
                    f"unexpected columns for {file_name}: {reader.fieldnames}"
                )
            rows: list[dict[str, Any]] = []
            for row_number, source in enumerate(reader, 2):
                row: dict[str, Any] = dict(source)
                for field in INT_FIELDS.intersection(row):
                    row[field] = _optional_int(row[field], field, row_number)
                for field in FLOAT_FIELDS.intersection(row):
                    row[field] = _optional_float(row[field], field, row_number)
                for field in BOOL_FIELDS.intersection(row):
                    row[field] = _optional_bool(row[field], field, row_number)
                rows.append(row)
        output[table] = rows
    validate_seed(output)
    return output


def validate_seed(seed: dict[str, list[dict[str, Any]]]) -> None:
    for table, expected in EXPECTED_COUNTS.items():
        rows = seed.get(table, [])
        if len(rows) != expected:
            raise M10FacultyFixtureError(f"{table} must contain {expected} rows")
        if not rows:
            continue
        stable_field = STABLE_ID_FIELD[table]
        stable_ids = [str(row[stable_field]) for row in rows]
        duplicates = [key for key, count in Counter(stable_ids).items() if count > 1]
        if any(not value for value in stable_ids) or duplicates:
            raise M10FacultyFixtureError(
                f"{table} stable IDs must be unique and non-empty"
            )
        orders = [row["sort_order"] for row in rows]
        if any(value is None for value in orders) or orders != sorted(orders):
            raise M10FacultyFixtureError(f"{table} sort_order must be populated and ordered")

    faculty = {row["faculty_revision_id"]: row for row in seed["Faculties"]}
    expected_faculties = {
        "faculty.innate_upper@1": ("innate", "innate", "", "body_group.upper_limb"),
        "faculty.innate_bite@1": ("innate", "innate", "none", "body_group.jaw_teeth"),
        "faculty.arcana@1": ("arcana", "", "voice", "body_group.jaw_teeth"),
        "faculty.mudra@1": ("mudra", "", "none", "body_group.hand_fingers"),
        "faculty.psyche@1": ("psyche", "", "none", "body_group.head_spine"),
    }
    if set(faculty) != set(expected_faculties):
        raise M10FacultyFixtureError("faculty revision set differs from P·10 / M·2A.10a")
    for revision_id, expected in expected_faculties.items():
        row = faculty[revision_id]
        if revision_id != f'{row["faculty_id"]}@{row["revision_number"]}':
            raise M10FacultyFixtureError(f"invalid revision identity {revision_id}")
        actual = (
            row["faculty_family_id"], row["faculty_origin"],
            row["delivery_hook_id"], row["gate_node_group_id"],
        )
        if actual != expected:
            raise M10FacultyFixtureError(f"{revision_id} family/hook/gate differs from source")
        if (
            row["content_version"] != "0.29.0"
            or row["lifecycle_status_id"] != "candidate"
            or row["design_status_id"] != "fixture"
            or row["schema_version"]
            or row["base_damage_profile_id"]
        ):
            raise M10FacultyFixtureError(f"{revision_id} governance fields are incorrect")
    if seed["Faculty_profiles"]:
        raise M10FacultyFixtureError(
            "faculty profiles must remain empty until source-owned footprints exist"
        )

    builds = {row["fixture_build_id"]: row for row in seed["Fixture_builds"]}
    expected_floors = {
        "fixture.build.striker": (0.25, 0.15, 0.05, "pressure"),
        "fixture.build.controller": (0.09, 0.18, 0.18, "discipline"),
        "fixture.build.technical": (0.15, 0.10, 0.20, "instinct"),
        "fixture.build.trickster": (0.12, 0.08, 0.25, "instinct"),
        "fixture.build.war_priest": (0.15, 0.20, 0.10, "discipline"),
    }
    if set(builds) != set(expected_floors):
        raise M10FacultyFixtureError("fixture build set differs from P·10.2")
    for build_id, (floor_m, floor_f, floor_i, region) in expected_floors.items():
        row = builds[build_id]
        if (
            (row["floor_m"], row["floor_f"], row["floor_i"], row["home_region_id"])
            != (floor_m, floor_f, floor_i, region)
            or abs(row["floor_sum"] - 0.45) > 1e-12
            or row["floor_valid"] is not True
            or row["fixture_set_id"] != "m10-v1"
            or row["design_status_id"] != "fixture"
        ):
            raise M10FacultyFixtureError(f"{build_id} differs from the locked fixture")

    expected_weights = {
        "fixture.build.striker": (3, 2, 1, 1, 1, 1, 2, 1, 2),
        "fixture.build.controller": (1, 1, 3, 2, 2, 3, 2, 2, 3),
        "fixture.build.technical": (1, 3, 1, 3, 2, 1, 1, 2, 1),
        "fixture.build.trickster": (1, 3, 1, 3, 2, 2, 1, 2, 1),
        "fixture.build.war_priest": (2, 1, 2, 2, 3, 3, 2, 2, 2),
    }
    stat_order = (
        "strength", "finesse", "stamina", "intellect", "will", "spirit",
        "frame", "poise", "constitution",
    )
    actual_weights: dict[str, dict[str, int]] = defaultdict(dict)
    for row in seed["Fixture_stat_weights"]:
        if row["fixture_set_id"] != "m10-v1" or row["normalisation_group"] != "core_stats":
            raise M10FacultyFixtureError("fixture stat-weight governance fields are incorrect")
        actual_weights[row["fixture_build_id"]][row["stat_id"]] = row["relative_weight"]
    for build_id, weights in expected_weights.items():
        if tuple(actual_weights[build_id].get(stat) for stat in stat_order) != weights:
            raise M10FacultyFixtureError(f"{build_id} stat weights differ from P·10.2")

    expected_loadouts = {
        "fixture.build.striker": [("weapon.maul@1", "main_hand", "both")],
        "fixture.build.controller": [
            ("weapon.sword_1h@1", "main_hand", "main_hand"),
            ("shield.standard@1", "off_hand", "off_hand"),
        ],
        "fixture.build.technical": [
            ("weapon.dagger@1", "main_hand", "main_hand"),
            ("weapon.dagger@1", "off_hand", "off_hand"),
        ],
        "fixture.build.trickster": [("weapon.dagger@1", "main_hand", "main_hand")],
        "fixture.build.war_priest": [("weapon.mace_1h@1", "main_hand", "main_hand")],
    }
    actual_loadouts: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for row in seed["Fixture_loadouts"]:
        if row["fixture_set_id"] != "m10-v1" or row["quantity"] != 1:
            raise M10FacultyFixtureError("fixture loadout governance fields are incorrect")
        actual_loadouts[row["fixture_build_id"]].append(
            (row["equipment_revision_id"], row["slot_id"], row["hand_assignment"])
        )
    if dict(actual_loadouts) != expected_loadouts:
        raise M10FacultyFixtureError("fixture loadouts differ from P·10.2–10.3")

    expected_encounters = {
        "fixture.encounter.corridor": (2, ""),
        "fixture.encounter.chamber": (3, ""),
        "fixture.encounter.gallery": (4, ""),
        "fixture.encounter.vault": (3, "high_ground"),
        "fixture.encounter.den": (3, ""),
    }
    encounters = {
        row["fixture_encounter_id"]: (row["zone_count"], row["environment_id"])
        for row in seed["Fixture_encounters"]
    }
    if encounters != expected_encounters:
        raise M10FacultyFixtureError("fixture encounters differ from P·10.6")

    coverage = seed["Fixture_coverage"]
    summary = Counter(row["coverage_kind"] for row in coverage)
    if summary != {"proof": 12, "gap": 17}:
        raise M10FacultyFixtureError("fixture coverage must contain 12 proofs and 17 gaps")
    for row in coverage:
        if row["fixture_set_id"] != "m10-v1":
            raise M10FacultyFixtureError("fixture coverage has the wrong set ID")
        if row["coverage_kind"] == "proof" and row["gap_status"]:
            raise M10FacultyFixtureError("proof coverage cannot carry a gap status")
        if row["coverage_kind"] == "gap" and row["gap_status"] not in {"open", "deferred"}:
            raise M10FacultyFixtureError("gap coverage must be open or deferred")

    scalar_fields = {
        "faculty_id", "faculty_revision_id", "faculty_family_id", "faculty_origin",
        "delivery_hook_id", "gate_node_group_id", "fixture_build_id",
        "fixture_set_id", "home_region_id", "stat_id", "normalisation_group",
        "equipment_revision_id", "slot_id", "hand_assignment", "environment_id",
        "fixture_kind", "fixture_id", "rule_id", "coverage_kind", "gap_status",
    }
    for rows in seed.values():
        for row in rows:
            for field in scalar_fields.intersection(row):
                value = row[field]
                if isinstance(value, str) and any(token in value for token in (";", "|", ",")):
                    raise M10FacultyFixtureError(
                        f"scalar field {field} contains a delimited value"
                    )


def _id_map(connection: sqlite3.Connection, table: str, field: str) -> dict[str, int]:
    return {
        str(row[field]): int(row["id"])
        for row in connection.execute(f'SELECT id, "{field}" FROM "{table}"')
    }


def _reverse_id_map(connection: sqlite3.Connection, table: str, field: str) -> dict[int, str]:
    return {value: key for key, value in _id_map(connection, table, field).items()}


def _stable_rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY manualSort, id')
    ]
    maps = {
        "lifecycle": _reverse_id_map(connection, "Ref_lifecycle_status", "lifecycle_status_id"),
        "design": _reverse_id_map(connection, "Ref_design_status", "design_status_id"),
        "family": _reverse_id_map(connection, "Ref_faculty_families", "faculty_family_id"),
        "hook": _reverse_id_map(connection, "Ref_hooks", "hook_id"),
        "damage": _reverse_id_map(connection, "Ref_damage_types", "damage_type_id"),
        "region": _reverse_id_map(connection, "Ref_regions", "region_id"),
        "faculty": _reverse_id_map(connection, "Faculties", "faculty_revision_id"),
        "build": _reverse_id_map(connection, "Fixture_builds", "fixture_build_id"),
        "stat": _reverse_id_map(connection, "Ref_stats", "stat_id"),
        "equipment": _reverse_id_map(connection, "Equipment", "equipment_revision_id"),
        "slot": _reverse_id_map(connection, "Ref_slots", "slot_id"),
        "rule": _reverse_id_map(connection, "Ref_rules", "rule_id"),
    }
    output: list[dict[str, Any]] = []
    for source in rows:
        if table == "Faculties":
            row = {
                "faculty_id": source["faculty_id"],
                "revision_number": source["revision_number"],
                "faculty_revision_id": source["faculty_revision_id"],
                "schema_version": source["schema_version"] or "",
                "content_version": source["content_version"],
                "lifecycle_status_id": maps["lifecycle"].get(source["lifecycle_status"], ""),
                "design_status_id": maps["design"].get(source["design_status"], ""),
                "faculty_family_id": maps["family"].get(source["faculty_family"], ""),
                "faculty_origin": source["faculty_origin"] or "",
                "display_name_key": source["display_name_key"],
                "description_key": source["description_key"],
                "base_damage_profile_id": source["base_damage_profile_id"] or "",
                "delivery_hook_id": maps["hook"].get(source["delivery_hook"], ""),
                "gate_node_group_id": source["gate_node_group_id"] or "",
                "source_document_ref": source["source_document_ref"],
                "decision_origin": source["decision_origin"],
                "authoring_notes": source["authoring_notes"] or "",
                "content_hash": source["content_hash"] or "",
                "approved_by": source["approved_by"] or "",
                "approved_at": source["approved_at"] or "",
                "sort_order": source["manualSort"],
            }
        elif table == "Faculty_profiles":
            row = {
                "faculty_profile_entry_id": source["faculty_profile_entry_id"],
                "faculty_revision_id": maps["faculty"].get(source["faculty_revision"], ""),
                "entry_kind": source["entry_kind"],
                "profile_id": source["profile_id"] or "",
                "damage_type_id": maps["damage"].get(source["damage_type"], ""),
                "base_pips": source["base_pips"],
                "skill_revision_id": source["skill_revision_id"] or "",
                "scope_kind": source["scope_kind"],
                "region_id": maps["region"].get(source["region"], ""),
                "grant_mode": source["grant_mode"],
                "source_hook_id": maps["hook"].get(source["source_hook"], ""),
                "gate_node_group_id": source["gate_node_group_id"] or "",
                "requirement_eligible": bool(source["requirement_eligible"]),
                "condition_expression_id": source["condition_expression_id"] or "",
                "authoring_notes": source["authoring_notes"] or "",
                "sort_order": source["sort_order"],
            }
        elif table == "Fixture_builds":
            row = {
                "fixture_build_id": source["fixture_build_id"],
                "fixture_set_id": source["fixture_set_id"],
                "display_name": source["display_name"],
                "floor_m": source["floor_m"], "floor_f": source["floor_f"],
                "floor_i": source["floor_i"], "floor_sum": source["floor_sum"],
                "floor_valid": bool(source["floor_valid"]),
                "home_region_id": maps["region"].get(source["home_region"], ""),
                "intended_fantasy": source["intended_fantasy"],
                "design_status_id": maps["design"].get(source["design_status"], ""),
                "description": source["description"], "sort_order": source["sort_order"],
            }
        elif table == "Fixture_stat_weights":
            row = {
                "fixture_stat_weight_id": source["fixture_stat_weight_id"],
                "fixture_set_id": source["fixture_set_id"],
                "fixture_build_id": maps["build"].get(source["build"], ""),
                "stat_id": maps["stat"].get(source["stat"], ""),
                "relative_weight": source["relative_weight"],
                "normalisation_group": source["normalisation_group"],
                "sort_order": source["sort_order"],
            }
        elif table == "Fixture_loadouts":
            row = {
                "fixture_loadout_id": source["fixture_loadout_id"],
                "fixture_set_id": source["fixture_set_id"],
                "fixture_build_id": maps["build"].get(source["build"], ""),
                "equipment_revision_id": maps["equipment"].get(source["equipment_revision"], ""),
                "slot_id": maps["slot"].get(source["slot"], ""),
                "quantity": source["quantity"],
                "hand_assignment": source["hand_assignment"],
                "authoring_notes": source["authoring_notes"] or "",
                "sort_order": source["sort_order"],
            }
        elif table == "Fixture_encounters":
            row = {field: source[field] if source[field] is not None else "" for field in HEADERS[table]}
        else:
            row = {
                "fixture_coverage_id": source["fixture_coverage_id"],
                "fixture_set_id": source["fixture_set_id"],
                "fixture_kind": source["fixture_kind"],
                "fixture_id": source["fixture_id"],
                "rule_id": maps["rule"].get(source["rule_id"], ""),
                "system_feature": source["system_feature"],
                "expected_assertion": source["expected_assertion"],
                "coverage_kind": source["coverage_kind"],
                "gap_status": source["gap_status"] or "",
                "notes": source["notes"] or "",
                "sort_order": source["sort_order"],
            }
        output.append(row)
    return output


def stable_snapshot(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    return {table: _stable_rows(connection, table) for table in TABLE_FILES}


def schema_snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for table in TABLE_FILES:
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
        "Faculties": {
            "lifecycle_status_id": "lifecycle_status", "design_status_id": "design_status",
            "faculty_family_id": "faculty_family", "delivery_hook_id": "delivery_hook",
        },
        "Faculty_profiles": {
            "faculty_revision_id": "faculty_revision", "damage_type_id": "damage_type",
            "region_id": "region", "source_hook_id": "source_hook",
        },
        "Fixture_builds": {
            "home_region_id": "home_region", "design_status_id": "design_status",
        },
        "Fixture_stat_weights": {"fixture_build_id": "build", "stat_id": "stat"},
        "Fixture_loadouts": {
            "fixture_build_id": "build", "equipment_revision_id": "equipment_revision",
            "slot_id": "slot",
        },
        "Fixture_encounters": {},
        "Fixture_coverage": {},
    }[table]
    derived = {
        "Faculties": {"faculty_revision_id", "sort_order"},
        "Fixture_builds": {"floor_sum", "floor_valid"},
    }.get(table, set())
    columns = {aliases.get(field, field) for field in HEADERS[table] if field not in derived}
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


def _require_baseline(connection: sqlite3.Connection) -> dict[str, int]:
    expected = {
        "Chassis_profiles": 5, "Integrity_profiles": 1, "Integrity_states": 3,
        "Construction_profiles": 2, "Equipment": 5, "Equipment_text": 20,
        "Equipment_tags": 0, "Slot_occupancy": 9, "Damage_profile_entries": 9,
        "Defence_profile_entries": 1, "Ref_rules": 148,
    }
    actual = {
        table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        for table in expected
    }
    if actual != expected:
        raise M10FacultyFixtureError(
            f"source is not the adopted M10 equipment baseline: {actual}"
        )
    return actual


def apply_faculties_fixtures(
    connection: sqlite3.Connection,
    seed: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    connection.row_factory = sqlite3.Row
    validate_seed(seed)
    baseline = _require_baseline(connection)
    before = stable_snapshot(connection)
    for table, rows in before.items():
        if rows and rows != seed[table]:
            raise M10FacultyFixtureError(f"{table} is non-empty and differs from the governed seed")
    for table in TABLE_FILES:
        _make_editable(connection, table)

    ids = {
        "lifecycle": _id_map(connection, "Ref_lifecycle_status", "lifecycle_status_id"),
        "design": _id_map(connection, "Ref_design_status", "design_status_id"),
        "family": _id_map(connection, "Ref_faculty_families", "faculty_family_id"),
        "hook": _id_map(connection, "Ref_hooks", "hook_id"),
        "damage": _id_map(connection, "Ref_damage_types", "damage_type_id"),
        "region": _id_map(connection, "Ref_regions", "region_id"),
        "stat": _id_map(connection, "Ref_stats", "stat_id"),
        "equipment": _id_map(connection, "Equipment", "equipment_revision_id"),
        "slot": _id_map(connection, "Ref_slots", "slot_id"),
        "rule": _id_map(connection, "Ref_rules", "rule_id"),
    }
    for row in seed["Faculties"]:
        for field, mapping in (
            ("lifecycle_status_id", "lifecycle"), ("design_status_id", "design"),
            ("faculty_family_id", "family"),
        ):
            if row[field] not in ids[mapping]:
                raise M10FacultyFixtureError(f"unresolved {field}={row[field]!r}")
        if row["delivery_hook_id"] and row["delivery_hook_id"] not in ids["hook"]:
            raise M10FacultyFixtureError(
                f"unresolved delivery_hook_id={row['delivery_hook_id']!r}"
            )
    for row in seed["Fixture_builds"]:
        if row["home_region_id"] not in ids["region"] or row["design_status_id"] not in ids["design"]:
            raise M10FacultyFixtureError(f"unresolved build Reference in {row['fixture_build_id']}")
    for row in seed["Fixture_stat_weights"]:
        if row["stat_id"] not in ids["stat"]:
            raise M10FacultyFixtureError(f"unresolved stat_id={row['stat_id']!r}")
    for row in seed["Fixture_loadouts"]:
        if row["equipment_revision_id"] not in ids["equipment"] or row["slot_id"] not in ids["slot"]:
            raise M10FacultyFixtureError(f"unresolved loadout Reference in {row['fixture_loadout_id']}")
    for row in seed["Fixture_coverage"]:
        if row["rule_id"] and row["rule_id"] not in ids["rule"]:
            raise M10FacultyFixtureError(f"unresolved rule_id={row['rule_id']!r}")

    if not before["Faculties"]:
        def faculty_row(source: dict[str, Any]) -> dict[str, Any]:
            return {
                "faculty_id": source["faculty_id"],
                "revision_number": source["revision_number"],
                "faculty_revision_id": source["faculty_revision_id"],
                "schema_version": source["schema_version"],
                "content_version": source["content_version"],
                "lifecycle_status": ids["lifecycle"][source["lifecycle_status_id"]],
                "gristHelper_Display": source["lifecycle_status_id"],
                "design_status": ids["design"][source["design_status_id"]],
                "gristHelper_Display2": source["design_status_id"],
                "faculty_family": ids["family"][source["faculty_family_id"]],
                "gristHelper_Display3": source["faculty_family_id"],
                "faculty_origin": source["faculty_origin"],
                "display_name_key": source["display_name_key"],
                "description_key": source["description_key"],
                "base_damage_profile_id": source["base_damage_profile_id"],
                "delivery_hook": ids["hook"].get(source["delivery_hook_id"], 0),
                "gristHelper_Display4": source["delivery_hook_id"] or None,
                "gate_node_group_id": source["gate_node_group_id"],
                "source_document_ref": source["source_document_ref"],
                "decision_origin": source["decision_origin"],
                "authoring_notes": source["authoring_notes"],
                "content_hash": source["content_hash"],
                "approved_by": source["approved_by"],
                "approved_at": None,
            }
        _insert_rows(connection, "Faculties", seed["Faculties"], faculty_row)

    faculty_ids = _id_map(connection, "Faculties", "faculty_revision_id")
    if not before["Faculty_profiles"] and seed["Faculty_profiles"]:
        _insert_rows(connection, "Faculty_profiles", seed["Faculty_profiles"], lambda s: {
            "faculty_profile_entry_id": s["faculty_profile_entry_id"],
            "faculty_revision": faculty_ids[s["faculty_revision_id"]],
            "gristHelper_Display": s["faculty_revision_id"],
            "entry_kind": s["entry_kind"], "profile_id": s["profile_id"],
            "damage_type": ids["damage"].get(s["damage_type_id"], 0),
            "gristHelper_Display2": s["damage_type_id"] or None,
            "base_pips": s["base_pips"], "skill_revision_id": s["skill_revision_id"],
            "scope_kind": s["scope_kind"], "region": ids["region"].get(s["region_id"], 0),
            "gristHelper_Display3": s["region_id"] or None,
            "grant_mode": s["grant_mode"], "source_hook": ids["hook"].get(s["source_hook_id"], 0),
            "gristHelper_Display4": s["source_hook_id"] or None,
            "gate_node_group_id": s["gate_node_group_id"],
            "requirement_eligible": s["requirement_eligible"],
            "condition_expression_id": s["condition_expression_id"],
            "authoring_notes": s["authoring_notes"], "sort_order": s["sort_order"],
        })

    if not before["Fixture_builds"]:
        _insert_rows(connection, "Fixture_builds", seed["Fixture_builds"], lambda s: {
            "fixture_build_id": s["fixture_build_id"], "fixture_set_id": s["fixture_set_id"],
            "display_name": s["display_name"], "floor_m": s["floor_m"],
            "floor_f": s["floor_f"], "floor_i": s["floor_i"],
            "floor_sum": s["floor_sum"], "floor_valid": s["floor_valid"],
            "home_region": ids["region"][s["home_region_id"]],
            "gristHelper_Display": s["home_region_id"],
            "intended_fantasy": s["intended_fantasy"],
            "design_status": ids["design"][s["design_status_id"]],
            "gristHelper_Display2": s["design_status_id"],
            "description": s["description"], "sort_order": s["sort_order"],
        })
    build_ids = _id_map(connection, "Fixture_builds", "fixture_build_id")

    transforms: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
        "Fixture_stat_weights": lambda s: {
            "fixture_stat_weight_id": s["fixture_stat_weight_id"],
            "fixture_set_id": s["fixture_set_id"], "build": build_ids[s["fixture_build_id"]],
            "gristHelper_Display": s["fixture_build_id"], "stat": ids["stat"][s["stat_id"]],
            "gristHelper_Display2": s["stat_id"], "relative_weight": s["relative_weight"],
            "normalisation_group": s["normalisation_group"], "sort_order": s["sort_order"],
        },
        "Fixture_loadouts": lambda s: {
            "fixture_loadout_id": s["fixture_loadout_id"], "fixture_set_id": s["fixture_set_id"],
            "build": build_ids[s["fixture_build_id"]], "gristHelper_Display": s["fixture_build_id"],
            "equipment_revision": ids["equipment"][s["equipment_revision_id"]],
            "gristHelper_Display2": s["equipment_revision_id"],
            "slot": ids["slot"][s["slot_id"]], "gristHelper_Display3": s["slot_id"],
            "quantity": s["quantity"], "hand_assignment": s["hand_assignment"],
            "authoring_notes": s["authoring_notes"], "sort_order": s["sort_order"],
        },
        "Fixture_encounters": lambda s: dict(s),
        "Fixture_coverage": lambda s: {
            "fixture_coverage_id": s["fixture_coverage_id"],
            "fixture_set_id": s["fixture_set_id"], "fixture_kind": s["fixture_kind"],
            "fixture_id": s["fixture_id"], "rule_id": ids["rule"].get(s["rule_id"], 0),
            "gristHelper_Display": s["rule_id"] or None,
            "system_feature": s["system_feature"],
            "expected_assertion": s["expected_assertion"],
            "coverage_kind": s["coverage_kind"], "gap_status": s["gap_status"],
            "notes": s["notes"], "sort_order": s["sort_order"],
        },
    }
    for table in (
        "Fixture_stat_weights", "Fixture_loadouts", "Fixture_encounters",
        "Fixture_coverage",
    ):
        if not before[table]:
            _insert_rows(connection, table, seed[table], transforms[table])

    after = stable_snapshot(connection)
    if after != seed:
        raise M10FacultyFixtureError("stable-ID readback differs from the governed seed")
    assert_integrity(connection)
    coverage_summary = dict(sorted(Counter(
        row["coverage_kind"] for row in after["Fixture_coverage"]
    ).items()))
    free_hands = {
        build: not any(
            row["hand_assignment"] in {"off_hand", "both"}
            for row in after["Fixture_loadouts"]
            if row["fixture_build_id"] == build
        )
        for build in build_ids
    }
    return {
        "before_counts": {table: len(rows) for table, rows in before.items()},
        "after_counts": {table: len(rows) for table, rows in after.items()},
        "baseline_counts": baseline,
        "stable_ids_unique": True,
        "stable_reference_readback": True,
        "scalar_authoring": True,
        "coverage_summary": coverage_summary,
        "free_hand_by_build": dict(sorted(free_hands.items())),
        "faculty_profiles_deferred": len(after["Faculty_profiles"]) == 0,
        "fixture_enemy_tables_deferred": not any(
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            for table in ("Fixture_enemies", "Fixture_encounter_members")
        ),
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
