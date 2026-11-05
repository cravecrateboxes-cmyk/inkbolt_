/* INKBOLT - generated levels after 20 (brief section 5.16, symbols 5.12). Pure, no DOM.
   Coordinates: zone-local metres from the template's top-left corner; a cell (col, row) has its
   centre at x = col + 0.5, z = row + 0.5. Grids are arrays of equal-length strings. */
(function (IB) {
  'use strict';

  var MAX_SIZE = 40;
  var BLOCKING = { '#': 1, '=': 1, 'c': 1, 'C': 1, 'T': 1 };
  var COVER = { 'c': 1, 'C': 1, '=': 1 };
  var CAPS = { bruiser: 2, binhive: 1 };
  var MAX_ATTEMPTS = 10;
  var MIN_SPAWN_DIST = 8;
  var MIN_COVER = 4;

  function toRows(src) {
    var rows;
    if (Array.isArray(src)) rows = src.slice();
    else if (src && typeof src === 'object') rows = src.rows ? src.rows.slice() : String(src.text || '').split('\n');
    else rows = String(src).split('\n');
    rows = rows.map(function (r) { return String(r).replace(/\r$/, ''); });
    while (rows.length && rows[0].trim() === '') rows.shift();
    while (rows.length && rows[rows.length - 1].trim() === '') rows.pop();
    var w = 0;
    rows.forEach(function (r) { if (r.length > w) w = r.length; });
    return rows.map(function (r) {
      var s = r.replace(/ /g, '.');
      while (s.length < w) s += '.';
      return s;
    });
  }

  function isBlockingChar(ch) { return !!BLOCKING[ch]; }

  /* parseZone(text | rows[] | {text} | {rows}) ->
     {w, h, rows, at(x,z), blocked(x,z), find(ch) -> [{x,z}] (cell indices), inside(x,z)} */
  function parseZone(src) {
    var rows = toRows(src);
    var h = rows.length;
    var w = h ? rows[0].length : 0;
    function inside(x, z) { return x >= 0 && z >= 0 && x < w && z < h; }
    function at(x, z) { return inside(x, z) ? rows[z].charAt(x) : '#'; }
    return {
      w: w, h: h, rows: rows,
      inside: inside,
      at: at,
      blocked: function (x, z) { return isBlockingChar(at(x, z)); },
      find: function (ch) {
        var out = [];
        for (var z = 0; z < h; z++) for (var x = 0; x < w; x++) if (rows[z].charAt(x) === ch) out.push({ x: x, z: z });
        return out;
      }
    };
  }

  // rot: quarter turns clockwise (0..3); mirror: flip left-right before rotating.
  function transform(rows, rot, mirror) {
    var r = rows.slice();
    if (mirror) r = r.map(function (s) { return s.split('').reverse().join(''); });
    for (var k = 0; k < (rot & 3); k++) {
      var h = r.length, w = h ? r[0].length : 0;
      var nr = [];
      for (var x = 0; x < w; x++) {
        var line = '';
        for (var z = h - 1; z >= 0; z--) line += r[z].charAt(x);
        nr.push(line);
      }
      r = nr;
    }
    return r;
  }

  function bfs(zone, starts) {
    var w = zone.w, h = zone.h;
    var dist = new Int32Array(w * h).fill(-1);
    var q = [];
    starts.forEach(function (s) {
      if (zone.inside(s.x, s.z) && !zone.blocked(s.x, s.z) && dist[s.z * w + s.x] < 0) {
        dist[s.z * w + s.x] = 0; q.push(s.z * w + s.x);
      }
    });
    for (var qi = 0; qi < q.length; qi++) {
      var i = q[qi], x = i % w, z = (i - x) / w;
      var nb = [[x + 1, z], [x - 1, z], [x, z + 1], [x, z - 1]];
      for (var n = 0; n < 4; n++) {
        var nx = nb[n][0], nz = nb[n][1];
        if (!zone.inside(nx, nz) || zone.blocked(nx, nz)) continue;
        var j = nz * w + nx;
        if (dist[j] >= 0) continue;
        dist[j] = dist[i] + 1;
        q.push(j);
      }
    }
    return dist;
  }

  // Connected pieces (4-neighbour, same symbol) of cover cells: c, C, =.
  function coverPieces(zone) {
    var w = zone.w, h = zone.h;
    var seen = new Uint8Array(w * h);
    var pieces = 0;
    for (var z = 0; z < h; z++) for (var x = 0; x < w; x++) {
      var ch = zone.at(x, z);
      if (!COVER[ch] || seen[z * w + x]) continue;
      pieces++;
      var stack = [[x, z]];
      seen[z * w + x] = 1;
      while (stack.length) {
        var p = stack.pop();
        var nb = [[p[0] + 1, p[1]], [p[0] - 1, p[1]], [p[0], p[1] + 1], [p[0], p[1] - 1]];
        for (var n = 0; n < 4; n++) {
          var nx = nb[n][0], nz = nb[n][1];
          if (zone.inside(nx, nz) && !seen[nz * w + nx] && zone.at(nx, nz) === ch) {
            seen[nz * w + nx] = 1; stack.push([nx, nz]);
          }
        }
      }
    }
    return pieces;
  }

  /* validate(zone) where zone is a parseZone result, a grid (rows / text), or {grid:[...], spawns}.
     Rules (5.16): size <= 40 x 40; a P and a G; path P -> G (BFS, 4-neighbour, blocking: # = c C T);
     every S cell (and every generated spawn) >= 8 m from the nearest P; >= 4 cover pieces;
     no spawn enclosed (every S reachable from P); >= 1 ammo box 'a'.
     -> {ok, errors:[string], cover, spawnCells} */
  function validate(z) {
    var zone = z && z.at && z.rows ? z : parseZone(z && z.grid ? z.grid : z);
    var spawns = z && z.spawns ? z.spawns : [];
    var errors = [];
    if (zone.w > MAX_SIZE || zone.h > MAX_SIZE) errors.push('size ' + zone.w + 'x' + zone.h + ' exceeds 40x40');
    var P = zone.find('P'), G = zone.find('G'), S = zone.find('S');
    if (!P.length) errors.push('no entry P');
    if (!G.length) errors.push('no exit G');
    if (!S.length) errors.push('no spawn S');
    var dist = P.length ? bfs(zone, P) : null;
    if (dist && G.length && !G.some(function (g) { return dist[g.z * zone.w + g.x] >= 0; })) errors.push('no path P to G');
    function minDistToP(x, z) {
      var best = Infinity;
      P.forEach(function (p) {
        var dx = x - (p.x + 0.5), dz = z - (p.z + 0.5);
        var d = Math.sqrt(dx * dx + dz * dz);
        if (d < best) best = d;
      });
      return best;
    }
    S.forEach(function (s) {
      if (P.length && minDistToP(s.x + 0.5, s.z + 0.5) < MIN_SPAWN_DIST) errors.push('spawn ' + s.x + ',' + s.z + ' within 8 m of P');
      if (dist && dist[s.z * zone.w + s.x] < 0) errors.push('spawn ' + s.x + ',' + s.z + ' enclosed');
    });
    spawns.forEach(function (s) {
      if (P.length && minDistToP(s.x, s.z) < MIN_SPAWN_DIST) errors.push('robot spawn ' + s.type + ' within 8 m of P');
    });
    var cover = coverPieces(zone);
    if (cover < MIN_COVER) errors.push('only ' + cover + ' cover pieces');
    if (!zone.find('a').length) errors.push('no ammo box');
    return { ok: errors.length === 0, errors: errors, cover: cover, spawnCells: S.length };
  }

  function zoneCount(L) { return Math.min(7, 4 + Math.floor((L - 20) / 10)); }
  function budget(L) { return 8 + 1.6 * L; }

  // Fixed shuffled theme order per slot seed.
  function themeOrder(slotSeed) {
    return IB.RNG.shuffle(IB.RNG.mulberry32((slotSeed >>> 0) ^ 0x1B0B), IB.THEME_ORDER);
  }

  function themeFor(L, slotSeed) {
    var order = themeOrder(slotSeed);
    return order[(((L - 21) % order.length) + order.length) % order.length];
  }

  // Spend the zone budget on robots whose first level <= L, honouring caps.
  function allocate(rng, L, cells) {
    var R = IB.RNG;
    var types = IB.ENEMY_ORDER.filter(function (id) { return IB.ENEMIES[id].first <= L; });
    var left = budget(L);
    var counts = {};
    var list = [];
    for (;;) {
      var cand = types.filter(function (id) {
        return IB.ENEMIES[id].cost <= left + 1e-9 && (CAPS[id] === undefined || (counts[id] || 0) < CAPS[id]);
      });
      if (!cand.length) break;
      var id = R.pick(rng, cand);
      counts[id] = (counts[id] || 0) + 1;
      left -= IB.ENEMIES[id].cost;
      list.push(id);
    }
    list = R.shuffle(rng, list);
    var waves = Math.min(3, 1 + Math.floor(list.length / 8));
    var spawns = list.map(function (type, i) {
      var c = R.pick(rng, cells);
      return { type: type, x: c.x + 0.5, z: c.z + 0.5, wave: type === 'binhive' ? 0 : Math.floor(i * waves / list.length) };
    });
    return { spawns: spawns, counts: counts, spent: budget(L) - left, waves: waves };
  }

  /* generate(L, slotSeed, templates) ->
     {level, theme, variant, palette, zones:[{grid, spawns:[{type,x,z,wave}], w, h, template, rot, mirror,
      entry, exit, budget, spent, counts, waves, attempts, valid}], boss, bossScale, arena, valid, seed} */
  function generate(L, slotSeed, templates) {
    if (!templates || !templates.length) throw new Error('LevelGen.generate: no templates');
    var R = IB.RNG;
    var seed = ((slotSeed >>> 0) ^ L) >>> 0;
    var rng = R.mulberry32(seed);
    var parsed = templates.map(function (t) { return toRows(t); });
    var zones = [];
    var n = zoneCount(L);
    var allValid = true;
    for (var zi = 0; zi < n; zi++) {
      var out = null, last = null;
      for (var attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        var ti = R.int(rng, 0, parsed.length - 1);
        var rot = R.int(rng, 0, 3);
        var mirror = rng() < 0.5;
        var zone = parseZone(transform(parsed[ti], rot, mirror));
        var v = validate(zone);
        last = { zone: zone, ti: ti, rot: rot, mirror: mirror, errors: v.errors, attempt: attempt };
        if (!v.ok) continue;
        var alloc = allocate(rng, L, zone.find('S'));
        var p = zone.find('P')[0], g = zone.find('G')[0];
        out = {
          grid: zone.rows, w: zone.w, h: zone.h, spawns: alloc.spawns, template: ti, rot: rot, mirror: mirror,
          entry: { x: p.x + 0.5, z: p.z + 0.5 }, exit: { x: g.x + 0.5, z: g.z + 0.5 },
          budget: budget(L), spent: alloc.spent, counts: alloc.counts, waves: alloc.waves,
          attempts: attempt + 1, valid: true
        };
        break;
      }
      if (!out) {
        allValid = false;
        out = { grid: last.zone.rows, w: last.zone.w, h: last.zone.h, spawns: [], template: last.ti, rot: last.rot,
          mirror: last.mirror, entry: null, exit: null, budget: budget(L), spent: 0, counts: {}, waves: 0,
          attempts: MAX_ATTEMPTS, valid: false, errors: last.errors };
      }
      zones.push(out);
    }
    var theme = themeFor(L, slotSeed);
    var boss = IB.bossForLevel(L);
    return {
      level: L, theme: theme, variant: null, palette: IB.THEMES[theme].palette.slice(), zones: zones,
      boss: boss, bossScale: boss ? IB.bossScale(L) : null, bossTheme: boss ? IB.BOSSES[boss].theme : null,
      arena: !!boss, valid: allValid, seed: seed
    };
  }

  IB.LevelGen = {
    generate: generate, parseZone: parseZone, validate: validate, transform: transform,
    zoneCount: zoneCount, budget: budget, themeOrder: themeOrder, themeFor: themeFor,
    coverPieces: coverPieces, isBlocking: isBlockingChar, CAPS: CAPS
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
