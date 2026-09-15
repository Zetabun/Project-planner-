from pathlib import Path
import re, subprocess, tempfile

INDEX = Path('index.html')
CHANGELOG = Path('CHANGELOG.md')
html = INDEX.read_text(encoding='utf-8')
log = CHANGELOG.read_text(encoding='utf-8')


def rep(text, old, new, label, count=1):
    n = text.count(old)
    if n != count:
        raise SystemExit(f'{label}: expected {count}, found {n}')
    return text.replace(old, new, count)


def sub(text, pattern, repl, label, count=1):
    out, n = re.subn(pattern, repl, text, count=count, flags=re.S)
    if n != count:
        raise SystemExit(f'{label}: expected {count}, found {n}')
    return out

# Release metadata
html = rep(html, 'Version 1.9.7 · 15 September 2026, 14:23 UTC', 'Version 1.9.8 · 15 September 2026, 14:43 UTC', 'header version')
html = rep(html, 'const VERSION = "1.9.7";', 'const VERSION = "1.9.8";', 'VERSION')
html = rep(html, 'const BUILD = "15 September 2026, 14:23 UTC";', 'const BUILD = "15 September 2026, 14:43 UTC";', 'BUILD')
release = '''  {\n    version: "1.9.8", date: "15 September 2026, 14:43 UTC",\n    summary: "A focused interaction fix keeps sticky notes within a sensible size and makes system-moving mode easy to exit.",\n    items: [\n      "Sticky/detail notes now have a sensible maximum size, preventing an accidental resize at low zoom from turning a note into a board-filling sheet.",\n      "Existing or imported oversized sticky notes are clamped back into the supported range during normalisation, so already-affected boards repair themselves on load.",\n      "Move system + contents now clears the temporary multi-selection after a completed move instead of leaving every member selected.",\n      "While system-moving mode is active, the system menu changes to Finish moving system so the mode can be cancelled explicitly before a drag, including on touch devices.",\n      "Tapping empty board space while system-moving mode is active now exits the mode cleanly."\n    ]\n  },\n'''
html = rep(html, 'const RELEASES = [\n', 'const RELEASES = [\n' + release, 'release entry')

# Sticky note size bounds. Keep other item types on their existing generous limits.
helper = '''\nfunction itemSizeLimits(type) {\n  if (type === "sticky") return { minW:110, minH:110, maxW:520, maxH:520 };\n  return { minW:90, minH:type === "tag" ? 34 : 70, maxW:1400, maxH:1400 };\n}\n'''
pat = r'(const DEFAULTS = \{.*?\n\};\n)'
html, n = re.subn(pat, lambda m: m.group(1) + helper, html, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'item size helper insert: expected 1, found {n}')

# Repair already-saved/imported malformed sticky sizes as boards are normalised.
old_norm = '''    ["w", "h", "x", "y"].forEach(k => { if (typeof i[k] !== "number") i[k] = DEFAULTS[i.type] ? DEFAULTS[i.type][k] || 0 : 0; });'''
new_norm = '''    ["w", "h", "x", "y"].forEach(k => { if (typeof i[k] !== "number") i[k] = DEFAULTS[i.type] ? DEFAULTS[i.type][k] || 0 : 0; });\n    const lim = itemSizeLimits(i.type);\n    i.w = Math.round(clamp(i.w, lim.minW, lim.maxW));\n    i.h = Math.round(clamp(i.h, lim.minH, lim.maxH));'''
html = rep(html, old_norm, new_norm, 'normalise size clamp')

# Use the same limits during live resize so the malformed state cannot be created again.
old_resize = '''    const min = it.type === "tag" ? 34 : 70;\n    it.w = Math.round(clamp(resize.w + (p.x - resize.sx), 90, 1400));\n    it.h = Math.round(clamp(resize.h + (p.y - resize.sy), min, 1400));'''
new_resize = '''    const lim = itemSizeLimits(it.type);\n    it.w = Math.round(clamp(resize.w + (p.x - resize.sx), lim.minW, lim.maxW));\n    it.h = Math.round(clamp(resize.h + (p.y - resize.sy), lim.minH, lim.maxH));'''
html = rep(html, old_resize, new_resize, 'live resize clamp')

# System menu should show when the move mode is active and offer an explicit finish action.
old_state = '''  const membersEditing = editingGroupMembersId === id;\n  const state = `${g.collapsed ? "Collapsed · " : ""}${manual ? `Manual sizing${g.locked ? " · Locked" : editing ? " · Editing border" : ""}` : "Automatic sizing"}`;'''
new_state = '''  const membersEditing = editingGroupMembersId === id;\n  const moving = movingGroupContentsId === id;\n  const state = `${moving ? "Moving contents · " : ""}${g.collapsed ? "Collapsed · " : ""}${manual ? `Manual sizing${g.locked ? " · Locked" : editing ? " · Editing border" : ""}` : "Automatic sizing"}`;'''
html = rep(html, old_state, new_state, 'group moving state')

html = rep(
    html,
    '''    <button data-a="moveall"><svg><use href="#i-fit"/></svg>Move system + contents</button>''',
    '''    <button data-a="moveall"><svg><use href="#i-fit"/></svg>${moving ? "Finish moving system" : "Move system + contents"}</button>''',
    'moveall button')

old_moveall = '''    if (b.dataset.a === "moveall") {\n      if (g.collapsed) { snap(); g.collapsed = false; save(); }\n      editingGroupMembersId = ""; editingGroupId = ""; movingGroupContentsId = id;\n      setMulti((g.itemIds || []).filter(id => byId(id))); renderGroups();\n      toast("Drag any selected item to move the whole system. The boundary moves with it.", 4400);\n      return;\n    }'''
new_moveall = '''    if (b.dataset.a === "moveall") {\n      if (moving) {\n        movingGroupContentsId = ""; clearMulti(false); renderGroups();\n        toast("Finished moving system");\n        return;\n      }\n      if (g.collapsed) { snap(); g.collapsed = false; save(); }\n      editingGroupMembersId = ""; editingGroupId = ""; movingGroupContentsId = id;\n      setMulti((g.itemIds || []).filter(id => byId(id))); renderGroups();\n      toast("Drag any selected item to move the whole system. Tap empty space or the system name to finish.", 4800);\n      return;\n    }'''
html = rep(html, old_moveall, new_moveall, 'moveall toggle')

# Empty-space taps should cancel the temporary system-move state as well as ordinary selection.
old_bg = '''  // background\n  if (linking) { cancelLink(); return; }\n  deselect();'''
new_bg = '''  // background\n  if (linking) { cancelLink(); return; }\n  if (movingGroupContentsId) { movingGroupContentsId = ""; renderGroups(); }\n  deselect();'''
html = rep(html, old_bg, new_bg, 'background system-move cancel')

# A completed system move is a complete action; clear its temporary multi-selection immediately.
old_end = '''      justMoved = true;\n      if (drag.systemMove) movingGroupContentsId = "";\n      const movedIds = drag.group ? drag.group.map(o => o.id) : [drag.id];'''
new_end = '''      justMoved = true;\n      if (drag.systemMove) { movingGroupContentsId = ""; clearMulti(false); }\n      const movedIds = drag.group ? drag.group.map(o => o.id) : [drag.id];'''
html = rep(html, old_end, new_end, 'clear selection after system move')

# Changelog
entry = '''---\n\n## 1.9.8 — 15 September 2026, 14:43 UTC\n\n- Added sensible sticky/detail-note resize limits so a low-zoom resize cannot accidentally create a board-filling sticky sheet.\n- Existing/imported oversized sticky notes are repaired automatically during board normalisation.\n- **Move system + contents** now clears its temporary multi-selection when the move finishes.\n- The active system menu now changes to **Finish moving system**, giving desktop and touch users an explicit way to cancel the move mode before dragging.\n- Tapping empty board space also exits system-moving mode cleanly.\n\n## 1.9.7 — 15 September 2026, 14:23 UTC'''
log = rep(log, '''---\n\n## 1.9.7 — 15 September 2026, 14:23 UTC''', entry, 'changelog')

INDEX.write_text(html, encoding='utf-8')
CHANGELOG.write_text(log, encoding='utf-8')

# Verification pass 1: every inline script must parse.
scripts = re.findall(r'<script(?:\\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f's{i}.js'
        p.write_text(script, encoding='utf-8')
        subprocess.run(['node', '--check', str(p)], check=True)

# Verification pass 2: explicit regression contracts for both reported bugs.
checks = {
    'version': 'const VERSION = "1.9.8";' in html,
    'build': 'const BUILD = "15 September 2026, 14:43 UTC";' in html,
    'release': 'version: "1.9.8", date: "15 September 2026, 14:43 UTC"' in html,
    'changelog': '## 1.9.8 — 15 September 2026, 14:43 UTC' in log,
    'sticky-limits-helper': 'if (type === "sticky") return { minW:110, minH:110, maxW:520, maxH:520 };' in html,
    'sticky-normalise-repair': 'i.w = Math.round(clamp(i.w, lim.minW, lim.maxW));' in html,
    'live-resize-limits': 'resize.w + (p.x - resize.sx), lim.minW, lim.maxW' in html,
    'move-toggle-label': '${moving ? "Finish moving system" : "Move system + contents"}' in html,
    'move-finish-branch': 'toast("Finished moving system")' in html,
    'background-cancel': 'if (movingGroupContentsId) { movingGroupContentsId = ""; renderGroups(); }' in html,
    'post-move-deselect': 'if (drag.systemMove) { movingGroupContentsId = ""; clearMulti(false); }' in html,
    'old-resize-gone': 'resize.w + (p.x - resize.sx), 90, 1400' not in html,
}
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise SystemExit('regression checks failed: ' + ', '.join(failed))

print(f'Pin It 1.9.8 verified: {len(scripts)} inline scripts parse; {len(checks)} bugfix checks passed')
