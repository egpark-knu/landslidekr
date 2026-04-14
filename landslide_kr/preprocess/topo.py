"""
Topographic preprocessing — slope, upslope area (specific contributing area),
flow direction — from DEM.

Runtime fallback chain: richdem Dinf (preferred when available) → pysheds
D8 + Horn slope (second choice; Cython-backed) → pure-numpy D8 + finite-
difference slope (last resort). The three Korean benchmark runs released
with this paper used the pysheds D8 + Horn path because the richdem wheel
is not available on Mac ARM64; the executed backend is recorded per event
in the `topo.backend` field of each agent_trace.json.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class TopoArrays:
    slope_rad: "np.ndarray"          # radians
    slope_deg: "np.ndarray"          # degrees
    upslope_area_m2: "np.ndarray"    # m² (cell count × pixel area)
    contour_length_m: "np.ndarray"   # m (approx cell width; unit contour = 1 pixel)
    transform: object                 # rasterio Affine
    crs: object
    nodata_mask: "np.ndarray"


def compute_topo(dem_path: Path, pixel_size_m: Optional[float] = None) -> TopoArrays:
    """
    Compute slope + upslope area from DEM GeoTIFF.

    Runtime fallback chain:
      1. richdem Dinf (preferred when importable) — `_richdem_topo`.
      2. pysheds D8 + Horn slope (second choice) — `_pysheds_topo`.
      3. pure-numpy D8 + finite-difference slope (last resort) — `_numpy_topo`.

    The released Korean benchmark runs used the pysheds D8 + Horn path because
    the richdem wheel is not available on Mac ARM64. The per-event backend is
    logged to the `topo.backend` field in agent_trace.json.
    """
    import numpy as np
    import rasterio

    with rasterio.open(dem_path) as ds:
        dem = ds.read(1).astype(np.float32)
        transform = ds.transform
        crs = ds.crs
        nodata = ds.nodata
        px_w = abs(transform.a)
        px_h = abs(transform.e)

    # Heuristic pixel size in meters
    if pixel_size_m is None:
        if crs and crs.is_projected:
            pixel_size_m = (px_w + px_h) / 2.0
        else:
            center_lat = (transform.f + transform.e * dem.shape[0] / 2)
            pixel_size_m = ((px_w + px_h) / 2.0) * 111_000.0 * max(
                0.1, abs(np.cos(np.radians(center_lat)))
            )

    nodata_mask = np.isfinite(dem) if nodata is None else (dem != nodata)
    dem_filled = np.where(nodata_mask, dem, np.nanmin(dem[nodata_mask]))

    try:
        import richdem as rd  # preferred: Dinf flow
        rd_dem = rd.rdarray(dem_filled, no_data=-9999)
        rd_dem.geotransform = [transform.c, transform.a, transform.b,
                                transform.f, transform.d, transform.e]
        rd_filled = rd.FillDepressions(rd_dem, in_place=False)
        slope_deg = np.array(
            rd.TerrainAttribute(rd_filled, attrib="slope_degrees"), dtype=np.float32
        )
        slope_rad = np.radians(slope_deg)
        accum = np.array(
            rd.FlowAccumulation(rd_filled, method="Dinf"), dtype=np.float32
        )
        upslope_area_m2 = accum * (pixel_size_m ** 2)
    except ImportError:
        # pysheds (Cython-backed) second choice
        try:
            slope_deg, upslope_area_m2 = _pysheds_topo(dem_path, pixel_size_m)
            slope_rad = np.radians(slope_deg).astype(np.float32)
        except ImportError:
            # Pure numpy fallback — slow, only for tiny DEMs
            slope_deg, upslope_area_m2 = _numpy_topo(dem_filled, pixel_size_m)
            slope_rad = np.radians(slope_deg).astype(np.float32)

    contour_length_m = np.full(dem.shape, pixel_size_m, dtype=np.float32)

    return TopoArrays(
        slope_rad=slope_rad.astype(np.float32),
        slope_deg=slope_deg.astype(np.float32),
        upslope_area_m2=upslope_area_m2.astype(np.float32),
        contour_length_m=contour_length_m,
        transform=transform,
        crs=crs,
        nodata_mask=nodata_mask,
    )


def _pysheds_topo(dem_path: Path, pixel_size_m: float):
    """
    pysheds-based slope (Horn) + D8 flow accumulation. Much faster than pure numpy.
    """
    import numpy as np
    from pysheds.grid import Grid

    grid = Grid.from_raster(str(dem_path))
    dem = grid.read_raster(str(dem_path))
    # Fill depressions + resolve flats so flow accumulation is well-defined
    filled = grid.fill_depressions(dem)
    inflated = grid.resolve_flats(filled)
    fdir = grid.flowdir(inflated, routing="d8")
    accum = grid.accumulation(fdir, routing="d8")

    # Horn slope
    z = np.asarray(inflated, dtype=np.float32)
    padded = np.pad(z, 1, mode="edge")
    dzdx = ((padded[:-2, 2:] + 2 * padded[1:-1, 2:] + padded[2:, 2:]) -
            (padded[:-2, :-2] + 2 * padded[1:-1, :-2] + padded[2:, :-2])) / (8 * pixel_size_m)
    dzdy = ((padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:]) -
            (padded[:-2, :-2] + 2 * padded[:-2, 1:-1] + padded[:-2, 2:])) / (8 * pixel_size_m)
    slope_deg = np.degrees(np.arctan(np.sqrt(dzdx ** 2 + dzdy ** 2))).astype(np.float32)

    upslope_area_m2 = (np.asarray(accum, dtype=np.float32) + 1.0) * (pixel_size_m ** 2)
    return slope_deg, upslope_area_m2


def _numpy_topo(dem: "np.ndarray", pixel_size_m: float):
    """
    Pure-numpy fallback: finite-difference slope (degrees) + D8 flow accumulation.

    Notes:
    - Slope: Horn (1981) 3x3 kernel (matches GDAL DEMProcessing slope).
    - Flow: simple D8 topological iteration (Jenson & Domingue 1988), no pit filling.
      This is less accurate than richdem Dinf but sufficient for event-scale SHALSTAB
      (which cares about relative magnitudes of upslope contributing area).
    """
    import numpy as np

    h, w = dem.shape
    # --- Horn slope ---
    # Pad for kernel
    padded = np.pad(dem, 1, mode="edge")
    z = {
        "a": padded[:-2, :-2], "b": padded[:-2, 1:-1], "c": padded[:-2, 2:],
        "d": padded[1:-1, :-2],                        "f": padded[1:-1, 2:],
        "g": padded[2:,   :-2], "h": padded[2:,   1:-1], "i": padded[2:,   2:],
    }
    dzdx = ((z["c"] + 2 * z["f"] + z["i"]) - (z["a"] + 2 * z["d"] + z["g"])) / (8 * pixel_size_m)
    dzdy = ((z["g"] + 2 * z["h"] + z["i"]) - (z["a"] + 2 * z["b"] + z["c"])) / (8 * pixel_size_m)
    rise_run = np.sqrt(dzdx ** 2 + dzdy ** 2)
    slope_deg = np.degrees(np.arctan(rise_run)).astype(np.float32)

    # --- D8 flow accumulation ---
    # Offsets for the 8 neighbors (row_off, col_off, distance-weight)
    dirs = [(-1, -1, np.sqrt(2)), (-1, 0, 1), (-1, 1, np.sqrt(2)),
            (0, -1, 1),                       (0, 1, 1),
            (1, -1, np.sqrt(2)), (1, 0, 1), (1, 1, np.sqrt(2))]

    # For each cell, compute the index of steepest descent neighbor
    flow_dir = np.full((h, w), -1, dtype=np.int8)  # -1 means sink/no flow
    best_drop = np.zeros((h, w), dtype=np.float32)
    for idx, (dr, dc, dist) in enumerate(dirs):
        # Neighbor elevation
        r_src_slice = slice(max(0, -dr), h - max(0, dr))
        r_dst_slice = slice(max(0, dr), h - max(0, -dr))
        c_src_slice = slice(max(0, -dc), w - max(0, dc))
        c_dst_slice = slice(max(0, dc), w - max(0, -dc))
        neigh = np.full((h, w), np.inf, dtype=np.float32)
        neigh[r_src_slice, c_src_slice] = dem[r_dst_slice, c_dst_slice]
        drop = (dem - neigh) / (pixel_size_m * dist)
        better = (drop > best_drop) & np.isfinite(neigh)
        best_drop = np.where(better, drop, best_drop)
        flow_dir = np.where(better, idx, flow_dir)

    # Topological sort by elevation descending, accumulate
    order = np.argsort(-dem.ravel(), kind="stable")
    accum = np.ones((h, w), dtype=np.float32)
    rows_flat = order // w
    cols_flat = order % w
    for i in range(order.size):
        r = int(rows_flat[i])
        c = int(cols_flat[i])
        d = int(flow_dir[r, c])
        if d < 0:
            continue
        dr, dc, _ = dirs[d]
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            accum[nr, nc] += accum[r, c]

    upslope_area_m2 = accum * (pixel_size_m ** 2)
    return slope_deg, upslope_area_m2


def save_topo_layers(topo: TopoArrays, out_dir: Path) -> dict:
    """Save slope/area/contour as separate GeoTIFFs."""
    import rasterio
    import numpy as np

    out_dir.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": topo.slope_rad.shape[0],
        "width": topo.slope_rad.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": topo.crs,
        "transform": topo.transform,
        "compress": "deflate",
    }
    paths = {}
    for name, arr in [
        ("slope_deg", topo.slope_deg),
        ("slope_rad", topo.slope_rad),
        ("upslope_area_m2", topo.upslope_area_m2),
        ("contour_length_m", topo.contour_length_m),
    ]:
        p = out_dir / f"{name}.tif"
        with rasterio.open(p, "w", **profile) as ds:
            ds.write(arr, 1)
        paths[name] = str(p)
    return paths


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m landslide_kr.preprocess.topo <dem.tif> [out_dir]")
        sys.exit(1)
    dem_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else dem_path.parent / "topo"
    topo = compute_topo(dem_path)
    paths = save_topo_layers(topo, out_dir)
    import json
    print(json.dumps(paths, indent=2))
