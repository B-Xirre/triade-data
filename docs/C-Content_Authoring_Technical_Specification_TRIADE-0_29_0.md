# Triade — Content Authoring Technical Specification

**Version:** 0.29.0
**Aligned to Triade:** v0.29.0
**Date:** 12 August 2026
**Status:** Stage 2 authoring-schema baseline complete; M10 dependency and equipment layers adopted; v0.29.0 rules, shield arithmetic, faculties, fixture records, and off-hand preview populated and proved in an offline candidate
**Classification:** **Registered technical document.** Implements P; holds no game-design authority  
**Design authority:** **P — Content Pipeline & Data Model**; game meaning remains in T/M/K/H/E/W/G/V/L

---

## 0. Purpose and authority

This document records the **concrete technical implementation** of P's authoring layer for the Triade content pipeline. It consolidates the repository bootstrap, local Grist setup, protected reference layer, current authoring-table schema, Grist column behavior, Stage 2 implementation sequence, and the unresolved implementation gaps discovered while building the schema.

It does **not** redefine game mechanics. **If this specification conflicts with a design document, the design document wins and this file is patched** — never the reverse. P·2.1 and P·2.3 state the same rule from the other side.

**What a technical document is.** It records how a design-owned system is *realized* in a particular tool at a particular version. It may hold column names, container versions and file layouts. It may not hold a number, a rule or a term that no design document owns — anything of that kind belongs in its home document first, and appears here only as a reference.

The implementation contract remains:

```text
Grist authoring façade
  ↓ deterministic export
CSV interchange
  ↓ compile + validate
canonical ordered JSON + JSON Schema          ← source of truth
  ↓ import
DuckDB operational catalogue                 ← rebuildable
  ↓ instantiate
◈M10 fixtures + headless simulation
  ↓
attributed traces → partitioned Parquet
  ↓
DuckDB analytics / signatures / findings
```

The direction is one-way: authored text/data → canonical JSON → database. DuckDB and Parquet are never authoring authorities.

---

## 1. Current implementation checkpoint

| Area | State |
| --- | --- |
| Repository | Candidate patch is based on the post-`8d2776b` implementation checkpoint and adds the v0.29.0 rule/equipment reconciliation, faculty/fixture population, M-C11 preview formulas, regression tests, and proof artifacts; operator landing remains pending |
| Local authoring | R7, the M10 dependency layer, and the five equipment records are adopted into active document `3TwLJyu7fythPjAj1e1424`; a v0.29.0 faculties/fixtures candidate is produced offline and awaits operator adoption |
| Reference layer | **17 protected reference tables complete** |
| Current authoring layer | **22 authoring tables complete for the ◈M10 vertical slice** |
| Grist References | Target tables and shown stable-ID columns verified |
| Choice/Checkbox configuration | Verified; `construction_profiles.bridge2_mechanism` now carries `edm_damping`, `home_well_strengthening`, `barycentre_well`, `none` |
| Calculated fields | Ten intended normal Formula columns verified: the inherited six plus four M-C11 loadout-preview columns; no Trigger Formula is required |
| Authoring fields in empty tables | May remain Grist **Empty Columns** until first entry; populated dependency/equipment/faculty/fixture columns were converted to Data Columns (`isFormula = 0`) and verified; derived identifiers/floors and the four loadout previews remain normal Formula columns |
| `ref_rules` | **v0.29.0 candidate complete:** 148 generated rows; 148 unique IDs; 86 Critical / 48 High / 14 Medium; deterministic seed/export hash proved |
| `fixture_coverage.rule_id` | **R7 complete on the supplied copy:** `Reference → ref_rules`, shown by `rule_id`; existing row/value preservation proved at 0→0 and populated behavior covered by a synthetic migration/export test |
| `ref_tags` | Empty at current checkpoint |
| ◈M10 data | **Dependency/equipment adopted; v0.29.0 reconciliation complete in candidate:** Standard Shield 1 offence + 1 Physical defence pip; 5 faculty identities, 0 faculty profiles, 5 builds, 45 stat weights, 7 equipment loadouts, 5 scalar encounters, and 29 coverage rows (12 proof declarations / 17 explicit gaps) |
| Canonical JSON schemas | Bootstrap placeholders only; implementation pending |
| DuckDB catalogue | SQL bootstrap only; import implementation pending |
| Headless sim/traces | Not built yet |
| ◇P3 fixed-point scale | **Open; no persisted trace data may be treated as authoritative before it is resolved** |
| ◈P7 source-rule defect | **CLOSED 0.20.0.** No longer a Stage 2c exit condition |

> **Re-proofed and implemented against 0.29.0 — 12 Aug 2026.** The dependency and equipment candidates were adopted by the operator and landed at repository commit `8d2776b`. The current population was executed from the post-adoption Grist backup, not from a pre-adoption candidate.
>
> **Current verification boundary.** *Mechanically executed on a fresh post-equipment copy:* 143→148 stable-ID rule reconciliation; Standard Shield 1/1 pip split; five faculty identities; five builds; 45 stat weights; seven equipment assignments; five scalar encounter shells; 29 coverage records; four M-C11 formula previews; byte-identical eight-table rule/fixture export; exact idempotence; unresolved-reference and `◇M13` tie rejection before persistence; 12/12 regression tests; and SQLite integrity. *Not yet executed:* operator adoption, concrete faculty profiles, build-to-faculty assignment, actor-lineage/physique authoring, enemy/encounter membership, canonical JSON, DuckDB, simulation, or traces.

## 1.1 Completed implementation stages

1. Repository and directory bootstrap.
2. Dockerized local Grist installation and persistence verification.
3. Reference taxonomy design and population.
4. v0.16 reconciliation: `shield` confirmed as a distinct seventh category.
5. Stage 2 core-table creation.
6. Full Reference wiring and shown-ID verification.
7. Formula/Choice/Checkbox review.
8. Schema checkpoint passed.
9. R7 candidate adopted into the active document and centrally validated.
10. M10 dependency layer populated, proved and adopted into the active document.
11. Five M10 equipment revisions and their text/damage/occupancy/shield-defence child records populated, proved, adopted, and committed as `8d2776b`.
12. v0.29.0 protected-rule reconciliation, Standard Shield 1/1 split, five faculty identities, unblocked fixture records, and M-C11 loadout previews populated and proved in an offline candidate.

**Next:** adopt the v0.29.0 candidate, land the repository patch, and centrally reconcile `TS-M10F-01`, `TS-M10F-02`, and `TS-V029-01`–`03` before complete faculty-, lineage-, and enemy-bearing fixture instantiation.

---

## 2. Repository baseline

```text
triade-data/
├── .gitignore
├── README.md
├── requirements.txt
├── grist/
│   ├── docker-compose.yml
│   ├── .env               # ignored
│   └── persist/           # ignored/runtime
├── schema/
│   ├── common.schema.json
│   ├── equipment.schema.json
│   ├── affix.schema.json
│   ├── faculty.schema.json
│   ├── fixture.schema.json
│   └── trace.schema.json
├── content/
│   ├── csv/
│   └── canonical/
├── sql/
│   ├── 001_schemas.sql
│   ├── 010_reference.sql
│   ├── 020_content.sql
│   ├── 030_fixture.sql
│   ├── 040_validation.sql
│   └── 050_analytics.sql
├── tools/
│   ├── export_grist.py
│   ├── import_duckdb.py
│   ├── compile_json.py
│   ├── validate_json.py
│   └── validate_content.py
├── warehouse/
├── lake/
│   ├── traces/
│   └── signatures/
├── tests/
│   └── fixtures/
│       └── m10/
│           ├── README.md
│           ├── expected/
│           └── snapshots/
└── docs/
```

### 2.1 Bootstrap state

- The six JSON Schema files exist as placeholders.
- SQL bootstrap establishes the logical schemas: `staging`, `ref`, `content`, `generation`, `fixture`, `runtime`, `trace`, `analytics`, `audit`.
- Python tools exist as placeholders.
- `requirements.txt` currently carries the initial bootstrap dependencies: `duckdb`, `jsonschema`, `requests`, `pyarrow`, `pytest`.
- P's validation stack additionally requires **Pydantic v2 + Pandera** before record/table validation is implemented.
- Raw DuckDB files, Grist persistence, raw trace/signature lakes, environment files, Python artefacts and editor artefacts are ignored from Git.
- Empty tracked directories use `.gitkeep` where required.
- No raw Parquet belongs in Git.

---

## 3. Grist implementation conventions

### 3.1 Machine-facing identifiers

- Table IDs and column IDs use **lowercase snake_case**.
- Implementation-step numbers such as `2.3.1` are documentation/checklist numbers only and are **never part of table names**.
- Domain IDs are authored explicitly. Grist's hidden row ID is never a canonical domain ID.
- Repeatable values are child rows, never delimited strings in one cell.

### 3.2 Column notation

This document uses the agreed notation:

```text
Text
Integer
Numeric
DateTime
Choice → value1 / value2 / ...
Toggle → Checkbox
Reference → target_table → shown_stable_id_column
Formula → result_type
```

Every Reference must show the **stable ID column**, not a Grist row number.

### 3.3 Grist column behavior

An unused typed authoring column may remain an **Empty Column**. On first manual cell entry Grist converts it to a Data Column. Manual conversion before data entry is unnecessary.

Only genuine calculated fields are explicit **Formula Columns**. The current ten are:

| Table | Formula column |
| --- | --- |
| `equipment` | `equipment_revision_id` |
| `faculties` | `faculty_revision_id` |
| `fixture_builds` | `floor_sum` |
| `fixture_builds` | `floor_valid` |
| `triade_effects` | `vector_sum_q` |
| `triade_effects` | `vector_valid` |
| `fixture_loadouts` | `base_pip_total` |
| `fixture_loadouts` | `m_c11_state` |
| `fixture_loadouts` | `effective_pip_total` |
| `fixture_loadouts` | `effective_damage_preview` |

These are normal Formula columns, **not Trigger Formulas**.

### 3.4 Formula definitions

`equipment.equipment_revision_id`:

```python
if not $equipment_id or not $revision_number:
    return ""
return $equipment_id + "@" + str($revision_number)
```

`faculties.faculty_revision_id`:

```python
if not $faculty_id or not $revision_number:
    return ""
return $faculty_id + "@" + str($revision_number)
```

`fixture_builds.floor_sum`:

```python
$floor_m + $floor_f + $floor_i
```

`fixture_builds.floor_valid`:

```python
if not $fixture_build_id:
    return False
return (
    $floor_sum <= 0.45
    and max($floor_m, $floor_f, $floor_i) <= 0.25
)
```

`triade_effects.vector_sum_q`:

```python
$dm_q + $df_q + $di_q
```

`triade_effects.vector_valid`:

```python
if not $effect_id:
    return False
return $vector_sum_q == 0
```

### 3.5 Revision and protection behavior

- `approved` revisions are immutable; a change creates a new revision.
- `content_hash` is reserved for generated canonical-content hashes.
- `can_drop`, `can_salvage`, `can_reroll`, `can_sell`, `can_discard` are **not authoring columns**; P-C6 requires them to be derived.
- `is_secret` and `is_relic` remain explicit protected flags.
- `free_hand` is not authored on an item definition; it is derived from the complete equipped loadout.
- `category`, `slot/occupancy`, and `delivery_hook` remain separate quantities.

---

## 4. Protected reference layer

The reference layer is protected authoring infrastructure. It supplies enums/taxonomy to authoring tables and must be exported deterministically with stable IDs.

### 4.1 `ref_affix_groups`

| Column ID | Grist type / configuration |
| --- | --- |
| `affix_group_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `prefix`, `suffix`, `implicit`

### 4.2 `ref_categories`

| Column ID | Grist type / configuration |
| --- | --- |
| `category_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `weapon`, `armour`, `shield`, `trinket`, `consumable`, `currency`, `tome`

### 4.3 `ref_damage_groups`

| Column ID | Grist type / configuration |
| --- | --- |
| `damage_group_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `physical`, `volatile`, `corruptive`, `structural`, `occult`

### 4.4 `ref_damage_types`

| Column ID | Grist type / configuration |
| --- | --- |
| `damage_type_id` | **Text** |
| `display_name` | **Text** |
| `damage_group` | **Reference → `ref_damage_groups` → `damage_group_id`** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** Physical: `slash`, `impact`, `pierce`; Volatile: `explosive`, `fire`, `lightning`, `cold`; Corruptive: `corrosive`, `poison`; Structural: `shatter`, `tear`; Occult: `chaos`, `divine`, `psychic`

### 4.5 `ref_demand_tiers`

| Column ID | Grist type / configuration |
| --- | --- |
| `demand_tier_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `broad`, `focused`, `exacting`

### 4.6 `ref_design_status`

| Column ID | Grist type / configuration |
| --- | --- |
| `design_status_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `locked`, `sim`, `open`, `gap`, `fixture`

### 4.7 `ref_effect_modes`

| Column ID | Grist type / configuration |
| --- | --- |
| `effect_mode_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `impulse`, `force`

### 4.8 `ref_faculty_families`

| Column ID | Grist type / configuration |
| --- | --- |
| `faculty_family_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `innate`, `arcana`, `mudra`, `psyche`

### 4.9 `ref_hooks`

| Column ID | Grist type / configuration |
| --- | --- |
| `hook_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `main_hand`, `off_hand`, `voice`, `none`

### 4.10 `ref_integrity_states`

| Column ID | Grist type / configuration |
| --- | --- |
| `integrity_state_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `stable`, `cracked`, `fractured`, `broken_guard`

### 4.11 `ref_lifecycle_status`

| Column ID | Grist type / configuration |
| --- | --- |
| `lifecycle_status_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `draft`, `candidate`, `approved`, `deprecated`, `retired`

### 4.12 `ref_regions`

| Column ID | Grist type / configuration |
| --- | --- |
| `region_id` | **Text** |
| `display_name` | **Text** |
| `parent_corner_a` | **Choice → `momentum` / `form` / `mind`** |
| `parent_corner_b` | **Choice → `momentum` / `form` / `mind`** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `instinct` = Momentum+Mind; `pressure` = Momentum+Form; `discipline` = Mind+Form

### 4.13 `ref_rules`

| Column ID | Grist type / configuration |
| --- | --- |
| `rule_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `severity` | **Choice → `critical` / `high` / `medium`** |
| `source_reference` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** **148 generated rows in the 0.29.0 candidate — 86 Critical / 48 High / 14 Medium.** The deterministic CSV seed has SHA-256 `5230f7b4f80b6b16bbc876dc1b58bb888e4d9c25cf3db72dd1a7952fe174d402`; exact Grist readback and byte-identical rule export are proved.

#### 4.13.1 R7 seed contract

`ref_rules` is a generated protected reference table, not an authoring surface for new rules.

- Enumerate the **148** current rows from the regenerated Validation Rules Index, then verify each row against its home source under **P-C8**. The index is the compilation surface; the source row remains authoritative.
- Copy the exact stable ID to `rule_id`, the exact rule statement to `description`, the normalized severity to `severity`, and the exact source locator to `source_reference`.
- Set `display_name` to `rule_id` unless a source-owned short label exists. Do not invent a second rule name in Grist.
- Assign `sort_order` from the deterministic regenerated index order.
- Fail the seed build on duplicate IDs, missing source rows, index/source text drift, invalid severity, or a total other than **148 — 86 / 48 / 14**.
- Treat future rule additions, removals and edits as a generated-seed diff requiring corpus re-proof; never patch the protected table by hand.

**R7 population acceptance:** 148 rows; 148 unique non-empty `rule_id` values; severity split 86/48/14; every `source_reference` resolves; rerunning the generator produces a byte-identical seed export. Reconciliation preserves the row IDs of the 143 adopted rules and appends `T-C14`, `M-C9`, `M-C10`, `M-C11`, and `E-C7` in regenerated index order.

### 4.14 `ref_slots`

| Column ID | Grist type / configuration |
| --- | --- |
| `slot_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `main_hand`, `off_hand`, `body`, `trinket`

### 4.15 `ref_stats`

| Column ID | Grist type / configuration |
| --- | --- |
| `stat_id` | **Text** |
| `display_name` | **Text** |
| `corner` | **Choice → `momentum` / `mind` / `form`** |
| `role` | **Choice → `capacity` / `application` / `resilience`** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** Momentum: `strength` (capacity), `finesse` (application), `stamina` (resilience); Mind: `intellect`, `will`, `spirit`; Form: `frame`, `poise`, `constitution` in the same role order.

### 4.16 `ref_tags`

| Column ID | Grist type / configuration |
| --- | --- |
| `tag_id` | **Text** |
| `display_name` | **Text** |
| `tag_family` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** **Empty at the current checkpoint.**

### 4.17 `ref_triade_origins`

| Column ID | Grist type / configuration |
| --- | --- |
| `origin_id` | **Text** |
| `display_name` | **Text** |
| `description` | **Text** |
| `sort_order` | **Integer** |

**Current seed:** `adm`, `cdm`, `edm`

### 4.18 Reference-layer rules

- `ref_damage_types.damage_group` is a real Reference to `ref_damage_groups`.
- `ref_rules` was held empty until **◈P7** closed at 0.20.0. Historical context: at 0.17.0 the suite had **139** rules — 78 Critical / 47 High / 14 Medium — and at least nineteen lacked an ID-bearing source row. That hold is now superseded by the R7 seed contract in §4.13.1.
- `ref_tags` may stay empty until content begins to require controlled tag rows.
- `free_hand` is **not** a hook.
- `two_handed` is **not** a slot.
- Doctrinal/transgressive are item flags, not demand tiers.
- `shield` is a distinct category value, not weapon or armour subtype.

---

## 5. Current authoring layer — 22-table ◈M10 vertical slice

**P·2.3 names 30 authoring sheets as of 0.17.0.** The current implementation builds the **22** needed for the first ◈M10 vertical slice and defers eight:

| Deferred | Count | Why |
| --- | ---: | --- |
| Affix / generation / loot sheets | 6 | Breadth; deliberately held until the vertical slice runs end to end |
| `fixture_enemies`, `fixture_encounter_members` | 2 | Registered in P·2.3 at 0.17.0, but **their column sets are `[OPEN]` under ◇P8** and must be reconciled against E and H before they can be built |

The second group is a **new** deferral and a different kind: the first six are sequencing, the last two are blocked on a design decision. Building them now would mean inventing the field list, which is what ◇P8 exists to prevent.

For every table below, the schema shown is the **current verified Grist implementation**. Fields marked *temporary unresolved reference* stay Text until their target registry exists; do not create fake References.

### 5.1 `design_parameters`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `parameter_id` | **Text** | Stable parameter/SIM identifier. |
| `display_name` | **Text** | Human-readable name. |
| `value_text` | **Text** | Textual value where an integer `_q` representation is not yet available. |
| `value_q` | **Integer** | Fixed-point value; leave blank until the scale is defined where applicable. |
| `unit` | **Text** | Unit or interpretation. |
| `basis` | **Choice → `derived` / `precedent` / `arbitrary` / `unset`** | Required provenance for `[SIM]` values. |
| `source_reference` | **Text** | Home-document reference. |
| `validation_gate` | **Text** | Metric or gate that accepts/rejects the value. |
| `failure_path` | **Text** | What changes if the gate fails. |
| `design_status` | **Reference → `ref_design_status` → `design_status_id`** | Current design state. |
| `notes` | **Text** | Authoring notes. |
| `sort_order` | **Integer** | Stable display/export ordering. |

### 5.2 `provenance`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `provenance_id` | **Text** | Stable provenance-row ID. |
| `subject_kind` | **Text** | Kind of revision/artefact described. |
| `subject_revision_id` | **Text** | Stable revision/artefact identifier. |
| `source_document_ref` | **Text** | Design/document source. |
| `agent_id` | **Text** | Agent identity where applicable. |
| `charter_version` | **Text** | Agent charter version. |
| `model` | **Text** | Model identifier. |
| `prompt_hash` | **Text** | Prompt hash. |
| `input_schema_hash` | **Text** | Input-schema hash. |
| `seed` | **Text** | Seed or seed identifier. |
| `validation_results` | **Text** | Validation-result reference/summary. |
| `human_verdict` | **Choice → `approved` / `rejected` / `pending` / `not_required`** | Human decision. |
| `notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.3 `equipment`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `equipment_id` | **Text** | Stable identity across revisions. |
| `revision_number` | **Integer** | Revision sequence. |
| `equipment_revision_id` | **Formula → Text** | Normal Formula column; `equipment_id@revision_number`. |
| `schema_version` | **Text** | Schema contract version. |
| `content_version` | **Text** | Design/content version per revision; the reconciled Standard Shield is `0.29.0`, while unchanged fixture weapons retain `0.25.0`. |
| `lifecycle_status` | **Reference → `ref_lifecycle_status` → `lifecycle_status_id`** | Revision lifecycle. |
| `design_status` | **Reference → `ref_design_status` → `design_status_id`** | Design state. |
| `category` | **Reference → `ref_categories` → `category_id`** | Seven-value item category. |
| `chassis_profile` | **Reference → `chassis_profiles` → `chassis_profile_id`** | Typed chassis component. |
| `construction_profile` | **Reference → `construction_profiles` → `construction_profile_id`** | Typed construction component. |
| `integrity_profile` | **Reference → `integrity_profiles` → `integrity_profile_id`** | Integrity component. |
| `demand_tier` | **Reference → `ref_demand_tiers` → `demand_tier_id`** | Broad/focused/exacting demand. |
| `display_name_key` | **Text** | Localisation key. |
| `short_name_key` | **Text** | Localisation key. |
| `description_key` | **Text** | Localisation key. |
| `flavour_key` | **Text** | Localisation key. |
| `accessibility_description_key` | **Text** | Accessibility localisation key. |
| `is_doctrinal` | **Toggle → Checkbox** | Default false. |
| `is_transgressive` | **Toggle → Checkbox** | Default false. |
| `is_unique` | **Toggle → Checkbox** | Default false. |
| `is_secret` | **Toggle → Checkbox** | Protected flag; default false. |
| `is_relic` | **Toggle → Checkbox** | Protected flag; default false. |
| `introduced_in_version` | **Text** | Version introduced. |
| `deprecated_in_version` | **Text** | Optional deprecation version. |
| `source_document_ref` | **Text** | Design source. |
| `decision_origin` | **Choice → `W` / `U` / `BOTH` / `NEW`** | Queryable reconciliation provenance. |
| `authoring_notes` | **Text** | Designer-only notes. |
| `content_hash` | **Text — generated/read-only later** | Canonical content hash. |
| `approved_by` | **Text** | Approver. |
| `approved_at` | **DateTime** | Approval timestamp. |

### 5.4 `equipment_text`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `equipment_text_id` | **Text** | Stable row ID. |
| `equipment_revision` | **Reference → `equipment` → `equipment_revision_id`** | Parent revision. |
| `locale` | **Text** | Reference locale is `en-GB`. |
| `text_key` | **Text** | Stable localisation key. |
| `text_kind` | **Choice → `display_name` / `short_name` / `description` / `flavour` / `accessibility`** | One field per row. |
| `text_value` | **Text** | Localized text. |
| `revision` | **Integer** | Text revision. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.5 `equipment_tags`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `equipment_tag_id` | **Text** | Stable row ID. |
| `equipment_revision` | **Reference → `equipment` → `equipment_revision_id`** | Parent revision. |
| `tag` | **Reference → `ref_tags` → `tag_id`** | One tag per row. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.6 `chassis_profiles`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `chassis_profile_id` | **Text** | Stable profile ID. |
| `display_name` | **Text** | Human-readable name. |
| `chassis_family` | **Text** | Family identifier. |
| `handedness` | **Choice → `one_handed` / `two_handed` / `handless`** | Authoring classification. |
| `weight_class` | **Text — temporary unresolved reference** | Promote to Reference only when its registry exists. |
| `reach_class` | **Text — temporary unresolved reference** | Promote to Reference only when its registry exists. |
| `base_martial_profile_id` | **Text** | Stable join key used by damage-profile entries. |
| `description` | **Text** | Description. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.7 `integrity_profiles`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `integrity_profile_id` | **Text** | Stable integrity-machine ID. |
| `display_name` | **Text** | Human-readable name. |
| `description` | **Text** | Description. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.8 `construction_profiles`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `construction_profile_id` | **Text** | Stable profile ID. |
| `display_name` | **Text** | Human-readable name. |
| `construction_family_id` | **Text — temporary unresolved reference** | Registry not yet created. |
| `material_id` | **Text — temporary unresolved reference** | Registry not yet created. |
| `rigidity_parameter` | **Reference → `design_parameters` → `parameter_id`** | Tunable rigidity parameter. |
| `coverage_profile_id` | **Text — temporary unresolved reference** | Registry not yet created. |
| `brittleness_parameter` | **Reference → `design_parameters` → `parameter_id`** | Tunable brittleness parameter. |
| `defence_profile_id` | **Text** | Join key for defence-profile rows. |
| `type_exception_budget` | **Integer** | Type-exception allowance. |
| `integrity_profile` | **Reference → `integrity_profiles` → `integrity_profile_id`** | Integrity machine. |
| `ward_source_profile_id` | **Text — temporary unresolved reference** | Registry not yet created. |
| `bridge2_mechanism` | **Choice → `edm_damping` / `home_well_strengthening` / `barycentre_well` / `none`** | Locked mechanism class; M·2A.7 maps Medium to `barycentre_well`. |
| `encumbrance_profile_id` | **Text — temporary unresolved reference** | Registry not yet created. |
| `visual_mesh_family_id` | **Text — temporary unresolved reference** | Presentation registry not yet created. |
| `integrity_render_profile_id` | **Text — temporary unresolved reference** | Presentation registry not yet created. |
| `description` | **Text** | Description. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.9 `slot_occupancy`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `occupancy_id` | **Text** | Stable row ID. |
| `equipment_revision` | **Reference → `equipment` → `equipment_revision_id`** | Equipment revision. |
| `slot` | **Reference → `ref_slots` → `slot_id`** | Occupied/allowed slot. |
| `occupancy_role` | **Choice → `primary` / `secondary` / `required` / `optional`** | Role in occupancy definition. |
| `hand_group` | **Choice → `left` / `right` / `both` / `none` / `body_relative`** | Hand/body grouping. |
| `occupancy_units` | **Integer** | Units consumed. |
| `delivery_hook` | **Reference → `ref_hooks` → `hook_id`** | Action delivery channel; not hand count. |
| `supports_combo_source` | **Toggle → Checkbox** | Whether it can serve as a combo source. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.10 `damage_profile_entries`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `damage_profile_entry_id` | **Text** | Stable row ID. |
| `profile_id` | **Text** | Martial-profile join key. |
| `damage_type` | **Reference → `ref_damage_types` → `damage_type_id`** | One damage type per row. |
| `base_pips` | **Integer** | Base pip value. |
| `pip_budget_group` | **Text** | Budget grouping. |
| `primary_status_hook_id` | **Text — temporary unresolved reference** | Status-hook registry not yet created. |
| `secondary_status_hook_id` | **Text — temporary unresolved reference** | Status-hook registry not yet created. |
| `requirement_eligible` | **Toggle → Checkbox** | Whether this contribution may satisfy requirements. |
| `source_layer` | **Choice → `chassis` / `affix` / `inscription`** | Source layer. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.11 `defence_profile_entries`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `defence_profile_entry_id` | **Text** | Stable row ID. |
| `defence_profile_id` | **Text** | Defence-profile join key. |
| `scope_kind` | **Choice → `group` / `type_exception`** | Baseline group or sharp exception. |
| `damage_group` | **Reference → `ref_damage_groups` → `damage_group_id`** | Required for group rows. |
| `damage_type` | **Reference → `ref_damage_types` → `damage_type_id`** | Required for type-exception rows. |
| `rating_value` | **Integer** | Defence rating. |
| `rating_unit` | **Text** | Rating interpretation. |
| `exception_polarity` | **Choice → `none` / `strength` / `weakness`** | Exception direction. |
| `condition_expression_id` | **Text — temporary unresolved reference** | Predicate registry not yet created. |
| `narration_fragment_id` | **Text — temporary unresolved reference** | Narration registry not yet created. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.12 `integrity_states`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `integrity_state_row_id` | **Text** | Stable row ID. |
| `integrity_profile` | **Reference → `integrity_profiles` → `integrity_profile_id`** | Parent profile. |
| `state` | **Reference → `ref_integrity_states` → `integrity_state_id`** | State identifier. |
| `ordinal` | **Integer** | State order. |
| `entry_condition_id` | **Text — temporary unresolved reference** | Predicate registry not yet created. |
| `opening_delta_modifier_q` | **Integer** | Fixed-point modifier; leave blank before ◇P3 where appropriate. |
| `opening_decay_modifier_q` | **Integer** | Fixed-point modifier; leave blank before ◇P3 where appropriate. |
| `discipline_creation_enabled` | **Toggle → Checkbox** | State behavior. |
| `finisher_gate_eligible` | **Toggle → Checkbox** | State behavior. |
| `render_state_id` | **Text — temporary unresolved reference** | Presentation registry not yet created. |
| `repair_policy_id` | **Text — temporary unresolved reference** | Repair-policy registry not yet created. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.13 `triade_effects`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `effect_id` | **Text** | Stable effect ID. |
| `owner_kind` | **Choice → `equipment` / `affix` / `skill` / `faculty` / `condition` / `environment`** | Owning domain. |
| `owner_revision_id` | **Text** | Polymorphic owner revision. |
| `effect_kind` | **Choice → `pull` / `dwell` / `efficiency` / `threshold` / `recovery` / `displacement`** | Effect semantics. |
| `origin` | **Reference → `ref_triade_origins` → `origin_id`** | ADM/CDM/EDM. |
| `mode` | **Reference → `ref_effect_modes` → `effect_mode_id`** | Impulse/force. |
| `dm_q` | **Integer** | Fixed-point Momentum delta. |
| `df_q` | **Integer** | Fixed-point Form delta. |
| `di_q` | **Integer** | Fixed-point Mind delta. |
| `vector_sum_q` | **Formula → Integer** | Normal Formula column: `dm_q + df_q + di_q`. |
| `vector_valid` | **Formula → Toggle / Checkbox** | Normal Formula column: true only when nonblank effect has zero-sum vector. |
| `vector_scale_parameter` | **Reference → `design_parameters` → `parameter_id`** | Eventually points to fixed-point scale parameter. |
| `duration_kind` | **Choice → `instant` / `n_turns` / `while_active`** | Duration mode. |
| `duration_value` | **Integer** | Duration magnitude when applicable. |
| `dynamics_value_q` | **Integer** | Optional fixed-point Dot Dynamics. |
| `condition_expression_id` | **Text — temporary unresolved reference** | Predicate registry not yet created. |
| `region` | **Reference → `ref_regions` → `region_id`** | Optional region target. |
| `threshold_delta_q` | **Integer** | Fixed-point threshold delta. |
| `dwell_modifier_q` | **Integer** | Fixed-point dwell modifier. |
| `efficiency_modifier_q` | **Integer** | Fixed-point efficiency modifier. |
| `volatility_q` | **Integer** | Fixed-point volatility. |
| `recovery_q` | **Integer** | Fixed-point recovery. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.14 `vocabulary_links`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `vocabulary_link_id` | **Text** | Stable row ID. |
| `equipment_revision` | **Reference → `equipment` → `equipment_revision_id`** | Equipment revision. |
| `skill_revision_id` | **Text — temporary unresolved reference** | Skill registry not yet created. |
| `scope_kind` | **Choice → `generic` / `region`** | Avoids inventing a fake generic region. |
| `region` | **Reference → `ref_regions` → `region_id`** | Required only for region-scoped rows. |
| `grant_mode` | **Choice → `vocabulary` / `inherent` / `conditional` / `inscription`** | Grant semantics. |
| `source_hook` | **Reference → `ref_hooks` → `hook_id`** | Delivery source. |
| `minimum_integrity_state` | **Reference → `ref_integrity_states` → `integrity_state_id`** | Minimum state gate. |
| `requires_free_hand` | **Toggle → Checkbox** | Loadout-level free-hand requirement. |
| `minimum_skill_level` | **Integer** | Skill-level requirement. |
| `condition_expression_id` | **Text — temporary unresolved reference** | Predicate registry not yet created. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.15 `stat_modifiers`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `stat_modifier_id` | **Text** | Stable modifier ID. |
| `owner_kind` | **Choice → `equipment` / `affix` / `inscription`** | Owning domain. |
| `owner_revision_id` | **Text** | Polymorphic owner revision. |
| `stat` | **Reference → `ref_stats` → `stat_id`** | Target stat. |
| `stat_bucket` | **Choice → `primary` / `derived` / `resource` / `meta` / `technical`** | Stat taxonomy. |
| `operation` | **Choice → `flat_add` / `additive_percent` / `multiplicative` / `set` / `min` / `max`** | Aggregation operator. |
| `value_min_q` | **Integer** | Fixed-point lower/ranged value. |
| `value_max_q` | **Integer** | Fixed-point upper/ranged value. |
| `value_curve_id` | **Text — temporary unresolved reference** | Curve registry not yet created. |
| `stacking_rule_id` | **Text — temporary unresolved reference** | Stacking-rule registry not yet created. |
| `stacking_group_id` | **Text — temporary unresolved reference** | Stacking-group registry not yet created. |
| `rounding_rule_id` | **Text — temporary unresolved reference** | Rounding registry not yet created. |
| `condition_expression_id` | **Text — temporary unresolved reference** | Predicate registry not yet created. |
| `permanence_tier` | **Choice → `baseline` / `worn_effective` / `consumable` / `run_scoped`** | Permanence class. |
| `display_format_id` | **Text — temporary unresolved reference** | UI-format registry not yet created. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.16 `faculties`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `faculty_id` | **Text** | Stable identity. |
| `revision_number` | **Integer** | Revision sequence. |
| `faculty_revision_id` | **Formula → Text** | Normal Formula column; `faculty_id@revision_number`. |
| `schema_version` | **Text** | Schema contract version. |
| `content_version` | **Text** | Design/content version. |
| `lifecycle_status` | **Reference → `ref_lifecycle_status` → `lifecycle_status_id`** | Revision lifecycle. |
| `design_status` | **Reference → `ref_design_status` → `design_status_id`** | Design state. |
| `faculty_family` | **Reference → `ref_faculty_families` → `faculty_family_id`** | Innate/Arcana/Mudra/Psyche. |
| `faculty_origin` | **Choice → `innate` / `learned` / `granted`** | Implementation classification. |
| `display_name_key` | **Text** | Localisation key. |
| `description_key` | **Text** | Localisation key. |
| `base_damage_profile_id` | **Text** | Damage-profile join key. |
| `delivery_hook` | **Reference → `ref_hooks` → `hook_id`** | Delivery hook; free hand is not a hook. |
| `gate_node_group_id` | **Text — temporary unresolved reference** | Body-node-group registry not yet created. |
| `source_document_ref` | **Text** | Design source. |
| `decision_origin` | **Choice → `W` / `U` / `BOTH` / `NEW`** | Reconciliation provenance. |
| `authoring_notes` | **Text** | Notes. |
| `content_hash` | **Text — generated/read-only later** | Canonical content hash. |
| `approved_by` | **Text** | Approver. |
| `approved_at` | **DateTime** | Approval timestamp. |

### 5.17 `faculty_profiles`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `faculty_profile_entry_id` | **Text** | Stable row ID. |
| `faculty_revision` | **Reference → `faculties` → `faculty_revision_id`** | Parent faculty revision. |
| `entry_kind` | **Choice → `damage` / `vocabulary`** | Typed child row. |
| `profile_id` | **Text** | Damage-profile join key for damage rows. |
| `damage_type` | **Reference → `ref_damage_types` → `damage_type_id`** | Damage row field. |
| `base_pips` | **Integer** | Damage row field. |
| `skill_revision_id` | **Text — temporary unresolved reference** | Vocabulary row field; skill registry not yet created. |
| `scope_kind` | **Choice → `generic` / `region`** | Vocabulary scope. |
| `region` | **Reference → `ref_regions` → `region_id`** | Region when scope is region. |
| `grant_mode` | **Choice → `vocabulary` / `inherent` / `conditional`** | Grant semantics. |
| `source_hook` | **Reference → `ref_hooks` → `hook_id`** | Source hook. |
| `gate_node_group_id` | **Text — temporary unresolved reference** | Body-node-group registry not yet created. |
| `requirement_eligible` | **Toggle → Checkbox** | Whether contribution satisfies requirements. |
| `condition_expression_id` | **Text — temporary unresolved reference** | Predicate registry not yet created. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.18 `fixture_builds`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `fixture_build_id` | **Text** | Stable fixture-build ID. |
| `fixture_set_id` | **Text** | Fixture-set version ID; initial ◈M10 set uses `m10-v1`. |
| `display_name` | **Text** | Human-readable name. |
| `floor_m` | **Numeric** | Authoring value. |
| `floor_f` | **Numeric** | Authoring value. |
| `floor_i` | **Numeric** | Authoring value. |
| `floor_sum` | **Formula → Numeric** | Normal Formula column: `floor_m + floor_f + floor_i`. |
| `floor_valid` | **Formula → Toggle / Checkbox** | Normal Formula column validating total and per-corner caps. |
| `home_region` | **Reference → `ref_regions` → `region_id`** | Home region. |
| `intended_fantasy` | **Text** | Fixture intent. |
| `design_status` | **Reference → `ref_design_status` → `design_status_id`** | Normally `fixture`. |
| `description` | **Text** | Description. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.19 `fixture_stat_weights`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `fixture_stat_weight_id` | **Text** | Stable row ID. |
| `fixture_set_id` | **Text** | Fixture-set ID. |
| `build` | **Reference → `fixture_builds` → `fixture_build_id`** | Build. |
| `stat` | **Reference → `ref_stats` → `stat_id`** | Stat. |
| `relative_weight` | **Integer** | Dimensionless relative weight. |
| `normalisation_group` | **Text** | Initial group `core_stats`. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.20 `fixture_loadouts`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `fixture_loadout_id` | **Text** | Stable row ID. |
| `fixture_set_id` | **Text** | Fixture-set ID. |
| `build` | **Reference → `fixture_builds` → `fixture_build_id`** | Build. |
| `equipment_revision` | **Reference → `equipment` → `equipment_revision_id`** | Exact equipment revision. |
| `slot` | **Reference → `ref_slots` → `slot_id`** | Actual equipped slot. |
| `quantity` | **Integer** | Normally 1; twin copies use two rows. |
| `hand_assignment` | **Choice → `main_hand` / `off_hand` / `both` / `none`** | Actual fixture hand assignment. |
| `authoring_notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |
| `base_pip_total` | **Formula → Integer** | Read-only sum of the referenced chassis martial profile. |
| `m_c11_state` | **Formula → Choice** | `unaffected`, `applied`, `tie_blocked`, or `missing_profile`. |
| `effective_pip_total` | **Formula → Integer** | Applies the one-pip M-C11 reduction; blank when `◇M13` is required. |
| `effective_damage_preview` | **Formula → Text** | Human-readable preview only; canonical damage remains in child rows. |

The preview transforms only a one-handed weapon assigned to `off_hand`. It removes one pip from the unique highest base damage type before requirement checking. A tied highest profile returns `tie_blocked` and no effective total rather than inventing the unresolved `◇M13` tie-break. These are normal Formula columns with verified cached values, not Trigger Formulas or canonical flattened storage.

### 5.21 `fixture_encounters`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `fixture_encounter_id` | **Text** | Stable encounter ID. |
| `fixture_set_id` | **Text** | Fixture-set ID. |
| `display_name` | **Text** | Human-readable name. |
| `zone_count` | **Integer** | Must remain within locked combat-room bounds. |
| `environment_id` | **Text — temporary unresolved reference** | Environment registry not yet created. |
| `proof_purpose` | **Text** | Structural purpose. |
| `description` | **Text** | Description. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.22 `fixture_coverage`

| Column ID | Grist type / configuration | Purpose / note |
| --- | --- | --- |
| `fixture_coverage_id` | **Text** | Stable row ID. |
| `fixture_set_id` | **Text** | Fixture-set ID. |
| `fixture_kind` | **Choice → `build` / `loadout` / `encounter` / `enemy` / `negative_case`** | Fixture class. |
| `fixture_id` | **Text** | Fixture identifier; polymorphic until all fixture child tables exist. |
| `rule_id` | **Reference → `ref_rules`**, shown by `rule_id` | R7 migrated on the supplied working copy after seed verification. The supplied table contained zero rows; preservation proved 0→0. Migration tooling rejects unresolved non-empty IDs. |
| `system_feature` | **Text** | Feature under proof. |
| `expected_assertion` | **Text** | Expected behavior. |
| `coverage_kind` | **Choice → `proof` / `gap`** | Coverage status. |
| `gap_status` | **Choice → `open` / `accepted` / `deferred`** | Only meaningful for gaps. |
| `notes` | **Text** | Notes. |
| `sort_order` | **Integer** | Stable ordering. |

### 5.23 Deferred P·2.3 authoring sheets

These six P·2.3 authoring sheets are **not missing accidentally**; they are deferred until after the core ◈M10 vertical slice works end-to-end:

```text
affixes
affix_effects
inscriptions
generation_policies
loot_tables
loot_entries
```

Two further sheets are deferred for a different reason — they are **blocked, not sequenced**:

```text
fixture_enemies
fixture_encounter_members
```

Both were registered in P·2.3 at 0.17.0 to close the encounter-composition gap described in §8.3. **Their columns are undecided (`◇P8`)**, and the illustrative field lists circulated with that patch are explicitly *not* a schema. Creating these tables before ◇P8 resolves would freeze a guessed field set into the authoring layer, which §8.4 exists to prevent.

Generated/read-only preview and findings sheets are also not yet implemented.

---

## 6. Current table counts and dependency map

| Class | Count | State |
| --- | ---: | --- |
| Protected reference tables | **17** | Complete |
| Current authoring tables | **22** | Complete structurally |
| Deferred — affix / generation / loot | **6** | Sequenced; not built yet |
| Deferred — `fixture_enemies`, `fixture_encounter_members` | **2** | **Blocked on ◇P8**; columns undecided |
| Generated/read-only sheets | — | Pending |
| **Total Grist tables built now** | **39** | 17 reference + 22 authoring |
| **P·2.3 authoring sheets registered** | **30** | 22 built + 8 deferred |

*Both totals are counted from the tables in §4 and §5, not carried forward from the previous checkpoint.*

### 6.1 Dependency-safe population order

```text
1.  chassis_profiles                                  ADOPTED
2.  integrity_profiles                                ADOPTED
3.  integrity_states needed by ◈M10                   ADOPTED
4.  construction_profiles needed by ◈M10              ADOPTED
5.  equipment — five ◈M10 equipment revisions         ADOPTED
6.  damage_profile_entries                            ADOPTED
7.  slot_occupancy                                    ADOPTED
8.  defence_profile_entries for Standard Shield       RECONCILED IN CANDIDATE — Physical 1 pip
9.  faculties                                         COMPLETE IN CANDIDATE — 5 identities at 0.29.0
10. faculty_profiles                                  HELD — 0 rows; TS-M10F-01
11. fixture_builds                                    COMPLETE IN CANDIDATE — 5
12. fixture_stat_weights                              COMPLETE IN CANDIDATE — 45
13. fixture_loadouts                                  COMPLETE IN CANDIDATE — 7 equipment rows
14. fixture_encounters — scalar fields only           COMPLETE IN CANDIDATE — 5
15. fixture_coverage                                  COMPLETE IN CANDIDATE — 29
```

`equipment` was not populated first because its component References must resolve from the start. The dependency seed contains 5 chassis, 1 Standard Shield integrity profile, 3 shield states and 2 construction profiles; exact proof is in `docs/M10_DEPENDENCY_IMPLEMENTATION_PROOF.md`.

---

## 7. ◈M10 content target

The current authoring schema is specifically sized to prove P10 before broad content authoring begins.

### 7.1 Equipment definitions authored in the candidate

```text
weapon.maul@1
weapon.dagger@1
weapon.sword_1h@1
shield.standard@1
weapon.mace_1h@1
```

`shield.standard` uses category `shield`, not `weapon` or `armour`.

All five rows use lifecycle `candidate`, design status `fixture`, and exact component References. The Standard Shield is reconciled to content version `0.29.0`; the four unchanged weapon revisions retain `0.25.0`. `schema_version` stays blank because the canonical equipment JSON Schema remains a placeholder; blank is not an invented version. Four `en-GB` text rows per revision supply display, short, description and accessibility text. No flavour text is invented.

For weapon families that may legally exist in both one-handed and two-handed forms, the **type label must state handedness explicitly** using the `1h-` / `2h-` convention: `1h-Sword`, `2h-Sword`, `1h-Mace`, `2h-Mace`, `1h-Axe`, `2h-Axe`, `1h-Hammer`, `2h-Hammer`, and so on. Canonical machine IDs remain lowercase snake_case and keep the family grouped, using `_1h` / `_2h` suffixes such as `weapon.sword_1h` and `weapon.sword_2h`. Inherently one-handed or inherently two-handed types need no redundant qualifier unless ambiguity exists.

### 7.2 Handedness and locked martial profiles

**Base weapon pip budget is determined by handedness** — locked in M·2A.9 as rule **M-C1** at 0.17.0, not by this document: a normal **one-handed weapon has 3 base pips** and a normal **two-handed weapon has 4 base pips**. Skill redistribution remains zero-sum against that base total. Explicit Transgressive/Inscription effects may break the normal budget under their existing rule-break contract. Shields are governed separately by the pooled shield budget and are not evidence for the ordinary weapon pip norm.

The formerly unqualified 4-pip Sword profile is therefore a **2h-Sword** profile. The Controller fixture uses a **1h-Sword**, because it is paired with a shield.

| Item | Handedness | Damage profile | Total pips | Fixture use |
| --- | --- | --- | ---: | --- |
| Maul | Two-handed | Impact 3 + Shatter 1 | 4 | Striker |
| Dagger | One-handed | Pierce 2 + Slash 1 | 3 | Technical / Trickster |
| **1h-Sword** | One-handed | **Slash 2 + Pierce 1** | **3** | Controller |
| **2h-Sword** | Two-handed | **Slash 2 + Impact 1 + Pierce 1** | **4** | Reference variant; not in current ◈M10 loadout |
| Shield | One hand occupied; shield budget applies | Impact 1 | 1 offence + 1 Physical defence | Controller |
| **1h-Mace** | One-handed | Impact 2 + Shatter 1 | 3 | War Priest |

The 4-pip rule fixes the **total** for a future `2h-Mace`, `2h-Axe`, `2h-Hammer`, etc.; it does **not** determine where the additional pip goes. That martial-profile distribution remains authored per chassis and must not be inferred automatically.

Every damage contribution is one `damage_profile_entries` row.

At 0.29.0 the shield's flat two-pip pool is split across weapon-side and armour-side records: Standard Shield carries Impact 1 and Physical defence 1 pip. Structural remains excluded from the shield defence half under M-C10. The two sides are summed for validation; neither side is inferred from the other.

M-C11 is represented as a derived loadout preview, not by mutating the canonical Dagger profile. The Technical fixture's off-hand Dagger reads Pierce 2 + Slash 1 at base and previews Pierce 1 + Slash 1 after the one-pip highest-type reduction. The main-hand Dagger remains unchanged.

**No schema change was required for M-C1.** `chassis_profiles.handedness` already stores `one_handed` / `two_handed` / `handless`, so the linter validates the sum of `damage_profile_entries.base_pips` for a chassis against its handedness with no new field. A design rule that lands without a migration is worth recording as such.

### 7.3 Frozen builds

| Build | Fm | Ff | Fi | Home | Loadout | Free hand |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Striker | 0.25 | 0.15 | 0.05 | Pressure | Maul | No |
| Controller | 0.09 | 0.18 | 0.18 | Discipline | **1h-Sword + Shield** | No |
| Technical | 0.15 | 0.10 | 0.20 | Instinct | Twin Daggers | No |
| Trickster | 0.12 | 0.08 | 0.25 | Instinct | Single Dagger | Yes |
| War Priest | 0.15 | 0.20 | 0.10 | Discipline | **1h-Mace** | Yes |

Stat weights are **relative and dimensionless**. The harness chooses the absolute budget and normalises at instantiation.

### 7.4 Faculty families

| Family | Delivery / gate |
| --- | --- |
| `innate` | Body-template-derived slot; hook may be hand or none |
| `arcana` | `voice`; jaw/teeth gate |
| `mudra` | Requires a free hand; free hand is loadout state, not a hook |
| `psyche` | `none`; head/spine gate |

### 7.5 Negative fixtures that must remain representable

- Arcana + Arcana illegal.
- Three-source Combo-Action illegal.
- Mudra on a two-handed loadout refused.
- A one-handed weapon with an empty off-hand may carry Mudra.
- Equipmentless Trash still acts through Innate faculty.
- Canine Innate slots derive from its body template.

### 7.6 Populated faculty and fixture boundary

The offline 0.29.0 candidate contains:

| Table | Rows | Boundary |
| --- | ---: | --- |
| `faculties` | 5 | Source-named identities and family/anatomical delivery-gate fields |
| `faculty_profiles` | 0 | Held under `TS-M10F-01`; no source-owned concrete origin/footprint/vocabulary rows |
| `fixture_builds` | 5 | Exact P·10.2 floors, regions, fantasies |
| `fixture_stat_weights` | 45 | Five exact nine-stat relative-weight vectors |
| `fixture_loadouts` | 7 | Equipment assignments plus four read-only M-C11 preview formulas; free hand derives true for Trickster and War Priest |
| `fixture_encounters` | 5 | Scalar shells only; no composition encoded while `◇P8` remains open |
| `fixture_coverage` | 29 | 12 proof declarations and 17 explicit gaps |

The five faculty identities are `faculty.innate_upper@1`, `faculty.innate_bite@1`, `faculty.arcana@1`, `faculty.mudra@1`, and `faculty.psyche@1`, all reconciled to content version `0.29.0`. `Mudra` uses delivery hook `none` because a free hand is loadout state rather than a hook; `Arcana` uses `voice`; `Psyche` and bite use `none`. The upper Innate hook remains blank because it derives from the body-template slot.

The temporary gate-group IDs (`body_group.upper_limb`, `body_group.jaw_teeth`, `body_group.hand_fingers`, `body_group.head_spine`) encode only the exact source-owned node groupings. They remain staged Text values until the body-node-group registry exists.

---

## 8. Known implementation gaps and deliberate holds

### 8.1 ◇P3 — fixed-point scale

`_q` columns exist structurally, but **◇P3 / S-P01 is unresolved**. Do not treat persisted trace values as authoritative before one versioned fixed-point scale is chosen and recorded in `design_parameters`.

### 8.2 ◈P7 — source-rule derivability [CLOSED 0.20.0]

The current validation suite contains **148 rules — 86 Critical / 48 High / 14 Medium**, counted from the 0.29.0 rows.

**`◈P7` closed at 0.20.0.** Every rule is authored in its home document, verified against **P-C8** — the ID leads its line or its first table cell. The 0.29.0 regeneration yields **148 of 148** current rows.

**`◈P7a` closed at 0.19.0.** The regeneration command was never defective; its shortfall *was* `◈P7`. It now recovers the whole suite in a single positional pass.

**Consequences for this specification — implemented on the supplied working copy:**

- `ref_rules` is populated from the verified source-derived rule set;
- `fixture_coverage.rule_id` is migrated from Text to `Reference → ref_rules`;
- neither operation is a design decision. **Together they are R7, implementation work owned by the technical stream.**

**R7 migration acceptance:**

1. Snapshot every existing non-empty `fixture_coverage.rule_id` value before changing the column type.
2. Reject migration if any value is absent from `ref_rules`; do not coerce, drop or silently blank it.
3. Change the Grist column to `Reference → ref_rules` and show `rule_id`.
4. Confirm row count and values are unchanged after migration.
5. Confirm deterministic CSV/canonical export emits the stable rule ID, never a Grist row number or display label.
6. Record a before/after schema proof and a fixture-coverage referential-integrity check.

> **Verification status of this section.** R7 is mechanically and operationally complete through the adopted 143-row checkpoint. The offline 0.29.0 candidate reconciles that table to 148 unique IDs with the 86/48/14 split while preserving existing row IDs; seed and export are byte-identical; Reference metadata and `INTEGER DEFAULT 0` storage remain present; unresolved `P-C999` aborts; idempotent rerun and SQLite integrity pass. Adoption of this 148-row candidate is pending.

### 8.3 Fixture enemy and encounter membership

**Resolved in part at 0.17.0.** P·10.5–10.6 specify concrete enemy fixtures and encounter compositions such as `1 Commander, 2 Standard`, which **P-C3** forbids encoding in one delimited cell. Through 0.16.0, P·2.3 named no relation able to hold them, so the locked ◈M10 fixture set could not be represented canonically **by any legal means** — the gap was not an oversight in the implementation but a missing relation in the design.

P·2.3 now registers both:

```text
fixture_enemies                one frozen enemy-fixture definition
fixture_encounter_members      one encounter × enemy-fixture row, with integer quantity
```

**The relation is decided; the columns are not.** `◇P8` holds the field-set question, which must be reconciled against **E**'s capability ladder and tag classes and against **H**'s body templates. Until it closes:

- do not add a free-text composition column;
- keep `fixture_encounters` scalar-only;
- **do not create either table from the illustrative field lists** — they were offered as examples, not schema;
- canonical ◈M10 fixture JSON stays unfrozen.

### 8.4 Temporary Text fields

A field marked `Text — temporary unresolved reference` is a deliberate staging choice. It may become a Reference only after the target registry/table is designed and exists. This prevents provisional fake registries from becoming accidental canon.

### 8.5 Later authoring breadth

Affixes, inscriptions, generation policies and loot tables remain outside the current slice. This follows the Stage 2 strategy: prove the smallest end-to-end content → fixture → sim path before broadening the authoring surface.

### 8.6 Concrete faculty profiles — `TS-M10F-01`

M·2A.10a requires a faculty to carry a base footprint, but the current sources do not supply concrete non-Innate origin, damage-type/pip, or vocabulary rows for the five fixture identities. The implementation therefore writes the identities and anatomical delivery/gate fields, leaves `base_damage_profile_id` blank, and keeps `faculty_profiles` empty. This blocks faculty damage/vocabulary instantiation without blocking the other fixture records.

### 8.7 Build-to-faculty assignment — `TS-M10F-02`

P·10.4 assigns faculty combinations to named builds, while the registered schema relates builds only to stat weights and equipment loadouts. No normalized build × faculty-revision relation exists. Faculty IDs were not placed in notes or delimited cells: that would violate P-C3 and would not create stable References. Positive faculty-bearing build instantiation remains blocked pending central reconciliation.

### 8.8 Actor lineage and physique authoring — `TS-V029-03`

T·A4.8a and E·F1/E-C7 add actor Lineage and size-conditioned Physique, but P·2.3 does not yet register an actor-lineage/physique authoring grain. The existing `chassis_profiles` table is equipment chassis and must not be overloaded with actor body-template semantics. Enemy and actor fixture instantiation therefore remains blocked until the central schema owns the necessary identity, typical-size, nine-stat lineage offsets, and up-to-two zero-sum physique pairs per non-typical size.

---

## 9. Stage 2 technical sequence from this checkpoint

| Step | Work | State |
| ---: | --- | --- |
| 1 | v0.16 reference reconciliation | **Complete** |
| 2 | `design_parameters` + `provenance` | **Complete structurally** |
| 3 | Equipment identity/text/tag tables | **Complete structurally** |
| 4 | Physical profile/component tables | **Complete structurally** |
| 5 | Faculty tables | **Complete structurally** |
| 6 | ◈M10 fixture tables | **Complete structurally** |
| 7 | **R7:** populate `ref_rules`; migrate `fixture_coverage.rule_id` after seed proof | **Complete, adopted into active document and centrally validated** |
| 8 | Populate dependency profiles + five ◈M10 equipment revisions | **Complete, adopted, repository commit `8d2776b`** |
| 9 | Populate ◈M10 faculties and fixture records | **Complete to authoritative boundary in offline candidate; adoption pending; TS-M10F-01/-02 hold full instantiation** |
| 10 | Add Grist generated previews/validation controls | **Partially complete: four M-C11 loadout previews; broader controls pending** |
| 11 | Deterministic Grist → CSV exporter | Pending |
| 12 | Replace placeholder JSON Schemas | Pending |
| 13 | CSV → canonical JSON compiler | Pending |
| 14 | JSON/Pydantic/Pandera/content validation | Pending |
| 15 | Canonical JSON → DuckDB import | Pending |
| 16 | Resolve ◇P3 fixed-point scale | Blocking before authoritative trace persistence |
| 17 | Headless ◈M10 simulator | Pending |
| 18 | Named deterministic RNG provenance | Pending |
| 19 | Per-delta trace model | Pending |
| 20 | Partitioned Parquet trace output | Pending |
| 21 | Golden tests | Pending |
| 22 | DuckDB analytics + log-power decomposition | Pending |
| 23 | First S-K01 / S-K02 sweep | Stage 2c exit work |
| 24 | ~~Close ◇P7~~ | **Done — closed centrally at 0.20.0** |

The first sweep target remains S-K01/S-K02; the log-power decomposition is part of the harness requirement, not optional analysis.

---

## 10. Validation obligations for this authoring layer

The implementation must eventually lint at least:

- unique identities and exact revision resolution;
- scalar authoring / no delimited arrays;
- category component completeness;
- `shield` = weapon-side + armour-side components;
- damage type → exactly one damage group;
- handedness pip budget (`1h = 3`, `2h = 4`) and pip conservation — rule **M-C1**, source-owned in M·2A.9 since 0.17.0 and therefore linter-executable;
- Structural → integrity;
- zero-sum Triade vectors;
- per-region-only threshold reductions;
- temporary effects never mutate baseline floors;
- exactly two Combo-Action delivery hooks;
- free-hand legality from actual loadout occupancy;
- one pooled shield budget;
- shield pool = exactly two pips split between offence and Physical defence under M-C9/M-C10; Structural excluded;
- M-C11 reduces a unique highest off-hand one-handed weapon damage type before requirement checking and blocks unresolved ties under `◇M13`;
- shield and body-armour integrity independence;
- protected Secret/Relic behavior;
- fixture coverage or explicit gap.
- actor Lineage/Physique authoring remains a declared gap until T-C14/E-C7 have a central schema grain.

Database CHECK constraints are for local arithmetic only; cross-row/domain semantics belong in the content linter.

---

## 11. Technical decisions recorded by this implementation

| Decision | Current ruling |
| --- | --- |
| Authoring UI | Grist |
| Grist role | Editing façade only |
| Canonical authority | Deterministically ordered JSON |
| Database | Rebuildable DuckDB catalogue |
| Trace store | Partitioned Parquet |
| Machine IDs | lowercase snake_case |
| Repeatables | Child rows only |
| Item classification | category ≠ occupancy ≠ delivery hook |
| Shield category | Distinct seventh value |
| Free hand | Derived from complete loadout |
| Revision identity | `stable_id@revision_number` |
| Formula behavior | Ten normal Formula columns for derived values; no Trigger Formula |
| Empty authoring columns | May remain Empty until first manual entry |
| `ref_rules` | Generated protected 148-row seed under §4.13.1; 86/48/14 split, stable-ID merge, and deterministic hash proved |
| `fixture_coverage.rule_id` | `Reference → ref_rules`, shown/exported by stable `rule_id`; unresolved IDs reject migration |
| Fixed-point state | `_q` integers; scale pending ◇P3 |
| ◈M10 first slice | Maul, Dagger, **1h-Sword**, Shield, **1h-Mace** + faculty/fixture proof records |
| M10 dependency seed | 5 chassis, 1 shield integrity profile, 3 shield states, 2 construction profiles; deterministic CSV → Grist → byte-identical CSV |
| `bridge2_mechanism` | Four exact values: `edm_damping`, `home_well_strengthening`, `barycentre_well`, `none`; Standard Shield uses `barycentre_well` under M·2A.7 |
| Standard Shield integrity path | `stable → cracked → broken_guard` — centralised in M·2A.6 at 0.23.0 |
| Unresolved dependency fields | Weapon weight/reach and construction material/rigidity/brittleness/coverage remain blank; blank is not zero or `none` |
| M10 equipment seed | 5 revisions, 20 text rows, 9 damage entries, 9 occupancy rows, 1 shield defence entry, 0 tag rows; deterministic CSV → Grist → byte-identical CSV |
| Shield defence rating | Standard Shield Physical defence is `1` with unit `pip`; together with Impact 1 it exactly consumes the flat two-pip pool |
| Equipment tags | No rows while protected `ref_tags` is empty; fake tag IDs are forbidden |
| Equipment schema version | Blank until the placeholder canonical schema is implemented and versioned |
| M10 faculty identity seed | 5 candidate/fixture revisions at content version 0.29.0; no invented schema version or base footprint |
| Faculty profiles | 0 rows until concrete source-owned origins, footprints, and vocabulary assignments exist (`TS-M10F-01`) |
| M10 fixture seed | 5 builds, 45 stat weights, 7 equipment loadout rows, 5 scalar encounters, 29 coverage rows; deterministic CSV → Grist → byte-identical CSV |
| Fixture coverage status | 12 proving-fixture declarations and 17 explicit gaps; a declaration is not an executed simulation result |
| M-C11 implementation | Four read-only `fixture_loadouts` formulas preview the unique-highest reduction; canonical damage child rows remain unchanged and a tie is blocked under `◇M13` |
| Build faculty assignment | Not encoded in notes or delimited cells; normalized relation absent (`TS-M10F-02`) |
| Enemy/encounter composition | No guessed tables or prose encoding while `◇P8` remains open |

---

## 12. Change log

| Version | Date | Change |
| --- | --- | --- |
| **0.29.0** | 12 Aug 2026 | Reconciled the adopted post-equipment checkpoint to 148 rules (86/48/14), Standard Shield Impact 1 + Physical defence 1 pip, five 0.29 faculty identities, and 29 fixture-coverage rows (12 proof / 17 gap). Added four normal Formula columns implementing the M-C11 off-hand preview without mutating canonical damage rows; the Technical twin-Dagger fixture proves 3→2 pips and ties block under `◇M13`. Exact idempotence, byte-identical export, rollback negatives, SQLite integrity, and 12/12 regression tests pass. Recorded `TS-V029-01` through `TS-V029-03`; no AUTHORED DESIGN DECISION. |
| **0.28.0** | 11 Aug 2026 | Re-proof checkpoint only; no technical schema or content mutation was adopted. |
| **0.27.0** | 11 Aug 2026 | Reconciled the new Lineage/Physique rules as a schema gap: actor body-template semantics are not assigned to equipment `chassis_profiles`; no provisional relation was invented. |
| **0.26.0** | 11 Aug 2026 | Re-aligned current-state claims after equipment adoption at commit `8d2776b`. Populated and proved 5 faculty identities, 5 builds, 45 stat weights, 7 equipment loadout rows, 5 scalar encounters, and 24 coverage rows (9 proof declarations / 15 gaps). Preserved 0 faculty profiles, all adopted rows, 143 R7 rules, Formula/Data column behavior, byte-identical seven-table export, exact idempotence, rejection-before-write, and 10/10 regression tests. Recorded `TS-M10F-01` and `TS-M10F-02`; no AUTHORED DESIGN DECISION. |
| **0.25.0** | 11 Aug 2026 | Aligned current-state claims to 0.25.0. Added `barycentre_well` to the Grist Bridge-2 Choice enum and migrated the Standard Shield construction record. Populated and proved five M10 equipment revisions, 20 `en-GB` text rows, 9 damage entries, 9 occupancy rows and one null-rated Physical shield-defence row. Preserved the empty protected tag registry, exact References, byte-identical six-table seed/export, idempotence, R7 and dependency counts. |
| **0.24.0** | 10 Aug 2026 | Fourth weight class adopted. No new quantity invented — the class occupies a seat the dot model already had. |
| **0.23.0** | 10 Aug 2026 | M10 dependency handoff dispositioned — one authored design decision centralised, one finding backlogged, three accepted. |
| **0.22.0** | 10 Aug 2026 | Filename convention adopted — `<REF>-<Name>_TRIADE-[V_e_r].md`. Re-aligned this specification internally to 0.22.0 and implemented the M10 dependency candidate: 5 chassis, 1 Standard Shield integrity profile, 3 shield states, and 2 construction profiles. Added deterministic CSV seeds/import/export proof, byte-identical hashes, idempotence and R7 regression. The Standard Shield path `stable → cracked → broken_guard` is marked authored-but-not-yet-centralised. |
| **0.21.0** *(R7 implementation, 10 Aug)* | 10 Aug 2026 | Implemented and proved R7 on the supplied repository and Grist working copy: generated/populated 143 unique `ref_rules` rows with the 81/48/14 split; migrated `fixture_coverage.rule_id` to `Reference → ref_rules`; proved 0→0 preservation, stable-ID export with a populated synthetic case, unresolved-ID rejection, idempotence, identical seed/export SHA-256 and SQLite integrity. The running self-hosted Grist instance was not mutated. No design decision or central patch was authored. |
| **0.21.0** *(technical re-proof, 10 Aug)* | 10 Aug 2026 | Re-proofed against the 0.21.0 corpus copy and central handoff. Current suite locked here to **143 — 81 / 48 / 14**; every rule ID cited by this specification resolves in the current index. R7 is now the explicit next technical step: generate the protected `ref_rules` seed, then migrate `fixture_coverage.rule_id` without data loss. Added deterministic seed and migration acceptance criteria in §4.13.1 and §8.2. **No Grist or repository implementation was executed or claimed by this pass.** |
| **0.21.0** | 10 Aug 2026 | The technical-stream instructions enter the governed set as `TRIADE-Technical_Stream_Project_Instructions-[V_e_r].md`; the central instructions are renamed `TRIADE-Design_Stream_Project_Instructions-[V_e_r].md`. Both carry the design-set version in the filename as a co-authorship marker. |
| **0.20.0** | 10 Aug 2026 | Corpus normalised to `markdownlint` under a tracked `.markdownlint.jsonc`; 1,956 table separators unified. Content-equivalence proven by whitespace-normalised diff against `Archive/v0.19.0/`. |
| **0.19.0** | 10 Aug 2026 | Subsection headings lost the document letter — `### V4.1` → `### 4.1` — completing the 0.18.0 pass, which had changed `## Part Xn` and left `### Xn.n`. Bare `Xn.n` references normalised to `X·n.n`. |
| **0.18.1** | 10 Aug 2026 | Non-goals take **⦻** (`⦻Xn`), the sixth and last unglyphed identifier namespace. No design decision changed. |
| **0.18.0** | 10 Aug 2026 | Identifier glyphs adopted set-wide — `◇` live open item, `◈` closed, `◉` goal, `⇥` phase, `⌬` skill level; see L·§0. Section headings across K, V, E, G and P lost their document letter, so a bare `Xn` in prose is now a section and anything else must be glyphed. Stale spaced filenames repointed to the underscored convention. `content_version` example advanced to 0.18.0. |
| **0.17.0** | 9 Aug 2026 | **Registered in `VERSION-MANIFEST` as the first technical document** — a class distinct from the ten design documents, implementing a design-owned system without owning game meaning. Reconciled against the patched design set: **P·2.3 now names 30 authoring sheets**, and `fixture_enemies` / `fixture_encounter_members` move from *missing relation* (§8.3, a design gap) to *registered but blocked on `◇P8`* (a decided relation with undecided columns) — deferrals now split into six sequenced and two blocked. **◇P7 restated** from seventeen to at least nineteen, as a floor rather than a total; **◇P7a added**, the regeneration command recovering 82 of 139 rules. The handedness pip budget is re-attributed to **M-C1** in M·2A.9 rather than asserted here, which is the authority rule working as intended: the ruling this document carried at 0.16.0 is now design-owned, and no Grist schema change was needed to enforce it. |
| **0.16.0** | 9 Aug 2026 | Initial technical specification. Consolidates repository bootstrap, local Grist authoring implementation, 17-table protected reference layer, 22-table current authoring slice, v0.16 shield/category reconciliation, formula/reference conventions, ◈M10 population target, ◇P3/◇P7 holds, and the encounter-membership schema gap discovered during implementation. **Same-version correction:** weapon handedness now fixes the ordinary base pip budget at `1h = 3` and `2h = 4`; ambiguous weapon families use explicit `1h-` / `2h-` type labels, the Controller fixture uses `1h-Sword` (`Slash 2 + Pierce 1`), and the former 4-pip Sword profile is explicitly `2h-Sword`. |
