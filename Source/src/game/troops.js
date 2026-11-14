/* INKBOLT troops: the Soldier and the Blade Bot (robot types registered into IB.AI before AI.init; rows in
   data/enemies.js, models in blender/fam_bots.py). Health, shields and damage scale with the campaign level through
   the same multipliers as every robot (AI.hpMul / r.dmgMul from core/damage.js, tempo for windups and cooldowns).

   Soldier: a trooper in SWAT / military kit, drawn as a skinned, animated character by trooperrig.js (the rigid parts
     below are its fallback). Fires carbine rounds: fast tracer bullets, now and then an explosive, shock or acid round
     (def.specialRounds) that also hurts over time on a hit (Tr.dot). Shield pool (r.shield / r.maxShield, the health bar's shield row) soaks damage
     first, recharges after def.shieldDelay; keeps 7-15 m, strafes and takes cover (Gunner planner), fires 4-bolt
     bursts from its rifle, throws up to 3 frag grenades (arc, bounce, blinking fuse, red ring, Projectiles.explode),
     rifle-butts the player inside def.meleeRange after a pull-back tell. Rigid parts: hips + legs face the way it
     walks, the torso turns to aim, both arms and the rifle pitch together about the shoulder line, the left arm
     throws. Armour variants: plate colour per instance (AI key-tint material) x 2 torsos x 3 helmets.
   Blade Bot: a hover saucer whose hub arm wields a katana or a Voltaxe (r.weaponId 'katana' | 'eaxe'). Slow patrol;
     seeing the player it homes in, spins up (whine, flashing tell), dashes spinning at ~19 rev/s with a smear arc,
     cuts on contact (the axe also shocks: damage over time on the player), overshoots and stays dizzy (takes extra
     damage). Standing next to it triggers a spin slash in place.
   Levels 20+: the Robot Trooper ('mech') and the Grenadier share the Soldier's brain and rig (a Grenadier fires 40 mm
     grenades from its launcher: launchShell, impact bursts, a red ring at the landing spot); the Hawk is a flyer with
     its own parts and brain (thinkHawk), one special-round type per Hawk painted on its accents.
   Weapon drops: player kills call IB.WeaponDrops.roll(r) (Soldier) / IB.WeaponDrops.melee(r, r.weaponId) if present.
   Also here: the enemy grenade pool (rendered + simulated through AI.update / AI.sync / AI.clear wrappers), the
   blade smear arcs and the player's shock from the Voltaxe. Test hooks: IB.Troops.stats(), IB.Troops.grenades. */
(function (IB) {
  'use strict';
  var AI = IB.AI, K = AI.K, VIS = AI.VIS, BEH = AI.BEH, PAL = IB.PAL, TAU = Math.PI * 2, G = 16, KCHAIN = 16;
  var Tr = IB.Troops = { grenades: [], smears: [], shock: { left: 0, tick: 0, dps: 0, src: { x: 0, z: 0, type: 'blader', proj: true } },
    stats: null, nadeCap: 12, liveNadeMax: 2 };
  var _tmp = [], _c = null;
  function stat(r, k, f) { var v = r.def[k]; return v === undefined ? f : v; }
  function rnd(a, b) { return a + Math.random() * (b - a); }
  function sfx(name, at, gain, pitch) { if (IB.Audio) IB.Audio.play(name, { pos: at, gain: gain, pitch: pitch }); }
  function ease(k) { k = k < 0 ? 0 : k > 1 ? 1 : k; return k * k * (3 - 2 * k); }

  // ======================================================================= SOLDIER
  function sk(n) { return K.sock('BOT_SOLDIER_' + n); }
  VIS.soldier = {
    radius: 0.36, y0: 0.05, y1: 1.86, coreR: 0.11, shadow: 0.55, eye: 1.7, home: 'keep',
    parts: { Hips: { count: 1, asset: 'BOT_SOLDIER_Hips', tint: true }, Thigh: { count: 2, asset: 'BOT_SOLDIER_Thigh', tint: true },
      Shin: { count: 2, asset: 'BOT_SOLDIER_Shin', tint: true },
      TorsoA: { count: 1, asset: 'BOT_SOLDIER_TorsoA', tint: true, opt: true }, TorsoB: { count: 1, asset: 'BOT_SOLDIER_TorsoB', tint: true, opt: true },
      HelmA: { count: 1, asset: 'BOT_SOLDIER_HelmA', tint: true, opt: true }, HelmB: { count: 1, asset: 'BOT_SOLDIER_HelmB', tint: true, opt: true },
      HelmC: { count: 1, asset: 'BOT_SOLDIER_HelmC', tint: true, opt: true },
      ArmR: { count: 1, asset: 'BOT_SOLDIER_ArmR', tint: true }, ArmL: { count: 1, asset: 'BOT_SOLDIER_ArmL', tint: true },
      Nade: { count: 1, asset: 'BOT_SOLDIER_Nade', opt: true }, Visor: { count: 1, light: true, asset: 'BOT_SOLDIER_Visor' } },
    sockets: function (v) {
      v.hips = [sk('HIP0'), sk('HIP1')]; v.waist = sk('WAIST'); v.neck = sk('NECK'); v.sh = [sk('SHOULDER0'), sk('SHOULDER1')];
      v.visor = sk('VISOR'); v.muzzle = sk('MUZZLE'); v.handL = sk('HANDL');
      var c = sk('CORE'); v.coreY = v.waist[1] + c[1]; v.coreZ = c[2];
    },
    init: function (r, opts) {
      var d = r.def, A = d.armour || ['#EEF1F5'];
      if (!r.tint) r.tint = new THREE.Color();
      r.armour = (Math.random() * A.length) | 0; r.tint.set(A[r.armour]); r.tintHex = r.tint.getHex();
      r.torso = (d.torsos || ['A'])[(Math.random() * (d.torsos || ['A']).length) | 0];
      r.helm = (d.helmets || ['A'])[(Math.random() * (d.helmets || ['A']).length) | 0];
      r.maxShield = r.shield = (d.shield || 0) * (AI.hpMul || 1); r.shT = 99; r.shFx = 0;
      r.nades = d.grenades !== undefined ? d.grenades : 3; r.ncool = rnd(2.5, 5); r.mcool = 0; r.act = '';
      // overwhelm control: about 40 % of soldiers are poorer shots (core/damage.js sloppyAim / SLOPPY)
      AI.soldierSeq = (AI.soldierSeq || 0) + 1;
      r.sloppy = !opts || !opts.pose ? !!(IB.Damage && IB.Damage.sloppyAim && IB.Damage.sloppyAim(AI.soldierSeq)) : false;
      r.legRel = 0; r.legDir = 1; r.legMove = 0; r.aim = -0.25; r.rigPitch = 0; r.rigPush = 0; r.throwL = 0; r.holdNade = false; r.bit = false; r.twist = 0;
    },
    onDamage: function (r, dmg) {
      if (!(r.maxShield > 0)) return dmg;
      r.shT = 0;   // any hit restarts the recharge delay
      if (r.shield <= 0) return dmg;
      var ab = Math.min(r.shield, dmg), y = r.y + 1.2;
      r.shield -= ab;
      if (IB.Boom && IB.Boom.ready && r.shFx <= 0) { r.shFx = 0.08; IB.Boom.zap(r.x, y, r.z, 0.45, 0x8ED2FF); }
      if (r.shield <= 0.001) {   // shield breaks: a blue burst and a crackle
        r.shield = 0;
        if (IB.Boom && IB.Boom.ready) { IB.Boom.zap(r.x, y, r.z, 1.3, 0x5FC2FF); IB.Boom.sparks(r.x, y, r.z, 0, 0.5, 0, 10, 0x8ED2FF); }
        sfx('boltHit', r, 0.9, 0.6);
      }
      return dmg - ab;
    },
    pose: function (r, P) {
      var v = VIS.soldier, ph = r.walk * 1.9, mv = r.legMove, bob = Math.abs(Math.sin(ph)) * 0.035 * mv - r.crouch * 0.06, i;
      // hips and legs face the way it walks (legRel off the torso yaw)
      P.root().ry(r.legRel).t(0, bob, 0).emit('Hips', 0);
      for (i = 0; i < 2; i++) {
        var s = Math.sin(ph + i * Math.PI) * r.legDir, sw = s * 0.5 * mv, knee = Math.max(0, Math.cos(ph + i * Math.PI) * r.legDir) * 0.95 * mv + r.crouch * 0.5;
        P.push().tv(v.hips[i]).rx(-sw - r.crouch * 0.35).emit('Thigh', i).t(0, -0.43, 0).rx(knee).emit('Shin', i).pop();
      }
      // torso turns to aim; arms + rifle pitch about the shoulder line
      P.root().t(0, bob, 0).tv(v.waist).ry(r.twist).rx(r.crouch * 0.12);
      P.emit(r.torso === 'B' ? 'TorsoB' : 'TorsoA', 0).hide(r.torso === 'B' ? 'TorsoA' : 'TorsoB', 0);
      var hn = 'Helm' + r.helm;
      P.push().tv(v.neck).rx(-r.aim * 0.4).emit(hn, 0);
      if (hn !== 'HelmA') P.hide('HelmA', 0); if (hn !== 'HelmB') P.hide('HelmB', 0); if (hn !== 'HelmC') P.hide('HelmC', 0);
      P.tv(v.visor).emit('Visor', 0).pop();
      var th = -r.aim + r.rigPitch;
      P.push().tv(v.sh[0]).rx(th).t(0, 0, r.rigPush - r.kick * 0.04).emit('ArmR', 0).pop();
      P.push().tv(v.sh[1]).rx(th + r.throwL).t(0, 0, r.rigPush).emit('ArmL', 0);
      if (r.holdNade) P.tv(v.handL).ry(r.st * 6).emit('Nade', 0); else P.hide('Nade', 0);
      P.pop();
    },
    lightColor: function (r) {
      if (r.state === 'windup' && (r.st * 14 | 0) % 2 === 0) return PAL.red;
      if (r.alert > 0) return Math.sin(r.alert * 40) > 0 ? PAL.red : 0x7FE8FF;
      return r.state === 'idle' ? 0x3C7C8C : 0x7FE8FF;
    },
    // rest pose for the ink silhouette
    corpse: function (v, add) {
      var M = new THREE.Matrix4(), W = v.waist;
      add('BOT_SOLDIER_Hips', M.identity());
      v.hips.forEach(function (h) { add('BOT_SOLDIER_Thigh', M.makeTranslation(h[0], h[1], h[2])); add('BOT_SOLDIER_Shin', M.makeTranslation(h[0], h[1] - 0.43, h[2])); });
      add('BOT_SOLDIER_TorsoA', M.makeTranslation(W[0], W[1], W[2]));
      add('BOT_SOLDIER_HelmA', M.makeTranslation(W[0] + v.neck[0], W[1] + v.neck[1], W[2] + v.neck[2]));
      add('BOT_SOLDIER_ArmR', M.makeTranslation(W[0] + v.sh[0][0], W[1] + v.sh[0][1], W[2] + v.sh[0][2]));
      add('BOT_SOLDIER_ArmL', M.makeTranslation(W[0] + v.sh[1][0], W[1] + v.sh[1][1], W[2] + v.sh[1][2]));
    },
    // the torso aims at the target while the legs walk the way it moves (backwards when backing off)
    face: function (r, dt, P, dx, dz, dist, hs, fwd, mode) {
      var busy = r.state === 'windup' || r.state === 'attack';
      if (r.state !== 'stagger' && r.state !== 'blinded') {
        if (P.alive && !mode && r.state !== 'idle' && (r.seesPlayer || busy || r.lost < 1.5)) K.turnTo(r, Math.atan2(dx, dz), busy ? 9 : 6, dt);
        else if (hs > 0.3) K.turnTo(r, Math.atan2(r.vx, r.vz), 6, dt);
      }
      if (hs > 0.3) {
        var rel = K.wrapAngle(Math.atan2(r.vx, r.vz) - r.yaw), dir = 1;
        if (Math.abs(rel) > Math.PI * 0.6) { rel = K.wrapAngle(rel + Math.PI); dir = -1; }
        r.legRel += (K.clamp(rel, -1.15, 1.15) - r.legRel) * Math.min(1, dt * 8); r.legDir = dir;
      } else r.legRel *= Math.max(0, 1 - dt * 4);
      r.legMove += ((hs > 0.3 ? Math.min(1, hs / 2.6) : 0) - r.legMove) * Math.min(1, dt * 7);
      if (!busy) r.crouch = Math.max(0, r.crouch - dt * 3);
      r.twist += ((r.state === 'attack' && r.act === 'melee' ? -0.35 : 0) - r.twist) * Math.min(1, dt * 12);
    }
  };

  /* Robot Trooper ('mech') and Grenadier: drawn by trooperrig.js on the Soldier's rig (TROOPER_MECH: a robot body;
     the Soldier's own mesh with its carbine hidden + TROOPER_GL: the grenade launcher). They share the Soldier's
     brain (thinkSoldier: a Grenadier fires its launcher where a Soldier fires a burst, a Robot Trooper throws nothing)
     and its rigid fallback parts, hit volumes and death. */
  VIS.mech = Object.assign({}, VIS.soldier);
  VIS.grenadier = Object.assign({}, VIS.soldier);
  // Rocket Soldier (levels 35+): the Soldier's body and brain, a Murmur or a Hothead on its shoulder (trooperrig.js)
  VIS.rocketeer = Object.assign({}, VIS.soldier, {
    init: function (r, opts) { VIS.soldier.init(r, opts); r.launcher = IB.rocketeerLauncher ? IB.rocketeerLauncher(Math.random()) : 'hothead'; r.nades = 0; }
  });

  // world position of a point given in a shoulder's arm space (aim rig rotated by th, pushed along its z)
  var _w = { x: 0, y: 0, z: 0 };
  function armPoint(r, shi, pt, th, push) {
    var v = VIS.soldier, s = v.sh[shi], c = Math.cos(th), sn = Math.sin(th), pz = pt[2] + push;
    var lx = s[0] + pt[0], ly = v.waist[1] + s[1] + (pt[1] * c - pz * sn), lz = s[2] + (pt[1] * sn + pz * c);
    var sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
    _w.x = r.x + lx * cy + lz * sy; _w.y = r.y + ly; _w.z = r.z - lx * sy + lz * cy;
    return _w;
  }
  function aimAt(r, p) { return Math.atan2(p.y + 1.15 - (r.y + 1.44), Math.max(0.6, Math.hypot(p.x - r.x, p.z - r.z))); }
  function liveNades() { var n = 0; for (var i = 0; i < Tr.grenades.length; i++) if (Tr.grenades[i].on) n++; return n; }

  function thinkSoldier(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, speed = def.speed || 3.2, T = K.tempo(), lv = K.offLevel(r, p, zone), GL = !!def.launcher, RL = !!def.rockets;
    var wuF = (def.windup || 0.45) * T.tellMul, wuN = (def.grenadeWindup || 0.6) * T.tellMul, wuM = (def.meleeWindup || 0.4) * T.tellMul;
    var k;
    r.ncool -= dt; r.mcool -= dt;
    if (r.state !== 'windup' || r.act !== 'melee') { r.rigPitch *= Math.max(0, 1 - dt * 8); r.rigPush *= Math.max(0, 1 - dt * 8); }
    switch (r.state) {
      case 'keep': {
        r.aim += ((r.seesPlayer ? aimAt(r, p) : -0.3) - r.aim) * Math.min(1, dt * 5);
        r.throwL *= Math.max(0, 1 - dt * 6);
        if (!p.alive) break;
        r.thinkT -= dt;
        if (r.thinkT <= 0 || (r.mode === 'strafe' && r.bump > 0.25)) { if (r.bump > 0.25) { r.sdir = -r.sdir; r.bump = 0; } K.planKeep(r, ctx, zone, dist); }
        K.keepMove(r, ctx, zone, dx, dz, dist, speed);
        var gr = def.grenadeRange || [6, 19];
        if (r.seesPlayer && !lv && dist < (def.meleeRange || 2.2) && r.mcool <= 0 && (K.takeToken(r) || dist < 1.6)) {
          r.act = 'melee'; K.setState(r, 'windup'); K.play('servo', r, 0.6);
        } else if (r.seesPlayer && r.nades > 0 && r.ncool <= 0 && dist > gr[0] && dist < gr[1] && liveNades() < Tr.liveNadeMax && K.takeToken(r)) {
          r.act = 'nade'; K.setState(r, 'windup'); r.holdNade = true; K.play('clank', r, 0.8);
        } else if ((!(GL || RL) || dist > def.minRange) && K.canFire(r, ctx, dist)) { r.act = RL ? 'rl' : GL ? 'gl' : 'fire'; K.setState(r, 'windup'); K.play(GL || RL ? 'clank' : 'servo', r, 0.45); }
        break;
      }
      case 'windup':
        if (r.act === 'melee') {
          K.turnTo(r, Math.atan2(dx, dz), 12, dt);
          k = ease(r.st / wuM); r.rigPitch = 0.55 * k; r.rigPush = -0.14 * k; r.crouch = 0.4 * k;
          K.tell(r, r.st / wuM);
          if (dist > 1.4) K.move(dx, dz, speed * 0.8);   // step in
          if (r.st >= wuM) { K.setState(r, 'attack'); r.bit = false; K.play('shove', r, 0.9); }
        } else if (r.act === 'nade') {
          K.turnTo(r, Math.atan2(dx, dz), 8, dt);
          r.aim += (aimAt(r, p) - r.aim) * Math.min(1, dt * 6);
          r.throwL = -2.5 * ease(r.st / wuN);
          K.tell(r, r.st / wuN);
          if (r.st >= wuN) { throwNade(r, p); K.setState(r, 'attack'); }
        } else if (r.act === 'rl') {   // Rocket Soldier: shoulders the launcher (trooperrig.js r.shoulder), aims, a long tell
          K.turnTo(r, Math.atan2(dx, dz), 8, dt);
          r.aim += (aimAt(r, p) + (r.launcher === 'murmur' ? 0.2 : 0.02) - r.aim) * Math.min(1, dt * 7);
          K.tell(r, r.st / wuF);
          K.move(-dz * r.sdir, dx * r.sdir, speed * 0.15);
          if (r.st >= wuF) { K.setState(r, 'attack'); r.shots = 0; r.shotT = 0; }
        } else if (r.act === 'gl') {   // Grenadier: brings the launcher up, aims high, a longer tell
          K.turnTo(r, Math.atan2(dx, dz), 9, dt);
          r.aim += (aimAt(r, p) + 0.12 - r.aim) * Math.min(1, dt * 7);
          K.tell(r, r.st / wuF);
          K.move(-dz * r.sdir, dx * r.sdir, speed * 0.2);
          if (r.st >= wuF) { launchShell(r, p); K.setState(r, 'attack'); }
        } else {
          r.aim += (aimAt(r, p) - r.aim) * Math.min(1, dt * 9);
          K.tell(r, r.st / wuF);
          K.move(-dz * r.sdir, dx * r.sdir, speed * 0.3);   // keeps sidestepping while it brings the rifle up
          if (r.st >= wuF) { K.setState(r, 'attack'); r.shots = 0; r.shotT = 0; }
        }
        break;
      case 'attack':
        if (r.act === 'melee') {
          k = Math.min(1, r.st / 0.1); r.rigPitch = 0.55 - 1.5 * k; r.rigPush = -0.14 + 0.5 * k; r.crouch = 0.4 * (1 - k);
          if (!r.bit && r.st >= 0.06) {
            r.bit = true;
            var fx = Math.sin(r.yaw), fz = Math.cos(r.yaw), facing = (dx * fx + dz * fz) / dist;
            if (dist < (def.meleeRange || 2.2) + 0.45 && facing > 0.4 && Math.abs(p.y - r.fy) < 1.3) {
              ctx.hurt(r, (def.meleeDamage || 14) * r.dmgMul);
              if (!p.robot) { var kb = def.meleeKnock || 6; p.knockX = (p.knockX || 0) + dx / dist * kb; p.knockZ = (p.knockZ || 0) + dz / dist * kb; }
              if (IB.Boom && IB.Boom.ready) { IB.Boom.word('WHAM!', p.x, p.y + 1.9, p.z, 1.1); IB.Boom.sparks(r.x + dx / dist * 1.0, r.y + 1.3, r.z + dz / dist * 1.0, -dx / dist, 0.3, -dz / dist, 6); }
              K.play('clank', r, 1);
            }
          }
          if (r.st >= 0.22) K.setState(r, 'recover');
        } else if (r.act === 'nade') {
          r.throwL += (0.5 - r.throwL) * Math.min(1, dt * 22);   // follow-through
          if (r.st >= 0.25) K.setState(r, 'recover');
        } else if (r.act === 'rl') {
          var RLd = def[r.launcher] || def.hothead;
          K.turnTo(r, Math.atan2(dx, dz), 6, dt);
          r.aim += (aimAt(r, p) + (r.launcher === 'murmur' ? 0.2 : 0.02) - r.aim) * Math.min(1, dt * 6);
          r.shotT -= dt;
          if (r.shots < RLd.rockets && r.shotT <= 0) { fireRocket(r, p, RLd); r.shots++; r.shotT = RLd.gap; }
          if (r.shots >= RLd.rockets && r.shotT <= -0.3) K.setState(r, 'recover');
        } else if (r.act === 'gl') {
          r.kick *= Math.max(0, 1 - dt * 5);
          if (r.st >= 0.3) K.setState(r, 'recover');
        } else {
          r.aim += (aimAt(r, p) - r.aim) * Math.min(1, dt * 6);
          K.move(-dz * r.sdir, dx * r.sdir, speed * 0.3);
          r.shotT -= dt;
          if (r.shots < (def.bolts || 4) && r.shotT <= 0) {
            var m = r.muzzleW || armPoint(r, 0, VIS.soldier.muzzle, -r.aim + r.rigPitch, r.rigPush);   // the carbine's muzzle (trooperrig.js)
            fireRound(r, m, p, def.boltSpeed || 58, (def.damage || 6) * r.dmgMul, 0.4, r.shots ? 0.04 : 0.01);
            r.shots++; r.shotT = 0.1;
          }
          if (r.shots >= (def.bolts || 4) && r.shotT <= -0.08) K.setState(r, 'recover');
        }
        break;
      case 'recover':
        if (r.token) K.releaseToken(r);
        r.throwL *= Math.max(0, 1 - dt * 6);
        r.aim += ((r.seesPlayer ? aimAt(r, p) : -0.3) - r.aim) * Math.min(1, dt * 3);
        var rt = r.act === 'melee' ? 0.6 : r.act === 'nade' ? 0.45 : (def.recover || 0.7);
        if (r.st >= rt) {
          K.setState(r, 'keep'); r.thinkT = 0;
          if (r.act === 'melee') r.mcool = 1.4 + Math.random() * 0.8;
          else if (r.act === 'nade') { var ge = def.grenadeEvery || [6, 10]; r.ncool = rnd(ge[0], ge[1]) * T.coolMul * (IB.Damage && IB.Damage.lateBoom ? IB.Damage.lateBoom() : { dmg: 1, cool: 1 }).cool; r.cool = Math.max(r.cool, 0.6); }
          else if (r.act === 'rl') { var rf = (def[r.launcher] || def.hothead).fireEvery; r.cool = rnd(rf[0], rf[1]); }   // flat: slower than every other soldier
          else if (r.act === 'gl') { var fe = def.fireEvery || [3.4, 5]; r.cool = rnd(fe[0], fe[1]) * T.coolMul * (IB.Damage && IB.Damage.lateBoom ? IB.Damage.lateBoom() : { dmg: 1, cool: 1 }).cool; }
          else r.cool = (1.1 + Math.random() * 1.3) * T.coolMul;
          r.act = '';
        }
        break;
    }
  }
  function tickSoldier(r, dt) {
    r.shFx -= dt;
    if (r.maxShield > 0) { r.shT += dt; if (r.shT >= stat(r, 'shieldDelay', 3.5) && r.shield < r.maxShield) r.shield = Math.min(r.maxShield, r.shield + stat(r, 'shieldRate', 24) * (AI.hpMul || 1) * dt); }
    if (r.state !== 'windup' || r.act !== 'nade') r.holdNade = false;
  }
  BEH.soldier = { think: thinkSoldier, tick: tickSoldier };
  BEH.mech = BEH.grenadier = BEH.rocketeer = BEH.soldier;

  /* Rocket Soldier (levels 35+): a rocket from its launcher's muzzle (trooperrig.js r.muzzleW). Hothead: a heavy rocket
     straight at the player's feet / chest with a little lead; Murmur: a small missile that pops up and steers at the
     player for homeT s at most `turn` rad/s (strafing shakes it). Damage eases off like every explosive on levels 20+. */
  function fireRocket(r, p, L) {
    var ER = IB.EnemyRockets; if (!ER) return;
    var m = r.muzzleW || armPoint(r, 0, VIS.soldier.muzzle, -r.aim + r.rigPitch, r.rigPush);
    var lb = IB.Damage && IB.Damage.lateBoom ? IB.Damage.lateBoom().dmg : 1, mul = r.rogue > 0 ? AI.rogueDmgMul : 1;
    var o = { speed: L.speed, turn: L.turn, homeT: L.homeT, R: L.radius, dmg: L.damage * r.dmgMul * lb, rdmg: L.robotDamage * (AI.hpMul || 1) * mul, sc: L.scale || 1 };
    var sy = Math.sin(r.yaw), cy = Math.cos(r.yaw), SL = r.sloppy ? 1.8 : 1, dx, dy, dz, tx, ty, tz;
    if (r.launcher === 'murmur') {
      var side = (r.shots % 2 ? 1 : -1) * rnd(0.15, 0.4);
      dx = sy + cy * side; dy = 0.55; dz = cy - sy * side;
      tx = p.x; ty = (p.y || 0) + 1.0; tz = p.z;
      o.track = true; o.color = 0xFFD86A; o.sound = 'missile';
    } else {
      var d = Math.hypot(p.x - m.x, p.z - m.z), t = d / L.speed;
      tx = p.x + (p.vx || 0) * t * 0.4 + rnd(-0.5, 0.5) * SL; tz = p.z + (p.vz || 0) * t * 0.4 + rnd(-0.5, 0.5) * SL; ty = (p.y || 0) + 0.7;
      dx = tx - m.x; dy = ty - m.y; dz = tz - m.z;
      o.color = 0xFFB21E; o.sound = 'rocket';
    }
    ER.fire(r, m.x, m.y, m.z, dx, dy, dz, tx, ty, tz, o);
    if (IB.FX) { IB.FX.puff(m.x, m.y, m.z, 4, PAL.paper, 0.1, 0.35, 1.6); IB.FX.puff(m.x - sy * 0.9, m.y + 0.05, m.z - cy * 0.9, 3, 0xE9E4F0, 0.12, 0.45, 1.2); }   // back blast
    r.kick = 1; Tr.rockets = (Tr.rockets || 0) + 1;
  }

  /* a carbine round: a fast tracer bullet; now and then (def.specialRounds odds) an explosive, shock or acid round,
     which also hurts over time on a hit (projectiles.js special(), Tr.dot) */
  function fireRound(r, m, p, speed, dmg, lead, spread, kind0) {
    var T = K.tempo(), tx = p.x, ty = p.y + 1.15, tz = p.z;
    var dx = tx - m.x, dy = ty - m.y, dz = tz - m.z, d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
    lead = (lead || 0) + T.leadAdd; spread = (spread || 0) * T.aimMul;
    var SL = r.sloppy && !p.robot && IB.Damage && IB.Damage.SLOPPY;   // a poorer shot: wider spread, less lead
    if (SL) { spread = spread * SL.spreadMul + SL.spreadAdd; lead *= SL.leadMul; }
    if (lead) { var tt = d / speed; tx += (p.vx || 0) * tt * lead; tz += (p.vz || 0) * tt * lead; dx = tx - m.x; dz = tz - m.z; d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1; }
    dx /= d; dy /= d; dz /= d;
    if (spread) { dx += (Math.random() - 0.5) * spread; dy += (Math.random() - 0.5) * spread * 0.6; dz += (Math.random() - 0.5) * spread; }
    var Pj = IB.Projectiles, b = Pj && Pj.fire ? Pj.fire(m.x, m.y, m.z, dx, dy, dz, speed, r.rogue > 0 ? dmg * AI.rogueDmgMul : dmg, r, r.rogue > 0 ? 1 : p.robot ? 2 : 0) : null;
    if (b) {
      var sp = r.def.specialRounds || {}, x = Math.random(), acc = 0, kind = kind0 || 'bullet';
      if (!kind0) { var bc = (IB.Damage && IB.Damage.lateBoom ? IB.Damage.lateBoom() : { dmg: 1, cool: 1 }).cool; for (var k in sp) { acc += k === 'boom' ? sp[k] / bc : sp[k]; if (x < acc) { kind = k; break; } } }
      b.kind = kind;
      if (kind === 'boom' && !(r.rogue > 0) && IB.Damage && IB.Damage.lateBoom) b.dmg *= IB.Damage.lateBoom().dmg;   // levels 20+: explosive rounds hit a little softer
    }
    if (IB.Boom) IB.Boom.muzzle(m.x, m.y, m.z, 0.3);
    if (IB.FX) IB.FX.puff(m.x, m.y, m.z, 1, PAL.paper, 0.06, 0.18, 1.4);
    sfx('gun', r, 0.45, 1.25 + Math.random() * 0.15);
    r.kick = 1;
  }
  // damage over time on the player from special rounds: 'shock' (shares the Voltaxe's shock) or 'acid'
  Tr.acid = { left: 0, tick: 0, dps: 0, src: { x: 0, z: 0, type: 'soldier', proj: true } };
  Tr.dot = function (kind, src, dps, time) {
    var S = kind === 'acid' ? Tr.acid : Tr.shock;
    S.dps = Math.max(S.left > 0 ? S.dps : 0, dps * (src && src.type ? 1 : 1)); S.left = Math.max(S.left, time); if (S.tick <= 0) S.tick = 0.4;
    if (src) { S.src.x = src.x; S.src.z = src.z; }
  };

  // ---------------- enemy grenades ----------------
  var NR = 0.07;
  function throwNade(r, p) {
    if (r.nades <= 0) return;
    var g = null, i;
    for (i = 0; i < Tr.grenades.length; i++) if (!Tr.grenades[i].on) { g = Tr.grenades[i]; break; }
    r.holdNade = false;
    if (!g) return;
    r.nades--;
    var h = r.handLW ? { x: r.handLW.x, y: r.handLW.y + 0.1, z: r.handLW.z } : armPoint(r, 1, VIS.soldier.handL, -r.aim + r.throwL, 0);
    var dx = p.x - h.x, dz = p.z - h.z, d = Math.hypot(dx, dz);
    var t = K.clamp(0.55 + d * 0.05, 0.7, 1.4), lead = 0.5;
    // aim a little short: the grenade skids on to the player's feet (plus a little scatter)
    var sh = Math.min(0.9, d * 0.1) / (d || 1);
    var tx = p.x - dx * sh + (p.vx || 0) * t * lead + rnd(-0.6, 0.6), tz = p.z - dz * sh + (p.vz || 0) * t * lead + rnd(-0.6, 0.6), ty = (p.y || 0) + NR;
    var def = r.def;
    g.on = true; g.t = 0; g.x = h.x; g.y = h.y; g.z = h.z; g.rest = false; g.spin = rnd(8, 13); g.rx = 0; g.rz = 0; g.impact = false;
    g.vx = (tx - h.x) / t; g.vz = (tz - h.z) / t; g.vy = (ty - h.y + 0.5 * G * t * t) / t;
    g.fuse = (def.grenadeFuse || 2.1) * Math.max(0.85, K.tempo().tellMul);
    g.R = def.grenadeRadius || 3.4; g.dmg = r.rogue > 0 ? 0 : (def.grenadeDamage || 30) * r.dmgMul * (IB.Damage && IB.Damage.lateBoom ? IB.Damage.lateBoom() : { dmg: 1, cool: 1 }).dmg;
    g.rdmg = (def.grenadeRobotDamage || 20) * (AI.hpMul || 1) * (r.rogue > 0 ? AI.rogueDmgMul : 1);
    g.src.x = r.x; g.src.z = r.z; g.src.type = r.type;
    K.play('shove', r, 0.7);
  }
  /* Grenadier: a 40 mm grenade on a high arc from the launcher's muzzle at the player's feet (a little lead and
     scatter). It bursts on impact (floor, a wall, the player), or shellFuse s after coming to rest; while it flies a red
     ring marks where it will land (g.lx / g.lz). */
  function launchShell(r, p) {
    var g = null, i;
    for (i = 0; i < Tr.grenades.length; i++) if (!Tr.grenades[i].on) { g = Tr.grenades[i]; break; }
    if (!g) return;
    var def = r.def, m = r.muzzleW || armPoint(r, 0, VIS.soldier.muzzle, -r.aim + r.rigPitch, r.rigPush);
    var dx = p.x - m.x, dz = p.z - m.z, d = Math.hypot(dx, dz);
    var t = K.clamp(0.6 + d * 0.032, 0.75, 1.35);
    var SL = r.sloppy ? 1.6 : 1, tx = p.x + (p.vx || 0) * t * 0.45 + rnd(-0.7, 0.7) * SL, tz = p.z + (p.vz || 0) * t * 0.45 + rnd(-0.7, 0.7) * SL;
    var W = IB.Zones && IB.Zones.world, ty = (W && W.floorAt ? W.floorAt(tx, tz, (p.y || 0) + 0.4) : (p.y || 0)) + NR;
    g.on = true; g.t = 0; g.x = m.x; g.y = m.y; g.z = m.z; g.rest = false; g.spin = rnd(14, 20); g.rx = 0; g.rz = 0;
    g.vx = (tx - m.x) / t; g.vz = (tz - m.z) / t; g.vy = (ty - m.y + 0.5 * G * t * t) / t;
    g.impact = true; g.lx = tx; g.ly = ty; g.lz = tz; g.fuse = t + 2.5; g.shellFuse = def.shellFuse || 0.45;
    g.R = def.shellRadius || 3; g.dmg = r.rogue > 0 ? 0 : (def.shellDamage || 26) * r.dmgMul * (IB.Damage && IB.Damage.lateBoom ? IB.Damage.lateBoom() : { dmg: 1, cool: 1 }).dmg;
    g.rdmg = (def.shellRobotDamage || 14) * (AI.hpMul || 1) * (r.rogue > 0 ? AI.rogueDmgMul : 1);
    g.src.x = r.x; g.src.z = r.z; g.src.type = r.type;
    r.kick = 1; Tr.shells = (Tr.shells || 0) + 1;
    if (IB.Boom) IB.Boom.muzzle(m.x, m.y, m.z, 0.55);
    if (IB.FX) { IB.FX.puff(m.x, m.y, m.z, 4, PAL.paper, 0.1, 0.35, 1.6); IB.FX.puff(m.x, m.y, m.z, 2, PAL.ink, 0.08, 0.3, 1); }
    sfx('gun', r, 0.7, 0.55);
  }
  function burst(g) { g.t = g.fuse; }
  function bounce(g, nx, ny, nz) {
    if (g.impact && g.t > 0.06) { burst(g); return; }   // a launcher grenade bursts on impact
    var e = 0.3, vn = g.vx * nx + g.vy * ny + g.vz * nz;
    if (vn >= 0) return;
    g.vx -= (1 + e) * vn * nx; g.vy -= (1 + e) * vn * ny; g.vz -= (1 + e) * vn * nz;
    var f = ny > 0.5 ? 0.45 : 0.6; g.vx *= f; g.vz *= f; if (ny < 0.5) g.vy *= f;   // heavy can: it thuds and skids, not bowls
    g.spin *= 0.6;
    if (Math.abs(vn) > 1.5) sfx('step', g, Math.min(1, Math.abs(vn) / 6), 1.7);
  }
  function updateNades(dt, world, P) {
    for (var i = 0; i < Tr.grenades.length; i++) {
      var g = Tr.grenades[i]; if (!g.on) continue;
      g.t += dt;
      if (g.impact) {
        if (P && P.alive && !g.rest && Math.hypot(g.x - P.x, g.z - P.z) < 0.5 && g.y > (P.y || 0) - 0.1 && g.y < (P.y || 0) + 1.8) burst(g);   // hits the player
        if (g.rest && g.t < g.fuse - g.shellFuse) g.fuse = g.t + g.shellFuse;
        if (IB.FX && !g.rest && Math.random() < 0.6) IB.FX.puff(g.x, g.y, g.z, 1, PAL.paper, 0.05, 0.16, 0.5);
      }
      if (g.t >= g.fuse) { g.on = false; g.impact = false; if (IB.Projectiles && IB.Projectiles.explode) IB.Projectiles.explode(g.x, Math.max(0.3, g.y), g.z, g.R, g.dmg, g.rdmg, g.src); if (AI.hear) AI.hear(g.x, g.z, 25); continue; }
      if (g.rest || !world) continue;
      g.vy -= G * dt; g.x += g.vx * dt; g.y += g.vy * dt; g.z += g.vz * dt;
      var fl = world.floorAt ? world.floorAt(g.x, g.z, g.y + 0.3) : 0;
      if (g.y < fl + NR) { g.y = fl + NR; bounce(g, 0, 1, 0); }
      world.query(g.x - NR, g.z - NR, g.x + NR, g.z + NR, _tmp);
      for (var k = 0; k < _tmp.length; k++) {
        var b = _tmp[k];
        if (g.x + NR <= b.x0 || g.x - NR >= b.x1 || g.z + NR <= b.z0 || g.z - NR >= b.z1 || g.y + NR <= b.y0 || g.y - NR >= b.y1) continue;
        var px0 = g.x + NR - b.x0, px1 = b.x1 - (g.x - NR), pz0 = g.z + NR - b.z0, pz1 = b.z1 - (g.z - NR), py0 = g.y + NR - b.y0, py1 = b.y1 - (g.y - NR);
        var m = Math.min(px0, px1, pz0, pz1, py0, py1);
        if (m === py1) { g.y = b.y1 + NR; bounce(g, 0, 1, 0); } else if (m === py0) { g.y = b.y0 - NR; bounce(g, 0, -1, 0); }
        else if (m === px0) { g.x = b.x0 - NR; bounce(g, -1, 0, 0); } else if (m === px1) { g.x = b.x1 + NR; bounce(g, 1, 0, 0); }
        else if (m === pz0) { g.z = b.z0 - NR; bounce(g, 0, 0, -1); } else { g.z = b.z1 + NR; bounce(g, 0, 0, 1); }
      }
      if (g.y <= fl + NR + 0.01 && Math.abs(g.vy) < 0.6 && Math.hypot(g.vx, g.vz) < 0.25) { g.rest = true; g.vx = g.vy = g.vz = 0; }
      g.rx += g.spin * dt; g.rz += g.spin * 0.6 * dt;
    }
  }

  // ======================================================================= BLADE BOT
  function bk(n) { return K.sock('BOT_BLADER_' + n); }
  VIS.blader = {
    radius: 0.48, y0: 0.15, y1: 0.95, coreR: 0.16, shadow: 0.6, eye: 0.6, home: 'stalk',
    parts: { Body: { count: 1, asset: 'BOT_BLADER_Body' }, Hub: { count: 1, asset: 'BOT_BLADER_Hub' },
      Katana: { count: 1, asset: 'BOT_BLADER_Katana', opt: true }, Axe: { count: 1, asset: 'BOT_BLADER_Axe', opt: true },
      Fundo: { count: 1, asset: 'BOT_BLADER_Fundo', opt: true }, Kusari: { count: 1, asset: 'BOT_BLADER_Kusari', opt: true },
      Chain: { count: KCHAIN, asset: 'BOT_BLADER_Chain', opt: true },
      Light: { count: 1, light: true, asset: 'BOT_BLADER_Light' } },
    sockets: function (v) {
      var c = bk('CORE'); v.coreY = c[1]; v.coreZ = c[2];
      v.hub = bk('HUB'); v.grip = bk('GRIP'); v.light = bk('LIGHT'); v.chain = bk('CHAIN');
    },
    init: function (r) {
      var W = r.def.weapons || ['katana', 'eaxe'];
      r.weaponId = IB.bladerWeapon ? IB.bladerWeapon(Math.random()) : W[(Math.random() * W.length) | 0];   // katana, Voltaxe or kusarigama
      r.reach = r.weaponId === 'eaxe' ? 1.32 : 1.5;
      kusariInit(r);
      r.hub = Math.random() * TAU; r.spinV = 3; r.bspin = 0; r.bspinV = 0; r.act = ''; r.hitT = 0; r.lean = 0; r.dashX = 0; r.dashZ = 1;
      r.swishT = 0; r.starT = 0;
    },
    onDamage: function (r, dmg) { return r.state === 'recover' && r.act === 'dash' ? dmg * stat(r, 'dizzyMul', 1.35) : dmg; },
    noStagger: function (r) { return r.state === 'windup' || r.state === 'attack'; },
    onPlayerKill: function (r) { if (IB.WeaponDrops && IB.WeaponDrops.melee) IB.WeaponDrops.melee(r, r.weaponId); },
    pose: function (r, P) {
      var v = VIS.blader, bob = Math.sin(r.idleT * 2.6 + r.slot) * 0.03 - r.crouch * 0.08;
      P.root().t(0, bob, 0).ry(r.bspin).rx(r.lean).rz(r.wob).emit('Body', 0);
      P.push().tv(v.light).emit('Light', 0).pop();
      if (r.weaponId === 'kusari') { poseKusari(r, P, v); return; }
      var wn = r.weaponId === 'eaxe' ? 'Axe' : 'Katana';
      P.tv(v.hub).ry(r.hub).emit('Hub', 0).tv(v.grip).rx(0.45).emit(wn, 0).hide(wn === 'Axe' ? 'Katana' : 'Axe', 0);
      P.hide('Fundo', 0).hide('Kusari', 0); for (var ci = 0; ci < KCHAIN; ci++) P.hide('Chain', ci);
    },
    lightColor: function (r) {
      if (r.state === 'windup' || r.state === 'attack') return (r.st * 16 | 0) % 2 ? PAL.red : PAL.paper;
      if (r.state === 'recover' && r.act === 'dash') return (r.st * 6 | 0) % 2 ? PAL.amber : 0x7A6A4A;
      return K.lightDefault(r);
    },
    corpse: function (v, add) {
      var M = new THREE.Matrix4();
      add('BOT_BLADER_Body', M.identity());
      add('BOT_BLADER_Hub', M.makeTranslation(v.hub[0], v.hub[1], v.hub[2]));
    },
    face: function (r, dt, P, dx, dz, dist, hs, fwd, mode) {
      var dashing = r.state === 'attack';
      if (!dashing && r.state !== 'stagger' && r.state !== 'blinded') {
        if (P.alive && !mode && r.state !== 'idle' && r.seesPlayer) K.turnTo(r, Math.atan2(dx, dz), 5, dt);
        else if (hs > 0.3) K.turnTo(r, Math.atan2(r.vx, r.vz), 5, dt);
      }
      // body spin: whirls during the dash and the spin slash, settles back facing forward after
      if (dashing && r.weaponId !== 'kusari') r.bspinV += (26 - r.bspinV) * Math.min(1, dt * 6); else r.bspinV *= Math.max(0, 1 - dt * 3);   // the kusarigama swings the chain, not the body
      r.bspin += r.bspinV * dt;
      if (r.bspinV < 2) r.bspin = K.wrapAngle(r.bspin) * Math.max(0, 1 - dt * 3);
      r.lean += ((dashing && r.act === 'dash' ? 0.22 : r.state === 'windup' ? -0.12 : 0) - r.lean) * Math.min(1, dt * 6);
      if (r.state !== 'windup') r.crouch = Math.max(0, r.crouch - dt * 3);
      if (r.state !== 'recover' && r.state !== 'stagger') r.wob *= Math.max(0, 1 - dt * 6);
    }
  };

  function bladeHit(r, ctx, dmg, dirx, dirz) {
    var p = ctx.player, dx = p.x - r.x, dz = p.z - r.z, d = Math.hypot(dx, dz) || 0.01;
    if (d > r.reach + 0.35 || Math.abs((p.y + 0.9) - (r.y + 0.84)) > 1.15) return false;
    ctx.hurt(r, dmg);
    if (!p.robot) {
      var kx = dirx !== undefined ? dirx * 0.6 + dx / d * 0.8 : dx / d, kz = dirz !== undefined ? dirz * 0.6 + dz / d * 0.8 : dz / d;
      p.knockX = (p.knockX || 0) + kx * 6.5; p.knockZ = (p.knockZ || 0) + kz * 6.5;
      if (r.weaponId === 'eaxe') {   // Voltaxe: shock on the player (damage over time)
        var S = Tr.shock; S.left = stat(r, 'shockTime', 2); S.dps = stat(r, 'shockDps', 4) * r.dmgMul; S.src.x = r.x; S.src.z = r.z; if (S.tick <= 0) S.tick = 0.4;
      }
    }
    var hx = r.x + dx / d * Math.min(d, r.reach), hz = r.z + dz / d * Math.min(d, r.reach), hy = r.y + 0.9;
    if (IB.Boom && IB.Boom.ready) {
      IB.Boom.sparks(hx, hy, hz, -dx / d, 0.3, -dz / d, 10, r.weaponId === 'eaxe' ? 0x8ED2FF : undefined);
      if (r.weaponId === 'eaxe') IB.Boom.zap(hx, hy, hz, 0.8);
      IB.Boom.word(r.weaponId === 'eaxe' ? 'ZZAP!' : 'KRAK!', p.x, p.y + 2.0, p.z, 1.1);
    }
    sfx('slash', r, 1);
    return true;
  }

  function thinkBlader(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, T = K.tempo(), lv = K.offLevel(r, p, zone), top = stat(r, 'spinRev', 19) * TAU;
    var wu = (def.windup || 0.8) * T.tellMul, k;
    r.hitT -= dt;
    switch (r.state) {
      case 'stalk':
        r.spinV += ((r.seesPlayer ? 9 : 3) - r.spinV) * Math.min(1, dt * 2);
        if (!p.alive) break;
        // seen: homes in fast; not seen: closes in on the flow field at patrol pace
        K.towardPlayer(r, ctx, zone, dx, dz, dist, r.seesPlayer ? stat(r, 'stalkSpeed', 2.6) : (def.speed || 1.6));
        if (r.seesPlayer && !lv && dist < stat(r, 'spinRange', 2.4) && (K.takeToken(r) || dist < 1.8)) {
          r.act = 'spin'; K.setState(r, 'windup'); sfx('spinup', r, 0.6, 1.6);
        } else if (r.seesPlayer && !lv && !r.held && dist < (def.range || 9) && dist > 3.2 && r.cool <= 0 && K.takeToken(r)) {
          r.act = 'dash'; K.setState(r, 'windup'); sfx('spinup', r, 0.9, 1);
        }
        break;
      case 'windup': {
        var w = r.act === 'spin' ? 0.32 * T.tellMul : wu;
        k = Math.min(1, r.st / w);
        r.spinV += (top * (0.25 + 0.75 * k * k) - r.spinV) * Math.min(1, dt * 10);
        r.crouch = k; r.wob = Math.sin(r.st * 60) * 0.05 * k;
        K.tell(r, k);
        if (r.act === 'dash') { if (dist < 3) K.move(-dx, -dz, 1.5); }   // backs off a touch while it winds up
        else K.move(dx, dz, 1.2);
        if (r.st >= w) {
          if (r.act === 'dash') {
            var tx = p.x + (p.vx || 0) * 0.22, tz = p.z + (p.vz || 0) * 0.22, ddx = tx - r.x, ddz = tz - r.z, dl = Math.hypot(ddx, ddz) || 1;
            r.dashX = ddx / dl; r.dashZ = ddz / dl; r.dashT = Math.min(def.dashTime || 1.1, (dl + 3.2) / (def.chargeSpeed || 12)); r.yaw = Math.atan2(r.dashX, r.dashZ);
          }
          K.setState(r, 'attack'); r.hitT = 0; r.bump = 0;
        }
        break;
      }
      case 'attack':
        r.spinV += (top - r.spinV) * Math.min(1, dt * 8);
        r.swishT -= dt; if (r.swishT <= 0) { r.swishT = 0.11; sfx('swish', r, 0.55, 0.9 + Math.random() * 0.3); }
        if (r.act === 'dash') {
          K.mv.x = r.dashX; K.mv.z = r.dashZ; K.mv.s = def.chargeSpeed || 12;
          if (r.hitT <= 0 && bladeHit(r, ctx, (def.damage || 18) * r.dmgMul, r.dashX, r.dashZ)) r.hitT = 0.45;
          var past = (dx * r.dashX + dz * r.dashZ) < -2.5;
          if (r.st >= r.dashT || past || (r.st > 0.15 && r.bump > 0.1)) { K.setState(r, 'recover'); if (r.bump > 0.1 && IB.Boom && IB.Boom.ready) IB.Boom.word('CLANG!', r.x, r.y + 1.4, r.z, 1.2); }
        } else {
          K.move(dx, dz, 1.4);
          if (r.hitT <= 0 && bladeHit(r, ctx, (def.spinDamage || 7) * r.dmgMul)) r.hitT = 0.25;
          if (r.st >= 0.9) K.setState(r, 'recover');
        }
        break;
      case 'recover': {
        if (r.token) K.releaseToken(r);
        var dz_ = r.act === 'dash' ? (def.recover || 1.4) : 0.7;
        r.spinV *= Math.max(0, 1 - dt * 2.2);
        r.wob = Math.sin(r.st * 9) * 0.2 * Math.max(0, 1 - r.st / dz_);   // dizzy wobble
        if (r.act === 'dash') {
          r.starT -= dt;
          if (r.starT <= 0 && IB.FX) { r.starT = 0.12; var a = r.st * 9; IB.FX.puff(r.x + Math.cos(a) * 0.4, r.y + 1.15, r.z + Math.sin(a) * 0.4, 1, Math.random() < 0.5 ? PAL.amber : PAL.paper, 0.05, 0.1, 0.4); }
        }
        if (r.st >= dz_) { K.setState(r, 'stalk'); r.cool = (1.0 + Math.random() * 1.2) * T.coolMul; r.act = ''; r.wob = 0; }
        break;
      }
    }
  }
  function tickBlader(r, dt) {
    if (r.state !== 'windup' && r.state !== 'attack' && r.state !== 'recover' && r.state !== 'stalk') r.spinV += (2 - r.spinV) * Math.min(1, dt * 2);
    r.hub += r.spinV * dt;
    if (r.hub > TAU * 64) r.hub -= TAU * 64;
  }
  BEH.blader = { think: function (r, dt, ctx, zone, dx, dz, dist) { if (r.weaponId === 'kusari') thinkKusari(r, dt, ctx, zone, dx, dz, dist); else thinkBlader(r, dt, ctx, zone, dx, dz, dist); },
    tick: function (r, dt, ctx) { tickBlader(r, dt); if (r.weaponId === 'kusari') tickKusari(r, dt, ctx); } };

  /* ---- the kusarigama (third Blade Bot weapon, 'kusari'): the hub's clamp holds the weight, a chain (up to KCHAIN
     segments of BOT_BLADER_Chain, as many as its length needs) runs to the sickle. r.km: 'hang' (dangles under the
     clamp and swings), 'whirl' (circles the bot at r.kR m, angle r.kang, the hub turning with it), 'throw' (flies
     straight at the spot the player stood on, r.kv), 'pull' (reeled back in). r.ks: the sickle's world position, r.cs:
     where the chain leaves the weight (kept by the pose). Attack: spin up (windup, a flashing tell), whirl around the
     player for kusariWhirl s (a cut every kusariTick s while he stays inside the circle), a short tell as the circle
     tightens, then the throw; a sidestep beats it (0.65 m). */
  function kusariInit(r) {
    r.km = 'hang'; r.kR = 0.6; r.kang = 0; r.kangV = 0; r.kTick = 0; r.kTicks = 0; r.kHits = 0; r.kHit = false; r.kLen = 0.6; r.kFly = 0;
    if (!r.ks) { r.ks = { x: 0, y: 0, z: 0 }; r.cs = { x: 0, y: 0, z: 0 }; r.kv = { x: 0, y: 0, z: 0 }; r.kt = { x: 0, y: 0, z: 0 }; }
    r.ks.x = r.x; r.ks.y = r.y + 0.3; r.ks.z = r.z; r.cs.x = r.x; r.cs.y = r.y + 0.84; r.cs.z = r.z;
  }
  function thinkKusari(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, T = K.tempo(), lv = K.offLevel(r, p, zone), R = stat(r, 'kusariRadius', 2.7);
    var tx = -dz / dist * r.sdir, tz = dx / dist * r.sdir;
    switch (r.state) {
      case 'stalk':
        r.spinV += ((r.seesPlayer ? 5 : 2.5) - r.spinV) * Math.min(1, dt * 2);
        if (!p.alive) break;
        K.towardPlayer(r, ctx, zone, dx, dz, dist, r.seesPlayer ? stat(r, 'stalkSpeed', 2.6) : (def.speed || 1.6));
        if (r.seesPlayer && !lv && dist < stat(r, 'kusariRange', 4.2) && r.cool <= 0 && (K.takeToken(r) || dist < 2)) {
          r.act = 'whirl'; K.setState(r, 'windup'); r.km = 'whirl'; r.kang = Math.atan2(-(r.ks.z - r.z), r.ks.x - r.x); r.kangV = 3;
          sfx('spinup', r, 0.8, 1.3);
        }
        break;
      case 'windup': {   // the chain pays out and spins up into a wide circle
        var w = 0.6 * T.tellMul;
        r.kangV += (13 - r.kangV) * Math.min(1, dt * 4); r.kR += (R - r.kR) * Math.min(1, dt * 4);
        K.tell(r, Math.min(1, r.st / w));
        if (dist > R * 0.8) K.move(dx, dz, 1.6); else if (dist < 1.6) K.move(-dx, -dz, 1.4);
        if (r.st >= w) { K.setState(r, 'attack'); r.kTick = 0.1; }
        break;
      }
      case 'attack':
        if (r.act === 'whirl') {
          // circles around the player with the chain sweeping over him: a cut every kusariTick s while he is inside it
          var rad = K.clamp((dist - R * 0.65) / 1.5, -1, 1);
          K.move(tx * 0.8 + dx / dist * rad, tz * 0.8 + dz / dist * rad, stat(r, 'stalkSpeed', 2.6));
          r.kTick -= dt;
          if (r.kTick <= 0 && dist <= R + 0.45 && dist > 0.5 && Math.abs((p.y || 0) + 0.9 - r.ks.y) < 1.4) {
            r.kTick = stat(r, 'kusariTick', 0.4); r.kTicks++;
            ctx.hurt(r, stat(r, 'kusariDamage', 5) * r.dmgMul);
            if (IB.Boom && IB.Boom.ready) IB.Boom.sparks(p.x, (p.y || 0) + 1.0, p.z, 0, 0.4, 0, 6);
            sfx('slash', p, 0.5, 1.3);
          }
          if (r.st >= stat(r, 'kusariWhirl', 1.8)) { r.act = 'tell'; r.st = 0; sfx('spinup', r, 0.7, 2); }
        } else if (r.act === 'tell') {   // the circle tightens, the slit flashes: the throw is coming
          r.kangV += (17 - r.kangV) * Math.min(1, dt * 6); r.kR += (1.1 - r.kR) * Math.min(1, dt * 6);
          var tt = stat(r, 'kusariTell', 0.45) * Math.max(0.8, T.tellMul);
          K.tell(r, Math.min(1, r.st / tt));
          if (r.st >= tt) {
            // the sickle flies straight at where the player stands now (a touch of lead)
            var ax = p.x + (p.vx || 0) * 0.12, ay = (p.y || 0) + 1.0, az = p.z + (p.vz || 0) * 0.12;
            var ux = ax - r.ks.x, uy = ay - r.ks.y, uz = az - r.ks.z, ul = Math.hypot(ux, uy, uz) || 1, sp = stat(r, 'kusariSpeed', 17);
            r.kv.x = ux / ul * sp; r.kv.y = uy / ul * sp; r.kv.z = uz / ul * sp;
            r.kt.x = ax; r.kt.y = ay; r.kt.z = az; r.kFly = ul + 1.5;
            r.km = 'throw'; r.act = 'throw'; r.st = 0; r.kHit = false;
            sfx('slash', r, 1, 0.8);
          }
        } else if (r.km === 'hang') K.setState(r, 'recover');   // thrown and reeled back in (tickKusari)
        break;
      case 'recover':
        if (r.token) K.releaseToken(r);
        r.spinV *= Math.max(0, 1 - dt * 2.2);
        if (r.st >= 0.6) { var kc = def.kusariCool || [1.6, 2.6]; K.setState(r, 'stalk'); r.cool = rnd(kc[0], kc[1]) * T.coolMul; r.act = ''; }
        break;
    }
  }
  function tickKusari(r, dt, ctx) {
    var cx = r.x, cy = r.y + 0.84, cz = r.z;
    if (r.km === 'throw' && r.state !== 'attack') r.km = 'pull';   // staggered or blinded mid-throw: reel in
    if (r.km === 'whirl' && r.state !== 'windup' && r.state !== 'attack') r.km = 'hang';
    if (r.km === 'whirl') {
      r.kang += r.kangV * dt;
      var tx = cx + Math.cos(r.kang) * r.kR, ty = cy + 0.05 * Math.sin(r.kang * 2), tz = cz - Math.sin(r.kang) * r.kR;
      var f = Math.min(1, dt * 18); r.ks.x += (tx - r.ks.x) * f; r.ks.y += (ty - r.ks.y) * f; r.ks.z += (tz - r.ks.z) * f;
      r.hub = r.kang - r.yaw - r.bspin;   // the weight points at the sickle
      r.swishT -= dt; if (r.swishT <= 0) { r.swishT = Math.PI / Math.max(4, r.kangV); sfx('swish', r, 0.5, 0.7 + Math.random() * 0.2); }
    } else if (r.km === 'throw') {
      var ox = r.ks.x, oy = r.ks.y, oz = r.ks.z, sp = Math.hypot(r.kv.x, r.kv.y, r.kv.z) || 1;
      r.ks.x += r.kv.x * dt; r.ks.y += r.kv.y * dt; r.ks.z += r.kv.z * dt; r.kFly -= sp * dt;
      var p = ctx.player, Pj = IB.Projectiles;
      if (!r.kHit && p && p.alive && Pj && Pj.segHitsCapsule && Pj.segHitsCapsule(ox, oy, oz, r.ks.x, r.ks.y, r.ks.z, p.x, (p.y || 0) + 0.35, (p.y || 0) + 1.35, p.z, 0.35, 0.3)) {
        r.kHit = true; r.kHits++;
        ctx.hurt(r, stat(r, 'kusariThrow', 16) * r.dmgMul);
        if (!p.robot) { var hx = r.x - p.x, hz = r.z - p.z, hl = Math.hypot(hx, hz) || 1; p.knockX = (p.knockX || 0) + hx / hl * 3; p.knockZ = (p.knockZ || 0) + hz / hl * 3; }   // the chain tugs him in
        if (IB.Boom && IB.Boom.ready) { IB.Boom.sparks(r.ks.x, r.ks.y, r.ks.z, -r.kv.x / sp, 0.3, -r.kv.z / sp, 10); IB.Boom.word('SHNK!', p.x, (p.y || 0) + 2.0, p.z, 1.1); }
        sfx('slash', p, 1, 1.1);
        r.km = 'pull';
      }
      var W = ctx.world, wall = W && W.ray ? W.ray(ox, oy, oz, r.kv.x / sp, r.kv.y / sp, r.kv.z / sp, sp * dt + 0.05) : null;
      var floor = W && W.floorAt ? W.floorAt(r.ks.x, r.ks.z, r.ks.y + 0.3) : 0;
      if (r.km === 'throw' && (wall || r.ks.y < floor + 0.05)) { if (IB.Boom && IB.Boom.ready) IB.Boom.sparks(r.ks.x, r.ks.y, r.ks.z, 0, 0.5, 0, 6); sfx('clank', r.ks, 0.8); r.km = 'pull'; }
      if (r.kFly <= 0 || Math.hypot(r.ks.x - cx, r.ks.z - cz) > stat(r, 'kusariReach', 7.5)) r.km = 'pull';
      r.hub = Math.atan2(-(r.ks.z - cz), r.ks.x - cx) - r.yaw - r.bspin;
    } else if (r.km === 'pull') {
      var bx = r.cs.x - r.ks.x, by = r.cs.y - 0.5 - r.ks.y, bz = r.cs.z - r.ks.z, bl = Math.hypot(bx, by, bz), step = 14 * dt;
      if (bl <= Math.max(step, 0.3)) r.km = 'hang';
      else { r.ks.x += bx / bl * step; r.ks.y += by / bl * step; r.ks.z += bz / bl * step; }
      r.hub = Math.atan2(-(r.ks.z - cz), r.ks.x - cx) - r.yaw - r.bspin;
    } else {
      // hang: the sickle dangles half a metre under the weight and swings a little
      var sw = Math.sin(r.idleT * 2.3 + r.slot) * 0.12, g = Math.min(1, dt * 7);
      var hx2 = r.cs.x + sw * Math.cos(r.yaw), hy2 = r.cs.y - 0.55, hz2 = r.cs.z - sw * Math.sin(r.yaw);
      r.ks.x += (hx2 - r.ks.x) * g; r.ks.y += (hy2 - r.ks.y) * g; r.ks.z += (hz2 - r.ks.z) * g;
      r.kangV *= Math.max(0, 1 - dt * 3); r.kR += (0.6 - r.kR) * Math.min(1, dt * 3);
    }
    r.kLen = Math.hypot(r.ks.x - r.cs.x, r.ks.y - r.cs.y, r.ks.z - r.cs.z);
  }
  /* pose: the hub and the weight in the clamp (level), then the chain and the sickle in world space */
  var _km = null, _kq = null, _kv = null, _ks = null, _kx = null, _ky = null, _kz = null, _kup = null, _kp = [];
  function poseKusari(r, P, v) {
    if (!_km) {
      _km = new THREE.Matrix4(); _kq = new THREE.Quaternion(); _kv = new THREE.Vector3(0, 0, 1); _ks = new THREE.Vector3(); _kx = new THREE.Vector3();
      _ky = new THREE.Vector3(); _kz = new THREE.Vector3(); _kup = new THREE.Vector3(0, 1, 0);
      for (var q = 0; q <= KCHAIN; q++) _kp.push(new THREE.Vector3());
    }
    P.tv(v.hub).ry(r.hub).emit('Hub', 0).tv(v.grip).emit('Fundo', 0).tv(v.chain).pos(r.cs).hide('Katana', 0).hide('Axe', 0);
    var a = r.cs, b = r.ks, Lx = b.x - a.x, Ly = b.y - a.y, Lz = b.z - a.z, L = Math.hypot(Lx, Ly, Lz) || 0.001;
    var n = Math.max(2, Math.min(KCHAIN, Math.ceil(L / 0.2))), i;
    // a bend: the whirling chain trails its sweep, a thrown one ripples, a hanging one barely curves
    var hl = Math.hypot(Lx, Lz) || 0.001, px = -Lz / hl, pz = Lx / hl;
    var bend = r.km === 'whirl' ? -0.16 * L : r.km === 'throw' ? 0.1 * L * Math.sin(r.st * 22) : 0.03, sag = r.km === 'hang' ? 0 : r.km === 'whirl' ? 0.05 : 0.1;
    for (i = 0; i <= n; i++) {
      var t = i / n, sn = Math.sin(t * Math.PI);
      _kp[i].set(a.x + Lx * t + px * bend * sn, a.y + Ly * t - sag * sn * L, a.z + Lz * t + pz * bend * sn);
    }
    for (i = 0; i < KCHAIN; i++) {
      if (i >= n) { P.hide('Chain', i); continue; }
      _kz.subVectors(_kp[i + 1], _kp[i]); var sl = _kz.length() || 0.001; _kz.divideScalar(sl);
      _kq.setFromUnitVectors(_kv, _kz);
      _km.compose(_kp[i], _kq, _ks.set(1, 1, sl / 0.2));
      P.mat(_km).emit('Chain', i);
    }
    // the sickle: its handle runs on along the chain, the blade lies flat and leads the swing
    _kz.subVectors(_kp[n], _kp[n - 1]).normalize();
    if (r.km === 'whirl') _kx.set(-Math.sin(r.kang), 0, -Math.cos(r.kang)); else _kx.crossVectors(_kup, _kz);
    _kx.addScaledVector(_kz, -_kx.dot(_kz)); if (_kx.lengthSq() < 1e-6) _kx.set(1, 0, 0); _kx.normalize();
    _ky.crossVectors(_kz, _kx);
    _km.makeBasis(_kx, _ky, _kz).setPosition(b.x, b.y, b.z);
    P.mat(_km).emit('Kusari', 0);
  }


  // ======================================================================= HAWK (levels 20+)
  /* An advanced aerial robot: armoured fuselage, two ducted fans that vector with its flight (Fan, Rotor), a chin
     turret (Gun) and a sensor eye (Light). Orbits the player like the Drone, a little faster, and darts aside when hit.
     Each Hawk has one round type (def.rounds odds), painted on its accents (key-tint material: r.tint) and its eye:
     'bullet' normal rounds, 'shock' / 'acid' damage over time on the player, 'boom' a small blast (projectiles.js
     special rounds, the Soldier's plumbing). */
  function hk(n) { return K.sock('BOT_HAWK_' + n); }
  var HAWK_KINDS = ['bullet', 'shock', 'acid', 'boom'];
  VIS.hawk = {
    radius: 0.42, y0: 0.08, y1: 0.56, coreR: 0.13, shadow: 0.55, eye: 0.3, home: 'keep', flying: true, centre: 0.3,
    parts: { Body: { count: 1, asset: 'BOT_HAWK_Body', tint: true }, Fan: { count: 2, asset: 'BOT_HAWK_Fan', tint: true },
      Rotor: { count: 2, asset: 'BOT_HAWK_Rotor' }, Gun: { count: 1, asset: 'BOT_HAWK_Gun', tint: true },
      Light: { count: 1, light: true, asset: 'BOT_HAWK_Light' } },
    sockets: function (v) {
      var c = hk('CORE'); v.coreY = c[1]; v.coreZ = c[2];
      v.fans = [hk('FAN0'), hk('FAN1')]; v.pivot = hk('GUNPIVOT'); v.muzzle = hk('GUN'); v.light = hk('LIGHT');
    },
    init: function (r) {
      var o = r.def.rounds || { bullet: 1 }, x = Math.random(), acc = 0, k;
      r.round = 'bullet';
      for (k in o) { acc += o[k]; if (x < acc) { r.round = k; break; } }
      if (!r.tint) r.tint = new THREE.Color();
      r.tint.set((r.def.roundColors || {})[r.round] || '#E6ECF5'); r.tintHex = r.tint.getHex();
      r.fanT = 0; r.dodge = 0; r.dodgeT = 0; r.hit0 = r.hp;
    },
    pose: function (r, P) {
      var v = VIS.hawk, c = v.centre, i;
      P.root().t(0, c, 0).rx(r.bankX).rz(r.bankZ + r.wob).t(0, -c, 0).emit('Body', 0);
      for (i = 0; i < 2; i++) P.push().tv(v.fans[i]).rx(r.fanT).rz((i ? -1 : 1) * r.bankZ * 0.8).emit('Fan', i).ry((i ? 1 : -1) * r.spin * 1.6).emit('Rotor', i).pop();
      P.push().tv(v.pivot).rx(-r.aim).t(0, 0, -r.kick * 0.03).emit('Gun', 0).pop();
      P.tv(v.light).emit('Light', 0);
    },
    lightColor: function (r) {
      if (r.state === 'windup' && (r.st * 14 | 0) % 2 === 0) return PAL.red;
      if (r.alert > 0) return Math.sin(r.alert * 40) > 0 ? PAL.red : r.tintHex;
      return r.state === 'idle' ? 0x4A5A66 : r.tintHex;
    },
    corpse: function (v, add) {
      var M = new THREE.Matrix4();
      add('BOT_HAWK_Body', M.identity());
      v.fans.forEach(function (f) { add('BOT_HAWK_Fan', M.makeTranslation(f[0], f[1], f[2])); });
      add('BOT_HAWK_Gun', M.makeTranslation(v.pivot[0], v.pivot[1], v.pivot[2]));
    }
  };
  function thinkHawk(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, v = VIS.hawk, T = K.tempo(), speed = def.speed || 5.4, wu = (def.windup || 0.4) * T.tellMul;
    var kd = def.keepDistance || [9, 17], mid = (kd[0] + kd[1]) / 2;
    // hit: a quick dodge to the side (a second at most every 2.5 s)
    r.dodgeT -= dt; r.dodge = Math.max(0, r.dodge - dt);
    if (r.hp < r.hit0 - 0.01) { if (r.dodgeT <= 0) { r.dodge = 0.55; r.dodgeT = 2.5; r.sdir = -r.sdir; } }
    r.hit0 = r.hp;
    var boost = r.dodge > 0 ? 1.8 : 1;
    // orbit: tangential strafe + radial correction toward the middle of the band
    var rad = K.clamp((dist - mid) / 4, -1, 1), tx = -dz / dist * r.sdir, tz = dx / dist * r.sdir;
    var ox = tx * 0.85 + dx / dist * rad, oz = tz * 0.85 + dz / dist * rad;
    r.thinkT -= dt;
    if (r.thinkT <= 0 || r.bump > 0.25) { r.thinkT = 1.4 + Math.random() * 2; if (r.bump > 0.25 || Math.random() < 0.6) r.sdir = -r.sdir; r.bump = 0; }
    if (p.alive) K.turnTo(r, Math.atan2(dx, dz), 6, dt);
    switch (r.state) {
      case 'keep':
        r.aim += (-0.25 - r.aim) * Math.min(1, dt * 4);
        if (!p.alive) break;
        if (!r.seesPlayer && r.lost > 1.5) K.towardPlayer(r, ctx, zone, dx, dz, dist, speed);
        else K.move(ox, oz, speed * boost);
        if (K.canFire(r, ctx, dist)) { K.setState(r, 'windup'); K.play('rotor', r, 0.7); }
        break;
      case 'windup':
        K.move(ox, oz, speed * 0.5 * boost);
        r.aim += (K.aimPitch(r, v, p) - r.aim) * Math.min(1, dt * 9);
        K.tell(r, r.st / wu);
        if (r.st >= wu) { K.setState(r, 'attack'); r.shots = 0; r.shotT = 0; }
        break;
      case 'attack':
        K.move(ox, oz, speed * boost);
        r.aim += (K.aimPitch(r, v, p) - r.aim) * Math.min(1, dt * 10);
        r.shotT -= dt;
        var n = r.round === 'boom' ? Math.max(1, (def.bolts || 3) - 1) : (def.bolts || 3);
        if (r.shots < n && r.shotT <= 0) {
          var m = K.muzzleWorld(r, v, 0);
          fireRound(r, { x: m.x, y: m.y, z: m.z }, p, def.boltSpeed || 30, (def.damage || 5) * r.dmgMul, 0.2, r.shots ? 0.05 : 0.02, r.round);
          r.shots++; r.shotT = 0.13;
        }
        if (r.shots >= n && r.shotT <= -0.05) K.setState(r, 'recover');
        break;
      case 'recover':
        if (r.token) K.releaseToken(r);
        K.move(ox, oz, speed * 0.8 * boost);
        r.aim += (-0.25 - r.aim) * Math.min(1, dt * 3);
        if (r.st >= (def.recover || 0.75)) { K.setState(r, 'keep'); r.cool = (1.2 + Math.random() * 1.5) * T.coolMul * (r.round === 'boom' ? (IB.Damage && IB.Damage.lateBoom ? IB.Damage.lateBoom() : { dmg: 1, cool: 1 }).cool : 1); }
        break;
    }
  }
  function tickHawk(r, dt) {
    // the fans vector with the flight: tipped forward when it flies forward, back when it brakes
    var fwd = (r.vx || 0) * Math.sin(r.yaw) + (r.vz || 0) * Math.cos(r.yaw);
    r.fanT += (K.clamp(fwd * 0.09, -0.45, 0.45) - r.fanT) * Math.min(1, dt * 6);
    r.kick = Math.max(0, r.kick - dt * 6);
  }
  BEH.hawk = { think: thinkHawk, tick: tickHawk };
  Tr.HAWK_KINDS = HAWK_KINDS;

  // ======================================================================= runtime: grenades, smears, shock
  // smear arc: an annulus sector trailing the blade (local +X = the blade, the trail sweeps toward +Z behind it),
  // alpha fading along the arc, a thin ink line at the outer edge (comic speed arc)
  function smearGeometry() {
    var SEG = 36, ARC = 5.4, rows = [[0.34, 0], [0.46, 0.5], [0.72, 0.62], [0.9, 0.9], [0.955, 0.95], [0.975, 1], [1.035, 1]], ink = [0, 0, 0, 0, 0, 1, 1];
    var pos = [], al = [], ik = [], idx = [], i, j;
    for (i = 0; i <= SEG; i++) {
      var th = i / SEG * ARC, f = 0.18 + 0.82 * Math.pow(1 - i / SEG, 1.3);
      for (j = 0; j < rows.length; j++) { pos.push(Math.cos(th) * rows[j][0], 0, Math.sin(th) * rows[j][0]); al.push(rows[j][1] * f); ik.push(ink[j]); }
    }
    var W = rows.length;
    for (i = 0; i < SEG; i++) for (j = 0; j < W - 1; j++) { var a = i * W + j, b = a + W; idx.push(a, b, a + 1, a + 1, b, b + 1); }
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('aA', new THREE.Float32BufferAttribute(al, 1));
    g.setAttribute('aInk', new THREE.Float32BufferAttribute(ik, 1));
    g.setIndex(idx);
    return g;
  }
  var SMEAR_CAP = 40, smear = null, nadeMesh = null, ringMesh = null, _m4 = null, _q4 = null, _v4 = null, _s4 = null, _up = null;
  function initRuntime(scene) {
    _m4 = new THREE.Matrix4(); _q4 = new THREE.Quaternion(); _v4 = new THREE.Vector3(); _s4 = new THREE.Vector3(); _up = new THREE.Vector3(0, 1, 0); _c = new THREE.Color();
    var g = smearGeometry(), ic = new THREE.InstancedBufferAttribute(new Float32Array(SMEAR_CAP * 4), 4);
    ic.setUsage(THREE.DynamicDrawUsage); g.setAttribute('iCol', ic);
    var mat = new THREE.ShaderMaterial({
      uniforms: { uInk: { value: new THREE.Color(PAL.ink) } }, transparent: true, depthWrite: false, side: THREE.DoubleSide,
      vertexShader: 'attribute float aA; attribute float aInk; attribute vec4 iCol; varying float vA; varying float vInk; varying vec4 vCol;\n' +
        'void main() { vA = aA; vInk = aInk; vCol = iCol; gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4(position, 1.0); }',
      fragmentShader: 'uniform vec3 uInk; varying float vA; varying float vInk; varying vec4 vCol;\n' +
        'void main() { gl_FragColor = vec4(mix(vCol.rgb, uInk, vInk), vA * vCol.a * mix(0.85, 1.0, vInk)); }'
    });
    smear = new THREE.InstancedMesh(g, mat, SMEAR_CAP);
    smear.instanceMatrix.setUsage(THREE.DynamicDrawUsage); smear.frustumCulled = false; smear.renderOrder = 3; smear.count = 0; smear.visible = false; smear.name = 'bladeSmear';
    scene.add(smear);
    // grenades: the Soldier's grenade model in the robot material (aFx.x blinks the fuse), red reach rings
    var ng = IB.Assets.get('BOT_SOLDIER_Nade').clone(), n = Tr.nadeCap;
    var fx = new THREE.InstancedBufferAttribute(new Float32Array(n * 4), 4); fx.setUsage(THREE.DynamicDrawUsage); ng.setAttribute('aFx', fx);
    nadeMesh = new THREE.InstancedMesh(ng, AI.mat, n);
    nadeMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); nadeMesh.frustumCulled = false; nadeMesh.count = 0; nadeMesh.visible = false; nadeMesh.name = 'enemyNades';
    scene.add(nadeMesh);
    var rg = new THREE.RingGeometry(0.92, 1, 40); rg.rotateX(-Math.PI / 2);
    ringMesh = new THREE.InstancedMesh(rg, new THREE.MeshBasicMaterial({ color: PAL.red, transparent: true, opacity: 0.6, depthWrite: false }), n);
    ringMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); ringMesh.frustumCulled = false; ringMesh.renderOrder = 2; ringMesh.count = 0; ringMesh.visible = false;
    scene.add(ringMesh);
    for (var i = 0; i < n; i++) Tr.grenades.push({ on: false, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, t: 0, fuse: 2, rest: false, spin: 0, rx: 0, rz: 0, R: 3.4, dmg: 0, rdmg: 0, src: { x: 0, z: 0, type: 'soldier', proj: true } });
  }
  var SMEAR_COL = { katana: new THREE.Color(0xDCEBFF), eaxe: new THREE.Color(0x6FEFFF), kusari: new THREE.Color(0xFFE2D6) };
  var _t = 0;
  function syncRuntime() {
    if (!smear) return;
    _t += 1 / 60;
    var n = 0, ic = smear.geometry.attributes.iCol, T = AI.types.blader, i;
    if (T) for (i = 0; i <= T.hi; i++) {
      var r = T.slots[i]; if (!r.on || n >= SMEAR_CAP) continue;
      var kus = r.weaponId === 'kusari';
      var k = kus ? (r.km === 'whirl' ? K.clamp((r.kangV - 6) / 8, 0, 1) * K.clamp((r.kR - 0.8) / 1.2, 0, 1) : 0) : K.clamp((r.spinV - 30) / 70, 0, 1); if (k <= 0.02) continue;
      var v = VIS.blader, bob = Math.sin(r.idleT * 2.6 + r.slot) * 0.03 - r.crouch * 0.08, yaw = r.yaw + r.bspin, sy = Math.sin(yaw), cy = Math.cos(yaw);
      _v4.set(r.x + v.hub[0] * cy + v.hub[2] * sy, r.y + bob + v.hub[1] + 0.02, r.z - v.hub[0] * sy + v.hub[2] * cy);
      if (kus) { _v4.set(r.x, r.ks.y, r.z); _q4.setFromAxisAngle(_up, r.kang); _s4.set(r.kR + 0.25, 1, r.kR + 0.25); }   // the whirling chain's sweep
      else { _q4.setFromAxisAngle(_up, yaw + r.hub); _s4.set(r.reach + 0.04, 1, r.reach + 0.04); }
      _m4.compose(_v4, _q4, _s4); smear.setMatrixAt(n, _m4);
      var c = SMEAR_COL[r.weaponId] || SMEAR_COL.katana; ic.setXYZW(n, c.r, c.g, c.b, 0.92 * k);
      n++;
    }
    smear.count = n; smear.visible = n > 0;
    if (n) { smear.instanceMatrix.needsUpdate = true; ic.needsUpdate = true; }
    // grenades + rings (the ring shows the blast reach in the last 1.2 s, blinking faster near the end)
    var m = 0, rn = 0, fxa = nadeMesh.geometry.attributes.aFx;
    for (i = 0; i < Tr.grenades.length; i++) {
      var g = Tr.grenades[i]; if (!g.on) continue;
      var left = g.fuse - g.t, blink = Math.sin(_t * (left < 0.6 ? 40 : left < 1.2 ? 22 : 9)) > 0.3 ? 1 : 0;
      _v4.set(g.x, g.y, g.z);
      if (g.rest) _q4.setFromEuler(_e.set(Math.PI / 2, g.rx, 0)); else _q4.setFromEuler(_e.set(g.rx, 0, g.rz));
      var gs = g.impact ? 0.95 : 1.15; _s4.set(gs, gs, gs); _m4.compose(_v4, _q4, _s4); nadeMesh.setMatrixAt(m, _m4); fxa.setXYZW(m, g.impact ? 0 : blink, 0, 0, 0); m++;
      if (g.impact && !g.rest) {   // launcher grenade in flight: the ring waits where it will land
        if (Math.sin(_t * 26) > -0.3) { _v4.set(g.lx, g.ly - NR + 0.03, g.lz); _q4.identity(); _s4.set(g.R, 1, g.R); _m4.compose(_v4, _q4, _s4); ringMesh.setMatrixAt(rn++, _m4); }
      } else if (left < 1.2 && Math.sin(_t * (left < 0.5 ? 40 : 22)) > -0.2) {
        _v4.set(g.x, Math.max(0.02, g.y - NR + 0.02), g.z); _q4.identity(); _s4.set(g.R, 1, g.R); _m4.compose(_v4, _q4, _s4); ringMesh.setMatrixAt(rn++, _m4);
      }
      if (IB.FX && Math.random() < 0.2) IB.FX.puff(g.x, g.y + 0.08, g.z, 1, PAL.paper, 0.04, 0.12, 0.4);
    }
    nadeMesh.count = m; nadeMesh.visible = m > 0; ringMesh.count = rn; ringMesh.visible = rn > 0;
    if (m) { nadeMesh.instanceMatrix.needsUpdate = true; fxa.needsUpdate = true; }
    if (rn) ringMesh.instanceMatrix.needsUpdate = true;
  }
  var _e = null;
  // the Voltaxe's shock on the player: a hit every 0.4 s while it lasts
  function updateShock(dt, ctx) {
    var S = Tr.shock; if (S.left <= 0) return;
    var p = ctx.player; if (!p || !p.alive || p.robot) { S.left = 0; return; }
    S.left -= dt; S.tick -= dt;
    if (S.tick <= 0) {
      S.tick = 0.4; ctx.hurt(S.src, S.dps * 0.4);
      if (IB.Boom && IB.Boom.ready) IB.Boom.zap(p.x + rnd(-0.3, 0.3), p.y + 0.7, p.z + rnd(-0.3, 0.3), 0.5);
      sfx('boltHit', p, 0.4, 1.6);
    }
  }
  function updateAcid(dt, ctx) {
    var S = Tr.acid; if (S.left <= 0) return;
    var p = ctx.player; if (!p || !p.alive || p.robot) { S.left = 0; return; }
    S.left -= dt; S.tick -= dt;
    if (S.tick <= 0) {
      S.tick = 0.5; ctx.hurt(S.src, S.dps * 0.5);
      if (IB.FX) IB.FX.puff(p.x + rnd(-0.3, 0.3), p.y + 0.6 + rnd(0, 0.6), p.z + rnd(-0.3, 0.3), 3, 0x6BE03A, 0.08, 0.3, 1.2);
      sfx('hit', p, 0.3, 0.7);
    }
  }
  function clearRuntime() { Tr.grenades.forEach(function (g) { g.on = false; g.impact = false; }); Tr.shock.left = 0; Tr.shock.tick = 0; Tr.acid.left = 0; Tr.acid.tick = 0; }

  // ---- hook into the robot runtime (init / update / sync / clear)
  var baseInit = AI.init, baseUpdate = AI.update, baseSync = AI.sync, baseClear = AI.clear, baseDespawn = AI.despawn;
  AI.init = function (scene) { baseInit.apply(AI, arguments); _e = new THREE.Euler(); initRuntime(scene); };
  AI.update = function (dt, ctx) { baseUpdate.apply(AI, arguments); updateNades(dt, ctx.world, ctx.player); updateShock(dt, ctx); updateAcid(dt, ctx); };
  AI.sync = function () { baseSync.apply(AI, arguments); syncRuntime(); };
  AI.clear = function () { baseClear.apply(AI, arguments); clearRuntime(); };
  AI.despawn = function () { baseDespawn.apply(AI, arguments); clearRuntime(); };

  Tr.stats = function () {
    var out = { nades: liveNades(), shock: +Tr.shock.left.toFixed(2), acid: +Tr.acid.left.toFixed(2), smears: smear ? smear.count : 0, soldiers: [], bladers: [],
      mechs: [], grenadiers: [], hawks: [], rocketeers: [], shells: Tr.shells || 0, rockets: Tr.rockets || 0 };
    AI.robots.forEach(function (r) {
      if (!r.on) return;
      if (r.type === 'soldier') out.soldiers.push({ slot: r.slot, state: r.state, act: r.act, hp: +r.hp.toFixed(1), shield: +r.shield.toFixed(1), nades: r.nades, armour: r.armour, torso: r.torso, helm: r.helm });
      if (r.type === 'blader') out.bladers.push({ slot: r.slot, state: r.state, act: r.act, weapon: r.weaponId, spinRev: +(r.spinV / TAU).toFixed(1), km: r.km || '', chain: r.kLen ? +r.kLen.toFixed(2) : 0, kTicks: r.kTicks || 0, kHits: r.kHits || 0 });
      if (r.type === 'rocketeer') out.rocketeers.push({ slot: r.slot, state: r.state, act: r.act, launcher: r.launcher, hp: +r.hp.toFixed(1), shield: +r.shield.toFixed(1), shoulder: +(r.shoulder || 0).toFixed(2), variant: r.trVariant });
      if (r.type === 'mech' || r.type === 'grenadier') out[r.type + 's'].push({ slot: r.slot, state: r.state, act: r.act, hp: +r.hp.toFixed(1), shield: +r.shield.toFixed(1), nades: r.nades, variant: r.trVariant });
      if (r.type === 'hawk') out.hawks.push({ slot: r.slot, state: r.state, round: r.round, tint: r.tintHex, hp: +r.hp.toFixed(1), y: +r.y.toFixed(2) });
    });
    return out;
  };
})(window.IB = window.IB || {});
