/* 從海口到山頂 — 單頁程式
 * 路由：#/ 海拔總覽　#/s/<縣市序號>/<文資 id> 文資卡片　#/river 溯河而上　#/trail 越嶺古道　#/about 說明
 * 資料：data/alt.json，由 tools/build.py 產生；網頁只畫圖，數字都在建置時算好（排序、四分位數除外）。
 * 高度尺：全站共用 U(h) = ln(1 + h / 5)，低處放大、高處壓縮；河流與山徑的剖面也用同一把尺。 */
(function () {
  "use strict";
  var app = document.getElementById("app"), dlg = document.getElementById("dlg");
  var D = null;
  var LV = ["國定古蹟", "市縣定古蹟", "歷史建築", "紀念建築", "聚落建築群", "文化景觀", "考古遺址"];
  var state = { color: "era", county: -1, hl: null, hlLabel: "" };
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var K = 5, TOP = 4000, PEAK = 3952;
  function U(h) { return Math.log(1 + Math.max(0, h) / K); }
  function Uinv(u) { return (Math.exp(u) - 1) * K; }
  var UMAX = U(TOP);

  /* ---------- 小工具 ---------- */
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function num(n) { return Math.round(n).toLocaleString("en-US"); }
  function getJSON(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }
  function yearText(o) { if (o.y == null) return "年代不詳"; return (o.y < 0 ? "西元前 " + (-o.y) : o.y) + " 年" + (o.e ? "（推估）" : ""); }
  function key(o) { return o.c + "/" + o.i; }
  function q(a, p) { var i = (a.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i); return a[lo] + (a[hi] - a[lo]) * (i - lo); }
  function src(o, size) { var p = o.p[size === "l" ? 1 : 0]; return /^https?:/.test(p) ? p : D.counties[o.c].base + p; }
  function ticket(o, cls) {
    return '<span class="tk lv' + o.k + " " + (cls || "") + '" style="--lvc:var(--dc)" aria-hidden="true"><b>' + (o.y == null ? "？" : (o.y < 0 ? "前" : "") + Math.abs(o.y)) + "</b><i>" + esc(D.eras[o.r].name) + "</i></span>";
  }
  function img(o, size, cls) {
    if (!o.p) return ticket(o, cls);
    return '<img class="' + (cls || "") + '" src="' + esc(src(o, size)) + '" alt="" loading="lazy" decoding="async" data-fb="' + esc(JSON.stringify({ k: o.k, y: o.y, r: o.r })) + '">';
  }
  document.addEventListener("error", function (e) { /* 照片載入失敗 → 換成票卡樣式 */
    var t = e.target;
    if (t.tagName === "IMG" && t.dataset.fb) {
      var o = JSON.parse(t.dataset.fb), w = document.createElement("span");
      w.innerHTML = ticket(o, t.className);
      var fig = t.closest(".card-ph"); if (fig) { fig.classList.add("nophoto"); var fc = fig.querySelector("figcaption"); if (fc) fc.remove(); }
      t.replaceWith(w.firstChild);
    }
  }, true);
  function say(who, mood, text, cls) {
    return '<div class="say say-' + who + " " + (cls || "") + '"><img src="assets/characters/' + (who === "R" ? "arale-" : "allan-") + mood + '.webp" alt="" width="64" height="64" loading="lazy"><p><b>' +
      (who === "R" ? "阿拉蕾" : "Allan") + "</b>" + text + "</p></div>";
  }
  function duo(a, r) {
    return '<div class="duo" aria-label="Allan 和阿拉蕾"><div class="duo-b">' + '<p class="bub bub-A"><b>Allan</b>' + a + '</p><p class="bub bub-R"><b>阿拉蕾</b>' + r + "</p></div>" +
      '<div class="duo-p"><img src="assets/characters/allan-wave.webp" alt="Allan" width="560" height="657"><img src="assets/characters/arale-wave.webp" alt="阿拉蕾" width="311" height="640"></div></div>';
  }
  var ICON = {
    alt: '<svg viewBox="0 0 36 36" aria-hidden="true"><path d="M2 32 14 10l6 9 4-5 10 18z" fill="currentColor" opacity=".9"/><path d="M4 34h28" stroke="currentColor" stroke-width="2"/><path d="M30 4v22M27 7l3-3 3 3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    river: '<svg viewBox="0 0 36 36" aria-hidden="true"><path d="M3 30c6 0 6-6 12-6s5-7 10-7 5-8 9-12" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/><circle cx="12" cy="26" r="2.6" fill="currentColor"/><circle cx="24" cy="17" r="2.6" fill="currentColor"/></svg>',
    trail: '<svg viewBox="0 0 36 36" aria-hidden="true"><path d="M2 32 12 14l5 6 7-12 10 24z" fill="currentColor" opacity=".25"/><path d="M4 30c4-1 5-6 9-8s4-6 8-8 5-6 9-8" fill="none" stroke="currentColor" stroke-width="2.4" stroke-dasharray="3 3" stroke-linecap="round"/></svg>'
  };
  function units(cur) {
    var u = [["alt", "#/", "單元 1", "文資住在多高", "全臺文資依海拔排列，從海平面到最高處"],
      ["river", "#/river", "單元 2", "溯河而上", "從出海口到源頭，沿河的文資與高度剖面"],
      ["trail", "#/trail", "單元 3", "越嶺古道", "歷史古道的高度剖面、駐在所與遺址"]];
    return '<nav class="units" aria-label="三個單元">' + u.map(function (x) {
      var soon = x[0] !== "alt";
      return '<a class="unit' + (x[0] === cur ? " cur" : "") + (soon ? " soon" : "") + '" href="' + x[1] + '"' + (x[0] === cur ? ' aria-current="page"' : "") + ">" + ICON[x[0]] +
        '<span class="u-no">' + x[2] + "</span><b>" + x[3] + "</b><small>" + x[4] + "</small></a>";
    }).join("") + "</nav>";
  }

  /* ---------- 首頁：開頭 ---------- */
  var FACT_FACE = { "一半的文資": ["R", "surprised"], "山很多，文資很少": ["A", "think"], "越往山上越年輕？": ["A", "scratch"], "最靠海的時代": ["R", "explain"], "國定古蹟住得最低": ["A", "point"], "為什麼上山": ["R", "think"] };
  function viewHome() {
    var m = D.meta, high = D.bands.filter(function (b) { return b.lo >= m.high; }).reduce(function (a, b) { return a + b.n; }, 0);
    var yrs = D.bands.map(function (b) { return b.year; }).filter(function (y) { return y; });
    var f = D.facts.map(function (x, i) {
      var ff = FACT_FACE[x.k] || ["A", "smile"], word = !/^[\d,.]+$/.test(x.big);
      return '<li><button type="button" class="fact" data-fact="' + i + '" style="--i:' + i + '"><img class="fact-face" src="assets/characters/' + (ff[0] === "R" ? "arale-" : "allan-") + ff[1] + '.webp" alt="" width="60" height="60"><span class="fact-k">' + esc(x.k) +
        '</span><span class="fact-big"><b' + (word ? ' class="word"' : "") + ">" + esc(x.big) + "</b><i>" + esc(x.unit) + '</i></span><span class="fact-t">' + esc(x.t) + '</span><span class="fact-go">在高度剖面上看 ↓</span></button></li>';
    }).join("");
    app.innerHTML = '<div class="ascent">' +
      '<section class="home-hero has-duo"><div class="wrap">' +
      '<p class="kicker">從海口到山頂・單元 1・全臺 ' + num(m.total) + " 處有形文資</p>" +
      "<h1>文資住在多高</h1>" + '<p class="home-sub">從海平面一路往上數，數到最高的那一處。</p>' +
      '<p class="lede">臺灣本島一半的土地在 <b>' + num(D.land.median) + "</b> 公尺以上，文資卻有一半住在 <b>" + num(m.median) + "</b> 公尺以下。" +
      m.high + " 公尺以上只有 <b>" + high + "</b> 處，它們為什麼上山？下面每一則都是從資料算出來的。</p>" +
      duo("臺灣是山的島，可是古蹟和歷史建築都住在哪個高度？", "我把 " + num(m.total) + " 處全部量過了，一半在 " + num(m.median) + " 公尺以下，差不多七層樓高而已！") +
      units("alt") + "</div></section>" +
      '<section class="wrap sec"><h2 class="sr-only">從資料算出的事實</h2><div class="talk">' +
      say("R", "think", "Allan，越往山上，文資是不是越新？平地先開發，山上比較晚嘛。") +
      say("A", "scratch", "我原本也這樣猜。算出來不成立：每個高度帶文資創建年的中位數，都落在 " + Math.min.apply(null, yrs) + " 到 " + Math.max.apply(null, yrs) + " 年之間。") +
      '</div><ul class="facts">' + f + "</ul></section>" +
      '<section class="wrap sec" id="profile"><div class="sec-h"><h2>高度剖面</h2><p id="pf-sum"></p></div>' +
      '<p class="sec-lede">一點是一處文資，依海拔由下往上排；同一列由左到右依創建年排。左邊淡棕色是臺灣本島土地落在各高度的比例。高度尺在低處放大（見刻度），所以 0 到 20 公尺佔的高度和 500 到 2,000 公尺差不多。</p>' +
      '<div class="talk">' + say("R", "surprised", "左邊棕色的山那麼胖，右邊的點卻全擠在下面！") +
      say("A", "point", "本島 " + Math.round(D.land.over[String(m.high)] * 100) + "% 的土地在 " + num(m.high) + " 公尺以上，文資只有 " + high + " 處在那裡。按一下任何一點，看看它是誰。") + "</div>" +
      '<div class="pf-bar"><div class="flt" id="pf-ctl"></div></div><div id="pf-say" class="pf-say" aria-live="polite"></div>' +
      '<div class="pf-wrap" id="pf-wrap"><div class="pf-legend" id="pf-legend"></div><svg class="pf" id="pf" role="img" aria-label="全臺文資的海拔分布：一點一處，由海平面排到最高處"></svg><div class="tip" id="tip" hidden></div></div>' +
      bandTable() + "</section>" +
      '<section class="wrap sec"><div class="sec-h"><h2>時代與類型</h2><p>海拔的中位數與分布範圍</p></div>' +
      '<p class="sec-lede">圓點是中位數，粗線是中間一半文資（第 25 到 75 百分位）的範圍，細線延伸到第 90 百分位。橫軸用和剖面相同的高度尺。</p>' +
      cmpTalk() + '<div class="cmp-grid"><div class="cmp"><h3>各時代</h3><svg id="cmp-era"></svg></div><div class="cmp"><h3>各類型</h3><svg id="cmp-cat"></svg></div></div></section>' +
      '<section class="wrap sec"><div class="sec-h"><h2>最高的十處</h2><p>依推估海拔排序</p></div>' + top10Talk() + top10() + "</section>" +
      '<section class="wrap sec"><div class="sec-h"><h2>各縣市最高的文資</h2><p>' + D.counties.length + " 個縣市，依最高一處的海拔排序</p></div>" + countyTalk() + countyList() + "</section>" +
      '<section class="wrap sec" id="method"><div class="sec-h"><h2>海拔怎麼算的</h2><p>推估，有誤差</p></div>' + '<div class="talk">' +
      say("A", "scratch", "老實說，這裡的海拔都是推估。七家灣考古遺址的座標落在山坡上，直接取值就多了將近一千公尺。") +
      say("R", "explain", "所以我把介紹文字有寫海拔的 " + D.meta.check.n + " 處都拿來對過，中位差 " + D.meta.check.medAbs + " 公尺；差太多的 " + D.meta.check.adopted + " 處改用文字。") + "</div>" + methodBox() + "</section>" +
      '<section class="wrap sec"><div class="sec-h"><h2>接著往哪走</h2></div><div class="next-units">' +
      '<a class="unit soon" href="#/river">' + ICON.river + '<span class="u-no">單元 2</span><b>溯河而上</b><small>從出海口往源頭走，看開墾是不是沿著河往上游推進。</small></a>' +
      '<a class="unit soon" href="#/trail">' + ICON.trail + '<span class="u-no">單元 3</span><b>越嶺古道</b><small>500 公尺以上的文資只有 ' + high + ' 處；山上的歷史，要沿著古道看。</small></a></div></section></div>';
    paintControls();
    drawProfile();
    drawCmp("cmp-era", "r", D.eras.map(function (e) { return e.name; }), "ev");
    drawCmp("cmp-cat", "k", LV, "lv");
  }
  function cmpTalk() {
    var cs = D.catStats.slice().sort(function (a, b) { return a.med - b.med; }), lo = cs[0], hi = cs[cs.length - 1];
    var es = D.eraStats.slice().sort(function (a, b) { return b.med - a.med; });
    return '<div class="talk">' + say("R", "think", "最「愛住海邊」的是哪一種文資？") +
      say("A", "point", esc(lo.name) + "，中位數 " + lo.med + " 公尺；" + esc(hi.name) + "最高，" + hi.med + " 公尺。時代裡中位數最高的反而是最早的" + esc(es[0].name) + "（" + es[0].med + " 公尺）。") + "</div>";
  }
  function top10Talk() {
    var t = D.top10.map(function (i) { return D.sites[i]; }), f = t.filter(function (o) { return o.why === "forest"; }).length;
    return '<div class="talk">' + say("R", "surprised", "第一名是" + esc(t[0].n) + "，" + num(t[0].h) + " 公尺！") +
      say("A", "wink", "前十名有 " + f + " 處跟阿里山、太平山的林業有關。伐木把人帶上了兩千公尺。") + "</div>";
  }
  function countyTalk() {
    var c = D.countyTop.slice().sort(function (a, b) { return a.med - b.med; }), lo = c[0], hi = c[c.length - 1];
    return '<div class="talk">' + say("R", "think", "哪個縣市的文資住得最低？") +
      say("A", "point", esc(D.counties[lo.c].name) + "，中位數只有 " + lo.med + " 公尺；" + esc(D.counties[hi.c].name) + "最高，" + hi.med + " 公尺。可是" + esc(D.counties[lo.c].name) + "最高的一處在 " + num(lo.h) + " 公尺。") + "</div>";
  }
  function bandTable() {
    var tot = D.meta.total;
    var rows = D.bands.map(function (b) {
      var lab = b.hi ? num(b.lo) + "–" + num(b.hi) : num(b.lo) + " 以上";
      return "<tr><td>" + lab + ' 公尺</td><td class="n">' + num(b.n) + "（" + (b.n / tot * 100).toFixed(b.n / tot < .1 ? 1 : 0) + '%）</td><td class="n">' + (b.share * 100).toFixed(b.share < .1 ? 1 : 0) + '%</td><td class="n">' + Math.round(b.land * 100) + '%</td><td class="n">' + (b.year || "—") + "</td></tr>";
    }).join("");
    return '<div class="method-b" style="margin-top:16px;overflow-x:auto"><h3>各高度帶</h3><table class="mini-t"><thead><tr><th>海拔</th><th class="n">文資（全臺）</th><th class="n">文資（本島）</th><th class="n">本島土地</th><th class="n">中位創建年</th></tr></thead><tbody>' + rows +
      '</tbody></table><p class="hint" style="margin-top:6px">「本島」是臺灣本島與綠島、蘭嶼、龜山島，不含澎湖、金門、馬祖，才能和本島土地比較。土地比例由同一套數值地表模型算出。</p></div>';
  }

  /* ---------- 高度剖面 ---------- */
  function paintControls() {
    var opts = '<option value="-1">全部縣市</option>' + D.counties.map(function (c, i) { return '<option value="' + i + '"' + (state.county === i ? " selected" : "") + ">" + esc(c.name) + "</option>"; }).join("");
    document.getElementById("pf-ctl").innerHTML =
      '<div class="flt-g" role="group" aria-label="顏色"><span class="flt-l">顏色</span><div class="seg"><button type="button" data-color="era" aria-pressed="' + (state.color === "era") + '">時代</button><button type="button" data-color="cat" aria-pressed="' + (state.color === "cat") + '">類型</button></div></div>' +
      '<div class="flt-g"><label class="flt-l" for="pf-county">縣市</label><select id="pf-county">' + opts + "</select></div>" +
      (state.hl ? '<div class="flt-g"><span class="chip" aria-pressed="true">' + esc(state.hlLabel) + '</span><button type="button" class="link" data-clear>清除標示</button></div>' : "");
    var lg = state.color === "era" ? D.eras.map(function (e, i) { return '<span class="ev' + i + '"><i></i>' + esc(e.name) + "</span>"; }) : LV.map(function (n, i) { return '<span class="lv' + i + '"><i></i>' + n + "</span>"; });
    document.getElementById("pf-legend").innerHTML = lg.join("") + '<span><i class="u"></i>空心：海拔不確定</span><span><i class="land"></i>本島土地</span>';
  }
  var PF = null;
  function layoutProfile(W) {
    var S = D.sites, n = S.length, mob = W < 640;
    var LW = mob ? 64 : Math.min(190, Math.round(W * 0.2)), x0 = LW, DW = W - x0 - 10;
    var Hmin = mob ? 900 : 1000, Hmax = mob ? 2600 : 1800, pick = null;
    var u = S.map(function (o) { return U(o.h); });
    /* 每一列高 d×k、可疊 k 行；找點最大、行數最少、又放得下的組合 */
    [[7, 1], [6, 1], [5, 1], [5, 2], [4.4, 2], [4.4, 3], [4, 3], [4, 4]].some(function (dk) {
      var d = dk[0], k = dk[1], cap = Math.floor((DW - 6) / d);
      for (var pxu = Hmin / UMAX; pxu * UMAX <= Hmax; pxu *= 1.06) {
        var cnt = {}, mx = 0;
        for (var i = 0; i < n; i++) { var r = Math.floor((UMAX - u[i]) * pxu / (d * k)); cnt[r] = (cnt[r] || 0) + 1; if (cnt[r] > mx) mx = cnt[r]; }
        if (mx <= cap * k) { pick = { d: d, k: k, pxu: pxu, cap: cap }; return true; }
      }
      return false;
    });
    if (!pick) pick = { d: 4, k: 4, pxu: Hmax / UMAX, cap: Math.floor((DW - 6) / 4) };
    return { W: W, LW: LW, x0: x0, DW: DW, d: pick.d, k: pick.k, R: pick.d * pick.k, cap: pick.cap, pxu: pick.pxu, top: 34, H: UMAX * pick.pxu, mob: mob };
  }
  function yOf(L, h) { return L.top + (UMAX - U(h)) * L.pxu; }
  function drawProfile() {
    var wrap = document.getElementById("pf-wrap"); if (!wrap) return;
    var svg = document.getElementById("pf"), W = svg.clientWidth || wrap.clientWidth - 24;
    var L = layoutProfile(W), S = D.sites, d = L.d, R = L.R, s = [];
    PF = L;
    var Ht = L.top + L.H + 40;
    svg.setAttribute("viewBox", "0 0 " + W + " " + Ht); svg.setAttribute("height", Ht);
    s.push('<defs><linearGradient id="skyg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--sea)" stop-opacity=".10"/><stop offset=".6" stop-color="var(--sea)" stop-opacity="0"/></linearGradient></defs>');
    s.push('<rect class="sky" x="0" y="0" width="' + W + '" height="' + (L.top + L.H) + '"/>');
    /* 土地：每列的面積比例＝該高度的密度 × 列的公尺跨度 */
    var sh = D.land.share, step = D.land.step, rows = Math.ceil(L.H / R), land = [], mx = 0;
    for (var r = 0; r < rows; r++) {
      var uTop = UMAX - r * R / L.pxu, uBot = UMAX - (r + 1) * R / L.pxu, hT = Uinv(uTop), hB = Uinv(Math.max(0, uBot)), hm = (hT + hB) / 2;
      var b = Math.floor(hm / step), dens = (sh[b] || 0) / step, v = dens * (hT - hB);
      land.push(v); if (v > mx) mx = v;
    }
    var pth = "M" + L.x0 + " " + L.top;
    land.forEach(function (v, r) { var x = L.x0 - v / mx * (L.LW - 6); pth += "L" + x.toFixed(1) + " " + (L.top + r * R).toFixed(1) + "L" + x.toFixed(1) + " " + (L.top + (r + 1) * R).toFixed(1); });
    pth += "L" + L.x0 + " " + (L.top + rows * R) + "Z";
    s.push('<path class="landa" d="' + pth + '"/>');
    /* 刻度 */
    var ticks = [0, 5, 10, 20, 30, 50, 100, 200, 500, 1000, 2000, 3000], major = { 20: 1, 100: 1, 500: 1, 1000: 1 };
    ticks.forEach(function (h) {
      var y = yOf(L, h);
      if (L.mob && (h === 5 || h === 30)) return;
      s.push('<g class="tick' + (major[h] ? " major" : "") + '"><line x1="' + (L.x0 - (major[h] ? L.LW : 6)) + '" x2="' + (major[h] ? W : L.x0) + '" y1="' + y.toFixed(1) + '" y2="' + y.toFixed(1) + '"/>' +
        '<text x="' + (L.x0 - 6) + '" y="' + (y - 3).toFixed(1) + '" text-anchor="end" paint-order="stroke" stroke="var(--card)" stroke-width="3">' + num(h) + (h === 0 ? "" : "") + "</text></g>");
    });
    s.push('<line class="axis" x1="' + L.x0 + '" x2="' + L.x0 + '" y1="' + L.top + '" y2="' + (L.top + L.H + 6) + '"/>');
    /* 海平面 */
    var y0 = L.top + L.H;
    var wave = "M0 " + (y0 + 4);
    for (var x = 0; x <= W; x += 16) wave += "q4 -4 8 0t8 0";
    s.push('<path class="seaf" d="' + wave + "V" + (Ht) + "H0Z" + '"/>');
    s.push('<text class="lbl" x="' + (L.x0 + 6) + '" y="' + (y0 + 24) + '">海平面 0 公尺</text>');
    s.push('<text class="hd" x="' + (L.x0 - 8) + '" y="16" text-anchor="end">本島土地</text><text class="hd" x="' + (L.x0 + 8) + '" y="16">文資（一點一處）</text>');
    /* 玉山 */
    var yp = yOf(L, PEAK);
    s.push('<path class="peak-m" d="M' + (L.x0 - 7) + " " + (yp + 6) + "l7 -12l7 12z" + '"/><text class="peak" x="' + (L.x0 + 12) + '" y="' + (yp + 4) + '">玉山主峰 3,952 公尺・本島最高點</text>');
    /* 點：每列由左到右依創建年 */
    var byRow = {};
    S.forEach(function (o, i) { var r = Math.floor((UMAX - U(o.h)) * L.pxu / R); (byRow[r] = byRow[r] || []).push(i); });
    var col = state.color === "era" ? "ev" : "lv", hl = state.hl, dots = [];
    var pos = new Array(S.length);
    Object.keys(byRow).forEach(function (r) {
      var a = byRow[r].sort(function (i, j) { var A = S[i], B = S[j]; return (A.y == null ? 9999 : A.y) - (B.y == null ? 9999 : B.y); });
      a.forEach(function (i, k) {
        var o = S[i], ln = Math.floor(k / L.cap), cx = L.x0 + 4 + (k % L.cap) * d + d / 2, cy = L.top + r * R + (L.k - 1 - ln) * d + d / 2;
        pos[i] = [cx, cy];
        dots.push('<circle class="dot ' + col + (col === "ev" ? o.r : o.k) + (o.f === "steep" || o.f === "txt" || o.f === "coord" ? " u" : "") + (hl && hl[i] ? " hl" : "") + '" cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="' + (d / 2 - (d > 4 ? .4 : .2)).toFixed(2) + '" data-i="' + i + '"/>');
      });
    });
    s.push('<g class="dots">' + dots.join("") + "</g>");
    /* 縣市中位數 */
    if (state.county >= 0) {
      var hs = S.filter(function (o) { return o.c === state.county; }).map(function (o) { return o.h; }).sort(function (a, b) { return a - b; });
      var ym = yOf(L, q(hs, .5));
      s.push('<line class="medl" x1="' + (L.x0 - 10) + '" x2="' + (W - 4) + '" y1="' + ym.toFixed(1) + '" y2="' + ym.toFixed(1) + '"/><text class="medt" x="' + (W - 6) + '" y="' + (ym - 6).toFixed(1) + '" text-anchor="end">' + esc(D.counties[state.county].name) + "中位數 " + num(q(hs, .5)) + " 公尺</text>");
    }
    /* 高處的名字：1,000 公尺以上逐一標出，往下推開避免重疊 */
    var hk = hl ? Object.keys(hl).map(Number) : [];
    var tags = hl && hk.length <= 20 ? hk : S.map(function (o, i) { return i; }).filter(function (i) { return S[i].h >= 1000 && (!hl || hl[i]); });
    tags.sort(function (a, b) { return S[b].h - S[a].h; });
    var tx = L.x0 + Math.max(L.mob ? 44 : 70, d * 9), lastY = -99, gap = L.mob ? 15 : 16, maxc = L.mob ? 11 : 26;
    tags.forEach(function (i) {
      var o = S[i], p = pos[i], ty = Math.max(p[1] + 4, lastY + gap); lastY = ty;
      var nm = o.n.length > maxc ? o.n.slice(0, maxc - 1) + "…" : o.n;
      s.push('<path class="tag-l" d="M' + (p[0] + d / 2 + 1) + " " + p[1] + "L" + (tx - 4) + " " + (ty - 4) + '"/>' +
        '<text class="tag" data-i="' + i + '" x="' + tx + '" y="' + ty + '">' + esc(nm) + "<tspan> " + num(o.h) + "</tspan></text>");
    });
    svg.innerHTML = s.join("");
    svg.classList.toggle("hl-on", !!hl);
    var shown = hl ? Object.keys(hl).length : S.length;
    document.getElementById("pf-sum").innerHTML = hl ? "標示中：<b>" + num(shown) + "</b> 處" : "共 <b>" + num(S.length) + "</b> 處・最高 <b>" + num(S[D.top10[0]].h) + "</b> 公尺";
  }
  function setHL(set, label, face) {
    state.hl = set; state.hlLabel = label || "";
    paintControls(); drawProfile();
    var box = document.getElementById("pf-say"); if (!box) return;
    if (!set) { box.innerHTML = ""; return; }
    var n = Object.keys(set).length, hs = Object.keys(set).map(function (i) { return D.sites[i].h; }).sort(function (a, b) { return a - b; });
    var f = face || ["R", "explain"];
    box.innerHTML = say(f[0], f[1], "標出來了：「" + esc(label) + "」共 " + num(n) + " 處，海拔中位數 " + num(q(hs, .5)) + " 公尺。其他的點先調淡。");
  }
  function factHL(x) {
    var S = D.sites, set = {}, any = false;
    S.forEach(function (o, i) {
      var on = false;
      if (x.band) on = o.h >= x.band[0] && o.h <= x.band[1];
      if (x.ids) on = x.ids.indexOf(key(o)) >= 0;
      if (x.era) on = x.era.indexOf(o.r) >= 0;
      if (x.cat) on = x.cat.indexOf(o.k) >= 0;
      if (on) { set[i] = 1; any = true; }
    });
    return any ? set : null;
  }

  /* ---------- 時代與類型的比較 ---------- */
  function drawCmp(id, field, names, cls) {
    var svg = document.getElementById(id); if (!svg) return;
    var W = svg.clientWidth || 400, LX = 98, RX = W - 12, rowH = 34, groups = [];
    names.forEach(function (nm, gi) {
      var a = D.sites.filter(function (o) { return o[field] === gi; }).map(function (o) { return o.h; }).sort(function (x, y) { return x - y; });
      if (a.length) groups.push({ gi: gi, nm: nm, n: a.length, q1: q(a, .25), md: q(a, .5), q3: q(a, .75), p90: q(a, .9) });
    });
    var umx = U(1000);
    function X(h) { return LX + Math.min(1, U(h) / umx) * (RX - LX); }
    var H = groups.length * rowH + 26, s = [];
    [0, 10, 20, 50, 100, 200, 500, 1000].forEach(function (h) {
      if (W < 380 && (h === 10 || h === 200)) return;
      s.push('<g class="gx"><line x1="' + X(h) + '" x2="' + X(h) + '" y1="0" y2="' + (H - 18) + '"/><text x="' + X(h) + '" y="' + (H - 4) + '">' + num(h) + "</text></g>");
    });
    groups.forEach(function (g, k) {
      var y = k * rowH + 18;
      s.push('<g class="' + cls + g.gi + '"><text class="rl" x="0" y="' + (y + 1) + '">' + esc(g.nm) + '</text><text class="rn" x="0" y="' + (y + 14) + '">' + num(g.n) + " 處</text>" +
        '<line class="p90" x1="' + X(g.q1) + '" x2="' + X(g.p90) + '" y1="' + y + '" y2="' + y + '"/>' +
        '<line class="iqr" x1="' + X(g.q1) + '" x2="' + X(g.q3) + '" y1="' + y + '" y2="' + y + '"/>' +
        '<circle class="md" cx="' + X(g.md) + '" cy="' + y + '" r="6"><title>' + esc(g.nm) + "：中位數 " + num(g.md) + " 公尺，中間一半 " + num(g.q1) + "–" + num(g.q3) + " 公尺，第 90 百分位 " + num(g.p90) + " 公尺</title></circle>" +
        '<text class="mv" x="' + (X(g.md)) + '" y="' + (y - 9) + '" text-anchor="middle">' + num(g.md) + "</text></g>");
    });
    svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.setAttribute("height", H);
    svg.innerHTML = s.join("");
  }

  /* ---------- 最高的十處、縣市、方法 ---------- */
  function flagTag(o) { return o.f === "txt" ? '<span class="flagt">依介紹文字</span>' : (o.f ? '<span class="flagt">海拔不確定</span>' : ""); }
  function top10() {
    return '<ol class="top10">' + D.top10.map(function (i, k) {
      var o = D.sites[i];
      return '<li><button type="button" class="t10 lv' + o.k + '" data-open="' + i + '"><span class="t10-ph">' + img(o, "s") + '<span class="t10-n">' + (k + 1) + '</span></span><span class="t10-b"><span class="t10-h">' + num(o.h) +
        "<small>公尺</small></span><span class=\"t10-t\">" + esc(o.n) + '</span><span class="t10-m">' + esc(D.counties[o.c].name) + "・" + LV[o.k] + "・" + yearText(o) + "</span>" + flagTag(o) + "</span></button></li>";
    }).join("") + "</ol>";
  }
  function countyList() {
    var umx = U(2500);
    return '<div class="cty-key"><span><i class="k1"></i>該縣市最高一處的海拔</span><span><i class="k2"></i>該縣市文資的海拔中位數</span><span>長度用同一把高度尺</span></div><ol class="cty">' + D.countyTop.map(function (r) {
      var o = D.sites.filter(function (x) { return x.c === r.c && x.i === r.i; })[0], idx = D.sites.indexOf(o);
      return '<li><button type="button" data-open="' + idx + '"><span class="cty-c">' + esc(D.counties[r.c].name) + '</span><span class="cty-m"><small>' + esc(o.n) + '</small><span class="cty-bar" style="--w:' + (U(r.h) / umx * 100).toFixed(1) + "%;--m:" + (U(r.med) / umx * 100).toFixed(1) + '%"><i></i><em></em></span></span>' +
        '<span class="cty-v"><b>' + num(r.h) + "</b> 公尺<br>中位 " + num(r.med) + "</span></button></li>";
    }).join("") + "</ol>";
  }
  function methodBox() {
    var m = D.meta, c = m.check;
    var rows = D.checks.map(function (r) {
      var o = D.sites[r[0]], diff = r[2] - r[3];
      return '<tr><td><button type="button" data-open="' + r[0] + '">' + esc(o.n) + "</button></td><td>" + esc(r[1]) + '</td><td class="n">' + num(r[2]) + '</td><td class="n">' + (diff > 0 ? "+" : "") + num(diff) + "</td></tr>";
    }).join("");
    return '<div class="method"><div class="method-b"><h3>做法</h3><ul>' +
      "<li>地形資料用歐盟哥白尼計畫的 Copernicus DEM（GLO-30，約 30 公尺網格），在每處文資的座標點內插取值。這是數值<b>地表</b>模型，含樹冠與建築的高度。</li>" +
      "<li>內政部 20 公尺網格數值地形模型（DTM）解析度較高、也去除了地物，但本站建置時無法從主機取得檔案，所以沒有採用。</li>" +
      "<li>座標周圍約 200 公尺內高低差超過 " + m.steep + " 公尺的，標為「海拔不確定」（" + m.flags.steep + " 處），圖上畫成空心點。知識網站註明座標未能核對的也一樣（" + m.flags.coord + " 處）。</li>" +
      "<li>知識網站的介紹文字有 " + c.n + " 處寫明海拔。推估與文字的中位差是 " + c.medAbs + " 公尺；相差超過 50 公尺且超過 5% 的 " + c.adopted + " 處，改用文字的數字（標「依介紹文字」）。這幾處都是座標點不在文資本體上，例如七家灣考古遺址的座標落在武陵農場西邊約 2 公里的山坡，推估成 2,476 公尺，介紹文字寫的是 1,500 公尺以上。</li>" +
      "<li>換成更細的網格幫助不大：30 公尺網格與 140 公尺網格的結果，中位差只有 1 公尺左右；山區的大誤差主要來自座標，不是地形資料。</li></ul>" +
      '<p class="hint">' + esc(m.dem.attribution) + "。" + esc(m.dem.disclaimer) + "。</p></div>" +
      '<div class="method-b"><h3>和介紹文字比對（' + c.n + ' 處）</h3><div style="overflow-x:auto"><table class="mini-t"><thead><tr><th>文資</th><th>介紹文字</th><th>座標點推估</th><th>差</th></tr></thead><tbody>' + rows + "</tbody></table></div></div></div>";
  }

  /* ---------- 文資卡片 ---------- */
  function openCard(i) {
    var o = D.sites[i]; if (!o) return;
    var kb = D.counties[o.c].base + "#map/" + o.i, lic = o.p ? D.lic[o.p[3]] : null;
    var credit = o.p ? "<figcaption>攝影：" + (o.p[4] ? '<a href="https://commons.wikimedia.org/wiki/File:' + esc(o.p[4]) + '" target="_blank" rel="noopener">' + esc(o.p[2] || "Wikimedia Commons") + "</a>" : esc(o.p[2])) + "｜" +
      (lic && lic[1] ? '<a href="' + esc(lic[1]) + '" target="_blank" rel="noopener">' + esc(lic[0]) + "</a>" : esc(lic ? lic[0] : "")) + "</figcaption>" : "";
    var rl = o.rl ? '<a class="btn btn-rail" href="' + D.meta.railUrl + "#/line/" + o.rl[0] + "/" + o.rl[1] + '" target="_blank" rel="noopener">搭火車：' + esc(o.rl[2]) + "站走 " + o.rl[3] + " 分</a>" : "";
    var rank = D.sites.filter(function (x) { return x.h > o.h; }).length + 1, lower = D.sites.filter(function (x) { return x.h < o.h; }).length, tipc;
    if (o.f === "txt") tipc = say("A", "scratch", "這處的座標點不在本體上，直接取值會差很多，所以海拔改用介紹文字的數字。");
    else if (o.f) tipc = say("A", "scratch", "這處的海拔不太確定，座標稍微偏一點就會差很多，看看就好。");
    else if (rank <= 10) tipc = say("R", "surprised", "全臺第 " + rank + " 高的文資！");
    else if (o.rl) tipc = say("R", "thumb", "搭火車到" + esc(o.rl[2]) + "站，走 " + o.rl[3] + " 分鐘就到（推估）。");
    else tipc = say("R", "explain", "它比全臺 " + Math.round(lower / D.sites.length * 100) + "% 的文資住得高。");
    dlg.innerHTML = '<button type="button" class="dlg-x" data-close aria-label="關閉">×</button><article class="card lvc' + o.k + '">' +
      '<figure class="card-ph' + (o.p ? "" : " nophoto") + '">' + img(o, "l") + credit + "</figure>" +
      '<div class="card-b"><p class="card-meta"><span class="lvt lv' + o.k + '">' + LV[o.k] + "</span><span>" + yearText(o) + "・" + esc(D.eras[o.r].name) + "</span></p>" +
      "<h3>" + esc(o.n) + '</h3><p class="card-s">' + esc(o.s) + "</p>" +
      '<dl class="card-f"><div><dt>海拔（推估）</dt><dd><b' + (o.f ? ' class="u"' : "") + ">" + num(o.h) + "</b> 公尺</dd></div><div><dt>全臺第</dt><dd><b>" + num(rank) + "</b> 高</dd></div><div><dt>所在</dt><dd>" + esc(D.counties[o.c].name + o.t) + "</dd></div></dl>" +
      tipc + (o.fn ? '<p class="card-note"><b>' + (o.f === "txt" ? "依介紹文字" : "海拔不確定") + "</b>　" + esc(o.fn) + "</p>" : "") +
      '<p class="card-a"><a class="btn btn-solid" href="' + esc(kb) + '" target="_blank" rel="noopener">看完整介紹</a>' + rl + "</p></div></article>";
    if (!dlg.open) { if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", ""); }
  }
  function closeCard() { if (dlg.open) { if (dlg.close) dlg.close(); else dlg.removeAttribute("open"); } }
  dlg.addEventListener("close", function () { if (/^#\/s\//.test(location.hash)) history.replaceState(null, "", "#/"); });
  dlg.addEventListener("click", function (e) { if (e.target === dlg || e.target.closest("[data-close]")) closeCard(); });

  /* ---------- 其他頁 ---------- */
  function viewSoon(which) {
    var t = which === "river" ? ["單元 2", "溯河而上", "從出海口到源頭，文資依距出海口的公里數排在左右兩岸。河道資料與收錄規則確認後開始製作。"] :
      ["單元 3", "越嶺古道", "臺灣的歷史古道與越嶺道，沿線的高度剖面、駐在所與遺址。路線資料與出處確認後開始製作。"];
    app.innerHTML = '<section class="home-hero"><div class="wrap"><p class="kicker">從海口到山頂・' + t[0] + "</p><h1>" + t[1] + '</h1><p class="lede">' + t[2] + "</p>" +
      '<div class="talk">' + say("R", "sad", "這個單元還在整理資料，先回海拔總覽看看吧。") + "</div>" + units(which) + "</div></section>";
  }
  function viewAbout() {
    var m = D.meta;
    app.innerHTML = '<section class="wrap about"><h1>資料說明</h1>' +
      "<h2>文化資產</h2><p>全臺 " + num(m.total) + " 處有形文化資產的名稱、等級、座標與年代，來自文化部文化資產局國家文化資產網，經兩個文資知識網站整理，主檔沿用文資地圖集；時代一律由創建年重新計算。照片來自 Wikimedia Commons，作者與授權標在卡片照片下方。</p>" +
      "<h2>海拔</h2><p>全部是<b>推估</b>。地形資料：" + esc(m.dem.source) + "。" + esc(m.dem.attribution) + "。" + esc(m.dem.disclaimer) + "。</p>" +
      "<p>做法與誤差：在文資座標點內插取值（約 30 公尺網格，含樹冠與建築）；座標周圍高低差大的標為海拔不確定；介紹文字寫明海拔且相差過大的改用文字。詳見海拔總覽頁的「海拔怎麼算的」。</p>" +
      "<h3>高度尺</h3><p>剖面的縱軸是 ln(1 + 海拔 ÷ 5)：低處放大、高處壓縮，0 到 20 公尺和 500 到 2,000 公尺佔的高度差不多。全站（包括之後的河流與山徑剖面）都用同一把尺，刻度上的數字是實際公尺。</p>" +
      "<h3>本島土地的高度分布</h3><p>同一套地形資料，北緯 21.8–25.4 度、東經 120–122.1 度範圍內高於 0 公尺的格子，約每 90 公尺取一格統計；含綠島、蘭嶼、龜山島。</p>" +
      "<h2>鐵道連結</h2><p>文資卡片上的「搭火車」連到姊妹站搭火車逛文資，條件是該處在某個臺鐵車站步行 15 分鐘（推估）內；有多個車站時取最近的一站。</p>" +
      '<p class="hint">資料產生日期：' + esc(m.generated) + "</p></section>";
  }

  /* ---------- 路由 ---------- */
  var cur = "";
  function route() {
    var parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean), page = parts[0] || "home";
    if (page === "s") page = "home";
    document.querySelectorAll("[data-nav]").forEach(function (a) { a.classList.toggle("cur", a.dataset.nav === page); });
    if (page !== cur) {
      closeCard();
      if (page === "river" || page === "trail") { viewSoon(page); document.title = (page === "river" ? "溯河而上" : "越嶺古道") + "｜從海口到山頂"; }
      else if (page === "about") { viewAbout(); document.title = "資料說明｜從海口到山頂"; }
      else { viewHome(); document.title = "從海口到山頂｜Allan 和阿拉蕾陪你看文資住在多高"; }
      if (parts[0] !== "s") window.scrollTo(0, 0);
      cur = page;
    }
    if (parts[0] === "s") {
      var c = +parts[1], id = decodeURIComponent(parts[2] || ""), i = -1;
      D.sites.forEach(function (o, k) { if (o.c === c && o.i === id) i = k; });
      if (i >= 0) openCard(i);
    }
  }
  function openHash(i) { var o = D.sites[i]; location.hash = "#/s/" + o.c + "/" + encodeURIComponent(o.i); }

  /* ---------- 事件 ---------- */
  var tip = null;
  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-open],[data-fact],[data-color],[data-clear],.dot,.tag"); if (!t) return;
    if (t.dataset.open) { openHash(+t.dataset.open); return; }
    if (t.classList.contains("dot") || t.classList.contains("tag")) { openHash(+t.dataset.i); return; }
    if (t.dataset.fact) {
      var x = D.facts[+t.dataset.fact];
      setHL(factHL(x), x.k, FACT_FACE[x.k]);
      document.getElementById("profile").scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
      return;
    }
    if (t.dataset.color) { state.color = t.dataset.color; paintControls(); drawProfile(); return; }
    if ("clear" in t.dataset) { state.county = -1; setHL(null, ""); }
  });
  document.addEventListener("change", function (e) {
    if (e.target.id !== "pf-county") return;
    state.county = +e.target.value;
    if (state.county < 0) { setHL(null, ""); return; }
    var set = {}; D.sites.forEach(function (o, i) { if (o.c === state.county) set[i] = 1; });
    setHL(set, D.counties[state.county].name, ["A", "smile"]);
  });
  function showTip(e) {
    tip = tip || document.getElementById("tip");
    var t = e.target.closest && e.target.closest(".dot"); if (!tip) return;
    document.querySelectorAll(".dot.hot").forEach(function (x) { if (x !== t) x.classList.remove("hot"); });
    if (!t) { tip.hidden = true; return; }
    var o = D.sites[+t.dataset.i], wrap = document.getElementById("pf-wrap").getBoundingClientRect(), b = t.getBoundingClientRect();
    t.classList.add("hot");
    tip.innerHTML = "<b>" + esc(o.n) + "</b>" + num(o.h) + " 公尺" + (o.f ? "（不確定）" : "") + "・" + esc(D.counties[o.c].name) + "・" + yearText(o);
    tip.hidden = false;
    var x = Math.min(Math.max(b.left + b.width / 2 - wrap.left, 130), wrap.width - 130);
    tip.style.left = x + "px"; tip.style.top = (b.top - wrap.top) + "px";
  }
  document.addEventListener("pointermove", function (e) { if (e.pointerType === "mouse") showTip(e); });
  var rt = 0, lastW = 0;
  window.addEventListener("resize", function () {
    clearTimeout(rt);
    rt = setTimeout(function () {
      var svg = document.getElementById("pf"); if (!svg || svg.clientWidth === lastW) return;
      lastW = svg.clientWidth; drawProfile();
      drawCmp("cmp-era", "r", D.eras.map(function (e) { return e.name; }), "ev"); drawCmp("cmp-cat", "k", LV, "lv");
    }, 150);
  });

  getJSON("data/alt.json").then(function (d) { D = d; window.addEventListener("hashchange", route); route(); })
    .catch(function () { app.innerHTML = '<p class="loading wrap">資料載入失敗，請重新整理。</p>'; });
})();
