from pathlib import Path
import re
import subprocess
import tempfile
from html.parser import HTMLParser

INDEX = Path("index.html")
README = Path("README.md")
CHANGELOG = Path("CHANGELOG.md")
html = INDEX.read_text(encoding="utf-8")
readme = README.read_text(encoding="utf-8")
log = CHANGELOG.read_text(encoding="utf-8")


def rep(text, old, new, label, count=1):
    n = text.count(old)
    if n != count:
        raise SystemExit(f"{label}: expected {count} match(es), found {n}")
    return text.replace(old, new, count)


# ── Release metadata ──────────────────────────────────────────────────────────
html = rep(
    html,
    "Version 1.8.1 · 15 September 2026, 11:21 UTC",
    "Version 1.9.0 · 15 September 2026, 11:31 UTC",
    "header version",
)
html = rep(html, 'const VERSION = "1.8.1";', 'const VERSION = "1.9.0";', "VERSION")
html = rep(
    html,
    'const BUILD = "15 September 2026, 11:21 UTC";',
    'const BUILD = "15 September 2026, 11:31 UTC";',
    "BUILD",
)
release = '''  {
    version: "1.9.0", date: "15 September 2026, 11:31 UTC",
    summary: "Large boards are easier to navigate with a live minimap and a structured outline view of systems, items and expansion relationships.",
    items: [
      "Added a collapsible Board Map beside the zoom controls. It shows system boundaries, item clusters and the current viewport, and supports tap/drag navigation.",
      "The Board Map stays live while panning and zooming, opens by default on desktop, and starts collapsed on narrow/mobile screens to preserve workspace.",
      "Added Board Outline, a structured view grouped by systems with ungrouped items separated out. Expands into relationships become nested hierarchy where possible.",
      "Clicking an outline item jumps back to and selects it on the board; clicking a system fits that system into view. Hidden members of collapsed systems are expanded automatically when targeted."
    ]
  },\n'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# ── Icons ─────────────────────────────────────────────────────────────────────
fit_icon = '  <symbol id="i-fit" viewBox="0 0 24 24"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></symbol>\n'
nav_icons = fit_icon + '''  <symbol id="i-map" viewBox="0 0 24 24"><path d="M4 5l5-2 6 3 5-2v15l-5 2-6-3-5 2z" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linejoin="round"/><path d="M9 3v15M15 6v15" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></symbol>
  <symbol id="i-outline" viewBox="0 0 24 24"><path d="M5 6h3M11 6h8M5 12h3M11 12h8M5 18h3M11 18h8" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/><circle cx="7" cy="6" r="1" fill="currentColor"/><circle cx="7" cy="12" r="1" fill="currentColor"/><circle cx="7" cy="18" r="1" fill="currentColor"/></symbol>
'''
html = rep(html, fit_icon, nav_icons, "navigation icons")

# ── Minimap + outline styling ─────────────────────────────────────────────────
zoom_css_anchor = '#zoomlvl{font-family:var(--type); font-size:11px; color:var(--ui-fg); opacity:.85}\n\n/* ───────────── drawers / sheets ───────────── */'
zoom_css = '''#zoomlvl{font-family:var(--type); font-size:11px; color:var(--ui-fg); opacity:.85}

#minimap{position:absolute; z-index:21; right:68px; bottom:calc(14px + var(--safe-b)); width:196px;
  padding:7px; border:1px solid var(--ui-line); border-radius:5px;
  background:linear-gradient(180deg,var(--ui-1),var(--ui-2)); color:var(--ui-fg);
  box-shadow:0 8px 24px var(--ui-drop), inset 0 1px 0 var(--ui-hi);
  opacity:0; transform:translateY(8px) scale(.98); pointer-events:none;
  transition:opacity .16s, transform .18s, bottom .2s}
#minimap.show{opacity:1; transform:none; pointer-events:auto}
#minimap .minimap-head{height:24px; display:flex; align-items:center; justify-content:space-between; padding:0 2px 5px 5px;
  font:700 9.5px/1 var(--ui); letter-spacing:.12em; text-transform:uppercase; opacity:.9}
#minimap .minimap-close{width:22px; height:22px; display:grid; place-items:center; color:var(--ui-fg); opacity:.7; border-radius:3px}
#minimap .minimap-close:hover{opacity:1; background:var(--ui-hi)}
#minimap canvas{display:block; width:180px; height:112px; border-radius:3px; background:var(--sheet-2); touch-action:none; cursor:crosshair}
body.inspecting #minimap{transform:translateX(calc(-1 * min(300px,84vw)))}
body.tl #minimap{bottom:calc(90px + var(--safe-b))}

/* ───────────── drawers / sheets ───────────── */'''
html = rep(html, zoom_css_anchor, zoom_css, "minimap CSS")

inspect_css = '''#inspect{top:0; bottom:0; right:0; width:min(300px,84vw); transform:translateX(104%);
  border-left:1px solid var(--pan-line); padding-top:var(--safe-t)}
#inspect.show{transform:none}
'''
outline_css = inspect_css + '''#outline{top:0; bottom:0; right:0; width:min(390px,92vw); transform:translateX(104%);
  border-left:1px solid var(--pan-line); padding-top:var(--safe-t)}
#outline.show{transform:none}
#outline .outline-sub{margin-top:3px; color:var(--pan-sub); font:10.5px/1.25 var(--ui)}
#outline-body{padding:10px 10px 20px}
.outline-system{border:1px solid var(--pan-line); border-radius:5px; overflow:hidden; margin-bottom:10px; background:var(--pan-soft)}
.outline-system-head{width:100%; display:flex; align-items:center; justify-content:space-between; gap:10px; text-align:left;
  padding:10px 11px; color:var(--pan-head); border-bottom:1px solid var(--pan-line); background:var(--pan-soft2)}
.outline-system-head:hover{filter:brightness(1.08)}
.outline-system-head b{display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font:700 12px/1.2 var(--type)}
.outline-system-head small{display:block; margin-top:3px; color:var(--pan-sub); font:10.5px/1.2 var(--ui); font-weight:400}
.outline-system-head svg{width:15px; height:15px; flex:none; opacity:.65}
.outline-list{padding:4px 0}
.outline-item{--depth:0; width:100%; display:grid; grid-template-columns:12px minmax(0,1fr) auto; align-items:center; gap:7px;
  padding:7px 9px 7px calc(9px + var(--depth) * 15px); color:var(--pan-fg); text-align:left; border-radius:3px}
.outline-item:hover{background:var(--pan-soft2)}
.outline-node{width:7px; height:7px; border:1px solid var(--pan-sub); border-radius:50%; opacity:.7}
.outline-item[data-depth]:not([data-depth="0"]) .outline-node{border-radius:1px; transform:scale(.78)}
.outline-copy{min-width:0}
.outline-copy b{display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font:600 12px/1.25 var(--ui)}
.outline-copy small{display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-top:2px; color:var(--pan-sub); font:9.5px/1.2 var(--ui); text-transform:uppercase; letter-spacing:.06em}
.outline-state{max-width:74px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding:2px 5px; border:1px solid var(--pan-line); border-radius:999px;
  color:var(--pan-sub); font:9px/1.2 var(--ui)}
.outline-state.done{color:var(--ok); border-color:color-mix(in srgb,var(--ok) 44%,transparent)}
.outline-empty{padding:24px 16px; color:var(--pan-sub); text-align:center; font:12px/1.5 var(--ui)}
'''
html = rep(html, inspect_css, outline_css, "outline panel CSS")

# Keep drawing mode clean, and fit the new navigation UI on narrow screens.
html = rep(
    html,
    'body.penmode #selbar,body.penmode #zoomrail{display:none}',
    'body.penmode #selbar,body.penmode #zoomrail,body.penmode #minimap{display:none}',
    "pen mode minimap visibility",
)
mobile_anchor = '  #zoomrail{right:8px; bottom:calc(64px + var(--safe-b)); flex-direction:column}\n'
mobile_extra = mobile_anchor + '''  #minimap{right:56px; bottom:calc(64px + var(--safe-b)); width:166px; padding:6px}
  #minimap canvas{width:152px; height:96px}
  body.tl #minimap{bottom:calc(126px + var(--safe-b))}
  #outline{top:auto; bottom:0; left:0; right:0; width:auto; height:min(82vh,640px); transform:translateY(104%);
    border-left:0; border-top:1px solid var(--pan-line); border-radius:12px 12px 0 0; padding-top:0}
  #outline.show{transform:none}
'''
html = rep(html, mobile_anchor, mobile_extra, "mobile navigation views CSS")

# ── Navigation UI markup ──────────────────────────────────────────────────────
zoom_html = '''  <div id="zoomrail">
    <button class="chip icon" id="btn-zin" aria-label="Zoom in"><svg><use href="#i-plus"/></svg></button>
    <span id="zoomlvl">100%</span>
    <button class="chip icon" id="btn-zout" aria-label="Zoom out"><svg><use href="#i-minus"/></svg></button>
    <button class="chip icon" id="btn-fit" aria-label="Fit board"><svg><use href="#i-fit"/></svg></button>
  </div>
'''
zoom_html_new = '''  <div id="minimap" aria-label="Board map">
    <div class="minimap-head"><span>Board map</span><button class="minimap-close" id="btn-map-close" aria-label="Collapse board map"><svg width="14" height="14"><use href="#i-x"/></svg></button></div>
    <canvas id="minimap-canvas" aria-label="Board overview; tap or drag to navigate"></canvas>
  </div>

  <div id="zoomrail">
    <button class="chip icon" id="btn-zin" aria-label="Zoom in"><svg><use href="#i-plus"/></svg></button>
    <span id="zoomlvl">100%</span>
    <button class="chip icon" id="btn-zout" aria-label="Zoom out"><svg><use href="#i-minus"/></svg></button>
    <button class="chip icon" id="btn-fit" aria-label="Fit board"><svg><use href="#i-fit"/></svg></button>
    <button class="chip icon" id="btn-map" aria-label="Toggle board map" aria-pressed="false" title="Board map"><svg><use href="#i-map"/></svg></button>
    <button class="chip icon" id="btn-outline" aria-label="Open board outline" title="Board outline"><svg><use href="#i-outline"/></svg></button>
  </div>
'''
html = rep(html, zoom_html, zoom_html_new, "navigation view controls")

inspect_markup = '''<aside class="panel" id="inspect" aria-label="Item settings">
  <header>
    <h2 id="inspect-title">Item</h2>
    <button class="xbtn" data-close="inspect" aria-label="Close"><svg width="18" height="18"><use href="#i-x"/></svg></button>
  </header>
  <div class="body" id="inspect-body"></div>
  <footer id="inspect-foot"></footer>
</aside>
'''
outline_markup = inspect_markup + '''
<aside class="panel" id="outline" aria-label="Board outline">
  <header>
    <div><h2>Board outline</h2><div class="outline-sub" id="outline-summary">Systems and items</div></div>
    <button class="xbtn" data-close="outline" aria-label="Close board outline"><svg width="18" height="18"><use href="#i-x"/></svg></button>
  </header>
  <div class="body" id="outline-body"></div>
</aside>
'''
html = rep(html, inspect_markup, outline_markup, "outline panel markup")

# ── Minimap rendering/navigation ──────────────────────────────────────────────
render_const = 'const world = $("#world"), svg = $("#threads"), viewport = $("#viewport");\n'
render_const_new = render_const + 'let minimapOpen = !matchMedia("(max-width:720px)").matches, minimapMetrics = null, minimapDragging = false;\n'
html = rep(html, render_const, render_const_new, "minimap render state")

apply_anchor = '''  const r = viewport.getBoundingClientRect();
  view.w = Math.round(r.width); view.h = Math.round(r.height);
}
function toWorld(sx, sy) {'''
minimap_js = r'''  const r = viewport.getBoundingClientRect();
  view.w = Math.round(r.width); view.h = Math.round(r.height);
  renderMinimap();
}
function minimapBounds() {
  const rects = [];
  (board.groups || []).forEach(g => {
    const b = typeof groupBounds === "function" ? groupBounds(g) : null;
    if (b) rects.push(b);
  });
  (board.items || []).forEach(it => {
    if (typeof itemHiddenByGroup === "function" && itemHiddenByGroup(it.id)) return;
    rects.push({ x:it.x, y:it.y, w:it.w, h:it.h });
  });
  if (!rects.length) {
    const s = Math.max(.05, view.s || 1);
    return { x:-view.x / s, y:-view.y / s, w:Math.max(320, viewport.clientWidth / s), h:Math.max(220, viewport.clientHeight / s) };
  }
  const x1 = Math.min(...rects.map(b => b.x)), y1 = Math.min(...rects.map(b => b.y));
  const x2 = Math.max(...rects.map(b => b.x + b.w)), y2 = Math.max(...rects.map(b => b.y + b.h));
  const pad = Math.max(60, Math.min(180, Math.max(x2 - x1, y2 - y1) * .08));
  return { x:x1 - pad, y:y1 - pad, w:Math.max(180, x2 - x1 + pad * 2), h:Math.max(120, y2 - y1 + pad * 2) };
}
function setMinimapOpen(on) {
  minimapOpen = !!on;
  const box = $("#minimap"), btn = $("#btn-map");
  if (box) box.classList.toggle("show", minimapOpen);
  if (btn) { btn.classList.toggle("on", minimapOpen); btn.setAttribute("aria-pressed", minimapOpen ? "true" : "false"); }
  if (minimapOpen) requestAnimationFrame(renderMinimap);
}
function renderMinimap() {
  const canvas = $("#minimap-canvas");
  if (!minimapOpen || !canvas || !board) return;
  const r = canvas.getBoundingClientRect();
  if (r.width < 20 || r.height < 20) return;
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const pw = Math.max(1, Math.round(r.width * dpr)), ph = Math.max(1, Math.round(r.height * dpr));
  if (canvas.width !== pw || canvas.height !== ph) { canvas.width = pw; canvas.height = ph; }
  const c = canvas.getContext("2d");
  c.setTransform(dpr,0,0,dpr,0,0); c.clearRect(0,0,r.width,r.height);
  const css = getComputedStyle(document.body);
  const bg = css.getPropertyValue("--sheet-2").trim() || "#241a12";
  const fg = css.getPropertyValue("--pan-fg").trim() || "#eee1c8";
  const line = css.getPropertyValue("--brass").trim() || "#c9a227";
  const hot = css.getPropertyValue("--ink-red").trim() || "#b02a1f";
  c.fillStyle = bg; c.fillRect(0,0,r.width,r.height);
  const b = minimapBounds(), pad = 7;
  const sc = Math.max(.0001, Math.min((r.width - pad * 2) / b.w, (r.height - pad * 2) / b.h));
  const ox = pad + (r.width - pad * 2 - b.w * sc) / 2 - b.x * sc;
  const oy = pad + (r.height - pad * 2 - b.h * sc) / 2 - b.y * sc;
  minimapMetrics = { b, sc, ox, oy };
  c.save(); c.beginPath(); c.rect(0,0,r.width,r.height); c.clip();
  c.globalAlpha = .52; c.strokeStyle = line; c.lineWidth = 1;
  (board.groups || []).forEach(g => {
    const gb = typeof groupBounds === "function" ? groupBounds(g) : null; if (!gb) return;
    c.strokeRect(ox + gb.x * sc, oy + gb.y * sc, Math.max(1, gb.w * sc), Math.max(1, gb.h * sc));
  });
  c.globalAlpha = .62; c.fillStyle = fg;
  (board.items || []).forEach(it => {
    if (typeof itemHiddenByGroup === "function" && itemHiddenByGroup(it.id)) return;
    const x = ox + it.x * sc, y = oy + it.y * sc;
    c.fillRect(x, y, Math.max(2.2, it.w * sc), Math.max(2.2, it.h * sc));
  });
  const s = Math.max(.05, view.s || 1);
  const vx = -view.x / s, vy = -view.y / s, vw = viewport.clientWidth / s, vh = viewport.clientHeight / s;
  c.globalAlpha = .95; c.strokeStyle = hot; c.lineWidth = 1.6;
  c.strokeRect(ox + vx * sc, oy + vy * sc, Math.max(3, vw * sc), Math.max(3, vh * sc));
  c.restore();
}
function navigateFromMinimap(e) {
  if (!minimapMetrics) renderMinimap();
  if (!minimapMetrics) return;
  const canvas = $("#minimap-canvas"), r = canvas.getBoundingClientRect(), m = minimapMetrics;
  const wx = (e.clientX - r.left - m.ox) / m.sc, wy = (e.clientY - r.top - m.oy) / m.sc;
  view.x = viewport.clientWidth / 2 - wx * view.s;
  view.y = viewport.clientHeight / 2 - wy * view.s;
  applyView();
}
function toWorld(sx, sy) {'''
html = rep(html, apply_anchor, minimap_js, "minimap rendering functions")

render_all_anchor = '  drawInk(); drawThreads(); updateEmpty(); renderLegend(); applyFilter();\n'
html = rep(html, render_all_anchor, '  drawInk(); drawThreads(); updateEmpty(); renderLegend(); applyFilter(); renderMinimap();\n', "minimap refresh after render")

# ── Outline panel logic ───────────────────────────────────────────────────────
html = rep(
    html,
    '  if (id === "cases") renderCases();\n',
    '  if (id === "cases") renderCases();\n  if (id === "outline") renderOutline();\n',
    "outline render on open",
)
need_old = '''  const need = $("#cases").classList.contains("show") ||
    ($("#inspect").classList.contains("show") && matchMedia("(max-width:720px)").matches);
'''
need_new = '''  const need = $("#cases").classList.contains("show") || $("#outline").classList.contains("show") ||
    ($("#inspect").classList.contains("show") && matchMedia("(max-width:720px)").matches);
'''
html = rep(html, need_old, need_new, "outline scrim state")
html = rep(
    html,
    'scrim.addEventListener("click", () => { closePanel("cases"); closePanel("inspect"); deselect(); });',
    'scrim.addEventListener("click", () => { closePanel("cases"); closePanel("inspect"); closePanel("outline"); deselect(); });',
    "outline scrim close",
)

inspector_marker = '/* ═══════════════ inspector ═══════════════ */'
outline_js = r'''/* ═══════════════ board outline ═══════════════ */
function outlineItemName(it) {
  const raw = it && (it.title || it.text || TYPE_NAMES[it.type] || "Item");
  return String(raw || "Item").split("\n")[0].trim().slice(0, 70) || TYPE_NAMES[it.type] || "Item";
}
function outlineItemMeta(it) {
  const bits = [TYPE_NAMES[it.type] || it.type || "item"];
  if (it.due) bits.push(it.due);
  if (it.stamp && !it.done) bits.push(it.stamp);
  return bits.join(" · ");
}
function outlineSortIds(ids) {
  return [...ids].sort((a, b) => {
    const A = byId(a), B = byId(b); if (!A || !B) return 0;
    return (A.y - B.y) || (A.x - B.x) || outlineItemName(A).localeCompare(outlineItemName(B));
  });
}
function outlineRows(ids) {
  const allowed = new Set(ids.filter(id => byId(id)));
  const children = new Map([...allowed].map(id => [id, []]));
  const incoming = new Set();
  (board.links || []).forEach(l => {
    const rel = l.rel || (typeof relationKeyFromLabel === "function" ? relationKeyFromLabel(l.label) : "");
    if (rel !== "expands" || l.a === l.b || !allowed.has(l.a) || !allowed.has(l.b)) return;
    children.get(l.a).push(l.b); incoming.add(l.b);
  });
  children.forEach((list, id) => children.set(id, outlineSortIds([...new Set(list)])));
  const seen = new Set();
  const row = (id, depth, path) => {
    if (seen.has(id) || path.has(id)) return "";
    const it = byId(id); if (!it) return "";
    seen.add(id);
    const nextPath = new Set(path); nextPath.add(id);
    const state = it.done ? "Done" : (it.stamp || "");
    let h = `<button class="outline-item" data-outline-item="${esc(id)}" data-depth="${depth}" style="--depth:${Math.min(depth,6)}"><span class="outline-node"></span><span class="outline-copy"><b>${esc(outlineItemName(it))}</b><small>${esc(outlineItemMeta(it))}</small></span>${state ? `<span class="outline-state${it.done ? " done" : ""}">${esc(state)}</span>` : "<span></span>"}</button>`;
    (children.get(id) || []).forEach(child => { h += row(child, depth + 1, nextPath); });
    return h;
  };
  const roots = outlineSortIds([...allowed].filter(id => !incoming.has(id)));
  let h = roots.map(id => row(id, 0, new Set())).join("");
  outlineSortIds([...allowed].filter(id => !seen.has(id))).forEach(id => { h += row(id, 0, new Set()); });
  return h;
}
function outlineGroupMeta(g) {
  const members = (g.itemIds || []).map(byId).filter(Boolean);
  const done = members.filter(it => it.done).length;
  let tasks = 0, tasksDone = 0;
  members.forEach(it => (it.tasks || []).forEach(t => { tasks++; if (t.done) tasksDone++; }));
  const bits = [`${members.length} item${members.length === 1 ? "" : "s"}`, `${done}/${members.length || 0} done`];
  if (tasks) bits.push(`${tasksDone}/${tasks} tasks`);
  if (g.collapsed) bits.push("collapsed");
  return bits.join(" · ");
}
function renderOutline() {
  const body = $("#outline-body"), summary = $("#outline-summary");
  if (!body || !board) return;
  const groups = [...(board.groups || [])].sort((a, b) => {
    const A = typeof expandedGroupBounds === "function" ? expandedGroupBounds(a) : null;
    const B = typeof expandedGroupBounds === "function" ? expandedGroupBounds(b) : null;
    if (!A || !B) return String(a.name || "").localeCompare(String(b.name || ""));
    return (A.y - B.y) || (A.x - B.x);
  });
  const memberIds = new Set(groups.flatMap(g => g.itemIds || []));
  const ungrouped = board.items.filter(it => !memberIds.has(it.id)).map(it => it.id);
  if (summary) summary.textContent = `${groups.length} system${groups.length === 1 ? "" : "s"} · ${board.items.length} item${board.items.length === 1 ? "" : "s"} · ${(board.links || []).length} connection${(board.links || []).length === 1 ? "" : "s"}`;
  let h = "";
  groups.forEach(g => {
    const ids = (g.itemIds || []).filter(id => byId(id));
    h += `<section class="outline-system"><button class="outline-system-head" data-outline-group="${esc(g.id)}"><span><b>${esc(g.name || "System")}</b><small>${esc(outlineGroupMeta(g))}</small></span><svg><use href="#i-fit"/></svg></button><div class="outline-list">${outlineRows(ids)}</div></section>`;
  });
  if (ungrouped.length || !groups.length) {
    const ids = ungrouped.length ? ungrouped : board.items.map(it => it.id);
    h += `<section class="outline-system"><div class="outline-system-head"><span><b>${groups.length ? "Ungrouped" : "Board items"}</b><small>${ids.length} item${ids.length === 1 ? "" : "s"}</small></span><svg><use href="#i-outline"/></svg></div><div class="outline-list">${outlineRows(ids)}</div></section>`;
  }
  body.innerHTML = h || '<div class="outline-empty">Nothing is on this board yet.</div>';
}
function focusOutlineRect(b, maxScale) {
  if (!b) return;
  const r = viewport.getBoundingClientRect(), marginX = Math.min(150, r.width * .22), marginY = Math.min(170, r.height * .24);
  const sx = (r.width - marginX) / Math.max(80, b.w), sy = (r.height - marginY) / Math.max(80, b.h);
  view.s = clamp(Math.min(sx, sy), .18, maxScale || 1.15);
  view.x = r.width / 2 - (b.x + b.w / 2) * view.s;
  view.y = r.height / 2 - (b.y + b.h / 2) * view.s;
  applyView(); save(true);
}
function jumpToOutlineItem(id) {
  const it = byId(id); if (!it) return;
  let expanded = false;
  (board.groups || []).forEach(g => {
    if (g.collapsed && (g.itemIds || []).includes(id)) { g.collapsed = false; expanded = true; }
  });
  if (expanded) renderAll();
  closePanel("outline");
  const r = viewport.getBoundingClientRect();
  view.s = clamp(Math.max(view.s || 1, .55), .25, 1.35);
  view.x = r.width / 2 - (it.x + it.w / 2) * view.s;
  view.y = r.height / 2 - (it.y + it.h / 2) * view.s;
  applyView(); selectItem(id); save(true);
}
$("#outline-body").addEventListener("click", e => {
  const item = e.target.closest("[data-outline-item]");
  if (item) { jumpToOutlineItem(item.dataset.outlineItem); return; }
  const gb = e.target.closest("[data-outline-group]");
  if (!gb) return;
  const g = (board.groups || []).find(x => x.id === gb.dataset.outlineGroup); if (!g) return;
  const b = g.collapsed && typeof groupBounds === "function" ? groupBounds(g) : (typeof expandedGroupBounds === "function" ? expandedGroupBounds(g) : null);
  closePanel("outline"); focusOutlineRect(b, 1.12);
});

'''
html = rep(html, inspector_marker, outline_js + inspector_marker, "outline logic")

# ── Controls and pointer interaction ──────────────────────────────────────────
fit_listener = '$("#btn-fit").addEventListener("click", () => fitBoard(true));\n'
nav_listeners = fit_listener + '''$("#btn-map").addEventListener("click", () => setMinimapOpen(!minimapOpen));
$("#btn-map-close").addEventListener("click", () => setMinimapOpen(false));
$("#btn-outline").addEventListener("click", () => { closePanel("inspect"); openPanel("outline"); });
const minimapCanvas = $("#minimap-canvas");
minimapCanvas.addEventListener("pointerdown", e => {
  if (e.pointerType === "mouse" && e.button !== 0) return;
  e.preventDefault(); minimapDragging = true; minimapCanvas.setPointerCapture(e.pointerId); navigateFromMinimap(e);
});
minimapCanvas.addEventListener("pointermove", e => { if (minimapDragging) { e.preventDefault(); navigateFromMinimap(e); } });
const finishMinimapDrag = e => {
  if (!minimapDragging) return; minimapDragging = false;
  if (minimapCanvas.hasPointerCapture && minimapCanvas.hasPointerCapture(e.pointerId)) minimapCanvas.releasePointerCapture(e.pointerId);
  save(true);
};
minimapCanvas.addEventListener("pointerup", finishMinimapDrag);
minimapCanvas.addEventListener("pointercancel", finishMinimapDrag);
setMinimapOpen(minimapOpen);
'''
html = rep(html, fit_listener, nav_listeners, "navigation view listeners")

# ── README and changelog ──────────────────────────────────────────────────────
readme_anchor = '''Membership, collapse state, manual size, position and lock state are stored with the board, survive import/export and undo/redo, adapt to Corkboard, Whiteboard and Blueprint themes, count toward **Fit board**, and are included when the board is saved as a picture.

## Dates and the timeline'''
readme_new = '''Membership, collapse state, manual size, position and lock state are stored with the board, survive import/export and undo/redo, adapt to Corkboard, Whiteboard and Blueprint themes, count toward **Fit board**, and are included when the board is saved as a picture.

## Board map

The map button beside the zoom controls opens a compact live overview of the whole board. System boundaries and item clusters are drawn at board scale, with a highlighted rectangle showing the part currently on screen. Tap or drag anywhere in the map to move the camera there without changing the board itself.

The map updates while you pan and zoom. It opens by default on desktop, can be collapsed at any time, and starts collapsed on narrow/mobile screens so it does not take over the working area.

## Board outline

The outline button beside the zoom controls opens a structured companion view of the same board data. Systems appear as sections, their member cards and notes appear underneath, and loose items are collected under **Ungrouped**. Where items inside a section use the **Expands into** relationship, the outline nests the child item under its parent so a visual chain can also be read as a hierarchy.

Tap an item in the outline to close the panel, centre the board on it and select it. If that item was hidden inside a collapsed system, Pin It expands the system first. Tap a system heading to fit that whole system into view. The outline never creates a second copy of the project — it is only another way to navigate and read the existing board.

## Dates and the timeline'''
readme = rep(readme, readme_anchor, readme_new, "README navigation views")

changelog_anchor = "---\n\n## 1.8.1 — 15 September 2026, 11:21 UTC"
changelog_entry = '''---

## 1.9.0 — 15 September 2026, 11:31 UTC

- Added a collapsible **Board Map** beside the zoom controls, showing system boundaries, item clusters and the live viewport.
- The map can be tapped or dragged to navigate large boards, updates continuously while panning/zooming, opens by default on desktop and starts collapsed on narrow/mobile screens.
- Added **Board Outline**, grouping items by system and collecting loose items under Ungrouped.
- **Expands into** relationships inside a system are represented as nested parent/child rows in the outline, with cycle-safe fallbacks for more complex graphs.
- Outline items jump to and select their corresponding board item; hidden items automatically expand their collapsed system first. System headings fit that system into view.
- Added responsive styling and dedicated map/outline icons without changing existing board data or export formats.

## 1.8.1 — 15 September 2026, 11:21 UTC'''
log = rep(log, changelog_anchor, changelog_entry, "changelog entry")

INDEX.write_text(html, encoding="utf-8")
README.write_text(readme, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# ── Verification pass 1: JavaScript parses ───────────────────────────────────
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# ── Verification pass 2: DOM + behavioural contracts ─────────────────────────
class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id" and v: self.ids.append(v)

collector = IdCollector(); collector.feed(html)
required_ids = ["minimap", "minimap-canvas", "btn-map", "btn-map-close", "btn-outline", "outline", "outline-summary", "outline-body"]
checks = {
    "version": 'const VERSION = "1.9.0";' in html,
    "build": 'const BUILD = "15 September 2026, 11:31 UTC";' in html,
    "release": 'version: "1.9.0", date: "15 September 2026, 11:31 UTC"' in html,
    "changelog": "## 1.9.0 — 15 September 2026, 11:31 UTC" in log,
    "readme-map": "## Board map" in readme,
    "readme-outline": "## Board outline" in readme,
    "unique-new-ids": all(collector.ids.count(x) == 1 for x in required_ids),
    "minimap-live-view": "const vx = -view.x / s" in html and "renderMinimap();" in html,
    "minimap-navigation": 'navigateFromMinimap(e)' in html and 'setPointerCapture(e.pointerId)' in html,
    "outline-open-render": 'if (id === "outline") renderOutline();' in html,
    "outline-expansion-tree": 'rel !== "expands"' in html and 'children.get(l.a).push(l.b)' in html,
    "outline-cycle-guard": 'seen.has(id) || path.has(id)' in html,
    "outline-jump": 'jumpToOutlineItem' in html and 'selectItem(id); save(true);' in html,
    "collapsed-auto-expand": 'g.collapsed && (g.itemIds || []).includes(id)' in html,
    "mobile-map-default": 'let minimapOpen = !matchMedia("(max-width:720px)").matches' in html,
    "mobile-outline-sheet": '#outline{top:auto; bottom:0; left:0; right:0; width:auto; height:min(82vh,640px)' in html,
    "scrim-outline": '$("#outline").classList.contains("show")' in html,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("second-pass checks failed: " + ", ".join(failed))

print(f"Pin It 1.9.0 verified: {len(scripts)} inline scripts parse; {len(required_ids)} new IDs are unique; {len(checks)} behavioural checks passed")
