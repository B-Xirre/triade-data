#!/usr/bin/env python3
"""Populate the M10 dependency layer in a new offline .grist document copy."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path

from m10_dependencies import (
    M10DependencyError,
    apply_dependencies,
    dependency_schema_snapshot,
    export_snapshot,
    load_seed,
    stable_snapshot,
)
from r7_grist import sha256_file, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="R7-complete source .grist document")
    parser.add_argument("seed_dir", type=Path, help="directory containing four dependency CSVs")
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
        before_sha = sha256_file(args.source)
        connection = sqlite3.connect(args.output)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                result = apply_dependencies(connection, seed)
            snapshot = stable_snapshot(connection)
            schema = dependency_schema_snapshot(connection)
        finally:
            connection.close()

        export_snapshot(snapshot, args.proof_dir / "export")
        seed_hashes = {
            path.name: sha256_file(path)
            for path in sorted(args.seed_dir.glob("*.csv"))
            if path.name in {
                "chassis_profiles.csv",
                "integrity_profiles.csv",
                "integrity_states.csv",
                "construction_profiles.csv",
            }
        }
        export_hashes = {
            path.name: sha256_file(path)
            for path in sorted((args.proof_dir / "export").glob("*.csv"))
        }
        result.update({
            "source_document": str(args.source),
            "output_document": str(args.output),
            "source_sha256": before_sha,
            "output_sha256": sha256_file(args.output),
            "seed_files": sorted(path.name for path in args.seed_dir.glob("*_profiles.csv"))
            + ["integrity_states.csv"],
            "seed_sha256": seed_hashes,
            "export_sha256": export_hashes,
            "seed_export_byte_identical": seed_hashes == export_hashes,
            "centralised_design_decisions": [
                "Standard Shield integrity path stable -> cracked -> broken_guard (M·2A.6)",
                "Medium weight class uses barycentre_well (M·2A.7)",
            ],
        })
        write_json(args.proof_dir / "m10_dependencies_result.json", result)
        write_json(args.proof_dir / "m10_dependencies_snapshot.json", snapshot)
        write_json(args.proof_dir / "m10_dependencies_schema.json", schema)
    except (OSError, sqlite3.Error, M10DependencyError, KeyError) as exc:
        if args.output.exists():
            args.output.unlink()
        print(f"M10 dependency population failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
