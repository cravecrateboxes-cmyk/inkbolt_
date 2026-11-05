/* INKBOLT weapons: table-driven hitscan guns (semi/auto/burst), spread + recoil rules (5.2),
   reload/draw/holster, quick shove, greybox viewmodel with spring kick. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var W = IB.Weapons = {};
  var D2R = Math.PI / 180;
  var _dir = new THREE.Vector3(), _right = new THREE.Vector3(), _up = new THREE.Vector3(), _fwd = new THREE.Vector3();

  // ---------------- viewmodels ----------------
  function gloves(g, aim) {
    // right hand on the grip, left hand forward on the guard; gunmetal gloves with an amber cuff stripe
    g.box(0.0, -0.11, 0.07, 0.085, 0.1, 0.11, PAL.gunmetal);
    g.box(0.0, -0.11, 0.135, 0.09, 0.03, 0.02, PAL.amber, { hull: false });
    g.box(0.02, -0.2, 0.2, 0.1, 0.1, 0.24, 0x3A3846);
    g.box(-0.035, -0.04, -0.17, 0.08, 0.075, 0.1, PAL.gunmetal);
    g.box(-0.06, -0.09, -0.06, 0.08, 0.08, 0.22, 0x3A3846);
  }
  var MODELS = {
    pip: function (g) {
      g.box(0, 0.0, -0.06, 0.06, 0.07, 0.26, PAL.gunmetal);
      g.box(0, 0.025, -0.06, 0.062, 0.02, 0.24, PAL.amber, { hull: false });
      g.box(0, -0.075, 0.03, 0.055, 0.12, 0.07, 0x3A3846);
      g.box(0, 0.045, -0.17, 0.02, 0.02, 0.02, PAL.ink, { hull: false });
      gloves(g);
      return { muzzle: [0, 0.0, -0.2], mag: [0, -0.13, 0.03] };
    },
    buzz: function (g) {
      g.box(0, 0.0, -0.08, 0.075, 0.09, 0.36, PAL.gunmetal);
      g.box(0, 0.035, -0.08, 0.077, 0.02, 0.3, PAL.amber, { hull: false });
      g.box(0, 0.0, -0.3, 0.035, 0.035, 0.12, PAL.ink);
      g.box(0, -0.08, 0.04, 0.06, 0.12, 0.07, 0x3A3846);
      g.box(0, -0.09, -0.08, 0.045, 0.16, 0.06, 0x3A3846);
      g.box(0, 0.0, 0.14, 0.05, 0.06, 0.12, PAL.gunmetal);
      gloves(g);
      return { muzzle: [0, 0.0, -0.37], mag: [0, -0.17, -0.08] };
    }
  };
  function genericModel(g, def) {
    var len = { pistol: 0.26, smg: 0.36, rifle: 0.5, sniper: 0.62, rocket: 0.6, shotgun: 0.5 }[def.cls] || 0.4;
    g.box(0, 0, -len / 3, 0.08, 0.1, len, PAL.gunmetal);
    g.box(0, 0.04, -len / 3, 0.082, 0.02, len * 0.8, PAL.amber, { hull: false });
    g.box(0, -0.09, 0.03, 0.06, 0.12, 0.07, 0x3A3846);
    gloves(g);
    return { muzzle: [0, 0, -len / 3 - len / 2 - 0.02], mag: [0, -0.15, -len / 3] };
  }

  W.init = function (vmScene) {
    W.vmRoot = new THREE.Group();
    vmScene.add(W.vmRoot);
    W.vmMat = IB.Render.toonMaterial({ uni: IB.Render.vmOutline });
    W.models = {};
    // muzzle flash: flat comic star, unlit
    var star = new THREE.Shape(), pts = 10;
    for (var i = 0; i <= pts; i++) { var a = i / pts * Math.PI * 2, r = i % 2 ? 0.035 : 0.09; if (i === 0) star.moveTo(Math.cos(a) * r, Math.sin(a) * r); else star.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
    W.flash = new THREE.Mesh(new THREE.ShapeGeometry(star), new THREE.MeshBasicMaterial({ color: PAL.amber, depthTest: false }));
    var inner = new THREE.Mesh(new THREE.CircleGeometry(0.03, 8), new THREE.MeshBasicMaterial({ color: PAL.paper, depthTest: false }));
    inner.position.z = 0.001; W.flash.add(inner);
    W.flash.renderOrder = 10; inner.renderOrder = 11; W.flash.visible = false;
    W.vmRoot.add(W.flash);
  };
  function model(id) {
    if (W.models[id]) return W.models[id];
    var def = IB.WEAPONS[id], g = new IB.Geo();
    var sock = (MODELS[id] || function (gg) { return genericModel(gg, def); })(g);
    var mesh = new THREE.Mesh(g.build(), W.vmMat);
    mesh.visible = false; W.vmRoot.add(mesh);
    W.models[id] = { mesh: mesh, sock: sock };
    return W.models[id];
  }

  // ---------------- state ----------------
  /* owned: array of weapon ids; fx: upgrade effects */
  W.create = function (owned, fx) {
    var s = { guns: {}, slots: {}, cur: null, state: 'idle', t: 0, next: 0, burst: 0, sinceShot: 9, shotsInRow: 0,
      recoilP: 0, recoilY: 0, kickZ: 0, kickZv: 0, kickR: 0, kickRv: 0, swayX: 0, swayY: 0, flashT: 0, reloadT: 0, drawT: 0,
      aim: 0, shoveT: 0, fx: fx || {}, triggerWas: false, pending: null };
    owned.forEach(function (id) { W.give(s, id); });
    return s;
  };
  W.give = function (s, id) {
    var def = IB.WEAPONS[id]; if (!def || def.fire === 'throw' || def.fire === 'melee' || def.fire === 'projectile') return;
    var mag = W.magSize(s, def);
    s.guns[id] = { id: id, def: def, mag: mag, reserve: (def.reserve === null || def.reserve === undefined || def.reserve === Infinity) ? Infinity : def.reserve };
    if (!s.slots[def.slot]) s.slots[def.slot] = id;
    model(id);
  };
  W.magSize = function (s, def) { return IB.Upgrades ? IB.Upgrades.magSize(def.mag, s.fx.magLevel || 0) : def.mag; };
  W.refill = function (s) { Object.keys(s.guns).forEach(function (k) { var g = s.guns[k]; g.mag = W.magSize(s, g.def); g.reserve = (g.def.reserve == null || g.def.reserve === Infinity) ? Infinity : g.def.reserve; }); };
  W.addAmmo = function (s, frac) { Object.keys(s.guns).forEach(function (k) { var g = s.guns[k]; if (g.reserve !== Infinity) g.reserve = Math.min(g.def.reserve * 1.5, g.reserve + Math.ceil(g.def.reserve * frac)); }); };
  W.current = function (s) { return s.cur ? s.guns[s.cur] : null; };
  W.ownedSlots = function (s) { return Object.keys(s.slots).map(Number).sort(); };

  W.equip = function (s, id, instant) {
    if (!s.guns[id] || (s.cur === id && s.state !== 'holster')) return;
    if (s.cur && !instant) { s.pending = id; s.state = 'holster'; s.t = 0; return; }
    if (s.cur) W.models[s.cur].mesh.visible = false;
    s.cur = id; s.state = 'draw'; s.t = 0; s.burst = 0; s.shotsInRow = 0; s.recoilP *= 0.5;
    W.models[id].mesh.visible = true;
    if (instant) s.state = 'idle';
    IB.Audio && IB.Audio.play('draw');
  };
  W.slot = function (s, n) { if (s.slots[n]) W.equip(s, s.slots[n]); };
  W.cycle = function (s, dir) {
    var sl = W.ownedSlots(s); if (sl.length < 2) return;
    var curSlot = s.guns[s.cur].def.slot, i = sl.indexOf(curSlot);
    W.slot(s, sl[(i + dir + sl.length) % sl.length]);
  };
  W.reload = function (s) {
    var g = W.current(s); if (!g || s.state !== 'idle') return;
    if (g.mag >= W.magSize(s, g.def) || g.reserve <= 0) return;
    s.state = 'reload'; s.t = 0; s.reloadT = g.def.reload * (s.fx.reloadMul || 1); s.burst = 0;
    IB.Audio && IB.Audio.play('magOut');
  };

  // spread cone half-angle (deg) right now
  W.spread = function (s, player) {
    var g = W.current(s); if (!g) return 0;
    var d = g.def, base = (s.aim > 0.5 ? d.spreadAim : d.spreadHip) * (s.fx.spreadMul || 1);
    if (player.moving) base *= 1.5;
    if (!player.onGround) base *= 2;
    if (s.sinceShot > 0.4) base *= 0.25;
    else base *= 1 + Math.min(6, s.shotsInRow) * 0.05;
    return base;
  };

  /* ctx: {player, cam, input:{fire, firePressed, aim}, shoot(origin, dir, def, shotIdx), dt} */
  W.update = function (s, dt, ctx) {
    var g = W.current(s), p = ctx.player, inp = ctx.input;
    s.t += dt; s.sinceShot += dt; s.next -= dt; s.flashT -= dt; s.shoveT -= dt;
    // recoil recovery: 12 deg/s, faster for small kicks so a single shot settles in ~0.18 s
    if (s.sinceShot > 0.06) {
      var rate = Math.max(12 * D2R, Math.abs(s.recoilP) / 0.18);
      s.recoilP = Math.max(0, s.recoilP - rate * dt);
      s.recoilY *= Math.max(0, 1 - dt / 0.18 * 2.5);
      if (s.sinceShot > 0.3) s.shotsInRow = 0;
    }
    // springs (stiffness 220, damping 18)
    s.kickZv += (-220 * s.kickZ - 18 * s.kickZv) * dt; s.kickZ += s.kickZv * dt;
    s.kickRv += (-220 * s.kickR - 18 * s.kickRv) * dt; s.kickR += s.kickRv * dt;
    var wantAim = inp.aim && s.state !== 'reload' && !p.sprinting;
    s.aim += ((wantAim ? 1 : 0) - s.aim) * Math.min(1, dt * 14);
    p.aiming = s.aim > 0.5;
    if (!g) return;
    p.weaponMoveMul = g.def.moveMul || 1;
    switch (s.state) {
      case 'holster':
        if (s.t >= 0.2) { var nid = s.pending; s.pending = null; W.models[s.cur].mesh.visible = false; s.cur = null; W.equip(s, nid, false); }
        return;
      case 'draw':
        if (s.t >= 0.3) s.state = 'idle';
        return;
      case 'reload':
        if (s.t >= s.reloadT * 0.55 && !s._magIn) { s._magIn = true; IB.Audio && IB.Audio.play('magIn'); }
        if (s.t >= s.reloadT) {
          s._magIn = false;
          var need = W.magSize(s, g.def) - g.mag, take = Math.min(need, g.reserve);
          g.mag += take; if (g.reserve !== Infinity) g.reserve -= take;
          s.state = 'idle'; IB.Audio && IB.Audio.play('slide');
        }
        return;
    }
    if (p.sprinting) { s.burst = 0; return; }
    var d = g.def;
    var trig = d.fire === 'auto' ? inp.fire : inp.firePressed;
    if (s.burst > 0 && s.next <= 0) { fire(s, g, ctx); s.burst--; s.next = s.burst > 0 ? (d.burstGap || 60 / d.rpm) : Math.max(0, d.cycle - (d.burst - 1) * (d.burstGap || 60 / d.rpm)); return; }
    if (trig && s.next <= 0 && s.burst === 0) {
      if (g.mag <= 0) { if (inp.firePressed) IB.Audio && IB.Audio.play('dry'); W.reload(s); return; }
      if (d.burst > 1) { s.burst = d.burst; s.next = 0; fire(s, g, ctx); s.burst--; s.next = d.burstGap || 60 / d.rpm; }
      else { fire(s, g, ctx); s.next = d.cycle || 60 / d.rpm; }
    }
  };

  function fire(s, g, ctx) {
    if (g.mag <= 0) { s.burst = 0; return; }
    var d = g.def, p = ctx.player, cam = ctx.cam;
    g.mag--;
    var spread = W.spread(s, p) * D2R;
    s.sinceShot = 0; s.shotsInRow++;
    cam.getWorldDirection(_fwd);
    _right.set(1, 0, 0).applyQuaternion(cam.quaternion); _up.set(0, 1, 0).applyQuaternion(cam.quaternion);
    for (var k = 0; k < (d.pellets || 1); k++) {
      var a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * Math.tan(spread);
      _dir.copy(_fwd).addScaledVector(_right, Math.cos(a) * r).addScaledVector(_up, Math.sin(a) * r).normalize();
      ctx.shoot(cam.position, _dir, d, k);
    }
    // recoil: climbs over the first 6 shots of auto weapons
    var climb = d.fire === 'auto' ? 0.55 + 0.45 * Math.min(1, (s.shotsInRow - 1) / 5) : 1;
    var rec = d.recoil * (s.fx.recoilMul || 1) * climb * (s.aim > 0.5 ? 0.75 : 1);
    s.recoilP += rec * D2R;
    s.recoilY += (Math.random() * 2 - 1) * (d.recoilH || 0) * (s.fx.recoilMul || 1) * D2R;
    s.kickZv += 1.6 + rec * 0.5; s.kickRv += 2.0 + rec * 1.2;
    s.flashT = 0.045;
    IB.Audio && IB.Audio.play(d.id === 'buzz' ? 'buzz' : (d.id === 'pip' ? 'pip' : 'gun'), { pitch: 1 + (Math.random() * 0.08 - 0.04) });
    if (ctx.onFire) ctx.onFire(d);
  }

  // quick shove with F when no melee weapon is equipped (20 damage)
  W.shove = function (s) {
    if (s.shoveT > 0) return false;
    s.shoveT = 0.5; s.kickZv -= 3; s.kickRv -= 2;
    return true;
  };

  // world-space muzzle point approximation for tracers
  W.muzzleWorld = function (cam, out) {
    _right.set(1, 0, 0).applyQuaternion(cam.quaternion); _up.set(0, 1, 0).applyQuaternion(cam.quaternion); cam.getWorldDirection(_fwd);
    return out.copy(cam.position).addScaledVector(_right, 0.16).addScaledVector(_up, -0.13).addScaledVector(_fwd, 0.55);
  };

  /* place viewmodel: lookDX/DY for sway, player for bob/sprint */
  W.pose = function (s, dt, player, lookDX, lookDY, headBob, t) {
    var g = W.current(s);
    s.swayX += ((-lookDX * 0.0006) - s.swayX) * Math.min(1, dt * 10);
    s.swayY += ((lookDY * 0.0006) - s.swayY) * Math.min(1, dt * 10);
    s.swayX = Math.max(-0.05, Math.min(0.05, s.swayX)); s.swayY = Math.max(-0.05, Math.min(0.05, s.swayY));
    var a = s.aim;
    var portrait = IB.Render.vmCam.aspect < 1;
    var x = (portrait ? 0.13 : 0.19) * (1 - a), y = -0.13 + 0.035 * a, z = -0.5 + 0.08 * a, rx = 0, ry = 0.06 * (1 - a), rz = 0;
    // idle breathe + walk bob
    var hs = Math.hypot(player.vx, player.vz);
    var bobAmt = (headBob ? 1 : 0.5) * Math.min(1, hs / 6) * (1 - a * 0.8);
    x += Math.sin(player.bobT) * 0.012 * bobAmt; y += Math.abs(Math.cos(player.bobT)) * 0.012 * bobAmt;
    y += Math.sin(t * 1.6) * 0.003 * (1 - a);
    if (player.sprinting) { x -= 0.04; y -= 0.06; rx -= 0.35; ry += 0.55; }
    if (s.state === 'draw') { var k = 1 - s.t / 0.3; y -= k * k * 0.25; rx -= k * 0.8; }
    if (s.state === 'holster') { var h = s.t / 0.2; y -= h * 0.25; rx -= h * 0.8; }
    if (s.state === 'reload') {
      var rk = s.t / s.reloadT, dip = Math.sin(Math.min(1, rk) * Math.PI);
      y -= dip * 0.06; rz += dip * 0.5; rx += dip * 0.25;
    }
    y -= player.dip * 0.4;
    z += s.kickZ * 0.02; rx += s.kickR * 0.03;
    W.vmRoot.position.set(x + s.swayX, y + s.swayY, z);
    W.vmRoot.rotation.set(rx, ry, rz);
    W.vmRoot.scale.setScalar(0.85);
    W.vmRoot.visible = !!g && !s.hidden;
    if (g) {
      var m = W.models[g.id], mz = m.sock.muzzle;
      W.flash.visible = s.flashT > 0;
      W.flash.position.set(mz[0], mz[1], mz[2] - 0.03);
      W.flash.rotation.z = Math.random() * 6.28;
      var fs = 0.8 + Math.random() * 0.5; W.flash.scale.set(fs, fs, fs);
    }
  };
})(window.IB = window.IB || {});
