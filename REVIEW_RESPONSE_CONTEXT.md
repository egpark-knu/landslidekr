# LandslideKR — Review-Response Context Pack

**Purpose.** This file is the single-point handoff for picking up the manuscript when reviewer comments arrive (anywhere from 2 weeks to 6 months after submission). It consolidates everything a fresh-context agent needs to respond without re-deriving decisions.

**Last updated.** 2026-04-14 23:25 KST (pre-submission freeze).

---

## 1. Paper identity

- **Title.** *Event-type-dependent applicability of a steady-state physical landslide model: a three-event Korean retrospective benchmark with reproducible execution traces*
- **Corresponding author.** Eungyu Park (`egpark@knu.ac.kr`), Department of Geology, Kyungpook National University, Daegu, Republic of Korea.
- **Target journal.** *Landslides* (Springer Nature, ISSN 1612-5118, IF 6.7).
- **Article type.** Original Paper.
- **Reference style.** sn-basic (author–year).
- **Code repository.** <https://github.com/egpark-knu/landslidekr> (public, `main` branch; commit hash locked at submission time).
- **Expected DOI.** assigned by Springer upon acceptance; Zenodo DOI for code release to be created at that time.

## 2. Authoritative files (at submission freeze)

| File | Role | Last touched |
|---|---|---|
| `draft/_integrated_v06_draft.md` | **Authoritative manuscript source** (Markdown) | 2026-04-14 23:19 |
| `draft/_LandslideKR_v0.8.1_journal.pdf` | **Rendered PDF** (10.4 MB, 4 figures embedded) | 2026-04-14 23:20 |
| `draft/_LandslideKR_v0.8.1_journal.tex` | LaTeX wrapper (R12-backup preamble + fresh body) | 2026-04-14 23:20 |
| `draft/tables_v0.1.md` | Appendix tables workbook | 2026-04-14 23:12 |
| `draft/_preamble_landslides.tex` | LaTeX preamble fragment | (stable) |
| `draft/DRAFT_PROVENANCE.md` | Declares authoritative vs superseded | (stable) |
| `draft/_working_fragments/` | Superseded section fragments — NOT authoritative | 2026-04-14 22:48 |
| `SPRINGER_SUBMISSION_KIT.md` | Template porting guide | 2026-04-14 23:18 |
| `README.md` (repo root) | Public landing page | 2026-04-14 22:31 |

Numeric backing:
- `analysis-output/axis6_label_ablation.json` + `.csv` — variants A/B/C/D × 3 events
- `analysis-output/far_filter_results.json` + `.csv` — 9 filters × 3 events
- `analysis-output/post_hoc_refinement.json` — baseline + 3 alternative scorings × 3 events
- `analysis-output/axis3_repeatability.json` + `.csv` — 5 seeds × 3 events (default-lithology fallback)
- `analysis-output/axis4_param_sensitivity.json` — 8 corners × 3 events
- `analysis-output/calibration_isotonic.json` — within-sample isotonic × 3 events
- `analysis-output/pr_auc_summary.json` — PR-AUC per event

Traces: `out/*/agent_trace.json` (Yecheon, Chuncheon executed with `_annotation_note` at index 0 disclosing post-hoc `fetch_nidr` re-annotation); `out/pohang_2022_run_20260414_1513_C2.log` (Pohang executed run log, since Pohang's stored JSON is a dry-run probe).

## 3. Story — the message the reader should take away

**Layered in §4.1** (do not flatten):

1. **Primary finding.** Against event-window Sentinel-2 scar labels, SHALSTAB discriminates on the typhoon event (Pohang ROC-AUC 0.612, sep +0.198) but is rank-inverted on the large monsoon AOI (Yecheon 0.449, sep −0.070) and near-random on the small monsoon AOI (Chuncheon 0.499, sep +0.006). Under this baseline, rainfall typology is the most consistent explanatory axis for SHALSTAB skill — **working hypothesis, not a regime law**, pending additional independent events.
2. **Auxiliary layer 1 — AOI composition interacts with typology.** The large mixed-terrain Yecheon AOI contains floodplains that make SHALSTAB's $a/b$ term behave as a confounder (§3.2 elevation-decile evidence). This describes how typology + AOI composition interact on the largest AOI; it is not a separate claim.
3. **Auxiliary layer 2 — label-source sensitivity partially recovers monsoon skill.** Under annual administrative-area NIDR labels, Yecheon ROC-AUC recovers to 0.608 and Chuncheon to 0.635. Because NIDR is annual (not event-window), this is a **label-source sensitivity check**, not an event-window validation. It means the Sentinel-label monsoon deficit partially reflects Sentinel-specific false positives rather than pure model failure. We keep the typology claim at working-hypothesis strength and explicitly avoid stronger causal language.
4. **Chuncheon status.** Retrospective diagnostic, not preregistered — qualitative predictions pre-committed, numeric cutoffs post-hoc. Disclosed in released case config.
5. **Agentic contribution.** Not a data-scientist agent; the orchestrator is a **constructed-resource operating layer** on the EO+geology+reports+solver stack, giving three operating-layer guarantees (typed AgentTrace with rationale, dry-run vs executed separation, symmetric failure-mode disclosure). Model-selection layer and NL config frontend are **deferred** to follow-on work.

## 4. Pre-authored response pack for likely reviewer concerns

The 20-round internal review (Gemini + codex-fresh + codex-98) surfaced every concern a *Landslides* reviewer is plausibly going to raise. Pre-mapped responses:

### 4.1 "Why is typology the claim and not AOI size?"
- Three-event disambiguation: Chuncheon (small-mountainous, monsoon) patterns with Yecheon (large, monsoon), not with Pohang (small, typhoon). If AOI size were the dominant signal, Chuncheon would pattern with Pohang. It doesn't.
- Hedge: claim is working hypothesis pending additional events; three events is not enough to establish a regime law.

### 4.2 "Isn't the monsoon deficit just Sentinel false positives?"
- Partially — yes. This is exactly what §5.6 Axis 6 shows (Yecheon 0.449→0.608 under NIDR).
- But Pohang is excluded from the NIDR comparison (`n_nidr_in_bbox=0`), so the ablation cannot fully separate model-applicability from label-source.
- Our claim strength matches the data: Sentinel-event-window baseline is the primary comparison, NIDR is a sensitivity check, stronger causal language is avoided.

### 4.3 "The NIDR labels are annual — isn't this a fatal flaw?"
- Disclosed in §2.3 (annual placeholder `YYYY-01-01`) and §5.6 (label-source sensitivity, not event-window validation).
- Effect: magnitude of monsoon deficit under Sentinel labels overstates deficit under human-reported labels. Sign and direction (typology ordering) are preserved under both label sources.
- NIDR is not used in the §3.1 baseline; only in the §5.6 ablation.

### 4.4 "The Chuncheon preregistration is post-hoc."
- Explicitly disclosed. Qualitative A/B/C predictions pre-committed; numeric cutoffs added post-execution to map results onto those predictions. Treated as retrospective-diagnostic, not preregistered confirmatory test.
- Released case config (`cases/chuncheon_2020/config.json`) carries the full disclosure in a `preregistration` block.

### 4.5 "The Table 4 parameter bounds say 'pre-registered' but granite was adjusted."
- Current §2.2 wording: "literature-grounded; granite bounds adjusted once during this study to reduce a probability-saturation artifact observed in early Pohang runs." Table 4 caption: "literature-grounded; see §2.2 for the single granite-bound adjustment." The in-code annotation at `lithology_params.py:60-62` is authoritative.

### 4.6 "Isotonic calibration in §5.8 — is that a real ROC gain?"
- No. §5.8 is explicit: within-sample fit + score on the same Sentinel labels; the monsoon-side uplift (Yecheon +0.053, Chuncheon +0.038) is a tie-handling artifact of collapsing the p≈1 tie block, not out-of-sample ranking gain. Not a generalization claim.

### 4.7 "Why call this an agent paper?"
- §4.5 "Why an agent" is the operating-layer claim: typed AgentTrace with rationale field; dry-run vs executed separation enabling pre-commitment discipline; symmetric per-event failure-mode disclosure. These are three concrete properties a plain Snakemake/Nextflow DAG with a logging decorator does not provide. Deferred follow-on: NL config frontend + in-pipeline model-selection layer on the released AgentTrace schema.

### 4.8 "The manuscript reads like a reproducibility dossier."
- Addressed across R15–R20: operational detail moved to Online Resource 2. User-requested post-APPROVED compression pass at 23:09 further stripped §2.1 run-trace detail, §3.1 Table 2 provenance paragraph + Source rows, §5.3/§5.6 operational narration.

### 4.9 "Figure 3 panel order"
- Figure 3 top-row (a–c): Pohang / Yecheon / Chuncheon. Bottom-row (d–f): ROC curves for the four scoring methods per event. §3.2 references Figure 3a (Pohang) and 3c (Chuncheon) for leave-alone stratification.

### 4.10 "Reference to Youssef et al. 2023"
- Removed in R19 cleanup — inline citation could not be verified against a concrete Youssef 2023 landslide-susceptibility paper without Scholar access. Merghadi 2020 alone covers the ML-landslide-susceptibility positioning.

## 5. Numeric anchors (memorize these)

| Quantity | Pohang 2022 | Yecheon 2023 | Chuncheon 2020 |
|---|---|---|---|
| ROC-AUC (baseline) | 0.612 | 0.449 | 0.499 |
| Scar/non-scar separation | +0.198 | −0.070 | +0.006 |
| Top-1 % recall | 69 % | 14 % | 29 % |
| Positives (px) | 1,099 | 183,507 | 15,571 |
| Base rate | 0.12 % | 1.65 % | 1.24 % |
| IMERG window (exclusive-end) | 2 d (5–7 Sep) | 5 d (13–18 Jul) | 7 d (1–8 Aug) |
| IMERG peak / mean (mm) | 96 / 91 | 216 / 188 | 461 / 403 |
| Slope-alone ROC-AUC | 0.506 | 0.669 | 0.547 |
| Hillslope-masked ROC-AUC | 0.520 | 0.593 | 0.550 |
| Axis 6 NIDR-only ROC-AUC | — (no data) | 0.608 | 0.635 |
| Axis 6 NIDR in-bbox points | 0 | 273 | 18 |
| Precision lift (best single-knob) | 1.31× (F0) | 1.42× (F7 slope>20°) | 1.11× (F7) |

## 6. Decisions locked before submission

- Keep the 6-citation reference list (Baum 2008, Merghadi 2020, Montgomery & Dietrich 1994, Pack 1998, Park 2013, Park WildfireKR 2026); expand if editor requests deeper positioning.
- Single-author paper (E. Park). No co-authors to add.
- English-only; no Korean terms in the main text except event names.
- Figures 1–4 as currently ordered; Figure 5 (pipeline schematic) deferred — manuscript explicitly states "described in prose below; a schematic pipeline figure is not included in this submission" (§2.1).
- Declarations block adopted as written (Section 8 of this doc is the canonical wording — synced with manuscript §Declarations).

## 7. What to do when the review arrives

1. **Do not touch the manuscript markdown until the reviewer letter has been fully read.** Copy the reviewer letter into `review_response/round_1/reviewer_letter.md` (create on first review).
2. Re-read §3 of this file — the layered story. Every reviewer response must preserve the primary/auxiliary/tertiary structure.
3. Match each reviewer comment to a §4 pre-authored response if it matches; otherwise draft a new response.
4. For any number-question, re-pull from `analysis-output/*.json` or `out/*/agent_trace.json` + `out/pohang_2022_run_20260414_1513_C2.log`; do not recall from memory.
5. If the review requests new experiments, the operating-layer claim in §4.5 enables: per-event configs are in `cases/`; re-running is `python -m landslide_kr.agent.orchestrator cases/<event>/config.json` (see `README.md`).
6. Build pipeline: `draft/_integrated_v06_draft.md` (edit) → `pandoc --wrap=preserve --top-level-division=section` to `_body_only.tex` → strip to body (from `\section{1. Introduction}` onward) → concat with R12-backup preamble (abstract block surgically replaced) → tectonic compile → 10 MB PDF with 4 figures embedded. Reference: `SPRINGER_SUBMISSION_KIT.md` has the minimal Python one-liner.
7. Response letter template: `review_response/round_1/response_letter.md` (create from Springer's standard "reviewer comment → author response → manuscript change location" 3-column style).

## 8. Declarations (synced with manuscript §Declarations — use verbatim in cover letter if asked)

**Funding.** Not applicable.

**Competing interests.** The author declares no competing financial or non-financial interests relevant to the content of this article.

**Ethics approval and consent to participate.** Not applicable — public data only.

**Consent for publication.** Not applicable.

**Data availability.** Public EO + administrative data only (GPM IMERG V07, Sentinel-2 L2A via GEE; Copernicus GLO-30 DSM as pre-downloaded COG; KIGAM 1:50 000 Korean geology vector; NIDR via data.go.kr ID 15074816 + VWorld 2.0). Processed outputs (AgentTrace JSON, NIDR GeoJSON, run logs, three-event analysis bundles) released at the code repository. Large intermediate rasters (probability rasters, DEM UTM mosaics) are regeneratable from the released configs; not redistributed.

**Code availability.** <https://github.com/egpark-knu/landslidekr>.

**Materials availability.** Not applicable.

**Author contributions.** E.P. conceived the study, designed the benchmark, implemented the code and analysis, executed the runs, prepared figures/tables, and wrote the manuscript.

## 9. Infrastructure state at freeze

- MAS refine-gate: disabled (3-reviewer APPROVED achieved R20).
- MAS review-revision mode: disabled.
- tmux agent sessions (`agents:codex-1`, `agents:codex-98`, `agents:gemini-1`): can be left running or stopped; not needed until review arrives.
- No scheduled wakeups / loops active on this project.

## 10. Where to find this file if the path changes

- Primary: `/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/REVIEW_RESPONSE_CONTEXT.md`
- Tracked in git: <https://github.com/egpark-knu/landslidekr/blob/main/REVIEW_RESPONSE_CONTEXT.md>
- User memory pointer (via MAS): `~/.claude/projects/-Users-eungyupark-mas-project/memory/project_landslidekr_paper.md`
