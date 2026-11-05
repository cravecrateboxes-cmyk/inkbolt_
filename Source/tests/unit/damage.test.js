'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/saves', 'core/levelgen']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const D = IB.Damage;
const W = IB.WEAPONS;

const near = (a, b, msg) => assert.ok(Math.abs(a - b) < 1e-9, (msg || '') + ` expected ${b}, got ${a}`);
const fixed = (v) => () => v;

const DISTS = [0, 10, 25, 40, 70];
// Expected body damage per bullet/pellet with no upgrades, at 0/10/25/40/70 m (5.2 falloff).
const EXPECTED = {
  pip: [18, 18, 14.4, 10.8, 10.8],
  handcannon: [55, 55, 44, 33, 33],
  twintap: [16, 16, 12.8, 9.6, 9.6],
  buzz: [11, 11, 5.5, 5.5, 5.5],
  whisk: [8, 8, 4, 4, 4],
  hornet: [14, 14, 7, 7, 7],
  rivet: [22, 22, 22, 19.8, 15.4],
  triplet: [26, 26, 26, 23.4, 18.2],
  longtom: [60, 60, 60, 54, 42],
  brick: [26, 26, 26, 23.4, 18.2],
  needle: [160, 160, 160, 160, 160],
  cancannon: [140, 140, 140, 140, 140],
  scrapper: [9, 8.1, 3.6, 3.6, 3.6]
};

test('each weapon damage at 0, 10, 25, 40, 70 m', () => {
  for (const id of Object.keys(EXPECTED)) {
    DISTS.forEach((d, i) => {
      const r = D.hit({ weapon: W[id], dist: d, zone: 'body' });
      near(r.damage, EXPECTED[id][i], `${id} @${d}m`);
      assert.equal(r.crit, false);
    });
  }
});

test('falloff curves by class', () => {
  near(D.falloff('pistol', 15), 1); near(D.falloff('pistol', 35), 0.6); near(D.falloff('pistol', 100), 0.6);
  near(D.falloff('smg', 10), 1); near(D.falloff('smg', 17.5), 0.75); near(D.falloff('smg', 25), 0.5);
  near(D.falloff('rifle', 30), 1); near(D.falloff('rifle', 45), 0.85); near(D.falloff('rifle', 60), 0.7);
  near(D.falloff('sniper', 500), 1);
  near(D.falloff('shotgun', 8), 1); near(D.falloff('shotgun', 14), 0.7); near(D.falloff('shotgun', 20), 0.4);
  near(D.falloff('rocket', 80), 1); near(D.falloff('melee', 3), 1);
});

test('Scrapper full blast is 9 pellets x 9', () => {
  assert.equal(W.scrapper.pellets, 9);
  near(D.hit({ weapon: W.scrapper, dist: 0, zone: 'body' }).damage * W.scrapper.pellets, 81);
});

test('core multipliers', () => {
  near(D.hit({ weapon: W.pip, dist: 0, zone: 'core' }).damage, 31.5);
  near(D.hit({ weapon: W.rivet, dist: 0, zone: 'core' }).damage, 38.5);
  near(D.hit({ weapon: W.needle, dist: 0, zone: 'core' }).damage, 400);
  near(D.hit({ weapon: W.longtom, dist: 0, zone: 'core' }).damage, 120);
  // Core Finder +15% core-hit damage per level
  near(D.hit({ weapon: W.pip, dist: 0, zone: 'core', coreLevel: 2 }).damage, 18 * 1.75 * 1.3);
  near(D.hit({ weapon: W.needle, dist: 0, zone: 'core', coreLevel: 4 }).damage, 160 * 2.5 * 1.6);
  // Core Finder does nothing on body hits
  near(D.hit({ weapon: W.pip, dist: 0, zone: 'body', coreLevel: 4 }).damage, 18);
});

test('Heavy Slugs levels 0 to 6', () => {
  const exp = [18, 20.7, 23.4, 26.1, 28.8, 31.5, 34.2];
  for (let l = 0; l <= 6; l++) near(D.hit({ weapon: W.pip, dist: 0, dmgLevel: l }).damage, exp[l], 'slugs ' + l);
  near(D.hit({ weapon: W.needle, dist: 0, dmgLevel: 6 }).damage, 160 * 1.9);
});

test('crit doubling with a fixed RNG', () => {
  let r = D.hit({ weapon: W.pip, dist: 0, critLevel: 1, rng: fixed(0.05) });
  assert.equal(r.crit, true); near(r.damage, 36);
  r = D.hit({ weapon: W.pip, dist: 0, critLevel: 1, rng: fixed(0.06) });
  assert.equal(r.crit, false); near(r.damage, 18);
  r = D.hit({ weapon: W.pip, dist: 0, critLevel: 5, rng: fixed(0.29) });
  assert.equal(r.crit, true);
  r = D.hit({ weapon: W.pip, dist: 0, critLevel: 0, rng: fixed(0) });
  assert.equal(r.crit, false, 'no Targeting Chip, no crit');
  // seeded rng: crit rate ~ 6% per level
  const rng = IB.RNG.mulberry32(42);
  let crits = 0;
  for (let i = 0; i < 20000; i++) if (D.hit({ weapon: W.pip, dist: 0, critLevel: 3, rng }).crit) crits++;
  assert.ok(Math.abs(crits / 20000 - 0.18) < 0.01, 'crit rate ' + crits / 20000);
});

test('blind bonus x1.25 and full formula product', () => {
  near(D.hit({ weapon: W.pip, dist: 0, blinded: true }).damage, 22.5);
  const r = D.hit({ weapon: W.buzz, dist: 25, zone: 'core', dmgLevel: 2, coreLevel: 1, critLevel: 1, rng: fixed(0), blinded: true });
  near(r.damage, 11 * 1.3 * 0.5 * 1.75 * 1.15 * 2 * 1.25);
});

test('Needle pierce: 30% less per robot passed', () => {
  near(D.hit({ weapon: W.needle, dist: 0, pierceIndex: 1 }).damage, 112);
  near(D.hit({ weapon: W.needle, dist: 0, pierceIndex: 2 }).damage, 160 * 0.49);
});

test('rocket splash at 0, 2, 4, 4.1 m and through cover', () => {
  near(D.rocketSplash(0, 0, false), 120);
  near(D.rocketSplash(2, 0, false), 120 * Math.pow(0.5, 0.7));
  near(D.rocketSplash(4, 0, false), 0);
  near(D.rocketSplash(4.1, 0, false), 0);
  near(D.rocketSplash(0, 0, true), 60);
  near(D.rocketSplash(2, 0, true), 60 * Math.pow(0.5, 0.7));
  // Blast Wrap +20% radius per level: R = 4.8 at level 1
  assert.ok(D.rocketSplash(4.1, 1, false) > 0);
  near(D.rocketSplash(2.4, 1, false), 120 * Math.pow(0.5, 0.7));
  near(D.rocketSplash(4.8, 1, false), 0);
  // direct hit: 140 + splash at 0 m
  near(D.hit({ weapon: W.cancannon, dist: 30 }).damage + D.rocketSplash(0, 0, false), 260);
});

test('frag splash, self-damage cap, knockback', () => {
  near(D.frag(0, 0, false), 150);
  near(D.frag(2.5, 0, false), 75);
  near(D.frag(5, 0, false), 0);
  near(D.frag(2.5, 0, true), 37.5);
  near(D.frag(5, 3, false), 150 * (1 - 5 / 8));
  near(D.selfDamage(150), 35);
  near(D.selfDamage(120), 35);
  near(D.selfDamage(50), 17.5);
  near(D.selfDamage(0), 0);
  for (let d = 0; d <= 5; d += 0.25) assert.ok(D.selfDamage(D.frag(d, 3, false)) <= 35);
  near(D.knockback(0, 4), 9); near(D.knockback(2, 4), 4.5); near(D.knockback(4, 4), 0); near(D.knockback(5, 4), 0);
  near(D.splash(100, 10, 5, 1, false), 50);
});

test('Pop Flash: robots blinded, player overlay', () => {
  assert.equal(D.blindDuration(false), 3.5);
  assert.equal(D.blindDuration(true), 1.5);
  assert.equal(D.flashDamage(9.9), 10); assert.equal(D.flashDamage(10.5), 0);
  let f = D.flashPlayer(0, 0, true, 1, false);
  near(f.opacity, 1); near(f.hold, 1.6); near(f.fade, 1.5);
  f = D.flashPlayer(6, 0, true, 1, false); near(f.opacity, 0.5);
  f = D.flashPlayer(0, 0, true, 1, true); near(f.opacity, 0.6);
  f = D.flashPlayer(0, 0, true, 1 - 0.3 * 2, false); near(f.hold, 1.6 * 0.4); near(f.fade, 1.5 * 0.4);
  assert.equal(D.flashPlayer(13, 0, true).opacity, 0);
  assert.equal(D.flashPlayer(5, 80, true).opacity, 0);
  assert.equal(D.flashPlayer(5, 10, false).opacity, 0);
});

test('Shieldbot shield absorption', () => {
  assert.deepEqual(D.shield(150, 100), { shieldHp: 50, through: 0 });
  assert.deepEqual(D.shield(50, 80), { shieldHp: 0, through: 30 });
  assert.deepEqual(D.shield(150, 150), { shieldHp: 0, through: 0 });
  assert.deepEqual(D.shield(0, 40), { shieldHp: 0, through: 40 });
  assert.deepEqual(D.shield(150, 75, true), { shieldHp: 0, through: 0 }, 'axe breaks shield outright');
  assert.equal(IB.ENEMIES.shieldbot.shield, 150);
});

test('boss shell and core multipliers', () => {
  near(D.bossShell(100, false, false), 25);
  near(D.bossShell(100, false, true), 25);
  near(D.bossShell(100, true, false), 150);
  near(D.bossShell(100, true, true), 250);
});

test('melee damage', () => {
  near(D.melee({ weapon: W.katana, combo: 0 }), 45);
  near(D.melee({ weapon: W.katana, combo: 1 }), 45);
  near(D.melee({ weapon: W.katana, combo: 2 }), 72);
  near(D.melee({ weapon: W.katana, combo: 0, first: false }), 27);
  near(D.melee({ weapon: W.katana, combo: 0, edgeLevel: 2 }), 63);
  near(D.melee({ weapon: W.fireaxe, combo: 0 }), 75);
  near(D.melee({ weapon: W.fireaxe, charged: true }), 150);
  near(D.melee({ weapon: W.fireaxe, charged: true, edgeLevel: 1 }), 180);
  near(D.melee({ weapon: W.fireaxe, charged: true, first: false }), 90);
  near(D.melee({ weapon: W.katana, charged: true }), 45, 'katana has no charge');
  assert.equal(D.staggers(25, 100), true);
  assert.equal(D.staggers(24, 100), false);
  assert.equal(D.staggers(1, 100, true), true);
});

test('level scaling of robot HP and damage (5.7)', () => {
  near(D.enemyHpMul(1), 1); near(D.enemyHpMul(11), 1.6); near(D.enemyHpMul(40), 3.34);
  near(D.enemyHpMul(41), 3.37); near(D.enemyHpMul(60), 3.94);
  near(D.enemyDmgMul(1), 1); near(D.enemyDmgMul(26), 2); near(D.enemyDmgMul(51), 3); near(D.enemyDmgMul(90), 3);
  assert.equal(D.attackTokens(1), 3); assert.equal(D.attackTokens(5), 4); assert.equal(D.attackTokens(20), 7);
});
