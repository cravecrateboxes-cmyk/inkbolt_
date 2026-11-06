// Mountains theme (campaign level 1, "Pine Ridge"): the level plan follows the level-1 rules, every map is
// playable, and the cliff wall chooser only ever asks for pieces the kit has.
const test = require('node:test');
const assert = require('node:assert');
require('../../src/data/themes.js');
require('../../src/data/themes.gen.js');
require('../../src/data/zones.gen.js');
require('../../src/data/levelplans.js');
const IB = globalThis.IB;
const theme = IB.THEME_DEFS.mountains;
const plan = IB.LEVEL_PLANS.mountains;

function parse(text) {
  const rows = text.replace(/\r/g, '').split('\n').filter(r => r.length > 0);
  const w = Math.max(...rows.map(r => r.length));
  const R = rows.map(r => r.padEnd(w, '.'));
  return { w, h: R.length, rows: R, at: (c, r) => (r < 0 || r >= R.length || c < 0 || c >= w) ? '#' : R[r][c] };
}
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
// greedy rectangles, as zones.js builds prefab blocks
function rects(g, ch) {
  const used = g.rows.map(() => new Array(g.w).fill(false)), out = [];
  for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
    if (used[r][c] || g.rows[r][c] !== ch) continue;
    let w = 1; while (c + w < g.w && !used[r][c + w] && g.rows[r][c + w] === ch) w++;
    let h = 1, ok = true;
    while (ok && r + h < g.h) { for (let k = 0; k < w; k++) if (used[r + h][c + k] || g.rows[r + h][c + k] !== ch) { ok = false; break; } if (ok) h++; }
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) used[r + y][c + x] = true;
    out.push({ c, r, w, h });
  }
  return out;
}
const count = (g, ch) => g.rows.reduce((n, row) => n + row.split(ch).length - 1, 0);
const find = (g, ch) => { const o = []; g.rows.forEach((row, r) => [...row].forEach((x, c) => { if (x === ch) o.push({ c, r }); })); return o; };

test('mountains is campaign level 1 with a gentle, busy three-zone plan', () => {
  assert.ok(theme, 'theme registered');
  assert.strictEqual(IB.CAMPAIGN[0], 'mountains');
  assert.strictEqual(plan.level, 1);
  assert.strictEqual(plan.themeId, 'mountains');
  assert.strictEqual(plan.zones.length, 3);
  let total = 0;
  plan.zones.forEach((z, i) => {
    assert.strictEqual(z.waves.length, 3, 'three waves per zone');
    z.waves.forEach((w, wi) => w.forEach(([type, n]) => {
      total += n;
      if (type === 'bomber' || type === 'drone') assert.strictEqual(i, plan.zones.length - 1, type + ' only in the last zone');
      if (type === 'gunner') assert.ok(i > 0 || wi > 0, 'no gunner in the very first wave');
    }));
  });
  const first = plan.zones[0].waves[0];
  assert.ok(first.length === 1 && first[0][0] === 'crawler' && first[0][1] >= 6 && first[0][1] <= 8, 'first wave: 6-8 crawlers');
  assert.ok(total >= 60 && total <= 75, 'robots in the level: ' + total);
});

test('every mountains map is big, gated and fully reachable', () => {
  const blocking = new Set('#%oO=fxctFHATJQSpk');
  plan.zones.forEach((zp, i) => {
    const g = parse(IB.ZONE_MAPS[zp.map]);
    assert.ok(g.w >= 44 && g.w <= 60 && g.h >= 40 && g.h <= 56, zp.map + ' size ' + g.w + 'x' + g.h);
    const G = find(g, 'G'), E = find(g, 'E'), P = find(g, 'P');
    assert.strictEqual(P.length, 1);
    assert.ok(G.length === 3 && G.every(p => p.r === 0), zp.map + ' exit GGG on the north edge');
    if (i > 0) assert.ok(E.length === 3 && E.every(p => p.r === g.h - 1), zp.map + ' entry EEE on the south edge');
    const S = find(g, 'S');
    assert.ok(S.length >= 10 && S.length <= 14, zp.map + ' spawns ' + S.length);
    S.forEach(s => assert.ok(Math.hypot(s.c - P[0].c, s.r - P[0].r) >= 14, zp.map + ' spawn near P'));
    assert.ok(count(g, 'a') >= 2 && count(g, 'a') <= 3 && count(g, 'h') >= 2 && count(g, 'h') <= 3, zp.map + ' pickups');
    // walkable grid: prefab cells of the rope-bridge pass and the lift line count as open (only their towers block)
    const open = (c, r) => { const ch = g.at(c, r); return ch === 'Y' || ch === 'K' || (ch !== '#' && !blocking.has(ch) && ch !== 'G' && ch !== 'E'); };
    const seen = new Set([P[0].c + ',' + P[0].r]), q = [[P[0].c, P[0].r]];
    while (q.length) {
      const [c, r] = q.shift();
      [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dc, dr]) => { const k = (c + dc) + ',' + (r + dr); if (!seen.has(k) && open(c + dc, r + dr)) { seen.add(k); q.push([c + dc, r + dr]); } });
    }
    assert.ok(G.some(p => seen.has(p.c + ',1')), zp.map + ' path from P to the exit');
    S.forEach(s => assert.ok([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dc, dr]) => seen.has((s.c + dc) + ',' + (s.r + dr))), zp.map + ' spawn reachable'));
  });
});

test('prefab blocks tile exactly and the wall chooser only names kit pieces', () => {
  const pieces = new Set(theme.allPieces());
  plan.zones.forEach(zp => {
    const g = parse(IB.ZONE_MAPS[zp.map]);
    Object.entries(theme.symbols).forEach(([ch, d]) => {
      d.pieces.forEach(p => assert.ok(pieces.has(p), ch + ' piece ' + p + ' listed in allPieces'));
      if (!d.size) return;
      const [sw, sd] = d.size;
      rects(g, ch).forEach(R => assert.ok((R.w % sw === 0 && R.h % sd === 0) || (R.w % sd === 0 && R.h % sw === 0),
        zp.map + ' ' + ch + ' block ' + R.w + 'x' + R.h + ' at ' + R.c + ',' + R.r));
    });
    const W = '#GE', solid = (c, r) => W.indexOf(g.at(c, r)) >= 0;
    find(g, '#').forEach(p => {
      let exposed = false;
      for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if ((dc || dr) && !solid(p.c + dc, p.r + dr)) exposed = true;
      if (!exposed) return;
      const horiz = solid(p.c - 1, p.r) || solid(p.c + 1, p.r), vert = solid(p.c, p.r - 1) || solid(p.c, p.r + 1);
      const name = theme.wall.choose(p.c, p.r, horiz, horiz && vert, hash, g);
      assert.ok(pieces.has(name), zp.map + ' wall ' + name + ' at ' + p.c + ',' + p.r);
      // pre-rotated cliff modules rely on the engine leaving the yaw at 0 (horizontal neighbour present)
      if (/^Cliff_[SNEW]_/.test(name)) assert.ok(horiz, 'straight module needs a horizontal neighbour at ' + p.c + ',' + p.r);
    });
  });
});
