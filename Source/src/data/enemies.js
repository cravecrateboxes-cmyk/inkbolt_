/* INKBOLT - robot and boss tables (brief sections 4.4, 5.7, 5.8, 2.1). Pure data, no DOM.
   hp / damage are level-1 values; scale with IB.Damage.enemyHpMul / enemyDmgMul.
   radius / height: collision capsule (m). coreOffset: core sphere centre relative to the robot's
   feet (x right, y up, z forward). windup / recover in seconds. cost = level generator points. */
(function (IB) {
  'use strict';

  var ENEMIES = {
    crawler: {
      id: 'crawler', name: 'Crawler', built: 'Kitted-out tin can on 4 spring legs', first: 1,
      hp: 30, shield: 0, speed: 5.0, chargeSpeed: 0, attack: 'Lunge bite', damage: 8,
      windup: 0.35, recover: 0.4, range: 1.4, gems: { chip: 1, shard: 0, core: 0 }, cost: 1,
      color: '#C9CFD6', accent: '#D9663B', pack: [3, 6], zigzag: true,
      radius: 0.45, height: 0.7, coreOffset: [0, 0.4, 0.2], coreRadius: 0.16,
      notes: 'Comes in packs of 3 to 6; zigzags'
    },
    gunner: {
      id: 'gunner', name: 'Gunner', built: 'Armoured sentry with a twin autocannon', first: 2,
      hp: 55, shield: 0, speed: 3.0, chargeSpeed: 0, attack: '3-bolt volley', damage: 6,
      bolts: 3, boltSpeed: 22, windup: 0.5, recover: 0.8, range: 22,
      gems: { chip: 2, shard: 0, core: 0 }, cost: 2, color: '#4FA36A', keepDistance: [8, 16],
      usesCover: true, radius: 0.55, height: 1.3, coreOffset: [0, 0.95, 0.3], coreRadius: 0.2,
      notes: 'Keeps 8 to 16 m, uses cover'
    },
    bomber: {
      id: 'bomber', name: 'Bomber', built: 'Fizzing bottle on a roller', first: 3,
      hp: 25, shield: 0, speed: 4.2, chargeSpeed: 0, attack: 'Rushes, fuse flash, explodes',
      damage: 35, robotDamage: 45, blastRadius: 3, windup: 0.6, fuse: 0.6, recover: 0, range: 2,
      hurtsRobots: true, gems: { chip: 2, shard: 0, core: 0 }, cost: 1.5, color: '#3E86D8',
      radius: 0.4, height: 0.9, coreOffset: [0, 0.45, 0.2], coreRadius: 0.15,
      notes: 'Shoot it early: its blast also hurts robots'
    },
    tosser: {
      id: 'tosser', name: 'Tosser', built: 'Jar-head catapult on treads', first: 4,
      hp: 60, shield: 0, speed: 2.6, chargeSpeed: 0, attack: 'Lobs an ink jar', damage: 20,
      dot: 5, puddleRadius: 2.5, puddleTime: 2, ringLead: 0.8, windup: 0.7, recover: 1.0,
      range: 18, gems: { chip: 3, shard: 0, core: 0 }, cost: 2.5, color: '#F08A2E',
      keepDistance: [8, 16], radius: 0.6, height: 1.2, coreOffset: [0, 0.8, 0.3], coreRadius: 0.2,
      notes: 'Red ring marks the landing spot 0.8 s ahead'
    },
    drone: {
      id: 'drone', name: 'Drone', built: 'Soda can with a 4-rotor lid', first: 6,
      hp: 35, shield: 0, speed: 4.5, chargeSpeed: 0, attack: 'Strafing bolt bursts', damage: 5,
      bolts: 4, boltSpeed: 22, windup: 0.45, recover: 0.8, range: 20, flying: true, hover: 3,
      gems: { chip: 3, shard: 0, core: 0 }, cost: 2, color: '#E2483D', keepDistance: [8, 16],
      radius: 0.4, height: 0.6, coreOffset: [0, 0.3, 0.2], coreRadius: 0.14,
      notes: 'Hovers 3 m up; one rocket splash kills groups'
    },
    shieldbot: {
      id: 'shieldbot', name: 'Shieldbot', built: 'Steel bucket behind a stop-sign shield', first: 7,
      hp: 90, shield: 150, speed: 2.4, chargeSpeed: 0, attack: 'Shield bash', damage: 18,
      windup: 0.6, recover: 1.0, range: 1.8, shieldArc: 120,
      gems: { chip: 0, shard: 1, core: 0 }, cost: 4, color: '#7D8796', shieldColor: '#FF8A3D',
      radius: 0.6, height: 1.5, coreOffset: [0, 1.05, -0.25], coreRadius: 0.2,
      notes: 'Shield blocks frontal shots; flank it, grenade it, or axe it'
    },
    bruiser: {
      id: 'bruiser', name: 'Bruiser', built: 'Dumpster on piston legs', first: 8,
      hp: 260, shield: 0, speed: 2.2, chargeSpeed: 9, attack: 'Slam (3 m) or charge',
      damage: 25, chargeDamage: 30, slamDamage: 25, slamRadius: 3, slamWindup: 0.7,
      windup: 0.9, recover: 1.2, range: 3, chargeRange: 14,
      gems: { chip: 3, shard: 1, core: 0 }, cost: 6, color: '#2F7F5E',
      staggerOnly: ['chargedAxe', 'rocketDirect', 'chunk25'],
      radius: 1.2, height: 2.4, coreOffset: [0, 1.7, 0.9], coreRadius: 0.3,
      notes: 'Staggers only from charged axe, rocket direct hit or 25% chunk'
    },
    binhive: {
      id: 'binhive', name: 'Bin Hive', built: 'Overflowing trash can, stationary', first: 11,
      hp: 200, shield: 0, speed: 0, chargeSpeed: 0, attack: 'Spits a Crawler', damage: 0,
      windup: 0.5, recover: 0, spawnEvery: 6, spawnType: 'crawler', maxChildren: 3, stationary: true,
      gems: { chip: 0, shard: 2, core: 0 }, cost: 7, color: '#6E7480',
      radius: 0.9, height: 1.6, coreOffset: [0, 1.5, 0], coreRadius: 0.3, coreOnlyOpen: true,
      notes: 'Lid flips open to show its core during each spawn'
    },
    /* Soldier (game/troops.js): an armoured robot trooper. A shield pool (shield, x enemyHpMul) soaks damage before
       health and recharges after shieldDelay s at shieldRate/s; keeps 7-15 m and strafes / uses cover, fires 4-bolt
       bursts, throws up to `grenades` frag grenades (arc, bounce, red ring, blast), rifle-butts the player inside
       meleeRange. armour: per-instance plate colours; torso / helmet shape sets. weaponDrops: chances per rarity on a
       player kill (read by IB.WeaponDrops.roll). */
    soldier: {
      id: 'soldier', name: 'Soldier', built: 'Trooper in SWAT / military kit with a carbine', first: 4,
      hp: 80, shield: 60, shieldPool: true, shieldDelay: 3.5, shieldRate: 24, speed: 3.2, chargeSpeed: 0,
      attack: '4-round bursts (some explosive, shock or acid rounds), frag grenades, rifle-butt strike', damage: 6, bolts: 4, boltSpeed: 58,
      specialRounds: { boom: 0.035, shock: 0.035, acid: 0.035 },
      windup: 0.45, recover: 0.7, range: 24, keepDistance: [7, 15], usesCover: true,
      grenades: 3, grenadeDamage: 30, grenadeRobotDamage: 20, grenadeRadius: 3.4, grenadeFuse: 2.1, grenadeEvery: [6, 10],
      grenadeRange: [6, 19], grenadeWindup: 0.6,
      meleeDamage: 14, meleeRange: 2.2, meleeWindup: 0.4, meleeKnock: 6,
      gems: { chip: 4, shard: 0, core: 0 }, cost: 3.5, color: '#7FA8E0',
      armour: ['#EEF1F5', '#9EA5B0', '#6F95D8', '#9B7BD8', '#474C59', '#C46C6C'],
      torsos: ['A', 'B'], helmets: ['A', 'B', 'C'],
      radius: 0.36, height: 1.88, coreOffset: [0, 1.32, 0.17], coreRadius: 0.11,
      weaponDrops: { gray: 0.12, green: 0.06, blue: 0.04, purple: 0.016, orange: 0.0034 },   // doubled: guns drop twice as often; legendary x0.85 (rarer world drops)
      notes: 'Shield bar soaks damage first and recharges; 3 grenades each; rifle-butt up close'
    },
    /* Blade Bot (game/troops.js): hover saucer with a spinning hub arm that wields a katana or a Voltaxe (weapons).
       Patrols slowly; once it sees the player it homes in, winds up (spin-up whine, windup s), dashes at chargeSpeed
       for up to dashTime s spinning the blade at ~spinRev rev/s, cuts on contact (damage; the axe also shocks for
       shockDps x shockTime), overshoots and stays dizzy for `recover` s (dizzyMul damage taken). Too close: a spin
       slash in place (spinDamage per cut). meleeDrop: chance to drop its weapon on a player kill. */
    blader: {
      id: 'blader', name: 'Blade Bot', built: 'Hover saucer with a spinning blade arm (katana or Voltaxe)', first: 3,
      hp: 70, shield: 0, speed: 1.6, stalkSpeed: 2.6, chargeSpeed: 12, attack: 'Spin-up, dash, contact cuts',
      damage: 18, spinDamage: 7, shockDps: 4, shockTime: 2, windup: 0.8, recover: 1.4, dizzyMul: 1.35,
      range: 9, dashTime: 1.1, spinRev: 19, spinRange: 2.4, weapons: ['katana', 'eaxe', 'kusari'],
      // spawn odds per weapon (IB.bladerWeapon); the kusarigama ('kusari'): a sickle on a chain held by its weight. It
      // closes to kusariRange, whirls the chain around itself (a wide circle that sweeps over the player: kusariDamage
      // every kusariTick s while he stays inside kusariRadius), then a tell (kusariTell s, backing off to kusariThrowRange
      // m) and the sickle flies straight at where he stood (kusariThrow damage on a hit within 0.65 m; a sidestep beats
      // it) and is reeled back in
      weaponOdds: { katana: 1 / 3, eaxe: 1 / 3, kusari: 1 / 3 },
      kusariRange: 4.2, kusariRadius: 2.7, kusariWhirl: 1.8, kusariDamage: 5, kusariTick: 0.4, kusariTell: 0.6, kusariThrowRange: 4.5,
      kusariThrow: 16, kusariReach: 7.5, kusariSpeed: 15, kusariCool: [1.6, 2.6],
      gems: { chip: 3, shard: 0, core: 0 }, cost: 2.5, color: '#8A6CD8',
      radius: 0.48, height: 1.0, coreOffset: [0, 0.67, 0], coreRadius: 0.16,
      meleeDrop: 0.07,
      notes: 'Dodge the dash, then punish it while it is dizzy; never stand next to it'
    }
  };

  /* ---- levels 20+ (levelplans.js lateWaves turns the theme files' gunner / bomber / drone / soldier entries into these)
     Robot Trooper (game/troops.js + trooperrig.js): a gun-wielding robot built like the Soldier (same rig, animations
     and brain) from robotic parts: servo joints, piston limbs, a segmented chassis, a sensor head with one optic.
     Normal carbine rounds only, no grenades, a light armour pool (shield) that recharges slowly; a threat between a
     Gunner and a Soldier. Its guns drop at 40 % of a Soldier's rates. */
  ENEMIES.mech = {
    id: 'mech', name: 'Robot Trooper', built: 'Heavy industrial walker robot: big shoulder blocks, low boxy head with one red optic, piston arms with clamp hands, flat feet', first: 20,
    hp: 85, shield: 25, shieldPool: true, shieldDelay: 5, shieldRate: 12, speed: 3.0, chargeSpeed: 0,
    attack: '3-round carbine bursts (normal rounds), rifle-butt strike', damage: 6, bolts: 3, boltSpeed: 52,
    windup: 0.5, recover: 0.8, range: 24, keepDistance: [8, 16], usesCover: true, grenades: 0,
    meleeDamage: 12, meleeRange: 2.1, meleeWindup: 0.45, meleeKnock: 5,
    gems: { chip: 3, shard: 0, core: 0 }, cost: 3, color: '#A9B3BF',
    radius: 0.36, height: 1.8, coreOffset: [0, 1.36, -0.17], coreRadius: 0.11,
    weaponDrops: { gray: 0.048, green: 0.024, blue: 0.016, purple: 0.0064, orange: 0.00136 },   // 40 % of a Soldier's
    notes: 'Robot Trooper: tougher than a Gunner, no grenades; its light armour recharges slowly'
  };
  /* Grenadier: a Soldier (same kit, armour colours, shield, rifle butt and drops) holding a 6-shot grenade launcher
     instead of the carbine. One 40 mm grenade per volley on a high arc, a red ring on the ground where it will land,
     it bursts on impact (or after shellFuse s if it comes to rest), far slower than a Soldier's bursts (fireEvery s). */
  ENEMIES.grenadier = {
    id: 'grenadier', name: 'Grenadier', built: 'Soldier with a 6-shot grenade launcher', first: 20,
    hp: 80, shield: 60, shieldPool: true, shieldDelay: 3.5, shieldRate: 24, speed: 3.0, chargeSpeed: 0,
    attack: 'Lobs 40 mm grenades (red ring where they land, burst on impact), rifle-butt strike', damage: 26,
    launcher: true, shellDamage: 26, shellRobotDamage: 14, shellRadius: 3.0, shellFuse: 0.45, fireEvery: [3.4, 5.0], minRange: 5,
    windup: 0.7, recover: 0.9, range: 26, keepDistance: [9, 17], usesCover: true, grenades: 0,
    meleeDamage: 14, meleeRange: 2.2, meleeWindup: 0.4, meleeKnock: 6,
    gems: { chip: 4, shard: 0, core: 0 }, cost: 3.5, color: '#D9A441',
    armour: ['#EEF1F5', '#9EA5B0', '#6F95D8', '#9B7BD8', '#474C59', '#C46C6C'], torsos: ['A', 'B'], helmets: ['A', 'B', 'C'],
    radius: 0.36, height: 1.88, coreOffset: [0, 1.32, 0.17], coreRadius: 0.11,
    weaponDrops: { gray: 0.12, green: 0.06, blue: 0.04, purple: 0.016, orange: 0.0034 },
    notes: 'Watch for the red ring and step out of it; slow to reload'
  };
  /* Hawk: an advanced aerial robot (sleek armoured fuselage, ducted fans, sensor eye, chin turret). Hovers and strafes
     like the Drone, a little faster and tougher, dodges when hit. Each Hawk fires one round type, shown by its accent
     colour (rounds: odds per Hawk): normal (steel white), shock (blue: electric damage over time), acid (green: acid
     damage over time) or explosive (orange: a small blast). */
  ENEMIES.hawk = {
    id: 'hawk', name: 'Hawk', built: 'Armoured aerial robot with ducted fans and a chin turret', first: 20,
    hp: 50, shield: 0, speed: 5.4, chargeSpeed: 0, attack: '3-round bursts of normal, shock, acid or explosive rounds',
    damage: 5, bolts: 3, boltSpeed: 30, windup: 0.4, recover: 0.75, range: 22, flying: true, hover: 3.3,
    rounds: { bullet: 0.4, shock: 0.2, acid: 0.2, boom: 0.2 },
    roundColors: { bullet: '#E6ECF5', shock: '#3FC8FF', acid: '#6BE03A', boom: '#FF7A1E' },
    gems: { chip: 3, shard: 0, core: 0 }, cost: 2.5, color: '#3FC8FF', keepDistance: [9, 17],
    radius: 0.45, height: 0.6, coreOffset: [0, 0.17, 0.17], coreRadius: 0.12,
    notes: 'Its accent colour tells its rounds: white normal, blue shock, green acid, orange explosive'
  };

  /* ---- levels 35+ (levelplans.js lateWaves35 turns a share of the hawks / robot troopers into these)
     Jet Trooper (game/jets.js): an advanced robot soldier on a jet back unit. Outdoors it flies at `hover` m and orbits
     like a Hawk, firing bursts from its hand launcher, and boost-dashes sideways every airDash.every s (airDash.speed
     m/s for airDash.time s); indoors (ceiling under lowCeiling m over its floor) it skims low (skim m) and now and then
     ground-boosts across the room (dashSpeed for dashTime s) with a hop (hopHeight m). Its rocket volley: whenever it
     is within volley.near m of the player, or within volley.far m and at least volley.above m higher, it climbs
     volley.rise m (volley.riseTime s) and holds steady, raises and opens its two pods (3 tubes each) and locks on (a
     red ring shrinking on the player, rising beeps) for
     volley.lock s, then fires 6 rockets (volley.gap s apart) at the spot it locked plus a little scatter: dodgeable by
     moving. Cooldown volley.cool s. Every rocket deals explosive damage (volley.damage at the centre, volley.radius m);
     each Jet Trooper rolls one element (elements: odds), shown on its accents: shock (electric: + electric damage over
     time on the player), acid (+ acid damage over time) or boom (plain explosive: boomMul more blast, a wider one). */
  ENEMIES.jet = {
    id: 'jet', name: 'Jet Trooper', built: 'Armoured robot soldier on a jet back unit, two rising rocket pods (3 tubes each), a hand-held bullet launcher', first: 35,
    hp: 100, shield: 40, shieldPool: true, shieldDelay: 5, shieldRate: 14, speed: 4.6, chargeSpeed: 0, dashSpeed: 10, dashTime: 0.6,
    airDash: { every: [1.6, 3.0], time: 0.36, speed: 11 }, skim: 0.22, hopHeight: 0.7,
    attack: '4-round launcher bursts; a locked-on 6-rocket volley (electric, acid or explosive)', damage: 5, bolts: 4, boltSpeed: 40,
    windup: 0.45, recover: 0.75, range: 26, keepDistance: [9, 16], flying: true, hover: 4.2, lowCeiling: 6.5,
    volley: { rockets: 6, near: 14, far: 22, above: 2.2, lock: 0.95, gap: 0.09, cool: [6.5, 9], damage: 13, robotDamage: 6, radius: 2.3,
      speed: 15, turn: 2.2, homeT: 0.45, scatter: 1.1, rise: 0.9, riseTime: 0.35 },
    elements: { shock: 1 / 3, acid: 1 / 3, boom: 1 / 3 },
    elementColors: { shock: '#3FC8FF', acid: '#6BE03A', boom: '#FF7A1E' },
    elementDot: { shock: { dps: 4, time: 2.5 }, acid: { dps: 3.2, time: 4 } }, boomMul: 1.35, boomRadiusMul: 1.25,
    pullResist: 1,
    gems: { chip: 5, shard: 0, core: 0 }, cost: 4.5, color: '#FF7A1E',
    radius: 0.42, height: 2.0, coreOffset: [0, 1.36, 0.22], coreRadius: 0.1,
    weaponDrops: { gray: 0.06, green: 0.03, blue: 0.02, purple: 0.008, orange: 0.0017 },
    notes: 'Watch its pods: when they rise and the red ring closes on you, move. Its accents tell the rocket element'
  };
  /* Rocket Soldier: a Soldier (same kit, armour, shield, rifle butt and weapon drops; no grenades) shouldering a
     launcher: it spawns with a Murmur or a Hothead (launchers: odds), rests the stock on its shoulder to fire, and
     fires far slower than a Soldier or the player's launchers. Hothead: `hothead.rockets` heavy rockets `gap` s apart;
     Murmur: `murmur.rockets` small missiles that home in a little (turn rad/s for homeT s) -- strafe to shake them. */
  ENEMIES.rocketeer = {
    id: 'rocketeer', name: 'Rocket Soldier', built: 'Soldier with a Murmur or Hothead rocket launcher on its shoulder', first: 35,
    hp: 80, shield: 60, shieldPool: true, shieldDelay: 3.5, shieldRate: 24, speed: 2.9, chargeSpeed: 0,
    attack: 'Shoulder-fired rockets (Hothead) or a homing missile salvo (Murmur), rifle-butt strike', damage: 22,
    rockets: true, launchers: { hothead: 0.5, murmur: 0.5 },
    hothead: { rockets: 2, gap: 1.1, damage: 22, robotDamage: 10, radius: 3.0, speed: 21, turn: 0, homeT: 0, fireEvery: [5.5, 7.5], scale: 1 },
    murmur: { rockets: 4, gap: 0.24, damage: 9, robotDamage: 5, radius: 2.1, speed: 12, turn: 1.6, homeT: 1.3, fireEvery: [6.5, 8.5], scale: 0.62 },
    minRange: 6, windup: 0.8, recover: 0.9, range: 26, keepDistance: [10, 18], usesCover: true, grenades: 0,
    meleeDamage: 14, meleeRange: 2.2, meleeWindup: 0.4, meleeKnock: 6, pullResist: 1,
    gems: { chip: 4, shard: 0, core: 0 }, cost: 4, color: '#F26B1D',
    armour: ['#EEF1F5', '#9EA5B0', '#6F95D8', '#9B7BD8', '#474C59', '#C46C6C'], torsos: ['A', 'B'], helmets: ['A', 'B', 'C'],
    radius: 0.36, height: 1.88, coreOffset: [0, 1.32, 0.17], coreRadius: 0.11,
    weaponDrops: { gray: 0.12, green: 0.06, blue: 0.04, purple: 0.016, orange: 0.0034 },
    notes: 'It shoulders the launcher before it fires: break line of sight or keep strafing'
  };
  // the Singularity (Void can, game/gear.js) cannot drag flyers or the shoulder-braced Rocket Soldier (1 = 100 % resist)
  ENEMIES.drone.pullResist = 1;
  ENEMIES.hawk.pullResist = 1;

  /* weighted pick from {key: odds} with x in [0, 1) (odds need not sum to 1) */
  function pickOdds(odds, x) {
    var keys = Object.keys(odds), tot = 0, i;
    for (i = 0; i < keys.length; i++) tot += odds[keys[i]];
    var acc = 0, t = x * tot;
    for (i = 0; i < keys.length; i++) { acc += odds[keys[i]]; if (t < acc) return keys[i]; }
    return keys[keys.length - 1];
  }
  IB.pickOdds = pickOdds;
  // a Blade Bot's weapon (katana, Voltaxe or kusarigama), a Jet Trooper's element, a Rocket Soldier's launcher
  IB.bladerWeapon = function (x) { var b = ENEMIES.blader; return pickOdds(b.weaponOdds || { katana: 1, eaxe: 1 }, x); };
  IB.jetElement = function (x) { return pickOdds(ENEMIES.jet.elements, x); };
  IB.rocketeerLauncher = function (x) { return pickOdds(ENEMIES.rocketeer.launchers, x); };
  /* one Jet Trooper rocket for element elem at damage multiplier dmgMul (r.dmgMul x the late explosives' ease-off):
     explosive damage at the blast centre, its radius, and the damage over time it leaves on the player it reaches
     ({kind 'shock' | 'acid', dps, time} or null; game/jets.js hands it to IB.Troops.dot) */
  IB.jetRocket = function (elem, dmgMul) {
    var J = ENEMIES.jet, V = J.volley, boom = elem === 'boom', d = J.elementDot[elem];
    return { damage: V.damage * (dmgMul || 1) * (boom ? J.boomMul : 1), radius: V.radius * (boom ? J.boomRadiusMul : 1),
      dot: d ? { kind: elem, dps: d.dps * (dmgMul || 1), time: d.time } : null };
  };
  // 1 = the Singularity cannot pull this robot type at all
  IB.pullResist = function (type) { var e = ENEMIES[type]; return (e && e.pullResist) || 0; };

  var BOSSES = {
    skimmer: {
      id: 'skimmer', name: 'Skimmer', level: 5, theme: 'pool', hp: 2500,
      gems: { chip: 0, shard: 2, core: 2 },
      built: 'Pool-cleaner robot built from a pump, hoses and folded lounge chairs',
      arena: 'Pool deck with an empty deep end and lounge-chair cover',
      mechanic: 'Hose sweep: a water jet sweeps the deck at knee height; jump it or hide behind chairs. Phase 2 adds a second hose; phase 3 floods the deep end (slows you 40% in water).',
      tell: 'Hose nozzles flash Amber and a hiss rises for 1.0 s', tellTime: 1.0,
      window: 'Pump lid lifts for 3 s after each sweep', windowTime: 3,
      waterSlow: 0.4
    },
    dumpstertank: {
      id: 'dumpstertank', name: 'Dumpster Tank', level: 10, theme: 'military', hp: 4500,
      gems: { chip: 0, shard: 3, core: 3 },
      built: 'Tracked dumpster with three exhaust stacks and a mortar tube',
      arena: 'Parade ground with sandbag walls and two hangars',
      mechanic: 'Mortar rings: lobs 3 to 5 shells; red rings mark impacts 1.2 s ahead. Destroy all 3 exhaust stacks (400 HP each) to force the lid open. Lid opening also releases 4 Crawlers.',
      tell: 'Mortar tube tilts up with three clanks', tellTime: 1.0,
      window: 'Lid open 5 s after the stacks are gone (stacks regrow in phase 3)', windowTime: 5,
      shells: [3, 5], ringLead: 1.2, stacks: 3, stackHp: 400, adds: 4
    },
    cartcolossus: {
      id: 'cartcolossus', name: 'Cart Colossus', level: 15, theme: 'stockpile', hp: 7000,
      gems: { chip: 0, shard: 4, core: 4 },
      built: 'A giant built from welded shopping carts around a checkout conveyor core',
      arena: 'Long warehouse aisles with tall shelves',
      mechanic: 'Aisle charge: charges down an aisle; if it hits a shelf end it is stunned for 4 s. Phase 2 drops Bomber bottles from its basket; phase 3 charges twice in a row.',
      tell: 'Wheels spin up with a screech and sparks for 1.1 s; its target aisle\'s floor lights Alert Red',
      tellTime: 1.1, window: 'Conveyor core exposed while stunned', windowTime: 4
    },
    compactorprime: {
      id: 'compactorprime', name: 'Compactor Prime', level: 20, theme: 'recycling', hp: 11000,
      gems: { chip: 0, shard: 6, core: 6 },
      built: 'A walking trash compactor with a magnet crane arm and a scrap antenna',
      arena: 'Square pit with conveyor edges',
      mechanic: 'Magnet pull: the arm pulls the player 4 m/s toward it for 2.5 s and catches grenades and rockets (they detonate harmlessly on the magnet). Compaction: each phase moves the pit walls 4 m inward. Phase 3 alternates pull and a 360 degree slam ring you must jump.',
      tell: 'Magnet coil glows Pop Teal and hums (noise band) for 1.0 s; slam ring is preceded by the body rising 1 m',
      tellTime: 1.0, window: 'Crusher plate opens for 3 s after each slam', windowTime: 3,
      pullSpeed: 4, pullTime: 2.5, wallStep: 4
    }
  };

  // Shared boss rules (5.8).
  var BOSS_RULES = {
    shellMul: 0.25, openMul: 1.5, openSniperMul: 2.5, phases: [1, 0.66, 0.33], hitStop: 0.035,
    loopHpMul: 0.35, tellSpeedup: 0.1, windowCut: 0.5, windowMin: 2
  };

  // AI timing (4.4).
  var AI_RULES = {
    spawnTelegraph: 0.8, patrolSpeedMul: 0.4, sightCone: 120, sightRange: 25, losInterval: 0.2,
    hearRange: 20, reaction: 0.4, recover: [0.4, 1.2], stagger: 0.6, staggerFrac: 0.25,
    blind: 3.5, blindAway: 1.5, blindMul: 1.25, flowInterval: 0.25, navCell: 0.5,
    spawnMinDist: 6, spawnMinDistInView: 4, separation: 0.6
  };

  IB.ENEMIES = ENEMIES;
  IB.ENEMY_ORDER = ['crawler', 'gunner', 'bomber', 'tosser', 'drone', 'shieldbot', 'bruiser', 'binhive', 'soldier', 'blader', 'mech', 'grenadier', 'hawk', 'jet', 'rocketeer'];
  IB.BOSSES = BOSSES;
  IB.BOSS_ORDER = ['skimmer', 'dumpstertank', 'cartcolossus', 'compactorprime'];
  IB.BOSS_RULES = BOSS_RULES;
  IB.AI_RULES = AI_RULES;
  IB.GLB_BOT_NAMES = IB.ENEMY_ORDER.map(function (id) { return 'BOT_' + id.toUpperCase(); });
  IB.GLB_BOSS_NAMES = IB.BOSS_ORDER.map(function (id) { return 'BOSS_' + id.toUpperCase(); });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
