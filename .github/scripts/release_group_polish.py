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


# Release metadata.
html = rep(html, "Version 1.6.0 · 14 September 2026, 23:15 UTC", "Version 1.6.1 · 14 September 2026, 23:38 UTC", "header version")
html = rep(html, 'const VERSION = "1.6.0";', 'const VERSION = "1.6.1";', "VERSION")
html = rep(html, 'const BUILD = "14 September 2026, 23:15 UTC";', 'const BUILD = "14 September 2026, 23:38 UTC";', "BUILD")
release = '''  {
    version: "1.6.1", date: "14 September 2026, 23:38 UTC",
    summary: "Group labels get clearer breathing room and the Blueprint drafting grid now follows the board as it pans and zooms.",
    items: [
      "Reserved extra space beneath group/system labels so the first card or note no longer crowds the heading.",
      "Made the Blueprint minor and major grid scale proportionally with board zoom instead of staying fixed to the screen.",
      "Anchored the Blueprint grid to the board pan position so the drafting surface feels like part of the workspace rather than a screen overlay."
    ]
  },
'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# Give group labels a little title band above the nearest item.
old_group = '''function groupBounds(g) {
  const members = (g.itemIds || []).map(byId).filter(Boolean);
  if (members.length < 2) return null;
  const pad = clamp(+g.pad || 42, 28, 120);
  const x1 = Math.min(...members.map(i => i.x)) - pad;
  const y1 = Math.min(...members.map(i => i.y)) - pad;
  const x2 = Math.max(...members.map(i => i.x + i.w)) + pad;
  const y2 = Math.max(...members.map(i => i.y + i.h)) + pad;
  return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
}
'''
new_group = '''function groupBounds(g) {
  const members = (g.itemIds || []).map(byId).filter(Boolean);
  if (members.length < 2) return null;
  const pad = clamp(+g.pad || 42, 28, 120);
  const labelGap = 18; // reserved title band so the group name never crowds the top item
  const x1 = Math.min(...members.map(i => i.x)) - pad;
  const y1 = Math.min(...members.map(i => i.y)) - pad - labelGap;
  const x2 = Math.max(...members.map(i => i.x + i.w)) + pad;
  const y2 = Math.max(...members.map(i => i.y + i.h)) + pad;
  return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
}
'''
html = rep(html, old_group, new_group, "group label spacing")

# Make the Blueprint grid use zoom/pan-aware CSS variables. Decorative gradients remain screen-sized.
old_grid = '''  background-size:20px 20px, 20px 20px, 100px 100px, 100px 100px, 100% 100%, 100% 100%, 100% 100%;
  background-position:0 0, 0 0, -1px -1px, -1px -1px, 0 0, 0 0, 0 0;
'''
new_grid = '''  background-size:var(--bp-minor,20px) var(--bp-minor,20px), var(--bp-minor,20px) var(--bp-minor,20px),
    var(--bp-major,100px) var(--bp-major,100px), var(--bp-major,100px) var(--bp-major,100px), 100% 100%, 100% 100%, 100% 100%;
  background-position:var(--bp-grid-x,0px) var(--bp-grid-y,0px), var(--bp-grid-x,0px) var(--bp-grid-y,0px),
    var(--bp-grid-x,0px) var(--bp-grid-y,0px), var(--bp-grid-x,0px) var(--bp-grid-y,0px), 0 0, 0 0, 0 0;
'''
html = rep(html, old_grid, new_grid, "blueprint zoom-aware grid CSS")

old_view = '''function applyView() {
  world.style.transform = `translate(${view.x}px,${view.y}px) scale(${view.s})`;
  $("#zoomlvl").textContent = Math.round(view.s * 100) + "%";
  const r = viewport.getBoundingClientRect();
  view.w = Math.round(r.width); view.h = Math.round(r.height);
}
'''
new_view = '''function syncBlueprintBackdrop() {
  const s = Math.max(.01, view.s || 1);
  viewport.style.setProperty("--bp-minor", (20 * s) + "px");
  viewport.style.setProperty("--bp-major", (100 * s) + "px");
  viewport.style.setProperty("--bp-grid-x", (view.x || 0) + "px");
  viewport.style.setProperty("--bp-grid-y", (view.y || 0) + "px");
}
function applyView() {
  world.style.transform = `translate(${view.x}px,${view.y}px) scale(${view.s})`;
  syncBlueprintBackdrop();
  $("#zoomlvl").textContent = Math.round(view.s * 100) + "%";
  const r = viewport.getBoundingClientRect();
  view.w = Math.round(r.width); view.h = Math.round(r.height);
}
'''
html = rep(html, old_view, new_view, "blueprint backdrop sync")

old_theme = '''  const tf = $("#tagstylefield");
  if (tf) tf.style.display = (board && board.tags && board.tags.length) ? "" : "none";
}
'''
new_theme = '''  const tf = $("#tagstylefield");
  if (tf) tf.style.display = (board && board.tags && board.tags.length) ? "" : "none";
  syncBlueprintBackdrop();
}
'''
html = rep(html, old_theme, new_theme, "theme backdrop sync")

# Documentation.
readme = rep(
    readme,
    "**Blueprint** — a navy drafting surface with a fine technical grid and blue drafting sheets throughout: sticky notes, index cards, reports, checklists, photo frames and evidence tags. White marker-style notes and headings, precise borders, typed report text and metal pins with coloured rims give it a workshop-plan feel. Sticky notes retain six distinct colour accents and folded corners. Titles, dates, stamps, editing fields, completion indicators and the mobile tool rail all match. Connections are straight drafting lines, with brighter ink colours for legibility.",
    "**Blueprint** — a navy drafting surface with a fine technical grid and blue drafting sheets throughout: sticky notes, index cards, reports, checklists, photo frames and evidence tags. White marker-style notes and headings, precise borders, typed report text and metal pins with coloured rims give it a workshop-plan feel. Sticky notes retain six distinct colour accents and folded corners. Titles, dates, stamps, editing fields, completion indicators and the mobile tool rail all match. Connections are straight drafting lines, with brighter ink colours for legibility. The technical grid is anchored to the board itself, so it pans and scales naturally with zoom.",
    "README blueprint grid note",
)
readme = rep(
    readme,
    "The area is deliberately not another rigid container: every note and card remains individually draggable, resizable and linkable. The boundary recalculates from its members, so it grows, shrinks and moves as the cluster changes. Tap the group label to select all of its contents, rename it, or remove only the boundary while leaving the work untouched.",
    "The area is deliberately not another rigid container: every note and card remains individually draggable, resizable and linkable. The boundary recalculates from its members, so it grows, shrinks and moves as the cluster changes. A small title band is reserved above the nearest item so the group name stays visually separate from its contents. Tap the group label to select all of its contents, rename it, or remove only the boundary while leaving the work untouched.",
    "README group spacing note",
)

entry = '''## 1.6.1 — 14 September 2026, 23:38 UTC

- Added extra breathing room between a group/system label and the nearest card or note.
- Blueprint minor and major grid lines now scale proportionally as the board zooms.
- Blueprint grid origin now follows board panning, keeping the drafting grid visually attached to the workspace rather than the screen.

'''
log = rep(log, "---\n\n", "---\n\n" + entry, "changelog insertion")

INDEX.write_text(html, encoding="utf-8")
README.write_text(readme, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# First pass: structural assertions.
required = [
    'const VERSION = "1.6.1";',
    'const BUILD = "14 September 2026, 23:38 UTC";',
    'const labelGap = 18;',
    'var(--bp-minor,20px)',
    'var(--bp-major,100px)',
    'function syncBlueprintBackdrop()',
    'viewport.style.setProperty("--bp-grid-x"',
    'syncBlueprintBackdrop();',
]
for token in required:
    if token not in html:
        raise SystemExit("verification failed: " + token)
if 'background-size:20px 20px, 20px 20px, 100px 100px, 100px 100px' in html:
    raise SystemExit("old fixed Blueprint grid sizing is still present")
if "## 1.6.1 — 14 September 2026, 23:38 UTC" not in log:
    raise SystemExit("changelog mismatch")
if "grid is anchored to the board itself" not in readme:
    raise SystemExit("README Blueprint note missing")

# Parse every inline script independently, as the app is a single-file build.
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

print(f"Pin It 1.6.1 verified: {len(scripts)} inline scripts parse successfully")
