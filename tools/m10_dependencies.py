"""M10 dependency seed validation, Grist population, and stable-ID exports."""

from __future__ import annotations

import csv
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from r7_grist import R7Error, assert_integrity, column_metadata, user_table_ref


class M10DependencyError(R7Error):
    """Raised when an M10 dependency precondition or proof gate fails."""


TABLE_FILES = {
    "Chassis_profiles": "chassis_profiles.csv",
    "Integrity_profiles": "integrity_profiles.csv",
    "Integrity_states": "integrity_states.csv",
    "Construction_profiles": "construction_profiles.csv",
}

HEADERS = {
    "Chassis_profiles": (
        "chassis_profile_id", "display_name", "chassis_family", "handedness",
        "weight_class", "reach_class", "base_martial_profile_id", "description",
        "authoring_notes", "sort_order",
    ),
    "Integrity_profiles": (
        "integrity_profile_id", "display_name", "description", "authoring_notes",
        "sort_order",
    ),
    "Integrity_states": (
        "integrity_state_row_id", "integrity_profile_id", "state_id", "ordinal",
        "entry_condition_id", "opening_delta_modifier_q",
        "opening_decay_modifier_q", "discipline_creation_enabled",
        "finisher_gate_eligible", "render_state_id", "repair_policy_id",
        "authoring_notes", "sort_order",
    ),
    "Construction_profiles": (
        "construction_profile_id", "display_name", "construction_family_id",
        "material_id", "rigidity_parameter_id", "coverage_profile_id",
        "brittleness_parameter_id", "defence_profile_id", "type_exception_budget",
        "integrity_profile_id", "ward_source_profile_id", "bridge2_mechanism",
        "encumbrance_profile_id", "visual_mesh_family_id",
        "integrity_render_profile_id", "description", "authoring_notes", "sort_order",
    ),
}

STABLE_ID_FIELD = {
    "Chassis_profiles": "chassis_profile_id",
    "Integrity_profiles": "integrity_profile_id",
    "Integrity_states": "integrity_state_row_id",
    "Construction_profiles": "construction_profile_id",
}

EXPECTED_COUNTS = {
    "Chassis_profiles": 5,
    "Integrity_profiles": 1,
    "Integrity_states": 3,
    "Construction_profiles": 2,
}

INT_FIELDS = {
    "sort_order", "ordinal", "opening_delta_modifier_q",
    "opening_decay_modifier_q", "type_exception_budget",
}
BOOL_FIELDS = {"discipline_creation_enabled", "finisher_gate_eligible"}


def _parse_optional_int(value: str, field: str, row_number: int) -> int | None:
    if value == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise M10DependencyError(
            f"row {row_number} has invalid integer {field}={value!r}"
        ) from exc


def _parse_bool(value: str, field: str, row_number: int) -> bool:
    lowered = value.lower()
    if lowered not in {"true", "false"}:
        raise M10DependencyError(
            f"row {row_number} has invalid boolean {field}={value!r}"
        )
    return lowered == "true"


def load_seed(seed_dir: Path) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for table, file_name in TABLE_FILES.items():
        path = seed_dir / file_name
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != HEADERS[table]:
                raise M10DependencyError(
                    f"unexpected columns for {file_name}: {reader.fieldnames}"
                )
            rows: list[dict[str, Any]] = []
            for row_number, source in enumerate(reader, 2):
                row: dict[str, Any] = dict(source)
                for field in INT_FIELDS.intersection(row):
                    row[field] = _parse_optional_int(row[field], field, row_number)
                for field in BOOL_FIELDS.intersection(row):
                    row[field] = _parse_bool(row[field], field, row_number)
                rows.append(row)
        output[table] = rows
    validate_seed(output)
    return output


def validate_seed(seed: dict[str, list[dict[str, Any]]]) -> None:
    for table, expected in EXPECTED_COUNTS.items():
        rows = seed.get(table, [])
        if len(rows) != expected:
            raise M10DependencyError(f"{table} must contain {expected} rows")
        field = STABLE_ID_FIELD[table]
        ids = [str(row[field]) for row in rows]
        duplicates = [key for key, count in Counter(ids).items() if count > 1]
        if any(not value for value in ids) or duplicates:
            raise M10DependencyError(f"{table} stable IDs must be unique and non-empty")
        sort_orders = [row["sort_order"] for row in rows]
        if any(value is None for value in sort_orders) or sort_orders != sorted(sort_orders):
            raise M10DependencyError(f"{table} sort_order must be populated and ordered")

    chassis = {row["chassis_profile_id"]: row for row in seed["Chassis_profiles"]}
    expected_handedness = {
        "chassis.maul": "two_handed",
        "chassis.dagger": "one_handed",
        "chassis.sword_1h": "one_handed",
        "chassis.shield_standard": "one_handed",
        "chassis.mace_1h": "one_handed",
    }
    if {key: chassis.get(key, {}).get("handedness") for key in expected_handedness} != expected_handedness:
        raise M10DependencyError("M10 chassis handedness does not match the locked fixture")

    profiles = {row["integrity_profile_id"] for row in seed["Integrity_profiles"]}
    ref_states = [row["state_id"] for row in seed["Integrity_states"]]
    if profiles != {"integrity.shield_standard"}:
        raise M10DependencyError("the dependency slice must contain the Standard Shield profile")
    if ref_states != ["stable", "cracked", "broken_guard"]:
        raise M10DependencyError("Standard Shield state path must be stable/cracked/broken_guard")
    if any(row["integrity_profile_id"] not in profiles for row in seed["Integrity_states"]):
        raise M10DependencyError("integrity state references an unknown profile")

    constructions = {
        row["construction_profile_id"]: row for row in seed["Construction_profiles"]
    }
    shield = constructions.get("construction.shield_standard", {})
    if shield.get("integrity_profile_id") != "integrity.shield_standard":
        raise M10DependencyError("Standard Shield construction must reference its integrity profile")
    if shield.get("defence_profile_id") != "defence.shield_standard":
        raise M10DependencyError("Standard Shield defence join key is not stable")
    if shield.get("bridge2_mechanism") != "barycentre_well":
        raise M10DependencyError("Standard Shield must use the v0.25.0 barycentre well")

    prose_fields = {"description", "authoring_notes"}
    for rows in seed.values():
        for row in rows:
            for field, value in row.items():
                if (
                    field not in prose_fields
                    and isinstance(value, str)
                    and any(token in value for token in (";", "|"))
                ):
                    raise M10DependencyError(
                        f"scalar field {field} contains a delimited value"
                    )


def _id_map(connection: sqlite3.Connection, table: str, field: str) -> dict[str, int]:
    return {
        str(row[field]): int(row["id"])
        for row in connection.execute(f'SELECT id, "{field}" FROM "{table}"')
    }


def _stable_rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    rows = [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY sort_order, id')]
    output: list[dict[str, Any]] = []
    if table == "Integrity_states":
        profiles = {value: key for key, value in _id_map(
            connection, "Integrity_profiles", "integrity_profile_id"
        ).items()}
        states = {value: key for key, value in _id_map(
            connection, "Ref_integrity_states", "integrity_state_id"
        ).items()}
        for source in rows:
            output.append({
                "integrity_state_row_id": source["integrity_state_row_id"],
                "integrity_profile_id": profiles.get(source["integrity_profile"], ""),
                "state_id": states.get(source["state"], ""),
                "ordinal": source["ordinal"],
                "entry_condition_id": source["entry_condition_id"] or "",
                "opening_delta_modifier_q": source["opening_delta_modifier_q"],
                "opening_decay_modifier_q": source["opening_decay_modifier_q"],
                "discipline_creation_enabled": bool(source["discipline_creation_enabled"]),
                "finisher_gate_eligible": bool(source["finisher_gate_eligible"]),
                "render_state_id": source["render_state_id"] or "",
                "repair_policy_id": source["repair_policy_id"] or "",
                "authoring_notes": source["authoring_notes"] or "",
                "sort_order": source["sort_order"],
            })
        return output
    if table == "Construction_profiles":
        profiles = {value: key for key, value in _id_map(
            connection, "Integrity_profiles", "integrity_profile_id"
        ).items()}
        parameters = {value: key for key, value in _id_map(
            connection, "Design_parameters", "parameter_id"
        ).items()}
        for source in rows:
            output.append({
                "construction_profile_id": source["construction_profile_id"],
                "display_name": source["display_name"],
                "construction_family_id": source["construction_family_id"] or "",
                "material_id": source["material_id"] or "",
                "rigidity_parameter_id": parameters.get(source["rigidity_parameter"], ""),
                "coverage_profile_id": source["coverage_profile_id"] or "",
                "brittleness_parameter_id": parameters.get(source["brittleness_parameter"], ""),
                "defence_profile_id": source["defence_profile_id"] or "",
                "type_exception_budget": source["type_exception_budget"],
                "integrity_profile_id": profiles.get(source["integrity_profile"], ""),
                "ward_source_profile_id": source["ward_source_profile_id"] or "",
                "bridge2_mechanism": source["bridge2_mechanism"] or "",
                "encumbrance_profile_id": source["encumbrance_profile_id"] or "",
                "visual_mesh_family_id": source["visual_mesh_family_id"] or "",
                "integrity_render_profile_id": source["integrity_render_profile_id"] or "",
                "description": source["description"] or "",
                "authoring_notes": source["authoring_notes"] or "",
                "sort_order": source["sort_order"],
            })
        return output
    for source in rows:
        output.append({field: source[field] for field in HEADERS[table]})
    return output


def stable_snapshot(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    return {table: _stable_rows(connection, table) for table in TABLE_FILES}


def dependency_schema_snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for table in TABLE_FILES:
        table_ref = user_table_ref(connection, table)
        output[table] = {
            "columns": [
                {
                    key: row[key]
                    for key in (
                        "colId", "type", "isFormula", "formula", "displayCol", "visibleCol"
                    )
                }
                for row in connection.execute(
                    "SELECT * FROM _grist_Tables_column "
                    "WHERE parentId = ? ORDER BY parentPos, id",
                    (table_ref,),
                )
            ],
            "sqlite_schema": [
                {
                    "name": row[1],
                    "type": row[2],
                    "default": row[4],
                    "primary_key": bool(row[5]),
                }
                for row in connection.execute(f'PRAGMA table_info("{table}")')
            ],
        }
    return output


def _make_editable(connection: sqlite3.Connection, table: str) -> None:
    table_ref = user_table_ref(connection, table)
    fields = set(HEADERS[table])
    aliases = {
        "Integrity_states": {"integrity_profile_id": "integrity_profile", "state_id": "state"},
        "Construction_profiles": {
            "rigidity_parameter_id": "rigidity_parameter",
            "brittleness_parameter_id": "brittleness_parameter",
            "integrity_profile_id": "integrity_profile",
        },
    }.get(table, {})
    columns = {aliases.get(field, field) for field in fields}
    for column in columns:
        column_metadata(connection, table_ref, column)
    placeholders = ",".join("?" for _ in columns)
    connection.execute(
        f"UPDATE _grist_Tables_column SET isFormula = 0, formula = '' "
        f"WHERE parentId = ? AND colId IN ({placeholders})",
        (table_ref, *sorted(columns)),
    )


def _insert_rows(
    connection: sqlite3.Connection,
    table: str,
    rows: list[dict[str, Any]],
    transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> None:
    next_id = int(connection.execute(
        f'SELECT COALESCE(MAX(id), 0) + 1 FROM "{table}"'
    ).fetchone()[0])
    for offset, source in enumerate(rows):
        row = transform(source) if transform else dict(source)
        row = {"id": next_id + offset, "manualSort": source["sort_order"], **row}
        fields = list(row)
        connection.execute(
            f'INSERT INTO "{table}" ({", ".join(fields)}) '
            f'VALUES ({", ".join("?" for _ in fields)})',
            [row[field] for field in fields],
        )


def apply_dependencies(
    connection: sqlite3.Connection,
    seed: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    connection.row_factory = sqlite3.Row
    validate_seed(seed)
    before = stable_snapshot(connection)
    for table, rows in before.items():
        if rows and rows != seed[table]:
            raise M10DependencyError(f"{table} is non-empty and differs from the governed seed")

    for table in TABLE_FILES:
        _make_editable(connection, table)

    if not before["Chassis_profiles"]:
        _insert_rows(connection, "Chassis_profiles", seed["Chassis_profiles"])
    if not before["Integrity_profiles"]:
        _insert_rows(connection, "Integrity_profiles", seed["Integrity_profiles"])

    profile_ids = _id_map(connection, "Integrity_profiles", "integrity_profile_id")
    state_ids = _id_map(connection, "Ref_integrity_states", "integrity_state_id")
    if not before["Integrity_states"]:
        def state_row(source: dict[str, Any]) -> dict[str, Any]:
            row = dict(source)
            profile_id = row.pop("integrity_profile_id")
            state_id = row.pop("state_id")
            row["integrity_profile"] = profile_ids[profile_id]
            row["state"] = state_ids[state_id]
            row["gristHelper_Display"] = profile_id
            row["gristHelper_Display2"] = state_id
            return row
        _insert_rows(connection, "Integrity_states", seed["Integrity_states"], state_row)

    parameter_ids = _id_map(connection, "Design_parameters", "parameter_id")
    if not before["Construction_profiles"]:
        def construction_row(source: dict[str, Any]) -> dict[str, Any]:
            row = dict(source)
            rigidity = row.pop("rigidity_parameter_id")
            brittleness = row.pop("brittleness_parameter_id")
            integrity = row.pop("integrity_profile_id")
            row["rigidity_parameter"] = parameter_ids.get(rigidity, 0) if rigidity else 0
            row["brittleness_parameter"] = parameter_ids.get(brittleness, 0) if brittleness else 0
            row["integrity_profile"] = profile_ids.get(integrity, 0) if integrity else 0
            row["gristHelper_Display"] = rigidity or None
            row["gristHelper_Display2"] = brittleness or None
            row["gristHelper_Display3"] = integrity or None
            return row
        _insert_rows(
            connection, "Construction_profiles", seed["Construction_profiles"], construction_row
        )

    after = stable_snapshot(connection)
    if after != seed:
        raise M10DependencyError("stable-ID readback differs from the governed seed")
    assert_integrity(connection)
    schema = dependency_schema_snapshot(connection)
    authored_columns_data = all(
        column["isFormula"] == 0
        for table in TABLE_FILES
        for column in schema[table]["columns"]
        if column["colId"] in {
            {
                "integrity_profile_id": "integrity_profile",
                "state_id": "state",
                "rigidity_parameter_id": "rigidity_parameter",
                "brittleness_parameter_id": "brittleness_parameter",
            }.get(field, field)
            for field in HEADERS[table]
        }
    )
    return {
        "before_counts": {table: len(rows) for table, rows in before.items()},
        "after_counts": {table: len(rows) for table, rows in after.items()},
        "stable_ids_unique": True,
        "stable_reference_readback": True,
        "scalar_authoring": True,
        "q_fields_remain_null": all(
            row["opening_delta_modifier_q"] is None
            and row["opening_decay_modifier_q"] is None
            for row in after["Integrity_states"]
        ),
        "authored_columns_are_data": authored_columns_data,
        "sqlite_integrity": "ok",
    }


def export_snapshot(
    snapshot: dict[str, list[dict[str, Any]]], output_dir: Path
) -> None:
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
