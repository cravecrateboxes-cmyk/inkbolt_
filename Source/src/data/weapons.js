/* INKBOLT - weapon table (brief section 5.2, 5.3, 5.4, 5.5, 5.6). Pure data, no DOM.
   Units: damage per bullet / pellet / swing; rpm shots per minute (burst weapons: see below);
   cycle seconds between shots or bursts; spread = cone half-angle in degrees; recoil degrees;
   reload seconds; ranges metres. Fields the brief leaves blank are 0 (see notes per entry).
   unlock = the campaign level whose start has it on a stand (src/data/unlocks.js); 0 = not in the campaign yet. */
(function (IB) {
  'use strict';

  var DEFAULTS = {
    pellets: 1, burst: 1, burstGap: 0, aimZoom: 0.85, scopeZoom: 0, moveMul: 1, pierce: 0,
    pierceMul: 1, coreMul: 1.75, recoilH: 0, reloadPerShell: false, splash: 0, radius: 0,
    exponent: 1, fuse: 0, carry: 0, speed: 0
  };

  function W(o) {
    var w = {};
    var k;
    for (k in DEFAULTS) w[k] = DEFAULTS[k];
    for (k in o) w[k] = o[k];
    if (w.cycle === undefined) w.cycle = w.rpm ? 60 / w.rpm : 0;
    if (w.rpm === undefined && w.cycle) w.rpm = 60 / w.cycle;   // melee: swings per minute from the swing cycle
    return w;
  }

  // every pistol shares one spare-ammo capacity, like the SMG / rifle / sniper classes
  var PISTOL_RESERVE = 250;

  var WEAPONS = {
    pip: W({
      id: 'pip', name: 'P-12 Warden', cls: 'pistol', slot: 1, fire: 'semi', damage: 18, rpm: 450,
      // Each gun rolls its magazine (40-50, see GunLevel.rollMagRange) on first use; the roll is kept in the save.
      // 3x damage on crit spots (core, head), as the Ironjaw.
      spreadHip: 0.8, spreadAim: 0.3, recoil: 1.2, recoilH: 0.3, reload: 1.1, mag: 40, magRange: [40, 50],
      reserve: PISTOL_RESERVE, coreMul: 3, headMul: 3,
      // 10% of hits split the round in two: the second half hits the nearest robot within 6 m for the same damage
      split: { chance: 0.1, range: 6 },
      unlock: 1, sound: 'click transient, 2.4 kHz noise snap, short bright tail'
    }),
    handcannon: W({
      // Wyrmforged: a very fast pistol (Maggie-style: click-fast, low recoil), 3x damage on crit spots (core, soldier head).
      // Each drop rolls its magazine (18-30, more at higher player levels) and a x2 or x3 damage multiplier (GunLevel.wyrmRoll).
      id: 'handcannon', name: 'Wyrmforged Ironjaw', cls: 'pistol', slot: 1, fire: 'semi', action: 'revolver',
      // revolver shot (def.action): heavier single kick, 1.6 (was 1.0); the extra vertical kick is in weapons.js fire()
      damage: 22, rpm: 750, spreadHip: 0.5, spreadAim: 0.15, recoil: 1.6, recoilH: 0.3, reload: 2.2,
      mag: 18, reserve: PISTOL_RESERVE, unlock: 2, coreMul: 3, headMul: 3, wyrm: { mag: [18, 30], mult: [2, 3] },
      sound: '120 to 50 Hz thump, noise crack, metal ring'
    }),
    twintap: W({
      // Brief gives 220 bursts/min only; rpm keeps that figure (bursts), cycle = 60/220.
      // burstGap (time between the 2 rounds of one burst) is not in the brief: 0.06 s chosen.
      // 5-round bursts. rpm is bursts per minute: 780 rounds/min (+30% on the old 600) = 156 bursts/min.
      id: 'twintap', name: 'P-16 Twinfire', cls: 'pistol', slot: 1, fire: 'burst', damage: 16, burst: 5,
      rpm: 156, cycle: 60 / 156, burstGap: 0.06, spreadHip: 1.0, spreadAim: 0.4, recoil: 0.9, recoilH: 0,
      // 50% of each hit's damage burns on as acid over 3 s (the same elemental over-time as the acid muzzle)
      acid: 0.5, acidDur: 3,
      reload: 1.3, mag: 16, reserve: PISTOL_RESERVE, unlock: 5, sound: 'double tick, tight snap, slide clack'
    }),
    buzz: W({
      id: 'buzz', name: 'KV-9 Buzzsaw', cls: 'smg', slot: 2, fire: 'auto', damage: 11, rpm: 900,
      spreadHip: 2.2, spreadAim: 1.2, recoil: 0.5, recoilH: 0.4, reload: 1.6, mag: 30, reserve: 180,
      unlock: 1, sound: 'fast buzz noise, low rattle, casing ticks'
    }),
    whisk: W({
      id: 'whisk', name: 'KV-4 Whiplash', cls: 'smg', slot: 2, fire: 'auto', damage: 8, rpm: 1100,
      spreadHip: 3.2, spreadAim: 2.0, recoil: 0.35, recoilH: 0.6, reload: 1.4, mag: 40, reserve: 240,
      unlock: 3, sound: 'thin high buzz, tin rattle'
    }),
    hornet: W({
      id: 'hornet', name: 'KV-7 Hornet', cls: 'smg', slot: 2, fire: 'auto', damage: 14, rpm: 750,
      spreadHip: 1.4, spreadAim: 0.6, recoil: 0.6, recoilH: 0.25, reload: 1.8, mag: 32, reserve: 192,
      unlock: 4, sound: 'sharp snap, mid thud, bolt clack'
    }),
    rivet: W({
      id: 'rivet', name: 'AR-22 Rivet', cls: 'rifle', slot: 3, fire: 'auto', damage: 22, rpm: 600,
      spreadHip: 1.4, spreadAim: 0.4, recoil: 0.9, recoilH: 0.3, reload: 2.0, mag: 30, reserve: 180,
      unlock: 2, sound: 'punchy crack, low body, rivet-gun clank'
    }),
    triplet: W({
      // rpm 1000 is the in-burst rate (burstGap = 0.06 s); cycle 0.32 s between bursts.
      id: 'triplet', name: 'AR-3 Tribolt', cls: 'rifle', slot: 3, fire: 'burst', damage: 26, burst: 3,
      rpm: 1000, cycle: 0.32, burstGap: 60 / 1000, spreadHip: 1.0, spreadAim: 0.25, recoil: 0.8, recoilH: 0,
      reload: 2.2, mag: 24, reserve: 144, unlock: 3, scopeView: true, sound: 'three cracks, rising pitch, burst-end clack'   // scopeView: aiming shows the scope view (the model carries a tube scope)
    }),
    longtom: W({
      id: 'longtom', name: 'DMR-60 Longtom', cls: 'rifle', slot: 3, fire: 'semi', damage: 60, rpm: 240,
      spreadHip: 0.6, spreadAim: 0.05, recoil: 2.8, recoilH: 0.4, reload: 2.4, mag: 10, reserve: 60,
      unlock: 4, aimZoom: 0.67, scopeView: true, coreMul: 2.0, sound: 'heavy crack, long tail, bolt slap'
    }),
    brick: W({
      id: 'brick', name: 'LMG-26 Bricklayer', cls: 'rifle', slot: 3, fire: 'auto', damage: 26, rpm: 500,
      spreadHip: 2.0, spreadAim: 0.8, recoil: 1.1, recoilH: 0.5, reload: 3.4, mag: 60, reserve: 240,
      unlock: 5, moveMul: 0.9, sound: 'deep chug, metal stomp, belt rattle'
    }),
    needle: W({
      // Scope: FOV = base / 3.5 (aimZoom = 1/3.5), toggles in 0.22 s; pierce 2, each pierce -30%.
      id: 'needle', name: 'SR-160 Needle', cls: 'sniper', slot: 4, fire: 'bolt', damage: 160, rpm: 45,
      spreadHip: 4.0, spreadAim: 0, recoil: 6.0, recoilH: 0, reload: 3.0, mag: 5, reserve: 25,
      unlock: 6, aimZoom: 1 / 3.5, scopeZoom: 3.5, scopeTime: 0.22, sway: 0.15, swayHz: 0.5,
      steadyTime: 2, steadyCooldown: 1, pierce: 2, pierceMul: 0.7, coreMul: 2.5,
      sound: 'huge crack, 0.6 s echo tail, bolt cycle'
    }),
    cancannon: W({
      // 140 direct + splash 120 x (1 - d/4)^0.7 within 4 m; projectile 28 m/s, r 0.15 m, 2 s life.
      id: 'cancannon', name: 'RL-1 Canister', cls: 'rocket', slot: 5, fire: 'projectile', damage: 140,
      rpm: 40, spreadHip: 0.3, spreadAim: 0.3, recoil: 5.0, recoilH: 0, reload: 2.6, mag: 1, reserve: 8,
      unlock: 0, splash: 120, radius: 4, exponent: 0.7, speed: 28, projRadius: 0.15, life: 2,
      gravity: 0, knockback: 9, selfMul: 0.35, selfCap: 35, shakeDeg: 1.5, shakeRange: 6,
      sound: 'whoosh launch, hiss trail loop, boom on hit'
    }),
    frag: W({
      id: 'frag', name: 'M-15 Frag Can', cls: 'grenade', slot: 'Q', pickSlot: 7, fire: 'throw', damage: 150,
      cycle: 0.45, rpm: 60 / 0.45, spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0,
      unlock: 4, splash: 150, radius: 5, exponent: 1, fuse: 2.2, carry: 3, speed: 18, throwUp: 4,
      restitution: 0.35, selfMul: 0.35, selfCap: 35, sound: 'tin pin pop, bounce clinks, boom'
    }),
    popflash: W({
      // 10 damage within 10 m plus Blinded 3.5 s (1.5 s facing away); bosses: 1.0 s stagger, 20 s immunity.
      id: 'popflash', name: 'FX-2 Pop Flash', cls: 'grenade', slot: 'Q', pickSlot: 8, fire: 'throw', damage: 10,
      cycle: 0.45, rpm: 60 / 0.45, spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0,
      unlock: 0, splash: 10, radius: 10, exponent: 0, fuse: 1.5, carry: 2, speed: 18, throwUp: 4,
      restitution: 0.35, blind: 3.5, blindAway: 1.5, bossStagger: 1.0, bossImmune: 20,
      playerRange: 12, playerAngle: 70, playerHold: 1.6, playerFade: 1.5, duckDb: 12,
      sound: 'pin pop, sharp bang, high ring'
    }),
    // Melee costs stamina: `stamina` = share of the max stamina pool per swing (the Stamina skill's bigger pool does not
    // make swings free). Out of stamina a swing is 50% slower and hits for 60% (game.js MELEE_WINDED).
    // ---- melee (struck with V: the gun goes away for one swing; src/game/weapons.js W.meleeStart). swing = clip length (s),
    // hit = fraction of the swing where the blow lands, arc = cone (deg) in front, range m; clips = Blender actions
    // <ID>_<clip> played in turn (combo). Unlocked at the start of campaign levels 3-5 (src/data/levelplans.js).
    dagger: W({
      id: 'dagger', name: 'Stinger', cls: 'melee', slot: 'V', fire: 'melee', damage: 40, swing: 0.32, hit: 0.46,
      arc: 70, range: 2.1, backstab: 2.5, clips: ['Strike', 'Strike2'], comboWindow: 0.45, cycle: 0.36,
      spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0, unlock: 3,
      stamina: 0.12, blurb: 'Fast stab. x2.5 damage on robots that have not seen you.', sound: 'quick swish, stab thunk'
    }),
    nunchucks: W({
      id: 'nunchucks', name: 'Twin Strikers', cls: 'melee', slot: 'V', fire: 'melee', damage: 24, swing: 0.30, hit: 0.40,
      hit2: 0.62, arc: 120, range: 2.3, stagger: true, clips: ['Strike', 'Strike2'], comboWindow: 0.45, cycle: 0.32,
      spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0, unlock: 4,
      stamina: 0.13, blurb: 'Two quick hits per swing in a wide arc. Staggers robots.', sound: 'chain whirr, wood clacks'
    }),
    katana: W({
      id: 'katana', name: 'Ronin Blade', cls: 'melee', slot: 'V', fire: 'melee', damage: 62, swing: 0.46, hit: 0.40,
      arc: 110, range: 2.7, combo: 3, comboMul: 1.6, comboWindow: 0.6, comboLunge: 2, clips: ['Strike', 'Strike2', 'Strike3'], cycle: 0.48,
      spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0, unlock: 5, blockMul: 0.4, parryWindow: 0.2, parryMul: 2,
      charged: 0, chargeTime: 0, knockback: 0,
      stamina: 0.2, blurb: 'Three-swing combo; the third cut does x1.6.', sound: 'air swish, steel ring on hit'
    }),
    eaxe: W({
      id: 'eaxe', name: 'Voltaxe', cls: 'melee', slot: 'V', fire: 'melee', damage: 95, swing: 0.75, hit: 0.44,
      arc: 80, range: 2.4, shock: { dps: 10, dur: 3, chain: 2, chainRange: 4.5, chainMul: 0.45 }, breaksShield: true, knockback: 6,
      clips: ['Strike', 'Strike2'], comboWindow: 0.7, cycle: 0.78, charged: 150, chargeTime: 0.8,
      spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0, unlock: 5,
      stamina: 0.32, blurb: 'Heavy electric chop: shocks the target and arcs to 2 robots nearby.', sound: 'heavy whoosh, crunch, zap'
    }),
    scrapper: W({
      // Slot 9; reloads one shell at a time (0.5 s per shell). Falloff: full to 8 m, 40% at 20 m.
      id: 'scrapper', name: 'SG-9 Scrapper', cls: 'shotgun', slot: 9, fire: 'pump', damage: 9, pellets: 9,
      rpm: 70, spreadHip: 6.0, spreadAim: 4.5, recoil: 3.5, recoilH: 0, reload: 0.5, reloadPerShell: true,
      mag: 6, reserve: 36, unlock: 7, sound: 'boom, pump clack'
    }),
    // ---- round 3 guns (Blender models in fam_weapons.py)
    vanguard: W({
      id: 'vanguard', name: 'AR-40 Vanguard', cls: 'rifle', slot: 3, fire: 'auto', damage: 34, rpm: 480,
      spreadHip: 1.6, spreadAim: 0.35, recoil: 1.3, recoilH: 0.45, reload: 2.3, mag: 20, reserve: 140,
      unlock: 8, moveMul: 0.95, sound: 'heavy crack, deep body, brake bark'
    }),
    thunder: W({
      id: 'thunder', name: 'SG-12 Thunderclap', cls: 'shotgun', slot: 9, fire: 'auto', damage: 8, pellets: 8, rpm: 240,
      spreadHip: 5.5, spreadAim: 4.0, recoil: 2.6, recoilH: 0.8, reload: 2.6, mag: 12, reserve: 72,
      unlock: 9, moveMul: 0.93, sound: 'boom, boom, drum rattle'
    }),
    railspike: W({
      // scope 3x; the slug pierces up to 4 robots (each one -15%)
      id: 'railspike', name: 'SR-9 Railspike', cls: 'sniper', slot: 4, fire: 'semi', damage: 135, rpm: 70,
      spreadHip: 3.0, spreadAim: 0, recoil: 4.0, recoilH: 0.2, reload: 2.6, mag: 6, reserve: 36,
      unlock: 11, aimZoom: 1 / 3, scopeZoom: 3, scopeTime: 0.22, pierce: 4, pierceMul: 0.85, coreMul: 2.2,
      sound: 'electric whine, sharp crack, coil hum'
    }),
    // ---- round 5 launchers (game/launchers.js; Blender models in fam_weapons.py). They take NO mods (noMods), drop from
    // robots from campaign level 14 on (core/gunlevel.js), and use rocket ammo (ammo: 'rocket'): one pool for both,
    // dropped only by soldiers (rocket ammo director). magRoll: the magazine is rolled per drop. damage = direct hit,
    // splash = blast at the centre (x (1 - d/R)^exponent, x0.5 behind cover), self damage like a frag (35% capped at 35).
    hothead: W({
      // rapid-fire elemental launcher: 0.5 s between rockets, 3-5 per cassette; element per drop (IB.LAUNCHER_ELEMENTS)
      id: 'hothead', name: 'RL-3 Hothead', cls: 'rocket', slot: 5, fire: 'rocket', launcher: 'elemental', ammo: 'rocket', ammoPer: 1,
      noMods: true, elements: true, damage: 170, splash: 190, radius: 4.5, exponent: 0.5, rpm: 120, spreadHip: 0.7, spreadAim: 0.15,
      recoil: 3.4, recoilH: 0.5, reload: 3.2, mag: 3, magRoll: [3, 5], reserve: 0, unlock: 0, speed: 42, projRadius: 0.12, life: 2.4,
      selfMul: 0.35, selfCap: 35, knockback: 7, moveMul: 0.92, aimZoom: 0.8, coreMul: 1,
      blurb: 'Rapid-fire rockets. Each one carries its element.', sound: 'thump launch, hiss trail, boom on hit'
    }),
    murmur: W({
      // homing salvo: locks up to 5 robots (or spots) in front, 6 missiles split over the locks; 2 rockets a salvo
      id: 'murmur', name: 'ML-6 Murmur', cls: 'rocket', slot: 5, fire: 'rocket', launcher: 'homing', ammo: 'rocket', ammoPer: 2,
      noMods: true, damage: 36, splash: 58, radius: 3.0, exponent: 0.5, missiles: 6, missilesLegend: 8, locks: 5, lockRange: 60, lockCone: 26,
      rpm: 60, spreadHip: 0.5, spreadAim: 0.2, recoil: 4.2, recoilH: 0.6, reload: 3.4, mag: 2, magRoll: [2, 4], reserve: 0, unlock: 0,
      speed: 30, turn: 6.5, projRadius: 0.1, life: 3.2, selfMul: 0.35, selfCap: 35, knockback: 4, moveMul: 0.9, aimZoom: 0.8, coreMul: 1,
      blurb: 'Locks up to 5 targets and fires 6 homing missiles.', sound: 'servo chirps, rippled launch, six booms'
    })
  };
  /* Hothead elements: none (plain rocket), Blast (bigger blast + bomblets), Volt (shock over time + arcs to robots
     nearby), Acid (acid over time + an acid pool). weight = drop odds; splashMul / radiusMul on the blast; dot = share
     of the blast damage dealt again over dur seconds; colour of the rocket, its trail and the canister glow. */
  var LAUNCHER_ELEMENTS = {
    none: { id: 'none', name: '', weight: 34, color: '#FFB21E', splashMul: 1, radiusMul: 1 },
    boom: { id: 'boom', name: 'Blast', weight: 22, color: '#FF6A2A', splashMul: 1.1, radiusMul: 1.3, bomblets: 3, bombletMul: 0.25, bombletR: 1.6 },
    shock: { id: 'shock', name: 'Volt', weight: 22, color: '#5FC2FF', splashMul: 0.85, radiusMul: 1, dot: 0.4, dur: 3, arcs: 3, arcRange: 6, arcMul: 0.35 },
    acid: { id: 'acid', name: 'Acid', weight: 22, color: '#7BE34A', splashMul: 0.85, radiusMul: 1, dot: 0.5, dur: 5, pool: 2.0, poolLife: 5 }
  };
  IB.LAUNCHER_ELEMENTS = LAUNCHER_ELEMENTS;

  // Global weapon feel rules (5.2, 5.4).
  var WEAPON_RULES = {
    moveSpreadMul: 1.5, airSpreadMul: 2.0, firstShotRest: 0.4, firstShotMul: 0.25,
    recoilClimbShots: 6, recoilRecover: 12, draw: 0.3, holster: 0.2, aimMoveMul: 0.7,
    shoveDamage: 20, ammoDropChance: 0.2, meleeSecondaryMul: 0.6, lungeRange: 3.2, lungeAngle: 25,
    lungeDist: 1.2, meleeHitStop: 0.035
  };

  var ORDER = ['pip', 'handcannon', 'twintap', 'buzz', 'whisk', 'hornet', 'rivet', 'triplet', 'longtom',
    'brick', 'needle', 'cancannon', 'frag', 'popflash', 'dagger', 'nunchucks', 'katana', 'eaxe', 'scrapper', 'vanguard', 'thunder',
    'railspike', 'hothead', 'murmur'];
  // the four melee weapons in unlock order (struck with V)
  var MELEE = ['dagger', 'nunchucks', 'katana', 'eaxe'];

  IB.WEAPONS = WEAPONS;
  IB.WEAPON_ORDER = ORDER;
  IB.MELEE_WEAPONS = MELEE;
  IB.WEAPON_RULES = WEAPON_RULES;
  IB.WEAPON_CLASSES = ['pistol', 'smg', 'rifle', 'sniper', 'shotgun', 'rocket', 'melee'];
  IB.GLB_WEAPON_NAMES = ORDER.map(function (id) { return 'WPN_' + id.toUpperCase(); });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
