# Map asset upgrade brief (owner request, after the tactical look)

## Owner's words

"I also need all levels need to be upgraded especially assets and details that consist of just simple shapes and designs and
whatnot. You can find countless examples of this literally anywhere in every map. This is the most prevalent until map
level 20. But even still remains something I need. Many mistakes and low effort on some visual details. and things not so
hard to notice. You need to catch this as much as possible within all the maps in my game. And destroy this."

## What to hunt (every map, every zone)

### 1. Primitive-looking assets

These are props, set pieces, landmarks and backdrop pieces that read as a box, cylinder, cone or sphere with a colour on it. Typical examples:
- cone or lollipop trees
- box cars
- cube crates with no planks or straps
- cylinder barrels with no rims or ribs
- slab furniture
- flat-colour signs
- box buildings with no windows, sills or roof edge
- pipes with no flanges
- lamps that are a stick and a ball
- rocks that are a single squashed sphere

### 2. Low-effort detail

- big flat untextured faces
- repeated identical props in a grid
- props with no base or contact (floating, or sunk into the floor)
- missing trims where walls meet floors and ceilings
- doors with no frame
- windows with no depth
- stairs with no stringers
- railings that are one bar

### 3. Mistakes

- z-fighting and flicker (the `?zcheck=1` page lists cross-piece z-fights)
- gaps and seams you can see through
- props clipping into walls or each other
- floating objects
- wrong scale (a chair bigger than a door)
- stretched or smeared palette UVs
- inside-out or missing faces
- holes in the sky backdrop
- backdrop buildings that end abruptly
- out-of-place colours
- light or emissive parts with no fixture
- text or signs mirrored

Maps 1–20 are the worst; go deepest there.

## How to fix

### Remodel

Remodel the weak assets in the kit's Blender script (`blender/fam_kit_<theme>.py` and its `*_detail.py` helpers) so they read as designed objects:
- real silhouettes and proportions
- bevels or chamfers on big edges
- sub-parts: frames, rims, handles, legs, panels, bolts where they matter
- varied variants instead of clones
- materials from the kit palette

Give organic things (trees, rocks, bushes) layered, irregular forms: several clumps, trunks with taper and branches, rocks that are faceted clusters.

### Add missing dressing

Add missing dressing that belongs to the piece, such as trims, frames and window depth. The detail helpers in `blender/kit_base.py` are documented in `docs/tactical-look/KIT-BRIEF.md`.

### Fix mistakes

Fix the mistakes at their source (the kit piece, the theme's layout in `src/data/themes/<id>.js`, or a placement rule). Keep the decal and clutter dressing (`src/game/dress.js`) as is, unless a rule places something visibly wrong.

## Rules (from KIT-BRIEF.md, all still apply)

- **Names and layout stay put.** Never change piece names, origins, footprints, socket empties, palette cell order, the faces robots walk on, or wall-module mating edges.
- **Collision must stay identical** (the `_COL` / `_WCOL` node names, positions and scales; compare with the previous GLB). The only exception is a real collision bug, such as an invisible wall, a hole you can fall through, or a prop you can walk through that looks solid. Fix those and list each one in the report.
- **Detail parts are `ink=False`.** They sit 3 mm proud and 3 mm embedded, and horizontal runs are inset 5 mm. `ib_lib.check_zfight` must pass.
- **New palette cells** may go only in free slots.
- **Budgets:**
  - prop 2,500 triangles, landmark 8,000, kit 90,000 (`IB.TRI_BUDGET`); raise a theme's own budget in `src/data/themes/<id>.js` only when needed
  - triangles in view about 750k or less
  - GLB under 4 MB per kit
  - `perf.spec.js` draw calls: desktop 230, phone 140
- **Build with AO** for the final build: `python3 blender/build_assets.py --family kit-<theme>`. `--no-ao` is for iteration only.
- **Don't touch:**
  - HUD files (`src/ui/*`, `hpbars.js`, `dmgnum.js`; `tests/e2e/hud-lock.spec.js` must pass)
  - the look code (`look.js`, `surface.js`, `post.js`, `lightgrid.js`, `shadows.js`, `atmo.js`, `looks.js`), except a theme's own look entry if a fix truly needs it
  - enemies (`fam_bots.py`, `fam_trooper.py`, `jets.js`)
- **Gameplay stays the same:** spawns, routes, cover positions, doors, elevators.
- `?look=classic` must still load and play.

## Process per map

1. **Before shots.** Run `node tests/e2e/look-shots.js Source/dist/look/upgrade/<theme>/before <plan>`, which takes 8 automatic spots. Add `map-shots.js` close-ups of the worst props.
   - The machine renders on the CPU (SwiftShader): set `LOAD_MS=400000` where a script reads it.
   - Other workers share the machine, so expect it to be slow.
2. **Make a findings list.** Look at the shots, and also read the kit script's piece list. Use `node tools/piece_usage.js Source/dist/look/piece-usage.json <plan>` to rank pieces by screen area. Fix the most visible ones first.
3. **Remodel and fix.** Rebuild the kit, compare it with `tools/glb_compare.py` (only the pieces you touched may differ), and compare collision.
4. **Rebuild the game.** Run `python3 tools/build.py`. Run `npm test` in `Source/`. Run the theme's own e2e walk test if it has one (`tests/e2e/<theme>-walk.spec.js` etc.).
5. **After shots and sheet.** Take the same spots for after shots, then make a sheet with `python3 tests/e2e/look-sheet.py <before> <after> Source/dist/look/upgrade/<theme>/sheet.jpg <plan>`.
6. **Commit.** Commit per map on your worktree branch, and end every message with the two attribution lines your brief gives you.

## Report (per worker, under 300 words)

Per map, give:
- what was remodelled
- the mistakes fixed
- any collision changes, with the reason
- triangles before and after
- the sheet path

Then list anything you saw but could not fix.
