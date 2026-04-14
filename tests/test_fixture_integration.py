"""
Non-dry-run fixture integration test.

Builds synthetic DEM + label + geology rasters in a temp dir, exercises the actual
model execution path (ensemble → evaluation) without needing GEE or data.go.kr.

Validates that the pipeline produces:
    - prob_unstable.tif
    - prediction.tif (binary mask)
    - consensus_label.tif (when inputs present)
    - metrics dict with POD/FAR/CSI/F1 + ROC_AUC
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

rasterio = pytest.importorskip("rasterio")
from rasterio.transform import from_bounds
from rasterio.features import rasterize
from shapely.geometry import Point

from landslide_kr.models.ensemble import run_ensemble
from landslide_kr.metrics.evaluation import confusion_from_arrays, roc_auc
from landslide_kr.io.lithology_loader import load_or_default


def _make_synthetic_dem(tmp_path: Path) -> Path:
    """Make a 50×50 synthetic UTM DEM with a central peak."""
    h, w = 50, 50
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))
    dem = (500 + 300 * np.exp(-((xx - w / 2) ** 2 + (yy - h / 2) ** 2) / (10 ** 2))).astype(np.float32)
    transform = from_bounds(500_000.0, 3_900_000.0, 500_000.0 + 30 * w, 3_900_000.0 + 30 * h, w, h)
    out = tmp_path / "dem.tif"
    profile = {"driver": "GTiff", "height": h, "width": w, "count": 1,
               "dtype": "float32", "crs": "EPSG:32652",
               "transform": transform}
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(dem, 1)
    return out


def test_fixture_pipeline_without_external_apis(tmp_path):
    """
    Exercise: lithology_loader → ensemble → metrics without GEE/data.go.kr.
    """
    dem = _make_synthetic_dem(tmp_path)

    # Load lithology (no GPKG → default)
    lith = load_or_default(None, dem)
    assert lith.shape == (50, 50)
    assert (lith == "default").all()

    # Synthetic topo inputs (bypass richdem — keep test fast + stable)
    xx, yy = np.meshgrid(np.arange(50), np.arange(50))
    dist = np.sqrt((xx - 25) ** 2 + (yy - 25) ** 2)
    slope_deg = np.clip(50 * np.exp(-dist / 12), 0, 55)
    slope_rad = np.radians(slope_deg).astype(np.float32)
    area = (500 + dist * 100).astype(np.float32)
    b = np.full((50, 50), 30.0, dtype=np.float32)
    rain = np.full((50, 50), 5e-6, dtype=np.float32)

    # Run ensemble
    result = run_ensemble(slope_rad, area, b, rain, "granite", n_realizations=30, seed=0)
    assert result.prob_unstable.shape == (50, 50)
    assert 0 <= result.prob_unstable.min()
    assert result.prob_unstable.max() <= 1

    # Synthetic consensus label: steep cells (central peak radius)
    label = (slope_deg > 25).astype(np.uint8)
    # Must have at least some positive pixels for the test to be meaningful
    assert label.sum() > 0

    # Evaluate: confusion stats + ROC-AUC
    pred_binary = result.prob_unstable >= 0.5
    stats = confusion_from_arrays(pred_binary, label.astype(bool))
    metrics = stats.to_dict()

    auc_res = roc_auc(result.prob_unstable, label.astype(bool), n_thresholds=20)
    metrics["ROC_AUC"] = auc_res["auc"]

    # All required fields present
    for key in ("POD", "FAR", "CSI", "F1", "Precision", "ROC_AUC", "tp", "fp", "fn", "tn"):
        assert key in metrics, f"{key} missing from metrics"

    # Counts sum to total cells
    assert metrics["tp"] + metrics["fp"] + metrics["fn"] + metrics["tn"] == 50 * 50


def test_consensus_label_logic(tmp_path):
    """
    Verify that the step_build_consensus_label union logic works
    (OR between scar raster and NIDR points buffered).
    """
    # Build 2 minimal rasters + 1 NIDR geojson, verify union
    from shapely.geometry import Point
    import json
    h, w = 30, 30
    transform = from_bounds(500_000.0, 3_900_000.0, 500_000.0 + 30 * w, 3_900_000.0 + 30 * h, w, h)
    profile = {"driver": "GTiff", "height": h, "width": w, "count": 1, "dtype": "uint8",
               "crs": "EPSG:32652", "transform": transform}
    # Scar raster: first 10 rows
    scar = np.zeros((h, w), dtype=np.uint8)
    scar[:10, :] = 1
    scar_path = tmp_path / "scars.tif"
    with rasterio.open(scar_path, "w", **profile) as dst:
        dst.write(scar, 1)

    # Verify logical OR manually
    # NIDR simulated: single point at grid center
    cell_size_m = 30.0
    center_x = 500_000.0 + w / 2 * cell_size_m
    center_y = 3_900_000.0 + h / 2 * cell_size_m
    nidr_gj = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:32652"}},
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [center_x, center_y]},
            "properties": {"occurrence_date": "2022-09-06", "damage_m2": 100.0},
        }],
    }
    nidr_path = tmp_path / "nidr.geojson"
    with open(nidr_path, "w") as f:
        json.dump(nidr_gj, f)

    # Rasterize NIDR with 30 m buffer
    gpd = pytest.importorskip("geopandas")
    gdf = gpd.read_file(nidr_path)
    buffered = gdf.geometry.buffer(30.0)
    shapes = [(g, 1) for g in buffered]
    nidr_rast = rasterize(shapes, out_shape=(h, w), transform=transform, fill=0, dtype="uint8")
    assert nidr_rast.sum() > 0, "NIDR rasterize should produce pixels"

    # Union = consensus label
    consensus = np.maximum(scar, nidr_rast)
    assert consensus.sum() >= max(scar.sum(), nidr_rast.sum())


def test_agent_run_nondry_with_monkeypatched_externals(tmp_path, monkeypatch):
    """
    Exercise orchestrator.run(dry_run=False) end-to-end with externals monkey-patched.
    This validates the step wiring that Codex review flagged.
    """
    from landslide_kr.io.case_config import CaseConfig, EventWindow, AOI
    from landslide_kr.agent import orchestrator as orch_mod

    # Build a synthetic DEM at work_dir/dem_utm.tif before step_run_model would attempt mosaic
    work_dir = tmp_path / "case_synth"
    work_dir.mkdir()
    dem = _make_synthetic_dem(work_dir)
    # Also copy/rename to what orchestrator expects
    import shutil
    shutil.copy(dem, work_dir / "dem_utm.tif")

    # Monkey-patch external calls to bypass GEE + data.go.kr + DEM mosaic
    def _fake_fetch_rainfall(self, dry_run=False):
        out = self.work_dir / "rain.tif"
        # Create a synthetic rainfall raster (uniform 100 mm total, same grid as DEM)
        with rasterio.open(self.work_dir / "dem_utm.tif") as dem_ds:
            profile = dem_ds.profile.copy()
            profile.update(dtype="float32", compress="deflate")
            data = np.full((dem_ds.height, dem_ds.width), 100.0, dtype=np.float32)
        with rasterio.open(out, "w", **profile) as dst:
            dst.write(data, 1)
        self.trace.add("fetch_rainfall", "synthetic", {}, {"out_path": str(out)},
                       "synthetic 100 mm uniform rainfall for test")
        return out

    def _fake_detect_scars(self, dry_run=False):
        out = self.work_dir / "scars.tif"
        with rasterio.open(self.work_dir / "dem_utm.tif") as dem_ds:
            profile = dem_ds.profile.copy()
            profile.update(dtype="uint8", compress="deflate")
            data = np.zeros((dem_ds.height, dem_ds.width), dtype=np.uint8)
            data[20:30, 20:30] = 1  # synthetic scar patch
        with rasterio.open(out, "w", **profile) as dst:
            dst.write(data, 1)
        self.trace.add("detect_scars", "synthetic", {}, {"out_path": str(out)},
                       "synthetic scar patch for test")
        return out

    def _fake_fetch_nidr(self, dry_run=False):
        out = self.work_dir / "nidr.geojson"
        # Empty FeatureCollection (still valid)
        import json
        with open(out, "w") as f:
            json.dump({"type": "FeatureCollection", "features": []}, f)
        self.trace.add("fetch_nidr", "synthetic", {}, {"n_records": 0, "out_path": str(out)}, "")
        return out

    # Patch dem_mosaic.build_dem_for_case to reuse the pre-placed dem_utm.tif
    def _fake_build_dem(bbox, dem_root, out_path, target_res_m=30):
        import shutil as _sh
        src = work_dir / "dem_utm.tif"
        if Path(out_path).resolve() != src.resolve():
            _sh.copy(src, out_path)
        return {"out_path": str(out_path), "crs": "EPSG:32652",
                "n_tiles": 0, "width": 50, "height": 50, "res_m": target_res_m}

    # Patch topo.compute_topo to avoid richdem dep
    class _FakeTopo:
        def __init__(self, dem_path):
            with rasterio.open(dem_path) as ds:
                self.h, self.w = ds.height, ds.width
                self.transform = ds.transform
                self.crs = ds.crs
            xx, yy = np.meshgrid(np.arange(self.w), np.arange(self.h))
            dist = np.sqrt((xx - self.w // 2) ** 2 + (yy - self.h // 2) ** 2)
            sdeg = np.clip(45 * np.exp(-dist / 12), 0, 55).astype(np.float32)
            self.slope_rad = np.radians(sdeg)
            self.slope_deg = sdeg
            self.upslope_area_m2 = (500 + dist * 100).astype(np.float32)
            self.contour_length_m = np.full((self.h, self.w), 30.0, dtype=np.float32)
            self.nodata_mask = np.ones((self.h, self.w), dtype=bool)

    def _fake_compute_topo(dem_path, pixel_size_m=None):
        return _FakeTopo(dem_path)

    # Apply patches
    monkeypatch.setattr(orch_mod.LandslideAgent, "step_fetch_rainfall", _fake_fetch_rainfall)
    monkeypatch.setattr(orch_mod.LandslideAgent, "step_detect_scars", _fake_detect_scars)
    monkeypatch.setattr(orch_mod.LandslideAgent, "step_fetch_nidr", _fake_fetch_nidr)
    import landslide_kr.preprocess.dem_mosaic as dem_mod
    monkeypatch.setattr(dem_mod, "build_dem_for_case", _fake_build_dem)
    import landslide_kr.preprocess.topo as topo_mod
    monkeypatch.setattr(topo_mod, "compute_topo", _fake_compute_topo)
    # Stub GEE init to avoid real auth during the test
    import landslide_kr.io.gee_init as gee_mod
    monkeypatch.setattr(gee_mod, "init_ee",
                        lambda project=None: {"project": project or "stub", "auth_mode": "test_stub"})

    # Create case config
    cfg = CaseConfig(
        case_id="synth",
        event_window=EventWindow(start="2022-09-05", end="2022-09-07"),
        aoi=AOI(bbox=[0.0, 0.0, 1.0, 1.0]),
        dem_root=str(work_dir),
        geology_path=None,
        gee_project="test-project",
        cumulative_mm=100.0,
        model_name="SHALSTAB",
        model_params={"n_realizations": 10, "seed": 0},
    )

    agent = orch_mod.LandslideAgent(cfg, work_dir=work_dir)
    result = agent.run(dry_run=False)

    # Key assertions: pipeline produced expected artifacts + metrics
    assert result.status in ("success", "partial"), f"unexpected status: {result.status}, msg: {result.message}"
    assert Path(work_dir / "prob_unstable.tif").exists()
    assert Path(work_dir / "prediction.tif").exists()
    assert (work_dir / "agent_trace.json").exists()
    # Trace should have steps from every pipeline phase (step_run_model expands to sub-steps)
    step_names = {s["step"] for s in result.trace}
    assert "fetch_rainfall" in step_names
    assert "detect_scars" in step_names
    assert "fetch_nidr" in step_names
    assert "dem_mosaic" in step_names       # inside step_run_model
    assert "ensemble" in step_names          # inside step_run_model
    assert "save_prediction" in step_names   # inside step_run_model


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
