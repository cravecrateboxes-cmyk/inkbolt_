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
           F Undercover (skill: 7.5 s invisible, 23 s cooldown; badge above the bottom edge), Esc pause.
           Tab opens the field kit (pauses): Inventory, Skills, Character. Q / E (or the yellow chevrons) switch
           tabs, arrows move, Enter selects (Enter again spends a skill point; in the inventory Enter equips),
           pointing at an item shows its card, Tab or Esc resumes.
  Phone:   left thumb moves (push far forward to sprint), right thumb looks, Fire / Aim / Reload /
           Swap / Jump buttons on the right (plus an eye button for Undercover once learned, its ring is the cooldown;
           a blade button (tap: strike, hold: next melee weapon) and a can button once you own them),
           pause button top right, field kit (grid) button next to it.

PROGRESSION
  Player level: +1 for every campaign level cleared (LV 20 cap), shown above the health bar with a rank title.
  Level 21+ boost: guns of gun level 21+ hit harder on top of their tier (blue x1.04, purple x1.07, orange x1.15);
    gear of item level 21+ gets its level-scaled stats raised (rare x1.03, epic x1.05, legendary x1.1).
  Health regen: from campaign level 21 the player repairs a % of max health per second after 4 s without damage
    (0.6 % on 21, 1.4 % on 25, 2.9 % on 30, a bigger step every level; IB.Damage.levelRegenPct), on top of bench / skills.
  Skill points: from clearing levels 1-17 only (22 in total, see src/data/skills.js); the tree holds 43, so pick.
  Skill tree: seven rows, trunk at the bottom (gates 2 / 5 / 8 / 11 / 14 points in the rows below, 18 for the endgame row), three pick-one endgame
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
  Galleria Mall (mall): two storeys of shopfronts round a glazed atrium; about a third of the bays (west and east walls,
    both storeys) are walk-in shops with furnished 5 x 6 m rooms (books, coffee, fashion, electronics, toys, jewellery,
    shoes, optics, bakery, homeware, leather goods) that robots follow you into; the others are window-only or
    shuttered. Zone layers: tools/mall_zones.py; rooms: blender/mall_rooms.py; doorways: theme wall.passage.
  Lagoon Island (island): a wide island with wadeable ponds, tide pools and a lagoon, sea walls on the shore and open
    ocean to the horizon all round (theme backdrop.build paints the island ground and the sea).
  Downtown Standoff (downtown): a wide daylight downtown braced for a battle -- Commerce Avenue (a checkpoint and an
    overturned truck across a six-lane avenue), Liberty Square (sandbag nests round the Founders monument) and Market
    Street (a stalled tram among market stalls, a service lane behind); five building styles, cars, taxis, police
    cruisers, a bus, vans, trucks and bikes everywhere, ten walk-in shops with furnished 7 x 8 m rooms and back rooms
    (pharmacy, diner, electronics, convenience store, books, barber, sporting goods, hardware, pawn, laundromat).
    Kit: blender/fam_kit_downtown.py (downtown_*.py); zones: tools/downtown_zones.py. The everyday vehicles are
    kit-parking pieces: theme option `families` loads more kits for a level (zones.js Z.themeFamilies).

  Helix Vault (datacenter): a 74 m wide hyperscale data center (hot / cold aisles of blinking rack rows, CRAC units,
    a NOC with a video wall), the secure core (colocation cages round a quantum computer), a vault, a UPS room, and the
    HELIXA R&D wing (robot chassis on gantries, holo design tables, weapon prototypes in containment fields, cryo
    cylinders, an energy test chamber, the Forge). Glow companions (theme option `glow`, zones.js): LEDs, screens and
    holograms drawn unlit, blinked / turned by the theme.

  BULKBARN Warehouse Club (megastore, 2 zones): the inside of a huge warehouse store under a 10 m steel roof on
    open-web joists (skylights, high-bay lamps, hanging aisle and department boards). Sales Floor (80 m): eight rows of
    5.6 m pallet racks (goods on the shelves, shrink-wrapped pallets above; every rack, endcap and pallet repainted
    per copy from a dozen product colours, theme symbol option `paint`), produce, dairy / drink coolers and walk-ins,
    a TV wall, apparel, the pharmacy / optical counter, freezer bunkers, checkout lanes, cart corrals, the entrance
    vestibule and the BULKBARN CAFE food court. Stockroom (72 m), behind the EMPLOYEES ONLY doors: 8.6 m racks,
    forklifts (kit-parking via `families`), dock doors with trailers backed in, a baler, a stretch wrapper, the break
    room under a mezzanine and the receiving office up on it (steel stair, high ground). Kit: blender/fam_kit_megastore.py
    (ms_*.py); zones: tools/megastore_zones.py.

BREAKABLE DOORS (src/game/doors.js, theme symbol option `breakable`; first used by Helix Vault)
  A prefab symbol with breakable: { hp, debris: 'metal' | 'glass' | 'mesh' | 'field', word, leaf, blend } places its
  frame like any prefab and its leaf (<Piece>_Leaf, _Leaf_D1, _Leaf_D2, _Broken) as its own mesh and collision. The
  leaf blocks movement, shots, sight lines and the nav grid. It takes damage from the player's bullets and melee, robot
  bolts, and every blast in reach (frag cans, rockets, soldier grenades, bombers, canisters; x4 against doors); hp is in
  level-1 units (hits are divided by the robots' health multiplier). Under 2/3 and 1/3 hp it shows dents / cracks and
  sparks, at 0 it bursts (Boom.shatter: debris, dust, a comic word), its boxes switch off and Zones.renav rebuilds the
  zone's nav grid so robots path through. orient: 'span' lines a door up with its wall; doorway cells in 2-cell walls
  are wall.passage cells (several symbols allowed). Loot mounts inside a breakable prefab stay locked until it breaks.
  Doors are whole again on a restart. Test: node tests/e2e/doors.spec.js.

MELEE, GRENADES AND NEW GUNS
  Melee weapons (V, src/game/weapons.js W.meleeStart + game.js meleeHit): Stinger dagger (fast stab, x2.5 on a
  robot that has not seen you or is struck from behind), Twin Strikers nunchucks (two hits per swing in a wide arc,
  staggers), Ronin Blade katana (two-handed, 3-cut combo, the third cut x1.6), Voltaxe electric axe (two-handed
  heavy chop, shock damage over time, arcs to 2 robots nearby). The gun goes away for the swing and is drawn again.
  Frag cans (G, src/game/throwables.js): carry 3, thrown from the support hand; they bounce, a red ring shows the blast
  reach in the last second, and the blast hurts robots (and you, capped at 35). Ammo boxes give one back.
  Unlocks (src/data/unlocks.js, stands at the start of the level): dagger L3, frag cans + nunchucks L4, katana + Voltaxe
  L5 (every melee weapon and grenades by level 5); SG-9 Scrapper pump shotgun L7 (loads shell by shell), AR-40 Vanguard
  battle rifle L8, SG-12 Thunderclap auto shotgun L9, SR-9 Railspike rail rifle L11 (3x scope, pierces 4 robots).
  A save that already cleared a level gets what stood at its start when the next level loads.
  Models and arm actions: blender/fam_weapons.py (MELEE_SWINGS, THROW_L, pump_fire, shell_reload).

WEAPON DROPS, MELEE STAMINA, MUZZLE CANS (round 4)
  Waves (src/data/levelplans.js tuneWaves): light robots x1.15 on level 1 rising to x1.6 on level 13, each level has at
  least 5% more robots than the one before (82 on level 1 to about 250 on level 13); Soldiers and Blade Bots at 2.5x
  (light robots make room, never more than half a wave), Soldiers from level 4, Blade Bots from
  level 7; the next wave drops in when 6 or fewer robots are left.
  Gun tiers (src/game/wdrops.js): every gun has a quality tier, gray Standard x1.00, green Tuned x1.07, blue Rare x1.14,
  purple Epic x1.22, orange Legendary x1.32 damage (shown as its colour in the inventory). Soldiers drop guns at
  6 / 3 / 2 / 0.8 / 0.2 % (gray / green / blue / purple / orange); blade bots drop the katana or Voltaxe they wield at 7 %.
  Nothing is taken by walking over it and nothing is broken down into gems: walk up to a dropped gun (its card shows)
  and press E (touch: USE). A model you do not own joins the arsenal: carried at once if a loadout slot is free, else in
  the backpack. A model you own is swapped and the one you had is laid on the floor in its place. Or leave it there.
  A gun stands in a tall beam of its tier colour with ribbons of light and sparks, about twice the size of a gear beam.
  Melee costs stamina per swing (dagger 12 %, nunchucks 13 %, katana 20 %, Voltaxe 32 % of the pool) and ends a sprint;
  out of stamina a swing is 50 % slower and hits for 60 %.
  Muzzle cans (one per gun): acid, Arc Can (shock + arcs to the nearest robot, after level 3), Boom Can (small blast on
  the robot, never hurts you, after level 5), Void Can (a singularity pulls nearby robots into the one you hit, after
  level 7). Shotguns take the Arc / Boom / Void cans.
  Undercover (F): a quick fade-flicker in, then a dark blue stealth look with every robot outlined in glowing blue.

GUN LEVELS AND LAUNCHERS (round 5; src/core/gunlevel.js, src/game/launchers.js, tests/unit/gunlevel.test.js)
  Gun levels: every gun has an item level (Lv N on the E prompt, the rack prompt, the gun card and the HUD
  weapon panel). A drop is the campaign level it dropped on; a rack or stand gun the level it was taken on; guns from
  older saves get the highest level cleared (saved per gun in slot.gunLevel). Damage x (1 + 0.055 (Lv - 1)): x1.72 on
  14, x2.60 on 30, a little under the robots' health growth (x1.78 / x2.74), so a fresh gray gun kills a robot of its
  level in about as many hits as on level 1; tier, Upgrade Bench and skills put it ahead. A gun never counts below
  (player level - 4, the player level capped at the level being played), so old favourites stay usable but new drops
  are ~8-20% better. Melee weapons ride that floor. A pickup of a gun you own replaces it when tier x level (launchers:
  also x (mag / base)^0.35) beats yours now; taking it is always the player's call (E), the card compares the two.
  Launchers (no mods fit them; from campaign level 14 on, i.e. after level 13 is beaten):
    RL-3 Hothead: rapid-fire rockets (0.5 s), 3-5 per cassette (rolled per drop), 220 direct + 140 splash (3.2 m),
      reload 3.2 s, 42 m/s. Element rolled per drop: none (34%), Blast (22%: +30% radius, +10% splash, 3 bomblets),
      Volt (22%: shock over 3 s, arcs to 3 robots nearby), Acid (22%: acid over 5 s, an acid pool). The element shows in
      the name (Volt Hothead), the card, the canister glow on the gun and the rocket's trail.
    ML-6 Murmur: 2-4 salvos per cassette, 2 rockets a salvo; each salvo locks up to 5 robots in a 26 degree cone in
      front within 60 m (centre of view, close and threatening first; the aim point and spots around it fill the rest),
      shows red LOCK brackets (dim previews while the Murmur is up), then ripples out 6 homing missiles (48 direct +
      44 splash, 2.2 m) over the locks; reload 3.4 s.
    Both: splash x0.5 behind cover, self damage like a frag can (35% of the splash, at most 35). Drops: 0.6% per soldier
    kill, 0.08% per other robot kill (Hothead 60 / Murmur 40), 3% of armory rack guns; tiers 50/28/15/5.5/1.5%.
  Rocket ammo: one pool for both (slot.rockets, loaded magazines included; 16 max), never from ammo boxes or respawns.
    Only soldiers drop rocket crates, through a director: need = how far rockets (plus crates on the map) are below
    70% of the cap with a launcher carried (30% with one only in the backpack, nothing without one), weighted by rockets
    fired in the last 90 s; a soldier kill drops a crate with chance 0.4 x need holding 2-5 rockets, a carried launcher
    short of one shot gets one after at most 4 dry soldier kills, and a level never hands out more than a quarter of
    its soldiers' count (at least 12). A new launcher comes with one magazine of rockets.
  Balance (unit-tested): the highest damage per shot of any gun; single-target damage over a magazine + reload
  1.4-2.2x the best rifle / SMG; a level's rockets (pool + budget) at 2.5 robots per rocket stay under 25% of its robots.

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

ROBOTS OF LEVELS 20+ (rows mech / grenadier / hawk in src/data/enemies.js; src/game/troops.js, trooperrig.js, ai.js;
  models in blender/fam_trooper.py (fps-troopers.glb) and blender/fam_bots.py (fps-bots.glb))
  From campaign level 20 on, the Gunner (green trash-can robot) and the Bomber (blue bomb bot) are gone; levels 1-19
  play exactly as before. The mapping runs once per level plan in src/data/levelplans.js (IB.lateWaves, called at the
  end of tuneWaves, after the 5%-a-level climb is settled on the old robots; IB.LATE_WAVES holds the numbers):
    gunner + bomber -> Robot Trooper ('mech'), 0.6 per robot (it is about twice as tough as a Gunner);
    drone -> Hawk ('hawk'), 0.75 per robot; a quarter of the soldiers -> Grenadier ('grenadier').
  The robots those shares leave out come back as Crawlers (in the new skin from level 22), so a level keeps its count
  and the campaign's robot totals keep climbing; the threat climbs through the tougher robots.
  The shares are carried over the waves of the whole level, so a level holds exactly the rounded share (3/4 Soldiers,
  1/4 Grenadiers) and each wave is within one robot of it; a wave of 4 or more soldiers always has a Grenadier, a wave
  that had gunners / bombers / drones keeps at least one Robot Trooper / Hawk. Theme files keep writing gunner, drone,
  soldier (bomber 0-2 a wave); a plan with lateRobots: false keeps the old robots, and waves may name mech / hawk /
  grenadier directly (left as written).
  Robot Trooper: built like the Soldier (same rig, animations and brain) but a robot: a heavy industrial walker of
    bevelled blocks (big shoulder blocks, a small low head with one red optic, wide chest on a narrow piston waist, a
    back reactor as its weak spot, segmented piston arms with clamp hands, tall legs on flat feet, stencils and hazard
    marks), each block skinned to one bone; four colourways (gunmetal, olive, sand, arctic). Fires 3-round carbine bursts of
    normal rounds only, no grenades, rifle-butts up close; a light armour pool (25 vs the Soldier's 60, slower recharge).
    Guns drop at 40% of a Soldier's rates.
  Grenadier: a Soldier (same kit colours, shield, rifle butt and drops) holding a 6-shot 40 mm grenade launcher (olive,
    revolving drum) with a bandolier of grenades across the chest; its carbine is hidden (the carbine's vertices carry
    vertex alpha 0 -> aMask). One grenade per volley every 3.4-5 s on a high arc; a red ring waits where it will land;
    it bursts on impact (or 0.45 s after it comes to rest): 3 m blast.
  Hawk: an armoured aerial robot (graphite fuselage, V-tail, two ducted fans that tilt with its flight, a chin turret, a
    sensor eye). Orbits like the Drone, faster and tougher, darts aside when hit. Each Hawk fires one round type, shown by
    its accent strips, duct rims, thruster glow and eye: steel white = normal, blue = shock (electric damage over time),
    green = acid (acid damage over time), orange = explosive (a small blast); 40 / 20 / 20 / 20%. Shot down, it drops
    out of the air and blows up where it lands.
  Crawler: the old look is phased out (1/2 of the Crawlers on level 20, 1/4 on 21, none from 22); the others wear an advanced skin of the same silhouette (plated shell, sloped head ring,
    wrap-around cyan visor, panel lines and bolts), painted per crawler by a two-colour key-tint material (ai.js keyMat2):
    66% grey / 33% black or 66% black / 33% grey, half each; one in three also carries white specks and a stencil chevron.
  Review: node tests/e2e/latebots.spec.js (SHOTS=1 -> tests/e2e/review/latebots-*.png), tests/unit/latebots.test.js.

LOOT AND GEAR
  About one robot in twenty drops an item: a drop pod with a beam in its rarity colour, also marked on the radar as a
  diamond. Walk over it to bag it; an empty slot is filled right away. Walking up to it shows its item card (stats,
  perk, compare with what you wear or have fitted), like a gun's. Bag (worn and fitted items included): 16 slots at
  player LV 1, a slot or two more every level, the full 40 from LV 20 (LOOT.invStart / invCap / invCapLevel).
  Legendary gun attachments: a Legendary attachment roll stays Legendary one time in three, otherwise it drops as an
  Epic or a Rare one (LOOT.legendaryAttachKeep); shield cells and vests are not affected.
  Inventory: every gun and item has a Drop button (the last carried gun cannot be dropped).
  Rarities: Common (white), Rare (blue), Epic (purple), Legendary (orange, only from campaign level 6). Rarer gear
  drops more often the further you get (LOOT.rarityOdds in src/data/loot.js; levels 1-3 roll as they always did):
      level      1-3   4    5    6    7    8    9    10   11   12   13   15   17+
      Common      70   66   62   56   52   48   44   40   36   33   30   27   24
      Rare        24   26   28   29   30   31   32   33   34   34   35   35   35
      Epic         6    8   10   12   14   16   18   20   22   24   25   26   27
      Legendary    0    0    0    3    4    5    6    7    8    9   10   12   14
  Stats roll inside the rarity's range, then grow with the campaign level (LOOT.levelScale): levels 1-3 as before,
  past level 3 shields (capacity, recharge, vest health, Nova damage) grow about as fast as the robots' pressure
  (capacity and recharge rate x1.5 at base and x(1 + 0.0008 (L - 1)^2) on top: a top Legendary cell holds 312 on level 20, 550 on 30, 922 on 40, 1468 on 50; x1.35 on level 6, x1.71 on 10, x1.98 on 13, cap x5.78 at level 50) and attachments a little (x1.12 / 1.24 / 1.33, cap x2.44 at level 50); a stat with a hard ceiling grows on a gentler slope so a top Legendary roll reaches it at level 50 (both keep growing to the beta level cap, 50).
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
  node tests/e2e/collision-audit.spec.js    (every map: no collision box stops the player in open air -- invisible walls)
  node tests/e2e/vfx-shots.js               (frame-stepped explosion screenshots -> tests/e2e/review/vfx-*.png)
  node tests/e2e/troops.spec.js             (Soldier shield / grenades / melee, Blade Bot dash; SHOTS=1 -> review/troops-*.png)
  node tests/e2e/hud-shots.js              (HUD, enemy health bars and loader at 3 sizes -> tests/e2e/review/hud-*.png, loader-*.png)
  Dev page: serve the repo folder over http and open Source/dev.html  (add ?autotest=1 to skip the title).

SAVING
  Progress lives in the save slot as it is earned (XP, gems, items, guns, skills, the loadout in key order) and is
  written: at level start and clear, at every zone clear, on pause, on quitting to the title, when the page is hidden
  or closed (visibilitychange / pagehide / beforeunload), and by an autosave within 12 s of anything earned
  (game.js G.saveNow / G.touchSave). The gun in hand is saved too (slot.curGun) and comes to hand at the next start.
  A level itself is not checkpointed: Continue starts the level you were on from its first zone.
