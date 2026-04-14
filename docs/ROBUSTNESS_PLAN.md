# LandslideKR — Agent Robustness Evaluation Plan

Inherits the WildfireKR (IEEE Access, 2026) robustness template. Codex-98, two academic reviewers, and HP Round 4 (codex-99) all converge on the same diagnosis: the current manuscript does not carry enough robustness evidence to pass *Landslides* review on n=2 alone. This plan lays out the seven-axis evidence package.

All claims here mirror WildfireKR's honesty boundaries: no LLM-physics claims, no regime laws, all experiments pre-specified.

## Axis 1 — LLM-Backend Robustness (E1-analog)

Direct port of WildfireKR Table 16 / Section V-F.4.

| Design element | Value |
|---|---|
| LLM backends | Claude Sonnet 4.6, Claude Haiku 4.5, GPT-5.4, GPT-5.4 mini |
| Scenarios | Pohang 2022 full-spec (S1), Yecheon 2023 descriptor-only (S2), "a recent monsoon event in central Korea" vague (S3) |
| Repetitions | 5 per (LLM × scenario) |
| Total runs | 4 × 3 × 5 = **60 runs** |
| Primary metric | Config validity (binary), parameter accuracy (per-field pass rate), latency |

Report table (mirror of WildfireKR Table 16):
- Config valid (X/15 per LLM)
- Parameter accuracy (overall %)
- Per-scenario S1/S2/S3 accuracy
- Latency (mean ± sd)
- Parameter-level pass rates (bbox, event_window, scar_dNDVI_threshold, n_realizations, lithology_field)

Framing (verbatim honesty template):
> "The purpose of this comparison is not to rank LLM backends, but to verify that the schema-constrained tool-calling interface yields stable configuration quality regardless of the underlying model."

Honesty caveats to include:
- Commercial APIs only; open-source LLMs not tested (MCP function-calling maturity).
- Config-stage robustness does not imply downstream metric equivalence. The physical pipeline is deterministic given identical configs; we report config equivalence, not downstream IoU.

## Axis 2 — Adversarial Input Handling (guardrail table)

Mirror WildfireKR Table 12 (8/8 fail-fast tests). LandslideKR-specific cases:

| # | Adversarial input | Expected behavior |
|---|---|---|
| 1 | bbox with invalid order (xmax < xmin) | Reject at config validation |
| 2 | bbox over ocean | Geology rasterization empty → fallback to "default" lithology with warning |
| 3 | event_window of 0 days | Reject at config |
| 4 | event_window 180 days (monsoon-season-spanning) | Accept but warn; S2 pre/post may be unreliable |
| 5 | n_realizations = 0 | Reject |
| 6 | n_realizations = 10 000 (memory blow-up) | Reject with actionable bound |
| 7 | Missing `gee_project` key | Agent halts at `init_ee`, not at `ensemble` |
| 8 | data.go.kr key missing/invalid | `fetch_nidr` returns non-fatal; consensus reduces to Sentinel-only (Yecheon 2023 is the natural experiment here) |
| 9 | DEM tile missing for AOI | `dem_mosaic` explicit error before `topo` |
| 10 | Geology polygon field name absent | Fallback to `default` lithology, logged |

Report all 10 as executed tests in a table. Label any live natural-experiment occurrences (Yecheon #8 already documented).

## Axis 3 — Stochastic Repeatability

Mirror WildfireKR Table 10 (20 identical runs, CV 3.3–7.1 %).

| Metric | Test |
|---|---|
| Scar-mean probability | N = 20 identical `run_case.py` invocations per event |
| ROC-AUC | Per-run variation from Monte Carlo seed pool |
| Top-1% recall | Same |
| Output file count | 8/8 expected artifacts per run |

Report CV %. Goal: show that agent pipeline is deterministic-enough that the reported point estimates are not cherry-picked.

## Axis 4 — Parameter Sensitivity Surface (SHALSTAB)

Mirror WildfireKR Table 13 / Fig. 3 (pBL sweep).

Primary knob: friction angle `phi`, cohesion `c`, transmissivity `T` bounds per lithology.

Grid:
- `phi_mean` ∈ {28°, 31°, 34°, 37°, 40°} for granite
- `c_mean`  ∈ {1 000, 2 000, 4 000, 8 000} Pa
- `T_mean`  ∈ {1e-5, 5e-5, 1e-4, 5e-4, 1e-3} m²/s

Run per event, report ROC-AUC surface. Demonstrate whether Pohang-good / Yecheon-bad holds over a flat plateau or is knife-edge.

## Axis 5 — Scar-Threshold Robustness

Mirror WildfireKR Table 14 (closing radius).

Sweep:
- dNDVI threshold ∈ {0.10, 0.12, 0.15, 0.18, 0.20}
- post-NDVI cap ∈ {0.30, 0.35, 0.40}
- slope gate ∈ {5°, 10°, 15°}

Report ROC-AUC + sep. Show whether the Pohang-good / Yecheon-bad contrast is thresholding artifact or structural.

## Axis 6 — Label-Layer Ablation

Mirror WildfireKR "Recall vs IoU" trade-off (Table 7).

Vary reference label composition:
- A. Sentinel-only (= Yecheon actually executed)
- B. NIDR-only (point-buffer proxy, 30 m)
- C. Sentinel ∪ NIDR (planned consensus)
- D. Sentinel ∩ NIDR (high-confidence)

Report metrics per label variant for the event(s) where NIDR is available (Pohang). This lets reviewers see exactly what the label source does to the metrics — closes the provenance-asymmetry concern flagged by both reviewers.

## Axis 7 — Hold-out / LOOCV-Analog

Mirror WildfireKR LOOCV (parameter stability across fires).

With n=2, strict LOOCV is 1-event cross-validation (weak). Strengthen by:

1. **Intra-event spatial hold-out**: split each event's AOI into NE/SW halves, calibrate thresholds on one, test on the other. Report ROC-AUC per half.
2. **Temporal hold-out**: train dNDVI thresholds on Pohang 60-day window, apply frozen thresholds to Yecheon (already effectively the case; make it explicit).
3. **Third-event plan (not executed)**: document explicitly that a third-event validation is scoped as future work. HP Round 4 flagged this as submission-blocking; either execute or accept the limitation.

## Reporting in the manuscript

Each axis becomes one table + one short paragraph in a new **§5 Agent Robustness Evaluation** section (demoting the current §5 Limitations to §6). Total new text: ~1 500 words + 7 tables + 1 figure (sensitivity surface).

Honesty phrases to reuse verbatim from WildfireKR:
- "not to rank backends but to verify schema-constrained stability"
- "backend-agnostic design"
- "config equivalence, not downstream IoU equivalence"
- "open-source models were not tested"
- "a direct per-backend downstream comparison remains a worthwhile follow-up"

## Cost estimate (engineering-only, for planning)

| Axis | Runs | Hours |
|---|---|---|
| 1 LLM backends | 60 | 1 (config-stage only, no physics re-run) |
| 2 Guardrails | 10 | 0.5 |
| 3 Repeatability | 40 | 3 (20 full pipeline runs × 2 events) |
| 4 Param sensitivity | 125/event × 2 | 6 |
| 5 Scar thresholds | 45/event × 2 | 4 |
| 6 Label ablation | 4 variants × 1 event | 0.5 |
| 7 Hold-out | 4 splits × 2 events | 2 |

Total ~17 engineering-hours. Well within reach of one iteration.

## What this plan does NOT commit to

- Open-source LLM testing (scoped out with the same justification as WildfireKR).
- A third independent event (flagged as future work; HP Round 4's No-go on n=2 stands as a risk, not a blocker, subject to user decision on submission timing).
- An in-pipeline model-selector layer — this plan evaluates robustness of the current orchestrator-only agent, consistent with v0.3 scoping.
