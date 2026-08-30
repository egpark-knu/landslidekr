#!/usr/bin/env python3
"""Render the Turn 07a-2 final package at the adjudicated minimum size.

This renderer adapts the immutable Turn 07a renderer without modifying it.  It
changes only the display primitive used for positive cells in pixel panels
(a) and (b): every stored positive is drawn once as an equal square centred at
the source raster cell centre.  S1/S2 candidate evidence and the independent
Grok gate select side 2 in final 300-dpi device pixels; S4 cryptographically
links the distributed PNGs to that candidate and renders PDF/SVG from the same
state without making a final visual-gate approval.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import platform
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import fitz
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib import font_manager, patheffects
from matplotlib.collections import PathCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box


ROUND3 = Path("/Users/eungyupark/Dropbox/Manuscripts/0_Landslides/round_3")
FIGURE_DIR = ROUND3 / "figures/turn07a2"
EVIDENCE_DIR = ROUND3 / "evidence/turn07a2"
CANDIDATE_DIR = EVIDENCE_DIR / "candidates"
INTEGRITY_PATH = EVIDENCE_DIR / "source_integrity.json"
SEARCH_PATH = EVIDENCE_DIR / "minimum_size_search.json"
INDEX_PATH = EVIDENCE_DIR / "candidate_contact_sheet_index.md"
EXECUTOR_PATH = EVIDENCE_DIR / "turn07a2_candidate_executor.json"
FINAL_MANIFEST_PATH = FIGURE_DIR / "figure2_render_v2_manifest.json"
RAW_REQUEST_PATH = Path(
    "/Users/eungyupark/mas2-project/downloads/20260830_034013_BQACAgUA.md"
)
SOURCE_PACKET_PATH = ROUND3 / "source_packet/turn07a2_manifest.md"
GROK_GATE_PATH = EVIDENCE_DIR / "grok_candidate_adjudication.json"
CLAUDE_PRECHECK_PATH = EVIDENCE_DIR / "claude_caption_minimality_precheck.json"
CANDIDATE_EXECUTOR_PATH = EVIDENCE_DIR / "turn07a2_candidate_executor.json"

SELECTED_SIDE_PX = 2
ADAPTED_FROM_SHA256 = (
    "59af5227892478723e5fe586c5b54ba995b7c29bc3d59e60290e689fb88869a0"
)
CONTROL_HASHES = {
    "raw_request": "f6d9aaed1b53ae3d3a4486523795f2c51399343b3a806d74f5af26c367ca1edf",
    "corrected_source_packet": "203cdf92baea27f199e46b161b461f475e7018db52802523c5da4e5c95493ed2",
    "source_integrity": "957d1d3f5292271de5fad121ee3f9464f9960b0938897a7cb549ae51a434baf0",
    "minimum_size_search": "25564ac1bb501756c28788a40cdc9b73f43abe8528c09907fc6113396f8d2c27",
    "grok_candidate_gate": "8550ef04113e7a33a849ca5bd6f224b1b789c4b0aa25c6fac6e9f01196063213",
    "claude_caption_precheck": "4c8828c37fc0cd0db64fd603efca02544b63e39cdd7e6bb8b0cab6d51a5db9be",
    "candidate_executor": "3e2aa6eb7f5f877d601650eac637a8bc46e30fc26e24dc6c2984307810ecaea5",
}
FINAL_NAMES = {
    "pdf": "fig02_validation_supports_v2_final.pdf",
    "svg": "fig02_validation_supports_v2_final.svg",
    "final_png": "fig02_validation_supports_v2_final.png",
    "single_color": "fig02_validation_supports_v2_single_color.png",
    "single_grayscale": "fig02_validation_supports_v2_single_grayscale.png",
    "double_color": "fig02_validation_supports_v2_double_color.png",
    "double_grayscale": "fig02_validation_supports_v2_double_grayscale.png",
    "renderer": "render_figure2_turn07a2.py",
    "manifest": "figure2_render_v2_manifest.json",
}

PNG_DPI = 300
HEIGHT_TO_WIDTH = 1.12
MARK_ALPHA = 0.94
MARK_ANTIALIASED = False
INITIAL_SIDES = [1, 2, 3, 4]
EXTENSION_SIDES = [5, 6, 8]
COUNT_RATIO = 231 / 183507
NEAR_ZERO_B_PIXELS = math.ceil(0.10 * 231)

SOURCES = {
    "dem": {
        "path": Path(
            "/Users/eungyupark/Dropbox/Manuscripts/0_Landslides/out/"
            "extreme_rainfall_2023/dem_utm.tif"
        ),
        "sha256": "58a1be2058658afd0f989890bdd83f877bf1d1c35ec31db91d5a8393e2dea7ef",
    },
    "sentinel_pixel": {
        "path": Path(
            "/Users/eungyupark/Dropbox/Manuscripts/0_Landslides/out/"
            "extreme_rainfall_2023/consensus_label.tif"
        ),
        "sha256": "f1d78212dc5a47c55d2a032a5ccd9e1d0ef287e16b62c9b33de9bbe820c8e233",
    },
    "nidr_pixel": {
        "path": Path(
            "/Users/eungyupark/Dropbox/Manuscripts/0_Landslides/out/"
            "extreme_rainfall_2023/consensus_label_variant_B.tif"
        ),
        "sha256": "f2c14512cfa65e35340ed23702cc6f09d013ed6e3179e33636cc7016e2eae4d9",
    },
    "kfs_admin": {
        "path": Path(
            "/Users/eungyupark/Dropbox/Manuscripts/0_Landslides/round_2/"
            "phase3c_aggregate_validation/unit_level_stats.csv"
        ),
        "sha256": "273aff475d5b264e2ce8e4fe04da9ad1a8d45a3f99b0df9afccb69a88ef1def7",
    },
    "sentinel_admin": {
        "path": Path(
            "/Users/eungyupark/Dropbox/Manuscripts/0_Landslides/round_2/"
            "phase4_exploratory_diagnosis/aggregate_sentinel_unit_stats.csv"
        ),
        "sha256": "69cbd314733e632d604d96c650e7b33cc7c49a6e81c9a0ce1413837b8efec486",
    },
    "emd": {
        "path": Path(
            "/Users/eungyupark/Dropbox/GeoAI/01_2026_project/00_demo/"
            "dev_nie_korea/geodata/emd_all.gpkg"
        ),
        "sha256": "9c4f3697f7fab5ed556d77efb28caf353cc2b47a201e93d0609491b50efe075c",
        "layer": "emd_all",
    },
}

BASELINE_FILES = {
    "single_color": {
        "path": ROUND3 / "figures/turn07a/fig02_validation_supports_single_color.png",
        "sha256": "5431d9ebf91353926c68e7d809586fa137835e16ff2097bf3c88eb5cff3a1136",
    },
    "single_grayscale": {
        "path": ROUND3 / "figures/turn07a/fig02_validation_supports_single_grayscale.png",
        "sha256": "5d64791eb9543eb503d660828aaca494eae64862abbb0b4f001a2b1a18da0d0c",
    },
    "double_color": {
        "path": ROUND3 / "figures/turn07a/fig02_validation_supports_double_color.png",
        "sha256": "5c58d48e682b5fcb37a7210b036b442e3bfb9945ef92710418359fa6648d05f1",
    },
    "double_grayscale": {
        "path": ROUND3 / "figures/turn07a/fig02_validation_supports_double_grayscale.png",
        "sha256": "82301bc804e0a622e4dc9aa665e19195900505e10263b6018713110b2ebc07e6",
    },
}

CONDITIONS = {
    "single_color": {
        "pixel_width": 992,
        "width_cm": 8.4,
        "grayscale": False,
    },
    "single_grayscale": {
        "pixel_width": 992,
        "width_cm": 8.4,
        "grayscale": True,
    },
    "double_color": {
        "pixel_width": 2067,
        "width_cm": 17.5,
        "grayscale": False,
    },
    "double_grayscale": {
        "pixel_width": 2067,
        "width_cm": 17.5,
        "grayscale": True,
    },
}

EVENT_BBOXES_LONLAT = {
    "Pohang 2022": [129.2, 36.0, 129.5, 36.2],
    "Yecheon 2023": [127.6, 36.3, 128.9, 37.0],
    "Chuncheon 2020": [127.6, 37.75, 127.95, 38.0],
}

PALETTE = {
    "sentinel": "#0072B2",
    "nidr": "#CC79A7",
    "kfs": "#D55E00",
    "terrain_low": "#F5F5F2",
    "terrain_high": "#B7BAB7",
    "text": "#111111",
}

EXPECTED = {
    "shape": [2768, 4015],
    "crs": "EPSG:32652",
    "sentinel_positive": 183507,
    "nidr_positive": 231,
    "kfs_positive": 4,
    "sentinel_admin_positive": 176,
    "admin_denominator": 205,
    "emd_features": 3558,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_preflight_and_sources() -> dict[str, str]:
    integrity = json.loads(INTEGRITY_PATH.read_text(encoding="utf-8"))
    if integrity.get("verdict") != "PASS":
        raise RuntimeError("source_integrity.json is not PASS")
    if not all(integrity.get("checks", {}).values()):
        raise RuntimeError("source_integrity.json contains a failed check")

    actual = {}
    for key, source in SOURCES.items():
        value = sha256(source["path"])
        actual[key] = value
        if value != source["sha256"]:
            raise RuntimeError(f"held-source hash mismatch: {key}")
    for key, source in BASELINE_FILES.items():
        if sha256(source["path"]) != source["sha256"]:
            raise RuntimeError(f"immutable v1 baseline mismatch: {key}")
    return actual


def raster_cell_centres(mask: np.ndarray, transform) -> dict:
    rows, cols = np.nonzero(mask == 1)
    x = transform.c + (cols.astype(np.float64) + 0.5) * transform.a
    y = transform.f + (rows.astype(np.float64) + 0.5) * transform.e
    linear = rows.astype(np.int64) * mask.shape[1] + cols.astype(np.int64)
    unique_count = int(np.unique(linear).size)
    return {
        "rows": rows,
        "cols": cols,
        "x": x,
        "y": y,
        "primitive_count": int(rows.size),
        "unique_centres": unique_count,
    }


def read_inputs() -> dict:
    with rasterio.open(SOURCES["dem"]["path"]) as ds:
        dem = ds.read(1)
        meta = {
            "crs": str(ds.crs),
            "shape": [ds.height, ds.width],
            "transform": ds.transform,
            "transform_tuple": tuple(ds.transform),
            "bounds": tuple(ds.bounds),
        }
    with rasterio.open(SOURCES["sentinel_pixel"]["path"]) as ds:
        sentinel = ds.read(1)
        sentinel_meta = (str(ds.crs), [ds.height, ds.width], tuple(ds.transform), tuple(ds.bounds))
    with rasterio.open(SOURCES["nidr_pixel"]["path"]) as ds:
        nidr = ds.read(1)
        nidr_meta = (str(ds.crs), [ds.height, ds.width], tuple(ds.transform), tuple(ds.bounds))

    dem_meta = (meta["crs"], meta["shape"], meta["transform_tuple"], meta["bounds"])
    if dem_meta != sentinel_meta or dem_meta != nidr_meta:
        raise RuntimeError("raster CRS/shape/transform/bounds drift")
    if meta["shape"] != EXPECTED["shape"] or meta["crs"] != EXPECTED["crs"]:
        raise RuntimeError("raster expected grid guard failed")

    centres = {
        "a": raster_cell_centres(sentinel, meta["transform"]),
        "b": raster_cell_centres(nidr, meta["transform"]),
    }
    if centres["a"]["primitive_count"] != EXPECTED["sentinel_positive"]:
        raise RuntimeError("Sentinel primitive-count guard failed")
    if centres["b"]["primitive_count"] != EXPECTED["nidr_positive"]:
        raise RuntimeError("NIDR primitive-count guard failed")
    if centres["a"]["unique_centres"] != EXPECTED["sentinel_positive"]:
        raise RuntimeError("Sentinel unique-centre guard failed")
    if centres["b"]["unique_centres"] != EXPECTED["nidr_positive"]:
        raise RuntimeError("NIDR unique-centre guard failed")

    kfs = pd.read_csv(SOURCES["kfs_admin"]["path"], dtype={"ADM_CD": str})
    sentinel_admin = pd.read_csv(
        SOURCES["sentinel_admin"]["path"], dtype={"ADM_CD": str}
    )
    kfs = kfs.loc[kfs["event"].eq("yecheon_2023")].copy()
    sentinel_admin = sentinel_admin.loc[
        sentinel_admin["event"].eq("yecheon_2023")
    ].copy()
    if len(kfs) != 205 or len(sentinel_admin) != 205:
        raise RuntimeError("admin denominator guard failed")
    if set(kfs["ADM_CD"]) != set(sentinel_admin["ADM_CD"]):
        raise RuntimeError("admin identity guard failed")
    if int(kfs["positive"].eq(1).sum()) != 4:
        raise RuntimeError("KFS count guard failed")
    if int(sentinel_admin["positive"].eq(1).sum()) != 176:
        raise RuntimeError("Sentinel admin count guard failed")

    layers = gpd.list_layers(SOURCES["emd"]["path"])
    if "emd_all" not in set(layers["name"]):
        raise RuntimeError("emd_all layer absent")
    emd = gpd.read_file(SOURCES["emd"]["path"], layer="emd_all")
    emd["ADM_CD"] = emd["ADM_CD"].astype(str)
    if str(emd.crs) != "EPSG:5186" or len(emd) != 3558:
        raise RuntimeError("EMD CRS/feature guard failed")
    if emd["ADM_CD"].duplicated().any():
        raise RuntimeError("EMD ADM_CD uniqueness guard failed")

    event_codes = set(kfs["ADM_CD"])
    event_emd = emd.loc[emd["ADM_CD"].isin(event_codes)].copy()
    if len(event_emd) != 205:
        raise RuntimeError("EMD join guard failed")
    event_emd = event_emd.merge(
        kfs[["ADM_CD", "positive"]].rename(columns={"positive": "kfs_positive"}),
        on="ADM_CD",
        how="left",
        validate="one_to_one",
    ).merge(
        sentinel_admin[["ADM_CD", "positive"]].rename(
            columns={"positive": "sentinel_positive"}
        ),
        on="ADM_CD",
        how="left",
        validate="one_to_one",
    )

    locator_boxes = {
        name: gpd.GeoSeries([box(*coordinates)], crs="EPSG:4326")
        .to_crs(emd.crs)
        .iloc[0]
        for name, coordinates in EVENT_BBOXES_LONLAT.items()
    }
    return {
        "dem": dem,
        "dem_meta": meta,
        "centres": centres,
        "emd": emd,
        "event_emd": event_emd.to_crs("EPSG:32652"),
        "locator_boxes": locator_boxes,
    }


def terrain_cmap(grayscale: bool) -> LinearSegmentedColormap:
    colors = (
        ["#F5F5F5", "#D8D8D8", "#B8B8B8"]
        if grayscale
        else [PALETTE["terrain_low"], "#D8DAD6", PALETTE["terrain_high"]]
    )
    return LinearSegmentedColormap.from_list("held_dem_neutral", colors)


def add_scale_bar(ax, bounds, length_m, label, font_size, line_width):
    left, bottom, right, top = bounds
    x0 = left + 0.055 * (right - left)
    y0 = bottom + 0.065 * (top - bottom)
    tick = 0.018 * (top - bottom)
    effect = [
        patheffects.Stroke(linewidth=line_width + 2.0, foreground="white"),
        patheffects.Normal(),
    ]
    ax.plot(
        [x0, x0 + length_m],
        [y0, y0],
        color="#111111",
        linewidth=line_width,
        solid_capstyle="butt",
        path_effects=effect,
        zorder=30,
    )
    for x in (x0, x0 + length_m):
        ax.plot(
            [x, x],
            [y0 - tick / 2, y0 + tick / 2],
            color="#111111",
            linewidth=line_width,
            path_effects=effect,
            zorder=30,
        )
    ax.text(
        x0 + length_m / 2,
        y0 + tick * 0.72,
        label,
        ha="center",
        va="bottom",
        fontsize=font_size,
        color=PALETTE["text"],
        path_effects=[patheffects.withStroke(linewidth=2.0, foreground="white")],
        zorder=31,
    )


def add_shared_north_arrow(ax, font_size, line_width):
    ax.annotate(
        "",
        xy=(0.944, 0.82),
        xytext=(0.944, 0.67),
        xycoords="axes fraction",
        arrowprops={
            "arrowstyle": "-|>",
            "color": "#111111",
            "linewidth": line_width,
            "mutation_scale": 8,
        },
        zorder=35,
    )
    ax.text(
        0.944,
        0.835,
        "N",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=font_size,
        fontweight="bold",
        color=PALETTE["text"],
        path_effects=[patheffects.withStroke(linewidth=2.2, foreground="white")],
        zorder=35,
    )


def draw_locator(ax, data, grayscale, font_size, line_width):
    emd = data["emd"]
    fill = "#EEEEEA" if not grayscale else "#ECECEC"
    emd.plot(ax=ax, facecolor=fill, edgecolor="none", zorder=1)
    emd.boundary.plot(
        ax=ax,
        color="#A8A8A3" if not grayscale else "#AAAAAA",
        linewidth=max(0.08, line_width * 0.12),
        zorder=2,
    )
    styles = {"Pohang 2022": "-", "Yecheon 2023": "--", "Chuncheon 2020": ":"}
    offsets = {"Pohang 2022": (5, -8), "Yecheon 2023": (-40, -3), "Chuncheon 2020": (20, -10)}
    for name, geom in data["locator_boxes"].items():
        gpd.GeoSeries([geom], crs=emd.crs).boundary.plot(
            ax=ax,
            color="#222222",
            linestyle=styles[name],
            linewidth=line_width * 0.9,
            zorder=6,
        )
        point = geom.representative_point()
        ax.annotate(
            name,
            xy=(point.x, point.y),
            xytext=offsets[name],
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=font_size,
            color=PALETTE["text"],
            arrowprops={
                "arrowstyle": "-",
                "linewidth": max(0.35, line_width * 0.45),
                "color": "#555555",
                "shrinkA": 1,
                "shrinkB": 1,
            },
            path_effects=[patheffects.withStroke(linewidth=2.0, foreground="white")],
            zorder=8,
        )
    minx, miny, maxx, maxy = emd.total_bounds
    xpad = 0.025 * (maxx - minx)
    ypad = 0.025 * (maxy - miny)
    ax.set_xlim(minx - xpad, maxx + xpad)
    ax.set_ylim(miny - ypad, maxy + ypad)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.text(
        0.01,
        0.99,
        "Three-event locator",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=font_size + 0.4,
        fontweight="bold",
        color=PALETTE["text"],
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.83, "pad": 1.2},
        zorder=20,
    )
    add_scale_bar(
        ax,
        (minx - xpad, miny - ypad, maxx + xpad, maxy + ypad),
        100000,
        "100 km",
        max(font_size - 0.3, 5.0),
        max(line_width * 0.75, 0.6),
    )


def legend_handles(grayscale):
    if grayscale:
        provenance = [
            Patch(facecolor="#333333", edgecolor="#222222", label="Sentinel provenance"),
            Patch(facecolor="#777777", edgecolor="#222222", label="Stored national-inventory provenance"),
            Patch(facecolor="#B5B5B5", edgecolor="#222222", label="Forest-service provenance"),
        ]
    else:
        provenance = [
            Patch(facecolor=PALETTE["sentinel"], edgecolor="none", label="Sentinel provenance"),
            Patch(facecolor=PALETTE["nidr"], edgecolor="none", label="Stored national-inventory provenance"),
            Patch(facecolor=PALETTE["kfs"], edgecolor="none", label="Forest-service provenance"),
        ]
    return provenance + [
        Patch(facecolor="#333333", edgecolor="none", label="Pixel support (stored centres)"),
        Patch(facecolor="#E0E0E0", edgecolor="#444444", hatch="///", label="Administrative support"),
        Line2D([0], [0], color="#777777", linewidth=0.7, label="EMD boundary"),
        Line2D([0], [0], color="#222222", linewidth=0.9, linestyle="--", label="Event bounding box"),
    ]


def draw_legend(ax, grayscale, font_size):
    ax.set_axis_off()
    ax.text(
        0.0,
        0.985,
        "Integrated figure key",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=font_size + 0.4,
        fontweight="bold",
        color=PALETTE["text"],
    )
    ax.legend(
        handles=legend_handles(grayscale),
        loc="upper left",
        bbox_to_anchor=(0.0, 0.88),
        frameon=False,
        fontsize=font_size,
        handlelength=1.9,
        handleheight=0.75,
        borderaxespad=0.0,
        labelspacing=0.40,
        columnspacing=0.8,
        ncol=1,
    )


def scatter_positive_marks(ax, centre_record, side_px, color):
    side_points = side_px * 72.0 / PNG_DPI
    return ax.scatter(
        centre_record["x"],
        centre_record["y"],
        s=side_points**2,
        marker="s",
        facecolors=color,
        edgecolors="none",
        linewidths=0,
        alpha=MARK_ALPHA,
        antialiaseds=MARK_ANTIALIASED,
        transform=ax.transData,
        clip_on=True,
        zorder=8,
    )


def set_detail_extent(ax, data):
    left, bottom, right, top = data["dem_meta"]["bounds"]
    ax.set_xlim(left, right)
    ax.set_ylim(bottom, top)
    ax.set_aspect("equal")
    ax.set_axis_off()


def draw_detail_panel(ax, data, panel, grayscale, font_size, line_width, side_px):
    left, bottom, right, top = data["dem_meta"]["bounds"]
    extent = [left, right, bottom, top]
    ax.imshow(
        data["dem"],
        cmap=terrain_cmap(grayscale),
        vmin=0,
        vmax=1400,
        extent=extent,
        origin="upper",
        interpolation="nearest",
        resample=False,
        zorder=0,
    )
    if panel == "a":
        color = "#333333" if grayscale else PALETTE["sentinel"]
        scatter_positive_marks(ax, data["centres"]["a"], side_px, color)
        title = "(a) Sentinel\npixel support | n = 183,507"
    elif panel == "b":
        color = "#777777" if grayscale else PALETTE["nidr"]
        scatter_positive_marks(ax, data["centres"]["b"], side_px, color)
        title = "(b) Stored national inventory\npixel support | n = 231"
    else:
        event_emd = data["event_emd"]
        event_emd.boundary.plot(
            ax=ax,
            color="#666666",
            linewidth=max(0.18, line_width * 0.27),
            zorder=10,
        )
        if panel == "c":
            positives = event_emd.loc[event_emd["kfs_positive"].eq(1)]
            face = "#B5B5B5" if grayscale else PALETTE["kfs"]
            positives.plot(
                ax=ax,
                facecolor=face,
                edgecolor="#333333",
                linewidth=max(0.25, line_width * 0.36),
                alpha=0.76,
                hatch="////",
                zorder=12,
            )
            title = "(c) Forest service\nadministrative support | n = 4 / 205"
        else:
            positives = event_emd.loc[event_emd["sentinel_positive"].eq(1)]
            face = "#666666" if grayscale else PALETTE["sentinel"]
            positives.plot(
                ax=ax,
                facecolor=face,
                edgecolor="#222222",
                linewidth=max(0.22, line_width * 0.32),
                alpha=0.62,
                hatch="\\\\",
                zorder=12,
            )
            title = "(d) Sentinel\nadministrative support | n = 176 / 205"
    set_detail_extent(ax, data)
    ax.text(
        0.012,
        0.988,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=font_size,
        fontweight="bold",
        linespacing=1.08,
        color=PALETTE["text"],
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "pad": 1.2},
        zorder=40,
    )
    add_scale_bar(
        ax,
        (left, bottom, right, top),
        20000,
        "20 km",
        max(font_size - 0.4, 5.0),
        max(line_width * 0.75, 0.65),
    )


def create_layout(pixel_width, transparent=False):
    pixel_height = round(pixel_width * HEIGHT_TO_WIDTH)
    fig = plt.figure(
        figsize=(pixel_width / PNG_DPI, pixel_height / PNG_DPI),
        dpi=PNG_DPI,
        facecolor="none" if transparent else "white",
    )
    grid = fig.add_gridspec(
        3,
        2,
        height_ratios=[0.94, 1.0, 1.0],
        width_ratios=[1.0, 1.0],
        left=0.025,
        right=0.985,
        bottom=0.022,
        top=0.985,
        wspace=0.035,
        hspace=0.055,
    )
    locator_ax = fig.add_subplot(grid[0, 0])
    legend_ax = fig.add_subplot(grid[0, 1])
    detail_axes = [
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
        fig.add_subplot(grid[2, 0]),
        fig.add_subplot(grid[2, 1]),
    ]
    if transparent:
        fig.patch.set_alpha(0.0)
        for ax in [locator_ax, legend_ax, *detail_axes]:
            ax.patch.set_alpha(0.0)
    return fig, locator_ax, legend_ax, detail_axes


def build_figure(pixel_width, grayscale, side_px):
    fig, locator_ax, legend_ax, detail_axes = create_layout(pixel_width)
    single = pixel_width < 1500
    font_size = 6.15 if single else 7.15
    line_width = 0.85 if single else 1.0
    draw_locator(locator_ax, DATA, grayscale, font_size, line_width)
    draw_legend(legend_ax, grayscale, font_size)
    for ax, panel in zip(detail_axes, ("a", "b", "c", "d")):
        draw_detail_panel(
            ax, DATA, panel, grayscale, font_size, line_width, side_px
        )
    add_shared_north_arrow(detail_axes[1], font_size, line_width)
    return fig


def save_candidate(path, pixel_width, grayscale, side_px):
    fig = build_figure(pixel_width, grayscale, side_px)
    fig.savefig(
        path,
        dpi=PNG_DPI,
        facecolor="white",
        metadata={
            "Software": "Turn 07a-2 deterministic candidate renderer",
            "Figure": f"Figure 2 display-size candidate {side_px}px",
        },
        pil_kwargs={"compress_level": 6},
    )
    plt.close(fig)


def roi_array_slice(bbox, pixel_width, pixel_height):
    x0 = max(0, int(math.ceil(bbox.x0 - 0.5)))
    x1 = min(pixel_width, int(math.ceil(bbox.x1 - 0.5)))
    y0_display = max(0, int(math.ceil(bbox.y0 - 0.5)))
    y1_display = min(pixel_height, int(math.ceil(bbox.y1 - 0.5)))
    row0 = pixel_height - y1_display
    row1 = pixel_height - y0_display
    return slice(row0, row1), slice(x0, x1), {
        "x_start": x0,
        "x_stop_exclusive": x1,
        "display_y_start": y0_display,
        "display_y_stop_exclusive": y1_display,
        "array_row_start": row0,
        "array_row_stop_exclusive": row1,
    }


def panel_geometry_record(ax, centre_record, bbox):
    coordinates = np.column_stack((centre_record["x"], centre_record["y"]))
    display = ax.transData.transform(coordinates)
    recovered = ax.transData.inverted().transform(display)
    max_error = float(np.max(np.abs(recovered - coordinates)))
    left, bottom, right, top = DATA["dem_meta"]["bounds"]
    inside_map = (
        (centre_record["x"] >= left)
        & (centre_record["x"] <= right)
        & (centre_record["y"] >= bottom)
        & (centre_record["y"] <= top)
    )
    inside_display = (
        (display[:, 0] >= bbox.x0)
        & (display[:, 0] <= bbox.x1)
        & (display[:, 1] >= bbox.y0)
        & (display[:, 1] <= bbox.y1)
    )
    anchor_x = np.floor(display[:, 0]).astype(np.int64)
    anchor_y = np.floor(display[:, 1]).astype(np.int64)
    anchors = anchor_y * 100000 + anchor_x
    unique_anchors = int(np.unique(anchors).size)
    return {
        "primitive_count": centre_record["primitive_count"],
        "unique_centres": centre_record["unique_centres"],
        "centres_inside_map_bounds": int(np.count_nonzero(inside_map)),
        "centres_inside_display_bounds": int(np.count_nonzero(inside_display)),
        "coordinate_preservation": bool(
            max_error < 1e-7
            and np.count_nonzero(inside_map) == centre_record["primitive_count"]
            and np.count_nonzero(inside_display) == centre_record["primitive_count"]
        ),
        "inverse_transform_max_abs_error_map_units": max_error,
        "display_unique_anchor_pixels": unique_anchors,
        "display_anchor_collisions": centre_record["primitive_count"] - unique_anchors,
        "display_centre_bounds_px": [
            float(display[:, 0].min()),
            float(display[:, 1].min()),
            float(display[:, 0].max()),
            float(display[:, 1].max()),
        ],
    }


def render_coverage_metrics(pixel_width, side_px):
    pixel_height = round(pixel_width * HEIGHT_TO_WIDTH)
    fig, locator_ax, legend_ax, axes = create_layout(pixel_width, transparent=True)
    locator_ax.set_axis_off()
    legend_ax.set_axis_off()
    for ax in axes:
        set_detail_extent(ax, DATA)
    scatter_positive_marks(axes[0], DATA["centres"]["a"], side_px, "#000000")
    scatter_positive_marks(axes[1], DATA["centres"]["b"], side_px, "#000000")
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba()).copy()
    renderer = fig.canvas.get_renderer()
    single_alpha_byte = int(round(MARK_ALPHA * 255))
    panels = {}
    bboxes = []
    for panel, ax in zip(("a", "b"), axes[:2]):
        bbox = ax.get_window_extent(renderer)
        bboxes.append(bbox)
        row_slice, col_slice, roi_index = roi_array_slice(
            bbox, pixel_width, pixel_height
        )
        alpha = rgba[row_slice, col_slice, 3]
        touched = int(np.count_nonzero(alpha > 0))
        overlap_pixels = int(np.count_nonzero(alpha > single_alpha_byte))
        height, width = alpha.shape
        record = panel_geometry_record(ax, DATA["centres"][panel], bbox)
        record.update(
            {
                "map_roi_width_px": int(width),
                "map_roi_height_px": int(height),
                "map_roi_total_px": int(width * height),
                "coverage_pixels": touched,
                "coverage_ratio": touched / (width * height),
                "overlap_pixels": overlap_pixels,
                "overlap_present": overlap_pixels > 0,
                "overlap_ratio_of_coverage": overlap_pixels / touched if touched else None,
                "coverage_alpha_values": [int(v) for v in np.unique(alpha) if v > 0],
                "roi_index": roi_index,
            }
        )
        panels[panel] = record
    transform_a = axes[0].transData.get_affine().get_matrix()
    transform_b = axes[1].transData.get_affine().get_matrix()
    scale_max_abs_difference = float(
        np.max(np.abs(transform_a[:2, :2] - transform_b[:2, :2]))
    )
    same_scale = bool(
        np.allclose(
            transform_a[:2, :2],
            transform_b[:2, :2],
            atol=1e-15,
            rtol=1e-12,
        )
    )
    same_roi = (
        panels["a"]["map_roi_width_px"] == panels["b"]["map_roi_width_px"]
        and panels["a"]["map_roi_height_px"] == panels["b"]["map_roi_height_px"]
    )
    plt.close(fig)
    display_ratio = (
        panels["b"]["coverage_ratio"] / panels["a"]["coverage_ratio"]
        if panels["a"]["coverage_ratio"]
        else None
    )
    return {
        "panels": panels,
        "b_to_a_display_coverage_ratio": display_ratio,
        "inflation_vs_exact_count_ratio": display_ratio / COUNT_RATIO,
        "exact_count_ratio_231_over_183507": COUNT_RATIO,
        "same_roi_dimensions_a_b": same_roi,
        "same_data_to_device_scale_a_b": same_scale,
        "a_b_scale_matrix_max_abs_difference": scale_max_abs_difference,
        "a_b_scale_equivalence_tolerance": {"absolute": 1e-15, "relative": 1e-12},
        "same_primitive": "matplotlib PathCollection square marker",
        "same_side_px": side_px,
        "same_alpha": MARK_ALPHA,
        "same_antialiasing": MARK_ANTIALIASED,
        "same_coordinate_transform_rule": "source cell-centre map coordinates through each equal-size panel's ax.transData",
        "physical_mark_side_mm": side_px * 25.4 / PNG_DPI,
        "single_mark_alpha_byte": single_alpha_byte,
    }


def inspect_png(path, expected_width, grayscale):
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"))
        dpi = image.info.get("dpi")
        dimensions = list(image.size)
    channels_equal = bool(
        np.array_equal(rgb[..., 0], rgb[..., 1])
        and np.array_equal(rgb[..., 1], rgb[..., 2])
    )
    return {
        "path": str(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "pixel_dimensions": dimensions,
        "encoded_dpi": [float(v) for v in dpi] if dpi else None,
        "expected_pixel_width": expected_width,
        "expected_pixel_height": round(expected_width * HEIGHT_TO_WIDTH),
        "dimension_check": dimensions
        == [expected_width, round(expected_width * HEIGHT_TO_WIDTH)],
        "rgb_channels_identical": channels_equal,
        "grayscale_channel_check": channels_equal if grayscale else True,
    }


def render_side(side_px):
    width_metrics = {
        992: render_coverage_metrics(992, side_px),
        2067: render_coverage_metrics(2067, side_px),
    }
    condition_records = []
    for condition, spec in CONDITIONS.items():
        path = CANDIDATE_DIR / f"figure2_side{side_px:02d}_{condition}.png"
        save_candidate(path, spec["pixel_width"], spec["grayscale"], side_px)
        metrics = copy.deepcopy(width_metrics[spec["pixel_width"]])
        metrics.update(
            {
                "condition": condition,
                "intended_width_cm": spec["width_cm"],
                "color_mode": "grayscale" if spec["grayscale"] else "color",
                "grayscale_geometry_equal_to_color": True,
                "geometry_mask_reused_for_color_and_grayscale": True,
                "file": inspect_png(
                    path, spec["pixel_width"], spec["grayscale"]
                ),
            }
        )
        condition_records.append(metrics)
    return {
        "side_px": side_px,
        "physical_mark_side_mm": side_px * 25.4 / PNG_DPI,
        "conditions": condition_records,
    }


def make_contact_sheet(condition, candidate_records):
    paths = [
        Path(
            next(
                c["file"]["path"]
                for c in candidate["conditions"]
                if c["condition"] == condition
            )
        )
        for candidate in candidate_records
    ]
    thumb_width = 470
    label_height = 38
    margin = 12
    images = []
    for path in paths:
        with Image.open(path) as opened:
            image = opened.convert("RGB")
            scale = thumb_width / image.width
            image = image.resize(
                (thumb_width, round(image.height * scale)), Image.Resampling.LANCZOS
            )
            images.append(image)
    sheet_height = label_height + max(image.height for image in images) + 2 * margin
    sheet_width = len(images) * thumb_width + (len(images) + 1) * margin
    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)
    font_path = font_manager.findfont("Times New Roman", fallback_to_default=True)
    try:
        font = ImageFont.truetype(font_path, 23)
    except OSError:
        font = ImageFont.load_default()
    for index, (image, candidate) in enumerate(zip(images, candidate_records)):
        x = margin + index * (thumb_width + margin)
        draw.text(
            (x, margin),
            f"side = {candidate['side_px']} device px",
            fill="black",
            font=font,
        )
        sheet.paste(image, (x, margin + label_height))
    path = EVIDENCE_DIR / f"contact_sheet_{condition}.png"
    sheet.save(path, dpi=(PNG_DPI, PNG_DPI), compress_level=6)
    return inspect_png(path, sheet_width, grayscale=False)


def baseline_records():
    records = {}
    for condition, record in BASELINE_FILES.items():
        path = record["path"]
        spec = CONDITIONS[condition]
        inspection = inspect_png(path, spec["pixel_width"], spec["grayscale"])
        inspection["expected_sha256"] = record["sha256"]
        inspection["hash_match"] = inspection["sha256"] == record["sha256"]
        inspection["immutable_reference_only"] = True
        records[condition] = inspection
    return records


def write_index(candidate_records, contact_sheets, baselines):
    lines = [
        "# Turn 07a-2 candidate contact sheets",
        "",
        "These sheets are navigation aids for Grok, not visual-gate verdicts. Candidate images remain the 300-dpi files listed below. The immutable Turn 07a native files are referenced in place and were not copied or modified.",
        "",
        "## Contact sheets",
        "",
    ]
    for condition, record in contact_sheets.items():
        lines.append(f"- `{condition}`: `{record['path']}`")
    lines.extend(["", "## Immutable native v1 references", ""])
    for condition, record in baselines.items():
        lines.append(
            f"- `{condition}`: `{record['path']}` — SHA-256 `{record['sha256']}`"
        )
    lines.extend(["", "## Candidate files", ""])
    lines.append("| side (device px) | condition | file | SHA-256 |")
    lines.append("|---:|---|---|---|")
    for candidate in candidate_records:
        for condition in candidate["conditions"]:
            file_record = condition["file"]
            lines.append(
                f"| {candidate['side_px']} | {condition['condition']} | `{file_record['path']}` | `{file_record['sha256']}` |"
            )
    lines.extend(
        [
            "",
            "Coverage in `minimum_size_search.json` is the renderer-side union of device pixels touched by at least one display mark before colour compositing. It is not stored-raster area and does not change counts or coordinates.",
            "",
            "`visual_gate_status` remains `UNJUDGED`; only Grok may select the first candidate passing G1 and G1b in all four print conditions.",
        ]
    )
    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    global DATA
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams.update(
        {
            "font.family": "Times New Roman",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.unicode_minus": False,
            "image.interpolation": "nearest",
            "hatch.linewidth": 0.45,
        }
    )

    source_hashes_before = verify_preflight_and_sources()
    DATA = read_inputs()
    baselines = baseline_records()
    if not all(record["hash_match"] for record in baselines.values()):
        raise RuntimeError("native v1 baseline reference hash mismatch")

    candidate_records = [render_side(side) for side in INITIAL_SIDES]
    side4 = candidate_records[-1]
    side4_b_coverage = {
        record["condition"]: record["panels"]["b"]["coverage_pixels"]
        for record in side4["conditions"]
    }
    extension_triggered = any(
        value <= NEAR_ZERO_B_PIXELS for value in side4_b_coverage.values()
    )
    if extension_triggered:
        candidate_records.extend(render_side(side) for side in EXTENSION_SIDES)

    contact_sheets = {
        condition: make_contact_sheet(condition, candidate_records)
        for condition in CONDITIONS
    }
    write_index(candidate_records, contact_sheets, baselines)

    source_hashes_after = {
        key: sha256(source["path"]) for key, source in SOURCES.items()
    }
    if source_hashes_after != source_hashes_before:
        raise RuntimeError("held-source identity changed during rendering")

    script_path = Path(__file__).resolve()
    script_hash = sha256(script_path)
    search = {
        "schema_version": "turn07a2-minimum-display-size-search-v1",
        "turn_id": "T1_codex1_d60027",
        "scope_nodes": ["S1", "S2"],
        "visual_gate_status": "UNJUDGED",
        "selected_candidate": None,
        "selection_authority": "Only Grok may pick the first tested size whose four print conditions pass G1 and G1b.",
        "coverage_metric_warning": "Renderer-side binary coverage counts final device pixels touched by at least one display mark before colour compositing. It measures visible display marks, not stored raster area, and it does not change stored counts or coordinates.",
        "exact_count_ratio_231_over_183507": COUNT_RATIO,
        "candidate_order_rule": "ascending integer side lengths; no smaller tested integer may be skipped before selection",
        "candidate_side_definition": "square side length in final output device pixels at 300 dpi",
        "mark_contract": {
            "primitive": "matplotlib PathCollection square marker",
            "one_primitive_per_stored_positive": True,
            "location": "exact affine-derived raster cell-centre map coordinate",
            "side_points_formula": "side_px * 72 / 300",
            "alpha": MARK_ALPHA,
            "antialiasing": MARK_ANTIALIASED,
            "same_for_panels_a_b": True,
            "coordinate_transform": "ax.transData on equal-size panels with the common held DEM extent",
        },
        "immutable_native_v1_baseline": baselines,
        "extension_rule": {
            "initial_sides": INITIAL_SIDES,
            "conditional_sides": EXTENSION_SIDES,
            "near_zero_definition": f"panel-b coverage_pixels <= {NEAR_ZERO_B_PIXELS}, i.e. no more than 10% of 231 stored positives worth of touched device pixels",
            "candidate4_panel_b_coverage_pixels": side4_b_coverage,
            "triggered": extension_triggered,
            "reason": "Candidate 4 did not have zero or nearly-zero panel-b renderer coverage in any condition; no extension for visual comfort was permitted."
            if not extension_triggered
            else "Candidate 4 met the predeclared zero/nearly-zero implementation threshold, so 5, 6 and 8 were generated monotonically.",
        },
        "candidates": candidate_records,
        "contact_sheets": contact_sheets,
        "contact_sheet_index": {
            "path": str(INDEX_PATH),
            "sha256": sha256(INDEX_PATH),
            "size_bytes": INDEX_PATH.stat().st_size,
        },
        "script": {
            "path": str(script_path),
            "sha256": script_hash,
            "size_bytes": script_path.stat().st_size,
        },
        "forbidden_operations": {
            "cluster": False,
            "merge": False,
            "discard": False,
            "subsample": False,
            "smooth": False,
            "data_space_dilation": False,
            "data_space_buffer": False,
            "stored_raster_write": False,
            "extent_change": False,
            "layout_change": False,
            "scientific_layer_change": False,
        },
    }
    SEARCH_PATH.write_text(
        json.dumps(search, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    candidate_files = [
        record["file"]
        for candidate in candidate_records
        for record in candidate["conditions"]
    ]
    deterministic_checks = {
        "source_integrity_pass": True,
        "held_sources_rechecked_before_and_after": source_hashes_before
        == source_hashes_after,
        "candidate_sides_ascending": [c["side_px"] for c in candidate_records]
        == sorted(c["side_px"] for c in candidate_records),
        "all_candidate_dimensions_and_dpi": all(
            record["dimension_check"]
            and record["encoded_dpi"] is not None
            and all(abs(value - PNG_DPI) < 0.01 for value in record["encoded_dpi"])
            for record in candidate_files
        ),
        "all_grayscale_channels_equal": all(
            record["grayscale_channel_check"] for record in candidate_files
        ),
        "primitive_counts_exact_all_records": all(
            condition["panels"]["a"]["primitive_count"] == 183507
            and condition["panels"]["b"]["primitive_count"] == 231
            for candidate in candidate_records
            for condition in candidate["conditions"]
        ),
        "unique_centres_exact_all_records": all(
            condition["panels"]["a"]["unique_centres"] == 183507
            and condition["panels"]["b"]["unique_centres"] == 231
            for candidate in candidate_records
            for condition in candidate["conditions"]
        ),
        "coordinates_preserved_all_records": all(
            condition["panels"]["a"]["coordinate_preservation"]
            and condition["panels"]["b"]["coordinate_preservation"]
            for candidate in candidate_records
            for condition in candidate["conditions"]
        ),
        "same_mark_contract_a_b_all_records": all(
            condition["same_roi_dimensions_a_b"]
            and condition["same_data_to_device_scale_a_b"]
            and condition["same_side_px"] == candidate["side_px"]
            and condition["same_alpha"] == MARK_ALPHA
            and condition["same_antialiasing"] is MARK_ANTIALIASED
            for candidate in candidate_records
            for condition in candidate["conditions"]
        ),
        "color_grayscale_geometry_equal": all(
            condition["grayscale_geometry_equal_to_color"]
            for candidate in candidate_records
            for condition in candidate["conditions"]
        ),
        "no_final_v2_output_names_created": True,
        "selected_candidate_is_null": True,
        "visual_gate_unjudged": True,
    }
    if not all(deterministic_checks.values()):
        raise RuntimeError(f"deterministic candidate guard failed: {deterministic_checks}")

    executor = {
        "schema_version": "turn07a2-candidate-executor-v1",
        "turn_id": "T1_codex1_d60027",
        "role": "primary candidate renderer and quantitative search executor",
        "scope_completed": ["S1", "S2"],
        "preflight": {
            "path": str(INTEGRITY_PATH),
            "sha256": sha256(INTEGRITY_PATH),
            "verdict": "PASS",
        },
        "commands": [
            "/Users/eungyupark/anaconda3/bin/python /Users/eungyupark/Dropbox/Manuscripts/0_Landslides/round_3/figures/turn07a2/render_figure2_turn07a2.py"
        ],
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "matplotlib": matplotlib.__version__,
            "rasterio": rasterio.__version__,
            "geopandas": gpd.__version__,
        },
        "script": {
            "path": str(script_path),
            "sha256": script_hash,
            "size_bytes": script_path.stat().st_size,
            "immutable_v1_renderer": str(
                ROUND3 / "figures/turn07a/render_figure2_turn07a.py"
            ),
            "immutable_v1_renderer_sha256": "fbba253617c9fd5d60ccd3df39fbf424e8fbd444a0ad32539e34c506617f2ff4",
        },
        "coverage_method": {
            "renderer": "Matplotlib Agg at the final 300-dpi pixel dimensions",
            "mask": "A transparent, layout-identical figure draws the same square PathCollections. Within each final map ROI, alpha > 0 defines the pre-colour-compositing binary union mask.",
            "overlap": f"With antialiasing disabled and single-mark alpha byte {round(MARK_ALPHA * 255)}, alpha greater than that byte records pixels hit by overlapping primitives.",
            "distinction": "Coverage is display-space mark coverage, not stored raster area.",
        },
        "files": {
            "source_integrity": str(INTEGRITY_PATH),
            "minimum_size_search": str(SEARCH_PATH),
            "contact_sheet_index": str(INDEX_PATH),
            "candidate_images": [record["path"] for record in candidate_files],
            "contact_sheets": [record["path"] for record in contact_sheets.values()],
        },
        "invariant_checks": deterministic_checks,
        "extension_decision": search["extension_rule"],
        "limitations": [
            "No visual G1/G1b or G2-G6 verdict is made by this executor.",
            "Device-pixel coverage is a rendering metric and must not be interpreted as scientific raster area.",
            "Overlapping display squares reduce union coverage without merging or deleting source primitives.",
            "Contact sheets are downsampled navigation aids; Grok must inspect the original 300-dpi candidate files at final print size.",
            "The renderer was executed in the base GIS environment because it contains rasterio/geopandas; MAS command traffic remains on the required MAS Python runtime.",
        ],
        "automated_file_inspection": {
            "all_images_opened_with_pillow": True,
            "dimensions_dpi_and_grayscale_channels_checked": True,
            "deterministic_defects_found": [],
            "visual_gate_approval_attempted": False,
        },
        "independent_visual_inspection": {
            "status": "PENDING_WORKER_ORIGINAL_FILE_INSPECTION",
            "scope": "deterministic implementation defects only",
        },
        "no_self_approval": "visual_gate_status is UNJUDGED, selected_candidate is null, and only Grok may select the first G1/G1b-passing size.",
    }
    EXECUTOR_PATH.write_text(
        json.dumps(executor, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "candidate_sides": [record["side_px"] for record in candidate_records],
                "candidate_images": len(candidate_files),
                "extension_triggered": extension_triggered,
                "search": str(SEARCH_PATH),
                "executor": str(EXECUTOR_PATH),
            },
            indent=2,
        )
    )


def sha256_prefix(path: Path, byte_count: int) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        digest.update(stream.read(byte_count))
    return digest.hexdigest()


def final_control_preflight():
    control_paths = {
        "raw_request": RAW_REQUEST_PATH,
        "corrected_source_packet": SOURCE_PACKET_PATH,
        "source_integrity": INTEGRITY_PATH,
        "minimum_size_search": SEARCH_PATH,
        "grok_candidate_gate": GROK_GATE_PATH,
        "claude_caption_precheck": CLAUDE_PRECHECK_PATH,
        "candidate_executor": CANDIDATE_EXECUTOR_PATH,
    }
    control_records = {}
    for name, path in control_paths.items():
        actual = sha256(path)
        if actual != CONTROL_HASHES[name]:
            raise RuntimeError(f"S4 control hash mismatch: {name}")
        control_records[name] = {
            "path": str(path),
            "sha256": actual,
            "size_bytes": path.stat().st_size,
        }

    integrity = json.loads(INTEGRITY_PATH.read_text(encoding="utf-8"))
    if integrity.get("verdict") != "PASS" or not all(
        integrity.get("checks", {}).values()
    ):
        raise RuntimeError("source_integrity.json did not retain PASS")

    immutable_before = {}
    for section in ("held_sources", "frozen_and_turn07a_baselines"):
        for name, record in integrity[section].items():
            path = Path(record["path"])
            prefix_bytes = 18074 if name == "editorial_decisions" else None
            actual = (
                sha256_prefix(path, prefix_bytes) if prefix_bytes else sha256(path)
            )
            expected = record["expected_sha256"]
            if actual != expected:
                raise RuntimeError(f"S4 immutable-input hash mismatch: {name}")
            immutable_before[name] = {
                "group": section,
                "path": str(path),
                "expected_sha256": expected,
                "before_sha256": actual,
                "hash_scope": "first 18,074 bytes"
                if prefix_bytes
                else "complete file",
                "prefix_bytes": prefix_bytes,
            }

    search = json.loads(SEARCH_PATH.read_text(encoding="utf-8"))
    grok = json.loads(GROK_GATE_PATH.read_text(encoding="utf-8"))
    claude = json.loads(CLAUDE_PRECHECK_PATH.read_text(encoding="utf-8"))
    if grok.get("selected_candidate_px") != SELECTED_SIDE_PX:
        raise RuntimeError("Grok did not select exactly side_px=2")
    if grok.get("option_A_fallback") is not False:
        raise RuntimeError("Grok option_A_fallback is not false")
    if grok.get("all_16_hashes_match_index") is not True:
        raise RuntimeError("Grok all_16_hashes_match_index is not true")
    if len(grok.get("files_inspected", [])) != 16:
        raise RuntimeError("Grok gate does not contain exactly 16 inspected files")

    search_index = {
        (candidate["side_px"], condition["condition"]): condition
        for candidate in search["candidates"]
        for condition in candidate["conditions"]
    }
    if len(search_index) != 16:
        raise RuntimeError("minimum_size_search.json does not index 16 candidates")
    candidate_hash_checks = []
    for inspected in grok["files_inspected"]:
        key = (inspected["side_px"], inspected["condition"])
        indexed = search_index[key]["file"]
        actual = sha256(Path(inspected["path"]))
        values = {
            actual,
            inspected["computed_sha256"],
            inspected["index_sha256"],
            indexed["sha256"],
        }
        if inspected.get("hash_match") is not True or len(values) != 1:
            raise RuntimeError(f"candidate hash mismatch: {key}")
        candidate_hash_checks.append(
            {
                "side_px": key[0],
                "condition": key[1],
                "path": inspected["path"],
                "sha256": actual,
                "match": True,
            }
        )

    role_boundary = claude.get("role_boundary", {})
    if claude.get("verdict") != "PRECHECK_COMPLETE_NO_APPROVAL" or any(
        role_boundary.get(key) is not False
        for key in (
            "is_visual_selector",
            "approves_candidate_or_final_figure",
            "judges_G1_or_G1b",
        )
    ):
        raise RuntimeError("Claude precheck exceeded or lost its advisory boundary")
    if any(search.get("forbidden_operations", {}).values()):
        raise RuntimeError("minimum search records a forbidden operation")

    selected = {
        condition: search_index[(SELECTED_SIDE_PX, condition)]
        for condition in CONDITIONS
    }
    permitted_preexisting = set(FINAL_NAMES.values())
    unexpected = {
        path.name for path in FIGURE_DIR.iterdir() if path.name not in permitted_preexisting
    }
    if unexpected:
        raise RuntimeError(f"unexpected file in final package directory: {unexpected}")
    return control_records, immutable_before, search, grok, claude, selected, candidate_hash_checks


def immutable_after_records(before):
    after = copy.deepcopy(before)
    for name, record in after.items():
        path = Path(record["path"])
        actual = (
            sha256_prefix(path, record["prefix_bytes"])
            if record["prefix_bytes"]
            else sha256(path)
        )
        record["after_sha256"] = actual
        record["before_after_match"] = actual == record["before_sha256"]
        record["expected_after_match"] = actual == record["expected_sha256"]
        if not record["before_after_match"] or not record["expected_after_match"]:
            raise RuntimeError(f"immutable input changed during S4: {name}")
    return after


def render_final_vectors(pdf_path: Path, svg_path: Path):
    fig = build_figure(2067, grayscale=False, side_px=SELECTED_SIDE_PX)
    exact_width_in = 17.5 / 2.54
    fig.set_size_inches(exact_width_in, exact_width_in * HEIGHT_TO_WIDTH, forward=True)
    marker_counts_by_panel = {}
    scientific_collections = []
    for panel, ax in zip(("a", "b"), fig.axes[2:4]):
        panel_collections = [
            collection
            for collection in ax.collections
            if isinstance(collection, PathCollection)
        ]
        if len(panel_collections) != 1:
            raise RuntimeError(
                f"expected one scientific PathCollection in panel {panel}: "
                f"found {len(panel_collections)}"
            )
        collection = panel_collections[0]
        scientific_collections.append(collection)
        marker_counts_by_panel[panel] = int(len(collection.get_offsets()))
    marker_counts_sorted = sorted(marker_counts_by_panel.values())
    if marker_counts_sorted != [231, 183507]:
        raise RuntimeError(
            f"unexpected sorted final PathCollection counts: {marker_counts_sorted}"
        )
    if marker_counts_by_panel != {"a": 183507, "b": 231}:
        raise RuntimeError(
            f"unexpected panel-mapped PathCollection counts: {marker_counts_by_panel}"
        )
    for collection in scientific_collections:
        collection.set_rasterized(True)
    fixed_time = dt.datetime(2026, 8, 30, 0, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    fig.savefig(
        pdf_path,
        format="pdf",
        dpi=PNG_DPI,
        facecolor="white",
        metadata={
            "Title": "Figure 2 validation supports v2 final",
            "Author": "MAS2 Turn 07a-2",
            "Subject": "Selected 2-device-pixel final renderer state",
            "Creator": "Turn 07a-2 deterministic final renderer",
            "CreationDate": fixed_time,
            "ModDate": fixed_time,
        },
    )
    fig.savefig(
        svg_path,
        format="svg",
        dpi=PNG_DPI,
        facecolor="white",
        metadata={
            "Title": "Figure 2 validation supports v2 final",
            "Date": fixed_time.isoformat(),
            "Creator": "Turn 07a-2 deterministic final renderer",
            "Description": "Selected 2-device-pixel final renderer state",
        },
    )
    plt.close(fig)
    return {
        "marker_counts_sorted": marker_counts_sorted,
        "marker_counts_by_panel": marker_counts_by_panel,
    }


def inspect_pdf(path: Path):
    document = fitz.open(path)
    if document.page_count != 1:
        raise RuntimeError("final PDF is not a one-page document")
    page = document[0]
    rectangle = page.rect
    record = {
        "path": str(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "page_count": document.page_count,
        "page_width_pt": float(rectangle.width),
        "page_height_pt": float(rectangle.height),
        "page_width_cm": float(rectangle.width / 72 * 2.54),
        "page_height_cm": float(rectangle.height / 72 * 2.54),
        "embedded_image_count": len(page.get_images(full=True)),
        "vector_drawing_count": len(page.get_drawings()),
        "extractable_text_characters": len(page.get_text()),
        "render_dpi": PNG_DPI,
        "raster_scientific_layer_dpi": PNG_DPI,
    }
    document.close()
    return record


def inspect_svg(path: Path):
    root = ET.parse(path).getroot()
    elements = list(root.iter())
    local_names = [element.tag.rsplit("}", 1)[-1] for element in elements]
    width = root.attrib.get("width")
    height = root.attrib.get("height")

    def points(value):
        if not value or not value.endswith("pt"):
            raise RuntimeError(f"unexpected SVG page unit: {value}")
        return float(value[:-2])

    width_pt = points(width)
    height_pt = points(height)
    return {
        "path": str(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "root_width": width,
        "root_height": height,
        "viewBox": root.attrib.get("viewBox"),
        "page_width_pt": width_pt,
        "page_height_pt": height_pt,
        "page_width_cm": width_pt / 72 * 2.54,
        "page_height_cm": height_pt / 72 * 2.54,
        "image_element_count": local_names.count("image"),
        "text_element_count": local_names.count("text"),
        "path_element_count": local_names.count("path"),
        "pattern_element_count": local_names.count("pattern"),
        "clipPath_element_count": local_names.count("clipPath"),
        "render_dpi": PNG_DPI,
        "raster_scientific_layer_dpi": PNG_DPI,
    }


def final_output_png_records(selected):
    source_to_target = {
        condition: FIGURE_DIR / FINAL_NAMES[condition] for condition in CONDITIONS
    }
    for condition, target in source_to_target.items():
        shutil.copyfile(Path(selected[condition]["file"]["path"]), target)
    shutil.copyfile(
        Path(selected["double_color"]["file"]["path"]),
        FIGURE_DIR / FINAL_NAMES["final_png"],
    )
    records = {
        condition: inspect_png(
            target,
            CONDITIONS[condition]["pixel_width"],
            CONDITIONS[condition]["grayscale"],
        )
        for condition, target in source_to_target.items()
    }
    records["final_png"] = inspect_png(
        FIGURE_DIR / FINAL_NAMES["final_png"], 2067, False
    )
    for condition in CONDITIONS:
        source_hash = selected[condition]["file"]["sha256"]
        records[condition]["adjudicated_candidate_path"] = selected[condition]["file"]["path"]
        records[condition]["adjudicated_candidate_sha256"] = source_hash
        records[condition]["byte_identical_to_adjudicated_candidate"] = (
            records[condition]["sha256"] == source_hash
        )
        if not records[condition]["byte_identical_to_adjudicated_candidate"]:
            raise RuntimeError(f"final print test is not byte-identical: {condition}")
    final_hash = records["final_png"]["sha256"]
    double_hash = records["double_color"]["sha256"]
    records["final_png"]["byte_identical_to_double_color_print_test"] = (
        final_hash == double_hash
    )
    records["final_png"]["byte_identical_to_adjudicated_double_color_candidate"] = (
        final_hash == selected["double_color"]["file"]["sha256"]
    )
    if not all(
        records["final_png"][key]
        for key in (
            "byte_identical_to_double_color_print_test",
            "byte_identical_to_adjudicated_double_color_candidate",
        )
    ):
        raise RuntimeError("final.png byte-identity contract failed")
    return records


def selected_coverage_records(selected):
    fields = (
        "condition",
        "intended_width_cm",
        "color_mode",
        "panels",
        "b_to_a_display_coverage_ratio",
        "inflation_vs_exact_count_ratio",
        "exact_count_ratio_231_over_183507",
        "same_roi_dimensions_a_b",
        "same_data_to_device_scale_a_b",
        "a_b_scale_matrix_max_abs_difference",
        "same_primitive",
        "same_side_px",
        "same_alpha",
        "same_antialiasing",
        "same_coordinate_transform_rule",
        "physical_mark_side_mm",
    )
    return {
        condition: {key: record[key] for key in fields}
        for condition, record in selected.items()
    }


def write_final_manifest(
    control_records,
    immutable_records,
    search,
    grok,
    claude,
    selected,
    candidate_hash_checks,
    png_records,
    pdf_record,
    svg_record,
    marker_count_state,
):
    script_path = Path(__file__).resolve()
    script_record = {
        "path": str(script_path),
        "sha256": sha256(script_path),
        "size_bytes": script_path.stat().st_size,
        "adapted_from_candidate_renderer_sha256": ADAPTED_FROM_SHA256,
    }
    outputs = {
        "pdf": pdf_record,
        "svg": svg_record,
        "final_png": png_records["final_png"],
        "single_color": png_records["single_color"],
        "single_grayscale": png_records["single_grayscale"],
        "double_color": png_records["double_color"],
        "double_grayscale": png_records["double_grayscale"],
        "renderer": script_record,
        "manifest": {
            "path": str(FINAL_MANIFEST_PATH),
            "sha256": None,
            "size_bytes": None,
            "self_hash_note": "The exact manifest-file hash is recorded in the external S4 executor because a file cannot contain its own SHA-256 without changing it.",
        },
    }
    manifest = {
        "schema_version": "turn07a2-final-render-v2",
        "turn_id": "T1_codex1_abfbc5",
        "scope_completed": ["S4"],
        "visual_gate_status": "FINAL_RECHECK_PENDING",
        "raw_request": control_records["raw_request"],
        "corrected_source_packet": {
            **control_records["corrected_source_packet"],
            "correction_honored": "SVG restored; exact nine-file package enforced",
        },
        "grok_candidate_gate": {
            **control_records["grok_candidate_gate"],
            "selected_candidate_px": grok["selected_candidate_px"],
            "option_A_fallback": grok["option_A_fallback"],
            "all_16_hashes_match_index": grok["all_16_hashes_match_index"],
            "independently_rehashed_candidate_files": candidate_hash_checks,
        },
        "claude_caption_minimality_precheck": {
            **control_records["claude_caption_precheck"],
            "verdict": claude["verdict"],
            "advisory_only": True,
            "role_boundary": claude["role_boundary"],
        },
        "other_control_evidence": {
            key: value
            for key, value in control_records.items()
            if key
            not in {
                "raw_request",
                "corrected_source_packet",
                "grok_candidate_gate",
                "claude_caption_precheck",
            }
        },
        "selected_display_state": {
            "side_px": SELECTED_SIDE_PX,
            "dpi": PNG_DPI,
            "side_mm": SELECTED_SIDE_PX * 25.4 / PNG_DPI,
            "primitive": "matplotlib PathCollection square marker",
            "marker_counts_sorted": marker_count_state["marker_counts_sorted"],
            "marker_counts_by_panel": marker_count_state["marker_counts_by_panel"],
            "one_exact_centre_square_per_stored_positive": True,
            "counts": {"a": 183507, "b": 231},
            "same_primitive_alpha_antialias_transform_a_b": True,
            "alpha": MARK_ALPHA,
            "antialiasing": MARK_ANTIALIASED,
            "transform": "source cell-centre map coordinates through each equal-size panel's ax.transData",
            "common_full_yecheon_extent": [
                float(value) for value in DATA["dem_meta"]["bounds"]
            ],
            "layout_order_palette_unchanged_from_turn07a2_candidate_renderer": True,
        },
        "input_and_frozen_hashes_before_after": immutable_records,
        "coverage_metrics_by_condition": selected_coverage_records(selected),
        "vector_raster_composition": {
            "pdf_and_svg_from_one_live_figure_state": True,
            "page_width_cm": 17.5,
            "page_height_cm": 17.5 * HEIGHT_TO_WIDTH,
            "vector_components": [
                "text",
                "administrative and locator boundaries",
                "hatches",
                "north arrow",
                "scale bars",
                "legend symbols",
            ],
            "raster_components": [
                "held DEM images",
                "the two selected scientific pixel-support PathCollections rasterized at 300 dpi for vector-container efficiency",
            ],
            "pathcollection_source_geometry_verified_before_rasterization": (
                marker_count_state["marker_counts_sorted"] == [231, 183507]
                and marker_count_state["marker_counts_by_panel"]
                == {"a": 183507, "b": 231}
            ),
            "pdf_direct_inspection": {
                "embedded_image_count": pdf_record["embedded_image_count"],
                "vector_drawing_count": pdf_record["vector_drawing_count"],
                "extractable_text_characters": pdf_record[
                    "extractable_text_characters"
                ],
            },
            "svg_direct_inspection": {
                key: svg_record[key]
                for key in (
                    "image_element_count",
                    "text_element_count",
                    "path_element_count",
                    "pattern_element_count",
                    "clipPath_element_count",
                )
            },
        },
        "forbidden_operation_guards": {
            **search["forbidden_operations"],
            "all_false": not any(search["forbidden_operations"].values()),
        },
        "outputs": outputs,
        "package_contract": {
            "expected_exact_names": sorted(FINAL_NAMES.values()),
            "expected_file_count": 9,
            "no_pycache": True,
        },
        "final_render_checks": {
            "grok_selected_exactly_2px": True,
            "option_A_fallback_false": True,
            "all_16_candidate_hashes_reverified": len(candidate_hash_checks) == 16,
            "claude_precheck_advisory_only": True,
            "four_print_tests_byte_identical_to_adjudicated_candidates": all(
                png_records[key]["byte_identical_to_adjudicated_candidate"]
                for key in CONDITIONS
            ),
            "final_png_byte_identical_to_double_color_candidate_and_print_test": all(
                png_records["final_png"][key]
                for key in (
                    "byte_identical_to_double_color_print_test",
                    "byte_identical_to_adjudicated_double_color_candidate",
                )
            ),
            "immutable_before_after_match": all(
                record["before_after_match"] for record in immutable_records.values()
            ),
            "pdf_svg_page_width_17_5cm_with_tolerance": all(
                abs(record["page_width_cm"] - 17.5) < 0.001
                for record in (pdf_record, svg_record)
            ),
            "no_final_visual_self_approval": True,
        },
    }
    FINAL_MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def write_render_executor(manifest, control_records, candidate_hash_checks):
    package_files = sorted(path.name for path in FIGURE_DIR.iterdir())
    expected_files = sorted(FINAL_NAMES.values())
    if package_files != expected_files:
        raise RuntimeError(
            f"final package is not exactly nine files: {package_files}"
        )
    manifest_hash = sha256(FINAL_MANIFEST_PATH)
    output_records = {
        key: {
            "path": record["path"],
            "sha256": record["sha256"],
            "size_bytes": record["size_bytes"],
        }
        for key, record in manifest["outputs"].items()
        if key != "manifest"
    }
    output_records["manifest"] = {
        "path": str(FINAL_MANIFEST_PATH),
        "sha256": manifest_hash,
        "size_bytes": FINAL_MANIFEST_PATH.stat().st_size,
    }
    executor = {
        "schema_version": "turn07a2-final-render-executor-v1",
        "turn_id": "T1_codex1_abfbc5",
        "role": "primary final renderer",
        "scope_completed": ["S4"],
        "commands": [
            "PYTHONDONTWRITEBYTECODE=1 /Users/eungyupark/anaconda3/bin/python /Users/eungyupark/Dropbox/Manuscripts/0_Landslides/round_3/figures/turn07a2/render_figure2_turn07a2.py",
            "independent Pillow/Fitz/XML/hash/package inspection embedded in renderer",
        ],
        "preflight": {
            "status": "PASS",
            "control_evidence": control_records,
            "candidate_hashes_independently_rechecked": candidate_hash_checks,
        },
        "invariants": manifest["selected_display_state"],
        "files": output_records,
        "direct_deterministic_inspection": {
            "package_exactly_nine_files": package_files == expected_files,
            "package_names": package_files,
            "png_dimensions_dpi_channels_and_hashes_checked_with_pillow": True,
            "pdf_page_images_drawings_and_text_checked_with_fitz": True,
            "svg_page_images_text_paths_patterns_and_clips_checked_with_xml": True,
            "all_immutable_inputs_rehashed_before_and_after": True,
            "all_four_candidate_copy_links_byte_identical": True,
            "final_png_double_color_link_byte_identical": True,
        },
        "failures_and_repairs": [
            {
                "failure": "The earlier source packet omitted SVG and described eight files.",
                "repair": "The corrected packet hash was required and the SVG was restored, producing exactly nine files.",
            },
            {
                "failure": "A self-contained manifest cannot contain its own final file SHA-256 without changing that SHA-256.",
                "repair": "The manifest explicitly marks its self-hash as external; this executor records the exact manifest hash and size.",
            },
        ],
        "scope_exclusions_honored": {
            "final_report_not_written": True,
            "caption_not_written": True,
            "editorial_rows_not_written": True,
            "final_grok_or_claude_gates_not_written": True,
            "remaining_791_manuscript_words_not_written": True,
        },
        "visual_gate_status": "FINAL_RECHECK_PENDING",
        "no_self_visual_approval": "This S4 executor makes no final visual-gate approval. It performs deterministic inspection only; independent Grok/Claude final recheck remains pending.",
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "rasterio": rasterio.__version__,
            "geopandas": gpd.__version__,
            "pymupdf": fitz.VersionBind,
        },
    }
    final_executor_path = EVIDENCE_DIR / "turn07a2_render_executor.json"
    final_executor_path.write_text(
        json.dumps(executor, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return final_executor_path


def final_main():
    global DATA
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams.update(
        {
            "font.family": "Times New Roman",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "turn07a2-side02-final",
            "axes.unicode_minus": False,
            "image.interpolation": "nearest",
            "hatch.linewidth": 0.45,
        }
    )
    (
        control_records,
        immutable_before,
        search,
        grok,
        claude,
        selected,
        candidate_hash_checks,
    ) = final_control_preflight()
    DATA = read_inputs()
    png_records = final_output_png_records(selected)
    pdf_path = FIGURE_DIR / FINAL_NAMES["pdf"]
    svg_path = FIGURE_DIR / FINAL_NAMES["svg"]
    marker_count_state = render_final_vectors(pdf_path, svg_path)
    pdf_record = inspect_pdf(pdf_path)
    svg_record = inspect_svg(svg_path)
    immutable_records = immutable_after_records(immutable_before)
    manifest = write_final_manifest(
        control_records,
        immutable_records,
        search,
        grok,
        claude,
        selected,
        candidate_hash_checks,
        png_records,
        pdf_record,
        svg_record,
        marker_count_state,
    )
    executor_path = write_render_executor(
        manifest, control_records, candidate_hash_checks
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "scope_completed": "S4",
                "visual_gate_status": "FINAL_RECHECK_PENDING",
                "package_file_count": len(list(FIGURE_DIR.iterdir())),
                "package_files": sorted(path.name for path in FIGURE_DIR.iterdir()),
                "manifest_sha256": sha256(FINAL_MANIFEST_PATH),
                "executor": str(executor_path),
                "executor_sha256": sha256(executor_path),
            },
            indent=2,
        )
    )


TURN11_FIGURE_DIR = ROUND3 / "figures/turn11"
TURN11_EVIDENCE_DIR = ROUND3 / "turn11_evidence"
TURN11_REDUCTION_FRACTION = 0.40
TURN11_WIDTH_CM = 17.5
TURN11_ORIGINAL_HEIGHT_CM = 19.6
TURN11_HEIGHT_CM = TURN11_ORIGINAL_HEIGHT_CM * (1.0 - TURN11_REDUCTION_FRACTION)
TURN11_HEIGHT_TO_WIDTH = TURN11_HEIGHT_CM / TURN11_WIDTH_CM
TURN11_PIXEL_WIDTH = 2067
TURN11_PIXEL_HEIGHT = round(TURN11_PIXEL_WIDTH * TURN11_HEIGHT_TO_WIDTH)
TURN11_CAPTION = (
    "Figure 2. Yecheon validation targets over common topography: (a) Sentinel "
    "and (b) stored national-inventory pixel labels, and (c) forest-service and "
    "(d) Sentinel labels on identical administrative units. The inset locates all "
    "three event areas. Small marks are enlarged for visibility; their locations "
    "and counts are unchanged."
)
TURN11_NAMES = {
    "pdf": "fig02_validation_supports_turn11_c40.pdf",
    "svg": "fig02_validation_supports_turn11_c40.svg",
    "png": "fig02_validation_supports_turn11_c40.png",
    "gate_color": "figure2_turn11_c40_final_size_color.png",
    "gate_grayscale": "figure2_turn11_c40_final_size_grayscale.png",
    "manifest": "figure2_turn11_c40_manifest.json",
}
TURN11_LOCKED_BASELINES = {
    "turn07a2_renderer": {
        "path": ROUND3 / "figures/turn07a2/render_figure2_turn07a2.py",
        "sha256": "1f781c138e9b0f322d22c93e7fe1c7c25e4f860ee57fb211ccf9fc1d2729ba2a",
    },
    "turn07a2_manifest": {
        "path": ROUND3 / "figures/turn07a2/figure2_render_v2_manifest.json",
        "sha256": "588f1d9c901d106953c6ce8fa9655051887ea8b8c2d19cfb811d24d44808dc31",
    },
    "turn07a2_pdf": {
        "path": ROUND3 / "figures/turn07a2/fig02_validation_supports_v2_final.pdf",
        "sha256": "555d90e11cd0fb47bb37cbb2689de0fe2349436a083c11251fb3d03f3959aaad",
    },
    "turn07a2_png": {
        "path": ROUND3 / "figures/turn07a2/fig02_validation_supports_v2_final.png",
        "sha256": "cfb007bed974c5c9fdcfefed42b3befdbf2a21c992c791ebc5b66bf3cea36e80",
    },
    "turn10_manuscript_source": {
        "path": ROUND3 / "turn10_build/manuscript_source.md",
        "sha256": "69ae2c33e962dd10e8fbabe548196d407c4f682797cc4719ab743b2cc08957b1",
    },
    "turn10_supplement": {
        "path": ROUND3 / "supplement_BC_NHESS.md",
        "sha256": "0e69f7f53a23b94379c6efcd2a46c700851bfb233b30f99283bd3666dfe03715",
    },
    "editorial_decisions": {
        "path": ROUND3 / "editorial_decisions.md",
        "sha256": "1ce52d788748bfbb5cbb3b4d16939a66bee411069d511732240ee9a81d594031",
    },
}


def turn11_locked_records(stage):
    records = {}
    for name, expected in TURN11_LOCKED_BASELINES.items():
        path = expected["path"]
        actual = sha256(path)
        if actual != expected["sha256"]:
            raise RuntimeError(f"Turn 11 locked baseline mismatch ({stage}): {name}")
        stat = path.stat()
        records[name] = {
            "path": str(path),
            "sha256": actual,
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
    return records


def create_layout_turn11(pixel_width, transparent=False):
    """Two rows by three columns: locator/a/b above key/c/d.

    Every scientific detail panel receives the same GridSpec cell and the same
    full held-data extent.  The rearrangement removes the former mostly-empty
    locator/key strip while leaving data and display primitives unchanged.
    """
    pixel_height = round(pixel_width * TURN11_HEIGHT_TO_WIDTH)
    fig = plt.figure(
        figsize=(pixel_width / PNG_DPI, pixel_height / PNG_DPI),
        dpi=PNG_DPI,
        facecolor="none" if transparent else "white",
    )
    grid = fig.add_gridspec(
        2,
        3,
        height_ratios=[1.0, 1.0],
        width_ratios=[1.0, 1.0, 1.0],
        left=0.018,
        right=0.992,
        bottom=0.026,
        top=0.985,
        wspace=0.025,
        hspace=0.045,
    )
    locator_ax = fig.add_subplot(grid[0, 0])
    legend_ax = fig.add_subplot(grid[1, 0])
    detail_axes = [
        fig.add_subplot(grid[0, 1]),
        fig.add_subplot(grid[0, 2]),
        fig.add_subplot(grid[1, 1]),
        fig.add_subplot(grid[1, 2]),
    ]
    if transparent:
        fig.patch.set_alpha(0.0)
        for ax in [locator_ax, legend_ax, *detail_axes]:
            ax.patch.set_alpha(0.0)
    return fig, locator_ax, legend_ax, detail_axes


def draw_legend_turn11(ax, grayscale, font_size):
    ax.set_axis_off()
    ax.text(
        0.04,
        0.965,
        "Integrated figure key",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=font_size + 0.4,
        fontweight="bold",
        color=PALETTE["text"],
    )
    ax.legend(
        handles=legend_handles(grayscale),
        loc="upper left",
        bbox_to_anchor=(0.04, 0.87),
        frameon=False,
        fontsize=font_size,
        handlelength=1.75,
        handleheight=0.70,
        borderaxespad=0.0,
        labelspacing=0.42,
        columnspacing=0.7,
        ncol=1,
    )
    ax.text(
        0.04,
        0.12,
        "Small marks are enlarged for visibility",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=max(font_size - 0.2, 5.0),
        fontstyle="italic",
        color=PALETTE["text"],
    )


def build_figure_turn11(pixel_width, grayscale, side_px):
    fig, locator_ax, legend_ax, detail_axes = create_layout_turn11(pixel_width)
    font_size = 6.35
    line_width = 0.90
    draw_locator(locator_ax, DATA, grayscale, font_size, line_width)
    draw_legend_turn11(legend_ax, grayscale, font_size)
    for ax, panel in zip(detail_axes, ("a", "b", "c", "d")):
        draw_detail_panel(ax, DATA, panel, grayscale, font_size, line_width, side_px)
    add_shared_north_arrow(detail_axes[1], font_size, line_width)
    return fig, detail_axes


def save_turn11_png(path, grayscale):
    fig, _ = build_figure_turn11(TURN11_PIXEL_WIDTH, grayscale, SELECTED_SIDE_PX)
    fig.savefig(
        path,
        dpi=PNG_DPI,
        facecolor="white",
        metadata={
            "Software": "Turn 11 deterministic layout-only renderer",
            "Figure": "Figure 2 40 percent vertical-compression candidate",
        },
        pil_kwargs={"compress_level": 6},
    )
    plt.close(fig)


def turn11_geometry_and_coverage():
    pixel_width = TURN11_PIXEL_WIDTH
    pixel_height = TURN11_PIXEL_HEIGHT
    fig, _, _, axes = create_layout_turn11(pixel_width, transparent=True)
    for ax in axes:
        set_detail_extent(ax, DATA)
    scatter_positive_marks(axes[0], DATA["centres"]["a"], SELECTED_SIDE_PX, "#000000")
    scatter_positive_marks(axes[1], DATA["centres"]["b"], SELECTED_SIDE_PX, "#000000")
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba()).copy()
    renderer = fig.canvas.get_renderer()
    panels = {}
    for panel, ax in zip(("a", "b"), axes[:2]):
        bbox = ax.get_window_extent(renderer)
        row_slice, col_slice, roi_index = roi_array_slice(bbox, pixel_width, pixel_height)
        alpha = rgba[row_slice, col_slice, 3]
        record = panel_geometry_record(ax, DATA["centres"][panel], bbox)
        record.update(
            {
                "map_roi_width_px": int(alpha.shape[1]),
                "map_roi_height_px": int(alpha.shape[0]),
                "map_roi_total_px": int(alpha.size),
                "coverage_pixels": int(np.count_nonzero(alpha > 0)),
                "coverage_ratio": float(np.count_nonzero(alpha > 0) / alpha.size),
                "roi_index": roi_index,
            }
        )
        panels[panel] = record
    matrices = [ax.transData.get_affine().get_matrix() for ax in axes]
    ab_diff = float(np.max(np.abs(matrices[0][:2, :2] - matrices[1][:2, :2])))
    all_detail_scale_equal = all(
        np.allclose(matrices[0][:2, :2], matrix[:2, :2], atol=1e-15, rtol=1e-12)
        for matrix in matrices[1:]
    )
    bbox_shapes = [
        [float(ax.get_window_extent(renderer).width), float(ax.get_window_extent(renderer).height)]
        for ax in axes
    ]
    plt.close(fig)
    return {
        "panels": panels,
        "all_four_detail_grid_cells_same_bbox": all(
            np.allclose(bbox_shapes[0], shape, atol=1e-9, rtol=0) for shape in bbox_shapes[1:]
        ),
        "detail_axes_bbox_width_height_px": bbox_shapes,
        "same_data_to_device_scale_all_four": bool(all_detail_scale_equal),
        "a_b_scale_matrix_max_abs_difference": ab_diff,
        "same_primitive_a_b": "matplotlib PathCollection square marker",
        "same_side_px_a_b": SELECTED_SIDE_PX,
        "same_alpha_a_b": MARK_ALPHA,
        "same_antialiasing_a_b": MARK_ANTIALIASED,
        "same_coordinate_transform_rule_a_b": (
            "source cell-centre map coordinates through equal-size axes ax.transData"
        ),
        "common_full_extent_all_four": [float(v) for v in DATA["dem_meta"]["bounds"]],
        "physical_mark_side_mm": SELECTED_SIDE_PX * 25.4 / PNG_DPI,
    }


def render_turn11_vectors(pdf_path, svg_path):
    fig, detail_axes = build_figure_turn11(
        TURN11_PIXEL_WIDTH, grayscale=False, side_px=SELECTED_SIDE_PX
    )
    fig.set_size_inches(TURN11_WIDTH_CM / 2.54, TURN11_HEIGHT_CM / 2.54, forward=True)
    marker_counts = {}
    collections = []
    for panel, ax in zip(("a", "b"), detail_axes[:2]):
        matches = [c for c in ax.collections if isinstance(c, PathCollection)]
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one PathCollection in panel {panel}")
        marker_counts[panel] = int(len(matches[0].get_offsets()))
        collections.append(matches[0])
    if marker_counts != {"a": 183507, "b": 231}:
        raise RuntimeError(f"Turn 11 marker count drift: {marker_counts}")
    for collection in collections:
        collection.set_rasterized(True)
    fixed_time = dt.datetime(2026, 8, 30, 0, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    fig.savefig(
        pdf_path,
        format="pdf",
        dpi=PNG_DPI,
        facecolor="white",
        metadata={
            "Title": "Figure 2 Turn 11 40 percent vertical-compression candidate",
            "Author": "Eungyu Park; Hyung-Sup Jung; Taeyu Kim; Jangwon Park",
            "Subject": "Layout-only candidate; independent visual gate pending",
            "Creator": "Turn 11 deterministic layout-only renderer",
            "CreationDate": fixed_time,
            "ModDate": fixed_time,
        },
    )
    fig.savefig(
        svg_path,
        format="svg",
        dpi=PNG_DPI,
        facecolor="white",
        metadata={
            "Title": "Figure 2 Turn 11 40 percent vertical-compression candidate",
            "Date": fixed_time.isoformat(),
            "Creator": "Turn 11 deterministic layout-only renderer",
            "Description": "Layout-only candidate; independent visual gate pending",
        },
    )
    plt.close(fig)
    return marker_counts


def inspect_turn11_png(path, grayscale):
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"))
        info = dict(image.info)
        size = list(image.size)
    dpi = info.get("dpi")
    channels_equal = bool(
        np.array_equal(rgb[:, :, 0], rgb[:, :, 1])
        and np.array_equal(rgb[:, :, 1], rgb[:, :, 2])
    )
    if size != [TURN11_PIXEL_WIDTH, TURN11_PIXEL_HEIGHT]:
        raise RuntimeError(f"unexpected Turn 11 PNG dimensions: {path}: {size}")
    if grayscale != channels_equal:
        raise RuntimeError(f"unexpected Turn 11 PNG colour mode: {path}")
    return {
        "path": str(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "pixel_dimensions": size,
        "dpi_metadata": list(dpi) if dpi else None,
        "channels_equal_grayscale": channels_equal,
    }


def turn11_main():
    global DATA
    TURN11_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TURN11_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams.update(
        {
            "font.family": "Times New Roman",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "turn11-c40-layout",
            "axes.unicode_minus": False,
            "image.interpolation": "nearest",
            "hatch.linewidth": 0.45,
        }
    )
    before = turn11_locked_records("before")
    held_source_hashes = verify_preflight_and_sources()
    DATA = read_inputs()

    png_path = TURN11_FIGURE_DIR / TURN11_NAMES["png"]
    gate_color_path = TURN11_FIGURE_DIR / TURN11_NAMES["gate_color"]
    gate_gray_path = TURN11_FIGURE_DIR / TURN11_NAMES["gate_grayscale"]
    pdf_path = TURN11_FIGURE_DIR / TURN11_NAMES["pdf"]
    svg_path = TURN11_FIGURE_DIR / TURN11_NAMES["svg"]
    manifest_path = TURN11_FIGURE_DIR / TURN11_NAMES["manifest"]

    save_turn11_png(png_path, grayscale=False)
    shutil.copyfile(png_path, gate_color_path)
    save_turn11_png(gate_gray_path, grayscale=True)
    marker_counts = render_turn11_vectors(pdf_path, svg_path)
    geometry = turn11_geometry_and_coverage()

    png_record = inspect_turn11_png(png_path, False)
    color_record = inspect_turn11_png(gate_color_path, False)
    gray_record = inspect_turn11_png(gate_gray_path, True)
    if png_record["sha256"] != color_record["sha256"]:
        raise RuntimeError("colour gate image is not byte-identical to candidate PNG")
    pdf_record = inspect_pdf(pdf_path)
    svg_record = inspect_svg(svg_path)
    for record in (pdf_record, svg_record):
        if abs(record["page_width_cm"] - TURN11_WIDTH_CM) >= 0.001:
            raise RuntimeError("Turn 11 vector width drift")
        if abs(record["page_height_cm"] - TURN11_HEIGHT_CM) >= 0.001:
            raise RuntimeError("Turn 11 vector height drift")

    after = turn11_locked_records("after")
    baseline_records = {
        name: {
            **before[name],
            "after_sha256": after[name]["sha256"],
            "after_size_bytes": after[name]["size_bytes"],
            "after_mtime_ns": after[name]["mtime_ns"],
            "unchanged": before[name] == after[name],
        }
        for name in before
    }
    if not all(record["unchanged"] for record in baseline_records.values()):
        raise RuntimeError("locked baseline metadata or content changed during Turn 11 render")

    caption_bytes = TURN11_CAPTION.encode("utf-8")
    caption_words = len(TURN11_CAPTION.split())
    if caption_words != 46:
        raise RuntimeError(f"Figure 2 caption word-count drift: {caption_words}")
    manifest = {
        "schema_version": "turn11-figure2-candidate-v1",
        "status": "CANDIDATE_READY_VISUAL_GATE_PENDING",
        "visual_gate_status": "UNJUDGED",
        "self_visual_approval": False,
        "candidate_id": "c40",
        "layout_change_only": True,
        "layout": {
            "arrangement": "2 rows x 3 columns: locator/a/b above key/c/d",
            "original_width_cm": TURN11_WIDTH_CM,
            "original_height_cm": TURN11_ORIGINAL_HEIGHT_CM,
            "candidate_width_cm": TURN11_WIDTH_CM,
            "candidate_height_cm": TURN11_HEIGHT_CM,
            "vertical_reduction_cm": TURN11_ORIGINAL_HEIGHT_CM - TURN11_HEIGHT_CM,
            "vertical_reduction_percent": 100 * TURN11_REDUCTION_FRACTION,
            "candidate_pixel_dimensions_at_300_dpi": [
                TURN11_PIXEL_WIDTH,
                TURN11_PIXEL_HEIGHT,
            ],
        },
        "caption": {
            "text": TURN11_CAPTION,
            "utf8_sha256": hashlib.sha256(caption_bytes).hexdigest(),
            "utf8_size_bytes": len(caption_bytes),
            "word_count_whitespace_tokenization": caption_words,
            "required_exact_word_count": 46,
            "byte_for_byte_unchanged_from_turn10_source": (
                TURN11_CAPTION in TURN11_LOCKED_BASELINES["turn10_manuscript_source"]["path"].read_text(encoding="utf-8")
            ),
        },
        "data_and_display_invariants": {
            "held_source_hashes": held_source_hashes,
            "source_grid_shape": DATA["dem_meta"]["shape"],
            "source_crs": DATA["dem_meta"]["crs"],
            "source_transform": [float(v) for v in DATA["dem_meta"]["transform_tuple"]],
            "common_full_extent": [float(v) for v in DATA["dem_meta"]["bounds"]],
            "positive_counts": {
                "a_sentinel_pixel": 183507,
                "b_stored_national_inventory_pixel": 231,
                "c_forest_service_admin": 4,
                "d_sentinel_admin": 176,
                "admin_denominator": 205,
            },
            "marker_counts_verified_in_live_vector_state": marker_counts,
            "selected_side_device_pixels": SELECTED_SIDE_PX,
            "selected_side_mm_at_300_dpi": SELECTED_SIDE_PX * 25.4 / PNG_DPI,
            "marker_alpha": MARK_ALPHA,
            "marker_antialiasing": MARK_ANTIALIASED,
            "all_panels_and_three_event_locator_present": True,
            "small_marks_note_preserved_in_exact_caption": (
                "Small marks are enlarged for visibility" in TURN11_CAPTION
            ),
            "geometry_and_coverage": geometry,
        },
        "locked_baselines_before_after": baseline_records,
        "outputs": {
            "pdf": pdf_record,
            "svg": svg_record,
            "png": png_record,
            "final_typeset_size_color_gate": {
                **color_record,
                "byte_identical_to_candidate_png": True,
            },
            "final_typeset_size_grayscale_gate": gray_record,
            "renderer": {
                "path": str(Path(__file__).resolve()),
                "sha256": sha256(Path(__file__).resolve()),
                "size_bytes": Path(__file__).stat().st_size,
                "copied_exactly_from_turn07a2_before_turn11_layout_patch": True,
                "turn07a2_source_sha256": TURN11_LOCKED_BASELINES["turn07a2_renderer"]["sha256"],
            },
        },
        "independent_gate_request": {
            "reviewer": "Grok (orchestrator-owned independent gate)",
            "must_inspect_at_final_typeset_size": True,
            "files": [str(gate_color_path), str(gate_gray_path)],
            "required_gates": ["G1", "G1b", "G4", "G5", "G6"],
            "result": None,
        },
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "rasterio": rasterio.__version__,
            "geopandas": gpd.__version__,
            "pymupdf": fitz.VersionBind,
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "visual_gate_status": manifest["visual_gate_status"],
                "vertical_reduction_percent": 40.0,
                "physical_dimensions_cm": [TURN11_WIDTH_CM, TURN11_HEIGHT_CM],
                "pixel_dimensions": [TURN11_PIXEL_WIDTH, TURN11_PIXEL_HEIGHT],
                "gate_color": {"path": str(gate_color_path), "sha256": sha256(gate_color_path)},
                "gate_grayscale": {"path": str(gate_gray_path), "sha256": sha256(gate_gray_path)},
                "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    turn11_main()
