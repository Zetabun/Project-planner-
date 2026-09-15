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
html = rep(html, "Version 1.9.2 · 15 September 2026, 13:34 UTC", "Version 1.9.3 · 15 September 2026, 13:46 UTC", "header version")
html = rep(html, 'const VERSION = "1.9.2";', 'const VERSION = "1.9.3";', "VERSION")
html = rep(html, 'const BUILD = "15 September 2026, 13:34 UTC";', 'const BUILD = "15 September 2026, 13:46 UTC";', "BUILD")
release = '''  {
    version: "1.9.3", date: "15 September 2026, 13:46 UTC",
    summary: "Moves board persistence to IndexedDB so normal projects and imports are no longer constrained by localStorage's small quota.",
    items: [
      "IndexedDB is now the primary board database, with automatic one-time migration from the old localStorage record and cleanup of that legacy copy after migration.",
      "Existing boards migrate automatically on first load; no re-import is required for boards that were already saved.",
      "Imports are written transactionally to IndexedDB before they are added to the live board list, so failed imports still leave existing work untouched.",
      "The storage meter now reports project data and browser storage estimates instead of treating 5 MB as the app's hard ceiling when IndexedDB is available.",
      "Photo compression keeps a conservative soft budget while allowing substantially larger projects than the old localStorage backend."
    ]
  },\n'''
html = rep(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# Replace localStorage-only storage layer with IndexedDB-first storage and automatic migration.
old_store = '''/* ── storage: localStorage with a memory fallback only when persistence is unavailable at startup ── */
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
})();
const KEY = "pinit.v1";'''
new_store = '''/* ── storage: IndexedDB first; localStorage is migration/fallback only ── */
const store = (() => {
  const DB_NAME = "pin-it-storage";
  const STORE_NAME = "kv";
  let mem = {}, openP = null;
  let localOK = true;
  let idbOK = typeof indexedDB !== "undefined";
  try { localStorage.setItem("__t", "1"); localStorage.removeItem("__t"); } catch (e) { localOK = false; }

  function openDB() {
    if (!idbOK) return Promise.reject(new Error("IndexedDB unavailable"));
    if (openP) return openP;
    openP = new Promise((resolve, reject) => {
      let req;
      try { req = indexedDB.open(DB_NAME, 1); }
      catch (e) { idbOK = false; reject(e); return; }
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) db.createObjectStore(STORE_NAME);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => { idbOK = false; openP = null; reject(req.error || new Error("IndexedDB open failed")); };
      req.onblocked = () => { openP = null; reject(new Error("IndexedDB open blocked")); };
    });
    return openP;
  }
  async function idbGet(k) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const req = tx.objectStore(STORE_NAME).get(k);
      req.onsuccess = () => resolve(req.result == null ? null : req.result);
      req.onerror = () => reject(req.error || new Error("IndexedDB read failed"));
      tx.onabort = () => reject(tx.error || new Error("IndexedDB read aborted"));
    });
  }
  async function idbSet(k, v) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).put(v, k);
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => reject(tx.error || new Error("IndexedDB write failed"));
      tx.onabort = () => reject(tx.error || new Error("IndexedDB write aborted"));
    });
  }
  function legacyGet(k) {
    if (!localOK) return mem[k] ?? null;
    try { return localStorage.getItem(k); } catch (e) { return mem[k] ?? null; }
  }
  function clearLegacy(k) {
    if (!localOK) return;
    try { localStorage.removeItem(k); } catch (e) {}
  }

  return {
    get persistent() { return idbOK || localOK; },
    get largeCapacity() { return idbOK; },
    async get(k) {
      if (idbOK) {
        try {
          const v = await idbGet(k);
          if (v != null) { clearLegacy(k); return v; }
          const legacy = legacyGet(k);
          if (legacy != null) {
            try { await idbSet(k, legacy); clearLegacy(k); } catch (e) {}
            return legacy;
          }
          return null;
        } catch (e) { idbOK = false; openP = null; }
      }
      return legacyGet(k);
    },
    async set(k, v) {
      if (idbOK) {
        try {
          await idbSet(k, v);
          clearLegacy(k);
          return true;
        } catch (e) { idbOK = false; openP = null; }
      }
      if (!localOK) { mem[k] = v; return false; }
      try { localStorage.setItem(k, v); return true; }
      catch (e) { return false; }
    }
  };
})();
const KEY = "pinit.v1";'''
html = rep(html, old_store, new_store, "storage backend")

# Make saving asynchronous and ordered. This prevents out-of-order IndexedDB writes.
old_save = '''let saveT = null;
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
new_save = '''let saveT = null;
let storageWriteBlocked = false;
let storageWriteP = Promise.resolve(true);
function allowStorageRetry() { storageWriteBlocked = false; }
function queueStorageWrite(payload) {
  storageWriteP = storageWriteP.catch(() => false).then(() => store.set(KEY, payload));
  return storageWriteP;
}
function save(now) {
  if (!board) return Promise.resolve(false);
  board.updated = Date.now();
  board.view = { x: view.x, y: view.y, s: view.s, w: view.w, h: view.h };
  clearTimeout(saveT);
  renderTimeline();
  const write = async () => {
    if (storageWriteBlocked) { flashSaved("not saved — storage unavailable"); return false; }
    let payload;
    try { payload = JSON.stringify(DB); }
    catch (e) { flashSaved("not saved"); return false; }
    const okw = await queueStorageWrite(payload);
    payload = null;
    if (!okw) {
      storageWriteBlocked = true;
      toast("Browser storage could not be written — saving is paused. Export a backup before closing this tab.", 6200);
      flashSaved("not saved — storage unavailable");
      return false;
    }
    if (!store.persistent) flashSaved("not saved — private mode");
    else flashSaved("saved");
    return true;
  };
  if (now) return write();
  saveT = setTimeout(() => { void write(); }, 450);
  return Promise.resolve(true);
}'''
html = rep(html, old_save, new_save, "async save")

# Load from IndexedDB, automatically migrating the existing localStorage record.
html = rep(html, '''function load() {
  let raw = store.get(KEY);''', '''async function load() {
  let raw = await store.get(KEY);''', "async load")

# Storage sizing: 5 MB only applies to legacy localStorage. IndexedDB gets a conservative soft working budget.
old_meter = '''function dbBytes() { try { return JSON.stringify(DB).length; } catch (e) { return 0; } }
const QUOTA = 5 * 1024 * 1024;
function renderMeter() {
  const bar = $("#meter"); if (!bar) return;
  const used = dbBytes(), pct = Math.min(100, Math.round(used / QUOTA * 100));
  bar.querySelector("i").style.width = Math.max(2, pct) + "%";
  bar.classList.toggle("full", pct > 80);
  const pics = DB.boards.reduce((n, b) => n + b.items.filter(i => i.src).length, 0);
  $("#meterlab").textContent = `${fmtBytes(used)} used of about 5 MB · ${pics} picture${pics === 1 ? "" : "s"}`;
  $("#btn-shrink").style.display = board.items.some(i => i.src) ? "" : "none";
  backupLine();
}'''
new_meter = '''function dbBytes() {
  try { return new Blob([JSON.stringify(DB)]).size; }
  catch (e) { try { return JSON.stringify(DB).length; } catch (e2) { return 0; } }
}
const LEGACY_QUOTA = 5 * 1024 * 1024;
const IDB_SOFT_BUDGET = 64 * 1024 * 1024;
const storageBudget = () => store.largeCapacity ? IDB_SOFT_BUDGET : LEGACY_QUOTA;
function renderMeter() {
  const bar = $("#meter"); if (!bar) return;
  const used = dbBytes();
  const pics = DB.boards.reduce((n, b) => n + b.items.filter(i => i.src).length, 0);
  const picText = `${pics} picture${pics === 1 ? "" : "s"}`;
  if (store.largeCapacity) {
    const softPct = Math.min(100, Math.round(used / IDB_SOFT_BUDGET * 100));
    bar.querySelector("i").style.width = Math.max(2, softPct) + "%";
    bar.classList.toggle("full", false);
    $("#meterlab").textContent = `${fmtBytes(used)} project data · database storage · ${picText}`;
    if (navigator.storage && navigator.storage.estimate) {
      navigator.storage.estimate().then(est => {
        if (!bar.isConnected || !store.largeCapacity) return;
        const usage = +est.usage || 0, quota = +est.quota || 0;
        const pct = quota ? Math.min(100, Math.round(usage / quota * 100)) : softPct;
        bar.querySelector("i").style.width = Math.max(2, pct) + "%";
        bar.classList.toggle("full", pct > 85);
        $("#meterlab").textContent = quota
          ? `${fmtBytes(used)} project data · ${fmtBytes(usage)} of ${fmtBytes(quota)} browser storage used · ${picText}`
          : `${fmtBytes(used)} project data · database storage · ${picText}`;
      }).catch(() => {});
    }
  } else {
    const pct = Math.min(100, Math.round((used * 2) / LEGACY_QUOTA * 100));
    bar.querySelector("i").style.width = Math.max(2, pct) + "%";
    bar.classList.toggle("full", pct > 80);
    $("#meterlab").textContent = `${fmtBytes(used * 2)} local storage used of about 5 MB · ${picText}`;
  }
  $("#btn-shrink").style.display = board.items.some(i => i.src) ? "" : "none";
  backupLine();
}'''
html = rep(html, old_meter, new_meter, "storage meter")

# Photo budget should use the active backend's soft budget, not a fixed 5 MB ceiling.
html = rep(html, 'const room = QUOTA - dbBytes();', 'const room = storageBudget() - dbBytes();', "photo room budget")

# Imports: await IndexedDB, use the static 5 MB check only on legacy fallback, and serialize against pending saves.
html = rep(html, 'fr.onload = () => {\n    try {', 'fr.onload = async () => {\n    try {', "async import callback")
html = rep(html, '''      if (payload.length > QUOTA * .96) {
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
      DB.boards.push(...staged);''', '''      if (!store.largeCapacity && payload.length * 2 > LEGACY_QUOTA * .96) {
        payload = null;
        toast("Import cancelled — this browser fell back to limited local storage. Export/remove a board or try a normal browser window.", 6200);
        return;
      }
      clearTimeout(saveT);
      await storageWriteP.catch(() => false);
      if (!await queueStorageWrite(payload)) {
        payload = null;
        toast("Import cancelled — browser database storage could not be written. Your existing boards were left unchanged.", 6200);
        return;
      }
      payload = null;
      DB.boards.push(...staged);''', "transactional IndexedDB import")

# Startup now waits for IndexedDB/migration before any UI or save is initialised.
old_boot = '''/* ═══════════════ go ═══════════════ */
load();
$("#version").textContent = "Pin It " + VERSION + " · " + BUILD;
const wasVersion = DB.version;
if (!DB.lastSeenRelease) DB.lastSeenRelease = wasVersion || VERSION;
DB.version = VERSION;
updateReleaseBadges();
applyTheme();
renderLegend();
plate();
renderAll();
applyView();
if (board.items.length) {
  const v = board.view || {}, r = viewport.getBoundingClientRect();
  const resized = !v.w || !v.h || Math.abs(v.w - r.width) > r.width * 0.18 || Math.abs(v.h - r.height) > r.height * 0.18;
  if (resized || (!v.x && !v.y) || !anyVisible()) fitBoard(false);
}
updateUndo();
if (wasVersion && wasVersion !== VERSION) setTimeout(() => toast("Updated to Pin It " + VERSION, 3600), 1200);
save(true);
quietPersistOnce();
setTimeout(safetyCheck, 2600);
if (FRESH) startTour("first");
else if (!store.persistent) toast("This browser won't save boards — export before you close the tab.", 5000);'''
new_boot = '''/* ═══════════════ go ═══════════════ */
(async function bootPinIt() {
  await load();
  $("#version").textContent = "Pin It " + VERSION + " · " + BUILD;
  const wasVersion = DB.version;
  if (!DB.lastSeenRelease) DB.lastSeenRelease = wasVersion || VERSION;
  DB.version = VERSION;
  updateReleaseBadges();
  applyTheme();
  renderLegend();
  plate();
  renderAll();
  applyView();
  if (board.items.length) {
    const v = board.view || {}, r = viewport.getBoundingClientRect();
    const resized = !v.w || !v.h || Math.abs(v.w - r.width) > r.width * 0.18 || Math.abs(v.h - r.height) > r.height * 0.18;
    if (resized || (!v.x && !v.y) || !anyVisible()) fitBoard(false);
  }
  updateUndo();
  if (wasVersion && wasVersion !== VERSION) setTimeout(() => toast("Updated to Pin It " + VERSION, 3600), 1200);
  await save(true);
  renderMeter();
  quietPersistOnce();
  setTimeout(safetyCheck, 2600);
  if (FRESH) startTour("first");
  else if (!store.persistent) toast("This browser won't save boards — export before you close the tab.", 5000);
})().catch(err => {
  console.error("Pin It startup failed", err);
  toast("Pin It could not open browser storage. Reload the page or export any visible work before closing.", 7000);
});'''
html = rep(html, old_boot, new_boot, "async startup")

# Changelog.
entry = '''---

## 1.9.3 — 15 September 2026, 13:46 UTC

- Moved Pin It's primary board database from `localStorage` to **IndexedDB**, removing the old ~5 MB structural ceiling for normal browsers.
- Existing saved boards migrate automatically the first time 1.9.3 loads; after a successful migration the old `localStorage` copy is removed to immediately free that quota.
- Kept `localStorage` only as a fallback for browsers where IndexedDB is unavailable.
- Updated autosave and board import to use ordered asynchronous database writes so newer state cannot be overwritten by an older pending save.
- Imports remain transactional: the candidate database must be stored successfully before the imported board is added to the live session.
- Updated the storage meter to show project-data size and, where supported, the browser's real storage estimate rather than a fixed 5 MB ceiling.
- Photo compression now uses a conservative IndexedDB soft budget while preserving the tighter legacy fallback behaviour.

## 1.9.2 — 15 September 2026, 13:34 UTC'''
log = rep(log, '''---

## 1.9.2 — 15 September 2026, 13:34 UTC''', entry, "changelog")

INDEX.write_text(html, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# First pass: every inline script must parse.
scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S | re.I)
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        p = Path(td) / f"script-{i}.js"
        p.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(p)], check=True)

# Second pass: storage migration and release contracts.
checks = {
    "version": 'const VERSION = "1.9.3";' in html,
    "build": 'const BUILD = "15 September 2026, 13:46 UTC";' in html,
    "release": 'version: "1.9.3", date: "15 September 2026, 13:46 UTC"' in html,
    "changelog": "## 1.9.3 — 15 September 2026, 13:46 UTC" in log,
    "idb-open": 'indexedDB.open(DB_NAME, 1)' in html,
    "idb-store": 'db.createObjectStore(STORE_NAME)' in html,
    "legacy-migration": 'await idbSet(k, legacy); clearLegacy(k);' in html,
    "legacy-cleanup": 'localStorage.removeItem(k)' in html,
    "async-load": 'async function load()' in html and 'let raw = await store.get(KEY);' in html,
    "ordered-save": 'storageWriteP = storageWriteP.catch(() => false).then(() => store.set(KEY, payload));' in html,
    "await-save": 'const okw = await queueStorageWrite(payload);' in html,
    "async-import": 'fr.onload = async () =>' in html,
    "transactional-import": 'if (!await queueStorageWrite(payload))' in html,
    "legacy-only-import-cap": 'if (!store.largeCapacity && payload.length * 2 > LEGACY_QUOTA * .96)' in html,
    "no-old-hard-cap": 'payload.length > QUOTA * .96' not in html,
    "meter-estimate": 'navigator.storage.estimate()' in html,
    "idb-photo-budget": 'const room = storageBudget() - dbBytes();' in html,
    "async-boot": '(async function bootPinIt()' in html and 'await load();' in html,
    "old-sync-load-gone": '\nload();\n$("#version")' not in html,
}
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise SystemExit("v1.9.3 checks failed: " + ", ".join(failed))

print(f"Pin It 1.9.3 verified: {len(scripts)} inline scripts parsed; {len(checks)} migration/storage checks passed")
