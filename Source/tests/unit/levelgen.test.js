'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/saves', 'core/levelgen']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const LG = IB.LevelGen;

// ---- synthetic template library: 30 valid zones 20x20..40x40, plus 2 deliberately broken ones ----
function makeTemplate(seed) {
  const rng = IB.RNG.mulberry32(seed);
  const w = 20 + Math.floor(rng() * 21), h = 20 + Math.floor(rng() * 21);
  const g = [];
  for (let z = 0; z < h; z++) {
    const row = [];
    for (let x = 0; x < w; x++) row.push(x === 0 || z === 0 || x === w - 1 || z === h - 1 ? '#' : '.');
    g.push(row);
  }
  const mid = Math.floor(h / 2);
  g[mid][2] = 'P';
  g[mid][w - 1] = 'G';
  g[2][3] = 'a';
  if (rng() < 0.5) g[h - 3][w - 4] = 'h';
  // interior wall with a 3-cell gap
  const wx = Math.floor(w / 2);
  const gap = 2 + Math.floor(rng() * (h - 7));
  for (let z = 1; z < h - 1; z++) if (z < gap || z > gap + 2) g[z][wx] = '#';
  const free = (x, z) => g[z][x] === '.' && Math.abs(z - mid) > 1 && x !== wx - 1 && x !== wx + 1 && x > 1 && x < w - 2 && z > 1 && z < h - 2;
  // cover: crates, a low wall, a container (2x2)
  let placed = 0;
  while (placed < 6) {
    const x = 1 + Math.floor(rng() * (w - 2)), z = 1 + Math.floor(rng() * (h - 2));
    if (free(x, z)) { g[z][x] = 'c'; placed++; }
  }
  g[h - 3][4] = '='; g[h - 3][5] = '=';
  g[3][w - 6] = 'C'; g[3][w - 5] = 'C'; g[4][w - 6] = 'C'; g[4][w - 5] = 'C';
  g[h - 2][Math.floor(w / 4)] = 'p';
  // spawns at least 10 m from P
  let s = 0;
  const want = 6 + Math.floor(rng() * 5);
  while (s < want) {
    const x = 12 + Math.floor(rng() * (w - 13)), z = 1 + Math.floor(rng() * (h - 2));
    if (g[z][x] === '.') { g[z][x] = 'S'; s++; }
  }
  return g.map((r) => r.join('')).join('\n');
}

const GOOD = [];
for (let i = 0; i < 30; i++) GOOD.push(makeTemplate(1000 + i));
const NO_AMMO = GOOD[0].replace('a', '.');
const ENCLOSED = [
  '##########################',
  '#........................#',
  '#.a..c.....c.....###.....#',
  '#.................#S#....#',
  '#P.....c.....c....###....G',
  '#...........S............#',
  '#.........=..............#',
  '#........................#',
  '##########################'
].join('\n');
const LIB = GOOD.concat([NO_AMMO, ENCLOSED]);
const BAD = new Set([30, 31]);

test('synthetic library: 30 valid templates, broken ones rejected for the right reason', () => {
  GOOD.forEach((t, i) => {
    const v = LG.validate(t);
    assert.ok(v.ok, 'template ' + i + ': ' + v.errors.join('; '));
    const z = LG.parseZone(t);
    assert.ok(z.w >= 20 && z.w <= 40 && z.h >= 20 && z.h <= 40);
  });
  assert.ok(LG.validate(NO_AMMO).errors.includes('no ammo box'));
  assert.ok(LG.validate(ENCLOSED).errors.some((e) => /enclosed/.test(e)));
});

test('validate catches each rule', () => {
  const base = [
    '####################',
    '#..................#',
    '#.a..c....c........#',
    '#..................#',
    '#P........S.......SG',
    '#.....c.......c....#',
    '####################'
  ];
  const ok = LG.validate(base);
  assert.ok(ok.ok, ok.errors.join('; '));
  assert.equal(ok.cover, 4);
  const set = (rows, x, z, ch) => rows.map((r, i) => (i === z ? r.slice(0, x) + ch + r.slice(x + 1) : r));
  // path blocked
  let r = base.map((row, i) => (i > 0 && i < 6 ? row.slice(0, 15) + '#' + row.slice(16) : row));
  assert.ok(LG.validate(r).errors.includes('no path P to G'));
  // spawn too close to P (7 cells)
  r = set(base, 8, 4, 'S');
  assert.ok(LG.validate(r).errors.some((e) => /within 8 m/.test(e)));
  // fewer than 4 cover pieces
  r = set(base, 5, 2, '.');
  assert.ok(LG.validate(r).errors.some((e) => /cover/.test(e)));
  // adjacent crates count as one piece
  r = set(set(base, 5, 2, '.'), 11, 2, 'c');
  assert.equal(LG.validate(r).cover, 3);
  // no G, no P
  assert.ok(LG.validate(set(base, 19, 4, '#')).errors.includes('no exit G'));
  assert.ok(LG.validate(set(base, 1, 4, '.')).errors.includes('no entry P'));
  // generated robot spawn too close
  assert.ok(LG.validate({ grid: base, spawns: [{ type: 'crawler', x: 3.5, z: 4.5 }] }).errors.some((e) => /robot spawn/.test(e)));
  // oversize
  const big = ['#'.repeat(41)].concat(base.slice(1));
  assert.ok(LG.validate(big).errors.some((e) => /exceeds/.test(e)));
});

test('parseZone helpers and transforms', () => {
  const z = LG.parseZone('\n##\n#P S\n');
  assert.equal(z.w, 4); assert.equal(z.h, 2);
  assert.deepEqual(z.rows, ['##..', '#P.S']);
  assert.equal(z.at(1, 1), 'P'); assert.equal(z.at(-1, 0), '#'); assert.equal(z.blocked(0, 0), true); assert.equal(z.blocked(2, 1), false);
  assert.deepEqual(z.find('S'), [{ x: 3, z: 1 }]);
  const t = LG.parseZone(GOOD[3]).rows;
  assert.deepEqual(LG.transform(t, 4, false), t);
  assert.deepEqual(LG.transform(LG.transform(t, 1, false), 3, false), t);
  assert.deepEqual(LG.transform(LG.transform(t, 0, true), 0, true), t);
  const r1 = LG.transform(t, 1, false);
  assert.equal(r1.length, t[0].length); assert.equal(r1[0].length, t.length);
  assert.deepEqual(LG.transform(['ab', 'cd'], 1, false), ['ca', 'db']);
  assert.deepEqual(LG.transform(['ab', 'cd'], 0, true), ['ba', 'dc']);
  for (let rot = 0; rot < 4; rot++) for (const m of [false, true]) assert.ok(LG.validate(LG.transform(t, rot, m)).ok);
});

function checkLevel(lv, L) {
  assert.equal(lv.level, L);
  assert.ok(IB.THEMES[lv.theme], 'theme');
  assert.equal(lv.zones.length, Math.min(7, 4 + Math.floor((L - 20) / 10)));
  assert.equal(lv.valid, true);
  assert.equal(lv.boss, L % 5 === 0 ? IB.bossForLevel(L) : null);
  const budget = 8 + 1.6 * L;
  for (const z of lv.zones) {
    assert.equal(z.valid, true);
    assert.ok(!BAD.has(z.template), 'broken template used');
    const v = LG.validate({ grid: z.grid, spawns: z.spawns });
    assert.ok(v.ok, v.errors.join('; '));
    const counts = {};
    let spent = 0;
    for (const s of z.spawns) {
      counts[s.type] = (counts[s.type] || 0) + 1;
      spent += IB.ENEMIES[s.type].cost;
      assert.ok(IB.ENEMIES[s.type].first <= L);
      assert.equal(z.grid[Math.floor(s.z)][Math.floor(s.x)], 'S', 'spawn sits on an S cell');
      assert.ok(s.wave >= 0 && s.wave < 3);
    }
    assert.ok((counts.bruiser || 0) <= 2, 'bruiser cap');
    assert.ok((counts.binhive || 0) <= 1, 'bin hive cap');
    assert.ok(spent <= budget + 1e-9, 'budget');
    assert.ok(budget - spent < 1, 'budget used up (crawler costs 1)');
    assert.ok(Math.abs(z.spent - spent) < 1e-9);
  }
}

test('500 seeds for levels 21 to 60 all pass validation, deterministic, caps respected', () => {
  let hives = 0, bruisers = 0, reseeded = 0;
  for (let i = 0; i < 500; i++) {
    const L = 21 + (i % 40);
    const seed = (i * 2654435761) >>> 0;
    const a = LG.generate(L, seed, LIB);
    checkLevel(a, L);
    const b = LG.generate(L, seed, LIB);
    assert.deepEqual(a, b, 'deterministic');
    for (const z of a.zones) { hives += z.counts.binhive || 0; bruisers += z.counts.bruiser || 0; if (z.attempts > 1) reseeded++; }
  }
  assert.ok(hives > 0 && bruisers > 0, 'capped types do appear');
  assert.ok(reseeded > 0, 'broken templates were drawn and rejected (reseed path exercised)');
});

test('different seeds give different levels; theme order fixed per slot', () => {
  const a = LG.generate(30, 1, LIB), b = LG.generate(30, 2, LIB);
  assert.notDeepEqual(a.zones.map((z) => z.grid), b.zones.map((z) => z.grid));
  const order = LG.themeOrder(1234);
  assert.equal(new Set(order).size, 18);
  for (let L = 21; L < 21 + 36; L++) assert.equal(LG.generate(L, 1234, LIB).theme, order[(L - 21) % 18]);
  assert.deepEqual(LG.themeOrder(1234), order);
  assert.equal(LG.zoneCount(21), 4); assert.equal(LG.zoneCount(30), 5); assert.equal(LG.zoneCount(50), 7); assert.equal(LG.zoneCount(90), 7);
  assert.equal(LG.budget(25), 48);
  const boss = LG.generate(45, 9, LIB);
  assert.equal(boss.boss, 'skimmer'); assert.equal(boss.arena, true); assert.equal(boss.bossScale.hpMul, 1.7);
  assert.throws(() => LG.generate(30, 1, []));
});

test('robots limited to those introduced by level L', () => {
  const lv = LG.generate(9, 5, LIB);
  for (const z of lv.zones) for (const s of z.spawns) assert.ok(IB.ENEMIES[s.type].first <= 9);
  assert.ok(lv.zones.every((z) => !z.counts.binhive));
});

test('only broken templates -> zones flagged invalid, no throw', () => {
  const lv = LG.generate(30, 3, [NO_AMMO, ENCLOSED]);
  assert.equal(lv.valid, false);
  assert.ok(lv.zones.every((z) => z.valid === false && z.spawns.length === 0 && z.attempts === 10));
});

test('gem income can be estimated from a generated level', () => {
  const lv = LG.generate(30, 77, LIB);
  const inc = IB.Gems.levelIncome(30, { level: lv });
  assert.ok(inc.robots > 0 && inc.boss === 90 && inc.clear === 165);
});
