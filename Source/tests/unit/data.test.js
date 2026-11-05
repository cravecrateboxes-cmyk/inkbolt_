'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/saves', 'core/levelgen']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const W = IB.WEAPONS;

test('weapon table numbers (5.2)', () => {
  const rows = {
    // id: [damage, rpm, hip, aim, recoil, recoilH, reload, mag, reserve, slot, cls, fire]
    // pistol fire rates raised from the brief at the user's request (pip 300->450, handcannon 110->150, twintap 220->300 bursts)
    pip: [18, 450, 0.8, 0.3, 1.2, 0.3, 1.1, 12, Infinity, 1, 'pistol', 'semi'],
    handcannon: [55, 150, 0.5, 0.15, 4.0, 0.8, 2.2, 6, 36, 1, 'pistol', 'semi'],
    twintap: [16, 300, 1.0, 0.4, 0.9, 0, 1.3, 16, 96, 1, 'pistol', 'burst'],
    buzz: [11, 900, 2.2, 1.2, 0.5, 0.4, 1.6, 30, 180, 2, 'smg', 'auto'],
    whisk: [8, 1100, 3.2, 2.0, 0.35, 0.6, 1.4, 40, 240, 2, 'smg', 'auto'],
    hornet: [14, 750, 1.4, 0.6, 0.6, 0.25, 1.8, 32, 192, 2, 'smg', 'auto'],
    rivet: [22, 600, 1.4, 0.4, 0.9, 0.3, 2.0, 30, 180, 3, 'rifle', 'auto'],
    triplet: [26, 1000, 1.0, 0.25, 0.8, 0, 2.2, 24, 144, 3, 'rifle', 'burst'],
    longtom: [60, 240, 0.6, 0.05, 2.8, 0.4, 2.4, 10, 60, 3, 'rifle', 'semi'],
    brick: [26, 500, 2.0, 0.8, 1.1, 0.5, 3.4, 60, 240, 3, 'rifle', 'auto'],
    needle: [160, 45, 4.0, 0, 6.0, 0, 3.0, 5, 25, 4, 'sniper', 'bolt'],
    cancannon: [140, 40, 0.3, 0.3, 5.0, 0, 2.6, 1, 8, 5, 'rocket', 'projectile'],
    scrapper: [9, 70, 6.0, 4.5, 3.5, 0, 0.5, 6, 36, 9, 'shotgun', 'pump']
  };
  for (const [id, r] of Object.entries(rows)) {
    const w = W[id];
    assert.deepEqual([w.damage, w.rpm, w.spreadHip, w.spreadAim, w.recoil, w.recoilH, w.reload, w.mag, w.reserve, w.slot, w.cls, w.fire], r, id);
  }
  assert.equal(W.twintap.burst, 2); assert.ok(Math.abs(W.twintap.cycle - 60 / 300) < 1e-12);
  assert.equal(W.triplet.burst, 3); assert.equal(W.triplet.cycle, 0.32);
  assert.ok(Math.abs(W.pip.cycle - 60 / 450) < 1e-12);
  assert.equal(W.longtom.aimZoom, 0.67); assert.equal(W.pip.aimZoom, 0.85); assert.equal(W.needle.scopeZoom, 3.5);
  assert.equal(W.brick.moveMul, 0.9); assert.equal(W.pip.moveMul, 1);
  assert.equal(W.needle.pierce, 2); assert.equal(W.pip.pierce, 0);
  assert.equal(W.needle.coreMul, 2.5); assert.equal(W.longtom.coreMul, 2.0); assert.equal(W.buzz.coreMul, 1.75);
  assert.equal(W.scrapper.pellets, 9); assert.equal(W.scrapper.unlock, 25); assert.equal(W.scrapper.reloadPerShell, true);
  assert.equal(W.cancannon.splash, 120); assert.equal(W.cancannon.radius, 4); assert.equal(W.cancannon.speed, 28);
  assert.deepEqual([W.frag.damage, W.frag.radius, W.frag.fuse, W.frag.carry, W.frag.speed, W.frag.cycle], [150, 5, 2.2, 3, 18, 0.45]);
  assert.deepEqual([W.popflash.damage, W.popflash.radius, W.popflash.fuse, W.popflash.carry, W.popflash.blind], [10, 10, 1.5, 2, 3.5]);
  assert.deepEqual([W.katana.damage, W.katana.cycle, W.katana.arc, W.katana.range, W.katana.windup, W.katana.active, W.katana.recovery, W.katana.comboMul],
    [45, 0.38, 100, 2.6, 0.08, 0.10, 0.20, 1.6]);
  assert.deepEqual([W.fireaxe.damage, W.fireaxe.charged, W.fireaxe.cycle, W.fireaxe.arc, W.fireaxe.range, W.fireaxe.windup, W.fireaxe.active, W.fireaxe.recovery, W.fireaxe.chargeTime],
    [75, 150, 0.75, 70, 2.3, 0.18, 0.12, 0.45, 0.8]);
  assert.equal(W.frag.slot, 'Q'); assert.equal(W.katana.slot, 6);
});

test('every weapon has the required fields and names', () => {
  const names = ['P-12 Warden', 'R-50 Ironjaw', 'P-16 Twinfire', 'KV-9 Buzzsaw', 'KV-4 Whiplash', 'KV-7 Hornet', 'AR-22 Rivet',
    'AR-3 Tribolt', 'DMR-60 Longtom', 'LMG-26 Bricklayer', 'SR-160 Needle', 'RL-1 Canister', 'M-15 Frag Can', 'FX-2 Pop Flash',
    'Mk-1 Ronin Blade', 'BA-7 Breacher Axe', 'SG-9 Scrapper'];
  assert.deepEqual(IB.WEAPON_ORDER.map((id) => W[id].name), names);
  assert.equal(Object.keys(W).length, 17);
  for (const w of Object.values(W)) {
    for (const f of ['id', 'name', 'cls', 'slot', 'fire', 'damage', 'pellets', 'burst', 'rpm', 'cycle', 'spreadHip', 'spreadAim',
      'recoil', 'recoilH', 'reload', 'mag', 'reserve', 'unlock', 'aimZoom', 'moveMul', 'pierce', 'coreMul', 'sound']) {
      assert.ok(w[f] !== undefined, w.id + '.' + f);
    }
    assert.ok(Number.isFinite(w.cycle) && w.cycle > 0, w.id + ' cycle');
    assert.ok(Number.isFinite(w.reload), w.id + ' reload finite');
  }
  assert.deepEqual(IB.WEAPON_CLASSES, ['pistol', 'smg', 'rifle', 'sniper', 'rocket', 'melee']);
  assert.equal(IB.GLB_WEAPON_NAMES.length, 17);
  assert.ok(IB.GLB_WEAPON_NAMES.includes('WPN_PIP') && IB.GLB_WEAPON_NAMES.includes('WPN_FRAG'));
});

test('robot table (5.7)', () => {
  const E = IB.ENEMIES;
  const rows = {
    crawler: [1, 30, 5.0, 8, 1, 0, 1], gunner: [2, 55, 3.0, 6, 2, 0, 2], bomber: [3, 25, 4.2, 35, 2, 0, 1.5],
    tosser: [4, 60, 2.6, 20, 3, 0, 2.5], drone: [6, 35, 4.5, 5, 3, 0, 2], shieldbot: [7, 90, 2.4, 18, 0, 1, 4],
    bruiser: [8, 260, 2.2, 25, 3, 1, 6], binhive: [11, 200, 0, 0, 0, 2, 7]
  };
  for (const [id, r] of Object.entries(rows)) {
    const e = E[id];
    assert.deepEqual([e.first, e.hp, e.speed, e.damage, e.gems.chip, e.gems.shard, e.cost], r, id);
    assert.ok(e.windup >= 0.35 && e.windup <= 0.9, id + ' windup');
    assert.ok(e.radius > 0 && e.height > 0 && e.coreRadius > 0 && e.coreOffset.length === 3, id + ' collision');
    assert.match(e.color, /^#[0-9A-F]{6}$/);
  }
  assert.equal(E.shieldbot.shield, 150); assert.equal(E.bruiser.chargeSpeed, 9); assert.equal(E.bruiser.chargeDamage, 30);
  assert.equal(E.tosser.dot, 5); assert.equal(E.crawler.windup, 0.35); assert.equal(E.bomber.windup, 0.6);
  assert.equal(E.shieldbot.windup, 0.6); assert.equal(E.bruiser.windup, 0.9); assert.equal(E.drone.hover, 3);
  for (const id of ['gunner', 'tosser', 'drone']) assert.deepEqual(E[id].keepDistance, [8, 16]);
  assert.equal(IB.GLB_BOT_NAMES.length, 8);
});

test('bosses (5.8) and rotation', () => {
  const B = IB.BOSSES;
  assert.deepEqual(['skimmer', 'dumpstertank', 'cartcolossus', 'compactorprime'].map((id) => [B[id].level, B[id].hp, B[id].gems.core, B[id].gems.shard]),
    [[5, 2500, 2, 2], [10, 4500, 3, 3], [15, 7000, 4, 4], [20, 11000, 6, 6]]);
  for (const b of Object.values(B)) for (const f of ['arena', 'mechanic', 'tell', 'window']) assert.ok(b[f], b.id + '.' + f);
  assert.equal(IB.bossForLevel(5), 'skimmer'); assert.equal(IB.bossForLevel(20), 'compactorprime');
  assert.equal(IB.bossForLevel(25), 'skimmer'); assert.equal(IB.bossForLevel(30), 'dumpstertank');
  assert.equal(IB.bossForLevel(35), 'cartcolossus'); assert.equal(IB.bossForLevel(40), 'compactorprime');
  assert.equal(IB.bossForLevel(45), 'skimmer'); assert.equal(IB.bossForLevel(21), null);
  for (let l = 1; l <= 20; l++) assert.equal(IB.bossForLevel(l), IB.LEVELS[l].boss, 'L' + l);
  assert.equal(IB.isBossLevel(5), true); assert.equal(IB.isBossLevel(6), false); assert.equal(IB.isBossLevel(0), false);
  assert.deepEqual([IB.bossScale(20).hpMul, IB.bossScale(20).modifiers], [1, 0]);
  assert.deepEqual([IB.bossScale(25).hpMul, IB.bossScale(25).modifiers], [1.35, 1]);
  assert.deepEqual([IB.bossScale(40).hpMul, IB.bossScale(40).modifiers], [1.35, 1]);
  assert.deepEqual([IB.bossScale(45).hpMul, IB.bossScale(45).modifiers], [1.7, 2]);
});

test('themes and level plan (6)', () => {
  assert.equal(Object.keys(IB.THEMES).length, 18);
  assert.deepEqual(Object.keys(IB.THEMES).sort(), IB.THEME_ORDER.slice().sort());
  for (const t of Object.values(IB.THEMES)) {
    assert.equal(t.palette.length, 4);
    t.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
  }
  assert.equal(IB.LEVELS.length, 21); assert.equal(IB.LEVELS[0], null);
  const tiny = [1, 2, 3, 4];
  for (let l = 1; l <= 20; l++) {
    const lv = IB.LEVELS[l];
    assert.equal(lv.level, l);
    assert.ok(IB.THEMES[lv.theme], 'theme ' + lv.theme);
    assert.equal(lv.scale, tiny.includes(l) ? 'tiny' : (l === 12 || l === 15 ? 'huge' : 'full'));
    assert.equal(lv.arena, IB.isBossLevel(l));
    for (const id of Object.keys(lv.mix)) assert.ok(IB.ENEMIES[id].first <= l, `L${l} ${id} before its first level`);
  }
  assert.deepEqual(IB.LEVELS[1].mix, { crawler: 18 });
  assert.deepEqual(IB.LEVELS[20].mix, { crawler: 16, gunner: 10, bomber: 8, tosser: 6, drone: 8, shieldbot: 6, bruiser: 4, binhive: 2 });
  assert.equal(IB.LEVELS[11].theme, 'toytown'); assert.equal(IB.LEVELS[11].variant, 'lot');
  assert.equal(IB.LEVELS[15].theme, 'stockpile'); assert.equal(IB.LEVELS[15].variant, 'dock');
  assert.deepEqual(IB.LEVELS.slice(1).map((l) => l.zones), [3, 3, 3, 4, 3, 4, 4, 4, 4, 3, 5, 5, 5, 5, 4, 5, 5, 6, 6, 4]);
  assert.equal(IB.LEVELS[1].name, "Kid's Bedroom");
});
