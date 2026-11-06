// Classroom theme (level 3): zone rules, prefab tiling and the wall chooser.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/classroom.js');
const IB = globalThis.IB;
// the zone maps straight from src/data/zones (zones.gen.js is a build output)
const MAPS = (name) => fs.readFileSync(path.join(__dirname, '../../src/data/zones', name + '.txt'), 'utf8');
const TH = IB.THEME_DEFS.classroom;
const PLAN = IB.LEVEL_PLANS.classroom;

// same grid contract as zones.js Z.parse: outside cells read as wall
function parse(text) {
  const rows = text.replace(/\r/g, '').split('\n').filter((r) => r.length > 0);
  const w = Math.max(...rows.map((r) => r.length));
  const R = rows.map((r) => r.padEnd(w, '.'));
  return { w, h: R.length, rows: R, at: (c, r) => (r < 0 || r >= R.length || c < 0 || c >= w ? '#' : R[r][c]) };
}
function find(g, ch) { const o = []; for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if (g.rows[r][c] === ch) o.push({ c, r }); return o; }
// greedy rectangles, as zones.js rects()
function rects(g, ch) {
  const used = g.rows.map(() => new Uint8Array(g.w)), out = [];
  for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
    if (used[r][c] || g.rows[r][c] !== ch) continue;
    let w = 1; while (c + w < g.w && !used[r][c + w] && g.rows[r][c + w] === ch) w++;
    let h = 1, ok = true;
    while (ok && r + h < g.h) { for (let k = 0; k < w; k++) if (used[r + h][c + k] || g.rows[r + h][c + k] !== ch) { ok = false; break; } if (ok) h++; }
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) used[r + y][c + x] = 1;
    out.push({ c, r, w, h });
  }
  return out;
}
const hash = (a, b) => { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
const zones = PLAN.zones.map((z) => ({ name: z.map, g: parse(MAPS(z.map)), plan: z }));

test('classroom theme and level plan register', () => {
  assert.equal(TH.family, 'kit-classroom');
  assert.equal(TH.env.sky, null);
  assert.ok(TH.env.ceiling && TH.env.ceiling.height > 15 && TH.env.ceiling.light === 'LightPanel');
  assert.equal(PLAN.themeId, 'classroom');
  assert.ok(PLAN.name && PLAN.intro);
  assert.equal(PLAN.zones.length, 3);
  const total = PLAN.zones.reduce((t, z) => t + z.waves.reduce((a, w) => a + w.reduce((b, e) => b + e[1], 0), 0), 0);
  assert.ok(total >= 90 && total <= 105, 'robots ' + total);
  for (const z of PLAN.zones) {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    for (const w of z.waves) for (const [id, n] of w) assert.ok(['crawler', 'gunner', 'bomber', 'drone'].includes(id) && n > 0);
  }
  const pieces = new Set(TH.allPieces());
  for (const d of Object.values(TH.symbols)) for (const p of d.pieces) assert.ok(pieces.has(p), p);
  for (const p of [TH.gate.frame, TH.gate.shutter, TH.trail.wall, TH.hatch, TH.stand, TH.env.ceiling.light]) assert.ok(pieces.has(p), p);
});

test('zones are big, bounded and follow the zone rules', () => {
  const known = new Set(['#', '.', 'S', 'P', 'E', 'G', 'a', 'h'].concat(Object.keys(TH.symbols)));
  for (const { name, g } of zones) {
    assert.ok(g.w >= 44 && g.w <= 60 && g.h >= 40 && g.h <= 56, name + ' size ' + g.w + 'x' + g.h);
    for (const row of g.rows) for (const ch of row) assert.ok(known.has(ch), name + ' symbol ' + ch);
    for (let c = 0; c < g.w; c++) { assert.ok('#GE'.includes(g.rows[0][c]) && '#GE'.includes(g.rows[g.h - 1][c]), name + ' closed N/S'); }
    for (let r = 0; r < g.h; r++) { assert.equal(g.rows[r][0], '#'); assert.equal(g.rows[r][g.w - 1], '#'); }
    const P = find(g, 'P'), G = find(g, 'G'), E = find(g, 'E'), S = find(g, 'S');
    assert.equal(P.length, 1);
    assert.deepEqual(G.map((p) => p.r), [0, 0, 0]);
    assert.equal(G[2].c - G[0].c, 2);
    assert.deepEqual(E.map((p) => p.r), [g.h - 1, g.h - 1, g.h - 1]);
    for (const p of G) for (const k of [1, 2]) assert.equal(g.rows[k][p.c], '.', name + ' exit approach');
    for (const p of E) for (const k of [1, 2]) assert.equal(g.rows[g.h - 1 - k][p.c], '.', name + ' entry approach');
    assert.ok(S.length >= 10 && S.length <= 14, name + ' spawns ' + S.length);
    for (const s of S) {
      assert.ok(Math.hypot(s.c - P[0].c, s.r - P[0].r) >= 14, name + ' spawn near P ' + s.c + ',' + s.r);
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) if (dc || dr) assert.equal(g.rows[s.r + dr][s.c + dc], '.', name + ' spawn crowded ' + s.c + ',' + s.r);
    }
    const a = find(g, 'a').length, h = find(g, 'h').length;
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, name + ' pickups');
  }
});

test('prefab blocks tile exactly (no stretched or overlapping prefabs)', () => {
  for (const { name, g } of zones) {
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      const [sw, sd] = d.size;
      for (const R of rects(g, ch)) {
        const fits = (R.w % sw === 0 && R.h % sd === 0) || (R.w % sd === 0 && R.h % sw === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + R.w + 'x' + R.h + ' at ' + R.c + ',' + R.r);
      }
    }
  }
});

test('reachability: P reaches the exit and every spawn (desks and floor decals are walkable)', () => {
  const BLOCK = new Set('#BcKwLJO=eTQNSn'.split(''));
  for (const { name, g } of zones) {
    const P = find(g, 'P')[0], seen = new Set([P.c + ',' + P.r]), q = [P];
    while (q.length) {
      const { c, r } = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = { c: c + dc, r: r + dr }, k = n.c + ',' + n.r, ch = g.at(n.c, n.r);
        if (seen.has(k) || n.c < 0 || n.r < 0 || n.c >= g.w || n.r >= g.h) continue;
        if (ch === 'G' || ch === 'S' || !BLOCK.has(ch)) { seen.add(k); if (ch !== 'G' && ch !== 'S') q.push(n); }
      }
    }
    for (const p of find(g, 'G')) assert.ok(seen.has(p.c + ',' + p.r), name + ' exit unreachable');
    for (const s of find(g, 'S')) assert.ok(seen.has(s.c + ',' + s.r), name + ' spawn unreachable ' + s.c + ',' + s.r);
  }
});

test('wall chooser: every perimeter module exists, decor faces the room, windows west, alphabet north', () => {
  const pieces = new Set(TH.allPieces()), WALLISH = '#GE';
  for (const { name, g } of zones) {
    const used = {};
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.rows[r][c] !== '#') continue;
      const solid = (x, y) => WALLISH.includes(g.at(x, y));
      // the flags zones.js buildWalls hands to choose()
      const horiz = solid(c - 1, r) || solid(c + 1, r), vert = solid(c, r - 1) || solid(c, r + 1);
      const n = TH.wall.choose(c, r, horiz, horiz && vert, hash, g);
      assert.ok(pieces.has(n), name + ' unknown wall piece ' + n + ' at ' + c + ',' + r);
      used[n] = (used[n] || 0) + 1;
      // perimeter west / east columns come out of the engine with yaw 0: they must use the turned modules
      if (c === 0 && r > 0 && r < g.h - 1) assert.ok(/_R90$/.test(n), name + ' west wall ' + n);
      if (c === g.w - 1 && r > 0 && r < g.h - 1) assert.ok(/_R270$/.test(n), name + ' east wall ' + n);
    }
    assert.equal(used.Wall_Corner, 4, name + ' corners');
    assert.ok(Object.keys(used).some((k) => /^Win_Bay_/.test(k)), name + ' has window bays');
    assert.ok(Object.keys(used).some((k) => /^Wall_Cork/.test(k)), name + ' has a cork board');
    const board = g.rows[1].includes('k');
    if (board) for (const L of 'ABCDEFGHIJKLMNOPQRSTUVWXYZ') assert.equal(used['Alpha_' + L], 1, name + ' letter ' + L);
    else assert.ok(!Object.keys(used).some((k) => /^Alpha_/.test(k)) && used.Wall_Map >= 1, name + ' north wall: map, no alphabet');
  }
});
