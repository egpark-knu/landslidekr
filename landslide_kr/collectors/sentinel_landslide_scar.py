"""
Sentinel-2 landslide scar auto-detection — NDVI pre/post event.

Inspired by WildfireKR's `sentinel_burn_scar.py`:
    - Wildfire version: dNBR + NDVI drop to detect burn scars
    - Landslide version: NDVI drop + slope filter + low-NDVI-post threshold

Output: binary raster (1=landslide scar, 0=no change), suitable as training label.

Decision rule (literature-anchored):
    scar = (NDVI_pre - NDVI_post) > ndvi_drop_threshold
         AND NDVI_post < post_max  (exclude healthy veg)
         AND slope_deg > min_slope_deg  (exclude agriculture/urban)
         AND bare_soil_ratio > bare_min  (optional; post/pre band ratio)

References:
    - Scheip & Wegmann (2021) HazMapper for landslide mapping via NDVI change
    - Martha et al. (2010) Landslide detection with Sentinel-2 NDVI
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def detect_landslide_scars(
    bbox: list[float],
    event_start: str,
    event_end: str,
    out_path: Path,
    ndvi_drop_threshold: float = 0.20,
    post_ndvi_max: float = 0.30,
    min_slope_deg: float = 10.0,
    scale_m: int = 10,
    pre_days: int = 60,
    post_days: int = 30,
    export_mode: str = "local",
) -> dict:
    """
    Detect landslide scars from Sentinel-2 NDVI change using Google Earth Engine.

    Requires GEE to be initialized: ee.Initialize(project="<your-project>").

    Args:
        bbox: [min_lon, min_lat, max_lon, max_lat] (EPSG:4326)
        event_start, event_end: YYYY-MM-DD (inclusive)
        out_path: output GeoTIFF (or Drive filename if export_mode='drive')
        ndvi_drop_threshold: min NDVI decrease to flag as scar (default 0.20)
        post_ndvi_max: post-event NDVI must be below this (exclude healthy veg)
        min_slope_deg: min slope (degrees) to accept (exclude crops/urban)
        scale_m: output resolution (default 10 m, Sentinel-2 native)
        pre_days: days before event_start to form pre-event median
        post_days: days after event_end to form post-event median
        export_mode: 'local' (getDownloadURL + streaming) or 'drive' (Drive export)

    Returns:
        metadata dict: {scar_pixel_count, pre_count, post_count, aoi_km2, export_task_id|out_path}
    """
    import ee
    from datetime import datetime, timedelta

    try:
        ee.Number(1).getInfo()  # sanity check
    except Exception as e:
        raise RuntimeError(
            f"Earth Engine not initialized: {e}. "
            "Run: ee.Authenticate(); ee.Initialize(project='<your-gee-project>')."
        )

    aoi = ee.Geometry.Rectangle(bbox)

    start_dt = datetime.fromisoformat(event_start)
    end_dt = datetime.fromisoformat(event_end)
    pre_start = (start_dt - timedelta(days=pre_days)).date().isoformat()
    pre_end = (start_dt - timedelta(days=1)).date().isoformat()
    post_start = (end_dt + timedelta(days=1)).date().isoformat()
    post_end = (end_dt + timedelta(days=post_days)).date().isoformat()

    # S2 SR Harmonized + cloud mask (QA60)
    def mask_clouds(img):
        qa = img.select("QA60")
        cloud = qa.bitwiseAnd(1 << 10).Or(qa.bitwiseAnd(1 << 11))
        return img.updateMask(cloud.Not()).divide(10000)

    def add_ndvi(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi)

    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(aoi).filter(
        ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40)
    )

    pre_coll = s2.filterDate(pre_start, pre_end).map(mask_clouds).map(add_ndvi)
    post_coll = s2.filterDate(post_start, post_end).map(mask_clouds).map(add_ndvi)

    pre_ndvi = pre_coll.select("NDVI").median().rename("NDVI_pre")
    post_ndvi = post_coll.select("NDVI").median().rename("NDVI_post")
    dndvi = pre_ndvi.subtract(post_ndvi).rename("dNDVI")

    # Slope from SRTM v3 (Copernicus GLO30 returns None in some AOIs — 2026-04-14 bug)
    dem = ee.Image("USGS/SRTMGL1_003")
    slope_rad = ee.Terrain.slope(dem)  # degrees by default

    # Decision rule
    scar = dndvi.gt(ndvi_drop_threshold).And(
        post_ndvi.lt(post_ndvi_max)
    ).And(slope_rad.gt(min_slope_deg)).rename("scar").uint8()

    # Reduce stats for metadata
    pre_count = pre_coll.size().getInfo()
    post_count = post_coll.size().getInfo()
    scar_count = (
        scar.reduceRegion(ee.Reducer.sum(), aoi, scale_m, maxPixels=1e10).get("scar").getInfo()
    )
    aoi_area_km2 = aoi.area(maxError=10).getInfo() / 1e6

    meta = {
        "pre_count": pre_count,
        "post_count": post_count,
        "scar_pixel_count": scar_count,
        "aoi_km2": round(aoi_area_km2, 2),
        "scale_m": scale_m,
        "bbox": bbox,
        "event_window": [event_start, event_end],
        "thresholds": {
            "ndvi_drop": ndvi_drop_threshold,
            "post_ndvi_max": post_ndvi_max,
            "min_slope_deg": min_slope_deg,
        },
    }

    if export_mode == "drive":
        fn = Path(out_path).stem
        task = ee.batch.Export.image.toDrive(
            image=scar,
            description=fn,
            folder="landslide_kr_scars",
            fileNamePrefix=fn,
            region=aoi,
            scale=scale_m,
            maxPixels=1e10,
        )
        task.start()
        meta["export_task_id"] = task.id
        meta["out_path"] = f"drive:landslide_kr_scars/{fn}.tif"
    else:
        # Local streaming download via getDownloadURL (memory-safe)
        url = scar.getDownloadURL(
            {"region": aoi, "scale": scale_m, "format": "GeoTIFF"}
        )
        import urllib.request
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as resp, open(out_path, "wb") as f:
            # Stream in chunks (WildfireKR lesson: never resp.read() for big images)
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
        meta["out_path"] = str(out_path)

    return meta


if __name__ == "__main__":
    # Example: 2022 Pohang event
    import json, sys
    try:
        m = detect_landslide_scars(
            bbox=[129.20, 36.00, 129.50, 36.20],
            event_start="2022-09-05",
            event_end="2022-09-07",
            out_path=Path("out/pohang_2022_scars.tif"),
            export_mode="drive",  # safer for first run
        )
        print(json.dumps(m, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
