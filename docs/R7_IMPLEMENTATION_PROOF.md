# R7 implementation proof

**Aligned Triade version:** 0.21.0

**Executed:** 10 August 2026

**Scope:** generated `ref_rules` seed and `Fixture_coverage.rule_id` migration

**Authority boundary:** technical implementation evidence only; no design rule changed

## Inputs

- governed `TRIADE-Validation_Rules_Index-0_21_0.md`;
- supplied `Triade - Equipment Authoring.grist` working copy;
- supplied `triade-data` repository.

The home-source derivability of all 143 rules is inherited from the governed
0.21.0 central proof that closed `◈P7`. This run independently verifies the
compiled row set, stable IDs, non-empty source locators, severity split and
implementation behavior; it does not re-author or re-proof source rules.

## Executed results

| Gate | Result |
| --- | --- |
| Generated rows | 143 |
| Unique non-empty `rule_id` values | 143 |
| Severity split | 81 Critical / 48 High / 14 Medium |
| `sort_order` | Exact sequence 1–143 |
| Seed regeneration | Byte-identical |
| Seed/export SHA-256 | `64777d393800814f683a4aed711aa00cf97f565996a010a1ccb8ad267d4d624c` |
| Coverage rows before/after | 0 / 0 |
| Coverage values preserved | Yes |
| Migrated Grist type | `Ref:Ref_rules` |
| Shown stable-ID column | `Ref_rules.rule_id` |
| Physical SQLite type/default | `INTEGER DEFAULT 0` |
| Export behavior | Stable rule IDs; never Grist row numbers |
| Unresolved-ID behavior | Migration rejected before commit |
| Idempotent rerun | Passed; identical seed/export/document hashes |
| SQLite integrity | `ok` |
| Updated `.grist` SHA-256 | `2a9b7f1b9b6e8810cbbf69f9182dfe779be17e6c3046da14420ee4d26fe28a80` |

The supplied `Fixture_coverage` table was empty, so the live-copy preservation
proof is legitimately 0→0. A synthetic populated-row test migrated `P-C8`,
then proved the CSV export emitted `P-C8` rather than its numeric Grist row ID.
A separate `P-C999` case proved unresolved IDs abort the migration.

## Evidence files

- `content/csv/ref_rules.csv` — governed generated seed;
- `proof/r7/schema_before.json` and `schema_after.json` — Grist/SQLite schema proof;
- `proof/r7/fixture_coverage_before.json` and `fixture_coverage_after.json` — value snapshot;
- `proof/r7/ref_rules_export.csv` — deterministic seed round trip;
- `proof/r7/fixture_coverage_export.csv` — stable-ID export surface;
- `proof/r7/r7_result.json` — machine-readable acceptance result;
- `tests/test_r7.py` — regeneration and stable-reference export tests.

## Remaining operational boundary

The updated file is an offline exact document copy. Importing or replacing the
active self-hosted Grist document remains an operator action; this run did not
connect to or mutate the running `localhost:8484` instance. The complete
all-table deterministic exporter and canonical JSON compiler remain later
Stage 2 work.
