# analysis-output — release package authoritative files

This directory holds the numeric backing for the manuscript.

**Authoritative (three-event, submission-safe):**
- `far_filter_results.json`, `far_filter_results.csv` — 9 filters × 3 events (Pohang, Yecheon, Chuncheon)
- `axis6_label_ablation.json`, `axis6_label_ablation.csv` — variant A/B/C/D × 3 events
- `axis3_repeatability.json`, `axis3_repeatability.csv` — 5 seeds × 3 events (default-lithology fallback; see §5.3)
- `axis4_param_sensitivity.json` — 8 parameter corners × 3 events
- `post_hoc_refinement.json` — baseline + hillslope-masked + slope-alone + slope×relief × 3 events
- `calibration_isotonic.json` — within-sample isotonic diagnostic × 3 events

**Superseded (two-event early draft, kept for provenance, NOT authoritative):**
- `stats-appendix.md.SUPERSEDED_two_event_notes`
- `figure-catalog.md.SUPERSEDED_two_event_notes`
- `analysis-report.md.SUPERSEDED_two_event_notes`

The three-event synthesis lives in the manuscript (`../draft/_integrated_v06_draft.md` §3, §5) and the appendix tables (`../draft/tables_v0.1.md`). The `.SUPERSEDED_*` markdowns above are not part of the submission package; they are retained for traceability of how the benchmark grew from two events to three.
