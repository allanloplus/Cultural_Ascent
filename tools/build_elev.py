#!/usr/bin/env python3
"""每處文資的地面高度與本島陸地的高度分布 → data/raw/elev.json

讀取：.cache/dem/（tools/fetch_dem.py 下載的 Copernicus DEM GLO-30 原始檔，1 角秒約 30 公尺）
      ../Cultural_Atlas/data/sites.json（文資座標；可用 ATLAS_DIR 指定）
輸出：data/raw/elev.json
  sites：{"縣市代碼/文資 id": [海拔公尺, 周圍高低差公尺]}
         海拔：座標點的雙線性內插；高低差：以座標為中心 7×7 格（約 210 公尺見方）內最高與最低的差，
         用來判斷「座標稍有偏差、海拔就差很多」的陡坡。
  land：臺灣本島（北緯 21.8–25.4 度、東經 120–122.1 度，含綠島、蘭嶼）陸地高度的分布，
        每 10 公尺一格的面積比例（取樣間隔約 90 公尺）。
需要：pip install numpy rasterio（只有這支腳本需要，build.py 只用標準函式庫）
注意：Copernicus DEM 是「數值地表模型」（含樹冠與建築），不是去除地物的地形模型；
      與知識網站介紹文字中寫明海拔的 21 處比較，中位差 5 公尺。
"""
import json, math, os
import numpy as np
import rasterio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS = os.environ.get("ATLAS_DIR", os.path.join(os.path.dirname(ROOT), "Cultural_Atlas"))
CACHE = os.path.join(ROOT, ".cache", "dem")
WIN = 3            # 高低差視窗半徑（格）
TILES = {}


def tile(lat, lng):
    k = (int(math.floor(lat)), int(math.floor(lng)))
    if k not in TILES:
        p = os.path.join(CACHE, "Copernicus_DSM_COG_10_N%02d_00_E%03d_00_DEM.tif" % k)
        TILES[k] = rasterio.open(p).read(1).astype(np.float32) if os.path.exists(p) else None
    return TILES[k], k


def sample(lat, lng):
    a, k = tile(lat, lng)
    if a is None:                      # 範圍外（東沙）或全是海的格子
        return 0.0, 0.0
    h, w = a.shape
    y = (k[0] + 1 - lat) * h - 0.5     # 像素中心對齊
    x = (lng - k[1]) * w - 0.5
    y0 = int(np.clip(math.floor(y), 0, h - 2)); x0 = int(np.clip(math.floor(x), 0, w - 2))
    fy, fx = y - y0, x - x0
    v = a[y0:y0 + 2, x0:x0 + 2]
    e = v[0, 0] * (1 - fy) * (1 - fx) + v[0, 1] * (1 - fy) * fx + v[1, 0] * fy * (1 - fx) + v[1, 1] * fy * fx
    yi, xi = int(round(y)), int(round(x))
    win = a[max(0, yi - WIN):yi + WIN + 1, max(0, xi - WIN):xi + WIN + 1]
    return max(0.0, float(e)), float(win.max() - win.min())


def land_hist():
    vals = []
    for lat in range(21, 26):
        for lng in (120, 121):
            a, _ = tile(lat + .5, lng + .5)
            if a is None:
                continue
            h, w = a.shape
            lat_top = lat + 1
            r0 = int(max(0, (lat_top - 25.4) * h)); r1 = int(min(h, (lat_top - 21.8) * h))
            c1 = int(min(w, (122.1 - lng) * w))
            b = a[r0:r1:3, 0:c1:3]
            vals.append(b[b > 0.5])
    v = np.concatenate(vals)
    top = int(math.ceil(v.max() / 10))
    cnt = np.bincount((v // 10).astype(int), minlength=top)
    return {"step": 10, "share": [round(float(c) / len(v), 6) for c in cnt], "median": round(float(np.median(v))),
            "over": {str(t): round(float((v >= t).mean()), 4) for t in (20, 50, 100, 200, 500, 1000, 2000, 3000)}}


def main():
    S = json.load(open(os.path.join(ATLAS, "data", "sites.json"), encoding="utf-8"))
    F = S["meta"]["fields"]
    out = {}
    for r in S["sites"]:
        o = dict(zip(F, r))
        e, rel = sample(o["lat"], o["lng"])
        out["%s/%s" % (S["counties"][o["county"]]["slug"], o["id"])] = [round(e, 1), round(rel)]
    doc = {"source": "Copernicus DEM GLO-30（Copernicus WorldDEM-30），https://copernicus-dem-30m.s3.amazonaws.com/",
           "attribution": "produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved",
           "disclaimer": "The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30",
           "method": "座標點雙線性內插；高低差為 7×7 格（約 210 公尺見方）內最高減最低",
           "sites": out, "land": land_hist()}
    with open(os.path.join(ROOT, "data", "raw", "elev.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print("完成：%d 處文資；本島陸地中位海拔 %d 公尺" % (len(out), doc["land"]["median"]))


if __name__ == "__main__":
    main()
