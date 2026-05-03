"""
K-Beauty Pulse — scraper.py
데이터 수집: Google Trends (related_queries 실시간 발굴) + RSS + Amazon
고정 키워드 없이 매주 자동으로 트렌딩 키워드 발굴
"""

import json
import time
import datetime
import os
import feedparser
import requests
from pytrends.request import TrendReq

# ── 지역 시드 키워드 (발굴의 출발점 — 최소한만 고정) ──────
# 이 키워드로 related_queries를 당겨서 실시간 트렌딩 키워드를 자동 발굴
REGION_SEEDS = {
    "americas": {"label": "Americas", "geo": "US", "platform": "Amazon / TikTok Shop",
                 "seeds": ["korean skincare", "k-beauty"]},
    "europe":   {"label": "Europe",   "geo": "GB", "platform": "Lookfantastic / Boots",
                 "seeds": ["korean skincare", "k-beauty"]},
    "sea":      {"label": "Southeast Asia", "geo": "SG", "platform": "Shopee / TikTok Shop",
                 "seeds": ["korean skincare", "k beauty"]},
    "mideast":  {"label": "Middle East",    "geo": "AE", "platform": "Noon / Sephora ME",
                 "seeds": ["korean skincare", "k beauty"]},
    "india":    {"label": "India",    "geo": "IN", "platform": "Nykaa / Myntra",
                 "seeds": ["korean skincare", "k-beauty"]},
}

BEAUTYMATTER_RSS = "https://beautymatter.com/feed/"
COSMETICSBIZ_RSS = "https://cosmeticsbusiness.com/rss"


# ── 실시간 트렌딩 키워드 발굴 ──────────────────────────────
def discover_trending_keywords(geo: str, seeds: list) -> list:
    """
    시드 키워드의 related_queries에서 급상승 키워드를 자동 추출
    → 매주 실행마다 다른 실시간 트렌딩 키워드가 나옴
    """
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    discovered = []

    for seed in seeds:
        try:
            pytrends.build_payload(
                [seed],
                cat=44,          # 44 = Beauty & Fitness 카테고리
                timeframe="now 7-d",
                geo=geo,
                gprop="",
            )
            related = pytrends.related_queries()

            if seed in related and related[seed]:
                # 급상승(rising) 키워드 우선 추출
                rising_df = related[seed].get("rising")
                top_df    = related[seed].get("top")

                if rising_df is not None and not rising_df.empty:
                    for _, row in rising_df.head(8).iterrows():
                        kw = str(row["query"]).strip()
                        if len(kw) > 2:
                            discovered.append({
                                "keyword": kw,
                                "value":   int(row["value"]),
                                "type":    "rising",  # 급상승
                            })

                if top_df is not None and not top_df.empty:
                    for _, row in top_df.head(5).iterrows():
                        kw = str(row["query"]).strip()
                        if len(kw) > 2:
                            discovered.append({
                                "keyword": kw,
                                "value":   int(row["value"]),
                                "type":    "top",     # 인기
                            })

            time.sleep(5)  # rate limit 방지

        except Exception as e:
            print(f"[Discovery] {geo} / {seed} 오류: {e}")
            time.sleep(8)

    # 중복 제거 + 급상승 우선 정렬
    seen = set()
    unique = []
    for item in sorted(discovered, key=lambda x: (x["type"] == "top", -x["value"])):
        if item["keyword"] not in seen:
            seen.add(item["keyword"])
            unique.append(item)

    return unique[:15]  # 상위 15개


# ── 발굴된 키워드 검색량 측정 ──────────────────────────────
def fetch_trends_for_keywords(keywords: list, geo: str) -> dict:
    """발굴된 키워드들의 실제 검색량 지수 측정"""
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    results = {}

    # 5개씩 묶어서 요청 (pytrends 최대 5개 제한)
    kw_names = [k["keyword"] for k in keywords[:10]]
    chunks = [kw_names[i:i+5] for i in range(0, len(kw_names), 5)]

    for chunk in chunks:
        try:
            pytrends.build_payload(
                chunk,
                cat=44,
                timeframe="now 7-d",
                geo=geo,
                gprop="",
            )
            df = pytrends.interest_over_time()

            if not df.empty:
                for kw in chunk:
                    if kw in df.columns:
                        results[kw] = {
                            "current": int(df[kw].iloc[-1]),
                            "avg_7d":  int(df[kw].mean()),
                            "peak":    int(df[kw].max()),
                            "trend":   "up" if df[kw].iloc[-1] > df[kw].mean() else "down",
                        }
            time.sleep(8)

        except Exception as e:
            print(f"[Trends] 측정 오류: {e}")
            time.sleep(10)

    return results


# ── RSS 뉴스 ───────────────────────────────────────────────
def fetch_rss_news() -> list:
    articles = []
    for feed_url in [BEAUTYMATTER_RSS, COSMETICSBIZ_RSS]:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "")
                if any(kw in title.lower() for kw in [
                    "k-beauty", "korean", "kbeauty", "cosrx", "laneige",
                    "beauty of joseon", "anua", "medicube", "innisfree",
                    "scinic", "skincare", "ingredient", "serum", "sunscreen"
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


# ── Amazon 베스트셀러 ──────────────────────────────────────
def fetch_amazon_bestsellers() -> list:
    url = "https://www.amazon.com/Best-Sellers-Beauty-Korean-Skin-Care/zgbs/beauty/10528509011"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
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
            products.append({
                "rank":     i,
                "name":     name_el.text.strip()  if name_el  else "N/A",
                "price":    price_el.text.strip() if price_el else "N/A",
                "platform": "Amazon US",
            })
    except Exception as e:
        print(f"[Amazon] 오류: {e}")
    return products


# ── 전체 수집 실행 ─────────────────────────────────────────
def collect_all() -> dict:
    print("=== K-Beauty Pulse 데이터 수집 시작 ===")
    data = {
        "collected_at": datetime.datetime.utcnow().isoformat(),
        "week":         datetime.datetime.utcnow().strftime("Week %W · %b %d, %Y"),
        "trends":       {},
        "news":         [],
        "amazon_top":   [],
    }

    print("→ 실시간 트렌딩 키워드 발굴 + 검색량 측정 중...")
    for region_key, region in REGION_SEEDS.items():
        print(f"   [{region['label']}] 키워드 발굴 중...")

        # 1단계: 실시간 키워드 발굴
        discovered = discover_trending_keywords(region["geo"], region["seeds"])
        print(f"   → {len(discovered)}개 키워드 발굴: {[d['keyword'] for d in discovered[:5]]}")

        # 2단계: 발굴된 키워드 검색량 측정
        search_volumes = fetch_trends_for_keywords(discovered, region["geo"])

        data["trends"][region_key] = {
            "discovered_keywords": discovered,   # 발굴된 키워드 전체
            "search_volumes":      search_volumes,  # 검색량 측정값
            "platform":            region["platform"],
        }
        time.sleep(10)  # 지역 간 대기

    print("→ RSS 뉴스 수집 중...")
    data["news"] = fetch_rss_news()

    print("→ Amazon 베스트셀러 수집 중...")
    data["amazon_top"] = fetch_amazon_bestsellers()

    os.makedirs("data", exist_ok=True)
    with open("data/weekly_raw.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("=== 수집 완료 → data/weekly_raw.json 저장 ===")
    return data


if __name__ == "__main__":
    collect_all()
