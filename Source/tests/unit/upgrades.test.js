'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/saves', 'core/levelgen']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const U = IB.Upgrades;
const near = (a, b, m) => assert.ok(Math.abs(a - b) < 1e-9, `${m || ''} expected ${b}, got ${a}`);

test('card table (5.11)', () => {
  const rows = [
    ['dmg', 'Weapon', 'Heavy Slugs', 6, 40], ['reload', 'Weapon', 'Quick Hands', 4, 30], ['recoil', 'Weapon', 'Steady Grip', 4, 30],
    ['spread', 'Weapon', 'Tight Choke', 4, 30], ['mag', 'Weapon', 'Deep Mags', 4, 35], ['core', 'Weapon', 'Core Finder', 4, 40],
    ['crit', 'Weapon', 'Targeting Chip', 5, 45], ['blast', 'Weapon', 'Blast Wrap', 3, 45], ['edge', 'Weapon', 'Edge Hone', 4, 35],
    ['hp', 'Chassis', 'Armor Plating', 6, 35], ['regen', 'Chassis', 'Nanite Welders', 3, 50], ['speed', 'Chassis', 'Servo Legs', 4, 35],
    ['jump', 'Chassis', 'Spring Boots', 3, 40], ['leech', 'Chassis', 'Salvage Protocol', 3, 45], ['magnet', 'Module', 'Gem Magnet', 3, 25],
    ['press', 'Module', 'Gem Press', 5, 50], ['cans', 'Module', 'Spare Cans', 3, 40], ['flash', 'Module', 'Flash Shield', 2, 25],
    ['stamina', 'Module', 'Sprint Cells', 3, 25]
  ];
  assert.deepEqual(IB.UPGRADES.map((u) => [u.id, u.cat, u.name, u.max, u.base]), rows);
  for (const u of IB.UPGRADES) assert.match(u.effect, /\d/, u.id + ' effect has a number');
});

test('cost formula at each level', () => {
  assert.equal(U.round5(202.5), 205); assert.equal(U.round5(67.5), 70); assert.equal(U.round5(101.25), 100); assert.equal(U.round5(12), 10);
  assert.deepEqual([0, 1, 2, 3, 4, 5].map((l) => U.cost('dmg', l)), [40, 60, 90, 135, 205, 305]);
  assert.deepEqual([0, 1, 2, 3].map((l) => U.cost('reload', l)), [30, 45, 70, 100]);
  assert.deepEqual([0, 1].map((l) => U.cost('flash', l)), [25, 40]);
  assert.equal(U.cost('dmg', 6), null, 'no price at max');
  for (const u of IB.UPGRADES) {
    for (let l = 0; l < u.max; l++) {
      const c = U.cost(u.id, l);
      assert.equal(c, Math.round(u.base * Math.pow(1.5, l) / 5) * 5);
      assert.equal(c % 5, 0);
    }
    assert.equal(U.cost(u.id, u.max), null);
  }
});

test('three distinct cards, never at max', () => {
  const rng = IB.RNG.mulberry32(7);
  for (let i = 0; i < 2000; i++) {
    const owned = {};
    for (const u of IB.UPGRADES) owned[u.id] = Math.floor(rng() * (u.max + 1));
    const cards = U.draw(owned, rng);
    const open = IB.UPGRADES.filter((u) => owned[u.id] < u.max).length;
    assert.equal(cards.length, Math.min(3, open));
    assert.equal(new Set(cards).size, cards.length);
    for (const id of cards) assert.ok(owned[id] < IB.UPGRADE_BY_ID[id].max, id + ' offered at max');
  }
  const allMax = {};
  for (const u of IB.UPGRADES) allMax[u.id] = u.max;
  assert.deepEqual(U.draw(allMax, rng), []);
  allMax.hp = 2; allMax.speed = 0;
  assert.deepEqual(U.draw(allMax, rng).sort(), ['hp', 'speed']);
  assert.equal(U.draw({}, rng).length, 3);
  assert.equal(U.draw({}, rng, 5).length, 5);
  assert.deepEqual(U.draw({}, IB.RNG.mulberry32(99)), U.draw({}, IB.RNG.mulberry32(99)), 'deterministic per seed');
});

test('reroll cost increments', () => {
  assert.deepEqual([0, 1, 2, 3].map(U.rerollCost), [10, 20, 30, 40]);
});

test('effects applied correctly', () => {
  assert.equal(U.magSize(30, 0), 30); assert.equal(U.magSize(30, 1), 36); assert.equal(U.magSize(30, 2), 42);
  assert.equal(U.magSize(12, 1), 15); assert.equal(U.magSize(1, 4), 2); assert.equal(U.magSize(5, 3), 8);
  assert.equal(U.magSize(Infinity, 2), Infinity);
  const z = U.effects({});
  assert.deepEqual([z.dmgLevel, z.reloadMul, z.recoilMul, z.spreadMul, z.maxHp, z.regen, z.speedMul, z.jumpMul, z.doubleJump, z.leech,
    z.magnetRadius, z.pressLevel, z.extraCans, z.flashMul, z.staminaMul, z.critLevel, z.coreLevel, z.blastLevel, z.meleeMul],
  [0, 1, 1, 1, 100, 0, 1, 1, false, 0, 2.5, 0, 0, 1, 1, 0, 0, 0, 1]);
  const e = U.effects({ dmg: 2, reload: 2, recoil: 4, spread: 3, mag: 1, core: 1, crit: 2, blast: 3, edge: 2, hp: 6, regen: 3,
    speed: 4, jump: 3, leech: 2, magnet: 3, press: 5, cans: 3, flash: 2, stamina: 3 });
  assert.equal(e.dmgLevel, 2); near(e.reloadMul, 1 / 1.3); near(e.recoilMul, 0.4); near(e.spreadMul, 0.64);
  near(e.magMul, 1.2); assert.equal(e.coreLevel, 1); assert.equal(e.critLevel, 2); near(e.critChance, 0.12);
  assert.equal(e.blastLevel, 3); near(e.meleeMul, 1.4); assert.equal(e.maxHp, 220); near(e.regen, 4.5);
  assert.equal(e.regenDelay, 3); near(e.speedMul, 1.32); near(e.jumpMul, 1.45); near(e.jumpVelMul, Math.sqrt(1.45));
  assert.equal(e.doubleJump, true); assert.equal(e.leech, 6); near(e.magnetRadius, 6.25); assert.equal(e.pressLevel, 5);
  assert.equal(e.extraCans, 3); near(e.flashMul, 0.4); near(e.staminaMul, 1.75);
  assert.equal(U.effects({ jump: 2 }).doubleJump, false);
});

test('card text shows current to next', () => {
  assert.equal(U.cardText('dmg', 1).text, 'Damage 115% to 130%');
  assert.deepEqual([U.cardText('dmg', 1).from, U.cardText('dmg', 1).to], ['115%', '130%']);
  assert.equal(U.cardText('dmg', 0).effect, '+15% weapon damage');
  assert.equal(U.cardText('hp', 0).text, 'Max health 100 to 120');
  assert.equal(U.cardText('recoil', 1).text, 'Recoil 85% to 70%');
  assert.equal(U.cardText('regen', 1).text, 'Repair 1.5 hp/s to 3 hp/s');
  assert.equal(U.cardText('magnet', 0).text, 'Pickup range 2.5 m to 3.75 m');
  assert.equal(U.cardText('jump', 2).text, 'Jump height 130% to 145% + double jump');
  assert.equal(U.cardText('dmg', 6).maxed, true);
  assert.equal(U.cardText('dmg', 6).text, 'Damage 190% (max)');
  for (const u of IB.UPGRADES) for (let l = 0; l <= u.max; l++) assert.ok(U.cardText(u.id, l).text.length > 0);
});
