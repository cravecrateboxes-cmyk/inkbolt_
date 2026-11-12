/* INKBOLT gun skins at runtime: a gun's skin (src/core/gunskins.js) as an 8 x 8 palette texture (one texel per
   weapons-palette cell, the cell flags in alpha) on a toon material with a small shader extension:
     pattern (object-space: wood grain, carbon twill, camo blotches, hex lattice, filigree, anodising sheen, and the
     Legendary finishes: molten veins (emissive), oil-slick iridescence, aurora nebula, damascus bands, pearl) on
     'pat' cells, unlit breathing glow on 'glow' cells, a slow bright sweep on 'shim' cells (Legendary).
   One program for every skin (patterns are uniforms); one material per (gun, tier, outline set), made on first use.
     IB.GunSkins.material(gunId, tier, uni)  uni: IB.Render.vmOutline (viewmodel), worldOutline (default) or any
                                             outline uniform set (thumbs)
     IB.GunSkins.tierOf(gunId)               the owned gun's tier id ('gray' when not owned)
     IB.GunSkins.name(gunId, tier, base) / feel(tier)   (IB.GunSkinData)
     IB.GunSkins.tick(t)                     shared time uniform (glow breathing, shimmer) */
(function (IB) {
  'use strict';
  var GS = IB.GunSkins = { cache: {} };
  var D = function () { return IB.GunSkinData; };
  var time = { value: 0 };
  GS.time = time;
  GS.tick = function (t) { time.value = t; };
  GS.tierOf = function (id) { var s = IB.Game && IB.Game.slot; return (s && s.gunTier && s.gunTier[id]) || 'gray'; };
  GS.name = function (id, tier, base) { return D() ? D().name(id, tier, base) : base; };
  GS.feel = function (tier) { return D() ? D().feel(tier) : null; };

  /* Rarity layers: extra meshes of a gun named WPN_<ID>_L<tiers> (and WPN_<ID>_Mag_L<tiers> on its magazine), shown
     when the gun's tier digit (1 Standard .. 5 Legendary) is in <tiers> (blender/fam_weapons.py build_weapon_meshes).
       GS.layerOn(name, tier)     is this mesh shown at that tier (true for anything that is not a layer)
       GS.layerNames(id, tier)    { gun: [names], mag: [names] } of the layers shown at that tier
       GS.dress(obj, mat, tier)   a gun or magazine node: material on it and its layers, layers shown / hidden */
  var TIER_N = { gray: '1', green: '2', blue: '3', purple: '4', orange: '5' }, layerCache = {};
  GS.layerOn = function (name, tier) { var m = /_L(\d+)$/.exec(name || ''); return !m || m[1].indexOf(TIER_N[tier] || '1') >= 0; };
  GS.layerNames = function (id, tier) {
    var K = 'WPN_' + String(id).toUpperCase(), all = layerCache[K];
    if (!all) {
      all = { gun: [], mag: [] };
      var geo = (IB.Assets && IB.Assets.geo) || {}, n = 0;
      Object.keys(geo).forEach(function (nm) {
        n++;
        if (nm.indexOf(K + '_L') === 0 && /^_L\d+$/.test(nm.slice(K.length))) all.gun.push(nm);
        else if (nm.indexOf(K + '_Mag_L') === 0 && /^_Mag_L\d+$/.test(nm.slice(K.length))) all.mag.push(nm);
      });
      if (n) layerCache[K] = all;   // only once the models are in
    }
    function on(nm) { return GS.layerOn(nm, tier); }
    return { gun: all.gun.filter(on), mag: all.mag.filter(on) };
  };
  GS.dress = function (obj, mat, tier) {
    if (!obj) return;
    if (mat) obj.material = mat;
    for (var i = 0; i < obj.children.length; i++) {
      var c = obj.children[i]; if (!c.isMesh) continue;
      if (mat) c.material = mat;
      c.frustumCulled = false; c.visible = GS.layerOn(c.name, tier);
    }
  };

  var FLAG_A = { pat: 223, glow: 191, shim: 159, patshim: 127, patshimgrad: 32 };   // patshimgrad (7): pattern + shimmer + height gradient
  var base = null;   // Uint8 RGBA of the weapons palette, one texel per cell (cell i -> texel (i % 8, 7 - i / 8))
  function basePixels() {
    if (base) return base;
    var img = IB.Assets && IB.Assets.palette && IB.Assets.palette.weapons && IB.Assets.palette.weapons.image;
    base = new Uint8Array(64 * 4);
    try {
      var cv = document.createElement('canvas'); cv.width = cv.height = 64;
      var cx = cv.getContext('2d'); cx.drawImage(img, 0, 0, 64, 64);
      var d = cx.getImageData(0, 0, 64, 64).data;
      for (var r = 0; r < 8; r++) for (var c = 0; c < 8; c++) {   // texel row r = image row band r (top down)
        var k = ((r * 8 + 3) * 64 + c * 8 + 3) * 4, o = (r * 8 + c) * 4;
        base[o] = d[k]; base[o + 1] = d[k + 1]; base[o + 2] = d[k + 2]; base[o + 3] = 255;
      }
    } catch (e) { for (var i = 0; i < 256; i++) base[i] = 200; }
    return base;
  }
  function texture(skin) {
    var px = new Uint8Array(basePixels()), cells = D().CELLS;
    Object.keys(skin.cells).forEach(function (n) {
      var i = cells.indexOf(n); if (i < 0) return;
      var o = ((7 - (i >> 3)) * 8 + (i & 7)) * 4, c = D().rgb(skin.cells[n].hex), f = skin.cells[n].flag;
      px[o] = c[0]; px[o + 1] = c[1]; px[o + 2] = c[2]; px[o + 3] = f ? FLAG_A[f] : 255;
    });
    var t = new THREE.DataTexture(px, 8, 8, THREE.RGBAFormat);
    t.encoding = THREE.LinearEncoding; t.magFilter = t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.flipY = false;
    t.needsUpdate = true;
    return t;
  }

  // surface per cell for the tactical shading: R gloss, G metal (IB.GunSkinData.SURF), same 8 x 8 layout as the skin
  function surfTexture(skin) {
    var px = new Uint8Array(64 * 4), cells = D().CELLS, def = D().SURF_DEF;
    for (var i = 0; i < 64; i++) {
      var v = (skin.surf && skin.surf[cells[i]]) || def, o = ((7 - (i >> 3)) * 8 + (i & 7)) * 4;
      px[o] = Math.round(v[0] * 255); px[o + 1] = Math.round(v[1] * 255); px[o + 2] = 0; px[o + 3] = 255;
    }
    var t = new THREE.DataTexture(px, 8, 8, THREE.RGBAFormat);
    t.encoding = THREE.LinearEncoding; t.magFilter = t.minFilter = THREE.NearestFilter; t.generateMipmaps = false; t.flipY = false;
    t.needsUpdate = true;
    return t;
  }

  /* Tactical shading (guns only; the rest of the game keeps the flat comic ramp): a soft three-zone light ramp with a
     cool sky / warm bounce tint, a highlight sized by the cell's gloss and coloured by its metal, a rim on glancing
     faces, fine grain (brushed streaks along the barrel on metal, stipple on polymer) and grime that gathers where the
     baked cavity shading (vertex colour, blender/wpn_core.py cavity) is dark. The ink outline is untouched. */
  var FRAG_LIGHT = [
    'vec3 ibS = texture2D( uSurf, vUv ).rgb;',
    'vec3 ibNn = normalize( normal ); vec3 ibV = normalize( vViewPosition );',
    '#if NUM_DIR_LIGHTS > 0',
    '  vec3 ibL = directionalLights[ 0 ].direction; vec3 ibLC = min( directionalLights[ 0 ].color, vec3( 1.25 ) );',
    '#else',
    '  vec3 ibL = vec3( 0.3, 0.9, 0.5 ); vec3 ibLC = vec3( 1.0 );',
    '#endif',
    'float ibAO = vColor.r;',
    'float ibNL = dot( ibNn, ibL ), ibW = ibNL * 0.5 + 0.5;',
    'float ibRamp = 0.46 + 0.24 * smoothstep( 0.16, 0.40, ibW ) + 0.30 * smoothstep( 0.52, 0.82, ibW );',
    'vec3 ibUp = normalize( ( viewMatrix * vec4( 0.0, 1.0, 0.0, 0.0 ) ).xyz );',
    'float ibSky = dot( ibNn, ibUp ) * 0.5 + 0.5;',
    'vec3 ibAmb = mix( vec3( 0.90, 0.82, 0.80 ), vec3( 0.95, 1.0, 1.07 ), ibSky );',
    'float ibNear = 1.0 - smoothstep( 0.9, 2.6, vViewPosition.z );',
    'float ibGr = mix( ibH( floor( vIbP * 620.0 ) ), ibN( vec3( vIbP.x * 800.0, vIbP.y * 800.0, vIbP.z * 34.0 ) ), step( 0.4, ibS.g ) );',
    'float ibGrime = ibN( vIbP * 24.0 ) * 0.6 + ibN( vIbP * 61.0 ) * 0.4;',
    'vec3 ibBase = diffuseColor.rgb * ( 1.0 + ( ibGr - 0.5 ) * 0.085 * ibNear ) * ( 1.0 - ibGrime * ( 0.05 + 0.5 * ( 1.0 - ibAO ) ) * ibNear );',
    'vec3 ibCol = ibBase * ibRamp * ibAmb * ibLC;',
    'float ibNH = max( dot( ibNn, normalize( ibL + ibV ) ), 0.0 );',
    'float ibSp = pow( ibNH, mix( 5.0, 110.0, ibS.r ) ) * ( 0.06 + 0.94 * ibS.r ) * smoothstep( -0.05, 0.2, ibNL );',
    'ibCol += mix( vec3( 1.0 ), ibBase * 1.5 + 0.22, ibS.g ) * ibSp * 0.62 * ibAO * ibLC;',
    'float ibFr = pow( 1.0 - max( dot( ibNn, ibV ), 0.0 ), 3.0 );',
    'ibCol += mix( vec3( 0.56, 0.64, 0.78 ), ibBase, 0.35 ) * ibFr * ( 0.08 + 0.34 * ibS.r ) * ( 0.35 + 0.65 * ibSky );',
    'vec3 outgoingLight = ibCol + totalEmissiveRadiance;'
  ].join('\n');

  var FRAG_PARS = [
    'uniform float uPat, uPatS, uShim, uTime, uPatGlow; uniform vec3 uPatC, uGlowC, uShimC, uGradC; uniform vec2 uGradY; uniform sampler2D uSurf;',
    'varying vec3 vIbP; varying vec3 vIbN;',
    'float ibH( vec3 p ) { return fract( sin( dot( p, vec3( 127.1, 311.7, 74.7 ) ) ) * 43758.5453 ); }',
    'float ibN( vec3 p ) { vec3 i = floor( p ), f = fract( p ); f = f * f * ( 3.0 - 2.0 * f );',
    '  return mix( mix( mix( ibH( i ), ibH( i + vec3( 1, 0, 0 ) ), f.x ), mix( ibH( i + vec3( 0, 1, 0 ) ), ibH( i + vec3( 1, 1, 0 ) ), f.x ), f.y ),',
    '    mix( mix( ibH( i + vec3( 0, 0, 1 ) ), ibH( i + vec3( 1, 0, 1 ) ), f.x ), mix( ibH( i + vec3( 0, 1, 1 ) ), ibH( i + vec3( 1, 1, 1 ) ), f.x ), f.y ), f.z ); }',
    // 2D surface coordinates: the plane the face looks along (sides of the gun: forward x up)
    'vec2 ibUV( vec3 p, vec3 n ) { n = abs( n ); return n.x > max( n.y, n.z ) ? p.zy : ( n.y > n.z ? p.zx : p.xy ); }',
    'float ibPattern( float t, vec3 p, vec3 n ) {',
    '  vec2 uv = ibUV( p, n );',
    '  if ( t < 1.5 ) { float v = ibN( p * 15.0 ) * 0.65 + ibN( p * 38.0 ) * 0.35; return step( 0.56, v ) + step( 0.44, v ) * 0.45; }',  // camo: 2 tones
    '  if ( t < 2.5 ) { vec2 q = uv * 62.0, r = vec2( 1.0, 1.7320508 ), h = r * 0.5;',                                                   // hex lattice
    '    vec2 a = mod( q, r ) - h, b = mod( q - h, r ) - h, g = dot( a, a ) < dot( b, b ) ? a : b;',
    '    return smoothstep( 0.40, 0.46, max( dot( abs( g ), vec2( 0.5, 0.8660254 ) ), abs( g.x ) ) ); }',
    '  if ( t < 3.5 ) { vec2 q = floor( uv * 160.0 ); float w = mod( q.x + q.y, 4.0 ) < 2.0 ? 1.0 : 0.0;',                                 // carbon twill
    '    return w * 0.85; }',
    '  if ( t < 4.5 ) { float g = fract( uv.y * 55.0 + sin( uv.x * 9.0 ) * 0.9 + ibN( p * 9.0 ) * 2.2 ); return smoothstep( 0.62, 0.9, g ) * 0.9; }',   // wood grain
    // filigree scrolls, computed in 3D (not per face), so the engraved lines run unbroken over the box edges
    '  if ( t < 5.5 ) { vec3 q = p * 95.0; float a = sin( q.x + sin( q.y * 0.9 ) * 2.4 ) + sin( q.y + sin( q.z * 0.8 ) * 2.2 ) + sin( q.z + sin( q.x * 0.7 ) * 2.0 );',
    '    return ( 1.0 - smoothstep( 0.12, 0.3, abs( a ) ) ) * 0.9; }',
    '  if ( t < 6.5 ) return smoothstep( -0.2, 1.0, sin( dot( uv, vec2( 18.0, 30.0 ) ) ) ) * 0.55;',                                      // sheen bands
    '  if ( t < 7.5 ) { float v = min( abs( ibN( p * 16.0 ) - 0.5 ), abs( ibN( p * 34.0 + 3.1 ) - 0.5 ) * 1.4 );',                     // molten veins
    '    return 1.0 - smoothstep( 0.012, 0.034, v ); }',
    '  if ( t < 8.5 ) return 0.55 + 0.3 * ibN( p * 7.0 );',                                                                               // oil slick
    '  if ( t < 9.5 ) return 0.92;',                                                                                                      // aurora
    '  if ( t < 10.5 ) { float g = sin( uv.y * 70.0 + sin( uv.x * 11.0 + ibN( p * 5.0 ) * 5.0 ) * 3.2 + ibN( p * 18.0 ) * 2.4 );',     // damascus
    '    return smoothstep( 0.1, 0.8, g ) * 0.85; }',
    '  return 0.55 + 0.3 * ibN( p * 6.0 );',                                                                                              // pearl
    '}',
    // the pattern colour: most patterns use uPatC; oil slick, aurora and pearl paint their own
    'vec3 ibPatCol( float t, vec3 p, vec3 n ) {',
    '  if ( t > 7.5 && t < 8.5 ) { float h = ibN( p * 4.5 ) * 1.4 + dot( n, vec3( 0.45, 0.7, 0.3 ) ) * 0.5 + uTime * 0.04;',
    '    return mix( uPatC, 0.6 + 0.4 * cos( 6.2832 * ( h + vec3( 0.0, 0.33, 0.67 ) ) ), 0.62 ); }',
    '  if ( t > 8.5 && t < 9.5 ) { float k = ibN( p * 3.5 ) * 0.9 + p.z * 2.2 + p.y * 1.6 + 0.2 * sin( uTime * 0.4 );',
    '    vec3 c = mix( vec3( 0.06, 0.08, 0.26 ), uPatC, smoothstep( 0.15, 0.6, fract( k ) ) );',
    '    c = mix( c, vec3( 0.62, 0.32, 0.95 ), smoothstep( 0.55, 0.95, fract( k ) ) );',
    '    c = mix( c, vec3( 0.06, 0.08, 0.26 ), smoothstep( 0.0, 0.25, abs( ibN( p * 9.0 ) - 0.5 ) ) * 0.55 );',
    '    return c + step( 0.992, ibH( floor( p * 220.0 ) ) ) * 0.9; }',                                                                     // star specks
    '  if ( t > 10.5 ) return mix( uPatC, vec3( 0.86, 0.95, 1.0 ), 0.5 + 0.5 * n.y );',
    '  return uPatC;',
    '}'
  ].join('\n');
  var FRAG_MAP = [
    '#include <map_fragment>',
    'float ibF = floor( ( 1.0 - texelColor.a ) * 8.0 + 0.5 );',   // 0 none, 1 pat, 2 glow, 3 shim, 4 pat + shim
    'diffuseColor.a = opacity;',
    'if ( ibF == 7.0 ) diffuseColor.rgb = mix( diffuseColor.rgb, uGradC, smoothstep( uGradY.x, uGradY.y, vIbP.y ) );',   // height gradient
    'if ( ( ibF == 1.0 || ibF == 4.0 || ibF == 7.0 ) && uPat > 0.5 ) diffuseColor.rgb = mix( diffuseColor.rgb, ibPatCol( uPat, vIbP, vIbN ), ibPattern( uPat, vIbP * uPatS, vIbN ) );'
  ].join('\n');
  var FRAG_END = [
    'if ( ibF == 2.0 ) gl_FragColor.rgb = mix( gl_FragColor.rgb, uGlowC * ( 1.05 + 0.18 * sin( uTime * 3.2 + vIbP.z * 9.0 ) ), 0.88 );',
    'if ( uPatGlow > 0.5 && ( ibF == 1.0 || ibF == 4.0 || ibF == 7.0 ) ) gl_FragColor.rgb = mix( gl_FragColor.rgb, uPatC * ( 1.15 + 0.3 * sin( uTime * 2.2 + vIbP.z * 14.0 ) ), ibPattern( uPat, vIbP * uPatS, vIbN ) * 0.92 );',
    'if ( uShim > 0.5 && ( ibF >= 2.0 ) ) {',
    '  float s = fract( vIbP.z * 0.9 - vIbP.y * 0.6 - uTime * 0.32 ); float b = smoothstep( 0.0, 0.035, s ) * ( 1.0 - smoothstep( 0.035, 0.11, s ) );',
    '  gl_FragColor.rgb += uShimC * b * 0.55; }',
    'if ( vHull > 0.5 )'
  ].join('\n');

  function C(h) { return new THREE.Color(h); }
  /* outMax (optional): outline width cap for a gun shown enlarged in the world (IB.Render.toonMaterial) */
  GS.material = function (gunId, tier, uni, outMax) {
    var R = IB.Render, A = IB.Assets;
    uni = uni || R.worldOutline;
    tier = tier || 'gray';
    if (!D() || !A.palette || !A.palette.weapons) return R.toonMaterial({ uni: uni, map: A.palette && A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0, outMax: outMax });
    if (!uni._skinId) uni._skinId = 'u' + (GS._u = (GS._u || 0) + 1);
    var key = gunId + '|' + tier + '|' + uni._skinId + (outMax ? '|' + outMax : '');
    if (GS.cache[key]) return GS.cache[key];
    var sk = D().skin(gunId, tier);
    var mat = R.toonMaterial({ uni: uni, map: texture(sk), baked: A.BAKED ? A.BAKED.weapons : 0, outMax: outMax });
    var U = { uPat: { value: D().PATTERNS[sk.pat.type] || 0 }, uPatS: { value: sk.pat.scale }, uPatC: { value: C(sk.pat.col) },
      uGlowC: { value: C(sk.glow) }, uShim: { value: sk.shimmer }, uTime: time, uSurf: { value: surfTexture(sk) },
      uShimC: { value: C(sk.shimCol || '#FFEBB3') }, uPatGlow: { value: sk.patGlow || 0 },
      uGradC: { value: C(sk.grad ? sk.grad.from : '#FFFFFF') }, uGradY: { value: new THREE.Vector2(sk.grad ? sk.grad.y0 : 0, sk.grad ? sk.grad.y1 : 1) } };
    var inner = mat.onBeforeCompile, key0 = mat.customProgramCacheKey;
    mat.onBeforeCompile = function (sh) {
      inner(sh);
      for (var k in U) sh.uniforms[k] = U[k];
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vIbP; varying vec3 vIbN;')
        .replace('vHull = 0.0;', 'vHull = 0.0; vIbP = position; vIbN = normal;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\n' + FRAG_PARS)
        .replace('#include <map_fragment>', FRAG_MAP).replace('if ( vHull > 0.5 )', FRAG_END)
        .replace('vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;', FRAG_LIGHT);
    };
    mat.customProgramCacheKey = function () { return key0() + 'skin'; };
    mat.userData.skin = sk;
    GS.cache[key] = mat;
    return mat;
  };
})(window.IB = window.IB || {});
