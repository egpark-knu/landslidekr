#!/usr/bin/env python3
"""
Benchmark runner — iterates all case configs, aggregates metrics.

WildfireKR pattern: run_benchmarks.py + benchmark_summary.json.

Usage:
    python scripts/run_benchmarks.py
    python scripts/run_benchmarks.py --cases pohang_2022,extreme_rainfall_2023
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_benchmarks(case_ids: list[str], dry_run: bool = False) -> dict:
    """Run all specified cases, aggregate metrics into summary JSON."""
    cases_dir = PROJECT_ROOT / "cases"
    out_path = PROJECT_ROOT / "data" / "benchmark_summary.json"

    summary = {
        "timestamp": datetime.now().isoformat(),
        "cases_run": [],
        "cases_failed": [],
    }

    for case_id in case_ids:
        cfg_path = cases_dir / case_id / "config.json"
        if not cfg_path.exists():
            print(f"  ⚠️ Config missing: {cfg_path}")
            summary["cases_failed"].append(case_id)
            continue

        print(f"\n▶ Running {case_id}...")
        try:
            from scripts.run_case import run_case
            result = run_case(cfg_path, dry_run=dry_run)
            summary["cases_run"].append(result)
        except Exception as e:
            print(f"  ❌ {case_id} failed: {e}")
            summary["cases_failed"].append({"case_id": case_id, "error": str(e)})

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n✅ Summary saved: {out_path}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default="pohang_2022,extreme_rainfall_2023")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    case_ids = [c.strip() for c in args.cases.split(",") if c.strip()]
    run_benchmarks(case_ids, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
