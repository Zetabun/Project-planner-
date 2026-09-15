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


def rep(text, old, new, label, count=1):
    n = text.count(old)
    if n != count:
        raise SystemExit(f"{label}: expected {count} match(es), found {n}")
    return text.replace(old, new, count)


def sub1(text, pattern, repl, label, flags=0):
    out, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, found {n}")
    return out


# Release metadata.
html = rep(html, "Version 1.7.0 · 15 September 2026, 10:07 UTC", "Version 1.8.0 · 15 September 2026, 10:49 UTC", "header version")
html = rep(html, 'const VERSION = "1.7.0";', 'const VERSION = "1.8.0";', "VERSION")
html = rep(html, 'const BUILD = "15 September 2026, 10:07 UTC";', 'const BUILD = "15 September 2026, 10:49 UTC";', "BUILD")
release = '''  {
    version: "1.8.0", date: "15 September 2026, 10:49 UTC",
    summary: "Systems become active planning objects: edit their membership, move whole systems, collapse them for overview, and see when a new release is waiting to be read.",
    items: [
      "Added Edit contents to system/group menus: tap cards and notes to add or remove them from an existing system without recreating the boundary.",
      "Added Move system + contents, which selects a system as one movable cluster while keeping manual boundaries aligned with their contents.",
      "Added Collapse / Expand system. Collapsed systems hide their internal cards, compress to a compact summary, and keep external connections routed to the system block.",
      "Collapsed systems are respected by Fit board and picture export, while their hidden item data and links remain intact for expansion later.",
      "Added unread-update badges to the burger menu and What's new button. Opening the latest release history marks that version as read and clears both badges."
    ]
  },\n'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# Group/system affordances and unread-release badges.
group_css_anchor = 'body[data-theme="blueprint"] .group-resize-handle::after{border-color:#8dd8ff; background:#173f5d}\n'
group_css_extra = group_css_anchor + '''.group-box.collapsed{height:76px; min-height:76px; background:rgba(255,244,213,.12); box-shadow:inset 0 0 26px rgba(73,42,18,.06),0 7px 18px rgba(50,28,12,.06)}
.group-box.collapsed .group-label{max-width:calc(100% - 28px)}
.group-summary{position:absolute; left:16px; right:14px; top:44px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  font:10.5px/1.2 var(--ui); letter-spacing:.025em; color:rgba(92,57,33,.72); pointer-events:none}
.group-box.group-members-editing{outline:2px solid rgba(201,162,39,.68); outline-offset:5px}
.group-box.group-moving{outline:2px dashed rgba(201,162,39,.72); outline-offset:5px}
body[data-theme="white"] .group-box.collapsed{background:rgba(89,171,219,.09)}
body[data-theme="white"] .group-summary{color:rgba(49,95,127,.78)}
body[data-theme="white"] .group-box.group-members-editing,body[data-theme="white"] .group-box.group-moving{outline-color:rgba(58,146,201,.66)}
body[data-theme="blueprint"] .group-box.collapsed{background:rgba(141,216,255,.065)}
body[data-theme="blueprint"] .group-summary{font-family:var(--bp-mono); color:#9fcde5}
body[data-theme="blueprint"] .group-box.group-members-editing,body[data-theme="blueprint"] .group-box.group-moving{outline-color:rgba(141,216,255,.7)}
'''
html = rep(html, group_css_anchor, group_css_extra, "group workflow CSS")

chip_anchor = '.chip.icon{width:38px; padding:0; justify-content:center}\n'
badge_css = chip_anchor + '''#btn-cases{position:relative}
#btn-cases.has-update::after{content:""; position:absolute; right:-4px; top:-4px; width:11px; height:11px; border-radius:50%;
  background:#e24c3f; box-shadow:0 0 0 2px var(--ui-2),0 2px 6px rgba(0,0,0,.42)}
#btn-releases{position:relative; justify-content:flex-start; padding-right:52px}
#btn-releases.has-update::after{content:"NEW"; position:absolute; right:10px; top:50%; transform:translateY(-50%); padding:2px 6px 1px;
  border-radius:999px; background:#e24c3f; color:#fff; font:700 9px/1.35 var(--ui); letter-spacing:.08em; box-shadow:0 2px 6px rgba(0,0,0,.2)}
'''
html = rep(html, chip_anchor, badge_css, "release badge CSS")

# Persist collapse state on groups and keep old boards compatible.
html = rep(html,
    '      mode, locked:mode === "manual" && !!g.locked, box };',
    '      mode, locked:mode === "manual" && !!g.locked, collapsed:!!g.collapsed, box };',
    "group collapsed normalization")

# Replace group implementation as one coherent unit.
new_group_block = r'''const GROUP_MIN_W = 180, GROUP_MIN_H = 120;
let editingGroupId = "", editingGroupMembersId = "", movingGroupContentsId = "";
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
function expandedGroupBounds(g) {
  if (g && g.mode === "manual" && g.box && [g.box.x, g.box.y, g.box.w, g.box.h].every(Number.isFinite)) {
    return { x:g.box.x, y:g.box.y, w:Math.max(GROUP_MIN_W, g.box.w), h:Math.max(GROUP_MIN_H, g.box.h) };
  }
  return autoGroupBounds(g);
}
function groupBounds(g) {
  const b = expandedGroupBounds(g); if (!b) return null;
  if (!g.collapsed) return b;
  const nameW = 174 + Math.min(130, String(g.name || "Group").length * 4.6);
  return { x:b.x, y:b.y, w:clamp(nameW, 220, 340), h:76 };
}
function collapsedGroupForItem(id) {
  return (board.groups || []).find(g => g.collapsed && (g.itemIds || []).includes(id)) || null;
}
function itemHiddenByGroup(id) { return !!collapsedGroupForItem(id); }
function linkEndpoint(id) {
  const g = collapsedGroupForItem(id);
  if (!g) return byId(id);
  const b = groupBounds(g); if (!b) return null;
  return { id:"group:" + g.id, x:b.x, y:b.y, w:b.w, h:b.h, type:"marker", done:false };
}
function groupStats(g) {
  const members = (g.itemIds || []).map(byId).filter(Boolean);
  let tasks = 0, done = 0;
  members.forEach(i => (i.tasks || []).forEach(t => { tasks++; if (t.done) done++; }));
  return tasks ? `${members.length} items · ${done}/${tasks} tasks` : `${members.length} items`;
}
function placeGroupBox(n, b) {
  n.style.left = b.x + "px"; n.style.top = b.y + "px";
  n.style.width = b.w + "px"; n.style.height = b.h + "px";
}
function beginGroupBoxGesture(e, g, n, kind) {
  if (!g || g.mode !== "manual" || g.locked || g.collapsed) return;
  const base = expandedGroupBounds(g); if (!base) return;
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
    const manual = g.mode === "manual", editing = manual && !g.locked && !g.collapsed && editingGroupId === g.id;
    const membersEditing = editingGroupMembersId === g.id, moving = movingGroupContentsId === g.id;
    const n = document.createElement("div");
    n.className = "group-box" + (manual ? " manual" : " auto") + (editing ? " group-editing" : "") +
      (g.locked ? " group-locked" : "") + (g.collapsed ? " collapsed" : "") +
      (membersEditing ? " group-members-editing" : "") + (moving ? " group-moving" : "");
    n.dataset.group = g.id;
    placeGroupBox(n, b);
    n.innerHTML = `<button type="button" class="group-label" data-group-label="${g.id}" title="Group area — ${g.collapsed ? "collapsed" : manual ? (g.locked ? "manual, locked" : "manual sizing") : "automatic sizing"}">${esc(g.name || "Group")}</button>${g.collapsed ? `<div class="group-summary">${esc(groupStats(g))} · collapsed</div>` : ""}${editing ? `
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
  const has = id => id && (board.groups || []).some(g => g.id === id);
  if (!has(editingGroupId)) editingGroupId = "";
  if (!has(editingGroupMembersId)) editingGroupMembersId = "";
  if (!has(movingGroupContentsId)) movingGroupContentsId = "";
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
  board.groups.push({ id:uid(), name:(v.trim() || "Group").slice(0, 48), itemIds:clean, pad:42, mode:"auto", locked:false, collapsed:false, box:null });
  renderGroups(); save();
  toast("Group area added");
}
function toggleGroupMemberItem(itemId) {
  const g = (board.groups || []).find(k => k.id === editingGroupMembersId);
  if (!g) { editingGroupMembersId = ""; return false; }
  const has = (g.itemIds || []).includes(itemId);
  if (has && g.itemIds.length <= 2) { toast("A system needs at least two items"); return true; }
  snap();
  g.itemIds = has ? g.itemIds.filter(id => id !== itemId) : [...g.itemIds, itemId];
  setMulti(g.itemIds.filter(id => byId(id)));
  renderGroups(); save();
  toast(has ? "Removed from " + g.name : "Added to " + g.name, 1600);
  return true;
}
function groupMenu(id, x, y) {
  const g = (board.groups || []).find(k => k.id === id); if (!g) return;
  const manual = g.mode === "manual";
  const editing = manual && !g.locked && !g.collapsed && editingGroupId === id;
  const membersEditing = editingGroupMembersId === id;
  const state = `${g.collapsed ? "Collapsed · " : ""}${manual ? `Manual sizing${g.locked ? " · Locked" : editing ? " · Editing border" : ""}` : "Automatic sizing"}`;
  showCtx(`<div class="ctx-rel-head"><b>${esc(g.name || "Group")}</b><span>${g.itemIds.length} items · ${state}</span></div>
    <button data-a="select"><svg><use href="#i-lasso"/></svg>Select contents</button>
    <button data-a="members"><svg><use href="#i-group"/></svg>${membersEditing ? "Finish editing contents" : "Edit contents"}</button>
    <button data-a="moveall"><svg><use href="#i-fit"/></svg>Move system + contents</button>
    <button data-a="collapse"><svg><use href="#${g.collapsed ? "i-plus" : "i-minus"}"/></svg>${g.collapsed ? "Expand system" : "Collapse system"}</button>
    <button data-a="rename"><svg><use href="#i-card"/></svg>Rename group area</button>
    <hr><button data-a="mode"><svg><use href="#i-group"/></svg>${manual ? "Use automatic sizing" : "Use manual sizing"}</button>
    ${manual ? `<button data-a="editbox"><svg><use href="#i-resize"/></svg>${editing ? "Finish resizing" : "Resize / move box"}</button>
    <button data-a="lock"><svg><use href="#${g.locked ? "i-unlock" : "i-lock"}"/></svg>${g.locked ? "Unlock box" : "Lock box"}</button>` : ""}
    <hr><button data-a="del" class="danger"><svg><use href="#i-trash"/></svg>Remove group area</button>`, x, y);
  ctx.onclick = e => {
    const b = e.target.closest("button"); if (!b) return;
    hideCtx();
    if (b.dataset.a === "select") { setMulti((g.itemIds || []).filter(id => byId(id))); return; }
    if (b.dataset.a === "members") {
      if (membersEditing) {
        editingGroupMembersId = ""; clearMulti(false); renderGroups(); toast("Finished editing system contents");
      } else {
        if (g.collapsed) { snap(); g.collapsed = false; save(); }
        editingGroupMembersId = id; movingGroupContentsId = ""; editingGroupId = "";
        setMulti((g.itemIds || []).filter(id => byId(id))); renderGroups();
        toast("Tap cards or notes to add/remove them. Tap the system name when finished.", 4800);
      }
      return;
    }
    if (b.dataset.a === "moveall") {
      if (g.collapsed) { snap(); g.collapsed = false; save(); }
      editingGroupMembersId = ""; editingGroupId = ""; movingGroupContentsId = id;
      setMulti((g.itemIds || []).filter(id => byId(id))); renderGroups();
      toast("Drag any selected item to move the whole system. The boundary moves with it.", 4400);
      return;
    }
    if (b.dataset.a === "collapse") {
      snap(); g.collapsed = !g.collapsed;
      if (editingGroupId === id) editingGroupId = "";
      if (editingGroupMembersId === id) editingGroupMembersId = "";
      if (movingGroupContentsId === id) movingGroupContentsId = "";
      deselect(); renderAll(); save(); toast(g.collapsed ? "System collapsed" : "System expanded");
      return;
    }
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
        const bounds = expandedGroupBounds(g); if (!bounds) return;
        snap(); g.mode = "manual"; g.locked = false; g.box = { ...bounds }; editingGroupId = g.collapsed ? "" : id;
        renderGroups(); save(); toast(g.collapsed ? "Manual sizing saved — expand the system to edit its border." : "Manual sizing on — drag the box to move it, or drag a corner to resize.", 4200);
      }
      return;
    }
    if (b.dataset.a === "editbox") {
      if (g.locked) { toast("Unlock this group box before resizing it."); return; }
      if (g.collapsed) { snap(); g.collapsed = false; editingGroupId = id; renderAll(); save(); toast("System expanded — resize handles are active"); return; }
      editingGroupId = editing ? "" : id; renderGroups();
      toast(editing ? "Finished resizing" : "Drag the box to move it; drag a corner to resize.", editing ? 1800 : 3600);
      return;
    }
    if (b.dataset.a === "lock") {
      snap(); g.locked = !g.locked;
      editingGroupId = g.locked || g.collapsed ? "" : id;
      renderGroups(); save();
      toast(g.locked ? "Group box locked" : (g.collapsed ? "Group box unlocked" : "Group box unlocked — resize handles are active"));
      return;
    }
    if (b.dataset.a === "del") {
      snap(); board.groups = (board.groups || []).filter(k => k.id !== id);
      if (editingGroupId === id) editingGroupId = ""; if (editingGroupMembersId === id) editingGroupMembersId = ""; if (movingGroupContentsId === id) movingGroupContentsId = "";
      renderAll(); save(); toast("Group area removed — items kept");
    }
  };
}
'''
html = sub1(html, r'const GROUP_MIN_W = 180, GROUP_MIN_H = 120;.*?\nfunction renderAll\(\) \{', new_group_block + '\nfunction renderAll() {', "system group implementation", re.S)

# Collapsed systems hide members but retain data; external links terminate at compact group blocks.
html = rep(html,
    '    el.style.display = (hideDone && it.done) ? "none" : "";',
    '    el.style.display = ((hideDone && it.done) || itemHiddenByGroup(it.id)) ? "none" : "";',
    "filter collapsed members")

endpoint_old = '    const A = byId(l.a), B = byId(l.b); if (!A || !B) return;'
endpoint_new = '    const A = linkEndpoint(l.a), B = linkEndpoint(l.b); if (!A || !B || A.id === B.id) return;'
html = rep(html, endpoint_old, endpoint_new, "link endpoints for collapsed systems", count=3)

html = rep(html,
    '  board.items.forEach(i => {\n    x1 = Math.min(x1, i.x); y1 = Math.min(y1, i.y);',
    '  board.items.forEach(i => {\n    if (itemHiddenByGroup(i.id)) return;\n    x1 = Math.min(x1, i.x); y1 = Math.min(y1, i.y);',
    "collapsed extents")

html = rep(html,
    '  const order = board.items.filter(i => !(hideDone && i.done)).sort((a, b) => (a.z || 0) - (b.z || 0));',
    '  const order = board.items.filter(i => !(hideDone && i.done) && !itemHiddenByGroup(i.id)).sort((a, b) => (a.z || 0) - (b.z || 0));',
    "collapsed PNG items")

html = rep(html,
    '    c.lineWidth = 2; c.setLineDash([8, 6]);',
    '    c.lineWidth = 2; c.setLineDash(gp.mode === "manual" ? [] : [8, 6]);',
    "PNG manual group border")

# Center navigation on a collapsed system if the requested item is currently hidden inside one.
old_center = '''function centerOn(it) {
  const r = viewport.getBoundingClientRect();
  world.style.transition = "transform .4s cubic-bezier(.2,.8,.25,1)";
  view.x = r.width / 2 - (it.x + it.w / 2) * view.s;
  view.y = r.height / 2 - (it.y + it.h / 2) * view.s;
  applyView(); setTimeout(() => world.style.transition = "", 420); save();
}
'''
new_center = '''function centerOn(it) {
  const r = viewport.getBoundingClientRect();
  const target = (it && typeof linkEndpoint === "function" && linkEndpoint(it.id)) || it;
  if (!target) return;
  world.style.transition = "transform .4s cubic-bezier(.2,.8,.25,1)";
  view.x = r.width / 2 - (target.x + target.w / 2) * view.s;
  view.y = r.height / 2 - (target.y + target.h / 2) * view.s;
  applyView(); setTimeout(() => world.style.transition = "", 420); save();
}
'''
html = rep(html, old_center, new_center, "center collapsed system")

# Edit-members mode intercepts normal item gestures.
html = rep(html,
    '    if (linking) { completeLink(it.id); return; }\n\n    // checklist toggle',
    '    if (linking) { completeLink(it.id); return; }\n    if (editingGroupMembersId && toggleGroupMemberItem(it.id)) return;\n\n    // checklist toggle',
    "membership pointer toggle")

# Moving a system reuses multi-drag and carries a manual box along with the items.
old_drag = '''    const group = multi.has(it.id) && multi.size > 1;
    if (!group) { selectItem(it.id); bump(it); }
    const p = toWorld(e.clientX, e.clientY);
    if (e.target.closest(".grip")) {
      resize = { id: it.id, sx: p.x, sy: p.y, w: it.w, h: it.h };
    } else {
      drag = { id: it.id, dx: p.x - it.x, dy: p.y - it.y, moved: false, ox: it.x, oy: it.y,
        group: group ? [...multi].map(id => { const o = byId(id); return { id, x: o.x, y: o.y }; }) : null };
'''
new_drag = '''    const group = multi.has(it.id) && multi.size > 1;
    if (!group) { selectItem(it.id); bump(it); }
    const moveSystem = group && movingGroupContentsId ? (board.groups || []).find(g => g.id === movingGroupContentsId) : null;
    const p = toWorld(e.clientX, e.clientY);
    if (e.target.closest(".grip")) {
      resize = { id: it.id, sx: p.x, sy: p.y, w: it.w, h: it.h };
    } else {
      drag = { id: it.id, dx: p.x - it.x, dy: p.y - it.y, moved: false, ox: it.x, oy: it.y,
        group: group ? [...multi].map(id => { const o = byId(id); return { id, x: o.x, y: o.y }; }) : null,
        systemMove: moveSystem ? { id:moveSystem.id, box:moveSystem.mode === "manual" && moveSystem.box ? { ...moveSystem.box } : null } : null };
'''
html = rep(html, old_drag, new_drag, "system multi-drag setup")

html = rep(html,
    '''      drag.group.forEach(g => {
        const o = byId(g.id); if (!o) return;
        o.x = g.x + ddx; o.y = g.y + ddy;
        const e2 = els.get(g.id); if (e2) { e2.style.left = o.x + "px"; e2.style.top = o.y + "px"; }
      });
''',
    '''      drag.group.forEach(g => {
        const o = byId(g.id); if (!o) return;
        o.x = g.x + ddx; o.y = g.y + ddy;
        const e2 = els.get(g.id); if (e2) { e2.style.left = o.x + "px"; e2.style.top = o.y + "px"; }
      });
      if (drag.systemMove && drag.systemMove.box) {
        const sg = (board.groups || []).find(g => g.id === drag.systemMove.id);
        if (sg) sg.box = { ...drag.systemMove.box, x:drag.systemMove.box.x + ddx, y:drag.systemMove.box.y + ddy };
      }
''',
    "manual box follows system move")

old_enddrag = '''function endDrag() {
  clearTimeout(pressT);
  if (drag) { const el = els.get(drag.id); if (el) el.classList.remove("dragging"); if (drag.moved) { justMoved = true; save(); } }
  if (resize) { justMoved = true; refresh(resize.id); save(); }
  drag = null; resize = null;
}
'''
new_enddrag = '''function endDrag() {
  clearTimeout(pressT);
  if (drag) {
    const el = els.get(drag.id); if (el) el.classList.remove("dragging");
    if (drag.moved) {
      justMoved = true;
      if (drag.systemMove) movingGroupContentsId = "";
      save(); renderGroups();
    }
  }
  if (resize) { justMoved = true; refresh(resize.id); save(); }
  drag = null; resize = null;
}
'''
html = rep(html, old_enddrag, new_enddrag, "finish system move")

# Escape cleanly leaves the two new system-edit modes before the general deselect path.
html = rep(html,
    '''  if (e.key === "Escape") {
    if (ideaDrawerOpen()) { toggleIdeaDrawer(false); return; }
    if (activeTags.size) { activeTags.clear(); applyFilter(); return; }
''',
    '''  if (e.key === "Escape") {
    if (ideaDrawerOpen()) { toggleIdeaDrawer(false); return; }
    if (editingGroupMembersId) { editingGroupMembersId = ""; clearMulti(false); renderGroups(); toast("Finished editing system contents"); return; }
    if (movingGroupContentsId) { movingGroupContentsId = ""; clearMulti(false); renderGroups(); toast("System move cancelled"); return; }
    if (activeTags.size) { activeTags.clear(); applyFilter(); return; }
''',
    "escape system modes")

# Unread release badge state. Opening What's new is the read action.
old_release_fn = '''function renderReleaseHistory() {
  const host = $("#release-list");
  host.innerHTML = RELEASES.map((r, i) => `
    <details class="release-item${i === 0 ? " latest" : ""}"${i === 0 ? " open" : ""}>
      <summary><span class="release-ver">${esc(r.version)}</span><span class="release-date">${esc(r.date)}</span></summary>
      <div class="release-copy">
        <p class="release-summary">${esc(r.summary)}</p>
        <ul>${r.items.map(item => `<li>${esc(item)}</li>`).join("")}</ul>
      </div>
    </details>`).join("");
}
function openReleaseHistory() {
  closePanel("cases");
  renderReleaseHistory();
  $("#releasewrap").hidden = false;
  requestAnimationFrame(() => $("#release-x").focus());
}
'''
new_release_fn = '''function renderReleaseHistory() {
  const host = $("#release-list");
  host.innerHTML = RELEASES.map((r, i) => `
    <details class="release-item${i === 0 ? " latest" : ""}"${i === 0 ? " open" : ""}>
      <summary><span class="release-ver">${esc(r.version)}</span><span class="release-date">${esc(r.date)}</span></summary>
      <div class="release-copy">
        <p class="release-summary">${esc(r.summary)}</p>
        <ul>${r.items.map(item => `<li>${esc(item)}</li>`).join("")}</ul>
      </div>
    </details>`).join("");
}
function updateReleaseBadges() {
  const unread = !!DB.lastSeenRelease && DB.lastSeenRelease !== VERSION;
  $("#btn-cases").classList.toggle("has-update", unread);
  $("#btn-releases").classList.toggle("has-update", unread);
  $("#btn-cases").setAttribute("aria-label", unread ? "Boards — new update available" : "Boards");
}
function markLatestReleaseRead() {
  if (DB.lastSeenRelease === VERSION) return;
  DB.lastSeenRelease = VERSION;
  updateReleaseBadges();
  save(true);
}
function openReleaseHistory() {
  closePanel("cases");
  renderReleaseHistory();
  $("#releasewrap").hidden = false;
  markLatestReleaseRead();
  requestAnimationFrame(() => $("#release-x").focus());
}
'''
html = rep(html, old_release_fn, new_release_fn, "release badge logic")

startup_old = '''const wasVersion = DB.version;
DB.version = VERSION;
applyTheme();
'''
startup_new = '''const wasVersion = DB.version;
if (!DB.lastSeenRelease) DB.lastSeenRelease = wasVersion || VERSION;
DB.version = VERSION;
updateReleaseBadges();
applyTheme();
'''
html = rep(html, startup_old, startup_new, "startup unread release state")

# Onboarding reflects systems as editable planning objects.
html = rep(html,
    '<li><svg><use href="#i-group"/></svg><div><b>Group area = a system boundary</b>Lasso related items and wrap them in a faint labelled area. It follows the cluster automatically, or tap its name to switch to manual sizing and lock the box in place.</div></li>',
    '<li><svg><use href="#i-group"/></svg><div><b>Group area = a system boundary</b>Lasso related items into a named system. Tap its name later to edit what belongs, move the whole system, collapse it for overview, or take manual control of its boundary.</div></li>',
    "onboarding system workflow")

# README: expand system workflow and release notification guidance.
old_group_readme = '''Tap the group/system name to open its menu. Choose **Use manual sizing** when you want the border itself to be art-directed: drag the box to move it and drag any corner handle to resize it without moving the cards inside. Once it is where you want it, choose **Lock box** to prevent accidental movement or resizing. The same menu can unlock it later, or switch the group back to automatic sizing at any time.

Manual size, position and lock state are stored with the board, survive import/export and undo/redo, adapt to Corkboard, Whiteboard and Blueprint themes, count toward **Fit board**, and are included when the board is saved as a picture.
'''
new_group_readme = '''Tap the group/system name to open its menu. **Edit contents** turns membership into an explicit editing mode: tap any card or note to add or remove it, without deleting and recreating the system. **Move system + contents** selects all of its members as one cluster; drag any selected item and the full system moves together, including a manually positioned boundary.

**Collapse system** compresses a busy system into a small summary block while keeping its cards, notes and links intact underneath. Links that leave the system temporarily terminate at the collapsed block, and **Fit board** plus picture export use the compact view. Expand it from the same menu to restore the full layout exactly where it was.

Choose **Use manual sizing** when you want the border itself to be art-directed: drag the box to move it and drag any corner handle to resize it without moving the cards inside. Once it is where you want it, choose **Lock box** to prevent accidental movement or resizing. The same menu can unlock it later, or switch the group back to automatic sizing at any time.

Membership, collapse state, manual size, position and lock state are stored with the board, survive import/export and undo/redo, adapt to Corkboard, Whiteboard and Blueprint themes, count toward **Fit board**, and are included when the board is saved as a picture.
'''
readme = rep(readme, old_group_readme, new_group_readme, "README system workflow")

readme = rep(readme,
    '''The boards drawer has a **What's new** button. It opens the full release history, newest first, with the current release expanded and every previous release available underneath. The version stamp at the bottom of the drawer opens the same view. The history is embedded in `index.html`, so it still works when the app is running as a single local/offline file.
''',
    '''The boards drawer has a **What's new** button. It opens the full release history, newest first, with the current release expanded and every previous release available underneath. The version stamp at the bottom of the drawer opens the same view. The history is embedded in `index.html`, so it still works when the app is running as a single local/offline file.

When the app version is newer than the last release history the user opened, a notification dot appears on the burger menu and a **NEW** badge appears on **What's new**. Opening the release history marks the current version as read and clears both badges; if it is not opened, the badges remain on later visits.
''',
    "README release badges")

# Changelog newest first.
entry = '''## 1.8.0 — 15 September 2026, 10:49 UTC

- Added **Edit contents** to system/group menus so existing systems can gain or lose cards and notes without being recreated.
- Added **Move system + contents** using the existing multi-drag interaction; manual boundaries travel with the selected system.
- Added **Collapse / Expand system** with a compact system summary. Internal items hide without being deleted and external links reroute to the collapsed block.
- Fit Board and picture export now respect collapsed systems and omit their hidden internal items while preserving all data for later expansion.
- Added unread-update badges: a dot on the burger menu and a **NEW** badge on **What's new** until the latest release history is opened.
- Updated onboarding and README guidance for the expanded system workflow and release notifications.

'''
log = rep(log, "---\n\n", "---\n\n" + entry, "changelog insertion")

INDEX.write_text(html, encoding="utf-8")
README.write_text(readme, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# First pass: release and feature assertions.
required = [
    'const VERSION = "1.8.0";',
    'const BUILD = "15 September 2026, 10:49 UTC";',
    'version: "1.8.0", date: "15 September 2026, 10:49 UTC"',
    'editingGroupMembersId',
    'movingGroupContentsId',
    'Edit contents',
    'Move system + contents',
    'Collapse system',
    'Expand system',
    'function itemHiddenByGroup(id)',
    'function linkEndpoint(id)',
    'collapsed:!!g.collapsed',
    'collapsed:false, box:null',
    'DB.lastSeenRelease',
    'updateReleaseBadges()',
    '#btn-cases.has-update::after',
    '#btn-releases.has-update::after',
]
for token in required:
    if token not in html:
        raise SystemExit("verification failed: " + token)
if "## 1.8.0 — 15 September 2026, 10:49 UTC" not in log:
    raise SystemExit("changelog mismatch")
for token in ("Edit contents", "Move system + contents", "Collapse system", "NEW"):
    if token not in readme:
        raise SystemExit("README verification failed: " + token)

# Parse every inline script independently.
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# Second pass: behavioural contracts for systems and unread releases.
checks = {
    "edit-members-click": 'if (editingGroupMembersId && toggleGroupMemberItem(it.id)) return;' in html,
    "minimum-two": 'g.itemIds.length <= 2' in html,
    "move-system-selection": 'movingGroupContentsId = id;' in html and 'systemMove: moveSystem ?' in html,
    "manual-box-follows": 'x:drag.systemMove.box.x + ddx' in html and 'y:drag.systemMove.box.y + ddy' in html,
    "collapse-persists": 'collapsed:!!g.collapsed' in html and 'g.collapsed = !g.collapsed;' in html,
    "collapsed-items-hidden": 'itemHiddenByGroup(it.id)' in html,
    "collapsed-links-reroute": html.count('const A = linkEndpoint(l.a), B = linkEndpoint(l.b); if (!A || !B || A.id === B.id) return;') == 3,
    "collapsed-export": '!itemHiddenByGroup(i.id)' in html and 'c.setLineDash(gp.mode === "manual" ? [] : [8, 6])' in html,
    "badge-version-compare": 'DB.lastSeenRelease !== VERSION' in html,
    "badge-read-on-open": 'markLatestReleaseRead();' in new_release_fn,
    "badge-survives-revisit": 'if (!DB.lastSeenRelease) DB.lastSeenRelease = wasVersion || VERSION;' in html,
    "release-sync": 'Version 1.8.0 · 15 September 2026, 10:49 UTC' in html and '## 1.8.0 — 15 September 2026, 10:49 UTC' in log,
}
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise SystemExit("second-pass checks failed: " + ", ".join(failed))
print(f"Pin It 1.8.0 verified: {len(scripts)} inline scripts parse; {len(checks)} second-pass checks passed")
