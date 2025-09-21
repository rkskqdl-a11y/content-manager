import requests
import json
import os
import datetime

AFFID = '2efa07'
API_URL = f"https://adpick.co.kr/apis/offers.php?affid={AFFID}&order=rand"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

OUTPUT_DIR = "ads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 발행 기록 파일 (발행한 apOffer 리스트 저장)
PUBLISHED_FILE = "published_offers.json"

# 자연스럽고 후킹 좋은 기본 문구
DEFAULT_PROMO = "딱 내 스타일~ 오늘 바로 써봐!"
BUTTON_TEXT = "지금 바로 체험하기 🚀"

def load_published():
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_published(published_set):
    with open(PUBLISHED_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(published_set), f, ensure_ascii=False, indent=2)

def fetch_campaigns():
    try:
        res = requests.get(API_URL, headers=HEADERS)
        res.raise_for_status()
        return res.json() or []
    except Exception as e:
        print(f"[에러] API 호출 실패: {e}")
        return []

def select_new_campaign(campaigns, published):
    # 하루 1개 자동발행 목표: 제일 최근 중 미발행 캠페인 1개 선택
    for camp in campaigns:
        offer_id = camp.get("apOffer")
        if not offer_id:
            continue
        # 발행 기록에 없으면 새 캠페인
        if offer_id not in published:
            return camp
    return None

def generate_html(data):
    promo = data.get("apAppPromoText")
    headline = data.get("apHeadline")
    if not promo or promo.strip() == "":
        promo = headline if headline else DEFAULT_PROMO

    html = f"""
    <div style="max-width:480px; margin:auto; padding:20px; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background:#fff; border-radius:14px; box-shadow:0 5px 15px rgba(0,0,0,0.1); text-align:center;">
      <h2 style="color:#0056b3; margin-bottom:12px;">{data.get('apAppTitle','')}</h2>
      <img src="{data.get('apImages',{{}}).get('icon','')}" alt="{data.get('apAppTitle','')} 아이콘" style="width:130px; height:auto; border-radius:22%;" />
      <p style="font-weight:700; font-size:1.1rem; margin:16px 0 8px; color:#222;">{headline}</p>
      <p style="color:#444; font-size:0.95rem; line-height:1.5; margin-bottom:26px;">{promo}</p>
      <a href="{data.get('apTrackingLink','#')}" target="_blank" 
         style="display:inline-block; background:#0066ff; color:#fff; font-weight:700; padding:14px 30px; border-radius:9px; text-decoration:none;
                box-shadow:0 4px 10px rgba(0,102,255,0.3); transition:background-color 0.3s ease;">
        {BUTTON_TEXT}
      </a>
    </div>
    """
    return html

def save_html(html, title):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).replace(" ", "_")
    filename = f"{today}_{safe_title[:30]}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[완료] HTML 파일 생성됨: {filepath}")
    return filename

def main():
    published = load_published()
    campaigns = fetch_campaigns()
    if not campaigns:
        print("캠페인 목록이 비어있음. 종료!")
        return

    new_camp = select_new_campaign(campaigns, published)
    if not new_camp:
        print("새로운 캠페인이 없습니다.")
        return

    html = generate_html(new_camp)
    filename = save_html(html, new_camp.get('apAppTitle',''))

    # 발행 기록에 추가 & 저장
    published.add(new_camp.get("apOffer"))
    save_published(published)

    print(f"'{filename}' 파일로 신규 캠페인 자동발행 완료!")

if __name__ == "__main__":
    main()
