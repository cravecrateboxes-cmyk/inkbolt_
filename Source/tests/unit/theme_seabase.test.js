// Abyssal Station Thalassa theme (kit-seabase): level plan and waves (2 zones, elite targets), the two zones (size,
// gates, layers, codes, symbols, prefab tiling and facing, spawns, pickups, flood water only on floor, one landmark),
// the wall chooser (every piece in the kit, the sea round the observation chambers), runs and spans modelled along
// their line of cells (checked on the GLB's collision boxes), the observation chamber's glass ring, the glow pieces.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/seabase.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.seabase;
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
function glb(file) {
  const d = fs.readFileSync(path.join(__dirname, '../../assets', file));
  return JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
}
const plan = IB.LEVEL_PLANS.seabase;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEGDf';
const ART = 'o0123456789';
const CODES = '~&%' + ART;
const CEIL = '=+-"\'@';
const MARKS = '/!;';

test('seabase theme: kit-seabase, no sky, 7.5 m walls, two zones without the theme ceiling, waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-seabase');
  assert.equal(TH.env.sky, null);
  assert.equal(TH.wall.height, 7.5);
  assert.equal(plan.zones.length, 2);
  plan.zones.forEach((z) => assert.equal(z.ceiling, false));
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader', 'mech', 'hawk', 'grenadier'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
  // the codes layer is read by the theme only: no code is a symbol
  for (const ch of CODES) assert.ok(!TH.symbols[ch], 'code ' + ch + ' is not a symbol');
});

test('elite targets (final level 32): each zone has 56-57.5 soldiers and 32-33.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.seabase;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  p.zones.forEach((z, i) => {
    const s = count(z, (t) => t === 'soldier' || t === 'grenadier'), b = count(z, (t) => t === 'blader');
    assert.ok(s >= 56 && s <= 57.5, 'zone ' + i + ' soldiers ' + s);
    assert.ok(b >= 32 && b <= 33.5, 'zone ' + i + ' bladers ' + b);
    z.waves.forEach((w) => {
      const tot = w.reduce((a, e) => a + e[1], 0), el = w.filter(([t]) => /soldier|grenadier|blader/.test(t)).reduce((a, e) => a + e[1], 0);
      assert.ok(el <= tot / 2, 'elites ' + el + ' of ' + tot);
    });
  });
  assert.ok(!p.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

const SIZES = { seabase_1: [72, 64], seabase_2: [71, 64] };
const LAYERS = { seabase_1: [0.01, 0.22, 3.2, 4.5, 6, 7.5], seabase_2: [0.01, 0.22, 3.2, 4.5, 7] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, codes, symbols, prefab tiling and facing, spawns, pickups, one landmark', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    assert.deepEqual(g.layers.map((L) => L.y), LAYERS[name]);
    const [F, K, Dk, ...C] = g.layers;
    F.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.') return;
      assert.ok(MARKS.includes(ch), name + ' floor mark ' + ch);
      assert.ok(STAND.includes(g.at(c, r)), name + ' mark on floor ' + c + ',' + r);
    }));
    let water = 0;
    K.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.') return;
      assert.ok(CODES.includes(ch), name + ' code ' + ch);
      if (ART.includes(ch) || ch === '%') assert.equal(g.at(c, r), '#', name + ' art code ' + ch + ' off the wall at ' + c + ',' + r);
      else { water++; assert.ok(!'#DGE'.includes(g.at(c, r)), name + ' water on a wall at ' + c + ',' + r); assert.ok(!'ah'.includes(g.at(c, r)), name + ' pickup in the water'); }
    }));
    assert.ok(water > 100, name + ' has flooded floor');
    assert.equal(K.at(0, 0) === '%', name === 'seabase_2', 'research finish code');
    Dk.rows.forEach((row) => [...row].forEach((ch) => assert.ok('.urJ'.includes(ch), name + ' deck ' + ch)));
    C.forEach((L) => L.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.') return;
      assert.ok(CEIL.includes(ch), name + ' ceiling ' + ch);
      if (ch !== '@') assert.ok(!'#DGEAZ'.includes(g.at(c, r)), name + ' ceiling tile over ' + g.at(c, r) + ' at ' + c + ',' + r);
    })));
    // every open cell has exactly one ceiling (or is under the dome, or in an observation chamber)
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      const ch = g.at(c, r); if ('#DGEAZ'.includes(ch)) continue;
      const n = C.filter((L) => L.at(c, r) !== '.').length;
      assert.equal(n, 1, name + ' ceilings over ' + c + ',' + r + ': ' + n);
    }
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '#' || STAND.includes(ch) || TH.symbols[ch], name + ' plan ' + ch + ' at ' + c + ',' + r)));
    for (const G of [g, ...g.layers]) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      rects(G, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
        if (typeof d.face === 'number') {
          const side = Math.abs(Math.sin(d.face)) > 0.5;
          const [sw, sd] = side ? [d.size[1], d.size[0]] : d.size;
          assert.ok(R.w % sw === 0 && R.h % sd === 0, name + ' fixed-facing ' + ch + ' ' + JSON.stringify(R));
        }
      });
    }
    // bulkhead doors sit in 2-cell walls with wall at both ends; glass doors in glass runs
    rects(g, 'D').forEach((R) => {
      const ends = R.w > R.h ? [[R.c - 1, R.r], [R.c + R.w, R.r]] : [[R.c, R.r - 1], [R.c, R.r + R.h]];
      ends.forEach(([c, r]) => assert.equal(g.at(c, r), '#', name + ' door end ' + c + ',' + r));
      assert.equal(Math.min(R.w, R.h), 2, name + ' door depth');
    });
    rects(g, 'f').forEach((R) => {
      const ends = R.w > R.h ? [[R.c - 1, R.r], [R.c + R.w, R.r]] : [[R.c, R.r - 1], [R.c, R.r + R.h]];
      ends.forEach(([c, r]) => assert.ok('q#'.includes(g.at(c, r)), name + ' glass door end ' + c + ',' + r));
    });
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++; }));
    assert.equal(P.length, 1);
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'S') return;
      S++;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P');
      assert.equal(Dk.at(c, r), '.', name + ' spawn under the deck');
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    assert.equal(rects(g, 'M').length + rects(g, 'Y').length, 1, name + ' landmark');
    if (name === 'seabase_2') {   // the observation chambers fill their notches, the hull runs along their flat side
      const A = rects(g, 'A'), Z = rects(g, 'Z');
      assert.deepEqual([A.length, Z.length], [1, 1]);
      assert.equal(A[0].c, 1); assert.equal(Z[0].c + Z[0].w, g.w - 1);
      for (let r = A[0].r; r < A[0].r + A[0].h; r++) { assert.ok('#D'.includes(g.at(A[0].c + A[0].w, r))); assert.ok('#D'.includes(g.at(Z[0].c - 1, r))); }
    }
  });
}

test('wall chooser: every exposed wall cell gets a kit piece; door cells and the sea round the chambers stay empty; finishes per zone', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  for (const { name, g } of maps) {
    const solid = (c, r) => '#GED'.includes(g.at(c, r));
    const style = new Set();
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (!'#D'.includes(g.at(c, r))) continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r);
      const nOpen = oS + oN + oE + oW;
      const exposed = nOpen > 0 || [[1, 1], [1, -1], [-1, 1], [-1, -1]].some(([x, y]) => !solid(c + x, r + y));
      if (!exposed) continue;
      const face = nOpen === 0 ? 'none' : nOpen === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      if (out === null) {
        const outer = c === 0 || r === 0 || c === g.w - 1 || r === g.h - 1;
        const sea = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]].some(([x, y]) => 'AZ'.includes(g.at(c + x, r + y)));
        assert.ok(g.at(c, r) === 'D' || (outer && sea), name + ' empty wall cell ' + c + ',' + r);
        continue;
      }
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      style.add(out.replace(/^Corner/, 'W').slice(0, 2));
      if (/Port$/.test(out)) assert.ok(c === 0 || r === 0 || c === g.w - 1 || r === g.h - 1, name + ' porthole on an inner wall ' + c + ',' + r);
    }
    if (name === 'seabase_1') assert.deepEqual([...style].sort(), ['WS']);
    else assert.deepEqual([...style].sort(), ['WH', 'WR']);
  }
});

const G = glb('fps-kit-seabase.glb');
function boxes(piece) {
  const node = G.nodes.find((n) => n.name === 'KIT_SEABASE_' + piece);
  assert.ok(node, piece);
  return (node.children || []).map((i) => G.nodes[i]).filter((n) => /_W?COL\d+$/.test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale, walk: /_WCOL/.test(n.name) }));
}
function extent(piece) {   // the union of a piece's boxes: [x0, x1, z0, z1] (glTF axes)
  const e = [Infinity, -Infinity, Infinity, -Infinity];
  boxes(piece).forEach(({ t, s }) => { e[0] = Math.min(e[0], t[0] - s[0]); e[1] = Math.max(e[1], t[0] + s[0]); e[2] = Math.min(e[2], t[2] - s[2]); e[3] = Math.max(e[3], t[2] + s[2]); });
  return e;
}

test('runs and spans are modelled along their line of cells (collision boxes in the GLB: long axis on the run)', () => {
  // link runs (no turn): full modules along glTF Z (Blender Y), so a north-south run of cells gets yaw 0
  for (const [p, ch] of [['GlassFull', 'q'], ['RailFull', 'r']]) {
    const [b] = boxes(p);
    assert.ok(b.s[2] > 4 * b.s[0], p + ' long axis on Z ' + JSON.stringify(b.s));
    assert.ok(!TH.symbols[ch].turn, p + ' needs no turn');
    const [h] = boxes(p.replace('Full', 'Half'));   // the half module reaches from the cell centre toward +Z (yaw 0 = south)
    assert.ok(h.t[2] > 0.2 && h.s[2] > 0.2, p + ' half toward +Z ' + JSON.stringify(h));
  }
  // spans (doors in a wall line) and rotate:'run' cells: long axis on X (the placer turns vertical runs a quarter)
  for (const p of ['Bulkhead', 'GlassDoor', 'Barrier_A', 'Barrier_B', 'PipeRun']) {
    const e = extent(p);
    assert.ok(e[1] - e[0] > e[3] - e[2], p + ' long axis on X ' + JSON.stringify(e));
  }
  for (const ch of 'Df') assert.equal(TH.symbols[ch].orient, 'span');
  for (const ch of 'bsi') assert.equal(TH.symbols[ch].rotate, 'run');
  // the bulkhead's coaming is a walkable step a person (0.35) and a robot (0.4) step onto
  const sill = boxes('Bulkhead').filter((b) => b.walk);
  assert.equal(sill.length, 1);
  assert.ok(Math.abs(sill[0].t[1] + sill[0].s[1] - 0.3) < 0.01, 'coaming top');
});

test('observation chamber: the glass ring is a closed half circle on the hull line (local +X), inside the [12, 25] footprint', () => {
  const all = boxes('Landmark_Obs'), b = all.filter((x) => x.s[1] > 1.5 && x.s[0] < 0.2 && x.s[2] < 0.2);   // the glass boxes
  // the seabed outside the glass is solid, and no seabed box reaches into the half circle
  all.filter((x) => x.s[1] > 1.5 && (x.s[0] > 0.3 || x.s[2] > 0.3)).forEach(({ t, s }) => {
    const nx = Math.max(t[0] - s[0], Math.min(6, t[0] + s[0])), nz = Math.max(t[2] - s[2], Math.min(0, t[2] + s[2]));
    assert.ok(Math.hypot(nx - 6, nz) >= 9.5 - 0.01, 'seabed box inside the glass ' + JSON.stringify([t, s]));
  });
  assert.ok(b.length > 100, 'ring boxes ' + b.length);
  b.forEach(({ t }) => {
    const r = Math.hypot(t[0] - 6, t[2]);
    assert.ok(Math.abs(r - 9.5) < 0.05, 'on the circle ' + r);
    assert.ok(t[0] <= 6.0001 && t[0] >= -6 && Math.abs(t[2]) <= 12.5, 'in the footprint ' + t);
  });
  // consecutive boxes overlap: no gap a capsule slips through
  const pts = b.map(({ t }) => Math.atan2(t[2], 6 - t[0])).sort((a, c) => a - c);
  for (let i = 1; i < pts.length; i++) assert.ok((pts[i] - pts[i - 1]) * 9.5 < 0.3, 'ring gap');
  assert.ok(Math.abs(pts[0] + Math.PI / 2) < 0.01 && Math.abs(pts[pts.length - 1] - Math.PI / 2) < 0.01, 'ends on the hull');
});

test('glow companions and every piece the theme places exist in the kit', () => {
  const names = new Set(G.nodes.map((n) => n.name));
  for (const n of TH.allPieces()) assert.ok(names.has('KIT_SEABASE_' + n), 'kit has ' + n);
  Object.values(TH.glow).forEach((g) => [].concat(g).forEach((d) => assert.ok(names.has('KIT_SEABASE_' + d.piece), d.piece)));
});
