/* INKBOLT weapons: table-driven hitscan guns (semi/auto/burst), spread + recoil rules (5.2),
   reload/draw/holster, quick shove, greybox viewmodel with spring kick. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var W = IB.Weapons = {};
  var D2R = Math.PI / 180;
  var FIRE_SND = { pistol: ['pip', 1], smg: ['buzz', 1], rifle: ['gun', 1.05], sniper: ['gun', 0.62], handcannon: ['gun', 0.78], twintap: ['pip', 1.12],
    whisk: ['buzz', 1.18], hornet: ['buzz', 0.9], longtom: ['gun', 0.82], brick: ['gun', 0.88], triplet: ['gun', 1.12] };
  var _dir = new THREE.Vector3(), _right = new THREE.Vector3(), _up = new THREE.Vector3(), _fwd = new THREE.Vector3();

  // ---------------- viewmodel: Blender arms rig (22 bones) + weapon meshes from fps-weapons.glb ----------------
  W.init = function (vmScene) {
    var A = IB.Assets;
    W.vmRoot = new THREE.Group();
    vmScene.add(W.vmRoot);
    W.vmMat = IB.Render.toonMaterial({ uni: IB.Render.vmOutline, map: A.palette.weapons, baked: A.BAKED.weapons });
    W.vmSkinMat = IB.Render.toonMaterial({ uni: IB.Render.vmOutline, map: A.palette.weapons, baked: A.BAKED.weapons, skinning: true });
    var rig = W.rig = A.node.ARMS_Rig;
    rig.parent && rig.parent.remove(rig);
    rig.position.set(0, 0, 0); rig.updateMatrixWorld(true);
    W.vmRoot.add(rig);
    var arms = A.node.ARMS;
    arms.material = W.vmSkinMat; arms.frustumCulled = false;
    W.bone = { Weapon: rig.getObjectByName('Weapon'), Mag: rig.getObjectByName('Mag') };
    // rest-pose world matrices (rig space) so meshes modelled in rig space can ride the bones
    W.vmRoot.updateMatrixWorld(true);
    var rigInv = rig.matrixWorld.clone().invert();
    W.restInv = {};
    ['Weapon', 'Mag'].forEach(function (b) {
      var m = new THREE.Matrix4().multiplyMatrices(rigInv, W.bone[b].matrixWorld);
      W.restInv[b] = m.clone().invert();
      W.restPos = W.restPos || {}; W.restPos[b] = new THREE.Vector3().setFromMatrixPosition(m);
    });
    W.mixer = new THREE.AnimationMixer(rig);
    W.clips = {};
    A.gltf.weapons.animations.forEach(function (c) { W.clips[c.name] = c; });
    W.models = {};
    // muzzle flash: flat comic star, unlit, parented to the active weapon's MUZZLE socket
    var star = new THREE.Shape(), pts = 10;
    for (var i = 0; i <= pts; i++) { var a = i / pts * Math.PI * 2, r = i % 2 ? 0.035 : 0.09; if (i === 0) star.moveTo(Math.cos(a) * r, Math.sin(a) * r); else star.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
    W.flash = new THREE.Mesh(new THREE.ShapeGeometry(star), new THREE.MeshBasicMaterial({ color: PAL.amber, depthTest: false }));
    var inner = new THREE.Mesh(new THREE.CircleGeometry(0.03, 8), new THREE.MeshBasicMaterial({ color: PAL.paper, depthTest: false }));
    inner.position.z = 0.001; W.flash.add(inner);
    W.flash.renderOrder = 10; inner.renderOrder = 11; W.flash.visible = false;
  };
  function model(id) {
    if (W.models[id]) return W.models[id];
    var A = IB.Assets, key = 'WPN_' + id.toUpperCase();
    if (!A.node[key]) return null;   // weapon without a Blender model yet
    var gun = A.node[key], mag = A.node[key + '_Mag'];
    [gun, mag].forEach(function (o) { if (o && o.parent) o.parent.remove(o); });
    gun.material = W.vmMat; gun.frustumCulled = false; gun.matrixAutoUpdate = false; gun.matrix.copy(W.restInv.Weapon); gun.visible = false;
    W.bone.Weapon.add(gun);
    if (mag) {
      // the Mag bone is keyed onto each weapon's MAG socket; keep the mesh in rig orientation at the bone head
      mag.material = W.vmMat; mag.frustumCulled = false; mag.matrixAutoUpdate = false;
      mag.matrix.copy(W.restInv.Mag).multiply(new THREE.Matrix4().makeTranslation(W.restPos.Mag.x, W.restPos.Mag.y, W.restPos.Mag.z));
      mag.visible = false; W.bone.Mag.add(mag);
    }
    var muzzle = gun.getObjectByName(key + '_MUZZLE');
    W.models[id] = { mesh: gun, mag: mag, muzzle: muzzle, key: id.toUpperCase() };
    return W.models[id];
  }
  function showModel(id, on) { var m = W.models[id]; if (!m) return; m.mesh.visible = on; if (m.mag) m.mag.visible = on; if (on && m.muzzle) m.muzzle.add(W.flash); }

  // ---------------- arm animation (Blender actions <WEAPON>_<Action>) ----------------
  W.anim = function (s, name, opts) {
    opts = opts || {};
    var m = s.cur && W.models[s.cur]; if (!m) return;
    var clip = W.clips[m.key + '_' + name]; if (!clip) return;
    var act = W.mixer.clipAction(clip);
    act.reset(); act.enabled = true; act.setEffectiveWeight(1);
    act.setLoop(opts.once ? THREE.LoopOnce : THREE.LoopRepeat, Infinity);
    act.clampWhenFinished = !!opts.once;
    act.timeScale = opts.timeScale || 1;
    act.play();
    if (W.action && W.action !== act) act.crossFadeFrom(W.action, opts.fade === undefined ? 0.08 : opts.fade, false);
    W.action = act; W.animName = name; W.animOnce = !!opts.once;
  };

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
    if (!model(id)) return;   // only weapons with a Blender model are playable
    s.guns[id] = { id: id, def: def, mag: mag, reserve: (def.reserve === null || def.reserve === undefined || def.reserve === Infinity) ? Infinity : def.reserve };
    if (!s.slots[def.slot]) s.slots[def.slot] = id;
  };
  W.magSize = function (s, def) { return IB.Upgrades ? IB.Upgrades.magSize(def.mag, s.fx.magLevel || 0) : def.mag; };
  W.refill = function (s) { Object.keys(s.guns).forEach(function (k) { var g = s.guns[k]; g.mag = W.magSize(s, g.def); g.reserve = (g.def.reserve == null || g.def.reserve === Infinity) ? Infinity : g.def.reserve; }); };
  W.addAmmo = function (s, frac) { Object.keys(s.guns).forEach(function (k) { var g = s.guns[k]; if (g.reserve !== Infinity) g.reserve = Math.min(g.def.reserve * 1.5, g.reserve + Math.ceil(g.def.reserve * frac)); }); };
  W.current = function (s) { return s.cur ? s.guns[s.cur] : null; };
  W.ownedSlots = function (s) { return Object.keys(s.slots).map(Number).sort(); };

  W.equip = function (s, id, instant) {
    if (!s.guns[id] || (s.cur === id && s.state !== 'holster')) return;
    if (s.cur && !instant) { s.pending = id; s.state = 'holster'; s.t = 0; W.anim(s, 'Holster', { once: true }); return; }
    Object.keys(W.models).forEach(function (k) { showModel(k, false); });
    s.cur = id; s.state = 'draw'; s.t = 0; s.burst = 0; s.shotsInRow = 0; s.recoilP *= 0.5;
    showModel(id, true);
    if (instant) { s.state = 'idle'; W.anim(s, 'Idle', { fade: 0 }); }
    else W.anim(s, 'Draw', { once: true, fade: 0 });
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
    var rc = W.clips[W.models[s.cur].key + '_Reload'];
    W.anim(s, 'Reload', { once: true, timeScale: rc ? rc.duration / s.reloadT : 1 });   // Quick Hands rescales the clip
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
        if (s.t >= 0.2) { var nid = s.pending; s.pending = null; showModel(s.cur, false); s.cur = null; W.equip(s, nid, false); }
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
    W.anim(s, 'Fire', { once: true, fade: 0.02 });
    // layered shot per class; heavier guns pitch down, light ones up (+/-4% random per shot)
    var snd = FIRE_SND[d.id] || FIRE_SND[d.cls] || ['gun', 1];
    IB.Audio && IB.Audio.play(snd[0], { pitch: snd[1] * (1 + (Math.random() * 0.08 - 0.04)) });
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
  // Viewmodel handling (modern-shooter feel): figure-8 walk bob, look-lag sway with rotation, strafe and jump
  // inertia, landing dip, sprint/slide carry (rig actions), and aim-down-sights that puts the real sights on centre.
  var DEFAULT_SIGHT = { pistol: [0, 0.055, -0.06], smg: [0, 0.075, -0.1], rifle: [0, 0.085, -0.1], sniper: [0, 0.1, -0.1] };
  W.sightOf = function (id) {
    var m = W.models[id]; if (!m) return null;
    if (!m.sight) {
      // scoped weapons aim through the eyepiece; everything else along the iron/red-dot sight line
      var sk = m.mesh.getObjectByName('WPN_' + m.key + '_SCOPE') || m.mesh.getObjectByName('WPN_' + m.key + '_SIGHT');
      m.sight = sk ? sk.position.clone() : new THREE.Vector3().fromArray(DEFAULT_SIGHT[IB.WEAPONS[id].cls] || DEFAULT_SIGHT.rifle);
    }
    return m.sight;
  };
  var ADS_DIST = { pistol: 0.34, smg: 0.22, rifle: 0.17, sniper: 0.13, shotgun: 0.2, rocket: 0.2 }, VM_SCALE = 0.85;
  W.pose = function (s, dt, player, lookDX, lookDY, headBob, t) {
    var g = W.current(s), k = Math.min(1, dt * 10);
    // look sway lags the camera; clamp so fast flicks don't throw the gun off screen
    s.swayX += ((-lookDX * 0.0007) - s.swayX) * k; s.swayY += ((lookDY * 0.0007) - s.swayY) * k;
    s.swayX = Math.max(-0.06, Math.min(0.06, s.swayX)); s.swayY = Math.max(-0.05, Math.min(0.05, s.swayY));
    // strafe + vertical inertia
    var right = player.vx * Math.cos(player.yaw) - player.vz * Math.sin(player.yaw);
    s.strafe = (s.strafe || 0) + ((right / 6) - (s.strafe || 0)) * Math.min(1, dt * 8);
    s.vert = (s.vert || 0) + ((-player.vy * 0.004) - (s.vert || 0)) * Math.min(1, dt * 10);
    s.vert = Math.max(-0.035, Math.min(0.035, s.vert));
    var a = s.aim, hip = 1 - a;
    var portrait = IB.Render.vmCam.aspect < 1;
    var x = (portrait ? 0.13 : 0.19), y = -0.13, z = -0.5, rx = 0, ry = 0.06, rz = 0;
    // walk cycle: figure-8 with roll; bigger and faster at sprint
    var hs = Math.hypot(player.vx, player.vz), moving = player.onGround && !player.sliding ? Math.min(1, hs / 6) : 0;
    var amt = (headBob ? 1 : 0.6) * moving * (player.sprinting ? 1.7 : 1) * (1 - a * 0.85), ph = player.bobT;
    x += Math.sin(ph) * 0.013 * amt; y -= Math.abs(Math.cos(ph)) * 0.011 * amt; rz += Math.sin(ph) * 0.03 * amt; ry += Math.cos(ph) * 0.012 * amt;
    // idle breathing
    y += Math.sin(t * 1.6) * 0.0028 * hip; rx += Math.sin(t * 1.6 + 1) * 0.004 * hip;
    // inertia
    x -= s.strafe * 0.012 * hip; rz -= s.strafe * 0.05; y += s.vert * hip;
    y -= player.dip * 0.45 + (player.landKick || 0) * 0.03;
    rx += s.swayY * 1.4; ry += s.swayX * 1.6;
    // slide carry (procedural until a Slide action exists for the weapon)
    var slideClip = g && W.clips[W.models[g.id].key + '_Slide'];
    s.slideK = (s.slideK || 0) + ((player.sliding ? 1 : 0) - (s.slideK || 0)) * Math.min(1, dt * 12);
    if (!slideClip) { rz += 0.5 * s.slideK; x -= 0.03 * s.slideK; y -= 0.035 * s.slideK; }
    // aim down sights: blend toward the pose that puts the sight point on the screen centre
    if (g && a > 0.001) {
      var sp = W.sightOf(g.id);
      var ax = -sp.x * VM_SCALE, ay = -sp.y * VM_SCALE, az = -(ADS_DIST[g.def.cls] || 0.25) - sp.z * VM_SCALE;
      x += (ax - x) * a; y += (ay - y) * a; z += (az - z) * a;
      rx *= hip * 0.6 + 0.4 * (1 - a); ry *= hip; rz *= hip * 0.7 + 0.3;
    }
    // arm animation: once-clips (draw, fire, reload, holster) fall back to the Idle / Sprint / Slide loop
    if (g && W.mixer) {
      var want = player.sliding && slideClip ? 'Slide' : (player.sprinting ? 'Sprint' : 'Idle');
      var busy = W.animOnce && W.action && W.action.isRunning();
      if (!busy && W.animName !== want && s.state !== 'holster') W.anim(s, want, { fade: want === 'Slide' ? 0.08 : 0.14 });
      W.mixer.update(dt);
    }
    // recoil kick (spring) on top
    z += s.kickZ * 0.02 * (1 - a * 0.5); rx += s.kickR * 0.03 * (1 - a * 0.4);
    W.vmRoot.position.set(x + s.swayX * hip, y + s.swayY * hip, z);
    W.vmRoot.rotation.set(rx, ry, rz);
    W.vmRoot.scale.setScalar(VM_SCALE);
    W.vmRoot.visible = !!g && !s.hidden;
    if (g) {
      W.flash.visible = s.flashT > 0;
      W.flash.position.set(0, 0, -0.03);
      W.flash.rotation.z = Math.random() * 6.28;
      var fs = 0.8 + Math.random() * 0.5; W.flash.scale.set(fs, fs, fs);
    }
  };
})(window.IB = window.IB || {});
