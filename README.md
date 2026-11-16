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
| https://cultural-town.123hi.org/ | 鄉鎮文資性格卡 | allanloplus/Cultural_Town |
| https://cultural-ascent.123hi.org/ | 從海口到山頂（本 repo） | allanloplus/Cultural_Ascent |

## 目前的進度

| 單元 | 網址 | 狀態 |
|---|---|---|
| 1. 海拔總覽「文資住在多高」 | `#/` | 完成（已合併到 main） |
| 2. 河流版「溯河而上」 | `#/river`、`#/river/<河>` | 完成，待確認 |
| 3. 山徑版「越嶺古道」 | `#/trail`、`#/trail/<古道>` | 完成（已合併到 main） |

## 單元 1：文資住在多高

- **開頭的事實**：6 則，全部由 `tools/build.py` 的資料算出（海拔中位數、山多文資少、越往山上越年輕是否成立、最靠海的時代、國定古蹟住得最低、為什麼上山）。按一下會在高度剖面上標出相關文資。
- **高度剖面**：一點一處，依海拔由下往上排，同一列由左到右依創建年排；左邊是本島土地落在各高度的比例。可依時代或類型上色、標出單一縣市（附該縣市中位數線）。1,000 公尺以上的文資逐一標名。
- **時代與類型**：海拔的中位數、四分位距、第 90 百分位。
- **最高的十處**、**各縣市最高的文資**、**海拔怎麼算的**（含與介紹文字的比對表）。
- **文資卡片**（`#/s/<縣市序號>/<文資 id>`）：照片、等級、年代、海拔、摘要，連回知識網站 `<縣市網址>/#map/<景點 id>`；在鐵道版有車站步行 15 分鐘可達的，連到鐵道版車站頁。
- Allan 與阿拉蕾出現在開頭（全身像與對話）、事實卡表情、剖面、各段落與卡片；台詞裡的數字都從資料帶入（`ascent.js` 的 `duo()`、`say()`、`cmpTalk()` 等）。圖檔 `assets/characters/` 複製自 Cultural_Rail（源頭是 Cultural_Heritage），那邊更新時要再複製一次。

## 單元 2：溯河而上

做淡水河（主流＋新店溪、基隆河兩條支線）與濁水溪。蘭陽溪、高屏溪、曾文溪沿岸的文資太少（主流 2 公里內只有 8–15 處），算出的趨勢不可靠，所以不做；總覽頁有一張表說明各河的數字與原因。

- **總覽（`#/river`）**：兩條河的卡片、「為什麼只做兩條」的數字表、河道怎麼來的。
- **河流頁（`#/river/<id>`）**：5 則從資料算出的事實（開墾有沒有往上游推進、上中下游、最密集的河段、左右岸、淹水潛勢）；河流剖面（出海口到源頭橫向，文資依距出海口公里數排在左右兩岸，下方是河床高度，與單元 1 同一把對數高度尺；手機改直向，3 公里以上沒有文資的河段縮成一段並標出公里數）；創建年對照距出海口的散佈圖；上中下游的時代組成；淹水潛勢清單（保留文資地圖集的免責聲明）。
- **收錄規則**：文資在該河的水利署流域範圍內，且離推算的主流或支線 1 公里內（淡水河）或 2 公里內（濁水溪，沿岸太少所以放寬）。公里數是投影到最近的河道點、沿河道量；支線＝匯流點公里數＋支線上的公里數。面向下游，左手邊為左岸。
- **主流是推算的**：水利署「河川支流」圖層在寬河段沒有主流的線，所以 `tools/river_stem.py` 在流域內用地形推算水流（燒入水利署河川線、優先沿同名河川線上溯）。與水利署公布的主流長度比較：淡水河 146.8／158.7 公里、濁水溪 172.9／186.6 公里，約短 7%。
- **「是否為舊渡口或河港」**：只在最密集河段的文資名稱含渡、碼頭、港時才提，否則寫「資料不足以說它是舊河港」。

## 單元 3：越嶺古道

收錄有公開軌跡的五條歷史古道：浸水營古道、能高越嶺道、霞喀羅古道、福巴越嶺古道、八通關越道（只有鹿鳴吊橋段有軌跡）。合歡越嶺道、錐麓古道沒有找到可下載的公開軌跡，沒有收錄。

- **總覽（`#/trail`）**：5 則從資料算出的事實（最高處比所有文資都高、浸水營從山頂走到海口、坡度 10% 以下的比例、駐在所間距、沿線文資只有 1 處）、五條古道疊在同一把尺上的高度剖面、每條一張卡（迷你剖面、坡度分布）、年表、出處。
- **古道頁（`#/trail/<id>`）**：高度剖面（線的顏色是坡度、標出駐在所與遺址，可切換共用 0–3,000 公尺或放大）、4 則事實、沿線地點表（含與官方標示海拔的比對）、剖面以外的遺跡、歷史（逐句標出處）、沿線文資。
- **安全**：每一頁都寫明「僅供認識歷史，不可作為登山導航」，連到林業保育署步道開放狀態、玉山國家公園步道狀況、警政署入山申請、臺灣登山申請一站式服務網；本站不抓取、不保存開放狀態。
- **歷史內容的規則**：只用 `tools/build_trails.py` 的 `SRC` 列出的官方來源（林業保育署、觀光署、原民會、文資局、玉管處），每一句都標出處；來源之間說法不同時並列（例如八通關越道的開鑿年代、浸水營古道的全長），官方沒寫的就寫「官方資料沒有寫」。
- **點位**：有官方座標的（浸水營、鹿鳴段）直接投影到軌跡；只有官方里程的（能高、霞喀羅）依里程等比例放上，頁面標示為近似位置。

古道的高度剖面用線性高度（坡度才有意義），五條共用 0–3,000 公尺；單元 1 的對數高度尺只用在「文資住在多高」的剖面。

### 高度尺

單元 1 與之後的河流剖面共用 `U(h) = ln(1 + h / 5)`：低處放大、高處壓縮，0–20 公尺與 500–2,000 公尺佔的高度差不多。定義在 `assets/js/ascent.js` 開頭。

## 架構

純靜態網站，沒有後台與資料庫，沒有外部函式庫（字型取自 Google Fonts）。計算都在建置時用 Python 完成。

```
index.html               唯一的頁面
assets/css/ascent.css    樣式（共用區塊沿用 Cultural_Rail 的 rail.css，兩邊要一起改）
assets/css/trail.css     單元 3 的樣式
assets/js/ascent.js      路由與畫面
assets/characters/       Allan 與阿拉蕾的圖檔
data/raw/elev.json       每處文資的推估海拔、周圍高低差，與本島陸地的高度分布（build_elev.py 產生）
data/alt.json            單元 1 的全部資料（build.py 產生）
assets/og.png            分享到社群時的縮圖（1200×630）
tools/og.html            縮圖的原稿：用瀏覽器以 1200×630 開啟後截圖，存成 assets/og.png（數字改了要跟著改）
tools/fetch_dem.py       下載 Copernicus DEM 原始檔到 .cache/dem/（約 400 MB，不進 repo）
tools/build_elev.py      由 DEM 取每處文資的海拔 → data/raw/elev.json（需要 numpy、rasterio）
tools/build.py           產生 data/alt.json（只用標準函式庫）
data/raw/trails/         古道的原始軌跡與官方文字（抓一次就存檔，來源見下方）
data/raw/trails/tracks.json  組好的軌跡、每 25 公尺的海拔、點位海拔（trail_elev.py 產生）
data/trails.json         單元 3 的全部資料（build_trails.py 產生）
data/raw/wra/            水利署流域範圍圖（BASIN.zip 原檔）、河川支流的流域內裁切（riverlin-subset.geojson）、河川基本資料
data/raw/rivers/stems.json  推算的主流與支線（river_stem.py 產生）
data/rivers.json         單元 2 的全部資料（build_rivers.py 產生）
assets/css/river.css     單元 2 的樣式
tools/river_stem.py      推算主流與支線（需要 numpy、rasterio、shapely、pyproj、pyshp）
tools/build_rivers.py    產生 data/rivers.json（只用標準函式庫）
tools/trail_elev.py      組裝古道軌跡並由 DEM 取海拔（需要 numpy、rasterio）
tools/build_trails.py    產生 data/trails.json（只用標準函式庫）
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

文資清單或淹水潛勢更新後，重算單元 2：

```bash
python3 tools/build_rivers.py
```

河道要重新推算時（例如換新版水利署圖資）：

```bash
python3 tools/river_stem.py
```

古道資料不需要定期更新。要改歷史文字或加古道時，改 `tools/build_trails.py` 的 `TRAILS` 後：

```bash
python3 tools/build_trails.py
```

軌跡換新或加新古道時，先把原始檔放進 `data/raw/trails/`、在 `trail_elev.py` 的 `build()` 加一筆，再執行：

```bash
python3 tools/trail_elev.py
```

### 海拔的採用規則

- 預設用 Copernicus DEM（約 30 公尺網格）在文資座標點的雙線性內插值。它是數值**地表**模型，含樹冠與建築。
- 知識網站 `sites-content.json` 的介紹文字寫明海拔、且與推估相差超過 50 公尺又超過 5% 的，改用文字的數字，頁面標「依介紹文字」（目前 5 處：阿里山觀象所、七家灣、巴蘭、富世、蕉埔邱家水窟）。
- 座標周圍約 210 公尺見方內高低差超過 100 公尺的，標「海拔不確定」（目前 32 處）；知識網站 `coordNote` 註明「未能核對」的也標示。
- 500 公尺以上文資的「上山理由」依名稱與主題標籤歸類，規則在 `build.py` 的 `REASONS`。

## 待取得的資料（需在臺灣的網路下載）

建置主機在境外，下列政府資料的主機擋連線，請在臺灣下載後放進 `data/raw/`：

| 用途 | 檔案 | 放到 |
|---|---|---|
| 單元 2 河道（已取得，2026-11-16） | 水利署「河川支流」（政府資料開放平臺 25780）：https://gic.wra.gov.tw/gis/gic/API/Google/DownLoad.aspx?fname=RIVERLIN&filetype=SHP | 原檔約 21 MB 未存入；流域內裁切存為 `data/raw/wra/riverlin-subset.geojson` |
| 單元 2 流域（已取得，2026-11-16） | 水利署「河川流域範圍圖」（9823）：https://gic.wra.gov.tw/gis/gic/API/Google/DownLoad.aspx?fname=BASIN&filetype=SHP | `data/raw/wra/BASIN.zip` |
| 海拔校正（選用） | 內政部 20 公尺 DTM（35430）：https://www.tgos.tw/MDE/VirtualDir_TC/Product/9981ede9-584a-4470-8c5c-dbe579d4ecb4/不分幅_全台及澎湖DEM.zip | `.cache/dtm/`（檔案大，不進 repo） |

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
- 河川與流域：經濟部水利署「河川流域範圍圖」（政府資料開放平臺 9823）、「河川支流」（25780）、「河川基本資料」（167895），政府資料開放授權條款第 1 版；前兩者 2026-11-16 由 Allan 在臺灣下載提供（建置主機在境外連不上 gic.wra.gov.tw）。
- 淹水潛勢：經濟部水利署第三代淹水潛勢圖（2018），沿用文資地圖集 `data/risk.json` 的套疊結果；依《水災潛勢資料公開辦法》僅供防救災使用，不得作為土地使用管制或開發限制的依據，頁面保留此聲明。
- 古道軌跡（2026-11-16 下載，存於 `data/raw/trails/`），都依政府資料開放授權條款第 1 版：
  - 林業及自然保育署所轄自然步道軌跡圖（政府資料開放平臺）：065 能高越嶺道西段（38461）、026 霞喀羅古道（26999）、154 八通關越道鹿鳴吊橋段（31149）。
  - 林業及自然保育署 台灣山林悠遊網的步道 KML（`https://recreation.forest.gov.tw/Files/RT/GE/122.kml`，浸水營古道西段、東段與 75 個點位、`154.kml` 鹿鳴段點位）與步道基本資料 API（`/mis/api/BasicInfo/Trail`）。山林悠遊網的開放資料註明適用政府資料開放平臺資料使用規範。
  - 交通部觀光署 步道資料（政府資料開放平臺 41653）：能高越嶺道東段、福巴越嶺國家步道的線形與介紹文字。
- 古道歷史文字：上述林業保育署頁面（`data/raw/trails/rec-page-excerpts.json` 為 2026-11-16 擷取的摘錄）、原住民族委員會「臺灣原住民族古道簡介資料」（政府資料開放平臺 166817）、文化部文化資產局文化資產開放資料（八通關古道、浸水營古道(屏東段)）、玉山國家公園管理處「八通關越道」頁面。頁面上每一句都連回出處。

---

Copyright © 2026 Allan Lo. 文字內容與程式碼版權所有；第三方資料依各自授權。
