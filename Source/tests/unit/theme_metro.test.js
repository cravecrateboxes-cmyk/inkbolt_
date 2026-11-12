// Metro Central theme (kit-metro): level plan and waves (2 zones, elite targets for level 41), the two zones (size,
// gates, symbols on every grid, prefab tiling and facing, spawns, pickups, landmarks), the data layers (art codes on
// wall cells only, sliced signs of the right length, sunk cells and their side art, the finish schemes), the sunk
// floors (theme.sunk: trackbeds 0.9 m, the escalator well 4.5 m; every trackbed stretch has steps out, the trains, the
// track, the escalators and the stairs stand in them), the footbridge decks, the wall chooser (a finish face per open
// side in the scheme of the cell it looks onto, overlays, through pieces, nothing on doors or beside a gate), the sunk
// side chooser, and the kit pieces checked on the GLB: run pieces along their line of cells, [n, 1] pieces along X,
// the stairs, the escalators, the footbridge stairs and the trackbed steps the player and the robots climb.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/themes.js');
require('../../src/data/themes/metro.js');
const IB = globalThis.IB;
const TH = IB.THEME_DEFS.metro;
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
const plan = IB.LEVEL_PLANS.metro;
const maps = plan.zones.map((z) => ({ name: z.map, g: parse(fs.readFileSync(path.join(ZDIR, z.map + '.txt'), 'utf8')) }));
const isData = (L) => TH.dataLayers.includes(L.y);
const layer = (g, y) => g.layers.find((L) => Math.abs(L.y - y) < 1e-4);
const STAND = '.SahPEG';
const DOORS = 'DOd';
const SUNK = (g) => layer(g, 0.04);

test('metro theme: kit-metro, underground (no sky), data layers, sunk floors, two zones of waves (bombers at most 2, first wave clean)', () => {
  assert.equal(TH.family, 'kit-metro');
  assert.equal(TH.env.sky, null);
  assert.equal(TH.env.ceiling.height, 3.6, 'the trails and the hatch room get the 3.6 m ceiling');
  assert.deepEqual(TH.dataLayers, [0.02, 0.03, 0.04, 0.05]);
  assert.equal(TH.wall.height, 8.0);
  assert.equal(TH.sunk.layer, 0.04);
  assert.deepEqual(TH.sunk.depth, { t: 0.9, w: 4.5 });
  assert.equal(plan.zones.length, 2);
  plan.zones.forEach((z) => assert.equal(z.ceiling, false, 'zones bring their own ceilings and vaults'));
  const types = new Set();
  plan.zones.forEach((z) => z.waves.forEach((w) => w.forEach(([t, n]) => { types.add(t); if (t === 'bomber') assert.ok(n <= 2, 'bombers per wave'); })));
  for (const t of types) assert.ok(['crawler', 'gunner', 'bomber', 'drone', 'soldier', 'blader'].includes(t), t);
  assert.ok(!plan.zones[0].waves[0].some(([t]) => /soldier|blader|grenadier/.test(t)), 'first wave of zone 1');
});

test('elite targets (level 41): each zone holds 66-67.5 soldiers and 42-43.5 blade bots after tuning, elites at most half a wave', () => {
  const S = path.join(__dirname, '../../src/');
  ['data/weapons', 'data/enemies', 'data/unlocks', 'data/levels', 'core/damage', 'core/gems'].forEach((f) => require(S + f + '.js'));
  fs.readdirSync(S + 'data/themes').filter((f) => f.endsWith('.js')).forEach((f) => require(S + 'data/themes/' + f));
  require(S + 'data/levelplans.js');
  const p = IB.LEVEL_PLANS.metro;
  assert.ok(p.tuned, 'tuned');
  const count = (z, f) => z.waves.reduce((a, w) => a + w.filter(([t]) => f(t)).reduce((b, e) => b + e[1], 0), 0);
  const sold = p.zones.map((z) => count(z, (t) => t === 'soldier' || t === 'grenadier'));
  const blad = p.zones.map((z) => count(z, (t) => t === 'blader'));
  sold.forEach((s, i) => assert.ok(s >= 66 && s <= 67.5, 'zone ' + (i + 1) + ' soldiers ' + s));
  blad.forEach((b, i) => assert.ok(b >= 42 && b <= 43.5, 'zone ' + (i + 1) + ' blade bots ' + b));
  p.zones.forEach((z) => z.waves.forEach((w) => {
    const tot = w.reduce((a, e) => a + e[1], 0), el = w.filter(([t]) => /soldier|grenadier|blader/.test(t)).reduce((a, e) => a + e[1], 0);
    assert.ok(el <= tot / 2, 'elites ' + el + ' of ' + tot);
  }));
});

const SIZES = { metro_1: [72, 70], metro_2: [72, 66] };
for (const { name, g } of maps) {
  test('zone ' + name + ': size, gates, symbols on every grid, prefab tiling and facing, spawns, pickups, landmark', () => {
    assert.deepEqual([g.w, g.h], SIZES[name]);
    const gc = g.rows[0].indexOf('GGG'), ec = g.rows[g.h - 1].indexOf('EEE');
    assert.ok(gc > 0 && ec > 0, 'gates');
    const K = SUNK(g);
    for (let c = gc; c < gc + 3; c++) for (const r of [1, 2]) assert.ok(STAND.includes(g.at(c, r)) && K.at(c, r) === '.', 'exit approach');
    for (let c = ec; c < ec + 3; c++) for (const r of [g.h - 2, g.h - 3]) assert.ok(STAND.includes(g.at(c, r)) && K.at(c, r) === '.', 'entry approach');
    for (let r = 0; r < g.h; r++) for (const c of [0, g.w - 1]) assert.equal(g.at(c, r), '#', 'perimeter');
    const grids = [g].concat(g.layers.filter((L) => !isData(L)));
    grids.forEach((G, gi) => G.rows.forEach((row, r) => [...row].forEach((ch, c) => {
      assert.ok(ch === '.' || (gi === 0 && (ch === '#' || STAND.includes(ch))) || TH.symbols[ch], name + ' grid ' + gi + ' ' + ch + ' at ' + c + ',' + r);
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
    // pieces turned against a wall (orient 'wall', zones.js wallYaw): the block's long side is the one along the wall
    for (const G of grids) for (const [ch, d] of Object.entries(TH.symbols)) {
      if (d.orient !== 'wall' || d.flip || d.size[0] === d.size[1]) continue;
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
    // doors stand in a wall line: wall (or a window) at both ends, open floor on both faces
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
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
        assert.ok(STAND.includes(g.at(c + dc, r + dr)), name + ' spawn ' + c + ',' + r + ' open round');
        assert.equal(K.at(c + dc, r + dr), K.at(c, r), name + ' spawn ' + c + ',' + r + ' on one level');
      }
      assert.ok(Math.hypot(c - P[0][0], r - P[0][1]) >= 14, name + ' spawn near P');
    }));
    assert.ok(S >= 10 && S <= 14, 'spawns ' + S);
    assert.ok(all('a') >= 2 && all('a') <= 3 && all('h') >= 2 && all('h') <= 3, 'pickups ' + all('a') + '/' + all('h'));
    if (name === 'metro_1') {
      assert.equal(rects(g, 'Z').length, 1, 'the departures board');
      assert.equal(rects(g, 'X').length, 1, 'the escalator bank');
      assert.equal(rects(g, 'N').length, 2, 'two fixed stairs down the well');
      assert.ok(all('F') >= 20 && all('W') >= 2, 'the fare gate line');
      assert.equal(rects(layer(g, 2.9), '3').length + rects(layer(g, 2.9), '4').length + rects(layer(g, 2.9), '5').length + rects(layer(g, 2.9), '6').length, 4, 'four shop fascias');
    } else {
      assert.equal(rects(g, '@').length, 1, 'the station clock');
      assert.ok(rects(g, 'e').length === 1 && rects(g, 'x').length === 1, 'two trains');
      assert.equal(rects(g, '<').length + rects(g, '>').length, 6, 'a footbridge stair on each platform, two bridges');
      assert.equal(rects(layer(g, 4.5), 'u').length >= 2, true, 'two footbridge decks');
    }
  });
}

test('data layers: art codes on wall cells only, sliced signs of their exact length, schemes on every cell a wall looks onto', () => {
  const N = { n: 3, A: 3, U: 3, m: 2, X: 2, g: 2, G: 2, L: 2 };
  const SCH = 'hpeokfnmrbi';
  maps.forEach(({ name, g }) => {
    const Sc = layer(g, 0.05);
    [layer(g, 0.02), layer(g, 0.03)].forEach((L, li) => {
      const side = li === 0 ? [[0, 1], [1, 0]] : [[0, -1], [-1, 0]];
      for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
        const ch = L.at(c, r);
        if (ch === '.') continue;
        assert.equal(g.at(c, r), '#', name + ' code ' + ch + ' off the wall at ' + c + ',' + r);
        if (!N[ch]) continue;
        // runs along the wall (either direction): their lengths are multiples of the sign's length
        const hz = L.at(c - 1, r) === ch || L.at(c + 1, r) === ch, vt = L.at(c, r - 1) === ch || L.at(c, r + 1) === ch;
        if (hz && L.at(c - 1, r) !== ch) { let n = 0; while (L.at(c + n, r) === ch) n++; assert.equal(n % N[ch], 0, name + ' run ' + ch + ' at ' + c + ',' + r + ' len ' + n); }
        if (vt && L.at(c, r - 1) !== ch) { let n = 0; while (L.at(c, r + n) === ch) n++; assert.equal(n % N[ch], 0, name + ' run ' + ch + ' at ' + c + ',' + r + ' len ' + n); }
        assert.ok(side.some(([dc, dr]) => g.at(c + dc, r + dr) !== '#'), name + ' code ' + ch + ' faces open floor at ' + c + ',' + r);
      }
    });
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      if (g.at(c, r) !== '#') continue;
      [[0, 1], [0, -1], [1, 0], [-1, 0]].forEach(([dc, dr]) => {
        const ch = g.at(c + dc, r + dr);
        if (('#GE' + DOORS).includes(ch)) return;
        assert.ok(SCH.includes(Sc.at(c + dc, r + dr)), name + ' no scheme at ' + (c + dc) + ',' + (r + dr) + ' (a wall looks onto it)');
      });
    }
  });
});

test('sunk floors: trackbeds and the well on open cells, the trains, track, escalators and stairs stand in them, every trackbed stretch has steps out', () => {
  maps.forEach(({ name, g }) => {
    const K = SUNK(g);
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      const k = K.at(c, r), ch = g.at(c, r);
      if (k === 't' || k === 'w') assert.ok(!('#GE' + DOORS + 'n').includes(ch), name + ' sunk wall / door at ' + c + ',' + r);
      if ('ex~12'.includes(ch)) assert.equal(k, 't', name + ' ' + ch + ' out of the trackbed at ' + c + ',' + r);
      if ('XN'.includes(ch)) assert.equal(k, 'w', name + ' ' + ch + ' out of the well at ' + c + ',' + r);
      if ('UnamY'.includes(k)) {   // side art: on a higher cell next to the well
        assert.ok([[0, 1], [0, -1], [1, 0], [-1, 0]].some(([dc, dr]) => K.at(c + dc, r + dr) === 'w'), name + ' side art ' + k + ' off the well at ' + c + ',' + r);
      }
    }
    // stretches of trackbed between the trains (4-connected 't' cells not under a train) each reach steps
    const seen = new Set();
    for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
      if (K.at(c, r) !== 't' || 'ex'.includes(g.at(c, r)) || seen.has(c + ',' + r)) continue;
      const q = [[c, r]]; seen.add(c + ',' + r); let steps = 0, n = 0;
      while (q.length) {
        const [x, y] = q.pop(); n++;
        if ('12'.includes(g.at(x, y))) steps++;
        [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
          const k2 = (x + dx) + ',' + (y + dy);
          if (K.at(x + dx, y + dy) === 't' && !'ex'.includes(g.at(x + dx, y + dy)) && !seen.has(k2)) { seen.add(k2); q.push([x + dx, y + dy]); }
        });
      }
      assert.ok(steps > 0, name + ' a trackbed stretch of ' + n + ' cells from ' + c + ',' + r + ' has no steps out');
    }
    // the side chooser: platform edges, trimmed where the cell also drops away to its right, plain beside the steps
    let edges = 0;
    for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
      if (K.at(c, r) === 't' || K.at(c, r) === 'w') continue;
      [[0, 1], [0, -1], [1, 0], [-1, 0]].forEach(([dc, dr]) => {
        const k = K.at(c + dc, r + dr); if (k !== 't' && k !== 'w') return;
        const piece = TH.sunk.side(c, r, dc, dr, k, g, () => 0.3);
        assert.ok(TH.allPieces().includes(piece), name + ' side piece ' + piece);
        if (k === 'w') assert.ok(/^Well/.test(piece), name + ' well side ' + piece);
        else if (g.at(c, r) !== '#') { edges++; assert.ok(/^Edge/.test(piece), name + ' platform edge ' + piece); }
      });
    }
    if (name === 'metro_2') assert.ok(edges > 250, 'platform edges ' + edges);
  });
});

test('footbridges: decks on the 4.5 m layer over both tracks, rails along both sides, a gap where each stair lands', () => {
  const g = maps[1].g, D = layer(g, 4.5), K = SUNK(g);
  for (const [c0, sym] of [[15, '<'], [53, '>']]) {
    let overTrack = 0;
    for (let r = 9; r <= 40; r++) {
      for (let c = c0; c < c0 + 4; c++) { assert.ok('u]'.includes(D.at(c, r)), 'deck at ' + c + ',' + r); if (K.at(c, r) === 't') overTrack++; }
      const land = sym === '<' ? c0 + 3 : c0, other = sym === '<' ? c0 : c0 + 3;
      assert.equal(D.at(other, r), ']', 'outer rail ' + other + ',' + r);
      const stairNext = g.at(sym === '<' ? c0 + 4 : c0 - 1, r) === sym;
      assert.equal(D.at(land, r), stairNext ? 'u' : ']', 'landing side ' + land + ',' + r);
    }
    assert.ok(overTrack >= 2 * 4 * 3, 'the deck crosses both trackbeds');
  }
});

test('wall chooser: a finish face per open side in the scheme it looks onto, overlays on top, none on doors or beside a gate', () => {
  const pieces = new Set(TH.allPieces());
  const hash = (a, b) => ((Math.sin(a * 12.9898 + b * 78.233) * 43758.5453) % 1 + 1) % 1;
  const SCHEME = { h: 'IH', p: 'IP', e: 'IE', o: 'IO', k: 'IK', f: 'IF', n: 'IN', m: 'IM', r: 'IR', b: 'IB', i: 'II' };
  maps.forEach(({ name, g }) => {
    const Sc = layer(g, 0.05);
    let faces = 0, through = 0;
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
      if (list.some((p) => /^(SW|TW)_/.test(p))) { assert.equal(list.length, 1, name + ' a through piece alone at ' + c + ',' + r); through++; continue; }
      const plain = list.filter((p) => /^I[A-Z]$/.test(p));
      assert.equal(plain.length, open.length, name + ' one finish face per open side at ' + c + ',' + r);
      if (face !== 'corner') open.forEach(([dc, dr], i) => assert.equal(plain[i], SCHEME[Sc.at(c + dc, r + dr)], name + ' scheme at ' + c + ',' + r));
      faces += list.length;
    }
    assert.ok(faces > 400, name + ' faces ' + faces);
    if (name === 'metro_1') assert.ok(through >= 20, 'shop and ticket windows ' + through);
  });
});

test('kit pieces on the GLB: runs along their line, [n, 1] pieces along X, stairs, escalators and steps climbable', () => {
  const G = glb('fps-kit-metro.glb');
  const names = new Set(G.nodes.map((n) => n.name));
  for (const p of TH.allPieces()) assert.ok(names.has(IB.themePiece(TH, p)), 'missing ' + p);
  const cols = (piece, walk) => {
    const node = G.nodes.find((n) => n.name === 'KIT_METRO_' + piece);
    assert.ok(node, piece);
    return (node.children || []).map((i) => G.nodes[i]).filter((n) => (walk ? /_WCOL\d+$/ : /_W?COL\d+$/).test(n.name)).map((n) => ({ t: n.translation || [0, 0, 0], s: n.scale }));
  };
  // link runs (no turn): the full rail runs along glTF Z (Blender Y), the half reaches from the centre toward +Z
  for (const [full, half, ch] of [['GRailFull', 'GRailHalf', '|'], ['BRailFull', 'BRailHalf', ']']]) {
    const [rf] = cols(full);
    assert.ok(rf.s[2] > 5 * rf.s[0], full + ' long axis on Z ' + JSON.stringify(rf.s));
    assert.ok(!TH.symbols[ch].turn);
    const [rh] = cols(half);
    assert.ok(rh.t[2] > 0.2 && rh.t[2] + rh.s[2] <= 0.51, half + ' toward +Z ' + JSON.stringify(rh));
  }
  // [n, 1] prefabs along X
  for (const p of ['Bench', 'TVM3', 'Counter', 'Gondola', 'Cooler', 'MagRack', 'MagIsland', 'Shelf', 'Lockers', 'Workbench', 'ToolCage', 'ElecCab', 'QueueBar', 'LightBox']) {
    const b = cols(p).reduce((m, x) => (x.s[0] * x.s[2] > m.s[0] * m.s[2] ? x : m));
    assert.ok(b.s[0] > 2 * b.s[2], p + ' along X ' + JSON.stringify(b.s));
  }
  // the fare gate cabinet stands across its unit (1.1 m along the aisle, glTF Z)
  const [fg] = cols('FareGate');
  assert.ok(fg.s[2] > 2.5 * fg.s[0], 'FareGate cabinet along the aisle ' + JSON.stringify(fg.s));
  // a train car: 18 m along X, its walkable floor 2 cm over the platform (0.9 m over the trackbed)
  const floor = cols('CarMid', true).reduce((m, x) => (x.s[0] > m.s[0] ? x : m));
  assert.ok(floor.s[0] > 8.9 && Math.abs(floor.t[1] + floor.s[1] - 0.92) < 0.005, 'the car floor ' + JSON.stringify(floor));
  // steps: each walkable step rises at most 0.35 m per 0.5 m nav cell and reaches its top
  const climb = (piece, top, axis, tread, rise) => {
    const st = cols(piece, true).map((b) => ({ u: b.t[axis], top: b.t[1] + b.s[1], w: b.s[axis === 0 ? 2 : 0], d: b.s[axis] * 2 }))
      .filter((b) => Math.abs(b.d - tread) < 0.01).sort((a, b) => a.top - b.top);
    assert.ok(st.length >= 5, piece + ' steps ' + st.length);
    for (let i = 1; i < st.length; i++) {
      assert.ok(Math.abs(st[i].top - st[i - 1].top - rise) < 0.005, piece + ' rise ' + i + ' ' + (st[i].top - st[i - 1].top));
      assert.ok(Math.abs(Math.abs(st[i].u - st[i - 1].u) - tread) < 0.01, piece + ' tread ' + i);
    }
    assert.ok(Math.ceil(0.5 / tread - 1e-6) * rise <= 0.35, piece + ' rise per 0.5 m nav cell');
    assert.ok(st[st.length - 1].top >= top - 0.35, piece + ' reaches ' + top + ' (' + st[st.length - 1].top + ')');
    assert.ok(st.every((s) => s.w >= 0.6), piece + ' wide enough for the nav grid');
  };
  climb('Stair', 4.5, 2, 0.25, 4.5 / 28);
  climb('EscBank', 4.5, 2, 0.25, 4.5 / 26);
  climb('BStair', 4.5, 0, 0.25, 4.5 / 28);
  climb('Steps', 0.9, 2, 0.3, 0.15);
  for (const p of ['Stair', 'EscBank', 'BStair']) {
    const tops = cols(p, true).map((b) => b.t[1] + b.s[1]);
    assert.ok(Math.abs(Math.max(...tops) - 4.5) < 0.01, p + ' meets its 4.5 m landing');
  }
});
