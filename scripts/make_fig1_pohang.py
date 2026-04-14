#!/usr/bin/env python3
"""
Figure 1 — Pohang 2022 LandslideKR prob_unstable map with Sentinel-2 scar overlay.

Multipanel layout:
  (a) Instability probability (prob_unstable.tif, continuous colormap)
  (b) Binary unstable mask at p>=0.5 + scar points overlay
  (c) Scar vs non-scar probability distribution (histograms)

Output: figures/fig1_pohang_2022.png (300 DPI)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import rasterio


def _reproject_to_latlon(case_dir: Path, src_name: str):
    """Reproject a UTM raster to EPSG:4326 for lat/lon display."""
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    with rasterio.open(case_dir / src_name) as src:
        dst_crs = "EPSG:4326"
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        dst_data = np.zeros((height, width), dtype=src.read(1).dtype)
        reproject(
            source=rasterio.band(src, 1),
            destination=dst_data,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=transform, dst_crs=dst_crs,
            resampling=Resampling.nearest,
        )
        left, top = transform * (0, 0)
        right, bottom = transform * (width, height)
        return dst_data, (left, right, bottom, top)


def main(case_dir: Path, out_path: Path) -> None:
    # Reproject to lat/lon for display (per user 2026-04-14 지시)
    prob, (lon_min, lon_max, lat_min, lat_max) = _reproject_to_latlon(case_dir, "prob_unstable.tif")
    label_raw, _ = _reproject_to_latlon(case_dir, "consensus_label.tif")
    label = label_raw > 0
    extent = [lon_min, lon_max, lat_min, lat_max]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5),
                              gridspec_kw={"width_ratios": [1.1, 1.1, 1]})

    # Panel (a) — continuous prob
    ax = axes[0]
    im = ax.imshow(prob, cmap="RdYlBu_r", vmin=0, vmax=1, extent=extent, aspect="auto")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label("P(unstable)", rotation=270, labelpad=14)
    ax.set_title("(a) Instability probability\n(SINMAP-style MC, n=100)", fontsize=11)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.tick_params(labelsize=8)

    # Panel (b) — binary mask + scar overlay (with legend)
    ax = axes[1]
    mask = (prob >= 0.5).astype(np.uint8)
    ax.imshow(mask, cmap="Greys", vmin=0, vmax=1, extent=extent, alpha=0.6, aspect="auto")
    # Overlay scars in red (dilate for visibility)
    from scipy.ndimage import binary_dilation
    try:
        scar_dil = binary_dilation(label, iterations=2)
    except Exception:
        scar_dil = label
    scar_mask = np.full_like(prob, np.nan, dtype=np.float32)
    scar_mask[scar_dil] = 1.0
    ax.imshow(scar_mask, cmap="Reds", vmin=0, vmax=1, extent=extent, aspect="auto")
    # Legend via proxy patches
    from matplotlib.patches import Patch
    legend_items = [
        Patch(facecolor="dimgrey", edgecolor="k", label="Predicted unstable (p>=0.5)"),
        Patch(facecolor="white",    edgecolor="k", label="Predicted stable"),
        Patch(facecolor="firebrick", edgecolor="k", label="Sentinel-2 scar (dilated 2 px)"),
    ]
    ax.legend(handles=legend_items, loc="upper right", fontsize=8, framealpha=0.85)
    ax.set_title("(b) Binary prediction + Sentinel-2 scar", fontsize=11)
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.tick_params(labelsize=8)

    # Panel (c) — probability distribution by class
    ax = axes[2]
    scar_probs = prob[label]
    non_scar_probs = prob[~label]
    bins = np.linspace(0, 1, 41)
    ax.hist(non_scar_probs, bins=bins, alpha=0.5, color="steelblue",
            density=True, label=f"non-scar (n={len(non_scar_probs):,})")
    ax.hist(scar_probs, bins=bins, alpha=0.7, color="firebrick",
            density=True, label=f"scar (n={len(scar_probs):,})")
    ax.axvline(np.mean(scar_probs), color="firebrick", linestyle="--", linewidth=1)
    ax.axvline(np.mean(non_scar_probs), color="steelblue", linestyle="--", linewidth=1)
    ax.set_xlabel("P(unstable)")
    ax.set_ylabel("Density")
    ax.set_title(f"(c) Probability separability\n(Δmean = +{np.mean(scar_probs)-np.mean(non_scar_probs):.3f})",
                 fontsize=11)
    ax.legend(loc="upper left", fontsize=9)
    ax.tick_params(labelsize=8)

    # Case-specific title
    case_name = case_dir.name
    titles = {
        "pohang_2022": "LandslideKR — Pohang 2022 (Typhoon Hinnamnor, 5–7 Sep)",
        "extreme_rainfall_2023": "LandslideKR — Yecheon 2023 (Monsoon, 13–18 Jul)",
    }
    fig.suptitle(titles.get(case_name, f"LandslideKR — {case_name}"),
                 fontsize=13, y=1.02)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_path}")
    print(f"  dimensions: {prob.shape}")
    print(f"  scar mean prob: {np.mean(scar_probs):.3f}")
    print(f"  non-scar mean prob: {np.mean(non_scar_probs):.3f}")


if __name__ == "__main__":
    case_dir = Path(sys.argv[1] if len(sys.argv) > 1
                    else "/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/out/pohang_2022")
    out_path = Path(sys.argv[2] if len(sys.argv) > 2
                    else "/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/figures/fig1_pohang_2022.png")
    main(case_dir, out_path)
