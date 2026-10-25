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
    if (btns.length) show(btns[0].getAttribute("data-tab"));
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
  function load(task, sid) {
    stop(); t = 0;
    var list = DATA[task] || [];
    if (selTask.tagName === "SELECT") selTask.value = task;
    selSub.innerHTML = list.map(function (e) { return "<option value='" + e.id + "'>" + e.id + " · " + e.when + " · " + e.result + (e.train ? " · training video" : "") + "</option>"; }).join("");
    if (!list.length) { selSub.innerHTML = "<option>no submissions yet</option>"; cur = null; setSrc("train", null); setSrc("target", null); meta.textContent = ""; sync(true); return; }
    cur = list.filter(function (e) { return e.id === sid; })[0] || list[0];
    selSub.value = cur.id;
    var views = cur.target ? Object.keys(cur.target.views) : [];
    var keep = selView.value;
    selView.innerHTML = views.map(function (v) { return "<option value='" + v + "'>" + v + "</option>"; }).join("") || "<option>–</option>";
    if (views.indexOf(keep) >= 0) selView.value = keep;
    setTarget();
    var tr = cur.train;
    setSrc("train", tr ? tr.src : null, tr && tr.poster);
    $("[data-gone='train'] [data-reason]", root).textContent = "No video for " + cur.id + ": " + cur.train_reason + ".";
    $("[data-source='train']", root).textContent = tr ? "Source: agent-registered training rollout of " + cur.id + (tr.simulator ? " · " + tr.simulator : "") + " · video " + (tr.sha || "") + " · registered " + tr.recorded + " (" + (tr.timing === "after_result" ? "after" : "before") + " the target result)" : "";
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
