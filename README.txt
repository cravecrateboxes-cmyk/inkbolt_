INKBOLT - comic-style browser FPS (round 1: M1 playable greybox)

WHAT IS HERE
  Play Inkbolt.html   The whole game in one file. Open it in a desktop or phone browser; it runs offline.
                      Round 1 content: one Toy Town level, 2 zones, Crawler robots, Pip pistol and Buzz SMG.
  Source/             Everything the game is built from:
    src/data/         Tables: weapons, robots, bosses, upgrades, unlocks, levels 1-20, zone maps (ASCII .txt).
    src/core/         Pure logic (no browser needed): damage, gems, upgrades, saves, level generator, RNG.
    src/game/         Runtime: renderer + ink outlines, zones/gates/trail, player, weapons, robots/AI, effects, audio, input, platform hooks.
    src/ui/           HUD (hud.js + hud.css), menus, between-levels loader (loader.js + loader.css), field kit
                      (Inventory / Skills / Character), stylesheet ("holo ink" look, ui.css).
    vendor/           three.js r128, Archivo and Barlow Condensed fonts (OFL licences), BufferGeometryUtils and GLTFLoader.
    tools/build.py    Builds Play Inkbolt.html, Source/dev.html and Source/dist/upload/.
    tests/unit/       node:test unit tests for src/core and src/data.
    tests/e2e/        Headless Chromium tests: smoke (plays the level), screens (screenshot matrix), perf.
  ROUND-1-REPORT.md   What was built and tested this round, numbers, known issues, next round.

CONTROLS
  Desktop: click to lock the mouse. WASD move, mouse look, left click fire, right click aim,
           Space jump, Shift sprint, R reload, 1-3 or mouse wheel switch carried guns, V shove,
           F Undercover (skill: 5 s invisible, 30 s cooldown; badge above the bottom edge), Esc pause.
           Tab opens the field kit (pauses): Inventory, Skills, Character. Q / E (or the yellow chevrons) switch
           tabs, arrows move, Enter selects (Enter again spends a skill point; in the inventory Enter equips),
           pointing at an item shows its card, Tab or Esc resumes.
  Phone:   left thumb moves (push far forward to sprint), right thumb looks, Fire / Aim / Reload /
           Swap / Jump buttons on the right (plus an eye button for Undercover once learned, its ring is the cooldown),
           pause button top right, field kit (grid) button next to it.

PROGRESSION
  Player level: +1 for every campaign level cleared (LV 20 cap), shown above the health bar with a rank title.
  Skill points: from clearing levels 1-17 only (22 in total, see src/data/skills.js); the tree holds 43, so pick.
  Skill tree: six rows, trunk at the bottom (gates 2 / 5 / 8 / 11 / 14 points in the rows below), two pick-one endgame
  skills on top. Runtime: src/game/skillfx.js (procs, acid pools, wet coats, Undercover), ai.js (cloak search, rogue
  robots), ui/skillhud.js (Undercover badge + comic black-and-white look). Saves with the old tree are refunded on load.
  Damage over time lasts: Electrify 5 s, Hazard / Hydrate burns 5 s, acid muzzles 5 / 6 / 7 s by rarity.
  Respec: resets the tree for gems (40% of a level's expected income at your progress).
  Loadout: carry 2 guns from your arsenal (3 after clearing level 10); weapon stands add guns to the arsenal.
  Robots get a little tougher every level (health, damage, fire rate, aim, speed; src/core/damage.js).

LOOT AND GEAR
  About one robot in twenty drops an item: a drop pod with a beam in its rarity colour (Common / Rare / Epic),
  also marked on the radar as a diamond. Walk over it to bag it; an empty slot is filled right away.
  Shield cells (after level 3 is cleared) soak damage before health and recharge after a short delay.
  Gun attachments: Grip (less recoil and spread), Scope (zoom and a tighter aim; aim to look through it),
  Acid muzzle (silenced; part of each hit burns on as acid). The Inventory tab of the field kit (IB.GearUI, ui/gear.js)
  shows the item card (stats, compare, flavour) + ammo, EQUIPPED (weapon slots 1-3, slot 3 locked until level 10 is
  cleared, the attachment slots of each carried gun, the shield) and the BACKPACK (weapons, attachments, shields);
  it equips, fits, moves and scraps them. Tables: src/data/loot.js; logic: src/core/loot.js; models: blender/fam_gear.py.

HUD (src/ui/hud.js, hud.css)
  Tactical look (Call of Duty / Titanfall 2 vein) over the comic world: translucent glass panels with cut corners in the
  corners of the screen, hairline accents, Barlow Condensed tabular numerals. Top-left objective + gems, top-centre zone /
  timer / robots-left strip, top-right radar + kill feed, bottom-left level tag + shield + segmented health bar (a red
  chip trails the damage you just took) + stamina, bottom-right carried guns + weapon name (ink-brush underline) + big
  ammo count with the reserve smaller. Comic touches stay: halftone at the screen edges when hurt or low on health,
  ink-outlined damage numbers. Phones keep the same layout as before (clear of the stick and the button cluster).
  Enemy health bars (src/game/hpbars.js): a slim slanted bar over a robot while it is hurt and within 30 m, under the
  crosshair, or just hit; smooth drain with a delayed chip, a shield row when a robot has one, the type's colour on the
  left tab, more segments for tougher robots. One instanced draw call for all of them (up to 24 at once), depth-tested
  so cover hides them, sized in screen pixels with a legible minimum.
  Loading (src/ui/loader.js): a black screen with a real-3D gear and pinion (own small WebGL canvas, toon-metal shading,
  teal / amber / purple glowing rims and neon edges), the next level's name and a hairline progress bar. It lasts 3.5 s,
  then the level fades in from dark.

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
  node tests/e2e/hud-shots.js               (HUD, enemy health bars and loader at 3 sizes -> tests/e2e/review/hud-*.png, loader-*.png)
  Dev page: serve the repo folder over http and open Source/dev.html  (add ?autotest=1 to skip the title).
