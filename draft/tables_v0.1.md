# Manuscript Tables — v0.1 draft values

Tables verified against the executed-run artifacts.

## Table 1 — Event and data configuration

| Field | Pohang 2022 | Yecheon 2023 | Chuncheon 2020 |
|---|---|---|---|
| Rainfall type | Typhoon Hinnamnor | 2023 Central Korea Monsoon | 2020 Gangwon Monsoon |
| Event window | 2022-09-05 – 2022-09-07 | 2023-07-13 – 2023-07-18 | 2020-08-01 – 2020-08-08 |
| AOI bbox (lon/lat) | 129.20, 36.00, 129.50, 36.20 | 127.60, 36.30, 128.90, 37.00 | 127.60, 37.75, 127.95, 38.00 |
| AOI area (km²) | ~597 (computed from bbox) | ~8 990 (computed from bbox) | ~850 (computed from bbox) |
| Terrain | hillslope-dominated | mixed-terrain (floodplain + hillslope) | small mountainous |
| Lithology mix | granite-dominated | sedimentary + metamorphic + alluvium | granite + metamorphic (per KIGAM 1:50 000) |
| IMERG window duration (filterDate exclusive-end) | 2 days | 5 days | 7 days |
| Station-reported rainfall | 412 mm / 24 h (Pohang station) | ~580 mm cumulative (Yecheon station) | — |
| IMERG peak pixel over window | 96 mm | 216 mm | 461 mm |
| IMERG AOI-mean over window | 91 mm | 188 mm | 403 mm |
| DEM source | Local Copernicus DSM COG 30 m | Local Copernicus DSM COG 30 m | Local Copernicus DSM COG 30 m |
| Scar scale | 10 m (AOI < 0.2 deg²) | 30 m auto-scaled (AOI > 0.2 deg²) | 10 m (AOI ≈ 0.087 deg²) |
| Baseline §3.1 label | Sentinel-2 scar | Sentinel-2 scar | Sentinel-2 scar |
| NIDR in §5.6 ablation | 0 in-bbox (Guryongpo east of bbox) | 273 in-bbox | 18 in-bbox |

## Table 2 — Baseline metrics (SHALSTAB MC, n=100 realizations/pixel)

| Metric | Pohang 2022 | Yecheon 2023 | Chuncheon 2020 |
|---|---|---|---|
| N valid pixels | 912 384 | 11 113 520 | 1 259 904 |
| Actual positives (scar) | 1 099 (0.120 %) | 183 507 (1.651 %) | 15 571 (1.236 %) |
| POD (recall) | 0.9145 | 0.4838 | 0.7152 |
| FAR (raw) | 0.9984 | 0.9855 | 0.9879 |
| CSI | 0.0016 | 0.0143 | 0.0121 |
| F1 | 0.0032 | 0.0281 | 0.0239 |
| Precision | 0.0016 | 0.0145 | 0.0121 |
| ROC-AUC (sklearn) | **0.6118** | **0.449** | **0.4992** |
| Scar mean prob | 0.887 | 0.464 | 0.685 |
| Non-scar mean prob | 0.688 | 0.534 | 0.679 |
| Separation (scar − non-scar) | **+0.198** | **−0.070** | **+0.006** |
| Top-1 % recall | 0.692 | 0.144 | 0.290 |

## Table 3 — Post-hoc refinement comparison (ROC-AUC)

Hillslope mask: slope > 10° ∩ local relief > 30 m in a 33-pixel window. Slope alone: Horn slope normalized to [0, 1]. Slope × relief: slope_score × (relief / relief_max).

| Method | Pohang 2022 | Yecheon 2023 | Chuncheon 2020 |
|---|---|---|---|
| Baseline SHALSTAB MC | **0.612** | 0.449 | 0.499 |
| Hillslope-masked | 0.520 | **0.593** | **0.550** |
| Slope alone | 0.506 | **0.669** | 0.547 |
| Slope × relief | 0.527 | 0.641 | 0.536 |

On Yecheon the slope-alone ranking beats every SHALSTAB variant. On Pohang the baseline SHALSTAB leads. On Chuncheon the topographic predictors deliver consistent gains over baseline 0.499, reaching 0.536 to 0.550; hillslope-masked SHALSTAB is the best alternative there at 0.550. The pattern across all three events: monsoon AOIs benefit from topographic-only or topographic-augmented scorings; the typhoon AOI prefers the unmodified physical model.

## Table 4 — Lithology-class Monte Carlo parameter bounds (literature-grounded; see §2.2 for the single granite-bound adjustment)

| Class | Friction angle φ (°) | Cohesion c (Pa) | Transmissivity T (m²/s) | Soil depth z (m) | Rationale |
|---|---|---|---|---|---|
| granite | 28 – 38 | 2 000 – 10 000 | 1 × 10⁻⁴ – 1 × 10⁻³ | 0.8 – 2.5 | Park et al. (2013) Pohang-area residual soil; tight φ, high-floor cohesion and transmissivity |
| volcanic | 30 – 40 | 2 000 – 12 000 | 1 × 10⁻⁴ – 1 × 10⁻³ | 0.5 – 2.0 | Weathered volcanic (Jeju, SE Korea ridges) |
| sedimentary | 22 – 34 | 500 – 5 000 | 2 × 10⁻⁵ – 2 × 10⁻⁴ | 1.0 – 3.0 | Mudstone / sandstone residual |
| metamorphic | 26 – 36 | 1 500 – 8 000 | 3 × 10⁻⁵ – 3 × 10⁻⁴ | 0.8 – 2.5 | Gneiss / schist residual |
| alluvium | 25 – 35 | 500 – 3 000 | 5 × 10⁻⁴ – 5 × 10⁻³ | 1.5 – 5.0 | Colluvium / fluvial — stable on low slopes |
| default (fallback) | 28 – 36 | 1 000 – 6 000 | 5 × 10⁻⁵ – 5 × 10⁻⁴ | 0.8 – 2.5 | Used when lithology layer unavailable |

Soil density is uniform across classes at 1 600 – 2 000 kg m⁻³. Transmissivity is sampled in log-space; all other parameters are sampled uniformly within the stated bounds. n = 100 realizations per pixel.

## Table 5 — Label provenance (executed vs planned)

| Event | Planned label | Executed label | Reason for gap |
|---|---|---|---|
| Pohang 2022 | NIDR 30 m point buffer ∪ Sentinel-2 scar | Sentinel-2 scar (baseline) | NIDR records do not fall within the published bbox; §5.6 ablation excludes Pohang |
| Yecheon 2023 | NIDR 30 m point buffer ∪ Sentinel-2 scar | Sentinel-2 scar (baseline) | NIDR-augmented label-layer ablation in §5.6 (273 in-bbox points) |
| Chuncheon 2020 | NIDR 30 m point buffer ∪ Sentinel-2 scar | Sentinel-2 scar (baseline) | NIDR-augmented label-layer ablation in §5.6 (18 in-bbox points; small-N town-centroid resolution) |

## Table 6 — FAR-filter precision-lift (source: the FAR-filter results (Online Resource 1))

Interpretation: At these positive-class rates (0.12 – 1.65 %), raw FAR is structurally pinned near 99 %; we report precision lift over base rate jointly with POD and kept-fraction.

### Pohang 2022 (base rate 0.1205 %)

| Filter | POD | Precision | Lift | Kept-fraction |
|---|---|---|---|---|
| F0 baseline | 0.914 | 0.00158 | 1.31× | 69.6 % |
| F1 hillslope | 0.208 | 0.00174 | 1.44× | 14.4 % |
| F2 prob top-10 % | 0.692 | 0.00156 | 1.30× | 53.3 % |
| F3 prob top-5 % | 0.692 | 0.00156 | 1.30× | 53.3 % |
| F4 prob top-1 % | 0.692 | 0.00156 | 1.30× | 53.3 % |
| F5 F1 ∩ top-10 % | 0.065 | 0.00188 | **1.56×** | 4.15 % |
| F6 F1 ∩ top-5 % | 0.065 | 0.00188 | **1.56×** | 4.15 % |
| F7 slope > 20° | 0.049 | 0.00120 | 1.00× | 4.93 % |
| F8 F1 ∩ slope > 20° ∩ prob > 0.9 | 0.023 | 0.00090 | 0.75× | 3.04 % |

### Yecheon 2023 (base rate 1.6512 %)

| Filter | POD | Precision | Lift | Kept-fraction |
|---|---|---|---|---|
| F0 baseline | 0.484 | 0.01448 | 0.88× | 55.2 % |
| F1 hillslope | 0.417 | 0.02115 | 1.28× | 32.5 % |
| F2 prob top-10 % | 0.144 | 0.00968 | 0.59× | 24.5 % |
| F3 prob top-5 % | 0.144 | 0.00968 | 0.59× | 24.5 % |
| F4 prob top-1 % | 0.144 | 0.00968 | 0.59× | 24.5 % |
| F5 F1 ∩ top-10 % | 0.097 | 0.01913 | 1.16× | 8.37 % |
| F6 F1 ∩ top-5 % | 0.097 | 0.01913 | 1.16× | 8.37 % |
| F7 slope > 20° | 0.268 | 0.02339 | **1.42×** | 18.9 % |
| F8 F1 ∩ slope > 20° ∩ prob > 0.9 | 0.122 | 0.02246 | 1.36× | 8.95 % |

### Chuncheon 2020 (base rate 1.2359 %)

| Filter | POD | Precision | Lift | Kept-fraction |
|---|---|---|---|---|
| F0 baseline | 0.715 | 0.01207 | 0.98× | 72.82 % |
| F1 hillslope | 0.581 | 0.01338 | **1.08×** | 53.66 % |
| F2 prob top-10 % | 0.290 | 0.01153 | 0.93× | 31.20 % |
| F3 prob top-5 % | 0.290 | 0.01153 | 0.93× | 31.20 % |
| F4 prob top-1 % | 0.290 | 0.01153 | 0.93× | 31.20 % |
| F5 F1 ∩ top-10 % | 0.180 | 0.01346 | 1.09× | 16.61 % |
| F6 F1 ∩ top-5 % | 0.180 | 0.01346 | 1.09× | 16.61 % |
| F7 slope > 20° | 0.426 | 0.01371 | **1.11×** | 38.44 % |
| F8 F1 ∩ slope > 20° ∩ prob > 0.9 | 0.195 | 0.01307 | 1.06× | 18.39 % |

Note: F2 / F3 / F4 are identical per event because the SHALSTAB MC probability distribution is bimodal (peaks at p = 0 and p = 1); the top-1 / 5 / 10 % quantile thresholds all collapse to the p = 1.0 tier. This is reported as a calibration limitation in §5.8.
