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
    src/ui/           HUD, menus, field kit (Inventory / Skills / Character), stylesheets (ui.css; fieldkit.css: the field kit's
                      comic holo-device look, also used by the menus), item pictures rendered from the models (thumbs.js),
                      hand-inked skill icons (skillicons.js).
    vendor/           three.js r128, Archivo and Ranchers fonts (OFL licences in vendor/fonts), BufferGeometryUtils and GLTFLoader (for the Blender GLBs next round).
    tools/build.py    Builds Play Inkbolt.html, Source/dev.html and Source/dist/upload/.
    tests/unit/       node:test unit tests for src/core and src/data.
    tests/e2e/        Headless Chromium tests: smoke (plays the level), screens (screenshot matrix), perf.
  ROUND-1-REPORT.md   What was built and tested this round, numbers, known issues, next round.

CONTROLS
  Desktop: click to lock the mouse. WASD move, mouse look, left click fire, right click aim,
           Space jump, Shift sprint, R reload, 1-3 or mouse wheel switch carried guns,
           V melee strike with the equipped melee weapon (a shove until you own one; quick presses chain a combo),
           B next melee weapon, G throw a frag can,
           F Undercover (skill: 5 s invisible, 30 s cooldown; badge above the bottom edge), Esc pause.
           Tab opens the field kit (pauses): Inventory, Skills, Character. Q / E (or the yellow chevrons) switch
           tabs, arrows move, Enter selects (Enter again spends a skill point; in the inventory Enter equips),
           pointing at an item shows its card, Tab or Esc resumes.
  Phone:   left thumb moves (push far forward to sprint), right thumb looks, Fire / Aim / Reload /
           Swap / Jump buttons on the right (plus an eye button for Undercover once learned, its ring is the cooldown;
           a blade button (tap: strike, hold: next melee weapon) and a can button once you own them),
           pause button top right, field kit (grid) button next to it.

PROGRESSION
  Player level: +1 for every campaign level cleared (LV 20 cap), shown above the health bar with a rank title.
  Skill points: from clearing levels 1-17 only (22 in total, see src/data/skills.js); the tree holds 43, so pick.
  Skill tree: six rows, trunk at the bottom (gates 2 / 5 / 8 / 11 / 14 points in the rows below), two pick-one endgame
  skills on top. Runtime: src/game/skillfx.js (procs, acid pools, wet coats, Undercover), ai.js (cloak search, rogue
  robots), ui/skillhud.js (Undercover badge + comic black-and-white look). Saves with the old tree are refunded on load.
  Damage over time lasts: Electrify 5 s, Hazard / Hydrate burns 5 s, acid muzzles 5 / 6 / 7 / 8 s by rarity.
  Respec: resets the tree for gems (40% of a level's expected income at your progress).
  Loadout: carry 2 guns from your arsenal (3 after clearing level 10); weapon stands add guns to the arsenal.
  Robots get a little tougher every level (health, damage, fire rate, aim, speed; src/core/damage.js).

CAMPAIGN (src/data/levelplans.js ORDER)
  1 Mountains, 2 Small City, 3 Classroom, 4 Office Tower, 5 Big Bedroom, 6 Coal Mine, 7 Castle, 8 Downtown at Dusk,
  9 Robot Works, 10 Living Room, 11 Wide Garden Playground, 12 Heavy Works, 13 Lagoon Island.
  Wide Garden Playground (garden): a park with big climbable play forts, bridges, a pirate ship; walkable decks
    (Blender boxes named <Piece>_WCOL<n>) give the zone a two-layer nav grid, so robots climb stairs and cross
    bridges after you (zones.js floorAt / layered flow field, ai.js foot heights).
  Heavy Works (factory2): giant walkers and tread bruisers built along moving lines (bare chassis, drivetrain, armour,
    paint), overhead cranes, a test track. Moving lines (theme symbol option `conveyor`, zones.js updateLines,
    one instanced mesh per moving symbol) run in both factories; standing on a belt carries you.
  Lagoon Island (island): a wide island with wadeable ponds, tide pools and a lagoon, sea walls on the shore and open
    ocean to the horizon all round (theme backdrop.build paints the island ground and the sea).

MELEE, GRENADES AND NEW GUNS
  Melee weapons (V, src/game/weapons.js W.meleeStart + game.js meleeHit): KN-3 Stinger dagger (fast stab, x2.5 on a
  robot that has not seen you or is struck from behind), NC-2 Twin Strikers nunchucks (two hits per swing in a wide arc,
  staggers), Mk-1 Ronin Blade katana (two-handed, 3-cut combo, the third cut x1.6), VX-7 Voltaxe electric axe (two-handed
  heavy chop, shock damage over time, arcs to 2 robots nearby). The gun goes away for the swing and is drawn again.
  Frag cans (G, src/game/throwables.js): carry 3, thrown from the support hand; they bounce, a red ring shows the blast
  reach in the last second, and the blast hurts robots (and you, capped at 35). Ammo boxes give one back.
  Unlocks (src/data/unlocks.js, stands at the start of the level): dagger L3, frag cans + nunchucks L4, katana + Voltaxe
  L5 (every melee weapon and grenades by level 5); SG-9 Scrapper pump shotgun L7 (loads shell by shell), AR-40 Vanguard
  battle rifle L8, SG-12 Thunderclap auto shotgun L9, SR-9 Railspike rail rifle L11 (3x scope, pierces 4 robots).
  A save that already cleared a level gets what stood at its start when the next level loads.
  Models and arm actions: blender/fam_weapons.py (MELEE_SWINGS, THROW_L, pump_fire, shell_reload).

SOLDIERS AND BLADE BOTS (src/game/troops.js, rows in src/data/enemies.js, models in blender/fam_bots.py)
  Soldier (from level 4): an armoured robot trooper. Its shield (the blue row on its health bar, 75% of its health)
  takes damage first and recharges after 3.5 s without a hit. It keeps 7-15 m, strafes and uses cover, fires 4-bolt
  bursts, throws up to 3 frag grenades (they bounce, blink, show a red ring, then blow) and rifle-butts you inside
  2.2 m after a pull-back tell. Six armour colours (white, grey, blue, purple, black, crimson), two torsos, three
  helmets; a visor slit, no face. Kills roll a weapon drop (6% gray, 3% green, 2% blue, 0.8% purple, 0.2% orange).
  Blade Bot (from level 3): a hover saucer with a hub arm holding a katana or a Voltaxe. It patrols slowly; once it
  sees you it homes in, spins up (whine, flashing), dashes with its blade at ~19 rev/s, cuts on contact (the Voltaxe
  also shocks you for 2 s), overshoots and stays dizzy for 1.4 s, taking 35% more damage. Stand next to it and it spin
  slashes in place. Kills have a 7% chance to drop its weapon. Both grow with the level like every robot.

LOOT AND GEAR
  About one robot in twenty drops an item: a drop pod with a beam in its rarity colour, also marked on the radar as a
  diamond. Walk over it to bag it; an empty slot is filled right away. Bag: 40 items (worn and fitted ones included).
  Rarities: Common (white), Rare (blue), Epic (purple), Legendary (orange, only from campaign level 6). Rarer gear
  drops more often the further you get (LOOT.rarityOdds in src/data/loot.js; levels 1-3 roll as they always did):
      level      1-3   4    5    6    7    8    9    10   11   12   13   15   17+
      Common      70   66   62   56   52   48   44   40   36   33   30   27   24
      Rare        24   26   28   29   30   31   32   33   34   34   35   35   35
      Epic         6    8   10   12   14   16   18   20   22   24   25   26   27
      Legendary    0    0    0    3    4    5    6    7    8    9   10   12   14
  Stats roll inside the rarity's range, then grow with the campaign level (LOOT.levelScale): levels 1-3 as before,
  past level 3 shields (capacity, recharge, vest health, Nova damage) grow about as fast as the robots' pressure
  (x1.35 on level 6, x1.71 on 10, x1.98 on 13, cap x2.8) and attachments a little (x1.12 / 1.24 / 1.33, cap x1.5).
  Shield cells (after level 3 is cleared; a common one is handed out then) soak damage before health and recharge
  after a short delay. Each rarity has its own cell model and HUD bar colour: Tin Cell (cyan), Volt Cell (blue,
  twin terminals), Storm Cell (purple, lightning fins), Nova Cell (orange, gold trim and an orb in a halo). Epic and
  Legendary cells carry one perk (a pip on the shield bar): Overcharge (a kill starts the recharge at once and speeds
  it up 40-100% for 4 s) or Nova (when the cell breaks: a shock burst that hits and staggers robots within 4.5 / 6 m,
  once per charge, re-armed when the cell is full again).
  Armour vests (after level 5 is cleared; a common one is handed out then): worn like the shield, they cut the damage
  that gets past the shield (4-17%) and add max health (5-32, grows with the level).
  Gun attachments: Grip (less recoil and spread; SMG, rifle, sniper, shotgun), Scope (zoom and a tighter aim; aim to
  look through it), Acid muzzle (silenced; part of each hit burns on as acid), Extended mag (more rounds, at least +1,
  and a faster reload; pistol, SMG, rifle, sniper, shotgun, not revolvers; it rides the gun's magazine in first person).
  Slots are data: LOOT.slots (per gun: grip, scope, muzzle, mag) and LOOT.worn (player: shield, armor).
  The Inventory tab of the field kit (IB.GearUI, ui/gear.js) shows the item card (rarity title bar, stats, compare,
  the perk, the item's picture) + ammo, EQUIPPED (weapon slots 1-3, slot 3 locked until level 10 is cleared, the
  attachment slots of each carried gun, the shield and the vest) and the BACKPACK (weapons, attachments, shields,
  armour), every item as its real model drawn into a framed picture; it equips, fits, moves and scraps them.
  Tables: src/data/loot.js; logic: src/core/loot.js; runtime: src/game/gear.js (effects, perks, viewmodel parts),
  src/game/drops.js; models: blender/fam_gear.py. Review shots: node tests/e2e/gear-shots.js (tests/e2e/review/gear-*.png).

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
  node tests/e2e/troops.spec.js             (Soldier shield / grenades / melee, Blade Bot dash; SHOTS=1 -> review/troops-*.png)
  node tests/e2e/hud-shots.js              (HUD, enemy health bars and loader at 3 sizes -> tests/e2e/review/hud-*.png, loader-*.png)
  Dev page: serve the repo folder over http and open Source/dev.html  (add ?autotest=1 to skip the title).
