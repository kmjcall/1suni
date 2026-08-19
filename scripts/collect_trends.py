import json, os, re, html, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (compatible; 1suni-collector/1.0)"}
RSS = "https://trends.google.com/trending/rss?geo=KR"
NS = "{https://trends.google.com/trending/rss}"

BLOCK = ["아동", "n번방", "그루밍", "자살"]

def blocked(kw):
    s = kw.replace(" ", "")
    return any(b.replace(" ", "") in s for b in BLOCK)

def vol_to_num(txt):
    t = str(txt).replace(",", "")
    m = re.search(r"(\d+)", t)
    if not m:
        return 0
    n = int(m.group(1))
    if "만" in t:
        n *= 10000
    elif "천" in t:
        n *= 1000
    return n

req = urllib.request.Request(RSS, headers=UA)
with urllib.request.urlopen(req, timeout=25) as r:
    root = ET.fromstring(r.read())

rows = []
for item in root.iter("item"):
    title = (item.findtext("title") or "").strip()
    if not title or blocked(title):
        print("  건너뜀:", title)
        continue

    vol = vol_to_num(item.findtext(NS + "approx_traffic") or "0")

    arts = []
    for na in item.findall(NS + "news_item"):
        t = (na.findtext(NS + "news_item_title") or "").strip()
        u = (na.findtext(NS + "news_item_url") or "").strip()
        p = (na.findtext(NS + "news_item_source") or "").strip()
        if t and u:
            arts.append({"t": html.unescape(re.sub(r"<[^>]+>", "", t))[:80],
                         "u": u, "press": p or "기사"})
        if len(arts) == 3:
            break

    rows.append({"name": html.unescape(title), "vol": vol, "news": arts})
    if len(rows) == 10:
        break
        
rows.sort(key=lambda x: -x["vol"])
if len(rows) < 3:
    raise SystemExit("급상승 검색어를 충분히 받지 못했습니다")

prev = {}
try:
    with open("data/bigissue.json", encoding="utf-8") as f:
        old = json.load(f)
    prev = {it["name"]: i + 1 for i, it in enumerate(old.get("list", []))}
except Exception:
    pass

top = max(r["vol"] for r in rows) or 1
lst = []
for i, r in enumerate(rows, 1):
    if not prev:
        mv = 0
    elif r["name"] in prev:
        mv = prev[r["name"]] - i
    else:
        mv = "NEW"
    idx = max(5, round(r["vol"] / top * 100)) if top > 1 else max(5, 105 - i * 10)
    lst.append({"name": r["name"], "idx": idx, "mv": mv, "news": r["news"]})
    print(f"  {i}. {r['name']}  ({r['vol']:,}+ / 기사 {len(r['news'])}건)")

out = {
    "source": "구글 트렌드",
    "basis": "구글 급상승 검색어",
    "targetDate": datetime.now(KST).strftime("%Y%m%d"),
    "updated": datetime.now(KST).isoformat(timespec="seconds"),
    "list": lst,
}

os.makedirs("data", exist_ok=True)
with open("data/bigissue.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("DONE", len(lst), "개")
