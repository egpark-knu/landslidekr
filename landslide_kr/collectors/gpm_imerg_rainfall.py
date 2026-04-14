"""
GPM IMERG V07 rainfall collector via Google Earth Engine.

Provides:
    - cumulative_rainfall_mm(bbox, start, end) → GeoTIFF (total mm over window)
    - hourly_rainfall_timeseries(bbox, start, end) → list of (timestamp, mean_mm) for transient models
    - max_6h_intensity(bbox, start, end) → rolling 6h max intensity raster (for SHALSTAB critical rainfall)

Data: NASA/GPM_L3/IMERG_V07 (half-hourly, 0.1°, global)
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


def cumulative_rainfall_mm(
    bbox: list[float],
    start: str,
    end: str,
    out_path: Path,
    export_mode: str = "drive",
) -> dict:
    """
    Compute cumulative rainfall (mm) over [start, end] for bbox using GPM IMERG V07.

    Args:
        bbox: [min_lon, min_lat, max_lon, max_lat]
        start, end: YYYY-MM-DD
        out_path: output GeoTIFF
        export_mode: 'drive' | 'local' (getDownloadURL streaming)

    Returns:
        metadata dict
    """
    import ee

    try:
        ee.Number(1).getInfo()
    except Exception as e:
        raise RuntimeError(
            f"Earth Engine not initialized: {e}. "
            "Run: ee.Authenticate(); ee.Initialize(project='<your-gee-project>')."
        )

    aoi = ee.Geometry.Rectangle(bbox)
    coll = (
        ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
        .filterBounds(aoi)
        .filterDate(start, end)
        .select("precipitation")  # mm/hr (half-hourly × 0.5 to mm per 30-min)
    )

    # IMERG gives mm/hr; to get mm over window, sum × 0.5 h per 30-min image
    total_mm = coll.sum().multiply(0.5).rename("rain_mm")

    n_images = coll.size().getInfo()
    mean_total = (
        total_mm.reduceRegion(ee.Reducer.mean(), aoi, 11132, maxPixels=1e10)
        .get("rain_mm")
        .getInfo()
    )

    meta = {
        "n_images": n_images,
        "window": [start, end],
        "mean_total_mm": round(float(mean_total), 2) if mean_total else None,
        "bbox": bbox,
        "scale_m": 11132,  # IMERG native ~0.1°
    }

    scale_m = 11132
    if export_mode == "drive":
        fn = Path(out_path).stem
        task = ee.batch.Export.image.toDrive(
            image=total_mm,
            description=fn,
            folder="landslide_kr_rainfall",
            fileNamePrefix=fn,
            region=aoi,
            scale=scale_m,
            maxPixels=1e10,
        )
        task.start()
        meta["export_task_id"] = task.id
        meta["out_path"] = f"drive:landslide_kr_rainfall/{fn}.tif"
    else:
        url = total_mm.getDownloadURL(
            {"region": aoi, "scale": scale_m, "format": "GeoTIFF"}
        )
        import urllib.request
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as resp, open(out_path, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
        meta["out_path"] = str(out_path)

    return meta


def max_rolling_intensity(
    bbox: list[float],
    start: str,
    end: str,
    window_hours: int = 6,
    out_path: Optional[Path] = None,
    export_mode: str = "drive",
) -> dict:
    """
    Compute maximum rolling N-hour rainfall intensity (mm/hr) over event window.

    This is the key driver for SHALSTAB nowcasting: compare max intensity to q_cr.
    """
    import ee

    aoi = ee.Geometry.Rectangle(bbox)
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    # Build a list of rolling-window sum images
    windows = []
    t = start_dt
    step = timedelta(hours=1)
    while t + timedelta(hours=window_hours) <= end_dt + timedelta(days=1):
        w_start = t.strftime("%Y-%m-%dT%H:%M:%S")
        w_end = (t + timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%S")
        window = (
            ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
            .filterBounds(aoi)
            .filterDate(w_start, w_end)
            .select("precipitation")
            .sum()
            .multiply(0.5)  # mm
            .divide(window_hours)  # → mm/hr average over window
            .rename("intensity")
        )
        windows.append(window)
        t += step

    if not windows:
        return {"error": "empty window list"}

    max_int = ee.ImageCollection(windows).max().rename("max_intensity")

    meta = {
        "window_hours": window_hours,
        "n_windows": len(windows),
        "period": [start, end],
        "bbox": bbox,
    }

    if out_path is None:
        return meta

    scale_m = 11132
    if export_mode == "drive":
        fn = Path(out_path).stem
        task = ee.batch.Export.image.toDrive(
            image=max_int,
            description=fn,
            folder="landslide_kr_rainfall",
            fileNamePrefix=fn,
            region=aoi,
            scale=scale_m,
            maxPixels=1e10,
        )
        task.start()
        meta["export_task_id"] = task.id
        meta["out_path"] = f"drive:landslide_kr_rainfall/{fn}.tif"
    else:
        url = max_int.getDownloadURL(
            {"region": aoi, "scale": scale_m, "format": "GeoTIFF"}
        )
        import urllib.request
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as resp, open(out_path, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
        meta["out_path"] = str(out_path)

    return meta


def hourly_timeseries(bbox: list[float], start: str, end: str) -> list[tuple[str, float]]:
    """
    Return list of (timestamp_iso, mean_mm_per_hr) for each IMERG half-hourly image.

    For TRIGRS transient forcing.
    """
    import ee

    aoi = ee.Geometry.Rectangle(bbox)
    coll = (
        ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
        .filterBounds(aoi)
        .filterDate(start, end)
        .select("precipitation")
    )

    def feature_row(img):
        mean = img.reduceRegion(ee.Reducer.mean(), aoi, 11132, maxPixels=1e10).get("precipitation")
        return ee.Feature(None, {"t": img.date().format(), "rate": mean})

    fc = coll.map(feature_row)
    rows = fc.getInfo()["features"]
    return [(r["properties"]["t"], r["properties"]["rate"]) for r in rows]


if __name__ == "__main__":
    import json, sys
    try:
        m = cumulative_rainfall_mm(
            bbox=[129.20, 36.00, 129.50, 36.20],
            start="2022-09-05",
            end="2022-09-08",
            out_path=Path("out/pohang_2022_rain.tif"),
            export_mode="drive",
        )
        print(json.dumps(m, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
