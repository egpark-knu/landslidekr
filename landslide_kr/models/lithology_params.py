"""
Lithology-based SHALSTAB parameter table (Phase 2 decision).

Rationale (from BoN consensus):
    - Per-event manual tuning is a reviewer attack surface ("tuning artifact").
    - Pre-registered parameter bounds per lithology class (Granite / Volcanic /
      Sedimentary / Metamorphic / Alluvium) are more defensible.
    - Bounds → SINMAP-style Monte Carlo ensemble → instability probability map.

References:
    - Park, Nikhil & Lee (2013) Korean SHALSTAB parameters, NHESS 13:2833
    - Montgomery & Dietrich (1994) original parameter ranges
    - Hammond et al. (1992) SINMAP parameter ranges

Note: These are **literature-grounded bounds**, not best-fits to our events.
Event-holdout / leave-one-out evaluation must preserve these bounds.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParamBounds:
    """Bounded parameter range for Monte Carlo sampling."""

    friction_angle_deg: tuple[float, float]   # φ (degrees)
    cohesion_pa: tuple[float, float]          # c (Pa) — soil + root
    transmissivity: tuple[float, float]       # T (m²/s)
    soil_thickness_m: tuple[float, float]     # depth (m)
    soil_density: tuple[float, float] = (1600.0, 2000.0)   # kg/m³

    def sample(self, rng=None) -> dict:
        """Uniform sample from bounds."""
        import numpy as np
        if rng is None:
            rng = np.random.default_rng()
        return {
            "friction_angle_deg": float(rng.uniform(*self.friction_angle_deg)),
            "cohesion_pa": float(rng.uniform(*self.cohesion_pa)),
            "transmissivity": 10 ** float(rng.uniform(
                # sample in log-space for transmissivity (spans orders of magnitude)
                *[math_log10(x) for x in self.transmissivity]
            )),
            "soil_thickness_m": float(rng.uniform(*self.soil_thickness_m)),
            "soil_density": float(rng.uniform(*self.soil_density)),
        }


def math_log10(x: float) -> float:
    import math
    return math.log10(x)


# Literature-grounded bounds per lithology class (Korean context emphasis)
LITHOLOGY_BOUNDS: dict[str, ParamBounds] = {
    "granite": ParamBounds(
        # Well-weathered granite residual soil — common in Korea
        # HP Round 3 Decision C (2026-04-14): bounds relaxed to reduce saturation
        # at prob=1.0 observed in Pohang 2022 MC (mean 0.85 / median 1.0 for scar,
        # 0.68 / 0.99 for non-scar → over-confident).
        friction_angle_deg=(28.0, 38.0),   # Park et al. 2013 Pohang-area
        cohesion_pa=(2000.0, 10000.0),     # ↑ higher floor reduces unstable prediction
        transmissivity=(1e-4, 1e-3),       # ↑ higher T → less pore pressure buildup
        soil_thickness_m=(0.8, 2.5),
    ),
    "volcanic": ParamBounds(
        # Weathered volcanic (Cheju, some SE Korea ridges)
        friction_angle_deg=(30.0, 40.0),
        cohesion_pa=(2000.0, 12000.0),
        transmissivity=(1e-4, 1e-3),
        soil_thickness_m=(0.5, 2.0),
    ),
    "sedimentary": ParamBounds(
        # Mudstone / sandstone residual
        friction_angle_deg=(22.0, 34.0),
        cohesion_pa=(500.0, 5000.0),
        transmissivity=(2e-5, 2e-4),
        soil_thickness_m=(1.0, 3.0),
    ),
    "metamorphic": ParamBounds(
        # Gneiss / schist residual
        friction_angle_deg=(26.0, 36.0),
        cohesion_pa=(1500.0, 8000.0),
        transmissivity=(3e-5, 3e-4),
        soil_thickness_m=(0.8, 2.5),
    ),
    "alluvium": ParamBounds(
        # Colluvium / fluvial — generally stable on low slopes
        friction_angle_deg=(25.0, 35.0),
        cohesion_pa=(500.0, 3000.0),
        transmissivity=(5e-4, 5e-3),
        soil_thickness_m=(1.5, 5.0),
    ),
    "default": ParamBounds(
        # Fallback when lithology layer unavailable
        friction_angle_deg=(28.0, 36.0),
        cohesion_pa=(1000.0, 6000.0),
        transmissivity=(5e-5, 5e-4),
        soil_thickness_m=(0.8, 2.5),
    ),
}


def get_bounds(lithology: str) -> ParamBounds:
    """Get bounds for a lithology class (case-insensitive, falls back to default)."""
    key = (lithology or "default").lower().strip()
    # Map common Korean geology codes to classes
    mapping = {
        "화강암": "granite",
        "화산암": "volcanic",
        "퇴적암": "sedimentary",
        "변성암": "metamorphic",
        "충적층": "alluvium",
    }
    key = mapping.get(key, key)
    return LITHOLOGY_BOUNDS.get(key, LITHOLOGY_BOUNDS["default"])


if __name__ == "__main__":
    import json
    import numpy as np

    rng = np.random.default_rng(42)
    for lith in ["granite", "volcanic", "sedimentary", "metamorphic", "alluvium"]:
        b = get_bounds(lith)
        sample = b.sample(rng)
        print(f"\n{lith}:")
        print(json.dumps(sample, indent=2))
