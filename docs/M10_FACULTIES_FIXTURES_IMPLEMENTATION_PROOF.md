# M10 faculties and fixtures — implementation proof

**Aligned Triade version:** 0.26.0
**Scope:** `faculties`, `faculty_profiles`, `fixture_builds`, `fixture_stat_weights`, `fixture_loadouts`, `fixture_encounters`, `fixture_coverage`
**Owning design:** M — Stats, Items, Equipment; P — Content Pipeline & Data Model
**Authority boundary:** technical implementation and fixture seed only; this proof does not author game rules or balance values
**Implementation state:** unblocked faculty identities and M10 fixture records populated in an offline candidate; explicit holds retained where the authoritative model is incomplete

## Inputs

| Input | SHA-256 |
| --- | --- |
| Adopted post-equipment Grist backup | `e3590afaae456fecc2ce7e3c9e9c127d3456f64575f4a774005d4043de2fdc0f` |
| Repository snapshot | commit `8d2776be28eaf129d920c7135e51dbe3f2cafd90` |

The starting document contained the adopted dependency and equipment layers:

| Table group | Measured baseline |
| --- | ---: |
| Chassis / integrity / construction dependency rows | 11 |
| Equipment revisions | 5 |
| Equipment text / occupancy / damage / defence child rows | 39 |
| Equipment tags | 0 |
| Protected validation rules | 143 — 81 Critical / 48 High / 14 Medium |

## Population result

| Table | Before | After |
| --- | ---: | ---: |
| `faculties` | 0 | 5 |
| `faculty_profiles` | 0 | 0 |
| `fixture_builds` | 0 | 5 |
| `fixture_stat_weights` | 0 | 45 |
| `fixture_loadouts` | 0 | 7 |
| `fixture_encounters` | 0 | 5 |
| `fixture_coverage` | 0 | 24 |

The five faculty identities are `faculty.innate_upper@1`, `faculty.innate_bite@1`, `faculty.arcana@1`, `faculty.mudra@1`, and `faculty.psyche@1`. The five builds, floors, 45 dimensionless weights, seven equipment assignments, and five scalar encounter shells reproduce P·10.2–10.6.

`fixture_coverage` contains **9 proving-fixture declarations and 15 explicit gaps**. Proof rows do not claim that a headless simulation has run; they name the record and expected assertion that the future harness must execute.

## Executable verification

The full inherited and new standard-library suite passed:

```text
Ran 10 tests in 0.110s
OK
```

Coverage includes:

- exact source-owned seed shapes and values;
- stable-ID Reference resolution for families, hooks, regions, stats, builds, equipment, slots, and rule IDs;
- deterministic CSV → Grist → byte-identical seven-table CSV export;
- exact idempotence on a second application;
- rejection of an unresolved equipment revision before any target row is written;
- preservation of all adopted dependency/equipment rows and the 143-rule R7 layer;
- preservation of `faculty_revision_id`, `floor_sum`, and `floor_valid` as normal Formula columns;
- conversion of populated authoring columns from Grist Empty Columns to Data Columns;
- floor cap/sum validation, stat-weight matrix equality, loadout/free-hand derivation, encounter bounds, scalar authoring, and SQLite integrity.

The unresolved-reference negative case was executed against a scratch copy and left `faculties` and `fixture_builds` at 0 rows.

## Candidate

| Artifact | SHA-256 |
| --- | --- |
| `Triade - Equipment Authoring-M10-faculties-fixtures.grist` | `0bb88fbb2960080e905e7c2216a2ffeb040778aab2d9f7b6a1fab52211d4f2f5` |

All seven seed/export file hashes match byte-for-byte. Exact hashes are recorded in `proof/m10_faculties_fixtures/m10_faculties_fixtures_result.json`.

## Deliberate holds

Verified and intentionally unpopulated:

1. `faculty_profiles` remains empty. M defines the requirement that every faculty carries a base footprint, but the current sources do not supply concrete origin, damage-type/pip, or vocabulary rows for these five identities. Inventing them would be design authoring.
2. Positive build-to-faculty assignments are not representable as normalized records. The current fixture model relates builds to equipment only.
3. `fixture_enemies` and `fixture_encounter_members` remain absent under existing `◇P8`; encounter composition was not encoded into prose cells.
4. `fixture_encounters.environment_id = high_ground` is used only for the source-named Vault marker; the environment registry remains a temporary unresolved Reference.
5. `schema_version` remains blank under `◇P6`; equipment tags remain empty under `◇P10`; shield defence magnitude remains null under `◇M12`.

The first two findings are carried in the aligned companion intake as `TS-M10F-01` and `TS-M10F-02`. No **AUTHORED DESIGN DECISION** was introduced.

## Verification boundary

**Verified:** deterministic offline migration, stable-ID readback, Formula/Data column metadata, exact counts, byte-identical export, idempotence, rejection behavior, inherited R7/M10 regression, and SQLite integrity.

**Not verified:** operator adoption into the active Grist document, canonical JSON/schema validation, build-to-faculty instantiation, enemy/encounter composition, headless simulation, trace output, or any balance outcome.
