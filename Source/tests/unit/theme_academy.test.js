// Chalkstone Academy theme (kit-academy): level plan and waves (2 zones, elite targets for level 36), the two zones
// (size, gates, symbols on every grid, prefab tiling and facing, spawns, pickups, landmarks), the data layers (art codes
// on wall cells only, sliced signs of the right length, outdoor cells), door leaves kept clear, the ceiling and roof
// grids, the wall chooser (a face piece per open side, brick toward the courtyard, nothing over doors and gate
// frames), and the kit pieces checked on the GLB: run pieces along their line of cells, [n, 1] pieces along X, stairs,
// bleachers, tiers and the stage that the player and the robots climb.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/academy.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.academy;
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
function glb(file) {
  const d = fs.readFileSync(path.join(__dirname, '../../assets', file));
  return JSON.parse(d.toString('utf8', 20, 20 + d.readUInt32LE(12)));
}
const plan = IB.LEVEL_PLANS.academy;
const RAW = JSON.parse(JSON.stringify(plan.zones.map((z) => z.waves)));   // as written (levelplans.js tunes the plan in place)
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const isData = (L) => TH.dataLayers.includes(L.y);
const STAND = '.SahPEG';
const DOORS = 'D7OQ';

test('academy theme: kit-academy, sky over the courtyard, data layers, two zones of waves (bombers at most 2, first wave clean)', () => {
  assert.equal(TH.family, 'kit-academy');
  assert.ok(TH.env.sky && TH.env.clouds);
  assert.equal(TH.env.ceiling.height, 4.0, 'the trails and the hatch room get the 4 m ceiling');
  assert.deepEqual(TH.dataLayers, [0.02, 0.03]);
  assert.equal(TH.wall.height, 8.0);
  assert.equal(plan.zones.length, 2);
  plan.zones.forEach((z) => assert.equal(z.ceiling, false, 'zones bring their own ceilings and roofs'));
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader', 'mech', 'hawk', 'grenadier'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 36): each zone holds 61-62.5 soldiers and 37-38.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.academy;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 61 && s <= 62.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 37 && b <= 38.5, 'zone ' + (i + 1) + ' blade bots ' + b));
  // the counts do not lean on the half-a-wave cap (so they hold at any level number): elites = round(2.5 x written)
  const raw = (zi, k) => RAW[zi].reduce((a, w) => a + w.filter(([t]) => t === k).reduce((b, e) => b + Math.round(e[1] * 2.5), 0), 0);
  assert.deepEqual(sold, [raw(0, 'soldier'), raw(1, 'soldier')]);
  assert.deepEqual(blad, [raw(0, 'blader'), raw(1, 'blader')]);
  p.zones.forEach((z) => z.waves.forEach((w) => {
    const tot = w.reduce((a, e) => a + e[1], 0), el = w.filter(([t]) => /soldier|grenadier|blader/.test(t)).reduce((a, e) => a + e[1], 0);
    assert.ok(el <= tot / 2, 'elites ' + el + ' of ' + tot);
  }));
});

const SIZES = { academy_1: [72, 70], academy_2: [72, 72] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols on every grid, prefab tiling and facing, spawns, pickups, landmark', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)), 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)), 'entry approach');
    for (let r = 0; r < g.h; r++) for (const c of [0, g.w - 1]) assert.equal(g.at(c, r), '#', 'perimeter');
    const grids = [g].concat(g.layers.filter((L) => !isData(L)));
    grids.forEach((G, gi) => G.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      assert.ok(ch === '.' || (gi === 0 && (ch === '#' || STAND.includes(ch))) || TH.symbols[ch] || (gi > 0 && 'Sah'.includes(ch)), name + ' grid ' + gi + ' ' + ch + ' at ' + c + ',' + r);
    })));
    for (const G of grids) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (!d.size) continue;
      rects(G, ch).forEach((R) => {
        const fits = (R.w % d.size[0] === 0 && R.h % d.size[1] === 0) || (R.w % d.size[1] === 0 && R.h % d.size[0] === 0);
        assert.ok(fits, name + ' ' + ch + ' block ' + JSON.stringify(R) + ' vs ' + d.size);
        if (typeof d.face === 'number') {   // a fixed facing turns the model, so the block must match the turned footprint
          const side = Math.abs(Math.sin(d.face)) > 0.5;
          const [sw, sd] = side ? [d.size[1], d.size[0]] : d.size;
          assert.ok(R.w % sw === 0 && R.h % sd === 0, name + ' fixed-facing ' + ch + ' ' + JSON.stringify(R));
        }
      });
    }
    // pieces turned against a wall (orient 'wall', as zones.js wallYaw does): the block's long side is the one along
    // the wall (a [2, 1] bookcase in a corner must not turn its short end to the wall: it would stand a quarter off)
    for (const G of grids) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (d.orient !== 'wall' || d.size[0] === d.size[1]) continue;
      rects(G, ch).forEach((R) => {
        const wallAt = (c, r) => g.at(c, r) === '#';
        let n = 0, s = 0, w = 0, e = 0;
        for (let i = 0; i < R.w; i++) { if (wallAt(R.c + i, R.r - 1)) n++; if (wallAt(R.c + i, R.r + R.h)) s++; }
        for (let i = 0; i < R.h; i++) { if (wallAt(R.c - 1, R.r + i)) w++; if (wallAt(R.c + R.w, R.r + i)) e++; }
        const best = Math.max(n, s, w, e), alongX = best === n || best === s;
        assert.ok(best > 0, name + ' ' + ch + ' against no wall ' + JSON.stringify(R));
        assert.equal(alongX, R.w > R.h, name + ' ' + ch + ' turned across its block ' + JSON.stringify(R));
      });
    }
    // doors stand in a wall line: wall (or another door) at both ends, open floor on both faces
    for (const ch of DOORS) rects(g, ch).forEach((R) => {
      const along = R.w > R.h;
      const endA = along ? g.at(R.c - 1, R.r) : g.at(R.c, R.r - 1), endB = along ? g.at(R.c + R.w, R.r) : g.at(R.c, R.r + R.h);
      assert.ok(endA === '#' && endB === '#', name + ' door ends in the wall ' + JSON.stringify(R));
      const fA = along ? g.at(R.c, R.r - 1) : g.at(R.c - 1, R.r), fB = along ? g.at(R.c, R.r + 1) : g.at(R.c + 1, R.r);
      assert.ok(fA !== '#' && fB !== '#', name + ' door faces open ' + JSON.stringify(R));
    });
    const all = (ch) => [g].concat(g.layers.filter((L) => !isData(L))).reduce((a, G) => a + G.rows.reduce((b, row) => b + [...row].filter((x) => x === ch).length, 0), 0);
    assert.equal(all('P'), 1);
    const P = []; g.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (ch === 'P') P.push([c, r]); }));
    let S = 0;
    g.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch !== 'S') return;
      S++;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) assert.ok(STAND.includes(g.at(c + dc, r + dr)) || 'n3,'.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P');
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(all('a') >= 2 && all('a') <= 3 && all('h') >= 2 && all('h') <= 3, 'pickups ' + all('a') + '/' + all('h'));
    if (name === 'academy_1') {
      assert.equal(rects(g, 'Z').length, 1, 'the serving line');
      assert.ok(rects(g, 'N').length + rects(g, 'U').length === 2, 'two stairs to the library');
      assert.ok(rects(g, 'L').length >= 8 && rects(g, 'F').length >= 3 && rects(g, 'x').length === 1, 'lab benches, fume hoods, the skeleton');
    } else {
      assert.equal(rects(g, '@').length, 1, 'the big tree');
      assert.ok(rects(g, '{').length + rects(g, '}').length === 2 && rects(g, '&').length === 1, 'bleachers and the stage');
      assert.ok(rects(g, '3').length === 1 && rects(g, '4').length === 1, 'the covered walkway and the flagpole');
    }
  });
}

test('data layers: art codes on wall cells only, sliced signs of their exact length, outdoor marks on open cells', () => {
  const SL = { C: 8, R: 8, L: 5, N: 13, G: 8 };
  maps.forEach(({ name, g }) => {
    const D = g.layers.filter(isData);
    assert.equal(D.length, 2, name + ' two data layers');
    D.forEach((L) => L.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      if (ch === '.') return;
      if (ch === 'o') { assert.ok(L.y === 0.02 && g.at(c, r) !== '#', name + ' outdoor mark on ' + c + ',' + r); return; }
      assert.equal(g.at(c, r), '#', name + ' code ' + ch + ' off the wall at ' + c + ',' + r);
      assert.ok(TH.chooser.artPiece(g, c, r, L.y === 0.02 ? 'S' : 'N', ch, () => 0.3) || TH.chooser.artPiece(g, c, r, L.y === 0.02 ? 'E' : 'W', ch, () => 0.3), name + ' unknown code ' + ch);
    })));
    for (const L of D) for (const [ch, n] of Object.entries(SL)) {
      const cells = []; L.rows.forEach((row, r) => [...row].forEach((x, c) => { if (x === ch) cells.push([c, r]); }));
      if (!cells.length) continue;
      const runs = rects(L, ch);
      runs.forEach((R) => assert.equal(Math.max(R.w, R.h), n, name + ' sign ' + ch + ' run ' + JSON.stringify(R)));
    }
  });
  assert.ok(maps[1].g.layers.find((L) => L.y === 0.02).rows.join('').split('o').length > 2000, 'the courtyard is outdoors');
});

test('door leaves (folded flat on one face) have a clear wall either side: no art, nothing standing against it', () => {
  maps.forEach(({ name, g }) => {
    const A = g.layers.find((L) => L.y === 0.02), B = g.layers.find((L) => L.y === 0.03);
    for (const ch of DOORS) rects(g, ch).forEach((R) => {
      const along = R.w > R.h, back = ch !== '7';   // 'D' 'O' 'Q' fold to the north / west, '7' to the south / east
      const n = 1;
      const side = along ? (back ? [0, -1] : [0, 1]) : (back ? [-1, 0] : [1, 0]);
      const ends = along ? [[R.c - 1, R.r], [R.c + R.w, R.r]] : [[R.c, R.r - 1], [R.c, R.r + R.h]];
      ends.forEach(([c, r]) => {
        for (let k = 0; k < n; k++) {
          const L = (side[0] > 0 || side[1] > 0) ? A : B;
          assert.equal(L.at(c, r), '.', name + ' art beside the door leaf at ' + c + ',' + r);
          const f = g.at(c + side[0], r + side[1]);
          assert.ok('.Sah'.includes(f) || f === '#', name + ' something against the door leaf at ' + (c + side[0]) + ',' + (r + side[1]) + ' (' + f + ')');
        }
      });
    });
  });
});

test('ceilings: every indoor 4 m cell has a tile, none over walls, doors, gates, double-height rooms or the courtyard', () => {
  maps.forEach(({ name, g }) => {
    const C = g.layers.find((L) => L.y === 4 && L.rows.join('').match(/[=+*-]/));
    const R8 = g.layers.find((L) => L.y === 8);
    const A = g.layers.find((L) => L.y === 0.02);
    let n = 0;
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      const ch = g.at(c, r), t = C.at(c, r), roof = R8.at(c, r) !== '.', out = A.at(c, r) === 'o';
      if ('#GE'.includes(ch) || DOORS.includes(ch)) { assert.equal(t, '.', name + ' tile over a wall / door at ' + c + ',' + r); continue; }
      if (roof || out || ch === 'n') { assert.equal(t, '.', name + ' tile under the roof / sky at ' + c + ',' + r); continue; }
      assert.ok('=+*-'.includes(t), name + ' no ceiling at ' + c + ',' + r); n++;
    }
    assert.ok(n > 600, name + ' tiled cells ' + n);
  });
});

test('wall chooser: a face piece per open side (brick toward the courtyard), none on doors or beside a gate', () => {
  const pieces = new Set(TH.allPieces());
  const hash = (a, b) => ((Math.sin(a * 12.9898 + b * 78.233) * 43758.5453) % 1 + 1) % 1;
  maps.forEach(({ name, g }, zi) => {
    const A = g.layers.find((L) => L.y === 0.02);
    let faces = 0, brick = 0;
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      const ch = g.at(c, r);
      if (ch !== '#' && !DOORS.includes(ch)) continue;
      const W = (x, y) => ('#GE' + DOORS).includes(g.at(x, y));
      const open = [[0, 1], [0, -1], [1, 0], [-1, 0]].filter(([dc, dr]) => !W(c + dc, r + dr));
      const horiz = W(c - 1, r) || W(c + 1, r), vert = W(c, r - 1) || W(c, r + 1);
      const oS = !W(c, r + 1), oN = !W(c, r - 1), oE = !W(c + 1, r), oW = !W(c - 1, r), nO = oS + oN + oE + oW;
      const face = nO === 0 ? 'none' : nO === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      const out = TH.wall.choose(c, r, horiz, horiz && vert, hash, g, face);
      const besideGate = (r === 0 || r === g.h - 1) && [g.at(c - 1, r), g.at(c + 1, r)].some((x) => x === 'G' || x === 'E');
      if (DOORS.includes(ch) || besideGate) { assert.equal(out, null, name + ' door / gate cell ' + c + ',' + r); continue; }
      if (!open.length) continue;
      assert.ok(Array.isArray(out), name + ' faces at ' + c + ',' + r);
      const list = out.map((e) => (typeof e === 'string' ? e : e.piece));
      list.forEach((p) => assert.ok(pieces.has(p), name + ' unknown piece ' + p));
      if (!list.some((p) => /^OW_/.test(p))) assert.equal(list.length, open.length, name + ' one face per open side at ' + c + ',' + r);
      open.forEach(([dc, dr], i) => {
        if (A.at(c + dc, r + dr) === 'o' && list[i]) { brick++; assert.ok(/^X/.test(list[i]), name + ' brick toward the courtyard at ' + c + ',' + r + ' got ' + list[i]); }
      });
      faces += list.length;
    }
    assert.ok(faces > 450, name + ' faces ' + faces);
    if (zi === 1) assert.ok(brick > 200, 'courtyard facades ' + brick);
  });
});

test('kit pieces on the GLB: runs along their line, [n, 1] pieces along X, stairs, bleachers, tiers and the stage climbable', () => {
  const G = glb('fps-kit-academy.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const cols = (piece, walk) => {
    const node = G.nodes.find((n) => n.name === 'KIT_ACADEMY_' + piece);
    assert.ok(node, piece);
    return (node.children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  };
  // link runs (no turn): the full rail runs along glTF Z (Blender Y), the half reaches from the centre toward +Z
  const [rf] = cols('RailFull');
  assert.ok(rf.s[2] > 5 * rf.s[0], 'RailFull long axis on Z ' + JSON.stringify(rf.s));
  assert.ok(!TH.symbols['|'].turn);
  const [rh] = cols('RailHalf');
  assert.ok(rh.t[2] > 0.2 && rh.t[2] + rh.s[2] <= 0.51, 'RailHalf toward +Z ' + JSON.stringify(rh));
  // [n, 1] prefabs along X: benches, cafeteria tables, bookcases, the serving line, the bike rack, book stacks
  for (const p of ['Bench', 'CafTable', 'Bookcase', 'Shelf', 'TrayReturn', 'Kitchenette', 'SinkCounter', 'DemoBench']) {
    const b = cols(p).reduce((m, x) => (x.s[0] * x.s[2] > m.s[0] * m.s[2] ? x : m));
    assert.ok(b.s[0] > 2 * b.s[2], p + ' along X ' + JSON.stringify(b.s));
  }
  // steps: each walkable step rises at most 0.2 m over the one below it on treads of 0.3 m (stairs, 0.25 m) / 0.28 m
  // (bleachers) / 0.62 m (tiers) and reaches its top: under the robots' 0.4 m per 0.5 m nav cell
  const climb = (piece, top, axis, tread, rise) => {
    const st = cols(piece, true).map((b) => ({ u: b.t[axis], top: b.t[1] + b.s[1], w: b.s[axis === 0 ? 2 : 0], d: b.s[axis] * 2 }))
      .filter((b) => Math.abs(b.d - tread) < 0.01).sort((a, b) => a.top - b.top);
    assert.ok(st.length >= 5, piece + ' steps ' + st.length);
    for (let i = 1; i < st.length; i++) {
      assert.ok(st[i].top - st[i - 1].top > rise - 0.005 && st[i].top - st[i - 1].top < rise + 0.005, piece + ' rise ' + i);
      assert.ok(Math.ceil(0.5 / tread) * rise <= 0.34, piece + ' rise per 0.5 m nav cell');
      assert.ok(Math.abs(Math.abs(st[i].u - st[i - 1].u) - tread) < 0.01, piece + ' tread ' + i);
    }
    assert.ok(st[st.length - 1].top >= top - 0.25, piece + ' reaches ' + top + ' (' + st[st.length - 1].top + ')');
    assert.ok(st.every((s) => s.w >= 0.6), piece + ' wide enough for the nav grid');
  };
  climb('Stair', 3.8, 2, 0.25, 0.16);
  climb('Bleacher', 2.2, 2, 0.28, 0.16);
  climb('Tiers', 1.0, 2, 0.62, 0.2);
  const stairTop = Math.max(...cols('Stair', true).map((b) => b.t[1] + b.s[1]));
  assert.ok(Math.abs(stairTop - 4.0) < 0.01, 'the stair meets the 4 m mezzanine');
  const deck = cols('Stage', true).find((b) => b.s[0] > 6);
  assert.ok(deck && Math.abs(deck.t[1] + deck.s[1] - 1.0) < 0.01, 'the stage platform is walkable at 1 m');
  assert.ok(cols('Stage', true).filter((b) => Math.abs(b.s[2] * 2 - 0.25) < 0.01).length >= 12, 'the stage steps');
});
