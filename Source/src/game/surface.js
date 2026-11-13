/* INKBOLT surface light model (tactical look, plan section 5.4). One implementation for every lit look material,
   inserted by render.js toonMaterial's own onBeforeCompile AFTER the ink outline patch and BEFORE any caller's
   chained patch (ai.js, trooperrig.js, projectiles.js, gunskins.js keep finding their anchors: trap T4).
   Anchors (exact strings of r128's toon shader):
     vertex   '#include <common>'                    varyings
              'vHull = 0.0;' (render.js VERT_PROJECT) world position, after the instance transform (trap T13)
     fragment '#include <shadowmap_pars_fragment>'   uniforms + functions here (vViewPosition is declared: trap T3)
              the outgoingLight line                  replaced by the light model
              '#include <fog_fragment>'               replaced by the shared fog + sun glow (order kept: ink, fog, cloak)
   Light maths is done in linear light on pow(albedo, 2.2); the result is written as display values with headroom
   above 1.0 (emissive cells, sun glints), so legacy unlit materials (display values) stay consistent. */
(function (IB) {
  'use strict';
  var S = IB.Surface = {};
  var OUTLINE_LINE = 'vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;';

  // 8x8 surface texture of a family: R gloss, G metal, B class / 15, A 255 for emissive cells.
  // Texel of cell i at ((7 - (i >> 3)) * 8 + (i & 7)), as gunskins.js surfTexture (palette UVs are glTF, flipY false).
  var cache = {};
  S.texFor = function (fam) {
    if (cache[fam]) return cache[fam];
    var T = IB.SURFACES && IB.SURFACES[fam], C = IB.SURFACE_CLASSES || [], px = new Uint8Array(64 * 4);
    for (var i = 0; i < 64; i++) {
      var c = T && i < T.cls.length ? T.cls[i] : 0, k = C[c] || { gloss: 0.3, metal: 0 }, o = ((7 - (i >> 3)) * 8 + (i & 7)) * 4;
      px[o] = Math.round(k.gloss * 255); px[o + 1] = Math.round(k.metal * 255); px[o + 2] = Math.round(c / 15 * 255); px[o + 3] = c === 15 ? 255 : 0;
    }
    var t = new THREE.DataTexture(px, 8, 8, THREE.RGBAFormat);
    t.encoding = THREE.LinearEncoding; t.magFilter = t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.flipY = false; t.needsUpdate = true;
    return (cache[fam] = t);
  };
  // flat surface vector for materials without a palette (code-built floors): gloss, metal, class / 15, emissive
  S.flat = function (cls, gloss) { return new THREE.Vector4(gloss, 0, cls / 15, 0); };

  var PARS = [
    'varying vec3 vWP;',
    'uniform sampler2D uSurf; uniform vec4 uSurfFlat;',
    'uniform vec3 uAmbSky, uAmbGround, uSunFog, uSunDirW;',
    'uniform float uSunI, uAmbI, uAmbFloor, uIndoorAmb, uAlbSat, uAlbGain, uAlbCeil, uIndoor, uEmBoost, uShEdge;',
    'uniform sampler2D uGrid; uniform vec4 uGridO; uniform vec4 uGridY; uniform float uGridI, uGridOn;',
    'uniform vec4 uFlashP[ 4 ]; uniform vec4 uFlashC[ 4 ];',
    'uniform float uGExpo, uGSat, uGCon; uniform vec3 uGLo, uGHi;',
    // light volume: a 2D atlas of Y slices (lightgrid.js), two bilinear fetches mixed across slices
    'vec4 ibGridAt( vec3 p ) {',
    '  float n = uGridY.z, f = clamp( ( p.y - uGridY.x ) / uGridY.y, 0.0, n - 1.0 ), s0 = floor( f ), s1 = min( s0 + 1.0, n - 1.0 );',
    '  float u = ( p.x - uGridO.x ) * uGridO.z, vz = clamp( ( p.z - uGridO.y ) * uGridO.w, uGridY.w, 1.0 - uGridY.w );',
    '  return mix( texture2D( uGrid, vec2( u, ( vz + s0 ) / n ) ), texture2D( uGrid, vec2( u, ( vz + s1 ) / n ) ), f - s0 );',
    '}',
    'float ibH2( vec2 p ) { return fract( sin( dot( p, vec2( 127.1, 311.7 ) ) ) * 43758.5453 ); }',
    'float ibN2( vec2 p ) { vec2 i = floor( p ), f = fract( p ); f = f * f * ( 3.0 - 2.0 * f );',
    '  return mix( mix( ibH2( i ), ibH2( i + vec2( 1.0, 0.0 ) ), f.x ), mix( ibH2( i + vec2( 0.0, 1.0 ) ), ibH2( i + vec2( 1.0, 1.0 ) ), f.x ), f.y ); }'
  ].join('\n');

  /* Detail (Stage 5): a texture array of tiling layers (tools/gen_detail.py; R albedo, G gloss, B/A normal x/y, 128 =
     neutral) sampled triplanar in world space, so courses of brick and boards run level and line up across pieces.
     IB_DETAIL 2 = three projections (high), 1 = the dominant one (medium); without it (low, potato, WebGL1) only the
     cheap macro term. Per class (IB_CD): layer (-1 none), tile size m, normal strength, albedo amount. */
  var DETAIL_PARS = [
    '#ifdef IB_DETAIL',
    'precision highp sampler2DArray;',   // trap T18
    'uniform sampler2DArray uDetail; uniform float uDetailOn;',
    'const vec4 IB_CD[ 16 ] = vec4[ 16 ](',
    '  vec4( 13.0, 1.5, 0.35, 0.6 ), vec4( 1.0, 2.4, 0.6, 0.6 ), vec4( 2.0, 1.0, 0.5, 0.7 ), vec4( 3.0, 1.5, 0.5, 0.8 ),',
    '  vec4( 4.0, 1.2, 0.7, 0.9 ), vec4( 5.0, 0.5, 0.6, 0.8 ), vec4( 6.0, 2.0, 0.7, 0.75 ), vec4( 7.0, 0.8, 0.6, 0.9 ),',
    '  vec4( 8.0, 3.0, 0.9, 1.0 ), vec4( 9.0, 1.25, 0.8, 1.0 ), vec4( 10.0, 0.6, 0.6, 0.9 ), vec4( -1.0, 1.0, 0.0, 0.0 ),',
    '  vec4( 11.0, 2.0, 0.6, 0.75 ), vec4( 12.0, 2.5, 0.5, 0.6 ), vec4( -1.0, 1.0, 0.0, 0.0 ), vec4( -1.0, 1.0, 0.0, 0.0 ) );',
    'vec4 ibDet( vec2 uv, float layer ) { vec4 t = texture( uDetail, vec3( uv, layer ) ); return vec4( ( t.rg * 255.0 - 128.0 ) / 320.0, ( t.ba * 255.0 - 128.0 ) / 127.0 ); }',
    '#endif'
  ].join('\n');

  var LIGHT = [
    '#ifdef USE_MAP',
    '  vec4 ibS = texture2D( uSurf, vUv );',
    '#else',
    '  vec4 ibS = uSurfFlat;',
    '#endif',
    // vertex colour on kit meshes: R classic two-step AO, G smooth ground-contact AO, B edge wear (Stage 5D); trap T5
    '#if defined( USE_MAP ) && defined( USE_COLOR )',
    '  vec3 ibAlb = diffuseColor.rgb / max( vColor.rrr, vec3( 0.001 ) ); float ibAO = vColor.r, ibAOs = vColor.g, ibWear = vColor.b;',
    '#else',
    '  vec3 ibAlb = diffuseColor.rgb; float ibAO = 1.0, ibAOs = 1.0, ibWear = 0.5;',
    '#endif',
    'float ibCls = floor( ibS.b * 15.0 + 0.5 );',
    'float ibEm = step( 0.5, ibS.a );',
    'vec3 ibNv = normalize( normal ); vec3 ibV = normalize( vViewPosition );',
    'vec3 ibNw = inverseTransformDirection( ibNv, viewMatrix );',
    'float ibDist = length( vViewPosition );',
    // albedo grade: saturation, gain, ceiling (compress, never clip); emissive cells untouched
    'const vec3 IB_LUMA = vec3( 0.2126, 0.7152, 0.0722 );',
    'vec3 ibA = ibAlb;',
    'ibA = mix( vec3( dot( ibA, IB_LUMA ) ), ibA, mix( uAlbSat, 1.0, ibEm ) ) * mix( uAlbGain, 1.0, ibEm );',
    'ibA *= mix( min( 1.0, uAlbCeil / max( dot( ibA, IB_LUMA ), 1e-4 ) ), 1.0, ibEm );',
    // macro variation: big soft blotches so large flat areas are never one flat colour
    'float ibRough = ibCls == 1.0 || ibCls == 6.0 || ibCls == 8.0 || ibCls == 12.0 ? 1.0 : ibCls == 4.0 || ibCls == 5.0 || ibCls == 9.0 || ibCls == 13.0 ? 0.7 : ibCls == 11.0 || ibCls == 14.0 || ibCls == 15.0 ? 0.0 : 0.4;',
    'vec2 ibQ = vec2( vWP.x + vWP.y * 0.71, vWP.z - vWP.y * 0.63 );',
    'float ibGlossK = 1.0; vec3 ibNwB = ibNw;',
    '#ifdef IB_DETAIL',
    '  float ibMacro = texture( uDetail, vec3( ibQ / 6.0, 0.0 ) ).r * 255.0 / 256.0;',
    '  vec4 ibCD = IB_CD[ int( ibCls ) ];',
    '  float ibDF = ( 1.0 - smoothstep( 30.0, 80.0, ibDist ) ) * uDetailOn * step( 0.0, ibCD.x );',
    '  vec3 ibP = vWP / ibCD.y; float ibLay = max( ibCD.x, 0.0 );',
    '  vec3 ibW3 = pow( abs( ibNw ), vec3( 4.0 ) ); ibW3 /= ( ibW3.x + ibW3.y + ibW3.z );',
    '  #if IB_DETAIL > 1',
    '    vec4 ibDx = ibDet( vec2( ibP.z * sign( ibNw.x ), ibP.y ), ibLay ), ibDy = ibDet( ibP.xz, ibLay ), ibDz = ibDet( vec2( -ibP.x * sign( ibNw.z ), ibP.y ), ibLay );',
    '    vec4 ibD = ibDx * ibW3.x + ibDy * ibW3.y + ibDz * ibW3.z;',
    '    vec3 ibDN = ibW3.x * vec3( 0.0, ibDx.w, ibDx.z * sign( ibNw.x ) ) + ibW3.y * vec3( ibDy.z, 0.0, ibDy.w ) + ibW3.z * vec3( -ibDz.z * sign( ibNw.z ), ibDz.w, 0.0 );',
    '  #else',
    '    float ibAx = ibW3.x > max( ibW3.y, ibW3.z ) ? 0.0 : ( ibW3.y > ibW3.z ? 1.0 : 2.0 );',
    '    vec2 ibUv = ibAx < 0.5 ? vec2( ibP.z * sign( ibNw.x ), ibP.y ) : ( ibAx < 1.5 ? ibP.xz : vec2( -ibP.x * sign( ibNw.z ), ibP.y ) );',
    '    vec4 ibD = ibDet( ibUv, ibLay );',
    '    vec3 ibDN = ibAx < 0.5 ? vec3( 0.0, ibD.w, ibD.z * sign( ibNw.x ) ) : ( ibAx < 1.5 ? vec3( ibD.z, 0.0, ibD.w ) : vec3( -ibD.z * sign( ibNw.z ), ibD.w, 0.0 ) );',
    '  #endif',
    '  ibA *= 1.0 + ibD.x * ibCD.w * ibDF;',
    '  ibGlossK = 1.0 + ibD.y * ibDF;',
    '  ibNwB = normalize( ibNw + ibDN * ibCD.z * ibDF );',
    '#else',
    '  float ibMacro = ibN2( ibQ * 0.33 ) * 0.6 + ibN2( ibQ * 0.89 + 5.3 ) * 0.4;',
    '#endif',
    'ibA *= 1.0 + ( ibMacro - 0.5 ) * 0.22 * ibRough;',
    // ground-contact grime (G) and edge wear (B, painted classes show lighter chipped edges; concrete darker)
    'float ibWearK = smoothstep( 0.62, 0.95, ibWear ) * ( 1.0 - ibEm );',
    'ibA *= mix( 0.78, 1.0, smoothstep( 0.0, 0.9, ibAOs ) );',
    'if ( ibCls == 0.0 || ibCls == 3.0 ) ibA = mix( ibA, ibA * 1.18 + 0.03, ibWearK * 0.45 );',
    'if ( ibCls == 1.0 || ibCls == 8.0 ) ibA *= 1.0 - ibWearK * 0.08;',
    'vec3 ibAL = pow( max( ibA, vec3( 0.0 ) ), vec3( 2.2 ) );',
    'vec3 ibNb = normalize( ( viewMatrix * vec4( ibNwB, 0.0 ) ).xyz );',   // bumped normal, view space
    // light
    '#if NUM_DIR_LIGHTS > 0',
    '  vec3 ibL = directionalLights[ 0 ].direction; vec3 ibLC = directionalLights[ 0 ].color;',
    '#else',
    '  vec3 ibL = vec3( 0.0, 1.0, 0.0 ); vec3 ibLC = vec3( 0.0 );',
    '#endif',
    'float ibSh = 1.0;',
    '#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0',
    '  ibSh = receiveShadow ? getShadow( directionalShadowMap[ 0 ], directionalLightShadows[ 0 ].shadowMapSize, directionalLightShadows[ 0 ].shadowBias, directionalLightShadows[ 0 ].shadowRadius, vDirectionalShadowCoord[ 0 ] ) : 1.0;',
    '  { vec3 ibSc = vDirectionalShadowCoord[ 0 ].xyz / vDirectionalShadowCoord[ 0 ].w; float ibE = min( min( ibSc.x, 1.0 - ibSc.x ), min( ibSc.y, 1.0 - ibSc.y ) );',
    '    ibSh = mix( 1.0, ibSh, smoothstep( 0.0, uShEdge, ibE ) ); }',   // fade out over the box's last 8 m
    '#endif',
    // light volume sampled 0.35 m off the surface into the room it faces (trap T15); alpha = sky visibility (trap T12)
    'vec4 ibG = uGridOn > 0.5 ? ibGridAt( vWP + ibNw * 0.35 ) : vec4( 0.0, 0.0, 0.0, 1.0 - uIndoor );',
    'float ibSky = ibG.a;',
    'float ibNL = ibCls == 7.0 ? clamp( ( dot( ibNb, ibL ) + 0.45 ) / 1.45, 0.0, 1.0 ) : max( dot( ibNb, ibL ), 0.0 ) * step( 0.0, dot( ibNv, ibL ) + 0.05 );',   // foliage wraps the light
    'float ibHem = ibNwB.y * 0.5 + 0.5;',
    'float ibOcc = min( mix( 0.5, 1.0, smoothstep( 0.8, 1.0, ibAO ) ), mix( 0.35, 1.0, ibAOs ) );',
    'float ibAmbK = ibSky + ( 1.0 - ibSky ) * uIndoorAmb;',
    'vec3 ibAmb = mix( uAmbGround, uAmbSky, ibHem ) * uAmbI * ibOcc * ibAmbK + vec3( uAmbFloor );',
    'vec3 ibLoc = ibG.rgb * ibG.rgb * 4.0 * uGridI * mix( 0.5, 1.0, ibHem ) * ibOcc;',
    // flash lights (muzzle flashes, blasts)
    'for ( int i = 0; i < 4; i++ ) {',
    '  if ( uFlashC[ i ].a > 0.0 ) {',
    '    vec3 ibFd = uFlashP[ i ].xyz - vWP; float ibDd = dot( ibFd, ibFd ), ibFr2 = uFlashP[ i ].w;',
    '    if ( ibDd < ibFr2 * ibFr2 ) ibLoc += uFlashC[ i ].rgb * uFlashC[ i ].a * 6.0 / ( 1.0 + ibDd ) * ( 1.0 - sqrt( ibDd ) / ibFr2 ) * ( 0.35 + 0.65 * max( dot( ibNwB, ibFd * inversesqrt( max( ibDd, 1e-4 ) ) ), 0.0 ) );',
    '  }',
    '}',
    'vec3 ibSun = ibLC * uSunI * ibNL * ibSh * ibSky;',
    // glass and water: a dark body (12% of the palette colour), the rest is reflection below
    'float ibMirror = ibCls == 11.0 || ibCls == 14.0 ? 1.0 : 0.0;',
    'vec3 ibCol = ibAL * ( ibSun + ibAmb + ibLoc ) * mix( 1.0, 0.16, ibMirror );',
    // specular: sun Blinn-Phong + sky / lamp sheen with Fresnel; none on foliage
    'float ibGloss = clamp( ibS.r * ibGlossK * ( ibCls == 0.0 || ibCls == 3.0 ? 1.0 + ibWearK * 0.4 : 1.0 ) * mix( 1.0, 0.7, ( 1.0 - ibAOs ) ), 0.0, 1.0 ) * ( ibCls == 7.0 ? 0.0 : 1.0 );',
    'vec3 ibSpecC = mix( vec3( 0.04 ), ibAL, ibS.g );',
    'float ibNH = max( dot( ibNb, normalize( ibL + ibV ) ), 0.0 );',
    'float ibPow = mix( 6.0, 180.0, ibGloss * ibGloss );',
    'ibCol += ibSpecC * pow( ibNH, ibPow ) * ( ibPow + 8.0 ) / 25.0 * ibLC * uSunI * ibSh * ibSky * ibNL * 4.0 * ( 0.15 + ibGloss ) * step( 0.01, ibGloss );',
    'float ibFr = pow( 1.0 - max( dot( ibNb, ibV ), 0.0 ), 5.0 );',
    'vec3 ibRd = reflect( -inverseTransformDirection( ibV, viewMatrix ), ibNwB );',
    'vec3 ibRefl = mix( uAmbGround, uAmbSky * mix( 1.0, 1.6, ibMirror ), clamp( ibRd.y * 0.5 + 0.5, 0.0, 1.0 ) ) * uAmbI * ibAmbK + ibLoc * 0.6;',
    'ibCol += ibRefl * ( ibSpecC + ( 1.0 - ibSpecC ) * max( ibFr, ibMirror * 0.22 ) ) * ibGloss * ibGloss * 1.4 * ibOcc;',
    'ibCol = pow( max( ibCol, vec3( 0.0 ) ), vec3( 1.0 / 2.2 ) );',
    'ibCol = mix( ibCol, ibAlb * uEmBoost, ibEm );',   // emissive cells: unlit, boosted (bloom source above 1.0)
    'vec3 outgoingLight = ibCol + totalEmissiveRadiance;'
  ].join('\n');

  var FOG = [
    '#ifdef USE_FOG',
    '  float ibFf = ibFogAmount( fogDepth, vWP.y, fogNear, fogFar );',
    '  vec3 ibVd = normalize( vWP - cameraPosition );',
    '  vec3 ibFc = mix( fogColor, uSunFog, pow( max( dot( ibVd, uSunDirW ), 0.0 ), 6.0 ) * 0.55 * ibSky );',
    '  gl_FragColor.rgb = mix( gl_FragColor.rgb, ibFc, ibFf );',
    '#endif',
    // tiers without the post pass: the same exposure, saturation, split tone, contrast and shoulder here (plan 6.5)
    '#ifdef IB_GRADE_IN_MATERIAL',
    '  { vec3 c = gl_FragColor.rgb * uGExpo; float l = dot( c, vec3( 0.2126, 0.7152, 0.0722 ) ); c = mix( vec3( l ), c, uGSat );',
    '    c *= mix( uGLo, uGHi, smoothstep( 0.05, 0.85, l ) ); vec3 k = clamp( c, 0.0, 1.0 ); c = mix( c, k * k * ( 3.0 - 2.0 * k ) + max( c - 1.0, 0.0 ), uGCon );',
    '    gl_FragColor.rgb = c / ( 1.0 + max( c - 0.82, 0.0 ) * 0.9 ); }',
    '#endif'
  ].join('\n');

  // shell offset: classic only ever adds to the baked 2 cm shell; the look can pull it back toward the surface
  // (plan 2.7, trap T27) and fades it out with distance (ink.fade)
  var INK_CLASSIC = 'max( 0.0, min( uOutMax, max( uOutBase, uOutK * -mvPosition.z ) * uHullK ) - uBaked )';
  var INK_LOOK = '( max( min( uOutMax, max( uOutBase, uOutK * -mvPosition.z ) * uHullK ) * ( 1.0 - smoothstep( uInkFade.x, uInkFade.y, -mvPosition.z ) * step( uHullK, 1.0 ) ), 0.001 ) - uBaked )';
  S.INK_CLASSIC = INK_CLASSIC;

  function req(src, anchor, what) {
    if (src.indexOf(anchor) < 0) { var e = 'IB.Surface: anchor missing (' + what + '): ' + anchor.slice(0, 60); if (IB.Game && IB.Game.errors) IB.Game.errors.push(e); console.error(e); }
  }

  // detail projections for the current tier: 2 high, 1 medium, 0 low / potato / WebGL1 / no texture array support
  S.detailLevel = function () {
    var R = IB.Render, r = R && R.renderer;
    if (!r || !r.capabilities.isWebGL2 || !THREE.DataTexture2DArray) return 0;
    return Math.max(0, IB.LOOKS.tier(R.tier).detail);
  };
  /* The detail array: two opaque RGB strips (trap T26) decoded through a canvas and interleaved into RGBA
     (R albedo, G gloss from detail-a; B, A normal x, y from detail-n). In the single-file build they are data URLs
     (IB.TEX_DATA); the dev page loads assets/tex/. Until loaded, uDetailOn = 0. */
  S.loadDetail = function (renderer) {
    var U = IB.Look.U;
    if (!IB.Look.on || !renderer.capabilities.isWebGL2 || !THREE.DataTexture2DArray || S._detailP) return S._detailP || Promise.resolve(null);
    var src = IB.TEX_DATA || {};
    function load(fn) { return new Promise(function (res, rej) { var im = new Image(); im.onload = function () { res(im); }; im.onerror = function () { rej(new Error('detail texture ' + fn)); }; im.src = src[fn] || ('assets/tex/' + fn); }); }
    S._detailP = Promise.all([load('detail-a.webp'), load('detail-n.webp')]).then(function (ims) {
      var w = ims[0].width, h = ims[0].height, layers = Math.round(h / w);
      function px(im) { var c = document.createElement('canvas'); c.width = w; c.height = h; var g = c.getContext('2d'); g.drawImage(im, 0, 0); return g.getImageData(0, 0, w, h).data; }
      var a = px(ims[0]), n = px(ims[1]), out = new Uint8Array(w * h * 4);
      for (var i = 0, N = w * h; i < N; i++) { out[i * 4] = a[i * 4]; out[i * 4 + 1] = a[i * 4 + 1]; out[i * 4 + 2] = n[i * 4]; out[i * 4 + 3] = n[i * 4 + 1]; }
      var t = new THREE.DataTexture2DArray(out, w, w, layers);
      t.format = THREE.RGBAFormat; t.type = THREE.UnsignedByteType; t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter; t.generateMipmaps = true;
      t.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy()); t.needsUpdate = true;
      U.uDetail.value = t; U.uDetailOn.value = 1;
      // decode check: each layer's mean albedo and gloss byte within 3 of 128
      var bad = [];
      for (var l = 0; l < layers; l++) { var sr = 0, sg = 0, o = l * w * w; for (var k = 0; k < w * w; k += 7) { sr += out[(o + k) * 4]; sg += out[(o + k) * 4 + 1]; } var cnt = Math.ceil(w * w / 7); if (Math.abs(sr / cnt - 128) > 3 || Math.abs(sg / cnt - 128) > 3) bad.push(l); }
      S.detailInfo = { w: w, layers: layers, bad: bad };
      if (bad.length) console.error('[look] detail layers decode off-centre: ' + bad.join(','));
      return t;
    }).catch(function (e) { console.warn('[look] detail textures unavailable: ' + e.message); return null; });
    return S._detailP;
  };

  // sh: the shader being compiled; kind: 'world' | 'actor'; surf: { tex } (palette materials) or { flat: Vector4 uniform }
  S.patch = function (sh, kind, surf) {
    var U = IB.Look.U;
    for (var k in U) sh.uniforms[k] = U[k];
    sh.uniforms.uSurf = { value: surf.tex || S.texFor('') };
    sh.uniforms.uSurfFlat = surf.flat || { value: S.flat(1, 0.14) };
    req(sh.vertexShader, 'vHull = 0.0;', 'vertex world position');
    req(sh.vertexShader, INK_CLASSIC, 'ink clamp');
    req(sh.fragmentShader, '#include <shadowmap_pars_fragment>', 'fragment pars');
    req(sh.fragmentShader, OUTLINE_LINE, 'light line');
    req(sh.fragmentShader, '#include <fog_fragment>', 'fog');
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWP;\nuniform vec2 uInkFade;')
      .replace(INK_CLASSIC, INK_LOOK)
      .replace('vHull = 0.0;', 'vHull = 0.0;\n{ vec4 ibW = vec4( transformed, 1.0 );\n#ifdef USE_INSTANCING\n ibW = instanceMatrix * ibW;\n#endif\n vWP = ( modelMatrix * ibW ).xyz; }');
    var det = S.detailLevel();
    sh.uniforms.uDetail = U.uDetail; sh.uniforms.uDetailOn = U.uDetailOn;
    var gradeIn = !(IB.Post && IB.Post.on);
    sh.fragmentShader = (det > 0 ? '#define IB_DETAIL ' + det + '\n' : '') + (gradeIn ? '#define IB_GRADE_IN_MATERIAL\n' : '') + sh.fragmentShader
      .replace('#include <shadowmap_pars_fragment>', '#include <shadowmap_pars_fragment>\n' + PARS + '\n' + DETAIL_PARS)
      .replace(OUTLINE_LINE, LIGHT)
      .replace('#include <fog_fragment>', FOG);
  };
})(window.IB = window.IB || {});
