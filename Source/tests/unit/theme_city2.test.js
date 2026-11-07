// Downtown at Dusk theme (city2): level plan, zone map rules, reachability, the facade chooser, the El and the alleys.
const test = require('node:test');
const assert = require('node:assert');
require('../../src/data/themes.js');
require('../../src/data/themes.gen.js');
require('../../src/data/zones.gen.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.city2;
const PLAN = IB.LEVEL_PLANS.city2;

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
// the El spans are open underneath (only their columns collide), so robots and the player walk under them
function walkable(ch) {
  if ('.PEGahLR'.includes(ch)) return true;
  const d = TH.symbols[ch];
  return !!d && d.collide === false;
}
const hash = (a, b) => { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
function faceOf(g, c, r) {
  const solid = (x, y) => '#GE'.includes(g.at(x, y));
  const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
  return n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
}

test('theme and level plan are registered; ?plan=city2 resolves', () => {
  assert.ok(TH, 'theme city2');
  assert.strictEqual(TH.family, 'kit-city2');
  assert.ok(PLAN && PLAN.themeId === 'city2' && PLAN.id === 'city2');
  assert.ok(PLAN.name && PLAN.intro);
  assert.strictEqual(PLAN.zones.length, 3);
  for (const k of ['gate', 'trail', 'hatch', 'stand', 'env', 'floor', 'wall', 'symbols', 'backdrop', 'budget']) assert.ok(TH[k], k);
  assert.strictEqual(TH.env.ceiling, null);
  assert.strictEqual(TH.wall.facing, 'open');
});

test('looks nothing like Small City: its own family, sky, floor and palette', () => {
  const sc = IB.THEME_DEFS.smallcity;
  assert.notStrictEqual(TH.family, sc.family);
  assert.notDeepStrictEqual(TH.env.sky, sc.env.sky);
  assert.notStrictEqual(TH.floor.color, sc.floor.color);
  assert.notStrictEqual(TH.env.fog.color, sc.env.fog.color);
});

test('the passages between blocks are high alleys (nothing beyond shows over them)', () => {
  assert.ok(TH.trail.height >= 12, 'trail ' + TH.trail.height);
});

test('robots: 80-95 in all, 3-4 waves a zone, 2-4 drones, no bombers in zone 1', () => {
  let total = 0, drones = 0;
  PLAN.zones.forEach((z, i) => {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    z.waves.forEach((w) => w.forEach(([type, n]) => {
      assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(type), type);
      total += n; if (type === 'drone') drones += n;
      if (i === 0) assert.notStrictEqual(type, 'bomber', 'no bombers in zone 1');
    }));
  });
  assert.ok(total >= 80 && total <= 95, 'total ' + total);
  assert.ok(drones >= 2 && drones <= 4, 'drones ' + drones);
});

for (const zp of (PLAN ? PLAN.zones : [])) {
  test('zone ' + zp.map + ': size, gates, spawns, reachability, symbols, prefabs, El runs', () => {
    const text = IB.ZONE_MAPS[zp.map];
    assert.ok(text, 'map ' + zp.map);
    const g = parse(text);
    assert.ok(g.w >= 56 && g.w <= 64 && g.h >= 48 && g.h <= 58, zp.map + ' is ' + g.w + 'x' + g.h);
    for (const row of g.rows) for (const ch of row) assert.ok('#.SPEGah'.includes(ch) || TH.symbols[ch], 'unknown symbol ' + JSON.stringify(ch));
    for (let c = 0; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0))); assert.ok('#E'.includes(g.at(c, g.h - 1))); }
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
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if (walkable(g.at(c, r)) && !'EG'.includes(g.at(c, r))) assert.ok(seen.has(c + ',' + r), 'sealed open cell ' + c + ',' + r);
    const S = find(g, 'S');
    assert.ok(S.length >= 10 && S.length <= 14, 'spawns ' + S.length);
    for (const s of S) {
      assert.ok(Math.hypot(s.c - P[0].c, s.r - P[0].r) >= 14, 'spawn too close ' + s.c + ',' + s.r);
      for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(walkable(g.at(s.c + dc, s.r + dr)) && !'LR'.includes(g.at(s.c + dc, s.r + dr)), 'spawn crowded ' + s.c + ',' + s.r);
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
    // an El run (L / R cells) always ends against a facade at both ends, never in mid-street
    const el = (c, r) => 'LR'.includes(g.at(c, r)), elDone = new Set();
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (!el(c, r) || elDone.has(c + ',' + r)) continue;
      let c0 = c, c1 = c, r0 = r, r1 = r;
      const st = [[c, r]]; elDone.add(c + ',' + r);
      while (st.length) {
        const [x, y] = st.pop(); c0 = Math.min(c0, x); c1 = Math.max(c1, x); r0 = Math.min(r0, y); r1 = Math.max(r1, y);
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const k = (x + dx) + ',' + (y + dy); if (el(x + dx, y + dy) && !elDone.has(k)) { elDone.add(k); st.push([x + dx, y + dy]); } }
      }
      const vert = r1 - r0 > c1 - c0;
      assert.strictEqual(vert ? c1 - c0 + 1 : r1 - r0 + 1, 4, 'El run is 4 cells wide');
      if (vert) for (let x = c0; x <= c1; x++) { assert.strictEqual(g.at(x, r0 - 1), '#', 'El ends in the street'); assert.strictEqual(g.at(x, r1 + 1), '#', 'El ends in the street'); }
      else for (let y = r0; y <= r1; y++) { assert.strictEqual(g.at(c0 - 1, y), '#', 'El ends in the street'); assert.strictEqual(g.at(c1 + 1, y), '#', 'El ends in the street'); }
    }
  });
}

test('the facade chooser only returns kit pieces; El portals, corners and gate pilasters where they belong', () => {
  const all = new Set(TH.allPieces());
  let portals = 0, escapes = 0, doors = 0;
  for (const zp of PLAN.zones) {
    const g = parse(IB.ZONE_MAPS[zp.map]);
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const face = faceOf(g, c, r), name = TH.wall.choose(c, r, true, false, hash, g, face);
      assert.ok(all.has(name), zp.map + ' ' + c + ',' + r + ' -> ' + name);
      if (face === 'corner' || face === 'none') assert.ok(/^Corner_/.test(name), name);
      if (/^Portal_/.test(name)) portals++;
      if (/^Esc/.test(name)) escapes++;
      if (/^Door_/.test(name)) doors++;
      if (face !== 'corner' && face !== 'none') {
        const fc = c + (face === 'E' ? 1 : face === 'W' ? -1 : 0), fr = r + (face === 'S' ? 1 : face === 'N' ? -1 : 0);
        if ('LR'.includes(g.at(fc, fr))) assert.ok(/^Portal_/.test(name), 'El portal at ' + c + ',' + r);
      }
    }
  }
  assert.ok(portals >= 8 && escapes >= 30 && doors >= 30, 'portals ' + portals + ' escapes ' + escapes + ' doors ' + doors);
  for (const d of Object.values(TH.symbols)) for (const n of d.pieces) assert.ok(all.has(n), n);
  for (const n of [TH.gate.frame, TH.gate.shutter, TH.trail.wall, TH.hatch, TH.stand]) assert.ok(all.has(n), n);
  for (const ring of TH.backdrop.ring) assert.ok(all.has(ring.piece) && /Backdrop/.test(ring.piece), ring.piece);
});
