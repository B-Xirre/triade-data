# M10 dependency-layer implementation proof

**Aligned Triade version:** 0.22.0  
**Scope:** `Chassis_profiles`, `Integrity_profiles`, `Integrity_states`, `Construction_profiles`  
**Owning design:** M — Stats, Items, Equipment; constrained by P — Content Pipeline & Data Model  
**Authority boundary:** technical implementation and fixture seed only; no record here is authoritative game design  
**Implementation state:** dependency layer populated in an offline R7-complete candidate; five equipment revisions are next  
**Proof status:** mechanically verified; active-document adoption of this candidate is not yet performed

## 1. Governed baseline

The run re-read `VERSION-MANIFEST.md` and the 0.22.0 governed set. Version 0.22.0 preserves the completed R7 state and changes the document naming convention without changing the M10 content target. The governing sources for this stage are:

- `M-Stats_Items_Equipment_design_TRIADE-0_22_0.md` — M·2A.3, M·2A.6, M·2A.9, M·2A.11;
- `P-Content_Pipeline_design_TRIADE-0_22_0.md` — P·1.2, P·1.3, P·2.3, P·7.1, P·10;
- `C-Content_Authoring_Technical_Specification_TRIADE-0_22_0.md` — C·5.6–5.8, C·5.12, C·6.1, C·7;
- `R-Validation_Rules_Index_TRIADE-0_22_0.md` — M-C1, M-C2, M-C4, P-C3 and P-C8;
- `B-Open_Items_Index_TRIADE-0_22_0.md` — ◇P3 and ◇P8.

No derived index was edited.

## 2. Implemented seed

| Table | Before | After | Stable IDs |
| --- | ---: | ---: | --- |
| `Chassis_profiles` | 0 | 5 | `chassis.maul`, `chassis.dagger`, `chassis.sword_1h`, `chassis.shield_standard`, `chassis.mace_1h` |
| `Integrity_profiles` | 0 | 1 | `integrity.shield_standard` |
| `Integrity_states` | 0 | 3 | `integrity.shield_standard.stable`, `.cracked`, `.broken_guard` |
| `Construction_profiles` | 0 | 2 | `construction.fixture_weapon_m10`, `construction.shield_standard` |

The chassis handedness is exact against M-C1 and the locked M10 target. Weapon weight/reach and construction material/rigidity/brittleness/coverage fields remain blank because their values are not source-owned. The Standard Shield profile reserves `defence.shield_standard` as the stable join key for the next physical-record stage.

## 3. Authored working decision

`AUTHORED DESIGN DECISION`: the Standard Shield fixture uses the state path:

```text
stable → cracked → broken_guard
```

M·2A.6 establishes `Stable → Cracked → Fractured`, plus `Broken Guard` for shields and rigid off-hand defence, but does not state whether the shield path includes `Fractured`. The working implementation routes the Standard Shield from `Cracked` to `Broken Guard`; `Broken Guard` disables Discipline Opening-creation. This remains **authored-but-not-yet-centralised** and is recorded in the companion PATCHES / INTAKE file.

## 4. Executable evidence

Command:

```powershell
py tools/apply_m10_dependencies.py `
  "Triade - Equipment Authoring-R7.grist" `
  content/csv `
  "Triade - Equipment Authoring-M10-dependencies.grist" `
  proof/m10_dependencies
```

Regression command:

```powershell
py -m unittest -v tests/test_m10_dependencies.py tests/test_r7.py
```

Measured result:

- four tests pass;
- all 11 dependency rows read back by stable ID;
- all four exported CSV files are byte-identical to their governed seed files;
- stable IDs are unique;
- Reference columns resolve exact profile/state IDs rather than Grist row numbers;
- authoring columns written by the seed are Data Columns (`isFormula = 0`);
- `_q` Opening modifiers remain SQL `NULL` while ◇P3 is unresolved;
- scalar authoring check passes;
- SQLite `PRAGMA integrity_check` returns `ok`;
- R7 remains intact: 143 `Ref_rules` rows and `Fixture_coverage.rule_id = Reference → Ref_rules`.

Proof artefacts:

```text
proof/m10_dependencies/m10_dependencies_result.json
proof/m10_dependencies/m10_dependencies_snapshot.json
proof/m10_dependencies/m10_dependencies_schema.json
proof/m10_dependencies/export/chassis_profiles.csv
proof/m10_dependencies/export/integrity_profiles.csv
proof/m10_dependencies/export/integrity_states.csv
proof/m10_dependencies/export/construction_profiles.csv
```

Candidate SHA-256:

```text
4c60458caf1af1e3542b31b310b929843714d40e6ebe77ebb4f2bd86501d7e27
```

## 5. Verified versus unverified

Verified:

- exact dependency row counts and stable IDs;
- handedness and M10 chassis identity;
- stable Reference readback;
- deterministic byte-identical seed/export;
- idempotent reapplication;
- unresolved numeric blanks preserved;
- R7 regression and SQLite integrity.

Not yet verified:

- import/adoption into active Grist document `3TwLJyu7fythPjAj1e1424`;
- Grist UI presentation after active-document adoption;
- the five equipment revisions and their exact References;
- damage, defence, slot, tag and localisation child rows;
- full category-component and shield pooled-budget validation;
- canonical JSON, DuckDB, simulation and traces.

## 6. Change log

| Version | Date | Change |
| --- | --- | --- |
| 0.22.0 | 10 Aug 2026 | Initial dependency-layer implementation proof: 5 chassis, 1 integrity profile, 3 integrity states and 2 construction profiles; byte-identical seed/export and R7 regression verified. |
