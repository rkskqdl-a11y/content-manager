import requests
import json
from datetime import datetime
import os

AFFID = '2efa07'
API_URL = f"https://adpick.co.kr/apis/offers.php?affid={AFFID}&order=randone"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{app_title} - 오늘의 추천</title>
<style>
    body {{ font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif; margin:20px; background:#f4f7f6; color:#333; line-height:1.6; }}
    .container {{ max-width:800px; margin:30px auto; padding:30px; background:#fff; border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,0.08); }}
    h1 {{ color:#0056b3; text-align:center; margin-bottom:25px; font-size:2.2em; border-bottom:2px solid #eee; padding-bottom:15px; }}
    .app-info {{ text-align:center; margin-bottom:30px; }}
    .app-info img {{ max-width:150px; height:auto; border-radius:25%; border:4px solid #ddd; padding:5px; background:#fff; margin-bottom:15px; }}
    .ad-headline {{ font-size:1.3em; color:#444; font-weight:bold; margin:25px 0 15px 0; text-align:center; }}
    .promo-text {{ font-size:1em; color:#666; margin-bottom:30px; text-align:justify; padding:0 15px; }}
    .btn-link {{ display:block; width:80%; max-width:300px; margin:0 auto 40px; padding:15px 25px; background:#007bff; color:#fff; text-align:center; text-decoration:none; border-radius:8px; font-weight:bold; transition:background-color .3s ease; }}
    .btn-link:hover {{ background-color:#0056b3; }}
    .disclaimer {{ margin-top:50px; padding:20px; border-top:1px solid #eee; font-size:.9em; color:#888; text-align:center; background:#f9f9f9; border-radius:0 0 10px 10px; }}
    @media(max-width:600px) {{
        .container {{ margin:15px; padding:20px; }}
        h1 {{ font-size:1.8em; }}
        .app-info img {{ max-width:100px; }}
        .btn-link {{ width:90%; padding:12px 20px; }}
    }}
</style>
</head>
<body>
    <div class="container">
        <header><h1>{app_title}</h1></header>
        <main>
            <div class="app-info">
                <img src="{icon_url}" alt="{app_title} 아이콘" />
                <div class="ad-headline">"<strong>{ad_headline}</strong>"</div>
                <p class="promo-text">{promo_text}</p>
                <a href="{tracking_link}" target="_blank" class="btn-link">캠페인 참여하기</a>
            </div>
        </main>
        <footer class="disclaimer">
            이 포스팅은 애드픽 캠페인 참여로 인해 작성되었으며, 수익 발생 시 일정액의 대가를 받을 수 있습니다.
        </footer>
    </div>
</body>
</html>
"""

OUTPUT_DIR = "ads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_ad_and_generate_html():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        ads = response.json()
        if not ads:
            print("캠페인 데이터가 없습니다.")
            return None
        ad = ads[0]
        app_title = ad.get("apAppTitle", "제목 없음")
        ad_headline = ad.get("apHeadline", "상세 설명이 없습니다.")
        icon_url = ad.get("apImages", {}).get("icon", "")
        tracking_link = ad.get("apTrackingLink", "#")
        promo_text = ad.get("apAppPromoText", ad_headline)
        html = HTML_TEMPLATE.format(
            app_title=app_title, ad_headline=ad_headline,
            icon_url=icon_url, tracking_link=tracking_link, promo_text=promo_text
        )
        today = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c for c in app_title if c.isalnum() or c in (" ", "-", "_")).replace(" ", "_")
        fname = f"{today}_{safe_title[:30]}.html"
        fpath = os.path.join(OUTPUT_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML 파일 생성 완료: {fpath}")
        return fpath
    except Exception as e:
        print(f"오류 발생: {e}")
        return None

if __name__ == "__main__":
    fetch_ad_and_generate_html()
