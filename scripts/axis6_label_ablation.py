#!/usr/bin/env python3
"""
Axis 6 — Label-layer ablation.

Evaluates SHALSTAB MC predictions against four reference-label variants:
  A. Sentinel-only (existing Sentinel-2 scar raster)
  B. NIDR-only (30 m buffer around VWorld-geocoded NIDR points)
  C. Sentinel ∪ NIDR (planned consensus)
  D. Sentinel ∩ NIDR (high-confidence intersection)

Reports per variant + event:
  - Base rate
  - POD / FAR / CSI / F1
  - ROC-AUC (sklearn)
  - Scar/non-scar mean prob + separation
  - AP (average precision) + AP/base_rate lift

Only executes on events whose `nidr.geojson` contains N_nidr_points > 0.
Events without NIDR points fall through with a disclosure entry.

Outputs:
  - analysis-output/axis6_label_ablation.json
  - analysis-output/axis6_label_ablation.csv
"""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import rasterio
import rasterio.features
import geopandas as gpd
from shapely.geometry import Point
from sklearn.metrics import roc_auc_score, average_precision_score

ROOT = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting")
OUT = ROOT / "analysis-output"
OUT.mkdir(parents=True, exist_ok=True)

EVENTS = [
    {"name": "Pohang 2022",     "dir": ROOT / "out" / "pohang_2022",           "label": "pohang"},
    {"name": "Yecheon 2023",    "dir": ROOT / "out" / "extreme_rainfall_2023", "label": "yecheon"},
    {"name": "Chuncheon 2020",  "dir": ROOT / "out" / "chuncheon_2020",        "label": "chuncheon"},
]

NIDR_BUFFER_M = 30


def build_nidr_mask(nidr_geojson_path: Path, prob_raster_path: Path) -> tuple[np.ndarray, int]:
    """Buffer NIDR points by NIDR_BUFFER_M and rasterize to the prob grid."""
    if not nidr_geojson_path.exists():
        with rasterio.open(prob_raster_path) as ds:
            return np.zeros((ds.height, ds.width), dtype=bool), 0
    try:
        gdf = gpd.read_file(nidr_geojson_path)
    except Exception:
        with rasterio.open(prob_raster_path) as ds:
            return np.zeros((ds.height, ds.width), dtype=bool), 0
    if gdf.empty:
        with rasterio.open(prob_raster_path) as ds:
            return np.zeros((ds.height, ds.width), dtype=bool), 0

    # Project to the prob raster CRS (UTM) so 30 m buffer is sensible
    with rasterio.open(prob_raster_path) as ds:
        target_crs = ds.crs
        out_shape = (ds.height, ds.width)
        transform = ds.transform
    gdf = gdf.to_crs(target_crs)

    # Keep only points (NIDR as centroids)
    gdf = gdf[gdf.geometry.type.isin(["Point", "MultiPoint"])].copy()
    n_pts = len(gdf)
    if n_pts == 0:
        return np.zeros(out_shape, dtype=bool), 0

    # Buffer each point by NIDR_BUFFER_M metres
    gdf["geometry"] = gdf.geometry.buffer(NIDR_BUFFER_M)
    shapes = ((geom, 1) for geom in gdf.geometry if not geom.is_empty)
    mask = rasterio.features.rasterize(
        shapes, out_shape=out_shape, transform=transform,
        fill=0, dtype=np.uint8, all_touched=True,
    ).astype(bool)
    return mask, n_pts


def metrics(prob: np.ndarray, label: np.ndarray, valid: np.ndarray) -> dict:
    y_score = prob[valid]
    y_true = label[valid]
    if y_true.sum() == 0:
        return {"skipped": True, "reason": "no positive pixels"}

    base = float(y_true.mean())
    # Binary prediction at p >= 0.5
    y_pred = (y_score >= 0.5)
    TP = int(((y_pred) & (y_true)).sum())
    FP = int(((y_pred) & (~y_true)).sum())
    FN = int(((~y_pred) & (y_true)).sum())
    TN = int(((~y_pred) & (~y_true)).sum())
    POD = TP / max(TP + FN, 1)
    FAR = FP / max(TP + FP, 1)
    CSI = TP / max(TP + FP + FN, 1)
    precision = TP / max(TP + FP, 1)
    f1 = 2 * precision * POD / max(precision + POD, 1e-12)
    roc = float(roc_auc_score(y_true, y_score)) if y_true.sum() > 0 and (~y_true).sum() > 0 else None
    ap = float(average_precision_score(y_true, y_score)) if y_true.sum() > 0 else None
    scar_mean = float(y_score[y_true].mean()) if y_true.sum() > 0 else None
    non_scar_mean = float(y_score[~y_true].mean()) if (~y_true).sum() > 0 else None
    sep = (scar_mean - non_scar_mean) if scar_mean is not None and non_scar_mean is not None else None
    return {
        "skipped": False,
        "n_valid": int(valid.sum()),
        "n_positive": int(y_true.sum()),
        "base_rate": base,
        "TP": TP, "FP": FP, "FN": FN, "TN": TN,
        "POD": round(POD, 4),
        "FAR": round(FAR, 4),
        "CSI": round(CSI, 4),
        "F1": round(f1, 4),
        "precision": round(precision, 6),
        "ROC_AUC": round(roc, 4) if roc is not None else None,
        "AP": round(ap, 4) if ap is not None else None,
        "ap_over_base_rate": round(ap / max(base, 1e-9), 3) if ap is not None else None,
        "scar_mean_prob": round(scar_mean, 4) if scar_mean is not None else None,
        "non_scar_mean_prob": round(non_scar_mean, 4) if non_scar_mean is not None else None,
        "separation": round(sep, 4) if sep is not None else None,
    }


def process(ev: dict) -> dict:
    d = ev["dir"]
    prob_p = d / "prob_unstable.tif"
    consensus_p = d / "consensus_label.tif"  # Sentinel-only equivalent when NIDR empty
    nidr_p = d / "nidr.geojson"

    with rasterio.open(prob_p) as src:
        prob = src.read(1).astype(float)
    # Variant A: use consensus_label.tif (prob-grid aligned, matches §3.1)
    with rasterio.open(consensus_p) as src:
        consensus = src.read(1) > 0
    valid = np.isfinite(prob) & (prob >= 0)

    # Align shapes (defensive — they should already match since consensus is written on prob grid)
    h = min(prob.shape[0], consensus.shape[0])
    w = min(prob.shape[1], consensus.shape[1])
    prob = prob[:h, :w]; consensus = consensus[:h, :w]; valid = valid[:h, :w]

    nidr_mask, n_nidr_pts = build_nidr_mask(nidr_p, prob_p)
    nidr_mask = nidr_mask[:h, :w]
    scars = consensus  # When NIDR is empty, consensus == Sentinel-scar raster on prob grid

    out = {"event": ev["name"], "n_nidr_points": int(n_nidr_pts),
           "nidr_mask_positive_pixels": int(nidr_mask.sum())}

    variants = {
        "A_sentinel_only":  scars,
        "B_nidr_only":      nidr_mask,
        "C_union":          scars | nidr_mask,
        "D_intersection":   scars & nidr_mask,
    }
    out["variants"] = {name: metrics(prob, lbl, valid) for name, lbl in variants.items()}

    # Disclosure: if NIDR has 0 points or 0 mask pixels, B/D are degenerate
    if n_nidr_pts == 0 or nidr_mask.sum() == 0:
        out["disclosure"] = (
            "NIDR layer empty at run time; variants B and D are degenerate. "
            "Only variant A (Sentinel-only) is reportable."
        )
    return out


def main():
    results = {ev["label"]: process(ev) for ev in EVENTS}

    json_path = OUT / "axis6_label_ablation.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # CSV — variant-event long table
    lines = ["event,n_nidr_points,variant,base_rate,n_positive,POD,FAR,CSI,F1,ROC_AUC,AP,ap_over_base_rate,scar_mean,non_scar_mean,separation"]
    for ev_label, ev in results.items():
        for vname, m in ev["variants"].items():
            if m.get("skipped"):
                lines.append(f'{ev["event"]},{ev["n_nidr_points"]},{vname},,,skipped:{m.get("reason","")},,,,,,,,,')
                continue
            lines.append(",".join([
                ev["event"], str(ev["n_nidr_points"]), vname,
                str(m["base_rate"]), str(m["n_positive"]),
                str(m["POD"]), str(m["FAR"]), str(m["CSI"]), str(m["F1"]),
                str(m["ROC_AUC"]), str(m["AP"]), str(m["ap_over_base_rate"]),
                str(m["scar_mean_prob"]), str(m["non_scar_mean_prob"]), str(m["separation"]),
            ]))
    csv_path = OUT / "axis6_label_ablation.csv"
    csv_path.write_text("\n".join(lines) + "\n")

    # Console summary
    for ev_label, ev in results.items():
        print(f"\n=== {ev['event']} — NIDR points: {ev['n_nidr_points']} (mask pixels: {ev['nidr_mask_positive_pixels']}) ===")
        for vname, m in ev["variants"].items():
            if m.get("skipped"):
                print(f"  {vname}: SKIPPED ({m.get('reason')})")
                continue
            print(f"  {vname:<18} base={m['base_rate']*100:.3f}%  ROC={m['ROC_AUC']}  AP={m['AP']}  "
                  f"sep={m['separation']:+.4f}  POD={m['POD']}")
        if "disclosure" in ev:
            print(f"  [disclosure] {ev['disclosure']}")

    print(f"\nSaved: {json_path}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
