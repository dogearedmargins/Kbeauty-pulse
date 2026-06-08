# K-Beauty Pulse

**글로벌 K-Beauty 트렌드 B2B 인텔리전스 대시보드**

🔗 **Live** → [kbeauty-pulse.vercel.app](https://kbeauty-pulse.vercel.app)

---

## 무엇인가

K-Beauty Pulse는 화장품 업계 브랜드사·유통사 담당자를 위한 **글로벌 트렌드 모니터링 대시보드**입니다.

매주 업데이트되는 5개 지역의 K-beauty 트렌드 데이터를 한 화면에서 확인하고, 실무 보고 및 전략 수립에 바로 활용할 수 있는 수준의 디테일을 제공하는 것을 목표로 만들었습니다.

---

## 누구를 위한 도구인가

- K-beauty 브랜드사 마케팅·영업 담당자
- 글로벌 유통사 MD 및 바이어
- 트렌드 리서치 및 보고서 작성이 필요한 뷰티 업계 실무자

---

## 주요 기능

### 트렌드 대시보드
5개 지역(Americas / Europe / Southeast Asia / Middle East / India)별로 아래 데이터를 제공합니다.

- **Weekly Best Sellers** — 지역별 주간 인기 제품 랭킹
- **Channel Share** — 온·오프라인 채널별 판매 비중
- **Trending Keywords** — 지역별 검색량 급상승 키워드
- **Keyword Ranking** — Google Trends 기반 트렌드 강도 지수 (0–100)
- **Signal Cards** — 이번 주 주목할 뉴스·숫자·브랜드 동향
- **관세청 수출 현황** — 공식 데이터 기반 지역별·품목별 수출액 추이
- **AI Insight** — Groq AI가 생성하는 지역별 트렌드 요약

### 키워드 딥다이브
- 키워드별 월별 검색량 히트맵 (시즈널리티 분석)
- 키워드 → 연관 제품 연결맵
- Google Trends 기반 월별 검색량 트렌드 차트

### 주간 이메일 리포트 *(선택)*
대시보드 내용을 매주 월요일 이메일로 자동 발송받을 수 있습니다. GitHub Actions + Gmail SMTP 기반으로 구성되어 있으며, 별도 설정 없이 대시보드만 사용해도 무방합니다.

---

## 데이터 소스

모든 데이터는 검증된 소스만 사용합니다. 추정치나 생성된 데이터는 사용하지 않습니다.

**해외 B2B 미디어**
WWD · BeautyMatter · CosmeticsDesign-Asia · CosmeticsBusiness · GCI Global Cosmetics News · 조선비즈

**한국 공공기관**
관세청 수출입무역통계 · KOTRA · KCII · KITA · 더케이뷰티사이언스

**한국 전문지**
코스모닝 · 뷰티누리 · CNC News

---

## 기술 스택

| 구성 | 사용 기술 |
|---|---|
| 호스팅 | Vercel (Serverless Functions) |
| AI 분석 | Groq API (`llama-3.3-70b-versatile`) |
| 이미지 | Unsplash API |
| 뉴스 수집 | RSS + Groq AI 필터링 (B2B 관련성 자동 분류) |
| 키워드 데이터 | Google Trends (pytrends, 주 1회 업데이트) |
| 이메일 발송 | Gmail SMTP + GitHub Actions |
| 데이터 저장 | `data.json` + `history/` 폴더 |

---

## 업데이트 주기

| 항목 | 주기 |
|---|---|
| Signal Cards (뉴스) | 매일 자동 수집 |
| 키워드 트렌드 점수 | 매주 업데이트 |
| 관세청 수출 데이터 | 분기별 공식 발표 기준 |
| 지역별 트렌드·셀러 | 매주 업데이트 |

---

## 이메일 리포트 세팅 방법 *(선택)*

주간 이메일 리포트를 받으려면 아래 5개 GitHub Secret을 설정하세요.

| Secret | 값 |
|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) 에서 발급 |
| `GMAIL_ADDRESS` | 발신 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (16자리) |
| `REDDIT_CLIENT_ID` | Reddit 앱 client_id |
| `REDDIT_CLIENT_SECRET` | Reddit 앱 secret |

설정 후 Actions 탭 → "K-Beauty Pulse Weekly Report" → Run workflow로 테스트 가능합니다.
매주 **월요일 오전 9시 (KST)** 자동 실행됩니다.
