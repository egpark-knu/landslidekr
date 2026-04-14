#!/usr/bin/env python3
"""
Probability calibration via isotonic regression (closes §5.8).

Diagnoses the bimodal Monte Carlo probability distribution observed in §3.5
(top-1/5/10 % quantile filters collapsing to the p = 1.0 saturated tier) by
fitting an isotonic regression of the raw MC probability against the Sentinel-2
scar reference label, and reports whether calibration changes the top-quantile
operational result.

Per-event isotonic fit (no cross-fold; we report fit-on-fit ROC-AUC for
diagnostic purposes only — the calibration is intended to spread the saturated
tail and recover top-quantile resolution, not to claim out-of-sample skill).

Output:
    - analysis-output/calibration_isotonic.json
    - analysis-output/calibration_isotonic.csv
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import numpy as np
import rasterio
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score

PROJECT = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting")
sys.path.insert(0, str(PROJECT))

OUT_DIR = PROJECT / "analysis-output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EVENTS = [
    {"name": "Pohang 2022", "dir": PROJECT / "out" / "pohang_2022", "label": "pohang"},
    {"name": "Yecheon 2023", "dir": PROJECT / "out" / "extreme_rainfall_2023", "label": "yecheon"},
    {"name": "Chuncheon 2020", "dir": PROJECT / "out" / "chuncheon_2020", "label": "chuncheon"},
]


def calibrate(case_dir: Path):
    with rasterio.open(case_dir / "prob_unstable.tif") as ds:
        prob = ds.read(1)
    with rasterio.open(case_dir / "consensus_label.tif") as ds:
        label_raw = ds.read(1) > 0
    # align shapes
    h = min(prob.shape[0], label_raw.shape[0])
    w = min(prob.shape[1], label_raw.shape[1])
    prob = prob[:h, :w]
    label = label_raw[:h, :w]
    valid = np.isfinite(prob)
    p = prob[valid].ravel().astype(np.float64)
    y = label[valid].ravel().astype(int)

    # Pre-calibration metrics
    auc_pre = float(roc_auc_score(y, p))
    sat_top_p1 = float((p >= 0.99).mean())
    # Top-quantile resolution: how many distinct values in the top 10 %?
    top10_threshold = np.quantile(p, 0.90)
    top10_mask = p >= top10_threshold
    n_top10 = int(top10_mask.sum())
    n_distinct_top10 = int(np.unique(p[top10_mask]).size)
    pre_top10_recall = float(y[top10_mask].sum() / y.sum())

    # Isotonic regression — monotonic non-decreasing fit
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(p, y)
    p_cal = iso.predict(p)
    auc_post = float(roc_auc_score(y, p_cal))

    # Calibrated top-quantile resolution
    top10_threshold_cal = np.quantile(p_cal, 0.90)
    top10_mask_cal = p_cal >= top10_threshold_cal
    n_top10_cal = int(top10_mask_cal.sum())
    n_distinct_top10_cal = int(np.unique(p_cal[top10_mask_cal]).size)
    post_top10_recall = float(y[top10_mask_cal].sum() / y.sum())

    # Mean-separation
    sep_pre = float(p[y.astype(bool)].mean() - p[~y.astype(bool)].mean())
    sep_post = float(p_cal[y.astype(bool)].mean() - p_cal[~y.astype(bool)].mean())

    return {
        "n_pixels": int(p.size),
        "n_positives": int(y.sum()),
        "base_rate": float(y.mean()),
        "p_saturation_at_1": sat_top_p1,
        "ROC_AUC_pre_calibration": auc_pre,
        "ROC_AUC_post_calibration": auc_post,
        "separation_pre": sep_pre,
        "separation_post": sep_post,
        "top10pct_pre": {"n_pixels": n_top10, "n_distinct_scores": n_distinct_top10, "recall": pre_top10_recall},
        "top10pct_post": {"n_pixels": n_top10_cal, "n_distinct_scores": n_distinct_top10_cal, "recall": post_top10_recall},
        "calibration_resolution_gain": n_distinct_top10_cal - n_distinct_top10,
    }


def main():
    out = {}
    for ev in EVENTS:
        print(f"=== {ev['name']} ===")
        r = calibrate(ev["dir"])
        out[ev["label"]] = {"name": ev["name"], **r}
        print(f"  Saturation at p≈1: {r['p_saturation_at_1']*100:.1f}%")
        print(f"  ROC-AUC pre→post: {r['ROC_AUC_pre_calibration']:.4f} → {r['ROC_AUC_post_calibration']:.4f}")
        print(f"  Separation pre→post: {r['separation_pre']:+.4f} → {r['separation_post']:+.4f}")
        print(f"  Top-10% distinct-score gain: {r['top10pct_pre']['n_distinct_scores']} → {r['top10pct_post']['n_distinct_scores']} (Δ {r['calibration_resolution_gain']:+d})")
        print(f"  Top-10% recall pre→post: {r['top10pct_pre']['recall']:.3f} → {r['top10pct_post']['recall']:.3f}")
        print()

    with open(OUT_DIR / "calibration_isotonic.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {OUT_DIR / 'calibration_isotonic.json'}")

    with open(OUT_DIR / "calibration_isotonic.csv", "w") as f:
        f.write("event,base_rate,saturation_p1,ROC_AUC_pre,ROC_AUC_post,sep_pre,sep_post,top10_distinct_pre,top10_distinct_post,top10_recall_pre,top10_recall_post\n")
        for ev in EVENTS:
            r = out[ev["label"]]
            f.write(f"{ev['label']},{r['base_rate']:.6f},{r['p_saturation_at_1']:.4f},{r['ROC_AUC_pre_calibration']:.4f},{r['ROC_AUC_post_calibration']:.4f},{r['separation_pre']:+.4f},{r['separation_post']:+.4f},{r['top10pct_pre']['n_distinct_scores']},{r['top10pct_post']['n_distinct_scores']},{r['top10pct_pre']['recall']:.3f},{r['top10pct_post']['recall']:.3f}\n")
    print(f"Saved: {OUT_DIR / 'calibration_isotonic.csv'}")


if __name__ == "__main__":
    main()
