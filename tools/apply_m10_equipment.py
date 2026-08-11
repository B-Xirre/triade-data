#!/usr/bin/env python3
"""Populate the five M10 equipment revisions in a new offline Grist copy."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from m10_equipment import (
    M10EquipmentError,
    TABLE_FILES,
    apply_equipment,
    equipment_schema_snapshot,
    export_snapshot,
    load_seed,
    stable_snapshot,
)
from r7_grist import sha256_file, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="adopted M10-dependency .grist copy")
    parser.add_argument("seed_dir", type=Path, help="directory containing equipment CSVs")
    parser.add_argument("output", type=Path, help="new populated .grist document")
    parser.add_argument("proof_dir", type=Path, help="directory for proof artifacts")
    parser.add_argument("--force", action="store_true", help="replace an existing output copy")
    args = parser.parse_args(argv)

    if args.output.exists() and not args.force:
        print(f"output already exists: {args.output}", file=sys.stderr)
        return 1
    try:
        seed = load_seed(args.seed_dir)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.source, args.output)
        source_hash = sha256_file(args.source)
        connection = sqlite3.connect(args.output)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                result = apply_equipment(connection, seed)
            snapshot = stable_snapshot(connection)
            schema = equipment_schema_snapshot(connection)
            r7_rows = [dict(row) for row in connection.execute(
                "SELECT severity FROM Ref_rules ORDER BY id"
            )]
            dependency_counts = {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in (
                    "Chassis_profiles", "Integrity_profiles", "Integrity_states",
                    "Construction_profiles",
                )
            }
        finally:
            connection.close()

        export_snapshot(snapshot, args.proof_dir / "export")
        seed_hashes = {
            file_name: sha256_file(args.seed_dir / file_name)
            for file_name in TABLE_FILES.values()
        }
        export_hashes = {
            file_name: sha256_file(args.proof_dir / "export" / file_name)
            for file_name in TABLE_FILES.values()
        }
        severity = Counter(str(row["severity"]).lower() for row in r7_rows)
        result.update({
            "source_document": str(args.source),
            "output_document": str(args.output),
            "source_sha256": source_hash,
            "output_sha256": sha256_file(args.output),
            "seed_sha256": seed_hashes,
            "export_sha256": export_hashes,
            "seed_export_byte_identical": seed_hashes == export_hashes,
            "dependency_counts": dependency_counts,
            "r7_count": len(r7_rows),
            "r7_severity_split": dict(sorted(severity.items())),
            "verified_design_sources": [
                "P·10.3", "M·2A.6", "M·2A.7", "M·2A.9", "M·2A.11"
            ],
            "unresolved": [
                "Standard Shield numeric defence rating and pooled-budget scale",
                "protected Ref_tags registry is empty",
                "canonical equipment schema version is not implemented",
            ],
        })
        write_json(args.proof_dir / "m10_equipment_result.json", result)
        write_json(args.proof_dir / "m10_equipment_snapshot.json", snapshot)
        write_json(args.proof_dir / "m10_equipment_schema.json", schema)
    except (OSError, sqlite3.Error, M10EquipmentError, KeyError) as exc:
        if args.output.exists():
            args.output.unlink()
        print(f"M10 equipment population failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
