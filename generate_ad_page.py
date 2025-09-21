import requests
import json
import os
import datetime

# --- 애드픽 API 설정 (니 affid 꼭 확인해!) ---
AFFID = '2efa07'
API_URL = f"https://adpick.co.kr/apis/offers.php?affid={AFFID}&order=rand"

# User-Agent 헤더 (봇 차단 방지용)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

OUTPUT_DIR = "ads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PUBLISHED_FILE = "published_offers.json"

DEFAULT_PROMO = "딱 내 스타일~ 오늘 바로 써봐!"
BUTTON_TEXT = "지금 바로 체험하기 🚀"

def load_published():
    if os.path.exists(PUBLISHED_FILE):
        try:
            with open(PUBLISHED_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    return set(json.loads(content))
                return set()
        except json.JSONDecodeError:
            print(f"경고: {PUBLISHED_FILE} 파일 손상! 새로 생성합니다.")
            return set()
    return set()

def save_published(published_set):
    with open(PUBLISHED_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(published_set), f, ensure_ascii=False, indent=2)

def fetch_campaigns():
    print("[시작] 애드픽 API 캠페인 목록 불러오는 중...")
    try:
        res = requests.get(API_URL, headers=HEADERS)
        res.raise_for_status()
        campaign_list = res.json()
        print(f"[정보] {len(campaign_list)}개 캠페인 조회됨.")
        return campaign_list or []
    except Exception as e:
        print(f"[에러] API 호출 실패: {e}")
        return []

def select_new_campaign(campaigns, published):
    for camp in campaigns:
        offer_id = camp.get("apOffer")
        if not offer_id:
            continue
        if offer_id not in published:
            print(f"[선택] 신규 캠페인: {camp.get('apAppTitle', offer_id)}")
            return camp
    print("[정보] 신규 캠페인 없음.")
    return None

def generate_html(data):
    app_title = data.get('apAppTitle', '새 캠페인')
    icon_url = data.get('apImages', {}).get('icon', '')
    headline = data.get('apHeadline', '매력적인 다양한 기능을 지금 만나봐!')
    promo_text_api = data.get('apAppPromoText')
    tracking_link = data.get('apTrackingLink', '#')
    remain = data.get('apRemain')

    if not promo_text_api or promo_text_api.strip() == "":
        promo = headline if headline != '매력적인 다양한 기능을 지금 만나봐!' else DEFAULT_PROMO
    else:
        promo = promo_text_api

    remain_html = ''
    if remain and isinstance(remain, int) and remain > 0:
        remain_html = f'<p style="color:#d9534f; font-weight:bold; margin-bottom:18px;">⏰ 오늘 남은 잔여 수량: {remain}개</p>'

    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{app_title}</title>
    <style>
      body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin:20px; background:#f4f7f6; color:#333; }}
      .container {{ max-width:480px; margin:auto; padding:20px; background:#fff; border-radius:14px; box-shadow:0 5px 20px rgba(0,0,0,0.1); text-align:center; }}
      h2 {{ color:#0056b3; margin-bottom:12px; font-size:1.8rem; }}
      img {{ width:130px; height:auto; border-radius:22%; border:3px solid #eee; margin-bottom:16px; }}
      p.headline {{ font-weight:700; font-size:1.15rem; margin:16px 0 8px; color:#111; }}
      p.promo-text {{ color:#444; font-size:0.95rem; line-height:1.5; margin-bottom:18px; white-space:pre-line; }}
      a.button {{ display:inline-block; padding:14px 34px; font-weight:700; background:#007bff; color:#fff; border-radius:8px; text-decoration:none; box-shadow:0 5px 15px rgba(0,123,255,0.4); transition:background-color 0.3s ease; }}
      a.button:hover {{ background-color:#0056cc; }}
      p.remain {{ color:#d9534f; font-weight:bold; margin-bottom:18px; }}
      p.footer {{ font-size:0.85rem; color:#888; margin-top:36px; }}
    </style>
    </head>
    <body>
      <div class="container">
        <h2>{app_title}</h2>
        <img src="{icon_url}" alt="{app_title} 아이콘" />
        <p class="headline">{headline}</p>
        <p class="promo-text">{promo}</p>
        {remain_html}
        <a href="{tracking_link}" target="_blank" class="button">{BUTTON_TEXT}</a>
        <p class="footer">이 포스팅은 애드픽 캠페인 참여로 작성되었으며, 수익 발생 시 대가를 받을 수 있습니다.</p>
      </div>
    </body>
    </html>
    """
    return html

def save_html(html_content, title, offer_id):
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).replace(" ", "_")
    filename = f"{today_str}_{safe_title[:30]}_{offer_id}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[완료] HTML 파일 생성됨: {filepath}")
    return filename

def main():
    published_offers = load_published()
    campaigns = fetch_campaigns()
    if not campaigns:
        print("캠페인 없음, 종료!")
        return
    new_camp = select_new_campaign(campaigns, published_offers)
    if not new_camp:
        print("새 캠페인 없음!")
        return
    html = generate_html(new_camp)
    offer_id = new_camp.get("apOffer")
    filename = save_html(html, new_camp.get('apAppTitle', ''), offer_id)
    published_offers.add(offer_id)
    save_published(published_offers)
    print(f"'{filename}' 캠페인 자동발행 완료!")

if __name__ == "__main__":
    main()
