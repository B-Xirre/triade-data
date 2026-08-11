# Content Authoring Technical Specification — PATCHES / INTAKE

**Aligned Triade version:** 0.29.0
**Companion to:** `C-Content_Authoring_Technical_Specification_TRIADE-0_29_0.md`
**Implementation package:** M10 faculties, fixtures, and 0.29.0 reconciliation candidate
**Authority:** central handoff only; this file is not authoritative design content
**AUTHORED DESIGN DECISION count:** **0**

## Scope and measured evidence

This companion carries the two unresolved M10 faculty findings and records three 0.29.0 cross-document/schema findings. The implementation follows the current authoritative M rules for the shield pool and off-hand transform; it does not amend design documents or resolve open tie, lineage, physique, faculty-footprint, or relation questions.

- adopted source Grist SHA-256: `e3590afaae456fecc2ce7e3c9e9c127d3456f64575f4a774005d4043de2fdc0f`;
- 0.29.0 candidate Grist SHA-256: `fa221333ae6ea0f6d162c526b79606715e09e9a869d6fda57e370ba15687442e`;
- 148 rules, split 86 Critical / 48 High / 14 Medium;
- Standard Shield: Impact 1 + Physical defence 1 pip, flat pool total 2;
- 5 faculties, 0 faculty profiles, 5 builds, 45 stat weights, 7 loadouts, 5 scalar encounters, 29 coverage rows;
- 12 proof declarations and 17 explicit gaps;
- Technical off-hand Dagger M-C11 preview: 3 base pips → 2 effective pips;
- 12/12 tests passed; deterministic readback/export, idempotence, rollback negatives, and SQLite integrity passed.

## TS-M10F-01 — concrete faculty definition content is absent

| Field | Record |
| --- | --- |
| **Type** | `FINDING` |
| **Finding** | M·2A.10a requires a faculty base footprint and defines origin, gate nodes, hook, and vocabulary, but the current corpus does not supply concrete non-Innate origins, damage-type/pip footprints, or vocabulary rows for the five M10 identities. |
| **Implementation pressure** | The five identities and anatomical delivery/gate fields are representable. Populating `faculty_profiles`, `base_damage_profile_id`, or generic Arcana/Mudra/Psyche origin would invent content or balance values. |
| **Evidence** | `faculties.csv` contains five 0.29.0 candidate/fixture identities with blank schema/base-profile values; `faculty_profiles.csv` remains header-only; exact readback and byte-identical export pass. |
| **References checked** | M·2A.9–2A.10a; M·9.5; P·2.2–2.3; P·7.1; P·10.2–10.5; T·A3.8; H·6.3; H·7.2a; H·13; L faculty entries; R rules T-C12/T-C13/H-C7/E-C6/P-C3/P-C7. |
| **Affected documents** | M and P; C records only the implementation consequence. |
| **Recommended target** | P · Part 10, with M · 2A.10a amended only if the missing content is a family rule rather than fixture data. |
| **Impact if not adopted** | Faculty damage, vocabulary, Combo-Action instantiation, and headless faculty simulation remain blocked. |
| **Implementation blocker** | **Yes** for concrete faculty profiles and simulation; **no** for delivered identity/build/loadout/encounter shells. |
| **Central disposition** | `unresolved` |

## TS-M10F-02 — fixture builds cannot own faculty revisions as normalized rows

| Field | Record |
| --- | --- |
| **Type** | `FINDING` |
| **Finding** | P·10.4 assigns faculty combinations to named builds, but the registered fixture model has no normalized build × faculty-revision relation. |
| **Implementation pressure** | Encoding faculty IDs in notes or delimited cells would violate P-C3 and would not create stable References. `fixture_loadouts` is equipment-specific and must not be overloaded. |
| **Evidence** | Five builds and seven equipment loadouts are exact, but positive faculty membership and its free-hand legality cannot be generated from authoring data. |
| **References checked** | P·2.2–2.3; P·7.1; P·10.1–10.4; M·2A.10–2A.10a; T·A3.8; C·5.18–5.22; R rules P-C3/T-C12/T-C13/H-H6. |
| **Recommended target** | P · 2.3 and Part 10 if a new row grain is accepted; C then defines concrete columns. |
| **Impact if not adopted** | M10 build instantiation, faculty legality, Divine purge coverage, and per-source trace attribution remain blocked. |
| **Implementation blocker** | **Yes** for complete build/faculty instantiation; **no** for delivered equipment loadouts. |
| **Central disposition** | `unresolved` |
| **Reconciliation notes** | Not a duplicate of `◇P8`, which currently owns fixture enemies and encounter membership. |

## TS-V029-01 — P·10.3 retains the superseded shield fixture values

| Field | Record |
| --- | --- |
| **Type** | `FINDING` |
| **Finding** | P·10.3 still specifies the Standard Shield as `Shield Impact ++ / 2`, while current M·2A.11 and M-C9/M-C10 define a flat two-pip pool split as Standard Shield offence 1 + Physical defence 1 pip, with Structural excluded. |
| **Implementation pressure** | A literal P fixture import would recreate the superseded two-offence-pip record and conflict with current rules. |
| **Implementation treatment** | The 0.29.0 Grist candidate follows M·2A.11 and the version-manifest handoff: Impact 1, Physical defence 1 pip. No P document was edited. |
| **Recommended target** | P · 10.3 fixture table. |
| **Recommended wording** | Replace the Standard Shield fixture profile with the current 1 offence + 1 Physical defence-pip split and cite M-C9/M-C10. |
| **Impact if not adopted** | Future fixture seed regeneration from P alone can regress the shield record. |
| **Implementation blocker** | **No** for this candidate because the authoritative M rules are explicit; **yes** for unqualified P-only regeneration. |
| **Central disposition** | `unresolved` |

## TS-V029-02 — P·10.5 still uses `Medium` after the size rename

| Field | Record |
| --- | --- |
| **Type** | `FINDING` |
| **Finding** | E·F1 defines the available sizes as Small, Average, Large, and Giant and records the `Medium` → `Average` rename, but P·10.5 still labels Standard, Elite, and Beast fixture sizes `Medium`. |
| **Implementation pressure** | Enemy fixture instantiation cannot choose whether `Medium` is a stale label or a distinct value; silently normalizing it would hide source drift. |
| **Recommended target** | P · 10.5. |
| **Recommended wording** | Replace intended `Medium` values with `Average`, or explicitly state a different mapping if that was intended. |
| **Impact if not adopted** | Canonical enemy-size validation and lineage/physique lookup remain ambiguous. |
| **Implementation blocker** | **Yes** for enemy fixture instantiation; independently, `◇P8` still blocks the enemy table columns. |
| **Central disposition** | `unresolved` |

## TS-V029-03 — actor Lineage/Physique has no registered authoring grain

| Field | Record |
| --- | --- |
| **Type** | `FINDING` |
| **Finding** | T·A4.8a/T-C14 make Lineage the actor Chassis/body template, and E·F1/E-C7 add typical-size lineage offsets plus size-conditioned Physique pairs. P·2.3 registers no actor-lineage/physique tables or relations. |
| **Implementation pressure** | The existing `chassis_profiles` table is equipment chassis. Reusing it would collapse distinct semantics and create accidental canon. The required typical size, nine-stat zero-sum offsets, and up-to-two additive zero-sum pairs per non-typical size have no legal row grain. |
| **Recommended target** | P · 2.3 and Part 10 for the logical actor authoring model; C for concrete Grist columns after central acceptance. |
| **Impact if not adopted** | Actor and enemy fixture records cannot deterministically compose Lineage → Physique → later modifiers. |
| **Implementation blocker** | **Yes** for lineage/physique-backed actor and enemy instantiation; **no** for the delivered equipment/faculty/loadout shell. |
| **Central disposition** | `unresolved` |

## Existing items and closed findings — no duplication

| Item | Implementation treatment |
| --- | --- |
| `◇M13` | Tied highest M-C11 damage profiles return `tie_blocked`; no tie-break is invented. |
| `◇P8` | `fixture_enemies` and `fixture_encounter_members` remain uncreated; composition is not encoded in prose cells. |
| `◇P6` | Schema versions remain blank; no canonical package validation is claimed. |
| `◇P3` / `S-P01` | No authoritative fixed-point trace persistence is claimed. |
| `TS-M10E-01` | Re-proofed and superseded by current M·2A.11/M-C9/M-C10; no duplicate intake item. |
| `◇M12` | Closed by the current authored shield pool; no longer used as a hold. |

## No additional patch required

- **T** — T-C14 is source-authored; the missing authoring grain is recorded as TS-V029-03.
- **M** — M-C9/M-C10/M-C11 are implemented literally; no mechanics text is proposed here.
- **E** — E-C7 is source-authored; the stale P size label and missing authoring grain are recorded separately.
- **K / H / W / L** — no action, anatomy, encounter, or terminology contract was changed.
- **B / Y / R** — derived indexes were read only; all 29 non-empty coverage rule IDs resolve against the 148-row seed.
- **A / VERSION-MANIFEST** — adoption/status updates remain central follow-up after operator acceptance.
- **Instruction files** — the technical-stream replacement is alignment-only; no workflow rule is changed.

## Requested central closeout

1. Disposition the five findings once each, in their named design homes.
2. Update P·10.3 and P·10.5 before the next canonical fixture regeneration.
3. Do not treat the 12 proof declarations as executed simulation results.
4. After operator adoption and repository landing, update the manifest/ROADMAP status; retain this companion until every item has a terminal disposition.
