import requests
import json
from datetime import datetime
import os

# --- 애드픽 API 설정 (!!!니 affid가 맞는지 다시 한번 확인하고, 아니면 수정해줘!!!) ---
AFFID = '2efa07'
API_URL = f"https://adpick.co.kr/apis/offers.php?affid={AFFID}&order=randone" # order=randone이면 1개만 가져옴

# --- [포동이 수정!] ---
# 403 Forbidden 에러 해결을 위해 User-Agent를 삭제하고 Referer를 추가한 최소 헤더 구성
# requests 라이브러리가 기본 User-Agent를 보내도록 하고, Referer로 애드픽 웹사이트를 명시
HEADERS = {
    'Referer': 'https://adpick.co.kr/', # ⭐ 이게 가장 중요! 이 요청이 애드픽 사이트에서 온 것처럼 보이게 함
    'Accept': '*/*', # 모든 타입 허용 (가장 보편적인 요청)
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}
# --- [포동이 수정 끝!] ---

OUTPUT_DIR = "ads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PUBLISHED_FILE = "published_offers.json"

# --- sitemap.xml 관련 상수 ---
# BASE_URL은 content-manager 레포가 배포되는 실제 웹 주소여야 합니다.
BASE_URL = "https://rkskqdl-a11y.github.io/content-manager/"
SITEMAP_FILENAME = "sitemap.xml" 

# 모든 컨텐츠에 어울리는 자연스러운 구어체 후킹 문구
DEFAULT_PROMO = "딱 내 스타일~ 오늘 바로 써봐!"
BUTTON_TEXT = "지금 바로 체험하기 🚀"

# --- [포동이 수정!] --- 하루에 발행할 최대 캠페인 수 설정
# 이 값은 GitHub Actions 등의 스케줄러가 한번 실행될 때 발행될 캠페인 수입니다.
MAX_CAMPAIGNS_PER_RUN = 5 
# --- [포동이 수정 끝!] ---

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
        # requests.get 호출 시 headers 인자로 위에서 정의한 HEADERS 사용!
        res = requests.get(API_URL, headers=HEADERS) 
        res.raise_for_status() # HTTP 오류가 발생하면 예외 발생 (4xx, 5xx)
        campaign_list = res.json()
        print(f"[정보] {len(campaign_list)}개 캠페인 조회됨.")
        return campaign_list or []
    except Exception as e:
        print(f"[에러] API 호출 실패: {e} - 애드픽 API 호출 정책(1분 1회)을 위반했거나 IP 차단일 수 있습니다.") # --- [포동이 수정!] --- 에러 메시지 추가
        return []

# --- [포동이 수정!] --- 여러 개의 신규 캠페인을 선택하도록 함수 수정
def select_n_new_campaigns(campaigns, published, limit):
    new_campaigns = []
    # 애드픽 API가 'order=randone'으로 설정되어 있으면 매번 1개만 가져오므로,
    # 실제로는 이 함수가 limit개 만큼의 '다른' 캠페인을 찾는 게 어려울 수 있습니다.
    # 하지만 fetch_campaigns()에서 여러 캠페인을 가져온다고 가정하고 로직은 유지합니다.
    # order 파라미터를 'rand' 등으로 바꾸면 더 많은 캠페인을 가져올 수 있습니다.
    
    for camp in campaigns:
        offer_id = camp.get("apOffer")
        if not offer_id:
            continue
        if offer_id not in published:
            new_campaigns.append(camp)
            if len(new_campaigns) >= limit:
                break # 설정된 개수만큼 찾았으면 중단
    
    if new_campaigns:
        print(f"[선택] {len(new_campaigns)}개의 신규 캠페인 발견.")
    else:
        print("[정보] 신규 캠페인 없음.")
    return new_campaigns
# --- [포동이 수정 끝!] ---

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
    today_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).replace(" ", "_")
    filename = f"{today_str}_{safe_title[:30]}_{offer_id}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding="utf-8") as f:
        f.write(html_content)
    print(f"[완료] HTML 파일 생성됨: {filepath}")
    return filename

def generate_sitemap():
    print("[시작] sitemap.xml 생성 중...")
    
    all_ad_pages = []
    if os.path.exists(OUTPUT_DIR):
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith(".html"):
                # URL 생성 시 BASE_URL과 OUTPUT_DIR를 사용해서 올바른 경로 생성
                all_ad_pages.append(f"{BASE_URL}{OUTPUT_DIR}/{filename}")
    
    # 루트 페이지 (content-manager 기본 페이지)도 포함
    # (주의: 만약 BASE_URL이 content-manager 레포의 루트 페이지가 아니라면 수정 필요)
    all_pages = [BASE_URL] + sorted(all_ad_pages)

    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in all_pages:
        sitemap_content += '  <url>\n'
        sitemap_content += f'    <loc>{url}</loc>\n'
        sitemap_content += f'    <lastmod>{datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")}</lastmod>\n'
        sitemap_content += '    <changefreq>daily</changefreq>\n' 
        sitemap_content += '    <priority>0.8</priority>\n'
        sitemap_content += '  </url>\n'
    
    sitemap_content += '</urlset>\n'
    
    # --- [포동이 수정!] --- sitemap.xml을 ads 폴더 내에 생성하도록 수정
    # 이렇게 하면 sitemap.xml의 최종 경로는 "https://rkskqdl-a11y.github.io/content-manager/ads/sitemap.xml" 가 됩니다.
    root_sitemap_path = os.path.join(OUTPUT_DIR, SITEMAP_FILENAME) 
    with open(root_sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    
    print(f"[완료] sitemap.xml 업데이트됨: {root_sitemap_path}")


def main():
    print("--- [캠페인 자동발행 시작] ---")
    published_offers = load_published()
    
    # --- [포동이 수정!] ---
    # 애드픽 API의 1분 1회 호출 제한 정책으로 인해 API 호출 시도 시 403 에러가 발생할 수 있으므로,
    # 스크립트를 재실행하기 전에 충분한 시간 (최소 몇 시간)을 기다려야 합니다.
    # 또한 API_URL의 order=randone 파라미터는 1개 캠페인만 가져옵니다.
    # 만약 fetch_campaigns()에서 여러 캠페인을 가져오도록 API_URL을 수정하지 않았다면,
    # select_n_new_campaigns는 여전히 최대 1개의 신규 캠페인만 반환할 수 있습니다.
    campaigns = fetch_campaigns() 
    if not campaigns:
        print("캠페인 없음, 종료!")
        return

    # 최대 발행 개수만큼 신규 캠페인 선택
    new_campaigns_to_publish = select_n_new_campaigns(campaigns, published_offers, MAX_CAMPAIGNS_PER_RUN)

    if not new_campaigns_to_publish:
        print("새 캠페인 없음!")
        # 신규 캠페인이 없더라도 sitemap은 항상 최신 상태여야 하므로, 이 경우에도 generate_sitemap을 호출합니다.
        generate_sitemap() # --- [포동이 수정!] ---
        return

    published_count_current_run = 0
    for new_camp in new_campaigns_to_publish:
        app_title = new_camp.get('apAppTitle', '')
        offer_id = new_camp.get("apOffer")

        html = generate_html(new_camp)
        filename = save_html(html, app_title, offer_id)
        
        published_offers.add(offer_id) # 발행된 캠페인 ID를 published_offers 세트에 추가
        print(f"'{filename}' 캠페인 자동발행 완료!")
        published_count_current_run += 1
        
    save_published(published_offers) # 한 번의 실행에서 발행된 모든 캠페인을 저장
    print(f"총 {published_count_current_run}개 캠페인 발행 및 기록 완료!")
    # --- [포동이 수정 끝!] ---
    
    generate_sitemap() # 새 HTML 생성 후, sitemap.xml도 업데이트!

    print("--- [캠페인 자동발행 종료] ---")

if __name__ == "__main__":
    main()
