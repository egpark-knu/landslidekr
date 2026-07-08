#!/usr/bin/env python3
"""Regenerate compact reviewer-facing summaries from frozen NHESS tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "frozen_tables"


def rows(name: str) -> list[dict[str, str]]:
    path = DATA / name
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows_: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows_:
            writer.writerow({field: row.get(field, "") for field in fields})


def f4(value: str) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return value


def protocol_skill_summary() -> list[dict[str, object]]:
    selected_fields = [
        "event",
        "scale",
        "label_source",
        "roc_auc",
        "n_positive",
        "n_negative",
        "source_status",
    ]
    output = []
    for row in rows("unified_skill_table.csv"):
        output.append({
            "event": row["event"],
            "scale": row["scale"],
            "label_source": row["label_source"],
            "roc_auc": f4(row["roc_auc"]),
            "n_positive": row["n_positive"],
            "n_negative": row["n_negative"],
            "source_status": row["source_status"],
        })
    return output


def terrain_contrast_summary() -> list[dict[str, object]]:
    output = []
    for row in rows("terrain_contrast_stats.csv"):
        output.append({
            "event": row["event"],
            "label_source": row["label_source"],
            "variable": row["variable"],
            "n_correct": row["n_correct"],
            "n_misranked": row["n_misranked"],
            "correct_mean": f4(row["correct_mean"]),
            "misranked_mean": f4(row["misranked_mean"]),
            "standardized_difference": f4(row["standardized_difference"]),
        })
    return output


def aggregate_reversal_summary() -> list[dict[str, object]]:
    output = []
    for row in rows("aggregate_reversal_anatomy_stats.csv"):
        output.append({
            "variable": row["variable"],
            "positive_n": row["positive_n"],
            "negative_n": row["negative_n"],
            "positive_mean": f4(row["positive_mean"]),
            "negative_mean": f4(row["negative_mean"]),
            "difference_positive_minus_negative": f4(row["difference_positive_minus_negative"]),
            "standardized_difference": f4(row["standardized_difference"]),
        })
    return output


def write_markdown_summary(path: Path) -> None:
    skill = protocol_skill_summary()
    pohang = next(r for r in skill if r["event"] == "Pohang 2022" and r["scale"] == "pixel")
    yecheon_sentinel = next(
        r for r in skill
        if r["event"] == "Yecheon 2023" and r["scale"] == "pixel" and r["label_source"] == "Sentinel scar label"
    )
    yecheon_nidr = next(
        r for r in skill
        if r["event"] == "Yecheon 2023" and r["scale"] == "pixel" and r["label_source"] == "NIDR-only pixel label"
    )
    yecheon_kfs = next(
        r for r in skill
        if r["event"] == "Yecheon 2023" and r["scale"] == "EMD aggregate" and "KFS" in r["label_source"]
    )
    path.write_text(
        "\n".join([
            "# NHESS Frozen-Table Reproduction Summary",
            "",
            "Generated from `data/frozen_tables/` by `scripts/reproduce_summary_tables.py`.",
            "",
            "## Key Checks",
            "",
            f"- Pohang pixel/Sentinel ROC-AUC: {pohang['roc_auc']}.",
            f"- Yecheon pixel/Sentinel ROC-AUC: {yecheon_sentinel['roc_auc']}.",
            f"- Yecheon pixel/NIDR-only ROC-AUC: {yecheon_nidr['roc_auc']}.",
            f"- Yecheon EMD/KFS aggregate ROC-AUC: {yecheon_kfs['roc_auc']}.",
            "",
            "These values preserve the revised manuscript's protocol-dependence finding: the measured signal changes with label source and scale.",
            "",
            "## Generated Files",
            "",
            "- `protocol_skill_summary.csv`",
            "- `terrain_contrast_summary.csv`",
            "- `aggregate_reversal_summary.csv`",
            "",
        ]),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "derived"), help="Output directory for generated summaries")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    write_csv(
        out / "protocol_skill_summary.csv",
        protocol_skill_summary(),
        ["event", "scale", "label_source", "roc_auc", "n_positive", "n_negative", "source_status"],
    )
    write_csv(
        out / "terrain_contrast_summary.csv",
        terrain_contrast_summary(),
        ["event", "label_source", "variable", "n_correct", "n_misranked", "correct_mean", "misranked_mean", "standardized_difference"],
    )
    write_csv(
        out / "aggregate_reversal_summary.csv",
        aggregate_reversal_summary(),
        ["variable", "positive_n", "negative_n", "positive_mean", "negative_mean", "difference_positive_minus_negative", "standardized_difference"],
    )
    write_markdown_summary(out / "README.md")
    print(f"Wrote summaries to {out}")


if __name__ == "__main__":
    main()
