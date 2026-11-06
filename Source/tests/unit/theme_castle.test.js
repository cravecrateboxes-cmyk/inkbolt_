// Castle Courtyard theme: level plan, zone map rules, reachability, the curtain-wall chooser, closed passages.
const test = require('node:test');
const assert = require('node:assert');
require('../../src/data/themes.js');
require('../../src/data/themes.gen.js');
require('../../src/data/zones.gen.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.castle;
const PLAN = IB.LEVEL_PLANS.castle;

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
function walkable(ch) {
  if ('.PEGah'.includes(ch)) return true;
  const d = TH.symbols[ch];
  return !!d && d.collide === false;
}
const hash = (a, b) => { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
// mirror of zones.js buildWalls: exposure and the open-side facing handed to the chooser
function faceOf(g, c, r) {
  const solid = (x, y) => '#GE'.includes(g.at(x, y));
  const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
  return n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
}

test('theme and level plan are registered; ?plan=castle resolves', () => {
  assert.ok(TH, 'theme castle');
  assert.strictEqual(TH.family, 'kit-castle');
  assert.ok(PLAN && PLAN.themeId === 'castle' && PLAN.id === 'castle');
  assert.ok(PLAN.name && PLAN.intro);
  assert.strictEqual(PLAN.zones.length, 3);
  for (const k of ['gate', 'trail', 'hatch', 'stand', 'env', 'floor', 'wall', 'symbols', 'backdrop', 'budget']) assert.ok(TH[k], k);
  assert.strictEqual(TH.env.ceiling, null);
  assert.ok(TH.env.sky && TH.env.clouds);
  assert.strictEqual(TH.wall.facing, 'open');
});

test('the passages between wards are walled as high as the curtain (nothing beyond shows over them)', () => {
  assert.ok(TH.trail.height >= TH.wall.height, 'trail ' + TH.trail.height + ' vs wall ' + TH.wall.height);
});

test('robots: 80-95 in all, 3-4 waves a zone, 2-4 drones, no bombers in zone 1', () => {
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
  test('zone ' + zp.map + ': wide, gates, spawns, reachability, symbols, prefabs', () => {
    const text = IB.ZONE_MAPS[zp.map];
    assert.ok(text, 'map ' + zp.map);
    const g = parse(text);
    assert.ok(g.w >= 56 && g.w <= 64 && g.h >= 48 && g.h <= 58, zp.map + ' is ' + g.w + 'x' + g.h);
    for (const row of g.rows) for (const ch of row) assert.ok('#.SPEGah'.includes(ch) || TH.symbols[ch], 'unknown symbol ' + JSON.stringify(ch));
    // closed curtain: the whole border is wall or gate
    for (let c = 0; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0)), 'north wall ' + c); assert.ok('#E'.includes(g.at(c, g.h - 1)), 'south wall ' + c); }
    for (let r = 0; r < g.h; r++) { assert.strictEqual(g.at(0, r), '#'); assert.strictEqual(g.at(g.w - 1, r), '#'); }
    const P = find(g, 'P'), E = find(g, 'E'), G = find(g, 'G');
    assert.strictEqual(P.length, 1);
    assert.strictEqual(E.length, 3); assert.ok(E.every((e) => e.r === g.h - 1) && E[2].c - E[0].c === 2);
    assert.strictEqual(G.length, 3); assert.ok(G.every((e) => e.r === 0) && G[2].c - G[0].c === 2);
    for (const e of G) for (const k of [1, 2]) assert.ok(walkable(g.at(e.c, k)), 'open in front of the exit ' + e.c);
    for (const e of E) for (const k of [1, 2]) assert.ok(walkable(g.at(e.c, g.h - 1 - k)), 'open behind the entry ' + e.c);
    const seen = new Set([P[0].c + ',' + P[0].r]), q = [P[0]];
    while (q.length) {
      const { c, r } = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const k = (c + dc) + ',' + (r + dr);
        if (!seen.has(k) && walkable(g.at(c + dc, r + dr))) { seen.add(k); q.push({ c: c + dc, r: r + dr }); }
      }
    }
    assert.ok(G.some((e) => seen.has(e.c + ',1')), 'exit reachable from P');
    // no sealed pockets of open ground
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if (walkable(g.at(c, r)) && !'EG'.includes(g.at(c, r))) assert.ok(seen.has(c + ',' + r), 'sealed open cell ' + c + ',' + r);
    const S = find(g, 'S');
    assert.ok(S.length >= 10 && S.length <= 14, 'spawns ' + S.length);
    for (const s of S) {
      assert.ok(Math.hypot(s.c - P[0].c, s.r - P[0].r) >= 14, 'spawn too close ' + s.c + ',' + s.r);
      for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(walkable(g.at(s.c + dc, s.r + dr)), 'spawn crowded ' + s.c + ',' + s.r);
    }
    assert.ok(find(g, 'a').length >= 2 && find(g, 'a').length <= 3);
    assert.ok(find(g, 'h').length >= 2 && find(g, 'h').length <= 3);
    for (const dc of [-2, -1, 1, 2]) assert.ok(walkable(g.at(P[0].c + dc, P[0].r - 4)), 'stand cell');
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
    // landmarks: a keep, a well or the trebuchet in every ward, towers on the walls
    assert.ok(find(g, 'T').length + find(g, 'W').length + find(g, 'Q').length > 0, 'a landmark in ' + zp.map);
    assert.ok(find(g, 'O').length >= 100, 'drum towers in ' + zp.map);
  });
}

test('the curtain chooser only returns kit pieces: straight runs get modules, corners the corner turret', () => {
  const all = new Set(TH.allPieces());
  for (const zp of PLAN.zones) {
    const g = parse(IB.ZONE_MAPS[zp.map]);
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const face = faceOf(g, c, r), name = TH.wall.choose(c, r, true, false, hash, g, face);
      assert.ok(all.has(name), zp.map + ' ' + c + ',' + r + ' -> ' + name);
      if (face === 'corner' || face === 'none') assert.strictEqual(name, 'Corner');
      else assert.ok(/^Curtain_/.test(name), name);
      // nothing proud (banners, buttresses, torches) right beside a gatehouse
      for (let d = -3; d <= 3; d++) if ('GE'.includes(g.at(c + d, r)) && (face === 'S' || face === 'N')) assert.ok(/^Curtain_[MC]$/.test(name), 'plain beside the gate: ' + name);
    }
  }
  for (const d of Object.values(TH.symbols)) for (const n of d.pieces) assert.ok(all.has(n), n);
  for (const n of [TH.gate.frame, TH.gate.shutter, TH.trail.wall, TH.hatch, TH.stand]) assert.ok(all.has(n), n);
  for (const ring of TH.backdrop.ring) assert.ok(all.has(ring.piece) && /Backdrop/.test(ring.piece), ring.piece);
});
