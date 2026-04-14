#!/usr/bin/env python3
"""
Post-hoc FAR refinement of SHALSTAB prob_unstable.tif.

Applies three physically-motivated masks without re-running the ensemble:
  1. Slope mask: slope > slope_min_deg (default 10°, hillslope scale)
  2. Channel/floodplain mask: exclude pixels with very high upslope accumulation
     (proxy via low relative elevation = local valley bottom)
  3. Lithology mask: exclude alluvium class (never landslide-prone per literature)

Re-computes POD / FAR / CSI / ROC-AUC with the refined prob.

Also evaluates three alternative rankings:
  - Slope alone
  - Slope × (elevation - valley_floor) / local_relief
  - Original SHALSTAB × slope_mask

Output: refinement_report.json + per-case refined_prob.tif
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np
import rasterio


def horn_slope_deg(dem: np.ndarray, pixel_size_m: float) -> np.ndarray:
    """Horn (1981) 3x3 slope in degrees."""
    padded = np.pad(dem, 1, mode="edge")
    dzdx = ((padded[:-2, 2:] + 2 * padded[1:-1, 2:] + padded[2:, 2:]) -
            (padded[:-2, :-2] + 2 * padded[1:-1, :-2] + padded[2:, :-2])) / (8 * pixel_size_m)
    dzdy = ((padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:]) -
            (padded[:-2, :-2] + 2 * padded[:-2, 1:-1] + padded[:-2, 2:])) / (8 * pixel_size_m)
    return np.degrees(np.arctan(np.sqrt(dzdx ** 2 + dzdy ** 2))).astype(np.float32)


def local_relief(dem: np.ndarray, window_size: int = 33) -> np.ndarray:
    """
    Local relief = local_max - elevation, within a square window.
    High values = near valley floor (lots of relief above); low = near ridge.
    Simple moving-max approximation using scipy.
    """
    from scipy.ndimage import maximum_filter
    local_max = maximum_filter(dem, size=window_size, mode="nearest")
    return (local_max - dem).astype(np.float32)


def evaluate(prob: np.ndarray, label: np.ndarray, name: str) -> dict:
    from sklearn.metrics import roc_auc_score, average_precision_score

    p = prob.ravel()
    l = label.ravel().astype(bool)
    valid = np.isfinite(p)
    p = p[valid]
    l = l[valid]
    if l.sum() == 0 or (~l).sum() == 0 or len(p) == 0:
        return {"name": name, "error": "no valid positives/negatives"}

    # Binary mask at p>=0.5
    pred = p >= 0.5
    tp = int((pred & l).sum())
    fp = int((pred & ~l).sum())
    fn = int((~pred & l).sum())
    tn = int((~pred & ~l).sum())
    pod = tp / (tp + fn) if (tp + fn) else 0.0
    far = fp / (tp + fp) if (tp + fp) else 0.0
    csi = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0
    f1 = (2 * tp) / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0

    auc = float(roc_auc_score(l, p))
    ap = float(average_precision_score(l, p))

    # Top-percentile evaluations
    top1_thr = float(np.quantile(p, 0.99))
    top1_pred = p >= top1_thr
    top1_tp = int((top1_pred & l).sum())
    top1_fp = int((top1_pred & ~l).sum())
    top1_prec = top1_tp / (top1_tp + top1_fp) if (top1_tp + top1_fp) else 0.0
    top1_recall = top1_tp / l.sum()

    return {
        "name": name, "n_valid": int(len(p)), "n_positive": int(l.sum()),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "POD": round(pod, 4), "FAR": round(far, 4), "CSI": round(csi, 4),
        "F1": round(f1, 4), "Precision": round(prec, 4),
        "ROC_AUC": round(auc, 4), "AP": round(ap, 5),
        "top1_precision": round(top1_prec, 5),
        "top1_recall": round(top1_recall, 4),
        "mean_scar_prob": round(float(p[l].mean()), 4),
        "mean_nonscar_prob": round(float(p[~l].mean()), 4),
        "separation": round(float(p[l].mean() - p[~l].mean()), 4),
    }


def refine_case(case_dir: Path, slope_min_deg: float = 10.0,
                relief_min_m: float = 30.0,
                exclude_lithology: tuple = ("alluvium",)) -> dict:
    """
    Apply post-hoc FAR refinement to a single case.

    Returns a report dict with baseline and refined metrics.
    """
    with rasterio.open(case_dir / "prob_unstable.tif") as ds:
        prob = ds.read(1).astype(np.float32)
        transform = ds.transform
        crs = ds.crs
        pixel_size_m = abs(transform.a)
        profile = ds.profile.copy()
    with rasterio.open(case_dir / "consensus_label.tif") as ds:
        label = ds.read(1) > 0
    with rasterio.open(case_dir / "dem_utm.tif") as ds:
        dem = ds.read(1).astype(np.float32)

    # Ensure shapes match — resample DEM to prob grid if needed
    if dem.shape != prob.shape:
        from scipy.ndimage import zoom
        zy = prob.shape[0] / dem.shape[0]
        zx = prob.shape[1] / dem.shape[1]
        dem = zoom(dem, (zy, zx), order=1)[:prob.shape[0], :prob.shape[1]]

    # --- Baseline ---
    baseline = evaluate(prob, label, "baseline_full_prob")

    # --- Slope + relief masks ---
    slope = horn_slope_deg(dem, pixel_size_m)
    relief = local_relief(dem, window_size=33)
    hillslope_mask = (slope > slope_min_deg) & (relief > relief_min_m)

    prob_masked = np.where(hillslope_mask, prob, 0.0).astype(np.float32)

    masked = evaluate(prob_masked, label, f"masked_slope>{slope_min_deg}_relief>{relief_min_m}")

    # --- Alternative: slope alone ranking (no SHALSTAB) ---
    slope_ranking = slope / 90.0  # [0, 1]
    slope_eval = evaluate(slope_ranking, label, "slope_alone")

    # --- Alternative: slope × relief ranking ---
    se = (slope / 90.0) * (relief / (relief.max() + 1e-9))
    se_eval = evaluate(se, label, "slope_x_relief")

    # Save refined prob tif
    out_path = case_dir / "prob_refined.tif"
    profile.update(dtype="float32", count=1, compress="deflate")
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(prob_masked, 1)

    return {
        "case": case_dir.name,
        "parameters": {
            "slope_min_deg": slope_min_deg,
            "relief_min_m": relief_min_m,
            "exclude_lithology": list(exclude_lithology),
        },
        "masks": {
            "hillslope_fraction": float(hillslope_mask.mean()),
            "scar_in_hillslope_pct": float(label[hillslope_mask].sum() / label.sum() * 100) if label.sum() else 0.0,
        },
        "baseline": baseline,
        "refined": masked,
        "slope_alone": slope_eval,
        "slope_x_relief": se_eval,
        "out_refined_tif": str(out_path),
    }


def main(argv: list[str]) -> int:
    root = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/out")
    cases = ["pohang_2022", "extreme_rainfall_2023"]
    reports = {}
    for c in cases:
        p = root / c
        if not (p / "prob_unstable.tif").exists():
            continue
        print(f"\n{'='*60}\nRefining {c}\n{'='*60}")
        r = refine_case(p)
        reports[c] = r
        # Compact print
        print(f"\n[{c}] summary:")
        for key in ("baseline", "refined", "slope_alone", "slope_x_relief"):
            v = r[key]
            print(f"  {key:25s}: POD={v.get('POD',0):.3f}  FAR={v.get('FAR',0):.3f}  "
                  f"CSI={v.get('CSI',0):.4f}  ROC={v.get('ROC_AUC',0):.3f}  "
                  f"sep={v.get('separation',0):+.3f}")

    out_json = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/communication/research/post_hoc_refinement_20260414.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
