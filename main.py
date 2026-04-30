"""
K-Beauty Pulse — main.py
전체 파이프라인 실행: 수집 → 분석 → 발송
GitHub Actions에서 이 파일 하나만 실행하면 끝
"""

import os
import json
from scraper  import collect_all
from analyzer import analyze
from emailer  import send_email


def run():
    print("\n" + "="*50)
    print(" K-Beauty Pulse 위클리 파이프라인 시작")
    print("="*50 + "\n")

    os.makedirs("data", exist_ok=True)

    # STEP 1 — 데이터 수집
    print("[1/3] 데이터 수집 중...\n")
    raw = collect_all(
        reddit_id     = os.environ["REDDIT_CLIENT_ID"],
        reddit_secret = os.environ["REDDIT_CLIENT_SECRET"],
        reddit_agent  = "kbeauty-pulse/1.0 by dogearedmargins",
    )

    # STEP 2 — AI 분석
    print("\n[2/3] Groq AI 분석 중...\n")
    analysis = analyze(raw)

    # STEP 3 — 이메일 발송
    print("\n[3/3] 이메일 발송 중...\n")
    send_email(analysis)

    print("\n" + "="*50)
    print(" 완료! 이메일이 dogearedmargins@gmail.com으로 발송됨")
    print("="*50 + "\n")


if __name__ == "__main__":
    run()
