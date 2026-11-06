'use strict';
// Skill tree, player level, respec, loadout and per-level enemy tempo (src/core/skills.js, src/core/loadout.js,
// src/data/skills.js, IB.Damage.enemyTempo).
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/skills', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/skills', 'core/loadout', 'core/saves']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const S = IB.Skills;

const buyAll = (sk, h, ids) => ids.reduce((acc, id) => { const n = S.buy(acc, h, id); assert.ok(n, 'buy ' + id + ' ' + JSON.stringify(S.canBuy(acc, h, id))); return n; }, sk || {});
const treeCost = (filter) => IB.SKILLS.filter(filter || (() => true)).reduce((n, s) => n + s.max * s.cost, 0);

test('data: 12-16 skills, valid tiers, 3-rank skills, 1-rank specials, exactly two capstones', () => {
  assert.ok(IB.SKILLS.length >= 12 && IB.SKILLS.length <= 16, String(IB.SKILLS.length));
  const ids = new Set();
  IB.SKILLS.forEach((s) => {
    assert.ok(!ids.has(s.id), 'unique ' + s.id); ids.add(s.id);
    assert.ok(IB.SKILL_TIERS[s.tier - 1], 'tier ' + s.id);
    assert.equal(s.max, s.ranks.length);
    if (s.kind === 'rank') assert.equal(s.max, 3, s.id + ' has 3 ranks');
    else assert.equal(s.max, 1, s.id + ' is a 1-rank skill');
    assert.ok(s.ranks.every((v, i) => i === 0 || v > s.ranks[i - 1]), s.ranks.join());
  });
  const caps = IB.SKILLS.filter((s) => s.kind === 'capstone');
  assert.equal(caps.length, 2);
  assert.ok(caps.every((s) => s.tier === IB.SKILL_TIERS.length && s.group === 'capstone'));
  assert.ok(IB.SKILLS.some((s) => s.kind === 'special'));
  assert.deepEqual(IB.SKILL_TIERS.map((t) => t.gate), [0, 3, 6, 9, 13]);
});

test('economy: 22 points from levels 1-17 only, the last one on level 17', () => {
  // the schedule documented in data/skills.js
  const after = [0, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 22];
  for (let L = 0; L <= 17; L++) assert.equal(S.earned(L), after[L], 'after level ' + L);
  assert.equal(S.totalPoints(), 22);
  for (let L = 18; L <= 60; L++) assert.equal(S.earned(L), 22, 'nothing after level 17 (' + L + ')');
  assert.ok(S.earned(17) > S.earned(16), 'level 17 pays the final point');
  assert.equal(S.earned(-3), 0); assert.equal(S.earned(NaN), 0); assert.equal(S.earned('17'), 0);
  // points are never enough for everything: not the whole tree, not even every normal skill
  assert.equal(treeCost(), 43);
  assert.equal(treeCost((s) => s.kind !== 'capstone'), 33);
  assert.ok(treeCost((s) => s.kind !== 'capstone') > S.totalPoints());
});

test('available points are derived from progress, never stored; buying is the only way to spend them', () => {
  let sk = {};
  assert.equal(S.available(sk, 0), 0);
  assert.equal(S.buy(sk, 0, 'overboard'), null, 'no points before the first clear');
  sk = buyAll(sk, 1, ['overboard', 'overboard']);
  assert.equal(S.available(sk, 1), 0);
  assert.equal(S.buy(sk, 1, 'overboard'), null);
  assert.equal(S.canBuy(sk, 1, 'overboard').reason, 'points');
  assert.equal(S.available(sk, 2), 1, 'the next clear pays one more');
  // buy() never mutates its input
  const before = JSON.stringify(sk); S.buy(sk, 5, 'overboard'); assert.equal(JSON.stringify(sk), before);
  // ranks stop at max
  sk = buyAll({}, 5, ['overboard', 'overboard', 'overboard']);
  assert.equal(S.canBuy(sk, 5, 'overboard').reason, 'max');
});

test('random players can never spend more than they earned, and every reachable tree validates', () => {
  let seed = 7;
  const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
  for (let run = 0; run < 300; run++) {
    let sk = {};
    for (let h = 1; h <= 20; h++) {
      for (let tries = 0; tries < 40; tries++) {
        const s = IB.SKILLS[Math.floor(rnd() * IB.SKILLS.length)];
        const n = S.buy(sk, h, s.id); if (n) sk = n;
      }
      assert.ok(S.spent(sk) <= S.earned(h), 'run ' + run + ' level ' + h);
      assert.ok(S.validate(sk, h).ok, JSON.stringify(S.validate(sk, h)));
      assert.ok(!(S.rank(sk, 'lightningrod') && S.rank(sk, 'tintitan')));
    }
  }
});

test('tier gates: a tier opens once enough points are spent in the tiers above it', () => {
  const h = 17;
  let sk = buyAll({}, h, ['overboard', 'fastfingers']);
  assert.equal(S.canBuy(sk, h, 'steadyink').reason, 'tier');
  assert.equal(S.canBuy(sk, h, 'steadyink').need, 1);
  sk = buyAll(sk, h, ['tinhide']);
  assert.ok(S.tierUnlocked(sk, 2));
  assert.ok(S.canBuy(sk, h, 'steadyink').ok);
  assert.equal(S.canBuy(sk, h, 'heavyink').reason, 'tier', 'tier III needs 6');
  sk = buyAll(sk, h, ['steadyink', 'scrapmagnet', 'secondwind']);
  assert.ok(S.canBuy(sk, h, 'electrify').ok);
  assert.equal(S.canBuy(sk, h, 'overclock').reason, 'tier', 'tier IV needs 9');
  sk = buyAll(sk, h, ['heavyink', 'electrify', 'coredump']);
  assert.ok(S.canBuy(sk, h, 'closecall').ok);
  assert.equal(S.canBuy(sk, h, 'tintitan').reason, 'tier', 'capstones need 13');
  assert.equal(S.spentAbove(sk, 5), 9);
  // a hand-made tree that skips a gate is invalid
  assert.ok(!S.validate({ heavyink: 1 }, 17).ok);
  assert.ok(!S.validate({ overboard: 3, closecall: 1 }, 17).ok);
});

test('capstones: one only, by rule and by budget; first affordable after the level 15 boss', () => {
  const route = ['overboard', 'overboard', 'overboard', 'fastfingers', 'fastfingers', 'fastfingers', 'tinhide', 'tinhide', 'tinhide',
    'steadyink', 'steadyink', 'steadyink', 'scrapmagnet'];   // 13 points: every tier is open
  const sk = buyAll({}, 17, route);
  assert.ok(S.tierUnlocked(sk, 5));
  const rod = buyAll(sk, 17, ['lightningrod']);
  assert.equal(S.canBuy(rod, 17, 'tintitan').reason, 'exclusive');
  assert.equal(S.canBuy(rod, 99, 'tintitan').reason, 'exclusive', 'more points do not help');
  // budget: the cheapest way to own both is gate + both costs, more than the whole campaign pays
  const caps = IB.SKILLS.filter((s) => s.kind === 'capstone');
  const gate = IB.SKILL_TIERS[4].gate;
  assert.ok(gate + caps[0].cost + caps[1].cost > S.totalPoints());
  assert.ok(gate + caps[0].cost <= S.totalPoints());
  // the earliest clear that can afford one capstone is level 15
  const first = [...Array(18).keys()].find((L) => S.earned(L) >= gate + caps[0].cost);
  assert.equal(first, 15);
  assert.ok(!S.validate({ overboard: 3, fastfingers: 3, tinhide: 3, steadyink: 3, scrapmagnet: 1, lightningrod: 1, tintitan: 1 }, 99).ok);
});

test('respec: cost scales with progress (40% of EXPECTED_INCOME), never free, about half a real level of gems', () => {
  const table = { 1: 25, 2: 30, 5: 60, 8: 90, 10: 110, 15: 175, 17: 200, 20: 240 };
  for (const L in table) assert.equal(S.respecCost(+L), table[L], 'level ' + L);
  assert.equal(S.respecCost(0), 25);
  let prev = 0;
  for (let L = 1; L <= 20; L++) {
    const c = S.respecCost(L), inc = IB.Gems.levelIncome(L).total;
    assert.ok(c >= prev, 'monotonic'); prev = c;
    assert.equal(c % 5, 0);
    assert.ok(c / inc >= 0.3 && c / inc <= 0.7, 'level ' + L + ': ' + c + ' vs ' + inc);
  }
  const slot = { highest: 8, gems: 200, skills: buyAll({}, 8, ['overboard', 'overboard', 'fastfingers']) };
  const r = S.respec(slot);
  assert.deepEqual(r, { ok: true, cost: 90 });
  assert.equal(slot.gems, 110); assert.deepEqual(slot.skills, {});
  assert.equal(S.available(slot.skills, 8), S.earned(8), 'every point refunded');
  assert.equal(S.respec(slot).reason, 'empty', 'nothing to reset');
  const poor = { highest: 8, gems: 89, skills: { overboard: 1 } };
  assert.equal(S.respec(poor).reason, 'gems'); assert.equal(poor.gems, 89); assert.deepEqual(poor.skills, { overboard: 1 });
});

test('effects: every skill changes the runtime numbers it promises', () => {
  const none = S.effects({});
  assert.deepEqual([none.magMul, none.reloadMul, none.maxHpAdd, none.recoilMul, none.spreadMul, none.magnetMul, none.staminaMul, none.dmgMul,
    none.coreMul, none.rateMul, none.leech, none.dmgTakenMul, none.regen], [1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0]);
  assert.ok(!none.shock && !none.chain && !none.closeCall && !none.arc);
  const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, a + ' vs ' + b);
  near(S.effects({ overboard: 1 }).magMul, 1.1); near(S.effects({ overboard: 3 }).magMul, 1.3);
  near(S.effects({ fastfingers: 3 }).reloadMul, 1 / 1.24);
  assert.equal(S.effects({ tinhide: 2 }).maxHpAdd, 20);
  near(S.effects({ steadyink: 3 }).recoilMul, 0.7); near(S.effects({ steadyink: 3 }).spreadMul, 0.85);
  near(S.effects({ scrapmagnet: 2 }).magnetMul, 1.7);
  near(S.effects({ secondwind: 3 }).staminaMul, 1.45);
  near(S.effects({ heavyink: 3 }).dmgMul, 1.12);
  near(S.effects({ coredump: 3 }).coreMul, 1.24);
  near(S.effects({ overclock: 3 }).rateMul, 1.12);
  assert.equal(S.effects({ salvagebolts: 3 }).leech, 6);
  assert.ok(S.effects({ electrify: 1 }).shock);
  assert.ok(S.effects({ chainreaction: 1 }).chain);
  assert.ok(S.effects({ closecall: 1 }).closeCall);
  const rod = S.effects({ lightningrod: 1 });
  assert.ok(rod.shock && rod.arc); assert.equal(rod.shockMul, 1.5); assert.equal(rod.arcTargets, 2);
  const titan = S.effects({ tintitan: 1, tinhide: 3 });
  assert.equal(titan.maxHpAdd, 70); assert.equal(titan.dmgTakenMul, 0.8); assert.equal(titan.regen, 4);
  // Electrify: each hit adds 20% of itself (2..16) as shock over 2 s (x1.5 with Lightning Rod) - a small extra
  const e = S.effects({ electrify: 1 }), total = (fx, d) => S.shockDps(fx, d) * fx.shockTime;
  near(total(e, 5), 2); near(total(e, 18), 3.6); near(total(e, 160), 16);
  near(total(rod, 18), 5.4);
  for (const id of ['pip', 'buzz', 'rivet', 'needle', 'whisk']) assert.ok(total(e, IB.WEAPONS[id].damage) <= 0.25 * IB.WEAPONS[id].damage, id);
  // every skill id is read by effects(): owning it changes at least one field
  const base = JSON.stringify(none);
  IB.SKILLS.forEach((s) => assert.notEqual(JSON.stringify(S.effects({ [s.id]: 1 })), base, s.id));
  // the whole tree maxed (impossible in play) still keeps robots dangerous: under +25% damage, under 2x health
  const max = {}; IB.SKILLS.forEach((s) => { if (s.id !== 'lightningrod') max[s.id] = s.max; });
  const m = S.effects(max);
  assert.ok(m.dmgMul <= 1.15 && m.maxHpAdd <= 100);
});

test('player level: +1 per completed campaign level, capped at 20, with a rank title each', () => {
  assert.equal(S.playerLevel(0), 1);
  for (let h = 0; h <= 19; h++) assert.equal(S.playerLevel(h), h + 1);
  assert.equal(S.playerLevel(20), 20); assert.equal(S.playerLevel(45), 20);
  for (let lv = 1; lv <= 20; lv++) assert.ok(typeof S.rankTitle(lv) === 'string' && S.rankTitle(lv).length > 3, 'title ' + lv);
  assert.equal(new Set(IB.RANK_TITLES.slice(1)).size, 20, 'titles are unique');
  assert.equal(S.rankTitle(99), S.rankTitle(20));
});

test('loadout: 2 guns until level 10 is cleared, then 3; assign / pickup rules', () => {
  assert.equal(S.loadoutMax(0), 2); assert.equal(S.loadoutMax(9), 2); assert.equal(S.loadoutMax(10), 3); assert.equal(S.loadoutMax(20), 3);
  const L = IB.Loadout;
  assert.deepEqual(L.fix(['pip', 'pip', 'ghost', 'buzz', 'rivet'], ['pip', 'buzz', 'rivet'], 2), ['pip', 'buzz']);
  assert.deepEqual(L.fix([], ['rivet', 'pip', 'buzz'], 2), ['rivet', 'pip'], 'an empty loadout carries the first guns');
  assert.deepEqual(L.fixArsenal(['pip', 'nope', 'pip', 3, 'buzz']), ['pip', 'buzz']);
  // assign into an empty slot, replace, swap, take out
  assert.deepEqual(L.assign(['pip'], 2, 1, 'buzz'), ['pip', 'buzz']);
  assert.deepEqual(L.assign(['pip', 'buzz'], 2, 1, 'rivet'), ['pip', 'rivet']);
  assert.deepEqual(L.assign(['pip', 'buzz'], 2, 0, 'buzz'), ['buzz', 'pip'], 'swap');
  assert.deepEqual(L.assign(['pip', 'buzz'], 2, 1, 'buzz'), ['pip'], 'same slot again: taken out');
  assert.deepEqual(L.assign(['pip'], 2, 0, 'pip'), ['pip'], 'the last gun stays');
  assert.deepEqual(L.assign(['pip', 'buzz'], 2, 5, 'rivet'), ['pip', 'rivet'], 'slot index clamped to the limit');
  assert.deepEqual(L.assign(['pip', 'buzz'], 3, 2, 'pip'), ['buzz', 'pip'], 'moving a carried gun to the empty slot');
  // weapon stand pickups
  let r = L.pickup(['pip'], ['pip'], 2, 'buzz', 'pip');
  assert.deepEqual(r, { arsenal: ['pip', 'buzz'], loadout: ['pip', 'buzz'], slot: 1 });
  r = L.pickup(['pip', 'buzz'], ['pip', 'buzz'], 2, 'rivet', 'pip');
  assert.deepEqual(r, { arsenal: ['pip', 'buzz', 'rivet'], loadout: ['rivet', 'buzz'], slot: 0 }, 'full: replaces the gun in hand');
  r = L.pickup(['pip', 'buzz'], ['pip', 'buzz', 'rivet'], 2, 'buzz', 'pip');
  assert.deepEqual(r.loadout, ['pip', 'buzz']); assert.equal(r.slot, 1, 'already carried');
});

test('difficulty: enemy health, damage and tempo rise gently per level and are capped', () => {
  const D = IB.Damage;
  let prev = D.enemyTempo(1);
  assert.deepEqual(prev, { coolMul: 1, aimMul: 1, leadAdd: 0, tellMul: 1, speedMul: 1 });
  for (let L = 2; L <= 40; L++) {
    const t = D.enemyTempo(L);
    assert.ok(t.coolMul <= prev.coolMul && t.aimMul <= prev.aimMul && t.tellMul <= prev.tellMul, 'L' + L);
    assert.ok(t.leadAdd >= prev.leadAdd && t.speedMul >= prev.speedMul, 'L' + L);
    assert.ok(t.coolMul >= 0.75 && t.aimMul >= 0.6 && t.tellMul >= 0.85 && t.leadAdd <= 0.3 && t.speedMul <= 1.15, 'caps L' + L);
    assert.ok(D.enemyHpMul(L) > D.enemyHpMul(L - 1) && D.enemyDmgMul(L) >= D.enemyDmgMul(L - 1));
    prev = t;
  }
  // each level is only a small step
  const a = D.enemyTempo(8), b = D.enemyTempo(9);
  assert.ok(a.coolMul - b.coolMul <= 0.02 && b.speedMul - a.speedMul <= 0.01);
  assert.deepEqual(D.enemyTempo(20), D.enemyTempo(30), 'all capped by level 20');
  // robots outscale even a fully skilled player's damage: level 17 health x1.96 vs at most x1.12 gun damage
  assert.ok(D.enemyHpMul(17) > 1.7 * S.effects({ heavyink: 3 }).dmgMul);
});
