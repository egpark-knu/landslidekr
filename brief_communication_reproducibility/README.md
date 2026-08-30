# Brief communication reproducibility package

This directory publishes six frozen research artifacts used by the brief communication. The artifacts are stored byte-for-byte; the sizes and SHA-256 identities below are the verification authority for this package.

## Published artifacts

| Artifact | Repository path | Size (bytes) | SHA-256 |
|---|---|---:|---|
| Yecheon 2023 evaluated Sentinel pixel labels | `brief_communication_reproducibility/data/yecheon_2023/consensus_label.tif` | 126,195 | `f1d78212dc5a47c55d2a032a5ccd9e1d0ef287e16b62c9b33de9bbe820c8e233` |
| Yecheon 2023 stored national-inventory pixel labels | `brief_communication_reproducibility/data/yecheon_2023/consensus_label_variant_B.tif` | 55,104 | `f2c14512cfa65e35340ed23702cc6f09d013ed6e3179e33636cc7016e2eae4d9` |
| Chuncheon 2020 stored national-inventory pixel labels | `brief_communication_reproducibility/data/chuncheon_2020/consensus_label_variant_B.tif` | 6,507 | `34c18ed9bae2b8302ef7c010074dde4be21f62da59b05c7fec70ae9c66b296dc` |
| Forest-service unit statistics | `brief_communication_reproducibility/data/frozen_tables/unit_level_stats.csv` | 31,335 | `273aff475d5b264e2ce8e4fe04da9ad1a8d45a3f99b0df9afccb69a88ef1def7` |
| Eleven-cell Figure 1 result ledger | `brief_communication_reproducibility/data/frozen_tables/figure1_reproduction.json` | 18,766 | `39d622d6993d07ca8cbd3f77a29de06ebf86ab41b0f82910de0bf5422a68a1b8` |
| Figure 2 renderer | `brief_communication_reproducibility/scripts/render_figure2_turn07a2.py` | 74,531 | `1f781c138e9b0f322d22c93e7fe1c7c25e4f860ee57fb211ccf9fc1d2729ba2a` |

The following frozen table was already public and is referenced rather than duplicated:

| Artifact | Repository path | Size (bytes) | SHA-256 |
|---|---|---:|---|
| Sentinel administrative-unit statistics | `nhess_reproducibility/data/frozen_tables/aggregate_sentinel_unit_stats.csv` | 30,583 | `69cbd314733e632d604d96c650e7b33cc7c49a6e81c9a0ce1413837b8efec486` |

## Copernicus GLO-30 acquisition for Figure 2

The Figure 2 terrain background uses a derived raster, `dem_utm.tif` (37,763,880 bytes; SHA-256 `58a1be2058658afd0f989890bdd83f877bf1d1c35ec31db91d5a8393e2dea7ef`). That derivative is not redistributed here. Its source is the Copernicus DEM GLO-30 digital surface model, dataset `COP-DEM_GLO-30-DGED` (`productType` `SAR_DGE_30_A4AD`).

The Figure 2 AOI is `[127.6, 36.3, 128.9, 37.0]` in EPSG:4326. The repository preprocessing code uses the four 1-degree public COGs below. These URLs and byte identities were verified on 2026-08-30.

| Source COG | Public object URL | Size (bytes) | SHA-256 |
|---|---|---:|---|
| `Copernicus_DSM_COG_10_N36_00_E127_00_DEM.tif` | [download](https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N36_00_E127_00_DEM/Copernicus_DSM_COG_10_N36_00_E127_00_DEM.tif) | 49,583,060 | `5acd8774fc11205e1029b20a59f3444750ac5546a5186e936b8bf334a0f9f48e` |
| `Copernicus_DSM_COG_10_N36_00_E128_00_DEM.tif` | [download](https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N36_00_E128_00_DEM/Copernicus_DSM_COG_10_N36_00_E128_00_DEM.tif) | 48,490,284 | `8af5b10b27529358db96d8b019c8c5fee09426dcc48a831fe5f16514febd47f8` |
| `Copernicus_DSM_COG_10_N37_00_E127_00_DEM.tif` | [download](https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N37_00_E127_00_DEM/Copernicus_DSM_COG_10_N37_00_E127_00_DEM.tif) | 49,403,795 | `4f8fef79da8c18ed9a9a0fb97b3d2695c4681181e013e039d87044e5479f7df6` |
| `Copernicus_DSM_COG_10_N37_00_E128_00_DEM.tif` | [download](https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N37_00_E128_00_DEM/Copernicus_DSM_COG_10_N37_00_E128_00_DEM.tif) | 45,141,829 | `69036070795162395dcea060375abba2d448dc2a5b74949844784466191b707c` |

For the current official catalogue and access route, see the [Copernicus DEM collection](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) and [Copernicus Contributing Missions documentation](https://documentation.dataspace.copernicus.eu/Data/Others/CCM.html). As checked on 2026-08-30, Copernicus Data Space access to GLO-30 requires registration with Copernicus Contributing Missions access enabled and is available through Copernicus Browser or OData. The [public COG documentation](https://copernicus-dem-30m.s3.amazonaws.com/readme.html) describes the object layout used above. Follow the official product page for the current license, citation DOI, and required upstream attribution.

Place the four unchanged COG files in one directory, then run the tracked preprocessing module from the repository root:

```bash
python -m landslide_kr.preprocess.dem_mosaic \
  <directory-containing-the-four-COGs> \
  '127.6,36.3,128.9,37.0' \
  <output-dem.tif>
```

`landslide_kr/preprocess/dem_mosaic.py` selects the intersecting tiles, mosaics the AOI with a 0.02-degree buffer, reprojects it to UTM zone 52N (EPSG:32652), and writes a 30 m raster using bilinear resampling. The published renderer is intentionally preserved at its recorded hash and contains original absolute source paths; running it elsewhere requires mapping those dependencies to local paths without treating a modified script as the frozen artifact.

## Scope and non-redistributed inputs

- `dem_utm.tif` is not distributed. The acquisition and preprocessing route above identifies its source and construction.
- `emd_all.gpkg` is not distributed. Its frozen local identity is 143,622,144 bytes with SHA-256 `9c4f3697f7fab5ed556d77efb28caf353cc2b47a201e93d0609491b50efe075c`; its provider, release, version, and license remain unresolved.
- The national-inventory label rasters in this package are public held artifacts. This package does not claim to regenerate their upstream national-inventory lineage or the administrative boundary file.
- The package supports evaluation of the stored artifacts and documents the terrain acquisition route. It does not claim universal regeneration or software-version-independent byte reproduction of the excluded derived DEM.

## Repository license status

No tracked `LICENSE` or `COPYING` file existed in this repository when this package was published. Public visibility is not a grant of reuse rights. Consult the relevant rights holder and upstream source terms for each artifact; for Copernicus GLO-30, use the official product page linked above. No repository license is selected or implied by this README.
