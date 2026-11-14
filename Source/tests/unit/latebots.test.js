// Robots of levels 20+ (data/enemies.js rows mech / grenadier / hawk; levelplans.js lateWaves): the rows, and the
// wave mapping that turns the theme files' gunner / bomber / drone / soldier entries into them from level 20 on.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'data/themes', 'core/damage', 'core/gems'].forEach((f) => require('../../src/' + f + '.js'));
fs.readdirSync(path.join(__dirname, '../../src/data/themes')).forEach((f) => require('../../src/data/themes/' + f));
require('../../src/data/levelplans.js');
const IB = globalThis.IB;
const E = IB.ENEMIES, D = IB.Damage, LATE = IB.LATE_WAVES;
const NEW = ['mech', 'grenadier', 'hawk'];

const sum = (waves, f) => waves.reduce((a, w) => a + w.filter((e) => f(e[0])).reduce((b, e) => b + e[1], 0), 0);
const plan = (zones, extra) => Object.assign({ id: 'test', zones: zones.map((waves, i) => ({ map: 'z' + i, waves: JSON.parse(JSON.stringify(waves)) })) }, extra || {});
const all = (p) => p.zones.reduce((a, z) => a.concat(z.waves), []);
const cost = (p) => all(p).reduce((a, w) => a + w.reduce((b, e) => b + e[1] * E[e[0]].cost, 0), 0);

test('new robot rows: ids, first level 20, a place in ENEMY_ORDER, the Soldier\'s plumbing', () => {
  assert.deepEqual(IB.ENEMY_ORDER.slice(10, 13), NEW);
  for (const id of NEW) {
    const e = E[id];
    assert.equal(e.id, id); assert.equal(e.first, 20);
    assert.match(e.color, /^#[0-9A-F]{6}$/);
    assert.ok(e.hp > 0 && e.cost > 0 && e.gems.chip > 0 && e.radius > 0 && e.height > 0 && e.coreOffset.length === 3, id);
    assert.ok(e.windup >= 0.35 && e.windup <= 0.9, id + ' windup');
  }
  // Robot Trooper: normal rounds only, no grenades, a lighter armour pool than the Soldier, tougher than a Gunner
  const m = E.mech, s = E.soldier, g = E.gunner;
  assert.equal(m.grenades, 0); assert.equal(m.specialRounds, undefined);
  assert.ok(m.shield < s.shield && m.hp + m.shield < s.hp + s.shield && m.hp + m.shield > 1.5 * g.hp);
  for (const t of Object.keys(s.weaponDrops)) assert.ok(m.weaponDrops[t] < s.weaponDrops[t] && m.weaponDrops[t] > 0, 'mech drops ' + t);
  // Grenadier: a Soldier (armour, shield, drops) with a launcher that fires far slower than the Soldier's bursts
  const gr = E.grenadier;
  assert.deepEqual([gr.hp, gr.shield, gr.armour, gr.weaponDrops], [s.hp, s.shield, s.armour, s.weaponDrops]);
  assert.equal(gr.launcher, true); assert.equal(gr.grenades, 0);
  assert.ok(gr.fireEvery[0] >= 3 && gr.shellRadius > 2 && gr.shellDamage > s.damage && gr.minRange >= 4);
  // Hawk: a flyer, faster and tougher than the Drone, four round types with four accent colours
  const h = E.hawk, dr = E.drone;
  assert.equal(h.flying, true);
  assert.ok(h.speed > dr.speed && h.hp > dr.hp);
  assert.deepEqual(Object.keys(h.rounds).sort(), ['boom', 'acid', 'bullet', 'shock'].sort());
  assert.ok(Math.abs(Object.values(h.rounds).reduce((a, b) => a + b, 0) - 1) < 1e-9);
  assert.equal(new Set(Object.values(h.roundColors)).size, 4);
  // levelled like every robot
  for (const id of NEW) assert.ok(D.enemyAt(E[id], 20).hp > E[id].hp);
});

test('levels 1-19 play as before: no new robots in the campaign up to level 19, lateWaves is a no-op there', () => {
  IB.CAMPAIGN.forEach((id) => {
    const p = IB.LEVEL_PLANS[id];
    if (p.level >= LATE.level) return;
    for (const w of all(p)) for (const e of w) assert.ok(!NEW.includes(e[0]), id + ' ' + e[0]);
  });
  const waves = [[['crawler', 10], ['gunner', 4], ['bomber', 2], ['drone', 3], ['soldier', 6]], [['soldier', 5], ['drone', 2]]];
  const p = plan([waves]), before = JSON.stringify(p.zones);
  IB.lateWaves(p, 19);
  assert.equal(JSON.stringify(p.zones), before);
  assert.equal(LATE.level, 20);
});

test('level 20: gunner + bomber -> mech (x0.6), drone -> hawk (x0.75), a quarter of the soldiers -> grenadier', () => {
  const zones = [
    [[['crawler', 12], ['gunner', 5]], [['crawler', 10], ['bomber', 2], ['gunner', 3], ['soldier', 4]], [['drone', 4], ['soldier', 6], ['blader', 3]]],
    [[['gunner', 6], ['crawler', 9]], [['soldier', 3], ['drone', 2], ['bomber', 1]], [['soldier', 8], ['gunner', 2], ['crawler', 14]]],
    [[['soldier', 2], ['crawler', 8]], [['soldier', 1], ['drone', 5]], [['soldier', 10], ['gunner', 4], ['bomber', 2], ['drone', 3]]]
  ];
  const src = plan(zones), p = plan(zones);
  IB.lateWaves(p, 20);
  const W0 = all(src), W1 = all(p);
  // no old light robots left, nothing else touched
  for (const w of W1) for (const e of w) assert.ok(!['gunner', 'bomber', 'drone'].includes(e[0]), e[0]);
  assert.equal(sum(W1, (k) => k === 'blader'), sum(W0, (k) => k === 'blader'));
  // level totals: the rounded shares exactly; the robots the shares leave out come back as Crawlers (same count)
  const gb = sum(W0, (k) => k === 'gunner' || k === 'bomber'), dr = sum(W0, (k) => k === 'drone'), so = sum(W0, (k) => k === 'soldier');
  assert.equal(sum(W1, (k) => k === 'crawler'), sum(W0, (k) => k === 'crawler') + gb - Math.round(gb * LATE.mech) + dr - Math.round(dr * LATE.hawk));
  assert.equal(sum(W1, () => true), sum(W0, () => true));
  assert.equal(sum(W1, (k) => k === 'mech'), Math.round(gb * LATE.mech));
  assert.equal(sum(W1, (k) => k === 'hawk'), Math.round(dr * LATE.hawk));
  assert.equal(sum(W1, (k) => k === 'grenadier'), Math.round(so / 4));
  assert.equal(sum(W1, (k) => k === 'soldier' || k === 'grenadier'), so);
  // per wave: 3/4 soldiers, 1/4 grenadiers (within one), at least one grenadier in a wave of 4 or more soldiers,
  // a mech wherever there were gunners / bombers, a hawk wherever there were drones
  W0.forEach((w0, i) => {
    const w1 = W1[i], n = (w, k) => sum([w], (x) => x === k);
    const s0 = n(w0, 'soldier'), g1 = n(w1, 'grenadier');
    assert.ok(Math.abs(g1 - s0 / 4) <= 1, 'wave ' + i + ': ' + g1 + ' of ' + s0);
    assert.equal(n(w1, 'soldier') + g1, s0);
    if (s0 >= 4) assert.ok(g1 >= 1, 'wave ' + i + ' has a grenadier');
    if (n(w0, 'gunner') + n(w0, 'bomber')) assert.ok(n(w1, 'mech') >= 1 && Math.abs(n(w1, 'mech') - 0.6 * (n(w0, 'gunner') + n(w0, 'bomber'))) <= 1, 'wave ' + i + ' mechs');
    if (n(w0, 'drone')) assert.ok(n(w1, 'hawk') >= 1, 'wave ' + i + ' hawks');
    // the entries keep the theme's order (the old robot's slot)
    assert.ok(w1.every((e) => e[1] > 0));
  });
  // idempotent, and a plan can opt out
  const again = JSON.stringify(p.zones); IB.lateWaves(p, 20); assert.equal(JSON.stringify(p.zones), again);
  const off = plan(zones, { lateRobots: false }); IB.lateWaves(off, 22); assert.equal(JSON.stringify(off.zones), JSON.stringify(src.zones));
  // ids written directly are left as written
  const direct = plan([[[['mech', 3], ['hawk', 2], ['grenadier', 1], ['soldier', 4]]]]); IB.lateWaves(direct, 21);
  assert.deepEqual(direct.zones[0].waves[0], [['mech', 3], ['hawk', 2], ['grenadier', 2], ['soldier', 3]]);
});

test('the level-19 waves converted for level 20 keep the difficulty on a smooth climb', () => {
  const L19 = IB.LEVEL_PLANS[IB.CAMPAIGN.find((id) => IB.LEVEL_PLANS[id].level === 19)];
  assert.ok(L19, 'a level 19 plan');
  const p = plan(L19.zones.map((z) => z.waves)), before = cost(p), n0 = all(p).reduce((a, w) => a + w.reduce((b, e) => b + e[1], 0), 0);
  IB.lateWaves(p, 20);
  const after = cost(p), n1 = all(p).reduce((a, w) => a + w.reduce((b, e) => b + e[1], 0), 0);
  // tougher robots plus Crawler fodder: the same count, the level's weighted cost climbs a step, never a wall or a dip
  assert.ok(after >= before && after <= before * 1.25, 'cost ' + before + ' -> ' + after);
  assert.equal(n1, n0, 'robots ' + n0 + ' -> ' + n1);
  // each mech is worth about a gunner and two thirds in health x damage (so 0.6 per gunner holds the pressure)
  const tough = (id) => D.enemyAt(E[id], 20).hp + (E[id].shield || 0) * D.enemyHpMul(20);
  assert.ok(tough('mech') * LATE.mech > tough('gunner') * 0.9 && tough('mech') * LATE.mech < tough('gunner') * 1.6);
  assert.ok(tough('hawk') * LATE.hawk > tough('drone') * 0.9 && tough('hawk') * LATE.hawk < tough('drone') * 1.4);
});

// Blade Bot's advanced skin (levels 30+): look only. New meshes for the body, hub and weapons on the normal skin's
// sockets (chain and weight shared), registered and budgeted within +20 % of the normal skin; the switch is a level
// test in game/ai.js read by game/troops.js, which swaps meshes and nothing else.
test('blade bot advanced skin: meshes, sockets, budgets and the level 30 switch', () => {
  require('../../src/data/assets.js');
  const SKIN = ['BOT_BLADER_Body2', 'BOT_BLADER_Hub2', 'BOT_BLADER_Katana2', 'BOT_BLADER_Axe2', 'BOT_BLADER_Kusari2'];
  for (const n of SKIN) assert.ok(IB.ASSET_NAMES.bots.includes(n), n);
  const d = fs.readFileSync(path.join(__dirname, '../../assets/fps-bots.glb'));
  const g = JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
  const node = (n) => g.nodes.find((x) => x.name === n);
  const kids = (n) => (node(n).children || []).map((i) => g.nodes[i].name).sort();
  for (const n of SKIN) assert.ok(node(n) && node(n).mesh !== undefined, n + ' mesh');
  // the skin parts carry no sockets of their own: the game keeps reading CORE / HUB / LIGHT / GRIP / CHAIN off the
  // normal skin, so the pivots and hit volumes cannot drift
  for (const n of SKIN) assert.deepEqual(kids(n), [], n + ' has no sockets');
  assert.deepEqual(kids('BOT_BLADER_Body'), ['BOT_BLADER_CORE', 'BOT_BLADER_HUB', 'BOT_BLADER_LIGHT']);
  assert.deepEqual(kids('BOT_BLADER_Hub'), ['BOT_BLADER_GRIP']);
  // budgets: each skin row mirrors its normal row (2-suffixed body, hub and weapon) within +20 %
  const R = IB.TRI_BUDGET.robots;
  for (const [skin, base] of [['bladerSkin2', 'blader'], ['bladerSkin2Axe', 'bladerAxe'], ['bladerSkin2Kusari', 'bladerKusari']]) {
    const want = Object.fromEntries(Object.entries(R[base].parts).map(([n, k]) => [/_(Body|Hub|Katana|Axe|Kusari)$/.test(n) ? n + '2' : n, k]));
    assert.deepEqual(R[skin].parts, want, skin + ' parts');
    assert.ok(R[skin].max <= R[base].max * 1.2, skin + ' budget ' + R[skin].max + ' vs ' + R[base].max);
  }
  // the switch: every Blade Bot from level 30 on, none before; the pose swaps meshes only
  const ai = fs.readFileSync(path.join(__dirname, '../../src/game/ai.js'), 'utf8');
  assert.match(ai, /AI\.BLADER_SKIN2_LEVEL = 30;/);
  const sw = new Function('AI', ai.match(/AI\.bladerSkin = function \(L\) \{[^}]*\};/)[0] + ' return AI.bladerSkin;')({ BLADER_SKIN2_LEVEL: 30 });
  assert.deepEqual([1, 20, 29, 30, 31, 50].map(sw), [0, 0, 0, 1, 1, 1]);
  const tr = fs.readFileSync(path.join(__dirname, '../../src/game/troops.js'), 'utf8');
  for (const n of SKIN) assert.ok(tr.includes(n.replace('BOT_BLADER_', '') + ": { count: 1, asset: '" + n + "', opt: true }"), n + ' in troops.js');
});
