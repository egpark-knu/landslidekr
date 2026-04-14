"""
Landslide models.

Status:
- shalstab.py: Steady-state infinite-slope + TOPMODEL hydrology (Montgomery & Dietrich 1994)
- trigrs.py: Transient rainfall infiltration + grid-based slope stability (USGS)
- sinmap.py: Stability Index Mapping (probabilistic)

Priority: SHALSTAB first (simplest, fastest). TRIGRS second (transient rainfall).
"""
from __future__ import annotations

__all__ = ["shalstab", "trigrs", "sinmap"]
