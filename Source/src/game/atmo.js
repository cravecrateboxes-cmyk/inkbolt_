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
})(window.IB = window.IB || {});
