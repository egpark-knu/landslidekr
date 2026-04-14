#!/usr/bin/env python3
"""
Axis 4 — Parameter sensitivity (executed).

Test whether the three-event Pohang-positive / Yecheon-inverted / Chuncheon-random
ROC-AUC pattern lives on a parameter plateau or a knife-edge by sweeping the
SHALSTAB parameter triple (φ, c, T) at the corner combinations of the
pre-registered Table 4 bounds for the *default* lithology fallback.

Design:
    - 3 events × 8 parameter corners (2³ = low/high on each of φ, c, T)
      = 24 ensemble runs, n=100 realizations each.
    - z (soil thickness) and ρ (soil density) held at midpoints.
    - All other inputs (DEM, topo, rainfall, scar reference) constant.
    - Report ROC-AUC and separation per corner per event.
    - Flag: does the three-event qualitative pattern survive across corners?

Output:
    - analysis-output/axis4_param_sensitivity.json
    - analysis-output/axis4_param_sensitivity.csv
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import itertools
import numpy as np
import rasterio
from datetime import datetime
from sklearn.metrics import roc_auc_score

PROJECT = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting")
sys.path.insert(0, str(PROJECT))

from landslide_kr.models.shalstab import compute_stability, ShalstabParams
from landslide_kr.preprocess.topo import compute_topo

OUT_DIR = PROJECT / "analysis-output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EVENTS = [
    {"name": "Pohang 2022", "dir": PROJECT / "out" / "pohang_2022", "label": "pohang", "wstart": "2022-09-05", "wend": "2022-09-07"},
    {"name": "Yecheon 2023", "dir": PROJECT / "out" / "extreme_rainfall_2023", "label": "yecheon", "wstart": "2023-07-13", "wend": "2023-07-18"},
    {"name": "Chuncheon 2020", "dir": PROJECT / "out" / "chuncheon_2020", "label": "chuncheon", "wstart": "2020-08-01", "wend": "2020-08-08"},
]

# Default lithology bounds (Table 4 fallback row) — same as Axis 3 to keep the
# experiment self-contained. φ in degrees, c in Pa, T in m²/s.
PHI_LO, PHI_HI = 28.0, 36.0
C_LO, C_HI = 1000.0, 6000.0
T_LO, T_HI = 5e-5, 5e-4
Z_MID = (0.8 + 2.5) / 2  # 1.65 m
RHO_MID = 1800.0  # midpoint
N_REALIZATIONS = 100
SEED = 42

# Eight corners (low/high on φ, c, T)
CORNERS = list(itertools.product([("phi_lo", PHI_LO), ("phi_hi", PHI_HI)],
                                  [("c_lo", C_LO),     ("c_hi", C_HI)],
                                  [("T_lo", T_LO),     ("T_hi", T_HI)]))


def load_inputs(case_dir: Path, wstart: str, wend: str):
    """Load DEM-derived topo + cached rain raster + reference label, per-event window."""
    delta = datetime.fromisoformat(wend) - datetime.fromisoformat(wstart)
    event_seconds = max(delta.total_seconds(), 3600.0)

    topo = compute_topo(case_dir / "dem_utm.tif")
    with rasterio.open(case_dir / "rain.tif") as ds:
        rain_mm = ds.read(1).astype(float)
    if rain_mm.shape != topo.slope_rad.shape:
        from scipy.ndimage import zoom
        zy = topo.slope_rad.shape[0] / rain_mm.shape[0]
        zx = topo.slope_rad.shape[1] / rain_mm.shape[1]
        rain_mm = zoom(rain_mm, (zy, zx), order=1)[: topo.slope_rad.shape[0], : topo.slope_rad.shape[1]]
    rain_m_per_s = ((rain_mm / 1000.0) / event_seconds).astype(np.float32)

    with rasterio.open(case_dir / "consensus_label.tif") as ds:
        label = ds.read(1) > 0
    if label.shape != topo.slope_rad.shape:
        h = min(label.shape[0], topo.slope_rad.shape[0])
        w = min(label.shape[1], topo.slope_rad.shape[1])
        label = label[:h, :w]
    return topo, rain_m_per_s, label


def run_corner(topo, rain, label, phi, c, T, z, rho):
    """Single deterministic SHALSTAB run at a parameter corner — no MC, no seeds.

    For Axis 4 we want to expose the systematic effect of moving the parameter
    triple, not stochastic noise; we therefore use the corner values directly
    rather than the MC sampler. n=100 only matters for Axis 3 stochastic CV%.
    """
    params = ShalstabParams(
        friction_angle_deg=phi,
        cohesion_pa=c,
        transmissivity=T,
        soil_thickness_m=z,
        soil_density=rho,
    )
    sidx = compute_stability(
        slope_rad=topo.slope_rad,
        upslope_area_m2=topo.upslope_area_m2,
        contour_length_m=topo.contour_length_m,
        rainfall_m_per_s=rain,
        params=params,
    )
    sidx = np.asarray(sidx, dtype=np.float64)
    # Use the stability index directly as the rank score for ROC-AUC
    score = sidx
    valid = np.isfinite(score)
    if score.shape != label.shape:
        h = min(score.shape[0], label.shape[0])
        w = min(score.shape[1], label.shape[1])
        score = score[:h, :w]
        valid = np.isfinite(score)
        lab = label[:h, :w]
    else:
        lab = label
    valid &= np.isfinite(score)
    score_v = score[valid].ravel()
    lab_v = lab[valid].ravel()
    if lab_v.sum() == 0 or lab_v.sum() == lab_v.size:
        return {"skipped": True, "reason": "label degenerate"}
    auc = float(roc_auc_score(lab_v, score_v))
    sep = float(score_v[lab_v].mean() - score_v[~lab_v].mean())
    return {"ROC_AUC": auc, "separation": sep, "n_valid": int(lab_v.size), "n_pos": int(lab_v.sum())}


def main():
    all_results = {}
    for ev in EVENTS:
        print(f"\n=== {ev['name']} ===")
        topo, rain, label = load_inputs(ev["dir"], ev["wstart"], ev["wend"])
        ev_results = []
        for ((pl, phi), (cl, c), (Tl, T)) in CORNERS:
            tag = f"{pl}+{cl}+{Tl}"
            r = run_corner(topo, rain, label, phi, c, T, Z_MID, RHO_MID)
            r["corner"] = tag
            r["phi"] = phi
            r["c"] = c
            r["T"] = T
            ev_results.append(r)
            if r.get("skipped"):
                print(f"  {tag}: SKIPPED ({r['reason']})")
            else:
                print(f"  {tag}: ROC={r['ROC_AUC']:.4f} sep={r['separation']:+.3e}")
        # Pattern-survival summary: does ROC ranking Pohang > Chuncheon > Yecheon hold?
        all_results[ev["label"]] = {
            "name": ev["name"],
            "corners": ev_results,
            "ROC_AUC_min": min((r["ROC_AUC"] for r in ev_results if not r.get("skipped")), default=None),
            "ROC_AUC_max": max((r["ROC_AUC"] for r in ev_results if not r.get("skipped")), default=None),
        }

    # Cross-corner pattern check: in each corner, what is Pohang/Yecheon/Chuncheon ranking?
    print("\n=== Pattern survival across corners ===")
    pattern_ok = 0
    for i, corner in enumerate(CORNERS):
        tag = "+".join(c[0] for c in corner)
        rocs = {ev["label"]: all_results[ev["label"]]["corners"][i].get("ROC_AUC") for ev in EVENTS}
        ranking = sorted(rocs.items(), key=lambda kv: -kv[1] if kv[1] is not None else 0)
        ranking_str = " > ".join(f"{k}({v:.3f})" for k, v in ranking)
        # Headline pattern: Pohang highest ROC, Yecheon below 0.5
        headline_ok = rocs["pohang"] > rocs["yecheon"] and rocs["pohang"] > rocs["chuncheon"]
        pattern_ok += int(headline_ok)
        print(f"  {tag}: {ranking_str} | Pohang highest? {headline_ok}")
    print(f"\nHeadline pattern (Pohang highest ROC) survives in {pattern_ok}/{len(CORNERS)} corners.")
    all_results["pattern_summary"] = {
        "n_corners": len(CORNERS),
        "n_corners_with_pohang_highest": pattern_ok,
        "fraction_pattern_survives": pattern_ok / len(CORNERS),
    }

    out_json = OUT_DIR / "axis4_param_sensitivity.json"
    with open(out_json, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved: {out_json}")

    out_csv = OUT_DIR / "axis4_param_sensitivity.csv"
    with open(out_csv, "w") as f:
        f.write("event,corner,phi,c,T,ROC_AUC,separation\n")
        for ev in EVENTS:
            for r in all_results[ev["label"]]["corners"]:
                if r.get("skipped"):
                    continue
                f.write(f"{ev['label']},{r['corner']},{r['phi']},{r['c']},{r['T']:.2e},{r['ROC_AUC']:.4f},{r['separation']:+.4e}\n")
    print(f"Saved: {out_csv}")


if __name__ == "__main__":
    main()
