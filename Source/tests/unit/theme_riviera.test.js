// Grand Hotel Riviera theme (kit-riviera): level plan and waves (2 zones, elite targets for level 44), the two zones
// (size, gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, the gallery and its balustrades, the
// roof garden's deck over the podium, the stairs that land on them, the pools on the cliff edge), the wall chooser (the
// ground floor's panelled walls and sea windows, the suites, doorways; the terrace's facades, the podium, the sea edge
// and the infinity edge, gaps for the portals), and the kit pieces checked on the GLBs (every piece the theme places,
// its own and the borrowed ones): balustrade halves along Z, stairs the player and the robots climb, walkable landings,
// the pool copings robots step over, the parapet's collision over the roof.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/riviera.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.riviera;
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
const plan = IB.LEVEL_PLANS.riviera;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEG';
const DECK = 4.5;

test('riviera theme: kit-riviera with the hotel and venetian kits, a 9 m ceiling over the ground floor only, a level-wide backdrop, two zones of waves', () => {
  assert.equal(TH.family, 'kit-riviera');
  assert.deepEqual(TH.families, ['kit-hotel', 'kit-venetian']);
  assert.equal(TH.env.ceiling.height, 9);
  assert.equal(plan.zones[0].ceiling, 'plain');
  assert.equal(plan.zones[1].ceiling, false);
  assert.ok(TH.env.sky && TH.env.clouds);
  assert.equal(typeof TH.backdrop.build, 'function');
  assert.equal(TH.wall.height, 4.5);
  assert.ok(TH.wall.cols, 'taller wall modules carry their own collision above 4.5 m');
  assert.equal(TH.trail.height, 4.2);
  assert.equal(plan.zones.length, 2);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t), t);
  assert.ok(!RAW[0][0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 44): each zone holds 69-70.5 soldiers and 45-46.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.riviera;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 69 && s <= 70.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 45 && b <= 46.5, 'zone ' + (i + 1) + ' blade bots ' + b));
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

const SIZES = { riviera_1: [73, 63], riviera_2: [75, 68] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols, prefab tiling and facing, spawns, pickups, landmarks, decks and stairs', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const grids = [g].concat(g.layers);
    grids.forEach((G, li) => G.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '#' || ch === '.' || STAND.includes(ch) || TH.symbols[ch] || ch === 'n', name + ' grid ' + li + ' ' + ch + ' at ' + c + ',' + r))));
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
    const S = []; g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'S') S.push([c, r]); }));
    assert.ok(S.length >= 10 && S.length <= 14, 'spawns ' + S.length);
    const P = [...g.rows.join('')].filter((ch) => ch === 'P').length;
    assert.equal(P, 1);
    const at45 = g.layers.filter((L) => Math.abs(L.y - DECK) < 0.01);
    if (name === 'riviera_1') {
      assert.equal(rects(g, 'X').length, 1, 'the Imperial Staircase');
      assert.ok(rects(g, 'M').length === 1 && rects(g, 'N').length === 1 && rects(g, 'W').length === 1, 'three walk-in suites');
      assert.equal(rects(g, 'D').length, 1, 'the stage');
      assert.ok(rects(g, 'Y').length >= 6, 'rows of chairs');
      assert.ok(rects(g, 'd').length >= 5 && rects(g, 'u').length >= 4 && rects(g, 'B').length === 1, 'restaurant tables, the bar');
      assert.ok(rects(g, 'R').length === 1 && rects(g, 'F').length === 1, 'reception, flower table');
      // each suite's front is a wall line with a two-cell doorway in its middle
      for (const ch of 'MNW') {
        const R = rects(g, ch)[0];
        let n = 0; for (let c = R.c; c < R.c + R.w; c++) if (g.at(c, R.r + R.h) === 'n') n++;
        assert.equal(n, 2, ch + ' doorway');
      }
      // the gallery: one deck layer at 4.5 m, its edges closed by balustrades or the stair's own landings
      const G = at45[0];
      assert.ok(G && G.rows.join('').split('m').length > 300, 'gallery deck');
      const deckish = (c, r) => G.at(c, r) !== '.' && G.at(c, r) !== '#';
      const X = rects(g, 'X')[0];
      G.rows.forEach((row, r) => [...row].forEach((ch, c) => {
        if (ch !== 'm') return;
        [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dc, dr]) => {
          const c2 = c + dc, r2 = r + dr;
          if (deckish(c2, r2) || g.at(c2, r2) === '#' || g.at(c2, r2) === 'n') return;
          // an open deck edge meets the stair's top landing (cols 30 / 42 of the stair's front rows)
          assert.ok(g.at(c2, r2) === 'X' && r2 >= X.r + 6, 'open gallery edge at ' + c + ',' + r);
        });
      }));
      // a column under every column on the gallery's edge
      G.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'i') assert.equal(g.at(c, r), 'I', 'column under ' + c + ',' + r); }));
      assert.ok(g.layers.some((L) => L.y === 9 && L.rows.join('').includes('H')), 'the great chandelier');
    } else {
      assert.equal(rects(g, '%').length, 1, 'the infinity pool');
      const pool = rects(g, '%')[0];
      assert.ok(pool.c === 1 && pool.w === 12 && pool.h === 45, 'the infinity pool runs along the cliff edge ' + JSON.stringify(pool));
      assert.ok(rects(g, '&').length === 1 && rects(g, '$').length === 1, 'the spa pool, the pool bar');
      assert.equal(rects(g, '?').length, 2, 'two stairs into the podium');
      // the roof garden's deck over the podium's inner cells; every roof garden piece stands on it
      const D = at45.find((L) => L.rows.join('').includes('=')), F = at45.find((L) => !L.rows.join('').includes('='));
      assert.ok(D && F, 'deck and furniture layers');
      let deck = 0; D.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === '=') { deck++; assert.equal(g.at(c, r), '#', 'deck over the podium ' + c + ',' + r); } }));
      assert.ok(deck > 700, 'roof garden ' + deck);
      F.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch !== '.') assert.equal(D.at(c, r), '=', 'on the deck: ' + ch + ' at ' + c + ',' + r); }));
      // each stair's top lands on the deck: the cell past its upper end is a deck cell
      const st = rects(g, '?');
      const S1 = st.find((R) => R.w === 8), S2 = st.find((R) => R.h === 8);
      for (let r = S1.r; r < S1.r + S1.h; r++) assert.equal(D.at(S1.c + S1.w, r), '=', 'west stair head');
      for (let c = S2.c; c < S2.c + S2.w; c++) assert.equal(D.at(c, S2.r - 1), '=', 'south stair head');
      // nothing stands in front of the stairs' feet
      for (let r = S1.r; r < S1.r + S1.h; r++) assert.ok(STAND.includes(g.at(S1.c - 1, r)), 'west stair foot');
      for (let c = S2.c; c < S2.c + S2.w; c++) assert.ok(STAND.includes(g.at(c, S2.r + S2.h)), 'south stair foot');
    }
  });
}

test('wall chooser: panelled walls, sea windows, suites and doorways inside; facades, the podium, the sea edge outside', () => {
  const all = new Set(TH.allPieces().concat(TH.borrowed()));
  const hash = () => 0.5;
  maps.forEach(({ name, g }, zi) => {
    let n = 0;
    const seen = new Set();
    const wl = (ch) => ch === '#' || ch === 'n' || ch === 'G' || ch === 'E';
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      const ch = g.at(c, r);
      if (ch !== '#' && ch !== 'n') continue;
      const oS = !wl(g.at(c, r + 1)), oN = !wl(g.at(c, r - 1)), oE = !wl(g.at(c + 1, r)), oW = !wl(g.at(c - 1, r));
      const k = oS + oN + oE + oW;
      if (!k) continue;
      const face = k === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const horiz = wl(g.at(c - 1, r)) || wl(g.at(c + 1, r));
      const out = TH.wall.choose(c, r, horiz, false, hash, g, face);
      if (out === null) continue;
      n++; seen.add(out.replace(/^KIT_HOTEL_/, '').replace(/_.*/, ''));
      assert.ok(all.has(out), name + ' chooser piece ' + out + ' at ' + c + ',' + r);
      const corner = (c === 0 || c === g.w - 1) && (r === 0 || r === g.h - 1);
      if (ch === 'n') assert.ok(/^Door_[LMR]$/.test(out), 'doorway ' + out);
      if (zi === 1 && c === 0 && !corner) assert.ok(/^(InfEdge|SeaBal(_L)?)$/.test(out), 'the sea edge ' + out);
      if (zi === 1 && c === 0 && g.at(1, r) === '%') assert.equal(out, 'InfEdge', 'the vanishing edge beside the pool');
      if (zi === 1 && (r === 0 || r === g.h - 1) && !corner) assert.ok(/^F_/.test(out), 'a facade ' + out);
      if (zi === 0 && c === 0 && r >= 21 && r < g.h - 1) assert.ok(/^(SW_[ABP]|Core)$/.test(out), 'the restaurant\'s sea windows ' + out);
    }
    assert.ok(n > 250, name + ' wall modules ' + n);
    if (zi === 0) for (const k of ['IW', 'SW', 'SF', 'Door', 'SuiteDoor', 'KitDoor', 'Lift', 'SuiteWin']) assert.ok(seen.has(k), name + ' uses ' + k);
    else for (const k of ['F', 'PW', 'SeaBal', 'InfEdge']) assert.ok(seen.has(k), name + ' uses ' + k);
  });
  // a window half's partner: SW_A has its arch centre on its +X edge (on the west wall, facing east, local +X is
  // north), so walking south along the restaurant's windows every A follows its B
  const g = maps[0].g;
  let prev = null, pairs = 0;
  for (let r = 1; r < g.h - 1; r++) {
    const out = TH.wall.choose(0, r, false, false, () => 0.5, g, 'E');
    if (out === 'SW_A') { assert.equal(prev, 'SW_B', 'pair at ' + r); pairs++; }
    prev = out;
  }
  assert.ok(pairs >= 12, 'window pairs ' + pairs);
});

test('kit pieces on the GLBs: every placed piece exists, balustrade halves along Z, stairs the robots climb, walkable copings and landings', () => {
  const G = glb('fps-kit-riviera.glb'), GH = glb('fps-kit-hotel.glb'), GV = glb('fps-kit-venetian.glb');
  const names = new Set(G.nodes.concat(GH.nodes, GV.nodes).map((n) => n.name));
  const own = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(own.has(IB.themePiece(TH, p)), 'missing ' + p);
  for (const p of TH.borrowed()) assert.ok(names.has(p) && /^KIT_(HOTEL|VENETIAN)_/.test(p), 'missing borrowed ' + p);
  for (const p of ['Hatch', TH.gate.frame, TH.gate.shutter, TH.trail.wall, TH.trail.end].concat(TH.trail.variants)) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const node = (piece) => { const nd = G.nodes.find((n) => n.name === 'KIT_RIVIERA_' + piece); assert.ok(nd, piece); return nd; };
  const cols = (piece, walk) => (node(piece).children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  // the gallery's balustrade (links, no turn): the full module along glTF Z, the half from the centre toward +Z
  const [f] = cols('GRailFull'), [hf] = cols('GRail');
  assert.ok(f.s[2] >= 0.49 && f.s[2] > 3 * f.s[0], 'GRailFull long axis on Z ' + JSON.stringify(f.s));
  assert.ok(hf.t[2] > 0.2 && hf.t[2] + hf.s[2] <= 0.51, 'GRail toward +Z ' + JSON.stringify(hf));
  assert.ok(!TH.symbols.r.turn && TH.symbols.r.links === 'ri');
  // stairs: every walkable step rises at most 0.18 m over the one below (<= 0.36 m a 0.5 m nav cell)
  const steps = (piece) => cols(piece, true).map((b) => ({ top: +(b.t[1] + b.s[1]).toFixed(3), wx: b.s[0] * 2, wz: b.s[2] * 2 }));
  const climb = (piece, top, minSteps, maxRise) => {
    const tops = [...new Set(steps(piece).map((s) => s.top))].sort((a, b) => a - b);
    assert.ok(tops.length >= minSteps, piece + ' steps ' + tops.length);
    for (let i = 1; i < tops.length; i++) assert.ok(tops[i] - tops[i - 1] <= maxRise + 0.002, piece + ' rise ' + (tops[i] - tops[i - 1]));
    assert.ok(Math.abs(tops[tops.length - 1] - top) < 0.01, piece + ' reaches ' + top);
    assert.ok(tops[0] <= maxRise + 0.002, piece + ' first step');
  };
  climb('Landmark_Stair', DECK, 25, 0.18);
  climb('RoofStair', DECK, 28, 0.161);
  // the landing at 2.16 m and the two top landings at 4.5 m are walkable over a real area
  const area = (piece, h) => steps(piece).filter((s) => Math.abs(s.top - h) < 0.01).reduce((a, s) => a + s.wx * s.wz, 0);
  assert.ok(area('Landmark_Stair', 2.16) > 35, 'stair landing');
  assert.ok(area('Landmark_Stair', DECK) > 25, 'top landings');
  // the pools' copings are walkable 0.3 m steps (robots and the player wade in); the parapet stands over the roof
  for (const p of ['Landmark_Pool_S', 'Landmark_Pool_M', 'Landmark_Pool_N', 'SpaPool']) {
    const c = cols(p, true);
    assert.ok(c.length >= 1 && c.every((b) => b.t[1] + b.s[1] <= 0.62 + 0.001), p + ' copings ' + c.length);
  }
  const par = cols('PW_Win').filter((b) => b.t[1] - b.s[1] >= DECK - 0.01);
  assert.ok(par.length === 1 && par[0].t[1] + par[0].s[1] >= DECK + 1.0, 'parapet collision over the roof');
  // tall modules stop the player above the 4.5 m wall box (the gallery level)
  for (const p of ['IW_Plain', 'SF_Plain', 'Door_M', 'Core']) assert.ok(cols(p).some((b) => b.t[1] - b.s[1] <= 4.51 && b.t[1] + b.s[1] >= 8.99), p + ' upper collision');
  // the kit's GLB stays within the size budget
  assert.ok(fs.statSync(path.join(__dirname, '../../assets/fps-kit-riviera.glb')).size <= 2.5 * 1024 * 1024, 'kit-riviera GLB <= 2.5 MB');
});
