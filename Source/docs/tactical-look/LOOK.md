# The tactical look: how it works and where the knobs are

The game draws every map with a "tactical" lighting look on top of its comic art: sun shadows, light from the
lamps modelled in the map, haze, surface detail, glow and a colour grade, dressing (stains, cracks, clutter) and
material-aware hit effects. The comic ink outlines stay. Plan and history: `PLAN.md` and `PROGRESS.md` in this
folder.

## Switches (URL)

| Query | Effect |
|---|---|
| `?look=classic` | Everything off: the original look, byte-for-byte the same picture |
| `?post=0` | The look without the post pass (what low tiers do) |
| `?shadows=0` | No sun shadows |
| `?lookstats=1` | Frame time, draw calls, tier and render sizes in the console every 2 s (nothing on screen) |
| `?zcheck=1` | Cross-piece z-fighting check (with `tests/e2e/map-shots.js`) |

## A new map needs no look work

A new theme gets a correct look with no entry anywhere:

1. **Family preset.** `src/data/looks.js` `LOOKS.guess(env)` picks a family (`mil-ext`, `urban-ext`, `wild-ext`,
   `ind-int`, `dark-int`, `civic-int`, `giant-room`) from the theme's env: sky or ceiling, fog, sun height. An
   explicit entry in `LOOKS.themes` is tuning on top.
2. **Surface classes.** Each palette cell of the kit gets a class (paint, concrete, metal, wood, glass, ...) from
   the name rules in `blender/surface_classes.py`; `python3 tools/gen_surfaces.py` regenerates
   `src/data/surfaces.gen.js`. Add an override there only when a name misleads the rules.
3. **Lights.** Glowing palette cells and `*_Glow` companions of the kit become lights in the light volume
   automatically. Never add a light with no fixture.
4. **Dressing.** Decals and clutter follow the family's rules (`LOOKS.dress`) on the zone grid.
5. **Review shots.** `node Source/tests/e2e/look-shots.js <outDir> <plan>` shoots an automatic 8-spot recipe on any
   map; `look-sheet.py` makes a before/after sheet, `look-metrics.py` checks brightness ranges.

## Where things live

| File | What |
|---|---|
| `src/data/looks.js` | Defaults, families, per-theme tuning, tiers, dressing rules (`LOOKS.dress`) |
| `src/game/look.js` | Per-level setup (`Look.begin`), shared uniforms (`Look.U`), flash lights, viewmodel light link, `Look.lightAt` |
| `src/game/surface.js` | The light model injected into the toon materials; detail texture array; hit classes (`hitClass`) |
| `src/game/atmo.js` | Height fog, sky, haze for custom shaders, dust motes, lamp cones |
| `src/game/shadows.js` | Sun shadow map around the player |
| `src/game/lightgrid.js` | Light volume: lamps -> a baked grid of light per zone (time-sliced, 3 ms a frame) |
| `src/game/post.js` | Offscreen target, bloom, grade, FXAA; HUD bars and comic words drawn after the grade |
| `src/game/dress.js` | Decals and clutter per zone |
| `src/game/boom.js` | Hit effects by surface class (`impactLook`), tracer shape |
| `tools/gen_detail.py`, `tools/gen_decals.py` | The detail texture array and the decal atlas (`assets/tex/`) |
| `blender/fam_dress.py` | Clutter props (`fps-dress.glb`) |
| `blender/kit_base.py` | Shared kit detail helpers (seams, bolts, trims, conduit, vents, signs, ...) |

## Tuning a map (most common knobs, `LOOKS.themes.<id>`)

- `sunI`, `sunColor`: sun strength and colour. `ambI`, `ambSky`, `ambGround`: sky / ground fill.
- `indoorAmb`: fill under a roof (raise for dark interiors with no lamps). `grid.intensity`: lamp light strength.
- `fog.length`: metres to 63% haze. `exposure`, `grade.sat`, `grade.contrast`: final picture.
- `floor: { cls, gloss }`: the code-built floor's class. `wet`: wet floors (0..1).
- `dress: { density, floor, base, wall, clutter, wallClutter, off }`: dressing rules.

Brightness ranges per scene type are in `PLAN.md` section 4.2; `look-metrics.py --check` reports them.

## Rules that must hold

- No HUD file changes (the list is in `tests/e2e/hud-lock.spec.js`), no gameplay change, renderer tone mapping
  and output encoding stay off, three.js r128.
- `?look=classic` must stay identical to the original game.
- Detail parts on kits are at least 3 mm proud (`ib_lib.check_zfight`), and dressing is never solid.
