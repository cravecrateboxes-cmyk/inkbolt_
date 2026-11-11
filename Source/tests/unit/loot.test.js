// Loot: drop rolls, rarity odds by level, stat generation and ranges, shield perks, compatibility, weapon modifiers,
// shield and vest math, gear inventory.
const test = require('node:test');
const assert = require('node:assert');
require('../../src/core/rng.js');
require('../../src/data/weapons.js');
require('../../src/data/assets.js');
require('../../src/data/loot.js');
require('../../src/core/loot.js');
const IB = globalThis.IB, L = IB.Loot, T = IB.LOOT;
const RAR = ['common', 'rare', 'epic', 'legendary'];

// small deterministic RNG (mulberry32)
function rng(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const seq = vals => { let i = 0; return () => vals[i++ % vals.length]; };

test('drop chance is about 5 % overall', () => {
  const r = rng(7); let n = 0; const N = 200000;
  for (let i = 0; i < N; i++) if (L.rollDrop(r, { level: 5, cleared: 4 })) n++;
  assert.ok(Math.abs(n / N - 0.05) < 0.003, 'rate ' + n / N);
  assert.equal(T.dropChance, 0.05);
});

test('shields only drop after level 3 is cleared, vests after level 5', () => {
  const r = rng(11), seen = c => { const s = new Set(); for (let i = 0; i < 6000; i++) s.add(L.rollType(r, { cleared: c })); return s; };
  for (const c of [0, 1, 2]) assert.ok(!seen(c).has('shield'), 'no shield with cleared=' + c);
  for (const c of [0, 3, 4]) assert.ok(!seen(c).has('armor'), 'no vest with cleared=' + c);
  const s3 = seen(3);
  for (const t of ['shield', 'grip', 'scope', 'acid', 'mag']) assert.ok(s3.has(t), t + ' after level 3');
  assert.ok(seen(5).has('armor'), 'vests after level 5');
  assert.deepEqual(L.allowedTypes({ cleared: 0 }).map(t => t.id).sort(), ['acid', 'grip', 'mag', 'scope']);
  // the new muzzle cans arrive level by level: Arc after 3, Boom after 5, Void after 7
  assert.deepEqual(L.allowedTypes({ cleared: 7 }).map(t => t.id).filter(t => ['shock', 'blast', 'void'].includes(t)).sort(), ['blast', 'shock', 'void']);
  assert.deepEqual(L.allowedTypes({ cleared: 4 }).map(t => t.id).filter(t => ['shock', 'blast', 'void'].includes(t)), ['shock']);
});

test('rarity odds: levels 1-3 as before (70 / 24 / 6), no legendary before level 6', () => {
  const count = (lv, N) => { const r = rng(3 + lv), c = { common: 0, rare: 0, epic: 0, legendary: 0 }; for (let i = 0; i < N; i++) c[L.rollRarity(r, lv)]++; return c; };
  for (const lv of [undefined, 1, 2, 3]) {
    const N = 60000, c = count(lv, N);
    assert.ok(Math.abs(c.common / N - 0.70) < 0.01, JSON.stringify(c));
    assert.ok(Math.abs(c.rare / N - 0.24) < 0.01, JSON.stringify(c));
    assert.ok(Math.abs(c.epic / N - 0.06) < 0.006, JSON.stringify(c));
    assert.equal(c.legendary, 0);
  }
  for (const lv of [4, 5]) assert.equal(count(lv, 20000).legendary, 0, 'no legendary on level ' + lv);
  const c6 = count(6, 60000); assert.ok(c6.legendary > 0 && Math.abs(c6.legendary / 60000 - 0.03) < 0.004, JSON.stringify(c6));
  const c13 = count(13, 60000); assert.ok(Math.abs(c13.legendary / 60000 - 0.10) < 0.008 && Math.abs(c13.common / 60000 - 0.30) < 0.012, JSON.stringify(c13));
  // the table: every row sums to 100, rarer gets more likely with the level, never less
  let prev = null;
  for (const row of T.rarityOdds) {
    assert.equal(row.w.reduce((a, b) => a + b, 0), 100, 'row from ' + row.from);
    assert.equal(row.w.length, T.rarities.length);
    if (row.from < T.rarityById.legendary.minLevel) assert.equal(row.w[3], 0);
    if (prev) { assert.ok(row.from > prev.from); assert.ok(row.w[0] <= prev.w[0] && row.w[2] >= prev.w[2] && row.w[3] >= prev.w[3], 'row ' + row.from); }
    prev = row;
  }
  assert.deepEqual(L.rarityOdds(99), T.rarityOdds[T.rarityOdds.length - 1].w);
  assert.deepEqual(L.rarityOdds(0), [70, 24, 6, 0]);
});

test('stats stay inside their rarity range (level 1) and rarer is better', () => {
  for (const type of Object.keys(T.types)) {
    const td = T.types[type];
    for (const rar of RAR) {
      assert.ok(td.names[rar], type + ' has a ' + rar + ' name');
      for (const x of [0, 0.5, 0.999]) {
        const it = L.makeItem(type, rar, 1, seq([x]));
        for (const k of Object.keys(td.stats)) {
          const rr = td.stats[k][rar], lo = Math.min(rr[0], rr[1]), hi = Math.max(rr[0], rr[1]), step = td.stats[k].round || 0;
          assert.ok(it.stats[k] >= lo - step && it.stats[k] <= hi + step, type + '.' + k + ' ' + it.stats[k] + ' in ' + rr);
        }
      }
    }
    // the best roll of a rarity never beats the worst roll of the next one
    for (let i = 0; i + 1 < RAR.length; i++) {
      const best = L.makeItem(type, RAR[i], 1, seq([0.999])), worst = L.makeItem(type, RAR[i + 1], 1, seq([0]));
      for (const k of Object.keys(td.stats)) {
        if (td.stats[k][RAR[i]][0] === td.stats[k][RAR[i]][1]) continue;
        if (td.stats[k].better === 'low') assert.ok(worst.stats[k] <= best.stats[k] + 1e-9, type + '.' + k + ' ' + RAR[i + 1]);
        else assert.ok(worst.stats[k] >= best.stats[k] - 1e-9, type + '.' + k + ' ' + RAR[i + 1]);
      }
    }
    // legendary names are their own
    assert.notEqual(td.names.legendary, td.names.epic);
  }
});

test('campaign level scales stats: levels 1-3 as before, faster from level 4, with caps', () => {
  // levels 1-3: the old growth (shield +4 % a level, attachments +1.5 %)
  assert.equal(L.levelMul('shield', 1), 1); assert.equal(L.levelMul('mod', 1), 1);
  assert.ok(Math.abs(L.levelMul('shield', 3) - 1.08) < 1e-9 && Math.abs(L.levelMul('mod', 3) - 1.03) < 1e-9);
  for (let lv = 2; lv <= 20; lv++) {
    assert.ok(L.levelMul('shield', lv) > L.levelMul('shield', lv - 1), 'shield grows on level ' + lv);
    assert.ok(L.levelMul('mod', lv) >= L.levelMul('mod', lv - 1));
  }
  assert.ok(L.levelMul('shield', 99) <= T.levelScale.shield.cap && L.levelMul('mod', 99) <= T.levelScale.mod.cap);
  const s1 = L.makeItem('shield', 'rare', 1, seq([0.5])), s10 = L.makeItem('shield', 'rare', 10, seq([0.5])), s99 = L.makeItem('shield', 'rare', 99, seq([0.5]));
  assert.ok(s10.stats.capacity > s1.stats.capacity && s10.stats.rate > s1.stats.rate);
  assert.ok(s99.stats.capacity <= Math.ceil(T.types.shield.stats.capacity.rare[1] * T.levelScale.shield.cap * (1 + T.types.shield.stats.capacity.curve * 49 * 49)));
  assert.equal(s10.stats.delay, s1.stats.delay, 'delay does not scale');
  const g99 = L.makeItem('grip', 'legendary', 99, seq([0.999]));
  assert.ok(g99.stats.recoil <= T.types.grip.stats.recoil.max && g99.stats.spread <= T.types.grip.stats.spread.max);
  // shields stay useful late: an average cell of the rarity you mostly find soaks a similar share of a health bar on
  // levels 10-13 as on level 4 (player health from core/damage.js: LV = level played)
  require('../../src/core/damage.js');
  const share = (rar, lv) => L.makeItem('shield', rar, lv, seq([0.5])).stats.capacity / IB.Damage.playerMaxHp(lv);
  for (const lv of [10, 11, 12, 13]) assert.ok(share('epic', lv) > share('rare', 4) * 0.95, 'epic on ' + lv + ': ' + share('epic', lv).toFixed(2));
  assert.ok(share('common', 13) > share('common', 4) * 0.9, 'a common cell still counts on level 13');
  // balance: a top legendary cell holds a big share of a health bar, never more than one bar (levels 20-50)
  for (const lv of [20, 30, 40, 50]) {
    const top = L.makeItem('shield', 'legendary', lv, seq([0.999]));
    assert.ok(top.stats.capacity > IB.Damage.playerMaxHp(lv) * 0.7 && top.stats.capacity < IB.Damage.playerMaxHp(lv), 'legendary L' + lv + ' ' + top.stats.capacity);
  }
});

test('items have names, rarity, level and display lines', () => {
  const it = L.makeItem('scope', 'epic', 4, seq([0.5]));
  assert.match(it.name, /^Hawkeye \d\.\dx$/);
  assert.match(L.makeItem('scope', 'legendary', 8, seq([0.5])).name, /^Oracle \d\.\dx$/);
  assert.equal(it.level, 4);
  for (const type of Object.keys(T.types)) {
    const lines = L.statLines(L.makeItem(type, 'rare', 3, seq([0.4])));
    assert.ok(lines.length >= 2 && lines.every(l => l.k && l.v), type);
    assert.ok(L.modelOf({ type, rarity: 'rare' }) === null || /^GEAR_/.test(L.modelOf({ type, rarity: 'rare' })));
  }
  assert.match(L.summary(L.makeItem('grip', 'common', 1, seq([0]))), /Recoil -8% · Spread -4%/);
  assert.match(L.summary(L.makeItem('mag', 'common', 1, seq([0]))), /Magazine \+15% · Reload -4%/);
  assert.match(L.summary(L.makeItem('armor', 'rare', 1, seq([0]))), /Armour -7% dmg · Max health \+10/);
  // a shield model per rarity
  assert.deepEqual(RAR.map(r => L.modelOf({ type: 'shield', rarity: r })), ['GEAR_ShieldCell', 'GEAR_ShieldCell_Rare', 'GEAR_ShieldCell_Epic', 'GEAR_ShieldCell_Legendary']);
});

test('shield perks: Epic and Legendary cells roll one, Common and Rare none', () => {
  const r = rng(21), seen = { overcharge: 0, nova: 0 };
  for (let i = 0; i < 400; i++) {
    for (const rar of ['common', 'rare']) assert.equal(L.makeItem('shield', rar, 8, r).perk, undefined);
    const e = L.makeItem('shield', i % 2 ? 'epic' : 'legendary', 8, r);
    assert.ok(e.perk && T.perks[e.perk.id], JSON.stringify(e.perk));
    seen[e.perk.id]++;
    const rr = T.perks[e.perk.id].v[e.rarity], k = T.perks[e.perk.id].scale ? L.levelMul('shield', 8) : 1;
    assert.ok(e.perk.v >= rr[0] * k - 1 && e.perk.v <= rr[1] * k + 1, e.perk.id + ' ' + e.perk.v);
    if (e.perk.id === 'nova') assert.equal(e.perk.radius, T.perks.nova.radius[e.rarity]);
    assert.ok(L.perkLine(e).name && L.perkLine(e).text);
  }
  assert.ok(seen.overcharge > 100 && seen.nova > 100, JSON.stringify(seen));
  // other types never get one
  assert.equal(L.makeItem('grip', 'legendary', 8, r).perk, undefined);
  assert.equal(L.perkLine(L.makeItem('grip', 'epic', 8, r)), null);
  // legendary perks are stronger
  const pk = (id, rar) => { for (let i = 0; i < 99; i++) { const x = L.makeItem('shield', rar, 8, seq([0.5, 0.5, 0.5, id === 'overcharge' ? 0.1 : 0.9, 0.5])); if (x.perk.id === id) return x.perk.v; } };
  assert.ok(pk('overcharge', 'legendary') > pk('overcharge', 'epic') && pk('nova', 'legendary') > pk('nova', 'epic'));
});

test('attachment compatibility per weapon class', () => {
  const W = IB.WEAPONS, grip = { type: 'grip' }, scope = { type: 'scope' }, acid = { type: 'acid' }, mag = { type: 'mag' }, shield = { type: 'shield' }, vest = { type: 'armor' };
  assert.ok(!L.compatible(grip, 'pip', W.pip), 'no grip on a pistol');
  assert.ok(!L.compatible(scope, 'pip', W.pip), 'no scope on a pistol');
  assert.ok(L.compatible(acid, 'pip', W.pip), 'pistols take a muzzle');
  assert.ok(L.compatible(mag, 'pip', W.pip), 'pistols take a mag');
  assert.ok(!L.compatible(mag, 'handcannon', W.handcannon), 'no magazine on a revolver');
  for (const id of ['buzz', 'rivet']) for (const it of [grip, scope, acid, mag]) assert.ok(L.compatible(it, id, W[id]), it.type + ' on ' + id);
  assert.ok(!L.compatible(scope, 'needle', W.needle) && !L.compatible(scope, 'longtom', W.longtom), 'scoped rifles keep their optics');
  assert.ok(L.compatible(grip, 'needle', W.needle) && L.compatible(mag, 'needle', W.needle));
  assert.ok(!L.compatible(shield, 'rivet', W.rivet) && !L.compatible(vest, 'rivet', W.rivet));
  assert.deepEqual(L.slotsFor('pip', W.pip), ['muzzle', 'mag']);
  assert.deepEqual(L.slotsFor('handcannon', W.handcannon), ['muzzle']);
  assert.deepEqual(L.slotsFor('rivet', W.rivet), ['grip', 'scope', 'muzzle', 'mag']);
  assert.deepEqual(L.slotsFor('needle', W.needle), ['grip', 'muzzle', 'mag']);
  // shotguns take a grip and a mag; melee weapons and grenades nothing
  const sg = { cls: 'shotgun', mag: 6, reload: 0.5 }, melee = { cls: 'melee', mag: 0 };
  assert.deepEqual(L.slotsFor('sg', sg), ['grip', 'muzzle', 'mag']);   // shotguns take the Arc / Boom / Void cans (not acid)
  assert.deepEqual(L.slotsFor('blade', melee), []);
  if (W.frag) assert.deepEqual(L.slotsFor('frag', W.frag), []);
  assert.equal(L.typeForSlot('muzzle'), 'acid'); assert.equal(L.typeForSlot('mag'), 'mag');
  assert.ok(L.isWorn({ type: 'armor' }) && L.isWorn({ type: 'shield' }) && !L.isWorn({ type: 'mag' }) && L.isAttachment({ type: 'mag' }));
});

test('applyMods changes a copy of the weapon def', () => {
  const W = IB.WEAPONS, base = W.rivet, snap = JSON.stringify(base);
  const grip = L.makeItem('grip', 'rare', 1, seq([0.5])), scope = L.makeItem('scope', 'rare', 1, seq([0.5])), acid = L.makeItem('acid', 'epic', 1, seq([0.5]));
  const mag = L.makeItem('mag', 'legendary', 8, seq([0.5]));
  const d = L.applyMods(base, { grip, scope, muzzle: acid, mag });
  assert.equal(JSON.stringify(base), snap, 'table untouched');
  assert.ok(Math.abs(d.recoil - base.recoil * (1 - grip.stats.recoil)) < 1e-9);
  assert.ok(Math.abs(d.spreadHip - base.spreadHip * (1 - grip.stats.spread)) < 1e-9);
  assert.ok(Math.abs(d.spreadAim - base.spreadAim * (1 - grip.stats.spread) * (1 - scope.stats.aimSpread)) < 1e-9);
  assert.ok(Math.abs(d.aimZoom - 1 / scope.stats.zoom) < 1e-9 && d.optic);
  assert.equal(d.acid, acid.stats.acid); assert.equal(d.acidDur, acid.stats.dur); assert.ok(d.quiet < 1);
  assert.equal(d.mag, Math.round(base.mag * (1 + mag.stats.mag))); assert.ok(d.mag > base.mag);
  assert.ok(Math.abs(d.reload - base.reload * (1 - mag.stats.reload)) < 1e-9 && d.reload < base.reload);
  assert.equal(d.damage, base.damage, 'attachments never change raw damage');
  const plain = L.applyMods(base, {});
  assert.equal(plain.recoil, base.recoil); assert.equal(plain.acid, undefined); assert.equal(plain.mag, base.mag);
  // a small magazine always gains at least one round
  const small = L.applyMods({ mag: 5, reload: 2, recoil: 1, spreadHip: 1, spreadAim: 1 }, { mag: L.makeItem('mag', 'common', 1, seq([0])) });
  assert.equal(small.mag, 6);
});

test('shield absorbs damage before health, then recharges after the delay', () => {
  const item = L.makeItem('shield', 'common', 1, seq([0]));   // 22 cap, 5 s delay, 9/s
  const st = L.shieldState(item);
  assert.equal(st.cur, 22);
  let r = L.absorb(st, 17);
  assert.deepEqual([r.through, r.absorbed, r.broke], [0, 17, false]);
  r = L.absorb(st, 9);
  assert.deepEqual([r.through, r.absorbed, r.broke, r.nova], [4, 5, true, false]);
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
  assert.equal(st.cur, 17);
  assert.equal(L.absorb(null, 12).through, 12, 'no shield: all damage goes through');
  assert.equal(L.shieldKill(st), false, 'no perk: a kill does nothing');
});

test('Overcharge: a kill starts the recharge at once and speeds it up', () => {
  const item = L.makeItem('shield', 'epic', 1, seq([0, 0, 0, 0.1, 0.5]));
  assert.equal(item.perk.id, 'overcharge');
  const st = L.shieldState(item), plain = L.shieldState(Object.assign({}, item, { perk: undefined }));
  L.absorb(st, 20); L.absorb(plain, 20);
  assert.equal(L.shieldKill(plain), false);
  assert.ok(L.shieldKill(st));
  assert.equal(L.tickShield(st, 0.1), 'start', 'recharge begins without waiting for the delay');
  assert.equal(L.tickShield(plain, 0.1), null);
  const gain = st.cur - (st.max - 20);
  assert.ok(Math.abs(gain - st.rate * (1 + item.perk.v) * 0.1) < 1e-6, 'boosted rate ' + gain);
  for (let i = 0; i < 50; i++) L.tickShield(st, 0.1);
  assert.equal(st.boostT, 0, 'the boost runs out');
  L.tickShield(st, 99); assert.equal(st.cur, st.max);
  assert.equal(L.shieldKill(st), false, 'a full cell needs no overcharge');
});

test('Nova: fires once when the cell breaks, re-arms when it is full again', () => {
  const item = L.makeItem('shield', 'legendary', 6, seq([0, 0, 0, 0.9, 0.5]));
  assert.equal(item.perk.id, 'nova'); assert.equal(item.perk.radius, 6);
  const st = L.shieldState(item);
  let r = L.absorb(st, 10); assert.equal(r.nova, false);
  r = L.absorb(st, 999); assert.ok(r.broke && r.nova, 'breaking the cell fires the burst');
  for (let i = 0; i < 40; i++) L.tickShield(st, 0.1);   // part recharge
  assert.ok(st.cur > 0 && st.cur < st.max);
  r = L.absorb(st, 999); assert.ok(r.broke && !r.nova, 'not again before the cell was full');
  let ev = null; for (let i = 0; i < 200 && ev !== 'full'; i++) ev = L.tickShield(st, 0.1);
  assert.equal(ev, 'full');
  r = L.absorb(st, 999); assert.ok(r.nova, 're-armed once full');
});

test('armour vest: damage reduction after the shield, extra max health', () => {
  const v = L.makeItem('armor', 'epic', 1, seq([0.5]));
  const a = L.armorOf(v);
  assert.ok(a.dr >= 0.10 && a.dr <= 0.13 && a.hp >= 16 && a.hp <= 24, JSON.stringify(a));
  assert.ok(Math.abs(L.armorCut(v, 100) - 100 * (1 - a.dr)) < 1e-9);
  assert.equal(L.armorCut(null, 40), 40);
  assert.deepEqual(L.armorOf(null), { dr: 0, hp: 0 });
  assert.ok(L.armorOf(L.makeItem('armor', 'legendary', 99, seq([0.999]))).dr <= T.types.armor.stats.dr.max);
  assert.ok(L.makeItem('armor', 'rare', 13, seq([0.5])).stats.hp > L.makeItem('armor', 'rare', 1, seq([0.5])).stats.hp, 'vest health grows with the level');
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
  // mags ride the guns like any attachment; vests are worn like the shield
  const mg = L.addItem(g, L.makeItem('mag', 'epic', 4, r)), vs = L.addItem(g, L.makeItem('armor', 'rare', 6, r));
  assert.ok(L.attach(g, 'buzz', W.buzz, mg.id)); assert.equal(L.weaponItems(g, 'buzz').mag.id, mg.id);
  assert.ok(!L.equipWorn(g, 'shield', vs.id), 'a vest is not a shield');
  assert.ok(!L.equipWorn(g, 'armor', mg.id), 'a mag is not a vest');
  assert.ok(!L.equipWorn(g, 'hat', vs.id), 'unknown slot');
  assert.ok(L.equipWorn(g, 'armor', vs.id)); assert.equal(L.worn(g, 'armor').id, vs.id); assert.equal(L.wornSlot(g, vs.id), 'armor');
  assert.ok(L.equipWorn(g, 'armor', null)); assert.equal(g.armor, null);
  L.equipWorn(g, 'armor', vs.id); assert.ok(L.discard(g, vs.id)); assert.equal(g.armor, null);
  // bag cap
  const full = L.defaultGear();
  for (let i = 0; i < T.invCap; i++) assert.ok(L.addItem(full, L.makeItem('grip', 'common', 1, r)));
  assert.equal(L.addItem(full, L.makeItem('grip', 'common', 1, r)), null);
  // migrate drops junk and dangling refs, keeps ids unique and next past them
  const m = L.migrateGear({ inv: [{ id: 'g7', type: 'grip', rarity: 'rare', stats: { recoil: 0.1, spread: 0.1 } }, { id: 'g8', type: 'laser', rarity: 'rare', stats: {} }, 5],
    shield: 'g7', attach: { rivet: { grip: 'g7', scope: 'g99' } }, next: 2 });
  assert.equal(m.inv.length, 1); assert.equal(m.shield, null, 'a grip cannot be the shield'); assert.deepEqual(m.attach, { rivet: { grip: 'g7' } }); assert.equal(m.next, 8);
  assert.deepEqual(L.migrateGear(null), L.defaultGear());
  // an old save (no vest slot, no legendary, no perks) keeps everything; new fields survive a round trip
  const old = { inv: [{ id: 'g1', type: 'shield', rarity: 'epic', level: 5, name: 'Storm Cell', stats: { capacity: 40, delay: 3.4, rate: 15 } },
    { id: 'g2', type: 'acid', rarity: 'common', level: 2, name: 'Fizz Can', stats: { acid: 0.15, dur: 2 } }], shield: 'g1', attach: { pip: { muzzle: 'g2' } }, next: 3, found: 2, starter: true };
  const mo = L.migrateGear(JSON.parse(JSON.stringify(old)));
  assert.equal(mo.inv.length, 2); assert.equal(mo.shield, 'g1'); assert.equal(mo.armor, null); assert.equal(mo.starter, true); assert.equal(mo.starterVest, undefined);
  assert.deepEqual(mo.attach, { pip: { muzzle: 'g2' } });
  const now = L.defaultGear(); now.starter = now.starterVest = true;
  const lg = L.addItem(now, L.makeItem('shield', 'legendary', 9, r)), lv = L.addItem(now, L.makeItem('armor', 'legendary', 9, r)), lm = L.addItem(now, L.makeItem('mag', 'legendary', 9, r));
  L.equipShield(now, lg.id); L.equipWorn(now, 'armor', lv.id); L.attach(now, 'rivet', W.rivet, lm.id);
  const back = L.migrateGear(JSON.parse(JSON.stringify(now)));
  assert.deepEqual(back, JSON.parse(JSON.stringify(now)), 'a current gear object passes through unchanged');
  assert.ok(back.inv[0].perk, 'the perk is kept');
  // a broken perk is dropped, the item kept
  const bad = L.migrateGear({ inv: [{ id: 'g1', type: 'shield', rarity: 'epic', stats: { capacity: 40, delay: 3, rate: 15 }, perk: { id: 'laser' } }], shield: 'g1' });
  assert.equal(bad.inv.length, 1); assert.equal(bad.inv[0].perk, undefined); assert.equal(bad.shield, 'g1');
});

test('gear GLB has every model the loot runtime asks for', () => {
  const fs = require('fs'), path = require('path');
  const f = path.join(__dirname, '../../assets/fps-gear.glb');
  const d = fs.readFileSync(f), len = d.readUInt32LE(12), j = JSON.parse(d.toString('utf8', 20, 20 + len));
  const names = new Set(j.nodes.map(n => n.name));
  const want = ['GEAR_ShieldCell', 'GEAR_Grip', 'GEAR_Scope', 'GEAR_Scope_EYE', 'GEAR_Acid', 'GEAR_Acid_TIP', 'GEAR_Acid_Glow', 'GEAR_Mag', 'GEAR_Vest', 'LOOT_Capsule', 'LOOT_Glow'];
  Object.keys(T.types).forEach(k => RAR.forEach(r => { const m = L.modelOf({ type: k, rarity: r }); if (m) want.push(m); }));
  for (const n of want) assert.ok(names.has(n), 'fps-gear.glb missing ' + n);
  // triangle budgets incl. hull: attachments are viewmodel detail, the capsule is a world prop
  const tris = n => { const node = j.nodes.find(x => x.name === n && x.mesh !== undefined); return j.meshes[node.mesh].primitives.reduce((t, p) => t + j.accessors[p.indices].count / 3, 0); };
  for (const [n, max] of [['GEAR_Grip', 1000], ['GEAR_Scope', 2200], ['GEAR_Acid', 1500], ['GEAR_ShieldCell', 1200], ['GEAR_ShieldCell_Rare', 1500], ['GEAR_ShieldCell_Epic', 1800],
    ['GEAR_ShieldCell_Legendary', 2200], ['GEAR_Mag', 1000], ['GEAR_Vest', 2000], ['LOOT_Capsule', 1200]]) assert.ok(tris(n) <= max, n + ' ' + tris(n) + ' tris > ' + max);
});

test('armour can be excluded from a drop context (crawlers and bombers never drop armour)', () => {
  const ctx = { cleared: 20, level: 10 };
  assert.ok(L.allowedTypes(ctx).some((t) => t.id === 'armor'), 'armour is in the table by default');
  assert.ok(!L.allowedTypes(Object.assign({ exclude: ['armor'] }, ctx)).some((t) => t.id === 'armor'), 'excluded');
  let armour = 0;
  for (let i = 0; i < 4000; i++) { const it = L.rollDrop(Math.random, Object.assign({ chance: 1, exclude: ['armor'] }, ctx)); if (it && it.type === 'armor') armour++; }
  assert.equal(armour, 0);
});

test('legendary gun attachments: one roll in three stays Legendary, the rest come down to Epic or Rare; cells and vests keep theirs', () => {
  assert.ok(Math.abs(T.legendaryAttachKeep - 1 / 3) < 1e-9);
  const r = rng(77), N = 30000, c = { legendary: 0, epic: 0, rare: 0, common: 0 };
  for (let i = 0; i < N; i++) c[L.dropRarity('grip', 'legendary', r)]++;
  assert.equal(c.common, 0);
  assert.ok(Math.abs(c.legendary / N - 1 / 3) < 0.012, JSON.stringify(c));
  assert.ok(Math.abs(c.epic / N - 1 / 3) < 0.012 && Math.abs(c.rare / N - 1 / 3) < 0.012, JSON.stringify(c));
  // every attachment type is covered, worn gear is not; other rarities pass through untouched
  Object.keys(T.types).forEach((k) => {
    const att = T.slots.indexOf(T.types[k].slot) >= 0;
    let kept = 0; for (let i = 0; i < 300; i++) if (L.dropRarity(k, 'legendary', r) === 'legendary') kept++;
    if (att) assert.ok(kept > 60 && kept < 140, k + ' ' + kept); else assert.equal(kept, 300, k);
    for (const q of ['common', 'rare', 'epic']) assert.equal(L.dropRarity(k, q, r), q);
  });
  // through the real drop roll on a late level: attachments turn up Legendary about a third as often as the odds table says
  const ctx = { level: 17, cleared: 16, chance: 1 }, odds = L.rarityOdds(17)[3] / 100;
  let att = 0, attLeg = 0, worn = 0, wornLeg = 0;
  for (let i = 0; i < 60000; i++) {
    const it = L.rollDrop(r, ctx);
    if (L.isAttachment(it)) { att++; if (it.rarity === 'legendary') attLeg++; } else { worn++; if (it.rarity === 'legendary') wornLeg++; }
  }
  assert.ok(Math.abs(attLeg / att - odds / 3) < 0.006, 'attachments ' + (attLeg / att).toFixed(4));
  assert.ok(Math.abs(wornLeg / worn - odds) < 0.012, 'worn ' + (wornLeg / worn).toFixed(4));
});

test('bag size grows with the player level: 16 at LV 1, a slot or two a level, the full 40 from LV 20', () => {
  assert.equal(L.bagCap(1), T.invStart); assert.equal(T.invStart, 16);
  assert.equal(L.bagCap(T.invCapLevel), T.invCap); assert.equal(L.bagCap(30), T.invCap); assert.equal(L.bagCap(99), T.invCap);
  assert.equal(L.bagCap(0), T.invStart); assert.equal(L.bagCap(undefined), T.invStart);
  for (let lv = 2; lv <= T.invCapLevel; lv++) {
    const step = L.bagCap(lv) - L.bagCap(lv - 1);
    assert.ok(step >= 1 && step <= 2, 'LV ' + lv + ' adds ' + step);
  }
  assert.deepEqual([1, 5, 10, 15, 20].map(L.bagCap), [16, 21, 27, 34, 40]);
  // addItem honours the size it is given
  const g = L.defaultGear(), r = rng(5);
  for (let i = 0; i < 16; i++) assert.ok(L.addItem(g, L.makeItem('grip', 'common', 1, r), L.bagCap(1)));
  assert.equal(L.addItem(g, L.makeItem('grip', 'common', 1, r), L.bagCap(1)), null, 'full at LV 1');
  assert.ok(L.addItem(g, L.makeItem('grip', 'common', 1, r), L.bagCap(2)), 'room again at LV 2');
});
