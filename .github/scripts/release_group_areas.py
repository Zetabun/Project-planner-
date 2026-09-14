from pathlib import Path
import re
import subprocess
import tempfile

INDEX = Path("index.html")
README = Path("README.md")
CHANGELOG = Path("CHANGELOG.md")
html = INDEX.read_text(encoding="utf-8")
readme = README.read_text(encoding="utf-8")
log = CHANGELOG.read_text(encoding="utf-8")


def rep(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, found {n}")
    return text.replace(old, new, 1)


# Release metadata.
html = rep(html, "Version 1.5.1 · 14 September 2026, 22:45 UTC", "Version 1.6.0 · 14 September 2026, 23:15 UTC", "header version")
html = rep(html, 'const VERSION = "1.5.1";', 'const VERSION = "1.6.0";', "VERSION")
html = rep(html, 'const BUILD = "14 September 2026, 22:45 UTC";', 'const BUILD = "14 September 2026, 23:15 UTC";', "BUILD")
release = '''  {
    version: "1.6.0", date: "14 September 2026, 23:15 UTC",
    summary: "Named group areas make related clusters read as systems while keeping every card and note independently editable.",
    items: [
      "Lasso-select two or more items and use Group area to wrap them in a faint labelled boundary.",
      "Group areas automatically grow, shrink and move with their member items instead of becoming another rigid container.",
      "Tap a group label to select its contents, rename the area or remove only the boundary while keeping the items.",
      "Added distinct Corkboard, Whiteboard and Blueprint group styling, plus group regions in fit-to-board and picture export.",
      "Group membership persists through save, import/export and undo/redo, with automatic cleanup when grouped items are removed."
    ]
  },
'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# Theme-aware faint group/system regions behind cards and links.
html = rep(html,
'''#threads{position:absolute; top:0; left:0; overflow:visible; pointer-events:none; z-index:1}
#threads path{pointer-events:stroke; cursor:pointer}
''',
'''#threads{position:absolute; top:0; left:0; overflow:visible; pointer-events:none; z-index:1}
#threads path{pointer-events:stroke; cursor:pointer}
.group-box{position:absolute; z-index:0; pointer-events:none; border:2px dashed rgba(86,49,23,.34); border-radius:18px;
  background:rgba(255,244,213,.055); box-shadow:inset 0 0 30px rgba(73,42,18,.035)}
.group-label{position:absolute; left:14px; top:10px; max-width:calc(100% - 28px); min-height:25px; padding:5px 10px 4px;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; pointer-events:auto; cursor:pointer;
  font:700 12px/1.2 var(--type); letter-spacing:.07em; text-transform:uppercase; color:#5c3921;
  background:rgba(240,224,188,.9); border:1px solid rgba(92,57,33,.2); border-radius:2px;
  box-shadow:0 3px 8px rgba(54,30,12,.12); transform:rotate(-.45deg)}
body[data-theme="white"] .group-box{border-color:rgba(58,146,201,.46); background:rgba(89,171,219,.035);
  box-shadow:inset 0 0 34px rgba(72,151,198,.025)}
body[data-theme="white"] .group-label{font-family:var(--hand-bold); font-size:14px; font-weight:400; letter-spacing:.015em; text-transform:none;
  color:#315f7f; background:rgba(231,244,252,.94); border-color:rgba(58,146,201,.24); box-shadow:0 3px 8px rgba(54,96,124,.08)}
body[data-theme="blueprint"] .group-box{border-color:rgba(141,216,255,.48); background:rgba(141,216,255,.024);
  box-shadow:inset 0 0 34px rgba(141,216,255,.02)}
body[data-theme="blueprint"] .group-label{font-family:var(--bp-mono); font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  color:#cfeeff; background:#173f5d; border-color:rgba(141,216,255,.42); box-shadow:0 3px 8px rgba(5,16,25,.24)}
''', "group styles")

# Multi-selection gets a Group area action without crowding single-item actions.
html = rep(html,
'''#selbar.multi [data-s="edit"],#selbar.multi [data-s="link"],#selbar.multi [data-s="style"]{display:none}
#selbar [data-s="tags"],#selbar [data-s="done"]{color:var(--ui-fg)}
''',
'''#selbar.multi [data-s="edit"],#selbar.multi [data-s="link"],#selbar.multi [data-s="style"]{display:none}
#selbar [data-s="group"]{display:none}
#selbar.multi [data-s="group"]{display:grid}
#selbar [data-s="tags"],#selbar [data-s="done"]{color:var(--ui-fg)}
''', "group selection css")
html = rep(html,
'''  <symbol id="i-lasso" viewBox="0 0 24 24"><rect x="3.5" y="4.5" width="17" height="15" rx="2" stroke="currentColor" stroke-width="1.7" fill="none" stroke-dasharray="3.5 3"/><circle cx="20.5" cy="19.5" r="2.2" fill="currentColor"/></symbol>
''',
'''  <symbol id="i-lasso" viewBox="0 0 24 24"><rect x="3.5" y="4.5" width="17" height="15" rx="2" stroke="currentColor" stroke-width="1.7" fill="none" stroke-dasharray="3.5 3"/><circle cx="20.5" cy="19.5" r="2.2" fill="currentColor"/></symbol>
  <symbol id="i-group" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3" stroke="currentColor" stroke-width="1.7" fill="none" stroke-dasharray="3 2.8"/><path d="M6.5 8h9M6.5 11h6" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/></symbol>
''', "group icon")
html = rep(html,
'''    <button data-s="tags" aria-label="Tags"><svg><use href="#i-tags"/></svg></button>
    <button data-s="style" aria-label="Style and stamp"><svg><use href="#i-pin"/></svg></button>
''',
'''    <button data-s="tags" aria-label="Tags"><svg><use href="#i-tags"/></svg></button>
    <button data-s="group" aria-label="Create group area" title="Create group area"><svg><use href="#i-group"/></svg></button>
    <button data-s="style" aria-label="Style and stamp"><svg><use href="#i-pin"/></svg></button>
''', "group selection button")
html = rep(html,
'''        <li><svg><use href="#i-tags"/></svg><div><b>Tags = areas of the project</b>Use them for Engine, Sound, Environment or whatever systems an idea touches.</div></li>
''',
'''        <li><svg><use href="#i-tags"/></svg><div><b>Tags = areas of the project</b>Use them for Engine, Sound, Environment or whatever systems an idea touches.</div></li>
        <li><svg><use href="#i-group"/></svg><div><b>Group area = a system boundary</b>Lasso related items and wrap them in a faint labelled area. The boundary follows the cluster as it grows.</div></li>
''', "onboarding group tip")

# Data model and migration.
html = rep(html,
'''    items: [], links: [], ink: [], tags: [], inbox: [], view: { x: 0, y: 0, s: 1 }
''',
'''    items: [], links: [], ink: [], tags: [], inbox: [], groups: [], view: { x: 0, y: 0, s: 1 }
''', "new board groups")
html = rep(html,
'''  if (!Array.isArray(b.inbox)) b.inbox = [];
  b.tags = b.tags.filter(t => t && t.id).slice(0, MAXTAGS);
''',
'''  if (!Array.isArray(b.inbox)) b.inbox = [];
  if (!Array.isArray(b.groups)) b.groups = [];
  b.tags = b.tags.filter(t => t && t.id).slice(0, MAXTAGS);
''', "normalise groups array")
html = rep(html,
'''  const ids = new Set(b.items.map(i => i.id));
  b.links = b.links.filter(l => l && ids.has(l.a) && ids.has(l.b));   // drop strings to nothing
''',
'''  const ids = new Set(b.items.map(i => i.id));
  b.groups = b.groups.filter(g => g && g.id).map(g => {
    const itemIds = [...new Set(Array.isArray(g.itemIds) ? g.itemIds : [])].filter(id => ids.has(id));
    return { id: g.id, name: String(g.name || "Group").slice(0, 48), itemIds, pad: clamp(+g.pad || 42, 28, 120) };
  }).filter(g => g.itemIds.length >= 2);
  b.links = b.links.filter(l => l && ids.has(l.a) && ids.has(l.b));   // drop strings to nothing
''', "normalise group membership")

# Undo / redo must include group membership.
html = rep(html,
'''  history.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox }));
''',
'''  history.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox, groups: board.groups }));
''', "snap groups")
html = rep(html,
'''  const d = JSON.parse(s); board.items = d.items; board.links = d.links; board.ink = d.ink || []; board.inbox = d.inbox || [];
''',
'''  const d = JSON.parse(s); board.items = d.items; board.links = d.links; board.ink = d.ink || []; board.inbox = d.inbox || []; board.groups = d.groups || [];
''', "apply snap groups")
html = rep(html,
'''  future.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox }));
''',
'''  future.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox, groups: board.groups }));
''', "undo future groups")
html = rep(html,
'''  history.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox }));
  applySnap(future.pop()); updateUndo();
''',
'''  history.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox, groups: board.groups }));
  applySnap(future.pop()); updateUndo();
''', "redo history groups")

# First-run example demonstrates the new visual hierarchy.
html = rep(html,
'''  const b = { theme: "cork", id: uid(), name: "The Greenhouse Job", no: "NO. 001", created: Date.now(), updated: Date.now(), items: [], links: [], ink: [], tags: [], inbox: [], view: { x: 0, y: 0, s: 1 } };
''',
'''  const b = { theme: "cork", id: uid(), name: "The Greenhouse Job", no: "NO. 001", created: Date.now(), updated: Date.now(), items: [], links: [], ink: [], tags: [], inbox: [], groups: [], view: { x: 0, y: 0, s: 1 } };
''', "seed groups array")
html = rep(html,
'''  b.inbox.push({ id: uid(), text: "Could this feature react differently at night?", kind: "sticky", created: Date.now() });
''',
'''  b.groups.push({ id: uid(), name: "FEATURE SYSTEM", itemIds: [brief.id, string.id, plan.id], pad: 42 });
  b.inbox.push({ id: uid(), text: "Could this feature react differently at night?", kind: "sticky", created: Date.now() });
''', "sample group")

# Group geometry, rendering, lifecycle and menu.
group_js = r'''function groupBounds(g) {
  const members = (g.itemIds || []).map(byId).filter(Boolean);
  if (members.length < 2) return null;
  const pad = clamp(+g.pad || 42, 28, 120);
  const x1 = Math.min(...members.map(i => i.x)) - pad;
  const y1 = Math.min(...members.map(i => i.y)) - pad;
  const x2 = Math.max(...members.map(i => i.x + i.w)) + pad;
  const y2 = Math.max(...members.map(i => i.y + i.h)) + pad;
  return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
}
function renderGroups() {
  $$(".group-box").forEach(n => n.remove());
  (board.groups || []).forEach(g => {
    const b = groupBounds(g); if (!b) return;
    const n = document.createElement("div");
    n.className = "group-box"; n.dataset.group = g.id;
    n.style.left = b.x + "px"; n.style.top = b.y + "px";
    n.style.width = b.w + "px"; n.style.height = b.h + "px";
    n.innerHTML = `<button type="button" class="group-label" data-group-label="${g.id}" title="Group area">${esc(g.name || "Group")}</button>`;
    const label = n.querySelector(".group-label");
    label.addEventListener("pointerdown", e => {
      e.preventDefault(); e.stopPropagation();
      groupMenu(g.id, e.clientX, e.clientY);
    });
    world.appendChild(n);
  });
}
function pruneGroups() {
  const ids = new Set(board.items.map(i => i.id));
  board.groups = (board.groups || []).map(g => ({ ...g, itemIds: (g.itemIds || []).filter(id => ids.has(id)) }))
    .filter(g => g.itemIds.length >= 2);
}
function createGroupArea(ids) {
  const clean = [...new Set(ids)].filter(id => byId(id));
  if (clean.length < 2) { toast("Select at least two items first"); return; }
  const same = (board.groups || []).find(g => {
    const a = [...(g.itemIds || [])].sort(), b = [...clean].sort();
    return a.length === b.length && a.every((id, i) => id === b[i]);
  });
  if (same) { toast("Those items already have a group area"); return; }
  const v = prompt("Name this group area", "SYSTEM");
  if (v === null) return;
  snap();
  board.groups = board.groups || [];
  board.groups.push({ id: uid(), name: (v.trim() || "Group").slice(0, 48), itemIds: clean, pad: 42 });
  renderGroups(); save();
  toast("Group area added");
}
function groupMenu(id, x, y) {
  const g = (board.groups || []).find(k => k.id === id); if (!g) return;
  showCtx(`<div class="ctx-rel-head"><b>${esc(g.name || "Group")}</b><span>${g.itemIds.length} items in this area.</span></div>
    <button data-a="select"><svg><use href="#i-lasso"/></svg>Select contents</button>
    <button data-a="rename"><svg><use href="#i-card"/></svg>Rename group area</button>
    <hr><button data-a="del" class="danger"><svg><use href="#i-trash"/></svg>Remove group area</button>`, x, y);
  ctx.onclick = e => {
    const b = e.target.closest("button"); if (!b) return;
    hideCtx();
    if (b.dataset.a === "select") { setMulti((g.itemIds || []).filter(id => byId(id))); return; }
    if (b.dataset.a === "rename") {
      const v = prompt("Rename group area", g.name || "Group");
      if (v !== null && v.trim()) { snap(); g.name = v.trim().slice(0, 48); renderGroups(); save(); }
      return;
    }
    if (b.dataset.a === "del") {
      snap(); board.groups = (board.groups || []).filter(k => k.id !== id); renderGroups(); save();
      toast("Group area removed — items kept");
    }
  };
}
'''
html = rep(html, "function renderAll() {\n", group_js + "\nfunction renderAll() {\n", "group rendering functions")
html = rep(html,
'''  els.clear();
  board.items.slice().sort((a, b) => (a.z || 0) - (b.z || 0)).forEach(it => { makeEl(it); refresh(it.id); });
''',
'''  els.clear();
  renderGroups();
  board.items.slice().sort((a, b) => (a.z || 0) - (b.z || 0)).forEach(it => { makeEl(it); refresh(it.id); });
''', "render groups in renderAll")
html = rep(html,
'''const redraw = () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; drawThreads(); }); };
''',
'''const redraw = () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; renderGroups(); drawThreads(); }); };
''', "live group redraw")

# Selection action creates a boundary from the current lasso set.
html = rep(html,
'''  if (a === "tags") {
    const r = b.getBoundingClientRect();
    tagPicker(multi.size > 1 ? [...multi] : [sel], r.left, r.top - 8);
    return;
  }
  if (multi.size > 1) {
''',
'''  if (a === "tags") {
    const r = b.getBoundingClientRect();
    tagPicker(multi.size > 1 ? [...multi] : [sel], r.left, r.top - 8);
    return;
  }
  if (a === "group") { if (multi.size > 1) createGroupArea([...multi]); return; }
  if (multi.size > 1) {
''', "group selection handler")

# Item removal cleans up group membership immediately.
html = rep(html,
'''  board.items = board.items.filter(i => !kill.has(i.id));
  board.links = board.links.filter(l => !kill.has(l.a) && !kill.has(l.b));
''',
'''  board.items = board.items.filter(i => !kill.has(i.id));
  board.links = board.links.filter(l => !kill.has(l.a) && !kill.has(l.b));
  pruneGroups(); renderGroups();
''', "removeMany group cleanup")
html = rep(html,
'''  board.items = board.items.filter(i => i.id !== id);
  board.links = board.links.filter(l => l.a !== id && l.b !== id);
  const el = els.get(id); if (el) el.remove(); els.delete(id);
''',
'''  board.items = board.items.filter(i => i.id !== id);
  board.links = board.links.filter(l => l.a !== id && l.b !== id);
  pruneGroups(); renderGroups();
  const el = els.get(id); if (el) el.remove(); els.delete(id);
''', "removeItem group cleanup")
html = rep(html,
'''  board.items = board.items.filter(i => i.id !== id);
  board.links = board.links.filter(l => l.a !== id && l.b !== id);
  const el = els.get(id); if (el) el.remove(); els.delete(id);
  if (sel === id) deselect();
''',
'''  board.items = board.items.filter(i => i.id !== id);
  board.links = board.links.filter(l => l.a !== id && l.b !== id);
  pruneGroups(); renderGroups();
  const el = els.get(id); if (el) el.remove(); els.delete(id);
  if (sel === id) deselect();
''', "inbox group cleanup")

# Fit-to-board includes the faint boundary, not only the cards inside it.
html = rep(html,
'''  board.items.forEach(i => {
    x1 = Math.min(x1, i.x); y1 = Math.min(y1, i.y);
    x2 = Math.max(x2, i.x + i.w); y2 = Math.max(y2, i.y + i.h);
  });
  (board.ink || []).forEach(s => {
''',
'''  board.items.forEach(i => {
    x1 = Math.min(x1, i.x); y1 = Math.min(y1, i.y);
    x2 = Math.max(x2, i.x + i.w); y2 = Math.max(y2, i.y + i.h);
  });
  (board.groups || []).forEach(g => {
    const b = groupBounds(g); if (!b) return;
    x1 = Math.min(x1, b.x); y1 = Math.min(y1, b.y);
    x2 = Math.max(x2, b.x + b.w); y2 = Math.max(y2, b.y + b.h);
  });
  (board.ink || []).forEach(s => {
''', "group extents")

# Picture export draws the group area behind links and cards.
export_groups = r'''  /* faint group/system areas */
  (board.groups || []).forEach(gp => {
    const b = groupBounds(gp); if (!b) return;
    c.save();
    c.lineWidth = 2; c.setLineDash([8, 6]);
    if (blueprint) { c.strokeStyle = "rgba(141,216,255,.52)"; c.fillStyle = "rgba(141,216,255,.025)"; }
    else if (W_) { c.strokeStyle = "rgba(58,146,201,.46)"; c.fillStyle = "rgba(89,171,219,.035)"; }
    else { c.strokeStyle = "rgba(86,49,23,.36)"; c.fillStyle = "rgba(255,244,213,.055)"; }
    rrect(c, b.x, b.y, b.w, b.h, 18); c.fill(); c.stroke(); c.setLineDash([]);
    const label = String(gp.name || "Group");
    c.font = blueprint ? '700 11px Consolas, monospace' : W_ ? 'bold 14px "Kalam", cursive' : '700 12px "Special Elite", monospace';
    const lw = Math.min(Math.max(72, c.measureText(label).width + 20), Math.max(72, b.w - 28));
    const lx = b.x + 14, ly = b.y + 10;
    c.fillStyle = blueprint ? "#173f5d" : W_ ? "rgba(231,244,252,.94)" : "rgba(240,224,188,.92)";
    c.strokeStyle = blueprint ? "rgba(141,216,255,.42)" : W_ ? "rgba(58,146,201,.24)" : "rgba(92,57,33,.2)";
    c.lineWidth = 1; c.fillRect(lx, ly, lw, 25); c.strokeRect(lx, ly, lw, 25);
    c.fillStyle = blueprint ? "#cfeeff" : W_ ? "#315f7f" : "#5c3921";
    c.textAlign = "left"; c.textBaseline = "middle"; c.fillText(label, lx + 10, ly + 12.5, lw - 20);
    c.restore();
  });

'''
html = rep(html, "  /* string, or marker lines */\n", export_groups + "  /* string, or marker lines */\n", "group picture export")

# README guidance.
readme = rep(readme,
'''With several selected you can drag the whole cluster as one, duplicate it, or remove it. Tap the background to drop the selection.

## Dates and the timeline
''',
'''With several selected you can drag the whole cluster as one, duplicate it, or remove it. Tap the background to drop the selection.

## Group areas

When a cluster represents one system or subtopic, lasso two or more items and tap **Group area** on the selection bar. Give it a name such as **RAIN SYSTEM** and Pin It draws a faint labelled boundary behind those items.

The area is deliberately not another rigid container: every note and card remains individually draggable, resizable and linkable. The boundary recalculates from its members, so it grows, shrinks and moves as the cluster changes. Tap the group label to select all of its contents, rename it, or remove only the boundary while leaving the work untouched.

Group areas are stored with the board, survive import/export and undo/redo, adapt to Corkboard, Whiteboard and Blueprint themes, count toward **Fit board**, and are included when the board is saved as a picture.

## Dates and the timeline
''', "README group areas")

# Changelog entry.
entry = '''## 1.6.0 — 14 September 2026, 23:15 UTC

- Added **Group areas**: lasso two or more items and wrap them in a faint named system/subtopic boundary.
- Group boundaries automatically follow their member items as cards move or resize, while the items remain independently editable.
- Tapping a group label lets you select its contents, rename the group or remove just the boundary.
- Added theme-specific Corkboard, Whiteboard and Blueprint treatments, plus group support in Fit board and picture export.
- Group membership now persists through save/import/export and undo/redo, and automatically cleans itself up when grouped items are removed.
- Updated onboarding and the worked example to demonstrate system boundaries.

'''
log = rep(log, "---\n\n", "---\n\n" + entry, "changelog insertion")

INDEX.write_text(html, encoding="utf-8")
README.write_text(readme, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# First verification pass: release metadata, feature wiring and JS syntax.
required = [
    'const VERSION = "1.6.0";',
    'const BUILD = "14 September 2026, 23:15 UTC";',
    'class="group-box"',
    'function groupBounds(g)',
    'function createGroupArea(ids)',
    'data-s="group"',
    'groups: []',
    'groups: board.groups',
    'faint group/system areas',
    'version: "1.6.0"',
]
for token in required:
    if token not in html:
        raise SystemExit("verification failed: missing " + token)
if "## 1.6.0 — 14 September 2026, 23:15 UTC" not in log:
    raise SystemExit("verification failed: changelog entry missing")
if "## Group areas" not in readme:
    raise SystemExit("verification failed: README section missing")

scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)
print(f"Pin It 1.6.0 first pass verified: {len(scripts)} inline scripts parse successfully")
