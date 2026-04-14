# LandslideKR Manuscript Outline (v0.4, 2026-04-14, HP-99 binding)

**Working title (tentative)**: *One Physical Model, Three Korean Rainfall Events, Diverging Skill: A Benchmark-Led Case for Agentic Model Selection in Landslide Nowcasting*

Alternative tentative titles:
- *Event-Type-Dependent Applicability of SHALSTAB Across Korean Typhoon and Monsoon Rainfall: An Open Agentic Benchmark*
- *When One Physical Model Is Not Enough: A Three-Event Korean Benchmark for Rainfall-Triggered Landslide Nowcasting*

**Target**: *Landslides* (Springer, IF 6.7); stretch *Earth-Science Reviews*.
**Status**: Two events executed and analyzed (Pohang 2022, Yecheon 2023). Third event selection pending. Seven-axis robustness evaluation planned. Draft at outline + Introduction-v0.2 level.

## Position (binding, post-HP-Round-4)

The paper's center of gravity is the **benchmark finding**, not the agent. The agent is *enabling infrastructure* that makes the benchmark reproducible and traced; the scientific claim is about event-type-dependent applicability of a single physical landslide model, with a topographic predictor outperforming it on the monsoon-scale AOI.

What this paper is:
- A Korean multi-event retrospective benchmark of a lithology-conditional Monte Carlo SHALSTAB ensemble, with full execution provenance.
- Diagnostic evidence that a single steady-state physical model has divergent skill across typhoon- and monsoon-driven AOIs.
- An open LLM-agent data-and-compute orchestrator that makes the benchmark replicable.

What this paper is not:
- A claim that an LLM understood slope-stability physics.
- A claim that the agent currently selects among physical models.
- A regime law for typhoon-vs-monsoon model selection — the mapping is a working hypothesis on n=3.

---

## Abstract (~260 words, v0.4 benchmark-centered)

Physically based landslide nowcasting models are parameter-sensitive and can mis-rank slopes at scales where the hillslope assumption breaks down, while machine-learning classifiers trade interpretability for accuracy; neither tradition has converged on a preferred workflow for pre-event nowcasting across heterogeneous Korean rainfall typologies, and the heterogeneous Earth-observation, geology, and report streams both require must be wired together reproducibly on a per-event basis. We report a three-event Korean retrospective benchmark of a lithology-conditional Monte Carlo SHALSTAB ensemble (n=100 per pixel, five lithology classes from KIGAM 1:50 000 with pre-registered parameter bounds), against a positive-evidence reference label built from National Institute for Disaster Reduction (NIDR) reports and Sentinel-2 NDVI-change scars. The events are Typhoon Hinnamnor (Pohang, Sep 2022, 600 km²), the 2023 Central Korea Monsoon (Yecheon–Yeongju–Cheongju, Jul 2023, 12 100 km²), and Chuncheon 2020 (monsoon, small mountainous AOI — selected to disentangle whether Yecheon's failure reflects the monsoon typology or the large mixed-terrain AOI). SHALSTAB separates scars from non-scars on Pohang (ROC-AUC 0.612, mean-probability separation +0.198) but fails on Yecheon with rank inversion (ROC-AUC 0.449, −0.070); a slope-only ranking there reaches AUC 0.669, beating every SHALSTAB variant tested. Because the positive-class rate is 0.12–1.65 %, raw false-alarm rate is structurally pinned near 99 % and is not a useful operational axis; we report precision lift over base rate jointly with recall and kept-fraction. The benchmark is made possible by **LandslideKR**, an open LLM-agent data-and-compute orchestrator whose eleven-step traced pipeline is released together with both dry-run and executed artifacts and a seven-axis agent-robustness evaluation. Label provenance is disclosed symmetrically per event: the reported Pohang metrics use Sentinel-scar-only labels — NIDR was configured but not joined in that run — and the Yecheon run reverted to Sentinel-only labels after an NIDR API timeout. The three-event divergence is offered as diagnostic evidence motivating future agentic model selection, not as a demonstrated agent capability in this release.

---

## 1. Introduction (~1400 words, single-block; current draft: `draft/section1_introduction_v0.2.md`)

Narrative arc (benchmark-centered):

1. Korean rainfall-triggered landslides and the two anchor events (Pohang 2022 typhoon, Yecheon 2023 monsoon) + one third event for triangulation.
2. Two research communities (physically based models and ML classifiers) on separate tracks and the per-event orchestration problem they both inherit.
3. Gap: no open, reproducible, traced, end-to-end agent implementation against which to study single-model behavior across Korean rainfall typologies.
4. Falsifiable question (benchmark-centered, not agent-centered): *across three structurally distinct Korean rainfall–landslide events, does a single physical model suffice, or does the benchmark expose event-type-dependent applicability?*
5. Scopings: agent is an orchestrator (not a selector); reference label is a positive-evidence proxy (not field-verified ground truth); ML baselines are deferred to a future iteration scoped around a model-selection layer.
6. LandslideKR as the enabling infrastructure — an eleven-step traced pipeline. Execution provenance disclosed symmetrically (Yecheon Sentinel-only after NIDR timeout; Pohang executed-log vs stored dry-run trace; third event documented in the same format).
7. Headline benchmark result: Pohang AUC 0.612 / sep +0.198; Yecheon AUC 0.449 / sep −0.070 with rank inversion; slope-only AUC 0.669 on Yecheon > every SHALSTAB variant. Third event anchors the contrast in a third point.
8. Contribution list (benchmark first, agent second).
9. Nugget: the Yecheon-style rank inversion is itself diagnostic; it is not a failure to hide but a signal to surface.
10. Roadmap paragraph (§§2–7).

### 1.1 Gap in published literature (verifiable)

- No published open, reproducible, traced, end-to-end LLM-agent pipeline for pre-event Korean rainfall-triggered landslide nowcasting. *Disaster Copilot* (arXiv 2510.16034) is a vision paper; geotechnical perspectives (ScienceDirect 2025) argue for such agents but do not release one.
- No published three-event Korean retrospective benchmark of a physically based landslide model with disclosed execution provenance.
- Little published event-typology-conditioned comparison of physical vs topographic predictors for Korean rainfall–landslide events.

### 1.2 Contribution (benchmark-ordered, scoped)

1. **A three-event retrospective benchmark** of a lithology-conditional Monte Carlo SHALSTAB ensemble across structurally distinct Korean rainfall events, with full execution provenance released.
2. **Two-event-level diagnostic evidence** that a single steady-state physical model has divergent skill across typhoon- and monsoon-driven AOIs, with a slope-only predictor beating every SHALSTAB variant on the large monsoon AOI. A third event corroborates or refutes the pattern as a working hypothesis.
3. **A seven-axis agent-robustness evaluation** (§5) covering LLM backend, adversarial input handling, stochastic repeatability, SHALSTAB parameter sensitivity, scar-threshold sensitivity, label-layer ablation, and spatial hold-out.
4. **LandslideKR** as the open enabling infrastructure: an LLM-agent data-and-compute orchestrator with an eleven-step traced pipeline, lithology-conditional MC wired to KIGAM 1:50 000 geology with pre-registered bounds from Park et al. (2013), and explicit label/execution provenance disclosure per event.
5. **A scoped forward hypothesis** that agentic model selection is warranted, stated as future work to be validated on additional events, not as a demonstrated agent capability here.

---

## 2. Methods (~1900 words)

### 2.1 LandslideKR as Enabling Infrastructure

Sequential pipeline with explicit trace (`AgentTrace`):
1. `init_ee()` — Earth Engine project initialization.
2. `fetch_rainfall` — GPM IMERG V07 cumulative.
3. `detect_scars` — Sentinel-2 NDVI change with slope filter (auto-scale 10/30 m for large AOIs).
4. `fetch_nidr` — data.go.kr API 15074816 with optional VWorld geocoding (NIDR returns XML; no polygon coordinates).
5. `dem_mosaic` — local Copernicus DSM COG 30 m tiles (Copernicus GLO-30 DSM, pre-downloaded to `dem_root`) discovered by `landslide_kr/preprocess/dem_mosaic.py::find_copernicus_tiles`, mosaicked, and reprojected to the local UTM zone. An incidental call to GEE SRTM (USGS/SRTMGL1_003) is made inside `landslide_kr/collectors/sentinel_landslide_scar.py` solely to generate a slope gate on the Sentinel-2 scar raster; it is not the main SHALSTAB DEM. A previous draft of this text incorrectly attributed the main DEM to SRTM and is recovered here.
6. `topo` — `pysheds` Cython D8 flow accumulation with Horn (1981) 3×3 slope kernel; three-tier fallback (`richdem` → `pysheds` → numpy) documented.
7. `lithology` — KIGAM 1:50 000 geology rasterized to DEM grid using the principal-rock-type field, mapped to five classes.
8. `ensemble` — SINMAP-style bounded Monte Carlo (n=100 per pixel) over the lithology-conditional parameter ranges of §2.2.
9. `save_prediction` — `prob_unstable.tif` + binary mask at p ≥ 0.5.
10. `consensus_label` — NIDR point buffer ∪ Sentinel-2 scars; see §2.3 for what each event actually used.
11. `evaluate` — POD / FAR / CSI / F1 / ROC-AUC via scikit-learn; per-event precision-lift table computed post-hoc (§3.5).

The agent does not choose among physical models. Every event is run under the uniformly configured SHALSTAB ensemble. Comparisons to hillslope-masked, slope-only, and slope × relief scorings (§§3.3, 3.5) are offline analyses, not in-pipeline agent behavior.

### 2.2 SHALSTAB + Lithology-Conditional Monte Carlo

Montgomery & Dietrich (1994) q/qcr formulation. Five lithology classes (granite / volcanic / sedimentary / metamorphic / alluvium) each with pre-registered ranges for friction angle (φ), cohesion (c), transmissivity (T), and soil depth (z) from Park et al. (2013) and the Korean geotechnical literature. Ranges and per-class central values appear in Table 4. Each pixel draws 100 parameter realizations from the appropriate lithology's bounded distribution; the output is a probability of instability at that pixel.

### 2.3 Reference Label Construction (planned vs executed, per event)

**Planned label** (all events): union of
- NIDR (Korea Forest Service) administrative-area records with 30-m buffer around geocoded centroids (no polygons; no 300-m tolerance buffer claimed at evaluation time).
- Sentinel-2 scars: dNDVI > 0.15 ∧ post-NDVI < 0.35 ∧ slope > 10°, 60-day post window.

**Executed label, per event**:
- **Pohang 2022**: **Sentinel-scar-only in the reported run.** NIDR was configured in the case JSON but was not joined to the evaluation label in the executed log run (`out/pohang_2022_run_20260414_1513_C2.log`). The stored `agent_trace.json` is an earlier dry-run probe and differs from the executed run; both artifacts are released side by side. This means the Pohang/Yecheon contrast in §3 is between two Sentinel-scar-only labels, not between a consensus label and a Sentinel-only label.
- **Yecheon 2023**: Sentinel-only. `fetch_nidr` returned `timed out` at run time (trace: `out/extreme_rainfall_2023/agent_trace.json` step 4, `nidr_path: null`, `n_nidr_points: 0`). The planned consensus reduced to Sentinel-2 scars.
- **Chuncheon 2020** (third event): to be documented in the same format once executed. Planned consensus is Sentinel-2 ∪ NIDR 30-m point buffer; any failure mode of either source is reported identically.

We use the term **positive-evidence proxy** throughout. Sentinel-2 false positives (flood scars on floodplains, harvest, cloud shadow) are discussed in §4.4 and, for events where NIDR is available, quantified via the label-layer ablation of §5 Axis 6.

### 2.4 Events

| Event | Type | Date | AOI (km²) | Rainfall peak | Lithology mix | Status |
|---|---|---|---|---|---|---|
| Pohang 2022 (Typhoon Hinnamnor) | Typhoon | 5–7 Sep 2022 | ~600 | 412 mm/24 h | granite-dominated | Executed |
| Yecheon 2023 (Monsoon) | Monsoon | 13–18 Jul 2023 | ~12 100 | 580 mm/6 d | sedimentary + metamorphic + alluvium | Executed (Sentinel-only) |
| **Chuncheon 2020** (third event, binding) | Monsoon, small mountainous AOI | Aug 2020 | ~700 (to confirm) | TBD | Granite + metamorphic mix (to confirm) | **Next target** |

The third event is Chuncheon 2020 — monsoon forcing but on a small mountainous AOI. This is the structurally informative choice because it isolates whether Yecheon's rank inversion is driven by rainfall typology (monsoon vs typhoon) or by AOI size and terrain mix (large mixed-terrain vs small hillslope-dominated). If Chuncheon 2020 patterns like Pohang, the signal is AOI; if it patterns like Yecheon, the signal is typology. Either outcome tightens the typology working hypothesis. NIDR coverage and cloud-free Sentinel-2 availability are verified before execution.

---

## 3. Results (~2200 words)

### 3.1 Two-event baseline SHALSTAB-ensemble (executed)

| Metric | Pohang 2022 | Yecheon 2023 | Third event |
|---|---|---|---|
| N valid pixels | 912 384 | 11 113 520 | 1 259 904 |
| Positives (scar) | 1 099 (0.12 %) | 183 507 (1.65 %) | 15 571 (1.24 %) |
| POD | 0.9145 | 0.4838 | 0.7152 |
| FAR (raw) | 0.9984 | 0.9855 | 0.9879 |
| CSI | 0.0016 | 0.0143 | 0.0121 |
| F1  | 0.0032 | 0.0281 | 0.0239 |
| ROC-AUC | **0.6118** | **0.449** | **0.4992** |
| Scar mean prob | 0.887 | 0.464 | 0.685 |
| Non-scar mean prob | 0.688 | 0.534 | 0.679 |
| Separation | **+0.198** | **−0.070** | **+0.006** |
| Top-1 % recall | 0.692 | 0.144 | 0.290 |

**Interpretation (three-event contrast, honest provenance per `cases/chuncheon_2020/config.json`)**: Chuncheon 2020 landed at ROC-AUC 0.499 with near-zero separation +0.006. The qualitative pattern-matching prediction classes (Pohang-like / Yecheon-like / intermediate) were committed to the config before execution; the specific numeric cutoffs (ROC ≥ 0.55, separation ≥ +0.10) and the resulting Prediction-B classification were recorded after execution and are disclosed as a **post-hoc classification of a pre-committed qualitative framework**, not as a preregistered hypothesis test. A reviewer who requires strict preregistration should treat the three-event benchmark as retrospective diagnostic, not as a confirmatory test; the config file's `preregistration.status` field makes this disclosure. Chuncheon agrees with Yecheon on rainfall typology (monsoon) but agrees with Pohang on AOI size and terrain mix (small mountainous); its monsoon-side placement is therefore informative about which of those two factors drives SHALSTAB's applicability divergence. Stating the claim at the level the three-event benchmark actually supports: **across this three-event benchmark, rainfall typology appears more explanatory than AOI size for SHALSTAB skill, but the pattern remains a working hypothesis rather than a regime law** (HP Round 5, 2026-04-14). Additional events are required before this working hypothesis can be upgraded, and the claim is explicitly kept at this level throughout §4 and §7.

Pohang shows positive separation; Yecheon shows rank inversion. The third event's placement on this spectrum is the triangulation point.

### 3.2 Root-cause analysis (Yecheon rank inversion)

Elevation-decile breakdown:
- Scar mean elevation **455 m** (median 343 m) vs non-scar 280 m (240 m).
- Model probability decreases with elevation: 0.794 (<89 m) → 0.346 (>538 m).
- Scar rate increases with elevation: 0.2 % (<89 m) → 4.9 % (>538 m).

Interpretation: the model over-predicts on low-elevation valleys where SHALSTAB's steady-state upslope-area term inflates the `a/b` denominator; actual scars cluster on steep higher-elevation slopes. This explains why a predictor that avoids the `a/b` confounder (raw slope) beats SHALSTAB on Yecheon (§3.3).

### 3.3 Post-hoc hillslope mask and alternative scorings

Hillslope mask: slope > 10° ∩ local relief > 30 m within a 33-pixel window.

| Method | Pohang ROC-AUC | Yecheon ROC-AUC | Chuncheon ROC-AUC |
|---|---|---|---|
| Baseline SHALSTAB | **0.612** | 0.449 | 0.499 |
| Hillslope-masked   | 0.520 | **0.593** | 0.555 |
| Slope alone        | 0.506 | **0.669** | 0.549 |
| Slope × relief     | 0.527 | 0.641 | **0.572** |

Masking rescues Yecheon; slope alone beats every SHALSTAB variant there. The same simplification hurts Pohang slightly. This is an offline diagnostic comparison, not an agent decision.

### 3.4 Maps (Figures 1–3): prob_unstable + scar overlay + histogram

- **Fig 1 — Pohang 2022**: prob map (p = 1 saturation on high-relief), binary prediction with Sentinel-2 scars dilated 2 px, probability separability histogram (Δmean = +0.198).
- **Fig 2 — Yecheon 2023**: prob map with extensive p > 0.5 coverage including valleys, binary + scars, histogram (Δmean = −0.070 computed on rasters; figure renders at −0.061 due to different masking — reconciled in the supplement).
- **Fig 3 — Third event**: same three-panel format; rendered once executed.

All figures in lat/lon. Panels (b) carry legend proxies for predicted-unstable, predicted-stable, and Sentinel-2 scar.

### 3.5 False-alarm reduction via post-hoc filters (new in v0.4)

Raw FAR is structurally pinned near 99 % at these positive-class rates (0.12–1.65 %) — any filter that keeps > 2 % of pixels as predicted-unstable will have FAR ≥ 98 %. Raw FAR is therefore not a useful headline operational knob. We report **precision lift over base rate** (precision ÷ base_rate) jointly with POD and kept-fraction, following the Recall/IoU trade-off reporting pattern of WildfireKR (IEEE Access 2026).

Nine filters are evaluated per event:
- F0 baseline; F1 hillslope; F2–F4 probability top-10/5/1 %; F5–F6 compound with hillslope; F7 slope > 20°; F8 compound (F1 ∩ slope > 20° ∩ prob > 0.9).

Headline results (full table in `analysis-output/analysis-report.md`):

| Filter | Pohang lift | Pohang POD | Yecheon lift | Yecheon POD |
|---|---|---|---|---|
| F0 baseline | 1.31× | 0.914 | 0.88× (sub-random) | 0.484 |
| F1 hillslope | 1.44× | 0.208 | **1.28×** | 0.417 |
| F7 slope > 20° | 1.00× | 0.049 | **1.42×** | 0.268 |
| F5/F6 F1 ∩ top-10/5 % | **1.56×** | 0.065 | 1.16× | 0.097 |
| F8 compound | 0.75× (over-filtered) | 0.023 | 1.36× | 0.122 |

Two additional findings:
- The Monte Carlo probability distribution is bimodal (peaks at p = 0 and p = 1); the top-10/5/1 % quantile thresholds all collapse to the p = 1.0 tier. Probability calibration is future work.
- On Yecheon, the slope > 20° gate alone is the cleanest single-knob lift (1.42×) while preserving POD > 0.25 — the pixel-level analog of the §3.3 slope-only ROC-AUC finding.

**Standard precision-recall view (augmenting, not replacing, the lift analysis).** Per codex-98 v0.4 must-fix #3, we also report Average Precision (AP = area under the precision-recall curve) and its ratio to the event base rate for each event. `analysis-output/pr_auc_summary.json` + `analysis-output/figures/figure-02-pr-curves.png` are released alongside the precision-lift table.

| Event | Base rate | AP (sklearn) | AP / base rate |
|---|---|---|---|
| Pohang 2022   | 0.1205 % | 0.0016 | **1.29×** (weak positive discrimination) |
| Yecheon 2023  | 1.6512 % | 0.0139 | **0.84×** (sub-random, consistent with rank inversion) |
| Chuncheon 2020| 1.2359 % | 0.0121 | **0.98×** (random, consistent with separation +0.006) |

AP and precision-lift give the same qualitative reading per event: Pohang > base, Yecheon < base, Chuncheon ~ base. ROC-AUC is insensitive to base-rate differences and is reported in Table 2 for completeness.

### 3.6 Three-event contrast figure

Figure 4: event-contrast, six panels — (a–c) prob vs elevation deciles and scar rate vs elevation deciles for each event; (d–f) ROC curves for the four scorings (baseline / hillslope-masked / slope alone / slope × relief) per event. Anchors the working-hypothesis claim of §4.

---

## 4. Discussion (~1200 words)

### 4.1 Event-typology-dependent applicability

SHALSTAB's steady-state hydrology matches sharp-peak typhoon forcing on a hillslope-dominated small AOI. On a large AOI with extensive floodplains and channels under distributed multi-day monsoon forcing, the hillslope assumption is violated and the upslope-area term becomes a systematic confounder.

### 4.2 Why simpler slope-based ranking outperforms

The slope-alone ranking carries no upslope-area term and therefore does not over-predict valleys. On the monsoon-forced large AOI this is a feature, not a bug. On the hillslope-dominated typhoon AOI the upslope-area term is informative and the simplification hurts.

### 4.3 Agentic implications (scoped, n=3 working hypothesis)

The three-event divergence is evidence that a single-model commitment is brittle across Korean rainfall typologies. It **motivates** an agentic model-selection layer; it does not establish a regime law on n=3. We propose candidate decision rules:

- Typhoon / small AOI / sharp rainfall peak → unmasked SHALSTAB ensemble.
- Monsoon / large AOI / distributed multi-day rainfall → hillslope-masked SHALSTAB or slope-only ranking.
- Medium-duration events → TRIGRS-class transient models (not tested here).

Stated as **candidate decision rules for future work**, to be validated on additional events before being embedded in the agent as an in-pipeline selector.

### 4.4 Label limitations and Sentinel-2 false-positive modes

Sentinel-2 scar proxy captures NDVI drops from flood scars, harvest, cloud shadow. For events where NIDR is joinable (Pohang, third event if reachable), the label-layer ablation (§5 Axis 6) quantifies how much the Sentinel-only sub-label contributes to apparent positives on low-elevation / agricultural pixels. On Yecheon, which ran Sentinel-only, we do not separate these modes at the raster level; we flag this as a label-provenance caveat whose effect on the rank inversion is bounded but non-zero.

---

## 5. Agent Robustness Evaluation (~1500 words)

Mirror of WildfireKR (IEEE Access 2026) systems-evaluation section. Full plan in `docs/ROBUSTNESS_PLAN.md`.

### 5.1 Axis 1 — LLM backend (E1-analog)

4 LLMs (Claude Sonnet 4.6, Claude Haiku 4.5, GPT-5.4, GPT-5.4 mini) × 3 scenario-specificity levels (full / descriptor / vague) × 5 reps = 60 config runs. Table 7 reports config-validity, parameter-accuracy, per-scenario accuracy, and latency. Framing (verbatim honesty template): "not to rank LLM backends, but to verify that the schema-constrained tool-calling interface yields stable configuration quality regardless of the underlying model." Commercial APIs only; open-source LLMs not tested because MCP function-calling maturity is not yet standardized.

### 5.2 Axis 2 — Adversarial input handling

Ten fail-fast tests (bbox order, ocean bbox, zero/huge event_window, n_realizations bounds, missing gee_project, invalid data.go.kr key, missing DEM tile, absent lithology field, malformed event date). Each either halts with actionable error or falls back with logged warning. Yecheon's NIDR timeout is itself a natural-experiment instance of guardrail case #8.

### 5.3 Axis 3 — Stochastic repeatability

Twenty identical runs per event (n = 60 total). Report CV % on POD, ROC-AUC, top-1 % recall, scar-mean probability, output-file count. Establishes that the point estimates in §3.1 are not cherry-picked.

### 5.4 Axis 4 — Parameter sensitivity surface

Grid over φ × c × T per lithology per event. Identify whether the Pohang-good / Yecheon-bad pattern lives on a flat plateau or a knife-edge. Report ROC-AUC surface per event (Fig 7).

### 5.5 Axis 5 — Scar-threshold robustness

Sweep over dNDVI ∈ {0.10, 0.12, 0.15, 0.18, 0.20}, post-NDVI cap ∈ {0.30, 0.35, 0.40}, slope gate ∈ {5°, 10°, 15°}. Report whether the Pohang-good / Yecheon-bad contrast is a thresholding artifact or structural.

### 5.6 Axis 6 — Label-layer ablation

Four reference-label variants: Sentinel-only, NIDR-only, Sentinel ∪ NIDR, Sentinel ∩ NIDR. Reported on the events for which NIDR is available. This is the direct response to Sentinel-provenance asymmetry concerns.

### 5.7 Axis 7 — Spatial hold-out

Split each event's AOI into NE/SW halves. Calibrate scar thresholds on one half; test on the other. Report ROC-AUC per held-out half. Weak cross-validation but the strongest feasible on three events.

### 5.8 Bimodality of the MC probability output

Empirical observation (§3.5): > 10 % of pixels per event have p = 1.0. The ensemble produces a near-binary ranking rather than a calibrated probability. We report this without claiming a calibration pipeline; isotonic regression per lithology or logistic calibration on MC counts is flagged as future work.

---

## 6. Limitations (~400 words)

1. **No field-verified ground truth**; labels are a positive-evidence proxy.
2. **Sentinel-2 scar proxy** captures non-landslide NDVI drops (flood, harvest, shadow).
3. **Yecheon used Sentinel-only labels** due to an NIDR API timeout at run time; Pohang benchmark numbers come from an executed log run, not the stored dry-run trace. Both are released.
4. **NIDR polygons unavailable**; address-level centroid buffered at 30 m; no 300-m tolerance buffer is applied at evaluation time.
5. **n = 3 events**; typology mapping is a working hypothesis, not a regime law.
6. **Agent does not currently select models**; selection evidence is offline, not in-pipeline.
7. **Monte Carlo n = 100**; tail estimates are modest.
8. **Monte Carlo probability bimodality** (p = 0, p = 1); quantile gating above p = 0.5 is degenerate without calibration.
9. **Sentinel-1 SAR not integrated** (future extension; design in `docs/SAR_INTEGRATION_PLAN.md`).
10. **Commercial LLMs only** in Axis 1; open-source models not tested.

---

## 7. Conclusions (~300 words)

1. LandslideKR's three-event Korean retrospective benchmark shows that a single physically based model (lithology-conditional Monte Carlo SHALSTAB) has sharply event-type-dependent skill — workable on the typhoon-forced Pohang AOI, rank-inverted on the monsoon-forced Yecheon AOI where a topographic predictor outperforms it.
2. At the positive-class rates of Korean landslide events (0.1–2 %), raw false-alarm rate is not a useful operational axis; precision lift over base rate, reported jointly with recall and kept-fraction, communicates the real trade-off.
3. The benchmark is made possible by an open, traced LLM-agent data-and-compute orchestrator that we release as enabling infrastructure; the agent does not currently select physical models.
4. The three-event divergence **motivates** an agentic model-selection layer. We present candidate decision rules as a working hypothesis and defer their validation to additional events.
5. Code, traces (dry-run and executed), logs, figures, seven-axis robustness artifacts, and a forward SAR-integration plan are released with disclosed limitations.

---

## Figures (binding list)

- **Fig 1**: Pohang 2022 — prob + binary+scar + histogram (made)
- **Fig 2**: Yecheon 2023 — prob + binary+scar + histogram (made)
- **Fig 3**: Third event — same three-panel format (pending event execution)
- **Fig 4**: Three-event contrast — prob vs elevation deciles + scar-rate vs elevation deciles + ROC-4-scorings per event (6 panels)
- **Fig 5**: Agent architecture infographic — **PaperBanana** (not matplotlib)
- **Fig 6**: FAR analysis — precision lift vs kept-fraction scatter, all events on one panel
- **Fig 7**: Robustness — LLM-backend config-validity bars + parameter-sensitivity surfaces composite

## Tables (binding list)

- **Table 1**: Event + data configuration (three events)
- **Table 2**: Baseline metrics, three events
- **Table 3**: Post-hoc refinement comparison (4 scorings × 3 events)
- **Table 4**: Lithology class parameter bounds (five classes; φ, c, T, z)
- **Table 5**: Label provenance (executed vs planned, per event)
- **Table 6**: FAR-filter precision-lift table (9 filters × 3 events)
- **Table 7**: LLM-backend comparison (Axis 1, WildfireKR Table 16 port)
- **Table 8**: Robustness summary matrix (7 axes × 3 events)

---

## Next actions

1. Select third event (candidates: Chuncheon 2020, Jeju 2021, Busan 2020.07, Gangneung 2023.05, Gapyeong 2022.08).
2. Rewrite Introduction §1 v0.2 → v0.3 with agent-demotion pass and benchmark-ordered contribution list.
3. Execute Axes 2 (guardrails), 3 (stochastic repeatability), 6 (label ablation) on current two events — self-executable without third-event pending.
4. Re-run §3.3 / §3.5 / §4 once third event lands.
5. Generate Fig 6 (precision-lift scatter) and Fig 7 composite.
6. Align `TITLE_DECISION.md` and `README.md` with this v0.4 outline.
