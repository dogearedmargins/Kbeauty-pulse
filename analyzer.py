"""
K-Beauty Pulse — analyzer.py
requests로 Groq API 직접 호출 (groq 라이브러리 미사용)
"""

import json
import os
import requests

REGIONS_META = {
    "americas": {"label": "Americas",       "platform": "Amazon / TikTok Shop"},
    "europe":   {"label": "Europe",         "platform": "Lookfantastic / Boots"},
    "sea":      {"label": "Southeast Asia", "platform": "Shopee / TikTok Shop"},
    "mideast":  {"label": "Middle East",    "platform": "Noon / Sephora ME"},
    "india":    {"label": "India",          "platform": "Nykaa / Myntra"},
}

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def call_groq(prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {os.environ['GROQ_API_KEY'].strip()}",
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        raw_text = resp.json()["choices"][0]["message"]["content"].strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"[Groq] 오류: {e}")
        return {}


def build_region_prompt(region_key: str, raw: dict) -> str:
    meta        = REGIONS_META[region_key]
    region_data = raw["trends"].get(region_key, {})
    news        = raw["news"][:5]
    discovered  = region_data.get("discovered_keywords", [])
    volumes     = region_data.get("search_volumes", {})
    if not discovered and not volumes:
        volumes = region_data

    rising_lines = [f"- {d['keyword']} (급상승 {d['value']}%)"
                    for d in discovered if d.get("type") == "rising"][:8]
    vol_lines    = [f"- {k} (검색지수 {v.get('current', 0)}/100)"
                    for k, v in list(volumes.items())[:5]]
    news_lines   = [f"- {n['source']}: {n['title']}" for n in news[:3]]

    kw_section = "\n".join(rising_lines) if rising_lines else \
                 "\n".join(vol_lines)    if vol_lines    else "데이터 수집 중"
    news_section = "\n".join(news_lines) if news_lines else "데이터 없음"

    return (
        f"당신은 K-Beauty 글로벌 B2B 마케팅 전문가입니다.\n"
        f"지역: {meta['label']}, 채널: {meta['platform']}\n\n"
        f"[이번 주 트렌딩 키워드]\n{kw_section}\n\n"
        f"[최신 뉴스]\n{news_section}\n\n"
        f"아래 JSON 형식으로만 답하세요. 다른 텍스트 없이.\n"
        f'{{"wow_change":"+X% WoW","headline":"핵심 요약 50자 이내",'
        f'"insight":"마케터용 2문장 인사이트",'
        f'"top_keywords":["키워드1","키워드2","키워드3"],'
        f'"action":"이번 주 실행 액션 1가지"}}'
    )


def build_global_signal_prompt(region_analyses: dict, raw: dict) -> str:
    summaries    = [f"{REGIONS_META[rk]['label']}: {a.get('headline', '')}"
                    for rk, a in region_analyses.items()]
    amazon_lines = [f"#{p['rank']} {p['name']}"
                    for p in raw.get("amazon_top", [])[:3]]

    return (
        f"K-Beauty 글로벌 마케팅 전문가로서 5개 지역 트렌드를 종합해 시그널 3개를 도출하세요.\n\n"
        f"[지역별 요약]\n" + "\n".join(summaries) + "\n\n"
        f"[Amazon TOP3]\n" + ("\n".join(amazon_lines) if amazon_lines else "없음") + "\n\n"
        f"아래 JSON 형식으로만 답하세요. 다른 텍스트 없이.\n"
        f'{{"alert":"글로벌 시그널 1문장",'
        f'"signals":['
        f'{{"icon":"up","title":"제목","text":"액션포인트"}},'
        f'{{"icon":"sun","title":"제목","text":"액션포인트"}},'
        f'{{"icon":"arrow","title":"제목","text":"액션포인트"}}],'
        f'"global_top5":['
        f'{{"rank":1,"product":"제품명","brand":"브랜드","region":"지역"}},'
        f'{{"rank":2,"product":"제품명","brand":"브랜드","region":"지역"}},'
        f'{{"rank":3,"product":"제품명","brand":"브랜드","region":"지역"}},'
        f'{{"rank":4,"product":"제품명","brand":"브랜드","region":"지역"}},'
        f'{{"rank":5,"product":"제품명","brand":"브랜드","region":"지역"}}]}}'
    )


def analyze(raw: dict) -> dict:
    print("=== Groq 분석 시작 ===")
    result = {
        "week":            raw.get("week", ""),
        "collected_at":    raw.get("collected_at", ""),
        "region_analyses": {},
        "global":          {},
    }

    for region_key in REGIONS_META:
        print(f"-> {REGIONS_META[region_key]['label']} 분석 중...")
        analysis = call_groq(build_region_prompt(region_key, raw))
        result["region_analyses"][region_key] = {
            "wow_change":   analysis.get("wow_change", "N/A"),
            "headline":     analysis.get("headline", ""),
            "insight":      analysis.get("insight", "데이터 분석 중"),
            "top_keywords": analysis.get("top_keywords", []),
            "action":       analysis.get("action", ""),
        }

    print("-> 글로벌 시그널 분석 중...")
    g = call_groq(build_global_signal_prompt(result["region_analyses"], raw))
    result["global"] = {
        "alert":       g.get("alert", ""),
        "signals":     g.get("signals", []),
        "global_top5": g.get("global_top5", []),
    }

    os.makedirs("data", exist_ok=True)
    with open("data/weekly_analysis.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("=== 분석 완료 ===")
    return result


if __name__ == "__main__":
    with open("data/weekly_raw.json", encoding="utf-8") as f:
        raw = json.load(f)
    analyze(raw)
