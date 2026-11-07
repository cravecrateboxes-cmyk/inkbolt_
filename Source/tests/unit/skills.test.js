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

test('data: 15 skills in 6 tiers (trunk at the bottom), 3-rank skills, 1-rank specials, two endgame skills', () => {
  assert.equal(IB.SKILLS.length, 15);
  assert.equal(IB.SKILL_TIERS.length, 6);
  const ids = new Set();
  IB.SKILLS.forEach((s) => {
    assert.ok(!ids.has(s.id), 'unique ' + s.id); ids.add(s.id);
    assert.ok(IB.SKILL_TIERS[s.tier - 1], 'tier ' + s.id);
    assert.equal(s.max, s.ranks.length);
    if (s.kind === 'rank') assert.equal(s.max, 3, s.id + ' has 3 ranks');
    else assert.equal(s.max, 1, s.id + ' is a 1-rank skill');
    assert.ok(s.ranks.every((v, i) => i === 0 || v > s.ranks[i - 1]), s.ranks.join());
    assert.ok(typeof s.text === 'string' && s.text.length > 10, 'text ' + s.id);
  });
  // the layout of the player's sketch: row by row, top (endgame) to bottom (trunk)
  const row = (t) => IB.SKILLS.filter((s) => s.tier === t).map((s) => s.id);
  assert.deepEqual(row(6), ['handyhelpers', 'chainreaction']);
  assert.deepEqual(row(5), ['tank', 'fastfingers']);
  assert.deepEqual(row(4), ['stamina', 'hydrate', 'undercover']);
  assert.deepEqual(row(3), ['hazard', 'ricochet', 'healthy']);
  assert.deepEqual(row(2), ['stream', 'electrify', 'rapid']);
  assert.deepEqual(row(1), ['overload', 'heavyink']);
  const caps = IB.SKILLS.filter((s) => s.kind === 'capstone');
  assert.equal(caps.length, 2);
  assert.ok(caps.every((s) => s.tier === IB.SKILL_TIERS.length && !s.group && s.cost === 5));
  assert.deepEqual(IB.SKILLS.filter((s) => s.kind === 'special').map((s) => s.id), ['electrify', 'stamina', 'undercover']);
  assert.deepEqual(IB.SKILL_TIERS.map((t) => t.gate), [0, 1, 3, 5, 7, 9]);
  assert.ok(IB.SKILL_TIERS[5].capstone && IB.SKILL_TIERS.slice(0, 5).every((t) => !t.capstone));
});

test('economy: 22 points from levels 1-19 only, never more; a build, not the whole tree', () => {
  // the schedule documented in data/skills.js
  const after = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 19, 20, 21, 22];
  for (let L = 0; L <= 19; L++) assert.equal(S.earned(L), after[L], 'after level ' + L);
  assert.equal(S.totalPoints(), 22);
  for (let L = 20; L <= 60; L++) assert.equal(S.earned(L), 22, 'nothing after level 19 (' + L + ')');
  assert.equal(S.earned(-3), 0); assert.equal(S.earned(NaN), 0); assert.equal(S.earned('19'), 0);
  assert.equal(treeCost(), 43);
  assert.ok(IB.SKILL_TIERS[5].gate + 10 <= S.totalPoints(), 'both endgame skills fit in a max-level build');
});

test('available points are derived from progress, never stored; buying is the only way to spend them', () => {
  let sk = {};
  assert.equal(S.available(sk, 0), 0);
  assert.equal(S.buy(sk, 0, 'overload'), null, 'no points before the first clear');
  sk = buyAll(sk, 1, ['overload', 'overload']);
  assert.equal(S.available(sk, 1), 0);
  assert.equal(S.buy(sk, 1, 'overload'), null);
  assert.equal(S.canBuy(sk, 1, 'overload').reason, 'points');
  assert.equal(S.available(sk, 2), 1, 'the next clear pays one more');
  // buy() never mutates its input
  const before = JSON.stringify(sk); S.buy(sk, 5, 'overload'); assert.equal(JSON.stringify(sk), before);
  // ranks stop at max; specials have one rank
  sk = buyAll({}, 5, ['overload', 'overload', 'overload']);
  assert.equal(S.canBuy(sk, 5, 'overload').reason, 'max');
  sk = buyAll(sk, 5, ['electrify']);
  assert.equal(S.canBuy(sk, 5, 'electrify').reason, 'max');
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
      assert.ok(S.spent(sk) <= S.totalPoints());
      assert.ok(S.validate(sk, h).ok, JSON.stringify(S.validate(sk, h)));
    }
  }
});

test('tier gates: a row opens once enough points are spent in the rows below it (1 / 3 / 5 / 7 / 9)', () => {
  const h = 19;
  assert.equal(S.canBuy({}, h, 'stream').reason, 'tier');
  assert.equal(S.canBuy({}, h, 'stream').need, 1);
  let sk = buyAll({}, h, ['overload']);
  assert.ok(S.tierUnlocked(sk, 2));
  assert.ok(S.canBuy(sk, h, 'stream').ok && S.canBuy(sk, h, 'electrify').ok && S.canBuy(sk, h, 'rapid').ok);
  assert.equal(S.canBuy(sk, h, 'hazard').reason, 'tier', 'row 3 needs 3');
  sk = buyAll(sk, h, ['electrify', 'stream']);
  assert.ok(S.canBuy(sk, h, 'hazard').ok && S.canBuy(sk, h, 'ricochet').ok && S.canBuy(sk, h, 'healthy').ok);
  assert.equal(S.canBuy(sk, h, 'undercover').reason, 'tier', 'row 4 needs 5');
  sk = buyAll(sk, h, ['healthy', 'ricochet']);
  assert.ok(S.canBuy(sk, h, 'stamina').ok && S.canBuy(sk, h, 'hydrate').ok && S.canBuy(sk, h, 'undercover').ok);
  assert.equal(S.canBuy(sk, h, 'tank').reason, 'tier', 'row 5 needs 7');
  sk = buyAll(sk, h, ['undercover', 'stamina']);
  assert.ok(S.canBuy(sk, h, 'tank').ok && S.canBuy(sk, h, 'fastfingers').ok);
  assert.equal(S.canBuy(sk, h, 'handyhelpers').reason, 'tier', 'endgame needs 9');
  assert.equal(S.spentAbove(sk, 6), 7);
  // the gate counts the rows below only
  sk = buyAll(sk, h, ['tank', 'tank']);
  assert.equal(S.spentAbove(sk, 6), 9);
  assert.equal(S.spentAbove(sk, 5), 7);
  assert.ok(S.canBuy(sk, h, 'handyhelpers').ok);
  // a hand-made tree that skips a gate is invalid
  assert.ok(!S.validate({ stream: 1 }, 19).ok);
  assert.ok(!S.validate({ overload: 2, heavyink: 2, undercover: 1 }, 19).ok);
  assert.ok(S.validate({ overload: 2, heavyink: 2, hazard: 1, undercover: 1 }, 19).ok);
});

test('endgame: both can be owned; however the points went in, the top opens and is affordable at max level', () => {
  const route = ['overload', 'overload', 'overload', 'heavyink', 'heavyink', 'electrify', 'healthy', 'healthy',
    'undercover'];   // 9 points: every row is open
  const sk = buyAll({}, 19, route);
  assert.ok(S.tierUnlocked(sk, 6));
  const both = buyAll(sk, 19, ['handyhelpers', 'chainreaction']);
  assert.ok(S.rank(both, 'handyhelpers') && S.rank(both, 'chainreaction'));
  assert.ok(S.validate(both, 19).ok);
  assert.equal(S.available(both, 19), 3);
  // a player who pours 17 points into the low rows first still reaches and buys an endgame skill at max level
  const low = IB.SKILLS.filter((s) => s.kind !== 'capstone').flatMap((s) => Array(s.max).fill(s.id)).slice(0, 17);
  const one = buyAll(buyAll({}, 19, low), 19, ['handyhelpers']);
  assert.equal(S.spent(one), 22);
  assert.equal(S.available(one, 19), 0);
  assert.equal(S.buy(one, 99, 'chainreaction'), null, 'never more than 22 points');
  // the earliest clear that can afford one is level 12
  const caps = IB.SKILLS.filter((s) => s.kind === 'capstone');
  const first = [...Array(20).keys()].find((L) => S.earned(L) >= IB.SKILL_TIERS[5].gate + caps[0].cost);
  assert.equal(first, 12);
});

test('old saves: trees with the retired skill ids are refunded in full, never crash', () => {
  const old = [
    { overboard: 3, fastfingers: 3, tinhide: 3, steadyink: 3, scrapmagnet: 1, lightningrod: 1 },
    { overboard: 2 }, { tintitan: 1, heavyink: 3 }, { closecall: 1 }, { heavyink: 3, fastfingers: 1, coredump: 2 }
  ];
  for (const sk of old) {
    const r = S.sanitize(sk, 17);
    assert.deepEqual(r.skills, {}, JSON.stringify(sk));
    assert.equal(r.reset, true);
    assert.equal(S.available(r.skills, 20), 22, 'every point back');
    assert.doesNotThrow(() => S.effects(r.skills));
  }
  // effects() of a raw old tree (before sanitize) ignores what it does not know instead of throwing
  assert.doesNotThrow(() => S.effects({ overboard: 3, heavyink: 2 }));
  assert.equal(S.effects({ overboard: 3, heavyink: 2 }).dmgMul, 1.08);
  // a valid new tree passes untouched
  assert.deepEqual(S.sanitize({ overload: 2, heavyink: 1 }, 2), { skills: { overload: 2, heavyink: 1 }, reset: false });
  // through the save loader: old ids -> empty tree, a one-time refund flag for the game's notice
  const be = IB.Saves.memoryBackend(), store = IB.Saves.create(be);
  be.setItem('inkbolt.slot1', JSON.stringify({ v: 1, id: 1, highest: 12, skills: { overboard: 3, coredump: 2, lightningrod: 1 } }));
  const slot = store.load(1);
  assert.deepEqual(slot.skills, {}); assert.equal(slot.skillsRefunded, true);
  assert.equal(S.available(slot.skills, slot.highest), S.earned(12));
  be.setItem('inkbolt.slot2', JSON.stringify({ v: 1, id: 2, highest: 12, skills: { overload: 3, heavyink: 1 } }));
  assert.equal(store.load(2).skillsRefunded, undefined, 'a valid tree raises no flag');
});

test('effects: every skill changes the runtime numbers its text promises', () => {
  const none = S.effects({});
  assert.deepEqual([none.magMul, none.dmgMul, none.rateMul, none.reloadMul, none.swapMul, none.maxHpMul, none.dmgTakenMul, none.sprintMul,
    none.staminaMul, none.staminaRechargeMul, none.pierce, none.ricochet, none.pool, none.coat, none.rogue, none.chain, none.regenPct, none.regenFlat],
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]);
  assert.ok(!none.shock && !none.cloak);
  assert.equal(S.regenRate(none, 100), 0);
  const near = (a, b, m) => assert.ok(Math.abs(a - b) < 1e-9, (m ? m + ': ' : '') + a + ' vs ' + b);
  // trunk
  near(S.effects({ overload: 1 }).magMul, 1.1); near(S.effects({ overload: 3 }).magMul, 1.3);
  near(S.effects({ heavyink: 3 }).dmgMul, 1.12);
  // row 2
  const st = S.effects({ stream: 3 }); near(st.pierce, 0.18); assert.equal(st.pierceMul, 2);
  const el = S.effects({ electrify: 1 }); assert.ok(el.shock); assert.equal(el.shockTime, 5);
  near(S.shockDps(el, 20) * el.shockTime, 5, 'Electrify: 25% of the hit again'); near(S.shockDps(el, 160) * el.shockTime, 40);
  near(S.effects({ rapid: 3 }).rateMul, 1.12);
  // row 3
  const hz = S.effects({ hazard: 2 }); near(hz.pool, 0.1); assert.equal(hz.poolTime, 5); assert.ok(hz.poolBurn >= 5 && hz.poolBurn <= 7);
  assert.equal(S.poolDps(hz, 2), hz.poolMin); assert.equal(S.poolDps(hz, 999), hz.poolMax); near(S.poolDps(hz, 18), 9);
  const rc = S.effects({ ricochet: 3 }); near(rc.ricochet, 0.24); assert.equal(rc.ricochetRange, 10); near(rc.ricochetFrac, 0.6);
  const hl = S.effects({ healthy: 3 }); near(hl.maxHpMul, 1.24); near(hl.regenPct, 1.5); assert.equal(hl.regenDelay, 4);
  near(S.regenRate(hl, 200), 3, '0.5% per rank per second');
  // row 4
  const sm = S.effects({ stamina: 1 }); assert.deepEqual([sm.sprintMul, sm.moveMul, sm.staminaMul, sm.staminaRechargeMul], [1.15, 1.15, 2.5, 0.5]);
  const hy = S.effects({ hydrate: 3 }); near(hy.coat, 0.18); assert.equal(hy.coatTime, 6); assert.equal(hy.coatRadius, 3); assert.ok(hy.coatBurn >= 5 && hy.coatBurn <= 7);
  const uc = S.effects({ undercover: 1 }); assert.ok(uc.cloak); assert.equal(uc.cloakTime, 5); assert.equal(uc.cloakCooldown, 30);
  // row 5
  const tk = S.effects({ tank: 3 }); near(tk.dmgTakenMul, 0.85); assert.equal(tk.regenFlat, 3); near(S.regenRate(tk, 150), 3);
  near(S.regenRate(S.effects({ tank: 2, healthy: 1 }), 100), 2.5);
  const ff = S.effects({ fastfingers: 3 }); near(ff.reloadMul, 1 / 1.3); near(ff.swapMul, 1 / 1.3);
  // endgame
  const hh = S.effects({ handyhelpers: 1 }); near(hh.rogue, 0.08); assert.equal(hh.rogueTime, 15);
  const cr = S.effects({ chainreaction: 1 }); near(cr.chain, 0.1); assert.equal(cr.chainMin, 2); assert.equal(cr.chainRadius, 4); near(cr.chainFrac, 0.4);
  // every skill id is read by effects(): owning it changes at least one field
  const base = JSON.stringify(none);
  IB.SKILLS.forEach((s) => assert.notEqual(JSON.stringify(S.effects({ [s.id]: 1 })), base, s.id));
  // the whole tree maxed (impossible in play: both endgames) still keeps robots dangerous
  const max = {}; IB.SKILLS.forEach((s) => { max[s.id] = s.max; });
  const m = S.effects(max);
  assert.ok(m.dmgMul <= 1.15 && m.maxHpMul <= 1.25 && m.dmgTakenMul >= 0.85 && m.rateMul <= 1.15);
  assert.ok(S.regenRate(m, 160) <= 6, 'repair stays slow next to robot fire');
});

test('Chain Reaction damage: 40% of each robot max health, and never wrecks the whole group at once', () => {
  const f = S.effects({ chainreaction: 1 });
  assert.deepEqual(S.chainDamage(f, [100, 100, 100], [100, 100, 100]), [40, 40, 40]);
  // two are nearly dead, one is fresh: the weak ones go, the fresh one takes its 40%
  assert.deepEqual(S.chainDamage(f, [10, 20, 100], [100, 100, 100]), [40, 40, 40]);
  // all three would die: the toughest keeps 1 health
  assert.deepEqual(S.chainDamage(f, [10, 30, 25], [100, 100, 100]), [40, 29, 40]);
  for (let t = 0; t < 200; t++) {
    const n = 3 + (t % 4), hp = [], mx = [];
    for (let i = 0; i < n; i++) { mx.push(30 + ((t * 7 + i * 13) % 90)); hp.push(1 + ((t * 11 + i * 5) % mx[i])); }
    const dm = S.chainDamage(f, hp, mx);
    assert.ok(dm.some((x, i) => x < hp[i]), 'someone survives ' + JSON.stringify([hp, mx, dm]));
    assert.ok(dm.every((x) => x >= 0) && dm.every((x, i) => x <= 0.4 * mx[i] + 1e-9));
  }
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
  const slot = { highest: 8, gems: 200, skills: buyAll({}, 8, ['overload', 'overload', 'heavyink']) };
  const r = S.respec(slot);
  assert.deepEqual(r, { ok: true, cost: 90 });
  assert.equal(slot.gems, 110); assert.deepEqual(slot.skills, {});
  assert.equal(S.available(slot.skills, 8), S.earned(8), 'every point refunded');
  assert.equal(S.respec(slot).reason, 'empty', 'nothing to reset');
  const poor = { highest: 8, gems: 89, skills: { overload: 1 } };
  assert.equal(S.respec(poor).reason, 'gems'); assert.equal(poor.gems, 89); assert.deepEqual(poor.skills, { overload: 1 });
});

test('player level: +1 per completed campaign level, capped at 30, with a rank title each', () => {
  assert.equal(S.playerLevel(0), 1);
  for (let h = 0; h <= 19; h++) assert.equal(S.playerLevel(h), h + 1);
  assert.equal(S.playerLevel(20), 21); assert.equal(S.playerLevel(29), 30); assert.equal(S.playerLevel(45), 30);
  for (let lv = 1; lv <= 30; lv++) assert.ok(typeof S.rankTitle(lv) === 'string' && S.rankTitle(lv).length > 3, 'title ' + lv);
  assert.equal(new Set(IB.RANK_TITLES.slice(1)).size, 30, 'titles are unique');
  assert.equal(S.rankTitle(99), S.rankTitle(30));
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
