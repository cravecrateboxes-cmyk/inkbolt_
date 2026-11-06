// Office Skyscraper theme (kit-office): level plan, zone maps (size, gates, reachability, spawns, prefab tiling)
// and the wall chooser (every '#' cell resolves to a piece the kit exports).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/office.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.office;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function parse(text) {
  const rows = text.replace(/\r/g, '').split('\n').filter((r) => r.length > 0);
  const w = Math.max(...rows.map((r) => r.length));
  const padded = rows.map((r) => r.padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? '#' : padded[r][c] };
}
// same hash as zones.js
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const SOLID = new Set('#=cFrkfwKbMDLTRpS'.split(''));   // cells nobody stands in (prefabs counted whole)
const plan = IB.LEVEL_PLANS.office;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));

test('office theme registers kit-office with a ceiling, sky and skyline', () => {
  assert.equal(TH.family, 'kit-office');
  assert.equal(TH.prefix, 'KIT_OFFICE_');
  assert.ok(TH.env.ceiling && TH.env.ceiling.height === TH.wall.height, 'walls reach the ceiling');
  assert.ok(Array.isArray(TH.env.sky), 'daylight sky outside the windows');
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.env.ceiling.height);
  assert.equal(TH.backdrop.ring[0].count, 4, 'skyline slices due east, south, west and north');
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
});

test('office level plan: three zones, 100-115 robots, all four robot types, no campaign fields set here', () => {
  assert.equal(plan.themeId, 'office');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f + ' is the campaign\'s to set');
  assert.ok(plan.name && plan.intro);
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); }));
  });
  assert.ok(total >= 100 && total <= 115, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone']) assert.ok(types.has(t), t);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, reachability, spawns, prefab tiling', () => {
    assert.ok(g.w >= 44 && g.w <= 60 && g.h >= 40 && g.h <= 56, name + ' ' + g.w + 'x' + g.h);
    for (let c = 0; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0)), 'north edge'); assert.ok('#E'.includes(g.at(c, g.h - 1)), 'south edge'); }
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const G = [...g.rows[0]].map((ch, c) => ch === 'G' ? c : -1).filter((c) => c >= 0);
    const E = [...g.rows[g.h - 1]].map((ch, c) => ch === 'E' ? c : -1).filter((c) => c >= 0);
    assert.deepEqual([G.length, G[2] - G[0]], [3, 2], 'GGG');
    assert.deepEqual([E.length, E[2] - E[0]], [3, 2], 'EEE');
    G.forEach((c) => { assert.ok(!SOLID.has(g.at(c, 1)) && !SOLID.has(g.at(c, 2)), 'two open rows before the exit'); });
    E.forEach((c) => assert.ok(!SOLID.has(g.at(c, g.h - 2)), 'open in front of the entry'));
    let P = null;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') { assert.equal(P, null, 'one P'); P = [c, r]; } }));
    assert.ok(P, 'P');
    // BFS over open cells from P
    const dist = new Map(); const key = (c, r) => c + ',' + r; const q = [P]; dist.set(key(...P), 0);
    while (q.length) {
      const [c, r] = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = [c + dc, r + dr];
        if (n[0] < 1 || n[1] < 1 || n[0] >= g.w - 1 || n[1] >= g.h - 1 || dist.has(key(...n)) || SOLID.has(g.at(...n))) continue;
        dist.set(key(...n), dist.get(key(c, r)) + 1); q.push(n);
      }
    }
    assert.ok(G.some((c) => dist.has(key(c, 1))), 'P reaches the exit gate');
    const S = [], ammo = [], health = [];
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'S') S.push([c, r]); if (ch === 'a') ammo.push(1); if (ch === 'h') health.push(1); }));
    assert.ok(S.length >= 10 && S.length <= 14, 'spawns ' + S.length);
    assert.ok(ammo.length >= 2 && ammo.length <= 3 && health.length >= 2 && health.length <= 3, 'pickups');
    for (const [c, r] of S) {
      assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14, 'spawn ' + c + ',' + r + ' >= 14 m from P');
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) if (dc || dr) assert.ok(!SOLID.has(g.at(c + dc, r + dr)), 'spawn ' + c + ',' + r + ' 3x3 open');
      assert.ok([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dc, dr]) => dist.has(key(c + dc, r + dr))), 'spawn ' + c + ',' + r + ' reachable');
    }
    // every prefab block tiles by its size (either way round), so no piece is stretched or overlaps another
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      const seen = new Set();
      for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
        if (g.at(c, r) !== ch || seen.has(key(c, r))) continue;
        let w = 0; while (g.at(c + w, r) === ch && !seen.has(key(c + w, r))) w++;
        let h = 0; while ([...Array(w).keys()].every((k) => g.at(c + k, r + h) === ch && !seen.has(key(c + k, r + h)))) h++;
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen.add(key(c + x, r + y));
        const [sw, sd] = d.size;
        assert.ok((w % sw === 0 && h % sd === 0) || (w % sd === 0 && h % sw === 0), name + ' ' + ch + ' block ' + w + 'x' + h + ' at ' + c + ',' + r);
      }
    }
  });

  test('zone ' + name + ': the wall chooser returns kit pieces for every wall cell', () => {
    const all = new Set(TH.allPieces());
    const wallish = (c, r) => '#GE'.includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const horiz = wallish(c - 1, r) || wallish(c + 1, r), vert = wallish(c, r - 1) || wallish(c, r + 1);
      const n = TH.wall.choose(c, r, horiz, horiz && vert, hash, g);
      assert.ok(all.has(n), name + ' ' + c + ',' + r + ' -> ' + n);
      // east / west facade cells come pre-turned while the engine counts the outside as wall
      if ((c === 0 || c === g.w - 1) && r > 0 && r < g.h - 1 && /^Win/.test(n)) assert.match(n, c === 0 ? /_W$/ : /_E$/);
    }
  });
}
