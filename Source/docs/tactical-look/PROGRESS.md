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

### First full pilot set (`dist/look/on3`, 56 shots) and first tuning pass

- Classic baseline: mean luminance 0.565, 54 of 56 shots outside the section 4.2 ranges (it is the "toy" look).
- Look on, before tuning: downtown, datacenter, mall and mountains read as intended on the sheets. Problems:
  stronghold zone 2 (carved halls under the rock) far too dark (mean 0.08 to 0.14, up to 28% of pixels under
  0.06); stronghold's warm apron went grey; bedroom lost its cheer (muddy purple walls); mall too bright
  (mean ~0.50) with washed-out floor inlays; metro platform zone brighter than the dark-interior range.
- Tuning (looks.js): stronghold sun 1.5 warmer (#FFD6AE), indoor fill 0.55 and lamp light x1.6 for the halls;
  bedroom ambient 0.66 / indoor fill 0.72, saturation 1.06; mall ambient 0.42, indoor fill 0.45, lamps x0.72,
  floor gloss 0.40; metro lamps x0.36; downtown sun 1.35; mountains sun 0.85.
- Decision: the snow range of section 4.2 (mean 0.40 to 0.55) is too dark for a snowfield that fills most of the
  frame; mountains reads right at mean ~0.60 with under 1% clipped. The review sheet is the judge (as section
  4.2 says); the range stays as a guide and mountains is accepted above it unless the owner disagrees.
- Second pass: stronghold halls indoor fill 0.8, lamp light x2.0 (zone 2 was still 0.11 to 0.18 mean). Metrics now
  take per-zone scene types from `look-spots.json` `zoneTypes` (stronghold zone 2 = int-dark, observatory zone 2 =
  int-lit): mixed maps are judged against the right range.

### Stage 8 checks

- `troops.spec.js` (SHOTS=1): ALL PASS, no console errors. The committed troops review pictures were black
  (taken with the render loop paused before); the new ones render: soldiers and the Blade Bot read clearly,
  props cast sun shadows. Soldier armour reads very dark: owner question at Checkpoint 1.
- `latebots.spec.js`: ALL PASS (Hawk accent colours, Crawler two-tone skins, no console errors).
- `gear-shots.js`: the committed `review/gear-*.png` were stale (another save state and the old gun designs), so
  the inventory pictures are compared base build vs look build instead. Its last shot (a pickup card in play)
  times out on the CPU renderer with the look on (it waits on game time at 1920x1080), as trap T25 warns.

## Checkpoint 1 package (`dist/look/cp1`, 56 shots, second tuning pass)

Sheets (left classic, right look): `tests/e2e/review/look/cp1-<map>.jpg` for mountains, stronghold, downtown,
metro, datacenter, bedroom, mall. Overall mean luminance 0.408 (classic 0.565); 48 of 56 shots sit outside at
least one section 4.2 bound, mostly by small margins on mean/median; the sheets are the judge.

Notes from the sheet review:
- Stronghold apron and sky read warm; sun shadows ground the props. Zone 2 halls are now readable (mean 0.12 to
  0.20) but still the darkest scene in the set: owner question (1).
- Bedroom keeps its colours but white furniture reads beige/grey under the detail texture and indoor fill:
  owner question (3).
- Mall zone 2 long view is bright (mean 0.67); metro platform zone mean 0.29 to 0.37 (above int-dark). Both
  read correctly on the sheet.
- Mountains above the snow range by decision (see first tuning pass).

Owner questions: frame rate and tier on a real device (`?lookstats=1`); yes/change on (1) interior darkness,
(2) ink thickness, (3) colour, (4) bloom and grain; soldier armour darkness; the snow range decision.

Still open before Stage 9 (not blocking the checkpoint): Stage 4 enemy readability gate (metro/coalmine),
bake timing gate, Stage 6 vfx-shots and perf budgets on real hardware, TIER=low sheet.

### Metrics (cp1)

| shot | type | mean | median | p5 | >0.92 | <0.06 | sat | out of range |
|---|---|---|---|---|---|---|---|---|
| bedroom-z0-aim | int-lit | 0.602 | 0.637 | 0.493 | 0.0% | 1.7% | 0.14 | mean, median, p5 |
| bedroom-z0-floor | int-lit | 0.461 | 0.508 | 0.137 | 0.0% | 1.5% | 0.31 | mean, median, p5 |
| bedroom-z0-long | int-lit | 0.435 | 0.454 | 0.110 | 0.0% | 1.6% | 0.34 | mean, median |
| bedroom-z0-up | int-lit | 0.489 | 0.526 | 0.148 | 0.0% | 1.3% | 0.22 | mean, median, p5 |
| bedroom-z0-wall | int-lit | 0.371 | 0.385 | 0.078 | 0.1% | 3.8% | 0.34 | median |
| bedroom-z1-back | int-lit | 0.379 | 0.410 | 0.066 | 0.0% | 3.7% | 0.33 | median |
| bedroom-z1-long | int-lit | 0.433 | 0.439 | 0.111 | 0.3% | 1.3% | 0.33 | mean, median |
| bedroom-z1-wall | int-lit | 0.399 | 0.439 | 0.129 | 0.1% | 1.3% | 0.35 | median, p5 |
| datacenter-z0-aim | int-ind | 0.191 | 0.162 | 0.124 | 0.0% | 1.7% | 0.29 | mean, p5 |
| datacenter-z0-floor | int-ind | 0.497 | 0.566 | 0.099 | 0.0% | 2.3% | 0.12 | mean, median |
| datacenter-z0-long | int-ind | 0.340 | 0.303 | 0.088 | 0.0% | 2.5% | 0.18 | mean, median |
| datacenter-z0-up | int-ind | 0.253 | 0.166 | 0.112 | 0.0% | 2.7% | 0.23 | p5 |
| datacenter-z0-wall | int-ind | 0.345 | 0.345 | 0.074 | 0.1% | 3.4% | 0.19 | mean, median |
| datacenter-z1-back | int-ind | 0.291 | 0.227 | 0.080 | 0.0% | 3.4% | 0.22 |  |
| datacenter-z1-long | int-ind | 0.321 | 0.244 | 0.075 | 0.3% | 2.9% | 0.20 | mean |
| datacenter-z1-wall | int-ind | 0.286 | 0.227 | 0.058 | 0.1% | 5.2% | 0.25 |  |
| downtown-z0-aim | ext-day | 0.522 | 0.617 | 0.113 | 5.2% | 1.3% | 0.33 | mean, median, >0.92 |
| downtown-z0-floor | ext-day | 0.393 | 0.305 | 0.112 | 0.0% | 3.3% | 0.21 |  |
| downtown-z0-long | ext-day | 0.431 | 0.414 | 0.095 | 0.1% | 1.0% | 0.25 |  |
| downtown-z0-up | ext-day | 0.439 | 0.421 | 0.109 | 0.0% | 0.8% | 0.32 | median |
| downtown-z0-wall | ext-day | 0.389 | 0.366 | 0.064 | 0.1% | 3.8% | 0.33 |  |
| downtown-z1-back | ext-day | 0.463 | 0.359 | 0.124 | 2.2% | 0.6% | 0.26 | mean |
| downtown-z1-long | ext-day | 0.490 | 0.472 | 0.106 | 3.0% | 1.4% | 0.23 | mean, median |
| downtown-z1-wall | ext-day | 0.492 | 0.444 | 0.123 | 0.3% | 0.7% | 0.26 | mean, median |
| mall-z0-aim | int-lit | 0.469 | 0.449 | 0.069 | 0.9% | 3.7% | 0.13 | mean, median |
| mall-z0-floor | int-lit | 0.475 | 0.510 | 0.133 | 0.4% | 1.4% | 0.21 | mean, median, p5 |
| mall-z0-long | int-lit | 0.435 | 0.455 | 0.085 | 0.4% | 1.4% | 0.20 | mean, median |
| mall-z0-up | int-lit | 0.475 | 0.461 | 0.076 | 0.6% | 2.7% | 0.18 | mean, median |
| mall-z0-wall | int-lit | 0.437 | 0.453 | 0.076 | 1.1% | 2.6% | 0.24 | mean, median |
| mall-z1-back | int-lit | 0.403 | 0.369 | 0.073 | 0.4% | 2.8% | 0.26 | mean |
| mall-z1-long | int-lit | 0.666 | 0.690 | 0.371 | 1.1% | 0.8% | 0.13 | mean, median, p5 |
| mall-z1-wall | int-lit | 0.466 | 0.455 | 0.094 | 0.5% | 1.8% | 0.23 | mean, median |
| metro-z0-aim | int-dark | 0.273 | 0.273 | 0.126 | 0.0% | 3.6% | 0.12 | mean, median, p5 |
| metro-z0-floor | int-dark | 0.185 | 0.178 | 0.046 | 0.0% | 10.0% | 0.21 |  |
| metro-z0-long | int-dark | 0.202 | 0.189 | 0.084 | 0.0% | 2.6% | 0.16 | p5 |
| metro-z0-up | int-dark | 0.245 | 0.236 | 0.079 | 0.0% | 2.6% | 0.15 | p5 |
| metro-z0-wall | int-dark | 0.205 | 0.191 | 0.070 | 0.1% | 3.8% | 0.17 | p5 |
| metro-z1-back | int-dark | 0.286 | 0.289 | 0.086 | 0.0% | 2.2% | 0.19 | mean, median, p5 |
| metro-z1-long | int-dark | 0.371 | 0.358 | 0.132 | 0.4% | 1.4% | 0.14 | mean, median, p5 |
| metro-z1-wall | int-dark | 0.288 | 0.272 | 0.078 | 0.1% | 2.8% | 0.25 | mean, median, p5 |
| mountains-z0-aim | ext-snow | 0.625 | 0.635 | 0.589 | 0.0% | 0.3% | 0.41 | mean, median, p5 |
| mountains-z0-floor | ext-snow | 0.617 | 0.819 | 0.163 | 0.2% | 0.5% | 0.11 | mean, median |
| mountains-z0-long | ext-snow | 0.619 | 0.742 | 0.157 | 0.7% | 0.5% | 0.15 | mean, median |
| mountains-z0-up | ext-snow | 0.628 | 0.787 | 0.183 | 0.1% | 0.4% | 0.17 | mean, median, p5 |
| mountains-z0-wall | ext-snow | 0.401 | 0.263 | 0.129 | 0.1% | 0.8% | 0.23 | median |
| mountains-z1-back | ext-snow | 0.557 | 0.625 | 0.186 | 0.3% | 0.4% | 0.16 | mean, median, p5 |
| mountains-z1-long | ext-snow | 0.620 | 0.728 | 0.166 | 0.9% | 0.3% | 0.15 | mean, median |
| mountains-z1-wall | ext-snow | 0.511 | 0.352 | 0.170 | 0.0% | 0.4% | 0.17 | median |
| stronghold-z0-aim | ext-dusk | 0.470 | 0.462 | 0.268 | 0.0% | 0.7% | 0.41 | mean, median, p5 |
| stronghold-z0-floor | ext-dusk | 0.492 | 0.587 | 0.133 | 0.0% | 1.6% | 0.26 | mean, median, p5 |
| stronghold-z0-long | ext-dusk | 0.368 | 0.367 | 0.117 | 0.0% | 1.6% | 0.23 | mean, median, p5 |
| stronghold-z0-up | ext-dusk | 0.340 | 0.273 | 0.181 | 0.1% | 0.6% | 0.28 | mean, p5 |
| stronghold-z0-wall | ext-dusk | 0.501 | 0.589 | 0.136 | 0.2% | 1.7% | 0.26 | mean, median, p5 |
| stronghold-z1-back | int-dark | 0.185 | 0.151 | 0.063 | 0.1% | 4.0% | 0.16 |  |
| stronghold-z1-long | int-dark | 0.195 | 0.166 | 0.069 | 0.4% | 3.0% | 0.20 |  |
| stronghold-z1-wall | int-dark | 0.117 | 0.101 | 0.066 | 0.0% | 3.9% | 0.16 | mean, median |
| all | | 0.408 | 0.409 | 0.130 | | | | 48 of 56 |

## After Checkpoint 1

The owner said "do the remaining things" without answering the Checkpoint 1 questions. Decision: the current
tuning stands as the answer (interiors, ink, colour, bloom and grain unchanged, soldier armour and the bright snow
kept); any of it can change later from the owner's play test. Work goes on with Stage 9 onward.

### Open gates from stages 1 to 6

- **Light volume bake timing (Stage 4).** Measured with `look-diag.js` (EVAL loop over `LightGrid.work()`).
  First run: per-zone bake 20 to 370 ms (gate 1.5 s: pass), but single frames 25 to 30 ms and the sky-visibility
  render up to 23 s on later zones under the CPU renderer. Fixes: the sky render runs for every zone at level
  start, under the loader (83 to 115 ms in total per level); light work in one-cell units; sky and post passes in
  10-row bands; budget 3 ms a frame. Result (metro, downtown, stronghold): 0 of 123,616 work units over 6 ms,
  7 to 14 over 2 ms (thread noise from the CPU renderer sharing the cores); worst frame 5.0 to 7.2 ms at the
  old 4 ms budget, so the budget is now 3 ms.
- Emitters per zone: metro 256 / 217, datacenter 256 x 3 (capped), mall 256 x 3, stronghold 53 / 113, downtown
  141 to 165, coalmine 37 to 46, mountains 14 to 22, bedroom 0 (the giant room is lit by its window and the
  indoor fill; it has no modelled lamps: no fake lights added, as section 4 says).
- Enemy readability: `tests/e2e/look-readability.js` (+ `.py`): darkest open cell of zone 0, Crawler and Soldier
  posed at 12 m and 30 m, shots with and without, robot pixels vs a 16 px ring. Results below when run.
- `perf.spec.js` budgets raised to the section 6 numbers (desktop 230, phone 140).

### Stage 9. World dressing

- 9.1 `tools/gen_decals.py` -> `assets/tex/decals.webp` (1024 x 1024, 46 cells, 154 KB) and
  `src/data/decals.gen.js` (cell table). A separate tool rather than a second output of `gen_detail.py` (no
  shared code; the detail generator stays as it was).
- 9.2 `src/game/dress.js`: floor decals on open `.` cells (weighted toward walls and props), wall decals on the
  open face of wall modules found by rays against the placed module's own mesh (all five probes on one flat,
  non-glass, non-glowing face). Exclusions 1.5 m round gates, pickups, spawn cans, weapon stands, doors,
  elevators, walkable boxes and water symbols; the floor under every decal must agree (2 cm flat, 25 cm terrain).
  Look kind `decal` (IB_DECAL: tint from the vertex colour, alpha from the atlas times the strength, light
  volume + sun + shadow, no detail). One decal mesh and one clutter mesh per zone, in the zone's group.
- 9.3 `blender/fam_dress.py` -> `assets/fps-dress.glb` (177 KB, gate 600 KB): 30 pieces, 14 to 288 triangles
  with an 8 mm shell, no collision; loaded only with the look on (classic loads exactly what it did).
  `IB.DRESS_PIECES` in `assets.js` gives the names and a 300-triangle budget each (`assets.test.js` covers them).
- 9.4 rules per family in `looks.js` (`LOOKS.dress`), mountains overridden (prints and stones only). Giant rooms
  get no clutter (adult-scale props read as crumbs there).
- 9.5 density from the tier table at level build.
- Counts (floor / wall decals / clutter per zone): metro 151/28/49 and 108/29/45; downtown 113/3/40, 97/1/21,
  100/1/35; stronghold 154/1/25 and 167/0/48. Build time 28 to 40 ms per level. Wall decals were rejected
  mostly because the corner probes missed narrow modules: wall decals are now one module wide at most.
- Gates: nothing is solid (no world boxes are added, so collision, bounds and nav cannot change); unit tests
  486 pass; the sheets (`dist/look/s9a`) show lit stains and cracks sitting on the floors, none floating.
