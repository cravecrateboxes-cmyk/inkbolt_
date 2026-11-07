// Campaign levels 14-16 (Galleria Mall, Strike Team HQ, Redwood Hollow) and the armory odds.
const test = require('node:test');
const assert = require('node:assert');
require('../../src/data/weapons.js');
require('../../src/data/themes.js');
require('../../src/data/themes.gen.js');
require('../../src/data/zones.gen.js');
require('../../src/data/levelplans.js');
const IB = globalThis.IB;

// same grammar as Zones.parse: floor plan, then "@layer <y>" grids of the same size
function parse(text) {
  const lines = text.replace(/\r/g, '').split('\n'), base = [], layers = [];
  let cur = base;
  for (const l of lines) { const m = /^@layer\s+(-?[\d.]+)/.exec(l); if (m) { cur = []; layers.push({ y: +m[1], rows: cur }); } else if (l.length) cur.push(l); }
  const w = Math.max(...base.map(r => r.length));
  const grid = (rows, out) => ({ w, h: rows.length, rows, at: (c, r) => (r < 0 || r >= rows.length || c < 0 || c >= w) ? out : rows[r][c] });
  const g = grid(base, '#'); g.layers = layers.map(L => Object.assign(grid(L.rows, '.'), { y: L.y }));
  return g;
}
const find = (g, ch) => { const o = []; g.rows.forEach((row, r) => [...row].forEach((x, c) => { if (x === ch) o.push({ c, r }); })); return o; };
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

test('the three new levels close the campaign as levels 14, 15 and 16', () => {
  assert.deepStrictEqual(IB.CAMPAIGN.slice(-3), ['mall', 'police', 'grove']);
  ['mall', 'police', 'grove'].forEach((id, i) => {
    const p = IB.LEVEL_PLANS[id];
    assert.strictEqual(p.level, 14 + i);
    assert.strictEqual(p.zones.length, 3);
    p.zones.forEach(z => { assert.ok(IB.ZONE_MAPS[z.map], z.map); assert.ok(z.waves.length >= 3); });
  });
  assert.strictEqual(IB.LEVEL_PLANS.island.next, 'mall');
  assert.strictEqual(IB.LEVEL_PLANS.grove.next, null);
});

test('every new map is gated, sized like the others and only uses its theme symbols', () => {
  for (const id of ['mall', 'police', 'grove']) {
    const th = IB.THEME_DEFS[id], known = new Set(Object.keys(th.symbols).concat(['#', 'S', 'P', 'E', 'G', 'a', 'h', '.']));
    IB.LEVEL_PLANS[id].zones.forEach(zp => {
      const g = parse(IB.ZONE_MAPS[zp.map]);
      assert.ok(g.w * g.h >= 2000 && g.w <= 60 && g.h <= 60, zp.map + ' size');
      assert.strictEqual(find(g, 'G').length, 3); assert.strictEqual(find(g, 'E').length, 3); assert.strictEqual(find(g, 'P').length, 1);
      assert.ok(find(g, 'S').length + g.layers.reduce((n, L) => n + find(L, 'S').length, 0) >= 5, zp.map + ' spawns');
      [g].concat(g.layers).forEach(L => L.rows.forEach(row => [...row].forEach(ch => assert.ok(known.has(ch), zp.map + ' unknown symbol ' + ch))));
      g.layers.forEach(L => assert.strictEqual(L.h, g.h, zp.map + ' layer rows'));
      // every prefab block tiles into whole prefabs
      Object.entries(th.symbols).forEach(([ch, d]) => {
        if (!d.size) return;
        [g].concat(g.layers).forEach(L => rects(L, ch).forEach(R => {
          const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
          assert.ok(fits, zp.map + ' ' + ch + ' block ' + R.w + 'x' + R.h + ' at ' + R.c + ',' + R.r);
        }));
      });
    });
  }
});

test('mall: a 4.5 m mezzanine ring with rails on every open edge, two escalators and a lift per zone', () => {
  IB.LEVEL_PLANS.mall.zones.forEach(zp => {
    const g = parse(IB.ZONE_MAPS[zp.map]), up = g.layers.find(L => L.y === 4.5);
    assert.ok(up, zp.map + ' has the 4.5 m layer');
    assert.strictEqual(rects(g, 'N').length + rects(g, 'V').length, 2, 'two escalators');
    assert.strictEqual(rects(g, 'L').length + rects(g, 'J').length, 1, 'one elevator');
    // escalator tops meet the deck
    rects(g, 'N').forEach(R => { for (let k = 0; k < R.w; k++) assert.notStrictEqual(up.at(R.c + k, R.r - 1), '.', 'N top lands on the deck'); });
    rects(g, 'V').forEach(R => { for (let k = 0; k < R.w; k++) assert.notStrictEqual(up.at(R.c + k, R.r + R.h), '.', 'V top lands on the deck'); });
    // deck cells next to the void are rails, except the escalator landings and the elevator door
    const open = new Set();
    rects(g, 'N').forEach(R => { for (let k = 0; k < R.w; k++) open.add((R.c + k) + ',' + (R.r - 1)); });
    rects(g, 'V').forEach(R => { for (let k = 0; k < R.w; k++) open.add((R.c + k) + ',' + (R.r + R.h)); });
    rects(g, 'L').forEach(R => { for (let k = 0; k < R.h; k++) open.add((R.c - 1) + ',' + (R.r + k)); });
    rects(g, 'J').forEach(R => { for (let k = 0; k < R.h; k++) open.add((R.c + R.w) + ',' + (R.r + k)); });
    for (let r = 0; r < up.h; r++) for (let c = 0; c < up.w; c++) {
      const ch = up.at(c, r); if (ch === '.' || ch === '#' || ch === 'r' || open.has(c + ',' + r)) continue;
      let edge = false;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) if (up.at(c + dc, r + dr) === '.') edge = true;
      assert.ok(!edge, zp.map + ' unrailed deck edge at ' + c + ',' + r);
    }
    // nothing on the ground floor under the deck is taller than the 4.1 m slab underside (planters with trees stay in the atrium)
    rects(g, 'O').forEach(R => assert.strictEqual(up.at(R.c, R.r), '.', zp.map + ' big planter under the deck'));
  });
});

test('police: every weapon rack backs onto a wall and the armory has benches and gear shelves', () => {
  let racks = 0;
  IB.LEVEL_PLANS.police.zones.forEach(zp => {
    const g = parse(IB.ZONE_MAPS[zp.map]);
    rects(g, 'R').forEach(R => {
      racks++;
      const long = R.w > R.h, wall = (c, r) => g.at(c, r) === '#';
      let ok = false;
      if (long) ok = [...Array(R.w).keys()].every(k => wall(R.c + k, R.r - 1)) || [...Array(R.w).keys()].every(k => wall(R.c + k, R.r + R.h));
      else ok = [...Array(R.h).keys()].every(k => wall(R.c - 1, R.r + k)) || [...Array(R.h).keys()].every(k => wall(R.c + R.w, R.r + k));
      assert.ok(ok, zp.map + ' rack at ' + R.c + ',' + R.r + ' is not against a wall');
    });
    assert.ok(rects(g, 'b').length >= 1 && rects(g, 'g').length >= 1, zp.map + ' benches + shelves');
  });
  assert.ok(racks >= 20, 'racks ' + racks);
  const th = IB.THEME_DEFS.police;
  assert.strictEqual(th.symbols.R.mounts.length, 4);
  th.symbols.R.mounts.forEach(m => assert.strictEqual(m[4], 'gun'));
});

test('grove: bumpy terrain, redwood pairs joined by a 9 m bridge between their limbs', () => {
  const th = IB.THEME_DEFS.grove;
  let top = 0;
  for (let c = 0; c < 50; c++) for (let r = 0; r < 52; r++) top = Math.max(top, th.terrain.height(c, r, 0));
  assert.ok(top > 2.5 && top < 6, 'terrain top ' + top);
  IB.LEVEL_PLANS.grove.zones.forEach(zp => {
    const g = parse(IB.ZONE_MAPS[zp.map]), up = g.layers.find(L => L.y === 9);
    const trees = rects(g, 'Z');
    assert.ok(trees.length >= 3, zp.map + ' redwoods');
    const bridge = find(up, '=');
    assert.ok(bridge.length > 10, zp.map + ' bridge');
    const rows = [...new Set(bridge.map(p => p.r))].sort((a, b) => a - b);
    assert.strictEqual(rows.length, 2, 'two planks wide');
    const cs = bridge.map(p => p.c), c0 = Math.min(...cs), c1 = Math.max(...cs);
    // both ends touch a redwood footprint, on the rows either side of its centre line (the limbs are 1.6 m wide)
    const west = trees.find(T => T.c + T.w === c0), east = trees.find(T => T.c === c1 + 1);
    assert.ok(west && east, zp.map + ' bridge ends at two trees');
    [west, east].forEach(T => assert.deepStrictEqual(rows, [T.r + 2, T.r + 3]));
  });
});

test('armory racks: purple is very rare and orange never hangs there; bench gear never Legendary', () => {
  const A = IB.THEME_DEFS.police.armory, tot = o => Object.values(o).reduce((a, b) => a + b, 0);
  assert.strictEqual(A.tiers.orange, 0);
  assert.ok(A.tiers.purple > 0 && A.tiers.purple / tot(A.tiers) < 0.015, 'purple ' + A.tiers.purple / tot(A.tiers));
  assert.ok(A.tiers.gray > A.tiers.green && A.tiers.green > A.tiers.blue && A.tiers.blue > A.tiers.purple);
  assert.strictEqual(A.gear.legendary, 0);
  // tier ids are the weapon-drop tiers (src/game/wdrops.js)
  assert.deepStrictEqual(Object.keys(A.tiers), ['gray', 'green', 'blue', 'purple', 'orange']);
});
