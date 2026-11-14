/* INKBOLT weapon drops: guns of a quality tier (gray, green, blue, purple, orange) and melee weapons dropped by robots.
   Enemy rows carry the odds (src/data/enemies.js): weaponDrops {gray, green, blue, purple, orange} (soldiers),
   meleeDrop (blade bots drop the katana or the Voltaxe they wield). ai.js / game.js call IB.WeaponDrops.roll(r) /
   IB.WeaponDrops.melee(r, id) on a player kill.
   A dropped gun is one of the guns unlocked up to this level, lying in a tall glowing beam of its tier colour (and on
   the radar). Every drop also has an item level (the campaign level it dropped on; core/gunlevel.js).
   Nothing is picked up by walking over it and nothing is ever broken down into gems: walk up to a gun (its card
   shows) and press E (touch: USE) to take it, or leave it lying there. A model you do not own joins the arsenal and is
   carried at once when a loadout slot is free, otherwise it goes to the backpack. A model you already own is swapped:
   the new one takes its place and the one you had is laid on the floor where the other was.
   Tier x level multiply the gun's damage (dmgMul: game.js shoot / meleeHit, launchers.js) and are saved per gun in
   slot.gunTier / slot.gunLevel (launchers also their rolled magazine and element in slot.gunRoll).
   From campaign level 14 a kill may also drop a launcher (rollLauncher; IB.GunLevel.launcherDropChance).
     IB.WeaponDrops.init(scene) / clear() / update(dt, t, G) / radar() / tierOf(id) / levelOf(id) / dmgMul(id) /
     useTarget(G) / take(d, G) (game.js updateLoot: the E prompt) /
     acquire(id, tier, level, roll) (also used by the armory racks in game.js) */
(function (IB) {
  'use strict';
  var WD = IB.WeaponDrops = { list: [] };
  var TIERS = WD.TIERS = [
    { id: 'gray', name: 'Standard', color: '#C9C6BE', dmg: 1.00, gems: 15 },
    { id: 'green', name: 'Tuned', color: '#6BE05A', dmg: 1.07, gems: 30 },
    { id: 'blue', name: 'Rare', color: '#4A9BFF', dmg: 1.14, gems: 60 },
    { id: 'purple', name: 'Epic', color: '#B77BFF', dmg: 1.22, gems: 110 },
    { id: 'orange', name: 'Legendary', color: '#FF9A2E', dmg: 1.32, gems: 200 }
  ];
  var BY = {}; TIERS.forEach(function (t, i) { t.rank = i; BY[t.id] = t; });
  WD.tier = function (id) { return BY[id] || BY.gray; };
  var CAP = 40, USE_R = 2.4, CLOSE_R = 1.2, PEEK_R = 7;   // E reach (looking at it), reach whatever you look at, card distance

  function slot() { return IB.Game && IB.Game.slot; }
  WD.tierOf = function (gunId) { var s = slot(); return WD.tier(s && s.gunTier && s.gunTier[gunId]); };
  function GL() { return IB.GunLevel; }
  function playerLv() { var s = slot(); return IB.Skills && IB.Skills.gained ? IB.Skills.playerLevel(s ? IB.Skills.gained(s) : 0) : 1; }
  function curLevel() { return (IB.Game && IB.Game.plan && IB.Game.plan.level) || 1; }
  /* the level a gun fights at (its own, or player level - 4); melee weapons have none and ride the floor */
  WD.ownLevel = function (gunId) { var s = slot(); return (s && s.gunLevel && s.gunLevel[gunId]) || 1; };
  WD.levelOf = function (gunId) { return GL() ? GL().effective(WD.ownLevel(gunId), playerLv(), curLevel()) : 1; };
  /* level 21+ guns (their own gun level): the top tiers hit harder on top of the tier multiplier, orange the most */
  WD.LATE_BOOST = { level: 21, blue: 1.04, purple: 1.07, orange: 1.15 };
  WD.lateBoost = function (tierId, lv) { return lv >= WD.LATE_BOOST.level ? WD.LATE_BOOST[tierId] || 1 : 1; };
  WD.dmgMul = function (gunId) { var r = WD.rollOf(gunId); return WD.lateBoost(WD.tierOf(gunId).id, WD.ownLevel(gunId)) * WD.tierOf(gunId).dmg * (GL() ? GL().mul(WD.levelOf(gunId)) : 1) * (r && r.mult ? r.mult : 1); };
  WD.rollOf = function (gunId) {
    var s = slot(), def = IB.WEAPONS[gunId], gl = GL(), saved = s && s.gunRoll && s.gunRoll[gunId];
    if (!def || !gl) return null;
    if (gl.isLauncher(def)) return gl.fixRoll(def, saved);
    if (def.magRange) {   // the Warden: its magazine is rolled the first time it is needed, then kept in the save
      if (!saved && s) { s.gunRoll = s.gunRoll || {}; saved = s.gunRoll[gunId] = gl.rollMagRange(def); }
      return gl.fixMagRange(def, saved);
    }
    return def.wyrm ? gl.fixWyrm(def, saved) : null;
  };
  // the player level a new drop's roll uses (XP-based, 1-30)
  function playerLv() { return IB.Game && IB.Game.progress ? IB.Game.progress().level : 1; }
  /* display name: the model name (launchers with their element), dressed by the tier (core/gunskins.js: 'Cobalt Rivet') */
  WD.skinName = function (gunId, tierId, roll) {
    var def = IB.WEAPONS[gunId], base = GL() ? GL().displayName(def, roll) : def.name;
    return IB.GunSkinData ? IB.GunSkinData.name(gunId, WD.tier(tierId).id, base) : base;
  };
  WD.nameOf = function (gunId) { return WD.skinName(gunId, WD.tierOf(gunId).id, WD.rollOf(gunId)); };
  /* a gun taken (floor drop, armory rack). A model you do not own joins the arsenal and is carried at once when a
     loadout slot is free, otherwise it waits in the backpack. A model you already own is swapped: the new one takes
     its place (its attachments stay on) and the one you had comes back as `old` {id, tier, level, roll} for the caller
     to lay on the floor. Nothing is broken down. Returns {line, old, carried, key}. */
  WD.acquire = function (id, tierId, level, roll) {
    var G = IB.Game, s = G.slot, def = IB.WEAPONS[id], gl = GL(), line, old = null, carried = false, key = 0;
    s.gunTier = s.gunTier || {}; s.arsenal = s.arsenal || []; s.gunLevel = s.gunLevel || {}; s.gunRoll = s.gunRoll || {};
    var have = s.arsenal.indexOf(id) >= 0, nt = WD.tier(tierId), lv = Math.max(1, level || curLevel());
    var launcher = gl && gl.isLauncher(def); if (launcher) roll = gl.fixRoll(def, roll || gl.rollLauncher(def));
    var wyrm = gl && def.wyrm; if (wyrm) roll = gl.fixWyrm(def, roll || gl.wyrmRoll(def, playerLv()));
    var name = WD.skinName(id, nt.id, roll);
    if (have) old = { id: id, tier: WD.tierOf(id).id, level: WD.ownLevel(id), roll: s.gunRoll[id] || null };
    else { s.arsenal.push(id); s.owned = s.arsenal.slice(); }
    s.gunTier[id] = nt.id; s.gunLevel[id] = lv;
    if (roll) s.gunRoll[id] = roll; else delete s.gunRoll[id];
    var lo = (s.loadout || []).slice(), max = G.progress ? G.progress().loadoutMax : 2;
    if (!have && lo.indexOf(id) < 0 && lo.length < max) { lo.push(id); s.loadout = lo; carried = true; if (G.bank) delete G.bank[id]; }   // a fresh gun comes loaded
    key = lo.indexOf(id) + 1;
    if (G.ws && IB.Weapons && key > 0) {   // the carried guns follow at once (a swapped gun keeps its rounds, cut to its magazine)
      IB.Weapons.setLoadout(G.ws, lo, G.bank);
      if (IB.Gear) IB.Gear.refresh(G);
    }
    if (launcher && IB.Launchers) IB.Launchers.onAcquire(id, !have);
    if (old) line = 'Swapped for ' + name + ' · ' + nt.name + ' Lv ' + lv;
    else line = name + (carried ? ' · carried on key ' + key : ' · in your backpack (Tab)');
    return { line: line, old: old, carried: carried, key: key };
  };

  /* The loot glow: one designed effect per tier, taller, wider and brighter than any gear beam, so a gun reads as a
     gun (and its rarity at a glance) from across the zone. Every gun on the floor is drawn by three shared batches,
     whatever the number of drops (three draw calls in all, none while no gun lies anywhere):
       beam    one camera-facing card per drop: a soft shaft (gaussian across, a bright core, slow streaks climbing
               it) that is brightest at the foot and thins out to nothing well before its top, so it has no top edge;
               under a ceiling it is cut down to fit
       floor   one flat card per drop: a soft pool of light and inked rings, one (Standard, Tuned), two (Rare, Epic)
               or three (Legendary, the outer one dashed and turning, Epic's too); Rare and up send a ripple out
       motes   one point cloud: slow sparks rising round the beam, Rare 4, Epic 7, Legendary 10
     plus a gentle rim of the tier colour on the turning gun (GunSkins.material rim, one material per drop slot).
     One envelope per drop drives all of it: life (spawn eases out over SPAWN_T, take eases in over OUT_T), the idle
     breath (one phase for beam, rings, motes and rim), the distance fade (the scene fog at the drop, so the glow goes
     with the gun it marks) and a mote fade that cross-fades the fine sparks out with distance (no LOD switch). The
     glow is premultiplied (emission plus partial cover, which keeps the tier colour on a bright sky or white wall and
     gives the rings an ink edge), never fogged, writes no depth, and its instances keep one fixed order: overlapping
     drops blend the same every frame, so nothing sorts or flickers. */
  var BEAM_H = 7.5;
  // per rank (gray .. orange; melee weapons rank 0): beam height (m) and motes. Beam width, brightness and the floor
  // radius and rings follow the rank in the shaders below
  var LOOKS = [{ h: 5.4, motes: 0 }, { h: 5.9, motes: 0 }, { h: 6.4, motes: 4 }, { h: 6.9, motes: 7 }, { h: BEAM_H, motes: 10 }];
  WD.LOOKS = LOOKS;
  var SPAWN_T = 0.5, OUT_T = 0.4, MOTES = 10, MELEE_COL = '#FFC23A';
  // a shaft of light seen from the side: soft across (bright middle, darker rim), bright at the foot, gone at the top
  // (the gear beams in game/drops.js use it and the spark below)
  function shaftTex(tight) {
    var t = IB.Render.canvasTex(64, 128, function (c) {
      c.clearRect(0, 0, 64, 128);
      for (var x = 0; x < 64; x++) {
        var u = (x + 0.5) / 32 - 1, a = Math.exp(-u * u * (tight ? 7 : 3.4)) * (1 - u * u), sh = Math.round(255 * (tight ? 1 : 0.5 + 0.5 * Math.exp(-u * u * 7)));
        var g = c.createLinearGradient(0, 0, 0, 128), col = sh + ',' + sh + ',' + sh;
        g.addColorStop(0, 'rgba(' + col + ',0)'); g.addColorStop(0.3, 'rgba(' + col + ',' + (a * 0.42).toFixed(3) + ')'); g.addColorStop(0.7, 'rgba(' + col + ',' + (a * 0.82).toFixed(3) + ')'); g.addColorStop(1, 'rgba(' + col + ',' + a.toFixed(3) + ')');
        c.fillStyle = g; c.fillRect(x, 0, 1, 128);
      }
    });
    return t;
  }
  function sparkTex() {
    return IB.Render.canvasTex(32, 32, function (c) {
      var g = c.createRadialGradient(16, 16, 0, 16, 16, 16);
      g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.3, 'rgba(255,255,255,0.7)'); g.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = g; c.fillRect(0, 0, 32, 32);
    });
  }
  WD.beamTextures = function () { return WD.tex || (WD.tex = { shaft: shaftTex(false), spark: sparkTex() }); };
  // turn a shaft plane (it stands on the drop, facing +z) toward the camera (the gear beams)
  WD.faceCamera = function (mesh, x, z) { var c = IB.Render && IB.Render.camera; if (c) mesh.rotation.y = Math.atan2(c.position.x - x, c.position.z - z); };

  /* ---- the three glow batches (shaders) ----
     Per drop (instance) attributes: aP = (x, floor y, z, beam height), aC = (tier colour, rank), aE = (life, breath,
     fade, seed). Motes carry aP, aC, aS = (angle, radius, phase, speed) and aM = (life x fade x mote fade, breath). */
  var GLOW_PARS = 'uniform float uT; attribute vec4 aP; attribute vec4 aC; attribute vec4 aE;\n';
  var BEAM_V = GLOW_PARS + [
    'varying vec2 vUv; varying vec3 vCol; varying float vA, vRank, vH, vSeed;',
    'void main() {',
    '  float life = aE.x, rank = aC.w;',
    '  vec2 d = cameraPosition.xz - aP.xz; float L = length( d );',
    '  vec2 f = L > 1e-3 ? d / L : vec2( 0.0, 1.0 );',
    '  vec3 right = vec3( f.y, 0.0, -f.x );',
    '  float H = aP.w * ( 0.3 + 0.7 * life ), w = ( 1.3 + 0.12 * rank ) * ( 0.45 + 0.55 * life );',   // grows out of the floor, sinks back
    '  vec3 p = aP.xyz + right * ( position.x * w ) + vec3( 0.0, position.y * H, 0.0 );',
    '  vec3 v = normalize( cameraPosition - p );',
    // standing in (or next to) the beam thins it, so it never washes the screen; seen from high above the flat card
    // hands over to the floor glow
    '  float nearF = mix( 0.3, 1.0, smoothstep( 0.35, 2.4, L ) ), steep = mix( 0.2, 1.0, 1.0 - smoothstep( 0.7, 0.95, abs( v.y ) ) );',
    '  vA = life * aE.z * nearF * steep * ( 0.86 + 0.14 * aE.y );',
    '  vUv = uv; vCol = aC.rgb; vRank = rank; vH = H; vSeed = aE.w;',
    '  gl_Position = projectionMatrix * viewMatrix * vec4( p, 1.0 );',
    '}'].join('\n');
  var BEAM_F = [
    'uniform float uT; varying vec2 vUv; varying vec3 vCol; varying float vA, vRank, vH, vSeed;',
    'void main() {',
    '  float x = vUv.x * 2.0 - 1.0, y = vUv.y, x2 = x * x;',
    '  float halo = exp( -x2 * 4.0 ) * ( 1.0 - x2 ), core = exp( -x2 * ( 40.0 - vRank * 3.0 ) );',
    // brightest at the foot, an even shaft, then a long smooth fall over its upper half that reaches zero with zero
    // slope at the top: no edge anywhere
    '  float vert = ( 1.0 - 0.6 * y ) * ( 1.0 - smoothstep( 0.4, 1.0, y ) ) * smoothstep( 0.0, 0.03, y );',
    // slow soft streaks climbing the shaft (the comic speed-line), stronger the rarer
    '  float s = sin( ( y * vH * 0.8 - uT * ( 0.55 + 0.08 * vRank ) + x * 0.9 + vSeed * 7.0 ) * 6.2832 );',
    '  float band = 1.0 + smoothstep( 0.3, 1.0, s ) * ( 0.12 + 0.06 * vRank ) * ( 1.0 - x2 );',
    '  vec3 hot = mix( vCol, vec3( 1.0 ), 0.15 );',
    '  float I = 0.68 + 0.06 * vRank;',
    '  vec3 e = ( vCol * halo * 0.8 + hot * core * 0.9 ) * vert * band * I;',
    // a good part of what lies behind is covered, so the tier colour holds against a bright sky or a white wall
    '  float cover = ( halo * 0.55 + core * 0.6 ) * vert;',
    '  gl_FragColor = vec4( e * vA, cover * vA );',
    '}'].join('\n');
  var FLOOR_V = GLOW_PARS + [
    'varying vec2 vQ; varying vec3 vCol; varying float vA, vRank, vR, vBr, vSeed;',
    'void main() {',
    '  float life = aE.x, rank = aC.w;',
    '  vR = ( 1.3 + 0.12 * rank ) * ( 0.55 + 0.45 * life );',   // the rings open out as the gun lands, close as it goes
    '  vec3 p = aP.xyz + vec3( position.x * vR, 0.05, position.z * vR );',
    '  vQ = position.xz; vCol = aC.rgb; vRank = rank; vBr = aE.y; vSeed = aE.w; vA = life * aE.z;',
    '  gl_Position = projectionMatrix * viewMatrix * vec4( p, 1.0 );',
    '}'].join('\n');
  var FLOOR_F = [
    'uniform float uT; varying vec2 vQ; varying vec3 vCol; varying float vA, vRank, vR, vBr, vSeed;',
    'float band( float r, float c, float w ) { float k = ( r - c ) / w; return exp( -k * k ); }',
    'void main() {',
    '  float q = length( vQ ), r = q * vR, edge = 1.0 - smoothstep( 0.8, 1.0, q );',
    '  float pool = exp( -r * r * 1.9 ) * ( 0.3 + 0.08 * vBr );',
    '  float r0 = 0.6 + 0.035 * vBr, ring = band( r, r0, 0.045 ), ink = band( r, r0 + 0.075, 0.03 );',
    '  float ang = atan( vQ.y, vQ.x ), dash = smoothstep( 0.15, 0.6, 0.5 + 0.5 * cos( ang * 9.0 - uT * 0.5 + vSeed * 6.0 ) );',
    '  float r1 = r0 + 0.27, r2 = r0 + 0.5;',
    '  float ring1 = step( 1.5, vRank ) * band( r, r1, 0.03 ) * ( vRank > 2.5 && vRank < 3.5 ? dash : 1.0 );',
    '  float ring2 = step( 3.5, vRank ) * band( r, r2, 0.028 ) * dash;',
    '  float ink1 = step( 1.5, vRank ) * band( r, r1 + 0.06, 0.022 ) + step( 3.5, vRank ) * band( r, r2 + 0.055, 0.02 );',
    // Rare and up: a ripple runs out over the floor; it starts and ends at nothing (no ring pops in or out)
    '  float ph = fract( uT * 0.4 + vSeed ), rip = step( 1.5, vRank ) * band( r, 0.55 + ph * ( vR * 0.78 - 0.55 ), 0.07 ) * pow( sin( 3.14159 * ph ), 2.0 ) * 0.55;',
    '  float lit = ring * ( 0.85 + 0.15 * vBr ) + ring1 * 0.75 + ring2 * 0.65;',
    '  float I = 0.8 + 0.07 * vRank;',
    '  vec3 e = vCol * ( pool + rip + lit ) * I;',
    // the rings mostly replace the floor under them (so the tier colour holds on a pale floor) and carry an ink
    // edge (the comic outline); the pool tints a little
    '  float cover = min( 1.0, lit * 0.8 + rip * 0.5 + ink * 0.55 + ink1 * 0.45 + pool * 0.3 );',
    '  gl_FragColor = vec4( e, cover ) * ( vA * edge );',
    '}'].join('\n');
  var MOTE_V = [
    'uniform float uT, uSize, uScale; attribute vec4 aP; attribute vec4 aC; attribute vec4 aS; attribute vec4 aM;',
    'varying vec3 vCol; varying float vA;',
    'void main() {',
    '  float ph = fract( aS.z + uT * 0.085 * aS.w ), ang = aS.x + uT * ( 0.25 + 0.2 * aS.w ), rr = aS.y * ( 1.0 - 0.45 * ph );',
    '  vec3 p = aP.xyz + vec3( cos( ang ) * rr, 0.25 + ph * aP.w * 0.7 * ( 0.3 + 0.7 * aM.x ), sin( ang ) * rr );',
    '  vec4 mv = viewMatrix * vec4( p, 1.0 ); float dz = max( -mv.z, 0.1 ), px = uSize * uScale / dz;',
    '  gl_PointSize = max( px, 1.6 );',
    // each spark fades in at the foot and out near the top (none pops at the wrap); a spark smaller than a couple of
    // pixels dims instead of shimmering
    '  vA = aM.x * pow( sin( 3.14159 * ph ), 1.5 ) * min( 1.0, px / 1.6 ) * ( 0.8 + 0.2 * aM.y );',
    '  vCol = mix( aC.rgb, vec3( 1.0 ), 0.3 );',
    '  gl_Position = projectionMatrix * mv;',
    '}'].join('\n');
  var MOTE_F = 'varying vec3 vCol; varying float vA; void main() { vec2 q = gl_PointCoord - 0.5; float a = smoothstep( 0.25, 0.02, dot( q, q ) ) * vA; if ( a < 0.004 ) discard; gl_FragColor = vec4( vCol * a, a * 0.3 ); }';
  function glowMat(v, f, extra) {
    var o = { uniforms: { uT: WD.glowT }, vertexShader: v, fragmentShader: f, transparent: true, depthWrite: false, fog: false,
      blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor };
    if (extra) for (var k in extra) o[k] = extra[k];
    return new THREE.ShaderMaterial(o);
  }
  WD.glowT = { value: 0 };
  // the batches, sized for `cap` drops (regrown when more lie about)
  function buildBatches(cap) {
    var B = WD.batch, scene = WD.scene;
    if (B) { [B.beam, B.floor, B.motes].forEach(function (m) { scene.remove(m); m.geometry.dispose(); }); }
    // per-drop data: one set of buffers, read by both the beam and the floor cards
    var per = {}; ['aP', 'aC', 'aE'].forEach(function (k) { per[k] = new THREE.InstancedBufferAttribute(new Float32Array(cap * 4), 4).setUsage(THREE.DynamicDrawUsage); });
    function inst(src) {
      var g = new THREE.InstancedBufferGeometry(); g.setIndex(src.index);
      ['position', 'uv'].forEach(function (k) { g.setAttribute(k, src.attributes[k]); });
      for (var k in per) g.setAttribute(k, per[k]);
      g.instanceCount = 0;
      return g;
    }
    var bq = new THREE.PlaneGeometry(1, 1); bq.translate(0, 0.5, 0);
    var fq = new THREE.PlaneGeometry(2, 2); fq.rotateX(-Math.PI / 2);
    var mats = WD.glowMats || (WD.glowMats = {
      beam: glowMat(BEAM_V, BEAM_F, { side: THREE.DoubleSide }),
      floor: glowMat(FLOOR_V, FLOOR_F, { polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 }),
      motes: glowMat(MOTE_V, MOTE_F, { uniforms: { uT: WD.glowT, uSize: { value: 0.15 }, uScale: { value: 300 } } })
    });
    var beam = new THREE.Mesh(inst(bq), mats.beam), floor = new THREE.Mesh(inst(fq), mats.floor);
    var mg = new THREE.BufferGeometry(), nm = cap * MOTES;
    ['position', 'aP', 'aC', 'aS', 'aM'].forEach(function (k, j) { mg.setAttribute(k, new THREE.BufferAttribute(new Float32Array(nm * (j ? 4 : 3)), j ? 4 : 3).setUsage(THREE.DynamicDrawUsage)); });
    mg.setDrawRange(0, 0);
    var motes = new THREE.Points(mg, mats.motes);
    // fixed order after the world: floor glow, then beams, then motes; never culled (one box would not hold them)
    floor.renderOrder = 2; beam.renderOrder = 3; motes.renderOrder = 4;
    [beam, floor, motes].forEach(function (m) { m.frustumCulled = false; m.visible = false; scene.add(m); });
    WD.batch = { cap: cap, beam: beam, floor: floor, motes: motes };
  }
  WD.init = function (scene) {
    WD.scene = scene;
    WD.beamTextures();
    WD.addSlot = function () {
      var grp = new THREE.Group(); grp.visible = false; scene.add(grp);
      var spin = new THREE.Group(); spin.position.y = 0.95; grp.add(spin);
      var seed = [];
      for (var k = 0; k < MOTES; k++) seed.push([Math.random() * Math.PI * 2, 0.2 + Math.random() * 0.45, (k + Math.random() * 0.8) / MOTES, 0.6 + Math.random() * 0.8]);
      // the rim on the turning gun: this slot's own uniforms (GunSkins.material makes one material per slot)
      var rim = { uRimC: { value: new THREE.Color() }, uRimA: { value: 0 } };
      WD.list.push({ on: false, out: -1, grp: grp, spin: spin, seed: seed, rim: rim, phase: Math.random(), mesh: null, id: null, tier: null, melee: false,
        x: 0, z: 0, y: 0, t: 0, gt: 0, life: 0, level: 1, roll: null, col: new THREE.Color(), rank: 0, beamH: BEAM_H });
    };
    for (var i0 = 0; i0 < CAP; i0++) WD.addSlot(i0);
    buildBatches(CAP);
  };
  WD.clear = function () { WD.list.forEach(function (d) { d.on = false; d.out = -1; d.grp.visible = false; }); if (IB.HUD && IB.HUD.peek) IB.HUD.peek('drop', null); };

  // enemies that never drop guns or armour: the grey crawler and the exploding bomber
  var NO_GUN = { crawler: 1, bomber: 1 };
  WD.OTHER_GUN_CHANCE = 0.05;   // 2.5 % doubled, for every robot except soldiers' own table
  function def0(id) { return IB.WEAPONS && IB.WEAPONS[id]; }
  function G0() { return IB.Game; }
  var OUT_MAX = 0.006;   // ink outline cap for the turning gun (it is drawn 1.7x): it keeps its size at any distance
  // the beam is cut down under a ceiling or deck above the drop: its fall to nothing ends 0.4 m past it, so the
  // ceiling meets almost no light (no hard line where it cuts the beam)
  function beamHeight(x, floor, z, h) {
    var w = G0() && G0().level && G0().level.world, hit = w && w.ray ? w.ray(x, floor + 1.2, z, 0, 1, 0, h) : null;
    return hit ? Math.max(1.6, Math.min(h, 1.2 + hit.t + 0.4)) : h;
  }
  function spawn(id, tier, x, z, melee, y, level, roll) {
    var A = IB.Assets, node = 'WPN_' + id.toUpperCase();
    if (!A.geo[node]) return null;
    // a free slot (not one still fading out from a pickup: that one finishes its fade)
    var d = null; for (var i = 0; i < WD.list.length; i++) if (!WD.list[i].on && WD.list[i].out < 0) { d = WD.list[i]; break; }
    // list full: one more slot. A dropped gun is never removed; it stays until the player takes it or leaves
    if (!d) { WD.addSlot(WD.list.length); d = WD.list[WD.list.length - 1]; }
    if (d.mesh) d.spin.remove(d.mesh);
    if (!WD.mat) WD.mat = IB.Render.toonMaterial({ map: A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0, outMax: OUT_MAX, look: 'actor', surf: IB.Surface && IB.Surface.surf('weapons') });
    d.mesh = new THREE.Mesh(G0() && G0().gunGeo && !melee ? G0().gunGeo(id, tier) : A.get(node), !melee && IB.GunSkins ? IB.GunSkins.material(id, tier, null, OUT_MAX, d.rim) : WD.mat);   // rarity skin (with this slot's rim), magazine in
    d.mesh.scale.setScalar(melee ? 1.5 : 1.7);
    if (melee) d.mesh.rotation.set(0, 0, 0.5); else d.mesh.rotation.set(0, 0, 0);
    d.spin.add(d.mesh);
    var floor = IB.Zones && IB.Zones.floorY ? IB.Zones.floorY(x, z, (y || 0) + 0.6) : 0;   // the floor (or deck) it fell on
    d.on = true; d.id = id; d.tier = tier; d.melee = !!melee; d.x = x; d.z = z; d.t = 0; d.y = floor;
    d.level = Math.max(1, level || curLevel()); d.roll = roll || null;
    if (!d.roll && !melee && IB.GunLevel && def0(id) && def0(id).wyrm) d.roll = IB.GunLevel.wyrmRoll(def0(id), playerLv());
    d.grp.position.set(x, floor, z); d.grp.visible = true; d.spin.scale.setScalar(0.001);
    d.out = -1; d.gt = 0; d.life = 0;
    // the rarer the gun, the taller and fuller its glow (a melee weapon gets the plain one, in gold)
    d.rank = melee ? 0 : WD.tier(tier).rank; d.col.set(melee ? MELEE_COL : WD.tier(tier).color); d.rim.uRimC.value.copy(d.col); d.rim.uRimA.value = 0;
    d.beamH = beamHeight(x, floor, z, LOOKS[d.rank].h);
    if (IB.Audio) IB.Audio.play('pickup', { pos: { x: x, z: z }, pitch: 0.7, gain: 0.6 });
    return d;
  }

  // the guns that can drop on this level: every gun unlocked up to it (falls back to the arsenal)
  function pool() {
    var L = (IB.Game && IB.Game.plan && IB.Game.plan.level) || 1, out = [];
    (IB.ownedWeapons ? IB.ownedWeapons(L) : []).forEach(function (id) { if (IB.Weapons.playable(id)) out.push(id); });
    if (!out.length && slot() && slot().arsenal) out = slot().arsenal.slice();
    return out;
  }
  /* a soldier (or any robot whose row has weaponDrops) was wrecked by the player: maybe drop a gun */
  WD.roll = function (r, rng) {
    rng = rng || Math.random;
    var row = IB.ENEMIES && IB.ENEMIES[r.type], odds = row && row.weaponDrops;
    if (!odds) {   // every other robot: 5% per kill in total, split like the soldiers' gun drops (crawlers and bombers never)
      if (NO_GUN[r.type]) return null;
      var sold = IB.ENEMIES && IB.ENEMIES.soldier && IB.ENEMIES.soldier.weaponDrops || {}, tot = 0, k;
      Object.keys(sold).forEach(function (t) { tot += sold[t]; });
      odds = {}; Object.keys(sold).forEach(function (t) { odds[t] = tot ? sold[t] * WD.OTHER_GUN_CHANCE / tot : 0; });
    }
    var x = rng(), acc = 0, tier = null;
    for (var i = TIERS.length - 1; i >= 0; i--) { acc += odds[TIERS[i].id] || 0; if (x < acc) { tier = TIERS[i].id; break; } }
    if (!tier) return null;
    var p = pool(); if (!p.length) return null;
    return spawn(p[Math.floor(rng() * p.length)], tier, r.x, r.z, false, r.y, curLevel());
  };
  /* any player kill from campaign level 14 on: maybe a launcher (soldiers more often): RL-3 Hothead 60 %, ML-6 Murmur
     40 %, its tier from GunLevel.LAUNCHER_TIERS, magazine and element rolled now */
  WD.rollLauncher = function (r, rng) {
    rng = rng || Math.random;
    var gl = GL(); if (!gl) return null;
    if (rng() >= gl.launcherDropChance(r.type, curLevel())) return null;
    var id = rng() < 0.6 ? 'hothead' : 'murmur', def = IB.WEAPONS[id]; if (!def || !IB.Weapons.playable(id)) return null;
    return spawn(id, WD.rollTier(gl.LAUNCHER_TIERS, rng), r.x, r.z, false, r.y, curLevel(), gl.rollLauncher(def, rng));
  };
  WD.rollTier = function (w, rng) {
    var tot = 0, k; for (k in w) tot += w[k];
    var x = (rng || Math.random)() * tot; for (k in w) { x -= w[k]; if (x < 0) return k; }
    return 'gray';
  };
  /* a blade bot was wrecked: maybe drop the melee weapon it wields */
  WD.melee = function (r, id, rng) {
    rng = rng || Math.random;
    var row = IB.ENEMIES && IB.ENEMIES[r.type], ch = row && row.meleeDrop !== undefined ? row.meleeDrop : 0.07;
    if (!id || !IB.WEAPONS[id] || rng() >= ch) return null;
    var sl = slot(); if (sl && sl.melee && sl.melee.indexOf(id) >= 0) return null;   // you carry it already: nothing to take
    return spawn(id, 'gray', r.x, r.z, true, r.y);
  };

  /* E on a drop: a melee weapon goes on V; a gun is taken by WD.acquire (a swapped-out gun of yours lands where
     this one lay) */
  function take(d, G) {
    var s = G.slot, def = IB.WEAPONS[d.id], HUD = IB.HUD;
    if (!d.on || !s) return false;
    var x = d.x, z = d.z, y = d.y;
    d.on = false; d.out = 0;   // gone for the game at once; the glow and the gun ease out over OUT_T (WD.update)
    if (d.melee) {
      s.melee = s.melee || [];
      if (s.melee.indexOf(d.id) < 0) s.melee.push(d.id);
      s.meleeSel = d.id;
      if (HUD.pickup) HUD.pickup(def.name, 'melee', 'V');
      if (HUD.toast) HUD.toast(def.name + ' · on V', 1.8, 'tick:gear');
    } else {
      var r = WD.acquire(d.id, d.tier, d.level, d.roll);
      if (r.old) spawn(r.old.id, r.old.tier, x, z, false, y, r.old.level, r.old.roll);
      if (HUD.toast) HUD.toast(r.line, 2.4, 'tick:gear');   // the gun in hand stays in hand: the new one waits on its key
    }
    if (IB.Audio) IB.Audio.play('pickup');
    if (IB.FX) IB.FX.puff(x, (y || 0) + 0.9, z, 10, parseInt((d.melee ? MELEE_COL : WD.tier(d.tier).color).slice(1), 16), 0.14, 0.45, 3.5);
    if (G.store) G.store.save(s);
    return true;
  }
  WD.take = take;
  /* what E would do with drop d right now: {text, sub} for the prompt */
  function promptFor(d, G) {
    var s = G.slot, def = IB.WEAPONS[d.id];
    if (d.melee) return { text: 'Take ' + def.name, sub: 'Melee · goes on V' };
    var T = WD.tier(d.tier), name = WD.skinName(d.id, d.tier, d.roll), have = s && (s.arsenal || []).indexOf(d.id) >= 0;
    var lo = (s && s.loadout) || [], max = G.progress ? G.progress().loadoutMax : 2, sub;
    if (have) sub = 'Swap · your ' + WD.tierOf(d.id).name + ' Lv ' + WD.ownLevel(d.id) + ' stays here';
    else sub = lo.length < max ? 'Carried on key ' + (lo.length + 1) : 'Goes to your backpack';
    return { text: (have ? 'Swap for ' : 'Take ') + name, sub: T.name + ' · Lv ' + d.level + ' · ' + sub };
  }
  /* the drop E would take: the one you stand over, else the one you look at within reach. {d, text, sub, color, gun} */
  WD.useTarget = function (G) {
    var p = G.player, best = null, bs = -1;
    if (!p || !p.alive) return null;
    for (var i = 0; i < WD.list.length; i++) {
      var q = WD.list[i]; if (!q.on || q.t < 0.35) continue;
      var dx = q.x - p.x, dz = q.z - p.z, dist = Math.hypot(dx, dz); if (dist > USE_R || Math.abs(p.y - q.y) > 1.6) continue;
      var face = dist > 0.01 ? (-Math.sin(p.yaw) * dx - Math.cos(p.yaw) * dz) / dist : 1;
      if (dist > CLOSE_R && face < 0.6) continue;
      var sc = (dist <= CLOSE_R ? 2 : face) - dist * 0.2; if (sc > bs) { bs = sc; best = q; }
    }
    if (!best) return null;
    var pr = promptFor(best, G);
    return { d: best, text: pr.text, sub: pr.sub, color: best.melee ? '#FFC23A' : WD.tier(best.tier).color,
      gun: { id: best.id, tier: best.tier, level: best.level, roll: best.roll, melee: best.melee, wx: best.x, wy: (best.y || 0) + 1.9, wz: best.z } };
  };

  /* The shared envelope of one drop, all its parts read it: life 0..1 (spawn eases out, a take eases in), breath
     0..1 (the idle pulse), fade (fog at the drop's distance) and the motes' distance fade. */
  function ease(k) { k = k < 0 ? 0 : k > 1 ? 1 : k; return 1 - (1 - k) * (1 - k) * (1 - k); }   // ease out (cubic)
  function smooth(a, b, x) { var k = (x - a) / (b - a); k = k < 0 ? 0 : k > 1 ? 1 : k; return k * k * (3 - 2 * k); }
  WD.envelope = function (d, t, cam) {
    var inn = ease(d.gt / SPAWN_T), out = d.out < 0 ? 1 : 1 - smooth(0, 1, d.out / OUT_T);
    var e = { life: inn * out, inn: inn, out: d.out < 0 ? 0 : smooth(0, 1, d.out / OUT_T), breath: 0.5 + 0.5 * Math.sin(t * 2.4 + d.phase * 6.2832), fade: 1, motes: 1 };
    if (cam) {
      var dx = cam.x - d.x, dy = cam.y - d.y - 1, dz = cam.z - d.z, dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
      var fog = IB.Render && IB.Render.scene && IB.Render.scene.fog, f = 0;
      if (fog) f = IB.Look && IB.Look.on && IB.Atmo && IB.Atmo.fogAmount ? IB.Atmo.fogAmount(dist, d.y + 2, fog.near, fog.far) : smooth(fog.near, fog.far, dist);
      // the glow goes with the fogged gun it marks, a little slower (it is light), and is gone at the fog wall
      e.fade = (1 - 0.75 * f) * (fog ? 1 - smooth(fog.far * 0.85, fog.far, dist) : 1);
      e.motes = 1 - smooth(18, 32, dist);   // the fine sparks cross-fade out with distance
    }
    return e;
  };
  var _cam = new THREE.Vector3();
  WD.update = function (dt, t, G) {
    var p = G.player, B = WD.batch, cam = IB.Render && IB.Render.camera ? IB.Render.camera.getWorldPosition(_cam) : null;
    if (IB.GunSkins) IB.GunSkins.tick(t);
    WD.glowT.value = t;
    if (B && WD.list.length > B.cap) buildBatches(Math.max(WD.list.length, B.cap * 2));
    B = WD.batch;
    var bp = B && B.beam.geometry.attributes, mp = B && B.motes.geometry.attributes, n = 0, m = 0;
    for (var i = 0; i < WD.list.length; i++) {
      var d = WD.list[i]; if (!d.on && d.out < 0) continue;
      if (d.on) d.t += dt;   // gameplay clock (E is offered from 0.35 s), untouched by the glow
      d.gt += dt;
      if (d.out >= 0) { d.out += dt; if (d.out >= OUT_T) { d.out = -1; d.grp.visible = false; continue; } }
      var e = WD.envelope(d, t, cam), L = LOOKS[d.rank];
      d.life = e.life;
      // the gun: it grows in as it settles from a little above, turns and bobs, and on a take shrinks and lifts away
      var bob = Math.sin(t * 2.2 + i) * 0.09 * (0.4 + 0.6 * e.inn);
      d.spin.rotation.y = t * 1.5 + i;
      d.spin.position.y = 0.95 + bob + (1 - e.inn) * 0.55 + e.out * 0.45;
      d.spin.scale.setScalar(Math.max(0.001, e.inn * (1 - e.out)));
      d.rim.uRimA.value = 0.5 * e.life * (0.8 + 0.2 * e.breath);
      if (!B) continue;
      var c = d.col, k4 = n * 4;
      bp.aP.array[k4] = d.x; bp.aP.array[k4 + 1] = d.y; bp.aP.array[k4 + 2] = d.z; bp.aP.array[k4 + 3] = d.beamH;
      bp.aC.array[k4] = c.r; bp.aC.array[k4 + 1] = c.g; bp.aC.array[k4 + 2] = c.b; bp.aC.array[k4 + 3] = d.rank;
      bp.aE.array[k4] = e.life; bp.aE.array[k4 + 1] = e.breath; bp.aE.array[k4 + 2] = e.fade; bp.aE.array[k4 + 3] = d.phase;
      n++;
      var mf = e.life * e.fade * e.motes;
      if (L.motes && mf > 0.002) for (var j = 0; j < L.motes; j++) {
        var sd = d.seed[j], q4 = m * 4;
        mp.aP.array[q4] = d.x; mp.aP.array[q4 + 1] = d.y; mp.aP.array[q4 + 2] = d.z; mp.aP.array[q4 + 3] = d.beamH;
        mp.aC.array[q4] = c.r; mp.aC.array[q4 + 1] = c.g; mp.aC.array[q4 + 2] = c.b; mp.aC.array[q4 + 3] = d.rank;
        mp.aS.array[q4] = sd[0]; mp.aS.array[q4 + 1] = sd[1]; mp.aS.array[q4 + 2] = sd[2]; mp.aS.array[q4 + 3] = sd[3];
        mp.aM.array[q4] = mf; mp.aM.array[q4 + 1] = e.breath;
        m++;
      }
    }
    if (B) {
      bp.aP.needsUpdate = bp.aC.needsUpdate = bp.aE.needsUpdate = true;   // shared with the floor cards
      B.beam.geometry.instanceCount = B.floor.geometry.instanceCount = n;
      B.beam.visible = B.floor.visible = n > 0;
      mp.aP.needsUpdate = mp.aC.needsUpdate = mp.aS.needsUpdate = mp.aM.needsUpdate = true;
      B.motes.geometry.setDrawRange(0, m); B.motes.visible = m > 0;
      if (IB.Render && IB.Render.renderer) {   // sparks are sized in render-target pixels (the post target may be smaller)
        var h = IB.Post && IB.Post.on && IB.Post.h ? IB.Post.h : IB.Render.height * (IB.Render.pixelRatio || 1);
        B.motes.material.uniforms.uScale.value = h * 0.5;
      }
    }
    // weapon card for the drop you walk up to and look at (HUD peek panel; rebuilt only when the target changes)
    var best = null, bs = 0;
    if (p && p.alive) for (i = 0; i < WD.list.length; i++) {
      var q = WD.list[i]; if (!q.on) continue;
      var dx = q.x - p.x, dz = q.z - p.z, dist = Math.hypot(dx, dz); if (dist > PEEK_R || Math.abs(p.y - q.y) > 2.5) continue;
      var face = dist > 0.01 ? (-Math.sin(p.yaw) * dx - Math.cos(p.yaw) * dz) / dist : 1; if (dist > CLOSE_R && face < 0.82) continue;
      var sc = (dist <= CLOSE_R ? 2 : face) - dist * 0.05; if (sc > bs) { bs = sc; best = q; }
    }
    WD.peeked = best;
    if (IB.HUD && IB.HUD.peek) IB.HUD.peek('drop', best ? { id: best.id, tier: best.tier, level: best.level, roll: best.roll, melee: best.melee, wx: best.x, wy: (best.y || 0) + 1.9, wz: best.z } : null);
  };
  WD.radar = function () { return WD.list.filter(function (d) { return d.on; }).map(function (d) { return { x: d.x, z: d.z, kind: 'weapon' }; }); };
  WD.live = function () { return WD.list.filter(function (d) { return d.on; }).map(function (d) { return { id: d.id, tier: d.tier, melee: d.melee, x: d.x, z: d.z, level: d.level, roll: d.roll }; }); };
  // the player drops a gun (Inventory): it lands at x, z with its tier, level and roll and leaves the arsenal (its
  // attachments go back to the bag, see Gear.refresh prune). The last carried gun cannot be dropped. Returns false if
  // the gun is not owned, is the only one carried, or has no model.
  WD.dropGun = function (id, x, z) {
    var G = IB.Game, s = G && G.slot, p = G && G.player;
    if (!s || !p || !s.arsenal || s.arsenal.indexOf(id) < 0) return false;
    var lo = s.loadout || [], at = lo.indexOf(id);
    if (at >= 0 && lo.length <= 1) return false;
    var d = spawn(id, WD.tierOf(id).id, x, z, false, p.y, WD.ownLevel(id), s.gunRoll ? s.gunRoll[id] : null);
    if (!d) return false;
    if (at >= 0) s.loadout = lo.filter(function (k) { return k !== id; });
    s.arsenal = s.arsenal.filter(function (k) { return k !== id; }); s.owned = s.arsenal.slice();
    if (s.gunTier) delete s.gunTier[id]; if (s.gunLevel) delete s.gunLevel[id]; if (s.gunRoll) delete s.gunRoll[id];
    if (G.bank) delete G.bank[id];
    return true;
  };
  // lay a gun {id, tier, level, roll} on the floor at x, z (a gun swapped out at an armory rack)
  WD.layDown = function (g, x, z, y) { return spawn(g.id, g.tier, x, z, false, y, g.level, g.roll); };
  // tests: put a drop right in front of the player (level / roll optional)
  WD.testDrop = function (id, tier, melee, level, roll) {
    var p = IB.Game.player, def = IB.WEAPONS[id], gl = GL();
    if (!roll && gl && gl.isLauncher(def)) roll = gl.rollLauncher(def);
    return !!spawn(id, tier || 'blue', p.x - Math.sin(p.yaw) * 2, p.z - Math.cos(p.yaw) * 2, !!melee, p.y, level, roll);
  };
})(window.IB = window.IB || {});
