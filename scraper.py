"""
K-Beauty Pulse — scraper.py
데이터 수집: Google Trends (pytrends) + Reddit API + BeautyMatter RSS
완전 무료 소스만 사용
"""

import json
import time
import datetime
import feedparser
import praw
import requests
from pytrends.request import TrendReq

# ── 지역 설정 ──────────────────────────────────────────────
REGIONS = {
    "americas": {
        "label": "Americas",
        "geo": "US",
        "platform": "Amazon / TikTok Shop",
        "keywords": ["snail mucin", "glass skin", "korean sunscreen", "PDRN skincare", "milky toner"],
    },
    "europe": {
        "label": "Europe",
        "geo": "GB",
        "platform": "Lookfantastic / Boots",
        "keywords": ["korean skincare", "peptide serum", "LED face mask", "retinol", "clean beauty korean"],
    },
    "sea": {
        "label": "Southeast Asia",
        "geo": "SG",
        "platform": "Shopee / TikTok Shop",
        "keywords": ["tone up sunscreen", "whitening serum", "SPF stick", "glass skin", "brightening cream"],
    },
    "mideast": {
        "label": "Middle East",
        "geo": "AE",
        "platform": "Noon / Sephora ME",
        "keywords": ["anti aging korean", "halal skincare", "PDRN skincare", "ginseng serum", "korean glass skin"],
    },
    "india": {
        "label": "India",
        "geo": "IN",
        "platform": "Nykaa / Myntra",
        "keywords": ["niacinamide serum", "barrier repair", "vitamin c serum", "SPF sunscreen routine", "korean skincare"],
    },
}

REDDIT_SUBREDDITS = ["AsianBeauty", "SkincareAddiction", "kbeauty"]
BEAUTYMATTER_RSS  = "https://beautymatter.com/feed/"
COSMETICSBIZ_RSS  = "https://cosmeticsbusiness.com/rss"


# ── Google Trends ──────────────────────────────────────────
def fetch_google_trends(region_key: str) -> dict:
    """지역별 키워드 검색량 지수 (0-100) 수집"""
    region = REGIONS[region_key]
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))

    results = {}
    # pytrends는 한 번에 최대 5개 키워드
    kws = region["keywords"][:5]

    try:
        pytrends.build_payload(
            kws,
            cat=0,
            timeframe="now 7-d",   # 최근 7일
            geo=region["geo"],
            gprop="",
        )
        interest_df = pytrends.interest_over_time()

        if not interest_df.empty:
            for kw in kws:
                if kw in interest_df.columns:
                    results[kw] = {
                        "current": int(interest_df[kw].iloc[-1]),
                        "avg_7d":  int(interest_df[kw].mean()),
                        "peak":    int(interest_df[kw].max()),
                        "trend":   "up" if interest_df[kw].iloc[-1] > interest_df[kw].mean() else "down",
                    }
        time.sleep(2)  # rate limit 방지
    except Exception as e:
        print(f"[Trends] {region_key} 오류: {e}")
        # fallback: 빈 데이터
        for kw in kws:
            results[kw] = {"current": 0, "avg_7d": 0, "peak": 0, "trend": "unknown"}

    return results


# ── Reddit ─────────────────────────────────────────────────
def fetch_reddit(client_id: str, client_secret: str, user_agent: str) -> list:
    """r/AsianBeauty 등 핫 포스트 수집"""
    posts = []
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        for sub_name in REDDIT_SUBREDDITS:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.hot(limit=10):
                posts.append({
                    "subreddit": sub_name,
                    "title":     post.title,
                    "score":     post.score,
                    "comments":  post.num_comments,
                    "url":       f"https://reddit.com{post.permalink}",
                    "created":   datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d"),
                })
    except Exception as e:
        print(f"[Reddit] 오류: {e}")

    # 점수 높은 순 정렬
    return sorted(posts, key=lambda x: x["score"], reverse=True)[:15]


# ── RSS Feeds ──────────────────────────────────────────────
def fetch_rss_news() -> list:
    """BeautyMatter + CosmeticsBusiness RSS 최신 뉴스"""
    articles = []
    for feed_url in [BEAUTYMATTER_RSS, COSMETICSBIZ_RSS]:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "")
                # K-beauty 관련 필터
                if any(kw in title.lower() for kw in [
                    "k-beauty", "korean", "kbeauty", "cosrx", "laneige",
                    "beauty of joseon", "anua", "medicube", "innisfree",
                    "skincare", "ingredient", "serum", "sunscreen"
                ]):
                    articles.append({
                        "title":   title,
                        "summary": entry.get("summary", "")[:200],
                        "link":    entry.get("link", ""),
                        "date":    entry.get("published", ""),
                        "source":  feed.feed.get("title", feed_url),
                    })
        except Exception as e:
            print(f"[RSS] {feed_url} 오류: {e}")

    return articles[:10]


# ── Amazon Best Sellers (공개 페이지) ──────────────────────
def fetch_amazon_bestsellers() -> list:
    """Amazon K-beauty 베스트셀러 공개 페이지 파싱"""
    url = "https://www.amazon.com/Best-Sellers-Beauty-Korean-Skin-Care/zgbs/beauty/10528509011"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    products = []
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("div.zg-grid-general-faceout")[:10]
        for i, item in enumerate(items, 1):
            name_el  = item.select_one("div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1") or \
                       item.select_one("span.a-size-small")
            price_el = item.select_one("span.p13n-sc-price")
            name  = name_el.text.strip()  if name_el  else "N/A"
            price = price_el.text.strip() if price_el else "N/A"
            products.append({"rank": i, "name": name, "price": price, "platform": "Amazon US"})
    except Exception as e:
        print(f"[Amazon] 오류: {e}")

    return products


# ── 전체 수집 실행 ─────────────────────────────────────────
def collect_all(reddit_id: str, reddit_secret: str, reddit_agent: str) -> dict:
    print("=== K-Beauty Pulse 데이터 수집 시작 ===")
    data = {
        "collected_at": datetime.datetime.utcnow().isoformat(),
        "week":         datetime.datetime.utcnow().strftime("Week %W · %b %d, %Y"),
        "trends":       {},
        "reddit":       [],
        "news":         [],
        "amazon_top":   [],
    }

    # 1. Google Trends (지역별)
    print("→ Google Trends 수집 중...")
    for region_key in REGIONS:
        print(f"   {region_key}...")
        data["trends"][region_key] = fetch_google_trends(region_key)
        time.sleep(3)  # API 과부하 방지

    # 2. Reddit
    print("→ Reddit 수집 중...")
    data["reddit"] = fetch_reddit(reddit_id, reddit_secret, reddit_agent)

    # 3. RSS 뉴스
    print("→ RSS 뉴스 수집 중...")
    data["news"] = fetch_rss_news()

    # 4. Amazon 베스트셀러
    print("→ Amazon 베스트셀러 수집 중...")
    data["amazon_top"] = fetch_amazon_bestsellers()

    # JSON 저장 (analyzer.py에서 읽어감)
    with open("data/weekly_raw.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("=== 수집 완료 → data/weekly_raw.json 저장 ===")
    return data


if __name__ == "__main__":
    import os
    collect_all(
        reddit_id     = os.environ["REDDIT_CLIENT_ID"],
        reddit_secret = os.environ["REDDIT_CLIENT_SECRET"],
        reddit_agent  = "kbeauty-pulse/1.0",
    )
