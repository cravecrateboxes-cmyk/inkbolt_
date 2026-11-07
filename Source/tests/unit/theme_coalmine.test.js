// Deep Coal Mine theme (kit-coalmine): level plan, zone maps (size, gates, reachability, spawns, prefab tiling, drifts,
// light spacing) and the wall chooser (every '#' cell resolves to a piece the kit exports; lamps / overlooks only on
// long straight runs).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/coalmine.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.coalmine;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function parse(text) {
  const rows = text.replace(/\r/g, '').split('\n').filter((r) => r.length > 0);
  const w = Math.max(...rows.map((r) => r.length));
  const padded = rows.map((r) => r.padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? '#' : padded[r][c] };
}
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const SOLID = new Set('#cuObl=LXIkTHZQC'.split(''));   // cells nobody stands in (prefabs whole); drifts, rails, decals walkable
const plan = IB.LEVEL_PLANS.coalmine;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const key = (c, r) => c + ',' + r;
// engine facing (zones.js buildWalls)
function face(g, c, r) {
  const s = (x, y) => '#GE'.includes(g.at(x, y));
  const oS = !s(c, r + 1), oN = !s(c, r - 1), oE = !s(c + 1, r), oW = !s(c - 1, r), n = oS + oN + oE + oW;
  if (n === 0) return 'none';
  if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
  return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
}

test('coalmine theme: kit-coalmine underground, walls meet the roof, gates and drifts closed above', () => {
  assert.equal(TH.family, 'kit-coalmine');
  assert.equal(TH.prefix, 'KIT_COALMINE_');
  assert.equal(TH.env.sky, null, 'no sky underground');
  assert.ok(TH.env.ceiling && TH.wall.height > TH.env.ceiling.height, 'rock walls poke above the roof');
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.env.ceiling.height);
  assert.equal(TH.wall.facing, 'open');
  assert.ok(TH.env.fog.far <= 90 && TH.env.fog.near >= 12, 'smoky fog');
  assert.equal(TH.backdrop.ring[0].count, 4);
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
  const all = new Set(TH.allPieces());
  for (const n of ['GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Stand', 'CeilRock', 'Backdrop_Cavern']) assert.ok(all.has(n), n);
});

test('coalmine level plan: three zones, 100-120 robots, all four robot types, campaign fields left to levelplans.js', () => {
  assert.equal(plan.themeId, 'coalmine');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f + ' is the campaign\'s to set');
  assert.ok(plan.name && plan.intro);
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); }));
  });
  assert.ok(total >= 100 && total <= 120, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone']) assert.ok(types.has(t), t);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, reachability, spawns, prefab tiling, drifts, lights', () => {
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
    const S = [], lights = { l: [], L: [] }; let ammo = 0, health = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'S') S.push([c, r]); if (ch === 'a') ammo++; if (ch === 'h') health++; if (lights[ch]) lights[ch].push([c, r]);
    }));
    assert.ok(S.length >= 10 && S.length <= 14, 'spawns ' + S.length);
    assert.ok(ammo >= 2 && ammo <= 3 && health >= 2 && health <= 3, 'pickups');
    for (const [c, r] of S) {
      assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14, 'spawn ' + c + ',' + r + ' >= 14 m from P');
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) if (dc || dr) assert.ok(!SOLID.has(g.at(c + dc, r + dr)), 'spawn ' + c + ',' + r + ' 3x3 open');
      assert.ok([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dc, dr]) => dist.has(key(c + dc, r + dr))), 'spawn ' + c + ',' + r + ' reachable');
    }
    // same-kind light pools never overlap (lantern posts r 2.2 m, work lights r 2.8 m)
    for (const [ch, dmin] of [['l', 5], ['L', 6]]) {
      const L = lights[ch];
      for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) assert.ok(Math.hypot(L[i][0] - L[j][0], L[i][1] - L[j][1]) >= dmin, ch + ' lights too close');
    }
    // prefab blocks tile by their size; drifts are cut through rock along both long sides
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
    for (const ch of ['Y', 'y']) {
      for (const [c, r, w, h] of blocks(ch)) {
        const sides = w === 6 ? [...Array(h).keys()].flatMap((k) => [[c - 1, r + k], [c + 6, r + k]]) : [...Array(w).keys()].flatMap((k) => [[c + k, r - 1], [c + k, r + 6]]);
        sides.forEach(([x, y]) => assert.equal(g.at(x, y), '#', name + ' drift at ' + c + ',' + r + ' open at ' + x + ',' + y));
      }
    }
    // no 1-thick rock (a module's back would show)
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      if (g.at(c, r) !== '#') continue;
      const thinV = !'#GE'.includes(g.at(c, r - 1)) && !'#GE'.includes(g.at(c, r + 1)), thinH = !'#GE'.includes(g.at(c - 1, r)) && !'#GE'.includes(g.at(c + 1, r));
      assert.ok(!thinV && !thinH, name + ' 1-thick rock at ' + c + ',' + r);
    }
  });

  test('zone ' + name + ': the wall chooser returns kit pieces; lamps and overlooks only on long straight runs', () => {
    const all = new Set(TH.allPieces());
    const wallish = (c, r) => '#GE'.includes(g.at(c, r));
    const lamps = [];
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const horiz = wallish(c - 1, r) || wallish(c + 1, r), vert = wallish(c, r - 1) || wallish(c, r + 1), F = face(g, c, r);
      const n = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, F);
      assert.ok(all.has(n), name + ' ' + c + ',' + r + ' -> ' + n);
      if (F === 'none' || F === 'corner') assert.match(n, /^Rock_Corner_/);
      if (/Lamp/.test(n)) { assert.equal(n, 'Rock_Lamp' + F); lamps.push([c, r, F]); }
      if (n === 'Rock_Open') assert.ok((c === 0 || c === g.w - 1) && (F === 'E' || F === 'W'), 'overlooks on the east / west edges');
    }
    // two lamp pools of the same facing never overlap (each reaches 2.6 m along the wall)
    for (let i = 0; i < lamps.length; i++) for (let j = i + 1; j < lamps.length; j++) {
      if (lamps[i][2] !== lamps[j][2]) continue;
      assert.ok(Math.hypot(lamps[i][0] - lamps[j][0], lamps[i][1] - lamps[j][1]) >= 6, 'lamps ' + lamps[i] + ' / ' + lamps[j]);
    }
  });
}
