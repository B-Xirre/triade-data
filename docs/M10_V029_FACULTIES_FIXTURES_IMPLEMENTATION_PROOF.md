# M10 v0.29.0 Faculties / Fixtures Implementation Proof

**Aligned Triade version:** 0.29.0
**Proof date:** 12 Aug 2026
**Implementation authority:** technical realization only; no design document was edited
**AUTHORED DESIGN DECISION count:** **0**

## Result

The offline candidate upgrades a fresh copy of the adopted post-equipment Grist document to the current 0.29.0 rule registry, applies the authored Standard Shield pool, populates the latest unblocked M10 faculty/fixture records, and installs a read-only M-C11 off-hand preview.

| Artifact | SHA-256 |
| --- | --- |
| Adopted input Grist | `e3590afaae456fecc2ce7e3c9e9c127d3456f64575f4a774005d4043de2fdc0f` |
| Candidate Grist | `fa221333ae6ea0f6d162c526b79606715e09e9a869d6fda57e370ba15687442e` |
| 148-row `ref_rules.csv` | `5230f7b4f80b6b16bbc876dc1b58bb888e4d9c25cf3db72dd1a7952fe174d402` |

The source document was read and copied, never edited in place. The active self-hosted Grist document was not mutated.

## Corpus preflight

The supplied 0.29.0 tracked corpus passed all mandated preflight gates before implementation:

| Check | Result |
| --- | --- |
| Ledger | clean, 23 / 23 tracked files |
| History | 273 historical entries, checked against the earliest included archive checkpoint |
| Version alignment | 29 / 29 current-state claims aligned to 0.29.0 |

The governing source changes used by the migration are T·A4.8a/T-C14, E·F1/E-C7, M·2A.10a, M·2A.11, M-C9, M-C10, M-C11, and P·10.2–10.7. Cross-document mismatches and missing schema grains are recorded in the 0.29.0 PATCHES / INTAKE companion; no local design ruling was substituted.

## Reconciliation proof

### Rule registry

- preserved the Grist row IDs of all 143 adopted rule records;
- merged the regenerated 0.29.0 seed to 148 unique stable IDs;
- added `T-C14`, `M-C9`, `M-C10`, `M-C11`, and `E-C7`;
- verified the exact 86 Critical / 48 High / 14 Medium split and sort order 1…148;
- verified exact seed readback, byte-identical deterministic export, and resolution of all 26 non-empty fixture-coverage references.

### Standard Shield

| Side | Stored record |
| --- | --- |
| Offence | `martial.shield_standard.impact` = Impact 1 |
| Defence | `defence.shield_standard.physical` = Physical 1, unit `pip` |
| Validation | Flat pool total = 2; Structural not used |

Only the shield revision is advanced to content version 0.29.0. The unchanged Maul, Dagger, 1h-Sword, and 1h-Mace fixture revisions retain content version 0.25.0.

### Faculties and fixtures

| Table | Rows | Proof boundary |
| --- | ---: | --- |
| `faculties` | 5 | All identities at content version 0.29.0; source-owned family/gate/hook data only |
| `faculty_profiles` | 0 | Deliberately held by `TS-M10F-01` |
| `fixture_builds` | 5 | Exact floors, regions, fantasies |
| `fixture_stat_weights` | 45 | Five complete nine-stat relative-weight vectors |
| `fixture_loadouts` | 7 | Stable equipment References and hand assignments |
| `fixture_encounters` | 5 | Scalar shells only |
| `fixture_coverage` | 29 | 12 proof declarations, 17 explicit gaps |

All seven rule/fixture CSV seed/export pairs and the rule export are byte-identical. Stable identities are unique, all References read back by stable ID, and a second application makes no change.

## M-C11 fixture-record implementation

Four normal Grist Formula columns were added to `fixture_loadouts` and exposed in all three existing view sections:

| Column | Result type | Role |
| --- | --- | --- |
| `base_pip_total` | Integer | Sum canonical martial-profile child rows |
| `m_c11_state` | Choice | `unaffected`, `applied`, `tie_blocked`, or `missing_profile` |
| `effective_pip_total` | Integer | One-pip reduction when applied; blank on blocked state |
| `effective_damage_preview` | Text | Human preview only; canonical damage remains normalized child rows |

The formulas apply only to an off-hand, one-handed weapon. They remove one pip from the unique highest base damage type before requirement checking. Independent syntax parsing succeeded for all four stored formula bodies.

| Fixture row | Base | State | Effective | Preview |
| --- | ---: | --- | ---: | --- |
| Technical main-hand Dagger | 3 | `unaffected` | 3 | `pierce ++, slash +` |
| Technical off-hand Dagger | 3 | `applied` | 2 | `pierce +, slash +` |

The candidate contains no naturally tied-highest M10 profile. The negative test temporarily creates a 2/2 Dagger profile, verifies `tie_blocked` under unresolved `◇M13`, aborts before persistence, and proves transaction rollback. No tie-break was invented.

## Executed verification

| Verification | Result |
| --- | --- |
| Full regression suite | 12 / 12 passed, no skips |
| Candidate SQLite `integrity_check` | `ok` |
| User table count | 39, unchanged |
| Rule seed/readback | exact, 148 / 148 unique |
| Fixture/equipment seed readback | exact |
| Deterministic seed/export | byte-identical |
| Idempotent reapplication | exact |
| Unresolved rule reference negative | rejected before write |
| Divergent populated-table negative | rejected before write |
| M-C11 tied-highest negative | blocked and rolled back |
| Formula metadata | four columns, `isFormula = 1`, normal Formula behavior |
| Formula cached readback | exact for all seven loadout rows |

The candidate proves authoring and migration behavior, not combat simulation. Canonical JSON, DuckDB import, action execution, traces, and S-K01/S-K02 runs remain unexecuted.

## Remaining holds

- `TS-M10F-01`: no source-owned concrete faculty footprints/vocabulary;
- `TS-M10F-02`: no normalized fixture build × faculty relation;
- `TS-V029-01`: P·10.3 retains the superseded shield profile;
- `TS-V029-02`: P·10.5 retains `Medium` after the `Average` rename;
- `TS-V029-03`: no actor Lineage/Physique authoring grain;
- `◇M13`: tied-highest M-C11 profiles remain blocked;
- `◇P8`: fixture enemy and encounter-member columns remain blocked;
- `◇P6` and `◇P3`/`S-P01`: canonical package versioning and authoritative fixed-point traces remain blocked.

## Operator handoff

Use the candidate as an offline adoption candidate. Verify it in the target Grist release before replacing the active document, then land the combined repository patch over the adopted post-equipment baseline. Central process should disposition the five intake findings and update the manifest only after adoption.
