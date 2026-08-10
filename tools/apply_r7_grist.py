#!/usr/bin/env python3
"""Populate ref_rules and migrate Fixture_coverage.rule_id in a .grist copy."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

from r7_grist import (
    R7Error,
    assert_integrity,
    column_metadata,
    export_fixture_coverage,
    export_ref_rules,
    load_seed,
    schema_snapshot,
    sha256_file,
    stable_coverage_rows,
    user_table_ref,
    write_json,
)


def _quoted(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _column_sql(column: sqlite3.Row, force_integer: bool = False) -> str:
    declaration = [_quoted(str(column["name"]))]
    column_type = "INTEGER" if force_integer else str(column["type"] or "")
    if column_type:
        declaration.append(column_type)
    if column["notnull"]:
        declaration.append("NOT NULL")
    default_value = "0" if force_integer else column["dflt_value"]
    if default_value is not None:
        declaration.extend(("DEFAULT", str(default_value)))
    if column["pk"]:
        declaration.append("PRIMARY KEY")
    return " ".join(declaration)


def _ensure_helper_metadata(
    connection: sqlite3.Connection, fixture_ref: int, visible_column_ref: int
) -> int:
    formula = "$rule_id.rule_id"
    row = connection.execute(
        "SELECT id FROM _grist_Tables_column WHERE parentId = ? AND formula = ?",
        (fixture_ref, formula),
    ).fetchone()
    if row is not None:
        helper_ref = int(row[0])
    else:
        existing = {
            str(row[0])
            for row in connection.execute(
                "SELECT colId FROM _grist_Tables_column WHERE parentId = ?", (fixture_ref,)
            )
        }
        suffix = 1
        helper_id = "gristHelper_Display"
        while helper_id in existing:
            suffix += 1
            helper_id = f"gristHelper_Display{suffix}"
        helper_ref = int(
            connection.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM _grist_Tables_column").fetchone()[0]
        )
        parent_pos = connection.execute(
            "SELECT COALESCE(MAX(parentPos), 0) + 1 FROM _grist_Tables_column WHERE parentId = ?",
            (fixture_ref,),
        ).fetchone()[0]
        connection.execute(
            "INSERT INTO _grist_Tables_column "
            "(id, parentId, parentPos, colId, type, widgetOptions, isFormula, formula, label) "
            "VALUES (?, ?, ?, ?, 'Any', '', 1, ?, ?)",
            (helper_ref, fixture_ref, parent_pos, helper_id, formula, helper_id),
        )
    connection.execute(
        "UPDATE _grist_Tables_column SET type = 'Ref:Ref_rules', isFormula = 0, formula = '', "
        "displayCol = ?, visibleCol = ? WHERE parentId = ? AND colId = 'rule_id'",
        (helper_ref, visible_column_ref, fixture_ref),
    )
    return helper_ref


def _rebuild_fixture_table(
    connection: sqlite3.Connection,
    rule_to_id: dict[str, int],
    helper_name: str,
    source_is_reference: bool,
) -> None:
    old_columns = list(connection.execute('PRAGMA table_info("Fixture_coverage")'))
    old_names = [str(column["name"]) for column in old_columns]
    existing_rows = [dict(row) for row in connection.execute(
        "SELECT * FROM Fixture_coverage ORDER BY id"
    )]

    mapped_rows: list[dict[str, Any]] = []
    id_to_rule = {row_id: rule_id for rule_id, row_id in rule_to_id.items()}
    for row in existing_rows:
        raw_value = row.get("rule_id")
        stable_id: str | None
        if raw_value in (None, "", 0, "0"):
            row["rule_id"] = 0
            stable_id = None
        elif source_is_reference:
            try:
                row_id = int(raw_value)
                stable_id = id_to_rule[row_id]
            except (KeyError, TypeError, ValueError) as exc:
                raise R7Error(f"coverage row reference {raw_value!r} is dangling") from exc
            row["rule_id"] = row_id
        else:
            stable_id = str(raw_value)
            if stable_id not in rule_to_id:
                raise R7Error(f"coverage value {stable_id!r} is absent from ref_rules")
            row["rule_id"] = rule_to_id[stable_id]
        row[helper_name] = stable_id
        mapped_rows.append(row)

    definitions = [
        _column_sql(column, force_integer=(column["name"] == "rule_id"))
        for column in old_columns
    ]
    if helper_name not in old_names:
        definitions.append(f'{_quoted(helper_name)} BLOB DEFAULT NULL')
    connection.execute('DROP TABLE IF EXISTS "_r7_Fixture_coverage_new"')
    connection.execute(
        'CREATE TABLE "_r7_Fixture_coverage_new" (' + ", ".join(definitions) + ")"
    )
    insert_names = old_names + ([] if helper_name in old_names else [helper_name])
    if mapped_rows:
        placeholders = ", ".join("?" for _ in insert_names)
        connection.executemany(
            f'INSERT INTO "_r7_Fixture_coverage_new" '
            f'({", ".join(_quoted(name) for name in insert_names)}) VALUES ({placeholders})',
            [[row.get(name) for name in insert_names] for row in mapped_rows],
        )
    connection.execute('DROP TABLE "Fixture_coverage"')
    connection.execute(
        'ALTER TABLE "_r7_Fixture_coverage_new" RENAME TO "Fixture_coverage"'
    )


def apply_r7(connection: sqlite3.Connection, seed: list[dict[str, Any]]) -> dict[str, Any]:
    connection.row_factory = sqlite3.Row
    ref_rules_ref = user_table_ref(connection, "Ref_rules")
    fixture_ref = user_table_ref(connection, "Fixture_coverage")
    rule_id_ref = int(column_metadata(connection, ref_rules_ref, "rule_id")["id"])
    fixture_rule = column_metadata(connection, fixture_ref, "rule_id")

    before_rows = stable_coverage_rows(connection)
    existing_ref_rules = [dict(row) for row in connection.execute(
        "SELECT rule_id, display_name, description, severity, source_reference, sort_order "
        "FROM Ref_rules ORDER BY sort_order, id"
    )]
    if existing_ref_rules and existing_ref_rules != seed:
        raise R7Error("Ref_rules is non-empty and differs from the governed seed")

    if not existing_ref_rules:
        connection.executemany(
            "INSERT INTO Ref_rules "
            "(id, manualSort, rule_id, display_name, description, severity, source_reference, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    index,
                    index,
                    row["rule_id"],
                    row["display_name"],
                    row["description"],
                    row["severity"],
                    row["source_reference"],
                    row["sort_order"],
                )
                for index, row in enumerate(seed, 1)
            ],
        )
    connection.execute(
        "UPDATE _grist_Tables_column SET isFormula = 0, formula = '' "
        "WHERE parentId = ? AND colId IN "
        "('rule_id','display_name','description','severity','source_reference','sort_order')",
        (ref_rules_ref,),
    )

    rule_to_id = {
        str(row["rule_id"]): int(row["id"])
        for row in connection.execute("SELECT id, rule_id FROM Ref_rules")
    }
    unresolved = sorted(
        {
            str(row["rule_id"])
            for row in before_rows
            if row.get("rule_id") not in (None, "") and str(row["rule_id"]) not in rule_to_id
        }
    )
    if unresolved:
        raise R7Error(f"unresolved coverage values: {', '.join(unresolved)}")

    helper_ref = _ensure_helper_metadata(connection, fixture_ref, rule_id_ref)
    helper_name = str(
        connection.execute(
            "SELECT colId FROM _grist_Tables_column WHERE id = ?", (helper_ref,)
        ).fetchone()[0]
    )
    sqlite_rule_type = next(
        row["type"] for row in connection.execute('PRAGMA table_info("Fixture_coverage")')
        if row["name"] == "rule_id"
    )
    if str(fixture_rule["type"]) == "Text" or str(sqlite_rule_type).upper() != "INTEGER":
        _rebuild_fixture_table(
            connection,
            rule_to_id,
            helper_name,
            source_is_reference=(str(fixture_rule["type"]) == "Ref:Ref_rules"),
        )
    elif str(fixture_rule["type"]) != "Ref:Ref_rules":
        raise R7Error(f"unexpected source column type {fixture_rule['type']}")

    after_rows = stable_coverage_rows(connection)
    if before_rows != after_rows:
        raise R7Error("fixture coverage values changed across stable-ID comparison")
    assert_integrity(connection)
    return {
        "coverage_row_count_before": len(before_rows),
        "coverage_row_count_after": len(after_rows),
        "coverage_values_preserved": before_rows == after_rows,
        "ref_rules_count": connection.execute("SELECT COUNT(*) FROM Ref_rules").fetchone()[0],
        "ref_rules_unique_ids": connection.execute(
            "SELECT COUNT(DISTINCT rule_id) FROM Ref_rules"
        ).fetchone()[0],
        "severity_counts": {
            row["severity"]: row["count"]
            for row in connection.execute(
                "SELECT severity, COUNT(*) AS count FROM Ref_rules GROUP BY severity ORDER BY severity"
            )
        },
        "fixture_rule_column_type": column_metadata(
            connection, fixture_ref, "rule_id"
        )["type"],
        "fixture_rule_visible_column": "Ref_rules.rule_id",
        "sqlite_integrity": "ok",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="source .grist document")
    parser.add_argument("seed", type=Path, help="generated ref_rules CSV")
    parser.add_argument("output", type=Path, help="new migrated .grist document")
    parser.add_argument("proof_dir", type=Path, help="directory for R7 proof artifacts")
    parser.add_argument("--force", action="store_true", help="replace an existing output copy")
    args = parser.parse_args(argv)

    if args.output.exists() and not args.force:
        print(f"R7 migration failed: output exists: {args.output}", file=sys.stderr)
        return 1
    try:
        seed = load_seed(args.seed)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.source, args.output)
        connection = sqlite3.connect(args.output)
        connection.row_factory = sqlite3.Row
        try:
            before_schema = schema_snapshot(connection)
            before_coverage = stable_coverage_rows(connection)
            with connection:
                result = apply_r7(connection, seed)
            after_schema = schema_snapshot(connection)
            after_coverage = stable_coverage_rows(connection)
            export_ref_rules(connection, args.proof_dir / "ref_rules_export.csv")
            export_fixture_coverage(connection, args.proof_dir / "fixture_coverage_export.csv")
        finally:
            connection.close()

        write_json(args.proof_dir / "schema_before.json", before_schema)
        write_json(args.proof_dir / "schema_after.json", after_schema)
        write_json(args.proof_dir / "fixture_coverage_before.json", before_coverage)
        write_json(args.proof_dir / "fixture_coverage_after.json", after_coverage)
        result.update(
            {
                "seed_sha256": sha256_file(args.seed),
                "ref_rules_export_sha256": sha256_file(args.proof_dir / "ref_rules_export.csv"),
                "fixture_coverage_export_sha256": sha256_file(
                    args.proof_dir / "fixture_coverage_export.csv"
                ),
                "output_grist_sha256": sha256_file(args.output),
            }
        )
        write_json(args.proof_dir / "r7_result.json", result)
    except (OSError, sqlite3.Error, R7Error) as exc:
        print(f"R7 migration failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
