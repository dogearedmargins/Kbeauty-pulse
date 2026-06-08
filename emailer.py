"""
K-Beauty Pulse — emailer.py
data.json 기반 간결한 주간 리포트 이메일
"""

import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RECIPIENT   = "dogearedmargins@gmail.com"
SENDER_NAME = "K-Beauty Pulse"

REGION_LABELS = {
    "americas": "Americas",
    "europe":   "Europe",
    "sea":      "Southeast Asia",
    "mideast":  "Middle East",
    "india":    "India",
}

REGION_ACCENT = {
    "americas": "#17243F",
    "europe":   "#788CE3",
    "sea":      "#92BAD5",
    "mideast":  "#b8a832",
    "india":    "#5a8a4a",
}


def build_html(data: dict) -> str:
    meta    = data.get("meta", {})
    regions = data.get("regions", {})
    week    = meta.get("week_label", "K-Beauty Pulse Weekly")

    region_rows = ""
    for rk, label in REGION_LABELS.items():
        d = regions.get(rk, {})
        if not d:
            continue

        accent  = REGION_ACCENT[rk]
        sellers = d.get("sellers", [])[:2]
        kws     = d.get("kw_ranking", [])[:4]
        tip     = d.get("trend_tooltip", "")

        # 핵심 한 줄: trend_tooltip 첫 문장만
        summary = tip.split(".")[0].strip() + "." if tip else ""

        # 키워드 pills
        kw_pills = "".join([
            f'<span style="display:inline-block;font-size:10px;padding:2px 8px;'
            f'border-radius:2px;background:{accent}18;color:{accent};'
            f'font-weight:600;margin-right:4px;margin-bottom:4px">'
            f'{k.get("kw","")}</span>'
            for k in kws
        ])

        # 셀러 목록
        seller_list = "".join([
            f'<div style="font-size:11px;color:#3a4a6a;padding:3px 0;'
            f'border-bottom:0.5px solid rgba(23,36,63,0.06)">'
            f'<span style="font-weight:600;color:#17243F">#{i+1}</span>'
            f'&nbsp;&nbsp;{s.get("name","")}</div>'
            for i, s in enumerate(sellers)
        ])

        region_rows += f"""
        <tr>
          <td style="padding:18px 0;border-bottom:0.5px solid rgba(23,36,63,0.08)">
            <table style="width:100%;border-collapse:collapse">
              <tr>
                <td style="vertical-align:top;width:110px;padding-right:20px">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
                    <div style="width:3px;height:14px;background:{accent};border-radius:2px;flex-shrink:0"></div>
                    <span style="font-size:12px;font-weight:700;color:#17243F">{label}</span>
                  </div>
                  <div style="font-size:10px;color:#788CE3;line-height:1.6">{summary}</div>
                </td>
                <td style="vertical-align:top;width:180px;padding-right:20px;
                      border-left:0.5px solid rgba(23,36,63,0.08);padding-left:20px">
                  <div style="font-size:9px;font-weight:700;color:#788CE3;
                        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">Keywords</div>
                  <div>{kw_pills}</div>
                </td>
                <td style="vertical-align:top;
                      border-left:0.5px solid rgba(23,36,63,0.08);padding-left:20px">
                  <div style="font-size:9px;font-weight:700;color:#788CE3;
                        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">Best Sellers</div>
                  {seller_list}
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>K-Beauty Pulse — {week}</title>
</head>
<body style="margin:0;padding:20px;background:#FAF9F6;
  font-family:Helvetica,'Apple SD Gothic Neo',-apple-system,sans-serif">

<div style="max-width:620px;margin:0 auto;background:#ffffff;border-radius:6px;
     overflow:hidden;border:0.5px solid rgba(23,36,63,0.1)">

  <!-- HEADER -->
  <div style="background:#17243F;padding:24px 28px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
      <div style="display:flex;align-items:center;gap:8px">
        <table cellpadding="0" cellspacing="2" style="width:18px;height:18px;flex-shrink:0">
          <tr>
            <td style="background:#788CE3;border-radius:1px;width:8px;height:8px"></td>
            <td style="background:#DFF478;border-radius:1px;width:8px;height:8px"></td>
          </tr>
          <tr>
            <td style="background:#DFF478;border-radius:1px;width:8px;height:8px"></td>
            <td style="background:#92BAD5;border-radius:1px;width:8px;height:8px"></td>
          </tr>
        </table>
        <span style="font-size:12px;font-weight:700;color:#ffffff;letter-spacing:0.02em">K-Beauty Pulse</span>
      </div>
      <span style="font-size:10px;color:rgba(255,255,255,0.4)">{week}</span>
    </div>
    <div style="font-size:20px;font-weight:700;color:#ffffff;line-height:1.25;letter-spacing:-0.01em">
      글로벌 K-Beauty 위클리 리포트
    </div>
  </div>

  <!-- BODY -->
  <div style="padding:8px 28px 20px">
    <table style="width:100%;border-collapse:collapse">
      {region_rows}
    </table>
  </div>

  <!-- FOOTER -->
  <div style="background:#FAF9F6;padding:14px 28px;border-top:0.5px solid rgba(23,36,63,0.08);
       display:flex;align-items:center;justify-content:space-between">
    <div style="font-size:9px;color:#788CE3;line-height:1.7">
      출처: WWD · BeautyMatter · CosmeticsDesign-Asia · KOTRA · 관세청<br>
      검증된 소스 기반 · 추정치 미사용
    </div>
    <a href="https://kbeauty-pulse.vercel.app"
       style="font-size:10px;color:#17243F;font-weight:700;text-decoration:none;
              padding:5px 12px;border-radius:3px;border:0.5px solid rgba(23,36,63,0.2)">
      대시보드 보기 →
    </a>
  </div>

</div>
</body></html>"""

    return html


def send_email(data: dict) -> None:
    sender_email = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    week         = data.get("meta", {}).get("week_label", "K-Beauty Weekly Report")

    html_content = build_html(data)

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
    import os, json
    data_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    html = build_html(data)
    with open("email_preview.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("=== email_preview.html 저장 완료 ===")
