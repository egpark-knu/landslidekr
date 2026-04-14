"""
Agent orchestrator tests — dry-run should produce trace + artifacts without any external call.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from landslide_kr.io.case_config import CaseConfig
from landslide_kr.agent.orchestrator import LandslideAgent


def _load_cfg() -> CaseConfig:
    cfg_path = Path(__file__).resolve().parent.parent / "cases" / "pohang_2022" / "config.json"
    return CaseConfig.from_json(cfg_path)


def test_dry_run_produces_trace():
    cfg = _load_cfg()
    agent = LandslideAgent(cfg)
    result = agent.run(dry_run=True)
    assert result.status == "dry-run"
    assert result.trace is not None
    assert len(result.trace) == 4  # rain, scars, nidr, model
    step_names = {s["step"] for s in result.trace}
    assert step_names == {"fetch_rainfall", "detect_scars", "fetch_nidr", "run_model"}


def test_skip_step():
    cfg = _load_cfg()
    agent = LandslideAgent(cfg)
    result = agent.run(dry_run=True, skip={"detect_scars"})
    assert "scars" not in result.artifacts
    assert "rain" in result.artifacts


def test_trace_is_saved():
    cfg = _load_cfg()
    agent = LandslideAgent(cfg)
    result = agent.run(dry_run=True)
    trace_path = agent.work_dir / "agent_trace.json"
    assert trace_path.exists()
    with open(trace_path) as f:
        saved = json.load(f)
    assert len(saved) == 4


def test_case_config_has_all_fields():
    cfg = _load_cfg()
    assert cfg.case_id == "pohang_2022"
    assert cfg.event_window.start == "2022-09-05"
    assert len(cfg.aoi.bbox) == 4
    assert cfg.model_name == "SHALSTAB"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
