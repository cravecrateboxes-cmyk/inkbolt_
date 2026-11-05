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

  // ---------------- theme kits (Blender GLB pieces, brief 3.2 / 5.12) ----------------
  // Each theme maps ASCII symbols to its kit's meshes. Pieces are placed per cell and merged per zone
  // into one geometry on the kit's palette material (plus one for fps-common pieces such as spawn cans).
  var KITS = IB.KITS;   // src/data/assets.js
  Z.KITS = KITS;
  function kitFor(theme) { return KITS[theme.kit || theme.id] || KITS.toytown; }
  function kitColors(theme) {
    var p = theme.palette.map(function (h) { return new THREE.Color(h); });
    return { main: p[0], second: p[1], accent: p[2], ground: p[3] };
  }
  var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _up = new THREE.Vector3(0, 1, 0), _p = new THREE.Vector3(), _s1 = new THREE.Vector3(1, 1, 1);
  function M(x, y, z, yaw) { _q.setFromAxisAngle(_up, yaw || 0); _p.set(x, y, z); return _m.clone().compose(_p, _q, _s1); }

  function Parts() { this.kit = []; this.common = []; this.roof = []; }
  var PID = 0;
  Z.pidNames = {};
  Parts.prototype.add = function (name, x, y, z, yaw) {
    var list = IB.Assets.family[name] === 'common' ? this.common : this.kit;
    var g = IB.Assets.placed(name, M(x, y, z, yaw));
    if (Z.ZCHECK) {   // tag each placed piece so the cross-piece z-fighting check can tell pieces apart
      var n = g.attributes.position.count, a = new Float32Array(n); a.fill(++PID);
      g.setAttribute('pid', new THREE.BufferAttribute(a, 1)); Z.pidNames[PID] = name;
    }
    list.push(g);
  };
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

  function buildWalls(P, z, grid, kit, world) {
    rects(grid, '#').forEach(function (R) {
      world.add(z.ox + R.c, 0, z.oz + R.r, z.ox + R.c + R.w, 3, z.oz + R.r + R.h, 'wall', z.idx);
    });
    var WALLISH = '#GE';
    function solid(c, r) { return cellIs(grid, c, r, WALLISH); }
    find(grid, '#').forEach(function (p) {
      // only cells with an open neighbour get a wall module; building interiors get a flat roof instead
      var exposed = !solid(p.c - 1, p.r) || !solid(p.c + 1, p.r) || !solid(p.c, p.r - 1) || !solid(p.c, p.r + 1) ||
        !solid(p.c - 1, p.r - 1) || !solid(p.c + 1, p.r - 1) || !solid(p.c - 1, p.r + 1) || !solid(p.c + 1, p.r + 1);
      if (!exposed) { P.roof.push(p); return; }
      var horiz = cellIs(grid, p.c - 1, p.r, WALLISH) || cellIs(grid, p.c + 1, p.r, WALLISH);
      var vert = cellIs(grid, p.c, p.r - 1, WALLISH) || cellIs(grid, p.c, p.r + 1, WALLISH);
      var corner = horiz && vert;
      // shop fronts: runs of 4 cells share a colour; windows most of the way, the odd door
      var run = horiz ? Math.floor(p.c / 4) * 31 + p.r : Math.floor(p.r / 4) * 31 + p.c * 7;
      var color = kit.wallColors[Math.floor(hash(run, horiz ? 3 : 5) * kit.wallColors.length)];
      var h = hash(p.c * 13, p.r * 17), kind = corner ? 'Plain' : (h < 0.12 ? 'Door' : h < 0.72 ? 'Window' : 'Plain');
      P.add(kit.prefix + 'Wall' + kind + '_' + color, z.ox + p.c + 0.5, 0, z.oz + p.r + 0.5, (!horiz && vert) ? Math.PI / 2 : 0);
    });
  }
  function buildLowWalls(P, z, grid, kit, world) {
    rects(grid, '=').forEach(function (R) { world.add(z.ox + R.c, 0, z.oz + R.r, z.ox + R.c + R.w, 1, z.oz + R.r + R.h, 'cover', z.idx); });
    find(grid, '=').forEach(function (p) {
      var vert = !(cellIs(grid, p.c - 1, p.r, '=') || cellIs(grid, p.c + 1, p.r, '=')) && (cellIs(grid, p.c, p.r - 1, '=') || cellIs(grid, p.c, p.r + 1, '='));
      P.add(kit.prefix + kit.low[(p.c + p.r) % 2], z.ox + p.c + 0.5, 0, z.oz + p.r + 0.5, vert ? Math.PI / 2 : 0);
    });
  }
  function buildCrates(P, z, grid, kit, world) {
    find(grid, 'c').forEach(function (p) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5, tall = hash(p.c * 5, p.r * 3) > 0.78;
      world.add(x - 0.5, 0, zz - 0.5, x + 0.5, tall ? 2 : 1, zz + 0.5, 'cover', z.idx);
      P.add(kit.prefix + kit.crate, x, 0, zz, Math.floor(hash(p.c, p.r * 9) * 4) * Math.PI / 2);
      if (tall) P.add(kit.prefix + kit.crateTop, x, 1, zz, Math.floor(hash(p.c * 7, p.r) * 4) * Math.PI / 2);   // quarter turns only: stays inside its cell
    });
  }
  function buildContainers(P, z, grid, kit, world) {
    blocks(grid, 'C', 2, 2).forEach(function (R) {
      var x0 = z.ox + R.c, z0 = z.oz + R.r;
      world.add(x0, 0, z0, x0 + R.w, 2.5, z0 + R.h, 'cover', z.idx);
      P.add(kit.prefix + kit.containers[Math.floor(hash(R.c, R.r) * kit.containers.length)], x0 + R.w / 2, 0, z0 + R.h / 2, 0);
    });
  }
  function buildLandmark(P, z, grid, kit, world) {
    blocks(grid, 'T', 6, 6).forEach(function (R) {
      var cx = z.ox + R.c + R.w / 2, cz = z.oz + R.r + R.h / 2, hw = 1.3;
      [[-hw, -hw], [hw, -hw], [hw, hw], [-hw, hw]].forEach(function (L) {
        world.add(cx + L[0] - 0.2, 0, cz + L[1] - 0.2, cx + L[0] + 0.2, 7.5, cz + L[1] + 0.2, 'wall', z.idx);
      });
      P.add(kit.prefix + kit.landmark, cx, 0, cz, 0);
    });
  }
  function buildDecor(P, z, grid, kit) {
    find(grid, 'p').forEach(function (p, i) { P.add(kit.prefix + kit.billboards[i % kit.billboards.length], z.ox + p.c + 0.5, 0, z.oz + p.r + 0.5, 0); });
  }
  function buildSpawnCans(P, z, grid, world) {
    find(grid, 'S').forEach(function (p) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5;
      P.add('SpawnCan', x, 0, zz, hash(p.c, p.r) * 6.28);
      world.add(x - 0.4, 0, zz - 0.4, x + 0.4, 1.0, zz + 0.4, 'cover', z.idx);
    });
  }
  function paintLotLines(g, z, grid) {
    for (var r = 3; r < grid.h - 3; r += 6) {
      for (var c = 2; c < grid.w - 2; c += 3) {
        if (hash(c, r) < 0.35) continue;
        var x = z.ox + c, zz = z.oz + r;
        g.flat([[x - 0.06, zz], [x + 0.06, zz], [x + 0.06, zz + 2.6], [x - 0.06, zz + 2.6]], 0.012, 0xFFFDF7);
      }
    }
  }
  function meshesFor(P, group) {
    var out = [];
    if (P.kit.length) { var a = new THREE.Mesh(IB.Assets.merge(P.kit), IB.Assets.mat[IB.Assets.family[Z.kitProbe]]); group.add(a); out.push(a); }
    if (P.common.length) { var b = new THREE.Mesh(IB.Assets.merge(P.common), IB.Assets.mat.common); group.add(b); out.push(b); }
    return out;
  }

  // ---------------- gates ----------------
  // the frame is merged into the zone mesh; the shutter is its own mesh so it can roll up
  function makeGate(P, cx, cz, width, kit, zoneIdx, world, kind) {
    P.add(kit.prefix + kit.gateFrame, cx, 0, cz, 0);
    var shutter = new THREE.Mesh(IB.Assets.get(kit.prefix + kit.shutter), IB.Assets.material(kit.prefix + kit.shutter));
    shutter.scale.x = width / 3;
    var grp = new THREE.Group(); grp.add(shutter);
    grp.position.set(cx, 0, cz);
    var box = world.add(cx - width / 2, 0, cz - 0.3, cx + width / 2, 3.2, cz + 0.3, 'gate', zoneIdx);
    return { group: grp, shutter: shutter, box: box, open: 1, target: 1, x: cx, z: cz, w: width, kind: kind, speed: 1 / 1.2 };
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
    gate.shutter.position.y = o * 3.05;
    gate.shutter.visible = o < 0.98;
    gate.box.on = o < 0.7;
  };

  // ---------------- trail ----------------
  var DULL = new THREE.Color(0xE9DFC8), TEAL = new THREE.Color(PAL.teal);
  function buildTrail(level, from, to, theme, kit, world, idx) {
    var g = new IB.Geo(), kc = kitColors(theme), P = new Parts();
    var x = from.x, z0 = from.z, z1 = to.z, w = 3;
    g.flat([[x - w / 2 - 0.5, z1], [x + w / 2 + 0.5, z1], [x + w / 2 + 0.5, z0], [x - w / 2 - 0.5, z0]], 0.006, kc.ground.clone().multiplyScalar(0.96));
    var len = z0 - z1;
    [-1, 1].forEach(function (sgn) {
      var wx = x + sgn * (w / 2 + 0.75);
      for (var k = 0; k < len; k++) P.add(kit.prefix + kit.trailWall, wx, 0, z1 + k + 0.5, 0);
      world.add(wx - 0.25, 0, z1, wx + 0.25, 2.6, z0, 'wall', idx);
    });
    var grp = new THREE.Group();
    grp.add(new THREE.Mesh(g.build(), Z.mat));
    meshesFor(P, grp);
    // painted arrows: TrailArrow (fps-common) copies, recoloured per arrow when lit
    var n = Math.floor(len / 2), src = IB.Assets.get('TrailArrow'), list = [];
    for (var i = 0; i < n; i++) list.push(IB.Assets.placed('TrailArrow', M(x, 0.02, z0 - 1 - i * 2, 0)));
    var ag = THREE.BufferGeometryUtils.mergeBufferGeometries(list, false);
    var vertsPer = src.attributes.position.count;
    var col = new Float32Array(ag.attributes.position.count * 3);
    for (var v = 0; v < col.length; v += 3) { col[v] = DULL.r; col[v + 1] = DULL.g; col[v + 2] = DULL.b; }
    ag.setAttribute('color', new THREE.BufferAttribute(col, 3));
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
        var b = tmp[k]; if (b.y1 < 0.35 || b.kind === 'gate') continue;
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
  /* plan: {theme:{id,palette,...}, zones:[{map:'name', waves:[[['crawler',4]], ...]}]} */
  Z.ZCHECK = /[?&]zcheck=1/.test(typeof location !== 'undefined' ? location.search : '');
  Z.buildLevel = function (plan, scene) {
    if (!Z.mat) Z.mat = IB.Render.toonMaterial({});
    var world = new World(), theme = plan.theme, kc = kitColors(theme), kit = kitFor(theme);
    Z.kitProbe = kit.prefix + kit.crate;
    var level = { world: world, zones: [], trails: [], plan: plan, root: new THREE.Group(), theme: theme, kit: kit, tris: 0 };
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
      var g = new IB.Geo(), P = new Parts();
      g.flat([[ox, oz], [ox + grid.w, oz], [ox + grid.w, oz + grid.h], [ox, oz + grid.h]], 0.004, kc.ground);
      paintLotLines(g, zone, grid);
      buildWalls(P, zone, grid, kit, world);
      buildLowWalls(P, zone, grid, kit, world);
      buildCrates(P, zone, grid, kit, world);
      buildContainers(P, zone, grid, kit, world);
      buildLandmark(P, zone, grid, kit, world);
      buildDecor(P, zone, grid, kit);
      buildSpawnCans(P, zone, grid, world);
      // flat roofs over building interiors (below the parapet trim of the edge modules)
      var roofCol = new THREE.Color(0xD9D2E6);
      P.roof.forEach(function (p) {
        var x = ox + p.c, zz = oz + p.r;
        g.flat([[x, zz], [x + 1, zz], [x + 1, zz + 1], [x, zz + 1]], 3.04, roofCol);
      });
      if (E.length) zone.entryGate = makeGate(P, ox + ecx, oz + grid.h - 0.5, E.length, kit, idx, world, 'entry');
      var gcx = (G[0].c + G[G.length - 1].c + 1) / 2;
      zone.exitGate = makeGate(P, ox + gcx, oz + 0.5, G.length, kit, idx, world, 'exit');
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
        var tr = buildTrail(level, { x: prevExit.x, z: prevExit.z }, { x: prevExit.x, z: prevExit.z - TRAIL_LEN }, theme, kit, world, idx - 1);
        level.trails.push(tr); level.root.add(tr.group);
      }
      prevExit = { x: ox + gcx, z: oz };
    });
    var last = Z.buildHatch(level, prevExit, theme, kit, world);
    level.trails.push(last.trail); level.root.add(last.trail.group);
    level.hatch = last.hatch; level.root.add(last.hatch.group);
    Z.buildBackdrop(level, theme);
    if (Z.ZCHECK) {
      level.zfight = [];
      level.root.traverse(function (o) { if (o.isMesh && o.geometry.attributes.pid) level.zfight = level.zfight.concat(Z.zfight(o)); });
    }
    return level;
  };

  Z.buildHatch = function (level, exit, theme, kit, world) {
    // the exit waypath: a long walled path; the screen dims as the player walks it, then the next level loads
    var WAY = 22;
    var tr = buildTrail(level, { x: exit.x, z: exit.z }, { x: exit.x, z: exit.z - WAY }, theme, kit, world, level.zones.length - 1);
    var hz = exit.z - WAY - 1.5, g = new IB.Geo(), P = new Parts();
    g.flat([[exit.x - 3, hz - 2.5], [exit.x + 3, hz - 2.5], [exit.x + 3, exit.z - WAY], [exit.x - 3, exit.z - WAY]], 0.006, 0xE6DCC6);
    for (var k = 0; k < 6; k++) P.add(kit.prefix + kit.trailWall, exit.x - 2.5 + k, 0, hz - 2.95, Math.PI / 2);
    for (k = 0; k < 5; k++) { P.add(kit.prefix + kit.trailWall, exit.x - 3.0, 0, hz - 2 + k, 0); P.add(kit.prefix + kit.trailWall, exit.x + 3.0, 0, hz - 2 + k, 0); }
    world.add(exit.x - 3.25, 0, hz - 3.2, exit.x + 3.25, 3, hz - 2.7, 'wall', -1);
    world.add(exit.x - 3.25, 0, hz - 2.75, exit.x - 2.75, 3, hz + 2.75, 'wall', -1);
    world.add(exit.x + 2.75, 0, hz - 2.75, exit.x + 3.25, 3, hz + 2.75, 'wall', -1);
    P.add(kit.prefix + kit.hatch, exit.x, 0, hz, 0);
    var grp = new THREE.Group(); grp.add(new THREE.Mesh(g.build(), Z.mat));
    meshesFor(P, grp);
    return { trail: tr, hatch: { group: grp, x: exit.x, z: hz, r: 1.2, z0: exit.z } };
  };

  // distant rolling hills and pines beyond the playable area (printed backdrop, fogged), outlined puff clouds
  Z.buildBackdrop = function (level, theme) {
    var g = new IB.Geo(), kc = kitColors(theme), P = new Parts();
    var minZ = 0, maxZ = 0;
    level.zones.forEach(function (z) { minZ = Math.min(minZ, z.oz - 20); });
    var cz = (minZ + maxZ) / 2, rad = (maxZ - minZ) / 2 + 70;
    g.flat([[-rad - 60, cz - rad - 60], [rad + 60, cz - rad - 60], [rad + 60, cz + rad + 60], [-rad - 60, cz + rad + 60]], -0.02, kc.ground.clone().multiplyScalar(0.94));
    var list = [];
    for (var i = 0; i < 26; i++) {
      var a = i / 26 * Math.PI * 2, r = rad + 10 * hash(i, 3), x = Math.cos(a) * r * 0.6, z = cz + Math.sin(a) * r;
      var s = 0.9 + hash(i, 7) * 0.6, hm = M(x, -2, z, a);
      hm.multiply(new THREE.Matrix4().makeScale(s, s * (0.8 + hash(i, 8) * 0.5), s));
      list.push(IB.Assets.placed('Hill', hm));
      if (i % 3 === 0) for (var t = 0; t < 3; t++) list.push(IB.Assets.placed('Tree', M(x + t * 3 - 3, 0, z - 12 * Math.sign(Math.sin(a) || 1), t)));
    }
    var ground = new THREE.Mesh(g.build(), Z.mat);
    var hills = new THREE.Mesh(IB.Assets.merge(list), IB.Assets.mat.common);
    level.root.add(ground); level.root.add(hills);
    level.backdrop = hills;
    // clouds: one instanced mesh per puff shape, drifting
    if (!Z.cloudMat) { Z.cloudMat = IB.Render.toonMaterial({ map: IB.Assets.palette.common, baked: 0.06 }); Z.cloudMat.emissive = new THREE.Color(0x7A7468); Z.cloudMat.fog = false; }
    level.clouds = []; level.cloudMeshes = [];
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
    if (!level.clouds) return;
    for (var k = 0; k < level.clouds.length; k++) {
      var cl = level.clouds[k]; cl.x += dt * 0.6; if (cl.x > 140) cl.x = -140;
      _cq.setFromAxisAngle(_up, cl.yaw); _cp.set(cl.x, cl.y, cl.z); _cs.set(cl.s, cl.s, cl.s);
      cl.mesh.setMatrixAt(cl.i, _cm.compose(_cp, _cq, _cs));
    }
    level.cloudMeshes.forEach(function (m) { m.instanceMatrix.needsUpdate = true; });
  };

  // visibility: previous, current, next zone + trails around current
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
