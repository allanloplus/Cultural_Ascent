#!/usr/bin/env python3
"""產生 data/trails.json（單元 3「越嶺古道」）。只用 Python 標準函式庫。

讀取：data/raw/trails/tracks.json（tools/trail_elev.py 產生：軌跡、每 25 公尺的海拔、點位海拔）
      data/raw/trails/ 的官方文字（林業及自然保育署、原住民族委員會、文化部文化資產局、玉山國家公園）
      data/alt.json（單元 1 的文資海拔，用來比較與找沿線文資）

歷史內容只用下面 SRC 列出的官方來源，每一句都標出處；來源之間說法不同時並列，不自行取捨。
坡度由數值地表模型算出（含樹冠），先以約 150 公尺平滑，再每 200 公尺算一段，只是概略。
"""
import datetime, json, math, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data", "raw", "trails")
SMOOTH = 3          # 平滑：前後各 3 點（約 ±75 公尺）
SEG = 8             # 坡度：每 8 點（200 公尺）一段
NEAR_KM = 3         # 沿線文資：離軌跡多少公里內
POI_M = 250         # 有座標的點位：離軌跡多少公尺內才放上剖面
GRADES = [5, 10, 20]  # 坡度分級（%）：平緩、緩坡、陡、很陡

SRC = {
    "rec064": ("林業及自然保育署 台灣山林悠遊網：能高越嶺道-西段", "https://recreation.forest.gov.tw/Trail/RT?tr_id=064"),
    "rec066": ("林業及自然保育署 台灣山林悠遊網：能高越嶺道：東段", "https://recreation.forest.gov.tw/Trail/RT?tr_id=066"),
    "rec026": ("林業及自然保育署 台灣山林悠遊網：霞喀羅國家步道", "https://recreation.forest.gov.tw/Trail/RT?tr_id=026"),
    "rec024": ("林業及自然保育署 台灣山林悠遊網：福巴越嶺國家步道", "https://recreation.forest.gov.tw/Trail/RT?tr_id=024"),
    "rec122": ("林業及自然保育署 台灣山林悠遊網：浸水營古道：西段", "https://recreation.forest.gov.tw/Trail/RT?tr_id=122"),
    "rec170": ("林業及自然保育署 台灣山林悠遊網：浸水營國家步道東段", "https://recreation.forest.gov.tw/Trail/RT?tr_id=170"),
    "rec207": ("林業及自然保育署 台灣山林悠遊網：浸水營步道：前段", "https://recreation.forest.gov.tw/Trail/RT?tr_id=207"),
    "rec154": ("林業及自然保育署 台灣山林悠遊網：八通關越道：鹿鳴吊橋段", "https://recreation.forest.gov.tw/Trail/RT?tr_id=154"),
    "mot": ("交通部觀光署 步道資料（政府資料開放平臺 41653）", "https://data.gov.tw/dataset/41653"),
    "cip": ("原住民族委員會 臺灣原住民族古道簡介資料（政府資料開放平臺 166817）", "https://data.gov.tw/dataset/166817"),
    "boch_btg": ("文化部文化資產局 國家文化資產網：八通關古道（國定古蹟）", "https://nchdb.boch.gov.tw/assets/advanceSearch/monument/19870417000001"),
    "boch_jsy": ("文化部文化資產局 國家文化資產網：浸水營古道(屏東段)（文化景觀）", "https://nchdb.boch.gov.tw/assets/advanceSearch/culturalLandscape/20150715000001"),
    "ysnp": ("玉山國家公園管理處：八通關越道", "https://www.ysnp.gov.tw/StaticPage/AncientRoad1"),
}

# 每條古道：基本資料、歷史（年份、文字、出處）、依官方里程放上剖面的點位
TRAILS = [
    dict(id="jinshuiying", name="浸水營古道", sub="國家步道西段＋東段：大漢林道 23.5K → 大武", eras=["清領", "日治"], color="#a85a1c",
         where="屏東縣春日鄉 → 臺東縣達仁鄉、大武鄉", official="全線約 47 公里（枋寮到大武）；本頁剖面是西段＋東段", rec=["rec122", "rec170"],
         history=[
             (1885, "清光緒 11 年開通；據施添福研究，為清代所修的南路之一。", "cip"),
             (None, "全線西起屏東縣枋寮，東至臺東縣大武，全長約 47 公里，原為清代撫番道路；後來古道西段多被大漢林道新路取代。", "rec207"),
             (None, "原民會的資料寫全長約 45 公里，與林業保育署的 47 公里不同。", "cip"),
             (1901, "水底寮的領路頭石碑由日人所立，往大武的旅人會在此祭拜。", "rec170"),
             (1908, "明治 41 年官方修築枋寮經浸水營到卑南的道路；日治時期是東西部之間的郵遞與電信道路，並改修為理蕃道路。", "cip"),
             (None, "清代道路沿稜線闢建，日治時期則為腰繞闢建；現有路徑以日治時期警備道路為基礎整建。", "boch_jsy"),
             (2015, "屏東縣登錄為文化景觀「浸水營古道(屏東段)」，範圍自大漢林道 23.5 公里至州廳界，約 2.5 公里。", "boch_jsy"),
             (None, "林業保育署稱它是臺灣所有橫越中央山脈的古道中，越嶺點最低、使用頻率最高、使用時間最長的一條。", "rec170"),
         ],
         posts=None, post_note="官方資料列出的駐在所遺址：坎頭營（天台宮旁）、大樹林（大漢林道 20.1K）、浸水營、出水坡、新姑仔崙、古里巴保諾、歸化開社遺址等，前四處以外的位置見下方清單。",
         off=[("清代歸化門營盤遺址", "大漢林道 7.4K", "rec170"), ("清代六儀社營盤遺址", "大漢林道 14K", "rec170"), ("大樹前營盤、大樹林駐在所遺址", "大漢林道 20.1K", "rec170"),
              ("石頭營聖蹟亭", "前段一帶", "rec170"), ("清代崁頭營原址及日警駐在所", "天台宮旁", "rec170"), ("領路頭石碑（1901 年）", "水底寮", "rec170")],
         off_note="浸水營古道全線約 47 公里，西側的前段（新開苗圃到大漢林道 5.2K，約 2.5 公里）與大漢林道 5.2K–23.5K 沒有連續的古道軌跡，剖面從大漢林道 23.5K 的西段入口開始。"),
    dict(id="nenggao", name="能高越嶺道", sub="屯原登山口 → 光被八表 → 東段登山口", eras=["日治"], color="#1d5fae",
         where="南投縣仁愛鄉 → 花蓮縣秀林鄉", official="全長 26.5 公里（光被八表在 15.5 公里處）", rec=["rec064", "rec066"],
         history=[
             (None, "原先是賽德克族原住民遷徙及貿易的社路。", "rec064"),
             (1914, "「太魯閣征伐戰役」中，能高越嶺道是日本東西部隊攻擊太魯閣群的主要路線之一。", "rec064"),
             (1917, "為控制山地興築警備道，命名為「初音奇萊橫斷道路」（能高越嶺東段的舊道）。", "rec064"),
             (1925, "因舊道東段海拔太高、冬季常積雪，重新興築越嶺道全線，即現今的能高越嶺道，完成後總里程 76.8 公里。", "rec064"),
             (None, "沿線設多處駐在所，並指定宿泊所：屯原、尾上（今雲海保線所）、富士見、能高（今天池山莊）、東能高（今檜林保線所）、邊（今磐石保線所）。", "rec064"),
             (None, "戰後台電拓建為「東電西送」的保線路，在能高鞍部立「光被八表」紀念碑；2002 年後納入國家步道系統。", "rec064"),
         ],
         kmpois=[("屯原登山口", 0, "gate", "rec066", 2150), ("雲海保線所（原尾上駐在所）", 4.5, "post", "rec066", 2360), ("松原木炭窯遺址", 8, "ruin", "rec066", 2600),
                 ("能高瀑布", 12, "spot", "rec066"), ("天池山莊（原能高駐在所）", 13, "post", "rec066", 2860), ("光被八表碑・越嶺點", 15.5, "pass", "rec066", 2787),
                 ("檜林保線所（原東能高駐在所）", 20.3, "post", "rec066"), ("東段登山口", 26.5, "gate", "rec066", 1582)],
         km_total=26.5, anchor=("光被八表", 15.5, 121.27981, 24.02916),
         posts=6, post_len=26.5, post_note="本線 26.5 公里上，官方資料點名的駐在所有屯原、富士見、尾上、松原、能高、東能高 6 處（邊駐在所在東段登山口外的奇萊路上，不計）。",
         notes=["官方頁面對光被八表的海拔有 2,787 公尺與 2,890 公尺兩種寫法，天池山莊也有 13 公里與 16 公里兩種里程；剖面上的海拔一律由地形資料推估。",
                "東段軌跡由觀光署資料的 104 段碎片依端點接成，截在離官方東段登山口最近的點，全長 25.9 公里，比官方的 26.5 公里短。"]),
    dict(id="xiakeluo", name="霞喀羅古道", sub="石鹿登山口 → 養老登山口", eras=["日治"], color="#14876b",
         where="新竹縣五峰鄉 → 尖石鄉", official="全長約 22 公里", rec=["rec026"],
         history=[
             (None, "Syakaro（霞喀羅）是泰雅族語的烏心石，因山區盛產此樹而得名；古道是早期當地部落的聯外交通要道。", "rec026"),
             (None, "沿線可見日治時期日人為討伐尖石、五峰一帶部落所修築的駐在所、電線杆、碉堡、紀念碑、土牆及砲台遺址。", "rec026"),
             (None, "官方資料沒有寫開闢年份。", None),
         ],
         kmpois=[("石鹿登山口", 0, "gate", "rec026"), ("田村台駐在所遺址", 1.2, "post", "rec026"), ("楢山駐在所遺址", 6.4, "post", "rec026"), ("朝日駐在所遺址", 10.2, "post", "rec026"),
                 ("霞喀羅吊橋", 10.6, "bridge", "rec026"), ("白石駐在所遺址", 11.8, "post", "rec026"), ("白石吊橋", 13.3, "bridge", "rec026"), ("武神駐在所遺址", 14.5, "post", "rec026"),
                 ("馬鞍駐在所遺址", 16.9, "post", "rec026"), ("栗園駐在所遺址", 18.5, "post", "rec026"), ("木炭窯", 19.3, "ruin", "rec026"), ("養老登山口", 22.2, "gate", "rec026")],
         km_total=22.2, posts=7, post_len=22.2, post_note="官方行程表從石鹿到養老共 22.2 公里，沿途 7 處駐在所遺址。",
         notes=["官方行程表各段里程合計 22.2 公里，公開軌跡只有 18.1 公里；點位依官方里程等比例放到軌跡上，只是近似位置。",
                "官方資料寫海拔 1,600–1,900 公尺，地形資料推估的最高點較高，可能是軌跡經過稜線或地表模型含樹冠。"]),
    dict(id="fuba", name="福巴越嶺古道", sub="福山（新北市烏來）→ 巴陵（桃園市復興）", eras=["日治"], color="#c08400",
         where="新北市烏來區 → 桃園市復興區", official="全長約 18 公里", rec=["rec024"],
         history=[
             (None, "古道為早年泰雅人狩獵、通婚、訪親的社路。", "mot"),
             (None, "日治時期設隘勇線，作為山地警備道路，至今仍留有駐在所的遺跡。", "mot"),
             (None, "官方資料沒有寫開闢年份，也沒有駐在所的名稱與位置。", None),
         ],
         posts=None, post_note="官方資料只寫「仍留有駐在所的遺跡」，沒有名稱與位置，所以剖面上沒有標。"),
    dict(id="batongguan", name="八通關越道", sub="只有花蓮卓溪的鹿鳴吊橋段有公開軌跡", eras=["清領", "日治"], color="#b02a2a",
         where="花蓮縣卓溪鄉（鹿鳴吊橋段）", official="清代八通關古道全長 152.64 公里；日治八通關越道約 96 公里（玉管處）或約 120 公里（原民會）", rec=["rec154"],
         history=[
             (1875, "清光緒元年，總兵吳光亮督兵三營，由林圯埔（今竹山）向東開到璞石閣（今玉里），即「八通關古道」；為牡丹社事件後「開山撫番」的中路。", "boch_btg"),
             (1987, "清代八通關古道經內政部公告為一級古蹟（今國定古蹟）。今日能通行的是整修後的八通關越嶺古道，清代古道早已廢棄不用。", "boch_btg"),
             (1919, "日治時期為壓制拉庫拉庫溪流域的布農族人，自 1919 年起興建八通關越嶺道路；鹿鳴吊橋初建於 1920 年。", "rec154"),
             (None, "開鑿年代各來源說法不同：原民會寫大正 8 年（1919）開鑿、大正 9 年（1920）完工；玉管處寫 1918–1921 年，1921 年闢建完成，全程約 96 公里。", "cip"),
             (None, "玉管處：八通關東段駐在所曾多達 40 幾處。林業保育署：沿拉庫拉庫溪流域設置 46 個警察駐在所，1945 年撤廢。", "ysnp"),
         ],
         posts=None, post_note="八通關越道全線的駐在所數量，各來源寫法不同（東段「40 幾處」、拉庫拉庫溪流域 46 處），本站只有 3.5 公里的軌跡，不計算密度。",
         notes=["公開軌跡只有鹿鳴吊橋段（官方 2.7 公里，軌跡 3.5 公里），不代表整條越道的高度。"]),
]

KIND = [("駐在所", "post"), ("營盤", "camp"), ("神社", "shrine"), ("聖蹟亭", "monument"), ("州廳界", "pass"), ("吊橋", "bridge"), ("遺址", "ruin"), ("遺跡", "ruin")]
SKIP = ("入口", "登山口", "社區", "派出所", "警察局", "休閒", "軍營", "控制點", "苖圃", "苗圃")


def hav(a, b):
    p = math.radians
    x = math.sin(p(b[1] - a[1]) / 2) ** 2 + math.cos(p(a[1])) * math.cos(p(b[1])) * math.sin(p(b[0] - a[0]) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(x))


def smooth(h):
    return [statistics.fmean(h[max(0, i - SMOOTH):i + SMOOTH + 1]) for i in range(len(h))]


def nearest(pts, lng, lat):
    best = min(range(len(pts)), key=lambda i: (pts[i][0] - lng) ** 2 + ((pts[i][1] - lat) * 1.1) ** 2)
    return best, hav(pts[best][:2], (lng, lat))


def fmt(n):
    return f"{int(round(n)):,}"


def main():
    T = json.load(open(os.path.join(RAW, "tracks.json"), encoding="utf-8"))
    ALT = json.load(open(os.path.join(ROOT, "data", "alt.json"), encoding="utf-8"))
    A = json.load(open(os.path.join(ATLAS_SITES), encoding="utf-8"))
    F = A["meta"]["fields"]
    coords = [dict(zip(F, r)) for r in A["sites"]]
    sites = ALT["sites"]
    H_all = sorted(o["h"] for o in sites)
    out = []
    for C in TRAILS:
        tr = T[C["id"]]
        pts = tr["pts"]
        step = tr["step"] / 1000
        h = smooth([p[2] for p in pts])
        n = len(pts)
        L = (n - 1) * step
        grades = []   # (起點 km, 坡度 %)
        for i in range(0, n - SEG, SEG):
            grades.append((i * step, (h[i + SEG] - h[i]) / (SEG * tr["step"]) * 100))
        absg = [abs(g) for _, g in grades]
        share = [sum(1 for g in absg if (lo is None or g >= lo) and (hi is None or g < hi)) / len(absg)
                 for lo, hi in zip([None] + GRADES, GRADES + [None])]
        steep = max(grades, key=lambda x: abs(x[1]))
        up = sum(max(0, h[i + 1] - h[i]) for i in range(n - 1))
        down = sum(max(0, h[i] - h[i + 1]) for i in range(n - 1))
        imax = max(range(n), key=lambda i: h[i])
        imin = min(range(n), key=lambda i: h[i])
        # 點位
        pois = []
        if C.get("kmpois"):
            if C.get("anchor"):
                ia, _ = nearest(pts, C["anchor"][2], C["anchor"][3])
                ka = ia * step
                m = lambda k: k / C["anchor"][1] * ka if k <= C["anchor"][1] else ka + (k - C["anchor"][1]) / (C["km_total"] - C["anchor"][1]) * (L - ka)
            else:
                m = lambda k: k / C["km_total"] * L
            for row in C["kmpois"]:
                name, k, kind, s = row[:4]
                km = min(L, m(k)); i = int(round(km / step))
                p = {"n": name, "km": round(km, 2), "h": round(h[min(i, n - 1)]), "k": kind, "pos": "km", "ok": k, "s": s}
                if len(row) > 4:
                    p["oh"] = row[4]
                pois.append(p)
        for name, x, y, ph in T["_pois"].get(C["id"], []):
            kind = next((v for kw, v in KIND if kw in name), None)
            if not kind or any(w in name for w in SKIP) and kind != "post":
                continue
            i, d = nearest(pts, x, y)
            if d <= POI_M:
                pois.append({"n": name.replace("西測入口與", "").replace("測", "側"), "km": round(i * step, 2), "h": round(h[i]), "k": kind, "pos": "xy", "d": round(d), "s": C["rec"][0]})
        pois.sort(key=lambda p: p["km"])
        ded = []
        for p in pois:   # 同一處標了兩次（例如「吊橋遺址」與「姑仔崙吊橋遺址」）只留名稱較長的
            q = next((q for q in ded if q["k"] == p["k"] and abs(q["km"] - p["km"]) < 0.2), None)
            if q and len(p["n"]) > len(q["n"]):
                ded[ded.index(q)] = p
            elif not q:
                ded.append(p)
        pois = ded
        chk = [abs(p["h"] - p["oh"]) for p in pois if "oh" in p]
        # 沿線文資（單元 1 的 3,032 處裡，離軌跡 NEAR_KM 公里內）
        near = []
        lo_lng = min(p[0] for p in pts) - .04; hi_lng = max(p[0] for p in pts) + .04
        lo_lat = min(p[1] for p in pts) - .04; hi_lat = max(p[1] for p in pts) + .04
        for si, o in enumerate(coords):
            if lo_lng <= o["lng"] <= hi_lng and lo_lat <= o["lat"] <= hi_lat:
                i, d = nearest(pts, o["lng"], o["lat"])
                if d <= NEAR_KM * 1000:
                    near.append({"i": si, "km": round(i * step, 1), "d": round(d / 1000, 1)})
        above = sum(1 for v in H_all if v < h[imax]) / len(H_all)
        prof = [[round(i * step, 3), round(h[i])] for i in range(0, n, 2)] + ([[round(L, 3), round(h[-1])]] if (n - 1) % 2 else [])
        stats = {"len": round(L, 1), "max": round(h[imax]), "maxKm": round(imax * step, 1), "min": round(h[imin]), "start": round(h[0]), "end": round(h[-1]),
                 "up": round(up), "down": round(down), "medGrade": round(statistics.median(absg), 1), "share": [round(x, 3) for x in share],
                 "steep": [round(steep[0], 1), round(steep[1], 1)], "above": round(above, 4),
                 "postGap": round(C["post_len"] / C["posts"], 1) if C.get("posts") else None,
                 "ohDiff": [min(chk), max(chk)] if chk else None}
        t = {k: C[k] for k in ("id", "name", "sub", "eras", "color", "where", "official")}
        t.update(stats=stats, profile=prof, grades=[[round(k, 2), round(g, 1)] for k, g in grades], pois=pois, near=near,
                 history=[{"y": y, "t": txt, "s": s} for y, txt, s in C["history"]], rec=C["rec"], src=tr["src"],
                 posts=C.get("posts"), postNote=C.get("post_note"), notes=C.get("notes", []),
                 off=[{"n": a, "w": b, "s": c} for a, b, c in C.get("off", [])], offNote=C.get("off_note"))
        out.append(t)
        print(f"{C['name']}：{L:.1f} 公里，最高 {h[imax]:.0f}（{imax * step:.1f} km），坡度中位 {stats['medGrade']}%，"
              f"<5% {share[0]:.0%}、5–10 {share[1]:.0%}、10–20 {share[2]:.0%}、≥20 {share[3]:.0%}；點位 {len(pois)}；沿線文資 {len(near)}")
        for nn in near:
            print("     沿線文資：", sites[nn["i"]]["n"], nn["d"], "km")

    # ---------- 總覽的事實 ----------
    by = {t["id"]: t for t in out}
    top = max(out, key=lambda t: t["stats"]["max"])
    hmax_site = max(sites, key=lambda o: o["h"])
    facts = []
    facts.append({"k": "比所有文資都高", "big": fmt(top["stats"]["max"]), "unit": f"公尺・{top['name']}",
                  "t": f"{top['name']}的最高處推估約 {fmt(top['stats']['max'])} 公尺，比全臺 {fmt(len(sites))} 處文資裡最高的{hmax_site['n']}（{fmt(hmax_site['h'])} 公尺）還高 {fmt(top['stats']['max'] - hmax_site['h'])} 公尺。",
                  "tr": top["id"]})
    j = by["jinshuiying"]["stats"]
    facts.append({"k": "從山頂走到海口", "big": fmt(j["start"]), "unit": "公尺 → 海邊",
                  "t": f"浸水營古道的剖面從大漢林道 23.5K 的 {fmt(j['start'])} 公尺開始，{j['len']} 公里後下到約 {fmt(j['end'])} 公尺的大武一側，五條裡只有它走到海邊。最高處約 {fmt(j['max'])} 公尺，比能高越嶺道低 {fmt(by['nenggao']['stats']['max'] - j['max'])} 公尺。",
                  "tr": "jinshuiying"})
    gentle = sorted([t for t in out if t["stats"]["len"] >= 10], key=lambda t: t["stats"]["share"][0] + t["stats"]["share"][1], reverse=True)
    facts.append({"k": "腰繞的路", "big": f"{round((gentle[0]['stats']['share'][0] + gentle[0]['stats']['share'][1]) * 100)}%", "unit": f"坡度 10% 以下・{gentle[0]['name']}",
                  "t": "每 200 公尺算一段坡度，坡度在 10% 以下的比例：" + "、".join(f"{t['name']} {round((t['stats']['share'][0] + t['stats']['share'][1]) * 100)}%" for t in gentle) +
                       "（八通關越道只有 3.5 公里，不列入）。文資局在浸水營的登錄資料指出，清代道路沿稜線、日治改為腰繞，現有路徑以日治警備道為基礎；清代沿稜線的路沒有公開軌跡，所以資料無法直接比較兩個時代的坡度。",
                  "tr": gentle[0]["id"]})
    pg = [t for t in out if t["stats"]["postGap"]]
    facts.append({"k": "幾公里一個駐在所", "big": str(min(t["stats"]["postGap"] for t in pg)), "unit": "公里・" + min(pg, key=lambda t: t["stats"]["postGap"])["name"],
                  "t": "依官方資料點名的駐在所與步道長度：" + "、".join(f"{t['name']} {t['posts']} 處，約每 {t['stats']['postGap']} 公里一處" for t in pg) +
                       "。浸水營與福巴的官方資料沒有完整的駐在所清單，八通關越道只有一小段軌跡，都不計算。", "tr": pg[0]["id"]})
    nn = sum(len(t["near"]) for t in out)
    facts.append({"k": "沿線的文資", "big": str(nn), "unit": f"處・離軌跡 {NEAR_KM} 公里內",
                  "t": f"單元 1 的 {fmt(len(sites))} 處文資，離這五條古道 {NEAR_KM} 公里內的只有 {nn} 處。古道上的駐在所與營盤遺址大多沒有登錄為文資，所以本單元的歷史內容取自林業保育署、原民會、文資局與玉管處的公開資料。",
                  "tr": None})
    years = sorted({(h["y"], t["name"]) for t in out for h in t["history"] if h["y"]})
    doc = {"meta": {"generated": datetime.date.today().isoformat(), "grades": GRADES, "nearKm": NEAR_KM, "seg": SEG * 25, "smooth": (2 * SMOOTH + 1) * 25,
                    "status": "https://recreation.forest.gov.tw/Trail/", "permit": "https://nv2.npa.gov.tw/NM107-604Client/", "park": "https://hike.taiwan.gov.tw/",
                    "ysStatus": "https://www.ysnp.gov.tw/Trail/Status", "highSite": ALT["sites"].index(hmax_site)},
           "src": {k: list(v) for k, v in SRC.items()}, "facts": facts, "timeline": [[y, n] for y, n in years], "trails": out}
    with open(os.path.join(ROOT, "data", "trails.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    for x in facts:
        print(f"  [{x['k']}] {x['big']} {x['unit']}｜{x['t']}")
    print("檔案大小：", os.path.getsize(os.path.join(ROOT, "data", "trails.json")))


ATLAS_SITES = os.path.join(os.environ.get("ATLAS_DIR", os.path.join(os.path.dirname(ROOT), "Cultural_Atlas")), "data", "sites.json")

if __name__ == "__main__":
    main()
