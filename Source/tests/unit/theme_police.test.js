// Strike Team HQ theme (kit-police): level plan, zone maps (floor plan + floor layer + ceiling layer: size, gates,
// reachability, spawns, prefab tiling, finishes everywhere), the wall chooser (room styles, art codes, runs) and the
// armory mounts (guns rest in front of the rack board, plates sit clear of the slot).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/police.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.police;
const ZDIR = path.join(__dirname, '../../src/data/zones');

// mirrors zones.js Z.parse: the floor plan, then "@layer <y>" grids of the same size
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
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
const plan = IB.LEVEL_PLANS.police;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const PREFAB = Object.keys(TH.symbols).filter((k) => TH.symbols[k].size);
const FLOOR = new Set('12345678/^,-|_:M09%');
const CEIL = new Set('ij=!+~;{}$[]');

test('police theme: kit-police, indoor ceiling, zones light themselves, three zones of 100+ robots', () => {
  assert.equal(TH.family, 'kit-police');
  assert.equal(TH.env.ceiling.height, TH.wall.height);
  assert.equal(TH.trail.height, TH.wall.height);
  assert.ok(TH.gate.height <= TH.env.ceiling.height);
  assert.equal(plan.zones.length, 3);
  let total = 0;
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([, n]) => { total += n; })));
  assert.ok(total >= 100, 'robots ' + total);
  // the auto ceiling lights skip every cell a floor plan can hold (the corridors keep them)
  for (const { g } of maps) for (const row of g.rows) for (const ch of row) assert.ok(TH.env.ceiling.clear.includes(ch), 'clear ' + ch);
});

for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, layers, reachability, spawns, prefab tiling', () => {
    assert.ok(g.w >= 44 && g.h >= 44 && g.w * g.h >= 2000, name + ' ' + g.w + 'x' + g.h);
    assert.equal(g.rows[0].slice(23, 26), 'GGG');
    assert.equal(g.rows[g.h - 1].slice(23, 26), 'EEE');
    for (let r = 0; r < g.h; r++) { assert.equal(g.at(0, r), '#'); assert.equal(g.at(g.w - 1, r), '#'); }
    const [F, K] = g.layers;
    assert.ok(F && F.y > 0 && F.y < 0.02, 'floor layer just above the floor');
    assert.ok(K && K.y === TH.env.ceiling.height, 'ceiling layer at the ceiling');
    const P = [];
    const open = (c, r) => g.at(c, r) === '.' || 'Pah'.includes(g.at(c, r));
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      const b = g.at(c, r);
      if (b === 'P') P.push([c, r]);
      if (!'#GE'.includes(b)) assert.ok(FLOOR.has(F.at(c, r)), name + ' floor finish at ' + c + ',' + r);
      if (K.at(c, r) !== '.') {
        assert.ok(CEIL.has(K.at(c, r)), name + ' ceiling symbol ' + K.at(c, r));
        assert.notEqual(b, '#', name + ' ceiling piece over a wall at ' + c + ',' + r);
      }
    }
    assert.equal(P.length, 1);
    const seen = new Set([P[0].join()]), q = [P[0]];
    while (q.length) {
      const [c, r] = q.shift();
      for (const [dc, dr] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = [c + dc, r + dr];
        if (!seen.has(n.join()) && open(...n)) { seen.add(n.join()); q.push(n); }
      }
    }
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) if (open(c, r)) assert.ok(seen.has(c + ',' + r), name + ' sealed cell ' + c + ',' + r);
    assert.ok([23, 24, 25].some((c) => seen.has(c + ',1')), 'P reaches the exit gate');
    let S = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) if (g.at(c, r) === 'S') {
      S++;
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, 'spawn ' + c + ',' + r + ' far from P');
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) if (dc || dr) assert.ok(open(c + dc, r + dr), 'spawn ' + c + ',' + r + ' 3x3 open');
    }
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    // prefab blocks tile by their size (floor plan and floor layer)
    for (const L of [g, F]) for (const ch of PREFAB) {
      const used = new Set();
      for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
        if (L.at(c, r) !== ch || used.has(c + ',' + r)) continue;
        let w = 0; while (L.at(c + w, r) === ch && !used.has((c + w) + ',' + r)) w++;
        let h = 0; while ([...Array(w).keys()].every((k) => L.at(c + k, r + h) === ch && !used.has((c + k) + ',' + (r + h)))) h++;
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) used.add((c + x) + ',' + (r + y));
        const [sw, sd] = TH.symbols[ch].size;
        assert.ok((w % sw === 0 && h % sd === 0) || (w % sd === 0 && h % sw === 0), name + ' ' + ch + ' ' + w + 'x' + h + ' at ' + c + ',' + r);
      }
    }
  });

  test('zone ' + name + ': the wall chooser styles every wall from its room and returns kit pieces', () => {
    const all = new Set(TH.allPieces());
    const solid = (c, r) => '#GE'.includes(g.at(c, r));
    let art = 0, styled = new Set();
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (g.at(c, r) !== '#') continue;
      const oS = !solid(c, r + 1), oN = !solid(c, r - 1), oE = !solid(c + 1, r), oW = !solid(c - 1, r), n = oS + oN + oE + oW;
      const face = n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const p = TH.wall.choose(c, r, false, false, hash, g, face);
      assert.ok(all.has(p), name + ' ' + c + ',' + r + ' -> ' + p);
      assert.ok(!(g.layers[0].at(c, r) in TH.symbols), name + ' art code ' + g.layers[0].at(c, r) + ' at ' + c + ',' + r + ' is also a symbol');
      if (g.layers[0].at(c, r) !== '.' && n === 1) { art++; assert.ok(!/^W[LOAGRC]$/.test(p), name + ' art code at ' + c + ',' + r + ' left plain (' + p + ')'); }
      styled.add(p.replace(/^Corner|^W/, '').charAt(0));
    }
    assert.ok(art >= 10, name + ' wall art ' + art);
    assert.ok(styled.size >= 3, name + ' room styles ' + [...styled].join(''));
  });
}

test('armory mounts: guns rest in front of the rack board, plates clear of the slot, gear on its surface', () => {
  const R = TH.symbols.R, b = TH.symbols.b, g = TH.symbols.g;
  assert.equal(R.mounts.length, 4);
  for (const m of R.mounts) {
    const o = m[5];
    assert.equal(m[4], 'gun');
    assert.ok(o.back && m[2] > -0.45 && m[2] < -0.4, 'gun back plane in front of the board (z -0.45) and its pegs');
    assert.ok(Math.abs(m[0]) + o.len / 2 < 1.42 && Math.abs(m[0]) - o.len / 2 > 0.03, 'gun inside its slot (frame posts at +-1.42 and 0)');
    assert.ok(o.tag[1] + 0.025 < -o.h / 2, 'plate below the gun');
  }
  const slots = R.mounts.map((m) => [m[0], m[1]]);
  for (let i = 0; i < 4; i++) for (let j = i + 1; j < 4; j++) {
    const [a, c] = [R.mounts[i], R.mounts[j]];
    assert.ok(Math.abs(a[0] - c[0]) >= a[5].len || Math.abs(a[1] - c[1]) >= a[5].h + 0.2, 'slots ' + slots[i] + ' / ' + slots[j] + ' apart');
  }
  for (const d of [b, g]) for (const m of d.mounts) assert.ok(m[5] && m[5].tag, 'gear plate offset');
});
