#!/usr/bin/env python3
"""產生 data/rivers.json（單元 2「溯河而上」）。只用 Python 標準函式庫。

讀取：data/raw/rivers/stems.json（tools/river_stem.py 推算的主流與支線）
      data/raw/wra/river-basic.json（水利署河川基本資料：官方主流長度）
      data/alt.json（單元 1：每處文資的海拔與屬性，順序同文資地圖集 sites.json）
      ../Cultural_Atlas/data/sites.json（座標）、../Cultural_Atlas/data/risk.json（淹水潛勢）

收錄規則（頁面上都標「推估」）：
  - 文資到主流或支線的最近距離 ≤ BUF[河]（淡水河 1 公里、濁水溪 2 公里），且在該河的流域範圍內。
  - 距出海口公里數：投影到最近的一點，沿推算的河道量；支線＝匯流點公里數＋支線上的公里數。
  - 左右岸：面向下游，左手邊為左岸（水利署慣例）。
"""
import collections, datetime, json, math, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ATLAS = os.environ.get("ATLAS_DIR", os.path.join(os.path.dirname(ROOT), "Cultural_Atlas"))

DONE = [
    dict(id="danshui", name="淡水河", buf=1.0, color="#1d5fae", main="主流（淡水河－大漢溪）",
         intro="淡水河從石門水庫上游的大漢溪一路流到淡水出海，新店溪、基隆河在臺北盆地匯入。"),
    dict(id="zhuoshui", name="濁水溪", buf=2.0, color="#a85a1c", main="主流",
         intro="濁水溪從合歡山流到彰化、雲林交界出海，是臺灣最長的河。沿岸文資不多，收錄範圍放寬到 2 公里。"),
]
SKIP = [dict(id="lanyang", name="蘭陽溪"), dict(id="gaoping", name="高屏溪"), dict(id="zengwen", name="曾文溪")]
FLOOD = 2          # 淹水潛勢情境：24 小時 650 毫米
FLOOD_MIN = 3      # 深度代碼 3＝0.5–1 公尺以上
BIN = 5            # 散佈圖與密度：每 5 公里一段
WIN = 2            # 最密集河段的視窗（公里）
FLOOD_NOTE = "淹水潛勢為經濟部水利署第三代淹水潛勢圖（2018 年）在文資位置的模擬淹水深度，沿用文資地圖集的套疊結果。依《水災潛勢資料公開辦法》僅供防救災使用，不得作為土地使用管制或開發限制的依據；模擬假設防洪設施正常運作，結果具不確定性。"


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def xy(lng, lat, lat0):
    return (lng * 111.32 * math.cos(math.radians(lat0)), lat * 110.57)


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
    rx, ry = rank(x), rank(y); mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0


def theil_sen(x, y):
    s = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x)) if x[j] != x[i]]
    return statistics.median(s) if s else 0


def fmt(n):
    return f"{int(round(n)):,}"


def project(stems, lat0, p):
    """回傳 (支線序號, 線上公里數, 距離公里, 左右岸)。"""
    best = None
    for si, st in enumerate(stems):
        P = st["_xy"]
        for i in range(len(P) - 1):
            ax, ay = P[i]; bx, by = P[i + 1]
            dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy or 1e-12
            t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
            qx, qy = ax + t * dx, ay + t * dy
            dd = math.hypot(p[0] - qx, p[1] - qy)
            if best is None or dd < best[2]:
                # 面向下游（往公里數變小的方向）：向量 (a - b)；site 在其左側為左岸
                cross = (ax - bx) * (p[1] - by) - (ay - by) * (p[0] - bx)
                best = (si, st["km"][i] + t * (st["km"][i + 1] - st["km"][i]), dd, "L" if cross > 0 else "R")
    return best


def point_in(poly, x, y):
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def main():
    ST = load(os.path.join(ROOT, "data", "raw", "rivers", "stems.json"))["rivers"]
    OFF = {r["rivername"]: float(r["lengthofmainriver"]) for r in load(os.path.join(ROOT, "data", "raw", "wra", "river-basic.json"))["records"] if r.get("lengthofmainriver")}
    ALT = load(os.path.join(ROOT, "data", "alt.json"))
    A = load(os.path.join(ATLAS, "data", "sites.json")); F = A["meta"]["fields"]
    coords = [dict(zip(F, r)) for r in A["sites"]]
    risk = load(os.path.join(ATLAS, "data", "risk.json"))["sites"]
    sites = ALT["sites"]
    ERAS = ALT["eras"]

    def system(R):
        st = ST[R["id"]]
        lat0 = statistics.fmean(p[1] for p in st["pts"])
        stems = [{"id": "main", "name": R.get("main", "主流"), "pts": st["pts"], "km": st["km"], "at": 0}]
        for b in st.get("branches", []):
            stems.append({"id": b["id"], "name": b["name"], "pts": b["pts"], "km": b["km"], "at": b["at"]})
        for s in stems:
            s["_xy"] = [xy(p[0], p[1], lat0) for p in s["pts"]]
        basin = st["basinGeo"]
        lo = [min(p[0] for p in basin), min(p[1] for p in basin), max(p[0] for p in basin), max(p[1] for p in basin)]
        found = []
        for i, o in enumerate(coords):
            if not (lo[0] <= o["lng"] <= lo[2] and lo[1] <= o["lat"] <= lo[3]):
                continue
            if not point_in(basin, o["lng"], o["lat"]):
                continue
            si, k, d, side = project(stems, lat0, xy(o["lng"], o["lat"], lat0))
            found.append((i, si, k, d, side))
        return stems, found, lat0

    out_done = []
    for R in DONE:
        stems, found, lat0 = system(R)
        near = [f for f in found if f[3] <= R["buf"]]
        rows = []
        for i, si, k, d, side in near:
            s = stems[si]
            j = min(range(len(s["km"])), key=lambda j: abs(s["km"][j] - k))
            fl = risk[i][3][FLOOD] if risk[i] and risk[i][3] else 0
            rows.append({"i": i, "s": si, "k": round(k, 2), "m": round(k + s["at"], 2), "d": round(d * 1000), "b": side, "rh": round(s["pts"][j][2]), "fl": fl})
        rows.sort(key=lambda r: r["m"])
        n = len(rows)
        # ---------- 事實 ----------
        facts = []
        dated = [r for r in rows if sites[r["i"]]["y"] is not None and sites[r["i"]]["k"] != 6]
        xs = [r["m"] for r in dated]; ys = [sites[r["i"]]["y"] for r in dated]
        rho = spearman(xs, ys) if len(dated) > 5 else 0
        slope = theil_sen(xs, ys) if len(dated) > 5 else 0
        bins = collections.defaultdict(list)
        for r in dated:
            bins[int(r["m"] // BIN)].append(sites[r["i"]]["y"])
        binmed = [[b * BIN, (b + 1) * BIN, len(v), round(statistics.median(v))] for b, v in sorted(bins.items())]
        good = [b for b in binmed if b[2] >= 5]
        if abs(rho) >= 0.3:
            t = f"{len(dated)} 處有創建年的文資，距出海口越遠{'越晚' if rho > 0 else '越早'}（等級相關係數 {rho:.2f}）；粗估每往上游 10 公里，創建年{'晚' if slope > 0 else '早'}約 {abs(slope) * 10:.0f} 年。"
        else:
            t = f"{len(dated)} 處有創建年的文資，創建年和距出海口的距離幾乎沒有關係（等級相關係數 {rho:.2f}），看不出沿河往上游開發越晚的趨勢。"
        if good:
            t += "每 5 公里一段的中位創建年：" + "、".join(f"{b[0]}–{b[1]} 公里 {b[3]} 年（{b[2]} 處）" for b in good[:6]) + "。"
        if len(dated) < 50:
            t += f"只有 {len(dated)} 處，樣本少，趨勢僅供參考。"
        facts.append({"k": "開墾有沒有往上游推進", "big": ("成立" if rho >= .3 else "相反" if rho <= -.3 else "看不出來"), "unit": f"相關係數 {rho:.2f}", "t": t, "chart": "scatter"})
        # 上中下游
        L = stems[0]["km"][-1]
        thirds = [(0, L / 3), (L / 3, 2 * L / 3), (2 * L / 3, L + 1)]
        comp = []
        for lo_, hi_ in thirds:
            g = [r for r in rows if lo_ <= r["m"] < hi_]
            ec = collections.Counter(sites[r["i"]]["r"] for r in g)
            comp.append({"lo": round(lo_, 1), "hi": round(min(hi_, L), 1), "n": len(g), "eras": [ec.get(e, 0) for e in range(len(ERAS))],
                         "top": ERAS[ec.most_common(1)[0][0]]["name"] if g else None})
        facts.append({"k": "上中下游", "big": f"{round(comp[0]['n'] / n * 100) if n else 0}%", "unit": "在下游三分之一",
                      "t": "把主流的長度分成三等分：" + "、".join(f"{['下游', '中游', '上游'][j]}（{c['lo']:.0f}–{c['hi']:.0f} 公里）{c['n']} 處" + (f"，以{c['top']}最多" if c["top"] else "") for j, c in enumerate(comp)) + "。支線上的文資依距出海口的公里數歸段。",
                      "chart": "comp"})
        # 最密集的河段
        best = None
        for r in rows:
            w = [q for q in rows if r["m"] <= q["m"] < r["m"] + WIN]
            if best is None or len(w) > len(best[1]):
                best = (r["m"], w)
        towns = collections.Counter((sites[q["i"]]["c"], sites[q["i"]]["t"]) for q in best[1]).most_common(2)
        ferry = [sites[q["i"]]["n"] for q in best[1] if any(w in sites[q["i"]]["n"] for w in ("渡", "碼頭", "港", "河港"))]
        t = f"距出海口 {best[0]:.1f}–{best[0] + WIN:.1f} 公里的 {WIN} 公里內有 {len(best[1])} 處，最集中在" + "、".join(ALT["counties"][c]["name"] + tw for (c, tw), _ in towns) + "。"
        t += ("這一段的文資名稱裡有和渡口、碼頭有關的：" + "、".join(ferry[:3]) + "。") if ferry else "這一段的文資名稱裡沒有渡口或碼頭，資料不足以說它是舊河港。"
        facts.append({"k": "最密集的河段", "big": str(len(best[1])), "unit": f"處・{best[0]:.0f}–{best[0] + WIN:.0f} 公里", "t": t, "range": [round(best[0], 1), round(best[0] + WIN, 1)]})
        # 左右岸
        lc = sum(1 for r in rows if r["b"] == "L"); rc = n - lc
        more = "左岸" if lc > rc else "右岸"
        facts.append({"k": "左岸、右岸", "big": f"{lc}：{rc}", "unit": "左岸：右岸",
                      "t": f"面向下游，左手邊是左岸。{n} 處裡左岸 {lc} 處、右岸 {rc} 處，{more}多 {abs(lc - rc)} 處。" +
                           "；".join(f"{s['name']}：左 {sum(1 for r in rows if r['s'] == si and r['b'] == 'L')}、右 {sum(1 for r in rows if r['s'] == si and r['b'] == 'R')}" for si, s in enumerate(stems) if any(r["s"] == si for r in rows)) + "。"})
        fl = [r for r in rows if r["fl"] >= FLOOD_MIN]
        facts.append({"k": "淹水潛勢", "big": str(len(fl)), "unit": "處・0.5 公尺以上", "flood": 1,
                      "t": f"沿河 {n} 處裡，水利署 24 小時 650 毫米情境下模擬淹水 0.5 公尺以上的有 {len(fl)} 處" + (f"，例如" + "、".join(sites[r['i']]["n"] for r in fl[:3]) if fl else "") + "。僅供防救災參考。"})
        # 剖面：每約 0.5 公里一點
        sto = []
        for s in stems:
            prof, last = [], -9
            for kk, p in zip(s["km"], s["pts"]):
                if kk - last >= 0.5 or kk == s["km"][-1]:
                    prof.append([round(kk + s["at"], 2), round(p[2])]); last = kk
            sto.append({"id": s["id"], "name": s["name"], "at": s["at"], "len": round(s["km"][-1], 1), "src": round(s["pts"][-1][2]), "prof": prof})
        out_done.append({"id": R["id"], "name": R["name"], "buf": R["buf"], "color": R["color"], "intro": R["intro"], "official": OFF.get(R["name"]),
                         "n": n, "basinN": len(found), "stems": sto, "sites": rows, "facts": facts, "bins": binmed, "comp": comp, "rho": round(rho, 3),
                         "slope": round(slope, 3)})
        print(f"{R['name']}：主流 {stems[0]['km'][-1]:.1f} 公里（官方 {OFF.get(R['name'])}），流域內 {len(found)}、{R['buf']} 公里內 {n} 處；相關 {rho:.2f}")
        for x in facts:
            print(f"   [{x['k']}] {x['big']} {x['unit']}｜{x['t']}")

    out_skip = []
    for R in SKIP:
        stems, found, lat0 = system(R)
        n1 = sum(1 for f in found if f[3] <= 1); n2 = sum(1 for f in found if f[3] <= 2)
        ex = [sites[f[0]]["n"] for f in sorted(found, key=lambda f: f[3]) if f[3] <= 2][:4]
        out_skip.append({"id": R["id"], "name": R["name"], "len": round(stems[0]["km"][-1], 1), "official": OFF.get(R["name"]), "basinN": len(found), "n1": n1, "n2": n2, "ex": ex})
        print(f"不做 {R['name']}：流域內 {len(found)}，1 公里內 {n1}、2 公里內 {n2}")
    doc = {"meta": {"generated": datetime.date.today().isoformat(), "bin": BIN, "win": WIN, "floodNote": FLOOD_NOTE, "floodScenario": "24 小時 650 毫米",
                    "src": ["經濟部水利署 河川流域範圍圖（政府資料開放平臺 9823）", "經濟部水利署 河川支流（政府資料開放平臺 25780）", "經濟部水利署 河川基本資料（政府資料開放平臺 167895）"]},
           "rivers": out_done, "skip": out_skip}
    with open(os.path.join(ROOT, "data", "rivers.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print("檔案大小：", os.path.getsize(os.path.join(ROOT, "data", "rivers.json")))


if __name__ == "__main__":
    main()
