import json, os, re, html, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (compatible; 1suni-collector/1.0)"}
RSS = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR%3Ako"

def search(kw):
    url = RSS.format(q=urllib.parse.quote(kw + " when:7d"))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        root = ET.fromstring(r.read())

    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        src = item.find("source")
        press = (src.text or "").strip() if src is not None else "기사"
        if not title or not link:
            continue
        if press and title.endswith(" - " + press):
            title = title[: -(len(press) + 3)]
        out.append({"t": html.unescape(title)[:80], "u": link, "press": press})
        if len(out) == 3:
            break
    return out

KEYWORDS = []
try:
    src = open("index.html", encoding="utf-8").read()
    m = re.search(r'\["빅이슈"\s*,\s*"뉴스"\s*,\s*\[(.*?)\]\]', src, re.S)
    if m:
        KEYWORDS = re.findall(r'"([^"]+)"', m.group(1))
except Exception as e:
    print("index.html 파싱 실패:", e)

if not KEYWORDS:
    raise SystemExit("빅이슈 항목을 찾지 못했습니다")

print("키워드:", KEYWORDS)

out = {"updated": datetime.now(KST).isoformat(timespec="seconds"), "news": {}}
for kw in KEYWORDS:
    try:
        arts = search(kw)
        if arts:
            out["news"][kw] = arts
        print(f"  {kw}: {len(arts)}건  {arts[0]['press'] if arts else '-'}")
    except Exception as e:
        print(f"  {kw}: 실패 {e}")

os.makedirs("data", exist_ok=True)
with open("data/news.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("DONE", len(out["news"]), "개 항목")
