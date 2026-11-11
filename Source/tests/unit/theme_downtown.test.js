// Downtown Standoff theme (kit-downtown): level plan and waves, the three zones (size, gates, paving layer, symbols,
// prefab tiling and facing, spawns, pickups), the walk-in shops (7 x 8 rooms behind a frontage with three doorway
// cells, the approach kept clear), the facade chooser (shop fronts, room walls, every piece in the kit), the
// kit-parking pieces the theme borrows (present in fps-kit-parking.glb) and their paint jobs.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/downtown.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.downtown;
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
const plan = IB.LEVEL_PLANS.downtown;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const ROOMS = '567890&$%@';
const FLOOR = '.-|~!zZ_:ox*=';
const STAND = '.SahPEG' + FLOOR;

test('downtown theme: kit-downtown with kit-parking, daylight sky, three zones of hard waves (bombers at most 2 a wave)', () => {
  assert.equal(TH.family, 'kit-downtown');
  assert.deepEqual(TH.families, ['kit-parking']);
  assert.ok(Array.isArray(TH.env.sky) && TH.env.ceiling === null);
  assert.equal(plan.zones.length, 3);
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  assert.ok(total >= 300, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, paving layer, symbols, prefab tiling and facing, spawns, pickups', () => {
    assert.ok(g.w === 64 && g.h === 56, name + ' ' + g.w + 'x' + g.h);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    assert.deepEqual(g.layers.map((L) => L.y), [0]);
    g.layers[0].rows.forEach((row, r) => [...row].forEach((ch, c) => {
      assert.ok('.,;ah'.includes(ch), name + ' @0 ' + ch + ' at ' + c + ',' + r);
      if ('ah'.includes(ch)) assert.ok(ROOMS.includes(g.at(c, r)), name + ' layer pickups lie in shops');
      if (',;'.includes(ch)) assert.ok(!'#n'.includes(g.at(c, r)) && !ROOMS.includes(g.at(c, r)), name + ' paving on open ground ' + c + ',' + r);
    }));
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(ch === '#' || ch === 'n' || STAND.includes(ch) || TH.symbols[ch], name + ' plan ' + ch + ' at ' + c + ',' + r)));
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
      });
    }
    const P = []; let S = 0, a = 0, h = 0;
    for (const G of [g, ...g.layers]) G.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++; }));
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

test('walk-in shops: ten different shops, 7 x 8 rooms, three doorway cells in the middle of the frontage, approach clear', () => {
  const seen = new Set();
  for (const { name, g } of maps) {
    let n = 0;
    for (const ch of ROOMS) rects(g, ch).forEach((R) => {
      n++; assert.ok(!seen.has(ch), ch + ' used twice'); seen.add(ch);
      assert.ok((R.w === 8 && R.h === 7) || (R.w === 7 && R.h === 8), name + ' room ' + ch + ' ' + JSON.stringify(R));
      // the frontage: the one side with doorway cells, three of them in the middle, the other cells building
      const sides = [
        { cells: [...Array(R.h).keys()].map((k) => [R.c - 1, R.r + k]), out: [-1, 0] },
        { cells: [...Array(R.h).keys()].map((k) => [R.c + R.w, R.r + k]), out: [1, 0] },
        { cells: [...Array(R.w).keys()].map((k) => [R.c + k, R.r - 1]), out: [0, -1] },
        { cells: [...Array(R.w).keys()].map((k) => [R.c + k, R.r + R.h]), out: [0, 1] }];
      const front = sides.filter((s) => s.cells.some(([c, r]) => g.at(c, r) === 'n'));
      assert.equal(front.length, 1, name + ' ' + ch + ' one frontage');
      const F = front[0], pat = F.cells.map(([c, r]) => g.at(c, r)).join('');
      assert.equal(pat, '##nnn##', name + ' ' + ch + ' frontage ' + pat);
      sides.filter((s) => s !== F).forEach((s) => s.cells.forEach(([c, r]) => assert.equal(g.at(c, r), '#', name + ' ' + ch + ' walled')));
      F.cells.filter(([c, r]) => g.at(c, r) === 'n').forEach(([c, r]) => {
        for (let k = 1; k <= 2; k++) assert.ok(STAND.includes(g.at(c + F.out[0] * k, r + F.out[1] * k)), name + ' ' + ch + ' doorway approach ' + (c + F.out[0] * k) + ',' + (r + F.out[1] * k));
      });
      // the room piece turns to the side with the fewest building cells: the frontage
      const share = sides.map((s) => s.cells.filter(([c, r]) => g.at(c, r) === '#').length / s.cells.length);
      assert.equal(Math.min(...share), share[sides.indexOf(F)]);
      assert.equal(share.filter((x) => x === share[sides.indexOf(F)]).length, 1);
    });
    assert.ok(n >= 3, name + ' has ' + n + ' shops');
  }
  assert.equal(seen.size, 10);
});

test('facade chooser: shop fronts, room walls left to the room piece, every piece it returns is in the kit', () => {
  const all = new Set(TH.allPieces());
  const hash = (a, b) => { const x = Math.sin(a * 91.7 + b * 17.3) * 1e4; return x - Math.floor(x); };
  for (const { name, g } of maps) {
    const solid = (c, r) => '#GEn'.includes(g.at(c, r));
    let shopFront = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      const ch = g.at(c, r);
      if (ch !== '#' && ch !== 'n') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r);
      const nOpen = oS + oN + oE + oW;
      let face = nOpen === 0 ? 'none' : nOpen === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      face = TH.wall.faceOf(c, r, g, face) || face;
      const exposed = nOpen > 0 || [[1, 1], [1, -1], [-1, 1], [-1, -1]].some(([a, b]) => !solid(c + a, r + b));
      if (!exposed) continue;
      const out = TH.wall.choose(c, r, false, false, hash, g, face);
      if (out === null) {
        const D = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] }[face];
        assert.ok(D && ROOMS.includes(g.at(c + D[0], r + D[1])), name + ' empty wall cell ' + c + ',' + r + ' not a room wall');
        continue;
      }
      [].concat(out).forEach((n) => assert.ok(all.has(n), name + ' chooser piece ' + n + ' at ' + c + ',' + r));
      if (ch === 'n') { assert.match(out, /^ShopOpen_\d$/, name + ' doorway ' + c + ',' + r); shopFront++; }
      if (/^Shop/.test(out)) assert.ok([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([a, b]) => ROOMS.includes(g.at(c + a, r + b))), name + ' shop module beside a room');
    }
    assert.ok(shopFront >= 9, name + ' doorways ' + shopFront);
  }
});

test('kit-parking pieces the theme places exist in fps-kit-parking.glb, cars repainted from its paint cell', () => {
  const d = fs.readFileSync(path.join(__dirname, '../../assets/fps-kit-parking.glb'));
  const js = JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
  const names = new Set(js.nodes.map((n) => n.name));
  const list = TH.parkingPieces();
  assert.ok(list.length >= 15);
  for (const n of list) assert.ok(names.has(n), 'kit-parking missing ' + n);
  const pb = fs.readFileSync(path.join(__dirname, '../../blender/parking_base.py'), 'utf8');
  const pal = [...pb.slice(pb.indexOf('PALETTES[FAM]')).matchAll(/\('(\w+)', '#[0-9A-Fa-f]{6}'\)/g)].map((m) => m[1]);
  const base = 8;   // ib_lib BASE cells come first
  assert.equal(pal.indexOf('paint') + base, 48);
  assert.equal(pal.indexOf('pYellow') + base, TH.symbols.A.paint.to[0][0]);
  assert.equal(pal.indexOf('pWhite') + base, TH.symbols.Q.paint.to[0][0]);
  assert.deepEqual(TH.symbols.A.with, { KIT_PARKING_Sedan: ['TaxiTop'] });
});
