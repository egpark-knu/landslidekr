# Korea Landslide Nowcasting

LLM-agent-orchestrated physically-based landslide susceptibility nowcasting for Korea, combining global Earth-observation archives with lithology-conditional Monte Carlo parameter sampling and Sentinel-2-derived scar labels.

Inherits architecture from [WildfireKR](https://doi.org/10.1109/ACCESS.2026.xxx).

## Status (2026-04-14, v0.4 honest)

**Three-event retrospective benchmark executed.** Agent is a data/compute orchestrator; it does not currently select among physical models (see manuscript §1.2).

- ✅ Core modules (dem_mosaic, topo, lithology, ensemble, metrics, agent orchestrator) — unit + fixture tests pass
- ✅ GEE end-to-end executed for all three events (GPM IMERG, Copernicus DSM, Sentinel-2)
- ✅ Pohang 2022 retrospective: ROC-AUC 0.61, +0.20 separation (log run `out/pohang_2022_run_20260414_1513_C2.log`; stored agent_trace.json is a dry-run probe)
- ✅ Yecheon 2023 retrospective: ROC-AUC 0.45, rank-inverted; post-hoc slope-only AUC 0.67
- ✅ Chuncheon 2020 retrospective: ROC-AUC 0.50, near-random (third event disambiguating rainfall typology from AOI size)
- ✅ NIDR service-key + VWorld-geocoding integration used in §5.6 Axis-6 label-layer ablation (multi-province filter; Yecheon 273 in-bbox, Chuncheon 18 in-bbox)
- ⏳ Sentinel-1 SAR — **future work only**, not integrated
- ⏳ TRIGRS pilot — future work
- ⏳ In-pipeline agent model-selection layer — proposed, not implemented in this release

## Quick start

```bash
pip install -r requirements.txt
# Config validation (no external API calls)
python scripts/run_case.py cases/pohang_2022/config.json --dry-run
# Unit tests
python -m pytest tests/ -v
```

## Layout

- `landslide_kr/` — core package (models, collectors, io, viz)
- `cases/` — per-event configs
- `scripts/` — case runners, benchmark aggregators
- `geodata/` — symlinks to DEM (Copernicus 30m) + GIS Korea
- `docs/` — WildfireKR reference (symlinks)
- `PLAN.md` — 6-week roadmap

## Key models

| Model | Status | Reference |
|-------|--------|-----------|
| SHALSTAB (primary) | ✅ Core eqn + 4 unit tests | Montgomery & Dietrich (1994) |
| SINMAP-style MC (uncertainty) | ✅ Bounded-parameter ensemble + 5 tests | Pack et al. (1998) |
| Lithology-conditional params | ✅ 5 class × 5 param table | Park, Nikhil & Lee (2013) |
| TRIGRS (transient pilot) | 🔜 Scaffold planned (Pohang only) | Baum et al. (2008) USGS |

## Data sources (public Earth-observation archives + national geology)

- **DEM**: Copernicus GLO-30 (35 tiles, Korea nationwide) — local
- **Rainfall**: GPM IMERG V07 (30-min) — GEE
- **Soil**: ISRIC SoilGrids 250m — GEE
- **Landcover**: Dynamic World, WorldCover — GEE
- **Slope/Aspect**: computed from the DEM via `landslide_kr/preprocess/topo.py` (runtime fallback chain: richdem Dinf → pysheds D8 + Horn slope → numpy D8; the released runs used pysheds D8 + Horn as the richdem wheel is not available on Mac ARM64, consistent with the manuscript §2.1 description and the per-event agent_trace `topo.backend` field)
- **Event labels**: NIDR (forest service), Sentinel-2 NDVI pre/post auto-detection
