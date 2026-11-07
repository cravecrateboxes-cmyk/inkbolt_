// Redwood Hollow theme (kit-grove): level plan, zone maps (size, edges, gates, reachability, spawns, prefab tiling),
// the 9 m walkway layer (bridges join climbable redwoods east-west, the platform rails close every footprint edge
// except bridge landings and the stairwell, piers stand under the bridges, nothing tall grows into the walkways) and
// the wall chooser (every '#' cell resolves to a kit piece, or to nothing only where a gate frame, a corner pile or a
// neighbouring 2 m module covers it).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/grove.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.grove;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function grid(rows) {
  const w = Math.max(...rows.map((r) => r.length));
  const padded = rows.map((r) => r.padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? '#' : padded[r][c] };
}
function parse(text) {
  const lines = text.replace(/\r/g, '').split('\n'), base = [], layers = {};
  let cur = base;
  for (const l of lines) { const m = /^@layer\s+(-?[\d.]+)/.exec(l); if (m) { cur = []; layers[m[1]] = cur; } else if (l.length) cur.push(l); }
  return { g: grid(base), layers: Object.fromEntries(Object.entries(layers).map(([y, rows]) => [y, grid(rows)])) };
}
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const WALK = new Set('.:nvmwpekWPSah'.split(''));   // ground you can walk over (spawn cans block, but their cells count for reachability)
const SOLID = (ch) => !WALK.has(ch) && ch !== 'G' && ch !== 'E';
const plan = IB.LEVEL_PLANS.grove;
const maps = plan.zones.map((z) => Object.assign({ name: z.map }, parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8'))));
const key = (c, r) => c + ',' + r;
function blocks(g, ch) {
  const seen = new Set(), out = [];
  for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
    if (g.at(c, r) !== ch || seen.has(key(c, r))) continue;
    let w = 0; while (g.at(c + w, r) === ch && !seen.has(key(c + w, r))) w++;
    let h = 0; while ([...Array(w).keys()].every((k) => g.at(c + k, r + h) === ch && !seen.has(key(c + k, r + h)))) h++;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen.add(key(c + x, r + y));
    out.push([c, r, w, h]);
  }
  return out;
}

test('grove theme: kit-grove outdoors, terrain with ground paint, coded forest backdrop, climbable redwoods, walkway symbols', () => {
  assert.equal(TH.family, 'kit-grove');
  assert.equal(TH.prefix, 'KIT_GROVE_');
  assert.ok(Array.isArray(TH.env.sky) && TH.env.clouds && TH.env.ceiling === null);
  assert.equal(TH.env.fog.color, TH.env.sky[1], 'fog = horizon colour: the haze runs out into the sky');
  assert.equal(typeof TH.terrain.height, 'function');
  assert.equal(typeof TH.terrain.paint, 'function');
  for (const ch of 'ZWkCTFJ') assert.ok(TH.terrain.flat.includes(ch), ch + ' stands on level ground');
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(TH.wall.facing, 'open');
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
  const all = new Set(TH.allPieces());
  for (const [ch, d] of Object.entries(TH.symbols)) d.pieces.forEach((p) => assert.ok(all.has(p), ch + ' ' + p));
  assert.deepEqual(TH.symbols.Z.size, [8, 8]);
  assert.equal(TH.symbols.Z.face, 0, 'redwoods never turn (the stairwell is always on the north-east)');
  assert.equal(TH.symbols['='].rotate, 'edge');
  const R = { '^': 0, '_': Math.PI, '[': Math.PI / 2, ']': -Math.PI / 2, '1': 0, '2': -Math.PI / 2, '3': Math.PI, '4': Math.PI / 2 };
  for (const [ch, yaw] of Object.entries(R)) assert.equal(TH.symbols[ch].rotate, yaw, 'rail ' + ch);
  for (const ch of 'nvmwpekW') assert.equal(TH.symbols[ch].collide, false, ch + ' is walk-through');
  // the paint: a trail vertex is dirt, a vertex at the creek is mud
  const g = grid(['....', '.::.', '.kk.', '....']);
  assert.ok(TH.terrain.paint(2, 1, 0, g)[0] !== TH.terrain.paint(2, 3, 0, g)[0], 'trail and creek tint differently');
  // slopes stay walkable for robots: < 0.4 m rise per 0.5 m nav cell
  for (let zi = 0; zi < 3; zi++) for (let r = 0; r < 50; r++) for (let c = 0; c < 50; c++) {
    assert.ok(Math.abs(TH.terrain.height(c + 1, r, zi) - TH.terrain.height(c, r, zi)) < 0.8, 'slope x');
    assert.ok(Math.abs(TH.terrain.height(c, r + 1, zi) - TH.terrain.height(c, r, zi)) < 0.8, 'slope z');
  }
});

test('grove level plan: three zones of four waves', () => {
  assert.equal(plan.themeId, 'grove');
  assert.equal(plan.zones.length, 3);
  plan.zones.forEach((z) => assert.equal(z.waves.length, 4, z.map));
});

for (const { name, g, layers } of maps) {
  test('zone ' + name + ': size, edges, gates, reachability, spawns, prefab tiling, symbols', () => {
    assert.equal(g.w, 50); assert.equal(g.h, 50);
    for (let c = 0; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0)), 'north edge'); assert.ok('#E'.includes(g.at(c, g.h - 1)), 'south edge'); }
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const known = new Set(Object.keys(TH.symbols).concat('#GEPSah.:'.split('')));
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(known.has(ch), 'unknown symbol ' + ch + ' at ' + c + ',' + r)));
    let P = null;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') { assert.equal(P, null, 'one P'); P = [c, r]; } }));
    assert.ok(P);
    for (const dc of [-2, -1, 1, 2]) assert.ok(!SOLID(g.at(P[0] + dc, P[1] - 4)), 'weapon stand spot clear');
    const dist = new Set([key(...P)]); const q = [P];
    while (q.length) {
      const [c, r] = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = [c + dc, r + dr];
        if (n[0] < 1 || n[1] < 1 || n[0] >= g.w - 1 || n[1] >= g.h - 1 || dist.has(key(...n)) || SOLID(g.at(...n))) continue;
        dist.add(key(...n)); q.push(n);
      }
    }
    const G = [...g.rows[0]].map((ch, c) => ch === 'G' ? c : -1).filter((c) => c >= 0);
    assert.deepEqual(G, [24, 25, 26]);
    assert.ok(G.some((c) => dist.has(key(c, 1))), 'P reaches the exit gate');
    let sealed = 0;
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) if (!SOLID(g.at(c, r)) && !dist.has(key(c, r))) sealed++;
    assert.equal(sealed, 0, 'every open cell reachable');
    const S = []; let ammo = 0, health = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'S') S.push([c, r]); if (ch === 'a') ammo++; if (ch === 'h') health++; }));
    assert.ok(S.length >= 10 && S.length <= 14, 'spawns ' + S.length);
    assert.ok(ammo >= 2 && ammo <= 3 && health >= 2 && health <= 3, 'pickups');
    for (const [c, r] of S) assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14, 'spawn ' + c + ',' + r + ' far from P');
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      const [sw, sd] = d.size;
      for (const [c, r, w, h] of blocks(g, ch)) assert.ok((w === sw && h === sd) || (w === sd && h === sw), name + ' ' + ch + ' block ' + w + 'x' + h + ' at ' + c + ',' + r);
    }
    // every climbable redwood: its stairs start (south-west corner) is reachable from open ground
    const trees = blocks(g, 'Z');
    assert.ok(trees.length >= 3, 'three or more climbable redwoods');
    for (const [c, r] of trees) assert.ok(dist.has(key(c - 1, r + 7)), 'stairs start of the redwood at ' + c + ',' + r);
  });

  test('zone ' + name + ': the 9 m walkways: bridges between redwoods, rails, piers, clear airspace', () => {
    const L = layers['9'];
    assert.ok(L && L.w === 50 && L.h === 50, 'an @layer 9 grid');
    const trees = blocks(g, 'Z'), inTree = (c, r) => trees.find(([tc, tr]) => c >= tc && c < tc + 8 && r >= tr && r < tr + 8);
    // bridges: 2 rows, running from one tree's east edge to the next tree's west edge
    const runs = blocks(L, '=');
    assert.ok(runs.length >= 1, 'bridges');
    for (const [c, r, w, h] of runs) {
      assert.equal(h, 2, 'bridges are two cells wide');
      const A = inTree(c - 1, r), B = inTree(c + w, r);
      assert.ok(A && B && A !== B, 'bridge at ' + c + ',' + r + ' joins two redwoods');
      assert.equal(r, A[1] + 3, 'it lands on the middle of the east side'); assert.equal(r, B[1] + 3, 'and of the west side');
      for (let x = c; x < c + w; x++) for (let y = r; y < r + 2; y++) assert.ok(!inTree(x, y), 'no bridge over a footprint');
      const piers = blocks(g, 'J').filter(([pc, pr]) => pc >= c && pc < c + w && pr === r);
      if (w > 9) assert.ok(piers.length >= 1, 'a long bridge stands on piers');
    }
    blocks(g, 'J').forEach(([pc, pr]) => assert.equal(L.at(pc, pr), '=', 'piers stand under bridges'));
    // rails: every footprint edge cell has its rail, except bridge landings and the stairwell (north edge cells 4..7,
    // east edge cells 1..2); nothing else on the walkway level
    for (const [tc, tr] of trees) {
      for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) {
        const c = tc + i, r = tr + j, ch = L.at(c, r), edge = i === 0 || i === 7 || j === 0 || j === 7;
        const stairwell = (j === 0 && i >= 4) || (i === 7 && (j === 1 || j === 2));
        const landing = (i === 7 && L.at(c + 1, r) === '=') || (i === 0 && L.at(c - 1, r) === '=');
        if (!edge || stairwell || landing) { assert.equal(ch, '.', 'open walkway at ' + c + ',' + r); continue; }
        const want = { '0,0': '1', '7,0': '2', '7,7': '3', '0,7': '4' }[i + ',' + j] || (j === 0 ? '^' : j === 7 ? '_' : i === 0 ? '[' : ']');
        assert.equal(ch, want, 'rail at ' + c + ',' + r);
      }
    }
    for (let r = 0; r < 50; r++) for (let c = 0; c < 50; c++) { const ch = L.at(c, r); if (ch !== '.' && ch !== '#' && ch !== '=') assert.ok(inTree(c, r), 'rail ' + ch + ' off a platform at ' + c + ',' + r); }
    // airspace: young redwoods (crowns 5..19 m) keep 3 cells from platforms and bridges
    for (let r = 0; r < 50; r++) for (let c = 0; c < 50; c++) {
      if (g.at(c, r) !== 'y') continue;
      for (let dr = -3; dr <= 3; dr++) for (let dc = -3; dc <= 3; dc++) assert.ok(g.at(c + dc, r + dr) !== 'Z' && L.at(c + dc, r + dr) !== '=', 'young redwood at ' + c + ',' + r + ' grows into the walkways');
    }
  });

  test('zone ' + name + ': the wall chooser returns kit pieces and leaves no gaps in a run', () => {
    const all = new Set(TH.allPieces());
    let mods = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const n = TH.wall.choose(c, r, true, false, hash, g);
      if (n) { assert.ok(all.has(n), n); mods++; continue; }
      // empty: beside a gate, next to a corner pile, or an odd cell between two 2 m modules
      const along = r === 0 || r === g.h - 1, u = along ? c : r;
      const gate = (r === 0 || r === g.h - 1) && [-2, -1, 1, 2].some((d) => 'GE'.includes(g.at(c + d, r)));
      const corner = (along ? [c - 1, c + 1] : [r - 1, r + 1]).some((v) => v === 0 || v === (along ? g.w : g.h) - 1);
      assert.ok(gate || corner || u % 2 === 1, 'gap in the wall at ' + c + ',' + r);
    }
    assert.ok(mods > 80, 'modules ' + mods);
  });
}
