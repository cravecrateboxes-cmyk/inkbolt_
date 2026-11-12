/* INKBOLT zones: ASCII zone layouts -> merged toon geometry, AABB collision (2 m grid),
   gates, trail arrows, exit hatch, nav grid + BFS flow fields.

   Walkable surfaces (generic, data-driven): a kit piece marks a collision box as something ground robots may walk ON
   by naming its Blender empty <Piece>_WCOL<n> instead of <Piece>_COL<n> (decks, stair steps, ramps as stepped boxes,
   bridge planks, a raised gazebo floor). Such boxes get box.walk = true. The world answers floorAt(x, z, y): the top
   of the highest walkable box under a point, at or below y (0 = the ground plane). A zone that holds walkable boxes
   gets a two-layer nav grid (layer 0: the lowest standable surface of each cell, layer 1: a deck above it with
   headroom underneath); neighbouring cells connect only when their surfaces differ by at most NAV_STEP, so the BFS
   flow field climbs stairs and ramps and never "teleports" up a deck edge. Zones without walkable boxes keep the
   original single-layer grid and code path unchanged. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var Z = IB.Zones = {};
  var CELL = 2;          // collision grid cell (m)
  var NAV = 0.5;         // nav cell (m)
  var TRAIL_LEN = 12;
  var NAV_STEP = 0.4;
  var NAV_LAYERS = 4;    // walkable surfaces kept per nav cell (ground, stair flights / branch steps stacked above, a deck)    // largest rise between neighbouring walkable nav cells (robots' step-up, ai.js STEP_UP)

  // ---------------- parsing ----------------
  /* A zone file is the floor plan, optionally followed by upper layers: a line "@layer <y>" starts a grid of the same
     size whose symbols stand at height y (decks, rails, props, spawns and pickups on a mezzanine or a tree platform). */
  function mkGrid(rows, w0, out) {
    rows = rows.filter(function (r) { return r.length > 0; });
    var w = w0 || 0; if (!w0) rows.forEach(function (r) { w = Math.max(w, r.length); });
    rows = rows.map(function (r) { r = r.slice(0, w); while (r.length < w) r += '.'; return r; });
    return { w: w, h: rows.length, rows: rows, at: function (c, r) { return (r < 0 || r >= rows.length || c < 0 || c >= w) ? out : rows[r][c]; } };
  }
  Z.parse = function (text) {
    var lines = text.replace(/\r/g, '').split('\n'), base = [], layers = [], cur = base;
    lines.forEach(function (l) {
      var m = /^@layer\s+(-?[\d.]+)/.exec(l);
      if (m) { cur = []; layers.push({ y: parseFloat(m[1]), rows: cur }); } else cur.push(l);
    });
    var g = mkGrid(base, 0, '#');
    g.layers = layers.map(function (L) {
      var lg = mkGrid(L.rows, g.w, '.');
      while (lg.rows.length < g.h) lg.rows.push(new Array(g.w + 1).join('.'));
      lg.h = g.h; lg.y = L.y; return lg;
    });
    return g;
  };

  // greedy rectangle merge of cells with char ch -> [{c,r,w,h}]
  function rects(grid, ch) {
    var used = [], out = [], r, c;
    for (r = 0; r < grid.h; r++) used.push(new Uint8Array(grid.w));
    for (r = 0; r < grid.h; r++) for (c = 0; c < grid.w; c++) {
      if (used[r][c] || grid.rows[r][c] !== ch) continue;
      var w = 1; while (c + w < grid.w && !used[r][c + w] && grid.rows[r][c + w] === ch) w++;
      var h = 1, ok = true;
      while (ok && r + h < grid.h) {
        for (var k = 0; k < w; k++) if (used[r + h][c + k] || grid.rows[r + h][c + k] !== ch) { ok = false; break; }
        if (ok) h++;
      }
      for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) used[r + y][c + x] = 1;
      out.push({ c: c, r: r, w: w, h: h });
    }
    return out;
  }
  // connected blocks (for containers / landmarks) as bounding rects, split to max size
  function blocks(grid, ch, maxW, maxH) {
    var rs = rects(grid, ch), out = [];
    rs.forEach(function (R) {
      for (var y = 0; y < R.h; y += maxH) for (var x = 0; x < R.w; x += maxW)
        out.push({ c: R.c + x, r: R.r + y, w: Math.min(maxW, R.w - x), h: Math.min(maxH, R.h - y) });
    });
    return out;
  }
  function find(grid, ch) {
    var out = [];
    for (var r = 0; r < grid.h; r++) for (var c = 0; c < grid.w; c++) if (grid.rows[r][c] === ch) out.push({ c: c, r: r });
    return out;
  }
  function hash(a, b) { var h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }

  // ---------------- collision world ----------------
  function World() { this.boxes = []; this.grid = new Map(); this.walkN = 0; this.terrains = []; }
  /* ground height: 0, or a zone's terrain heightfield (1 m vertex grid, bilinear) for themes with bumpy ground */
  World.prototype.groundAt = function (x, z) {
    if (this.voids) { var vy = this.voidAt(x, z); if (vy !== null) return vy; }
    for (var i = 0; i < this.terrains.length; i++) {
      var T = this.terrains[i], u = x - T.ox, v = z - T.oz;
      if (u < 0 || v < 0 || u >= T.w || v >= T.h) continue;
      var c = Math.floor(u), r = Math.floor(v), fu = u - c, fv = v - r, W = T.w + 1, H = T.hf;
      var a = H[r * W + c], b = H[r * W + c + 1], d = H[(r + 1) * W + c], e = H[(r + 1) * W + c + 1];
      return (a * (1 - fu) + b * fu) * (1 - fv) + (d * (1 - fu) + e * fu) * fv;
    }
    return 0;
  };
  /* open air (rooftops.js): over a void mask's cells the ground is far down (the street), so whoever walks off a
     roof falls. test(c, r) -> ground height or null (solid floor) for the mask's cells (1 m, from ox, oz). */
  World.prototype.addVoid = function (ox, oz, w, h, test) {
    var d = new Float32Array(w * h);
    for (var r = 0; r < h; r++) for (var c = 0; c < w; c++) { var v = test(c, r); d[r * w + c] = v === null ? NaN : v; }
    (this.voids || (this.voids = [])).push({ ox: ox, oz: oz, w: w, h: h, d: d });
  };
  World.prototype.voidAt = function (x, z) {
    for (var i = 0; i < this.voids.length; i++) {
      var V = this.voids[i], c = Math.floor(x - V.ox), r = Math.floor(z - V.oz);
      if (c < 0 || r < 0 || c >= V.w || r >= V.h) continue;
      var v = V.d[r * V.w + c]; return typeof v === 'number' && v === v ? v : null;
    }
    return null;
  };
  var _gn = { x: 0, y: 1, z: 0 };
  World.prototype.groundNormal = function (x, z) {
    var hx = this.groundAt(x + 0.25, z) - this.groundAt(x - 0.25, z), hz = this.groundAt(x, z + 0.25) - this.groundAt(x, z - 0.25);
    var L = Math.sqrt(hx * hx * 4 + 1 + hz * hz * 4); _gn.x = -hx * 2 / L; _gn.y = 1 / L; _gn.z = -hz * 2 / L; return _gn;
  };
  // first t along a ray where it dips under the terrain (march 0.35 m, then bisect), or Infinity
  World.prototype.rayTerrain = function (ox, oy, oz, dx, dy, dz, maxT) {
    if (!this.terrains.length) return Infinity;
    var top = this.terrainTop || 0, step = 0.35, prev = 0;
    for (var t = 0; t <= maxT; t += step) {
      var y = oy + dy * t;
      if (y > top + 0.01 && dy >= 0) return Infinity;
      if (y < this.groundAt(ox + dx * t, oz + dz * t)) {
        var lo = prev, hi = t;
        for (var k = 0; k < 8; k++) { var m = (lo + hi) / 2; if (oy + dy * m < this.groundAt(ox + dx * m, oz + dz * m)) hi = m; else lo = m; }
        return hi;
      }
      prev = t;
    }
    return Infinity;
  };
  World.prototype.add = function (x0, y0, z0, x1, y1, z1, kind, zone) {
    var b = { id: this.boxes.length, x0: Math.min(x0, x1), y0: y0, z0: Math.min(z0, z1), x1: Math.max(x0, x1), y1: y1, z1: Math.max(z0, z1), on: true, kind: kind || 'wall', zone: zone === undefined ? -1 : zone };
    this.boxes.push(b);
    var cx0 = Math.floor(b.x0 / CELL), cx1 = Math.floor(b.x1 / CELL), cz0 = Math.floor(b.z0 / CELL), cz1 = Math.floor(b.z1 / CELL);
    for (var i = cx0; i <= cx1; i++) for (var k = cz0; k <= cz1; k++) {
      var key = i * 73856 + k; var a = this.grid.get(key); if (!a) { a = []; this.grid.set(key, a); } a.push(b.id);
    }
    return b;
  };
  /* an invisible movement-only boundary (kind 'bound'): players, robots and bouncing grenades collide with it, rays
     (shots, line of sight) and projectiles pass through, so nothing ever hits a surface that is not drawn */
  var BOUND_TOP = 400;
  World.prototype.bound = function (x0, y0, z0, x1, y1, z1, zone) {
    var b = this.add(x0, y0, z0, x1, y1 === undefined ? BOUND_TOP : y1, z1, 'bound', zone); b.noRay = true; return b;
  };
  var _q = [], _stamp = 1, _seen = new Uint32Array(8192);
  World.prototype.query = function (x0, z0, x1, z1, out) {
    out.length = 0; _stamp++;
    if (this.boxes.length > _seen.length) _seen = new Uint32Array(this.boxes.length * 2);
    var cx0 = Math.floor(x0 / CELL), cx1 = Math.floor(x1 / CELL), cz0 = Math.floor(z0 / CELL), cz1 = Math.floor(z1 / CELL);
    for (var i = cx0; i <= cx1; i++) for (var k = cz0; k <= cz1; k++) {
      var a = this.grid.get(i * 73856 + k); if (!a) continue;
      for (var j = 0; j < a.length; j++) { var id = a[j]; if (_seen[id] === _stamp) continue; _seen[id] = _stamp; var b = this.boxes[id]; if (b.on) out.push(b); }
    }
    return out;
  };
  // Ray vs boxes using grid DDA on XZ. Returns hit {t, box, nx,ny,nz} or null. Ground plane y=0 included.
  var _hit = { t: 0, box: null, nx: 0, ny: 0, nz: 0 };
  World.prototype.ray = function (ox, oy, oz, dx, dy, dz, maxT, skipKind) {
    var best = maxT, bb = null, bnx = 0, bny = 0, bnz = 0;
    if (dy < -1e-6) {
      var tg = -oy / dy;
      if (this.voids && tg > 0) { var vg = this.voidAt(ox + dx * tg, oz + dz * tg); if (vg !== null) tg = (vg - oy) / dy; }   // open air: the street far below
      if (tg > 0 && tg < best) { best = tg; bb = null; bnx = 0; bny = 1; bnz = 0; }
    }
    if (this.terrains.length) {
      var tt0 = this.rayTerrain(ox, oy, oz, dx, dy, dz, best);
      if (tt0 < best) { var tn = this.groundNormal(ox + dx * tt0, oz + dz * tt0); best = tt0; bb = null; bnx = tn.x; bny = tn.y; bnz = tn.z; }
    }
    _stamp++;

    var cx = Math.floor(ox / CELL), cz = Math.floor(oz / CELL);
    var stepX = dx > 0 ? 1 : -1, stepZ = dz > 0 ? 1 : -1;
    var tDX = Math.abs(dx) > 1e-9 ? CELL / Math.abs(dx) : 1e9, tDZ = Math.abs(dz) > 1e-9 ? CELL / Math.abs(dz) : 1e9;
    var tMX = Math.abs(dx) > 1e-9 ? ((dx > 0 ? (cx + 1) * CELL - ox : ox - cx * CELL) / Math.abs(dx)) : 1e9;
    var tMZ = Math.abs(dz) > 1e-9 ? ((dz > 0 ? (cz + 1) * CELL - oz : oz - cz * CELL) / Math.abs(dz)) : 1e9;
    var tCur = 0, guard = 0;
    while (tCur <= best && guard++ < 400) {
      var a = this.grid.get(cx * 73856 + cz);
      if (a) for (var j = 0; j < a.length; j++) {
        var id = a[j]; if (_seen[id] === _stamp) continue; _seen[id] = _stamp;
        var b = this.boxes[id]; if (!b.on || b.noRay || (skipKind && b.kind === skipKind)) continue;
        // slab test
        var t0 = 0, t1 = best, n = 0, s = 0, tt, ta, tb, inv;
        inv = 1 / (dx || 1e-12); ta = (b.x0 - ox) * inv; tb = (b.x1 - ox) * inv; if (ta > tb) { tt = ta; ta = tb; tb = tt; } if (ta > t0) { t0 = ta; n = 0; } if (tb < t1) t1 = tb; if (t0 > t1) continue;
        inv = 1 / (dy || 1e-12); ta = (b.y0 - oy) * inv; tb = (b.y1 - oy) * inv; if (ta > tb) { tt = ta; ta = tb; tb = tt; } if (ta > t0) { t0 = ta; n = 1; } if (tb < t1) t1 = tb; if (t0 > t1) continue;
        inv = 1 / (dz || 1e-12); ta = (b.z0 - oz) * inv; tb = (b.z1 - oz) * inv; if (ta > tb) { tt = ta; ta = tb; tb = tt; } if (ta > t0) { t0 = ta; n = 2; } if (tb < t1) t1 = tb; if (t0 > t1) continue;
        if (t0 > 0 && t0 < best) {
          best = t0; bb = b; bnx = bny = bnz = 0;
          if (n === 0) bnx = dx > 0 ? -1 : 1; else if (n === 1) bny = dy > 0 ? -1 : 1; else bnz = dz > 0 ? -1 : 1;
        }
      }
      if (tMX < tMZ) { tCur = tMX; tMX += tDX; cx += stepX; } else { tCur = tMZ; tMZ += tDZ; cz += stepZ; }
    }
    if (best >= maxT) return null;
    _hit.t = best; _hit.box = bb; _hit.nx = bnx; _hit.ny = bny; _hit.nz = bnz;
    return _hit;
  };
  // top of the highest walkable box (box.walk) whose footprint holds (x, z) and whose top is at or below y; 0 (the
  // ground plane) when there is none. Worlds without walkable boxes answer 0 straight away.
  World.prototype.floorAt = function (x, z, y) {
    var g0 = this.terrains.length || this.voids ? this.groundAt(x, z) : 0;
    if (!this.walkN) return g0;
    var a = this.grid.get(Math.floor(x / CELL) * 73856 + Math.floor(z / CELL)), best = g0;
    if (!a) return g0;
    for (var j = 0; j < a.length; j++) {
      var b = this.boxes[a[j]];
      if (!b.walk || !b.on || b.y1 > y || b.y1 <= best || x < b.x0 || x > b.x1 || z < b.z0 || z > b.z1) continue;
      best = b.y1;
    }
    return best;
  };
  World.prototype.los = function (ax, ay, az, bx, by, bz) {
    var dx = bx - ax, dy = by - ay, dz = bz - az, d = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (d < 1e-4) return true;
    return !this.ray(ax, ay, az, dx / d, dy / d, dz / d, d - 0.05);
  };
  Z.World = World;

  // ---------------- themes (Blender kit families; src/data/themes/*.js) ----------------
  function themeOf(plan) { return IB.THEME_DEFS[plan.themeId] || IB.THEME_DEFS.toytown; }
  Z.themeOf = themeOf;
  // theme.families (optional): other kit families a theme places pieces from (by their full KIT_<FAMILY>_ names)
  Z.themeFamilies = function (plan) { var t = themeOf(plan); return [t.family].concat(t.families || []); };
  function col(hex, fallback) { return new THREE.Color(hex || fallback || '#CCCCCC'); }
  var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _up = new THREE.Vector3(0, 1, 0), _p = new THREE.Vector3(), _s1 = new THREE.Vector3(1, 1, 1);
  function M(x, y, z, yaw) { _q.setFromAxisAngle(_up, yaw || 0); _p.set(x, y, z); return _m.clone().compose(_p, _q, _s1); }

  // pieces collected per Blender family, merged into one mesh per family per zone
  function Parts(theme) { this.lists = {}; this.roof = []; this.theme = theme; }
  var PID = 0;
  Z.pidNames = {};
  Parts.prototype.add = function (name, x, y, z, yaw, m, paint) {
    name = IB.themePiece(this.theme, name);
    var fam = IB.Assets.family[name];
    if (!fam || !IB.Assets.geo[name]) throw new Error('INKBOLT kit piece missing: ' + name);
    var g = IB.Assets.placed(name, m || M(x, y, z, yaw));
    if (paint) repaint(g, paint);
    if (Z.ZCHECK) {   // tag each placed piece so the cross-piece z-fighting check can tell pieces apart
      var n = g.attributes.position.count, a = new Float32Array(n); a.fill(++PID);
      g.setAttribute('pid', new THREE.BufferAttribute(a, 1)); Z.pidNames[PID] = name;
    }
    (this.lists[fam] || (this.lists[fam] = [])).push(g);
    var GL = glowOf(this.theme, name);
    if (GL) {
      var gm = (m || M(x, y, z, yaw)).clone(), ge = gm.elements, gh = hash(Math.round(ge[12] * 7 + ge[13] * 3), Math.round(ge[14] * 13)), self = this;
      [].concat(GL).forEach(function (D) { (self.glow || (self.glow = [])).push({ def: D, m: gm, k: Math.floor(gh * (D.groups || 1)) }); });
    }
  };
  /* theme.glow (optional): { 'Piece': { piece: 'Piece_Glow', groups: 3, blend: 'add' | 'basic', spin: false } | [defs] }. A
     companion piece (modelled without an outline shell) placed with the same transform as every copy of Piece, drawn
     unlit (blend 'add': additive, a hologram or a force field) in one mesh per zone and phase group (copies are dealt
     to `groups` groups by position), or one mesh per copy with spin (so the theme can turn it). level.glows lists
     them ({ mesh, piece, group, zone, def }) for the theme to blink, pulse or turn (backdrop.build api.tick). */
  function glowOf(theme, full) {
    if (!theme.glow) return null;
    if (!theme._glowFull) { theme._glowFull = {}; Object.keys(theme.glow).forEach(function (k) { theme._glowFull[IB.themePiece(theme, k)] = theme.glow[k]; }); }
    return theme._glowFull[full] || null;
  }
  var glowMats = {};
  function glowMat(fam, blend) {
    var key = fam + blend;
    if (!glowMats[key]) {
      var add = blend === 'add';
      glowMats[key] = new THREE.MeshBasicMaterial({ map: IB.Assets.mat[fam].map, transparent: add, blending: add ? THREE.AdditiveBlending : THREE.NormalBlending, depthWrite: !add, side: add ? THREE.DoubleSide : THREE.FrontSide });
    }
    return glowMats[key];
  }
  function buildGlows(level, zone, P) {
    var by = {};
    (P.glow || []).forEach(function (e) {
      var full = IB.themePiece(P.theme, e.def.piece), fam = IB.Assets.family[full];
      if (!fam || !IB.Assets.geo[full]) throw new Error('INKBOLT glow piece missing: ' + full);
      var mat = glowMat(fam, e.def.blend || 'basic');
      if (e.def.spin) {
        var one = new THREE.Mesh(IB.Assets.get(full), mat);
        e.m.decompose(one.position, one.quaternion, one.scale);
        one.userData.yaw0 = new THREE.Euler().setFromQuaternion(one.quaternion, 'YXZ').y;
        zone.group.add(one);
        level.glows.push({ mesh: one, piece: e.def.piece, group: e.k, zone: zone.idx, def: e.def });
        return;
      }
      var key = full + '#' + e.k;
      (by[key] || (by[key] = { full: full, mat: mat, def: e.def, k: e.k, list: [] })).list.push(IB.Assets.placed(full, e.m));
    });
    Object.keys(by).forEach(function (key) {
      var B = by[key], mesh = new THREE.Mesh(IB.Assets.merge(B.list), B.mat);
      if (B.def.blend === 'add') mesh.renderOrder = 2;
      zone.group.add(mesh);
      level.glows.push({ mesh: mesh, piece: B.def.piece, group: B.k, zone: zone.idx, def: B.def });
    });
  }
  /* Symbol option `paint` (generic): one model in many paint jobs. Kit pieces colour their faces by palette cell (an
     8 x 8 grid on the family's 64 px palette texture; cell index = row * 8 + column, the order the Blender palette lists
     them), so a placed copy is repainted by moving the UVs of its `from` cells onto other cells:
       paint: { from: [cell, ...], to: [[cell, ...], ...] }   one paint job per placed piece, picked by hash
       paint: { from: [cell, ...], to: function (zoneIdx, layerY, hash) -> [cell, ...] | null }   (per zone / level)
     Used by kit-parking for car colours and the per-level colour bands on columns and ramps. */
  function cellUV(i) { return [((i % 8) + 0.5) / 8, 1 - (Math.floor(i / 8) + 0.5) / 8]; }
  function repaint(g, map) {
    var uv = g.attributes.uv.array;
    for (var i = 0; i < uv.length; i += 2) {
      var cell = Math.floor(uv[i] * 8) + 8 * Math.floor((1 - uv[i + 1]) * 8);
      for (var k = 0; k < map.length; k++) if (map[k][0] === cell) { var t = cellUV(map[k][1]); uv[i] = t[0]; uv[i + 1] = t[1]; break; }
    }
  }
  function paintFor(d, zi, yb, h) {
    var P = d.paint; if (!P) return null;
    var to = typeof P.to === 'function' ? P.to(zi, yb || 0, h) : P.to[Math.min(P.to.length - 1, Math.floor(h * P.to.length))];
    return to ? P.from.map(function (f, i) { return [f, to[i]]; }) : null;
  }
  Z.repaint = repaint;
  function meshesFor(P, group) {
    var out = [];
    Object.keys(P.lists).forEach(function (fam) {
      var m = new THREE.Mesh(IB.Assets.merge(P.lists[fam]), IB.Assets.mat[fam]);
      group.add(m); out.push(m);
    });
    return out;
  }
  // Cross-piece z-fighting check: coplanar (< 2.5 mm), same-facing, overlapping triangles from different
  // placed pieces in a merged zone mesh. Returns a list of problems (empty = clean).
  Z.zfight = function (mesh) {
    var g = mesh.geometry, pos = g.attributes.position.array, pid = g.attributes.pid, idx = g.index.array;
    if (!pid) return [];
    var buckets = new Map(), out = [], va = new THREE.Vector3(), vb = new THREE.Vector3(), vc = new THREE.Vector3(), n = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
    var hull = g.attributes.aHull.array;
    var tris = [];
    for (var t = 0; t < idx.length; t += 3) {
      var i0 = idx[t], i1 = idx[t + 1], i2 = idx[t + 2];
      if (hull[i0 * 3] || hull[i0 * 3 + 1] || hull[i0 * 3 + 2]) continue;   // outline shell faces don't count
      va.fromArray(pos, i0 * 3); vb.fromArray(pos, i1 * 3); vc.fromArray(pos, i2 * 3);
      n.crossVectors(e1.subVectors(vb, va), e2.subVectors(vc, va));
      var area = n.length() / 2; if (area < 1e-6) continue;
      n.normalize();
      if (n.y < -0.99 && Math.abs(va.y) < 0.01) continue;   // bottoms resting on the ground are never seen
      var d = n.dot(va), key = Math.round(n.x * 50) + ',' + Math.round(n.y * 50) + ',' + Math.round(n.z * 50);
      var tri = { p: pid.array[i0], d: d, n: n.clone(), a: va.clone(), b: vb.clone(), c: vc.clone() };
      var lst = buckets.get(key); if (!lst) { lst = []; buckets.set(key, lst); } lst.push(tri);
    }
    function proj(tri) {
      var u = Math.abs(tri.n.y) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0).cross(tri.n).normalize(), v = new THREE.Vector3().crossVectors(tri.n, u);
      return [[tri.a.dot(u), tri.a.dot(v)], [tri.b.dot(u), tri.b.dot(v)], [tri.c.dot(u), tri.c.dot(v)]];
    }
    function ccw(P) { var s2 = 0; for (var i = 0; i < P.length; i++) { var q = P[(i + 1) % P.length]; s2 += P[i][0] * q[1] - q[0] * P[i][1]; } return s2 > 0 ? P : P.slice().reverse(); }
    function clip(P, a, b) { var o = []; for (var i = 0; i < P.length; i++) { var p = P[i], q = P[(i + 1) % P.length]; var sp = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]), sq = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0]); if (sp >= 0) o.push(p); if ((sp >= 0) !== (sq >= 0)) { var tt = sp / (sp - sq); o.push([p[0] + (q[0] - p[0]) * tt, p[1] + (q[1] - p[1]) * tt]); } } return o; }
    function areaOf(P) { var s2 = 0; for (var i = 0; i < P.length; i++) { var q = P[(i + 1) % P.length]; s2 += P[i][0] * q[1] - q[0] * P[i][1]; } return Math.abs(s2) / 2; }
    buckets.forEach(function (lst) {
      if (lst.length < 2) return;
      lst.sort(function (x, y) { return x.d - y.d; });
      for (var i = 0; i < lst.length && out.length < 20; i++) {
        for (var j = i + 1; j < lst.length; j++) {
          var A = lst[i], B = lst[j];
          if (B.d - A.d > 0.0025) break;
          if (A.p === B.p) continue;
          var pa = A.pa || (A.pa = ccw(proj(A))), pb = B.pb || (B.pb = ccw(proj(B))), inter = pa;
          for (var k = 0; k < 3 && inter.length >= 3; k++) inter = clip(inter, pb[k], pb[(k + 1) % 3]);
          if (inter.length >= 3 && areaOf(inter) > 1e-5) { out.push(Z.pidNames[A.p] + ' / ' + Z.pidNames[B.p] + ' at ' + A.a.toArray().map(function (v) { return v.toFixed(2); }).join(',')); break; }
        }
      }
    });
    return out;
  };
  function cellIs(grid, c, r, set) { return set.indexOf(grid.at(c, r)) >= 0; }
  function pick(list, h) { return list[Math.min(list.length - 1, Math.floor(h * list.length))]; }

  // collision boxes authored in Blender as <Piece>_COL<n> empties (centre + half extents), cached per piece
  var colCache = {};
  function colsOf(name) {
    if (colCache[name] !== undefined) return colCache[name];
    var node = IB.Assets.node[name], out = [];
    if (node) node.children.forEach(function (c) {
      // <Piece>_COL<n>: solid box; <Piece>_WCOL<n>: a box robots may also walk on (deck, step, plank)
      if (/_W?COL\d*$/.test(c.name)) out.push({ x: c.position.x, y: c.position.y, z: c.position.z, hx: Math.abs(c.scale.x), hy: Math.abs(c.scale.y), hz: Math.abs(c.scale.z), walk: /_WCOL\d*$/.test(c.name), piece: name });
    });
    colCache[name] = out.length ? out : null;
    return colCache[name];
  }
  Z.colsOf = colsOf;
  // quarter-turn yaw: x' = x c + z s, z' = -x s + z c (three.js Y rotation)
  function addCols(world, cols, x, z, yaw, kind, zi) {
    var c = Math.round(Math.cos(yaw)), s = Math.round(Math.sin(yaw));
    cols.forEach(function (b) {
      var cx = b.x * c + b.z * s, cz = -b.x * s + b.z * c, hx = c !== 0 ? b.hx : b.hz, hz = c !== 0 ? b.hz : b.hx;
      var nb = world.add(x + cx - hx, b.y - b.hy, z + cz - hz, x + cx + hx, b.y + b.hy, z + cz + hz, kind, zi);
      if (b.piece) nb.piece = b.piece;   // source kit piece (collision audit)
      if (b.walk) { nb.walk = true; world.walkN++; }
    });
  }
  // d.with: { piece: [extra pieces] } placed with the same transform (a big landmark split into parts that each
  // keep to the theme's per-piece triangle budget); their collision boxes are added too
  function addWith(P, world, theme, d, name, x, y, zz, yaw, zi) {
    var extra = d.with && d.with[name];
    if (!extra) return;
    extra.forEach(function (n2) {
      P.add(n2, x, y, zz, yaw);
      var c2 = d.collide !== false && colsOf(IB.themePiece(theme, n2));
      if (c2) addCols(world, c2, x, zz, yaw, d.kind || 'cover', zi);
    });
  }
  function boxCols(w, d, h) { return [{ x: 0, y: h / 2, z: 0, hx: w / 2, hy: h / 2, hz: d / 2 }]; }

  // '#': exposed cells get a wall module; building interiors get a flat roof
  function buildWalls(P, z, grid, theme, world) {
    var W = theme.wall || {}, H = W.height || 3, PS = W.passage;
    rects(grid, '#').forEach(function (R) {
      world.add(z.ox + R.c, 0, z.oz + R.r, z.ox + R.c + R.w, H, z.oz + R.r + R.h, 'wall', z.idx);
    });
    /* wall.passage = { ch, solid: [[y0, y1], ...] } (optional): a doorway cell in a wall line. It counts as wall for the
       modules around it (facing, exposure) and gets a module from the chooser like any wall cell, but it is solid only
       in the given height bands (lintels), so people walk through it (a walk-in shop's open front, on each storey) */
    // (ch may list several symbols: doorways of different doors, see game/doors.js)
    var PCH = PS ? PS.ch.split('') : [];
    PCH.forEach(function (pc) {
      rects(grid, pc).forEach(function (R) {
        PS.solid.forEach(function (b) { world.add(z.ox + R.c, b[0], z.oz + R.r, z.ox + R.c + R.w, b[1], z.oz + R.r + R.h, 'wall', z.idx); });
      });
    });
    var WALLISH = '#GE' + (PS ? PS.ch : '');
    function solid(c, r) { return cellIs(grid, c, r, WALLISH); }
    PCH.reduce(function (a, pc) { return a.concat(find(grid, pc)); }, find(grid, '#')).forEach(function (p) {
      var exposed = !solid(p.c - 1, p.r) || !solid(p.c + 1, p.r) || !solid(p.c, p.r - 1) || !solid(p.c, p.r + 1) ||
        !solid(p.c - 1, p.r - 1) || !solid(p.c + 1, p.r - 1) || !solid(p.c - 1, p.r + 1) || !solid(p.c + 1, p.r + 1);
      if (!exposed) { P.roof.push(p); return; }
      var horiz = cellIs(grid, p.c - 1, p.r, WALLISH) || cellIs(grid, p.c + 1, p.r, WALLISH);
      var vert = cellIs(grid, p.c, p.r - 1, WALLISH) || cellIs(grid, p.c, p.r + 1, WALLISH);
      // facing from the open cardinal neighbours: 'S','N','E','W', 'corner' (two adjacent open sides) or 'none'
      var oS = !solid(p.c, p.r + 1), oN = !solid(p.c, p.r - 1), oE = !solid(p.c + 1, p.r), oW = !solid(p.c - 1, p.r);
      var nOpen = oS + oN + oE + oW, face = nOpen === 0 ? 'none' : nOpen === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
      // wall.faceOf (optional): the theme settles the facing of a cell open on two opposite sides (a shop front with
      // the hall on one side and the shop's own room on the other)
      if (W.faceOf) face = W.faceOf(p.c, p.r, grid, face) || face;
      var name = W.choose ? W.choose(p.c, p.r, horiz, horiz && vert, hash, grid, face) : pick(W.pieces, hash(p.c * 13, p.r * 17));
      if (!name) return;   // the chooser leaves cells a gate built-in covers empty (their collision stays)
      // a list of names: parts stacked in one cell with one transform (a storefront per storey over a shared shell)
      // wall modules face +/-Z; rotate for vertical runs. faceOpen: turn the module's +Z face (Blender -Y) to the open side
      var yaw = (!horiz && vert) ? Math.PI / 2 : 0;
      if (W.facing === 'open' && face !== 'none' && face !== 'corner') yaw = { S: 0, N: Math.PI, E: Math.PI / 2, W: -Math.PI / 2 }[face];
      else if (W.faceOpen) {
        if (yaw === 0 && !solid(p.c, p.r - 1) && solid(p.c, p.r + 1)) yaw = Math.PI;
        if (yaw !== 0 && !solid(p.c - 1, p.r) && solid(p.c + 1, p.r)) yaw = -Math.PI / 2;   // +Z face toward the open (west) side
      }
      [].concat(name).forEach(function (n) {
        // an entry may be { piece, turn }: that part turned by `turn` more (one face piece drawn on any side of the cell)
        var tn = 0; if (n && typeof n === 'object') { tn = n.turn || 0; n = n.piece; }
        P.add(n, z.ox + p.c + 0.5, 0, z.oz + p.r + 0.5, yaw + tn);
        // wall.cols (opt-in): a module's own _COL boxes collide too (a buttress standing out into the room)
        var wc = W.cols && colsOf(IB.themePiece(theme, n));
        if (wc) addCols(world, wc, z.ox + p.c + 0.5, z.oz + p.r + 0.5, yaw + tn, 'wall', z.idx);
      });
    });
  }
  // height a piece stands at: the layer height, or (floor plan) the terrain under it; prefabs sink to their lowest corner
  function baseY(world, yb, x, z, hw, hd) {
    if (yb) return yb;
    if (!world.terrains.length) return 0;
    var y = world.groundAt(x, z);
    if (hw) [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(function (k) { y = Math.min(y, world.groundAt(x + k[0] * hw, z + k[1] * hd)); });
    return y;
  }
  function addColsY(world, cols, x, y0, z, yaw, kind, zi) {
    addCols(world, cols.map(function (b) { return { x: b.x, y: b.y + y0, z: b.z, hx: b.hx, hy: b.hy, hz: b.hz, walk: b.walk, piece: b.piece }; }), x, z, yaw, kind, zi);
  }
  // walkable deck (mezzanine floor) over each block of the symbol: slab with fascia, ink edge bands, collision
  function buildDeck(g, z, grid, world, ch, d, yb) {
    var D = d.deck, t = D.thick || 0.4, chars = ch + (D.with || '');
    if (chars.length > 1) { var rows2 = grid.rows.map(function (row) { var o = ''; for (var i = 0; i < row.length; i++) o += (D.with === '*' ? row[i] !== '.' && row[i] !== '#' : chars.indexOf(row[i]) >= 0) ? ch : row[i]; return o; }); grid = { w: grid.w, h: grid.h, rows: rows2, at: function (c, r) { return (r < 0 || r >= rows2.length || c < 0 || c >= grid.w) ? '.' : rows2[r][c]; } }; }
    var top = col(D.color, '#E8E0D0'), side = col(D.edge, '#BFB6A6'), under = col(D.under, '#D9D2C4');
    rects(grid, ch).forEach(function (R) {
      var x0 = z.ox + R.c, z0 = z.oz + R.r;
      g.box(x0 + R.w / 2, yb - t / 2, z0 + R.h / 2, R.w, t, R.h, side, { hull: false, topTint: top, noBottom: true });
      var bi = g.pos.length / 3;
      g.flat([[x0, z0], [x0 + R.w, z0], [x0 + R.w, z0 + R.h], [x0, z0 + R.h]], yb - t, under);
      for (var q = bi; q < g.pos.length / 3; q++) g.nor[q * 3 + 1] = -1;
      for (var ti = g.idx.length - 6; ti < g.idx.length; ti += 3) { var tmp = g.idx[ti + 1]; g.idx[ti + 1] = g.idx[ti + 2]; g.idx[ti + 2] = tmp; }
      var db = world.add(x0, yb - t, z0, x0 + R.w, yb, z0 + R.h, 'deck', z.idx); db.walk = true; world.walkN++;
    });
    // ink bands along exposed slab edges (top and bottom of the fascia), 1 cm proud, merged into runs
    var ink = col(PAL.ink);
    [[0, -1], [0, 1], [-1, 0], [1, 0]].forEach(function (n) {
      var along = n[1] ? [1, 0] : [0, 1], seen = {};
      find(grid, ch).forEach(function (p) {
        var key = p.c + ',' + p.r;
        if (seen[key] || grid.at(p.c + n[0], p.r + n[1]) === ch) return;
        var len = 0, c0 = p.c, r0 = p.r;
        while (grid.at(c0 + along[0] * len, r0 + along[1] * len) === ch && grid.at(c0 + along[0] * len + n[0], r0 + along[1] * len + n[1]) !== ch) { seen[(c0 + along[0] * len) + ',' + (r0 + along[1] * len)] = 1; len++; }
        var cx = z.ox + c0 + 0.5 + n[0] * 0.505 + along[0] * (len - 1) / 2, cz = z.oz + r0 + 0.5 + n[1] * 0.505 + along[1] * (len - 1) / 2;
        var sx = n[0] ? 0.02 : len, sz = n[1] ? 0.02 : len;
        g.box(cx, yb - 0.0275, cz, sx, 0.045, sz, ink, { hull: false });
        g.box(cx, yb - t + 0.0275, cz, sx, 0.045, sz, ink, { hull: false });
      });
    });
  }

  // ---------------- elevators ----------------
  /* E = { top, wait, speed, cab: piece, inner: [w, d] (cab floor, prefab-local), floor: cab floor top, wall: cab wall
     height (1.1), doors: optional { cab: leaf piece, landing: leaf piece, width: doorway (1.3), slide: leaf travel (0.6),
     time: open / close seconds (0.7), cabZ: cab door line, landZ: [z0, z1] landing door line, half: shaft half width,
     sill: true (a walkable sill bridges the cab and an upper landing) } }.
     The cab (its own mesh) shuttles between y0 and y0 + top, waiting `wait` s at each stop. Everyone inside the cab
     (player, robots) rides with it. The open side (local +Z) is closed while the cab moves, and the shaft opening of
     every stop the cab is not standing at is closed, so nobody walks into an empty shaft. With doors, two leaves
     part on the cab and on the landing of the stop it stands at; they stay open while someone stands in the doorway. */
  function makeElevator(P, z, theme, world, E, x, y0, zz, yaw) {
    var name = IB.themePiece(theme, E.cab), mesh = new THREE.Mesh(IB.Assets.get(name), IB.Assets.material(name));
    mesh.position.set(x, y0, zz); mesh.rotation.y = yaw;
    var group = new THREE.Group(); group.add(mesh);
    var c = Math.round(Math.cos(yaw)), s = Math.round(Math.sin(yaw));
    function rot(lx, lz) { return [x + lx * c + lz * s, zz - lx * s + lz * c]; }
    function box(lx0, lz0, lx1, lz1, ya, yb2, kind) {
      var A = rot(lx0, lz0), B = rot(lx1, lz1);
      return world.add(Math.min(A[0], B[0]), ya, Math.min(A[1], B[1]), Math.max(A[0], B[0]), yb2, Math.max(A[1], B[1]), kind, z.idx);
    }
    var iw = E.inner[0] / 2, id = E.inner[1] / 2, ft = 0.2, wh = E.wall || 1.1, fy = E.floor || 0.06, D = E.doors || null;
    var dw = D ? (D.width || 1.3) / 2 : iw + 0.1, half = D ? (D.half || iw + 0.25) : iw + 0.1;
    var lz = D && D.landZ ? D.landZ : [id + 0.05, id + 0.2];
    var L = { mesh: mesh, group: group, x: x, z: zz, c: c, s: s, y0: y0, top: E.top, wait: E.wait || 3, speed: E.speed || 1.5, h: 0, dir: 1, t: E.wait || 3, state: 'wait', fy: fy, rot: rot,
      iw: iw, id: id, wh: wh, dw: dw, lz: lz, open: 1, hold: 0, doorT: D ? (D.time || 0.7) : 0, slide: D ? (D.slide || 0.6) : 0, moving: [], stop: [], leaves: [] };
    function leaf(piece, parent, lzc, ly) {   // a pair of door leaves (one piece, centred on its own origin)
      var nm = IB.themePiece(theme, piece);
      [-1, 1].forEach(function (sg) {
        var m = new THREE.Mesh(IB.Assets.get(nm), IB.Assets.material(nm));
        m.position.set(sg * dw / 2, ly, lzc); parent.add(m); L.leaves.push({ m: m, sg: sg });
      });
    }
    // cab boxes (local offsets from the cab floor top) move with the cab: floor, sides, back, front jambs and the door
    var fl = box(-iw, -id, iw, id, y0 + fy - ft, y0 + fy, 'step'); fl.walk = true; world.walkN++;
    L.moving.push({ b: fl, lo: -ft, hi: 0 });
    L.moving.push({ b: box(-iw - 0.08, -id, -iw, id, y0 + fy, y0 + fy + wh, 'wall'), lo: 0, hi: wh });
    L.moving.push({ b: box(iw, -id, iw + 0.08, id, y0 + fy, y0 + fy + wh, 'wall'), lo: 0, hi: wh });
    L.moving.push({ b: box(-iw, -id - 0.08, iw, -id, y0 + fy, y0 + fy + wh, 'wall'), lo: 0, hi: wh });
    if (dw < iw) [-1, 1].forEach(function (sg) { L.moving.push({ b: box(sg * dw, id, sg * iw, id + 0.08, y0 + fy, y0 + fy + wh, 'wall'), lo: 0, hi: wh }); });
    L.door = box(-Math.min(dw, iw), id, Math.min(dw, iw), id + 0.08, y0 + fy, y0 + fy + wh, 'wall');
    L.moving.push({ b: L.door, lo: 0, hi: wh });
    if (D && D.cab) leaf(D.cab, mesh, D.cabZ || id + 0.04, fy);
    // stops: the shaft opening (a door across the doorway, fixed jambs beside it), shut unless the cab stands there open
    [0, E.top].forEach(function (hh) {
      var st = { h: hh, b: box(-dw, lz[0], dw, lz[1], y0 + hh, y0 + hh + Math.max(wh, 2.4), 'wall'), leaves: [] };
      if (D) {
        [-1, 1].forEach(function (sg) { box(sg * dw, lz[0], sg * half, lz[1], y0 + hh, y0 + hh + 2.4, 'wall'); });
        if (hh > 0 && D.sill !== false) { var sl = box(-half, id + 0.09, half, lz[1], y0 + hh - 0.25, y0 + hh, 'step'); sl.walk = true; world.walkN++; }
        if (D.landing) {
          var lg = new THREE.Group(); lg.position.set(x, y0 + hh, zz); lg.rotation.y = yaw; group.add(lg);
          var n0 = L.leaves.length; leaf(D.landing, lg, (lz[0] + lz[1]) / 2, 0); st.leaves = L.leaves.splice(n0, 2);
        }
      }
      L.stop.push(st);
    });
    doorState(L);
    return L;
  }
  // door boxes and leaves from the cab's state: the cab door and the landing it stands at follow L.open
  function doorState(L) {
    var atStop = L.state === 'wait';
    L.door.on = !(atStop && L.open > 0.85);
    L.stop.forEach(function (st) {
      var here = atStop && Math.abs(st.h - L.h) < 0.01, o = here ? L.open : 0;
      st.b.on = !(here && L.open > 0.85);
      st.leaves.forEach(function (lv) { lv.m.position.x = lv.sg * (L.dw / 2 + o * L.slide); });
    });
    L.leaves.forEach(function (lv) { lv.m.position.x = lv.sg * (L.dw / 2 + (atStop ? L.open : 0) * L.slide); });
  }
  /* advance every elevator; riders: [{x, z, y (feet), set(dy)}] */
  Z.updateElevators = function (level, dt, riders) {
    (level.elevators || []).forEach(function (L) {
      var dh = 0, T = L.doorT;
      if (L.state === 'wait') {
        L.t -= dt;
        if (L.t > T) L.open = T ? Math.min(1, L.open + dt / T) : 1;
        else {
          // someone in the doorway (between the cab and the landing): hold the doors (up to 8 s), like a real lift
          var busy = false, floorY = L.y0 + L.fy + L.h;
          if (T && L.hold < 8) riders.forEach(function (R) {
            var wx = R.x - L.x, wz = R.z - L.z, lx = wx * L.c - wz * L.s, lz = wx * L.s + wz * L.c;
            if (Math.abs(lx) < L.dw + 0.4 && lz > L.id - 0.5 && lz < L.lz[1] + 0.5 && R.y > floorY - 0.4 && R.y < floorY + 1.5) busy = true;
          });
          if (busy && L.open > 0) { L.hold += dt; L.t = T; L.open = Math.min(1, L.open + dt / T); }
          else L.open = T ? Math.max(0, L.open - dt / T) : 0;
          if (L.t <= 0 && L.open <= 0) { L.state = 'move'; L.hold = 0; }
        }
      } else {
        var nh = Math.max(0, Math.min(L.top, L.h + L.dir * L.speed * dt));
        dh = nh - L.h; L.h = nh;
        if ((L.dir > 0 && nh >= L.top) || (L.dir < 0 && nh <= 0)) {
          L.state = 'wait'; L.t = L.wait + T; L.dir = -L.dir; L.open = T ? 0 : 1;
          if (IB.Audio) IB.Audio.play('pickup', { pos: { x: L.x, z: L.z } });
        }
      }
      if (dh) {
        // everyone inside the cab rides: standing, jumping or crouching (feet between the floor and the cab roof)
        var fY = L.y0 + L.fy + L.h - dh;
        riders.forEach(function (R) {
          var wx = R.x - L.x, wz = R.z - L.z, lx = wx * L.c - wz * L.s, lz = wx * L.s + wz * L.c;
          if (Math.abs(lx) < L.iw + 0.05 && Math.abs(lz) < L.id + 0.1 && R.y > fY - 0.3 && R.y < fY + L.wh) R.set(dh);
        });
        L.moving.forEach(function (m) { m.b.y0 = L.y0 + L.fy + L.h + m.lo; m.b.y1 = L.y0 + L.fy + L.h + m.hi; });
        L.mesh.position.y = L.y0 + L.h;
      }
      doorState(L);
    });
  };

  // a single-cell symbol: one piece per cell
  function buildCells(P, z, grid, theme, world, ch, d, yb) {
    var pts = find(grid, ch);
    if (d.links) {   // rails: one half-module from the cell centre toward each linked neighbour (straight, L, T, end)
      pts.forEach(function (p) {
        var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5, y0 = baseY(world, yb, x, zz), n = 0, lk = d.links, tn = d.turn || 0;
        // turn (optional): a kit that models its runs along local X (Blender X) instead of Z gives -pi/2 here
        var L = function (dc, dr) { return lk.indexOf(grid.at(p.c + dc, p.r + dr)) >= 0; };
        var ns = L(0, 1) && L(0, -1) && !L(1, 0) && !L(-1, 0), ew = L(1, 0) && L(-1, 0) && !L(0, 1) && !L(0, -1);
        if (d.full && (ns || ew)) {   // straight run: one full module, no post
          var fy = (ns ? 0 : Math.PI / 2) + tn;
          P.add(d.full, x, y0, zz, fy);
          if (d.collide !== false) addColsY(world, colsOf(IB.themePiece(theme, d.full)) || boxCols(0.2, 1, d.h || 1), x, y0, zz, fy, d.kind || 'cover', z.idx);
          return;
        }
        [[0, 1, 0], [1, 0, Math.PI / 2], [0, -1, Math.PI], [-1, 0, -Math.PI / 2]].forEach(function (k) {
          if (lk.indexOf(grid.at(p.c + k[0], p.r + k[1])) < 0) return;
          n++; P.add(d.pieces[0], x, y0, zz, k[2] + tn);
          if (d.collide !== false) addColsY(world, colsOf(IB.themePiece(theme, d.pieces[0])) || boxCols(0.2, 0.5, d.h || 1), x, y0, zz, k[2] + tn, d.kind || 'cover', z.idx);
        });
        if (d.post) P.add(d.post, x, y0, zz, 0);
      });
      return;
    }
    pts.forEach(function (p, i) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5, yaw = 0;
      if (d.rotate === 'run') {
        var vert = !(cellIs(grid, p.c - 1, p.r, ch) || cellIs(grid, p.c + 1, p.r, ch)) && (cellIs(grid, p.c, p.r - 1, ch) || cellIs(grid, p.c, p.r + 1, ch));
        yaw = vert ? Math.PI / 2 : 0;
      } else if (d.rotate === 'random90') yaw = Math.floor(hash(p.c, p.r * 9) * 4) * Math.PI / 2;
      else if (d.rotate === 'edge') yaw = edgeYaw(grid, p.c, p.r, d.edge || '.');
      else if (typeof d.rotate === 'number') yaw = d.rotate;
      var name = d.sequence ? d.pieces[i % d.pieces.length] : d.alternate ? d.pieces[(p.c + p.r) % d.pieces.length] : pick(d.pieces, hash(p.c * 3 + 1, p.r * 5 + 2));
      var y0 = baseY(world, yb || 0, x, zz, d.sink ? 0.45 : 0, d.sink ? 0.45 : 0), py = (d.y || 0) + y0;
      P.add(name, x, py, zz, yaw, null, paintFor(d, z.idx, yb, hash(p.c * 11 + 3, p.r * 13 + 7)));
      if (d.collide !== false) addColsY(world, d.cols || colsOf(IB.themePiece(theme, name)) || boxCols(1, 1, d.h || 1), x, py, zz, yaw, d.kind || 'cover', z.idx);
      addWith(P, world, theme, d, name, x, py, zz, yaw, z.idx);
      if (d.mount && z.mounts) z.mounts.push({ x: x, y: y0, z: zz, yaw: yaw, kind: d.mount, piece: name, fill: d.fill === undefined ? 1 : d.fill });
      if (d.stack && hash(p.c * 5, p.r * 3) < d.stack.chance) {
        P.add(d.stack.piece, x, (d.h || 1) + y0, zz, Math.floor(hash(p.c * 7, p.r) * 4) * Math.PI / 2);
        if (d.collide !== false) world.add(x - 0.5, (d.h || 1) + y0, zz - 0.5, x + 0.5, (d.h || 1) + y0 + (d.stack.h || 1), zz + 0.5, d.kind || 'cover', z.idx);
      }
    });
    // moving line: one lane per straight run of cells (a 1-wide column runs north-south, anything else per row)
    if (d.conveyor) rects(grid, ch).forEach(function (R) {
      if (R.w === 1 && R.h > 1) addLine(P, z, theme, world, ch, d, z.ox + R.c + 0.5, z.oz + R.r + R.h / 2, Math.PI / 2, R.h / 2, null);
      else for (var y = 0; y < R.h; y++) addLine(P, z, theme, world, ch, d, z.ox + R.c + R.w / 2, z.oz + R.r + y + 0.5, 0, R.w / 2, null);
    });
  }
  // a one-cell piece (rotate: 'edge') turns its front (+Z) toward a neighbouring `edge` cell (open floor by default),
  // preferring a side whose back is not open too (a locker against a wall faces the room)
  function edgeYaw(grid, c, r, edge) {
    function open(cc, rr) { return rr >= 0 && cc >= 0 && rr < grid.h && cc < grid.w && grid.rows[rr][cc] === edge; }
    var D = [[0, 1, 0], [0, -1, Math.PI], [1, 0, Math.PI / 2], [-1, 0, -Math.PI / 2]], pick = null;
    for (var i = 0; i < 4; i++) {
      var d = D[i]; if (!open(c + d[0], r + d[1])) continue;
      if (!open(c - d[0], r - d[1])) return d[2];
      if (pick === null) pick = d[2];
    }
    return pick === null ? 0 : pick;
  }
  // a wall-mounted prefab (orient: 'wall') turns its front (+Z) away from the nearest wall cell along its block's sides;
  // with no wall beside it keeps the given yaw
  function wallYaw(grid, R, y) {
    function wallAt(r, c) { return r < 0 || c < 0 || r >= grid.h || c >= grid.w || grid.rows[r][c] === '#'; }
    var n = 0, s = 0, w = 0, e = 0, i;
    for (i = 0; i < R.w; i++) { if (wallAt(R.r - 1, R.c + i)) n++; if (wallAt(R.r + R.h, R.c + i)) s++; }
    for (i = 0; i < R.h; i++) { if (wallAt(R.r + i, R.c - 1)) w++; if (wallAt(R.r + i, R.c + R.w)) e++; }
    var best = Math.max(n, s, w, e); if (!best) return y;
    return best === n ? 0 : best === s ? Math.PI : best === w ? Math.PI / 2 : -Math.PI / 2;
  }
  // orient: 'open': the front (+Z) turns to the side of the block with the smallest share of wall cells (a room whose
  // front is a shop window line with a doorway, walled on its other three sides)
  function openYaw(grid, R, y) {
    function wallAt(r, c) { return r < 0 || c < 0 || r >= grid.h || c >= grid.w || grid.rows[r][c] === '#'; }
    var n = 0, s = 0, w = 0, e = 0, i;
    for (i = 0; i < R.w; i++) { if (wallAt(R.r - 1, R.c + i)) n++; if (wallAt(R.r + R.h, R.c + i)) s++; }
    for (i = 0; i < R.h; i++) { if (wallAt(R.r + i, R.c - 1)) w++; if (wallAt(R.r + i, R.c + R.w)) e++; }
    var f = [[n / R.w, Math.PI], [s / R.w, 0], [w / R.h, -Math.PI / 2], [e / R.h, Math.PI / 2]].sort(function (a, b) { return a[0] - b[0]; });
    return f[0][0] < f[1][0] ? f[0][1] : y;
  }
  // orient: 'span': the prefab's local X runs along the wall line it stands in (a door: the block's sides holding wall
  // cells or wall-kind symbols are its ends, the open sides its faces); the given yaw's half turn is kept
  function spanYaw(grid, theme, R, y) {
    var S = theme.symbols || {};
    function wallAt(c, r) { var ch = grid.at(c, r); return ch === '#' || !!(S[ch] && S[ch].kind === 'wall'); }
    var ns = 0, ew = 0, i;
    for (i = 0; i < R.w; i++) { if (wallAt(R.c + i, R.r - 1)) ns++; if (wallAt(R.c + i, R.r + R.h)) ns++; }
    for (i = 0; i < R.h; i++) { if (wallAt(R.c - 1, R.r + i)) ew++; if (wallAt(R.c + R.w, R.r + i)) ew++; }
    var flip = Math.abs(Math.cos(y)) > 0.5 ? (Math.cos(y) < 0 ? Math.PI : 0) : (Math.sin(y) < 0 ? Math.PI : 0);
    return (ew >= ns ? 0 : Math.PI / 2) + flip;
  }
  // a multi-cell prefab symbol: each connected block is tiled with prefabs of size [w, d] (rotated 90 if that fits)
  function buildPrefabs(P, z, grid, theme, world, ch, d, yb) {
    var sw = d.size[0], sd = d.size[1];
    yb = yb || 0;
    rects(grid, ch).forEach(function (R, ri) {
      var yaw = 0, tw = sw, td = sd;
      if (!(R.w % sw === 0 && R.h % sd === 0) && R.w % sd === 0 && R.h % sw === 0) { yaw = Math.PI / 2; tw = sd; td = sw; }
      var nx = Math.max(1, Math.floor(R.w / tw)), nz = Math.max(1, Math.floor(R.h / td));
      if (R.w % tw || R.h % td) { tw = R.w / nx; td = R.h / nz; }   // block not a multiple: centre one prefab per cell group
      // the run (prefabs in a row along the prefab's local X) and its downstream order: local +X is east, or north for
      // turned blocks; conveyor.dir -1 reverses it
      var nRun = yaw ? nz : nx, lanes = d.conveyor ? [] : null, back = d.conveyor && d.conveyor.dir === -1;
      for (var i = 0; i < nx; i++) for (var k = 0; k < nz; k++) {
        var x = z.ox + R.c + (i + 0.5) * tw, zz = z.oz + R.r + (k + 0.5) * td, h = hash(R.c + i * 7, R.r + k * 11);
        var y = yaw + (d.turn || 0) + (d.flip && hash(R.c * 3 + i, R.r * 5 + k) > 0.5 ? Math.PI : 0);
        if (typeof d.face === 'number') y = d.face;
        if (d.orient === 'wall') y = wallYaw(grid, R, y);
        else if (d.orient === 'open') y = openYaw(grid, R, y);
        else if (d.orient === 'span') y = spanYaw(grid, theme, R, y);
        var seq = yaw ? nz - 1 - k : i; if (back) seq = nRun - 1 - seq;
        // sequence 'run': the first and last pieces cap each run (feed / dispatch), the middle ones repeat in order
        var L = d.pieces.length, name = d.sequence === 'run' ? d.pieces[seq === 0 ? 0 : seq === nRun - 1 ? L - 1 : 1 + (seq - 1) % Math.max(1, L - 2)]
          : d.sequence ? d.pieces[(ri + i + k) % L] : pick(d.pieces, h);
        var y0 = baseY(world, yb, x, zz, tw / 2 * 0.8, td / 2 * 0.8), py = (d.y || 0) + y0;
        P.add(name, x, py, zz, y, null, paintFor(d, z.idx, yb, hash(R.c * 7 + i * 13 + 5, R.r * 3 + k * 17 + 1)));
        var nb0 = world.boxes.length;
        if (d.collide !== false) addColsY(world, d.cols || colsOf(IB.themePiece(theme, name)) || boxCols(sw, sd, d.h || 1), x, py, zz, y, d.kind || 'cover', z.idx);
        // fence: m (opt-in): the piece's collision runs on up to m above its base as a movement-only bound -- a low fence
        // round a sunken or closed-off area (a test track) the player could jump into from a crate but not out of
        if (d.fence) for (var fb = nb0, nb1 = world.boxes.length; fb < nb1; fb++) { var FB = world.boxes[fb]; if (FB.y1 < py + d.fence) world.bound(FB.x0, FB.y1, FB.z0, FB.x1, py + d.fence, FB.z1, z.idx); }
        addWith(P, world, theme, d, name, x, py, zz, y, z.idx);
        if (d.elevator) z.elevators.push(makeElevator(P, z, theme, world, d.elevator, x, y0, zz, y));
        var m0 = z.mounts.length;
        if (d.mounts) d.mounts.forEach(function (m) {   // pickup mounts inside the prefab (guns on a wall rack), prefab-local
          var c = Math.round(Math.cos(y)), s2 = Math.round(Math.sin(y));
          z.mounts.push({ x: x + m[0] * c + m[2] * s2, y: y0 + m[1], z: zz - m[0] * s2 + m[2] * c, yaw: y + (m[3] || 0), kind: m[4] || 'gun', piece: name, fill: d.fill === undefined ? 1 : d.fill, opt: m[5] || null });
        });
        // breakable (game/doors.js): the leaf is its own mesh and collision, the prefab's mounts stay locked until it breaks
        if (d.breakable && IB.Doors) IB.Doors.build(z, theme, world, d, name, x, py, zz, y, z.mounts.slice(m0));
        if (lanes) {
          if (d.conveyor.path) addLine(P, z, theme, world, ch, d, x, zz, y, 0, [{ at: 0, name: name }]);   // a loop per prefab
          else { var li = yaw ? i : k; (lanes[li] || (lanes[li] = [])).push({ x: x, z: zz, name: name }); }
        }
      }
      // straight lines: one lane per row of prefabs, tiles in downstream order (stations are looked up per tile)
      if (lanes) lanes.forEach(function (T) {
        var cx = 0, cz = 0, len = yaw ? td : tw, yw = yaw + (d.turn || 0);
        T.forEach(function (t) { cx += t.x / T.length; cz += t.z / T.length; });
        addLine(P, z, theme, world, ch, d, cx, cz, yw, T.length * len / 2, T.map(function (t) {
          return { at: (t.x - cx) * Math.cos(yw) - (t.z - cz) * Math.sin(yw), name: t.name };   // tile centre, line-local x
        }));
      });
    });
  }

  // ---------------- moving lines (theme symbol option `conveyor`) ----------------
  /* A symbol with `conveyor: {...}` is a moving line: belt cleats / track slats slide along each run and parts or
     half-built robots ride it, popping in and out of sight inside end hoods or station booths so the loop never shows.
       speed: 0.6 (m/s), dir: 1 | -1 | 'alt' (downstream = the placed piece's local +X, -X, or flipping every other run)
       y: 0.86             height of the item base (belt top)
       spacing: 1.2        metres between items (count: n overrides it)
       items: ['Piece', ['Stage0', 'Stage1', ...]]   each item a piece or a stage chain (see stations); items of one
                           symbol must come from one kit family
       inset: 0.5          items pop in / out this far inside each end of the run
       ends: { start: 'Feed', end: 'Exit', at: 0.5 }  pieces placed at the run ends (centre `at` m in from each end),
                           turned so their local +X points downstream; their _COL boxes collide
       stations: { 'Piece': x }   prefab lines: a tile of that piece moves its items on to the next stage where they pass
                           its local x (inside a booth that hides the swap)
       cleat: 'Cleat', cleatEvery: 0.5, cleatY: 0.86   belt cleats / track slats sliding along the whole run
       path: [[x, z], ...] prefabs only: a closed loop in prefab-local metres (a test track) instead of a straight run;
                           the items face along it
       carry: { top: 1.0, width: 0.8 }   a player standing on the line's collision top is carried along
     Per zone each moving symbol is ONE InstancedMesh (all its item kinds merged into one geometry; each instance shows
     only its own kind), plus one more for every cleat, so a zone's lines cost a few draw calls; Z.updateLines (once a
     frame from game.js) moves the visible zones only. Collision stays static: the line is cover. */
  function addLine(P, z, theme, world, ch, d, cx, cz, yaw, half, tiles) {
    var C = d.conveyor, lines = z.lines || (z.lines = []);
    var nth = lines.filter(function (l) { return l.ch === ch; }).length;
    var dir = C.dir === 'alt' ? (nth % 2 ? -1 : 1) : (C.dir || 1);
    var l = { ch: ch, C: C, cx: cx, cz: cz, yaw: yaw, c: Math.cos(yaw), s: Math.sin(yaw), dir: dir, half: half, len: 2 * half, y: C.y || 0, stations: [], nth: nth };
    if (C.path) {   // closed loop: cumulative arc length of the polyline
      var pts = C.path, cum = [0];
      for (var i = 1; i <= pts.length; i++) { var a = pts[i - 1], b = pts[i % pts.length]; cum.push(cum[i - 1] + Math.hypot(b[0] - a[0], b[1] - a[1])); }
      l.loop = { pts: pts, cum: cum }; l.t0 = 0; l.span = cum[pts.length]; l.dir = 1;
    } else {
      var inset = C.inset !== undefined ? C.inset : 0.5;
      l.t0 = inset; l.span = Math.max(0.1, l.len - 2 * inset);
      (tiles || []).forEach(function (t) {
        var sx = C.stations && C.stations[t.name];
        if (sx !== undefined && sx !== null) l.stations.push(half + dir * (t.at + sx));
      });
      l.stations.sort(function (a, b) { return a - b; });
      if (C.ends) [['start', 0], ['end', 1]].forEach(function (E) {
        var n = C.ends[E[0]]; if (!n) return;
        var at = C.ends.at !== undefined ? C.ends.at : 0.5, t = E[1] ? l.len - at : at, lx = dir * (t - half);
        var ex = cx + lx * l.c, ez = cz - lx * l.s, ey = yaw + (dir < 0 ? Math.PI : 0);
        P.add(n, ex, 0, ez, ey);
        var ec = colsOf(IB.themePiece(theme, n)); if (ec) addCols(world, ec, ex, ez, ey, 'cover', z.idx);
      });
    }
    var n = C.n || Math.max(1, Math.round(l.span / (C.spacing || 1.2)));
    l.n = n; l.gap = l.span / n;
    l.chains = [];
    for (var k = 0; k < n; k++) {
      var it = C.items[(k + nth * 3) % C.items.length];
      l.chains.push((Array.isArray(it) ? it : [it]).map(function (nm) { return IB.themePiece(theme, nm); }));
    }
    if (C.cleat && !C.path) { l.cleat = IB.themePiece(theme, C.cleat); l.cn = Math.max(1, Math.round(l.len / (C.cleatEvery || 0.5))); }
    lines.push(l);
  }
  // all kinds merged into one geometry; aKind tags each kind's vertices (cached per level, shared by the zones)
  function kindAtlas(level, names) {
    var key = names.join('|'), A = level.atlas || (level.atlas = {});
    if (!A[key]) {
      var list = names.map(function (n, k) {
        var g = IB.Assets.get(n).clone(), a = new Float32Array(g.attributes.position.count); a.fill(k);
        g.setAttribute('aKind', new THREE.BufferAttribute(a, 1)); return g;
      });
      A[key] = list.length > 1 ? THREE.BufferGeometryUtils.mergeBufferGeometries(list, false) : list[0];
    }
    var src = A[key], g = new THREE.BufferGeometry();   // a zone's view of the atlas: shared buffers + its own iKind
    g.setIndex(src.index);
    Object.keys(src.attributes).forEach(function (a) { g.setAttribute(a, src.attributes[a]); });
    return g;
  }
  // the kit's toon material, plus: an instance draws only the vertices of its own kind (iKind)
  var lineMats = {};
  function lineMat(fam) {
    if (lineMats[fam]) return lineMats[fam];
    var m = IB.Render.toonMaterial({ map: IB.Assets.palette[fam], baked: IB.Assets.BAKED[fam] !== undefined ? IB.Assets.BAKED[fam] : 0.02 });
    var base = m.onBeforeCompile, key = m.customProgramCacheKey;
    m.onBeforeCompile = function (sh) {
      base(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aKind;\nattribute float iKind;\n')
        .replace('#include <fog_vertex>', '#include <fog_vertex>\nif ( abs( aKind - iKind ) > 0.5 ) gl_Position = vec4( 0.0, 0.0, -2.0, 1.0 );');
    };
    m.customProgramCacheKey = function () { return key() + 'line'; };
    return (lineMats[fam] = m);
  }
  function lineMesh(level, zone, names, count) {
    var g = kindAtlas(level, names), kind = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
    kind.setUsage(THREE.DynamicDrawUsage); g.setAttribute('iKind', kind);
    var mesh = new THREE.InstancedMesh(g, lineMat(IB.Assets.family[names[0]]), count);
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); mesh.frustumCulled = false;
    zone.group.add(mesh);
    return { mesh: mesh, kind: kind, names: names };
  }
  function buildLines(level, zone) {
    if (!zone.lines) return;
    var syms = {};
    zone.lines.forEach(function (l) { (syms[l.ch] || (syms[l.ch] = [])).push(l); });
    zone.lineMeshes = [];
    Object.keys(syms).forEach(function (ch) {
      var L = syms[ch], names = [], count = 0;
      L.forEach(function (l) { l.base = count; count += l.n; l.chains.forEach(function (c) { c.forEach(function (n) { if (names.indexOf(n) < 0) names.push(n); }); }); });
      var M = lineMesh(level, zone, names, count);
      L.forEach(function (l) { l.items = M; l.kinds = l.chains.map(function (c) { return c.map(function (n) { return names.indexOf(n); }); }); });
      zone.lineMeshes.push(M);
    });
    var cl = zone.lines.filter(function (l) { return l.cleat; }), cnames = [], cc = 0;
    cl.forEach(function (l) { l.cbase = cc; cc += l.cn; if (cnames.indexOf(l.cleat) < 0) cnames.push(l.cleat); });
    if (cl.length) {
      var CM = lineMesh(level, zone, cnames, cc);
      cl.forEach(function (l) { l.cleats = CM; for (var j = 0; j < l.cn; j++) CM.kind.array[l.cbase + j] = cnames.indexOf(l.cleat); });
      zone.lineMeshes.push(CM);
    }
    placeLines(zone, level.lineT || 0);
  }
  var _lp = { x: 0, z: 0, yaw: 0 }, _lm = new THREE.Matrix4(), _lq = new THREE.Quaternion(), _lv = new THREE.Vector3();
  function linePos(l, t, out) {
    var lx, lz = 0, yaw = l.yaw;
    if (l.loop) {
      var P = l.loop.pts, cum = l.loop.cum, i = 0;
      while (i < P.length - 1 && cum[i + 1] < t) i++;
      var a = P[i], b = P[(i + 1) % P.length], f = (t - cum[i]) / Math.max(1e-6, cum[i + 1] - cum[i]);
      lx = a[0] + (b[0] - a[0]) * f; lz = a[1] + (b[1] - a[1]) * f;
      yaw += Math.atan2(b[0] - a[0], b[1] - a[1]);   // models face +Z: turn them along the path
    } else lx = l.dir * (t - l.half);
    out.x = l.cx + lx * l.c + lz * l.s; out.z = l.cz - lx * l.s + lz * l.c; out.yaw = yaw;
    return out;
  }
  function setInst(M, i, x, y, z, yaw) {
    _lq.setFromAxisAngle(_up, yaw); _lv.set(x, y, z);
    M.mesh.setMatrixAt(i, _lm.compose(_lv, _lq, _s1));
  }
  function placeLines(zone, T) {
    zone.lines.forEach(function (l) {
      var run = T * (l.C.speed || 0.6);
      for (var i = 0; i < l.n; i++) {
        var t = l.t0 + ((i * l.gap + run) % l.span), k = l.kinds[i], st = 0;
        while (st < l.stations.length && l.stations[st] < t) st++;
        linePos(l, t, _lp);
        setInst(l.items, l.base + i, _lp.x, l.y, _lp.z, _lp.yaw);
        l.items.kind.array[l.base + i] = k[Math.min(st, k.length - 1)];
      }
      if (l.cleats) for (var j = 0; j < l.cn; j++) {
        linePos(l, (j * l.len / l.cn + run) % l.len, _lp);
        setInst(l.cleats, l.cbase + j, _lp.x, l.C.cleatY !== undefined ? l.C.cleatY : l.y, _lp.z, _lp.yaw);
      }
    });
    zone.lineMeshes.forEach(function (M) { M.mesh.instanceMatrix.needsUpdate = true; M.kind.needsUpdate = true; });
  }
  // once a frame (game.js): move the lines of the zones being drawn; carry a player standing on a line top
  var _carry = [];
  Z.updateLines = function (level, dt, player) {
    if (!level) return;
    level.lineT = (level.lineT || 0) + dt;
    level.zones.forEach(function (zone) {
      if (!zone.lineMeshes || !zone.group.visible) return;
      placeLines(zone, level.lineT);
      if (!player || !player.onGround || !dt) return;
      zone.lines.forEach(function (l) {
        var K = l.C.carry; if (!K || l.loop || Math.abs(player.y - K.top) > 0.05) return;
        var dx = player.x - l.cx, dz = player.z - l.cz, lx = dx * l.c - dz * l.s, lz = dx * l.s + dz * l.c;
        if (Math.abs(lx) > l.half || Math.abs(lz) > (K.width || 0.8) / 2) return;
        var v = l.dir * (l.C.speed || 0.6) * dt, nx = player.x + v * l.c, nz = player.z - v * l.s, r = IB.MOVE.radius;
        level.world.query(nx - r, nz - r, nx + r, nz + r, _carry);
        for (var i = 0; i < _carry.length; i++) {   // never carry the player into a wall, a hood or a crate
          var b = _carry[i];
          if (b.y1 > player.y + 0.05 && b.y0 < player.y + IB.MOVE.height && nx + r > b.x0 && nx - r < b.x1 && nz + r > b.z0 && nz - r < b.z1) return;
        }
        player.x = nx; player.z = nz;
      });
    });
  };
  // overlay: an upper-layer grid ("@layer <y>"); "@layer 0" overlays the floor plan (inlays, rugs) without its walls
  function buildSymbols(P, z, grid, theme, world, g, yb, overlay) {
    yb = yb || 0;
    if (!yb && !overlay) buildWalls(P, z, grid, theme, world);
    Object.keys(theme.symbols || {}).forEach(function (ch) {
      var d = theme.symbols[ch];
      if (d.deck) { if (find(grid, ch).length) buildDeck(g, z, grid, world, ch, d, yb); }   // only on grids that hold the deck symbol itself (with: '*' would claim every non-empty cell of any layer)
      else if (d.size) buildPrefabs(P, z, grid, theme, world, ch, d, yb);
      else buildCells(P, z, grid, theme, world, ch, d, yb);
    });
    // spawn cans (fps-common) are part of every theme
    find(grid, 'S').forEach(function (p) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5, y0 = baseY(world, yb, x, zz, 0.4, 0.4);
      P.add(theme.spawn || 'SpawnCan', x, y0, zz, hash(p.c, p.r) * 6.28);
      world.add(x - 0.4, y0, zz - 0.4, x + 0.4, y0 + 1.0, zz + 0.4, 'cover', z.idx);
      z.spawns.push({ x: x, y: y0, z: zz });
    });
    ['a', 'h'].forEach(function (k) {
      find(grid, k).forEach(function (s) { var x = z.ox + s.c + 0.5, zz = z.oz + s.r + 0.5; z.pickups.push({ kind: k === 'a' ? 'ammo' : 'health', x: x, y: baseY(world, yb, x, zz), z: zz }); });
    });
  }

  // floor: flat colour plus optional painted lines (lot lines, planks, carpet tiles, lane marks);
  // floor.trailLines (optional) replaces floor.lines on the trails and the exit waypath (e.g. boardwalk planks)
  function paintFloor(g, x0, z0, w, h, theme, isTrail) {
    var F = theme.floor || {};
    g.flat([[x0, z0], [x0 + w, z0], [x0 + w, z0 + h], [x0, z0 + h]], 0.004, col(isTrail && F.trail ? F.trail : F.color, '#E6DCC6'));
    ((isTrail && F.trailLines) || F.lines || []).forEach(function (L) {
      var y = L.y || 0.008, c = col(L.color), half = (L.width || 0.04) / 2, every = L.every || 1;
      if (L.dir === 'x') for (var zz = z0 + every; zz < z0 + h - 0.01; zz += every) g.flat([[x0, zz - half], [x0 + w, zz - half], [x0 + w, zz + half], [x0, zz + half]], y, c);
      else for (var xx = x0 + every; xx < x0 + w - 0.01; xx += every) g.flat([[xx - half, z0], [xx + half, z0], [xx + half, z0 + h], [xx - half, z0 + h]], y, c);
    });
    if (F.lot && !isTrail) {
      for (var r = 3; r < h - 3; r += 6) for (var c2 = 2; c2 < w - 2; c2 += 3) {
        if (hash(c2, r) < 0.35) continue;
        var lx = x0 + c2, lz = z0 + r;
        g.flat([[lx - 0.06, lz], [lx + 0.06, lz], [lx + 0.06, lz + 2.6], [lx - 0.06, lz + 2.6]], 0.012, 0xFFFDF7);
      }
    }
  }
  // indoor ceiling over a rectangle (faces down), with optional light fixtures every N metres
  // mode (a zone plan's `ceiling`): false = no ceiling over this zone (a glass roof from its own layer grid),
  // 'plain' = the ceiling without the theme's light fittings (the zone's roof layer places them)
  function addCeiling(g, P, x0, z0, w, h, theme, grid, mode) {
    var C = theme.env && theme.env.ceiling; if (!C || mode === false) return;
    var y = C.height, c = col(C.color, '#F2F2F2');
    g.flat([[x0, z0], [x0, z0 + h], [x0 + w, z0 + h], [x0 + w, z0]].reverse(), y, c);   // winding chosen by flat(); flipped below
    var pos = g.nor, n0 = pos.length - 12;
    for (var i = n0; i < pos.length; i += 3) pos[i + 1] = -1;
    // flip the last quad's triangles so it faces down
    var idx = g.idx; for (var t = idx.length - 6; t < idx.length; t += 3) { var tmp = idx[t + 1]; idx[t + 1] = idx[t + 2]; idx[t + 2] = tmp; }
    if (C.light && mode !== 'plain') {
      var ev = C.every || 4;
      // light: one piece, or a list mixed per bay (e.g. roof bays with and without an overhead crane)
      var clr = C.clear || '', rad = C.clearR || 2;   // keep fittings off walls and tall pieces (symbols within clearR cells)
      for (var lx = x0 + ev / 2; lx < x0 + w; lx += ev) for (var lz = z0 + ev / 2; lz < z0 + h; lz += ev) {
        var ok = true;
        if (grid && clr) for (var dr = -rad; dr <= rad && ok; dr++) for (var dc = -rad; dc <= rad && ok; dc++) if (clr.indexOf(grid.at(Math.floor(lx - x0) + dc, Math.floor(lz - z0) + dr)) >= 0) ok = false;
        if (ok) P.add(Array.isArray(C.light) ? pick(C.light, hash(Math.round(lx) * 7 + 3, Math.round(lz) * 11 + 5)) : C.light, lx, y, lz, 0);
      }
    }
  }

  // ---------------- gates ----------------
  /* How high the closed shutter has to reach: the underside of the frame's lintel, measured on the frame's own
     model (and the pieces dressing it). Seen along the gate's axis, straight up from the top of the shutter model at
     seven places across the opening: the first height where the frame closes the view; the highest of them counts,
     so nothing shows over the shutter anywhere (a shutter top inside a lower part of the lintel is hidden by it).
     A place that stays open for 0.9 m has no lintel (an open-air gate between posts) and is left out. Every kit's
     shutter is 3.05 m tall and most frames open a little higher (4 to 46 cm): without this you see through the
     gap above a closed gate. Cached per theme. */
  function gateOpening(theme, GT, stop) {
    if (theme._gateTop !== undefined) return theme._gateTop;
    var tris = [];
    [GT.frame || 'GateFrame'].concat(GT.dress || []).forEach(function (n) {
      var g = IB.Assets.geo[IB.themePiece(theme, n)]; if (!g || !g.index) return;
      var p = g.attributes.position.array, h = g.attributes.aHull ? g.attributes.aHull.array : null, ix = g.index.array;
      for (var t = 0; t < ix.length; t += 3) {
        var a = ix[t] * 3, b = ix[t + 1] * 3, c = ix[t + 2] * 3;
        if (h && (h[a] || h[a + 1] || h[a + 2] || h[b] || h[b + 1] || h[b + 2] || h[c] || h[c + 1] || h[c + 2])) continue;   // outline shell
        if (Math.max(p[a + 1], p[b + 1], p[c + 1]) < stop || Math.min(p[a + 1], p[b + 1], p[c + 1]) > stop + 1) continue;
        tris.push(p[a], p[a + 1], p[b], p[b + 1], p[c], p[c + 1]);
      }
    });
    function closed(x, y) {
      for (var i = 0; i < tris.length; i += 6) {
        var d1 = (tris[i + 2] - tris[i]) * (y - tris[i + 1]) - (tris[i + 3] - tris[i + 1]) * (x - tris[i]);
        var d2 = (tris[i + 4] - tris[i + 2]) * (y - tris[i + 3]) - (tris[i + 5] - tris[i + 3]) * (x - tris[i + 2]);
        var d3 = (tris[i] - tris[i + 4]) * (y - tris[i + 5]) - (tris[i + 1] - tris[i + 5]) * (x - tris[i + 4]);
        if ((d1 >= 0 && d2 >= 0 && d3 >= 0) || (d1 <= 0 && d2 <= 0 && d3 <= 0)) return true;
      }
      return false;
    }
    var top = stop;
    if (tris.length) [-1.3, -0.9, -0.45, 0, 0.45, 0.9, 1.3].forEach(function (x) {
      for (var y = stop + 0.005; y < stop + 0.9; y += 0.01) if (closed(x, y)) { top = Math.max(top, y); return; }
    });
    return (theme._gateTop = top);
  }
  // the frame is merged into the zone mesh; the shutter is its own mesh so it can roll up
  function makeGate(P, cx, cz, width, theme, zoneIdx, world, kind) {
    var GT = theme.gate || {};
    P.add(GT.frame || 'GateFrame', cx, 0, cz, 0);
    (GT.dress || []).forEach(function (n) { P.add(n, cx, 0, cz, 0); });   // extra pieces dressing the frame
    // a frame that stands proud of the wall (a built-in, a portal) brings its own collision boxes
    var fcols = colsOf(IB.themePiece(theme, GT.frame || 'GateFrame'));
    if (fcols) addCols(world, fcols, cx, cz, 0, 'wall', zoneIdx);
    var sname = IB.themePiece(theme, GT.shutter || 'GateShutter');
    var sgeo = IB.Assets.get(sname), shutter = new THREE.Mesh(sgeo, IB.Assets.material(sname));
    shutter.scale.x = width / 3;
    // closed, the shutter reaches the underside of the lintel (a touch into it, so no hairline of light is left)
    var stop = sgeo.boundingBox ? sgeo.boundingBox.max.y : (GT.shutterHeight || 3.05), reach = gateOpening(theme, GT, stop);
    var sy = reach > stop + 0.004 ? (reach + 0.02) / stop : 1;
    var grp = new THREE.Group(); grp.add(shutter);
    grp.position.set(cx, 0, cz);
    var box = world.add(cx - width / 2, 0, cz - 0.3, cx + width / 2, GT.height || 3.2, cz + 0.3, 'gate', zoneIdx);
    return { group: grp, shutter: shutter, box: box, open: 1, target: 1, x: cx, z: cz, w: width, kind: kind, speed: 1 / 1.2, h: (GT.shutterHeight || 3.05) * sy, sy: sy };
  }
  /* The zone's outer ring of cells is solid at every height (tools: tests/e2e/bounds.spec.js). Wall collision stops
     at the wall height and a gate's at the gate height, so without this a player on a deck, a tree platform or a
     crate (Spring Boots double jump) could hop over the perimeter wall, or walk off a mezzanine through the wall
     drawn above a gate into the sky-bridge / trail behind it -- and never get back in. Per ring cell the boundary
     starts at the top of what stands there ('#': the wall height, a gate: its shutter box, anything else: the floor)
     and runs up out of reach; movement-only, so shots and sight lines are unchanged. */
  function addZoneBounds(zone, grid, theme, world) {
    var wallH = (theme.wall && theme.wall.height) || 3, gateH = (theme.gate && theme.gate.height) || 3.2, w = grid.w, h = grid.h;
    function bottom(c, r) { var ch = grid.at(c, r); return ch === '#' ? wallH : (ch === 'G' || ch === 'E') ? gateH : 0; }
    function run(c0, r0, dc, dr, n) {   // merge equal bottoms along one side of the ring
      var s = 0;
      for (var k = 1; k <= n; k++) {
        if (k < n && bottom(c0 + dc * k, r0 + dr * k) === bottom(c0 + dc * s, r0 + dr * s)) continue;
        var ca = c0 + dc * s, ra = r0 + dr * s, cb = c0 + dc * (k - 1), rb = r0 + dr * (k - 1);
        world.bound(zone.ox + ca, bottom(ca, ra), zone.oz + ra, zone.ox + cb + 1, undefined, zone.oz + rb + 1, zone.idx);
        s = k;
      }
    }
    run(0, 0, 1, 0, w); run(0, h - 1, 1, 0, w);
    run(0, 1, 0, 1, h - 2); run(w - 1, 1, 0, 1, h - 2);
  }
  Z.setGate = function (gate, open, instant) {
    gate.target = open ? 1 : 0;
    gate.speed = open ? 1 / 1.2 : 1 / 0.6;
    if (instant) { gate.open = gate.target; gate.was = gate.open; }
    Z.applyGate(gate);
  };
  Z.applyGate = function (gate) {
    var o = gate.open;
    if (o <= 0 && gate.target === 0 && gate.was > 0 && IB.Boom) IB.Boom.gateSlam(gate);   // shutter hits the floor: dust, chips, CLANG!
    gate.was = o;
    gate.shutter.scale.y = Math.max(0.02, 1 - o) * (gate.sy || 1);
    gate.shutter.position.y = o * (gate.h || 3.05);
    gate.shutter.visible = o < 0.98;
    gate.box.on = o < 0.7;
  };

  // ---------------- trail ----------------
  var DULL = new THREE.Color(0xE9DFC8), TEAL = new THREE.Color(PAL.teal);
  // trail.variants (optional): modules mixed in per slot with trail.wall, so a long run never repeats one slice
  function trailPiece(T, k, side) {
    var W = T.wall || 'TrailWall';
    return T.variants && T.variants.length ? pick([W].concat(T.variants), hash(k * 7 + 3, side * 13 + 101)) : W;
  }
  function buildTrail(level, from, to, theme, world, idx) {
    var g = new IB.Geo(), P = new Parts(theme), T = theme.trail || {};
    // trail.byTrail (optional): per trail (index = the zone it leaves) options over the theme's, e.g. its own variants
    if (T.byTrail && T.byTrail[idx]) T = Object.assign({}, T, T.byTrail[idx]);
    var x = from.x, z0 = from.z, z1 = to.z, w = 3, len = z0 - z1, wallH = T.height || 2.6;
    paintFloor(g, x - w / 2 - 0.5, z1, w + 1, len, theme, true);
    addCeiling(g, P, x - w / 2 - 1, z1, w + 2, len, theme);
    [-1, 1].forEach(function (sgn) {
      var wx = x + sgn * (w / 2 + 0.75);
      for (var k = 0; k < len; k++) P.add(trailPiece(T, Math.round(z1 + k) * 3 + idx * 31, sgn), wx, 0, z1 + k + 0.5, sgn > 0 ? Math.PI : 0);
      world.add(wx - 0.25, 0, z1, wx + 0.25, wallH, z0, 'wall', idx);
      world.bound(wx - 0.25, wallH, z1, wx + 0.25, undefined, z0, idx);   // and out of reach above it (addZoneBounds)
    });
    var grp = new THREE.Group();
    grp.add(new THREE.Mesh(g.build(), Z.mat));
    meshesFor(P, grp);
    // painted arrows: TrailArrow (fps-common) copies, recoloured per arrow when lit
    var n = Math.floor(len / 2), src = IB.Assets.get('TrailArrow'), list = [];
    for (var i = 0; i < n; i++) list.push(IB.Assets.placed('TrailArrow', M(x, 0.02, z0 - 1 - i * 2, 0)));
    var ag = THREE.BufferGeometryUtils.mergeBufferGeometries(list, false);
    var vertsPer = src.attributes.position.count;
    var cl = new Float32Array(ag.attributes.position.count * 3);
    for (var v = 0; v < cl.length; v += 3) { cl[v] = DULL.r; cl[v + 1] = DULL.g; cl[v + 2] = DULL.b; }
    ag.setAttribute('color', new THREE.BufferAttribute(cl, 3));
    var arrows = new THREE.Mesh(ag, new THREE.MeshBasicMaterial({ vertexColors: true }));
    grp.add(arrows);
    return { group: grp, arrows: arrows, count: n, vertsPer: vertsPer, lit: 0, litT: -1, x: x, z0: z0, z1: z1 };
  }
  Z.lightTrail = function (trail, n) {
    var colA = trail.arrows.geometry.attributes.color;
    for (var i = 0; i < trail.count; i++) {
      var c = i < n ? TEAL : DULL;
      for (var v = 0; v < trail.vertsPer; v++) colA.setXYZ(i * trail.vertsPer + v, c.r, c.g, c.b);
    }
    colA.needsUpdate = true; trail.lit = n;
  };

  // ---------------- nav grid / flow field ----------------
  function buildNav(zone, world) {
    var nx = Math.ceil(zone.w / NAV), nz = Math.ceil(zone.h / NAV);
    if (zone.terrain) return buildNavLayered(zone, world, nx, nz);   // bumpy ground: every cell has its own height
    for (var w = 0; w < world.boxes.length; w++) if (world.boxes[w].walk && world.boxes[w].zone === zone.idx) return buildNavLayered(zone, world, nx, nz);
    var blocked = new Uint8Array(nx * nz), tmp = [];
    for (var j = 0; j < nz; j++) for (var i = 0; i < nx; i++) {
      var x = zone.ox + (i + 0.5) * NAV, z = zone.oz + (j + 0.5) * NAV, inf = 0.3;
      world.query(x - inf, z - inf, x + inf, z + inf, tmp);
      for (var k = 0; k < tmp.length; k++) {
        var b = tmp[k]; if (b.y1 < 0.35 || b.y0 > 1.2 || b.kind === 'gate') continue;   // walk under raised boxes (desks, beds)
        if (x + inf > b.x0 && x - inf < b.x1 && z + inf > b.z0 && z - inf < b.z1) { blocked[j * nx + i] = 1; break; }
      }
      if (i === 0 || j === 0 || i === nx - 1 || j === nz - 1) blocked[j * nx + i] = 1;
    }
    zone.nav = { nx: nx, nz: nz, blocked: blocked, dist: new Int16Array(nx * nz), queue: new Int32Array(nx * nz), t: 0 };
  }
  /* Zones with walkable boxes: two nav layers. Node n = layer * nx * nz + cell; nav.h[n] = surface height.
     Per cell the walkable boxes holding the cell centre are stacked bottom-up: a box that starts on (or within 0.35 m
     of) a surface raises it (stair steps, a solid platform), a box floating higher starts a new surface (a deck with
     open ground under it). A surface is open when nothing but the gate blocks the robot's body there (0.3 m around
     the centre, from step height to 1.2 m above it; walkable boxes a step up or less never block). Layer 0 = the
     lowest open surface, layer 1 = the next one at least 1.2 m higher. Layer 0 matches the single-layer grid wherever
     no walkable box is near, so canister / pickup placement (ground cells, nav.h = 0) works as before. */
  function buildNavLayered(zone, world, nx, nz) {
    var NL = NAV_LAYERS, NC = nx * nz, blocked = new Uint8Array(NC * NL), hgt = new Float32Array(NC * NL), tmp = [], surf = [], wb = [];
    blocked.fill(1);
    for (var j = 1; j < nz - 1; j++) for (var i = 1; i < nx - 1; i++) {
      var c = j * nx + i, x = zone.ox + (i + 0.5) * NAV, z = zone.oz + (j + 0.5) * NAV, inf = 0.3, k, b, s;
      world.query(x - inf, z - inf, x + inf, z + inf, tmp);
      wb.length = 0;
      for (k = 0; k < tmp.length; k++) { b = tmp[k]; if (b.walk && x >= b.x0 && x <= b.x1 && z >= b.z0 && z <= b.z1) wb.push(b); }
      wb.sort(function (p, q) { return p.y0 - q.y0; });
      surf.length = 0; surf.push(world.groundAt(x, z));
      for (k = 0; k < wb.length; k++) {
        b = wb[k];
        var on = -1;
        for (s = 0; s < surf.length; s++) if (b.y0 <= surf[s] + 0.35 && b.y1 > surf[s]) on = s;
        if (on >= 0) surf[on] = Math.max(surf[on], b.y1); else if (b.y1 > surf[surf.length - 1]) surf.push(b.y1);
      }
      var L = 0, last = -9, vf = world.voids ? world.voidAt(x, z) : null;
      for (s = 0; s < surf.length && L < NL; s++) {
        var h = surf[s], open = h - last >= 1.2 && !(vf !== null && h <= vf + 0.01);   // open air: nothing to stand on
        for (k = 0; k < tmp.length && open; k++) {
          b = tmp[k];
          if (b.kind === 'gate' || b.y1 < h + 0.35 || b.y0 > h + 1.2 || (b.walk && b.y1 <= h + NAV_STEP)) continue;
          if (x + inf > b.x0 && x - inf < b.x1 && z + inf > b.z0 && z - inf < b.z1) open = false;
        }
        if (!open) continue;
        blocked[L * NC + c] = 0; hgt[L * NC + c] = h; last = h; L++;
      }
    }
    zone.nav = { nx: nx, nz: nz, layers: NL, blocked: blocked, h: hgt, dist: new Int16Array(NC * NL), queue: new Int32Array(NC * NL), t: 0 };
  }
  /* rebuild a zone's nav grid from the world's boxes as they are now (a box switched off: a broken door, game/doors.js);
     the arrays are refilled in place and the flow field is due at once */
  Z.renav = function (zone, world) {
    var old = zone.nav;
    buildNav(zone, world || zone.world);
    var N = zone.nav;
    if (old && old.blocked.length === N.blocked.length && !!old.h === !!N.h) {
      old.blocked.set(N.blocked); if (old.h) old.h.set(N.h);
      zone.nav = old;
    }
    zone.nav.t = 0;
  };
  // a walkable surface appeared at run time (a plank thrown across a gap, rooftops.js): the zone's grid again
  Z.rebuildNav = function (zone) { var t = zone.nav ? zone.nav.t : 0; buildNav(zone, zone.world); zone.nav.t = Math.min(t, 0); };
  Z.navCell = function (zone, x, z) {
    var i = Math.floor((x - zone.ox) / NAV), j = Math.floor((z - zone.oz) / NAV);
    if (i < 0 || j < 0 || i >= zone.nav.nx || j >= zone.nav.nz) return -1;
    return j * zone.nav.nx + i;
  };
  // layered nav: the open node of cell c whose surface is nearest to height y (within maxDy), or -1
  function nodeAt(N, c, y, maxDy) {
    var NC = N.nx * N.nz, best = -1, bd = maxDy;
    for (var L = 0; L < N.layers; L++) { var n = L * NC + c; if (N.blocked[n]) continue; var d = Math.abs(N.h[n] - y); if (d < bd) { bd = d; best = n; } }
    return best;
  }
  // the open node of cell c that a robot standing at height y can step to (|dh| <= NAV_STEP), or -1
  function stepNode(N, c, y) {
    var NC = N.nx * N.nz;
    for (var L = 0; L < N.layers; L++) { var n = L * NC + c; if (!N.blocked[n] && Math.abs(N.h[n] - y) <= NAV_STEP) return n; }
    return -1;
  }
  Z.navNode = function (zone, x, z, y) { var c = Z.navCell(zone, x, z); return c < 0 ? -1 : zone.nav.layers ? nodeAt(zone.nav, c, y || 0, 1.0) : (zone.nav.blocked[c] ? -1 : c); };
  function flowFieldLayered(zone, tx, tz, ty) {
    var N = zone.nav, d = N.dist, q = N.queue, nx = N.nx, nz = N.nz, NC = nx * nz;
    d.fill(32767);
    var c0 = Z.navCell(zone, tx, tz);
    if (c0 < 0) return;
    var s = nodeAt(N, c0, ty, 1.0);
    if (s < 0) {   // nearest open node on the target's level
      var bd = 1e9, si = c0 % nx, sj = (c0 / nx) | 0;
      for (var r = 1; r < 6 && s < 0; r++) for (var dj = -r; dj <= r; dj++) for (var di = -r; di <= r; di++) {
        var ii = si + di, jj = sj + dj; if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) continue;
        var n = nodeAt(N, jj * nx + ii, ty, 1.0); if (n >= 0 && di * di + dj * dj < bd) { bd = di * di + dj * dj; s = n; }
      }
      if (s < 0) return;
    }
    var h = 0, t = 0; q[t++] = s; d[s] = 0;
    while (h < t) {
      var cur = q[h++], cc = cur % NC, ci = cc % nx, cj = (cc / nx) | 0, cd = d[cur] + 1, ch = N.h[cur];
      for (var e = 0; e < 4; e++) {
        var ni = ci + (e === 0 ? -1 : e === 1 ? 1 : 0), nj = cj + (e === 2 ? -1 : e === 3 ? 1 : 0);
        if (ni < 0 || nj < 0 || ni >= nx || nj >= nz) continue;
        var m = stepNode(N, nj * nx + ni, ch);
        if (m >= 0 && d[m] > cd) { d[m] = cd; q[t++] = m; }
      }
    }
  }
  // ty: the target's height (layered zones only; single-layer grids ignore it)
  Z.flowField = function (zone, tx, tz, ty) {
    if (zone.nav.layers) return flowFieldLayered(zone, tx, tz, ty || 0);
    var N = zone.nav, d = N.dist, q = N.queue, nx = N.nx, nz = N.nz;
    d.fill(32767);
    var s = Z.navCell(zone, tx, tz);
    if (s < 0) return;
    if (N.blocked[s]) { // nearest open cell
      var best = -1, bd = 1e9, si = s % nx, sj = (s / nx) | 0;
      for (var r = 1; r < 6 && best < 0; r++) for (var dj = -r; dj <= r; dj++) for (var di = -r; di <= r; di++) {
        var ii = si + di, jj = sj + dj; if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) continue;
        var c = jj * nx + ii; if (!N.blocked[c] && di * di + dj * dj < bd) { bd = di * di + dj * dj; best = c; }
      }
      if (best < 0) return; s = best;
    }
    var h = 0, t = 0; q[t++] = s; d[s] = 0;
    while (h < t) {
      var cur = q[h++], ci = cur % nx, cj = (cur / nx) | 0, cd = d[cur] + 1;
      if (ci > 0 && !N.blocked[cur - 1] && d[cur - 1] > cd) { d[cur - 1] = cd; q[t++] = cur - 1; }
      if (ci < nx - 1 && !N.blocked[cur + 1] && d[cur + 1] > cd) { d[cur + 1] = cd; q[t++] = cur + 1; }
      if (cj > 0 && !N.blocked[cur - nx] && d[cur - nx] > cd) { d[cur - nx] = cd; q[t++] = cur - nx; }
      if (cj < nz - 1 && !N.blocked[cur + nx] && d[cur + nx] > cd) { d[cur + nx] = cd; q[t++] = cur + nx; }
    }
  };
  // layered flow direction for a robot standing at height y: the step-reachable neighbour node with the least
  // distance (a robot on a blocked node, e.g. brushing a rail, still finds its way out)
  function flowDirLayered(zone, x, z, y, out) {
    var N = zone.nav, c = Z.navCell(zone, x, z);
    if (c < 0) return false;
    var nx = N.nx, ci = c % nx, cj = (c / nx) | 0, me = stepNode(N, c, y), hy = me >= 0 ? N.h[me] : y;
    var best = me >= 0 ? N.dist[me] : 32767, bi = -1, bj = -1;
    for (var dj = -1; dj <= 1; dj++) for (var di = -1; di <= 1; di++) {
      if (!di && !dj) continue;
      var ii = ci + di, jj = cj + dj; if (ii < 0 || jj < 0 || ii >= nx || jj >= N.nz) continue;
      var k = stepNode(N, jj * nx + ii, hy); if (k < 0) continue;
      if (di && dj && (stepNode(N, cj * nx + ii, hy) < 0 || stepNode(N, jj * nx + ci, hy) < 0)) continue; // no corner cutting
      var v = N.dist[k] + ((di && dj) ? 0.4 : 0);
      if (v < best) { best = v; bi = ii; bj = jj; }
    }
    if (bi < 0) return false;
    out.x = zone.ox + (bi + 0.5) * NAV - x; out.z = zone.oz + (bj + 0.5) * NAV - z;
    var L = Math.hypot(out.x, out.z) || 1; out.x /= L; out.z /= L;
    return true;
  }
  // direction toward target along the flow field (writes into out {x,z}); returns false if none.
  // y: the robot's floor height (layered zones only; single-layer grids ignore it)
  Z.flowDir = function (zone, x, z, out, y) {
    var N = zone.nav;
    if (N.layers) return flowDirLayered(zone, x, z, y || 0, out);
    var c = Z.navCell(zone, x, z);
    if (c < 0) return false;
    var nx = N.nx, ci = c % nx, cj = (c / nx) | 0, best = N.dist[c], bi = -1, bj = -1;
    for (var dj = -1; dj <= 1; dj++) for (var di = -1; di <= 1; di++) {
      if (!di && !dj) continue;
      var ii = ci + di, jj = cj + dj; if (ii < 0 || jj < 0 || ii >= nx || jj >= N.nz) continue;
      var k = jj * nx + ii; if (N.blocked[k]) continue;
      if (di && dj && (N.blocked[cj * nx + ii] || N.blocked[jj * nx + ci])) continue; // no corner cutting
      var v = N.dist[k] + ((di && dj) ? 0.4 : 0);
      if (v < best) { best = v; bi = ii; bj = jj; }
    }
    if (bi < 0) return false;
    out.x = zone.ox + (bi + 0.5) * NAV - x; out.z = zone.oz + (bj + 0.5) * NAV - z;
    var L = Math.hypot(out.x, out.z) || 1; out.x /= L; out.z /= L;
    return true;
  };
  // open ground (in layered zones: layer 0 at ground level, not a stair step or a platform top)
  Z.isOpen = function (zone, x, z) { var c = Z.navCell(zone, x, z); return c >= 0 && !zone.nav.blocked[c] && (!zone.nav.h || zone.nav.h[c] - (zone.world ? zone.world.groundAt(x, z) : 0) < 0.05); };
  // floor height under (x, z) at or below y in the current level (0 without walkable surfaces); used by effects
  Z.floorY = function (x, z, y) { return Z.world ? Z.world.floorAt(x, z, y === undefined ? 1e9 : y) : 0; };
  Z.NAV_STEP = NAV_STEP;

  // ---------------- terrain (bumpy ground) ----------------
  /* theme.terrain = { height(c, r, zoneIdx) -> m (cell-corner coords), flat: 'symbols kept level', ramp: [a, b] cells,
     low: '#hex', high: '#hex', top: m (height that maps to 'high'), paint: fn (optional, see below) }. Walls, gates, the entry, spawns and every symbol
     listed in `flat` stand on level ground; the bumps ease in over `ramp` cells around them. */
  function buildTerrain(g, z, grid, theme, world) {
    var T = theme.terrain, W = grid.w + 1, H = grid.h + 1, dist = new Float32Array(W * H).fill(1e9), q = [], flat = '#GEPS' + (T.flat || '');
    function seed(c, r) { var v = r * W + c; if (dist[v] > 0) { dist[v] = 0; q.push(v); } }
    for (var r = 0; r < grid.h; r++) for (var c = 0; c < grid.w; c++) {
      if (r === 0 || c === 0 || r === grid.h - 1 || c === grid.w - 1 || flat.indexOf(grid.rows[r][c]) >= 0) { seed(c, r); seed(c + 1, r); seed(c, r + 1); seed(c + 1, r + 1); }
    }
    for (var h0 = 0; h0 < q.length; h0++) {
      var v = q[h0], vc = v % W, vr = (v / W) | 0;
      for (var dr = -1; dr <= 1; dr++) for (var dc = -1; dc <= 1; dc++) {
        var nc = vc + dc, nr = vr + dr; if (nc < 0 || nr < 0 || nc >= W || nr >= H) continue;
        var nv = nr * W + nc, nd = dist[v] + ((dc && dr) ? 1.41 : 1); if (nd < dist[nv]) { dist[nv] = nd; q.push(nv); }
      }
    }
    var ramp = T.ramp || [1, 5], hf = new Float32Array(W * H), top = 0;
    for (var i = 0; i < W * H; i++) {
      var k = Math.max(0, Math.min(1, (dist[i] - ramp[0]) / (ramp[1] - ramp[0]))); k = k * k * (3 - 2 * k);
      hf[i] = Math.max(0, T.height(i % W, (i / W) | 0, z.idx) * k); top = Math.max(top, hf[i]);
    }
    world.terrains.push({ ox: z.ox, oz: z.oz, w: grid.w, h: grid.h, hf: hf });
    world.terrainTop = Math.max(world.terrainTop || 0, top);
    z.terrain = hf;
    // mesh: one shared vertex per corner, smooth normals, colour from height plus a soft patch pattern
    var lo = col(T.low || (theme.floor && theme.floor.color), '#8CC46A'), hi = col(T.high, '#B8DE8A'), alt = col(T.patch || T.high, '#A6D27C'), cc2 = new THREE.Color();
    // T.paint (optional): fn(c, r, zoneIdx, grid) -> ['#hex', amount] tints that corner vertex (trails, mud, duff)
    var b0 = g.pos.length / 3, tp = T.top || 3, pcol = {}, pv;
    for (r = 0; r < H; r++) for (c = 0; c < W; c++) {
      var hh = hf[r * W + c];
      var hx = hf[r * W + Math.min(W - 1, c + 1)] - hf[r * W + Math.max(0, c - 1)], hz = hf[Math.min(H - 1, r + 1) * W + c] - hf[Math.max(0, r - 1) * W + c];
      var n = new THREE.Vector3(-hx / 2, 1, -hz / 2).normalize();
      cc2.copy(lo).lerp(hi, Math.min(1, hh / tp));
      var pt = Math.sin(c * 0.43 + r * 0.21) + Math.sin(c * 0.17 - r * 0.37 + 1.3);
      if (pt > 0.9) cc2.lerp(alt, 0.55);
      if (T.paint && (pv = T.paint(c, r, z.idx, grid))) cc2.lerp(pcol[pv[0]] || (pcol[pv[0]] = col(pv[0])), pv[1]);
      g._vert(z.ox + c, hh + 0.004, z.oz + r, n.x, n.y, n.z, cc2.clone());
    }
    for (r = 0; r < grid.h; r++) for (c = 0; c < grid.w; c++) {
      var a = b0 + r * W + c;
      g.idx.push(a, a + W, a + 1, a + 1, a + W, a + W + 1);
    }
  }

  /* theme.dataLayers (optional): [y, ...] -- "@layer <y>" grids that only hold codes the theme reads (its wall chooser:
     art per wall face, outdoor cells); they are never built as symbols, so their codes may use any character */
  function isDataLayer(theme, lg) { return !!(theme.dataLayers && theme.dataLayers.indexOf(lg.y) >= 0); }
  Z.isDataLayer = isDataLayer;

  // ---------------- level assembly ----------------
  /* plan: {themeId, zones:[{map:'name', waves:[[['crawler',4]], ...]}]} */
  Z.ZCHECK = /[?&]zcheck=1/.test(typeof location !== 'undefined' ? location.search : '');
  Z.buildLevel = function (plan, scene) {
    if (!Z.mat) Z.mat = IB.Render.toonMaterial({});
    var world = new World(), theme = themeOf(plan);
    Z.world = world;   // floor queries for effects (Z.floorY)
    var level = { world: world, zones: [], trails: [], plan: plan, root: new THREE.Group(), theme: theme, tris: 0, elevators: [], glows: [] };
    scene.add(level.root);
    var prevExit = null;
    plan.zones.forEach(function (zp, idx) {
      var grid = Z.parse(IB.ZONE_MAPS[zp.map]);
      var E = find(grid, 'E'), G = find(grid, 'G'), Pc = find(grid, 'P')[0];
      var ecx = E.length ? (E[0].c + E[E.length - 1].c + 1) / 2 : grid.w / 2;
      var ox, oz;
      if (!prevExit) { ox = -ecx; oz = -grid.h; }
      else { ox = prevExit.x - ecx; oz = prevExit.z - TRAIL_LEN - grid.h; }
      var zone = { idx: idx, ox: ox, oz: oz, w: grid.w, h: grid.h, grid: grid, plan: zp, group: new THREE.Group(), state: 'idle',
        world: world, spawns: [], pickups: [], elevators: [], mounts: [], doors: [] };
      zone.entry = { x: ox + Pc.c + 0.5, z: oz + Pc.r + 0.5 };
      var g = new IB.Geo(), P = new Parts(theme);
      var roofZone = IB.Rooftops && IB.Rooftops.has(grid, theme);   // open air between buildings (rooftops.js)
      if (theme.terrain) buildTerrain(g, zone, grid, theme, world);
      else if (!roofZone) paintFloor(g, ox, oz, grid.w, grid.h, zp.floor ? { floor: zp.floor } : theme, false);   // zone plan `floor` (optional): this zone's own floor paint and lines (a ship's deck, hold and engine room)
      buildSymbols(P, zone, grid, theme, world, g, 0);
      grid.layers.forEach(function (lg) { if (!isDataLayer(theme, lg)) buildSymbols(P, zone, lg, theme, world, g, lg.y, true); });
      if (roofZone) IB.Rooftops.build(level, zone, grid, theme, world, g, P);
      var roofCol = col(theme.wall && theme.wall.roof, '#D9D2E6'), roofY = ((theme.wall && theme.wall.height) || 3) + 0.04;
      P.roof.forEach(function (p) {
        var x = ox + p.c, zz = oz + p.r;
        g.flat([[x, zz], [x + 1, zz], [x + 1, zz + 1], [x, zz + 1]], roofY, roofCol);
      });
      addCeiling(g, P, ox, oz, grid.w, grid.h, theme, grid, zp.ceiling);
      if (E.length) zone.entryGate = makeGate(P, ox + ecx, oz + grid.h - 0.5, E.length, theme, idx, world, 'entry');
      var gcx = (G[0].c + G[G.length - 1].c + 1) / 2;
      zone.exitGate = makeGate(P, ox + gcx, oz + 0.5, G.length, theme, idx, world, 'exit');
      addZoneBounds(zone, grid, theme, world);
      zone.ground = new THREE.Mesh(g.build(), Z.mat);
      zone.group.add(zone.ground);
      zone.meshes = meshesFor(P, zone.group);
      if (P.glow) buildGlows(level, zone, P);   // theme.glow companions: LEDs, screens, holograms (unlit)
      buildLines(level, zone);   // moving lines (conveyor symbols): instanced items + belt cleats
      zone.tris = zone.meshes.reduce(function (t, m) { return t + m.geometry.index.count / 3; }, 0);
      level.tris += zone.tris;
      if (zone.entryGate) zone.group.add(zone.entryGate.group);
      zone.elevators.forEach(function (L) { zone.group.add(L.group || L.mesh); level.elevators.push(L); });
      Z.setGate(zone.exitGate, false, true);
      zone.group.add(zone.exitGate.group);
      level.root.add(zone.group);
      buildNav(zone, world);
      level.zones.push(zone);
      if (prevExit) {
        var tr = buildTrail(level, { x: prevExit.x, z: prevExit.z }, { x: prevExit.x, z: prevExit.z - TRAIL_LEN }, theme, world, idx - 1);
        level.trails.push(tr); level.root.add(tr.group);
      }
      prevExit = { x: ox + gcx, z: oz };
    });
    var last = Z.buildHatch(level, prevExit, theme, world);
    level.trails.push(last.trail); level.root.add(last.trail.group);
    level.hatch = last.hatch; level.root.add(last.hatch.group);
    Z.buildBackdrop(level, theme);
    if (Z.ZCHECK) {
      level.zfight = [];
      level.root.traverse(function (o) { if (o.isMesh && o.geometry.attributes.pid) level.zfight = level.zfight.concat(Z.zfight(o)); });
    }
    return level;
  };

  Z.buildHatch = function (level, exit, theme, world) {
    // the exit waypath: a long walled path; the screen dims as the player walks it, then the next level loads
    var WAY = 22, T = theme.trail || {}, wallH = T.height || 2.6;
    var tr = buildTrail(level, { x: exit.x, z: exit.z }, { x: exit.x, z: exit.z - WAY }, theme, world, level.zones.length - 1);
    var hz = exit.z - WAY - 1.5, g = new IB.Geo(), P = new Parts(theme);
    paintFloor(g, exit.x - 3, hz - 2.5, 6, exit.z - WAY - (hz - 2.5), theme, true);
    addCeiling(g, P, exit.x - 3.5, hz - 3.5, 7, exit.z - WAY - (hz - 3.5), theme);
    // back wall: the module's trail face (+X) turned toward the hatch room (south), lifted 5 mm so its trims never
    // share a plane with the side walls' where they cross in the corners
    for (var k = 0; k < 6; k++) P.add(T.end || trailPiece(T, k * 5 + 900, 2), exit.x - 2.5 + k, T.endLift !== undefined ? T.endLift : 0.005, hz - 2.95, T.endYaw !== undefined ? T.endYaw : -Math.PI / 2);
    for (k = 0; k < 5; k++) { P.add(trailPiece(T, k + 950, -1), exit.x - 3.0, 0, hz - 2 + k, 0); P.add(trailPiece(T, k + 950, 1), exit.x + 3.0, 0, hz - 2 + k, Math.PI); }
    world.add(exit.x - 3.25, 0, hz - 3.2, exit.x + 3.25, wallH, hz - 2.7, 'wall', -1);
    world.add(exit.x - 3.25, 0, hz - 2.75, exit.x - 2.75, wallH, hz + 2.75, 'wall', -1);
    world.add(exit.x + 2.75, 0, hz - 2.75, exit.x + 3.25, wallH, hz + 2.75, 'wall', -1);
    world.bound(exit.x - 3.25, wallH, hz - 3.2, exit.x + 3.25, undefined, hz + 2.75, -1);   // the hatch room has no way out over its walls
    P.add(theme.hatch || 'Hatch', exit.x, 0, hz, 0);
    var grp = new THREE.Group(); grp.add(new THREE.Mesh(g.build(), Z.mat));
    meshesFor(P, grp);
    return { trail: tr, hatch: { group: grp, x: exit.x, z: hz, r: 1.2, z0: exit.z } };
  };

  // A city far below a high-rise level (theme.below): the street grid sits `depth` metres down. Built in code as one
  // vertex-coloured mesh; the haze is baked per vertex by depth (aerial perspective), so looking down out of the windows
  // shows streets, rooftops and water tanks fading into the haze instead of a flat fog wall. Contents:
  //   * this tower's own curtain wall running down from the floor slab
  //   * tall shafts under the skyline rows (the printed skyline pieces stop at z = -25)
  //   * a block grid of mid and low buildings with banded window floors, parapets, water tanks and roof boxes
  //   * streets, avenues with lane marks, and a park block or two
  // Options beyond the office tower's defaults (all optional; the office uses none of them):
  //   facade / glass: our tower's skin colours; diagrid: [bay, height] draws that skin as a diagonal steel lattice
  //   towerTop: [m above the floor per zone (+ one for the exit's core when bridges)]: each zone's tower is drawn as a
  //     closed outside skin from the street to that height, faces turned outward (invisible from inside the zone, so a
  //     zone that is not being drawn still stands there seen from the others), with openings where bridges join
  //   bridges: true: the trails are sky-bridges (no set-back blocks between the towers; a core tower under the exit
  //     room); bridgeHole: [half width, bottom, top] of the openings
  //   skyline: { piece: [[x, front, w, d, colour, window], ...] } footprints per skyline piece (any ring, any copy);
  //     shaftTop: where the shafts under them stop (the pieces' base)
  //   hazeDist: [start, range, max] distance haze; hazeMax: the haze cap (1 = the horizon colour itself)
  //   detail: radius of the detailed blocks (simple ones beyond, to `extent`); horizon: flat painted blocks and the
  //     street out to here, so the city runs into the horizon haze; far: { count, radius, height, width } hazy towers
  //     on the horizon
  //   For a lower floor, where the street reads in detail (see cityLife below): winBand: [floor height, sill, head,
  //     mullion spacing, mullion share] our skin's glazing; topMax: city roofs scaled to stay this far below our floor;
  //     cars: { every, colors, radius } traffic in the lanes; trees: { every, color, dark, radius } sidewalk trees;
  //     roofs: { radius } plant rooms, roof gardens, solar rows and skylights on the buildings near the tower
  function buildCityBelow(level, theme, cz, rad, B) {
    var C = theme.below, D = C.depth || 170;
    var pos = [], colr = [], win = [], fac = [], edge = [], push = [], idx = [];
    // fac: (u along the face in m, floor height in m (0 = plain, < 0 = diagrid), light factor); win: window colour
    // edge: (u, v, width, height) of the quad in metres, so the shader can ink every outer edge at a constant
    // screen width (the comic outline the rest of the game has); width < 0 = no outline (streets, lane marks)
    // E (optional): [[u, v] x 4, width, height]: the quad's corners inside a larger face (a face split round an opening
    // is inked on the whole face's outline only)
    // push (optional): [[sx, sz] x 4] the outward corner direction of each vertex: the shader moves it out by the
    // world's ink outline width at that distance and inks the face 3.2 px wide instead of 1.7, so a shaft under a
    // kit building has exactly the silhouette and outline of the building standing on it
    var NOWIN = new THREE.Color(0, 0, 0);
    function quad(a, b, c2, d, c, w, fh, k, ua, ub, noInk, E, P) {
      var n = pos.length / 3, U = [ua || 0, ub || 0, ub || 0, ua || 0];
      var Lu = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]), Lv = Math.hypot(d[0] - a[0], d[1] - a[1], d[2] - a[2]);
      var EE = E ? E[0] : [[0, 0], [Lu, 0], [Lu, Lv], [0, Lv]], eu = E ? E[1] : Lu, ev = E ? E[2] : Lv;
      [a, b, c2, d].forEach(function (p, i) {
        pos.push(p[0], p[1], p[2]); colr.push(c.r, c.g, c.b); var ww = w || NOWIN; win.push(ww.r, ww.g, ww.b); fac.push(U[i], fh || 0, k);
        edge.push(EE[i][0], EE[i][1], noInk ? -1 : eu, ev);
        push.push(P ? P[i][0] : 0, P ? P[i][1] : 0);
      });
      idx.push(n, n + 1, n + 2, n, n + 2, n + 3);
    }
    var LIGHT = [0.86, 0.72, 0.96, 0.64];       // +x, -x, +z, -z (low southern sun)
    var INK = col('#2A2735'), ROOF = col(C.roof || '#8C8A93');
    var FACES = function (x0, z0, x1, z1) { return [[[x1, z1], [x1, z0], 0], [[x0, z0], [x0, z1], 1], [[x0, z1], [x1, z1], 2], [[x1, z0], [x0, z0], 3]]; };
    function roofCap(x0, z0, x1, z1, y1, roof) {
      var rc = roof || ROOF, r = Math.min(0.6, (x1 - x0) * 0.08), y = y1 + 0.03;
      quad([x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0], rc, null, 0, 1);
      quad([x0, y, z1], [x1, y, z1], [x1, y, z1 - r], [x0, y, z1 - r], INK, null, 0, 1, 0, 0, true);
      quad([x0, y, z0 + r], [x1, y, z0 + r], [x1, y, z0], [x0, y, z0], INK, null, 0, 1, 0, 0, true);
      quad([x0, y, z1], [x0 + r, y, z1], [x0 + r, y, z0], [x0, y, z0], INK, null, 0, 1, 0, 0, true);
      quad([x1 - r, y, z1], [x1, y, z1], [x1, y, z0], [x1 - r, y, z0], INK, null, 0, 1, 0, 0, true);
    }
    // box walls (no bottom) with an optional window grid drawn by the shader; roof cap + dark parapet rim
    function tower(x0, z0, x1, z1, y0, y1, base, winC, fh, roof) {
      FACES(x0, z0, x1, z1).forEach(function (F) {
        var a = F[0], b = F[1], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
        quad([a[0], y0, a[1]], [b[0], y0, b[1]], [b[0], y1, b[1]], [a[0], y1, a[1]], base, winC, fh, LIGHT[F[2]], 0, L);
      });
      if (roof === false) return;
      roofCap(x0, z0, x1, z1, y1, roof);
    }
    /* the lower part of a skyline building (the kit piece stands on it): same footprint as the piece, its walls moved
       out by the outline width and inked like the piece's own outline (see `push`); the top edge carries no ink (the
       building goes on above it) and a cap in the wall colour closes the narrow step between the two */
    function shaft(x0, z0, x1, z1, y0, y1, base, winC, fh) {
      var sg = function (px, pz) { return [px === x0 ? -1 : 1, pz === z0 ? -1 : 1]; };
      FACES(x0, z0, x1, z1).forEach(function (F) {
        var a = F[0], b = F[1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), Hh = y1 - y0, pa = sg(a[0], a[1]), pb = sg(b[0], b[1]);
        quad([a[0], y0, a[1]], [b[0], y0, b[1]], [b[0], y1, b[1]], [a[0], y1, a[1]], base, winC, fh, LIGHT[F[2]], 0, L, false,
          [[[0, 0], [L, 0], [L, Hh], [0, Hh]], L, Hh + 1e4], [pa, pb, pb, pa]);
      });
      quad([x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0], base, null, 0, 0.8, 0, 0, true, null, [sg(x0, z1), sg(x1, z1), sg(x1, z0), sg(x0, z0)]);
    }
    // a tower's outside skin with openings: holes = [{ face: 2 (south) | 3 (north), x0, x1, y0, y1 }]; node = [x, z]
    // a point the facade pattern is aligned to (a diagrid node of the curtain wall modules); plugs (optional): the
    // openings' own quads are collected there (drawn while the zone itself is not, so a bridge never ends in a void)
    function skin(x0, z0, x1, z1, y0, y1, base, winC, fh, holes, node, plugs) {
      FACES(x0, z0, x1, z1).forEach(function (F) {
        var a = F[0], b = F[1], f = F[2], L = Math.hypot(b[0] - a[0], b[1] - a[1]), Hh = y1 - y0;
        var u0 = node ? -(f < 2 ? Math.abs(a[1] - node[1]) : Math.abs(a[0] - node[0])) : 0;
        var P = function (s, y) { return [a[0] + (b[0] - a[0]) * s / L, y, a[1] + (b[1] - a[1]) * s / L]; };
        var piece = function (s0, s1, ya, yb) {
          if (s1 - s0 < 0.01 || yb - ya < 0.01) return;
          quad(P(s0, ya), P(s1, ya), P(s1, yb), P(s0, yb), base, winC, fh, LIGHT[f], u0 + s0, u0 + s1, false,
            [[[s0, ya - y0], [s1, ya - y0], [s1, yb - y0], [s0, yb - y0]], L, Hh]);
        };
        var hs = (holes || []).filter(function (h) { return h.face === f; }).map(function (h) {
          var s0 = f === 2 ? h.x0 - a[0] : a[0] - h.x1, s1 = f === 2 ? h.x1 - a[0] : a[0] - h.x0;
          return [Math.max(0, s0), Math.min(L, s1), Math.max(y0, h.y0), Math.min(y1, h.y1)];
        }).sort(function (p, q) { return p[0] - q[0]; });
        var s = 0;
        hs.forEach(function (h, k) {   // openings in the same column (theme.below.levels: one per height) share it
          var col0 = k === 0 || hs[k - 1][0] !== h[0] || hs[k - 1][1] !== h[1], last = k === hs.length - 1 || hs[k + 1][0] !== h[0] || hs[k + 1][1] !== h[1];
          if (col0) { piece(s, h[0], y0, y1); var gaps = hs.filter(function (q) { return q[0] === h[0] && q[1] === h[1]; }).sort(function (p, q) { return p[2] - q[2]; }); var yy = y0; gaps.forEach(function (q) { piece(h[0], h[1], yy, q[2]); yy = Math.max(yy, q[3]); }); piece(h[0], h[1], yy, y1); }
          if (last) s = h[1];
          if (plugs) plugs.push([P(h[0], h[2]), P(h[1], h[2]), P(h[1], h[3]), P(h[0], h[3]), base, winC, fh, LIGHT[f], u0 + h[0], u0 + h[1]]);
        });
        piece(s, L, y0, y1);
      });
      roofCap(x0, z0, x1, z1, y1, col('#8F8A86'));
    }
    function tank(x, z, y, s) {                 // rooftop water tank: legs, barrel, cone roof (octagon)
      var seg = 8, r = 1.3 * s, h = 2.6 * s, yb = y + 1.6 * s, wood = col('#9A6B4A'), cone = col('#6E4B38');
      tower(x - 0.9 * s, z - 0.9 * s, x + 0.9 * s, z + 0.9 * s, y, yb, col('#3B3545'), null, 0, false);
      for (var i = 0; i < seg; i++) {
        var a0 = i / seg * 6.283, a1 = (i + 1) / seg * 6.283, k = 0.72 + 0.28 * Math.cos(a0 - 0.8);
        var p0 = [x + Math.cos(a0) * r, z + Math.sin(a0) * r], p1 = [x + Math.cos(a1) * r, z + Math.sin(a1) * r];
        quad([p1[0], yb, p1[1]], [p0[0], yb, p0[1]], [p0[0], yb + h, p0[1]], [p1[0], yb + h, p1[1]], wood, null, 0, k);
        var n = pos.length / 3; pos.push(p1[0], yb + h, p1[1], p0[0], yb + h, p0[1], x, yb + h + r * 0.8, z);
        for (var j = 0; j < 3; j++) { colr.push(cone.r, cone.g, cone.b); win.push(0, 0, 0); fac.push(0, 0, k); edge.push(0, 0, -1, 0); }
        idx.push(n, n + 1, n + 2);
      }
    }
    function ground(x0, z0, x1, z1, y, c, ink) { quad([x0, y, z1], [x1, y, z1], [x1, y, z0], [x0, y, z0], c, null, 0, 1, 0, 0, !ink); }
    // level footprint (our tower)
    var minX = 1e9, maxX = -1e9, minZ = 1e9, maxZ = -1e9;
    level.zones.forEach(function (z) { minX = Math.min(minX, z.ox); maxX = Math.max(maxX, z.ox + z.w); minZ = Math.min(minZ, z.oz); maxZ = Math.max(maxZ, z.oz + z.h); });
    var hz = level.hatch ? level.hatch.z : minZ;
    minZ = Math.min(minZ, hz - 6);
    minX -= 0.6; maxX += 0.6; minZ -= 4; maxZ += 4;
    var Y0 = -D, facade = col(C.facade || '#7E93AA'), glass = col(C.glass || '#5F7FA2'), setback = col(C.setback || '#6C7F95');
    // the tower: each zone is a wing with its own curtain wall down to the street; between wings (where the trail
    // corridors run) a lower set-back block with a roof 4 m down, so every floor plate stands on a building
    var wings = level.zones.map(function (z) { return [z.ox - 0.6, z.oz - 0.3, z.ox + z.w + 0.6, z.oz + z.h + 0.3]; });
    var TT = C.towerTop, FH = C.diagrid ? -1 : C.winBand ? 1000 + C.winBand[0] : 4, BH = C.bridgeHole || [2.6, -1.2, ((theme.wall && theme.wall.height) || 4) + 0.5];
    // levels (optional): each zone's floor height above the street; FL(i) = zone i's floor in the city mesh's own frame
    // (the floor of a zone at the full `depth` is 0); towerTop and the openings count from each zone's own floor
    var FL = function (i) { return C.levels ? C.levels[Math.min(i, C.levels.length - 1)] - D : 0; };
    function hole(face, x, top, b) { b = b || 0; return { face: face, x0: x - BH[0], x1: x + BH[0], y0: b + BH[1], y1: b + (top === undefined ? BH[2] : top) }; }
    var plugs = level.zones.map(function () { return []; });
    wings.forEach(function (w, i) {
      var RZ = level.zones[i].roofs;   // a rooftop zone (rooftops.js): every building under its roofs, down to the street
      if (RZ) { RZ.forEach(function (b) { tower(b[0], b[1], b[2], b[3], Y0, b[4], col(b[5]), col(b[6]), b[7], false); }); return; }
      if (!TT) { tower(w[0], w[1], w[2], w[3], Y0, -0.06, facade, glass, 4, false); return; }
      var z = level.zones[i], holes = [hole(3, z.exitGate.x, undefined, FL(i))];
      if (i > 0 && z.entryGate) holes.push(hole(2, z.entryGate.x, undefined, FL(i)));
      // levels: the stair up to this zone is seen while the outside still stands at the zone below
      if (C.levels && i > 0 && z.entryGate) holes.push(hole(2, z.entryGate.x, undefined, FL(i - 1)));
      skin(w[0], w[1], w[2], w[3], Y0, FL(i) + TT[i], facade, glass, FH, holes, [z.ox + 1, z.oz + 1], plugs[i]);
    });
    if (C.bridges && level.hatch) {   // the exit room stands on (and in) a slender core tower
      var hx = level.hatch.x, hz0 = hz - 3.55, hz1 = hz + 3.1;
      var FX = FL(level.zones.length - 1);
      skin(hx - 3.65, hz0, hx + 3.65, hz1, Y0, FX + (TT ? TT[level.zones.length] || 30 : -0.8), facade, glass, FH, [hole(2, hx, undefined, FX)], [hx, hz1]);
    }
    for (var wi = 0; wi < wings.length && !C.bridges; wi++) {
      var lo = wings[wi], next = wings[wi + 1];
      var gz0 = next ? next[3] : minZ, gz1 = lo[1];
      if (gz1 - gz0 < 0.2) continue;
      var gx0 = Math.max(lo[0], next ? next[0] : lo[0]) + 3, gx1 = Math.min(lo[2], next ? next[2] : lo[2]) - 3;
      // with levels the block between two wings closes round the trail (linkTop m over the lower floor); the one over
      // the exit trail and hatch room is crownHalf m either side of the hatch when given
      if (C.levels && !next && C.crownHalf && level.hatch) { gx0 = level.hatch.x - C.crownHalf; gx1 = level.hatch.x + C.crownHalf; }
      if (C.levels) {   // the trail runs through it: openings at both ends (just the south one under the crown)
        var tx = level.zones[wi].exitGate.x, lh = [hole(2, tx, undefined, FL(wi))];
        if (next) lh.push(hole(3, tx, undefined, FL(wi)));
        skin(gx0, gz0, gx1, gz1, Y0, FL(wi) + (C.linkTop || 10), setback, glass, 4, lh, null, null);
      } else tower(gx0, gz0, gx1, gz1, Y0, -4, setback, glass, 4, col(C.linkRoof || '#9AA3AE'));
    }
    var keep = [[minX - 7, minZ - 7, maxX + 7, maxZ + 7]];
    function used(x0, z0, x1, z1) { for (var i = 0; i < keep.length; i++) { var k = keep[i]; if (x0 < k[2] && x1 > k[0] && z0 < k[3] && z1 > k[1]) return true; } return false; }
    // skyline rows: shafts carry the printed skyline down to the street (its pieces stop at shaftTop). They start
    // just behind the skyline's front blocks and run under its towers, stopping under its base; the dark roofs only
    // show in the gaps between skyline blocks. One shaft under every skyline building (theme.below.skyline mirrors the
    // blocks in the kit: [x, front depth, width, depth, colour, window colour]); the gaps between them look down into
    // the streets. A plain list is ring 0's piece; an object lists the footprints of each skyline piece.
    var SKY = C.skyline || [], _c = new THREE.Vector3(), STOP = C.shaftTop !== undefined ? C.shaftTop : -24;
    ((B && B.ring) || []).forEach(function (ring, ri) {
      if (Array.isArray(SKY) && ri > 0) return;
      for (var i = 0; i < ring.count; i++) {
        var list = Array.isArray(SKY) ? SKY : SKY[ring.pieces ? ring.pieces[i % ring.pieces.length] : ring.piece] || [];
        if (!list.length) continue;
        var pl = ringPlace(ring, ri, i, cz, rad), pm = M(pl.x, 0, pl.z, pl.yaw);
        list.forEach(function (bk, j) {
          var lx0 = bk[0] - bk[2] / 2, lx1 = bk[0] + bk[2] / 2, ly0 = bk[1], ly1 = bk[1] + bk[3];   // the building's own footprint
          var ax0 = 1e9, ax1 = -1e9, az0 = 1e9, az1 = -1e9;
          [[lx0, ly0], [lx1, ly0], [lx0, ly1], [lx1, ly1]].forEach(function (q) {
            _c.set(q[0], 0, -q[1]).applyMatrix4(pm); ax0 = Math.min(ax0, _c.x); ax1 = Math.max(ax1, _c.x); az0 = Math.min(az0, _c.z); az1 = Math.max(az1, _c.z);
          });
          if (used(ax0 + 0.5, az0 + 0.5, ax1 - 0.5, az1 - 0.5)) return;   // corners where two rows cross: first one wins
          keep.push([ax0, az0, ax1, az1]);
          var pc = col(bk[4]), wc = col(bk[5] || '#64798E');
          shaft(ax0, az0, ax1, az1, Y0, STOP, pc, wc, 3.4 + (j % 3) * 0.3);
        });
      }
    });
    // street grid out to the haze; blocks of 1, 2 or 4 buildings (simple single blocks beyond `detail`, flat painted
    // ones out to `horizon`)
    var ext = C.extent || 250, BLK = 26, ST = 9, street = col(C.street || '#5B616D'), walk = col('#A9A69D'), lane = col('#E8D47C'), park = col('#7FAA66');
    var DET = C.detail || 1e9, HOR = C.horizon || 0, EXT = Math.max(ext, HOR);
    var life = cityLife(C, { quad: quad, tower: tower, ground: ground, col: col, hash: hash, Y0: Y0, cz: cz, BLK: BLK, ST: ST });
    ground(-EXT, cz - EXT, EXT, cz + EXT, Y0, street);
    var BPAL = (C.blocks || ['#CDB89A', '#B39C86', '#9DB0C2', '#C9C3B6', '#AC8F78', '#8E9FB2', '#D2A58C']).map(function (h) { return col(h); });
    var bc = 0;
    for (var gx = -EXT; gx < EXT; gx += BLK + ST) for (var gz = cz - EXT; gz < cz + EXT; gz += BLK + ST) {
      var bx0 = gx + ST / 2, bz0 = gz + ST / 2, bx1 = bx0 + BLK, bz1 = bz0 + BLK, hh = hash(Math.round(gx) + 999, Math.round(gz) + 999);
      var dc = Math.hypot((bx0 + bx1) / 2, (bz0 + bz1) / 2 - cz), inner = gx >= -ext && gx < ext && gz >= cz - ext && gz < cz + ext;
      if (!inner || dc > DET) {   // far blocks: one plain building (inside `extent`), a flat painted block beyond
        if (used(bx0, bz0, bx1, bz1) || (!inner && dc > HOR)) continue;
        var fc = BPAL[Math.floor(hh * 97) % BPAL.length];
        if (inner && hh >= 0.06) tower(bx0 + 1, bz0 + 1, bx1 - 1, bz1 - 1, Y0, Y0 + 14 + hh * hh * 40, fc, fc.clone().multiplyScalar(0.55), 3.6, ROOF.clone().lerp(fc, 0.3));
        else ground(bx0, bz0, bx1, bz1, Y0 + 0.3, hh < 0.06 ? park : fc);
        continue;
      }
      ground(gx + ST / 2 - 0.14, gz, gx + ST / 2 + 0.14, gz + BLK + ST, Y0 + 0.05, lane);     // avenue centre line
      ground(gx, gz + ST / 2 - 0.14, gx + BLK + ST, gz + ST / 2 + 0.14, Y0 + 0.06, lane);     // street centre line
      ground(bx0 - 0.8, bz0 - 0.8, bx1 + 0.8, bz1 + 0.8, Y0 + 0.15, walk, true);                    // sidewalk slab
      if (C.cars || C.trees) life.street(gx, gz, bx0, bz0, bx1, bz1, dc);
      if (hh < 0.06) { ground(bx0, bz0, bx1, bz1, Y0 + 0.3, park, true); continue; }
      var parts = hh < 0.38 ? 1 : hh < 0.74 ? 2 : 4, mx = (bx0 + bx1) / 2, mz = (bz0 + bz1) / 2;
      for (var q = 0; q < parts; q++) {
        var qx0 = bx0, qz0 = bz0, qx1 = bx1, qz1 = bz1;
        if (parts === 2) { if (q === 0) qz1 = mz - 0.8; else qz0 = mz + 0.8; }
        if (parts === 4) { if (q & 1) qx0 = mx + 0.8; else qx1 = mx - 0.8; if (q & 2) qz0 = mz + 0.8; else qz1 = mz - 0.8; }
        if (used(qx0, qz0, qx1, qz1)) continue;
        var r2 = hash(bc, 51), dist = Math.hypot((qx0 + qx1) / 2, (qz0 + qz1) / 2 - cz);
        // downtown towers near the centre, walk-ups toward the edges; every roof stays far below our floor
        var top = Y0 + 16 + r2 * r2 * Math.max(24, 125 - dist * 0.38), tc = BPAL[bc % BPAL.length];
        if (C.topMax !== undefined) top = Y0 + (top - Y0) * Math.min(1, (C.topMax - Y0) / 141);
        tower(qx0, qz0, qx1, qz1, Y0, top, tc, tc.clone().multiplyScalar(0.55), 3.4 + hash(bc, 55) * 0.8, ROOF.clone().lerp(tc, 0.3));
        if (r2 > 0.42) tank(qx0 + 3 + hash(bc, 52) * Math.max(0, qx1 - qx0 - 6), qz0 + 3 + hash(bc, 53) * Math.max(0, qz1 - qz0 - 6), top, 1 + hash(bc, 54) * 0.4);
        if (r2 < 0.75 && qx1 - qx0 > 8) tower(qx1 - 6, qz0 + 2, qx1 - 2, qz0 + 5, top, top + 1.6, col('#8A8794'), null, 0, col('#77747F'));   // roof bulkhead
        if (C.roofs && dist < (C.roofs.radius || 200)) life.roof(qx0, qz0, qx1, qz1, top, bc, r2);
        bc++;
      }
    }
    // a far horizon of tall towers in the haze
    if (C.far) for (var fi = 0; fi < C.far.count; fi++) {
      var FA = C.far, an2 = (fi + hash(fi, 71) * 0.7) / FA.count * Math.PI * 2, fr = FA.radius[0] + hash(fi, 72) * (FA.radius[1] - FA.radius[0]);
      var fxx = Math.cos(an2) * fr, fzz = cz + Math.sin(an2) * fr, fw = FA.width[0] + hash(fi, 73) * (FA.width[1] - FA.width[0]);
      var ftop = FA.height[0] + hash(fi, 74) * (FA.height[1] - FA.height[0]), ftc = BPAL[fi % BPAL.length];
      tower(fxx - fw / 2, fzz - fw / 2, fxx + fw / 2, fzz + fw / 2, Y0, ftop, ftc, ftc.clone().multiplyScalar(0.6), 4, ROOF.clone().lerp(ftc, 0.3));
    }
    function geometry() {
      var geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      geo.setAttribute('color', new THREE.Float32BufferAttribute(colr, 3));
      geo.setAttribute('aWin', new THREE.Float32BufferAttribute(win, 3));
      geo.setAttribute('aFac', new THREE.Float32BufferAttribute(fac, 3));
      geo.setAttribute('aEdge', new THREE.Float32BufferAttribute(edge, 4));
      geo.setAttribute('aPush', new THREE.Float32BufferAttribute(push, 2));
      geo.setIndex(pos.length / 3 > 65535 ? new THREE.Uint32BufferAttribute(idx, 1) : new THREE.Uint16BufferAttribute(idx, 1));
      geo.computeBoundingSphere();
      return geo;
    }
    var geo = geometry(), cityTris = idx.length / 3;
    // window grid (floor bands + mullions) or diagrid, and the depth + distance haze are drawn per pixel: one quad
    // per facade
    var HD = C.hazeDist || [120, 260, 0.3], DG = C.diagrid || [6, 9];
    var mat = new THREE.ShaderMaterial({
      uniforms: { uInk: { value: col('#221E2C') }, uHaze: { value: col(C.haze || '#CCDCE8') }, uDepth: { value: D }, uTop: { value: C.hazeTop || 0.18 }, uBot: { value: C.hazeBottom || 0.6 },
        uWB: { value: C.winBand ? new THREE.Vector4(C.winBand[1], C.winBand[2], C.winBand[3], C.winBand[4]) : new THREE.Vector4(0.38, 0.9, 2.6, 0.14) },
        uHz: { value: new THREE.Vector3(HD[0], HD[1], HD[2]) }, uMaxH: { value: C.hazeMax || 0.92 }, uDia: { value: new THREE.Vector2(DG[0], DG[1]) },
        uOutBase: IB.Render.worldOutline.uOutBase, uOutK: IB.Render.worldOutline.uOutK, uOutPx: { value: IB.Render.worldOutline.px || 3.2 } },
      extensions: { derivatives: true },
      vertexShader: 'attribute vec3 color; attribute vec3 aWin; attribute vec3 aFac; attribute vec4 aEdge; attribute vec2 aPush; uniform float uOutBase; uniform float uOutK; uniform float uOutPx;\n' +
        'varying vec3 vC; varying vec3 vW; varying vec3 vF; varying vec4 vE; varying float vY; varying float vDist; varying float vInk; varying float vWY;\n' +
        'void main(){ vC = color; vW = aWin; vF = aFac; vE = aEdge; vY = position.y; vec3 p = position; vInk = 1.7;\n' +
        '  vec4 mv = modelViewMatrix * vec4(p, 1.0);\n' +
        '  if (aPush.x != 0.0 || aPush.y != 0.0) { float w = max(uOutBase, uOutK * -mv.z); p.x += aPush.x * w; p.z += aPush.y * w; mv = modelViewMatrix * vec4(p, 1.0); vInk = uOutPx; }\n' +
        '  vWY = (modelMatrix * vec4(p, 1.0)).y; vDist = length(mv.xyz); gl_Position = projectionMatrix * mv; }',
      fragmentShader: 'uniform vec4 uWB; uniform vec3 uHaze; uniform float uDepth; uniform float uTop; uniform float uBot; uniform vec3 uInk; uniform vec3 uHz; uniform float uMaxH; uniform vec2 uDia;\n' +
        'varying vec3 vC; varying vec3 vW; varying vec3 vF; varying vec4 vE; varying float vY; varying float vDist; varying float vInk; varying float vWY;\n' +
        'void main(){ vec3 c = vC;\n' +
        '  if (vF.y > 999.0) { float fy = fract(vY / (vF.y - 1000.0)); float fu = fract(vF.x / uWB.z);\n' +   // theme.below.winBand
        '    if (fy > uWB.x && fy < uWB.y && fu > uWB.w) c = vW; }\n' +
        '  else if (vF.y > 0.0) { float fy = fract(vY / vF.y); float fu = fract(vF.x / 2.6);\n' +
        '    if (fy > 0.38 && fy < 0.9 && fu > 0.14) c = vW; }\n' +
        '  else if (vF.y < 0.0) {\n' +   // diagrid: steel diagonals (bay uDia.x wide, climbing uDia.y per half diamond) and floor beams over glass
        '    float sl = uDia.x / uDia.y, kk = inversesqrt(1.0 + sl * sl), s1 = vF.x - vY * sl, s2 = vF.x + vY * sl;\n' +
        '    float d = min(abs(s1 - uDia.x * floor(s1 / uDia.x + 0.5)), abs(s2 - uDia.x * floor(s2 / uDia.x + 0.5))) * kk;\n' +
        '    float fb = abs(vY - uDia.y * 0.5 * floor(vY / (uDia.y * 0.5) + 0.5));\n' +
        '    float aa = fwidth(d) + 1e-4, ab = fwidth(fb) + 1e-4;\n' +
        '    vec3 gl = mix(vW, vC * 0.8, (1.0 - smoothstep(0.22 - ab, 0.22 + ab, fb)) * 0.8);\n' +
        '    vec3 cc = mix(gl, vC, 1.0 - smoothstep(0.17 - aa, 0.17 + aa, d));\n' +
        '    c = mix(cc, mix(vW, vC, 0.2), clamp(aa * 5.0 - 0.25, 0.0, 1.0)); }\n' +
        '  c *= vF.z;\n' +
        '  if (vE.z > 0.0) { vec2 d = min(vE.xy, vE.zw - vE.xy); vec2 px = fwidth(vE.xy) * vInk;\n' +
        '    if (d.x < px.x || d.y < px.y) c = uInk; }\n' +
        '  float h = mix(uTop, uBot, clamp(-vWY / uDepth, 0.0, 1.0)) + clamp((vDist - uHz.x) / uHz.y, 0.0, uHz.z);\n' +
        '  gl_FragColor = vec4(mix(c, uHaze, clamp(h, 0.0, uMaxH)), 1.0); }'
    });
    var mesh = new THREE.Mesh(geo, mat);
    mesh.frustumCulled = false; mesh.name = 'CityBelow';
    level.root.add(mesh);
    level.cityTris = cityTris;
    // the plugs: one small mesh per zone tower closing its bridge openings, shown while that zone is not drawn
    // (Z.setVisible), so a bridge seen from the next tower ends at a facade, not in a see-through hole
    level.plugs = [];
    plugs.forEach(function (list, i) {
      if (!list.length) return;
      pos = []; colr = []; win = []; fac = []; edge = []; idx = [];
      list.forEach(function (q) { quad(q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8], q[9]); });
      var pm = new THREE.Mesh(geometry(), mat);
      pm.frustumCulled = false; pm.name = 'CityPlug' + i; pm.visible = false;
      level.root.add(pm); level.plugs.push({ zone: i, mesh: pm });
    });
  }
  /* Street life and rooftop detail for a city seen from a mid-rise floor (theme.below cars / trees / roofs), drawn with
     the city's own quad / tower / ground helpers (K). street(): per detailed block, cars in the two lanes each side of
     the avenue and the street centre lines, zebra crossings at the corner, trees along the block's north and south
     sidewalks; roof(): per building, one of plant units, a raised roof garden, solar rows or a skylight, kept clear of
     the bulkhead (north-east corner) the city already puts there. Everything is a few boxes, inked like the city. */
  function cityLife(C, K) {
    var Y0 = K.Y0, ST = K.ST, BLK = K.BLK, hash = K.hash, col = K.col, CR = C.cars || {}, TR = C.trees || {};
    var cars = (CR.colors || ['#EEEEEA', '#2C2F36', '#C8312C', '#3B6FB6', '#9AA2AC']).map(function (h) { return col(h); });
    var glass = col('#2B3442'), white = col('#F4F2EC'), leaf = col(TR.color || '#6FA352'), leafD = col(TR.dark || '#4C7F3E');
    var roofG = col('#7FAE5E'), soil = col('#8A7158'), solar = col('#2E4A78'), unit = col('#C9CCD1'), unitD = col('#9A9EA6'), sky = col('#BFE3F2');
    function car(x, z, along, seed) {   // along: 'z' (avenue) or 'x' (street); body + cabin
      var L = 4.2 + hash(seed, 3) * 0.8, W = 1.8, cc = cars[Math.floor(hash(seed, 4) * cars.length) % cars.length];
      var hx = along === 'z' ? W / 2 : L / 2, hz = along === 'z' ? L / 2 : W / 2;
      K.tower(x - hx, z - hz, x + hx, z + hz, Y0 + 0.25, Y0 + 1.0, cc, null, 0, cc);
      var cx = along === 'z' ? W / 2 - 0.12 : L * 0.27, czz = along === 'z' ? L * 0.27 : W / 2 - 0.12;
      K.tower(x - cx, z - czz, x + cx, z + czz, Y0 + 1.0, Y0 + 1.55, glass, null, 0, cc);
    }
    function lane(a0, a1, fixed, along, seed) {   // cars along one lane from a0 to a1 (away from the crossings)
      var ev = CR.every || 8;
      for (var a = a0 + 3; a < a1 - 3; a += ev) {
        var hh = hash(seed + Math.round(a * 3), 17);
        if (hh < 0.45) continue;
        var p = a + (hh - 0.45) * 2.5;
        if (along === 'z') car(fixed, p, 'z', seed + Math.round(a)); else car(p, fixed, 'x', seed + Math.round(a));
      }
    }
    return {
      street: function (gx, gz, bx0, bz0, bx1, bz1, dc) {
        var seed = Math.round(gx) * 31 + Math.round(gz) * 7;
        if (C.cars && dc < (CR.radius || 220)) {
          // the avenue runs north-south on x = gx, the street east-west on z = gz (the junction is round (gx, gz));
          // this block's stretch of each runs from ST / 2 to ST / 2 + BLK past it
          var s0 = ST / 2, s1 = ST / 2 + BLK;
          lane(gz + s0, gz + s1, gx - 1.7, 'z', seed); lane(gz + s0, gz + s1, gx + 1.7, 'z', seed + 5);
          lane(gx + s0, gx + s1, gz - 1.7, 'x', seed + 9); lane(gx + s0, gx + s1, gz + 1.7, 'x', seed + 13);
          for (var i = 0; i < 5; i++) {      // zebra crossings on the avenue and the street, next to the junction
            var o = -2.4 + i * 1.2;
            K.ground(gx + o - 0.3, gz + s0 + 0.4, gx + o + 0.3, gz + s0 + 2.4, Y0 + 0.08, white);
            K.ground(gx + s0 + 0.4, gz + o - 0.3, gx + s0 + 2.4, gz + o + 0.3, Y0 + 0.08, white);
          }
        }
        if (C.trees && dc < (TR.radius || 200)) {
          var ev = TR.every || 7;
          [bz0 - 0.4, bz1 + 0.4].forEach(function (tz, s) {
            for (var tx = bx0 + 2; tx < bx1 - 1; tx += ev) {
              var r = 1.1 + hash(seed + Math.round(tx), 21 + s) * 0.5, y = Y0 + 2.4;
              K.tower(tx - r, tz - r, tx + r, tz + r, y, y + 1.6 + r * 0.6, hash(seed + Math.round(tx), 23) < 0.5 ? leaf : leafD, null, 0, leaf);
            }
          });
        }
      },
      roof: function (x0, z0, x1, z1, top, bc, r2) {
        var w = x1 - x0, d = z1 - z0, k = hash(bc, 61), y = top;
        if (w < 7 || d < 7) return;
        var ax0 = x0 + 1.5, az0 = z0 + (d > 12 ? 6 : 1.5), ax1 = x0 + w * 0.62, az1 = z1 - 1.5;   // clear of the bulkhead
        if (k < 0.3) {                // a raised roof garden: planter bed, lawn, a few shrubs
          K.tower(ax0, az0, ax1, az1, y, y + 0.45, soil, null, 0, roofG);
          for (var i = 0; i < 3; i++) {
            var sx = ax0 + 1 + hash(bc, 62 + i) * Math.max(0.5, ax1 - ax0 - 2), sz = az0 + 1 + hash(bc, 66 + i) * Math.max(0.5, az1 - az0 - 2);
            K.tower(sx - 0.8, sz - 0.8, sx + 0.8, sz + 0.8, y + 0.45, y + 1.9, i % 2 ? leaf : leafD, null, 0, leaf);
          }
        } else if (k < 0.55) {        // solar rows on low frames
          for (var zz = az0; zz + 1.4 < az1; zz += 2.2) K.tower(ax0, zz, ax1, zz + 1.4, y + 0.2, y + 0.55, unitD, null, 0, solar);
        } else if (k < 0.8) {         // plant units: chillers and condensers in a row
          for (var xx = ax0; xx + 2 < ax1; xx += 2.8) K.tower(xx, az0, xx + 2, az0 + 1.6, y, y + 1.3, unit, null, 0, unitD);
          K.tower(ax0, az1 - 1.2, ax1, az1 - 0.6, y, y + 0.6, unitD, null, 0, unitD);   // a duct run
        } else {                      // a skylight with its upstand
          K.tower(ax0 + 1, az0 + 1, ax1 - 1, az1 - 1, y, y + 0.5, unit, null, 0, sky);
        }
      }
    };
  }
  // where copy i of backdrop ring ri stands (and faces): shared by the ring placement and the city's skyline shafts
  function ringPlace(ring, ri, i, cz, rad) {
    var a = (i + ri * 0.37) / ring.count * Math.PI * 2, rr = rad - 70 + ring.radius[0] + (ring.radius[1] - ring.radius[0]) * hash(i, 3 + ri);
    var x = Math.cos(a) * rr * (ring.squeezeX || 0.6), z = cz + Math.sin(a) * rr;
    return { x: x, z: z, a: a, rr: rr, yaw: ring.face ? Math.atan2(-x, -(z - cz)) : a };
  }

  // backdrop beyond the playable area (printed, fogged): rings of theme/common pieces; outlined puff clouds outdoors.
  // backdrop.build (optional): fn(level, api) paints its own ground (instead of the flat outside plane) and places
  // pieces itself; api = { geo (IB.Geo merged with the world toon material), add(piece, x, y, z, yaw, scale), hash,
  // tick(fn(dt, t)) (called every frame with the clouds) }
  Z.buildBackdrop = function (level, theme) {
    var g = new IB.Geo(), minZ = 0, maxZ = 0, F = theme.floor || {};
    level.zones.forEach(function (z) { minZ = Math.min(minZ, z.oz - 20); });
    var cz = (minZ + maxZ) / 2, rad = (maxZ - minZ) / 2 + 70;
    var B0 = theme.backdrop, n0 = level.root.children.length;
    level.ticks = [];
    if (B0 && B0.build) {
      var P0 = new Parts(theme);
      B0.build(level, {
        geo: g, hash: hash,
        add: function (n, x, y, z, yaw, s) { var m = M(x, y, z, yaw); if (s && s !== 1) m.multiply(new THREE.Matrix4().makeScale(s, s, s)); P0.add(n, 0, 0, 0, 0, m); },
        tick: function (fn) { level.ticks.push(fn); }
      });
      if (g.count()) level.root.add(new THREE.Mesh(g.build(), Z.mat));
      meshesFor(P0, level.root);
    } else if (theme.backdrop !== null && !theme.below) {
      g.flat([[-rad - 60, cz - rad - 60], [rad + 60, cz - rad - 60], [rad + 60, cz + rad + 60], [-rad - 60, cz + rad + 60]], -0.02, col(F.outside || F.color, '#E6DCC6').multiplyScalar(F.outside ? 1 : 0.94));
      level.root.add(new THREE.Mesh(g.build(), Z.mat));
    }
    var B = theme.backdrop, P = new Parts(theme);
    if (theme.below) buildCityBelow(level, theme, cz, rad, B);
    if (B && B.ring) B.ring.forEach(function (ring, ri) {
      for (var i = 0; i < ring.count; i++) {
        var pl = ringPlace(ring, ri, i, cz, rad);
        var sc = ring.scale[0] + (ring.scale[1] - ring.scale[0]) * hash(i, 7 + ri), sq = ring.squash ? ring.squash[0] + (ring.squash[1] - ring.squash[0]) * hash(i, 8) : 1;
        var m = M(pl.x, ring.y || 0, pl.z, pl.yaw);
        m.multiply(new THREE.Matrix4().makeScale(sc, sc * sq, sc));
        P.add(ring.pieces ? ring.pieces[i % ring.pieces.length] : ring.piece, 0, 0, 0, 0, m);   // pieces: one per copy, in turn
      }
    });
    meshesFor(P, level.root);
    level.clouds = []; level.cloudMeshes = [];
    if (!(theme.env && theme.env.clouds)) { if (theme.below && theme.below.levels) belowGroup(level, n0); return; }
    if (!Z.cloudMat) { Z.cloudMat = IB.Render.toonMaterial({ map: IB.Assets.palette.common, baked: 0.06 }); Z.cloudMat.emissive = new THREE.Color(0x7A7468); Z.cloudMat.fog = false; }
    /* env.clouds: true (puffs 44-66 m up drifting east) or { y: [lo, hi], count (per cloud shape), scale: [lo, hi],
       lanes: [near, far] (|x| band on both sides of the level, kept clear of the buildings), span (m along z, centred
       on the level), speed, axis: 'z' (drift north along the lanes, wrapping inside the span) } */
    var CO = typeof theme.env.clouds === 'object' ? theme.env.clouds : null;
    ['Cloud_A', 'Cloud_B', 'Cloud_C'].forEach(function (name, si) {
      var N = CO ? CO.count || 4 : 4, im = new THREE.InstancedMesh(IB.Assets.get(name), Z.cloudMat, N);
      im.frustumCulled = false;
      for (var k = 0; k < N; k++) {
        var j = si * N + k;
        if (CO) {
          var sp = CO.span || 260, ln = CO.lanes || [60, 90], yr = CO.y || [44, 66], sr = CO.scale || [1.6, 3];
          level.clouds.push({ mesh: im, i: k, x: (j % 2 ? 1 : -1) * (ln[0] + hash(j, 11) * (ln[1] - ln[0])), y: yr[0] + hash(j, 12) * (yr[1] - yr[0]),
            z: cz + (hash(j, 13) - 0.5) * sp, s: sr[0] + hash(j, 14) * (sr[1] - sr[0]), yaw: hash(j, 15) * 6.28,
            axis: CO.axis, v: CO.speed || 0.6, lo: cz - sp / 2, hi: cz + sp / 2 });
        } else level.clouds.push({ mesh: im, i: k, x: (hash(j, 11) - 0.5) * 260, y: 44 + hash(j, 12) * 22, z: cz + (hash(j, 13) - 0.5) * 260, s: 1.6 + hash(j, 14) * 1.4, yaw: hash(j, 15) * 6.28 });
      }
      level.cloudMeshes.push(im); level.root.add(im);
    });
    Z.updateClouds(level, 0);
    if (theme.below && theme.below.levels) belowGroup(level, n0);
  };
  /* theme.below.levels: [m above the street per zone] -- the zones stand at different heights of one building (a
     lobby on the street, a floor in the middle, the top). Everything outside (the city, its haze, the backdrop and
     the clouds) is one group, lifted so the street lies levels[i] under the floor of the zone the player is nearest
     (Z.updateBelow, every frame; in a trail the switch happens halfway along it). Only the current and the next zone
     are drawn then (the one behind stands at another height; its gate is shut). */
  function belowGroup(level, n0) {
    var grp = level.belowGroup;
    if (!grp) { grp = level.belowGroup = new THREE.Group(); grp.name = 'Below'; }
    level.root.children.slice(n0).forEach(function (o) { if (o !== grp) grp.add(o); });
    if (grp.parent !== level.root) level.root.add(grp);
    level.belowAt = -1;
    Z.updateBelow(level, null);
  }
  Z.updateBelow = function (level, p) {
    var C = level && level.belowGroup && level.theme.below;
    if (!C) return;
    var best = 0, bd = 1e9;
    if (p) level.zones.forEach(function (z, i) { var d = Math.max(0, z.oz - p.z, p.z - (z.oz + z.h)); if (d < bd - 1e-6) { bd = d; best = i; } });
    if (best === level.belowAt) return;
    level.belowAt = best;
    level.belowGroup.position.y = (C.depth || 170) - C.levels[Math.min(best, C.levels.length - 1)];
    level.belowGroup.updateMatrixWorld(true);
  };
  var _cm = new THREE.Matrix4(), _cq = new THREE.Quaternion(), _cp = new THREE.Vector3(), _cs = new THREE.Vector3();
  Z.updateClouds = function (level, dt) {
    if (level && level.ticks) { level.tickT = (level.tickT || 0) + dt; for (var ti = 0; ti < level.ticks.length; ti++) level.ticks[ti](dt, level.tickT); }
    if (!level || !level.clouds || !level.clouds.length) return;
    for (var k = 0; k < level.clouds.length; k++) {
      var cl = level.clouds[k];
      if (cl.axis === 'z') { cl.z -= dt * cl.v; if (cl.z < cl.lo) cl.z = cl.hi; } else { cl.x += dt * 0.6; if (cl.x > 140) cl.x = -140; }
      _cq.setFromAxisAngle(_up, cl.yaw); _cp.set(cl.x, cl.y, cl.z); _cs.set(cl.s, cl.s, cl.s);
      cl.mesh.setMatrixAt(cl.i, _cm.compose(_cp, _cq, _cs));
    }
    level.cloudMeshes.forEach(function (m) { m.instanceMatrix.needsUpdate = true; });
  };

  // brief 4.2: only the current zone, the next zone and the trail between them are drawn
  /* Zones drawn while the player is in zone `cur`: the one behind, this one and the next, so looking back through a
     window or over a wall never shows a hole where the last zone stood. A theme whose walls are mostly glass
     (theme.showAllZones, the office tower) keeps every zone drawn. */
  Z.setVisible = function (level, cur) {
    var all = !!(level.theme && level.theme.showAllZones), back = level.belowGroup ? 0 : 1;   // theme.below.levels: see belowGroup
    level.zones.forEach(function (z, i) { z.group.visible = all || (i >= cur - back && i <= cur + 1); });
    level.trails.forEach(function (t, i) { t.group.visible = (i === cur || (back > 0 && i === cur - 1)); });
    if (level.hatch) level.hatch.group.visible = cur >= level.zones.length - 1;
    (level.plugs || []).forEach(function (p) { p.mesh.visible = !level.zones[p.zone].group.visible; });   // theme.below bridge openings
  };

  Z.zoneAt = function (level, x, z) {
    for (var i = 0; i < level.zones.length; i++) {
      var zn = level.zones[i];
      if (x > zn.ox && x < zn.ox + zn.w && z > zn.oz && z < zn.oz + zn.h) return i;
    }
    return -1;
  };
  Z.TRAIL_LEN = TRAIL_LEN;
})(window.IB = window.IB || {});
