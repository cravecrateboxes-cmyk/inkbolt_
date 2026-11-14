/* INKBOLT levels 35+: the Jet Trooper (robot type 'jet', registered into IB.AI before AI.init; row in data/enemies.js,
   model in blender/fam_bots.py build_jet) and the enemy rockets it shares with the Rocket Soldier (troops.js
   'rocketeer', drawn by trooperrig.js).

   Jet Trooper: an advanced robot soldier on a jet back unit, posed from rigid parts like the Soldier's fallback rig
   (hips, legs, torso, sensor-slit head, the launcher arm, the free arm, two telescoping pod arms, two pods, their lids,
   glowing seams and two jet flames). Each one rolls an element (IB.jetElement: shock / acid / boom) painted on its
   accents (key-tint material: r.tint) and carried by its rockets.
     - Outdoors it flies at its hover height (VIS flying), drifting up and down every few seconds, and orbits the
       player in its keep band like a Hawk, firing 4-round bursts from the hand launcher (r.muzzleW, placed every
       frame by its pose). Every def.airDash.every s it boost-dashes sideways (act 'dash': def.airDash.speed m/s for
       .time s, most of the speed at once, a thruster burst, a tilt and a warm exhaust trail).
     - Hover feel: a figure-8 drift (side to side, and up and down twice as fast: VIS.jet.bob), the body pitching into
       its advance and rolling into its strafes on springs about the chest core (the weak point stays put), legs
       dangling and swinging behind the motion, the free arm swaying, the gun arm following the player, flames that
       grow with the effort (climbing, braking, boosting) and flicker at idle. A hit jolts it; shot out of the air it
       spins down (VIS.jet.deathSpin, ai.js corpses).
     - Indoors (the ceiling less than def.lowCeiling m over its floor: r.low) it skims low (def.skim m) with the same
       banking, and every few seconds ground-boosts across the room (act 'dash') with a short hop (def.hopHeight m).
     - Rocket volley ("flight core"): within def.volley.near m of the player, or within .far m while at least .above m
       higher, and off its cooldown, it takes an attack token and climbs .rise m higher for .riseTime s (act 'rise'),
       holding steady; then (act 'volley') the pods snap up on their arms and the lids open, and it locks on: for .lock
       s (never under 0.8 s) a red ring closes on the player and a red beam joins its slit to him, with rising beeps.
       Then the 6 tubes fire .gap s apart at the spot it locked (with a little scatter), each pod kicking back: the
       rockets steer only for their first .homeT s, so moving beats them. Cooldown .cool s (not shortened by the level
       tempo), and it drops straight back into its dashes. Losing sight of the player for 0.5 s during the lock aborts.
   Enemy rockets (IB.EnemyRockets): pooled, drawn with the launchers' PROJ_Rocket model, an exhaust glow in the rocket's
   colour and a smoke trail; they burst on the world, near the player (or, from a rogue, near a robot) or at the end of
   their life through IB.Projectiles.explode (explosive damage to the player and robots, cover halves it). Elements:
   'shock' adds electric damage over time, 'acid' acid damage over time (IB.Troops.dot), 'boom' a bigger, wider blast.
   Test hooks: IB.EnemyRockets.stats(), IB.Jets.stats(). */
(function (IB) {
  'use strict';
  var AI = IB.AI, K = AI.K, VIS = AI.VIS, BEH = AI.BEH, PAL = IB.PAL, TAU = Math.PI * 2;
  var Jets = IB.Jets = {};
  function rnd(a, b) { return a + Math.random() * (b - a); }
  function stat(r, k, f) { var v = r.def[k]; return v === undefined ? f : v; }
  function sfx(name, at, gain, pitch) { if (IB.Audio) IB.Audio.play(name, { pos: at, gain: gain, pitch: pitch }); }
  function lateDmg() { return IB.Damage && IB.Damage.lateBoom ? IB.Damage.lateBoom().dmg : 1; }

  // ======================================================================= JET TROOPER
  function jk(n) { return K.sock('BOT_JET_' + n); }
  /* Hover feel: a figure-8 drift (side to side at W8 rad/s, up and down twice as fast: bob m, lat m), springy body
     pitch / roll (into the move, out of the hits and recoil) about the chest core, legs and the free arm swinging on
     softer springs behind the body's motion */
  var W8 = 1.45, BOB_AIR = 0.24, BOB_LOW = 0.04, LAT_AIR = 0.24, LAT_LOW = 0.05;
  var PITCH_K = 70, PITCH_C = 10, LEG_K = 28, LEG_C = 3.6, ARM_K = 36, ARM_C = 5;
  var MAX_PITCH = 0.5, MAX_ROLL = 0.55, MAX_ACC = 25;
  VIS.jet = {
    radius: 0.4, y0: 0.05, y1: 1.98, coreR: 0.1, shadow: 0.6, eye: 1.75, home: 'keep', flying: true, centre: 0, minFly: 0, climb: 2.4,
    parts: {
      Hips: { count: 1, asset: 'BOT_JET_Hips', tint: true }, Thigh: { count: 2, asset: 'BOT_JET_Thigh', tint: true },
      Shin: { count: 2, asset: 'BOT_JET_Shin', tint: true }, Torso: { count: 1, asset: 'BOT_JET_Torso', tint: true },
      Head: { count: 1, asset: 'BOT_JET_Head', tint: true }, ArmR: { count: 1, asset: 'BOT_JET_ArmR', tint: true },
      ArmL: { count: 1, asset: 'BOT_JET_ArmL', tint: true }, PodArm: { count: 2, asset: 'BOT_JET_PodArm', tint: true },
      Pod: { count: 2, asset: 'BOT_JET_Pod', tint: true }, Lid: { count: 2, asset: 'BOT_JET_Lid', tint: true },
      Light: { count: 1, light: true, asset: 'BOT_JET_Light', lightColor: slitColor },
      Seam: { count: 1, light: true, asset: 'BOT_JET_Seam', lightColor: seamColor },
      Flame: { count: 2, light: true, asset: 'BOT_JET_Flame', lightColor: flameColor }
    },
    sockets: function (v) {
      v.hips = [jk('HIP0'), jk('HIP1')]; v.waist = jk('WAIST'); v.neck = jk('NECK'); v.sh = [jk('SHOULDER0'), jk('SHOULDER1')];
      v.arm = [jk('ARM0'), jk('ARM1')]; v.noz = [jk('NOZ0'), jk('NOZ1')]; v.slit = jk('SLIT'); v.muzzle = jk('MUZZLE');
      v.podTop = jk('PODTOP')[1]; v.lid = jk('LID'); v.tubes = [jk('TUBE0'), jk('TUBE1'), jk('TUBE2')];
      var c = jk('CORE'); v.coreY = v.waist[1] + c[1]; v.coreZ = c[2];
      v.headY = v.waist[1] + v.neck[1] + 0.13; v.headR = 0.14; v.headZ = 0;   // head crit sphere
      v.thigh = 0.48;
    },
    init: function (r, opts) {
      var d = r.def;
      if (!r.tint) r.tint = new THREE.Color();
      r.elem = IB.jetElement ? IB.jetElement(Math.random()) : 'boom';
      r.tint.set((d.elementColors || {})[r.elem] || '#FF7A1E'); r.tintHex = r.tint.getHex();
      r.maxShield = r.shield = (d.shield || 0) * (AI.hpMul || 1); r.shT = 99; r.shFx = 0;
      r.hover = (d.hover || 4) + ((r.slot % 3) - 1) * 0.45;
      r.hy = r.hyT = r.hover;
      r.legDir = 1; r.pod = 0; r.lidA = 0; r.podAim = 0; r.thrust = 0.6; r.air = 1; r.legMove = 0; r.act = ''; r.low = false;
      r.vcool = rnd(2.5, 4.5); r.dashCool = rnd(1.2, 2.6); r.dashX = 0; r.dashZ = 1; r.dashT = 0; r.lostT = 0; r.beepT = 0;
      r.lockX = r.lockY = r.lockZ = 0; r.lockK = 0; r.puffT = 0; r.aim = -0.2; r.volleys = 0; r.dashes = 0; r.riseT = 0;
      // motion state: body pitch / roll springs, leg and arm swing springs, figure-8 drift, thrust burst, recoil
      r.pitch = r.pitchV = r.roll = r.rollV = 0; r.legP = r.legPV = r.legR = r.legRV = r.legK = 0; r.armP = r.armPV = r.armR = r.armRV = 0;
      r.pvf = r.pvs = r.af = r.as = 0; r.py = r.y || 0; r.vy = 0; r.f8 = null; r.steady = 1; r.burst = 0; r.pk0 = r.pk1 = 0; r.jolt = 0;
      r.altOff = 0; r.altT = rnd(1.5, 3); r.spdK = 1;
      if (!r.muzzleW) { r.muzzleW = { x: 0, y: 0, z: 0, set: false }; r.tubeW = []; for (var i = 0; i < 6; i++) r.tubeW.push({ x: 0, y: 0, z: 0 }); }
      r.muzzleW.set = false;
    },
    // a hit: the shield soaks it as a Soldier's does, and the body jolts away from it (springs settle it in ~0.4 s)
    onDamage: function (r, dmg, opts) {
      var left = VIS.soldier.onDamage(r, dmg, opts);
      jolt(r, Math.min(1, 0.35 + 5 * dmg / Math.max(1, r.maxHp + r.maxShield)) * (left > 0 ? 1 : 0.75), opts);
      return left;
    },
    noStagger: function (r) { return r.act === 'rise' || (r.act === 'volley' && (r.state === 'windup' || r.state === 'attack')); },
    // the hover bob: the up-and-down half of the figure-8 (calmer while it holds the volley steady)
    bob: function (r) { return Math.sin(r.idleT * W8 * 2 + r.slot * 3.4) * (r.hy > 0.6 ? BOB_AIR : BOB_LOW) * r.steady; },
    // shot out of the air it spins down (ai.js corpses): rad/s about its vertical, the way it was rolling
    deathSpin: function (r) { return r.y - (r.fy || 0) > 0.9 ? (r.roll >= 0 ? 1 : -1) * rnd(7, 10) : 0; },
    pose: function (r, P) {
      var v = VIS.jet, air = r.air, mv = r.legMove, ph = r.walk * 1.9, i, k, cy = v.coreY, cz = v.coreZ;
      var pit = r.pitch, rol = r.roll + r.wob;
      // the body pitches and rolls about the chest core, so the weak point stays where the game aims at it
      function base() { return P.root().t(0, cy, cz).rx(pit).rz(rol).t(0, -cy, -cz); }
      base().emit('Hips', 0);
      // legs: walking on the ground; in the air a bent-knee hang that trails and swings behind the body's motion
      for (i = 0; i < 2; i++) {
        var sd = i ? 1 : -1, s = Math.sin(ph + i * Math.PI) * r.legDir, sw = s * 0.5 * mv;
        var knee = Math.max(0, Math.cos(ph + i * Math.PI) * r.legDir) * 0.9 * mv + air * (0.75 + 0.12 * i + 0.07 * Math.sin(r.idleT * 2.1 + i * 1.3) + r.legK);
        var lp = air * (r.legP * (1 - 0.15 * i) + 0.05 * Math.sin(r.idleT * 1.6 + i * 2.1)), lr = air * r.legR * (1 + 0.2 * sd);
        base().tv(v.hips[i]).rz(sd * 0.07 * air + lr).rx(-sw - air * (0.32 + 0.1 * i) + lp).emit('Thigh', i).t(0, -v.thigh, 0).rx(knee).emit('Shin', i);
      }
      // torso, seams, head (the slit tilts with the aim and keeps nearer level than the body)
      base().tv(v.waist).emit('Torso', 0).emit('Seam', 0).push().tv(v.neck).rx(-r.aim * 0.4 - pit * 0.5).rz(-rol * 0.45).emit('Head', 0).tv(v.slit).emit('Light', 0).pop();
      // the launcher arm aims (the body's pitch and some of its roll taken out); the muzzle's world spot is kept for the shots
      P.push().tv(v.sh[0]).rx(-r.aim * 0.9 - pit).rz(-rol * 0.5).t(0, 0, -r.kick * 0.03).emit('ArmR', 0).tv(v.muzzle).pos(r.muzzleW).pop();
      r.muzzleW.set = true;
      P.push().tv(v.sh[1]).rx(-air * 0.2 + Math.sin(ph) * 0.25 * mv + air * (r.armP + 0.05 * Math.sin(r.idleT * 1.3 + 0.7))).rz(air * (0.14 + r.armR)).emit('ArmL', 0).pop();
      // pods: the arms telescope up (and splay a little), the pods pitch to the target and kick back as they fire,
      // the lids flip open
      var e = r.pod, ext = 0.35 + 0.65 * e;
      for (i = 0; i < 2; i++) {
        var sx = i ? 1 : -1;
        base().tv(v.waist).tv(v.arm[i]).rz(sx * 0.2 * e).push().s(1, ext, 1).emit('PodArm', i).pop()
          .t(0, v.podTop * ext, 0).rz(-sx * 0.2 * e).rx(-r.podAim * e).t(0, 0, -0.055 * (i ? r.pk1 : r.pk0));
        P.emit('Pod', i);
        for (k = 0; k < 3; k++) P.push().tv(v.tubes[k]).pos(r.tubeW[i * 3 + k]).pop();
        P.tv(v.lid).rx(-1.95 * r.lidA).emit('Lid', i);
      }
      // jet flames: length and width follow the effort (r.thrust), flickering; the nozzle on the outside of a roll
      // burns harder (none while it stands)
      var diff = K.clamp(r.rollV * 0.12, -0.35, 0.35);
      for (i = 0; i < 2; i++) {
        var f = Math.min(2, r.thrust * (0.86 + 0.28 * Math.random()) * (1 + (i ? diff : -diff)));
        if (f < 0.04) { P.hide('Flame', i); continue; }
        base().tv(v.waist).tv(v.noz[i]).s(0.7 + 0.42 * f, 0.35 + 1.25 * f, 0.7 + 0.42 * f).emit('Flame', i);
      }
    },
    lightColor: slitColor,
    corpse: function (v, add) {
      var M = new THREE.Matrix4(), W = v.waist;
      add('BOT_JET_Hips', M.identity());
      v.hips.forEach(function (h) { add('BOT_JET_Thigh', M.makeTranslation(h[0], h[1], h[2])); add('BOT_JET_Shin', M.makeTranslation(h[0], h[1] - v.thigh, h[2])); });
      add('BOT_JET_Torso', M.makeTranslation(W[0], W[1], W[2]));
      add('BOT_JET_Head', M.makeTranslation(W[0] + v.neck[0], W[1] + v.neck[1], W[2] + v.neck[2]));
      add('BOT_JET_ArmR', M.makeTranslation(W[0] + v.sh[0][0], W[1] + v.sh[0][1], W[2] + v.sh[0][2]));
      add('BOT_JET_ArmL', M.makeTranslation(W[0] + v.sh[1][0], W[1] + v.sh[1][1], W[2] + v.sh[1][2]));
      v.arm.forEach(function (a) { add('BOT_JET_Pod', M.makeTranslation(W[0] + a[0], W[1] + a[1] + v.podTop * 0.35, W[2] + a[2])); });
    }
  };
  function slitColor(r) {
    if (r.act === 'volley' && r.state === 'windup') return (r.st * 18 | 0) % 2 ? PAL.red : 0xFFFFFF;
    if (r.state === 'windup' && (r.st * 14 | 0) % 2 === 0) return PAL.red;
    if (r.alert > 0) return Math.sin(r.alert * 40) > 0 ? PAL.red : r.tintHex;
    return r.state === 'idle' ? 0x4A5A66 : PAL.red;
  }
  function seamColor(r) { return r.state === 'idle' ? 0x3A4048 : r.tintHex; }
  var _fc = [0xFFE6A0, 0xFFB64A, 0xFFF4D8];
  function flameColor(r) { return _fc[(Math.random() * 3) | 0]; }
  // a hit's jolt (j 0..1): the body snaps away from the hit (knockback direction, else backward), dips, flames flare
  function jolt(r, j, opts) {
    var kx = (opts && opts.kx) || 0, kz = (opts && opts.kz) || 0, sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
    var kf = kx * sy + kz * cy, ks = kx * cy - kz * sy, kl = Math.hypot(kf, ks);
    if (kl < 1e-3) { kf = -1; ks = rnd(-0.7, 0.7); kl = Math.hypot(kf, ks); }
    r.pitchV += kf / kl * 6 * j; r.rollV -= ks / kl * 5 * j;
    r.legPV -= kf / kl * 3 * j; r.jolt = Math.max(r.jolt, j);
    if (r.y - (r.fy || 0) > 0.3) r.y -= 0.05 * j;
  }

  function pitchTo(fromY, p, d) { return Math.atan2(p.y + 1.0 - fromY, Math.max(0.6, d)); }

  /* a boost-dash sideways to the player (outdoors a short, fast snap in the air; indoors a ground boost with a hop):
     the side with open floor 5 m out, a little in or out toward its keep band */
  function startDash(r, dx, dz, dist, rad, zone, air) {
    var def = r.def, AD = def.airDash || {}, side = Math.random() < 0.6 ? -r.sdir : r.sdir;
    var ux = -dz / dist * side + dx / dist * rad * 0.4, uz = dx / dist * side + dz / dist * rad * 0.4, ul = Math.hypot(ux, uz) || 1;
    ux /= ul; uz /= ul;
    var open = function (x, z) { return !zone || !IB.Zones.isOpen || IB.Zones.isOpen(zone, x, z); };
    if (!open(r.x + ux * 5, r.z + uz * 5)) {
      ux = -ux; uz = -uz;
      if (air && !open(r.x + ux * 5, r.z + uz * 5)) { r.dashCool = 0.6; return false; }
    }
    var spd = air ? AD.speed || 11 : def.dashSpeed || 10;
    r.dashX = ux; r.dashZ = uz; r.dashT = air ? AD.time || 0.36 : def.dashTime || 0.6; r.act = 'dash'; r.dashes++; r.burst = 1;
    r.sdir = (ux * -dz + uz * dx) / dist >= 0 ? 1 : -1;   // carry on orbiting the way it dashed
    r.vx = ux * spd * 0.8; r.vz = uz * spd * 0.8;          // the snap: most of the speed at once
    var ls = ux * Math.cos(r.yaw) - uz * Math.sin(r.yaw); r.rollV -= ls * 2.4; r.legRV += ls * 2;
    r.hyT = air ? r.hyT + 0.25 : def.hopHeight || 0.7;
    K.setState(r, 'attack'); K.play('rotor', r, 0.9);
    var by = air ? r.y + 1.05 : r.fy + 0.1, bx = r.x - Math.sin(r.yaw) * 0.3, bz = r.z - Math.cos(r.yaw) * 0.3;
    if (IB.FX) IB.FX.puff(bx, by, bz, air ? 5 : 6, air ? 0xFFC060 : PAL.paper, 0.1, 0.4, 2.5);
    if (air && IB.Boom && IB.Boom.muzzle) IB.Boom.muzzle(bx, r.y + 1.0, bz, 0.5);
    return true;
  }

  function thinkJet(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, T = K.tempo(), speed = def.speed || 4.6, VL = def.volley, AD = def.airDash || {}, wu = (def.windup || 0.45) * T.tellMul;
    var kd = def.keepDistance || [9, 16], mid = (kd[0] + kd[1]) / 2;
    r.low = (r.ceil - r.fy) < (def.lowCeiling || 6.5);
    r.vcool -= dt; r.dashCool -= dt;
    // hover height: its own (outdoors, drifting up and down every few s) or a low skim indoors; higher for the volley
    r.altT -= dt;
    if (r.altT <= 0) { r.altT = rnd(2.2, 4.5); r.altOff = rnd(-1.0, 0.4); }
    var hb = r.low ? def.skim || 0.22 : r.hover + r.altOff;
    if (r.act === 'rise' || (r.act === 'volley' && r.state !== 'recover')) hb = r.low ? hb + 0.5 : r.hover + Math.max(0, r.altOff) + (VL.rise || 0.9);
    if (r.act !== 'dash') r.hyT = hb;
    var rad = K.clamp((dist - mid) / 4, -1, 1), tx = -dz / dist * r.sdir, tz = dx / dist * r.sdir;
    var ox = tx * 0.85 + dx / dist * rad, oz = tz * 0.85 + dz / dist * rad;
    r.thinkT -= dt;
    if (r.thinkT <= 0 || r.bump > 0.25) { r.thinkT = 1.5 + Math.random() * 2; if (r.bump > 0.25 || Math.random() < 0.6) r.sdir = -r.sdir; r.bump = 0; r.spdK = rnd(0.8, 1.2); }
    if (p.alive) K.turnTo(r, Math.atan2(dx, dz), r.act === 'volley' || r.act === 'rise' ? 8 : 6, dt);
    var above = r.y - (p.y || 0), podY = r.y + 1.75;
    switch (r.state) {
      case 'keep': {
        // the gun arm follows the player, held a little low between bursts
        var aimT = r.seesPlayer && p.alive ? pitchTo(r.y + 1.3, p, dist) * 0.7 - 0.06 : -0.15;
        r.aim += (aimT - r.aim) * Math.min(1, dt * 3);
        if (r.act === 'rise') {
          // Flight Core: it climbs a little higher and steadies, then the pods snap open and the lock runs
          K.move(ox, oz, speed * 0.15);
          r.riseT -= dt;
          if (!p.alive || (!r.token && !K.takeToken(r))) { if (r.token) K.releaseToken(r); r.act = ''; break; }
          if (r.riseT <= 0) { r.act = 'volley'; K.setState(r, 'windup'); r.lostT = 0; r.beepT = 0; r.lockK = 0; K.play('servo', r, 0.8); }
          break;
        }
        if (!p.alive) break;
        var inV = (dist >= 4 && dist <= VL.near) || (dist <= VL.far && above >= VL.above);
        if (r.vcool <= 0 && r.seesPlayer && inV && K.takeToken(r)) {
          r.act = 'rise'; r.riseT = VL.riseTime || 0.35; r.burst = Math.max(r.burst, 0.6);
          break;
        }
        // boost-dashes: outdoors a snap sideways every few s; indoors a ground boost across the room
        if (r.dashCool <= 0 && r.seesPlayer && dist < 20 && startDash(r, dx, dz, dist, rad, zone, !r.low)) break;
        if (!r.seesPlayer && r.lost > 1.5) K.towardPlayer(r, ctx, zone, dx, dz, dist, speed);
        else K.move(ox, oz, speed * (r.low ? 0.6 : r.spdK));
        if (K.canFire(r, ctx, dist)) { r.act = 'gun'; K.setState(r, 'windup'); K.play('servo', r, 0.5); }
        break;
      }
      case 'windup':
        if (r.act === 'volley') {
          K.move(ox, oz, speed * 0.1);   // it holds steady while it locks on: readable, fair
          var lock = Math.max(0.8, Math.min(1.0, (VL.lock || 0.95) * T.tellMul));
          r.podAim += (pitchTo(podY, p, dist) - r.podAim) * Math.min(1, dt * 8);
          r.lockX = p.x; r.lockY = p.y || 0; r.lockZ = p.z; r.lockK = Math.min(1, r.st / lock);
          r.beepT -= dt;
          if (r.beepT <= 0) { r.beepT = 0.24 - 0.17 * r.lockK; sfx('lock', r, 0.9, 0.85 + 0.5 * r.lockK); }
          K.tell(r, r.lockK);
          r.lostT = r.seesPlayer ? 0 : r.lostT + dt;
          if (r.lostT > 0.5 || !p.alive) { r.act = 'abort'; K.setState(r, 'recover'); break; }
          if (r.st >= lock && r.pod > 0.85) {
            // the lock holds where the player is now (a touch of lead): the rockets go there
            r.lockX = p.x + (p.vx || 0) * 0.25; r.lockZ = p.z + (p.vz || 0) * 0.25;
            K.setState(r, 'attack'); r.shots = 0; r.shotT = 0; r.volleys++;
            sfx('lock', r, 1, 1.6);
          }
        } else {
          K.move(ox, oz, speed * 0.5);
          r.aim += (pitchTo(r.y + 1.3, p, dist) - r.aim) * Math.min(1, dt * 9);
          K.tell(r, r.st / wu);
          if (r.st >= wu) { K.setState(r, 'attack'); r.shots = 0; r.shotT = 0; }
        }
        break;
      case 'attack':
        if (r.act === 'volley') {
          K.move(ox, oz, speed * 0.2);
          r.podAim += (pitchTo(podY, p, dist) - r.podAim) * Math.min(1, dt * 4);
          r.shotT -= dt;
          if (r.shots < VL.rockets && r.shotT <= 0) { fireVolleyRocket(r, ctx, r.shots); r.shots++; r.shotT = VL.gap; }
          if (r.shots >= VL.rockets && r.shotT <= -0.25) K.setState(r, 'recover');
        } else if (r.act === 'dash') {
          K.mv.x = r.dashX; K.mv.z = r.dashZ; K.mv.s = r.low ? def.dashSpeed || 10 : AD.speed || 11;
          if (r.low && r.st > r.dashT * 0.45) r.hyT = def.skim || 0.22;   // the hop comes down: it skims out of the boost
          if (r.st >= r.dashT || (r.st > 0.12 && r.bump > 0.12)) {
            r.act = ''; r.dashCool = r.low ? rnd(2.6, 4.6) : rnd((AD.every || [1.6, 3])[0], (AD.every || [1.6, 3])[1]);
            K.setState(r, 'keep'); r.thinkT = 0;
          }
        } else {
          K.move(ox, oz, speed);
          r.aim += (pitchTo(r.y + 1.3, p, dist) - r.aim) * Math.min(1, dt * 10);
          r.shotT -= dt;
          if (r.shots < (def.bolts || 4) && r.shotT <= 0) {
            var m = muzzle(r);
            K.fireFrom(r, m, p, def.boltSpeed || 40, (def.damage || 5) * r.dmgMul, 0.25, r.shots ? 0.045 : 0.02);
            r.shots++; r.shotT = 0.11;
          }
          if (r.shots >= (def.bolts || 4) && r.shotT <= -0.05) K.setState(r, 'recover');
        }
        break;
      case 'recover': {
        if (r.token) K.releaseToken(r);
        K.move(ox, oz, speed * 0.7);
        r.aim += (-0.15 - r.aim) * Math.min(1, dt * 3);
        var rt = r.act === 'volley' || r.act === 'abort' ? 0.7 : (def.recover || 0.75);
        if (r.st >= rt) {
          if (r.act === 'volley') { r.vcool = rnd(VL.cool[0], VL.cool[1]); r.dashCool = Math.min(r.dashCool, rnd(0.2, 0.7)); }   // then straight back to agile
          else if (r.act === 'abort') r.vcool = 2.5;
          else r.cool = (1.2 + Math.random() * 1.5) * T.coolMul;
          r.act = ''; K.setState(r, 'keep'); r.thinkT = 0;
        }
        break;
      }
    }
  }
  var _mz = { x: 0, y: 0, z: 0 };
  function muzzle(r) {
    if (r.muzzleW && r.muzzleW.set) { _mz.x = r.muzzleW.x; _mz.y = r.muzzleW.y; _mz.z = r.muzzleW.z; return _mz; }
    var sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
    _mz.x = r.x + sy * 0.9 - cy * 0.3; _mz.y = r.y + 1.15; _mz.z = r.z + cy * 0.9 + sy * 0.3;
    return _mz;
  }
  // one rocket of the volley: tubes fire left / right in turn, at the locked spot with a little scatter
  var ORDER = [0, 3, 1, 4, 2, 5];
  function fireVolleyRocket(r, ctx, n) {
    var def = r.def, VL = def.volley, ti = ORDER[n % 6], t = r.tubeW[ti], sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
    var x = t.x, y = t.y, z = t.z;
    if (!r.muzzleW.set) { var sx = ti < 3 ? -1 : 1; x = r.x - cy * 0.2 * sx + sy * 0.2; y = r.y + 1.85; z = r.z + sy * 0.2 * sx + cy * 0.2; }
    var a = Math.random() * TAU, sc = VL.scatter * Math.sqrt(Math.random());
    var tx = r.lockX + Math.cos(a) * sc, tz = r.lockZ + Math.sin(a) * sc, ty = r.lockY + 0.7;
    // leave along the pod's line (forward, pitched to the target), then steer to the spot
    var cp = Math.cos(r.podAim), dx = sy * cp, dy = Math.sin(r.podAim) + 0.12, dz = cy * cp;
    var mul = r.rogue > 0 ? AI.rogueDmgMul : 1, J = IB.jetRocket(r.elem, r.dmgMul * lateDmg());
    ER.fire(r, x, y, z, dx, dy, dz, tx, ty, tz, {
      speed: VL.speed, turn: VL.turn, homeT: VL.homeT, R: J.radius, dmg: J.damage, rdmg: VL.robotDamage * (AI.hpMul || 1) * mul,
      elem: r.elem, color: r.tintHex, sc: 0.62, dot: J.dot
    });
    if (IB.FX) IB.FX.puff(x, y, z, 2, PAL.paper, 0.08, 0.25, 1.5);
    // recoil: the firing pod kicks back, the body rocks back and toward that side
    if (ti < 3) r.pk0 = 1; else r.pk1 = 1;
    r.pitchV -= 1.5; r.rollV += (ti < 3 ? 1 : -1) * 1.1;
    r.kick = 1;
  }

  // a spring toward target T (stiffness k, damping c): value r[key], its rate r[kv]
  function spring(r, key, kv, T, k, c, dt) { r[kv] += ((T - r[key]) * k - r[kv] * c) * dt; r[key] += r[kv] * dt; }

  function tickJet(r, dt) {
    r.shFx -= dt;
    if (r.maxShield > 0) { r.shT += dt; if (r.shT >= stat(r, 'shieldDelay', 5) && r.shield < r.maxShield) r.shield = Math.min(r.maxShield, r.shield + stat(r, 'shieldRate', 14) * (AI.hpMul || 1) * dt); }
    var vol = r.act === 'volley' && (r.state === 'windup' || r.state === 'attack' || (r.state === 'recover' && r.st < 0.35));
    r.pod += ((vol ? 1 : 0) - r.pod) * Math.min(1, dt * (vol ? 10 : 4));            // the pods snap up and open
    r.lidA += (((vol && r.pod > 0.5) ? 1 : 0) - r.lidA) * Math.min(1, dt * 14);
    if (!vol) r.podAim *= Math.max(0, 1 - dt * 3);
    r.pk0 = Math.max(0, r.pk0 - dt * 7); r.pk1 = Math.max(0, r.pk1 - dt * 7);
    // hover height eases to its target (a climb or a landing), never snaps
    var dh = r.hyT - r.hy, st = 2.4 * dt; r.hy += dh > st ? st : dh < -st ? -st : dh;
    // indoors a ground boost is a hop: an arc up to def.hopHeight m and back down over the boost
    if (r.act === 'dash' && r.low && r.state === 'attack') { var hop = r.fy + (r.def.hopHeight || 0.7) * Math.sin(Math.PI * Math.min(1, r.st / r.dashT)); if (r.y < hop) r.y = hop; }
    var air = K.clamp((r.y - r.fy) / 0.45, 0, 1);
    r.air += (air - r.air) * Math.min(1, dt * 8);
    // steady while it climbs for and holds the volley; the figure-8's side-to-side half (the bob is VIS.jet.bob)
    var calm = r.act === 'rise' || (r.act === 'volley' && r.state !== 'recover');
    r.steady += ((calm ? 0.3 : 1) - r.steady) * Math.min(1, dt * 3);
    var sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
    var lat = Math.sin(r.idleT * W8 + r.slot * 1.7) * (r.hy > 0.6 ? LAT_AIR : LAT_LOW) * r.steady;
    if (r.f8 !== null && r.state !== 'stagger' && r.state !== 'blinded') { r.x += cy * (lat - r.f8); r.z -= sy * (lat - r.f8); }
    r.f8 = lat;
    // local velocity (forward / to its left) and a smoothed acceleration; vertical speed
    var hs = Math.hypot(r.vx, r.vz), vf = r.vx * sy + r.vz * cy, vs = r.vx * cy - r.vz * sy, idt = 1 / Math.max(dt, 1e-4);
    r.af += (K.clamp((vf - r.pvf) * idt, -MAX_ACC, MAX_ACC) - r.af) * Math.min(1, dt * 8);
    r.as += (K.clamp((vs - r.pvs) * idt, -MAX_ACC, MAX_ACC) - r.as) * Math.min(1, dt * 8);
    r.pvf = vf; r.pvs = vs;
    r.vy += ((r.y - r.py) * idt - r.vy) * Math.min(1, dt * 6); r.py = r.y;
    // body: pitch into the advance (back when it brakes), roll into the strafe; calmer while it holds the volley
    var bk = calm ? 0.45 : 1;
    spring(r, 'pitch', 'pitchV', K.clamp(vf * 0.055 + r.af * 0.03, -0.35, 0.42) * bk, PITCH_K, PITCH_C, dt);
    spring(r, 'roll', 'rollV', K.clamp(-vs * 0.06 - r.as * 0.025, -0.5, 0.5) * bk, PITCH_K, PITCH_C, dt);
    r.pitch = K.clamp(r.pitch, -MAX_PITCH, MAX_PITCH); r.roll = K.clamp(r.roll, -MAX_ROLL, MAX_ROLL);
    // legs dangle on softer springs: dragged back by the speed, left behind by the acceleration, hanging nearer
    // plumb than the body; knees tuck as it climbs or boosts
    spring(r, 'legP', 'legPV', K.clamp(vf * 0.05 + r.af * 0.05, -0.35, 0.6) - r.pitch * 0.55, LEG_K, LEG_C, dt);
    spring(r, 'legR', 'legRV', K.clamp(-vs * 0.04 - r.as * 0.04, -0.4, 0.4) - r.roll * 0.55, LEG_K, LEG_C, dt);
    r.legK += (K.clamp(r.vy * 0.12, -0.15, 0.35) + (r.act === 'dash' ? 0.3 : 0) - r.legK) * Math.min(1, dt * 6);
    spring(r, 'armP', 'armPV', K.clamp(vf * 0.03 + r.af * 0.04, -0.3, 0.4) - r.pitch * 0.3, ARM_K, ARM_C, dt);
    spring(r, 'armR', 'armRV', K.clamp(-vs * 0.025 - r.as * 0.03, -0.25, 0.35), ARM_K, ARM_C, dt);
    // thrust follows the effort: hovering, speed, climbing, braking or boosting hard; a flicker at idle
    r.burst = Math.max(0, r.burst - dt * 2.5); r.jolt = Math.max(0, r.jolt - dt * 4);
    var flying = air > 0.05 || r.hyT > r.hy + 0.05, acc = Math.min(1, Math.hypot(r.af, r.as) / 10);
    var th = flying ? 0.5 + 0.3 * Math.min(1, hs / 5) + 0.6 * K.clamp(r.vy / 2, -0.4, 1) + 0.45 * acc + (r.act === 'dash' ? 0.7 : 0) + 0.7 * r.burst +
      0.4 * r.jolt + 0.1 * Math.sin(r.idleT * 29 + r.slot) * Math.sin(r.idleT * 7.3) : 0;
    r.thrust += (th - r.thrust) * Math.min(1, dt * 12);
    r.legDir = vf < -0.3 ? -1 : 1;
    r.legMove += (((1 - air) * Math.min(1, hs / 2.6)) - r.legMove) * Math.min(1, dt * 7);
    // exhaust: smoke puffs under the nozzles while it flies, a quick warm trail while it boosts
    r.puffT -= dt;
    if (r.thrust > 0.3 && r.puffT <= 0 && IB.FX) {
      var boost = r.act === 'dash' || r.burst > 0.5;
      r.puffT = boost ? 0.035 : 0.09;
      IB.FX.puff(r.x - sy * 0.32, r.y + 1.05, r.z - cy * 0.32, 1, boost || Math.random() < 0.35 ? 0xFFC060 : 0xE9E4F0, boost ? 0.1 : 0.08, 0.3, 0.6, 1.5);
    }
  }
  BEH.jet = { think: thinkJet, tick: tickJet };

  // ======================================================================= ENEMY ROCKETS
  var ROCKET_CAP = 48, LOCK_CAP = 10, PLAYER_R = 0.35, PLAYER_H = 1.7;
  var ER = IB.EnemyRockets = { rockets: [], fired: 0, bursts: 0, hits: 0, player: null };
  for (var ri = 0; ri < ROCKET_CAP; ri++) ER.rockets.push({ on: false, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, sp: 0, sp1: 0, t: 0, life: 4, tx: 0, ty: 0, tz: 0,
    turn: 0, homeT: 0, track: false, dmg: 0, rdmg: 0, R: 2, elem: '', color: 0xFFB21E, sc: 1, dot: null, vs: 0, puff: 0, src: { x: 0, z: 0, type: 'jet', proj: true } });
  var _tmp = [];
  /* src robot, start (x, y, z), launch direction (dx, dy, dz), target point; o: {speed, turn, homeT, track (home on
     the player instead of the point), R, dmg, rdmg, elem, color, sc, dot: {dps, time}} */
  ER.fire = function (src, x, y, z, dx, dy, dz, tx, ty, tz, o) {
    var k = null, i;
    for (i = 0; i < ROCKET_CAP; i++) if (!ER.rockets[i].on) { k = ER.rockets[i]; break; }
    if (!k) return null;
    var L = Math.hypot(dx, dy, dz) || 1, sp0 = o.speed * 0.6;
    k.on = true; k.t = 0; k.life = o.life || 4; k.x = x; k.y = y; k.z = z; k.sp = sp0; k.sp1 = o.speed;
    k.vx = dx / L * sp0; k.vy = dy / L * sp0; k.vz = dz / L * sp0;
    k.tx = tx; k.ty = ty; k.tz = tz; k.turn = o.turn || 0; k.homeT = o.homeT || 0; k.track = !!o.track;
    k.R = o.R || 2; k.dmg = src && src.rogue > 0 ? 0 : o.dmg; k.rdmg = o.rdmg || 0; k.elem = o.elem || ''; k.color = o.color === undefined ? 0xFFB21E : o.color;
    k.sc = o.sc || 1; k.dot = o.dot || null; k.vs = src && src.rogue > 0 ? 1 : 0; k.puff = 0;
    k.src.x = src ? src.x : x; k.src.z = src ? src.z : z; k.src.type = src ? src.type : 'jet';
    ER.fired++;
    sfx(o.sound || 'missile', { x: x, z: z }, 0.75, 1.1 + Math.random() * 0.2);
    if (IB.Boom && IB.Boom.muzzle) IB.Boom.muzzle(x, y, z, 0.35);
    return k;
  };
  function burst(k, ctx) {
    k.on = false; ER.bursts++;
    var Pj = IB.Projectiles; if (Pj && Pj.explode) Pj.explode(k.x, k.y, k.z, k.R, k.dmg, k.rdmg, k.src);
    var p = ctx.player, col = k.color;
    if (k.elem === 'shock' && IB.Boom && IB.Boom.ready) { IB.Boom.zap(k.x, k.y, k.z, 1.2, col); IB.Boom.sparks(k.x, k.y, k.z, 0, 0.6, 0, 8, 0x8ED2FF); }
    if (k.elem === 'acid' && IB.FX) { IB.FX.puff(k.x, k.y, k.z, 10, col, 0.14, 0.5, 2.8); IB.FX.puff(k.x, Math.max(k.y - 0.3, 0.05), k.z, 5, 0x3FAE2A, 0.2, 0.6, 1.2); }
    // element damage over time on the player when the blast reaches him (not from a rogue's rockets)
    if (k.dot && k.vs === 0 && p && p.alive && !p.robot && IB.Troops && IB.Troops.dot) {
      var cy = Math.max(p.y + PLAYER_R, Math.min(p.y + PLAYER_H - PLAYER_R, k.y));
      var d = Math.hypot(p.x - k.x, cy - k.y, p.z - k.z) - PLAYER_R;
      if (d < k.R * 0.85) { IB.Troops.dot(k.dot.kind, k.src, k.dot.dps, k.dot.time); ER.hits++; }
    }
    if (AI.hear) AI.hear(k.x, k.z, 20);
  }
  ER.update = function (dt, ctx) {
    ER.player = ctx.player;
    var p = ctx.player, world = ctx.world, Pj = IB.Projectiles, i;
    for (i = 0; i < ROCKET_CAP; i++) {
      var k = ER.rockets[i]; if (!k.on) continue;
      k.t += dt;
      if (k.t > k.life) { burst(k, ctx); continue; }
      // speed ramps up; steer toward the target (or the player) for the first homeT s, at most `turn` rad/s
      k.sp = Math.min(k.sp1, k.sp + k.sp1 * 1.6 * dt);
      var vl = Math.hypot(k.vx, k.vy, k.vz) || 1, ux = k.vx / vl, uy = k.vy / vl, uz = k.vz / vl;
      if (k.t < k.homeT && k.turn > 0) {
        var gx = k.track && p ? p.x : k.tx, gy = k.track && p ? (p.y || 0) + 1.0 : k.ty, gz = k.track && p ? p.z : k.tz;
        var wx = gx - k.x, wy = gy - k.y, wz = gz - k.z, wl = Math.hypot(wx, wy, wz) || 1;
        wx /= wl; wy /= wl; wz /= wl;
        var dot = Math.max(-1, Math.min(1, ux * wx + uy * wy + uz * wz)), ang = Math.acos(dot), mx = k.turn * dt;
        if (ang > 1e-4) {
          var f = Math.min(1, mx / ang);
          ux += (wx - ux) * f; uy += (wy - uy) * f; uz += (wz - uz) * f;
          var ul = Math.hypot(ux, uy, uz) || 1; ux /= ul; uy /= ul; uz /= ul;
        }
      } else if (k.t >= k.homeT) uy -= 0.6 * dt;   // after the guidance, a slight drop
      k.vx = ux * k.sp; k.vy = uy * k.sp; k.vz = uz * k.sp;
      var nx = k.x + k.vx * dt, ny = k.y + k.vy * dt, nz = k.z + k.vz * dt;
      // the player (proximity fuse) or, for a rogue's rocket, a robot
      if (k.vs === 0 && p && p.alive && Pj && Pj.segHitsCapsule(k.x, k.y, k.z, nx, ny, nz, p.x, (p.y || 0) + PLAYER_R, (p.y || 0) + PLAYER_H - PLAYER_R, p.z, PLAYER_R, 0.3)) {
        k.x = nx; k.y = ny; k.z = nz; burst(k, ctx); continue;
      }
      if (k.vs === 1) {
        var hitR = false;
        for (var j = 0; j < AI.robots.length && !hitR; j++) {
          var o = AI.robots[j]; if (!o.on || o.rogue > 0 || o.state === 'spawn' || o.state === 'pose') continue;
          var ov = VIS[o.type];
          if (Pj && Pj.segHitsCapsule(k.x, k.y, k.z, nx, ny, nz, o.x, o.y + ov.y0 + ov.radius * 0.5, o.y + ov.y1 - ov.radius * 0.5, o.z, ov.radius, 0.25)) hitR = true;
        }
        if (hitR) { k.x = nx; k.y = ny; k.z = nz; burst(k, ctx); continue; }
      }
      // the world: a ray along the step
      var step = k.sp * dt, h = world && world.ray ? world.ray(k.x, k.y, k.z, ux, uy, uz, step + 0.1) : null;
      var fl = world && world.floorAt ? world.floorAt(nx, nz, ny + 0.3) : 0;
      if (h || ny <= fl + 0.05) {
        if (h) { k.x += ux * Math.max(0, h.t - 0.08); k.y += uy * Math.max(0, h.t - 0.08); k.z += uz * Math.max(0, h.t - 0.08); }
        else { k.x = nx; k.y = fl + 0.1; k.z = nz; }
        burst(k, ctx); continue;
      }
      k.x = nx; k.y = ny; k.z = nz;
      // smoke trail
      k.puff -= dt;
      if (k.puff <= 0 && IB.FX) { k.puff = 0.035; IB.FX.puff(k.x - ux * 0.25 * k.sc, k.y - uy * 0.25 * k.sc, k.z - uz * 0.25 * k.sc, 1, Math.random() < 0.3 ? k.color : 0xE9E4F0, 0.06 * k.sc + 0.05, 0.22 * k.sc + 0.1, 0.25, -0.4); }
    }
  };
  ER.clear = function () { ER.rockets.forEach(function (k) { k.on = false; }); };
  ER.live = function () { var n = 0; for (var i = 0; i < ROCKET_CAP; i++) if (ER.rockets[i].on) n++; return n; };
  ER.stats = function () { return { live: ER.live(), fired: ER.fired, bursts: ER.bursts, dotHits: ER.hits }; };

  // ---- render: rocket bodies (the launchers' PROJ_Rocket), exhaust glows, lock rings and beams
  var rMesh = null, gMesh = null, ringMesh = null, beamMesh = null;
  var _m = null, _q = null, _v = null, _s = null, _d = null, _nz = null, _c = null, _up = null;
  function initRuntime(scene) {
    _m = new THREE.Matrix4(); _q = new THREE.Quaternion(); _v = new THREE.Vector3(); _s = new THREE.Vector3(); _d = new THREE.Vector3();
    _nz = new THREE.Vector3(0, 0, -1); _c = new THREE.Color(); _up = new THREE.Vector3(0, 1, 0);
    var A = IB.Assets;
    if (A.geo.PROJ_Rocket) {
      var mat = IB.Render.toonMaterial({ map: A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0, look: 'actor', surf: IB.Surface && IB.Surface.surf('weapons') });
      rMesh = new THREE.InstancedMesh(A.get('PROJ_Rocket'), mat, ROCKET_CAP);
      rMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); rMesh.frustumCulled = false; rMesh.count = 0; rMesh.name = 'enemyRockets';
      scene.add(rMesh);
    }
    gMesh = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), ROCKET_CAP);
    gMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); gMesh.frustumCulled = false; gMesh.count = 0;
    for (var i = 0; i < ROCKET_CAP; i++) gMesh.setColorAt(i, _c.set(0xffffff));
    scene.add(gMesh);
    // lock-on: a red ring closing on the player's feet and a red beam from the trooper's slit
    var rg = new THREE.RingGeometry(0.86, 1, 40); rg.rotateX(-Math.PI / 2);
    ringMesh = new THREE.InstancedMesh(rg, new THREE.MeshBasicMaterial({ color: PAL.red, transparent: true, opacity: 0.85, depthWrite: false, side: THREE.DoubleSide }), LOCK_CAP * 2);
    ringMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); ringMesh.frustumCulled = false; ringMesh.renderOrder = 2; ringMesh.count = 0; ringMesh.name = 'jetLockRings';
    scene.add(ringMesh);
    var bg = new THREE.CylinderGeometry(1, 1, 1, 6, 1, true); bg.translate(0, 0.5, 0); bg.rotateX(Math.PI / 2);   // along +Z from the origin
    beamMesh = new THREE.InstancedMesh(bg, new THREE.MeshBasicMaterial({ color: PAL.red, transparent: true, opacity: 0.55, depthWrite: false }), LOCK_CAP);
    beamMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); beamMesh.frustumCulled = false; beamMesh.renderOrder = 2; beamMesh.count = 0; beamMesh.name = 'jetLockBeams';
    scene.add(beamMesh);
  }
  var _t = 0, _eye = { x: 0, y: 0, z: 0 };
  Jets.locks = 0;
  function syncRuntime() {
    if (!gMesh) return;
    _t += 1 / 60;
    var i, n = 0;
    for (i = 0; i < ROCKET_CAP; i++) {
      var k = ER.rockets[i]; if (!k.on) continue;
      var vl = Math.hypot(k.vx, k.vy, k.vz) || 1; _d.set(k.vx / vl, k.vy / vl, k.vz / vl);
      _q.setFromUnitVectors(_nz, _d); _v.set(k.x, k.y, k.z);
      if (rMesh) { _m.compose(_v, _q, _s.set(k.sc, k.sc, k.sc)); rMesh.setMatrixAt(n, _m); }
      var fl = 0.085 * k.sc * (0.85 + Math.random() * 0.4);
      _v.set(k.x - _d.x * 0.27 * k.sc, k.y - _d.y * 0.27 * k.sc, k.z - _d.z * 0.27 * k.sc);
      _m.compose(_v, _q, _s.set(fl, fl, fl * 1.9)); gMesh.setMatrixAt(n, _m); gMesh.setColorAt(n, _c.set(k.color));
      n++;
    }
    if (rMesh) { rMesh.count = n; rMesh.visible = n > 0; rMesh.instanceMatrix.needsUpdate = true; }
    gMesh.count = n; gMesh.visible = n > 0; gMesh.instanceMatrix.needsUpdate = true; if (gMesh.instanceColor) gMesh.instanceColor.needsUpdate = true;
    // lock-on tells
    var T = AI.types.jet, rn = 0, bn = 0, p = ER.player || (IB.Game && IB.Game.player);
    if (T && p) for (i = 0; i <= T.hi; i++) {
      var r = T.slots[i]; if (!r.on || r.act !== 'volley' || r.state !== 'windup' || rn >= LOCK_CAP * 2) continue;
      var kk = r.lockK, blink = Math.sin(_t * (14 + 30 * kk)) > -0.2;
      var py = (IB.Zones && IB.Zones.world && IB.Zones.world.floorAt ? IB.Zones.world.floorAt(p.x, p.z, (p.y || 0) + 0.4) : (p.y || 0)) + 0.04;
      if (blink) {
        var R = 2.4 - 1.75 * kk;
        _v.set(p.x, py, p.z); _q.identity(); _s.set(R, 1, R); _m.compose(_v, _q, _s); ringMesh.setMatrixAt(rn++, _m);
        _s.set(R * 0.55, 1, R * 0.55); _q.setFromAxisAngle(_up, _t * 3); _m.compose(_v, _q, _s); ringMesh.setMatrixAt(rn++, _m);
      }
      // beam: slit -> chest, thin, flickering
      var v = VIS.jet, sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
      _eye.x = r.x + sy * 0.2; _eye.y = r.y + v.waist[1] + v.neck[1] + 0.12; _eye.z = r.z + cy * 0.2;
      var bx = p.x - _eye.x, by = (p.y || 0) + 1.1 - _eye.y, bz = p.z - _eye.z, bl = Math.hypot(bx, by, bz) || 1;
      if ((_t * 20 | 0) % 3) {
        _d.set(bx / bl, by / bl, bz / bl); _q.setFromUnitVectors(_v.set(0, 0, 1), _d);
        _v.set(_eye.x, _eye.y, _eye.z); var w = 0.012 + 0.01 * kk; _m.compose(_v, _q, _s.set(w, w, bl)); beamMesh.setMatrixAt(bn++, _m);
      }
    }
    Jets.locks = rn ? rn / 2 : 0;
    ringMesh.count = rn; ringMesh.visible = rn > 0; if (rn) ringMesh.instanceMatrix.needsUpdate = true;
    beamMesh.count = bn; beamMesh.visible = bn > 0; if (bn) beamMesh.instanceMatrix.needsUpdate = true;
  }

  Jets.stats = function () {
    var out = [];
    AI.robots.forEach(function (r) {
      if (!r.on || r.type !== 'jet') return;
      out.push({ slot: r.slot, state: r.state, act: r.act, elem: r.elem, tint: r.tintHex, hp: +r.hp.toFixed(1), shield: +r.shield.toFixed(1), y: +r.y.toFixed(2),
        fy: +r.fy.toFixed(2), low: r.low, pod: +r.pod.toFixed(2), lid: +r.lidA.toFixed(2), volleys: r.volleys, dashes: r.dashes, vcool: +r.vcool.toFixed(2) });
    });
    return { jets: out, rockets: ER.stats(), locks: Jets.locks };
  };

  // ---- hook into the robot runtime (after troops.js; before trooperrig.js)
  var baseInit = AI.init, baseUpdate = AI.update, baseSync = AI.sync, baseClear = AI.clear, baseDespawn = AI.despawn;
  AI.init = function (scene) { baseInit.apply(AI, arguments); initRuntime(scene); };
  AI.update = function (dt, ctx) { baseUpdate.apply(AI, arguments); ER.update(dt, ctx); };
  AI.sync = function () { baseSync.apply(AI, arguments); syncRuntime(); };
  AI.clear = function () { baseClear.apply(AI, arguments); ER.clear(); };
  AI.despawn = function () { baseDespawn.apply(AI, arguments); ER.clear(); };
})(window.IB = window.IB || {});
