# 2026 Fantasy Draft Guide

A static, single-page draft board for a 10-team, full-PPR, 16-round snake draft,
built from ESPN's 2026 PPR cheat sheet. Deployed on GitHub Pages.

## What it is

`index.html` is a self-contained (inline CSS/JS, no external libraries) draft
board with a Big Board view, per-position tabs grouped by tier, and a My Team
tab. It reads player data from `players.js`, which is generated from the ESPN
PDF cheat sheet.

## Updating the rankings

1. To tweak the WR tier overrides only: edit `WR_OVERRIDE` in `build_players.py`,
   then re-run:
   ```
   python3 build_players.py
   ```
2. To pull in a new season's cheat sheet: replace `NFL26_CS_PPR.pdf` with the new
   PDF (same filename, or update the `PDF` constant in `parse.py`), then run:
   ```
   python3 parse.py && python3 build_players.py
   ```
3. Commit and push the regenerated `players.js` (and `players_raw.json` if you
   want it tracked):
   ```
   git add players.js players_raw.json
   git commit -m "Update rankings"
   git push
   ```

## How draft-day state works

All draft state — drafted players, your team (★), your draft slot, the "hide
drafted" toggle, and the active tab — is saved to the browser's `localStorage`
under the key `draftguide_2026`. Closing the tab or reloading the page restores
everything exactly as you left it. Use the **Reset draft** button (with
confirmation) to wipe the state and start over.

Because state lives in `localStorage`, it's local to one browser/device — it
does not sync across devices or get committed to git.

## Deployment

The site is plain static HTML/JS and is served via GitHub Pages from the
`main` branch, root (`/`) directory. Any push to `main` updates the live site
within a minute or two.
