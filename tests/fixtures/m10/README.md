# M10 reference fixture set

## Purpose

`m10-v1` is the frozen reference set for the Triade equipment, faculty,
fixture, combat, stat, and trace pipelines. It is validation content, not
production game content.

## Reference builds

| Build | Floor `(m,f,i)` | Home | Equipment |
| --- | --- | --- | --- |
| Striker | `(0.25, 0.15, 0.05)` | Pressure | Maul |
| Controller | `(0.09, 0.18, 0.18)` | Discipline | 1h-Sword + Standard Shield |
| Technical | `(0.15, 0.10, 0.20)` | Instinct | Twin Daggers |
| Trickster | `(0.12, 0.08, 0.25)` | Instinct | Single Dagger; off hand empty |
| War Priest | `(0.15, 0.20, 0.10)` | Discipline | 1h-Mace; off hand empty |

Stat weights are relative and dimensionless. The future harness supplies and
normalizes the absolute budget.

## Faculty identities

- `faculty.innate_upper@1`
- `faculty.innate_bite@1`
- `faculty.arcana@1`
- `faculty.mudra@1`
- `faculty.psyche@1`

The identity and anatomical delivery/gate fields are populated. Concrete base
footprints, faculty origin for non-Innate families, vocabulary rows, and
build-to-faculty assignment remain explicit gaps; the fixture must not invent
them.

## Equipment profiles

- Maul: Impact 3 + Shatter 1; both hands; one delivery hook.
- Dagger: Pierce 2 + Slash 1; one independent footprint per copy.
- 1h-Sword: Slash 2 + Pierce 1.
- Standard Shield: Impact 2 plus independent defence/integrity; defence
  magnitude remains null.
- 1h-Mace: Impact 2 + Shatter 1.

## Encounter shells

The five scalar encounter rows are Corridor, Chamber, Gallery, Vault, and Den.
Their zone counts are 2, 3, 4, 3, and 3. Vault carries the source-named
`high_ground` marker. Enemy definitions and normalized encounter membership are
not represented until `◇P8` resolves their field sets.

## Coverage policy

`fixture_coverage` records 9 proving-fixture declarations and 15 explicit gaps,
including all five gaps in P·10.7. A proof row names what the future harness
must execute; it is not evidence that a simulation already passed.

Do not alter an existing fixture merely to make a failing test pass. When the
governed design changes, update the record deliberately, regenerate the exact
snapshot/export proof, and review the resulting simulation delta once a
simulator exists.
