// Robots and robot features of levels 30+ (data/enemies.js rows jet / rocketeer, blader kusarigama, pullResist;
// levelplans.js lateWaves35): spawn levels, the thinning grey bots, the Jet Trooper's element roll and its damage over
// time, Singularity immunity, the Blade Bot's three weapons, the Rocket Soldier's slow launchers.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'data/themes', 'core/damage', 'core/gems'].forEach((f) => require('../../src/' + f + '.js'));
fs.readdirSync(path.join(__dirname, '../../src/data/themes')).forEach((f) => require('../../src/data/themes/' + f));
require('../../src/data/levelplans.js');
const IB = globalThis.IB;
const E = IB.ENEMIES, D = IB.Damage, W = IB.WEAPONS;

const count = (p, f) => p.zones.reduce((a, z) => a + z.waves.reduce((b, w) => b + w.filter((e) => f(e[0])).reduce((c, e) => c + e[1], 0), 0), 0);
const byLevel = (L) => IB.LEVEL_PLANS[IB.CAMPAIGN.find((id) => IB.LEVEL_PLANS[id].level === L)];
const plan = (zones) => ({ id: 'test', zones: zones.map((waves, i) => ({ map: 'z' + i, waves: JSON.parse(JSON.stringify(waves)) })) });

test('rows: Jet Trooper and Rocket Soldier arrive on level 35, registered and levelled like every robot', () => {
  assert.deepEqual(IB.ENEMY_ORDER.slice(-2), ['jet', 'rocketeer']);
  for (const id of ['jet', 'rocketeer']) {
    const e = E[id];
    assert.equal(e.id, id); assert.equal(e.first, 35); assert.equal(IB.MIN_LEVEL[id], 35);
    assert.ok(e.hp > 0 && e.shield > 0 && e.cost > 0 && e.gems.chip > 0 && e.radius > 0 && e.height > 1.8, id);
    assert.ok(D.enemyAt(e, 35).hp > e.hp * 2.5, id + ' scales with the level');
    assert.ok(IB.GLB_BOT_NAMES.includes('BOT_' + id.toUpperCase()));
  }
  // based on the Soldier / Hawk at level 35: about a Soldier's total toughness, a Hawk's bullet damage, it flies
  const j = E.jet, s = E.soldier, h = E.hawk;
  const tough = (r) => D.enemyAt(r, 35).hp + r.shield * D.enemyHpMul(35);
  assert.ok(tough(j) >= tough(s) * 0.9 && tough(j) <= tough(s) * 1.25, 'jet toughness ' + tough(j) + ' vs soldier ' + tough(s));
  assert.ok(tough(j) > 2 * tough(h), 'tougher than a hawk');
  assert.equal(j.flying, true); assert.equal(j.damage, h.damage);
  // the volley: 6 rockets, a clear lock-on tell of 0.8-1 s, a 6-9 s cooldown, dodgeable speeds
  const V = j.volley;
  assert.equal(V.rockets, 6);
  assert.ok(V.lock >= 0.8 && V.lock <= 1.0 && V.lock * D.enemyTempo(35).tellMul <= 1.0);
  assert.ok(V.cool[0] >= 6 && V.cool[1] <= 9 && V.cool[0] < V.cool[1]);
  assert.ok(V.speed <= 18 && V.homeT <= 0.6 && V.scatter > 0, 'rockets steer briefly and fly slowly enough to dodge');
  assert.ok(V.near < V.far && V.above >= 1.5);
  assert.ok(j.lowCeiling > 4 && j.dashSpeed > j.speed * 1.8 && j.dashTime > 0, 'indoors: stays on its feet and dashes');
  // Rocket Soldier: a Soldier's body (health, shield, armour, drops), no grenades, a launcher instead of the carbine
  const r = E.rocketeer;
  assert.deepEqual([r.hp, r.shield, r.armour, r.weaponDrops], [s.hp, s.shield, s.armour, s.weaponDrops]);
  assert.equal(r.grenades, 0); assert.equal(r.rockets, true);
});

test('Rocket Soldier: a Murmur or a Hothead, and it fires slower than the player versions and than any other soldier', () => {
  const r = E.rocketeer;
  assert.deepEqual(Object.keys(r.launchers).sort(), ['hothead', 'murmur']);
  const seen = { hothead: 0, murmur: 0 };
  for (let i = 0; i < 1000; i++) seen[IB.rocketeerLauncher((i + 0.5) / 1000)]++;
  assert.ok(seen.hothead > 400 && seen.murmur > 400, JSON.stringify(seen));
  for (const id of ['hothead', 'murmur']) {
    const L = r[id], P = W[id];
    // the player's: Hothead one rocket every 60/rpm s, Murmur one salvo every 60/rpm s; the enemy's volley cycle is
    // the shots' spacing plus the pause between volleys -- far slower per rocket
    const playerGap = 60 / P.rpm, cycle = (L.rockets - 1) * L.gap + L.fireEvery[0] + r.windup;
    assert.ok(cycle / L.rockets > playerGap * 2, id + ' ' + (cycle / L.rockets).toFixed(2) + ' s per rocket vs ' + playerGap);
    assert.ok(L.fireEvery[0] > E.soldier.recover + 1.1 + 1.3 && L.fireEvery[0] >= E.grenadier.fireEvery[0], id + ' slower than soldiers');
    assert.ok(L.damage > 0 && L.radius >= 2 && L.speed >= 10);
  }
  assert.ok(r.murmur.turn > 0 && r.murmur.homeT > 0 && r.hothead.turn === 0, 'Murmur missiles home a little, Hothead rockets fly straight');
});

test('spawn levels: no Jet Troopers or Rocket Soldiers before level 35, both on every campaign level from 35', () => {
  IB.CAMPAIGN.forEach((id) => {
    const p = IB.LEVEL_PLANS[id], j = count(p, (k) => k === 'jet'), r = count(p, (k) => k === 'rocketeer');
    if (p.level < 35) assert.equal(j + r, 0, id);
    else if (p.lateRobots !== false) assert.ok(j > 0 && r > 0, id + ' ' + j + ' / ' + r);
  });
  assert.ok(byLevel(35), 'a level 35 plan');
  // a theme that names them early: they step back (jet -> hawk, rocketeer -> mech)
  const early = plan([[[['crawler', 2], ['jet', 2], ['rocketeer', 3]]]]);
  const zone = early.zones[0];
  zone.waves = zone.waves.map((w) => w.map(([k, n]) => { let id = k; while (IB.MIN_LEVEL[id] && 30 < IB.MIN_LEVEL[id]) id = { jet: 'hawk', rocketeer: 'mech' }[id]; return [id, n]; }));
  assert.deepEqual(zone.waves[0].map((e) => e[0]), ['crawler', 'hawk', 'mech']);
  // lateWaves35: a share of the hawks / mechs become the new robots, one for one; the opening wave stays as it was
  const zones = [[[['crawler', 10], ['hawk', 4], ['mech', 5]], [['crawler', 8], ['hawk', 6], ['mech', 10]]], [[['hawk', 5], ['mech', 6], ['soldier', 3]]]];
  const p = plan(zones), n0 = count(p, () => true), h0 = count(p, (k) => k === 'hawk'), m0 = count(p, (k) => k === 'mech');
  IB.lateWaves35(p, 35);
  assert.deepEqual(p.zones[0].waves[0].filter((e) => e[0] !== 'crawler'), [['hawk', 4], ['mech', 5]], 'opening wave');
  const j = count(p, (k) => k === 'jet'), r = count(p, (k) => k === 'rocketeer');
  assert.equal(count(p, (k) => k === 'hawk') + j, h0); assert.equal(count(p, (k) => k === 'mech') + r, m0);
  assert.equal(j, Math.round((6 + 5) * IB.LATE35.jet)); assert.equal(r, Math.round((10 + 6) * IB.LATE35.rocketeer));
  assert.equal(count(p, () => true) + p.crawlerCut, n0);
  const again = JSON.stringify(p.zones); IB.lateWaves35(p, 35); assert.equal(JSON.stringify(p.zones), again, 'idempotent');
  const q = plan(zones); IB.lateWaves35(q, 34); assert.equal(count(q, (k) => k === 'jet' || k === 'rocketeer'), 0, 'level 34: none');
});

test('grey bots thin out: fewer Crawlers from level 30, much lower by level 35', () => {
  assert.equal(IB.crawlerShare(29), 1);
  let prev = 1;
  for (let L = 30; L <= 45; L++) { const s = IB.crawlerShare(L); assert.ok(s <= prev && s < 1, 'L' + L); prev = s; }
  assert.ok(IB.crawlerShare(30) >= 0.8, 'a gentle start');
  assert.ok(IB.crawlerShare(35) <= 0.45 && IB.crawlerShare(45) === IB.crawlerShare(35), 'much lower from 35');
  // the plan: the same waves keep about crawlerShare of their Crawlers (each wave keeps at least one)
  const waves = [[['crawler', 12], ['mech', 4]], [['crawler', 9], ['hawk', 3]], [['crawler', 1], ['soldier', 4]]];
  for (const L of [29, 30, 33, 35, 40]) {
    const p = plan([waves]); IB.lateWaves35(p, L);
    const c = count(p, (k) => k === 'crawler');
    if (L < 30) assert.equal(c, 22);
    else assert.ok(Math.abs(c - Math.max(3, 22 * IB.crawlerShare(L))) <= 1.5, 'L' + L + ' ' + c);
    p.zones[0].waves.forEach((w) => assert.ok(w.some((e) => e[0] === 'crawler' && e[1] >= 1), 'a wave keeps a crawler'));
  }
  // the campaign: Crawlers per zone dip from level 30 and level 35 has far fewer than level 29
  const per = (L) => { const p = byLevel(L); return count(p, (k) => k === 'crawler') / p.zones.length; };
  assert.ok(per(30) < per(29), '30 < 29');
  assert.ok(per(35) < per(29) * 0.65, '35: ' + per(35) + ' vs 29: ' + per(29));
  for (let L = 30; L <= 35; L++) assert.ok(byLevel(L).crawlerCut > 0, 'cut on ' + L);
  // levels 1-29 are untouched
  IB.CAMPAIGN.forEach((id) => { const p = IB.LEVEL_PLANS[id]; if (p.level < 30) assert.ok(!p.crawlerCut, id); });
});

test('Jet Trooper element: one of electric / acid / explosive per robot, painted on its accents, carried by its rockets', () => {
  const j = E.jet, seen = { shock: 0, acid: 0, boom: 0 };
  assert.deepEqual(Object.keys(j.elements).sort(), ['acid', 'boom', 'shock']);
  for (let i = 0; i < 3000; i++) seen[IB.jetElement((i + 0.5) / 3000)]++;
  for (const k of Object.keys(seen)) assert.ok(Math.abs(seen[k] / 3000 - 1 / 3) < 0.01, k + ' ' + seen[k]);
  // the accent colours match the Hawk's round colours for the same element (the game's status colours)
  assert.equal(j.elementColors.shock, E.hawk.roundColors.shock); assert.equal(j.elementColors.acid, E.hawk.roundColors.acid);
  assert.equal(j.elementColors.boom, E.hawk.roundColors.boom);
  // every rocket deals explosive damage; electric and acid add damage over time on the player, explosive a bigger blast
  const mul = D.enemyDmgMul(35), S = IB.jetRocket('shock', mul), A = IB.jetRocket('acid', mul), B = IB.jetRocket('boom', mul);
  for (const r of [S, A, B]) assert.ok(r.damage > 0 && r.radius >= 2, 'explosive');
  assert.deepEqual([S.dot.kind, A.dot.kind, B.dot], ['shock', 'acid', null]);
  assert.ok(S.dot.dps > 0 && S.dot.time > 0 && A.dot.dps > 0 && A.dot.time > 0);
  assert.ok(Math.abs(S.dot.dps - j.elementDot.shock.dps * mul) < 1e-9, 'the damage over time scales with the level');
  assert.ok(B.damage > S.damage * 1.2 && B.radius > S.radius, 'explosive: extra explosive damage, a wider blast');
  assert.equal(S.damage, A.damage);
  // a whole volley that lands on the player is a heavy hit, never a one-shot (player health at level 35)
  const volley = 6 * B.damage * D.lateBoom(35).dmg;
  assert.ok(volley < D.playerMaxHp(35) * 0.35, 'volley ' + volley.toFixed(0) + ' of ' + D.playerMaxHp(35));
});

test('Singularity immunity: drones, hawks, Jet Troopers and Rocket Soldiers resist it fully, the others not at all', () => {
  for (const id of ['drone', 'hawk', 'jet', 'rocketeer']) assert.equal(IB.pullResist(id), 1, id);
  for (const id of ['crawler', 'gunner', 'bomber', 'soldier', 'blader', 'mech', 'grenadier']) assert.equal(IB.pullResist(id), 0, id);
  assert.equal(E.jet.flying, true); assert.equal(E.drone.flying, true); assert.equal(E.hawk.flying, true);
});

test('Blade Bot weapons: katana, Voltaxe or kusarigama, a third each; the kusarigama numbers', () => {
  const b = E.blader, seen = { katana: 0, eaxe: 0, kusari: 0 };
  assert.deepEqual(Object.keys(b.weaponOdds), b.weapons);
  for (let i = 0; i < 3000; i++) seen[IB.bladerWeapon((i + 0.5) / 3000)]++;
  for (const k of Object.keys(seen)) assert.ok(Math.abs(seen[k] / 3000 - 1 / 3) < 0.01, k + ' ' + seen[k]);
  assert.equal(IB.bladerWeapon(0), 'katana'); assert.equal(IB.bladerWeapon(0.999), 'kusari');
  // whirl: ticks while the player stays inside the circle; then a tell and a throw that a sidestep beats
  assert.ok(b.kusariRadius > b.spinRange && b.kusariRange <= b.kusariRadius + 2, 'the chain reaches farther than the blades');
  assert.ok(b.kusariDamage < b.spinDamage && b.kusariTick >= 0.3, 'whirl ticks: small, steady');
  assert.ok(b.kusariWhirl * b.kusariDamage / b.kusariTick < 4 * b.damage, 'a whole whirl is not a one-shot');
  assert.ok(b.kusariTell >= 0.35 && b.kusariThrow > b.kusariDamage && b.kusariReach > b.kusariRadius);
  assert.ok(b.kusariSpeed <= 20, 'the sickle can be sidestepped');
  assert.ok(!IB.WEAPONS.kusari, 'not a player weapon: nothing to drop');
});
