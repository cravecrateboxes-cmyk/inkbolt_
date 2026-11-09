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

  var FLAG_A = { pat: 223, glow: 191, shim: 159, patshim: 127 };
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

  var FRAG_PARS = [
    'uniform float uPat, uPatS, uShim, uTime, uPatGlow; uniform vec3 uPatC, uGlowC, uShimC;',
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
    '  if ( t < 5.5 ) { vec2 q = uv * 95.0; float a = sin( q.x + sin( q.y * 0.9 ) * 2.4 ) + sin( q.y + sin( q.x * 0.7 ) * 2.0 );',          // filigree scrolls: a sum (not a product) gives unbroken curves
    '    return ( 1.0 - smoothstep( 0.1, 0.22, abs( a ) ) ) * 0.9; }',
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
    'if ( ( ibF == 1.0 || ibF == 4.0 ) && uPat > 0.5 ) diffuseColor.rgb = mix( diffuseColor.rgb, ibPatCol( uPat, vIbP, vIbN ), ibPattern( uPat, vIbP * uPatS, vIbN ) );'
  ].join('\n');
  var FRAG_END = [
    'if ( ibF == 2.0 ) gl_FragColor.rgb = mix( gl_FragColor.rgb, uGlowC * ( 1.05 + 0.18 * sin( uTime * 3.2 + vIbP.z * 9.0 ) ), 0.88 );',
    'if ( uPatGlow > 0.5 && ( ibF == 1.0 || ibF == 4.0 ) ) gl_FragColor.rgb = mix( gl_FragColor.rgb, uPatC * ( 1.15 + 0.3 * sin( uTime * 2.2 + vIbP.z * 14.0 ) ), ibPattern( uPat, vIbP * uPatS, vIbN ) * 0.92 );',
    'if ( uShim > 0.5 && ( ibF >= 2.0 ) ) {',
    '  float s = fract( vIbP.z * 0.9 - vIbP.y * 0.6 - uTime * 0.32 ); float b = smoothstep( 0.0, 0.035, s ) * ( 1.0 - smoothstep( 0.035, 0.11, s ) );',
    '  gl_FragColor.rgb += uShimC * b * 0.55; }',
    'if ( vHull > 0.5 )'
  ].join('\n');

  function C(h) { return new THREE.Color(h); }
  GS.material = function (gunId, tier, uni) {
    var R = IB.Render, A = IB.Assets;
    uni = uni || R.worldOutline;
    tier = tier || 'gray';
    if (!D() || !A.palette || !A.palette.weapons) return R.toonMaterial({ uni: uni, map: A.palette && A.palette.weapons, baked: A.BAKED ? A.BAKED.weapons : 0 });
    if (!uni._skinId) uni._skinId = 'u' + (GS._u = (GS._u || 0) + 1);
    var key = gunId + '|' + tier + '|' + uni._skinId;
    if (GS.cache[key]) return GS.cache[key];
    var sk = D().skin(gunId, tier);
    var mat = R.toonMaterial({ uni: uni, map: texture(sk), baked: A.BAKED ? A.BAKED.weapons : 0 });
    var U = { uPat: { value: D().PATTERNS[sk.pat.type] || 0 }, uPatS: { value: sk.pat.scale }, uPatC: { value: C(sk.pat.col) },
      uGlowC: { value: C(sk.glow) }, uShim: { value: sk.shimmer }, uTime: time,
      uShimC: { value: C(sk.shimCol || '#FFEBB3') }, uPatGlow: { value: sk.patGlow || 0 } };
    var inner = mat.onBeforeCompile, key0 = mat.customProgramCacheKey;
    mat.onBeforeCompile = function (sh) {
      inner(sh);
      for (var k in U) sh.uniforms[k] = U[k];
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vIbP; varying vec3 vIbN;')
        .replace('vHull = 0.0;', 'vHull = 0.0; vIbP = position; vIbN = normal;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\n' + FRAG_PARS)
        .replace('#include <map_fragment>', FRAG_MAP).replace('if ( vHull > 0.5 )', FRAG_END);
    };
    mat.customProgramCacheKey = function () { return key0() + 'skin'; };
    mat.userData.skin = sk;
    GS.cache[key] = mat;
    return mat;
  };
})(window.IB = window.IB || {});
