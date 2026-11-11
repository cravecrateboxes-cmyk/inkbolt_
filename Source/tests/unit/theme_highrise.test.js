// Zenith Command theme (kit-highrise, the final level): level plan, zone layers, gates, interior reachability, the
// roof zone (open air, plank sites with roofs at both ends, the exit reachable over the plank laid from the start),
// spawns, prefab tiling, the wall chooser, armory odds and the skyline table.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/highrise.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.highrise;
const ZDIR = path.join(__dirname, '../../src/data/zones');

function grid(rows, out) {
  return { w: rows[0].length, h: rows.length, rows, at: (c, r) => (r < 0 || r >= rows.length || c < 0 || c >= rows[0].length) ? out : rows[r][c] };
}
function parse(text) {
  const o = { base: [], layers: {} };
  let cur = o.base;
  text.replace(/\r/g, '').split('\n').filter((l) => l.length).forEach((l) => {
    const m = /^@layer\s+(-?[\d.]+)/.exec(l);
    if (m) { cur = []; o.layers[m[1]] = cur; } else cur.push(l);
  });
  o.g = grid(o.base, '#');
  Object.keys(o.layers).forEach((k) => { o.layers[k] = grid(o.layers[k], '.'); o.layers[k].y = parseFloat(k); });
  o.g.layers = Object.values(o.layers);
  return o;
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
const plan = IB.LEVEL_PLANS.highrise;
const maps = plan.zones.map((z) => ({ name: z.map, plan: z, ...parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const RO = TH.rooftop;
const OPEN = '.Pah';

test('highrise theme: kit-highrise, 4.5 m floors, a sky over the city, armory odds tilted to green / blue', () => {
  assert.equal(TH.family, 'kit-highrise');
  assert.equal(TH.prefix, 'KIT_HIGHRISE_');
  assert.equal(TH.wall.height, 4.5);
  assert.equal(TH.env.ceiling.height, 4.5);
  assert.equal(TH.env.sky[1], TH.env.fog.color);
  assert.equal(TH.below.haze, TH.env.fog.color);
  const T = TH.armory.tiers, tot = Object.values(T).reduce((a, b) => a + b, 0);
  assert.ok((T.green + T.blue) / tot > 0.9, 'mostly green and blue');
  assert.ok(T.purple / tot < 0.03 && T.purple > 0, 'a purple or two');
  assert.ok(Math.abs(T.orange / tot - 0.003) < 0.001, 'orange about 0.3 %');
  const Gr = TH.armory.gear; assert.ok(Gr.rare > Gr.common && Gr.epic > 0 && !Gr.legendary);
  assert.equal(RO.void, '_');
  [RO.site, RO.laid, RO.void].forEach((ch) => assert.equal(TH.symbols[ch], undefined, ch + ' is not a theme symbol'));
});

test('level plan: three zones, the roof last, the biggest waves, soldiers and gun robots on the roof', () => {
  assert.equal(plan.themeId, 'highrise');
  assert.equal(plan.zones.length, 3);
  for (const f of ['level', 'next', 'weapons', 'start']) assert.equal(plan[f], undefined, f);
  let total = 0;
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { total += n; if (t === 'bomber') assert.ok(n <= 2); })));
  assert.ok(total >= 360, 'climactic: ' + total);
  const roof = plan.zones[2], kinds = {};
  roof.waves.forEach((w) => w.forEach(([t, n]) => { kinds[t] = (kinds[t] || 0) + n; }));
  assert.ok(kinds.soldier >= 25 && kinds.gunner >= 40, JSON.stringify(kinds));
  assert.equal(roof.ceiling, false);
});

for (const m of maps.slice(0, 2)) {
  test('interior ' + m.name + ': size, layers, gates, reachability, spawns, prefab tiling', () => {
    const g = m.g;
    assert.ok(g.w >= 60 && g.h >= 54, 'bigger and wider than Strike Team HQ');
    assert.deepEqual(Object.keys(m.layers).sort(), ['0.008', '4.5']);
    const G = [...g.rows[0]].map((ch, c) => ch === 'G' ? c : -1).filter((c) => c >= 0);
    const E = [...g.rows[g.h - 1]].map((ch, c) => ch === 'E' ? c : -1).filter((c) => c >= 0);
    assert.deepEqual([G.length, E.length], [3, 3]);
    let P = null;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P = [c, r]; }));
    const seen = new Set([P.join()]), q = [P];
    while (q.length) {
      const [c, r] = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = [c + dc, r + dr]; if (seen.has(n.join()) || !OPEN.includes(g.at(...n))) continue;
        seen.add(n.join()); q.push(n);
      }
    }
    assert.ok(G.some((c) => seen.has(c + ',1')), 'P reaches the exit');
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (OPEN.includes(ch)) assert.ok(seen.has(c + ',' + r), m.name + ' sealed ' + c + ',' + r); }));
    let n = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'S') return; n++;
      assert.ok(Math.hypot(c - P[0], r - P[1]) >= 14);
      for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (dc || dr) assert.ok(OPEN.includes(g.at(c + dc, r + dr)), m.name + ' spawn ' + c + ',' + r);
    }));
    assert.ok(n >= 10 && n <= 16);
    for (const L of [g, ...Object.values(m.layers)]) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      rects(L, ch).forEach((R) => assert.ok((R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0), m.name + ' ' + ch + ' ' + JSON.stringify(R)));
    }
  });
}

test('the roof: open air, roofs within +-3 m, plank sites 3 - 7 m with roofs at both ends, the exit over the laid plank', () => {
  const m = maps[2], g = m.g, H = {};
  const SOLID = '#GE' + 'FNJMAXLWfrqz';
  for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if (!'_%$'.includes(g.at(c, r))) H[c + ',' + r] = 0;
  for (const L of g.layers) {
    if (L.y === 0.008) continue;
    assert.ok(Math.abs(L.y) <= 3, 'roof height ' + L.y);
    L.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch !== '.') { assert.equal(g.at(c, r), '_', 'deck over open air ' + c + ',' + r); H[c + ',' + r] = L.y; } }));
  }
  const links = [];
  for (const ch of [RO.site, RO.laid]) rects(g, ch).forEach((R) => {
    const z = R.h >= R.w, ends = z ? [[R.c, R.r - 1], [R.c, R.r + R.h]] : [[R.c - 1, R.r], [R.c + R.w, R.r]], span = z ? R.h : R.w;
    assert.ok(Math.min(R.w, R.h) === 2 && span >= 3 && span <= 7, JSON.stringify(R));
    ends.forEach((e) => assert.ok(e.join() in H, 'plank end on a roof ' + e));
    links.push({ ends: ends.map((e) => e.join()), laid: ch === RO.laid });
  });
  assert.equal(links.filter((l) => l.laid).length, 1);
  const cellOf = (k) => { const [c, r] = k.split(',').map(Number); const y = H[k]; const L = g.layers.find((q) => q.y === y); return y === 0 ? g.at(c, r) : L.at(c, r); };
  const free = (k) => k in H && !SOLID.includes(cellOf(k));
  let P = null; g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P = c + ',' + r; }));
  function reach(all) {
    const seen = new Set([P]), q = [P];
    while (q.length) {
      const k = q.shift(), [c, r] = k.split(',').map(Number);
      const nb = [[c + 1, r], [c - 1, r], [c, r + 1], [c, r - 1]].map((p) => p.join()).filter((n) => n in H && H[n] === H[k]);
      links.forEach((l) => { if ((all || l.laid) && l.ends.includes(k)) l.ends.forEach((e) => nb.push(e)); });
      nb.forEach((n) => { if (!seen.has(n) && free(n)) { seen.add(n); q.push(n); } });
    }
    return seen;
  }
  const base = reach(false), all = reach(true);
  const gate = [...g.rows[0]].map((ch, c) => ch === 'G' ? c + ',1' : null).filter(Boolean);
  assert.ok(gate.some((k) => base.has(k)), 'exit reachable without any robot-thrown plank');
  Object.keys(H).forEach((k) => { if (free(k)) assert.ok(all.has(k), 'roof cell ' + k + ' reachable with every plank'); });
});

test('wall chooser: every wall cell of every zone resolves to a kit piece', () => {
  const pieces = new Set(TH.allPieces()), SOLID = '#GE';
  for (const m of maps) {
    const g = m.g, solid = (c, r) => SOLID.includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
      if (!n && ![[-1, -1], [1, -1], [-1, 1], [1, 1]].some(([a, b]) => !solid(c + a, r + b))) continue;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const horiz = solid(c - 1, r) || solid(c + 1, r), vert = solid(c, r - 1) || solid(c, r + 1);
      const got = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, face);
      assert.ok(pieces.has(got), m.name + ' ' + c + ',' + r + ' ' + got);
    }
  }
});

test('outside: the skyline table, the city below, a top for every zone tower and the exit core', () => {
  const ring = TH.backdrop.ring[0];
  ring.pieces.forEach((p) => assert.ok(TH.allPieces().includes(p) && Array.isArray(TH.skyline[p]), p));
  assert.equal(TH.below.skyline, TH.skyline);
  assert.equal(TH.below.towerTop.length, plan.zones.length + 1);
  assert.ok(TH.below.depth >= 200 && TH.rooftop.depth === TH.below.depth, 'the gaps fall to the street');
});
