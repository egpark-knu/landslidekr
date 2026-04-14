# Springer Landslides submission kit

Template pathway for porting the current authoritative manuscript (`draft/_integrated_v06_draft.md` → `draft/_LandslideKR_v0.8.1_journal.tex`) into the official Springer Nature **sn-jnl** class used by *Landslides*.

## 1. Template source

Landslides (Springer, ISSN 1612-5118) follows the standard Springer Nature author template. Current template (v2.2+) lives in the official Springer LaTeX Template bundle:

- Official download page (Springer Nature LaTeX author support):
  <https://www.springernature.com/gp/authors/campaigns/latex-author-support>
- Overleaf mirror (recommended for web-based editing):
  <https://www.overleaf.com/latex/templates/springer-nature-latex-template/myxmhdsbzkyd>

Files delivered in the bundle (put next to the manuscript .tex):
- `sn-jnl.cls` — main class
- `sn-basic.bst`, `sn-mathphys-ay.bst`, `sn-mathphys-num.bst`, `sn-vancouver.bst`, `sn-nature.bst` — bibliography styles
- `sn-article.tex` — minimal author template that we fork for the submission

## 2. Documentclass options for Landslides

Landslides uses **sn-basic** reference style (author–year for earth-science journals). Use:

```latex
\documentclass[sn-basic]{sn-jnl}
% options: sn-basic, sn-mathphys-ay, sn-mathphys-num, sn-vancouver-ay,
%          sn-vancouver-num, sn-apa, sn-chicago, sn-nature
```

Two-column vs single-column: Landslides is published single-column; the default `sn-basic` is single-column so no extra flag is needed.

## 3. Skeleton port from the current draft

Current draft structure already matches Springer's required ordering:

| Springer required | Current draft location |
|---|---|
| Title block | `_integrated_v06_draft.md:1` |
| Abstract | `_integrated_v06_draft.md:3–5` |
| Keywords | injected after abstract in rendered PDF |
| §1 Introduction | `_integrated_v06_draft.md:9–22` |
| §2 Methods | `_integrated_v06_draft.md:26–69` |
| §3 Results | `_integrated_v06_draft.md:71–?` |
| §4 Discussion | §4.1–§4.5 already layered |
| §5 (optional Robustness) | §5.1–§5.8 |
| §6 Limitations | present |
| §7 Conclusions | present |
| Declarations | present (NEW as of 2026-04-14 23:18 KST) |
| References | present (6 DOI-verified entries) |

### Minimal sn-article.tex wrapper (to replace the current R12-backup-based preamble wrapper)

```latex
\documentclass[sn-basic]{sn-jnl}

% Packages already used in the current build (fontspec, amsmath, amssymb,
% graphicx, booktabs, longtable, array, calc, caption, url, hyperref,
% xcolor, lineno, authblk) — most of these are either bundled or compatible
% with sn-jnl. Minor adjustments:
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{amsmath, amssymb}
\usepackage{url}
\usepackage{hyperref}
\usepackage{lineno}\linenumbers

\title[Event-typology-dependent applicability of SHALSTAB in Korea]{%
  Event-type-dependent applicability of a steady-state physical landslide
  model: a three-event Korean retrospective benchmark with reproducible
  execution traces}

\author*[1]{\fnm{Eungyu} \sur{Park}}
  \email{egpark@knu.ac.kr}
\affil[1]{\orgdiv{Department of Geology},
          \orgname{Kyungpook National University},
          \city{Daegu}, \country{Republic of Korea}}

\abstract{%
  [paste current abstract verbatim from _integrated_v06_draft.md:5]
}

\keywords{shallow rainfall-triggered landslides, SHALSTAB,
          Monte Carlo ensemble, Korean monsoon, Typhoon Hinnamnor,
          Sentinel-2 NDVI-change, reproducible benchmark,
          agent-orchestrated pipeline, precision lift}

\begin{document}
\maketitle

% Body: \section{1 Introduction} ... \section{7 Conclusions} ...
% Figures/tables: same content as current tex; pandoc-style paths already absolute

\section{Declarations}
% paste current Declarations block from _integrated_v06_draft.md

\bibliography{landslidekr}  % if converting to .bib
\end{document}
```

## 4. Landslides-specific format points

- **Abstract**: Springer recommends 150–250 words; current abstract is ~290 words — trim at submission time if the editor requests, but Landslides accepts longer abstracts on technical benchmarks.
- **Keywords**: 5–8 keywords recommended; current draft has 9 — trim one ("agent-orchestrated pipeline" or "precision lift") if editor asks.
- **Figures**: submit as separate PNG/TIFF files (300 dpi color, 600 dpi line art) plus caption list; current figures in `figures/fig{1,2,3,6}_*.png` already meet Springer's 300 dpi minimum.
- **Reference format**: author–year in text (sn-basic). Current draft already uses this style inline ("[Montgomery and Dietrich, 1994]") — will render natively under sn-jnl.
- **Line numbers**: enabled by default for reviewer convenience (`\linenumbers`) — already in current wrapper.
- **Declarations section**: now included as the last content block before References (2026-04-14 23:18 KST update).
- **Code availability statement**: points to <https://github.com/egpark-knu/landslidekr> (now explicit in Declarations).

## 5. Submission steps (Springer Editorial Manager)

1. Editorial Manager URL for Landslides: <https://www.editorialmanager.com/land>
2. Create / sign in with corresponding-author ORCID.
3. Article type: **Original Paper** (benchmark + reproducibility infrastructure).
4. Upload:
   - Main manuscript `.tex` + `.bib` + `.cls` (sn-jnl) — OR `.pdf` (current PDF is already submission-ready as a reviewer proof)
   - Figure files (`figures/*.png`, 4 files)
   - Supplementary material (Online Resource 2 — operational detail): the `docs/` folder contents (`PIPELINE_DETAIL.md`, `NIDR_API_SPEC.md`, `ROBUSTNESS_PLAN.md`, `SAR_INTEGRATION_PLAN.md`, `VWORLD_KEY_GUIDE.md`) compressed as one zip
   - Supplementary material (Online Resource 1 — backing artifacts): a zip of `analysis-output/*.json`, `analysis-output/*.csv`, `cases/*/config.json`, `out/*/agent_trace.json`, `out/*/nidr.geojson`, `out/*.log`
5. Cover letter (draft to follow in `COVER_LETTER.md`).
6. Suggested reviewers: 3 names with institutional affiliations + emails (draft to follow in `SUGGESTED_REVIEWERS.md`).
7. Competing interests: the Declarations block is already drafted as none.

## 6. What to do right now before submission

- [ ] Download `sn-jnl.cls` + `sn-basic.bst` from Springer / Overleaf.
- [ ] Port `draft/_LandslideKR_v0.8.1_journal.tex` to use `\documentclass[sn-basic]{sn-jnl}` (minimal edit; current preamble's fontspec + packages remain compatible).
- [ ] Re-render with the sn-jnl class and verify figure placement.
- [ ] Trim abstract to 250 words if editor asks.
- [ ] Draft cover letter (one page; I will prepare `COVER_LETTER.md` on request).
- [ ] Draft suggested-reviewers list (I will prepare `SUGGESTED_REVIEWERS.md` on request).
- [ ] Deposit a Zenodo DOI for the v0.8.1 GitHub release upon acceptance.

## 7. Where the GitHub URL now appears

<https://github.com/egpark-knu/landslidekr> is cited in:
- **Declarations / Code availability** — primary canonical pointer
- Manuscript §2.1 "constructed-resource operating layer" (implicitly via "released code")
- `draft/DRAFT_PROVENANCE.md` (package-internal)
- `README.md` on the repo itself (landing page)

No other placement is needed in the main text — Landslides convention is that the Code availability statement in Declarations is the authoritative pointer, and duplicating the URL in §2.1 or §7 would be redundant.
