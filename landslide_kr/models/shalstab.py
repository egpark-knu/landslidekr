"""
SHALSTAB — Shallow Landsliding Stability Model (Montgomery & Dietrich, 1994)

Core equation (critical steady-state rainfall for slope failure):
    q_cr / T = (sin θ / a/b) × [ρs/ρw × (1 - tan θ / tan φ) + C' / (ρw g z cos²θ tan φ)]

Simplified cohesionless form:
    q_cr / T = (sin θ · b / a) × (ρs/ρw) × (1 - tan θ / tan φ)

Where:
    q_cr: critical steady-state rainfall [m/s]
    T: soil transmissivity [m²/s]
    a: upslope contributing area [m²]
    b: contour length [m]
    θ: local slope [rad]
    φ: friction angle [rad]
    ρs, ρw: soil, water density [kg/m³]
    C': effective cohesion [Pa]
    z: soil thickness [m]

Output classes:
    unconditionally_stable, stable, quasi-stable, lower_threshold, upper_threshold,
    unconditionally_unstable
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class ShalstabParams:
    """SHALSTAB parameters (Korea-calibrated defaults).

    Defaults tuned for Korean granitic/volcanic terrain with shallow residual soils.
    Users should override per case study.
    """
    friction_angle_deg: float = 35.0   # φ for Korean weathered granite/soil
    cohesion_pa: float = 2000.0        # C' [Pa] — residual soils
    soil_density: float = 1800.0       # ρs [kg/m³]
    water_density: float = 1000.0      # ρw [kg/m³]
    soil_thickness_m: float = 1.5      # z [m]
    transmissivity: float = 1e-4       # T [m²/s]
    gravity: float = 9.81              # g [m/s²]


def compute_stability(
    slope_rad: np.ndarray,
    upslope_area_m2: np.ndarray,
    contour_length_m: np.ndarray,
    rainfall_m_per_s: np.ndarray,
    params: ShalstabParams,
) -> np.ndarray:
    """
    Compute SHALSTAB stability index.

    Returns:
        stability_ratio: q / q_cr (>1 = unstable)
    """
    sin_theta = np.sin(slope_rad)
    tan_theta = np.tan(slope_rad)
    tan_phi = np.tan(np.radians(params.friction_angle_deg))

    # Avoid div-by-zero
    slope_term = np.where(sin_theta > 1e-6, sin_theta, 1e-6)
    area_term = np.where(contour_length_m > 0, upslope_area_m2 / contour_length_m, np.inf)

    # Cohesion term
    coh_term = params.cohesion_pa / (
        params.water_density * params.gravity * params.soil_thickness_m
        * np.cos(slope_rad) ** 2 * tan_phi
    )

    # Critical rainfall ratio q_cr/T
    qcr_over_T = (slope_term / np.maximum(area_term, 1e-6)) * (
        (params.soil_density / params.water_density) * (1 - tan_theta / tan_phi)
        + coh_term
    )

    # Actual rainfall ratio q/T
    q_over_T = rainfall_m_per_s / params.transmissivity

    # Stability ratio
    stability = q_over_T / np.maximum(qcr_over_T, 1e-12)

    return stability


def classify(stability: np.ndarray, slope_rad: np.ndarray, params: ShalstabParams) -> np.ndarray:
    """
    Classify SHALSTAB output into 6 stability classes.

    Returns:
        class_map: int array (0=unconditionally_stable ... 5=unconditionally_unstable)
    """
    tan_theta = np.tan(slope_rad)
    tan_phi = np.tan(np.radians(params.friction_angle_deg))

    classes = np.zeros_like(stability, dtype=np.int8)

    # Unconditionally stable: tan θ ≤ tan φ (1 - ρw/ρs)
    uncond_stable = tan_theta <= tan_phi * (1 - params.water_density / params.soil_density)
    # Unconditionally unstable: tan θ > tan φ
    uncond_unstable = tan_theta > tan_phi

    classes[uncond_stable] = 0
    classes[~uncond_stable & (stability < 0.1)] = 1          # stable
    classes[~uncond_stable & (stability >= 0.1) & (stability < 0.5)] = 2   # quasi-stable
    classes[~uncond_stable & (stability >= 0.5) & (stability < 1.0)] = 3   # lower threshold
    classes[~uncond_stable & (stability >= 1.0) & ~uncond_unstable] = 4    # upper threshold
    classes[uncond_unstable] = 5

    return classes
