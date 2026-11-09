'use strict';
// gun levels, launchers and the rocket ammo director (src/core/gunlevel.js) + the launcher balance intent
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/skills', 'data/unlocks', 'data/levels', 'data/themes', 'data/themes.gen',
  'data/levelplans', 'core/damage', 'core/gems', 'core/upgrades', 'core/skills', 'core/gunlevel', 'core/saves']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const GL = IB.GunLevel, W = IB.WEAPONS;
function seq(vals) { let i = 0; return () => vals[i++ % vals.length]; }

test('gun level damage keeps step with robot health through level 30', () => {
  assert.equal(GL.mul(1), 1);
  assert.ok(Math.abs(GL.mul(30) - 2.595) < 1e-9);
  for (let L = 1; L <= 30; L++) {
    const r = GL.mul(L) / IB.Damage.enemyHpMul(L);
    // a fresh gray gun at level L: within 6 % of the hits a fresh gun needed on level 1 ...
    assert.ok(r > 0.94 && r <= 1 + 1e-9, 'level ' + L + ' ratio ' + r.toFixed(3));
    // ... and a green one with one bench damage level is ahead of where level 1 was
    assert.ok(GL.power(1.07, L) * 1.15 / IB.Damage.enemyHpMul(L) > 1.1, 'level ' + L + ' tuned gun');
  }
  for (let L = 2; L <= 30; L++) assert.ok(GL.mul(L) > GL.mul(L - 1));
});

test('effective level: own level, or player level - 4 (never ahead of the level being played)', () => {
  assert.equal(GL.effective(5, 20, 20), 16);
  assert.equal(GL.effective(5, 30, 19), 15);      // XP level outran the campaign: the floor follows the level played
  assert.equal(GL.effective(25, 10, 10), 25);
  assert.equal(GL.effective(undefined, 1, 1), 1);
  assert.equal(GL.effective(3, 6, 6), 3);
  // an old gun stays within ~8 % of a fresh drop
  assert.ok(GL.mul(GL.effective(1, 30, 30)) / GL.mul(30) > 0.9);
});

test('saves: guns from older saves get the highest level cleared; rockets start at 0', () => {
  const s = IB.Saves.migrate({ v: 1, id: 1, highest: 12, arsenal: ['pip', 'rivet'], loadout: ['rivet'], gunTier: { rivet: 'blue' } });
  assert.deepEqual(s.gunLevel, { pip: 12, rivet: 12 });
  assert.equal(s.rockets, 0);
  assert.deepEqual(s.gunRoll, {});
  const n = IB.Saves.migrate({ v: 1, id: 1, highest: 0, arsenal: ['pip'] });
  assert.equal(n.gunLevel.pip, 1);
  const kept = IB.Saves.migrate({ v: 1, id: 1, highest: 9, arsenal: ['pip'], gunLevel: { pip: 4 } });
  assert.equal(kept.gunLevel.pip, 4);
});

test('pickup score: tier x level; a launcher also its magazine', () => {
  assert.ok(GL.score(W.rivet, 1.0, 15) > GL.score(W.rivet, 1.32, 5));
  assert.ok(GL.score(W.rivet, 1.14, 10) > GL.score(W.rivet, 1.07, 10));
  assert.ok(GL.score(W.hothead, 1, 14, { mag: 5 }) > GL.score(W.hothead, 1, 14, { mag: 3 }));
  assert.ok(GL.score(W.hothead, 1, 18, { mag: 3 }) > GL.score(W.hothead, 1, 14, { mag: 4 }));
});

test('launchers: no mods, rocket ammo, rolled magazines and elements', () => {
  for (const id of ['hothead', 'murmur']) {
    const d = W[id];
    assert.ok(GL.isLauncher(d) && d.noMods && d.ammo === 'rocket' && d.unlock === 0, id);
    for (const t of Object.values(IB.LOOT ? IB.LOOT.types : {})) if (t.classes) assert.ok(!t.classes.includes(d.cls), 'mod fits ' + id);
    assert.ok(!IB.ownedWeapons(30).includes(id), id + ' never on a stand');
  }
  assert.deepEqual(W.hothead.magRoll, [3, 5]); assert.deepEqual(W.murmur.magRoll, [2, 4]);
  assert.equal(W.hothead.mag, 3);
  const mags = new Set(), elems = {};
  const rng = IB.RNG && IB.RNG.mulberry32 ? IB.RNG.mulberry32(7) : Math.random;
  for (let i = 0; i < 2000; i++) { const r = GL.rollLauncher(W.hothead, rng); mags.add(r.mag); elems[r.elem] = (elems[r.elem] || 0) + 1; }
  assert.deepEqual([...mags].sort(), [3, 4, 5]);
  assert.deepEqual(Object.keys(elems).sort(), ['acid', 'boom', 'none', 'shock']);
  for (let i = 0; i < 200; i++) { const r = GL.rollLauncher(W.murmur, rng); assert.ok(r.mag >= 2 && r.mag <= 4); assert.equal(r.elem, 'none'); }
  assert.equal(GL.displayName(W.hothead, { elem: 'shock' }), 'Volt Hothead');
  assert.equal(GL.displayName(W.hothead, { elem: 'none' }), 'RL-3 Hothead');
  assert.deepEqual(GL.fixRoll(W.murmur, { mag: 9, elem: 'acid' }), { mag: 4, elem: 'none' });
});

test('launchers drop only after level 13, soldiers more often', () => {
  for (let L = 1; L <= 13; L++) { assert.equal(GL.launcherDropChance('soldier', L), 0); assert.equal(GL.launcherDropChance('crawler', L), 0); }
  assert.ok(GL.launcherDropChance('soldier', 14) > GL.launcherDropChance('crawler', 14));
  assert.ok(GL.launcherDropChance('soldier', 14) <= 0.02);
});

test('rocket ammo director: nothing without a launcher or when full, more when short and in use', () => {
  const R = GL.ROCKET;
  assert.equal(GL.rocketNeed({ owned: false, carried: false, ammo: 0 }), 0);
  assert.equal(GL.rocketNeed({ owned: true, carried: true, ammo: R.cap }), 0);
  assert.equal(GL.rocketNeed({ owned: true, carried: true, ammo: 4, pending: R.cap }), 0);
  const idle = GL.rocketNeed({ owned: true, carried: true, ammo: 2, used: 0 });
  const busy = GL.rocketNeed({ owned: true, carried: true, ammo: 2, used: 6 });
  const pack = GL.rocketNeed({ owned: true, carried: false, ammo: 2, used: 0 });
  assert.ok(busy > idle && idle > pack && pack > 0);
  assert.ok(GL.rocketNeed({ owned: true, carried: true, ammo: 1, used: 6 }) > busy);
  // no crate with a full pool, none past the budget
  assert.equal(GL.rocketDrop({ owned: true, carried: true, ammo: R.cap }, () => 0), 0);
  assert.equal(GL.rocketDrop({ owned: true, carried: true, ammo: 0, used: 6, budget: 12, dropped: 12 }, () => 0), 0);
  // a crate holds 2-5 rockets, never more than the room left
  const n = GL.rocketDrop({ owned: true, carried: true, ammo: 0, used: 6, budget: 40 }, () => 0);
  assert.ok(n >= 2 && n <= 5, 'crate ' + n);
  assert.equal(GL.rocketDrop({ owned: true, carried: true, ammo: R.cap - 1, used: 6, budget: 40, carriedTarget: 1 }, () => 0), 0);
  // pity: a carried launcher out of rockets gets a crate after a few dry soldier kills
  assert.ok(GL.rocketDrop({ owned: true, carried: true, ammo: 0, used: 0, per: 2, dry: R.pity - 1, budget: 40 }, () => 0.999) > 0);
  assert.equal(GL.rocketDrop({ owned: true, carried: true, ammo: 0, used: 0, per: 2, dry: 0, budget: 40 }, () => 0.999), 0);
});

test('balance: launchers hit hardest per shot, but stay inside the ammo economy', () => {
  const guns = Object.values(W).filter((d) => !GL.isLauncher(d) && !['melee', 'grenade'].includes(d.cls) && d.fire !== 'projectile');
  const best = Math.max(...guns.map((d) => GL.shotDamage(d)));
  for (const id of ['hothead', 'murmur']) assert.ok(GL.shotDamage(W[id]) > best, id + ' ' + GL.shotDamage(W[id]) + ' vs ' + best);
  // single-target damage over a magazine + reload: above the best rifle / SMG, but not absurdly (<= 2.5x at the best roll)
  const auto = guns.filter((d) => d.cls === 'rifle' || d.cls === 'smg');
  const top = Math.max(...auto.map((d) => GL.sustainedDps(d)));
  for (const [id, mags] of [['hothead', [3, 5]], ['murmur', [2, 4]]]) {
    const lo = GL.sustainedDps(W[id], mags[0]), hi = GL.sustainedDps(W[id], mags[1]);
    assert.ok(lo > top * 1.2, id + ' lo ' + lo.toFixed(0) + ' vs ' + top.toFixed(0));
    assert.ok(hi <= top * 2.5, id + ' hi ' + hi.toFixed(0) + ' vs ' + top.toFixed(0));
  }
  // a whole level's rockets (a full pool + the director's budget) cannot clear more than a quarter of its robots,
  // even at 2.5 robots wrecked per rocket (a Murmur salvo of 2 rockets spread over 5 locks)
  let checked = 0;
  IB.CAMPAIGN.forEach((pid, i) => {
    const L = i + 1; if (L < GL.LAUNCHER_LEVEL) return;
    const p = IB.LEVEL_PLANS[pid]; let robots = 0, soldiers = 0, bladers = 0;
    p.zones.forEach((z) => z.waves.forEach((w) => w.forEach((e) => { robots += e[1]; if (e[0] === 'soldier') soldiers += e[1]; if (e[0] === 'blader') bladers += e[1]; })));
    const rockets = GL.rocketBudget(soldiers) + GL.ROCKET.cap;   // bladers drop crates too (half chance), from the same budget
    assert.ok(rockets * 2.5 / robots <= 0.25, 'level ' + L + ': ' + rockets + ' rockets vs ' + robots + ' robots');
    checked++;
  });
  assert.ok(checked >= 1);
  // rocket crates stay far rarer than normal ammo boxes (20 % of every kill)
  assert.ok(GL.ROCKET.maxChance * 0.25 < IB.WEAPON_RULES.ammoDropChance);
});

test('rocket crates: melee bladers drop them at half a soldier\'s chance, other robots never', () => {
  assert.equal(GL.rocketDropWeight('soldier'), 1);
  assert.equal(GL.rocketDropWeight('blader'), 0.5);
  assert.equal(GL.rocketDropWeight('bruiser'), 0);
  const st = { owned: true, carried: true, ammo: 0, used: 6, budget: 40 };
  const need = GL.rocketNeed(st), pS = GL.ROCKET.maxChance * need;
  // a roll just under the blader's threshold drops for both; one between the two thresholds only for a soldier
  assert.ok(GL.rocketDrop(Object.assign({ w: 0.5 }, st), () => pS * 0.5 - 1e-6) > 0);
  assert.equal(GL.rocketDrop(Object.assign({ w: 0.5 }, st), () => pS * 0.75), 0);
  assert.ok(GL.rocketDrop(Object.assign({ w: 1 }, st), () => pS * 0.75) > 0);
  assert.equal(GL.rocketDrop(Object.assign({ w: 0 }, st), () => 0), 0);
  // bladers share the soldiers' level budget: once it is spent, no crate from either
  assert.equal(GL.rocketDrop(Object.assign({ w: 0.5, dropped: 40 }, st), () => 0), 0);
});

test('Wyrmforged Ironjaw roll: magazine 18-30 (higher at higher player levels), damage x2 or x3 per drop', () => {
  const def = IB.WEAPONS.handcannon, GL = IB.GunLevel;
  assert.deepEqual(def.wyrm, { mag: [18, 30], mult: [2, 3] });
  assert.equal(def.coreMul, 3); assert.equal(def.headMul, 3);
  const seen = new Set();
  for (let i = 0; i < 400; i++) {
    const r = GL.wyrmRoll(def, 1 + (i % 30), Math.random);
    assert.ok(r.mag >= 18 && r.mag <= 30, 'mag ' + r.mag);
    assert.ok(r.mult === 2 || r.mult === 3, 'mult ' + r.mult);
    seen.add(r.mult);
  }
  assert.equal(seen.size, 2, 'both x2 and x3 turn up');
  // the same luck at LV 1 and at LV 30: the high player level gives the bigger magazine
  const mean = (lv) => { let t = 0; for (let i = 0; i < 2000; i++) t += GL.wyrmRoll(def, lv, Math.random).mag; return t / 2000; };
  assert.ok(mean(30) > mean(1) + 1.5, 'LV 30 averages ' + mean(30).toFixed(2) + ', LV 1 ' + mean(1).toFixed(2));
  assert.deepEqual(GL.fixWyrm(def, { mag: 99, mult: 3 }), { mag: 30, mult: 3 });
  assert.deepEqual(GL.fixWyrm(def, undefined), { mag: 18, mult: 2 });
});

test('Warden: magazine rolled 40-50 (kept as a roll), crit spots x3', () => {
  const def = IB.WEAPONS.pip, GL = IB.GunLevel;
  assert.deepEqual(def.magRange, [40, 50]);
  assert.equal(def.coreMul, 3); assert.equal(def.headMul, 3);
  const seen = new Set();
  for (let i = 0; i < 400; i++) { const r = GL.rollMagRange(def, Math.random); assert.ok(r.mag >= 40 && r.mag <= 50, 'mag ' + r.mag); seen.add(r.mag); }
  assert.ok(seen.size > 3, 'the magazine varies between drops');
  assert.deepEqual(GL.fixMagRange(def, { mag: 99 }), { mag: 50 });
  assert.deepEqual(GL.fixMagRange(def, undefined), { mag: 40 });
});
