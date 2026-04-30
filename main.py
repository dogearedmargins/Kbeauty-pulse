"""
K-Beauty Pulse — main.py
전체 파이프라인: 수집 → 분석 → 발송
"""

import os
from scraper  import collect_all
from analyzer import analyze
from emailer  import send_email


def run():
    print("\n" + "="*50)
    print(" K-Beauty Pulse 위클리 파이프라인 시작")
    print("="*50 + "\n")

    os.makedirs("data", exist_ok=True)

    print("[1/3] 데이터 수집 중...\n")
    raw = collect_all()

    print("\n[2/3] Groq AI 분석 중...\n")
    analysis = analyze(raw)

    print("\n[3/3] 이메일 발송 중...\n")
    send_email(analysis)

    print("\n" + "="*50)
    print(" 완료! → dogearedmargins@gmail.com 발송됨")
    print("="*50 + "\n")


if __name__ == "__main__":
    run()
