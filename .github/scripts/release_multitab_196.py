from pathlib import Path
import re, subprocess, tempfile

INDEX=Path('index.html'); CHANGELOG=Path('CHANGELOG.md'); README=Path('README.md')
html=INDEX.read_text(encoding='utf-8'); log=CHANGELOG.read_text(encoding='utf-8'); readme=README.read_text(encoding='utf-8')

def rep(text, old, new, label, count=1):
    n=text.count(old)
    if n!=count: raise SystemExit(f'{label}: expected {count}, found {n}')
    return text.replace(old,new,count)

def sub(text, pattern, repl, label, count=1):
    out,n=re.subn(pattern,repl,text,count=count,flags=re.S)
    if n!=count: raise SystemExit(f'{label}: expected {count}, found {n}')
    return out

# Release metadata
html=rep(html,'Version 1.9.5 · 15 September 2026, 14:08 UTC','Version 1.9.6 · 15 September 2026, 14:17 UTC','header')
html=rep(html,'const VERSION = "1.9.5";','const VERSION = "1.9.6";','version')
html=rep(html,'const BUILD = "15 September 2026, 14:08 UTC";','const BUILD = "15 September 2026, 14:17 UTC";','build')
release='''  {\n    version: "1.9.6", date: "15 September 2026, 14:17 UTC",\n    summary: "Multi-tab protection and another storage-performance pass reduce the remaining ways two sessions or large projects could lose or stall work.",\n    items: [\n      "Added an active-tab lease with a blocking safety screen: a second Pin It tab opens protected instead of silently competing to save the same boards.",\n      "Added safe Take over & reload handling, storage revision broadcasts and cross-tab Web Locks where supported so control can move between tabs without last-write-wins corruption.",\n      "Tabs now detect a newer saved revision even if the other tab has already closed, forcing a reload before stale in-memory data can save over it.",\n      "The project-size meter now reuses the size of the most recently serialized database instead of stringifying the whole project again just to measure it.",\n      "Imports now participate in the same cross-tab write lock/revision protocol as autosave, closing a remaining race between imports and another open session.",\n      "Added Page Lifecycle freeze flushing and a focused retry path for transient IndexedDB write failures."\n    ]\n  },\n'''
html=rep(html,'const RELEASES = [\n','const RELEASES = [\n'+release,'release entry')

# Multi-tab guard lives next to the storage key so all persistence paths can share it.
tab_code=r'''

/* ── multi-tab guard: one writer at a time, with reload-before-takeover semantics ── */
const TAB_LEASE_KEY = "pinit.tabLease.v1";
const TAB_REV_KEY = "pinit.storageRev.v1";
const TAB_CHANNEL_NAME = "pin-it-tabs-v1";
const TAB_LEASE_TTL = 7000;
const TAB_HEARTBEAT_MS = 2200;
const TAB_STARTED_AT = Date.now();
let tabGuardStarted = false, tabReadOnly = false, tabLeaseTimer = null, tabChannel = null;
let tabLeaseStorageOK = true, tabForceTakeover = false;
let TAB_ID = "";
try {
  TAB_ID = sessionStorage.getItem("pinit.tabId.v1") || (Date.now().toString(36) + "-" + Math.random().toString(36).slice(2));
  sessionStorage.setItem("pinit.tabId.v1", TAB_ID);
  tabForceTakeover = sessionStorage.getItem("pinit.tabTakeover.v1") === "1";
  sessionStorage.removeItem("pinit.tabTakeover.v1");
} catch (e) {
  TAB_ID = Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
}
try { localStorage.setItem("__pinit_tab_test", "1"); localStorage.removeItem("__pinit_tab_test"); }
catch (e) { tabLeaseStorageOK = false; }

function readTabLease() {
  if (!tabLeaseStorageOK) return null;
  try { const raw = localStorage.getItem(TAB_LEASE_KEY); return raw ? JSON.parse(raw) : null; }
  catch (e) { tabLeaseStorageOK = false; return null; }
}
function tabLeaseFresh(l) { return !!(l && l.id && Date.now() - (+l.ts || 0) < TAB_LEASE_TTL); }
function readExternalRevision() {
  if (!tabLeaseStorageOK) return 0;
  try { return +(localStorage.getItem(TAB_REV_KEY) || 0); } catch (e) { return 0; }
}
function writeTabLease(force) {
  if (!tabLeaseStorageOK) return false;
  try {
    const cur = readTabLease();
    if (!force && tabLeaseFresh(cur) && cur.id !== TAB_ID) return false;
    localStorage.setItem(TAB_LEASE_KEY, JSON.stringify({ id:TAB_ID, ts:Date.now(), rev:+storageRevision || 0 }));
    return true;
  } catch (e) { tabLeaseStorageOK = false; return false; }
}
function announceTab(msg) {
  if (!tabChannel) return;
  try { tabChannel.postMessage(Object.assign({ id:TAB_ID, started:TAB_STARTED_AT, rev:+storageRevision || 0 }, msg)); } catch (e) {}
}
function ensureTabGuardUI() {
  if (document.getElementById("tabguard")) return;
  const style = document.createElement("style");
  style.textContent = `#tabguard{position:fixed;inset:0;z-index:100000;display:grid;place-items:center;padding:24px;background:rgba(8,8,8,.64);backdrop-filter:blur(4px)}
  #tabguard[hidden]{display:none}#tabguard .tg-card{width:min(520px,calc(100vw - 32px));padding:22px;border:1px solid var(--ui-line);border-radius:10px;background:linear-gradient(180deg,var(--ui-1),var(--ui-2));color:var(--ui-fg);box-shadow:0 24px 70px rgba(0,0,0,.45);font-family:var(--ui)}
  #tabguard .tg-card h2{margin:0 0 9px;font-size:20px;color:var(--pan-head)}#tabguard .tg-card p{margin:0 0 18px;line-height:1.45;color:var(--pan-sub)}
  #tabguard .tg-actions{display:flex;gap:9px;flex-wrap:wrap;justify-content:flex-end}#tabguard button{padding:10px 14px;border:1px solid var(--ui-line);border-radius:7px;background:var(--pan-soft2);color:var(--ui-fg);font-weight:700}
  #tabguard button.primary{background:linear-gradient(180deg,var(--btn1),var(--btn2));color:var(--btnfg);border-color:var(--ui-online)}`;
  document.head.appendChild(style);
  const guard = document.createElement("div");
  guard.id = "tabguard"; guard.hidden = true;
  guard.innerHTML = `<div class="tg-card" role="dialog" aria-modal="true" aria-labelledby="tg-title"><h2 id="tg-title">Pin It is active in another tab</h2><p id="tg-copy">This tab is protected from saving so two copies cannot overwrite each other. Reload this tab, or move control here and reload the latest saved state.</p><div class="tg-actions"><button type="button" id="tg-reload">Reload this tab</button><button type="button" class="primary" id="tg-takeover">Use this tab instead</button></div></div>`;
  document.body.appendChild(guard);
  document.getElementById("tg-reload").onclick = () => location.reload();
  document.getElementById("tg-takeover").onclick = async () => {
    try { sessionStorage.setItem("pinit.tabTakeover.v1", "1"); } catch (e) {}
    await withCrossTabStorageLock(async () => { writeTabLease(true); announceTab({ type:"takeover" }); });
    location.reload();
  };
}
function setTabReadOnly(on, message) {
  tabReadOnly = !!on;
  ensureTabGuardUI();
  const guard = document.getElementById("tabguard");
  const copy = document.getElementById("tg-copy");
  if (copy && message) copy.textContent = message;
  if (guard) guard.hidden = !tabReadOnly;
  if (tabReadOnly) { clearInterval(tabLeaseTimer); tabLeaseTimer = null; clearTimeout(saveT); }
}
async function withCrossTabStorageLock(fn) {
  if (navigator.locks && navigator.locks.request) {
    try { return await navigator.locks.request("pin-it-storage-write-v1", { mode:"exclusive" }, fn); }
    catch (e) {}
  }
  return fn();
}
function tabCanWrite() {
  if (!tabGuardStarted) return true;
  if (tabReadOnly) return false;
  const externalRev = readExternalRevision();
  if (externalRev > (+storageRevision || 0)) {
    setTabReadOnly(true, "A newer Pin It save exists from another tab. Reload before editing so this older in-memory copy cannot overwrite it.");
    return false;
  }
  if (tabLeaseStorageOK) {
    const cur = readTabLease();
    if (tabLeaseFresh(cur) && cur.id !== TAB_ID) {
      setTabReadOnly(true, "Another Pin It tab currently controls saving. Reload here, or use this tab instead to transfer control safely.");
      return false;
    }
    if (!writeTabLease(false)) return false;
  }
  return !tabReadOnly;
}
function publishTabRevision() {
  if (tabLeaseStorageOK) {
    try { localStorage.setItem(TAB_REV_KEY, String(+storageRevision || 0)); } catch (e) {}
    writeTabLease(true);
  }
  announceTab({ type:"saved", rev:+storageRevision || 0 });
}
function handleTabMessage(data) {
  if (!data || data.id === TAB_ID) return;
  const otherRev = +data.rev || 0;
  if (data.type === "saved" && otherRev > (+storageRevision || 0)) {
    setTabReadOnly(true, "Another Pin It tab saved newer changes. Reload this tab before continuing so those changes cannot be overwritten.");
    return;
  }
  if (data.type === "takeover") {
    setTabReadOnly(true, "Another Pin It tab has taken control of saving. Reload this tab to continue from the newest saved state.");
    return;
  }
  if (!tabLeaseStorageOK && (data.type === "hello" || data.type === "primary")) {
    const otherWins = (+data.started || 0) < TAB_STARTED_AT || ((+data.started || 0) === TAB_STARTED_AT && String(data.id) < TAB_ID);
    if (otherWins) setTabReadOnly(true, "Another Pin It tab was opened first, so this copy is protected from saving. Reload or take over to continue here.");
    else if (!tabReadOnly) announceTab({ type:"primary" });
  }
  if (data.type === "hello" && !tabReadOnly) announceTab({ type:"primary" });
}
function checkTabGuard() {
  if (!tabGuardStarted || tabReadOnly) return !tabReadOnly;
  return tabCanWrite();
}
function initTabGuard() {
  ensureTabGuardUI();
  if (!tabGuardStarted) {
    tabGuardStarted = true;
    if (typeof BroadcastChannel !== "undefined") {
      try { tabChannel = new BroadcastChannel(TAB_CHANNEL_NAME); tabChannel.onmessage = e => handleTabMessage(e.data); } catch (e) { tabChannel = null; }
    }
    addEventListener("storage", e => {
      if (e.key === TAB_REV_KEY && +(e.newValue || 0) > (+storageRevision || 0)) {
        setTabReadOnly(true, "Another Pin It tab saved newer changes. Reload this tab before continuing.");
      }
      if (e.key === TAB_LEASE_KEY) {
        const l = readTabLease();
        if (tabLeaseFresh(l) && l.id !== TAB_ID) setTabReadOnly(true, "Another Pin It tab now controls saving. Reload or take over before continuing here.");
      }
    });
  }
  if (readExternalRevision() > (+storageRevision || 0)) {
    setTabReadOnly(true, "A newer saved revision already exists. Reload this tab before making changes.");
    return false;
  }
  const cur = readTabLease();
  if (!tabForceTakeover && tabLeaseFresh(cur) && cur.id !== TAB_ID) {
    setTabReadOnly(true, "Pin It is already open in another tab. This copy is read-only to prevent one tab overwriting the other.");
  } else {
    writeTabLease(!!tabForceTakeover);
    tabForceTakeover = false;
    setTabReadOnly(false);
    clearInterval(tabLeaseTimer);
    tabLeaseTimer = setInterval(() => { if (!tabReadOnly) writeTabLease(false); }, TAB_HEARTBEAT_MS);
  }
  announceTab({ type:"hello" });
  return !tabReadOnly;
}
'''
html=rep(html,'const KEY = "pinit.v1";\n\n/* ── state ── */','const KEY = "pinit.v1";'+tab_code+'\n/* ── state ── */','tab guard insertion')

# Cache most recent serialized size, and make autosave/import obey cross-tab ownership + lock.
html=rep(html,'let storageRevision = 0;','let storageRevision = 0;\nlet lastKnownDbBytes = 0;','size cache state')
html=rep(html,'function flushStorage() {\n  storageDirty = true;\n  if (storageFlushP) return storageFlushP;',
'''function flushStorage() {\n  storageDirty = true;\n  if (!tabCanWrite()) { flashSaved("read-only — another tab"); return Promise.resolve(false); }\n  if (storageFlushP) return storageFlushP;''','flush tab precheck')
old_write='''      let payload;\n      try { payload = JSON.stringify(DB); }\n      catch (e) { flashSaved("not saved"); return false; }\n      ok = await store.set(KEY, payload);\n      payload = null;\n      if (!ok) {\n        storageWriteBlocked = true;\n        toast("Browser storage could not be written — saving is paused. Export a backup before closing this tab.", 6200);\n        flashSaved("not saved — storage unavailable");\n        return false;\n      }'''
new_write='''      if (!tabCanWrite()) { flashSaved("read-only — another tab"); return false; }\n      let payload;\n      try { payload = JSON.stringify(DB); }\n      catch (e) { flashSaved("not saved"); return false; }\n      const payloadBytes = payload.length;\n      ok = await withCrossTabStorageLock(async () => {\n        if (!tabCanWrite()) return false;\n        return store.set(KEY, payload);\n      });\n      payload = null;\n      if (!ok) {\n        if (tabReadOnly) { flashSaved("read-only — another tab"); return false; }\n        storageWriteBlocked = true;\n        toast("Browser storage could not be written — saving is paused. Export a backup before closing this tab.", 6200);\n        flashSaved("not saved — storage unavailable");\n        return false;\n      }\n      lastKnownDbBytes = payloadBytes;\n      publishTabRevision();'''
html=rep(html,old_write,new_write,'cross-tab autosave write')
html=rep(html,'function save(now) {\n  if (!board) return Promise.resolve(false);',
'''function save(now) {\n  if (!board) return Promise.resolve(false);\n  if (tabGuardStarted && tabReadOnly) { flashSaved("read-only — another tab"); return Promise.resolve(false); }''','save read-only guard')
html=rep(html,'  let raw = await store.get(KEY);\n  if (raw) { try { DB = JSON.parse(raw); } catch (e) { DB = { boards: [], current: null }; } }',
'''  let raw = await store.get(KEY);\n  if (raw) {\n    lastKnownDbBytes = String(raw).length;\n    try { DB = JSON.parse(raw); } catch (e) { DB = { boards: [], current: null }; }\n  }''','load size cache')
old_dbbytes='''function dbBytes() {\n  try { return new Blob([JSON.stringify(DB)]).size; }\n  catch (e) { try { return JSON.stringify(DB).length; } catch (e2) { return 0; } }\n}'''
new_dbbytes='''function dbBytes() {\n  if (lastKnownDbBytes > 0) return lastKnownDbBytes;\n  try {\n    const raw = JSON.stringify(DB);\n    lastKnownDbBytes = raw.length;\n    return lastKnownDbBytes;\n  } catch (e) { return 0; }\n}'''
html=rep(html,old_dbbytes,new_dbbytes,'db size cache')

# Import must use the same ownership check, write lock and revision broadcast.
html=rep(html,'      clearTimeout(saveT);\n      if (storageDirty && !await flushStorage()) {',
'''      if (!tabCanWrite()) {\n        toast("Import cancelled — another Pin It tab currently controls saving. Reload or take over first.", 6200); return;\n      }\n      clearTimeout(saveT);\n      if (storageDirty && !await flushStorage()) {''','import tab guard')
old_import='''      const persisted = await queueStorageOp(() => store.set(KEY, payload));\n      payload = null;\n      if (!persisted) {'''
new_import='''      const payloadBytes = payload.length;\n      const persisted = await queueStorageOp(() => withCrossTabStorageLock(async () => {\n        if (!tabCanWrite()) return false;\n        return store.set(KEY, payload);\n      }));\n      payload = null;\n      if (!persisted) {'''
html=rep(html,old_import,new_import,'import locked write')
html=rep(html,'      DB.storageRev = candidate.storageRev; storageRevision = DB.storageRev;\n      storageWriteBlocked = false; storageDirty = false;',
'''      DB.storageRev = candidate.storageRev; storageRevision = DB.storageRev;\n      lastKnownDbBytes = payloadBytes; publishTabRevision();\n      storageWriteBlocked = false; storageDirty = false;''','import revision publish')

# Boot guard before any normal boot-time save can run.
html=rep(html,'(async function bootPinIt() {\n  await load();\n  $("#version").textContent = "Pin It " + VERSION + " · " + BUILD;',
'''(async function bootPinIt() {\n  await load();\n  initTabGuard();\n  $("#version").textContent = "Pin It " + VERSION + " · " + BUILD;''','boot tab guard')

# Page lifecycle: keep async flushes early and recheck ownership when a frozen/background page returns.
html=rep(html,'document.addEventListener("visibilitychange", () => { if (document.hidden) flushForExit(); });',
'''document.addEventListener("visibilitychange", () => { if (document.hidden) flushForExit(); });\ndocument.addEventListener("freeze", flushForExit);\naddEventListener("pageshow", () => {\n  checkTabGuard();\n  if (!tabReadOnly && storageWriteBlocked && storageDirty) { storageWriteBlocked = false; void flushStorage(); }\n});\naddEventListener("focus", () => {\n  checkTabGuard();\n  if (!tabReadOnly && storageWriteBlocked && storageDirty) { storageWriteBlocked = false; void flushStorage(); }\n});''','page lifecycle')

# README: document one-writer behaviour.
needle='''## Keeping boards safe\n\nBoards live in the browser, and browsers do clear storage — iOS Safari is the strict one, wiping script-writable storage for sites it hasn't seen in roughly a week of use. Four things guard against that:\n'''
replace='''## Keeping boards safe\n\nBoards live in the browser, and browsers do clear storage — iOS Safari is the strict one, wiping script-writable storage for sites it hasn't seen in roughly a week of use.\n\n**One editing tab at a time.** Pin It protects the database with an active-tab lease. If the same app is opened in another tab/window, the second copy is blocked from saving rather than competing with the first. **Use this tab instead** transfers control and reloads the newest saved state before editing, and storage revisions catch stale tabs even after the other window has closed. Browsers that support Web Locks also serialize the actual database write across tabs.\n\nFour other things guard against loss:\n'''
readme=rep(readme,needle,replace,'README multi-tab safety')

# Changelog
entry='''---\n\n## 1.9.6 — 15 September 2026, 14:17 UTC\n\n- Added **single-writer multi-tab protection**: a second Pin It tab/window is blocked from saving instead of silently racing the first one.\n- Added a persistent active-tab lease, heartbeat and saved-revision marker, plus `BroadcastChannel` notifications where available.\n- **Use this tab instead** now transfers control and reloads the latest saved database before the new tab can edit it.\n- Database writes and imports use the browser **Web Locks API** where available, providing another cross-tab serialization layer around IndexedDB.\n- Tabs detect a newer revision even if the other tab has already closed, preventing a stale in-memory copy from overwriting newer work.\n- Reworked the storage-size meter to reuse the most recently serialized payload size instead of running another whole-project `JSON.stringify()` solely for metering.\n- Board imports now follow the same tab-ownership, lock and revision-publication path as autosave.\n- Added Page Lifecycle `freeze` flushing and automatic retry of a transient IndexedDB failure when the app returns to focus.\n\n## 1.9.5 — 15 September 2026, 14:08 UTC'''
log=rep(log,'---\n\n## 1.9.5 — 15 September 2026, 14:08 UTC',entry,'changelog')

INDEX.write_text(html,encoding='utf-8'); CHANGELOG.write_text(log,encoding='utf-8'); README.write_text(readme,encoding='utf-8')

# Pass 1: every inline script must parse.
scripts=re.findall(r'<script(?:\\s[^>]*)?>(.*?)</script>',html,re.S|re.I)
with tempfile.TemporaryDirectory() as td:
    for i,s in enumerate(scripts):
        p=Path(td)/f's{i}.js'; p.write_text(s,encoding='utf-8')
        subprocess.run(['node','--check',str(p)],check=True)

# Pass 2: reliability contracts.
checks={
 'version':'const VERSION = "1.9.6";' in html,
 'build':'const BUILD = "15 September 2026, 14:17 UTC";' in html,
 'release':'version: "1.9.6", date: "15 September 2026, 14:17 UTC"' in html,
 'changelog':'## 1.9.6 — 15 September 2026, 14:17 UTC' in log,
 'lease':'const TAB_LEASE_KEY = "pinit.tabLease.v1";' in html,
 'revision-marker':'const TAB_REV_KEY = "pinit.storageRev.v1";' in html,
 'broadcast':'new BroadcastChannel(TAB_CHANNEL_NAME)' in html,
 'web-lock':'navigator.locks.request("pin-it-storage-write-v1"' in html,
 'save-owner-check':'if (!tabCanWrite()) { flashSaved("read-only — another tab")' in html,
 'write-lock':'ok = await withCrossTabStorageLock(async () =>' in html,
 'revision-publish':html.count('publishTabRevision();') >= 2,
 'takeover-reload':'sessionStorage.setItem("pinit.tabTakeover.v1", "1")' in html and 'location.reload();' in html,
 'boot-guard':'await load();\n  initTabGuard();' in html,
 'import-guard':'Import cancelled — another Pin It tab currently controls saving.' in html,
 'size-cache':'if (lastKnownDbBytes > 0) return lastKnownDbBytes;' in html,
 'no-meter-reserialize':'new Blob([JSON.stringify(DB)])' not in html,
 'freeze-flush':'document.addEventListener("freeze", flushForExit);' in html,
 'readme':'One editing tab at a time.' in readme,
}
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('reliability checks failed: '+', '.join(failed))
print(f'Pin It 1.9.6 verified: {len(scripts)} inline scripts parse; {len(checks)} reliability checks passed')
