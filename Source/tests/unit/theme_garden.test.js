// Wide Garden Playground theme (kit-garden): level plan, zone maps (size, gates, reachability, spawns, prefab tiling,
// a playground in every garden, the big fort in the middle one), the wall chooser, and the kit's walkable collision
// boxes (<Piece>_WCOL<n>: decks, steps and planks robots may walk on; see src/game/zones.js).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/garden.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.garden;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function parse(text) {
  const rows = text.replace(/\r/g, '').split('\n').filter((r) => r.length > 0);
  const w = Math.max(...rows.map((r) => r.length));
  const padded = rows.map((r) => r.padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? '#' : padded[r][c] };
}
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
// cells nobody stands in on the map (prefabs counted whole; paths, paving and the rubber surface are floor)
const SOLID = new Set('#tf=-oildbkFZHQWwMTUXY'.split(''));
const plan = IB.LEVEL_PLANS.garden;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const key = (c, r) => c + ',' + r;
function face(g, c, r) {
  const s = (x, y) => '#GE'.includes(g.at(x, y));
  const oS = !s(c, r + 1), oN = !s(c, r - 1), oE = !s(c + 1, r), oW = !s(c - 1, r), n = oS + oN + oE + oW;
  if (n === 0) return 'none';
  if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
  return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
}

test('garden theme: kit-garden park, open sky, hedge walls as tall as the trail, playground symbols', () => {
  assert.equal(TH.family, 'kit-garden');
  assert.equal(TH.prefix, 'KIT_GARDEN_');
  assert.ok(Array.isArray(TH.env.sky) && TH.env.clouds && TH.env.ceiling === null, 'outdoors');
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.wall.height);
  assert.equal(TH.wall.facing, 'open');
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
  const all = new Set(TH.allPieces());
  for (const n of ['GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Stand', 'Landmark_PlayTower', 'Landmark_PlayFort', 'Landmark_PlayFortLinks',
    'Landmark_PlayShip', 'Landmark_Gazebo', 'Landmark_Fountain', 'Swings', 'Seesaw', 'MonkeyBars', 'Sandpit', 'Backdrop_Trees', 'Backdrop_Houses']) assert.ok(all.has(n), n);
  assert.deepEqual(TH.symbols.X.with, { Landmark_PlayFort: ['Landmark_PlayFortLinks'] }, 'the fort is placed as two pieces');
});

test('garden level plan: three zones, 115-135 robots, all four robot types, campaign fields left to levelplans.js', () => {
  assert.equal(plan.themeId, 'garden');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f + ' is the campaign\'s to set');
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); }));
  });
  assert.ok(total >= 115 && total <= 135, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone']) assert.ok(types.has(t), t);
});

test('a playground in every garden, the big fort in the middle one', () => {
  const has = (g, ch) => g.rows.some((row) => row.includes(ch));
  maps.forEach(({ name, g }) => assert.ok('TUXY'.split('').some((ch) => has(g, ch)), name + ' has a playground'));
  assert.ok(has(maps[1].g, 'X'), 'the fort stands in the middle garden');
  assert.ok(!has(maps[0].g, 'X') && !has(maps[2].g, 'X'));
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, reachability, spawns, prefab tiling', () => {
    assert.ok(g.w >= 44 && g.w <= 60 && g.h >= 40 && g.h <= 56, name + ' ' + g.w + 'x' + g.h);
    assert.ok(g.w * g.h >= 2000, 'big zone');
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
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      if (!SOLID.has(g.at(c, r))) assert.ok(dist.has(key(c, r)), name + ' open cell ' + c + ',' + r + ' reachable');
    }
    const S = []; let ammo = 0, health = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'S') S.push([c, r]); if (ch === 'a') ammo++; if (ch === 'h') health++; }));
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
      for (const [c, r, w, h] of blocks(ch)) assert.ok((w % sw === 0 && h % sd === 0) || (w % sd === 0 && h % sw === 0), name + ' ' + ch + ' block ' + w + 'x' + h + ' at ' + c + ',' + r);
    }
    // the playgrounds (exact footprint, not rotated: their stairs face the way the map was drawn)
    for (const ch of 'TUXY') for (const [c, r, w, h] of blocks(ch)) assert.deepEqual([w, h], TH.symbols[ch].size, name + ' ' + ch + ' footprint at ' + c + ',' + r);
  });

  test('zone ' + name + ': the wall chooser returns hedge pieces; empty only for the gate piers', () => {
    const all = new Set(TH.allPieces());
    const wallish = (c, r) => '#GE'.includes(g.at(c, r));
    let empty = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const horiz = wallish(c - 1, r) || wallish(c + 1, r), vert = wallish(c, r - 1) || wallish(c, r + 1), F = face(g, c, r);
      const n = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, F);
      if (n === null) {
        empty++;
        assert.ok((r === 0 && ('G'.includes(g.at(c - 1, r)) || 'G'.includes(g.at(c + 1, r)))) || (r === g.h - 1 && ('E'.includes(g.at(c - 1, r)) || 'E'.includes(g.at(c + 1, r)))), 'empty cell beside a gate ' + c + ',' + r);
        continue;
      }
      assert.ok(all.has(n), name + ' ' + c + ',' + r + ' -> ' + n);
      if (F === 'none' || F === 'corner') assert.equal(n, 'Hedge_Corner');
    }
    assert.equal(empty, 4, 'two pier cells beside each gate');
  });
}

test('kit-garden: the playground pieces carry walkable collision boxes, the props only solid ones', () => {
  const d = fs.readFileSync(path.join(__dirname, '../../assets/fps-kit-garden.glb'));
  const len = d.readUInt32LE(12), g = JSON.parse(d.toString('utf8', 20, 20 + len));
  const kids = (n) => { const node = g.nodes.find((x) => x.name === 'KIT_GARDEN_' + n); assert.ok(node, n); return (node.children || []).map((i) => g.nodes[i].name); };
  for (const n of ['Landmark_PlayTower', 'Landmark_PlayFort', 'Landmark_PlayFortLinks', 'Landmark_PlayShip', 'Landmark_Gazebo', 'Sandpit']) {
    assert.ok(kids(n).some((k) => /_WCOL\d+$/.test(k)), n + ' has walkable boxes');
  }
  for (const n of ['Bench', 'Tree_Oak', 'Landmark_Fountain', 'Shed', 'Swings']) {
    const k = kids(n);
    assert.ok(k.some((x) => /_COL\d+$/.test(x)) && !k.some((x) => /_WCOL\d+$/.test(x)), n + ' solid only');
  }
  // every walkable step rises at most 0.35 m (the player's step-up): the fort links' step tops, sorted, never jump
  const tops = kids('Landmark_PlayFortLinks').filter((k) => /_WCOL/.test(k)).map((k) => { const n = g.nodes.find((x) => x.name === k); return n.translation[1] + (n.scale ? n.scale[1] : 1); });
  assert.ok(tops.length > 40, 'fort links steps ' + tops.length);
  assert.ok(Math.max(...tops) <= 2.75 && Math.min(...tops) > 0, 'step tops within the deck heights');
});
