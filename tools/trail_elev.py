#!/usr/bin/env python3
"""組裝古道軌跡、每 25 公尺取一點，並由 DEM 取海拔 → data/raw/trails/tracks.json

讀取：data/raw/trails/ 的原始軌跡（來源見 README「資料來源與授權」）
      .cache/dem/（tools/fetch_dem.py 下載的 Copernicus DEM）
輸出：tracks.json：{古道 id: {"pts": [[經度, 緯度, 海拔], ...], "src": 說明}}，點由起點往終點排。
需要：numpy、rasterio（只有這支與 build_elev.py 需要）。

軌跡的方向一律依林業及自然保育署公布的里程方向（0 公里在起點）。
"""
import json, math, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data", "raw", "trails")
STEP = 25.0          # 重新取樣間隔（公尺）
JOIN_M = 400         # 能高東段的碎片：端點相距這麼近才接起來
EAST_GATE = (121.33507, 24.02932)   # 能高越嶺道東段登山口（林業保育署 API 的 TWD97 座標換算）

sys.path.insert(0, HERE)
from build_elev import sample  # noqa: E402  與文資海拔用同一套取值方式


def hav(a, b):
    p = math.radians
    x = math.sin(p(b[1] - a[1]) / 2) ** 2 + math.cos(p(a[1])) * math.cos(p(b[1])) * math.sin(p(b[0] - a[0]) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(x))


def kml_lines(text):
    """[(名稱, [(經度, 緯度), ...]), ...]"""
    out = []
    for pm in re.findall(r"<Placemark[^>]*>(.*?)</Placemark>", text, re.S):
        nm = re.search(r"<name>(.*?)</name>", pm, re.S)
        for c in re.findall(r"<LineString>.*?<coordinates>(.*?)</coordinates>", pm, re.S):
            pts = [tuple(map(float, x.split(",")[:2])) for x in c.split()]
            out.append(((nm.group(1).strip() if nm else ""), pts))
    return out


def kmz_lines(path):
    z = zipfile.ZipFile(path)
    return kml_lines(z.read([n for n in z.namelist() if n.endswith(".kml")][0]).decode("utf-8"))


def wkt_lines(g):
    return [[tuple(map(float, p.split()[:2])) for p in s.split(",")] for s in re.findall(r"\(([^()]+)\)", g)]


def mot(name):
    for t in json.load(open(os.path.join(RAW, "mot-41653-trails.json"), encoding="utf-8")):
        if t["TrailName"] == name:
            return wkt_lines(t["Geometry"])
    raise KeyError(name)


def chain(frags, start):
    """把碎片依端點接成一條：從離 start 最近的端點開始，每次接上端點最近的碎片。"""
    frags = [f for f in frags if len(f) >= 2 and sum(hav(a, b) for a, b in zip(f, f[1:])) > 5]
    line, cur = [], start
    while frags:
        best = None
        for i, f in enumerate(frags):
            for rev in (False, True):
                g = f[::-1] if rev else f
                d = hav(cur, g[0])
                if best is None or d < best[0]:
                    best = (d, i, g)
        if best[0] > JOIN_M:
            break
        line += best[2][1:] if line and hav(line[-1], best[2][0]) < 1 else best[2]
        cur = line[-1]
        frags.pop(best[1])
    return line, len(frags)


def kml_points(text):
    out = []
    for pm in re.findall(r"<Placemark[^>]*>(.*?)</Placemark>", text, re.S):
        nm = re.search(r"<name>(.*?)</name>", pm, re.S)
        c = re.search(r"<Point>.*?<coordinates>(.*?)</coordinates>", pm, re.S)
        if nm and c:
            x, y = map(float, c.group(1).split(",")[:2])
            out.append((nm.group(1).strip(), x, y))
    return out


def resample(pts):
    out, carry = [pts[0]], 0.0
    for a, b in zip(pts, pts[1:]):
        d = hav(a, b)
        t = STEP - carry
        while t <= d:
            f = t / d
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            t += STEP
        carry = d - (t - STEP)
    if hav(out[-1], pts[-1]) > 1:
        out.append(pts[-1])
    return out


def build():
    T = {}
    jsy = dict(kml_lines(open(os.path.join(RAW, "rec-122-jinshuiying.kml"), encoding="utf-8").read()))
    T["jinshuiying"] = (jsy["浸水營國家步道(西段)"] + jsy["浸水營國家步道(東段)"][1:],
                        "林業及自然保育署 台灣山林悠遊網 KML（tr_id=122）的「西段」＋「東段」")
    west = kmz_lines(os.path.join(RAW, "forest-38461-nenggao-w.kmz"))[0][1]
    east, left = chain(mot("能高越嶺道：東段"), west[-1])
    # 最後幾段碎片越過東段登山口又往回爬，在離官方東段登山口（TWD97 284083, 2658311）最近的點截斷
    cut = min(range(len(east)), key=lambda i: hav(east[i], EAST_GATE))
    east = east[:cut + 1]
    T["nenggao"] = (west + east, "西段：林業保育署軌跡圖 065（資料集 38461）；東段：交通部觀光署步道資料（資料集 41653）的 104 段碎片依端點接成（剩 %d 段接不上，已略過）" % left)
    T["xiakeluo"] = (kmz_lines(os.path.join(RAW, "forest-26999-xiakeluo.kmz"))[0][1][::-1], "林業保育署軌跡圖 026（資料集 26999），反轉為石鹿→養老")
    T["fuba"] = (mot("福巴越嶺國家步道")[0], "交通部觀光署步道資料（資料集 41653）")
    T["batongguan"] = (kmz_lines(os.path.join(RAW, "forest-31149-batongguan-luming.kmz"))[0][1][::-1], "林業保育署軌跡圖 154（資料集 31149），反轉為西側入口→東側出口")
    out = {}
    for k, (pts, src) in T.items():
        rs = resample(pts)
        out[k] = {"src": src, "step": STEP, "pts": [[round(x, 6), round(y, 6), round(sample(y, x)[0], 1)] for x, y in rs]}
        print("%-11s %5.1f 公里  %4d 點  %s" % (k, (len(rs) - 1) * STEP / 1000, len(rs), src))
    pois = {}
    for k, fn in (("jinshuiying", "rec-122-jinshuiying.kml"), ("batongguan", "rec-154-batongguan-luming.kml")):
        pois[k] = [[n, round(x, 6), round(y, 6), round(sample(y, x)[0], 1)] for n, x, y in kml_points(open(os.path.join(RAW, fn), encoding="utf-8").read())]
    out["_pois"] = pois
    with open(os.path.join(RAW, "tracks.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    build()
