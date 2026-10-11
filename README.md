# TRIADE Data Pipeline

## Triade Tuning Lab

The locally deployed versioned workbench and combat mathematics framework use authoring schema 1.1.0 and lab execution schema 1.0.0. See [lab deployment and usage](lab/README.md). The 0.46.0 canonical snapshot below remains the frozen regression baseline; current lab authoring is `content/canonical/authoring-1.1.0.json`.

## Authority model

Grist
→ human authoring

CSV
→ deterministic interchange / staging

JSON Schema
→ structural contract

Canonical JSON
→ approved source of truth

DuckDB
→ rebuildable catalogue, validation and analytics

Parquet
→ immutable simulation and game trace data

Git / GitHub
→ version authority

## Triade 0.46.0 authoring contracts

Schema 1.0.0 covers 108 authoring tables, including combat protection scopes,
shield partition budgets, magic attributes, Ward selection, Faculty authorization,
fixed-point parameters and isolated fixture values. The versioned manifest pins
245 source rules (175 Critical / 56 High / 14 Medium).

```text
python tools/run_regression.py
python tools/authoring046.py --doc-id <candidate-id> --registry schema/authoring-registry-1.0.0.json --manifest content/authoring-manifest.json --schema schema/authoring.schema.json --output <export-directory>
python tools/migrate_authoring046.py --candidate <candidate-id> --active <active-id> --backup <backup-id> --registry schema/authoring-registry-1.0.0.json --seed content/authoring-seed-0.46.0.json
```

The API client reads loopback Grist using environment credentials. Migration is
candidate-only; its default mode previews schema changes and `--apply` performs
the guarded schema and stable-ID seed migration. Reference targets must exist
before their dependents. Access rules and stable-ID display formulas are separately
verified release operations, rather than freely editable authoring facts.

Canonical exports use stable References, conservative integers, explicit nulls for
unset parameters and no display floats. `--profile approved-runtime` intentionally
rejects this release: tuning coefficients and runtime integration remain open.
The mathematical helpers and fixtures validate contracts; they do not constitute
a playable combat implementation or encounter balance validation.

The historical index test can be enabled with `TRIADE_VALIDATION_RULES_INDEX`
pointing to its frozen 0.29.0 validation index. Historical golden datasets remain
unchanged.

## Historical R7 rule-reference migration

R7 is implemented by standard-library-only tools:

```text
python tools/generate_ref_rules.py <validation-index.md> content/csv/ref_rules.csv
python tools/apply_r7_grist.py <source.grist> content/csv/ref_rules.csv <output.grist> proof/r7
python tools/export_grist.py <output.grist> <csv-output-directory>
python -m unittest -v tests/test_r7.py
```

Without a versioned manifest, `generate_ref_rules.py` retains the historical
148-rule contract (86 Critical / 48 High / 14 Medium). Current 0.46.0 generation
requires `--manifest content/authoring-manifest.json`. `apply_r7_grist.py` writes a
new document copy, rejects unresolved coverage IDs, migrates the Reference
column, and records before/after proof artifacts. `export_grist.py` is currently
R7-scoped; it is not the complete Grist-to-CSV pipeline.
