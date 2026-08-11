# M10 Equipment Implementation Proof

**Aligned Triade version:** 0.25.0  
**Implementation date:** 11 August 2026  
**Scope:** five ◈M10 equipment revisions and their current physical child rows  
**Authority boundary:** technical implementation only; P and M own game meaning  
**Candidate state:** mechanically complete offline; active-document adoption pending  

## Source basis

- `VERSION-MANIFEST.md` — 0.25.0 handoff and required `barycentre_well` schema change.
- P·10.3 — locked five-item M10 loadout and martial profiles.
- M·2A.6 — Standard Shield integrity path.
- M·2A.7 — Medium uses a second, shallower barycentre well.
- M·2A.9 / M-C1 — one-/two-handed pip budgets.
- M·2A.11 / M-C4 — shield dual nature and one pooled budget.
- C·5–7 — concrete Grist schemas and stable IDs.

The current Drive mirror reports itself in sync in the manifest. The authoritative
`X:\Documentation` tracked store was not attached to this session, so
`tools/ledger.sh check`, `tools/history-check.sh`, and `tools/version-check.sh`
could not be run against it. Their exit codes and denominators are therefore
**not verified in this run** and remain a handoff gate.

## Implemented records

| Table | Before | After | Notes |
| --- | ---: | ---: | --- |
| `equipment` | 0 | 5 | Exact revisions: Maul, Dagger, `1h-Sword`, Shield, `1h-Mace` |
| `equipment_text` | 0 | 20 | Four `en-GB` rows per revision: display, short, description, accessibility |
| `equipment_tags` | 0 | 0 | Protected `ref_tags` is empty; no fake IDs authored |
| `damage_profile_entries` | 0 | 9 | One scalar row per damage contribution |
| `slot_occupancy` | 0 | 9 | Two-hand occupancy kept separate from delivery-hook count |
| `defence_profile_entries` | 0 | 1 | Standard Shield Physical group row; rating remains null |

The migration also changes `construction_profiles.bridge2_mechanism` metadata
to the exact four-value Choice set:

```text
edm_damping
home_well_strengthening
barycentre_well
none
```

`construction.shield_standard` reads back as `barycentre_well`.

## Locked pip proof

| Martial profile | Distribution | Total |
| --- | --- | ---: |
| `martial.maul` | Impact 3 + Shatter 1 | 4 |
| `martial.dagger` | Pierce 2 + Slash 1 | 3 |
| `martial.sword_1h` | Slash 2 + Pierce 1 | 3 |
| `martial.shield_standard` | Impact 2 | 2 |
| `martial.mace_1h` | Impact 2 + Shatter 1 | 3 |

## Executable verification

Command:

```text
python3 -m unittest -v \
  tests/test_m10_dependencies.py \
  tests/test_m10_equipment.py \
  tests/test_r7.py
```

Result: **7 tests passed**.

Verified:

- exact unique revision and child stable IDs;
- stable-ID Reference resolution and readback;
- unresolved chassis Reference rejection with zero equipment writes;
- idempotent second application;
- byte-identical seed/export for all six tables;
- exact 4/3/3/2/3 pip totals;
- Maul occupies two primary/required hand units but exposes one active hook;
- one-hand canonical occupancy for the other four revisions;
- Standard Shield has weapon, construction, integrity and defence components;
- null shield defence rating is preserved as SQL `NULL`, not zero;
- dependency counts preserved at 5/1/3/2;
- R7 preserved at 143 rules and 81/48/14;
- SQLite integrity result `ok`.

## Deterministic hashes

| Artefact | SHA-256 |
| --- | --- |
| Source dependency candidate | `4c60458caf1af1e3542b31b310b929843714d40e6ebe77ebb4f2bd86501d7e27` |
| Equipment candidate | `c6dc5d19a95f568e135ab024a5270d4bdb5868f94d9dc4942dfd86ddf6543401` |
| `equipment.csv` | `b87acc3d2fc5ee78e570eba195edf01804ec2f28b80af258bdfae03002b911d9` |
| `equipment_text.csv` | `1cf2f0ee9abe90af84b63acfaffb6b7ee53ebfc697a6ae8a878b5628aef43aae` |
| `equipment_tags.csv` | `bdc1fda1d000789ad7a4729de5ff1628761d7fd610a39acbc0be949706e046fe` |
| `slot_occupancy.csv` | `820935f0c3819a1fdbe0868446974f28a5b91886ddcb49bd1acbc29c2b64db17` |
| `damage_profile_entries.csv` | `81e6ccdd9d644adca02e1fd499d5e5747331c8bca2949287e3f077ea96b004f3` |
| `defence_profile_entries.csv` | `d4480e20c0b78f928544226a37ae7467eff8e49473246582e1470cb0a6f6d65b` |

Seed and export hashes match pairwise for all six CSVs.

## Unverified or deliberately unresolved

- Standard Shield numeric defence magnitude and pooled-budget scale are not
  source-owned. The Physical row exists; `rating_value` stays null.
- `ref_tags` is empty. `equipment_tags` stays header-only.
- Canonical `equipment.schema.json` is still a placeholder, so equipment
  `schema_version` stays blank.
- Active Grist adoption and visual verification are not part of this offline run.
- Faculty and fixture rows are the next population stage.

No `AUTHORED DESIGN DECISION` was required in this run.
