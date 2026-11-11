// The Aurelian theme (kit-hotel): level plan (three zones up one tower, waves on the levels 14-19 line, few Bombers),
// zone layers (floor plan, floors and plates, the lobby gallery, ceiling / glass roof), odd widths with the gates on
// the centre line, reachability on both floors, spawns, pickups, prefab tiling, the open suites (front to the
// doorway, a plate by each door), the wall chooser (every wall cell resolves to a kit piece, arch halves flip on the S
// and W walls), the upholstery repaint cells, and the outside: every zone at its own height above the street.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/hotel.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.hotel;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function grid(rows) {
  return { w: rows[0].length, h: rows.length, rows, at: (c, r) => (r < 0 || r >= rows.length || c < 0 || c >= rows[0].length) ? '#' : rows[r][c] };
}
function parse(text) {
  const out = { base: [], layers: {} };
  let cur = out.base;
  text.replace(/\r/g, '').split('\n').filter((l) => l.length).forEach((l) => {
    const m = /^@layer\s+(-?[\d.]+)/.exec(l);
    if (m) { cur = []; out.layers[m[1]] = cur; } else cur.push(l);
  });
  out.g = grid(out.base);
  Object.keys(out.layers).forEach((k) => { out.layers[k] = grid(out.layers[k]); });
  return out;
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
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const plan = IB.LEVEL_PLANS.hotel;
const maps = plan.zones.map((z) => ({ name: z.map, plan: z, ...parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const GROUND = '.ahPn', DECK = 'm;ah';
const LAYER_SYMS = { '0': 'x-_!+&%$', '0.01': '123456', '4.5': 'mri;LwpOSah', '9': '~:HY^' };

test('hotel theme: kit-hotel, 9 m floors, sky outside, a far camera and a tier-scaled fog for the city', () => {
  assert.equal(TH.family, 'kit-hotel');
  assert.equal(TH.prefix, 'KIT_HOTEL_');
  assert.equal(TH.wall.height, 9);
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(Array.isArray(TH.env.sky) && TH.env.sky[1] === TH.env.fog.color && TH.below.haze === TH.env.fog.color, 'sky horizon, fog and city haze are one colour');
  assert.ok(TH.env.far >= TH.below.horizon, 'the camera sees the haze ground out to the horizon');
  assert.ok(TH.env.fog.tierScale);
  assert.ok(TH.budget.total <= 100000);
  assert.ok(TH.wall.passage && TH.wall.passage.ch === 'n' && TH.wall.passage.solid[0][0] >= 2.5, 'doorways open below their lintel');
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
});

test('level plan: three zones up the tower, waves on the campaign line, Soldiers and Blade Bots, at most 2 Bombers a wave', () => {
  assert.equal(plan.themeId, 'hotel');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f);
  const types = new Set(); let total = 0;
  plan.zones.forEach((z) => z.waves.forEach((w) => {
    let bombers = 0;
    w.forEach(([t, n]) => { types.add(t); total += n; if (t === 'bomber') bombers += n; });
    assert.ok(bombers <= 2, 'bombers ' + bombers);
  }));
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
  assert.ok(total >= 300 && total <= 380, 'total ' + total);
  assert.deepEqual(plan.zones.map((z) => z.ceiling), ['plain', 'plain', false], 'lobby and ballroom floor: ceiling fittings; the roof: a glass roof');
  plan.zones.forEach((z) => assert.ok(typeof z.label === 'string' && z.label.length < 24, 'zone label'));
  assert.ok(IB.LEVEL_PLANS.hotel.zones.every((z) => z.waves.length === 4));
});

for (const m of maps) {
  test('zone ' + m.name + ': size, layers, gates on the centre line, reachability on both floors, spawns, pickups, prefab tiling', () => {
    const g = m.g, mez = m.layers['4.5'];
    assert.equal(g.w % 2, 1, 'odd width: the 3-cell gates sit on the centre line');
    assert.ok(g.w >= 50 && g.w <= 60 && g.h >= 50 && g.h <= 60, g.w + 'x' + g.h);
    for (const [y, L] of Object.entries(m.layers)) {
      assert.ok(y in LAYER_SYMS, 'layer ' + y);
      assert.equal(L.w, g.w); assert.equal(L.h, g.h);
      L.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok((LAYER_SYMS[y] + '.#').includes(ch), m.name + ' @' + y + ' ' + ch + ' at ' + c + ',' + r)));
    }
    assert.ok(m.layers['9'], 'ceiling fittings / glass roof layer');
    if (m.plan.ceiling === false) assert.ok(rects(m.layers['9'], '^').length > 0, 'a glass roof where there is no ceiling');
    for (let c = 0; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0))); assert.ok('#E'.includes(g.at(c, g.h - 1))); }
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const G = [...g.rows[0]].map((ch, c) => ch === 'G' ? c : -1).filter((c) => c >= 0);
    const E = [...g.rows[g.h - 1]].map((ch, c) => ch === 'E' ? c : -1).filter((c) => c >= 0);
    assert.deepEqual([G.length, G[2] - G[0], E.length, E[2] - E[0]], [3, 2, 3, 2]);
    assert.equal(G[1] + 0.5, g.w / 2, 'exit on the centre line'); assert.equal(E[1] + 0.5, g.w / 2, 'entry on the centre line');
    G.forEach((c) => { assert.ok(GROUND.includes(g.at(c, 1)) && GROUND.includes(g.at(c, 2)), 'open in front of the exit'); });
    E.forEach((c) => { assert.ok(GROUND.includes(g.at(c, g.h - 2)), 'open behind the entry'); });
    let P = null;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') { assert.equal(P, null); P = [c, r]; } }));
    assert.ok(P);
    for (const dc of [-2, -1, 1, 2]) assert.ok(GROUND.includes(g.at(P[0] + dc, P[1] - 4)), 'weapon stand cells');
    const links = [];
    rects(g, 'Z').forEach((R) => {
      for (let c = R.c; c < R.c + R.w; c++) {
        const lo = [c, R.r + R.h], hi = [c, R.r - 1];
        assert.ok(GROUND.includes(g.at(...lo)), m.name + ' stair foot ' + lo);
        assert.ok(mez && DECK.includes(mez.at(...hi)), m.name + ' stair head on the gallery ' + hi);
        links.push([lo, hi]);
      }
    });
    const key = (L, c, r) => L + ':' + c + ',' + r, seen = new Set([key(0, ...P)]), q = [[0, ...P]];
    while (q.length) {
      const [L, c, r] = q.shift(), nb = [[1, 0], [-1, 0], [0, 1], [0, -1]].map(([dc, dr]) => [L, c + dc, r + dr]);
      links.forEach(([a, b]) => { if (L === 0 && a[0] === c && a[1] === r) nb.push([1, ...b]); if (L === 1 && b[0] === c && b[1] === r) nb.push([0, ...a]); });
      for (const n of nb) {
        const k = key(...n); if (seen.has(k)) continue;
        if (n[0] === 0 ? GROUND.includes(g.at(n[1], n[2])) : (mez && DECK.includes(mez.at(n[1], n[2])))) { seen.add(k); q.push(n); }
      }
    }
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (GROUND.includes(ch)) assert.ok(seen.has(key(0, c, r)), m.name + ' ground cell ' + c + ',' + r + ' sealed'); }));
    if (mez) mez.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (DECK.includes(ch)) assert.ok(seen.has(key(1, c, r)), m.name + ' deck cell ' + c + ',' + r + ' sealed'); }));
    assert.ok(G.some((c) => seen.has(key(0, c, 1))), 'P reaches the exit');
    let n = 0, nDeck = 0;
    [[g, GROUND.replace('n', ''), 0], [mez, DECK, 1]].forEach(([L, OPEN, lv]) => {
      if (!L) return;
      L.rows.forEach((row, r) => [...row].forEach((ch, c) => {
        if (ch !== 'S') return;
        n++; if (lv) nDeck++;
        if (!lv) assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14, m.name + ' spawn near P');
        for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(OPEN.includes(L.at(c + dc, r + dr)), m.name + ' spawn ' + c + ',' + r + ' crowded');
        if (lv) assert.notEqual(g.at(c, r), 'Z', 'deck spawn over a stair');
      }));
    });
    assert.ok(n >= 10 && n <= 16, m.name + ' spawns ' + n);
    if (mez) assert.ok(nDeck >= 3, 'spawns on the gallery too');
    const count = (ch) => [g, mez].filter(Boolean).reduce((s, L) => s + L.rows.join('').split(ch).length - 1, 0);
    assert.ok(count('a') >= 2 && count('a') <= 3 && count('h') >= 2 && count('h') <= 3, 'pickups');
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'I') assert.equal(mez.at(c, r), 'i', 'column ' + c + ',' + r); }));
    for (const L of [g, ...Object.values(m.layers)]) {
      for (const [ch, d] of Object.entries(TH.symbols)) {
        if (!d.size) continue;
        rects(L, ch).forEach((R) => assert.ok((R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0), m.name + ' ' + ch + ' ' + JSON.stringify(R)));
      }
    }
  });
}

test('the open suites: walled on three sides, a two-cell doorway in the front, a numbered plate beside each of six doors', () => {
  const m = maps.find((x) => x.name === 'hotel_ballroom'), g = m.g, plates = m.layers['0.01'];
  const suites = [].concat(...'MNW'.split('').map((ch) => rects(g, ch).map((R) => ({ ch, ...R }))));
  assert.equal(suites.length, 7);
  const nums = [];
  suites.forEach((S) => {
    assert.deepEqual([S.w, S.h], [6, 6]);
    for (let r = S.r; r < S.r + 6; r++) { assert.equal(g.at(S.c - 1, r), '#', 'facade behind'); }
    for (let c = S.c; c < S.c + 6; c++) { assert.equal(g.at(c, S.r - 1), '#'); assert.equal(g.at(c, S.r + 6), '#'); }
    const front = [];
    for (let r = S.r; r < S.r + 6; r++) front.push(g.at(S.c + 6, r));
    assert.equal(front.join(''), '##nn##', 'doorway in the middle of the front wall');
    for (let r = S.r; r < S.r + 6; r++) if ('123456'.includes(plates.at(S.c + 7, r))) nums.push(+plates.at(S.c + 7, r));
  });
  assert.deepEqual(nums.sort(), [1, 2, 3, 4, 5, 6]);
  for (const ch of 'MNW') assert.equal(TH.symbols[ch].orient, 'open');
});

test('wall chooser: every wall cell resolves to a kit piece; arch halves pair up and flip on the S and W walls', () => {
  const pieces = new Set(TH.allPieces());
  const SOLID = '#GEn';
  for (const m of maps) {
    const g = m.g, solid = (c, r) => SOLID.includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (!'#n'.includes(g.at(c, r))) continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
      if (!n && ![[-1, -1], [1, -1], [-1, 1], [1, 1]].some(([a, b]) => !solid(c + a, r + b))) continue;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const horiz = solid(c - 1, r) || solid(c + 1, r), vert = solid(c, r - 1) || solid(c, r + 1);
      const got = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, face);
      if (got === null) {   // the suite band (each suite draws its walls) and the gate portal's posts
        const cornerCell = (c === 0 || c === g.w - 1) && (r === 0 || r === g.h - 1);
        assert.ok(cornerCell || (m.name === 'hotel_ballroom' && c >= 1 && c <= 6) || ('GE'.includes(g.at(c - 1, r)) || 'GE'.includes(g.at(c + 1, r))), 'no module at ' + c + ',' + r);
        continue;
      }
      assert.ok(pieces.has(got), m.name + ' ' + c + ',' + r + ' ' + got);
      if (g.at(c, r) === 'n') assert.match(got, /^Door_[LMR]$/);
      // arch / lift halves come in pairs: the partner cell along the wall carries the other half
      const edgeNS = r === 0 || r === g.h - 1, edgeEW = c === 0 || c === g.w - 1;
      const mm = /^(Win|Revolve|Lift)_([AB])$/.exec(got);
      if (mm && (edgeNS || edgeEW)) {
        const flip = r === g.h - 1 || c === 0;
        const partnerPlus = (mm[2] === 'A') !== flip;   // partner at +c (N/S walls) or +r (E/W walls)
        const pc = edgeNS ? c + (partnerPlus ? 1 : -1) : c, pr = edgeNS ? r : r + (partnerPlus ? 1 : -1);
        const oface = face;
        const other = TH.wall.choose(pc, pr, true, false, hash, g, oface);
        assert.equal(other, mm[1] + '_' + (mm[2] === 'A' ? 'B' : 'A'), m.name + ' pair at ' + c + ',' + r);
      }
    }
  }
});

test('upholstery repaint cells match the kit palette order (wine -> emerald, navy, teal)', () => {
  const src = fs.readFileSync(path.join(__dirname, '../../blender/hotel_base.py'), 'utf8');
  const names = ['HULL', 'ink', 'paper', 'white', 'teal', 'amber', 'gunmetal', 'red'];
  const block = src.slice(src.indexOf("ib_lib.PALETTES[FAM] = BASE + ["), src.indexOf(']\nassert len'));
  for (const m of block.matchAll(/\('([A-Za-z0-9]+)', '#[0-9A-Fa-f]{6}'\)/g)) names.push(m[1]);
  assert.ok(names.length <= 64);
  const P = TH.symbols.L.paint;
  assert.equal(names[P.from[0]], 'wine');
  assert.deepEqual(P.to.map((t) => names[t[0]]), ['wine', 'emerald', 'navy', 'teal2']);
});

test('outside: the street drops away zone by zone, the tower closes round each zone and stair, the street under the lobby', () => {
  const B = TH.below;
  assert.equal(B.levels.length, plan.zones.length);
  for (let i = 1; i < B.levels.length; i++) assert.ok(B.levels[i] - B.levels[i - 1] >= 60, 'each zone well above the last');
  assert.ok(B.levels[0] > 0 && B.levels[0] < 1, 'the lobby a step above the street');
  assert.equal(B.depth, B.levels[B.levels.length - 1], 'the city mesh is built for the top floor');
  assert.equal(B.towerTop.length, plan.zones.length);
  B.towerTop.slice(0, -1).forEach((t, i) => {
    assert.ok(t > TH.wall.height + 2, 'wing ' + i + ' rises past its zone (its skin hides the zone from the next one)');
    assert.ok(B.levels[i] + t < B.levels[i + 1], 'and stays under the next zone, which looks down on its roof');
  });
  assert.ok(B.towerTop[B.towerTop.length - 1] < 0, 'the top zone is the roof');
  assert.ok(B.linkTop > TH.trail.height, 'the link blocks close over the service stairs');
  assert.ok(!B.bridges && !TH.showAllZones);
  assert.equal(typeof TH.backdrop.build, 'function', 'the street outside the lobby');
  assert.equal(TH.trail.byTrail.length, plan.zones.length, 'a stair sign per trail (the last one: the roof)');
  TH.trail.byTrail.forEach((t, i) => assert.ok(t.variants.includes(['TrailWall_F24', 'TrailWall_F56', 'TrailWall_FR'][i])));
});
