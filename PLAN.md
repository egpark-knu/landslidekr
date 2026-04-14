# Korea Landslide Nowcasting — 실행 계획 (v1, 2026-04-14)

> WildfireKR (IEEE Access ACCEPTED) 파이프라인을 재활용하여 산사태 nowcasting 논문 생산.
> 타겟: *Landslides* (IF 5.2) 또는 *Natural Hazards* (IF 4.0) 또는 *RSE* (IF 13).

---

## 🎯 목표 (MPU — Minimum Publishable Unit)

**"LLM-agent가 Copernicus DEM, GPM IMERG, Sentinel-2, KIGAM 지질도를 오케스트레이션하여 공공 사건 라벨(NIDR)과 교차검증된 한국 최초 reproducible 산사태 nowcasting 벤치마크"**

정량 기여:
- N개 이상 사건 (최소 3건 목표: 2022 포항, 2023 극한호우 2건)
- 각 사건에 대한 IoU / Precision / Recall / F1 (WildfireKR 형식)
- 파라미터 민감도 분석 (friction_angle, cohesion, rainfall threshold)

---

## 🗂 자산 인벤토리

### ✅ 이미 있는 것

| 자산 | 경로 | 산사태 재사용 가능성 |
|------|------|---------------------|
| **Copernicus DEM 30m (35 tiles, 한국 전역)** | `geodata/dem_30m_copernicus/` | ⭐⭐⭐⭐⭐ — 슬로프, 기여유역 계산 기본 |
| **WildfireKR 사건 스크립트** (goseong, uljin, samcheok, gangneung, uiseong, palgongsan) | `docs/wildfire_reference_scripts/` | ⭐⭐⭐⭐ — 케이스 config 구조 재사용 |
| **WildfireKR case config 구조** (aoi.json, summary.json, ign.json) | `docs/wildfire_reference_data/gangneung_2022/` | ⭐⭐⭐⭐⭐ — 동일 구조 채택 |
| **WildfireKR benchmark pipeline** (run_asos_benchmarks, run_benchmarks) | `docs/wildfire_reference_scripts/run_benchmarks.py` | ⭐⭐⭐⭐⭐ — 벤치마크 자동화 재사용 |
| **WildfireKR 논문 LaTeX 템플릿** (IEEE Access) | `docs/wildfire_reference_scripts/../../paper_access.tex` | ⭐⭐⭐⭐⭐ — 논문 양식 즉시 재사용 |
| **GIS Korea geodata** (sigungu, sido, river, soil_drn, slope_all, geology) | `geodata/gis_korea_geodata/` | ⭐⭐⭐⭐⭐ — **slope_all.tif, soil_drn.gpkg, geology.gpkg 직접 사용** |
| **GIS Korea agents** (drastic, hydro, modflow, prediction, geostat) | 원본 경로 참조 | ⭐⭐⭐ — agent 호출 패턴 참고 |

### ❌ 아직 없는 것 (수집/생성 필요)

| 필요 데이터 | 소스 | 계획 |
|------------|------|------|
| **산사태 사건 라벨** (polygons) | 산림청 NIDR, 행안부 재해연보 | Phase 3에서 스크레이핑/수동 수집 |
| **GPM IMERG 강우** (30-min, cumulative) | GEE `NASA/GPM_L3/IMERG_V07` | Phase 4에서 GEE 스크립트 작성 |
| **Sentinel-1 pre/post InSAR** (변위) | GEE `COPERNICUS/S1_GRD` or ARIA | Phase 4 (선택사항, 주요 사건용) |
| **Dynamic World / WorldCover 2020** | GEE `GOOGLE/DYNAMICWORLD/V1`, `ESA/WorldCover/v200` | Phase 4 GEE 자동 |
| **SMAP soil moisture** | GEE `NASA/SMAP/SPL4SMGP/008` | Phase 4 GEE 자동 |
| **산사태 전/후 Sentinel-2 NDVI** (검증 라벨 보강) | GEE | Phase 4 |

### 🤔 데이터 Gap 분석

**Major gap 1: 산사태 사건 라벨 품질**
- NIDR은 공개 API가 없다. HTML 스크레이핑 또는 PDF 연보 파싱 필요
- 해결책: 
  - 2022 포항 산사태: 논문/보도자료에서 좌표 추출 (대략 20건)
  - 2023 극한호우(청주·영주·예천): 행안부 재해연보 + 뉴스
  - 대안: Sentinel-2 NDVI 감소(pre/post)로 landslide scar 자동 탐지 (WildfireKR의 sentinel_burn_scar.py 패턴 재사용!)

**Major gap 2: 토심(soil thickness)**
- SHALSTAB 파라미터 중 z (soil thickness)가 민감
- 해결책: ISRIC SoilGrids 250m (GEE `projects/soilgrids-isric/` 또는 직접 다운로드)
- 또는 SHALSTAB_iz = z·T (depth-transmissivity combined) 변수로 축약

**Minor gap: 지하수위**
- TRIGRS용. 첫 버전에서는 steady-state 가정, 생략

---

## 📋 실행 계획 (6주 로드맵)

### Week 1: 데이터 확보
- **Day 1-2**: GEE 파이프라인 (강우, DEM, 토지피복, 토양수분) — `collectors/gee_*.py`
- **Day 3-4**: 사건 라벨 수집 (포항 2022, 극한호우 2023) — 수동 + NDVI 자동
- **Day 5-7**: GIS Korea의 `slope_all.tif`, `geology.gpkg`, `soil_drn.gpkg` 통합

### Week 2: 모델 파이프라인
- **Day 8-10**: `shalstab.py` 완성 + 단위 테스트
- **Day 11-12**: `trigrs.py` 스캐폴드 (transient version)
- **Day 13-14**: Case runner (`scripts/run_case.py`) — WildfireKR pattern

### Week 3: 첫 MPU 케이스 (Pohang 2022)
- **Day 15-17**: SHALSTAB + 파라미터 스윕 (friction, cohesion)
- **Day 18-19**: 라벨 vs 예측 IoU/Precision/Recall
- **Day 20-21**: 민감도 분석 Figure

### Week 4: 추가 사건 + 모델 비교
- **Day 22-24**: 극한호우 2023 사건 2건
- **Day 25-28**: 모델 간 비교 (SHALSTAB vs TRIGRS vs SINMAP)

### Week 5: 논문 초안
- **Day 29-32**: Introduction, Methods, Results 초안
- **Day 33-35**: Figures (WildfireKR 형식 재사용)

### Week 6: Revision + Submit
- **Day 36-38**: Codex/Gemini 독립 리뷰
- **Day 39-40**: De-AI 파이프라인 + 서지 검증
- **Day 41-42**: *Landslides* or *Natural Hazards* 투고

---

## 🏗 인프라 스캐폴딩 (완료)

```
/Users/eungyupark/Dropbox/myproj/dev_260414_nowcasting/
├── landslide_kr/               # 핵심 패키지
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── shalstab.py         ✅ 작성됨 (핵심 방정식)
│   ├── collectors/
│   │   ├── __init__.py
│   │   └── gee_rainfall.py     ⚠️ 스켈레톤 (Phase 4에서 완성)
│   ├── io/
│   │   ├── __init__.py
│   │   └── case_config.py      ✅ 스키마 정의
│   └── viz/                    📂 placeholder
├── cases/
│   ├── pohang_2022/            📂 1차 MPU
│   └── extreme_rainfall_2023/  📂 2차 케이스
├── data/{dem,rainfall,insar,landcover,soil,labels}/
├── geodata/
│   ├── dem_30m_copernicus → /Users/eungyupark/Dropbox/GeoAI/07_geodata/dem_30m_copernicus/
│   └── gis_korea_geodata → /Users/eungyupark/Dropbox/GeoAI/01_2026_project/00_demo/dev_gis_korea/geodata/
├── docs/
│   ├── wildfire_reference_scripts → /Users/eungyupark/Dropbox/Manuscripts/0_wildfire/scripts/
│   └── wildfire_reference_data → /Users/eungyupark/Dropbox/Manuscripts/0_wildfire/data/
├── scripts/                    📂 run_case, run_benchmarks
├── figures/                    📂 논문 figure 저장
├── tests/                      📂 pytest
├── cases/, out/, communication/
└── PLAN.md                     ← **현재 문서**
```

---

## 🔍 다음 액션 (사용자 승인 대기)

**사용자 승인 필요 항목:**
1. **Phase 4 GEE 스크립트 작성 착수 여부** — `collectors/gee_*.py` 실제 코드
2. **Phase 3 사건 라벨 수집 방법 선택**:
   - (a) 수동 + 문헌 기반 (빠름, 정확도 중간)
   - (b) Sentinel-2 NDVI 자동 탐지 (느림, 자동화)
   - (c) 둘 다 병용 (권고)
3. **MPU 타겟 저널**:
   - (a) *Landslides* — 전문 저널, IF 5.2
   - (b) *Natural Hazards* — 종합, IF 4.0
   - (c) *Remote Sensing of Environment* (RSE) — 원격탐사 강조 시 IF 13
4. **모델 우선순위**:
   - 현재 계획: SHALSTAB 첫 → TRIGRS 두번째
   - 대안: SINMAP (probabilistic) 도 함께?

---

## ⚠️ 리스크 & 완화

| 리스크 | 완화 |
|--------|------|
| 산사태 사건 라벨 부족 | Sentinel-2 NDVI 자동 탐지로 보강 (WildfireKR의 `sentinel_burn_scar.py` 재사용) |
| SHALSTAB 파라미터 과적합 | LOOCV, 다중 사건 교차검증 (WildfireKR loocv_results.json 패턴) |
| GEE API quota | Drive export fallback (generate_fig5_safe.py 패턴 재사용) |
| 모델 계산 비용 | SHALSTAB은 steady-state → numpy 벡터화로 빠름 |
| **메모리 폭발 (GEE)** | `generate_fig5_safe.py`의 streaming download + scale guard 재사용 필수 |

---

## 📚 레퍼런스 (논문화 지원)

**핵심 선행연구:**
- Montgomery & Dietrich (1994) — SHALSTAB 원논문
- Baum et al. (2010) — TRIGRS USGS
- Pack et al. (2005) — SINMAP
- 이영진 et al. (2022) — 한국 산사태 통계 / 취약성
- Lombardo et al. (2020) — Landslide susceptibility ML vs physical

**WildfireKR 관련 (자사 자산):**
- Park et al. (2026, IEEE Access) — WildfireKR Korea calibration

---

> **이 계획은 인프라 스캐폴딩 완료 후 작성되었다. 승인 시 Phase 3-4로 진행한다.**
> **승인 전 실제 GEE 다운로드, 라벨 수집 실행 금지.**
