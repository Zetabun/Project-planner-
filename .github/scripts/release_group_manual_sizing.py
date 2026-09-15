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
        raise SystemExit(f"{label}: expected exactly one match, found {n}")
    return text.replace(old, new, 1)


def sub1(text, pattern, repl, label, flags=0):
    out, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, found {n}")
    return out


# Release metadata.
html = rep(html, "Version 1.6.1 · 14 September 2026, 23:38 UTC", "Version 1.7.0 · 15 September 2026, 10:07 UTC", "header version")
html = rep(html, 'const VERSION = "1.6.1";', 'const VERSION = "1.7.0";', "VERSION")
html = rep(html, 'const BUILD = "14 September 2026, 23:38 UTC";', 'const BUILD = "15 September 2026, 10:07 UTC";', "BUILD")
release = '''  {
    version: "1.7.0", date: "15 September 2026, 10:07 UTC",
    summary: "System/group boundaries can now switch between automatic and manual sizing, with direct resize/move controls and an optional lock.",
    items: [
      "Tap a system/group name to switch its boundary between Automatic sizing and Manual sizing.",
      "Manual boundaries can be moved directly and resized from four touch-friendly corner handles without moving the cards inside them.",
      "Manual boundaries can be locked after positioning to prevent accidental resizing or movement, then unlocked from the same menu.",
      "Automatic mode remains the default and continues to grow, shrink and move with the group's member items.",
      "Manual size, position and lock state persist through save, backup/import, picture export and undo/redo."
    ]
  },\n'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# Editing affordances for manual group boundaries.
css_anchor = '''body[data-theme="blueprint"] .group-label{font-family:var(--bp-mono); font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  color:#cfeeff; background:#173f5d; border-color:rgba(141,216,255,.42); box-shadow:0 3px 8px rgba(5,16,25,.24)}
'''
css_extra = css_anchor + '''.group-box.manual{border-style:solid}
.group-box.group-editing{z-index:9999; pointer-events:auto; cursor:move; outline:1px solid rgba(201,162,39,.5); outline-offset:4px}
.group-box.group-locked .group-label{padding-right:28px}
.group-box.group-locked .group-label::after{content:""; position:absolute; right:8px; top:50%; width:8px; height:7px; transform:translateY(-20%);
  border:1.5px solid currentColor; border-radius:1px; opacity:.72}
.group-box.group-locked .group-label::before{content:""; position:absolute; right:9.5px; top:5px; width:5px; height:6px;
  border:1.5px solid currentColor; border-bottom:0; border-radius:5px 5px 0 0; opacity:.72}
.group-resize-handle{position:absolute; width:32px; height:32px; padding:0; pointer-events:auto; touch-action:none; background:transparent; z-index:4}
.group-resize-handle::after{content:""; position:absolute; inset:9px; border-radius:50%; background:var(--ui-1); border:2px solid var(--brass);
  box-shadow:0 2px 7px rgba(0,0,0,.32)}
.group-resize-handle.nw{left:-16px; top:-16px; cursor:nwse-resize}
.group-resize-handle.ne{right:-16px; top:-16px; cursor:nesw-resize}
.group-resize-handle.sw{left:-16px; bottom:-16px; cursor:nesw-resize}
.group-resize-handle.se{right:-16px; bottom:-16px; cursor:nwse-resize}
body[data-theme="white"] .group-box.group-editing{outline-color:rgba(58,146,201,.48)}
body[data-theme="white"] .group-resize-handle::after{border-color:#3a92c9; background:#f7fbfd}
body[data-theme="blueprint"] .group-box.group-editing{outline-color:rgba(141,216,255,.5)}
body[data-theme="blueprint"] .group-resize-handle::after{border-color:#8dd8ff; background:#173f5d}
'''
html = rep(html, css_anchor, css_extra, "manual group CSS")

# Menu icons.
icon_anchor = '''  <symbol id="i-group" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="3" stroke="currentColor" stroke-width="1.7" fill="none" stroke-dasharray="3 2.8"/><path d="M6.5 8h9M6.5 11h6" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/></symbol>
'''
icon_extra = icon_anchor + '''  <symbol id="i-resize" viewBox="0 0 24 24"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 8l8 8M16 12v4h-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-lock" viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.7" fill="none"/><path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round"/><circle cx="12" cy="15" r="1.4" fill="currentColor"/></symbol>
  <symbol id="i-unlock" viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.7" fill="none"/><path d="M16 10V7a4 4 0 0 0-7.5-2" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round"/><circle cx="12" cy="15" r="1.4" fill="currentColor"/></symbol>
'''
html = rep(html, icon_anchor, icon_extra, "group menu icons")

# Backward-compatible board normalization for new manual sizing fields.
old_norm = '''  b.groups = b.groups.filter(g => g && g.id).map(g => {
    const itemIds = [...new Set(Array.isArray(g.itemIds) ? g.itemIds : [])].filter(id => ids.has(id));
    return { id: g.id, name: String(g.name || "Group").slice(0, 48), itemIds, pad: clamp(+g.pad || 42, 28, 120) };
  }).filter(g => g.itemIds.length >= 2);
'''
new_norm = '''  b.groups = b.groups.filter(g => g && g.id).map(g => {
    const itemIds = [...new Set(Array.isArray(g.itemIds) ? g.itemIds : [])].filter(id => ids.has(id));
    let mode = g.mode === "manual" ? "manual" : "auto";
    let box = null;
    if (mode === "manual" && g.box && [g.box.x, g.box.y, g.box.w, g.box.h].every(Number.isFinite)) {
      box = { x:+g.box.x, y:+g.box.y, w:Math.max(180, +g.box.w), h:Math.max(120, +g.box.h) };
    } else if (mode === "manual") mode = "auto";
    return { id:g.id, name:String(g.name || "Group").slice(0, 48), itemIds, pad:clamp(+g.pad || 42, 28, 120),
      mode, locked:mode === "manual" && !!g.locked, box };
  }).filter(g => g.itemIds.length >= 2);
'''
html = rep(html, old_norm, new_norm, "group normalization")

# Replace the group-area implementation as one cohesive block.
new_group_block = r'''const GROUP_MIN_W = 180, GROUP_MIN_H = 120;
let editingGroupId = "";
function autoGroupBounds(g) {
  const members = (g.itemIds || []).map(byId).filter(Boolean);
  if (members.length < 2) return null;
  const pad = clamp(+g.pad || 42, 28, 120);
  const labelGap = 18;
  const x1 = Math.min(...members.map(i => i.x)) - pad;
  const y1 = Math.min(...members.map(i => i.y)) - pad - labelGap;
  const x2 = Math.max(...members.map(i => i.x + i.w)) + pad;
  const y2 = Math.max(...members.map(i => i.y + i.h)) + pad;
  return { x:x1, y:y1, w:x2 - x1, h:y2 - y1 };
}
function groupBounds(g) {
  if (g && g.mode === "manual" && g.box && [g.box.x, g.box.y, g.box.w, g.box.h].every(Number.isFinite)) {
    return { x:g.box.x, y:g.box.y, w:Math.max(GROUP_MIN_W, g.box.w), h:Math.max(GROUP_MIN_H, g.box.h) };
  }
  return autoGroupBounds(g);
}
function placeGroupBox(n, b) {
  n.style.left = b.x + "px"; n.style.top = b.y + "px";
  n.style.width = b.w + "px"; n.style.height = b.h + "px";
}
function beginGroupBoxGesture(e, g, n, kind) {
  if (!g || g.mode !== "manual" || g.locked) return;
  const base = groupBounds(g); if (!base) return;
  e.preventDefault(); e.stopPropagation();
  const sx = e.clientX, sy = e.clientY;
  let snapped = false;
  const onMove = ev => {
    ev.preventDefault();
    const scale = Math.max(.05, view.s || 1);
    const dx = (ev.clientX - sx) / scale, dy = (ev.clientY - sy) / scale;
    if (!snapped && Math.abs(dx) + Math.abs(dy) < .6) return;
    if (!snapped) { snap(); snapped = true; }
    let x = base.x, y = base.y, w = base.w, h = base.h;
    if (kind === "move") { x = base.x + dx; y = base.y + dy; }
    else {
      if (kind.includes("e")) w = Math.max(GROUP_MIN_W, base.w + dx);
      if (kind.includes("s")) h = Math.max(GROUP_MIN_H, base.h + dy);
      if (kind.includes("w")) { w = Math.max(GROUP_MIN_W, base.w - dx); x = base.x + (base.w - w); }
      if (kind.includes("n")) { h = Math.max(GROUP_MIN_H, base.h - dy); y = base.y + (base.h - h); }
    }
    g.box = { x, y, w, h };
    placeGroupBox(n, g.box);
  };
  const onDone = () => {
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onDone);
    window.removeEventListener("pointercancel", onDone);
    if (snapped) { save(); renderGroups(); }
  };
  window.addEventListener("pointermove", onMove, { passive:false });
  window.addEventListener("pointerup", onDone, { once:true });
  window.addEventListener("pointercancel", onDone, { once:true });
}
function renderGroups() {
  $$(".group-box").forEach(n => n.remove());
  (board.groups || []).forEach(g => {
    const b = groupBounds(g); if (!b) return;
    const manual = g.mode === "manual", editing = manual && !g.locked && editingGroupId === g.id;
    const n = document.createElement("div");
    n.className = "group-box" + (manual ? " manual" : " auto") + (editing ? " group-editing" : "") + (g.locked ? " group-locked" : "");
    n.dataset.group = g.id;
    placeGroupBox(n, b);
    n.innerHTML = `<button type="button" class="group-label" data-group-label="${g.id}" title="Group area — ${manual ? (g.locked ? "manual, locked" : "manual sizing") : "automatic sizing"}">${esc(g.name || "Group")}</button>${editing ? `
      <button type="button" class="group-resize-handle nw" data-dir="nw" aria-label="Resize top left"></button>
      <button type="button" class="group-resize-handle ne" data-dir="ne" aria-label="Resize top right"></button>
      <button type="button" class="group-resize-handle sw" data-dir="sw" aria-label="Resize bottom left"></button>
      <button type="button" class="group-resize-handle se" data-dir="se" aria-label="Resize bottom right"></button>` : ""}`;
    const label = n.querySelector(".group-label");
    label.addEventListener("pointerdown", e => {
      e.preventDefault(); e.stopPropagation();
      groupMenu(g.id, e.clientX, e.clientY);
    });
    if (editing) {
      n.querySelectorAll(".group-resize-handle").forEach(h => h.addEventListener("pointerdown", e => beginGroupBoxGesture(e, g, n, h.dataset.dir)));
      n.addEventListener("pointerdown", e => {
        if (e.target.closest(".group-label,.group-resize-handle")) return;
        beginGroupBoxGesture(e, g, n, "move");
      });
    }
    world.appendChild(n);
  });
}
function pruneGroups() {
  const ids = new Set(board.items.map(i => i.id));
  board.groups = (board.groups || []).map(g => ({ ...g, itemIds: (g.itemIds || []).filter(id => ids.has(id)) }))
    .filter(g => g.itemIds.length >= 2);
  if (editingGroupId && !(board.groups || []).some(g => g.id === editingGroupId)) editingGroupId = "";
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
  board.groups.push({ id:uid(), name:(v.trim() || "Group").slice(0, 48), itemIds:clean, pad:42, mode:"auto", locked:false, box:null });
  renderGroups(); save();
  toast("Group area added");
}
function groupMenu(id, x, y) {
  const g = (board.groups || []).find(k => k.id === id); if (!g) return;
  const manual = g.mode === "manual";
  const editing = manual && !g.locked && editingGroupId === id;
  const state = manual ? `Manual sizing${g.locked ? " · Locked" : editing ? " · Editing" : ""}` : "Automatic sizing";
  showCtx(`<div class="ctx-rel-head"><b>${esc(g.name || "Group")}</b><span>${g.itemIds.length} items · ${state}</span></div>
    <button data-a="select"><svg><use href="#i-lasso"/></svg>Select contents</button>
    <button data-a="rename"><svg><use href="#i-card"/></svg>Rename group area</button>
    <hr><button data-a="mode"><svg><use href="#i-group"/></svg>${manual ? "Use automatic sizing" : "Use manual sizing"}</button>
    ${manual ? `<button data-a="editbox"><svg><use href="#i-resize"/></svg>${editing ? "Finish resizing" : "Resize / move box"}</button>
    <button data-a="lock"><svg><use href="#${g.locked ? "i-unlock" : "i-lock"}"/></svg>${g.locked ? "Unlock box" : "Lock box"}</button>` : ""}
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
    if (b.dataset.a === "mode") {
      if (manual) {
        snap(); g.mode = "auto"; g.locked = false; g.box = null; if (editingGroupId === id) editingGroupId = "";
        renderGroups(); save(); toast("Automatic sizing on — the boundary follows its contents.");
      } else {
        const bounds = autoGroupBounds(g); if (!bounds) return;
        snap(); g.mode = "manual"; g.locked = false; g.box = { ...bounds }; editingGroupId = id;
        renderGroups(); save(); toast("Manual sizing on — drag the box to move it, or drag a corner to resize.", 4200);
      }
      return;
    }
    if (b.dataset.a === "editbox") {
      if (g.locked) { toast("Unlock this group box before resizing it."); return; }
      editingGroupId = editing ? "" : id; renderGroups();
      toast(editing ? "Finished resizing" : "Drag the box to move it; drag a corner to resize.", editing ? 1800 : 3600);
      return;
    }
    if (b.dataset.a === "lock") {
      snap(); g.locked = !g.locked;
      editingGroupId = g.locked ? "" : id;
      renderGroups(); save();
      toast(g.locked ? "Group box locked" : "Group box unlocked — resize handles are active");
      return;
    }
    if (b.dataset.a === "del") {
      snap(); board.groups = (board.groups || []).filter(k => k.id !== id); if (editingGroupId === id) editingGroupId = "";
      renderGroups(); save(); toast("Group area removed — items kept");
    }
  };
}
'''
html = sub1(html, r'function groupBounds\(g\) \{.*?\n\}\n\nfunction renderAll\(\) \{', new_group_block + '\nfunction renderAll() {', "group implementation", re.S)

# Onboarding copy teaches the new sizing mode without adding another step.
html = rep(html,
    '<li><svg><use href="#i-group"/></svg><div><b>Group area = a system boundary</b>Lasso related items and wrap them in a faint labelled area. The boundary follows the cluster as it grows.</div></li>',
    '<li><svg><use href="#i-group"/></svg><div><b>Group area = a system boundary</b>Lasso related items and wrap them in a faint labelled area. It follows the cluster automatically, or tap its name to switch to manual sizing and lock the box in place.</div></li>',
    "onboarding group sizing tip")

# README: replace the whole Group areas section so usage is explicit.
readme = sub1(readme, r'## Group areas\n\n.*?\n\n## Dates and the timeline', '''## Group areas

When a cluster represents one system or subtopic, lasso two or more items and tap **Group area** on the selection bar. Give it a name such as **RAIN SYSTEM** and Pin It draws a faint labelled boundary behind those items.

Group areas start in **Automatic sizing**. The boundary recalculates from its members, so it grows, shrinks and moves as the cluster changes while every note and card remains individually draggable, resizable and linkable.

Tap the group/system name to open its menu. Choose **Use manual sizing** when you want the border itself to be art-directed: drag the box to move it and drag any corner handle to resize it without moving the cards inside. Once it is where you want it, choose **Lock box** to prevent accidental movement or resizing. The same menu can unlock it later, or switch the group back to automatic sizing at any time.

Manual size, position and lock state are stored with the board, survive import/export and undo/redo, adapt to Corkboard, Whiteboard and Blueprint themes, count toward **Fit board**, and are included when the board is saved as a picture.

## Dates and the timeline''', "README group section", re.S)

entry = '''## 1.7.0 — 15 September 2026, 10:07 UTC

- Added **Automatic / Manual sizing** to the menu opened from a system/group name.
- Manual group boundaries can be moved independently and resized from four touch-friendly corner handles without moving the cards inside them.
- Added **Lock box / Unlock box** for manual boundaries to prevent accidental movement or resizing once positioned.
- Switching back to Automatic immediately returns the boundary to following its member items.
- Manual box geometry and lock state persist through save, backup/import, undo/redo, Fit board and picture export.
- Updated onboarding and README guidance for the new group-boundary controls.

'''
log = rep(log, "---\n\n", "---\n\n" + entry, "changelog insertion")

INDEX.write_text(html, encoding="utf-8")
README.write_text(readme, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# First pass: structural and release assertions.
required = [
    'const VERSION = "1.7.0";',
    'const BUILD = "15 September 2026, 10:07 UTC";',
    'version: "1.7.0", date: "15 September 2026, 10:07 UTC"',
    'const GROUP_MIN_W = 180, GROUP_MIN_H = 120;',
    'function autoGroupBounds(g)',
    'function beginGroupBoxGesture(e, g, n, kind)',
    'Use manual sizing',
    'Use automatic sizing',
    'Resize / move box',
    'Lock box',
    'Unlock box',
    'class="group-resize-handle nw"',
    'mode:"auto", locked:false, box:null',
    'g.mode === "manual"',
    'box = { x:+g.box.x, y:+g.box.y, w:Math.max(180, +g.box.w), h:Math.max(120, +g.box.h) };',
]
for token in required:
    if token not in html:
        raise SystemExit("verification failed: " + token)
if "## 1.7.0 — 15 September 2026, 10:07 UTC" not in log:
    raise SystemExit("changelog mismatch")
for token in ("Use manual sizing", "Lock box", "four touch-friendly corner handles"):
    if token not in readme:
        raise SystemExit("README verification failed: " + token)

# Parse every inline script independently.
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# Second-pass behavioural contract checks.
checks = {
    "auto-default": 'mode:"auto", locked:false, box:null' in html,
    "manual-bounds": 'g.mode === "manual" && g.box' in html,
    "scale-correct-drag": '(ev.clientX - sx) / scale' in html and '(ev.clientY - sy) / scale' in html,
    "four-corners": all(f'data-dir="{d}"' in html for d in ("nw", "ne", "sw", "se")),
    "move-box": 'beginGroupBoxGesture(e, g, n, "move")' in html,
    "lock-guard": 'g.mode !== "manual" || g.locked' in html,
    "unlock-enters-edit": 'editingGroupId = g.locked ? "" : id;' in html,
    "auto-resets-box": 'g.mode = "auto"; g.locked = false; g.box = null;' in html,
    "undo-before-gesture": 'if (!snapped) { snap(); snapped = true; }' in html,
    "persistence-normalise": 'locked:mode === "manual" && !!g.locked, box' in html,
    "release-sync": 'Version 1.7.0 · 15 September 2026, 10:07 UTC' in html and '## 1.7.0 — 15 September 2026, 10:07 UTC' in log,
}
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise SystemExit("second-pass checks failed: " + ", ".join(failed))
print(f"Pin It 1.7.0 verified: {len(scripts)} inline scripts parse; {len(checks)} second-pass checks passed")
