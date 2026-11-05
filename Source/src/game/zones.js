/* INKBOLT zones: ASCII zone layouts -> merged toon geometry, AABB collision (2 m grid),
   gates, trail arrows, exit hatch, nav grid + BFS flow fields. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var Z = IB.Zones = {};
  var CELL = 2;          // collision grid cell (m)
  var NAV = 0.5;         // nav cell (m)
  var TRAIL_LEN = 12;

  // ---------------- parsing ----------------
  Z.parse = function (text) {
    var rows = text.replace(/\r/g, '').split('\n').filter(function (r) { return r.length > 0; });
    var w = 0; rows.forEach(function (r) { w = Math.max(w, r.length); });
    rows = rows.map(function (r) { while (r.length < w) r += '.'; return r; });
    return { w: w, h: rows.length, rows: rows, at: function (c, r) { return (r < 0 || r >= rows.length || c < 0 || c >= w) ? '#' : rows[r][c]; } };
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
  function World() { this.boxes = []; this.grid = new Map(); }
  World.prototype.add = function (x0, y0, z0, x1, y1, z1, kind, zone) {
    var b = { id: this.boxes.length, x0: Math.min(x0, x1), y0: y0, z0: Math.min(z0, z1), x1: Math.max(x0, x1), y1: y1, z1: Math.max(z0, z1), on: true, kind: kind || 'wall', zone: zone === undefined ? -1 : zone };
    this.boxes.push(b);
    var cx0 = Math.floor(b.x0 / CELL), cx1 = Math.floor(b.x1 / CELL), cz0 = Math.floor(b.z0 / CELL), cz1 = Math.floor(b.z1 / CELL);
    for (var i = cx0; i <= cx1; i++) for (var k = cz0; k <= cz1; k++) {
      var key = i * 73856 + k; var a = this.grid.get(key); if (!a) { a = []; this.grid.set(key, a); } a.push(b.id);
    }
    return b;
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
    if (dy < -1e-6) { var tg = -oy / dy; if (tg > 0 && tg < best) { best = tg; bb = null; bnx = 0; bny = 1; bnz = 0; } }
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
        var b = this.boxes[id]; if (!b.on || (skipKind && b.kind === skipKind)) continue;
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
  World.prototype.los = function (ax, ay, az, bx, by, bz) {
    var dx = bx - ax, dy = by - ay, dz = bz - az, d = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (d < 1e-4) return true;
    return !this.ray(ax, ay, az, dx / d, dy / d, dz / d, d - 0.05);
  };
  Z.World = World;

  // ---------------- themes (Blender kit families; src/data/themes/*.js) ----------------
  function themeOf(plan) { return IB.THEME_DEFS[plan.themeId] || IB.THEME_DEFS.toytown; }
  Z.themeOf = themeOf;
  function col(hex, fallback) { return new THREE.Color(hex || fallback || '#CCCCCC'); }
  var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _up = new THREE.Vector3(0, 1, 0), _p = new THREE.Vector3(), _s1 = new THREE.Vector3(1, 1, 1);
  function M(x, y, z, yaw) { _q.setFromAxisAngle(_up, yaw || 0); _p.set(x, y, z); return _m.clone().compose(_p, _q, _s1); }

  // pieces collected per Blender family, merged into one mesh per family per zone
  function Parts(theme) { this.lists = {}; this.roof = []; this.theme = theme; }
  var PID = 0;
  Z.pidNames = {};
  Parts.prototype.add = function (name, x, y, z, yaw, m) {
    name = IB.themePiece(this.theme, name);
    var fam = IB.Assets.family[name];
    if (!fam || !IB.Assets.geo[name]) throw new Error('INKBOLT kit piece missing: ' + name);
    var g = IB.Assets.placed(name, m || M(x, y, z, yaw));
    if (Z.ZCHECK) {   // tag each placed piece so the cross-piece z-fighting check can tell pieces apart
      var n = g.attributes.position.count, a = new Float32Array(n); a.fill(++PID);
      g.setAttribute('pid', new THREE.BufferAttribute(a, 1)); Z.pidNames[PID] = name;
    }
    (this.lists[fam] || (this.lists[fam] = [])).push(g);
  };
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
      if (/_COL\d*$/.test(c.name)) out.push({ x: c.position.x, y: c.position.y, z: c.position.z, hx: Math.abs(c.scale.x), hy: Math.abs(c.scale.y), hz: Math.abs(c.scale.z) });
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
      world.add(x + cx - hx, b.y - b.hy, z + cz - hz, x + cx + hx, b.y + b.hy, z + cz + hz, kind, zi);
    });
  }
  function boxCols(w, d, h) { return [{ x: 0, y: h / 2, z: 0, hx: w / 2, hy: h / 2, hz: d / 2 }]; }

  // '#': exposed cells get a wall module; building interiors get a flat roof
  function buildWalls(P, z, grid, theme, world) {
    var W = theme.wall || {}, H = W.height || 3;
    rects(grid, '#').forEach(function (R) {
      world.add(z.ox + R.c, 0, z.oz + R.r, z.ox + R.c + R.w, H, z.oz + R.r + R.h, 'wall', z.idx);
    });
    var WALLISH = '#GE';
    function solid(c, r) { return cellIs(grid, c, r, WALLISH); }
    find(grid, '#').forEach(function (p) {
      var exposed = !solid(p.c - 1, p.r) || !solid(p.c + 1, p.r) || !solid(p.c, p.r - 1) || !solid(p.c, p.r + 1) ||
        !solid(p.c - 1, p.r - 1) || !solid(p.c + 1, p.r - 1) || !solid(p.c - 1, p.r + 1) || !solid(p.c + 1, p.r + 1);
      if (!exposed) { P.roof.push(p); return; }
      var horiz = cellIs(grid, p.c - 1, p.r, WALLISH) || cellIs(grid, p.c + 1, p.r, WALLISH);
      var vert = cellIs(grid, p.c, p.r - 1, WALLISH) || cellIs(grid, p.c, p.r + 1, WALLISH);
      var name = W.choose ? W.choose(p.c, p.r, horiz, horiz && vert, hash, grid) : pick(W.pieces, hash(p.c * 13, p.r * 17));
      // wall modules face +/-Z; rotate for vertical runs. Optional per-face: the open side decides a 180 flip
      var yaw = (!horiz && vert) ? Math.PI / 2 : 0;
      if (W.faceOpen) {
        if (yaw === 0 && !solid(p.c, p.r - 1) && solid(p.c, p.r + 1)) yaw = Math.PI;
        if (yaw !== 0 && !solid(p.c + 1, p.r) && solid(p.c - 1, p.r)) yaw = -Math.PI / 2;
      }
      P.add(name, z.ox + p.c + 0.5, 0, z.oz + p.r + 0.5, yaw);
    });
  }
  // a single-cell symbol: one piece per cell
  function buildCells(P, z, grid, theme, world, ch, d) {
    var pts = find(grid, ch);
    pts.forEach(function (p, i) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5, yaw = 0;
      if (d.rotate === 'run') {
        var vert = !(cellIs(grid, p.c - 1, p.r, ch) || cellIs(grid, p.c + 1, p.r, ch)) && (cellIs(grid, p.c, p.r - 1, ch) || cellIs(grid, p.c, p.r + 1, ch));
        yaw = vert ? Math.PI / 2 : 0;
      } else if (d.rotate === 'random90') yaw = Math.floor(hash(p.c, p.r * 9) * 4) * Math.PI / 2;
      else if (typeof d.rotate === 'number') yaw = d.rotate;
      var name = d.sequence ? d.pieces[i % d.pieces.length] : d.alternate ? d.pieces[(p.c + p.r) % d.pieces.length] : pick(d.pieces, hash(p.c * 3 + 1, p.r * 5 + 2));
      P.add(name, x, d.y || 0, zz, yaw);
      if (d.collide !== false) addCols(world, d.cols || colsOf(IB.themePiece(theme, name)) || boxCols(1, 1, d.h || 1), x, zz, yaw, d.kind || 'cover', z.idx);
      if (d.stack && hash(p.c * 5, p.r * 3) < d.stack.chance) {
        P.add(d.stack.piece, x, d.h || 1, zz, Math.floor(hash(p.c * 7, p.r) * 4) * Math.PI / 2);
        if (d.collide !== false) world.add(x - 0.5, d.h || 1, zz - 0.5, x + 0.5, (d.h || 1) + (d.stack.h || 1), zz + 0.5, d.kind || 'cover', z.idx);
      }
    });
  }
  // a multi-cell prefab symbol: each connected block is tiled with prefabs of size [w, d] (rotated 90 if that fits)
  function buildPrefabs(P, z, grid, theme, world, ch, d) {
    var sw = d.size[0], sd = d.size[1];
    rects(grid, ch).forEach(function (R, ri) {
      var yaw = 0, tw = sw, td = sd;
      if (!(R.w % sw === 0 && R.h % sd === 0) && R.w % sd === 0 && R.h % sw === 0) { yaw = Math.PI / 2; tw = sd; td = sw; }
      var nx = Math.max(1, Math.floor(R.w / tw)), nz = Math.max(1, Math.floor(R.h / td));
      if (R.w % tw || R.h % td) { tw = R.w / nx; td = R.h / nz; }   // block not a multiple: centre one prefab per cell group
      for (var i = 0; i < nx; i++) for (var k = 0; k < nz; k++) {
        var x = z.ox + R.c + (i + 0.5) * tw, zz = z.oz + R.r + (k + 0.5) * td, h = hash(R.c + i * 7, R.r + k * 11);
        var y = yaw + (d.flip && hash(R.c * 3 + i, R.r * 5 + k) > 0.5 ? Math.PI : 0);
        var name = d.sequence ? d.pieces[(ri + i + k) % d.pieces.length] : pick(d.pieces, h);
        P.add(name, x, d.y || 0, zz, y);
        if (d.collide !== false) addCols(world, d.cols || colsOf(IB.themePiece(theme, name)) || boxCols(sw, sd, d.h || 1), x, zz, y, d.kind || 'cover', z.idx);
      }
    });
  }
  function buildSymbols(P, z, grid, theme, world) {
    buildWalls(P, z, grid, theme, world);
    Object.keys(theme.symbols || {}).forEach(function (ch) {
      var d = theme.symbols[ch];
      if (d.size) buildPrefabs(P, z, grid, theme, world, ch, d); else buildCells(P, z, grid, theme, world, ch, d);
    });
    // spawn cans (fps-common) are part of every theme
    find(grid, 'S').forEach(function (p) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5;
      P.add(theme.spawn || 'SpawnCan', x, 0, zz, hash(p.c, p.r) * 6.28);
      world.add(x - 0.4, 0, zz - 0.4, x + 0.4, 1.0, zz + 0.4, 'cover', z.idx);
    });
  }
  // floor: flat colour plus optional painted lines (lot lines, planks, carpet tiles, lane marks)
  function paintFloor(g, x0, z0, w, h, theme, isTrail) {
    var F = theme.floor || {};
    g.flat([[x0, z0], [x0 + w, z0], [x0 + w, z0 + h], [x0, z0 + h]], 0.004, col(isTrail && F.trail ? F.trail : F.color, '#E6DCC6'));
    (F.lines || []).forEach(function (L) {
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
  function addCeiling(g, P, x0, z0, w, h, theme) {
    var C = theme.env && theme.env.ceiling; if (!C) return;
    var y = C.height, c = col(C.color, '#F2F2F2');
    g.flat([[x0, z0], [x0, z0 + h], [x0 + w, z0 + h], [x0 + w, z0]].reverse(), y, c);   // winding chosen by flat(); flipped below
    var pos = g.nor, n0 = pos.length - 12;
    for (var i = n0; i < pos.length; i += 3) pos[i + 1] = -1;
    // flip the last quad's triangles so it faces down
    var idx = g.idx; for (var t = idx.length - 6; t < idx.length; t += 3) { var tmp = idx[t + 1]; idx[t + 1] = idx[t + 2]; idx[t + 2] = tmp; }
    if (C.light) {
      var ev = C.every || 4;
      for (var lx = x0 + ev / 2; lx < x0 + w; lx += ev) for (var lz = z0 + ev / 2; lz < z0 + h; lz += ev) P.add(C.light, lx, y, lz, 0);
    }
  }

  // ---------------- gates ----------------
  // the frame is merged into the zone mesh; the shutter is its own mesh so it can roll up
  function makeGate(P, cx, cz, width, theme, zoneIdx, world, kind) {
    var GT = theme.gate || {};
    P.add(GT.frame || 'GateFrame', cx, 0, cz, 0);
    var sname = IB.themePiece(theme, GT.shutter || 'GateShutter');
    var shutter = new THREE.Mesh(IB.Assets.get(sname), IB.Assets.material(sname));
    shutter.scale.x = width / 3;
    var grp = new THREE.Group(); grp.add(shutter);
    grp.position.set(cx, 0, cz);
    var box = world.add(cx - width / 2, 0, cz - 0.3, cx + width / 2, GT.height || 3.2, cz + 0.3, 'gate', zoneIdx);
    return { group: grp, shutter: shutter, box: box, open: 1, target: 1, x: cx, z: cz, w: width, kind: kind, speed: 1 / 1.2, h: GT.shutterHeight || 3.05 };
  }
  Z.setGate = function (gate, open, instant) {
    gate.target = open ? 1 : 0;
    gate.speed = open ? 1 / 1.2 : 1 / 0.6;
    if (instant) gate.open = gate.target;
    Z.applyGate(gate);
  };
  Z.applyGate = function (gate) {
    var o = gate.open;
    gate.shutter.scale.y = Math.max(0.02, 1 - o);
    gate.shutter.position.y = o * (gate.h || 3.05);
    gate.shutter.visible = o < 0.98;
    gate.box.on = o < 0.7;
  };

  // ---------------- trail ----------------
  var DULL = new THREE.Color(0xE9DFC8), TEAL = new THREE.Color(PAL.teal);
  function buildTrail(level, from, to, theme, world, idx) {
    var g = new IB.Geo(), P = new Parts(theme), T = theme.trail || {};
    var x = from.x, z0 = from.z, z1 = to.z, w = 3, len = z0 - z1, wallH = T.height || 2.6;
    paintFloor(g, x - w / 2 - 0.5, z1, w + 1, len, theme, true);
    addCeiling(g, P, x - w / 2 - 1, z1, w + 2, len, theme);
    [-1, 1].forEach(function (sgn) {
      var wx = x + sgn * (w / 2 + 0.75);
      for (var k = 0; k < len; k++) P.add(T.wall || 'TrailWall', wx, 0, z1 + k + 0.5, sgn > 0 ? Math.PI : 0);
      world.add(wx - 0.25, 0, z1, wx + 0.25, wallH, z0, 'wall', idx);
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
  Z.navCell = function (zone, x, z) {
    var i = Math.floor((x - zone.ox) / NAV), j = Math.floor((z - zone.oz) / NAV);
    if (i < 0 || j < 0 || i >= zone.nav.nx || j >= zone.nav.nz) return -1;
    return j * zone.nav.nx + i;
  };
  Z.flowField = function (zone, tx, tz) {
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
  // direction toward target along the flow field (writes into out {x,z}); returns false if none
  Z.flowDir = function (zone, x, z, out) {
    var N = zone.nav, c = Z.navCell(zone, x, z);
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
  Z.isOpen = function (zone, x, z) { var c = Z.navCell(zone, x, z); return c >= 0 && !zone.nav.blocked[c]; };

  // ---------------- level assembly ----------------
  /* plan: {themeId, zones:[{map:'name', waves:[[['crawler',4]], ...]}]} */
  Z.ZCHECK = /[?&]zcheck=1/.test(typeof location !== 'undefined' ? location.search : '');
  Z.buildLevel = function (plan, scene) {
    if (!Z.mat) Z.mat = IB.Render.toonMaterial({});
    var world = new World(), theme = themeOf(plan);
    var level = { world: world, zones: [], trails: [], plan: plan, root: new THREE.Group(), theme: theme, tris: 0 };
    scene.add(level.root);
    var prevExit = null;
    plan.zones.forEach(function (zp, idx) {
      var grid = Z.parse(IB.ZONE_MAPS[zp.map]);
      var E = find(grid, 'E'), G = find(grid, 'G'), Pc = find(grid, 'P')[0];
      var ecx = E.length ? (E[0].c + E[E.length - 1].c + 1) / 2 : grid.w / 2;
      var ox, oz;
      if (!prevExit) { ox = -ecx; oz = -grid.h; }
      else { ox = prevExit.x - ecx; oz = prevExit.z - TRAIL_LEN - grid.h; }
      var zone = { idx: idx, ox: ox, oz: oz, w: grid.w, h: grid.h, grid: grid, plan: zp, group: new THREE.Group(), state: 'idle' };
      zone.entry = { x: ox + Pc.c + 0.5, z: oz + Pc.r + 0.5 };
      zone.spawns = find(grid, 'S').map(function (s) { return { x: ox + s.c + 0.5, z: oz + s.r + 0.5 }; });
      zone.pickups = find(grid, 'a').map(function (s) { return { kind: 'ammo', x: ox + s.c + 0.5, z: oz + s.r + 0.5 }; })
        .concat(find(grid, 'h').map(function (s) { return { kind: 'health', x: ox + s.c + 0.5, z: oz + s.r + 0.5 }; }));
      var g = new IB.Geo(), P = new Parts(theme);
      paintFloor(g, ox, oz, grid.w, grid.h, theme, false);
      buildSymbols(P, zone, grid, theme, world);
      var roofCol = col(theme.wall && theme.wall.roof, '#D9D2E6'), roofY = ((theme.wall && theme.wall.height) || 3) + 0.04;
      P.roof.forEach(function (p) {
        var x = ox + p.c, zz = oz + p.r;
        g.flat([[x, zz], [x + 1, zz], [x + 1, zz + 1], [x, zz + 1]], roofY, roofCol);
      });
      addCeiling(g, P, ox, oz, grid.w, grid.h, theme);
      if (E.length) zone.entryGate = makeGate(P, ox + ecx, oz + grid.h - 0.5, E.length, theme, idx, world, 'entry');
      var gcx = (G[0].c + G[G.length - 1].c + 1) / 2;
      zone.exitGate = makeGate(P, ox + gcx, oz + 0.5, G.length, theme, idx, world, 'exit');
      zone.ground = new THREE.Mesh(g.build(), Z.mat);
      zone.group.add(zone.ground);
      zone.meshes = meshesFor(P, zone.group);
      zone.tris = zone.meshes.reduce(function (t, m) { return t + m.geometry.index.count / 3; }, 0);
      level.tris += zone.tris;
      if (zone.entryGate) zone.group.add(zone.entryGate.group);
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
    for (var k = 0; k < 6; k++) P.add(T.wall || 'TrailWall', exit.x - 2.5 + k, 0, hz - 2.95, Math.PI / 2);
    for (k = 0; k < 5; k++) { P.add(T.wall || 'TrailWall', exit.x - 3.0, 0, hz - 2 + k, 0); P.add(T.wall || 'TrailWall', exit.x + 3.0, 0, hz - 2 + k, Math.PI); }
    world.add(exit.x - 3.25, 0, hz - 3.2, exit.x + 3.25, wallH, hz - 2.7, 'wall', -1);
    world.add(exit.x - 3.25, 0, hz - 2.75, exit.x - 2.75, wallH, hz + 2.75, 'wall', -1);
    world.add(exit.x + 2.75, 0, hz - 2.75, exit.x + 3.25, wallH, hz + 2.75, 'wall', -1);
    P.add(theme.hatch || 'Hatch', exit.x, 0, hz, 0);
    var grp = new THREE.Group(); grp.add(new THREE.Mesh(g.build(), Z.mat));
    meshesFor(P, grp);
    return { trail: tr, hatch: { group: grp, x: exit.x, z: hz, r: 1.2, z0: exit.z } };
  };

  // backdrop beyond the playable area (printed, fogged): rings of theme/common pieces; outlined puff clouds outdoors
  Z.buildBackdrop = function (level, theme) {
    var g = new IB.Geo(), minZ = 0, maxZ = 0, F = theme.floor || {};
    level.zones.forEach(function (z) { minZ = Math.min(minZ, z.oz - 20); });
    var cz = (minZ + maxZ) / 2, rad = (maxZ - minZ) / 2 + 70;
    if (theme.backdrop !== null) {
      g.flat([[-rad - 60, cz - rad - 60], [rad + 60, cz - rad - 60], [rad + 60, cz + rad + 60], [-rad - 60, cz + rad + 60]], -0.02, col(F.outside || F.color, '#E6DCC6').multiplyScalar(F.outside ? 1 : 0.94));
      level.root.add(new THREE.Mesh(g.build(), Z.mat));
    }
    var B = theme.backdrop, P = new Parts(theme);
    if (B && B.ring) B.ring.forEach(function (ring, ri) {
      for (var i = 0; i < ring.count; i++) {
        var a = (i + ri * 0.37) / ring.count * Math.PI * 2, rr = rad - 70 + ring.radius[0] + (ring.radius[1] - ring.radius[0]) * hash(i, 3 + ri);
        var x = Math.cos(a) * rr * (ring.squeezeX || 0.6), z = cz + Math.sin(a) * rr;
        var sc = ring.scale[0] + (ring.scale[1] - ring.scale[0]) * hash(i, 7 + ri), sq = ring.squash ? ring.squash[0] + (ring.squash[1] - ring.squash[0]) * hash(i, 8) : 1;
        var m = M(x, ring.y || 0, z, ring.face ? Math.atan2(-x, -(z - cz)) : a);
        m.multiply(new THREE.Matrix4().makeScale(sc, sc * sq, sc));
        P.add(ring.piece, 0, 0, 0, 0, m);
      }
    });
    meshesFor(P, level.root);
    level.clouds = []; level.cloudMeshes = [];
    if (!(theme.env && theme.env.clouds)) return;
    if (!Z.cloudMat) { Z.cloudMat = IB.Render.toonMaterial({ map: IB.Assets.palette.common, baked: 0.06 }); Z.cloudMat.emissive = new THREE.Color(0x7A7468); Z.cloudMat.fog = false; }
    ['Cloud_A', 'Cloud_B', 'Cloud_C'].forEach(function (name, si) {
      var N = 4, im = new THREE.InstancedMesh(IB.Assets.get(name), Z.cloudMat, N);
      im.frustumCulled = false;
      for (var k = 0; k < N; k++) {
        var j = si * 4 + k;
        level.clouds.push({ mesh: im, i: k, x: (hash(j, 11) - 0.5) * 260, y: 44 + hash(j, 12) * 22, z: cz + (hash(j, 13) - 0.5) * 260, s: 1.6 + hash(j, 14) * 1.4, yaw: hash(j, 15) * 6.28 });
      }
      level.cloudMeshes.push(im); level.root.add(im);
    });
    Z.updateClouds(level, 0);
  };
  var _cm = new THREE.Matrix4(), _cq = new THREE.Quaternion(), _cp = new THREE.Vector3(), _cs = new THREE.Vector3();
  Z.updateClouds = function (level, dt) {
    if (!level || !level.clouds || !level.clouds.length) return;
    for (var k = 0; k < level.clouds.length; k++) {
      var cl = level.clouds[k]; cl.x += dt * 0.6; if (cl.x > 140) cl.x = -140;
      _cq.setFromAxisAngle(_up, cl.yaw); _cp.set(cl.x, cl.y, cl.z); _cs.set(cl.s, cl.s, cl.s);
      cl.mesh.setMatrixAt(cl.i, _cm.compose(_cp, _cq, _cs));
    }
    level.cloudMeshes.forEach(function (m) { m.instanceMatrix.needsUpdate = true; });
  };

  // brief 4.2: only the current zone, the next zone and the trail between them are drawn
  Z.setVisible = function (level, cur) {
    level.zones.forEach(function (z, i) { z.group.visible = (i === cur || i === cur + 1); });
    level.trails.forEach(function (t, i) { t.group.visible = (i === cur || i === cur - 1); });
    if (level.hatch) level.hatch.group.visible = cur >= level.zones.length - 1;
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
