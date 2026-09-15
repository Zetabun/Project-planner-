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


# Release bookkeeping.
html = rep(html,
    "Version 1.9.0 · 15 September 2026, 11:31 UTC",
    "Version 1.9.1 · 15 September 2026, 11:56 UTC",
    "header version")
html = rep(html, 'const VERSION = "1.9.0";', 'const VERSION = "1.9.1";', "VERSION")
html = rep(html,
    'const BUILD = "15 September 2026, 11:31 UTC";',
    'const BUILD = "15 September 2026, 11:56 UTC";',
    "BUILD")
release = '''  {
    version: "1.9.1", date: "15 September 2026, 11:56 UTC",
    summary: "Polishes the mobile Idea Inbox and gives stored ideas a physical drawer-opening shuffle.",
    items: [
      "Moved the Ideas tray button upward on mobile and made its position responsive to short viewport heights so it stays clear of the expanded zoom/navigation rail.",
      "When the Idea Inbox opens, stored ideas now shift, wobble and settle with a short staggered paper-like animation, while reduced-motion preferences remain respected."
    ]
  },\n'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# Give idea cards a brief physical shuffle when the drawer is opened. The final
# state is unchanged, so the list remains easy to read and interact with.
card_anchor = '''.idea-card{position:relative; margin:0 0 9px; padding:11px 10px 9px; border:1px solid var(--pan-line); border-radius:5px;
  background:var(--pan-soft); box-shadow:0 3px 9px rgba(0,0,0,.12); touch-action:pan-y; user-select:none; -webkit-user-select:none}
.idea-card:active{background:var(--pan-soft2)}
'''
card_css = card_anchor + '''#idea-drawer.opening .idea-card{transform-origin:50% 90%;
  animation:idea-drawer-rummage .78s cubic-bezier(.22,.8,.24,1) both;
  animation-delay:calc((var(--idea-order,0) * 34ms) + 80ms); will-change:transform}
.idea-card:nth-child(4n+1){--idea-order:0;--idea-x1:9px;--idea-y1:-5px;--idea-r1:1.7deg;--idea-x2:-5px;--idea-r2:-1.1deg}
.idea-card:nth-child(4n+2){--idea-order:1;--idea-x1:-8px;--idea-y1:-3px;--idea-r1:-1.5deg;--idea-x2:5px;--idea-r2:.9deg}
.idea-card:nth-child(4n+3){--idea-order:2;--idea-x1:6px;--idea-y1:-7px;--idea-r1:1.2deg;--idea-x2:-4px;--idea-r2:-.8deg}
.idea-card:nth-child(4n){--idea-order:3;--idea-x1:-6px;--idea-y1:-4px;--idea-r1:-1.1deg;--idea-x2:4px;--idea-r2:.7deg}
@keyframes idea-drawer-rummage{
  0%{transform:translate(var(--idea-x1,8px),var(--idea-y1,-5px)) rotate(var(--idea-r1,1.4deg));box-shadow:0 7px 14px rgba(0,0,0,.18)}
  34%{transform:translate(var(--idea-x2,-5px),3px) rotate(var(--idea-r2,-1deg))}
  62%{transform:translate(3px,-1px) rotate(.45deg)}
  82%{transform:translate(-1px,1px) rotate(-.18deg)}
  100%{transform:none;box-shadow:0 3px 9px rgba(0,0,0,.12)}
}
@media(prefers-reduced-motion:reduce){#idea-drawer.opening .idea-card{animation:none;will-change:auto}}
'''
html = rep(html, card_anchor, card_css, "idea card opening animation")

# Move the mobile tray control clear of the now-taller navigation/zoom rail. The
# dynamic viewport expression gives extra clearance on shorter phone viewports.
mobile_old = '''@media(max-width:720px){
  #idea-tab{right:6px; top:50%; width:45px; min-height:61px}
  #idea-drawer{top:calc(var(--safe-t) + 68px); bottom:calc(var(--safe-b) + 72px); width:min(86vw,330px)}
'''
mobile_new = '''@media(max-width:720px){
  #idea-tab{right:6px; top:44%; width:45px; min-height:61px}
  @supports(height:100dvh){#idea-tab{top:min(44%, max(calc(var(--safe-t) + 82px), calc(100dvh - 376px - var(--safe-b))))}}
  #idea-drawer{top:calc(var(--safe-t) + 68px); bottom:calc(var(--safe-b) + 72px); width:min(86vw,330px)}
'''
html = rep(html, mobile_old, mobile_new, "mobile idea tray position")

# Replay the movement every time the tray is opened, after the current ideas have
# been rendered. Closing cancels the class/timer so reopening always feels fresh.
js_old = '''const ideaDrawer = $("#idea-drawer"), ideaList = $("#idea-list"), ideaInput = $("#idea-input");
function ideaDrawerOpen() { return ideaDrawer.classList.contains("show"); }
function toggleIdeaDrawer(force) {
  const on = force === undefined ? !ideaDrawerOpen() : !!force;
  ideaDrawer.classList.toggle("show", on);
  ideaDrawer.setAttribute("aria-hidden", on ? "false" : "true");
  $("#idea-tab").setAttribute("aria-expanded", on ? "true" : "false");
  document.body.classList.toggle("ideas-open", on);
  if (on) { renderIdeaInbox(); setTimeout(() => { if (!isNarrow()) ideaInput.focus(); }, 80); }
}
'''
js_new = '''const ideaDrawer = $("#idea-drawer"), ideaList = $("#idea-list"), ideaInput = $("#idea-input");
let ideaDrawerMotionT = null;
function ideaDrawerOpen() { return ideaDrawer.classList.contains("show"); }
function toggleIdeaDrawer(force) {
  const on = force === undefined ? !ideaDrawerOpen() : !!force;
  ideaDrawer.classList.toggle("show", on);
  ideaDrawer.setAttribute("aria-hidden", on ? "false" : "true");
  $("#idea-tab").setAttribute("aria-expanded", on ? "true" : "false");
  document.body.classList.toggle("ideas-open", on);
  clearTimeout(ideaDrawerMotionT);
  ideaDrawer.classList.remove("opening");
  if (on) {
    renderIdeaInbox();
    if (!matchMedia("(prefers-reduced-motion: reduce)").matches && board.inbox.length) {
      requestAnimationFrame(() => requestAnimationFrame(() => ideaDrawer.classList.add("opening")));
      ideaDrawerMotionT = setTimeout(() => ideaDrawer.classList.remove("opening"), 1150);
    }
    setTimeout(() => { if (!isNarrow()) ideaInput.focus(); }, 80);
  }
}
'''
html = rep(html, js_old, js_new, "idea drawer opening motion")

# Changelog entry.
log_anchor = "---\n\n## 1.9.0 — 15 September 2026, 11:31 UTC"
log_entry = '''---

## 1.9.1 — 15 September 2026, 11:56 UTC

- Moved the **Ideas** tray button upward on mobile and made its position adapt to short viewport heights so it stays clear of the taller zoom/navigation rail.
- Added a short staggered physical shuffle when the Idea Inbox opens: stored ideas wobble, slide and settle like loose paper in a drawer that has just been opened.
- The movement does not change card positions or data, does not interfere with dragging, and is disabled when the device requests reduced motion.

## 1.9.0 — 15 September 2026, 11:31 UTC'''
log = rep(log, log_anchor, log_entry, "changelog entry")

INDEX.write_text(html, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# First verification pass: every inline script must still parse.
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# Second verification pass: release metadata and the two requested behaviours.
checks = {
    "version": 'const VERSION = "1.9.1";' in html,
    "build": 'const BUILD = "15 September 2026, 11:56 UTC";' in html,
    "release": 'version: "1.9.1", date: "15 September 2026, 11:56 UTC"' in html,
    "mobile-up": '#idea-tab{right:6px; top:44%; width:45px; min-height:61px}' in html,
    "short-height-clearance": 'calc(100dvh - 376px - var(--safe-b))' in html,
    "opening-class": 'ideaDrawer.classList.add("opening")' in html,
    "opening-cleanup": 'ideaDrawer.classList.remove("opening")' in html,
    "stagger": 'animation-delay:calc((var(--idea-order,0) * 34ms) + 80ms)' in html,
    "reduced-motion-css": '@media(prefers-reduced-motion:reduce)' in html,
    "reduced-motion-js": 'matchMedia("(prefers-reduced-motion: reduce)").matches' in html,
    "changelog": '## 1.9.1 — 15 September 2026, 11:56 UTC' in log,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("second-pass checks failed: " + ", ".join(failed))

print(f"Pin It 1.9.1 verified: {len(scripts)} inline scripts parse; {len(checks)} behaviour checks passed")
