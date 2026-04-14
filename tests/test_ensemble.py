"""
Tests for SINMAP-style bounded Monte Carlo ensemble wrapper.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from landslide_kr.models.ensemble import run_ensemble
from landslide_kr.models.lithology_params import get_bounds, LITHOLOGY_BOUNDS


def _make_grid(slope_deg_range=(20, 40), n=10):
    h, w = n, n
    slope_rad = np.radians(np.linspace(slope_deg_range[0], slope_deg_range[1], h)[:, None] * np.ones((1, w)))
    area = np.full((h, w), 2000.0)
    b = np.full((h, w), 30.0)
    rain = np.full((h, w), 5e-6)  # 18 mm/hr (realistic heavy rain)
    return slope_rad, area, b, rain


def test_ensemble_runs_uniform_lithology():
    slope, area, b, rain = _make_grid()
    result = run_ensemble(slope, area, b, rain, lithology_class="granite", n_realizations=20)
    assert result.n_realizations == 20
    assert result.prob_unstable.shape == slope.shape
    # Probability must be in [0, 1]
    assert (result.prob_unstable >= 0).all()
    assert (result.prob_unstable <= 1).all()


def test_ensemble_probability_monotone_with_rainfall():
    slope, area, b, _ = _make_grid()
    rain_low = np.full(slope.shape, 1e-7)   # drizzle
    rain_high = np.full(slope.shape, 5e-5)  # extreme

    r_low = run_ensemble(slope, area, b, rain_low, "granite", n_realizations=20, seed=1)
    r_high = run_ensemble(slope, area, b, rain_high, "granite", n_realizations=20, seed=1)

    # On steep terrain, higher rainfall should increase P(unstable) for same seed
    steep_mask = np.radians(35) < slope
    assert r_high.prob_unstable[steep_mask].mean() >= r_low.prob_unstable[steep_mask].mean()


def test_lithology_per_cell_array():
    slope, area, b, rain = _make_grid(n=6)
    # Half the grid granite, half sedimentary
    lith = np.full(slope.shape, "granite", dtype=object)
    lith[:, 3:] = "sedimentary"
    result = run_ensemble(slope, area, b, rain, lithology_class=lith, n_realizations=10)
    assert result.prob_unstable.shape == slope.shape


def test_bounds_are_literature_grounded():
    """Sanity check on parameter bounds."""
    for lith, b in LITHOLOGY_BOUNDS.items():
        assert 20 <= b.friction_angle_deg[0] <= b.friction_angle_deg[1] <= 45, f"phi bounds for {lith}"
        assert 100 <= b.cohesion_pa[0] <= b.cohesion_pa[1] <= 15000, f"cohesion bounds for {lith}"
        assert 1e-6 <= b.transmissivity[0] <= b.transmissivity[1] <= 1e-2, f"T bounds for {lith}"
        assert 0.3 <= b.soil_thickness_m[0] <= b.soil_thickness_m[1] <= 6.0, f"depth bounds for {lith}"


def test_korean_lithology_mapping():
    """Korean names should map to English classes."""
    assert get_bounds("화강암").friction_angle_deg == LITHOLOGY_BOUNDS["granite"].friction_angle_deg
    assert get_bounds("화산암").friction_angle_deg == LITHOLOGY_BOUNDS["volcanic"].friction_angle_deg
    assert get_bounds("unknown_fallback").friction_angle_deg == LITHOLOGY_BOUNDS["default"].friction_angle_deg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
