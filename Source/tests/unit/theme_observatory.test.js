// Vesper Peak Observatory theme (kit-observatory): level plan and waves (2 zones, elite targets for level 45), the two
// zones (size, gates, edges, symbols on every grid, prefab tiling and facing, spawns, pickups, the landmarks, stairs
// that land on their decks, rails), the wall chooser (a finish face per open side, doorway heads, the glazing, gaps for
// the gates), and the kit pieces checked on the GLB: link pieces along Z, run and [n, 1] pieces along X, stairs the
// robots climb, the walkable roof deck and catwalk ring, collision on the big pieces.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/observatory.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.observatory;
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
const plan = IB.LEVEL_PLANS.observatory;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEG';
const MARK = '`:';
const DATA = [0.02, 0.03, 0.04, 0.05];
const layer = (g, y) => g.layers.find((L) => Math.abs(L.y - y) < 1e-4);

test('observatory theme: kit-observatory, dusk sky, terrain for zone 1 only, a level-wide backdrop, two zones of waves (bombers at most 2, the first wave clean)', () => {
  assert.equal(TH.family, 'kit-observatory');
  assert.ok(TH.env.sky && TH.env.clouds === false && TH.env.far >= 2000);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(typeof TH.terrain.height, 'function');
  assert.equal(plan.zones.length, 2);
  assert.equal(plan.zones[1].terrain, false, 'the dome keeps its painted floor');
  assert.ok(plan.zones[1].floor && plan.zones[1].floor.lines.length === 2);
  assert.equal(TH.terrain.height(10, 10, 1), 0, 'no terrain inside the dome');
  assert.deepEqual(TH.dataLayers, DATA);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 45): each zone holds 70-71.5 soldiers and 46-47.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.observatory;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 70 && s <= 71.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 46 && b <= 47.5, 'zone ' + (i + 1) + ' blade bots ' + b));
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

const SIZES = { observatory_1: [72, 70], observatory_2: [72, 68] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, edges, symbols, prefab tiling and facing, spawns, pickups, landmarks, stairs onto their decks, rails', () => {
    const z1 = name === 'observatory_1';
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.equal(gc, 34); assert.equal(ec, 34);   // both gates on one line: the zones line up edge to edge
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    for (let r = 0; r < g.h; r++) for (const c of [0, g.w - 1]) assert.ok(g.at(c, r) === '#' || (z1 && g.at(c, r) === '{'), 'edge ' + c + ',' + r);
    const grids = [g].concat(g.layers.filter((L) => !DATA.includes(L.y)));
    grids.forEach((G, li) => G.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '#' || STAND.includes(ch) || MARK.includes(ch) || TH.symbols[ch], name + ' grid ' + li + ' ' + ch + ' at ' + c + ',' + r))));
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
    const n = (ch) => g.rows.join('').split(ch).length - 1;
    assert.ok(n('S') >= 10 && n('S') <= 14, 'spawns ' + n('S'));
    assert.ok(n('a') >= 2 && n('h') >= 2, 'pickups');
    if (z1) {
      const T3 = layer(g, 3), P15 = layer(g, 1.5);
      assert.equal(rects(T3, 'O').length, 1, 'the Halden Dome');
      assert.equal(rects(g, 'C').length, 1, 'the ground station');
      assert.ok(rects(g, 'B').length === 1 && rects(g, 'K').length === 1 && rects(P15, 'M').length === 3, 'two dishes, three masts');
      // the stairs land on their decks: the ground station's stair at its south face, the terrace stairs, the pad steps
      const st = rects(g, 'u')[0], gs = rects(g, 'C')[0];
      assert.ok(st.r === gs.r + gs.h && st.c === gs.c, 'stair to the roof deck');
      const T = rects(g, 'T')[0], Y = rects(g, 'Y')[0], J = rects(g, 'J')[0];
      assert.equal(T3.at(T.c, T.r - 1), 'U'); assert.equal(T3.at(T.c + 3, T.r - 1), 'U');
      assert.equal(T3.at(Y.c + Y.w, Y.r), 'U'); assert.equal(T3.at(Y.c + Y.w, Y.r + 3), 'U');
      assert.equal(P15.at(J.c, J.r - 1), 'd'); assert.equal(P15.at(J.c + 2, J.r - 1), 'd');
      // no rail where a stair arrives; the gantry runs from the roof deck to the terrace
      for (let c = T.c; c < T.c + 4; c++) assert.equal(T3.at(c, T.r - 1), 'U', 'open where the stair lands');
      for (let c = gs.c + gs.w; c < 48; c++) assert.ok("m'".includes(T3.at(c, 40)) && "m'".includes(T3.at(c, 41)), 'gantry at ' + c);
      // rails only on deck edges (never round a prop on the deck)
      for (const L of [T3, P15]) L.rows.forEach((row, r) => [...row].forEach((ch, c) => {
        if (!"r'".includes(ch)) return;
        const out = [[0, 1], [0, -1], [1, 0], [-1, 0]].some(([dc, dr]) => L.at(c + dc, r + dr) === '.' && !'#{'.includes(g.at(c + dc, r + dr)));
        assert.ok(out || (c === 48 && (r === 39 || r === 42)), 'rail inland at ' + c + ',' + r);
      }));
    } else {
      const DK = layer(g, 4.8);
      assert.equal(rects(g, '$').length, 1, 'the telescope');
      assert.equal(rects(DK, '@').length, 1, 'the catwalk ring');
      assert.equal(rects(layer(g, 10), '*').length, 1, 'the dome');
      const ring = rects(DK, '@')[0], tel = rects(g, '$')[0];
      assert.deepEqual([ring.c + ring.w / 2, ring.r + ring.h / 2], [tel.c + tel.w / 2, tel.r + tel.h / 2], 'ring round the telescope');
      // the stairs reach the ring's edge on its axis, the bridge its east point, the gallery stair the gallery
      const N = rects(g, 'N').find((R) => R.r > ring.r), s2 = rects(g, 'n')[0];
      assert.ok(N && N.r === ring.r + ring.h && N.c === 35, 'south stair');
      assert.ok(s2.r + s2.h === ring.r && s2.c === 35, 'north stair');
      for (let r = 32; r < 36; r++) assert.ok("m'".includes(DK.at(ring.c + ring.w, r)), 'bridge');
      const e = rects(g, 'e')[0];
      assert.ok(DK.at(e.c + e.w, e.r) === 'm' && DK.at(e.c + e.w, e.r + 1) === 'm', 'gallery stair lands on the deck');
      // ceilings over every room but the hall; the glazing along both viewing rooms
      for (const y of [4.2, 5, 8, 9]) assert.ok(layer(g, y).rows.join('').includes('-'), 'ceiling ' + y);
      assert.ok(layer(g, 0.03).rows.filter((row) => row[71] === 'g').length >= 50, 'glazing');
      // ring columns keep their cells
      assert.ok(g.rows.join('').split(':').length - 1 >= 16, 'ring column cells');
    }
  });
}

test('wall chooser: a finish face per open side in the scheme it looks onto, doorway heads, the glazing, nothing on gates', () => {
  const C = TH.wall.choose;
  maps.forEach(({ name, g }) => {
    let faces = 0, heads = 0, glass = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      const ch = g.at(c, r);
      if (!'#DW'.includes(ch)) continue;
      const out = C(c, r, false, false, () => 0.3, g, null);
      if (!out) continue;
      const list = [].concat(out).map((p) => (typeof p === 'object' ? p.piece : p));
      for (const p of list) assert.ok(TH.allPieces().includes(p), name + ' piece ' + p);
      if (list.some((p) => /^TG/.test(p))) { assert.equal(list.length, 1); glass++; continue; }
      if ('DW'.includes(ch)) { assert.ok(list.every((p) => /_U$/.test(p)), 'doorway head ' + list); heads++; }
      faces += list.filter((p) => /^F[A-Z]/.test(p)).length;
    }
    assert.ok(faces > (name === 'observatory_1' ? 120 : 300), name + ' faces ' + faces);
    if (name === 'observatory_2') { assert.ok(heads >= 30, 'doorway heads ' + heads); assert.ok(glass >= 50, 'glazing ' + glass); }
    // the gate frame covers the gate and one cell either side
    for (const r of [0, g.h - 1]) for (let c = 33; c <= 37; c++) assert.equal(C(c, r, true, false, () => 0.3, g, r ? 'N' : 'S'), null);
  });
});

test('kit pieces on the GLB: links along Z, runs and [n, 1] prefabs along X, stairs the robots climb, the roof deck and the ring walkable, collision on the big pieces', () => {
  const G = glb('fps-kit-observatory.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const node = (piece) => { const nd = G.nodes.find((n) => n.name === 'KIT_OBSERVATORY_' + piece); assert.ok(nd, piece); return nd; };
  const cols = (piece, walk) => (node(piece).children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  const bbox = (piece) => {   // the mesh's POSITION bounds (glTF: x, y up, z = Blender -y)
    const m = G.meshes[node(piece).mesh], a = G.accessors[m.primitives[0].attributes.POSITION];
    return { min: a.min, max: a.max };
  };
  // link runs (no turn): the full module runs along glTF Z (Blender Y), the half reaches from the centre toward +Z
  for (const p of ['Fence', 'Rail']) {
    const [f] = cols(p + 'Full'), [hf] = cols(p + 'Half');
    assert.ok(f.s[2] >= 0.49 && f.s[2] > 4 * f.s[0], p + 'Full long axis on Z ' + JSON.stringify(f.s));
    assert.ok(hf.t[2] > 0.2 && hf.t[2] + hf.s[2] <= 0.51, p + 'Half toward +Z ' + JSON.stringify(hf));
    const b = bbox(p + 'Full');
    assert.ok(b.max[2] - b.min[2] > 0.95 && b.max[0] - b.min[0] < 0.2, p + 'Full drawn along Z');
  }
  for (const ch of "fr'") assert.ok(!TH.symbols[ch].turn && TH.symbols[ch].links.includes(ch));
  // rotate 'run' pieces (parapets, cable bridges) and [n, 1] prefabs lie along glTF X
  for (const p of ['Par_A', 'Par_B', 'Cable_A', 'Cable_B', 'Bench', 'Panorama', 'LabBench', 'PlateCab', 'Rack', 'Console', 'OpsDesk', 'VideoWall',
    'Lockers', 'BenchIn', 'Sofa', 'LowTable', 'CafeBar', 'Sign_Station', 'Sign_Annex', 'Door2', 'Door4']) {
    const b = bbox(p);
    assert.ok(b.max[0] - b.min[0] > b.max[2] - b.min[2], p + ' long along X ' + JSON.stringify(b));
  }
  for (const ch of '{x') assert.equal(TH.symbols[ch].rotate, 'run');
  // stairs: walkable treads at most 0.16 m apart on 0.25 m treads (0.32 m a 0.5 m nav cell, under the robots' 0.4 m
  // step), up to their landing; they rise toward glTF -Z (north) at no turn
  const climb = (piece, top) => {
    const st = cols(piece, true).map((b) => ({ z: b.t[2], top: b.t[1] + b.s[1], wx: b.s[0] * 2, wz: b.s[2] * 2 })).sort((a, b) => a.top - b.top);
    for (let i = 1; i < st.length; i++) assert.ok(st[i].top - st[i - 1].top <= 0.161, piece + ' rise ' + (st[i].top - st[i - 1].top));
    assert.ok(Math.abs(st[st.length - 1].top - top) < 0.01, piece + ' reaches ' + top);
    assert.ok(st[st.length - 1].z < st[0].z, piece + ' rises north');
    assert.ok(st.every((s) => s.wx >= 1.6), piece + ' wide enough');
  };
  climb('Stair30', 3.0); climb('Stair48', 4.8); climb('StairC', 3.0); climb('Steps15', 1.5);
  // the ground station's roof is a deck at 3 m over the whole building; the ring's deck is walkable all round
  const gs = cols('GroundStation', true);
  assert.ok(gs.some((b) => Math.abs(b.t[1] + b.s[1] - 3.0) < 0.01 && b.s[0] >= 4.9 && b.s[2] >= 2.9), 'roof deck');
  const ring = cols('Landmark_Ring', true), area = ring.reduce((a, b) => a + 4 * b.s[0] * b.s[2], 0);
  assert.ok(ring.every((b) => Math.abs(b.t[1] + b.s[1]) < 0.01) && area > 130 && area < 180, 'ring deck ' + area.toFixed(1));
  // the telescope and the Halden Dome stand solid; the dome, the floor rings and the signs have none
  assert.ok(cols('Landmark_Telescope').length >= 20 && cols('Landmark_OldDome').length >= 20);
  for (const ch of '*(12') assert.equal(TH.symbols[ch].collide, false);
  assert.ok(TH.budget.prop >= 2500 && TH.budget.landmark >= 6000);
});
