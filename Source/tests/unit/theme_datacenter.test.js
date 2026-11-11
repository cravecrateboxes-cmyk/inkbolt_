// Helix Vault theme (kit-datacenter): level plan and waves, zone layers (floor plan, floor finishes + wall art, ceiling
// fittings), prefab tiling, spawns and pickups, the breakable doors (each in a wall or partition line, open faces on
// both sides, hp and debris set), loot behind them (rooms reachable only through a breakable door hold lockers, every
// containment field a gun), the wall chooser (finishes from the floor in front, the video wall run, no module on a
// door cell) and the glow companions.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/datacenter.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.datacenter;
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
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const plan = IB.LEVEL_PLANS.datacenter;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const layer = (g, y) => g.layers.find((L) => Math.abs(L.y - y) < 0.001);
const SYM = TH.symbols;
const DOORS = Object.keys(SYM).filter((k) => SYM[k].breakable && SYM[k].orient === 'span');
const STAND = '.SahPEG';
const PLAN = Object.keys(SYM).filter((k) => SYM[k].collide !== false && !'-=_+:;{'.includes(k)).join('');
const FLOOR = '1234567890m,', ART = 'ipsI@!|vnt%J^&?', CEIL = '-=_+:;{';

test('datacenter theme: kit-datacenter indoors under a 6 m ceiling, three zones of hard waves', () => {
  assert.equal(TH.family, 'kit-datacenter');
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.env.ceiling.height);
  assert.equal(plan.zones.length, 3);
  let total = 0; const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; types.add(t); })));
  assert.ok(total >= 300, 'robots ' + total);
  for (const t of ['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader']) assert.ok(types.has(t), t);
  // the theme file's own counts (before tuneWaves): bombers stay at 0-2 a wave
  const src = fs.readFileSync(path.join(__dirname, '../../src/data/themes/datacenter.js'), 'utf8');
  for (const m of src.matchAll(/\['bomber', (\d+)\]/g)) assert.ok(+m[1] <= 2, 'bombers ' + m[1]);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': a very wide hall, gates, layers and their symbols, prefab tiling, spawns, pickups', () => {
    assert.ok(g.w >= 70 && g.h >= 48, name + ' ' + g.w + 'x' + g.h);
    assert.equal(g.rows[0].indexOf('GGG'), 35);
    assert.equal(g.rows[g.h - 1].indexOf('EEE'), 35);
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    for (let c = 35; c < 38; c++) for (const r of [1, 2]) assert.equal(g.at(c, r), '.', 'exit approach');
    assert.deepEqual(g.layers.map((L) => L.y), [0.01, 6]);
    const F = layer(g, 0.01), K = layer(g, 6);
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => assert.ok(('#' + STAND + PLAN).includes(ch), name + ' plan ' + ch + ' at ' + c + ',' + r)));
    F.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.') return;
      if (g.at(c, r) === '#') assert.ok(ART.includes(ch), name + ' art ' + ch + ' at ' + c + ',' + r);
      else assert.ok(FLOOR.includes(ch), name + ' floor ' + ch + ' at ' + c + ',' + r);
    }));
    K.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.') return;
      assert.ok(CEIL.includes(ch), name + ' ceiling ' + ch + ' at ' + c + ',' + r);
      assert.ok(!('#' + DOORS.join('')).includes(g.at(c, r)), name + ' fitting over a wall or door ' + c + ',' + r);
    }));
    // art codes are never symbols the layer would build
    for (const ch of ART) assert.ok(!SYM[ch], 'art code ' + ch + ' is a symbol');
    for (const G of [g, ...g.layers]) for (const [ch, d] of Object.entries(SYM)) {
      if (!d.size) continue;
      rects(G, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
      });
    }
    const P = []; let S = 0, a = 0, h = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === 'P') P.push([c, r]); if (ch === 'a') a++; if (ch === 'h') h++;
      if (ch === 'S') {
        S++;
        for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      }
    }));
    assert.deepEqual(P, [[36, g.h - 3]]);
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(a >= 2 && a <= 3 && h >= 2 && h <= 3, 'pickups ' + a + '/' + h);
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'S') assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P'); }));
  });
}

test('breakable doors: hp, debris and leaf pieces set; every door closes a wall or partition line with open faces', () => {
  const pieces = new Set(TH.allPieces());
  for (const ch of DOORS.concat(['F'])) {
    const d = SYM[ch], B = d.breakable;
    assert.ok(B.hp > 0 && ['metal', 'glass', 'mesh', 'field'].includes(B.debris), ch);
    for (const s of ['_Leaf', '_Leaf_D1', '_Leaf_D2', '_Broken']) assert.ok(pieces.has((B.leaf || d.pieces[0]) + s), ch + ' ' + s);
  }
  assert.equal(TH.wall.passage.ch, 'DuV');
  for (const ch of TH.wall.passage.ch) assert.deepEqual(SYM[ch].size, [3, 2]);
  // a gun shot is weaker than a door, a frag can at the door (x BLAST_MUL 4) breaks glass, a cage gate and a security door
  assert.ok(SYM.d.breakable.hp > 22 * 3 && SYM.d.breakable.hp < 150 * 4);
  assert.ok(SYM.c.breakable.hp < 150 * 4 * 0.6 && SYM.D.breakable.hp < 150 * 4 * 0.75 && SYM.V.breakable.hp > 150 * 4);
  let n = 0;
  for (const { name, g } of maps) {
    for (const ch of DOORS) rects(g, ch).forEach((R) => {
      n++;
      const along = R.w > R.h;   // a [3, d] door runs along X when wider than deep
      const ends = along ? [[R.c - 1, R.r], [R.c + R.w, R.r]] : [[R.c, R.r - 1], [R.c, R.r + R.h]];
      const faces = along ? [[R.c + 1, R.r - 1], [R.c + 1, R.r + R.h]] : [[R.c - 1, R.r + 1], [R.c + R.w, R.r + 1]];
      ends.forEach(([c, r]) => assert.ok('#qw'.includes(g.at(c, r)), name + ' ' + ch + ' end ' + c + ',' + r + ' is ' + g.at(c, r)));
      faces.forEach(([c, r]) => assert.ok(!'#qw'.includes(g.at(c, r)), name + ' ' + ch + ' face ' + c + ',' + r + ' is ' + g.at(c, r)));
    });
  }
  assert.ok(n >= 12, 'doors ' + n);
});

test('loot behind the doors: rooms only reachable through a breakable door hold lockers; containment fields hold guns', () => {
  let rooms = 0, loot = 0;
  for (const { name, g } of maps) {
    // flood from the entry without passing doors: every loot prefab out of reach sits in a sealed room
    const seen = new Set(), q = [];
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') { q.push([c, r]); seen.add(c + ',' + r); } }));
    while (q.length) {
      const [c, r] = q.pop();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const k = (c + dc) + ',' + (r + dr), ch = g.at(c + dc, r + dr);
        if (!seen.has(k) && (ch === '.' || 'SahPEG'.includes(ch))) { seen.add(k); q.push([c + dc, r + dr]); }
      }
    }
    for (const ch of ['W', 'g', 'j']) rects(g, ch).forEach((R) => {
      loot++;
      let near = false;
      for (let r = R.r - 1; r <= R.r + R.h; r++) for (let c = R.c - 1; c <= R.c + R.w; c++) if (seen.has(c + ',' + r)) near = true;
      if (!near) rooms++;
    });
    assert.ok(rects(g, 'F').length === 0 || SYM.F.mounts.length === 1, name);
  }
  assert.ok(loot >= 14, 'loot prefabs ' + loot);
  assert.ok(rooms >= 10, 'loot prefabs behind doors ' + rooms);
  assert.ok(SYM.W.mounts.length === 4 && SYM.W.mounts.every((m) => m[4] === 'gun'));
  assert.ok(SYM.g.mounts.every((m) => m[4] === 'item') && SYM.j.mounts.every((m) => m[4] === 'mod'));
  const T = TH.armory.tiers, sum = Object.values(T).reduce((a, b) => a + b, 0);
  assert.ok(Math.abs(sum - 100) < 1e-6 && T.orange > 0 && T.blue > 4);
});

test('wall chooser: finishes from the floor in front, video wall runs, corners, nothing on a door cell', () => {
  const pieces = new Set(TH.allPieces());
  const SOLID = '#GE' + TH.wall.passage.ch;
  let video = 0, styles = new Set();
  maps.forEach(({ name, g }) => {
    const solid = (c, r) => SOLID.includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      const cell = g.at(c, r);
      if (!SOLID.includes(cell) || 'GE'.includes(cell)) continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
      const exposed = n || [[-1, -1], [1, -1], [-1, 1], [1, 1]].some(([a, b]) => !solid(c + a, r + b));
      if (!exposed) continue;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const got = TH.wall.choose(c, r, false, false, hash, g, face);
      if (cell !== '#') { assert.equal(got, null, name + ' door cell ' + c + ',' + r); continue; }
      assert.ok(pieces.has(got), name + ' ' + c + ',' + r + ' ' + got);
      if (/^WN_Video[LMR]$/.test(got)) video++;
      const m = /^W([HNLR])(_|$)/.exec(got); if (m) styles.add(m[1]);
    }
  });
  assert.ok(video >= 9, 'video wall modules ' + video);
  for (const s of 'HNLR') assert.ok(styles.has(s), 'finish ' + s);
});

test('glow companions: every glow piece is in the kit list; racks blink in phase groups, holograms turn', () => {
  const pieces = new Set(TH.allPieces());
  for (const [k, v] of Object.entries(TH.glow)) {
    assert.ok(pieces.has(k), k);
    [].concat(v).forEach((d) => assert.ok(pieces.has(d.piece), d.piece));
  }
  assert.ok([].concat(TH.glow.RackRow_A).some((d) => d.groups === 4));
  assert.ok([].concat(TH.glow.HoloTable).some((d) => d.spin && d.blend === 'add'));
  assert.equal(typeof TH.backdrop.build, 'function');
});
