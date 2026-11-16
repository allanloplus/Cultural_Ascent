# 從海口到山頂

以「高度」為主軸看臺灣的有形文化資產，是「Allan Lo 和你逛文化」的第六個姊妹站。

- 網址：https://cultural-ascent.123hi.org/
- 規劃設計：Allan Lo，https://www.123hi.org，2026年11月

| 網站 | 內容 | Repo |
|---|---|---|
| https://cultural.123hi.org/ | 文資知識網站第一站（13 縣市＋共用程式） | allanloplus/Cultural_Heritage |
| https://cultural2.123hi.org/ | 文資知識網站第二站（9 縣市） | allanloplus/Cultural_Heritage2 |
| https://cultural-visit.123hi.org/ | 文資達人訪查 | allanloplus/Cultural_Heritage_Master |
| https://cultural-atlas.123hi.org/ | 文資地圖集 | allanloplus/Cultural_Atlas |
| https://cultural-rail.123hi.org/ | 搭火車逛文資 | allanloplus/Cultural_Rail |
| https://cultural-ascent.123hi.org/ | 從海口到山頂（本 repo） | allanloplus/Cultural_Ascent |

## 目前的進度

| 單元 | 網址 | 狀態 |
|---|---|---|
| 1. 海拔總覽「文資住在多高」 | `#/` | 完成，待確認 |
| 2. 河流版「溯河而上」 | `#/river` | 製作中（只有預告頁） |
| 3. 山徑版「越嶺古道」 | `#/trail` | 製作中（只有預告頁） |

## 單元 1：文資住在多高

- **開頭的事實**：6 則，全部由 `tools/build.py` 的資料算出（海拔中位數、山多文資少、越往山上越年輕是否成立、最靠海的時代、國定古蹟住得最低、為什麼上山）。按一下會在高度剖面上標出相關文資。
- **高度剖面**：一點一處，依海拔由下往上排，同一列由左到右依創建年排；左邊是本島土地落在各高度的比例。可依時代或類型上色、標出單一縣市（附該縣市中位數線）。1,000 公尺以上的文資逐一標名。
- **時代與類型**：海拔的中位數、四分位距、第 90 百分位。
- **最高的十處**、**各縣市最高的文資**、**海拔怎麼算的**（含與介紹文字的比對表）。
- **文資卡片**（`#/s/<縣市序號>/<文資 id>`）：照片、等級、年代、海拔、摘要，連回知識網站 `<縣市網址>/#map/<景點 id>`；在鐵道版有車站步行 15 分鐘可達的，連到鐵道版車站頁。
- Allan 與阿拉蕾出現在開頭（全身像與對話）、事實卡表情、剖面、各段落與卡片；台詞裡的數字都從資料帶入（`ascent.js` 的 `duo()`、`say()`、`cmpTalk()` 等）。圖檔 `assets/characters/` 複製自 Cultural_Rail（源頭是 Cultural_Heritage），那邊更新時要再複製一次。

### 高度尺

全站共用 `U(h) = ln(1 + h / 5)`：低處放大、高處壓縮，0–20 公尺與 500–2,000 公尺佔的高度差不多。之後河流與山徑的剖面也用這把尺。定義在 `assets/js/ascent.js` 開頭。

## 架構

純靜態網站，沒有後台與資料庫，沒有外部函式庫（字型取自 Google Fonts）。計算都在建置時用 Python 完成。

```
index.html               唯一的頁面
assets/css/ascent.css    樣式（共用區塊沿用 Cultural_Rail 的 rail.css，兩邊要一起改）
assets/js/ascent.js      路由與畫面
assets/characters/       Allan 與阿拉蕾的圖檔
data/raw/elev.json       每處文資的推估海拔、周圍高低差，與本島陸地的高度分布（build_elev.py 產生）
data/alt.json            單元 1 的全部資料（build.py 產生）
tools/fetch_dem.py       下載 Copernicus DEM 原始檔到 .cache/dem/（約 400 MB，不進 repo）
tools/build_elev.py      由 DEM 取每處文資的海拔 → data/raw/elev.json（需要 numpy、rasterio）
tools/build.py           產生 data/alt.json（只用標準函式庫）
```

### 更新資料

知識網站、文資地圖集或鐵道版的資料有變動後：

```bash
python3 tools/build.py
```

腳本會找本 repo 旁邊的 `Cultural_Atlas`、`Cultural_Heritage`、`Cultural_Heritage2`、`Cultural_Rail`（或用環境變數 `ATLAS_DIR`、`CH1_DIR`、`CH2_DIR`、`RAIL_DIR` 指定），只讀取、不修改。

文資有新增或座標有修正時，要先重算海拔（第一次要先下載 DEM）：

```bash
pip install numpy rasterio
```

```bash
python3 tools/fetch_dem.py
```

```bash
python3 tools/build_elev.py
```

### 海拔的採用規則

- 預設用 Copernicus DEM（約 30 公尺網格）在文資座標點的雙線性內插值。它是數值**地表**模型，含樹冠與建築。
- 知識網站 `sites-content.json` 的介紹文字寫明海拔、且與推估相差超過 50 公尺又超過 5% 的，改用文字的數字，頁面標「依介紹文字」（目前 5 處：阿里山觀象所、七家灣、巴蘭、富世、蕉埔邱家水窟）。
- 座標周圍約 210 公尺見方內高低差超過 100 公尺的，標「海拔不確定」（目前 32 處）；知識網站 `coordNote` 註明「未能核對」的也標示。
- 500 公尺以上文資的「上山理由」依名稱與主題標籤歸類，規則在 `build.py` 的 `REASONS`。

## 部署

GitHub Pages：Settings → Pages → Deploy from a branch，選 `main` 與 `/ (root)`。自訂網域寫在 `CNAME`（`cultural-ascent.123hi.org`），DNS 需要一筆 CNAME 記錄指向 `allanloplus.github.io`。

## 本機預覽

```bash
python3 -m http.server 8000
```

## 資料來源與授權

- 地形：Copernicus DEM GLO-30（https://copernicus-dem-30m.s3.amazonaws.com/），2026-11-16 下載。授權為 Licence for the use of the Copernicus WorldDEM-30，可重製、散布、改作，須標示：produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved。免責聲明：The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30。
  - 內政部 20 公尺網格數值地形模型（政府資料開放平臺資料集 35430，政府資料開放授權條款第 1 版）解析度較高且為地形模型，但檔案放在 TGOS，建置主機（境外）連線回 403；國網中心 SciDM 的鏡像需要登入。若在臺灣的網路下載 `不分幅_全台及澎湖DEM.zip`，可改寫 `build_elev.py` 讀它。
- 文化資產清單、座標、年代、摘要、介紹文字：文化部文化資產局國家文化資產網，經兩個知識網站與文資地圖集整理。
- 照片：Wikimedia Commons，作者與授權標在卡片照片下方，取自知識網站各縣市的 `images.json`。
- 車站步行可達：姊妹站搭火車逛文資的 `data/lines/*.json`（推估）。
- 玉山主峰 3,952 公尺為一般通用的高度，只作剖面頂端的參考線。

---

Copyright © 2026 Allan Lo. 文字內容與程式碼版權所有；第三方資料依各自授權。
