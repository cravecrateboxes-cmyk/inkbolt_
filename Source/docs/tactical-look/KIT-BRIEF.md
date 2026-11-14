# Kit detail brief (tactical look, plan Stage 11)

How to add modelled detail to a map kit (`blender/fam_kit_<theme>.py` and its helper modules) so the maps read
less "toy" under the tactical look. Written from the `kit-stronghold` exemplar pass.

## What to detail first

Run `node Source/tools/piece_usage.js Source/dist/look/piece-usage.json <plan>`: it ranks the kit's pieces by
visible area (bounding-box faces x placements). The top 15 to 25 pieces cover most of the screen; detail those.
Up-close interior pieces (doors, lockers, consoles) matter more than distant cliffs and rock (rock is already
broken up by the tiling detail texture of Stage 5).

## The helpers (`blender/kit_base.py`, "detail helpers")

`panel_seams`, `bolt_row`, `rivet_strip`, `kick_plate`, `base_trim`, `cap_trim`, `drip_edge`, `corner_guard`,
`conduit_run`, `pipe_run`, `junction_box`, `vent`, `cable_tray`, `sign_plate`, `window_frame_depth`.

- Every helper draws on a face that looks toward Blender -Y (game +Z) at the plane `y = yf`, in the current
  `k.push()` frame. For another face, `k.push(x, y, deg)` first (e.g. `deg=180` for the back face).
- All parts are `ink=False`: small detail must not thicken the comic outline.
- Parts stand at least 3 mm proud and start 3 mm inside the face (`EMBED`), and horizontal runs stop 5 mm short of
  the piece's sides, so `ib_lib.check_zfight` passes. The build stops on any coplanar overlap and names the two
  shapes: move one of them (most often a seam crossing a bolt or a slit; split the seam run round it).
- Use only palette names the kit already has; new palette cells only in free slots (cell order is data).

## Never change

Piece names, origins, footprints, `_COL` / `_WCOL` boxes, socket empties, the faces robots walk on, wall module
mating edges, palette cell order.

## Collision fitted from the mesh

`blender/col_fit.py` lists pieces per kit (e.g. `Mast_*`, `FuelTank` in kit-arctic) whose `_COL` boxes are re-cut
from the visible mesh at export. Detail on those pieces can change their collision, which changes play. After a
build, compare the `_COL` / `_WCOL` node names, positions and scales with the previous GLB (the arctic mast's guy
wires turned five fitted boxes into one; that detail was taken out). The kit pass is done only when collision
is identical.

## Budgets

Per prop 2,500 triangles, landmark 8,000, kit total 90,000 (`IB.TRI_BUDGET.kitPropMax`, `kitMax`; raise the
theme's own `budget` in `src/data/themes/<id>.js` when its pass needs it). Rivets and bolts are 12 triangles
each: prefer `rivet_strip` with a wider `every` on big doors (the stronghold blast door went from 300 to 1,476).
GLB under 4 MB.

## Review loop (per kit)

1. `python3 Source/blender/build_assets.py --family kit-<theme>` (with the AO bake: `--no-ao` changes the classic
   look's shading, so use it only while iterating).
2. `python3 Source/tools/glb_compare.py <old.glb> Source/assets/fps-kit-<theme>.glb`: only the pieces you touched
   may differ.
3. `python3 Source/tools/build.py`, `npm test` (in `Source/`): budgets, names, the theme's own unit test.
4. In-level shots: `node Source/tests/e2e/look-shots.js <dir> <plan>` and a sheet against the previous shots.
5. The theme's e2e walk test, the collision audit, `?zcheck=1`.

## Done

The top pieces of the kit show panel seams, fixings, trims and service runs where a real building would have
them; no z-fighting; budgets and tests green; the sheet reads less flat at 10 m without looking busy at 30 m.
