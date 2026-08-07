import json, os, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
KEY = os.environ["KOFIC_KEY"]
target = (datetime.now(KST) - timedelta(days=1)).strftime("%Y%m%d")

url = ("http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/"
       "searchDailyBoxOfficeList.json?"
       + urllib.parse.urlencode({"key": KEY, "targetDt": target}))

with urllib.request.urlopen(url, timeout=20) as r:
    raw = json.load(r)

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
    "targetDate": target,
    "updated": datetime.now(KST).isoformat(timespec="seconds"),
    "list": lst,
}

os.makedirs("data", exist_ok=True)
with open("data/movies.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("OK", target, [i["name"] for i in lst])
