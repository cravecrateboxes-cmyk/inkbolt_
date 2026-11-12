// Mosswood Gardens theme (kit-mossgarden): level plan and waves (2 zones, elite targets for level 37), the two zones
// (size, gates, symbols, prefab tiling and facing, spawns on level ground, pickups, landmarks), the terrain (the
// terrace exactly 2.34 m up inside its balustrade ring, stairs in the ring, the folly on the mound's plateau, open
// slopes climbable), the GARDEN ribbons (paths and the stream run over open ground only), the wall chooser, and the
// kit pieces checked on the GLB: hedge runs along their line of cells, the rose arch and the bridge across their
// paths, stairs and bridge steps the robots climb, glow companions.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/mossgarden.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.mossgarden;
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
const plan = IB.LEVEL_PLANS.mossgarden;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const GROUND = '.;:_~,';
const STAND = GROUND + 'SahPEGbvnzi';
const GD = TH.garden;

test('mossgarden theme: kit-mossgarden, open sky, terrain, two zones of waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-mossgarden');
  assert.ok(TH.env.sky && TH.env.clouds);
  assert.equal(TH.env.ceiling, null);
  assert.equal(typeof TH.terrain.paint, 'function');
  assert.deepEqual(TH.terrain.ramp, [0, 1]);
  assert.equal(TH.terrain.flat, '');
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader', 'mech', 'hawk', 'grenadier'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 37): each zone holds 62-63.5 soldiers and 38-39.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.mossgarden;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 62 && s <= 63.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 38 && b <= 39.5, 'zone ' + (i + 1) + ' blade bots ' + b));
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

// the engine's easing (zones.js buildTerrain, ramp [0, 1]): walls, gates, the entry and the spawns pin their corners
function heights(g, zi) {
  const W = g.w + 1, flat = '#GEPS' + TH.terrain.flat, pin = new Uint8Array(W * (g.h + 1));
  for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if (r === 0 || c === 0 || r === g.h - 1 || c === g.w - 1 || flat.includes(g.at(c, r))) { pin[r * W + c] = pin[r * W + c + 1] = pin[(r + 1) * W + c] = pin[(r + 1) * W + c + 1] = 1; }
  return (c, r) => (pin[r * W + c] ? 0 : TH.terrainHeight(c, r, zi));
}

const SIZES = { mossgarden_1: [72, 70], mossgarden_2: [74, 70] };
for (const [zi, { name, g }] of maps.entries()) {
  test('zone ' + name + ': size, gates, symbols, prefab tiling and facing, spawns, pickups, landmarks', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)) || g.at(c, r) === 'P', 'entry approach');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
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
        }
        if (d.orient === 'wall') {   // wall-backed prefabs stand against the garden wall, along it
          const touch = [...Array(R.w).keys()].some((i) => g.at(R.c + i, R.r - 1) === '#' || g.at(R.c + i, R.r + R.h) === '#') ||
            [...Array(R.h).keys()].some((i) => g.at(R.c - 1, R.r + i) === '#' || g.at(R.c + R.w, R.r + i) === '#');
          assert.ok(touch, name + ' ' + ch + ' against a wall ' + JSON.stringify(R));
          const alongX = R.w >= R.h;
          if (R.w !== R.h) assert.ok(alongX ? (g.at(R.c, R.r - 1) === '#' || g.at(R.c, R.r + R.h) === '#') : (g.at(R.c - 1, R.r) === '#' || g.at(R.c + R.w, R.r) === '#'), name + ' ' + ch + ' long side on the wall');
        }
      });
    }
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++; }));
    assert.equal(P.length, 1);
    const hf = heights(g, zi);
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'S') return;
      S++;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P');
      assert.ok(Math.max(TH.terrainHeight(c, r, zi), TH.terrainHeight(c + 1, r + 1, zi), TH.terrainHeight(c + 1, r, zi), TH.terrainHeight(c, r + 1, zi)) < 0.01, name + ' spawn on level ground ' + c + ',' + r);
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    if (zi === 0) {
      assert.equal(rects(g, 'F').length, 1, 'the fountain');
      assert.equal(rects(g, 'X').length, 1, 'the glasshouse');
      for (const ch of 'UuYpbRlHOCw') assert.ok(rects(g, ch).length >= 1, ch);
    } else {
      assert.equal(rects(g, 'M').length, 1, 'the folly');
      assert.equal(rects(g, 'D').length, 2, 'two bridges');
      for (const ch of 'VZN I&$H'.replace(' ', '')) assert.ok(rects(g, ch).length >= 1, ch);
    }
    assert.ok(hf(1, 1) === 0);
  });
}

test('zone 1 terrain: the terrace 2.34 m up inside its ring, the stairs in the ring, level ground elsewhere', () => {
  const g = maps[0].g, hf = heights(g, 0), [c0, r0, c1, r1, H] = GD.terrace;
  assert.equal(H, 2.34);
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) assert.equal(hf(c, r), H, 'terrace corner ' + c + ',' + r);
  for (let r = r0; r < r1; r++) for (let c = c0; c < c1; c++) assert.ok(!'BKQ#'.includes(g.at(c, r)), 'terrace interior ' + c + ',' + r);
  // the ring: every cell round the interior is a balustrade, a corner pier, a back border or a stair
  for (let c = c0 - 1; c <= c1; c++) { assert.ok('BKUu'.includes(g.at(c, r1)), 'south ring ' + c); assert.ok('QK^'.includes(g.at(c, r0 - 1)), 'back row ' + c); }
  for (let r = r0 - 1; r <= r1; r++) { assert.ok('|KY'.includes(g.at(c1, r)), 'east ring ' + r); assert.ok('^K'.includes(g.at(c0 - 1, r)) || r === r0 - 1, 'back column ' + r); }
  // each ring symbol turns its walk side (the piece's front, +Z) toward the terrace
  const yaw = { B: Math.PI, '|': -Math.PI / 2, Q: 0, '^': Math.PI / 2 };
  for (const [ch, y] of Object.entries(yaw)) assert.equal(TH.symbols[ch].rotate, y, ch);
  // the ring stands on 0 (its cells sit on the terrain's slope from the terrace down to the garden)
  for (const ch of 'B|QK^') assert.equal(TH.symbols[ch].onTerrain, false, ch);
  // stairs: the top row of each stair block is the ring row, the foot on the garden ground
  rects(g, 'U').forEach((R) => { assert.equal(R.r, r1); assert.ok(GROUND.includes(g.at(R.c + 2, R.r + R.h))); });
  rects(g, 'u').forEach((R) => { assert.equal(R.r, r1); assert.ok(GROUND.includes(g.at(R.c + 1, R.r + R.h))); });
  rects(g, 'Y').forEach((R) => { assert.equal(R.c, c1); assert.ok(GROUND.includes(g.at(R.c + R.w, R.r + 1))); });
  // nothing else is raised
  for (let r = 0; r <= g.h; r++) for (let c = 0; c <= g.w; c++) if (c < c0 || c > c1 || r < r0 || r > r1) assert.equal(hf(c, r), 0);
});

test('zone 2 terrain: the folly on the mound\'s plateau, every open slope climbable, spawns and the stream on level ground', () => {
  const g = maps[1].g, hf = heights(g, 1), M = GD.mound;
  rects(g, 'M').forEach((R) => { for (let r = R.r; r <= R.r + R.h; r++) for (let c = R.c; c <= R.c + R.w; c++) assert.ok(Math.abs(hf(c, r) - M[4]) < 1e-6, 'folly on the plateau ' + c + ',' + r); });
  let open = 0;
  for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
    const ch = g.at(c, r), a = hf(c, r), b = hf(c + 1, r), d = hf(c, r + 1), e = hf(c + 1, r + 1);
    if ('~iDVNIZ'.includes(ch)) assert.ok(Math.max(a, b, d, e) < 0.01, 'level ground under ' + ch + ' at ' + c + ',' + r);
    if (!STAND.includes(ch)) continue;
    open++;
    assert.ok(Math.max(Math.abs(a - b), Math.abs(d - e), Math.abs(a - d), Math.abs(b - e)) <= 0.75, 'open slope at ' + c + ',' + r);
  }
  assert.ok(open > 3000);
});

// the theme's curve sampler: the ribbons the theme draws run over open ground (paths may run into a stair foot, the
// fountain plaza, a bridge, the gazebo, the folly or the glasshouse door), the stream over its own cells
test('GARDEN ribbons: paths over open ground, the stream over its cells and under its bridges', () => {
  maps.forEach(({ name, g }, zi) => {
    (GD.paths[zi] || []).forEach((P, pi) => {
      const S = TH.sampleCurve(P.pts, 0.25);
      let bad = [];
      S.forEach((q) => {
        for (const t of [-P.w / 2 + 0.03, 0, P.w / 2 - 0.03]) {
          const ch = g.at(Math.floor(q.x + q.nx * t), Math.floor(q.z + q.nz * t));
          if (!(STAND + 'UuYFXZDMVR').includes(ch)) bad.push(ch + '@' + (q.x + q.nx * t).toFixed(1) + ',' + (q.z + q.nz * t).toFixed(1));
        }
      });
      assert.equal(bad.length, 0, name + ' path ' + pi + ' over ' + bad.slice(0, 6).join(' '));
    });
    (GD.streams[zi] || []).forEach((st) => {
      TH.sampleCurve(st.pts, 0.25).forEach((q) => {
        for (const t of [-st.w / 2 + 0.03, 0, st.w / 2 - 0.03]) {
          const ch = g.at(Math.floor(q.x + q.nx * t), Math.floor(q.z + q.nz * t));
          assert.ok('~iDNI'.includes(ch), name + ' stream over ' + ch + ' at ' + q.x.toFixed(1) + ',' + q.z.toFixed(1));
        }
      });
    });
  });
});

test('wall chooser: 2 m modules paired along every run (no cell covered twice), corner piers, gaps for the gate frames', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  const side = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };   // the module's local +X in (dc, dr)
  maps.forEach(({ name, g }) => {
    const cover = new Map();
    let n = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !'#GE'.includes(g.at(c, r + 1)), oN = !'#GE'.includes(g.at(c, r - 1)), oE = !'#GE'.includes(g.at(c + 1, r)), oW = !'#GE'.includes(g.at(c - 1, r));
      const k = oS + oN + oE + oW;
      if (!k) continue;
      const face = k === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      if (out === null) continue;
      n++;
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      const cells = [[c, r]];
      if (/^Wall2/.test(out)) cells.push([c + side[face][0], r + side[face][1]]);
      cells.forEach(([x, y]) => { const key = x + ',' + y; assert.ok(!cover.has(key), name + ' cell covered twice ' + key); cover.set(key, out); });
    }
    assert.ok(n > 120, name + ' wall modules ' + n);
  });
});

test('kit pieces on the GLB: hedges along their line, the rose arch and the bridge across their paths, stairs the robots climb, glow companions, budgets', () => {
  const G = glb('fps-kit-mossgarden.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const cols = (piece, walk) => {
    const node = G.nodes.find((n) => n.name === 'KIT_MOSSGARDEN_' + piece);
    assert.ok(node, piece);
    return (node.children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  };
  // link runs (no turn): the full hedge module runs along glTF Z (Blender Y), the half reaches from the post toward +Z
  for (const k of ['Box', 'Mid', 'Yew']) {
    const [ff] = cols(k + 'Full');
    assert.ok(Math.abs(ff.s[2] - 0.5) < 0.01 && ff.s[0] < 0.5, k + 'Full long axis on Z ' + JSON.stringify(ff.s));
    const [fh] = cols(k + 'Half');
    assert.ok(fh.t[2] > 0.2 && fh.t[2] + fh.s[2] <= 0.51, k + 'Half toward +Z ' + JSON.stringify(fh));
    assert.ok(!TH.symbols[{ Box: 'l', Mid: 'm', Yew: 'H' }[k]].turn);
  }
  // the rose arch [4, 1] spans X (its posts at both ends of X), the bridge [3, 5] carries its walk along Z
  const ra = cols('RoseArch');
  assert.ok(ra.every((b) => Math.abs(b.t[0]) > 1.3), 'rose arch posts at the ends of X');
  const bw = cols('Bridge', true);
  const crown = bw.find((b) => Math.abs(b.t[1] + b.s[1] - 0.9) < 0.01 && b.s[2] > 1.4);
  assert.ok(crown && crown.s[0] < 1.2, 'bridge crown along Z ' + JSON.stringify(crown));
  // steps: every walkable step rises at most 0.185 m over the one below on 0.25 m treads (robots climb 0.4 m per 0.5 m
  // nav cell), from the ground up to the deck
  const climb = (piece, top, axis, minW) => {
    const st = cols(piece, true).map((b) => ({ u: b.t[axis], top: b.t[1] + b.s[1], w: b.s[axis === 0 ? 2 : 0], d: b.s[axis] * 2 }))
      .filter((b) => Math.abs(b.d - 0.25) < 0.01).sort((a, b) => a.top - b.top);
    assert.ok(st.length >= 4, piece + ' steps ' + st.length);
    for (let i = 1; i < st.length; i++) {
      assert.ok(st[i].top - st[i - 1].top > 0.175 && st[i].top - st[i - 1].top < 0.185, piece + ' rise ' + i);
      assert.ok(Math.abs(Math.abs(st[i].u - st[i - 1].u) - 0.25) < 0.01, piece + ' tread ' + i);
    }
    assert.ok(Math.abs(st[st.length - 1].top - top) < 0.01, piece + ' reaches ' + top);
    assert.ok(st.every((s) => s.w >= minW), piece + ' stair wide enough for the nav grid');
  };
  climb('TerraceStair', 2.34, 2, 2.0);
  climb('TerraceStairS', 2.34, 2, 1.0);
  // the stair's top landing stands at the terrace height, in the ring row (toward glTF -Z = Blender +Y)
  assert.ok(cols('TerraceStair', true).some((b) => Math.abs(b.t[1] + b.s[1] - 2.34) < 0.01 && b.t[2] < -1.9), 'grand stair landing');
  for (const k of ['TerraceWall', 'TerraceWall_P', 'TerraceBack_A']) assert.ok(cols(k, true).some((b) => Math.abs(b.t[1] + b.s[1] - 2.34) < 0.01 && b.s[0] >= 0.49), k + ' walk top');
  // balustrades stand on the garden side (glTF +Z = Blender -Y is the front, toward the terrace)
  assert.ok(cols('TerraceWall').some((b) => b.t[1] > 2.34 && b.t[2] < -0.1), 'balustrade on the garden side');
  for (const g of Object.values(TH.glow)) assert.ok(names.has('KIT_MOSSGARDEN_' + g.piece), g.piece);
});
