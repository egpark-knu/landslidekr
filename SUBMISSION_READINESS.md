# LandslideKR — Submission Readiness Checklist (v0.6, 2026-04-14 18:35 KST)

A concise yes/no readiness ledger for the corresponding author's go/no-go decision.

## Manuscript text (sections + tables)

| Section | Status | Words |
|---|---|---|
| §1 Introduction | Drafted (v0.3, benchmark-first, agent demoted) | 1,302 |
| §2 Methods | Drafted (v0.1, code-text aligned to `compute_stability`, AgentTrace fields, Copernicus DSM COG) | 1,817 |
| §3 Results | Drafted (v0.1, 3-event tables + §3.6 preregistration disclosure) | 1,957 |
| §4 Discussion | Drafted (v0.1, working-hypothesis language only) | 1,303 |
| §5 Robustness | Drafted (v0.1, **Axis 3 EXECUTED**, others marked Deferred) | 1,391 |
| §6 Limitations | Drafted (v0.1, 10 items) | 641 |
| §7 Conclusions | Drafted (v0.1, 5 headline findings) | 478 |
| Tables 1–6 | Drafted, synced with §3 numbers | (in `tables_v0.1.md`) |
| **Sections total** | **8,889 words** | |
| **With tables** | **10,339 words** | |

Integrated single file: `draft/_integrated_v06_draft.md`.

## Figures

| Figure | Status | File |
|---|---|---|
| Fig 1 — Pohang prob + scar + histogram | Made | `figures/fig1_pohang_2022.png` |
| Fig 2 — Yecheon prob + scar + histogram | Made | `figures/fig2_yecheon_2023.png` |
| Fig 3 — 3-event contrast (6-panel: prob × elev decile + ROC × 4 scorings × 3 events) | Made | `figures/fig3_event_contrast.png` |
| Fig 4 — *(reserved for third-event single-panel if reviewers ask)* | Pending | — |
| Fig 5 — Agent architecture infographic | Pending (PaperBanana, not matplotlib) | — |
| Fig 6 — Precision lift vs kept-fraction (3 events) | Made | `figures/fig6_precision_lift.png` |
| Fig 7 — Robustness composite | Pending (would consolidate Axis 3 CV plot once n=20 expansion lands) | — |
| Fig 02 — PR curves (3 events) | Made | `analysis-output/figures/figure-02-pr-curves.png` |

Critical figures (1, 2, 3, 6) are in place. Fig 5 (agent architecture) is the single submission-impact gap; recommended quick draft via PaperBanana before submission.

## Quantitative artifacts released

- `analysis-output/far_filter_results.{json,csv}` — 9 filters × 3 events
- `analysis-output/pr_auc_summary.json` — AP per event
- `analysis-output/axis3_repeatability.{json,csv}` — 5 seeds × 3 events
- `analysis-output/axis6_label_ablation.{json,csv}` — Variant A executed, B/C/D blocked by environmental constraint
- `out/{pohang_2022,extreme_rainfall_2023,chuncheon_2020}/` — full per-event raster outputs + AgentTrace JSON
- `cases/{pohang_2022,extreme_rainfall_2023,chuncheon_2020}/config.json` — frozen configs

## Code released

- `landslide_kr/` — full agent + models + collectors + IO package
- `scripts/run_case.py` — case runner
- `scripts/apply_far_filters.py` — FAR-filter analysis
- `scripts/axis3_stochastic_repeatability.py` — Axis 3
- `scripts/axis6_label_ablation.py` — Axis 6 framework
- `scripts/make_fig{1_pohang,2_yecheon,3_event_contrast,6_precision_lift}.py`
- `requirements.txt`

## Disclosures (load-bearing — all in main text)

- Pohang executed run is Sentinel-scar-only (NIDR configured but not joined) — §2.3 + Table 5
- Yecheon executed run is Sentinel-scar-only (NIDR API timeout) — §2.3 + Table 5
- Chuncheon executed run is Sentinel-scar-only (NIDR returned 0 records under first-run config) — §2.3 + Table 5
- Chuncheon "NOT a true preregistration" — §3.6 first paragraph + `cases/chuncheon_2020/config.json::preregistration`
- VWorld API blocker (3 attempts hung, environmental, off-network re-run pending) — §5.6
- Robustness Axes 1, 4, 5, 7 deferred to follow-on work — §5.9 status table

## Hard go/no-go checklist

| Item | Status | Decision-relevant note |
|---|---|---|
| Three executed events with traces released | ✅ | Pohang, Yecheon, Chuncheon |
| Headline metric (ROC-AUC + separation) reproducible | ✅ | Same script + same configs reproduces §3.1 |
| Stochastic stability of headline metric | ✅ | Axis 3 CV ≤ 0.5–7 % per metric |
| Standard precision-recall view (AP) | ✅ | §3.5 + `pr_auc_summary.json` |
| Code-text consistency (equation, function names, schema) | ✅ | §2 verified against `shalstab.py`/`orchestrator.py` |
| Tables consistent with §3 numbers | ✅ | Tables 1, 2, 3, 5, 6 synced |
| Provenance disclosure per event | ✅ | §2.3 + Table 5 + §3.1 |
| Working-hypothesis language only on n=3 | ✅ | §3.6, §4.1, §4.3, §7 |
| Korean-free in paper + figures | ✅ | grep 0 hits |
| Axis 6 NIDR ablation populated | ❌ | VWorld blocker, deferred to follow-on |
| Field-verified ground truth | ❌ | Not available for these events; documented |
| LaTeX template applied | ❌ | Markdown draft only; conversion pending |
| Figure 5 (agent architecture infographic) | ❌ | PaperBanana draft pending |

## Recommended next steps before submission (priority order)

1. **(High) Convert markdown to LaTeX** using the Landslides Springer template; ~2-4 hours of layout work.
2. **(High) Generate Fig 5** via PaperBanana with the 11-step trace as the visual anchor.
3. **(Medium) Run Axis 3 with n=20 seeds** for tighter CV bounds (script accepts seed list; ~30 min compute).
4. **(Optional / off-network)** Retry Chuncheon VWorld re-run from a non-KNU network; populate Axis 6 variants B/C/D.
5. **(Optional)** Bibliography verification — `draft/related_work_seed.md` has 15 candidate citations; verify each via Semantic Scholar / CrossRef before final inclusion.

## Risk register if submitted as-is

| Risk | Severity | Mitigation in current draft |
|---|---|---|
| "Where is the agent decision?" | Medium | Reframed as enabling-infrastructure; future-work flag explicit |
| "n=3 too thin for typology claim" | Medium | Working-hypothesis language throughout; Chuncheon designed to disambiguate |
| "Chuncheon is post-hoc tie-breaker" | Medium-High | §3.6 disclosure block + `cases/chuncheon_2020/config.json::preregistration` |
| "Why do Sentinel labels dominate?" | Medium | §2.3 + Table 5 disclose per-event provenance; §6.4 lists as limitation |
| "Why no Axis 4/5/7 sensitivity?" | Medium | §5 deferred status explicit; Axis 3 CV provides the strongest single piece of robustness evidence |
| "Why no PR-AUC?" | Low | §3.5 includes AP per event, PR curve in `analysis-output/figures/` |

## Author decision summary

The manuscript is **defensible at the level it claims** (a three-event Korean retrospective benchmark + an enabling-infrastructure agent + working-hypothesis typology). It is **not** a submission-grade demonstration of agent-driven model selection, and the v0.6 draft does not pretend otherwise. Whether to submit this week depends on the author's tolerance for "honest deferred-work ledger" framing in §5 versus the value of an additional 1–2 weeks executing Axes 4/5/7 plus the off-network Axis 6 re-run.
