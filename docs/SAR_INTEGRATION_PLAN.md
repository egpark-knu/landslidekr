# Sentinel-1 SAR Integration — Planning Document

Status: **Future work.** Not integrated in v0.3 release. Listed in manuscript §5 Limitations item 8 and §6 Conclusions.

This document captures the design so a future iteration can implement it without re-litigating the scope.

## 1. Motivation

Sentinel-2 NDVI-change scars miss two failure modes:
- **Cloud-persistent monsoon scenes** — 2023 Korean monsoon produced ≥5 consecutive cloudy days in the immediate 7-day post window for parts of the Yecheon AOI.
- **Bare rock / shadowed north-facing scars** — low pre-event NDVI means dNDVI below detection threshold.

Sentinel-1 C-band SAR is cloud-penetrating and sensitive to surface-roughness changes that accompany shallow landsliding. Pairing S1 backscatter-change with S2 NDVI-change is the standard robustness extension in recent disaster-EO literature (e.g., Ferrario et al., 2023; Handwerger et al., 2022).

## 2. Scope in LandslideKR

This integration targets the **reference-label side only** in the first pass. It does **not** change the physical model, the agent's step chain, or the evaluation protocol — only the label source.

Two roles:

| Role | Purpose | Affects |
|---|---|---|
| A. Label augmentation | Add S1 log-ratio scars to the union label | `consensus_label.tif` |
| B. Label sanity check | Flag S2-only scars without S1 corroboration as "low-confidence" | new `scar_confidence.tif` side product |

Role A increases recall; Role B quantifies FP risk in the Sentinel-2-only layer that §4.4 discusses.

## 3. Data and preprocessing

| Item | Choice |
|---|---|
| Collection | `COPERNICUS/S1_GRD` (IW, VV + VH, dB) |
| Orbit | descending only (consistent) |
| Time windows | pre: 30 d before event start; post: 30 d after event end |
| Speckle filter | Refined Lee 5×5 on raw σ⁰ |
| Terrain flattening | GEE built-in `ee.Algorithms.Terrain` not sufficient — use the Vollrath et al. (2020) angular-based volumetric model published as `users/andreasvollrath/Sentinel-1/slope_correction` |
| Resolution | native 10 m; reproject to match Pohang (10 m) or Yecheon (30 m, auto-scaled) |
| Polarization | VH primary (vegetation/roughness sensitivity); VV as secondary |

## 4. Change detection

Log-ratio on median composites:

```
LR_VH = 10 · log10( median(post_VH) / median(pre_VH) )
```

Threshold rule (paired with S2):

```
sar_scar = (LR_VH < −2.0 dB) ∧ (slope > 10°) ∧ (landcover ≠ water)
```

The `−2.0 dB` threshold is the conservative default from the published Korean landslide SAR literature; tune per-event within ±0.5 dB via ROC on the S2-confirmed subset.

## 5. Label fusion logic

Replace the current `consensus_label = nidr_buffer ∪ s2_scar` with:

```
high_conf_scar = s2_scar ∧ sar_scar
mid_conf_scar  = (s2_scar ⊕ sar_scar)    # exclusive-or
low_conf_scar  = nidr_only

consensus_label   = high ∪ mid ∪ low
scar_confidence   = 2 · high + 1 · mid + 0.5 · low
```

Evaluation in §3 reports metrics at three operating points: high-conf-only, high+mid, full union.

## 6. Agent orchestrator change

New step slots into the existing 11-step trace between `detect_scars` and `fetch_nidr`:

```
3.5  detect_scars_sar   — S1 log-ratio scars
```

Implementation file: `landslide_kr/collectors/sentinel1.py` (to be created, mirrors `sentinel2.py`).

The `consensus_label` step (current step 10) is the only downstream point that changes.

## 7. GEE quota and timing

- Pohang AOI (600 km²): expected export ≈ 12 MB @ 10 m, well within the 50 MB `getDownloadURL` cap.
- Yecheon AOI (12 100 km²): expected export ≈ 240 MB @ 10 m → will require 30 m auto-scale (matching current S2 path) or tiled export. Use the same scale logic already implemented in the S2 collector.

## 8. Validation experiments planned for the next paper iteration

1. **S1+S2 vs S2-only label** — re-run both events with the fused label; does the rank order (Pohang Go / Yecheon rank-inverted) survive?
2. **S1 confidence gating on §3.3 post-hoc alternatives** — does hillslope-masked SHALSTAB's AUC improvement hold when FPs from S2-only are downweighted?
3. **S2-only false-positive characterization** — S2-only scars that lack S1 corroboration: spatial clustering with floodplains? Harvested fields? This quantifies the §4.4 concern directly.

## 9. Non-goals for the SAR integration pass

- We are **not** adding InSAR coherence loss in this pass (needs burst-level SLC, breaks the GEE-only workflow).
- We are **not** using SAR for pre-event soil-moisture conditioning of SHALSTAB yet — that touches the physical model and is a separate research question.
- We are **not** claiming SAR integration enables agentic model selection. Selection remains a separate future layer.

## 10. Dependencies and blockers

- ✅ GEE service account with `COPERNICUS/S1_GRD` access — already available in `~/.mas/gee.json`.
- ⏳ Vollrath slope-correction asset access — public Earth Engine asset, no additional credentials.
- ⏳ Per-event threshold tuning requires the S2-confirmed subset — depends on current v0.3 benchmark being frozen (which it now is).

## 11. Effort estimate (engineering-only)

| Task | Notes |
|---|---|
| `sentinel1.py` collector (mirror of s2) | straightforward port |
| Slope-correction wrapper | single GEE function |
| Label-fusion refactor in `orchestrator.py` | three-valued confidence + union |
| `consensus_label` writer update | add `scar_confidence.tif` as side product |
| Two-event re-run | reuses existing case configs; Yecheon 30 m path already proven |
| Figures 5-6 (SAR overlay + confidence histogram) | mirrors fig1-2 script scaffolding |

Effort is bounded by GEE export times, not by code. No new external dependencies.

## 12. What this document does **not** commit

This plan is a roadmap, not a schedule. Its presence in the released repository is a truthful statement that SAR integration is a scoped future extension with a designed path, not a vague aspiration. The v0.3 manuscript explicitly states that Sentinel-1 is not part of the released benchmark, and that statement must remain unless all items in §8 have been executed.
