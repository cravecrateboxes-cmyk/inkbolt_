/* INKBOLT enemy projectiles and explosions (Gunner bolts, Drone bursts, Bomber blasts).
   Contract used by game.js:
     IB.Projectiles.init(scene)
     IB.Projectiles.clear()
     IB.Projectiles.update(dt, ctx)  ctx = {player, world, hurt(source, dmg), shake(trauma), onKill(robot)}
   Used by ai.js:
     IB.Projectiles.fire(x, y, z, dx, dy, dz, speed, dmg, sourceRobot)       one bolt (dir normalised); returns it
       b.kind = 'bullet' (Soldier rounds: a thin fast tracer) or a special round that also hurts over time on a hit:
       'boom' (explosive: a small blast), 'shock' (electric DoT), 'acid' (acid DoT) -- IB.Troops.dot()
     IB.Projectiles.explode(x, y, z, radius, dmgPlayer, dmgRobots, sourceRobot)  queued blast (60 ms later, so chains ripple)
   Pools (brief 4.5): 96 bolts, 8 blasts (5 lobes each), 16 queued blasts; everything is drawn by ONE InstancedMesh:
   an unlit sphere with a baked inverted-hull ink outline; a bolt = Amber head + a stretched Alert-red trail,
   a blast = a comic cloud of outlined lobes going Paper White -> Amber -> Alert Red as it swells and shrinks.
   Collision (brief 4.3): bolt segment vs player capsule (r 0.35, h 1.7), ray + sphere vs world AABBs.
   Blast damage: D * (1 - d/R)^0.7 within R of the target's surface, x0.5 behind cover (world ray), knockback. */
(function (IB) {
  'use strict';
  var BOLT_CAP = 96, BLAST_CAP = 8, LOBES = 5, QUEUE_CAP = 16;
  var HIT_R = 0.08, VIS_R = 0.12, PLAYER_R = 0.35, PLAYER_H = 1.7, LIFE = 3.0, TRAIL = 0.95, BLAST_T = 0.42;
  var Pj = IB.Projectiles = { bolts: [], blasts: [], queue: [], mesh: null, ctx: null, boltCount: 0 };

  // ---------------- pure helpers (unit-tested, no THREE) ----------------
  function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
  /* squared distance between segments P0P1 and Q0Q1 (closest points, clamped; Ericson 5.1.9) */
  Pj.segSegDist2 = function (p0x, p0y, p0z, p1x, p1y, p1z, q0x, q0y, q0z, q1x, q1y, q1z) {
    var d1x = p1x - p0x, d1y = p1y - p0y, d1z = p1z - p0z, d2x = q1x - q0x, d2y = q1y - q0y, d2z = q1z - q0z;
    var rx = p0x - q0x, ry = p0y - q0y, rz = p0z - q0z;
    var a = d1x * d1x + d1y * d1y + d1z * d1z, e = d2x * d2x + d2y * d2y + d2z * d2z, f = d2x * rx + d2y * ry + d2z * rz;
    var s, t;
    if (a <= 1e-12 && e <= 1e-12) { s = t = 0; }
    else if (a <= 1e-12) { s = 0; t = clamp01(f / e); }
    else {
      var c = d1x * rx + d1y * ry + d1z * rz;
      if (e <= 1e-12) { t = 0; s = clamp01(-c / a); }
      else {
        var b = d1x * d2x + d1y * d2y + d1z * d2z, den = a * e - b * b;
        s = den > 1e-12 ? clamp01((b * f - c * e) / den) : 0;
        t = (b * s + f) / e;
        if (t < 0) { t = 0; s = clamp01(-c / a); } else if (t > 1) { t = 1; s = clamp01((b - c) / a); }
      }
    }
    var dx = (p0x + d1x * s) - (q0x + d2x * t), dy = (p0y + d1y * s) - (q0y + d2y * t), dz = (p0z + d1z * s) - (q0z + d2z * t);
    return dx * dx + dy * dy + dz * dz;
  };
  /* does the moving sphere (segment A->B, radius br) touch a vertical capsule (axis x,z from y0 to y1, radius cr)? */
  Pj.segHitsCapsule = function (ax, ay, az, bx, by, bz, cx, y0, y1, cz, cr, br) {
    var R = cr + br;
    return Pj.segSegDist2(ax, ay, az, bx, by, bz, cx, y0, cz, cx, y1, cz) <= R * R;
  };
  /* sphere vs AABB {x0,y0,z0,x1,y1,z1} */
  Pj.sphereBox = function (x, y, z, r, b) {
    var cx = x < b.x0 ? b.x0 : x > b.x1 ? b.x1 : x, cy = y < b.y0 ? b.y0 : y > b.y1 ? b.y1 : y, cz = z < b.z0 ? b.z0 : z > b.z1 ? b.z1 : z;
    var dx = x - cx, dy = y - cy, dz = z - cz;
    return dx * dx + dy * dy + dz * dz <= r * r;
  };
  /* blast falloff (brief 5.6 shape): D * (1 - d/R)^0.7 for d < R, halved behind cover */
  Pj.blastDamage = function (d, R, D, covered) {
    if (d >= R) return 0;
    return D * Math.pow(1 - Math.max(0, d) / R, 0.7) * (covered ? 0.5 : 1);
  };

  if (typeof window === 'undefined' || typeof THREE === 'undefined') return;   // node unit tests: helpers only

  var PAL = IB.PAL;
  var ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
  var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _v = new THREE.Vector3(), _s = new THREE.Vector3(), _d = new THREE.Vector3(), _z = new THREE.Vector3(0, 0, 1), _c = new THREE.Color(), _tmp = [];
  var KIND = {   // head, trail colours per round kind (bolt = the robots' ink bolts)
    bullet: [new THREE.Color(0xFFF1B8), new THREE.Color(0xFFD86A)], boom: [new THREE.Color(0xFFB04A), new THREE.Color(0xFF5A1E)],
    shock: [new THREE.Color(0xC8F6FF), new THREE.Color(0x3FC8FF)], acid: [new THREE.Color(0xD6FF8A), new THREE.Color(0x5BE03A)] };
  var C_HEAD = new THREE.Color(0xFFC83A), C_TRAIL = new THREE.Color(PAL.red), C_HOT = new THREE.Color(PAL.paper), C_AMBER = new THREE.Color(PAL.amber), C_RED = new THREE.Color(PAL.red);

  // unlit sphere + inverted hull (aHull = outward dir, 0 on the solid), one geometry, one draw call
  function inkSphere() {
    var g = new THREE.SphereGeometry(1, 10, 7), pos = g.attributes.position.array, idx = g.index.array, n = pos.length / 3;
    var P = new Float32Array(n * 6), H = new Float32Array(n * 6), I = new (n * 2 > 65535 ? Uint32Array : Uint16Array)(idx.length * 2);
    for (var i = 0; i < n * 3; i++) { P[i] = pos[i]; P[n * 3 + i] = pos[i]; H[n * 3 + i] = pos[i]; }
    for (i = 0; i < idx.length; i += 3) {
      I[i] = idx[i]; I[i + 1] = idx[i + 1]; I[i + 2] = idx[i + 2];
      I[idx.length + i] = idx[i] + n; I[idx.length + i + 1] = idx[i + 2] + n; I[idx.length + i + 2] = idx[i + 1] + n;   // flipped
    }
    var out = new THREE.BufferGeometry();
    out.setAttribute('position', new THREE.BufferAttribute(P, 3));
    out.setAttribute('aHull', new THREE.BufferAttribute(H, 3));
    out.setIndex(new THREE.BufferAttribute(I, 1));
    g.dispose();
    return out;
  }
  function inkMaterial() {
    var mat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    var uInk = { value: new THREE.Color(PAL.ink) };
    mat.onBeforeCompile = function (sh) {
      sh.uniforms.uInk = uInk;
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nattribute vec3 aHull;\nvarying float vHull;')
        .replace('#include <project_vertex>', [
          'vec4 mvPosition = vec4( transformed, 1.0 );',
          '#ifdef USE_INSTANCING',
          ' mvPosition = instanceMatrix * mvPosition;',
          '#endif',
          'mvPosition = modelViewMatrix * mvPosition;',
          'vHull = 0.0;',
          'if ( dot( aHull, aHull ) > 0.0 ) {',
          '  vec4 hd = vec4( aHull, 0.0 );',
          '  #ifdef USE_INSTANCING',
          '   hd = instanceMatrix * hd;',
          '  #endif',
          '  hd = modelViewMatrix * hd;',
          '  float L = length( hd.xyz );',
          '  if ( L > 1e-5 ) mvPosition.xyz += hd.xyz / L * max( 0.022, 0.0032 * -mvPosition.z );',
          '  vHull = 1.0;',
          '}',
          'gl_Position = projectionMatrix * mvPosition;'].join('\n'));
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform vec3 uInk;\nvarying float vHull;')
        .replace('#include <fog_fragment>', 'if ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );\n#include <fog_fragment>');
    };
    mat.customProgramCacheKey = function () { return 'ibinksphere'; };
    return mat;
  }

  Pj.init = function (scene) {
    var n = BLAST_CAP * LOBES + BOLT_CAP * 2;
    var im = new THREE.InstancedMesh(inkSphere(), inkMaterial(), n);
    im.instanceMatrix.setUsage(THREE.DynamicDrawUsage); im.frustumCulled = false;
    for (var i = 0; i < n; i++) { im.setMatrixAt(i, ZERO); im.setColorAt(i, C_HEAD); }
    im.instanceColor.setUsage(THREE.DynamicDrawUsage);
    im.count = BLAST_CAP * LOBES; im.visible = false;
    scene.add(im);
    Pj.mesh = im;
    for (i = 0; i < BOLT_CAP; i++) Pj.bolts.push({ on: false, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, sp: 0, t: 0, dmg: 0, vs: 0, src: { x: 0, z: 0, type: 'gunner', proj: true } });
    for (i = 0; i < BLAST_CAP; i++) Pj.blasts.push({ on: false, x: 0, y: 0, z: 0, R: 3, t: 0, lobe: new Float32Array(LOBES * 4) });
    for (i = 0; i < QUEUE_CAP; i++) Pj.queue.push({ on: false, t: 0, x: 0, y: 0, z: 0, R: 3, D: 0, Dr: 0, src: { x: 0, z: 0, type: 'bomber', proj: true } });
    Pj.next = 0;
  };

  Pj.clear = function () {
    if (!Pj.mesh) return;
    var i;
    for (i = 0; i < BOLT_CAP; i++) Pj.bolts[i].on = false;
    for (i = 0; i < BLAST_CAP; i++) Pj.blasts[i].on = false;
    for (i = 0; i < QUEUE_CAP; i++) Pj.queue[i].on = false;
    for (i = 0; i < Pj.mesh.instanceMatrix.count; i++) Pj.mesh.setMatrixAt(i, ZERO);
    Pj.mesh.instanceMatrix.needsUpdate = true; Pj.mesh.count = BLAST_CAP * LOBES; Pj.mesh.visible = false; Pj.boltCount = 0;
  };

  /* vs: 0 a bolt at the player; 1 a rogue's bolt (Handy Helpers): hits robots that are not rogue, never the player;
     2 a bolt at a rogue: hits rogue robots, and the player if he is in the way */
  /* special rounds: explosive = a small blast where it lands; shock / acid = a burst of colour, and on the player a
     short damage-over-time (IB.Troops.dot) */
  function special(b, x, y, z, onPlayer) {
    var k = b.kind; if (!k || k === 'bullet') return;
    if (k === 'boom') { Pj.explode(x, y, z, 1.7, b.dmg * 0.8, 0, null); return; }
    var c = KIND[k][1].getHex();
    if (IB.Boom && IB.Boom.ready) { if (k === 'shock') IB.Boom.zap(x, y, z, 0.6, c); else IB.Boom.sparks(x, y, z, 0, 0.6, 0, 8, c); }
    if (IB.FX) IB.FX.puff(x, y, z, 5, c, 0.12, 0.4, 2.2);
    if (onPlayer && IB.Troops && IB.Troops.dot) IB.Troops.dot(k, b.src, k === 'shock' ? 3 : 2.5, k === 'shock' ? 2 : 3.5);
  }
  Pj.fire = function (x, y, z, dx, dy, dz, speed, dmg, src, vs) {
    if (!Pj.mesh) return null;
    var b = null, i, oldest = 0;
    for (i = 0; i < BOLT_CAP; i++) {
      var c = Pj.bolts[(Pj.next + i) % BOLT_CAP];
      if (!c.on) { b = c; Pj.next = (Pj.next + i + 1) % BOLT_CAP; break; }
    }
    if (!b) { for (i = 1; i < BOLT_CAP; i++) if (Pj.bolts[i].t > Pj.bolts[oldest].t) oldest = i; b = Pj.bolts[oldest]; }
    var L = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
    b.on = true; b.t = 0; b.x = x; b.y = y; b.z = z; b.sp = speed;
    b.vx = dx / L * speed; b.vy = dy / L * speed; b.vz = dz / L * speed; b.dmg = dmg;
    b.src.x = src ? src.x : x; b.src.z = src ? src.z : z; b.src.type = src ? src.type : 'gunner';
    b.vs = vs || 0; b.kind = '';
    return b;
  };

  Pj.explode = function (x, y, z, R, D, Dr, src) {
    var q = null;
    for (var i = 0; i < QUEUE_CAP; i++) if (!Pj.queue[i].on) { q = Pj.queue[i]; break; }
    if (!q) q = Pj.queue[0];
    q.on = true; q.t = 0.06; q.x = x; q.y = y; q.z = z; q.R = R; q.D = D; q.Dr = Dr;
    q.src.x = x; q.src.z = z; q.src.type = src ? src.type : 'bomber';
    return q;
  };

  function sfx(name, x, z, gain) { if (IB.Audio) IB.Audio.play(name, { pos: { x: x, z: z }, gain: gain }); }
  function covered(world, ax, ay, az, bx, by, bz) {
    var dx = bx - ax, dy = by - ay, dz = bz - az, d = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (d < 0.2) return false;
    var h = world.ray(ax, ay, az, dx / d, dy / d, dz / d, d - 0.15);
    return !!(h && h.box);
  }

  function detonate(q, ctx) {
    var x = q.x, y = q.y, z = q.z, R = q.R, p = ctx.player, world = ctx.world, FX = IB.FX, i, Boom = IB.Boom && IB.Boom.ready ? IB.Boom : null;
    sfx('boom', x, z, 1);
    if (Boom) Boom.blast(x, y, z, R, q.src.type);   // comic fireball, smoke, debris, ring, scorch, word, shake (game/boom.js)
    else blastBall(x, y, z, R, ctx);
    // player: distance to the capsule surface, cover halves it
    if (p && p.alive) {
      var cy = Math.max(p.y + PLAYER_R, Math.min(p.y + PLAYER_H - PLAYER_R, y));
      var dp = Math.sqrt((p.x - x) * (p.x - x) + (cy - y) * (cy - y) + (p.z - z) * (p.z - z));
      if (ctx.shake && !Boom) ctx.shake(dp < 6 ? 0.6 : 0.6 * Math.max(0, 1 - (dp - 6) / 8));
      var dmg = Pj.blastDamage(dp - PLAYER_R, R, q.D, covered(world, x, y, z, p.x, p.y + 1.0, p.z));
      if (dmg > 0.5 && ctx.hurt) ctx.hurt(q.src, dmg * (IB.AI && IB.AI.rangedMul || 1));   // early levels: x0.75 (ai.js setLevel)
    }
    // robots (Bombers caught in it go off next: AI.kill queues their own blast)
    var AI = IB.AI;
    if (AI && AI.robots) {
      for (i = 0; i < AI.robots.length; i++) {
        var r = AI.robots[i]; if (!r.on || r.state === 'spawn' || r.state === 'pose') continue;
        var v = AI.VIS[r.type], ry = Math.max(r.y + v.y0, Math.min(r.y + v.y1, y));
        var hx = r.x - x, hz = r.z - z, hd = Math.sqrt(hx * hx + hz * hz);
        var d = Math.sqrt(hd * hd + (ry - y) * (ry - y)) - v.radius;
        if (d >= R) continue;
        var rd = Pj.blastDamage(d, R, q.Dr, covered(world, x, y, z, r.x, ry, r.z));
        if (rd <= 0) continue;
        var kb = 7 * (1 - Math.max(0, d) / R) / (hd || 1);
        AI.damage(r, rd, { kx: hx * kb, kz: hz * kb, stagger: d < R * 0.6 }, ctx.onKill);
      }
    }
    // explosive canisters in reach light up and go off next (chains ripple)
    if (Boom) Boom.onBlast(x, y, z, R);
    if (IB.Doors) IB.Doors.blast(x, y, z, R, Math.max(q.Dr || 0, (q.D || 0) * 3));   // breakable doors in reach (robot blasts too)
  }
  // the original lobe cloud (used only when game/boom.js is not loaded)
  function blastBall(x, y, z, R, ctx) {
    var bl = null, i, FX = IB.FX;
    for (i = 0; i < BLAST_CAP; i++) if (!Pj.blasts[i].on) { bl = Pj.blasts[i]; break; }
    if (!bl) bl = Pj.blasts[0];
    bl.on = true; bl.t = 0; bl.x = x; bl.y = y; bl.z = z; bl.R = R;
    for (i = 0; i < LOBES; i++) {   // lobe 0 = core; the rest ring it, biased upward (offset xyz, size)
      var a = i * 2.4 + Math.random() * 0.8, e = 0.15 + Math.random() * 0.6, o = i ? 0.3 + Math.random() * 0.12 : 0;
      bl.lobe[i * 4] = Math.cos(a) * Math.cos(e) * o; bl.lobe[i * 4 + 1] = Math.sin(e) * o + (i ? 0 : 0.08); bl.lobe[i * 4 + 2] = Math.sin(a) * Math.cos(e) * o;
      bl.lobe[i * 4 + 3] = i ? 0.26 + Math.random() * 0.08 : 0.42;
    }
    if (FX) {
      FX.decal(x, 0.01, z, 0, 1, 0, 'splat', R * 1.05);
      FX.puff(x, y, z, 14, PAL.ink, 0.35, 1.2, 6.5, -2);
      FX.puff(x, y + 0.2, z, 8, PAL.amber, 0.3, 0.85, 5);
      FX.puff(x, y + 0.2, z, 4, PAL.paper, 0.25, 0.6, 4);
      FX.puff(x, y, z, 4, PAL.red, 0.25, 0.7, 4.5);
      FX.chunk(x, y, z, 6, 5);
    }
    if (IB.FX && IB.FX.word) IB.FX.word(['BLAM', 'KRUNCH', 'FWOOM'][(Math.random() * 3) | 0], x, y + 0.9, z, 1.7);
  }

  function hitRobot(b, nx, ny, nz, ctx) {
    var AI = IB.AI; if (!AI || !AI.robots) return false;
    for (var i = 0; i < AI.robots.length; i++) {
      var r = AI.robots[i]; if (!r.on || r.state === 'spawn' || r.state === 'pose') continue;
      if (b.vs === 1 ? r.rogue > 0 : !(r.rogue > 0)) continue;
      var v = AI.VIS[r.type];
      if (!Pj.segHitsCapsule(b.x, b.y, b.z, nx, ny, nz, r.x, r.y + v.y0 + v.radius * 0.5, r.y + v.y1 - v.radius * 0.5, r.z, v.radius, HIT_R)) continue;
      b.on = false;
      AI.damage(r, b.dmg, { kx: b.vx / b.sp * 2, kz: b.vz / b.sp * 2 }, b.vs === 1 ? ctx.onKill : null);
      if (IB.Boom) IB.Boom.boltHit(nx, ny, nz, -b.vx / b.sp, -b.vy / b.sp, -b.vz / b.sp);
      sfx('boltHit', nx, nz, 0.5);
      return true;
    }
    return false;
  }

  Pj.update = function (dt, ctx) {
    if (!Pj.mesh) return;
    Pj.ctx = ctx;
    var i, p = ctx.player, world = ctx.world, FX = IB.FX, im = Pj.mesh;
    for (i = 0; i < QUEUE_CAP; i++) { var q = Pj.queue[i]; if (q.on && (q.t -= dt) <= 0) { q.on = false; detonate(q, ctx); } }
    var hi = -1;
    for (i = 0; i < BOLT_CAP; i++) {
      var b = Pj.bolts[i];
      if (!b.on) continue;
      b.t += dt;
      if (b.t > LIFE) { b.on = false; continue; }
      var nx = b.x + b.vx * dt, ny = b.y + b.vy * dt, nz = b.z + b.vz * dt;
      // robot fights (rogues): robot capsules on the bolt's side
      if (b.vs && hitRobot(b, nx, ny, nz, ctx)) continue;
      // player capsule
      if (b.vs !== 1 && p && p.alive && Pj.segHitsCapsule(b.x, b.y, b.z, nx, ny, nz, p.x, p.y + PLAYER_R, p.y + PLAYER_H - PLAYER_R, p.z, PLAYER_R, HIT_R)) {
        b.on = false;
        if (ctx.hurt) ctx.hurt(b.src, b.dmg * (IB.AI && IB.AI.rangedMul || 1));
        special(b, nx, ny, nz, true);
        if (FX) { FX.puff(nx, ny, nz, 3, PAL.amber, 0.1, 0.3, 2.5); FX.puff(nx, ny, nz, 2, PAL.ink, 0.12, 0.35, 2); }
        if (IB.Boom) IB.Boom.boltHit(nx, ny, nz, -b.vx / b.sp, -b.vy / b.sp, -b.vz / b.sp);
        sfx('boltHit', nx, nz, 0.9);
        continue;
      }
      // world: ray along the step (no tunnelling), then a sphere test at the new spot (grazes)
      var ux = b.vx / b.sp, uy = b.vy / b.sp, uz = b.vz / b.sp, step = b.sp * dt;
      var h = world.ray(b.x, b.y, b.z, ux, uy, uz, step + HIT_R);
      var hit = false, hx = 0, hy = 0, hz = 0, nnx = 0, nny = 1, nnz = 0, hbox = null;
      if (h) { hit = true; hx = b.x + ux * h.t; hy = b.y + uy * h.t; hz = b.z + uz * h.t; nnx = h.nx; nny = h.ny; nnz = h.nz; hbox = h.box; }
      else {
        world.query(nx - HIT_R, nz - HIT_R, nx + HIT_R, nz + HIT_R, _tmp);
        for (var k = 0; k < _tmp.length; k++) {
          var bx = _tmp[k]; if (bx.noRay) continue;   // movement-only zone bounds (zones.js World.bound)
          if (Pj.sphereBox(nx, ny, nz, HIT_R, bx)) { hit = true; hx = nx; hy = ny; hz = nz; nnx = -ux; nny = -uy; nnz = -uz; hbox = bx; break; }
        }
      }
      if (hit) {
        b.on = false;
        if (FX) { FX.impact(hx, hy, hz, nnx, nny, nnz, false); FX.puff(hx + nnx * 0.05, hy + nny * 0.05, hz + nnz * 0.05, 2, PAL.amber, 0.08, 0.22, 2); }
        if (IB.Boom) { IB.Boom.boltHit(hx, hy, hz, nnx, nny, nnz); if (hbox && hbox.kind === 'canister') IB.Boom.hitCan(hbox, b.dmg * 2); }   // robot fire sets canisters off too
        if (hbox && hbox.door && IB.Doors) IB.Doors.hit(hbox, b.dmg, hx, hy, hz, nnx, nny, nnz, 'robot');   // and wears breakable doors down
        special(b, hx + nnx * 0.1, hy + nny * 0.1, hz + nnz * 0.1, false);
        sfx('boltHit', hx, hz, 0.45);
        continue;
      }
      b.x = nx; b.y = ny; b.z = nz;
      hi = i;
    }
    // ---- instances: blast b lobe l -> b * LOBES + l; bolt i -> head BASE + 2i, trail +1
    var anyBlast = false, BASE = BLAST_CAP * LOBES, ex = p ? p.x : 0, ey = p ? p.y + 1.55 : -99, ez = p ? p.z : 0;
    for (i = 0; i < BLAST_CAP; i++) {
      var bl = Pj.blasts[i], l, j0 = i * LOBES;
      if (bl.on) { bl.t += dt; if (bl.t >= BLAST_T) bl.on = false; }
      if (!bl.on) { for (l = 0; l < LOBES; l++) im.setMatrixAt(j0 + l, ZERO); continue; }
      anyBlast = true;
      var f = bl.t / BLAST_T, g = f < 0.22 ? 0.3 + 0.7 * Math.sin(f / 0.22 * Math.PI / 2) : 1 - (f - 0.22) / 0.78 * 0.9;
      for (l = 0; l < LOBES; l++) {
        var L4 = l * 4, sc = bl.R * bl.lobe[L4 + 3] * g * (l ? 1 - f * 0.35 : 1), rise = bl.R * 0.25 * f;
        var lx = bl.x + bl.lobe[L4] * bl.R, ly = bl.y + bl.lobe[L4 + 1] * bl.R + rise + sc * 0.2, lz = bl.z + bl.lobe[L4 + 2] * bl.R;
        // a lobe around the eye would paint the whole screen flat: leave it out
        if ((lx - ex) * (lx - ex) + (ly - ey) * (ly - ey) + (lz - ez) * (lz - ez) < (sc + 0.35) * (sc + 0.35)) { im.setMatrixAt(j0 + l, ZERO); continue; }
        _m.makeScale(sc, sc * 0.9, sc).setPosition(lx, ly, lz);
        im.setMatrixAt(j0 + l, _m);
        var fc = l ? f * 1.4 : f;   // outer lobes cool faster
        im.setColorAt(j0 + l, fc < 0.14 ? C_HOT : fc < 0.55 ? C_AMBER : C_RED);
      }
    }
    for (i = 0; i < BOLT_CAP; i++) {
      var o = BASE + i * 2, bb = Pj.bolts[i];
      if (!bb.on) { if (i <= Pj.boltCount) { im.setMatrixAt(o, ZERO); im.setMatrixAt(o + 1, ZERO); } continue; }
      _d.set(bb.vx, bb.vy, bb.vz).divideScalar(bb.sp);
      _q.setFromUnitVectors(_z, _d);
      // head: a hot ball, a touch long along its flight
      // bullets: a small slug and a long thin tracer; special rounds a little fatter and in their colour
      var KC = bb.kind ? KIND[bb.kind] : null, hr = KC ? (bb.kind === 'bullet' ? 0.38 : 0.6) * VIS_R : VIS_R;
      _v.set(bb.x, bb.y, bb.z); _s.set(hr, hr, hr * (KC ? 2.2 : 1.35));
      _m.compose(_v, _q, _s); im.setMatrixAt(o, _m); im.setColorAt(o, KC ? KC[0] : C_HEAD);
      // trail: stretched red streak behind it, grows out of the muzzle
      var L = Math.min(KC ? TRAIL * 1.6 : TRAIL, bb.t * bb.sp) * 0.5, tr = KC ? hr * 0.45 : VIS_R * 0.55;
      _v.set(bb.x - _d.x * (L + 0.04), bb.y - _d.y * (L + 0.04), bb.z - _d.z * (L + 0.04)); _s.set(tr, tr, Math.max(0.01, L));
      _m.compose(_v, _q, _s); im.setMatrixAt(o + 1, _m); im.setColorAt(o + 1, KC ? KC[1] : C_TRAIL);
    }
    Pj.boltCount = hi + 1;
    im.count = BASE + 2 * (hi + 1);
    im.visible = anyBlast || hi >= 0;
    im.instanceMatrix.needsUpdate = true; im.instanceColor.needsUpdate = true;
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
