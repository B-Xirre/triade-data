#!/usr/bin/env python3
"""R7-scoped deterministic exports from an offline .grist document copy.

This intentionally exports only the two R7 tables. It is not yet the complete
Grist-to-CSV pipeline described by the technical specification.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from r7_grist import R7Error, export_fixture_coverage, export_ref_rules


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        connection = sqlite3.connect(f"file:{args.document}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            export_ref_rules(connection, args.output_dir / "ref_rules.csv")
            export_fixture_coverage(connection, args.output_dir / "fixture_coverage.csv")
        finally:
            connection.close()
    except (OSError, sqlite3.Error, R7Error) as exc:
        print(f"R7 export failed: {exc}", file=sys.stderr)
        return 1
    print(f"exported R7 tables to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
