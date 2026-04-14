#!/usr/bin/env python3
"""
Figure 3 — Event-typology contrast: prob-by-elevation + ROC comparison across scoring methods.

4-panel layout:
  (a) Pohang: prob by elevation decile (scar_rate overlay)
  (b) Yecheon: prob by elevation decile (scar_rate overlay)
  (c) Pohang: ROC curves — baseline / hillslope-masked / slope-alone / slope x relief
  (d) Yecheon: same 4 ROC curves

Annotations highlight the central finding (Yecheon slope-alone > SHALSTAB; Pohang
baseline SHALSTAB > alternatives).
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rasterio
from scipy.ndimage import maximum_filter
from sklearn.metrics import roc_curve, roc_auc_score


# Okabe-Ito colorblind-safe palette
COLORS = {
    "baseline":  "#0072B2",  # blue
    "hillslope": "#009E73",  # green
    "slope":     "#E69F00",  # orange
    "sxr":       "#CC79A7",  # pink
    "prob":      "#0072B2",
    "scar":      "#D55E00",  # vermilion
}


def horn_slope_deg(dem, px):
    padded = np.pad(dem, 1, mode="edge")
    dzdx = ((padded[:-2,2:]+2*padded[1:-1,2:]+padded[2:,2:])-(padded[:-2,:-2]+2*padded[1:-1,:-2]+padded[2:,:-2]))/(8*px)
    dzdy = ((padded[2:,:-2]+2*padded[2:,1:-1]+padded[2:,2:])-(padded[:-2,:-2]+2*padded[:-2,1:-1]+padded[:-2,2:]))/(8*px)
    return np.degrees(np.arctan(np.sqrt(dzdx**2+dzdy**2))).astype(np.float32)


def load(case_dir: Path):
    with rasterio.open(case_dir / "prob_unstable.tif") as ds:
        prob = ds.read(1).astype(np.float32)
        transform = ds.transform
        pixel_m = abs(transform.a)
    with rasterio.open(case_dir / "consensus_label.tif") as ds:
        label = ds.read(1) > 0
    with rasterio.open(case_dir / "dem_utm.tif") as ds:
        dem = ds.read(1).astype(np.float32)
    if dem.shape != prob.shape:
        from scipy.ndimage import zoom
        zy = prob.shape[0] / dem.shape[0]
        zx = prob.shape[1] / dem.shape[1]
        dem = zoom(dem, (zy, zx), order=1)[:prob.shape[0], :prob.shape[1]]
    slope = horn_slope_deg(dem, pixel_m)
    relief = (maximum_filter(dem, size=33, mode="nearest") - dem).astype(np.float32)
    return prob, label, dem, slope, relief


def elev_decile_stats(dem, prob, label, n=10):
    deciles = np.percentile(dem, np.linspace(0, 100, n + 1))
    rows = []
    for i in range(n):
        mask = (dem >= deciles[i]) & (dem < deciles[i + 1])
        if mask.sum() == 0:
            continue
        rows.append({
            "elev_lo": deciles[i], "elev_hi": deciles[i + 1],
            "elev_mid": (deciles[i] + deciles[i + 1]) / 2,
            "n": int(mask.sum()),
            "prob_mean": float(prob[mask].mean()),
            "scar_rate": float(label[mask].mean() * 100),
        })
    return rows


def main(out_path: Path):
    root = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/out")
    pohang = load(root / "pohang_2022")
    yecheon = load(root / "extreme_rainfall_2023")
    chuncheon = load(root / "chuncheon_2020")

    fig, axes = plt.subplots(2, 3, figsize=(20, 10.5))
    cases = [("Pohang 2022 (Typhoon Hinnamnor)", pohang),
             ("Yecheon 2023 (Monsoon, large AOI)", yecheon),
             ("Chuncheon 2020 (Monsoon, small AOI)", chuncheon)]

    # Row 1: elevation decile plots
    for col, (title, data) in enumerate(cases):
        prob, label, dem, slope, relief = data
        ax = axes[0, col]
        rows = elev_decile_stats(dem, prob, label, n=10)
        mids = [r["elev_mid"] for r in rows]
        prob_means = [r["prob_mean"] for r in rows]
        scar_rates = [r["scar_rate"] for r in rows]
        ax.plot(mids, prob_means, "o-", color=COLORS["prob"], label="Mean P(unstable)",
                linewidth=2, markersize=6)
        ax.set_ylabel("Mean P(unstable)", color=COLORS["prob"], fontsize=10)
        ax.set_xlabel("Elevation (m)", fontsize=10)
        ax.tick_params(axis="y", labelcolor=COLORS["prob"])
        ax.set_ylim(0, 1.02)
        ax2 = ax.twinx()
        ax2.plot(mids, scar_rates, "s-", color=COLORS["scar"], label="Scar rate (%)",
                 linewidth=2, markersize=6)
        ax2.set_ylabel("Scar rate (%)", color=COLORS["scar"], fontsize=10)
        ax2.tick_params(axis="y", labelcolor=COLORS["scar"])
        ax.set_title(f"({chr(97+col)}) {title} — prob vs scar rate by elevation decile",
                     fontsize=10.5)
        ax.grid(alpha=0.3)

        # Annotation: show inversion on Yecheon
        if col == 1:  # Yecheon
            ax.annotate("Rank inversion:\nprob falls, scar rate rises",
                        xy=(mids[-2], prob_means[-2]),
                        xytext=(mids[3], 0.85),
                        fontsize=9, color="black",
                        arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
                        bbox=dict(boxstyle="round,pad=0.3",
                                  facecolor="#FFF2CC", edgecolor="black", alpha=0.9))
        if col == 2:  # Chuncheon
            ax.annotate("Near-random:\nprob ~ flat, scar rate weak",
                        xy=(mids[len(mids)//2], prob_means[len(prob_means)//2]),
                        xytext=(mids[1], 0.25),
                        fontsize=9, color="black",
                        arrowprops=dict(arrowstyle="->", color="black", lw=1.2),
                        bbox=dict(boxstyle="round,pad=0.3",
                                  facecolor="#FFF2CC", edgecolor="black", alpha=0.9))

    # Row 2: ROC curves — 4 scorings
    for col, (title, data) in enumerate(cases):
        prob, label, dem, slope, relief = data
        ax = axes[1, col]
        hillslope = (slope > 10.0) & (relief > 30.0)
        prob_masked = np.where(hillslope, prob, 0.0)
        slope_score = slope / 90.0
        sr_score = slope_score * (relief / (relief.max() + 1e-9))

        l = label.ravel().astype(bool)
        scorings = [
            ("Baseline SHALSTAB", prob.ravel(),        COLORS["baseline"]),
            ("Hillslope-masked",   prob_masked.ravel(), COLORS["hillslope"]),
            ("Slope alone",        slope_score.ravel(), COLORS["slope"]),
            ("Slope x relief",     sr_score.ravel(),    COLORS["sxr"]),
        ]

        aucs = {}
        for name, score, color in scorings:
            try:
                fpr, tpr, _ = roc_curve(l, score)
                auc = roc_auc_score(l, score)
                aucs[name] = auc
                ax.plot(fpr, tpr, color=color, label=f"{name} (AUC = {auc:.3f})",
                        linewidth=2.0)
            except Exception:
                pass
        ax.plot([0, 1], [0, 1], "k--", alpha=0.5, linewidth=0.7)
        ax.set_xlabel("False Positive Rate", fontsize=10)
        ax.set_ylabel("True Positive Rate", fontsize=10)
        ax.set_title(f"({chr(100+col)}) {title} — ROC comparison across scoring methods",
                     fontsize=10.5)
        ax.legend(loc="lower right", fontsize=9.5, framealpha=0.95)
        ax.grid(alpha=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        # Headline annotation: show the winner
        if col == 0 and "Baseline SHALSTAB" in aucs:
            best = max(aucs, key=aucs.get)
            ax.text(0.02, 0.97, f"Best: {best} (AUC {aucs[best]:.3f})",
                    transform=ax.transAxes, fontsize=9.5, va="top",
                    bbox=dict(boxstyle="round,pad=0.3",
                              facecolor="#E8F5E8", edgecolor="black", alpha=0.95))
        if col == 1 and "Slope alone" in aucs and "Baseline SHALSTAB" in aucs:
            delta = aucs["Slope alone"] - aucs["Baseline SHALSTAB"]
            ax.text(0.02, 0.97,
                    f"Slope alone (AUC {aucs['Slope alone']:.3f}) beats\n"
                    f"Baseline SHALSTAB (AUC {aucs['Baseline SHALSTAB']:.3f}) by {delta:+.3f}",
                    transform=ax.transAxes, fontsize=9.5, va="top",
                    bbox=dict(boxstyle="round,pad=0.3",
                              facecolor="#E8F5E8", edgecolor="black", alpha=0.95))
        if col == 2 and "Baseline SHALSTAB" in aucs:
            ax.text(0.02, 0.97,
                    f"Baseline SHALSTAB AUC {aucs['Baseline SHALSTAB']:.3f}\n"
                    f"Near-random. Monsoon-side of borderline\n"
                    f"(small AOI did not rescue SHALSTAB).",
                    transform=ax.transAxes, fontsize=9.5, va="top",
                    bbox=dict(boxstyle="round,pad=0.3",
                              facecolor="#FFF2CC", edgecolor="black", alpha=0.95))

    fig.suptitle("LandslideKR — Event-typology contrast: SHALSTAB vs hillslope-masked vs slope alone vs slope x relief",
                 fontsize=12.5, y=1.00)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    out = Path("/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/figures/fig3_event_contrast.png")
    main(out)
