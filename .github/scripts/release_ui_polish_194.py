from pathlib import Path
import re
import subprocess
import tempfile

INDEX = Path("index.html")
CHANGELOG = Path("CHANGELOG.md")
html = INDEX.read_text(encoding="utf-8")
log = CHANGELOG.read_text(encoding="utf-8")


def rep(text, old, new, label, count=1):
    found = text.count(old)
    if found != count:
        raise SystemExit(f"{label}: expected {count} match(es), found {found}")
    return text.replace(old, new, count)

# Release metadata
html = rep(html, "Version 1.9.3 · 15 September 2026, 13:46 UTC", "Version 1.9.4 · 15 September 2026, 13:54 UTC", "header version")
html = rep(html, 'const VERSION = "1.9.3";', 'const VERSION = "1.9.4";', "VERSION")
html = rep(html, 'const BUILD = "15 September 2026, 13:46 UTC";', 'const BUILD = "15 September 2026, 13:54 UTC";', "BUILD")
release = '''  {
    version: "1.9.4", date: "15 September 2026, 13:54 UTC",
    summary: "A board presentation polish pass keeps the map out of the way on load, removes visible cork tiling and gives the desktop board label proper clearance.",
    items: [
      "Board Map now starts closed on every screen size and only opens when the user presses the map button.",
      "Removed the obvious 620px repeating seam from the cork surface by stretching the low-frequency texture layer across the viewport instead of tiling it.",
      "Added desktop spacing between the burger/boards button and the board-name card so its decorative tape no longer overlaps the menu control."
    ]
  },\n'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# Minimap should never auto-open on first load.
html = rep(
    html,
    'let minimapOpen = !matchMedia("(max-width:720px)").matches, minimapMetrics = null, minimapDragging = false;',
    'let minimapOpen = false, minimapMetrics = null, minimapDragging = false;',
    "minimap default"
)

# Keep the fine cork grain, but stop the large low-frequency SVG from visibly tiling.
html = rep(
    html,
    '  background-size:300px 300px, 620px 620px, 100% 100%, 100% 100%, 100% 100%;\n  background-blend-mode:multiply, soft-light, normal, normal, normal;',
    '  background-size:300px 300px, 100% 100%, 100% 100%, 100% 100%, 100% 100%;\n  background-repeat:repeat, no-repeat, no-repeat, no-repeat, no-repeat;\n  background-blend-mode:multiply, soft-light, normal, normal, normal;',
    "cork texture tiling"
)

# The case-file tape projects 10px left, so give it the same desktop clearance already used on mobile.
html = rep(
    html,
    '#caseplate{\n  pointer-events:auto; position:relative; padding:7px 16px 9px; min-width:0;',
    '#caseplate{\n  pointer-events:auto; position:relative; padding:7px 16px 9px; min-width:0; margin-left:10px;',
    "desktop caseplate spacing"
)

# Changelog
entry = '''---

## 1.9.4 — 15 September 2026, 13:54 UTC

- Changed **Board Map** so it starts closed on desktop as well as mobile; it now opens only when requested.
- Removed the visible large-scale cork texture tiling by making the low-frequency cork variation a single non-repeating viewport layer while retaining the fine surface grain.
- Added desktop clearance between the burger/boards button and the board-name case card so the decorative tape no longer visually clashes with the menu.

## 1.9.3 — 15 September 2026, 13:46 UTC'''
log = rep(log, '''---

## 1.9.3 — 15 September 2026, 13:46 UTC''', entry, "changelog")

INDEX.write_text(html, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# Pass 1: syntax check every inline script.
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"inline-{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# Pass 2: targeted regression checks.
checks = {
    "version": 'const VERSION = "1.9.4";' in html,
    "build": 'const BUILD = "15 September 2026, 13:54 UTC";' in html,
    "release": 'version: "1.9.4", date: "15 September 2026, 13:54 UTC"' in html,
    "changelog": "## 1.9.4 — 15 September 2026, 13:54 UTC" in log,
    "map-closed": 'let minimapOpen = false, minimapMetrics = null, minimapDragging = false;' in html,
    "no-old-map-default": '!matchMedia("(max-width:720px)").matches, minimapMetrics' not in html,
    "large-cork-not-tiled": 'background-size:300px 300px, 100% 100%, 100% 100%, 100% 100%, 100% 100%;' in html,
    "large-cork-no-repeat": 'background-repeat:repeat, no-repeat, no-repeat, no-repeat, no-repeat;' in html,
    "no-620-tile": 'background-size:300px 300px, 620px 620px' not in html,
    "desktop-case-clearance": '#caseplate{\n  pointer-events:auto; position:relative; padding:7px 16px 9px; min-width:0; margin-left:10px;' in html,
    "mobile-case-clearance-kept": '#caseplate{max-width:38vw; font-size:12.5px; padding:5px 10px 7px; margin-left:10px}' in html,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("UI polish checks failed: " + ", ".join(failed))

print(f"Pin It 1.9.4 verified: {len(scripts)} inline scripts parse; {len(checks)} targeted checks passed")
