/* INKBOLT render core: toon materials with inverted-hull ink outlines, geometry builder,
   world + viewmodel scenes, sky, clouds, backdrop. three.js r128 (global THREE). */
(function (IB) {
  'use strict';

  var PAL = IB.PAL = {
    ink: 0x15121C, paper: 0xFFFDF7, cream: 0xFFF1D6, sky: 0x8ED2FF, teal: 0x12C7B6,
    tangerine: 0xFF8A3D, bubblegum: 0xFF7FB0, sand: 0xF6D57A, purple: 0x8A6CD8,
    green: 0x5BCF4A, ammo: 0x2F7BEA, red: 0xF0443A, amber: 0xFFB21E, gunmetal: 0x2B2A33,
    shadow: 0x5E4F8C, chip: 0x12C7B6, shard: 0xFF7FB0, core: 0xFFC23A
  };

  // ---------- toon gradient: 4 texels, darkest band tinted toward Shadow Tint ----------
  function makeGradient() {
    var t = new THREE.Color(PAL.shadow);
    var m = Math.max(t.r, t.g, t.b);
    var tint = [t.r / m, t.g / m, t.b / m];
    // lighter tones: shadow band 0.72 (tinted toward Shadow Tint), mid band 0.9
    var band0 = tint.map(function (c) { return 0.72 * (0.6 + 0.4 * c); });
    var px = [band0, [0.9, 0.9, 0.9], [1, 1, 1], [1, 1, 1]];
    var data = new Uint8Array(16);
    for (var i = 0; i < 4; i++) {
      data[i * 4] = Math.round(px[i][0] * 255); data[i * 4 + 1] = Math.round(px[i][1] * 255);
      data[i * 4 + 2] = Math.round(px[i][2] * 255); data[i * 4 + 3] = 255;
    }
    var tex = new THREE.DataTexture(data, 4, 1, THREE.RGBAFormat);
    tex.minFilter = tex.magFilter = THREE.NearestFilter;
    tex.generateMipmaps = false; tex.needsUpdate = true;
    return tex;
  }

  // Outline uniforms are shared per "view" (world vs viewmodel) so resize/FOV updates are one write.
  function outlineUniforms(base, px) {
    return { uInk: { value: new THREE.Color(PAL.ink) }, uOutBase: { value: base }, uOutK: { value: 0.002 }, px: px };
  }

  var VERT_PARS = 'attribute vec3 aHull;\nvarying float vHull;\nuniform float uOutBase;\nuniform float uOutK;\nuniform float uBaked;\nuniform float uHullK;\nuniform float uOutMax;\n';
  var VERT_PROJECT = [
    'vec4 mvPosition = vec4( transformed, 1.0 );',
    '#ifdef USE_INSTANCING',
    ' mvPosition = instanceMatrix * mvPosition;',
    '#endif',
    'mvPosition = modelViewMatrix * mvPosition;',
    'vHull = 0.0;',
    'if ( dot( aHull, aHull ) > 0.0 ) {',
    '  vec4 hd = vec4( aHull, 0.0 );',
    '  #ifdef USE_SKINNING',
    '   hd = skinMatrix * hd;',   // the outline follows the bones (skinMatrix: skinnormal_vertex)
    '  #endif',
    '  #ifdef USE_INSTANCING',
    '   hd = instanceMatrix * hd;',
    '  #endif',
    '  hd = modelViewMatrix * hd;',
    '  mvPosition.xyz += hd.xyz * max( 0.0, min( uOutMax, max( uOutBase, uOutK * -mvPosition.z ) * uHullK ) - uBaked );',
    '  vHull = 1.0;',
    '}',
    'gl_Position = projectionMatrix * mvPosition;'
  ].join('\n');

  /* Undercover (IB.Render.cloak 0..1, driven by ui/skillhud.js): the world goes a comic ink black, greyed with shades
     (no streaks); robots (their own material) keep their colours, get a cold blue sheen and a thick,
     bright stealth-blue outline drawn after the fog so they read from across the map. */
  var ONE = { value: 1 };
  var CLOAK_WORLD = [
    'if ( uCloak > 0.0 ) {',
    '  float lum = dot( gl_FragColor.rgb, vec3( 0.299, 0.587, 0.114 ) );',
    '  vec3 g = vec3( pow( lum, 1.35 ) * 0.55 );',
    '  float hatch = step( 0.5, fract( ( gl_FragCoord.x - gl_FragCoord.y ) * 0.25 ) ) * step( lum, 0.32 ) * 0.05;',
    '  g = g - hatch;',
    '  if ( vHull > 0.5 ) g = vec3( 0.02 );',
    '  gl_FragColor.rgb = mix( gl_FragColor.rgb, g, uCloak );',
    '}'
  ].join('\n');
  var CLOAK_ROBOT = [
    'if ( uCloak > 0.0 ) {',
    '  if ( vHull > 0.5 ) gl_FragColor.rgb = mix( gl_FragColor.rgb, uInk, uCloak );',
    '  else gl_FragColor.rgb = mix( gl_FragColor.rgb, gl_FragColor.rgb * 0.55 + vec3( 0.10, 0.42, 0.85 ), uCloak * 0.55 );',
    '}'
  ].join('\n');

  /* opts: { uni: outline uniforms, fx: per-instance flash/ink attribute, vertexColors, color, opacityAttr,
       outMax: cap on the outline width in the mesh's own units (default: none). The outline normally widens with
       distance to stay about 3 px on screen; on a small object drawn enlarged (loot, pickups, a gun turning in its
       beam) that swallows the whole thing in black and makes it look several times its size from afar, so those
       materials cap it and the object keeps its real silhouette at any distance. } */
  function toonMaterial(opts) {
    opts = opts || {};
    var mat = new THREE.MeshToonMaterial({
      color: opts.color !== undefined ? opts.color : 0xffffff,
      vertexColors: opts.vertexColors !== false,
      gradientMap: IB.Render.gradient,
      map: opts.map || null
    });
    if (opts.skinning) mat.skinning = true;
    var baked = { value: opts.baked || 0 }, outMax = { value: opts.outMax > 0 ? opts.outMax : 1e6 };
    var uni = opts.uni || IB.Render.worldOutline;
    var fx = !!opts.fx, robot = uni === IB.Render.robotOutline;
    mat.onBeforeCompile = function (sh) {
      sh.uniforms.uInk = uni.uInk; sh.uniforms.uOutBase = uni.uOutBase; sh.uniforms.uOutK = uni.uOutK; sh.uniforms.uBaked = baked; sh.uniforms.uOutMax = outMax;
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\n' + VERT_PARS + (fx ? 'attribute vec2 aFx;\nvarying vec2 vFx;\n' : ''))
        .replace('#include <project_vertex>', VERT_PROJECT + (fx ? '\nvFx = aFx;' : ''));
      sh.uniforms.uCloak = IB.Render.cloak; sh.uniforms.uHullK = robot ? IB.Render.robotHull : ONE;
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform vec3 uInk;\nuniform float uCloak;\nvarying float vHull;\n' + (fx ? 'varying vec2 vFx;\n' : ''))
        .replace('#include <fog_fragment>',
          (fx ? 'gl_FragColor.rgb = mix( gl_FragColor.rgb, vec3( 1.0 ), vFx.x );\ngl_FragColor.rgb = mix( gl_FragColor.rgb, uInk, vFx.y );\n' : '') +
          'if ( vHull > 0.5 ) gl_FragColor = vec4( uInk, 1.0 );\n#include <fog_fragment>\n' + (robot ? CLOAK_ROBOT : CLOAK_WORLD));
    };
    mat.customProgramCacheKey = function () { return 'ibtoon' + (fx ? 'fx' : '') + (robot ? 'r' : uni === IB.Render.worldOutline ? 'w' : 'v') + (opts.skinning ? 's' : ''); };
    mat.userData.outMax = outMax;   // the cap can be set later: mat.userData.outMax.value = 0.02
    return mat;
  }

  // ---------- Geometry builder: solid parts + inverted hull in one geometry ----------
  var _v = new THREE.Vector3(), _n = new THREE.Vector3(), _nm = new THREE.Matrix3();
  function Geo() { this.pos = []; this.nor = []; this.col = []; this.hull = []; this.idx = []; this.m = null; }
  Geo.prototype.setMatrix = function (m) { this.m = m || null; if (m) _nm.getNormalMatrix(m); return this; };
  Geo.prototype._vert = function (x, y, z, nx, ny, nz, c, hx, hy, hz) {
    if (this.m) {
      _v.set(x, y, z).applyMatrix4(this.m); x = _v.x; y = _v.y; z = _v.z;
      _n.set(nx, ny, nz).applyMatrix3(_nm).normalize(); nx = _n.x; ny = _n.y; nz = _n.z;
      if (hx || hy || hz) {
        var L = Math.sqrt(hx * hx + hy * hy + hz * hz);
        _n.set(hx, hy, hz).applyMatrix3(_nm).normalize().multiplyScalar(L); hx = _n.x; hy = _n.y; hz = _n.z;
      }
    }
    this.pos.push(x, y, z); this.nor.push(nx, ny, nz); this.col.push(c.r, c.g, c.b); this.hull.push(hx || 0, hy || 0, hz || 0);
    return this.pos.length / 3 - 1;
  };
  var _c = new THREE.Color();
  function col(c) { return (c && c.isColor) ? c : _c.set(c === undefined ? 0xffffff : c).clone(); }

  // Axis-aligned box centred at (cx,cy,cz). opts.hull (default true), opts.noBottom.
  Geo.prototype.box = function (cx, cy, cz, sx, sy, sz, color, opts) {
    opts = opts || {};
    var c = col(color), hx = sx / 2, hy = sy / 2, hz = sz / 2;
    var faces = [
      [1, 0, 0, [[1, -1, 1], [1, -1, -1], [1, 1, -1], [1, 1, 1]]],
      [-1, 0, 0, [[-1, -1, -1], [-1, -1, 1], [-1, 1, 1], [-1, 1, -1]]],
      [0, 1, 0, [[-1, 1, 1], [1, 1, 1], [1, 1, -1], [-1, 1, -1]]],
      [0, -1, 0, [[-1, -1, -1], [1, -1, -1], [1, -1, 1], [-1, -1, 1]]],
      [0, 0, 1, [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]]],
      [0, 0, -1, [[1, -1, -1], [-1, -1, -1], [-1, 1, -1], [1, 1, -1]]]
    ];
    var tint = opts.topTint;
    for (var f = 0; f < 6; f++) {
      var F = faces[f];
      if (opts.noBottom && F[1] === -1) continue;
      var fc = (tint && F[1] === 1) ? col(tint) : c;
      var b = this.pos.length / 3;
      for (var k = 0; k < 4; k++) { var p = F[3][k]; this._vert(cx + p[0] * hx, cy + p[1] * hy, cz + p[2] * hz, F[0], F[1], F[2], fc); }
      this.idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
    }
    if (opts.hull !== false) this.boxHull(cx, cy, cz, sx, sy, sz, opts.hullScale || 1);
    return this;
  };
  Geo.prototype.boxHull = function (cx, cy, cz, sx, sy, sz, s) {
    var b = this.pos.length / 3, hx = sx / 2, hy = sy / 2, hz = sz / 2, ink = col(PAL.ink);
    for (var i = 0; i < 8; i++) {
      var X = (i & 1) ? 1 : -1, Y = (i & 2) ? 1 : -1, Z = (i & 4) ? 1 : -1;
      this._vert(cx + X * hx, cy + Y * hy, cz + Z * hz, 0, 1, 0, ink, X * s, Y * s, Z * s);
    }
    // reversed winding (inside-out shell)
    var q = [[1, 3, 7, 5], [0, 4, 6, 2], [2, 6, 7, 3], [0, 1, 5, 4], [4, 5, 7, 6], [0, 2, 3, 1]];
    for (var j = 0; j < 6; j++) {
      var Q = q[j];
      this.idx.push(b + Q[0], b + Q[2], b + Q[1], b + Q[0], b + Q[3], b + Q[2]);
    }
  };
  // Vertical cylinder / cone frustum. rTop, rBot, height h, base at y0.
  Geo.prototype.cyl = function (cx, y0, cz, rBot, rTop, h, seg, color, opts) {
    opts = opts || {};
    var c = col(color), self = this, i, a, ca, sa;
    var slope = (rBot - rTop) / h, nyS = slope / Math.sqrt(1 + slope * slope), nrS = 1 / Math.sqrt(1 + slope * slope);
    var b = this.pos.length / 3;
    for (i = 0; i <= seg; i++) {
      a = i / seg * Math.PI * 2; ca = Math.cos(a); sa = Math.sin(a);
      this._vert(cx + ca * rBot, y0, cz + sa * rBot, ca * nrS, nyS, sa * nrS, c);
      this._vert(cx + ca * rTop, y0 + h, cz + sa * rTop, ca * nrS, nyS, sa * nrS, c);
    }
    for (i = 0; i < seg; i++) { var p = b + i * 2; this.idx.push(p, p + 1, p + 3, p, p + 3, p + 2); }
    function cap(y, r, ny) {
      if (r <= 0.0001) return;
      var cb = self.pos.length / 3; self._vert(cx, y, cz, 0, ny, 0, opts.capColor ? col(opts.capColor) : c);
      for (var k = 0; k <= seg; k++) { var A = k / seg * Math.PI * 2; self._vert(cx + Math.cos(A) * r, y, cz + Math.sin(A) * r, 0, ny, 0, opts.capColor ? col(opts.capColor) : c); }
      for (k = 0; k < seg; k++) { if (ny > 0) self.idx.push(cb, cb + k + 2, cb + k + 1); else self.idx.push(cb, cb + k + 1, cb + k + 2); }
    }
    if (!opts.noTop) cap(y0 + h, rTop, 1);
    if (!opts.noBottom) cap(y0, rBot, -1);
    if (opts.hull !== false) {
      var hb = this.pos.length / 3, ink = col(PAL.ink), s = opts.hullScale || 1;
      for (i = 0; i <= seg; i++) {
        a = i / seg * Math.PI * 2; ca = Math.cos(a); sa = Math.sin(a);
        this._vert(cx + ca * rBot, y0, cz + sa * rBot, 0, 1, 0, ink, ca * s, -s, sa * s);
        this._vert(cx + ca * rTop, y0 + h, cz + sa * rTop, 0, 1, 0, ink, ca * s, s, sa * s);
      }
      var ct = this._vert(cx, y0 + h, cz, 0, 1, 0, ink, 0, s, 0), cbm = this._vert(cx, y0, cz, 0, 1, 0, ink, 0, -s, 0);
      for (i = 0; i < seg; i++) {
        var q = hb + i * 2;
        this.idx.push(q, q + 3, q + 1, q, q + 2, q + 3);
        this.idx.push(ct, q + 1, q + 3); this.idx.push(cbm, q + 2, q);
      }
    }
    return this;
  };
  // Low-poly sphere (lat/long), optional y-squash.
  Geo.prototype.sphere = function (cx, cy, cz, r, color, opts) {
    opts = opts || {};
    var c = col(color), ws = opts.ws || 8, hs = opts.hs || 6, sy = opts.sy || 1, b = this.pos.length / 3, i, j;
    for (j = 0; j <= hs; j++) {
      var th = j / hs * Math.PI, st = Math.sin(th), ct = Math.cos(th);
      for (i = 0; i <= ws; i++) {
        var ph = i / ws * Math.PI * 2, x = Math.cos(ph) * st, z = Math.sin(ph) * st;
        this._vert(cx + x * r, cy + ct * r * sy, cz + z * r, x, ct, z, c);
      }
    }
    for (j = 0; j < hs; j++) for (i = 0; i < ws; i++) {
      var a = b + j * (ws + 1) + i, d = a + ws + 1;
      this.idx.push(a, a + 1, d, a + 1, d + 1, d);
    }
    if (opts.hull !== false) {
      var hb = this.pos.length / 3, ink = col(PAL.ink), s = opts.hullScale || 1;
      for (j = 0; j <= hs; j++) {
        var th2 = j / hs * Math.PI, st2 = Math.sin(th2), ct2 = Math.cos(th2);
        for (i = 0; i <= ws; i++) {
          var ph2 = i / ws * Math.PI * 2, x2 = Math.cos(ph2) * st2, z2 = Math.sin(ph2) * st2;
          this._vert(cx + x2 * r, cy + ct2 * r * sy, cz + z2 * r, 0, 1, 0, ink, x2 * s, ct2 * s, z2 * s);
        }
      }
      for (j = 0; j < hs; j++) for (i = 0; i < ws; i++) {
        var a2 = hb + j * (ws + 1) + i, d2 = a2 + ws + 1;
        this.idx.push(a2, d2, a2 + 1, a2 + 1, d2, d2 + 1);
      }
    }
    return this;
  };
  // Flat polygon on XZ plane (y up), e.g. painted marks. pts: [[x,z],...] convex.
  Geo.prototype.flat = function (pts, y, color) {
    var c = col(color), b = this.pos.length / 3;
    for (var i = 0; i < pts.length; i++) this._vert(pts[i][0], y, pts[i][1], 0, 1, 0, c);
    // pick winding so the face points up (+y)
    var ax = pts[1][0] - pts[0][0], az = pts[1][1] - pts[0][1], bx = pts[2][0] - pts[0][0], bz = pts[2][1] - pts[0][1];
    var up = (az * bx - ax * bz) > 0;
    for (i = 1; i < pts.length - 1; i++) { if (up) this.idx.push(b, b + i, b + i + 1); else this.idx.push(b, b + i + 1, b + i); }
    return this;
  };
  Geo.prototype.count = function () { return this.idx.length / 3; };
  Geo.prototype.build = function () {
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.nor, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.col, 3));
    g.setAttribute('aHull', new THREE.Float32BufferAttribute(this.hull, 3));
    var n = this.pos.length / 3;
    g.setIndex(n > 65535 ? new THREE.Uint32BufferAttribute(this.idx, 1) : new THREE.Uint16BufferAttribute(this.idx, 1));
    g.computeBoundingSphere(); g.computeBoundingBox();
    return g;
  };
  IB.Geo = Geo;

  // ---------- Renderer ----------
  var R = IB.Render = {
    renderer: null, scene: null, camera: null, vmScene: null, vmCam: null,
    gradient: null, worldOutline: null, vmOutline: null, baseFov: 100, fovMul: 1, tier: 'high', pixelRatio: 1,
    width: 1, height: 1
  };

  R.init = function (canvas) {
    var r = R.renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, powerPreference: 'high-performance' });
    r.autoClear = false;
    r.setClearColor(PAL.ink, 1);
    R.gradient = makeGradient();
    R.worldOutline = outlineUniforms(0.012, 3.2);
    // robots: the world's outline width (shared uniforms) but their own ink colour (Undercover tints it a stealthy blue)
    R.robotOutline = { uInk: { value: new THREE.Color(PAL.ink) }, uOutBase: R.worldOutline.uOutBase, uOutK: R.worldOutline.uOutK, px: R.worldOutline.px };
    R.vmOutline = outlineUniforms(0.0035, 2.2);
    R.cloak = { value: 0 }; R.robotHull = { value: 1 };   // Undercover look (ui/skillhud.js)
    R.scene = new THREE.Scene();
    R.camera = new THREE.PerspectiveCamera(60, 1, 0.1, 420);   // near 0.1 for depth precision
    R.camera.rotation.order = 'YXZ';
    R.scene.add(R.camera);
    var sun = R.sun = new THREE.DirectionalLight(0xffffff, 1); sun.position.set(0.42, 0.82, 0.38); R.scene.add(sun);
    R.vmScene = new THREE.Scene();
    R.vmCam = new THREE.PerspectiveCamera(58, 1, 0.01, 10);
    var vsun = new THREE.DirectionalLight(0xffffff, 1); vsun.position.set(0.3, 0.9, 0.5); R.vmScene.add(vsun);
    R.vmScene.add(R.vmCam);
    R.makeSky();
    R.setFog(PAL.cream, 45, 120);
    R.resize();
  };

  R.setFog = function (color, near, far) {
    R.scene.fog = new THREE.Fog(color, near, far);
    R.fogFar = far;
  };

  R.makeSky = function () {
    var g = new THREE.SphereGeometry(300, 24, 12);
    var m = new THREE.ShaderMaterial({
      uniforms: { top: { value: new THREE.Color(PAL.sky) }, horizon: { value: new THREE.Color(PAL.cream) }, uCloak: R.cloak },
      vertexShader: 'varying float vY; void main(){ vY = normalize(position).y; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
      fragmentShader: 'uniform vec3 top; uniform vec3 horizon; uniform float uCloak; varying float vY; void main(){ float t = smoothstep(0.0, 0.32, vY); t = floor(t*5.0+0.5)/5.0; vec3 c = mix(horizon, top, t); float l = dot(c, vec3(0.299, 0.587, 0.114)); gl_FragColor = vec4(mix(c, vec3(l * 0.32 + 0.03), uCloak), 1.0); }',
      side: THREE.BackSide, depthWrite: false, fog: false
    });
    R.sky = new THREE.Mesh(g, m); R.sky.renderOrder = -10; R.sky.frustumCulled = false;
    R.scene.add(R.sky);
  };
  // theme environment: sky dome (or none indoors), background colour, fog, light direction
  R.applyEnv = function (env) {
    var fog = env.fog || {};
    R.sky.visible = !!env.sky;
    if (env.sky) R.setSky(env.sky[0], env.sky[1]);
    R.renderer.setClearColor(new THREE.Color(env.clear || fog.color || '#15121C'), 1);
    R.scene.fog.color.set(fog.color || '#FFF0DC');
    R.scene.fog.near = R.envFogNear = fog.near || 45;
    R.envFogFar = fog.far || 120;
    R.envFogScale = !!fog.tierScale;
    R.applyFogFar();
    // env.far (optional): the camera's far plane for levels that look a long way out (a city hundreds of metres down)
    R.camera.far = env.far || 420; R.camera.updateProjectionMatrix();
    var s = env.sun || [0.42, 0.82, 0.38]; R.sun.position.set(s[0], s[1], s[2]);
  };
  // fog end: the theme's, capped by the graphics tier (120 m on high); a theme with fog.tierScale (a skyline far out
  // that must stay readable) scales its own distance by the tier instead (high = 120 = x1)
  R.applyFogFar = function () {
    if (!R.scene.fog) return;
    var t = R.tierFogFar || 999, e = R.envFogFar || 120;
    R.scene.fog.far = R.envFogScale && t < 999 ? e * t / 120 : Math.min(e, t);
    // a low tier's short fog end must not land on or before the theme's fog start (the whole view would turn fog
    // colour): keep the start at most 55% of the end. High / medium never hit this (end 120+, starts are 45-62).
    if (R.envFogNear !== undefined) R.scene.fog.near = Math.min(R.envFogNear, R.scene.fog.far * 0.55);
  };
  R.setSky = function (top, horizon) { R.sky.material.uniforms.top.value.set(top); R.sky.material.uniforms.horizon.value.set(horizon); };

  // horizontal FOV setting -> vertical camera FOV (portrait keeps the setting as vertical)
  R.vfov = function (hfovDeg, aspect) {
    var h = hfovDeg * Math.PI / 180;
    var v = 2 * Math.atan(Math.tan(h / 2) / Math.max(aspect, 1e-3));
    return Math.min(v * 180 / Math.PI, hfovDeg);
  };

  R.updateOutlineK = function () {
    var cssH = R.height;
    var wv = R.camera.fov * Math.PI / 180, vv = R.vmCam.fov * Math.PI / 180;
    R.worldOutline.uOutK.value = R.worldOutline.px * 2 * Math.tan(wv / 2) / cssH;
    R.vmOutline.uOutK.value = R.vmOutline.px * 2 * Math.tan(vv / 2) / cssH;
  };

  R.applyFov = function () {
    R.camera.aspect = R.width / R.height;
    R.camera.fov = R.vfov(R.baseFov * R.fovMul, R.camera.aspect);
    R.camera.updateProjectionMatrix();
    R.vmCam.aspect = R.camera.aspect;
    R.vmCam.fov = R.vmCam.aspect >= 1 ? 58 : Math.min(88, 58 / Math.sqrt(R.vmCam.aspect));
    R.vmCam.updateProjectionMatrix();
    R.updateOutlineK();
  };

  R.resize = function () {
    var w = window.innerWidth, h = window.innerHeight;
    R.width = Math.max(1, w); R.height = Math.max(1, h);
    var dpr = window.devicePixelRatio || 1;
    var pr = { high: Math.min(dpr, 2), medium: Math.min(dpr, 1.5), low: 1, potato: 0.85 }[R.tier] || 1;
    R.pixelRatio = pr;
    R.renderer.setPixelRatio(pr);
    R.renderer.setSize(R.width, R.height, false);
    R.applyFov();
  };

  R.render = function (showViewmodel) {
    var r = R.renderer;
    r.clear(true, true, true);
    R.sky.position.copy(R.camera.position);
    r.render(R.scene, R.camera);
    if (showViewmodel) { r.clearDepth(); r.render(R.vmScene, R.vmCam); }
  };

  // Canvas texture helper (decal atlas, blob, stripes)
  R.canvasTex = function (w, h, draw, nearest) {
    var cv = document.createElement('canvas'); cv.width = w; cv.height = h;
    draw(cv.getContext('2d'), w, h);
    var t = new THREE.CanvasTexture(cv);
    if (nearest) { t.minFilter = t.magFilter = THREE.NearestFilter; t.generateMipmaps = false; }
    return t;
  };

  R.toonMaterial = toonMaterial;
})(window.IB = window.IB || {});
