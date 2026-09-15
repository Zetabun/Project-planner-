# Changelog

Newest first. The version here must match `VERSION` and `BUILD` near the top of the script in `index.html` — bump both together, or the app will stamp the wrong number on exports.

> **Mandatory future-agent rule:** before any update is considered complete or pushed, add its release to the top of this file **and** the `RELEASES` array in `index.html`, bump `VERSION`/`BUILD`, preserve all older history, and verify all four agree.

Numbers follow the usual shape: **major** for a change that breaks old saved boards, **minor** for new features, **patch** for fixes and polish.

---

## 1.9.8 — 15 September 2026, 14:43 UTC

- Added sensible sticky/detail-note resize limits so a low-zoom resize cannot accidentally create a board-filling sticky sheet.
- Existing/imported oversized sticky notes are repaired automatically during board normalisation.
- **Move system + contents** now clears its temporary multi-selection when the move finishes.
- The active system menu now changes to **Finish moving system**, giving desktop and touch users an explicit way to cancel the move mode before dragging.
- Tapping empty board space also exits system-moving mode cleanly.

## 1.9.7 — 15 September 2026, 14:23 UTC

- Follow-up hardening for the new multi-tab safety system.
- Writer IDs are now **unique per loaded document**. They are no longer persisted as a session tab ID, because some browsers copy `sessionStorage` when duplicating a tab and could otherwise give two live pages the same writer identity.
- Added a one-shot predecessor token so a normal refresh/reload can reclaim the exact lease owned by the document it replaced without making duplicated tabs writable.
- Startup now reads IndexedDB inside the same cross-tab **Web Lock** used for writes when supported, reducing a reload race with an in-flight exit save.
- A genuinely fresh/recreated database can clear an orphaned saved-revision marker when there is no active tab lease, preventing a stale marker from trapping an empty recovery state in read-only mode.

## 1.9.6 — 15 September 2026, 14:17 UTC

- Added **single-writer multi-tab protection**: a second Pin It tab/window is blocked from saving instead of silently racing the first one.
- Added a persistent active-tab lease, heartbeat and saved-revision marker, plus `BroadcastChannel` notifications where available.
- **Use this tab instead** now transfers control and reloads the latest saved database before the new tab can edit it.
- Database writes and imports use the browser **Web Locks API** where available, providing another cross-tab serialization layer around IndexedDB.
- Tabs detect a newer revision even if the other tab has already closed, preventing a stale in-memory copy from overwriting newer work.
- Reworked the storage-size meter to reuse the most recently serialized payload size instead of running another whole-project `JSON.stringify()` solely for metering.
- Board imports now follow the same tab-ownership, lock and revision-publication path as autosave.
- Added Page Lifecycle `freeze` flushing and automatic retry of a transient IndexedDB failure when the app returns to focus.

## 1.9.5 — 15 September 2026, 14:08 UTC

- Hardened IndexedDB/localStorage reconciliation so an old fallback copy cannot silently replace newer IndexedDB data after a storage error.
- Replaced the old queued full-database payloads with a **coalescing latest-state writer**, preventing rapid edits from accumulating multiple large serialized database copies in memory.
- Added a monotonically increasing storage revision used by migration/reconciliation.
- Expanded undo/redo snapshots to restore board tags and whole-board text/theme metadata, and prune image payloads once no remaining undo/redo state references them.
- Backup timestamps are now **per board** rather than global, so backing up one project no longer marks unrelated boards as backed up.
- **Hide Done** now hides connected strings/relationship labels and omits hidden finished items from board-fit extents.
- Freehand drawings now contribute to Board Map bounds and appear in the minimap.
- Fixed an asynchronous photo load being able to land on a different board after switching projects.
- Refreshed progress/tag/minimap chrome after deletes, duplications, inbox moves and undo/redo so counts do not remain stale.
- The onboarding example now retains its example system; cancelling onboarding after previewing another theme restores the actual board theme.
- Cancelling **New board** no longer creates an Untitled board, and Escape now closes the Board Outline/Boards drawer first.
- Added page-hide save flushing and corrected README Board Map behaviour.

## 1.9.4 — 15 September 2026, 13:54 UTC

- Changed **Board Map** so it starts closed on desktop as well as mobile; it now opens only when requested.
- Removed the visible large-scale cork texture tiling by making the low-frequency cork variation a single non-repeating viewport layer while retaining the fine surface grain.
- Added desktop clearance between the burger/boards button and the board-name case card so the decorative tape no longer visually clashes with the menu.

## 1.9.3 — 15 September 2026, 13:46 UTC

- Moved Pin It's primary board database from `localStorage` to **IndexedDB**, removing the old ~5 MB structural ceiling for normal browsers.
- Existing saved boards migrate automatically the first time 1.9.3 loads; after a successful migration the old `localStorage` copy is removed to immediately free that quota.
- Kept `localStorage` only as a fallback for browsers where IndexedDB is unavailable.
- Updated autosave and board import to use ordered asynchronous database writes so newer state cannot be overwritten by an older pending save.
- Imports remain transactional: the candidate database must be stored successfully before the imported board is added to the live session.
- Updated the storage meter to show project-data size and, where supported, the browser's real storage estimate rather than a fixed 5 MB ceiling.
- Photo compression now uses a conservative IndexedDB soft budget while preserving the tighter legacy fallback behaviour.

## 1.9.2 — 15 September 2026, 13:34 UTC

- Fixed the desktop **Ideas** drawer doing unnecessary work on every open: it no longer rebuilds the full idea list just to display it.
- Kept the physical drawer feel while limiting the shuffle to the first eight visible ideas, shortening it, and removing animated box-shadow work that caused expensive repaints.
- Fixed failed `localStorage` writes retaining a second copy of the full database in RAM after quota exhaustion.
- Autosave now stops repeatedly serialising/retrying an oversized database after the first quota failure; deleting items/boards or shrinking pictures enables a clean retry.
- Imports are now transactional: the full candidate database is checked and persisted before the live board list is changed, so a too-large import is cancelled without leaving unsaved data resident in memory.
- Reworked undo history so embedded image data is stored once and referenced by snapshots rather than copied into every undo entry; history remains capped and is cleared between boards.

## 1.9.1 — 15 September 2026, 11:56 UTC

- Moved the **Ideas** tray button upward on mobile and made its position adapt to short viewport heights so it stays clear of the taller zoom/navigation rail.
- Added a short staggered physical shuffle when the Idea Inbox opens: stored ideas wobble, slide and settle like loose paper in a drawer that has just been opened.
- The movement does not change card positions or data, does not interfere with dragging, and is disabled when the device requests reduced motion.

## 1.9.0 — 15 September 2026, 11:31 UTC

- Added a collapsible **Board Map** beside the zoom controls, showing system boundaries, item clusters and the live viewport.
- The map can be tapped or dragged to navigate large boards, updates continuously while panning/zooming, opens by default on desktop and starts collapsed on narrow/mobile screens.
- Added **Board Outline**, grouping items by system and collecting loose items under Ungrouped.
- **Expands into** relationships inside a system are represented as nested parent/child rows in the outline, with cycle-safe fallbacks for more complex graphs.
- Outline items jump to and select their corresponding board item; hidden items automatically expand their collapsed system first. System headings fit that system into view.
- Added responsive styling and dedicated map/outline icons without changing existing board data or export formats.
- Fixed automatic systems not recognising newly added notes: ungrouped items created or deliberately dropped inside an automatic system now join it automatically and immediately participate in auto-sizing. Existing members are not silently removed when dragged out.

## 1.8.1 — 15 September 2026, 11:21 UTC

- Moved the board label 10px to the right on mobile/narrow screens so its decorative tape edge no longer crowds the burger/boards button.
- Desktop top-bar spacing is unchanged.

## 1.8.0 — 15 September 2026, 10:49 UTC

- Added **Edit contents** to system/group menus so existing systems can gain or lose cards and notes without being recreated.
- Added **Move system + contents** using the existing multi-drag interaction; manual boundaries travel with the selected system.
- Added **Collapse / Expand system** with a compact system summary. Internal items hide without being deleted and external links reroute to the collapsed block.
- Fit Board and picture export now respect collapsed systems and omit their hidden internal items while preserving all data for later expansion.
- Added unread-update badges: a dot on the burger menu and a **NEW** badge on **What's new** until the latest release history is opened.
- Updated onboarding and README guidance for the expanded system workflow and release notifications.

## 1.7.0 — 15 September 2026, 10:07 UTC

- Added **Automatic / Manual sizing** to the menu opened from a system/group name.
- Manual group boundaries can be moved independently and resized from four touch-friendly corner handles without moving the cards inside them.
- Added **Lock box / Unlock box** for manual boundaries to prevent accidental movement or resizing once positioned.
- Switching back to Automatic immediately returns the boundary to following its member items.
- Manual box geometry and lock state persist through save, backup/import, undo/redo, Fit board and picture export.
- Updated onboarding and README guidance for the new group-boundary controls.

## 1.6.1 — 14 September 2026, 23:38 UTC

- Added extra breathing room between a group/system label and the nearest card or note.
- Blueprint minor and major grid lines now scale proportionally as the board zooms.
- Blueprint grid origin now follows board panning, keeping the drafting grid visually attached to the workspace rather than the screen.

## 1.6.0 — 14 September 2026, 23:15 UTC

- Added **Group areas**: lasso two or more items and wrap them in a faint named system/subtopic boundary.
- Group boundaries automatically follow their member items as cards move or resize, while the items remain independently editable.
- Tapping a group label lets you select its contents, rename the group or remove just the boundary.
- Added theme-specific Corkboard, Whiteboard and Blueprint treatments, plus group support in Fit board and picture export.
- Group membership now persists through save/import/export and undo/redo, and automatically cleans itself up when grouped items are removed.
- Updated onboarding and the worked example to demonstrate system boundaries.

## 1.5.1 — 14 September 2026, 22:45 UTC

- Idea Inbox cards now allow normal vertical drawer scrolling while preserving deliberate drag-out placement gestures.
- Long relationship menus now scroll within the screen instead of extending beyond shorter mobile displays.
- Protected photos from being converted into text-only Idea Inbox entries.
- Restored **Evidence tag** terminology for the standalone tag item while keeping board tags as project-area labels.
- Fixed the final onboarding guidance so it appears on Corkboard, Whiteboard and Blueprint themes alike.

## 1.5.0 — 14 September 2026, 22:01 UTC

- Added a collapsible **Idea Inbox** on the right of every board for quick capture before organising. Ideas persist with the board, can be dragged onto the board with touch or mouse, or placed explicitly as a **Feature** or **Note**.
- Added **Move to Idea Inbox** to item menus and the inspector so ideas can be de-cluttered without being deleted.
- Established a clear planning model: **Feature card = main idea**, **Sticky note = detail/behaviour/question**, **Checklist = implementation work**, **Tag = project area/system**.
- Connecting two items now asks what the relationship means: **Expands into**, **Depends on**, **Affects**, **Blocked by**, or **Related to**.
- Relationship choices automatically apply a useful label, colour and solid/dashed style; the relationship can be changed later from the connection menu.
- Expanded Getting Started from three to four steps so new and existing users are taught the item roles, Idea Inbox and relationship workflow.
- Updated the example board to demonstrate the new planning model and include a loose idea waiting in the Inbox.

## 1.4.2 — 14 September 2026, 21:55 UTC

- Fixed newly added sticky notes, marker text and evidence tags sometimes refusing to move on the first drag in the mobile app.
- On mobile/narrow layouts, new text items remain selected and immediately draggable instead of automatically opening the full-item inline editor over themselves.
- Text remains one tap away through **Edit** on the mobile selection bar; desktop keeps the existing instant quick-edit behaviour.

## 1.4.1 — 14 September 2026, 20:04 UTC

- Blueprint notes, index cards, reports, checklists, photos and tags now use blue drafting sheets, fine grids, white marker-style handwriting and crisp borders.
- Sticky notes have six tinted sheets with coloured accent edges and folded corners; stored paper and ink choices are preserved when switching themes.
- Restyled the board title, labels, dates, stamps, completion indicators, editing fields, resize handles and mobile tool rail to match Blueprint.
- Connections are straight, high-contrast drafting lines, and both new and existing pen strokes stay visible on blue boards.
- Picture exports now retain Blueprint sheets, colours, metal pins, headings and annotations instead of reverting to whiteboard paper and tape.

## 1.4.0 — 14 September 2026

- Added a third board style: **Blueprint**.
- Blueprint boards use a navy drafting surface with a technical grid, cool steel-blue chrome and pinned paper notes with metal tacks.
- Connections on blueprint boards now render as crisp drawn planning lines rather than sagging string.
- Enabled the pen tool on blueprint boards, matching the existing whiteboard freehand workflow.
- Updated the board-style picker, onboarding flow, picture export and README documentation to include the new theme.

## 1.3.0 — 14 September 2026

- Added a visible **What's new** button to the boards drawer.
- Added a dedicated release-history view: the newest release opens by default and older versions can be expanded underneath it.
- Backfilled the in-app history for `1.0.0`, `1.1.0`, `1.1.1` and `1.2.0` so the app now shows its release history retroactively.
- The version stamp now opens the full release history rather than only the current release notes.
- Added an explicit future-release requirement to `README.md`, `CHANGELOG.md` and the `index.html` release block so future agents must update the in-app history and changelog before completing/pushing work.

## 1.2.0 — 14 September 2026

- **Marking things done.** One tap on the selection bar, `D`, or a button in the item panel. The paper fades and desaturates, a DONE ribbon crosses the top corner, and the strings running to it soften, so a glance at the board shows what's still live.
- Checklists look after themselves: tick every box and the item finishes; untick one and it comes back. Marking the item done ticks every box.
- Works on a whole lasso selection, so a week's finished work is one action.
- Progress counts: `9/24 DONE` beside the board title, and `3/12` on each tag chip so you can see which areas are lagging.
- A **Hide done** chip clears finished work off the board without deleting anything.
- Finished items lose their due date — the ribbon says all that's needed.
- Small items get a compact DONE pill instead of a corner ribbon, and the picture export renders all of it.

## 1.1.1 — 14 September 2026

- Due dates moved from the bottom-left corner to the top right, level with an item's heading. They were fighting the tag strip and the date underline for the same corner.
- Headings now stop short of the date rather than running underneath it.
- A checklist's progress tally moved to the bottom-right corner to free the top line for the date.
- The picture export follows all of the above.

## 1.1.0 — 14 September 2026

- Tag strips have a second mode: the tag name runs down the height of the strip, read bottom to top, with the strip widened to suit. Set it per board in the boards drawer under **Tag strips**.
- Fixed: text on index cards was written straight over the ruled red margin. Headings and body now start clear of it, and clear of a tag strip when there is one.
- Every item type now makes room for a tag strip rather than letting it sit under the text.

## 1.0.0 — 14 September 2026

First published version.

**The board**

- Pin up photos, sticky notes, index cards, reports, checklists, evidence tags and marker headings
- Drag, resize, rotate and stamp anything (Done, Urgent, Blocked, Idea, Review)
- Run string between items, in five colours, solid or dashed, with labels
- Pan and pinch-zoom, undo and redo, search that spotlights matches
- Select several at once with a lasso, then move, duplicate or tag them as a group
- Freehand marker pen on the whiteboard, with five colours, three nib widths and a stroke eraser

**Organising**

- Tags with colour accents down the edge of an item, a legend with live counts, and tap-to-filter
- Due dates with a timeline strip along the bottom and a marker for today
- Follow the thread: select an item and everything it isn't tied to fades back
- Text size per item or across a whole board

**Looks**

- Two board styles — corkboard with pins and waxed string, whiteboard with tape and marker lines
- The interface follows the board: stained wood on cork, brushed steel on the whiteboard
- Save the whole board as a picture, drawn to match whichever style it uses

**Keeping it**

- Boards save to the browser as you go; export and import as self-contained JSON
- Pictures shrink themselves to fit a size budget as storage fills
- Asks the browser for persistent storage, nudges iPhone users to install, and tracks backups
- Installs to a home screen with its own icon and launches full-screen
