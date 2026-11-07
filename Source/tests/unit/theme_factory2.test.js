// Heavy Works theme (kit-factory2): level plan, zone maps (size, gates, reachability, spawns, prefab tiling, full-length
// build lines), the moving lines (stage chains, stations, loop path) and the wall chooser (every '#' cell resolves to a
// kit piece; open clerestory windows only on the zone edge and never beside a gate frame).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/factory2.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.factory2;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function parse(text) {
  const rows = text.replace(/\r/g, '').split('\n').filter((r) => r.length > 0);
  const w = Math.max(...rows.map((r) => r.length));
  const padded = rows.map((r) => r.padEnd(w, '.'));
  return { w, h: padded.length, rows: padded, at: (c, r) => (r < 0 || r >= padded.length || c < 0 || c >= w) ? '#' : padded[r][c] };
}
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const SOLID = new Set('#=LUCXMlpwTDcbx'.split(''));   // cells nobody stands in (prefabs whole); hazard pads walkable
const plan = IB.LEVEL_PLANS.factory2;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const key = (c, r) => c + ',' + r;
function face(g, c, r) {
  const s = (x, y) => '#GE'.includes(g.at(x, y));
  const oS = !s(c, r + 1), oN = !s(c, r - 1), oE = !s(c + 1, r), oW = !s(c - 1, r), n = oS + oN + oE + oW;
  if (n === 0) return 'none';
  if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
  return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
}
const blocks = (g, ch) => {
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

test('factory2 theme: its own kit and look, tall halls, walls meet the roof, dusk outside, backdrop ring', () => {
  assert.equal(TH.family, 'kit-factory2');
  assert.equal(TH.prefix, 'KIT_FACTORY2_');
  assert.notDeepEqual(TH.palette, IB.THEME_DEFS.factory ? IB.THEME_DEFS.factory.palette : [], 'its own palette');
  assert.ok(Array.isArray(TH.env.sky), 'sky outside the windows');
  assert.ok(TH.env.ceiling.height >= 14, 'a taller plant than Robot Works');
  assert.ok(TH.wall.height > TH.env.ceiling.height, 'walls poke above the roof');
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.env.ceiling.height);
  assert.equal(TH.wall.facing, 'open');
  assert.ok(Array.isArray(TH.env.ceiling.light) && TH.env.ceiling.light.some((n) => /Plate|Leg/.test(n)), 'some roof bays carry a crane');
  assert.equal(TH.backdrop.ring[0].count, 4);
  TH.palette.forEach((c) => assert.match(c, /^#[0-9A-F]{6}$/));
  const all = new Set(TH.allPieces());
  for (const n of ['GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Stand', 'CeilBay', 'Backdrop_Heavy', 'Landmark_Titan', 'TestTrack'].concat(TH.env.ceiling.light)) assert.ok(all.has(n), n);
});

test('factory2 moving lines: walker and bruiser lines go through four stages in booths, belts have hoods, the test track loops', () => {
  for (const ch of ['L', 'U']) {
    const d = TH.symbols[ch], C = d.conveyor;
    assert.deepEqual(d.size, [14, 8]);
    assert.equal(d.sequence, 'run');
    assert.deepEqual(d.pieces, ['Jig_Feed', 'Jig_Armour', 'Jig_Paint', 'Jig_Dispatch']);
    assert.equal(C.items.length, 1);
    const chain = C.items[0];
    assert.equal(chain.length, 4, 'frame -> drivetrain -> armour -> paint');
    assert.match(chain[0], /_Frame$/); assert.match(chain[1], /_Drive$/); assert.match(chain[2], /_Armour$/); assert.match(chain[3], /_Paint$/);
    assert.equal(Object.keys(C.stations).length, chain.length - 1, 'one booth per stage change');
    for (const p of Object.keys(C.stations)) assert.ok(d.pieces.includes(p), p);
    assert.ok(C.inset >= 2 && C.speed > 0 && C.spacing >= 4.5, 'items pop inside the houses and never overlap');
    assert.ok(C.cleat, 'moving track slats');
  }
  const B = TH.symbols['='].conveyor;
  assert.ok(B.ends.start && B.ends.end && B.items.length >= 3 && B.cleat && B.carry);
  const T = TH.symbols.T.conveyor;
  assert.ok(Array.isArray(T.path) && T.path.length >= 8, 'test track loop');
  for (const [x, z] of T.path) assert.ok(Math.abs(x) < 7.6 && Math.abs(z) < 5.6, 'loop inside the track fence');
  const all = new Set(TH.allPieces());
  for (const ch of Object.keys(TH.symbols)) for (const n of IB.conveyorPieces(TH.symbols[ch].conveyor)) assert.ok(all.has(n), 'allPieces lists ' + n);
});

test('factory2 level plan: three zones, 125-145 robots, the modelled robot types, campaign fields left to levelplans.js', () => {
  assert.equal(plan.themeId, 'factory2');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f + ' is the campaign\'s to set');
  assert.ok(plan.name && plan.intro);
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => {
    assert.ok(z.waves.length >= 3 && z.waves.length <= 4, z.map + ' waves');
    z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); }));
  });
  assert.ok(total >= 125 && total <= 145, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone']) assert.ok(types.has(t), t);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, reachability, spawns, prefab tiling, a full build line', () => {
    assert.ok(g.w >= 56 && g.w <= 64 && g.h >= 48 && g.h <= 58, name + ' ' + g.w + 'x' + g.h);
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
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) if (!SOLID.has(g.at(c, r)) && !'GE'.includes(g.at(c, r))) assert.ok(dist.has(key(c, r)), 'open cell ' + c + ',' + r + ' reachable');
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
    for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      const [sw, sd] = d.size;
      for (const [c, r, w, h] of blocks(g, ch)) assert.ok((w % sw === 0 && h % sd === 0) || (w % sd === 0 && h % sw === 0), name + ' ' + ch + ' block ' + w + 'x' + h + ' at ' + c + ',' + r);
    }
    // exactly one build line, a full run of four tiles laid east-west (feed house west, dispatch house east)
    const lines = blocks(g, 'L').concat(blocks(g, 'U'));
    assert.equal(lines.length, 1, 'one build line');
    assert.deepEqual(lines[0].slice(2), [56, 8], 'four 14 x 8 tiles in a row');
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      if (g.at(c, r) !== '#') continue;
      const thinV = !'#GE'.includes(g.at(c, r - 1)) && !'#GE'.includes(g.at(c, r + 1)), thinH = !'#GE'.includes(g.at(c - 1, r)) && !'#GE'.includes(g.at(c + 1, r));
      assert.ok(!thinV && !thinH, name + ' 1-thick wall at ' + c + ',' + r);
    }
  });

  test('zone ' + name + ': the wall chooser returns kit pieces; windows only on the edge, none beside the gates', () => {
    const all = new Set(TH.allPieces());
    const wallish = (c, r) => '#GE'.includes(g.at(c, r));
    let wins = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const horiz = wallish(c - 1, r) || wallish(c + 1, r), vert = wallish(c, r - 1) || wallish(c, r + 1), F = face(g, c, r);
      const n = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, F);
      assert.ok(all.has(n), name + ' ' + c + ',' + r + ' -> ' + n);
      if (F === 'none' || F === 'corner') assert.equal(n, 'Corner');
      const edge = c === 0 || r === 0 || c === g.w - 1 || r === g.h - 1;
      if (/^Wall_Win/.test(n)) {
        wins++;
        assert.ok(edge, 'window at ' + c + ',' + r + ' is on the zone edge');
        for (const dc of [-2, -1, 1, 2]) { const ch = g.at(c + dc, r); assert.ok(r > 0 && r < g.h - 1 || (ch !== 'G' && ch !== 'E'), 'window beside a gate at ' + c + ',' + r); }
      }
      if (!edge && F !== 'none' && F !== 'corner') assert.match(n, /^Block_/);
    }
    assert.ok(wins > 80, 'clerestory windows ' + wins);
  });
}
