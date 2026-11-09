// Soldier + Blade Bot (data/enemies.js rows read by game/troops.js): stats, drop tables, level scaling, and how
// they enter the campaign waves (Soldiers from level 4, Blade Bots from level 7, more of both each level).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'data/themes', 'core/damage', 'core/gems'].forEach((f) => require('../../src/' + f + '.js'));
fs.readdirSync(path.join(__dirname, '../../src/data/themes')).forEach((f) => require('../../src/data/themes/' + f));
require('../../src/data/levelplans.js');
const IB = globalThis.IB;
const E = IB.ENEMIES, D = IB.Damage;

test('soldier row: armoured trooper with a shield pool, grenades, melee and weapon drops', () => {
  const s = E.soldier;
  assert.deepEqual([s.first, s.hp, s.shield, s.speed, s.damage, s.gems.chip, s.cost], [4, 80, 60, 3.2, 6, 4, 3.5]);
  assert.equal(s.shieldPool, true);
  assert.ok(s.shieldDelay > 2 && s.shieldDelay < 6 && s.shieldRate > 0);
  assert.equal(s.grenades, 3);
  assert.ok(s.grenadeDamage > 0 && s.grenadeRadius > 2 && s.grenadeFuse >= 1.5);
  assert.ok(s.meleeRange >= 2 && s.meleeRange <= 2.5 && s.meleeDamage > s.damage);
  assert.deepEqual(s.weaponDrops, { gray: 0.06, green: 0.03, blue: 0.02, purple: 0.008, orange: 0.002 });
  assert.ok(s.armour.length >= 5 && s.armour.every((c) => /^#[0-9A-F]{6}$/.test(c)), 'armour colours');
  assert.ok(s.torsos.length >= 2 && s.helmets.length >= 3, 'shape sets');
  assert.ok(s.windup >= 0.35 && s.windup <= 0.9);
});

test('blade bot row: slow patrol, fast dizzy-ending dash, a katana or a Voltaxe that can drop', () => {
  const b = E.blader;
  assert.deepEqual([b.first, b.hp, b.speed, b.damage, b.gems.chip, b.cost], [3, 70, 1.6, 18, 3, 2.5]);
  assert.ok(b.chargeSpeed >= 3 * b.stalkSpeed && b.stalkSpeed > b.speed, 'slow normally, dashes fast');
  assert.ok(b.spinRev >= 15 && b.spinRev <= 25, 'blade spins 15-25 rev/s');
  assert.deepEqual(b.weapons, ['katana', 'eaxe']);
  assert.equal(b.meleeDrop, 0.07);
  assert.ok(b.recover >= 1 && b.dizzyMul > 1, 'a dizzy window to punish');
  assert.ok(b.shockDps > 0 && b.shockTime > 0, 'the axe shocks');
});

test('new robots: registered, gem drops, models', () => {
  assert.deepEqual(IB.ENEMY_ORDER.slice(-2), ['soldier', 'blader']);
  assert.ok(IB.GLB_BOT_NAMES.includes('BOT_SOLDIER') && IB.GLB_BOT_NAMES.includes('BOT_BLADER'));
  assert.equal(IB.Gems.robotDrop('soldier', 6, 0).total, 4);
  assert.equal(IB.Gems.robotDrop('blader', 6, 0).total, 3);
});

test('health, shield and damage grow with the level like every robot (never a wall)', () => {
  for (const id of ['soldier', 'blader']) {
    const row = E[id];
    let prev = null;
    for (let L = 1; L <= 20; L++) {
      const a = D.enemyAt(row, L);
      assert.ok(Math.abs(a.hp - row.hp * D.enemyHpMul(L)) < 1e-9 && Math.abs(a.damage - row.damage * D.enemyDmgMul(L)) < 1e-9, id + ' L' + L);
      if (prev) assert.ok(a.hp > prev.hp && a.damage > prev.damage && a.shield >= prev.shield, id + ' grows at L' + L);
      prev = a;
    }
  }
  const s1 = D.enemyAt(E.soldier, 4), s10 = D.enemyAt(E.soldier, 10), s13 = D.enemyAt(E.soldier, 13);
  assert.ok(Math.abs(s1.shield / s1.hp - 0.75) < 1e-9 && Math.abs(s13.shield / s13.hp - 0.75) < 1e-9, 'shield keeps pace with health');
  // a mid-tier threat: more total toughness than a Gunner, well under a Bruiser
  assert.ok(s1.hp + s1.shield > 2 * E.gunner.hp * D.enemyHpMul(4) && s1.hp + s1.shield < E.bruiser.hp * D.enemyHpMul(4));
  // its hits keep pace with the player's health growth (pressure / health stays near 1, as for the other robots)
  for (const L of [4, 10, 13]) {
    const hpRatio = D.playerMaxHp(L) / D.playerMaxHp(1), dmgRatio = D.enemyAt(E.soldier, L).damage / E.soldier.damage;
    assert.ok(dmgRatio <= hpRatio * 1.05, 'L' + L + ' damage ' + dmgRatio.toFixed(2) + ' vs health ' + hpRatio.toFixed(2));
  }
  assert.ok(s10.grenade > s1.grenade && s10.melee > s1.melee);
});

test('campaign waves: Soldiers from level 4, Blade Bots from level 7, growing with the level, totals climb', () => {
  const count = (plan, t) => plan.zones.reduce((a, z) => a + z.waves.reduce((b, w) => b + w.filter((e) => e[0] === t).reduce((c, e) => c + e[1], 0), 0), 0);
  let lastS = 0, lastB = 0;
  IB.CAMPAIGN.forEach((id) => {
    const p = IB.LEVEL_PLANS[id], L = p.level, s = count(p, 'soldier'), b = count(p, 'blader');
    if (L < 7) assert.equal(b, 0, id + ' bladers');
    if (L < 4) assert.equal(s, 0, id + ' soldiers');
    if (L === 7) assert.ok(b >= 5 && b <= 16, id + ' a first taste of Blade Bots (x2.5 elites)');
    if (L === 4) assert.ok(s >= 3 && s <= 8, id + ' a first taste of Soldiers (x2.5 elites)');
    if (L >= 4) assert.ok(s >= lastS && b >= lastB, id + ' grows');
    const all = p.zones.reduce((a, z) => a + z.waves.reduce((b2, w) => b2 + w.reduce((c, e) => c + e[1], 0), 0), 0);
    assert.ok(all >= (globalThis.__lastAll || 0), id + ' has at least as many robots as the level before');
    globalThis.__lastAll = all;
    // the first wave of the first zone stays as it was (no new robots while the player settles in)
    assert.ok(p.zones[0].waves[0].every((e) => e[0] !== 'soldier' && e[0] !== 'blader'), id + ' opening wave');
    for (const z of p.zones) for (const w of z.waves) {
      const n = w.reduce((a, e) => a + e[1], 0), special = w.filter((e) => e[0] === 'soldier' || e[0] === 'blader').reduce((a, e) => a + e[1], 0);
      assert.ok(special <= Math.ceil(n * 0.5), id + ' ' + z.map + ' never mostly elites');
    }
    lastS = s; lastB = b;
  });
  const last = IB.LEVEL_PLANS[IB.CAMPAIGN[IB.CAMPAIGN.length - 1]];
  assert.ok(count(last, 'soldier') >= 25 && count(last, 'blader') >= 15);
});

test('XP levelling: playing the campaign through (90% of robots) puts the player around LV N+1 after level N', () => {
  require('../../src/data/skills.js'); require('../../src/core/skills.js');
  const S = IB.Skills;
  let xp = 0;
  IB.CAMPAIGN.forEach((id) => {
    const p = IB.LEVEL_PLANS[id], L = p.level;
    p.zones.forEach((z) => z.waves.forEach((w) => w.forEach((e) => { xp += 0.9 * e[1] * S.killXp(e[0], L); })));
    xp += S.clearXp(L);
    const lv = S.levelFromXp(xp);
    assert.ok(lv >= L && lv <= L + 2, id + ' (level ' + L + ') -> LV ' + lv);
  });
  assert.ok(S.levelFromXp(xp) < IB.PLAYER_LEVEL_CAP, 'LV 30 is for the maps still to come');
  // the XP table climbs, killXp grows with the level, replays of early maps pay less
  for (let n = 2; n <= 30; n++) assert.ok(S.xpForLevel(n) > S.xpForLevel(n - 1));
  assert.equal(S.levelFromXp(S.xpForLevel(30) * 5), 30);
  assert.ok(S.killXp('soldier', 15) > S.killXp('soldier', 3) && S.killXp('soldier', 1) > S.killXp('crawler', 1));
  // skill points: 22 by LV 20 and none after
  assert.equal(S.earned(19), 19); assert.equal(S.earned(29), 25);
});

test('no exploding Bombers before level 4', () => {
  IB.CAMPAIGN.forEach((id) => {
    const p = IB.LEVEL_PLANS[id];
    if (p.level < 4) p.zones.forEach((z) => z.waves.forEach((w) => w.forEach((e) => assert.notEqual(e[0], 'bomber', id))));
  });
});
