/* INKBOLT breakable doors and panels (theme symbol option `breakable`). Generic: any theme can give a prefab symbol
     breakable: { hp: 420, debris: 'metal' | 'glass' | 'mesh' | 'field', color: '#3A4048', word: 'KRUNCH!',
                  blend: 'add' (the leaf is drawn additive and unlit: a force field),
                  leaf: 'Name' (optional: the leaf pieces' base name, so frame variants share one leaf) }
   usually with orient: 'span' (the prefab's local X runs along the wall line it closes) and kind: 'wall'. Kit pieces:
     <Piece>            the frame (jambs, header, reveal): merged into the zone like any prefab, its _COL boxes collide
     <Piece>_Leaf       the closed door: its own mesh; its _COL boxes (or one box over the opening) block movement,
                        shots, sight lines and the nav grid until it breaks
     <Piece>_Leaf_D1    dented / cracked (shown under 2/3 of its hp), <Piece>_Leaf_D2 (under 1/3), both optional
     <Piece>_Broken     what is left in the frame after it bursts (bent leaf stubs, a glass fringe), optional; its
                        _COL boxes (a slab left leaning in the opening) collide only once it has burst
   Damage: the player's bullets (game.js shoot) and melee (meleeHit), robot bolts (projectiles.js), and every blast in
   reach (Projectiles detonate: frag cans, soldier grenades, bombers, canisters, Boom Cans; launchers.js rockets) with
   falloff over the blast radius, x BLAST_MUL. hp is in level-1 damage units: hits are divided by the level's robot
   health multiplier (AI.hpMul), so a door takes as many shots on level 20 as on level 1 with a gun of the level.
   Damaged doors spark now and then. At 0 hp the leaf bursts (Boom.shatter: debris, dust, a comic word), its boxes
   switch off and the zone's nav grid is rebuilt (Zones.renav), so robots path through and sight lines open.
   Mounts in a breakable prefab (a gun in a containment pod) are locked (mount.lock) until it breaks (game.js).
   Every door is whole again when the level restarts (reset, from game.js resetLevelState). */
(function (IB) {
  'use strict';
  var D = IB.Doors = {};
  D.BLAST_MUL = 4;      // explosives against doors
  D.MELEE_MUL = 1.5;    // a blade or an axe against a door
  D.stats = { hits: 0, blasts: 0, broken: 0 };
  var STATES = ['_Leaf', '_Leaf_D1', '_Leaf_D2', '_Broken'];
  var addMat = {};
  function glowMat(fam) {
    if (!addMat[fam]) addMat[fam] = new THREE.MeshBasicMaterial({ map: IB.Assets.mat[fam].map, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false });
    return addMat[fam];
  }
  function rnd(a, b) { return a + Math.random() * (b - a); }
  function hpMul() { return (IB.AI && IB.AI.hpMul) || 1; }

  /* zones.js buildPrefabs: one breakable prefab placed at (x, y0, zz) turned by yaw (the frame is already merged) */
  D.build = function (z, theme, world, d, name, x, y0, zz, yaw, mounts) {
    var B = d.breakable, A = IB.Assets, Z = IB.Zones, base = B.leaf || name;
    var names = STATES.map(function (s) { var n = IB.themePiece(theme, base + s); return A.geo[n] ? n : null; });
    if (!names[0]) throw new Error('INKBOLT breakable leaf missing: ' + IB.themePiece(theme, base + '_Leaf'));
    var grp = new THREE.Group(); grp.position.set(x, y0, zz); grp.rotation.y = yaw;
    var meshes = names.map(function (n, i) {
      if (!n) return null;
      var m = new THREE.Mesh(A.get(n), B.blend === 'add' && i < 3 ? glowMat(A.family[n]) : A.material(n));
      if (B.blend === 'add' && i < 3) m.renderOrder = 2;
      m.visible = i === 0; grp.add(m); return m;
    });
    var cols = Z.colsOf(names[0]) || [{ x: 0, y: 1.3, z: 0, hx: d.size[0] / 2, hy: 1.3, hz: 0.12 }];
    var c = Math.round(Math.cos(yaw)), s = Math.round(Math.sin(yaw)), rec = null, boxes = [], after = [], lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
    function add(b, piece) {
      var cx = b.x * c + b.z * s, cz = -b.x * s + b.z * c, hx = c !== 0 ? b.hx : b.hz, hz = c !== 0 ? b.hz : b.hx;
      var nb = world.add(x + cx - hx, y0 + b.y - b.hy, zz + cz - hz, x + cx + hx, y0 + b.y + b.hy, zz + cz + hz, 'wall', z.idx);
      nb.piece = piece; return nb;
    }
    cols.forEach(function (b) {
      var nb = add(b, names[0]); boxes.push(nb);
      lo[0] = Math.min(lo[0], nb.x0); lo[1] = Math.min(lo[1], nb.y0); lo[2] = Math.min(lo[2], nb.z0);
      hi[0] = Math.max(hi[0], nb.x1); hi[1] = Math.max(hi[1], nb.y1); hi[2] = Math.max(hi[2], nb.z1);
    });
    if (names[3]) (Z.colsOf(names[3]) || []).forEach(function (b) { var nb = add(b, names[3]); nb.on = false; after.push(nb); });
    var ax = Math.cos(yaw), az = -Math.sin(yaw);   // the prefab's local X in the world: along the opening
    rec = { zone: z.idx, x: (lo[0] + hi[0]) / 2, y: (lo[1] + hi[1]) / 2, z: (lo[2] + hi[2]) / 2, lo: lo, hi: hi, yaw: yaw, ax: ax, az: az,
      w: Math.abs(ax) > 0.5 ? hi[0] - lo[0] : hi[2] - lo[2], h: hi[1] - lo[1], hp0: B.hp || 300, hp: B.hp || 300, state: 0, broken: false,
      boxes: boxes, after: after, meshes: meshes, group: grp, kind: B.debris || 'metal', color: B.color ? parseInt(B.color.slice(1), 16) : undefined,
      word: B.word || null, piece: name, sparkT: 0, mounts: mounts || [] };
    boxes.forEach(function (b) { b.door = rec; });
    rec.mounts.forEach(function (m) { m.lock = rec; });
    z.doors.push(rec); z.group.add(grp);
    return rec;
  };

  function show(rec) {
    var k = rec.broken ? 3 : rec.state;
    rec.meshes.forEach(function (m, i) { if (m) m.visible = i === k || (rec.broken && i === 3); });
    if (!rec.broken) {   // a missing damage stage shows the one before it
      var j = k; while (j > 0 && !rec.meshes[j]) j--;
      if (rec.meshes[j]) rec.meshes[j].visible = true;
    }
  }
  function burst(rec, px, pz) {
    var G = IB.Game, level = G && G.level; if (!level) return;
    rec.broken = true; rec.hp = 0;
    rec.boxes.forEach(function (b) { b.on = false; });
    rec.after.forEach(function (b) { b.on = true; });
    show(rec);
    // the debris flies away from what broke it (along the door's normal)
    var nx = -rec.az, nz = rec.ax, k = (px - rec.x) * nx + (pz - rec.z) * nz;
    if (k > 0) { nx = -nx; nz = -nz; }
    if (IB.Boom && IB.Boom.shatter) IB.Boom.shatter(rec.x, rec.y, rec.z, rec.w, rec.h, rec.ax, rec.az, nx, nz, rec.kind, rec.color, rec.word);
    var zone = level.zones[rec.zone];
    if (zone && IB.Zones.renav) IB.Zones.renav(zone, level.world);
    if (IB.AI && IB.AI.hear) IB.AI.hear(rec.x, rec.z, 30);
    D.stats.broken++;
  }
  // amt in level-1 units; (px, pz): where the damage came from
  function damage(rec, amt, px, pz) {
    if (rec.broken || !(amt > 0)) return;
    rec.hp -= amt;
    if (rec.hp <= 0) { burst(rec, px, pz); return; }
    var st = rec.hp < rec.hp0 / 3 ? 2 : rec.hp < rec.hp0 * 2 / 3 ? 1 : 0;
    if (st !== rec.state) {
      rec.state = st; show(rec);
      if (IB.Boom && IB.Boom.sparks) IB.Boom.sparks(rec.x, rec.y + rec.h * 0.1, rec.z, 0, 0.5, 0, 10, rec.kind === 'field' ? 0x8EF6FF : undefined);
      if (IB.Audio) IB.Audio.play(rec.kind === 'glass' ? 'crunch' : 'boltHit', { pos: { x: rec.x, z: rec.z }, gain: 0.7, pitch: rec.kind === 'glass' ? 1.8 : 0.7 });
    }
  }
  /* a bullet, bolt or blade hit a box (true when it was a door): dmg as dealt to robots; from 'player' | 'robot' | 'melee' */
  D.hit = function (box, dmg, x, y, z, nx, ny, nz, from) {
    var rec = box && box.door; if (!rec || rec.broken) return false;
    D.stats.hits++;
    var B = IB.Boom && IB.Boom.ready ? IB.Boom : null;
    if (B) {
      if (rec.kind === 'glass') B.sparks(x, y, z, nx, ny, nz, 3, 0xE9FCFF);
      else if (rec.kind === 'field') B.zap(x + nx * 0.05, y, z + nz * 0.05, 0.35, 0x5FF2FF);
      else B.impact(x, y, z, nx, ny, nz, { kind: 'gate' });   // metal: sparks and a glint
    }
    damage(rec, dmg * (from === 'melee' ? D.MELEE_MUL : 1) / hpMul(), x + nx, z + nz);
    return true;
  };
  /* a blast at (x, y, z) of radius R that deals dmg at its centre (to robots): every door in reach takes its share */
  D.blast = function (x, y, z, R, dmg) {
    var G = IB.Game, level = G && G.level; if (!level || !(R > 0) || !(dmg > 0)) return;
    D.stats.blasts++;
    level.zones.forEach(function (zone) {
      (zone.doors || []).forEach(function (rec) {
        if (rec.broken) return;
        var cx = Math.max(rec.lo[0], Math.min(rec.hi[0], x)), cy = Math.max(rec.lo[1], Math.min(rec.hi[1], y)), cz = Math.max(rec.lo[2], Math.min(rec.hi[2], z));
        var d = Math.sqrt((cx - x) * (cx - x) + (cy - y) * (cy - y) + (cz - z) * (cz - z));
        if (d >= R) return;
        damage(rec, dmg * Math.pow(1 - d / R, 0.5) * D.BLAST_MUL / hpMul(), x, z);
      });
    });
  };
  /* sparks off damaged doors near the player; a cracked force field flickers */
  D.update = function (dt, player) {
    var G = IB.Game, level = G && G.level; if (!level || !player) return;
    var B = IB.Boom && IB.Boom.ready ? IB.Boom : null;
    level.zones.forEach(function (zone) {
      if (!zone.group.visible) return;
      (zone.doors || []).forEach(function (rec) {
        if (rec.broken || !rec.state) return;
        if (rec.kind === 'field' && rec.meshes[rec.state]) rec.meshes[rec.state].visible = Math.random() > 0.12 * rec.state;
        rec.sparkT -= dt;
        if (rec.sparkT > 0) return;
        rec.sparkT = rnd(0.5, 1.8) / rec.state;
        if (!B || Math.hypot(player.x - rec.x, player.z - rec.z) > 36) return;
        var u = rnd(-0.45, 0.45) * rec.w, side = Math.random() < 0.5 ? -1 : 1, d = (rec.hi[0] - rec.lo[0] + rec.hi[2] - rec.lo[2] - rec.w) / 2 + 0.03;
        B.sparks(rec.x + rec.ax * u - rec.az * side * d, rec.lo[1] + rnd(0.3, 0.9) * rec.h, rec.z + rec.az * u + rec.ax * side * d, -rec.az * side, 0.2, rec.ax * side, 3 + rec.state * 2, rec.kind === 'field' ? 0x8EF6FF : undefined);
      });
    });
  };
  /* level (re)start: every door whole and shut, nav grids rebuilt where one was open */
  D.reset = function (level) {
    if (!level) return;
    level.zones.forEach(function (zone) {
      var dirty = false;
      (zone.doors || []).forEach(function (rec) {
        if (rec.broken) dirty = true;
        rec.hp = rec.hp0; rec.state = 0; rec.broken = false; rec.sparkT = 0;
        rec.boxes.forEach(function (b) { b.on = true; });
        rec.after.forEach(function (b) { b.on = false; });
        show(rec);
      });
      if (dirty && IB.Zones.renav) IB.Zones.renav(zone, level.world);
    });
    D.stats.hits = D.stats.blasts = D.stats.broken = 0;
  };
  /* tests: every door of the level */
  D.list = function () {
    var G = IB.Game, level = G && G.level, out = [];
    if (level) level.zones.forEach(function (zone, zi) {
      (zone.doors || []).forEach(function (rec, i) {
        out.push({ zone: zi, i: i, piece: rec.piece, x: rec.x, y: rec.y, z: rec.z, ax: rec.ax, az: rec.az, w: rec.w, h: rec.h, hp: rec.hp, hp0: rec.hp0, state: rec.state, broken: rec.broken, kind: rec.kind,
          boxes: rec.boxes.map(function (b) { return b.id; }), mounts: rec.mounts.length });
      });
    });
    return out;
  };
})(window.IB = window.IB || {});
