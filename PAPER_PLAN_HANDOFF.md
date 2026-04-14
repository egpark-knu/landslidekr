# LandslideKR — Full Paper Plan Handoff (v0.4, binding)

Audience: any external LLM or collaborator who needs to pick up this paper without prior context.
Date: 2026-04-14
Status: **v0.4 is binding after HP Round 4 (codex-99) rulings**. Supersedes v0.3 (manuscript_outline.md).

## 0. The One-Line Paper

Two structurally distinct Korean rainfall–landslide events expose event-type-dependent applicability of a single physical landslide model (SHALSTAB), motivating future agentic model selection; the open, reproducible, traced agent pipeline that makes the comparison possible is released as enabling infrastructure.

## 1. Position (binding, post-HP-Round-4)

The paper's center of gravity is the **benchmark finding**, not the agent. The agent is enabling infrastructure. Do not pitch the paper as "first LLM agent for landslides". Pitch it as:

> "On two structurally distinct Korean rainfall–landslide events, one steady-state physical model has sharply event-type-dependent applicability — with a topographic predictor outperforming it on the monsoon-scale AOI. The open LLM-agent pipeline that produced the benchmark is released to make this finding replicable."

Candidate titles (author picks):
1. "One Physical Model, Two Korean Rainfall Events, Diverging Skill: A Benchmark-Led Case for Agentic Model Selection in Landslide Nowcasting"
2. "Event-Type-Dependent Applicability of SHALSTAB Across Korean Typhoon and Monsoon Rainfall: An Open Agentic Benchmark"
3. (current working) "When One Physical Model Is Not Enough: Evidence From Two Korean Rainfall–Landslide Events for Agentic Model Selection"

Target: *Landslides* (Springer, IF 6.7). Stretch: *Earth-Science Reviews*.

## 2. HP Round 4 (codex-99) binding rulings

| Question | Verdict | Action committed |
|---|---|---|
| A. Is the central claim sharp enough for Landslides? | No-go | Retitle + refocus framing question on benchmark, demote agent to enabling infrastructure. |
| B. Is the orchestrator framing honest and still interesting? | Go | Keep orchestrator-not-selector honesty; tighten Pohang provenance and NIDR timeout language. |
| C. Is n=2 enough for submission? | No-go | **Add a third independent event.** Intra-2023-monsoon splits are appendix-grade, not substitutes. |

User directive (2026-04-14 16:17): proceed in the direction reviewers cannot push back on, even if compute increases. No talk-paper.

## 3. Scope of the empirical study (binding)

### 3.1 Events

Three events, all Korean rainfall-triggered:

| Event | Type | Date | AOI | Status |
|---|---|---|---|---|
| Typhoon Hinnamnor 2022 | Typhoon | 5–7 Sep 2022 | ~600 km², Pohang | Executed |
| 2023 Central Korea Monsoon | Monsoon | 13–18 Jul 2023 | ~12 100 km², Yecheon–Yeongju–Cheongju | Executed (Sentinel-only label) |
| **Third event (to select)** | Must be structurally distinct from both above | Candidates below | TBD | **Not executed** |

Candidates for third event (author to select; all in NIDR record and Sentinel-2 cloud-free):
- Chuncheon 2020.08 — monsoon, mountainous, ~700 km². Contrasts with Yecheon on size.
- Busan 2020.07.23–24 — localized heavy rainfall, urban hillslopes. Contrasts on land-cover.
- Gangneung 2023.05.11 — short-duration torrential burst in coastal mountains. Contrasts on duration.
- Gapyeong 2022.08.08–11 — intense monsoon on moderate AOI. Near-neighbor to Yecheon in typology.
- Jeju 2021.09 (Typhoon Chanthu landfall adjacent) — island volcanic lithology. Strong contrast on geology.

Recommended: **Chuncheon 2020** or **Jeju 2021** (strong typology or lithology contrast; decisive third point).

### 3.2 Physical model

- **SHALSTAB** (Montgomery & Dietrich 1994) with lithology-conditional Monte Carlo ensemble (n=100 per pixel).
- Lithology from KIGAM 1:50 000 geology (`대표암상` field; 5 classes: granite / volcanic / sedimentary / metamorphic / alluvium).
- Parameter bounds from Park et al. (2013).

### 3.3 Reference label

- **Positive-evidence proxy**, NOT field-verified ground truth.
- NIDR administrative-area reports (data.go.kr API 15074816) + Sentinel-2 NDVI-change scars.
- Per-event provenance disclosure is mandatory (Yecheon was Sentinel-only after NIDR timeout; document any similar fact for the new event).

### 3.4 Post-hoc comparisons

Four scorings reported per event:
1. Baseline SHALSTAB MC probability
2. SHALSTAB + hillslope mask (slope > 10° ∩ relief > 30 m in 33-px window)
3. Slope alone
4. Slope × relief

All four computed for all three events. This is offline diagnostic analysis; the in-pipeline agent does not select among them.

## 4. Robustness evaluation (binding — execute all seven axes)

Per `docs/ROBUSTNESS_PLAN.md`. Compute all axes, not just cheap ones. This is the reviewer-proofing work.

| Axis | What | Why |
|---|---|---|
| 1. LLM backend | 4 LLM × 3 scenarios × 5 reps = 60 config runs (Claude Sonnet 4.6, Claude Haiku 4.5, GPT-5.4, GPT-5.4 mini) | Schema-constrained interface stability |
| 2. Adversarial guardrails | 10 fail-fast tests | Agent does not silently produce plausible-wrong outputs |
| 3. Stochastic repeatability | 20 identical runs × 3 events | CV% on POD/FAR/ROC-AUC |
| 4. Parameter sensitivity | phi × c × T grid per lithology per event | Identify flat vs knife-edge regions |
| 5. Scar-threshold robustness | dNDVI × post-NDVI-cap × slope-gate sweep | Finding is structural, not thresholding artifact |
| 6. Label-layer ablation | Sentinel-only / NIDR-only / ∪ / ∩ per event | Quantify label-provenance sensitivity |
| 7. Spatial hold-out | NE/SW AOI halves per event | Weak cross-validation (n=3 strengthens vs n=2) |

Total engineering ~17 hours per `ROBUSTNESS_PLAN.md`.

## 5. FAR reduction (binding new subsection)

Per `analysis-output/analysis-report.md`. Raw FAR is structurally pinned by class imbalance and is not a useful headline. The paper reports **precision lift over base rate + POD + kept-fraction jointly**, mirroring WildfireKR's Recall/IoU trade-off. Slope > 20° as a standalone gate gives the cleanest lift on Yecheon (1.42×) without collapsing recall (POD 0.268). Probability quantile gating is degenerate because the Monte Carlo probability distribution is bimodal (peaks at 0 and 1) — calibration is future work.

## 6. Manuscript structure (binding)

Target length: 9 000 words excluding references, ~7 tables, ~5 figures.

1. **Introduction** — single block, benchmark-centered framing question, agent as enabling infrastructure. ~1 400 words. Current draft: `draft/section1_introduction_v0.2.md` needs one more pass to demote agent per HP-99 A.
2. **Methods** — Agent orchestration, SHALSTAB MC, label construction (planned vs executed, per-event), events (now three). ~1 800 words.
3. **Results** — Per-event metrics, rank-inversion diagnosis, post-hoc refinement, FAR-reduction analysis, figure walkthroughs. ~2 200 words.
4. **Robustness Evaluation** — 7-axis reporting. ~1 500 words.
5. **Discussion** — Event-typology applicability (now across three events), why topographic predictors win on large monsoon AOIs, agentic implications scoped as future work. ~1 200 words.
6. **Limitations** — 8 items inherited from v0.3 + third-event-specific caveats.
7. **Conclusions** — Benchmark finding primary, agent-infrastructure secondary.

## 7. Figures (binding list)

| # | Title | Content |
|---|---|---|
| Fig 1 | Pohang 2022 — prob + scar + histogram | lat/lon, legend, Δmean |
| Fig 2 | Yecheon 2023 — prob + scar + histogram | as above |
| Fig 3 | Third event — prob + scar + histogram | as above |
| Fig 4 | Event-contrast — prob vs elevation deciles + ROC curves 4 scorings × 3 events | 6-panel |
| Fig 5 | Agent architecture infographic | **PaperBanana** (not matplotlib) |
| Fig 6 | FAR analysis — precision-lift vs kept-fraction | all three events on one scatter |
| Fig 7 | Robustness — LLM backend config validity + parameter sensitivity surfaces | composite |

## 8. Tables (binding list)

1. Event + data configuration (3 events)
2. Baseline metrics (3 events, Table 2 of current draft + third row)
3. Post-hoc refinement comparison (4 scorings × 3 events)
4. Lithology class parameter bounds
5. Label limitations / provenance (executed vs planned, per event)
6. FAR-filter precision-lift table (new, from `analysis-output/`)
7. LLM backend comparison (WildfireKR Table 16 port)
8. Robustness summary (7 axes)

## 9. Strict no-go list (from user feedback memory)

- **No Korean in paper or figures** (`feedback_no_korean_in_paper.md`). Working docs may contain Korean; manuscript/figures do not.
- **No AI verbosity** (`feedback_avoid_ai_verbosity.md`). Lead with claim, numbers over narrative, no "Furthermore, we emphasize…" filler.
- **No "waiting ≠ progress"** labeling in status reports.
- **No "API only" framing** (user 2026-04-14: reject-worthy).
- **No ground-truth claim** — "positive-evidence proxy" throughout.
- **No over-claiming on n=2 even with 3rd event added** — the three-event contrast is diagnostic evidence, not a regime law.
- **No agent-physics claim** — agent orchestrates data and compute, not physics understanding.

## 10. Open decisions

- Third event: Chuncheon 2020 committed (2026-04-14) and executed. **Not a preregistration** — see §12 Honest disclosures below.
- Title: author to pick from §1 candidates.
- Submission timing: after all 7 robustness axes executed AND the Chuncheon VWorld-enabled re-run provides the label-layer ablation (Axis 6) for HP Round 5 C closure.

## 12. Honest disclosures (added 2026-04-14 17:30 after user-requested audit)

- **Chuncheon preregistration is post-hoc qualitative**: the bbox, event window, and qualitative Pohang-like/Yecheon-like/intermediate prediction classes were committed before execution; the numeric cutoffs and the executed classification were added afterwards. The paper does not claim preregistration of the three-event benchmark; it claims a frozen qualitative framework with a disclosed post-hoc numeric mapping. `cases/chuncheon_2020/config.json::preregistration` holds the full disclosure.
- **All three reported events use Sentinel-scar-only labels**: Pohang NIDR configured but not joined in the executed log run, Yecheon NIDR timed out, Chuncheon first executed run had n_nidr_points=0. The VWorld-enabled Chuncheon re-run targeted for label ablation is pending (two launch attempts blocked by EventWindow dataclass + GEE CLOSE_WAIT respectively; still open).
- **Robustness plan is a plan**: seven-axis evaluation described in `docs/ROBUSTNESS_PLAN.md` is designed but not yet executed. Intro and §5 wording must say "we define" / "§5 reports axes executed in this release", not "we release".

## 11. File map for the external LLM

Load in this order:
1. `PAPER_PLAN_HANDOFF.md` (this file) — binding plan
2. `manuscript_outline.md` v0.3 — needs §§1, 2.3, 4.3, 5, 6 updated to v0.4 per this plan
3. `draft/section1_introduction_v0.2.md` — current Introduction draft (needs HP-99-A demotion pass)
4. `communication/benchmark_summary_v03.md` — executed numbers + provenance
5. `analysis-output/{analysis-report, stats-appendix, figure-catalog}.md` — FAR analysis
6. `docs/ROBUSTNESS_PLAN.md` — 7-axis evidence plan
7. `docs/SAR_INTEGRATION_PLAN.md` — future work only, not in this paper
8. `TITLE_DECISION.md` — internal title log (may contain Korean; do not copy verbatim into paper)
9. `README.md` — code-side status
10. Feedback memories at `~/.claude/projects/-Users-eungyupark-mas-project/memory/feedback_{avoid_ai_verbosity,no_korean_in_paper,waiting_is_not_progress,all_agents_mandatory,always_view_figures,figure_multimodal_check}.md` — author conventions

## 12. What another LLM must NOT do

- Do not over-index on agent novelty; it is enabling infrastructure.
- Do not soften the n=2 limitation by calling 3 events "sufficient for regime law" — three is still not sufficient.
- Do not claim the agent chooses models.
- Do not translate Korean place names inconsistently (always use the romanization in the working docs: Pohang, Yecheon, Yeongju, Cheongju, etc.).
- Do not add hedging or AI-verbosity phrases; the author has a strict rule against them.
- Do not run the SHALSTAB Monte Carlo with new random seeds without versioning the output directory — existing `prob_unstable.tif` files are load-bearing artifacts.

## 13. Cost and timing (informational)

- Third event execution: ~2 h compute + 1 h label construction
- Seven robustness axes: ~17 engineering hours per plan
- Narrative rewrite to v0.4: ~4 hours
- Figure regeneration (Figs 3, 6, 7 new; Figs 1-2 touch-up): ~3 hours
- Total to submission-ready draft: roughly 1.5 engineering-days of sustained work
