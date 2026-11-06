// Loot: drop rolls, stat generation and ranges, compatibility, weapon modifiers, shield math, gear inventory.
const test = require('node:test');
const assert = require('node:assert');
require('../../src/core/rng.js');
require('../../src/data/weapons.js');
require('../../src/data/assets.js');
require('../../src/data/loot.js');
require('../../src/core/loot.js');
const IB = globalThis.IB, L = IB.Loot, T = IB.LOOT;

// small deterministic RNG (mulberry32)
function rng(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const seq = vals => { let i = 0; return () => vals[i++ % vals.length]; };

test('drop chance is about 5 % overall', () => {
  const r = rng(7); let n = 0; const N = 200000;
  for (let i = 0; i < N; i++) if (L.rollDrop(r, { level: 5, cleared: 4 })) n++;
  assert.ok(Math.abs(n / N - 0.05) < 0.003, 'rate ' + n / N);
  assert.equal(T.dropChance, 0.05);
});

test('shields only drop after level 3 is cleared', () => {
  const r = rng(11), seen = c => { const s = new Set(); for (let i = 0; i < 4000; i++) s.add(L.rollType(r, { cleared: c })); return s; };
  for (const c of [0, 1, 2]) assert.ok(!seen(c).has('shield'), 'no shield with cleared=' + c);
  const s3 = seen(3);
  for (const t of ['shield', 'grip', 'scope', 'acid']) assert.ok(s3.has(t), t + ' after level 3');
  assert.deepEqual(L.allowedTypes({ cleared: 0 }).map(t => t.id).sort(), ['acid', 'grip', 'scope']);
});

test('rarity weights: common most, epic rare', () => {
  const r = rng(3), c = { common: 0, rare: 0, epic: 0 }, N = 60000;
  for (let i = 0; i < N; i++) c[L.rollRarity(r)]++;
  assert.ok(Math.abs(c.common / N - 0.70) < 0.01, JSON.stringify(c));
  assert.ok(Math.abs(c.rare / N - 0.24) < 0.01, JSON.stringify(c));
  assert.ok(Math.abs(c.epic / N - 0.06) < 0.006, JSON.stringify(c));
});

test('stats stay inside their rarity range (level 1) and rarer is better', () => {
  for (const type of Object.keys(T.types)) {
    const td = T.types[type];
    for (const rar of ['common', 'rare', 'epic']) {
      for (const x of [0, 0.5, 0.999]) {
        const it = L.makeItem(type, rar, 1, seq([x]));
        for (const k of Object.keys(td.stats)) {
          const rr = td.stats[k][rar], lo = Math.min(rr[0], rr[1]), hi = Math.max(rr[0], rr[1]), step = td.stats[k].round || 0;
          assert.ok(it.stats[k] >= lo - step && it.stats[k] <= hi + step, type + '.' + k + ' ' + it.stats[k] + ' in ' + rr);
        }
      }
    }
    // the best common roll never beats the worst epic roll
    const best = L.makeItem(type, 'common', 1, seq([0.999])), worst = L.makeItem(type, 'epic', 1, seq([0]));
    for (const k of Object.keys(td.stats)) {
      if (td.stats[k].common[0] === td.stats[k].common[1]) continue;
      if (td.stats[k].better === 'low') assert.ok(worst.stats[k] <= best.stats[k] + 1e-9, type + '.' + k);
      else assert.ok(worst.stats[k] >= best.stats[k] - 1e-9, type + '.' + k);
    }
  }
});

test('campaign level scales stats modestly, with caps', () => {
  const s1 = L.makeItem('shield', 'rare', 1, seq([0.5])), s10 = L.makeItem('shield', 'rare', 10, seq([0.5])), s99 = L.makeItem('shield', 'rare', 99, seq([0.5]));
  assert.ok(s10.stats.capacity > s1.stats.capacity && s10.stats.rate > s1.stats.rate);
  assert.ok(s99.stats.capacity <= Math.ceil(T.types.shield.stats.capacity.rare[1] * T.levelScale.shield[1]));
  assert.equal(s10.stats.delay, s1.stats.delay, 'delay does not scale');
  const g99 = L.makeItem('grip', 'epic', 99, seq([0.999]));
  assert.ok(g99.stats.recoil <= T.types.grip.stats.recoil.max && g99.stats.spread <= T.types.grip.stats.spread.max);
  assert.equal(L.levelMul('mod', 1), 1);
  assert.ok(L.levelMul('mod', 20) <= 1.25 && L.levelMul('shield', 20) <= 1.8);
  // balance: an epic shield at level 20 is less than one full health bar
  assert.ok(L.makeItem('shield', 'epic', 20, seq([0.999])).stats.capacity < 100);
});

test('items have names, rarity, level and display lines', () => {
  const it = L.makeItem('scope', 'epic', 4, seq([0.5]));
  assert.match(it.name, /^Hawkeye \d\.\dx$/);
  assert.equal(it.level, 4);
  for (const type of Object.keys(T.types)) {
    const lines = L.statLines(L.makeItem(type, 'rare', 3, seq([0.4])));
    assert.ok(lines.length >= 2 && lines.every(l => l.k && l.v), type);
  }
  assert.match(L.summary(L.makeItem('grip', 'common', 1, seq([0]))), /Recoil -8% · Spread -4%/);
});

test('attachment compatibility per weapon class', () => {
  const W = IB.WEAPONS, grip = { type: 'grip' }, scope = { type: 'scope' }, acid = { type: 'acid' }, shield = { type: 'shield' };
  assert.ok(!L.compatible(grip, 'pip', W.pip), 'no grip on a pistol');
  assert.ok(!L.compatible(scope, 'pip', W.pip), 'no scope on a pistol');
  assert.ok(L.compatible(acid, 'pip', W.pip), 'pistols take a muzzle');
  for (const id of ['buzz', 'rivet']) for (const it of [grip, scope, acid]) assert.ok(L.compatible(it, id, W[id]), it.type + ' on ' + id);
  assert.ok(!L.compatible(scope, 'needle', W.needle) && !L.compatible(scope, 'longtom', W.longtom), 'scoped rifles keep their optics');
  assert.ok(L.compatible(grip, 'needle', W.needle));
  assert.ok(!L.compatible(shield, 'rivet', W.rivet));
  assert.deepEqual(L.slotsFor('pip', W.pip), ['muzzle']);
  assert.deepEqual(L.slotsFor('rivet', W.rivet), ['grip', 'scope', 'muzzle']);
  assert.deepEqual(L.slotsFor('needle', W.needle), ['grip', 'muzzle']);
});

test('applyMods changes a copy of the weapon def', () => {
  const W = IB.WEAPONS, base = W.rivet, snap = JSON.stringify(base);
  const grip = L.makeItem('grip', 'rare', 1, seq([0.5])), scope = L.makeItem('scope', 'rare', 1, seq([0.5])), acid = L.makeItem('acid', 'epic', 1, seq([0.5]));
  const d = L.applyMods(base, { grip, scope, muzzle: acid });
  assert.equal(JSON.stringify(base), snap, 'table untouched');
  assert.ok(Math.abs(d.recoil - base.recoil * (1 - grip.stats.recoil)) < 1e-9);
  assert.ok(Math.abs(d.spreadHip - base.spreadHip * (1 - grip.stats.spread)) < 1e-9);
  assert.ok(Math.abs(d.spreadAim - base.spreadAim * (1 - grip.stats.spread) * (1 - scope.stats.aimSpread)) < 1e-9);
  assert.ok(Math.abs(d.aimZoom - 1 / scope.stats.zoom) < 1e-9 && d.optic);
  assert.equal(d.acid, acid.stats.acid); assert.equal(d.acidDur, acid.stats.dur); assert.ok(d.quiet < 1);
  assert.equal(d.damage, base.damage, 'attachments never change raw damage');
  const plain = L.applyMods(base, {});
  assert.equal(plain.recoil, base.recoil); assert.equal(plain.acid, undefined);
});

test('shield absorbs damage before health, then recharges after the delay', () => {
  const item = L.makeItem('shield', 'common', 1, seq([0]));   // 15 cap, 5 s delay, 6/s
  const st = L.shieldState(item);
  assert.equal(st.cur, 15);
  let r = L.absorb(st, 10);
  assert.deepEqual([r.through, r.absorbed, r.broke], [0, 10, false]);
  r = L.absorb(st, 9);
  assert.deepEqual([r.through, r.absorbed, r.broke], [4, 5, true]);
  assert.equal(st.cur, 0);
  r = L.absorb(st, 7);
  assert.deepEqual([r.through, r.absorbed, r.broke], [7, 0, false], 'empty shield passes everything');
  // no recharge before the delay
  for (let t = 0; t < 4.9; t += 0.1) assert.equal(L.tickShield(st, 0.1) === 'start' ? 'early' : 'ok', 'ok');
  assert.equal(st.cur, 0);
  let ev = null, t = 0;
  while (ev !== 'start' && t < 2) { ev = L.tickShield(st, 0.1); t += 0.1; }
  assert.equal(ev, 'start');
  while (ev !== 'full' && t < 10) { ev = L.tickShield(st, 0.1); t += 0.1; }
  assert.equal(ev, 'full'); assert.equal(st.cur, st.max);
  assert.ok(t > 2 && t < 3.2, 'refill takes cap / rate seconds: ' + t.toFixed(2));
  // a hit during recharge restarts the delay
  L.absorb(st, 5); L.tickShield(st, 1);
  assert.equal(st.cur, 10);
  assert.equal(L.absorb(null, 12).through, 12, 'no shield: all damage goes through');
});

test('gear inventory: add, equip, attach, move, detach, discard, prune, migrate', () => {
  const W = IB.WEAPONS, g = L.defaultGear(), r = rng(5);
  const sh = L.addItem(g, L.makeItem('shield', 'rare', 4, r)), gr = L.addItem(g, L.makeItem('grip', 'common', 4, r)), ac = L.addItem(g, L.makeItem('acid', 'rare', 4, r));
  assert.deepEqual([sh.id, gr.id, ac.id], ['g1', 'g2', 'g3']);
  assert.ok(L.equipShield(g, sh.id)); assert.equal(g.shield, sh.id);
  assert.ok(!L.equipShield(g, gr.id), 'a grip is not a shield');
  assert.ok(!L.attach(g, 'pip', W.pip, gr.id), 'grip does not fit the pistol');
  assert.ok(L.attach(g, 'rivet', W.rivet, gr.id));
  assert.ok(L.attach(g, 'pip', W.pip, ac.id));
  assert.deepEqual(L.attachedTo(g, ac.id), { weapon: 'pip', slot: 'muzzle' });
  assert.ok(L.attach(g, 'buzz', W.buzz, ac.id), 'moving an attachment to another gun');
  assert.equal(L.weaponItems(g, 'pip').muzzle, undefined);
  assert.equal(L.weaponItems(g, 'buzz').muzzle.id, ac.id);
  assert.ok(L.detach(g, 'buzz', 'muzzle')); assert.equal(L.attachedTo(g, ac.id), null);
  L.attach(g, 'buzz', W.buzz, ac.id);
  assert.ok(L.discard(g, ac.id)); assert.equal(L.find(g, ac.id), null); assert.equal(L.weaponItems(g, 'buzz').muzzle, undefined);
  assert.ok(L.discard(g, sh.id)); assert.equal(g.shield, null);
  L.prune(g, ['pip', 'buzz']); assert.equal(g.attach.rivet, undefined);
  // bag cap
  const full = L.defaultGear();
  for (let i = 0; i < T.invCap; i++) assert.ok(L.addItem(full, L.makeItem('grip', 'common', 1, r)));
  assert.equal(L.addItem(full, L.makeItem('grip', 'common', 1, r)), null);
  // migrate drops junk and dangling refs, keeps ids unique and next past them
  const m = L.migrateGear({ inv: [{ id: 'g7', type: 'grip', rarity: 'rare', stats: { recoil: 0.1, spread: 0.1 } }, { id: 'g8', type: 'laser', rarity: 'rare', stats: {} }, 5],
    shield: 'g7', attach: { rivet: { grip: 'g7', scope: 'g99' } }, next: 2 });
  assert.equal(m.inv.length, 1); assert.equal(m.shield, null, 'a grip cannot be the shield'); assert.deepEqual(m.attach, { rivet: { grip: 'g7' } }); assert.equal(m.next, 8);
  assert.deepEqual(L.migrateGear(null), L.defaultGear());
});

test('gear GLB has every model the loot runtime asks for', () => {
  const fs = require('fs'), path = require('path');
  const f = path.join(__dirname, '../../assets/fps-gear.glb');
  const d = fs.readFileSync(f), len = d.readUInt32LE(12), j = JSON.parse(d.toString('utf8', 20, 20 + len));
  const names = new Set(j.nodes.map(n => n.name));
  for (const n of ['GEAR_ShieldCell', 'GEAR_Grip', 'GEAR_Scope', 'GEAR_Scope_EYE', 'GEAR_Acid', 'GEAR_Acid_TIP', 'GEAR_Acid_Glow', 'LOOT_Capsule', 'LOOT_Glow']) assert.ok(names.has(n), 'fps-gear.glb missing ' + n);
  // triangle budgets incl. hull: attachments are viewmodel detail, the capsule is a world prop
  const tris = n => { const node = j.nodes.find(x => x.name === n && x.mesh !== undefined); return j.meshes[node.mesh].primitives.reduce((t, p) => t + j.accessors[p.indices].count / 3, 0); };
  for (const [n, max] of [['GEAR_Grip', 1000], ['GEAR_Scope', 2200], ['GEAR_Acid', 1500], ['GEAR_ShieldCell', 1200], ['LOOT_Capsule', 1200]]) assert.ok(tris(n) <= max, n + ' ' + tris(n) + ' tris > ' + max);
});
