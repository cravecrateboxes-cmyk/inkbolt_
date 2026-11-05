'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/saves', 'core/levelgen']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const G = IB.Gems;

test('gem values', () => {
  assert.deepEqual(G.VALUES, { chip: 1, shard: 5, core: 25 });
  assert.equal(G.value({ chip: 3, shard: 2, core: 1 }), 38);
});

test('each robot drop at L1, L10, L20', () => {
  // totals: Shard-tier robots (shieldbot, bruiser, binhive) gain floor(L/4) Chips
  const exp = {
    crawler: [1, 1, 1], gunner: [2, 2, 2], bomber: [2, 2, 2], tosser: [3, 3, 3], drone: [3, 3, 3],
    shieldbot: [5, 7, 10], bruiser: [8, 10, 13], binhive: [10, 12, 15]
  };
  for (const [id, t] of Object.entries(exp)) {
    [1, 10, 20].forEach((L, i) => assert.equal(G.robotDrop(id, L, 0).total, t[i], `${id} L${L}`));
  }
  assert.deepEqual(G.robotDrop('bruiser', 20, 0), { chip: 8, shard: 1, core: 0, total: 13 });
  assert.deepEqual(G.robotDrop('crawler', 20, 0), { chip: 1, shard: 0, core: 0, total: 1 });
  assert.equal(G.isShardTier('shieldbot'), true); assert.equal(G.isShardTier('drone'), false);
  assert.throws(() => G.robotDrop('nope', 1, 0));
});

test('Gem Press levels', () => {
  // crawler: 10% of 1 rounds down to 0 at every level
  for (let p = 0; p <= 5; p++) assert.equal(G.robotDrop('crawler', 1, p).total, 1);
  assert.equal(G.robotDrop('gunner', 1, 4).total, 2);
  assert.equal(G.robotDrop('gunner', 1, 5).total, 3);
  assert.equal(G.robotDrop('drone', 1, 4).total, 4);
  // Shard-tier: minimum 1 extra
  assert.equal(G.robotDrop('shieldbot', 1, 1).total, 6);
  assert.equal(G.robotDrop('shieldbot', 1, 0).total, 5);
  assert.equal(G.robotDrop('shieldbot', 20, 3).total, 13);
  assert.equal(G.robotDrop('bruiser', 20, 3).total, 16);
  assert.equal(G.robotDrop('binhive', 10, 5).total, 18);
  assert.equal(G.bossDrop('compactorprime', 0).total, 180);
  assert.equal(G.bossDrop('compactorprime', 2).total, 216);
});

test('boss drops', () => {
  assert.deepEqual(['skimmer', 'dumpstertank', 'cartcolossus', 'compactorprime'].map((b) => G.bossDrop(b, 0).total), [60, 90, 120, 180]);
});

test('clear, no-death and replay bonuses', () => {
  assert.equal(G.clearBonus(1), 20);
  assert.equal(G.clearBonus(10), 65);
  assert.equal(G.clearBonus(20), 115);
  assert.equal(G.noDeathBonus(100), 25);
  assert.equal(G.noDeathBonus(18), 4);
  assert.equal(G.noDeathBonus(0), 0);
  assert.equal(G.replay(45), 22);
  assert.equal(G.replay(306), 153);
  assert.equal(G.levelIncome(10, { replay: true }).total, 153);
});

test('expected level income vs 5.10 targets', () => {
  // Estimate = robot drops from the level mix + boss + clear bonus + no-death bonus (25% of robot+boss gems).
  const actual = { 1: 42, 5: 162, 10: 306, 20: 635 };
  const withoutNoDeath = { 1: 38, 5: 138, 10: 258, 20: 531 };
  for (const L of [1, 5, 10, 20]) {
    const inc = G.levelIncome(L);
    assert.equal(inc.total, actual[L], 'L' + L);
    assert.equal(G.levelIncome(L, { noDeath: false }).total, withoutNoDeath[L], 'L' + L + ' with a death');
    const target = G.EXPECTED_INCOME[L];
    assert.ok(Math.abs(inc.total - target) / target <= 0.15, `L${L} ${inc.total} vs ${target}`);
  }
  // With deaths, L1 (38) is 15.6% under the 45 target: the no-death bonus is what lands it.
  assert.ok(Math.abs(38 - 45) / 45 > 0.15);
  assert.deepEqual(G.levelIncome(1), { robots: 18, boss: 0, earned: 18, clear: 20, noDeath: 4, total: 42 });
  assert.throws(() => G.levelIncome(33));
  assert.equal(G.levelIncome(33, { mix: { crawler: 10 }, boss: null }).total, 10 + 180 + 2);
});
