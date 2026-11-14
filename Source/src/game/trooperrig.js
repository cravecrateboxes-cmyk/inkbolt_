/* INKBOLT trooper rig: the Soldier drawn as a skinned, animated character in SWAT / military kit
   (fps-troopers.glb, built by blender/fam_trooper.py on Quaternius' CC0 Universal Animation Library).
   The Soldier's brain stays in troops.js; this file replaces only its look:
     - one skinned clone per live soldier (pooled), one of four kit colourways (palette recolour), the robot ink
       outline (and the Undercover stealth-blue glow), a hit flash and the rogue teal through per-soldier uniforms
     - layered animation: the legs play idle / walk / jog / sprint / crouch cycles matched to the ground speed (backwards
       when backing off), facing the way the soldier moves; the spine twists the chest back onto the target, and the
       upper body holds the carbine at low ready, or aims (up / level / down blended by pitch); one-shots for hit
       flinches, rifle-butt strikes, grenade throws and reloads; procedural recoil on every round
     - death: the Death animation plays out, the body lies for a moment and sinks (no ink corpse for soldiers)
     - r.muzzleW / r.handLW: world positions of the carbine muzzle and the left hand, used by troops.js for rounds and
       grenade throws
   Levels 20+ share the rig (TR.TYPES): the Grenadier is the Soldier's mesh with its carbine hidden (the carbine's
   vertices carry colour alpha 0 -> IB.Assets aMask; the grenadier material clips them) plus TROOPER_GL, a grenade
   launcher skinned to the right hand (r.muzzleW = TROOPER_GL_MUZZLE); the Robot Trooper ('mech') draws TROOPER_MECH,
   a robot body (servo joints, piston limbs, segmented chassis, sensor head, its own carbine) on the same bones, in one
   of TR.MECH_VARIANTS (palette recolour of its plate keys). One pool of rigs serves every type: each rig carries all
   three meshes and shows the ones its robot needs.
   IB.TrooperRig.init(scene) runs from AI.init; sync() from AI.sync; clear() from AI.clear / despawn. */
(function (IB) {
  'use strict';
  var AI = IB.AI, VIS = AI.VIS;
  var TR = IB.TrooperRig = { live: {}, pool: [], dying: [], ready: false, count: 0 };
  // kit colourways: palette colours swapped per soldier (defaults = the first one, as built in Blender)
  var KEYS = ['uniform', 'uniform2', 'vest', 'vest2', 'helmet', 'pad'];
  var BASEC = ['#2B3445', '#222937', '#1E2128', '#2D323C', '#23262D', '#2F333C'];
  TR.VARIANTS = [
    { name: 'SWAT', c: BASEC },
    { name: 'Black ops', c: ['#2A2C31', '#202126', '#17181C', '#2B2D33', '#1B1C20', '#33353B'] },
    { name: 'Woodland', c: ['#56613F', '#475133', '#8C7A55', '#77684A', '#5D6745', '#6B5E44'] },
    { name: 'Urban', c: ['#4C525B', '#3E444C', '#2E3238', '#3B4047', '#3A3F46', '#555B64'] }
  ];
  // Robot Trooper colourways: its two plate keys and the accent (hazard) key
  var MKEYS = ['#5E6670', '#454C55', '#E8A42A'];
  TR.MECH_VARIANTS = [
    { name: 'Gunmetal', c: MKEYS },
    { name: 'Olive', c: ['#6E7552', '#555B3F', '#E8A42A'] },
    { name: 'Sand', c: ['#A8996F', '#83775A', '#D9452F'] },
    { name: 'Arctic', c: ['#C3C9D1', '#8F97A2', '#E0482F'] }
  ];
  TR.TYPES = { soldier: 1, grenadier: 1, mech: 1, rocketeer: 1 };
  /* Rocket Soldier (levels 35+): the Soldier's body with its carbine hidden (like the Grenadier) and the player's own
     launcher model (fps-weapons WPN_HOTHEAD / WPN_MURMUR with its cassette, drawn LAUNCHER_SCALE up): carried in the
     right hand, tube forward and low; shouldered while it aims and fires (r.shoulder 0..1 eases between the two): the
     launcher's stock (rest point RL_REST, launcher space) sits on top of the right shoulder and the tube follows the
     aim. r.muzzleW = the launcher's muzzle socket. On death the launcher stays in the falling hand. */
  var LAUNCHER_SCALE = 1.3, RL_REST = { hothead: [0, -0.02, 0.24], murmur: [0, -0.02, 0.17] };
  var UPPER = /spine00[23]|neck|head|shoulder|upper_arm|forearm|hand|f_(index|middle|pinky|ring)|thumb/;
  var LOW = { idle: 'Idle_Loop', walk: 'Walk_Loop', jog: 'Jog_Fwd_Loop', sprint: 'Sprint_Loop', cidle: 'Crouch_Idle_Loop', cwalk: 'Crouch_Fwd_Loop' };
  var UP = { ready: 'Pistol_Idle_Loop', aimN: 'Pistol_Aim_Neutral', aimU: 'Pistol_Aim_Up', aimD: 'Pistol_Aim_Down' };
  var ONE = { hit: 'Hit_Chest', hitH: 'Hit_Head', punch: 'Punch_Cross', toss: 'Spell_Simple_Shoot', reload: 'Pistol_Reload' };
  var clips = null, src = null, mats = [], scene = null;
  var _v = new THREE.Vector3(), _q = new THREE.Quaternion(), _qp = new THREE.Quaternion(), _ax = new THREE.Vector3(0, 1, 0);

  function boneName(trackName) { return trackName.slice(0, trackName.lastIndexOf('.')); }
  function part(clip, upper, name) {
    var tr = clip.tracks.filter(function (t) { var b = boneName(t.name); return /^root/.test(b) ? false : UPPER.test(b) === upper; });
    return new THREE.AnimationClip(name, clip.duration, tr);
  }
  function prepClips(list) {
    var by = {}; list.forEach(function (c) { by[c.name] = c; });
    var out = { low: {}, up: {}, one: {}, death: null };
    Object.keys(LOW).forEach(function (k) { if (by[LOW[k]]) out.low[k] = part(by[LOW[k]], false, k); });
    Object.keys(UP).forEach(function (k) { if (by[UP[k]]) out.up[k] = part(by[UP[k]], true, k); });
    Object.keys(ONE).forEach(function (k) { if (by[ONE[k]]) out.one[k] = part(by[ONE[k]], true, k); });
    if (by.Death01) out.death = new THREE.AnimationClip('death', by.Death01.duration, by.Death01.tracks.filter(function (t) { return !/^root/.test(boneName(t.name)); }));
    return out;
  }

  // palette recolour: every texel of a key colour becomes the colourway's colour
  function hexRGB(h) { var n = parseInt(h.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
  function recolour(img, to, keys) {
    var w = img.width, h = img.height, cv = document.createElement('canvas'); cv.width = w; cv.height = h;
    var g = cv.getContext('2d'); g.drawImage(img, 0, 0);
    var d = g.getImageData(0, 0, w, h), px = d.data, from = (keys || BASEC).map(hexRGB), dst = to.map(hexRGB);
    for (var i = 0; i < px.length; i += 4) {
      for (var k = 0; k < from.length; k++) {
        var f = from[k];
        if (Math.abs(px[i] - f[0]) < 3 && Math.abs(px[i + 1] - f[1]) < 3 && Math.abs(px[i + 2] - f[2]) < 3) { px[i] = dst[k][0]; px[i + 1] = dst[k][1]; px[i + 2] = dst[k][2]; break; }
      }
    }
    g.putImageData(d, 0, 0);
    var t = new THREE.CanvasTexture(cv);
    t.flipY = false; t.encoding = THREE.LinearEncoding; t.magFilter = t.minFilter = THREE.NearestFilter; t.generateMipmaps = false;
    return t;
  }
  /* a per-soldier material: the robot toon material (skinned) + flash / rogue uniforms. hideGun: the Grenadier's body
     (the carbine's vertices, aMask 0, are clipped away); U: share the flash uniform with the rig's other mesh */
  function soldierMat(tex, hideGun, U) {
    U = U || { value: new THREE.Vector3() };
    var m = IB.Render.toonMaterial({ map: tex, skinning: true, uni: IB.Render.robotOutline, baked: IB.Assets.BAKED.troopers, look: 'actor', surf: IB.Surface && IB.Surface.surf('troopers') });
    var base = m.onBeforeCompile;
    m.onBeforeCompile = function (sh) {
      base(sh);
      if (hideGun) sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aMask;')
        .replace('gl_Position = projectionMatrix * mvPosition;', 'gl_Position = projectionMatrix * mvPosition;\nif ( aMask < 0.5 ) gl_Position = vec4( 0.0, 0.0, 2.0, 1.0 );');
      sh.uniforms.uTrFx = U;
      sh.fragmentShader = sh.fragmentShader
        .replace('uniform vec3 uInk;', 'uniform vec3 uInk;\nuniform vec3 uTrFx;')
        .replace('if ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );',
          'gl_FragColor.rgb = mix( gl_FragColor.rgb, vec3( 1.0 ), uTrFx.x );\n' +
          'gl_FragColor.rgb = mix( gl_FragColor.rgb, vec3( 0.07, 0.78, 0.71 ), uTrFx.y );\n' +
          'if ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );');
    };
    var key = m.customProgramCacheKey;
    m.customProgramCacheKey = function () { return key() + 'trp' + (hideGun ? 'g' : ''); };
    m.userData.fx = U.value;
    return m;
  }
  // clone the rig with its own skeleton (SkeletonUtils.clone)
  function cloneRig(root) {
    var c = root.clone(true), sl = [], cl = [];
    root.traverse(function (o) { sl.push(o); }); c.traverse(function (o) { cl.push(o); });
    var map = new Map(); sl.forEach(function (o, i) { map.set(o, cl[i]); });
    cl.forEach(function (o, i) {
      if (!o.isSkinnedMesh) return;
      var s = sl[i];
      o.bind(new THREE.Skeleton(s.skeleton.bones.map(function (b) { return map.get(b); }), s.skeleton.boneInverses), s.bindMatrix);
    });
    return c;
  }

  function makeRig() {
    var root = cloneRig(src), mesh = null, bones = {}, sk = {};
    root.traverse(function (o) { if (o.isSkinnedMesh) { sk[o.name] = o; o.frustumCulled = false; } if (o.isBone) bones[o.name.replace(/[.:\/\[\]]/g, '')] = o; });
    mesh = sk.TROOPER || Object.keys(sk).map(function (k) { return sk[k]; })[0];
    var R = { root: root, mesh: mesh, mech: sk.TROOPER_MECH || null, gl: sk.TROOPER_GL || null, type: '',
      muzzle: root.getObjectByName('TROOPER_MUZZLE'), glMuzzle: root.getObjectByName('TROOPER_GL_MUZZLE'), handL: bones['DEF-handL'],
      spine: [bones['DEF-spine001'], bones['DEF-spine002'], bones['DEF-spine003']], var: -1,
      neck: bones['DEF-neck'], head: bones['DEF-head'], arm: [bones['DEF-upper_armL'], bones['DEF-upper_armR']],
      fore: [bones['DEF-forearmL'], bones['DEF-forearmR']], thigh: [bones['DEF-thighL'], bones['DEF-thighR']],
      shin: [bones['DEF-shinL'], bones['DEF-shinR']], pYaw: null, mixer: new THREE.AnimationMixer(root), handR: bones['DEF-handR'], rl: null, rlId: '',
      low: {}, up: {}, one: {}, death: null, os: null, osT: 0, osDur: 0, r: null, t: 0, sink: 0 };
    mesh.material = mats[0]; if (R.mech) R.mech.visible = false; if (R.gl) R.gl.visible = false;
    Object.keys(clips.low).forEach(function (k) { var a = R.mixer.clipAction(clips.low[k]); a.play(); a.setEffectiveWeight(0); R.low[k] = a; });
    Object.keys(clips.up).forEach(function (k) { var a = R.mixer.clipAction(clips.up[k]); a.play(); a.setEffectiveWeight(0); R.up[k] = a; });
    Object.keys(clips.one).forEach(function (k) { var a = R.mixer.clipAction(clips.one[k]); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; R.one[k] = a; });
    if (clips.death) { R.death = R.mixer.clipAction(clips.death); R.death.setLoop(THREE.LoopOnce, 1); R.death.clampWhenFinished = true; }
    R.w = {}; R.root.visible = false; scene.add(root);
    TR.count++;
    return R;
  }
  // the rig's look for its robot: Soldier (kit colourway), Grenadier (same kit, launcher instead of the carbine) or
  // Robot Trooper (robot body in a colourway of its own); every mesh of one robot shares one flash uniform
  function dress(R, r) {
    var mech = r.type === 'mech' && R.mech, gren = r.type === 'grenadier' && R.gl, rl = r.type === 'rocketeer', n = mech ? TR.MECH_VARIANTS.length : TR.VARIANTS.length;
    var v = r.trVariant; if (v === undefined || v >= n) v = r.trVariant = (Math.random() * n) | 0;
    var key = (mech ? 'm' : gren ? 'g' : rl ? 'r' : 's') + v;
    if (!R.mats) R.mats = {};
    if (!R.mats[key]) {
      if (mech) R.mats[key] = [soldierMat(mats.mtex[v])];
      else if (gren) { var a = soldierMat(mats.tex[v], !!R.mesh.geometry.attributes.aMask); R.mats[key] = [a, soldierMat(mats.tex[v], false, { value: a.userData.fx })]; }
      else if (rl) { var b = soldierMat(mats.tex[v], !!R.mesh.geometry.attributes.aMask); R.mats[key] = [b, launcherMat({ value: b.userData.fx })]; }
      else R.mats[key] = [soldierMat(mats.tex[v])];
    }
    var M = R.mats[key];
    R.mesh.visible = !mech; if (R.mech) R.mech.visible = !!mech; if (R.gl) R.gl.visible = !!gren;
    if (mech) R.mech.material = M[0]; else R.mesh.material = M[0];
    if (gren) R.gl.material = M[1];
    R.fx = M[0].userData.fx; R.type = r.type;
    // the Rocket Soldier's launcher (one group per rig and launcher model, made on first use)
    if (R.rl) R.rl.visible = false;
    if (rl) {
      var id = r.launcher === 'murmur' ? 'murmur' : 'hothead';
      R.rls = R.rls || {};
      if (!R.rls[id]) R.rls[id] = makeLauncher(id);
      R.rl = R.rls[id]; R.rlId = id;
      if (R.rl) { R.rl.traverse(function (o) { if (o.isMesh) o.material = M[1]; }); if (R.rl.parent !== scene) scene.attach(R.rl); R.rl.visible = true; }
    } else { R.rl = null; R.rlId = ''; }
  }
  // a launcher group in launcher space (forward -Z, grip at the origin) at LAUNCHER_SCALE: body + cassette, muzzle node
  function makeLauncher(id) {
    var A = IB.Assets, K = 'WPN_' + id.toUpperCase();
    if (!A.geo[K]) return null;
    var g = new THREE.Group(), body = new THREE.Mesh(A.geo[K], null);
    body.frustumCulled = false; g.add(body);
    if (A.geo[K + '_Mag'] && A.node[K + '_MAG']) { var mg = new THREE.Mesh(A.geo[K + '_Mag'], null); mg.position.copy(A.node[K + '_MAG'].position); mg.frustumCulled = false; g.add(mg); }
    g.scale.setScalar(LAUNCHER_SCALE);
    g.userData.muzzle = A.node[K + '_MUZZLE'] ? A.node[K + '_MUZZLE'].position.clone() : new THREE.Vector3(0, 0.07, -0.4);
    g.userData.rest = new THREE.Vector3().fromArray(RL_REST[id]);
    g.visible = false; scene.add(g);
    return g;
  }
  /* the launcher's material: the weapons palette in the robots' look, sharing the soldier's flash / rogue uniform */
  function launcherMat(U) {
    var A = IB.Assets, m = IB.Render.toonMaterial({ map: A.palette.weapons, uni: IB.Render.robotOutline, baked: A.BAKED.weapons, look: 'actor', surf: IB.Surface && IB.Surface.surf('weapons') });
    var base = m.onBeforeCompile, key = m.customProgramCacheKey;
    m.onBeforeCompile = function (sh) {
      base(sh);
      sh.uniforms.uTrFx = U;
      sh.fragmentShader = sh.fragmentShader.replace('uniform vec3 uInk;', 'uniform vec3 uInk;\nuniform vec3 uTrFx;')
        .replace('if ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );',
          'gl_FragColor.rgb = mix( gl_FragColor.rgb, vec3( 1.0 ), uTrFx.x );\ngl_FragColor.rgb = mix( gl_FragColor.rgb, vec3( 0.07, 0.78, 0.71 ), uTrFx.y );\nif ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );');
    };
    m.customProgramCacheKey = function () { return key() + 'trl'; };
    return m;
  }
  /* carry (hand, low and forward) <-> shoulder (stock on the right shoulder, the tube along the aim) */
  var _lq = new THREE.Quaternion(), _lq2 = new THREE.Quaternion(), _le = new THREE.Euler(0, 0, 0, 'YXZ'), _lp = new THREE.Vector3(), _lp2 = new THREE.Vector3(), _lr = new THREE.Vector3();
  function placeLauncher(R, r, dt) {
    var g = R.rl; if (!g) return;
    var up = r.act === 'rl' && (r.state === 'windup' || r.state === 'attack' || (r.state === 'recover' && r.st < 0.45));
    r.shoulder = (r.shoulder || 0) + ((up ? 1 : 0) - (r.shoulder || 0)) * Math.min(1, dt * (up ? 7 : 4));
    var k = r.shoulder * r.shoulder * (3 - 2 * r.shoulder), yaw = r.yaw + Math.PI;
    // carry: grip in the right hand, tube level-ish and forward
    if (R.handR) R.handR.getWorldPosition(_lp); else _lp.set(r.x, r.y + 1.0, r.z);
    _le.set(-0.3, yaw, 0); _lq.setFromEuler(_le);
    // shoulder: the rest point on top of the right shoulder, tube along the aim (a little recoil kick)
    if (R.arm[1]) R.arm[1].getWorldPosition(_lp2); else _lp2.set(r.x, r.y + 1.45, r.z);
    _lp2.y += 0.1;
    _le.set(Math.max(-0.6, Math.min(0.6, r.aim || 0)) + (r.kick || 0) * 0.12, yaw, 0); _lq2.setFromEuler(_le);
    _lr.copy(g.userData.rest).multiplyScalar(LAUNCHER_SCALE).applyQuaternion(_lq2);
    _lp2.sub(_lr);
    g.position.copy(_lp).lerp(_lp2, k);
    g.quaternion.copy(_lq).slerp(_lq2, k);
    g.updateMatrixWorld(true);
    _lr.copy(g.userData.muzzle).applyMatrix4(g.matrixWorld);
    r.muzzleW = r.muzzleW || {}; r.muzzleW.x = _lr.x; r.muzzleW.y = _lr.y; r.muzzleW.z = _lr.z;
  }
  function take(r) {
    var R = TR.pool.pop() || makeRig();
    R.r = r; R.t = 0; R.sink = 0; R.os = null; R.root.visible = true; R.root.position.set(r.x, r.y, r.z);
    dress(R, r);
    if (R.death) R.death.stop();
    Object.keys(R.one).forEach(function (k) { R.one[k].stop(); });
    R.w = {};
    TR.live[r.type + r.slot] = R;
    return R;
  }
  function release(R) { R.root.visible = false; R.r = null; R.mixer.stopAllAction(); restart(R); if (R.rl) { if (R.rl.parent !== scene) scene.attach(R.rl); R.rl.visible = false; R.rl = null; } TR.pool.push(R); }
  function restart(R) {
    Object.keys(R.low).forEach(function (k) { R.low[k].play(); R.low[k].setEffectiveWeight(0); });
    Object.keys(R.up).forEach(function (k) { R.up[k].play(); R.up[k].setEffectiveWeight(0); });
  }

  TR.init = function (sc) {
    var A = IB.Assets, g = A.gltf && A.gltf.troopers;
    TR.ready = false; TR.live = {}; TR.pool = []; TR.dying = []; scene = sc;
    if (!g || !A.node.TROOPER_Rig) return;
    src = A.node.TROOPER_Rig; clips = prepClips(g.animations);
    var img = A.palette.troopers.image;
    mats = []; mats.tex = TR.VARIANTS.map(function (V, i) { return i === 0 ? A.palette.troopers : recolour(img, V.c); });
    mats.mtex = TR.MECH_VARIANTS.map(function (V, i) { return i === 0 ? A.palette.troopers : recolour(img, V.c, MKEYS); });
    mats.push(soldierMat(mats.tex[0]));
    A.node.TROOPER.geometry.computeBoundingSphere();
    // the troopers are drawn by this rig: their rigid parts never draw, the ink corpse is replaced by the death animation
    src.updateMatrixWorld(true);
    Object.keys(TR.TYPES).forEach(function (t) {
      var V = VIS[t]; if (!V) return;
      V.pose = function () {};
      // core (power cell on the back; the robot trooper's reactor) for weak-spot hits, measured on the rig
      var core = src.getObjectByName(t === 'mech' && src.getObjectByName('TROOPER_MECH_CORE') ? 'TROOPER_MECH_CORE' : 'TROOPER_CORE');
      if (core) { core.getWorldPosition(_v); src.worldToLocal(_v); V.coreY = _v.y; V.coreZ = _v.z; }
      // head: crit spot (a sphere around the head, 2x damage, damage number says CRIT); falls back to the standing height
      V.headY = Math.max(V.y1 || 1.88, 1.6) - 0.16; V.headR = 0.15; V.headZ = 0.02;
    });
    TR.ready = true;
  };

  function weight(R, act, key, target, rate, dt) {
    var w = R.w[key] === undefined ? 0 : R.w[key];
    w += (target - w) * Math.min(1, dt * rate);
    R.w[key] = w; act.setEffectiveWeight(w);
    return w;
  }
  // rotate a bone about a world axis (after the mixer): parent^-1 * Q * parent * local
  function turnBone(b, axis, ang) {
    if (!b || !ang) return;
    b.parent.getWorldQuaternion(_qp);
    _q.setFromAxisAngle(axis, ang);
    var inv = _qp.clone().invert();
    b.quaternion.premultiply(inv.multiply(_q).multiply(_qp));
    b.updateMatrixWorld(true);
  }
  function oneShot(R, key, speed) {
    var a = R.one[key]; if (!a) return;
    if (R.os && R.os !== a) R.os.fadeOut(0.12);
    a.reset(); a.timeScale = speed || 1; a.setEffectiveWeight(1); a.fadeIn(0.1); a.play();
    R.os = a; R.osT = 0; R.osDur = a.getClip().duration / (speed || 1);
  }

  function animate(R, r, dt) {
    var hs = Math.hypot(r.vx || 0, r.vz || 0), crouch = (r.crouch || 0) > 0.3 ? 1 : 0, back = r.legDir < 0;
    // legs: the cycle that matches the speed, played at a matching rate
    var wIdle = hs < 0.3 ? 1 : 0, wWalk = 0, wJog = 0, wSprint = 0;
    if (!wIdle) {
      if (hs < 2.0) wWalk = 1; else if (hs < 2.8) { wJog = (hs - 2.0) / 0.8; wWalk = 1 - wJog; } else if (hs < 5) wJog = 1; else wSprint = 1;
    }
    var sgn = back ? -1 : 1;
    if (R.low.walk) R.low.walk.timeScale = sgn * Math.max(0.6, hs / 1.5);
    if (R.low.jog) R.low.jog.timeScale = sgn * Math.max(0.7, hs / 3.4);
    if (R.low.sprint) R.low.sprint.timeScale = sgn * Math.max(0.8, hs / 5.6);
    if (R.low.cwalk) R.low.cwalk.timeScale = sgn * Math.max(0.6, hs / 1.4);
    var c = crouch, s = 1 - c;
    // dragged by a singularity: the stepping cycles give way to planted, dragging feet (the pulled layer below)
    var pl = r.pull || 0, keep = 1 - Math.min(1, pl * 1.25);
    wWalk *= keep; wJog *= keep; wSprint *= keep; wIdle = wIdle * keep + (1 - keep);
    weight(R, R.low.idle, 'idle', wIdle * s, 8, dt); weight(R, R.low.walk, 'walk', wWalk * s, 8, dt);
    weight(R, R.low.jog, 'jog', wJog * s, 8, dt); weight(R, R.low.sprint, 'sprint', wSprint * s, 8, dt);
    if (R.low.cidle) weight(R, R.low.cidle, 'cidle', wIdle * c, 8, dt);
    if (R.low.cwalk) weight(R, R.low.cwalk, 'cwalk', (1 - wIdle) * c, 8, dt);
    // upper body: low ready while it patrols; aiming (pitch blend) once it is in the fight
    var fight = r.state !== 'idle' && (r.seesPlayer || r.state === 'windup' || r.state === 'attack' || r.state === 'recover' || r.lost < 3);
    // one-shots: flinch on a stagger, rifle butt, grenade toss, a reload after some bursts
    if (r.state !== R.lastState) {
      if (r.state === 'stagger') oneShot(R, Math.random() < 0.5 ? 'hit' : 'hitH', 1.4);
      else if (r.state === 'windup' && r.act === 'melee') oneShot(R, 'punch', 1.5);
      else if (r.state === 'windup' && r.act === 'nade') oneShot(R, 'toss', 1.25);
      else if (r.state === 'recover' && R.lastAct === 'fire' && Math.random() < 0.35) oneShot(R, 'reload', 2.2);
      R.lastState = r.state;
    }
    R.lastAct = r.act;
    var osW = 0;
    if (R.os) { R.osT += dt; var left = R.osDur - R.osT; osW = Math.min(1, R.osT / 0.1, Math.max(0, left / 0.15)); R.os.setEffectiveWeight(osW); if (left <= 0) { R.os.stop(); R.os = null; osW = 0; } }
    var aim = r.aim || 0, up = Math.max(0, Math.min(1, aim / 0.6)), dn = Math.max(0, Math.min(1, -(aim + 0.05) / 0.6)), nt = Math.max(0, 1 - up - dn);
    var f = (fight ? 1 : 0) * (1 - osW) * keep, rd = (fight ? 0 : 1) * (1 - osW) * keep + (1 - keep) * (1 - osW);
    weight(R, R.up.ready, 'ready', rd, 6, dt);
    weight(R, R.up.aimN, 'aimN', f * nt, 10, dt); weight(R, R.up.aimU, 'aimU', f * up, 10, dt); weight(R, R.up.aimD, 'aimD', f * dn, 10, dt);
    R.mixer.update(dt);
    // the legs face the way it walks; the spine twists the chest back onto the aim, recoil kicks it
    var legRel = r.legRel || 0, yaw = r.yaw + legRel;
    if (pl > 0.01) { yaw = pullYaw(R, r, yaw, pl, dt); legRel *= 1 - pl; } else R.pYaw = null;
    R.root.rotation.set(0, yaw, 0);
    if (pl > 0.01) pullBody(R, r, pl, yaw);
    R.root.updateMatrixWorld(true);
    for (var i = 0; i < 3; i++) turnBone(R.spine[i], _ax, -legRel * (i === 2 ? 0.4 : 0.3));
    if (r.kick > 0.01) {
      _v.set(Math.cos(r.yaw), 0, -Math.sin(r.yaw));   // the soldier's right
      turnBone(R.spine[2], _v, -r.kick * 0.12);
    }
    if (pl > 0.01) pullLimbs(R, r, pl, yaw);
  }

  /* ---- the pulled layer (a Void can's singularity, gear.js: r.pull 0..1 eased, r.pullX / pullZ the core) ----
     The body is caught from behind: it turns (rate-limited, never spins) to brace with its back to the core, tips
     toward it from the feet, skips and lifts off the ground as the pull grows, its legs trail and kick, the spine
     arches and the head whips back, the arms flail forward grabbing for footing. All on top of the mixer's pose. */
  var _pd = new THREE.Vector3(), _pa = new THREE.Vector3(), _pr = new THREE.Vector3(), _pf = new THREE.Vector3();
  function wrapA(a) { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; }
  function pullDir(r) {
    var dx = (r.pullX === undefined ? r.x : r.pullX) - r.x, dz = (r.pullZ === undefined ? r.z : r.pullZ) - r.z, d = Math.hypot(dx, dz);
    if (d < 1e-3) { dx = -Math.sin(r.yaw); dz = -Math.cos(r.yaw); d = 1; }
    _pd.set(dx / d, 0, dz / d);
    _pa.set(_pd.z, 0, -_pd.x);   // up x (to the core): turning about it tips the top toward the core
    return _pd;
  }
  function pullYaw(R, r, yaw, pl, dt) {
    var d = pullDir(r), away = Math.atan2(d.x, d.z);   // forward (-sin, -cos) pointing away from the core
    // brace three-quarters away from the core on the side it already faces: a quarter turn at most, never a spin
    var off = wrapA(yaw - away), tgt = away + Math.max(-0.9, Math.min(0.9, off));
    if (R.pYaw === null) R.pYaw = yaw;
    var dl = wrapA(tgt - R.pYaw), mx = dt * 2.2;
    R.pYaw = wrapA(R.pYaw + Math.max(-mx, Math.min(mx, dl)));
    return yaw + wrapA(R.pYaw - yaw) * Math.min(1, pl * 1.4);
  }
  function pullBody(R, r, pl, yaw) {
    var t = r.pullT || 0, ph = r.slot * 1.3, air = Math.max(0, pl - 0.45) / 0.55;
    pullDir(r);
    // tip toward the core from the feet, rocking; airborne it tumbles a little further
    _q.setFromAxisAngle(_pa, pl * (0.26 + 0.05 * Math.sin(t * 7.1 + ph)) + air * 0.18);
    R.root.quaternion.premultiply(_q);
    _q.setFromAxisAngle(_pd, pl * 0.08 * Math.sin(t * 5.3 + ph)); R.root.quaternion.premultiply(_q);
    // skips off the ground, then floats
    R.root.position.y += pl * 0.05 * Math.abs(Math.sin(t * 8.4 + ph)) + air * air * (0.32 + 0.07 * Math.sin(t * 3.1 + ph));
  }
  function pullLimbs(R, r, pl, yaw) {
    var t = r.pullT || 0, ph = r.slot * 1.3, air = Math.max(0, pl - 0.45) / 0.55, i, sd;
    pullDir(r);
    _pr.set(Math.cos(yaw), 0, -Math.sin(yaw));   // the soldier's right
    _pf.set(-Math.sin(yaw), 0, -Math.cos(yaw));  // and forward
    // spine arches toward the core, the head lags and whips
    for (i = 0; i < 3; i++) turnBone(R.spine[i], _pa, pl * (0.07 + 0.02 * i) + pl * 0.03 * Math.sin(t * 9 + ph + i));
    turnBone(R.neck, _pa, pl * 0.1);
    turnBone(R.head, _pa, pl * (0.12 + 0.1 * Math.sin(t * 6.7 + ph)));
    for (i = 0; i < 2; i++) {
      sd = i ? 1 : -1;   // L, R
      // arms thrown up and out, clawing forward out of phase
      var claw = Math.sin(t * (10.5 + i * 1.7) + ph + i * 2.1);
      turnBone(R.arm[i], _pr, pl * (0.95 + 0.45 * claw));
      turnBone(R.arm[i], _pf, sd * pl * (0.45 + 0.2 * Math.sin(t * 7.9 + i * 1.3 + ph)));
      turnBone(R.fore[i], _pr, pl * (0.3 + 0.35 * Math.max(0, -claw)));
      // legs trail away from the core and kick for footing; airborne they hang and bicycle
      var kick = Math.sin(t * (8.2 + i * 0.9) + ph + i * Math.PI);
      turnBone(R.thigh[i], _pa, -pl * (0.22 + 0.25 * air) + pl * 0.28 * kick);
      turnBone(R.shin[i], _pr, -pl * (0.25 + 0.3 * air) * (0.6 + 0.4 * Math.max(0, kick)));
    }
  }

  TR.sync = function (dt) {
    if (!TR.ready) return;
    Object.keys(TR.TYPES).forEach(function (t) { syncType(t, dt); });
    // the fallen: the death animation, a moment on the ground, then it sinks away
    for (var i = TR.dying.length - 1; i >= 0; i--) {
      var D = TR.dying[i]; D.t += dt;
      D.mixer.update(dt);
      if (D.t > 2.4) { D.sink += dt * 0.7; D.root.position.y = D.y0 - D.sink; }
      D.root.updateMatrixWorld(true);
      if (D.t > 3.4) { TR.dying.splice(i, 1); release(D); }
    }
  };
  function syncType(t, dt) {
    var slots = AI.types[t] ? AI.types[t].slots : [];
    for (var s = 0; s < slots.length; s++) {
      var r = slots[s], id = t + s, R = TR.live[id];
      if (R && R.r !== r) { delete TR.live[id]; R = null; }
      if (!r.on) { if (R) { delete TR.live[id]; release(R); } continue; }
      if (!R) R = take(r);
      R.root.position.set(r.x, r.y, r.z);
      animate(R, r, dt);
      var fx = R.fx;
      fx.x = Math.min(1, (r.flash || 0) * 9) * 0.85;
      fx.y = r.rogue > 0 ? (r.rogue < 3 && Math.sin(r.rogue * 16) > 0 ? 0.25 : 0.55) : r.wet > 0 ? 0 : 0;
      R.root.updateMatrixWorld(true);
      var mz = t === 'grenadier' && R.glMuzzle ? R.glMuzzle : R.muzzle;
      if (t === 'rocketeer' && R.rl) { placeLauncher(R, r, dt); mz = null; }
      if (mz) { mz.getWorldPosition(_v); r.muzzleW = r.muzzleW || {}; r.muzzleW.x = _v.x; r.muzzleW.y = _v.y; r.muzzleW.z = _v.z; }
      if (R.handL) { R.handL.getWorldPosition(_v); r.handLW = r.handLW || {}; r.handLW.x = _v.x; r.handLW.y = _v.y; r.handLW.z = _v.z; }
    }
  }
  // a trooper went down: its rig plays the death and stays behind as the body
  TR.die = function (r) {
    var R = TR.live[r.type + r.slot]; if (!R || !R.death) return false;
    delete TR.live[r.type + r.slot];
    Object.keys(R.low).forEach(function (k) { R.low[k].fadeOut(0.15); });
    Object.keys(R.up).forEach(function (k) { R.up[k].fadeOut(0.15); });
    if (R.os) R.os.fadeOut(0.1);
    if (R.rl && R.handR) R.handR.attach(R.rl);   // the launcher falls with the hand
    R.death.reset(); R.death.timeScale = 1.25; R.death.setEffectiveWeight(1); R.death.fadeIn(0.1); R.death.play();
    R.fx.set(0, 0, 0);
    R.t = 0; R.sink = 0; R.y0 = r.fy || r.y || 0; R.r = null;
    TR.dying.push(R);
    return true;
  };
  TR.clear = function () {
    Object.keys(TR.live).forEach(function (s) { release(TR.live[s]); });
    TR.live = {};
    TR.dying.forEach(release); TR.dying = [];
  };

  // ---- hooks: after troops.js (which already wraps the AI runtime)
  var bInit = AI.init, bSync = AI.sync, bClear = AI.clear, bDespawn = AI.despawn, bKill = AI.kill;
  var _last = 0;
  AI.init = function (sc) { bInit.apply(AI, arguments); TR.init(sc); };
  AI.sync = function () {
    bSync.apply(AI, arguments);
    var now = performance.now(), dt = _last ? Math.min(0.1, (now - _last) / 1000) : 0.016; _last = now;
    if (IB.Game && IB.Game.paused) dt = 0;
    if (TR.ready) Object.keys(TR.TYPES).forEach(function (t) { var T = AI.types[t]; if (T) T.partList.forEach(function (P) { P.mesh.visible = false; }); });
    TR.sync(dt);
  };
  AI.clear = function () { bClear.apply(AI, arguments); TR.clear(); };
  AI.despawn = function () { bDespawn.apply(AI, arguments); TR.clear(); };
  AI.kill = function (r) {
    var soldier = r && r.on && TR.TYPES[r.type] && TR.ready;
    var x = r && r.x, z = r && r.z;
    bKill.apply(AI, arguments);
    if (!soldier) return;
    if (TR.die(r)) {   // no ink corpse: the rig is the body
      AI.types[r.type].corpses.forEach(function (c) { if (c.on && c.t === 0 && c.x === x && c.z === z) c.on = false; });
    }
  };
})(window.IB = window.IB || {});
