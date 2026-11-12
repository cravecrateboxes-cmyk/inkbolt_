// Scoops & Cream theme (kit-icecream): level plan and waves (2 zones, elite targets), the two zones (size, gates,
// layers, symbols, prefab tiling and facing, spawns, pickups, one landmark each), the wall chooser (every piece in the
// kit, the logo run, the dock bay), runs and spans modelled along their line of cells (belts, glass, panels, rails,
// counters, doors: checked on the GLB's collision boxes), the paint jobs, glow companions.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/icecream.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.icecream;
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
const plan = IB.LEVEL_PLANS.icecream;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const STAND = '.SahPEGdJT';
const ART = { icecream_1: '123*[](){}!^', icecream_2: '!^?`&@$_,"~' };
const RAISED = { icecream_1: [1.2, '.wltf'], icecream_2: [3.5, '.urot4'] };

test('icecream theme: kit-icecream, indoor 7 m ceiling, two zones of waves (bombers at most 2 a wave, the first wave clean of elites)', () => {
  assert.equal(TH.family, 'kit-icecream');
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, 7);
  assert.equal(TH.wall.height, 7);
  assert.equal(plan.zones.length, 2);
  assert.ok(plan.zones[1].floor && plan.zones[1].floor.color, 'the creamery paints its own floor');
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader', 'mech', 'hawk', 'grenadier'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 39): each zone averages 64-65.5 soldiers and 40-41.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.icecream;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  const avgS = (sold[0] + sold[1]) / 2, avgB = (blad[0] + blad[1]) / 2;
  assert.ok(avgS >= 64 && avgS <= 65.5, 'soldiers ' + avgS);
  assert.ok(avgB >= 40 && avgB <= 41.5, 'bladers ' + avgB);
  p.zones.forEach((z) => z.waves.forEach((w) => {
    const tot = w.reduce((a, e) => a + e[1], 0), el = w.filter(([t]) => /soldier|grenadier|blader/.test(t)).reduce((a, e) => a + e[1], 0);
    assert.ok(el <= tot / 2, 'elites ' + el + ' of ' + tot);
  }));
  assert.ok(!p.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

const SIZES = { icecream_1: [72, 60], icecream_2: [70, 58] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, symbols, prefab tiling and facing, spawns, pickups, one landmark', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    const [ry, rset] = RAISED[name];
    assert.deepEqual(g.layers.map((L) => L.y), [0.01, ry, 7]);
    const [F, Dk, Ce] = g.layers;
    // floor layer: tiles and marks off the walls, art codes only on wall cells (and never a symbol)
    F.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.') return;
      if (g.at(c, r) === '#') { assert.ok(ART[name].includes(ch), name + ' art code ' + ch + ' at ' + c + ',' + r); assert.ok(!TH.symbols[ch], 'art ' + ch + ' is a symbol'); }
      else assert.ok(":;-'+".includes(ch), name + ' floor mark ' + ch + ' at ' + c + ',' + r);
    }));
    Ce.rows.forEach((row) => [...row].forEach((ch) => assert.ok('.56789'.includes(ch), name + ' ceiling ' + ch)));
    Dk.rows.forEach((row) => [...row].forEach((ch) => assert.ok(rset.includes(ch), name + ' raised layer ' + ch)));
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
    // the steps and the stair rise north onto their raised layer: the row beyond the top end is deck, the row
    // below the low end is open floor
    for (const ch of 'TN') rects(g, ch).forEach((R) => {
      for (let c = R.c; c < R.c + R.w; c++) {
        assert.ok(Dk.at(c, R.r - 1) !== '.' && Dk.at(c, R.r - 1) !== '#', name + ' ' + ch + ' top meets the deck at ' + c);
        assert.ok(STAND.includes(g.at(c, R.r + R.h)), name + ' ' + ch + ' foot open at ' + c);
        assert.ok(!'lr'.includes(Dk.at(c, R.r - 1)), name + ' no rail across the top of ' + ch);
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
      assert.equal(Dk.at(c, r), '.', name + ' spawn under the raised layer');
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    // the terrace is a solid slab: nothing to pick up buried under it (the mezzanine has open floor under it)
    if (name === 'icecream_1') for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if ('ah'.includes(g.at(c, r)) || (g.at(c, r) !== '.' && g.at(c, r) !== '#' && !'TE'.includes(g.at(c, r)))) assert.equal(Dk.at(c, r), '.', name + ' ' + g.at(c, r) + ' under the terrace at ' + c + ',' + r);
    assert.equal(rects(g, 'L').length + rects(Dk, 'o').length, 1, name + ' landmark');
  });
}

test('wall chooser: every exposed wall cell gets a kit piece (the dock bay: the centre module, empty side cells), finishes per zone, the logo run', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  for (const { name, g } of maps) {
    const solid = (c, r) => '#GE'.includes(g.at(c, r));
    const style = new Set(), logo = [];
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r);
      const nOpen = oS + oN + oE + oW;
      const exposed = nOpen > 0 || [[1, 1], [1, -1], [-1, 1], [-1, -1]].some(([x, y]) => !solid(c + x, r + y));
      if (!exposed) continue;
      const face = nOpen === 0 ? 'none' : nOpen === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      const code = g.layers[0].at(c, r);
      if (out === null) { assert.equal(code, '_', name + ' empty wall cell ' + c + ',' + r); continue; }
      assert.ok(all.has(out), name + ' chooser piece ' + out);
      style.add(out.replace(/^Corner/, 'W').charAt(1));
      if (/Logo/.test(out)) logo.push(out);
      if (code === '$') assert.deepEqual([g.layers[0].at(c - 1, r), g.layers[0].at(c + 1, r)], ['_', '_'], name + ' dock bay');
    }
    assert.ok(style.has(name === 'icecream_1' ? 'P' : 'K'), name + ' finish');
    if (name === 'icecream_1') assert.deepEqual(logo, Array.from({ length: 10 }, (_, k) => 'WP_Logo' + k), 'the logo reads left to right');
  }
});

test('runs and spans are modelled along their line of cells (collision boxes in the GLB: long axis on the run)', () => {
  const G = glb('fps-kit-icecream.glb');
  const cols = (piece) => {
    const node = G.nodes.find((n) => n.name === 'KIT_ICECREAM_' + piece);
    assert.ok(node, piece);
    return (node.children || []).map((i) => G.nodes[i]).filter((n) => /_W?COL\d+$/.test(n.name));
  };
  const extent = (piece) => {   // the union of a piece's boxes: [x0, x1, z0, z1] (glTF axes)
    const e = [Infinity, -Infinity, Infinity, -Infinity];
    cols(piece).forEach((n) => {
      const t = n.translation || [0, 0, 0], sc = n.scale;
      e[0] = Math.min(e[0], t[0] - sc[0]); e[1] = Math.max(e[1], t[0] + sc[0]); e[2] = Math.min(e[2], t[2] - sc[2]); e[3] = Math.max(e[3], t[2] + sc[2]);
    });
    return e;
  };
  // link runs (no turn): full modules along glTF Z (Blender Y), so a north-south run of cells gets yaw 0
  for (const [p, ch] of [['BeltFull', 'q'], ['VGlassFull', 'e'], ['TRailFull', 'l'], ['PanFull', 'i'], ['RailFull', 'r']]) {
    const s = cols(p)[0].scale;
    assert.ok(s[2] > 4 * s[0], p + ' long axis on Z ' + JSON.stringify(s));
    assert.ok(!TH.symbols[ch].turn, p + ' needs no turn');
    assert.equal(TH.symbols[ch].full, p);
  }
  // spans (doors in a wall line) and prefab runs: long axis on X (the w of [w, d])
  for (const p of ['VDoor', 'FreezerDoor', 'Dip_A', 'Dip_B', 'Sundae', 'Waffle', 'ShakeBar', 'WindowBar', 'BlastFreezer', 'Lockers', 'Sink',
    'FreezerShelf', 'Cart', 'Sofa', 'BackBar_A', 'SoftServe', 'CakeFreezer', 'Landmark_Party', 'PrepTable_A', 'PlanterBox', 'Line_A', 'Line_B']) {
    const e = extent(p);
    assert.ok(e[1] - e[0] > e[3] - e[2], p + ' long axis on X ' + JSON.stringify(e));
  }
  // [w, d] with d > w: long axis on Z
  for (const p of ['Booth', 'Stair', 'Ctr_End']) {
    const e = extent(p);
    assert.ok(e[3] - e[2] > e[1] - e[0], p + ' long axis on Z ' + JSON.stringify(e));
  }
  assert.equal(TH.symbols.d.orient, 'span');
  assert.equal(TH.symbols.J.orient, 'span');
  // walkable steps: the terrace steps and the stair carry walk boxes
  for (const p of ['Steps', 'Stair']) assert.ok(cols(p).some((n) => /_WCOL\d+$/.test(n.name)), p + ' walkable');
});

test('paint jobs and glow companions: cells match the palette, every glow piece is in the kit', () => {
  const src = fs.readFileSync(path.join(__dirname, '../../blender/ic_base.py'), 'utf8');
  const pal = [...src.slice(src.indexOf('PALETTES[FAM]')).matchAll(/\('(\w+)', '#[0-9A-Fa-f]{6}'\)/g)].map((m) => m[1]);
  const cell = (n) => pal.indexOf(n) + 8;
  assert.deepEqual(TH.symbols.D.paint.from, [cell('wallP')]);
  assert.deepEqual(TH.symbols.B.paint.from, [cell('pinkD'), cell('wallP')]);
  assert.deepEqual(TH.symbols.s.paint.from, [cell('lilac')]);
  assert.deepEqual(TH.symbols.f.paint.from, [cell('mintD'), cell('wallM')]);
  const pastel = ['wallP', 'wallC', 'wallM', 'pinkD', 'mintD', 'cherry', 'lemon', 'sky', 'lilac', 'orange', 'glassL', 'peach'].map(cell);
  for (const ch of 'DBsftgn') TH.symbols[ch].paint.to.forEach((job) => job.forEach((c) => assert.ok(pastel.includes(c), ch + ' paint cell ' + c)));
  const all = new Set(TH.allPieces());
  Object.values(TH.glow).forEach((g) => [].concat(g).forEach((d) => assert.ok(all.has(d.piece), d.piece)));
  const names = new Set(glb('fps-kit-icecream.glb').nodes.map((n) => n.name));
  for (const n of all) assert.ok(names.has('KIT_ICECREAM_' + n), 'kit piece ' + n);
});
