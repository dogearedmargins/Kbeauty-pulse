# K-Beauty Pulse 🌿
> 매주 월요일, 글로벌 K-Beauty 트렌드를 자동으로 분석해서 이메일로 발송

**완전 무료 스택**: GitHub Actions + Groq API + Gmail SMTP

---

## 구조

```
main.py          ← 실행 진입점 (이것만 실행하면 끝)
scraper.py       ← 데이터 수집 (Google Trends + Reddit + RSS + Amazon)
analyzer.py      ← Groq AI 분석 (llama3-70b, 무료)
emailer.py       ← Gmail 자동 발송
.github/
  workflows/
    weekly.yml   ← 매주 월요일 자동 실행
requirements.txt
```

---

## 세팅 방법 (한 번만 하면 됨)

### Step 1 — API 키 발급

**A. Groq API 키 (무료)**
1. https://console.groq.com 접속 → 가입
2. API Keys → Create API Key
3. 키 복사해두기

**B. Gmail 앱 비밀번호**
1. Google 계정 → 보안 → 2단계 인증 활성화 (필수)
2. 보안 → 앱 비밀번호 → "K-Beauty Pulse" 이름으로 생성
3. 16자리 비밀번호 복사 (공백 없이)

**C. Reddit API (무료)**
1. https://www.reddit.com/prefs/apps 접속
2. "Create App" → script 선택
3. client_id (앱 이름 아래 짧은 문자열), secret 복사

---

### Step 2 — GitHub Repository 세팅

1. GitHub에서 새 repository 생성 (예: `kbeauty-pulse`)
2. 이 폴더 전체를 업로드
3. Settings → Secrets and variables → Actions → New repository secret

아래 5개 Secret 추가:

| Secret 이름 | 값 |
|---|---|
| `GROQ_API_KEY` | Groq에서 발급한 API 키 |
| `GMAIL_ADDRESS` | dogearedmargins@gmail.com |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (16자리) |
| `REDDIT_CLIENT_ID` | Reddit 앱 client_id |
| `REDDIT_CLIENT_SECRET` | Reddit 앱 secret |

---

### Step 3 — 테스트 실행

GitHub repository → Actions 탭 → "K-Beauty Pulse Weekly Report" → Run workflow

정상 실행되면 dogearedmargins@gmail.com으로 이메일 도착!

---

## 자동 실행 스케줄

매주 **월요일 오전 9시 (KST)** 자동 실행됨.
변경하려면 `.github/workflows/weekly.yml`의 cron 값 수정:
```yaml
- cron: "0 0 * * 1"   # 월요일 UTC 00:00 = KST 09:00
```

---

## 데이터 소스

| 소스 | 데이터 | 비용 |
|---|---|---|
| Google Trends (pytrends) | 지역별 키워드 검색량 | 무료 |
| Reddit API | r/AsianBeauty 트렌딩 포스트 | 무료 |
| BeautyMatter RSS | 최신 K-beauty 뉴스 | 무료 |
| CosmeticsBusiness RSS | 글로벌 뷰티 뉴스 | 무료 |
| Amazon Best Sellers | K-beauty 카테고리 TOP10 | 무료 |
| Groq API (llama3-70b) | AI 인사이트 생성 | 무료 |
| Gmail SMTP | 이메일 발송 | 무료 |
| GitHub Actions | 매주 자동 실행 | 무료 |
