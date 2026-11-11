// Kolvane Station K-7 theme (kit-arctic): level plan and waves (two zones), zone layers (the open trench and the
// station's 3.7 m ceilings; the deep labs' 4.4 m lab ceilings, catwalks at 4.5 / 7 m and the 12 m ice ceiling),
// prefab tiling, doors in their wall lines, stairs that arrive on walkable deck, spawns and pickups, the wall chooser
// per finish, the drifts, and every piece the theme can place being a real mesh in the kit GLB (under 2.5 MB).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/arctic.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.arctic;
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
const plan = IB.LEVEL_PLANS.arctic;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const layer = (g, y) => g.layers.find((L) => Math.abs(L.y - y) < 0.001);
const STAND = '.SahPEG';
const DOORS = 'DdBLlV,';

test('arctic theme: kit-arctic, open trench then a 12 m ice ceiling, two zones of hard waves', () => {
  assert.equal(TH.family, 'kit-arctic');
  assert.ok(TH.env.sky, 'a sky over the trench');
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(typeof TH.terrain.height, 'function');
  assert.equal(plan.zones.length, 2);
  assert.equal(plan.zones[0].ceiling, false, 'the trench is open to the sky');
  assert.notEqual(plan.zones[1].ceiling, false, 'the deep labs are under the ice');
  let total = 0; const types = new Set();
  plan.zones.forEach((z, zi) => z.waves.forEach((w, wi) => w.forEach(([t, n]) => {
    total += n; types.add(t);
    assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t) || ['mech', 'hawk', 'grenadier'].includes(t), t);
    if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave');
    if (zi === 0 && wi === 0) assert.ok(!['soldier', 'blader', 'grenadier'].includes(t), 'the first wave has no elites');
  })));
  assert.ok(total >= 280, 'robots ' + total);
  for (const t of ['crawler', 'soldier', 'blader']) assert.ok(types.has(t), t);
  // drifts only on the trench floor, the deep labs flat
  let hi = 0;
  for (let r = 0; r < 66; r++) for (let c = 0; c < 64; c++) { hi = Math.max(hi, TH.terrain.height(c, r, 0)); assert.equal(TH.terrain.height(c, r, 1), 0); if (r < 35) assert.equal(TH.terrain.height(c, r, 0), 0); }
  assert.ok(hi > 0.4 && hi <= 1.0, 'drift height ' + hi);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols, prefab tiling, doors, spawns, pickups', () => {
    assert.ok(g.w >= 60 && g.h >= 60 && g.w <= 80 && g.h <= 80, name + ' ' + g.w + 'x' + g.h);
    assert.ok(g.rows[0].indexOf('GGG') > 0, 'exit gate');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const gc = g.rows[0].indexOf('GGG');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.equal(g.at(c, r), '.', 'exit approach');
    const known = new Set(Object.keys(TH.symbols).concat(['#', '.', 'S', 'P', 'E', 'G', 'a', 'h']));
    for (const G of [g, ...g.layers]) G.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(known.has(ch), name + ' @' + (G.y || 0) + ' ' + ch + ' at ' + c + ',' + r)));
    for (const G of [g, ...g.layers]) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      rects(G, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
      });
    }
    // every door block closes a wall line: wall at both ends, open on both faces
    for (const ch of DOORS) rects(g, ch).forEach((R) => {
      const along = R.w > R.h;
      const ends = along ? [[R.c - 1, R.r], [R.c + R.w, R.r]] : [[R.c, R.r - 1], [R.c, R.r + R.h]];
      ends.forEach(([c, r]) => assert.equal(g.at(c, r), '#', name + ' door ' + ch + ' end ' + c + ',' + r));
      const faces = along ? [[R.c + 1, R.r - 1], [R.c + 1, R.r + R.h]] : [[R.c - 1, R.r + 1], [R.c + R.w, R.r + 1]];
      faces.forEach(([c, r]) => assert.notEqual(g.at(c, r), '#', name + ' door ' + ch + ' face ' + c + ',' + r));
    });
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++;
      if (ch === 'S') {
        S++;
        for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      }
    }));
    assert.equal(P.length, 1);
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'S') assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P ' + c + ',' + r); }));
    for (const dc of [-2, -1, 1, 2]) assert.equal(g.at(P[0][0] + dc, P[0][1] - 4), '.', 'weapon stand cell');
    // ceiling tiles only over cells that are not wall; one tile layer per zone
    const C = g.layers.find((L) => L.y > 3 && L.y < 5 && L.rows.some((row) => /[=+_%~-]/.test(row)));
    assert.ok(C, name + ' has a ceiling-tile layer');
    C.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch !== '.') assert.ok(!('#' + DOORS).includes(g.at(c, r)), name + ' tile over wall ' + c + ',' + r); }));
  });
}

test('stairs arrive on walkable deck, their feet on open floor; nothing stands under the catwalks that reaches them', () => {
  const g = maps[1].g, D = layer(g, 4.5), T = layer(g, 7);
  let n = 0;
  for (const [ch, G, top, dir] of [['X', g, D, -1], ['N', g, D, 1], ['<', D, T, -1]]) rects(G, ch).forEach((R) => {
    n++;
    for (let c = R.c + 1; c < R.c + R.w - 1; c++) {
      const tr = dir < 0 ? R.r - 1 : R.r + R.h, fr = dir < 0 ? R.r + R.h : R.r - 1;
      assert.ok('wSah'.includes(top.at(c, tr)), ch + ' top ' + c + ',' + tr + ' is ' + top.at(c, tr));
      assert.ok(G === g ? STAND.includes(g.at(c, fr)) : 'w'.includes(D.at(c, fr)), ch + ' foot ' + c + ',' + fr);
    }
  });
  assert.ok(n >= 5, 'stairs ' + n);
  for (const L of [D, T]) L.rows.forEach((row, r) => [...row].forEach((ch, c) => {
    if (ch === '.') return;
    assert.ok(!'()$/'.includes(g.at(c, r)), 'tall machine under a catwalk at ' + c + ',' + r);
    if (L === T) assert.equal(D.at(c, r), '.', 'two decks over one cell at ' + c + ',' + r);
  }));
  // the buried module's snow steps arrive at its roof
  const g1 = maps[0].g;
  rects(g1, 'Z').forEach((R) => assert.equal(g1.at(R.c + 1, R.r - 1), 'U'));
  rects(g1, 'z').forEach((R) => assert.equal(g1.at(R.c + 1, R.r + R.h), 'U'));
});

test('catwalk edges over open space are railed (except where stairs arrive)', () => {
  const g = maps[1].g;
  for (const y of [4.5, 7]) {
    const D = layer(g, y);
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      if (D.at(c, r) !== 'w') continue;
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        if (D.at(c + dc, r + dr) !== '.' || g.at(c + dc, r + dr) === '#') continue;
        // the only open edge is the one a stair arrives over (its top step meets the deck there)
        const arrive = dr !== 0 && ('XN'.includes(g.at(c, r + dr)) || layer(g, 4.5).at(c, r + dr) === '<');
        assert.ok(arrive, 'open edge at ' + c + ',' + r + ' @' + y);
      }
    }
  }
});

test('wall chooser: firn, the ramp, facade and name board, station, mess, lab, shell, plant, glacier ice; signs', () => {
  const pieces = new Set(TH.allPieces());
  const SOLID = '#GE' + DOORS;
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
      if (got === null) { assert.ok((face === 'S' || face === 'N') && /[GE]/.test(g.at(c - 1, r) + g.at(c + 1, r) + g.at(c - 2, r) + g.at(c + 2, r)), name + ' empty module only beside a gate ' + c + ',' + r); continue; }
      [].concat(got).forEach((p) => { assert.ok(pieces.has(p), name + ' ' + c + ',' + r + ' ' + p); seen[zi].add(String(p).split('_')[0]); });
    }
  });
  for (const k of ['Firn', 'Ramp', 'Fac', 'NameBoard', 'S', 'M', 'Sign', 'CornerF', 'CornerS']) assert.ok(seen[0].has(k), 'surface ' + k);
  for (const k of ['Cave', 'Shell', 'L', 'P', 'Sign', 'CornerC']) assert.ok(seen[1].has(k), 'deep labs ' + k);
});

test('every piece the theme places is a mesh in the kit GLB, the kit stays under 2.5 MB', () => {
  const d = fs.readFileSync(path.join(__dirname, '../../assets/fps-kit-arctic.glb'));
  const g = JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
  const meshes = new Set(g.nodes.filter((n) => n.mesh !== undefined).map((n) => n.name));
  for (const n of TH.allPieces()) assert.ok(meshes.has(TH.prefix + n), 'mesh ' + n);
  for (const s of ['_Leaf', '_Leaf_D1', '_Leaf_D2', '_Broken']) assert.ok(meshes.has(TH.prefix + 'VaultDoor' + s), 'vault ' + s);
  assert.ok(d.length <= 2.5 * 1024 * 1024, 'kit GLB ' + d.length);
});
