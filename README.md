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

`generate_ref_rules.py` fails unless the index yields exactly 143 unique rules
with the 81 Critical / 48 High / 14 Medium split. `apply_r7_grist.py` writes a
new document copy, rejects unresolved coverage IDs, migrates the Reference
column, and records before/after proof artifacts. `export_grist.py` is currently
R7-scoped; it is not the complete Grist-to-CSV pipeline.

## M10 dependency population

The first M10 population stage is stored as four deterministic CSV seeds:

```text
content/csv/chassis_profiles.csv
content/csv/integrity_profiles.csv
content/csv/integrity_states.csv
content/csv/construction_profiles.csv
```

Apply them to a fresh R7-complete document copy:

```bash
python tools/apply_m10_dependencies.py \
  "Triade - Equipment Authoring-R7.grist" \
  content/csv \
  "Triade - Equipment Authoring-M10-dependencies.grist" \
  proof/m10_dependencies
```

The command rejects divergent non-empty target tables, resolves Grist
References by stable ID, preserves unresolved `_q` values as null, exports all
four tables, and proves byte-identical seed/export. See
`docs/M10_DEPENDENCY_IMPLEMENTATION_PROOF.md`.

## M10 equipment population

The next deterministic seed adds the five locked M10 equipment revisions and
their source-owned child records:

```text
content/csv/equipment.csv
content/csv/equipment_text.csv
content/csv/equipment_tags.csv
content/csv/slot_occupancy.csv
content/csv/damage_profile_entries.csv
content/csv/defence_profile_entries.csv
```

Apply them to a dependency-complete copy:

```bash
python tools/apply_m10_equipment.py \
  "Triade - Equipment Authoring-M10-dependencies.grist" \
  content/csv \
  "Triade - Equipment Authoring-M10-equipment.grist" \
  proof/m10_equipment
```

The migration also adds `barycentre_well` to the
`construction_profiles.bridge2_mechanism` Choice metadata and assigns it to the
Standard Shield. It rejects unresolved References and divergent target rows,
is idempotent, and proves byte-identical six-table seed/export. The shield's
numeric defence rating remains null and equipment tags remain empty until an
authoritative budget scale and protected tag registry exist. See
`docs/M10_EQUIPMENT_IMPLEMENTATION_PROOF.md`.
