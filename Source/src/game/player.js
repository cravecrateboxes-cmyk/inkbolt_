/* INKBOLT player: movement (section 5.1), capsule vs AABB collision, camera feel. */
(function (IB) {
  'use strict';
  var MOVE = IB.MOVE = {
    walk: 6.0, sprint: 9.0, stamina: 4, staminaRefill: 2, staminaRest: 1,
    accel: 60, friction: 10, airControl: 0.35, jumpVel: 6.2, gravity: 18,
    coyote: 0.10, jumpBuffer: 0.12, stepUp: 0.35, radius: 0.35, height: 1.7, eye: 1.55,
    dipPerM: 0.04, dipMax: 0.12, dipReturn: 0.2, bobWalk: 0.012, bobSprint: 0.020,
    lookRad: 0.0022, pitchClamp: 88 * Math.PI / 180
  };

  var P = IB.Player = {};
  P.create = function () {
    return {
      x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, yaw: 0, pitch: 0,
      onGround: true, coyote: 0, jumpBuf: 0, stamina: MOVE.stamina, staminaRest: 0, sprinting: false,
      health: 100, maxHp: 100, protect: 0, alive: true, dip: 0, dipV: 0, bobT: 0, bob: 0,
      moving: false, aiming: false, speedMul: 1, jumpMul: 1, doubleJump: false, usedDouble: false,
      lastHurt: 99, knockX: 0, knockZ: 0, fallStartY: 0
    };
  };

  var _tmp = [];
  function overlapCircleRect(x, z, r, b) {
    var cx = Math.max(b.x0, Math.min(x, b.x1)), cz = Math.max(b.z0, Math.min(z, b.z1));
    var dx = x - cx, dz = z - cz;
    return dx * dx + dz * dz < r * r;
  }

  // horizontal resolve; allows step-up on low boxes when grounded
  function resolveXZ(p, world, r, H) {
    for (var it = 0; it < 3; it++) {
      var moved = false;
      world.query(p.x - r - 0.1, p.z - r - 0.1, p.x + r + 0.1, p.z + r + 0.1, _tmp);
      for (var i = 0; i < _tmp.length; i++) {
        var b = _tmp[i];
        if (b.y1 <= p.y + 0.001 || b.y0 >= p.y + H) continue;
        var cx = Math.max(b.x0, Math.min(p.x, b.x1)), cz = Math.max(b.z0, Math.min(p.z, b.z1));
        var dx = p.x - cx, dz = p.z - cz, d2 = dx * dx + dz * dz;
        if (d2 >= r * r) continue;
        var rise = b.y1 - p.y;
        if (rise > 0 && rise <= MOVE.stepUp && (p.onGround || p.coyote > 0) && canStand(p, world, b.y1, r, H)) {
          p.y = b.y1; p.vy = Math.max(p.vy, 0); moved = true; continue;
        }
        if (d2 > 1e-8) {
          var d = Math.sqrt(d2), push = r - d;
          p.x += dx / d * push; p.z += dz / d * push;
          var vn = (p.vx * dx + p.vz * dz) / d; if (vn < 0) { p.vx -= vn * dx / d; p.vz -= vn * dz / d; }
        } else { // centre inside: push out along the shortest axis
          var l = p.x - b.x0, rr = b.x1 - p.x, f = p.z - b.z0, k = b.z1 - p.z, m = Math.min(l, rr, f, k);
          if (m === l) { p.x = b.x0 - r; p.vx = Math.min(p.vx, 0); } else if (m === rr) { p.x = b.x1 + r; p.vx = Math.max(p.vx, 0); }
          else if (m === f) { p.z = b.z0 - r; p.vz = Math.min(p.vz, 0); } else { p.z = b.z1 + r; p.vz = Math.max(p.vz, 0); }
        }
        moved = true;
      }
      if (!moved) break;
    }
  }
  function canStand(p, world, y, r, H) {
    world.query(p.x - r, p.z - r, p.x + r, p.z + r, _tmp2);
    for (var i = 0; i < _tmp2.length; i++) {
      var b = _tmp2[i];
      if (b.y0 < y + H && b.y1 > y + 0.01 && overlapCircleRect(p.x, p.z, r * 0.9, b)) return false;
    }
    return true;
  }
  var _tmp2 = [];

  function resolveY(p, world, r, H, prevY) {
    var landed = false;
    if (p.y <= 0) { p.y = 0; if (p.vy < 0) p.vy = 0; landed = true; }
    world.query(p.x - r, p.z - r, p.x + r, p.z + r, _tmp);
    for (var i = 0; i < _tmp.length; i++) {
      var b = _tmp[i];
      if (!overlapCircleRect(p.x, p.z, r - 0.02, b)) continue;
      if (p.vy <= 0 && prevY >= b.y1 - 0.02 && p.y < b.y1) { p.y = b.y1; p.vy = 0; landed = true; }
      else if (p.vy > 0 && prevY + H <= b.y0 + 0.02 && p.y + H > b.y0) { p.y = b.y0 - H; p.vy = 0; }
    }
    // standing support check (walked off an edge?)
    if (!landed && p.vy <= 0) {
      if (p.y <= 0.001) landed = true;
      else for (var k = 0; k < _tmp.length; k++) {
        var bb = _tmp[k];
        if (Math.abs(p.y - bb.y1) < 0.02 && overlapCircleRect(p.x, p.z, r - 0.02, bb)) { landed = true; break; }
      }
    }
    return landed;
  }

  /* input: {mx, mz (-1..1 local move), sprint, jumpPressed, aim}, world */
  P.step = function (p, input, world, dt, fx) {
    var r = MOVE.radius, H = MOVE.height;
    // stamina / sprint
    var wantSprint = input.sprint && input.mz < -0.2 && !p.aiming;
    if (wantSprint && p.stamina > 0) { p.sprinting = true; p.stamina = Math.max(0, p.stamina - dt); p.staminaRest = 0; }
    else {
      p.sprinting = false; p.staminaRest += dt;
      if (p.staminaRest >= MOVE.staminaRest) p.stamina = Math.min(p.staminaMax || MOVE.stamina, p.stamina + (p.staminaMax || MOVE.stamina) / MOVE.staminaRefill * dt);
    }
    var speed = (p.sprinting ? MOVE.sprint : MOVE.walk) * p.speedMul * (p.aiming ? 0.7 : 1) * (p.weaponMoveMul || 1);
    // wish dir in world space (camera forward is -Z at yaw 0)
    var sy = Math.sin(p.yaw), cy = Math.cos(p.yaw);
    var mx = input.mx, mz = input.mz, ml = Math.hypot(mx, mz);
    if (ml > 1) { mx /= ml; mz /= ml; ml = 1; }
    var wx = mx * cy + mz * sy, wz = -mx * sy + mz * cy;
    var tx = wx * speed, tz = wz * speed;
    var acc = MOVE.accel * (p.onGround ? 1 : MOVE.airControl);
    if (p.onGround && ml < 0.05) {
      var f = Math.max(0, 1 - MOVE.friction * dt); p.vx *= f; p.vz *= f;
    } else {
      var dvx = tx - p.vx, dvz = tz - p.vz, dl = Math.hypot(dvx, dvz), maxDv = acc * dt;
      if (dl > maxDv) { dvx *= maxDv / dl; dvz *= maxDv / dl; }
      if (p.onGround || ml > 0.05) { p.vx += dvx; p.vz += dvz; }
    }
    // knockback impulse decays
    p.vx += p.knockX; p.vz += p.knockZ; p.knockX = p.knockZ = 0;
    p.moving = Math.hypot(p.vx, p.vz) > 0.8;
    // jump
    if (input.jumpPressed) p.jumpBuf = MOVE.jumpBuffer;
    else p.jumpBuf = Math.max(0, p.jumpBuf - dt);
    p.coyote = p.onGround ? MOVE.coyote : Math.max(0, p.coyote - dt);
    if (p.jumpBuf > 0 && (p.onGround || p.coyote > 0)) {
      p.vy = MOVE.jumpVel * Math.sqrt(p.jumpMul); p.onGround = false; p.coyote = 0; p.jumpBuf = 0; p.usedDouble = false;
      if (fx) fx.jump();
    } else if (input.jumpPressed && !p.onGround && p.doubleJump && !p.usedDouble) {
      p.vy = MOVE.jumpVel * 0.9; p.usedDouble = true; p.jumpBuf = 0;
    }
    p.vy -= MOVE.gravity * dt;
    var prevY = p.y, wasGround = p.onGround;
    if (wasGround) p.fallStartY = p.y; else p.fallStartY = Math.max(p.fallStartY, p.y);
    p.x += p.vx * dt; p.z += p.vz * dt;
    resolveXZ(p, world, r, H);
    p.y += p.vy * dt;
    p.onGround = resolveY(p, world, r, H, prevY);
    if (p.onGround && !wasGround) {
      var fell = Math.max(0, p.fallStartY - p.y);
      p.dip = Math.min(MOVE.dipMax, fell * MOVE.dipPerM + 0.02);
      if (fx) fx.land(fell);
    }
    // landing dip springs back over ~0.2 s
    p.dip = Math.max(0, p.dip - dt * (MOVE.dipMax / MOVE.dipReturn));
    // head bob
    var hs = Math.hypot(p.vx, p.vz);
    if (p.onGround && hs > 1) {
      p.bobT += dt * hs * 1.15;
      var amp = p.sprinting ? MOVE.bobSprint : MOVE.bobWalk;
      p.bob = Math.sin(p.bobT * 2) * amp;
      if (fx && Math.floor(p.bobT / Math.PI) !== p._step) { p._step = Math.floor(p.bobT / Math.PI); fx.step(p.sprinting); }
    } else p.bob *= Math.max(0, 1 - dt * 10);
    p.protect = Math.max(0, p.protect - dt);
    p.lastHurt += dt;
  };

  P.look = function (p, dx, dy, sens) {
    p.yaw -= dx * MOVE.lookRad * sens;
    p.pitch -= dy * MOVE.lookRad * sens;
    p.pitch = Math.max(-MOVE.pitchClamp, Math.min(MOVE.pitchClamp, p.pitch));
  };
  P.eyeY = function (p, headBob) { return p.y + MOVE.eye - p.dip + (headBob ? p.bob : 0); };
})(window.IB = window.IB || {});
