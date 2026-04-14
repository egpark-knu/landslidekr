# LandslideKR Pipeline — detailed eleven-step reference

This document is the canonical detailed reference for the eleven-step `AgentTrace` pipeline summarized in §2.1 of the manuscript. It is released alongside the manuscript so that readers can re-execute the pipeline deterministically given the same public archives and the same case configuration.

## Step list

1. **`init_ee`** — initialize the Google Earth Engine project (service-account credentials under `~/.mas/gee.json`).

2. **`fetch_rainfall`** — pull GPM IMERG V07 30-minute precipitation and reduce to a per-event cumulative raster over the case window.

3. **`detect_scars`** — generate a Sentinel-2 NDVI-change scar raster from matched pre- and post-event composites (dNDVI > 0.15 AND post-NDVI < 0.35 AND slope > 10°, 60-day post window). For AOIs larger than 0.2 deg² the collector auto-scales from 10 m to 30 m to stay under the Earth Engine `getDownloadURL` 50 MB cap; Yecheon 2023 triggers this branch.

4. **`fetch_nidr`** — attempt the data.go.kr NIDR past-landslide endpoint (service ID 15074816) with optional VWorld geocoding of administrative-area addresses. The endpoint returns XML only and the Korean field names (`ctprvNm`, `sgngNm`, `lndslDmgArea`) are parsed explicitly. If the endpoint times out, the step returns a non-fatal failure and downstream label construction reverts to Sentinel-only (observed in practice on Yecheon 2023; see §2.3 of the manuscript).

5. **`dem_mosaic`** — discover pre-downloaded Copernicus DSM COG 30 m tiles (Copernicus GLO-30 DSM) for the event AOI inside the local `dem_root`, mosaic, and reproject to the local UTM zone (implementation: `landslide_kr/preprocess/dem_mosaic.py::build_dem_for_case`). This is the main DEM used by all downstream SHALSTAB computations. A separate incidental call to GEE SRTM (USGS/SRTMGL1_003) is issued inside the Sentinel-2 scar detector to apply a slope gate to candidate scar pixels; this GEE SRTM call does not affect the main DEM or the SHALSTAB computation.

6. **`topo`** — compute D8 flow accumulation via the `pysheds` Cython engine together with a Horn (1981) 3×3 slope kernel. A three-tier fallback (`richdem` → `pysheds` → numpy) is implemented because `richdem` did not build on the target Mac ARM environment.

7. **`lithology`** — rasterize the KIGAM 1:50 000 Korean geology vector onto the DEM grid, reading the principal-rock-type field and mapping to five SHALSTAB classes (granite, volcanic, sedimentary, metamorphic, alluvium). Unmapped entries default to the granite class with a logged warning.

8. **`ensemble`** — run the SINMAP-style bounded Monte Carlo SHALSTAB (manuscript §2.2) with one hundred realizations per pixel, drawing parameters from the lithology-conditional bounds of Table 4.

9. **`save_prediction`** — write the per-pixel probability-of-instability raster `prob_unstable.tif` and the binary prediction `prediction.tif` thresholded at p ≥ 0.5.

10. **`consensus_label`** — build the reference label raster from the union of the NIDR 30 m point buffer and the Sentinel-2 scar raster. Which layers contributed per event is reported in manuscript §2.3.

11. **`evaluate`** — compute confusion-matrix metrics (POD, FAR, CSI, F1, precision) via `landslide_kr.metrics.evaluation.confusion_from_arrays` and continuous ROC-AUC via the in-tree `roc_auc` helper. Per-elevation-decile scar-rate tables and the scar/non-scar mean-probability separability statistics reported in manuscript §3.1 and §3.2 are computed in the offline analysis bundle (`analysis-output/`) from the rasters this step writes, not inside `step_evaluate` itself.

## AgentTrace JSON record schema

Every step writes `step`, `tool`, `inputs`, `outputs`, and `rationale` fields into the `AgentTrace` JSON list (`landslide_kr/agent/orchestrator.py::AgentTrace.add`). The trace is append-only within a run. Failure modes are recorded inside the step's `outputs` dict (for example, the Yecheon 2023 `fetch_nidr` step records `outputs: {"error": "timed out"}`) and dry-run mode marks each step's `outputs` with a `dry_run: true` flag.

## Released traces

The Pohang 2022 case has both a dry-run trace (stored `agent_trace.json`) and an executed log run (`out/pohang_2022_run_20260414_1513_C2.log`); both artifacts are released so readers can distinguish which run produced the manuscript-reported numbers. Yecheon 2023 and Chuncheon 2020 each have a single executed trace (`out/extreme_rainfall_2023/agent_trace.json` and `out/chuncheon_2020/agent_trace.json` respectively) with all eleven steps recorded.
