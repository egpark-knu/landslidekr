# VWorld API 키 발급 가이드 (LandslideKR 팀원용)

> **상태 (2026-04-14 16:45)**: 팀원이 발급한 키 수령 완료. 새 키 prefix `A28C7BD3-***`. 등록된 서비스 URL: `https://geoaialign.ai/`. 저장: `~/.mas/vworld.json` (chmod 600) + `.zshrc` line 25 `VWORLD_API_KEY` 환경 변수. 이전 키 `4DA2032F-***`는 대체됨.


**목적**: NIDR 산림청 API(15074816)가 제공하는 행정구역-레벨 주소를 위/경도 좌표로 변환하여 Sentinel-2 scar 래스터와 정확히 join하기 위함. Yecheon 2023 run처럼 NIDR 서비스가 타임아웃되면 fallback으로 Sentinel-only 레이블을 쓰지만, VWorld가 있으면 NIDR 보조 레이블을 살릴 수 있어 label ablation(§5 Axis 6)의 defensibility가 올라간다.

## 1. 등록 단계 (상세)

### 1-1. 계정 생성
1. https://www.vworld.kr 접속
2. 오른쪽 위 "회원가입" 클릭
3. 일반회원 선택 (기관/사업자 아님 — 연구 목적이면 일반으로 충분)
4. 본인 확인 방식:
   - 휴대전화 본인 인증 (권장 — 한국 휴대전화 필수)
   - 또는 이메일 + 아이핀(i-PIN)
5. 필수 입력: 이름, 생년월일, 휴대전화 번호, 이메일
6. 이용약관 동의 후 가입 완료 (즉시 활성화)

### 1-2. 개발자 센터 진입
1. 로그인 후 상단 메뉴 "오픈API" → "인증키 발급" 이동
   - 직링크: https://www.vworld.kr/dev/v4api.do
2. "2D/3D Open API" 가 아닌 "지오코더 API(Geocoder 2.0)" 탭 확인

### 1-3. 인증키 신청
1. "인증키 신청" 버튼 클릭
2. 입력 필드:

| 필드 | 값 |
|---|---|
| 서비스명 | `LandslideKR NIDR geocoding` (임의) |
| 서비스 URL | `http://localhost` (개발용이면 충분. 실서비스는 실제 도메인) |
| 서비스 분류 | `연구/학술용` |
| 이용 목적 | `한국 산사태 연구: 산림청 NIDR 행정구역 보고서의 주소를 좌표로 변환하여 Sentinel-2 기반 산사태 scar 지도와 결합. 논문 투고용 공개 연구 파이프라인.` |
| 활용 범위 | `본인 활용` |
| 이용 기간 | 최대 선택 (보통 2년) |

3. "지오코더 2.0" API를 선택 (중요! "2D 지도" "3D 지도"는 불필요)
4. 신청 완료

### 1-4. 승인 대기
- 영업일 기준 1~2일
- 승인 메일 수신 or "My 페이지 > 인증키 관리" 에서 상태 확인
- 승인되면 API 키 문자열이 노출됨 (형식: `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` UUID 형태)

## 2. 키 전달 후 저장 위치

받은 키는 교수님에게 공유 → 교수님이 아래 경로에 저장:

```bash
# ~/.mas/vworld.json
{
  "api_key": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
  "issued_at": "2026-04-XX",
  "owner": "team_member_name",
  "usage": "LandslideKR NIDR geocoding"
}
```

권한: `chmod 600 ~/.mas/vworld.json`

또는 환경 변수로:
```bash
export VWORLD_API_KEY="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
```
(교수님 `.zshrc` 26번째 줄에 이미 패턴 있음)

## 3. API 호출 예시 (파이프라인이 쓰는 형식)

```python
import requests, json
from pathlib import Path

key = json.load(open(Path.home() / ".mas/vworld.json"))["api_key"]

params = {
    "service": "address",
    "request": "GetCoord",
    "version": "2.0",
    "crs": "EPSG:4326",
    "address": "경상북도 예천군 효자면",  # NIDR 보고서의 주소
    "type": "PARCEL",  # 지번주소
    "key": key,
}
r = requests.get("https://api.vworld.kr/req/address", params=params, timeout=15)
r.raise_for_status()
data = r.json()
# data["response"]["result"]["point"]["x"], ["y"]
```

실패 모드:
- `INVALID_KEY` — 키 오타 또는 아직 승인 안 됨
- `UNREGISTERED_IP` — 서비스 URL/IP가 신청 시 등록한 값과 다름 (localhost로 신청했으면 localhost만 됨 — 교수님 개인 IP도 등록 추가 필요할 수 있음)
- `QUOTA_EXCEEDED` — 일일 호출량 초과 (일반 계정 보통 40,000건/일)

## 4. 쿼터 (일반 회원 기준)

- 지오코더 2.0: 40,000건/일 (대략)
- 산사태 NIDR 보고서는 연 수천 건 수준이라 쿼터 부족 가능성 없음
- 캐싱을 구현하면 같은 주소 재호출 없음 (파이프라인에 이미 lru_cache 준비됨)

## 5. 대안 (VWorld 어려울 경우)

| 대안 | 장점 | 단점 |
|---|---|---|
| Google Maps Geocoding API | 한국 주소 커버리지 우수 | 유료 (무료 쿼터 월 $200 크레딧까지) |
| Kakao Local API | 무료, 한국 최적화 | 별도 카카오 개발자 등록 필요 |
| Naver Cloud Platform Geocoding | 무료 (한도 내) | 네이버 클라우드 등록 필요 |

VWorld가 가장 간단하고 한국 행정구역 주소에 특화되어 있어 1순위다. 안 되면 Kakao가 2순위.

## 6. 팀원에게 전달할 요약 메시지

> 안녕하세요, LandslideKR 연구 파이프라인에서 산림청 NIDR API가 주는 행정구역 주소를 좌표로 변환하기 위해 VWorld 지오코더 2.0 API 키가 필요합니다. https://www.vworld.kr 에서 일반 회원으로 가입하시고, 오픈API → 인증키 발급 메뉴에서 서비스 URL은 http://localhost, API 종류는 "지오코더 2.0"로 신청해 주세요. 승인까지 1~2영업일 걸립니다. 승인되면 My 페이지에서 키(UUID 형태) 확인하셔서 교수님께 전달해 주세요. 신청 양식의 "이용 목적" 칸에는 `LandslideKR 연구 파이프라인 NIDR 지오코딩`이라고 적어 주시면 됩니다.
