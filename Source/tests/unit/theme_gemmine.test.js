// Glimmerdeep Colliery theme (kit-gemmine): level plan and waves (two zones, elites, no elites in the first wave), the
// two zones (size, gates, layers and what may stand in them, symbols, prefab tiling and facing, spawns, pickups), the
// wall chooser (coal-mine faces in zone 1, cavern faces and the chasm edge in zone 2, wall codes honoured, every piece
// in the kit), the glow companions and the walkable decks in fps-kit-gemmine.glb.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/gemmine.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.gemmine;
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
function glb(name) {
  const d = fs.readFileSync(path.join(__dirname, '../../assets/' + name));
  return JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
}
const plan = IB.LEVEL_PLANS.gemmine;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEG';
const LAYER0 = '.-p0123456789';

test('gemmine theme: kit-gemmine underground, two zones, hard waves with elites from the second wave', () => {
  assert.equal(TH.family, 'kit-gemmine');
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, 9.0);
  assert.equal(plan.zones.length, 2);
  assert.equal(plan.zones[1].ceiling, false, 'the cavern has its own roof grid');
  const types = new Set();
  plan.zones.forEach((z, zi) => z.waves.forEach((w, wi) => w.forEach(([t, n]) => {
    types.add(t);
    if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave');
    if (zi === 0 && wi === 0) assert.ok(t !== 'soldier' && t !== 'blader', 'the first wave of zone 1 has no elites');
  })));
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
});

for (const [zi, { name, g }] of maps.entries()) {
  test('zone ' + name + ': size, gates, layers, symbols, prefab tiling and facing, spawns, pickups', () => {
    assert.ok(g.w >= 64 && g.w <= 72 && g.h >= 66 && g.h <= 74, name + ' ' + g.w + 'x' + g.h);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.ok('#GE'.includes(g.at(0, r))); assert.ok('#GE'.includes(g.at(g.w - 1, r))); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    assert.deepEqual(g.layers.map((L) => L.y), zi === 0 ? [0, 9] : [0, 18]);
    // layer 0: rails on open floor, decking anywhere but walls, digits (wall codes) only on wall cells
    g.layers[0].rows.forEach((row, r) => [...row].forEach((ch, c) => {
      assert.ok(LAYER0.includes(ch), name + ' @0 ' + ch + ' at ' + c + ',' + r);
      if (ch === '-') assert.ok('.SPahA'.includes(g.at(c, r)), name + ' rail on open floor ' + c + ',' + r);
      if (ch === 'p') assert.ok(!'#GE'.includes(g.at(c, r)), name + ' decking off the walls ' + c + ',' + r);
      if (/\d/.test(ch)) assert.equal(g.at(c, r), '#', name + ' wall code on a wall ' + c + ',' + r);
    }));
    if (zi === 0) {   // roof fittings hang over open cells only
      g.layers[1].rows.forEach((row, r) => [...row].forEach((ch, c) => {
        assert.ok('.v~'.includes(ch), name + ' @9 ' + ch);
        if (ch !== '.') assert.ok(!'#GE'.includes(g.at(c, r)), name + ' roof fitting over a wall ' + c + ',' + r);
      }));
    } else {          // the cavern roof covers everything
      g.layers[1].rows.forEach((row) => assert.equal(row, 'r'.repeat(g.w)));
      assert.equal(rects(g.layers[1], 'r').length, 1);
    }
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '#' || STAND.includes(ch) || TH.symbols[ch], name + ' plan ' + ch + ' at ' + c + ',' + r)));
    for (const G of [g, ...g.layers]) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      rects(G, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
        if (typeof d.face === 'number') {   // a fixed facing turns the model, so the block must match the turned footprint
          const side = Math.abs(Math.sin(d.face)) > 0.5;
          const [sw, sd] = side ? [d.size[1], d.size[0]] : d.size;
          assert.ok(R.w % sw === 0 && R.h % sd === 0, name + ' fixed-facing ' + ch + ' ' + JSON.stringify(R));
        }
      });
    }
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++; }));
    assert.equal(P.length, 1);
    for (const dc of [-2, -1, 1, 2]) assert.ok(STAND.includes(g.at(P[0][0] + dc, P[0][1] - 4)), 'weapon stand cell');
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'S') return;
      S++;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P');
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
  });
}

test('the arch sets span the haulage gallery wall to wall and the tracks run under them', () => {
  const g = maps[0].g;
  const A = rects(g, 'A');
  assert.ok(A.length >= 8);
  A.forEach((R) => {
    assert.ok(R.w === 12 && R.h === 1, JSON.stringify(R));
    for (const c of [29, 36]) assert.equal(g.layers[0].at(c, R.r), '-', 'track under the arch at ' + c + ',' + R.r);
  });
  // carts stand on the tracks (their cells are left out of the rail layer: the cart brings its own track)
  rects(g, 'C').forEach((R) => assert.ok([29, 36].includes(R.c) && R.w === 1 && R.h === 2, JSON.stringify(R)));
});

test('wall chooser: coal-mine faces in zone 1, cavern faces and the chasm edge in zone 2, codes honoured, every piece in the kit', () => {
  const all = new Set(TH.allPieces());
  const hash = (a, b) => { const x = Math.sin(a * 91.7 + b * 17.3) * 1e4; return x - Math.floor(x); };
  for (const [zi, { name, g }] of maps.entries()) {
    const solid = (c, r) => '#GE'.includes(g.at(c, r));
    let chasm = 0, coded = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r);
      const n = oS + oN + oE + oW;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const exposed = n > 0 || [[1, 1], [1, -1], [-1, 1], [-1, -1]].some(([a, b]) => !solid(c + a, r + b));
      if (!exposed) continue;
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      assert.ok(all.has(out), name + ' chooser piece ' + out + ' at ' + c + ',' + r);
      assert.ok(zi === 0 ? !/^(Cave|Chasm)/.test(out) : /^(Cave|Chasm)/.test(out), name + ' ' + out + ' in the wrong zone');
      const code = g.layers[0].at(c, r);
      if (code === '9') { chasm++; assert.ok(/^Chasm|^Cave_Corner/.test(out), name + ' chasm cell ' + c + ',' + r + ' ' + out); }
      if ('1234'.includes(code) && (face === 'S' || face === 'N' || face === 'E' || face === 'W')) {
        coded++;
        const want = { 1: 'Ruby', 2: 'Emer', 3: 'Saph', 4: 'Dia' }[code];
        assert.equal(out, (zi === 0 ? 'Gem_' : 'Cave_') + want, name + ' vein code at ' + c + ',' + r);
      }
    }
    assert.ok(coded >= 10, name + ' vein codes ' + coded);
    if (zi === 1) assert.ok(chasm >= 30, 'chasm edge ' + chasm);
  }
});

test('glow companions: every listed one is in fps-kit-gemmine.glb, every _Glow piece there is listed', () => {
  const nodes = new Set(glb('fps-kit-gemmine.glb').nodes.map((n) => n.name));
  const listed = new Set();
  for (const [k, d] of Object.entries(TH.glow)) {
    assert.ok(nodes.has(TH.prefix + k), 'piece ' + k);
    assert.ok(nodes.has(TH.prefix + d.piece), 'glow ' + d.piece);
    listed.add(TH.prefix + d.piece);
  }
  for (const n of nodes) if (/_Glow$/.test(n) && !/Backdrop/.test(n)) assert.ok(listed.has(n), n + ' not listed in theme.glow');
});

test('run pieces are modelled along local X (the run placer turns X onto the run): rails, conveyors, timbers, duct, lamp strings', () => {
  const G = glb('fps-kit-gemmine.glb');
  const runs = Object.entries(TH.symbols).filter(([, d]) => d.rotate === 'run').flatMap(([, d]) => d.pieces);
  assert.ok(runs.length >= 6, runs.join());
  for (const n of runs) {
    const node = G.nodes.find((x) => x.name === TH.prefix + n && x.mesh !== undefined);
    assert.ok(node, n);
    const acc = G.accessors[G.meshes[node.mesh].primitives[0].attributes.POSITION];
    const ex = acc.max[0] - acc.min[0], ez = acc.max[2] - acc.min[2];
    assert.ok(ex >= 0.98 && ex <= 1.12 && ex > ez + 0.05, n + ' x ' + ex.toFixed(2) + ' z ' + ez.toFixed(2));
  }
});

test('walkable decks: the gallery at 4.8 m, platforms and the heart scaffold at 2.4 m, the catwalk at 3 m, the ledge at 1.4 m; stair rises <= 0.35 m', () => {
  const G = glb('fps-kit-gemmine.glb');
  const byPiece = {};
  G.nodes.forEach((n) => {
    const m = /^KIT_GEMMINE_(.+)_WCOL\d+$/.exec(n.name);
    if (!m) return;
    const t = n.translation || [0, 0, 0], s = n.scale || [1, 1, 1];
    (byPiece[m[1]] = byPiece[m[1]] || []).push(+(t[1] + s[1]).toFixed(3));
  });
  const want = { Landmark_Gallery: 4.8, Platform: 2.4, Landmark_GemHeart: 2.4, Landmark_BeltBridge: 3.0, Ledge: 1.4 };
  for (const [p, top] of Object.entries(want)) {
    const tops = [...new Set(byPiece[p] || [])].sort((a, b) => a - b);
    assert.ok(tops.length > 3, p + ' walkable boxes');
    assert.ok(Math.abs(tops[tops.length - 1] - top) < 0.01, p + ' deck top ' + tops[tops.length - 1]);
    for (let i = 1; i < tops.length; i++) assert.ok(tops[i] - tops[i - 1] <= 0.35 + 1e-3, p + ' rise ' + tops[i - 1] + ' -> ' + tops[i]);
    assert.ok(tops[0] <= 0.35 + 1e-3, p + ' first step ' + tops[0]);
  }
});
