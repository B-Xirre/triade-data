# TRIADE Data Pipeline

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

## R7 rule-reference migration

R7 is implemented by standard-library-only tools:

```text
python tools/generate_ref_rules.py <validation-index.md> content/csv/ref_rules.csv
python tools/apply_r7_grist.py <source.grist> content/csv/ref_rules.csv <output.grist> proof/r7
python tools/export_grist.py <output.grist> <csv-output-directory>
python -m unittest -v tests/test_r7.py
```

`generate_ref_rules.py` fails unless the current index yields exactly 148 unique
rules with the 86 Critical / 48 High / 14 Medium split. `apply_r7_grist.py` writes a
new document copy, rejects unresolved coverage IDs, migrates the Reference
column, and records before/after proof artifacts. `export_grist.py` is currently
R7-scoped; it is not the complete Grist-to-CSV pipeline.
