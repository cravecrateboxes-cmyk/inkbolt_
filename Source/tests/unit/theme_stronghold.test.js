// Fort Highwatch theme (kit-stronghold): level plan and waves (2 zones, elite targets for level 33), the two zones
// (size, gates and their alignment with the massif's face line, layers, symbols, prefab tiling and facing, terraces and
// their switchbacks, decks, rails, the cavern roof, the terrace doorways, spawns, pickups, landmarks), the wall chooser
// (2 m modules never reach past their run), and the kit pieces checked on the GLB: run pieces along their line of
// cells, ramps and stairs rising north in steps robots and the player can climb.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/stronghold.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.stronghold;
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
const plan = IB.LEVEL_PLANS.stronghold;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const OPEN = '.tSahPEG';

test('stronghold theme: kit-stronghold, sunset sky, tunnel ceiling for the trails only, two zones of waves', () => {
  assert.equal(TH.family, 'kit-stronghold');
  assert.ok(TH.env.sky && TH.env.sunColor && TH.env.far >= 2000 && TH.env.fog.tierScale);
  assert.equal(TH.env.ceiling.height, TH.trail.height);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(plan.zones.length, 2);
  plan.zones.forEach((z) => assert.equal(z.ceiling, false));
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t), t);
  assert.ok(!RAW[0][0].some(([t]) => /soldier|blader/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 33): each zone averages 57-58.5 soldiers and 33-34.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.stronghold;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  const avgS = (sold[0] + sold[1]) / 2, avgB = (blad[0] + blad[1]) / 2;
  assert.ok(avgS >= 57 && avgS <= 58.5, 'soldiers ' + avgS);
  assert.ok(avgB >= 33 && avgB <= 34.5, 'bladers ' + avgB);
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

const SIZES = { stronghold_1: [72, 64], stronghold_2: [75, 64] };
const LAYERS = { stronghold_1: [0, 1.8, 1.8, 3.6, 3.6, 5.4, 5.4, 7.2, 7.2], stronghold_2: [0, 2.4, 2.4, 12] };
// ramps / stairs: symbol -> [rise direction (dc, dr), base height of the piece's top end above its layer]
const RISE = { '>': [1, 0], '<': [-1, 0], '^': [0, -1], 'u': [0, -1], 'v': [0, 1] };

test('the two zones line up with the massif: the zone 2 terrace face (column 14) continues the zone 1 spur (column 20)', () => {
  const g1 = maps[0].g, g2 = maps[1].g;
  const gc = g1.rows[0].indexOf('GGG') + 1.5, ec = g2.rows[g2.h - 1].indexOf('EEE') + 1.5;
  assert.equal(gc - ec, 6, 'zone 2 sits 6 m east of zone 1');
  assert.equal(g1.at(19, 0), '}'); assert.equal(g1.at(20, 0), '#');
  for (let r = 0; r < g2.h; r++) assert.ok('#n'.includes(g2.at(14, r)), 'terrace face ' + r);
  assert.equal(rects(g2, 'n').length, 4, 'four doorways onto the terrace');
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, symbols, prefab tiling and facing, decks, ramps, rails, spawns, pickups, landmarks', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    assert.deepEqual(g.layers.map((L) => L.y), LAYERS[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(OPEN.includes(g.at(c, r)), 'exit approach');
    for (let r = 1; r < g.h - 1; r++) assert.equal(g.at(0, r), '{', 'parapet on the west edge');
    const CODES = g.layers[0];
    CODES.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch !== '.') { assert.ok(/[0-9]/.test(ch), 'code ' + ch); assert.equal(g.at(c, r), '#', 'code on a wall'); } }));
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok('#nt'.includes(ch) || OPEN.includes(ch) || TH.symbols[ch], name + ' plan ' + ch + ' at ' + c + ',' + r)));
    for (const G of [g, ...g.layers.slice(1)]) {
      G.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '.' || TH.symbols[ch] || '#ntSahPEG'.includes(ch), name + ' ' + ch)));
      for (const [ch, d] of Object.entries(TH.symbols)) {
        if (!d.size) continue;
        rects(G, ch).forEach((R) => {
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
    }
    // decks: every layer prop stands on a deck of its own height (or of a lower solid terrace under it, zone 1); every
    // ramp / stair top lands on a deck one flight higher, whose landing cells have no rail
    const decks = {}, things = {};
    g.layers.slice(1).forEach((L) => { if (L.y === 12) return; const hasDeck = L.rows.some((row) => /[DUdm]/.test(row)); (hasDeck ? decks : things)[L.y] = L; });
    const deckAt = (y, c, r) => decks[y] && /[DUdm]/.test(decks[y].at(c, r));
    for (const y of Object.keys(things)) {
      const L = things[y];
      L.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch !== '.') assert.ok(deckAt(+y, c, r), name + ' ' + ch + ' at ' + c + ',' + r + ' off its deck (' + y + ')'); }));
    }
    const flights = [[g, 0]].concat(Object.keys(things).map((y) => [things[y], +y]));
    flights.forEach(([G, y0]) => {
      for (const [ch, [dc, dr]] of Object.entries(RISE)) rects(G, ch).forEach((R) => {
        const d = TH.symbols[ch], rise = /Long/.test(d.pieces[0]) ? 3.6 : /Stair/.test(d.pieces[0]) ? 2.4 : 1.8, top = y0 + (d.pieces[0] === 'RampHi' ? 3.6 : rise);
        const cells = dc === 0 ? [...Array(R.w)].map((_, i) => [R.c + i, dr < 0 ? R.r - 1 : R.r + R.h]) : [...Array(R.h)].map((_, i) => [dc > 0 ? R.c + R.w : R.c - 1, R.r + i]);
        cells.forEach(([c, r]) => {
          assert.ok(deckAt(top, c, r), name + ' ' + ch + ' top lands on a ' + top + ' deck at ' + c + ',' + r);
          assert.notEqual(things[top] && things[top].at(c, r), 'r', name + ' rail across a landing ' + c + ',' + r);
        });
      });
    });
    // rails only on deck edges
    for (const y of Object.keys(things)) things[y].rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'r') return;
      const D = decks[y], me = D.at(c, r);
      assert.ok([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([a, b]) => D.at(c + a, r + b) !== me), name + ' rail inside a deck ' + c + ',' + r);
    }));
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++; }));
    assert.equal(P.length, 1);
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'S') return;
      S++;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok('.SahP'.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P');
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    if (name === 'stronghold_1') {
      assert.equal(rects(g, 'H').length, 1, 'helipad');
      assert.equal(rects(g, 'B').length, 2, 'bastions at the gate');
      assert.ok(rects(things[7.2], 'R').length === 1, 'radome on terrace 2');
    } else {
      assert.equal(rects(g, '$').length, 1, 'the tactical table');
      assert.equal(rects(g, 'T').length, 1, 'the armoured truck');
      const roof = g.layers[3];
      for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) assert.equal(roof.at(c, r) === '_', c >= 15, 'roof over the halls only ' + c + ',' + r);
    }
  });
}

test('wall chooser: kit pieces for every exposed wall cell; a 2 m module always has its run cell next to it (left empty)', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  for (const { name, g } of maps) {
    let n = 0;
    const face = (c, r) => { const s = (cc, rr) => '#GEn'.includes(g.at(cc, rr)); const oS = !s(c, r + 1), oN = !s(c, r - 1), oE = !s(c + 1, r), oW = !s(c - 1, r), k = oS + oN + oE + oW; return k === 0 ? 'none' : k === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E')); };
    const STEP = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (!'#n'.includes(g.at(c, r))) continue;
      const F = face(c, r), out = TH.wall.choose(c, r, false, false, hash, g, F);
      if (out === null) continue;
      n++;
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      if (/2(_|$)/.test(out)) {
        const [dc, dr] = STEP[F];
        assert.equal(g.at(c + dc, r + dr), '#', name + ' 2 m module ' + out + ' at ' + c + ',' + r + ' runs past its wall');
        assert.equal(face(c + dc, r + dr), F, name + ' 2 m module ' + out + ' turns a corner at ' + c + ',' + r);
        assert.equal(TH.wall.choose(c + dc, r + dr, false, false, hash, g, F), null, name + ' cell after a 2 m module is left empty');
      }
    }
    assert.ok(n > 60, name + ' wall modules ' + n);
  }
});

test('kit pieces on the GLB: run pieces along their line, ramps and stairs rising north in climbable steps', () => {
  const G = glb('fps-kit-stronghold.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const cols = (piece, walk) => {
    const node = G.nodes.find((n) => n.name === 'KIT_STRONGHOLD_' + piece);
    assert.ok(node, piece);
    return (node.children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  };
  // link runs (rails, the cage fence): the full module runs along glTF Z, the half module from the centre toward +Z
  for (const [full, half] of [['RailFull', 'RailHalf'], ['FenceFull', 'FenceHalf']]) {
    const [f] = cols(full), [h] = cols(half);
    assert.ok(f.s[2] > 4 * f.s[0], full + ' long axis on Z ' + JSON.stringify(f.s));
    assert.ok(h.t[2] > 0.2 && h.t[2] + h.s[2] <= 0.51, half + ' toward +Z ' + JSON.stringify(h));
  }
  // rotate 'run' pieces (parapets, sandbag walls, jersey barriers) lie along X: the placer turns them for N-S runs
  for (const p of ['Parapet_A', 'Parapet_B', 'Parapet_C', 'Sandbags_A', 'Sandbags_B', 'Jersey']) {
    const [b] = cols(p);
    assert.ok(Math.abs(b.s[0] - 0.5) < 0.01 && b.s[2] < 0.35, p + ' along X ' + JSON.stringify(b.s));
    assert.equal(TH.symbols[{ Parapet_A: '{', Parapet_B: '{', Parapet_C: '{', Sandbags_A: '=', Sandbags_B: '=', Jersey: 'j' }[p]].rotate, 'run');
  }
  // [w, d] prefabs along X: ammo rack, gun rack, console, workbench, generator, video wall, blast door, mess table
  for (const [p, w] of [['AmmoRack_A', 2], ['GunRack', 0.95], ['Console', 0.98], ['Workbench', 0.95], ['Generator', 0.95], ['VideoWall', 2.95], ['BlastDoor', 4.0], ['MessTable', 1.4]]) {
    const b = cols(p).reduce((m, c) => (c.s[0] > m.s[0] ? c : m));
    assert.ok(Math.abs(b.s[0] - w) < 0.02 && b.s[2] < b.s[0], p + ' along X ' + JSON.stringify(b.s));
  }
  // footprints along Z: bunk, truck, jeep, bowser
  for (const p of ['Bunk', 'Landmark_Truck', 'Jeep', 'Bowser']) {
    const b = cols(p).reduce((m, c) => (c.s[2] > m.s[2] ? c : m));
    assert.ok(b.s[2] > b.s[0], p + ' along Z ' + JSON.stringify(b.s));
  }
  // ramps and stairs: walkable 0.5 m treads (the nav cell, deeper than the player's radius) from the south end (+Z)
  // to the north end (-Z), rising at most 0.2 m each
  for (const [p, n, z0, z1, L] of [['RampLo', 12, 0, 1.8, 6], ['RampHi', 12, 1.8, 3.6, 6], ['RampLong', 24, 0, 3.6, 12], ['Stair', 12, 0, 2.4, 6]]) {
    const st = cols(p, true).map((b) => ({ z: b.t[2], top: b.t[1] + b.s[1], bot: b.t[1] - b.s[1], w: b.s[0] })).sort((a, b) => b.z - a.z);
    assert.equal(st.length, n, p);
    assert.ok(Math.abs(st[st.length - 1].top - z1) < 0.01 && st[st.length - 1].z < -L / 2 + 0.5, p + ' top step at the north end');
    assert.ok(st[0].top - z0 <= 0.2 + 1e-6 && st[0].z > L / 2 - 0.5, p + ' first step at the south end');
    for (let i = 1; i < st.length; i++) {
      assert.ok(st[i].top - st[i - 1].top > 0 && st[i].top - st[i - 1].top <= 0.2 + 1e-6, p + ' step ' + i);
      assert.ok(Math.abs(st[i - 1].z - st[i].z - 0.5) < 0.01, p + ' tread ' + i);
    }
    assert.ok(st.every((s) => s.w > 0.8 && s.bot < 0.01), p + ' steps wide enough and solid to the floor');
  }
});
