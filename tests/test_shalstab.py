"""
SHALSTAB unit tests — Montgomery & Dietrich (1994) equations.

Sanity checks:
- Flat terrain (slope=0) → unconditionally stable
- Very steep (slope > φ) → unconditionally unstable
- Stability increases with cohesion
- Stability decreases with rainfall
"""
from __future__ import annotations

import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from landslide_kr.models.shalstab import (
    ShalstabParams,
    compute_stability,
    classify,
)


def test_flat_is_unconditionally_stable():
    """Flat terrain should be unconditionally stable (class 0)."""
    slope = np.array([[0.0]])
    area = np.array([[1000.0]])
    b = np.array([[30.0]])
    rain = np.array([[1e-6]])
    p = ShalstabParams()
    s = compute_stability(slope, area, b, rain, p)
    c = classify(s, slope, p)
    assert c[0, 0] == 0


def test_very_steep_is_unconditionally_unstable():
    """Slope > φ should be unconditionally unstable (class 5)."""
    phi = 35.0
    slope = np.array([[np.radians(phi + 10)]])  # 45°
    area = np.array([[500.0]])
    b = np.array([[30.0]])
    rain = np.array([[1e-7]])
    p = ShalstabParams(friction_angle_deg=phi)
    s = compute_stability(slope, area, b, rain, p)
    c = classify(s, slope, p)
    assert c[0, 0] == 5


def test_cohesion_increases_stability():
    """Higher cohesion should decrease stability ratio (more stable)."""
    slope = np.array([[np.radians(25.0)]])
    area = np.array([[2000.0]])
    b = np.array([[30.0]])
    rain = np.array([[1e-6]])
    p_low = ShalstabParams(cohesion_pa=500.0)
    p_high = ShalstabParams(cohesion_pa=5000.0)
    s_low = compute_stability(slope, area, b, rain, p_low)
    s_high = compute_stability(slope, area, b, rain, p_high)
    assert s_high[0, 0] < s_low[0, 0]


def test_rainfall_increases_instability():
    """Higher rainfall → higher stability ratio q/q_cr."""
    slope = np.array([[np.radians(25.0)]])
    area = np.array([[2000.0]])
    b = np.array([[30.0]])
    rain_low = np.array([[1e-7]])
    rain_high = np.array([[1e-5]])
    p = ShalstabParams()
    s_low = compute_stability(slope, area, b, rain_low, p)
    s_high = compute_stability(slope, area, b, rain_high, p)
    assert s_high[0, 0] > s_low[0, 0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
