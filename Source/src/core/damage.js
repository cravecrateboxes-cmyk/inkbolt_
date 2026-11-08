/* INKBOLT - damage math (brief sections 5.2 to 5.8). Pure, no DOM. Damage values are unrounded floats. */
(function (IB) {
  'use strict';

  function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }

  // Linear ramp: 1 up to `near`, then down to `minMul` at `far`, flat beyond.
  function ramp(d, near, far, minMul) {
    if (d <= near) return 1;
    if (d >= far) return minMul;
    return 1 - (1 - minMul) * (d - near) / (far - near);
  }

  var FALLOFF = {
    pistol: [15, 35, 0.6],
    smg: [10, 25, 0.5],
    rifle: [30, 60, 0.7],
    shotgun: [8, 20, 0.4]
  };

  // 5.7: HP x(1 + 0.06(L-1)) to L40 (x3.34), then 3.34 + 0.03(L-40). Damage min(3, 1 + 0.04(L-1)).
  function enemyHpMul(L) {
    if (L <= 40) return 1 + 0.06 * (L - 1);
    return 3.34 + 0.03 * (L - 40);
  }
  function enemyDmgMul(L) { return Math.min(3, 1 + 0.04 * (L - 1)); }
  /* one robot row (data/enemies.js) at campaign level L: health, shield pool and hit damage as the runtime scales
     them (the shield grows with health; grenade / melee / dash damage with damage) */
  function enemyAt(row, L) {
    var h = enemyHpMul(L), d = enemyDmgMul(L);
    return { hp: row.hp * h, shield: (row.shieldPool ? row.shield : 0) * h, damage: row.damage * d,
      grenade: (row.grenadeDamage || 0) * d, melee: (row.meleeDamage || 0) * d, spin: (row.spinDamage || 0) * d };
  }

  /* Tempo per campaign level, on top of HP x enemyHpMul and damage x enemyDmgMul: robots fire a little more often,
     aim a little tighter, lead a moving target a little more, telegraph a little faster and move a little quicker.
     Every term reaches its cap by level 20 so the late game stays readable (tells never drop below 85%).
       L        1     5    10    15    20
       cool  1.00  0.94  0.87  0.79  0.75   (pause between volleys)
       aim   1.00  0.90  0.78  0.65  0.60   (bolt spread)
       lead  +0   +.06  +.14  +.22  +.30   (fraction of the player's velocity added to the aim lead)
       tell  1.00  0.97  0.93  0.89  0.85   (windup time)
       speed 1.00  1.03  1.07  1.11  1.15 */
  function enemyTempo(L) {
    var k = Math.max(0, (L || 1) - 1);
    return {
      coolMul: Math.max(0.75, 1 - 0.015 * k),
      aimMul: Math.max(0.6, 1 - 0.025 * k),
      leadAdd: Math.min(0.3, 0.016 * k),
      tellMul: Math.max(0.85, 1 - 0.008 * k),
      speedMul: Math.min(1.15, 1 + 0.008 * k)
    };
  }

  /* Player health per player level (LV = 1 + highest level cleared, cap 30): 100 + 9k + 0.3k^2 (k = LV - 1), so
     LV 20 has 379 base and LV 30 has 613 (+ Healthy, Tank, the vest and a shield on top). Tuned against the robots'
     pressure at the campaign level he is playing (damage x enemyDmgMul, volleys / coolMul, hits / sqrt(aimMul)):
       LV / L      1     5    10    15    20    25    30
       health    100   141   205   285   379   488   613
       pressure 1.00  1.30  1.79  2.45  3.03  3.40  3.73
     Health stays ahead of pressure and pulls further ahead late (ratio 1.0 at LV 1, ~1.15 by LV 10, ~1.25 at LV 20,
     ~1.6 at LV 30, unit tested): later levels throw more robots at once, so the margin grows with them. */
  function playerMaxHp(lv) { var k = Math.max(1, Math.min(30, lv || 1)) - 1; return Math.round(100 + 9 * k + 0.3 * k * k); }
  function enemyPressure(L) { var t = enemyTempo(L); return enemyDmgMul(L) / t.coolMul / Math.sqrt(t.aimMul); }

  // 4.4: at most 3 + floor(L/5) robots in Windup or Attack.
  function attackTokens(L) { return 3 + Math.floor(L / 5); }

  /* Overwhelm control (game/ai.js, game/game.js): a measured cap on how hard a late-level crowd can pile onto the
     player at once. Totals per level are unchanged; only how many close in at the same moment and how fast a wave
     lands.
       closeCap(L)        melee robots (Crawler, Bomber, Blade Bot) let into close range at once (5 + L/10); the rest hold a ring
                          HOLD.ringIn..ringOut m out (strafing) until a slot frees up (4 at LV 1-9, 5 at 10-19, 6 at 20+)
       crowdCap(L)        robots within CROWD_R m of the player at which the next queued spawn waits a moment (a wave
                          trickles in instead of landing all at once), never longer than SPAWN_WAIT_MAX s per robot
       sloppyAim(seq)     about 40 % of soldiers (golden-ratio sequence, so the share holds in any run of spawns) aim
                          worse: SLOPPY spread x1.9 + 0.02 and 60 % of the lead */
  var HOLD = { ringIn: 6, ringOut: 8.5 }, CROWD_R = 10, SPAWN_WAIT_MAX = 3.5, SPAWN_GAP = 0.26;
  var SLOPPY = { share: 0.4, spreadMul: 1.9, spreadAdd: 0.02, leadMul: 0.6 };
  function closeCap(L) { return 5 + Math.floor(Math.max(1, L || 1) / 10); }
  function crowdCap(L) { return 8 + Math.floor(Math.max(1, L || 1) / 6); }
  function sloppyAim(seq) { var f = (seq * 0.6180339887498949) % 1; return f < SLOPPY.share; }
  /* health director plan for the player's health fraction: cans wanted in the zone, seconds between checks and the
     ring they land in; critically hurt (< 30 %): twice as many, twice as often and closer (4-12 m, never on top) */
  var HEALTH_CRIT = 0.3;
  function healthPlan(frac) {
    var want = frac >= 0.8 ? 1 : frac >= 0.55 ? 2 : frac >= HEALTH_CRIT ? 3 : 4;
    if (frac < HEALTH_CRIT) return { want: want * 2, every: 1.25, dMin: 4, dMax: 12, critical: true };
    return { want: want, every: 2.5, dMin: 7, dMax: 22, critical: false };
  }

  function falloff(cls, d) {
    var f = FALLOFF[cls];
    return f ? ramp(d, f[0], f[1], f[2]) : 1;
  }

  /* opts: {weapon, dist, zone:'core'|'body', dmgLevel, coreLevel, critLevel, rng, blinded, pierceIndex}
     damage = base x (1 + 0.15 dmgLevel) x falloff x hitZone x crit x blind [x pierce] */
  function hit(o) {
    var w = o.weapon;
    var dmg = w.damage * (1 + 0.15 * (o.dmgLevel || 0));
    dmg *= falloff(w.cls, o.dist || 0);
    if (o.zone === 'core') dmg *= (w.coreMul || 1.75) * (1 + 0.15 * (o.coreLevel || 0));
    var crit = false;
    var chance = 0.06 * (o.critLevel || 0);
    if (chance > 0 && o.rng && o.rng() < chance) { crit = true; dmg *= 2; }
    if (o.blinded) dmg *= 1.25;
    if (o.pierceIndex) dmg *= Math.pow(w.pierceMul !== undefined ? w.pierceMul : 0.7, o.pierceIndex);
    return { damage: dmg, crit: crit };
  }

  // Generic splash: maxDmg x (1 - d/R)^exponent inside R, 0 at or beyond R, x0.5 behind cover.
  function splash(maxDmg, radius, d, exponent, covered) {
    if (!(radius > 0) || d >= radius) return 0;
    var t = 1 - Math.max(0, d) / radius;
    var dmg = maxDmg * (exponent === 0 ? 1 : Math.pow(t, exponent === undefined ? 1 : exponent));
    return covered ? dmg * 0.5 : dmg;
  }

  function blastRadius(baseR, blastLevel) { return baseR * (1 + 0.2 * (blastLevel || 0)); }

  // 5.6: 120 x (1 - d/R)^0.7 within R = 4 x (1 + 0.2 blast).
  function rocketSplash(d, blastLevel, covered) {
    return splash(120, blastRadius(4, blastLevel), d, 0.7, covered);
  }

  // 5.3: 150 at centre, linear to 0 at R = 5 x (1 + 0.2 blast).
  function frag(d, blastLevel, covered) {
    return splash(150, blastRadius(5, blastLevel), d, 1, covered);
  }

  // 5.3: Pop Flash deals a flat 10 within 10 m (radius not scaled by Blast Wrap).
  function flashDamage(d, covered) {
    if (d > 10) return 0;
    return covered ? 5 : 10;
  }

  function selfDamage(splashDmg) { return Math.min(35, 0.35 * splashDmg); }

  // Impulse speed (m/s) away from the centre: 9 at the centre, 0 at R.
  function knockback(d, R, max) {
    var m = max === undefined ? 9 : max;
    if (!(R > 0) || d >= R) return 0;
    return m * (1 - Math.max(0, d) / R);
  }

  // Robots: blinded for 3.5 s, 1.5 s when facing away.
  function blindDuration(facingAway) { return facingAway ? 1.5 : 3.5; }

  /* Player flash overlay (5.3). d metres, angleDeg between view direction and the detonation.
     Out of 12 m / beyond 70 degrees / no line of sight -> opacity 0. angleFactor = 1 - angle/70.
     flashMul from Flash Shield (1 - 0.3 L) scales hold and fade; reduceFlash caps opacity at 0.6. */
  function flashPlayer(d, angleDeg, los, flashMul, reduceFlash) {
    if (!los || d > 12 || angleDeg > 70) return { opacity: 0, hold: 0, fade: 0 };
    var mul = flashMul === undefined ? 1 : flashMul;
    var opacity = clamp01((1 - d / 12) * (1 - Math.max(0, angleDeg) / 70));
    if (reduceFlash) opacity = Math.min(0.6, opacity);
    return { opacity: opacity, hold: 1.6 * opacity * mul, fade: 1.5 * mul };
  }

  /* Shieldbot: frontal damage goes into shield HP first. breaks=true (Fire Axe) destroys the shield
     outright; that hit itself is spent on the shield (through 0). */
  function shield(shieldHp, dmg, breaks) {
    if (shieldHp <= 0) return { shieldHp: 0, through: dmg };
    if (breaks) return { shieldHp: 0, through: 0 };
    if (dmg <= shieldHp) return { shieldHp: shieldHp - dmg, through: 0 };
    return { shieldHp: 0, through: dmg - shieldHp };
  }

  // Bosses: closed shell x0.25; open core x1.5 (sniper x2.5).
  function bossShell(dmg, open, isSniper) {
    if (!open) return dmg * 0.25;
    return dmg * (isSniper ? 2.5 : 1.5);
  }

  /* opts: {weapon, combo (0..2), charged, edgeLevel, first (default true), blinded}
     Katana third hit (combo 2) x comboMul (1.6); axe charged -> weapon.charged (150);
     secondary targets x0.6; Edge Hone +20% per level. */
  function melee(o) {
    var w = o.weapon;
    var dmg = w.damage;
    if (o.charged && w.charged) dmg = w.charged;
    else if (w.combo > 1 && o.combo >= w.combo - 1) dmg *= w.comboMul;
    if (o.first === false) dmg *= 0.6;
    dmg *= 1 + 0.2 * (o.edgeLevel || 0);
    if (o.blinded) dmg *= 1.25;
    return dmg;
  }

  // 4.4 Stagger: one hit of at least 25% max HP, or a charged melee hit.
  function staggers(dmg, maxHp, charged) { return !!charged || dmg >= 0.25 * maxHp; }

  IB.Damage = {
    enemyHpMul: enemyHpMul, enemyDmgMul: enemyDmgMul, enemyAt: enemyAt, enemyTempo: enemyTempo, playerMaxHp: playerMaxHp, enemyPressure: enemyPressure, attackTokens: attackTokens, falloff: falloff,
    closeCap: closeCap, crowdCap: crowdCap, sloppyAim: sloppyAim, healthPlan: healthPlan, HOLD: HOLD, CROWD_R: CROWD_R, SPAWN_WAIT_MAX: SPAWN_WAIT_MAX, SPAWN_GAP: SPAWN_GAP, SLOPPY: SLOPPY, HEALTH_CRIT: HEALTH_CRIT,
    hit: hit, splash: splash, blastRadius: blastRadius, rocketSplash: rocketSplash, frag: frag,
    flashDamage: flashDamage, selfDamage: selfDamage, knockback: knockback, blindDuration: blindDuration,
    flashPlayer: flashPlayer, shield: shield, bossShell: bossShell, melee: melee, staggers: staggers
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
