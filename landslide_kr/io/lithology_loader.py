"""
Lithology raster loader — rasterize Korean geology map to grid that matches DEM.

Primary source:
    Korean geology GPKG (KIGAM or similar), typically containing polygons
    with attribute 'lith_class' or '지질' indicating rock type.

Fallback:
    If GPKG not available, returns a "default" single-class raster of shape matching DEM.
    This ensures the pipeline still runs (using literature-wide default bounds).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


# Common field name candidates in Korean geology datasets
LITH_FIELD_CANDIDATES = [
    "lith_class", "lithology", "rock_type",
    "대표암상",  # KIGAM 1:50,000 표준 필드 (2026-04-14 확인)
    "지층",      # formation name (자주 stratigraphic unit)
    "지질", "암상", "암종", "기호", "symnum",
    "LITH_CD", "LITHOLOGY",
]

# Mapping from field values to our 5 canonical classes
# Order matters: earlier keywords checked first (more specific before general).
KEYWORD_MAP = {
    # Granite family (one of the most common Korean lithologies)
    "화강": "granite", "granite": "granite", "흑운모화강": "granite",
    "각섬석화강": "granite", "화강반암": "granite", "편상 화강": "granite",
    "화강섬록": "granite",
    # Volcanic
    "화산": "volcanic", "안산": "volcanic", "현무": "volcanic",
    "유문": "volcanic", "응회": "volcanic", "규장": "volcanic",
    "volcanic": "volcanic", "석영반암": "volcanic",
    "산성암": "volcanic", "산성암맥": "volcanic", "중성암맥": "volcanic",
    # Sedimentary
    "퇴적": "sedimentary", "사암": "sedimentary", "셰일": "sedimentary",
    "이암": "sedimentary", "역암": "sedimentary", "석회암": "sedimentary",
    "돌로마이트": "sedimentary", "실트": "sedimentary",
    "mudstone": "sedimentary", "shale": "sedimentary", "limestone": "sedimentary",
    # Metamorphic
    "변성": "metamorphic", "편마": "metamorphic", "편암": "metamorphic",
    "각섬암": "metamorphic", "규암": "metamorphic", "gneiss": "metamorphic",
    "schist": "metamorphic",
    # Alluvium / unconsolidated
    "충적": "alluvium", "미고결": "alluvium",
    "alluvium": "alluvium", "colluvium": "alluvium",
}


def _classify_text(text: str) -> str:
    """Map Korean/English geology description to one of 5 canonical classes."""
    if not text:
        return "default"
    s = str(text).lower().strip()
    for kw, cls in KEYWORD_MAP.items():
        if kw.lower() in s:
            return cls
    return "default"


def rasterize_lithology(
    geology_path: Path,
    ref_dem_path: Path,
    out_path: Optional[Path] = None,
    field: Optional[str] = None,
) -> "np.ndarray":
    """
    Rasterize geology polygons to a lithology-class array matching ref_dem grid.

    Args:
        geology_path: path to GPKG / Shapefile with geology polygons
        ref_dem_path: reference DEM GeoTIFF (output grid matches this)
        out_path: optional output GeoTIFF for class indices (0=default, 1=granite, ...)
        field: attribute field name; if None, tries candidates

    Returns:
        2D numpy array of lithology class strings (dtype=object), shape = ref DEM shape
    """
    import numpy as np
    import rasterio
    from rasterio.features import rasterize
    try:
        import geopandas as gpd
    except ImportError as e:
        raise ImportError(
            f"geopandas required to rasterize geology: {e}. pip install geopandas"
        )

    with rasterio.open(ref_dem_path) as ds:
        ref_shape = (ds.height, ds.width)
        ref_transform = ds.transform
        ref_crs = ds.crs

    gdf = gpd.read_file(geology_path)
    if gdf.crs is not None and ref_crs is not None and gdf.crs != ref_crs:
        gdf = gdf.to_crs(ref_crs)

    # Pick field
    if field is None:
        for cand in LITH_FIELD_CANDIDATES:
            if cand in gdf.columns:
                field = cand
                break
    if field is None or field not in gdf.columns:
        # Fallback: default everywhere
        arr = np.full(ref_shape, "default", dtype=object)
        return arr

    # Map values to classes
    gdf["_lith_class"] = gdf[field].astype(str).apply(_classify_text)

    # 5 classes + default → integer codes for rasterize
    class_codes = {"default": 0, "granite": 1, "volcanic": 2,
                   "sedimentary": 3, "metamorphic": 4, "alluvium": 5}
    code_to_class = {v: k for k, v in class_codes.items()}

    shapes = [(geom, class_codes[lc]) for geom, lc in zip(gdf.geometry, gdf["_lith_class"])]
    code_raster = rasterize(shapes, out_shape=ref_shape, transform=ref_transform, fill=0, dtype="uint8")

    # Convert int code → class name string
    arr = np.empty(ref_shape, dtype=object)
    for code, cls in code_to_class.items():
        arr[code_raster == code] = cls

    if out_path is not None:
        profile = {
            "driver": "GTiff", "count": 1, "dtype": "uint8",
            "height": ref_shape[0], "width": ref_shape[1],
            "crs": ref_crs, "transform": ref_transform, "compress": "deflate",
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(code_raster, 1)

    return arr


def load_or_default(
    geology_path: Optional[Path],
    ref_dem_path: Path,
    out_path: Optional[Path] = None,
) -> "np.ndarray":
    """
    Convenience: load lithology if path provided and exists; else return default array.

    Returns a string array (dtype=object) with shape matching ref DEM.
    """
    import numpy as np
    import rasterio

    if geology_path and Path(geology_path).exists():
        try:
            return rasterize_lithology(Path(geology_path), ref_dem_path, out_path)
        except Exception as e:
            import logging
            logging.warning(f"Failed to rasterize geology ({e}); falling back to default")

    # Default: single-class array
    with rasterio.open(ref_dem_path) as ds:
        shape = (ds.height, ds.width)
    return np.full(shape, "default", dtype=object)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 3:
        print("Usage: python -m landslide_kr.io.lithology_loader <dem.tif> <geology.gpkg?> [out.tif]")
        sys.exit(1)
    dem = Path(sys.argv[1])
    geology = Path(sys.argv[2]) if sys.argv[2] != "-" else None
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    arr = load_or_default(geology, dem, out)
    # Report class distribution
    import numpy as np
    unique, counts = np.unique(arr, return_counts=True)
    report = {str(k): int(v) for k, v in zip(unique, counts)}
    print(json.dumps(report, indent=2))
