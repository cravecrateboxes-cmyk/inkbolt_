/* INKBOLT atmosphere (tactical look, Stage 2.5 / 7): one fog function for every material, the sky shader.
   Fog design (plan 2.5): every fogged material (the dozens of built-in unlit ones too: decals, particles, tracers,
   glows, sprites) must fog the same way, and built-in materials cannot take custom uniforms. So the look keeps a
   plain THREE.Fog and only three's standard fog uniforms, and overrides the four fog chunks ONCE, before any
   program compiles (trap T28: a changed chunk never reaches an already compiled program):
     scene.fog.near = haze length L (metres to 63% haze at ground level; look.fog.length, the same on every tier)
     scene.fog.far  = the fog wall distance exactly as before (theme far, capped or scaled by the tier: trap T7)
   Haze thins with height above IB_FOG_H0; the wall still reaches full density at fogFar so zone loading stays hidden.
   With ?look=classic install() does nothing and the stock chunks stay. */
(function (IB) {
  'use strict';
  var Atmo = IB.Atmo = { installed: false };

  var FOG_FN = [
    '#define IB_FOG_HK 0.045',
    '#define IB_FOG_H0 2.0',
    '#define IB_FOG_MAX 0.92',
    'float ibFogAmount( float depth, float worldY, float hazeLen, float wallFar ) {',
    '  float wall = smoothstep( wallFar * 0.72, wallFar, depth );',
    '  float thin = exp( -max( worldY - IB_FOG_H0, 0.0 ) * IB_FOG_HK );',
    '  float haze = ( 1.0 - exp( -depth / max( hazeLen, 1.0 ) * thin ) ) * IB_FOG_MAX;',
    '  return max( wall, haze );',
    '}'
  ].join('\n');
  Atmo.FOG_FN = FOG_FN;

  Atmo.install = function () {
    if (Atmo.installed || !IB.Look || !IB.Look.on) return;
    var C = THREE.ShaderChunk;
    C.fog_pars_vertex = '#ifdef USE_FOG\n\tvarying float fogDepth;\n\tvarying float vFogY;\n#endif\n';
    // world height without `transformed` (sprites have none) and without a new uniform: column 1 of the view
    // rotation, dotted with the view-space position, plus the camera height
    C.fog_vertex = '#ifdef USE_FOG\n\tfogDepth = - mvPosition.z;\n\tvFogY = dot( viewMatrix[ 1 ].xyz, mvPosition.xyz ) + cameraPosition.y;\n#endif\n';
    C.fog_pars_fragment = '#ifdef USE_FOG\n\tuniform vec3 fogColor;\n\tvarying float fogDepth;\n\tvarying float vFogY;\n' +
      '\t#ifdef FOG_EXP2\n\t\tuniform float fogDensity;\n\t#else\n\t\tuniform float fogNear;\n\t\tuniform float fogFar;\n\t#endif\n' + FOG_FN + '\n#endif\n';
    C.fog_fragment = '#ifdef USE_FOG\n\t#ifdef FOG_EXP2\n\t\tfloat fogFactor = 1.0 - exp( - fogDensity * fogDensity * fogDepth * fogDepth );\n' +
      '\t#else\n\t\tfloat fogFactor = ibFogAmount( fogDepth, vFogY, fogNear, fogFar );\n\t#endif\n' +
      '\tgl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );\n#endif\n';
    Atmo.installed = true;
  };

  // CPU twin of ibFogAmount (custom haze shaders fit their own fog to it, trap T8)
  Atmo.fogAmount = function (depth, worldY, hazeLen, wallFar) {
    var s = function (a, b, x) { var t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
    var wall = s(wallFar * 0.72, wallFar, depth);
    var thin = Math.exp(-Math.max(worldY - 2.0, 0) * 0.045);
    return Math.max(wall, (1 - Math.exp(-depth / Math.max(hazeLen, 1) * thin)) * 0.92);
  };

  /* Custom haze shaders (trap T8). Theme shaders that do their own linear haze with uniforms uFog / uNear / uFar
     (stronghold waterfalls, mossgarden stream; their ticks may copy scene.fog into them each frame) are fitted to
     ibFogAmount every frame after the theme ticks: a least-squares line through the curve at 100, 300 and 1000 m at
     the mesh's own height. The city below (zones.js) keeps its own depth haze: it is a vista hundreds of metres
     down, tuned per theme to the fog colour, and never meets world geometry at the same depth (decision recorded
     in PROGRESS.md). */
  var hazeMats = [];
  Atmo.adoptHaze = function (level) {
    hazeMats = [];
    if (!IB.Look.on || !level || !level.root) return;
    var _v = new THREE.Vector3();
    level.root.traverse(function (o) {
      var m = o.material;
      if (!o.isMesh || !m || !m.isShaderMaterial || !m.uniforms || !m.uniforms.uFog || !m.uniforms.uNear || !m.uniforms.uFar) return;
      if (!o.geometry.boundingSphere) o.geometry.computeBoundingSphere();
      o.updateMatrixWorld(true);
      _v.copy(o.geometry.boundingSphere.center).applyMatrix4(o.matrixWorld);
      hazeMats.push({ m: m, y: _v.y });
    });
  };
  Atmo.updateHaze = function () {
    if (!hazeMats.length) return;
    var fog = IB.Render.scene.fog; if (!fog) return;
    for (var i = 0; i < hazeMats.length; i++) {
      var h = hazeMats[i], D = [100, 300, 1000], sx = 0, sy = 0, sxx = 0, sxy = 0;
      for (var j = 0; j < 3; j++) { var a = Atmo.fogAmount(D[j], h.y, fog.near, fog.far); sx += D[j]; sy += a; sxx += D[j] * D[j]; sxy += D[j] * a; }
      var k = (3 * sxy - sx * sy) / (3 * sxx - sx * sx), b = (sy - k * sx) / 3;
      if (k <= 1e-6) { h.m.uniforms.uNear.value = 1e5; h.m.uniforms.uFar.value = 1e5 + 1; continue; }
      var n = -b / k; h.m.uniforms.uNear.value = n; h.m.uniforms.uFar.value = n + 1 / k;
      h.m.uniforms.uFog.value.copy(fog.color);
    }
  };

  // ---- sky: smooth gradient, sun glow and disc, a soft cloud layer (replaces the 5-band toy sky) ----
  var SKY_V = 'varying vec3 vD; void main(){ vD = normalize( position ); gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 ); }';
  var SKY_F = [
    'uniform vec3 top; uniform vec3 horizon; uniform float uCloak; uniform vec3 uSunDir; uniform vec3 uSunC; uniform float uClouds; uniform float uDisc;',
    'varying vec3 vD;',
    'float h3( vec3 p ) { return fract( sin( dot( p, vec3( 127.1, 311.7, 74.7 ) ) ) * 43758.5453 ); }',
    'float n3( vec3 p ) { vec3 i = floor( p ), f = fract( p ); f = f * f * ( 3.0 - 2.0 * f );',
    '  return mix( mix( mix( h3( i ), h3( i + vec3( 1, 0, 0 ) ), f.x ), mix( h3( i + vec3( 0, 1, 0 ) ), h3( i + vec3( 1, 1, 0 ) ), f.x ), f.y ),',
    '    mix( mix( h3( i + vec3( 0, 0, 1 ) ), h3( i + vec3( 1, 0, 1 ) ), f.x ), mix( h3( i + vec3( 0, 1, 1 ) ), h3( i + vec3( 1, 1, 1 ) ), f.x ), f.y ), f.z ); }',
    'void main() {',
    '  vec3 d = normalize( vD ); float t = pow( smoothstep( -0.02, 0.62, d.y ), 0.62 );',
    '  vec3 c = mix( horizon * 0.96, top * 0.82, t );',
    '  float s = max( dot( d, normalize( uSunDir ) ), 0.0 );',
    '  c += uSunC * ( pow( s, 420.0 ) * 2.4 * uDisc + pow( s, 14.0 ) * 0.30 + pow( s, 3.0 ) * 0.10 );',
    '  if ( uClouds > 0.0 ) {',
    '    vec2 q = d.xz / max( d.y + 0.12, 0.05 );',
    '    float cl = n3( vec3( q * 1.3, 1.0 ) ) * 0.55 + n3( vec3( q * 3.1, 4.0 ) ) * 0.3 + n3( vec3( q * 7.0, 9.0 ) ) * 0.15;',
    '    float cm = smoothstep( 0.52, 0.78, cl ) * smoothstep( 0.0, 0.22, d.y ) * uClouds;',
    '    c = mix( c, mix( horizon, vec3( 1.0 ), 0.55 ) * ( 0.82 + 0.3 * s ), cm * 1.5 );',
    '  }',
    '  float l = dot( c, vec3( 0.299, 0.587, 0.114 ) );',
    '  gl_FragColor = vec4( mix( c, vec3( l * 0.32 + 0.03 ), uCloak ), 1.0 );',
    '}'
  ].join('\n');
  // swap the sky dome's shaders once (keeps the uniforms top, horizon, uCloak that R.setSky and the cloak write)
  Atmo.skyInstall = function () {
    var R = IB.Render;
    if (!R.sky || R.sky.userData.look) return;
    var m = R.sky.material, U = IB.Look.U;
    m.uniforms.uSunDir = U.uSunDirW; m.uniforms.uSunC = U.uSunFog;
    m.uniforms.uClouds = { value: 0.5 }; m.uniforms.uDisc = { value: 1 };
    m.vertexShader = SKY_V; m.fragmentShader = SKY_F; m.needsUpdate = true;
    R.sky.userData.look = true;
  };
  Atmo.skyApply = function (look) {
    var R = IB.Render;
    if (!R.sky || !R.sky.userData.look) return;
    var u = R.sky.material.uniforms;
    u.uClouds.value = look.sky.clouds; u.uDisc.value = look.sky.sunDisc ? 1 : 0;
  };

  /* ---- Stage 7 extras (medium and high tiers only; absent on low and potato) ----
     Dust motes: one Points cloud in a 14 m box that wraps around the camera, drifting; brightness from the light
     volume at the camera (one CPU sample a frame) and the sun where the sky is visible. Kinds per look.dust:
     'wind' / 'beams' / 'heavy' / 'motes' (dust), 'pollen', 'snow', 'embers', null (none).
     Lamp cones: soft additive cones under the 32 nearest downward-facing lamp emitters, one instanced draw. */
  var DUST = { wind: { n: 1, col: [1.0, 0.92, 0.80], size: 0.05, fall: 0.02, drift: 0.35 }, beams: { n: 0.8, col: [1.0, 0.95, 0.85], size: 0.04, fall: 0.01, drift: 0.08 },
    heavy: { n: 1, col: [0.95, 0.92, 0.88], size: 0.045, fall: 0.02, drift: 0.06 }, motes: { n: 0.7, col: [1.0, 0.94, 0.80], size: 0.035, fall: 0.005, drift: 0.05 },
    pollen: { n: 0.6, col: [1.0, 0.97, 0.75], size: 0.05, fall: 0.03, drift: 0.25 }, snow: { n: 1.2, col: [1.0, 1.0, 1.0], size: 0.08, fall: 0.7, drift: 0.3 },
    embers: { n: 0.5, col: [1.0, 0.55, 0.2], size: 0.06, fall: -0.4, drift: 0.2 } };
  var X = { dust: null, cones: null, kind: null, t: 0 }, BOX = 14;
  Atmo.extras = X;   // tests (look-readability.js hides the dust)
  function dustMat() {
    return new THREE.ShaderMaterial({
      uniforms: { uCol: { value: new THREE.Vector3(1, 1, 1) }, uSize: { value: 0.05 }, uScale: { value: 400 }, uCam: { value: new THREE.Vector3() }, uT: { value: 0 }, uFall: { value: 0 }, uDrift: { value: 0 } },
      vertexShader: [
        'uniform float uSize, uScale, uT, uFall, uDrift; uniform vec3 uCam; attribute float aSeed; varying float vA;',
        'void main() {',
        '  vec3 p = position + vec3( sin( uT * 0.3 + aSeed * 6.28 ) * uDrift * 2.0 + uT * uDrift, -uT * uFall, cos( uT * 0.23 + aSeed * 4.1 ) * uDrift * 2.0 );',
        '  p = uCam + mod( p - uCam + ' + (BOX / 2).toFixed(1) + ', ' + BOX.toFixed(1) + ' ) - ' + (BOX / 2).toFixed(1) + ';',
        '  vec4 mv = modelViewMatrix * vec4( p, 1.0 );',
        '  float d = -mv.z; vA = smoothstep( 0.4, 1.5, d ) * ( 1.0 - smoothstep( 5.0, 7.0, d ) ) * ( 0.55 + 0.45 * sin( uT * 1.7 + aSeed * 40.0 ) );',
        '  gl_PointSize = uSize * uScale / max( d, 0.1 );',
        '  gl_Position = projectionMatrix * mv;',
        '}'].join('\n'),
      fragmentShader: 'uniform vec3 uCol; varying float vA; void main() { vec2 q = gl_PointCoord - 0.5; float a = smoothstep( 0.25, 0.0, dot( q, q ) ) * vA; if ( a < 0.01 ) discard; gl_FragColor = vec4( uCol * a, a ); }',
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false
    });
  }
  function coneMat() {
    return new THREE.ShaderMaterial({
      uniforms: { uI: { value: 0.18 } },
      vertexShader: 'attribute vec3 aCol; varying vec3 vCol; varying float vF; varying float vY; void main() { vCol = aCol; vY = uv.y;' +
        ' vec4 w = modelMatrix * instanceMatrix * vec4( position, 1.0 ); vec3 n = normalize( mat3( modelMatrix * instanceMatrix ) * normal );' +
        ' vec3 v = normalize( cameraPosition - w.xyz ); vF = pow( abs( dot( n, v ) ), 1.5 ); gl_Position = projectionMatrix * viewMatrix * w; }',
      fragmentShader: 'uniform float uI; varying vec3 vCol; varying float vF; varying float vY; void main() { float a = vF * smoothstep( 0.0, 0.35, vY ) * ( 0.25 + 0.75 * vY ) * uI; gl_FragColor = vec4( vCol * a, a ); }',
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false
    });
  }
  Atmo.beginExtras = function (level, L) {
    Atmo.endExtras();
    var R = IB.Render, T = IB.LOOKS.tier(R.tier);
    if (!IB.Look.on || T.dust <= 0) return;
    var theme = level.theme || {}, kind = L.dust;
    if (theme.id === 'mountains' || theme.id === 'arctic' || theme.id === 'seabase') kind = null;   // own snow / marine snow: do not double
    if (theme.id === 'foundry') kind = 'embers';
    X.kind = kind;
    if (kind && DUST[kind] && T.dust >= 1) {
      var D = DUST[kind], n = Math.round((R.tier === 'high' ? 400 : 150) * D.n), pos = new Float32Array(n * 3), seed = new Float32Array(n);
      for (var i = 0; i < n; i++) { pos[i * 3] = Math.random() * BOX; pos[i * 3 + 1] = Math.random() * BOX; pos[i * 3 + 2] = Math.random() * BOX; seed[i] = Math.random(); }
      var g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('aSeed', new THREE.BufferAttribute(seed, 1));
      var m = dustMat(); m.uniforms.uSize.value = D.size; m.uniforms.uFall.value = D.fall; m.uniforms.uDrift.value = D.drift;
      X.dust = new THREE.Points(g, m); X.dust.frustumCulled = false; X.dust.renderOrder = 8; X.dustDef = D;
      R.scene.add(X.dust);
    }
    // lamp cones from downward-facing lamp emitters
    var lights = (IB.LightGrid && IB.LightGrid.lights()) || [], down = lights.filter(function (l) { return l.ny < -0.6 && l.lamp > 0.3 && l.s > 0.25; });
    if (down.length && T.dust >= 1) {
      var cg = new THREE.CylinderGeometry(0.12, 1, 1, 16, 1, true); cg.translate(0, -0.5, 0);   // apex at the lamp, unit height downward
      var uv = cg.attributes.uv; for (var k = 0; k < uv.count; k++) uv.setY(k, uv.getY(k));   // uv.y: 1 at the lamp, 0 at the floor
      var N = 32, im = new THREE.InstancedMesh(cg, coneMat(), N), col = new Float32Array(N * 3);
      cg.setAttribute('aCol', new THREE.InstancedBufferAttribute(col, 3));
      im.frustumCulled = false; im.renderOrder = 7; im.count = 0;
      X.cones = { mesh: im, list: down, col: col, last: -1 };
      R.scene.add(im);
    }
  };
  var _m4 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _s = new THREE.Vector3();
  Atmo.updateExtras = function (dt, vmk) {
    if (!X.dust && !X.cones) return;
    var R = IB.Render, c = R.camera.position;
    X.t += dt;
    if (X.dust) {
      var u = X.dust.material.uniforms, D = X.dustDef, k = Math.min(1.2, 0.15 + (vmk || 0.5)) * 0.55;
      u.uT.value = X.t; u.uCam.value.copy(c); u.uScale.value = R.height * R.pixelRatio * 0.6;
      u.uCol.value.set(D.col[0] * k, D.col[1] * k, D.col[2] * k);
    }
    if (X.cones && (X.t - X.cones.last > 0.5)) {   // re-pick the 32 nearest lamps twice a second
      X.cones.last = X.t;
      var C = X.cones, world = IB.Game.level && IB.Game.level.world, list = C.list.slice().sort(function (a, b) { return ((a.x - c.x) * (a.x - c.x) + (a.z - c.z) * (a.z - c.z)) - ((b.x - c.x) * (b.x - c.x) + (b.z - c.z) * (b.z - c.z)); });
      var n = Math.min(32, list.length);
      for (var i = 0; i < n; i++) {
        var L = list[i], fy = world ? world.floorAt(L.x, L.z, L.y - 0.2) : 0, h = Math.max(0.5, Math.min(12, L.y - (fy || 0)));
        _p.set(L.x, L.y, L.z); _s.set(h * 0.45, h, h * 0.45); _m4.compose(_p, _q, _s); C.mesh.setMatrixAt(i, _m4);
        var g = Math.min(1, L.s / 1.5); C.col[i * 3] = L.r * g; C.col[i * 3 + 1] = L.g * g; C.col[i * 3 + 2] = L.b * g;
      }
      C.mesh.count = n; C.mesh.instanceMatrix.needsUpdate = true; C.mesh.geometry.attributes.aCol.needsUpdate = true;
    }
  };
  Atmo.endExtras = function () {
    var R = IB.Render;
    if (X.dust) { R.scene.remove(X.dust); X.dust.geometry.dispose(); X.dust.material.dispose(); X.dust = null; }
    if (X.cones) { R.scene.remove(X.cones.mesh); X.cones.mesh.geometry.dispose(); X.cones.mesh.material.dispose(); X.cones = null; }
    X.t = 0;
  };
})(window.IB = window.IB || {});
