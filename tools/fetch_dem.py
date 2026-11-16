#!/usr/bin/env python3
"""下載 Copernicus DEM GLO-30（1 角秒，約 30 公尺）原始 GeoTIFF 到 .cache/dem/。

來源：https://copernicus-dem-30m.s3.amazonaws.com/（歐盟哥白尼計畫，AWS 公開桶，免註冊）
授權：Licence for the use of the Copernicus WorldDEM-30（可重製、散布、改作，須標示來源與免責聲明）
大小：臺灣、澎湖、金門、馬祖約 20 格、400 MB；.cache/ 不進 repo，建置時才需要。
用法：python3 tools/fetch_dem.py
"""
import os, shutil, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "dem")
SRC = "https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif"
LAT0, LAT1, LNG0, LNG1 = 21, 27, 118, 123


def name(lat, lng):
    return "Copernicus_DSM_COG_10_N%02d_00_E%03d_00_DEM" % (lat, lng)


def fetch(lat, lng):
    n = name(lat, lng)
    path = os.path.join(CACHE, n + ".tif")
    if os.path.exists(path) or os.path.exists(path + ".none"):
        return
    for attempt in range(4):
        try:
            print("下載", n, flush=True)
            with urllib.request.urlopen(SRC.format(n=n), timeout=180) as r, open(path + ".part", "wb") as f:
                want = int(r.headers.get("Content-Length") or 0)
                shutil.copyfileobj(r, f)
            if want and os.path.getsize(path + ".part") != want:
                raise IOError("下載不完整")
            os.replace(path + ".part", path)
            return
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):          # 全是海的格子桶裡沒有
                open(path + ".none", "w").close()
                return
            print("  失敗", e)
        except (IOError, OSError) as e:
            print("  失敗", e)
        time.sleep(3 * (attempt + 1))
    sys.exit("下載失敗：" + n)


if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)
    for lat in range(LAT0, LAT1):
        for lng in range(LNG0, LNG1):
            fetch(lat, lng)
    print("完成")
