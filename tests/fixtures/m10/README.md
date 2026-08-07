# M10 Reference Fixture Set

## Purpose

M10 is the frozen reference fixture set used to validate the TRIADE
equipment, combat, stat, faculty, and trace pipelines.

It is not production game content.

Changes to M10 must be deliberate because validation results and
golden snapshots depend on this fixture set.

## Fixture ID

`m10-v1`

## Reference Builds

- Striker
- Controller
- Technical
- Adept

Stat values/weights in M10 are reference relationships for simulation,
not final production balance values.

## Reference Loadouts

### Maul

- Impact +++
- Shatter +
- Total: 4 pips
- Delivery hooks: 1

### Daggers

Each dagger:

- Pierce ++
- Slash +
- Total: 3 pips per dagger
- Combined loadout: two independent weapon vectors
- Delivery hooks: 2

The footprints do not pool unless used by a legal Combo-Action.

### Sword + Shield

Sword:

- Slash ++
- Impact +
- Pierce +
- Total: 4 pips

Shield:

- Impact ++
- Total: 2 pips

Delivery hooks: 2

The shield remains subject to the shared offence/defence shield budget.

### Wand + Free Hand

Wand:

- Impact +
- Total: 1 pip
- Delivery hooks: 1

The other hand remains free so the fixture can exercise Mudra legality.

## Coverage Goals

M10 must exercise, at minimum:

- one-source weapon actions
- two-source Combo-Actions
- weapon + faculty combinations
- Arcana + Mudra combinations
- free-hand requirements
- pip redistribution
- Structural damage
- shield behaviour
- exactly-two-source Combo-Action enforcement
- rejection of three-source combinations
- rejection of Arcana + Arcana as a two-hook combination where prohibited
- per-source trace attribution

## Fixture Policy

M10 is frozen reference content.

Do not alter an existing fixture merely to make a failing test pass.

When the intended design changes:

1. document the design change,
2. update the fixture deliberately,
3. regenerate affected expected results,
4. review the resulting simulation delta.

## Source

Derived from the M10 design study and the current TRIADE design
documents.

The machine-readable JSON files in this directory are authoritative
for automated tests.