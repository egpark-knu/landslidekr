"""
DEM mosaic + reproject for case AOI.

Workflow:
    1. Discover Copernicus DEM tiles intersecting the AOI bbox
    2. Merge into a single mosaic
    3. Reproject to local UTM (so topo.py receives m-based grid)
    4. Clip to AOI bbox (with small buffer)

Copernicus DEM 30m tiles are named like:
    Copernicus_DSM_COG_10_N36_00_E129_00_DEM.tif  (1° × 1° tile, 10m posting)
Directory: geodata/dem_30m_copernicus/
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def _bbox_tiles(bbox: list[float]) -> list[tuple[int, int]]:
    """Return list of (lat_int, lon_int) tiles that intersect the bbox."""
    import math
    min_lon, min_lat, max_lon, max_lat = bbox
    lat_start = math.floor(min_lat)
    lat_end = math.floor(max_lat) + 1
    lon_start = math.floor(min_lon)
    lon_end = math.floor(max_lon) + 1
    return [(lat, lon) for lat in range(lat_start, lat_end) for lon in range(lon_start, lon_end)]


def find_copernicus_tiles(
    bbox: list[float],
    dem_root: Path,
    pattern: str = "Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM.tif",
) -> list[Path]:
    """
    Find Copernicus DEM tiles covering bbox inside dem_root.

    Args:
        bbox: [min_lon, min_lat, max_lon, max_lat]
        dem_root: directory containing DEM tiles (or symlink)
        pattern: tile filename pattern with {lat} and {lon} placeholders

    Returns:
        list of tile paths (existing files only)
    """
    tiles = _bbox_tiles(bbox)
    found = []
    for lat, lon in tiles:
        fn = pattern.format(lat=lat, lon=lon)
        p = dem_root / fn
        if p.exists():
            found.append(p)
            continue
        # Also try recursive search (flatter patterns)
        for alt in dem_root.rglob(f"*N{lat:02d}*E{lon:03d}*DEM.tif"):
            found.append(alt)
            break
    return found


def mosaic_and_reproject(
    tile_paths: list[Path],
    bbox: list[float],
    out_path: Path,
    buffer_deg: float = 0.02,
    target_res_m: int = 30,
) -> dict:
    """
    Mosaic tiles, reproject to local UTM, clip to bbox+buffer.

    Args:
        tile_paths: DEM tiles to mosaic
        bbox: [min_lon, min_lat, max_lon, max_lat]
        out_path: output GeoTIFF (UTM CRS)
        buffer_deg: buffer (degrees) around bbox before clipping
        target_res_m: target resolution in meters

    Returns:
        dict: {out_path, crs, n_tiles, width, height, res_m}
    """
    import rasterio
    from rasterio.merge import merge
    from rasterio.warp import calculate_default_transform, reproject, Resampling

    if not tile_paths:
        raise FileNotFoundError("no DEM tiles found for bbox")

    min_lon, min_lat, max_lon, max_lat = bbox
    buf_bounds = (
        min_lon - buffer_deg,
        min_lat - buffer_deg,
        max_lon + buffer_deg,
        max_lat + buffer_deg,
    )

    # Pick UTM zone for center longitude
    cent_lon = (min_lon + max_lon) / 2.0
    utm_zone = int((cent_lon + 180) / 6) + 1
    # Assume Northern hemisphere (Korea always is)
    utm_crs = f"EPSG:{32600 + utm_zone}"

    # Open & merge
    srcs = [rasterio.open(p) for p in tile_paths]
    try:
        mosaic, mosaic_transform = merge(srcs, bounds=buf_bounds)
        profile = srcs[0].profile.copy()
        src_crs = srcs[0].crs
    finally:
        for s in srcs:
            s.close()

    profile.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        transform=mosaic_transform,
        compress="deflate",
    )

    # Write merged (in source CRS) to a temp step, then reproject
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp_path = tmp.name
    with rasterio.open(tmp_path, "w", **profile) as dst:
        dst.write(mosaic)

    # Reproject to UTM at target_res_m
    with rasterio.open(tmp_path) as src:
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src.crs, utm_crs, src.width, src.height, *src.bounds,
            resolution=target_res_m,
        )
        dst_profile = src.profile.copy()
        dst_profile.update(
            crs=utm_crs,
            transform=dst_transform,
            width=dst_width,
            height=dst_height,
            compress="deflate",
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out_path, "w", **dst_profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=utm_crs,
                    resampling=Resampling.bilinear,
                )

    Path(tmp_path).unlink(missing_ok=True)

    return {
        "out_path": str(out_path),
        "crs": utm_crs,
        "n_tiles": len(tile_paths),
        "width": dst_width,
        "height": dst_height,
        "res_m": target_res_m,
    }


def build_dem_for_case(
    bbox: list[float],
    dem_root: Path,
    out_path: Path,
    target_res_m: int = 30,
) -> dict:
    """One-call: find tiles + mosaic + reproject."""
    tiles = find_copernicus_tiles(bbox, dem_root)
    if not tiles:
        raise FileNotFoundError(
            f"No Copernicus DEM tiles found in {dem_root} for bbox {bbox}"
        )
    return mosaic_and_reproject(tiles, bbox, out_path, target_res_m=target_res_m)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 4:
        print("Usage: python -m landslide_kr.preprocess.dem_mosaic <dem_root> <bbox_csv> <out.tif>")
        print("  bbox_csv: 'min_lon,min_lat,max_lon,max_lat'")
        sys.exit(1)
    dem_root = Path(sys.argv[1])
    bbox = [float(x) for x in sys.argv[2].split(",")]
    out = Path(sys.argv[3])
    try:
        result = build_dem_for_case(bbox, dem_root, out)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
