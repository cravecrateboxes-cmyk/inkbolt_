// Lagoon Island theme (kit-island): level plan, zone maps (size, edges, sea walls, gates, reachability, spawns,
// prefab tiling) and the wall chooser (every '#' cell resolves to a kit piece, or to nothing only where a gate frame
// or a neighbouring 2 m module covers it).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/island.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.island;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function parse(text) {
  const rows = text.replace(/\r/g, '').split('\n').filter((r) => r.length > 0);
  const w = Math.max(...rows.map((r) => r.length));
  const padded = rows.map((r) => r.padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? '#' : padded[r][c] };
}
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
// cells nobody stands in (prefabs whole, except the walkable water / grass / dune patches and reeds)
const SOLID = new Set('#{}GEoOcbtFxf=puBHLTRAQK'.split(''));
const WALKABLE_SYMBOLS = ['W', 'w', 'M', 'D', 'r'];
const plan = IB.LEVEL_PLANS.island;
const maps = plan.zones.map((z) => ({ name: z.map, sea: z.sea, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const key = (c, r) => c + ',' + r;

test('island theme: kit-island outdoors, sky and sea-haze fog, coded island backdrop, wall chooser facing the open side', () => {
  assert.equal(TH.family, 'kit-island');
  assert.equal(TH.prefix, 'KIT_ISLAND_');
  assert.ok(Array.isArray(TH.env.sky) && TH.env.clouds, 'sky and clouds');
  assert.equal(TH.env.ceiling, null);
  assert.equal(TH.env.fog.color, TH.env.sky[1], 'fog = horizon colour: the ocean runs out into the sky');
  assert.equal(TH.wall.facing, 'open');
  assert.equal(typeof TH.wall.choose, 'function');
  assert.equal(typeof TH.backdrop.build, 'function', 'island ground + sea built by the theme');
  assert.ok(TH.wall.height >= 4, 'walls higher than a double jump');
  assert.ok(TH.floor.trailLines && TH.floor.trailLines.length, 'boardwalk planks on the trails');
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
  const all = new Set(TH.allPieces());
  for (const n of ['GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Crate_A', 'SeaWall_A', 'Corner_A', 'Jungle_A', 'Jungle_1',
    'Lagoon', 'Pond_A', 'TidePool_A', 'Landmark_Lighthouse', 'Landmark_Outpost', 'Landmark_Lookout', 'Landmark_Hut',
    'Jetty', 'Boat_A', 'Backdrop_Islet_A', 'Backdrop_Buoy', 'Sea_Glint']) assert.ok(all.has(n), n);
  // sea walls: turned so their beach face looks into the zone, taller than a double jump, solid
  assert.equal(TH.symbols['{'].rotate, Math.PI / 2);
  assert.equal(TH.symbols['}'].rotate, -Math.PI / 2);
  for (const s of ['{', '}']) { assert.ok(TH.symbols[s].h >= 4); assert.notEqual(TH.symbols[s].collide, false); }
  // wadeable water and ground patches carry no collision (the nav grid stays open over them)
  for (const s of WALKABLE_SYMBOLS) assert.equal(TH.symbols[s].collide, false, s + ' is walkable');
});

test('island level plan: three zones, 125-140 robots in 4 waves each, all four robot types, sea sides named', () => {
  assert.equal(plan.themeId, 'island');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f + ' is the campaign\'s to set');
  assert.ok(plan.name && plan.intro);
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => {
    assert.equal(z.waves.length, 4, z.map + ' waves');
    assert.ok(z.sea === 'E' || z.sea === 'W', z.map + ' faces the sea');
    z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); }));
  });
  assert.ok(total >= 125 && total <= 140, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone']) assert.ok(types.has(t), t);
  const last = plan.zones[2].waves[3].reduce((s, [, n]) => s + n, 0);
  assert.ok(last >= 15, 'a dense finale wave');
});

for (const { name, sea, g } of maps) {
  test('zone ' + name + ': size, edges and sea wall, gates, reachability, spawns, prefab tiling', () => {
    assert.ok(g.w >= 56 && g.w <= 64 && g.h >= 48 && g.h <= 58, name + ' ' + g.w + 'x' + g.h);
    assert.ok(g.w * g.h >= 3200, 'wide zone');
    for (let c = 0; c < g.w; c++) { assert.ok('#G'.includes(g.at(c, 0)), 'north edge'); assert.ok('#E'.includes(g.at(c, g.h - 1)), 'south edge'); }
    const seaCol = sea === 'E' ? g.w - 1 : 0, landCol = sea === 'E' ? 0 : g.w - 1, seaCh = sea === 'E' ? '}' : '{';
    for (let r = 1; r < g.h - 1; r++) { assert.equal(g.at(seaCol, r), seaCh, 'sea wall at ' + seaCol + ',' + r); assert.equal(g.at(landCol, r), '#'); }
    // every wall is on the edge, one cell thick (no interior walls, no roofs)
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) assert.ok(!'#{}'.includes(g.at(c, r)), 'interior wall at ' + c + ',' + r);
    const G = [...g.rows[0]].map((ch, c) => ch === 'G' ? c : -1).filter((c) => c >= 0);
    const E = [...g.rows[g.h - 1]].map((ch, c) => ch === 'E' ? c : -1).filter((c) => c >= 0);
    assert.deepEqual(G, [30, 31, 32], 'GGG on columns 30-32 (the zones line up)');
    assert.deepEqual(E, [30, 31, 32], 'EEE on columns 30-32');
    G.forEach((c) => { assert.ok(!SOLID.has(g.at(c, 1)) && !SOLID.has(g.at(c, 2)), 'two open rows before the exit'); });
    E.forEach((c) => assert.ok(!SOLID.has(g.at(c, g.h - 2)) && !SOLID.has(g.at(c, g.h - 3)), 'open in front of the entry'));
    let P = null;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') { assert.equal(P, null, 'one P'); P = [c, r]; } }));
    assert.ok(P, 'P');
    for (const dc of [-2, -1, 1, 2]) assert.ok(!SOLID.has(g.at(P[0] + dc, P[1] - 4)), 'weapon stand spot clear');
    const dist = new Map(); const q = [P]; dist.set(key(...P), 0);
    while (q.length) {
      const [c, r] = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = [c + dc, r + dr];
        if (n[0] < 1 || n[1] < 1 || n[0] >= g.w - 1 || n[1] >= g.h - 1 || dist.has(key(...n)) || SOLID.has(g.at(...n))) continue;
        dist.set(key(...n), dist.get(key(c, r)) + 1); q.push(n);
      }
    }
    assert.ok(G.some((c) => dist.has(key(c, 1))), 'P reaches the exit gate');
    let open = 0, sealed = 0;
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) if (!SOLID.has(g.at(c, r))) { open++; if (!dist.has(key(c, r))) sealed++; }
    assert.equal(sealed, 0, 'every open cell reachable (' + open + ' open)');
    const S = []; let ammo = 0, health = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'S') S.push([c, r]); if (ch === 'a') ammo++; if (ch === 'h') health++;
    }));
    assert.ok(S.length >= 10 && S.length <= 14, 'spawns ' + S.length);
    assert.ok(ammo >= 2 && ammo <= 3 && health >= 2 && health <= 3, 'pickups');
    for (const [c, r] of S) {
      assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14, 'spawn ' + c + ',' + r + ' >= 14 m from P');
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) if (dc || dr) assert.ok(!SOLID.has(g.at(c + dc, r + dr)), 'spawn ' + c + ',' + r + ' 3x3 open');
    }
    const blocks = (ch) => {
      const seen = new Set(), out = [];
      for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
        if (g.at(c, r) !== ch || seen.has(key(c, r))) continue;
        let w = 0; while (g.at(c + w, r) === ch && !seen.has(key(c + w, r))) w++;
        let h = 0; while ([...Array(w).keys()].every((k) => g.at(c + k, r + h) === ch && !seen.has(key(c + k, r + h)))) h++;
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen.add(key(c + x, r + y));
        out.push([c, r, w, h]);
      }
      return out;
    };
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      const [sw, sd] = d.size;
      for (const [c, r, w, h] of blocks(ch)) assert.ok((w === sw && h === sd) || (w === sd && h === sw), name + ' ' + ch + ' block ' + w + 'x' + h + ' at ' + c + ',' + r + ' is one ' + sw + 'x' + sd + ' prefab');
    }
    // the big lagoon only in the lagoon zone; landmarks where the story puts them
    const count = (ch) => g.rows.reduce((n, row) => n + row.split(ch).length - 1, 0);
    if (name === 'island_lagoon') assert.equal(count('V'), 140, 'one 14 x 10 lagoon');
    if (name === 'island_point') { assert.equal(count('L'), 36, 'the lighthouse'); assert.equal(count('R'), 35, 'the outpost lab'); }
    assert.ok(count('W') + count('w') + count('V') >= 32, 'pools and lakes all over');
  });

  test('zone ' + name + ': the wall chooser returns kit pieces and leaves no gaps in a run', () => {
    const all = new Set(TH.allPieces());
    let mods = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const n = TH.wall.choose(c, r, true, false, hash, g);
      if (n === null) {
        // only beside a gate (the frame's jambs) or on an odd cell between two 2 m modules
        const gate = (r === 0 || r === g.h - 1) && [-1, 1].some((d) => 'GE'.includes(g.at(c + d, r)));
        const along = r === 0 || r === g.h - 1;
        const nb = along ? [TH.wall.choose(c - 1, r, true, false, hash, g), TH.wall.choose(c + 1, r, true, false, hash, g)]
          : [TH.wall.choose(c, r - 1, true, false, hash, g), TH.wall.choose(c, r + 1, true, false, hash, g)];
        assert.ok(gate || nb.every((x) => x && /_(A|B)$/.test(x) && !/^Corner/.test(x)), name + ' gap at ' + c + ',' + r + ' between ' + nb);
        continue;
      }
      assert.ok(all.has(n), name + ' ' + c + ',' + r + ' -> ' + n);
      mods++;
    }
    assert.ok(mods > 70, 'wall modules ' + mods);
  });
}

test('island is in the campaign after the living room', () => {
  require('../../src/data/levelplans.js');
  assert.ok(IB.CAMPAIGN.includes('island'));
  assert.equal(IB.LEVEL_PLANS.island.level, IB.CAMPAIGN.indexOf('island') + 1);
  assert.ok(IB.CAMPAIGN.indexOf('island') > IB.CAMPAIGN.indexOf('livingroom'));
});
