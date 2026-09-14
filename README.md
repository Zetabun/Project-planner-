# Pin It

A planning board for projects. Pin photos, notes, cards and checklists, then connect them to show what belongs together. One HTML file, no build step, no dependencies beyond Google Fonts.

Works on desktop and mobile. Boards are saved in the browser and can be exported as JSON.

## What's in here

| File | Why |
|---|---|
| `index.html` | The whole app |
| `manifest.json` | Name, colours and icons for installing it |
| `icon-32/180/192/512.png`, `icon-maskable-512.png` | Home screen, tab and install icons |
| `CHANGELOG.md` | What changed in each version |
| `README.md` | This |

Upload all of them together — the app runs from `index.html` alone, but without the icon files and manifest it installs with a blank icon.

## Publish it to GitHub Pages

From this folder, with the GitHub CLI:

```bash
git init -b main
git add .
git commit -m "Pin It — evidence board"
gh repo create pin-it --public --source=. --push
gh api -X POST repos/:owner/pin-it/pages -f source[branch]=main -f source[path]=/
```

Without the CLI, create an empty repo called `pin-it` on github.com first, then:

```bash
git init -b main
git add .
git commit -m "Pin It — evidence board"
git remote add origin https://github.com/YOUR-USERNAME/pin-it.git
git push -u origin main
```

Then: repo → Settings → Pages → Source: *Deploy from a branch* → `main` / `/ (root)` → Save.

The link appears within a minute or two at:

```
https://YOUR-USERNAME.github.io/pin-it/
```

## Putting it on your phone

Open the published link in Safari, then **Share → Add to Home Screen**. It installs as *Pin It* with a corkboard icon and launches full-screen with no browser chrome — the address bar and toolbar are gone, so the board gets the whole display. Android is the same through Chrome's **Install app**.

Two things worth knowing. The icon only appears from the published URL, not from a file opened locally. And on iOS the home-screen version is what protects your boards: Safari clears storage for sites you haven't opened in about a week, and installed sites are exempt — so add it before you build anything you care about.

## First run

On a first visit you're asked what you're working on, shown the three board styles to pick from, and given three short pointers. You can then start empty or start with a small worked example to poke at. It never appears again after that — reopen it any time from the boards drawer under **How this works**.

## Three board styles

**Corkboard** — cork, brass pins, red waxed string that sags under its own weight, typewriter labels and rubber stamps.

**Whiteboard** — a wiped melamine surface in an aluminium frame, with a marker pen you can write on it with. Everything goes up with torn masking tape instead of pins (sticky notes keep sticking themselves). String becomes marker strokes: slightly bowed, drawn stopping just short of each item, with an arrowhead showing which way the connection runs. Stamps are scrawled and circled, dates are underlined, and everything handwritten is in marker — Permanent Marker for headings, Kalam for notes.

**Blueprint** — a navy drafting surface with a fine technical grid and blue drafting sheets throughout: sticky notes, index cards, reports, checklists, photo frames and evidence tags. White marker-style notes and headings, precise borders, typed report text and metal pins with coloured rims give it a workshop-plan feel. Sticky notes retain six distinct colour accents and folded corners. Titles, dates, stamps, editing fields, completion indicators and the mobile tool rail all match. Connections are straight drafting lines, with brighter ink colours for legibility.

The interface follows the board: dark stained-wood controls and panels on cork, brushed light-steel ones on the whiteboard, and cool steel-blue chrome on the blueprint theme, with the accent shifting to match.

Set it per board in the boards drawer under **Board style**, so a scruffy brainstorm, a clean client-facing plan and a technical planning board can all look different. New boards inherit the style of the one you're on. Picture exports match whichever style the board uses, including Blueprint sheets and metal pins. Switching styles preserves the underlying paper, pin and ink choices, so switching back restores the original colours.

## What's on the board

| Item | What it's for |
|---|---|
| Photo | Polaroid with a handwritten caption |
| Sticky note | Quick thought, six paper colours |
| Index card | Heading plus lined body text |
| Report | Typed document page for longer detail |
| Checklist | Tickable steps with a done counter |
| Evidence tag | Small luggage-tag label — owners, references, numbers |
| Marker text | Handwriting straight on the cork, for section headings |

Every item takes a coloured pin (or a tape colour on the whiteboard — masking, gaffer, blue painter's, washi) and an optional stamp: Done, Urgent, Blocked, Idea, Review. Blueprint boards keep the pin system, but with cleaner metal tacks and drafting-board styling.

## Text size

Four sizes — S, M, L, XL — scaling every bit of writing on an item together: note text, headings, checklist rows and their boxes, captions and tag labels.

- **Whole board:** boards drawer → **Text size**. Resizes everything currently pinned up and becomes the default for anything you add next.
- **One item:** its panel → **Text size**, which overrides the board setting for that item only — useful for making a heading shout or shrinking a long note to fit its card.

Both are undoable, and picture exports render at whatever size you set.

## Marking things done

Tap the tick on the selection bar, press `D`, or use the button in an item's panel. A finished item fades back and desaturates, takes a green DONE ribbon across its top corner, and the strings running to it soften — so you can see at a glance what's still live without reading a word. Small items get a compact DONE pill instead of a ribbon.

Checklists manage it themselves: tick every box and the item is done; untick one and it's back. Marking the item done the other way round ticks all its boxes.

It works on a whole selection, so finishing off a week's work is one action, and it's undoable like anything else.

Counts appear beside the board title (`9/24 DONE`) and on every tag chip (`3/12`), which is the quickest way to see which part of a project is lagging. A **Hide done** chip in the legend clears finished work out of view without deleting it.

Finished items drop their due date, since the ribbon covers it.

## Tags

Tags group things across the board without moving them. A tagged item gets a strip of colour down its left edge — tape on cork, a marker stripe on the whiteboard, and the same cleaner stripe treatment on blueprint — carrying the tag's initial, so you can tell at a glance that the red-edged notes are engine work and the green ones are gameplay. An item can carry more than one tag; the strip splits into bands rather than picking a winner.

Strips come two ways, set per board in the boards drawer under **Tag strips**: **colour only**, a slim band carrying the tag's initial, or **show names**, a wider band with the whole tag name running up it like a book spine. Names are better on a board with a handful of tags you're still learning; colour only is better once you know them and want the space back.

A legend sits under the title bar showing every tag with a live count, so nobody has to remember what red meant. Tap a chip to filter: everything without that tag fades back, along with the strings leading to it. Tap more chips to widen the filter, `Esc` to clear it.

Tags are applied from an item's panel, or — much faster — by selecting a cluster with the lasso and using the tag button on the action bar, which toggles the whole group at once. Long-press a legend chip to rename it, recolour it, select everything carrying it, or delete it. Twelve tags per board, eight distinct colours.

Tags live on the board, so each project keeps its own set, and they travel through export, import and picture export.

## Selecting several at once

Tap the dashed-box tool (bottom of the tool rail) and drag a box around what you want — on desktop, holding `Shift` while dragging does the same without switching tools. `Ctrl`/`Cmd` + `A` selects everything.

With several selected you can drag the whole cluster as one, duplicate it, or remove it. Tap the background to drop the selection.

## Dates and the timeline

Any item can take a due date, set under **Due** in its panel. A small tab appears on the item — red if it's due today or overdue, amber within a week, grey beyond that.

The calendar button in the top bar (or `T`) opens a strip along the bottom showing every dated item in order, with a marker for today. Tap a dot to jump to that item on the board. Items sharing a date group into one marker.

## Following a thread

Select an item and the board fades back everything it isn't tied to: direct connections stay bright, two hops out sit halfway, the rest drops away, and the strings dim to match. Tap the background to bring it all back. It turns itself off while you're searching or have several items selected.

## Saving the board as a picture

Boards drawer → **Save the board as a picture**. It draws the whole board — cork, string, pins, stamps, dates and the case plate — to a PNG at up to 2600px and downloads it. Good for sending someone the plan without sending them the app.

## Writing on whiteboards and blueprint boards

The pen tool (whiteboard and blueprint boards, or press `P`) lets you write and draw straight onto the board in marker — circle a note, sketch an arrow, scrawl a reminder in your own hand.

- Five marker colours and three nib widths, from the bar that appears at the bottom. Blueprint displays these as pale drafting inks; existing strokes adapt automatically without rewriting the saved colours.
- The eraser removes a whole stroke at a time, so a quick swipe clears a letter without nibbling at it.
- Strokes are smoothed as you draw, so a shaky finger still reads as handwriting.
- Two fingers pan and zoom as usual while the pen is active — only one finger draws.
- Marks sit above the notes, so a circle drawn round a sticky stays visible, and they move with the board when you pan or zoom.

Drawings are part of the board: they undo, save, export to the picture, and travel in the JSON like everything else. Switching a board back to cork hides the pen tool but keeps anything already drawn.

## Connecting things

Tap the string tool (or press `L`), tap the first item, then tap the second. Tap any string to change its colour, switch solid/dashed, add a label like "blocks" or "feeds into", or cut it.

Five colours: red, navy, gold, green and cream on cork; red, blue, orange, green and black marker on the whiteboard; and coral, sky, amber, mint and white drafting ink on blueprint boards.

## Adding pictures

- Tap a photo item and pick a file
- Paste an image from the clipboard anywhere on the board
- Drag an image file onto the board

Pictures are shrunk automatically on the way in. Each one is resized and re-encoded until it fits a size budget — dimensions come down first, then quality — and the budget tightens as the browser's storage fills up, so a late addition won't blow the limit. A 4 MB phone photo typically lands around 150–250 KB, and you're told what it saved.

Transparent PNGs are flattened onto white rather than going black, and the boards drawer shows how much storage you've used with a **Shrink the pictures on this board** button that does a second, harder pass over everything already pinned up.

## Keyboard shortcuts

| Key | Action |
|---|---|
| `L` | String mode |
| `T` | Show or hide the dates strip |
| `P` | Pen, on a whiteboard or blueprint board |
| `D` | Mark the selection done, or put it back |
| `Esc` | Clear a tag filter (then selection, then modes) |
| Corner handle | Resize an item (text keeps its size — use Text size for that) |
| `Shift` + drag | Select several with a box |
| `Ctrl`/`Cmd` + `A` | Select everything |
| `Ctrl`/`Cmd` + `D` | Duplicate the selected item |
| `F` | Fit the board to the screen |
| `/` | Search |
| `Delete` | Remove the selected item |
| Arrow keys | Nudge (hold `Shift` for bigger steps) |
| `Ctrl`/`Cmd` + `Z` | Undo (add `Shift` to redo) |
| `Esc` | Cancel / deselect |
| Double-click | Edit text (double-click a heading to edit the heading) |
| Right-click / long press | Item menu |
| Scroll / pinch | Zoom · drag the background to pan |

Pasting plain text creates a sticky note. Paste several lines at once and you get one note per line, laid out in a block and left selected so you can drag them somewhere as a group — the quickest way to get an existing list onto the board.

An item's panel also has **Fit height to the text**, which trims or grows the item so its writing just fits.

## Keeping boards safe

Boards live in the browser, and browsers do clear storage — iOS Safari is the strict one, wiping script-writable storage for sites it hasn't seen in roughly a week of use. Four things guard against that:

- **Persistent storage.** The app asks the browser to mark its storage persistent, which exempts it from routine eviction. Supported in Safari 17+, Chrome, Edge and Firefox. Browsers can refuse; the boards drawer tells you which mode you're in, with a button to ask again.
- **Install prompt.** On an iPhone in Safari, once you've got a few things pinned up, a one-off card explains the eviction rule and how to add the app to your home screen — installed web apps aren't part of Safari and keep their own usage clock.
- **Backup reminders.** The drawer shows when you last backed up, in red past a fortnight, and nudges you if it's been three weeks or you've never done it.
- **Back up via the share sheet.** On a phone, **Back up** opens the system share sheet so the file can go to Files, iCloud Drive, Mail or anywhere else, instead of vanishing into Downloads. Desktop still downloads.

None of this is a substitute for a backup you control. The export is one self-contained JSON with the pictures inside it, so it restores fully on any device.

## Where boards live

In `localStorage`, under the key `pinit.v1` — one browser, one device, no account. Use **Export** in the boards drawer to save a `.json` copy or move a board elsewhere, and **Import** to bring one back. Private/incognito windows won't persist anything; the app says so on load if that's the case.

To sync across devices you'd need a small backend — a Cloudflare Worker with KV would do it, swapping the `store` wrapper near the top of the script for `fetch` calls.

## What's new and release history

The boards drawer has a **What's new** button. It opens the full release history, newest first, with the current release expanded and every previous release available underneath. The version stamp at the bottom of the drawer opens the same view. The history is embedded in `index.html`, so it still works when the app is running as a single local/offline file.

The historical list is intentionally retrospective: versions `1.0.0`, `1.1.0`, `1.1.1`, `1.2.0`, `1.3.0` and every later release must remain available rather than replacing the previous entry.

## Releasing an update

**Mandatory for every future agent/update:** do not consider project work complete, and do not push a release, until all of the following are true:

1. Bump `VERSION` and `BUILD` near the top of the script in `index.html`.
2. Add the new release to the **top** of the `RELEASES` array in `index.html`. Never delete older releases.
3. Add the same version/date and matching change summary to the **top** of `CHANGELOG.md`.
4. Verify the newest `RELEASES` entry, `CHANGELOG.md`, `VERSION` and `BUILD` all agree.
5. Run the project checks and only then finish/commit/push.

The version is shown in the boards drawer, saved alongside the data and stamped into every exported board as `"app"`, so a file that turns up later can be traced to the build that wrote it. When someone opens a build newer than the one they last used, they get a quiet "Updated to…" note.

Use major for a change that breaks old saved boards, minor for new features, patch for fixes and polish.

## Editing the file

Everything is in `index.html`, in this order: design tokens and chrome CSS → item and thread CSS → markup and icon sprites → state, storage and board model → rendering → pointer interaction → panels, images, export and init. Each section starts with a banner comment.

## Blueprint maintenance and checks

Blueprint CSS is scoped to `body[data-theme="blueprint"]`. Keep colour mappings (`BLUEPRINT`, `BP_NOTES`, `bpMarker`, `draftInk`) presentation-only; never rewrite saved item or stroke colours when changing themes. Keep `drawBlueprintItem` and the Blueprint branches of `exportPNG` aligned with the DOM styling. The app remains self-contained in `index.html`.

Before a theme release, parse every inline script, check all seven item types and six sticky colours, edit text, toggle checklist completion, switch through all three themes and back, and save a picture. Check that date/stamp/connection labels stay readable, the pen palette matches its strokes, and mobile controls remain usable. Verify the newest embedded release and changelog agree with `VERSION`/`BUILD`.
