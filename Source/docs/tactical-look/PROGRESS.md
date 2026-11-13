# Tactical look: progress log

Plan: `PLAN.md` in this folder. Base commit `5cfa145` (the plan was written against it; the plan itself is `631f21a`).
Branch `claude/charming-heisenberg-f3j35w`. One line per finished step, the measured gate numbers, and decisions.

## Standing decisions

- **Future maps.** The game will grow past 45 maps. Nothing in the look may need hand work per map to be correct:
  a new theme gets a family preset from `looks.js` (an explicit entry, or a guess from its env: sky/ceiling, fog,
  sun colour), its kit's palette cells get surface classes from the name rules in `surface_classes.py`, its
  lamps become lights automatically, and `look-shots.js` shoots any plan with an automatic 8-spot recipe. A
  per-theme entry in `looks.js` is tuning on top, never a requirement. Unit tests check that every theme in
  the campaign resolves.
- Map content detail (more "working detail" per map) is an ongoing separate effort driven by tester reports;
  this job builds the systems (dressing, decals, kit detail) that make that cheap, and does Stage 11 for the
  pilots.

## Stage 0. Safety net and tools

- 0.1 This file.
- 0.2 `tests/e2e/look-shots.js`: plans from argv, `LOOK=classic|on`, `TIER` (default high, the auto tier guard is
  switched off for shots), `ZONES`, `VM=0`, `HTML`, `EXTRA`, `ONLY`. Spots from `look-spots.json`, else an automatic
  8-spot recipe (z0 long / wall / floor / up / aim, z1 long / back / wall) that works on any map, so future maps
  need no hand-picked spots. Aim shots hold the right mouse button. Waits for the light volume to finish the zone.
- 0.3 `tests/e2e/look-sheet.py`, 0.4 `tests/e2e/look-metrics.py` (`--check`, `--md`), scene types per plan in
  `look-spots.json` (all 46 themes, from section 8).
- 0.5 `tests/e2e/hud-lock.spec.js`: file lock (15 protected files vs `5cfa145`), HUD pixel lock at 1280x720,
  1920x1080, 844x390 touch, enemy-bar lock (only the bars drawn, through the real render path). Baselines in
  `tests/e2e/review/hud-lock/` from the untouched build. Two runs of the check on the untouched build: 0 pixels
  differ on all three HUD views and on the 3,180 bar pixels (fully deterministic).
- Extra tool: `tests/e2e/look-diag.js` prints post mode, shadow state, light volume (size, lights per zone, bake ms),
  look family, page errors; `EVAL=` evaluates an expression in the page.
- 0.6 Classic baseline: the untouched build is kept as `Source/dist/look/base.html` (ignored) so baselines can be
  re-shot at any time. Shots in `Source/dist/look/s0-base/`.
- 0.7 Unit tests: 478 pass at the base; 484 with the new look and surface tests. Smoke run: see the Stage 6 entry.

## Stages 1 to 6: implementation notes and decisions

Built together, then checked stage by stage with switches: `?look=classic` (everything off), `?look=classic&post=1`
(classic picture through the offscreen target: the Stage 1 passthrough gate), `?shadows=0` (Stage 2 without
Stage 3), `?post=0` (the look without the post pass: the low-tier path).

- Stage 1 `post.js`: fallback chain a/b/c/d with `checkFramebufferStatus` on both framebuffers of a multisampled
  target; megapixel caps; logged once per size/tier as `[look] post ...`.
- Stage 2 `looks.js` (families, all 46 themes, tier matrix, `guess()` for maps with no entry), `surface.js`
  (light model), `atmo.js` (fog chunks, sky). The fog's world height in the vertex chunk is
  `dot(viewMatrix[1].xyz, mvPosition.xyz) + cameraPosition.y`: the plan's `vec3(viewMatrix[0][1], ...)` is the
  transpose (row 1 instead of column 1 of the view rotation) and would give a wrong height on any tilted view.
- 2.6 custom haze shaders: stronghold waterfalls and the mossgarden stream (uniforms uFog/uNear/uFar) are fitted
  every frame to the shared fog curve at 100/300/1000 m at their own height (`Atmo.adoptHaze`, option a). The
  city below (`zones.js`) keeps its own depth haze (option b): it is a vista hundreds of metres down, tuned per
  theme to the fog colour, and never meets world geometry at the same depth.
- Stage 3 `shadows.js`: as planned. Floors (`zone.ground`) never cast.
- Stage 4 `lightgrid.js`: the volume is a 2D atlas of the Y slices for every device (the plan's WebGL1 fallback
  used everywhere: one code path, no `sampler3D`). Glow companions named `*Glass` are reflections, not lights,
  and glass/water faces of companions never emit (metro had its glass companions counted as lamps).
  Sky visibility renders only the baked zone's own group (rendering the whole level stalled 20 s on the CPU
  renderer). `LG.cellStats` lists light per palette cell for tuning.
- Stage 5A: `surface_classes.py` rules + overrides; all 51 families reviewed (27 families got overrides; red
  fire-safety cells are painted metal, `scrub` is vegetation, `ledge` concrete, `far*` backdrop cells class 0).
- Stage 5B: `tools/gen_detail.py` (14 layers, 1.73 MB). Grid lines sit half a cell off the tile edge so
  grooves never fall on the seam. Medium tier samples the same 512 px array (one projection) instead of a
  downsampled copy: no second texture, 19.5 MB of GPU memory with mips.
- Stage 5D: `ib_lib.bake_look_channels`: G is averaged per vertex so the exporter welds corners exactly as
  before (a per-corner G changed the vertex count). `IB_NO_LOOK_BAKE=1` builds without it.
  `tools/glb_compare.py` falls back to a corner-by-corner triangle comparison when welding differs. Two pieces
  (`KIT_STRONGHOLD_Flagpole`, `Landmark_Radar`) differ between any two rebuilds even without this change:
  existing non-determinism, not caused by the look.
- Stage 6: bars and comic words are drawn after the grade on layer 1. The bars test a packed copy of the world
  depth (taken before the viewmodel pass clears depth) and hide behind the gun via the viewmodel depth.

### Gate results (stages 1 to 6)

- Stage 1 passthrough (`?look=classic&post=1` vs `?look=classic`, metro + stronghold, 6 views): 99.88% to 100% of
  pixels within 3/255 outside the gun (gate 99.5%). Differences inside the gun box are the idle sway, which
  differs between any two runs.
- `?look=classic` vs the untouched build: identical outside the gun box on metro; stronghold differs only in timed
  animation (waterfalls, puffs). No change in the classic look.
- HUD lock with the look on: file lock clean, HUD views 0 pixels different at 1280x720, 1920x1080, 844x390. Enemy
  bars: interior bar pixels within 1/255 (the check now masks the baseline's bar pixels eroded by 1 px, because the
  graded background legitimately changes the antialiased edges).
- Light calibration: the prototype's sun intensity (2.6) blew sunlit snow out (22% of pixels clipped). Lit
  surfaces must stay under white by construction (section 4.2), so all light levels were rescaled: defaults
  sun 1.5 / ambient 0.40; mountains sun 0.95 (0.8% clipped after).
- Stage 7: dust motes (one Points draw, kinds per family; none in mountains, arctic, seabase which have their
  own snow), lamp cones under downward lamp emitters (one instanced draw, 32 nearest), wetness (`look.wet`:
  parking 0.5, scrapyard 0.5, seabase 0.4, cargoship 0.3, metro 0.2), seabase caustics. Medium and high only.
- Stage 8: robots, troopers, debris, canisters, thrown items, rockets, gems, world guns and moving lines use the
  look ('actor' = no tiling detail + a cool rim that grows in the dark); robot light parts are fully emissive;
  actors receive the sun shadow; smoke puffs follow the sun and the local light; GunSkins world instances take
  the light volume at their own position (viewmodel and inventory instances untouched).
