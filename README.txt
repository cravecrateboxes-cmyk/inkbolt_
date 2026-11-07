INKBOLT - comic-style browser FPS (round 1: M1 playable greybox)

WHAT IS HERE
  Play Inkbolt.html   The whole game in one file. Open it in a desktop or phone browser; it runs offline.
                      Round 1 content: one Toy Town level, 2 zones, Crawler robots, Pip pistol and Buzz SMG.
  Source/             Everything the game is built from:
    src/data/         Tables: weapons, robots, bosses, upgrades, unlocks, levels 1-20, zone maps (ASCII .txt).
    src/core/         Pure logic (no browser needed): damage, gems, upgrades, saves, level generator, RNG.
    src/game/         Runtime: renderer + ink outlines, zones/gates/trail, player, weapons, robots/AI, effects, audio, input, platform hooks.
    src/ui/           HUD, menus, stylesheet.
    vendor/           three.js r128, Archivo font (OFL licence), BufferGeometryUtils and GLTFLoader (for the Blender GLBs next round).
    tools/build.py    Builds Play Inkbolt.html, Source/dev.html and Source/dist/upload/.
    tests/unit/       node:test unit tests for src/core and src/data.
    tests/e2e/        Headless Chromium tests: smoke (plays the level), screens (screenshot matrix), perf.
  ROUND-1-REPORT.md   What was built and tested this round, numbers, known issues, next round.

LEVELS 9-11 (round 2 additions)
  9  Galleria Mall      two-storey atrium: mezzanine ring at 4.5 m, escalators, an automatic glass elevator.
  10 Strike Team HQ     police / special-forces base: weapon wall racks hold real guns with a rolled rarity
                        (grey, green, blue common; purple very rare; orange never), workbenches hold mods
                        (extended / speed mag, suppressor, compensator, long barrel, red dot, laser, grip),
                        shelves hold gear (Kevlar vest, med kit, ammo box). Look at one and press E (touch: USE).
  11 Redwood Hollow     bumpy garden valleys; giant redwoods with broken branch stairs up to 9 m limbs and rope
                        bridges between trees. Robots climb the stairs and branches after you.
  Kits: Source/blender/fam_kit_mall.py, fam_kit_police.py, fam_kit_grove.py (pip install bpy; python3 build_assets.py).
  Maps: Source/tools/mall_zones.py, police_zones.py, grove_zones.py write src/data/zones/*.txt.

CONTROLS
  Desktop: click to lock the mouse. WASD move, mouse look, left click fire, right click aim,
           Space jump, Shift sprint, R reload, 1/2 or mouse wheel switch weapon, F shove, E use / take, Esc pause.
  Phone:   left thumb moves (push far forward to sprint), right thumb looks, Fire / Aim / Reload /
           Swap / Jump buttons on the right, pause button top right.

BUILD AND TEST (from the Source folder)
  python3 tools/build.py
  npm test                                  (unit tests)
  node tests/e2e/smoke.spec.js              (plays level 1 headless: zones, gates, trail, hatch, death, input, touch)
  node tests/e2e/screens.spec.js            (screenshots in tests/e2e/screens/, layout checks)
  node tests/e2e/perf.spec.js               (draw calls, triangles, frame times)
  Dev page: serve the repo folder over http and open Source/dev.html  (add ?autotest=1 to skip the title).
