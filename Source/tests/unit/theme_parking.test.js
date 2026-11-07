// Deep Park theme (kit-parking): level plan and waves, zone layers (floor plan, markings, under-deck fittings, deck,
// deck markings, ceiling, the zone 2 platform and the zone 3 dock), prefab tiling, ramps and stairs that arrive on a
// walkable level, deck edges railed, columns continuing through the deck, spawns and pickups, the wall chooser (two
// storeys in the zone's level colours, corner ends, gate piers, dock shutters, piers under beams) and the paint jobs
// (palette cells mirrored from blender/parking_base.py).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/parking.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.parking;
const ZDIR = path.join(__dirname, '../../src/data/zones');

// mirrors zones.js Z.parse: the floor plan, then "@layer <y>" grids of the same size
function grid(rows, w, out) {
  const padded = rows.map((r) => r.slice(0, w).padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? out : padded[r][c] };
}
function parse(text) {
  const base = [], layers = []; let cur = base;
  for (const l of text.replace(/\r/g, '').split('\n')) {
    const m = /^@layer\s+(-?[\d.]+)/.exec(l);
    if (m) { cur = []; layers.push({ y: parseFloat(m[1]), rows: cur }); } else if (l.length) cur.push(l);
  }
  const w = Math.max(...base.map((r) => r.length)), g = grid(base, w, '#');
  g.layers = layers.map((L) => Object.assign(grid(L.rows, w, '.'), { y: L.y }));
  return g;
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
const plan = IB.LEVEL_PLANS.parking;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const layer = (g, y) => g.layers.find((L) => Math.abs(L.y - y) < 0.001);
const VEH = 'VHWTXYmkgA', CIRC = 'NURZzqOQ', PROPS = 'IiCBpobJKDLwF', DECKS = 'utd', MARK = '[]()v^<>:|%!?&$,*', FIT = '=+-~lfxc_1234';
const STAND = '.SahPEG';

test('parking theme: kit-parking indoors under a 7 m ceiling, level 19, three zones of hard waves', () => {
  assert.equal(TH.family, 'kit-parking');
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.env.ceiling.height);
  assert.equal(plan.zones.length, 3);
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); })));
  assert.ok(total >= 300, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers and their symbols, prefab tiling, spawns, pickups', () => {
    assert.ok(g.w >= 44 && g.h >= 44 && g.w * g.h >= 2000, name + ' ' + g.w + 'x' + g.h);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.equal(g.at(c, r), '.', 'exit approach');
    const ys = g.layers.map((L) => L.y);
    for (const y of [0.01, 3.2, 3.6, 3.61, 7]) assert.ok(ys.includes(y), name + ' layer ' + y);
    const allowed = (y) => y === 3.6 ? 'u r' + VEH + PROPS + 'Sah' : y === 1.8 ? 't r' + VEH + PROPS + CIRC + 'Sah' : y === 1.2 ? 'de' + VEH + PROPS + 'Sah'
      : (y === 3.2 || y === 7) ? FIT : MARK;
    for (const L of g.layers) L.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '.' || allowed(L.y).includes(ch), name + ' @' + L.y + ' ' + ch + ' at ' + c + ',' + r)));
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(('#.' + STAND + VEH + CIRC + PROPS).includes(ch), name + ' plan ' + ch + ' at ' + c + ',' + r)));
    for (const G of [g, ...g.layers]) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      rects(G, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
        if (typeof d.face === 'number' && Math.abs(Math.sin(d.face)) < 0.5) assert.ok(R.w % d.size[0] === 0 && R.h % d.size[1] === 0, name + ' fixed-facing ' + ch + ' not turned');
      });
    }
    const P = []; let S = 0, a = 0, h = 0;
    for (const G of [g, ...g.layers]) G.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++;
      if (ch === 'S') {
        S++;
        for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(G.at(c + dc, r + dr)) || 'utde'.includes(G.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      }
    }));
    assert.equal(P.length, 1);
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    for (const G of [g, ...g.layers]) G.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'S') assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P ' + c + ',' + r);
    }));
  });
}

// the level a ramp / stair block on layer y rises to, and the cells just beyond its top end
const RISE = { N: [0, -1], R: [0, -1], Z: [0, -1], O: [0, -1], Q: [0, -1], U: [0, 1], z: [-1, 0], q: [1, 0] };
const HIGH = { N: 3.6, U: 3.6, Z: 3.6, z: 3.6, q: 3.6, O: 1.2, Q: 1.2 };
test('ramps and stairs: every top end arrives on walkable deck (no rail across it), every foot on open ground', () => {
  for (const { name, g } of maps) {
    let n = 0;
    for (const G of [g, layer(g, 1.8)].filter(Boolean)) for (const ch of CIRC) rects(G, ch).forEach((R) => {
      n++;
      const d = RISE[ch], hi = ch === 'R' ? (G === g ? 1.8 : 3.6) : HIGH[ch], top = layer(g, hi);
      const cells = [];
      if (d[1]) for (let c = R.c + 1; c < R.c + R.w - 1; c++) cells.push([c, d[1] < 0 ? R.r - 1 : R.r + R.h, c, d[1] < 0 ? R.r + R.h : R.r - 1]);
      else for (let r = R.r + 1; r < R.r + R.h - 1; r++) cells.push([d[0] < 0 ? R.c - 1 : R.c + R.w, r, d[0] < 0 ? R.c + R.w : R.c - 1, r]);
      for (const [tc, tr, fc, fr] of cells) {
        assert.ok(DECKS.includes(top.at(tc, tr)) || 'uSah'.includes(top.at(tc, tr)), name + ' ' + ch + ' top ' + tc + ',' + tr + ' on ' + hi + ' is ' + top.at(tc, tr));
        const foot = G === g ? g.at(fc, fr) : G.at(fc, fr);
        assert.ok((G === g ? STAND : 't').includes(foot), name + ' ' + ch + ' foot ' + fc + ',' + fr + ' is ' + foot);
      }
    });
    assert.ok(n >= 4, name + ' has ramps and stairs');
  }
});

test('deck and platform edges over open space are railed; columns under the deck carry on above it', () => {
  for (const { name, g } of maps) {
    for (const [y, ch] of [[3.6, 'u'], [1.8, 't']]) {
      const D = layer(g, y); if (!D) continue;
      for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
        if (D.at(c, r) !== ch) continue;
        for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          if (D.at(c + dc, r + dr) !== '.' || g.at(c + dc, r + dr) === '#') continue;
          // an unrailed edge cell must be where a ramp / stair arrives: the cell beyond it is a circulation block
          const below = [g.at(c + dc, r + dr), (layer(g, 1.8) || { at: () => '.' }).at(c + dc, r + dr)];
          assert.ok(below.some((b) => CIRC.includes(b)), name + ' @' + y + ' open edge at ' + c + ',' + r);
        }
      }
    }
    const D = layer(g, 3.6);
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'I') assert.equal(D.at(c, r), 'i', name + ' column ' + c + ',' + r); }));
  }
});

test('wall chooser: two storeys in the zone levels, corner ends, gate piers, lift / stair doors, dock shutters', () => {
  const pieces = new Set(TH.allPieces());
  const SOLID = '#GE', LV = ['B1', 'B2', 'B3', 'B4'];
  maps.forEach(({ name, g }, zi) => {
    const solid = (c, r) => SOLID.includes(g.at(c, r));
    let ends = 0, dock = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
      const exposed = n || [[-1, -1], [1, -1], [-1, 1], [1, 1]].some(([a, b]) => !solid(c + a, r + b));
      if (!exposed) continue;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const horiz = solid(c - 1, r) || solid(c + 1, r), vert = solid(c, r - 1) || solid(c, r + 1);
      const got = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, face);
      [].concat(got).forEach((p) => assert.ok(pieces.has(p), name + ' ' + c + ',' + r + ' ' + p));
      if (face === 'none') { assert.match(got, /^Corner_/); continue; }
      if ((face === 'S' || face === 'N') && 'GE'.includes(g.at(c - 1, r) + g.at(c + 1, r)[0]) && (g.at(c - 1, r) === 'G' || g.at(c + 1, r) === 'G' || g.at(c - 1, r) === 'E' || g.at(c + 1, r) === 'E')) { assert.equal(got, 'GateSide'); continue; }
      if (!Array.isArray(got)) continue;
      assert.match(got[0], new RegExp('^Lo_' + LV[zi + 1] + '_'), name + ' lower storey on the floor level');
      // beside the split-level platform both storeys carry the floor's level; elsewhere the upper one the deck's
      const split = /_Split$/.test(got[0]);
      assert.equal(split, !!layer(g, 1.8) && layer(g, 1.8).at(c + (face === 'E' ? 1 : face === 'W' ? -1 : 0), r + (face === 'S' ? 1 : face === 'N' ? -1 : 0)) !== '.', name + ' split ' + c + ',' + r);
      assert.match(got[1], new RegExp('^Up_' + LV[split ? zi + 1 : zi] + '_'), name + ' upper storey level');
      const nearCorner = (face === 'S' || face === 'N') ? (c === 1 || c === g.w - 2) : (r === 1 || r === g.h - 2);
      assert.equal(/_End[LR]$/.test(got[0]), nearCorner, name + ' end module ' + c + ',' + r);
      if (nearCorner) ends++;
      if (/_Dock$/.test(got[0])) dock++;
    }
    assert.ok(ends === 8, name + ' ends ' + ends);
    assert.equal(dock > 0, !!layer(g, 1.2), name + ' dock shutters only behind a dock');
  });
});

test('paint jobs: car paint and level colours map onto the kit palette cells (blender/parking_base.py)', () => {
  const src = fs.readFileSync(path.join(__dirname, '../../blender/parking_base.py'), 'utf8');
  const names = ['HULL', 'ink', 'paper', 'white', 'teal', 'amber', 'gunmetal', 'red'].concat([...src.matchAll(/\('(\w+)', '#[0-9A-Fa-f]{6}'\)/g)].map((m) => m[1]));
  assert.ok(names.length <= 64);
  const cell = (n) => names.indexOf(n);
  const car = TH.symbols.V.paint;
  assert.deepEqual(car.from, [cell('paint')]);
  car.to.forEach((t) => assert.ok(t[0] >= cell('paint') && t[0] <= cell('pBrown'), 'car paint ' + t));
  assert.ok(new Set(car.to.map((t) => t[0])).size >= 10, 'many paint colours');
  const lv = TH.symbols.I.paint;
  assert.deepEqual(lv.from, [cell('lvB'), cell('lvBL')]);
  // zone 0: floor B2 green, deck B1 blue; zone 2: floor B4 purple, deck B3 orange
  assert.deepEqual(lv.to(0, 0), [cell('lvG'), cell('lvGL')]);
  assert.deepEqual(lv.to(0, 3.6), [cell('lvB'), cell('lvBL')]);
  assert.deepEqual(lv.to(1, 1.8), [cell('lvO'), cell('lvOL')]);
  assert.deepEqual(lv.to(2, 0), [cell('lvP'), cell('lvPL')]);
  assert.deepEqual(lv.to(2, 3.6), [cell('lvO'), cell('lvOL')]);
  for (const k of ['N', 'U', 'R', 'Z', 'i', 'C']) assert.equal(TH.symbols[k].paint, lv, k);
  for (const k of ['V', 'H', 'W', 'T', 'X', 'm', 'k']) assert.equal(TH.symbols[k].paint, car, k);
});
