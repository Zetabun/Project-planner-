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


def sub(text, pattern, repl, label, count=1):
    out, n = re.subn(pattern, repl, text, count=count, flags=re.S)
    if n != count:
        raise SystemExit(f"{label}: expected {count} regex match(es), found {n}")
    return out


# ── release metadata ─────────────────────────────────────────────────────────
html = rep(html, "Version 1.9.1 · 15 September 2026, 11:56 UTC", "Version 1.9.2 · 15 September 2026, 13:34 UTC", "header version")
html = rep(html, 'const VERSION = "1.9.1";', 'const VERSION = "1.9.2";', "VERSION")
html = rep(html, 'const BUILD = "15 September 2026, 11:56 UTC";', 'const BUILD = "15 September 2026, 13:34 UTC";', "BUILD")
release = '''  {
    version: "1.9.2", date: "15 September 2026, 13:34 UTC",
    summary: "Stability hotfix for the Ideas drawer and browser storage pressure, especially on large imported boards.",
    items: [
      "Stopped the Ideas drawer rebuilding its full list every time it opens and limited the paper shuffle to the first visible ideas, removing the expensive animated shadow work.",
      "Fixed failed localStorage writes retaining a second multi-megabyte copy of the database in memory after browser storage fills.",
      "Autosave now backs off after a quota failure instead of repeatedly serialising and retrying the same oversized database until something is removed or compressed.",
      "Board imports are now transactional: Pin It tests the complete candidate database before committing the imported board, so a failed import cannot leave an oversized unsaved board in memory.",
      "Undo snapshots now de-duplicate embedded picture data instead of copying every image into every history entry, sharply reducing memory growth on image-heavy boards."
    ]
  },\n'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# ── Ideas drawer: avoid full-list rebuild and animate only a small visible set ─
old_idea_css = '''#idea-drawer.opening .idea-card{transform-origin:50% 90%;
  animation:idea-drawer-rummage .78s cubic-bezier(.22,.8,.24,1) both;
  animation-delay:calc((var(--idea-order,0) * 34ms) + 80ms); will-change:transform}'''
new_idea_css = '''#idea-drawer.opening .idea-card:nth-child(-n+8){transform-origin:50% 90%;
  animation:idea-drawer-rummage .48s cubic-bezier(.22,.8,.24,1) both;
  animation-delay:calc((var(--idea-order,0) * 22ms) + 28ms); will-change:transform}'''
html = rep(html, old_idea_css, new_idea_css, "Ideas animation selector")
old_keyframes = '''@keyframes idea-drawer-rummage{
  0%{transform:translate(var(--idea-x1,8px),var(--idea-y1,-5px)) rotate(var(--idea-r1,1.4deg));box-shadow:0 7px 14px rgba(0,0,0,.18)}
  34%{transform:translate(var(--idea-x2,-5px),3px) rotate(var(--idea-r2,-1deg))}
  62%{transform:translate(3px,-1px) rotate(.45deg)}
  82%{transform:translate(-1px,1px) rotate(-.18deg)}
  100%{transform:none;box-shadow:0 3px 9px rgba(0,0,0,.12)}
}
@media(prefers-reduced-motion:reduce){#idea-drawer.opening .idea-card{animation:none;will-change:auto}}'''
new_keyframes = '''@keyframes idea-drawer-rummage{
  0%{transform:translate(var(--idea-x1,8px),var(--idea-y1,-5px)) rotate(var(--idea-r1,1.4deg))}
  38%{transform:translate(var(--idea-x2,-5px),2px) rotate(var(--idea-r2,-1deg))}
  70%{transform:translate(2px,-1px) rotate(.3deg)}
  100%{transform:none}
}
@media(prefers-reduced-motion:reduce){#idea-drawer.opening .idea-card:nth-child(-n+8){animation:none;will-change:auto}}'''
html = rep(html, old_keyframes, new_keyframes, "Ideas keyframes")
old_open = '''  if (on) {
    renderIdeaInbox();
    if (!matchMedia("(prefers-reduced-motion: reduce)").matches && board.inbox.length) {
      requestAnimationFrame(() => requestAnimationFrame(() => ideaDrawer.classList.add("opening")));
      ideaDrawerMotionT = setTimeout(() => ideaDrawer.classList.remove("opening"), 1150);
    }
    setTimeout(() => { if (!isNarrow()) ideaInput.focus(); }, 80);'''
new_open = '''  if (on) {
    // The inbox is kept current when its data changes; opening it should not rebuild every card.
    if (!matchMedia("(prefers-reduced-motion: reduce)").matches && board.inbox.length) {
      requestAnimationFrame(() => ideaDrawer.classList.add("opening"));
      ideaDrawerMotionT = setTimeout(() => ideaDrawer.classList.remove("opening"), 620);
    }
    setTimeout(() => { if (!isNarrow()) ideaInput.focus(); }, 80);'''
html = rep(html, old_open, new_open, "Ideas drawer open path")

# ── localStorage: do not retain a giant failed write in the memory fallback ──
old_store = '''/* ── storage: localStorage with a memory fallback so it never hard-fails ── */
const store = (() => {
  let ok = true, mem = {};
  try { localStorage.setItem("__t", "1"); localStorage.removeItem("__t"); } catch (e) { ok = false; }
  return {
    persistent: ok,
    get(k) { try { return ok ? localStorage.getItem(k) : mem[k] ?? null; } catch (e) { return mem[k] ?? null; } },
    set(k, v) {
      if (!ok) { mem[k] = v; return true; }
      try { localStorage.setItem(k, v); return true; }
      catch (e) { mem[k] = v; return false; }
    }
  };
})();'''
new_store = '''/* ── storage: localStorage with a memory fallback only when persistence is unavailable at startup ── */
const store = (() => {
  let ok = true, mem = {};
  try { localStorage.setItem("__t", "1"); localStorage.removeItem("__t"); } catch (e) { ok = false; }
  return {
    persistent: ok,
    get(k) { try { return ok ? localStorage.getItem(k) : mem[k] ?? null; } catch (e) { return mem[k] ?? null; } },
    set(k, v) {
      if (!ok) { mem[k] = v; return true; }
      try { localStorage.setItem(k, v); return true; }
      catch (e) {
        // A quota failure must not keep another multi-megabyte copy alive in RAM.
        return false;
      }
    }
  };
})();'''
html = rep(html, old_store, new_store, "storage fallback")

# ── undo history: store picture payload once, reference it from snapshots ─────
undo_pattern = r'''function snap\(\) \{\n  history\.push\(JSON\.stringify\(\{ items: board\.items, links: board\.links, ink: board\.ink, inbox: board\.inbox, groups: board\.groups \}\)\);\n  if \(history\.length > 60\) history\.shift\(\);\n  future\.length = 0; updateUndo\(\);\n\}\nfunction applySnap\(s\) \{\n  const d = JSON\.parse\(s\); board\.items = d\.items; board\.links = d\.links; board\.ink = d\.ink \|\| \[\]; board\.inbox = d\.inbox \|\| \[\]; board\.groups = d\.groups \|\| \[\];\n  sel = null; renderAll\(\); closePanel\("inspect"\); save\(\);\n\}\nfunction undo\(\) \{\n  if \(!history\.length\) return;\n  future\.push\(JSON\.stringify\(\{ items: board\.items, links: board\.links, ink: board\.ink, inbox: board\.inbox, groups: board\.groups \}\)\);\n  applySnap\(history\.pop\(\)\); updateUndo\(\);\n\}\nfunction redo\(\) \{\n  if \(!future\.length\) return;\n  history\.push\(JSON\.stringify\(\{ items: board\.items, links: board\.links, ink: board\.ink, inbox: board\.inbox, groups: board\.groups \}\)\);\n  applySnap\(future\.pop\(\)\); updateUndo\(\);\n\}'''
undo_new = r'''const undoMediaByValue = new Map(), undoMediaByKey = new Map();
let undoMediaSeq = 0;
function clearUndoMedia() { undoMediaByValue.clear(); undoMediaByKey.clear(); undoMediaSeq = 0; }
function snapshotState() {
  const items = board.items.map(it => {
    if (!it.src || typeof it.src !== "string") return it;
    let key = undoMediaByValue.get(it.src);
    if (!key) {
      key = "m" + (++undoMediaSeq);
      undoMediaByValue.set(it.src, key);
      undoMediaByKey.set(key, it.src);
    }
    const copy = Object.assign({}, it, { src: null, _undoSrc: key });
    return copy;
  });
  return JSON.stringify({ items, links: board.links, ink: board.ink, inbox: board.inbox, groups: board.groups });
}
function inflateSnapshot(s) {
  const d = JSON.parse(s);
  d.items = (d.items || []).map(it => {
    if (!it || !it._undoSrc) return it;
    const copy = Object.assign({}, it, { src: undoMediaByKey.get(it._undoSrc) || "" });
    delete copy._undoSrc;
    return copy;
  });
  return d;
}
function snap() {
  history.push(snapshotState());
  if (history.length > 40) history.shift();
  future.length = 0; updateUndo();
}
function applySnap(s) {
  const d = inflateSnapshot(s); board.items = d.items; board.links = d.links; board.ink = d.ink || []; board.inbox = d.inbox || []; board.groups = d.groups || [];
  sel = null; renderAll(); closePanel("inspect"); save();
}
function undo() {
  if (!history.length) return;
  future.push(snapshotState());
  if (future.length > 40) future.shift();
  applySnap(history.pop()); updateUndo();
}
function redo() {
  if (!future.length) return;
  history.push(snapshotState());
  if (history.length > 40) history.shift();
  applySnap(future.pop()); updateUndo();
}'''
html = sub(html, undo_pattern, undo_new, "undo snapshot memory")
html = rep(html,
    'board = normalise(b); DB.current = id; history = []; future = []; updateUndo();',
    'board = normalise(b); DB.current = id; history = []; future = []; clearUndoMedia(); updateUndo();',
    "clear undo media on board switch")

# ── autosave: stop retrying expensive failed writes until space is freed ─────
old_save = '''let saveT = null;
function save(now) {
  if (!board) return;
  board.updated = Date.now();
  board.view = { x: view.x, y: view.y, s: view.s, w: view.w, h: view.h };
  clearTimeout(saveT);
  renderTimeline();
  const write = () => {
    const okw = store.set(KEY, JSON.stringify(DB));
    if (!okw) toast("Storage is full — try “Shrink the pictures” in the boards drawer, or export and remove a few.", 5200);
    else if (!store.persistent) flashSaved("not saved — private mode");
    else flashSaved("saved");
  };
  now ? write() : saveT = setTimeout(write, 450);
}'''
new_save = '''let saveT = null;
let storageWriteBlocked = false;
function allowStorageRetry() { storageWriteBlocked = false; }
function save(now) {
  if (!board) return;
  board.updated = Date.now();
  board.view = { x: view.x, y: view.y, s: view.s, w: view.w, h: view.h };
  clearTimeout(saveT);
  renderTimeline();
  const write = () => {
    if (storageWriteBlocked) { flashSaved("not saved — storage full"); return; }
    let payload;
    try { payload = JSON.stringify(DB); }
    catch (e) { flashSaved("not saved"); return; }
    const okw = store.set(KEY, payload);
    payload = null;
    if (!okw) {
      storageWriteBlocked = true;
      toast("Storage is full — saving is paused until you remove something or shrink pictures.", 5200);
      flashSaved("not saved — storage full");
    }
    else if (!store.persistent) flashSaved("not saved — private mode");
    else flashSaved("saved");
  };
  now ? write() : saveT = setTimeout(write, 450);
}'''
html = rep(html, old_save, new_save, "autosave quota backoff")

# Re-enable one save attempt only after operations that can genuinely free storage.
html = rep(html, '''function shrinkAll() {
  const pics = board.items.filter(i => i.src);
  if (!pics.length) { toast("No pictures on this board"); return; }''', '''function shrinkAll() {
  const pics = board.items.filter(i => i.src);
  if (!pics.length) { toast("No pictures on this board"); return; }
  allowStorageRetry();''', "shrink retry")
html = rep(html, '''function removeItem(id) {
  if (linking && linking.from === id) cancelLink();
  snap();''', '''function removeItem(id) {
  if (linking && linking.from === id) cancelLink();
  snap();
  allowStorageRetry();''', "single delete retry")
html = rep(html, '''function removeMany(ids) {
  if (linking && ids.includes(linking.from)) cancelLink();
  snap();''', '''function removeMany(ids) {
  if (linking && ids.includes(linking.from)) cancelLink();
  snap();
  allowStorageRetry();''', "multi delete retry")
html = rep(html, '''      DB.boards = DB.boards.filter(k => k.id !== id);
      if (board.id === id) switchBoard(DB.boards[0].id);''', '''      allowStorageRetry();
      DB.boards = DB.boards.filter(k => k.id !== id);
      if (board.id === id) switchBoard(DB.boards[0].id);''', "board delete retry")

# ── transactional imports: persist candidate first, mutate live DB second ─────
import_pattern = r'''\$\("#jsonpick"\)\.addEventListener\("change", e => \{\n  const f = e\.target\.files\[0\]; if \(!f\) return;\n  const fr = new FileReader\(\);\n  fr\.onload = \(\) => \{\n    try \{\n      const d = JSON\.parse\(fr\.result\);\n      const incoming = d\.board \? \[d\.board\] : \(d\.boards \|\| \[\]\);\n      if \(!incoming\.length\) throw 0;\n      incoming\.forEach\(b => \{\n        b\.id = uid\(\); b\.name = b\.name \|\| "Imported board";\n        b\.no = "NO\. " \+ String\(DB\.boards\.length \+ 1\)\.padStart\(3, "0"\);\n        b\.updated = Date\.now\(\);\n        DB\.boards\.push\(normalise\(b\)\);\n      \}\);\n      save\(true\); renderCases\(\); toast\(incoming\.length \+ " board" \+ \(incoming\.length > 1 \? "s" : ""\) \+ " imported"\);\n    \} catch \(err\) \{ toast\("That file isn't a Pin It board"\); \}\n  \};\n  fr\.readAsText\(f\);\n\}\);'''
import_new = r'''$("#jsonpick").addEventListener("change", e => {
  const f = e.target.files[0]; if (!f) return;
  const fr = new FileReader();
  fr.onload = () => {
    try {
      const d = JSON.parse(fr.result);
      const incoming = d.board ? [d.board] : (d.boards || []);
      if (!incoming.length) throw 0;
      const staged = incoming.map((raw, ix) => {
        const b = normalise(JSON.parse(JSON.stringify(raw)));
        b.id = uid(); b.name = b.name || "Imported board";
        b.no = "NO. " + String(DB.boards.length + ix + 1).padStart(3, "0");
        b.updated = Date.now();
        return b;
      });
      const candidate = Object.assign({}, DB, { boards: DB.boards.concat(staged) });
      let payload = JSON.stringify(candidate);
      if (payload.length > QUOTA * .96) {
        payload = null;
        toast("Import cancelled — it would exceed this browser's safe storage budget. Shrink pictures or remove a board first.", 6200);
        return;
      }
      if (!store.set(KEY, payload)) {
        payload = null;
        toast("Import cancelled — the browser could not store it. Your existing boards were left unchanged.", 6200);
        return;
      }
      payload = null;
      DB.boards.push(...staged);
      storageWriteBlocked = false;
      if (!store.persistent) flashSaved("not saved — private mode"); else flashSaved("saved");
      renderCases(); renderMeter();
      toast(staged.length + " board" + (staged.length > 1 ? "s" : "") + " imported");
    } catch (err) { toast("That file isn't a Pin It board"); }
  };
  fr.readAsText(f);
});'''
html = sub(html, import_pattern, import_new, "transactional import")

# ── changelog ────────────────────────────────────────────────────────────────
entry = '''---

## 1.9.2 — 15 September 2026, 13:34 UTC

- Fixed the desktop **Ideas** drawer doing unnecessary work on every open: it no longer rebuilds the full idea list just to display it.
- Kept the physical drawer feel while limiting the shuffle to the first eight visible ideas, shortening it, and removing animated box-shadow work that caused expensive repaints.
- Fixed failed `localStorage` writes retaining a second copy of the full database in RAM after quota exhaustion.
- Autosave now stops repeatedly serialising/retrying an oversized database after the first quota failure; deleting items/boards or shrinking pictures enables a clean retry.
- Imports are now transactional: the full candidate database is checked and persisted before the live board list is changed, so a too-large import is cancelled without leaving unsaved data resident in memory.
- Reworked undo history so embedded image data is stored once and referenced by snapshots rather than copied into every undo entry; history remains capped and is cleared between boards.

## 1.9.1 — 15 September 2026, 11:56 UTC'''
log = rep(log, '''---

## 1.9.1 — 15 September 2026, 11:56 UTC''', entry, "changelog")

INDEX.write_text(html, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# ── verification pass 1: all inline JS parses ────────────────────────────────
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"s{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# ── verification pass 2: regression/stability contracts ─────────────────────
checks = {
    "version": 'const VERSION = "1.9.2";' in html,
    "build": 'const BUILD = "15 September 2026, 13:34 UTC";' in html,
    "release": 'version: "1.9.2", date: "15 September 2026, 13:34 UTC"' in html,
    "changelog": "## 1.9.2 — 15 September 2026, 13:34 UTC" in log,
    "no-quota-memory-copy": 'catch (e) { mem[k] = v; return false; }' not in html,
    "quota-backoff": 'if (storageWriteBlocked) { flashSaved("not saved — storage full"); return; }' in html,
    "delete-retry": html.count('allowStorageRetry();') >= 4,
    "transaction-before-commit": html.find('if (!store.set(KEY, payload))') < html.find('DB.boards.push(...staged);'),
    "import-no-save-repeat": 'DB.boards.push(normalise(b));' not in html,
    "undo-media-dedupe": 'undoMediaByValue' in html and '_undoSrc' in html and 'snapshotState()' in html,
    "undo-cap": 'if (history.length > 40) history.shift();' in html,
    "drawer-no-rerender-on-open": 'if (on) {\n    renderIdeaInbox();' not in html,
    "drawer-eight-cards": '#idea-drawer.opening .idea-card:nth-child(-n+8)' in html,
    "drawer-no-shadow-animation": '0%{transform:translate(var(--idea-x1,8px),var(--idea-y1,-5px)) rotate(var(--idea-r1,1.4deg));box-shadow' not in html,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("stability checks failed: " + ", ".join(failed))

print(f"Pin It 1.9.2 verified: {len(scripts)} inline scripts parse; {len(checks)} stability checks passed")
