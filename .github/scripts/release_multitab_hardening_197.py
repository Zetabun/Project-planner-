from pathlib import Path
import re, subprocess, tempfile

INDEX=Path('index.html'); CHANGELOG=Path('CHANGELOG.md')
html=INDEX.read_text(encoding='utf-8'); log=CHANGELOG.read_text(encoding='utf-8')

def rep(text, old, new, label, count=1):
    n=text.count(old)
    if n!=count: raise SystemExit(f'{label}: expected {count}, found {n}')
    return text.replace(old,new,count)

# release metadata
html=rep(html,'Version 1.9.6 · 15 September 2026, 14:17 UTC','Version 1.9.7 · 15 September 2026, 14:23 UTC','header')
html=rep(html,'const VERSION = "1.9.6";','const VERSION = "1.9.7";','version')
html=rep(html,'const BUILD = "15 September 2026, 14:17 UTC";','const BUILD = "15 September 2026, 14:23 UTC";','build')
release='''  {\n    version: "1.9.7", date: "15 September 2026, 14:23 UTC",\n    summary: "A follow-up hardening pass closes duplicate-tab and reload edge cases found while second-checking the new single-writer protection.",\n    items: [\n      "Tab writer IDs are now unique per document rather than stored as the tab session ID, so browser Duplicate Tab behaviour cannot accidentally give two live pages the same save identity.",\n      "Normal reloads use a one-shot predecessor handoff token to reclaim their own lease without weakening duplicate-tab detection.",\n      "Initial database loading now participates in the cross-tab Web Lock where supported, reducing reload races with an in-flight save from the page being replaced.",\n      "Fresh/recreated databases can reset an orphaned revision marker when no active writer exists, avoiding a stale local marker trapping an empty recovered app in read-only mode."\n    ]\n  },\n'''
html=rep(html,'const RELEASES = [\n','const RELEASES = [\n'+release,'release entry')

old_id='''const TAB_STARTED_AT = Date.now();\nlet tabGuardStarted = false, tabReadOnly = false, tabLeaseTimer = null, tabChannel = null;\nlet tabLeaseStorageOK = true, tabForceTakeover = false;\nlet TAB_ID = "";\ntry {\n  TAB_ID = sessionStorage.getItem("pinit.tabId.v1") || (Date.now().toString(36) + "-" + Math.random().toString(36).slice(2));\n  sessionStorage.setItem("pinit.tabId.v1", TAB_ID);\n  tabForceTakeover = sessionStorage.getItem("pinit.tabTakeover.v1") === "1";\n  sessionStorage.removeItem("pinit.tabTakeover.v1");\n} catch (e) {\n  TAB_ID = Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);\n}'''
new_id='''const TAB_STARTED_AT = Date.now();\nlet tabGuardStarted = false, tabReadOnly = false, tabLeaseTimer = null, tabChannel = null;\nlet tabLeaseStorageOK = true, tabForceTakeover = false, tabPreviousId = "";\nconst TAB_ID = (typeof crypto !== "undefined" && crypto.randomUUID)\n  ? crypto.randomUUID()\n  : (Date.now().toString(36) + "-" + Math.random().toString(36).slice(2) + "-" + Math.random().toString(36).slice(2));\ntry {\n  tabForceTakeover = sessionStorage.getItem("pinit.tabTakeover.v1") === "1";\n  tabPreviousId = sessionStorage.getItem("pinit.tabPrev.v1") || "";\n  sessionStorage.removeItem("pinit.tabTakeover.v1");\n  sessionStorage.removeItem("pinit.tabPrev.v1");\n} catch (e) {}'''
html=rep(html,old_id,new_id,'unique document tab id')

# Treat a reload successor specially, but only if the active lease belongs to its exact predecessor.
old_init='''  if (readExternalRevision() > (+storageRevision || 0)) {\n    setTabReadOnly(true, "A newer saved revision already exists. Reload this tab before making changes.");\n    return false;\n  }\n  const cur = readTabLease();\n  if (!tabForceTakeover && tabLeaseFresh(cur) && cur.id !== TAB_ID) {\n    setTabReadOnly(true, "Pin It is already open in another tab. This copy is read-only to prevent one tab overwriting the other.");\n  } else {\n    writeTabLease(!!tabForceTakeover);\n    tabForceTakeover = false;'''
new_init='''  let cur = readTabLease();\n  const ownReload = !!(tabPreviousId && cur && cur.id === tabPreviousId);\n  if (FRESH && !tabLeaseFresh(cur) && tabLeaseStorageOK) {\n    try { localStorage.setItem(TAB_REV_KEY, String(+storageRevision || 0)); } catch (e) {}\n  }\n  if (!ownReload && readExternalRevision() > (+storageRevision || 0)) {\n    setTabReadOnly(true, "A newer saved revision already exists. Reload this tab before making changes.");\n    return false;\n  }\n  cur = readTabLease();\n  if (!tabForceTakeover && !ownReload && tabLeaseFresh(cur) && cur.id !== TAB_ID) {\n    setTabReadOnly(true, "Pin It is already open in another tab. This copy is read-only to prevent one tab overwriting the other.");\n  } else {\n    writeTabLease(!!tabForceTakeover || ownReload);\n    tabForceTakeover = false; tabPreviousId = "";'''
html=rep(html,old_init,new_init,'reload lease handoff')

# Before navigation/reload, leave a one-shot predecessor identity in this browsing context.
old_lifecycle='''const flushForExit = () => { clearTimeout(saveT); if (board) { storageDirty = true; void flushStorage(); } };\naddEventListener("beforeunload", flushForExit);\naddEventListener("pagehide", flushForExit);'''
new_lifecycle='''const flushForExit = () => { clearTimeout(saveT); if (board && !tabReadOnly) { storageDirty = true; void flushStorage(); } };\nconst markTabPredecessor = () => { try { sessionStorage.setItem("pinit.tabPrev.v1", TAB_ID); } catch (e) {} };\naddEventListener("beforeunload", flushForExit);\naddEventListener("beforeunload", markTabPredecessor);\naddEventListener("pagehide", flushForExit);\naddEventListener("pagehide", markTabPredecessor);'''
html=rep(html,old_lifecycle,new_lifecycle,'reload predecessor marker')

# Serialize startup with any in-flight writer before reading IndexedDB.
html=rep(html,'(async function bootPinIt() {\n  await load();\n  initTabGuard();',
'''(async function bootPinIt() {\n  await withCrossTabStorageLock(() => load());\n  initTabGuard();''','locked boot load')

# Changelog
entry='''---\n\n## 1.9.7 — 15 September 2026, 14:23 UTC\n\n- Follow-up hardening for the new multi-tab safety system.\n- Writer IDs are now **unique per loaded document**. They are no longer persisted as a session tab ID, because some browsers copy `sessionStorage` when duplicating a tab and could otherwise give two live pages the same writer identity.\n- Added a one-shot predecessor token so a normal refresh/reload can reclaim the exact lease owned by the document it replaced without making duplicated tabs writable.\n- Startup now reads IndexedDB inside the same cross-tab **Web Lock** used for writes when supported, reducing a reload race with an in-flight exit save.\n- A genuinely fresh/recreated database can clear an orphaned saved-revision marker when there is no active tab lease, preventing a stale marker from trapping an empty recovery state in read-only mode.\n\n## 1.9.6 — 15 September 2026, 14:17 UTC'''
log=rep(log,'---\n\n## 1.9.6 — 15 September 2026, 14:17 UTC',entry,'changelog')

INDEX.write_text(html,encoding='utf-8'); CHANGELOG.write_text(log,encoding='utf-8')

# parse all inline scripts
scripts=re.findall(r'<script(?:\\s[^>]*)?>(.*?)</script>',html,re.S|re.I)
with tempfile.TemporaryDirectory() as td:
    for i,s in enumerate(scripts):
        p=Path(td)/f's{i}.js'; p.write_text(s,encoding='utf-8'); subprocess.run(['node','--check',str(p)],check=True)

checks={
 'version':'const VERSION = "1.9.7";' in html,
 'release':'version: "1.9.7", date: "15 September 2026, 14:23 UTC"' in html,
 'changelog':'## 1.9.7 — 15 September 2026, 14:23 UTC' in log,
 'no-persisted-tab-id':'pinit.tabId.v1' not in html,
 'random-doc-id':'crypto.randomUUID' in html,
 'predecessor-read':'sessionStorage.getItem("pinit.tabPrev.v1")' in html,
 'predecessor-write':'sessionStorage.setItem("pinit.tabPrev.v1", TAB_ID)' in html,
 'own-reload':'const ownReload = !!(tabPreviousId && cur && cur.id === tabPreviousId);' in html,
 'locked-load':'await withCrossTabStorageLock(() => load());' in html,
 'fresh-marker-recovery':'if (FRESH && !tabLeaseFresh(cur) && tabLeaseStorageOK)' in html,
}
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('hardening checks failed: '+', '.join(failed))
print(f'Pin It 1.9.7 verified: {len(scripts)} inline scripts parse; {len(checks)} hardening checks passed')
