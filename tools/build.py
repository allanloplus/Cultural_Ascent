#!/usr/bin/env python3
"""產生 data/alt.json（單元 1「文資住在多高」的全部資料）。只用 Python 標準函式庫。

讀取（只讀、不修改）：
  data/raw/elev.json                        每處文資的推估海拔與本島陸地高度分布（tools/build_elev.py 產生）
  ../Cultural_Atlas/data/sites.json         全臺有形文資主檔
  ../Cultural_Heritage、../Cultural_Heritage2 各縣市 data/ 的 images.json、sites-content.json
  ../Cultural_Rail/data/lines/*.json        鐵道版各線車站步行可達的文資（有的話卡片加連結）
可用環境變數 ATLAS_DIR、CH1_DIR、CH2_DIR、RAIL_DIR 指定資料夾位置。

海拔的採用規則（頁面上都標「推估」）：
  1. 預設用 Copernicus DEM（30 公尺）在文資座標點的值。
  2. 知識網站的介紹文字若寫明海拔（例如「海拔約2413公尺」），且與推估差超過 TEXT_TOL 公尺且超過 5%，
     改用文字的數字，標示「依介紹文字」；兩者差這麼多，幾乎都是座標點不在文資本體上。
  3. 座標周圍約 210 公尺見方內高低差超過 STEEP_M，標示「陡坡，海拔可能差很多」。
"""
import collections, datetime, glob, json, math, os, re, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UP = os.path.dirname(ROOT)
ATLAS = os.environ.get("ATLAS_DIR", os.path.join(UP, "Cultural_Atlas"))
CH1 = os.environ.get("CH1_DIR", os.path.join(UP, "Cultural_Heritage"))
CH2 = os.environ.get("CH2_DIR", os.path.join(UP, "Cultural_Heritage2"))
RAIL = os.environ.get("RAIL_DIR", os.path.join(UP, "Cultural_Rail"))
RAIL_URL = "https://cultural-rail.123hi.org/"

TEXT_TOL = 50       # 介紹文字的海拔與推估相差超過這個值（且超過 5%）就改用文字
STEEP_M = 100       # 座標周圍高低差超過這個值：標示陡坡
HIGH = 500          # 「上山」的門檻
MAIN = (21.8, 25.4, 120.0, 122.1)   # 本島範圍（含綠島、蘭嶼、龜山島），與陸地分布的範圍相同
BANDS = [0, 20, 100, 500, 1000]     # 頁面上的高度帶

# 500 公尺以上的文資「為什麼在山上」：依名稱與知識網站主題標籤歸類，依序比對，先符合者為準
REASONS = [
    ("road", "道路、古道與橋梁", re.compile("橋|古道|公路|隧道|茶亭"), set()),
    ("guard", "理蕃、隘勇與番界", re.compile("隘勇|駐在所|理蕃|巡查|彈藥|監督所|越界|番學堂|社學堂"), {"警政理蕃"}),
    ("forest", "林業與森林鐵道", re.compile("阿里山|太平山|奮起湖|樹靈塔"), {"鐵道林業", "林業鐵道"}),
    ("indig", "原住民族舊社與史前遺址", re.compile("部落|舊社|聚落|考古|起源地|自力更生"), {"原住民部落", "原住民族文化", "考古原住民", "考古遺址", "考古史前"}),
]
OTHER = ("other", "其他（茶廠、墓園、故居、教堂等）")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def med(a):
    return statistics.median(a) if a else None


def fmt(n):
    return f"{int(round(n)):,}"


def pct(a, b):
    v = a / b * 100
    return f"{v:.1f}" if v < 10 else f"{round(v)}"


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y); mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return num / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


def main_island(o):
    return MAIN[0] < o["lat"] < MAIN[1] and MAIN[2] < o["lng"] < MAIN[3]


# ---------- 讀資料 ----------
atlas = load(os.path.join(ATLAS, "data", "sites.json"))
F = atlas["meta"]["fields"]
COUNTIES, ERAS, CATS = atlas["counties"], atlas["eras"], atlas["cats"]
sites = [dict(zip(F, r)) for r in atlas["sites"]]
EL = load(os.path.join(ROOT, "data", "raw", "elev.json"))
LAND = EL["land"]

extra = {}
for ci, c in enumerate(COUNTIES):
    repo = CH2 if "cultural2." in c["base"] else CH1
    d = os.path.join(repo, c["slug"], "data")
    for k, v in load(os.path.join(d, "images.json")).items():
        if v:
            extra.setdefault((ci, k), {})["img"] = v[0]
    for o in load(os.path.join(d, "sites-content.json")):
        extra.setdefault((ci, o["id"]), {}).update(themes=o.get("themes") or [], text=(o.get("intro") or "") + " " + " ".join(o.get("highlights") or []),
                                                   coord=o.get("coordNote") or "")

rail = {}
for p in sorted(glob.glob(os.path.join(RAIL, "data", "lines", "*.json"))):
    L = load(p)
    for s in L["stations"]:
        for o in s["sites"]:
            k = (o["c"], o["i"])
            if k not in rail or o["m"] < rail[k][3]:
                rail[k] = [L["id"], s["id"], s["name"], o["m"], L["name"]]
print(f"鐵道版：{len(rail)} 處文資有車站步行可達" if rail else "注意：找不到 Cultural_Rail，卡片不會有鐵道連結")


LIC = []   # 授權條款表：[名稱, 網址]，照片用索引引用，省檔案大小


def photo(ci, im):
    """[小圖, 大圖, 作者, 授權索引, Commons 檔名]；本機圖檔存相對於縣市網址的路徑（網頁再補上前綴）。"""
    lic = [im.get("license") or "", im.get("licenseUrl") or ""]
    if lic not in LIC:
        LIC.append(lic)
    if im.get("local"):
        s, l = im.get("small") or im["local"], im["local"]
    else:
        s = l = im["thumb"]
    pg = im.get("page") or ""
    pg = pg.split("/wiki/File:", 1)[1] if "/wiki/File:" in pg else pg
    return [s, l, im.get("artist") or "", LIC.index(lic), pg]


ELEV_TXT = re.compile(r"海拔(?:約|高約|高達|將近|近)?\s*([\d,]+)(?:\s*[~～至到\-–]\s*([\d,]+))?\s*(?:多)?公尺(以上)?")

# ---------- 每處文資的海拔 ----------
checks = []
for x in sites:
    key = (x["county"], x["id"])
    ex = extra.get(key, {})
    dem, rel = EL["sites"]["%s/%s" % (COUNTIES[x["county"]]["slug"], x["id"])]
    x["dem"], x["rel"], x["h"], x["flag"] = dem, rel, dem, ""
    m = ELEV_TXT.search(ex.get("text", ""))
    if m:
        a = int(m.group(1).replace(",", "")); b = int(m.group(2).replace(",", "")) if m.group(2) else None
        ref = (a + b) / 2 if b else a
        checks.append((x, ref, m.group(0)))
        if abs(dem - ref) > max(TEXT_TOL, ref * 0.05):
            x["h"], x["flag"] = ref, "txt"
            x["note"] = f"介紹文字寫「{m.group(0)}」，座標點推估 {fmt(dem)} 公尺，兩者相差 {fmt(abs(dem - ref))} 公尺，採用文字；座標點可能不在文資本體上。"
    if not x["flag"] and rel > STEEP_M:
        x["flag"] = "steep"
        x["note"] = f"座標周圍約 200 公尺內高低差 {fmt(rel)} 公尺，座標稍有偏差，海拔就可能差很多。"
    if "未能核對" in ex.get("coord", ""):
        x["note"] = (x.get("note", "") + "知識網站註明此處座標未能核對。").strip()
        if not x["flag"]:
            x["flag"] = "coord"
    x["reason"] = None
    if x["h"] >= HIGH:
        th = set(ex.get("themes", []))
        for rid, _, rx, ts in REASONS:
            if rx.search(x["name"]) or (th & ts):
                x["reason"] = rid; break
        else:
            x["reason"] = OTHER[0]

n = len(sites)
H = [x["h"] for x in sites]
diffs = [x["dem"] - ref for x, ref, _ in checks]
adopted = [x for x in sites if x["flag"] == "txt"]
agree = [d for (x, ref, _), d in zip(checks, diffs) if x["flag"] != "txt"]
print(f"介紹文字寫有海拔：{len(checks)} 處；與推估的中位差 {med([abs(d) for d in diffs]):.0f} 公尺；改用文字 {len(adopted)} 處")
for x in adopted:
    print("   改用文字：", x["name"], x["note"])

# ---------- 統計 ----------
def by(key, groups):
    out = []
    for gi, g in enumerate(groups):
        a = [x["h"] for x in sites if x[key] == gi]
        if a:
            out.append({"i": gi, "name": g["name"], "n": len(a), "med": round(med(a)), "p90": round(sorted(a)[int(len(a) * .9)]),
                        "high": sum(1 for v in a if v >= HIGH)})
    return out


era_stats = by("era", ERAS)
cat_stats = by("cat", CATS)
county_top, county_stats = [], []
for ci, c in enumerate(COUNTIES):
    a = [x for x in sites if x["county"] == ci]
    t = max(a, key=lambda x: x["h"])
    county_stats.append({"c": ci, "n": len(a), "med": round(med([x["h"] for x in a]))})
    county_top.append({"c": ci, "i": t["id"], "h": round(t["h"]), "med": round(med([x["h"] for x in a])), "n": len(a)})
county_top.sort(key=lambda r: -r["h"])

main = [x for x in sites if main_island(x)]
main_high = sum(1 for x in main if x["h"] >= HIGH)
main_1000 = sum(1 for x in main if x["h"] >= 1000)

band_rows = []
for lo, hi in zip(BANDS, BANDS[1:] + [None]):
    a = [x for x in sites if x["h"] >= lo and (hi is None or x["h"] < hi)]
    am = [x for x in main if x["h"] >= lo and (hi is None or x["h"] < hi)]
    land = LAND["over"].get(str(lo), 1.0) - (LAND["over"].get(str(hi), 0.0) if hi else 0.0) if lo else 1 - LAND["over"]["20"]
    yrs = [x["year"] for x in a if x["year"] is not None]
    band_rows.append({"lo": lo, "hi": hi, "n": len(a), "share": round(len(am) / len(main), 4), "land": round(land, 4),
                      "year": round(med(yrs)) if yrs else None,
                      "eras": [sum(1 for x in a if x["era"] == e) for e in range(len(ERAS))]})

dated = [x for x in main if x["year"] is not None]
rho = spearman([x["h"] for x in dated], [x["year"] for x in dated])
built = [x for x in dated if x["cat"] != 6]
rho_b = spearman([x["h"] for x in built], [x["year"] for x in built])
high_old = sorted([x for x in sites if x["h"] >= HIGH and x["year"] is not None and x["cat"] != 6], key=lambda x: x["year"])
print(f"海拔與創建年的等級相關：全部 {rho:.3f}，不含考古遺址 {rho_b:.3f}")

top10 = sorted(sites, key=lambda x: -x["h"])[:10]
high = [x for x in sites if x["h"] >= HIGH]
rc = collections.Counter(x["reason"] for x in high)

# ---------- 開頭的事實 ----------
def ids(lst):
    return [f"{x['county']}/{x['id']}" for x in lst]


facts = []
low_half = [x for x in sites if x["h"] <= med(H)]
facts.append({"k": "一半的文資", "big": fmt(med(H)), "unit": "公尺以下",
              "t": f"全臺 {fmt(n)} 處文資的海拔中位數只有 {fmt(med(H))} 公尺；臺灣本島陸地的中位數是 {fmt(LAND['median'])} 公尺。一般人住在平地，文資也是。",
              "band": [0, round(med(H))]})
facts.append({"k": "山很多，文資很少", "big": pct(main_high, len(main)), "unit": f"%・{HIGH} 公尺以上",
              "t": f"本島 {round(LAND['over'][str(HIGH)] * 100)}% 的土地在 {HIGH} 公尺以上，本島 {fmt(len(main))} 處文資只有 {main_high} 處在那裡；"
                   f"1,000 公尺以上的土地佔 {round(LAND['over']['1000'] * 100)}%，文資 {main_1000} 處。",
              "band": [HIGH, 4000]})
yr = [b for b in band_rows if b["year"] is not None]
young = rho > 0.2
facts.append({"k": "越往山上越年輕？", "big": "成立" if young else "不成立", "unit": f"相關係數 {rho:.2f}",
              "t": "各高度帶文資創建年的中位數：" + "、".join(f"{b['lo']:,}–{b['hi']:,} 公尺 {b['year']} 年" if b["hi"] else f"{b['lo']:,} 公尺以上 {b['year']} 年" for b in yr) +
                   f"，看不出往高處變新的趨勢。{HIGH} 公尺以上最老的建造物是" +
                   "、".join(dict.fromkeys(x["name"].split("(")[0] for x in high_old[:3])) + "，創建年多為推估。",
              "ids": ids(high_old[:6])})
e_sorted = sorted([e for e in era_stats if e["n"] >= 20], key=lambda e: e["med"])
low_eras = [e for e in e_sorted if e["med"] == e_sorted[0]["med"]]
def where(ei):
    cc = collections.Counter(x["county"] for x in sites if x["era"] == ei).most_common(2)
    return "、".join(f"{COUNTIES[c]['name']} {k} 處" for c, k in cc)
facts.append({"k": "最靠海的時代", "big": fmt(e_sorted[0]["med"]), "unit": "公尺・" + "與".join(e["name"] for e in low_eras),
              "t": "各時代文資的海拔中位數：" + "、".join(f"{e['name']} {e['med']} 公尺" for e in e_sorted) + "。" +
                   "；".join(f"{e['name']}時期 {e['n']} 處裡，{where(e['i'])}" for e in low_eras) + "，都在海邊的平地。",
              "era": [e["i"] for e in low_eras]})
nat = [x for x in sites if x["cat"] == 0]
nat_hi = sorted([x for x in nat if x["h"] >= 200], key=lambda x: -x["h"])
c_sorted = sorted(cat_stats, key=lambda c: c["med"])
facts.append({"k": "國定古蹟住得最低", "big": fmt(c_sorted[0]["med"]), "unit": "公尺・國定古蹟中位數" if c_sorted[0]["i"] == 0 else "公尺",
              "t": f"{len(nat)} 處國定古蹟只有 {len(nat_hi)} 處在 200 公尺以上（{'、'.join(x['name'] for x in nat_hi)}）。"
                   f"中位數最高的是{c_sorted[-1]['name']}（{c_sorted[-1]['med']} 公尺）與{c_sorted[-2]['name']}（{c_sorted[-2]['med']} 公尺）。",
              "cat": [0]})
rs = [(rid, name, rc[rid]) for rid, name, *_ in REASONS + [OTHER] if rc[rid]]
rs.sort(key=lambda r: -r[2])
push = [x for x in high if x["reason"] in ("forest", "guard", "road")]
facts.append({"k": "為什麼上山", "big": str(len(high)), "unit": f"處在 {HIGH} 公尺以上",
              "t": "依名稱與主題歸類：" + "、".join(f"{name} {c} 處" for _, name, c in rs) +
                   f"。為伐木、理蕃與開路而上山的合計 {len(push)} 處，其中 {sum(1 for x in push if (x['year'] or 0) >= 1895)} 處建於日治以後；原住民族舊社與史前遺址則是原本就在山上。",
              "ids": ids(high)})

out_sites = []
for x in sites:
    ex = extra.get((x["county"], x["id"]), {})
    o = {"c": x["county"], "i": x["id"], "n": x["name"], "k": x["cat"], "y": x["year"], "e": x["estimated"], "r": x["era"],
         "h": round(x["h"]), "s": x["summary"], "t": x["town"]}
    if x["flag"]:
        o["f"] = x["flag"]; o["fn"] = x["note"]
        if x["flag"] == "txt":
            o["dem"] = round(x["dem"])
    if x["reason"]:
        o["why"] = x["reason"]
    if ex.get("img"):
        o["p"] = photo(x["county"], ex["img"])
    rr = rail.get((x["county"], x["id"]))
    if rr:
        o["rl"] = rr
    out_sites.append(o)
order = {(x["county"], x["id"]): i for i, x in enumerate(sites)}

doc = {
    "meta": {"generated": datetime.date.today().isoformat(), "total": n, "median": round(med(H)), "mainN": len(main),
             "high": HIGH, "steep": STEEP_M, "railUrl": RAIL_URL,
             "check": {"n": len(checks), "medAbs": round(med([abs(d) for d in diffs])), "agree": len(agree), "adopted": len(adopted),
                       "agreeMedAbs": round(med([abs(d) for d in agree])) if agree else None},
             "flags": {k: sum(1 for x in sites if x["flag"] == k) for k in ("txt", "steep", "coord")},
             "rho": round(rho, 3), "rhoBuilt": round(rho_b, 3),
             "dem": {"source": EL["source"], "attribution": EL["attribution"], "disclaimer": EL["disclaimer"]}},
    "eras": ERAS, "cats": CATS,
    "counties": [{"name": c["name"], "base": c["base"]} for c in COUNTIES], "lic": LIC,
    "land": {"step": LAND["step"], "share": LAND["share"], "median": LAND["median"], "over": LAND["over"]},
    "bands": band_rows, "eraStats": era_stats, "catStats": cat_stats, "countyTop": county_top,
    "top10": [order[(x["county"], x["id"])] for x in top10],
    "reasons": [{"id": rid, "name": name, "n": c} for rid, name, c in rs],
    "facts": facts, "sites": out_sites,
    "checks": sorted([[order[(x["county"], x["id"])], t, round(x["dem"]), round(ref)] for x, ref, t in checks], key=lambda r: -r[3]),
}
with open(os.path.join(ROOT, "data", "alt.json"), "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))

print(f"完成：{n} 處；中位數 {med(H):.1f} 公尺；陡坡 {doc['meta']['flags']['steep']} 處、座標未核對 {doc['meta']['flags']['coord']} 處")
for f_ in facts:
    print(f"  [{f_['k']}] {f_['big']} {f_['unit']}｜{f_['t']}")
print("最高的十處：", "、".join(f"{x['name']} {round(x['h'])}" for x in top10))
for rid, name, c in rs:
    print(f"  {name}：", "、".join(x["name"] for x in high if x["reason"] == rid))
print("檔案大小：", os.path.getsize(os.path.join(ROOT, "data", "alt.json")))
