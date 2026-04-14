"""
SINMAP-style bounded Monte Carlo ensemble for SHALSTAB.

Phase 2 decision: 100 realizations per lithology class per cell.
Output: instability probability map (0..1) + mean/std of q/q_cr.

This is the paper's main uncertainty-aware product.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from landslide_kr.models.shalstab import ShalstabParams, compute_stability
from landslide_kr.models.lithology_params import ParamBounds, get_bounds


@dataclass
class EnsembleResult:
    """Per-cell ensemble statistics."""

    prob_unstable: "np.ndarray"   # P(q/q_cr >= 1) in [0, 1]
    mean_ratio: "np.ndarray"      # mean of q/q_cr across realizations
    std_ratio: "np.ndarray"       # std of q/q_cr
    n_realizations: int


def run_ensemble(
    slope_rad: "np.ndarray",
    upslope_area_m2: "np.ndarray",
    contour_length_m: "np.ndarray",
    rainfall_m_per_s: "np.ndarray",
    lithology_class: "np.ndarray",  # dtype=object or int; dtype=str array mapped via get_bounds
    n_realizations: int = 100,
    unstable_threshold: float = 1.0,
    seed: int = 42,
) -> EnsembleResult:
    """
    Run Monte Carlo SHALSTAB ensemble with lithology-conditional parameter bounds.

    Args:
        slope_rad: slope in radians (H x W)
        upslope_area_m2: upslope contributing area (H x W)
        contour_length_m: unit-width contour length (H x W)
        rainfall_m_per_s: effective rainfall intensity (H x W)
        lithology_class: array of lithology names per cell (H x W, strings)
                         or a single string (applied uniformly)
        n_realizations: Monte Carlo samples per cell (Phase 2 decision: 100)
        unstable_threshold: q/q_cr threshold for "unstable" classification (default 1.0)
        seed: RNG seed

    Returns:
        EnsembleResult with prob_unstable, mean_ratio, std_ratio
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    h, w = slope_rad.shape

    # Accumulators
    count_unstable = np.zeros((h, w), dtype=np.float32)
    sum_ratio = np.zeros((h, w), dtype=np.float64)
    sum_sq_ratio = np.zeros((h, w), dtype=np.float64)

    # Case 1: single lithology string applied to all cells
    if isinstance(lithology_class, str):
        bounds = get_bounds(lithology_class)
        for i in range(n_realizations):
            params = _sample_params(bounds, rng)
            ratio = compute_stability(slope_rad, upslope_area_m2, contour_length_m, rainfall_m_per_s, params)
            count_unstable += (ratio >= unstable_threshold).astype(np.float32)
            sum_ratio += ratio
            sum_sq_ratio += ratio ** 2

    # Case 2: per-cell lithology array
    else:
        # Build a mask per unique lithology (efficiency: one simulation per lith class per realization)
        unique_liths = np.unique(lithology_class)
        for i in range(n_realizations):
            ratio = np.full((h, w), np.nan, dtype=np.float32)
            for lith in unique_liths:
                mask = (lithology_class == lith)
                bounds = get_bounds(str(lith))
                params = _sample_params(bounds, rng)
                # Apply only where mask (compute_stability works on arrays; subset via mask)
                sub_ratio = compute_stability(
                    slope_rad, upslope_area_m2, contour_length_m, rainfall_m_per_s, params
                )
                ratio[mask] = sub_ratio[mask]
            # Skip NaN cells from accumulation
            valid = np.isfinite(ratio)
            count_unstable[valid] += (ratio[valid] >= unstable_threshold).astype(np.float32)
            sum_ratio[valid] += ratio[valid]
            sum_sq_ratio[valid] += ratio[valid] ** 2

    prob_unstable = count_unstable / n_realizations
    mean_ratio = (sum_ratio / n_realizations).astype(np.float32)
    var_ratio = (sum_sq_ratio / n_realizations) - mean_ratio ** 2
    var_ratio = np.maximum(var_ratio, 0.0)  # numerical floor
    std_ratio = np.sqrt(var_ratio).astype(np.float32)

    return EnsembleResult(
        prob_unstable=prob_unstable.astype(np.float32),
        mean_ratio=mean_ratio,
        std_ratio=std_ratio,
        n_realizations=n_realizations,
    )


def _sample_params(bounds: ParamBounds, rng) -> ShalstabParams:
    sample = bounds.sample(rng)
    return ShalstabParams(**sample)


if __name__ == "__main__":
    import numpy as np

    # Smoke test: 50x50 grid, single lithology
    h, w = 50, 50
    slope = np.radians(np.linspace(10, 45, h)[:, None] * np.ones((1, w), dtype=np.float32))
    area = np.full((h, w), 3000.0, dtype=np.float32)
    b = np.full((h, w), 30.0, dtype=np.float32)
    rain = np.full((h, w), 1e-5, dtype=np.float32)  # 36 mm/hr equivalent

    result = run_ensemble(slope, area, b, rain, lithology_class="granite", n_realizations=50)
    print(f"n_realizations: {result.n_realizations}")
    print(f"prob_unstable shape: {result.prob_unstable.shape}")
    print(f"prob_unstable min/mean/max: {result.prob_unstable.min():.3f} / "
          f"{result.prob_unstable.mean():.3f} / {result.prob_unstable.max():.3f}")
    print(f"mean_ratio min/max: {result.mean_ratio.min():.3f} / {result.mean_ratio.max():.3f}")
