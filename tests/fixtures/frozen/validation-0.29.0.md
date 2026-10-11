# Triade — Validation Rules Index

**Version:** 0.29.0
**Date:** 8 August 2026
**Status:** Regenerated at 0.29.0. **Derived, not authored** — edit the rule table in the source document, regenerate this.

**Scope.** Every automated check across all nine documents, under one severity scheme with stable IDs.

---

## 1. Severity scheme

| Severity | Meaning | Build behaviour |
| --- | --- | --- |
| **Critical** | Violates a **locked invariant**. The design is wrong, not merely unbalanced | **Fail. Block merge** |
| **High** | Violates a **stated design goal**. May be intentional, must be justified | Fail, overridable with recorded justification |
| **Medium** | Quality, consistency or authoring hygiene | Warn |

**ID format: `{DOC}-{C|H|M}{n}`.** The Tile Pipeline uses the prefix `TILE-` rather than `G-`, because `G` reads as a generic axis label in a document set built on `ΣF`, `Φ` and barycentric coordinates.

**Metrics are not rules.** A metric measures; a rule passes or fails. Metrics live in the SIM Numbers Register with their gates.

**New at 0.12.0: the digest firewall.** Rules now divide by what they run on. **W-C10** is the boundary rule.

| Suite | Runs on | Feeds the proof digest? | Failure behaviour |
| --- | --- | --- | --- |
| **Gameplay proofs** | The integer logical model | **Yes** | Repair → reseed → reject |
| **Render proofs** (V-C1…C4) | The baked render package | **Never** | Fails the **build**, not the seed |

---

## 2. Critical — locked invariants

### Geometry & state

| ID | Rule | Source |
| --- | --- | --- |
| **T-C1** | All dot vectors satisfy `dm + df + di = 0` | T · A2.4 |
| **T-C2** | `ΣF ≤ 0.45` and `F ≤ 0.25` hold for every character at every point | T · A.2 |
| **T-C3** | `Σ Φ_base` is conserved — no permanent power creep | T · A4.2 |
| **T-C4** | Any floor modification is sum-preserving; threshold reductions per-region only | T · G.2 |
| **T-C5** | Region geometry valid under **every legal floor shape** | T · A.3, J.4 |
| **T-C6** | Temporary effects cannot modify baseline floors or global thresholds | T · A4.2a |
| **T-C7** | At run start, `ΣF_rendered == ΣF_baseline` | T · A4.2a *(◈W2f)* |
| **T-C8** | Action success scales on Triade position — no position-independent resolution | T · C.6 |
| **T-C9** | AP cannot fall below the guaranteed floor | T · H, K·3.3 |
| **T-C10** | Every skill anchor is reachable by its intended vocabulary owner | T · A3.8 |
| **T-C11** | The **corner**-floor render is affine in its field; the **sector**-floor render is super-additive | T · A4.4 |
| **T-C12** | Every `sources` entry resolves to a record — weapon, shield, `faculty` or environment object | T · A3.8, M · 2A.12 |
| **T-C13** | A `[Combo-Action]` declares **exactly two** delivery hooks | M · 2A.10 |
| **T-C14** | A lineage `offset` is a 9-stat integer vector summing to zero, measured at the lineage's `typical` size | T · A4.8a |
| **H-C6** | Every actor resolves to exactly one `[Chassis]`, and every `[Chassis]` to exactly one `BodyTemplate` | H · 5.3 |
| **H-C7** | `[Innate]` slots derive from the `BodyTemplate` node groups, never authored per chassis | H · 13, M · 2A.10a |
| **E-C5** | Every chassis names exactly one `BodyTemplate`; no chassis inlines coverage weights | E · 3 |
| **E-C6** | Every enemy carries at least one `[Faculty]`; no enemy has zero vocabulary sources | E · F.1 |

### Combat resolution

| ID | Rule | Source |
| --- | --- | --- |
| **K-C1** | No action creates an Opening **and** awards the same region's trickle | K · 16 |
| **K-C2** | No action reads without a valid Opening | K · 16 |
| **K-C3** | Edge cannot target a different Opening or combatant | K · 9.1 |
| **K-C4** | Loop-earned Advantage is one-shot | K · 16 |
| **K-C5** | `[Back-foot]` does not stack against one attacker | K · 16 |
| **K-C6** | Glancing outcomes award **no credit of any kind** | K · 6.2 |
| **K-C7** | Watch resolves exactly one branch per triggering event | K · 8.2 |
| **K-C8** | No corner holds more than one tempo lever | K · 3.3 |
| **K-C9** | Position snapshot is taken **before** the action resolves | K · 5.2 |

### Materiel

| ID | Rule | Source |
| --- | --- | --- |
| **M-C1** | Ordinary base weapon footprints obey the handedness budget — `1h` = 3 base pips, `2h` = 4 — and skill redistribution conserves that base total. Transgressive/Inscription effects excepted; shields governed by M-C4 | M · 2A.9 |
| **M-C2** | Structural effects use **integrity**, not typed mitigation | M · 2A.3 |
| **M-C3** | Two-vector loadouts do not pool footprints, except via `[Combo-Action]` | M · 2A.10 |
| **M-C4** | Shield pips and defensive value draw from **one** pooled budget | M · 2A.11 |
| **M-C9** | Every shield draws a **2-pip pool**, split by sub-family — buckler 2/0, standard 1/1, tower 0/2 — where offensive pips + defence pips = 2 | M · 2A.11 *(restated 0.29.0)* |
| **M-C10** | Offence and defence in a shield pool share the **same pip unit** — one defence pip is one 2A.4 signature step in a group resolving through typed defence. **Structural is not purchasable** (M-C2) | M · 2A.11 *(restated 0.29.0)* |
| **M-C11** | A one-handed weapon in the **off hand** loses one pip from its highest damage type, applied to the **base** footprint before 2A.10's requirement check | M · 2A.11 *(new 0.29.0)* |
| **M-C5** | Class starting offsets **sum to zero** | T · A4.8 |
| **M-C6** | `[Secret]` and `[Relic]` are authored by mission placement only — no affix, loot table or generation pipeline may set either | M · 2.7a *(new 0.12.0)* |
| **M-C7** | No `[Secret]`-flagged item is salvageable, rerollable, sellable or discardable. **Binds the internal attribute** | M · 2.7a *(new 0.12.0)* |
| **M-C8** | The same protection applies to `[Relic]` items | M · 2.7a *(new 0.12.0)* |

### Damage & health

| ID | Rule | Source |
| --- | --- | --- |
| **H-C1** | `Σ` of all effective-field reductions, all sources, per corner ≥ `max(Φ_safe_x, 0.5 × Φ_base_x)` | H · 10.2 |
| **H-C2** | At run start, `ΣF_rendered == ΣF_baseline` *(= T-C7)* | H · 9.3 |
| **H-C3** | No `RemedyDef` denominates `economy_cost` in `Location Grounding` / `[Imprint]`, or in Temper | H · 8.1 |
| **H-C4** | Vital-organ lethality gated on HP below the Finisher threshold, **or** target Downed | H · 9.4 |
| **H-C5** | Wound and temporary effects never alter baseline floors, thresholds or global geometry | H · 13 |

### Enemies

| ID | Rule | Source |
| --- | --- | --- |
| **E-C1** | Every enemy carries a position `(m,f,i)` summing to 1 | E · F.0 |
| **E-C2** | Tag arithmetic renormalises against floor budget and per-corner cap | E · F.1 |
| **E-C3** | Elite and Commander reads are position-dependent exactly as the player's are | E · F.0, T · C.6 |
| **E-C4** | Exactly one chassis per enemy; tag cardinality respected | E · F.1 |
| **E-C7** | A physique size map carries at most two additive integer pairs per size, each summing to zero; typical carries none, absent sizes are `null` | E · F.1 |

### World generation

| ID | Rule | Source |
| --- | --- | --- |
| **W-C1** | Every mandatory lock has a reachable prerequisite key path | W · 16.1 |
| **W-C2** | No object blocks the only critical route after placement **or any plausible destruction state** | W · 16.1 |
| **W-C3** | No temporary map effect alters baseline floors, thresholds or region geometry | W · 11.4 |
| **W-C4** | Same seed + same `generator_version` reproduces an identical proof digest | W · 16.1 |
| **W-C5** | Boss chamber contains a reachable exit | W · 5.5 |
| **W-C6** | At any access depth, the Location can generate at least one at-or-above-reference dungeon | W · 16.1 |
| **W-C7** | **No floating point anywhere** in the simulation core or any decision affecting an output hash | W · 7.2 |
| **W-C8** | No float-derived heuristic — including Shannon entropy — influences any generation decision reaching the proof digest | W · 16.1 *(new)* |
| **W-C9** | Every `[Vertical Portal]` has matched authored endpoints on both decks with safe landings; traversal never inferred from `(tx,ty)` overlap | W · 16.1 *(new)* |
| **W-C10** | No render- or screen-space-derived value participates in the proof digest | W · 16.1 *(new)* |
| **W-C11** | Every mandatory gate declares at least one **monotonic** resolution | W · 5.8a *(new)* |
| **W-C12** | Every progression site is reachable **without traversing the gate it opens** | W · 13 *(new)* |
| **W-C13** | Mandatory-path progression objects are indestructible, except a breakable seal whose declared resolution is `destroyed` | W · 5.8a *(new)* |
| **W-C14** | A `[Relic]`-gated door is never on the mandatory path of the run in which it appears | W · 5.9 *(new)* |
| **W-C15** | No `[Relic]` grants Grounding, `[Modification Ceiling]`, floor budget or stats. **Binds the internal name** | W · 5.9 *(new)* |
| **W-C16** | An `[Incursion]` awards no Grounding and no `[Modification Ceiling]`. **Binds the internal name** | W · 5.9 *(new)* |
| **W-C17** | An `[Incursion]` has no Stratum, checkpoint, descent unlock or Stratum lock; its record cannot express them | W · 5.9 *(new)* |
| **W-C18** | `[Incursion]` item level saturates at the maximum Location-obtainable tier | W · 5.9 *(new)* |
| **W-C19** | Every zone has exactly one `elevation_band`; no zone spans decks | W · 12 *(new)* |
| **W-C20** | `complex_room` is written only by room-template instantiation | W · 9, 12 *(new)* |

### Visual — render proofs

*New at 0.12.0. These run on the baked render package and **never** feed the proof digest (W-C10). A failure fails the build, not the seed.*

| ID | Rule | Source |
| --- | --- | --- |
| **V-C1** | Every walkable cell has a valid rendered surface; every exposed elevation edge has facade or intentional void | V · 4.9 |
| **V-C2** | No active actor, posture telegraph or Commander wind-up fully occluded in any cutaway state | V · 4.9 |
| **V-C3** | Y-sort stable across tile boundaries; screen-space selection resolves to exactly one intended target | V · 4.9 |
| **V-C4** | Every destruction state has matching art, collision and navigation | V · 4.9 |

### Tile pipeline

| ID | Rule | Source |
| --- | --- | --- |
| **TILE-C1** | Every socket label has ≥1 legal complement — no dead-end tile | G · 6 |
| **TILE-C2** | Every archetype declares a `projection_id` matching the locked camera matrix | G · 6 |
| **TILE-C3** | Atlas bake is deterministic — same tile set, byte-identical layout | G · 6 |
| **TILE-C4** | No float in socket identity, adjacency lookup or any bake hash reaching the digest | G · 6 |

### Content pipeline

| ID | Rule | Source |
| --- | --- | --- |
| **P-C1** | Canonical JSON is the source of truth; the build is one-directional, text → database | P · 2.1 |
| **P-C2** | All persisted simulation and trace state uses fixed-point integers, never floats | P · 3.4 *(W-C10)* |
| **P-C3** | No authored cell contains a delimited array; every repeatable value is a child row | P · 2.2 |
| **P-C4** | An approved revision is never edited in place | P · 2.4 |
| **P-C5** | Every trace event resolves to an exact content revision and `content_snapshot_hash` | P · 5.2 |
| **P-C6** | Economy permissions are derived from category and protected flags, never authored | P · 3.2 |
| **P-C7** | Every locked subsystem names a proving fixture, or an explicit declared gap | P · 10 |
| **P-C8** | Every indexed rule leads its line or first table cell in its home document | P · 9 |
| **P-C10** | An `AUTHORED DESIGN DECISION` is non-authoritative until disposed `authored`; technical docs mark it authored-but-not-yet-centralised | P · 9 |
| **P-C11** | Historical factual claims are not editable by a version sweep; notation migrations are exempt | P · 9 |

*Filed here at 0.16.0. P·Part 9 has stated these as **Critical** since 0.15.0; the index had all seven — plus `P-M1` — inside §3 High, and its printed totals had not moved since 0.12.0.*

**Critical total: 78.**

---

## 3. High — design goals

| ID | Rule | Source |
| --- | --- | --- |
| **T-H1** | Every reinforcing loop has a **named brake** | T · I.5 |
| **H-H5** | Aim never overrides the coverage cascade; `aim_weight` < `AIM_CEILING` < 1.0 | H · 6.2a *(S-H09)* |
| **H-H6** | Divine purge consumes the state it converts — no sequence extracts more than was invested | H · 6.2b *(T-H1)* |
| **E-H5** | `[Innate]` slots derive from the body template, never authored per chassis | E · 3 |
| **E-H6** | Enemy tier mix per band implements M·9.7's encounter budget, not a health multiplier | E · 3 *(◇W17/◇E11)* |
| **M-H5** | No single interaction exceeds ~20% of a band's total log-power gain unless authored unique with a named drawback | M · 9.6 *(T-H1)* |
| **P-H1** | The agent's query path is read-only; writes pass through record validation | P · 6.1 |
| **P-H2** | Every signature is keyed by all seven identity fields | P · 5.5 |
| **P-H3** | Every `[SIM]` parameter has a row carrying basis, gate and failure path | P · 3 |
| **P-H4** | Raw Parquet is never committed to git | P · 4.3 |
| **P-H5** | Every intake-record item carries one type and one disposition; `authored` names a document and section | P · 9 |
| **T-H2** | No reference build shows an unrecoverable spiral | T · Gate T |
| **T-H3** | Candidate entities exceed the trace-distance redundancy threshold | T · I.4 |
| **T-H4** | Triangle coverage above target across reference builds | T · Gate T |
| **K-H1** | Cooldowns used only for rare, dramatic skills | K · 5.1 |
| **M-H1** | Per-family armour exception budget respected | M · 5.4 |
| **M-H2** | Global matchup surface within portfolio budget (≈20) | M · 5.4 |
| **M-H3** | Item power within the band for its rarity and ilvl | M · 2.5 |
| **M-H4** | Bridge-2 weight-class consistency | M · 5.4 |
| **H-H1** | All wound `cdm_influence` vectors satisfy `dm+df+di = 0` | H · 13 |
| **H-H2** | Ambient wound summary ≤ 4 items | H · 7.6 |
| **H-H3** | Every remedy's `cure_tags` resolve to ≥1 reachable `ConditionDef` | H · 13 |
| **H-H4** | Every `ConditionDef` treatable by ≥1 reachable `RemedyDef` | H · 13 |
| **E-H1** | `chassis × role` matrix validated exhaustively | E · F.4 |
| **E-H2** | Encounter generation enforces behaviour-tag diversity within a group | E · F.4 |
| **E-H3** | No contradictory tag pairs | E · F.4 |
| **E-H4** | Enemy traces pass the redundancy gate | E · F.4 |
| **W-H1** | Extracted zones per **combat room** ∈ [2,4]. `complex_room` exempts the **floor only** | W · 16.2 |
| **W-H2** | Rooms hosting ranged enemies contain ≥1 reachable cover opportunity | W · 16.2 |
| **W-H3** | Off-mesh climb/vault links have safe endpoints | W · 16.2 |
| **W-H4** | Surface propagation cannot exceed active-space budget in one tick | W · 16.2 |
| **W-H5** | Generated hazards cannot remove all safe standing tiles from a mandatory room | W · 16.2 |
| **W-H6** | Cover density within the region's axis band | W · 16.2 |
| **W-H7** | Zone budget consumed by vertical profile | W · 16.2 *(new)* |
| **W-H8** | `high_ground` density within the balance-owned band, gated against S-E03 | W · 16.2 *(new)* |
| **W-H9** | Progression sites respect an anti-clustering band | W · 16.2 *(new)* |
| **W-H10** | `[Incursion]` content borrows a region package; bespoke needs Steward approval | W · 16.2 *(new)* |
| **W-H11** | Generation parameters saturate at a stated depth | W · 16.2 *(new)* |
| **W-H12** | 2-zone-floor failure resolved by furnishing → reseed → **demotion**; rejection only if mission-mandatory | W · 16.2 *(new)* |
| **W-H13** | ≥5 mutually non-mergeable walkable components is a structural layout defect | W · 16.2 *(new)* |
| **W-H14** | Every `complex_room` template passes W-C1, W-C2, W-C5, W-H2 individually | W · 16.2 *(new)* |
| **V-H1** | The two failure modes render distinctly on the skill bar | V · 4.1 |
| **V-H2** | Potency renders as a continuous ramp, never discrete steps | V · 4.1 |
| **V-H3** | Wound render targets disjoint from integrity render targets | V · 4.8 |
| **TILE-H1** | Non-edge-label-inducible tilesets explicitly flagged | G · 6 |
| **TILE-H2** | Symmetry class declared; connectors marked non-rotating | G · 6 |
| **TILE-H3** | Every state variant has matching art, collision and navigation | G · 6 |
| **TILE-H4** | Agent-originated archetypes carry provenance and recorded human approval | G · 6 |

**High total: 47.**

---

## 4. Medium — quality & hygiene

| ID | Rule | Source |
| --- | --- | --- |
| **W-M1** | Toppleable furniture has a valid post-state footprint | W · 16.3 |
| **W-M2** | Cover does not exceed per-zone density cap | W · 16.3 |
| **W-M3** | Decorative props do not consume reserved combat-affordance sockets | W · 16.3 |
| **W-M4** | Chokepoint width distribution within band | W · 16.3 |
| **W-M6** | `[Switch]` and other indestructible progression objects contribute no cover | W · 16.3 *(new)* |
| **H-M1** | Coverage weights normalise to 1.0 per body template | H · 13 |
| **H-M2** | Wound render targets disjoint from integrity | H · 13 |
| **E-M1** | Modifier space sampled rather than exhaustively simulated | E · F.4 |
| **L-M1** | Every locked term in any document appears in the Lexicon | L |
| **L-M2** | No term shadows a locked term in another domain | L |
| **TILE-M1** | Example-inferred adjacency does not encode incidental source detail | G · 6 |
| **TILE-M2** | Decorative props do not occupy reserved affordance sockets | G · 6 |
| **TILE-M3** | Archetype schema completeness | G · 6 |
| **P-M1** | `en-GB` is the explicitly labelled reference locale | P · 3.1 |

**Medium total: 14.**

### L-M2 earned two more catches at 0.16.0

| Proposed / found | Shadowed | Outcome |
| --- | --- | --- |
| `RemedyDef.category` *(standing since 0.10.0)* | `category`, the item classification (M·2.1, P·1.3) — and a remedy **is** an item | Renamed **`remedy_type`**. The two enums shared `consumable` and diverged on five values, which is what hid it |
| E·F.1 column header `Category` | as above | Renamed **Enemy Tag** |

*Both were found by a sweep prompted by a question about shields, not by a census. `category` had never been entered in the Lexicon at all, so an L-M2 grep against L would have returned a false negative — the `[Location Grounding]` failure in a second form.*

### L-M2 earned four more catches at 0.13.0

| Proposed | Shadowed | Outcome |
| --- | --- | --- |
| `[Signs]` | `signature` — 23 uses as `[Signature Action]` | Rejected → **`[Mudra]`** |
| `capability` as a `sources` value | the capability ladder — 38 of 42 uses | Slot yielded the word → **`faculty`** |
| `physique profile` | `[Physique]`, a locked **Enemy Tag** | Rejected; `martial profile` adopted for the other sense |
| **`focus`** for aim weight | `+focus`, `Focus-broken`, "Will / focus tax" | **Missed at Stage 0, caught within the same version** → `aim_weight` / `AIM_CEILING` |

The last is the instructive one: the census was run, 26 uses were seen, and the word was used anyway. A census that is not acted on is not a check.

### L-M2 earned three more catches at 0.12.0

| Rejected name | Collision |
| --- | --- |
| `[Walk Surface]` | *surface* is locked to environmental channels and named reactions in W·11 |
| `[Dungeon Floor]` | *floor* is the Triade barycentric sense — 103 uses in T, 39 in W, **none geometric** |
| `[Lever]` (as an object) | K-C8's *tempo lever* |

Adopted instead: `[Deck]`, `[Storey]`, `[Switch]`. Each was grep-verified against the full set before adoption.

---

## 5. Cross-referenced rules

| Invariant | IDs | Rationale |
| --- | --- | --- |
| `ΣF_rendered == ΣF_baseline` at run start | **T-C7** + **H-C2** | Asserted where the tier rule lives and where wounds could break it |
| Zero-sum dot vectors | **T-C1** ⊃ **H-H1** | Wounds are a large vector source |
| Wound / integrity render separation | **V-H3** = **H-M2** | Raised to High in V, which owns rendering |
| Baseline floor immutability | **T-C6**, **W-C3**, **H-C5** | Three effect sources: conditions, surfaces, wounds |
| No float in the digest path | **W-C7** ⊃ **W-C8**, **W-C10**, **TILE-C4** | One invariant asserted at the core, the solver, the render boundary and the bake |
| Progress-currency protection | **H-C3**, **W-C15**, **W-C16** | Remedies, Relics and Incursions each bind the internal name |
| Reserved affordance sockets | **W-M3** = **TILE-M2** | Asserted at placement and at tile authoring |
| Destruction-state completeness | **V-C4** ⊃ **TILE-H3** | Render proof and tile lint |

---

## 6. Coverage gaps

| Gap | Where implied | Severity if added |
| --- | --- | --- |
| No check that every `[SIM]` value has a gate | SIM Register §2 | Medium |
| No check that agent-authored content carries provenance | W · 17.2 | Medium — *partially closed by TILE-H4, tiles only* |
| No check on audio cue distinctness | T · A3.4 | — *(no audio document)* |
| No accessibility check | V · 4 | High, once owned |
| No check that a currency cost names a currency that **exists** | H-C3 covers forbidden currencies only | Medium |
| **No render proof harness** | V · 4.9, G · 3 | **The four V-C rules are specified and unrunnable** (◇V7 / ◇G7) |

The last is new and the most immediately actionable: 0.12.0 added four Critical render rules and no way to execute them.

---

## 7. Suite summary

| Severity | Count | Build behaviour |
| --- | ---: | --- |
| **Critical** | 86 | Fail; block merge |
| **High** | 48 | Fail; overridable with recorded justification |
| **Medium** | 14 | Warn |
| **Total** | **148** | |

By document: T 18 · M 16 · K 10 · W 39 · H 15 · E 14 · V 7 · G 11 · P 16 · L 2.

**Recounted again at 0.17.0 by counting rows: 78 / 47 / 14 = 139, unchanged.** *(amended in-version: the suite now stands at 80 / 48 / 14 = 142 — `P-C8`, `P-H5`, `P-C10` were added at 0.19.0–0.21.0.)* M-C1 was reworded, not added, and no rule was created or removed; the by-document line is unchanged. A count that stays the same across a version is still counted, not assumed.

**These counts are recounted from the tables above, not carried forward** [CORRECTED 0.16.0]. The printed totals had read 60 / 38 / 13 = 111 since 0.12.0 — three versions of additions were entered into the tables and never into the summary, and the changelog rows tracked a fourth figure (133) that matched neither. Three numbers, three sources, no agreement. The counts are now generated by counting rows.

**Two rules per version is the normal rate; 0.12.0's jump from 75 to 111 was the anomaly** and it was concentrated in W (17 → 39). Growth since is small and located where design work happened: T and H at 0.13.0 for the faculty channel, P at 0.15.0 for the pipeline.

### The index is fully derived — `◈P7` **CLOSED 0.20.0**

**All 142 rules are authored in their home document.** The census at 0.19.0 measured every rule against **P-C8** — the ID leads its line or its first table cell, changelogs excluded — and 0.20.0 closed the residue. Census and the published regeneration command agree at **142 of 142**.

**The figure moved four times before anyone measured it:** seventeen at 0.16.0, nineteen at 0.17.0, thirty at 0.18.0, each recounted from the last. Every one of those counts used a pattern that could only see bolded table rows, while the corpus states rules in tables, in fenced code blocks, inside box-drawing workflow art and as numbered Requirements in prose.

**The resolution, for the record:** twenty-five rules needed a tag, three were mis-homed — `L-M1` and `L-M2` authored in the design-stream instructions, `M-C5` cited to T — and **none needed a rule written**. `M-C3`, `M-H4` and `M-C5` had been reported as unwritten and were stated in **M** all along.

**This index is therefore derived for every entry it carries.** A rule appearing here without a source row is now a **P-C8** violation, not a known exception

---

## 8. Regeneration

**The command published here through 0.16.0 did not regenerate this index** [CORRECTED 0.17.0]. It read:

```bash
grep -hn "^| \*\*\(TILE\|[TKMHEWVL]\)-[CHM][0-9]" TRIADE-*design-0.17.0.md
```

and recovered **82 of 139 rules**. Two independent defects: the character class **omits `P`**, dropping all twelve P rules although they are correctly table-formatted; and **H's fifteen invariants live in a fenced code block**, which no `^|` pattern can reach. A command that silently returns 59% of the suite is worse than none, because it looks like it worked. Registered as **◇P7a**.

**One pass, implementing P-C8 — run at 0.19.0, recovered 135 of 140; re-run now it recovers 142 of 142.**

```bash
grep -rhoE '^[[:space:]|>│├└─]*[-*•]?[[:space:]]*\**`?(TILE|[TKMHEWVLPG])-[CHM][0-9]+' \
  [A-Z]-*_design_TRIADE-0_29_0.md C-Content_Authoring_Technical_Specification_TRIADE-0_29_0.md \
  | grep -oE '(TILE|[TKMHEWVLPG])-[CHM][0-9]+' | sort -u
```

**It replaces the two-pass command, which could not see prose or bullet forms.** The leading character class exists because a rule may lead a table cell, a list item, a prose sentence in bold, or a line inside a fenced ASCII workflow — H states fifteen invariants in a code block, and M·5.4 states `M-H1` inside box-drawing art. **P-C8 is a positional rule, not a formatting rule**, so the command tests position.

**Version-scope trap.** Both previous commands globbed a version string and silently matched **zero files** after a rename. The glob above must be advanced with every bump; if it returns fewer than the indexed total, check the scope before concluding anything about the corpus.

**The residual was ◇P7, and the census has run.** At 0.19.0 all 140 rules were measured against a positional test — **the ID leads its line or its first table cell**, changelogs excluded. **135 are authored; five are not.** Twenty-five rows were authored in the same pass (W§16 ×17, M ×5, V ×3).

> `L-M1` `L-M2` — authored in `Z-Design_Stream_Project_Instructions_TRIADE-0_29_0.md`, which this index does not treat as a source. Home mis-assigned.
> `M-C5` — its own row here cites `T · 4.8`. Home mis-assigned.
> `M-C3` `M-H4` — no statement exists to tag. These need a rule written.

**The test is rule P-C8.** `◈P7` closed at 0.20.0 and the two methods agree at **142 of 142** — the command recovers exactly what the census counts as authored.

**The single pass reaches every rule.** ◈P7 closed at 0.20.0, so no indexed rule lacks a source row and no exception remains.

Every rule in a source document must appear here with the same ID and severity; every rule here must have a source. Divergence is a defect.

---

## Changelog

| Version | Change |
| --- | --- |
| **0.29.0** | **M-C11 indexed; M-C9 and M-C10 restated.** Suite recounted by measurement. |
| **0.28.0** | **M-C9 and M-C10 indexed** from M·2A.11. Suite recounted by measurement. |
| **0.27.0** | Suite 143 → **145** with `T-C14` and `E-C7`; recounted — **83 / 48 / 14**. Character system opened: lineage, size and the stat-space conservation that binds them. |
| **0.26.0** | M10 equipment closeout dispositioned — three findings backlogged or enforced elsewhere, one authored. No AUTHORED DESIGN DECISION this run. |
| **0.25.0** | Medium armour pulls toward the barycentre. The mechanism authored at 0.24.0 was dynamic where 2A.7 is positional; this one is positional. |
| **0.24.0** | Fourth weight class adopted. No new quantity invented — the class occupies a seat the dot model already had. |
| **0.23.0** | M10 dependency handoff dispositioned — one authored design decision centralised, one finding backlogged, three accepted. |
| **0.22.0** | **Ref `R`, not `X`** — `X` is the generic document-letter placeholder in twenty-one template sites, so taking it would have made `X-C1` read as a rule of this index. §8's glob repointed and re-run: **143 of 143**. Filename convention adopted — `<REF>-<Name>_TRIADE-[V_e_r].md`. The ref letter leads so the folder reads at a glance; `TRIADE` moves into the stem. |
| **0.21.0** | Suite 141 → 142 with `P-C10`, recounted — **80 / 48 / 14**. The technical-stream instructions enter the governed set as `TRIADE-Technical_Stream_Project_Instructions-[V_e_r].md`; the central instructions are renamed `TRIADE-Design_Stream_Project_Instructions-[V_e_r].md`. Both carry the design-set version in the filename as a co-authorship marker. |
| **0.20.0** | Suite 140 → 141 with `P-H5` *(authored as `P-C9`)*, recounted by counting — **79 / 48 / 14**. The published command now recovers **all 141**. Corpus normalised to `markdownlint` under a tracked `.markdownlint.jsonc`; 1,956 table separators unified. Content-equivalence proven by whitespace-normalised diff against `Archive/v0.19.0/`. |
| **0.19.0** | **Suite 139 → 140** with `P-C8`; recounted by counting — **79 / 47 / 14**. §8's two-pass command replaced by a single positional pass that **recovers 135 of 140**, the five it misses being exactly ◇P7. Census result published. Subsection headings lost the document letter — `### V4.1` → `### 4.1` — completing the 0.18.0 pass, which had changed `## Part Xn` and left `### Xn.n`. Bare `Xn.n` references normalised to `X·n.n`. |
| **0.18.1** | Non-goals take **⦻** (`⦻Xn`), the sixth and last unglyphed identifier namespace. No design decision changed. |
| **0.18.0** | The published regeneration command corrected and **run**: 109 of 139, up from 82. Its scope had matched zero files after the underscore rename. The residual thirty are ◇P7 and are now listed by ID rather than counted. Identifier glyphs adopted set-wide — `◇` live open item, `◈` closed, `◉` goal, `⇥` phase, `⌬` skill level. Stale spaced filenames repointed to the underscored convention. **22 glyphed identifiers in this document.** |
| **0.17.0** | **No rules added or removed — 139 holds (78 / 47 / 14), recounted by counting.** **`M-C1` reworded and given a source row.** It now states the handedness pip budget (`1h` = 3, `2h` = 4) with redistribution conserving that base total, and M·2A.9 finally carries the ID-bearing row it had lacked since 0.11.0 — the invariant stays one ID rather than becoming a second unnumbered gate. **P7 corrected from seventeen to at least nineteen:** `M-C1`, `M-C2` and `W-C4` had no row in their home document in any form and were missing from the list; `M-C1` is now closed. The figure is stated as a floor because no single grep pattern fits all ten documents' rule formats and the marker census has not been run. **§8's regeneration command was found not to regenerate this index** — it recovered 82 of 139, omitting `P` from its character class and unable to reach H's code-block invariants. Corrected to two passes, with the residual gap named. New item **P7a**. |
| **0.16.0** | **No new rules. The suite was recounted and seven were refiled.** `P-C1`…`P-C7` and `P-M1` had been entered into **§3 High** at 0.15.0 — seven Criticals and a Medium filed under the wrong severity, against P·Part 9 which states them correctly. Printed section totals had read **60 / 38 / 13 = 111 since 0.12.0**, while the changelog rows tracked a separate running figure reaching **133**, and the tables actually held **139**. Three numbers from three sources, none agreeing, none derived by counting. **Totals are now counted from the rows: 78 / 47 / 14 = 139.** New open item **P7**: seventeen rules here have no ID-bearing row in their source document, so for those this index is authored rather than derived — the same defect found in T at 0.13.0, and the fix belongs in the sources. `P-C6` reworded to match P·3.2. |
| **0.15.0** | **Twelve rules added — 133 total (73 Critical, 46 High, 14 Medium).** All from the new **P** document. **P-C2** is the one worth noting: fixed-point persistence is not a new constraint but **W-C10 made physical** — the digest firewall already barred float-derived values, and nothing had stated what that meant for storage. **P-C7** closes the loop the fixture set opened: a locked subsystem must name its proving fixture or declare the gap. |
| **0.14.0** | **Two rules added — 121 total (66 Critical, 42 High, 13 Medium).** **M-H5** expresses T-H1's named-brake requirement in the power layer: no interaction may carry more than ~20% of a band's log-power gain without an authored drawback. **E-H6** binds the enemy tier mix to M·9.7's encounter budget — with a ×9 career multiple, enemy scaling that raises health alone lengthens combat without testing the Triade, and cleared bands trivialise. |
| **0.13.0** | **Eight rules added — 119 total (66 Critical, 40 High, 13 Medium).** T-C11 (corner-floor render affinity, closing ◈T6 after two versions), T-C12 (every source resolves to a record — the hole that let `capability` persist as an enum value with no object), T-C13 (Combo-Action declares exactly two hooks), H-C6, H-C7, H-H5, H-H6, E-C5, E-C6, E-H5. **T gained an authored rule table** (Part ◈H2): T-C1…T-C10 had circulated since 0.11.0 with no source table, so this index was authored rather than derived for one whole document while declaring otherwise. |
| **0.12.0** | Regenerated for the nine-document set. **36 rules added** — 20 Critical, 15 High, 1 Medium. New rule families: W's vertical and progression rules (W-C8…C20, W-H7…◇H14, W-M6), V's render proof suite (V-C1…C4), M's progression-attribute protection (M-C6…C8) and the Tile Pipeline suite (TILE-C1…C4, ◈H1…◈H4, ◈M1…◇M3). **The digest firewall is now a rule** (W-C10): render proofs fail the build, never the seed. W-H1 clarified — `complex_room` exempts the 2-zone floor only, so K·4 stands unamended. Three L-M2 catches recorded. One new coverage gap: the render proofs are specified and unrunnable. |
| **0.11.0** | Index created. Three incompatible severity schemes unified. K16's flat list assigned severities. Metrics moved to the SIM Register. L-M1 and L-M2 added. |
