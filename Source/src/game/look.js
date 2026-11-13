/* INKBOLT tactical look: switches, shared uniforms, per-level look (plan: Source/docs/tactical-look/PLAN.md).
   The look is a page-load switch: ?look=classic renders the game exactly as before the overhaul (no shader
   overrides, no shadows, no post). Nothing switches it while the page is open, so no material ever changes
   shader family at run time. ?post=0 keeps the look but draws straight to the canvas (the low-tier path).
   ?look=classic&post=1 is the classic picture drawn through the offscreen pipeline (Stage 1 gate).
   ?lookstats=1 prints frame time, draw calls, tier and target sizes to the console every two seconds.
   All look uniforms are shared objects in IB.Look.U: one write updates every look material. */
(function (IB) {
  'use strict';
  var q = (typeof location !== 'undefined' && location.search) || '';
  function param(k) { var m = new RegExp('[?&]' + k + '=([^&]*)').exec(q); return m ? decodeURIComponent(m[1]) : null; }
  var Look = IB.Look = {
    on: param('look') !== 'classic',
    stats: param('lookstats') === '1',
    cur: null,          // the resolved look of the current level
    sunDir: null,       // the theme's sun direction (never read back from the moved shadow light)
    mats: []            // every look material (tier changes recompile them)
  };
  // ?look=classic&post=1: the classic picture through the offscreen pipeline (proves the pipeline is a passthrough)
  Look.shadows = param('shadows') !== '0';   // ?shadows=0: no sun shadow map (isolates Stage 2 from Stage 3)
  Look.post = Look.on ? param('post') !== '0' : param('post') === '1';

  function v3(a) { return new THREE.Vector3(a[0], a[1], a[2]); }
  var U = null;
  Look.uniforms = function () {
    if (U) return U;
    var d = IB.LOOKS.defaults;
    U = Look.U = {
      uSunI: { value: d.sunI }, uAmbSky: { value: v3(d.ambSky) }, uAmbGround: { value: v3(d.ambGround) },
      uAmbI: { value: d.ambI }, uAmbFloor: { value: d.ambFloor }, uIndoorAmb: { value: d.indoorAmb },
      uAlbSat: { value: d.albSat }, uAlbGain: { value: d.albGain }, uAlbCeil: { value: d.albCeil },
      uIndoor: { value: 0 }, uEmBoost: { value: 1.8 }, uShEdge: { value: 0.06 },
      uSunDirW: { value: new THREE.Vector3(0.42, 0.82, 0.38).normalize() }, uSunFog: { value: v3(d.fog.sunGlow) },
      uInkFade: { value: new THREE.Vector2(d.ink.fade[0], d.ink.fade[1]) },
      uGrid: { value: null }, uGridO: { value: new THREE.Vector4(0, 0, 1, 1) }, uGridY: { value: new THREE.Vector4(0.9, 2.6, 1, 0.01) },
      uGridI: { value: 0 }, uGridOn: { value: 0 },
      uDetail: { value: null }, uDetailOn: { value: 0 },
      uGExpo: { value: 1 }, uGSat: { value: 1 }, uGCon: { value: 0 }, uGLo: { value: v3([1, 1, 1]) }, uGHi: { value: v3([1, 1, 1]) },
      uFlashP: { value: [0, 1, 2, 3].map(function () { return new THREE.Vector4(0, -999, 0, 1); }) },
      uFlashC: { value: [0, 1, 2, 3].map(function () { return new THREE.Vector4(0, 0, 0, 0); }) }
    };
    return U;
  };
  if (typeof THREE !== 'undefined') Look.uniforms();

  // program cache key part for a look material (kind + tier: a tier change recompiles)
  Look.key = function (kind) { return 'L' + kind + (IB.Render && IB.Render.tier || 'high') + (IB.Post && IB.Post.on ? 'p' : 'g'); };
  Look.register = function (mat) { Look.mats.push(mat); };
  Look.setTier = function () { Look.mats.forEach(function (m) { m.needsUpdate = true; }); };

  // level start: resolve the look (defaults <- family <- theme), write every uniform
  Look.begin = function (level) {
    if (!Look.on || !level) return;
    var R = IB.Render, theme = level.theme || {}, env = theme.env || {};
    var L = Look.cur = IB.LOOKS.resolve(theme.id, env);
    var s = env.sun || [0.42, 0.82, 0.38];
    Look.sunDir = new THREE.Vector3(s[0], s[1], s[2]).normalize();
    U.uSunDirW.value.copy(Look.sunDir);
    U.uSunI.value = L.sunI; U.uAmbSky.value.fromArray(L.ambSky); U.uAmbGround.value.fromArray(L.ambGround);
    U.uAmbI.value = L.ambI; U.uAmbFloor.value = L.ambFloor; U.uIndoorAmb.value = L.indoorAmb;
    U.uAlbSat.value = L.albSat; U.uAlbGain.value = L.albGain; U.uAlbCeil.value = L.albCeil;
    U.uIndoor.value = env.sky ? 0 : 1;   // Stage 4 replaces this with the light volume's sky visibility
    U.uSunFog.value.fromArray(L.fog.sunGlow);
    U.uInkFade.value.set(L.ink.fade[0], L.ink.fade[1]);
    if (L.sunColor) R.sun.color.set(L.sunColor);
    R.sun.intensity = 1;   // intensity is carried by uSunI
    // fog: near carries the haze length (atmo.js), far stays the theme's wall distance (trap T7)
    R.lookFogLen = L.fog.length;
    if (L.fog.color) R.scene.fog.color.set(L.fog.color);
    if (L.fog.far) R.envFogFar = L.fog.far;
    R.applyFogFar();
    // ink: thin, near-black, fading with distance
    R.worldOutline.px = L.ink.px; R.worldOutline.uOutBase.value = L.ink.base; R.worldOutline.uInk.value.set(L.ink.color);
    R.vmOutline.px = L.ink.vmPx; R.updateOutlineK();
    // the code-built floors / walls / roofs: the theme's floor class
    if (IB.Zones && IB.Zones.mat && IB.Zones.mat.userData.surfFlat) IB.Zones.mat.userData.surfFlat.value.copy(IB.Surface.flat(L.floor.cls, L.floor.gloss));
    // sky and the comic puff clouds (kept for classic only)
    if (IB.Atmo) { IB.Atmo.skyInstall(); IB.Atmo.skyApply(L); }
    (level.cloudMeshes || []).forEach(function (m) { m.visible = false; });
    if (IB.Atmo) IB.Atmo.adoptHaze(level);
    if (IB.Post) IB.Post.applyLook(L);
    U.uGExpo.value = L.exposure; U.uGSat.value = L.grade.sat; U.uGCon.value = L.grade.contrast; U.uGLo.value.fromArray(L.grade.lo); U.uGHi.value.fromArray(L.grade.hi);
    if (IB.Shadows) IB.Shadows.begin(level);
    // the light volume: lamps modelled in the map are its lights; the start zone bakes now (the loader covers it)
    if (IB.LightGrid) { IB.LightGrid.begin(level, L); IB.LightGrid.bakeZoneNow(0); }
  };
  Look.end = function () { Look.cur = null; if (IB.Shadows) IB.Shadows.end(); if (IB.LightGrid) IB.LightGrid.end(); };
  /* Flash lights (Stage 4.5): muzzle flashes and blasts light the world for a moment. 4 slots (fewer on low tiers),
     linear decay, inverse-square falloff with a radius cutoff, no shadows. Halved with Settings > reduce flashes. */
  var flashes = [0, 1, 2, 3].map(function () { return { t: 0, life: 0, i: 0 }; });
  Look.flash = function (x, y, z, color, radius, life, intensity) {
    if (!Look.on || !Look.cur || !U) return;
    var n = IB.LOOKS.tier(IB.Render.tier).flashes, k = 0, G = IB.Game;
    for (var i = 0; i < n; i++) { if (flashes[i].i <= 0) { k = i; break; } if (flashes[i].t / flashes[i].life > flashes[k].t / flashes[k].life) k = i; }
    var f = flashes[k], c = new THREE.Color(color === undefined ? 0xFFB45A : color);
    f.t = 0; f.life = life || 0.08; f.i = (intensity || 1) * (G && G.settings && G.settings.reduceFlash ? 0.5 : 1);
    U.uFlashP.value[k].set(x, y, z, radius || 6);
    U.uFlashC.value[k].set(c.r, c.g, c.b, f.i);
  };
  function updateFlashes(dt) {
    for (var i = 0; i < 4; i++) {
      var f = flashes[i]; if (f.i <= 0) continue;
      f.t += dt; var a = 1 - f.t / f.life;
      if (a <= 0) { f.i = 0; U.uFlashC.value[i].w = 0; } else U.uFlashC.value[i].w = f.i * a;
    }
  }

  /* Viewmodel light link (Stage 4.6): sample the light volume where the player stands (plus one sight line toward
     the sun) and tint the gun's light: dark in a dark room, lit under a lamp, full sun outdoors. Smoothed over 0.15 s. */
  var vm = { k: 1, r: 1, g: 1, b: 1, sun: 1 }, _sunTo = null;
  function updateViewmodel(dt) {
    var R = IB.Render, G = IB.Game, LG = IB.LightGrid, GS = IB.GunSkins, L = Look.cur;
    if (!GS || !GS.vmLight || !R.vmSun || !G.player || !LG || !LG.ready) return;
    var c = R.camera.position, s = LG.sampleAt(c.x, c.y - 0.4, c.z); if (!s) return;
    var sunVis = 0;
    if (s.sky > 0.5 && G.level && G.level.world) {
      var d = Look.sunDir;
      sunVis = G.level.world.los(c.x, c.y, c.z, c.x + d.x * 60, c.y + d.y * 60, c.z + d.z * 60) ? s.sky : s.sky * 0.3;
    } else sunVis = s.sky * 0.3;
    var loc = s.local, lum = (0.2126 * loc[0] + 0.7152 * loc[1] + 0.0722 * loc[2]) * L.grid.intensity;
    var amb = L.ambI * (s.sky + (1 - s.sky) * L.indoorAmb);
    var k = Math.min(1, 0.16 + amb * 0.75 + lum * 0.55 + sunVis * 0.45);
    var tr = 1, tg = 1, tb = 1;
    if (lum > 0.02) { var m = Math.max(loc[0], loc[1], loc[2]) || 1, w = Math.min(0.5, lum); tr = 1 - w + w * loc[0] / m; tg = 1 - w + w * loc[1] / m; tb = 1 - w + w * loc[2] / m; }
    var a = Math.min(1, dt / 0.15);
    vm.k += (k - vm.k) * a; vm.r += (tr - vm.r) * a; vm.g += (tg - vm.g) * a; vm.b += (tb - vm.b) * a; vm.sun += (sunVis - vm.sun) * a;
    var V = GS.vmLight;
    V.uVmAmbLo.value.set(0.90 * vm.k * vm.r, 0.82 * vm.k * vm.g, 0.80 * vm.k * vm.b);
    V.uVmAmbHi.value.set(0.95 * vm.k * vm.r, 1.0 * vm.k * vm.g, 1.07 * vm.k * vm.b);
    var sc = R.sun.color, sk = 0.55 + 0.45 * vm.sun;
    R.vmSun.color.setRGB(sc.r * sk, sc.g * sk, sc.b * sk);
    // the nearest live flash lights the gun too
    var best = 0, fr = 0, fg = 0, fb = 0;
    for (var i = 0; i < 4; i++) {
      var C = U.uFlashC.value[i]; if (C.w <= 0) continue;
      var P = U.uFlashP.value[i], dx = P.x - c.x, dy = P.y - c.y, dz = P.z - c.z, I = C.w * 1.2 / (1 + dx * dx + dy * dy + dz * dz);
      if (I > best) { best = I; fr = C.x * I; fg = C.y * I; fb = C.z * I; }
    }
    V.uVmFlash.value.set(fr, fg, fb);
  }

  // every frame, after the theme ticks, before R.render
  var statT = 0, statN = 0, statSum = 0;
  Look.update = function (dt) {
    if (Look.stats) {   // ?lookstats=1: console only, nothing on screen
      statT += dt; statN++; statSum += dt;
      if (statT >= 2) {
        var R = IB.Render, info = R.renderer.info, P = IB.Post || {};
        console.log('[lookstats] ' + (statSum / statN * 1000).toFixed(1) + ' ms/frame (' + Math.round(statN / statSum) + ' fps), tier ' + R.tier +
          ', calls ' + info.render.calls + ', tris ' + info.render.triangles + ', post ' + (P.on ? P.mode + ' ' + P.w + 'x' + P.h : 'off') +
          ', shadows ' + (IB.Shadows && IB.Shadows.on ? IB.Shadows.renders + ' renders' : 'off'));
        statT = statN = statSum = 0;
      }
    }
    if (!Look.on || !Look.cur) return;
    updateFlashes(dt);
    updateViewmodel(dt);
    if (IB.Atmo) IB.Atmo.updateHaze();
    if (IB.Shadows) IB.Shadows.update();
    if (IB.LightGrid && IB.LightGrid.ready) {
      var G = IB.Game;
      if (G.zone !== Look._zone) { Look._zone = G.zone; IB.LightGrid.prioritise(G.zone || 0); }
      IB.LightGrid.work();
    }
  };
})(window.IB = window.IB || {});
