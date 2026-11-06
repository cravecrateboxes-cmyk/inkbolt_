// Living Room theme: map rules, level plan size, wall chooser (paint per room, E/W trims), prefab tiling, reachability.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/livingroom.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.livingroom;
const PLAN = IB.LEVEL_PLANS.livingroom;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function load(name) {
  const rows = fs.readFileSync(path.join(ZDIR, name + '.txt'), 'utf8').replace(/\r/g, '').split('\n').filter(r => r.length);
  const w = Math.max(...rows.map(r => r.length));
  return { name, rows, w, h: rows.length, at: (c, r) => (r < 0 || r >= rows.length || c < 0 || c >= w) ? '#' : (rows[r][c] || '.') };
}
const MAPS = PLAN.zones.map(z => load(z.map));
const find = (g, ch) => { const o = []; g.rows.forEach((row, r) => [...row].forEach((v, c) => { if (v === ch) o.push([c, r]); })); return o; };
// cells a robot or the player can stand on (coarse): raised pieces you run under (coffee table, dining table, stools),
// floor anchors (rug, sun patch) and wall overlays without collision
const WALK = new Set(['.', 'P', 'a', 'h', 'Y', 'D', 'j', 'O', 'u', 'f', 'r', 'x', 'y']);

test('level plan: three zones, 3-4 waves each, 110-135 robots of the modelled types, dense finale', () => {
  assert.equal(PLAN.themeId, 'livingroom');
  assert.equal(PLAN.zones.length, 3);
  let total = 0;
  for (const z of PLAN.zones) {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    for (const w of z.waves) for (const [type, n] of w) { assert.ok(['crawler', 'gunner', 'bomber', 'drone'].includes(type), type); total += n; }
  }
  assert.ok(total >= 110 && total <= 135, 'robots ' + total);
  const last = PLAN.zones[2].waves[PLAN.zones[2].waves.length - 1].reduce((s, e) => s + e[1], 0);
  assert.ok(last >= 18, 'dense final wave ' + last);
  assert.equal(PLAN.level, undefined, 'campaign numbering is set by levelplans.js');
});

test('maps: wide, bordered, gated, one entry, spawns away from it, pickups, known symbols', () => {
  const known = new Set(['#', '.', 'S', 'P', 'E', 'G', 'a', 'h', ...Object.keys(TH.symbols)]);
  for (const g of MAPS) {
    assert.ok(g.w >= 60 && g.w <= 66 && g.h >= 44 && g.h <= 50 && g.w > g.h, g.name + ' size ' + g.w + 'x' + g.h);
    for (const row of g.rows) for (const ch of row) assert.ok(known.has(ch), g.name + ' unknown symbol ' + ch);
    for (let c = 0; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0)), g.name + ' north wall'); assert.ok('#E'.includes(g.at(c, g.h - 1)), g.name + ' south wall'); }
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const G = find(g, 'G'), E = find(g, 'E'), P = find(g, 'P'), S = find(g, 'S');
    assert.equal(G.length, 3); assert.equal(E.length, 3); assert.equal(P.length, 1);
    // the door built-in covers 3.55 m either side of the gate centre: nothing may stand against the wall there
    const gc = (G[0][0] + G[2][0] + 1) / 2;
    for (let c = 0; c < g.w; c++) if (Math.abs(c + 0.5 - gc) < 4.05) for (const r of [1, 2]) assert.ok(WALK.has(g.at(c, r)) || g.at(c, r) === 'S', g.name + ' clear by the exit door at ' + c);
    assert.ok(S.length >= 12 && S.length <= 14, g.name + ' spawns ' + S.length);
    for (const [c, r] of S) {
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, g.name + ' spawn near P at ' + c + ',' + r);
      for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(WALK.has(g.at(c + dc, r + dr)), g.name + ' spawn crowded at ' + c + ',' + r);
    }
    for (const ch of 'ah') { const n = find(g, ch).length; assert.ok(n >= 2 && n <= 3, g.name + ' ' + ch + ' ' + n); }
  }
});

test('every spawn, pickup and the exit are reachable from the entry (cell BFS)', () => {
  for (const g of MAPS) {
    const [pc, pr] = find(g, 'P')[0], seen = new Set([pc + ',' + pr]), q = [[pc, pr]];
    while (q.length) {
      const [c, r] = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const k = (c + dc) + ',' + (r + dr), ch = g.at(c + dc, r + dr);
        if (!seen.has(k) && (WALK.has(ch) || ch === 'S')) { seen.add(k); q.push([c + dc, r + dr]); }
      }
    }
    const G = find(g, 'G');
    assert.ok(seen.has(G[1][0] + ',1'), g.name + ' exit unreachable');
    for (const ch of 'Sah') for (const [c, r] of find(g, ch)) assert.ok(seen.has(c + ',' + r), g.name + ' ' + ch + ' unreachable at ' + c + ',' + r);
  }
});

test('rooms: lounge, dining and kitchen each have their landmarks; paint follows the room', () => {
  const has = (g, chs) => [...chs].every(ch => find(g, ch).length > 0);
  assert.ok(has(MAPS[0], 'TYVOQFWu'), 'lounge: sofa, coffee table, TV, rug, bookshelf, fireplace, window, sun');
  assert.ok(has(MAPS[1], 'DdCU'), 'dining: table, chairs both sides, sideboard');
  assert.ok(has(MAPS[2], 'IjRk'), 'kitchen: island, stools, fridge, counters');
  const wallAt = (g) => { for (let c = 1; c < g.w - 1; c++) if (g.at(c, 0) === '#' && g.at(c, 1) === '.') return [c, 0]; };
  const hash = () => 0.5;
  ['Wall1', 'Wall2', 'Wall3'].forEach((n, i) => { const [c, r] = wallAt(MAPS[i]); assert.equal(TH.wall.choose(c, r, true, false, hash, MAPS[i], 'S'), n, MAPS[i].name); });
});

test('wall chooser: E/W faces get the raised-trim modules, corners the hidden filler; every name exists', () => {
  const pieces = new Set(TH.allPieces());
  const hash = () => 0.5;
  for (const g of MAPS) for (const face of ['S', 'N', 'E', 'W', 'corner', 'none']) {
    const name = TH.wall.choose(1, 0, true, false, hash, g, face);
    assert.ok(pieces.has(name), name);
    if (face === 'E' || face === 'W') assert.ok(/_X$/.test(name), name);
    else if (face === 'S' || face === 'N') assert.ok(/^Wall\d$/.test(name), name);
    else assert.equal(name, 'Wall_Corner');
  }
  assert.equal(TH.wall.facing, 'open');
});

test('prefab blocks tile exactly (no stretched furniture)', () => {
  for (const g of MAPS) {
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      const seen = new Set();
      for (const [c0, r0] of find(g, ch)) {
        if (seen.has(c0 + ',' + r0)) continue;
        // block = maximal rectangle grown right then down (maps never put two blocks of one symbol side by side)
        let w = 0; while (g.at(c0 + w, r0) === ch) w++;
        let h = 0; while ([...Array(w).keys()].every(k => g.at(c0 + k, r0 + h) === ch)) h++;
        for (let r = r0; r < r0 + h; r++) for (let c = c0; c < c0 + w; c++) seen.add(c + ',' + r);
        const [sw, sd] = d.size;
        const fits = (w % sw === 0 && h % sd === 0) || (w % sd === 0 && h % sw === 0);
        assert.ok(fits, g.name + ' ' + ch + ' block ' + w + 'x' + h + ' at ' + c0 + ',' + r0 + ' vs ' + sw + 'x' + sd);
      }
    }
  }
});

test('indoor environment: no sky, an 18 m ceiling with lit tiles, walls and trails reach past it, budgets', () => {
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, 18);
  assert.equal(TH.env.ceiling.light, 'CeilingTile');
  assert.ok(TH.wall.height > TH.env.ceiling.height && TH.trail.height > TH.env.ceiling.height);
  assert.ok(TH.trail.variants.length >= 3);
  assert.ok(TH.budget.prop <= 2000 && TH.budget.total <= 70000);
});
