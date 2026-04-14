"""
Case configuration schema (WildfireKR-inspired).

Each landslide case is a YAML/JSON file under cases/<case_id>/config.yaml.

Example:
    case_id: pohang_2022
    event_window:
      start: "2022-09-05"
      end:   "2022-09-07"
    aoi:
      bbox: [129.2, 36.0, 129.5, 36.2]   # [min_lon, min_lat, max_lon, max_lat]
      crs: EPSG:4326
    rainfall:
      source: GPM_IMERG_V07
      cumulative_mm: 412.0
    labels:
      source: NIDR + Sentinel-2
      raster_path: data/labels/pohang_2022_labels.tif
    model:
      name: SHALSTAB
      params:
        friction_angle_deg: 35.0
        cohesion_pa: 2000.0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json


@dataclass
class EventWindow:
    start: str
    end: str


@dataclass
class AOI:
    bbox: list[float]
    crs: str = "EPSG:4326"
    description: str = ""


@dataclass
class CaseConfig:
    case_id: str
    event_window: EventWindow
    aoi: AOI
    rainfall_source: str = "GPM_IMERG_V07"
    cumulative_mm: Optional[float] = None
    label_path: Optional[Path] = None
    model_name: str = "SHALSTAB"
    model_params: dict = field(default_factory=dict)
    dem_root: Optional[str] = None        # Copernicus DEM tile directory
    geology_path: Optional[str] = None    # Korean geology GPKG path
    gee_project: Optional[str] = None     # Earth Engine project ID

    @classmethod
    def from_json(cls, path: Path) -> "CaseConfig":
        with open(path) as f:
            data = json.load(f)
        rainfall = data.get("rainfall", {})
        return cls(
            case_id=data["case_id"],
            event_window=EventWindow(**data["event_window"]),
            aoi=AOI(**data["aoi"]),
            rainfall_source=rainfall.get("source", "GPM_IMERG_V07"),
            cumulative_mm=rainfall.get("cumulative_mm_reported") or rainfall.get("cumulative_mm"),
            label_path=Path(data["labels"]["raster_path"]) if "labels" in data else None,
            model_name=data.get("model", {}).get("name", "SHALSTAB"),
            model_params=data.get("model", {}).get("params", {}),
            dem_root=data.get("dem_root"),
            geology_path=data.get("geology_path"),
            gee_project=data.get("gee_project"),
        )
