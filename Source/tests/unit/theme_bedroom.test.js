// Big Bedroom theme (level 5): map rules, level plan size, wall chooser orientation, coarse reachability.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/bedroom.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.bedroom;
const PLAN = IB.LEVEL_PLANS.bedroom;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function load(name) {
  const rows = fs.readFileSync(path.join(ZDIR, name + '.txt'), 'utf8').replace(/\r/g, '').split('\n').filter(r => r.length);
  const w = Math.max(...rows.map(r => r.length));
  return { name, rows, w, h: rows.length, at: (c, r) => (r < 0 || r >= rows.length || c < 0 || c >= w) ? '#' : (rows[r][c] || '.') };
}
const MAPS = PLAN.zones.map(z => load(z.map));
const find = (g, ch) => { const o = []; g.rows.forEach((row, r) => [...row].forEach((v, c) => { if (v === ch) o.push([c, r]); })); return o; };
// cells a robot or the player can stand on (coarse: prefab collision boxes are finer than cells)
const WALK = new Set(['.', 'P', 'a', 'h', 'T', 'O', 'Y', 't', 'q', 'p', 'f', 'F', 'L', '*', 'M']);

test('level plan: three zones, 3-4 waves each, 110-130 robots of the modelled types', () => {
  assert.equal(PLAN.themeId, 'bedroom');
  assert.equal(PLAN.zones.length, 3);
  let total = 0;
  for (const z of PLAN.zones) {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    for (const w of z.waves) for (const [type, n] of w) { assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(type), type); total += n; }
  }
  assert.ok(total >= 110 && total <= 130, 'robots ' + total);
  const last = PLAN.zones[2].waves[PLAN.zones[2].waves.length - 1].reduce((s, e) => s + e[1], 0);
  assert.ok(last >= 18, 'dense final wave ' + last);
  assert.equal(PLAN.level, undefined, 'campaign numbering is set by levelplans.js');
});

test('maps: size, border, gates, entry, spawns, pickups, symbols', () => {
  const known = new Set(['#', '.', 'S', 'P', 'E', 'G', 'a', 'h', '1', '2', '3', ...Object.keys(TH.symbols)]);
  MAPS.forEach((g, i) => {
    assert.ok(g.w >= 46 && g.w <= 60 && g.h >= 40 && g.h <= 56, g.name + ' size ' + g.w + 'x' + g.h);
    assert.equal(g.at(0, 0), String(i + 1), g.name + ' wall scheme digit');
    for (const row of g.rows) for (const ch of row) assert.ok(known.has(ch), g.name + ' unknown symbol ' + ch);
    for (let c = 1; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0)), g.name + ' north wall'); assert.ok('#E'.includes(g.at(c, g.h - 1)), g.name + ' south wall'); }
    for (let r = 1; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const G = find(g, 'G'), E = find(g, 'E'), P = find(g, 'P'), S = find(g, 'S');
    assert.equal(G.length, 3); assert.ok(G.every(([c, r]) => r === 0) && G[2][0] - G[0][0] === 2, g.name + ' GGG');
    assert.equal(E.length, 3); assert.ok(E.every(([c, r]) => r === g.h - 1), g.name + ' EEE');
    for (const [c] of G) for (const r of [1, 2]) assert.ok(WALK.has(g.at(c, r)), g.name + ' open in front of the exit');
    assert.equal(P.length, 1);
    assert.ok(S.length >= 12 && S.length <= 14, g.name + ' spawns ' + S.length);
    for (const [c, r] of S) {
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, g.name + ' spawn near P at ' + c + ',' + r);
      for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(WALK.has(g.at(c + dc, r + dr)), g.name + ' spawn crowded at ' + c + ',' + r);
    }
    for (const ch of 'ah') { const n = find(g, ch).length; assert.ok(n >= 2 && n <= 3, g.name + ' ' + ch + ' ' + n); }
  });
});

test('every spawn, pickup and the exit are reachable from the entry (cell BFS)', () => {
  for (const g of MAPS) {
    const [pc, pr] = find(g, 'P')[0], seen = new Set([pc + ',' + pr]), q = [[pc, pr]];
    while (q.length) {
      const [c, r] = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const k = (c + dc) + ',' + (r + dr);
        if (!seen.has(k) && WALK.has(g.at(c + dc, r + dr))) { seen.add(k); q.push([c + dc, r + dr]); }
      }
    }
    const G = find(g, 'G');
    assert.ok(seen.has(G[1][0] + ',1'), g.name + ' exit unreachable');
    for (const [c, r] of find(g, 'S')) assert.ok([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dc, dr]) => seen.has((c + dc) + ',' + (r + dr))), g.name + ' spawn unreachable ' + c + ',' + r);
    for (const ch of 'ah') for (const [c, r] of find(g, ch)) assert.ok(seen.has(c + ',' + r), g.name + ' ' + ch + ' unreachable');
  }
});

test('wall chooser: every exposed wall cell gets an existing module whose painted face turns to the room', () => {
  const pieces = new Set(TH.allPieces());
  const WALLISH = '#GE', TURN = ['S', 'E', 'N', 'W'];
  const hash = () => 0.5;
  for (const g of MAPS) {
    const wl = (c, r) => WALLISH.includes(g.at(c, r)), sd = (c, r) => (WALLISH + '123').includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const horiz = wl(c - 1, r) || wl(c + 1, r), vert = wl(c, r - 1) || wl(c, r + 1);
      const name = TH.wall.choose(c, r, horiz, horiz && vert, hash, g);
      assert.ok(pieces.has(name), g.name + ' ' + name);
      const open = [[0, 1, 'S'], [0, -1, 'N'], [1, 0, 'E'], [-1, 0, 'W']].filter(([dc, dr]) => !sd(c + dc, r + dr)).map(o => o[2]);
      if (open.length !== 1) { assert.equal(name, 'Wall_Corner'); continue; }
      // engine yaw (zones.js buildWalls with faceOpen), in quarter turns
      let q = (!horiz && vert) ? 1 : 0;
      if (q === 0 && !wl(c, r - 1) && wl(c, r + 1)) q = 2;
      if (q !== 0 && !wl(c - 1, r) && wl(c + 1, r)) q = 3;
      const authored = name.split('_')[2];
      assert.equal(TURN[(TURN.indexOf(authored) + q) % 4], open[0], g.name + ' ' + name + ' at ' + c + ',' + r + ' faces the wall');
    }
  }
});

test('indoor environment: no sky, an 18 m ceiling with lit tiles, walls reach past it', () => {
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, 18);
  assert.equal(TH.env.ceiling.light, 'CeilingTile');
  assert.equal(TH.env.ceiling.every, 1);
  assert.ok(TH.wall.height > TH.env.ceiling.height && TH.trail.height > TH.env.ceiling.height);
  for (const ch of ['L', '*', 'M']) assert.equal(TH.symbols[ch].y, TH.env.ceiling.height);
  assert.ok(TH.budget.prop <= 2000 && TH.budget.total <= 70000);
});
