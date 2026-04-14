"""
GEE rainfall collector — GPM IMERG Final Precipitation L3.

Uses memory-safe streaming download (inherited from wildfire_kr pattern).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def collect_cumulative_rainfall(
    bbox: list[float],  # [min_lon, min_lat, max_lon, max_lat]
    start_date: str,    # YYYY-MM-DD
    end_date: str,
    out_path: Path,
    scale_m: int = 1000,
) -> dict:
    """
    Collect cumulative rainfall from GPM IMERG over the event period.

    Uses:
      - NASA/GPM_L3/IMERG_V07 (30-min, 0.1° resolution)
      - ee.Image.getDownloadURL with streaming

    Returns:
        metadata dict with filepath, stats
    """
    import ee
    ee.Initialize()

    aoi = ee.Geometry.Rectangle(bbox)
    col = (
        ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
        .filterDate(start_date, end_date)
        .filterBounds(aoi)
        .select("precipitation")
    )

    # Sum (mm) — precipitation is mm/hr, each frame 30-min
    total = col.sum().multiply(0.5).clip(aoi).rename("total_rainfall_mm")

    # TODO: streaming download using pattern from generate_fig5_safe.py
    raise NotImplementedError("Use safe_download_geotiff pattern from WildfireKR")
