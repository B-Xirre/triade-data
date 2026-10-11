# Triade Tuning Lab

The local lab uses authoring schema 1.1.0 and execution schema 1.0.0. It registers every current rule and parameter, executes reviewed mathematical probes and preserves explicit capability gaps. Full encounters, credit loops, world generation, economy and usability require their declared future adapters or external evidence.

## Start locally

Set `TRIADE_LAB_DATA_HOST` to a persistent data directory and `TRIADE_GRIST_KEY_HOST` to an existing credential file outside the repository. Configure the stable active document through `TRIADE_GRIST_DOC_ID`. Run:

```text
docker compose -f lab/compose.yml build
docker compose -f lab/compose.yml up -d
```

Open `http://127.0.0.1:8765`. The deployment attaches to the existing `grist_default` network. Grist's existing container and Compose file are preserved. Its private alias is used with the configured home-domain Host header; credentials remain server-side. The API publishes only on loopback. The worker owns the DuckDB catalogue; SQLite stores durable job metadata.

## Workbench

Synchronize Grist, select an exact source revision, edit allowed fields or explicit fixture inputs and save an immutable version. Referenced unbound numeric parameters may be edited inside the experiment; the locked scale and original source rows are preserved. Choose a suite or bounded sweep and inspect results, exact metric values, traces and source requirements. Two-dimensional sweeps have a heatmap. Mathematical position probes are distinct from encounter trajectories.

Radar profile references are fixed and shared by baseline and variant. Missing measurements are unavailable, not zero. Zero components of a complete authored martial footprint are explicit computed zeros. Structural stress remains separate from typed HP quantity. Out-of-reference values are disclosed beside their exact values. Fixture examples do not bind production coefficients.

The baseline uses the pinned control fixture and original item. The variant uses its edited content and experiment inputs. Pairing holds the test context and named random streams constant. Adoption requests require an explicitly reviewed matching completed run with no failures/errors, create draft content/component revisions, retain gaps, and await the established release process. Fixture-input-only and incomplete template experiments cannot create a game-content adoption draft.

## Interfaces

FastAPI publishes `/api/v1` with OpenAPI at `/docs`: synchronization, subject/field discovery, coverage, chart profiles, immutable experiment revisions, run submission/cancellation, report/fact queries, downloads and adoption requests. Exact integers travel as decimal strings. Use `python -m lab.cli --help` for equivalent synchronization, validation, save, run, comparison and reporting commands.

New parameter or rule rows are discovered automatically. They receive a reviewed binding or explicit gap; new formula implementations and schema grains require code/schema review. Add trusted adapters against `lab.adapter_contract`, register their version/capability, source bindings, metrics and fixtures, then run the invariant and reproducibility suites. Authored equation text and assertion data are never arbitrary executable expressions.

## Evidence and recovery

Every job retains immutable snapshot, experiment, named-seed and runner-build pins. Result hashes cover logical canonical cases, metrics and comparisons, excluding packaging and wall-clock metadata. Parquet facts retain cases, metrics, requirement links and attributed calculation events. Reports distinguish pass, fail, blocked, error and not-applicable.

Cancellation preserves partial evidence. A worker restart marks running jobs interrupted and retains their manifests; resubmitting the exact manifest reproduces them. Rebuild the catalogue from retained Parquet through the worker's private `/rebuild` endpoint. Roll back application images independently of data; any failed post-promotion release restores the verified Grist backup through the guarded workflow.

The repository CI runs frozen-export tests without live Grist or credentials. Historical tests needing the retained `.grist` working copies report explicit skips in CI; the local release campaign mounts those copies read-only and must run the full suite. Historical golden datasets and the 0.46.0 canonical snapshot remain unchanged.

## Dependency policy

Python 3.12 and Node 22 base images are pinned by digest. Python and frontend locks pin all resolved versions; DuckDB is 1.5.6. Pydantic v2 validates rows and requests, JSON Schema validates snapshots, Pandera validates fact tables. Plotly assets are bundled locally. DuckDB 2.0 is a later compatibility migration.
