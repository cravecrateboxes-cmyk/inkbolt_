/* INKBOLT - weapon table (brief section 5.2, 5.3, 5.4, 5.5, 5.6). Pure data, no DOM.
   Units: damage per bullet / pellet / swing; rpm shots per minute (burst weapons: see below);
   cycle seconds between shots or bursts; spread = cone half-angle in degrees; recoil degrees;
   reload seconds; ranges metres. Fields the brief leaves blank are 0 (see notes per entry). */
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
    return w;
  }

  var WEAPONS = {
    pip: W({
      id: 'pip', name: 'Pip', cls: 'pistol', slot: 1, fire: 'semi', damage: 18, rpm: 300,
      spreadHip: 0.8, spreadAim: 0.3, recoil: 1.2, recoilH: 0.3, reload: 1.1, mag: 12, reserve: Infinity,
      unlock: 1, sound: 'click transient, 2.4 kHz noise snap, short bright tail'
    }),
    handcannon: W({
      id: 'handcannon', name: 'Hand Cannon', cls: 'pistol', slot: 1, fire: 'semi', action: 'revolver',
      damage: 55, rpm: 110, spreadHip: 0.5, spreadAim: 0.15, recoil: 4.0, recoilH: 0.8, reload: 2.2,
      mag: 6, reserve: 36, unlock: 8, sound: '120 to 50 Hz thump, noise crack, metal ring'
    }),
    twintap: W({
      // Brief gives 220 bursts/min only; rpm keeps that figure (bursts), cycle = 60/220.
      // burstGap (time between the 2 rounds of one burst) is not in the brief: 0.06 s chosen.
      id: 'twintap', name: 'Twin Tap', cls: 'pistol', slot: 1, fire: 'burst', damage: 16, burst: 2,
      rpm: 220, cycle: 60 / 220, burstGap: 0.06, spreadHip: 1.0, spreadAim: 0.4, recoil: 0.9, recoilH: 0,
      reload: 1.3, mag: 16, reserve: 96, unlock: 16, sound: 'double tick, tight snap, slide clack'
    }),
    buzz: W({
      id: 'buzz', name: 'Buzz', cls: 'smg', slot: 2, fire: 'auto', damage: 11, rpm: 900,
      spreadHip: 2.2, spreadAim: 1.2, recoil: 0.5, recoilH: 0.4, reload: 1.6, mag: 30, reserve: 180,
      unlock: 3, sound: 'fast buzz noise, low rattle, casing ticks'
    }),
    whisk: W({
      id: 'whisk', name: 'Whisk', cls: 'smg', slot: 2, fire: 'auto', damage: 8, rpm: 1100,
      spreadHip: 3.2, spreadAim: 2.0, recoil: 0.35, recoilH: 0.6, reload: 1.4, mag: 40, reserve: 240,
      unlock: 10, sound: 'thin high buzz, tin rattle'
    }),
    hornet: W({
      id: 'hornet', name: 'Hornet', cls: 'smg', slot: 2, fire: 'auto', damage: 14, rpm: 750,
      spreadHip: 1.4, spreadAim: 0.6, recoil: 0.6, recoilH: 0.25, reload: 1.8, mag: 32, reserve: 192,
      unlock: 17, sound: 'sharp snap, mid thud, bolt clack'
    }),
    rivet: W({
      id: 'rivet', name: 'Rivet', cls: 'rifle', slot: 3, fire: 'auto', damage: 22, rpm: 600,
      spreadHip: 1.4, spreadAim: 0.4, recoil: 0.9, recoilH: 0.3, reload: 2.0, mag: 30, reserve: 180,
      unlock: 5, sound: 'punchy crack, low body, rivet-gun clank'
    }),
    triplet: W({
      // rpm 1000 is the in-burst rate (burstGap = 0.06 s); cycle 0.32 s between bursts.
      id: 'triplet', name: 'Triplet', cls: 'rifle', slot: 3, fire: 'burst', damage: 26, burst: 3,
      rpm: 1000, cycle: 0.32, burstGap: 60 / 1000, spreadHip: 1.0, spreadAim: 0.25, recoil: 0.8, recoilH: 0,
      reload: 2.2, mag: 24, reserve: 144, unlock: 11, sound: 'three cracks, rising pitch, burst-end clack'
    }),
    longtom: W({
      id: 'longtom', name: 'Long Tom', cls: 'rifle', slot: 3, fire: 'semi', damage: 60, rpm: 240,
      spreadHip: 0.6, spreadAim: 0.05, recoil: 2.8, recoilH: 0.4, reload: 2.4, mag: 10, reserve: 60,
      unlock: 13, aimZoom: 0.67, coreMul: 2.0, sound: 'heavy crack, long tail, bolt slap'
    }),
    brick: W({
      id: 'brick', name: 'Brick', cls: 'rifle', slot: 3, fire: 'auto', damage: 26, rpm: 500,
      spreadHip: 2.0, spreadAim: 0.8, recoil: 1.1, recoilH: 0.5, reload: 3.4, mag: 60, reserve: 240,
      unlock: 18, moveMul: 0.9, sound: 'deep chug, metal stomp, belt rattle'
    }),
    needle: W({
      // Scope: FOV = base / 3.5 (aimZoom = 1/3.5), toggles in 0.22 s; pierce 2, each pierce -30%.
      id: 'needle', name: 'Needle', cls: 'sniper', slot: 4, fire: 'bolt', damage: 160, rpm: 45,
      spreadHip: 4.0, spreadAim: 0, recoil: 6.0, recoilH: 0, reload: 3.0, mag: 5, reserve: 25,
      unlock: 9, aimZoom: 1 / 3.5, scopeZoom: 3.5, scopeTime: 0.22, sway: 0.15, swayHz: 0.5,
      steadyTime: 2, steadyCooldown: 1, pierce: 2, pierceMul: 0.7, coreMul: 2.5,
      sound: 'huge crack, 0.6 s echo tail, bolt cycle'
    }),
    cancannon: W({
      // 140 direct + splash 120 x (1 - d/4)^0.7 within 4 m; projectile 28 m/s, r 0.15 m, 2 s life.
      id: 'cancannon', name: 'Can Cannon', cls: 'rocket', slot: 5, fire: 'projectile', damage: 140,
      rpm: 40, spreadHip: 0.3, spreadAim: 0.3, recoil: 5.0, recoilH: 0, reload: 2.6, mag: 1, reserve: 8,
      unlock: 12, splash: 120, radius: 4, exponent: 0.7, speed: 28, projRadius: 0.15, life: 2,
      gravity: 0, knockback: 9, selfMul: 0.35, selfCap: 35, shakeDeg: 1.5, shakeRange: 6,
      sound: 'whoosh launch, hiss trail loop, boom on hit'
    }),
    frag: W({
      id: 'frag', name: 'Frag Can', cls: 'grenade', slot: 'Q', pickSlot: 7, fire: 'throw', damage: 150,
      cycle: 0.45, rpm: 60 / 0.45, spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0,
      unlock: 4, splash: 150, radius: 5, exponent: 1, fuse: 2.2, carry: 3, speed: 18, throwUp: 4,
      restitution: 0.35, selfMul: 0.35, selfCap: 35, sound: 'tin pin pop, bounce clinks, boom'
    }),
    popflash: W({
      // 10 damage within 10 m plus Blinded 3.5 s (1.5 s facing away); bosses: 1.0 s stagger, 20 s immunity.
      id: 'popflash', name: 'Pop Flash', cls: 'grenade', slot: 'Q', pickSlot: 8, fire: 'throw', damage: 10,
      cycle: 0.45, rpm: 60 / 0.45, spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0,
      unlock: 6, splash: 10, radius: 10, exponent: 0, fuse: 1.5, carry: 2, speed: 18, throwUp: 4,
      restitution: 0.35, blind: 3.5, blindAway: 1.5, bossStagger: 1.0, bossImmune: 20,
      playerRange: 12, playerAngle: 70, playerHold: 1.6, playerFade: 1.5, duckDb: 12,
      sound: 'pin pop, sharp bang, high ring'
    }),
    katana: W({
      id: 'katana', name: 'Katana', cls: 'melee', slot: 6, fire: 'melee', damage: 45, cycle: 0.38,
      rpm: 60 / 0.38, spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0, unlock: 7,
      arc: 100, range: 2.6, windup: 0.08, active: 0.10, recovery: 0.20, combo: 3, comboMul: 1.6,
      comboWindow: 0.5, comboLunge: 2, blockMul: 0.4, parryWindow: 0.2, parryMul: 2,
      charged: 0, chargeTime: 0, knockback: 0, sound: 'air swish, steel ring on hit'
    }),
    fireaxe: W({
      id: 'fireaxe', name: 'Fire Axe', cls: 'melee', slot: 6, fire: 'melee', damage: 75, cycle: 0.75,
      rpm: 60 / 0.75, spreadHip: 0, spreadAim: 0, recoil: 0, reload: 0, mag: 0, reserve: 0, unlock: 14,
      arc: 70, range: 2.3, windup: 0.18, active: 0.12, recovery: 0.45, combo: 1, comboMul: 1,
      charged: 150, chargeTime: 0.8, knockback: 6, breaksShield: true,
      sound: 'heavy whoosh, crunch, metal clang'
    }),
    scrapper: W({
      // Slot 9; reloads one shell at a time (0.5 s per shell). Falloff: full to 8 m, 40% at 20 m.
      id: 'scrapper', name: 'Scrapper', cls: 'shotgun', slot: 9, fire: 'pump', damage: 9, pellets: 9,
      rpm: 70, spreadHip: 6.0, spreadAim: 4.5, recoil: 3.5, recoilH: 0, reload: 0.5, reloadPerShell: true,
      mag: 6, reserve: 36, unlock: 25, sound: 'boom, pump clack'
    })
  };

  // Global weapon feel rules (5.2, 5.4).
  var WEAPON_RULES = {
    moveSpreadMul: 1.5, airSpreadMul: 2.0, firstShotRest: 0.4, firstShotMul: 0.25,
    recoilClimbShots: 6, recoilRecover: 12, draw: 0.3, holster: 0.2, aimMoveMul: 0.7,
    shoveDamage: 20, ammoDropChance: 0.2, meleeSecondaryMul: 0.6, lungeRange: 3.2, lungeAngle: 25,
    lungeDist: 1.2, meleeHitStop: 0.035
  };

  var ORDER = ['pip', 'handcannon', 'twintap', 'buzz', 'whisk', 'hornet', 'rivet', 'triplet', 'longtom',
    'brick', 'needle', 'cancannon', 'frag', 'popflash', 'katana', 'fireaxe', 'scrapper'];

  IB.WEAPONS = WEAPONS;
  IB.WEAPON_ORDER = ORDER;
  IB.WEAPON_RULES = WEAPON_RULES;
  IB.WEAPON_CLASSES = ['pistol', 'smg', 'rifle', 'sniper', 'rocket', 'melee'];
  IB.GLB_WEAPON_NAMES = ORDER.map(function (id) { return 'WPN_' + id.toUpperCase(); });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
