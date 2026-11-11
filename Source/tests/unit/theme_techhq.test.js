// NOVYX HQ theme (kit-techhq): level plan, zone layers (floor plan, floor finishes, mezzanine deck, ceiling / roof),
// sizes that keep the facade bays and ceiling tiles even, gates, reachability on both floors (stairs and the
// bleacher land on the deck, the lab's doorways open onto the terrace), spawns, pickups, prefab tiling, the wall
// chooser (every wall and doorway cell resolves to a kit piece; mullions every 3 m; the terrace's windscreen) and
// the outside: the skyline table the kit and the city's shafts share, the mid-rise city options.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/parking.js');
require('../../src/data/themes/techhq.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.techhq;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function grid(rows, layers) {
  return { w: rows[0].length, h: rows.length, rows, layers, at: (c, r) => (r < 0 || r >= rows.length || c < 0 || c >= rows[0].length) ? '#' : rows[r][c] };
}
function parse(text) {
  const out = { base: [], layers: {} };
  let cur = out.base;
  text.replace(/\r/g, '').split('\n').filter((l) => l.length).forEach((l) => {
    const m = /^@layer\s+(-?[\d.]+)/.exec(l);
    if (m) { cur = []; out.layers[m[1]] = cur; } else cur.push(l);
  });
  Object.keys(out.layers).forEach((k) => { out.layers[k] = grid(out.layers[k]); out.layers[k].y = +k; });
  out.g = grid(out.base, Object.values(out.layers));
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
const plan = IB.LEVEL_PLANS.techhq;
const maps = plan.zones.map((z) => ({ name: z.map, plan: z, ...parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const GROUND = '.ahPn', DECK = 'ulah', STAIRS = 'NVZ';
const LAYER_SYMS = { '0': 'qwzy', '4': 'urilShaLMbkCdmpXA[]', '8': '~:^&' };

test('techhq theme: kit-techhq, double-height floors, a deck at 4 m, sky outside, a far camera and a tier-scaled fog', () => {
  assert.equal(TH.family, 'kit-techhq');
  assert.equal(TH.prefix, 'KIT_TECHHQ_');
  assert.equal(TH.wall.height, 8);
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(Array.isArray(TH.env.sky) && TH.env.sky[1] === TH.env.fog.color && TH.below.haze === TH.env.fog.color, 'sky horizon, fog and city haze are one colour');
  assert.ok(TH.env.far >= TH.below.horizon, 'the camera sees the haze ground out to the horizon');
  assert.ok(TH.env.fog.tierScale);
  assert.ok(TH.budget.total <= 90000);
  assert.deepEqual(TH.wall.passage.solid, [[2.7, 8]], 'the lab\'s doorways are open below 2.7 m');
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
  // paint jobs point at the brand cells of the kit palette (violet 23, coral 25, sun 26, mint 27)
  [TH.symbols.L.paint, TH.symbols.b.paint].forEach((P) => { assert.deepEqual(P.from, [23]); P.to.forEach((t) => assert.ok([23, 25, 26, 27].includes(t[0]))); });
});

test('level plan: three zones, soldiers and blade bots, bombers kept to two a wave, the lab open to the sky', () => {
  assert.equal(plan.themeId, 'techhq');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f);
  const types = new Set(); let total = 0;
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => {
    types.add(t); total += n;
    assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t), t);
    if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave');
  })));
  for (const t of ['crawler', 'gunner', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
  const parking = IB.LEVEL_PLANS.parking;
  if (parking) {
    let p = 0; parking.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([, n]) => { p += n; })));
    assert.ok(total >= p * 0.9, 'on the level 19 scale: ' + total + ' vs ' + p);
  }
  assert.deepEqual(plan.zones.map((z) => z.ceiling), ['plain', 'plain', false]);
});

for (const m of maps) {
  test('zone ' + m.name + ': size, layers, gates, reachability on both floors, spawns, pickups, prefab tiling', () => {
    const g = m.g, mez = m.layers['4'];
    assert.equal(g.w, 62, 'facade bays (3 m) and ceiling tiles (4 m) run evenly');
    assert.equal((g.h - 2) % 4, 0);
    assert.ok(g.h >= 44 && g.h <= 64, g.w + 'x' + g.h);
    for (const [y, L] of Object.entries(m.layers)) {
      assert.ok(y in LAYER_SYMS, 'layer ' + y);
      assert.equal(L.w, g.w); assert.equal(L.h, g.h);
      L.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok((LAYER_SYMS[y] + '.#').includes(ch), m.name + ' @' + y + ' ' + ch + ' at ' + c + ',' + r)));
    }
    assert.ok(mez, 'every zone has a deck');
    assert.ok(m.layers['8'], 'ceiling fittings / roof layer');
    if (m.plan.ceiling === false) assert.ok(rects(m.layers['8'], '^').length > 0, 'roof tiles where there is no ceiling');
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
    // stairs (and the bleacher) link the ground cell before their foot with the deck cell past their head
    const links = [];
    for (const ch of STAIRS) rects(g, ch).forEach((R) => {
      const north = ch !== 'V';
      for (let c = R.c; c < R.c + R.w; c++) {
        const lo = [c, north ? R.r + R.h : R.r - 1], hi = [c, north ? R.r - 1 : R.r + R.h];
        assert.ok(GROUND.includes(g.at(...lo)), m.name + ' stair foot ' + lo);
        assert.ok(DECK.includes(mez.at(...hi)), m.name + ' stair head on the deck ' + hi);
        links.push([lo, hi]);
      }
    });
    assert.ok(links.length >= 6, 'at least two ways up');
    const key = (L, c, r) => L + ':' + c + ',' + r, seen = new Set([key(0, ...P)]), q = [[0, ...P]];
    while (q.length) {
      const [L, c, r] = q.shift(), nb = [[1, 0], [-1, 0], [0, 1], [0, -1]].map(([dc, dr]) => [L, c + dc, r + dr]);
      links.forEach(([a, b]) => { if (L === 0 && a[0] === c && a[1] === r) nb.push([1, ...b]); if (L === 1 && b[0] === c && b[1] === r) nb.push([0, ...a]); });
      for (const n of nb) {
        const k = key(...n); if (seen.has(k)) continue;
        if (n[0] === 0 ? GROUND.includes(g.at(n[1], n[2])) : DECK.includes(mez.at(n[1], n[2]))) { seen.add(k); q.push(n); }
      }
    }
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (GROUND.includes(ch)) assert.ok(seen.has(key(0, c, r)), m.name + ' ground cell ' + c + ',' + r + ' sealed'); }));
    mez.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (DECK.includes(ch)) assert.ok(seen.has(key(1, c, r)), m.name + ' deck cell ' + c + ',' + r + ' sealed'); }));
    assert.ok(G.some((c) => seen.has(key(0, c, 1))), 'P reaches the exit');
    // spawns: open ground (or deck) round each can, the ground ones away from P; a few on the deck
    let n = 0, nDeck = 0;
    [[g, GROUND, 0], [mez, DECK, 1]].forEach(([L, OPEN, lv]) => {
      L.rows.forEach((row, r) => [...row].forEach((ch, c) => {
        if (ch !== 'S') return;
        n++; if (lv) nDeck++;
        if (!lv) assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14, m.name + ' spawn near P');
        for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(OPEN.includes(L.at(c + dc, r + dr)), m.name + ' spawn ' + c + ',' + r + ' crowded');
        if (lv) assert.ok(!STAIRS.includes(g.at(c, r)), 'deck spawn over a stair');
      }));
    });
    assert.ok(n >= 10 && n <= 16, m.name + ' spawns ' + n);
    assert.ok(nDeck >= 3, 'spawns upstairs too');
    const count = (ch) => [g, mez].reduce((s, L) => s + L.rows.join('').split(ch).length - 1, 0);
    assert.ok(count('a') >= 2 && count('a') <= 3 && count('h') >= 2 && count('h') <= 3, 'pickups');
    // columns stand under and over the rail line; nothing of the deck over a stair
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'I') assert.equal(mez.at(c, r), 'i', 'column ' + c + ',' + r);
      if (STAIRS.includes(ch)) assert.equal(mez.at(c, r), '.', 'deck over a stair at ' + c + ',' + r);
    }));
    // prefabs tile their blocks exactly, on every layer
    for (const L of [g, ...Object.values(m.layers)]) {
      for (const [ch, d] of Object.entries(TH.symbols)) {
        if (!d.size) continue;
        rects(L, ch).forEach((R) => assert.ok((R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0), m.name + ' ' + ch + ' ' + JSON.stringify(R)));
      }
    }
  });
}

test('wall chooser: every wall and doorway cell resolves to a kit piece; a mullion every 3 m; the terrace gets the windscreen', () => {
  const pieces = new Set(TH.allPieces());
  const SOLID = '#GEn';
  let screens = 0, glass = 0, doors = 0;
  for (const m of maps) {
    const g = m.g, solid = (c, r) => SOLID.includes(g.at(c, r));
    const L0 = m.layers['0'];
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#' && g.at(c, r) !== 'n') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), nOpen = oS + oN + oE + oW;
      if (!nOpen && ![[-1, -1], [1, -1], [-1, 1], [1, 1]].some(([a, b]) => !solid(c + a, r + b))) continue;
      const face = nOpen === 0 ? 'none' : nOpen === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const horiz = solid(c - 1, r) || solid(c + 1, r), vert = solid(c, r - 1) || solid(c, r + 1);
      const got = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, face);
      assert.ok(pieces.has(got), m.name + ' ' + c + ',' + r + ' ' + got);
      if (got === 'Screen') screens++;
      if (got === 'GlassWall') glass++;
      if (got === 'GlassDoor') { doors++; assert.equal(g.at(c, r), 'n'); }
      const edge = c === 0 || r === 0 || c === g.w - 1 || r === g.h - 1;
      if (edge && /^Win_/.test(got)) {
        const along = (r === 0 || r === g.h - 1) ? c : r;
        assert.equal(got === 'Win_M', (along - 1) % 3 === 1, m.name + ' mullion at ' + c + ',' + r);
      }
      if (got === 'Screen') { const ic = c === 0 ? 1 : c === g.w - 1 ? g.w - 2 : c, ir = r === 0 ? 1 : r === g.h - 1 ? g.h - 2 : r; assert.ok('wz'.includes(L0.at(ic, ir)), 'a windscreen only by the terrace'); }
      if (r === 0 && (g.at(c - 1, r) === 'G' || g.at(c + 1, r) === 'G')) assert.equal(got, 'GateSide');
    }
  }
  assert.ok(screens > 40 && glass > 40 && doors === 10, [screens, glass, doors].join(' '));
});

test('outside: one skyline table for the kit and the shafts, the zone towers, a mid-rise city with street life', () => {
  const ring = TH.backdrop.ring[0];
  assert.equal(ring.count, 4);
  assert.equal(ring.pieces.length, ring.count);
  ring.pieces.forEach((p) => assert.ok(TH.allPieces().includes(p) && Array.isArray(TH.skyline[p]), p));
  assert.equal(TH.below.skyline, TH.skyline);
  assert.equal(TH.below.shaftTop, TH.skylineBase + 1);
  const STYLES = ['brick', 'tower', 'garden', 'glass', 'court', 'solar', 'crane', 'hotel'];
  let above = 0, below = 0;
  Object.values(TH.skyline).forEach((rows) => {
    rows.forEach((t) => {
      assert.equal(t.length, 8);
      const [x, front, w, d, c, win, top, style] = t;
      assert.ok(Math.abs(x) + w / 2 <= 135 && front >= 4 && d > 0, 'inside the row');
      assert.match(c, /^#[0-9A-F]{6}$/); assert.match(win, /^#[0-9A-F]{6}$/);
      assert.ok(top > TH.skylineBase + 20 && STYLES.includes(style));
      if (top > 0) above++; else below++;
    });
    for (let i = 0; i < rows.length; i++) for (let j = i + 1; j < rows.length; j++) {
      const a = rows[i], b = rows[j];
      assert.ok(Math.abs(a[0] - b[0]) * 2 >= a[2] + b[2] + 2 || a[1] >= b[1] + b[3] + 2 || b[1] >= a[1] + a[3] + 2, 'buildings ' + i + ' / ' + j + ' overlap');
    }
  });
  assert.ok(below > above * 2 && above >= 2, 'mostly lower than us, a few towers above');
  const B = TH.below;
  assert.equal(B.towerTop.length, plan.zones.length + 1, 'a top for every zone tower and the exit');
  B.towerTop.forEach((t) => assert.ok(t > TH.wall.height, 'skins rise past the roof'));
  assert.ok(!B.bridges, 'lift lobbies sit on set-back blocks, not bridges');
  assert.ok(B.depth >= 90 && B.depth <= 160, 'a mid-rise: ' + B.depth);
  assert.ok(B.topMax < -TH.wall.height && B.topMax > -B.depth, 'city roofs stay below the floor');
  assert.equal(B.winBand.length, 5);
  assert.ok(B.winBand[1] < B.winBand[2] && B.winBand[2] <= 1);
  assert.ok(B.cars.colors.length >= 4 && B.cars.every > 4 && B.trees.every > 3 && B.roofs.radius > 0);
});
