// Airfield 7 theme (kit-airfield7): level plan and waves (2 zones, elite targets for level 43), the two zones (size,
// gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, the aircraft inside the revetments and the
// shelter), the wall chooser (T-walls, the runway-closure barriers where the runway meets zone 1's side walls, the
// corner pillars), and the kit pieces checked on the GLB: stairs and the transport's ramp that the player and the
// robots climb, the walkable terrace, gallery and hold, the wall modules' collision on their inside face.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/airfield7.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.airfield7;
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
const plan = IB.LEVEL_PLANS.airfield7;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEGlisu';
const inside = (R, c, r) => c >= R.c && c < R.c + R.w && r >= R.r && r < R.r + R.h;

test('airfield7 theme: kit-airfield7, open sky over the steppe, two zones of waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-airfield7');
  assert.deepEqual(TH.families, ['kit-stronghold', 'kit-parking']);
  assert.ok(TH.env.sky && TH.env.clouds && TH.env.far >= 900);
  assert.equal(TH.env.ceiling, null);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 43): each zone holds 68-69.5 soldiers and 44-45.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.airfield7;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 68 && s <= 69.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 44 && b <= 45.5, 'zone ' + (i + 1) + ' blade bots ' + b));
  // the counts do not lean on the half-a-wave cap (so they hold at any level number): elites = round(2.5 x written)
  const raw = (zi, k) => RAW[zi].reduce((a, w) => a + w.filter(([t]) => t === k).reduce((b, e) => b + Math.round(e[1] * 2.5), 0), 0);
  assert.deepEqual(sold, [raw(0, 'soldier'), raw(1, 'soldier')]);
  assert.deepEqual(blad, [raw(0, 'blader'), raw(1, 'blader')]);
  p.zones.forEach((z) => z.waves.forEach((w) => {
    const tot = w.reduce((a, e) => a + e[1], 0), el = w.filter(([t]) => /soldier|grenadier|blader/.test(t)).reduce((a, e) => a + e[1], 0);
    assert.ok(el <= tot / 2, 'elites ' + el + ' of ' + tot);
  }));
});

const SIZES = { airfield7_1: [76, 78], airfield7_2: [72, 74] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, aircraft in their shelters', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    for (let r = 0; r < g.h; r++) { assert.ok('#GE'.includes(g.at(0, r))); assert.equal(g.at(g.w - 1, r), '#'); }
    const grids = [g].concat(g.layers);
    assert.deepEqual(g.layers.map((L) => L.y), [0], 'one layer at 0 for the aircraft and the gear inside');
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
    const L0 = g.layers[0];
    if (name === 'airfield7_1') {
      assert.equal(rects(g, 'T').length, 1, 'the control tower');
      assert.equal(rects(g, 'Q').length, 1, 'the transport');
      const Rv = rects(g, 'R');   // two revetments back to back (one block the engine tiles with two prefabs)
      assert.equal(Rv.reduce((a, R) => a + R.w * R.h, 0), 2 * 18 * 18, 'two revetments');
      // each revetment (open east) holds a fighter nose east on the layer, inside its walls (x 3..18 of the block)
      const jets = rects(L0, 'K');
      assert.equal(jets.length, 2);
      Rv.forEach((R) => { for (let r0 = R.r; r0 < R.r + R.h; r0 += 18) assert.ok(jets.some((J) => J.r === r0 + 4 && J.c === R.c + 3 && J.h === 10), 'fighter in revetment at row ' + r0); });
      // the spawn is behind the transport's ramp: the ramp toe (block centre, 12.5 m south of it) a few metres north
      const P = g.rows.findIndex((row) => row.includes('P')), pc = g.rows[P].indexOf('P'), Q = rects(g, 'Q')[0];
      assert.ok(Math.abs(pc + 0.5 - (Q.c + Q.w / 2)) < 1.5 && P - (Q.r + Q.h / 2 + 12.5) > 2 && P - (Q.r + Q.h / 2 + 12.5) < 8, 'spawn behind the ramp');
      assert.ok(rects(g, 'W').length === 2 && rects(g, 'V').length === 1, 'fighters on the runway, the taxiway and the apron');
      // runway edge lights on both edges of the runway (rows 6 and 23), the windsock, the AA guns
      assert.ok([...g.rows[6]].filter((ch) => ch === 'l').length >= 10 && [...g.rows[23]].filter((ch) => ch === 'l').length >= 10, 'runway edge lights');
      assert.equal(rects(g, 'w').length, 1);
      assert.equal(rects(g, 'A').length, 2);
      rects(g, 'j').forEach((R) => assert.equal(R.h, 1, 'jersey barrier lines run along X'));
    } else {
      assert.equal(rects(g, 'H').length, 1, 'the shelter');
      const H = rects(g, 'H')[0], M = rects(L0, 'M');
      assert.equal(M.length, 1);
      assert.ok(inside(H, M[0].c, M[0].r) && inside(H, M[0].c + M[0].w - 1, M[0].r + M[0].h - 1), 'the fighter is inside the shelter');
      assert.ok(Math.abs(M[0].c + M[0].w / 2 - (H.c + H.w / 2)) < 0.01, 'on the shelter centre line');
      for (const ch of 'NYDZ') assert.equal(rects(g, ch).length, 1, ch);
      const N = rects(g, 'N')[0];
      for (const ch of 'zq123') rects(L0, ch).forEach((R) => assert.ok(inside(N, R.c, R.r) && inside(N, R.c + R.w - 1, R.r + R.h - 1), ch + ' inside the hangar'));
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

test('wall chooser: T-walls, runway-closure barriers on zone 1\'s side walls over the runway, corner pillars, gaps for the gate frames', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  maps.forEach(({ name, g }, zi) => {
    let n = 0, bars = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const out = TH.wall.choose(c, r, false, false, hash, g, 'S');
      if (out === null) { assert.ok(r === 0 || r === g.h - 1, 'only gate neighbours are empty'); continue; }
      n++;
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      const corner = (r === 0 || r === g.h - 1) && (c === 0 || c === g.w - 1);
      if (corner) { assert.equal(out, 'TWall_Corner'); continue; }
      const side = c === 0 || c === g.w - 1;
      if (zi === 0 && side && r >= 2 && r <= 26) { assert.ok(/^Barrier_/.test(out), 'barrier at ' + c + ',' + r); bars++; } else assert.ok(/^TWall_/.test(out), name + ' T-wall at ' + c + ',' + r + ' ' + out);
    }
    assert.ok(n > 250, name + ' wall modules ' + n);
    if (zi === 0) assert.equal(bars, 50, 'barriers over the runway and its shoulders, both sides');
  });
});

test('kit pieces on the GLB: stairs and the ramp the robots climb, the terrace, gallery and hold are walkable, wall collision on the inside face', () => {
  const G = glb('fps-kit-airfield7.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  // the borrowed pieces exist in their own kits
  const other = { KIT_STRONGHOLD_: glb('fps-kit-stronghold.glb'), KIT_PARKING_: glb('fps-kit-parking.glb') };
  assert.ok(TH.borrowed.length >= 12);
  for (const n of TH.borrowed) { const k = Object.keys(other).find((p) => n.startsWith(p)); assert.ok(k && other[k].nodes.some((nd) => nd.name === n), 'borrowed ' + n); }
  const node = (piece) => { const nd = G.nodes.find((n) => n.name === 'KIT_AIRFIELD7_' + piece); assert.ok(nd, piece); return nd; };
  const cols = (piece, walk) => (node(piece).children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  // wall modules: the T-walls' collision lies on the inside face (Blender -Y = glTF +Z), 3.6 m high, along X
  for (const p of ['TWall_A', 'TWall_B', 'TWall_Light', 'TWall_End']) {
    const [b] = cols(p);
    assert.ok(b.s[0] >= 0.49 && b.s[2] <= 0.16 && b.t[2] > 0.3 && b.t[2] < 0.5 && b.t[1] + b.s[1] >= 3.59, p + ' collision along X on the inside face ' + JSON.stringify(b));
  }
  const [bb] = cols('Barrier_A');
  assert.ok(bb.s[0] >= 0.49 && Math.abs(bb.t[2] + bb.s[2] - 0.5) < 0.01 && Math.abs(bb.t[1] + bb.s[1] - 1.1) < 0.01, 'barrier collision reaches the inside face ' + JSON.stringify(bb));
  // stairs and the ramp: every walkable step rises at most 0.2 m over the one below on a 0.5 m tread (robots climb
  // 0.4 m per 0.5 m nav cell), up to the terrace / gallery / hold floor
  const climb = (piece, top, minSteps, rise) => {
    const st = cols(piece, true).map((b) => ({ x: b.t[0], z: b.t[2], top: b.t[1] + b.s[1], wx: b.s[0] * 2, wz: b.s[2] * 2 }))
      .filter((b) => Math.min(b.wx, b.wz) < 0.51 && b.top < top + 0.01).sort((a, b) => a.top - b.top);
    const one = st.filter((b, i, A) => i === 0 || b.top - A[i - 1].top > 0.01 || Math.hypot(b.x - A[i - 1].x, b.z - A[i - 1].z) > 3);
    const lane = one.filter((b) => Math.abs(b.x - one[0].x) < 0.01);   // the first stair of the piece (all run along glTF Z)
    assert.ok(lane.length >= minSteps, piece + ' steps ' + lane.length);
    for (let i = 1; i < lane.length; i++) {
      assert.ok(Math.abs(lane[i].top - lane[i - 1].top - rise) < 0.005, piece + ' rise ' + i + ' ' + (lane[i].top - lane[i - 1].top).toFixed(3));
      assert.ok(Math.abs(Math.hypot(lane[i].x - lane[i - 1].x, lane[i].z - lane[i - 1].z) - 0.5) < 0.01, piece + ' tread ' + i);
    }
    assert.ok(Math.abs(lane[lane.length - 1].top - top) < 0.08, piece + ' reaches ' + top + ' (' + lane[lane.length - 1].top + ')');
    assert.ok(lane.every((s) => Math.max(s.wx, s.wz) >= 1.55), piece + ' wide enough for the nav grid');
  };
  climb('Landmark_Tower', 3.6, 18, 0.2);
  climb('Barracks', 3.2, 16, 0.2);
  climb('Transport', 1.2, 8, 0.15);
  // the walkable decks: the tower terrace, the barracks gallery, the transport's hold floor
  const area = (p, y) => cols(p, true).filter((b) => Math.abs(b.t[1] + b.s[1] - y) < 0.01 && b.s[0] > 0.6 && b.s[2] > 0.6).reduce((a, b) => a + 4 * b.s[0] * b.s[2], 0);
  assert.ok(area('Landmark_Tower', 3.6) > 80, 'tower terrace ' + area('Landmark_Tower', 3.6));
  assert.ok(area('Barracks', 3.2) > 70, 'barracks gallery ' + area('Barracks', 3.2));
  assert.ok(area('Transport', 1.2) > 35, 'transport hold ' + area('Transport', 1.2));
  // budgets
  const T = TH.budget;
  assert.ok(T.prop >= 4800 && T.landmark >= 4000);
});
