/* INKBOLT post pipeline (tactical look, Stages 1 and 6). The world and the viewmodel render into one offscreen
   target, then full-screen passes write the canvas. Fallback chain, chosen once per size / tier and logged:
     (a) multisampled half-float colour + depth texture  (b) the same without multisampling (+ FXAA)
     (c) 8-bit colour + depth texture (+ FXAA; bloom from a 0.9 threshold at half amount, trap T21)
     (d) no post: R.render draws straight to the canvas
   Every created target is bound and checked with gl.checkFramebufferStatus (three r128 does not check).
   Internal size = the drawing buffer, capped at 3.2 megapixels (high) / 2.1 (medium) (trap T11).
   Low and potato tiers and WebGL1 run without post (the look's grade then lives in the material: surface.js).

   Frame: world -> (copy of the world depth) -> viewmodel -> bloom (bright pass above 1.0 with a soft knee, a dual
   filter down / up chain: 5 levels high, 3 medium) -> composite (exposure, bloom, saturation, split tone, contrast,
   highlight shoulder, vignette, grain, dither) -> UI overlay pass.
   UI overlay (hard rule 1): the enemy health bars and the comic words live on layer 1 while post is on and are drawn
   after the composite straight to the canvas, so they skip bloom, grade and grain. The bars are depth-tested against
   a copy of the world depth and hidden behind the gun, by a runtime patch of their material (hpbars.js untouched).
   ?look=classic&post=1 draws the classic picture through the target with an identity composite (Stage 1 gate). */
(function (IB) {
  'use strict';
  var P = IB.Post = { on: false, mode: 'none', w: 0, h: 0, samples: 0, calls: 0, bloomAmt: 0 };
  var MP_CAP = { high: 3.2e6, medium: 2.1e6 };
  var SAMPLES = { high: 4, medium: 2 };
  var LEVELS = { high: 5, medium: 3 };
  var r = null, gl = null, main = null, depthCopy = null, fsScene = null, fsCam = null, fsMesh = null, logged = '';
  var bloomDown = [], bloomUp = [], M = {};
  var FS_V = 'varying vec2 vUv; void main(){ vUv = position.xy * 0.5 + 0.5; gl_Position = vec4( position.xy, 0.0, 1.0 ); }';

  P.pass = function (frag, uniforms, extra) {
    var o = { vertexShader: FS_V, fragmentShader: frag, uniforms: uniforms || {}, depthTest: false, depthWrite: false, fog: false };
    if (extra) for (var k in extra) o[k] = extra[k];
    return new THREE.ShaderMaterial(o);
  };
  P.run = function (mat, target) { fsMesh.material = mat; r.setRenderTarget(target); r.render(fsScene, fsCam); P.calls++; };

  var HASH = 'float ibH( vec2 p ) { return fract( sin( dot( p, vec2( 12.9898, 78.233 ) ) ) * 43758.5453 ); }';
  var COMP = [
    'uniform sampler2D tScene, tBloom; uniform float uIdentity, uExpo, uBloom, uSat, uCon, uVig, uGrain, uTime;',
    'uniform vec3 uLo, uHi; uniform vec2 uRes;',
    'varying vec2 vUv;', HASH,
    '#ifdef IB_FXAA',
    'vec3 ibFxaa( vec2 uv ) {',   // a compact FXAA for the non-multisampled fallbacks
    '  vec2 px = 1.0 / uRes; const vec3 L = vec3( 0.299, 0.587, 0.114 );',
    '  vec3 cM = texture2D( tScene, uv ).rgb;',
    '  float lM = dot( cM, L ), lN = dot( texture2D( tScene, uv + vec2( 0.0, px.y ) ).rgb, L ), lS = dot( texture2D( tScene, uv - vec2( 0.0, px.y ) ).rgb, L );',
    '  float lE = dot( texture2D( tScene, uv + vec2( px.x, 0.0 ) ).rgb, L ), lW = dot( texture2D( tScene, uv - vec2( px.x, 0.0 ) ).rgb, L );',
    '  float mn = min( lM, min( min( lN, lS ), min( lE, lW ) ) ), mx = max( lM, max( max( lN, lS ), max( lE, lW ) ) );',
    '  if ( mx - mn < max( 0.0312, mx * 0.125 ) ) return cM;',
    '  vec2 dir = normalize( vec2( ( lS - lN ), ( lE - lW ) ) + 1e-5 ) * px;',
    '  return 0.5 * ( texture2D( tScene, uv + dir * 0.5 ).rgb + texture2D( tScene, uv - dir * 0.5 ).rgb );',
    '}',
    '#endif',
    'void main() {',
    '#ifdef IB_FXAA',
    '  vec3 c = ibFxaa( vUv );',
    '#else',
    '  vec3 c = texture2D( tScene, vUv ).rgb;',
    '#endif',
    '  if ( uIdentity > 0.5 ) { gl_FragColor = vec4( c, 1.0 ); return; }',
    '  c *= uExpo;',
    '  c += texture2D( tBloom, vUv ).rgb * uBloom;',
    '  float l = dot( c, vec3( 0.2126, 0.7152, 0.0722 ) );',
    '  c = mix( vec3( l ), c, uSat );',
    '  c *= mix( uLo, uHi, smoothstep( 0.05, 0.85, l ) );',
    '  vec3 k = clamp( c, 0.0, 1.0 ); c = mix( c, k * k * ( 3.0 - 2.0 * k ) + max( c - 1.0, 0.0 ), uCon );',
    '  c = c / ( 1.0 + max( c - 0.82, 0.0 ) * 0.9 );',   // shoulder, identity below 0.82
    '  vec2 q = vUv - 0.5; c *= 1.0 - uVig * smoothstep( 0.28, 0.95, dot( q, q ) * 2.0 );',
    '  float lg = dot( clamp( c, 0.0, 1.0 ), vec3( 0.2126, 0.7152, 0.0722 ) );',
    '  c += ( ibH( vUv * uRes + uTime ) - 0.5 ) * uGrain * mix( 1.0, 0.45, lg );',
    '  c += ( ibH( vUv * uRes + uTime + 17.3 ) - ibH( vUv * uRes - uTime + 3.1 ) ) / 255.0;',   // triangular dither
    '  gl_FragColor = vec4( c, 1.0 );',
    '}'
  ].join('\n');
  // bright pass: above 1.0 with a soft knee (Unity-style); on the 8-bit fallback the threshold is 0.9
  var BRIGHT = [
    'uniform sampler2D t; uniform float uThr, uKnee; varying vec2 vUv;',
    'void main() {',
    '  vec3 c = texture2D( t, vUv ).rgb;',
    '  float m = max( c.r, max( c.g, c.b ) ), s = clamp( m - uThr + uKnee, 0.0, 2.0 * uKnee );',
    '  s = s * s / ( 4.0 * uKnee + 1e-4 );',
    '  gl_FragColor = vec4( c * max( s, m - uThr ) / max( m, 1e-4 ), 1.0 );',
    '}'
  ].join('\n');
  var DOWN = 'uniform sampler2D t; uniform vec2 uPx; varying vec2 vUv; void main() { vec3 c = texture2D( t, vUv ).rgb * 4.0;' +
    ' c += texture2D( t, vUv + vec2( -uPx.x, -uPx.y ) ).rgb + texture2D( t, vUv + vec2( uPx.x, -uPx.y ) ).rgb + texture2D( t, vUv + vec2( -uPx.x, uPx.y ) ).rgb + texture2D( t, vUv + uPx ).rgb;' +
    ' gl_FragColor = vec4( c / 8.0, 1.0 ); }';
  var UP = 'uniform sampler2D t, tAdd; uniform vec2 uPx; varying vec2 vUv; void main() { vec2 h = uPx;' +
    ' vec3 c = texture2D( t, vUv + vec2( -h.x * 2.0, 0.0 ) ).rgb + texture2D( t, vUv + vec2( h.x * 2.0, 0.0 ) ).rgb + texture2D( t, vUv + vec2( 0.0, -h.y * 2.0 ) ).rgb + texture2D( t, vUv + vec2( 0.0, h.y * 2.0 ) ).rgb;' +
    ' c += ( texture2D( t, vUv + vec2( -h.x, h.y ) ).rgb + texture2D( t, vUv + vec2( h.x, h.y ) ).rgb + texture2D( t, vUv + vec2( -h.x, -h.y ) ).rgb + texture2D( t, vUv + vec2( h.x, -h.y ) ).rgb ) * 2.0;' +
    ' gl_FragColor = vec4( c / 12.0 + texture2D( tAdd, vUv ).rgb, 1.0 ); }';
  // world depth copy, packed to RGBA8 (the overlay pass needs the world depth after the viewmodel pass cleared it)
  var DCOPY = '#include <packing>\nuniform sampler2D tDepth; varying vec2 vUv; void main() { gl_FragColor = packDepthToRGBA( texture2D( tDepth, vUv ).r ); }';

  P.init = function (renderer) {
    r = renderer; gl = r.getContext();
    fsScene = new THREE.Scene(); fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    var g = new THREE.BufferGeometry();   // one triangle covering the screen
    g.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
    fsMesh = new THREE.Mesh(g, null); fsMesh.frustumCulled = false; fsScene.add(fsMesh);
    M.comp = P.pass(COMP, {
      tScene: { value: null }, tBloom: { value: null }, uIdentity: { value: IB.Look && IB.Look.on ? 0 : 1 },
      uExpo: { value: 1 }, uBloom: { value: 0 }, uSat: { value: 1 }, uCon: { value: 0 }, uVig: { value: 0 }, uGrain: { value: 0 }, uTime: { value: 0 },
      uLo: { value: new THREE.Vector3(1, 1, 1) }, uHi: { value: new THREE.Vector3(1, 1, 1) }, uRes: { value: new THREE.Vector2(1, 1) } });
    M.compFxaa = M.comp.clone(); M.compFxaa.uniforms = M.comp.uniforms; M.compFxaa.defines = { IB_FXAA: '' };
    P.M = M;   // tests (look-readability.js switch the grain off)
    M.bright = P.pass(BRIGHT, { t: { value: null }, uThr: { value: 1 }, uKnee: { value: 0.35 } }); 
    M.down = P.pass(DOWN, { t: { value: null }, uPx: { value: new THREE.Vector2() } });
    M.up = P.pass(UP, { t: { value: null }, tAdd: { value: null }, uPx: { value: new THREE.Vector2() } });
    M.dcopy = P.pass(DCOPY, { tDepth: { value: null } });
    P.comp = M.comp;
  };
  P.warm = function () {
    if (!P.on) return;
    [M.comp, M.compFxaa, M.bright, M.down, M.up, M.dcopy].forEach(function (m) { fsMesh.material = m; try { r.compile(fsScene, fsCam); } catch (e) { /* first use compiles */ } });
  };

  function disposeAll() {
    if (main) { if (main.depthTexture) main.depthTexture.dispose(); main.dispose(); main = null; }
    if (depthCopy) { depthCopy.dispose(); depthCopy = null; }
    bloomDown.concat(bloomUp).forEach(function (t) { t.dispose(); }); bloomDown = []; bloomUp = [];
  }
  P.dispose = function () { disposeAll(); P.on = false; P.mode = 'none'; setOverlayLayers(); };

  function complete(t) {
    try {
      while (gl.getError() !== gl.NO_ERROR) { /* drain */ }
      r.setRenderTarget(t);
      r.clear(true, true, true);
      var ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE && gl.getError() === gl.NO_ERROR;
      if (ok && t.isWebGLMultisampleRenderTarget) {   // the resolve target is a second framebuffer
        var props = r.properties.get(t);
        if (props.__webglFramebuffer) { gl.bindFramebuffer(gl.FRAMEBUFFER, props.__webglFramebuffer); ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE; }
      }
      r.setRenderTarget(null);
      return ok;
    } catch (e) { r.setRenderTarget(null); return false; }
  }
  function make(kind, w, h, samples) {
    var dt = new THREE.DepthTexture(w, h); dt.type = THREE.UnsignedIntType; dt.format = THREE.DepthFormat;
    var o = { minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, format: THREE.RGBAFormat, depthBuffer: true, stencilBuffer: false, depthTexture: dt,
      type: kind === 'byte' ? THREE.UnsignedByteType : THREE.HalfFloatType };
    var t = samples > 0 ? new THREE.WebGLMultisampleRenderTarget(w, h, o) : new THREE.WebGLRenderTarget(w, h, o);
    if (samples > 0) t.samples = samples;
    t.texture.generateMipmaps = false;
    return t;
  }
  function colorRT(w, h, type) {
    var t = new THREE.WebGLRenderTarget(Math.max(1, w), Math.max(1, h), { minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, format: THREE.RGBAFormat, type: type, depthBuffer: false, stencilBuffer: false });
    t.texture.generateMipmaps = false;
    return t;
  }

  // called from R.resize: (re)build the targets for the current drawing-buffer size and tier
  P.resize = function () {
    if (!r) return;
    disposeAll();
    var R = IB.Render, tier = R.tier;
    P.on = false; P.mode = 'none';
    // ?posttest=b|c|d (plan 13.4): start the fallback chain at that step (d = no post pass: the grade in the materials)
    var force = typeof location !== 'undefined' ? (/[?&]posttest=([bcd])/.exec(location.search) || [])[1] : null;
    if (!IB.Look || !IB.Look.post || !MP_CAP[tier] || !r.capabilities.isWebGL2 || force === 'd') { setOverlayLayers(); log(); return; }
    var sz = new THREE.Vector2(); r.getDrawingBufferSize(sz);
    var w = sz.x, h = sz.y, k = Math.min(1, Math.sqrt(MP_CAP[tier] / (w * h)));
    w = Math.max(1, Math.floor(w * k)); h = Math.max(1, Math.floor(h * k));
    var tries = [['a', 'half', SAMPLES[tier]], ['b', 'half', 0], ['c', 'byte', 0]];
    if (!THREE.WebGLMultisampleRenderTarget) tries.shift();
    if (force) tries = tries.filter(function (t) { return t[0] >= force; });
    for (var i = 0; i < tries.length; i++) {
      var t = make(tries[i][1], w, h, tries[i][2]);
      if (complete(t)) { main = t; P.mode = tries[i][0]; P.samples = tries[i][2]; break; }
      if (t.depthTexture) t.depthTexture.dispose();
      t.dispose();
    }
    if (main) {
      P.on = true; P.w = w; P.h = h; P.target = main;
      var type = P.mode === 'c' ? THREE.UnsignedByteType : THREE.HalfFloatType;
      var n = LEVELS[tier] || 3, bw = w, bh = h;
      for (i = 0; i < n; i++) { bw = Math.max(1, bw >> 1); bh = Math.max(1, bh >> 1); bloomDown.push(colorRT(bw, bh, type)); if (i < n - 1) bloomUp.push(colorRT(bw, bh, type)); }
      depthCopy = colorRT(w, h, THREE.UnsignedByteType); depthCopy.texture.minFilter = depthCopy.texture.magFilter = THREE.NearestFilter;
      M.comp.uniforms.uRes.value.set(w, h);
      M.bright.uniforms.uThr.value = P.mode === 'c' ? 0.9 : 1.0;
    }
    setOverlayLayers();
    log();
  };
  function log() {
    var s = 'post ' + (P.on ? P.mode + ' ' + P.w + 'x' + P.h + (P.samples ? ' msaa' + P.samples : '') + ' bloom' + bloomDown.length : 'off') + ' tier ' + IB.Render.tier;
    if (s !== logged) { logged = s; if (IB.Look && (IB.Look.stats || IB.Look.on)) console.log('[look] ' + s); }
  }

  // per-level grade from the resolved look (IB.Look.begin)
  P.applyLook = function (L) {
    if (!M.comp) return;
    var u = M.comp.uniforms;
    if (!L) { u.uIdentity.value = 1; return; }
    u.uIdentity.value = 0;
    u.uExpo.value = L.exposure; P.bloomAmt = u.uBloom.value = L.bloom.amount * (P.mode === 'c' ? 0.5 : 1); u.uSat.value = L.grade.sat; u.uCon.value = L.grade.contrast;
    u.uLo.value.fromArray(L.grade.lo); u.uHi.value.fromArray(L.grade.hi);
    var T = IB.LOOKS.tier(IB.Render.tier);
    u.uVig.value = T.vignette ? L.vignette : 0; u.uGrain.value = T.vignette ? L.grain : 0;
    M.bright.uniforms.uKnee.value = L.bloom.knee;
  };

  // ---------------- UI overlay ----------------
  var overlay = [], bars = null, barPatched = false;
  P.overlay = function (obj) { if (overlay.indexOf(obj) < 0) overlay.push(obj); setLayer(obj); };
  function setLayer(o) { if (P.on && IB.Look && IB.Look.on) o.layers.set(1); else o.layers.set(0); }
  function setOverlayLayers() {
    overlay.forEach(setLayer);
    if (bars) { setLayer(bars); if (!(P.on && IB.Look && IB.Look.on) && barPatched) { bars.material.depthTest = true; bars.material.uniforms.uOverlay.value = 0; } }
  }
  function findBars() {
    if (bars || !IB.Look || !IB.Look.on) return;
    bars = IB.Render.scene.getObjectByName('hpbars');
    if (!bars) return;
    setLayer(bars);
    var m = bars.material;
    m.uniforms.tWorldDepth = { value: null }; m.uniforms.tVmDepth = { value: null }; m.uniforms.uInvRes = { value: new THREE.Vector2(1, 1) }; m.uniforms.uOverlay = { value: 0 }; m.uniforms.uVm = { value: 0 };
    m.fragmentShader = '#include <packing>\nuniform sampler2D tWorldDepth; uniform sampler2D tVmDepth; uniform vec2 uInvRes; uniform float uOverlay; uniform float uVm;\n' +
      m.fragmentShader.replace(/void\s+main\s*\(\s*\)\s*\{/, 'void main() {\n  if ( uOverlay > 0.5 ) { vec2 ibQ = gl_FragCoord.xy * uInvRes;' +
        ' if ( unpackRGBAToDepth( texture2D( tWorldDepth, ibQ ) ) < gl_FragCoord.z - 0.00002 || ( uVm > 0.5 && texture2D( tVmDepth, ibQ ).r < 0.9999 ) ) discard; }');
    m.needsUpdate = true; barPatched = true;
  }

  P.render = function (showViewmodel) {
    var R = IB.Render, look = IB.Look && IB.Look.on;
    P.calls = 0;
    findBars();
    r.setRenderTarget(main);   // explicit: ui/thumbs.js binds its own target on the same renderer (trap T6)
    r.clear(true, true, true);
    R.sky.position.copy(R.camera.position);
    R.camera.layers.set(0);
    r.render(R.scene, R.camera);
    if (look && barPatched) { M.dcopy.uniforms.tDepth.value = main.depthTexture; P.run(M.dcopy, depthCopy); r.setRenderTarget(main); }
    if (showViewmodel) { r.clearDepth(); r.render(R.vmScene, R.vmCam); }
    var u = M.comp.uniforms, bloomTex = null;
    if (look && P.bloomAmt > 0 && bloomDown.length) {
      M.bright.uniforms.t.value = main.texture; P.run(M.bright, bloomDown[0]);
      for (var i = 1; i < bloomDown.length; i++) {
        M.down.uniforms.t.value = bloomDown[i - 1].texture; M.down.uniforms.uPx.value.set(0.5 / bloomDown[i - 1].width, 0.5 / bloomDown[i - 1].height);
        P.run(M.down, bloomDown[i]);
      }
      var src = bloomDown[bloomDown.length - 1];
      for (i = bloomDown.length - 2; i >= 0; i--) {
        M.up.uniforms.t.value = src.texture; M.up.uniforms.tAdd.value = bloomDown[i].texture; M.up.uniforms.uPx.value.set(0.5 / src.width, 0.5 / src.height);
        P.run(M.up, bloomUp[i]); src = bloomUp[i];
      }
      bloomTex = src.texture;
    }
    u.tScene.value = main.texture; u.tBloom.value = bloomTex || main.texture; u.uBloom.value = bloomTex ? P.bloomAmt : 0;
    u.uTime.value = (performance.now() % 4096) / 1000;
    P.run(P.samples ? M.comp : M.compFxaa, null);
    // UI overlay: layer-1 objects straight to the canvas, after the grade
    if (look) {
      if (bars && barPatched) {
        var bu = bars.material.uniforms;
        bu.tWorldDepth.value = depthCopy.texture; bu.tVmDepth.value = main.depthTexture; bu.uInvRes.value.set(1 / R.renderer.domElement.width, 1 / R.renderer.domElement.height); bu.uOverlay.value = 1; bu.uVm.value = showViewmodel ? 1 : 0;
        bars.material.depthTest = false;
      }
      R.camera.layers.set(1);
      var bg = R.scene.background; R.scene.background = null;
      r.render(R.scene, R.camera); P.calls++;
      R.scene.background = bg;
      R.camera.layers.set(0);
    }
  };
})(window.IB = window.IB || {});
