# NHESS Reviewer Reproducibility Assets

This directory is the lightweight reproducibility package for the revised NHESS submission.
It is designed for the NHESS "Assets" field and for reviewers who need to inspect the
frozen numerical evidence without downloading the full local raster workspace.

Repository: https://github.com/egpark-knu/landslidekr

## What This Package Reproduces

- The protocol/label-source skill matrix used in the revised manuscript.
- The perturbation-screen table showing that simple model/input changes do not rescue the baseline failure.
- The manuscript terrain and aggregate diagnostic summaries.
- The frozen input tables behind the revised Figure 1 to Figure 4 summaries.

The package intentionally does not redistribute large raster inputs, raw Earth Engine exports,
private credentials, or local workspace paths. Path-like values inside the frozen tables are
sanitized with the `REPO_ROOT/` placeholder where needed.

## Quick Check

From the repository root:

```bash
python3 nhess_reproducibility/scripts/verify_package.py
python3 nhess_reproducibility/scripts/reproduce_summary_tables.py --out nhess_reproducibility/derived
```

Both scripts use only the Python standard library.

## Directory Layout

- `data/frozen_tables/` - small CSV tables frozen from the accepted NHESS revision workflow.
- `metadata/manifest.json` - SHA-256, row counts, source provenance, and required columns.
- `scripts/verify_package.py` - integrity, schema, path-hygiene, and size checks.
- `scripts/reproduce_summary_tables.py` - regenerates compact reviewer-facing summary tables.
- `derived/` - generated outputs from `reproduce_summary_tables.py`.

## Scope Boundary

End-to-end regeneration from satellite/rainfall archives requires the main project pipeline,
Earth Engine authentication, and public EO datasets listed in the repository README. This package
is the review-time numerical audit layer: it preserves the exact small tables used for the NHESS
revision and provides deterministic checks over those tables.
