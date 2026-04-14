#!/usr/bin/env python3
"""
Apply post-hoc false-alarm-reduction filters to LandslideKR baseline predictions.

For each of 2 events (Pohang 2022, Yecheon 2023) and 9 filter configurations,
compute POD, FAR, CSI, F1, Precision, Recall, and kept-pixel fraction.

Baseline binary prediction is `prediction.tif` (prob >= 0.5).
FAR filters are applied as logical AND: keep_pixel ⇐ baseline_unstable ∧ filter_pass.

Filters:
  F0: baseline (no filter)
  F1: hillslope mask (slope > 10° ∩ local relief > 30 m within 33-px window)
  F2: prob top-10% (per-event quantile)
  F3: prob top-5%
  F4: prob top-1%
  F5: F1 ∩ F2  (hillslope + top-10%)
  F6: F1 ∩ F3  (hillslope + top-5%)
  F7: slope > 20°
  F8: F1 ∩ slope>20° ∩ prob>0.9

Outputs:
  - analysis-output/far_filter_results.json
  - analysis-output/far_filter_results.csv
  - analysis-output/figures/figure-01-far-filter-comparison.png
"""
from pathlib import Path
import json
import numpy as np
import rasterio
from scipy.ndimage import maximum_filter, minimum_filter
import matplotlib.pyplot as plt

ROOT = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting")
OUT = ROOT / "analysis-output"
FIG = OUT / "figures"

EVENTS = [
    {"name": "Pohang 2022", "dir": ROOT / "out" / "pohang_2022", "label": "pohang"},
    {"name": "Yecheon 2023", "dir": ROOT / "out" / "extreme_rainfall_2023", "label": "yecheon"},
    {"name": "Chuncheon 2020", "dir": ROOT / "out" / "chuncheon_2020", "label": "chuncheon"},
]

FILTERS_ORDER = [
    "F0_baseline",
    "F1_hillslope",
    "F2_top10pct",
    "F3_top5pct",
    "F4_top1pct",
    "F5_hillslope_top10",
    "F6_hillslope_top5",
    "F7_slope20",
    "F8_compound",
]
FILTERS_LABEL = {
    "F0_baseline": "F0: baseline",
    "F1_hillslope": "F1: hillslope",
    "F2_top10pct": "F2: prob top-10%",
    "F3_top5pct": "F3: prob top-5%",
    "F4_top1pct": "F4: prob top-1%",
    "F5_hillslope_top10": "F5: F1 ∩ top-10%",
    "F6_hillslope_top5": "F6: F1 ∩ top-5%",
    "F7_slope20": "F7: slope > 20°",
    "F8_compound": "F8: F1 ∩ slope>20° ∩ prob>0.9",
}


def compute_slope_and_relief(dem_path: Path, window_px: int = 33):
    """Horn slope (degrees) + local relief (max-min in window) from DEM."""
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(float)
        res = src.res  # (xres, yres) in meters (UTM)
    nodata_mask = ~np.isfinite(dem) | (dem <= -1e6)
    dem_clean = np.where(nodata_mask, np.nan, dem)

    # Horn slope — 3x3 kernel
    dy, dx = np.gradient(dem_clean, res[1], res[0])
    slope_rad = np.arctan(np.hypot(dx, dy))
    slope_deg = np.degrees(slope_rad)

    # Local relief in a square window
    rel = maximum_filter(np.nan_to_num(dem_clean, nan=-1e9), size=window_px) - \
          minimum_filter(np.nan_to_num(dem_clean, nan=1e9), size=window_px)
    rel = np.where(nodata_mask, np.nan, rel)

    return slope_deg, rel


def metrics(pred: np.ndarray, label: np.ndarray, valid: np.ndarray) -> dict:
    """Compute POD, FAR, CSI, F1, precision, recall, kept_fraction."""
    v = valid & np.isfinite(pred) & np.isfinite(label)
    p = pred[v].astype(bool)
    l = label[v].astype(bool)
    TP = int(np.sum(p & l))
    FP = int(np.sum(p & ~l))
    FN = int(np.sum(~p & l))
    TN = int(np.sum(~p & ~l))
    N  = TP + FP + FN + TN
    P  = TP + FN  # actual positives
    pred_pos = TP + FP
    POD = TP / P if P > 0 else 0.0
    FAR = FP / pred_pos if pred_pos > 0 else 0.0
    CSI = TP / (TP + FP + FN) if (TP + FP + FN) > 0 else 0.0
    Pr  = TP / pred_pos if pred_pos > 0 else 0.0
    F1  = 2 * Pr * POD / (Pr + POD) if (Pr + POD) > 0 else 0.0
    kept_fraction = pred_pos / N if N > 0 else 0.0
    return {
        "TP": TP, "FP": FP, "FN": FN, "TN": TN,
        "N": N, "actual_pos": P, "pred_pos": pred_pos,
        "POD": POD, "FAR": FAR, "CSI": CSI, "F1": F1,
        "precision": Pr, "recall": POD,
        "kept_fraction": kept_fraction,
    }


def build_filters(prob: np.ndarray, slope: np.ndarray, relief: np.ndarray, valid: np.ndarray):
    """Return dict filter_name -> boolean mask (True = pass)."""
    # Quantile thresholds on valid pixels only
    valid_prob = prob[valid & np.isfinite(prob)]
    if valid_prob.size == 0:
        raise RuntimeError("No valid probability pixels.")
    q90 = float(np.quantile(valid_prob, 0.90))
    q95 = float(np.quantile(valid_prob, 0.95))
    q99 = float(np.quantile(valid_prob, 0.99))

    hillslope = (slope > 10.0) & (relief > 30.0)
    slope20   = (slope > 20.0)
    top10     = (prob >= q90)
    top5      = (prob >= q95)
    top1      = (prob >= q99)
    baseline  = (prob >= 0.5)  # binary prediction

    return {
        "F0_baseline":        baseline,
        "F1_hillslope":       baseline & hillslope,
        "F2_top10pct":        top10,
        "F3_top5pct":         top5,
        "F4_top1pct":         top1,
        "F5_hillslope_top10": top10 & hillslope,
        "F6_hillslope_top5":  top5  & hillslope,
        "F7_slope20":         baseline & slope20,
        "F8_compound":        (prob >= 0.9) & hillslope & slope20,
    }, {"q90": q90, "q95": q95, "q99": q99}


def process_event(ev: dict) -> dict:
    prob_path  = ev["dir"] / "prob_unstable.tif"
    label_path = ev["dir"] / "consensus_label.tif"
    dem_path   = ev["dir"] / "dem_utm.tif"

    with rasterio.open(prob_path)  as src: prob  = src.read(1).astype(float)
    with rasterio.open(label_path) as src: label = src.read(1).astype(bool)
    slope, relief = compute_slope_and_relief(dem_path, window_px=33)

    # Align shapes
    h = min(prob.shape[0], label.shape[0], slope.shape[0])
    w = min(prob.shape[1], label.shape[1], slope.shape[1])
    prob   = prob[:h, :w]
    label  = label[:h, :w]
    slope  = slope[:h, :w]
    relief = relief[:h, :w]

    valid = (
        np.isfinite(prob) & (prob >= 0) &
        np.isfinite(slope) & np.isfinite(relief)
    )

    filters, quantiles = build_filters(prob, slope, relief, valid)
    results = {}
    for fname in FILTERS_ORDER:
        mask = filters[fname]
        m = metrics(mask, label, valid)
        m["label"] = FILTERS_LABEL[fname]
        results[fname] = m

    return {
        "event": ev["name"],
        "quantile_thresholds": quantiles,
        "n_valid_pixels": int(np.sum(valid)),
        "n_actual_positive": int(np.sum(valid & label)),
        "filters": results,
    }


def plot_figure(all_results, out_path: Path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    metrics_to_plot = ["POD", "FAR", "CSI", "F1", "precision"]

    for ax, (ev_label, ev_data) in zip(axes, all_results.items()):
        filters = ev_data["filters"]
        x = np.arange(len(FILTERS_ORDER))
        width = 0.16
        colors = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd"]
        for i, m in enumerate(metrics_to_plot):
            vals = [filters[f][m] for f in FILTERS_ORDER]
            ax.bar(x + (i - 2) * width, vals, width, label=m, color=colors[i])
        ax.set_xticks(x)
        ax.set_xticklabels([FILTERS_LABEL[f].split(": ")[1] for f in FILTERS_ORDER],
                          rotation=30, ha="right", fontsize=9)
        ax.set_ylim(0, 1.02)
        ax.set_ylabel("Metric value")
        ax.set_title(f"{ev_data['event']} — FAR reduction filter comparison")
        ax.grid(axis="y", alpha=0.3)
        ax.legend(ncol=5, loc="upper right", fontsize=8)

    fig.suptitle("LandslideKR — Post-hoc FAR reduction (binary thresholded at prob >= 0.5 unless filter says otherwise)",
                 fontsize=11)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_csv(all_results, out_path: Path):
    lines = ["event,filter,POD,FAR,CSI,F1,precision,kept_fraction,TP,FP,FN,TN"]
    for ev_label, ev_data in all_results.items():
        for fname in FILTERS_ORDER:
            r = ev_data["filters"][fname]
            lines.append(
                f'{ev_data["event"]},{FILTERS_LABEL[fname]},'
                f'{r["POD"]:.4f},{r["FAR"]:.4f},{r["CSI"]:.4f},{r["F1"]:.4f},'
                f'{r["precision"]:.4f},{r["kept_fraction"]:.6f},'
                f'{r["TP"]},{r["FP"]},{r["FN"]},{r["TN"]}'
            )
    out_path.write_text("\n".join(lines) + "\n")


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    all_results = {}
    for ev in EVENTS:
        print(f"Processing {ev['name']}...")
        all_results[ev["label"]] = process_event(ev)

    json_path = OUT / "far_filter_results.json"
    csv_path  = OUT / "far_filter_results.csv"
    fig_path  = FIG / "figure-01-far-filter-comparison.png"

    json_path.write_text(json.dumps(all_results, indent=2))
    write_csv(all_results, csv_path)
    plot_figure(all_results, fig_path)

    # Console summary
    for ev_label, ev_data in all_results.items():
        print(f"\n=== {ev_data['event']} ===")
        print(f"Valid pixels: {ev_data['n_valid_pixels']:,}  |  "
              f"Actual positives: {ev_data['n_actual_positive']:,}  "
              f"({ev_data['n_actual_positive']/max(1,ev_data['n_valid_pixels'])*100:.2f}%)")
        print(f"Quantile thresholds: {ev_data['quantile_thresholds']}")
        print(f"{'Filter':<22} {'POD':>6} {'FAR':>6} {'CSI':>6} {'F1':>6} {'Prec':>6} {'kept%':>7}")
        for fname in FILTERS_ORDER:
            r = ev_data["filters"][fname]
            print(f"{FILTERS_LABEL[fname]:<22} "
                  f"{r['POD']:.3f}  {r['FAR']:.3f}  {r['CSI']:.3f}  "
                  f"{r['F1']:.3f}  {r['precision']:.3f}  {r['kept_fraction']*100:.3f}")

    print(f"\nSaved: {json_path}")
    print(f"Saved: {csv_path}")
    print(f"Saved: {fig_path}")


if __name__ == "__main__":
    main()
