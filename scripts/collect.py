import json, os, time, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
KEY = os.environ["KOFIC_KEY"]
target = (datetime.now(KST) - timedelta(days=1)).strftime("%Y%m%d")

url = ("http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/"
       "searchDailyBoxOfficeList.json?"
       + urllib.parse.urlencode({"key": KEY, "targetDt": target}))

raw = None
for attempt in range(1, 6):
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            raw = json.load(r)
        print(f"성공 (시도 {attempt}회)")
        break
    except Exception as e:
        print(f"시도 {attempt} 실패: {e}")
        if attempt < 5:
            time.sleep(attempt * 5)

if raw is None:
    raise SystemExit("KOFIC 연결 실패 — 기존 데이터 유지")

rows = raw["boxOfficeResult"]["dailyBoxOfficeList"][:10]
if not rows:
    raise SystemExit("no data for " + target)

top = max(int(x["audiCnt"]) for x in rows)

lst = []
for x in rows:
    mv = "NEW" if x.get("rankOldAndNew") == "NEW" else int(x.get("rankInten") or 0)
    lst.append({
        "name": x["movieNm"],
        "idx": max(1, round(int(x["audiCnt"]) / top * 100)),
        "mv": mv,
    })

out = {
    "source": "영화진흥위원회",
    "basis": "일별 관객수",
    "targetDate": target,
    "updated": datetime.now(KST).isoformat(timespec="seconds"),
    "list": lst,
}

os.makedirs("data", exist_ok=True)
with open("data/movies.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("OK", target, [i["name"] for i in lst])
