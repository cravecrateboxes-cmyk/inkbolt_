/* INKBOLT robots: instanced rigid parts, AI state machine (section 4.4), hitscan tests,
   ink-silhouette deaths. Crawler (melee lunge), Gunner (keeps distance, uses cover, 3-bolt volley),
   Bomber (rushes, 0.6 s fuse, blast that also hurts robots), Drone (hovers 3 m up, strafing bursts).
   Shared states: spawn, idle, alert, stagger, blinded, pose; per type: chase / keep, windup, attack, recover.
   Skill hooks (game/skillfx.js): AI.cloaked (Undercover: robots lose the player and search where he was last seen),
   rogue robots (Handy Helpers: r.rogue > 0 s left; they fight the others, the others target them; AI.makeRogue),
   a per-instance tint (teal rogue, wet blue Hydrate coat: r.wet).
   Per robot per frame there is no allocation: parts are posed with a small matrix stack of scratch matrices.
   Walkable surfaces (zones.js: boxes tagged walk, from <Piece>_WCOL empties): a ground robot keeps r.fy, the floor
   under it (world.floorAt, stepping up at most STEP_UP), and r.gy, its smoothed foot height (glides up a step, falls
   off an edge); r.y = r.gy + r.hop (the Crawler's lunge hop). Collision, sight, hits, shots, shadows and corpses all
   work from r.y / r.fy, so robots climb stairs and ramps, cross bridges and fight on decks. Off-level targets (the
   player up on a deck) are chased along the layered flow field instead of straight at them. Without walkable boxes
   r.fy = r.gy = 0 and everything behaves as before.
   Flyers (Drones) hover at their height over the floor under them (ground or deck) but always below the zone's
   ceiling (theme env.ceiling unless the zone plan says ceiling: false) and the underside of any box overhead (a car
   park deck), and collide only with boxes at their height (flyCeil / flyY).
   Overwhelm control (core/damage.js closeCap / HOLD): only the nearest few melee robots close in on the player at
   once; the rest hold a 6-8.5 m ring, strafing, until a slot frees up (r.close, holdRing).
   Blocked robots: a chaser that keeps bumping into something follows the flow field around it for a while (r.navT);
   a robot only picks a rogue it can see in its own zone and gives up on one it has lost sight of (r.ign). */
(function (IB) {
  'use strict';
  var PAL = IB.PAL;
  var AI = IB.AI = { robots: [], corpses: [], types: {}, typeList: [], tokens: 0, tokenMax: 3, level: 1,
    cloaked: false, lkx: 0, lkz: 0, rogueChance: 0, rogueTime: 15, rogueDmgMul: 2, hitRogues: false };
  var CAP = 40, CORPSE_CAP = 16, TAU = Math.PI * 2;
  // share of Crawlers in the old look: all before level 20, then phased out (1/2 on 20, 1/4 on 21, none from 22)
  AI.oldShare = function (L) { return L < AI.SKIN2_LEVEL ? 1 : L === AI.SKIN2_LEVEL ? 0.5 : L === AI.SKIN2_LEVEL + 1 ? 0.25 : 0; };
  AI.SKIN2_LEVEL = 20; AI.SKIN2 = { grey: '#9AA1AB', black: '#2A2D34', specks: 1 / 3 };   // the Crawler's advanced skin
  // the Blade Bot's advanced skin (troops.js: Body2 / Hub2 / Katana2 / Axe2 / Kusari2): every Blade Bot from level 30, look only
  AI.BLADER_SKIN2_LEVEL = 30; AI.bladerSkin = function (L) { return L >= AI.BLADER_SKIN2_LEVEL ? 1 : 0; };
  var STEP_UP = 0.4;   // the highest walkable step a ground robot climbs onto (matches IB.Zones NAV_STEP)
  var ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
  var _m = new THREE.Matrix4(), _m2 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _v = new THREE.Vector3(), _s = new THREE.Vector3(1, 1, 1), _up = new THREE.Vector3(0, 1, 0), _ax = new THREE.Vector3(1, 0, 0), _c = new THREE.Color(), _dir = { x: 0, z: 0 }, _tmp = [], _mz = { x: 0, y: 0, z: 0 };
  var LIGHT_DIM = 0x7A6A4A;

  function stat(id, key, fallback) { var e = IB.ENEMIES && IB.ENEMIES[id]; return (e && e[key] !== undefined) ? e[key] : fallback; }
  function sock(name) { var p = IB.Assets.socket(name); return [p.x, p.y, p.z]; }
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function wrapAngle(d) { while (d > Math.PI) d -= TAU; while (d < -Math.PI) d += TAU; return d; }
  // windup tell (brief 4.4): the body flashes Paper White twice
  function tell(r, ph) { if ((ph > 0.05 && ph < 0.3) || (ph > 0.55 && ph < 0.8)) r.flash = Math.max(r.flash, 0.02); }
  function play(name, r, gain) { if (IB.Audio) IB.Audio.play(name, { pos: r, gain: gain }); }

  // ---------------- visual definitions ----------------
  /* Robot parts come from fps-bots.glb (Blender). Each VIS entry:
       radius (collision + hit capsule), y0/y1 (hit capsule: cylinder from y0 + r/2 to y1 - r/2, sphere caps),
       coreY/coreZ/coreR (weak point sphere, from the CORE socket), eye (sight height), home (engaged state),
       parts {Name: {count, asset, light}}, sockets(v), pose(r, P) every frame, corpse(v, add) rest pose for the silhouette. */
  var VIS = AI.VIS = {
    /* levels 20+ (AI.level >= SKIN2_LEVEL): half the Crawlers wear the advanced skin (Body2 / Leg2: plated shell, sloped
       head ring, wrap-around visor, panel lines; same silhouette, pivots and hit volumes), its armour painted per
       crawler in two key colours (keyMat2: r.tint on 'plate', r.tint2 on 'plate2'): 66 % grey / 33 % black or
       66 % black / 33 % grey, half each; about one in three also carries white specks and a stencil chevron. */
    crawler: {
      radius: 0.42, y0: 0.12, y1: 0.86, coreR: 0.17, shadow: 0.5, eye: 0.8, home: 'chase',
      parts: { Body: { count: 1, asset: 'BOT_CRAWLER_Body' }, Leg: { count: 4, asset: 'BOT_CRAWLER_Leg' }, Light: { count: 1, light: true, asset: 'BOT_CRAWLER_Light' },
        Body2: { count: 1, asset: 'BOT_CRAWLER_Body2', tint: 2, opt: true }, Leg2: { count: 4, asset: 'BOT_CRAWLER_Leg2', tint: 2, opt: true },
        Specks: { count: 1, asset: 'BOT_CRAWLER_Specks', opt: true } },
      sockets: function (v) {
        v.hips = [0, 1, 2, 3].map(function (i) { return sock('BOT_CRAWLER_HIP' + i); });
        var c = sock('BOT_CRAWLER_CORE'); v.coreY = c[1]; v.coreZ = 0;
      },
      init: function (r) {
        r.skin = Math.random() >= AI.oldShare(AI.level || 1) ? 1 : 0;
        if (!r.skin) return;
        var dark = Math.random() < 0.5, S = AI.SKIN2;   // dark: 66 % black / 33 % grey
        if (!r.tint) { r.tint = new THREE.Color(); r.tint2 = new THREE.Color(); }
        r.tint.set(dark ? S.black : S.grey); r.tint2.set(dark ? S.grey : S.black);
        r.split = dark ? 'black' : 'grey'; r.specks = Math.random() < S.specks;
      },
      pose: function (r, P) {
        var v = VIS.crawler, bob = Math.abs(Math.sin(r.walk * 2)) * 0.05, crouch = r.crouch;
        var bodyY = bob - crouch * 0.12, sk = r.skin === 1, B = sk ? 'Body2' : 'Body', L = sk ? 'Leg2' : 'Leg';
        P.set(B, 0, 0, bodyY, 0, 0, 1).hide(sk ? 'Body' : 'Body2', 0);
        if (sk && r.specks) P.set('Specks', 0, 0, bodyY, 0, 0, 1); else P.hide('Specks', 0);
        for (var i = 0; i < 4; i++) {
          var h = v.hips[i], ph = Math.sin(r.walk * 2 + (i % 2) * Math.PI);
          var sc = (h[1] + bodyY) / h[1] * (1 + ph * 0.06);
          P.set(L, i, h[0], h[1] + bodyY, h[2], 0, Math.max(0.5, sc)).hide(sk ? 'Leg' : 'Leg2', i);
        }
        P.set('Light', 0, 0.12, 1.08 + bodyY, -0.08, 0, 1);
      },
      corpse: function (v, add) {
        add('BOT_CRAWLER_Body', _m.identity());
        v.hips.forEach(function (h) { add('BOT_CRAWLER_Leg', _m.makeTranslation(h[0], h[1], h[2])); });
      }
    },

    // Wheelie bin with a pipe gun on a gold battery (the core). Tilts back on its wheels to roll,
    // lid lifts and the gun raises + slides out during the windup.
    gunner: {
      radius: 0.44, y0: 0.22, y1: 0.86, coreR: 0.17, shadow: 0.62, eye: 1.1, home: 'keep', wheelR: 0.125,
      parts: { Body: { count: 1, asset: 'BOT_GUNNER_Body' }, Lid: { count: 1, asset: 'BOT_GUNNER_Lid' }, Gun: { count: 1, asset: 'BOT_GUNNER_Gun' },
        Wheel: { count: 2, asset: 'BOT_GUNNER_Wheel' }, Light: { count: 1, light: true, asset: 'BOT_GUNNER_Light' } },
      sockets: function (v) {
        var c = sock('BOT_GUNNER_CORE'); v.coreY = c[1]; v.coreZ = c[2];
        v.hinge = sock('BOT_GUNNER_HINGE'); v.pivot = sock('BOT_GUNNER_GUNPIVOT'); v.light = sock('BOT_GUNNER_LIGHT');
        v.muzzle = sock('BOT_GUNNER_GUN'); v.wheels = [sock('BOT_GUNNER_WHEEL0'), sock('BOT_GUNNER_WHEEL1')];
      },
      pose: function (r, P) {
        var v = VIS.gunner, w = v.wheels[0], i;
        for (i = 0; i < 2; i++) P.root().tv(v.wheels[i]).rx(r.roll).emit('Wheel', i);
        var bob = Math.abs(Math.sin(r.roll * 2.5)) * 0.012 * Math.min(1, r.tilt * 8);
        P.root().t(0, w[1] + bob, w[2]).rx(-r.tilt).rz(r.wob).t(0, -w[1], -w[2]).emit('Body', 0);
        P.push().tv(v.hinge).rx(-r.lid).emit('Lid', 0).pop();
        P.push().tv(v.pivot).rx(-r.aim).t(0, 0, r.gunOut - r.kick * 0.06).emit('Gun', 0).pop();
        P.tv(v.light).emit('Light', 0);
      },
      corpse: function (v, add) {
        add('BOT_GUNNER_Body', _m.identity());
        add('BOT_GUNNER_Lid', _m.makeTranslation(v.hinge[0], v.hinge[1], v.hinge[2]));
        add('BOT_GUNNER_Gun', _m.makeRotationX(0.4).setPosition(v.pivot[0], v.pivot[1], v.pivot[2]));
        v.wheels.forEach(function (h) { add('BOT_GUNNER_Wheel', _m.makeTranslation(h[0], h[1], h[2])); });
      }
    },

    // Fizzing bottle in a roller fork; the cap pops and the wick sparks during the fuse; strapped gold canister core.
    bomber: {
      radius: 0.3, y0: 0.15, y1: 0.9, coreR: 0.13, shadow: 0.42, eye: 0.8, home: 'chase', wheelR: 0.13,
      parts: { Body: { count: 1, asset: 'BOT_BOMBER_Body' }, Roller: { count: 1, asset: 'BOT_BOMBER_Roller' }, Cap: { count: 1, asset: 'BOT_BOMBER_Cap' },
        Light: { count: 1, light: true, asset: 'BOT_BOMBER_Light' } },
      sockets: function (v) {
        var c = sock('BOT_BOMBER_CORE'); v.coreY = c[1]; v.coreZ = c[2];
        v.axle = sock('BOT_BOMBER_AXLE'); v.cap = sock('BOT_BOMBER_CAP'); v.wick = sock('BOT_BOMBER_WICK');
      },
      pose: function (r, P) {
        var v = VIS.bomber, a = v.axle, lit = r.fuse > 0;
        P.root().tv(a).rx(r.roll).emit('Roller', 0);
        var jit = lit ? Math.sin(r.st * 70) * 0.05 : Math.sin(r.idleT * 9) * 0.012;
        var sw = lit ? 0.06 * (1 - r.fuse / r.fuse0) : 0;
        P.root().tv(a).rx(r.tilt).rz(jit + r.wob).t(-a[0], -a[1], -a[2]).s(1 + sw, 1 + sw * 0.5, 1 + sw).emit('Body', 0);
        P.tv(v.cap).t(0, r.capPop * 0.07, 0).ry(r.capPop * r.st * 9).rx(r.capPop * 0.25).emit('Cap', 0);
        var sp = lit ? 0.9 + Math.random() * 0.8 : (r.state === 'chase' || r.alert > 0 ? 0.55 : 0.35);
        P.tv(v.wick).ry(r.st * 13).s(sp, sp, sp).emit('Light', 0);
      },
      lightColor: function (r) {
        if (r.fuse > 0) { var k = (r.st * 25) | 0; return k % 3 === 0 ? PAL.paper : k % 3 === 1 ? PAL.amber : PAL.red; }
        return lightDefault(r);
      },
      corpse: function (v, add) {
        add('BOT_BOMBER_Body', _m.identity());
        add('BOT_BOMBER_Roller', _m.makeTranslation(v.axle[0], v.axle[1], v.axle[2]));
        add('BOT_BOMBER_Cap', _m.makeTranslation(v.cap[0], v.cap[1], v.cap[2]));
      },
      onDeath: function (r, quiet) {
        if (quiet || !IB.Projectiles || !IB.Projectiles.explode) return;
        var d = r.def;
        IB.Projectiles.explode(r.x, r.y + 0.45, r.z, d.blastRadius || 3, (r.rogue > 0 || r.rogueEnd) ? 0 : (d.damage || 35) * r.dmgMul, (d.robotDamage || 45) * (AI.hpMul || 1), r);
      }
    },

    // Soda can with a 4-rotor lid; hovers 3 m up, banks into its strafe; lid lifts and the gun drops to aim on the windup.
    drone: {
      radius: 0.34, y0: 0.1, y1: 0.58, coreR: 0.13, shadow: 0.45, eye: 0.3, home: 'keep', flying: true, centre: 0.3,
      parts: { Body: { count: 1, asset: 'BOT_DRONE_Body' }, Lid: { count: 1, asset: 'BOT_DRONE_Lid' }, Rotor: { count: 4, asset: 'BOT_DRONE_Rotor' },
        Gun: { count: 1, asset: 'BOT_DRONE_Gun' }, Light: { count: 1, light: true, asset: 'BOT_DRONE_Light' } },
      sockets: function (v) {
        var c = sock('BOT_DRONE_CORE'); v.coreY = c[1]; v.coreZ = c[2];
        v.lid = sock('BOT_DRONE_LID'); v.pivot = sock('BOT_DRONE_GUNPIVOT'); v.muzzle = sock('BOT_DRONE_GUN'); v.light = sock('BOT_DRONE_LIGHT');
        v.rotors = [0, 1, 2, 3].map(function (i) { return sock('BOT_DRONE_ROTOR' + i); });
      },
      pose: function (r, P) {
        var v = VIS.drone, c = v.centre;
        P.root().t(0, c, 0).rx(r.bankX).rz(r.bankZ + r.wob).t(0, -c, 0).emit('Body', 0);
        P.push().tv(v.pivot).rx(-r.aim).t(0, 0, -r.kick * 0.04).emit('Gun', 0).pop();
        P.tv(v.lid).t(0, r.lid * 0.13, 0).emit('Lid', 0);
        for (var i = 0; i < 4; i++) P.push().tv(v.rotors[i]).ry((i & 1 ? r.spin : -r.spin) + i).emit('Rotor', i).pop();
        P.tv(v.light).emit('Light', 0);
      },
      corpse: function (v, add) {
        add('BOT_DRONE_Body', _m.identity());
        add('BOT_DRONE_Lid', _m.makeTranslation(v.lid[0], v.lid[1], v.lid[2]));
        v.rotors.forEach(function (q, i) { add('BOT_DRONE_Rotor', _m.makeRotationY(i * 0.8).setPosition(v.lid[0] + q[0], v.lid[1] + q[1], v.lid[2] + q[2])); });
        add('BOT_DRONE_Gun', _m.makeTranslation(v.pivot[0], v.pivot[1], v.pivot[2]));
      }
    }
  };

  function lightDefault(r) {
    var lit = r.alert > 0 ? (Math.sin(r.alert * 40) > 0) : (r.state === 'chase' || r.state === 'keep' || r.state === 'windup' || r.state === 'attack' || r.state === 'recover');
    return lit ? PAL.amber : LIGHT_DIM;
  }

  // ---------------- materials / meshes ----------------
  AI.init = function (scene) {
    AI.scene = scene;
    splitCan();   // before any level is built: zones merge the lidless body, the lids are their own meshes
    var cmat = new THREE.MeshBasicMaterial({ color: PAL.ink, transparent: true, depthWrite: true });
    cmat.onBeforeCompile = function (sh) {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aOp;\nvarying float vOp;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvOp = aOp;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vOp;').replace('#include <fog_fragment>', 'gl_FragColor.a *= vOp;\n#include <fog_fragment>');
    };
    cmat.customProgramCacheKey = function () { return 'ibcorpse'; };
    AI.corpseMat = cmat;
    var A = IB.Assets, bake = A.BAKED.bots;
    AI.mat = IB.Render.toonMaterial({ fx: true, map: A.palette.bots, baked: bake, uni: IB.Render.robotOutline, look: 'actor', surf: IB.Surface && IB.Surface.surf('bots') });   // own ink colour (Undercover)
    tintMaterial(AI.mat);
    AI.lightMat = IB.Render.toonMaterial({ map: A.palette.bots, baked: bake, uni: IB.Render.robotOutline, look: 'actor', surf: IB.Surface && IB.Surface.surfAll(15) });   // tactical look: robot lights are emissive (bloom)
    // armour recolour (Soldier variants): the palette's key armour texels take a per-instance colour (aTint)
    AI.keyMat = IB.Render.toonMaterial({ fx: true, map: A.palette.bots, baked: bake, uni: IB.Render.robotOutline, look: 'actor', surf: IB.Surface && IB.Surface.surf('bots') });
    tintMaterial(AI.keyMat); keyTintMaterial(AI.keyMat);
    // two-colour recolour (the Crawler's advanced skin): 'plate' takes aTint, 'plate2' its own aTint2
    AI.keyMat2 = IB.Render.toonMaterial({ fx: true, map: A.palette.bots, baked: bake, uni: IB.Render.robotOutline, look: 'actor', surf: IB.Surface && IB.Surface.surf('bots') });
    tintMaterial(AI.keyMat2); keyTintMaterial(AI.keyMat2, true);
    Object.keys(VIS).forEach(function (id) {
      var v = VIS[id], T = { id: id, vis: v, parts: {}, partList: [], slots: [], corpse: null, hi: -1 };
      v.sockets(v);
      Object.keys(v.parts).forEach(function (pn) {
        var P = v.parts[pn];
        var geo = A.get(P.asset).clone(), n = CAP * P.count;
        if (!P.light) { var fx = new THREE.InstancedBufferAttribute(new Float32Array(n * 4), 4); fx.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aFx', fx); }
        if (P.tint) { var ta = new THREE.InstancedBufferAttribute(new Float32Array(n * 3).fill(1), 3); ta.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aTint', ta); }
        if (P.tint === 2) { var t2 = new THREE.InstancedBufferAttribute(new Float32Array(n * 3).fill(1), 3); t2.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('aTint2', t2); }
        var im = new THREE.InstancedMesh(geo, P.light ? AI.lightMat : P.tint === 2 ? AI.keyMat2 : P.tint ? AI.keyMat : AI.mat, n);
        im.instanceMatrix.setUsage(THREE.DynamicDrawUsage); im.frustumCulled = false;
        for (var i = 0; i < n; i++) { im.setMatrixAt(i, ZERO); if (P.light) im.setColorAt(i, _c.set(LIGHT_DIM)); }
        scene.add(im);
        // opt: a shape variant (only some robots wear it): drawn only in frames where a live robot uses it
        T.parts[pn] = { name: pn, mesh: im, count: P.count, fx: im.geometry.attributes.aFx || null, tint: im.geometry.attributes.aTint || null,
          tint2: im.geometry.attributes.aTint2 || null, opt: !!P.opt, used: false, lc: P.lightColor || null };   // lc: a light part's own colour (r)
        T.partList.push(T.parts[pn]);
      });
      // corpse geometry: whole robot in rest pose, all ink
      var cparts = [];
      v.corpse(v, function (asset, mat) { cparts.push(A.placed(asset, mat)); });
      var cgeo = A.merge(cparts);
      ['aHull', 'uv', 'color', 'normal'].forEach(function (k) { cgeo.deleteAttribute(k); });
      var op = new THREE.InstancedBufferAttribute(new Float32Array(CORPSE_CAP), 1); op.setUsage(THREE.DynamicDrawUsage); cgeo.setAttribute('aOp', op);
      var cm = new THREE.InstancedMesh(cgeo, cmat, CORPSE_CAP);
      cm.instanceMatrix.setUsage(THREE.DynamicDrawUsage); cm.frustumCulled = false;
      for (var k = 0; k < CORPSE_CAP; k++) cm.setMatrixAt(k, ZERO);
      scene.add(cm);
      T.corpse = cm; T.corpses = [];
      for (k = 0; k < CORPSE_CAP; k++) T.corpses.push({ on: false, t: 0, x: 0, y: 0, z: 0, vy: 0, yaw: 0, tip: 1, fy: 0 });
      for (var s = 0; s < CAP; s++) { var r = newRobot(id, s); T.slots.push(r); AI.robots.push(r); }
      AI.types[id] = T; AI.typeList.push(T);
    });
  };

  /* robot material: aFx grows to vec4 (x flash, y ink, z tint kind, w tint amount). Kind 1 = rogue (teal body and a teal
     outline), kind 2 = wet (Hydrate: cold blue, a rim sheen and a hard comic glint). */
  var TINT_GLSL = [
    'if ( vFx.z > 0.5 && vFx.z < 1.5 ) {',
    '  float lum = dot( gl_FragColor.rgb, vec3( 0.333 ) );',
    '  gl_FragColor.rgb = mix( gl_FragColor.rgb, vec3( 0.07, 0.78, 0.71 ) * ( 0.45 + 0.75 * lum ), vFx.w );',
    '} else if ( vFx.z > 1.5 ) {',
    '  vec3 nw = normalize( normal );',
    '  float rim = pow( 1.0 - abs( nw.z ), 2.0 );',
    '  float glint = step( 0.9, dot( nw, normalize( vec3( -0.35, 0.75, 0.55 ) ) ) );',
    '  gl_FragColor.rgb = mix( gl_FragColor.rgb, gl_FragColor.rgb * vec3( 0.55, 0.78, 1.2 ) + vec3( 0.0, 0.04, 0.12 ), vFx.w );',
    '  gl_FragColor.rgb += vFx.w * ( rim * vec3( 0.25, 0.55, 0.95 ) * 0.7 + glint * vec3( 0.85, 0.95, 1.0 ) );',
    '}',
    'if ( vHull > 0.5 ) gl_FragColor = vec4( ( vFx.z > 0.5 && vFx.z < 1.5 ) ? mix( uInk, vec3( 0.07, 0.85, 0.78 ), vFx.w ) : uInk, 1.0 );'
  ].join('\n');
  /* key-colour recolour: texels of the two armour key swatches ('plate' #F4F6F9, 'plate2' #B8BEC7 in fam_bots.py)
     take the instance colour aTint (plate2 a shade darker); everything else keeps its palette colour */
  function keyTintMaterial(mat, dual) {
    var base = mat.onBeforeCompile, key = mat.customProgramCacheKey;
    mat.onBeforeCompile = function (sh) {
      base(sh);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec3 aTint;\nvarying vec3 vTint;' + (dual ? '\nattribute vec3 aTint2;\nvarying vec3 vTint2;' : ''))
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvTint = aTint;' + (dual ? '\nvTint2 = aTint2;' : ''));
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vTint;' + (dual ? '\nvarying vec3 vTint2;' : ''))
        .replace('#include <map_fragment>', ['#include <map_fragment>',
          '#ifdef USE_MAP',
          'float ibK1 = step( distance( texelColor.rgb, vec3( 0.957, 0.965, 0.976 ) ), 0.012 );',
          'float ibK2 = step( distance( texelColor.rgb, vec3( 0.722, 0.745, 0.780 ) ), 0.012 );',
          'diffuseColor.rgb = mix( diffuseColor.rgb, vTint, ibK1 );',
          dual ? 'diffuseColor.rgb = mix( diffuseColor.rgb, vTint2, ibK2 );' : 'diffuseColor.rgb = mix( diffuseColor.rgb, vTint * 0.66, ibK2 );',
          '#endif'].join('\n'));
    };
    mat.customProgramCacheKey = function () { return key() + (dual ? 'key2' : 'key'); };
  }
  function tintMaterial(mat) {
    var base = mat.onBeforeCompile, key = mat.customProgramCacheKey;
    mat.onBeforeCompile = function (sh) {
      base(sh);
      sh.vertexShader = sh.vertexShader.replace('attribute vec2 aFx;\nvarying vec2 vFx;', 'attribute vec4 aFx;\nvarying vec4 vFx;');
      sh.fragmentShader = sh.fragmentShader.replace('varying vec2 vFx;', 'varying vec4 vFx;')
        .replace('if ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );', TINT_GLSL);
    };
    mat.customProgramCacheKey = function () { return key() + 'tint'; };
  }

  function newRobot(type, slot) {
    return { type: type, slot: slot, def: IB.ENEMIES && IB.ENEMIES[type] || {}, on: false, state: 'off', st: 0, x: 0, y: 0, z: 0, vx: 0, vz: 0, yaw: 0, hp: 1, maxHp: 1,
      zone: -1, flash: 0, walk: 0, crouch: 0, token: false, bit: false, lx: 0, lz: 0, losT: Math.random() * 0.2, seesPlayer: false, lost: 0,
      zig: Math.random() * 6, sx: 0, sz: 0, tx: 0, tz: 0, kx: 0, kz: 0, alert: 0, blind: 0, wanderT: 0, wx: 0, wz: 0, dmgMul: 1, pose: false, idleT: Math.random() * 5,
      // ranged / vehicle state
      cool: 0, thinkT: 0, mode: 'approach', gx: 0, gz: 0, sdir: 1, bump: 0, shots: 0, shotT: 0, aimTo: 0,
      roll: 0, tilt: 0, wob: 0, lid: 0, aim: -0.45, gunOut: 0, kick: 0, hy: 0, spin: Math.random() * 6, bankX: 0, bankZ: 0,
      fuse: 0, fuse0: 0.6, capPop: 0, fizzT: Math.random(),
      // walkable surfaces: floor under the robot, smoothed foot height, its fall speed, the Crawler's lunge hop
      fy: 0, gy: 0, fvy: 0, hop: 0,
      // skills: rogue seconds left (Handy Helpers), wet seconds left (Hydrate), current robot target
      rogue: 0, rogueEnd: false, wet: 0, tgt: null, tgtT: 0,
      // overwhelm / pathing: close-range slot, held at the ring this frame, flow-field detour time, ignored rogue
      close: true, held: false, navT: 0, ign: null, ignT: 0, rtT: 0, pd: 0,
      // flyers: ceiling over the robot (re-checked every 0.25 s)
      ceil: Infinity, ceilT: 0,
      // spawn can hop-out: the can it climbs out of, landing squash
      squash: 0, canX: 0, canZ: 0, canY: 0 };
  }

  AI.clear = function () {
    AI.robots.forEach(function (r) { r.on = false; r.state = 'off'; r.token = false; r.fuse = 0; r.rogue = 0; r.wet = 0; r.tgt = null; });
    AI.cloaked = false;
    AI.typeList.forEach(function (T) { T.corpses.forEach(function (c) { c.on = false; }); });
    AI.tokens = 0;
  };
  AI.setLevel = function (L) {
    AI.level = L; AI.tokenMax = 3 + Math.floor(L / 5);
    AI.hpMul = IB.Damage ? IB.Damage.enemyHpMul(L) : 1 + 0.06 * (L - 1);
    AI.dmgMul = IB.Damage ? IB.Damage.enemyDmgMul(L) : Math.min(3, 1 + 0.04 * (L - 1));
    // levels 1-7: everything robots shoot or throw at the player (bolts, blasts) deals 25% less (projectiles.js)
    AI.rangedMul = L <= 7 ? 0.75 : 1;
    // per-level tempo: volley pauses, aim spread and lead, windup tells, move speed (core/damage.js enemyTempo)
    AI.tempo = IB.Damage && IB.Damage.enemyTempo ? IB.Damage.enemyTempo(L) : TEMPO1;
  };
  var TEMPO1 = { coolMul: 1, aimMul: 1, leadAdd: 0, tellMul: 1, speedMul: 1 };
  function tempo() { return AI.tempo || TEMPO1; }

  // ---------------- spawn cans: a hinged lid that pops open as a robot climbs out ----------------
  /* The common kit's SpawnCan is one mesh; split it once (generic: by height and by the hull shell flag) into the body
     (stays the asset zones.js merges into each zone) and the lid (IB.Assets.geo.SpawnCan_Lid, hinge at the origin:
     the lid's back rim). A triangle belongs to the lid when it lies wholly in the top 20 % of the can, except flat
     faces no wider than the body below (the body's own top cap stays, so the open can is not see-through). */
  var CAN = AI.CAN = { hingeY: 0.95, hingeZ: -0.5, open: 1.95, popV: 15, spring: 70, damp: 7, bounce: 0.35, ready: false };
  function splitCan() {
    var A = IB.Assets; if (CAN.ready || !A || !A.geo || !A.geo.SpawnCan || !A.geo.SpawnCan.index) return;
    var g = A.geo.SpawnCan, pos = g.attributes.position.array, hull = g.attributes.aHull ? g.attributes.aHull.array : null, ix = g.index.array;
    var hs = hull ? g.attributes.aHull.itemSize : 0;
    function isHull(v) { if (!hull) return 0; for (var k = 0; k < hs; k++) if (hull[v * hs + k] !== 0) return 1; return 0; }
    g.computeBoundingBox();
    var y0 = g.boundingBox.min.y, y1 = g.boundingBox.max.y, ys = y0 + (y1 - y0) * 0.8, bodyR = [0, 0], t, k, v;
    for (t = 0; t < ix.length; t += 3) {
      var lo = 1e9; for (k = 0; k < 3; k++) lo = Math.min(lo, pos[ix[t + k] * 3 + 1]);
      if (lo >= ys) continue;
      for (k = 0; k < 3; k++) { v = ix[t + k]; var h = isHull(v); bodyR[h] = Math.max(bodyR[h], Math.hypot(pos[v * 3], pos[v * 3 + 2])); }
    }
    var body = [], lid = [], lidLo = 1e9, lidZ = 0;
    for (t = 0; t < ix.length; t += 3) {
      var mn = 1e9, mx = -1e9, rr = 0, hh = isHull(ix[t]);
      for (k = 0; k < 3; k++) { v = ix[t + k]; var y = pos[v * 3 + 1]; mn = Math.min(mn, y); mx = Math.max(mx, y); rr = Math.max(rr, Math.hypot(pos[v * 3], pos[v * 3 + 2])); }
      var flatTop = mn >= ys && mx - mn < 0.004 && rr <= bodyR[hh] + 0.005;   // the body's own top face, under the lid
      var isLid = mn >= ys && !flatTop;
      // the can is open under its lid: the body's solid top face is left out, so a swung-up lid shows the dark inside
      // of the can (the inside of the outline shell, which keeps its top face: that one only shows from within)
      if (flatTop && !hh) continue;
      (isLid ? lid : body).push(ix[t], ix[t + 1], ix[t + 2]);
      if (isLid && !hh) { lidLo = Math.min(lidLo, mn); for (k = 0; k < 3; k++) { v = ix[t + k]; lidZ = Math.min(lidZ, pos[v * 3 + 2]); } }
    }
    if (!lid.length || !body.length) return;
    CAN.hingeY = lidLo; CAN.hingeZ = lidZ;
    var lg = g.clone(); lg.setIndex(lid); lg.translate(0, -CAN.hingeY, -CAN.hingeZ);
    // translate() moves positions only; the outline direction (aHull) is a direction and stays as it is
    lg.computeBoundingSphere(); lg.computeBoundingBox();
    var bg = g.clone(); bg.setIndex(body); bg.computeBoundingSphere(); bg.computeBoundingBox();
    A.geo.SpawnCan = bg; A.geo.SpawnCan_Lid = lg; A.family.SpawnCan_Lid = A.family.SpawnCan || 'common';
    CAN.ready = true;
  }
  /* one lid per spawn can of a freshly built level (zone.spawns), in its zone's group so it shows and hides with it */
  AI.setupCans = function (level) {
    AI.cans = [];
    if (!CAN.ready || !level) return;
    var geo = IB.Assets.geo.SpawnCan_Lid, mat = IB.Assets.mat[IB.Assets.family.SpawnCan_Lid];
    level.zones.forEach(function (z) {
      (z.spawns || []).forEach(function (sp, i) {
        var piv = new THREE.Group(), m = new THREE.Mesh(geo, mat);
        piv.rotation.order = 'YXZ'; piv.add(m); z.group.add(piv);
        var c = { x: sp.x, y: sp.y || 0, z: sp.z, zone: z.idx, piv: piv, a: 0, v: 0, hold: 0 };
        canYaw(c, (i * 2.39996) % TAU);   // the closed lid is round: any hinge side looks the same
        sp.can = c; AI.cans.push(c);
      });
    });
  };
  // hinge side: the lid's back rim at local z = hingeZ, rotated about the can's axis by yaw
  function canYaw(c, yaw) {
    c.yaw = yaw; c.piv.rotation.y = yaw;
    c.piv.position.set(c.x + Math.sin(yaw) * CAN.hingeZ, c.y + CAN.hingeY, c.z + Math.cos(yaw) * CAN.hingeZ);
  }
  function canAt(x, z) {
    var cs = AI.cans || [], best = 0.36, bc = null;
    for (var i = 0; i < cs.length; i++) { var d = Math.abs(cs[i].x - x) + Math.abs(cs[i].z - z); if (d < best) { best = d; bc = cs[i]; } }
    return bc;
  }
  // lid: kicked open when a robot pops out, held open while it climbs out, then swings shut with a clatter and settles
  function updateCans(dt) {
    var cs = AI.cans || [];
    for (var i = 0; i < cs.length; i++) {
      var c = cs[i]; if (c.hold <= 0 && c.a === 0 && c.v === 0) continue;
      c.hold -= dt;
      var tgt = c.hold > 0 ? CAN.open : 0;
      c.v += (CAN.spring * (tgt - c.a) - CAN.damp * c.v) * dt; c.a += c.v * dt;
      if (c.a > CAN.open + 0.25) { c.a = CAN.open + 0.25; c.v = Math.min(0, c.v); }
      if (c.a < 0) {   // slams shut: bounce, a puff of dust once it settles
        if (c.v < -2.5) { if (IB.FX) IB.FX.puff(c.x, c.y + CAN.hingeY, c.z, 3, PAL.ink, 0.1, 0.3, 1.2); if (IB.Audio) IB.Audio.play('clank', { pos: c, gain: 0.35 }); }
        c.a = 0; c.v = Math.abs(c.v) > 1.2 ? -c.v * CAN.bounce : 0;
      }
      if (c.hold <= 0 && Math.abs(c.a) < 0.004 && Math.abs(c.v) < 0.05) { c.a = 0; c.v = 0; }
      c.piv.rotation.x = -c.a;   // lid tips back about its hinge
    }
  }
  AI.updateCans = updateCans;
  AI.canState = function () { return (AI.cans || []).map(function (c) { return { a: +c.a.toFixed(3), hold: c.hold > 0 }; }); };
  /* the hop out (SPAWN_T s): crouched in the can as the lid pops (0-0.2), rises to the rim (0.2-0.45), springs up and
     out in an arc to the landing spot beside the can (0.45-0.95), squashes on landing; a flyer lifts out instead and
     climbs to its hover height. The squash eases off after the spawn (r.squash, AI.sync). */
  var SPAWN_T = 0.95;
  AI.SPAWN_T = SPAWN_T;
  function ease(x) { return x * x * (3 - 2 * x); }
  function spawnPose(r, dt, fly, world) {
    var t = r.st, sy = r.canY, rim = sy + CAN.hingeY + 0.05, c = r.can;
    if (c && t < 0.6) c.hold = Math.max(c.hold, 0.45);
    if (t < 0.2) {
      var k0 = t / 0.2;
      r.x = r.canX; r.z = r.canZ; r.y = sy + 0.05 + 0.15 * k0; r.crouch = 1; r.squash = 0.35 * (1 - k0);
      if (c && t >= 0.06 && c.v === 0 && c.a < 0.1) {
        canYaw(c, Math.atan2(r.tx - r.canX, r.tz - r.canZ));   // hinge on the side away from the hop: the lid flips back
        c.v = CAN.popV; if (IB.FX) IB.FX.puff(r.canX, rim, r.canZ, 5, PAL.ink, 0.14, 0.4, 2.2); }
    } else if (t < 0.45) {
      var k1 = ease((t - 0.2) / 0.25);
      r.x = r.canX; r.z = r.canZ; r.y = sy + 0.2 + (rim - 0.15 - (sy + 0.2)) * k1; r.crouch = 1 - k1 * 0.4; r.squash = -0.18 * Math.sin(k1 * Math.PI);   // stretch as it pushes up
    } else {
      var k = Math.min(1, (t - 0.45) / (SPAWN_T - 0.45)), kk = ease(k);
      r.x = r.canX + (r.tx - r.canX) * kk; r.z = r.canZ + (r.tz - r.canZ) * kk;
      if (fly) {
        var hov = r.landY + r.hy; if (r.ceil < Infinity) hov = Math.min(hov, Math.max(r.landY + 0.5, r.ceil - VIS[r.type].y1 - 0.2));
        r.y = rim - 0.15 + (hov - (rim - 0.15)) * kk + Math.sin(k * Math.PI) * 0.35;
        r.crouch = 0; r.squash = 0;
      } else {
        var a = rim - 0.15, b = r.landY;   // ballistic-looking arc: up 0.7 m over the rim, down onto the floor
        r.y = a + (b - a) * k + Math.sin(k * Math.PI) * (0.7 + Math.max(0, a - b) * 0.25);
        r.crouch = Math.max(0, 0.6 - k * 1.5); r.squash = k < 0.25 ? -0.12 * (1 - k / 0.25) : 0;   // tucks, then stretches out
      }
    }
    r.walk += dt * 6;
  }

  AI.spawn = function (type, x, z, zone, tx, tz, opts) {
    var T = AI.types[type]; if (!T) return null;
    var r = null; for (var i = 0; i < CAP; i++) if (!T.slots[i].on) { r = T.slots[i]; break; }
    if (!r) return null;
    opts = opts || {};
    var v = VIS[type];
    r.on = true; r.zone = zone; r.state = opts.pose ? 'pose' : 'spawn'; r.st = 0; r.pose = !!opts.pose;
    r.maxHp = r.hp = stat(type, 'hp', 30) * (AI.hpMul || 1);
    r.sx = x; r.sz = z; r.x = x; r.z = z; r.tx = tx; r.tz = tz;
    r.hy = v.flying ? stat(type, 'hover', 3) - v.centre : 0;
    r.sy = opts.y || 0;   // the floor the spawn can stands on (a mezzanine spawn stands on the deck)
    r.y = r.sy + (opts.pose ? r.hy : 1.0);
    r.vx = r.vz = 0; r.kx = r.kz = 0; r.flash = 0; r.crouch = 0; r.token = false; r.alert = 0; r.blind = 0;
    r.cool = 0.6 + Math.random() * 1.2; r.thinkT = 0; r.mode = 'approach'; r.sdir = Math.random() < 0.5 ? -1 : 1; r.bump = 0; r.lost = 0;
    r.tilt = 0; r.wob = 0; r.pull = r.pullTgt = 0; r.lid = 0; r.aim = -0.45; r.gunOut = 0; r.kick = 0; r.bankX = r.bankZ = 0; r.fuse = 0; r.capPop = 0;
    r.yaw = Math.atan2(tx - x, tz - z); r.walk = Math.random() * 3; r.dmgMul = (AI.dmgMul || 1) * (opts.dmgScale || 1);
    r.rogue = 0; r.rogueEnd = false; r.wet = 0; r.tgt = null; r.tgtT = 0; r.slowT = 0;
    r.fy = r.gy = 0; r.fvy = 0; r.hop = 0;
    r.close = true; r.held = false; r.navT = 0; r.ign = null; r.ignT = 0; r.rtT = 0; r.ceil = Infinity; r.ceilT = 0; r.squash = 0;
    r.canX = x; r.canZ = z; r.canY = r.sy;
    r.maxShield = r.shield = 0;
    if (v.init) v.init(r, opts);   // per-type spawn state (troops.js: armour variant, shield pool, grenades, blade)
    r.can = opts.pose ? null : canAt(x, z);
    if (!opts.pose) {
      var W0 = IB.Zones && IB.Zones.world;
      r.landY = W0 && W0.floorAt ? W0.floorAt(tx, tz, r.sy + STEP_UP) : r.sy;
      r.fy = r.landY; r.ceil = v.flying && W0 ? flyCeil(r, W0, AI.levelRef) : Infinity;
      r.x = x; r.z = z; r.y = r.sy + 0.05;
    }
    return r;
  };

  AI.alive = function (zone) {
    // rogue robots (Handy Helpers) already counted as kills: they never hold a zone open
    var n = 0; for (var i = 0; i < AI.robots.length; i++) { var r = AI.robots[i]; if (r.on && r.state !== 'pose' && !(r.rogue > 0) && (zone === undefined || r.zone === zone)) n++; }
    return n;
  };
  // test hook / zone wipe: quiet kills (Bombers do not blow up)
  AI.killAll = function (zone, cb) {
    AI.robots.forEach(function (r) { if (r.on && r.state !== 'pose' && !(r.rogue > 0) && (zone === undefined || r.zone === zone)) AI.kill(r, cb, true); });
  };
  AI.despawn = function (zone) { AI.robots.forEach(function (r) { if (r.on && (zone === undefined || r.zone === zone)) { releaseToken(r); r.on = false; r.state = 'off'; r.fuse = 0; } }); };

  function releaseToken(r) { if (r.token) { r.token = false; AI.tokens = Math.max(0, AI.tokens - 1); } }
  function setState(r, s) { if ((s !== 'windup' && s !== 'attack') && r.token && s !== 'recover') releaseToken(r); r.state = s; r.st = 0; }
  // attack tokens ration the robots attacking the player at once; robot-vs-robot fights (rogues) need none
  var _freeToken = false;
  function takeToken(r) { if (_freeToken) return true; if (r.token || AI.tokens >= AI.tokenMax) return r.token; r.token = true; AI.tokens++; return true; }

  // hearing: wake robots within radius
  AI.hear = function (x, z, radius) {
    for (var i = 0; i < AI.robots.length; i++) {
      var r = AI.robots[i]; if (!r.on || r.state !== 'idle') continue;
      var dx = r.x - x, dz = r.z - z; if (dx * dx + dz * dz < radius * radius) { setState(r, 'alert'); }
    }
  };
  /* Pop Flash: stop attacking, spin slowly for secs (3.5 s, 1.5 s if facing away; brief 4.4) */
  AI.blind = function (r, secs) {
    if (!r.on || r.state === 'spawn' || r.state === 'pose') return;
    setState(r, 'blinded'); r.blind = secs || 3.5;
  };

  /* damage: returns true if killed. opts: {stagger, kx, kz} */
  AI.damage = function (r, dmg, opts, onKill) {
    if (!r.on || r.state === 'spawn' || r.state === 'pose') return false;
    opts = opts || {};
    if (r.rogue > 0) onKill = null;   // a rogue was already paid for; whoever wrecks it earns nothing
    var vd = VIS[r.type];
    if (vd.onDamage) {   // per-type: a shield pool soaks it first (Soldier), a dizzy Blade Bot takes more
      dmg = vd.onDamage(r, dmg, opts);
      if (!(dmg > 0)) { r.flash = 0.06; if (r.state === 'idle') setState(r, 'alert'); return false; }
    }
    r.hp -= dmg; r.flash = 0.06;
    if (r.state === 'idle') setState(r, 'alert');
    if (r.hp <= 0) {
      // Handy Helpers: a robot the player wrecks may turn rogue instead (it still counts as the player's kill)
      if (onKill && AI.rogueChance > 0 && !r.def.boss && Math.random() < AI.rogueChance) { AI.makeRogue(r, AI.rogueTime); onKill(r); paid(r); return true; }
      AI.kill(r, onKill); return true;
    }
    if ((dmg >= r.maxHp * 0.25 || opts.stagger) && !(vd.noStagger && vd.noStagger(r))) {
      setState(r, 'stagger'); r.kx = opts.kx || 0; r.kz = opts.kz || 0; r.crouch = 0;
    }
    return false;
  };
  /* kill: ink silhouette + chunks; onKill (gems, feed) only for kills the player earned; quiet skips death effects (Bomber blast) */
  AI.kill = function (r, onKill, quiet) {
    if (!r.on) return;
    releaseToken(r);
    r.on = false; r.state = 'off';
    var T = AI.types[r.type], c = null, v = VIS[r.type];
    for (var i = 0; i < CORPSE_CAP; i++) if (!T.corpses[i].on) { c = T.corpses[i]; c.idx = i; break; }
    if (!c) { var oldest = 0; for (i = 1; i < CORPSE_CAP; i++) if (T.corpses[i].t > T.corpses[oldest].t) oldest = i; c = T.corpses[oldest]; c.idx = oldest; }
    c.on = true; c.t = 0; c.x = r.x; c.y = r.y; c.vy = 0; c.z = r.z; c.yaw = r.yaw; c.tip = Math.random() < 0.5 ? 1 : -1; c.fy = r.fy || 0;
    var my = r.y + 0.5;
    if (IB.Boom && IB.Boom.ready) IB.Boom.robotDeath(r, quiet);   // comic explosion per type (Drones drop and blow up on impact)
    else if (IB.FX) { IB.FX.chunk(r.x, my, r.z, 3 + ((Math.random() * 4) | 0), 3); IB.FX.puff(r.x, my, r.z, 6, PAL.ink, 0.25, 0.7, 3); }
    r.fuse = 0;
    var rogue = r.rogue > 0 || r.rogueEnd;
    if (v.onDeath) v.onDeath(r, quiet);
    // a rogue self-destructs: a blast that only hurts robots (Bombers already blew up in onDeath, harmless to the player)
    if (rogue && !quiet && !v.onDeath && IB.Projectiles && IB.Projectiles.explode) IB.Projectiles.explode(r.x, r.y + 0.45, r.z, 2.6, 0, 30 * (AI.hpMul || 1), r);
    r.rogue = 0; r.rogueEnd = false; r.wet = 0; r.tgt = null;
    if (onKill && !rogue) { onKill(r); paid(r); }
  };
  // a kill the player earned: per-type extras (troops.js: weapon drops)
  function paid(r) { var v = VIS[r.type]; if (v.onPlayerKill) v.onPlayerKill(r); }
  /* Handy Helpers: r fights for the player (3-5x health, teal) until destroyed (rogueTime Infinity; a finite t
     still counts down and self-destructs) */
  AI.makeRogue = function (r, t) {
    if (!r.on || r.state === 'pose') return false;
    releaseToken(r);
    r.rogue = t || AI.rogueTime || 15; r.rogueEnd = false;
    var hm = AI.rogueHpMul || [1, 1]; r.maxHp *= hm[0] + Math.random() * (hm[1] - hm[0]); r.hp = r.maxHp;   // Handy Helpers: 3-5x health r.fuse = 0; r.capPop = 0; r.tgt = null; r.tgtT = 0; r.wet = 0;
    r.crouch = 0; r.kx = r.kz = 0; if (!VIS[r.type].flying) { r.hop = 0; r.y = r.gy; }
    setState(r, 'alert'); r.flash = 0.25;
    if (IB.Status && IB.Status.clearRobot) IB.Status.clearRobot(r);
    var y = r.y + 0.6;
    if (IB.Boom && IB.Boom.ready) { IB.Boom.zap(r.x, y, r.z, 1.3, PAL.teal); IB.Boom.word('CLANG!', r.x, y + 0.9, r.z, 1.5); }
    if (IB.FX) IB.FX.puff(r.x, y, r.z, 8, PAL.teal, 0.12, 0.4, 3);
    play('clank', r, 0.9);
    return true;
  };
  function rogueEnd(r) { r.rogue = 0; r.rogueEnd = true; AI.kill(r, null); }

  // ---------------- hitscan ----------------
  function rayCapsule(ox, oy, oz, dx, dy, dz, cx, cz, y0, y1, rad) {
    var best = Infinity;
    var px = ox - cx, pz = oz - cz, a = dx * dx + dz * dz;
    if (a > 1e-8) {
      var b = 2 * (px * dx + pz * dz), c = px * px + pz * pz - rad * rad, disc = b * b - 4 * a * c;
      if (disc >= 0) {
        var t = (-b - Math.sqrt(disc)) / (2 * a);
        if (t > 0) { var y = oy + dy * t; if (y >= y0 && y <= y1) best = t; }
      }
    }
    var ts = raySphere(ox, oy, oz, dx, dy, dz, cx, y0, cz, rad); if (ts < best) best = ts;
    ts = raySphere(ox, oy, oz, dx, dy, dz, cx, y1, cz, rad); if (ts < best) best = ts;
    return best;
  }
  function raySphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, rad) {
    var px = ox - cx, py = oy - cy, pz = oz - cz, b = px * dx + py * dy + pz * dz, c = px * px + py * py + pz * pz - rad * rad, disc = b * b - c;
    if (disc < 0) return Infinity;
    var t = -b - Math.sqrt(disc); return t > 0 ? t : Infinity;
  }
  AI.rayCapsule = rayCapsule; AI.raySphere = raySphere;
  var _hit = { robot: null, t: 0, zone: 'body' };
  AI.raycast = function (ox, oy, oz, dx, dy, dz, maxT, skip) {
    var best = maxT, br = null, bz = 'body';
    for (var i = 0; i < AI.robots.length; i++) {
      var r = AI.robots[i]; if (!r.on || r.state === 'pose' || r === skip || (r.rogue > 0 && !AI.hitRogues) || (skip && skip.indexOf && skip.indexOf(r) >= 0)) continue;
      var v = VIS[r.type], bodyY = r.y - r.crouch * 0.12;
      var tb = rayCapsule(ox, oy, oz, dx, dy, dz, r.x, r.z, bodyY + v.y0 + v.radius * 0.5, bodyY + v.y1 - v.radius * 0.5, v.radius);
      var sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
      var tc = raySphere(ox, oy, oz, dx, dy, dz, r.x + sy * v.coreZ, bodyY + v.coreY, r.z + cy * v.coreZ, v.coreR);
      var th = v.headR ? raySphere(ox, oy, oz, dx, dy, dz, r.x + sy * (v.headZ || 0), bodyY + v.headY, r.z + cy * (v.headZ || 0), v.headR) : Infinity;   // head crit spot (soldiers)
      var t = Math.min(tb, tc, th);
      if (t < best) { best = t; br = r; bz = (th < Infinity) ? 'head' : (tc <= tb + 0.12) ? 'core' : 'body'; }
    }
    if (!br) return null;
    _hit.robot = br; _hit.t = best; _hit.zone = bz; return _hit;
  };
  AI.nearest = function (x, z, maxD, filter) {
    var best = maxD * maxD, br = null;
    AI.robots.forEach(function (r) { if (!r.on || r.state === 'pose') return; if (filter && !filter(r)) return; var d = (r.x - x) * (r.x - x) + (r.z - z) * (r.z - z); if (d < best) { best = d; br = r; } });
    return br;
  };

  // ---------------- movement helpers ----------------
  // circle vs AABBs on XZ; boxes lower than ylo (or 0.3 m) are stepped over / flown over. base: a ground robot's
  // floor height (walkable surfaces): boxes are measured from it, and walkable boxes up to a step higher are walked onto
  function collide(r, world, rad, ylo, base, yhi) {
    world.query(r.x - rad, r.z - rad, r.x + rad, r.z + rad, _tmp);
    var lo = Math.max(0.3, ylo || 0) + (base || 0), top = 1.2 + (base || 0);
    for (var i = 0; i < _tmp.length; i++) {
      var b = _tmp[i]; if (b.y1 < lo || (!ylo && b.y0 > top) || (yhi !== undefined && b.y0 > yhi)) continue;   // ground robots pass under raised boxes, flyers under decks
      if (b.walk && !ylo && b.y1 <= (base || 0) + STEP_UP) continue;          // a step, ramp or deck edge: walk onto it
      var cx = Math.max(b.x0, Math.min(r.x, b.x1)), cz = Math.max(b.z0, Math.min(r.z, b.z1));
      var dx = r.x - cx, dz = r.z - cz, d2 = dx * dx + dz * dz;
      if (d2 >= rad * rad) continue;
      if (d2 > 1e-8) { var d = Math.sqrt(d2); r.x += dx / d * (rad - d); r.z += dz / d * (rad - d); }
      else { r.x += (r.x < (b.x0 + b.x1) / 2 ? -1 : 1) * 0.05; }
    }
  }
  function turnTo(r, yaw, rate, dt) {
    var d = wrapAngle(yaw - r.yaw);
    var m = rate * dt; r.yaw += Math.max(-m, Math.min(m, d));
  }
  // world position of a gun muzzle: pivot (body), gun pitch `aim` (up +), slide `out`, muzzle (gun local)
  function muzzleWorld(r, v, out) {
    var ca = Math.cos(r.aim), sa = Math.sin(r.aim), L = v.muzzle[2] + out;
    var lx = v.pivot[0] + v.muzzle[0], ly = v.pivot[1] + v.muzzle[1] * ca + L * sa, lz = v.pivot[2] - v.muzzle[1] * sa + L * ca;
    var sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
    _mz.x = r.x + lx * cy + lz * sy; _mz.y = r.y + ly; _mz.z = r.z - lx * sy + lz * cy;
    return _mz;
  }
  // pitch (up +) from a robot's gun pivot to the player's chest
  function aimPitch(r, v, p) {
    var sy = Math.sin(r.yaw), cy = Math.cos(r.yaw);
    var px = r.x + v.pivot[2] * sy, pz = r.z + v.pivot[2] * cy, py = r.y + v.pivot[1];
    return Math.atan2(p.y + 1.15 - py, Math.max(0.5, Math.hypot(p.x - px, p.z - pz)));
  }
  /* one bolt from the muzzle at the player's chest; lead = fraction of the player's velocity to lead by */
  function fireBolt(r, v, p, speed, dmg, lead, spread) { fireFrom(r, muzzleWorld(r, v, r.gunOut), p, speed, dmg, lead, spread); }
  function fireFrom(r, m, p, speed, dmg, lead, spread) {
    var tx = p.x, ty = p.y + 1.15, tz = p.z;
    var dx = tx - m.x, dy = ty - m.y, dz = tz - m.z, d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
    lead = (lead || 0) + tempo().leadAdd; spread = (spread || 0) * tempo().aimMul;
    if (lead) { var tt = d / speed; tx += (p.vx || 0) * tt * lead; tz += (p.vz || 0) * tt * lead; dx = tx - m.x; dz = tz - m.z; d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1; }
    dx /= d; dy /= d; dz /= d;
    if (spread) { dx += (Math.random() - 0.5) * spread; dy += (Math.random() - 0.5) * spread * 0.6; dz += (Math.random() - 0.5) * spread; }
    // bolts in a robot fight: a rogue's hit other robots only (vs 1, x rogueDmgMul), bolts at a rogue hit rogues (vs 2)
    if (IB.Projectiles && IB.Projectiles.fire) IB.Projectiles.fire(m.x, m.y, m.z, dx, dy, dz, speed, r.rogue > 0 ? dmg * AI.rogueDmgMul : dmg, r, r.rogue > 0 ? 1 : p.robot ? 2 : 0);
    if (IB.FX) { IB.FX.puff(m.x, m.y, m.z, 2, PAL.amber, 0.1, 0.22, 1.2); IB.FX.puff(m.x, m.y, m.z, 1, PAL.ink, 0.1, 0.3, 0.8); }
    if (IB.Boom) IB.Boom.muzzle(m.x, m.y, m.z, r.type === 'drone' ? 0.32 : 0.42);
    play('bolt', r, 0.8);
    r.kick = 1;
  }

  // ---------------- behaviours (engaged states) ----------------
  var _mv = { x: 0, z: 0, s: 0 };
  function move(x, z, s) { var l = Math.hypot(x, z); if (l > 1e-6) { _mv.x = x / l; _mv.z = z / l; _mv.s = s; } }
  // the target stands on another level (up on a deck while the robot is on the ground, or the other way round): only
  // in zones with walkable surfaces (layered nav); there the robot paths up the stairs instead of running at it
  function offLevel(r, P, zone) { return !!(zone && zone.nav.layers) && !VIS[r.type].flying && Math.abs(P.y - r.fy) > 0.9; }
  /* chase the player: straight at him while he is in sight, else (or while blocked: r.bump builds up when the robot
     moves much slower than it wants, e.g. against a crate it can see over) along the zone's flow field around it */
  function towardPlayer(r, ctx, zone, dx, dz, dist, s) {
    if (holdRing(r, ctx, dx, dz, dist, s)) return;
    if (r.bump > 0.35 && !ctx.player.robot) { r.navT = 1.6; r.bump = 0; }
    var nav = !ctx.player.robot && zone && r.zone === ctx.activeZone;
    if (!nav || (r.seesPlayer && !(r.navT > 0) && !offLevel(r, ctx.player, zone)) || !IB.Zones.flowDir(zone, r.x, r.z, _dir, VIS[r.type].flying ? 0 : r.fy)) move(dx, dz, s);
    else move(_dir.x, _dir.z, s);
  }
  /* overwhelm control: a melee robot without a close-range slot (r.close, given out nearest-first in AI.update)
     circles at the ring (6-8.5 m) instead of piling in; true when it did */
  var HOLD0 = { ringIn: 6, ringOut: 8.5 };
  function HOLD() { return (IB.Damage && IB.Damage.HOLD) || HOLD0; }
  function holdRing(r, ctx, dx, dz, dist, s) {
    var H = HOLD();
    if (r.close || ctx.player.robot || dist > H.ringOut) return false;
    var rad = dist < H.ringIn ? -1 : dist > H.ringIn + 1.5 ? 0.35 : 0;
    if (r.bump > 0.3) { r.sdir = -r.sdir; r.bump = 0; }
    move(-dz / dist * r.sdir * 0.8 + dx / dist * rad, dx / dist * r.sdir * 0.8 + dz / dist * rad, s * 0.6);
    r.held = true;
    return true;
  }

  // Crawler: chase with a zigzag, 0.35 s crouch windup, lunge bite
  function thinkCrawler(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, v = VIS.crawler, speed = def.speed || 5;
    switch (r.state) {
      case 'chase': {
        if (!p.alive) break;
        var lv = offLevel(r, p, zone);
        if (holdRing(r, ctx, dx, dz, dist, speed)) break;
        if (r.seesPlayer && dist < 14 && !lv && !(r.navT > 0) && r.bump < 0.35) {
          var mvx = dx / dist, mvz = dz / dist;
          var zz = Math.sin(r.zig + r.st * 5.5) * Math.min(1, (dist - 2) / 5) * 0.75;
          move(mvx - mvz * zz, mvz + mvx * zz, speed);
        } else towardPlayer(r, ctx, zone, dx, dz, dist, speed);
        if (dist < (def.reach || 2.3) && r.seesPlayer && !lv && takeToken(r)) { setState(r, 'windup'); r.lx = dx / dist; r.lz = dz / dist; }
        break;
      }
      case 'windup': {
        var wu = (def.windup || 0.35) * tempo().tellMul;
        turnTo(r, Math.atan2(dx, dz), 10, dt);
        r.crouch = Math.min(1, r.st / wu);
        tell(r, r.st / wu);
        r.lx = dx / dist; r.lz = dz / dist;
        if (r.st >= wu) { setState(r, 'attack'); r.bit = false; r.crouch = 0; }
        break;
      }
      case 'attack': {
        _mv.x = r.lx; _mv.z = r.lz; _mv.s = 9.5;
        r.hop = Math.sin(Math.min(1, r.st / 0.24) * Math.PI) * 0.35; r.y = r.gy + r.hop;
        if (!r.bit && dist < v.radius + 0.35 + 0.45 && Math.abs(p.y - r.y) < 1.2) {
          r.bit = true; ctx.hurt(r, (def.damage || 8) * r.dmgMul);
        }
        if (r.st >= 0.24) { r.hop = 0; r.y = r.gy; setState(r, 'recover'); }
        break;
      }
      case 'recover':
        if (r.token) releaseToken(r);
        r.crouch = Math.max(0, r.crouch - dt * 3);
        if (r.st >= 0.6) setState(r, 'chase');
        break;
    }
  }

  // Bomber: rush (faster when close), light the fuse in reach (needs a token), keep rolling at the player, blow up.
  function thinkBomber(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, speed = def.speed || 4.2, reach = (def.range || 2) + 0.6;
    switch (r.state) {
      case 'chase': {
        if (!p.alive) break;
        var rush = r.seesPlayer && dist < 7 ? 1.35 : 1, blv = offLevel(r, p, zone);
        if (r.fuse <= 0 && holdRing(r, ctx, dx, dz, dist, speed)) break;
        if (r.seesPlayer && dist < 16 && !blv && !(r.navT > 0) && r.bump < 0.35) {
          var w = Math.sin(r.zig + r.st * 3.1) * 0.25 * Math.min(1, (dist - 2) / 6);
          move(dx / dist - dz / dist * w, dz / dist + dx / dist * w, speed * rush);
        } else towardPlayer(r, ctx, zone, dx, dz, dist, speed);
        if (r.fuse > 0) move(dx, dz, speed * 0.55);   // fuse already lit (e.g. after a stagger): keep coming
        else if (dist < reach && r.seesPlayer && !blv) {
          if (takeToken(r)) { setState(r, 'windup'); r.fuse0 = r.fuse = def.fuse || def.windup || 0.6; play('fuse', r); }
          else move(-dz * r.sdir + dx * (dist - 2.6), dx * r.sdir + dz * (dist - 2.6), speed * 0.5);   // circle until a token frees up
        }
        break;
      }
      case 'windup':   // fuse lit: the tick below counts it down and detonates
        tell(r, 1 - r.fuse / r.fuse0);
        if (p.alive) move(dx, dz, speed * 0.55);
        break;
    }
  }
  function tickBomber(r, dt, ctx) {
    r.capPop += ((r.fuse > 0 ? 1 : 0) - r.capPop) * Math.min(1, dt * 18);
    if (r.fuse > 0) {
      r.fuse -= dt; r.fizzT -= dt;
      if (r.fizzT <= 0 && IB.FX) {
        r.fizzT = 0.05;
        var sy = Math.sin(r.yaw), cy = Math.cos(r.yaw), v = VIS.bomber, wy = r.y + v.cap[1] + v.wick[1] + 0.07;
        IB.FX.puff(r.x + v.wick[0] * cy, wy, r.z - v.wick[0] * sy, 1, Math.random() < 0.5 ? PAL.amber : PAL.paper, 0.05, 0.12, 2.5, -4);
      }
      if (r.fuse <= 0) AI.kill(r, null);   // self-detonation: blast, no gems
    } else if (r.state === 'chase' && IB.FX) {
      r.fizzT -= dt;   // fizz: a bubble now and then from under the cap
      if (r.fizzT <= 0) { r.fizzT = 0.35 + Math.random() * 0.4; IB.FX.puff(r.x, r.y + 0.95, r.z, 1, PAL.paper, 0.04, 0.1, 0.6, -1.5); }
    }
  }

  // Gunner / Drone: keep 8 to 16 m (Gunner prefers cover), windup, volley / strafing burst, recover.
  function findCover(r, ctx, zone, lo, hi) {
    var p = ctx.player, v = VIS[r.type], best = null, bs = Infinity;
    ctx.world.query(r.x - 8, r.z - 8, r.x + 8, r.z + 8, _tmp);
    for (var i = 0; i < _tmp.length; i++) {
      var b = _tmp[i]; if (b.kind !== 'cover' || b.y1 < 0.9) continue;
      var cx = (b.x0 + b.x1) / 2, cz = (b.z0 + b.z1) / 2, hx = (b.x1 - b.x0) / 2, hz = (b.z1 - b.z0) / 2;
      var ux = cx - p.x, uz = cz - p.z, ul = Math.hypot(ux, uz) || 1; ux /= ul; uz /= ul;
      var t = Math.min(Math.abs(ux) > 1e-3 ? hx / Math.abs(ux) : 1e9, Math.abs(uz) > 1e-3 ? hz / Math.abs(uz) : 1e9);
      var sx = cx + ux * (t + v.radius + 0.3), sz = cz + uz * (t + v.radius + 0.3);
      var dp = Math.hypot(sx - p.x, sz - p.z); if (dp < lo - 1 || dp > hi + 2) continue;
      if (zone && !IB.Zones.isOpen(zone, sx, sz)) continue;
      var dr = Math.hypot(sx - r.x, sz - r.z); if (dr > 10) continue;
      var taken = false;   // one Gunner per cover spot
      for (var j = 0; j < AI.robots.length && !taken; j++) { var o = AI.robots[j]; if (o !== r && o.on && o.type === r.type && (o.mode === 'cover' || o.mode === 'hold') && Math.abs(o.gx - sx) + Math.abs(o.gz - sz) < 1.5) taken = true; }
      if (taken) continue;
      var sc = dr + Math.abs(dp - (lo + hi) / 2) * 0.5 + (b.y1 >= 1.8 ? 0 : 1.5);
      if (sc < bs) { bs = sc; best = b; r.gx = sx; r.gz = sz; }
    }
    return best;
  }
  function planKeep(r, ctx, zone, dist) {
    var def = r.def, kd = def.keepDistance || [8, 16], lo = kd[0], hi = kd[1];
    r.thinkT = 0.5 + Math.random() * 0.6;
    if (dist > hi || (!r.seesPlayer && r.lost > 1.2 && r.mode !== 'hold' && r.mode !== 'cover')) { r.mode = 'approach'; return; }
    if (dist < lo) { r.mode = 'retreat'; return; }
    if (def.usesCover) {
      if (r.mode === 'hold') {
        if (!r.seesPlayer && Math.random() < 0.45) { r.mode = 'strafe'; r.thinkT = 0.7 + Math.random() * 0.5; }   // peek out
        return;
      }
      if (r.mode !== 'cover' && findCover(r, ctx, zone, lo, hi)) { r.mode = 'cover'; r.thinkT = 3; return; }
      if (r.mode === 'cover') return;
    }
    r.mode = 'strafe';
    if (Math.random() < 0.35) r.sdir = -r.sdir;
  }
  function keepMove(r, ctx, zone, dx, dz, dist, speed) {
    switch (r.mode) {
      case 'approach': towardPlayer(r, ctx, zone, dx, dz, dist, speed); break;
      case 'retreat': move(-dx / dist - dz / dist * r.sdir * 0.5, -dz / dist + dx / dist * r.sdir * 0.5, speed); break;
      case 'cover': {
        var gx = r.gx - r.x, gz = r.gz - r.z, gl = Math.hypot(gx, gz);
        if (gl < 0.35) { r.mode = 'hold'; r.thinkT = 1.2 + Math.random(); } else move(gx, gz, speed);
        break;
      }
      case 'strafe': move(-dz * r.sdir, dx * r.sdir, speed * 0.75); break;
    }
  }
  function canFire(r, ctx, dist) {
    var def = r.def;
    return r.cool <= 0 && r.seesPlayer && ctx.player.alive && dist <= (def.range || 20) && dist >= 3 && takeToken(r);
  }

  function thinkGunner(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, v = VIS.gunner, speed = def.speed || 3, wu = (def.windup || 0.5) * tempo().tellMul;
    var up = r.state === 'windup' || r.state === 'attack';
    r.lid += ((up ? 0.55 : 0) - r.lid) * Math.min(1, dt * (up ? 14 : 6));
    r.gunOut += ((up ? 0.07 : 0) - r.gunOut) * Math.min(1, dt * 10);
    switch (r.state) {
      case 'keep':
        r.aim += (-0.45 - r.aim) * Math.min(1, dt * 4);
        if (!p.alive) break;
        r.thinkT -= dt;
        if (r.thinkT <= 0 || (r.mode === 'strafe' && r.bump > 0.25)) { if (r.bump > 0.25) { r.sdir = -r.sdir; r.bump = 0; } planKeep(r, ctx, zone, dist); }
        keepMove(r, ctx, zone, dx, dz, dist, speed);
        if (canFire(r, ctx, dist)) { setState(r, 'windup'); play('servo', r, 0.5); }
        break;
      case 'windup':
        turnTo(r, Math.atan2(dx, dz), 6, dt);
        r.aimTo = aimPitch(r, v, p);
        r.aim += (r.aimTo - r.aim) * Math.min(1, dt * 9);
        tell(r, r.st / wu);
        if (r.st >= wu) { setState(r, 'attack'); r.shots = 0; r.shotT = 0; }
        break;
      case 'attack':
        turnTo(r, Math.atan2(dx, dz), 3, dt);
        r.aim += (aimPitch(r, v, p) - r.aim) * Math.min(1, dt * 6);
        r.shotT -= dt;
        if (r.shots < (def.bolts || 3) && r.shotT <= 0) {
          fireBolt(r, v, p, def.boltSpeed || 22, (def.damage || 6) * r.dmgMul, 0.45, r.shots ? 0.035 : 0);
          r.shots++; r.shotT = 0.14;
        }
        if (r.shots >= (def.bolts || 3) && r.shotT <= -0.1) setState(r, 'recover');
        break;
      case 'recover':
        if (r.token) releaseToken(r);
        r.aim += (-0.45 - r.aim) * Math.min(1, dt * 3);
        if (r.st >= (def.recover || 0.8)) { setState(r, 'keep'); r.cool = (1.0 + Math.random() * 1.4) * tempo().coolMul; r.thinkT = 0; }
        break;
    }
  }

  function thinkDrone(r, dt, ctx, zone, dx, dz, dist) {
    var p = ctx.player, def = r.def, v = VIS.drone, speed = def.speed || 4.5, wu = (def.windup || 0.45) * tempo().tellMul;
    var up = r.state === 'windup' || r.state === 'attack';
    r.lid += ((up ? 1 : 0) - r.lid) * Math.min(1, dt * (up ? 12 : 5));
    var kd = def.keepDistance || [8, 16], mid = (kd[0] + kd[1]) / 2;
    // orbit: tangential strafe + radial correction toward the middle of the band
    var rad = clamp((dist - mid) / 4, -1, 1), tx = -dz / dist * r.sdir, tz = dx / dist * r.sdir;
    var ox = tx * 0.85 + dx / dist * rad, oz = tz * 0.85 + dz / dist * rad;
    r.thinkT -= dt;
    if (r.thinkT <= 0 || r.bump > 0.25) { r.thinkT = 1.8 + Math.random() * 2.2; if (r.bump > 0.25 || Math.random() < 0.6) r.sdir = -r.sdir; r.bump = 0; }
    if (p.alive) turnTo(r, Math.atan2(dx, dz), 5, dt);
    switch (r.state) {
      case 'keep':
        r.aim += (-0.25 - r.aim) * Math.min(1, dt * 4);
        if (!p.alive) break;
        if (!r.seesPlayer && r.lost > 1.5) towardPlayer(r, ctx, zone, dx, dz, dist, speed);
        else move(ox, oz, speed);
        if (canFire(r, ctx, dist)) { setState(r, 'windup'); play('rotor', r, 0.7); }
        break;
      case 'windup':
        move(ox, oz, speed * 0.5);
        r.aim += (aimPitch(r, v, p) - r.aim) * Math.min(1, dt * 9);
        tell(r, r.st / wu);
        if (r.st >= wu) { setState(r, 'attack'); r.shots = 0; r.shotT = 0; }
        break;
      case 'attack':
        move(ox, oz, speed);
        r.aim += (aimPitch(r, v, p) - r.aim) * Math.min(1, dt * 10);
        r.shotT -= dt;
        if (r.shots < (def.bolts || 4) && r.shotT <= 0) {
          fireBolt(r, v, p, def.boltSpeed || 22, (def.damage || 5) * r.dmgMul, 0, 0.05);
          r.shots++; r.shotT = 0.1;
        }
        if (r.shots >= (def.bolts || 4) && r.shotT <= -0.05) setState(r, 'recover');
        break;
      case 'recover':
        if (r.token) releaseToken(r);
        move(ox, oz, speed * 0.8);
        r.aim += (-0.25 - r.aim) * Math.min(1, dt * 3);
        if (r.st >= (def.recover || 0.8)) { setState(r, 'keep'); r.cool = (1.3 + Math.random() * 1.6) * tempo().coolMul; }
        break;
    }
  }

  var BEH = {
    crawler: { think: thinkCrawler },
    gunner: { think: thinkGunner },
    bomber: { think: thinkBomber, tick: tickBomber },
    drone: { think: thinkDrone }
  };
  AI.BEH = BEH;
  // helpers shared with the robot types in other files (game/troops.js)
  AI.K = { move: move, mv: _mv, setState: setState, takeToken: takeToken, releaseToken: releaseToken, tell: tell, play: play, turnTo: turnTo,
    towardPlayer: towardPlayer, holdRing: holdRing, offLevel: offLevel, planKeep: planKeep, keepMove: keepMove, canFire: canFire, fireFrom: fireFrom,
    muzzleWorld: muzzleWorld, aimPitch: aimPitch,
    wrapAngle: wrapAngle, clamp: clamp, sock: sock, tempo: tempo, lightDefault: lightDefault, ZERO: ZERO };

  // ---------------- targets: the player, or a robot in a rogue fight ----------------
  /* A robot fighting a robot sees it through a stand-in "player": the behaviours aim at its chest, bite it and shoot it
     exactly as they would the player, and hurt() lands on the robot. */
  var _tp = { x: 0, y: 0, z: 0, vx: 0, vz: 0, alive: true, robot: null };
  var _rctx = { player: _tp, world: null, level: null, activeZone: -1, shake: null, onKill: null, hurt: hurtTarget };
  var _rogues = [];
  function hurtTarget(src, dmg) {
    var t = _tp.robot; if (!t || !t.on) return;
    var dx = t.x - src.x, dz = t.z - src.z, d = Math.hypot(dx, dz) || 1;
    AI.damage(t, src.rogue > 0 ? dmg * AI.rogueDmgMul : dmg, { kx: dx / d * 3, kz: dz / d * 3 }, src.rogue > 0 ? _rctx.onKill : null);
    play('bite', t, 0.7);
  }
  function fillTarget(t) {
    var v = VIS[t.type];
    _tp.x = t.x; _tp.z = t.z; _tp.y = t.y + (v.y0 + v.y1) * 0.5 - 1.15; _tp.vx = t.vx; _tp.vz = t.vz; _tp.alive = t.on; _tp.robot = t;
  }
  function fightable(o) { return o && o.on && o.state !== 'pose' && o.state !== 'spawn'; }
  /* robot-vs-robot targets must be worth chasing: the same zone (never through a shut gate), not the one it just gave
     up on, and in sight (eye to chest) -- so nobody runs into a wall trying to reach a robot on the other side */
  function canFight(r, o, world) {
    if (o.zone !== r.zone || o === r.ign) return false;
    if (!world) return true;
    var vo = VIS[o.type];
    return world.los(r.x, r.y + VIS[r.type].eye, r.z, o.x, o.y + (vo.y0 + vo.y1) * 0.5, o.z);
  }
  // a rogue picks the nearest robot that is not rogue (30 m) it can see
  function enemyFor(r, world) {
    var best = 900, br = null;
    for (var i = 0; i < AI.robots.length; i++) {
      var o = AI.robots[i]; if (o === r || !fightable(o) || o.rogue > 0) continue;
      var d = (o.x - r.x) * (o.x - r.x) + (o.z - r.z) * (o.z - r.z); if (d < best && canFight(r, o, world)) { best = d; br = o; }
    }
    return br;
  }
  // the others go for a rogue when it is nearer than the player (or the player is gone / cloaked), up to 25 m, in sight
  function rogueFor(r, distP, p, world) {
    var lim = AI.cloaked || !p.alive ? 25 : Math.min(25, distP), best = lim * lim, br = null;
    for (var i = 0; i < _rogues.length; i++) {
      var o = _rogues[i]; if (!o.on || !(o.rogue > 0)) continue;
      var d = (o.x - r.x) * (o.x - r.x) + (o.z - r.z) * (o.z - r.z); if (d < best && canFight(r, o, world)) { best = d; br = o; }
    }
    return br;
  }
  /* the player moved on to zone `zi`: helpers (rogues) left behind in an earlier zone would only draw fire through the
     wall, so they quietly power down (no blast, no corpse); the ones that came along now belong to the new zone */
  AI.dropRogues = function (zone, zi) {
    var n = 0;
    for (var i = 0; i < AI.robots.length; i++) {
      var r = AI.robots[i]; if (!r.on || !(r.rogue > 0)) continue;
      var inside = zone && r.x > zone.ox + 0.3 && r.x < zone.ox + zone.w - 0.3 && r.z > zone.oz + 0.3 && r.z < zone.oz + zone.h - 0.3;
      if (inside) { r.zone = zi; continue; }
      releaseToken(r); r.on = false; r.state = 'off'; r.fuse = 0; r.rogue = 0; r.rogueEnd = false; r.tgt = null; n++;
      if (IB.Status && IB.Status.clearRobot) IB.Status.clearRobot(r);
    }
    for (i = 0; i < AI.robots.length; i++) { var o = AI.robots[i]; if (o.tgt && !o.tgt.on) o.tgt = null; }
    return n;
  };
  /* Undercover: the player is invisible, so wander and search around where he was last seen; a rogue with nothing
     left to fight keeps close to the player */
  function searchMove(r, dt, mode, dx, dz, dist, speed) {
    if (mode === 'follow') {
      if (dist > 4) { move(dx, dz, speed * 0.9); return; }
      r.wanderT -= dt;
      if (r.wanderT <= 0) { r.wanderT = 1.5 + Math.random() * 1.5; var b = Math.random() * TAU; r.wx = r.x + dx + Math.cos(b) * 2.5; r.wz = r.z + dz + Math.sin(b) * 2.5; }
    } else {
      r.wanderT -= dt;
      if (r.wanderT <= 0) { r.wanderT = 1.4 + Math.random() * 1.8; var a = Math.random() * TAU, rad = 1.5 + Math.random() * 5; r.wx = AI.lkx + Math.cos(a) * rad; r.wz = AI.lkz + Math.sin(a) * rad; }
    }
    var wx = r.wx - r.x, wz = r.wz - r.z;
    if (Math.hypot(wx, wz) > 0.4) move(wx, wz, speed * (mode === 'follow' ? 0.6 : 0.5));
  }
  /* Undercover on / off; (x, z) is where the robots last saw the player */
  AI.cloak = function (on, x, z) {
    AI.cloaked = !!on;
    if (on) { AI.lkx = x; AI.lkz = z; for (var i = 0; i < AI.robots.length; i++) { var r = AI.robots[i]; if (r.on && !(r.rogue > 0)) { r.wanderT = Math.random() * 0.6; r.seesPlayer = false; } } }
  };

  /* overwhelm control: hand out the close-range slots (core/damage.js closeCap) to the melee robots after the player,
     nearest first; ones already winding up or striking keep theirs. Everyone else is r.close = true (no limit). */
  var MELEE = { crawler: 1, bomber: 1, blader: 1 }, _push = [];
  function byDist(a, b) { return a.pd - b.pd; }
  function closeSlots(p) {
    var n = 0, cap = IB.Damage && IB.Damage.closeCap ? IB.Damage.closeCap(AI.level) : 99, used = 0, i, r;
    for (i = 0; i < AI.robots.length; i++) {
      r = AI.robots[i]; r.close = true;
      if (!r.on || !MELEE[r.type] || r.rogue > 0 || r.tgt || r.state === 'spawn' || r.state === 'pose' || r.state === 'idle' || !p.alive || AI.cloaked) continue;
      if (r.state === 'windup' || r.state === 'attack' || r.fuse > 0) { used++; continue; }
      r.pd = (r.x - p.x) * (r.x - p.x) + (r.z - p.z) * (r.z - p.z); _push[n++] = r;
    }
    _push.length = n;
    if (n + used <= cap) return;
    _push.sort(byDist);
    for (i = 0; i < n; i++) _push[i].close = i < cap - used;
  }
  // robots (not rogues) within rad m of (p.x, p.z): the spawn pacing in game.js waits while too many crowd the player
  AI.crowd = function (p, rad) {
    var n = 0, r2 = rad * rad;
    for (var i = 0; i < AI.robots.length; i++) { var r = AI.robots[i]; if (r.on && r.state !== 'pose' && !(r.rogue > 0) && (r.x - p.x) * (r.x - p.x) + (r.z - p.z) * (r.z - p.z) < r2) n++; }
    return n;
  };

  /* flyers: the lowest thing overhead at (x, z): the zone's ceiling plane, or the underside of a box above the floor
     it hovers over (a deck, a beam with collision); zone bounds rings are ignored (they only stop walking) */
  function flyCeil(r, world, level) {
    var Z = level && level.zones[r.zone], C = level && level.theme && level.theme.env && level.theme.env.ceiling;
    var c = C && C.height && !(Z && Z.plan && Z.plan.ceiling === false) ? C.height : Infinity;
    var rad = VIS[r.type].radius + 0.15, lo = r.fy + 1.0;
    world.query(r.x - rad, r.z - rad, r.x + rad, r.z + rad, _tmp);
    for (var i = 0; i < _tmp.length; i++) {
      var b = _tmp[i]; if (b.kind === 'bound' || b.y0 < lo || b.y0 >= c) continue;
      if (r.x + rad < b.x0 || r.x - rad > b.x1 || r.z + rad < b.z0 || r.z - rad > b.z1) continue;
      c = b.y0;
    }
    return c;
  }
  // the height a flyer hovers at here: its hover over the floor, kept under the ceiling (top of the body 0.2 m clear)
  function flyY(r) {
    var v = VIS[r.type], y = r.fy + r.hy, top = r.ceil - v.y1 - 0.2;
    if (y > top) y = Math.max(r.fy + 0.5, top);
    return y;
  }
  AI.flyCeil = flyCeil; AI.flyY = flyY;

  /* ctx: {player, world, level, activeZone, hurt(robot, dmg), shake(trauma), onKill(robot)} */
  AI.update = function (dt, ctx) {
    var p = ctx.player, world = ctx.world, i, r;
    var nR = 0;
    for (i = 0; i < AI.robots.length; i++) { r = AI.robots[i]; if (r.on && r.rogue > 0) _rogues[nR++] = r; }
    _rogues.length = nR;
    _rctx.world = world; _rctx.level = ctx.level; _rctx.activeZone = ctx.activeZone; _rctx.shake = ctx.shake; _rctx.onKill = ctx.onKill;
    var zone = ctx.level && ctx.activeZone >= 0 ? ctx.level.zones[ctx.activeZone] : null;
    if (zone) {
      zone.nav.t -= dt;
      if (zone.nav.t <= 0) { zone.nav.t = 0.25; IB.Zones.flowField(zone, p.x, p.z, p.y); }
    }
    closeSlots(p);
    AI.levelRef = ctx.level;
    updateCans(dt);
    for (i = 0; i < AI.robots.length; i++) {
      r = AI.robots[i]; if (!r.on) continue;
      var def = r.def, v = VIS[r.type], B = BEH[r.type];
      r.held = false; if (r.navT > 0) r.navT -= dt;
      if (r.squash > 0 && r.state !== 'spawn') r.squash = Math.max(0, r.squash - dt * 4.5);   // landing squash springs back
      var speed = def.speed || 5.0, fly = !!v.flying;
      r.st += dt; r.flash = Math.max(0, r.flash - dt); r.idleT += dt; r.cool -= dt;
      r.kick = Math.max(0, r.kick - dt * 6);
      // target: the player; a robot (rogue fights); or nobody (player cloaked -> search, rogue with no enemy -> follow)
      var P = p, C = ctx, mode = null, tgt = null;
      var dxp = p.x - r.x, dzp = p.z - r.z, distP = Math.sqrt(dxp * dxp + dzp * dzp) || 0.001;
      if (r.rogue > 0) {
        r.rogue -= dt;
        if (r.rogue <= 0) { rogueEnd(r); continue; }
        r.tgtT -= dt; r.ignT -= dt; if (r.ignT <= 0) r.ign = null;
        if (r.tgt && r.lost > 2 && r.tgtT <= 0) { r.ign = r.tgt; r.ignT = 4; r.tgt = null; }   // lost sight of it: give up
        if (r.tgtT <= 0 || !fightable(r.tgt) || r.tgt.rogue > 0) { r.tgtT = 0.3; r.tgt = enemyFor(r, world); }
        tgt = r.tgt; if (!tgt) mode = 'follow';
      } else if (r.state !== 'pose') {
        r.rtT -= dt; r.ignT -= dt; if (r.ignT <= 0) r.ign = null;
        tgt = r.tgt && r.tgt.on && r.tgt.rogue > 0 && r.tgt.zone === r.zone ? r.tgt : null;
        // chasing a rogue it cannot see any more (behind a wall, round a corner): give up on it for a while
        if (tgt && r.lost > 1.5) { r.ign = tgt; r.ignT = 4; tgt = null; r.rtT = 0; }
        if (!nR || r.state === 'spawn') tgt = null;
        else if (r.rtT <= 0) { r.rtT = 0.3; tgt = rogueFor(r, distP, p, world); }
        if (tgt !== r.tgt) r.lost = 0;
        r.tgt = tgt;
        if (!tgt && AI.cloaked) mode = 'search';
      }
      if (tgt) { fillTarget(tgt); P = _tp; C = _rctx; }
      _freeToken = !!tgt;
      var dx = P.x - r.x, dz = P.z - r.z, dist = Math.sqrt(dx * dx + dz * dz) || 0.001;
      _mv.x = _mv.z = _mv.s = 0;
      // periodic sight check (staggered)
      r.losT -= dt;
      // nobody to fight: drop any attack in progress (a Bomber's fuse goes out too)
      if (mode) { r.seesPlayer = false; if (r.state === 'windup' || r.state === 'attack' || r.state === 'recover') { r.fuse = 0; if (!fly) { r.hop = 0; r.y = r.gy; } r.crouch = 0; setState(r, v.home); } }
      else if (r.losT <= 0 && r.state !== 'pose') {
        r.losT = 0.2;
        r.seesPlayer = P.alive && dist < 25 && world.los(r.x, r.y + v.eye, r.z, P.x, P.y + 1.4, P.z);
      }
      r.lost = r.seesPlayer ? 0 : r.lost + dt;
      switch (r.state) {
        case 'pose':
          r.walk += dt * 0.6; r.crouch = r.type === 'crawler' ? 0.15 + Math.sin(r.idleT * 2.2 + r.slot) * 0.12 : 0;
          if (fly) r.y = r.hy + Math.sin(r.idleT * 1.7 + r.slot) * 0.08;
          break;
        case 'spawn': {
          spawnPose(r, dt, fly, world);
          if (r.st >= SPAWN_T) {
            r.x = r.tx; r.z = r.tz;
            r.fy = r.gy = world.floorAt(r.x, r.z, (r.sy || 0) + STEP_UP); r.fvy = 0; r.hop = 0;   // the floor beside the spawn can (ground or deck)
            if (fly) { r.ceil = flyCeil(r, world, ctx.level); r.y = flyY(r); r.squash = 0; }
            else {
              r.y = r.gy; r.squash = 1; r.crouch = 0;   // lands: squash (springs back in ~0.2 s), dust
              if (IB.FX) { IB.FX.puff(r.x, r.gy + 0.1, r.z, 6, PAL.ink, 0.15, 0.45, 2.4); }
              play('land', r, 0.5);
            }
            setState(r, zone && r.zone === ctx.activeZone ? 'alert' : 'idle');
          }
          break;
        }
        case 'idle': {
          // wander between nearby points at 40% speed
          r.wanderT -= dt;
          if (r.wanderT <= 0) { r.wanderT = 2 + Math.random() * 2; var a = Math.random() * TAU; r.wx = r.x + Math.cos(a) * 3; r.wz = r.z + Math.sin(a) * 3; }
          var wx = r.wx - r.x, wz = r.wz - r.z, wl = Math.hypot(wx, wz);
          if (wl > 0.3) move(wx, wz, speed * 0.4);
          var fy = wrapAngle(Math.atan2(dx, dz) - r.yaw);
          if (r.seesPlayer && Math.abs(fy) < Math.PI / 3) setState(r, 'alert');
          break;
        }
        case 'alert':
          if (!mode) turnTo(r, Math.atan2(dx, dz), 8, dt);
          r.alert = 0.4;
          if (r.st >= 0.4) { setState(r, v.home); r.thinkT = 0; }
          break;
        case 'stagger':
          r.x += r.kx * dt; r.z += r.kz * dt; r.kx *= Math.max(0, 1 - 6 * dt); r.kz *= Math.max(0, 1 - 6 * dt);
          if (r.type === 'crawler' || fly) r.yaw += dt * 3;
          r.wob = Math.sin(r.st * 28) * 0.16 * (1 - r.st / 0.6);
          if (fly) r.y -= dt * 0.8 * (1 - r.st / 0.6);
          if (r.st >= 0.6) { r.wob = 0; setState(r, v.home); r.thinkT = 0; }
          break;
        case 'blinded':
          r.yaw += dt * 1.5;
          if (fly) r.y += ((flyY(r) - 0.5) - r.y) * Math.min(1, dt * 2);
          if (r.st >= r.blind) { setState(r, v.home); r.thinkT = 0; }
          break;
        default:
          if (mode) searchMove(r, dt, mode, dx, dz, dist, speed);
          else B.think(r, dt, C, zone, dx, dz, dist);
      }
      _freeToken = false;
      if (r.state === 'spawn' || r.state === 'pose') continue;
      if (B.tick) { B.tick(r, dt, C); if (!r.on) continue; }
      // movement: smooth velocity toward the wish, collide, face
      if (r.slowT > 0) r.slowT -= dt;   // Torpedo: a slowed robot moves a bit slower for a moment
      var sm = (r.state === 'attack' ? 1 : tempo().speedMul) * (r.slowT > 0 ? 1 - (r.slowMul || 0) : 1);
      var tvx = _mv.x * _mv.s * sm, tvz = _mv.z * _mv.s * sm, blend = Math.min(1, dt * (r.state === 'attack' && r.type === 'crawler' ? 30 : fly ? 4 : 10));
      r.vx += (tvx - r.vx) * blend; r.vz += (tvz - r.vz) * blend;
      var ox = r.x, oz = r.z;
      r.x += r.vx * dt; r.z += r.vz * dt;
      collide(r, world, v.radius * 0.9, fly ? r.y - 0.1 : 0, fly ? 0 : Math.max(r.fy, r.gy), fly ? r.y + v.y1 + 0.1 : undefined);
      if (!fly) {
        // walkable surfaces: the floor under the robot; glide up onto a step, fall off an edge (r.y = r.gy without them)
        r.fy = world.floorAt(r.x, r.z, Math.max(r.fy, r.gy) + STEP_UP);
        if (r.gy < r.fy) { r.gy += (r.fy - r.gy) * Math.min(1, dt * 14); if (r.fy - r.gy < 0.004) r.gy = r.fy; r.fvy = 0; }
        else if (r.gy > r.fy) { r.fvy -= 18 * dt; r.gy = Math.max(r.fy, r.gy + r.fvy * dt); if (r.gy <= r.fy) r.fvy = 0; }
        r.y = r.gy + r.hop;
      } else {
        r.fy = world.floorAt(r.x, r.z, r.y + 0.3);
        r.ceilT -= dt; if (r.ceilT <= 0) { r.ceilT = 0.25; r.ceil = flyCeil(r, world, ctx.level); }
      }
      if (fly && ctx.level) {
        var Z = ctx.level.zones[r.zone];
        if (Z) { r.x = clamp(r.x, Z.ox + 1.2, Z.ox + Z.w - 1.2); r.z = clamp(r.z, Z.oz + 1.2, Z.oz + Z.h - 1.2); }
      }
      // wall bump: moving much slower than wished -> strafe direction flips
      var want = Math.hypot(r.vx, r.vz) * dt, got = Math.hypot(r.x - ox, r.z - oz);
      if (want > 0.004 && got < want * 0.4) r.bump += dt; else r.bump = Math.max(0, r.bump - dt);
      var hs = Math.hypot(r.vx, r.vz);
      r.walk += dt * hs * 1.6;
      var fwd = r.vx * Math.sin(r.yaw) + r.vz * Math.cos(r.yaw);
      if (v.wheelR) r.roll += fwd * dt / v.wheelR;
      if (fly) {
        // hover: altitude bob, bank into the strafe, rotors
        if (r.state !== 'stagger' && r.state !== 'blinded') r.y += ((flyY(r) + (v.bob ? v.bob(r) : Math.sin(r.idleT * 1.7 + r.slot) * 0.1)) - r.y) * Math.min(1, dt * (v.climb || 3));
        // never into the ceiling / a deck overhead, never through the floor (stagger and blind drift included)
        var fmin = v.minFly !== undefined ? v.minFly : 0.15;   // a flyer that can land (Jet Trooper) stands on the floor
        r.y = clamp(r.y, r.fy + fmin, Math.max(r.fy + fmin, r.ceil - v.y1 - 0.1));
        var side = r.vx * Math.cos(r.yaw) - r.vz * Math.sin(r.yaw);
        r.bankX += (clamp(fwd * 0.05, -0.3, 0.3) - r.bankX) * Math.min(1, dt * 5);
        r.bankZ += (clamp(-side * 0.05, -0.3, 0.3) - r.bankZ) * Math.min(1, dt * 5);
        r.spin += dt * (r.lid > 0.5 ? 46 : 30);
      } else if (r.type === 'gunner') {
        r.tilt += ((Math.abs(fwd) > 0.4 && r.state !== 'windup' && r.state !== 'attack' ? 0.17 : 0) - r.tilt) * Math.min(1, dt * 6);
        if (r.state !== 'windup' && r.state !== 'attack' && r.state !== 'stagger' && r.state !== 'blinded') {
          if (hs > 0.3) {
            // roll backward (facing the player) when backing off, else face the way it rolls
            if ((r.vx * dx + r.vz * dz) / (hs * dist) < -0.3) turnTo(r, Math.atan2(-r.vx, -r.vz), 5, dt);
            else turnTo(r, Math.atan2(r.vx, r.vz), 5, dt);
          } else if (P.alive && r.state !== 'idle' && !mode) turnTo(r, Math.atan2(dx, dz), 4, dt);
        }
      } else if (v.face) {
        v.face(r, dt, P, dx, dz, dist, hs, fwd, mode);   // troops.js: Soldiers aim the torso while the legs walk, Blade Bots spin
      } else {
        if (r.type === 'bomber') r.tilt += ((r.state === 'chase' || r.state === 'windup' ? clamp(fwd * 0.03, -0.1, 0.16) : 0) - r.tilt) * Math.min(1, dt * 6);
        if (hs > 0.3 && r.state !== 'stagger' && r.state !== 'blinded') turnTo(r, Math.atan2(r.vx, r.vz), 9, dt);
        if (r.state !== 'windup' && r.state !== 'attack') r.crouch = Math.max(0, r.crouch - dt * 4);
      }
      r.alert = Math.max(0, r.alert - dt);
    }
    // soft separation (60% of overlap); flyers only separate from flyers
    for (i = 0; i < AI.robots.length; i++) {
      var A = AI.robots[i]; if (!A.on || A.state === 'spawn') continue;
      for (var j = i + 1; j < AI.robots.length; j++) {
        var b = AI.robots[j]; if (!b.on || b.state === 'spawn' || Math.abs(A.y - b.y) > 1.2) continue;
        var sx = b.x - A.x, sz = b.z - A.z, rr = VIS[A.type].radius + VIS[b.type].radius, d2 = sx * sx + sz * sz;
        if (d2 < rr * rr && d2 > 1e-6) {
          var d = Math.sqrt(d2), push = (rr - d) * 0.3 / d;
          A.x -= sx * push; A.z -= sz * push; b.x += sx * push; b.z += sz * push;
        }
      }
    }
  };

  // ---------------- render sync ----------------
  // P: a tiny matrix stack for posing parts. root() = the robot's transform; t/rx/ry/rz/s multiply in place; emit() writes an instance.
  var _base = new THREE.Matrix4(), _cur = new THREE.Matrix4(), _stk = [], _sp = 0, _rob = null, _T = null, _tk = 0, _ta = 0;
  for (var si = 0; si < 6; si++) _stk.push(new THREE.Matrix4());
  var P = AI.poser = {
    root: function () { _cur.copy(_base); _sp = 0; return P; },
    t: function (x, y, z) { _cur.multiply(_m2.makeTranslation(x, y, z)); return P; },
    tv: function (a) { _cur.multiply(_m2.makeTranslation(a[0], a[1], a[2])); return P; },
    rx: function (a) { if (a) _cur.multiply(_m2.makeRotationX(a)); return P; },
    ry: function (a) { if (a) _cur.multiply(_m2.makeRotationY(a)); return P; },
    rz: function (a) { if (a) _cur.multiply(_m2.makeRotationZ(a)); return P; },
    s: function (x, y, z) { _cur.multiply(_m2.makeScale(x, y, z)); return P; },
    push: function () { _stk[_sp++].copy(_cur); return P; },
    pop: function () { _cur.copy(_stk[--_sp]); return P; },
    emit: function (name, k) {
      var Pt = _T.parts[name], idx = _rob.slot * Pt.count + k;
      Pt.mesh.setMatrixAt(idx, _cur); Pt.used = true;
      if (Pt.tint && _rob.tint) Pt.tint.setXYZ(idx, _rob.tint.r, _rob.tint.g, _rob.tint.b);
      if (Pt.tint2 && _rob.tint2) Pt.tint2.setXYZ(idx, _rob.tint2.r, _rob.tint2.g, _rob.tint2.b);
      if (Pt.fx) Pt.fx.setXYZW(idx, _rob.flash > 0 ? 1 : 0, 0, _tk, _ta);
      else if (Pt.mesh.instanceColor) Pt.mesh.setColorAt(idx, _c.set(Pt.lc ? Pt.lc(_rob) : _T.vis.lightColor ? _T.vis.lightColor(_rob) : lightDefault(_rob)));
      return P;
    },
    // a part this robot does not show (another shape variant, a grenade not in hand)
    hide: function (name, k) { var Pt = _T.parts[name]; Pt.mesh.setMatrixAt(_rob.slot * Pt.count + (k || 0), ZERO); return P; },
    mul: function (m) { _cur.multiply(m); return P; },
    // the current frame's origin in world space (muzzles, tube mouths), or replace the frame with a world matrix
    pos: function (out) { out.x = _cur.elements[12]; out.y = _cur.elements[13]; out.z = _cur.elements[14]; return P; },
    mat: function (m) { _cur.copy(m); return P; },
    // legacy one-liner: translate, pitch about X, stretch Y
    set: function (name, k, lx, ly, lz, rx, sy) { return P.root().t(lx, ly, lz).rx(rx || 0).s(1, sy, 1).emit(name, k); }
  };
  /* dragged by a singularity (gear.js, r.pull 0..1): the body tips toward the core from its feet, rocks and skips
     off the ground, and stretches a little along the pull */
  var _qa = new THREE.Quaternion(), _ax = new THREE.Vector3();
  function pulled(r) {
    var p = r.pull, t = r.pullT || 0, ph = r.slot * 1.7, dx = (r.pullX || r.x) - r.x, dz = (r.pullZ || r.z) - r.z, d = Math.hypot(dx, dz) || 1;
    _ax.set(dz / d, 0, -dx / d);   // up x (to the core): tipping about it leans the top toward the core
    _qa.setFromAxisAngle(_ax, p * (0.3 + 0.07 * Math.sin(t * 8.5 + ph)));
    _q.premultiply(_qa);
    _ax.set(dx / d, 0, dz / d); _qa.setFromAxisAngle(_ax, p * 0.1 * Math.sin(t * 6.1 + ph)); _q.premultiply(_qa);   // side to side
    _v.y += p * p * (0.06 + 0.1 * Math.abs(Math.sin(t * 7.3 + ph)));
    _s.y *= 1 + 0.07 * p; _s.x *= 1 - 0.035 * p; _s.z *= 1 - 0.035 * p;
  }
  AI.sync = function () {
    for (var ti = 0; ti < AI.typeList.length; ti++) {
      var T = AI.typeList[ti], hi = -1, s, k, pi;
      for (s = CAP - 1; s >= 0; s--) if (T.slots[s].on) { hi = s; break; }
      _T = T;
      for (pi = 0; pi < T.partList.length; pi++) T.partList[pi].used = false;
      for (s = 0; s <= hi; s++) {
        var r = T.slots[s];
        if (!r.on) { for (pi = 0; pi < T.partList.length; pi++) { var Pz = T.partList[pi]; for (k = 0; k < Pz.count; k++) Pz.mesh.setMatrixAt(s * Pz.count + k, ZERO); } continue; }
        _rob = r;
        // tint: rogue teal (blinks in its last 3 s), wet blue while a Hydrate coat lasts
        if (r.rogue > 0) { _tk = 1; _ta = r.rogue < 3 && Math.sin(r.rogue * 16) > 0 ? 0.25 : 0.62; }
        else if (r.wet > 0) { _tk = 2; _ta = Math.min(1, r.wet * 1.5) * 0.85; }
        else { _tk = 0; _ta = 0; }
        var sq = r.squash || 0;   // spawn hop: + squashes (landing), - stretches (pushing up out of the can)
        _q.setFromAxisAngle(_up, r.yaw); _v.set(r.x, r.y, r.z); _s.set(1 + sq * 0.22, 1 - sq * 0.3, 1 + sq * 0.22);
        if (r.pull > 0.01 && !T.vis.flying) pulled(r);
        _base.compose(_v, _q, _s);
        T.vis.pose(r, P);
        if (IB.FX) IB.FX.blob(r.x, r.fy || 0, r.z, T.vis.shadow * (T.vis.flying ? 0.8 : 1 - Math.min(0.5, r.y - (r.fy || 0))));
      }
      for (pi = 0; pi < T.partList.length; pi++) {
        var Pt = T.partList[pi]; Pt.mesh.instanceMatrix.needsUpdate = true;
        Pt.mesh.count = (hi + 1) * Pt.count;   // draw only up to the highest live slot
        Pt.mesh.visible = hi >= 0 && (!Pt.opt || Pt.used);   // and no draw call at all for a type with none alive
        if (Pt.fx) Pt.fx.needsUpdate = true;
        if (Pt.tint) Pt.tint.needsUpdate = true;
        if (Pt.tint2) Pt.tint2.needsUpdate = true;
        if (Pt.mesh.instanceColor) Pt.mesh.instanceColor.needsUpdate = true;
      }
      T.hi = hi;
    }
  };

  // corpses: pop 0.3 m up (0.12 s), tip over (0.5 s), fade + sink (0.6 s); flyers drop to the ground meanwhile
  AI.updateCorpses = function (dt) {
    for (var ti = 0; ti < AI.typeList.length; ti++) {
      var T = AI.typeList[ti], op = T.corpse.geometry.attributes.aOp, hiC = -1;
      for (var i = 0; i < CORPSE_CAP; i++) {
        var c = T.corpses[i];
        if (!c.on) { T.corpse.setMatrixAt(i, ZERO); continue; }
        c.t += dt;
        if (c.y > c.fy) { c.vy -= 16 * dt; c.y = Math.max(c.fy, c.y + c.vy * dt); }   // drop to the floor under it
        var y, tip, alpha = 1;
        if (c.t < 0.12) { y = c.y + Math.sin(c.t / 0.12 * Math.PI / 2) * 0.3; tip = 0; }
        else if (c.t < 0.62) { var k = (c.t - 0.12) / 0.5; y = c.y + 0.3 * (1 - k * k); tip = k * k * (Math.PI / 2); }
        else if (c.t < 1.22) { var f = (c.t - 0.62) / 0.6; y = c.y - f * 0.35; tip = Math.PI / 2; alpha = 1 - f; }
        else { c.on = false; T.corpse.setMatrixAt(i, ZERO); continue; }
        _q.setFromAxisAngle(_up, c.yaw);
        _q2.setFromAxisAngle(_ax, tip * c.tip);
        _q.multiply(_q2);
        _v.set(c.x, y + (tip > 0 ? 0.3 * Math.sin(tip) : 0), c.z); _s.set(1, 1, 1);
        _m.compose(_v, _q, _s); T.corpse.setMatrixAt(i, _m);
        op.setX(i, alpha); hiC = i;
      }
      T.corpse.count = hiC + 1; T.corpse.visible = hiC >= 0;
      T.corpse.instanceMatrix.needsUpdate = true; op.needsUpdate = true;
    }
  };
})(window.IB = window.IB || {});
