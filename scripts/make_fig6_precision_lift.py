#!/usr/bin/env python3
"""
Figure 6 — Precision lift over base rate vs kept-fraction.

Scatter with filter labels: each (event, filter) combination is one point.
X: kept_fraction (log).  Y: precision lift (log-ish).  Marker: event.
Reference lines: lift = 1.0 (random), lift-isoquants per event.

Highlights:
  - Yecheon F7 (slope > 20°): best single-knob lift (1.42x, POD 0.268)
  - Pohang F5/F6: best lift (1.56x) but POD collapses to 0.065
  - F0 baselines: Pohang 1.31x / Yecheon 0.88x (sub-random, rank inversion)
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SRC = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/analysis-output/far_filter_results.json")
OUT = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/figures/fig6_precision_lift.png")

EVENT_META = {
    "pohang":    {"name": "Pohang 2022 (Typhoon)",     "marker": "o", "color": "#0072B2"},
    "yecheon":   {"name": "Yecheon 2023 (Monsoon)",    "marker": "s", "color": "#D55E00"},
    "chuncheon": {"name": "Chuncheon 2020 (Monsoon)",  "marker": "^", "color": "#009E73"},
}
# F0..F8 order
FKEY = ["F0_baseline","F1_hillslope","F2_top10pct","F3_top5pct","F4_top1pct",
        "F5_hillslope_top10","F6_hillslope_top5","F7_slope20","F8_compound"]
FLABEL = {
    "F0_baseline":"F0","F1_hillslope":"F1","F2_top10pct":"F2","F3_top5pct":"F3",
    "F4_top1pct":"F4","F5_hillslope_top10":"F5","F6_hillslope_top5":"F6",
    "F7_slope20":"F7","F8_compound":"F8",
}


def main():
    data = json.loads(SRC.read_text())
    fig, ax = plt.subplots(1, 1, figsize=(11, 7))

    # Reference line: lift = 1.0
    ax.axhline(1.0, color="black", linestyle="--", linewidth=0.9, alpha=0.6)

    for ek, em in EVENT_META.items():
        ev = data[ek]
        base_rate = ev["n_actual_positive"] / ev["n_valid_pixels"]
        xs, ys, labels = [], [], []
        for fk in FKEY:
            r = ev["filters"][fk]
            if r["kept_fraction"] <= 0:
                continue
            lift = r["precision"] / base_rate if base_rate > 0 else 0
            xs.append(r["kept_fraction"] * 100.0)  # percent
            ys.append(lift)
            labels.append(FLABEL[fk])

        ax.scatter(xs, ys, marker=em["marker"], s=120, facecolor=em["color"],
                   edgecolor="black", linewidths=1.0, alpha=0.9,
                   label=f"{em['name']} (base rate {base_rate*100:.2f}%)",
                   zorder=3)

        # Annotate each point with its filter code
        for xi, yi, lbl in zip(xs, ys, labels):
            ax.annotate(lbl, (xi, yi),
                        xytext=(xi + 1.2, yi + 0.02),
                        fontsize=8.5, color=em["color"], weight="bold")

    # Headline callouts — 3-event
    callouts = [
        ("yecheon", "F7_slope20",
         "F7: slope > 20°\nYecheon best lift 1.42×\n(POD 0.268)",
         (18.89, 1.42), (32, 1.58)),
        ("pohang",  "F5_hillslope_top10",
         "F5/F6: F1 ∩ top-q\nPohang best lift 1.56×\n(POD 0.065)",
         (4.15, 1.56), (14, 1.70)),
        ("yecheon", "F0_baseline",
         "F0 Yecheon = 0.88×\n(sub-random: rank inversion)",
         (55.18, 0.88), (48, 0.58)),
        ("chuncheon", "F7_slope20",
         "F7 Chuncheon = 1.11×\n(monsoon, small AOI, modest lift)",
         (38.44, 1.11), (42, 1.35)),
        ("chuncheon", "F0_baseline",
         "F0 Chuncheon = 0.98×\n(random; ROC 0.499, sep +0.006)",
         (72.82, 0.98), (55, 0.78)),
    ]
    for ek, fk, note, xy, xytext in callouts:
        ax.annotate(
            note, xy=xy, xytext=xytext,
            fontsize=9.0, color="black", ha="left",
            arrowprops=dict(arrowstyle="->", color="black", lw=1.0, alpha=0.75),
            bbox=dict(boxstyle="round,pad=0.35",
                      facecolor="#FFF2CC", edgecolor="black", alpha=0.95),
        )

    ax.set_xlabel("Kept-fraction (%) — share of AOI flagged predicted-unstable", fontsize=11)
    ax.set_ylabel("Precision lift over base rate  (precision ÷ base_rate)", fontsize=11)
    ax.set_title("LandslideKR — Post-hoc FAR filters: precision lift vs kept-fraction\n"
                 "(filter codes per Table 6; F0 baseline → F8 compound)",
                 fontsize=12)
    ax.set_xlim(0, 75)
    ax.set_ylim(0.40, 1.80)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.95)

    # Zone shading
    ax.axhspan(0.40, 1.00, facecolor="#F5E0DC", alpha=0.30, zorder=1)
    ax.axhspan(1.00, 1.80, facecolor="#E0F0E0", alpha=0.30, zorder=1)
    ax.text(72, 0.48, "harmful\n(lift < 1.0)", fontsize=9, color="#8B0000",
            ha="right", va="bottom", style="italic", zorder=2)
    ax.text(72, 1.73, "beneficial\n(lift > 1.0)", fontsize=9, color="#006400",
            ha="right", va="top", style="italic", zorder=2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT, dpi=300, bbox_inches="tight")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
