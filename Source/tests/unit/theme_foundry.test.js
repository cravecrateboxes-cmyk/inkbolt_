// Titan Foundry theme (kit-foundry): the level plan (three zones, the hardest waves so far), zone maps (floor plan,
// floor paint layer, the armour hall's gantry layer: size, gates, reachability, spawns, prefab tiling, paint and
// gantry symbols where they belong), the wall chooser (corners, gate sides, buttress rhythm, banner triples, bay
// numbers, flat backs behind the launch doors, plain walls beside the monorail ports) and the moving lines.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/grove.js');
require('../../src/data/themes/police.js');
require('../../src/data/themes/foundry.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.foundry;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function grid(rows, w, out) {
  const padded = rows.map((r) => r.slice(0, w).padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? out : padded[r][c] };
}
// mirrors zones.js Z.parse: the floor plan, then "@layer <y>" grids of the same size (g.layers, as the wall chooser sees)
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
// zones.js rects(): greedy row-first rectangles of one symbol
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
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
function faceOf(g, c, r) {
  const solid = (cc, rr) => '#GE'.includes(g.at(cc, rr));
  const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
  return n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
}
const total = (p) => p.zones.reduce((t, z) => t + z.waves.reduce((u, w) => u + w.reduce((v, e) => v + e[1], 0), 0), 0);
const plan = IB.LEVEL_PLANS.foundry;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const PREFAB = Object.keys(TH.symbols).filter((k) => TH.symbols[k].size);
const PAINT = '1234568 90'.replace(' ', '').split('');
// the armour bay's walkway decks at 6 m in the bay's own frame (x east, y = Blender y: north is +y), mirrored from
// blender/foundry_giants.py bay_armour_deck(): wings, front bridge, back landings
const DECKS = [[-10, -8, -9, 7.5], [8, 10, -9, 7.5], [-8, 8, -9, -6.5], [-12, -10, 3, 7.5], [10, 12, 3, 7.5]];

test('foundry theme: kit-foundry indoors, 30 m halls, trails as tall as the walls, roof bays clear of the giants', () => {
  assert.equal(TH.family, 'kit-foundry');
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, 30);
  assert.ok(TH.wall.height > TH.env.ceiling.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.env.ceiling.height);
  for (const ch of 'TYZXVD') assert.ok(TH.env.ceiling.clear.includes(ch), 'roof bays keep clear of ' + ch);
  assert.ok(TH.budget.total <= 100000 && TH.budget.landmark <= 6000);
});

test('level plan: three zones, more robots than Redwood Hollow and Strike Team HQ, every robot type, soldiers and bladers', () => {
  assert.equal(plan.zones.length, 3);
  assert.deepEqual(plan.zones.map((z) => z.map), ['foundry_1', 'foundry_2', 'foundry_3']);
  const t = total(plan);
  assert.ok(t > total(IB.LEVEL_PLANS.grove) && t > total(IB.LEVEL_PLANS.police), 'robots ' + t);
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([id]) => types.add(id))));
  for (const id of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(id), id);
  for (const z of plan.zones) assert.equal(z.waves.length, 4);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, reachability, spawns, pickups, prefab tiling', () => {
    assert.equal(g.w, 60); assert.equal(g.h, 72);
    assert.equal(g.rows[0].slice(29, 32), 'GGG');
    assert.equal(g.rows[g.h - 1].slice(29, 32), 'EEE');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const F = g.layers.find((L) => L.y === 0);
    assert.ok(F, 'floor paint layer');
    assert.deepEqual(g.layers.map((L) => L.y), name === 'foundry_2' ? [0, 6] : [0]);
    const open = (c, r) => '.ahPS'.includes(g.at(c, r));
    let P = null, S = 0, a = 0, h = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      const b = g.at(c, r);
      if (b === 'P') P = [c, r];
      if (b === 'a') a++; if (b === 'h') h++;
      const f = F.at(c, r);
      if (f !== '.') {
        assert.ok(PAINT.includes(f) || f === 'o', name + ' paint symbol ' + f);
        assert.ok(!'#GE'.includes(b), name + ' paint on a wall at ' + c + ',' + r);
        assert.equal(TH.symbols[f].collide, false);
      }
    }
    assert.ok(P, 'P');
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups a=' + a + ' h=' + h);
    const seen = new Set([P.join()]), q = [P];
    while (q.length) {
      const [c, r] = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = [c + dc, r + dr];
        if (!seen.has(n.join()) && open(...n)) { seen.add(n.join()); q.push(n); }
      }
    }
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) if (open(c, r)) assert.ok(seen.has(c + ',' + r), name + ' sealed cell ' + c + ',' + r);
    assert.ok([29, 30, 31].some((c) => seen.has(c + ',1')), 'P reaches the exit gate');
    for (const dc of [-2, -1, 1, 2]) assert.ok(open(P[0] + dc, P[1] - 4), 'weapon stand cell');
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if (g.at(c, r) === 'S') {
      S++;
      assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14, 'spawn ' + c + ',' + r + ' far from P');
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) if (dc || dr) assert.ok(open(c + dc, r + dr), 'spawn ' + c + ',' + r + ' 3x3 open');
    }
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    for (const L of [g, F]) for (const ch of PREFAB) for (const R of rects(L, ch)) {
      const [sw, sd] = TH.symbols[ch].size;
      assert.ok((R.w % sw === 0 && R.h % sd === 0) || (R.w % sd === 0 && R.h % sw === 0), name + ' ' + ch + ' ' + R.w + 'x' + R.h + ' at ' + R.c + ',' + R.r);
    }
    // the giants each have their own bay and launch doors stand against the south wall
    for (const R of rects(g, 'D')) { assert.equal(R.r + R.h, g.h - 1, 'door against the south wall'); assert.equal(R.h, 2); }
    // monorails run wall to wall on rows clear of the buttresses (their ports reach 1.9 m either side of the rail)
    const rails = rects(F, 'o');
    assert.equal(rails.length, name === 'foundry_3' ? 0 : 1);
    for (const R of rails) {
      assert.equal(R.c, 1); assert.equal(R.w, g.w - 2); assert.equal(R.h, 1);
      assert.ok([7, 0, 1].includes(R.r % 8), name + ' monorail row ' + R.r);
    }
  });

  test('zone ' + name + ': the wall chooser styles every wall cell and returns kit pieces', () => {
    const all = new Set(TH.allPieces());
    const pick = {};
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const face = faceOf(g, c, r), p = TH.wall.choose(c, r, false, false, hash, g, face);
      assert.ok(all.has(p), name + ' ' + c + ',' + r + ' -> ' + p);
      pick[c + ',' + r] = p;
      if (face === 'none' || face === 'corner') assert.match(p, /^Corner_(N|S)(W|E)$/);
      if (r === g.h - 1 && g.at(c, r - 1) === 'D') assert.equal(p, 'Wall_Back', 'flat wall behind a launch door');
      if ((c === 1 || c === g.w - 2) && (r === 0 || r === g.h - 1)) assert.match(p, /^Wall_End[LR]$/);
    }
    // a corner module's details stop on the corner's side: on the north wall (faces S) the west end is local -X
    assert.equal(pick['1,0'], 'Wall_EndL'); assert.equal(pick[(g.w - 2) + ',0'], 'Wall_EndR');
    assert.equal(pick['1,' + (g.h - 1)], 'Wall_EndR'); assert.equal(pick['0,1'], 'Wall_EndR'); assert.equal(pick[(g.w - 1) + ',1'], 'Wall_EndL');
    // banners always come as a full triple, halves in the module's own left-to-right order
    let banners = 0, buttresses = 0;
    for (const [k, p] of Object.entries(pick)) {
      const [c, r] = k.split(',').map(Number);
      if (p === 'Pilaster') {
        // a buttress reaches 1.75 m into the room: the two cells in front of it stay clear
        buttresses++;
        const ns = r === 0 || r === g.h - 1;
        assert.equal((ns ? c : r) % 8, 4, 'buttress every 8 m');
        for (const d of [1, 2]) {
          const cc = ns ? c : (c === 0 ? d : c - d), rr = ns ? (r === 0 ? d : r - d) : r;
          assert.ok('.SahP'.includes(g.at(cc, rr)), name + ' buttress at ' + k + ' blocked by ' + g.at(cc, rr));
        }
      }
      if (p !== 'Wall_BanM') continue;
      banners++;
      const face = faceOf(g, c, r), ns = face === 'S' || face === 'N', plusHi = face === 'S' || face === 'W';
      const lo = pick[ns ? (c - 1) + ',' + r : c + ',' + (r - 1)], hi = pick[ns ? (c + 1) + ',' + r : c + ',' + (r + 1)];
      assert.equal(plusHi ? lo : hi, 'Wall_BanL', name + ' banner at ' + k);
      assert.equal(plusHi ? hi : lo, 'Wall_BanR', name + ' banner at ' + k);
    }
    assert.ok(banners >= 6, name + ' banners ' + banners);
    assert.ok(buttresses >= 20, name + ' buttresses ' + buttresses);
    // the monorail ports cover the wall where a rail meets it: plain modules there
    for (const R of rects(g.layers[0], 'o')) for (const c of [0, g.w - 1]) for (let dr = -2; dr <= 2; dr++) assert.equal(pick[c + ',' + (R.r + dr)], 'Wall_Plain');
  });
}

test('armour hall gantry ("@layer 6"): spawns and pickups stand on the walkway decks, spawns with deck all round', () => {
  const { g } = maps[1], G = g.layers.find((L) => L.y === 6), [B] = rects(g, 'Y');
  assert.equal(B.w, 24); assert.equal(B.h, 18);
  const cx = B.c + B.w / 2, cz = B.r + B.h / 2;
  // a cell is on a deck when its whole square lies in one of the deck rectangles (bay frame: x east, y north = -z)
  const onDeck = (c, r) => DECKS.some(([x0, x1, y0, y1]) => c - cx >= x0 && c + 1 - cx <= x1 && cz - (r + 1) >= y0 && cz - r <= y1);
  let S = 0;
  for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
    const s = G.at(c, r);
    if (s === '.') continue;
    assert.ok('Sah'.includes(s), 'gantry symbol ' + s);
    assert.equal(g.at(c, r), 'Y');
    assert.ok(onDeck(c, r), s + ' at ' + c + ',' + r + ' on a deck');
    if (s === 'S') {
      S++;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(onDeck(c + dc, r + dr), 'deck round the spawn at ' + c + ',' + r);
    }
  }
  assert.equal(S, 2);
});

test('moving lines: chassis change stage inside the fitting tunnels, carriers ride the monorail between its ports', () => {
  const all = new Set(TH.allPieces());
  for (const ch of ['L', 'U']) {
    const C = TH.symbols[ch].conveyor;
    assert.deepEqual(TH.symbols[ch].pieces, ['Line_Feed', 'Line_Mid', 'Line_Out']);
    assert.equal(TH.symbols[ch].sequence, 'run');
    assert.ok(C.stations.Line_Feed > 1.2 && C.stations.Line_Feed < 5.8, 'the swap happens inside the tunnel (x 1.2 - 5.8)');
    assert.ok(C.inset >= 1.0 && C.inset <= 3.0, 'pop in / out inside the 4 m end houses');
    IB.conveyorPieces(C).forEach((n) => assert.ok(all.has(n), n));
  }
  const O = TH.symbols.o;
  assert.equal(O.collide, false);
  assert.deepEqual([O.conveyor.ends.start, O.conveyor.ends.end], ['ORail_PortIn', 'ORail_PortOut']);
  assert.ok(O.conveyor.inset >= O.conveyor.ends.at, 'carriers pop in and out inside the ports');
  IB.conveyorPieces(O.conveyor).forEach((n) => assert.ok(all.has(n), n));
  for (const ch of 'TYZXV') for (const n of Object.values(TH.symbols[ch].with || {})[0]) assert.ok(all.has(n), n);
});
