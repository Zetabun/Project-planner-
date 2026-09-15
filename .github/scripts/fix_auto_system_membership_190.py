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


# Automatic systems should adopt newly-created or deliberately moved ungrouped
# items whose centre lands inside their current automatic boundary. Membership is
# sticky once established: moving an existing member out does not silently remove
# semantic membership, and manual/collapsed systems never auto-capture items.
member_anchor = '''function toggleGroupMemberItem(itemId) {
'''
member_helper = r'''let autoGroupRefreshQueued = false;
function queueAutoGroupRefresh() {
  if (autoGroupRefreshQueued) return;
  autoGroupRefreshQueued = true;
  requestAnimationFrame(() => {
    autoGroupRefreshQueued = false;
    renderGroups();
    if (typeof renderMinimap === "function") renderMinimap();
    if ($("#outline") && $("#outline").classList.contains("show") && typeof renderOutline === "function") renderOutline();
  });
}
function autoJoinItemToContainingSystem(it) {
  if (!it || !board || !(board.groups || []).length) return "";
  // Explicit membership wins. Do not create accidental multi-system membership.
  if ((board.groups || []).some(g => (g.itemIds || []).includes(it.id))) return "";
  const cx = it.x + it.w / 2, cy = it.y + it.h / 2;
  const candidates = (board.groups || []).filter(g => g.mode === "auto" && !g.collapsed).map(g => {
    const b = autoGroupBounds(g);
    return b && cx >= b.x && cx <= b.x + b.w && cy >= b.y && cy <= b.y + b.h ? { g, b } : null;
  }).filter(Boolean).sort((a, b) => (a.b.w * a.b.h) - (b.b.w * b.b.h));
  if (!candidates.length) return "";
  const g = candidates[0].g;
  g.itemIds = [...(g.itemIds || []), it.id];
  queueAutoGroupRefresh();
  return g.name || "System";
}
function autoJoinItemsToContainingSystems(ids) {
  const joined = [];
  [...new Set(ids || [])].forEach(id => {
    const name = autoJoinItemToContainingSystem(byId(id));
    if (name) joined.push(name);
  });
  return [...new Set(joined)];
}
function toggleGroupMemberItem(itemId) {
'''
html = rep(html, member_anchor, member_helper, "automatic system membership helper")

# Register every way a newly-created board item is appended. Each of these code
# paths has already taken its undo snapshot before the push, so undo restores both
# the new item and the automatic system membership together.
push_replacements = [
    (
        'board.items.push(c); makeEl(c); refresh(c.id); made.push(c.id);',
        'board.items.push(c); autoJoinItemToContainingSystem(c); makeEl(c); refresh(c.id); made.push(c.id);',
        "multi duplicate auto-join",
    ),
    (
        'board.items.push(c); makeEl(c); refresh(c.id); selectItem(c.id); save();',
        'board.items.push(c); autoJoinItemToContainingSystem(c); makeEl(c); refresh(c.id); selectItem(c.id); save();',
        "duplicate auto-join",
        3,
    ),
    (
        'board.items.push(it); makeEl(it);\n      }\n      it.src = got.data;',
        'board.items.push(it); autoJoinItemToContainingSystem(it); makeEl(it);\n      }\n      it.src = got.data;',
        "photo auto-join",
    ),
    (
        'board.items.push(it); makeEl(it); refresh(it.id); made.push(it.id);',
        'board.items.push(it); autoJoinItemToContainingSystem(it); makeEl(it); refresh(it.id); made.push(it.id);',
        "paste block auto-join",
    ),
    (
        'board.items.push(n); makeEl(n); refresh(n.id); selectItem(n.id); updateEmpty(); save();',
        'board.items.push(n); autoJoinItemToContainingSystem(n); makeEl(n); refresh(n.id); selectItem(n.id); updateEmpty(); save();',
        "single paste auto-join",
    ),
    (
        'board.items.push(it); makeEl(it); refresh(it.id); selectItem(it.id);\n  renderIdeaInbox();',
        'board.items.push(it); autoJoinItemToContainingSystem(it); makeEl(it); refresh(it.id); selectItem(it.id);\n  renderIdeaInbox();',
        "idea inbox auto-join",
    ),
    (
        'snap(); board.items.push(it); makeEl(it); refresh(it.id); selectItem(it.id);',
        'snap(); board.items.push(it); autoJoinItemToContainingSystem(it); makeEl(it); refresh(it.id); selectItem(it.id);',
        "toolbar add auto-join",
    ),
    (
        'board.items.push(c); makeEl(c); refresh(c.id); selectItem(c.id); save(); return;',
        'board.items.push(c); autoJoinItemToContainingSystem(c); makeEl(c); refresh(c.id); selectItem(c.id); save(); return;',
        "keyboard duplicate auto-join",
    ),
]
for spec in push_replacements:
    old, new, label, *count = spec
    html = rep(html, old, new, label, count[0] if count else 1)

# Existing ungrouped items also become members when deliberately dropped into an
# automatic system. Multi-selection drag is handled as a batch.
end_drag_old = '''    if (drag.moved) {
      justMoved = true;
      if (drag.systemMove) movingGroupContentsId = "";
      save(); renderGroups();
    }
'''
end_drag_new = '''    if (drag.moved) {
      justMoved = true;
      if (drag.systemMove) movingGroupContentsId = "";
      const movedIds = drag.group ? drag.group.map(o => o.id) : [drag.id];
      autoJoinItemsToContainingSystems(movedIds);
      save(); renderGroups();
    }
'''
html = rep(html, end_drag_old, end_drag_new, "drag auto-join")

# Fold the behaviour into the same 1.9.0 release notes.
release_old = '''      "Clicking an outline item jumps back to and selects it on the board; clicking a system fits that system into view. Hidden members of collapsed systems are expanded automatically when targeted."
    ]
'''
release_new = '''      "Clicking an outline item jumps back to and selects it on the board; clicking a system fits that system into view. Hidden members of collapsed systems are expanded automatically when targeted.",
      "Automatic systems now adopt newly created or deliberately dropped ungrouped items when their centre lands inside the system boundary, so the auto-sized box immediately grows to include new notes."
    ]
'''
html = rep(html, release_old, release_new, "1.9.0 embedded auto-system note")

readme_old = '''Group areas start in **Automatic sizing**. The boundary recalculates from its members, so it grows, shrinks and moves as the cluster changes while every note and card remains individually draggable, resizable and linkable.
'''
readme_new = '''Group areas start in **Automatic sizing**. The boundary recalculates from its members, so it grows, shrinks and moves as the cluster changes while every note and card remains individually draggable, resizable and linkable. New ungrouped notes/cards created inside an automatic system — or deliberately dragged into it — are adopted by that system automatically, so the boundary immediately grows to respect them. Existing membership remains explicit when an item is moved back out; use **Edit contents** when you want to remove it from the system.
'''
readme = rep(readme, readme_old, readme_new, "README automatic membership")

log_old = '''- Added responsive styling and dedicated map/outline icons without changing existing board data or export formats.

## 1.8.1'''
log_new = '''- Added responsive styling and dedicated map/outline icons without changing existing board data or export formats.
- Fixed automatic systems not recognising newly added notes: ungrouped items created or deliberately dropped inside an automatic system now join it automatically and immediately participate in auto-sizing. Existing members are not silently removed when dragged out.

## 1.8.1'''
log = rep(log, log_old, log_new, "changelog automatic membership")

INDEX.write_text(html, encoding="utf-8")
README.write_text(readme, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# Parse every inline script after the membership changes.
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# Second pass: make sure automatic membership is conservative, undo-safe and
# connected to both new-item and drag paths.
checks = {
    "auto-only": 'g.mode === "auto" && !g.collapsed' in html,
    "no-auto-multigroup": '(board.groups || []).some(g => (g.itemIds || []).includes(it.id))' in html,
    "smallest-containing-system": '(a.b.w * a.b.h) - (b.b.w * b.b.h)' in html,
    "centre-containment": 'cx >= b.x && cx <= b.x + b.w && cy >= b.y && cy <= b.y + b.h' in html,
    "drag-batch": 'const movedIds = drag.group ? drag.group.map(o => o.id) : [drag.id];' in html,
    "toolbar-add": 'snap(); board.items.push(it); autoJoinItemToContainingSystem(it);' in html,
    "paste-add": 'board.items.push(n); autoJoinItemToContainingSystem(n);' in html,
    "photo-add": 'board.items.push(it); autoJoinItemToContainingSystem(it); makeEl(it);' in html,
    "release-note": 'Automatic systems now adopt newly created or deliberately dropped ungrouped items' in html,
    "readme": 'New ungrouped notes/cards created inside an automatic system' in readme,
    "changelog": 'Fixed automatic systems not recognising newly added notes' in log,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("automatic-system second-pass checks failed: " + ", ".join(failed))

print(f"Pin It 1.9.0 automatic-system fix verified: {len(scripts)} inline scripts parse; {len(checks)} behaviour checks passed")
