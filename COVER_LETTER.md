# Cover Letter — *Landslides*

**Draft v0.1 — 2026-04-15 (pre-submission; review before dispatch)**

---

**To:** Editor-in-Chief, *Landslides* (Springer Nature)
**From:** Eungyu Park (corresponding), Taeyu Kim, Jangwon Park
School of Earth System Sciences, Kyungpook National University, Daegu, Republic of Korea
GeoAI Alignment, Inc., Daegu, Republic of Korea
**Email:** egpark@knu.ac.kr
**Date:** [submission date]

**Manuscript title:** Event-type-dependent applicability of a steady-state physical landslide model: a three-event Korean retrospective benchmark with reproducible execution traces

**Article type:** Original Paper

---

Dear Editor,

I am pleased to submit the enclosed manuscript for consideration in *Landslides*. The paper reports a retrospective benchmark of a lithology-conditional Monte Carlo SHALSTAB ensemble across three structurally distinct Korean rainfall-triggered-landslide events — Typhoon Hinnamnor (Pohang 2022; ~600 km², hillslope-dominated), the 2023 central-Korea monsoon (Yecheon 2023; ~9 000 km², mixed-terrain), and the 2020 Gangwon monsoon (Chuncheon 2020; ~850 km², small mountainous) — executed through a traced, re-runnable data-and-compute orchestrator released with the paper.

**What the paper contributes, stated plainly.**

1. An open three-event Korean retrospective benchmark of Monte Carlo SHALSTAB with full execution provenance, evaluated against an event-window Sentinel-2 NDVI-change scar reference (with an annual administrative-area NIDR-report label-source sensitivity check reported separately).
2. Three-event diagnostic evidence that a single steady-state physical model has divergent skill across Korean rainfall–landslide events: ROC-AUC 0.612 with positive separation on the typhoon event, rank-inverted on the large monsoon AOI (0.449), and essentially random on the small monsoon AOI (0.499). A topographic predictor (slope alone) reaches 0.669 on the large monsoon AOI.
3. Precision-lift-over-base-rate reporting jointly with recall and kept-fraction, because raw false-alarm rate is structurally pinned near 99 % at the observed positive-class rates (0.12–1.65 %) and therefore uninformative.
4. The LandslideKR orchestrator — an eleven-step LLM-agent data-and-compute pipeline released under an open-source license — that makes the benchmark replicable end-to-end from public data sources.

**What the paper does not claim.** The agent layer is enabling infrastructure, not a demonstrated autonomous decision-maker. The three-event divergence motivates an in-pipeline agentic model-selection layer as future work; no such capability is claimed here.

**Why *Landslides*.** The manuscript sits at the intersection of physically based shallow-landslide modelling, multi-event retrospective benchmarking, and reproducible-research infrastructure — topics the journal has published across volumes. The paper's single-region three-event design complements, rather than competes with, cross-regional benchmarks, and its reproducible-execution-trace contribution targets the community goal of making model comparisons independently re-runnable.

**Originality and prior publication.** This manuscript has not been published elsewhere and is not under consideration by another journal. An open preprint may be posted to a recognised preprint server upon submission; no embargo is requested.

**Competing interests.** None. A full Declarations section (Funding; Competing interests; Ethics approval; Consent for publication; Data availability; Code availability; Materials availability; Author contributions) is included in the manuscript.

**Data and code availability.** All code, per-event configurations, analysis scripts, executed traces, and the manuscript source are publicly available at <https://github.com/egpark-knu/landslidekr>. The four Online Resources accompanying the submission are: (1) numeric backing artifacts, (2) pipeline reference and operational detail, (3) seven-axis robustness evaluation plan, (4) SAR integration plan for future work.

**Suggested reviewers.** A short list of suggested reviewers with institutional affiliations and publication-aligned rationale is provided in the separate Suggested Reviewers form.

I confirm that all listed authors have contributed substantially to this work and have read and agree to the journal's editorial policies. Eungyu Park is the corresponding author.

Thank you for considering this submission. I look forward to the editorial decision.

Sincerely,

Eungyu Park
Department of Geology
Kyungpook National University
80 Daehak-ro, Buk-gu, Daegu 41566, Republic of Korea
egpark@knu.ac.kr
ORCID: [to be inserted at submission]
