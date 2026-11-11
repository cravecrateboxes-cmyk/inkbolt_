// Larkspur Glen theme (kit-townhomes): level plan and waves (two zones), the zone grids (size, gates, the paving and
// house-floor layers, symbols, prefab tiling and facing, spawns, pickups), the town-house lots (6 x 12, walk-in houses
// with the approach to their doors and the step row clear), the wall chooser, the kit pieces the theme names and the
// kit-parking pieces it borrows.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/townhomes.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.townhomes;
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
const plan = IB.LEVEL_PLANS.townhomes;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const FLOOR = ".-|`!+^'o";
const PAVE = ',;:_=~"';
const STAND = '.SahPEG' + FLOOR;
const S_LOTS = 'HJKQ1237', N_LOTS = 'UVXY4568', WALK = '123456';

test('townhomes theme: kit-townhomes with kit-parking, daylight, two zones of hard waves (no elites in the first wave)', () => {
  assert.equal(TH.family, 'kit-townhomes');
  assert.deepEqual(TH.families, ['kit-parking']);
  assert.ok(Array.isArray(TH.env.sky) && TH.env.ceiling === null);
  assert.equal(plan.zones.length, 2);
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  assert.ok(total >= 200, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
  for (const t of plan.zones[0].waves[0]) assert.ok(!['soldier', 'blader'].includes(t[0]), 'first wave ' + t[0]);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, symbols, prefab tiling and facing, spawns, pickups', () => {
    assert.ok(g.w === 72 && g.h === 64, name + ' ' + g.w + 'x' + g.h);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    const ys = g.layers.map((L) => L.y);
    assert.deepEqual(ys.filter((y) => y !== 0.32 && y !== 3.32), [0]);
    g.layers.forEach((L) => L.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (L.y === 0) assert.ok(('.' + PAVE).includes(ch), name + ' @0 ' + ch + ' at ' + c + ',' + r);
      else {
        assert.ok('.ah'.includes(ch), name + ' @' + L.y + ' ' + ch);
        if (ch !== '.') assert.ok(WALK.includes(g.at(c, r)), name + ' house-floor pickup in a walk-in house ' + c + ',' + r);
      }
    })));
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

test('town-house lots: 6 x 12 blocks facing a street, walk-in houses reachable through both doors, step rows clear', () => {
  let walks = 0, lots = 0;
  for (const { name, g } of maps) {
    for (const ch of S_LOTS + N_LOTS) rects(g, ch).forEach((R) => {
      assert.ok(R.h === 12 && R.w % 6 === 0, name + ' lot ' + ch + ' ' + JSON.stringify(R));
      const south = S_LOTS.includes(ch);
      for (let i = 0; i < R.w / 6; i++) {
        lots++;
        const c0 = R.c + i * 6, front = south ? R.r + 12 : R.r - 1, back = south ? R.r - 1 : R.r + 12, out = south ? 1 : -1;
        // the first row in front is free of props (porch step / stoop); the door column leads on to open ground
        const door = south ? c0 + 1 : c0 + 4;
        for (let k = 0; k < 2; k++) assert.ok(STAND.includes(g.at(door, front + out * k)), name + ' door approach ' + door + ',' + (front + out * k));
        if (!WALK.includes(ch)) continue;
        walks++;
        for (let c = c0; c < c0 + 6; c++) assert.ok(STAND.includes(g.at(c, front)) || TH.symbols[g.at(c, front)].collide === false, name + ' step row ' + c + ',' + front);
        assert.ok(STAND.includes(g.at(door, back)) && STAND.includes(g.at(door, back - out)), name + ' back door ' + door + ',' + back);
        assert.ok(TH.symbols[ch].with, 'walk-in ' + ch + ' places its furniture');
      }
    });
  }
  assert.ok(lots >= 24, 'lots ' + lots);
  assert.ok(walks >= 5, 'walk-in houses ' + walks);
});

test('wall chooser and pieces: every name the theme can place is in the kit list; gate cells left to the gate piers', () => {
  const all = new Set(TH.allPieces());
  const hash = () => 0.5;
  for (const { g } of maps) {
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const solid = (cc, rr) => '#GE'.includes(g.at(cc, rr));
      const face = (cc, rr) => {   // zones.js buildWalls: the open cardinal neighbours
        const oS = !solid(cc, rr + 1), oN = !solid(cc, rr - 1), oE = !solid(cc + 1, rr), oW = !solid(cc - 1, rr), n = oS + oN + oE + oW;
        return n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      };
      const out = TH.wall.choose(c, r, false, false, hash, g, face(c, r));
      const nearGate = [-1, 0, 1].some((k) => 'GE'.includes(g.at(c + k, r)));
      if (nearGate) { assert.equal(out, null); continue; }
      if (out === null) {   // the second cell of a two-cell wall module: a neighbour draws it
        const lead = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([a, b]) => g.at(c + a, r + b) === '#' && TH.wall.choose(c + a, r + b, false, false, hash, g, face(c + a, r + b)) === 'Perim2');
        assert.ok(lead, 'empty wall cell ' + c + ',' + r);
        continue;
      }
      assert.ok(all.has(out), 'chooser piece ' + out);
    }
  }
  for (const d of Object.values(TH.symbols)) for (const n of d.pieces) if (n.indexOf('KIT_PARKING_') !== 0) assert.ok(all.has(n), 'allPieces lists ' + n);
  const glb = fs.readFileSync(path.join(__dirname, '../../assets/fps-kit-townhomes.glb'));
  const js = JSON.parse(glb.toString('utf8', 20, 20 + glb.readUInt32LE(12)));
  const names = new Set(js.nodes.map((n) => n.name));
  for (const n of all) assert.ok(names.has(TH.prefix + n), 'fps-kit-townhomes.glb has ' + n);
  assert.ok(glb.length <= 2500000, 'kit GLB ' + glb.length + ' bytes');
});

test('kit-parking pieces the theme places exist in fps-kit-parking.glb, cars repainted from its paint cell', () => {
  const d = fs.readFileSync(path.join(__dirname, '../../assets/fps-kit-parking.glb'));
  const js = JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
  const names = new Set(js.nodes.map((n) => n.name));
  const list = TH.parkingPieces();
  assert.ok(list.length >= 8);
  for (const n of list) assert.ok(names.has(n), 'kit-parking missing ' + n);
  assert.equal(TH.symbols.C.paint.from[0], 48);
});

test('house paint jobs map the five source cells onto palette cells of kit-townhomes', () => {
  const pb = fs.readFileSync(path.join(__dirname, '../../blender/townhomes_base.py'), 'utf8');
  const pal = [...pb.slice(pb.indexOf('PALETTES[FAM]')).matchAll(/\('(\w+)', '#[0-9A-Fa-f]{6}'\)/g)].map((m) => m[1]);
  const base = 8;
  assert.deepEqual(['sid', 'stu', 'brk', 'door', 'shut'].map((n) => pal.indexOf(n) + base), TH.symbols.H.paint.from);
  const P = TH.symbols.H.paint;
  P.to.forEach((job) => job.forEach((cell, i) => {
    const nm = pal[cell - base];
    assert.ok(nm, 'cell ' + cell);
    assert.ok(nm.startsWith(['sid', 'stu', 'brk', 'door', 'shut'][i].replace('door', 'door').slice(0, 3)) || (i === 4 && nm.startsWith('door')), 'job cell ' + nm + ' for ' + i);
  }));
});
