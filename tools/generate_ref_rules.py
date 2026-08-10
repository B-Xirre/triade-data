#!/usr/bin/env python3
"""Generate the protected Triade ref_rules seed from the governed rule index."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


EXPECTED_COUNTS = {"critical": 81, "high": 48, "medium": 14}
EXPECTED_TOTAL = sum(EXPECTED_COUNTS.values())
RULE_ID_RE = re.compile(r"^[A-Z]+-([CHM])(\d+)$")
SEVERITY_BY_LETTER = {"C": "critical", "H": "high", "M": "medium"}
SEVERITY_HEADINGS = {
    "## 2. Critical": "critical",
    "## 3. High": "high",
    "## 4. Medium": "medium",
}
FIELDNAMES = (
    "rule_id",
    "display_name",
    "description",
    "severity",
    "source_reference",
    "sort_order",
)


class SeedError(RuntimeError):
    """Raised when the governed index cannot produce a valid R7 seed."""


@dataclass(frozen=True)
class Rule:
    rule_id: str
    display_name: str
    description: str
    severity: str
    source_reference: str
    sort_order: int

    def as_row(self) -> dict[str, str | int]:
        return {name: getattr(self, name) for name in FIELDNAMES}


def _markdown_cells(line: str) -> list[str]:
    """Split one simple Markdown table row, retaining escaped pipe characters."""
    text = line.strip()
    if not (text.startswith("|") and text.endswith("|")):
        return []
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in text[1:-1]:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def parse_index(path: Path) -> list[Rule]:
    severity: str | None = None
    parsed: list[Rule] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for prefix, value in SEVERITY_HEADINGS.items():
            if line.startswith(prefix):
                severity = value
                break

        cells = _markdown_cells(line)
        if len(cells) != 3 or not cells[0].startswith("**"):
            continue
        rule_id = cells[0].removeprefix("**").removesuffix("**")
        match = RULE_ID_RE.fullmatch(rule_id)
        if not match:
            continue
        if severity is None:
            raise SeedError(f"{path}:{line_number}: rule appears before a severity heading")
        expected_severity = SEVERITY_BY_LETTER[match.group(1)]
        if severity != expected_severity:
            raise SeedError(
                f"{path}:{line_number}: {rule_id} is under {severity}, expected {expected_severity}"
            )
        description, source_reference = cells[1], cells[2]
        if not description or not source_reference:
            raise SeedError(f"{path}:{line_number}: {rule_id} has an empty required field")
        parsed.append(
            Rule(
                rule_id=rule_id,
                display_name=rule_id,
                description=description,
                severity=severity,
                source_reference=source_reference,
                sort_order=len(parsed) + 1,
            )
        )

    validate_rules(parsed)
    return parsed


def validate_rules(rules: list[Rule]) -> None:
    ids = [rule.rule_id for rule in rules]
    duplicates = sorted(rule_id for rule_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise SeedError(f"duplicate rule IDs: {', '.join(duplicates)}")
    if len(rules) != EXPECTED_TOTAL:
        raise SeedError(f"expected {EXPECTED_TOTAL} rules, found {len(rules)}")
    counts = Counter(rule.severity for rule in rules)
    if counts != Counter(EXPECTED_COUNTS):
        raise SeedError(f"severity split mismatch: expected {EXPECTED_COUNTS}, found {dict(counts)}")
    expected_order = list(range(1, EXPECTED_TOTAL + 1))
    if [rule.sort_order for rule in rules] != expected_order:
        raise SeedError("sort_order is not the deterministic 1-based index order")


def write_seed(rules: list[Rule], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rule.as_row() for rule in rules)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path, help="governed TRIADE Validation Rules Index Markdown")
    parser.add_argument("output", type=Path, help="destination ref_rules CSV")
    args = parser.parse_args(argv)
    try:
        rules = parse_index(args.index)
        write_seed(rules, args.output)
    except (OSError, SeedError) as exc:
        print(f"ref_rules seed generation failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"generated {len(rules)} rules "
        f"({EXPECTED_COUNTS['critical']}/{EXPECTED_COUNTS['high']}/{EXPECTED_COUNTS['medium']}) "
        f"at {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
