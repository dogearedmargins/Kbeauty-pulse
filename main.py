"""
K-Beauty Pulse — main.py
data.json을 읽어서 HTML 이메일로 발송
"""

import os
import json
from emailer import send_email

def run():
    print("\n" + "="*50)
    print(" K-Beauty Pulse 위클리 이메일 발송 시작")
    print("="*50 + "\n")

    # data.json 로드
    data_path = os.path.join(os.path.dirname(__file__), "data.json")
    print(f"[1/2] data.json 로드 중... ({data_path})")
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    # 이메일 발송
    print("[2/2] 이메일 발송 중...\n")
    send_email(data)

    print("\n" + "="*50)
    print(" 완료! 이메일이 발송되었습니다.")
    print("="*50 + "\n")


if __name__ == "__main__":
    run()
