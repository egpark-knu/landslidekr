"""
NIDR (National Institute for Disaster Reduction) landslide event loader.

Primary source: 산림청 공공데이터 API (data.go.kr ID 15074816)
    — 과거산사태 정보 (년도/지역별 산사태 발생 기록)

Backup source: 산사태정보시스템 (sansatai.forest.go.kr) Excel downloads

Use cases:
    - Label collection for 2022 Pohang, 2023 Yecheon events
    - Coordinate + date + damage area per record
    - Converted to (lon, lat, date, damage_m2) table → rasterized to binary label
"""
from __future__ import annotations

import os
import time
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import urllib.parse
import urllib.request

DATA_GO_KR_BASE = "http://apis.data.go.kr/1400000/pastLndslInfoService/pastLndslInfoList"
# Service Key must be stored in env var or ~/.mas/data_go_kr.json
ENV_KEY = "DATA_GO_KR_SERVICE_KEY"


@dataclass
class LandslideRecord:
    """Single landslide occurrence record."""

    occurrence_date: str  # YYYY-MM-DD (or YYYYMMDD in raw API)
    sido: str             # 시도 (e.g., "경상북도")
    sigungu: str          # 시군구 (e.g., "포항시 남구")
    address: str          # 상세주소
    lon: Optional[float]  # 경도 (EPSG:4326) — raw API may omit; backfill via geocoder
    lat: Optional[float]
    damage_m2: Optional[float]
    raw: dict             # raw API response dict (for debugging)


def _load_service_key() -> str:
    """Load data.go.kr service key from env or ~/.mas/data_go_kr.json."""
    key = os.environ.get(ENV_KEY)
    if key:
        return key
    cfg_path = Path.home() / ".mas" / "data_go_kr.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            cfg = json.load(f)
        return cfg.get("service_key", "")
    raise RuntimeError(
        f"data.go.kr service key not found. Set env {ENV_KEY} or create {cfg_path}."
    )


def fetch_records(
    year: int,
    sido: Optional[str] = None,
    sigungu: Optional[str] = None,
    page_size: int = 1000,
    max_pages: int = 20,
    service_key: Optional[str] = None,
    sleep_sec: float = 0.5,
) -> list[LandslideRecord]:
    """
    Fetch historical landslide records from data.go.kr API (산림청_과거산사태 15074816).

    Args:
        year: 재해연도 (e.g., 2022) — client-side filter (API ignores server-side)
        sido: 시도명 (optional filter, applied client-side)
        sigungu: 시군구명 (optional filter, applied client-side)
        page_size: 페이지당 레코드 수 (max 1000)
        max_pages: 최대 페이지 수 (안전장치)
        service_key: API 키
        sleep_sec: 페이지 간 대기

    Returns:
        list of LandslideRecord

    Notes:
        - API returns XML only (JSON param ignored). We parse XML.
        - Actual field names: ctprvNm / sgngNm / epmnNm / lndslDmgArea / lndslDsstrNm / lndslDsstrYr
        - NO coordinates in response — address+sigungu+eupmyeondong only. Use `backfill_coords_by_geocoding`.
        - Year filter appears ignored server-side — we filter client-side using lndslDsstrYr.
    """
    import xml.etree.ElementTree as ET

    key = service_key or _load_service_key()
    results: list[LandslideRecord] = []

    for page in range(1, max_pages + 1):
        params = {
            "serviceKey": key,
            "pageNo": str(page),
            "numOfRows": str(page_size),
        }

        url = f"{DATA_GO_KR_BASE}?{urllib.parse.urlencode(params)}"

        with urllib.request.urlopen(url, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")

        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            break

        # Response structure: <response><header/><body><items><item>...</item></items></body></response>
        body = root.find("body")
        if body is None:
            break
        items_wrap = body.find("items")
        if items_wrap is None:
            break
        items = list(items_wrap.findall("item"))

        if not items:
            break

        def _text(it, tag):
            el = it.find(tag)
            return el.text if el is not None and el.text is not None else ""

        def _match_year(disaster_year_str: str) -> bool:
            try:
                return int(disaster_year_str) == int(year)
            except (ValueError, TypeError):
                return False

        for it in items:
            sido_val = _text(it, "ctprvNm")
            sigungu_val = _text(it, "sgngNm")
            eupmyeondong = _text(it, "epmnNm")
            disaster_name = _text(it, "lndslDsstrNm")
            disaster_year = _text(it, "lndslDsstrYr")
            damage_ha = _text(it, "lndslDmgArea")

            # Client-side year filter (server ignores dsrYear param)
            if not _match_year(disaster_year):
                continue
            if sido and sido not in sido_val:
                continue
            if sigungu and sigungu not in sigungu_val:
                continue

            # Compose full address for geocoding (hectares → m²)
            addr_parts = [p for p in [sido_val, sigungu_val, eupmyeondong] if p]
            full_address = " ".join(addr_parts)

            damage_m2 = None
            try:
                damage_m2 = float(damage_ha) * 10000.0  # ha → m²
            except (ValueError, TypeError):
                pass

            results.append(
                LandslideRecord(
                    occurrence_date=f"{disaster_year}-01-01",  # API only provides year; event name has date string
                    sido=sido_val,
                    sigungu=sigungu_val,
                    address=full_address,
                    lon=None,
                    lat=None,
                    damage_m2=damage_m2,
                    raw={
                        "ctprvNm": sido_val,
                        "sgngNm": sigungu_val,
                        "epmnNm": eupmyeondong,
                        "lndslDsstrNm": disaster_name,
                        "lndslDsstrYr": disaster_year,
                        "lndslDmgArea_ha": damage_ha,
                    },
                )
            )

        # totalCount check for early exit
        total_el = body.find("totalCount")
        total = int(total_el.text) if total_el is not None and total_el.text else 0
        if total and page * page_size >= total:
            break
        time.sleep(sleep_sec)

    return results


def _parse_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def backfill_coords_by_geocoding(
    records: list[LandslideRecord],
    geocoder: str = "vworld",
    api_key: Optional[str] = None,
    sleep_sec: float = 0.2,
) -> int:
    """
    Backfill missing lon/lat by geocoding the address field.

    Supported geocoders:
        - "vworld": 국토지리정보원 VWorld geocoder (공공데이터포털)
        - "nominatim": OpenStreetMap (low QPS, for testing)

    Returns:
        number of records successfully geocoded
    """
    import urllib.parse
    import urllib.request
    import time
    import json

    count = 0
    for r in records:
        if r.lon is not None and r.lat is not None:
            continue
        addr = r.address or ""
        if not addr:
            continue

        try:
            if geocoder == "vworld":
                if api_key is None:
                    key = os.environ.get("VWORLD_API_KEY", "")
                else:
                    key = api_key
                if not key:
                    continue
                params = {
                    "service": "address", "request": "getcoord",
                    "version": "2.0", "crs": "epsg:4326",
                    "address": addr, "type": "parcel", "key": key,
                }
                url = "https://api.vworld.kr/req/address?" + urllib.parse.urlencode(params)
                with urllib.request.urlopen(url, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                result = data.get("response", {}).get("result", {})
                pt = result.get("point", {})
                r.lon = _parse_float(pt.get("x"))
                r.lat = _parse_float(pt.get("y"))
                if r.lon is not None and r.lat is not None:
                    count += 1
            elif geocoder == "nominatim":
                params = {"q": addr, "format": "json", "limit": 1}
                url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
                req = urllib.request.Request(url, headers={"User-Agent": "LandslideKR/0.1"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if data:
                    r.lon = _parse_float(data[0].get("lon"))
                    r.lat = _parse_float(data[0].get("lat"))
                    if r.lon is not None and r.lat is not None:
                        count += 1
        except Exception:
            continue

        time.sleep(sleep_sec)

    return count


def records_to_geojson(records: list[LandslideRecord], out_path: Path) -> None:
    """Save records as GeoJSON Point FeatureCollection (EPSG:4326)."""
    features = []
    for r in records:
        if r.lon is None or r.lat is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r.lon, r.lat]},
                "properties": {
                    "occurrence_date": r.occurrence_date,
                    "sido": r.sido,
                    "sigungu": r.sigungu,
                    "address": r.address,
                    "damage_m2": r.damage_m2,
                },
            }
        )
    fc = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}, "features": features}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)


def records_to_label_raster(
    records: list[LandslideRecord],
    bbox: tuple[float, float, float, float],
    resolution_m: int = 30,
    buffer_m: float = 50.0,
) -> "tuple":
    """
    Rasterize records to a binary label (1=landslide, 0=no) at given resolution.

    Args:
        records: landslide records
        bbox: (min_lon, min_lat, max_lon, max_lat) EPSG:4326
        resolution_m: output pixel size (default 30m to match Copernicus DEM)
        buffer_m: buffer radius around point records (50m default)

    Returns:
        (label_array, transform, crs) — rasterio-compatible
    """
    try:
        import numpy as np
        import rasterio
        from rasterio.transform import from_bounds
        from rasterio.features import rasterize
        from shapely.geometry import Point
        import pyproj
    except ImportError as e:
        raise ImportError(
            f"rasterize requires numpy, rasterio, shapely, pyproj: {e}. "
            "Install with: pip install rasterio shapely pyproj"
        )

    # Project bbox to a local UTM for m-based buffer
    min_lon, min_lat, max_lon, max_lat = bbox
    # Pick UTM zone based on centroid longitude
    cent_lon = (min_lon + max_lon) / 2.0
    utm_zone = int((cent_lon + 180) / 6) + 1
    utm_crs = f"EPSG:{32600 + utm_zone}"  # Northern hemisphere
    transformer = pyproj.Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
    inv = pyproj.Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True)

    # Build buffered shapes in lon/lat for rasterize
    shapes = []
    for r in records:
        if r.lon is None or r.lat is None:
            continue
        x, y = transformer.transform(r.lon, r.lat)
        buffered_m = Point(x, y).buffer(buffer_m)
        # Back to EPSG:4326 for rasterize with from_bounds transform
        from shapely.ops import transform as shp_transform
        poly_latlon = shp_transform(lambda xx, yy, z=None: inv.transform(xx, yy), buffered_m)
        shapes.append((poly_latlon.__geo_interface__, 1))

    # Compute grid dims (approximate — 30 m at ~37°N ≈ 0.00035° lat / 0.00042° lon; use degrees)
    deg_per_m_lat = 1.0 / 111_000.0
    deg_per_m_lon = 1.0 / (111_000.0 * np.cos(np.radians((min_lat + max_lat) / 2)))
    pixel_deg_lat = resolution_m * deg_per_m_lat
    pixel_deg_lon = resolution_m * deg_per_m_lon
    width = int(np.ceil((max_lon - min_lon) / pixel_deg_lon))
    height = int(np.ceil((max_lat - min_lat) / pixel_deg_lat))
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

    if not shapes:
        return np.zeros((height, width), dtype=np.uint8), transform, "EPSG:4326"

    label = rasterize(shapes, out_shape=(height, width), transform=transform, fill=0, dtype="uint8")
    return label, transform, "EPSG:4326"


if __name__ == "__main__":
    # Example: fetch 2022 Pohang records
    import sys
    try:
        records = fetch_records(year=2022, sido="경상북도", sigungu="포항시 남구")
        print(f"Fetched {len(records)} records for 2022 포항시 남구")
        for r in records[:3]:
            print(f"  {r.occurrence_date} | {r.address} | lon={r.lon}, lat={r.lat} | {r.damage_m2} m²")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("→ Set DATA_GO_KR_SERVICE_KEY env var first", file=sys.stderr)
