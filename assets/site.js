(function () {
  "use strict";
  document.documentElement.classList.add("js");
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // relative times ("5 min ago") next to absolute timestamps
  function ago(iso) {
    var s = (Date.now() - new Date(iso).getTime()) / 1000;
    if (!isFinite(s)) return "";
    if (s < 60) return "just now";
    var m = s / 60; if (m < 60) return Math.round(m) + " min ago";
    var h = m / 60; if (h < 48) return Math.round(h) + " h ago";
    return Math.round(h / 24) + " d ago";
  }
  function rels() { $$("[data-rel]").forEach(function (e) { e.textContent = "· " + ago(e.getAttribute("data-rel")); }); }
  rels(); setInterval(rels, 30000);

  // tabs (without JavaScript every panel stays visible)
  var tabsets = {};
  $$("[data-tabs]").forEach(function (box) {
    var g = box.getAttribute("data-tabs"), btns = $$("[data-tab]", box), panels = $$("[data-panel-group='" + g + "']");
    function show(k) {
      btns.forEach(function (b) { b.setAttribute("aria-selected", b.getAttribute("data-tab") === k ? "true" : "false"); });
      panels.forEach(function (p) { p.hidden = p.getAttribute("data-panel") !== k; });
    }
    btns.forEach(function (b) { b.addEventListener("click", function () { show(b.getAttribute("data-tab")); }); });
    var d = box.getAttribute("data-default");
    if (btns.length) show(btns.some(function (b) { return b.getAttribute("data-tab") === d; }) ? d : btns[0].getAttribute("data-tab"));
    tabsets[g] = show;
  });

  // freshness: the page is static; the data feed is re-read without caching to flag stale or newer data
  var body = document.body, exported = body.getAttribute("data-exported"), feed = body.getAttribute("data-feed");
  var stale = $("#stale"), newer = $("#newer");
  if (newer) $("button", newer).addEventListener("click", function () { location.reload(); });
  function age(iso) { return (Date.now() - new Date(iso).getTime()) / 60000; }
  function fresh() {
    var latest = exported;
    function flag() {
      if (!stale || !latest) return;
      var a = age(latest);
      stale.classList.toggle("on", a > 30);
      $("span", stale).textContent = Math.round(a) + " min";
    }
    flag();
    if (!feed || !window.fetch) return;
    fetch(feed + "?t=" + Date.now(), { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (d) {
      if (d.exported_utc) {
        if (exported && d.exported_utc > exported && newer) newer.classList.add("on");
        latest = d.exported_utc; flag();
      }
    }).catch(function () {});
  }
  fresh(); setInterval(fresh, 120000);

  // toss-height chart on narrow screens: open scrolled to the newest submissions
  $$(".toss .cw").forEach(function (c) { c.scrollLeft = c.scrollWidth; });

  // Demo-to-Sim reconstruction preview: playback speed buttons
  $$("[data-recon]").forEach(function (box) {
    var v = $("video", box), btns = $$("[data-rate]", box);
    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        v.playbackRate = +b.getAttribute("data-rate");
        btns.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      });
    });
  });

  // a tab named by the URL fragment opens (docs/index.html#pen); hash changes switch it too
  function hashTab() {
    var h = location.hash.slice(1);
    if (!h) return;
    $$("[data-tabs]").forEach(function (box) {
      if ($$("[data-tab]", box).some(function (b) { return b.getAttribute("data-tab") === h; })) tabsets[box.getAttribute("data-tabs")](h);
    });
  }
  hashTab(); window.addEventListener("hashchange", hashTab);

  // progress score vs. submission charts: drawn at the container's width from the embedded official points
  var NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function txt(x, y, s, cls, parent, anchor) { var e = el("text", { x: x, y: y, "class": cls, "text-anchor": anchor || "middle" }, parent); e.textContent = s; return e; }
  function niceStep(span, n) { var r = span / n, s = [1, 2, 5, 10, 20, 25, 50, 100]; for (var i = 0; i < s.length; i++) if (s[i] >= r) return s[i]; return 100; }
  function tipLines(p, s) {
    var L = [[p.id, " · " + s.label, true], ["Progress score: ", p.score == null ? "no score" : p.score.toFixed(2)], ["Status: ", p.status + (p.best ? " · best of its version group" : "")], ["Submitted: ", p.date]];
    var st = Object.keys(p.stages || {}).map(function (k) { return k + " " + (+p.stages[k]).toFixed(2); }).join(" · ");
    if (st) L.push(["Stages: ", st]);
    if (p.hw || p.rt) L.push(["Run: ", (p.rt ? "run " + p.rt : "") + (p.hw && p.rt ? " · " : "") + (p.hw ? "hardware " + p.hw : "")]);
    if (p.cmp) L.push(["Change: ", p.cmp]);
    return L;
  }
  function drawChart(box) {
    var plot = $(".cplot", box), data;
    try { data = JSON.parse($("script.chart-data", box).textContent); } catch (e) { return; }
    var compact = box.hasAttribute("data-compact"), W = Math.max(260, plot.clientWidth);
    var all = []; data.series.forEach(function (s) { s.points.forEach(function (p) { all.push(p); }); });
    var hasNS = all.some(function (p) { return p.score == null; });
    var m = { l: 60, r: 14, t: 16, b: 38 }, ns = hasNS ? 24 : 0, ph = compact ? 140 : (W < 560 ? 200 : 260), H = m.t + ph + ns + m.b;
    var maxN = Math.max(5, Math.max.apply(null, all.map(function (p) { return p.n; })));
    var X = function (n) { return m.l + 10 + (n - 1) / (maxN - 1) * (W - m.l - m.r - 20); }, Y = function (v) { return m.t + (1 - v) * ph; };
    plot.innerHTML = "";
    var svg = el("svg", { viewBox: "0 0 " + W + " " + H, width: W, height: H, "aria-hidden": "true" }, plot);
    [0, 0.25, 0.5, 0.75, 1].forEach(function (v) {
      el("line", { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), "class": v === 0 ? "base" : "grid" }, svg);
      txt(m.l - 8, Y(v) + 4, v === 0 ? "0" : v === 1 ? "1" : v.toFixed(2), "ax", svg, "end");
    });
    var step = niceStep(maxN, compact ? 5 : (W < 560 ? 6 : 10)), yb = m.t + ph + ns;
    for (var n = 1; n <= maxN; n += (n === 1 && step > 1 ? step - 1 : step)) txt(X(n), yb + 16, String(n), "ax", svg);
    txt((m.l + W - m.r) / 2, H - 4, "Submission number", "axt", svg);
    var yl = el("text", { x: 12, y: m.t + ph / 2, "class": "axt", "text-anchor": "middle", transform: "rotate(-90 12 " + (m.t + ph / 2) + ")" }, svg);
    yl.textContent = "Progress score";
    if (hasNS) { el("rect", { x: m.l, y: m.t + ph + 4, width: W - m.l - m.r, height: ns - 6, rx: 4, "class": "nsband" }, svg); txt(m.l - 8, m.t + ph + ns / 2 + 4, "no score", "ax", svg, "end"); }
    if (!all.some(function (p) { return p.score != null; })) txt((m.l + W - m.r) / 2, m.t + ph / 2, all.every(function (p) { return p.undefined; }) ? "Not scored: success criteria undefined" : "No scored submission yet", "axt", svg);
    var tip = document.createElement("div"); tip.className = "ctip"; tip.hidden = true; plot.appendChild(tip);
    function show(p, s, x, y) {
      tip.innerHTML = "";
      tipLines(p, s).forEach(function (l, i) {
        var d = document.createElement("div");
        if (i === 0) { var b = document.createElement("b"); b.textContent = l[0]; d.appendChild(b); d.appendChild(document.createTextNode(l[1])); }
        else { var k = document.createElement("span"); k.className = "k"; k.textContent = l[0]; d.appendChild(k); d.appendChild(document.createTextNode(l[1])); }
        tip.appendChild(d);
      });
      tip.hidden = false;
      var tw = tip.offsetWidth, th = tip.offsetHeight, left = Math.min(Math.max(0, x - tw / 2), W - tw), top = y - th - 14;
      if (top < 0) top = y + 16;
      tip.style.left = left + "px"; tip.style.top = top + "px";
    }
    function hide() { tip.hidden = true; }
    var hits = el("g", {}, null);
    data.series.forEach(function (s) {
      var pts = s.points.slice().sort(function (a, b) { return a.n - b.n; }), byG = {};
      pts.forEach(function (p) { if (p.score != null) (byG[p.group] = byG[p.group] || []).push(p); });
      Object.keys(byG).forEach(function (g) {
        var d = byG[g].map(function (p, i) { return (i ? "L" : "M") + X(p.n).toFixed(1) + " " + Y(p.score).toFixed(1); }).join(" ");
        if (byG[g].length > 1) el("path", { d: d, "class": "ln " + s.kind }, svg);
      });
      for (var i = 1; i < pts.length; i++) if (pts[i].group !== pts[i - 1].group) {
        var xs = (X(pts[i].n) + X(pts[i - 1].n)) / 2;
        el("line", { x1: xs, x2: xs, y1: m.t, y2: m.t + ph, "class": "sep" }, svg);
        if (!compact && W >= 560) txt(xs + 4, m.t + 10, "new version group", "sept", svg, "start");
      }
      pts.forEach(function (p) {
        var x = X(p.n), y = p.score == null ? m.t + ph + ns / 2 + 1 : Y(p.score), r = compact ? 3.6 : 4.6;
        if (p.score == null) el("path", { d: "M" + (x - 4) + " " + (y - 4) + "L" + (x + 4) + " " + (y + 4) + "M" + (x + 4) + " " + (y - 4) + "L" + (x - 4) + " " + (y + 4), "class": "ns " + s.kind }, svg);
        else {
          if (p.best) el("circle", { cx: x, cy: y, r: r + 4.5, "class": "best " + s.kind }, svg);
          el("circle", { cx: x, cy: y, r: p.status === "success" ? r + 1.4 : r, "class": "pt " + s.kind + (p.status === "success" ? " success" : "") }, svg);
        }
        var h = el("circle", { cx: x, cy: y, r: 11, fill: "transparent", tabindex: "0", role: "img", "class": "hit",
          "aria-label": tipLines(p, s).map(function (l) { return l.join(""); }).join("; ") }, hits);
        var on = function () { show(p, s, x, y); }; h.addEventListener("pointerenter", on); h.addEventListener("focus", on); h.addEventListener("pointerdown", on);
        h.addEventListener("pointerleave", hide); h.addEventListener("blur", hide);
      });
    });
    svg.appendChild(hits);
  }
  var charts = $$("[data-chart]");
  function drawAll() { charts.forEach(drawChart); }
  drawAll();
  var rz; window.addEventListener("resize", function () { clearTimeout(rz); rz = setTimeout(drawAll, 150); });
  $$("[data-tab]").forEach(function (b) { b.addEventListener("click", function () { setTimeout(drawAll, 0); }); });

  // synchronized training-sim / target-sim player
  var dataEl = $("#r2s2r-data");
  var root = $("[data-player]");
  if (!dataEl || !root) return;
  var DATA = JSON.parse(dataEl.textContent).player;
  var P = function (k) { return $("[data-p='" + k + "']", root); };
  var selTask = P("task"), selSub = P("sub"), selView = P("view"), selSync = P("sync"), selSpeed = P("speed");
  var btn = P("play"), seek = P("seek"), tm = P("time"), meta = $("[data-meta]", root);
  var V = { train: $("video[data-v='train']", root), target: $("video[data-v='target']", root) };
  var cur = null, t = 0, playing = false, last = 0, speed = 1;

  function dur(k) { var v = V[k]; return v.getAttribute("src") && isFinite(v.duration) && v.duration > 0 ? v.duration : 0; }
  function total() {
    var a = cur && cur.train ? dur("train") : 0, b = cur && cur.target ? (dur("target") || cur.target.duration || 0) : 0;
    return selSync.value === "stretch" ? (b || a) : Math.max(a, b);
  }
  function clampRate(r) { return Math.min(16, Math.max(0.0625, r)); }
  function sync(force) {
    var T = total();
    seek.max = T > 0 ? T : 1;
    ["train", "target"].forEach(function (k) {
      var v = V[k], d = dur(k);
      if (!d) return;
      var target = selSync.value === "stretch" && T > 0 ? t * d / T : Math.min(t, d);
      var rate = clampRate(selSync.value === "stretch" && T > 0 ? speed * d / T : speed);
      if (Math.abs(v.playbackRate - rate) > 1e-3) v.playbackRate = rate;
      var ended = target >= d - 0.02;
      if (playing && !ended) {
        if (v.paused) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
        if (force || Math.abs(v.currentTime - target) > 0.15) v.currentTime = target;
      } else {
        if (!v.paused) v.pause();
        var hold = Math.min(target, Math.max(d - 0.01, 0));
        if (force || Math.abs(v.currentTime - hold) > 0.04) v.currentTime = hold;
      }
    });
    seek.value = t;
    tm.textContent = t.toFixed(2) + " / " + T.toFixed(2) + " s";
  }
  function tick(now) {
    if (playing) {
      t += (now - last) / 1000 * speed;
      var T = total();
      if (t >= T) { t = T; playing = false; btn.textContent = "▶ Play"; }
    }
    last = now; sync(false);
    requestAnimationFrame(tick);
  }
  function stop() { playing = false; btn.textContent = "▶ Play"; }
  function setSrc(k, src, poster) {
    var v = V[k], gone = $("[data-gone='" + k + "']", root);
    v.hidden = !src; gone.hidden = !!src;
    if (src) { if (v.getAttribute("src") !== src) { v.setAttribute("src", src); if (poster) v.setAttribute("poster", poster); v.load(); } }
    else { v.removeAttribute("src"); v.removeAttribute("poster"); v.load(); }
  }
  function setTarget() {
    var tv = cur && cur.target, view = selView.value;
    setSrc("target", tv && tv.views[view] ? tv.views[view] : null, tv && tv.posters[view]);
    $("[data-source='target']", root).textContent = tv ? "Source: official target rollout of " + cur.id + " · " + view + " camera · rendered at " + (tv.fps || "?") + " fps, web copy 30 fps · " + (tv.duration || "?") + " s" : "";
  }
  function showNow(e, newest) {
    var id = $("[data-now-id]", root), m = $("[data-now-meta]", root), tag = $("[data-now-tag]", root);
    id.textContent = e ? e.id : "–";
    m.textContent = e ? "submitted " + e.when + " · " + e.result + (e.score != null ? " " + e.score.toFixed(2) : "") : "";
    tag.className = "chip" + (e && newest && e.id !== newest.id ? " undecided" : "");
    tag.textContent = !e || !newest ? "" : e.id === newest.id ? "newest submission" : "not the newest submission · newest is " + newest.id + " (" + newest.when + ")";
  }
  function load(task, sid) {
    stop(); t = 0;
    var list = DATA[task] || [];
    if (selTask.tagName === "SELECT") selTask.value = task;
    var opt = function (e) { return "<option value='" + e.id + "'>" + e.id + (e.train ? " ● training video" : "") + " · " + e.when + " · " + e.result + "</option>"; };
    var withTv = list.filter(function (e) { return e.train; }), noTv = list.filter(function (e) { return !e.train; });
    selSub.innerHTML = (withTv.length ? "<optgroup label='With training video (" + withTv.length + ")'>" + withTv.map(opt).join("") + "</optgroup>" : "") +
      (noTv.length ? "<optgroup label='" + (withTv.length ? "Without training video" : "No training videos yet") + " (" + noTv.length + ")'>" + noTv.map(opt).join("") + "</optgroup>" : "");
    if (!list.length) { selSub.innerHTML = "<option>no submissions yet</option>"; cur = null; setSrc("train", null); setSrc("target", null); meta.textContent = ""; showNow(null, null); sync(true); return; }
    cur = list.filter(function (e) { return e.id === sid; })[0] || list.filter(function (e) { return e.train && e.target; })[0] || list[0];
    selSub.value = cur.id;
    showNow(cur, list[0]);
    var views = cur.target ? Object.keys(cur.target.views) : [];
    var keep = selView.value;
    selView.innerHTML = views.map(function (v) { return "<option value='" + v + "'>" + v + "</option>"; }).join("") || "<option>–</option>";
    if (views.indexOf(keep) >= 0) selView.value = keep;
    setTarget();
    var tr = cur.train;
    setSrc("train", tr ? tr.src : null, tr && tr.poster);
    $("[data-gone='train'] [data-reason]", root).textContent = "No video for " + cur.id + ": " + cur.train_reason + ".";
    var ext = !tr ? "" : tr.rollout === "full" ? " · full rollout (agent-stated)" : tr.rollout === "partial" ? " · partial rollout (agent-stated): starts " + (tr.start || "?") + ", " + (tr.stated != null ? tr.stated + " s" : "?") + "; limitations: " + (tr.limits || "?") : " · rollout extent not stated";
    var len = tr && tr.measured != null ? " · video " + tr.measured.toFixed(1) + " s" + (cur.target && cur.target.duration ? " (target episode " + (+cur.target.duration).toFixed(1) + " s)" : "") : "";
    $("[data-source='train']", root).textContent = tr ? "Source: agent-registered training rollout of " + cur.id + (tr.simulator ? " · " + tr.simulator : "") + (tr.local_run ? " · local run " + tr.local_run : "") + (tr.match === "verified" ? " · package verified (same SHA-256 as " + cur.id + ")" : " · package not verified") + ext + len + " · file " + (tr.sha || "") + " · registered " + tr.recorded + " (" + (tr.timing === "after_result" ? "after" : "before") + " the target result)" : "";
    meta.textContent = cur.id + " · policy " + (cur.policy || "–") + " · package " + (cur.package || "–") + " · submitted " + cur.when;
    sync(true);
  }
  ["train", "target"].forEach(function (k) { V[k].addEventListener("loadedmetadata", function () { sync(true); }); });
  btn.addEventListener("click", function () {
    if (!cur) return;
    if (!playing && t >= total() - 0.01) t = 0;
    playing = !playing; btn.textContent = playing ? "❚❚ Pause" : "▶ Play";
    last = performance.now(); sync(true);
  });
  seek.addEventListener("input", function () { t = +seek.value; sync(true); });
  selSpeed.addEventListener("change", function () { speed = +selSpeed.value; sync(true); });
  selSync.addEventListener("change", function () { t = Math.min(t, total()); sync(true); });
  selView.addEventListener("change", function () { setTarget(); });
  selSub.addEventListener("change", function () { load(selTask.value, selSub.value); });
  if (selTask.tagName === "SELECT") selTask.addEventListener("change", function () { load(selTask.value); });
  $$("[data-compare]").forEach(function (b) {
    b.addEventListener("click", function () {
      load(b.getAttribute("data-compare"), b.getAttribute("data-sid"));
      root.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  load(selTask.value);
  requestAnimationFrame(tick);
})();
