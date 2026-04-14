#!/usr/bin/env python3
"""
Axis 3 — Stochastic repeatability.

Re-runs the SHALSTAB Monte Carlo ensemble for each event with N different
top-level RNG seeds, holding all other inputs (DEM, topo, lithology, rainfall,
Sentinel-scar reference label) constant. Reports CV% on key metrics.

Output:
  - analysis-output/axis3_repeatability.json
  - analysis-output/axis3_repeatability.csv

Default seeds: [42, 7, 19, 113, 271] (5 reps; n=5 gives meaningful variance for
CV% but is not as tight as n=20. We deliberately ship the smaller ensemble per
HP Round 6 C: "Axis 3 first" is more important than n=20-perfectionism.)
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import numpy as np
import rasterio
from sklearn.metrics import roc_auc_score, average_precision_score

# Project import path
PROJECT = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting")
sys.path.insert(0, str(PROJECT))

from landslide_kr.models.ensemble import run_ensemble
from landslide_kr.preprocess.topo import compute_topo

OUT_DIR = PROJECT / "analysis-output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EVENTS = [
    # event_window matches cases/<event>/config.json::event_window
    {"name": "Pohang 2022",     "dir": PROJECT / "out" / "pohang_2022",           "label": "pohang",    "window_start": "2022-09-05", "window_end": "2022-09-07"},
    {"name": "Yecheon 2023",    "dir": PROJECT / "out" / "extreme_rainfall_2023", "label": "yecheon",   "window_start": "2023-07-13", "window_end": "2023-07-18"},
    {"name": "Chuncheon 2020",  "dir": PROJECT / "out" / "chuncheon_2020",        "label": "chuncheon", "window_start": "2020-08-01", "window_end": "2020-08-08"},
]

SEEDS = [42, 7, 19, 113, 271]
N_REALIZATIONS = 100


def load_inputs(case_dir: Path, window_start: str, window_end: str):
    """Load DEM-derived topo + cached rain raster + reference label.

    Rainfall conversion mm/event → m/s uses the same per-event window the main
    pipeline (orchestrator.py:362-364) uses, computed from window_start/end
    rather than a 7-day proxy. The 7-day proxy in the v1 of this script was a
    Gemini-flagged bug because it left Pohang's 3-day typhoon and Yecheon's
    5-day monsoon under the same denominator as Chuncheon's 8-day window,
    suppressing recharge rate on the typhoon event and shifting absolute
    ROC-AUC away from §3.1 in a way that does not represent stochastic
    repeatability.
    """
    from datetime import datetime
    delta = datetime.fromisoformat(window_end) - datetime.fromisoformat(window_start)
    event_seconds = max(delta.total_seconds(), 3600.0)

    with rasterio.open(case_dir / "dem_utm.tif") as ds:
        dem = ds.read(1).astype(float)
    topo = compute_topo(case_dir / "dem_utm.tif")

    # Rainfall: read rain.tif, resample to topo grid if needed
    with rasterio.open(case_dir / "rain.tif") as ds:
        rain_mm = ds.read(1).astype(float)
    # crude resample by repeating to topo shape
    if rain_mm.shape != topo.slope_rad.shape:
        from scipy.ndimage import zoom
        zy = topo.slope_rad.shape[0] / rain_mm.shape[0]
        zx = topo.slope_rad.shape[1] / rain_mm.shape[1]
        rain_mm = zoom(rain_mm, (zy, zx), order=1)[
            : topo.slope_rad.shape[0], : topo.slope_rad.shape[1]
        ]
    # Per-event recharge rate (matches orchestrator.step_run_model)
    rain_m_per_s = (rain_mm / 1000.0) / event_seconds
    rain_m_per_s = rain_m_per_s.astype(np.float32)

    # Reference label
    with rasterio.open(case_dir / "consensus_label.tif") as ds:
        label = ds.read(1) > 0
    # Align consensus label to topo shape
    if label.shape != topo.slope_rad.shape:
        h = min(label.shape[0], topo.slope_rad.shape[0])
        w = min(label.shape[1], topo.slope_rad.shape[1])
        label = label[:h, :w]
    return topo, rain_m_per_s, label


def run_one(case_dir: Path, seed: int, window_start: str, window_end: str):
    topo, rain_m_per_s, label = load_inputs(case_dir, window_start, window_end)
    # Use single "default" lithology to keep this script self-contained;
    # the per-pixel lithology array is reproduced inside the production run.
    res = run_ensemble(
        slope_rad=topo.slope_rad,
        upslope_area_m2=topo.upslope_area_m2,
        contour_length_m=topo.contour_length_m,
        rainfall_m_per_s=rain_m_per_s,
        lithology_class="default",
        n_realizations=N_REALIZATIONS,
        seed=seed,
    )
    prob = res.prob_unstable.astype(float)

    # Align prob to label (defensive)
    h = min(prob.shape[0], label.shape[0])
    w = min(prob.shape[1], label.shape[1])
    prob = prob[:h, :w]
    lab_a = label[:h, :w]

    valid = np.isfinite(prob) & (prob >= 0)
    y = lab_a[valid].astype(bool)
    s = prob[valid]

    if y.sum() == 0 or (~y).sum() == 0:
        return {"skipped": True, "reason": "degenerate label"}

    pred = (s >= 0.5)
    TP = int((pred & y).sum())
    FP = int((pred & ~y).sum())
    FN = int((~pred & y).sum())
    TN = int((~pred & ~y).sum())
    POD = TP / max(TP + FN, 1)
    precision = TP / max(TP + FP, 1)
    f1 = 2 * precision * POD / max(precision + POD, 1e-12)
    roc = float(roc_auc_score(y, s))
    ap = float(average_precision_score(y, s))
    scar_mean = float(s[y].mean())
    non_scar_mean = float(s[~y].mean())

    return {
        "seed": seed,
        "POD": POD,
        "precision": precision,
        "F1": f1,
        "ROC_AUC": roc,
        "AP": ap,
        "scar_mean": scar_mean,
        "non_scar_mean": non_scar_mean,
        "separation": scar_mean - non_scar_mean,
        "n_predicted_positive": int(pred.sum()),
    }


def cv_pct(values):
    a = np.asarray(values, dtype=float)
    if a.size == 0 or a.mean() == 0:
        return None
    return float(100.0 * a.std(ddof=1) / abs(a.mean()))


def main():
    all_results = {}
    for ev in EVENTS:
        print(f"\n=== {ev['name']} ===")
        runs = []
        for s in SEEDS:
            print(f"  seed={s} ...", end=" ", flush=True)
            r = run_one(ev["dir"], s, ev["window_start"], ev["window_end"])
            runs.append(r)
            if r.get("skipped"):
                print(f"SKIPPED ({r['reason']})")
            else:
                print(f"ROC={r['ROC_AUC']:.4f} sep={r['separation']:+.4f} POD={r['POD']:.3f}")

        # Aggregate
        valid_runs = [r for r in runs if not r.get("skipped")]
        agg = {}
        for metric in ["POD", "precision", "F1", "ROC_AUC", "AP", "separation", "scar_mean", "non_scar_mean"]:
            vals = [r[metric] for r in valid_runs]
            if not vals:
                continue
            arr = np.asarray(vals, dtype=float)
            agg[metric] = {
                "values": [round(v, 6) for v in vals],
                "mean": round(float(arr.mean()), 6),
                "std": round(float(arr.std(ddof=1)) if arr.size > 1 else 0.0, 6),
                "cv_pct": round(cv_pct(vals), 3) if cv_pct(vals) is not None else None,
                "min": round(float(arr.min()), 6),
                "max": round(float(arr.max()), 6),
            }
        all_results[ev["label"]] = {
            "event": ev["name"],
            "seeds": SEEDS,
            "n_realizations_per_seed": N_REALIZATIONS,
            "n_seeds": len(SEEDS),
            "runs": runs,
            "aggregate": agg,
        }

        # Console summary
        print(f"  Aggregate (n={len(valid_runs)} seeds):")
        for metric in ["ROC_AUC", "separation", "POD", "AP"]:
            if metric in agg:
                a = agg[metric]
                print(f"    {metric:<12} mean={a['mean']:+.4f}  std={a['std']:.4f}  CV={a['cv_pct']}%  range=[{a['min']:.4f}, {a['max']:.4f}]")

    json_path = OUT_DIR / "axis3_repeatability.json"
    json_path.write_text(json.dumps(all_results, indent=2))

    # CSV
    lines = ["event,seed,POD,precision,F1,ROC_AUC,AP,scar_mean,non_scar_mean,separation"]
    for ev_label, ev in all_results.items():
        for r in ev["runs"]:
            if r.get("skipped"):
                continue
            lines.append(",".join([
                ev["event"], str(r["seed"]),
                f"{r['POD']:.4f}", f"{r['precision']:.4f}", f"{r['F1']:.4f}",
                f"{r['ROC_AUC']:.4f}", f"{r['AP']:.4f}",
                f"{r['scar_mean']:.4f}", f"{r['non_scar_mean']:.4f}", f"{r['separation']:+.4f}",
            ]))
    csv_path = OUT_DIR / "axis3_repeatability.csv"
    csv_path.write_text("\n".join(lines) + "\n")

    print(f"\nSaved: {json_path}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
