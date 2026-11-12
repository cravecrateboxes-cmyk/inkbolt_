// Ca' Doranza theme (kit-venetian): level plan and waves (2 zones, elite targets for level 40), the two zones (size,
// gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, the cloister's columns, arches and upper walk,
// the stairs that land on the walk, the balustrades), the wall chooser (house fronts in four colours, the quay over the
// canal, the mansion's fronts, the canal wing, the garden wall, gaps for the portals), and the kit pieces checked on the
// GLB: link pieces along their line of cells, the cloister arch along X, stairs the player and the robots climb, the
// walkable roof terraces, the house fronts' collision on the cell.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/venetian.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.venetian;
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
const plan = IB.LEVEL_PLANS.venetian;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEG';
const DECK = 4.32, TERR = 3.6;

test('venetian theme: kit-venetian, open sky, a level-wide backdrop, two zones of waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-venetian');
  assert.ok(TH.env.sky && TH.env.clouds);
  assert.equal(TH.env.ceiling, null);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(typeof TH.wall.paint, 'function');
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
  // the trail between the zones is the bridge (low balustrades), the exit path the lane
  assert.equal(TH.trail.byTrail[0].wall, 'Bridge_A');
  assert.ok(TH.trail.byTrail[0].height < 1.5 && TH.trail.height > 3);
});

test('elite targets (level 40): each zone holds 65-66.5 soldiers and 41-42.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.venetian;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 65 && s <= 66.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 41 && b <= 42.5, 'zone ' + (i + 1) + ' blade bots ' + b));
  // the counts do not lean on the half-a-wave cap (so they hold at any level number): elites = round(2.5 x written)
  const raw = (zi, k) => RAW[zi].reduce((a, w) => a + w.filter(([t]) => t === k).reduce((b, e) => b + Math.round(e[1] * 2.5), 0), 0);
  assert.deepEqual(sold, [raw(0, 'soldier'), raw(1, 'soldier')]);
  assert.deepEqual(blad, [raw(0, 'blader'), raw(1, 'blader')]);
  p.zones.forEach((z) => z.waves.forEach((w) => {
    const tot = w.reduce((a, e) => a + e[1], 0), el = w.filter(([t]) => /soldier|grenadier|blader/.test(t)).reduce((a, e) => a + e[1], 0);
    assert.ok(el <= tot / 2, 'elites ' + el + ' of ' + tot);
  }));
  assert.ok(!p.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

const SIZES = { venetian_1: [76, 70], venetian_2: [66, 72] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, stairs and decks', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const grids = [g].concat(g.layers);
    grids.forEach((G, li) => G.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '#' || ch === '.' || STAND.includes(ch) || TH.symbols[ch], name + ' grid ' + li + ' ' + ch + ' at ' + c + ',' + r))));
    for (const G of grids) for (const [ch, d] of Object.entries(TH.symbols)) {
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
    const layerAt = (y, ch) => g.layers.filter((L) => Math.abs(L.y - y) < 0.01 && L.rows.some((row) => row.includes(ch)));
    if (name === 'venetian_1') {
      assert.equal(rects(g, 'F').length, 1, 'the Fountain of the Four Winds');
      assert.equal(rects(g, 'K').length, 1, 'Caffe Zanetto');
      assert.equal(rects(g, 'k').length, 1, 'Pasticceria Brolo');
      assert.equal(rects(g, 'L').length, 1, 'the loggia');
      assert.ok(rects(g, 'u').length >= 6 && rects(g, 'M').length >= 2, 'parasol tables, market stalls');
      // the cafes stand against the houses, fronts to the campo
      const K = rects(g, 'K')[0], k2 = rects(g, 'k')[0];
      assert.equal(K.c, 1); assert.equal(k2.c + k2.w, g.w - 1);
      // the roof terraces carry balustrades on the 3.6 layer, the paving lies on a layer at 0
      const top = layerAt(TERR, 'r')[0];
      assert.ok(top, 'terrace balustrades');
      let onK = 0, onL = 0;
      const L = rects(g, 'L')[0];
      top.rows.forEach((row, r) => [...row].forEach((ch, c) => {
        if (ch !== 'r') return;
        if (g.at(c, r) === 'K') onK++; else if (g.at(c, r) === 'L') onL++; else assert.fail('rail off the terraces at ' + c + ',' + r);
      }));
      assert.ok(onK >= 15 && onL >= 28, 'rails ' + onK + ' / ' + onL);
      assert.ok(L.w === 16 && L.h === 6);
      assert.ok(layerAt(0, ',').length === 1, 'cobbles');
    } else {
      assert.equal(rects(g, 'Z').length, 1, 'the grand staircase');
      assert.equal(rects(g, 'Q').length, 1, 'the garden fountain');
      assert.ok(rects(g, 'R').length >= 4, 'parterres');
      // the cloister: columns every 3 m on two rings, an arch between each pair along the line (layer 0)
      let cols = 0; g.rows.forEach((row) => { cols += [...row].filter((ch) => ch === 'O').length; });
      assert.ok(cols >= 70, 'columns ' + cols);
      const arc = g.layers.find((L) => Math.abs(L.y) < 0.01 && L.rows.some((row) => /[AV]/.test(row)));
      assert.ok(arc, 'arch layer');
      rects(arc, 'A').forEach((R) => { assert.equal(R.h, 1); assert.equal(R.w % 2, 0); assert.equal(g.at(R.c - 1, R.r), 'O'); assert.equal(g.at(R.c + R.w, R.r), 'O'); });
      rects(arc, 'V').forEach((R) => { assert.equal(R.w, 1); assert.equal(R.h % 2, 0); assert.equal(g.at(R.c, R.r - 1), 'O'); assert.equal(g.at(R.c, R.r + R.h), 'O'); });
      // the deck covers both column lines; the stairs land on it: Z rises north, i west, j east
      const deck = layerAt(DECK, '=')[0];
      assert.ok(deck, 'deck');
      g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'O') assert.equal(deck.at(c, r), '=', 'column under the deck ' + c + ',' + r); }));
      const Z = rects(g, 'Z')[0], I = rects(g, 'i')[0], J = rects(g, 'j')[0];
      for (let c = Z.c; c < Z.c + Z.w; c++) assert.equal(deck.at(c, Z.r - 1), '=', 'grand stair top');
      for (let r = I.r; r < I.r + I.h; r++) assert.equal(deck.at(I.c - 1, r), '=', 'east stair top');
      for (let r = J.r; r < J.r + J.h; r++) assert.equal(deck.at(J.c + J.w, r), '=', 'west stair top');
      // every deck edge cell has a balustrade except the stair tops
      const rail = g.layers.find((L) => Math.abs(L.y - DECK) < 0.01 && L.rows.some((row) => row.includes('r')));
      let edges = 0, railed = 0;
      for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
        if (deck.at(c, r) !== '=') continue;
        if (![[0, 1], [0, -1], [1, 0], [-1, 0]].some(([dc, dr]) => deck.at(c + dc, r + dr) !== '=')) continue;
        edges++; if (rail.at(c, r) === 'r') railed++;
      }
      assert.ok(railed >= edges - 12 && railed > 200, 'deck edges railed ' + railed + ' of ' + edges);
      assert.ok(g.layers.some((L) => rects(L, 'W').length === 1), 'the roof loggia');
    }
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++; }));
    assert.equal(P.length, 1);
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

test('wall chooser: house fronts, the quay over the canal, the mansion, its canal wing, the garden wall, gaps for the portals; paint', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  maps.forEach(({ name, g }, zi) => {
    let n = 0;
    const seen = new Set();
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const face = r === 0 ? 'S' : r === g.h - 1 ? 'N' : c === 0 ? 'E' : 'W';
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      if (out === null) { assert.ok(r === 0 || r === g.h - 1, 'only gate neighbours are empty'); continue; }
      n++; seen.add(out.replace(/_.*/, ''));
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      const corner = (c === 0 || c === g.w - 1) && (r === 0 || r === g.h - 1);
      if (zi === 0 && r === 0 && !corner) assert.ok(/^Quay_/.test(out), 'the quay ' + out);
      if (zi === 0 && !corner && r > 0) assert.ok(/^H[23]_/.test(out), 'a house front ' + out);
      if (zi === 1 && c === 0 && !corner) assert.ok(/^GW_/.test(out), 'the garden wall ' + out);
      if (zi === 1 && r === g.h - 1 && !corner) assert.ok(/^C_/.test(out), 'the canal wing ' + out);
      if (zi === 1 && (r === 0 || c === g.w - 1) && !corner) assert.ok(/^HP_/.test(out), 'the mansion ' + out);
      const pm = TH.wall.paint(c, r, g, face, out);
      if (pm) pm.forEach(([a, b]) => assert.ok(a >= 8 && a <= 10 && b >= 11 && b <= 19, 'paint ' + a + '->' + b));
      if (zi === 1 && /^(HP|C)_/.test(out)) assert.ok(pm && pm[0][1] === 14, 'the mansion is rose');
    }
    assert.ok(n > 250, name + ' wall modules ' + n);
    if (zi === 0) assert.ok(seen.has('H3') && seen.has('H2') && seen.has('Quay'), 'two house heights and the quay');
  });
});

test('kit pieces on the GLB: links along Z, the cloister arch along X, stairs the robots climb, walkable terraces and walk, collision on the house fronts', () => {
  const G = glb('fps-kit-venetian.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const node = (piece) => { const nd = G.nodes.find((n) => n.name === 'KIT_VENETIAN_' + piece); assert.ok(nd, piece); return nd; };
  const cols = (piece, walk) => (node(piece).children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  // link runs (no turn): the full module runs along glTF Z (Blender Y), the half reaches from the centre toward +Z
  for (const p of ['Bal', 'Hedge']) {
    const [f] = cols(p + 'Full'), [hf] = cols(p + 'Half');
    assert.ok(f.s[2] >= 0.49 && f.s[2] > 1.4 * f.s[0], p + 'Full long axis on Z ' + JSON.stringify(f.s));
    assert.ok(hf.t[2] > 0.2 && hf.t[2] + hf.s[2] <= 0.51, p + 'Half toward +Z ' + JSON.stringify(hf));
  }
  for (const ch of 'rH') assert.ok(!TH.symbols[ch].turn && TH.symbols[ch].links === ch);
  // house fronts: one box over the whole cell, up to the cornice; the garden wall to its coping
  for (const p of ['H3_Win', 'H2_Pier', 'HP_BalM', 'C_Win', 'GW_A']) {
    const [b] = cols(p);
    assert.ok(b && b.s[0] >= 0.49 && b.s[2] >= 0.49 && b.t[1] + b.s[1] >= 3.1, p + ' collision ' + JSON.stringify(b));
  }
  // stairs: every walkable step rises 0.18 m over the one below on a 0.25 m tread (0.36 m a 0.5 m nav cell, under
  // the robots' 0.4 m step) up to the walk / the terrace
  const climb = (piece, top, minSteps) => {
    const st = cols(piece, true).map((b) => ({ x: b.t[0], z: b.t[2], top: b.t[1] + b.s[1], wx: b.s[0] * 2, wz: b.s[2] * 2 }))
      .filter((b) => Math.min(b.wx, b.wz) < 0.26 && b.top < top + 0.01).sort((a, b) => a.top - b.top)
      .filter((b, i, A) => i === 0 || b.top - A[i - 1].top > 0.01);
    assert.ok(st.length >= minSteps, piece + ' steps ' + st.length);
    for (let i = 1; i < st.length; i++) {
      assert.ok(Math.abs(st[i].top - st[i - 1].top - RISE) < 0.005, piece + ' rise ' + i + ' ' + (st[i].top - st[i - 1].top));
    }
    assert.ok(st.every((s) => Math.max(s.wx, s.wz) >= 1.1), piece + ' wide enough for the nav grid');
    const all = cols(piece, true).map((b) => b.t[1] + b.s[1]);
    assert.ok(all.some((t) => Math.abs(t - top) < 0.01), piece + ' reaches ' + top);
  };
  const RISE = 0.18;
  climb('Stair', DECK, 24);
  climb('Landmark_Stair', DECK, 24);
  climb('Cafe_A', TERR, 20);
  climb('Loggia', TERR, 20);
  // the roof terraces are walkable at 3.6 m over a large area
  for (const [p, min] of [['Cafe_A', 50], ['Loggia', 70]]) {
    const area = cols(p, true).filter((b) => Math.abs(b.t[1] + b.s[1] - TERR) < 0.01 && b.s[0] > 0.6 && b.s[2] > 0.6).reduce((a, b) => a + 4 * b.s[0] * b.s[2], 0);
    assert.ok(area > min, p + ' terrace ' + area.toFixed(1));
  }
  // the cloister arch spans 3 m along glTF X (column centre to column centre); the column's top is the arch's spring
  const arch = node('Arch'), col = cols('Column')[0];
  assert.ok(col.t[1] + col.s[1] >= 2.5 && col.t[1] + col.s[1] <= 2.6, 'column top ' + JSON.stringify(col));
  assert.ok(!cols('Arch').length && TH.symbols.A.collide === false && TH.symbols.V.face === Math.PI / 2, 'arches: no collision, V turned');
  assert.ok(arch, 'arch');
  const T = TH.budget;
  assert.ok(T.prop >= 2600 && T.landmark >= 4000);
});
