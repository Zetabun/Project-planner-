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
html=rep(html,'Version 1.9.4 · 15 September 2026, 13:54 UTC','Version 1.9.5 · 15 September 2026, 14:08 UTC','header')
html=rep(html,'const VERSION = "1.9.4";','const VERSION = "1.9.5";','version')
html=rep(html,'const BUILD = "15 September 2026, 13:54 UTC";','const BUILD = "15 September 2026, 14:08 UTC";','build')
release='''  {\n    version: "1.9.5", date: "15 September 2026, 14:08 UTC",\n    summary: "A reliability pass hardens storage, undo, backups and several edge cases found in the post-1.9.4 audit.",\n    items: [\n      "Hardened IndexedDB migration/fallback so an older localStorage copy cannot silently replace a newer IndexedDB database after a storage error.",\n      "Replaced queued full-database save payloads with a coalescing writer: rapid edits now collapse into the latest state instead of building a memory backlog.",\n      "Undo/redo now restores board tags and whole-board text settings as well as items, links, drawings, inbox ideas and systems; expired image history is pruned from memory.",\n      "Backup status is now tracked per board, so backing up one project no longer makes every board look safely backed up.",\n      "Hide Done now also suppresses strings and relationship labels attached to hidden finished items and excludes those items from fit calculations.",\n      "Fixed image-import board switching, stale progress/tag counts after deletes/duplicates/undo, minimap coverage for freehand drawings, onboarding example systems, theme-preview cancellation, New Board cancellation and Escape closing the outline.",\n      "Added stronger page-hide save flushing and corrected the Board Map documentation to match its collapsed-by-default behaviour."\n    ]\n  },\n'''
html=rep(html,'const RELEASES = [\n','const RELEASES = [\n'+release,'release entry')

# Storage backend: reconcile old split-brain state and never fall back to a stale local copy after IDB has become authoritative.
store_new=r'''/* ── storage: IndexedDB first; localStorage is migration/fallback only ── */
const store = (() => {
  const DB_NAME = "pin-it-storage";
  const STORE_NAME = "kv";
  let mem = {}, openP = null;
  let localOK = true;
  let idbOK = typeof indexedDB !== "undefined";
  let idbOpened = false, idbAuthoritative = false;
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
      req.onsuccess = () => { idbOpened = true; resolve(req.result); };
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
  function payloadStamp(raw) {
    try {
      const d = JSON.parse(raw), boards = Array.isArray(d.boards) ? d.boards : [];
      return { rev:+d.storageRev || 0, updated:boards.reduce((m,b) => Math.max(m,+b.updated || 0), 0) };
    } catch (e) { return { rev:0, updated:0 }; }
  }
  function newer(a, b) {
    const A = payloadStamp(a), B = payloadStamp(b);
    if (A.rev || B.rev) return A.rev !== B.rev ? A.rev > B.rev : A.updated > B.updated;
    return A.updated > B.updated;
  }

  return {
    get persistent() { return idbOK || localOK; },
    get largeCapacity() { return idbOK; },
    async get(k) {
      const legacy = legacyGet(k);
      if (idbOK) {
        try {
          const current = await idbGet(k);
          if (current != null) {
            idbAuthoritative = true;
            if (legacy != null && newer(legacy, current)) {
              await idbSet(k, legacy);
              clearLegacy(k);
              return legacy;
            }
            clearLegacy(k);
            return current;
          }
          if (legacy != null) {
            await idbSet(k, legacy);
            idbAuthoritative = true;
            clearLegacy(k);
            return legacy;
          }
          return null;
        } catch (e) {
          /* Once IndexedDB has opened/held real data, never resurrect a possibly stale local copy. */
          if (idbOpened || idbAuthoritative) throw e;
          idbOK = false; openP = null;
        }
      }
      return legacy;
    },
    async set(k, v) {
      if (idbOK) {
        try {
          await idbSet(k, v);
          idbAuthoritative = true;
          clearLegacy(k);
          return true;
        } catch (e) {
          /* Keep IDB as the authority and report failure; falling back here can create two divergent databases. */
          if (idbOpened || idbAuthoritative) return false;
          idbOK = false; openP = null;
        }
      }
      if (!localOK) { mem[k] = v; return false; }
      try { localStorage.setItem(k, v); return true; }
      catch (e) { return false; }
    }
  };
})();
const KEY = "pinit.v1";'''
html=sub(html,r'/\* ── storage: IndexedDB first; localStorage is migration/fallback only ── \*/\nconst store = \(\(\) => \{.*?\n\}\)\(\);\nconst KEY = "pinit\.v1";',store_new,'storage block')

# Persistence: serialize only when a queued write actually runs and collapse rapid edits into one latest-state write.
persist_new=r'''/* ── persistence ── */
let saveT = null;
let storageWriteBlocked = false;
let storageDirty = false;
let storageFlushP = null;
let storageOpP = Promise.resolve(true);
let storageRevision = 0;
function allowStorageRetry() { storageWriteBlocked = false; }
function queueStorageOp(fn) {
  storageOpP = storageOpP.catch(() => false).then(fn);
  return storageOpP;
}
function flushStorage() {
  storageDirty = true;
  if (storageFlushP) return storageFlushP;
  storageFlushP = queueStorageOp(async () => {
    let ok = true;
    while (storageDirty && !storageWriteBlocked) {
      storageDirty = false;
      DB.storageRev = Math.max(+DB.storageRev || 0, storageRevision) + 1;
      storageRevision = DB.storageRev;
      let payload;
      try { payload = JSON.stringify(DB); }
      catch (e) { flashSaved("not saved"); return false; }
      ok = await store.set(KEY, payload);
      payload = null;
      if (!ok) {
        storageWriteBlocked = true;
        toast("Browser storage could not be written — saving is paused. Export a backup before closing this tab.", 6200);
        flashSaved("not saved — storage unavailable");
        return false;
      }
      if (!store.persistent) flashSaved("not saved — private mode");
      else flashSaved("saved");
    }
    return ok;
  }).finally(() => {
    storageFlushP = null;
    if (storageDirty && !storageWriteBlocked) void flushStorage();
  });
  return storageFlushP;
}
function save(now) {
  if (!board) return Promise.resolve(false);
  board.updated = Date.now();
  board.view = { x: view.x, y: view.y, s: view.s, w: view.w, h: view.h };
  clearTimeout(saveT);
  renderTimeline();
  storageDirty = true;
  if (now) return flushStorage();
  saveT = setTimeout(() => { void flushStorage(); }, 300);
  return Promise.resolve(true);
}
function flashSaved(txt) {
  const t = $("#savetag"); t.textContent = txt; t.classList.add("show");
  clearTimeout(flashSaved._t); flashSaved._t = setTimeout(() => t.classList.remove("show"), 1400);
}
async function load() {
  let raw = await store.get(KEY);
  if (raw) { try { DB = JSON.parse(raw); } catch (e) { DB = { boards: [], current: null }; } }
  if (!DB.boards || !DB.boards.length) {
    DB = { boards: [], current: null };
    const b = newBoard("Untitled board");
    DB.boards.push(b); DB.current = b.id; FRESH = true;
  }
  DB.boards.forEach(normalise);
  board = DB.boards.find(b => b.id === DB.current) || DB.boards[0];
  if (!DB.flags) DB.flags = {};
  DB.current = board.id;
  storageRevision = +DB.storageRev || 0;
  view = Object.assign({ x: 0, y: 0, s: 1 }, board.view || {});
}

/* ── undo ── */'''
html=sub(html,r'/\* ── persistence ── \*/.*?/\* ── undo ── \*/',persist_new,'persistence block')

# Undo snapshots include board metadata and clean image payloads that have fallen out of both history stacks.
undo_new=r'''/* ── undo ── */
const undoMediaByValue = new Map(), undoMediaByKey = new Map();
let undoMediaSeq = 0;
function clearUndoMedia() { undoMediaByValue.clear(); undoMediaByKey.clear(); undoMediaSeq = 0; }
function pruneUndoMedia() {
  const keep = new Set();
  for (const s of [...history, ...future]) {
    const re = /"_undoSrc":"([^"]+)"/g;
    let m; while ((m = re.exec(s))) keep.add(m[1]);
  }
  for (const [key] of undoMediaByKey) if (!keep.has(key)) undoMediaByKey.delete(key);
  for (const [src, key] of undoMediaByValue) if (!keep.has(key)) undoMediaByValue.delete(src);
}
function snapshotState() {
  const items = board.items.map(it => {
    if (!it.src || typeof it.src !== "string") return it;
    let key = undoMediaByValue.get(it.src);
    if (!key) {
      key = "m" + (++undoMediaSeq);
      undoMediaByValue.set(it.src, key);
      undoMediaByKey.set(key, it.src);
    }
    return Object.assign({}, it, { src:null, _undoSrc:key });
  });
  return JSON.stringify({
    items, links:board.links, ink:board.ink, inbox:board.inbox, groups:board.groups,
    tags:board.tags, fs:board.fs, tagStyle:board.tagStyle, theme:board.theme
  });
}
function inflateSnapshot(s) {
  const d = JSON.parse(s);
  d.items = (d.items || []).map(it => {
    if (!it || !it._undoSrc) return it;
    const copy = Object.assign({}, it, { src:undoMediaByKey.get(it._undoSrc) || "" });
    delete copy._undoSrc;
    return copy;
  });
  return d;
}
function snap() {
  history.push(snapshotState());
  if (history.length > 40) history.shift();
  future.length = 0; pruneUndoMedia(); updateUndo();
}
function applySnap(s) {
  const d = inflateSnapshot(s);
  board.items = d.items || []; board.links = d.links || []; board.ink = d.ink || [];
  board.inbox = d.inbox || []; board.groups = d.groups || []; board.tags = d.tags || [];
  if (+d.fs > 0) board.fs = +d.fs;
  if (d.tagStyle) board.tagStyle = d.tagStyle;
  if (d.theme) board.theme = d.theme;
  sel = null; clearMulti(true); applyTheme(); renderAll(); plate(); renderTimeline(); renderLegend(); renderMeter();
  closePanel("inspect"); save();
}
function undo() {
  if (!history.length) return;
  future.push(snapshotState()); if (future.length > 40) future.shift();
  applySnap(history.pop()); pruneUndoMedia(); updateUndo();
}
function redo() {
  if (!future.length) return;
  history.push(snapshotState()); if (history.length > 40) history.shift();
  applySnap(future.pop()); pruneUndoMedia(); updateUndo();
}
function updateUndo() {
  $("#btn-undo").style.opacity = history.length ? 1 : .4;
  $("#btn-redo").style.opacity = future.length ? 1 : .4;
}

/* ── first-run sample board: teaches the interaction ── */'''
html=sub(html,r'/\* ── undo ── \*/.*?/\* ── first-run sample board: teaches the interaction ── \*/',undo_new,'undo block')

# Hide Done should also remove lines/labels from hidden items and keep them out of fitting bounds.
html=rep(html,'const A = linkEndpoint(l.a), B = linkEndpoint(l.b); if (!A || !B || A.id === B.id) return;\n    const { d, head } = linkGeom(l, A, B);',
'''const A = linkEndpoint(l.a), B = linkEndpoint(l.b); if (!A || !B || A.id === B.id) return;\n    if (hideDone && ((byId(l.a) && byId(l.a).done) || (byId(l.b) && byId(l.b).done))) return;\n    const { d, head } = linkGeom(l, A, B);''','hide-done threads',1)
html=rep(html,'const A = linkEndpoint(l.a), B = linkEndpoint(l.b); if (!A || !B || A.id === B.id) return;\n    const { mid } = linkGeom(l, A, B);',
'''const A = linkEndpoint(l.a), B = linkEndpoint(l.b); if (!A || !B || A.id === B.id) return;\n    if (hideDone && ((byId(l.a) && byId(l.a).done) || (byId(l.b) && byId(l.b).done))) return;\n    const { mid } = linkGeom(l, A, B);''','hide-done labels',1)
html=rep(html,'if (itemHiddenByGroup(i.id)) return;\n    x1 = Math.min(x1, i.x);',
'''if (itemHiddenByGroup(i.id) || (hideDone && i.done)) return;\n    x1 = Math.min(x1, i.x);''','hide-done extents',1)
html=rep(html,'if (typeof itemHiddenByGroup === "function" && itemHiddenByGroup(it.id)) return;\n    rects.push({ x:it.x, y:it.y, w:it.w, h:it.h });',
'''if ((hideDone && it.done) || (typeof itemHiddenByGroup === "function" && itemHiddenByGroup(it.id))) return;\n    rects.push({ x:it.x, y:it.y, w:it.w, h:it.h });''','minimap hidden done',1)

# Minimap bounds/rendering now include freehand ink.
needle='''  (board.items || []).forEach(it => {\n    if ((hideDone && it.done) || (typeof itemHiddenByGroup === "function" && itemHiddenByGroup(it.id))) return;\n    rects.push({ x:it.x, y:it.y, w:it.w, h:it.h });\n  });\n  if (!rects.length) {'''
repl='''  (board.items || []).forEach(it => {\n    if ((hideDone && it.done) || (typeof itemHiddenByGroup === "function" && itemHiddenByGroup(it.id))) return;\n    rects.push({ x:it.x, y:it.y, w:it.w, h:it.h });\n  });\n  (board.ink || []).forEach(st => {\n    const p = st && st.pts || []; if (p.length < 2) return;\n    let x1=Infinity,y1=Infinity,x2=-Infinity,y2=-Infinity;\n    for (let i=0;i<p.length;i+=2) { x1=Math.min(x1,p[i]); x2=Math.max(x2,p[i]); y1=Math.min(y1,p[i+1]); y2=Math.max(y2,p[i+1]); }\n    if (x1 !== Infinity) rects.push({x:x1,y:y1,w:Math.max(1,x2-x1),h:Math.max(1,y2-y1)});\n  });\n  if (!rects.length) {'''
html=rep(html,needle,repl,'minimap ink bounds')
needle='''  (board.items || []).forEach(it => {\n    if (typeof itemHiddenByGroup === "function" && itemHiddenByGroup(it.id)) return;\n    const x = ox + it.x * sc, y = oy + it.y * sc;\n    c.fillRect(x, y, Math.max(2.2, it.w * sc), Math.max(2.2, it.h * sc));\n  });\n  const s = Math.max(.05, view.s || 1);'''
repl='''  (board.items || []).forEach(it => {\n    if ((hideDone && it.done) || (typeof itemHiddenByGroup === "function" && itemHiddenByGroup(it.id))) return;\n    const x = ox + it.x * sc, y = oy + it.y * sc;\n    c.fillRect(x, y, Math.max(2.2, it.w * sc), Math.max(2.2, it.h * sc));\n  });\n  c.globalAlpha = .45; c.strokeStyle = fg; c.lineWidth = 1;\n  (board.ink || []).forEach(st => {\n    const p=st && st.pts || []; if (p.length < 4) return;\n    c.beginPath(); c.moveTo(ox+p[0]*sc, oy+p[1]*sc);\n    for (let i=2;i<p.length;i+=2) c.lineTo(ox+p[i]*sc, oy+p[i+1]*sc);\n    c.stroke();\n  });\n  const s = Math.max(.05, view.s || 1);'''
html=rep(html,needle,repl,'minimap ink render')

# Photos cannot finish loading into a different board after the user switches projects.
html=rep(html,'function readImage(file, id, at) {\n  if (!file.type.startsWith("image/")) { toast("That file isn\'t a picture"); return; }\n  const original = file.size || 0;',
'''function readImage(file, id, at) {\n  if (!file.type.startsWith("image/")) { toast("That file isn't a picture"); return; }\n  const sourceBoardId = board && board.id;\n  const original = file.size || 0;''','image board capture')
html=rep(html,'img.onload = () => {\n      const room = storageBudget() - dbBytes();',
'''img.onload = () => {\n      if (!board || board.id !== sourceBoardId) { toast("Picture not added — you changed boards while it was loading. Try again on that board.", 4800); return; }\n      const room = storageBudget() - dbBytes();''','image board race')

# Keep chrome counts in sync after destructive/mass changes and duplication.
html=rep(html,'deselect(); drawThreads(); updateEmpty(); renderTimeline(); save();\n  toast(ids.length + " items removed");',
'''deselect(); drawThreads(); updateEmpty(); renderTimeline(); plate(); renderLegend(); renderMinimap(); save();\n  toast(ids.length + " items removed");''','removeMany chrome')
html=rep(html,'if (sel === id) deselect();\n  drawThreads(); updateEmpty(); renderTimeline(); save();\n}',
'''if (sel === id) deselect();\n  drawThreads(); updateEmpty(); renderTimeline(); plate(); renderLegend(); renderMinimap(); save();\n}''','removeItem chrome')
html=rep(html,'setMulti(made); save();\n    }','setMulti(made); plate(); renderLegend(); renderMinimap(); save();\n    }','multi duplicate chrome',1)
html=rep(html,'board.items.push(c); autoJoinItemToContainingSystem(c); makeEl(c); refresh(c.id); selectItem(c.id); save(); }',
'board.items.push(c); autoJoinItemToContainingSystem(c); makeEl(c); refresh(c.id); selectItem(c.id); plate(); renderLegend(); renderMinimap(); save(); }','single duplicate chrome',1)
html=rep(html,'board.items.push(c); autoJoinItemToContainingSystem(c); makeEl(c); refresh(c.id); selectItem(c.id); save(); return;',
'board.items.push(c); autoJoinItemToContainingSystem(c); makeEl(c); refresh(c.id); selectItem(c.id); plate(); renderLegend(); renderMinimap(); save(); return;','keyboard duplicate chrome',1)
html=rep(html,'drawThreads(); updateEmpty(); renderTimeline(); renderIdeaInbox(); save();\n  toast("Moved to Idea Inbox");',
'drawThreads(); updateEmpty(); renderTimeline(); renderIdeaInbox(); plate(); renderLegend(); renderMinimap(); save();\n  toast("Moved to Idea Inbox");','inbox removal chrome')

# Transactional import uses the serialized operation lane and a new revision.
import_new=r'''$("#jsonpick").addEventListener("change", e => {
  const f = e.target.files[0]; if (!f) return;
  const fr = new FileReader();
  fr.onload = async () => {
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
      clearTimeout(saveT);
      if (storageDirty && !await flushStorage()) {
        toast("Import cancelled — finish resolving the current storage error first.", 6200); return;
      }
      const candidate = Object.assign({}, DB, { boards:DB.boards.concat(staged) });
      candidate.storageRev = Math.max(+DB.storageRev || 0, storageRevision) + 1;
      let payload = JSON.stringify(candidate);
      if (!store.largeCapacity && payload.length * 2 > LEGACY_QUOTA * .96) {
        payload = null;
        toast("Import cancelled — this browser fell back to limited local storage. Export/remove a board or try a normal browser window.", 6200);
        return;
      }
      const persisted = await queueStorageOp(() => store.set(KEY, payload));
      payload = null;
      if (!persisted) {
        toast("Import cancelled — browser database storage could not be written. Your existing boards were left unchanged.", 6200);
        return;
      }
      DB.boards.push(...staged);
      DB.storageRev = candidate.storageRev; storageRevision = DB.storageRev;
      storageWriteBlocked = false; storageDirty = false;
      if (!store.persistent) flashSaved("not saved — private mode"); else flashSaved("saved");
      renderCases(); renderMeter();
      toast(staged.length + " board" + (staged.length > 1 ? "s" : "") + " imported");
    } catch (err) { toast("That file isn't a Pin It board"); }
  };
  fr.readAsText(f);
});'''
html=sub(html,r'\$\("#jsonpick"\)\.addEventListener\("change", e => \{.*?\n\}\);\n\n/\* ═══════════════ chrome wiring ═══════════════ \*/',import_new+'\n\n/* ═══════════════ chrome wiring ═══════════════ */','import block')

# New Board cancel is a real cancel.
html=rep(html,'$("#btn-newcase").addEventListener("click", () => {\n  const b = newBoard(prompt("Name this board", "New board") || "Untitled board");\n  DB.boards.push(b); save(true); switchBoard(b.id); closePanel("cases");\n});',
'''$("#btn-newcase").addEventListener("click", () => {\n  const name = prompt("Name this board", "New board"); if (name === null) return;\n  const b = newBoard(name.trim() || "Untitled board");\n  DB.boards.push(b); save(true); switchBoard(b.id); closePanel("cases");\n});''','new board cancel')

# Escape closes open chrome before clearing board modes.
html=rep(html,'if (e.key === "Escape") {\n    if (ideaDrawerOpen()) { toggleIdeaDrawer(false); return; }',
'''if (e.key === "Escape") {\n    if (ideaDrawerOpen()) { toggleIdeaDrawer(false); return; }\n    if ($("#outline").classList.contains("show")) { closePanel("outline"); return; }\n    if ($("#cases").classList.contains("show")) { closePanel("cases"); return; }''','escape panels')

# Onboarding example retains its system; cancelling a theme preview restores the real board theme.
html=rep(html,'board.items = seed.items; board.links = seed.links; board.inbox = seed.inbox || [];',
'board.items = seed.items; board.links = seed.links; board.inbox = seed.inbox || []; board.groups = seed.groups || []; board.tags = seed.tags || []; board.ink = seed.ink || [];','tour seed groups')
html=rep(html,'if (how !== "skip") {\n    if (name && name !== board.name) { board.name = name.slice(0, 60); plate(); }',
'''if (how !== "skip") {\n    if (name && name !== board.name) { board.name = name.slice(0, 60); plate(); }''','tour branch anchor')
html=rep(html,'  if (how === "example" && !board.items.length) {',
'  if (how === "skip") applyTheme();\n  if (how === "example" && !board.items.length) {','tour preview restore')

# Per-board backup timestamps.
html=rep(html,'markBackup();','markBackup(b);','download backup target',1)
html=rep(html,'markBackup();\n      return true;','markBackup(b);\n      return true;','share backup target',1)
backup_new=r'''function markBackup(b = board) { if (!b) return; b.lastBackup = Date.now(); save(true); renderMeter(); }
function backupAge(b = board) {
  if (!b || !b.lastBackup) return null;
  return Math.floor((Date.now() - b.lastBackup) / 86400000);
}
function backupLine() {
  const el = $("#backuplab"); if (!el) return;
  const d = backupAge(board);
  const total = board ? board.items.length : 0;
  let txt;
  if (!total) txt = "Nothing to back up yet.";
  else if (d === null) txt = "This board has never been backed up. Use Back up to keep a copy.";
  else if (d === 0) txt = "This board was backed up today.";
  else txt = `This board was last backed up ${d} day${d === 1 ? "" : "s"} ago.`;
  if (persisted === true) txt += " Storage is protected on this device.";
  el.textContent = txt;
  el.classList.toggle("stale", total > 0 && (d === null || d > 14));
  const btn = $("#btn-protect");
  if (btn) btn.style.display = persisted === true ? "none" : "";
}'''
html=sub(html,r'function markBackup\(\) \{.*?\n\}\nfunction backupAge\(\) \{.*?\n\}\nfunction backupLine\(\) \{.*?\n\}',backup_new,'backup functions')
html=rep(html,'const d = backupAge();','const d = backupAge(board);','safety backup age',1)

# Flush promptly on lifecycle exits; still best-effort because browsers cannot synchronously wait on IndexedDB.
html=rep(html,'addEventListener("beforeunload", () => save(true));\ndocument.addEventListener("visibilitychange", () => { if (document.hidden) save(true); });',
'''const flushForExit = () => { clearTimeout(saveT); if (board) { storageDirty = true; void flushStorage(); } };\naddEventListener("beforeunload", flushForExit);\naddEventListener("pagehide", flushForExit);\ndocument.addEventListener("visibilitychange", () => { if (document.hidden) flushForExit(); });''','exit flushing')

# README correction for 1.9.4 minimap behaviour.
readme=rep(readme,'The map updates while you pan and zoom. It opens by default on desktop, can be collapsed at any time, and starts collapsed on narrow/mobile screens so it does not take over the working area.',
'The map updates while you pan and zoom. It starts collapsed on desktop and mobile so it never takes over the working area; open or close it at any time from the map button.','README minimap')

# Changelog
entry='''---\n\n## 1.9.5 — 15 September 2026, 14:08 UTC\n\n- Hardened IndexedDB/localStorage reconciliation so an old fallback copy cannot silently replace newer IndexedDB data after a storage error.\n- Replaced the old queued full-database payloads with a **coalescing latest-state writer**, preventing rapid edits from accumulating multiple large serialized database copies in memory.\n- Added a monotonically increasing storage revision used by migration/reconciliation.\n- Expanded undo/redo snapshots to restore board tags and whole-board text/theme metadata, and prune image payloads once no remaining undo/redo state references them.\n- Backup timestamps are now **per board** rather than global, so backing up one project no longer marks unrelated boards as backed up.\n- **Hide Done** now hides connected strings/relationship labels and omits hidden finished items from board-fit extents.\n- Freehand drawings now contribute to Board Map bounds and appear in the minimap.\n- Fixed an asynchronous photo load being able to land on a different board after switching projects.\n- Refreshed progress/tag/minimap chrome after deletes, duplications, inbox moves and undo/redo so counts do not remain stale.\n- The onboarding example now retains its example system; cancelling onboarding after previewing another theme restores the actual board theme.\n- Cancelling **New board** no longer creates an Untitled board, and Escape now closes the Board Outline/Boards drawer first.\n- Added page-hide save flushing and corrected README Board Map behaviour.\n\n## 1.9.4 —'''
log=sub(log,r'---\n\n## 1\.9\.4 —',entry,'changelog')

INDEX.write_text(html,encoding='utf-8'); CHANGELOG.write_text(log,encoding='utf-8'); README.write_text(readme,encoding='utf-8')

# Verification pass 1: parse every inline script.
scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',html,re.S|re.I)
with tempfile.TemporaryDirectory() as td:
  for i,s in enumerate(scripts):
    p=Path(td)/f's{i}.js'; p.write_text(s,encoding='utf-8'); subprocess.run(['node','--check',str(p)],check=True)

# Verification pass 2: stability contracts.
checks={
 'version': 'const VERSION = "1.9.5";' in html,
 'revisioned-storage': 'payloadStamp(raw)' in html and 'DB.storageRev' in html,
 'no-idb-stale-fallback': 'Once IndexedDB has opened/held real data' in html,
 'coalesced-writer': 'while (storageDirty && !storageWriteBlocked)' in html and 'queueStorageOp(fn)' in html,
 'no-old-payload-queue': 'queueStorageWrite(payload)' not in html,
 'undo-tags': 'tags:board.tags' in html and 'board.tags = d.tags || []' in html,
 'undo-fs': 'fs:board.fs' in html and 'board.fs = +d.fs' in html,
 'undo-prune': 'function pruneUndoMedia()' in html,
 'per-board-backup': 'b.lastBackup = Date.now()' in html and 'DB.lastBackup = Date.now()' not in html,
 'hide-done-lines': 'hideDone && ((byId(l.a) && byId(l.a).done)' in html,
 'hide-done-extents': 'itemHiddenByGroup(i.id) || (hideDone && i.done)' in html,
 'minimap-ink': '(board.ink || []).forEach(st =>' in html,
 'image-race': 'sourceBoardId' in html and 'you changed boards while it was loading' in html,
 'tour-system': 'board.groups = seed.groups || []' in html,
 'tour-preview': 'if (how === "skip") applyTheme();' in html,
 'cancel-new-board': 'if (name === null) return;' in html,
 'escape-outline': '$("#outline").classList.contains("show")' in html,
 'pagehide': 'addEventListener("pagehide", flushForExit);' in html,
 'readme-map': 'It starts collapsed on desktop and mobile' in readme,
 'changelog': '## 1.9.5 — 15 September 2026, 14:08 UTC' in log,
}
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('verification failed: '+', '.join(failed))
print(f'Pin It 1.9.5 verified: {len(scripts)} scripts parsed, {len(checks)} reliability checks passed')
