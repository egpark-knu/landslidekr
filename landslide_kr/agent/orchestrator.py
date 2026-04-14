"""
LandslideKR LLM-Agent Orchestrator.

The core novel contribution of the paper: an agent that autonomously executes
the full nowcasting pipeline given only a case config.

Steps:
    1. Parse case config (AOI, event window, model params)
    2. Fetch DEM tile(s) for AOI
    3. Fetch rainfall via GPM IMERG (GEE)
    4. Detect landslide scars via Sentinel-2 NDVI change (GEE)
    5. Fetch NIDR records from data.go.kr
    6. Derive slope / upslope area / contour length from DEM
    7. Run physical model (SHALSTAB primary, TRIGRS optional)
    8. Evaluate against NIDR + Sentinel-2 labels (POD/FAR/CSI)
    9. Generate report (maps + metrics + natural-language summary)

Agent roles:
    - Tool router: chooses which collector/model to invoke
    - Parameter inferencer: fills missing params from soil class / literature
    - Self-checker: runs sanity tests (e.g., slope range, rainfall magnitude)
    - Reporter: composes human-readable summary

This module provides the pipeline skeleton + pluggable LLM client interface.
The actual LLM decisions (tool selection, report drafting) go through
`AgentLLMClient` — a thin adapter over Claude/Codex/Gemini.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional

from landslide_kr.io.case_config import CaseConfig

log = logging.getLogger(__name__)


@dataclass
class AgentTrace:
    """Log of agent decisions for reproducibility + paper figures."""

    steps: list[dict] = field(default_factory=list)

    def add(self, step: str, tool: str, inputs: dict, outputs: dict, rationale: str = "") -> None:
        self.steps.append({
            "step": step,
            "tool": tool,
            "inputs": inputs,
            "outputs": outputs,
            "rationale": rationale,
        })

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.steps, f, indent=2, ensure_ascii=False)


@dataclass
class RunResult:
    case_id: str
    status: str  # "success" | "partial" | "failed" | "dry-run"
    artifacts: dict          # {dem: path, rain: path, scar: path, prediction: path}
    metrics: Optional[dict] = None
    trace: Optional[list] = None
    message: str = ""


class LandslideAgent:
    """
    Orchestrator agent for a single case.

    Usage:
        agent = LandslideAgent(case_cfg)
        result = agent.run(dry_run=False)
    """

    def __init__(
        self,
        cfg: CaseConfig,
        work_dir: Optional[Path] = None,
        llm_client: Optional[Callable] = None,
    ):
        self.cfg = cfg
        self.work_dir = work_dir or Path("out") / cfg.case_id
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.trace = AgentTrace()
        self.llm_client = llm_client  # optional; if None, uses deterministic defaults

    # ─── Pipeline steps ──────────────────────────────────────────────────────

    def step_fetch_rainfall(self, dry_run: bool = False) -> Optional[Path]:
        """
        Fetch cumulative rainfall from GPM IMERG V07 into a LOCAL GeoTIFF.

        Uses export_mode='local' (streaming download) by default so the file is
        actually available on disk for downstream step_run_model. Drive export
        breaks the local pipeline; only use it for very large AOIs by overriding
        cfg.model_params['rainfall_export_mode'] = 'drive'.
        """
        bbox = self.cfg.aoi.bbox
        start = self.cfg.event_window.start
        end = self.cfg.event_window.end
        out = self.work_dir / "rain.tif"

        if dry_run:
            self.trace.add("fetch_rainfall", "gpm_imerg", {"bbox": bbox, "start": start, "end": end},
                           {"out_path": str(out), "dry_run": True},
                           "dry-run: skipping GEE call")
            return out

        export_mode = str(self.cfg.model_params.get("rainfall_export_mode", "local"))
        from landslide_kr.collectors.gpm_imerg_rainfall import cumulative_rainfall_mm
        meta = cumulative_rainfall_mm(bbox, start, end, out, export_mode=export_mode)
        self.trace.add("fetch_rainfall", "gpm_imerg",
                       {"bbox": bbox, "export_mode": export_mode}, meta,
                       f"GPM IMERG V07 cumulative (export_mode={export_mode})")
        return out

    def step_detect_scars(self, dry_run: bool = False) -> Optional[Path]:
        """
        Detect Sentinel-2 landslide scars into a LOCAL GeoTIFF.

        Uses export_mode='local' (streaming) by default so scars.tif is
        on-disk for step_build_consensus_label. Override with
        cfg.model_params['scar_export_mode'] = 'drive' for large AOIs.
        """
        bbox = self.cfg.aoi.bbox
        start = self.cfg.event_window.start
        end = self.cfg.event_window.end
        out = self.work_dir / "scars.tif"

        if dry_run:
            self.trace.add("detect_scars", "sentinel2_ndvi", {"bbox": bbox},
                           {"out_path": str(out), "dry_run": True},
                           "dry-run: skipping GEE call")
            return out

        export_mode = str(self.cfg.model_params.get("scar_export_mode", "local"))
        # HP Round 2 Decision A: allow loose threshold + longer post window via cfg
        ndvi_drop = float(self.cfg.model_params.get("scar_ndvi_drop", 0.20))
        post_max = float(self.cfg.model_params.get("scar_post_ndvi_max", 0.30))
        min_slope = float(self.cfg.model_params.get("scar_min_slope_deg", 10.0))
        pre_days = int(self.cfg.model_params.get("scar_pre_days", 60))
        post_days = int(self.cfg.model_params.get("scar_post_days", 30))
        # Auto-scale for large AOI (GEE local getDownloadURL has 50MB limit)
        area_deg2 = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        default_scale = 30 if area_deg2 > 0.2 else 10  # Pohang 0.06°² → 10m, Yecheon 0.91°² → 30m
        scale_m = int(self.cfg.model_params.get("scar_scale_m", default_scale))

        from landslide_kr.collectors.sentinel_landslide_scar import detect_landslide_scars
        meta = detect_landslide_scars(
            bbox, start, end, out,
            ndvi_drop_threshold=ndvi_drop,
            post_ndvi_max=post_max,
            min_slope_deg=min_slope,
            pre_days=pre_days,
            post_days=post_days,
            scale_m=scale_m,
            export_mode=export_mode,
        )
        self.trace.add("detect_scars", "sentinel2_ndvi",
                       {"bbox": bbox, "export_mode": export_mode,
                        "ndvi_drop": ndvi_drop, "post_ndvi_max": post_max,
                        "min_slope_deg": min_slope,
                        "pre_days": pre_days, "post_days": post_days},
                       meta,
                       f"NDVI drop + slope filter (export={export_mode})")
        return out

    def step_fetch_nidr(self, dry_run: bool = False) -> Optional[Path]:
        """Fetch NIDR records, filter by AOI bbox + event window, optionally geocode."""
        bbox = self.cfg.aoi.bbox
        out = self.work_dir / "nidr.geojson"

        if dry_run:
            self.trace.add("fetch_nidr", "data_go_kr", {"bbox": bbox},
                           {"out_path": str(out), "dry_run": True},
                           "dry-run: skipping API call")
            return out

        from landslide_kr.io.nidr_loader import (
            fetch_records, records_to_geojson, backfill_coords_by_geocoding
        )
        year = int(self.cfg.event_window.start[:4])
        records = fetch_records(year=year)

        # Attempt geocoding for records without coords
        n_geocoded = 0
        if any(r.lon is None or r.lat is None for r in records):
            try:
                n_geocoded = backfill_coords_by_geocoding(records)
            except Exception as e:
                log.warning(f"Geocoding failed (continuing without): {e}")

        # Filter: year-level match + coords within AOI bbox.
        # NIDR records from data.go.kr service 15074816 are at annual resolution only
        # (the API returns a year field; occurrence_date is populated as `YYYY-01-01` in
        # landslide_kr/io/nidr_loader.py:161). Exact event-day filtering would drop every
        # record, so we match on event-year and bbox, consistent with §2.3 of the manuscript
        # which discloses the annual resolution of the NIDR record. This is the path that
        # reproduces the released nidr.geojson artifacts (Yecheon 273 in-bbox, Chuncheon 18
        # in-bbox) and the §5.6 Axis-6 ablation counts.
        from datetime import datetime
        win_start = datetime.fromisoformat(self.cfg.event_window.start).date()
        event_year = win_start.year
        min_lon, min_lat, max_lon, max_lat = bbox

        def _in_year(r):
            if not r.occurrence_date:
                return False
            try:
                s = str(r.occurrence_date)
                if len(s) >= 4 and s[:4].isdigit():
                    return int(s[:4]) == event_year
            except Exception:
                pass
            return False

        def _in_bbox(r):
            return (r.lon is not None and r.lat is not None
                    and min_lon <= r.lon <= max_lon and min_lat <= r.lat <= max_lat)

        n_total = len(records)
        filtered = [r for r in records if _in_year(r) and _in_bbox(r)]
        records_to_geojson(filtered, out)
        self.trace.add("fetch_nidr", "data_go_kr",
                       {"year": year, "bbox": bbox,
                        "window": [self.cfg.event_window.start, self.cfg.event_window.end],
                        "filter_mode": "annual_year_plus_bbox"},
                       {"n_total": n_total, "n_geocoded": n_geocoded,
                        "n_after_filter": len(filtered), "out_path": str(out)},
                       "data.go.kr ID 15074816 + AOI/year filter + geocoding (NIDR API is annual-resolution; see §2.3)")
        return out

    def step_build_consensus_label(self) -> Optional[Path]:
        """
        Build consensus label raster = (NIDR points rasterized) ∪ (Sentinel-2 scars).

        Saves to work_dir/consensus_label.tif. Returns path or None if neither available.
        """
        import numpy as np
        import rasterio

        scar_path = self.work_dir / "scars.tif"
        nidr_path = self.work_dir / "nidr.geojson"
        out = self.work_dir / "consensus_label.tif"
        dem_tif = self.work_dir / "dem_utm.tif"

        if not dem_tif.exists():
            self.trace.add("consensus_label", "skip",
                           {"reason": "no DEM UTM available"}, {}, "")
            return None

        with rasterio.open(dem_tif) as ds:
            ref_shape = (ds.height, ds.width)
            ref_transform = ds.transform
            ref_crs = ds.crs
            profile = ds.profile.copy()

        consensus = np.zeros(ref_shape, dtype=np.uint8)

        # Layer 1: Sentinel-2 scars (if available, reproject to DEM grid)
        if scar_path.exists():
            try:
                from rasterio.warp import reproject, Resampling
                with rasterio.open(scar_path) as sds:
                    scar_rep = np.zeros(ref_shape, dtype=np.uint8)
                    reproject(
                        source=sds.read(1), destination=scar_rep,
                        src_transform=sds.transform, src_crs=sds.crs,
                        dst_transform=ref_transform, dst_crs=ref_crs,
                        resampling=Resampling.nearest,
                    )
                    consensus = np.maximum(consensus, (scar_rep > 0).astype(np.uint8))
            except Exception as e:
                log.warning(f"scar reproject failed: {e}")

        # Layer 2: NIDR points rasterized (20 m buffer)
        n_nidr_points = 0
        if nidr_path.exists():
            try:
                import geopandas as gpd
                from rasterio.features import rasterize
                gdf = gpd.read_file(nidr_path)
                if gdf.crs != ref_crs:
                    gdf = gdf.to_crs(ref_crs)
                n_nidr_points = len(gdf)
                if n_nidr_points > 0:
                    buffer_m = 30.0
                    gdf_buffered = gdf.copy()
                    gdf_buffered["geometry"] = gdf_buffered.geometry.buffer(buffer_m)
                    shapes = [(geom, 1) for geom in gdf_buffered.geometry]
                    nidr_rast = rasterize(shapes, out_shape=ref_shape, transform=ref_transform, fill=0, dtype="uint8")
                    consensus = np.maximum(consensus, nidr_rast)
            except Exception as e:
                log.warning(f"NIDR rasterize failed: {e}")

        profile.update(count=1, dtype="uint8", compress="deflate")
        with rasterio.open(out, "w", **profile) as dst:
            dst.write(consensus, 1)

        self.trace.add("consensus_label", "NIDR ∪ scars",
                       {"scar_path": str(scar_path) if scar_path.exists() else None,
                        "nidr_path": str(nidr_path) if nidr_path.exists() else None},
                       {"n_nidr_points": n_nidr_points,
                        "positive_fraction": float((consensus > 0).mean()),
                        "out_path": str(out)},
                       "consensus of NIDR buffered points and Sentinel-2 scars")
        return out

    def step_run_model(self, dry_run: bool = False, rain_tif: Optional[Path] = None) -> Optional[Path]:
        """
        End-to-end model execution: DEM mosaic → topo → lithology → SINMAP-style ensemble.

        Requires:
            - self.cfg has `dem_root`, `geology_path` attributes (or attribute on cfg object)
            - rain_tif: path to rainfall TIFF (from step_fetch_rainfall, or pre-computed)
        """
        out = self.work_dir / "prediction.tif"
        prob_out = self.work_dir / "prob_unstable.tif"
        model_name = self.cfg.model_name.upper()

        if dry_run:
            self.trace.add("run_model", model_name, self.cfg.model_params,
                           {"out_path": str(out), "dry_run": True},
                           "dry-run: skipping model execution")
            return out

        if model_name != "SHALSTAB":
            raise NotImplementedError(f"Model {model_name} not yet supported")

        import numpy as np
        import rasterio

        # 1. DEM mosaic + reproject
        dem_root_raw = getattr(self.cfg, "dem_root", None)
        if dem_root_raw is None:
            raise ValueError("cfg.dem_root is required for model run")
        dem_root = Path(dem_root_raw)
        dem_tif = self.work_dir / "dem_utm.tif"
        from landslide_kr.preprocess.dem_mosaic import build_dem_for_case
        dem_meta = build_dem_for_case(self.cfg.aoi.bbox, dem_root, dem_tif)
        self.trace.add("dem_mosaic", "build_dem_for_case",
                       {"bbox": self.cfg.aoi.bbox, "root": str(dem_root)}, dem_meta,
                       "mosaic + reproject to UTM")

        # 2. Topo (slope + upslope area). Backend tier auto-selected per topo.compute_topo:
        #    richdem Dinf > pysheds D8 > numpy D8. Recorded rationale reflects actual tier used.
        from landslide_kr.preprocess.topo import compute_topo
        topo = compute_topo(dem_tif)
        try:
            import richdem  # noqa: F401
            topo_backend = "richdem Dinf"
        except ImportError:
            try:
                import pysheds  # noqa: F401
                topo_backend = "pysheds D8"
            except ImportError:
                topo_backend = "numpy D8 fallback"
        self.trace.add("topo", "compute_topo", {"dem": str(dem_tif)},
                       {"shape": list(topo.slope_rad.shape), "backend": topo_backend},
                       f"flow accumulation + slope ({topo_backend})")

        # 3. Lithology (GPKG → class raster, fallback to default)
        from landslide_kr.io.lithology_loader import load_or_default
        geology_path = getattr(self.cfg, "geology_path", None)
        lith_arr = load_or_default(Path(geology_path) if geology_path else None, dem_tif)
        self.trace.add("lithology", "load_or_default",
                       {"source": str(geology_path) if geology_path else "default"},
                       {"shape": list(lith_arr.shape)},
                       "Korean geology GPKG → class array (default fallback)")

        # 4. Rainfall array (resampled to DEM grid) — m/s averaged over event window
        from datetime import datetime
        delta = datetime.fromisoformat(self.cfg.event_window.end) - \
                datetime.fromisoformat(self.cfg.event_window.start)
        event_seconds = max(delta.total_seconds(), 3600.0)

        if rain_tif and Path(rain_tif).exists():
            from rasterio.warp import reproject, Resampling
            with rasterio.open(rain_tif) as rain_ds, rasterio.open(dem_tif) as dem_ds:
                rain_resampled = np.zeros(topo.slope_rad.shape, dtype=np.float32)
                reproject(
                    source=rain_ds.read(1), destination=rain_resampled,
                    src_transform=rain_ds.transform, src_crs=rain_ds.crs,
                    dst_transform=dem_ds.transform, dst_crs=dem_ds.crs,
                    resampling=Resampling.bilinear,
                )
            # rain_tif is in mm total over event window; convert to m/s
            rain_m_per_s = (rain_resampled / 1000.0) / event_seconds
        else:
            # Fallback: uniform synthetic rainfall from cfg.cumulative_mm / event seconds
            rain_mm = float(getattr(self.cfg, "cumulative_mm", 400.0))
            rain_m_per_s = np.full(
                topo.slope_rad.shape,
                (rain_mm / 1000.0) / event_seconds,
                dtype=np.float32,
            )

        # 5. SINMAP-style Monte Carlo ensemble
        from landslide_kr.models.ensemble import run_ensemble
        ensemble_result = run_ensemble(
            slope_rad=topo.slope_rad,
            upslope_area_m2=topo.upslope_area_m2,
            contour_length_m=topo.contour_length_m,
            rainfall_m_per_s=rain_m_per_s,
            lithology_class=lith_arr,
            n_realizations=int(self.cfg.model_params.get("n_realizations", 100)),
            seed=int(self.cfg.model_params.get("seed", 42)),
        )
        self.trace.add("ensemble", "run_ensemble",
                       {"n_realizations": ensemble_result.n_realizations},
                       {"prob_min": float(ensemble_result.prob_unstable.min()),
                        "prob_max": float(ensemble_result.prob_unstable.max()),
                        "prob_mean": float(ensemble_result.prob_unstable.mean())},
                       "SINMAP-style bounded MC")

        # 6. Save outputs
        profile = {
            "driver": "GTiff", "count": 1, "dtype": "float32",
            "height": topo.slope_rad.shape[0], "width": topo.slope_rad.shape[1],
            "crs": topo.crs, "transform": topo.transform, "compress": "deflate",
        }
        with rasterio.open(prob_out, "w", **profile) as dst:
            dst.write(ensemble_result.prob_unstable, 1)
        # Binary unstable mask at p>=0.5 for convenience
        with rasterio.open(out, "w", **profile) as dst:
            dst.write((ensemble_result.prob_unstable >= 0.5).astype(np.float32), 1)

        self.trace.add("save_prediction", "rasterio",
                       {"prob_tif": str(prob_out), "mask_tif": str(out)},
                       {"p>=0.5_fraction": float((ensemble_result.prob_unstable >= 0.5).mean())},
                       "prob_unstable + binary mask")

        # Attach ensemble result to agent for downstream evaluation
        self._last_ensemble = ensemble_result
        return out

    def step_evaluate(self, pred_path: Path, label_path: Path, dry_run: bool = False) -> Optional[dict]:
        """Evaluate binary mask (POD/FAR/CSI/F1) AND continuous probability (ROC-AUC)."""
        if dry_run:
            self.trace.add("evaluate", "confusion_matrix+roc_auc",
                           {"pred": str(pred_path), "label": str(label_path)},
                           {"dry_run": True},
                           "dry-run: skipping evaluation")
            return None

        try:
            import rasterio
            import numpy as np
            from landslide_kr.metrics.evaluation import confusion_from_arrays, roc_auc

            with rasterio.open(pred_path) as ds:
                pred = ds.read(1)
            with rasterio.open(label_path) as ds:
                label = ds.read(1)
            stats = confusion_from_arrays(pred > 0, label > 0)
            metrics = stats.to_dict()

            # Continuous ROC-AUC from prob_unstable.tif if available
            prob_path = self.work_dir / "prob_unstable.tif"
            if prob_path.exists():
                with rasterio.open(prob_path) as ds:
                    prob = ds.read(1)
                auc_res = roc_auc(prob, label > 0, n_thresholds=30)
                metrics["ROC_AUC"] = auc_res["auc"]
                metrics["n_roc_points"] = len(auc_res["roc_points"])

            self.trace.add("evaluate", "confusion_matrix+roc_auc",
                           {"pred": str(pred_path), "label": str(label_path),
                            "prob": str(prob_path) if prob_path.exists() else None},
                           metrics,
                           "TP/FP/FN/TN + POD/FAR/CSI/F1 + ROC-AUC")
            return metrics
        except Exception as e:
            log.warning(f"evaluate failed: {e}")
            return None

    # ─── Main entry ──────────────────────────────────────────────────────────

    def run(self, dry_run: bool = False, skip: Optional[set] = None) -> RunResult:
        """
        Execute the full pipeline.

        Args:
            dry_run: skip actual GEE/API calls, just trace the plan
            skip: set of step names to skip (e.g., {"detect_scars"} if already have labels)
        """
        skip = skip or set()
        artifacts: dict = {}

        try:
            # Initialize GEE once if needed (skip in dry-run)
            if not dry_run and ("fetch_rainfall" not in skip or "detect_scars" not in skip):
                from landslide_kr.io.gee_init import init_ee
                gee_info = init_ee(project=getattr(self.cfg, "gee_project", None))
                self.trace.add("gee_init", "init_ee",
                               {"project": getattr(self.cfg, "gee_project", None)},
                               gee_info, "Earth Engine initialized")

            if "fetch_rainfall" not in skip:
                artifacts["rain"] = self.step_fetch_rainfall(dry_run)
            if "detect_scars" not in skip:
                try:
                    artifacts["scars"] = self.step_detect_scars(dry_run)
                except Exception as e:
                    log.warning(f"detect_scars failed (non-fatal): {e}")
                    self.trace.add("detect_scars", "sentinel2_ndvi",
                                   {}, {"error": str(e)}, "non-fatal failure")
            if "fetch_nidr" not in skip:
                try:
                    artifacts["nidr"] = self.step_fetch_nidr(dry_run)
                except Exception as e:
                    log.warning(f"fetch_nidr failed (non-fatal): {e}")
                    self.trace.add("fetch_nidr", "data_go_kr",
                                   {}, {"error": str(e)}, "non-fatal failure")
            if "run_model" not in skip:
                # Pass rainfall artifact into model execution (structural wiring)
                rain_path = artifacts.get("rain")
                rain_path_real = Path(rain_path) if rain_path and Path(rain_path).exists() else None
                artifacts["prediction"] = self.step_run_model(dry_run, rain_tif=rain_path_real)

            metrics = None
            if not dry_run and "evaluate" not in skip and artifacts.get("prediction"):
                # Build consensus label (NIDR ∪ scars) if possible
                consensus = self.step_build_consensus_label()
                label_path = consensus or artifacts.get("scars") or self.cfg.label_path
                if label_path and Path(label_path).exists():
                    metrics = self.step_evaluate(artifacts["prediction"], Path(label_path), dry_run)

            self.trace.save(self.work_dir / "agent_trace.json")
            return RunResult(
                case_id=self.cfg.case_id,
                status="dry-run" if dry_run else ("success" if metrics else "partial"),
                artifacts={k: str(v) for k, v in artifacts.items()},
                metrics=metrics,
                trace=self.trace.steps,
                message="Pipeline complete" if metrics else "Pipeline partial (no eval)",
            )
        except Exception as e:
            log.exception("Pipeline failed")
            self.trace.save(self.work_dir / "agent_trace.json")
            return RunResult(
                case_id=self.cfg.case_id,
                status="failed",
                artifacts={k: str(v) for k, v in artifacts.items()},
                trace=self.trace.steps,
                message=str(e),
            )


if __name__ == "__main__":
    # Dry-run smoke test
    cfg = CaseConfig.from_json(
        Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/cases/pohang_2022/config.json")
    )
    agent = LandslideAgent(cfg)
    result = agent.run(dry_run=True)
    print(json.dumps({
        "case_id": result.case_id,
        "status": result.status,
        "artifacts": result.artifacts,
        "n_trace_steps": len(result.trace) if result.trace else 0,
    }, indent=2))
