# Content Authoring Technical Specification — PATCHES / INTAKE

**Aligned Triade version:** 0.25.0  
**Companion to:** `C-Content_Authoring_Technical_Specification_TRIADE-0_25_0.md`  
**Status:** central disposition pending  
**Authority:** intake only; this file authors no design rule or ID  

## TS-M10E-01 — Standard Shield defence magnitude

- **Type:** `FINDING`
- **Finding:** M·2A.11 requires independent shield defence and one pooled budget,
  but the corpus gives no numeric Standard Shield defence rating or budget scale.
- **Implementation pressure:** `defence_profile_entries.rating_value` cannot be
  populated without inventing a balance number.
- **Evidence checked:** M·2A.4, M·2A.11 / M-C4, P·7.1, P·10.3, C·5.11.
- **Affected documents:** M, P, C, Y if the value becomes a `[SIM]` parameter.
- **Recommended home:** M·2A.11 for the budget meaning; Y only for a tunable
  numeric parameter when a metric and failure path exist.
- **Recommended action:** define the budget representation and rating unit before
  choosing a magnitude. Until then keep the Physical group row and null rating.
- **Impact if not adopted:** shield structure is representable, but mitigation
  behavior cannot enter an authoritative simulation.
- **Implementation blocker:** yes — for shield mitigation, no — for record identity.
- **Central disposition:** `unresolved`.

## TS-M10E-02 — Empty equipment-tag registry

- **Type:** `FINDING`
- **Finding:** protected `ref_tags` contains zero records, so no legal
  `equipment_tags` Reference can be authored.
- **Implementation pressure:** creating plausible tag strings would bypass the
  protected registry and violate scalar/reference authoring.
- **Evidence checked:** P·2.2–2.4, P·7.1, C·4.16, C·5.5, current Grist seed.
- **Affected documents:** P, C; M/L only if tag semantics are newly designed.
- **Recommended home:** P if a minimum protected tag registry is required for the
  M10 vertical slice; otherwise leave the child table empty until tag authoring.
- **Impact if not adopted:** no current identity or martial-profile loss; tag-based
  search, generation and validation remain unavailable.
- **Implementation blocker:** no for current equipment adoption; yes for tag lints.
- **Central disposition:** `unresolved`.

## TS-M10E-03 — Canonical equipment schema version unavailable

- **Type:** `FINDING`
- **Finding:** `schema/equipment.schema.json` remains a placeholder and has no
  version contract, while equipment rows expose `schema_version`.
- **Implementation pressure:** a value would be fabricated, so all five rows keep
  `schema_version` blank.
- **Evidence checked:** P·2.1, P·3.1, C·1, C·5.3, repository schema file.
- **Affected documents:** P, C; repository schema/tooling.
- **Recommended home:** C and the implemented schema artefact, after P's logical
  model is encoded without adding design semantics.
- **Impact if not adopted:** canonical JSON validation and content-package approval
  cannot be completed.
- **Implementation blocker:** yes for canonical build; no for Grist candidate.
- **Central disposition:** `unresolved`.

## TS-M10E-04 — Central status after equipment adoption

- **Type:** `FINDING`
- **Finding:** once the candidate is adopted and verified, the manifest handoff and
  ROADMAP implementation status must move from equipment population to faculties
  and fixture records.
- **Implementation pressure:** status would otherwise remain behind the active data.
- **Evidence checked:** VERSION-MANIFEST handoff, A-ROADMAP sequencing, C·6.1 and C·9.
- **Affected documents:** VERSION-MANIFEST, A-ROADMAP, derived ledger after adoption.
- **Recommended target:** manifest handoff and the existing ROADMAP Stage 2 status;
  no design rule change.
- **Impact if not adopted:** the next session may repeat completed work.
- **Implementation blocker:** no.
- **Central disposition:** `unresolved` pending active adoption.

## No patch required

- M — all five martial profiles, shield integrity and `barycentre_well` are owned.
- P — the five M10 loadouts and normalized child-row model are sufficient.
- K and H — no combat-order or anatomy contract changed.
- L — no new player-facing term or reserved word was introduced.
- R — no validation rule was added or changed.
- B and Y — existing open/SIM items are not duplicated.
- Central and technical stream instructions — no workflow change found.

## Authored design decisions

None.
