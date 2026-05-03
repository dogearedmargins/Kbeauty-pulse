"""
K-Beauty Pulse — analyzer.py
Groq API (llama3-70b, 완전 무료) 로 수집 데이터 분석
related_queries로 발굴된 실시간 키워드 기반
"""

import json
import os
from groq import Groq

REGIONS_META = {
    "americas": {"label": "Americas",       "platform": "Amazon / TikTok Shop"},
    "europe":   {"label": "Europe",         "platform": "Lookfantastic / Boots"},
    "sea":      {"label": "Southeast Asia", "platform": "Shopee / TikTok Shop"},
    "mideast":  {"label": "Middle East",    "platform": "Noon / Sephora ME"},
    "india":    {"label": "India",          "platform": "Nykaa / Myntra"},
}


def build_region_prompt(region_key: str, raw: dict) -> str:
    meta   = REGIONS_META[region_key]
    region_data = raw["trends"].get(region_key, {})
    news   = raw["news"][:5]

    # 발굴된 키워드 정리
    discovered = region_data.get("discovered_keywords", [])
    volumes    = region_data.get("search_volumes", {})

    rising_kws = [d for d in discovered if d["type"] == "rising"][:8]
    top_kws    = [d for d in discovered if d["type"] == "top"][:5]

    rising_lines = [f"  - 🔥 {d['keyword']} (급상승 {d['value']}%)" for d in rising_kws]
    top_lines    = [f"  - ⭐ {k} (검색지수 {v.get('current',0)}/100, 추세:{v.get('trend','')})"
                    for k, v in list(volumes.items())[:5]]
    news_lines   = [f"  - {n['source']}: {n['title']}" for n in news[:3]]

    prompt = f"""당신은 K-Beauty 글로벌 B2B 마케팅 전문가입니다.
아래 이번 주 실시간으로 발굴된 트렌딩 키워드 데이터를 분석하여
{meta['label']} 지역 마케터가 바로 활용할 수 있는 인사이트를 작성하세요.

[지역] {meta['label']}
[주요 채널] {meta['platform']}

[이번 주 급상승 키워드 (Google Trends related_queries 실시간 발굴)]
{chr(10).join(rising_lines) if rising_lines else "  - 데이터 수집 중"}

[인기 키워드 검색량]
{chr(10).join(top_lines) if top_lines else "  - 데이터 수집 중"}

[최신 뉴스]
{chr(10).join(news_lines) if news_lines else "  - 데이터 없음"}

다음 형식으로 JSON만 출력 (다른 텍스트 없이):
{{
  "wow_change": "+X% WoW (추정치)",
  "headline": "이번 주 핵심 한 줄 요약 (50자 이내)",
  "insight": "마케터용 2-3문장. 급상승 키워드 중 주목할 브랜드/성분명 구체적으로 언급.",
  "top_keywords": ["급상승키워드1", "급상승키워드2", "급상승키워드3"],
  "action": "이번 주 바로 실행할 액션 1가지 (1문장)"
}}"""
    return prompt


def build_global_signal_prompt(region_analyses: dict, raw: dict) -> str:
    summaries = [f"[{REGIONS_META[rk]['label']}] {a.get('headline', '')}"
                 for rk, a in region_analyses.items()]
    amazon_lines = [f"  #{p['rank']} {p['name']}" for p in raw.get("amazon_top", [])[:3]]

    prompt = f"""K-Beauty 글로벌 마케팅 전문가로서, 이번 주 5개 지역 실시간 트렌드를 종합하여
마케터가 즉시 활용할 수 있는 글로벌 시그널 3개를 도출하세요.

[지역별 요약]
{chr(10).join(summaries)}

[Amazon US 베스트셀러 TOP3]
{chr(10).join(amazon_lines) if amazon_lines else "  - 데이터 없음"}

다음 형식으로 JSON만 출력:
{{
  "alert": "이번 주 가장 주목할 글로벌 시그널 (1문장, 수치 포함)",
  "signals": [
    {{"icon": "↑", "title": "시그널 제목", "text": "구체적 액션 포인트"}},
    {{"icon": "☀", "title": "시그널 제목", "text": "구체적 액션 포인트"}},
    {{"icon": "→", "title": "시그널 제목", "text": "구체적 액션 포인트"}}
  ],
  "global_top5": [
    {{"rank": 1, "product": "제품명", "brand": "브랜드", "region": "지역"}},
    {{"rank": 2, "product": "제품명", "brand": "브랜드", "region": "지역"}},
    {{"rank": 3, "product": "제품명", "brand": "브랜드", "region": "지역"}},
    {{"rank": 4, "product": "제품명", "brand": "브랜드", "region": "지역"}},
    {{"rank": 5, "product": "제품명", "brand": "브랜드", "region": "지역"}}
  ]
}}"""
    return prompt


def call_groq(client: Groq, prompt: str) -> dict:
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        raw_text = completion.choices[0].message.content.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"[Groq] 오류: {e}")
        return {}


def analyze(raw: dict) -> dict:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    print("=== Groq 분석 시작 ===")

    result = {
        "week":            raw.get("week", ""),
        "collected_at":    raw.get("collected_at", ""),
        "region_analyses": {},
        "global":          {},
    }

    for region_key in REGIONS_META:
        print(f"→ {REGIONS_META[region_key]['label']} 분석 중...")
        analysis = call_groq(client, build_region_prompt(region_key, raw))
        result["region_analyses"][region_key] = {
            "wow_change":   analysis.get("wow_change", "N/A"),
            "headline":     analysis.get("headline", ""),
            "insight":      analysis.get("insight", "데이터 분석 중"),
            "top_keywords": analysis.get("top_keywords", []),
            "action":       analysis.get("action", ""),
        }

    print("→ 글로벌 시그널 분석 중...")
    global_result = call_groq(client, build_global_signal_prompt(result["region_analyses"], raw))
    result["global"] = {
        "alert":       global_result.get("alert", ""),
        "signals":     global_result.get("signals", []),
        "global_top5": global_result.get("global_top5", []),
    }

    os.makedirs("data", exist_ok=True)
    with open("data/weekly_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=== 분석 완료 → data/weekly_analysis.json 저장 ===")
    return result


if __name__ == "__main__":
    with open("data/weekly_raw.json", encoding="utf-8") as f:
        raw = json.load(f)
    analyze(raw)
