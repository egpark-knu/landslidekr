# NIDR API 키 발급 요청 — 팀원 전달용 스펙

**목적**: 산사태 논문(LandslideKR)의 이벤트 라벨 자동 수집

---

## 발급 대상

**API 이름**: 산림청_과거산사태 정보
**제공 기관**: 산림청 / 한국임업진흥원
**등록 기관**: 공공데이터포털 (data.go.kr)
**API 일련번호**: **15074816**
**상세 URL**: https://www.data.go.kr/data/15074816/openapi.do

---

## 발급 절차 (팀원이 수행)

1. **공공데이터포털 회원가입**: https://www.data.go.kr/ (개인/단체 아무나 가능)
2. **API 활용신청**: 위 15074816 페이지에서 "활용신청" 클릭
3. **신청 양식 기입**:
   - 활용목적: "학술연구 — 한국 강우유발 산사태 Nowcasting 벤치마크 구축 (IEEE Access 투고)"
   - 사용 시스템: 비영리 연구 목적
   - 일일 트래픽: 1,000회 이하 (보수적 추정)
   - 기간: 2년
4. **승인 대기**: 보통 1~3영업일
5. **키 발급 완료 후**: "마이페이지 > 데이터 활용 > 개발계정" 에서 **일반 인증키(Decoding)** 복사
6. **박은규 교수에게 전달**: 텔레그램 또는 암호화 채널로 키 문자열만 공유 (URL 포함 전체 key)

---

## API 응답 스키마 (키 발급 후 검증 필요)

**엔드포인트**:
```
https://apis.data.go.kr/1400000/pastLandSlideInfoService/getPastLandSlideInfoList
```

**요청 파라미터**:
| 이름 | 타입 | 설명 | 예 |
|------|------|------|-----|
| serviceKey | string | 발급받은 인증키 | ... |
| dsrYear | string | 재해연도 | 2022 |
| ctprvnNm | string (optional) | 시도명 | 경상북도 |
| signguNm | string (optional) | 시군구명 | 포항시 남구 |
| pageNo | int | 페이지 번호 | 1 |
| numOfRows | int | 페이지당 레코드 수 (max 1000) | 1000 |
| type | string | "json" 또는 "xml" | json |

**응답 구조 (JSON, 확인 필요)**:
```json
{
  "response": {
    "body": {
      "totalCount": 1234,
      "numOfRows": 1000,
      "pageNo": 1,
      "items": {
        "item": [
          {
            "ocrrncDt": "20220906",     // 발생일 (YYYYMMDD)
            "ctprvnNm": "경상북도",
            "signguNm": "포항시 남구",
            "adres": "...",              // 상세 주소
            "lon": 129.350,              // 경도 (없을 수도 있음)
            "lat": 36.045,               // 위도 (없을 수도 있음)
            "dmgAr": 1234.5              // 피해면적 (㎡)
          },
          ...
        ]
      }
    }
  }
}
```

**⚠️ 불확실 항목** (키 받은 후 첫 호출로 검증 필요):
- 필드명: `ocrrncDt` vs `dsrOcrrncYmd`, `dmgAr` vs `damageArea`, 좌표 필드명 등
- 좌표가 응답에 포함되는지, 아니면 주소만 주고 별도 geocoding 필요한지
- `totalCount`가 실제 필터 후 개수인지 전체인지

첫 호출 후 필드명 확인되면 `landslide_kr/io/nidr_loader.py`의 `fetch_records()` 매핑 수정.

---

## 대체 소스 (키 없이도 가능)

1. **산사태통계 Excel 다운로드**: https://sansatai.forest.go.kr/data/statsInYearList.do
   - 연도별 통계만 있음 (개별 좌표 없음)
2. **자연재해통계지도**: https://ndsm.mods.go.kr/ndsm/srv/map/intMap.do?type=lndsld
   - 시각화만, raw 좌표 추출 어려움
3. **재난안전데이터공유플랫폼**: https://www.safetydata.go.kr/
   - 별도 키 필요, 구조 유사

→ 위 중 API(15074816)가 가장 구조화된 소스라 우선 사용.

---

## 보안

- 키는 개인 정보에 해당 (발급자 명의). 레포지토리 commit 금지.
- `~/.mas/data_go_kr.json` 에 저장 권장:
  ```json
  {"service_key": "발급받은_키_문자열"}
  ```
- 또는 env 변수 `DATA_GO_KR_SERVICE_KEY`.

---

## 팀원 연락용 요약 (복사해서 보낼 수 있는 버전)

> 안녕하세요. 산사태 연구용으로 공공데이터포털(data.go.kr)에서 **API 번호 15074816 "산림청_과거산사태 정보"** 활용신청 후 일반 인증키(Decoding)를 발급받아 주시면 감사하겠습니다. 활용 목적은 "학술연구 — 한국 산사태 Nowcasting 벤치마크(IEEE Access 투고)"로 적어주세요. 발급 완료되면 키 문자열만 박은규 교수께 텔레그램 DM으로 전달 부탁드립니다. URL: https://www.data.go.kr/data/15074816/openapi.do
