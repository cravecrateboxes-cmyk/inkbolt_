// Rustmoor Salvage theme (kit-scrapyard): level plan and waves (two zones, elites, no elites in the first wave), the
// two zones (size, gates, layer 0 and what may stand in it, symbols, prefab tiling and facing, spawns, pickups), the
// wall chooser (the Stacks' banks in zone 1, the graveyard's in zone 2, wall codes honoured, every piece in the kit),
// the glow and blink companions, run pieces along local X, the walkable decks in fps-kit-scrapyard.glb, the night env.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/scrapyard.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.scrapyard;
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
function glb(name) {
  const d = fs.readFileSync(path.join(__dirname, '../../assets/' + name));
  return JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
}
const plan = IB.LEVEL_PLANS.scrapyard;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEG';
const LAYER0 = '.wu12345679';

test('scrapyard theme: kit-scrapyard at night under an open sky, two zones, hard waves with elites from the second wave', () => {
  assert.equal(TH.family, 'kit-scrapyard');
  assert.deepEqual(TH.families, ['kit-parking']);
  assert.ok(Array.isArray(TH.env.sky) && TH.env.sky.length === 2, 'a night sky');
  for (const c of TH.env.sky.concat([TH.env.fog.color])) {
    const n = parseInt(c.slice(1), 16), lum = 0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255);
    assert.ok(lum < 60, 'dark night colour ' + c);
  }
  assert.equal(TH.env.ceiling, null);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z, zi) => z.waves.forEach((w, wi) => w.forEach(([t, n]) => {
    types.add(t);
    if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave');
    if (zi === 0 && wi === 0) assert.ok(t !== 'soldier' && t !== 'blader', 'the first wave of zone 1 has no elites');
  })));
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
});

for (const [zi, { name, g }] of maps.entries()) {
  test('zone ' + name + ': size, gates, layer 0, symbols, prefab tiling and facing, spawns, pickups', () => {
    assert.ok(g.w >= 64 && g.w <= 72 && g.h >= 66 && g.h <= 74, name + ' ' + g.w + 'x' + g.h);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.ok('#GE'.includes(g.at(0, r))); assert.ok('#GE'.includes(g.at(g.w - 1, r))); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    assert.deepEqual(g.layers.map((L) => L.y), [0]);
    // layer 0: the weighbridge and oil stains on open floor, digits (wall codes) only on wall cells
    g.layers[0].rows.forEach((row, r) => [...row].forEach((ch, c) => {
      assert.ok(LAYER0.includes(ch), name + ' @0 ' + ch + ' at ' + c + ',' + r);
      if (ch === 'w' || ch === 'u') assert.ok('.SPah'.includes(g.at(c, r)), name + ' ' + ch + ' on open floor ' + c + ',' + r);
      if (/\d/.test(ch)) assert.equal(g.at(c, r), '#', name + ' wall code on a wall ' + c + ',' + r);
    }));
    assert.equal(g.layers[0].at(0, 0) === '9', zi === 1, 'the graveyard marker on zone 2 only');
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
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++; }));
    assert.equal(P.length, 1);
    for (const dc of [-2, -1, 1, 2]) assert.ok(STAND.includes(g.at(P[0][0] + dc, P[0][1] - 4)), 'weapon stand cell');
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'S') return;
      S++;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P');
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    // one landmark per zone; floodlight towers far enough apart that their pools of light never overlap
    assert.equal(rects(g, zi === 0 ? 'Z' : 'I').length, 1, 'landmark');
    const T = rects(g, 'T');
    assert.ok(T.length >= 4, 'floodlight towers ' + T.length);
    for (let i = 0; i < T.length; i++) for (let j = 0; j < i; j++) assert.ok(Math.hypot(T[i].c - T[j].c, T[i].r - T[j].r) >= 13, 'tower pools overlap');
  });
}

test('wall chooser: the Stacks\' banks in zone 1, the graveyard\'s in zone 2, codes honoured, every piece in the kit', () => {
  const all = new Set(TH.allPieces());
  const hash = (a, b) => { const x = Math.sin(a * 91.7 + b * 17.3) * 1e4; return x - Math.floor(x); };
  const CODE = [{ 1: 'Bank_Sign1', 2: 'Bank_Sign2', 3: 'Bank_Car', 4: 'Bank_Tyres' }, { 2: 'Grave_Sign', 5: 'Grave_Leak', 6: 'Grave_Plate', 7: 'Grave_Finger' }];
  for (const [zi, { name, g }] of maps.entries()) {
    const solid = (c, r) => '#GE'.includes(g.at(c, r));
    let coded = 0, lamps = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r);
      const n = oS + oN + oE + oW;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const exposed = n > 0 || [[1, 1], [1, -1], [-1, 1], [-1, -1]].some(([a, b]) => !solid(c + a, r + b));
      if (!exposed) continue;
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      assert.ok(all.has(out), name + ' chooser piece ' + out + ' at ' + c + ',' + r);
      assert.ok(zi === 0 ? /^Bank_/.test(out) : /^Grave_/.test(out), name + ' ' + out + ' in the wrong zone');
      if (/Lamp/.test(out)) { lamps++; assert.ok(out.endsWith(face), name + ' lamp facing ' + out + ' ' + face); }
      const code = g.layers[0].at(c, r);
      if (CODE[zi][code] && 'SNEW'.includes(face) && face.length === 1) { coded++; assert.equal(out, CODE[zi][code], name + ' code at ' + c + ',' + r); }
    }
    assert.ok(coded >= 10, name + ' wall codes ' + coded);
    assert.ok(lamps >= 8, name + ' wall lamps ' + lamps);
  }
});

test('glow and blink companions: every listed one is in fps-kit-scrapyard.glb, every _Glow / _Blink piece there is listed', () => {
  const nodes = new Set(glb('fps-kit-scrapyard.glb').nodes.map((n) => n.name));
  const listed = new Set();
  for (const [k, defs] of Object.entries(TH.glow)) {
    assert.ok(nodes.has(TH.prefix + k), 'piece ' + k);
    for (const d of [].concat(defs)) {
      assert.ok(nodes.has(TH.prefix + d.piece), 'companion ' + d.piece);
      if (/_Blink$/.test(d.piece)) assert.equal(d.groups, 2, d.piece + ' blinks in two phase groups');
      listed.add(TH.prefix + d.piece);
    }
  }
  for (const n of nodes) if (/_(Glow|Blink)$/.test(n) && !/Backdrop/.test(n)) assert.ok(listed.has(n), n + ' not listed in theme.glow');
});

test('run pieces are modelled along local X (the run placer turns X onto the run): the jersey barriers', () => {
  const G = glb('fps-kit-scrapyard.glb');
  const runs = Object.entries(TH.symbols).filter(([, d]) => d.rotate === 'run').flatMap(([, d]) => d.pieces);
  assert.ok(runs.length >= 2, runs.join());
  for (const n of runs) {
    const node = G.nodes.find((x) => x.name === TH.prefix + n && x.mesh !== undefined);
    assert.ok(node, n);
    const acc = G.accessors[G.meshes[node.mesh].primitives[0].attributes.POSITION];
    const ex = acc.max[0] - acc.min[0], ez = acc.max[2] - acc.min[2];
    assert.ok(ex >= 0.98 && ex <= 1.12 && ex > ez + 0.3, n + ' x ' + ex.toFixed(2) + ' z ' + ez.toFixed(2));
  }
});

test('walkable decks: the office roof at 3.15 m, the baler platform at 2.4 m, the ribcage decks at 3.0 / 5.4 m, the scaffold at 3 / 6 m; rises <= 0.35 m', () => {
  const G = glb('fps-kit-scrapyard.glb');
  const byPiece = {};
  G.nodes.forEach((n) => {
    const m = /^KIT_SCRAPYARD_(.+)_WCOL\d+$/.exec(n.name);
    if (!m) return;
    const t = n.translation || [0, 0, 0], s = n.scale || [1, 1, 1];
    (byPiece[m[1]] = byPiece[m[1]] || []).push(+(t[1] + s[1]).toFixed(3));
  });
  const want = { Landmark_Office: [3.15], Landmark_Baler: [2.4], Landmark_Ribs: [3.0, 5.4], Scaffold: [3.0, 6.0] };
  for (const [p, decks] of Object.entries(want)) {
    const tops = [...new Set(byPiece[p] || [])].sort((a, b) => a - b);
    assert.ok(tops.length > 3, p + ' walkable boxes');
    for (const dz of decks) assert.ok(tops.some((t) => Math.abs(t - dz) < 0.01), p + ' deck at ' + dz + ': ' + tops.join(' '));
    assert.ok(Math.abs(tops[tops.length - 1] - decks[decks.length - 1]) < 0.01, p + ' top deck ' + tops[tops.length - 1]);
    for (let i = 1; i < tops.length; i++) assert.ok(tops[i] - tops[i - 1] <= 0.35 + 1e-3, p + ' rise ' + tops[i - 1] + ' -> ' + tops[i]);
    assert.ok(tops[0] <= 0.35 + 1e-3, p + ' first step ' + tops[0]);
  }
});
