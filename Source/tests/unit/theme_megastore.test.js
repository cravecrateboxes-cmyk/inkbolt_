// BULKBARN Warehouse Club theme (kit-megastore): level plan and waves (2 zones, elite targets), the two zones (size,
// gates, layers, symbols, prefab tiling and facing, spawns, pickups), the wall chooser (every piece in the kit, dock
// bays), runs modelled along their line of cells (glass, partitions, rails, racks: checked on the GLB's collision
// boxes), the goods paint jobs, and the kit-parking pieces the theme borrows.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/megastore.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.megastore;
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
const plan = IB.LEVEL_PLANS.megastore;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEGDJ';
const ART = 'de<f>{()89][?`_,*';

test('megastore theme: kit-megastore with kit-parking, indoor 10 m roof, two zones of waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-megastore');
  assert.deepEqual(TH.families, ['kit-parking']);
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, 10);
  assert.equal(TH.wall.height, 10);
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader', 'mech', 'hawk', 'grenadier'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 27): each zone averages 50-53 soldiers and 26-29 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.megastore;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  const avgS = (sold[0] + sold[1]) / 2, avgB = (blad[0] + blad[1]) / 2;
  assert.ok(avgS >= 50 && avgS <= 53, 'soldiers ' + avgS);
  assert.ok(avgB >= 26 && avgB <= 29, 'bladers ' + avgB);
  p.zones.forEach((z) => z.waves.forEach((w) => {
    const tot = w.reduce((a, e) => a + e[1], 0), el = w.filter(([t]) => /soldier|grenadier|blader/.test(t)).reduce((a, e) => a + e[1], 0);
    assert.ok(el <= tot / 2, 'elites ' + el + ' of ' + tot);
  }));
  assert.ok(!p.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

const SIZES = { megastore_1: [80, 66], megastore_2: [72, 60] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, symbols, prefab tiling and facing, spawns, pickups', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    assert.deepEqual(g.layers.map((L) => L.y), [0.01, 3.5, 10, 10]);
    const [F, Dk, Rf, Sg] = g.layers;
    // floor layer: marks on open floor, art codes only on wall cells
    F.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.') return;
      if (ART.includes(ch)) assert.equal(g.at(c, r), '#', name + ' art code ' + ch + ' off the wall at ' + c + ',' + r);
      else { assert.ok('-z/+'.includes(ch), name + ' floor mark ' + ch); assert.ok(STAND.includes(g.at(c, r)) || 'cpl'.includes(g.at(c, r)), name + ' mark on floor ' + c + ',' + r); }
      if (ART.includes(ch)) assert.ok(!TH.symbols[ch], 'art code ' + ch + ' is not a symbol');
    }));
    // roof layer: whole [4, 4] bays; sign layer: signs only
    Rf.rows.forEach((row) => [...row].forEach((ch) => assert.ok('.=~:;|'.includes(ch), name + ' roof ' + ch)));
    Sg.rows.forEach((row) => [...row].forEach((ch) => assert.ok('.1234567!@$%^&'.includes(ch), name + ' sign ' + ch)));
    // deck layer: deck, rails and the office only
    Dk.rows.forEach((row) => [...row].forEach((ch) => assert.ok('.uro'.includes(ch), name + ' deck ' + ch)));
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
    // racks run north-south (2 cells wide, whole bays)
    for (const ch of 'RT') rects(g, ch).forEach((R) => assert.ok(R.w === 2 && R.h % 3 === 0 && R.h >= 6, name + ' rack ' + JSON.stringify(R)));
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
    // one landmark per zone
    assert.equal(rects(g, 'Z').length + rects(Dk, 'o').length, 1, name + ' landmark');
  });
}

test('wall chooser: every exposed wall cell gets a kit piece (dock bays: the centre module, empty side cells), styles per zone', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  for (const { name, g } of maps) {
    const solid = (c, r) => '#GE'.includes(g.at(c, r));
    const style = new Set();
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r);
      const nOpen = oS + oN + oE + oW;
      const exposed = nOpen > 0 || [[1, 1], [1, -1], [-1, 1], [-1, -1]].some(([x, y]) => !solid(c + x, r + y));
      if (!exposed) continue;
      const face = nOpen === 0 ? 'none' : nOpen === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      const code = g.layers[0].at(c, r);
      if (out === null) { assert.equal(code, '_', name + ' empty wall cell ' + c + ',' + r); continue; }
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      style.add(out.replace(/^(Corner)?/, '').charAt(1));
      if (code === ']' || code === '[') assert.deepEqual([g.layers[0].at(c, r - 1), g.layers[0].at(c, r + 1)], ['_', '_'], name + ' dock bay ' + r);
    }
    assert.ok(style.has(name === 'megastore_1' ? 'S' : 'K'), name + ' finish');
  }
});

test('runs and spans are modelled along their line of cells (collision boxes in the GLB: long axis on the run)', () => {
  const G = glb('fps-kit-megastore.glb');
  const box = (piece) => {
    const node = G.nodes.find((n) => n.name === 'KIT_MEGASTORE_' + piece);
    assert.ok(node, piece);
    return (node.children || []).map((i) => G.nodes[i]).filter((n) => /_W?COL\d+$/.test(n.name)).map((n) => n.scale);
  };
  const extent = (piece) => {   // the union of a piece's boxes: [x0, x1, z0, z1] (glTF axes)
    const node = G.nodes.find((n) => n.name === 'KIT_MEGASTORE_' + piece);
    const e = [Infinity, -Infinity, Infinity, -Infinity];
    (node.children || []).map((i) => G.nodes[i]).filter((n) => /_W?COL\d+$/.test(n.name)).forEach((n) => {
      const t = n.translation || [0, 0, 0], sc = n.scale;
      e[0] = Math.min(e[0], t[0] - sc[0]); e[1] = Math.max(e[1], t[0] + sc[0]); e[2] = Math.min(e[2], t[2] - sc[2]); e[3] = Math.max(e[3], t[2] + sc[2]);
    });
    return e;
  };
  // link runs (no turn): full modules along glTF Z (Blender Y), so a north-south run of cells gets yaw 0
  for (const p of ['VGlassFull', 'PartFull', 'RailFull']) {
    const [s] = box(p);
    assert.ok(s[2] > 4 * s[0], p + ' long axis on Z ' + JSON.stringify(s));
    assert.ok(!TH.symbols[{ VGlassFull: 'q', PartFull: 'i', RailFull: 'r' }[p]].turn, p + ' needs no turn');
  }
  // spans (doors in a wall line) and rack runs: long axis on X
  for (const p of ['VDoor', 'BreakDoor', 'Rack_A', 'Rack_EndL', 'Tall_A', 'Tall_EndR']) {
    const e = extent(p);
    assert.ok(e[1] - e[0] > e[3] - e[2], p + ' long axis on X ' + JSON.stringify(e));
  }
  assert.equal(TH.symbols.D.orient, 'span');
  assert.equal(TH.symbols.J.orient, 'span');
  assert.equal(TH.symbols.R.sequence, 'run');
});

test('goods paint jobs and glow companions: cells match the palette, every glow piece is in the kit', () => {
  const src = fs.readFileSync(path.join(__dirname, '../../blender/ms_base.py'), 'utf8');
  const pal = [...src.slice(src.indexOf('PALETTES[FAM]')).matchAll(/\('(\w+)', '#[0-9A-Fa-f]{6}'\)/g)].map((m) => m[1]);
  const base = 8;
  assert.deepEqual(TH.symbols.R.paint.from, ['gA', 'gB', 'gC', 'gD'].map((n) => pal.indexOf(n) + base));
  const prod = ['gA', 'gB', 'gC', 'gD', 'pOrange', 'pPurple', 'pWhite', 'pBlack', 'pPink', 'pTeal', 'pBrown', 'pLime', 'pSky'].map((n) => pal.indexOf(n) + base);
  TH.symbols.R.paint.to.forEach((job) => job.forEach((cell) => assert.ok(prod.includes(cell), 'product colour ' + cell)));
  const all = new Set(TH.allPieces());
  Object.values(TH.glow).forEach((g) => [].concat(g).forEach((d) => assert.ok(all.has(d.piece), d.piece)));
});

test('kit-parking pieces the theme borrows exist in fps-kit-parking.glb', () => {
  const names = new Set(glb('fps-kit-parking.glb').nodes.map((n) => n.name));
  const list = TH.borrowed();
  assert.deepEqual(list.sort(), ['KIT_PARKING_Bins', 'KIT_PARKING_Drums', 'KIT_PARKING_Forklift', 'KIT_PARKING_Pallets']);
  for (const n of list) assert.ok(names.has(n), 'kit-parking missing ' + n);
});
