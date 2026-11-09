'use strict';
// gameplay tuning (round 7): full ammo boxes stay put, overwhelm control, Undercover numbers, critical health cans,
// blader rocket crates
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/unlocks', 'data/levels', 'data/skills',
  'core/damage', 'core/gunlevel', 'core/loadout', 'core/skills']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const D = IB.Damage;
const W = IB.WEAPONS;

test('ammo boxes: taken only while some carried gun can still hold more spare ammo', () => {
  const Lo = IB.Loadout, pip = W.pip, buzz = W.buzz;
  const cap = (d) => Lo.reserveCap(d);
  assert.equal(cap(pip), Math.floor(pip.reserve * 1.5));
  assert.ok(Lo.ammoFull({ pip: { def: pip, reserve: cap(pip) }, buzz: { def: buzz, reserve: cap(buzz) } }), 'all full');
  assert.ok(!Lo.ammoFull({ pip: { def: pip, reserve: cap(pip) }, buzz: { def: buzz, reserve: cap(buzz) - 1 } }), 'one gun short');
  // melee (infinite) and launchers (rocket pool: only rocket crates refill it) never ask for a box
  const melee = Object.values(W).find((d) => d.cls === 'melee');
  assert.ok(Lo.ammoFull({ pip: { def: pip, reserve: cap(pip) }, k: { def: melee, reserve: Infinity }, h: { def: W.hothead, reserve: 0 } }));
  assert.ok(Lo.ammoFull({}), 'nothing that takes ammo: full');
});

test('overwhelm control: a few melee robots close in at once, a wave trickles in, ~40 % of soldiers aim worse', () => {
  // close-range slots grow slowly with the level, and stay near the attack tokens' ration
  assert.equal(D.closeCap(1), 5); assert.equal(D.closeCap(9), 5); assert.equal(D.closeCap(10), 6); assert.equal(D.closeCap(19), 6); assert.equal(D.closeCap(20), 7);
  for (let L = 1; L <= 40; L++) assert.ok(D.closeCap(L) <= D.attackTokens(L) + 2 && D.closeCap(L) >= 5, 'L' + L);
  // the hold ring sits outside melee reach (2.4 m) and inside the gunners' band (7-16 m starts at 7)
  assert.ok(D.HOLD.ringIn > 3 && D.HOLD.ringOut > D.HOLD.ringIn && D.HOLD.ringOut <= 10);
  // spawn pacing: only a crowd of more than the close slots holds spawns back, and never for long
  for (let L = 1; L <= 30; L++) assert.ok(D.crowdCap(L) >= D.closeCap(L) + 3, 'L' + L);
  assert.ok(D.SPAWN_WAIT_MAX > 0 && D.SPAWN_WAIT_MAX <= 4);
  assert.ok(D.SPAWN_GAP >= 0.18 && D.SPAWN_GAP <= 0.35);
  // sloppy aim share: 35-45 % in any run of 20+ soldiers
  for (const start of [1, 7, 33, 120]) {
    for (const n of [20, 50, 200]) {
      let k = 0; for (let i = 0; i < n; i++) if (D.sloppyAim(start + i)) k++;
      const f = k / n; assert.ok(f >= 0.35 && f <= 0.45, start + '+' + n + ': ' + f);
    }
  }
  assert.ok(D.SLOPPY.spreadMul > 1 && D.SLOPPY.spreadMul <= 2.5 && D.SLOPPY.leadMul < 1 && D.SLOPPY.leadMul > 0.3);
});

test('Undercover: 7 s invisible, 25 s cooldown, and the skill text says so', () => {
  const uc = IB.Skills.effects({ undercover: 1 });
  assert.equal(uc.cloakTime, 7); assert.equal(uc.cloakCooldown, 25);
  const sk = IB.SKILLS.find((s) => s.id === 'undercover');
  assert.match(sk.desc || sk.text || JSON.stringify(sk), /7 s/);
  assert.match(sk.desc || sk.text || JSON.stringify(sk), /Cooldown 25 s/);
});

test('health director: critically hurt -> twice the cans, twice as often, closer (never on top of the player)', () => {
  const ok = D.healthPlan(0.6), low = D.healthPlan(0.31), crit = D.healthPlan(0.29);
  assert.equal(ok.want, 2); assert.equal(low.want, 3); assert.ok(!low.critical);
  assert.ok(crit.critical);
  assert.equal(crit.want, 8, 'four cans doubled');
  assert.equal(crit.every * 2, low.every, 'checked twice as often');
  assert.ok(crit.dMin >= 4 && crit.dMax <= 12 && crit.dMin < low.dMin && crit.dMax < low.dMax, 'closer');
  assert.equal(D.healthPlan(1).want, 1);
});

test('rocket crates: soldiers and (at half the chance) bladers; others never', () => {
  const GL = IB.GunLevel;
  assert.equal(GL.rocketDropWeight('blader') * 2, GL.rocketDropWeight('soldier'));
  for (const t of ['crawler', 'gunner', 'bomber', 'drone']) assert.equal(GL.rocketDropWeight(t), 0, t);
});
