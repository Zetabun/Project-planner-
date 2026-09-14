from pathlib import Path
import re
import subprocess
import tempfile

INDEX = Path("index.html")
CHANGELOG = Path("CHANGELOG.md")

html = INDEX.read_text(encoding="utf-8")
log = CHANGELOG.read_text(encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


html = replace_once(
    html,
    "Version 1.4.1 · 14 September 2026, 20:04 UTC",
    "Version 1.4.2 · 14 September 2026, 21:55 UTC",
    "header version",
)
html = replace_once(html, 'const VERSION = "1.4.1";', 'const VERSION = "1.4.2";', "VERSION")
html = replace_once(
    html,
    'const BUILD = "14 September 2026, 20:04 UTC";',
    'const BUILD = "14 September 2026, 21:55 UTC";',
    "BUILD",
)

release = '''  {
    version: "1.4.2", date: "14 September 2026, 21:55 UTC",
    summary: "A mobile interaction fix makes newly added notes and text immediately draggable.",
    items: [
      "Fixed newly added sticky notes, marker text and evidence tags sometimes refusing to move on the first drag in the mobile app.",
      "On mobile layouts, new text items now stay selected and draggable instead of immediately placing a full-item text editor over themselves.",
      "Text remains available from Edit on the mobile selection bar, while desktop keeps the existing instant quick-edit behaviour."
    ]
  },
'''
html = replace_once(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

old_add = '''  if (type === "photo") pickImage(it.id);
  else if (type === "sticky" || type === "marker" || type === "tag") setTimeout(() => startEdit(it.id, "text", true), 60);
}'''
new_add = '''  if (type === "photo") pickImage(it.id);
  else if (type === "sticky" || type === "marker" || type === "tag") {
    // On mobile, immediately opening a full-item textarea can swallow the first
    // drag gesture (especially in iOS standalone mode). Keep the new item selected
    // and draggable; Edit in the selection bar still opens the text editor.
    if (isNarrow()) toast("Added — drag to place, then tap Edit to write");
    else setTimeout(() => startEdit(it.id, "text", true), 60);
  }
}'''
html = replace_once(html, old_add, new_add, "mobile addItem interaction")

entry = '''## 1.4.2 — 14 September 2026, 21:55 UTC

- Fixed newly added sticky notes, marker text and evidence tags sometimes refusing to move on the first drag in the mobile app.
- On mobile/narrow layouts, new text items remain selected and immediately draggable instead of automatically opening the full-item inline editor over themselves.
- Text remains one tap away through **Edit** on the mobile selection bar; desktop keeps the existing instant quick-edit behaviour.

'''
log = replace_once(log, "---\n\n", "---\n\n" + entry, "changelog insertion")

INDEX.write_text(html, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# Pass 1: release metadata and behavior guard.
required_html = [
    'const VERSION = "1.4.2";',
    'const BUILD = "14 September 2026, 21:55 UTC";',
    'version: "1.4.2"',
    'if (isNarrow()) toast("Added — drag to place, then tap Edit to write")',
]
for token in required_html:
    if token not in html:
        raise SystemExit("verification failed, missing: " + token)
if "## 1.4.2 — 14 September 2026, 21:55 UTC" not in log:
    raise SystemExit("verification failed: changelog mismatch")

# Pass 2: every inline JavaScript block must parse independently.
scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.S | re.I)
if not scripts:
    raise SystemExit("verification failed: no inline scripts found")
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        js = Path(td) / f"script-{i}.js"
        js.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(js)], check=True)

print(f"Pin It 1.4.2 verified: {len(scripts)} inline script blocks parse successfully.")
