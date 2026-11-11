// Meridian International theme (kit-airport): level plan and waves (2 zones, elite targets), the two zones (size,
// gates, layers, symbols, prefab tiling and facing, spawns, pickups, one landmark-scale centrepiece each), the wall
// chooser (every piece in the kit; art codes only on wall cells, never symbols), runs modelled along their line of
// cells (glass screens, rails, belt barriers on the GLB's collision boxes; island and X-ray runs along X), the stair /
// escalator / scaffold steps rising north in climbable steps, the jet's walkable wing, and the borrowed pieces.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/airport.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.airport;
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
const plan = IB.LEVEL_PLANS.airport;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEGenU';
const ART = '¹²³¼½¾×÷¿¡¢£§©®°';
const CODES = '¤¦';

test('airport theme: kit-airport with kit-parking / kit-hotel / kit-police, a 14 m terminal, two zones (the apron open to the sky), bombers at most 2 a wave', () => {
  assert.equal(TH.family, 'kit-airport');
  assert.deepEqual(TH.families, ['kit-parking', 'kit-hotel', 'kit-police']);
  assert.equal(TH.env.ceiling.height, 14);
  assert.equal(TH.wall.height, 14);
  assert.equal(plan.zones.length, 2);
  assert.equal(plan.zones[1].ceiling, false);
  assert.ok(TH.backdrop && typeof TH.backdrop.build === 'function');
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader', 'mech', 'hawk', 'grenadier'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 34): each zone has 58 - 59.5 soldiers and 34 - 35.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.airport;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  p.zones.forEach((z, i) => {
    const s = count(z, (t) => t === 'soldier' || t === 'grenadier'), b = count(z, (t) => t === 'blader');
    assert.ok(s >= 58 && s <= 59.5, 'zone ' + i + ' soldiers ' + s);
    assert.ok(b >= 34 && b <= 35.5, 'zone ' + i + ' bladers ' + b);
  });
  p.zones.forEach((z) => z.waves.forEach((w) => {
    const tot = w.reduce((a, e) => a + e[1], 0), el = w.filter(([t]) => /soldier|grenadier|blader/.test(t)).reduce((a, e) => a + e[1], 0);
    assert.ok(el <= tot / 2, 'elites ' + el + ' of ' + tot);
  }));
  assert.ok(!p.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

const SIZES = { airport_1: [80, 78], airport_2: [72, 74] };
const LAYERS = { airport_1: [0.01, 0.02, 0.025, 4.5, 14], airport_2: [0.01, 0.02, 0.025, 2.6, 5.2, 14] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, symbols, prefab tiling and facing, spawns, pickups', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    assert.deepEqual(g.layers.map((L) => L.y), LAYERS[name]);
    const art = g.layers[2];
    // the art layer: art codes on wall cells only, the zone code at (0, 0), nothing that is a symbol
    art.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.' || (c === 0 && r === 0)) return;
      assert.ok(ART.includes(ch), name + ' art ' + ch);
      assert.equal(g.at(c, r), '#', name + ' art code ' + ch + ' off the wall at ' + c + ',' + r);
    }));
    for (const ch of ART + CODES) assert.ok(!TH.symbols[ch], 'art / zone code ' + ch + ' is not a symbol');
    assert.equal(art.at(0, 0), name === 'airport_1' ? '¤' : '¦');
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '#' || STAND.includes(ch) || TH.symbols[ch], name + ' plan ' + ch + ' at ' + c + ',' + r)));
    for (const L of g.layers) if (L !== art) L.rows.forEach((row) => [...row].forEach((ch) => assert.ok(ch === '.' || TH.symbols[ch], name + ' layer ' + L.y + ' ' + ch)));
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
    // runs: islands and X-ray lanes north-south (whole pieces, at least three), seats in single rows
    for (const ch of 'IJKLX') rects(g, ch).forEach((R) => assert.ok(R.w === (ch === 'X' ? 2 : 6) && R.h % 3 === 0 && R.h >= 9, name + ' run ' + ch + ' ' + JSON.stringify(R)));
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++; }));
    assert.equal(P.length, 1);
    const decks = g.layers.filter((L) => L.y > 1 && L.y < 10);
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'S') return;
      S++;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P');
      decks.forEach((D) => assert.equal(D.at(c, r), '.', name + ' spawn under a deck'));
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    // one centrepiece per zone: the departures board in the terminal, the jet in the hangar
    if (name === 'airport_1') assert.equal(rects(g, 'B').length, 1);
    else { let n = 0; g.rows.forEach((row) => { n += [...row].filter((ch) => ch === '@').length; }); assert.equal(n, 1); }
  });
}

test('wall chooser: every exposed wall cell gets a kit piece; glass where the terminal faces the apron and the kerb', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.3;
  for (const { name, g } of maps) {
    const solid = (c, r) => '#GE'.includes(g.at(c, r));
    const seen = new Set();
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r);
      const nOpen = oS + oN + oE + oW;
      const exposed = nOpen > 0 || [[1, 1], [1, -1], [-1, 1], [-1, -1]].some(([x, y]) => !solid(c + x, r + y));
      if (!exposed) continue;
      const face = nOpen === 0 ? 'none' : nOpen === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      assert.ok(all.has(out), name + ' chooser piece ' + out + ' at ' + c + ',' + r);
      seen.add(out);
    }
    if (name === 'airport_1') ['WT', 'WG', 'WG_M', 'WG_Door', 'WG_Bridge', 'WC', 'WT_WC', 'WT_FIDS'].forEach((p) => assert.ok(seen.has(p), name + ' uses ' + p));
    else ['WH', 'WH_Col', 'WF', 'WF_DoorA', 'WA', 'WA_Sign', 'WO'].forEach((p) => assert.ok(seen.has(p), name + ' uses ' + p));
  }
});

test('kit pieces on the GLB: runs along their line of cells, run prefabs along X, steps rising north, the walkable wing', () => {
  const G = glb('fps-kit-airport.glb');
  const node = (piece) => { const n = G.nodes.find((x) => x.name === 'KIT_AIRPORT_' + piece); assert.ok(n, piece); return n; };
  const boxes = (piece) => (node(piece).children || []).map((i) => G.nodes[i]).filter((n) => /_W?COL\d+$/.test(n.name))
    .map((n) => ({ walk: /_WCOL\d+$/.test(n.name), t: n.translation || [0, 0, 0], s: n.scale }));
  const extent = (piece) => {
    const e = [Infinity, -Infinity, Infinity, -Infinity];
    boxes(piece).forEach((b) => { e[0] = Math.min(e[0], b.t[0] - b.s[0]); e[1] = Math.max(e[1], b.t[0] + b.s[0]); e[2] = Math.min(e[2], b.t[2] - b.s[2]); e[3] = Math.max(e[3], b.t[2] + b.s[2]); });
    return e;
  };
  // link runs (no turn): full modules along glTF Z (Blender Y), so a north-south run of cells gets yaw 0
  for (const [p, ch] of [['GlassFull', 'q'], ['GRailFull', "'"], ['YRailFull', '\\'], ['BeltFull', 'b']]) {
    const [b] = boxes(p);
    assert.ok(b.s[2] > 4 * b.s[0], p + ' long axis on Z ' + JSON.stringify(b.s));
    assert.ok(!TH.symbols[ch].turn, p + ' needs no turn');
    const [h] = boxes(p.replace('Full', 'Half'));
    assert.ok(h.t[2] > 0 && h.s[2] > 4 * h.s[0], p + ' half module toward +Z');
  }
  // runs of prefabs (island, X-ray): one run step (3 m) along X, the depth across; the door, shutters, e-gates,
  // seats and gondolas: long axis on X (their [w, d] footprint)
  for (const [p, w, d] of [['Isl_Mid', 3, 6], ['Isl_End', 3, 6], ['Isl_Hood', 3, 6], ['Xr_In', 3, 2], ['Xr_Tunnel', 3, 2], ['Xr_Out', 3, 2]]) {
    const e = extent(p);
    assert.ok(Math.abs(e[1] - e[0] - w) < 0.05 && e[3] - e[2] <= d + 0.01, p + ' run step on X ' + JSON.stringify(e));
  }
  for (const p of ['LoungeDoor', 'EGate', 'ShutterUp', 'ShutterHalf', 'Seats', 'Gondola']) {
    const e = extent(p);
    assert.ok(e[1] - e[0] > e[3] - e[2], p + ' long axis on X ' + JSON.stringify(e));
  }
  assert.equal(TH.symbols.n.orient, 'span');
  // steps: walkable blocks rising toward glTF -Z (Blender +Y, game north at yaw 0), each rise climbable
  for (const p of ['Stair', 'Escalator', 'Scaf']) {
    const w = boxes(p).filter((b) => b.walk).map((b) => ({ z: b.t[2], top: b.t[1] + b.s[1] })).sort((a, b) => b.z - a.z);
    assert.ok(w.length >= 10, p + ' steps');
    // a robot's nav cell is 0.5 m: each step at least 0.5 m deep and at most 0.4 m up, so no cell spans two risers
    for (let i = 1; i < w.length; i++) assert.ok(w[i].top - w[i - 1].top <= 0.4 && w[i].top >= w[i - 1].top && w[i - 1].z - w[i].z >= 0.49, p + ' step ' + i);
  }
  // the stairs truck: steps rise toward glTF +Z (its front, the cab end) to the platform at the dock height
  const st = boxes('StairTruck').filter((b) => b.walk).sort((a, b) => a.t[2] - b.t[2]);
  assert.ok(Math.abs(Math.max(...st.map((b) => b.t[1] + b.s[1])) - 2.6) < 0.01, 'stairs truck platform at 2.6');
  for (let i = 1; i < st.length; i++) assert.ok(st[i].t[1] + st[i].s[1] - (st[i - 1].t[1] + st[i - 1].s[1]) <= 0.4 && st[i].t[2] - st[i - 1].t[2] >= 0.49, 'stairs truck step ' + i);
  // the jet: walkable wing strips both sides; the strips by the fuselage a step under the 2.6 m work platforms, the
  // wing rising outboard (dihedral) in small steps
  const wing = boxes('Jet_Body').filter((b) => b.walk);
  assert.equal(wing.length, 22);
  [-1, 1].forEach((s) => {
    const side = wing.filter((b) => Math.sign(b.t[0]) === s).sort((a, b) => Math.abs(a.t[0]) - Math.abs(b.t[0])).map((b) => b.t[1] + b.s[1]);
    assert.ok(side[0] > 2.6 - 0.35 && side[0] < 2.6, 'root strip ' + side[0]);
    for (let i = 1; i < side.length; i++) assert.ok(side[i] - side[i - 1] >= 0 && side[i] - side[i - 1] < 0.1, 'wing step ' + i);
  });
});

test('glow companions and borrowed pieces exist', () => {
  const names = new Set(glb('fps-kit-airport.glb').nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'kit piece ' + p);
  const fams = { KIT_PARKING_: 'fps-kit-parking.glb', KIT_HOTEL_: 'fps-kit-hotel.glb', KIT_POLICE_: 'fps-kit-police.glb' };
  const have = {};
  Object.entries(fams).forEach(([k, f]) => { have[k] = new Set(glb(f).nodes.map((n) => n.name)); });
  for (const n of TH.borrowed()) { const k = Object.keys(fams).find((p) => n.startsWith(p)); assert.ok(k && have[k].has(n), 'borrowed ' + n); }
});
