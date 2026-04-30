"""
K-Beauty Pulse — analyzer.py
Groq API (llama3-70b, 완전 무료) 로 수집 데이터 분석
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
    """지역별 분석 프롬프트 생성"""
    meta    = REGIONS_META[region_key]
    trends  = raw["trends"].get(region_key, {})
    reddit  = raw["reddit"][:5]
    news    = raw["news"][:5]

    # 트렌드 데이터 텍스트 변환
    trend_lines = []
    for kw, vals in trends.items():
        arrow = "▲" if vals.get("trend") == "up" else "▼"
        trend_lines.append(
            f"  - {kw}: 현재 {vals.get('current', 0)}/100 "
            f"(7일 평균 {vals.get('avg_7d', 0)}) {arrow}"
        )

    reddit_lines = [f"  - [{r['subreddit']}] {r['title']} (점수:{r['score']})" for r in reddit[:3]]
    news_lines   = [f"  - {n['source']}: {n['title']}" for n in news[:3]]

    prompt = f"""당신은 K-Beauty 글로벌 B2B 마케팅 전문가입니다.
아래 실시간 데이터를 분석하여 {meta['label']} 지역 마케터가 이번 주 바로 활용할 수 있는 인사이트를 작성해주세요.

[지역] {meta['label']}
[주요 채널] {meta['platform']}

[Google Trends 이번 주 검색량 (0-100 지수)]
{chr(10).join(trend_lines) if trend_lines else "  - 데이터 없음"}

[Reddit 트렌딩 포스트]
{chr(10).join(reddit_lines) if reddit_lines else "  - 데이터 없음"}

[최신 뉴스]
{chr(10).join(news_lines) if news_lines else "  - 데이터 없음"}

다음 형식으로 JSON만 출력해주세요 (다른 텍스트 없이):
{{
  "wow_change": "+X% WoW (추정치)",
  "headline": "이번 주 핵심 한 줄 요약 (50자 이내)",
  "insight": "마케터용 2-3문장 인사이트. 구체적인 제품명/채널명 포함.",
  "top_keywords": ["키워드1", "키워드2", "키워드3"],
  "action": "이번 주 바로 실행할 수 있는 액션 1가지 (1문장)"
}}"""
    return prompt


def build_global_signal_prompt(region_analyses: dict, raw: dict) -> str:
    """전체 글로벌 시그널 프롬프트"""
    summaries = []
    for rk, analysis in region_analyses.items():
        summaries.append(f"[{REGIONS_META[rk]['label']}] {analysis.get('headline', '')}")

    amazon_top3 = raw.get("amazon_top", [])[:3]
    amazon_lines = [f"  #{p['rank']} {p['name']}" for p in amazon_top3]

    prompt = f"""K-Beauty 글로벌 마케팅 전문가로서, 이번 주 5개 지역 트렌드를 종합하여
마케터가 즉시 활용할 수 있는 글로벌 시그널 3개를 도출해주세요.

[지역별 요약]
{chr(10).join(summaries)}

[Amazon US 베스트셀러 TOP3]
{chr(10).join(amazon_lines) if amazon_lines else "  - 데이터 없음"}

다음 형식으로 JSON만 출력해주세요:
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
    """Groq API 호출 (llama3-70b, 무료)"""
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        raw_text = completion.choices[0].message.content.strip()

        # JSON 파싱
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"[Groq] JSON 파싱 실패: {e}\n응답: {raw_text[:200]}")
        return {}
    except Exception as e:
        print(f"[Groq] API 오류: {e}")
        return {}


def analyze(raw: dict) -> dict:
    """전체 분석 실행"""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    print("=== Groq 분석 시작 ===")
    result = {
        "week":            raw.get("week", ""),
        "collected_at":    raw.get("collected_at", ""),
        "region_analyses": {},
        "global":          {},
    }

    # 1. 지역별 분석
    for region_key in REGIONS_META:
        print(f"→ {REGIONS_META[region_key]['label']} 분석 중...")
        prompt   = build_region_prompt(region_key, raw)
        analysis = call_groq(client, prompt)

        # fallback 기본값
        result["region_analyses"][region_key] = {
            "wow_change":    analysis.get("wow_change", "N/A"),
            "headline":      analysis.get("headline", ""),
            "insight":       analysis.get("insight", "데이터 분석 중"),
            "top_keywords":  analysis.get("top_keywords", []),
            "action":        analysis.get("action", ""),
        }

    # 2. 글로벌 시그널
    print("→ 글로벌 시그널 분석 중...")
    global_prompt  = build_global_signal_prompt(result["region_analyses"], raw)
    global_result  = call_groq(client, global_prompt)

    result["global"] = {
        "alert":      global_result.get("alert", ""),
        "signals":    global_result.get("signals", []),
        "global_top5": global_result.get("global_top5", []),
    }

    # 저장
    os.makedirs("data", exist_ok=True)
    with open("data/weekly_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=== 분석 완료 → data/weekly_analysis.json 저장 ===")
    return result


if __name__ == "__main__":
    with open("data/weekly_raw.json", encoding="utf-8") as f:
        raw = json.load(f)
    analyze(raw)
