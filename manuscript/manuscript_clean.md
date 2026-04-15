# Event-type-dependent applicability of a steady-state physical landslide model: a three-event Korean retrospective benchmark with reproducible execution traces

**Eungyu Park**$^{1,2,*}$, **Taeyu Kim**$^{1,2}$, and **Jangwon Park**$^{1,2}$

$^{1}$ School of Earth System Sciences, Kyungpook National University, Daegu 41566, Republic of Korea
$^{2}$ GeoAI Alignment, Inc., Daegu 41544, Republic of Korea

$^{*}$ Corresponding author: Eungyu Park (e-mail: egpark@knu.ac.kr)


## Abstract

We report a three-event Korean retrospective benchmark of a lithology-conditional Monte Carlo SHALSTAB ensemble across one typhoon (Pohang 2022, ~600 km$^{2}$, hillslope-dominated) and two monsoon events (Yecheon 2023, ~9 000 km$^{2}$, mixed-terrain; Chuncheon 2020, ~850 km$^{2}$, small mountainous) that together separate rainfall typology from area-of-interest size and terrain mix. Pre-event landslide nowcasting in monsoon-dominated East Asia depends on physical models whose hillslope-steady-state assumption is rarely tested across structurally distinct rainfall events on the same operational pipeline, and Korea has no published reproducible multi-event benchmark of this kind. We evaluate against an event-window Sentinel-2 NDVI-change scar reference, with an annual administrative-area NIDR-report augmentation reported separately as a label-source sensitivity check in §5.6 and release the eleven-step traced data-and-compute orchestrator that produces the per-event rasters and core confusion-matrix-plus-ROC-AUC evaluation outputs, with the additional decile and probability-separability statistics computed in the offline analysis bundle. SHALSTAB shows ROC-AUC 0.612 with positive scar/non-scar mean-probability separation +0.198 on the typhoon event, is rank-inverted on the large monsoon AOI (ROC-AUC 0.449, separation -0.070), and is essentially random on the small monsoon AOI (ROC-AUC 0.499, separation +0.006), while a topographic predictor (slope alone) reaches ROC-AUC 0.669 on the large monsoon AOI; raw false-alarm rate is structurally pinned near 99 % at the observed positive-class rates of 0.12–1.65 % so we report precision lift over base rate jointly with recall and kept-fraction. The three-event divergence motivates an agentic model-selection layer as future work, but the executed contribution of this paper is the open benchmark and the disclosed re-executable infrastructure, not a demonstrated agent capability.

Keywords: shallow rainfall-triggered landslides; SHALSTAB; Monte Carlo ensemble; Korean monsoon; Typhoon Hinnamnor; Sentinel-2 NDVI-change; reproducible benchmark; agent-orchestrated pipeline; precision lift

# 1. Introduction

Shallow rainfall-triggered landslides are a dominant geohazard across mountainous, monsoon-dominated East Asia, and pre-event nowcasting depends on physical models whose hillslope-steady-state assumption is rarely tested across structurally distinct rainfall typologies on the same operational pipeline. Korea offers a clean test set, with active national-scale nonstructural landslide mitigation infrastructure [Eu et al., 2025] generating administrative-area inventories such as NIDR (§2.3). Typhoon Hinnamnor produced short-duration high-intensity rainfall on a ~600 km$^{2}$ hillslope-dominated catchment around Pohang in September 2022. The 2023 central-Korea monsoon delivered multi-day distributed heavy rainfall across a ~9 000 km$^{2}$ mixed-terrain region spanning Yecheon, Yeongju, and Cheongju (IMERG-computed 188 mm AOI-mean, 216 mm peak pixel over the 13–18 July event window; ~580 mm cumulative reported at Yecheon station). The 2020 Gangwon monsoon hit a ~850 km$^{2}$ small mountainous AOI around Chuncheon. Together these three events separate rainfall typology (typhoon vs monsoon) from area-of-interest size and terrain mix, allowing one binary factor to be disambiguated from the other in a way no single event can.

This event-type-versus-AOI question is not yet answered in the published Korean literature. SHALSTAB [Montgomery and Dietrich, 1994], TRIGRS [Baum et al., 2008], and SINMAP [Pack et al., 1998] compute slope-instability indices from topography, soil strength, and pore pressure; they are interpretable and physically grounded but parameter-sensitive at scales where the hillslope assumption breaks down. Machine-learning classifiers trained on regional landslide inventories [Merghadi et al., 2020; Lee et al., 2024; Lee et al., 2025] report high accuracies but lose interpretability and generalize poorly when training sets are small or spatially biased. Neither tradition has converged on a preferred workflow for Korean nowcasting across heterogeneous rainfall typologies, and neither has released a reproducible Korean multi-event benchmark whose execution provenance is documented per event, despite recent advances in extreme-rainfall remote-sensing detection [Chrysafi et al., 2024].

We produce that benchmark by running a lithology-conditional Monte Carlo SHALSTAB ensemble through an open, traced LLM-agent data-and-compute orchestrator (LandslideKR) that does not choose among physical models. The orchestrator's eleven-step pipeline is detailed in §2.1; its role here is enabling infrastructure, not autonomous decision-making. Reference labels are a positive-evidence proxy, Sentinel-2 NDVI-change scars optionally joined with administrative-area NIDR reports, not field-verified ground truth. Per-event label provenance is documented in §2.3 (in the executed runs all three events evaluate against Sentinel-scar-only labels, for distinct reasons).

Running this pipeline on the three events yields a sharp three-way contrast. SHALSTAB shows positive scar/non-scar separation on the typhoon event (Pohang ROC-AUC 0.612, separation +0.198, top-percentile recall 69 %), is rank-inverted on the large monsoon AOI (Yecheon ROC-AUC 0.449, separation -0.070, top-percentile recall 14 %), and is essentially random on the small monsoon AOI (Chuncheon ROC-AUC 0.499, separation +0.006). A topographic predictor (slope alone) outperforms baseline SHALSTAB on both monsoon AOIs (slope-alone ROC-AUC 0.669 on Yecheon; hillslope-masked SHALSTAB 0.550 on Chuncheon). At the observed positive-class rates of 0.12–1.65 % the raw false-alarm rate is structurally pinned near 99 %, so we report precision lift over base rate jointly with recall and kept-fraction. The mechanism for the Yecheon inversion (§3.2) is that SHALSTAB's steady-state upslope-area term inflates probability on low-elevation valley pixels where the hillslope assumption fails, while the actual scars cluster on steep higher-elevation slopes, a confounder that a simpler slope predictor avoids on the large AOI but that is absent on Pohang's hillslope-dominated 600 km$^{2}$ catchment.

The contribution is narrow. We release an open three-event Korean retrospective benchmark of Monte Carlo SHALSTAB with full execution provenance, three-event diagnostic evidence that a single steady-state physical model has divergent skill across Korean rainfall–landslide events, and the LandslideKR orchestrator that makes the benchmark replicable. The three-event divergence motivates an in-pipeline agentic model-selection layer as future work; we do not claim that capability in this release. The executed contribution is the open benchmark and the disclosed re-executable infrastructure.

The remainder of the paper is organized as follows. Section 2 describes the orchestrator, the SHALSTAB Monte Carlo, the planned-versus-executed reference label, and the three events. Section 3 reports per-event metrics, the Yecheon-inversion mechanism, four post-hoc scoring comparisons, and the precision-lift FAR-filter results. Section 4 discusses event-typology-dependent applicability and the agentic implications. Section 5 reports executed agent-robustness checks and lists deferred extensions. Sections 6 and 7 enumerate limitations and conclude.


# 2. Methods

## 2.1 LandslideKR as a constructed-resource operating layer

LandslideKR is an LLM-agent operating layer for a deployed scientific-resource stack (global EO archives, GPM IMERG, Sentinel-2, Copernicus DSM; national administrative reporting, NIDR via data.go.kr + VWorld geocoding; national geology vector, KIGAM 1:50 000; a Monte Carlo SHALSTAB solver over lithology-conditional bounds). The agent's job on this stack is not to decide the science but to make the stack re-executable, provenance-traced, and failure-tolerant on a per-event basis: it binds heterogeneous endpoints under one schema, writes an append-only AgentTrace record per step (`step`, `tool`, `inputs`, `outputs`, `rationale`), supports a dry-run mode via an outputs flag so that run specifications can be committed before execution, and records non-fatal external-API failures inside the step's `outputs` rather than aborting the run. Concretely this gives the scientist and the reviewer three operating-layer guarantees that a hand-written workflow does not: (i) every reported number can be traced to the step that produced it, (ii) failure modes are disclosed symmetrically per event rather than silently routed around, and (iii) the per-event configuration (bbox, event window, model parameters, seed) can be frozen in a config file before the run, the dry-run vs executed distinction, and the Chuncheon preregistration disclosure in §3.6, are both instances of this pattern.

Within this scope the agent does *not* choose among competing physical models; it runs a single uniformly configured lithology-conditional Monte Carlo SHALSTAB ensemble on every event, so any divergence in model fit reported in §3 is a property of the physical model, not an agent decision. The three-event divergence in §3 motivates, but does not itself implement, an in-pipeline agentic model-selection layer, the scaffolding (typed AgentTrace schema, per-step rationale field, dry-run vs executed split) is where a future selector would plug in, and we discuss this explicitly in §4.3. Post-hoc comparisons to hillslope-masked, slope-only, and slope $\times$ relief scorings (§3.3, §3.5) are offline diagnostic analyses, not in-pipeline agent behavior.

The pipeline has four functional blocks: forcing and label inputs (GPM IMERG V07 rainfall, Sentinel-2 NDVI-change scars, NIDR administrative-area reports), topographic and geologic substrate (Copernicus DSM 30 m slopes and flow accumulation; KIGAM 1:50 000 lithology rasterized to five SHALSTAB classes), the physical model (lithology-conditional Monte Carlo SHALSTAB ensemble, n = 100 realizations per pixel; §2.2), and evaluation (per-pixel probability raster, binary prediction, and confusion-matrix plus ROC-AUC metrics against the Sentinel-scar reference). All operational detail, step-level I/O schema, trace format, runtime fallback choices, per-event artifact inventory, and release-package layout, is in Online Resource 2.

## 2.2 SHALSTAB with Lithology-Conditional Monte Carlo

The physical model is the steady-state slope-stability formulation of Montgomery and Dietrich (1994). For each pixel the model computes a critical steady-state rainfall-to-transmissivity ratio (implementation: the SHALSTAB stability function, Eq. (1), see Code Availability):

$$
\frac{q_{cr}}{T} = \frac{b}{a}\,\sin\theta \left[\, \frac{\rho_s}{\rho_w}\!\left(1 - \frac{\tan\theta}{\tan\phi}\right) + \frac{c}{\rho_w\, g\, z\, \cos^2\theta\, \tan\phi} \,\right] \qquad (1)
$$

where $\theta$ is the local slope, $\phi$ the friction angle, c the cohesion, T the soil transmissivity, z the vertical soil thickness, a the upslope contributing area, b the contour length of the pixel, $\rho_s$ and $\rho_w$ the soil and water densities, and g the gravitational acceleration. The observed forcing ratio is $q/T$ where q is the effective steady-state recharge (converted from GPM IMERG V07 event-cumulative precipitation over the event duration). Instability is declared when $q/T \geq q_{cr}/T$; the model-output stability index is $(q/T)/(q_{cr}/T)$. Pixels with stability $\geq 1$ are unstable under the specified steady-state forcing. The critical forcing ratio is converted into an instability probability by a SINMAP-style bounded Monte Carlo procedure: for each pixel we draw n=100 joint realizations of ($\phi$, c, T, z) from the lithology-conditional bounds in Table 1 ($\phi$, c, z uniform; T log-uniform, i.e., uniform in log-transmissivity) and count the fraction of realizations in which that pixel is unstable. The resulting per-pixel probability is the output written as the per-pixel probability-of-instability raster.

Lithology classes are the five SHALSTAB-relevant Korean rock categories (granite, volcanic, sedimentary, metamorphic, alluvium). The parameter bounds in Table 1 are grounded in Park et al. (2013) and the Korean slope-stability literature. The granite cohesion floor and transmissivity ceiling were adjusted once during this study to reduce a probability-saturation artifact observed in early Pohang runs (the adjustment is annotated inline in [`lithology_params.py`](https://github.com/egpark-knu/landslidekr/blob/main/landslide_kr/models/lithology_params.py)); this single post-hoc relaxation means Table 1 is not a strict preregistration of the parameter box. All other lithology-class bounds, the ensemble size n = 100, and the random seed were fixed before Yecheon or Chuncheon were executed, and the bounds are not retuned on the observed scar sets of any event. The alluvium class carries larger bounds on transmissivity and smaller bounds on cohesion, and the granite class carries the tightest bounds on friction angle.

The Monte Carlo count n=100 was chosen to be consistent across events; §5.3 reports the stochastic repeatability of the point estimates under re-seeding, and §5.4 reports the sensitivity of the event-level ROC-AUC to ($\phi$, c, T) grid moves within the Table 1 bounds.

Throughout this work SHALSTAB is used only as a hillslope-steady-state instability model; no dynamic transient solver (TRIGRS) is invoked, and the agent does not adaptively switch between SHALSTAB and alternatives.


## Table 1. Lithology-class Monte Carlo parameter bounds (literature-grounded)

\nopagebreak

|| Class | Friction angle $\phi$ ($^\circ$) | Cohesion c (Pa) | Transmissivity T (m$^{2}$/s) | Soil depth z (m) | Rationale |
|---|---|---|---|---|---|
| granite | 28 – 38 | 2 000 – 10 000 | 1 $\times 10^{-4}$ – 1 $\times 10^{-3}$ | 0.8 – 2.5 | Park et al. (2013) Pohang-area residual soil; tight $\phi$, high-floor cohesion and transmissivity |
| volcanic | 30 – 40 | 2 000 – 12 000 | 1 $\times 10^{-4}$ – 1 $\times 10^{-3}$ | 0.5 – 2.0 | Weathered volcanic (Jeju, SE Korea ridges) |
| sedimentary | 22 – 34 | 500 – 5 000 | 2 $\times 10^{-5}$ – 2 $\times 10^{-4}$ | 1.0 – 3.0 | Mudstone / sandstone residual |
| metamorphic | 26 – 36 | 1 500 – 8 000 | 3 $\times 10^{-5}$ – 3 $\times 10^{-4}$ | 0.8 – 2.5 | Gneiss / schist residual |
| alluvium | 25 – 35 | 500 – 3 000 | 5 $\times 10^{-4}$ – 5 $\times 10^{-3}$ | 1.5 – 5.0 | Colluvium / fluvial, stable on low slopes |
| default (fallback) | 28 – 36 | 1 000 – 6 000 | 5 $\times 10^{-5}$ – 5 $\times 10^{-4}$ | 0.8 – 2.5 | Used when lithology layer unavailable |

Soil density is uniform across classes at 1 600 – 2 000 kg m$^{-3}$. Transmissivity is sampled in log-space; all other parameters are sampled uniformly within the stated bounds. n = 100 realizations per pixel.

## 2.3 Reference Label Construction

The reference label is a positive-evidence proxy, not field-verified ground truth. We avoid the term "ground truth" throughout. Two evidence sources contribute. NIDR administrative-area reports from the data.go.kr service ID 15074816 return annual records at administrative-area (sigungu/eup/myeon) resolution, with reported damage area in hectares but no point or polygon geometry and no event-day date field, the date column is an annual placeholder (YYYY-01-01). Addresses are resolved to administrative centroids via the VWorld geocoder where a service key is available, and each centroid is buffered to 30 m to match the DEM cell size. Sentinel-2 NDVI-change scars are computed from a 90-day pre-event composite and a 60-day post-event composite, masked where dNDVI > 0.15, post-NDVI < 0.35, and slope > 10$^\circ$ (similar in spirit to the Sentinel-2 + Google Earth Engine semi-automatic mapping of Notti et al., 2023); the slope gate removes cropland and water.

The §3.1 baseline label is event-window Sentinel-scar only in all three reported runs. The NIDR-augmented ablation (§5.6) is a label-source sensitivity check: because NIDR is annual, the NIDR label layer represents administrative-area annual landslide presence within the AOI rather than event-window-confirmed landslides, and any ROC-AUC recovery under NIDR augmentation must be read with that caveat.


Table 2 summarizes the planned versus executed label source per event.

## Table 2. Label provenance (executed vs planned)

\nopagebreak

|| Event | Planned label | Executed label | Reason for gap |
|---|---|---|---|
| Pohang 2022 | NIDR 30 m point buffer $\cup$ Sentinel-2 scar | Sentinel-2 scar (baseline) | NIDR records do not fall within the published bbox; §5.6 ablation excludes Pohang |
| Yecheon 2023 | NIDR 30 m point buffer $\cup$ Sentinel-2 scar | Sentinel-2 scar (baseline) | NIDR-augmented label-layer ablation in §5.6 (273 in-bbox points) |
| Chuncheon 2020 | NIDR 30 m point buffer $\cup$ Sentinel-2 scar | Sentinel-2 scar only | NIDR records joined in the §5.6 (Axis 6) NIDR-augmented ablation; the §3.1 Table 4 baseline retains the Sentinel-only label for cross-event comparability |

## 2.4 Events

Three events comprise the benchmark. Each is in the NIDR record and has cloud-free Sentinel-2 availability in the 60-day post window (with a 90-day pre window for the matched composite).

Table 3 summarizes the three events' rainfall typology, AOI size, terrain, and executed reference-label source.

## Table 3. Three-event configuration: rainfall typology, AOI size, terrain, and label provenance.

\nopagebreak

|| Event | Type | Date | AOI | Rainfall peak | Lithology mix | Reported-run label | Status |
|---|---|---|---|---|---|---|---|
| Pohang 2022 (Typhoon Hinnamnor) | Typhoon | 5–7 Sep 2022 (IMERG 2-day window) | ~600 km$^{2}$ | 412 mm / 24 h reported at Pohang station; 96 mm peak pixel, 91 mm AOI-mean over IMERG window | granite-dominated | Sentinel-2 scar (NIDR town centroids fall east of bbox; §5.6) | Executed |
| Yecheon 2023 (Monsoon) | Monsoon | 13–18 Jul 2023 (IMERG 5-day window) | ~9 000 km$^{2}$ | ~580 mm cumulative reported at Yecheon station; 216 mm peak pixel, 188 mm AOI-mean over IMERG window | sedimentary + metamorphic + alluvium | Sentinel-2 scar (baseline) + 273 NIDR points in §5.6 ablation | Executed |
| Chuncheon 2020 (Monsoon) | Monsoon | 1–8 Aug 2020 (IMERG 7-day window) | ~850 km$^{2}$ | 461 mm peak pixel, 403 mm AOI-mean over IMERG window | granite + metamorphic (KIGAM 1:50 000) | Sentinel-2 scar (baseline) + 18 NIDR points in §5.6 ablation | Executed |

Pohang and Yecheon are the two anchor events, chosen to be structurally distinct on rainfall typology, AOI size, and terrain mix. Chuncheon 2020 is the third point designed to separate rainfall typology from AOI size and terrain: it agrees with Yecheon on typology (monsoon) but with Pohang on scale and terrain (small mountainous). The Chuncheon design is not a true preregistration: as disclosed in the released case configuration (Online Resource 1), the bounding box, event window, model parameters, ensemble seed, and the qualitative predictions A/B/C (Pohang-like / Yecheon-like / intermediate) were committed to disk before execution, but the specific numeric cutoffs used to map the executed result onto those three classes were added after the executed numbers were observed. We therefore treat the Chuncheon outcome as a retrospective diagnostic that is consistent with the working hypothesis, not as a preregistered test. Three events is sufficient to disambiguate one binary contrast, not to establish a regime law, the working-hypothesis status of the typology mapping is preserved throughout §§4–7.

# 3. Results

## 3.1 Baseline SHALSTAB Monte Carlo ensemble across three events

Baseline labels are event-window Sentinel-scar only for all three events. An NIDR-augmented label-source sensitivity check is reported separately in §5.6. Numeric backing (per-event AgentTrace `evaluate` steps, Pohang run log, and the JSON/CSV analysis artifacts that feed the tables and figures in this section) is in Online Resource 1; the pipeline-step schema that produces these numbers is in Online Resource 2; the offline raster recomputation scripts themselves are distributed with the code repository (see Code availability).

Table 4 reports the confusion-matrix metrics, ROC-AUC, and probability-separability statistics per event.

## Table 4. Baseline confusion-matrix metrics, ROC-AUC, and probability-separability statistics for the per-event SHALSTAB Monte Carlo ensemble (n=100 realizations per pixel).

\nopagebreak

|| Metric | Pohang 2022 | Yecheon 2023 | Chuncheon 2020 |
|---|---|---|---|
| N valid pixels | 912 384 | 11 113 520 | 1 259 904 |
| Positives (scar) | 1 099 (0.120 %) | 183 507 (1.651 %) | 15 571 (1.236 %) |
| POD (recall) | 0.9145 | 0.4838 | 0.7152 |
| FAR (raw) | 0.9984 | 0.9855 | 0.9879 |
| CSI | 0.0016 | 0.0143 | 0.0121 |
| F1 | 0.0032 | 0.0281 | 0.0239 |
| Precision | 0.0016 | 0.0145 | 0.0121 |
| ROC-AUC | 0.6118 | 0.449 | 0.4992 |
| Scar mean prob | 0.887 | 0.464 | 0.685 |
| Non-scar mean prob | 0.688 | 0.534 | 0.679 |
| Separation | +0.198 | -0.070 | +0.006 |
| Top-1 % recall | 0.692 | 0.144 | 0.290 |

Pohang shows positive discrimination (ROC-AUC 0.612, separation +0.198, top-1 % recall 69 %). Yecheon shows rank inversion (ROC-AUC 0.449, separation -0.070, top-1 % recall 14 %). Chuncheon shows essentially random discrimination (ROC-AUC 0.499, separation +0.006, top-1 % recall 29 %). The POD differences between events are not directly comparable because the binary prediction threshold is a fixed p $\geq 0.5$ and the pre-positive rates differ by an order of magnitude; we use POD as a consistency check rather than a ranking metric and rely on ROC-AUC and separation for ranking.

## 3.2 Root-cause analysis of the Yecheon rank inversion

We diagnose the negative Yecheon separation by stratifying the AOI into ten equal-count elevation deciles and reporting the mean SHALSTAB Monte Carlo probability alongside the observed Sentinel-2 scar rate per decile (Fig. 3a–c, top row).

Scar-population statistics make the inversion concrete: scars cluster at higher elevation (mean 455 m, median 343 m) than non-scars (mean 280 m, median 240 m), the model's mean SHALSTAB probability decreases monotonically with elevation (from 0.794 below 89 m to 0.346 above 538 m), and the observed scar rate increases monotonically with elevation (from 0.2 % below 89 m to 4.9 % above 538 m).

The model and the observations therefore sort the Yecheon AOI in opposite directions by elevation. A consistent working hypothesis for this pattern, which we offer as a mechanism consistent with the data but not as a directly demonstrated cause, is that the upslope-area term in SHALSTAB's $q_{cr}/T$ inflates probability on low-elevation valley pixels because the steady-state hillslope assumption is weakly satisfied there, while the actual Sentinel-scar layer carries landslide-labelled pixels clustered on steep higher-elevation slopes plus a non-landslide floodplain component at low elevation. Under this working hypothesis a predictor that does not carry the upslope-area term (raw slope, §3.3) would be expected to beat the physical model on a large mixed-terrain monsoon AOI, which is what is observed. Discriminating this mechanism from alternative label-noise or rainfall-distribution explanations is not possible with three events; the Axis 6 label-layer ablation (§5.6) provides indirect support (NIDR-only ROC-AUC on Yecheon recovers to 0.608) but does not isolate the upslope-area mechanism.

We do not repeat this diagnosis for Pohang (where the ranking is positive) or Chuncheon (where the ranking is essentially random) in the main text; the stratified figures for those events are in Fig. 3a and 3c respectively for reader inspection (Fig. 3 top-row panel order: Pohang / Yecheon / Chuncheon).

## 3.3 Post-hoc refinement with alternative scorings

Three alternative scorings are computed on the same DEM and evaluated against the same Sentinel-2 scar reference label as §3.1: hillslope-masked SHALSTAB (slope > 10$^\circ$ intersected with local relief > 30 m in a 33-pixel window), slope alone (Horn slope normalized to [0, 1]), and slope $\times$ relief (slope score multiplied by relief normalized). All four scorings are evaluated with the same scikit-learn ROC-AUC function on the same set of valid pixels per event.

## Table 5. Post-hoc refinement comparison: ROC-AUC of baseline SHALSTAB MC versus three alternative scoring methods (hillslope-masked, slope alone, slope $\times$ relief) per event.

\nopagebreak

|| Method | Pohang 2022 | Yecheon 2023 | Chuncheon 2020 |
|---|---|---|---|
| Baseline SHALSTAB MC | 0.612 | 0.449 | 0.499 |
| Hillslope-masked SHALSTAB | 0.520 | 0.593 | 0.550 |
| Slope alone | 0.506 | 0.669 | 0.547 |
| Slope $\times$ relief | 0.527 | 0.641 | 0.536 |

The ranking is event-type dependent. On the typhoon event Pohang, the baseline SHALSTAB leads every alternative (Table 5 column 1). On the large monsoon AOI Yecheon, every alternative beats baseline SHALSTAB and slope alone reaches the highest ROC-AUC of the four scorings tested across all events (Table 5 column 2). On the small monsoon AOI Chuncheon, all three alternatives improve on the random baseline (Table 5 column 3, gains +0.037 to +0.051), with hillslope-masked SHALSTAB the best alternative tested. The Chuncheon improvements are smaller in absolute terms than the Yecheon improvements, but in the same direction, consistent with the monsoon-side pattern at smaller AOI scale.


## 3.4 Event-wise maps and probability separability histograms

Figures 1 and 2 show the three-panel per-event summary (probability raster, binary prediction with Sentinel-2 scars dilated 2 px for visibility, probability separability histogram) for Pohang 2022 and Yecheon 2023. The corresponding Chuncheon 2020 panel is not included in the main text; the equivalent Chuncheon raster artifacts are released in the code repository for reader inspection (see Code availability), and the matching numeric metrics are in Online Resource 1. All panels are in lat/lon (EPSG:4326) with legends for predicted-unstable (grey), predicted-stable (white), and Sentinel-2 scar (firebrick). Histograms show the scar and non-scar probability distributions overlaid with the mean-separation value annotated.

![](/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/figures/fig1_pohang_2022.png){#fig:1 width=95%}

**Fig. 1.** Pohang 2022 (Typhoon Hinnamnor): (a) SHALSTAB Monte Carlo probability raster, (b) binary prediction (p $\geq 0.5$) with Sentinel-2 scars dilated 2 px for visibility, (c) probability separability histogram (scar vs non-scar). ROC-AUC 0.612, scar/non-scar mean-probability separation +0.198.

![](/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/figures/fig2_yecheon_2023.png){#fig:2 width=95%}

**Fig. 2.** Yecheon 2023 (central-Korea monsoon): same three-panel layout as Fig. 1. ROC-AUC 0.449 (rank-inverted); scar/non-scar mean-probability separation -0.070; top-1 % recall 14 %. The rank inversion is visible as the overlap between scar and non-scar histograms with the scar distribution shifted lower.

Figure 3 is the three-event contrast composite: panels (a–c) report mean SHALSTAB probability and Sentinel-2 scar rate across elevation deciles for each event; panels (d–f) report ROC curves for the four scoring methods per event (baseline, hillslope-masked, slope alone, slope $\times$ relief). The rank inversion on Yecheon and the near-diagonal ROC on Chuncheon are both visible as visual signatures of the underlying numerical findings.

![](/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/figures/fig3_event_contrast.png){#fig:3 width=98%}

**Fig. 3.** Three-event contrast composite. Top row (a–c): mean SHALSTAB Monte Carlo probability (blue) and observed Sentinel-2 scar rate (orange) across ten equal-count elevation deciles, per event (Pohang / Yecheon / Chuncheon). Bottom row (d–f): ROC curves for the four scoring methods (baseline SHALSTAB MC, hillslope-masked SHALSTAB, slope alone, slope $\times$ relief), per event.

## 3.5 False-alarm reduction via post-hoc filters

Raw false-alarm rate (FAR) is structurally pinned near 99 % at these positive-class rates (0.12 %–1.65 %) because any filter that keeps more than 2 % of pixels as predicted-unstable will have false-positive pixels dominating the predicted-positive denominator. FAR therefore varies trivially across all filter configurations we tested (Pohang 0.998$\to0$.999; Yecheon 0.977$\to0$.990; Chuncheon 0.986$\to0$.988). Reporting raw FAR as the FAR-reduction axis gives a false impression of stasis. The operationally meaningful axis at this class imbalance is precision lift over base rate (precision divided by base rate), reported jointly with POD and kept-fraction following the Recall/IoU trade-off reporting pattern of Park (WildfireKR, IEEE Access 2026).

We evaluate nine filter configurations per event:

- F0 baseline (p $\geq 0.5$); F1 hillslope mask; F2/F3/F4 probability top-10/5/1 % quantile gates; F5/F6 compound hillslope $\cap$ top-quantile; F7 slope > 20$^\circ$ gate; F8 compound hillslope $\cap$ slope > 20$^\circ$ $\cap$ p > 0.9.

Headline precision-lift results (Table 6; full numbers in the FAR-filter results (Online Resource 1)):

| Filter | Pohang lift | Pohang POD | Yecheon lift | Yecheon POD | Chuncheon lift | Chuncheon POD |
|---|---|---|---|---|---|---|
| F0 baseline | 1.31$\times$ | 0.914 | 0.88$\times$ (sub-random) | 0.484 | 0.98$\times$ (random) | 0.715 |
| F1 hillslope | 1.44$\times$ | 0.208 | 1.28$\times$ | 0.417 | 1.08$\times$ | 0.581 |
| F7 slope > 20$^\circ$ | 1.00$\times$ | 0.049 | 1.42$\times$ | 0.268 | 1.11$\times$ | 0.426 |
| F5/F6 F1 $\cap$ top-q | 1.56$\times$ | 0.065 | 1.16$\times$ | 0.097 | 1.09$\times$ | 0.180 |
| F8 compound | 0.75$\times$ (over-filtered) | 0.023 | 1.36$\times$ | 0.122 | 1.06$\times$ | 0.195 |

Two additional observations hold across all three events:

1. Probability quantile gating is degenerate. The SHALSTAB Monte Carlo probability distribution is bimodal (peaks at p = 0 and p = 1); more than 10 % of pixels saturate at p = 1.0 per event, so the top-10 %, top-5 %, and top-1 % quantile thresholds collapse to the same p = 1.0 tier and produce identical metrics. Post-hoc isotonic calibration (§5.8, executed) is a within-sample diagnostic (fit and scored on the same per-event Sentinel labels) with material within-sample ROC uplift on the monsoon events but no effect on the upper-tail degeneracy.
2. On both monsoon events, slope > 20$^\circ$ as a standalone gate gives the best or second-best single-knob lift. On Yecheon (large mixed-terrain, 9 000 km$^{2}$) F7 delivers 1.42$\times$ at POD 0.268; on Chuncheon (small mountainous, 850 km$^{2}$) F7 delivers 1.11$\times$ at POD 0.426. On the typhoon event (Pohang, small hillslope-dominated) F7 lift collapses to 1.00$\times$ (pure random) because the hillslope-dominated terrain has already been effectively filtered by the baseline prediction. The F7 pattern across the three events mirrors the ROC-level finding that slope-alone beats SHALSTAB on the monsoon-side AOIs but not on the typhoon-side AOI.

Standard precision-recall view (augmenting, not replacing, precision lift). We additionally compute Average Precision (AP) using scikit-learn's `average_precision_score` function for each event (the PR-AUC summary is in Online Resource 1; the precision-recall curves themselves are regenerable from the code repository):

| Event | Base rate | AP (sklearn) | AP / base rate |
|---|---|---|---|
| Pohang 2022 | 0.1205 % | 0.0016 | 1.29$\times$ (weak positive discrimination) |
| Yecheon 2023 | 1.6512 % | 0.0139 | 0.84$\times$ (sub-random, consistent with rank inversion) |
| Chuncheon 2020 | 1.2359 % | 0.0121 | 0.98$\times$ (random, consistent with separation +0.006) |

AP and precision-lift give the same qualitative reading per event, Pohang above base, Yecheon below base, Chuncheon at base, confirming that the precision-lift pivot is not metric-shopping.

Figure 4 shows the precision-lift landscape across the nine filter configurations per event; bars above the dashed 1$\times$ line indicate above-base-rate precision.

![](/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/figures/fig6_precision_lift.png){#fig:4 width=95%}

**Fig. 4.** Precision-lift over base rate across the nine post-hoc filters (F0–F8) per event. Dashed horizontal line at 1$\times$ marks parity with the event-specific base rate; bars above 1$\times$ indicate above-base-rate precision. Kept-fraction (the proportion of AOI pixels passing the filter) is overlaid for each bar to flag filters whose lift gains are offset by heavy recall loss. On both monsoon events F7 (slope > 20$^\circ$) gives the highest or near-highest single-knob lift (Yecheon 1.42$\times$, Chuncheon 1.11$\times$), narrowly edging Chuncheon F1 (hillslope mask) at 1.08$\times$; on the typhoon event (Pohang) F7 collapses to 1.00$\times$ because the hillslope-dominated AOI is already effectively filtered at baseline.


## Table 6. FAR-filter precision-lift (source: the FAR-filter results (Online Resource 1))

Interpretation: At these positive-class rates (0.12 – 1.65 %), raw FAR is structurally pinned near 99 %; we report precision lift over base rate jointly with POD and kept-fraction. Per-event filter rows are split into Table 6a (Pohang 2022), Table 6b (Yecheon 2023), and Table 6c (Chuncheon 2020) below.

### Table 6a. Pohang 2022 (base rate 0.1205 %)

\nopagebreak

|| Filter | POD | Precision | Lift | Kept-fraction |
|---|---|---|---|---|
| F0 baseline | 0.914 | 0.00158 | 1.31$\times$ | 69.6 % |
| F1 hillslope | 0.208 | 0.00174 | 1.44$\times$ | 14.4 % |
| F2 prob top-10 % | 0.692 | 0.00156 | 1.30$\times$ | 53.3 % |
| F3 prob top-5 % | 0.692 | 0.00156 | 1.30$\times$ | 53.3 % |
| F4 prob top-1 % | 0.692 | 0.00156 | 1.30$\times$ | 53.3 % |
| F5 F1 $\cap$ top-10 % | 0.065 | 0.00188 | 1.56$\times$ | 4.15 % |
| F6 F1 $\cap$ top-5 % | 0.065 | 0.00188 | 1.56$\times$ | 4.15 % |
| F7 slope > 20$^\circ$ | 0.049 | 0.00120 | 1.00$\times$ | 4.93 % |
| F8 F1 $\cap$ slope > 20$^\circ$ $\cap$ prob > 0.9 | 0.023 | 0.00090 | 0.75$\times$ | 3.04 % |

### Table 6b. Yecheon 2023 (base rate 1.6512 %)

| Filter | POD | Precision | Lift | Kept-fraction |
|---|---|---|---|---|
| F0 baseline | 0.484 | 0.01448 | 0.88$\times$ | 55.2 % |
| F1 hillslope | 0.417 | 0.02115 | 1.28$\times$ | 32.5 % |
| F2 prob top-10 % | 0.144 | 0.00968 | 0.59$\times$ | 24.5 % |
| F3 prob top-5 % | 0.144 | 0.00968 | 0.59$\times$ | 24.5 % |
| F4 prob top-1 % | 0.144 | 0.00968 | 0.59$\times$ | 24.5 % |
| F5 F1 $\cap$ top-10 % | 0.097 | 0.01913 | 1.16$\times$ | 8.37 % |
| F6 F1 $\cap$ top-5 % | 0.097 | 0.01913 | 1.16$\times$ | 8.37 % |
| F7 slope > 20$^\circ$ | 0.268 | 0.02339 | 1.42$\times$ | 18.9 % |
| F8 F1 $\cap$ slope > 20$^\circ$ $\cap$ prob > 0.9 | 0.122 | 0.02246 | 1.36$\times$ | 8.95 % |

### Table 6c. Chuncheon 2020 (base rate 1.2359 %)

| Filter | POD | Precision | Lift | Kept-fraction |
|---|---|---|---|---|
| F0 baseline | 0.715 | 0.01207 | 0.98$\times$ | 72.82 % |
| F1 hillslope | 0.581 | 0.01338 | 1.08$\times$ | 53.66 % |
| F2 prob top-10 % | 0.290 | 0.01153 | 0.93$\times$ | 31.20 % |
| F3 prob top-5 % | 0.290 | 0.01153 | 0.93$\times$ | 31.20 % |
| F4 prob top-1 % | 0.290 | 0.01153 | 0.93$\times$ | 31.20 % |
| F5 F1 $\cap$ top-10 % | 0.180 | 0.01346 | 1.09$\times$ | 16.61 % |
| F6 F1 $\cap$ top-5 % | 0.180 | 0.01346 | 1.09$\times$ | 16.61 % |
| F7 slope > 20$^\circ$ | 0.426 | 0.01371 | 1.11$\times$ | 38.44 % |
| F8 F1 $\cap$ slope > 20$^\circ$ $\cap$ prob > 0.9 | 0.195 | 0.01307 | 1.06$\times$ | 18.39 % |

Note: F2 / F3 / F4 are identical per event because the SHALSTAB MC probability distribution is bimodal (peaks at p = 0 and p = 1); the top-1 / 5 / 10 % quantile thresholds all collapse to the p = 1.0 tier. This is reported as a calibration limitation in §5.8.

## 3.6 Three-event contrast and the working hypothesis

We summarize the three-event pattern as a working hypothesis, not a regime law. Across this benchmark, rainfall typology appears more explanatory than AOI size or terrain mix for SHALSTAB skill: SHALSTAB has meaningful discrimination on Pohang (typhoon, 600 km$^{2}$, hillslope-dominated; ROC-AUC 0.612, separation +0.198, AP / base 1.29$\times$), is rank-inverted on Yecheon (monsoon, 9 000 km$^{2}$, mixed-terrain; ROC-AUC 0.449, separation -0.070, AP / base 0.84$\times$), and is at random on Chuncheon (monsoon, 850 km$^{2}$, small mountainous; ROC-AUC 0.499, separation +0.006, AP / base 0.98$\times$).

The Chuncheon outcome is the key test. Chuncheon agrees with Yecheon on rainfall typology (monsoon) but with Pohang on AOI size and terrain (small mountainous). If AOI size and terrain were the dominant signal, Chuncheon would have patterned like Pohang; instead it patterned closer to Yecheon. We treat this as a working hypothesis pending additional independent events and a retrospective diagnostic rather than a confirmatory test, and we retain the released case configuration as documentation of the prediction classes used. The §5.6 label-layer ablation (executed) provides a label-sensitivity check within the monsoon subset only: under NIDR-augmented labels Yecheon and Chuncheon ROC-AUCs both recover (to 0.608 and 0.635 respectively; see §5.6 for small-N caveats). The typhoon event is excluded from the ablation (no NIDR records in the published Pohang bbox), so Axis 6 demonstrates that the Sentinel-only monsoon-side rank inversion and near-random result are partly label-driven; it does not test whether the typhoon-vs-monsoon contrast itself persists under NIDR labels.

# 4. Discussion

Primary finding (baseline, Sentinel-event-window labels). SHALSTAB is a steady-state hillslope-hydrology model [Montgomery and Dietrich, 1994]; its central assumption is most defensible for short-duration high-intensity rainfall on hillslope-dominated topography. The typhoon event (Pohang 2022, ~600 km$^{2}$ hillslope-dominated AOI, ~412 mm over 24 hours) is where the assumption is least violated, and baseline SHALSTAB discriminates scars from non-scars there (ROC-AUC 0.612, separation +0.198, top-1 % recall 69 %). Both monsoon events under event-window Sentinel-only labels sit at or below random (Yecheon 0.449 rank-inverted; Chuncheon 0.499 near-random). Against the Sentinel-event-window reference the three-event pattern is therefore that rainfall typology is the most consistent single predictor of SHALSTAB skill across this benchmark: typhoon $\to$ discriminative, monsoon $\to$ not.

Auxiliary layer 1, AOI composition interacts with typology. On the large mixed-terrain monsoon AOI (Yecheon, 9 000 km$^{2}$, extensive Nakdong-tributary floodplains) the steady-state assumption breaks along two axes simultaneously: the integration scale of $a/b$ includes floodplain pixels that are not hillslopes (so the upslope-area term behaves as a confounder rather than a hillslope-hydrology signal), and the multi-day rainfall distribution is not summarized by one steady-state recharge. The §3.2 elevation-decile stratification makes the $a/b$ confounder visible: the model's mean probability decreases with elevation while the observed scar rate increases. This supports the typology finding but is not a separate claim, it describes how typology plus AOI composition interact on the largest AOI. The 850 km$^{2}$ small-mountainous Chuncheon AOI lacks this floodplain confound, so AOI composition is not a sufficient mechanism by itself; Chuncheon still patterns closer to Yecheon than to Pohang under the Sentinel label, which is what led us to prefer typology over AOI size as the primary explanatory axis.

Auxiliary layer 2, label-source sensitivity partially recovers monsoon skill. The §5.6 NIDR-augmented label-layer ablation replaces the event-window Sentinel scar raster with the annual administrative-area NIDR footprint (§2.3 disclosure: NIDR records are year-level, not event-day) and finds that SHALSTAB ROC-AUC recovers substantially on both monsoon events (Yecheon 0.449 $\to 0.608$; Chuncheon 0.499 $\to 0.635$), while Pohang is excluded (no NIDR records fall within the published Pohang bounding box). Because the NIDR layer is annual rather than event-window-specific, this is a label-source sensitivity check rather than an event-window validation, it does not falsify the Sentinel-based baseline but shows that part of the monsoon-side rank inversion and near-random result is label-driven (Sentinel-specific floodplain/agricultural/cloud-shadow false positives) rather than a pure model failure. We therefore keep the typology claim at working-hypothesis strength and explicitly avoid stronger causal language: the Sentinel-event-window three-event pattern is what the baseline supports, and the NIDR ablation indicates that the magnitude of the monsoon deficit under Sentinel labels overstates the monsoon deficit that would be seen under human-reported labels.

Status of the Chuncheon contrast. Chuncheon 2020 was designed to disambiguate rainfall typology from AOI size and terrain (small-mountainous AOI like Pohang, monsoon forcing like Yecheon). It patterned closer to the Yecheon side under Sentinel labels. As disclosed in the released case configuration (Online Resource 1), the qualitative predictions were pre-committed but the numeric cutoffs mapping the executed result onto those predictions were frozen after execution, so the Chuncheon contrast is retrospective-diagnostic rather than a preregistered confirmatory test.

## 4.2 Why a simpler slope-based ranking outperforms SHALSTAB on the monsoon events

On Yecheon, the slope-alone ROC-AUC (0.669) beats every SHALSTAB variant tested (§3.3 Table 5). The precision-lift table (§3.5 Table 6) shows the same pattern at the pixel-level operating regime: slope > 20$^\circ$ is the best single-knob lift (1.42$\times$) on Yecheon, and F7 lift on Chuncheon (1.11$\times$) is also the highest single-knob lift among the nine filters for that event. On Pohang the F7 gate collapses to lift 1.00$\times$ because the hillslope-dominated AOI is already effectively filtered at baseline.

The mechanism is mechanical, not mysterious. SHALSTAB's $q_{cr}/T$ inversely depends on $(a/b)$; at the large AOI scale where $a/b$ includes floodplain pixels, a high $a/b$ no longer indicates hydrologic concentration onto a potentially unstable hillslope, it indicates that the pixel is a low-elevation drainage point. The model's own output penalizes these pixels' stability ($q_{cr}/T$ low $\to$ stability low $\to$ classification as unstable), which is the opposite of what the scar distribution requires. A predictor that ignores upslope-area entirely, raw slope, or a slope $\times$ relief product, cannot be confounded by this artifact because the product of slope and relief does not integrate drainage.

We read this as a diagnostic result about the applicability window of SHALSTAB, not as a recommendation to retire physical models. A transient physical solver (TRIGRS, for example) may track the monsoon forcing better than a steady-state solver and is a natural direction for a follow-on paper; the present benchmark does not evaluate TRIGRS.

## 4.3 Agentic implications, scoped to the three-event benchmark

The orchestrator in LandslideKR is a data-and-compute agent: it assembles the inputs (rainfall, DEM, geology, scars, reports) and runs the SHALSTAB ensemble, leaving an AgentTrace record per step. It does not choose among competing physical models at run time. Any divergence in model fit between events reported in §3 is therefore a property of the physical model, not an agent-level decision. The three-event contrast is evidence that a single-model commitment is brittle across Korean rainfall typologies.

On the three-event benchmark, we stop at "evidence motivating an agentic model-selection layer" and refuse to report a decision-rule as a regime law. We offer the following candidate decision rules as a working hypothesis for future validation, not as a demonstrated agent capability in this release. Typhoon forcing on a hillslope-dominated AOI suggests the baseline SHALSTAB ensemble without topographic gating; monsoon forcing on a large mixed-terrain AOI suggests hillslope-masked SHALSTAB or a slope-only ranking; monsoon forcing on a small mountainous AOI is weak under all of the above, plausibly under-constrained with a single steady-state model and calling for a transient solver. Embedding these candidate rules into an in-pipeline model selector is future work. The agentic decision is not yet in the pipeline; it is explicitly a designed follow-on, and §2.1 and §4.3 read together make this scope explicit. The three-event retrospective benchmark surfaces the evidence that the decision is worth making, and the released AgentTrace record format is the place a future selector would read.

## 4.4 Label-source sensitivity (bridge to §5.6)

Sentinel-2 NDVI-change carries floodplain, agricultural, and cloud-shadow false positives that the slope > 10$^\circ$ gate reduces but does not eliminate, and the expected magnitude differs by AOI composition (Yecheon most exposed, Chuncheon intermediate, Pohang least). The §5.6 Axis-6 ablation executes this check and is the §4.1-auxiliary layer-2 finding: label-source sensitivity partly attenuates the monsoon deficit but does not replace the Sentinel-event-window baseline.


## 4.5 Why an agent, the operating-layer claim

Against the obvious question of why this work is called an agent paper rather than a Snakemake pipeline with a logging decorator: the operating-layer framing introduced in §2.1 is the non-trivial addition. A conventional workflow engine records what happened; the LandslideKR operating layer adds (i) a typed AgentTrace with per-step `rationale` field that captures non-fatal fallback paths, (ii) a dry-run / executed separation that lets per-event run specifications be committed before execution (the backbone of the §3.6 Chuncheon preregistration discipline), and (iii) symmetric per-event failure-mode disclosure (first-attempt NIDR failures, topography-backend fallbacks, geocoding choices). The release is a set of per-event configs plus a traced runtime that any team with the released credentials can re-execute against the same EO / reporting / geology / solver stack; a natural-language configuration front end (§5.1 Axis 1) and an in-pipeline model-selection layer are scaffolded on the AgentTrace schema but explicitly deferred to follow-on work rather than claimed here. The three-event diagnostic finding is a scientific result obtained on top of that operating layer; the operating layer is the infrastructure contribution.

# 5. Agent Robustness Evaluation

![](/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/figures/fig5_axes_overview.png){#fig:5 width=85%}

**Fig. 5.** Seven-axis robustness evaluation framework. Hub-and-spoke conceptual diagram of the seven axes that probe different sources of variability in physical-model prediction quality. Color code reflects execution status in this release: green = executed (Axes 3, 4, 6), peach = partially executed (Axis 2), gray = deferred to follow-on work (Axes 1, 5, 7). Axes 3, 4, and 6 are reported in §5.3, §5.4, and §5.6 respectively; deferred axes are described in Online Resource 3.

Figure 5 visualises the seven axes, their dependencies, and which were executed in this release.

Section structure mirrors the design in the released robustness plan (Online Resource 3). We clearly mark which axes are executed in this release and which are deferred to follow-on work. The plan itself is not a released result package; the contents of this section are.

## 5.1 LLM-backend robustness (Axis 1, deferred)

Deferred to follow-on work. Design (four commercial backends $\times$ three scenario-specificity levels $\times$ five repetitions on the schema-constrained configuration interface; open-source LLMs out of scope per the WildfireKR Axis 1 precedent) is in the released robustness plan (Online Resource 3). The physical pipeline is deterministic given identical configs, so this axis does not change downstream §3 metrics.

## 5.2 Adversarial input handling (Axis 2, partially executed)

Partially executed. The orchestrator handles non-fatal external-API failures by reverting the affected step to a logged non-fatal record and continuing to the consensus-label step; this fallback path is exercised by the released AgentTrace records and is part of the agent design rather than a one-off recovery. The full 10-case fail-fast suite (spanning bbox-validity, event-window typing, ensemble-size bounds, missing service credentials, missing DEM tiles, absent lithology fields, and malformed date / key strings) is deferred to follow-on work; we do not report a partial subset as "executed".

## 5.3 Stochastic repeatability (Axis 3, executed)

Status: executed. The SHALSTAB Monte Carlo ensemble was re-run under five RNG seeds per event (15 runs total). The repeatability script uses the default-lithology fallback for a reproducible parameter-space check, which shifts absolute ROC-AUC from §3.1 by a few percentage points but preserves the across-seed CV% that Axis 3 targets.

| Event | ROC-AUC mean $\pm$ std | CV% | Separation mean $\pm$ std | CV% | POD CV% | AP CV% |
|---|---|---|---|---|---|---|
| Pohang 2022 | 0.5328 $\pm 0.0029$ | 0.54 | +0.0461 $\pm 0.0017$ | 3.67 | 0.93 | 0.96 |
| Yecheon 2023 | 0.4304 $\pm 0.0024$ | 0.55 | -0.0754 $\pm 0.0033$ | 4.36 | 3.43 | 0.42 |
| Chuncheon 2020 | 0.4683 $\pm 0.0009$ | 0.20 | -0.0277 $\pm 0.0014$ | 4.91 | 2.19 | 0.27 |

ROC-AUC CV is below 0.6 % on all three events; AP CV is below 1.0 %; POD CV is below 4 %; separation CV is below 5 %. Axis 3 therefore establishes that the per-event point estimates under the default-lithology fallback are seed-stable to within a few tenths of a percent on ROC-AUC, it is a repeatability check on the stochastic Monte Carlo sampler, not a cross-check of the §3.1 per-pixel-lithology separations. In particular, Chuncheon separation under the default-lithology fallback is negative across all five Axis 3 seeds (-0.028 $\pm 0.001$), whereas the §3.1 baseline separation under the per-pixel lithology array is positive (+0.006); the Axis 3 run does not attempt to reproduce the per-pixel-lithology §3.1 numbers, and the sign difference reflects the lithology-array change, not ensemble noise. The follow-on n = 20 expansion is straightforward (the script accepts a seed list parameter) but gives diminishing returns on already-tight CV%.

## 5.4 Parameter sensitivity (Axis 4, executed)

Status: executed. We swept the SHALSTAB parameter triple ($\phi$, c, T) at the eight corner combinations (low/high on each axis) of the Table 1 default-lithology bounds (see §2.2 for the provenance and the single granite-bound adjustment), holding soil thickness and density at midpoints and all other inputs (DEM, topo, rainfall, scar reference) constant. Twenty-four deterministic SHALSTAB runs (3 events $\times 8$ corners) were evaluated against the same Sentinel-scar reference label as §3.1. The headline event-ranking pattern, Pohang ROC-AUC highest among the three events, survives in 6 of the 8 corners (75 %); the two failing corners are both at low friction angle combined with low cohesion (both $\phi_{lo}$ and $c_{lo}$), where Yecheon's ROC briefly exceeds Pohang's. Within each event the across-corner ROC range is small (Pohang 0.441 – 0.485, Yecheon 0.401 – 0.514, Chuncheon 0.458 – 0.479), and Yecheon and Chuncheon stay at or below 0.55 in every corner tested. The headline finding "rainfall typology more explanatory than AOI for SHALSTAB skill" is therefore robust against parameter-corner variation in the ($\phi$, c, T) box, conditional on parameters being above the lower bound on cohesion or friction angle. ROC absolute values differ from §3.1 because Axis 4 uses the single default-lithology fallback rather than the per-pixel lithology array.

## 5.5 Scar-threshold sensitivity (Axis 5, deferred)

Deferred. Design (sweeping the Sentinel-2 scar gate over (dNDVI, post-NDVI cap, slope gate) combinations to rule out a thresholding artifact in the three-event ROC-AUC pattern) is in the released robustness plan (Online Resource 3); the axis is GEE-bound and is released as a scripted design for off-network execution. It does not change the released §3 metrics, which are reported at the §2.3 scar-gate triple.

## 5.6 Label-layer ablation (Axis 6, executed)

Status: executed. The annual NIDR record (§2.3) was geocoded to yield 273, 18, and 0 in-bbox points for Yecheon, Chuncheon, and Pohang respectively. Because NIDR is annual, the rasterized NIDR layer is a full-year footprint: this is a label-source sensitivity check, not an event-window validation. Four variants per event, A (Sentinel-only), B (NIDR-only), C (union), D (intersection), are reported; Pohang has no in-bbox NIDR points and is excluded from variants B–D.

| Event | Variant | n_pos (px) | base rate | ROC-AUC | separation |
|---|---|---|---|---|---|
| Pohang 2022 | A Sentinel-only (= §3.1 baseline) | 1,099 | 0.120 % | 0.6118 | +0.1983 |
| Pohang 2022 | B–D NIDR-augmented |, |, | undefined | undefined (n_in_bbox = 0) |
| Yecheon 2023 | A Sentinel-only | 183,507 | 1.651 % | 0.4490 | -0.0699 |
| Yecheon 2023 | B NIDR-only | 231 | 0.002 % | 0.6077 | +0.1333 |
| Yecheon 2023 | C Sentinel $\cup$ NIDR | 183,735 | 1.653 % | 0.4492 | -0.0696 |
| Yecheon 2023 | D Sentinel $\cap$ NIDR | 3 | 0.000 % | 0.4002 | -0.1827 |
| Chuncheon 2020 | A Sentinel-only | 15,571 | 1.236 % | 0.4992 | +0.0064 |
| Chuncheon 2020 | B NIDR-only | 17 | 0.001 % | 0.6346 | +0.1676 |
| Chuncheon 2020 | C Sentinel $\cup$ NIDR | 15,588 | 1.237 % | 0.4993 | +0.0065 |

Variant-B NIDR-only ROC-AUC exceeds variant-A Sentinel-only on both monsoon events (Yecheon 0.608 vs 0.449; Chuncheon 0.635 vs 0.499). Small-N NIDR positive-pixel counts (231 and 17) and the town-centroid + 30 m buffer geometry make absolute variant-B magnitudes noisy, but the sign and direction indicate that part of the monsoon-side deficit under event-window Sentinel labels is attributable to label-source (floodplain/agricultural/cloud-shadow) false positives rather than to model failure alone. As §4.1 layers, this is an auxiliary finding: the primary baseline comparison remains Sentinel-event-window, and the Chuncheon NIDR-only variant should not be read as a confirmatory positive result for SHALSTAB on small-mountainous monsoon AOIs.

## 5.7 Spatial hold-out (Axis 7, deferred)

Deferred. Design (NE/SW AOI half-splits per event, threshold calibration on one half and evaluation on the other) is in the released robustness plan (Online Resource 3). With n = 3 events this is the strongest weak-cross-validation feasible without new external data, and it does not change the released §3 metrics, which are reported on the full per-event AOI.

## 5.8 Monte Carlo probability bimodality (observation, not an axis)

Status: executed observation. The SHALSTAB MC probability distribution is bimodal (54.5 % / 25.9 % / 32.8 % of valid pixels saturate at p $\approx 1.0$ for Pohang / Yecheon / Chuncheon), which is why the top-1 %, top-5 %, and top-10 % quantile filters in §3.5 collapse to the same p = 1.0 tier. A within-sample isotonic regression of the raw probability against the Sentinel-scar label produces monsoon-side ROC-AUC uplift (Yecheon 0.449 $\to 0.502$; Chuncheon 0.499 $\to 0.538$) that is a tie-handling artifact of collapsing the p $\approx 1$ tie block, not an out-of-sample ranking gain; the upper-tail degeneracy remains, so operational top-decile filtering is limited by ensemble bimodality rather than by calibration skill.

## 5.9 Summary of executed versus deferred axes

| Axis | Status |
|---|---|
| 1 LLM backend | Deferred |
| 2 Adversarial input | Partial, two natural-experiment instances executed; 10-case test suite deferred |
| 3 Stochastic repeatability | Executed, 5 seeds $\times 3$ events; ROC CV $\leq 0.6$ %, AP CV $\leq 1.0$ %, POD CV $\leq 4$ %, separation CV $\leq 5$ % |
| 4 Parameter sensitivity | Executed, 8 corners $\times 3$ events; headline Pohang-highest ranking survives in 6/8 corners |
| 5 Scar-threshold sweep | Deferred |
| 6 Label-layer ablation | Executed, Yecheon 273 NIDR pts $\to$ variant B ROC 0.608 sep +0.133 (vs Sentinel 0.449, -0.070); Chuncheon 18 pts $\to$ variant B ROC 0.635 sep +0.168 (vs Sentinel 0.499, +0.006); Pohang 0 in-bbox (Guryongpo east of bbox) |
| 7 Spatial hold-out | Deferred |
| 8 MC bimodality + isotonic calibration | Executed, p$\approx1$ saturation 54.5 / 25.9 / 32.8 % per event; within-sample isotonic calibration (same-event Sentinel label) produces material ROC-AUC uplift on the two monsoon events (Yecheon +0.053, Chuncheon +0.038) via tie-block collapse, not out-of-sample ranking gain; upper-tail degeneracy unchanged (one distinct calibrated score in the top tier) |

We do not claim a fully executed robustness evaluation in this release. We treat the deferred axes as design commitments for the follow-on paper rather than as omitted evidence; the released robustness plan (Online Resource 3) is the canonical design document and the Axis 6 label-ablation script (Code Availability) is the first executed axis script.

# 6. Limitations

We state the limitations we consider most likely to shape how a reviewer interprets this paper, and we keep the list narrow because longer lists tend to dilute rather than reassure.

The most consequential limitation is that no field-verified ground truth is available. All three events are evaluated against a positive-evidence proxy (event-window Sentinel-2 NDVI-change scars for the §3.1 baseline; annual administrative-area NIDR reports added in the §5.6 ablation only). The §5.6 ablation is a label-source sensitivity check, not an event-window validation: NIDR is annual (§2.3) and Pohang has zero in-bbox NIDR points. Under NIDR labels the monsoon-event ROC-AUCs recover to 0.608 (Yecheon) and 0.635 (Chuncheon), with small-N caveats (231 and 17 NIDR pixels; town-centroid + 30 m buffer geometry). This means the Sentinel-label monsoon deficit partly reflects Sentinel-specific false positives rather than pure model failure; we therefore hold the §4.1 typology claim at working-hypothesis strength and avoid stronger causal language.

Three events are also three events. The Pohang / Yecheon / Chuncheon contrast is sufficient to disambiguate one binary factor, rainfall typology versus AOI size and terrain, and insufficient to establish a regime law for typhoon-versus-monsoon SHALSTAB applicability; the mapping in §4.3 is a working hypothesis for future validation, not a regime claim, and the Chuncheon outcome is retrospective-diagnostic rather than preregistered (qualitative predictions pre-committed, numeric cutoffs added after execution; see the released case configuration). Within this release the agent additionally does not select among physical models: every event is run under one uniformly configured SHALSTAB Monte Carlo ensemble, and the post-hoc comparisons to hillslope-masked, slope-only, and slope $\times$ relief scorings are offline diagnostic analyses rather than in-pipeline agent behavior, with an in-pipeline model-selection layer proposed as future work. The Monte Carlo probability output is also bimodal, 54.5 / 25.9 / 32.8 % of pixels per event saturate at p = 1.0 under the current lithology-conditional bounds and the top-1 %, top-5 %, and top-10 % probability quantile filters collapse to the same p = 1.0 tier (§3.5 Table 6); the executed within-sample isotonic calibration in §5.8 does not break this upper-tail degeneracy (and its ROC-uplift is a within-sample tie-handling artifact, not an out-of-sample generalization claim), so operational top-decile filtering remains limited by the bimodality rather than by calibration skill.

The seven-axis agent-robustness evaluation is not fully executed in this release. Section 5 reports the axes executed to date and clearly marks those deferred; the robustness plan in the released robustness plan (Online Resource 3) is the design document, not a completed evidence package, and readers relying on the robustness argument for submission-readiness decisions should check §5 for the deferred-axis list before assuming an axis is executed. Sentinel-1 SAR is likewise not integrated, the SAR-based label augmentation plan in the SAR-integration plan (Online Resource 4) is future work, not part of the released benchmark, so reviewers expecting SAR-augmented labels will not find them here. Finally, the LLM-backend robustness test (Axis 1) covers commercial APIs only because the Model Context Protocol tool-calling interface used by the orchestrator is not uniformly supported across open-source endpoints (Llama, Mistral, Qwen at comparable tool-calling maturity) as of April 2026; this scope limitation is inherited from the WildfireKR Axis 1 precedent (IEEE Access, 2026).

# 7. Conclusions

We report a three-event Korean retrospective benchmark of a lithology-conditional Monte Carlo SHALSTAB ensemble and an open LLM-agent data-and-compute orchestrator that makes the benchmark reproducible.

A single steady-state physical model has sharply event-type-dependent skill on Korean rainfall–landslide events: SHALSTAB separates scars from non-scars on Typhoon Hinnamnor (Pohang 2022, ROC-AUC 0.612, separation +0.198), is rank-inverted on the 2023 Central Korea Monsoon (Yecheon, ROC-AUC 0.449, separation -0.070), and is essentially random on the 2020 Gangwon Monsoon (Chuncheon, ROC-AUC 0.499, separation +0.006). Across this three-event benchmark rainfall typology appears more explanatory than AOI size or terrain mix for SHALSTAB skill, though the pattern remains a working hypothesis rather than a regime law pending additional independent events. A topographic predictor, slope alone, correspondingly outperforms SHALSTAB on the monsoon-side AOIs: on Yecheon the slope-alone ROC-AUC reaches 0.669, beating every SHALSTAB variant tested, consistent with SHALSTAB's upslope-area term behaving as a confounder on large AOIs containing floodplains. This is diagnostic evidence for the applicability boundary of steady-state hillslope models, not a recommendation to retire them.

At positive-class rates of 0.12–1.65 %, raw false-alarm rate is structurally pinned near 99 % and is not a useful operational axis; reporting precision lift over base rate jointly with recall and kept-fraction surfaces a clean operational finding that the slope > 20$^\circ$ gate gives the best single-knob precision lift on both monsoon events (Yecheon 1.42$\times$, Chuncheon 1.11$\times$) while leaving the typhoon event unchanged, and standard Average Precision reporting (§3.5) gives the same qualitative reading per event.

The LandslideKR orchestrator is released as enabling infrastructure, not as a physicist-surrogate. The eleven-step traced pipeline, GPM IMERG rainfall, Sentinel-2 NDVI-change scar detection, NIDR reports via data.go.kr + VWorld geocoding, Copernicus DSM COG 30 m DEM, pysheds D8 flow accumulation and Horn slopes, KIGAM 1:50 000 lithology, and SINMAP-style bounded Monte Carlo SHALSTAB, is released with per-event artifacts (Pohang: dry-run AgentTrace JSON plus executed run log; Yecheon and Chuncheon: executed AgentTrace JSON records), and explicit per-event label-provenance disclosure in §2.3 and §5.6. The agent does not choose among physical models; its contribution is reproducibility, not physics. The three-event divergence instead motivates an agentic model-selection layer as future work, and we offer candidate decision rules as a working hypothesis (typhoon $\to$ baseline SHALSTAB; monsoon on large mixed-terrain $\to$ hillslope-masked SHALSTAB or slope-only; monsoon on small mountainous $\to$ transient solver) rather than as a demonstrated agent capability, with validation on additional independent events under frozen numeric preregistration as the natural direction for a follow-on paper.

Code, per-event traces and logs (Pohang: dry-run JSON + executed log; Yecheon and Chuncheon: executed JSON), figures, the seven-axis robustness evaluation plan with executed-versus-deferred axes clearly marked, the FAR / precision-lift / PR-AUC analysis bundle, the SAR-integration plan (future work only), and the VWorld-key acquisition guide are released together with the manuscript as a single reproducibility package; readers can re-execute the three-event benchmark end-to-end from the released configs and code, and the working-hypothesis status of the typology mapping leaves an obvious natural next step, validation on additional independent Korean events under frozen numeric preregistration, for a follow-on paper.

# Declarations

**Funding.** This work was supported by the National Research Foundation of Korea (NRF) grant funded by the Korea government (Ministry of Science and ICT, MSIT) under Grant RS-2023-002772264.

Competing interests. The authors declare no competing financial or non-financial interests relevant to the content of this article.

Ethics approval and consent to participate. Not applicable, this study uses only publicly available Earth-observation data (GPM IMERG, Sentinel-2, Copernicus DSM) and publicly released Korean administrative landslide reports (NIDR, data.go.kr service ID 15074816); no human subjects or animal experiments are involved.

Consent for publication. Not applicable.

Data availability. All datasets used are publicly available: GPM IMERG V07 precipitation and Sentinel-2 L2A imagery via Google Earth Engine; Copernicus GLO-30 DSM as pre-downloaded COG tiles; KIGAM 1:50 000 Korean geology vector (Korea Institute of Geoscience and Mineral Resources); NIDR administrative-area landslide records via the Korean public-data portal (data.go.kr service ID 15074816) and VWorld geocoder 2.0 (vworld.kr). Per-event processed outputs (AgentTrace JSON records, NIDR geocoded GeoJSON, run logs) and the three-event analysis bundles (FAR-filter JSON/CSV, Axis 3/4/6 JSON/CSV, isotonic calibration JSON, post-hoc refinement JSON) are released in the code repository below. Large intermediate raster outputs (per-event probability rasters, DEM UTM mosaics) are regeneratable from the released configs and are therefore not redistributed; the pipeline reproduces them end-to-end from the public data sources.

Code availability. The full LandslideKR orchestrator code, per-event configurations, analysis scripts, executed traces, and the manuscript source are publicly available at <https://github.com/egpark-knu/landslidekr>. The repository includes the runtime fallback chain for topographic preprocessing (richdem $\to$ pysheds $\to$ numpy), the year-match NIDR filter documented in §2.3, and the offline recomputation and figure-generation scripts referenced in §3 ([`scripts/run_case.py`](https://github.com/egpark-knu/landslidekr/blob/main/scripts/run_case.py), [`scripts/run_benchmarks.py`](https://github.com/egpark-knu/landslidekr/blob/main/scripts/run_benchmarks.py), [`scripts/apply_far_filters.py`](https://github.com/egpark-knu/landslidekr/blob/main/scripts/apply_far_filters.py), [`scripts/axis3_stochastic_repeatability.py`](https://github.com/egpark-knu/landslidekr/blob/main/scripts/axis3_stochastic_repeatability.py), [`scripts/axis4_param_sensitivity.py`](https://github.com/egpark-knu/landslidekr/blob/main/scripts/axis4_param_sensitivity.py), [`scripts/axis6_label_ablation.py`](https://github.com/egpark-knu/landslidekr/blob/main/scripts/axis6_label_ablation.py), [`scripts/calibration_isotonic.py`](https://github.com/egpark-knu/landslidekr/blob/main/scripts/calibration_isotonic.py), [`scripts/post_hoc_refinement.py`](https://github.com/egpark-knu/landslidekr/blob/main/scripts/post_hoc_refinement.py), and the [`scripts/make_fig*.py`](https://github.com/egpark-knu/landslidekr/tree/main/scripts) figure generators). A pinned archive of the submission-associated release will be deposited to Zenodo with a DOI upon acceptance.

Materials availability. Not applicable, no new physical materials were generated.

Author contributions. E.P. conceived the study, designed the benchmark, implemented the LandslideKR orchestrator and analysis code, executed the three-event runs, prepared the figures and tables, wrote the manuscript, and is the corresponding author. T.K. and J.P. contributed to code review, analysis discussion, and manuscript revision. All authors read and approved the final manuscript.


# References

Baum, R. L., Savage, W. Z., & Godt, J. W. (2008). *TRIGRS, A Fortran program for transient rainfall infiltration and grid-based regional slope-stability analysis, version 2.0*. U.S. Geological Survey Open-File Report 2008-1159. https://pubs.usgs.gov/of/2008/1159/

Chrysafi, A., Tsangaratos, P., Ilia, I., & Chen, W. (2024). Rapid landslide detection following an extreme rainfall event using remote sensing indices, synthetic aperture radar imagery, and probabilistic methods. *Land*, 14(1), 21. https://doi.org/10.3390/land14010021

Eu, S., Seo, J., Lee, K., Woo, C., & Lee, C. (2025). Nonstructural landslide mitigation of the Republic of Korea. *Landslides*, 22(3), 763–772. https://doi.org/10.1007/s10346-024-02445-z

Lee, S., & Lee, S. (2024). Landslide susceptibility assessment of South Korea using stacking ensemble machine learning. *Geoenvironmental Disasters*, 11(1). https://doi.org/10.1186/s40677-024-00271-y

Lee, S., Roh, M., Jo, H., Joon, K., & Lee, W. (2025). Machine learning-based rainfall-induced landslide susceptibility model and short-term early warning assessment in South Korea. *Landslides*, 22(8), 2809–2827. https://doi.org/10.1007/s10346-025-02513-y

Merghadi, A., Yunus, A. P., Dou, J., Whiteley, J., ThaiPham, B., Bui, D. T., Avtar, R., & Abderrahmane, B. (2020). Machine learning methods for landslide susceptibility studies: A comparative overview of algorithm performance. *Earth-Science Reviews*, 207, 103225. https://doi.org/10.1016/j.earscirev.2020.103225

Montgomery, D. R., & Dietrich, W. E. (1994). A physically based model for the topographic control on shallow landsliding. *Water Resources Research*, 30(4), 1153–1171. https://doi.org/10.1029/93WR02979

Notti, D., Cignetti, M., Godone, D., & Giordan, D. (2023). Semi-automatic mapping of shallow landslides using free Sentinel-2 images and Google Earth Engine. *Natural Hazards and Earth System Sciences*, 23(7), 2625–2648. https://doi.org/10.5194/nhess-23-2625-2023

Pack, R. T., Tarboton, D. G., & Goodwin, C. N. (1998). The SINMAP approach to terrain stability mapping. In *Proceedings of the 8th Congress of the International Association of Engineering Geology and the Environment* (Vol. 2, pp. 1157–1165). Vancouver, Canada.

Park, H. J., Lee, J. H., & Woo, I. (2013). Assessment of rainfall-induced shallow landslide susceptibility using a GIS-based probabilistic approach. *Engineering Geology*, 161, 1–15. https://doi.org/10.1016/j.enggeo.2013.04.011

Park, E. (2026). WildfireKR: An LLM-agent-orchestrated reproducible wildfire-spread benchmark for Korea. *IEEE Access* (in press). Open-access preprint and code: https://github.com/eungyupark/wildfire_kr.
