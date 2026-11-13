# INKBOLT "Inked Tactical" look overhaul: build plan

Written 2026-11-13 against commit `5cfa145` on branch `claude/charming-heisenberg-f3j35w`.
Planner: one session of research, measurement and a working prototype. Builder: follow the stages in order.

Every fact in sections 2 and 3 was read from the code, measured, or proven by running it in this repository.
File and line references are for commit `5cfa145`; re-find them by the quoted text if lines have moved.

---

## 0. How to use this plan

1. Read sections 1 to 6 once, fully. They are the contract.
2. Do the stages in section 7 in order. Each stage has: purpose, steps, traps, a gate, and what to commit.
   **Never start a stage while the previous stage's gate is red.**
3. Section 9 is the list of traps found during research. Each one cost time to find. Read it before you write
   any shader or touch any material.
4. Stop at every **OWNER CHECKPOINT** and show the owner the named review sheets. Do not roll the look out to
   more maps before the owner has agreed to the pilot maps.
5. The prototype in `Source/docs/tactical-look/prototype/` is working reference code, not shippable code.
   Section 3 says what to keep and what to replace.
6. Keep `Source/docs/tactical-look/PROGRESS.md` (create it in Stage 0): one line per finished step, the gate
   numbers you measured, and anything you decided. A later session resumes from that file.

Start here, in this order: read sections 1 to 6 and 9; look at the three sheets in `reference/`; run
`prototype/proto-shots.js` once on `stronghold` so you have seen the prototype work (see
`prototype/README.md`); then begin Stage 0.

Working rules for the whole job:

- One stage, one or more commits, pushed to `claude/charming-heisenberg-f3j35w`. Plain-English commit messages.
- After every stage: `python3 Source/tools/build.py`, `node --test Source/tests/unit/*.test.js` (478 pass today),
  the HUD lock check (Stage 0), and the look sheets for the pilot maps.
- Headless Chromium here renders on the CPU (SwiftShader, about 2 to 3 frames a second). Run **one** browser
  job at a time: two at once time out. Give `page.screenshot` a 240 s timeout. A map takes about 2.3 minutes
  for 8 shots.
- Images cost context. Join shots into sheets (PIL) and look at sheets, not single frames.
- Parallel workers (kit detail work in Stage 11) run in their own git worktrees and never edit shared files.
- **Big binaries bloat the repository.** `Play Inkbolt.html` is 35 MB and the kit GLBs are 104 MB. Commit the
  built `Play Inkbolt.html` only at owner checkpoints and at the end, not after every stage. Commit rebuilt
  GLBs once per stage that needs them (Stage 5D once, Stage 11 once per kit), never while still tuning.
  Build locally as often as you like.

---

## 1. Goal and hard rules

### 1.1 Goal

Give Inkbolt the raw, grounded tactical look of Titanfall 2 and Call of Duty: Modern Warfare while keeping a
thin comic ink line as its signature. In one sentence: **keep the ink, lose the toy.**

The owner's references and what to take from each (the four images of the request; in this session they
are `images/8.webp` to `11.webp` under the session's temp folder, and they are not copied into the
repository because they are other games' screenshots):

| Reference | What it shows | What we take |
|---|---|---|
| Titanfall 2, dark service corridor | Near-black space lit by a few cool lamps, wet concrete and pipe highlights, light haze, a glowing hologram | Darkness as a tool, light pools, specular on rough concrete and metal, bloom only on real emitters |
| Titanfall 2, stone courtyard | Hard sun, deep cast shadows, bright haze and bloom in the opening, warm stone with visible block texture | Sun and shadow contrast, atmospheric glow, material texture on big flat walls |
| Call of Duty DMZ range | Natural light under trees, depth haze, small props everywhere, soft depth of field on the gun | Depth layering by haze, clutter density, gun-in-world lighting match |
| Battlefield / CoD market street | Shop shutters, signs, baskets, litter, stains, cables: a lived-in street in open shade | Dressing density: decals, signage, clutter, grime gradients on walls |

Measured on those images (centre crop, luminance 0 to 1): mean 0.25 to 0.41, median 0.16 to 0.37, darkest 5%
at 0.02 to 0.11. The game today measures mean 0.51 to 0.64 with almost nothing below 0.10. **The gap is value
structure and light, not saturation**: the references are as colourful as the game (HSV saturation 0.18 to
0.60 against the game's 0.21 to 0.33). Do not grey the game out. Darken it, light it, and give surfaces a
material.

An honest ceiling: Inkbolt's models are low-polygon shapes built from code, with flat colours and no
authored textures. This plan gets the lighting, atmosphere, material response and density of those games,
drawn with an ink line. It does not make photographic assets. Where a map still reads as "toy" after
Stages 2 to 10, the cause will be its shapes, and Stage 11 (modelled detail) is the answer.

### 1.2 Hard rules

1. **The HUD does not change.** No edit to `Source/src/ui/hud.js`, `hud.css`, `hudf.css`, `skillhud.js`,
   `loothud.js`, `tabmenu.js`, `menus.js`, `gear.js`, `fieldkit.css`, `ui.css`, `loader.js`, `loader.css`,
   `skillicons.js`, or `Source/src/game/hpbars.js`, `dmgnum.js`. Enemy health bars, damage numbers, lock
   brackets, the crosshair, the radar and every panel must be pixel-identical before and after. Stage 0 builds
   the check that proves it; it runs after every stage. (`Source/src/ui/thumbs.js` may only be touched if a
   test shows the inventory pictures changed, and then only to restore them.)
2. **No gameplay change.** Collision boxes, nav grids, zone maps, waves, weapon numbers and saves stay as they
   are. New geometry is never solid. Enemies must stay readable in dark maps (Stage 4 has a measured gate).
3. **The comic identity stays**: ink outline (thinner), comic explosion words and cards, ink damage numbers,
   the halftone hurt vignette, the Undercover look.
4. **three.js stays at r128**, no bundler, no new runtime dependency. The game still ships as one HTML file and
   as the published artifact (page and each side file under 16 MB).
5. **Every tier keeps the same art direction.** A dark map is dark on every tier. Tiers change quality
   (shadow resolution, texture detail, post effects), never the lighting design.
6. **A classic switch exists** from the first shader stage: `?look=classic` renders exactly as today. It is the
   baseline for all before/after sheets and the escape hatch.
7. **Performance**: 60 frames a second on the owner's machine at the High tier; the existing auto tier guard
   (`game.js` `perfGuard`: steps down when the frame average is over 18.5 ms) keeps weaker devices playable.
   Draw calls stay inside the budgets in section 6.
8. Do not turn on `renderer.toneMapping`, `renderer.outputEncoding` or physically correct lights (trap T2).

### 1.3 Not in scope unless the owner asks

Audio, level layouts, enemy behaviour, new weapons, menus. Section 11 lists the open questions and the
defaults this plan takes.

---

## 2. Where the game is today (verified)

### 2.1 Rendering

- `Source/src/game/render.js` (390 lines) is the whole render core.
  - `toonMaterial(opts)` (line 86): `THREE.MeshToonMaterial` with a 4-texel gradient (line 14: shadow band
    0.72 tinted purple, mid 0.9, lit 1.0), vertex colours on, optional palette `map`. Its `onBeforeCompile`
    adds the inverted-hull ink outline (`aHull` attribute, `VERT_PROJECT` line 38) and the Undercover look
    (`CLOAK_WORLD` / `CLOAK_ROBOT`) at `#include <fog_fragment>`.
  - Outline width: `outlineUniforms(0.012, 3.2)` for the world (about 3.2 px), `(0.0035, 2.2)` for the
    viewmodel. Ink colour `#15121C`.
  - One white `DirectionalLight` per scene (`R.sun`, line 283; the viewmodel's at 286). **No ambient light, no
    shadows, no post-processing.** Linear `THREE.Fog` (line 293). Sky: a 5-band gradient sphere (line 298).
  - `R.render` (line 372): clear, render the world scene, clear depth, render the viewmodel scene, straight to
    the canvas. It is called from one place: `game.js:1157`.
  - `R.applyEnv(env)` (line 310) applies a theme's sky, fog, sun direction and `sunColor`.
- Colour handling: everything is display-referred. Palette textures are forced to `LinearEncoding`
  (`assets.js:89`), `THREE.Color` hex values are used raw, no shader does tone mapping or encoding. 11
  `onBeforeCompile` patches and 10 `ShaderMaterial`s all write final display colour.
- Tiers (`game.js:92`): `high`, `medium`, `low`, `potato`. They set decal and particle counts, fog distance
  and pixel ratio (`render.js:365`: high = min(dpr, 2), medium 1.5, low 1, potato 0.85). Settings offer Auto,
  High, Low (`menus.js:221`).

### 2.2 Assets

- 51 model families, each one GLB in `Source/assets/` built by `Source/blender/build_assets.py` from Python
  (`fam_*.py`; `bpy` 5.3.0 is installed). 46 are map kits (`kit-*`), about 1 to 2.5 MB each, 104 MB in all.
- Every family has **one 64 x 64 palette texture** (8 x 8 cells of flat colour, nearest filtering). Faces pick a
  cell by UV. There are **no other textures**. 1,143 distinct cell names exist across families (`steel`,
  `conc`, `wood`, `lamp`, `screen`, `glass`, `rust`, `leaf`...). The names are only in the Python palettes
  (`ib_lib.PALETTES`), not in the GLBs.
- Vertex colour `COLOR_0` is RGBA uint8 (`quantize_glb.py`). Today R = G = B = baked ambient occlusion,
  posterised to two steps, 1.0 or 0.87 (`ib_lib.bake_ao`, line 238; each piece is baked alone with no ground
  under it). Alpha is 255 except a removable-piece mask on the troopers.
- Every kit piece goes through `ib_lib.build_object` (line 133): bevel, palette UVs, AO bake, outline shell.
  That one function is the place to change what is baked into vertices.
- A kit rebuild is fast: `kit-stronghold` (103 pieces) with AO takes 6 seconds and gives a GLB of identical
  size to the committed one (bytes differ slightly: Cycles noise).
- `assets.js` `loadFamily` (line 71) makes one toon material per family (`A.mat[fam]`) and assigns it to every
  mesh of the family.

### 2.3 Maps

- 46 themes (`Source/src/data/themes/<id>.js`), 45 in the campaign (`levelplans.js:36` `ORDER`).
- `zones.js` `Z.buildLevel` (line 1423): per zone, kit pieces are placed and **merged into one mesh per
  family** (`Parts`, line 236; `meshesFor`, line 319), all sharing that family's material. Floors, ceilings,
  roofs and painted lines are code-built flat polygons with vertex colours and no texture (`IB.Geo`, material
  `Z.mat`, line 1424; `paintFloor`, line 955). A whole zone floor is one flat-coloured quad.
- Glow companions (`theme.glow`, 17 themes): unlit `MeshBasicMaterial` copies of lamp lenses, LEDs, screens,
  holograms (`glowMat`, line 267).
- Lamps exist in every theme as model pieces whose lenses are painted with cells named `lamp`, `light`,
  `glow`, `screen`, `fire` and similar. They emit no light.
- Measured on the High tier, standing at a zone entry: 62 to 142 draw calls and 216,000 to 487,000 triangles
  a frame; a zone is 65,000 to 144,000 triangles in 2 or 3 meshes. `perf.spec.js` budgets draw calls at 200
  (desktop) and 120 (phone).
- Zones drawn: the current one, the one behind and the next (`Z.setVisible`, line 1996; called from
  `game.js:337, 637, 739`).

### 2.4 Things that already look tactical

- Guns, arms and attachments: `Source/src/game/gunskins.js` `GS.tactical` and `FRAG_LIGHT` (line 102) already
  give them a soft light ramp, gloss, metal, rim and grain. It replaces the toon shader's
  `vec3 outgoingLight = ...` line. The world gets the same idea, done properly, in Stage 2.
- The HUD (already "Spectre" tactical).

### 2.5 Environment limits

- Outbound network: `raw.githubusercontent.com` and `registry.npmjs.org` work. `ambientcg.com`,
  `polyhaven.com`, `cdn.jsdelivr.net` are denied by the environment's network policy. This plan needs none of
  them: all textures are generated here (numpy 2.5, Pillow 12 with WebP, Blender 5.3). If the owner later
  wants scanned CC0 textures, they add the host in the environment's network settings; it is an optional
  swap-in in Stage 5, never a dependency.

---

## 3. What the prototype proved

`prototype/proto.js` is injected into the built page by `prototype/proto-shots.js` and changes nothing in the
repository. Sheets: `reference/before-after-1-stronghold-metro.jpg`, `-2-mountains-downtown.jpg`,
`-3-downtown-metro.jpg`. Left is today, right is the prototype with **no per-map work at all**.

Proven to work in this codebase:

| # | Technique | Result |
|---|---|---|
| P1 | Replacing the toon light line with a real light model (sun, sky/ground ambient, specular, rim) inside the existing material patch | Works on every kit material and on the code-built floors |
| P2 | Sun shadow map (4096, `PCFSoftShadowMap`, rendered once, `autoUpdate = false`) | Works. The ink shell must be removed from the shadow pass (trap T1) |
| P3 | Finding lights automatically: every triangle painted with an emissive palette cell becomes a light source; lights are merged on a 1.6 m grid; a 1 m light map is baked on the CPU with sight-line checks (`World.los`) and sampled by world position | Metro: 27 lights found, a bright cream hall became a lamp-lit station. No theme data needed |
| P4 | Height and distance fog with a sun-side glow, keeping the full fog wall at the tier's far distance | Works |
| P5 | Thin ink (1.5 px, `#0C0B10`) | Mid and far lines read as a drawn line. Near lines stay thick because of the baked shell (section 4.2); the fix is in Stage 2.7 |
| P6 | Offscreen pipeline: 4x multisampled half-float target, bloom, grade, vignette, grain | Works in r128 |
| P7 | `sampler2DArray` (`THREE.DataTexture2DArray`, mipmapped, repeat) inside a patched `MeshToonMaterial` | Works (`prototype/probe.js`) |
| P8 | Multisampled half-float target **with a depth texture**, depth readable after resolve | Works (`prototype/probe.js`) |

Prototype shortcuts that must **not** ship:

- Surface detail is hash noise computed in the shader. It aliases into "sandpaper" and is slow. Ship
  mipmapped tiling textures (Stage 5).
- Albedo saturation was cut to 0.72. That was wrong (section 1.1): measured saturation fell to 0.12 to 0.23,
  below the references. Ship 0.85 to 1.0 and get the mood from light and value.
- Snow and pale pavements blow out (mountains: 21% of pixels over 0.92). Ship the albedo ceiling and exposure
  rules of section 4.2.
- The light map is one 2D layer for one zone, baked in one blocking call. Ship the level-wide volume baked in
  slices of work (Stage 4).
- The shadow box is fixed on one zone. Ship the player-centred box (Stage 3).
- The viewmodel keeps its own fixed light, so the gun glows in a dark room. Ship the link (Stage 4).
- Surface classes come from quick name guesses. Ship the reviewed table (Stage 5).

---

## 4. Target look (the look bible)

### 4.1 Six pillars

1. **Grounded light.** Outdoors: one sun with real cast shadows and a sky/ground ambient. Indoors: light comes
   from the lamps that are modelled in the room, falls off, and is blocked by walls. Where there is no lamp it
   is dark.
2. **Material truth.** Each surface responds as what it is: concrete is rough and pitted, painted steel has a
   soft highlight and chipped edges, bare steel is brushed, wood has grain and boards, canvas has weave,
   rubber is matte, glass reflects the sky. Up close you see micro detail; from afar you see wear and stains.
3. **Atmosphere.** Depth haze that thickens low and far, glow toward the sun, dust in lamp light, bloom only
   on things that emit light.
4. **Value before colour.** Scenes are darker and have range. Colour stays, accents are deliberate: hazard
   yellow, emergency red, screen teal, lamp amber.
5. **Thin ink.** A 1.5 px near-black line on silhouettes. It thins and fades with distance. No thick toy
   outline, no outlined puff clouds.
6. **Density.** Stains, cracks, leaks, tyre marks, litter, cables, signage. Nothing is a clean flat slab.

### 4.2 Numeric targets (guides; the review sheet is the judge)

Measure with `tests/e2e/look-metrics.py` (Stage 0) on the centre crop (12% to 80% width, 10% to 74% height),
luminance = 0.2126 R + 0.7152 G + 0.0722 B of the screenshot.

| Scene type | Mean | Median | Darkest 5% | Pixels > 0.92 | Pixels < 0.06 |
|---|---|---|---|---|---|
| Exterior, day | 0.32 to 0.46 | 0.25 to 0.42 | 0.04 to 0.14 | under 4% | under 6% |
| Exterior, snow or white sand | 0.40 to 0.55 | 0.38 to 0.56 | 0.06 to 0.18 | under 6% | under 4% |
| Exterior, dusk or night | 0.16 to 0.32 | 0.12 to 0.28 | 0.02 to 0.08 | under 2% | under 20% |
| Interior, lit (mall, office, airport) | 0.26 to 0.40 | 0.22 to 0.38 | 0.04 to 0.12 | under 3% | under 6% |
| Interior, industrial | 0.20 to 0.32 | 0.16 to 0.30 | 0.03 to 0.10 | under 2% | under 10% |
| Interior, dark (mine, metro, seabase) | 0.15 to 0.26 | 0.12 to 0.24 | 0.02 to 0.07 | under 2% | under 18% |

Rules that produce those numbers:

- **Albedo ceiling.** No lit surface albedo above luminance 0.80 (snow 0.86). The shader compresses palette
  colours above the ceiling instead of clipping: `a = a * min(1, ceil / lum(a))`.
- **Albedo saturation scale** 0.85 to 1.0 per theme; emissive, hazard and signage cells are never scaled.
- **Sun to ambient**: clear day about 4:1 on a sun-facing surface against a shaded one; overcast or dusk 2:1.
- **Black floor.** Ambient never falls below a small floor (interior 0.035, exterior night 0.05 in linear
  light) so shapes stay readable. Only ink is black.
- **Bloom** comes only from values above 1.0 in the half-float target. Lit surfaces stay under 1.0 by
  construction; emissive cells write 1.6 to 3.0; sun speculars may exceed 1.0.
- **Ink**: world 1.5 px, viewmodel 1.3 px, colour `#0C0B10`, width multiplied by `1 - smoothstep(45, 110, distance)`
  so far geometry has no line. **The shell is baked 2 cm thick into every kit mesh** (`uBaked`), and today's
  shader only ever adds to it: `VERT_PROJECT` moves the shell by `max( 0.0, wanted - uBaked )`. At 2 m, 2 cm
  is about 5 px at 720p, so near objects keep a thick toy outline whatever `px` says (visible on the crate in
  the mountains prototype shot). Stage 2.7 removes that clamp so the shell can be pulled back toward the
  surface: `max( wanted, 0.001 ) - uBaked`.

### 4.3 Surface classes

Sixteen classes. Every palette cell of every family gets exactly one (Stage 5A builds and reviews the table).

| id | Class | Gloss | Metal | Detail layer | Tile size | Notes |
|---|---|---|---|---|---|---|
| 0 | paint / plastic | 0.30 | 0 | smooth-paint | 1.5 m | chips at edges, light scratches |
| 1 | concrete | 0.10 | 0 | concrete | 2.4 m | formwork panels, pits, hairline cracks; slab joints every 3 m on floors |
| 2 | metal, bare | 0.55 | 0.85 | brushed-metal | 1.0 m | scratches, rust blotches lower gloss |
| 3 | metal, painted | 0.38 | 0.25 | painted-metal | 1.5 m | panel seams, chips showing steel |
| 4 | wood | 0.16 | 0 | planks | 1.2 m | boards 14 cm, grain, knots |
| 5 | fabric / canvas / sandbag | 0.04 | 0 | weave | 0.5 m | |
| 6 | soil / sand / gravel | 0.03 | 0 | ground | 2.0 m | pebbles; ripples on sand |
| 7 | vegetation | 0.06 | 0 | foliage | 0.8 m | wrap lighting, no specular |
| 8 | rock | 0.08 | 0 | rock | 3.0 m | strata and cracks |
| 9 | brick | 0.08 | 0 | brick | 1.29 x 1.20 m | running bond: 6 bricks of 215 mm across, 16 courses of 75 mm up; mortar |
| 10 | tile / ceramic / marble | 0.55 | 0 | tile | 0.6 m | grout lines, glossy |
| 11 | glass | 0.92 | 0.1 | none | n/a | sky reflection, sun glint, dark interior |
| 12 | rubber / asphalt | 0.14 | 0 | asphalt | 2.0 m | aggregate, cracks, patches |
| 13 | snow / ice | 0.25 | 0 | snow | 2.5 m | soft drifts, sparkle in gloss |
| 14 | water | 0.95 | 0 | none | n/a | themes with their own water shader keep it |
| 15 | emissive | n/a | n/a | none | n/a | unlit, boosted, blooms, is a light source |

The detail layers are layers of one texture array (Stage 5B). A shared macro-variation layer breaks large
flat areas on every class.

### 4.4 Look families

Each theme belongs to one family; a family is a preset of light, fog, grade, dust and dressing rules. Theme
overrides sit on top. Section 8 assigns all 46 themes.

| Family | Mood | Sun / ambient | Fog | Grade | Dust | Dressing |
|---|---|---|---|---|---|---|
| `mil-ext` military or industrial exterior | hard, dry, functional | strong sun 4:1 | thin, warm toward the sun | neutral-warm highlights, cool shadows | windblown dust | tyre marks, oil, stencils, sandbag dirt |
| `urban-ext` streets | open shade, lived-in | sun 3.5:1, tall shadows | light haze | slightly cool | none or light | stains under windows, litter, manholes, posters, cables |
| `wild-ext` nature | soft sun through haze | sun 3:1, green bounce | depth haze, strong | natural | pollen, snow, leaves | ground clutter, rocks, grass tufts |
| `ind-int` industrial interior | sodium and white work lights, dark roof | lamps only (+ sky through clerestory) | light haze in beams | cool shadows, warm lamps | dust in beams | oil, hazard paint, floor wear lanes, conduit |
| `dark-int` underground | darkness with pools | lamps only, low floor | thick close haze | cold, teal or amber accents | heavy dust, drips | leaks, puddles, cables, grime |
| `civic-int` commercial or institutional | bright but with range | lamps + window light | very light | clean neutral | none | scuffs, signage, floor reflections |
| `giant-room` toy-scale rooms | a real room at toy scale | window sun + lamps | none | warm | motes in sun | carpet and wood detail, crumbs |

---

## 5. Architecture

### 5.1 New files

| File | Global | Job |
|---|---|---|
| `Source/src/data/looks.js` | `IB.LOOKS` | Look families, per-theme look parameters, tier matrix. Pure data, loads in node for unit tests |
| `Source/src/data/surfaces.gen.js` | `IB.SURFACES` | Generated: family -> 64 surface class ids (+ emissive weight). Written by `tools/gen_surfaces.py` |
| `Source/src/game/look.js` | `IB.Look` | Owns the shared uniforms, resolves the active look (family + theme + tier), `?look=` switches, per-frame update, `flash()` lights, `sampleAt()` for the viewmodel |
| `Source/src/game/surface.js` | `IB.Surface` | GLSL chunks for the world and actor light model; `Surface.patch(sh, mat, kind)` called from `toonMaterial`; surface data textures; detail texture array loader |
| `Source/src/game/shadows.js` | `IB.Shadows` | Sun shadow map, hull-less depth material, player-centred fitting, refresh triggers |
| `Source/src/game/lightgrid.js` | `IB.LightGrid` | Emitter extraction, light volume bake (time-sliced), sky visibility, CPU sampling |
| `Source/src/game/atmo.js` | `IB.Atmo` | Shared fog GLSL and the global `ShaderChunk` fog override, sky shader, dust motes, lamp cones, sun shafts |
| `Source/src/game/post.js` | `IB.Post` | Offscreen targets, bloom, grade, AA, vignette, grain, UI overlay pass, fallback chain |
| `Source/src/game/dress.js` | `IB.Dress` | Decal and clutter scatter at level build |
| `Source/blender/surface_classes.py` | | Name rules + per-family overrides for the class table |
| `Source/blender/fam_dress.py` | family `dress` | Small clutter and fixture pieces -> `fps-dress.glb` |
| `Source/tools/gen_surfaces.py` | | Writes `surfaces.gen.js`, `blender/palettes.gen.json` and one labelled swatch sheet per family |
| `Source/tools/gen_detail.py` | | numpy generator for the detail texture array and the decal atlas -> `Source/assets/tex/` |
| `Source/tools/piece_usage.js` | | Counts how often each kit piece is placed per theme (Stage 11 priorities) |
| `Source/tests/unit/look.test.js`, `surfaces.test.js` | | Data integrity |
| `Source/tests/e2e/look-shots.js`, `look-spots.json`, `look-metrics.py`, `look-sheet.py`, `hud-lock.spec.js`, `look-tour.spec.js` | | Review and gates (section 10) |

Script order in `Source/src/index.src.html` (inside `<!--BUILD:JS-->`): `looks.js` and `surfaces.gen.js` after
`themes.gen.js`; `look.js`, `surface.js`, `atmo.js` right after `render.js` (no material is created while
scripts load: `G.boot` creates them after the page is ready, so `toonMaterial` can call into them);
`shadows.js`, `lightgrid.js`, `post.js`, `dress.js` after `zones.js`. `tools/build.py` bundles in the order of
the script tags. `IB.Atmo.install()` runs first thing in `R.init`, before any material can compile.

### 5.2 Changes to existing files (all small and listed)

| File | Change |
|---|---|
| `render.js` | `toonMaterial` gains `opts.look`: `'world'`, `'actor'`, `'decal'` (Stage 9), `'none'` (default `'none'` so nothing changes until a caller opts in). `R.render` delegates to `IB.Post.render` when post is on. Sky material replaced through `IB.Atmo`. Outline uniforms read from the look. `R.resize` tells `IB.Post`. |
| `assets.js` | Kit and `common` family materials are created with `look: 'world'` and their surface texture. `weapons`, `gear`, `bots`, `troopers` stay `'none'` here (their users decide). |
| `zones.js` | `Z.mat` is created with `look: 'world'`; a per-theme floor class uniform. `Parts.add` unchanged. After a zone is built: `IB.LightGrid.collect(zone)`, `IB.Dress.build(...)`. Cloud puffs hidden when the look is on. The city-below shader (`zones.js:1769`, one of the three custom haze shaders of trap T8) calls the shared fog function. |
| `game.js` | `TIERS` gets the look fields; `G.setTier` calls `IB.Look.setTier`; `G.buildLevel` calls `IB.Look.begin(level)`; the frame calls `IB.Look.update(dt)` before `R.render`; zone changes call `IB.Shadows.refit()`; `disposeLevel` calls `IB.Look.end()`. |
| `ai.js`, `trooperrig.js`, `troops.js`, `boom.js` (debris, canisters), `throwables.js`, `launchers.js`, `fx.js` (gems), `wdrops.js`, `drops.js`, `game.js` (rack and pickup materials) | Opt their world toon materials into `look: 'actor'` (Stage 8). |
| `gunskins.js`, `weapons.js`, `gear.js` | The viewmodel light link: light colour and ambient become uniforms fed by `IB.Look.sampleAt` (Stage 4). No change to gun skins, layers or rarity. |
| `fx.js`, `boom.js`, `weapons.js` | Calls to `IB.Look.flash(...)` at muzzle flashes and blasts (Stage 4); overlay layer flag on comic word sprites (Stage 6); the VFX pass (Stage 12). |
| `ib_lib.py` | `bake_ao` writes the new G and B channels (Stage 5D). |
| `tools/build.py` | Embeds `Source/assets/tex/*` (inline in the single file, a side file `tex-1.js` in the artifact build). |
| `index.src.html` | New script tags only. No markup or CSS change. |
| `tests/e2e/perf.spec.js` | Budgets restated (section 6). |

Theme files (`src/data/themes/*.js`) are **not edited** for the look. Their unit tests assert env values. All
look data lives in `looks.js`, keyed by theme id.

### 5.3 The data flow at run time

```
level load
  Z.buildLevel ......... merged zone meshes (world materials) + emitters recorded per zone
  IB.Look.begin ........ resolve look = family preset + theme overrides + tier
  IB.LightGrid.bake .... emitters -> level-wide light volume (RGB light, A sky visibility), time-sliced
  IB.Shadows.refit ..... sun shadow box centred on the player, rendered once
  IB.Dress.build ....... decals + clutter merged into one extra mesh per zone
each frame
  IB.Look.update ....... flash lights decay, shadow refit when the player moved 8 m, viewmodel light sample
  IB.Post.render ....... world -> viewmodel -> (resolve) -> bloom -> composite (grade, shoulder, vignette, grain)
                         -> UI overlay pass (enemy bars, comic words) straight to the canvas
```

### 5.4 Shader contract

One implementation of the light model, in `surface.js`, used by every lit material:

- Inserted by `toonMaterial`'s own `onBeforeCompile` **after** the outline patch and **before** any caller's
  chained patch, so the existing chains in `ai.js` (`tintMaterial`, `keyTintMaterial`), `trooperrig.js`,
  `projectiles.js` and `gunskins.js` keep finding their anchors.
- Anchors (exact strings in r128's toon shader, verified):
  - vertex: `'#include <common>'` (declare varyings), `'vHull = 0.0;'` (compute world position; this string
    is in `VERT_PROJECT`),
  - fragment: `'#include <shadowmap_pars_fragment>'` (declare uniforms and functions **here**, trap T3),
    `'vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;'`
    (replace with the light model), `'#include <fog_fragment>'` (replace with the shared fog call; the
    outline and cloak code that `render.js` puts around it must stay in the same order: ink, fog, cloak).
- `customProgramCacheKey` gains the look kind and the tier (`'w3'`, `'a2'`...). A tier change sets
  `material.needsUpdate = true` on every look material.
- All look uniforms are shared objects in `IB.Look.U` (one write updates every material).
- Inputs available in the fragment: `diffuseColor.rgb` (palette colour x vertex colour, or vertex colour
  alone on code-built geometry), `vColor`, `vUv` (only with a map: `#ifdef USE_MAP`), `normal` (view space),
  `vViewPosition`, `directionalLights[0]`, `getShadow(...)`, `inverseTransformDirection(...)`, and the new
  `vWP` (world position).
- Albedo and occlusion (trap T5): with a map, `albedo = diffuseColor.rgb / max(vColor.rrr, 0.001)` and the
  occlusion comes from `vColor` (R legacy, G smooth, B wear after Stage 5D); without a map,
  `albedo = diffuseColor.rgb` and occlusion is 1.
- The model, in order: surface lookup -> detail (albedo, gloss, normal) -> albedo grade and ceiling -> sun
  (N.L x shadow x sky visibility) -> ambient (sky/ground hemisphere x occlusion x sky visibility) -> local
  light volume -> flash lights -> specular (sun Blinn-Phong + ambient/volume reflection with Fresnel) ->
  linear to display (`pow(1/2.2)`) -> emissive override -> `outgoingLight`.
- Light maths is done in linear light on `pow(albedo, 2.2)`; the result is written as display values with
  headroom above 1.0. That keeps every legacy unlit material (which writes display values) consistent in the
  same target without touching it.

`prototype/proto.js` holds a working first version of every block (`PARS`, `LIGHT`, `FOG`, `depthMat`,
`buildGrid`, `sky`, `post`). Port it block by block, replacing the shortcuts listed in section 3.

---

## 6. Quality tiers and budgets

| Feature | potato | low | medium | high |
|---|---|---|---|---|
| New light model, light volume, fog, ink, albedo grade | yes | yes | yes | yes |
| Sun shadow map | none (sky visibility only) | 1024, hard | 2048, PCF | 4096, PCF soft |
| Detail textures | none (macro noise in vertex stage only) | macro layer only | 256 px array, one projection | 512 px array, triplanar, anisotropy 4 |
| Normal detail (bumped specular) | no | no | yes | yes |
| Flash lights | 1 | 2 | 4 | 4 |
| Offscreen pipeline | no (grade in the material) | no (grade in the material) | yes, 8-bit or half-float, MSAA 2 | yes, half-float, MSAA 4 |
| Bloom | no | no | 3 levels | 5 levels |
| Vignette, grain | no | no | yes | yes |
| Dust, lamp cones | no | few | yes | yes |
| Decals, clutter density | 25% | 50% | 75% | 100% |
| Sun shafts, ambient occlusion pass, aim depth of field | no | no | no | optional (Stage 6 extras) |

Because potato and low have no composite pass, the per-theme grade (exposure, contrast, tint) is also
available **inside the material** (`#define IB_GRADE_IN_MATERIAL`) so the art direction matches on every tier
(hard rule 5).

Budgets (checked in `perf.spec.js` and `look-tour.spec.js`):

- Draw calls at a zone entry, robots off: desktop under **230**, phone settings under **140** (today's
  budgets 200 and 120 plus the post passes and one dressing mesh per zone). The shadow pass counts only on
  the frames it re-renders.
- Triangles in view: under 750,000 on High after all stages (today 216,000 to 487,000).
- GPU memory for render targets: under 200 MB on High, 80 MB on Medium. Internal render size is capped at
  3.2 megapixels (High) and 2.1 (Medium) whatever the display's pixel ratio; `IB.Post` logs the sizes once.
- Light volume bake: under 1.5 s of main-thread work per zone in total, sliced at 4 ms a frame.
- Added download: detail textures and decal atlas under 2.5 MB; `fps-dress.glb` under 600 KB. Kit GLBs do not
  grow from Stage 5 (vertex colour is already 4 bytes). Stage 11 may grow kits; each kit stays under 4 MB.
- Shader: one world program per tier. Fragment texture units used: palette, gradient (unused but bound),
  surface, detail array, light volume, shadow map = 6 of the 8 guaranteed.

Real frame times cannot be measured here (CPU renderer). The owner's play test at each checkpoint is the
performance gate; `?lookstats=1` prints frame time, draw calls, tier and target sizes to the console every
two seconds for that purpose (console only, nothing on screen).

---

## 7. Stages

Sizes: S = hours of one session, M = a session, L = several sessions, XL = many sessions with workers.

### Stage 0. Safety net and tools (S). No visual change.

Purpose: be able to prove, after every later step, that the HUD is untouched, nothing regressed, and the look
moved toward the target.

Steps:

0.1 Create `Source/docs/tactical-look/PROGRESS.md`. Record base commit `5cfa145`.

0.2 `Source/tests/e2e/look-shots.js`: productise `prototype/base-shots.js`.
   - Arguments: output folder, plan ids. Environment: `LOOK=classic|on` (adds `&look=classic` to the URL once
     that switch exists), `TIER=`, `ZONES=0,1`, `VM=0` to hide the viewmodel.
   - Camera spots come from `tests/e2e/look-spots.json` when the plan has an entry
     (`{ "stronghold": [{ "name": "ledge", "zone": 0, "x": 36, "z": 30, "yaw": 0.7, "pitch": -0.04 }, ...] }`,
     x/z in zone cells as in `map-shots.js`), otherwise the four automatic spots of the prototype (entry,
     mid, mid-back, quarter), found with `IB.Zones.isOpen`.
   - Robots off (`IB.AI.spawn = () => null`), waves cleared, player protected, shake off. One browser, one
     page per plan, 240 s screenshot timeout, 1280 x 720, deviceScaleFactor 1.
   - Hand-pick 8 spots for each pilot map (section 8) so each sheet shows: a long view, a wall up close, a
     floor at a grazing angle, a lamp or window, a prop cluster, a doorway or gate, the trail, and one with
     the gun aimed (`__TEST__` has no aim hook: set `IB.Game.ws.aim = 1` for the shot).
0.3 `Source/tests/e2e/look-sheet.py`: joins "classic" and "on" shots into labelled before/after sheets
   (two columns, 960 px wide cells, JPEG quality 88).
0.4 `Source/tests/e2e/look-metrics.py`: the measurement of section 4.2 for a folder of shots; prints a table
   and exits non-zero when a shot is outside the range given for its scene type in `look-spots.json`
   (`"type": "ext-day"` and so on per plan or per spot). The code is in this plan's history: crop, luminance,
   percentiles, share over 0.92 and under 0.06, HSV saturation.
0.5 **HUD lock**, two parts, both in `Source/tests/e2e/hud-lock.spec.js`:
   - File lock: `git diff --quiet 5cfa145 -- <the protected paths of rule 1.2.1>` must be clean. Print the
     offending files and fail otherwise.
   - Pixel lock: load `?autotest=1&plan=mountains`, robots off, then hide the 3D canvas
     (`document.getElementById('c').style.visibility = 'hidden'`) and put a fixed dark backdrop behind the HUD;
     freeze the HUD state (fixed health, shield, ammo, level, timer text as `hud-shots.js` does at lines
     57 to 60); screenshot at 1280 x 720, 1920 x 1080 and 844 x 390 (touch). Compare with baselines stored in
     `Source/tests/e2e/review/hud-lock/` (commit them now, from this commit). Pass = identical bytes after
     decoding, or at most 0.02% of pixels differing by at most 2/255 (font rasterisation noise).
   - Enemy bar lock (used from Stage 6 on): spawn one soldier at 8 m with `__TEST__.spawnRobot`, damage it so
     the bar shows, freeze, screenshot the bar's screen rectangle with the look classic and on; the bar's
     pixels must match within 3/255 on 99% of its area (antialiasing differs slightly between the two paths).
0.6 Capture the classic baseline for the seven pilot maps (`LOOK=classic` is today's build): shots, sheets,
   metrics table into `PROGRESS.md`. Keep PNGs out of git (put them under `Source/dist/look/`, which is
   ignored); commit only the JPEG sheets under `Source/tests/e2e/review/look/`.
0.7 Run and record today's test status so later failures can be told apart: unit tests (478 pass), then on a
   quiet machine `node Source/tests/e2e/smoke.spec.js`. Known failing checks at this commit: Esc pause, the
   backpack gun card, Overload, respec, a level-load timeout at `downtown` under the CPU renderer, and an
   occasional gun-drop card timing flake. Anything else that fails later is yours.

Gate: `hud-lock.spec.js` passes on the untouched build; look sheets and a metrics table exist for 7 pilots.
Commit: tools, baselines, `PROGRESS.md`.

### Stage 1. Offscreen pipeline, passthrough (M). No intended visual change.

Purpose: move rendering into `IB.Post` with an identity composite, so every later effect has a home and the
risky renderer plumbing is proven before the look depends on it.

Steps:

1.1 `post.js`: `IB.Post.init(renderer)`, `resize(w, h, pixelRatio)`, `render(showViewmodel)`, `dispose()`.
   - Main target: try in order (a) `WebGLMultisampleRenderTarget`, `HalfFloatType`, `DepthTexture`
     (`UnsignedIntType`), samples by tier; (b) the same without multisampling; (c) `UnsignedByteType`;
     (d) no post. After creating a target, bind it once and call
     `gl.checkFramebufferStatus(gl.FRAMEBUFFER)`; r128 does not check for you. Any result other than
     `FRAMEBUFFER_COMPLETE`, or a GL error, moves to the next option. Log the choice once.
   - WebGL1 context (`!renderer.capabilities.isWebGL2`): option (d). The game then runs the material-only
     path of the low tier.
   - Size: drawing-buffer size, capped by the megapixel budget of section 6 (scale both axes).
   - `render`: `setRenderTarget(main)`, `clear(true, true, true)`, sky follows the camera, render world,
     `clearDepth()`, render viewmodel, then the composite full-screen triangle to the canvas
     (`setRenderTarget(null)`). The composite shader is `gl_FragColor = texture2D(tScene, vUv)` for now.
   - Full-screen passes: one `Scene`, one `OrthographicCamera`, one mesh; `depthTest: false`,
     `depthWrite: false`; `frustumCulled = false`.
1.2 `render.js`: `R.render` calls `IB.Post.render` when `IB.Post.on`; `R.resize` calls `IB.Post.resize`.
   `G.setTier` (via `R.resize`) therefore re-creates the targets.
1.3 `ui/thumbs.js` shares the main renderer and binds its own target, saving and restoring the previous one
   (lines 76 to 90). Verify inventory pictures still render (`node tests/e2e/gear-shots.js`, compare with
   `tests/e2e/review/gear-*.png`). No code change expected.
1.4 `game.js:803` `renderer.compile(R.scene, R.camera)`: keep; add a compile of the composite material.
1.5 URL switches in `look.js` (create the file now with only this): `?post=0` forces the direct path;
   `?look=classic` (same as `post=0` for now).
1.6 `renderer.info` is reset manually each frame (`game.js:1149`), so the composite pass adds 1 call. Note
   the new numbers.

Traps: T2, T6, T10, T11.

Gate:
- Look sheets with post on against classic: 99.5% of pixels within 3/255 (edge antialiasing differs).
- HUD lock passes. Unit tests pass. Undercover (`F`, or `__TEST__.setSkills` + the cloak state) still shows
  its black-and-blue look and its CSS flicker on the canvas.
- Tier switch in play (`__TEST__.setTier('low')`, then `'high'`) leaves a correct picture.
- Title screen and the loader are unaffected (`node tests/e2e/screens.spec.js`).

Commit: `post.js`, `look.js` stub, wiring.

### Stage 2. World surface light model, fog, ink, sky (L)

Purpose: the first real step of the look, on world geometry only, without shadows or local lights yet.

Steps:

2.1 `looks.js`: the schema, with defaults for every field (values from the prototype, corrected):

```js
IB.LOOKS = {
  defaults: {
    family: 'urban-ext', type: 'ext-day',
    sunI: 2.6, sunColor: null,                 // null = the theme's env.sunColor or white
    ambSky: [0.55, 0.66, 0.85], ambGround: [0.34, 0.30, 0.27], ambI: 0.62, ambFloor: 0.05,
    albSat: 0.92, albGain: 0.90, albCeil: 0.80,
    fog: { length: 160, far: null, color: null, sunGlow: [1.0, 0.86, 0.66] },   // length: metres to 63% haze at ground level; far/color null = the theme's
    ink: { color: '#0C0B10', px: 1.5, base: 0.0045, fade: [45, 110] },
    sky: { clouds: 0.5, sunDisc: true },       // sunDisc false for themes that draw their own sun or moon
    floor: { cls: 1, gloss: 0.14 },            // class of the code-built floor of this theme
    wet: 0, dust: null, exposure: 1.0,
    grade: { sat: 0.98, contrast: 0.20, lo: [0.96, 1.0, 1.06], hi: [1.05, 1.0, 0.94] },
    bloom: { amount: 0.5, knee: 0.35 }, vignette: 0.35, grain: 0.028,
    grid: { intensity: 1.0, radius: 13, emit: {} },   // emit: { cellName: multiplier } overrides
    indoorAmb: 0.20
  },
  families: { 'mil-ext': {...}, 'urban-ext': {...}, ... },   // section 4.4
  themes: { stronghold: { family: 'mil-ext', type: 'ext-dusk', ... }, ... }   // section 8
};
IB.LOOKS.resolve = function (themeId) { /* defaults <- family <- theme, deep merge of the sub-objects */ };
```
   Unit test `look.test.js`: every campaign theme id has an entry; every entry names an existing family; all
   numbers are finite and inside sane ranges; `resolve` returns every default key.
2.2 `surface.js`:
   - Build the table tooling now (it is Stage 5A steps 5A.1 to 5A.3: `palettes.gen.json`,
     `surface_classes.py`, `tools/gen_surfaces.py`, `surfaces.gen.js`), with the prototype's `classify()`
     rules extended to the 16 classes as the first rule set. The careful review of all 51 families is
     Stage 5A; here only the 7 pilot kits, `kit-parking` (downtown borrows it) and `common` need to be right.
   - `Surface.texFor(family)`: 8 x 8 RGBA `DataTexture`, nearest, no mipmaps, `flipY = false`, texel for cell
     i at `((7 - (i >> 3)) * 8 + (i & 7))` exactly like `gunskins.js` `surfTexture` (line 86). R = gloss,
     G = metal, B = class id / 15, A = 255 for emissive, all from `IB.SURFACES[family]`.
   - GLSL chunks `PARS`, `LIGHT`, `FOG` as string builders taking the kind (`'world'`, `'actor'`) and the
     tier. Port from `prototype/proto.js` with these corrections: no in-shader hash noise except one cheap
     macro term (two octaves of value noise on `vWP * 0.33`); albedo ceiling; saturation default 0.92;
     ambient floor; no light-volume code yet (uniform present, intensity 0); shadow factor present but 1.0
     until Stage 3.
   - `Surface.patch(sh, mat, kind)`: the replacements of section 5.4.
2.3 `render.js` `toonMaterial`: `opts.look` and `opts.surf` (the family surface texture or a flat class
   vector); call `IB.Surface.patch` inside `onBeforeCompile` after the outline code; extend
   `customProgramCacheKey`.
2.4 `assets.js:92`: kit and `common` families get `look: 'world'`. `zones.js:1424`: `Z.mat` gets
   `look: 'world'` and the theme's floor class; because `Z.mat` is shared and lazily created once, set its
   floor uniform in `IB.Look.begin(level)`.
2.5 `atmo.js`. The fog must be one function for **every** material, including the dozens of unlit built-in
   ones (decals, particles, tracers, glows, sprites): a decal fogged differently from the floor it lies on
   shows as a patch. Built-in materials cannot receive custom uniforms, and r128's program cache does not
   notice a changed shader chunk, so the design uses **only three's standard fog uniforms** and a chunk
   override installed once:
   - `scene.fog` stays a `THREE.Fog` (so `fogColor`, `fogNear`, `fogFar` keep flowing to every fogged
     material each frame). In look mode its **`near` carries the haze length** L (metres to 63% haze at
     ground level, `look.fog.length`), and its `far` stays the fog wall distance exactly as today (theme far,
     capped or scaled by the tier in `R.applyFogFar`). Write this in a comment at `R.setFog` and
     `R.applyFogFar`, and make `applyFogFar` set `near = L` in look mode and the theme's near in classic
     mode. Haze length does not change with the tier, so the mood does not either.
   - The function (constants are global, in `atmo.js`):
     ```glsl
     // IB_FOG_HK 0.045 (height falloff per metre), IB_FOG_H0 2.0 (full density below this height), IB_FOG_MAX 0.92
     float ibFogAmount( float depth, float worldY, float hazeLen, float wallFar ) {
       float wall = smoothstep( wallFar * 0.72, wallFar, depth );              // hides zone loading, as today
       float thin = exp( -max( worldY - IB_FOG_H0, 0.0 ) * IB_FOG_HK );
       float haze = ( 1.0 - exp( -depth / hazeLen * thin ) ) * IB_FOG_MAX;
       return max( wall, haze );
     }
     ```
   - **Global override**, installed in `IB.Atmo.install()` before any material compiles (call it at the top
     of `R.init`): replace `THREE.ShaderChunk.fog_pars_vertex`, `fog_vertex`, `fog_pars_fragment`,
     `fog_fragment`. In `fog_vertex` compute the world height without `transformed` (sprites have none) and
     without any new uniform:
     `vFogY = dot( vec3( viewMatrix[0][1], viewMatrix[1][1], viewMatrix[2][1] ), mvPosition.xyz ) + cameraPosition.y;`
     `fog_fragment` becomes `gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, ibFogAmount( fogDepth, vFogY, fogNear, fogFar ) );`
   - **The look is a page-load switch.** `IB.Look.on` is read once from the URL (`?look=classic` turns it
     off). When it is off, `IB.Atmo.install()` leaves the stock chunks alone, `toonMaterial` ignores
     `opts.look`, shadows and post stay off and the puff clouds stay visible: the page renders exactly as
     today. Nothing switches the look while the page is open, so no material ever has to change shader
     family at run time. The review tools load the page twice.
   - The world and actor chunks call the same `ibFogAmount` and then add the sun-side glow, which needs a
     uniform (`uSunDirW`, `uSunFog`) and is therefore only on look materials:
     `fogColor` mixed toward `uSunFog` by `pow( max( dot( viewDirWorld, uSunDirW ), 0.0 ), 6.0 ) * 0.55 * skyVisibility`.
   - The two `ShaderMaterial`s that use three's fog (`boom.js:242` cards, `boom.js:294` smoke puffs) include
     all four fog chunks and name their view position `mvPosition` (checked: `boom.js:217-239` and
     `253-290`), so they pick the override up with no edit. `zones.js:840` hooks `#include <fog_vertex>` for
     the moving lines: the include string stays, so that hook still works.
   - Sky: replace the sky material's shaders with the prototype's smooth gradient + sun glow + soft cloud
     layer (`sky()` in the prototype). Per theme `sky.sunDisc: false` when the theme draws its own sun or moon
     (stronghold, scrapyard, observatory). Keep the uniforms `top`, `horizon`, `uCloak`.
   - Hide `level.cloudMeshes` when the look is on (`zones.js:1934` region); they stay for classic.
2.6 The three custom haze shaders (trap T8): `stronghold.js:357` (waterfalls; its tick at line 500 copies
   `scene.fog` colour, near and far into its own uniforms every frame, and in look mode `near` now holds the
   haze length), `mossgarden.js:388` (stream; reads the theme's fog definition once), `zones.js:1769` (the
   city below; its own haze baked per vertex). Theme files are not edited (section 5.2). Read the three
   sites, then for each choose and record one of: (a) from `IB.Atmo.adoptHaze(level)`, run after
   `Z.buildBackdrop`, overwrite that material's haze uniforms each frame with values that give the same
   haze as `ibFogAmount` at 100 m, 300 m and 1000 m (a linear near/far pair fitted to the curve); (b) leave
   the shader alone and tune the theme's `look.fog` so the vista meets it. `zones.js` is engine code and
   may simply call the shared function.
2.7 Ink: `R.worldOutline.px`, `uOutBase`, `uInk` from the look (`R.updateOutlineK()` after).
   - In `VERT_PROJECT` (`render.js:54`) change the shell offset from
     `max( 0.0, min( uOutMax, max( uOutBase, uOutK * -mvPosition.z ) * uHullK ) - uBaked )` to
     `( max( min( uOutMax, max( uOutBase, uOutK * -mvPosition.z ) * uHullK ), 0.001 ) - uBaked )`
     in look mode only (classic keeps the clamp). Tested in the prototype: near outlines go from about 5 px
     to under 2 px with no artefacts.
   - Add the distance fade (`ink.fade`) as a multiplier on the wanted width.
   - `skillhud.js:63` writes `robotOutline.uInk` every frame for the Undercover look: leave robots' ink to
     it and set only the world ink. Robots share the world's width uniforms (`render.js:276`), which is
     wanted; the Undercover look widens robots through `uHullK` and must still do so (check it).
   - The viewmodel outline (`R.vmOutline`) gets `px` 1.3; its baked shell is 3.5 mm.
2.8 `IB.Look.begin(level)`: resolve the look, write all uniforms, sun colour and intensity
   (`R.sun.color`, keep `R.sun.intensity = 1` and carry intensity in `uSunI`), `uIndoor` from
   `!theme.env.sky` for now (Stage 4 replaces it with sky visibility), the fog colour and haze length
   (through `R.applyFogFar`, step 2.5), the ink, the sky.
2.9 Tune the seven pilot themes roughly (final tuning is Stage 10): sun, ambient, fog, exposure.

Traps: T2, T3, T4, T5, T7, T8, T9, T13.

Gate:
- Sheets for the 7 pilots, classic against on. Exterior metrics inside section 4.2 except shadows-related
  contrast (no shadows yet; expect the mean about 0.05 high). No blown floors (pixels over 0.92 under 4%).
- `?look=classic` sheets match the Stage 0 baseline (99.5% within 3/255).
- HUD lock, unit tests, Undercover check, zcheck unchanged (`map-shots.js` prints `zfight 0` for the pilots).
- Draw calls unchanged from Stage 1.

Commit: `looks.js`, `surface.js`, `atmo.js`, wiring, tests.

### Stage 3. Sun shadows (M)

Steps:

3.1 `shadows.js`:
   - `renderer.shadowMap.enabled = true`, type by tier (`PCFSoftShadowMap` high, `PCFShadowMap` medium,
     `BasicShadowMap` low), `autoUpdate = false`.
   - `R.sun.castShadow = true`; map size by tier; start from the prototype's `bias = -0.0006`,
     `normalBias = 0.03`, `radius = 2.2`.
   - **Hull-less depth material** (trap T1): `MeshDepthMaterial({ depthPacking: RGBADepthPacking })` with an
     `onBeforeCompile` that declares `attribute vec3 aHull;` and, after `#include <project_vertex>`, does
     `if (dot(aHull, aHull) > 0.0) gl_Position = vec4(2.0, 2.0, 2.0, 1.0);`. Assign as
     `mesh.customDepthMaterial` on every caster. Instanced and skinned casters need their own variants
     (`customDepthMaterial` with `skinning: true`; instancing is handled by the built-in chunk).
   - Casters: every world toon mesh that has an `aHull` attribute and is not transparent, except the puff
     clouds, sky dressing and the instanced far forests (frontier, mossgarden). No distance rule is needed:
     the shadow camera is a column along the sun direction, so a far cliff whose shadow reaches the play
     area is inside the column and a far cliff whose shadow does not is outside it. Receivers: every look
     material.
   - **Player-centred box**: orthographic, half-width 70 m (high and medium), 45 m (low), centred on the
     player's position snapped to an 8 m grid and to whole shadow texels; light placed 220 m back along the
     theme's sun direction (`R.applyEnv` stores a direction in `R.sun.position`: keep the direction in
     `IB.Look.sunDir` and never read it back from the moved light). `shadowMap.needsUpdate = true` when the
     snapped centre changes, when a level starts, and for each frame in which a gate, shutter, breakable
     door or elevator is moving (`Z.setGate`, `IB.Doors`, `Z.updateElevators`: set a `Shadows.dirty` flag
     from the look's frame update by comparing their open amounts; do not edit their logic).
   - Outside the box three returns "lit"; fade shadows out over the last 8 m of the box so the edge does not
     show (multiply by a smoothstep on the shadow coordinate).
3.2 In `LIGHT`, the sun term uses `getShadow(directionalShadowMap[0], directionalLightShadows[0].shadowMapSize,
   directionalLightShadows[0].shadowBias, directionalLightShadows[0].shadowRadius, vDirectionalShadowCoord[0])`
   inside `#if defined(USE_SHADOWMAP) && NUM_DIR_LIGHT_SHADOWS > 0`, as the prototype does.
3.3 Robots keep their blob shadows (`FX.blobs`) in this stage; they receive the sun shadow in Stage 8.
3.4 Indoor themes (`env.sky` null): no shadow map at all (saves the pass).

Traps: T1, T12, T14.

Gate:
- Sheets: clean shadows from masts, props and buildings; no acne on floors at 2 m, 15 m and 50 m; no light
  leaking at wall bases (peter-panning under 3 cm); no visible box edge.
- Walk tests still pass (`tests/e2e/stronghold-walk.spec.js`, `frontier-walk.spec.js`); while walking 60 m the
  shadow map refreshes about 7 times, never every frame (log the count).
- Exterior metrics fully inside section 4.2.
- HUD lock, unit tests.

Commit: `shadows.js`, wiring.

### Stage 4. Local lights: the light volume, emissives, flashes, viewmodel link (L)

Steps:

4.1 Emitters (`lightgrid.js` `collect(zone)`), run right after a zone's meshes are merged:
   - For each merged kit mesh: walk the index buffer; a triangle whose first vertex UV falls in an emissive
     cell (`IB.SURFACES[fam].emit[cell] > 0`) adds its area, centroid, palette colour and normal to a hash of
     1.6 m cells (the prototype's `buildGrid` does this).
   - Also walk the zone's glow companion meshes (`level.glows` with `zone === idx`): all their faces are
     emissive by definition, and in many kits the lamp lens exists **only** in the companion (the base piece
     keeps the housing and the ink shell). Companions whose piece name ends in `_Blink` count at half
     strength. The prototype skipped companions; the shipped version must not.
   - An emitter = area-weighted mean position and colour, total area, mean normal. Strength =
     `min(2.2, area * 2.4) * classWeight * look.grid.emit[cellName]`. Class weights: lamp and light cells 1.0,
     fire 1.2 (warm), screens and LEDs 0.35, neon 0.6, holograms 0.25. Cap at 256 emitters per zone (keep
     the strongest).
   - Trails and the hatch room are built by `buildTrail` and `Z.buildHatch` into their own groups: collect
     those too.
4.2 The light volume (`bake(level)`):
   - One level-wide volume (materials are shared by all zones, so per-zone textures would need per-mesh
     uniform switching; one volume avoids that). X/Z cell 1 m on every tier, aligned to the zone grid. Y
     slices at 0.9 m and then every 2.6 m up to the level's highest walkable surface + 2 m, at most 6
     slices. A long level is about 300 x 80 x 6 = 144,000 cells, 0.6 MB as RGBA8.
   - Implement and gate the **single ground slice first** (that is what the prototype proved), then extend
     the same bake loop to the slices.
   - Measured with the prototype (one slice, 1 m cells, this machine): metro 38 ms (27 lights) and 36 ms
     (56), datacenter 56 / 15 / 5 ms (69 / 48 / 24 lights), coal mine 58 / 23 / 20 ms, mall 237 / 195 / 130 ms
     with about 505 uncapped light sources per zone. Six slices and the 256 cap fit the budget easily.
   - Cell value: sum over emitters within `radius` of `strength * colour * 9 / (1 + d²) * (1 - d / radius)`,
     multiplied by 0.12 when `world.los(cell, emitter)` is blocked (keep a little bounce). Skip cells inside
     solid wall cells (zone grid `#`), then fill them from their open neighbours so bilinear filtering does
     not pull darkness out of walls.
   - Alpha = sky visibility, taken from the **drawn geometry**, not from collision boxes (roofs, vaults
     and awnings are often visual only) and not from a per-theme flag (trap T12):
     once per zone, render the zone group straight down with an orthographic camera into a small target
     (2 texels per metre) using the hull-less depth material with RGBA depth packing, read it back
     (`readRenderTargetPixels`), and unpack to "height of the topmost surface" per texel. A cell at slice
     height y sees the sky when that top height is at most y + 0.5 m. A zone with an engine ceiling
     (`theme.env.ceiling && zonePlan.ceiling !== false`) is 0 everywhere without rendering. Blur 5 x 5 so
     covered-but-open places (an awning, a colonnade) keep partial sky light; in a zone where over 40% of
     the cells see the sky, never go below 0.25.
   - 3 x 3 blur per slice. Store as RGBA8 with `rgb = sqrt(light / 4)` (decode `x * x * 4` in the shader) in a
     `THREE.DataTexture3D` (linear filter, clamp). Verify `sampler3D` inside the patched toon material with a
     probe like `prototype/probe.js` first. **Fallback** if it fails or on WebGL1: a 2D atlas of the slices
     with manual interpolation between two slices.
   - Time-slice the bake: at most 4 ms per frame, the player's zone first, then the next zone. The loader
     screen (3.5 s) covers the first zone. Until a zone's cells are baked they hold a flat low ambient.
   - Dispose the texture in `IB.Look.end()`.
4.3 Shader: sample the volume at `vWP + worldNormal * 0.35` (trap T15: pulls the sample off the wall into the
   room it faces). Light volume term = `decoded.rgb * look.grid.intensity * mix(0.5, 1.0, hemisphere)`.
   With `v = decoded.a` (sky visibility), which replaces `uIndoor`: the sun term is multiplied by `v`;
   ambient = hemisphere colour x `ambI` x occlusion x `( v + ( 1.0 - v ) * indoorAmb )` + `ambFloor`.
4.4 Emissive cells: unlit, `albedo * 1.6 to 3.0` by class (lamps high, screens low), flagged by the surface
   texture's alpha.
4.5 Flash lights: `IB.Look.flash(x, y, z, color, radius, life)` fills one of 4 slots (uniform arrays
   `uFlashPos[4]`, `uFlashCol[4]`), linear decay, inverse-square falloff with a radius cutoff, no shadows.
   Call sites: `boom.js` `B.onFire(ws, def)` (line 837; it has no position: use the camera position plus
   0.6 m along the view; radius 6 m, 0.05 s, warm), `B.explode(x, y, z, ...)` (line 564) and
   `B.blast(x, y, z, R, ...)` (line 650; radius from the blast, 0.25 s), enemy muzzle `B.muzzle(x, y, z, size)`
   (line 732, radius 3 m). Halve the intensity when `G.settings.reduceFlash` is on.
4.6 Viewmodel link: `IB.Look.sampleAt(x, y, z)` returns `{ sun, sky, local }` on the CPU: trilinear read of the
   volume data, plus one `world.los` ray toward the sun for 60 m when sky visibility is over 0.5. Smooth over
   0.15 s. Feed: the viewmodel sun colour (`R.vmSun`, expose the light created at `render.js:286`) =
   sun colour x shade; and two new uniforms in `gunskins.js` `FRAG_LIGHT` replacing the constants of its
   ambient line (`vec3( 0.90, 0.82, 0.80 )`, `vec3( 0.95, 1.0, 1.07 )`) with `uVmAmbLo`, `uVmAmbHi`, set from
   the sample (default to those constants so classic is unchanged). Flash lights also light the gun: add the
   nearest flash as a simple additive term.
4.7 Readability floor (hard rule 2): robots get a view-space rim term and their light parts stay emissive in
   Stage 8; in this stage add the measured gate below so tuning cannot make enemies vanish.

Traps: T5, T12, T15, T16, T17.

Gate:
- Sheets for metro, datacenter, stronghold zone 2 (inside the mountain), bedroom: lamp pools visible on
  floors and walls, dark between them, light blocked by walls and big props.
- Emitters found: every pilot interior zone reports between 8 and 256; print the count and the bake time.
  Bake work under 1.5 s per zone in total and never more than 6 ms in one frame (measure with
  `performance.now()` around each slice; the CPU here is representative for this, unlike frame times).
- Interior metrics inside section 4.2.
- **Enemy readability**: in metro and coalmine, spawn a Crawler and a Soldier at 12 m and 30 m in the
  darkest open cell of the zone (lowest volume value); the mean luminance difference between the robot's
  pixels and a 16 px ring around it must be at least 0.06 (compute from a shot with and without the robot).
- The gun is dark in a dark room and brightens under a lamp (two shots, same map).
- HUD lock, unit tests, draw calls unchanged.

Commit: `lightgrid.js`, shader, flash calls, viewmodel link.

### Stage 5. Material detail (XL: four parts, 5A and 5B can run in parallel)

#### 5A. Surface class table for all 51 families

5A.1 `tools/gen_surfaces.py` imports every `fam_*.py` the way `build_assets.py` does (lines 31 to 35; about
    half a minute, nothing is built). After the imports `ib_lib.PALETTES` holds every family's
    `[(name, hex), ...]` in cell order. Write it to `Source/blender/palettes.gen.json` (committed; node tests
    read it, since the names are not in the GLBs).
5A.2 `blender/surface_classes.py`: an ordered list of `(regex, class)` rules and
    `OVERRIDES = { 'kit-metro': { 'cream': 10, ... }, ... }`. Start from the prototype's `classify()` and
    extend it for the 16 classes. The most common names and their classes: `steel`, `steelD`, `steel2`,
    `chrome`, `iron`, `galv` -> 2; `gunmetal`, `plate`, `panel`, `olive` on equipment -> 3; `conc*`,
    `stone*`, `plaster`, `stucco`, `ceil` -> 1; `rock*`, `cave*`, `cliff` -> 8; `brick*` -> 9; `tile`,
    `marble`, `pool` floor -> 10; `wood*`, `oak*`, `walnut*`, `plank`, `crate`, `trunk`, `bark` -> 4;
    `canvas`, `tarp`, `bag*`, `rope`, `curtain`, `carpet` -> 5; `soil`, `sand`, `gravel`, `dirt` -> 6;
    `leaf*`, `grass*`, `moss`, `hedge` -> 7; `glass*`, `lens` -> 11; `tire`, `rubber`, `asph*`, `cable` ->
    12; `snow`, `frost`, `ice` -> 13; `water*` -> 14; `lamp*`, `light*`, `glow`, `screen*`, `scr*`, `fire`,
    `beacon`, `neon`, `exitG` -> 15. Plain colour names (`teal`, `amber`, `red`, `navy`, `cream`, `white`,
    `paper`...) are paint (0) unless the family override says otherwise.
5A.3 The script writes `src/data/surfaces.gen.js`
    (`IB.SURFACES = { 'kit-metro': { cls: [64 ints], emit: [64 floats], names: [...] }, ... }`) and one swatch
    sheet per family (`Source/dist/look/surfaces/<family>.png`: each cell's colour, name and assigned class).
5A.4 **Review every sheet** (51 sheets, 1,143 names). Fix wrong guesses in `OVERRIDES`. Typical errors to
    look for: a colour name used for a material (`cream` wall tile, `navy` fabric), `far*` cells (painted
    backdrop: class 0, no detail, never emissive), sign and screen cells that are dark (`screenD`: not
    emissive), `ink` and `HULL` (class 12, no detail).
5A.5 `surfaces.test.js`: every family in `IB.ASSET_FILES` has an entry; 64 classes each in 0 to 15; names
    match `palettes.gen.json`; every family with a `lamp`-like name has at least one emissive cell; `HULL`
    and `ink` are never emissive.

#### 5B. The detail texture array

5B.1 `tools/gen_detail.py` (numpy + Pillow). For each layer make a **tileable** 512 x 512 height field, then
    derive: normal (periodic central differences), roughness variation, albedo variation. Tileable by
    construction: band-limited noise by filtering white noise in the Fourier domain (`np.fft`), cellular
    patterns with wrap-around distance, grids with integer periods.
    Layers (index = array layer):
    0 macro variation (blotches 0.5 to 4 m, used by every class), 1 concrete (fine pits + formwork panel
    lines 1.2 x 2.4 m with tie holes + hairline cracks), 2 brushed metal (anisotropic streaks + sparse
    scratches + rust mask in the roughness channel), 3 painted metal (very smooth + chips + a few seams),
    4 planks (14 cm boards, staggered ends, grain, knots), 5 weave, 6 ground (clumps + pebbles),
    7 foliage (leaf clusters), 8 rock (strata + cracks), 9 brick (running bond + per-brick tone), 10 tile
    (30 cm, grout, a few chipped corners), 11 asphalt (aggregate + cracks + patch outlines), 12 snow,
    13 smooth paint / plaster (orange-peel + scuffs).
    Packing per layer in the GPU texture, RGBA8: R = albedo multiplier (128 = x1.0, range x0.6 to x1.4),
    G = gloss multiplier, B and A = normal x and y (128 = flat).
5B.2 Output files: **two opaque RGB strips**, never data in an image's alpha channel (trap T26):
    `Source/assets/tex/detail-a.webp` (R albedo, G gloss, B height for later use) and
    `detail-n.webp` (R normal x, G normal y, B unused), each a vertical strip 512 x 7168 (14 layers). The
    loader combines them into the RGBA array. Make a 256 px pair for the Medium tier by downsampling at load
    (no second download). WebP quality 90; if normals show block artefacts at that quality, store
    `detail-n` lossless. Target under 1.8 MB for both files.
5B.3 Checks the script runs itself: seam test (left/right and top/bottom edge columns differ from their
    neighbours no more than interior neighbours do), mean of R and G within 2 of 128 (a layer must not
    brighten or darken on average), normal length valid. It also writes a preview sheet (each layer tiled
    3 x 3 and lit from the upper left) to `Source/dist/look/detail-preview.jpg`. **Look at it.** Each layer
    must be recognisable as its material at a glance; redo any that reads as generic noise.
5B.4 `tools/build.py`: embed the strips as data URLs (`IB.TEX_DATA`), in a side file `tex-1.js` for the
    artifact build (same pattern as `glb-N.js`, lines 91 to 103).
5B.5 `surface.js` loader: decode each strip with an `Image` + canvas (`getImageData`) into bytes, interleave
    into one `Uint8Array`, build `THREE.DataTexture2DArray` (RGBA, `LinearMipmapLinearFilter`,
    `RepeatWrapping`, `generateMipmaps = true`, anisotropy by tier). Load before the first level starts (it
    is in the page, no network). Shader needs `precision highp sampler2DArray;` (trap T18). Unit-check the
    decode in the page once: the mean of the decoded R and G channels of each layer is within 3 of 128.

#### 5C. Shader integration

5C.1 Per class: layer index, tile size, normal strength, albedo and gloss amounts, as a small uniform table
    (16 x vec4) or constants in the chunk.
5C.2 Projection: world-space triplanar. Weights from `abs(worldNormal)` raised to the 4th power. High tier:
    three samples. Medium: one sample on the dominant axis with a dithered hand-over. For classes with a
    direction (brick, planks, tile, concrete panels) the wall projections use world Y as V so courses run
    level, and they line up across neighbouring pieces because the coordinates are world space.
5C.3 Macro layer sampled at 1/6 scale on every class. Detail fades out between 30 m and 80 m (rely on
    mipmaps too) so nothing shimmers.
5C.4 Normal: reconstruct z, blend onto the geometric normal (whiteout blend), strength by class and tier.
5C.5 Wear from vertex data (after 5D): G = smooth occlusion drives grime and darkening; B = wear raises
    albedo slightly and gloss on painted classes (exposed metal), lowers it on concrete.
5C.6 Class specials: glass (class 11) = reflection of the sky gradient by the reflected view direction +
    sun glint + 12% of the palette colour, with a darker "interior" at steep angles; vegetation = wrap
    diffuse `(N.L + 0.4) / 1.4`, no specular; snow = sparkle from the gloss channel; water (14) outside
    themes with their own water = glossy dark with sky reflection.
5C.7 Floors: slab joints, tile grout and plank lines come from the detail layers now; remove the
    prototype's procedural joint lines.

#### 5D. Better baked vertex data

5D.1 `ib_lib.bake_ao` for `kit-*` and `common` families only (weapons, gear, bots, troopers use the colour
    for other things: `wpn_core.cavity`, the trooper mask):
    - First run today's bake exactly as it is (24 samples, piece alone, posterised to 1.0 / 0.87) and keep
      its result for channel **R**. The classic look reads R and must not move.
    - Then bake a second time into a scratch attribute: add a temporary ground plane at z = 0 (20 m square,
      hidden again afterwards) so everything darkens toward the floor it stands on; 48 samples; AO distance
      1.5 m (`scene.world.light_settings.distance`; the build's empty scene has no world, so create one
      first, and confirm the property name against `bpy` 5.3 before relying on it). Write that value,
      **not posterised**, to channel **G**.
    - Channel **B**: wear = clamp(0.5 + 0.5 x (mean signed dihedral angle of the sharp edges at the vertex)
      / 90°): above 0.5 on convex corners, below on concave. Computed from the mesh, no bake.
    - Alpha stays 1.
    - `Col` is a per-loop float colour attribute; the exporter and `quantize_glb.py` already carry RGBA as
      uint8, so file sizes do not change.
    - Tune the recipe on the pilot kits only, building into a scratch folder (set `ib_lib.OUT`, as
      `scratchpad/gunqa/build_one.py` does for guns) and loading those GLBs through the dev page. Rebuild
      and commit all families once, when the recipe is final.
5D.2 Before rebuilding, save a copy of all GLBs. Rebuild every kit and `common`
    (`python3 build_assets.py --family <each>`; about 6 s to 30 s each).
5D.3 Proof that nothing else moved: a script that, for every rebuilt GLB, compares accessor by accessor with
    the saved copy: POSITION, NORMAL, TEXCOORD_0, `_HULL`, indices and node transforms must be byte-identical
    (or the piece list identical where Blender reorders), only COLOR_0 may differ, and its R channel may
    differ on at most 1.5% of vertices (Cycles noise at the two-step threshold). Any other difference: stop
    and find out why before going on.
5D.4 `assets.js` `prepGeometry` already copies R, G, B into the `color` attribute (line 50). Trap T5: the
    legacy shader multiplies the diffuse by `vColor.rgb`, so with G and B no longer equal to R the **classic**
    look would tint. In `toonMaterial`, for materials with a map, always replace `#include <color_fragment>`
    with `#ifdef USE_COLOR` / `diffuseColor.rgb *= vColor.rrr;` / `#endif` (classic and new alike; for the
    weapon, gear, robot and trooper families R = G = B, so nothing changes for them). Code-built geometry
    (no map) keeps the stock chunk because its vertex colours are real colours.
5D.5 Unit tests (`assets.test.js`, all `theme_*.test.js`) must pass on the rebuilt GLBs.

Traps: T5, T18, T19, T20.

Gate for Stage 5:
- Swatch sheets reviewed, `surfaces.test.js` green.
- Detail preview sheet reviewed; seam and mean checks green.
- Pilot sheets: at 1 m a concrete wall, a steel panel, a wooden crate, a brick wall and a floor each read as
  their material; no visible tiling pattern on a 60 m floor seen from standing height; no shimmer between
  two shots taken 0.3 m apart.
- `?look=classic` still matches the Stage 0 baseline.
- The GLB comparison of 5D.3 is clean. Total asset size within 1% of before.
- HUD lock, unit tests, draw calls unchanged. Download growth under 2.5 MB.

Commit in four commits (5A, 5B, 5C, 5D).

### Stage 6. Post stack and UI isolation (M)

Steps:

6.1 Bloom: bright pass = `max(colour - 1.0, 0)` with a soft knee, from the resolved half-float target, then
    a down/up chain (5 levels High, 3 Medium) with 9-tap separable blurs or a dual filter. On the 8-bit
    fallback use a luminance threshold of 0.9 and half the amount.
6.2 Composite, in this order: exposure -> add bloom -> saturation -> split tone (`lo`/`hi` tints by
    luminance) -> contrast curve around mid grey -> highlight shoulder
    (`c / (1 + max(c - 0.82, 0) * 0.9)`, identity below 0.82 so legacy unlit effects keep their exact colours
    in the mid range) -> vignette -> grain (luminance weighted, animated) -> triangular dither of 1/255.
6.3 Antialiasing: MSAA from the target (4 High, 2 Medium). If the fallback chain landed on a
    non-multisampled target, add an FXAA pass in the composite.
6.4 **UI overlay pass** so in-world interface elements skip bloom, grade and grain (hard rule 1):
    - Overlay objects live on `THREE` layer 1: the enemy health bar mesh (find it with
      `R.scene.getObjectByName('hpbars')` after `IB.HPBars` initialises; `hpbars.js` is not edited) and the
      comic word sprites and meshes (`fx.js:164`, `boom.js:1164`; these files may be edited: set
      `layers.set(1)` where they are created).
    - Main pass: `camera.layers.set(0)`. After the composite: `camera.layers.set(1)`, render the world scene
      to the canvas without clearing, then restore layer 0.
    - The health bars are depth-tested against the world. The canvas has no scene depth, so patch the bar
      material **at run time** from `post.js`: prepend to its fragment shader a uniform `tSceneDepth` and
      `if (texture2D(tSceneDepth, gl_FragCoord.xy * uInvRes).r < gl_FragCoord.z - 0.00002) discard;`, set
      `depthTest = false` on it for the overlay pass. `gl_FragCoord.z` is comparable because the same camera
      draws both passes. With the post path off (low tiers, classic, a failed target) leave the material
      alone and keep every overlay object on layer 0, where it renders as today; move objects between the
      layers when the tier changes.
    - Comic words already have `depthTest: false`.
    - Everything else stays in the world pass on purpose: loot beams, reach rings, trail arrows and pickups
      are part of the scene and may bloom.
6.5 Potato and low tiers (no composite): the same exposure, contrast and tint maths runs at the end of the
    look materials' shader (`IB_GRADE_IN_MATERIAL`). Unlit effect materials are not graded on those tiers
    (they cannot take per-theme uniforms, trap T28); that is accepted. Check one pilot on `TIER=low`
    against `TIER=high`: same mood, mean luminance within 0.04.
6.6 Optional extras, each behind a look flag, each only if the owner's play test shows frame time to spare
    on High: (a) ambient occlusion pass at half resolution from the depth texture (8 taps, normals from
    depth, bilateral blur, applied to non-emissive pixels); (b) depth of field while aiming (half
    resolution, near field only, strength by `ws.aim`); (c) sun shafts (radial blur of the bright sky mask
    toward the sun's screen position, exterior themes).

Traps: T2, T6, T10, T11, T21.

Gate:
- Enemy bar lock of Stage 0.5 passes; comic words look the same as classic in `vfx-shots.js`.
- Bloom only on lamps, screens, fire, muzzle flashes, sun glints and the sky near the sun. A white wall in
  full sun does not bloom.
- No banding in a dark fog gradient (zoom a shot of the coal mine).
- Metrics for all pilots inside section 4.2; `TIER=low` check of 6.5.
- Draw calls inside the section 6 budgets (`perf.spec.js` with the new numbers).

**OWNER CHECKPOINT 1 (after Stage 6).** Build, publish the artifact, and give the owner: the before/after
sheets of the 7 pilots, the metrics table, and the play links (`?plan=mountains`, `stronghold`, `downtown`,
`metro`, `datacenter`, `bedroom`, `mall`). Ask for: frame rate and tier shown by `?lookstats=1` on their
machine, and a yes or change request on (1) how dark interiors are, (2) ink thickness, (3) colour, (4) bloom
and grain. Do not go on to Stage 9 or later before the answer; Stages 7 and 8 can proceed meanwhile.

### Stage 7. Atmosphere extras (M)

7.1 Dust motes: one `Points` or instanced-quad cloud of 400 (High) / 150 (Medium) particles in a 14 m box
    that wraps around the camera, drifting slowly; brightness from the light volume at the camera (one CPU
    sample per frame, not per particle) and from the sun when sky is visible. Types per look: dust, snow
    (arctic and mountains already have theme snow in places: do not double), embers (foundry), pollen
    (garden, grove), none. Seabase already has marine snow.
7.2 Lamp cones: for emitters whose mean normal points down (y under -0.6) and whose class is lamp: one
    additive cone, soft at the edges (fade by the angle to the view), 32 nearest at most, one instanced draw
    call. Height = distance to the floor below (`world.floorAt`). On High fade against the scene depth
    (soft intersection).
7.3 Wetness: `look.wet` 0 to 1 raises gloss on upward faces in patches (macro layer as the mask) and
    darkens albedo there. Candidates: parking, metro track level, seabase, cargoship deck, scrapyard (night
    rain look). Decide per theme in Stage 10.
7.4 Sky: cloud layer amount and tint per theme; night themes keep their own stars and moon; dusk themes keep
    their bands.
7.5 Seabase: slow caustic pattern multiplied into the light volume term on upward faces (two scrolling
    samples of the macro layer).

Gate: sheets show the additions; they are absent on low and potato; draw calls +3 at most; metrics unchanged
(dust and cones must not lift the mean by more than 0.02).

### Stage 8. Actors, pickups and the viewmodel match (M)

8.1 `look: 'actor'` for robot materials (`ai.js:196, 198, 200, 203`), troopers (`trooperrig.js:85`), debris
    and canisters (`boom.js:1172, 1174, 1188`), thrown cans, rockets, crates, racks and pickups, gems,
    dropped weapons. The actor chunk: same light model without triplanar detail; instanced world position
    (`instanceMatrix`), skinned variant for troopers; samples the light volume and the sun shadow at its own
    fragment position. Surface data: `bots` and `troopers` palettes get entries in `surface_classes.py`
    (armour = painted metal, joints = rubber, visor and lights = emissive).
8.2 Their existing patches must still apply (trap T4): `tintMaterial` replaces
    `'if ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );'`, `keyTintMaterial` hooks `map_fragment`, the
    trooper patch hooks the hull line. Keep those strings intact and in the same order in the patched
    shader. Test: hit flash (white), ink flash, soldier armour colours, Crawler two-tone skin, Undercover
    robot outline (bright blue) all still show (`node tests/e2e/troops.spec.js` with `SHOTS=1`,
    `latebots.spec.js`).
8.3 Rim light for readability: view-space rim on actors, strength by how dark the local light is.
8.4 Robot light parts (`AI.lightMat`) and the Hawk's accent strips are emissive (bloom).
8.5 Smoke puffs (`boom.js:294`) have a fixed light uniform `uLight`: feed it the sun direction and scale it by
    the light sample at the puff so smoke is not bright in dark rooms.
8.6 Guns lying or hanging in the world (weapon racks `game.js:240`, stands `game.js:357`, drops
    `wdrops.js:202`) use `IB.GunSkins.material(...)` with the world outline set. Their own light code
    (`FRAG_LIGHT`) reads the world sun unshadowed, so they would glow in a dark armoury. For those
    world-outline instances only, multiply `FRAG_LIGHT`'s sun term by the shadow and sky visibility and its
    ambient by the light volume sampled at the fragment's world position, using the same GLSL helpers as
    the actor chunk. Viewmodel and thumbnail instances are different material objects (the cache key
    includes the outline set, `gunskins.js:225`) and are not touched by this.
8.7 Inventory pictures (`ui/thumbs.js`) must not change: verify with `gear-shots.js` against
    `tests/e2e/review/gear-*.png` and the field-kit screens of `screens.spec.js`.

Gate: troop and late-bot sheets; enemy readability gate of Stage 4 re-run with the final actor shading; HUD
lock; unit tests; smoke test.

### Stage 9. World dressing: decals and clutter (L)

9.1 Decal atlas (`tools/gen_detail.py`, second output): 1024 x 1024, 8 x 8 cells, alpha. Types: oil stain,
    water stain, rust streak (vertical), leak streak, soot, crack (3), tyre arc, scuff lane, puddle mask,
    patch repair, drain cover, manhole, floor grate, paint arrow, hazard chevrons, bay number digits,
    stencil text blocks, torn poster (3), paper litter, leaf scatter, mud print, bullet scars (old). Greyscale
    and alpha; colour comes from a tint per placement. This atlas is used directly as an image texture
    (true transparency, no pixel read-back), so trap T26 does not apply to it.
9.2 `dress.js` `build(level, zone)`: deterministic (hash of cell coordinates), using the zone grid:
    - Floor decals on open cells: weighted toward wall bases, corners and under large props; scale 0.6 to
      3 m; random yaw; 4 mm above the floor with `polygonOffset`.
    - Wall decals on the open side of wall cells: streaks from the top, stains at the base, posters and
      stencils at 1.2 to 2.2 m, only on wall modules whose piece is in the family's "plain wall" list (never
      on windows, doors, shutters, glass, screens).
    - Never within 1.5 m of: gates, trail arrows, pickups (`a`, `h`), spawn cans (`S`), weapon stands,
      elevators, stairs and ramps (walkable boxes), water, breakable doors.
    - Decals are **lit**: a fourth look kind, `look: 'decal'`, an alpha-blended variant of the world chunk
      (light volume + sun + shadow, no detail, `depthWrite: false`, `polygonOffset`), so they do not glow in
      the dark. One merged mesh per zone, `renderOrder` after the world. They cast no shadow.
9.3 Clutter family `fam_dress.py` -> `fps-dress.glb`: about 30 pieces under 300 triangles each: rubble
    chunks, bricks, cans, bottles, cardboard, paper stacks, cable coils, pipe offcuts, pallets broken flat,
    leaves pile, stones, tufts of grass, cigarette-butt-scale litter, floor cable runs (1 m modules), wall
    conduit (1 m modules) with junction boxes, small vents, fire extinguisher, warning sign plates. All with
    ink shells no thicker than 1 cm, **no collision boxes**.
    Placed through the existing `Parts.add` into the zone's merge, so it costs one extra mesh per zone.
    The family must always be loaded: add `'dress'` to the boot list at `game.js:49`
    (`['common', 'weapons', 'bots', 'gear', 'troopers']`). Give it a palette, a surface table entry, names
    in `IB.ASSET_NAMES` and budgets in `IB.TRI_BUDGET` so `assets.test.js` covers it. Its pieces are placed
    by full name (`KIT_`-style prefixes pass through `IB.themePiece` unchanged, `themes.js:95`), so name
    them `KIT_DRESS_<Piece>`.
9.4 Rules per look family in `looks.js` (`dress: { floor: [[type, weight], ...], wall: [...], clutter: [...],
    density: 1.0 }`), theme overrides in Stage 10.
9.5 Density scales with the tier at level build.

Traps: T22, T23.

Gate:
- `?zcheck=1` (`map-shots.js`) reports no new z-fighting on the pilots.
- `node tests/e2e/collision-audit.spec.js` and `bounds.spec.js` unchanged; the walk tests of the pilot themes
  pass (nav unchanged because nothing is solid).
- Sheets: floors and walls are no longer clean; nothing floats, nothing covers a gate, sign, pickup or
  arrow; no decal is stretched over an edge.
- Draw calls +2 per visible zone at most. HUD lock, unit tests.

### Stage 10. Art direction for all 45 maps (XL)

10.1 Pilots first (final tuning of the 7): for each, the checklist below, eight hand-picked spots, metrics
     inside range, before/after sheet committed, parameters in `looks.js`.
10.2 **OWNER CHECKPOINT 2**: publish, show the 7 final pilot sheets. Roll out only after agreement.
10.3 Roll out in the batches of section 8, one look family at a time, in campaign order inside a family.
     After each batch run `look-tour.spec.js` over **all** themes tuned so far: shared shader changes must
     not drift earlier maps (metrics still in range, no console errors).

Per-theme checklist (copy into `PROGRESS.md` for each theme):

1. Family and scene type set; floor class set per zone where zones differ (zone plans with their own
   `floor`).
2. Sun: direction from the theme (unchanged), colour and intensity tuned; shadows read well from the entry.
3. Ambient sky and ground colours taken from the theme's own sky and floor colours.
4. Fog: colour (start from the theme's) and haze length; the far vista and the theme's own haze shaders
   agree.
5. Emitters: count per zone sane; lamp cells emit; screens do not overpower; dark zones have no black holes
   on the walk route (add `grid.emit` multipliers, or raise `indoorAmb` a little; never add fake lights
   that have no fixture).
6. Surface classes: walk the swatch sheet against the map; fix overrides.
7. Exposure and grade; metrics inside the range for its type.
8. Dust type, wetness, sky clouds.
9. Dressing rules and density; theme-specific exclusions.
10. Special systems still right: water (island, cargoship, pelagic, resort, riviera, venetian, seabase,
    mossgarden), city below (office, spire, hotel, techhq, highrise), terrain (grove, arctic, resort,
    frontier, mossgarden, observatory), moving lines (factory, factory2), elevators, breakable doors,
    glow blink groups, theme ticks.
11. Eight review shots + before/after sheet; `zfight 0`; the theme's own e2e test (walk or climb spec)
    passes; unit test of the theme passes.
12. Enemy readability check if the theme is dusk, night or a dark interior.

### Stage 11. More map geometry detail (XL, with workers)

Purpose: the owner asked for much more detail in the maps. Stages 5 and 9 add it to every surface without
modelling; this stage adds real modelled detail where it shows most.

11.1 `tools/piece_usage.js`: for every theme, count placements of each piece across its zone maps (run the
     level build in node or in the page and count `Parts.add` names) and the visible area (bounding box face
     area x count). Output a ranked list per kit. The top 15 to 25 pieces of a kit cover most of the screen.
11.2 Shared detail helpers in `Source/blender/kit_base.py` (the kit equivalent of `wpn_core.py`'s detail
     kit): `panel_seams`, `bolt_row`, `kick_plate`, `corner_guard`, `conduit_run`, `junction_box`, `vent`,
     `cable_tray`, `pipe_run` with brackets, `base_trim`, `cap_trim`, `sign_plate`, `rivet_strip`,
     `drip_edge`, `window_frame_depth`. All `ink=False` small parts (no outline shell), all staying 3 mm
     proud of their surface to pass the z-fight check.
11.3 Budgets raised on purpose, in one commit with the tests that assert them: per prop 1,200 -> 2,500
     triangles, landmark 4,000 -> 8,000, kit total (one of each) 40,000 -> 90,000
     (`IB.TRI_BUDGET.kitMax`, `kitPropMax` in `src/data/assets.js:75`, and each theme's own
     `budget: { prop, landmark, total }`). Zone total stays under the section 6
     triangle budget: check with `stats.js` after each kit.
11.4 Rules for every kit pass. **Never change**: piece names, origins, footprints, `_COL` / `_WCOL` boxes,
     socket empties, the faces robots walk on, wall module mating edges (neighbouring modules must still
     meet), palette cell order (the `paint` symbol option remaps cells by index). New palette cells only in
     free slots; many kits use all 64.
11.5 Do `kit-stronghold` first, alone, as the exemplar (walls, cliff modules, bunker faces, parapets, crates,
     the helipad, the command centre). Write `Source/docs/tactical-look/KIT-BRIEF.md` from what worked (as
     the gun pass did with its brief): the helpers, the rules, the review loop, the budgets, the done
     definition.
11.6 Then workers, one kit each, each in its own git worktree, editing only that kit's Python files. Review
     loop per worker: build the one kit (`build_assets.py --family kit-x`), a piece sheet rendered **in the
     game look** (a small page that loads one family and shows chosen pieces lit by a sun and a lamp, with
     the world material), then in-level shots at the theme's eight spots.
11.7 Order: the 7 pilot kits, then by campaign order (players see early levels first). Tier A = pilots;
     Tier B = levels 1 to 15 not yet done; Tier C = the rest. **OWNER CHECKPOINT 3 after Tier A**: show the
     seven kits before/after and agree how far down the list to go.
11.8 After each kit: unit tests (the theme's test checks ramps, stairs and run pieces on the GLB), the
     theme's e2e walk test, collision audit, `zfight 0`, look-tour metrics for that theme, GLB under 4 MB.

### Stage 12. Effects pass (M). Ask the owner first (section 11, question 4).

Tactical in substance, comic in accent:

- Muzzle flash: keep the ink-edged star, add a hot core and a brief smoke wisp; the flash light already
  exists from Stage 4.
- Impacts by surface class (`B.impact` at `boom.js:668` receives the hit box; look the class up from the
  nearest world triangle's cell or, cheaper, from the theme floor class and a per-box class tag set at
  build): sparks on metal, dust puff on concrete and rock, splinters on wood, dirt on ground, a glassy
  tick on glass.
- Bullet marks: class-specific decal cells instead of the one comic hole.
- Tracers: thinner, faster, emissive (bloom).
- Explosions: keep words and cards; add the flash light, a dark smoke layer lit by the volume, and scorch
  decals that are lit.
- Shell casings, gems, loot beams: unchanged apart from lighting.

Gate: `vfx-shots.js` sheets before/after; `perf.spec.js` VFX stress inside budgets; Reduce flash respected.

### Stage 13. Final pass and release (M)

13.1 `look-tour.spec.js` over all 45 plans: load, the automatic four shots per zone 0, metrics, console
     errors 0, draw calls and triangles inside budgets, `zfight 0`. A sheet per look family.
13.2 Every e2e test in `Source/tests/e2e/*.spec.js`, one at a time on a quiet machine; compare failures with
     the Stage 0.7 list.
13.3 Tier check: one map per family on each of the four tiers; mood identical, features as in section 6.
13.4 Fallback check: force each step of the target fallback chain (`?posttest=b`, `c`, `d`) and WebGL1
     (`?webgl1=1` creates the renderer as `THREE.WebGL1Renderer`, which r128 has) and confirm a correct
     picture.
13.5 Sizes: `Play Inkbolt.html`, each artifact file under 16 MB, the asset total.
13.6 README section "Look" (how the system works, where the knobs are), update `PROGRESS.md`, delete nothing
     from `docs/tactical-look/`.
13.7 Build, list the published artifact's files, republish to the same URL, commit, push.
13.8 Owner play test list: one map of each family from the campaign, frame rate, tier reached, anything that
     reads as "toy" still.

---

## 8. Themes, families and order

Pilots are marked **P**. Batches follow the family order below; inside a batch, campaign order.

| # | Theme | Setting | Family | Type | Notes for the look |
|---|---|---|---|---|---|
| 1 | mountains **P** | alpine valley, snow, day | wild-ext | ext-snow | First impression of the game. Snow albedo ceiling 0.86; pines get the foliage class; hide the comic clouds |
| 2 | smallcity | brick main street, late afternoon | urban-ext | ext-day | Low warm sun, long shadows |
| 3 | classroom | giant classroom | giant-room | int-lit | `LightPanel` ceiling emitters every 12 m |
| 4 | office | tower floor + city below | civic-int | int-lit | Mixed: sky dome and a 4 m ceiling; the city-below shader has its own haze |
| 5 | bedroom **P** | giant bedroom | giant-room | int-lit | Proves the look on a whimsical map: a real room at toy scale, window sun, wood and carpet detail |
| 6 | coalmine | room-and-pillar mine | dark-int | int-dark | Fog near 18 m today; lamps on rock; readability gate |
| 7 | castle | sandstone wards, summer | urban-ext | ext-day | Stone and rock classes, torches emit warm |
| 8 | city2 | brownstone downtown, sunset | urban-ext | ext-dusk | Sun very low (0.42 elevation component), strong sun-side fog glow |
| 9 | factory | robot assembly, dusk clerestory | ind-int | int-ind | Mixed sky + 10 m roof trusses; moving lines are instanced (trap T13) |
| 10 | livingroom | giant open-plan house | giant-room | int-lit | Fireplace and lamps emit |
| 11 | garden | park, sunny afternoon | wild-ext | ext-day | Grass floor with painted lines |
| 12 | factory2 | heavy plant, dusk | ind-int | int-ind | As factory; weld screens emit |
| 13 | island | tropical island | wild-ext | ext-day | Own surf and sea meshes on `Z.mat`; sand class |
| 14 | mall **P** | two-storey glazed mall | civic-int | int-lit | Bright interior that must still have range; 24 shop signs emit; two storeys test the light volume slices |
| 15 | police | special-forces base | ind-int | int-ind | Weapon racks (armory); ceiling lights every 4 m |
| 16 | grove | redwood forest | wild-ext | ext-day | Terrain; existing additive light shafts; fog near 24 m |
| 17 | spire | supertall towers, sky-bridges | civic-int | int-lit | City below, fog far 900 with tierScale, camera far 1500 |
| 18 | foundry | 30 m war-foundry halls | ind-int | int-ind | Very tall: the light volume needs all 6 slices; embers |
| 19 | parking | underground car park | ind-int | int-ind | Own strip-light overlays that flicker; wet floor candidate |
| 20 | hotel | grand hotel tower | civic-int | int-lit | City below; chandeliers emit warm |
| 21 | techhq | glass tech HQ | civic-int | int-lit | City below; lots of glass (class 11 matters) |
| 22 | cargoship | container ship at sea | mil-ext | ext-day | Zone 1 open deck, zones 2 and 3 holds with their own floor colours; own ocean |
| 23 | datacenter **P** | data center + R&D | ind-int | int-ind | The Titanfall interior case: dark, 75 glow companions, blinking racks, holograms |
| 24 | downtown **P** | commercial blocks, midday | urban-ext | ext-day | The CoD street case; loads `kit-parking` too; level-load is slow under the CPU renderer |
| 25 | highrise | HQ atop a skyscraper + rooftops | civic-int | int-lit | Rooftop zone outdoors at height; city below |
| 26 | gemmine | coal seam into gem cavern | dark-int | int-dark | 53 glow keys: crystals are the lights; cap screen/gem emit weights so the cavern is not flat |
| 27 | megastore | warehouse store | ind-int | int-lit | 10 m roof, skylights; loads `kit-parking` |
| 28 | townhomes | gated community, midday | urban-ext | ext-day | Painted house variants (`paint` remaps cells: classes follow the cell, fine) |
| 29 | arctic | polar station under ice | dark-int | int-dark | Mixed; terrain; own blowing snow; ice and snow classes |
| 30 | resort | tropical resort | wild-ext | ext-day | Terrain, palms, sea; torches |
| 31 | scrapyard | war-machine scrapyard, night | mil-ext | ext-night | Sun vector is the moon: low `sunI`, cool colour; own moon and stars (`sky.sunDisc: false`); readability gate |
| 32 | seabase | seabed research station | dark-int | int-dark | Own water, marine snow, beacons; caustics; teal and amber accents |
| 33 | stronghold **P** | mountain stronghold, sunset | mil-ext | ext-dusk | The military case. Zone 1 outdoors at sunset, zone 2 carved halls (sky visibility 0 under the rock roof). Own sun discs and sunset band (`sky.sunDisc: false`); waterfall haze shader; fog far 1500 |
| 34 | airport | terminal + apron | civic-int | int-lit | Mixed; 33 glow keys; fog far 260 without tierScale |
| 35 | frontier | log stockade, forest ridge | wild-ext | ext-day | Terrain; instanced forest backdrop; own mountain ring |
| 36 | academy | public school, bright day | civic-int | int-lit | Mixed zones without ceiling |
| 37 | mossgarden | walled estate garden | wild-ext | ext-day | Terrain, own stream shader and cobble material |
| 38 | pelagic | offshore air platform | mil-ext | ext-day | Fog far 720; steel deck: painted-metal and tread classes |
| 39 | icecream | ice cream shop + creamery | civic-int | int-lit | Keep it cheerful: this family's brightest preset |
| 40 | venetian | canal mansion, late afternoon | urban-ext | ext-day | Warm `sunColor`; canal water; fog far 280 without tierScale |
| 41 | metro **P** | deep-level metro station | dark-int | int-dark | The lamp-lit interior case; sunk trackbed; glass companions |
| 42 | toyfactory | bright toy factory | ind-int | int-lit | 44 glow keys (window walls); keep it lighter than the other factories |
| 43 | airfield7 | steppe air base, hazy | mil-ext | ext-day | Borrows `kit-stronghold` and `kit-parking`; runway lights emit |
| 44 | riviera | cliff-top grand hotel | civic-int | int-lit | Mixed; warm sun; sea |
| 45 | observatory | mountaintop, late dusk | mil-ext | ext-dusk | Own dusk dome and stars; terrain zone 1, interior zone 2 |
| n/a | toytown | pastel toy town (not in campaign) | urban-ext | ext-day | Test plans only; default family preset, no tuning |

Batches after the pilots: (1) the rest of `mil-ext`; (2) `urban-ext`; (3) `wild-ext`; (4) `ind-int`;
(5) `dark-int`; (6) `civic-int`; (7) `giant-room`.

---

## 9. Traps

T1. **The ink shell casts shadows on its own object.** The shell is an inverted copy 2 cm outside the
    surface. In the shadow pass (back faces) it renders and shadows everything it encloses. Use the
    hull-less depth material of Stage 3 on every caster. Proven in the prototype.

T2. **Never enable renderer tone mapping or output encoding.** In r128's built-in shaders the order is tone
    mapping, encoding, fog. Eight of the game's patches inject at `#include <fog_fragment>` (ink colour,
    flashes, the Undercover look, robot tints, corpse fade, projectile ink, gun glow), so they would run
    after tone mapping and come out wrong. All tone and grade work happens in `IB.Post` (or at the very end
    of the material on low tiers).

T3. **`vViewPosition` is declared after `<common>`** in the toon fragment shader
    (`lights_toon_pars_fragment`). Functions that use it (the bump helper) must be inserted after
    `#include <shadowmap_pars_fragment>`, not at `<common>`. The first prototype run failed on exactly this.

T4. **Patch chains depend on exact strings.** `gunskins.js`, `ai.js`, `trooperrig.js`, `projectiles.js` do
    `string.replace` on anchors that earlier patches create (`'vHull = 0.0;'`,
    `'if ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );'`, `'attribute vec2 aFx;\nvarying vec2 vFx;'`, the
    `outgoingLight` line, `#include <map_fragment>`). A `replace` that finds nothing fails silently. After
    every material change, assert in a dev check that each expected marker is present in the compiled
    fragment source (`renderer.info.programs[i].cacheKey` and `material.onBeforeCompile` output), and that
    `gunskins.js`'s own replacement of the `outgoingLight` line still wins on gun materials (those are
    `look: 'none'`).

T5. **Vertex colour is multiplied into the diffuse colour before you see it** (`color_fragment`:
    `diffuseColor.rgb *= vColor`). On kit meshes vertex colour is occlusion; on code-built floors it is the
    real colour. Recover albedo as in section 5.4. After Stage 5D, G and B differ from R: use `vColor.rrr`
    for the legacy multiply on mapped materials or the classic look tints.

T6. **Inventory pictures share the main renderer** (`ui/thumbs.js:76-90`): they bind their own target and
    restore the previous one. Never assume the current target is null inside `IB.Post`; set it explicitly at
    the start of each pass. With the shadow map enabled their scene's light has no shadow: fine. Check
    `gear-shots.js` after Stages 1, 3 and 8.

T7. **The fog wall hides zone loading.** Only three zones are drawn; the linear fog's far distance (120 m on
    High, less on lower tiers; `R.applyFogFar`) is what stops you seeing the void. The new fog must reach
    full density at `fogFar` exactly as before.

T8. **Three shaders do their own haze** to match the scene fog: `stronghold.js:357` (and its tick at 500
    copies `scene.fog` each frame), `mossgarden.js:388`, `zones.js:1769`. If the fog function changes and
    they do not, distant water and the city below stop matching the horizon.

T9. **Undercover** multiplies and replaces colours after fog (`CLOAK_WORLD`), writes `R.cloak` every frame
    (`skillhud.js:62`), sets `robotOutline.uInk` (63), and puts a CSS filter on the canvas (12). It must look
    as it does today: test it after every shader stage.

T10. **`renderer.info` is reset by hand** once a frame (`game.js:39, 1149`). Extra passes add to the draw
    call counts that `perf.spec.js` and the `__TEST__.state()` hook report. Restate budgets deliberately; do
    not hide passes from the count.

T11. **Render target memory explodes with pixel ratio.** High uses a pixel ratio up to 2. A 2880 x 1800
    multisampled half-float target with depth is over 240 MB. Cap the internal size (section 6) and verify
    framebuffer completeness yourself; three r128 will not tell you a target failed.

T12. **Mixed themes are indoors and outdoors at once** (17 themes have a sky and a ceiling; zone plans can
    switch the ceiling off per zone). One "indoor" flag per theme is wrong. Use the sky-visibility channel of
    the light volume everywhere (Stage 4).

T13. **Instanced meshes** (moving lines `zones.js:835`, racks, clouds, debris) need
    `instanceMatrix` in the world-position computation, and their own depth material variant for shadows.

T14. **Shadow acne and light leaks** come from the big flat code-built quads (floors are single-sided). Tune
    `normalBias` on the pilots at three distances. If floors still acne, do not let floors cast
    (`castShadow = false` on `zone.ground`); they have nothing below them to shadow.

T15. **Light bleeds through 1 m walls** when a 1 m light map is sampled exactly on the wall surface. Sample at
    the surface point pushed 0.35 m along its normal, and fill solid cells from open neighbours.

T16. **Emitter weights decide the mood.** Screens and LEDs cover large areas in some kits (datacenter racks,
    toyfactory window walls, gemmine crystals). Unweighted they flood the room. Class weights in Stage 4.1
    and per-theme `grid.emit` overrides exist for this.

T17. **Blinking lights are animated by theme ticks** on the glow companion meshes (colour and visibility).
    The baked volume is static. That is acceptable (the emissive surface still blinks and blooms); do not
    try to rebake per frame.

T18. **`sampler2DArray` needs its own precision line** (`precision highp sampler2DArray;`) in the fragment
    shader or the program does not compile on WebGL2.

T19. **`surfaces.gen.js` must be regenerated when a palette changes.** Add the check to `surfaces.test.js`
    (names equal to `palettes.gen.json`) and regenerate both whenever a `fam_*.py` palette is edited
    (Stage 11 will do that).

T20. **A kit rebuild is not byte-reproducible** (Cycles noise), so `git status` shows every GLB changed after
    a full rebuild. That is expected; the accessor comparison of 5D.3 is the real check.

T21. **The 8-bit fallback has no values above 1.0.** Bloom and the emissive boost behave differently there.
    Test the fallback chain on purpose (Stage 13.4), do not discover it on a phone.

T22. **Decals on moving or special surfaces**: conveyor belts, elevator floors, water, glass, shutters.
    Exclude by symbol and by piece list, and re-run `zcheck`.

T23. **`G.disposeLevel`** (`game.js:112`) disposes only `MeshBasicMaterial` and `ShaderMaterial` instances
    and non-shared geometries of the level. New per-level resources (light volume texture, decal mesh,
    dust) must be released in `IB.Look.end()`; shared look materials must not be disposed.

T24. **Theme unit tests assert env values** (sky colours, ceilings, zone counts). Do not edit
    `src/data/themes/*.js` for the look; `looks.js` holds everything.

T25. **Test machine limits.** One headless browser at a time. Under load, smoke checks that wait on game
    time fail spuriously. Long screenshot timeouts. The `downtown` level load can exceed 30 s.

T26. **Never carry data in an image's alpha channel through a 2D canvas.** `drawImage` + `getImageData`
    premultiplies and un-premultiplies alpha, which destroys the colour channels wherever alpha is low. All
    data textures that are decoded in the page are opaque RGB images (Stage 5B.2).

T27. **The ink shell has a baked minimum thickness** (2 cm on kits, 3.5 mm on weapons). The outline
    uniforms cannot make a line thinner than that until the clamp in `VERT_PROJECT` is changed (Stage 2.7).

T28. **A changed `THREE.ShaderChunk` does not invalidate compiled programs** in r128 (the program cache key
    of a built-in material is its type and parameters, not the chunk text). Install chunk overrides before
    the first material compiles and never change them afterwards.

---

## 10. Test and review toolkit

| Tool | Use |
|---|---|
| `node --test Source/tests/unit/*.test.js` | Must stay green (478 today + the new look and surface tests) |
| `node Source/tests/e2e/hud-lock.spec.js` | After every stage. File lock + HUD pixel lock + enemy bar lock |
| `LOOK=classic node Source/tests/e2e/look-shots.js <dir> <plans>` then `LOOK=on ...` | Shots for sheets |
| `python3 Source/tests/e2e/look-sheet.py <classicDir> <onDir> <out.jpg>` | Before/after sheets |
| `python3 Source/tests/e2e/look-metrics.py <dir>` | Section 4.2 ranges; non-zero exit when out of range |
| `node Source/tests/e2e/look-tour.spec.js` | All tuned themes: metrics, errors, budgets, z-fight |
| `node Source/tests/e2e/map-shots.js <plan> <shots.json>` | Existing: prints the cross-piece z-fight list (`?zcheck=1`) |
| `node Source/tests/e2e/perf.spec.js` | Draw calls, triangles, VFX stress (frame times are meaningless on the CPU renderer) |
| `node Source/tests/e2e/collision-audit.spec.js`, `bounds.spec.js`, `<theme>-walk/climb.spec.js` | Nothing solid changed |
| `node Source/tests/e2e/gear-shots.js`, `screens.spec.js`, `vfx-shots.js`, `troops.spec.js`, `latebots.spec.js` | Inventory pictures, menus, effects, robots |
| `node Source/tests/e2e/smoke.spec.js` | Whole-game check; compare with the Stage 0.7 list |
| `Source/docs/tactical-look/prototype/probe.js` | Pattern for proving a renderer capability before depending on it |
| `Source/docs/tactical-look/prototype/stats.js` | Draw calls, triangles, meshes, programs per plan |
| URL switches | `?look=classic`, `?post=0`, `?tier=` (if absent use `__TEST__.setTier`), `?lookstats=1`, `?plan=<id>`, `?autotest=1`, `?zcheck=1` |

Review habit for every visual step: classic and on, same spots, one sheet, look at the sheet, then the
metrics table. A step is not done because it compiled.

---

## 11. Decisions taken by default, and questions for the owner

This plan proceeds on the defaults. The owner can change any of them at a checkpoint.

| # | Question | Default taken |
|---|---|---|
| 1 | How dark may dark interiors get? | As the metro prototype but about 15% brighter, with the readability gate |
| 2 | How much comic stays? | Thin ink, comic words and cards, ink damage numbers, hurt halftone all stay; outlined puff clouds and the flat banded sky go |
| 3 | Whimsical maps (bedroom, classroom, living room, toy factory, ice cream) | Same light and material treatment, brighter and warmer presets; content unchanged |
| 4 | Effects pass (Stage 12) | Planned, but confirmed with the owner at Checkpoint 2 before starting |
| 5 | Audio | Out of scope. Worth a separate pass later: gun sound and reverb do a lot for "tactical" |
| 6 | Scanned textures from ambientCG or Poly Haven | Not used; everything is generated here. Possible later if the owner allows those hosts in the environment's network settings |
| 7 | Phones | Still supported through the lower tiers; art direction identical |
| 8 | A player-facing "Classic look" option in Settings | Not added (menus are left alone). The URL switch stays for testing |
| 9 | How far Stage 11 goes | Tier A (7 pilot kits) for sure; Tiers B and C decided at Checkpoint 3 |

---

## 12. What "done" means

- All 45 campaign maps tuned, each with a committed before/after sheet and metrics inside its range.
- HUD lock green; unit tests green; e2e failures limited to the Stage 0.7 list; z-fight lists empty.
- Budgets of section 6 met; fallback chain and four tiers verified.
- The owner has played one map of each look family at 60 frames a second on High on their machine and agreed
  the look at Checkpoints 1, 2 and 3.
- `PROGRESS.md` records every stage's measured numbers and every decision; the README explains the system.
- The artifact is republished and the branch is pushed.
