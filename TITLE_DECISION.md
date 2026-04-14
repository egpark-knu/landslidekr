# Tentative Title Decision

**Date**: 2026-04-14
**Status**: Tentative (pre-experiment; subject to post-result refinement)

---

## 선정된 제목 (v0.4 benchmark-centered, HP Round 4 binding)

> **Working title (tentative)**: *One Physical Model, Three Korean Rainfall Events, Diverging Skill: A Benchmark-Led Case for Agentic Model Selection in Landslide Nowcasting*

대안 후보 (모두 benchmark-led, agent는 enabling infrastructure):
- *Event-Type-Dependent Applicability of SHALSTAB Across Korean Typhoon and Monsoon Rainfall: An Open Agentic Benchmark*
- *When One Physical Model Is Not Enough: A Three-Event Korean Benchmark for Rainfall-Triggered Landslide Nowcasting*

**Running header (LaTeX)**: Three-Event Korean Benchmark for Rainfall-Triggered Landslides

### v0.4 framing 변경 (이전 v0.2/v0.3 대비)
- HP Round 4 (codex-99, 2026-04-14 16:00): novelty split 해결 위해 title을 benchmark-led로 재잠금. Agent는 enabling infrastructure로 강등. 자세한 내역: `manuscript_outline.md` v0.4 Position 섹션.

### Round 2 refinement (이전 안 대비 변경)

| 항목 | 이전 (Round 1) | 현재 (Round 2) | 이유 |
|------|---------------|---------------|------|
| Framework → | Decision Support Framework | **System** | "Framework"는 모호. 우리는 구현 + 벤치마크를 낸다 |
| Autonomous | Autonomous Event-Based | (제거) | Human-in-the-loop이 남는다. 과대 주장 제거 — reviewer 공격 면 |
| Scope | Event-Based | **Rainfall-Triggered** | SHALSTAB 물리 가정(강우→간극수압)과 정렬, 지진성 제외 명시 |
| Validation | (명시 없음) | **Retrospective Benchmarking on the 2022 Pohang and 2023 Yecheon Events** | 사건이 과거인 점 정직화, "where is the nowcast?" 공격 방어 |

### Contribution Statement (1 sentence — reviewer "so what?" 답변)

> We report a three-event Korean retrospective benchmark of a lithology-conditional Monte Carlo SHALSTAB ensemble on structurally distinct rainfall–landslide events — Typhoon Hinnamnor (Pohang 2022, 600 km², hillslope-dominated), the 2023 Central Korea Monsoon (Yecheon 2023, 12 100 km², mixed-terrain), and Chuncheon 2020 (monsoon, small mountainous AOI; the third point that separates rainfall typology from AOI size and terrain mix). Reference labels are a positive-evidence proxy combining Sentinel-2 NDVI-change scars with National Institute for Disaster Reduction (NIDR) reports; the Pohang reported run used Sentinel-scar-only labels because NIDR was configured but not joined in that executed log run, and the Yecheon run reverted to Sentinel-only after an NIDR API timeout — both are disclosed symmetrically. The benchmark is made possible by **LandslideKR**, an open LLM-agent data-and-compute orchestrator (eleven-step traced pipeline, GPM IMERG / SRTM / Sentinel-2 / KIGAM 1:50 000) released as enabling infrastructure. Unlike prior vision papers on agentic geohazard management (e.g., *Disaster Copilot*, arXiv 2510.16034), LandslideKR is an implementation with released traces, logs, and explicit label/execution provenance. Sentinel-1 SAR and an in-pipeline agentic model-selection layer are listed as future work and are **not integrated in this release**.

### Ground-truth limitation (reviewer 정직 프레이밍 — CRITICAL)

우리 연구의 "label"은 **complete ground truth가 아니다**. 두 층의 label을 **consensus**로 결합하되, 각 한계를 **drafting 단계에서부터 명시**한다:

| Source | Type | 한계 |
|--------|------|------|
| NIDR 산림청 15074816 | 사건 발생 행정구역 + 피해면적 (ha) | 위도/경도 미제공 → VWorld geocoder로 **주소→address-level centroid** 추정 (단일 점). 실제 scar polygon 아님. |
| Sentinel-2 NDVI change | 10m NDVI drop + slope filter | 농지/수확/낙엽 계절 변화 오경보; 구름/그림자; 식생이 없는 암반 scar 미검출. **proxy label**. |
| Consensus (NIDR ∪ scar) | 두 source 중 하나라도 양성 | 누락(FN) 필연. 진짜 precision은 현장 조사 없이는 측정 불가. |

→ Paper에서 **"ground truth"라는 단어를 사용하지 않고** "positive evidence label" 또는 "composite reference label"로 명시. Reviewer "ground truth 부재 자백" 공격을 **선제적 정직**으로 전환.

### Reviewer 공격 + 방어 (업데이트)

| 공격 | 방어 |
|------|------|
| "Sentinel-2 NDVI change는 true scar 아니다" | 동의. **consensus (NIDR 점 + scar)** 사용. 둘 다 한계 명시. precision은 label-set precision, not field-verified. |
| "NIDR is administrative-area only" | 주소 centroid + 30 m 버퍼 proxy로만 사용. 300 m tolerance-hit buffer는 **미구현**이므로 evaluation에서 주장하지 않는다 (§5 Limitations에 명시). 건별 polygon 주장도 안 함. |
| "Ground truth 없는 benchmark가 MPU 가치 있는가?" | **개별 사건에 대한 field-verified catalog가 한국에는 존재하지 않는다 (published knowledge). 우리의 consensus label은 현재 가용한 최선의 reference이며, 이 한계를 정직하게 명시하고 lower-bound recall만 주장한다.** |

### Agent의 구체적 역할 (reviewer가 요구할 질문 대비)

| 파이프라인 단계 | Agent가 하는 일 |
|----------------|----------------|
| 입력 수집 | DEM 타일 선택, 강우 사건 감지 (GPM IMERG 임계값), 토지피복 레이어 매핑 |
| 전처리 | bbox clipping, CRS 정렬, soil class 기반 SHALSTAB 파라미터 구성 |
| 모델 실행 | SHALSTAB 구동 (필요 시 TRIGRS·SINMAP과 앙상블), 불확실성 샘플링 |
| 검증 | NIDR 자동 다운로드, Sentinel-2 scar 자동 탐지, POD/FAR/CSI 산출 |
| 보고 | 지도 + 메트릭 표 + 자연어 요약 + 위험 커뮤니케이션 초안 |

→ **Data/compute orchestrator** (단순 챗봇 아님, 그러나 model selector도 아님). 파이프라인의 각 단계를 순차 실행하고 `AgentTrace` 기록을 남긴다. Model selection은 future work로 명시 분리.

### 왜 이 제목인가

1. **WildfireKR 시리즈 계승** — 저자의 IEEE Access ACCEPTED 논문 "WildfireKR: An LLM-Agent Decision Support Framework for Autonomous Wildfire Spread Simulation in South Korea" 의 직접 후속작. 저자 포트폴리오에 시리즈(KR-suite) 형성.
2. **에이전트 전면화 (사용자 요구)** — "LLM-Agent"가 제목 두 번째 단어. 모델 나열이 아니라 **자율 시스템**이 주체.
3. **학술적 Gap 정확히 조준** — 아래 문헌 분석 참조.
4. **가진 데이터로 즉시 실행 가능** — Copernicus DEM 30m (보유) + GPM IMERG V07 (GEE) + Sentinel-1/2 (GEE) + NIDR 사건 기록 (공개).

---

## 경쟁 연구와의 차별화 (2024–2026 문헌)

| 선행 연구 | 성격 | 한계 | LandslideKR 차별점 |
|-----------|------|------|-------------------|
| **Disaster Copilot** (arXiv 2510.16034, 2025) | Multi-agent 비전 paper | **구현 없음**, 개념적 프레임워크만 제시 | **Operational 구현 + 벤치마크** |
| **LLM agents reshaping geotechnical** (ScienceDirect, 2025) | Perspective — LLM으로 landslide geometry 추정, 보고서 요약 | **End-to-end 예측 아님** (후처리 도우미) | **사전 nowcasting + 물리 모델 구동** |
| **Multimodal LLM landslide imagery** (Areerob 2025, *CACAIE*) | LLM이 이미지+프롬프트로 사후 판독 | **사후 탐지**, 강우 입력 없음 | **사건 발생 이전 강우 기반 예측** |
| **ML landslide nowcasting** (MLEWS 2026, *GeoHazards*) | Random Forest + 기상 nowcasting | **블랙박스**, 에이전트 아님 | **물리 모델 + LLM 오케스트레이션 + 투명성** |
| **AI landslide mapping** (Cambridge, 2025) | 지진/폭우 후 AI로 사면붕괴 mapping | **사후 대응**, 에이전트 아님 | **사전 예측 + 자율 파이프라인** |

**GAP 요약**:
- Disaster Copilot = 비전, **구현 없음** ← 우리가 구현한다
- LLM + geotech 논문들 = 전부 **사후 분석/요약 보조** ← 우리는 **사전 예측 엔진**을 에이전트로 운영
- 물리 모델 (SHALSTAB/TRIGRS) 을 LLM 에이전트가 **자율 orchestration** 한 사례 없음
- 한국 사면붕괴 이벤트(2022 포항, 2023 예천)에 대한 **공개 재현가능 벤치마크 없음**

---

## 학술적 가치 (왜 reviewer가 accept 해야 하는가)

1. **First agentic implementation** for pre-event landslide nowcasting (vs Disaster Copilot 비전)
2. **Bridges LLM + physical models** — 현재 LLM+landslide 문헌은 전부 post-hoc ML/interpretation
3. **Open, field-survey-free, reproducible benchmark** for Korea — 공개 위성/지질 데이터 기반
4. **Operational pilot** — WildfireKR 패턴 반복 → 방법론적 일반성 논증

---

## 가진 데이터로 바로 가능한가? (자원 검증)

| 자원 | 보유/접근 | 상태 |
|------|----------|------|
| Copernicus DEM 30m | `/Users/eungyupark/Dropbox/GeoAI/07_geodata/dem_30m_copernicus/` (35 tiles) | ✅ 심볼릭 링크 완료 |
| GPM IMERG V07 강우 | GEE | ✅ public cloud archive |
| Sentinel-1/2 | GEE | ✅ public cloud archive |
| 토양/토지피복 | GEE + Korea geodata | ✅ 심볼릭 링크 완료 |
| NIDR 사건 DB | 공공데이터포털 | ✅ 다운로드 가능 |
| 산사태 scar 자동검출 | Sentinel-2 NDVI change + slope filter | ✅ WildfireKR burn_scar 패턴 이식 |
| SHALSTAB 코드 | `landslide_kr/models/shalstab.py` | ✅ 테스트 4/4 통과 |
| 에이전트 인프라 | MAS (Claude+Codex+Gemini) | ✅ 검증된 환경 |

**결론**: 오늘 오후부터 Phase 3 (라벨) + Phase 4 (GEE) 병행 착수 가능.

---

## Target Journals (우선순위)

| 순위 | 저널 | IF | 적합도 |
|------|------|----|----|
| **1** | **IEEE Access** | 3.9 | **WildfireKR이 여기서 accepted — 자매편 전략** |
| 2 | *Landslides* (Springer) | 6.7 | 하드 타겟, 물리 모델 정량 비교 강화 필요 |
| 3 | *Natural Hazards* (Springer) | 4.2 | 안전한 2순위 |
| 4 | *Computers & Geosciences* | 5.1 | 소프트웨어 섹션 강조 시 |

**권장 전략 — MPU (Minimum Publishable Unit)**:
- **1차 투고**: IEEE Access (WildfireKR 자매편 + reviewer pool 겹침 활용)
- 6개월 내 확장 → *Landslides* 재투고 (물리 모델 3종 + 전국 확장)

---

## Tentative Structure (section 수준)

1. Introduction — LLM agents in disaster management, landslide nowcasting gap
2. Related Work — Disaster Copilot 비전, LLM+geotech, ML nowcasting
3. LandslideKR Architecture — agent layers, tools, data flow
4. Data & Models — DEM/rainfall/scar, SHALSTAB (optionally TRIGRS)
5. Case Studies — 2022 Pohang, 2023 Yecheon
6. Evaluation — POD/FAR/CSI vs NIDR, computational cost, agent autonomy
7. Discussion — 한계, InSAR 확장 여지, 다른 지역 이식성
8. Conclusion

---

## 다음 액션 (승인 대기)

1. Phase 3: NIDR 사건 DB 다운로드 + 2022/2023 이벤트 shape 준비
2. Phase 4: GEE 파이프라인 (GPM IMERG 일누적 + Sentinel-2 scar detection)
3. Agent architecture MVP: `landslide_kr/agent/` — orchestrator, tools
4. Abstract draft (300 words)
