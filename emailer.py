"""
K-Beauty Pulse — emailer.py
Gmail SMTP로 HTML 이메일 자동 발송 (완전 무료)
"""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RECIPIENT   = "dogearedmargins@gmail.com"
SENDER_NAME = "K-Beauty Pulse"

REGION_COLORS = {
    "americas": {"bg": "#F0F4FB", "kw_bg": "#dce8f8", "kw_color": "#1a4a8a", "delta_bg": "#dce8f8", "delta_color": "#1a4a8a"},
    "europe":   {"bg": "#F5F0FA", "kw_bg": "#ede8f8", "kw_color": "#4a2a8a", "delta_bg": "#ede8f8", "delta_color": "#4a2a8a"},
    "sea":      {"bg": "#F0F8F2", "kw_bg": "#dcf0e8", "kw_color": "#1a5a3a", "delta_bg": "#dcf0e8", "delta_color": "#1a5a3a"},
    "mideast":  {"bg": "#FBF5EC", "kw_bg": "#f8f0dc", "kw_color": "#7a5a1a", "delta_bg": "#f8f0dc", "delta_color": "#7a5a1a"},
    "india":    {"bg": "#FBF0F0", "kw_bg": "#f8e8e8", "kw_color": "#8a2a2a", "delta_bg": "#f8e8e8", "delta_color": "#8a2a2a"},
}

REGION_LABELS = {
    "americas": "Americas",
    "europe":   "Europe",
    "sea":      "Southeast Asia",
    "mideast":  "Middle East",
    "india":    "India",
}


def build_html(analysis: dict) -> str:
    week      = analysis.get("week", "")
    regions   = analysis.get("region_analyses", {})
    glb       = analysis.get("global", {})
    alert     = glb.get("alert", "")
    signals   = glb.get("signals", [])
    top5      = glb.get("global_top5", [])

    # ── 지역 카드 HTML ────────────────────────────────────
    region_cards_html = ""
    region_keys = list(REGION_LABELS.keys())

    for i, rk in enumerate(region_keys):
        data   = regions.get(rk, {})
        c      = REGION_COLORS[rk]
        label  = REGION_LABELS[rk]
        wow    = data.get("wow_change", "")
        insight = data.get("insight", "")
        kws    = data.get("top_keywords", [])

        kw_pills = "".join([
            f'<span style="font-size:10px;padding:2px 7px;border-radius:8px;'
            f'background:{c["kw_bg"]};color:{c["kw_color"]};font-weight:500;'
            f'margin-right:4px;margin-bottom:4px;display:inline-block">{kw}</span>'
            for kw in kws
        ])

        # India는 full-width
        width_style = 'width:100%;' if rk == 'india' else 'width:47%;'

        region_cards_html += f"""
        <div style="{width_style}background:{c['bg']};border-radius:10px;
             padding:14px;border:0.5px solid rgba(71,88,92,0.12);
             margin-bottom:12px;vertical-align:top;display:inline-block;
             box-sizing:border-box">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
            <span style="font-size:11px;font-weight:600;color:#2a2e2f">{label}</span>
            <span style="font-size:10px;font-weight:600;padding:2px 7px;border-radius:8px;
                  background:{c['delta_bg']};color:{c['delta_color']}">{wow}</span>
          </div>
          <p style="font-size:12px;color:#47585C;line-height:1.55;margin:0 0 8px">{insight}</p>
          <div>{kw_pills}</div>
        </div>
        {'&nbsp;&nbsp;' if i % 2 == 0 and rk != 'india' else ''}
        """

    # ── TOP 5 베스트셀러 HTML ─────────────────────────────
    top5_html = ""
    for p in top5:
        top5_html += f"""
        <tr>
          <td style="padding:8px 0;border-bottom:0.5px solid rgba(71,88,92,0.08);width:24px;
                font-size:11px;font-weight:600;color:#4D80E6">#{p.get('rank','')}</td>
          <td style="padding:8px 0;border-bottom:0.5px solid rgba(71,88,92,0.08)">
            <div style="font-size:12px;font-weight:500;color:#2a2e2f">{p.get('product','')}</div>
            <div style="font-size:10px;color:#80989B">{p.get('brand','')}</div>
          </td>
          <td style="padding:8px 0;border-bottom:0.5px solid rgba(71,88,92,0.08);
                text-align:right;vertical-align:middle">
            <span style="font-size:10px;padding:2px 6px;border-radius:6px;
                  background:#F0F4FB;color:#4D80E6">{p.get('region','')}</span>
          </td>
        </tr>"""

    # ── AI 시그널 HTML ─────────────────────────────────────
    signals_html = ""
    for s in signals:
        signals_html += f"""
        <tr>
          <td style="padding:6px 0;vertical-align:top;width:20px;color:#C8D5B0;font-size:13px">{s.get('icon','→')}</td>
          <td style="padding:6px 0;padding-left:8px">
            <span style="font-size:12px;color:#ffffff;font-weight:500">{s.get('title','')} — </span>
            <span style="font-size:12px;color:rgba(255,255,255,0.75)">{s.get('text','')}</span>
          </td>
        </tr>"""

    # ── 전체 HTML 조립 ────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>K-Beauty Pulse Weekly Report</title>
</head>
<body style="margin:0;padding:20px;background:#F5F3F0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">

<div style="max-width:620px;margin:0 auto;background:#ffffff;border-radius:12px;
     overflow:hidden;border:0.5px solid rgba(71,88,92,0.15)">

  <!-- HEADER -->
  <div style="background:#2a2e2f;padding:28px 32px 24px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:8px">
        <table cellpadding="0" cellspacing="2" style="width:24px;height:24px">
          <tr>
            <td style="background:#4D80E6;border-radius:2px;width:11px;height:11px"></td>
            <td style="background:#C8D5B0;border-radius:2px;width:11px;height:11px"></td>
          </tr>
          <tr>
            <td style="background:#C8D5B0;border-radius:2px;width:11px;height:11px"></td>
            <td style="background:#80989B;border-radius:2px;width:11px;height:11px"></td>
          </tr>
        </table>
        <span style="font-size:13px;font-weight:500;color:#ffffff;letter-spacing:.02em">K-Beauty Pulse</span>
      </div>
      <span style="font-size:10px;padding:3px 10px;border-radius:10px;
            background:rgba(200,213,176,0.2);color:#C8D5B0;
            border:0.5px solid rgba(200,213,176,0.3)">{week}</span>
    </div>
    <h1 style="font-size:24px;font-weight:500;color:#ffffff;line-height:1.25;margin:0 0 8px">
      이번 주 글로벌<br>K-Beauty 트렌드 리포트
    </h1>
    <p style="font-size:12px;color:rgba(255,255,255,0.5);margin:0;line-height:1.5">
      5개 지역 · 실시간 데이터 기반 · Google Trends + Reddit + Amazon + BeautyMatter
    </p>
  </div>

  <!-- ALERT BAR -->
  <div style="background:#C8D5B0;padding:10px 32px;display:flex;align-items:center;gap:8px">
    <div style="width:7px;height:7px;border-radius:50%;background:#3a5a2a;flex-shrink:0"></div>
    <span style="font-size:12px;color:#3a5a2a;font-weight:500">{alert}</span>
  </div>

  <!-- BODY -->
  <div style="padding:28px 32px">

    <!-- 지역별 인사이트 -->
    <p style="font-size:10px;font-weight:600;color:#80989B;text-transform:uppercase;
         letter-spacing:.08em;margin:0 0 12px">지역별 주간 인사이트</p>
    <div style="font-size:0">
      {region_cards_html}
    </div>

    <!-- 구분선 -->
    <div style="height:0.5px;background:rgba(71,88,92,0.1);margin:4px 0 20px"></div>

    <!-- 글로벌 베스트셀러 TOP5 -->
    <p style="font-size:10px;font-weight:600;color:#80989B;text-transform:uppercase;
         letter-spacing:.08em;margin:0 0 12px">이번 주 글로벌 베스트셀러 TOP 5</p>
    <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
      {top5_html}
    </table>

    <!-- AI 시그널 -->
    <div style="background:#2a2e2f;border-radius:10px;padding:16px 18px;margin-bottom:24px">
      <p style="font-size:11px;font-weight:600;color:#C8D5B0;text-transform:uppercase;
           letter-spacing:.06em;margin:0 0 10px;display:flex;align-items:center;gap:6px">
        <span style="width:6px;height:6px;border-radius:50%;background:#C8D5B0;display:inline-block"></span>
        AI Signal — 이번 주 마케터 액션 포인트
      </p>
      <table style="width:100%;border-collapse:collapse">
        {signals_html}
      </table>
    </div>

    <!-- 출처 -->
    <p style="font-size:11px;color:#80989B;line-height:1.7;margin:0">
      데이터 출처: Google Trends · Reddit r/AsianBeauty · Amazon US Best Sellers · BeautyMatter RSS<br>
      분석: Groq API (llama3-70b) · 매주 월요일 오전 9시 자동 수집 및 발송
    </p>

  </div>

  <!-- FOOTER -->
  <div style="background:#F5F3F0;padding:16px 32px;display:flex;
       align-items:center;justify-content:space-between">
    <p style="font-size:10px;color:#80989B;line-height:1.6;margin:0">
      K-Beauty Pulse · dogearedmargins@gmail.com<br>
      GitHub Actions 자동 발송 · 매주 월요일 오전 9시
    </p>
    <span style="font-size:10px;color:#C8D5B0;font-weight:500">Auto Report</span>
  </div>

</div>
</body></html>"""

    return html


def send_email(analysis: dict) -> None:
    """Gmail SMTP로 발송"""
    sender_email = os.environ["GMAIL_ADDRESS"]
    app_password = "".join(c for c in os.environ["GMAIL_APP_PASSWORD"] if c.isascii()).strip().replace(" ", "")
    week         = analysis.get("week", "K-Beauty Weekly Report")

    html_content = build_html(analysis)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"K-Beauty Pulse — {week}"
    msg["From"]    = f"{SENDER_NAME} <{sender_email}>"
    msg["To"]      = RECIPIENT

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, RECIPIENT, msg.as_string())
        print(f"=== 이메일 발송 완료 → {RECIPIENT} ===")
    except Exception as e:
        print(f"[Email] 발송 실패: {e}")
        raise


if __name__ == "__main__":
    with open("data/weekly_analysis.json", encoding="utf-8") as f:
        analysis = json.load(f)
    send_email(analysis)
