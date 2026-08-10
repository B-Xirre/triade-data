"""Shared R7 Grist helpers: seed validation and stable-ID exports."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


EXPECTED_COUNTS = {"critical": 81, "high": 48, "medium": 14}
SEED_FIELDS = (
    "rule_id",
    "display_name",
    "description",
    "severity",
    "source_reference",
    "sort_order",
)


class R7Error(RuntimeError):
    """Raised when an R7 precondition or proof gate fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_seed(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != SEED_FIELDS:
            raise R7Error(f"unexpected seed columns: {reader.fieldnames}")
        rows: list[dict[str, Any]] = []
        for row_number, source in enumerate(reader, 2):
            try:
                sort_order = int(source["sort_order"])
            except (TypeError, ValueError) as exc:
                raise R7Error(f"seed row {row_number} has invalid sort_order") from exc
            row = {key: source[key] for key in SEED_FIELDS}
            row["sort_order"] = sort_order
            rows.append(row)

    ids = [row["rule_id"] for row in rows]
    duplicates = sorted(rule_id for rule_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise R7Error(f"duplicate seed rule IDs: {', '.join(duplicates)}")
    if len(rows) != 143 or len(set(ids)) != 143 or any(not rule_id for rule_id in ids):
        raise R7Error("seed must contain 143 unique non-empty rule IDs")
    counts = Counter(row["severity"] for row in rows)
    if counts != Counter(EXPECTED_COUNTS):
        raise R7Error(f"seed severity split mismatch: {dict(counts)}")
    if [row["sort_order"] for row in rows] != list(range(1, 144)):
        raise R7Error("seed sort_order must be the deterministic sequence 1..143")
    if any(not row["description"] or not row["source_reference"] for row in rows):
        raise R7Error("seed descriptions and source references must be non-empty")
    return rows


def user_table_ref(connection: sqlite3.Connection, table_id: str) -> int:
    row = connection.execute(
        "SELECT id FROM _grist_Tables WHERE tableId = ?", (table_id,)
    ).fetchone()
    if row is None:
        raise R7Error(f"missing Grist table {table_id}")
    return int(row[0])


def column_metadata(
    connection: sqlite3.Connection, table_ref: int, column_id: str
) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM _grist_Tables_column WHERE parentId = ? AND colId = ?",
        (table_ref, column_id),
    ).fetchone()
    if row is None:
        raise R7Error(f"missing Grist column metadata {table_ref}.{column_id}")
    return row


def stable_coverage_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    fixture_ref = user_table_ref(connection, "Fixture_coverage")
    rule_column = column_metadata(connection, fixture_ref, "rule_id")
    column_type = str(rule_column["type"])
    records = [dict(row) for row in connection.execute(
        "SELECT * FROM Fixture_coverage ORDER BY id"
    )]
    for record in records:
        for key in tuple(record):
            if key.startswith("gristHelper_"):
                del record[key]
    if column_type == "Text":
        for record in records:
            value = record.get("rule_id")
            record["rule_id"] = "" if value in (None, "", 0, "0") else str(value)
        return records
    if column_type != "Ref:Ref_rules":
        raise R7Error(f"unexpected Fixture_coverage.rule_id type {column_type}")

    id_to_rule = {
        int(row["id"]): str(row["rule_id"])
        for row in connection.execute("SELECT id, rule_id FROM Ref_rules")
    }
    for record in records:
        raw = record.get("rule_id")
        if raw in (None, "", 0, "0"):
            record["rule_id"] = ""
            continue
        try:
            record["rule_id"] = id_to_rule[int(raw)]
        except (KeyError, TypeError, ValueError) as exc:
            raise R7Error(f"dangling Fixture_coverage.rule_id value {raw!r}") from exc
    return records


def export_fixture_coverage(connection: sqlite3.Connection, path: Path) -> None:
    rows = stable_coverage_rows(connection)
    columns = [
        str(row[1])
        for row in connection.execute('PRAGMA table_info("Fixture_coverage")')
        if row[1] not in {"id", "manualSort"} and not str(row[1]).startswith("gristHelper_")
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def export_ref_rules(connection: sqlite3.Connection, path: Path) -> None:
    rows = [dict(row) for row in connection.execute(
        "SELECT rule_id, display_name, description, severity, source_reference, sort_order "
        "FROM Ref_rules ORDER BY sort_order, id"
    )]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SEED_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def schema_snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for table_id in ("Ref_rules", "Fixture_coverage"):
        table_ref = user_table_ref(connection, table_id)
        output[table_id] = {
            "columns": [
                {
                    key: row[key]
                    for key in (
                        "colId",
                        "type",
                        "isFormula",
                        "formula",
                        "displayCol",
                        "visibleCol",
                    )
                }
                for row in connection.execute(
                    "SELECT * FROM _grist_Tables_column WHERE parentId = ? ORDER BY parentPos, id",
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
                for row in connection.execute(f'PRAGMA table_info("{table_id}")')
            ],
        }
    return output


def assert_integrity(connection: sqlite3.Connection) -> None:
    result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise R7Error(f"SQLite integrity check failed: {result}")
