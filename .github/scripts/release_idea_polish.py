from pathlib import Path
import re
import subprocess
import tempfile

INDEX = Path("index.html")
CHANGELOG = Path("CHANGELOG.md")
html = INDEX.read_text(encoding="utf-8")
log = CHANGELOG.read_text(encoding="utf-8")


def rep(old, new, label):
    global html
    n = html.count(old)
    if n < 1:
        raise SystemExit(f"{label}: match not found")
    html = html.replace(old, new, 1)


rep("Version 1.5.0 · 14 September 2026, 22:01 UTC", "Version 1.5.1 · 14 September 2026, 22:45 UTC", "header")
rep('const VERSION = "1.5.0";', 'const VERSION = "1.5.1";', "VERSION")
rep('const BUILD = "14 September 2026, 22:01 UTC";', 'const BUILD = "14 September 2026, 22:45 UTC";', "BUILD")

release = '''  {
    version: "1.5.1", date: "14 September 2026, 22:45 UTC",
    summary: "A mobile polish pass makes the new idea workflow safer and easier to use on small screens.",
    items: [
      "Idea Inbox cards now allow normal vertical drawer scrolling while preserving deliberate drag-out placement gestures.",
      "Long relationship menus now scroll within the screen instead of extending beyond shorter mobile displays.",
      "Protected photos from being converted into text-only Idea Inbox entries.",
      "Restored Evidence tag terminology for the standalone tag item while keeping board tags as project-area labels.",
      "Fixed the final onboarding guidance so it appears on every board theme."
    ]
  },
'''
rep("const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

rep(
    '.idea-card{position:relative; margin:0 0 9px; padding:11px 10px 9px; border:1px solid var(--pan-line); border-radius:5px;\n  background:var(--pan-soft); box-shadow:0 3px 9px rgba(0,0,0,.12); touch-action:none; user-select:none; -webkit-user-select:none}',
    '.idea-card{position:relative; margin:0 0 9px; padding:11px 10px 9px; border:1px solid var(--pan-line); border-radius:5px;\n  background:var(--pan-soft); box-shadow:0 3px 9px rgba(0,0,0,.12); touch-action:pan-y; user-select:none; -webkit-user-select:none}',
    "Idea Inbox touch scrolling",
)

rep(
    '#ctx{position:fixed; z-index:50; background:linear-gradient(180deg,var(--sheet-2),var(--sheet)); border:1px solid var(--pan-line);\n  border-radius:var(--r); box-shadow:0 14px 34px var(--ui-drop); padding:5px; display:none; min-width:172px}',
    '#ctx{position:fixed; z-index:50; background:linear-gradient(180deg,var(--sheet-2),var(--sheet)); border:1px solid var(--pan-line);\n  border-radius:var(--r); box-shadow:0 14px 34px var(--ui-drop); padding:5px; display:none; min-width:172px;\n  max-height:calc(100vh - 16px); overflow-y:auto; overscroll-behavior:contain; -webkit-overflow-scrolling:touch}',
    "mobile relationship menu scrolling",
)

rep(
    'const TYPE_NAMES = { photo: "Photo", sticky: "Detail note", card: "Feature card", doc: "Report", list: "Implementation checklist", tag: "Area tag", marker: "Marker text" };',
    'const TYPE_NAMES = { photo: "Photo", sticky: "Detail note", card: "Feature card", doc: "Report", list: "Implementation checklist", tag: "Evidence tag", marker: "Marker text" };',
    "Evidence tag terminology",
)

rep(
    '<li class="ink"><svg><use href="#i-pen"/></svg><div><b>Keep capture loose</b>Not every thought needs a connection. If you cannot finish “this idea ___ that idea”, leave it unlinked for now.</div></li>',
    '<li><svg><use href="#i-pen"/></svg><div><b>Keep capture loose</b>Not every thought needs a connection. If you cannot finish “this idea ___ that idea”, leave it unlinked for now.</div></li>',
    "theme-independent onboarding guidance",
)

rep(
    '  try { card.setPointerCapture(e.pointerId); } catch (err) {}\n  e.preventDefault();\n});',
    '  try { card.setPointerCapture(e.pointerId); } catch (err) {}\n  if (e.pointerType === "mouse") e.preventDefault();\n});',
    "touch pointer scrolling",
)

rep(
    '    <button data-a="back">${ic("back")}Send to back</button>\n    <button data-a="inbox">${ic("sticky")}Move to Idea Inbox</button>\n    <hr>',
    '    <button data-a="back">${ic("back")}Send to back</button>\n    ${it.type === "photo" ? "" : `<button data-a="inbox">${ic("sticky")}Move to Idea Inbox</button>`}\n    <hr>',
    "hide photo inbox action",
)

rep(
    'function storeItemInInbox(id) {\n  const it = byId(id); if (!it) return;\n  snap();',
    'function storeItemInInbox(id) {\n  const it = byId(id); if (!it) return;\n  if (it.type === "photo") { toast("Photos stay on the board — the Idea Inbox stores text ideas"); return; }\n  snap();',
    "photo inbox data protection",
)

entry = '''## 1.5.1 — 14 September 2026, 22:45 UTC

- Idea Inbox cards now allow normal vertical drawer scrolling while preserving deliberate drag-out placement gestures.
- Long relationship menus now scroll within the screen instead of extending beyond shorter mobile displays.
- Protected photos from being converted into text-only Idea Inbox entries.
- Restored **Evidence tag** terminology for the standalone tag item while keeping board tags as project-area labels.
- Fixed the final onboarding guidance so it appears on Corkboard, Whiteboard and Blueprint themes alike.

'''
if "---\n\n" not in log:
    raise SystemExit("changelog insertion point missing")
log = log.replace("---\n\n", "---\n\n" + entry, 1)

INDEX.write_text(html, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

required = [
    'const VERSION = "1.5.1";',
    'touch-action:pan-y',
    'max-height:calc(100vh - 16px)',
    'tag: "Evidence tag"',
    'it.type === "photo" ? "" : `<button data-a="inbox"',
    'Photos stay on the board — the Idea Inbox stores text ideas',
    '<b>Keep capture loose</b>',
]
for token in required:
    if token not in html:
        raise SystemExit("verification failed: " + token)
if '<li class="ink"><svg><use href="#i-pen"/></svg><div><b>Keep capture loose</b>' in html:
    raise SystemExit("onboarding guidance is still theme-gated")
if "## 1.5.1 — 14 September 2026, 22:45 UTC" not in log:
    raise SystemExit("changelog mismatch")

scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)
print(f"Pin It 1.5.1 verified: {len(scripts)} inline scripts parse successfully")
