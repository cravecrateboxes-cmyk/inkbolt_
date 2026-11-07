/* INKBOLT throwables: the player's frag cans (G). A thrown can flies on a ballistic arc, bounces off the ground, walls,
   cover and robots (losing energy each bounce), rolls to a stop, and goes off when its fuse runs out: a comic blast
   through IB.Projectiles.explode (robots and the player in reach take splash, behind cover halves it; explosive
   canisters light up and chain). The fuse light blinks faster as it runs down and a red ring shows the blast reach.
     IB.Throwables.init(scene)
     IB.Throwables.throw(x, y, z, vx, vy, vz, def, dmgMul)    def: IB.WEAPONS.frag
     IB.Throwables.update(dt, world, level)                   fixed step (game.js)
     IB.Throwables.sync(t)                                    render side: meshes, rings
     IB.Throwables.clear(), IB.Throwables.live()              */
(function (IB) {
  'use strict';
  var T = IB.Throwables = { list: [] };
  var CAP = 6, R = 0.07, G = 16, _tmp = [];

  T.init = function (scene) {
    var A = IB.Assets, geo = A.get('HELD_Frag');
    var mat = IB.Render.toonMaterial({ map: A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0 });
    var ringMat = new THREE.MeshBasicMaterial({ color: IB.PAL.red, transparent: true, opacity: 0.55, depthWrite: false });
    var ringGeo = new THREE.RingGeometry(0.92, 1, 40);
    for (var i = 0; i < CAP; i++) {
      var m = new THREE.Mesh(geo, mat); m.visible = false; m.scale.setScalar(1.7); scene.add(m);
      var ring = new THREE.Mesh(ringGeo, ringMat); ring.rotation.x = -Math.PI / 2; ring.visible = false; ring.renderOrder = 2; scene.add(ring);
      T.list.push({ on: false, mesh: m, ring: ring, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, t: 0, fuse: 2.2, rx: 0, rz: 0, spin: 0, def: null, mul: 1, rest: false, bounces: 0 });
    }
  };
  T.clear = function () { T.list.forEach(function (g) { g.on = false; g.mesh.visible = false; g.ring.visible = false; }); };
  T.live = function () { return T.list.filter(function (g) { return g.on; }).length; };

  T.throw = function (x, y, z, vx, vy, vz, def, mul) {
    var g = null, i;
    for (i = 0; i < CAP; i++) if (!T.list[i].on) { g = T.list[i]; break; }
    if (!g) { g = T.list[0]; for (i = 1; i < CAP; i++) if (T.list[i].t > g.t) g = T.list[i]; }
    g.on = true; g.t = 0; g.x = x; g.y = y; g.z = z; g.vx = vx; g.vy = vy; g.vz = vz; g.def = def; g.fuse = def.fuse || 2.2;
    g.mul = mul || 1; g.rest = false; g.bounces = 0; g.spin = 9 + Math.random() * 5; g.rx = 0; g.rz = 0;
    g.mesh.visible = true;
    return g;
  };

  function bounce(g, nx, ny, nz) {
    var e = (g.def.restitution || 0.35), vn = g.vx * nx + g.vy * ny + g.vz * nz;
    if (vn >= 0) return;
    g.vx -= (1 + e) * vn * nx; g.vy -= (1 + e) * vn * ny; g.vz -= (1 + e) * vn * nz;
    var f = 0.72; g.vx *= f; g.vz *= f; if (ny < 0.5) g.vy *= f;   // scrape: tangential speed lost per bounce
    g.spin *= 0.6;
    if (Math.abs(vn) > 1.5) { g.bounces++; if (IB.Audio) IB.Audio.play('step', { pos: { x: g.x, z: g.z }, pitch: 1.8, gain: Math.min(1, Math.abs(vn) / 6) }); }
  }

  T.update = function (dt, world) {
    for (var i = 0; i < CAP; i++) {
      var g = T.list[i]; if (!g.on) continue;
      g.t += dt;
      if (g.t >= g.fuse) { detonate(g); continue; }
      if (g.rest) continue;
      g.vy -= G * dt;
      g.x += g.vx * dt; g.y += g.vy * dt; g.z += g.vz * dt;
      // ground
      if (g.y < R) { g.y = R; bounce(g, 0, 1, 0); }
      // boxes (walls, cover, gates, decks): push out along the shallowest axis and bounce off that face
      world.query(g.x - R, g.z - R, g.x + R, g.z + R, _tmp);
      for (var k = 0; k < _tmp.length; k++) {
        var b = _tmp[k];
        if (g.x + R <= b.x0 || g.x - R >= b.x1 || g.z + R <= b.z0 || g.z - R >= b.z1 || g.y + R <= b.y0 || g.y - R >= b.y1) continue;
        var px0 = g.x + R - b.x0, px1 = b.x1 - (g.x - R), pz0 = g.z + R - b.z0, pz1 = b.z1 - (g.z - R), py0 = g.y + R - b.y0, py1 = b.y1 - (g.y - R);
        var m = Math.min(px0, px1, pz0, pz1, py0, py1);
        if (m === py1) { g.y = b.y1 + R; bounce(g, 0, 1, 0); }
        else if (m === py0) { g.y = b.y0 - R; bounce(g, 0, -1, 0); }
        else if (m === px0) { g.x = b.x0 - R; bounce(g, -1, 0, 0); }
        else if (m === px1) { g.x = b.x1 + R; bounce(g, 1, 0, 0); }
        else if (m === pz0) { g.z = b.z0 - R; bounce(g, 0, 0, -1); }
        else { g.z = b.z1 + R; bounce(g, 0, 0, 1); }
      }
      // robots: a can thrown at a robot clonks off it
      var AI = IB.AI;
      if (AI && AI.robots) for (var j = 0; j < AI.robots.length; j++) {
        var r = AI.robots[j]; if (!r.on || r.state === 'spawn' || r.state === 'pose' || r.rogue > 0) continue;
        var v = AI.VIS[r.type], dx = g.x - r.x, dz = g.z - r.z, d = Math.hypot(dx, dz);
        if (d > v.radius + R || g.y < r.y + v.y0 - R || g.y > r.y + v.y1 + R) continue;
        d = d || 1; g.x = r.x + dx / d * (v.radius + R); g.z = r.z + dz / d * (v.radius + R);
        bounce(g, dx / d, 0, dz / d);
      }
      // settled on a surface: stop simulating (it waits for its fuse)
      if (g.y <= R + 0.01 && Math.abs(g.vy) < 0.6 && Math.hypot(g.vx, g.vz) < 0.25) { g.rest = true; g.vx = g.vz = g.vy = 0; }
      if (Math.hypot(g.vx, g.vz) < 0.25 && Math.abs(g.vy) < 0.6) g.vx *= 0.9, g.vz *= 0.9;
      g.rx += g.spin * dt; g.rz += g.spin * 0.6 * dt;
    }
  };

  function detonate(g) {
    g.on = false; g.mesh.visible = false; g.ring.visible = false;
    var d = g.def, Rb = (d.radius || 5) * (g.mul > 0 ? 1 : 1);
    // the player takes at most selfCap (35) from their own can; robots the full splash (scaled with robot health)
    if (IB.Projectiles) IB.Projectiles.explode(g.x, Math.max(0.3, g.y), g.z, Rb, d.selfCap || 35, (d.splash || d.damage) * g.mul, { type: 'frag', x: g.x, z: g.z, player: true });
    if (IB.AI && IB.AI.hear) IB.AI.hear(g.x, g.z, 30);
  }

  T.sync = function (t) {
    for (var i = 0; i < CAP; i++) {
      var g = T.list[i]; if (!g.on) continue;
      g.mesh.position.set(g.x, g.y, g.z);
      if (g.rest) g.mesh.rotation.set(Math.PI / 2, g.rx, 0); else g.mesh.rotation.set(g.rx, 0, g.rz);
      // the blast reach shows on the floor in the last second, blinking faster as the fuse runs down
      var left = g.fuse - g.t, show = left < 1.2;
      g.ring.visible = show && Math.sin(t * (left < 0.5 ? 40 : 22)) > -0.2;
      if (show) { var rr = (g.def.radius || 5); g.ring.position.set(g.x, Math.max(0.02, g.y - R + 0.02), g.z); g.ring.scale.set(rr, rr, rr); }
      if (IB.FX && Math.random() < 0.25) IB.FX.puff(g.x, g.y + 0.08, g.z, 1, IB.PAL.paper, 0.04, 0.12, 0.4);
    }
  };
})(window.IB = window.IB || {});
