/* INKBOLT weapons: table-driven hitscan guns (semi/auto/burst), spread + recoil rules (5.2),
   reload/draw/holster, quick shove, and the first-person viewmodel: Blender arm clips blended here (W.play) with
   procedural handling on top (W.pose). Every viewmodel feel number is in VM_TUNE / VM_CLASS just below. */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var W = IB.Weapons = {};
  var D2R = Math.PI / 180;
  var FIRE_SND = { pistol: ['pip', 1], smg: ['buzz', 1], rifle: ['gun', 1.05], sniper: ['gun', 0.62], handcannon: ['gun', 0.78], twintap: ['pip', 1.12],
    whisk: ['buzz', 1.18], hornet: ['buzz', 0.9], longtom: ['gun', 0.82], brick: ['gun', 0.88], triplet: ['gun', 1.12],
    shotgun: ['gun', 0.66], scrapper: ['gun', 0.6], thunder: ['gun', 0.7], vanguard: ['gun', 0.92], railspike: ['gun', 1.3],
    hothead: ['rocket', 1.05], murmur: ['rocket', 0.82] };
  var _dir = new THREE.Vector3(), _right = new THREE.Vector3(), _up = new THREE.Vector3(), _fwd = new THREE.Vector3(), _piv = new THREE.Vector3();

  // =====================================================================================================================
  // VIEWMODEL MOTION TUNING. Everything that shapes how the arms and gun move on screen is in these two tables.
  // Units: metres and radians in viewmodel-camera space (+x right, +y up, +z toward the player; +rx muzzle up,
  // +rz rolls the top of the gun to the left), seconds, and springs as [frequency rad/s, damping ratio]
  // (a ratio under 1 overshoots and settles, 1 is critically damped, a higher frequency is a tighter spring).
  // None of these change gameplay: fire timing, reload lengths, throw release, aim zoom and hits live elsewhere.
  // =====================================================================================================================
  var VM_SCALE = 0.85;
  var VM_TUNE = {
    // gameplay timers (s), the values the game always had; the Draw / Holster clips are time-scaled to fit them
    drawTime: 0.3, holsterTime: 0.2,
    // crossfades (s) between arm clips. 'Far' variants are used when the arms come from an unrelated pose (a sprint,
    // a half-done reload); sprint-in takes the class fade (VM_CLASS.fade), sprint-out that times sprintOut
    fade: { loop: 0.14, slideIn: 0.14, slideOut: 0.18, sprintOut: 0.9, fire: 0.03, fireFar: 0.08, reload: 0.1, reloadFar: 0.16,
      shell: 0.04, shellIn: 0.2 /* into the first shell: the gun rolls right over */, holster: 0.07, holsterFar: 0.11, draw: 0 /* a cut: out of frame */, melee: 0 /* a cut: every swing clip starts out of frame */, throwNear: 0.06, throwFar: 0.11 },
    // look sway: the gun lags a turn, overshoots a little when the turn stops, and rolls into it
    sway: [13, 0.5], swayGain: 0.000011 /* m per px/s of look */, swayMaxX: 0.05, swayMaxY: 0.04, swayYaw: 1.6, swayPitch: 1.4, swayRoll: 1.1,
    // strafe lean and start / stop inertia (targets follow the local velocity / 6 m/s)
    strafe: [10, 0.55], strafeX: 0.012, strafeRoll: 0.055,
    move: [10, 0.5], moveZ: 0.014 /* pushed back while running forward */, moveY: 0.005 /* carried lower */, movePitch: 0.012,
    // jump and fall: the gun lags the vertical speed (dips at take-off, rises in the fall) and floats at the apex
    vert: [13, 0.55], vertGain: 0.0045 /* m per m/s */, vertMax: 0.04, vertPitch: 0.7 /* rad per m */, apexFloat: 0.008, apexSpeed: 3.5 /* |vy| under this floats */,
    // landing: one push from the impact speed, compress then settle
    land: [17, 0.42], landGain: 0.14 /* m/s of gun per m/s of impact */, landMin: 1, landMaxV: 2.4, landPitch: 0.9 /* rad per m */, landRoll: 0.45,
    landRate: 28 /* 1/s: the push arrives over a few frames, not in one */,
    // walk / sprint bob. Phase is player.bobT (distance moved): side sway once per two steps, bounce once per step
    bobX: 0.009, bobY: 0.01, bobPitch: 0.007, bobYaw: 0.008, bobRoll: 0.02, bobLag: 0.6 /* rad the bounce trails the footfall */, bobEase: 10 /* 1/s amplitude ease */,
    sprint: [12, 0.65], slide: [15, 0.5],
    // idle life: scale of the breathing + micro-sway mix (incommensurate sines, so it never visibly repeats)
    idle: 1, idleClipDrift: 0.14 /* the baked Idle loop's speed wanders by this much */,
    // aim down sights: share of look sway kept while aimed (position / rotation about the sight)
    adsSwayPos: 0.04, adsSwayRot: 0.35,
    // short dips that cover a change of clip, as [drop m, pitch rad, roll rad] at the peak (spring 'bump')
    bump: [15, 0.5],
    dip: { sprintIn: [-0.014, -0.03, 0.02], sprintOut: [-0.008, 0.02, -0.015], slideIn: [-0.02, 0.03, 0.04], reload: [-0.006, -0.012, 0.025],
      cancel: [-0.035, -0.06, 0.05], throwIn: [-0.008, 0, 0.02], drawEnd: [-0.004, -0.012, 0], meleeIn: [-0.012, 0, -0.03] },
    // holster / draw: how far the viewmodel is lowered on top of the Holster / Draw clips (at stow = 1), enough that the
    // gun is out of frame when the models swap but back in view within a few frames of the draw
    // (times VM_CLASS.stow: the launchers are big and need more)
    stowX: 0.02, stowY: -0.1, stowZ: 0, stowPitch: 0.1, stowRoll: 0.1, stowRise: 22 /* 1/s, a leftover stow clearing */,
    // melee exit: over the tail of a swing (after this fraction of it) the melee weapon drops out of frame for the gun
    meleeOut: 0.8, meleeDropY: -0.26, meleeDropPitch: -0.35, meleeDropRoll: 0.2,
    // fire kick: each shot pushes a slow 'return' spring (per class: kickFreq / kickDamp) and the gun snaps onto it
    kickSnap: [70, 0.6], kickYaw: 3 /* rad per m of side push */, kickCap: 3 /* most pushes that can pile up */,
    shove: [-0.045, -0.06]   // V with no melee weapon: punch forward [m, rad]
  };
  /* Per weapon class, layered on top of the Blender rig actions (the authored poses come from HANDLING in
     Source/blender/fam_weapons.py: pistols sprint at high ready, muzzle up by the face; long guns at low ready across
     the chest). A class missing here (or a key missing in it) takes its `base` row, then the 'rifle' value, so a new
     weapon gets sane handling from its cls alone. 'revolver' is used for def.action === 'revolver'.
       ads        eye distance (m) behind the sight point when aiming
       adsIn/Out  time (s) to bring the sight up / take it down (eased: fast start, soft landing)
       adsRoll    roll (rad) at the middle of the aim transition;  adsDip: drop (m) at the middle
       adsKeep    share of bob and move inertia kept while aimed
       sprintBob  walk-bob scale while sprinting; the pistol's high-ready action carries its own footfall bob near
                  the face, so it takes less on top
       sprintRoll share of the bob's roll kept while sprinting (a raised pistol rolling about the hip pivot swings wide)
       fade       crossfade (s) into the sprint loop (weight: heavier guns take longer to come up)
       hipX/Y/Z   extra hip-fire offset (m): the bulky launchers sit lower, further right and further out so they
                  don't fill the screen or cover the HUD (aiming still lines up the sight)
       weight     scales landing, jump and dip amounts (a heavy gun moves more and feels slower)
       stow       scales how far the gun is lowered for a swap (VM_TUNE.stow*)
       bob        walk-bob scale
       kickBack   push back per shot (m);  kickPitch: muzzle flip per shot (rad)
       kickRoll   random roll per shot (rad);  kickSide: random side push per shot (m)
       kickDrop   share of the push back that also drops the gun (shoved into the shoulder)
       kickFreq   return spring frequency (rad/s): low = a long heavy recovery;  kickDamp: its damping ratio */
  var VM_CLASS = {
    rifle: { ads: 0.29, adsIn: 0.22, adsOut: 0.2, adsRoll: 0.05, adsDip: 0.006, adsKeep: 0.1, sprintBob: 1.7, sprintRoll: 1, fade: 0.2,
      hipX: 0, hipY: 0, hipZ: 0, weight: 1, stow: 1, bob: 1,
      kickBack: 0.008, kickPitch: 0.014, kickRoll: 0.012, kickSide: 0.0025, kickDrop: 0.15, kickFreq: 15, kickDamp: 0.5 },
    pistol: { ads: 0.34, adsIn: 0.17, adsOut: 0.15, adsRoll: 0.035, sprintBob: 1.15, sprintRoll: 0.45, fade: 0.18, weight: 0.75,
      kickBack: 0.009, kickPitch: 0.04, kickRoll: 0.02, kickSide: 0.003, kickFreq: 17, kickDamp: 0.45 },
    revolver: { base: 'pistol', weight: 0.9, kickBack: 0.016, kickPitch: 0.075, kickRoll: 0.03, kickSide: 0.004, kickDrop: 0.2, kickFreq: 11, kickDamp: 0.5 },
    smg: { ads: 0.27, adsIn: 0.19, adsOut: 0.17, sprintBob: 1.6, fade: 0.16, weight: 0.85,
      kickBack: 0.0055, kickPitch: 0.01, kickRoll: 0.012, kickSide: 0.003, kickFreq: 17 },
    sniper: { ads: 0.13, adsIn: 0.27, adsOut: 0.22, adsRoll: 0.06, fade: 0.22, weight: 1.3,
      kickBack: 0.03, kickPitch: 0.055, kickRoll: 0.03, kickSide: 0.004, kickDrop: 0.3, kickFreq: 8.5, kickDamp: 0.55 },
    shotgun: { ads: 0.2, adsIn: 0.23, weight: 1.15,
      kickBack: 0.028, kickPitch: 0.055, kickRoll: 0.035, kickSide: 0.006, kickDrop: 0.3, kickFreq: 9.5 },
    rocket: { ads: 0.34, adsIn: 0.3, adsOut: 0.25, adsRoll: 0.07, hipX: 0.035, hipY: -0.03, hipZ: -0.16, weight: 1.5, stow: 2.2,
      kickBack: 0.03, kickPitch: 0.04, kickRoll: 0.045, kickSide: 0.006, kickDrop: 0.4, kickFreq: 7.5, kickDamp: 0.6 }
  };
  W.vmTune = VM_TUNE;   // live: change a value from the console (IB.Weapons.vmTune.bobY = 0.02) to try it
  var _vmc = {};
  // the merged row for a class (cached: do not change the object it returns)
  W.vmClass = function (cls) {
    if (_vmc[cls]) return _vmc[cls];
    var c = VM_CLASS[cls] || {}, b = c.base && VM_CLASS[c.base] || {}, r = VM_CLASS.rifle, out = {};
    Object.keys(r).forEach(function (k) { out[k] = c[k] !== undefined ? c[k] : (b[k] !== undefined ? b[k] : r[k]); });
    return (_vmc[cls] = out);
  };
  function vmOf(def) { return W.vmClass(def.action === 'revolver' ? 'revolver' : def.cls); }
  // viewmodel motion state (springs and blends), one per weapon state, made once
  function newMotion() {
    return { swx: 0, swxv: 0, swy: 0, swyv: 0, str: 0, strv: 0, fwd: 0, fwdv: 0, vert: 0, vertv: 0, land: 0, landv: 0, spv: 0, slv: 0,
      by: 0, byv: 0, bp: 0, bpv: 0, br: 0, brv: 0, landq: 0, bobA: 0, ads: 0, adsP: 1, adsDir: -1, stow: 0, stow0: 0, out: 0, air: 0, airVy: 0, spr: 0, sld: 0 };
  }
  function mo(s) { return s.vm || (s.vm = newMotion()); }
  // one semi-implicit step of a spring o[x] (velocity o[v]) toward target; f = [frequency, damping ratio]
  function spr(o, x, v, target, f, h) { o[v] += (f[0] * f[0] * (target - o[x]) - 2 * f[1] * f[0] * o[v]) * h; o[x] += o[v] * h; }
  // a short dip of the whole viewmodel (VM_TUNE.dip rows): it peaks at about the amounts given, then settles
  var BUMP_GAIN = VM_TUNE.bump[0] / 0.546;   // spring impulse -> peak displacement at damping 0.5
  function bump(s, d, k) { var m = mo(s); k = (k === undefined ? 1 : k) * BUMP_GAIN; m.byv += d[0] * k; m.bpv += d[1] * k; m.brv += d[2] * k; }

  // ---------------- viewmodel: Blender arms rig (22 bones) + weapon meshes from fps-weapons.glb ----------------
  W.init = function (vmScene) {
    var A = IB.Assets;
    W.vmRoot = new THREE.Group();
    vmScene.add(W.vmRoot);
    W.vmMat = IB.Render.toonMaterial({ uni: IB.Render.vmOutline, map: A.palette.weapons, baked: A.BAKED.weapons });
    W.vmSkinMat = IB.Render.toonMaterial({ uni: IB.Render.vmOutline, map: A.palette.weapons, baked: A.BAKED.weapons, skinning: true });
    // the arms, melee weapons and held items take the guns' tactical shading (src/game/gunskins.js)
    if (IB.GunSkins && IB.GunSkins.tactical) { IB.GunSkins.tactical(W.vmMat, IB.GunSkins.ARM_SURF); IB.GunSkins.tactical(W.vmSkinMat, IB.GunSkins.ARM_SURF); }
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
    // muzzle flash: layered flat comic star (ink rim, amber star, paper core) with side flares and a forward
    // cone, unlit, parented to the active weapon's MUZZLE socket; scaled per class, two frames (full, then smaller)
    function starGeo(n, r0, r1, jit) {
      var sh = new THREE.Shape();
      for (var i = 0; i <= n * 2; i++) { var a = i / (n * 2) * Math.PI * 2, r = (i % 2 ? r1 : r0) * (1 + (i % 4 === 0 ? jit : 0)); if (i === 0) sh.moveTo(Math.cos(a) * r, Math.sin(a) * r); else sh.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
      return new THREE.ShapeGeometry(sh);
    }
    // layers are merged into one geometry each (vertex colours, drawn in order with no depth test): 3 draw calls
    var _lm = new THREE.Matrix4(), _lc = new THREE.Color();
    function layers(list) {
      var geos = list.map(function (L) {
        var g = L[0].clone(); g.applyMatrix4(_lm.compose(new THREE.Vector3(0, 0, L[3] || 0), new THREE.Quaternion().setFromEuler(new THREE.Euler(L[4] || 0, L[5] || 0, L[6] || 0)), new THREE.Vector3(L[2][0], L[2][1], 1)));
        var n = g.attributes.position.count, c = new Float32Array(n * 3); _lc.set(L[1]);
        for (var i = 0; i < n; i++) { c[i * 3] = _lc.r; c[i * 3 + 1] = _lc.g; c[i * 3 + 2] = _lc.b; }
        g.setAttribute('color', new THREE.BufferAttribute(c, 3)); g.deleteAttribute('uv'); g.deleteAttribute('normal');
        return g;
      });
      var m = new THREE.Mesh(THREE.BufferGeometryUtils.mergeBufferGeometries(geos), new THREE.MeshBasicMaterial({ vertexColors: true, depthTest: false, depthWrite: false, side: THREE.DoubleSide }));
      m.renderOrder = 10; m.frustumCulled = false;
      return m;
    }
    var petal = new THREE.Shape(); petal.moveTo(0, 0); petal.quadraticCurveTo(0.07, 0.03, 0.16, 0); petal.quadraticCurveTo(0.07, -0.03, 0, 0);
    var pg = new THREE.ShapeGeometry(petal), ONE = [1, 1];
    W.flash = new THREE.Group();
    W.flashStar = layers([[starGeo(6, 0.12, 0.058, 0.18), PAL.ink, ONE], [starGeo(6, 0.095, 0.04, 0.18), PAL.amber, ONE], [starGeo(5, 0.05, 0.028, 0), PAL.paper, ONE]]);
    W.flash.add(W.flashStar);
    // side flares (rifles, SMGs, snipers, shotguns): two petals out to the sides
    W.flashSide = layers([[pg, PAL.ink, [1.12, 1.7]], [pg, PAL.ink, [1.12, 1.7], 0, 0, 0, Math.PI], [pg, PAL.amber, ONE], [pg, PAL.amber, ONE, 0, 0, 0, Math.PI]]);
    W.flashSide.renderOrder = 9; W.flash.add(W.flashSide);
    // a cone of fire forward along -z (seen edge-on from behind: a short spike)
    W.flashCone = layers([[pg, PAL.ink, [1.5, 2.2], 0.002, 0, Math.PI / 2, 0], [pg, PAL.amber, [1.4, 1.5], 0, 0, Math.PI / 2, 0]]);
    W.flashCone.renderOrder = 9; W.flash.add(W.flashCone);
    W.flashCore = W.flashStar;
    // rarity flash sets (Tuned and up): the amber layers in the tier's flash tint (core/gunskins.js FEEL)
    W.flashSets = { gray: [W.flashStar, W.flashSide, W.flashCone] };
    var FD = IB.GunSkinData;
    if (FD) ['green', 'blue', 'purple', 'orange'].forEach(function (t) {
      var tc = FD.FEEL[t].flash;
      var st = layers([[starGeo(6, 0.12, 0.058, 0.18), PAL.ink, ONE], [starGeo(6, 0.095, 0.04, 0.18), tc, ONE], [starGeo(5, 0.05, 0.028, 0), PAL.paper, ONE]]);
      var sd = layers([[pg, PAL.ink, [1.12, 1.7]], [pg, PAL.ink, [1.12, 1.7], 0, 0, 0, Math.PI], [pg, tc, ONE], [pg, tc, ONE, 0, 0, 0, Math.PI]]); sd.renderOrder = 9;
      var cn = layers([[pg, PAL.ink, [1.5, 2.2], 0.002, 0, Math.PI / 2, 0], [pg, tc, [1.4, 1.5], 0, 0, Math.PI / 2, 0]]); cn.renderOrder = 9;
      [st, sd, cn].forEach(function (o) { o.visible = false; W.flash.add(o); });
      W.flashSets[t] = [st, sd, cn];
    });
    W.flash.visible = false;
    // things the support hand holds (frag can for a throw, a shell while loading the pump gun) ride the HOLD_L socket
    // on the left hand bone (blender/fam_weapons.py hold_socket)
    W.held = {};
    var hold = rig.getObjectByName('HOLD_L');
    ['Frag', 'Shell'].forEach(function (n) {
      var src = A.node['HELD_' + n]; if (!hold || !src) return;
      var m = new THREE.Mesh(src.geometry, W.vmMat); m.frustumCulled = false; m.visible = false;
      if (n === 'Frag') m.scale.setScalar(0.75);   // read at arm's length right in front of the lens: a little smaller
      hold.add(m); W.held[n] = m;
    });
  };
  function showHeld(n, on) { var m = W.held && W.held[n]; if (m) m.visible = !!on; }
  // flash size per class (pistol 1); and which classes get side flares
  var FLASH_SCALE = { pistol: 0.95, smg: 1.0, rifle: 1.2, sniper: 1.55, shotgun: 1.7, rocket: 1.4, handcannon: 1.45 };
  var FLASH_SIDE = { smg: true, rifle: true, sniper: true, shotgun: true };
  var REV_FLASH = 1.35;   // revolver (def.action) shots: the flash is this much bigger on top of FLASH_SCALE
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
  function setFlash(tier) {
    var set = W.flashSets && (W.flashSets[tier] || W.flashSets.gray); if (!set || set[0] === W.flashStar) return;
    [W.flashStar, W.flashSide, W.flashCone].forEach(function (o) { o.visible = false; });
    W.flashStar = W.flashCore = set[0]; W.flashSide = set[1]; W.flashCone = set[2]; W.flashStar.visible = true;
  }
  // rarity skin (src/game/gunskins.js): checked every frame, so a tier upgrade shows at once
  function skinModel(id) {
    var m = W.models[id]; if (!m || !IB.GunSkins || IB.WEAPONS[id].cls === 'melee') return;
    var tier = IB.GunSkins.tierOf(id); if (m.tier === tier) return;
    var mat = IB.GunSkins.material(id, tier, IB.Render.vmOutline);
    m.tier = tier; IB.GunSkins.dress(m.mesh, mat, tier); IB.GunSkins.dress(m.mag, mat, tier);   // + its rarity layers
    setFlash(tier);
  }
  function showModel(id, on) {
    var m = W.models[id]; if (!m) return; m.mesh.visible = on; if (m.mag) m.mag.visible = on;
    if (on) skinModel(id);
    if (on && m.muzzle && IB.WEAPONS[id].cls !== 'melee') m.muzzle.add(W.flash);
  }

  // ---------------- arm animation (Blender actions <WEAPON>_<Action>) ----------------
  W.anim = function (s, name, opts) {
    opts = opts || {};
    var m = s.cur && W.models[s.cur]; if (!m) return;
    W.play(m.key, name, opts);
  };
  /* play <KEY>_<name> on the arms rig (KEY: a gun or a melee weapon); false when there is no such clip.
     opts: once, fade (s), timeScale.
     The blending is done here, not with three's crossFade (which restarts from full weight when a fade is cut short,
     so chained transitions pop): every clip on screen keeps a weight, the new clip eases from the weight it has to 1
     while the others ease to 0, and the weights always add up to 1 (animTick). A loop that is still on screen keeps
     its phase. A once-clip asked for again while it is still on screen (auto fire, the next shell) starts on a twin
     action, so the restart is a short blend and never a jump back to frame 0. */
  W.acts = []; W.fadeT = 0; W.fadeD = 0;
  W.play = function (key, name, opts) {
    opts = opts || {};
    var clip = W.clips[key + '_' + name]; if (!clip) return false;
    var acts = W.acts, act = W.mixer.clipAction(clip), fade = opts.fade === undefined ? VM_TUNE.fade.reload : opts.fade, i;
    var live = acts.indexOf(act) >= 0 && act.isScheduled();
    if (live && opts.once) {
      var twin = W.mixer.clipAction(clip._twin || (clip._twin = clip.clone()));
      var twinLive = acts.indexOf(twin) >= 0 && twin.isScheduled();
      if (!twinLive || twin._w < act._w) { act = twin; live = twinLive; }   // restart whichever shows less
    }
    if (!live || opts.once) act.reset();
    if (!live) act._w = 0;
    if (acts.indexOf(act) < 0) acts.push(act);
    act.enabled = true; act.paused = false;
    act.setLoop(opts.once ? THREE.LoopOnce : THREE.LoopRepeat, Infinity);
    act.clampWhenFinished = !!opts.once;
    act.timeScale = opts.timeScale || 1;
    act.play();
    if (!(fade > 0) || acts.length === 1) {   // nothing to blend from, or asked to cut
      for (i = acts.length - 1; i >= 0; i--) if (acts[i] !== act) { if (acts[i].isScheduled()) acts[i].stop(); acts[i]._w = 0; }
      acts.length = 0; acts.push(act); act._w = 1; W.fadeD = 0;
    } else { for (i = 0; i < acts.length; i++) acts[i]._w0 = acts[i]._w; W.fadeT = 0; W.fadeD = fade; }
    act._w0 = act._w; act.weight = act._w;
    W.action = act; W.animName = name; W.animOnce = !!opts.once;
    return true;
  };
  // ease the clip weights along the running crossfade; clips that reach 0 stop
  function animTick(dt) {
    var acts = W.acts, k = 1, i, a, w;
    if (W.fadeD > 0) { W.fadeT += dt; k = Math.min(1, W.fadeT / W.fadeD); k = k * k * (3 - 2 * k); if (k >= 1) W.fadeD = 0; }
    for (i = acts.length - 1; i >= 0; i--) {
      a = acts[i];
      if (a === W.action) { a._w = a.weight = a._w0 + (1 - a._w0) * k; continue; }
      w = a._w0 * (1 - k);
      if (w < 0.001 || !a.isScheduled()) { if (a.isScheduled()) a.stop(); a._w = 0; acts[i] = acts[acts.length - 1]; acts.pop(); }
      else a._w = a.weight = w;
    }
  }
  // the fade into a once-clip: short when the arms are already in the gun's two-hand hold, longer from anywhere else
  function fadeNear(near, far) { return W.animName === 'Idle' || W.animName === 'Fire' ? near : far; }

  // ---------------- state ----------------
  /* owned: array of weapon ids; fx: upgrade effects */
  W.create = function (owned, fx) {
    var s = { guns: {}, slots: {}, cur: null, state: 'idle', t: 0, next: 0, burst: 0, sinceShot: 9, shotsInRow: 0,
      recoilP: 0, recoilY: 0, kickZ: 0, kickZv: 0, kickR: 0, kickRv: 0, swayX: 0, swayY: 0, flashT: 0, reloadT: 0, drawT: 0,
      aim: 0, shoveT: 0, fx: fx || {}, triggerWas: false, pending: null, melee: null, throwing: null, combo: 0, comboT: 9,
      ammo: { rocket: 0 },   // shared ammo pools: every launcher draws on ammo.rocket (game/launchers.js keeps it saved)
      // viewmodel only: aimT is the aim the player wants (0 / 1), the kick* / k?T values are the fire-kick springs
      // (kickZ back m, kickR pitch rad, kickL roll rad, kickS side m; k?T the slow return spring each one follows)
      aimT: 0, kickL: 0, kickLv: 0, kickS: 0, kickSv: 0, kzT: 0, kzTv: 0, krT: 0, krTv: 0, klT: 0, klTv: 0, ksT: 0, ksTv: 0,
      kickW: VM_CLASS.rifle.kickFreq, kickD: VM_CLASS.rifle.kickDamp, vm: newMotion() };
    owned.forEach(function (id) { W.give(s, id); });
    return s;
  };
  // guns with a Blender model are playable: hitscan guns and the launchers (fire 'rocket'); not grenades, melee or the
  // old RL-1 Canister ('projectile', no model)
  W.playable = function (id) {
    var def = IB.WEAPONS[id]; if (!def || def.fire === 'throw' || def.fire === 'melee' || def.fire === 'projectile') return false;
    return !!IB.Assets.node['WPN_' + id.toUpperCase()];
  };
  // slots are loadout positions: keys 1..n switch between the carried guns in loadout order
  W.give = function (s, id) {
    if (!W.playable(id) || !model(id)) return;
    var def = IB.WEAPONS[id];
    s.guns[id] = { id: id, def: def, mag: W.magSize(s, def), reserve: (def.reserve === null || def.reserve === undefined || def.reserve === Infinity) ? Infinity : W.reserveOf(def) };
    sharePool(s, s.guns[id]);
    if (def.ammo) {   // launchers: the spare ammo is the shared pool (s.ammo.rocket), not per gun
      var pool = s.ammo || (s.ammo = {}), kind = def.ammo; if (!(pool[kind] >= 0)) pool[kind] = 0;
      Object.defineProperty(s.guns[id], 'reserve', { enumerable: true, get: function () { return pool[kind]; }, set: function (v) { pool[kind] = Math.max(0, v); } });
    }
    if (W.slotOf(s, id) < 0) { var n = 1; while (s.slots[n]) n++; s.slots[n] = id; }
  };
  W.slotOf = function (s, id) { for (var k in s.slots) if (s.slots[k] === id) return +k; return -1; };
  /* carry exactly `ids` (in key order). Guns leaving the loadout park their ammo in `bank` and guns joining it take
     theirs back from there, so swapping in the Tab menu never refills a magazine. */
  W.setLoadout = function (s, ids, bank) {
    bank = bank || {};
    Object.keys(s.guns).forEach(function (k) { bank[k] = { mag: s.guns[k].mag, reserve: s.guns[k].reserve }; });
    var cur = s.cur;
    s.guns = {}; s.slots = {};
    ids.forEach(function (id) { W.give(s, id); var b = bank[id], g = s.guns[id]; if (g && b) { g.mag = Math.min(b.mag, W.magSize(s, g.def)); if (g.def.ammo) g._fromBank = true; else if (g.reserve === Infinity) g.reserve = b.reserve;   /* shared type pools live on s.pool and carry over */ } });
    if (!s.guns[cur]) { var first = s.slots[1]; s.cur = null; if (first) W.equip(s, first, true); else Object.keys(W.models).forEach(function (k) { showModel(k, false); }); }
    return bank;
  };
  W.magSize = function (s, def) {
    if (def.ammo) return IB.Launchers && IB.Launchers.magOf ? IB.Launchers.magOf(def) : def.mag;   // a launcher's rolled magazine; no bench / skill bonus
    var base = def.mag, rr = (def.wyrm || def.magRange) && IB.WeaponDrops && IB.WeaponDrops.rollOf ? IB.WeaponDrops.rollOf(def.id) : null;   // Wyrmforged / rolled magazine
    if (rr && rr.mag) base = rr.mag;
    var m = IB.Upgrades ? IB.Upgrades.magSize(base, s.fx.magLevel || 0) : base;
    return s.fx.magMul && m !== Infinity ? Math.ceil(m * s.fx.magMul - 1e-9) : m;   // Overload skill
  };
  // player LV 20+: every gun type's spare ammo (reserve) holds a third more; magazines stay as they are (IB.AMMO_MUL, set by game.js from the player level)
  W.capped = function (m) { var k = IB.AMMO_MUL || 1; return m === Infinity || k === 1 ? m : Math.ceil(m * k - 1e-9); };
  W.reserveOf = function (def) { return W.capped(IB.Loadout && IB.Loadout.classReserve ? IB.Loadout.classReserve(def) : def.reserve); };
  // guns of one type share one reserve: g.reserve reads and writes s.pool[type]
  function sharePool(s, g) {
    var def = g.def; if (def.ammo || g.reserve === Infinity) return;
    s.pool = s.pool || {}; var c = def.cls; if (s.pool[c] === undefined) s.pool[c] = g.reserve; delete g.reserve;
    Object.defineProperty(g, 'reserve', { get: function () { return s.pool[c]; }, set: function (v) { s.pool[c] = v; }, enumerable: true, configurable: true });
  }
  // refill (respawn) and ammo boxes leave the launchers alone: rocket ammo only comes in rocket crates
  W.refill = function (s) { Object.keys(s.guns).forEach(function (k) { var g = s.guns[k]; if (g.def.ammo) return; g.mag = W.magSize(s, g.def); g.reserve = (g.def.reserve == null || g.def.reserve === Infinity) ? Infinity : W.reserveOf(g.def); }); };
  W.addAmmo = function (s, frac) { Object.keys(s.guns).forEach(function (k) { var g = s.guns[k]; if (g.reserve !== Infinity && !g.def.ammo) g.reserve = Math.min(IB.Loadout.reserveCap(g.def), g.reserve + Math.ceil(W.reserveOf(g.def) * frac)); }); };   // the same cap as ammoFull (shared type pool, LV 20 bonus)
  /* every gun that takes ammo boxes is at its reserve cap (an ammo box would add nothing) */
  W.ammoFull = function (s) {
    return IB.Loadout.ammoFull(s.guns);   // core/loadout.js
  };
  W.current = function (s) { return s.cur ? s.guns[s.cur] : null; };
  W.ownedSlots = function (s) { return Object.keys(s.slots).map(Number).sort(); };

  W.equip = function (s, id, instant) {
    if (!s.guns[id] || (s.cur === id && s.state !== 'holster')) return;
    var sw = s.fx.swapMul || 1, m = mo(s), T = VM_TUNE;   // Fast Fingers: quicker holster and draw
    if (s.cur && !instant) {
      // one sequenced move: the gun in hand is lowered out of frame (Holster clip + the procedural stow), then the
      // new one comes up. Asking for another gun while one is already going down only changes what comes up.
      if (s.melee) { s.cur = id; s.pending = null; return; }   // mid-swing: this gun comes out after it
      s.pending = id;
      if (s.state === 'holster') return;
      if (s.state === 'reload') { s._magIn = false; showHeld('Shell', false); }
      s.state = 'holster'; s.t = 0; m.stow0 = m.stow;
      W.anim(s, 'Holster', { once: true, fade: fadeNear(T.fade.holster, T.fade.holsterFar), timeScale: clipLen(s.cur, 'Holster', T.holsterTime) / (T.holsterTime * sw) });
      return;
    }
    Object.keys(W.models).forEach(function (k) { showModel(k, false); });
    showHeld('Shell', false);
    s.cur = id; s.state = 'draw'; s.t = 0; s.burst = 0; s.shotsInRow = 0; s.recoilP *= 0.5;
    showModel(id, true);
    if (instant) { s.state = 'idle'; m.stow = 0; W.anim(s, 'Idle', { fade: 0 }); }
    else { m.stow = 1; W.anim(s, 'Draw', { once: true, fade: T.fade.draw, timeScale: clipLen(id, 'Draw', T.drawTime) / (T.drawTime * sw) }); }   // starts out of frame
    IB.Audio && IB.Audio.play('draw');
  };
  // length (s) of a gun's clip, or `dflt` when it has none
  function clipLen(id, name, dflt) { var md = W.models[id], c = md && W.clips[md.key + '_' + name]; return c ? c.duration : dflt; }
  W.slot = function (s, n) { if (s.slots[n]) W.equip(s, s.slots[n]); };
  W.cycle = function (s, dir) {
    var sl = W.ownedSlots(s); if (sl.length < 2) return;
    var curSlot = W.slotOf(s, s.cur), i = sl.indexOf(curSlot);
    W.slot(s, sl[(i + dir + sl.length) % sl.length]);
  };
  W.reload = function (s) {
    var g = W.current(s); if (!g || s.state !== 'idle') return;
    if (g.mag >= W.magSize(s, g.def) || g.reserve < (g.def.ammoPer || 1)) return;
    s.state = 'reload'; s.t = 0; s.reloadT = g.def.reload * (s.fx.reloadMul || 1); s.burst = 0; s._magIn = false;
    var rc = W.clips[W.models[s.cur].key + '_Reload'];
    W.anim(s, 'Reload', { once: true, fade: g.def.reloadPerShell ? VM_TUNE.fade.shellIn : fadeNear(VM_TUNE.fade.reload, VM_TUNE.fade.reloadFar), timeScale: rc ? rc.duration / s.reloadT : 1 });   // Fast Fingers rescales the clip
    bump(s, VM_TUNE.dip.reload, vmOf(g.def).weight);
    IB.Audio && IB.Audio.play(g.def.reloadPerShell ? 'magIn' : 'magOut', g.def.reloadPerShell ? { pitch: 1.3, gain: 0.7 } : undefined);
  };
  W.busy = function (s) { return !!(s.melee || s.throwing); };

  // ---------------- melee (V): the gun goes away for one swing of the melee weapon, then comes back ----------------
  /* id: melee weapon id. Swings chain into a combo (each swing plays the next clip) when V comes again inside the
     weapon's comboWindow. ctx.melee(def, comboIndex, hitNo) is called when a blow lands. */
  // V cuts into a reload, a draw or a holster (the swap finishes after the swing); never into another swing or a throw
  W.meleeReady = function (s) { return !s.melee && !s.throwing; };
  W.meleeStart = function (s, id) {
    var def = IB.WEAPONS[id], m = def && model(id);
    if (!m || !W.meleeReady(s)) return false;
    if (s.state === 'reload') { s.state = 'idle'; s._magIn = false; showHeld('Shell', false); bump(s, VM_TUNE.dip.cancel, 0.6); }
    if (s.state === 'holster' && s.pending) { s.cur = s.pending; s.pending = null; }   // the swap target comes out after the swing
    s.state = 'idle';
    var clips = def.clips || ['Strike'];
    s.combo = s.comboT < (def.comboWindow || 0.5) ? (s.combo + 1) % clips.length : 0;
    var dur = W.clips[m.key + '_' + clips[s.combo]] ? W.clips[m.key + '_' + clips[s.combo]].duration : def.swing;
    Object.keys(W.models).forEach(function (k) { showModel(k, false); });
    showModel(id, true);
    // the arms blend into the swing over a few frames (hit timing unchanged: the clip runs from its start) with a
    // short dip on top; a viewmodel still lowered from a swap or the last swing comes up with the strike (W.pose)
    W.play(m.key, clips[s.combo], { once: true, fade: VM_TUNE.fade.melee, timeScale: dur / (def.swing / (s.fx.meleeRate || 1)) });
    bump(s, VM_TUNE.dip.meleeIn);
    s.melee = { id: id, def: def, t: 0, dur: def.swing / (s.fx.meleeRate || 1), hits: 0, combo: s.combo };
    s.burst = 0; s.aim = 0; s.aimT = 0;
    IB.Audio && IB.Audio.play('shove', { pitch: id === 'eaxe' ? 0.7 : id === 'dagger' ? 1.35 : 1.05, gain: 1.1 });
    return true;
  };
  function meleeUpdate(s, dt, ctx) {
    var mm = s.melee; mm.t += dt;
    var f = mm.t / mm.dur, d = mm.def;
    if (mm.hits === 0 && f >= d.hit) { mm.hits = 1; if (ctx.melee) ctx.melee(d, mm.combo, 0); }
    if (mm.hits === 1 && d.hit2 && f >= d.hit2) { mm.hits = 2; if (ctx.melee) ctx.melee(d, mm.combo, 1); }
    if (mm.t >= mm.dur) {
      s.melee = null; s.comboT = 0;
      showModel(mm.id, false);
      var cur = s.cur; s.cur = null;
      if (cur) W.equip(s, cur, false);   // the gun is drawn again
    }
  }

  // ---------------- grenade (G): the support hand throws a frag can while the gun dips ----------------
  // the throw clip is generated per gun (<GUN>_Throw, 0.62 s, release at 52 %): ctx.onThrow() spawns the grenade
  var THROW_RELEASE = 0.52, THROW_SHOW = 0.16;
  W.throwStart = function (s) {
    var g = W.current(s); if (!g || s.melee || s.throwing || s.state === 'holster') return false;
    if (s.state === 'draw') s.state = 'idle';
    var cancel = s.state === 'reload';
    if (cancel) { s.state = 'idle'; s._magIn = false; showHeld('Shell', false); }
    var key = W.models[s.cur].key, clip = W.clips[key + '_Throw'];
    // the frag shows at 16 % of the clip, so the blend in stays shorter than that
    W.play(key, 'Throw', { once: true, fade: fadeNear(VM_TUNE.fade.throwNear, VM_TUNE.fade.throwFar) });
    bump(s, cancel ? VM_TUNE.dip.cancel : VM_TUNE.dip.throwIn, cancel ? 0.7 : 1);
    s.throwing = { t: 0, dur: clip ? clip.duration : 0.62, released: false };
    s.burst = 0;
    return true;
  };
  function throwUpdate(s, dt, ctx) {
    var th = s.throwing; th.t += dt;
    var f = th.t / th.dur;
    showHeld('Frag', f >= THROW_SHOW && !th.released);
    if (!th.released && f >= THROW_RELEASE) { th.released = true; showHeld('Frag', false); if (ctx.onThrow) ctx.onThrow(); IB.Audio && IB.Audio.play('shove', { pitch: 1.4, gain: 0.8 }); }
    if (th.t >= th.dur) s.throwing = null;
  }

  /* Epic (purple) and Legendary (orange) pistols and shotguns are tuned up: a faster fire rate; shotguns also fire more
     pellets (damage per pellet unchanged, so more damage per shot) in a wider cone. {rate, pellets, spread} multipliers. */
  var TIER_MODS = { purple: { rate: 1.15, pellets: 1.25, spread: 1.2 }, orange: { rate: 1.3, pellets: 1.5, spread: 1.4 } };
  W.tierMods = function (d) {
    var out = { rate: 1, pellets: 1, spread: 1 };
    if (!d || (d.cls !== 'pistol' && d.cls !== 'shotgun') || !IB.WeaponDrops) return out;
    var m = TIER_MODS[IB.WeaponDrops.tierOf(d.id).id]; if (!m) return out;
    out.rate = m.rate; if (d.cls === 'shotgun') { out.pellets = m.pellets; out.spread = m.spread; }
    return out;
  };
  // spread cone half-angle (deg) right now
  W.spread = function (s, player) {
    var g = W.current(s); if (!g) return 0;
    var d = g.def, base = (s.aim > 0.5 ? d.spreadAim : d.spreadHip) * (s.fx.spreadMul || 1) * W.tierMods(d).spread;
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
    // fire-kick springs: each shot pushes the slow return springs (k?T, tuned per class), which swing back to rest
    // with a little overshoot, and the gun (kick?) snaps onto them: a fast snap back, a slower springy return, and in
    // auto fire the pushes pile up into a steady shake around a held-back pose
    // (sub-stepped: one long frame must not blow the explicit springs up, e.g. a launcher's big kick on a slow phone)
    if (s.kzT === undefined) { s.kickL = s.kickLv = s.kickS = s.kickSv = s.kzT = s.kzTv = s.krT = s.krTv = s.klT = s.klTv = s.ksT = s.ksTv = 0; s.kickW = VM_CLASS.rifle.kickFreq; s.kickD = VM_CLASS.rifle.kickDamp; }
    var kdt = Math.min(dt, 0.1), kw = s.kickW * s.kickW, kc = 2 * s.kickD * s.kickW, ks = VM_TUNE.kickSnap, ksw = ks[0] * ks[0], ksc = 2 * ks[1] * ks[0];
    for (var sn = Math.max(1, Math.ceil(kdt / 0.008)), sh = kdt / sn, si = 0; si < sn; si++) {
      s.kzTv -= (kw * s.kzT + kc * s.kzTv) * sh; s.kzT += s.kzTv * sh; s.kickZv += (ksw * (s.kzT - s.kickZ) - ksc * s.kickZv) * sh; s.kickZ += s.kickZv * sh;
      s.krTv -= (kw * s.krT + kc * s.krTv) * sh; s.krT += s.krTv * sh; s.kickRv += (ksw * (s.krT - s.kickR) - ksc * s.kickRv) * sh; s.kickR += s.kickRv * sh;
      s.klTv -= (kw * s.klT + kc * s.klTv) * sh; s.klT += s.klTv * sh; s.kickLv += (ksw * (s.klT - s.kickL) - ksc * s.kickLv) * sh; s.kickL += s.kickLv * sh;
      s.ksTv -= (kw * s.ksT + kc * s.ksTv) * sh; s.ksT += s.ksTv * sh; s.kickSv += (ksw * (s.ksT - s.kickS) - ksc * s.kickSv) * sh; s.kickS += s.kickSv * sh;
    }
    s.comboT += dt;
    if (s.melee) { meleeUpdate(s, dt, ctx); p.aiming = false; s.aimT = 0; s.aim = Math.max(0, s.aim - dt * 14); return; }
    if (s.throwing) throwUpdate(s, dt, ctx);
    var wantAim = inp.aim && s.state !== 'reload' && !p.sprinting && !s.throwing;
    s.aimT = wantAim ? 1 : 0;   // W.pose eases the gun to the sights from this; s.aim stays the gameplay value (zoom, spread)
    s.aim += ((wantAim ? 1 : 0) - s.aim) * Math.min(1, dt * 14);
    p.aiming = s.aim > 0.5;
    if (!g) return;
    p.weaponMoveMul = g.def.moveMul || 1;
    switch (s.state) {
      case 'holster':
        if (s.t >= VM_TUNE.holsterTime * (s.fx.swapMul || 1)) { var nid = s.pending; s.pending = null; showModel(s.cur, false); s.cur = null; W.equip(s, nid, false); }
        return;
      case 'draw':
        if (s.t >= VM_TUNE.drawTime * (s.fx.swapMul || 1)) { s.state = 'idle'; bump(s, VM_TUNE.dip.drawEnd, vmOf(g.def).weight); }   // the gun settles into the hands
        return;
      case 'reload':
        if (g.def.reloadPerShell) {
          // one shell per cycle (the clip loops); fire with a shell in the tube stops loading
          showHeld('Shell', s.t >= s.reloadT * 0.22 && s.t < s.reloadT * 0.72);
          if (inp.firePressed && g.mag > 0) { s.state = 'idle'; showHeld('Shell', false); bump(s, VM_TUNE.dip.cancel, 0.5); break; }
          if (s.t >= s.reloadT) {
            g.mag++; if (g.reserve !== Infinity) g.reserve--;
            IB.Audio && IB.Audio.play('magIn', { pitch: 1.3, gain: 0.7 });
            showHeld('Shell', false);
            if (g.mag < W.magSize(s, g.def) && g.reserve > 0) { s.t = 0; W.anim(s, 'Reload', { once: true, fade: VM_TUNE.fade.shell, timeScale: (W.clips[W.models[s.cur].key + '_Reload'].duration) / s.reloadT }); }
            else { s.state = 'idle'; IB.Audio && IB.Audio.play('slide'); }
          }
          return;
        }
        if (s.t >= s.reloadT * 0.55 && !s._magIn) { s._magIn = true; IB.Audio && IB.Audio.play('magIn'); }
        if (s.t >= s.reloadT) {
          s._magIn = false;
          var per = g.def.ammoPer || 1, need = W.magSize(s, g.def) - g.mag, take = Math.min(need, Math.floor(g.reserve / per));   // a Murmur salvo takes 2 rockets
          g.mag += take; if (g.reserve !== Infinity) g.reserve -= take * per;
          s.state = 'idle'; IB.Audio && IB.Audio.play('slide');
        }
        return;
    }
    if (p.sprinting || s.throwing) { s.burst = 0; return; }
    var d = g.def;
    var trig = d.fire === 'auto' ? inp.fire : inp.firePressed;
    var rm = (s.fx.rateMul || 1) * W.tierMods(d).rate;   // Rapid skill + Epic / Legendary pistols and shotguns: shorter gaps between shots
    if (s.burst > 0 && s.next <= 0) { fire(s, g, ctx); s.burst--; s.next = (s.burst > 0 ? (d.burstGap || 60 / d.rpm) : Math.max(0, d.cycle - (d.burst - 1) * (d.burstGap || 60 / d.rpm))) / rm; return; }
    if (trig && s.next <= 0 && s.burst === 0) {
      if (g.mag <= 0) { if (inp.firePressed) IB.Audio && IB.Audio.play('dry'); W.reload(s); return; }
      if (d.burst > 1) { s.burst = d.burst; s.next = 0; fire(s, g, ctx); s.burst--; s.next = (d.burstGap || 60 / d.rpm) / rm; }
      else { fire(s, g, ctx); s.next = (d.cycle || 60 / d.rpm) / rm; }
    }
  };

  function fire(s, g, ctx) {
    if (g.mag <= 0) { s.burst = 0; return; }
    var d = g.def, p = ctx.player, cam = ctx.cam;
    // Torpedo (endgame): the last round of a magazine, fired with 1 left, is a torpedo; guns and rocket launchers, not grenades
    var torpedo = g.mag === 1 && s.fx && s.fx.torpedo && d.cls !== 'grenade' && d.cls !== 'melee' && ctx.torpedo;
    g.mag--;
    var spread = W.spread(s, p) * D2R;
    s.sinceShot = 0; s.shotsInRow++;
    cam.getWorldDirection(_fwd);
    _right.set(1, 0, 0).applyQuaternion(cam.quaternion); _up.set(0, 1, 0).applyQuaternion(cam.quaternion);
    if (torpedo) ctx.torpedo(d, cam, spread);   // game/launchers.js flies the torpedo
    else if (d.fire === 'rocket' && ctx.rocket) ctx.rocket(d, cam, spread);   // launchers: game/launchers.js flies the rockets
    else for (var k = 0, np = Math.round((d.pellets || 1) * W.tierMods(d).pellets); k < np; k++) {
      var a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * Math.tan(spread);
      _dir.copy(_fwd).addScaledVector(_right, Math.cos(a) * r).addScaledVector(_up, Math.sin(a) * r).normalize();
      ctx.shoot(cam.position, _dir, d, k);
    }
    // recoil: climbs over the first 6 shots of auto weapons
    var climb = d.fire === 'auto' ? 0.55 + 0.45 * Math.min(1, (s.shotsInRow - 1) / 5) : 1;
    var rec = d.recoil * (s.fx.recoilMul || 1) * climb * (s.aim > 0.5 ? 0.75 : 1);
    s.recoilP += rec * D2R;
    s.recoilY += (Math.random() * 2 - 1) * (d.recoilH || 0) * (s.fx.recoilMul || 1) * D2R;
    // viewmodel kick, shaped per class (VM_CLASS kick*; a revolver, def.action, has its own heavier row): a push
    // back and a muzzle flip onto the return springs plus a random roll and side push, so no two shots look the same.
    // Auto fire starts at 55 % and builds with the recoil climb. The bigger revolver flash is in W.pose.
    var rev = d.action === 'revolver', vc = vmOf(d), km = climb * Math.min(1.25, s.fx.recoilMul || 1), cap = VM_TUNE.kickCap;
    s.kzT = Math.min(s.kzT + vc.kickBack * km, vc.kickBack * cap); s.krT = Math.min(s.krT + vc.kickPitch * km, vc.kickPitch * cap);
    s.klT += (Math.random() < 0.5 ? -1 : 1) * (0.4 + 0.6 * Math.random()) * vc.kickRoll * km;
    s.ksT += (Math.random() < 0.5 ? -1 : 1) * (0.4 + 0.6 * Math.random()) * vc.kickSide * km;
    s.klT = Math.max(-vc.kickRoll * 2, Math.min(vc.kickRoll * 2, s.klT)); s.ksT = Math.max(-vc.kickSide * 2, Math.min(vc.kickSide * 2, s.ksT));
    s.kickW = vc.kickFreq; s.kickD = vc.kickDamp;
    s.flashT = 0.055; s.flashCls = d.id === 'handcannon' ? 'handcannon' : d.cls; s.flashRev = rev;
    // the Fire clip: a short blend from the two-hand hold (and from the last shot's clip: see W.play), a longer one
    // when the shot cuts into a sprint, slide or shell reload
    W.anim(s, 'Fire', { once: true, fade: fadeNear(VM_TUNE.fade.fire, VM_TUNE.fade.fireFar) });
    if (IB.Boom) IB.Boom.onFire(s, d);   // shell casing from the EJECT socket, muzzle smoke
    // layered shot per class; heavier guns pitch down, light ones up (+/-4% random per shot)
    var snd = FIRE_SND[d.id] || FIRE_SND[d.cls] || ['gun', 1];
    // rarer guns: a touch deeper and punchier, Epic / Legendary with a bright ring on top (core/gunskins.js FEEL)
    var feel = IB.GunSkins && IB.GunSkins.feel(IB.GunSkins.tierOf(d.id)) || { pitch: 1, gain: 1, ring: 0 };
    IB.Audio && IB.Audio.play(snd[0], { pitch: snd[1] * feel.pitch * (1 + (Math.random() * 0.08 - 0.04)), gain: feel.gain });
    if (feel.ring && IB.Audio) IB.Audio.play('pip', { pitch: 1.9 + Math.random() * 0.1, gain: feel.ring });
    if (ctx.onFire) ctx.onFire(d);
  }

  // quick shove with V when no melee weapon is equipped (20 damage)
  W.shove = function (s) {
    if (s.shoveT > 0) return false;
    s.shoveT = 0.5; s.kzT = (s.kzT || 0) + VM_TUNE.shove[0]; s.krT = (s.krT || 0) + VM_TUNE.shove[1];   // the gun punches forward on the kick springs
    return true;
  };

  // world-space muzzle point approximation for tracers
  W.muzzleWorld = function (cam, out) {
    _right.set(1, 0, 0).applyQuaternion(cam.quaternion); _up.set(0, 1, 0).applyQuaternion(cam.quaternion); cam.getWorldDirection(_fwd);
    return out.copy(cam.position).addScaledVector(_right, 0.16).addScaledVector(_up, -0.13).addScaledVector(_fwd, 0.55);
  };

  // ---------------- viewmodel placement ----------------
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
  /* Place the viewmodel for this frame: lookDX/DY (pixels this frame) for sway, player for bob / sprint / jump, t the
     clock for idle life. Numbers: VM_TUNE / VM_CLASS at the top of the file.
     The arm clips give the poses (W.play); on top the root gets, all on damped springs or eased blends so nothing
     steps: look sway with overshoot and roll, strafe lean, start / stop inertia, a distance-phased walk bob (bounce
     at twice the side-to-side rate), jump lag with a float at the apex, a landing push from the impact speed, the
     aim-down-sights blend (eased, exact on the sight point, rotations about the sight while aimed), the fire-kick
     springs (stepped in W.update), short dips that cover clip changes (bump) and the stow that takes the viewmodel
     out of frame for a swap. dt <= 0 is a frozen review frame (tests/e2e/viewmodel-shots.js): the settled pose. */
  W.pose = function (s, dt, player, lookDX, lookDY, headBob, t) {
    var g = W.current(s), T = VM_TUNE, vc = g ? vmOf(g.def) : W.vmClass('rifle'), m = mo(s), wg = vc.weight;
    if (s.melee) g = null;   // melee swing: the arms play the swing clip; no gun handling, no flash
    var live = dt > 0, hs = Math.hypot(player.vx, player.vz), cy = Math.cos(player.yaw), sy = Math.sin(player.yaw);
    var right = player.vx * cy - player.vz * sy, ahead = -(player.vx * sy + player.vz * cy);   // local velocity (m/s)
    var ground = !!player.onGround, sprinting = !!player.sprinting, sliding = !!player.sliding;
    var moveT = ground && !sliding ? Math.min(1, hs / 6) : 0, sw = s.fx.swapMul || 1, u, i;
    if (s.sprintK === undefined) { s.sprintK = 0; s.slideK = 0; }
    if (!live) {
      // frozen frame: every spring at rest, the blends on their targets
      m.swx = m.swxv = m.swy = m.swyv = m.str = m.strv = m.fwd = m.fwdv = m.vert = m.vertv = m.land = m.landv = m.spv = m.slv = 0;
      m.by = m.byv = m.bp = m.bpv = m.br = m.brv = m.landq = m.stow = m.out = 0; m.bobA = moveT; m.ads = s.aim; m.adsP = 1; m.adsDir = s.aim > 0.5 ? 1 : -1;
      m.air = 0; m.spr = sprinting ? 1 : 0; m.sld = sliding ? 1 : 0;
    } else {
      // events: landing (one push, scaled by how fast the player came down), sprint and slide entries
      if (ground && m.air && -m.airVy > T.landMin) m.landq += Math.min(T.landMaxV, -m.airVy * T.landGain) * wg;
      u = m.landq * Math.min(1, dt * T.landRate); m.landq -= u; m.landv -= u;
      if (!ground) m.airVy = player.vy;
      m.air = ground ? 0 : 1;
      if (sprinting !== !!m.spr) { m.spr = sprinting ? 1 : 0; if (!s.melee) bump(s, sprinting ? T.dip.sprintIn : T.dip.sprintOut, wg); }   // anticipation dip, settle
      if (sliding !== !!m.sld) { m.sld = sliding ? 1 : 0; if (sliding) bump(s, T.dip.slideIn, wg); }
      // spring targets
      var lx = Math.max(-T.swayMaxX, Math.min(T.swayMaxX, -lookDX / dt * T.swayGain)), ly = Math.max(-T.swayMaxY, Math.min(T.swayMaxY, lookDY / dt * T.swayGain));
      var vT = Math.max(-T.vertMax, Math.min(T.vertMax, -player.vy * T.vertGain));
      if (!ground) vT += T.apexFloat * Math.max(0, 1 - Math.abs(player.vy) / T.apexSpeed);   // weightless at the top of a jump
      var sT = Math.max(-1.5, Math.min(1.5, right / 6)), fT = Math.max(-1.5, Math.min(1.5, ahead / 6));
      var n = Math.min(4, Math.max(1, Math.ceil(dt / 0.0167))), h = Math.min(dt, 0.066) / n;
      for (i = 0; i < n; i++) {
        spr(m, 'swx', 'swxv', lx, T.sway, h); spr(m, 'swy', 'swyv', ly, T.sway, h);
        spr(m, 'str', 'strv', sT, T.strafe, h); spr(m, 'fwd', 'fwdv', fT, T.move, h);
        spr(m, 'vert', 'vertv', vT * wg, T.vert, h); spr(m, 'land', 'landv', 0, T.land, h);
        spr(m, 'by', 'byv', 0, T.bump, h); spr(m, 'bp', 'bpv', 0, T.bump, h); spr(m, 'br', 'brv', 0, T.bump, h);
        m.spv += (T.sprint[0] * T.sprint[0] * ((sprinting ? 1 : 0) - s.sprintK) - 2 * T.sprint[1] * T.sprint[0] * m.spv) * h; s.sprintK += m.spv * h;
        m.slv += (T.slide[0] * T.slide[0] * ((sliding ? 1 : 0) - s.slideK) - 2 * T.slide[1] * T.slide[0] * m.slv) * h; s.slideK += m.slv * h;
      }
      m.bobA += (moveT - m.bobA) * Math.min(1, dt * T.bobEase);   // bob amplitude eases, so a jump or a slide never cuts it
      // aim: eased each way along 1 - (1 - p^1.5)^3 (off the mark in a frame or two, fast through the middle, a soft
      // landing exactly on the sight); a change of mind picks up from where the gun is
      var dir = s.aimT && g ? 1 : -1;
      if (dir !== m.adsDir) { m.adsDir = dir; m.adsP = Math.pow(1 - Math.pow(dir > 0 ? 1 - m.ads : m.ads, 1 / 3), 2 / 3); }
      if (m.adsP < 1) { m.adsP = Math.min(1, m.adsP + dt / (dir > 0 ? vc.adsIn : vc.adsOut)); u = 1 - m.adsP * Math.sqrt(m.adsP); u = u * u * u; m.ads = dir > 0 ? 1 - u : u; }
      // stow (1 = lowered): rises over a holster and falls over a draw; out (1 = dropped away): rises over the tail of
      // a melee swing. The weapon in hand always leaves before the next one arrives and no model swap is seen.
      m.out = 0;
      if (s.melee) {
        var f0 = Math.min(0.92, Math.max(T.meleeOut, (s.melee.def.hit2 || s.melee.def.hit || 0) + 0.12)), fm = s.melee.t / s.melee.dur;
        if (fm > f0) { u = Math.min(1, (fm - f0) / (1 - f0)); m.out = u * u; }
        m.stow -= m.stow * Math.min(1, dt * T.stowRise);
      } else if (s.state === 'holster' && g) { u = Math.min(1, s.t / (T.holsterTime * sw)); m.stow = m.stow0 + (1 - m.stow0) * u * u; }
      else if (s.state === 'draw' && g) { u = 1 - Math.min(1, s.t / (T.drawTime * sw)); m.stow = Math.min(m.stow, u * u * u); }
      else m.stow -= m.stow * Math.min(1, dt * T.stowRise);
    }
    var e = m.ads, hip = 1 - e, keep = 1 - e * (1 - vc.adsKeep), half = 1 - e * 0.5;
    var sk = Math.max(0, Math.min(1.25, s.sprintK)), sl = Math.max(0, s.slideK);
    var portrait = IB.Render.vmCam.aspect < 1;
    var x = (portrait ? 0.13 : 0.19) + vc.hipX, y = -0.13 + vc.hipY, z = -0.5 + vc.hipZ, rx = 0, ry = 0.06 * hip, rz = 0;
    // aim down sights: blend toward the pose that puts the sight point on the screen centre
    var sp = g && e > 0.0005 ? W.sightOf(g.id) : null;
    if (sp) {
      x += (-sp.x * VM_SCALE - x) * e; y += (-sp.y * VM_SCALE - y) * e; z += (-(g.def.adsDist || vc.ads) - sp.z * VM_SCALE - z) * e;   // adsDist: a mounted scope's eye relief
      u = 4 * e * hip; rz += vc.adsRoll * u; y -= vc.adsDip * u;   // the gun rolls and dips a little on its way up and down
    }
    // walk cycle, phase = distance moved: side sway and roll once per two steps, bounce and nod once per step
    // (the bounce trails the footfall a little: weight); bigger at sprint, nearly gone while aimed
    var amt = (headBob ? 1 : 0.6) * m.bobA * vc.bob * (1 + (vc.sprintBob - 1) * sk) * keep, ph = player.bobT || 0, p2 = 2 * ph - T.bobLag;
    x += Math.sin(ph) * T.bobX * amt; y -= (0.5 + 0.5 * Math.cos(p2)) * T.bobY * amt;
    rx += Math.sin(p2) * T.bobPitch * amt; ry += Math.cos(ph) * T.bobYaw * amt;
    rz += Math.sin(ph) * T.bobRoll * amt * (1 + (vc.sprintRoll - 1) * sk);
    // idle life: breathing plus slow micro-sway, sines with no common period; calmer on the move, none on the sights
    var il = T.idle * hip * (1 - 0.5 * m.bobA);
    x += (Math.sin(t * 0.83 + 1.3) * 0.0011 + Math.sin(t * 1.37 + 0.4) * 0.0006) * il;
    y += (Math.sin(t * 1.55) * 0.0026 + Math.sin(t * 0.61 + 2.1) * 0.0009) * il;
    rx += (Math.sin(t * 1.55 + 1) * 0.0038 + Math.sin(t * 0.43 + 3) * 0.0015) * il;
    ry += Math.sin(t * 0.71 + 0.8) * 0.0022 * il; rz += Math.sin(t * 0.47 + 0.5) * 0.0035 * il;
    // inertia: strafe lean, start / stop lag, jump lag and landing
    x -= m.str * T.strafeX * keep; rz -= m.str * T.strafeRoll * (0.3 + 0.7 * hip);
    z += m.fwd * T.moveZ * keep * wg; y -= Math.abs(m.fwd) * T.moveY * keep; rx -= m.fwd * T.movePitch * hip;
    y += (m.vert + m.land) * half; rx += (m.vert * T.vertPitch + m.land * T.landPitch) * half; rz += m.land * T.landRoll * half;
    // look sway
    u = 1 - e * (1 - T.adsSwayPos); x += m.swx * u; y += m.swy * u;
    u = 1 - e * (1 - T.adsSwayRot); ry += m.swx * T.swayYaw * u; rx += m.swy * T.swayPitch * u; rz += m.swx * T.swayRoll * u;
    // slide carry: the Slide action (gun tucked low and canted in, support arm out for balance) plus a small lean
    // into the slide on top; procedural only for a weapon without a Slide action. Aiming while sliding keeps the
    // two-hand hold (no Slide clip under the sights).
    var slideClip = g && W.clips[W.models[g.id].key + '_Slide'];
    if (!slideClip) { rz += 0.5 * sl; x -= 0.03 * sl; y -= 0.035 * sl; }
    else { rz += 0.05 * sl * hip; y -= 0.008 * sl * hip; rx -= 0.02 * sl * hip; }
    // cover dips and the stow
    y += m.by * half; rx += m.bp * half; rz += m.br * half;
    u = m.stow * vc.stow; x += T.stowX * u; y += T.stowY * u; z += T.stowZ * u; rx += T.stowPitch * u; rz += T.stowRoll * u;
    u = m.out; y += T.meleeDropY * u; rx += T.meleeDropPitch * u; rz += T.meleeDropRoll * u;
    // arm animation: once-clips (draw, fire, reload, holster) fall back to the Idle / Sprint / Slide loop
    if (W.mixer && (g || s.melee)) {
      if (g) {
        var want = sliding && slideClip && s.aim < 0.5 ? 'Slide' : (sprinting ? 'Sprint' : 'Idle'), from = W.animName;
        var busy = W.animOnce && W.action && W.action.isRunning();
        if (!busy && from !== want && s.state !== 'holster') {
          W.anim(s, want, { fade: want === 'Slide' ? T.fade.slideIn : from === 'Slide' ? T.fade.slideOut : want === 'Sprint' ? vc.fade : from === 'Sprint' ? vc.fade * T.fade.sprintOut : T.fade.loop });
        }
        var la = W.action;
        if (live && la && !W.animOnce) {
          // the sprint loop is phased by the distance run (two steps a loop), so the arms keep step with the bob and
          // the footfalls at any speed; the idle loop's speed wanders so its 2 s cycle never reads as a loop
          if (W.animName === 'Sprint') { u = (player.bobT || 0) * 0.15915494; la.timeScale = 0; la.time = (u - Math.floor(u)) * la.getClip().duration; }
          else if (W.animName === 'Idle') la.timeScale = 1 + T.idleClipDrift * Math.sin(t * 0.37);
        }
      }
      if (live) animTick(dt);
      W.mixer.update(dt);
    }
    // fire kick (springs stepped in W.update): back and down into the shoulder, muzzle flip, roll, side push
    z += s.kickZ * half; y -= s.kickZ * vc.kickDrop * hip; rx += s.kickR * (1 - e * 0.4);
    rz += (s.kickL || 0) * half; x += (s.kickS || 0) * (1 - e * 0.7); ry += (s.kickS || 0) * T.kickYaw * hip;
    W.vmRoot.position.set(x, y, z);
    W.vmRoot.rotation.set(rx, ry, rz);
    // while aimed the root turns about the sight point, so roll, kick and sway never take the sight off the centre
    if (sp) {
      _piv.copy(sp).multiplyScalar(VM_SCALE); x = _piv.x; y = _piv.y; z = _piv.z; _piv.applyEuler(W.vmRoot.rotation);
      W.vmRoot.position.x += (x - _piv.x) * e; W.vmRoot.position.y += (y - _piv.y) * e; W.vmRoot.position.z += (z - _piv.z) * e;
    }
    W.vmRoot.scale.setScalar(VM_SCALE);
    W.vmRoot.visible = (!!g || !!s.melee) && !s.hidden;
    if (IB.GunSkins) { IB.GunSkins.tick(s.t); if (g) skinModel(s.cur); }
    if (!g) W.flash.visible = false;
    if (g) {
      W.flash.visible = s.flashT > 0 && s.aim < 0.3;   // never over the sights when aiming
      if (W.flash.visible) {
        var cls = s.flashCls || g.def.cls, big = s.flashT > 0.028 ? 1 : 0.62;   // frame 1 full, frame 2 smaller
        W.flash.position.set(0, 0, -0.03);
        W.flash.rotation.z = Math.random() * 6.28;
        var fs = (FLASH_SCALE[cls] || 1) * (0.85 + Math.random() * 0.4) * big * (s.flashRev ? REV_FLASH : 1); W.flash.scale.set(fs, fs, fs);
        W.flashSide.visible = !!FLASH_SIDE[cls]; W.flashSide.rotation.z = -W.flash.rotation.z + (Math.random() - 0.5) * 0.3;   // flares stay level
        W.flashCone.visible = big === 1;
      }
    }
  };
})(window.IB = window.IB || {});
