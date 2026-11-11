// Halcyon Vega theme (kit-cargoship): level plan and waves, zone layers (main deck with hatch covers, hold and engine
// room with walkways at 5.2 m and a 13 m deckhead), prefab tiling, stairs that arrive on walkable deck, spawns and
// pickups, the wall chooser per zone kind, container paint (palette cells mirrored from blender/cargo_base.py), and
// every piece the theme can place being a real mesh in the kit GLB.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/cargoship.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.cargoship;
const ZDIR = path.join(__dirname, '../../src/data/zones');

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
const plan = IB.LEVEL_PLANS.cargoship;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const layer = (g, y) => g.layers.find((L) => Math.abs(L.y - y) < 0.001);
const STAND = '.SahPEG';

test('cargoship theme: kit-cargoship at sea, 13 m deckhead below deck, three zones of hard waves', () => {
  assert.equal(TH.family, 'kit-cargoship');
  assert.ok(TH.env.sky && TH.env.clouds, 'open sky');
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.env.ceiling.height);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(plan.zones.length, 3);
  assert.equal(plan.zones[0].ceiling, false, 'the main deck is open to the sky');
  assert.ok(plan.zones[1].floor && plan.zones[2].floor, 'hold and engine room have their own floors');
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => {
    total += n; types.add(t);
    if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave');
  })));
  assert.ok(total >= 300, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols, prefab tiling, spawns, pickups', () => {
    assert.ok(g.w >= 44 && g.h >= 44 && g.w * g.h >= 2000, name + ' ' + g.w + 'x' + g.h);
    assert.ok(g.rows[0].indexOf('GGG') > 0, 'exit gate');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const gc = g.rows[0].indexOf('GGG');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.equal(g.at(c, r), '.', 'exit approach');
    const known = new Set(Object.keys(TH.symbols).concat(['#', '.', 'S', 'P', 'E', 'G', 'a', 'h', '^']));
    for (const G of [g, ...g.layers]) G.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(known.has(ch), name + ' @' + (G.y || 0) + ' ' + ch + ' at ' + c + ',' + r)));
    for (const G of [g, ...g.layers]) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      rects(G, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
      });
    }
    const P = []; let S = 0, a = 0, h = 0;
    for (const G of [g, ...g.layers]) G.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++;
      if (ch === 'S') {
        S++;
        for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok((STAND + 'twrL').includes(G.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      }
    }));
    assert.equal(P.length, 1);
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    for (const G of [g, ...g.layers]) G.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'S') assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P ' + c + ',' + r);
    }));
    for (const dc of [-2, -1, 1, 2]) assert.equal(g.at(P[0][0] + dc, P[0][1] - 4), '.', 'weapon stand cell');
  });
}

test('stairs: every top end arrives on walkable deck, every foot on open floor', () => {
  const RISE = { Z: -1, X: -1, U: 1, N: 1 }, TOP = { Z: 1.8, U: 1.8, X: 5.2, N: 5.2 };
  for (const { name, g } of maps) {
    let n = 0;
    for (const ch of Object.keys(RISE)) rects(g, ch).forEach((R) => {
      n++;
      const top = layer(g, TOP[ch]), d = RISE[ch];
      for (let c = R.c + 1; c < R.c + R.w - 1; c++) {
        const tr = d < 0 ? R.r - 1 : R.r + R.h, fr = d < 0 ? R.r + R.h : R.r - 1;
        assert.ok('twSah'.includes(top.at(c, tr)), name + ' ' + ch + ' top ' + c + ',' + tr + ' is ' + top.at(c, tr));
        assert.ok(STAND.includes(g.at(c, fr)) || 'e'.includes(g.at(c, fr)), name + ' ' + ch + ' foot ' + c + ',' + fr + ' is ' + g.at(c, fr));
        if (TOP[ch] === 5.2) for (let r = R.r; r < R.r + R.h; r++) assert.equal(top.at(c, r), '.', name + ' nothing over the stair ' + c + ',' + r);
      }
    });
    assert.ok(n >= 3, name + ' has stairs');
  }
});

test('walkway edges over open space are railed (except where stairs arrive and along the engine)', () => {
  for (const { name, g } of maps.slice(1)) {
    const D = layer(g, 5.2);
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      if (D.at(c, r) !== 'w') continue;
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        if (D.at(c + dc, r + dr) !== '.' || g.at(c + dc, r + dr) === '#') continue;
        const ok = 'XN'.includes(g.at(c + dc, r + dr)) || (dc && g.at(c + dc, r) === 'M');
        assert.ok(ok, name + ' open walkway edge at ' + c + ',' + r);
      }
    }
  }
});

test('wall chooser: superstructure front, forecastle, bulwarks, hold bulkheads and shell, engine room plating', () => {
  const pieces = new Set(TH.allPieces());
  const SOLID = '#GE';
  const seen = maps.map(() => new Set());
  maps.forEach(({ name, g }, zi) => {
    const solid = (c, r) => SOLID.includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
      const exposed = n || [[-1, -1], [1, -1], [-1, 1], [1, 1]].some(([a, b]) => !solid(c + a, r + b));
      if (!exposed) continue;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const horiz = solid(c - 1, r) || solid(c + 1, r), vert = solid(c, r - 1) || solid(c, r + 1);
      const got = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, face);
      if (got === null) { assert.ok((face === 'S' || face === 'N') && (g.at(c - 1, r) + g.at(c + 1, r) + g.at(c - 2, r) + g.at(c + 2, r)).match(/[GE]/), name + ' empty module only beside a door ' + c + ',' + r); continue; }
      [].concat(got).forEach((p) => { assert.ok(pieces.has(p), name + ' ' + c + ',' + r + ' ' + p); seen[zi].add(String(p).split('_')[0]); });
    }
  });
  for (const k of ['Sup', 'Fc', 'Bul', 'Corner']) assert.ok(seen[0].has(k), 'deck ' + k);
  for (const k of ['Hb', 'Hs', 'Corner']) assert.ok(seen[1].has(k), 'hold ' + k);
  for (const k of ['Er', 'Corner']) assert.ok(seen[2].has(k), 'engine room ' + k);
});

test('container paint: four slot pairs repainted to distinct line colours (blender/cargo_base.py cells)', () => {
  const src = fs.readFileSync(path.join(__dirname, '../../blender/cargo_base.py'), 'utf8');
  const names = ['HULL', 'ink', 'paper', 'white', 'teal', 'amber', 'gunmetal', 'red'].concat([...src.matchAll(/\('(\w+)', '#[0-9A-Fa-f]{6}'\)/g)].map((m) => m[1]));
  assert.ok(names.length <= 64);
  const cell = (n) => names.indexOf(n);
  const P = TH.symbols['1'].paint;
  assert.deepEqual(P.from, ['cBlu', 'cBluD', 'cRed', 'cRedD', 'cGrn', 'cGrnD', 'cOra', 'cOraD'].map(cell));
  assert.ok(P.to.length >= 12);
  P.to.forEach((job) => {
    assert.equal(job.length, 8);
    for (let i = 0; i < 8; i += 2) { assert.ok(job[i] >= cell('cBlu') && job[i] < cell('cWht'), 'main ' + job[i]); assert.equal(job[i + 1], job[i] + 1, 'rib cell'); }
    assert.equal(new Set([job[0], job[2], job[4], job[6]]).size, 4, 'four different colours');
  });
  for (const k of ['2', '3', '4', '5', '6', 'e', 'i', 'j', 'k', 'l', 'f']) assert.equal(TH.symbols[k].paint, P, k);
});

test('every piece the theme places is a mesh in the kit GLB', () => {
  const d = fs.readFileSync(path.join(__dirname, '../../assets/fps-kit-cargoship.glb'));
  const g = JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
  const meshes = new Set(g.nodes.filter((n) => n.mesh !== undefined).map((n) => n.name));
  for (const n of TH.allPieces()) assert.ok(meshes.has(TH.prefix + n), 'mesh ' + n);
  assert.ok(d.length <= 2.5 * 1024 * 1024, 'kit GLB ' + d.length);
});
