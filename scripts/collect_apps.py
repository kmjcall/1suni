import json, os, urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "1suni-collector/1.0"}
V2 = "https://rss.applemarketingtools.com/api/v2/kr/apps"

# 분야: (장르ID, 차트, {사이트 표기: [앱 이름 별칭]})
CATS = {
"은행 앱": (6015, "top-free", {
    "토스": ["토스"], "카카오뱅크": ["카카오뱅크"],
    "KB스타뱅킹": ["kb스타뱅킹", "starbanking", "kb국민은행"],
    "신한 SOL": ["신한sol", "sol뱅크", "신한쏠"],
    "우리WON": ["우리won", "won뱅킹"], "하나원큐": ["하나원큐"],
    "NH올원": ["nh올원", "올원뱅크", "nh스마트뱅킹"],
    "케이뱅크": ["케이뱅크"], "IBK i-ONE": ["i-one", "아이원"],
    "SC제일": ["sc제일"],
}),
"증권 앱": (6015, "top-free", {
    "토스증권": ["토스증권"], "키움 영웅문": ["영웅문", "키움증권"],
    "미래에셋 M-STOCK": ["m-stock", "엠스탁", "미래에셋증권"],
    "삼성증권 mPOP": ["mpop", "엠팝", "삼성증권"],
    "NH나무": ["나무증권", "nh투자증권"],
    "KB M-able": ["m-able", "마블"],
    "한국투자 신한": ["한국투자"], "신한 SOL": ["신한투자", "sol증권"],
    "대신 크레온": ["크레온", "대신증권"], "이베스트": ["이베스트", "ls증권"],
}),
"배달 앱": (6023, "top-free", {
    "배달의민족": ["배달의민족", "배민"], "쿠팡이츠": ["쿠팡이츠"],
    "요기요": ["요기요"], "땡겨요": ["땡겨요"], "위메프오": ["위메프오"],
    "배달특급": ["배달특급"], "먹깨비": ["먹깨비"], "놀장": ["놀장"],
    "부르심": ["부르심"], "띵동": ["띵동"],
}),
"부동산 앱": (6012, "top-free", {
    "호갱노노": ["호갱노노"], "네이버부동산": ["네이버부동산"],
    "직방": ["직방"], "다방": ["다방"], "아실": ["아실"],
    "부동산플래닛": ["부동산플래닛"], "리치고": ["리치고"],
    "밸류맵": ["밸류맵"], "디스코": ["디스코"], "알스퀘어": ["알스퀘어"],
}),
"음악 스트리밍": (6011, "top-free", {
    "멜론": ["멜론", "melon"], "유튜브 뮤직": ["youtubemusic", "유튜브뮤직"],
    "스포티파이": ["spotify", "스포티파이"], "지니뮤직": ["지니뮤직", "genie"],
    "플로": ["flo", "플로"], "바이브": ["vibe", "바이브"],
    "벅스": ["벅스", "bugs"], "애플 뮤직": ["applemusic", "애플뮤직"],
    "카카오뮤직": ["카카오뮤직"], "사운드클라우드": ["soundcloud"],
}),
"OTT": (6016, "top-free", {
    "넷플릭스": ["netflix", "넷플릭스"], "티빙": ["tving", "티빙"],
    "쿠팡플레이": ["쿠팡플레이"], "디즈니+": ["disney", "디즈니"],
    "웨이브": ["wavve", "웨이브"], "왓챠": ["watcha", "왓챠"],
    "애플TV+": ["appletv", "애플tv"], "라프텔": ["laftel", "라프텔"],
    "시리즈온": ["시리즈온"], "U+모바일tv": ["u+모바일", "모바일tv"],
}),
"모바일 게임": (6014, "top-grossing", {
    "로블록스": ["roblox", "로블록스"], "브롤스타즈": ["brawlstars", "브롤스타즈"],
    "리니지M": ["리니지m"], "오딘": ["오딘"], "원신": ["원신", "genshin"],
    "쿠키런": ["쿠키런"], "메이플M": ["메이플스토리m", "메이플m"],
    "붕괴 스타레일": ["스타레일", "starrail"],
    "프리코네": ["프리코네", "프린세스커넥트"],
    "전략적 팀 전투": ["전략적팀전투", "teamfight"],
}),
}

def norm(s):
    return "".join(str(s).lower().split())

def fetch(chart, genre=None, limit=100):
    url = (f"{V2}/{chart}/{limit}/apps.json" if genre is None
           else f"{V2}/{chart}/{limit}/genre={genre}/apps.json")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            rows = json.load(r).get("feed", {}).get("results", [])
        print(f"  [ok] {chart} genre={genre} -> {len(rows)}")
        return rows
    except Exception as e:
        print(f"  [--] {chart} genre={genre} : {e}")
        return []

# 이전 실행 결과 (등락 계산용)
prev = {}
try:
    with open("data/apps.json", encoding="utf-8") as f:
        old = json.load(f)
    for k, v in old.get("categories", {}).items():
        prev[k] = {it["name"]: i + 1 for i, it in enumerate(v.get("list", []))}
except Exception:
    pass

today = datetime.now(KST).strftime("%Y%m%d")
out = {"updated": datetime.now(KST).isoformat(timespec="seconds"), "categories": {}}

for cat, (genre, chart, alias) in CATS.items():
    print(f"[{cat}]")
    rows = fetch(chart, genre) or fetch(chart)
    if not rows:
        continue

    found = {}
    for i, app in enumerate(rows, 1):
        an = norm(app.get("name", ""))
        best, blen = None, 0
        for item, keys in alias.items():
            for k in keys:
                nk = norm(k)
                if nk and nk in an and len(nk) > blen:
                    best, blen = item, len(nk)
        if best and best not in found:
            found[best] = (i, app.get("name", ""))

    if len(found) < 3:
        print(f"  skip: {len(found)}개만 매칭")
        continue

    ranked = sorted(found.items(), key=lambda kv: kv[1][0])
    r1 = ranked[0][1][0]
    lst = []
    for pos, (item, (rank, real)) in enumerate(ranked, 1):
        if not prev:
            mv = 0
        elif item in prev.get(cat, {}):
            mv = prev[cat][item] - pos
        else:
            mv = "NEW"
        lst.append({"name": item, "idx": max(1, round(100 * r1 / rank)), "mv": mv})
        print(f"  {pos}. {item}  (차트 {rank}위 / {real})")

    out["categories"][cat] = {
        "source": "Apple App Store",
        "basis": "iOS 앱 순위",
        "targetDate": today,
        "list": lst,
    }

os.makedirs("data", exist_ok=True)
with open("data/apps.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("DONE", list(out["categories"].keys()))
