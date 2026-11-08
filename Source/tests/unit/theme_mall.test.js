// Galleria Mall theme (kit-mall): zone layers (floor plan, floor inlays, mezzanine, roof), prefab tiling, the lift's
// landings, the storefront wall chooser (stacked storey modules, corner / gate / food-stall rules) and the lift config.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/mall.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.mall;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function grid(rows) {
  return { w: rows[0].length, h: rows.length, rows, at: (c, r) => (r < 0 || r >= rows.length || c < 0 || c >= rows[0].length) ? '#' : rows[r][c] };
}
// zones.js: the floor plan, then "@layer <y>" grids of the same size
function parse(text) {
  const out = { base: [], layers: {} };
  let cur = out.base;
  text.replace(/\r/g, '').split('\n').filter((l) => l.length).forEach((l) => {
    const m = /^@layer\s+(-?[\d.]+)/.exec(l);
    if (m) { cur = []; out.layers[m[1]] = cur; } else cur.push(l);
  });
  out.g = grid(out.base);
  Object.keys(out.layers).forEach((k) => { out.layers[k] = grid(out.layers[k]); out.layers[k].y = +k; });
  out.g.layers = Object.values(out.layers);   // zones.js hands the wall chooser the plan with its layers
  return out;
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
// the shop band: wall cells left of the hall in the first open row
function band(g) { let i = 0; while (g.rows[1][i] === '#') i++; return i - 1; }
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const plan = IB.LEVEL_PLANS.mall;
const maps = plan.zones.map((z) => ({ name: z.map, ...parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const ROOF = '~&%$:', INLAY = 'xy=+Mkw', DECK = 'uril', LO_ROOMS = 'AZCRWU', UP_ROOMS = 'gvbmt';

test('mall theme: kit-mall indoors, ceiling at wall height, roof fittings come from the zone (no auto lights)', () => {
  assert.equal(TH.family, 'kit-mall');
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.env.ceiling.light, undefined);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.budget.total <= 90000);   // 70000 before the walk-in shop rooms (11 room pieces, 55 open-front modules)
});

test('every zone: floor plan + inlay (0), mezzanine (4.5) and roof (9.5) grids of one size, symbols on their own layer', () => {
  for (const m of maps) {
    assert.deepEqual(Object.keys(m.layers).sort(), ['0', '4.5', '9.5'], m.name);
    for (const [y, L] of Object.entries(m.layers)) {
      assert.equal(L.w, m.g.w, m.name + ' @' + y); assert.equal(L.h, m.g.h, m.name + ' @' + y);
      const allowed = { '0': INLAY + 'ah', '4.5': DECK + 'oBcSahd' + UP_ROOMS, '9.5': ROOF }[y] + '.#';
      L.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(allowed.includes(ch), m.name + ' @' + y + ' ' + ch + ' at ' + c + ',' + r)));
    }
    m.g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(!(INLAY + ROOF + DECK).includes(ch), m.name + ' plan ' + ch + ' at ' + c + ',' + r)));
  }
});

test('prefab symbols tile their blocks exactly (no stretched or overlapping copies)', () => {
  for (const m of maps) {
    const grids = [m.g, ...Object.values(m.layers)];
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      grids.forEach((g) => rects(g, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, m.name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
      }));
    }
  }
});

test('columns stand under and over the mezzanine edge; the lift opens onto deck upstairs and floor downstairs', () => {
  for (const m of maps) {
    const mez = m.layers['4.5'];
    let n = 0;
    m.g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'I') { n++; assert.equal(mez.at(c, r), 'i', m.name + ' column ' + c + ',' + r); } }));
    assert.ok(n >= 8, m.name + ' columns');
    for (const ch of 'LJ') rects(m.g, ch).forEach((R) => {
      assert.equal(R.w, 3); assert.equal(R.h, 3);
      const c = ch === 'L' ? R.c - 1 : R.c + 3;   // door west / east
      for (let r = R.r; r < R.r + 3; r++) {
        assert.ok('ul'.includes(mez.at(c, r)), m.name + ' upper landing ' + c + ',' + r + ' ' + mez.at(c, r));
        assert.equal(m.g.at(c, r) === '.' || m.g.at(c, r) === 'a' || m.g.at(c, r) === 'h', true, m.name + ' ground landing ' + c + ',' + r);
        for (let k = R.c; k < R.c + 3; k++) assert.equal(mez.at(k, r), '.', m.name + ' shaft is open on the mezzanine');
      }
    });
  }
});

test('wall chooser: stacked storey modules from the kit, narrow pilasters by the corners, piers by the gates, plain behind stalls', () => {
  const pieces = new Set(TH.allPieces());
  const SOLID = '#GE' + TH.wall.passage.ch;
  for (const m of maps) {
    const g = m.g, solid = (c, r) => SOLID.includes(g.at(c, r)), B = band(g);
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#' && g.at(c, r) !== TH.wall.passage.ch) continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
      const exposed = n || [[-1, -1], [1, -1], [-1, 1], [1, 1]].some(([a, b]) => !solid(c + a, r + b));
      if (!exposed) continue;
      let face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      face = TH.wall.faceOf(c, r, g, face) || face;
      const horiz = solid(c - 1, r) || solid(c + 1, r), vert = solid(c, r - 1) || solid(c, r + 1);
      const got = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, face);
      if (c < B || c > g.w - 1 - B) { assert.equal(got, null, m.name + ' shop room wall ' + c + ',' + r); continue; }
      [].concat(got).forEach((p) => assert.ok(pieces.has(p), m.name + ' ' + c + ',' + r + ' ' + p));
      if (c === B && face !== 'none' && face !== 'corner') assert.equal(face, 'E', m.name + ' west front ' + c + ',' + r);
      if (c === g.w - 1 - B && face !== 'none' && face !== 'corner') assert.equal(face, 'W', m.name + ' east front ' + c + ',' + r);
      const ns = face === 'S' || face === 'N';
      if (face !== 'none' && face !== 'corner' && (ns ? (c === B + 1 || c === g.w - B - 2) : (r === 1 || r === g.h - 2))) assert.equal(got, 'Pilaster_C', m.name + ' ' + c + ',' + r);
      if (ns && (g.at(c - 1, r) === 'G' || g.at(c + 1, r) === 'G' || g.at(c - 1, r) === 'E' || g.at(c + 1, r) === 'E')) assert.equal(got, 'GateSide');
      if (Array.isArray(got)) {
        assert.match(got[0], /^Lo_/); assert.match(got[1], /^Up_/);
        const front = g.at(c + (face === 'E' ? 1 : face === 'W' ? -1 : 0), r + (face === 'S' ? 1 : face === 'N' ? -1 : 0));
        assert.equal(got[0] === 'Lo_Plain', front === 'Y', m.name + ' ' + c + ',' + r);
      }
    }
  }
});

test('the glass lift: doors part on the cab and the landing, the doorway fits every ground robot, it reaches the deck', () => {
  const E = TH.symbols.L.elevator;
  assert.deepEqual(TH.symbols.J.elevator, E);
  assert.equal(E.top, 4.5);
  assert.ok(E.doors && E.doors.cab && E.doors.landing);
  assert.ok(E.doors.width >= 1.2 && E.doors.width < E.inner[0], 'doorway');
  assert.ok(E.doors.landZ[0] > E.inner[1] / 2 && E.doors.landZ[1] <= 1.5, 'landing doors between the cab and the shaft front');
  assert.ok(E.wall >= 2.2, 'cab walls are too high to jump out of');
  assert.ok(E.wait > E.doors.time * 2, 'doors open and close inside the wait');
});

test('walk-in shops: 5 x 6 m rooms behind a third or more of the west / east bays, both storeys, open to the hall', () => {
  const sym = TH.symbols, pieces = new Set(TH.allPieces());
  for (const m of maps) {
    const g = m.g, mez = m.layers['4.5'], B = band(g), n = TH.wall.passage.ch;
    assert.equal(B, 7, m.name + ' band');
    const rooms = [];
    for (const ch of LO_ROOMS) rects(g, ch).forEach((R) => rooms.push({ ch, R }));
    assert.ok(rooms.length >= 9, m.name + ' walk-in shops: ' + rooms.length);
    const brands = new Set();
    for (const { ch, R } of rooms) {
      assert.equal(R.w, 6, m.name + ' room depth'); assert.equal(R.h, 5, m.name + ' room width');
      assert.equal(sym[ch].size.join(), '5,6'); assert.equal(sym[ch].orient, 'open');
      assert.ok(pieces.has(sym[ch].pieces[0]));
      const west = R.c === 1, front = west ? B : g.w - 1 - B, inw = west ? 1 : -1;
      assert.ok(west || R.c + R.w === g.w - 1, m.name + ' room in the band');
      const up = new Set();
      for (let r = R.r; r < R.r + R.h; r++) for (let c = R.c; c < R.c + R.w; c++) up.add(mez.at(c, r));
      assert.equal(up.size, 1, m.name + ' one upper shop over the room');
      const uch = [...up][0];
      assert.ok(UP_ROOMS.includes(uch), m.name + ' upper room ' + uch);
      assert.ok(pieces.has(sym[uch].pieces[0]));
      brands.add(ch); brands.add(uch);
      // walls round the room on both storeys; the front: window, three doorways, window; deck in the upper doorways
      for (let r = R.r - 1; r <= R.r + R.h; r++) assert.equal(g.at(west ? 0 : g.w - 1, r), '#');
      for (let c = R.c; c < R.c + R.w; c++) { assert.equal(g.at(c, R.r - 1), '#'); assert.equal(g.at(c, R.r + R.h), '#'); }
      const fr = [];
      for (let r = R.r; r < R.r + R.h; r++) fr.push(g.at(front, r));
      assert.equal(fr.join(''), '#' + n + n + n + '#', m.name + ' shop front ' + R.r);
      for (let r = R.r + 1; r < R.r + 4; r++) {
        assert.ok('ul'.includes(mez.at(front, r)), m.name + ' upper doorway deck');
        for (const j of [1, 2]) {   // the way in is clear on both storeys
          assert.ok('.ah'.includes(g.at(front + inw * j, r)), m.name + ' doorway approach ' + (front + inw * j) + ',' + r);
          assert.ok('ul'.includes(mez.at(front + inw * j, r)), m.name + ' upper doorway approach');
        }
      }
      // the chooser opens the bay on both storeys with the rooms' own shops
      const face = west ? 'E' : 'W';
      for (let r = R.r; r < R.r + R.h; r++) {
        const got = TH.wall.choose(front, r, false, false, hash, g, face);
        assert.ok(Array.isArray(got), m.name + ' front ' + r);
        assert.match(got[0], /^Lo_[a-z]+_(WinAW|WinBW|OpenL|OpenC|OpenR)$/);
        assert.match(got[1], /^Up_[a-z]+_(WinAW|WinBW|OpenL|OpenC|OpenR)$/);
        assert.equal(/Open/.test(got[0]), g.at(front, r) === n, m.name + ' doorway module ' + r);
        assert.ok(!/^Up_gold_/.test(got[1]), 'Field & Court stays shuttered');
      }
    }
    assert.ok(brands.size >= 9, m.name + ' shop variety ' + brands.size);
    // the doorway lintels: open below the ground-storey transom and between the deck and the upper transom
    assert.deepEqual(TH.wall.passage.solid, [[3.0, 4.1], [7.3, 9.5]]);
    // spawns stay in the hall
    for (const L of [m.g, mez]) L.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'S') assert.ok(c > B && c < g.w - 1 - B, m.name + ' spawn in the hall'); }));
  }
});
