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

CONTROLS
  Desktop: click to lock the mouse. WASD move, mouse look, left click fire, right click aim,
           Space jump, Shift sprint, R reload, 1/2 or mouse wheel switch weapon, F shove, Esc pause.
  Phone:   left thumb moves (push far forward to sprint), right thumb looks, Fire / Aim / Reload /
           Swap / Jump buttons on the right, pause button top right.

BUILD AND TEST (from the Source folder)
  python3 tools/build.py
  npm test                                  (unit tests)
  node tests/e2e/smoke.spec.js              (plays level 1 headless: zones, gates, trail, hatch, death, input, touch)
  node tests/e2e/screens.spec.js            (screenshots in tests/e2e/screens/, layout checks)
  node tests/e2e/perf.spec.js               (draw calls, triangles, frame times)
  Dev page: serve the repo folder over http and open Source/dev.html  (add ?autotest=1 to skip the title).
