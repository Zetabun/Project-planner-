# Changelog

Newest first. The version here must match `VERSION` and `BUILD` near the top of the script in `index.html` — bump both together, or the app will stamp the wrong number on exports.

> **Mandatory future-agent rule:** before any update is considered complete or pushed, add its release to the top of this file **and** the `RELEASES` array in `index.html`, bump `VERSION`/`BUILD`, preserve all older history, and verify all four agree.

Numbers follow the usual shape: **major** for a change that breaks old saved boards, **minor** for new features, **patch** for fixes and polish.

---

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
