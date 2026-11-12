// Pelagic Airbase theme (kit-pelagic): level plan and waves (2 zones, elite targets for level 38), the two zones
// (size, gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, the decks and their stairs and rails),
// the wall chooser (railings on the deck edges, fences, the barricade over the runway, the operations block front),
// and the kit pieces checked on the GLB: run and link pieces along their line of cells, stairs that the player and
// the robots climb, the walkable galleries, the wall modules' collision on their inside face.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/pelagic.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.pelagic;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function grid(rows, w, out) {
  const padded = rows.map((r) => r.slice(0, w).padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? out : padded[r][c] };
}
function parse(text) {
  const base = [], layers = []; let cur = base, ly = null;
  for (const l of text.replace(/\r/g, '').split('\n')) {
    const m = /^@layer\s+(-?[\d.]+)/.exec(l);
    if (m) { cur = []; ly = { y: parseFloat(m[1]), rows: cur }; layers.push(ly); } else if (l.length) cur.push(l);
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
const plan = IB.LEVEL_PLANS.pelagic;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEGwx~';

test('pelagic theme: kit-pelagic, open sky over the sea, two zones of waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-pelagic');
  assert.ok(TH.env.sky && TH.env.clouds && TH.env.far >= 900);
  assert.equal(TH.env.ceiling, null);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 38): each zone holds 63-64.5 soldiers and 39-40.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.pelagic;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 63 && s <= 64.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 39 && b <= 40.5, 'zone ' + (i + 1) + ' blade bots ' + b));
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

const SIZES = { pelagic_1: [78, 76], pelagic_2: [64, 76] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, decks', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    for (let r = 0; r < g.h; r++) { assert.ok('#GE'.includes(g.at(0, r))); assert.equal(g.at(g.w - 1, r), '#'); }
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
    // stairs end at a deck edge: the cell beyond each stair's top is a deck cell of the matching layer
    const deckAt = (y, c, r) => g.layers.some((L) => Math.abs(L.y - y) < 0.01 && '=m'.includes(L.at(c, r)));
    for (const G of grids) {
      rects(G, 'u').forEach((R) => assert.ok(deckAt(2.4, R.c, R.r - 1) && deckAt(2.4, R.c + 1, R.r - 1), 'u stair top on the dock deck'));
      rects(G, 'U').forEach((R) => assert.ok(deckAt(2.4, R.c - 1, R.r) && deckAt(2.4, R.c - 1, R.r + 1), 'U stair top on the dock deck'));
      rects(G, 'i').forEach((R) => assert.ok(deckAt(3.0, R.c, R.r - 1) && deckAt(3.0, R.c + 1, R.r - 1), 'i stair top on the mezzanine'));
    }
    // every deck edge cell has a rail on its layer except the stair tops and the sides against a hangar wall
    g.layers.forEach((L) => {
      const deck = L.rows.some((row) => /[=m]/.test(row));
      if (!deck) return;
      const up = g.layers.filter((U) => Math.abs(U.y - L.y) < 0.01 && U !== L);
      const rail = (c, r) => up.some((U) => U.at(c, r) === 'r');
      let edges = 0, railed = 0;
      for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
        const ch = L.at(c, r); if (!'=m'.includes(ch)) continue;
        // a side against a hangar wall (the neighbour lies outside the hangar block holding the cell) needs no rail
        const hang = (cc, rr) => 'AB'.includes(g.at(cc, rr)) ? g.at(cc, rr) : null;
        const open = [[0, 1], [0, -1], [1, 0], [-1, 0]].some(([dc, dr]) => L.at(c + dc, r + dr) !== ch && !(hang(c, r) && hang(c + dc, r + dr) !== hang(c, r)));
        if (!open) continue;
        edges++; if (rail(c, r)) railed++;
      }
      assert.ok(railed >= edges - 4 && railed > 10, name + ' deck ' + L.y + ' railed ' + railed + ' of ' + edges);
    });
    if (name === 'pelagic_1') {
      assert.equal(rects(g, 'I').length, 1, 'the island');
      assert.equal(rects(g, 'L').length, 1, 'the light aircraft');
      // the spawn is beside the light aircraft
      const P = g.rows.findIndex((row) => row.includes('P')), pc = g.rows[P].indexOf('P'), L = rects(g, 'L')[0];
      assert.ok(Math.abs(pc - (L.c + L.w)) <= 4 && P >= L.r && P <= L.r + L.h + 1, 'spawn by the plane');
      assert.equal(g.layers.filter((L2) => rects(L2, 'Y').length === 1).length, 1, 'the helicopter on the dock');
      assert.ok(rects(g, 'D').length >= 2 && rects(g, 'w').length >= 4, 'blast deflectors, arresting wires');
      rects(g, 'w').forEach((R) => assert.equal(R.h, 1, 'wires run across the runway'));
    } else {
      assert.equal(rects(g, 'A').length, 1); assert.equal(rects(g, 'B').length, 1);
      assert.equal(rects(g, 'W').length, 1, 'the second tower');
      assert.equal(rects(g, 'C').length, 2, 'two cargo lifts');
      assert.ok(g.layers.some((L) => rects(L, 'M').length === 2), 'a fighter in each hangar');
      assert.ok(rects(g, 'V').length === 3 && g.rows.join('').split('~').length > 20, 'fuel tanks and the fuel line');
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

test('wall chooser: railings on the deck edges, fences and the runway barricade, the operations block front, gaps for the gate frames', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  maps.forEach(({ name, g }, zi) => {
    let n = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const out = TH.wall.choose(c, r, false, false, hash, g, 'S');
      if (out === null) { assert.ok(r === 0 || r === g.h - 1, 'only gate neighbours are empty'); continue; }
      n++;
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      if ((c === 0 || c === g.w - 1) && r > 0 && r < g.h - 1) assert.ok(zi === 1 && c === g.w - 1 ? /^Fence_/.test(out) : /^Edge_/.test(out), name + ' side ' + c + ',' + r + ' ' + out);
      if (zi === 0 && r === 0 && c >= 52 && c < g.w - 1) assert.ok(/^Barricade_/.test(out), 'barricade over the runway');
      if (zi === 0 && r === g.h - 1 && c > 0 && c < 52) assert.ok(/^Ops_/.test(out), 'operations block front');
    }
    assert.ok(n > 250, name + ' wall modules ' + n);
  });
});

test('kit pieces on the GLB: links along Z, runs along X, stairs the robots climb, walkable galleries, wall collision on the inside face', () => {
  const G = glb('fps-kit-pelagic.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const node = (piece) => { const nd = G.nodes.find((n) => n.name === 'KIT_PELAGIC_' + piece); assert.ok(nd, piece); return nd; };
  const cols = (piece, walk) => (node(piece).children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  // link runs (no turn): the full module runs along glTF Z (Blender Y), the half reaches from the centre toward +Z
  for (const p of ['Rail', 'Pipe', 'Bund']) {
    const [f] = cols(p + 'Full'), [hf] = cols(p + 'Half');
    assert.ok(f.s[2] >= 0.49 && f.s[2] > 1.9 * f.s[0], p + 'Full long axis on Z ' + JSON.stringify(f.s));
    assert.ok(hf.t[2] > 0.2 && hf.t[2] + hf.s[2] <= 0.51, p + 'Half toward +Z ' + JSON.stringify(hf));
  }
  for (const ch of 'r~-') assert.ok(!TH.symbols[ch].turn && TH.symbols[ch].links === ch);
  // runs placed with rotate 'run' are modelled along X: the arresting wire's cable spans the cell along X
  assert.equal(TH.symbols.w.rotate, 'run');
  // wall modules: the blast fence's and the barricade's collision lie on the inside face (Blender -Y = glTF +Z)
  for (const p of ['Fence_A', 'Fence_B', 'Barricade_Net']) {
    const [b] = cols(p);
    assert.ok(b.s[0] >= 0.49 && b.s[2] <= 0.11 && b.t[2] > 0.25 && b.t[2] < 0.5, p + ' collision along X on the inside face ' + JSON.stringify(b));
  }
  // stairs: every walkable step rises 0.2 m over the one below on a 0.5 m tread (robots climb 0.4 m per 0.5 m nav
  // cell), up to the deck / gallery height
  const climb = (piece, top) => {
    const st = cols(piece, true).map((b) => ({ x: b.t[0], z: b.t[2], top: b.t[1] + b.s[1], wx: b.s[0] * 2, wz: b.s[2] * 2 }))
      .filter((b) => Math.min(b.wx, b.wz) < 0.51 && b.top < top + 0.01).sort((a, b) => a.top - b.top)
      .filter((b, i, A) => i === 0 || b.top - A[i - 1].top > 0.01);   // a landing at the top is not another step
    assert.ok(st.length >= 12, piece + ' steps ' + st.length);
    for (let i = 1; i < st.length; i++) {
      assert.ok(Math.abs(st[i].top - st[i - 1].top - 0.2) < 0.005, piece + ' rise ' + i);
      assert.ok(Math.abs(Math.hypot(st[i].x - st[i - 1].x, st[i].z - st[i - 1].z) - 0.5) < 0.01, piece + ' tread ' + i);
    }
    assert.ok(Math.abs(st[st.length - 1].top - top) < 0.01, piece + ' reaches ' + top);
    assert.ok(st.every((s) => Math.max(s.wx, s.wz) >= 1.6), piece + ' wide enough for the nav grid');
  };
  climb('Stair24', 2.4);
  climb('Stair30', 3.0);
  climb('Landmark_Island', 3.6);
  climb('Landmark_Tower2', 3.6);
  // the galleries are walkable at 3.6 m over a large area
  for (const p of ['Landmark_Island', 'Landmark_Tower2']) {
    const area = cols(p, true).filter((b) => Math.abs(b.t[1] + b.s[1] - 3.6) < 0.01 && b.s[0] > 0.6).reduce((a, b) => a + 4 * b.s[0] * b.s[2], 0);
    assert.ok(area > 50, p + ' gallery ' + area.toFixed(1));
  }
  // budgets
  const T = TH.budget;
  assert.ok(T.prop >= 2400 && T.landmark >= 4000);
});
