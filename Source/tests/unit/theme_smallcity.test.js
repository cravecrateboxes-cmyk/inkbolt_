// Small City theme (campaign level 2): level plan, zone map rules, reachability and the facade chooser.
const test = require('node:test');
const assert = require('node:assert');
require('../../src/data/themes.js');
require('../../src/data/themes.gen.js');
require('../../src/data/zones.gen.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.smallcity;
const PLAN = IB.LEVEL_PLANS.smallcity;

function parse(text) {
  const rows = text.replace(/\r/g, '').split('\n').filter((r) => r.length > 0);
  const w = Math.max(...rows.map((r) => r.length));
  const g = rows.map((r) => r.padEnd(w, '.'));
  return { w, h: g.length, rows: g, at: (c, r) => (r < 0 || r >= g.length || c < 0 || c >= w) ? '#' : g[r][c] };
}
function find(grid, ch) {
  const out = [];
  for (let r = 0; r < grid.h; r++) for (let c = 0; c < grid.w; c++) if (grid.rows[r][c] === ch) out.push({ c, r });
  return out;
}
// cells a robot / the player can stand in: built-ins plus theme symbols without collision
function walkable(ch) {
  if ('.PEGah'.includes(ch)) return true;
  const d = TH.symbols[ch];
  return !!d && d.collide === false;
}

test('theme and level plan are registered', () => {
  assert.ok(TH, 'theme smallcity');
  assert.strictEqual(TH.family, 'kit-smallcity');
  assert.ok(PLAN && PLAN.themeId === 'smallcity');
  assert.ok(PLAN.name && PLAN.intro);
  assert.strictEqual(PLAN.zones.length, 3);
  for (const k of ['gate', 'trail', 'hatch', 'stand', 'env', 'floor', 'wall', 'symbols', 'backdrop', 'budget']) assert.ok(TH[k], k);
  assert.strictEqual(TH.env.ceiling, null);
  assert.ok(TH.env.sky && TH.env.clouds);
});

test('robots: 80-95 in all, 3-4 waves a zone, 2-4 drones, bombers from zone 2', () => {
  let total = 0, drones = 0;
  PLAN.zones.forEach((z, i) => {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    z.waves.forEach((w) => w.forEach(([type, n]) => {
      assert.ok(['crawler', 'gunner', 'bomber', 'drone'].includes(type), type);
      total += n; if (type === 'drone') drones += n;
      if (i === 0) assert.notStrictEqual(type, 'bomber', 'no bombers in zone 1');
    }));
    assert.ok(z.waves.some((w) => w.some(([t]) => t === 'gunner')), z.map + ' has gunners');
  });
  assert.ok(total >= 80 && total <= 95, 'total ' + total);
  assert.ok(drones >= 2 && drones <= 4, 'drones ' + drones);
});

for (const zp of (PLAN ? PLAN.zones : [])) {
  test('zone ' + zp.map + ': size, gates, spawns, reachability, symbols', () => {
    const text = IB.ZONE_MAPS[zp.map];
    assert.ok(text, 'map ' + zp.map);
    const g = parse(text);
    assert.ok(g.w >= 46 && g.w <= 60 && g.h >= 40 && g.h <= 56, zp.map + ' is ' + g.w + 'x' + g.h);
    // every symbol is known
    for (const row of g.rows) for (const ch of row) assert.ok('#.SPEGah'.includes(ch) || TH.symbols[ch], 'unknown symbol ' + JSON.stringify(ch));
    // one entry, EEE on the last row, GGG on row 0 with two open rows in front
    const P = find(g, 'P'), E = find(g, 'E'), G = find(g, 'G');
    assert.strictEqual(P.length, 1);
    assert.strictEqual(E.length, 3); assert.ok(E.every((e) => e.r === g.h - 1) && E[2].c - E[0].c === 2);
    assert.strictEqual(G.length, 3); assert.ok(G.every((e) => e.r === 0) && G[2].c - G[0].c === 2);
    for (const e of G) for (const k of [1, 2]) assert.ok(walkable(g.at(e.c, k)), 'open in front of the exit ' + e.c);
    for (const e of E) for (const k of [1, 2]) assert.ok(walkable(g.at(e.c, g.h - 1 - k)), 'open behind the entry ' + e.c);
    // breadth-first search from P over walkable cells
    const seen = new Set([P[0].c + ',' + P[0].r]), q = [P[0]];
    while (q.length) {
      const { c, r } = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const k = (c + dc) + ',' + (r + dr);
        if (!seen.has(k) && walkable(g.at(c + dc, r + dr))) { seen.add(k); q.push({ c: c + dc, r: r + dr }); }
      }
    }
    assert.ok(G.some((e) => seen.has(e.c + ',1')), 'exit reachable from P');
    // spawn cans: 10-14, >= 14 m from P, 3 x 3 open, reachable
    const S = find(g, 'S');
    assert.ok(S.length >= 10 && S.length <= 14, 'spawns ' + S.length);
    for (const s of S) {
      assert.ok(Math.hypot(s.c - P[0].c, s.r - P[0].r) >= 14, 'spawn too close ' + s.c + ',' + s.r);
      for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(walkable(g.at(s.c + dc, s.r + dr)), 'spawn crowded ' + s.c + ',' + s.r);
      assert.ok([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dc, dr]) => seen.has((s.c + dc) + ',' + (s.r + dr))), 'spawn unreachable ' + s.c + ',' + s.r);
    }
    assert.ok(find(g, 'a').length >= 2 && find(g, 'a').length <= 3);
    assert.ok(find(g, 'h').length >= 2 && find(g, 'h').length <= 3);
    // the weapon stands go 4 rows in front of P
    for (const dc of [-2, -1, 1, 2]) assert.ok(walkable(g.at(P[0].c + dc, P[0].r - 4)), 'stand cell');
    // prefab symbols come in exact multiples of their footprint
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      const cells = new Set(find(g, ch).map((p) => p.c + ',' + p.r)), done = new Set();
      for (const k of cells) {
        if (done.has(k)) continue;
        const comp = [k], stack = [k]; done.add(k);
        while (stack.length) {
          const [c, r] = stack.pop().split(',').map(Number);
          for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const n = (c + dc) + ',' + (r + dr); if (cells.has(n) && !done.has(n)) { done.add(n); comp.push(n); stack.push(n); } }
        }
        const xs = comp.map((s) => +s.split(',')[0]), ys = comp.map((s) => +s.split(',')[1]);
        const bw = Math.max(...xs) - Math.min(...xs) + 1, bh = Math.max(...ys) - Math.min(...ys) + 1, [w, dd] = d.size;
        assert.strictEqual(bw * bh, comp.length, ch + ' block not rectangular at ' + k);
        assert.ok((bw % w === 0 && bh % dd === 0) || (bw % dd === 0 && bh % w === 0), ch + ' block ' + bw + 'x' + bh + ' at ' + k);
      }
    }
    // east / west facades are '[' / ']' (the engine only turns '#' modules by 0 or 180 degrees)
    const solid = (c, r) => '#GE[]'.includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const ns = !solid(c, r - 1) || !solid(c, r + 1), ew = !solid(c - 1, r) || !solid(c + 1, r);
      assert.ok(!(ew && !ns), 'east/west facade left as # at ' + c + ',' + r);
    }
  });
}

test('the facade chooser only returns kit pieces, and every module fits its slot', () => {
  const all = new Set(TH.allPieces());
  const hash = (a, b) => { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
  for (const zp of PLAN.zones) {
    const g = parse(IB.ZONE_MAPS[zp.map]);
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const name = TH.wall.choose(c, r, true, true, hash, g);
      assert.ok(all.has(name), zp.map + ' ' + c + ',' + r + ' -> ' + name);
    }
  }
  for (const ch of ['[', ']']) for (const n of TH.symbols[ch].pieces) assert.ok(all.has(n), n);
  for (const d of Object.values(TH.symbols)) for (const n of d.pieces) assert.ok(all.has(n), n);
  for (const n of [TH.gate.frame, TH.gate.shutter, TH.trail.wall, TH.hatch, TH.stand]) assert.ok(all.has(n), n);
  for (const ring of TH.backdrop.ring) assert.ok(all.has(ring.piece) && /Backdrop/.test(ring.piece), ring.piece);
});
