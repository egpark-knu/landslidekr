#!/usr/bin/env python3
"""
Case runner — reads config.json, loads DEM/rainfall/labels, runs model, writes outputs.

WildfireKR 패턴 참고: run_goseong_fixed.py, run_uljin.py 등.

Usage:
    python scripts/run_case.py cases/pohang_2022/config.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure package importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from landslide_kr.io.case_config import CaseConfig


def run_case(config_path: Path, dry_run: bool = False) -> dict:
    """Run a single case end-to-end."""
    print(f"\n{'='*70}")
    print(f"Case Runner — {config_path.name}")
    print(f"{'='*70}")

    cfg = CaseConfig.from_json(config_path)
    print(f"  Case ID: {cfg.case_id}")
    print(f"  Event: {cfg.event_window.start} → {cfg.event_window.end}")
    print(f"  AOI bbox: {cfg.aoi.bbox}")
    print(f"  Model: {cfg.model_name}")
    print(f"  Params: {cfg.model_params}")

    # Delegate to LandslideAgent (LLM-Agent orchestrator)
    from landslide_kr.agent.orchestrator import LandslideAgent

    agent = LandslideAgent(cfg)
    result = agent.run(dry_run=dry_run)

    return {
        "case_id": result.case_id,
        "status": result.status,
        "config_ok": True,
        "artifacts": result.artifacts,
        "metrics": result.metrics,
        "n_trace_steps": len(result.trace) if result.trace else 0,
        "message": result.message,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a single landslide case")
    parser.add_argument("config", type=Path, help="Path to cases/<id>/config.json")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without running")
    args = parser.parse_args()

    if not args.config.exists():
        print(f"❌ Config not found: {args.config}", file=sys.stderr)
        return 1

    result = run_case(args.config, dry_run=args.dry_run)
    print(f"\n✅ Result: {json.dumps(result, indent=2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
