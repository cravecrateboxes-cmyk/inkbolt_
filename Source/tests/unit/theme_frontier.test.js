// Cinder Ridge Outpost theme (kit-frontier): level plan and waves (2 zones, elite targets for level 35, the last
// map), the two zones (size, gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, the walk-in
// buildings), zone 2's terrain (plateaus, ravine, bridge ends, level ground under buildings and spawns, every open
// slope climbable), the wall chooser, and the kit pieces checked on the GLB: run pieces along their line of cells,
// the bridge along X, stairs that the player and the robots climb, the walk-in floors.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/frontier.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.frontier;
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
  g.layers = layers;
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
const plan = IB.LEVEL_PLANS.frontier;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const GROUND = '.,:;';
const STAND = GROUND + "SahPEG'~A=";

test('frontier theme: kit-frontier, open sky, terrain, two zones of waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-frontier');
  assert.ok(TH.env.sky && TH.env.clouds);
  assert.equal(TH.env.ceiling, null);
  assert.equal(typeof TH.terrain.paint, 'function');
  assert.deepEqual(TH.terrain.ramp, [0, 1]);
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader', 'mech', 'hawk', 'grenadier'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 35): each zone holds 59-60.5 soldiers and 35-36.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.frontier;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 59 && s <= 60.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 35 && b <= 36.5, 'zone ' + (i + 1) + ' blade bots ' + b));
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

const SIZES = { frontier_1: [72, 70], frontier_2: [76, 72] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols, prefab tiling and facing, spawns, pickups, landmark, walk-ins', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)) || g.at(c, r) === 'P', 'entry approach');
    for (let r = 0; r < g.h; r++) { assert.ok('#{'.includes(g.at(0, r)) || 'GE'.includes(g.at(0, r))); assert.equal(g.at(g.w - 1, r), '#'); }
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '#' || STAND.includes(ch) || TH.symbols[ch], name + ' plan ' + ch + ' at ' + c + ',' + r)));
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      rects(g, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
        if (typeof d.face === 'number') {   // a fixed facing turns the model, so the block must match the turned footprint
          const side = Math.abs(Math.sin(d.face)) > 0.5;
          const [sw, sd] = side ? [d.size[1], d.size[0]] : d.size;
          assert.ok(R.w % sw === 0 && R.h % sd === 0, name + ' fixed-facing ' + ch + ' ' + JSON.stringify(R));
          if (side && d.size[0] !== d.size[1]) assert.ok(!(R.w % d.size[0] === 0 && R.h % d.size[1] === 0), name + ' merged block of ' + ch + ' ' + JSON.stringify(R));
        }
      });
    }
    // walk-in fronts face the street: west row (R90) fronts on the street's west edge, east row (-R90) on its east edge
    if (name === 'frontier_1') {
      for (const ch of 'HBKU') rects(g, ch).forEach((R) => assert.equal(g.at(R.c + R.w, R.r + 1), ':', ch + ' front on the street'));
      for (const ch of 'TOMku') rects(g, ch).forEach((R) => assert.equal(g.at(R.c - 1, R.r + 1), ':', ch + ' front on the street'));
      for (const ch of 'HTB') assert.equal(rects(g, ch).length, 1, 'walk-in ' + ch);
      assert.equal(rects(g, 'W').length, 1, 'the water tower');
      assert.equal(rects(g, 'Y').length + rects(g, 'y').length, 4, 'four watchtowers');
    } else {
      assert.equal(rects(g, 'X').length, 1, 'the lookout');
      for (const ch of 'I=J*C') assert.ok(rects(g, ch).length >= 1, ch);
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

test('zone 2 terrain: plateaus 3.2 m up, the ravine floor and the bridge ends, lips and banks where it steps, every open slope climbable', () => {
  const g = maps[1].g, H = TH.terrain.height;
  // the engine's easing (zones.js buildTerrain, ramp [0, 1]): flat cells pin their corners
  const W = g.w + 1, flat = '#GEPS' + TH.terrain.flat, pin = new Uint8Array(W * (g.h + 1));
  for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if (r === 0 || c === 0 || r === g.h - 1 || c === g.w - 1 || flat.includes(g.at(c, r))) { pin[r * W + c] = pin[r * W + c + 1] = pin[(r + 1) * W + c] = pin[(r + 1) * W + c + 1] = 1; }
  const hf = (c, r) => (pin[r * W + c] ? 0 : H(c, r, 1));
  rects(g, '=').forEach((R) => {
    assert.equal(hf(R.c, R.r), 3.2, 'bridge west end'); assert.equal(hf(R.c + R.w, R.r + 1), 3.2, 'bridge east end');
    for (let c = R.c + 2; c <= R.c + 5; c++) assert.equal(hf(c, R.r), 0, 'ravine floor under the bridge');
  });
  rects(g, 'X').forEach((R) => { for (let r = R.r; r <= R.r + R.h; r++) for (let c = R.c; c <= R.c + R.w; c++) assert.equal(hf(c, r), 3.2, 'lookout on the plateau'); });
  let open = 0;
  for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
    const ch = g.at(c, r), a = hf(c, r), b = hf(c + 1, r), d = hf(c, r + 1), e = hf(c + 1, r + 1);
    if (TH.terrain.flat.includes(ch)) assert.ok(Math.max(a, b, d, e) < 0.01, 'level ground under ' + ch + ' at ' + c + ',' + r);
    if (ch === 'S') assert.ok(Math.max(a, b, d, e) < 0.01, 'spawn on level ground ' + c + ',' + r);
    if (!(GROUND + "'~Sah").includes(ch)) continue;
    open++;
    const edge = Math.max(Math.abs(a - b), Math.abs(d - e), Math.abs(a - d), Math.abs(b - e));
    assert.ok(edge <= 0.75, 'open slope ' + edge.toFixed(2) + ' at ' + c + ',' + r);
  }
  assert.ok(open > 3000);
  // where the ground steps by more than a robot's stride, a lip / bank / wall cell stands in it
  for (let r = 1; r < 29; r++) for (const c of [30, 34]) {
    const step = Math.abs(hf(c, r) - hf(c + 1, r)) || 0;
    if (step > 0.75 && !(r === 10 || r === 11)) assert.ok('RQ()'.includes(g.at(c, r)), 'bank at ' + c + ',' + r);
  }
  assert.equal(TH.terrainHeight(10, 10, 0), 0, 'zone 1 is level');
});

test('wall chooser: palisade in the stockade, forest edge and rim in the wild, gaps left for the gate frames', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  maps.forEach(({ name, g }, zi) => {
    let n = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const out = TH.wall.choose(c, r, false, false, hash, g, 'S');
      if (out === null) continue;
      n++;
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      assert.ok(zi === 0 ? /^Palisade_/.test(out) : /^(Edge|Rim)_/.test(out), name + ' ' + out);
    }
    assert.ok(n > 200, name + ' wall modules ' + n);
  });
});

test('kit pieces on the GLB: runs along their line, the bridge along X, stairs the robots climb, walk-in floors, budgets', () => {
  const G = glb('fps-kit-frontier.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const cols = (piece, walk) => {
    const node = G.nodes.find((n) => n.name === 'KIT_FRONTIER_' + piece);
    assert.ok(node, piece);
    return (node.children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  };
  // link runs (no turn): the full fence module runs along glTF Z (Blender Y), the half reaches from the centre toward +Z
  const [ff] = cols('FenceFull');
  assert.ok(ff.s[2] > 4 * ff.s[0], 'FenceFull long axis on Z ' + JSON.stringify(ff.s));
  assert.ok(!TH.symbols.f.turn);
  const [fh] = cols('FenceHalf');
  assert.ok(fh.t[2] > 0.2 && fh.t[2] + fh.s[2] <= 0.51, 'FenceHalf toward +Z ' + JSON.stringify(fh));
  // the hitching rail [3, 1] runs along X; the flume [1, 4] along Z; the bridge [7, 2] deck along X at 3.2 m
  assert.ok(cols('HitchRail')[0].s[0] > 5 * cols('HitchRail')[0].s[2], 'hitching rail along X');
  const bw = cols('Bridge', true)[0];
  assert.ok(Math.abs(bw.s[0] - 3.5) < 0.02 && bw.s[2] < 0.75 && Math.abs(bw.t[1] + bw.s[1] - 3.2) < 0.01, 'bridge deck ' + JSON.stringify(bw));
  cols('Bridge').filter((b) => b.t[1] > 3.1 && Math.max(b.s[0], b.s[2]) > 1).forEach((b) => assert.ok(b.s[0] > 5 * b.s[2], 'bridge rail along X ' + JSON.stringify(b.s)));
  // stairs: every walkable step rises at most 0.2 m over the one below it (robots climb 0.4 m per 0.5 m nav cell, the
  // player steps 0.5 m on walkable boxes): 0.18 m on treads of 0.25 m (0.36 m per nav cell), from the floor up to the deck / upper floor
  const climb = (piece, top, axis) => {
    const st = cols(piece, true).map((b) => ({ u: b.t[axis], top: b.t[1] + b.s[1], w: b.s[axis === 0 ? 2 : 0], d: b.s[axis] * 2 }))
      .filter((b) => Math.abs(b.d - 0.25) < 0.01).sort((a, b) => a.top - b.top);
    assert.ok(st.length >= 12, piece + ' steps ' + st.length);
    for (let i = 1; i < st.length; i++) {
      assert.ok(st[i].top - st[i - 1].top > 0.175 && st[i].top - st[i - 1].top < 0.185, piece + ' rise ' + i);
      assert.ok(Math.abs(Math.abs(st[i].u - st[i - 1].u) - 0.25) < 0.01, piece + ' tread ' + i);
    }
    assert.ok(Math.abs(st[st.length - 1].top - top) < 0.01, piece + ' reaches ' + top);
    assert.ok(st.every((s) => s.w >= 0.6), piece + ' stair wide enough for the nav grid');
  };
  climb('Tower', 3.6, 2);
  climb('Landmark_Lookout', 2.34, 0);
  climb('Store', 3.59, 0);
  // walk-in floors: the store, the trading post and the bunkhouse stand 0.35 m up on walkable floors
  for (const p of ['Store', 'TradingPost', 'Bunkhouse']) {
    const fl = cols(p, true).filter((b) => Math.abs(b.t[1] + b.s[1] - 0.35) < 0.01 && b.s[0] > 3);
    assert.ok(fl.length >= 2, p + ' floor and porch');
  }
  // the store's upper floor is walkable at 3.59 m
  assert.ok(cols('Store', true).some((b) => Math.abs(b.t[1] + b.s[1] - 3.59) < 0.01 && b.s[0] > 3), 'store upper floor');
});
