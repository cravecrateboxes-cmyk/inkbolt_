/* INKBOLT look prototype (throwaway): injected into the built page by proto-shots.js. Nothing in the repo changes.
   window.IBLook.apply(cfg) patches the live materials: surface lighting + detail, sun shadow map, height fog,
   thinner ink, smooth sky, post pass (bloom, grade, vignette, grain). cfg: see DEFAULTS. */
(function () {
  'use strict';
  var L = window.IBLook = {};
  var DEFAULTS = {
    sunI: 2.6, sunColor: null, ambSky: [0.55, 0.66, 0.85], ambGround: [0.34, 0.30, 0.27], ambI: 0.62,
    albSat: 0.72, albGain: 0.86, fogDens: 0.006, fogHK: 0.045, fogH0: 2.0, fogMax: 0.92, fogColor: null, sunFog: [1.0, 0.86, 0.66],
    detail: 1.0, ink: '#0C0B10', outPx: 1.5, outBase: 0.0045, shadow: 4096, shadowSpan: 75,
    bloom: 0.55, bloomThr: 0.86, sat: 0.94, contrast: 0.22, vignette: 0.42, grain: 0.035, tintLo: [0.96, 1.0, 1.06], tintHi: [1.05, 1.0, 0.94],
    grid: false, gridI: 1.0, indoorAmb: 0.22, wet: 0.0, exposure: 1.0
  };

  // ---------------- surface classes from palette cell names ----------------
  // returns [gloss, metal, cls 0..7, emissive]
  function classify(n) {
    var s = n.toLowerCase();
    if (/^(hull|ink)$/.test(s)) return [0.2, 0, 7, 0];
    if (/^(lamp|light|glow|neon|scr|screen|fire|beacon|led|holo|lava|ember|bulb|flame|exitg|sign.?lit|laser|spark|arc|plasma)/.test(s)) return [0.3, 0, 0, 1];
    if (/glass|lens|visor|crystal|gem|ice|pool|water|mirror/.test(s)) return [0.9, 0.1, 6, 0];
    if (/rust/.test(s)) return [0.12, 0.5, 2, 0];
    if (/steel|iron|metal|chrome|galv|alu|brass|gold|copper|bronze|tin\b|gun|plate|rail|pipe|silver|zinc|wire|chain|mesh|grat|girder|truss/.test(s)) return [0.55, 0.85, 2, 0];
    if (/conc|stone|rock|cave|brick|tile|marble|slate|cement|plaster|asph|gravel|granite|cobble|pav|stucco|slab|kerb|curb|mortar|cliff|boulder/.test(s)) return [0.10, 0, 1, 0];
    if (/wood|plank|oak|walnut|crate|bark|trunk|log|timber|board|pine|bamboo|beam|ply/.test(s)) return [0.16, 0, 3, 0];
    if (/bag|canvas|tarp|cloth|blanket|linen|curtain|carpet|rope|fabric|flag|leather|cushion|sofa|felt|thatch|net|wool|towel|uphol/.test(s)) return [0.04, 0, 4, 0];
    if (/soil|sand|snow|grass|dirt|mud|leaf|moss|hedge|foliage|turf|earth|dust|fern|bush|needle|canopy|ground/.test(s)) return [0.03, 0, 5, 0];
    if (/tire|tyre|rubber|black|cable|hose/.test(s)) return [0.22, 0, 7, 0];
    return [0.30, 0.05, 0, 0];   // painted / plastic
  }
  function surfTexture(names) {
    var px = new Uint8Array(64 * 4);
    for (var i = 0; i < 64; i++) {
      var v = names[i] ? classify(names[i]) : [0.3, 0, 0, 0], o = ((7 - (i >> 3)) * 8 + (i & 7)) * 4;
      px[o] = Math.round(v[0] * 255); px[o + 1] = Math.round(v[1] * 255); px[o + 2] = Math.round(v[2] / 7 * 255); px[o + 3] = v[3] ? 255 : 0;
    }
    var t = new THREE.DataTexture(px, 8, 8, THREE.RGBAFormat);
    t.encoding = THREE.LinearEncoding; t.magFilter = t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.flipY = false; t.needsUpdate = true;
    return t;
  }

  // ---------------- shader pieces ----------------
  var PARS = [
    'varying vec3 vWP;',
    'uniform sampler2D uSurf; uniform vec4 uSurfFlat; uniform sampler2D uGrid; uniform vec4 uGridR; uniform float uGridI;',
    'uniform vec3 uAmbSky, uAmbGround, uSunFog; uniform float uSunI, uAmbI, uAlbSat, uAlbGain, uDetail, uFogDens, uFogHK, uFogH0, uFogMax, uWet, uIndoor;',
    'uniform vec3 uSunDirW;',
    'float ibH3( vec3 p ) { return fract( sin( dot( p, vec3( 127.1, 311.7, 74.7 ) ) ) * 43758.5453 ); }',
    'float ibN3( vec3 p ) { vec3 i = floor( p ), f = fract( p ); f = f * f * ( 3.0 - 2.0 * f );',
    '  return mix( mix( mix( ibH3( i ), ibH3( i + vec3( 1, 0, 0 ) ), f.x ), mix( ibH3( i + vec3( 0, 1, 0 ) ), ibH3( i + vec3( 1, 1, 0 ) ), f.x ), f.y ),',
    '    mix( mix( ibH3( i + vec3( 0, 0, 1 ) ), ibH3( i + vec3( 1, 0, 1 ) ), f.x ), mix( ibH3( i + vec3( 0, 1, 1 ) ), ibH3( i + vec3( 1, 1, 1 ) ), f.x ), f.y ), f.z ); }',
    'float ibFbm( vec3 p ) { return ibN3( p ) * 0.5 + ibN3( p * 2.03 + 7.1 ) * 0.3 + ibN3( p * 4.1 + 13.7 ) * 0.2; }',
    'vec3 ibBump( vec3 N, float h, float amt ) {',
    '  vec3 dpdx = dFdx( -vViewPosition ), dpdy = dFdy( -vViewPosition ); float dhx = dFdx( h ), dhy = dFdy( h );',
    '  vec3 r1 = cross( dpdy, N ), r2 = cross( N, dpdx ); float det = dot( dpdx, r1 );',
    '  vec3 g = sign( det ) * ( dhx * r1 + dhy * r2 ); return normalize( abs( det ) * N - amt * g ); }'
  ].join('\n');

  var LIGHT = [
    '#ifdef USE_MAP',
    '  vec4 ibS = texture2D( uSurf, vUv ); vec3 ibAlb = diffuseColor.rgb / max( vColor.rgb, vec3( 0.001 ) ); float ibAO = vColor.r;',
    '#else',
    '  vec4 ibS = uSurfFlat; vec3 ibAlb = diffuseColor.rgb; float ibAO = 1.0;',
    '#endif',
    'float ibCls = floor( ibS.b * 7.0 + 0.5 );',
    'vec3 ibNv = normalize( normal ); vec3 ibV = normalize( vViewPosition );',
    'float ibDist = length( vViewPosition ); float ibNear = 1.0 - smoothstep( 6.0, 26.0, ibDist ); float ibMid = 1.0 - smoothstep( 30.0, 90.0, ibDist );',
    // ---- detail: grain, macro blotches, streaks; per class
    'float ibFine = ibFbm( vWP * ( ibCls == 2.0 ? vec3( 70.0, 9.0, 70.0 ) : ibCls == 3.0 ? vec3( 6.0, 60.0, 60.0 ) : vec3( 13.0 ) ) );',
    'float ibMed = ibFbm( vWP * 3.1 + 11.0 ); float ibMacro = ibN3( vWP * 0.33 + 3.0 ) * 0.6 + ibN3( vWP * 0.93 ) * 0.4;',
    'float ibRough = ibCls == 1.0 ? 1.0 : ibCls == 5.0 ? 1.2 : ibCls == 4.0 ? 0.8 : ibCls == 3.0 ? 0.7 : ibCls == 2.0 ? 0.35 : 0.3;',
    'vec3 ibNw0 = inverseTransformDirection( ibNv, viewMatrix );',
    // dirt gathers low on walls and in baked AO; streaks run down vertical faces
    'float ibWall = 1.0 - abs( ibNw0.y );',
    'float ibStreak = ibN3( vec3( vWP.x * 5.0 + vWP.z * 5.0, vWP.y * 0.35, 1.7 ) ) * ibN3( vWP * 1.3 + 4.0 );',
    'float ibGrime = clamp( ( 1.0 - ibAO ) * 2.6 + ibWall * smoothstep( 1.3, 0.0, vWP.y ) * 0.55 + ibWall * smoothstep( 0.45, 0.75, ibStreak ) * 0.45 + smoothstep( 0.55, 0.9, ibMed ) * 0.3, 0.0, 1.0 ) * uDetail;',
    // slab joints on upward concrete / generic floors
    'float ibJoint = 0.0;',
    'if ( ibNw0.y > 0.9 && ( ibCls == 1.0 || ibCls == 0.0 ) ) { vec2 q = abs( fract( vWP.xz / 3.0 ) - 0.5 ); float e = min( q.x, q.y ) * 3.0; ibJoint = ( 1.0 - smoothstep( 0.0, 0.018, e ) ) * ibMid; }',
    'float ibEm = ibS.a;',
    'vec3 ibA = ibAlb;',
    'float ibLum = dot( ibA, vec3( 0.2126, 0.7152, 0.0722 ) );',
    'ibA = mix( vec3( ibLum ), ibA, mix( uAlbSat, 1.0, ibEm ) ) * mix( uAlbGain, 1.0, ibEm );',
    'ibA *= 1.0 + ( ibMacro - 0.5 ) * 0.22 * ibRough * uDetail + ( ibFine - 0.5 ) * 0.13 * ibRough * ibNear * uDetail;',
    'ibA *= 1.0 - ibGrime * 0.42 * ( 0.4 + 0.6 * ibMid ); ibA = mix( ibA, ibA * vec3( 0.80, 0.74, 0.66 ), ibGrime * 0.5 );',
    'ibA *= 1.0 - ibJoint * 0.55;',
    'vec3 ibAL = pow( max( ibA, vec3( 0.0 ) ), vec3( 2.2 ) );',
    // bumped normal from the fine + medium height
    'vec3 ibNb = ibBump( ibNv, ( ibFine * 0.012 + ibMed * 0.02 ) * ibRough + ibJoint * -0.02, 1.0 * ibNear * uDetail );',
    'vec3 ibNw = inverseTransformDirection( ibNb, viewMatrix );',
    // ---- light
    '#if NUM_DIR_LIGHTS > 0',
    '  vec3 ibL = directionalLights[ 0 ].direction; vec3 ibLC = directionalLights[ 0 ].color;',
    '#else',
    '  vec3 ibL = vec3( 0.0, 1.0, 0.0 ); vec3 ibLC = vec3( 0.0 );',
    '#endif',
    'float ibSh = 1.0;',
    '#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0',
    '  ibSh = receiveShadow ? getShadow( directionalShadowMap[ 0 ], directionalLightShadows[ 0 ].shadowMapSize, directionalLightShadows[ 0 ].shadowBias, directionalLightShadows[ 0 ].shadowRadius, vDirectionalShadowCoord[ 0 ] ) : 1.0;',
    '#endif',
    'float ibNL = max( dot( ibNb, ibL ), 0.0 );',
    'float ibHem = ibNw.y * 0.5 + 0.5;',
    'float ibAO2 = mix( 0.42, 1.0, smoothstep( 0.8, 1.0, ibAO ) );',
    'vec3 ibAmb = mix( uAmbGround, uAmbSky, ibHem ) * uAmbI * ibAO2;',
    'vec3 ibGridL = vec3( 0.0 );',
    'if ( uGridI > 0.0 ) { vec2 guv = ( vWP.xz - uGridR.xy ) * uGridR.zw; ibGridL = texture2D( uGrid, guv ).rgb * uGridI * mix( 0.5, 1.0, ibHem ) * ibAO2; }',
    'vec3 ibSun = ibLC * uSunI * ibNL * ibSh * ( 1.0 - uIndoor );',
    'vec3 ibCol = ibAL * ( ibSun + ibAmb + ibGridL );',
    // specular: sun (Blinn-Phong) + sky / lamp sheen at grazing angles
    'float ibGloss = clamp( ibS.r * ( 1.0 - ibGrime * 0.6 ) * ( 0.75 + 0.5 * ibFine ) + uWet * step( 0.9, ibNw0.y ) * smoothstep( 0.45, 0.7, ibMacro ) * 0.8, 0.0, 1.0 );',
    'vec3 ibSpecC = mix( vec3( 0.04 ), ibAL, ibS.g );',
    'float ibNH = max( dot( ibNb, normalize( ibL + ibV ) ), 0.0 );',
    'float ibPow = mix( 6.0, 180.0, ibGloss * ibGloss );',
    'ibCol += ibSpecC * pow( ibNH, ibPow ) * ( ibPow + 8.0 ) / 25.0 * ibLC * uSunI * ibSh * ibNL * ( 1.0 - uIndoor ) * 4.0 * ( 0.15 + ibGloss );',
    'float ibFr = pow( 1.0 - max( dot( ibNb, ibV ), 0.0 ), 5.0 );',
    'vec3 ibRefl = mix( uAmbGround, uAmbSky, clamp( reflect( -normalize( inverseTransformDirection( ibV, viewMatrix ) ), ibNw ).y * 0.5 + 0.5, 0.0, 1.0 ) ) * uAmbI + ibGridL * 0.6;',
    'ibCol += ibRefl * ( ibSpecC + ( 1.0 - ibSpecC ) * ibFr ) * ibGloss * ibGloss * 1.4 * ibAO2;',
    'ibCol = pow( max( ibCol, vec3( 0.0 ) ), vec3( 1.0 / 2.2 ) );',
    'ibCol = mix( ibCol, ibAlb * 1.75, ibEm );',
    'vec3 outgoingLight = ibCol + totalEmissiveRadiance;'
  ].join('\n');

  var FOG = [
    '#ifdef USE_FOG',
    '  float ibFd = fogDepth;',
    '  float ibDens = uFogDens * exp( -max( vWP.y - uFogH0, 0.0 ) * uFogHK );',
    '  float ibFf = ( 1.0 - exp( -ibFd * ibDens ) ) * uFogMax;',
    '  ibFf = max( ibFf, smoothstep( fogFar * 0.72, fogFar, ibFd ) );',
    '  vec3 ibVdW = normalize( vWP - cameraPosition );',
    '  vec3 ibFc = mix( fogColor, uSunFog, pow( max( dot( ibVdW, uSunDirW ), 0.0 ), 6.0 ) * 0.55 * ( 1.0 - uIndoor ) );',
    '  gl_FragColor.rgb = mix( gl_FragColor.rgb, ibFc, ibFf );',
    '#endif'
  ].join('\n');

  var U = null;
  function uniforms(c) {
    U = {
      uAmbSky: { value: new THREE.Vector3().fromArray(c.ambSky) }, uAmbGround: { value: new THREE.Vector3().fromArray(c.ambGround) },
      uSunFog: { value: new THREE.Vector3().fromArray(c.sunFog) }, uSunI: { value: c.sunI }, uAmbI: { value: c.ambI },
      uAlbSat: { value: c.albSat }, uAlbGain: { value: c.albGain }, uDetail: { value: c.detail },
      uFogDens: { value: c.fogDens }, uFogHK: { value: c.fogHK }, uFogH0: { value: c.fogH0 }, uFogMax: { value: c.fogMax },
      uWet: { value: c.wet }, uIndoor: { value: 0 }, uSunDirW: { value: new THREE.Vector3(0, 1, 0) },
      uGrid: { value: null }, uGridR: { value: new THREE.Vector4(0, 0, 1, 1) }, uGridI: { value: 0 }
    };
  }
  function patch(mat, id, surf, flat) {
    if (!mat || mat.userData.look) return;
    var inner = mat.onBeforeCompile, key0 = mat.customProgramCacheKey;
    mat.onBeforeCompile = function (sh, r) {
      if (inner) inner.call(mat, sh, r);
      for (var k in U) sh.uniforms[k] = U[k];
      sh.uniforms.uSurf = { value: surf }; sh.uniforms.uSurfFlat = { value: flat || new THREE.Vector4(0.16, 0, 1 / 7, 0) };
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWP;')
        .replace('max( 0.0, min( uOutMax, max( uOutBase, uOutK * -mvPosition.z ) * uHullK ) - uBaked )', '( max( min( uOutMax, max( uOutBase, uOutK * -mvPosition.z ) * uHullK ), 0.001 ) - uBaked )')
        .replace('vHull = 0.0;', 'vHull = 0.0;\n{ vec4 ibW = vec4( transformed, 1.0 );\n#ifdef USE_INSTANCING\n ibW = instanceMatrix * ibW;\n#endif\n vWP = ( modelMatrix * ibW ).xyz; }');
      sh.fragmentShader = sh.fragmentShader.replace('#include <shadowmap_pars_fragment>', '#include <shadowmap_pars_fragment>\n' + PARS)
        .replace('vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;', LIGHT)
        .replace('#include <fog_fragment>', FOG);
    };
    mat.customProgramCacheKey = function () { return (key0 ? key0.call(mat) : '') + 'look' + id; };
    mat.userData.look = true; mat.needsUpdate = true;
  }

  // ---------------- sun shadow (static, rendered once per call) ----------------
  function depthMat() {
    var m = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
    m.onBeforeCompile = function (sh) {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec3 aHull;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nif ( dot( aHull, aHull ) > 0.0 ) gl_Position = vec4( 2.0, 2.0, 2.0, 1.0 );');   // the ink shell casts nothing
    };
    return m;
  }
  L.shadowFit = function (zi, c) {
    var R = IB.Render, G = IB.Game, z = G.level.zones[zi], sun = R.sun;
    var dir = (L.sunDir || (L.sunDir = sun.position.clone().normalize()));
    var cx = z.ox + z.w / 2, cz = z.oz + z.h / 2, span = c.shadowSpan;
    sun.target.position.set(cx, 0, cz); R.scene.add(sun.target); sun.target.updateMatrixWorld();
    sun.position.set(cx + dir.x * 220, dir.y * 220, cz + dir.z * 220); sun.updateMatrixWorld();
    var cam = sun.shadow.camera; cam.left = -span; cam.right = span; cam.top = span; cam.bottom = -span; cam.near = 1; cam.far = 520; cam.updateProjectionMatrix();
    U.uSunDirW.value.copy(dir);
    R.renderer.shadowMap.needsUpdate = true;
  };
  function shadows(c) {
    var R = IB.Render, r = R.renderer, sun = R.sun;
    r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap; r.shadowMap.autoUpdate = false;
    sun.castShadow = true; sun.shadow.mapSize.set(c.shadow, c.shadow); sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.03; sun.shadow.radius = 2.2;
    var dm = depthMat();
    IB.Game.level.root.traverse(function (o) {
      if (!(o.isMesh || o.isInstancedMesh)) return;
      var m = o.material;
      if (!m || !m.isMeshToonMaterial || m.transparent) return;
      o.receiveShadow = true;
      if (o.geometry && o.geometry.attributes.aHull && m !== IB.Zones.cloudMat) { o.castShadow = true; o.customDepthMaterial = dm; }
    });
  }

  // ---------------- local light grid from emissive faces (indoor) ----------------
  L.buildGrid = function (zi, c) {
    var G = IB.Game, level = G.level, z = level.zones[zi], A = IB.Assets, world = level.world;
    var ems = new Map(), CELL = 1.6;
    z.meshes.forEach(function (mesh) {
      var fam = null; Object.keys(A.mat).forEach(function (f) { if (A.mat[f] === mesh.material) fam = f; });
      var names = L.pal[fam]; if (!names) return;
      var em = names.map(function (n) { return classify(n[0])[3] ? n : null; });
      var g = mesh.geometry, pos = g.attributes.position.array, uv = g.attributes.uv.array, idx = g.index.array;
      for (var t = 0; t < idx.length; t += 3) {
        var i0 = idx[t], cell = Math.floor(uv[i0 * 2] * 8) + 8 * Math.floor((1 - uv[i0 * 2 + 1]) * 8), e = em[cell];
        if (!e) continue;
        var i1 = idx[t + 1], i2 = idx[t + 2];
        var ax = pos[i0 * 3], ay = pos[i0 * 3 + 1], az = pos[i0 * 3 + 2], bx = pos[i1 * 3] - ax, by = pos[i1 * 3 + 1] - ay, bz = pos[i1 * 3 + 2] - az, cx = pos[i2 * 3] - ax, cy = pos[i2 * 3 + 1] - ay, cz = pos[i2 * 3 + 2] - az;
        var nx = by * cz - bz * cy, ny = bz * cx - bx * cz, nz = bx * cy - by * cx, area = Math.sqrt(nx * nx + ny * ny + nz * nz) / 2;
        if (area < 1e-5) continue;
        var mx = ax + (bx + cx) / 3, my = ay + (by + cy) / 3, mz = az + (bz + cz) / 3;
        var key = Math.floor(mx / CELL) + ',' + Math.floor(my / CELL) + ',' + Math.floor(mz / CELL), E = ems.get(key);
        if (!E) { E = { x: 0, y: 0, z: 0, a: 0, r: 0, g: 0, b: 0 }; ems.set(key, E); }
        var col = new THREE.Color(e[1]);
        E.x += mx * area; E.y += my * area; E.z += mz * area; E.a += area; E.r += col.r * area; E.g += col.g * area; E.b += col.b * area;
      }
    });
    var lights = [];
    ems.forEach(function (E) { if (E.a < 0.01) return; lights.push({ x: E.x / E.a, y: E.y / E.a, z: E.z / E.a, a: E.a, r: E.r / E.a, g: E.g / E.a, b: E.b / E.a }); });
    var RES = 1, W = Math.ceil(z.w / RES) + 4, H = Math.ceil(z.h / RES) + 4, ox = z.ox - 2, oz = z.oz - 2, data = new Float32Array(W * H * 4);
    var RAD = 13;
    for (var j = 0; j < H; j++) for (var i = 0; i < W; i++) {
      var px = ox + (i + 0.5) * RES, pz = oz + (j + 0.5) * RES, r = 0, g = 0, b = 0;
      for (var k = 0; k < lights.length; k++) {
        var Lt = lights[k], dx = Lt.x - px, dz = Lt.z - pz, d2 = dx * dx + dz * dz;
        if (d2 > RAD * RAD) continue;
        var dy = Math.max(0.6, Lt.y - 1.0), dd = d2 + dy * dy;
        var I = Math.min(2.2, Lt.a * 2.4) * 9.0 / (1.0 + dd) * Math.max(0, 1 - Math.sqrt(d2) / RAD);
        if (I < 0.004) continue;
        if (!world.los(px, 1.0, pz, Lt.x, Math.max(1.2, Lt.y - 0.25), Lt.z)) I *= 0.12;
        r += Lt.r * I; g += Lt.g * I; b += Lt.b * I;
      }
      var o = (j * W + i) * 4; data[o] = r; data[o + 1] = g; data[o + 2] = b; data[o + 3] = 1;
    }
    // 3x3 blur
    var out = new Float32Array(data.length);
    for (j = 0; j < H; j++) for (i = 0; i < W; i++) for (var ch = 0; ch < 3; ch++) {
      var s = 0, n = 0;
      for (var dj = -1; dj <= 1; dj++) for (var di = -1; di <= 1; di++) { var ii = i + di, jj = j + dj; if (ii < 0 || jj < 0 || ii >= W || jj >= H) continue; var wgt = (di === 0 && dj === 0) ? 2 : 1; s += data[(jj * W + ii) * 4 + ch] * wgt; n += wgt; }
      out[(j * W + i) * 4 + ch] = s / n;
    }
    var tex = new THREE.DataTexture(out, W, H, THREE.RGBAFormat, THREE.FloatType);
    tex.magFilter = tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false; tex.flipY = false; tex.needsUpdate = true;
    U.uGrid.value = tex; U.uGridR.value.set(ox, oz, 1 / (W * RES), 1 / (H * RES)); U.uGridI.value = c.gridI;
    return { lights: lights.length, w: W, h: H };
  };

  // ---------------- sky ----------------
  function sky(c) {
    var R = IB.Render, m = R.sky.material;
    m.uniforms.uSunDir = { value: (L.sunDir || R.sun.position.clone().normalize()) }; m.uniforms.uSunC = { value: new THREE.Vector3().fromArray(c.sunFog) };
    m.vertexShader = 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }';
    m.fragmentShader = ['uniform vec3 top; uniform vec3 horizon; uniform float uCloak; uniform vec3 uSunDir; uniform vec3 uSunC; varying vec3 vD;',
      'float h3( vec3 p ) { return fract( sin( dot( p, vec3( 127.1, 311.7, 74.7 ) ) ) * 43758.5453 ); }',
      'float n3( vec3 p ) { vec3 i = floor( p ), f = fract( p ); f = f * f * ( 3.0 - 2.0 * f ); return mix( mix( mix( h3( i ), h3( i + vec3( 1, 0, 0 ) ), f.x ), mix( h3( i + vec3( 0, 1, 0 ) ), h3( i + vec3( 1, 1, 0 ) ), f.x ), f.y ), mix( mix( h3( i + vec3( 0, 0, 1 ) ), h3( i + vec3( 1, 0, 1 ) ), f.x ), mix( h3( i + vec3( 0, 1, 1 ) ), h3( i + vec3( 1, 1, 1 ) ), f.x ), f.y ), f.z ); }',
      'void main(){ vec3 d = normalize( vD ); float t = pow( smoothstep( -0.02, 0.62, d.y ), 0.62 );',
      '  vec3 c = mix( horizon * 0.96, top * 0.82, t );',
      '  float s = max( dot( d, normalize( uSunDir ) ), 0.0 ); c += uSunC * ( pow( s, 420.0 ) * 2.4 + pow( s, 14.0 ) * 0.30 + pow( s, 3.0 ) * 0.10 );',
      '  vec2 q = d.xz / max( d.y + 0.12, 0.05 ); float cl = n3( vec3( q * 1.3, 1.0 ) ) * 0.55 + n3( vec3( q * 3.1, 4.0 ) ) * 0.3 + n3( vec3( q * 7.0, 9.0 ) ) * 0.15;',
      '  float cm = smoothstep( 0.52, 0.78, cl ) * smoothstep( 0.0, 0.22, d.y ); c = mix( c, mix( horizon, vec3( 1.0 ), 0.55 ) * ( 0.82 + 0.3 * s ), cm * 0.75 );',
      '  float l = dot( c, vec3( 0.299, 0.587, 0.114 ) ); gl_FragColor = vec4( mix( c, vec3( l * 0.32 + 0.03 ), uCloak ), 1.0 ); }'].join('\n');
    m.needsUpdate = true;
  }

  // ---------------- post ----------------
  var FSQ_V = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4( position.xy, 0.0, 1.0 ); }';
  function pass(frag, uni) { var m = new THREE.ShaderMaterial({ vertexShader: FSQ_V, fragmentShader: frag, uniforms: uni, depthTest: false, depthWrite: false }); return m; }
  function post(c) {
    var R = IB.Render, r = R.renderer, P = L.post = {};
    var sz = new THREE.Vector2(); r.getDrawingBufferSize(sz);
    var w = sz.x, h = sz.y;
    var ms = r.capabilities.isWebGL2 && THREE.WebGLMultisampleRenderTarget;
    var opt = { minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, format: THREE.RGBAFormat, type: THREE.HalfFloatType, depthBuffer: true };
    P.rt = ms ? new THREE.WebGLMultisampleRenderTarget(w, h, opt) : new THREE.WebGLRenderTarget(w, h, opt);
    if (ms) P.rt.samples = 4;
    var o2 = { minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, format: THREE.RGBAFormat, type: THREE.HalfFloatType, depthBuffer: false };
    P.b0 = new THREE.WebGLRenderTarget(w >> 1, h >> 1, o2); P.b1 = new THREE.WebGLRenderTarget(w >> 2, h >> 2, o2); P.b2 = new THREE.WebGLRenderTarget(w >> 2, h >> 2, o2);
    P.b3 = new THREE.WebGLRenderTarget(w >> 3, h >> 3, o2); P.b4 = new THREE.WebGLRenderTarget(w >> 3, h >> 3, o2);
    P.scene = new THREE.Scene(); P.cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    P.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), null); P.quad.frustumCulled = false; P.scene.add(P.quad);
    P.pre = pass('uniform sampler2D t; uniform float thr; varying vec2 vUv; void main(){ vec3 c = texture2D( t, vUv ).rgb; float l = max( c.r, max( c.g, c.b ) ); gl_FragColor = vec4( c * smoothstep( thr, thr + 0.35, l ), 1.0 ); }', { t: { value: null }, thr: { value: c.bloomThr } });
    var BL = 'uniform sampler2D t; uniform vec2 d; varying vec2 vUv; void main(){ vec3 c = texture2D( t, vUv ).rgb * 0.227; c += ( texture2D( t, vUv + d * 1.385 ).rgb + texture2D( t, vUv - d * 1.385 ).rgb ) * 0.316; c += ( texture2D( t, vUv + d * 3.231 ).rgb + texture2D( t, vUv - d * 3.231 ).rgb ) * 0.0703; gl_FragColor = vec4( c, 1.0 ); }';
    P.blur = pass(BL, { t: { value: null }, d: { value: new THREE.Vector2() } });
    P.comp = pass(['uniform sampler2D t, b1, b2; uniform float bloom, sat, contrast, vig, grain, time, expo; uniform vec3 lo, hi; uniform vec2 res; varying vec2 vUv;',
      'float h2( vec2 p ) { return fract( sin( dot( p, vec2( 12.9898, 78.233 ) ) ) * 43758.5453 ); }',
      'void main(){ vec3 c = texture2D( t, vUv ).rgb * expo;',
      '  c += ( texture2D( b1, vUv ).rgb * 0.6 + texture2D( b2, vUv ).rgb * 0.4 ) * bloom;',
      '  float l = dot( c, vec3( 0.2126, 0.7152, 0.0722 ) ); c = mix( vec3( l ), c, sat );',
      '  c *= mix( lo, hi, smoothstep( 0.05, 0.85, l ) );',
      '  vec3 k = clamp( c, 0.0, 1.0 ); c = mix( c, k * k * ( 3.0 - 2.0 * k ) + max( c - 1.0, 0.0 ), contrast );',
      '  c = c / ( 1.0 + max( c - 0.82, 0.0 ) * 0.9 );',   // soft shoulder for the over-bright
      '  vec2 q = vUv - 0.5; c *= 1.0 - vig * smoothstep( 0.28, 0.95, dot( q, q ) * 2.0 );',
      '  c += ( h2( vUv * res + time ) - 0.5 ) * grain;',
      '  gl_FragColor = vec4( c, 1.0 ); }'].join('\n'),
      { t: { value: null }, b1: { value: null }, b2: { value: null }, bloom: { value: c.bloom }, sat: { value: c.sat }, contrast: { value: c.contrast }, vig: { value: c.vignette }, grain: { value: c.grain },
        time: { value: 0 }, expo: { value: c.exposure }, lo: { value: new THREE.Vector3().fromArray(c.tintLo) }, hi: { value: new THREE.Vector3().fromArray(c.tintHi) }, res: { value: new THREE.Vector2(w, h) } });
    function run(mat, target) { P.quad.material = mat; r.setRenderTarget(target); r.render(P.scene, P.cam); }
    R.render = function (showViewmodel) {
      r.setRenderTarget(P.rt); r.clear(true, true, true);
      R.sky.position.copy(R.camera.position);
      r.render(R.scene, R.camera);
      if (showViewmodel) { r.clearDepth(); r.render(R.vmScene, R.vmCam); }
      P.pre.uniforms.t.value = P.rt.texture; run(P.pre, P.b0);
      P.blur.uniforms.t.value = P.b0.texture; P.blur.uniforms.d.value.set(1 / P.b1.width, 0); run(P.blur, P.b1);
      P.blur.uniforms.t.value = P.b1.texture; P.blur.uniforms.d.value.set(0, 1 / P.b1.height); run(P.blur, P.b2);
      P.blur.uniforms.t.value = P.b2.texture; P.blur.uniforms.d.value.set(1 / P.b3.width, 0); run(P.blur, P.b3);
      P.blur.uniforms.t.value = P.b3.texture; P.blur.uniforms.d.value.set(0, 1 / P.b3.height); run(P.blur, P.b4);
      P.comp.uniforms.t.value = P.rt.texture; P.comp.uniforms.b1.value = P.b2.texture; P.comp.uniforms.b2.value = P.b4.texture; P.comp.uniforms.time.value = (performance.now() % 1000) / 1000;
      run(P.comp, null);
    };
  }

  // ---------------- apply ----------------
  L.apply = function (cfg, pal) {
    var c = L.cfg = Object.assign({}, DEFAULTS, cfg || {}), R = IB.Render, A = IB.Assets, G = IB.Game, env = G.level.theme.env || {};
    L.pal = pal;   // family -> [[name, hex], ...]
    L.sunDir = R.sun.position.clone().normalize();
    uniforms(c);
    U.uIndoor.value = env.sky ? 0 : 1;
    if (!env.sky) U.uAmbI.value = c.indoorAmb;
    U.uSunDirW.value.copy(L.sunDir);
    Object.keys(A.mat).forEach(function (fam) { if (pal[fam]) patch(A.mat[fam], fam, surfTexture(pal[fam].map(function (n) { return n[0]; }))); });
    patch(IB.Zones.mat, 'ground', null, new THREE.Vector4(c.floorGloss !== undefined ? c.floorGloss : 0.14, 0, (c.floorCls !== undefined ? c.floorCls : 1) / 7, 0));
    // ink
    R.worldOutline.px = c.outPx; R.worldOutline.uOutBase.value = c.outBase; R.worldOutline.uInk.value.set(c.ink); R.robotOutline.uInk.value.set(c.ink); R.updateOutlineK();
    if (c.fogColor) R.scene.fog.color.set(c.fogColor);
    if (c.sunColor) R.sun.color.set(c.sunColor);
    (G.level.cloudMeshes || []).forEach(function (m) { m.visible = false; });
    if (env.sky) { shadows(c); L.shadowFit(G.zone || 0, c); sky(c); }
    if (c.post !== false) post(c);
    return { indoor: !env.sky, fams: Object.keys(A.mat).length };
  };
})();
