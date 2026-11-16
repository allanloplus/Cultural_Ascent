#!/usr/bin/env python3
"""推算河川主流（與淡水河的兩條支線）→ data/raw/rivers/stems.json

水利署「河川支流」圖層在寬河段沒有主流的線（主流畫在另一個「河川河道」面圖層），所以主流用推算的：
  1. 在水利署「河川流域範圍圖」的流域內，取 Copernicus DEM（3 角秒，約 90 公尺）。
  2. 把水利署河川線經過的格子降低 BURN 公尺（「燒入」），讓水流沿著已知的河道走。
  3. 從流域邊界做 priority-flood，得到每格的流向與集水面積。
  4. 從集水面積最大的格子（出海口）往上游走：上游格子中，若有水利署標為這條河的線（NAMES），
     且集水面積至少是最大者的 PREFER 倍，就走那一格；否則走集水面積最大的一格。
  5. 支線（新店溪、基隆河）：從該河名的線上集水面積最大的一格，往下游走到主流（匯流點），再往上游走。
  6. 每條線以約 270 公尺移動平均平滑後量長度；沿線海拔由下游往上游取累積最大值（河水不會往上流，
     可去掉橋梁與樹冠造成的突起）。

讀取：data/raw/wra/BASIN.zip、data/raw/wra/riverlin-subset.geojson、.cache/dem/
需要：numpy、rasterio、shapely、pyproj、pyshp
"""
import heapq, json, math, os
import numpy as np
import rasterio
import shapefile
from rasterio import features
from rasterio.transform import from_origin
from shapely.geometry import mapping, shape
from shapely import transform as shp_tf
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, ".cache", "dem")
STEP = 3
BURN = 40
PREFER = 0.15
SMOOTH = 1           # 平滑：前後各 1 格
OUT = os.path.join(ROOT, "data", "raw", "rivers", "stems.json")

RIVERS = [
    dict(id="danshui", basin="淡水河", names=["淡水河", "大漢溪"], branches=[dict(id="xindian", name="新店溪", names=["新店溪"]), dict(id="keelung", name="基隆河", names=["基隆河"])]),
    dict(id="zhuoshui", basin="濁水溪", names=["濁水溪"]),
    dict(id="lanyang", basin="蘭陽溪", names=["蘭陽溪"]),
    dict(id="gaoping", basin="高屏溪", names=["高屏溪", "荖濃溪"]),
    dict(id="zengwen", basin="曾文溪", names=["曾文溪"]),
]

T84 = Transformer.from_crs(3826, 4326, always_xy=True)


def to84(g):
    return shp_tf(g, lambda xy: np.column_stack(T84.transform(xy[:, 0], xy[:, 1])))


def mosaic(lo0, la0, lo1, la1):
    ppd = 3600 // STEP
    x0, x1 = math.floor(lo0 * ppd) / ppd, math.ceil(lo1 * ppd) / ppd
    y0, y1 = math.floor(la0 * ppd) / ppd, math.ceil(la1 * ppd) / ppd
    w, h = round((x1 - x0) * ppd), round((y1 - y0) * ppd)
    out = np.zeros((h, w), np.float32)
    for la in range(math.floor(y0), math.ceil(y1)):
        for lo in range(math.floor(x0), math.ceil(x1)):
            p = os.path.join(CACHE, "Copernicus_DSM_COG_10_N%02d_00_E%03d_00_DEM.tif" % (la, lo))
            if not os.path.exists(p):
                continue
            a = rasterio.open(p).read(1)
            a = a[:a.shape[0] // STEP * STEP, :a.shape[1] // STEP * STEP].reshape(a.shape[0] // STEP, STEP, a.shape[1] // STEP, STEP).mean(axis=(1, 3))
            r0 = round((y1 - (la + 1)) * ppd); c0 = round((lo - x0) * ppd)
            rs, cs, re, ce = max(0, r0), max(0, c0), min(h, r0 + a.shape[0]), min(w, c0 + a.shape[1])
            if re > rs and ce > cs:
                out[rs:re, cs:ce] = a[rs - r0:re - r0, cs - c0:ce - c0]
    return out, x0, y1, 1 / ppd


def km_of(pts):
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot((b[0] - a[0]) * 111.32 * math.cos(math.radians(a[1])), (b[1] - a[1]) * 110.57))
    return cum


def finish(cells, w, x0, y1, d, dem):
    """格子序列 → 平滑後的 [經度, 緯度, 海拔]、公里數。"""
    xy = [(x0 + (k % w + .5) * d, y1 - (k // w + .5) * d) for k in cells]
    n = len(xy)
    sm = [tuple(np.mean([xy[j] for j in range(max(0, i - SMOOTH), min(n, i + SMOOTH + 1))], axis=0)) for i in range(n)]
    sm[0], sm[-1] = xy[0], xy[-1]
    h = np.maximum.accumulate(np.maximum(0, [float(dem.flat[k]) for k in cells]))
    return [[round(x, 5), round(y, 5), round(float(e), 1)] for (x, y), e in zip(sm, h)], [round(k, 3) for k in km_of(sm)]


def run(R, BAS, LINES):
    g84 = to84(BAS[R["basin"]])
    lo0, la0, lo1, la1 = g84.bounds
    dem, x0, y1, d = mosaic(lo0 - .02, la0 - .02, lo1 + .02, la1 + .02)
    tr = from_origin(x0, y1, d, d)
    shp = dem.shape
    mask = features.rasterize([(mapping(g84), 1)], out_shape=shp, transform=tr, fill=0, all_touched=True).astype(bool)
    inb = [(nm, to84(g)) for nm, g in LINES if g.intersects(BAS[R["basin"]])]
    burn = features.rasterize([(mapping(g), 1) for _, g in inb], out_shape=shp, transform=tr, fill=0, all_touched=True).astype(bool)

    def named(ns):
        gs = [mapping(g) for nm, g in inb if nm in ns]
        return features.rasterize([(g, 1) for g in gs], out_shape=shp, transform=tr, fill=0, all_touched=True).astype(bool).ravel() if gs else np.zeros(shp[0] * shp[1], bool)

    z = dem.astype(np.float64) - np.where(burn & mask, BURN, 0)
    h, w = shp
    done = np.zeros(shp, bool); down = np.full(h * w, -1, np.int64); order = []; pq = []
    edge = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1))
    for r, c in zip(*np.nonzero(edge)):
        heapq.heappush(pq, (z[r, c], r * w + c)); done[r, c] = True
    N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    while pq:
        e, k = heapq.heappop(pq); r, c = divmod(k, w); order.append(k)
        for dr, dc in N8:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and mask[rr, cc] and not done[rr, cc]:
                done[rr, cc] = True; down[rr * w + cc] = k
                heapq.heappush(pq, (max(z[rr, cc], e + 1e-4), rr * w + cc))
    acc = np.zeros(h * w)
    acc[order] = 1
    for k in reversed(order):
        if down[k] >= 0:
            acc[down[k]] += acc[k]
    ups = {}
    for k in order:
        if down[k] >= 0:
            ups.setdefault(int(down[k]), []).append(k)

    def up_from(k, nm):
        path = [k]
        while path[-1] in ups:
            cand = ups[path[-1]]; m = max(acc[u] for u in cand)
            pref = [u for u in cand if nm[u] and acc[u] >= PREFER * m]
            path.append(max(pref or cand, key=lambda u: acc[u]))
        return path

    cell_km2 = (d * 111.32 * math.cos(math.radians((la0 + la1) / 2))) * (d * 110.57)
    mouth = int(np.argmax(acc))
    main = up_from(mouth, named(R["names"]))
    pts, km = finish(main, w, x0, y1, d, dem)
    out = {"id": R["id"], "basin": R["basin"], "pts": pts, "km": km, "area": round(acc[mouth] * cell_km2), "branches": []}
    onmain = {k: i for i, k in enumerate(main)}
    for B in R.get("branches", []):
        nm = named(B["names"])
        seed = max((k for k in np.nonzero(nm)[0] if k not in onmain and mask.flat[k]), key=lambda k: acc[k])
        dn = [int(seed)]
        while dn[-1] not in onmain and down[dn[-1]] >= 0:
            dn.append(int(down[dn[-1]]))
        conf = onmain[dn[-1]]
        cells = dn[::-1] + up_from(int(seed), nm)[1:]
        bp, bk = finish(cells, w, x0, y1, d, dem)
        out["branches"].append({"id": B["id"], "name": B["name"], "pts": bp, "km": bk, "at": km[conf], "area": round(acc[cells[1]] * cell_km2)})
        print("   支線 %s：%.1f 公里，在主流 %.1f 公里處匯入" % (B["name"], bk[-1], km[conf]), flush=True)
    print("%s：主流 %.1f 公里、集水 %d 平方公里、出海口 %s、源頭 %s（%.0f 公尺）" % (R["basin"], km[-1], out["area"], pts[0][:2], pts[-1][:2], pts[-1][2]), flush=True)
    return out


def main():
    B = shapefile.Reader(os.path.join(ROOT, "data", "raw", "wra", "BASIN.zip"), encoding="utf-8")
    BAS = {r["BASIN_NAME"]: shape(s.__geo_interface__) for r, s in zip(B.records(), B.shapes())}
    G = json.load(open(os.path.join(ROOT, "data", "raw", "wra", "riverlin-subset.geojson"), encoding="utf-8"))
    LINES = [(f["properties"]["NAME"], shape(f["geometry"])) for f in G["features"]]
    res = {"method": "流域內地形推算（燒入水利署河川線、優先沿同名河川線上溯），3 角秒 Copernicus DEM", "rivers": {}}
    for R in RIVERS:
        res["rivers"][R["id"]] = run(R, BAS, LINES)
        res["rivers"][R["id"]]["basinGeo"] = [[round(x, 4), round(y, 4)] for x, y in to84(BAS[R["basin"]]).simplify(.003).exterior.coords] if BAS[R["basin"]].geom_type == "Polygon" else \
            [[round(x, 4), round(y, 4)] for x, y in max(to84(BAS[R["basin"]]).simplify(.003).geoms, key=lambda g: g.area).exterior.coords]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
