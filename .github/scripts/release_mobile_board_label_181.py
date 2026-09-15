from pathlib import Path
import re
import subprocess
import tempfile

INDEX = Path("index.html")
CHANGELOG = Path("CHANGELOG.md")
html = INDEX.read_text(encoding="utf-8")
log = CHANGELOG.read_text(encoding="utf-8")


def rep(text, old, new, label, count=1):
    n = text.count(old)
    if n != count:
        raise SystemExit(f"{label}: expected {count} match(es), found {n}")
    return text.replace(old, new, count)


# Release metadata.
html = rep(
    html,
    "Version 1.8.0 · 15 September 2026, 10:49 UTC",
    "Version 1.8.1 · 15 September 2026, 11:21 UTC",
    "header version",
)
html = rep(html, 'const VERSION = "1.8.0";', 'const VERSION = "1.8.1";', "VERSION")
html = rep(
    html,
    'const BUILD = "15 September 2026, 10:49 UTC";',
    'const BUILD = "15 September 2026, 11:21 UTC";',
    "BUILD",
)
release = '''  {
    version: "1.8.1", date: "15 September 2026, 11:21 UTC",
    summary: "Polishes the mobile top bar so the board label sits cleanly clear of the boards menu.",
    items: [
      "Moved the board label 10px to the right on screens up to 720px, keeping its taped edge clear of the burger/boards button without changing desktop spacing."
    ]
  },\n'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# Mobile-only spacing: the case plate has decorative tape that extends 10px left.
# The existing flex gap is 6px, so a 10px plate margin leaves a clean 6px visual gap
# between that tape edge and the burger button while preserving the desktop layout.
mobile_old = '  #caseplate{max-width:38vw; font-size:12.5px; padding:5px 10px 7px}\n'
mobile_new = '  #caseplate{max-width:38vw; font-size:12.5px; padding:5px 10px 7px; margin-left:10px}\n'
html = rep(html, mobile_old, mobile_new, "mobile board-label spacing")

changelog_anchor = "---\n\n## 1.8.0 — 15 September 2026, 10:49 UTC"
changelog_entry = '''---

## 1.8.1 — 15 September 2026, 11:21 UTC

- Moved the board label 10px to the right on mobile/narrow screens so its decorative tape edge no longer crowds the burger/boards button.
- Desktop top-bar spacing is unchanged.

## 1.8.0 — 15 September 2026, 10:49 UTC'''
log = rep(log, changelog_anchor, changelog_entry, "changelog entry")

INDEX.write_text(html, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# Parse every inline script so a CSS-only fix cannot accidentally ship alongside
# malformed JavaScript after the release metadata edits.
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# Second pass: verify the requested change is mobile-only and release bookkeeping agrees.
desktop_match = re.search(r'(?ms)^#caseplate\{\n(.*?)^\}', html)
checks = {
    "mobile-spacing": mobile_new in html,
    "mobile-spacing-once": html.count(mobile_new) == 1,
    "desktop-caseplate-found": desktop_match is not None,
    "desktop-spacing-unchanged": desktop_match is not None and "margin-left" not in desktop_match.group(1),
    "version": 'const VERSION = "1.8.1";' in html,
    "build": 'const BUILD = "15 September 2026, 11:21 UTC";' in html,
    "release": 'version: "1.8.1", date: "15 September 2026, 11:21 UTC"' in html,
    "changelog": "## 1.8.1 — 15 September 2026, 11:21 UTC" in log,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("second-pass checks failed: " + ", ".join(failed))

print(f"Pin It 1.8.1 verified: {len(scripts)} inline scripts parse; {len(checks)} second-pass checks passed")
