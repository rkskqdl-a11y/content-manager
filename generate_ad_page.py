import requests
import json
import os
import datetime

# --- 애드픽 API 설정 (!!!여기 니 affid가 맞는지 다시 한번 확인하고, 아니면 수정해줘!!!) ---
AFFID = '2efa07'
API_URL = f"https://adpick.co.kr/apis/offers.php?affid={AFFID}&order=rand" # API_URL을 rand로 변경

# --- User-Agent 추가: GitHub Actions의 API 호출이 브라우저처럼 보이게 하기 위함 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

OUTPUT_DIR = "ads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 발행 기록 파일 (발행한 apOffer 리스트 저장)
# 이 파일은 content-manager 레포 루트에 생성됨
PUBLISHED_FILE = "published_offers.json"

# 자연스럽고 후킹 좋은 기본 문구 및 버튼 텍스트
DEFAULT_PROMO = "딱 내 스타일~ 오늘 바로 써봐!"
BUTTON_TEXT = "지금 바로 체험하기 🚀"

def load_published():
    if os.path.exists(PUBLISHED_FILE):
        try:
            with open(PUBLISHED_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if content: # 파일 내용이 비어있지 않은지 확인
                    return set(json.loads(content))
                return set()
        except json.JSONDecodeError: # JSON 파싱 오류 처리 (파일 내용이 유효한 JSON이 아닐 경우)
            print(f"경고: {PUBLISHED_FILE} 파일이 손상되었거나 형식이 잘못되었습니다. 새로 생성합니다.")
            return set()
    return set()

def save_published(published_set):
    with open(PUBLISHED_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(published_set), f, ensure_ascii=False, indent=2)

def fetch_campaigns():
    print("[시작] 애드픽 API 캠페인 목록 불러오는 중...")
    try:
        res = requests.get(API_URL, headers=HEADERS)
        res.raise_for_status() # HTTP 오류가 발생하면 예외 발생
        campaign_list = res.json()
        print(f"[정보] 총 {len(campaign_list)}개의 캠페인 조회됨.")
        return campaign_list or []
    except requests.exceptions.RequestException as e:
        print(f"[에러] API 호출 실패: {e}")
        return []
    except json.JSONDecodeError:
        print("[에러] API 응답이 유효한 JSON 형식이 아닙니다.")
        return []

def select_new_campaign(campaigns, published):
    # API 응답은 최신순 또는 랜덤으로 오지만, 여기서 한번 더 정렬 가능 (지금은 그냥 받은 순서)
    for camp in campaigns:
        offer_id = camp.get("apOffer")
        if not offer_id:
            print(f"경고: apOffer가 없는 캠페인 스킵: {camp.get('apAppTitle', 'Unknown')}")
            continue
        
        if offer_id not in published:
            print(f"[선택] 신규 캠페인 선택됨: {camp.get('apAppTitle', offer_id)}")
            return camp
    print("[정보] 발행 가능한 신규 캠페인을 찾을 수 없습니다.")
    return None

# !!! 이 함수가 아까 에러났던 부분이고, 지금 수정된 버전으로 바뀐 거야! !!!
def generate_html(data):
    # 필요한 데이터 먼저 추출 (빈 값 대비)
    app_title = data.get('apAppTitle', '새로운 캠페인')
    icon_url = data.get('apImages', {}).get('icon', '')
    headline = data.get('apHeadline', '매력적인 새로운 경험이 시작됩니다!')
    promo_text_api = data.get('apAppPromoText')
    tracking_link = data.get('apTrackingLink', '#')

    # 홍보 문구 부재 시 대체 로직
    # apAppPromoText가 비어있으면 apHeadline 사용, 그것도 비어있으면 DEFAULT_PROMO 사용
    if not promo_text_api or promo_text_api.strip() == "":
        promo = headline if headline != '매력적인 새로운 경험이 시작됩니다!' else DEFAULT_PROMO
    else:
        promo = promo_text_api

    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{app_title} - 놓치지 마세요!</title>
    <style>
      body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f4f7f6; color: #333; line-height: 1.6; }}
      .container {{ max-width: 480px; margin: auto; padding: 20px; background: #fff; border-radius: 14px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); text-align: center; }}
      h2 {{ color: #0056b3; margin-bottom: 12px; font-size: 1.8em; }}
      img {{ width: 130px; height: auto; border-radius: 22%; margin-bottom: 15px; border: 3px solid #eee; }}
      p.headline {{ font-weight: 700; font-size: 1.1rem; margin: 16px 0 8px; color: #222; }}
      p.promo-text {{ color: #444; font-size: 0.95rem; line-height: 1.5; margin-bottom: 26px; }}
      a.button {{ display: inline-block; background: #0066ff; color: #fff; font-weight: 700; padding: 14px 30px; border-radius: 9px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,102,255,0.3); transition: background-color 0.3s ease; }}
      a.button:hover {{ background-color: #0050cc; }}
    </style>
    </head>
    <body>
      <div class="container">
        <h2>{app_title}</h2>
        <img src="{icon_url}" alt="{app_title} 아이콘" />
        <p class="headline">{headline}</p>
        <p class="promo-text">{promo}</p>
        <a href="{tracking_link}" target="_blank" class="button">
          {BUTTON_TEXT}
        </a>
      </div>
    </body>
    </html>
    """
    return html

def save_html(html_content, title, offer_id):
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    # 파일명에 offer_id 포함하여 고유성 확보 (재발행 시 이전 파일 덮어쓰기 방지)
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).replace(" ", "_")
    filename = f"{today_str}_{safe_title[:30]}_{offer_id}.html" # 파일명에 offer_id 추가
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[완료] HTML 파일 생성됨: {filepath}")
    return filename

def main():
    print("--- [캠페인 자동발행 시작] ---")
    published_offers = load_published() # 발행 기록 로드
    all_campaigns = fetch_campaigns()   # 애드픽 API에서 전체 캠페인 가져오기

    if not all_campaigns:
        print("조회된 캠페인이 없어 작업을 종료합니다.")
        return

    # 새로운 캠페인만 필터링하여 선택
    campaign_to_publish = select_new_campaign(all_campaigns, published_offers)

    if campaign_to_publish:
        generated_html = generate_html(campaign_to_publish)
        new_offer_id = campaign_to_publish.get("apOffer")
        
        # 파일 저장 및 이름 가져오기
        saved_filename = save_html(generated_html, campaign_to_publish.get('apAppTitle', ''), new_offer_id)

        # 발행 기록 업데이트 및 저장
        published_offers.add(new_offer_id)
        save_published(published_offers)
        print(f"성공적으로 발행되었습니다: {saved_filename}")
    else:
        print("현재 발행할 새로운 캠페인이 없습니다. (이미 발행했거나 API에 신규 캠페인 없음)")

    print("--- [캠페인 자동발행 종료] ---")

if __name__ == "__main__":
    main()
