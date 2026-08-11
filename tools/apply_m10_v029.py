#!/usr/bin/env python3
"""Build the v0.29.0 M10 faculties/fixtures Grist candidate."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from m10_equipment import TABLE_FILES as EQUIPMENT_FILES
from m10_equipment import load_seed as load_equipment_seed
from m10_equipment import stable_snapshot as equipment_snapshot
from m10_faculties_fixtures import TABLE_FILES as FIXTURE_FILES
from m10_faculties_fixtures import apply_faculties_fixtures
from m10_faculties_fixtures import export_snapshot as export_fixture_snapshot
from m10_faculties_fixtures import load_seed as load_fixture_seed
from m10_faculties_fixtures import schema_snapshot as fixture_schema_snapshot
from m10_faculties_fixtures import stable_snapshot as fixture_snapshot
from r7_grist import R7Error, export_ref_rules, load_seed as load_rule_seed
from r7_grist import sha256_file, write_json
from v029_reconciliation import (
    V029ReconciliationError,
    install_m_c11_previews,
    reconcile_equipment,
    upgrade_ref_rules,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="adopted M10-equipment .grist copy")
    parser.add_argument("seed_dir", type=Path, help="directory containing current CSV seeds")
    parser.add_argument("output", type=Path, help="new v0.29.0 Grist candidate")
    parser.add_argument("proof_dir", type=Path, help="directory for proof artifacts")
    parser.add_argument("--force", action="store_true", help="replace an existing output")
    args = parser.parse_args(argv)

    if args.output.exists() and not args.force:
        print(f"output already exists: {args.output}", file=sys.stderr)
        return 1
    try:
        rule_seed = load_rule_seed(args.seed_dir / "ref_rules.csv")
        equipment_seed = load_equipment_seed(args.seed_dir)
        fixture_seed = load_fixture_seed(args.seed_dir)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.source, args.output)
        source_hash = sha256_file(args.source)
        connection = sqlite3.connect(args.output)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                rule_result = upgrade_ref_rules(connection, rule_seed)
                equipment_result = reconcile_equipment(connection, equipment_seed)
                fixture_result = apply_faculties_fixtures(connection, fixture_seed)
                preview_result = install_m_c11_previews(connection)
            stable_equipment = equipment_snapshot(connection)
            stable_fixtures = fixture_snapshot(connection)
            schema = fixture_schema_snapshot(connection)
            severity = Counter(
                str(row["severity"])
                for row in connection.execute("SELECT severity FROM Ref_rules")
            )
        finally:
            connection.close()

        args.proof_dir.mkdir(parents=True, exist_ok=True)
        export_fixture_snapshot(stable_fixtures, args.proof_dir / "export")
        export_ref_rules_sqlite = sqlite3.connect(args.output)
        export_ref_rules_sqlite.row_factory = sqlite3.Row
        try:
            export_ref_rules(export_ref_rules_sqlite, args.proof_dir / "export" / "ref_rules.csv")
        finally:
            export_ref_rules_sqlite.close()

        seed_files = list(EQUIPMENT_FILES.values()) + list(FIXTURE_FILES.values()) + ["ref_rules.csv"]
        seed_hashes = {name: sha256_file(args.seed_dir / name) for name in seed_files}
        export_hashes = {
            name: sha256_file(args.proof_dir / "export" / name)
            for name in list(FIXTURE_FILES.values()) + ["ref_rules.csv"]
        }
        result = {
            "aligned_triade_version": "0.29.0",
            "source_document": str(args.source),
            "output_document": str(args.output),
            "source_sha256": source_hash,
            "output_sha256": sha256_file(args.output),
            "rule_reconciliation": rule_result,
            "r7_count": sum(severity.values()),
            "r7_severity_split": dict(sorted(severity.items())),
            "equipment_reconciliation": equipment_result,
            "fixture_population": fixture_result,
            "m_c11_preview": preview_result,
            "seed_sha256": seed_hashes,
            "export_sha256": export_hashes,
            "fixture_seed_export_byte_identical": all(
                seed_hashes[name] == export_hashes[name]
                for name in FIXTURE_FILES.values()
            ),
            "rule_seed_export_byte_identical": (
                seed_hashes["ref_rules.csv"] == export_hashes["ref_rules.csv"]
            ),
            "equipment_seed_exact_readback": stable_equipment == equipment_seed,
            "fixture_seed_exact_readback": stable_fixtures == fixture_seed,
            "verified_design_sources": [
                "T·A4.8a", "E·F.1", "M·2A.10a", "M·2A.11",
                "M-C9", "M-C10", "M-C11", "P·10.2–10.7",
            ],
            "blockers": [
                "◇P6 blocks canonical schema/package versioning",
                "◇P3 / S-P01 blocks authoritative fixed-point trace persistence",
                "◇P8 blocks fixture enemy and encounter-member field sets",
                "◇P10 leaves the protected equipment-tag registry empty",
                "◇M13 blocks only tied-highest off-hand profiles",
            ],
            "unresolved_intake": [
                "TS-M10F-01 concrete faculty definitions",
                "TS-M10F-02 normalized build-to-faculty assignments",
                "TS-V029-01 stale P·10.3 shield profile",
                "TS-V029-02 stale P·10.5 Medium-size fixture values",
                "TS-V029-03 actor-lineage and physique authoring grain",
            ],
        }
        write_json(args.proof_dir / "m10_v029_result.json", result)
        write_json(args.proof_dir / "m10_v029_fixture_snapshot.json", stable_fixtures)
        write_json(args.proof_dir / "m10_v029_schema.json", schema)
    except (OSError, sqlite3.Error, KeyError, ValueError, R7Error) as exc:
        if args.output.exists():
            args.output.unlink()
        print(f"v0.29.0 M10 Grist reconciliation failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
