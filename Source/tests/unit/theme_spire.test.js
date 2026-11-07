// The Spire theme (kit-spire): level plan, zone layers (floor plan, inlays, mezzanine, ceiling / glass roof), sizes
// that keep the diagrid bays even, gates, reachability on both floors (stairs land on the deck), spawns, prefab tiling,
// the diagrid wall chooser (every '#' cell resolves to a kit piece, slices mirrored where the engine turns the module)
// and the outside: the skyline table the kit and the city's shafts share, the city / tower options.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/grove.js');
require('../../src/data/themes/spire.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.spire;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function grid(rows) {
  return { w: rows[0].length, h: rows.length, rows, at: (c, r) => (r < 0 || r >= rows.length || c < 0 || c >= rows[0].length) ? '#' : rows[r][c] };
}
function parse(text) {
  const out = { base: [], layers: {} };
  let cur = out.base;
  text.replace(/\r/g, '').split('\n').filter((l) => l.length).forEach((l) => {
    const m = /^@layer\s+(-?[\d.]+)/.exec(l);
    if (m) { cur = []; out.layers[m[1]] = cur; } else cur.push(l);
  });
  out.g = grid(out.base);
  Object.keys(out.layers).forEach((k) => { out.layers[k] = grid(out.layers[k]); });
  return out;
}
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
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const plan = IB.LEVEL_PLANS.spire;
const maps = plan.zones.map((z) => ({ name: z.map, plan: z, ...parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const GROUND = '.ahP', DECK = 'ulah', STAIRS = 'NVZU';
const LAYER_SYMS = { '0': 'xg-wq', '4.5': 'urilLBopSahdX' + 'M', '9': '~:HY^' };

test('spire theme: kit-spire, double-height floors, sky outside, a far camera and a tier-scaled fog for the skyline', () => {
  assert.equal(TH.family, 'kit-spire');
  assert.equal(TH.prefix, 'KIT_SPIRE_');
  assert.equal(TH.wall.height, 9);
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(Array.isArray(TH.env.sky) && TH.env.sky[1] === TH.env.fog.color && TH.below.haze === TH.env.fog.color, 'sky horizon, fog and city haze are one colour');
  assert.ok(TH.env.far >= TH.below.horizon, 'the camera sees the haze ground out to the horizon');
  assert.ok(TH.env.fog.tierScale, 'the skyline stays readable on every graphics tier');
  assert.ok(TH.budget.total <= 90000);
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
});

test('level plan: three zones, the biggest waves of the campaign so far, soldiers and blade bots, campaign fields left alone', () => {
  assert.equal(plan.themeId, 'spire');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f);
  const types = new Set(); let total = 0;
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); total += n; })));
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
  const grove = IB.LEVEL_PLANS.grove;
  if (grove) {
    let g = 0; grove.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([, n]) => { g += n; })));
    assert.ok(total > g, 'bigger than Redwood Hollow: ' + total + ' vs ' + g);
  }
  assert.deepEqual(plan.zones.map((z) => z.ceiling), ['plain', false, 'plain'], 'lobby and trading floor: plain ceiling; garden: glass roof');
});

for (const m of maps) {
  test('zone ' + m.name + ': size, layers, gates, reachability on both floors, spawns, pickups, prefab tiling', () => {
    const g = m.g, mez = m.layers['4.5'];
    assert.equal((g.w - 2) % 6, 0, 'diagrid bays run evenly across'); assert.equal((g.h - 2) % 6, 0, 'and along');
    assert.equal((g.w - 2) % 4, 0); assert.equal((g.h - 2) % 4, 0);
    assert.ok(g.w >= 44 && g.w <= 64 && g.h >= 44 && g.h <= 64, g.w + 'x' + g.h);
    for (const [y, L] of Object.entries(m.layers)) {
      assert.ok(y in LAYER_SYMS, 'layer ' + y);
      assert.equal(L.w, g.w); assert.equal(L.h, g.h);
      L.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok((LAYER_SYMS[y] + '.#').includes(ch), m.name + ' @' + y + ' ' + ch + ' at ' + c + ',' + r)));
    }
    assert.equal(!!m.layers['9'], true, 'ceiling fittings / glass roof layer');
    if (m.plan.ceiling === false) assert.ok(rects(m.layers['9'], '^').length > 0, 'a glass roof where there is no ceiling');
    for (let c = 0; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0))); assert.ok('#E'.includes(g.at(c, g.h - 1))); }
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const G = [...g.rows[0]].map((ch, c) => ch === 'G' ? c : -1).filter((c) => c >= 0);
    const E = [...g.rows[g.h - 1]].map((ch, c) => ch === 'E' ? c : -1).filter((c) => c >= 0);
    assert.deepEqual([G.length, G[2] - G[0], E.length, E[2] - E[0]], [3, 2, 3, 2]);
    G.forEach((c) => { assert.ok(GROUND.includes(g.at(c, 1)) && GROUND.includes(g.at(c, 2)), 'open in front of the exit'); });
    E.forEach((c) => { assert.ok(GROUND.includes(g.at(c, g.h - 2)), 'open behind the entry'); });
    let P = null;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') { assert.equal(P, null); P = [c, r]; } }));
    assert.ok(P);
    // stairs link the ground cell before their foot with the deck cell past their head
    const links = [];
    for (const ch of STAIRS) rects(g, ch).forEach((R) => {
      const north = ch === 'N' || ch === 'Z';
      for (let c = R.c; c < R.c + R.w; c++) {
        const lo = [c, north ? R.r + R.h : R.r - 1], hi = [c, north ? R.r - 1 : R.r + R.h];
        assert.ok(GROUND.includes(g.at(...lo)), m.name + ' stair foot ' + lo);
        assert.ok(mez && DECK.includes(mez.at(...hi)), m.name + ' stair head on the deck ' + hi);
        links.push([lo, hi]);
      }
    });
    const key = (L, c, r) => L + ':' + c + ',' + r, seen = new Set([key(0, ...P)]), q = [[0, ...P]];
    while (q.length) {
      const [L, c, r] = q.shift(), nb = [[1, 0], [-1, 0], [0, 1], [0, -1]].map(([dc, dr]) => [L, c + dc, r + dr]);
      links.forEach(([a, b]) => { if (L === 0 && a[0] === c && a[1] === r) nb.push([1, ...b]); if (L === 1 && b[0] === c && b[1] === r) nb.push([0, ...a]); });
      for (const n of nb) {
        const k = key(...n); if (seen.has(k)) continue;
        if (n[0] === 0 ? GROUND.includes(g.at(n[1], n[2])) : (mez && DECK.includes(mez.at(n[1], n[2])))) { seen.add(k); q.push(n); }
      }
    }
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (GROUND.includes(ch)) assert.ok(seen.has(key(0, c, r)), m.name + ' ground cell ' + c + ',' + r + ' sealed'); }));
    if (mez) mez.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (DECK.includes(ch)) assert.ok(seen.has(key(1, c, r)), m.name + ' deck cell ' + c + ',' + r + ' sealed'); }));
    assert.ok(G.some((c) => seen.has(key(0, c, 1))), 'P reaches the exit');
    // spawns: open ground (or deck) round each can, the ground ones away from P; a few on the deck where there is one
    let n = 0, nDeck = 0;
    [[g, GROUND, 0], [mez, DECK, 1]].forEach(([L, OPEN, lv]) => {
      if (!L) return;
      L.rows.forEach((row, r) => [...row].forEach((ch, c) => {
        if (ch !== 'S') return;
        n++; if (lv) nDeck++;
        if (!lv) assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14, m.name + ' spawn near P');
        for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(OPEN.includes(L.at(c + dc, r + dr)), m.name + ' spawn ' + c + ',' + r + ' crowded');
        if (lv) assert.ok(!STAIRS.includes(g.at(c, r)), 'deck spawn over a stair');
      }));
    });
    assert.ok(n >= 10 && n <= 16, m.name + ' spawns ' + n);
    if (mez) assert.ok(nDeck >= 3, 'spawns upstairs too');
    const count = (ch) => [g, mez].filter(Boolean).reduce((s, L) => s + L.rows.join('').split(ch).length - 1, 0);
    assert.ok(count('a') >= 2 && count('a') <= 3 && count('h') >= 2 && count('h') <= 3, 'pickups');
    // columns stand under and over the rail line
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'I') assert.equal(mez.at(c, r), 'i', 'column ' + c + ',' + r); }));
    // prefabs tile their blocks exactly, on every layer
    for (const L of [g, ...Object.values(m.layers)]) {
      for (const [ch, d] of Object.entries(TH.symbols)) {
        if (!d.size) continue;
        rects(L, ch).forEach((R) => assert.ok((R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0), m.name + ' ' + ch + ' ' + JSON.stringify(R)));
      }
    }
  });
}

test('wall chooser: every wall cell resolves to a kit piece; diagrid slices follow the 6 m bay, mirrored on the S and W walls', () => {
  const pieces = new Set(TH.allPieces());
  const SOLID = '#GE';
  for (const m of maps) {
    const g = m.g, solid = (c, r) => SOLID.includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
      if (!n && ![[-1, -1], [1, -1], [-1, 1], [1, 1]].some(([a, b]) => !solid(c + a, r + b))) continue;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const horiz = solid(c - 1, r) || solid(c + 1, r), vert = solid(c, r - 1) || solid(c, r + 1);
      const got = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, face);
      assert.ok(pieces.has(got), m.name + ' ' + c + ',' + r + ' ' + got);
      const edge = c === 0 || r === 0 || c === g.w - 1 || r === g.h - 1;
      if ((c === 0 || c === g.w - 1) && (r === 0 || r === g.h - 1)) assert.match(got, /^DiaCorner_/);
      if (edge && /^Dia_/.test(got)) {
        const along = (r === 0 || r === g.h - 1) ? c : r, k = (along - 1) % 6;
        assert.equal(got, 'Dia_' + ((r === g.h - 1 || c === 0) ? 5 - k : k), m.name + ' ' + c + ',' + r);
      }
      if (r === 0 && (g.at(c - 1, r) === 'G' || g.at(c + 1, r) === 'G')) assert.equal(got, 'GateSide');
    }
  }
});

test('outside: one skyline table for the kit and the shafts, rows due E S W N, the towers drawn up past each roof', () => {
  const ring = TH.backdrop.ring[0];
  assert.equal(ring.count, 4);
  assert.equal(ring.pieces.length, ring.count);
  ring.pieces.forEach((p) => assert.ok(TH.allPieces().includes(p) && Array.isArray(TH.skyline[p]), p));
  assert.equal(TH.below.skyline, TH.skyline, 'the city carries exactly the towers the kit builds');
  assert.equal(TH.below.shaftTop, TH.skylineBase + 1, 'shafts reach just inside the pieces\' bases');
  const STYLES = ['deco', 'needle', 'helipad', 'twist', 'prism', 'crane', 'obelisk', 'garden', 'slab'];
  Object.values(TH.skyline).forEach((rows) => {
    rows.forEach((t) => {
      assert.equal(t.length, 8);
      const [x, front, w, d, c, win, top, style] = t;
      assert.ok(Math.abs(x) + w / 2 <= 135 && front >= 4 && d > 0, 'inside the row');
      assert.match(c, /^#[0-9A-F]{6}$/); assert.match(win, /^#[0-9A-F]{6}$/);
      assert.ok(top > TH.skylineBase + 30 && STYLES.includes(style));
    });
    for (let i = 0; i < rows.length; i++) for (let j = i + 1; j < rows.length; j++) {
      const a = rows[i], b = rows[j];
      assert.ok(Math.abs(a[0] - b[0]) * 2 >= a[2] + b[2] + 2 || a[1] >= b[1] + b[3] + 2 || b[1] >= a[1] + a[3] + 2, 'towers ' + i + ' / ' + j + ' overlap');
    }
  });
  assert.equal(TH.below.towerTop.length, plan.zones.length + 1, 'a top for every zone tower and the exit core');
  TH.below.towerTop.forEach((t, i) => assert.ok(t > TH.wall.height + 2, 'tower ' + i + ' rises past its roof'));
  assert.ok(TH.below.bridges && TH.below.bridgeHole[2] > TH.wall.height, 'bridge openings reach over the bridge roof');
  assert.ok(TH.below.depth >= 300, 'ninety floors up');
});
