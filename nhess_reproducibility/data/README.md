# Data Notes

`frozen_tables/` contains small CSV files copied from the final NHESS revision workflow.

Large rasters, raw Earth Engine exports, and credential-dependent downloads are not redistributed
here. Where source tables contained machine-local paths, those paths were sanitized to `REPO_ROOT/`.

The table provenance and SHA-256 checksums are recorded in `../metadata/manifest.json`.
