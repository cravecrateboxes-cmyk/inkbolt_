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
           Space jump, Shift sprint, R reload, 1-3 or mouse wheel switch carried guns, F shove, Esc pause.
           Tab opens the field kit (pauses): Loadout, Gear, Skills. Q / E switch tabs, arrows move, Enter
           selects (Enter again spends a skill point), Tab or Esc resumes.
  Phone:   left thumb moves (push far forward to sprint), right thumb looks, Fire / Aim / Reload /
           Swap / Jump buttons on the right, pause button top right, field kit (grid) button next to it.

PROGRESSION
  Player level: +1 for every campaign level cleared (LV 20 cap), shown above the health bar with a rank title.
  Skill points: from clearing levels 1-17 only (22 in total, see src/data/skills.js); the tree holds 43, so pick.
  Respec: resets the tree for gems (40% of a level's expected income at your progress).
  Loadout: carry 2 guns from your arsenal (3 after clearing level 10); weapon stands add guns to the arsenal.
  Robots get a little tougher every level (health, damage, fire rate, aim, speed; src/core/damage.js).

LOOT AND GEAR
  About one robot in twenty drops an item: a drop pod with a beam in its rarity colour (Common / Rare / Epic),
  also marked on the radar as a diamond. Walk over it to bag it; an empty slot is filled right away.
  Shield cells (after level 3 is cleared) soak damage before health and recharge after a short delay.
  Gun attachments: Grip (less recoil and spread), Scope (zoom and a tighter aim; aim to look through it),
  Acid muzzle (silenced; part of each hit burns on as acid). The Gear tab of the in-game menu (IB.GearUI)
  equips, fits, moves and scraps them. Tables: src/data/loot.js; logic: src/core/loot.js; models: blender/fam_gear.py.

EXPLOSIONS AND HAZARDS (src/game/boom.js)
  Robots blow up as comic explosions (toon fireballs, ink smoke, flying parts, a word like KRAK! or KA-BOOM!);
  Drones drop out of the air and blow up where they land. Effects grow with the campaign level (IB.Boom.intensity:
  1.0 on level 1, +0.15 a level, 2.2 from level 9): bigger blasts, more debris and words, chains of scrap pops.
  Explosive canisters (red, from level 3: 1 per zone, up to 4) go off after a couple of shots, robot bolts or being caught
  in a blast; a red ring on the floor shows the blast reach during the fuse. They hurt robots and the player alike.
  Screen shake and Reduce flash (settings) are respected; counts scale with the graphics tier.

BUILD AND TEST (from the Source folder)
  python3 tools/build.py
  npm test                                  (unit tests)
  node tests/e2e/smoke.spec.js              (plays level 1 headless: zones, gates, trail, hatch, death, input, touch)
  node tests/e2e/screens.spec.js            (screenshots in tests/e2e/screens/, layout checks)
  node tests/e2e/perf.spec.js               (draw calls, triangles, frame times, VFX stress)
  node tests/e2e/vfx-shots.js               (frame-stepped explosion screenshots -> tests/e2e/review/vfx-*.png)
  Dev page: serve the repo folder over http and open Source/dev.html  (add ?autotest=1 to skip the title).
