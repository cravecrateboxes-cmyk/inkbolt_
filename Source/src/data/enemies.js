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
      weaponDrops: { gray: 0.12, green: 0.06, blue: 0.04, purple: 0.016, orange: 0.004 },   // doubled: guns drop twice as often
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
      range: 9, dashTime: 1.1, spinRev: 19, spinRange: 2.4, weapons: ['katana', 'eaxe'],
      gems: { chip: 3, shard: 0, core: 0 }, cost: 2.5, color: '#8A6CD8',
      radius: 0.48, height: 1.0, coreOffset: [0, 0.67, 0], coreRadius: 0.16,
      meleeDrop: 0.07,
      notes: 'Dodge the dash, then punish it while it is dizzy; never stand next to it'
    }
  };

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
  IB.ENEMY_ORDER = ['crawler', 'gunner', 'bomber', 'tosser', 'drone', 'shieldbot', 'bruiser', 'binhive', 'soldier', 'blader'];
  IB.BOSSES = BOSSES;
  IB.BOSS_ORDER = ['skimmer', 'dumpstertank', 'cartcolossus', 'compactorprime'];
  IB.BOSS_RULES = BOSS_RULES;
  IB.AI_RULES = AI_RULES;
  IB.GLB_BOT_NAMES = IB.ENEMY_ORDER.map(function (id) { return 'BOT_' + id.toUpperCase(); });
  IB.GLB_BOSS_NAMES = IB.BOSS_ORDER.map(function (id) { return 'BOSS_' + id.toUpperCase(); });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
