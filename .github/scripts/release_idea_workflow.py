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


def insert_before_once(text, marker, addition, label):
    count = text.count(marker)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one marker, found {count}")
    return text.replace(marker, addition + marker, 1)


def replace_span(text, start, end, replacement, label):
    i = text.find(start)
    if i < 0:
        raise SystemExit(f"{label}: start marker not found")
    j = text.find(end, i + len(start))
    if j < 0:
        raise SystemExit(f"{label}: end marker not found")
    if text.find(start, i + len(start)) >= 0 and text.find(start, i + len(start)) < j:
        raise SystemExit(f"{label}: ambiguous start marker")
    return text[:i] + replacement + text[j:]


# ---------------------------------------------------------------------------
# Release metadata
# ---------------------------------------------------------------------------
html = replace_once(
    html,
    "Version 1.4.2 · 14 September 2026, 21:55 UTC",
    "Version 1.5.0 · 14 September 2026, 22:01 UTC",
    "header version",
)
html = replace_once(html, 'const VERSION = "1.4.2";', 'const VERSION = "1.5.0";', "VERSION")
html = replace_once(
    html,
    'const BUILD = "14 September 2026, 21:55 UTC";',
    'const BUILD = "14 September 2026, 22:01 UTC";',
    "BUILD",
)

release = '''  {
    version: "1.5.0", date: "14 September 2026, 22:01 UTC",
    summary: "Ideas now have a clear workflow: capture them first, organise them by role, then connect them with meaningful relationships.",
    items: [
      "Added a collapsible per-board Idea Inbox on the right for quick capture, with touch/mouse drag-out placement plus Feature and Note actions.",
      "Feature cards, detail notes, implementation checklists and area tags now form an explicit planning model taught in onboarding.",
      "Creating a connection now asks whether it Expands into, Depends on, Affects, is Blocked by, or is simply Related to the second item.",
      "Relationship choices automatically set useful labels, colours and solid/dashed line styles, and can be changed later from the connection menu.",
      "Items can be moved back into the Idea Inbox when they are not ready to live on the board yet.",
      "Expanded the Getting Started flow to teach the Idea Inbox, item roles and relationship system."
    ]
  },
'''
html = replace_once(html, "const RELEASES = [\n", "const RELEASES = [\n" + release, "release history")

# ---------------------------------------------------------------------------
# Styling for Idea Inbox, relationship picker and onboarding additions.
# ---------------------------------------------------------------------------
extra_css = r'''

/* ───────────── idea workflow / inbox ───────────── */
#idea-tab{position:fixed; right:8px; top:48%; z-index:27; width:50px; min-height:66px; padding:7px 5px;
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:4px;
  border:1px solid var(--ui-line); border-radius:6px; color:var(--ui-fg);
  background:linear-gradient(180deg,var(--ui-1),var(--ui-2)); box-shadow:0 7px 20px var(--ui-drop);
  transition:opacity .18s,transform .18s}
#idea-tab svg{width:20px;height:20px}
#idea-tab span{font-size:9px; font-weight:800; letter-spacing:.09em; text-transform:uppercase}
#idea-tab b{min-width:20px; height:20px; padding:0 5px; display:grid; place-items:center; border-radius:11px;
  background:var(--ui-hi); border:1px solid var(--ui-line); font-size:10px; font-weight:800}
body.ideas-open #idea-tab{opacity:0; pointer-events:none; transform:translateX(14px)}
#idea-drawer{position:fixed; z-index:46; right:0; top:calc(var(--safe-t) + 72px); bottom:calc(var(--safe-b) + 76px);
  width:min(360px,90vw); display:flex; flex-direction:column; color:var(--pan-fg);
  background:linear-gradient(180deg,var(--sheet-2),var(--sheet)); border-left:1px solid var(--pan-line);
  box-shadow:-18px 0 42px rgba(0,0,0,.28); transform:translateX(104%);
  transition:transform .25s cubic-bezier(.2,.8,.25,1); pointer-events:none}
#idea-drawer.show{transform:translateX(0); pointer-events:auto}
#idea-drawer header{display:flex; align-items:center; justify-content:space-between; padding:13px 14px 10px;
  border-bottom:1px solid var(--pan-line)}
#idea-drawer header h2{margin:0; font-family:var(--type); font-size:17px; letter-spacing:.02em}
.idea-intro{padding:10px 14px 0; color:var(--pan-sub); font-size:12px; line-height:1.45}
#idea-form{display:flex; gap:7px; padding:10px 14px 12px; border-bottom:1px solid var(--pan-line)}
#idea-input{flex:1; min-width:0; min-height:42px; max-height:90px; resize:vertical; border:1px solid var(--pan-line);
  background:var(--in-bg); color:var(--in-fg); border-radius:4px; padding:9px 10px; font-size:13px; line-height:1.35}
#idea-form .btn{align-self:stretch; padding-inline:12px}
#idea-list{flex:1; overflow:auto; padding:11px 12px 18px; -webkit-overflow-scrolling:touch}
.idea-empty{padding:22px 10px; text-align:center; color:var(--pan-hint); font-size:12px; line-height:1.5}
.idea-card{position:relative; margin:0 0 9px; padding:11px 10px 9px; border:1px solid var(--pan-line); border-radius:5px;
  background:var(--pan-soft); box-shadow:0 3px 9px rgba(0,0,0,.12); touch-action:none; user-select:none; -webkit-user-select:none}
.idea-card:active{background:var(--pan-soft2)}
.idea-text{font-family:var(--hand); font-size:18px; line-height:1.24; overflow-wrap:anywhere; white-space:pre-wrap}
.idea-kind{margin-top:5px; color:var(--pan-hint); font:700 9px/1 var(--ui); letter-spacing:.09em; text-transform:uppercase}
.idea-actions{display:flex; gap:6px; margin-top:9px; align-items:center}
.idea-actions button{border:1px solid var(--pan-line); border-radius:4px; padding:6px 8px; color:var(--pan-fg);
  background:var(--pan-soft); font-size:10.5px; font-weight:700}
.idea-actions button:hover{background:var(--pan-soft2)}
.idea-actions .idea-del{margin-left:auto; width:29px; padding:6px 0; font-size:15px; color:var(--pan-sub)}
.idea-foot{padding:9px 14px 11px; border-top:1px solid var(--pan-line); color:var(--pan-hint); font-size:10.5px; line-height:1.4}
.idea-ghost{position:fixed; z-index:90; width:min(220px,58vw); max-height:130px; overflow:hidden; pointer-events:none;
  transform:translate(-50%,-50%) rotate(-2deg); padding:12px 13px; border-radius:4px; font-family:var(--hand); font-size:18px;
  color:var(--ink); background:#f7e06a; box-shadow:0 18px 38px rgba(0,0,0,.35); opacity:.94}
body[data-theme="white"] .idea-ghost{background:#fbfaf6}
body[data-theme="blueprint"] .idea-ghost{background:#19476b; color:#edf7ff; border:1px solid #73b3cf}
body.idea-dragging #idea-drawer{opacity:.88}

/* relationship chooser */
#ctx .ctx-rel-head{padding:7px 9px 5px; max-width:280px}
#ctx .ctx-rel-head b{display:block; color:var(--pan-head); font-size:12px; margin-bottom:3px}
#ctx .ctx-rel-head span{display:block; color:var(--pan-sub); font-size:10.5px; line-height:1.35}
#ctx button.rel-choice{align-items:flex-start; min-width:250px; padding-top:8px; padding-bottom:8px}
.rel-dot{width:11px; height:11px; margin-top:3px; border-radius:50%; flex:none; background:var(--relc); box-shadow:0 0 0 2px var(--pan-soft2)}
.rel-copy{display:flex; flex-direction:column; gap:1px; min-width:0}
.rel-copy b{font-size:12px; font-weight:800; color:var(--pan-fg)}
.rel-copy small{font-size:10px; line-height:1.3; color:var(--pan-sub); white-space:normal}
.tlabel.typed{border:1px solid var(--relc); box-shadow:0 2px 7px rgba(0,0,0,.16); font-weight:700}

/* onboarding planning model */
.tips.modeltips li{align-items:flex-start}
.tips .mini-rel{display:flex; flex-wrap:wrap; gap:5px; margin-top:6px}
.tips .mini-rel i{font-style:normal; border:1px solid var(--pan-line); border-radius:10px; padding:2px 7px;
  font:700 9px/1.2 var(--ui); color:var(--pan-sub); background:var(--pan-soft)}

@media(max-width:720px){
  #idea-tab{right:6px; top:50%; width:45px; min-height:61px}
  #idea-drawer{top:calc(var(--safe-t) + 68px); bottom:calc(var(--safe-b) + 72px); width:min(86vw,330px)}
  .idea-text{font-size:17px}
  #ctx button.rel-choice{min-width:min(250px,76vw)}
}
'''
html = replace_once(html, "</style>", extra_css + "\n</style>", "main stylesheet")

# ---------------------------------------------------------------------------
# HTML: tool naming, Idea Inbox drawer and richer onboarding.
# ---------------------------------------------------------------------------
html = replace_once(
    html,
    '<button class="tool" data-add="card"><svg><use href="#i-card"/></svg><span class="tip">Index card</span></button>',
    '<button class="tool" data-add="card"><svg><use href="#i-card"/></svg><span class="tip">Feature card</span></button>',
    "feature-card tool label",
)
html = replace_once(
    html,
    '<button class="tool" id="btn-link"><svg><use href="#i-string"/></svg><span class="tip">Run string (L)</span></button>',
    '<button class="tool" id="btn-link"><svg><use href="#i-string"/></svg><span class="tip">Connect ideas (L)</span></button>',
    "connection tool label",
)

idea_markup = r'''<button id="idea-tab" type="button" title="Idea Inbox (I)" aria-label="Open Idea Inbox" aria-controls="idea-drawer" aria-expanded="false">
  <svg><use href="#i-sticky"/></svg><span>Ideas</span><b id="idea-count">0</b>
</button>
<aside id="idea-drawer" aria-label="Idea Inbox" aria-hidden="true">
  <header>
    <h2>Idea Inbox</h2>
    <button class="xbtn" id="idea-close" aria-label="Close Idea Inbox"><svg width="18" height="18"><use href="#i-x"/></svg></button>
  </header>
  <div class="idea-intro"><b>Capture first. Organise later.</b><br>Keep loose thoughts here until they are ready for the board.</div>
  <form id="idea-form">
    <textarea id="idea-input" maxlength="400" rows="2" placeholder="Quick thought…"></textarea>
    <button class="btn primary" type="submit">Add</button>
  </form>
  <div id="idea-list"></div>
  <div class="idea-foot">Drag an idea onto the board, or use <b>Feature</b> for a main idea and <b>Note</b> for a detail, behaviour or question.</div>
</aside>

'''
html = replace_once(
    html,
    '</aside>\n\n<div id="tourwrap" hidden>',
    '</aside>\n\n' + idea_markup + '<div id="tourwrap" hidden>',
    "Idea Inbox markup",
)

html = replace_once(
    html,
    '<div class="tourhead"><span class="brand">Pin&nbsp;It</span><div class="dots"><i></i><i></i><i></i></div></div>',
    '<div class="tourhead"><span class="brand">Pin&nbsp;It</span><div class="dots"><i></i><i></i><i></i><i></i></div></div>',
    "tour dots",
)

old_step3 = r'''    <section data-step="3">
      <h2>A few things to know</h2>
      <ul class="tips">
        <li><svg><use href="#i-sticky"/></svg><div><b>Put things up</b>Pick from the tool rail. Double-tap to write, drag to move, pull the corner to resize.</div></li>
        <li><svg><use href="#i-string"/></svg><div><b>Join them up</b>Tap the string tool, then tap two items. Tap the string itself to label or cut it.</div></li>
        <li><svg><use href="#i-cal"/></svg><div><b>Keep track</b>Give things a due date, stamp them Urgent or Done, tick off checklists.</div></li>
        <li class="ink"><svg><use href="#i-pen"/></svg><div><b>Write on the board</b>The pen tool lets you scribble straight onto the whiteboard or blueprint board in marker — arrows, circles, a quick note in your own hand.</div></li>
      </ul>
      <p class="hint">Everything saves in this browser as you go. No account, no upload.</p>
      <div class="tourfoot" id="tour-end"></div>
    </section>'''
new_steps = r'''    <section data-step="3">
      <h2>Give each thing one job</h2>
      <p class="lead">The board stays readable when the shape of an item tells you what it means.</p>
      <ul class="tips modeltips">
        <li><svg><use href="#i-card"/></svg><div><b>Feature card = the main idea</b>A system, feature or outcome worth building around. Other thoughts can branch from it.</div></li>
        <li><svg><use href="#i-sticky"/></svg><div><b>Sticky note = a detail</b>A behaviour, refinement, question, rule or observation that explains a feature.</div></li>
        <li><svg><use href="#i-list"/></svg><div><b>Checklist = implementation work</b>Concrete steps needed to make an idea real.</div></li>
        <li><svg><use href="#i-tags"/></svg><div><b>Tags = areas of the project</b>Use them for Engine, Sound, Environment or whatever systems an idea touches.</div></li>
      </ul>
      <div class="tourfoot"><button class="btn" data-back>Back</button><button class="btn primary" data-next>Next</button></div>
    </section>

    <section data-step="4">
      <h2>Capture first, connect second</h2>
      <ul class="tips">
        <li><svg><use href="#i-sticky"/></svg><div><b>Use the Idea Inbox</b>Open the drawer on the right, jot down rough thoughts, then drag them onto the board when you are ready to organise them.</div></li>
        <li><svg><use href="#i-string"/></svg><div><b>Say why two things connect</b>After choosing two items, Pin It asks what the relationship means.<span class="mini-rel"><i>Expands into</i><i>Depends on</i><i>Affects</i><i>Blocked by</i></span></div></li>
        <li><svg><use href="#i-cal"/></svg><div><b>Then make it actionable</b>Add due dates, stamps and checklists once an idea becomes work you actually intend to do.</div></li>
        <li class="ink"><svg><use href="#i-pen"/></svg><div><b>Keep capture loose</b>Not every thought needs a connection. If you cannot finish “this idea ___ that idea”, leave it unlinked for now.</div></li>
      </ul>
      <p class="hint">Everything saves in this browser as you go. No account, no upload.</p>
      <div class="tourfoot" id="tour-end"></div>
    </section>'''
html = replace_once(html, old_step3, new_steps, "onboarding planning model")

# ---------------------------------------------------------------------------
# Data model: roles, relationships and per-board inbox.
# ---------------------------------------------------------------------------
html = replace_once(
    html,
    'const TYPE_NAMES = { photo: "Photo", sticky: "Sticky note", card: "Index card", doc: "Report", list: "Checklist", tag: "Evidence tag", marker: "Marker text" };',
    'const TYPE_NAMES = { photo: "Photo", sticky: "Detail note", card: "Feature card", doc: "Report", list: "Implementation checklist", tag: "Area tag", marker: "Marker text" };',
    "item role names",
)
html = replace_once(
    html,
    'card:   { w: 250, h: 160, title: "Untitled", text: "" },',
    'card:   { w: 250, h: 160, title: "New feature", text: "" },',
    "feature default title",
)

relation_code = r'''const RELATIONS = {
  expands: { name: "Expands into", label: "expands into", color: "navy", style: "solid", help: "The second item develops or breaks out this idea." },
  depends: { name: "Depends on", label: "depends on", color: "gold", style: "dashed", help: "This idea needs the second item to happen." },
  affects: { name: "Affects", label: "affects", color: "green", style: "solid", help: "These ideas influence one another without owning each other." },
  blocked: { name: "Blocked by", label: "blocked by", color: "red", style: "dashed", help: "The second item is preventing this idea from moving forward." },
  related: { name: "Related to", label: "related to", color: null, style: null, help: "They belong together, but none of the other relationships fits." }
};
const relationKeyFromLabel = label => Object.keys(RELATIONS).find(k => RELATIONS[k].label === label) || null;

'''
html = insert_before_once(html, 'const isWhite = () => !!board && board.theme === "white";', relation_code, "relationship constants")

html = replace_once(
    html,
    'items: [], links: [], ink: [], tags: [], view: { x: 0, y: 0, s: 1 }',
    'items: [], links: [], ink: [], tags: [], inbox: [], view: { x: 0, y: 0, s: 1 }',
    "new board inbox",
)
html = replace_once(
    html,
    '  if (!Array.isArray(b.tags)) b.tags = [];\n',
    '  if (!Array.isArray(b.tags)) b.tags = [];\n  if (!Array.isArray(b.inbox)) b.inbox = [];\n',
    "normalise inbox",
)
html = replace_once(
    html,
    '  b.links = b.links.filter(l => l && ids.has(l.a) && ids.has(l.b));   // drop strings to nothing\n  return b;',
    '  b.links = b.links.filter(l => l && ids.has(l.a) && ids.has(l.b));   // drop strings to nothing\n  b.links.forEach(l => { if (!l.rel || !RELATIONS[l.rel]) l.rel = relationKeyFromLabel(l.label) || "related"; });\n  b.inbox = b.inbox.filter(i => i && i.id && String(i.text || "").trim()).map(i => ({ id: i.id, text: String(i.text).slice(0, 400), kind: i.kind === "card" ? "card" : "sticky", created: +i.created || Date.now() }));\n  return b;',
    "normalise relationships and inbox",
)

# Undo/redo should include inbox changes too.
html = replace_once(
    html,
    'history.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink }));',
    'history.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox }));',
    "undo snapshot",
)
html = replace_once(
    html,
    'const d = JSON.parse(s); board.items = d.items; board.links = d.links; board.ink = d.ink || [];',
    'const d = JSON.parse(s); board.items = d.items; board.links = d.links; board.ink = d.ink || []; board.inbox = d.inbox || [];',
    "apply undo snapshot",
)
html = replace_once(
    html,
    'future.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink }));',
    'future.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox }));',
    "redo future snapshot",
)
# The redo function contains the same history snapshot text after snap() was already changed,
# so update the remaining occurrence explicitly.
html = replace_once(
    html,
    'history.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink }));',
    'history.push(JSON.stringify({ items: board.items, links: board.links, ink: board.ink, inbox: board.inbox }));',
    "redo history snapshot",
)

# Update the example board to teach the new model.
html = replace_once(
    html,
    'const b = { theme: "cork", id: uid(), name: "The Greenhouse Job", no: "NO. 001", created: Date.now(), updated: Date.now(), items: [], links: [], ink: [], tags: [], view: { x: 0, y: 0, s: 1 } };',
    'const b = { theme: "cork", id: uid(), name: "The Greenhouse Job", no: "NO. 001", created: Date.now(), updated: Date.now(), items: [], links: [], ink: [], tags: [], inbox: [], view: { x: 0, y: 0, s: 1 } };',
    "seed inbox",
)
html = replace_once(
    html,
    'const brief = it("card", 180, 220, { title: "The brief", text: "Drag things around. Double-tap to write.", rot: -2.2 });',
    'const brief = it("card", 180, 220, { title: "Main feature", text: "Feature cards hold the big idea. Details can branch away from them.", rot: -2.2 });',
    "seed feature card",
)
html = replace_once(
    html,
    'const string = it("sticky", 520, 210, { text: "Tap the string tool, then tap two pins to tie them together.", color: STICKY[2], rot: 2.6 });',
    'const string = it("sticky", 520, 210, { text: "Connect two items, then choose why they relate: expands, depends on, affects or blocked by.", color: STICKY[2], rot: 2.6 });',
    "seed relationship note",
)
html = replace_once(
    html,
    'title: "This week", rot: 1.4,\n    tasks: [{ t: "Pin the big idea", done: true }, { t: "Break it into parts", done: false }, { t: "Connect what depends on what", done: false }]',
    'title: "Implementation", rot: 1.4,\n    tasks: [{ t: "Define the feature", done: true }, { t: "Break it into details", done: false }, { t: "Turn the useful bits into work", done: false }]',
    "seed implementation checklist",
)
html = replace_once(
    html,
    'const risk = it("sticky", 560, 450, { text: "Anything unresolved goes on a sticky and gets a stamp.", color: STICKY[1], rot: -2.4, stamp: "urgent" });',
    'const risk = it("sticky", 560, 450, { text: "Loose thoughts can wait in the Idea Inbox until you know where they belong.", color: STICKY[1], rot: -2.4, stamp: "idea" });',
    "seed inbox note",
)
old_seed_links = r'''  b.links.push(
    { id: uid(), a: head.id, b: brief.id, color: "red", style: "solid", label: "" },
    { id: uid(), a: brief.id, b: string.id, color: "red", style: "solid", label: "then" },
    { id: uid(), a: brief.id, b: plan.id, color: "navy", style: "dashed", label: "breaks down into" },
    { id: uid(), a: string.id, b: risk.id, color: "red", style: "solid", label: "" },
    { id: uid(), a: risk.id, b: tag.id, color: "gold", style: "dashed", label: "blocked by" }
  );
  return b;'''
new_seed_links = r'''  b.links.push(
    { id: uid(), a: head.id, b: brief.id, rel: "related", color: "red", style: "solid", label: "related to" },
    { id: uid(), a: brief.id, b: string.id, rel: "expands", color: "navy", style: "solid", label: "expands into" },
    { id: uid(), a: brief.id, b: plan.id, rel: "depends", color: "gold", style: "dashed", label: "depends on" },
    { id: uid(), a: string.id, b: risk.id, rel: "affects", color: "green", style: "solid", label: "affects" },
    { id: uid(), a: risk.id, b: tag.id, rel: "blocked", color: "red", style: "dashed", label: "blocked by" }
  );
  b.inbox.push({ id: uid(), text: "Could this feature react differently at night?", kind: "sticky", created: Date.now() });
  return b;'''
html = replace_once(html, old_seed_links, new_seed_links, "seed relationships")

# ---------------------------------------------------------------------------
# Rendering: role language, relationship labels and inbox refresh.
# ---------------------------------------------------------------------------
html = replace_once(
    html,
    'return `<div class="ttl">${esc(it.title || "Untitled")}</div><div class="tx">${body(it, "What\'s the detail?")}</div>`;',
    'return `<div class="ttl">${esc(it.title || "New feature")}</div><div class="tx">${body(it, "What does this feature do?")}</div>`;',
    "feature card rendering",
)

html = replace_once(
    html,
    '  drawInk(); drawThreads(); updateEmpty(); renderLegend(); applyFilter();\n}',
    '  drawInk(); drawThreads(); updateEmpty(); renderLegend(); applyFilter();\n  if (typeof renderIdeaInbox === "function") renderIdeaInbox();\n}',
    "render inbox with board",
)
html = replace_once(
    html,
    'e.innerHTML = `<h3>Nothing pinned yet</h3><p>Start with a sticky note or a photo from the tools, then run string between them.</p>`;',
    'e.innerHTML = `<h3>Nothing pinned yet</h3><p>Start with a feature card or detail note — or capture loose thoughts in the Idea Inbox first.</p>`;',
    "empty board guidance",
)

old_label = '''    n.className = "tlabel"; n.textContent = l.label; n.dataset.link = l.id;
    n.style.left = mid.x + "px"; n.style.top = mid.y + "px";
    n.style.setProperty("--rot", (((l.id.charCodeAt(0) % 7) - 3)) + "deg");
    world.appendChild(n);'''
new_label = '''    const rel = l.rel || "related";
    n.className = "tlabel" + (rel !== "related" ? " typed rel-" + rel : ""); n.textContent = l.label; n.dataset.link = l.id;
    n.dataset.rel = rel;
    n.style.left = mid.x + "px"; n.style.top = mid.y + "px";
    n.style.setProperty("--rot", (((l.id.charCodeAt(0) % 7) - 3)) + "deg");
    if (rel !== "related") n.style.setProperty("--relc", threadCol(l.color));
    world.appendChild(n);'''
html = replace_once(html, old_label, new_label, "typed relationship labels")

# ---------------------------------------------------------------------------
# Connection workflow: ask what the line means after the two endpoints.
# ---------------------------------------------------------------------------
complete_replacement = r'''function itemLinkName(it) {
  if (!it) return "item";
  return String(it.title || it.text || TYPE_NAMES[it.type] || "item").split("\n")[0].trim().slice(0, 38) || TYPE_NAMES[it.type] || "item";
}
function applyLinkRelation(l, key) {
  const next = RELATIONS[key] || RELATIONS.related;
  const oldDefault = relationKeyFromLabel(l.label);
  const customLabel = !!l.label && !oldDefault;
  l.rel = key in RELATIONS ? key : "related";
  if (next.color) l.color = next.color;
  if (next.style) l.style = next.style;
  if (!customLabel) l.label = next.label;
}
function createRelatedLink(from, to, rel) {
  const meta = RELATIONS[rel] || RELATIONS.related;
  snap();
  const l = { id: uid(), a: from, b: to, rel: rel in RELATIONS ? rel : "related", color: meta.color || uiThread,
    style: meta.style || uiStyle, label: meta.label || "" };
  board.links.push(l);
  drawThreads(); save();
  toast("Connected · " + meta.name);
}
function chooseLinkRelationship(from, to) {
  const A = byId(from), B = byId(to); if (!A || !B) return;
  const target = els.get(to), r = target ? target.getBoundingClientRect() : null;
  const choices = Object.entries(RELATIONS).map(([key, meta]) => {
    const col = threadCol(meta.color || uiThread);
    return `<button class="rel-choice" data-rel="${key}"><span class="rel-dot" style="--relc:${col}"></span><span class="rel-copy"><b>${esc(meta.name)}</b><small>${esc(meta.help)}</small></span></button>`;
  }).join("");
  showCtx(`<div class="ctx-rel-head"><b>How do these ideas connect?</b><span>${esc(itemLinkName(A))} → ${esc(itemLinkName(B))}</span></div>${choices}`,
    r ? r.left + r.width / 2 : innerWidth / 2, r ? r.top + Math.min(r.height, 60) : innerHeight / 2);
  ctx.onclick = e => {
    const b = e.target.closest("button[data-rel]"); if (!b) return;
    hideCtx(); createRelatedLink(from, to, b.dataset.rel);
  };
}
function completeLink(id) {
  if (!linking) return;
  if (linking.from && !byId(linking.from)) { cancelLink(); return; }
  if (!byId(id)) { cancelLink(); return; }
  if (!linking.from) {
    linking.from = id;
    $$(".item").forEach(n => n.classList.toggle("linkable", n.dataset.id !== id));
    els.get(id).classList.add("sel");
    toast("Now tap what it connects to");
    return;
  }
  if (linking.from === id) { cancelLink(); return; }
  const from = linking.from;
  const exists = board.links.some(l => (l.a === from && l.b === id) || (l.b === from && l.a === id));
  if (exists) { toast("Those two are already connected"); cancelLink(); return; }
  cancelLink();
  chooseLinkRelationship(from, id);
}
'''
html = replace_span(html, "function completeLink(id) {", "function cancelLink() {", complete_replacement, "relationship creation flow")

link_menu_replacement = r'''function linkMenu(id, x, y) {
  const l = board.links.find(k => k.id === id); if (!l) return;
  const names = THREAD_NAMES[isBlueprint() ? "blueprint" : (isWhite() ? "white" : "cork")];
  const rels = Object.entries(RELATIONS).map(([key, meta]) =>
    `<button class="rel-choice" data-rel="${key}"><span class="rel-dot" style="--relc:${threadCol(meta.color || l.color)}"></span><span class="rel-copy"><b>${esc(meta.name)}${(l.rel || "related") === key ? " ✓" : ""}</b><small>${esc(meta.help)}</small></span></button>`).join("");
  const sw = Object.keys(THREADS).map(k =>
    `<button data-c="${k}" style="padding:6px 10px"><span style="width:16px;height:16px;border-radius:50%;background:${threadCol(k)};display:inline-block;box-shadow:0 1px 3px #0008"></span>${names[k]}${l.color === k ? " ✓" : ""}</button>`).join("");
  showCtx(`<div class="ctx-rel-head"><b>Relationship</b><span>Change what this connection means.</span></div>${rels}<hr>${sw}<hr>
    <button data-a="style"><svg><use href="#i-string"/></svg>${l.style === "dashed" ? "Make it solid" : "Make it dashed"}</button>
    <button data-a="label"><svg><use href="#i-tag"/></svg>${l.label ? "Change label" : "Add a label"}</button>
    <hr><button data-a="del" class="danger"><svg><use href="#i-trash"/></svg>${isDraftTheme() ? "Rub out this line" : "Cut the string"}</button>`, x, y);
  ctx.onclick = e => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.dataset.rel) { snap(); applyLinkRelation(l, b.dataset.rel); hideCtx(); drawThreads(); save(); toast("Relationship · " + RELATIONS[b.dataset.rel].name); return; }
    if (b.dataset.c) { snap(); l.color = b.dataset.c; uiThread = b.dataset.c; hideCtx(); drawThreads(); save(); return; }
    hideCtx();
    if (b.dataset.a === "style") { snap(); l.style = l.style === "dashed" ? "solid" : "dashed"; uiStyle = l.style; drawThreads(); save(); }
    if (b.dataset.a === "label") {
      const v = prompt("What does this connection mean?", l.label || "");
      if (v !== null) { snap(); l.label = v.slice(0, 40); drawThreads(); save(); }
    }
    if (b.dataset.a === "del") { snap(); board.links = board.links.filter(k => k.id !== id); drawThreads(); save(); toast(isDraftTheme() ? "Line rubbed out" : "String cut"); }
  };
}
'''
html = replace_span(html, "function linkMenu(id, x, y) {", "function removeItem(id) {", link_menu_replacement, "relationship edit menu")

# Item context menu can send a thought back to the inbox.
html = replace_once(
    html,
    '    <button data-a="back">${ic("back")}Send to back</button>\n    <hr>\n    <button data-a="del" class="danger">${ic("trash")}Remove from board</button>',
    '    <button data-a="back">${ic("back")}Send to back</button>\n    <button data-a="inbox">${ic("sticky")}Move to Idea Inbox</button>\n    <hr>\n    <button data-a="del" class="danger">${ic("trash")}Remove from board</button>',
    "item inbox context action",
)
html = replace_once(
    html,
    '    if (act === "back") { snap(); const m = Math.min(...board.items.map(i => i.z || 1)); it.z = m - 1; place(els.get(id), it); save(); }\n    if (act === "del") removeItem(id);',
    '    if (act === "back") { snap(); const m = Math.min(...board.items.map(i => i.z || 1)); it.z = m - 1; place(els.get(id), it); save(); }\n    if (act === "inbox") storeItemInInbox(id);\n    if (act === "del") removeItem(id);',
    "item inbox context handler",
)

# Inspector also exposes the action so it is easy to find on mobile.
html = replace_once(
    html,
    '  if (it.type !== "photo" && it.type !== "marker")\n    h += `<button class="btn wide" data-a="fith" style="margin-bottom:12px"><svg><use href="#i-fit"/></svg>Fit height to the text</button>`;',
    '  if (it.type !== "photo" && it.type !== "marker")\n    h += `<button class="btn wide" data-a="fith" style="margin-bottom:12px"><svg><use href="#i-fit"/></svg>Fit height to the text</button>`;\n  if (it.type !== "photo")\n    h += `<button class="btn wide" data-a="inbox" style="margin-bottom:12px"><svg><use href="#i-sticky"/></svg>Move to Idea Inbox</button>`;',
    "inspector inbox action",
)
html = replace_once(
    html,
    '    if (b.dataset.a === "done") { setDone([it.id]); openInspector(); }\n    if (b.dataset.tog) { toggleTagOn([it.id], b.dataset.tog); openInspector(); }',
    '    if (b.dataset.a === "done") { setDone([it.id]); openInspector(); }\n    if (b.dataset.a === "inbox") { storeItemInInbox(it.id); return; }\n    if (b.dataset.tog) { toggleTagOn([it.id], b.dataset.tog); openInspector(); }',
    "inspector inbox handler",
)

# ---------------------------------------------------------------------------
# Idea Inbox behavior, including pointer drag for touch/mobile.
# ---------------------------------------------------------------------------
inbox_js = r'''
/* ═══════════════ idea inbox ═══════════════ */
const ideaDrawer = $("#idea-drawer"), ideaList = $("#idea-list"), ideaInput = $("#idea-input");
function ideaDrawerOpen() { return ideaDrawer.classList.contains("show"); }
function toggleIdeaDrawer(force) {
  const on = force === undefined ? !ideaDrawerOpen() : !!force;
  ideaDrawer.classList.toggle("show", on);
  ideaDrawer.setAttribute("aria-hidden", on ? "false" : "true");
  $("#idea-tab").setAttribute("aria-expanded", on ? "true" : "false");
  document.body.classList.toggle("ideas-open", on);
  if (on) { renderIdeaInbox(); setTimeout(() => { if (!isNarrow()) ideaInput.focus(); }, 80); }
}
function ideaFromItem(it) {
  const boring = new Set(["Untitled", "New feature", "Report", "Checklist", "Implementation checklist"]);
  const parts = [];
  if (it.title && !boring.has(it.title)) parts.push(it.title.trim());
  if (it.text && it.text.trim()) parts.push(it.text.trim());
  if (it.type === "list" && it.tasks && it.tasks.length) parts.push(it.tasks.map(t => t.t).filter(Boolean).join("; "));
  return (parts.join(" — ") || TYPE_NAMES[it.type] || "Idea").slice(0, 400);
}
function renderIdeaInbox() {
  if (!ideaList || !board) return;
  board.inbox = Array.isArray(board.inbox) ? board.inbox : [];
  $("#idea-count").textContent = board.inbox.length;
  if (!board.inbox.length) {
    ideaList.innerHTML = `<div class="idea-empty"><b>Nothing waiting.</b><br>Use the box above whenever a thought arrives before you know where it belongs.</div>`;
    return;
  }
  ideaList.innerHTML = board.inbox.map(i => `<div class="idea-card" data-idea="${i.id}">
    <div class="idea-text">${esc(i.text)}</div>
    <div class="idea-kind">${i.kind === "card" ? "Stored feature" : "Loose idea"} · drag to place</div>
    <div class="idea-actions">
      <button type="button" data-pin="card">Feature</button>
      <button type="button" data-pin="sticky">Note</button>
      <button type="button" class="idea-del" data-del aria-label="Delete stored idea">×</button>
    </div>
  </div>`).join("");
}
function addInboxIdea(text, kind = "sticky") {
  const v = String(text || "").trim(); if (!v) return;
  snap();
  board.inbox.unshift({ id: uid(), text: v.slice(0, 400), kind: kind === "card" ? "card" : "sticky", created: Date.now() });
  renderIdeaInbox(); save();
}
function pinInboxIdea(id, at, forcedKind) {
  const idea = (board.inbox || []).find(i => i.id === id); if (!idea) return;
  const kind = forcedKind || idea.kind || "sticky";
  const d = DEFAULTS[kind] || DEFAULTS.sticky;
  const p = at || centerPoint();
  const extra = kind === "card"
    ? { title: idea.text.length <= 60 ? idea.text : idea.text.slice(0, 57).trimEnd() + "…", text: idea.text.length > 60 ? idea.text : "" }
    : { text: idea.text };
  snap();
  board.inbox = board.inbox.filter(i => i.id !== id);
  const it = mkItem(kind, p.x - d.w / 2, p.y - d.h / 2, extra);
  board.items.push(it); makeEl(it); refresh(it.id); selectItem(it.id);
  renderIdeaInbox(); updateEmpty(); save();
  if (isNarrow()) toggleIdeaDrawer(false);
  toast(kind === "card" ? "Feature placed on the board" : "Idea placed as a detail note");
}
function storeItemInInbox(id) {
  const it = byId(id); if (!it) return;
  snap();
  board.inbox = board.inbox || [];
  board.inbox.unshift({ id: uid(), text: ideaFromItem(it), kind: it.type === "card" ? "card" : "sticky", created: Date.now() });
  board.items = board.items.filter(i => i.id !== id);
  board.links = board.links.filter(l => l.a !== id && l.b !== id);
  const el = els.get(id); if (el) el.remove(); els.delete(id);
  if (sel === id) deselect();
  multi.delete(id); markSelected();
  drawThreads(); updateEmpty(); renderTimeline(); renderIdeaInbox(); save();
  toast("Moved to Idea Inbox");
}
$("#idea-tab").addEventListener("click", () => toggleIdeaDrawer());
$("#idea-close").addEventListener("click", () => toggleIdeaDrawer(false));
$("#idea-form").addEventListener("submit", e => {
  e.preventDefault();
  const v = ideaInput.value.trim(); if (!v) return;
  addInboxIdea(v); ideaInput.value = ""; ideaInput.focus();
});
ideaInput.addEventListener("keydown", e => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); $("#idea-form").requestSubmit(); }
});
ideaList.addEventListener("click", e => {
  const card = e.target.closest(".idea-card"); if (!card) return;
  const id = card.dataset.idea;
  const pin = e.target.closest("[data-pin]");
  if (pin) { pinInboxIdea(id, centerPoint(), pin.dataset.pin); return; }
  if (e.target.closest("[data-del]")) {
    snap(); board.inbox = board.inbox.filter(i => i.id !== id); renderIdeaInbox(); save();
  }
});
let inboxDrag = null;
function inboxGhost(text) {
  const g = document.createElement("div"); g.className = "idea-ghost"; g.textContent = text; document.body.appendChild(g); return g;
}
ideaList.addEventListener("pointerdown", e => {
  if (e.target.closest("button")) return;
  const card = e.target.closest(".idea-card"); if (!card) return;
  if (e.pointerType === "mouse" && e.button !== 0) return;
  const idea = (board.inbox || []).find(i => i.id === card.dataset.idea); if (!idea) return;
  inboxDrag = { id: idea.id, pointerId: e.pointerId, sx: e.clientX, sy: e.clientY, x: e.clientX, y: e.clientY, moved: false, ghost: null };
  try { card.setPointerCapture(e.pointerId); } catch (err) {}
  e.preventDefault();
});
ideaList.addEventListener("pointermove", e => {
  if (!inboxDrag || inboxDrag.pointerId !== e.pointerId) return;
  inboxDrag.x = e.clientX; inboxDrag.y = e.clientY;
  if (!inboxDrag.moved && Math.hypot(e.clientX - inboxDrag.sx, e.clientY - inboxDrag.sy) > 7) {
    inboxDrag.moved = true;
    const idea = (board.inbox || []).find(i => i.id === inboxDrag.id);
    inboxDrag.ghost = inboxGhost(idea ? idea.text : "Idea");
    document.body.classList.add("idea-dragging");
  }
  if (inboxDrag.ghost) { inboxDrag.ghost.style.left = e.clientX + "px"; inboxDrag.ghost.style.top = e.clientY + "px"; }
});
function finishInboxDrag(e, cancelled) {
  if (!inboxDrag || inboxDrag.pointerId !== e.pointerId) return;
  const d = inboxDrag; inboxDrag = null;
  if (d.ghost) d.ghost.remove();
  document.body.classList.remove("idea-dragging");
  if (cancelled || !d.moved) return;
  const r = viewport.getBoundingClientRect();
  const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
  if (!inside) { toast("Drop the idea onto the board"); return; }
  pinInboxIdea(d.id, toWorld(e.clientX, e.clientY));
}
ideaList.addEventListener("pointerup", e => finishInboxDrag(e, false));
ideaList.addEventListener("pointercancel", e => finishInboxDrag(e, true));

'''
html = insert_before_once(html, "/* ═══════════════ adding ═══════════════ */", inbox_js, "Idea Inbox behavior")

# Board list includes inbox count and uses neutral 'connections' wording.
html = replace_once(
    html,
    '<span class="s">${b.items.length} pinned · ${b.links.length} strings · ${when}</span></span>',
    '<span class="s">${b.items.length} pinned · ${b.links.length} connections · ${(b.inbox || []).length} inbox · ${when}</span></span>',
    "board list inbox count",
)

# ---------------------------------------------------------------------------
# Onboarding behavior and board switching.
# ---------------------------------------------------------------------------
html = replace_once(html, "tourStep = clamp(n, 1, 3);", "tourStep = clamp(n, 1, 4);", "tour step count")
html = replace_once(
    html,
    '  if (tourStep === 3) $("#tour-end").innerHTML = tourMode === "first"',
    '  if (tourStep === 4) $("#tour-end").innerHTML = tourMode === "first"',
    "tour finish step",
)
html = replace_once(
    html,
    '    board.items = seed.items; board.links = seed.links;',
    '    board.items = seed.items; board.links = seed.links; board.inbox = seed.inbox || [];',
    "tour seed inbox",
)
html = replace_once(
    html,
    '  if (e.key === "Enter" && tourStep < 3) { e.preventDefault(); showStep(tourStep + 1); }',
    '  if (e.key === "Enter" && tourStep < 4) { e.preventDefault(); showStep(tourStep + 1); }',
    "tour keyboard step count",
)
html = replace_once(
    html,
    '  else if (how === "empty") toast("Start with a sticky note or a photo from the tools");',
    '  else if (how === "empty") toast("Start with a feature card, a detail note, or the Idea Inbox");',
    "tour empty guidance",
)

# Keyboard: I toggles the inbox, Escape closes it first.
html = replace_once(
    html,
    '  if (e.key === "Escape") {\n    if (activeTags.size) { activeTags.clear(); applyFilter(); return; }',
    '  if (e.key === "Escape") {\n    if (ideaDrawerOpen()) { toggleIdeaDrawer(false); return; }\n    if (activeTags.size) { activeTags.clear(); applyFilter(); return; }',
    "Escape closes Idea Inbox",
)
html = replace_once(
    html,
    '  if (e.key.toLowerCase() === "p" && isDraftTheme()) { setPen(penMode ? null : "draw"); return; }',
    '  if (e.key.toLowerCase() === "i") { toggleIdeaDrawer(); return; }\n  if (e.key.toLowerCase() === "p" && isDraftTheme()) { setPen(penMode ? null : "draw"); return; }',
    "Idea Inbox keyboard shortcut",
)

# ---------------------------------------------------------------------------
# Changelog
# ---------------------------------------------------------------------------
entry = '''## 1.5.0 — 14 September 2026, 22:01 UTC

- Added a collapsible **Idea Inbox** on the right of every board for quick capture before organising. Ideas persist with the board, can be dragged onto the board with touch or mouse, or placed explicitly as a **Feature** or **Note**.
- Added **Move to Idea Inbox** to item menus and the inspector so ideas can be de-cluttered without being deleted.
- Established a clear planning model: **Feature card = main idea**, **Sticky note = detail/behaviour/question**, **Checklist = implementation work**, **Tag = project area/system**.
- Connecting two items now asks what the relationship means: **Expands into**, **Depends on**, **Affects**, **Blocked by**, or **Related to**.
- Relationship choices automatically apply a useful label, colour and solid/dashed style; the relationship can be changed later from the connection menu.
- Expanded Getting Started from three to four steps so new and existing users are taught the item roles, Idea Inbox and relationship workflow.
- Updated the example board to demonstrate the new planning model and include a loose idea waiting in the Inbox.

'''
log = replace_once(log, "---\n\n", "---\n\n" + entry, "changelog insertion")

INDEX.write_text(html, encoding="utf-8")
CHANGELOG.write_text(log, encoding="utf-8")

# ---------------------------------------------------------------------------
# Verification pass 1: release/data/UI invariants.
# ---------------------------------------------------------------------------
required_html = [
    'const VERSION = "1.5.0";',
    'const BUILD = "14 September 2026, 22:01 UTC";',
    'version: "1.5.0"',
    'id="idea-drawer"',
    'id="idea-tab"',
    'Feature card = the main idea',
    'const RELATIONS = {',
    'Expands into',
    'Depends on',
    'Blocked by',
    'function chooseLinkRelationship(from, to)',
    'function storeItemInInbox(id)',
    'tourStep = clamp(n, 1, 4);',
]
for token in required_html:
    if token not in html:
        raise SystemExit("verification failed, missing: " + token)
if "## 1.5.0 — 14 September 2026, 22:01 UTC" not in log:
    raise SystemExit("verification failed: changelog mismatch")
for element_id in ["idea-drawer", "idea-tab", "idea-list", "idea-input"]:
    if html.count(f'id="{element_id}"') != 1:
        raise SystemExit(f"verification failed: {element_id} id count")

# Verification pass 2: every inline JavaScript block must parse.
scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.S | re.I)
if not scripts:
    raise SystemExit("verification failed: no inline scripts found")
with tempfile.TemporaryDirectory() as td:
    for i, script in enumerate(scripts):
        js = Path(td) / f"script-{i}.js"
        js.write_text(script, encoding="utf-8")
        subprocess.run(["node", "--check", str(js)], check=True)

print(f"Pin It 1.5.0 verified: {len(scripts)} inline script blocks parse successfully.")
