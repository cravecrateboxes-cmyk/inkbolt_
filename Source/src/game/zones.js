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

  // ---------------- kit (Toy Town greybox) ----------------
  // Each theme maps symbols to geometry; palette = [main, secondary, accent, ground]
  function kitColors(theme) {
    var p = theme.palette.map(function (h) { return new THREE.Color(h); });
    return { main: p[0], second: p[1], accent: p[2], ground: p[3] };
  }
  var WALL_SET = [PAL.tangerine, PAL.bubblegum, PAL.purple, 0x5BC0EB, PAL.sand, 0xF26B5B];

  function buildWalls(g, z, grid, theme, world) {
    rects(grid, '#').forEach(function (R) {
      var x0 = z.ox + R.c, z0 = z.oz + R.r, sx = R.w, sz = R.h, H = 3;
      world.add(x0, 0, z0, x0 + sx, H, z0 + sz, 'wall', z.idx);
      // shop-front segments along the longer axis, each its own colour with a parapet strip
      var along = sx >= sz ? 'x' : 'z', len = along === 'x' ? sx : sz, seg = 0;
      while (seg < len) {
        var segLen = Math.min(len - seg, 3 + Math.floor(hash(R.c + seg, R.r) * 4));
        var colr = WALL_SET[Math.floor(hash(R.c * 3 + seg, R.r * 7) * WALL_SET.length)];
        var cx, cz, wx, wz;
        if (along === 'x') { cx = x0 + seg + segLen / 2; cz = z0 + sz / 2; wx = segLen; wz = sz; }
        else { cx = x0 + sx / 2; cz = z0 + seg + segLen / 2; wx = sx; wz = segLen; }
        var hh = H + (hash(seg, R.c + R.r) > 0.6 ? 0.6 : 0);
        g.box(cx, hh / 2, cz, wx, hh, wz, colr);
        g.box(cx, hh + 0.12, cz, wx + 0.12, 0.24, wz + 0.12, 0xF4EEE2);
        // windows / doors on both long faces
        if (segLen >= 3) {
          var n = Math.floor(segLen / 2.2);
          for (var k = 0; k < n; k++) {
            var off = (k + 0.5) * segLen / n - segLen / 2;
            var isDoor = (k === 0 && hash(seg + 9, R.r) > 0.6);
            var wy = isDoor ? 0.95 : 1.9, wh = isDoor ? 1.9 : 0.85, ww = isDoor ? 0.9 : 1.0;
            var winCol = isDoor ? 0x3B3550 : 0x8ED2FF;
            if (along === 'x') {
              g.box(cx + off, wy, cz - wz / 2 - 0.03, ww, wh, 0.06, winCol, { hullScale: 0.7 });
              g.box(cx + off, wy, cz + wz / 2 + 0.03, ww, wh, 0.06, winCol, { hullScale: 0.7 });
            } else {
              g.box(cx - wx / 2 - 0.03, wy, cz + off, 0.06, wh, ww, winCol, { hullScale: 0.7 });
              g.box(cx + wx / 2 + 0.03, wy, cz + off, 0.06, wh, ww, winCol, { hullScale: 0.7 });
            }
          }
        }
        seg += segLen;
      }
    });
  }
  function buildLowWalls(g, z, grid, theme, world) {
    rects(grid, '=').forEach(function (R) {
      var x0 = z.ox + R.c, z0 = z.oz + R.r;
      world.add(x0, 0, z0, x0 + R.w, 1, z0 + R.h, 'cover', z.idx);
      var along = R.w >= R.h, len = along ? R.w : R.h;
      for (var i = 0; i < len; i++) {
        var cx = along ? x0 + i + 0.5 : x0 + R.w / 2, cz = along ? z0 + R.h / 2 : z0 + i + 0.5;
        var sx = along ? 1 : R.w, sz = along ? R.h : 1;
        g.box(cx, 0.45, cz, sx - 0.04, 0.9, sz * 0.8, 0xD8D2C4, { topTint: 0xEAE5D8 });
        g.box(cx, 0.95, cz, sx - 0.04, 0.1, sz * 0.9, i % 2 ? PAL.teal : PAL.ink, { hull: false });
      }
    });
  }
  function buildCrates(g, z, grid, theme, world) {
    find(grid, 'c').forEach(function (p) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5;
      // stack a second crate on some
      var tall = hash(p.c * 5, p.r * 3) > 0.78;
      world.add(x - 0.5, 0, zz - 0.5, x + 0.5, tall ? 2 : 1, zz + 0.5, 'cover', z.idx);
      for (var s = 0; s < (tall ? 2 : 1); s++) {
        var y = s + 0.5, colr = s ? PAL.bubblegum : PAL.tangerine;
        g.box(x, y, zz, 0.96, 0.96, 0.96, colr);
        g.box(x, y, zz - 0.49, 0.98, 0.12, 0.04, 0xC8642A, { hull: false });
        g.box(x, y, zz + 0.49, 0.98, 0.12, 0.04, 0xC8642A, { hull: false });
        g.box(x - 0.49, y, zz, 0.04, 0.12, 0.98, 0xC8642A, { hull: false });
        g.box(x + 0.49, y, zz, 0.04, 0.12, 0.98, 0xC8642A, { hull: false });
      }
    });
  }
  function buildContainers(g, z, grid, theme, world) {
    blocks(grid, 'C', 2, 2).forEach(function (R, i) {
      var x0 = z.ox + R.c, z0 = z.oz + R.r, cx = x0 + R.w / 2, cz = z0 + R.h / 2, H = 2.5;
      world.add(x0, 0, z0, x0 + R.w, H, z0 + R.h, 'cover', z.idx);
      var colr = [PAL.teal, PAL.tangerine, PAL.bubblegum, 0x5BC0EB][Math.floor(hash(R.c, R.r) * 4)];
      g.box(cx, H / 2, cz, R.w - 0.04, H, R.h - 0.04, colr);
      // ribs
      for (var k = 0; k < 4; k++) {
        var o = -R.w / 2 + 0.3 + k * (R.w - 0.6) / 3;
        g.box(cx + o, H / 2, cz - R.h / 2, 0.08, H - 0.2, 0.06, PAL.ink, { hull: false });
        g.box(cx + o, H / 2, cz + R.h / 2, 0.08, H - 0.2, 0.06, PAL.ink, { hull: false });
      }
      g.box(cx, H + 0.03, cz, R.w - 0.2, 0.06, R.h - 0.2, 0xF4EEE2, { hull: false });
    });
  }
  function buildLandmark(g, z, grid, theme, world) {
    blocks(grid, 'T', 6, 6).forEach(function (R) {
      var x0 = z.ox + R.c, z0 = z.oz + R.r, cx = x0 + R.w / 2, cz = z0 + R.h / 2;
      var hw = R.w / 2 - 0.2, hd = R.h / 2 - 0.2, legH = 7.5;
      var legs = [[-hw, -hd], [hw, -hd], [hw, hd], [-hw, hd]];
      legs.forEach(function (L) {
        g.box(cx + L[0], legH / 2, cz + L[1], 0.28, legH, 0.28, PAL.purple);
        world.add(cx + L[0] - 0.2, 0, cz + L[1] - 0.2, cx + L[0] + 0.2, legH, cz + L[1] + 0.2, 'wall', z.idx);
      });
      // cross bracing (rotated thin boxes)
      var m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
      for (var side = 0; side < 4; side++) {
        var a = legs[side], b = legs[(side + 1) % 4];
        var mx = cx + (a[0] + b[0]) / 2, mz = cz + (a[1] + b[1]) / 2, len = Math.hypot(b[0] - a[0], b[1] - a[1]);
        var yaw = Math.atan2(b[1] - a[1], b[0] - a[0]);
        for (var lv = 0; lv < 2; lv++) {
          var y0 = 1.2 + lv * 3, diag = Math.hypot(len, 3), pitch = Math.atan2(3, len);
          [1, -1].forEach(function (sgn) {
            e.set(0, -yaw, sgn * pitch, 'YXZ'); q.setFromEuler(e);
            m.compose(new THREE.Vector3(mx, y0 + 1.5, mz), q, new THREE.Vector3(1, 1, 1));
            g.setMatrix(m); g.box(0, 0, 0, diag, 0.14, 0.14, PAL.purple); g.setMatrix(null);
          });
          g.box(mx, y0 + 3, mz, Math.abs(b[0] - a[0]) + 0.2, 0.18, Math.abs(b[1] - a[1]) + 0.2, PAL.purple);
        }
      }
      var r = Math.max(hw, hd) + 0.5;
      g.box(cx, legH + 0.1, cz, R.w + 0.6, 0.2, R.h + 0.6, 0x6A55B8);
      g.cyl(cx, legH + 0.2, cz, r, r, 3.0, 14, 0xF4EEE2);
      g.cyl(cx, legH + 1.2, cz, r + 0.03, r + 0.03, 0.5, 14, PAL.bubblegum, { hull: false, noTop: true, noBottom: true });
      g.cyl(cx, legH + 3.2, cz, r + 0.1, 0.3, 1.4, 14, PAL.tangerine);
      g.cyl(cx, legH + 4.6, cz, 0.08, 0.08, 1.0, 5, PAL.ink, { hull: false });
    });
  }
  function buildDecor(g, z, grid, theme) {
    find(grid, 'p').forEach(function (p, i) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5;
      var col = [PAL.bubblegum, PAL.tangerine, PAL.teal, PAL.purple][i % 4];
      // billboard on two posts, facing south (+z) toward the zone entry
      g.box(x - 1.2, 2.2, zz, 0.16, 4.4, 0.16, PAL.gunmetal);
      g.box(x + 1.2, 2.2, zz, 0.16, 4.4, 0.16, PAL.gunmetal);
      g.box(x, 4.1, zz, 3.6, 1.6, 0.2, 0xFFFDF7);
      g.box(x - 0.6, 4.1, zz + 0.12, 2.0, 0.8, 0.04, col, { hull: false });
      g.box(x + 1.15, 4.1, zz + 0.12, 0.7, 0.7, 0.04, PAL.ink, { hull: false });
    });
  }
  function buildSpawnCans(g, z, grid, world) {
    find(grid, 'S').forEach(function (p) {
      var x = z.ox + p.c + 0.5, zz = z.oz + p.r + 0.5;
      g.cyl(x, 0, zz, 0.42, 0.48, 0.95, 10, 0x8C93A0);
      g.cyl(x, 0.95, zz, 0.52, 0.5, 0.1, 10, 0x6E7480);
      g.box(x, 1.08, zz, 0.3, 0.08, 0.08, PAL.ink, { hull: false });
      world.add(x - 0.4, 0, zz - 0.4, x + 0.4, 1.0, zz + 0.4, 'cover', z.idx);
    });
  }
  function buildPickupsMarks(g, z, grid) {
    // painted lot lines on the ground around containers/crates for the "parking lot" read
    for (var r = 3; r < grid.h - 3; r += 6) {
      for (var c = 2; c < grid.w - 2; c += 3) {
        if (hash(c, r) < 0.35) continue;
        var x = z.ox + c, zz = z.oz + r;
        g.flat([[x - 0.06, zz], [x + 0.06, zz], [x + 0.06, zz + 2.6], [x - 0.06, zz + 2.6]], 0.012, 0xFFFDF7);
      }
    }
  }

  // ---------------- gates ----------------
  function makeGate(cx, cz, width, theme, zoneIdx, world, kind) {
    var g = new IB.Geo();
    var kc = kitColors(theme);
    g.box(-width / 2 - 0.25, 1.8, 0, 0.5, 3.6, 0.7, PAL.gunmetal);
    g.box(width / 2 + 0.25, 1.8, 0, 0.5, 3.6, 0.7, PAL.gunmetal);
    g.box(0, 3.35, 0, width + 1.0, 0.6, 0.8, PAL.gunmetal);
    g.box(-width / 2 + 0.3, 3.35, 0.42, 0.34, 0.24, 0.06, PAL.teal, { hullScale: 0.6 });
    g.box(width / 2 - 0.3, 3.35, 0.42, 0.34, 0.24, 0.06, PAL.teal, { hullScale: 0.6 });
    g.box(-width / 2 + 0.3, 3.35, -0.42, 0.34, 0.24, 0.06, PAL.teal, { hullScale: 0.6 });
    g.box(width / 2 - 0.3, 3.35, -0.42, 0.34, 0.24, 0.06, PAL.teal, { hullScale: 0.6 });
    var frame = new THREE.Mesh(g.build(), IB.Zones.mat);
    // shutter: slats in theme main colour, hazard band of teal/ink blocks at the bottom
    var s = new IB.Geo(), H = 3.05, slats = 9;
    for (var i = 0; i < slats; i++) {
      var y = 0.55 + i * (H - 0.55) / slats + (H - 0.55) / slats / 2;
      s.box(0, y, 0, width, (H - 0.55) / slats - 0.05, 0.14, i % 2 ? kc.main : kc.main.clone().multiplyScalar(0.92), { hull: false });
    }
    var nb = 8;
    for (var k = 0; k < nb; k++) s.box(-width / 2 + (k + 0.5) * width / nb, 0.27, 0, width / nb, 0.5, 0.16, k % 2 ? PAL.ink : PAL.teal, { hull: false });
    s.boxHull(0, H / 2, 0, width, H, 0.16, 1);
    var shutter = new THREE.Mesh(s.build(), IB.Zones.mat);
    var grp = new THREE.Group(); grp.add(frame); grp.add(shutter);
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
    gate.box.on = o < 0.7;
  };

  // ---------------- trail ----------------
  function buildTrail(level, from, to, theme, world, idx) {
    var g = new IB.Geo(), kc = kitColors(theme);
    var x = from.x, z0 = from.z, z1 = to.z, w = 3;
    // ground strip and walls either side
    g.flat([[x - w / 2 - 0.5, z1], [x + w / 2 + 0.5, z1], [x + w / 2 + 0.5, z0], [x - w / 2 - 0.5, z0]], 0.006, kc.ground.clone().multiplyScalar(0.96));
    var len = z0 - z1, wallH = 2.6;
    [-1, 1].forEach(function (sgn) {
      var wx = x + sgn * (w / 2 + 0.75);
      g.box(wx, wallH / 2, (z0 + z1) / 2, 0.5, wallH, len, kc.second);
      g.box(wx, wallH + 0.08, (z0 + z1) / 2, 0.62, 0.16, len, 0xF4EEE2);
      for (var k = 1; k < len; k += 3) g.box(wx, wallH / 2, z1 + k, 0.56, wallH * 0.98, 0.2, kc.accent, { hull: false });
      world.add(wx - 0.25, 0, z1, wx + 0.25, wallH, z0, 'wall', idx);
    });
    var mesh = new THREE.Mesh(g.build(), IB.Zones.mat);
    // arrows: one merged unlit mesh, recoloured per arrow
    var a = new IB.Geo(), n = Math.floor(len / 2), dull = new THREE.Color(0xE9DFC8);
    for (var i = 0; i < n; i++) {
      var az = z0 - 1 - i * 2;
      a.flat([[x, az - 0.5], [x + 0.7, az + 0.2], [x + 0.7, az + 0.55], [x, az - 0.15]], 0.02, dull);
      a.flat([[x, az - 0.5], [x, az - 0.15], [x - 0.7, az + 0.55], [x - 0.7, az + 0.2]], 0.02, dull);
    }
    var ag = a.build();
    var arrows = new THREE.Mesh(ag, new THREE.MeshBasicMaterial({ vertexColors: true }));
    var grp = new THREE.Group(); grp.add(mesh); grp.add(arrows);
    var vertsPer = ag.attributes.position.count / Math.max(1, n);
    return { group: grp, arrows: arrows, count: n, vertsPer: vertsPer, lit: 0, litT: -1, x: x, z0: z0, z1: z1 };
  }
  Z.lightTrail = function (trail, n) {
    var colA = trail.arrows.geometry.attributes.color, teal = new THREE.Color(PAL.teal), dull = new THREE.Color(0xE9DFC8);
    for (var i = 0; i < trail.count; i++) {
      var c = i < n ? teal : dull;
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
  /* plan: {theme:{palette,...}, zones:[{map:'name', waves:[[['crawler',4]], ...]}]} */
  Z.buildLevel = function (plan, scene) {
    if (!Z.mat) Z.mat = IB.Render.toonMaterial({});
    var world = new World(), theme = plan.theme, kc = kitColors(theme);
    var level = { world: world, zones: [], trails: [], plan: plan, root: new THREE.Group(), theme: theme };
    scene.add(level.root);
    var prevExit = null;
    plan.zones.forEach(function (zp, idx) {
      var grid = Z.parse(IB.ZONE_MAPS[zp.map]);
      var E = find(grid, 'E'), G = find(grid, 'G'), P = find(grid, 'P')[0];
      var ecx = E.length ? (E[0].c + E[E.length - 1].c + 1) / 2 : grid.w / 2;
      var ox, oz;
      if (!prevExit) { ox = -ecx; oz = -grid.h; }
      else { ox = prevExit.x - ecx; oz = prevExit.z - TRAIL_LEN - grid.h; }
      var zone = { idx: idx, ox: ox, oz: oz, w: grid.w, h: grid.h, grid: grid, plan: zp, group: new THREE.Group(), state: 'idle' };
      zone.entry = { x: ox + P.c + 0.5, z: oz + P.r + 0.5 };
      zone.spawns = find(grid, 'S').map(function (s) { return { x: ox + s.c + 0.5, z: oz + s.r + 0.5 }; });
      zone.pickups = find(grid, 'a').map(function (s) { return { kind: 'ammo', x: ox + s.c + 0.5, z: oz + s.r + 0.5 }; })
        .concat(find(grid, 'h').map(function (s) { return { kind: 'health', x: ox + s.c + 0.5, z: oz + s.r + 0.5 }; }));
      var g = new IB.Geo();
      // zone floor
      g.flat([[ox, oz], [ox + grid.w, oz], [ox + grid.w, oz + grid.h], [ox, oz + grid.h]], 0.004, kc.ground);
      buildWalls(g, zone, grid, theme, world);
      buildLowWalls(g, zone, grid, theme, world);
      buildCrates(g, zone, grid, theme, world);
      buildContainers(g, zone, grid, theme, world);
      buildLandmark(g, zone, grid, theme, world);
      buildDecor(g, zone, grid, theme);
      buildSpawnCans(g, zone, grid, world);
      buildPickupsMarks(g, zone, grid);
      zone.tris = g.count();
      zone.mesh = new THREE.Mesh(g.build(), Z.mat);
      zone.group.add(zone.mesh);
      // gates
      if (E.length) {
        zone.entryGate = makeGate(ox + ecx, oz + grid.h - 0.5, E.length, theme, idx, world, 'entry');
        zone.group.add(zone.entryGate.group);
      }
      var gcx = (G[0].c + G[G.length - 1].c + 1) / 2;
      zone.exitGate = makeGate(ox + gcx, oz + 0.5, G.length, theme, idx, world, 'exit');
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
    // final trail + exit hatch
    var last = Z.buildHatch(level, prevExit, theme, world);
    level.trails.push(last.trail); level.root.add(last.trail.group);
    level.hatch = last.hatch; level.root.add(last.hatch.group);
    Z.buildBackdrop(level, theme);
    return level;
  };

  Z.buildHatch = function (level, exit, theme, world) {
    var tr = buildTrail(level, { x: exit.x, z: exit.z }, { x: exit.x, z: exit.z - 8 }, theme, world, level.zones.length - 1);
    var hz = exit.z - 9.5, g = new IB.Geo();
    // pad + end wall
    g.flat([[exit.x - 3, hz - 2.5], [exit.x + 3, hz - 2.5], [exit.x + 3, exit.z - 8], [exit.x - 3, exit.z - 8]], 0.006, 0xE6DCC6);
    g.box(exit.x, 1.5, hz - 2.8, 6.5, 3, 0.5, PAL.gunmetal);
    g.box(exit.x - 3.0, 1.5, hz, 0.5, 3, 5.5, PAL.gunmetal);
    g.box(exit.x + 3.0, 1.5, hz, 0.5, 3, 5.5, PAL.gunmetal);
    world.add(exit.x - 3.25, 0, hz - 3.05, exit.x + 3.25, 3, hz - 2.55, 'wall', -1);
    world.add(exit.x - 3.25, 0, hz - 2.75, exit.x - 2.75, 3, hz + 2.75, 'wall', -1);
    world.add(exit.x + 2.75, 0, hz - 2.75, exit.x + 3.25, 3, hz + 2.75, 'wall', -1);
    g.cyl(exit.x, 0, hz, 1.25, 1.2, 0.12, 20, PAL.gunmetal);
    g.cyl(exit.x, 0.12, hz, 0.95, 0.95, 0.02, 20, PAL.teal, { hull: false });
    for (var i = 0; i < 6; i++) { var a = i / 6 * Math.PI * 2; g.cyl(exit.x + Math.cos(a) * 1.08, 0.12, hz + Math.sin(a) * 1.08, 0.07, 0.07, 0.05, 6, PAL.amber, { hull: false }); }
    g.box(exit.x, 2.7, hz - 2.5, 2.4, 0.5, 0.1, PAL.teal);
    var mesh = new THREE.Mesh(g.build(), Z.mat);
    var grp = new THREE.Group(); grp.add(mesh);
    return { trail: tr, hatch: { group: grp, x: exit.x, z: hz, r: 1.2 } };
  };

  // distant rolling hills + tree cones beyond the playable area (printed backdrop, fogged)
  Z.buildBackdrop = function (level, theme) {
    var g = new IB.Geo(), kc = kitColors(theme);
    var minZ = 0, maxZ = 0;
    level.zones.forEach(function (z) { minZ = Math.min(minZ, z.oz - 20); });
    var cz = (minZ + maxZ) / 2, rad = (maxZ - minZ) / 2 + 70;
    g.flat([[-rad - 60, cz - rad - 60], [rad + 60, cz - rad - 60], [rad + 60, cz + rad + 60], [-rad - 60, cz + rad + 60]], -0.02, kc.ground.clone().multiplyScalar(0.94));
    for (var i = 0; i < 26; i++) {
      var a = i / 26 * Math.PI * 2, r = rad + 10 * hash(i, 3);
      var x = Math.cos(a) * r * 0.6, z = cz + Math.sin(a) * r;
      g.sphere(x, -2, z, 14 + 10 * hash(i, 7), i % 2 ? 0x7FC47A : 0x9AD38A, { ws: 10, hs: 6, sy: 0.55 });
      if (i % 3 === 0) for (var t = 0; t < 3; t++) g.cyl(x + t * 3 - 3, 0, z - 12 * Math.sign(Math.sin(a) || 1), 1.2, 0, 4.5, 6, 0x3F8F6A);
    }
    var m = new THREE.Mesh(g.build(), Z.mat);
    level.root.add(m);
    level.backdrop = m;
    // clouds: one instanced mesh of a puff
    var c = new IB.Geo();
    c.sphere(0, 0, 0, 2.2, 0xFFFDF7, { sy: 0.7 }); c.sphere(2.2, -0.3, 0.2, 1.6, 0xFFFDF7, { sy: 0.7 }); c.sphere(-2.1, -0.4, 0, 1.5, 0xFFFDF7, { sy: 0.7 });
    if (!Z.cloudMat) { Z.cloudMat = IB.Render.toonMaterial({}); Z.cloudMat.emissive = new THREE.Color(0x8A8478); Z.cloudMat.fog = false; }
    var N = 10, im = new THREE.InstancedMesh(c.build(), Z.cloudMat, N), mm = new THREE.Matrix4();
    level.clouds = [];
    for (var k = 0; k < N; k++) {
      var cl = { x: (hash(k, 11) - 0.5) * 160, y: 26 + hash(k, 12) * 14, z: cz + (hash(k, 13) - 0.5) * 160, s: 1 + hash(k, 14) * 1.2 };
      level.clouds.push(cl);
      mm.makeScale(cl.s, cl.s, cl.s).setPosition(cl.x, cl.y, cl.z); im.setMatrixAt(k, mm);
    }
    im.frustumCulled = false;
    level.cloudMesh = im; level.root.add(im);
  };
  Z.updateClouds = function (level, dt) {
    if (!level.cloudMesh) return;
    var mm = new THREE.Matrix4();
    for (var k = 0; k < level.clouds.length; k++) {
      var cl = level.clouds[k]; cl.x += dt * 0.6; if (cl.x > 90) cl.x = -90;
      mm.makeScale(cl.s, cl.s, cl.s).setPosition(cl.x, cl.y, cl.z); level.cloudMesh.setMatrixAt(k, mm);
    }
    level.cloudMesh.instanceMatrix.needsUpdate = true;
  };

  // visibility: previous, current, next zone + trails around current
  Z.setVisible = function (level, cur) {
    level.zones.forEach(function (z, i) { z.group.visible = (i >= cur - 1 && i <= cur + 1); });
    level.trails.forEach(function (t, i) { t.group.visible = (i >= cur - 1 && i <= cur + 1); });
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
