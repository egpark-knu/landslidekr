# Draft provenance

The authoritative manuscript is `_integrated_v06_draft.md` in this directory. Supporting artifacts in `draft/`:

| File | Role |
|---|---|
| `_integrated_v06_draft.md` | Authoritative manuscript source. |
| `tables_v0.1.md` | Appendix-table workbook; values match the integrated draft. |
| `_preamble_landslides.tex` | LaTeX preamble (Springer Landslides-style wrapper). |
| `_LandslideKR_v0.8.1_journal.tex` | Rendered LaTeX (preamble + body from the integrated draft). |
| `_LandslideKR_v0.8.1_journal.pdf` | Rendered PDF (Tectonic/XeTeX). |
| `_working_fragments/` | Superseded per-section working drafts and older render snapshots; not part of the submitted release and may disagree with the integrated draft. |

Reviewers and downstream readers should read the integrated draft (`_integrated_v06_draft.md`) and the rendered PDF. Numeric backing lives in `../analysis-output/` (JSON/CSV) and `../out/*/` (per-event rasters, traces, and logs); case-configuration provenance lives in `../cases/*/config.json`.
