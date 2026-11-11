// Palmyra Cove Resort theme (kit-resort): level plan and waves (2 zones, elite targets for level 30), the two zones
// (size, gates, layers, symbols, prefab tiling and facing, spawns, pickups, landmarks), the tree platforms (every
// ramp's top end and every bridge end lands on a platform edge left open in the rails, rails everywhere else on the
// edge), the wall chooser, and the kit pieces checked on the GLB: run pieces along their line of cells, ramp steps
// rising toward the piece's north end in steps robots and the player can climb.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/resort.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.resort;
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
const plan = IB.LEVEL_PLANS.resort;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.,;~SahPEGge';
const PAINT = '.,;~';

test('resort theme: kit-resort, open sky, terrain paint, two zones of waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-resort');
  assert.ok(TH.env.sky && TH.env.clouds);
  assert.equal(TH.env.ceiling, null);
  assert.equal(typeof TH.terrain.paint, 'function');
  assert.equal(TH.terrain.height(10, 10, 0), 0);
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader', 'mech', 'hawk', 'grenadier'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 30): each zone averages 54-55.5 soldiers and 30-31.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.resort;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  const avgS = (sold[0] + sold[1]) / 2, avgB = (blad[0] + blad[1]) / 2;
  assert.ok(avgS >= 54 && avgS <= 55.5, 'soldiers ' + avgS);
  assert.ok(avgB >= 30 && avgB <= 31.5, 'bladers ' + avgB);
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

const SIZES = { resort_1: [72, 64], resort_2: [76, 68] };
const RAMPS = { '^': [0, -1], 'v': [0, 1], '>': [1, 0], '<': [-1, 0] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, symbols, prefab tiling and facing, platforms, ramps, bridges, rails, spawns, pickups', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 1; r < g.h - 1; r++) { assert.equal(g.at(0, r), '{', 'shore on the west edge'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    assert.deepEqual(g.layers.map((L) => L.y), [0.2, 0.2, 7.5, 7.5, 7.5]);
    const [BW, BD, DK, DJ, UP] = g.layers;
    const only = (L, set, what) => L.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(set.includes(ch), name + ' ' + what + ' ' + ch + ' at ' + c + ',' + r)));
    only(BW, '.w', 'boardwalk'); only(BD, '.db', 'boardwalk decal'); only(DK, '.D=', 'platform'); only(DJ, '.J', 'platform decal');
    only(UP, '.rVW[]MHotckq', 'on the platforms');
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
          // the engine tiles a block with the unturned footprint when that fits: a quarter-turned piece's block must not
          if (side && d.size[0] !== d.size[1]) assert.ok(!(R.w % d.size[0] === 0 && R.h % d.size[1] === 0), name + ' merged block of ' + ch + ' ' + JSON.stringify(R));
        }
      });
    }
    // decals cover their slabs exactly; things on the platforms stand on a slab; boardwalks lie on open ground
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      assert.equal(BW.at(c, r) === 'w', BD.at(c, r) !== '.', name + ' boardwalk decal ' + c + ',' + r);
      assert.equal(DK.at(c, r) === 'D', DJ.at(c, r) !== '.', name + ' platform decal ' + c + ',' + r);
      if (UP.at(c, r) !== '.') assert.equal(DK.at(c, r), 'D', name + ' prop off the platform ' + c + ',' + r);
      if (BW.at(c, r) === 'w') assert.ok(PAINT.includes(g.at(c, r)), name + ' boardwalk over ' + g.at(c, r));
      if (g.at(c, r) === 'Z') { assert.equal(DK.at(c, r), 'D', name + ' giant palm under a platform'); assert.equal(UP.at(c, r), '.', name + ' trunk cell ' + c + ',' + r); }
      if (DK.at(c, r) === 'D') assert.ok(!'pYq'.includes(g.at(c, r)), name + ' palm under a platform ' + c + ',' + r);
    }
    // openings in the platform edge: the cells a ramp top or a bridge end lands on; rails on every other edge cell
    const open = new Set();
    for (const [ch, [dx, dz]] of Object.entries(RAMPS)) rects(g, ch).forEach((R) => {
      const cells = dx === 0 ? [...Array(R.w)].map((_, i) => [R.c + i, dz < 0 ? R.r - 1 : R.r + R.h]) : [...Array(R.h)].map((_, i) => [dx > 0 ? R.c + R.w : R.c - 1, R.r + i]);
      assert.equal(R.w * R.h, 26, name + ' one ramp per block ' + JSON.stringify(R));
      cells.forEach(([c, r]) => { assert.equal(DK.at(c, r), 'D', name + ' ramp ' + ch + ' top lands on a platform ' + c + ',' + r); open.add(c + ',' + r); });
    });
    rects(DK, '=').forEach((R) => {
      const horiz = R.h === 2, ends = horiz ? [[R.c - 1, R.r], [R.c - 1, R.r + 1], [R.c + R.w, R.r], [R.c + R.w, R.r + 1]] : [[R.c, R.r - 1], [R.c + 1, R.r - 1], [R.c, R.r + R.h], [R.c + 1, R.r + R.h]];
      ends.forEach(([c, r]) => { assert.equal(DK.at(c, r), 'D', name + ' bridge end on a platform ' + c + ',' + r); open.add(c + ',' + r); });
    });
    rects(DK, 'D').forEach((R) => {
      for (let r = R.r; r < R.r + R.h; r++) for (let c = R.c; c < R.c + R.w; c++) {
        const edge = c === R.c || c === R.c + R.w - 1 || r === R.r || r === R.r + R.h - 1;
        if (!edge) continue;
        assert.equal(UP.at(c, r), open.has(c + ',' + r) ? '.' : 'r', name + ' platform edge ' + c + ',' + r);
      }
    });
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
    // landmarks: the lobby pavilion (zone 1), the CANOPY SUITE (zone 2); giant palms carry platforms in both
    if (name === 'resort_1') assert.equal(rects(g, 'L').length, 1); else assert.equal(rects(UP, 'M').length, 1);
    assert.ok(rects(g, 'Z').length >= 2 && rects(DK, 'D').length >= 1, name + ' treehouse platforms');
  });
}

test('wall chooser: every exposed wall cell gets a kit piece or is left to the gate frame / a neighbour module', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  for (const { name, g } of maps) {
    let n = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const out = TH.wall.choose(c, r, false, false, hash, g, 'S');
      if (out === null) continue;
      n++;
      assert.ok(all.has(out), name + ' chooser piece ' + out);
    }
    assert.ok(n > 60, name + ' wall modules ' + n);
  }
});

test('kit pieces on the GLB: runs along their line, bridges along X, ramps rising north in climbable steps, budgets', () => {
  const G = glb('fps-kit-resort.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const cols = (piece, walk) => {
    const node = G.nodes.find((n) => n.name === 'KIT_RESORT_' + piece);
    assert.ok(node, piece);
    return (node.children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  };
  // link runs (no turn): the full rail module runs along glTF Z (Blender Y), so a north-south run of cells gets yaw 0
  const [rf] = cols('RailFull');
  assert.ok(rf.s[2] > 4 * rf.s[0], 'RailFull long axis on Z ' + JSON.stringify(rf.s));
  assert.ok(!TH.symbols.r.turn);
  // the half module reaches from the cell centre toward +Z (the placer's yaw 0 neighbour is the cell to the south)
  const [rh] = cols('RailHalf');
  assert.ok(rh.t[2] > 0.2 && rh.t[2] + rh.s[2] <= 0.51, 'RailHalf toward +Z ' + JSON.stringify(rh));
  // the rope bridge [3, 2]: its walkable planks span 3 m along X, its rope rails run along X
  const bw = cols('Bridge', true)[0];
  assert.ok(Math.abs(bw.s[0] - 1.5) < 0.02 && Math.abs(bw.s[2] - 0.9) < 0.02, 'bridge deck ' + JSON.stringify(bw.s));
  cols('Bridge').filter((b) => b.s[1] > 0.3).forEach((b) => assert.ok(b.s[0] > 5 * b.s[2], 'bridge rail along X ' + JSON.stringify(b.s)));
  // ramps: 52 walkable steps from the south end (+Z) up to 7.5 m at the north end (-Z), each a 0.25 m tread,
  // rising at most 0.15 m (robots step 0.4 m per 0.5 m nav cell, the player snaps down 0.2 m)
  for (const p of ['Ramp_Limb', 'Ramp_LimbB', 'Ramp_Frond']) {
    const st = cols(p, true).map((b) => ({ z: b.t[2], top: b.t[1] + b.s[1], w: b.s[0] })).sort((a, b) => b.z - a.z);
    assert.equal(st.length, 52, p);
    assert.ok(Math.abs(st[st.length - 1].top - 7.5) < 0.01 && st[st.length - 1].z < -6, p + ' top step at the north end');
    assert.ok(st[0].top < 0.2 && st[0].z > 6, p + ' first step at the south end');
    for (let i = 1; i < st.length; i++) {
      assert.ok(st[i].top - st[i - 1].top > 0 && st[i].top - st[i - 1].top <= 0.15, p + ' step ' + i);
      assert.ok(Math.abs(st[i - 1].z - st[i].z - 0.25) < 0.01, p + ' tread ' + i);
    }
    assert.ok(st.every((s) => s.w > 0.85), p + ' walkway wide enough for the nav grid');
  }
  // the trunks reach up through the platform; their collision stays inside the visible trunk
  for (const p of ['Landmark_GiantPalm_A', 'Landmark_GiantPalm_B']) {
    const c = cols(p);
    assert.ok(c.some((b) => b.t[1] + b.s[1] > 9.5), p + ' trunk through the platform');
    assert.ok(c.every((b) => b.s[0] <= 1.31 && b.s[2] <= 1.31), p + ' trunk box');
  }
});
