# INKBOLT round 1 report (milestone M1: playable greybox)

## 1. What changed this round
- **Project and build.** The Source layout follows brief §4.8, with three.js r128 and the Archivo variable font vendored. `tools/build.py` writes the single-file offline `Play Inkbolt.html` (966 KB), a plain upload build, and a dev page.
- **Data tables, complete for the whole game.** All 17 weapons, 8 robots, 4 bosses, 19 upgrade cards, the unlock table, levels 1–20 with theme palettes, and 18 theme kits, with every number taken from the brief.
- **Pure logic, unit tested:**
  - damage formula, falloff, splash, shields, boss shells and melee
  - gem drops and bonuses
  - upgrade costs, draws and effects
  - 3-slot saves with `.bak` fallback and migration
  - the seeded level generator for levels 21+, with validation
- **Renderer:**
  - 3-band toon shading, with the darkest band tinted toward Shadow Tint
  - inverted-hull ink outlines baked into the same mesh and material, so each part is one draw call. The hull width scales with depth, so lines stay about 3 px at any distance.
  - a sky dome with a cream horizon, outlined puff clouds, rolling-hill backdrop and theme fog
  - the viewmodel in its own scene, drawn after `clearDepth`
- **Toy Town greybox level, 2 zones** from ASCII maps:
  - shop-front walls with windows and parapets
  - the water tower on purple lattice legs
  - crates, containers, low walls, billboards and spawn trash cans
  - painted lot lines
- **Level flow:**
  - the gate behind you shuts on zone entry (0.6 s), and wave 1 spawns 1.0 s later
  - further waves come at 2 or fewer robots alive, or after 25 s
  - on clear: a 0.4 s pause, gems vacuum to the player, the hazard-striped gate rolls up (1.2 s), and Pop Teal trail arrows light in sequence
  - the exit hatch ends the level
- **Player** uses the §5.1 movement values:
  - walk, sprint with stamina, jump, coyote time and jump buffer
  - capsule-vs-box collision with 0.35 m step-up
  - landing dip and head bob
- **Weapons:**
  - Pip and Buzz use their table values: spread with first-shot accuracy and moving/airborne penalties, recoil that climbs over 6 shots and recovers at 12°/s, aim zoom, reload, and draw/holster timing
  - the code is table-driven, so the other hitscan guns only need a viewmodel
  - viewmodel: chunky gunmetal gun with an amber stripe, gloved hands, a spring kick (stiffness 220, damping 18), sway and a comic muzzle star
  - F gives a 20-damage shove with 35 ms hit-stop
- **Crawler robot** (tin can on 4 spring legs, a single sensor slot, an amber antenna light, a gold core dome as the weak point; no eyes):
  - built from instanced rigid parts
  - full AI states: spawn, idle/patrol, alert, chase with zigzag and flow field, windup with two white flashes, lunge attack, recover, stagger, blinded
  - attack tokens and soft separation between robots
  - deaths: the robot pops up as an ink-black silhouette, tips over, then fades and sinks, while ink chunks scatter
- **Effects:**
  - bullet holes on every hit, ink splats on 1 shot in 3 (256-decal ring buffer)
  - ink puffs, tracers, blob shadows
  - gems pop, bounce, and pull toward the player within the magnet radius
- **Audio:** every sound is synthesised at load (no music): layered gunshots, reload clacks, hit and core ticks, can-crunch deaths, gate roll and latch, and gem ticks that rise in pitch. A compressor sits on the master bus, with 24-voice stealing, stereo pan and distance falloff.
- **Death and retries:** the view tips into a grey ink tint and the Eliminated card counts down 3 s. You respawn at the zone entry with 2 s of protection, and the zone resets. After 3 retries, the Fail screen appears.
- **UI:**
  - ink machined plates with chamfers, a 3 px outline and a flat under-plate; Archivo only; Pop Teal as the single accent
  - the full HUD from §2.4: scoreboard, zone pips, kill feed, gems, health, ammo, slots, a crosshair whose gap follows spread, hit markers and damage arcs
  - screens: title (3D scene with the robot line-up), Settings (every switch and slider, plus a confirm step on reset), Pause (Resume first), Results, Fail, level intro, rotate hint
  - keyboard focus rings
- **Controls:**
  - desktop: pointer lock, with drag-to-look if the lock is refused
  - touch: floating left stick (sprint by pushing far), right-side look drag, Fire / Aim / Reload / Swap / Jump buttons, a pause button, and light aim assist
- **Platform and saves:** `Plat` hooks are called at the right points (plain build, so ads are off). The game auto-saves at level start and level clear, and the performance guard steps between quality tiers.
- **Test hooks:** `window.__TEST__` provides `state`, `killZone`, `teleport`, `damagePlayer` and more.

## 2. Test results
- **Unit tests:** `npm test` passes **53 / 53** (damage, unlocks, gems, upgrades, saves, data tables, and the level generator across 500 seeds).
- **Smoke test** (`tests/e2e/smoke.spec.js`, headless Chromium over http, run on `Play Inkbolt.html`): **33 / 33 pass**.
  - In both zones, robots drop in, the zone clears, the gate opens and the trail lights.
  - Zone 2 starts on entry and its entry gate shuts.
  - The gem vacuum works, the hatch ends the level, results show, the save is written, and Plat hooks fire in order.
  - Death, respawn and the Fail screen all work.
  - With real input: WASD movement, jump, mouse look, weapon switch, zone 1 cleared with real mouse clicks, decals placed, Esc pauses with Resume first.
  - With touch: the stick moves, a drag turns the view, and the Fire button shoots.
  - There were no console errors or warnings.
- **Screenshot check** (`tests/e2e/screens.spec.js`): **136 / 136 automatic checks pass**.
  - Screens: title, HUD, Eliminated, pause, settings, reset confirm, results (with a 7-digit gem total), and fail.
  - Viewports: 390×844, 844×390 and 1920×1080, with each phone screen also rotated while open.
  - Checks: no horizontal overflow, every button inside the viewport, tap targets of at least 48 px (44 px for switches and sliders).
  - Images are in `Source/tests/e2e/screens/`. I reviewed them by eye and fixed these problems:
    - the viewmodel was too large
    - the portrait title camera sat behind a wall and the tagline box stretched
    - the portrait HUD plates overlapped
    - the sideways weapon slots covered the Reload button
    - the scoreboard text wrapped
    - secondary panel buttons were invisible
    - a mouse-load focus ring was showing
- **Not built yet, so not tested:** Trail Map, Garage, Upgrade Bench and the boss screens (M2–M5 scope).

## 3. Performance (headless Chromium, SwiftShader software GL)
| Viewport | Draw calls (max) | Triangles (combat max) | 40 robots: calls / tris | Frame p50 / p95 (ms, CPU renderer) | JS heap |
|---|---|---|---|---|---|
| Phone upright 390×844 | 33 | 45,645 | 32 / 80,524 | 66.6 / 133.4 | 13.6 MB |
| Phone sideways 844×390 | 35 | 45,709 | 33 / 80,572 | 66.7 / 150.1 | 13.6 MB |
| Desktop 1920×1080 | 31 | 39,189 | 30 / 78,012 | 233.4 / 449.9 | 9.5 MB |

Draw calls are far under the budget (120 on phones, 200 on desktop). Instanced meshes now draw only up to their highest live slot. **The frame times are from a CPU software renderer and don't predict real GPU speed;** a real-device check is still needed.

File sizes: `Play Inkbolt.html` 966 KB; the upload build is 377 KB `index.html` plus 603 KB `three.min.js`. There are no GLBs yet; this round is greybox.

## 4. Not tested, and why
- Real phones and real GPUs: the sandbox only has headless Chromium with software GL.
- Real CrazyGames and Poki SDKs: this round ships the plain build only, and the SDK zips are M6.
- How the audio actually sounds: the buffers are generated and played without errors, but nobody has listened in a browser.
- The Blender pipeline: `pip install bpy` was not attempted beyond a probe. M1 is greybox, so it wasn't needed.

## 5. Known issues (most severe first)
1. No Blender assets yet. All models are built in code (greybox per M1), and the GLB loader path is not wired.
2. Only the Crawler and two weapons are playable. The other robots and weapons exist as data only.
3. Results → Continue returns to the title, because the Upgrade Bench is M2.
4. The theme kit is Toy Town only. Gates and trail walls use theme colours, but walls and props are built for Toy Town.
5. The directional shadow map (High preset) is not built; only blob shadows exist.
6. Gems rest on the ground plane, not on top of crates.
7. The zone maps add `E` (entry gate cell) to the brief's ASCII symbols.

## 6. Who did which job
- **Lead (one coding model):** architecture, renderer, outlines, zones, player, weapons, AI, effects, audio, input, UI and menus, game flow, build, e2e tests, and the screenshot review and fixes.
- **One delegated helper (same model):** the data tables, pure core logic, and unit tests (`src/data/*` except `levelplans.js`, `src/core/*`, `tests/unit/*`).

## 7. Proposed next round (M2: combat complete)
- Every remaining gun with a viewmodel, plus the Frag Can and Pop Flash (cooking, bounce, the blind overlay with the Reduce flash setting), the Katana and Fire Axe (combo, block/parry, charge), the Needle scope, and Can Cannon splash with rocket jumps.
- The 7 other robot types, with projectiles, the ink puddle, shields, the Bruiser charge, and Bin Hive spawning.
- The Upgrade Bench with all 19 cards, wired to the saved slot.
- The debug "armoury" level.
- A first pass of the Blender `bpy` pipeline: weapons, arms and bots as quantized GLBs, replacing the code-built meshes.
- The comic-word atlas for explosions.
