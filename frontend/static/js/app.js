/* =====================================================================
   CampusNav front-end
   - location search (combobox)
   - route request  (/api/route, /api/emergency)
   - map engine: view switching, zoom / pan, animated route per step
   ===================================================================== */
(function () {
  "use strict";

  var BOOT = window.BOOT;
  var VIEWS = BOOT.views;
  var SECTION = BOOT.section;
  var LOCS = BOOT.locations;
  var IMG_W = 2480, IMG_H = 1753;
  var SVGNS = "http://www.w3.org/2000/svg";

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ------------------------------------------------------------ icons */
  var ICONS = {
    straight: '<path d="M12 20V5M6 11l6-6 6 6"/>',
    head: '<path d="M12 20V5M6 11l6-6 6 6"/>',
    turn_left: '<path d="M18 20v-6a4 4 0 0 0-4-4H6M10 5L5 10l5 5"/>',
    turn_right: '<path d="M6 20v-6a4 4 0 0 1 4-4h8M14 5l5 5-5 5"/>',
    around: '<path d="M8 20V9a4 4 0 0 1 8 0v3M12 8l4 4 4-4" />',
    stairs_up: '<path d="M4 20h4v-4h4v-4h4V8h4M15 4h5v5"/>',
    stairs_down: '<path d="M4 8h4v4h4v4h4v4h4M20 15v5h-5"/>',
    lift_up: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M12 16V9M9 12l3-3 3 3"/>',
    lift_down: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M12 8v7M9 12l3 3 3-3"/>',
    door_in: '<path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M2 21h16M10 12v.01M19 9l3 3-3 3M22 12h-7"/>',
    door_out: '<path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M2 21h16M10 12v.01M22 9l-3 3 3 3M19 12h-6" transform="translate(-1 0)"/>',
    start: '<circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="9"/>',
    arrive: '<path d="M6 21V4M6 4h11l-2 4 2 4H6"/>',
    pin: '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    room: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 21v-5h6v5M9 8h.01M15 8h.01M9 12h.01M15 12h.01"/>',
    food: '<path d="M6 3v8a2 2 0 0 0 2 2v8M10 3v8M6 7h4M17 3c-2 2-3 5-3 8h3v10"/>',
    medical: '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M12 8v8M8 12h8"/>',
    security: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    sports: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    lab: '<path d="M9 3h6M10 3v6l-5.5 9.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.5L14 9V3"/>',
    parking: '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M10 16V8h3a2.5 2.5 0 0 1 0 5h-3"/>',
    washroom: '<circle cx="8" cy="5" r="2"/><circle cx="16" cy="5" r="2"/><path d="M5 22v-8l-1-4h8l-1 4v8M13 10h6l-1.5 5H18v7h-3v-7h-.5"/>',
    exit: '<path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M2 21h16M19 9l3 3-3 3M22 12h-7"/>',
    entrance: '<path d="M3 21h18M5 21V10l7-6 7 6v11M10 21v-6h4v6"/>',
    building: '<path d="M3 21h18M5 21V7l7-4 7 4v14M9 10h.01M15 10h.01M9 14h.01M15 14h.01"/>',
    office: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>',
    hall: '<path d="M3 20h18M5 20V9l7-5 7 5v11M9 20v-6h6v6"/>',
    academic: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 19a2 2 0 0 1 2-2h13"/>',
    classroom: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    facility: '<circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/>'
  };
  function icon(name, size, sw) {
    size = size || 20;
    return '<svg viewBox="0 0 24 24" width="' + size + '" height="' + size + '" fill="none" stroke="currentColor" stroke-width="' + (sw || 2.1) +
      '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONS[name] || ICONS.pin) + '</svg>';
  }
  function catIcon(loc) { return ICONS[loc.category] ? loc.category : "pin"; }

  /* ------------------------------------------------------------- state */
  var state = {
    route: null, step: 0, view: "campus", legShown: -1, browsing: false,
    vb: { x: 0, y: 0, w: IMG_W, h: IMG_H }, emergency: false,
    from: null, to: null, anim: null, vbAnim: null, lastImg: ""
  };

  /* ---------------------------------------------------------- elements */
  var svg = $("#mapSvg"), mapImg = $("#mapImg"), routeLayer = $("#routeLayer"),
      markerLayer = $("#markerLayer"), bandLayer = $("#bandLayer"), mapWrap = $("#mapWrap");

  /* ============================================================
     1.  LOCATION COMBOBOX
     ============================================================ */
  function normalize(s) {
    return String(s || "").toLowerCase().replace(/[_\-\/()]/g, " ").replace(/[^\w\s]/g, "").replace(/\s+/g, " ").trim();
  }
  var LOC_INDEX = LOCS.map(function (l) {
    return { loc: l, texts: [l.name].concat(l.aliases || [], [l.id]).map(normalize) };
  });
  var LOC_BY_ID = {};
  LOCS.forEach(function (l) { LOC_BY_ID[l.id] = l; });

  function scoreLoc(entry, q) {
    var best = 0;
    for (var i = 0; i < entry.texts.length; i++) {
      var t = entry.texts[i];
      if (!t) continue;
      var s = 0;
      if (t === q) s = 100;
      else if (t.indexOf(q) === 0) s = 80;
      else if (t.split(" ").some(function (w) { return w.indexOf(q) === 0; })) s = 65;
      else if (t.indexOf(q) > -1) s = 50;
      if (s > best) best = s;
    }
    return best;
  }
  function searchLocs(query) {
    var q = normalize(query);
    if (!q) return LOCS;
    var out = [];
    LOC_INDEX.forEach(function (e) {
      var s = scoreLoc(e, q);
      if (s) out.push([s, e.loc]);
    });
    out.sort(function (a, b) { return b[0] - a[0] || a[1].name.length - b[1].name.length; });
    return out.slice(0, 40).map(function (x) { return x[1]; });
  }
  function highlight(text, query) {
    var q = query.trim();
    if (!q) return escapeHtml(text);
    var i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return escapeHtml(text);
    return escapeHtml(text.slice(0, i)) + "<mark>" + escapeHtml(text.slice(i, i + q.length)) + "</mark>" + escapeHtml(text.slice(i + q.length));
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }

  function Combo(root, onChange) {
    var input = $(".combo-input", root), list = $(".combo-list", root), clear = $(".combo-clear", root);
    var self = { value: null, input: input };
    var items = [], active = -1;

    function setValue(loc, silent) {
      self.value = loc;
      input.value = loc ? loc.name : "";
      input.classList.remove("invalid");
      if (clear) clear.hidden = !loc && !input.value;
      if (!silent && onChange) onChange(loc);
    }
    self.set = setValue;
    self.raw = function () { return input.value.trim(); };

    function render() {
      var q = input.value;
      items = searchLocs(q);
      list.innerHTML = "";
      active = items.length && q.trim() ? 0 : -1;
      if (!items.length) {
        list.innerHTML = '<li class="combo-empty">No place matches \u201C' + escapeHtml(q) + '\u201D</li>';
        return;
      }
      var lastGroup = null;
      items.forEach(function (loc, i) {
        if (!q.trim() && loc.group !== lastGroup) {
          lastGroup = loc.group;
          var g = document.createElement("li");
          g.className = "combo-group"; g.setAttribute("role", "presentation"); g.textContent = loc.group;
          list.appendChild(g);
        }
        var li = document.createElement("li");
        li.className = "combo-item" + (i === active ? " active" : "");
        li.setAttribute("role", "option"); li.dataset.i = i;
        li.innerHTML = '<span class="ico">' + icon(catIcon(loc), 18) + '</span><span class="txt"><span class="nm">' +
          highlight(loc.name, q) + '</span><span class="gp">' + escapeHtml(loc.group) + '</span></span>';
        li.addEventListener("mousedown", function (e) { e.preventDefault(); choose(i); });
        list.appendChild(li);
      });
    }
    function open() { render(); list.hidden = false; input.setAttribute("aria-expanded", "true"); }
    function close() { list.hidden = true; input.setAttribute("aria-expanded", "false"); }
    function choose(i) { if (items[i]) { setValue(items[i]); close(); } }
    function move(d) {
      if (!items.length) return;
      active = (active + d + items.length) % items.length;
      $$(".combo-item", list).forEach(function (el) {
        var on = Number(el.dataset.i) === active;
        el.classList.toggle("active", on);
        if (on) el.scrollIntoView({ block: "nearest" });
      });
    }

    input.addEventListener("focus", function () { input.select(); open(); });
    input.addEventListener("input", function () {
      self.value = null;
      if (clear) clear.hidden = !input.value;
      input.classList.remove("invalid");
      open();
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); if (list.hidden) open(); else move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") {
        if (!list.hidden && active > -1 && items[active]) { e.preventDefault(); choose(active); }
      } else if (e.key === "Escape") { close(); }
    });
    input.addEventListener("blur", function () {
      setTimeout(close, 120);
      // exact (case-insensitive) typed name -> accept as selection
      if (!self.value && input.value.trim()) {
        var q = normalize(input.value), hit = LOC_INDEX.filter(function (e) { return e.texts.indexOf(q) > -1; })[0];
        if (hit) setValue(hit.loc);
      }
    });
    if (clear) clear.addEventListener("click", function () { setValue(null); input.focus(); });
    return self;
  }

  var fromCombo = Combo($('.combo[data-role="from"]'));
  var toCombo = Combo($('.combo[data-role="to"]'));
  var emCombo = Combo($('.combo[data-role="em"]'));

  /* ============================================================
     2.  FORM + API
     ============================================================ */
  var formError = $("#formError");
  function showError(box, msg) { box.textContent = msg; box.hidden = !msg; }

  function api(path, params) {
    var q = Object.keys(params).filter(function (k) { return params[k] !== "" && params[k] != null; })
      .map(function (k) { return encodeURIComponent(k) + "=" + encodeURIComponent(params[k]); }).join("&");
    return fetch("/api/" + path + "?" + q, { headers: { Accept: "application/json" } }).then(function (r) {
      return r.json().then(function (data) { if (!r.ok || !data.ok) throw new Error(data.error || "Something went wrong."); return data; });
    });
  }
  function valueFor(combo) { return combo.value ? combo.value.id : combo.raw(); }

  function requestRoute(opts) {
    opts = opts || {};
    var f = valueFor(fromCombo), t = valueFor(toCombo);
    $(".combo-input", fromCombo.input.parentNode).classList.toggle("invalid", !f);
    $(".combo-input", toCombo.input.parentNode).classList.toggle("invalid", !t);
    if (!f || !t) { showError(formError, !f ? "Choose where you are starting from." : "Choose where you want to go."); return; }
    showError(formError, "");
    setBusy(true);
    api("route", { from: f, to: t, accessible: $("#accessibleChk").checked ? "1" : "" })
      .then(function (data) { fromCombo.set(LOC_BY_ID[data.from.id] || fromCombo.value, true); toCombo.set(LOC_BY_ID[data.to.id] || toCombo.value, true); startRoute(data, false, opts.step); })
      .catch(function (err) { showError(formError, err.message); })
      .then(function () { setBusy(false); });
  }
  function setBusy(b) {
    var btn = $("#goBtn");
    btn.disabled = b;
    btn.querySelector("span").textContent = b ? "Finding route\u2026" : "Get directions";
  }

  $("#routeForm").addEventListener("submit", function (e) { e.preventDefault(); requestRoute(); });
  $("#swapBtn").addEventListener("click", function () {
    var a = fromCombo.value, b = toCombo.value, ar = fromCombo.raw(), br = toCombo.raw();
    fromCombo.set(b, true); toCombo.set(a, true);
    if (!b) fromCombo.input.value = br;
    if (!a) toCombo.input.value = ar;
    if (state.route && !state.emergency) requestRoute();
  });
  $$("#examples .chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      fromCombo.set(LOC_BY_ID[chip.dataset.from], true);
      toCombo.set(LOC_BY_ID[chip.dataset.to], true);
      requestRoute();
    });
  });
  $("#accessibleChk").addEventListener("change", function () { if (state.route && !state.emergency) requestRoute({ step: state.step }); });
  $("#editBtn").addEventListener("click", function () {
    $("#planner").hidden = false;
    $("#panel").scrollTo({ top: 0, behavior: "smooth" });
    if (window.innerWidth > 920) toCombo.input.focus();
  });

  /* ------------------------------------------------------- emergency */
  var dlg = $("#emergencyDlg"), emError = $("#emError");
  $("#emergencyBtn").addEventListener("click", function () {
    var cur = state.route && !state.emergency ? state.route.steps[state.step] : null;
    if (!emCombo.value && fromCombo.value) emCombo.set(fromCombo.value, true);
    showError(emError, "");
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    setTimeout(function () { emCombo.input.focus(); }, 50);
  });
  $("#emCancel").addEventListener("click", function () { dlg.close ? dlg.close() : dlg.removeAttribute("open"); });
  function emergencyGo(kind) {
    var v = valueFor(emCombo);
    if (!v) { showError(emError, "Tell us where you are first."); return; }
    showError(emError, "");
    api("emergency", { from: v, type: kind }).then(function (data) {
      dlg.close ? dlg.close() : dlg.removeAttribute("open");
      fromCombo.set(LOC_BY_ID[data.from.id] || null, true);
      toCombo.set(LOC_BY_ID[data.to.id] || null, true);
      if (!LOC_BY_ID[data.to.id]) toCombo.input.value = data.to.name;
      startRoute(data, true);
    }).catch(function (err) { showError(emError, err.message); });
  }
  $("#emExit").addEventListener("click", function () { emergencyGo("exit"); });
  $("#emMedical").addEventListener("click", function () { emergencyGo("medical"); });

  /* ============================================================
     3.  ROUTE PRESENTATION  (panel, steps, stats)
     ============================================================ */
  function startRoute(data, emergency, wantStep) {
    state.route = data; state.emergency = !!emergency; state.legShown = -1; state.browsing = false;
    document.body.classList.toggle("emergency", state.emergency);
    $("#emptyHint").hidden = true;
    $("#planner").hidden = true;
    $("#result").hidden = false;
    $("#guide").hidden = false;
    $("#resFrom").textContent = data.from.name;
    $("#resTo").textContent = data.to.name;

    var banner = $("#emergencyBanner");
    banner.hidden = !state.emergency;
    if (state.emergency) {
      $("#emergencyTitle").textContent = data.summary.emergency_kind === "medical" ? "Route to the nearest medical room" : "Route to the nearest exit";
      $("#emergencySub").textContent = "Stay calm and follow the highlighted path. Do not use lifts.";
    }

    buildStats(data.summary);
    buildSteps(data.steps);
    buildTabs();
    var s = Math.min(Math.max(wantStep || 0, 0), data.steps.length - 1);
    goStep(s, { instant: true, first: true });
    $("#panel").scrollTo({ top: 0 });
    if (window.innerWidth <= 920) window.scrollTo({ top: 0, behavior: "smooth" });
    syncUrl();
  }

  function fmtTime(sum) { return sum.time_min + " min"; }
  function buildStats(sum) {
    var el = $("#stats");
    var floors = sum.floors_changed;
    var html = '<div class="stat"><b>' + sum.distance_m + ' m</b><span>Walking distance</span></div>' +
      '<div class="stat"><b>' + fmtTime(sum) + '</b><span>Estimated time</span></div>' +
      '<div class="stat"><b>' + (floors === 0 ? "Same floor" : floors + (floors === 1 ? " floor" : " floors")) + '</b><span>' +
      (sum.vertical ? "By " + sum.vertical : "No stairs needed") + '</span></div>';
    var pills = [];
    sum.buildings.forEach(function (b) { pills.push('<span class="pill">' + icon("building", 14, 2.2) + escapeHtml(b) + '</span>'); });
    if (sum.accessible) pills.push('<span class="pill green">Step-free</span>');
    if (pills.length) html += '<div class="stat wide">' + pills.join("") + '</div>';
    el.innerHTML = html;
  }

  var STEP_ICON = {
    start: "start", arrive: "arrive", head: "head", straight: "straight", turn_left: "turn_left", turn_right: "turn_right", around: "around",
    stairs_up: "stairs_up", stairs_down: "stairs_down", lift_up: "lift_up", lift_down: "lift_down", door_in: "door_in", door_out: "door_out"
  };
  function isVertical(s) { return /^(stairs|lift)_/.test(s.kind); }
  function groupLabel(s) {
    var v = VIEWS[s.view];
    return v.building ? v.building + " \u00b7 " + (s.view.indexOf("floor_") === 0 ? v.short : "Ground floor") : "Outdoors \u00b7 Campus";
  }

  function buildSteps(steps) {
    var ol = $("#steps");
    ol.innerHTML = "";
    var last = null;
    steps.forEach(function (s, i) {
      var g = groupLabel(s);
      if (g !== last) {
        last = g;
        var h = document.createElement("li");
        h.className = "step-group";
        h.innerHTML = icon(s.view === "campus" ? "pin" : "building", 14, 2.4) + "<span>" + escapeHtml(g) + "</span>";
        ol.appendChild(h);
      }
      var li = document.createElement("li");
      li.className = "step" + (isVertical(s) ? " s-vertical" : "");
      li.dataset.i = i; li.tabIndex = 0;
      li.innerHTML = '<span class="s-ico">' + icon(STEP_ICON[s.kind] || "straight", 18, 2.3) + '</span>' +
        '<span class="s-body"><div class="s-title">' + escapeHtml(s.title) + '</div><div class="s-text">' + escapeHtml(s.text) + '</div></span>' +
        (s.distance_m ? '<span class="s-dist">' + s.distance_m + ' m</span>' : "");
      li.addEventListener("click", function () { goStep(i); });
      li.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); goStep(i); } });
      ol.appendChild(li);
    });
  }

  function buildTabs() {
    var tabs = $("#viewTabs");
    tabs.innerHTML = "";
    var order = ["campus", "floor_1", "floor_2", "floor_3", "lab", "admin"];
    var used = {};
    if (state.route) state.route.legs.forEach(function (l) { used[l.view] = true; });
    order.forEach(function (key) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "vtab"; b.dataset.view = key; b.setAttribute("role", "tab");
      b.innerHTML = (used[key] ? '<span class="tick" title="On your route"></span>' : "") + escapeHtml(VIEWS[key].short);
      b.addEventListener("click", function () { browseView(key); });
      tabs.appendChild(b);
    });
    var sec = document.createElement("button");
    sec.type = "button"; sec.className = "vtab"; sec.dataset.view = "section"; sec.setAttribute("role", "tab");
    sec.textContent = "Building section";
    sec.addEventListener("click", function () { browseView("section"); });
    tabs.appendChild(sec);
  }
  buildTabs();

  /* ============================================================
     4.  STEP NAVIGATION
     ============================================================ */
  function goStep(i, opts) {
    opts = opts || {};
    var r = state.route;
    if (!r) return;
    i = Math.max(0, Math.min(i, r.steps.length - 1));
    var prev = r.steps[state.step];
    var s = r.steps[i];
    state.step = i;
    var wasBrowsing = state.browsing;
    state.browsing = false;

    // panel highlight
    $$(".step", $("#steps")).forEach(function (el) {
      var n = Number(el.dataset.i);
      el.classList.toggle("active", n === i);
      el.classList.toggle("done", n < i);
      if (n === i) el.setAttribute("aria-current", "step"); else el.removeAttribute("aria-current");
    });
    var activeEl = $('.step[data-i="' + i + '"]');
    if (activeEl && !opts.first) {
      var p = $("#panel");
      if (window.innerWidth > 920) {
        var top = activeEl.offsetTop;
        if (top < p.scrollTop + 40 || top > p.scrollTop + p.clientHeight - 120) p.scrollTo({ top: Math.max(0, top - 140), behavior: "smooth" });
      }
    }

    // guide card
    var total = r.steps.length;
    $("#guideMeta").textContent = "Step " + (i + 1) + " of " + total + " \u00b7 " + s.floor + (s.building !== "Campus" && window.innerWidth > 920 ? " \u00b7 " + s.building : "");
    $("#guideTitle").textContent = s.title;
    $("#guideDesc").textContent = s.text;
    var gi = $("#guideIcon");
    gi.innerHTML = icon(STEP_ICON[s.kind] || "straight", 28, 2.2);
    gi.classList.toggle("vertical", isVertical(s));
    $("#guideBar").style.width = (total <= 1 ? 100 : Math.round(i / (total - 1) * 100)) + "%";
    $("#prevBtn").disabled = i === 0;
    var nb = $("#nextBtn"), last = i === total - 1;
    nb.disabled = last;
    nb.querySelector("span").textContent = last ? "You have arrived" : (i === 0 ? "Start" : "Next");

    // map
    var leg = r.legs[s.leg];
    var legChanged = state.legShown !== s.leg || wasBrowsing;
    if (legChanged) {
      showView(leg.view, { crossfade: !opts.instant });
      var fitTarget = fitBounds(boundsOf(leg.points));
      if (opts.instant) { setVB(fitTarget); } else { animateVB(fitTarget); }
      state.legShown = s.leg;
      if (prev && prev.leg !== s.leg && !opts.first && !wasBrowsing) announceTransition(r, s);
    }
    drawRoute(true);
    updateTabs();
    updateFloorIndicator(leg.view);
    syncUrl();
  }

  function announceTransition(r, s) {
    var tr = r.transitions[s.leg - 1];
    if (!tr) return;
    var v = VIEWS[r.legs[s.leg].view];
    var name = v.building ? v.building + " \u00b7 " + v.short : "Campus";
    var ic = tr.kind === "stairs" ? (tr.badge && tr.badge.dir === "down" ? "stairs_down" : "stairs_up")
      : tr.kind === "lift" ? (tr.badge && tr.badge.dir === "down" ? "lift_down" : "lift_up")
      : (tr.badge && tr.badge.dir === "in" ? "door_in" : "door_out");
    toast('<span class="ti">' + icon(ic, 16, 2.4) + '</span><span>' + escapeHtml(name) + '</span>');
  }
  var toastTimer = null;
  function toast(html) {
    var t = $("#toast");
    t.innerHTML = html; t.hidden = false;
    t.style.animation = "none"; void t.offsetWidth; t.style.animation = "";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.hidden = true; }, 2600);
  }

  $("#nextBtn").addEventListener("click", function () { goStep(state.step + 1); });
  $("#prevBtn").addEventListener("click", function () { goStep(state.step - 1); });
  document.addEventListener("keydown", function (e) {
    if (!state.route) return;
    var tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA" || (dlg && dlg.open)) return;
    if (e.key === "ArrowRight" || e.key === "ArrowDown" && e.target === document.body) { e.preventDefault(); goStep(state.step + 1); }
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp" && e.target === document.body) { e.preventDefault(); goStep(state.step - 1); }
  });

  /* ============================================================
     5.  MAP ENGINE
     ============================================================ */
  function showView(key, o) {
    o = o || {};
    state.view = key;
    var src = key === "section" ? SECTION.image : VIEWS[key].image;
    if (state.lastImg !== src) {
      state.lastImg = src;
      if (o.crossfade) {
        mapImg.classList.add("fade");
        var pre = new Image();
        pre.onload = function () { if (state.lastImg === src) { mapImg.setAttribute("href", src); mapImg.classList.remove("fade"); } };
        pre.onerror = function () { mapImg.setAttribute("href", src); mapImg.classList.remove("fade"); };
        pre.src = src;
      } else {
        mapImg.setAttribute("href", src);
      }
    }
    updateTabs();
  }

  function browseView(key) {
    if (!state.route && key === "section") { showView("section"); animateVB({ x: 0, y: 0, w: IMG_W, h: IMG_H }); drawRoute(); return; }
    state.browsing = true;
    showView(key, { crossfade: true });
    var b = null;
    if (state.route && key !== "section") {
      var pts = [];
      state.route.legs.forEach(function (l) { if (l.view === key) pts = pts.concat(l.points); });
      if (pts.length) b = boundsOf(pts);
    }
    animateVB(b ? fitBounds(b) : { x: 0, y: 0, w: IMG_W, h: IMG_H });
    drawRoute();
    updateFloorIndicator(key);
  }

  function updateTabs() {
    $$(".vtab").forEach(function (b) { b.classList.toggle("active", b.dataset.view === state.view); b.setAttribute("aria-selected", b.dataset.view === state.view); });
  }

  /* ---- viewBox helpers ---- */
  function boundsOf(pts) {
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    pts.forEach(function (p) { x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]); });
    return { x0: x0, y0: y0, x1: x1, y1: y1 };
  }
  function aspect() { var r = svg.getBoundingClientRect(); return r.width > 0 && r.height > 0 ? r.width / r.height : IMG_W / IMG_H; }
  function clampVB(vb) {
    var a = aspect();
    vb.w = Math.max(260, Math.min(vb.w, IMG_W)); vb.h = vb.w / a;
    if (vb.h > IMG_H) { vb.h = IMG_H; vb.w = vb.h * a; }
    vb.x = Math.max(-300, Math.min(vb.x, IMG_W - vb.w + 300));
    vb.y = Math.max(-300, Math.min(vb.y, IMG_H - vb.h + 420));
    return vb;
  }
  function fitBounds(b) {
    var r = svg.getBoundingClientRect();
    var W = r.width || 800, H = r.height || 600;
    var guide = $("#guide");
    var insetB = guide && !guide.hidden ? guide.offsetHeight + 62 : 30;
    var insetT = 104, insetL = W < 700 ? 84 : 190, insetR = W < 700 ? 64 : 120;
    var availW = Math.max(120, W - insetL - insetR), availH = Math.max(120, H - insetB - insetT);
    var w = Math.max(b.x1 - b.x0, 60), h = Math.max(b.y1 - b.y0, 60);
    var s = Math.min(availW / w, availH / h);
    s = Math.min(s, W / 560);                    // never zoom in past ~560 drawing px
    s = Math.max(s, W / IMG_W);                  // never zoom out past the full drawing
    var vw = W / s, vh = H / s;
    var cx = (b.x0 + b.x1) / 2, cy = (b.y0 + b.y1) / 2;
    return clampVB({ x: cx - (insetL + availW / 2) / s, y: cy - (insetT + availH / 2) / s, w: vw, h: vh });
  }
  function setVB(vb) {
    state.vb = clampVB({ x: vb.x, y: vb.y, w: vb.w, h: vb.h });
    svg.setAttribute("viewBox", state.vb.x + " " + state.vb.y + " " + state.vb.w + " " + state.vb.h);
  }
  function animateVB(target) {
    cancelAnimationFrame(state.vbAnim);
    var from = { x: state.vb.x, y: state.vb.y, w: state.vb.w, h: state.vb.h }, t0 = performance.now(), dur = 650;
    function ease(t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
    function tick(now) {
      var k = Math.min(1, (now - t0) / dur), e = ease(k);
      setVB({ x: from.x + (target.x - from.x) * e, y: from.y + (target.y - from.y) * e, w: from.w + (target.w - from.w) * e, h: from.h + (target.h - from.h) * e });
      if (k < 1) state.vbAnim = requestAnimationFrame(tick); else drawRoute(false, true);
    }
    state.vbAnim = requestAnimationFrame(tick);
  }
  function unit() { return state.vb.w / 1000; }

  /* ---- zoom & pan ---- */
  function screenToSvg(cx, cy) {
    var r = svg.getBoundingClientRect(), s = Math.min(r.width / state.vb.w, r.height / state.vb.h);
    var ox = (r.width - state.vb.w * s) / 2, oy = (r.height - state.vb.h * s) / 2;
    return { x: state.vb.x + (cx - r.left - ox) / s, y: state.vb.y + (cy - r.top - oy) / s, s: s };
  }
  function zoomAt(factor, cx, cy) {
    cancelAnimationFrame(state.vbAnim);
    var p = screenToSvg(cx, cy), nw = state.vb.w * factor;
    nw = Math.max(260, Math.min(IMG_W, nw)); var f = nw / state.vb.w;
    setVB({ x: p.x - (p.x - state.vb.x) * f, y: p.y - (p.y - state.vb.y) * f, w: nw, h: state.vb.h * f });
    scheduleRedraw();
  }
  var redrawT = null;
  function scheduleRedraw() { cancelAnimationFrame(redrawT); redrawT = requestAnimationFrame(function () { drawRoute(false, true); }); }

  svg.addEventListener("wheel", function (e) { e.preventDefault(); zoomAt(e.deltaY > 0 ? 1.18 : 1 / 1.18, e.clientX, e.clientY); }, { passive: false });
  var pointers = {}, dragStart = null, pinchStart = null;
  svg.addEventListener("pointerdown", function (e) {
    svg.setPointerCapture(e.pointerId);
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
    cancelAnimationFrame(state.vbAnim);
    var ids = Object.keys(pointers);
    if (ids.length === 1) { dragStart = { x: e.clientX, y: e.clientY, vb: Object.assign({}, state.vb) }; svg.classList.add("dragging"); }
    else if (ids.length === 2) {
      var a = pointers[ids[0]], b = pointers[ids[1]];
      pinchStart = { d: Math.hypot(a.x - b.x, a.y - b.y), vb: Object.assign({}, state.vb), cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 };
      dragStart = null;
    }
  });
  svg.addEventListener("pointermove", function (e) {
    if (!pointers[e.pointerId]) return;
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
    var ids = Object.keys(pointers);
    if (ids.length === 1 && dragStart) {
      var r = svg.getBoundingClientRect(), s = Math.min(r.width / dragStart.vb.w, r.height / dragStart.vb.h);
      setVB({ x: dragStart.vb.x - (e.clientX - dragStart.x) / s, y: dragStart.vb.y - (e.clientY - dragStart.y) / s, w: dragStart.vb.w, h: dragStart.vb.h });
    } else if (ids.length === 2 && pinchStart) {
      var a = pointers[ids[0]], b = pointers[ids[1]], d = Math.hypot(a.x - b.x, a.y - b.y);
      state.vb = Object.assign({}, pinchStart.vb);
      svg.setAttribute("viewBox", state.vb.x + " " + state.vb.y + " " + state.vb.w + " " + state.vb.h);
      zoomAt(pinchStart.d / d, pinchStart.cx, pinchStart.cy);
    }
  });
  function endPointer(e) {
    delete pointers[e.pointerId];
    if (!Object.keys(pointers).length) { dragStart = null; pinchStart = null; svg.classList.remove("dragging"); scheduleRedraw(); }
    else { dragStart = null; pinchStart = null; }
  }
  svg.addEventListener("pointerup", endPointer);
  svg.addEventListener("pointercancel", endPointer);
  svg.addEventListener("dblclick", function (e) { zoomAt(0.55, e.clientX, e.clientY); });

  $("#zoomIn").addEventListener("click", function () { var r = svg.getBoundingClientRect(); zoomAt(1 / 1.35, r.left + r.width / 2, r.top + r.height / 2); });
  $("#zoomOut").addEventListener("click", function () { var r = svg.getBoundingClientRect(); zoomAt(1.35, r.left + r.width / 2, r.top + r.height / 2); });
  $("#recenter").addEventListener("click", function () {
    if (state.route && !state.browsing) {
      animateVB(fitBounds(boundsOf(state.route.legs[state.route.steps[state.step].leg].points)));
    } else if (state.route && state.view !== "section") {
      browseView(state.view);
    } else animateVB({ x: 0, y: 0, w: IMG_W, h: IMG_H });
  });
  window.addEventListener("resize", function () {
    setVB(state.vb);
    scheduleRedraw();
  });

  /* ---- SVG helpers ---- */
  function el(name, attrs, parent) {
    var n = document.createElementNS(SVGNS, name);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(n);
    return n;
  }
  function ptsStr(pts) { return pts.map(function (p) { return p[0] + "," + p[1]; }).join(" "); }
  function sliceLine(points, a, b) { return points.slice(a, b + 1); }

  function polyline(pts, cls, width, parent, extra) {
    if (pts.length < 2) return null;
    var p = el("polyline", Object.assign({ points: ptsStr(pts), "class": cls, "stroke-width": width }, extra || {}), parent);
    return p;
  }

  function label(parent, x, y, text, cls, u) {
    var fs = 15 * u, padX = 9 * u, h = fs * 1.9, w = text.length * fs * 0.58 + padX * 2;
    var g = el("g", { "class": "m-label " + (cls || ""), transform: "translate(" + x + " " + y + ")" }, parent);
    el("rect", { x: -w / 2, y: -h, width: w, height: h, rx: h / 2 }, g);
    var t = el("text", { x: 0, y: -h / 2 + fs * 0.36, "text-anchor": "middle", "font-size": fs }, g);
    t.textContent = text;
    return g;
  }

  /* ---- main route drawing ---- */
  function drawRoute(animate, noMotion) {
    var r = state.route, u = unit();
    routeLayer.innerHTML = ""; markerLayer.innerHTML = ""; bandLayer.innerHTML = "";
    if (state.anim) { cancelAnimationFrame(state.anim); state.anim = null; }

    if (state.view === "section") { drawSection(r, u); return; }
    if (!r) return;

    var cur = r.steps[state.step], curLeg = cur.leg, now = null;
    var wLine = 5.2 * u, wCase = 9.6 * u;

    r.legs.forEach(function (leg) {
      if (leg.view !== state.view) return;
      var pts = leg.points, a, b;
      if (leg.index < curLeg) { a = pts.length - 1; b = a; }
      else if (leg.index > curLeg) { a = 0; b = 0; }
      else { a = cur.from_idx; b = cur.to_idx; }

      var upcoming = leg.index > curLeg ? pts : sliceLine(pts, b, pts.length - 1);
      var doneP = leg.index < curLeg ? pts : sliceLine(pts, 0, a);
      var nowP = leg.index === curLeg ? sliceLine(pts, a, b) : [];

      // white casing under everything for contrast
      polyline(pts, "r-case", wCase, routeLayer);
      if (upcoming.length > 1) polyline(upcoming, "r-line r-todo", wLine * 0.9, routeLayer, { "stroke-dasharray": (wLine * 0.5) + " " + (wLine * 1.5) });
      if (doneP.length > 1) polyline(doneP, "r-line r-done", wLine, routeLayer);
      if (nowP.length > 1) {
        var path = polyline(nowP, "r-line r-now", wLine * 1.15, routeLayer);
        polyline(nowP, "r-line r-flow", wLine * 0.5, routeLayer, { "stroke-dasharray": (wLine * 0.4) + " " + (wLine * 2.6) });
        now = { path: path, pts: nowP };
      }
    });

    // vertical transition markers (stairs / lifts / doors) that touch this view
    r.transitions.forEach(function (tr) {
      var kindTxt = tr.kind === "stairs" ? "Stairs" : tr.kind === "lift" ? "Lift" : "Door";
      var dir = tr.badge ? tr.badge.dir : "";
      if (tr.from.view === state.view) {
        var txt = tr.kind === "door" || tr.kind === "exit_door" ? (dir === "in" ? "Enter building" : "Exit") :
          kindTxt + (dir === "down" ? " down" : " up") + " \u2192 " + (tr.badge ? tr.badge.to : "");
        transitionMarker(tr.from.x, tr.from.y, tr.kind, txt, u, tr.after_leg < curLeg);
      }
      if (tr.to.view === state.view && tr.kind !== "door" && tr.kind !== "exit_door") {
        transitionMarker(tr.to.x, tr.to.y, tr.kind, "From " + (tr.badge ? tr.badge.from : ""), u, tr.after_leg + 1 < curLeg, true);
      }
    });

    // start & destination
    var first = r.legs[0], last = r.legs[r.legs.length - 1];
    if (first.view === state.view) {
      var sp = first.points[0];
      pin(sp[0], sp[1], "start", u);
      label(markerLayer, sp[0], sp[1] - 16 * u, r.from.name, "light", u);
    }
    if (last.view === state.view) {
      var dp = last.points[last.points.length - 1];
      pin(dp[0], dp[1], "dest", u);
      label(markerLayer, dp[0], dp[1] - 26 * u, r.to.name, state.emergency ? "orange" : "", u);
    }

    // "you are here"
    var curLegObj = r.legs[curLeg];
    if (curLegObj.view === state.view && state.step < r.steps.length - 1) {
      var yp = curLegObj.points[Math.min(cur.to_idx, curLegObj.points.length - 1)];
      var dot = youDot(yp[0], yp[1], u);
      if (animate && !noMotion && now && now.pts.length > 1 && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) animateAlong(now, dot, u);
    }
  }

  function transitionMarker(x, y, kind, text, u, done, arrival) {
    var g = el("g", { transform: "translate(" + x + " " + y + ")" }, markerLayer);
    el("circle", { r: 15 * u, fill: done ? "#8aa0b8" : "#c2410c", stroke: "#fff", "stroke-width": 3 * u }, g);
    var ic = kind === "stairs" ? '<path d="M-6 6h4v-4h4v-4h4" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
      : kind === "lift" ? '<rect x="-5.5" y="-6.5" width="11" height="13" rx="1.5" fill="none" stroke="#fff" stroke-width="2"/><path d="M0 4V-3M-3 0l3-3 3 3" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
      : '<path d="M-5 6V-5h7v11M-7 6h14" fill="none" stroke="#fff" stroke-width="2.1" stroke-linecap="round"/>';
    var inner = el("g", { transform: "scale(" + (u * 1.0) + ")" }, g);
    inner.innerHTML = ic;
    if (text) label(g, 0, -20 * u, text, "orange", u);
  }

  function pin(x, y, type, u) {
    var g = el("g", { transform: "translate(" + x + " " + y + ")" }, markerLayer);
    if (type === "start") {
      el("circle", { r: 13 * u, fill: "#fff", stroke: "#16a34a", "stroke-width": 5 * u }, g);
      el("circle", { r: 4.5 * u, fill: "#16a34a" }, g);
    } else {
      var c = state.emergency ? "#dc2626" : "#e11d48";
      el("circle", { r: 22 * u, fill: "rgba(225,29,72,.18)", stroke: c, "stroke-width": 2.5 * u }, g);
      el("circle", { r: 12 * u, fill: c, stroke: "#fff", "stroke-width": 4 * u }, g);
      el("circle", { r: 4 * u, fill: "#fff" }, g);
    }
  }

  function youDot(x, y, u) {
    var g = el("g", { transform: "translate(" + x + " " + y + ")" }, markerLayer);
    el("circle", { r: 15 * u, fill: "rgba(37,99,235,.35)", "class": "m-pulse" }, g);
    el("circle", { r: 11 * u, fill: "#2563eb", stroke: "#fff", "stroke-width": 4 * u }, g);
    return g;
  }

  function animateAlong(now, dotG, u) {
    var path = now.path, total = path.getTotalLength();
    var dur = Math.min(1500, Math.max(650, total / u * 1.6)), t0 = performance.now();
    var wLine = 5.2 * u * 1.15;
    path.setAttribute("stroke-dasharray", total + " " + total);
    path.setAttribute("stroke-dashoffset", total);
    var start = now.pts[0];
    dotG.setAttribute("transform", "translate(" + start[0] + " " + start[1] + ")");
    function tick(t) {
      var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      path.setAttribute("stroke-dashoffset", total * (1 - e));
      var p = path.getPointAtLength(total * e);
      dotG.setAttribute("transform", "translate(" + p.x + " " + p.y + ")");
      if (k < 1) state.anim = requestAnimationFrame(tick);
      else { path.removeAttribute("stroke-dasharray"); path.removeAttribute("stroke-dashoffset"); state.anim = null; }
    }
    state.anim = requestAnimationFrame(tick);
  }

  /* ---- section drawing (highlights floor bands) ---- */
  function drawSection(r, u) {
    var floorsUsed = {};
    if (r) r.legs.forEach(function (l) { var v = VIEWS[l.view]; if (l.view.indexOf("floor_") === 0) floorsUsed[v.floor] = true; });
    var here = null;
    if (r) { var v = VIEWS[r.legs[r.steps[state.step].leg].view]; if (r.legs[r.steps[state.step].leg].view.indexOf("floor_") === 0) here = v.floor; }
    [1, 2, 3].forEach(function (n) {
      var b = SECTION.bands[n];
      var on = here === n, used = !!floorsUsed[n];
      el("rect", { x: b.x, y: b.y, width: b.w, height: b.h, rx: 8, "class": "band" + (on ? "" : " dim"), "stroke-width": (on ? 5 : 2.5) * u, opacity: used || !r ? 1 : 0.4 }, bandLayer);
      if (used && r) label(bandLayer, b.x + 120, b.y + b.h / 2 + 18 * u, (on ? "You are here \u00b7 " : "On route \u00b7 ") + n + (n === 1 ? "st" : n === 2 ? "nd" : "rd") + " floor", on ? "orange" : "light", u * 1.15);
    });
  }

  /* ---- floor indicator ---- */
  function updateFloorIndicator(view) {
    var box = $("#floorInd");
    if (view === "section") { box.hidden = true; return; }
    var v = VIEWS[view];
    box.hidden = false;
    $("#floorIndTitle").textContent = v.building || "Campus";
    var ul = $("#floorLevels");
    ul.innerHTML = "";
    if (view.indexOf("floor_") === 0) {
      var used = {};
      if (state.route) state.route.legs.forEach(function (l) { if (l.view.indexOf("floor_") === 0) used[VIEWS[l.view].floor] = true; });
      [3, 2, 1].forEach(function (n) {
        var li = document.createElement("li");
        li.className = (used[n] ? "used " : "") + (v.floor === n ? "here" : "");
        li.innerHTML = "<i></i>" + n + (n === 1 ? "st" : n === 2 ? "nd" : "rd") + " floor";
        ul.appendChild(li);
      });
    } else {
      var li = document.createElement("li");
      li.className = "here";
      li.innerHTML = "<i></i>" + (view === "campus" ? "Outdoors" : "Ground floor");
      ul.appendChild(li);
    }
  }

  /* ============================================================
     6.  URL SYNC  (shareable links)
     ============================================================ */
  function syncUrl() {
    if (!window.history || !window.history.replaceState) return;
    var p = new URLSearchParams();
    if (state.route) {
      if (state.emergency) { p.set("emergency", state.route.summary.emergency_kind || "exit"); p.set("from", state.route.from.id); }
      else { p.set("from", state.route.from.id); p.set("to", state.route.to.id); if (state.route.summary.accessible) p.set("accessible", "1"); }
      if (state.step) p.set("step", state.step);
    }
    var q = p.toString();
    window.history.replaceState(null, "", window.location.pathname + (q ? "?" + q : ""));
  }

  /* ============================================================
     7.  BOOT
     ============================================================ */
  function boot() {
    showView("campus");
    setVB({ x: 0, y: 0, w: IMG_W, h: IMG_H });
    updateTabs();

    var q = new URLSearchParams(window.location.search);
    var f = q.get("from"), t = q.get("to"), em = q.get("emergency"), st = Number(q.get("step") || 0);
    if (f && LOC_BY_ID[f]) fromCombo.set(LOC_BY_ID[f], true);
    if (t && LOC_BY_ID[t]) toCombo.set(LOC_BY_ID[t], true);
    if (q.get("accessible") === "1") $("#accessibleChk").checked = true;
    if (em && f) {
      emCombo.set(LOC_BY_ID[f] || null, true);
      api("emergency", { from: f, type: em }).then(function (d) { toCombo.set(LOC_BY_ID[d.to.id] || null, true); startRoute(d, true, st); }).catch(function () {});
    } else if (f && t) {
      requestRoute({ step: st });
    }
  }
  boot();
})();
