/* INKBOLT comic VFX ("Boom"): explosions, debris, sparks, arcs, onomatopoeia words, shell casings, explosive
   canisters and screen ink. Everything is pooled at init (no allocation in the hot loop) and drawn by a handful of
   instanced meshes that only draw while something in them is alive:
     puffs    toon fireball / smoke spheres: banded shading, halftone shadow, ink rim, ragged ink-edged dissolve  1 draw
     cards    flat comic cards from one canvas atlas: flash bursts, rings, speed lines, sparks, chips, dust,
              arcs, stars, bubbles, drips, tracers (3-tone: ink / tint / paper, channel-coded in the atlas)       1 draw
     words    onomatopoeia (KRAK! BLAM! ZZAP! KA-BOOM! ...): outlined, halftone-shaded, drawn over the world     1 draw
     debris   gears / bolts / plates + per-robot parts (lid, wheel, rotor, cap, leg) with ink outlines         <= 9 draws
     casings  shells from the gun's EJECT socket (viewmodel scene)                                              1 draw
     cans     explosive canisters placed in later zones (shoot them, or let a robot bolt / blast set them off) 1 draw
   Escalation: B.intensity(level) scales counts, sizes, debris, scrap chain pops, word rate and canisters per zone.
   Quality tier: FX.particleScale scales every count; settings.reduceFlash dims flash cards and skips the screen flash.
   Hooks: FX.init / FX.update / FX.clear / FX.dropGem / FX.word are wrapped here; ai.js, projectiles.js, game.js,
   status.js, skillfx.js, weapons.js and zones.js call IB.Boom.* when it exists. */
(function (IB) {
  'use strict';
  var B = IB.Boom = {};

  // ---------------- pure rules (unit-tested in node, no THREE) ----------------
  /* how hard the campaign hits: 1.0 on level 1, +0.15 a level, capped at 2.2 (level 9 on) */
  B.intensity = function (L) { L = Math.max(1, +L || 1); return Math.min(2.2, 1 + 0.15 * (L - 1)); };
  /* explosive canisters per zone: none on levels 1-2, then 1, 2, 3, up to 4 */
  B.canistersPerZone = function (L) { L = +L || 1; return L < 3 ? 0 : Math.min(4, Math.floor((L - 1) / 2)); };
  /* chance that a wreck throws a chain of secondary scrap pops (cosmetic) */
  B.chainChance = function (L) { L = +L || 1; return L < 2 ? 0 : Math.min(0.55, 0.08 * (L - 1)); };
  /* chance of a comic word on a robot death (big blasts always get one) */
  B.wordChance = function (L, big) { L = +L || 1; return big ? 1 : Math.min(0.85, 0.4 + 0.06 * (L - 1)); };
  /* open(i, j) -> bool for nav cells; true when every cell within rc cells of (i, j) is open */
  B.clearPatch = function (open, i, j, rc) {
    for (var dj = -rc; dj <= rc; dj++) for (var di = -rc; di <= rc; di++) {
      if (di * di + dj * dj > rc * rc + 1) continue;
      if (!open(i + di, j + dj)) return false;
    }
    return true;
  };
  /* canister rules: hp, fuse when shot (telegraphed by a red ring), fuse when a blast reaches it, blast */
  B.CAN = { hp: 24, fuse: 0.55, chainFuse: 0.2, radius: 3.4, dmgPlayer: 30, dmgRobots: 90, gap: 6, fromEntry: 7, fromSpawn: 3, fromGate: 5 };

  if (typeof window === 'undefined' || typeof THREE === 'undefined') return;   // node unit tests: rules only

  var PAL = IB.PAL, FX = IB.FX;
  var TAU = Math.PI * 2;
  var ZERO = new THREE.Matrix4().makeScale(0, 0, 0);
  var _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _qX = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2);
  var _v = new THREE.Vector3(), _s = new THREE.Vector3(), _a = new THREE.Vector3(), _b = new THREE.Vector3(), _n = new THREE.Vector3(), _e = new THREE.Euler();
  var _z = new THREE.Vector3(0, 0, 1), _y = new THREE.Vector3(0, 1, 0), _c = new THREE.Color(), _cam = new THREE.Vector3();
  function rnd(a, b) { return a + Math.random() * (b - a); }
  function ps() { return FX.particleScale > 0 ? FX.particleScale : 1; }
  function cnt(n) { var k = n * ps(); return Math.floor(k) + (Math.random() < k - Math.floor(k) ? 1 : 0); }
  function reduce() { var g = IB.Game; return !!(g && g.settings && g.settings.reduceFlash); }
  function playing() { var g = IB.Game; return !!(g && g.mode === 'play'); }
  function sfx(name, x, z, gain, pitch) { if (IB.Audio) IB.Audio.play(name, { pos: { x: x, z: z }, gain: gain, pitch: pitch }); }
  B.I = 1; B.lvl = 1;

  // ---------------- card atlas (1024 px, 4 x 4 cells): red = paper, green = tint, black = ink ----------------
  var C = { burst: 0, cloud: 1, ring: 2, streak: 3, chip: 4, star: 5, dust: 6, lines: 7, dots: 8, zig0: 9, zig1: 10, bubble: 11, drip: 12, ember: 13, petal: 14, shine: 15 };
  var INK = '#000000', TINT = '#00FF00', PAPER = '#FF0000';
  function rngFrom(seed) { var s = seed >>> 0; return function () { s = (s + 0x6D2B79F5) | 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function starPath(ctx, cx, cy, R, rad) { ctx.beginPath(); for (var i = 0; i < rad.length; i++) { var a = i / rad.length * TAU - Math.PI / 2, r = R * rad[i]; if (i) ctx.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r); else ctx.moveTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r); } ctx.closePath(); }
  function blobPath(ctx, cx, cy, R, bumps, rr) {
    ctx.beginPath();
    for (var i = 0; i < bumps; i++) { var a = i / bumps * TAU; ctx.moveTo(cx + Math.cos(a) * R * 0.6 + R * 0.42 * rr[i], cy + Math.sin(a) * R * 0.6); ctx.arc(cx + Math.cos(a) * R * 0.6, cy + Math.sin(a) * R * 0.6, R * 0.42 * rr[i], 0, TAU); }
    ctx.moveTo(cx + R * 0.7, cy); ctx.arc(cx, cy, R * 0.7, 0, TAU);
  }
  function layered(ctx, path, scales, colors) { for (var i = 0; i < scales.length; i++) { path(scales[i]); ctx.fillStyle = colors[i]; ctx.fill(); } }
  function drawCards(ctx) {
    ctx.clearRect(0, 0, 1024, 1024);
    var r = rngFrom(4242), i, k;
    function at(cell) { return [(cell % 4) * 256 + 128, Math.floor(cell / 4) * 256 + 128]; }
    var p;
    // burst: 14-point starburst, paper star core
    p = at(C.burst); var rad = []; for (i = 0; i < 28; i++) rad.push(i % 2 ? 0.52 + r() * 0.12 : 0.88 + r() * 0.12);
    var rad2 = []; for (i = 0; i < 16; i++) rad2.push(i % 2 ? 0.5 : 1);
    starPath(ctx, p[0], p[1], 118, rad); ctx.fillStyle = INK; ctx.fill();
    starPath(ctx, p[0], p[1], 104, rad); ctx.fillStyle = TINT; ctx.fill();
    starPath(ctx, p[0], p[1], 64, rad2); ctx.fillStyle = PAPER; ctx.fill();
    // cloud: bumpy comic flash cloud
    p = at(C.cloud); var rr = []; for (i = 0; i < 9; i++) rr.push(0.8 + r() * 0.3);
    layered(ctx, function (s) { blobPath(ctx, p[0], p[1], 116 * s, 9, rr); }, [1, 0.86, 0.5], [INK, TINT, PAPER]);
    // ring: broken shock ring
    p = at(C.ring);
    ctx.lineWidth = 34; ctx.strokeStyle = INK; ctx.beginPath(); ctx.arc(p[0], p[1], 98, 0, TAU); ctx.stroke();
    ctx.lineWidth = 20; ctx.strokeStyle = TINT; ctx.beginPath(); ctx.arc(p[0], p[1], 98, 0, TAU); ctx.stroke();
    ctx.lineWidth = 6; ctx.strokeStyle = PAPER; ctx.beginPath(); ctx.arc(p[0], p[1], 103, 0, TAU); ctx.stroke();
    ctx.save(); ctx.globalCompositeOperation = 'destination-out';
    for (i = 0; i < 5; i++) { var g0 = i / 5 * TAU + r() * 0.6; ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.arc(p[0], p[1], 125, g0, g0 + 0.12 + r() * 0.1); ctx.closePath(); ctx.fill(); }
    ctx.restore();
    // streak: tapered spark / tracer, head at +x
    p = at(C.streak);
    function teardrop(x0, x1, hr) { ctx.beginPath(); ctx.moveTo(p[0] + x0, p[1]); ctx.quadraticCurveTo(p[0] + (x0 + x1) / 2, p[1] - hr * 1.05, p[0] + x1, p[1] - hr); ctx.arc(p[0] + x1, p[1], hr, -Math.PI / 2, Math.PI / 2); ctx.quadraticCurveTo(p[0] + (x0 + x1) / 2, p[1] + hr * 1.05, p[0] + x0, p[1]); ctx.closePath(); }
    teardrop(-120, 92, 30); ctx.fillStyle = INK; ctx.fill();
    teardrop(-106, 92, 21); ctx.fillStyle = TINT; ctx.fill();
    teardrop(-70, 94, 11); ctx.fillStyle = PAPER; ctx.fill();
    // chip: irregular shard
    p = at(C.chip); var cr = []; for (i = 0; i < 6; i++) cr.push(0.65 + r() * 0.35);
    layered(ctx, function (s) { ctx.beginPath(); for (var j = 0; j < 6; j++) { var a = j / 6 * TAU + 0.3; ctx[j ? 'lineTo' : 'moveTo'](p[0] + Math.cos(a) * 110 * cr[j] * s, p[1] + Math.sin(a) * 110 * cr[j] * s); } ctx.closePath(); }, [1, 0.8], [INK, TINT]);
    ctx.beginPath(); ctx.moveTo(p[0] - 50, p[1] - 30); ctx.lineTo(p[0] - 10, p[1] - 60); ctx.lineTo(p[0] - 5, p[1] - 30); ctx.closePath(); ctx.fillStyle = PAPER; ctx.fill();
    // star: 4-point sparkle
    p = at(C.star);
    var r4 = [1, 0.24, 1, 0.24, 1, 0.24, 1, 0.24];
    starPath(ctx, p[0], p[1], 120, r4); ctx.fillStyle = INK; ctx.fill();
    starPath(ctx, p[0], p[1], 100, r4); ctx.fillStyle = TINT; ctx.fill();
    starPath(ctx, p[0], p[1], 52, r4); ctx.fillStyle = PAPER; ctx.fill();
    // dust: soft cloud with a paper highlight
    p = at(C.dust); var dr = []; for (i = 0; i < 7; i++) dr.push(0.85 + r() * 0.25);
    blobPath(ctx, p[0], p[1], 112, 7, dr); ctx.fillStyle = INK; ctx.fill();
    blobPath(ctx, p[0], p[1], 100, 7, dr); ctx.fillStyle = TINT; ctx.fill();
    ctx.save(); blobPath(ctx, p[0], p[1], 100, 7, dr); ctx.clip(); ctx.fillStyle = PAPER; ctx.globalAlpha = 1;
    ctx.beginPath(); ctx.arc(p[0] - 40, p[1] - 44, 46, 0, TAU); ctx.fill(); ctx.restore();
    // lines: radial comic speed lines
    p = at(C.lines); ctx.fillStyle = INK;
    for (i = 0; i < 34; i++) { var a = i / 34 * TAU + r() * 0.12, w = 0.025 + r() * 0.035, r0 = 58 + r() * 36; ctx.beginPath(); ctx.moveTo(p[0] + Math.cos(a - w) * 126, p[1] + Math.sin(a - w) * 126); ctx.lineTo(p[0] + Math.cos(a) * r0, p[1] + Math.sin(a) * r0); ctx.lineTo(p[0] + Math.cos(a + w) * 126, p[1] + Math.sin(a + w) * 126); ctx.closePath(); ctx.fill(); }
    // dots: halftone burst (dots shrink outward)
    p = at(C.dots); ctx.fillStyle = TINT;
    for (var yy = -120; yy <= 120; yy += 14) for (var xx = -120; xx <= 120; xx += 14) {
      var ox = xx + ((yy / 14) & 1 ? 7 : 0), d = Math.sqrt(ox * ox + yy * yy); if (d > 118) continue;
      var dot = 6.4 * Math.pow(1 - d / 120, 0.6); if (dot < 0.8) continue;
      ctx.beginPath(); ctx.arc(p[0] + ox, p[1] + yy, dot, 0, TAU); ctx.fill();
    }
    // zig0 / zig1: lightning bolts along +x
    [C.zig0, C.zig1].forEach(function (cell, zi) {
      var q = at(cell), pts = [], n = 7;
      for (var j = 0; j <= n; j++) pts.push([q[0] - 118 + j / n * 236, q[1] + (j === 0 || j === n ? 0 : (j % 2 ? -1 : 1) * (18 + r() * 26) * (zi ? -1 : 1))]);
      var br = [pts[3], [pts[3][0] + 34, pts[3][1] + (zi ? -52 : 52)], [pts[3][0] + 62, pts[3][1] + (zi ? -70 : 74)]];
      [[24, INK], [14, TINT], [5, PAPER]].forEach(function (st) {
        ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.lineWidth = st[0]; ctx.strokeStyle = st[1];
        ctx.beginPath(); pts.forEach(function (pp, j) { ctx[j ? 'lineTo' : 'moveTo'](pp[0], pp[1]); }); ctx.stroke();
        ctx.lineWidth = st[0] * 0.7; ctx.beginPath(); br.forEach(function (pp, j) { ctx[j ? 'lineTo' : 'moveTo'](pp[0], pp[1]); }); ctx.stroke();
      });
    });
    // bubble
    p = at(C.bubble);
    ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(p[0], p[1], 92, 0, TAU); ctx.fill();
    ctx.fillStyle = TINT; ctx.beginPath(); ctx.arc(p[0], p[1], 76, 0, TAU); ctx.fill();
    ctx.fillStyle = PAPER; ctx.beginPath(); ctx.arc(p[0] - 30, p[1] - 30, 18, 0, TAU); ctx.fill();
    // drip: falling drop, round end down
    p = at(C.drip);
    function drop(s) { ctx.beginPath(); ctx.moveTo(p[0], p[1] - 112 * s); ctx.quadraticCurveTo(p[0] + 70 * s, p[1] + 10 * s, p[0] + 62 * s, p[1] + 40 * s); ctx.arc(p[0], p[1] + 40 * s, 62 * s, 0, Math.PI); ctx.quadraticCurveTo(p[0] - 70 * s, p[1] + 10 * s, p[0], p[1] - 112 * s); ctx.closePath(); }
    layered(ctx, drop, [1, 0.82], [INK, TINT]);
    ctx.fillStyle = PAPER; ctx.beginPath(); ctx.arc(p[0] - 22, p[1] + 34, 14, 0, TAU); ctx.fill();
    // ember
    p = at(C.ember);
    ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(p[0], p[1], 80, 0, TAU); ctx.fill();
    ctx.fillStyle = TINT; ctx.beginPath(); ctx.arc(p[0], p[1], 62, 0, TAU); ctx.fill();
    ctx.fillStyle = PAPER; ctx.beginPath(); ctx.arc(p[0], p[1], 32, 0, TAU); ctx.fill();
    // petal: pointed flare along +x
    p = at(C.petal);
    function leaf(s) { ctx.beginPath(); ctx.moveTo(p[0] - 118 * s, p[1]); ctx.quadraticCurveTo(p[0], p[1] - 70 * s, p[0] + 118 * s, p[1]); ctx.quadraticCurveTo(p[0], p[1] + 70 * s, p[0] - 118 * s, p[1]); ctx.closePath(); }
    layered(ctx, leaf, [1, 0.84, 0.5], [INK, TINT, PAPER]);
    // shine: thin 6-point glint
    p = at(C.shine);
    var r6 = []; for (i = 0; i < 12; i++) r6.push(i % 2 ? 0.16 : (i % 4 ? 0.7 : 1));
    starPath(ctx, p[0], p[1], 120, r6); ctx.fillStyle = INK; ctx.fill();
    starPath(ctx, p[0], p[1], 98, r6); ctx.fillStyle = TINT; ctx.fill();
    starPath(ctx, p[0], p[1], 50, r6); ctx.fillStyle = PAPER; ctx.fill();
    k = 0; return k;
  }
  var RECT = [];
  for (var ci = 0; ci < 16; ci++) RECT.push([(ci % 4) * 0.25 + 0.003, 1 - (Math.floor(ci / 4) + 1) * 0.25 + 0.003, 0.244, 0.244]);

  // ---------------- word atlas (1024 px, 2 x 6 cells of 512 x 170): full colour ----------------
  var WORDS = [
    ['KRAK!', '#F0443A', '#FFF8C2', '#FFB21E'], ['BLAM!', '#FFB21E', '#FFFDF7', '#FF7FB0'], ['ZZAP!', '#2F7BEA', '#FFFDF7', '#8ED2FF'],
    ['KA-BOOM!', '#F0443A', '#FFE15A', '#FF8A3D'], ['KRUNCH!', '#8A6CD8', '#FFFDF7', '#FFC23A'], ['POW!', '#FFC23A', '#FFFDF7', '#FF8A3D'],
    ['BOOM!', '#FF8A3D', '#FFF8C2', '#FFE15A'], ['FWOOM!', '#FFB21E', '#FFFDF7', '#FF8A3D'], ['CLANG!', '#12C7B6', '#FFFDF7', '#BFF3EC'],
    ['WHAM!', '#FF7FB0', '#FFFDF7', '#FFE15A'], ['KA-CHUNK!', '#5E4F8C', '#FFFDF7', '#FFB21E'], ['KA-POW!', '#12C7B6', '#FFE15A', '#FF8A3D']
  ];
  var W_ID = {}; WORDS.forEach(function (w, i) { W_ID[w[0]] = i; });
  var ALIAS = { BLAM: 'BLAM!', KRUNCH: 'KRUNCH!', CLANG: 'CLANG!', FWOOM: 'FWOOM!', ZAP: 'ZZAP!', 'KA-CHUNK': 'KA-CHUNK!', KRAK: 'KRAK!', POW: 'POW!', BOOM: 'BOOM!', WHAM: 'WHAM!' };
  B.WORDS = WORDS.map(function (w) { return w[0]; });
  var WRECT = [];
  for (ci = 0; ci < 12; ci++) WRECT.push([(ci % 2) * 0.5 + 0.002, 1 - ((Math.floor(ci / 2) + 1) * 170) / 1024 + 0.002, 0.496, 166 / 1024]);
  function shade(hex, k) { _c.set(hex); _c.multiplyScalar(k); return '#' + _c.getHexString(); }
  function drawWords(ctx) {
    ctx.clearRect(0, 0, 1024, 1024);
    var tmp = document.createElement('canvas'); tmp.width = 512; tmp.height = 170;
    var t = tmp.getContext('2d'), r = rngFrom(777);
    WORDS.forEach(function (w, i) {
      var x0 = (i % 2) * 512, y0 = Math.floor(i / 2) * 170, cx = x0 + 256, cy = y0 + 85;
      // starburst plate with a halftone shade toward the lower right
      var n = 22, rad = []; for (var k = 0; k < n; k++) rad.push(k % 2 ? 0.72 + r() * 0.1 : 0.95 + r() * 0.05);
      function plate(s) { ctx.beginPath(); for (var k2 = 0; k2 < n; k2++) { var a = k2 / n * TAU, rr = rad[k2] * s; ctx[k2 ? 'lineTo' : 'moveTo'](cx + Math.cos(a) * 236 * rr, cy + Math.sin(a) * 76 * rr); } ctx.closePath(); }
      ctx.save(); ctx.translate(cx, cy); ctx.rotate((i % 2 ? 1 : -1) * 0.035); ctx.translate(-cx, -cy);
      plate(1); ctx.fillStyle = '#15121C'; ctx.fill();
      plate(0.93); ctx.fillStyle = w[1]; ctx.fill();
      ctx.save(); plate(0.93); ctx.clip(); ctx.fillStyle = shade(w[1], 0.72);
      for (var yy = y0; yy < y0 + 170; yy += 9) for (var xx = x0; xx < x0 + 512; xx += 9) {
        var f = ((xx - x0) / 512 * 0.6 + (yy - y0) / 170 * 0.4) - 0.45; if (f <= 0) continue;
        ctx.beginPath(); ctx.arc(xx + ((yy / 9) & 1 ? 4.5 : 0), yy, Math.min(4.6, f * 9), 0, TAU); ctx.fill();
      }
      ctx.restore(); ctx.restore();
      // letters: italic lean, condensed to fit, gradient + halftone fill, ink drop shadow and outline
      var size = 112;
      ctx.font = t.font = '900 ' + size + 'px Archivo, "Arial Black", Impact, sans-serif';
      var tw = ctx.measureText(w[0]).width, sx = Math.min(1, 410 / tw);
      ctx.textAlign = t.textAlign = 'center'; ctx.textBaseline = t.textBaseline = 'middle'; ctx.lineJoin = t.lineJoin = 'round';
      function place(c, ox, oy) { c.setTransform(sx, 0, -0.2 * sx, 1, 0, 0); c.translate(0, 0); return [(ox) / sx + (oy) * 0.2, oy]; }
      t.setTransform(1, 0, 0, 1, 0, 0); t.clearRect(0, 0, 512, 170);
      var g = t.createLinearGradient(0, 30, 0, 140); g.addColorStop(0, w[2]); g.addColorStop(0.55, w[2]); g.addColorStop(0.56, w[3]); g.addColorStop(1, w[3]);
      var pp = place(t, 256, 90); t.fillStyle = g; t.fillText(w[0], pp[0], pp[1]);
      t.setTransform(1, 0, 0, 1, 0, 0); t.globalCompositeOperation = 'source-atop'; t.fillStyle = shade(w[3], 0.8);
      for (yy = 92; yy < 170; yy += 7) for (xx = 0; xx < 512; xx += 7) { var f2 = (yy - 92) / 60; t.beginPath(); t.arc(xx + ((yy / 7) & 1 ? 3.5 : 0), yy, Math.min(3.4, 0.6 + f2 * 3), 0, TAU); t.fill(); }
      t.globalCompositeOperation = 'source-over';
      ctx.save();
      pp = place(ctx, cx + 7, cy + 12); ctx.fillStyle = '#15121C'; ctx.fillText(w[0], pp[0], pp[1]);
      pp = place(ctx, cx, cy + 5); ctx.lineWidth = 15; ctx.strokeStyle = '#15121C'; ctx.strokeText(w[0], pp[0], pp[1]);
      ctx.restore();
      ctx.drawImage(tmp, x0, y0);
      // paper glint on the upper edge of the letters
      ctx.save(); pp = place(ctx, cx - 2, cy + 3); ctx.lineWidth = 2.5; ctx.strokeStyle = 'rgba(255,253,247,0.7)'; ctx.strokeText(w[0], pp[0], pp[1]); ctx.restore();
    });
  }

  // ---------------- materials ----------------
  var CARD_VS = [
    'attribute vec4 aRect;', 'attribute float aA;', 'varying vec2 vUv;', 'varying vec3 vTint;', 'varying float vA;',
    '#include <fog_pars_vertex>',
    'void main() {',
    '  vUv = aRect.xy + uv * aRect.zw;',
    '  vTint = vec3(1.0);',
    '  #ifdef USE_INSTANCING_COLOR', '  vTint = instanceColor;', '  #endif',
    '  vA = aA;',
    '  vec4 mvPosition = modelViewMatrix * instanceMatrix * vec4(position, 1.0);',
    '  gl_Position = projectionMatrix * mvPosition;',
    '  #include <fog_vertex>',
    '}'].join('\n');
  var CARD_FS = [
    'uniform sampler2D map;', 'uniform vec3 uInk;', 'uniform vec3 uPaper;', 'varying vec2 vUv;', 'varying vec3 vTint;', 'varying float vA;',
    '#include <fog_pars_fragment>',
    'void main() {',
    '  vec4 t = texture2D(map, vUv);',
    '  #ifdef WORDS',
    '  gl_FragColor = vec4(t.rgb, t.a * vA);',
    '  #else',
    '  float k = max(0.0, 1.0 - t.r - t.g);',
    '  gl_FragColor = vec4(uInk * k + vTint * t.g + uPaper * t.r, t.a * vA);',
    '  #endif',
    '  if (gl_FragColor.a < 0.02) discard;',
    '  #include <fog_fragment>',
    '}'].join('\n');
  function cardMaterial(tex, words) {
    var m = new THREE.ShaderMaterial({
      uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, { map: { value: null }, uInk: { value: new THREE.Color(PAL.ink) }, uPaper: { value: new THREE.Color(PAL.paper) } }]),
      vertexShader: CARD_VS, fragmentShader: CARD_FS, transparent: true, depthWrite: false, depthTest: !words, fog: !words, side: THREE.DoubleSide   // arcs flicker by mirroring
    });
    if (words) m.defines = { WORDS: '' };
    m.uniforms.map.value = tex;
    return m;
  }
  var PUFF_VS = [
    'attribute vec3 aHull;', 'attribute vec3 aP;', 'uniform float uOutBase;', 'uniform float uOutK;',
    'varying vec3 vN;', 'varying vec3 vObj;', 'varying float vHull;', 'varying vec3 vCol;', 'varying vec3 vP;',
    '#include <fog_pars_vertex>',
    'void main() {',
    '  vObj = position; vP = aP; vCol = vec3(1.0);',
    '  #ifdef USE_INSTANCING_COLOR', '  vCol = instanceColor;', '  #endif',
    '  mat4 mw = modelViewMatrix * instanceMatrix;',
    '  vec4 mvPosition = mw * vec4(position, 1.0);',
    '  vN = normalize((mw * vec4(normal, 0.0)).xyz);',
    '  vHull = 0.0;',
    '  if (dot(aHull, aHull) > 0.0) {',
    '    vec3 hd = (mw * vec4(aHull, 0.0)).xyz; float L = length(hd);',
    '    if (L > 1e-5) mvPosition.xyz += hd / L * max(uOutBase, uOutK * -mvPosition.z) * 1.3;',
    '    vHull = 1.0;',
    '  }',
    '  gl_Position = projectionMatrix * mvPosition;',
    '  #include <fog_vertex>',
    '}'].join('\n');
  var PUFF_FS = [
    'uniform vec3 uInk;', 'uniform vec3 uHL;', 'uniform vec3 uLight;', 'uniform vec3 uShade;', 'uniform float uDot;',
    'varying vec3 vN;', 'varying vec3 vObj;', 'varying float vHull;', 'varying vec3 vCol;', 'varying vec3 vP;',
    '#include <fog_pars_fragment>',
    'void main() {',
    '  float s = vP.z;',
    '  float n = 0.5 + (sin(vObj.x * 5.1 + s) + sin(vObj.y * 4.3 + s * 1.7) + sin(vObj.z * 6.7 - s * 0.9) + sin((vObj.x + vObj.y) * 3.3 + s * 2.3)) * 0.125;',
    '  if (n < vP.y) discard;',
    '  vec3 c;',
    '  if (vHull > 0.5 || (vP.y > 0.001 && n < vP.y + 0.075)) c = uInk;',   // ink rim, and ink on the ragged dissolve edge
    '  else {',
    '    float d = dot(normalize(vN), uLight);',
    '    c = vCol;',
    '    if (d > 0.42) c = mix(vCol, uHL, vP.x);',
    '    else if (d < -0.1) {',
    '      c = vCol * uShade;',
    '      vec2 q = fract(gl_FragCoord.xy / uDot) - 0.5;',
    '      if (dot(q, q) < 0.05 + clamp(-0.1 - d, 0.0, 0.8) * 0.2) c *= 0.66;',   // halftone dots, denser deeper in shadow
    '    }',
    '  }',
    '  gl_FragColor = vec4(c, 1.0);',
    '  #include <fog_fragment>',
    '}'].join('\n');
  function puffMaterial() {
    var R = IB.Render;
    var m = new THREE.ShaderMaterial({
      uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, {
        uInk: { value: new THREE.Color(PAL.ink) }, uHL: { value: new THREE.Color(0xFFF8D8) }, uShade: { value: new THREE.Vector3(0.68, 0.58, 0.8) },
        uLight: { value: new THREE.Vector3(-0.42, 0.78, 0.46).normalize() }, uDot: { value: 6 }, uOutBase: { value: 0.012 }, uOutK: { value: 0.002 } }]),
      vertexShader: PUFF_VS, fragmentShader: PUFF_FS, fog: true
    });
    if (R && R.worldOutline) { m.uniforms.uOutBase = R.worldOutline.uOutBase; m.uniforms.uOutK = R.worldOutline.uOutK; }
    return m;
  }
  // unit sphere + inverted hull in one geometry (normals kept for the toon bands)
  function puffGeometry() {
    var g = new THREE.SphereGeometry(1, 11, 8), pos = g.attributes.position.array, nor = g.attributes.normal.array, idx = g.index.array, n = pos.length / 3;
    var P = new Float32Array(n * 6), N = new Float32Array(n * 6), H = new Float32Array(n * 6), I = new Uint16Array(idx.length * 2);
    for (var i = 0; i < n * 3; i++) { P[i] = P[n * 3 + i] = pos[i]; N[i] = N[n * 3 + i] = nor[i]; H[n * 3 + i] = pos[i]; }
    for (i = 0; i < idx.length; i += 3) {
      I[i] = idx[i]; I[i + 1] = idx[i + 1]; I[i + 2] = idx[i + 2];
      I[idx.length + i] = idx[i] + n; I[idx.length + i + 1] = idx[i + 2] + n; I[idx.length + i + 2] = idx[i + 1] + n;
    }
    var out = new THREE.BufferGeometry();
    out.setAttribute('position', new THREE.BufferAttribute(P, 3));
    out.setAttribute('normal', new THREE.BufferAttribute(N, 3));
    out.setAttribute('aHull', new THREE.BufferAttribute(H, 3));
    out.setIndex(new THREE.BufferAttribute(I, 1));
    g.dispose();
    return out;
  }
  function instanced(geo, mat, n, scene) {
    var im = new THREE.InstancedMesh(geo, mat, n);
    im.instanceMatrix.setUsage(THREE.DynamicDrawUsage); im.frustumCulled = false;
    for (var i = 0; i < n; i++) im.setMatrixAt(i, ZERO);
    im.count = 0; im.visible = false;
    if (scene) scene.add(im);
    return im;
  }
  function instColor(im, n) { var a = new THREE.InstancedBufferAttribute(new Float32Array(n * 3).fill(1), 3); a.setUsage(THREE.DynamicDrawUsage); im.instanceColor = a; return a; }
  function instAttr(geo, name, n, size) { var a = new THREE.InstancedBufferAttribute(new Float32Array(n * size), size); a.setUsage(THREE.DynamicDrawUsage); geo.setAttribute(name, a); return a; }

  // ---------------- debris geometry (procedural, ink hull) ----------------
  var STEEL = 0xB9B4C6, DARK = 0x3A3846;
  function gearGeo() {
    var g = new IB.Geo(), m = new THREE.Matrix4();
    g.cyl(0, -0.025, 0, 0.1, 0.1, 0.05, 12, STEEL, { hullScale: 0.7 });
    for (var i = 0; i < 8; i++) { g.setMatrix(m.makeRotationY(i / 8 * TAU)); g.box(0.118, 0, 0, 0.045, 0.05, 0.04, STEEL, { hullScale: 0.7 }); }
    g.setMatrix(null); g.cyl(0, -0.032, 0, 0.034, 0.034, 0.064, 8, PAL.amber, { hull: false });
    return g.build();
  }
  function boltGeo() {
    var g = new IB.Geo();
    g.cyl(0, 0.03, 0, 0.05, 0.05, 0.04, 6, STEEL, { hullScale: 0.7 });
    g.cyl(0, -0.08, 0, 0.02, 0.02, 0.11, 6, 0x8F8A9C, { hullScale: 0.6 });
    return g.build();
  }
  function plateGeo() {
    var g = new IB.Geo();
    g.box(0, 0, 0, 0.26, 0.026, 0.18, 0xFFFFFF, { hullScale: 0.7 });
    g.box(-0.09, 0.016, -0.055, 0.03, 0.012, 0.03, DARK, { hull: false }); g.box(0.09, 0.016, 0.055, 0.03, 0.012, 0.03, DARK, { hull: false });
    return g.build();
  }
  function springGeo() {
    var g = new IB.Geo(), m = new THREE.Matrix4();
    for (var i = 0; i < 5; i++) { g.setMatrix(m.makeRotationZ(0.35).setPosition(0, -0.08 + i * 0.04, 0)); g.cyl(0, -0.008, 0, 0.06, 0.06, 0.016, 10, STEEL, { hullScale: 0.5, noTop: false }); }
    g.setMatrix(null); return g.build();
  }
  function casingGeo() {
    var g = new IB.Geo();
    g.cyl(0, -0.012, 0, 0.0066, 0.0066, 0.024, 8, 0xE9B54A, { hullScale: 0.45 });
    g.cyl(0, -0.0135, 0, 0.0072, 0.0072, 0.003, 8, 0xB07A22, { hull: false });
    return g.build();
  }
  function canisterGeo() {
    var g = new IB.Geo(), m = new THREE.Matrix4();
    g.cyl(0, 0.02, 0, 0.3, 0.3, 0.8, 16, PAL.red);
    g.cyl(0, 0.13, 0, 0.312, 0.312, 0.06, 16, DARK, { hull: false });
    g.cyl(0, 0.66, 0, 0.312, 0.312, 0.06, 16, DARK, { hull: false });
    g.cyl(0, 0.27, 0, 0.306, 0.306, 0.3, 16, PAL.paper, { hull: false, noTop: true, noBottom: true });
    for (var i = 0; i < 2; i++) {
      g.setMatrix(m.identity().makeRotationY(i * Math.PI).multiply(new THREE.Matrix4().makeTranslation(0, 0.42, 0.305)).multiply(new THREE.Matrix4().makeRotationZ(Math.PI / 4)));
      g.box(0, 0, 0, 0.13, 0.13, 0.02, PAL.amber, { hullScale: 0.6 });
      g.box(0, 0, 0.012, 0.05, 0.05, 0.01, PAL.ink, { hull: false });
    }
    g.setMatrix(null);
    g.cyl(0, 0.82, 0, 0.27, 0.2, 0.06, 14, DARK);
    g.cyl(0.11, 0.86, 0, 0.04, 0.04, 0.08, 8, PAL.amber, { hullScale: 0.7 });
    return g.build();
  }

  // ---------------- pools ----------------
  var CARD_CAP = 480, PUFF_CAP = 200, WORD_CAP = 6, EVENT_CAP = 48, FALL_CAP = 12, CAN_CAP = 40, CASE_CAP = 24;
  var cards = [], puffs = [], words = [], events = [], fallers = [], cans = [], casings = [];
  var M_BILL = 0, M_GROUND = 1, M_STREAK = 2, M_SEG = 3, M_TRACER = 4;
  var E_OUT = 0, E_POP = 1, E_LIN = 2;
  var P_FIRE = 0, P_SMOKE = 1;
  var bins = [];   // debris bins: {mesh, pool, hi}
  var BIN = {};
  var nCards = 0, cardHint = 0, cardHi = -1, nPuffs = 0, puffHint = 0, puffHi = -1;

  function newCard() { return { on: false, idx: 0, mode: 0, cell: 0, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, g: 0, drag: 0, t: 0, life: 1, s0: 0, s1: 0, ease: 0, fd: 0.6, a0: 1, rot: 0, vr: 0, w: 0.1, st: 0, ex: 0, ey: 0, ez: 0, sp: 0, seg: 0, flick: 0, ft: 0, floor: -99, r: 1, gg: 1, b: 1, dx: 1, dy: 0, dz: 0 }; }
  function card(cell, mode, x, y, z, life, s0, s1, color) {
    var limit = Math.round(CARD_CAP * (0.45 + 0.55 * ps()));
    if (!B.ready || nCards >= limit) return DUMMY_CARD;
    var c = null, i;
    for (i = cardHint; i < CARD_CAP; i++) if (!cards[i].on) { c = cards[i]; cardHint = i + 1; break; }
    if (!c) return DUMMY_CARD;
    c.on = true; nCards++; c.idx = i;
    c.mode = mode; c.cell = cell; c.x = x; c.y = y; c.z = z; c.vx = c.vy = c.vz = 0; c.g = 0; c.drag = 0; c.t = 0; c.life = life;
    c.s0 = s0; c.s1 = s1; c.ease = E_OUT; c.fd = 0.6; c.a0 = 1; c.rot = Math.random() * TAU; c.vr = 0; c.w = 0.06; c.st = 0;
    c.flick = 0; c.ft = 0; c.floor = -99; c.dx = 1; c.dy = 0; c.dz = 0;
    _c.setHex(color === undefined ? 0xFFFFFF : color); c.r = _c.r; c.gg = _c.g; c.b = _c.b;
    var R = RECT[cell]; B.cardRect.setXYZW(i, R[0], R[1], R[2], R[3]);
    B.cardRect.needsUpdate = true;
    if (i > cardHi) cardHi = i;
    return c;
  }
  function roomy() { return nCards < CARD_CAP * (0.45 + 0.55 * ps()) * 0.7; }
  function freeCard(c) { c.on = false; nCards--; if (c.idx < cardHint) cardHint = c.idx; }

  var DUMMY_CARD = newCard();   // returned when the pool is full: same shape, so call sites stay monomorphic
  function newPuff() { return { on: false, idx: 0, kind: 0, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, buoy: 0, drag: 0, t: 0, life: 1, s1: 1, sq: 1, seed: 0, hl: 0.6, ramp: 0 }; }
  function puff(kind, x, y, z, s1, life, delay) {
    var limit = Math.round(PUFF_CAP * (0.4 + 0.6 * ps()));
    if (!B.ready || nPuffs >= limit) return DUMMY_PUFF;
    var p = null, i;
    for (i = puffHint; i < PUFF_CAP; i++) if (!puffs[i].on) { p = puffs[i]; puffHint = i + 1; break; }
    if (!p) return DUMMY_PUFF;
    p.on = true; nPuffs++; p.idx = i; p.kind = kind; p.x = x; p.y = y; p.z = z; p.vx = p.vy = p.vz = 0; p.t = -(delay || 0); p.life = life; p.s1 = s1;
    p.sq = 0.85 + Math.random() * 0.25; p.seed = Math.random() * 50; p.hl = kind === P_FIRE ? 0.7 : 0.28;
    p.buoy = kind === P_FIRE ? 2.2 : 1.1; p.drag = kind === P_FIRE ? 3.2 : 1.4; p.ramp = 1;
    if (i > puffHi) puffHi = i;
    return p;
  }
  var DUMMY_PUFF = newPuff();
  function freePuff(p) { p.on = false; nPuffs--; if (p.idx < puffHint) puffHint = p.idx; }

  function newDeb(i) { return { on: false, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, rx: 0, ry: 0, rz: 0, wx: 0, wy: 0, wz: 0, t: 0, life: 2, s: 1, rest: 0.05, smoke: -1, idx: i }; }
  var DUMMY_DEB = newDeb(0);
  function makeBin(name, geo, mat, cap, scene) {
    var im = instanced(geo, mat, cap, scene); instColor(im, cap);
    var bin = { name: name, mesh: im, pool: [], hi: -1, n: 0, cap: cap };
    for (var i = 0; i < cap; i++) bin.pool.push(newDeb(i));
    bins.push(bin); BIN[name] = bin;
    return bin;
  }
  function debris(bin, x, y, z, power, color, scale) {
    if (!bin) return DUMMY_DEB;
    var e = null;
    for (var i = 0; i < bin.cap; i++) if (!bin.pool[i].on) { e = bin.pool[i]; break; }
    if (!e) return DUMMY_DEB;
    e.on = true; bin.n++; e.t = 0; e.life = rnd(1.5, 2.3); e.x = x; e.y = y; e.z = z;
    var a = Math.random() * TAU, sp = power * rnd(0.45, 1.1);
    e.vx = Math.cos(a) * sp; e.vz = Math.sin(a) * sp; e.vy = rnd(3, 6.5) * Math.min(1.5, 0.6 + power * 0.12);
    e.rx = Math.random() * TAU; e.ry = Math.random() * TAU; e.rz = Math.random() * TAU;
    e.wx = rnd(-16, 16); e.wy = rnd(-12, 12); e.wz = rnd(-16, 16);
    e.s = (scale || 1) * (bin.name.indexOf('BOT_') === 0 ? 1 : 1.6); e.rest = 0.05 * e.s; e.smoke = Math.random() < 0.35 + 0.15 * (B.I - 1) ? 0 : -1;
    bin.mesh.setColorAt(e.idx, _c.setHex(color === undefined ? 0xFFFFFF : color)); bin.mesh.instanceColor.needsUpdate = true;
    if (e.idx > bin.hi) bin.hi = e.idx;
    return e;
  }

  // ---------------- explosion flavours ----------------
  var FLAV = {
    crawler: { S: 1.0, words: [0, 5, 4], debris: 5, parts: ['BOT_CRAWLER_Leg'], nParts: 2, color: 0xC9CFD6, sound: 0.6 },
    gunner: { S: 1.32, words: [1, 0, 6], debris: 7, parts: ['BOT_GUNNER_Lid', 'BOT_GUNNER_Wheel'], nParts: 2, color: 0x4FA36A, sound: 0.75 },
    bomber: { S: 0.75, words: null, debris: 3, parts: ['BOT_BOMBER_Cap'], nParts: 1, color: 0x3E86D8, sound: 0 },
    drone: { S: 1.18, words: [0, 6, 9], debris: 5, parts: ['BOT_DRONE_Rotor', 'BOT_DRONE_Lid'], nParts: 2, color: 0xE2483D, sound: 0.8 },
    // Soldier: armour plates in its own colour, the helmet pops off spinning, a blue burst where the shield cell blows
    soldier: { S: 1.4, words: [0, 4, 10], debris: 8, parts: ['BOT_SOLDIER_ArmL', 'BOT_SOLDIER_Shin'], nParts: 2, color: 0x9EA5B0, sound: 0.8 },
    soldierHelm: { S: 1, words: null, debris: 0, parts: ['BOT_SOLDIER_HelmA', 'BOT_SOLDIER_HelmB', 'BOT_SOLDIER_HelmC'], nParts: 0, color: 0xFFFFFF, sound: 0 },
    // Blade Bot: the hub flies off with its blade still turning, sparks (blue arcs for the Voltaxe)
    blader: { S: 1.2, words: [8, 0, 5], debris: 6, parts: ['BOT_BLADER_Hub'], nParts: 1, color: 0x8A6CD8, sound: 0.75 },
    bladerWpn: { S: 1, words: null, debris: 0, parts: ['BOT_BLADER_Katana', 'BOT_BLADER_Axe'], nParts: 0, color: 0xFFFFFF, sound: 0 },
    blast: { S: 1.75, words: [3, 6, 7], debris: 5, parts: null, nParts: 0, color: 0x3E86D8, big: true, sound: 0 },
    canister: { S: 2.0, words: [3, 6, 7], debris: 6, parts: null, nParts: 0, color: PAL.red, big: true, sound: 0 },
    chain: { S: 0.95, words: [4, 10], debris: 2, parts: null, nParts: 0, color: 0xFFB21E, sound: 0 },
    pop: { S: 0.48, words: null, debris: 1, parts: null, nParts: 0, color: 0xC9CFD6, sound: 0.25 },
    big: { S: 1.6, words: [3, 6, 9], debris: 9, parts: null, nParts: 0, color: 0x7D8796, big: true, sound: 1 }
  };
  B.FLAV = FLAV;
  var F_WORD = 1, F_SCORCH = 2, F_RING = 4, F_QUIET = 8, F_NOCHAIN = 16, F_NOSHAKE = 32;
  var SPARK_COLS = [0xFFE15A, PAL.amber, 0xFFFDF7, PAL.tangerine];

  function sparkBurst(x, y, z, n, speed, nx, ny, nz, spread, color, life) {
    for (var i = 0; i < n; i++) {
      var c = card(C.streak, M_STREAK, x, y, z, (life || 0.4) * rnd(0.6, 1.2), 0.05, 0.02, color === undefined ? SPARK_COLS[(Math.random() * 4) | 0] : color);
      var dx = nx + rnd(-spread, spread), dy = ny + rnd(-spread, spread) + 0.25, dz = nz + rnd(-spread, spread), L = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1, sp = speed * rnd(0.5, 1.15);
      c.vx = dx / L * sp; c.vy = dy / L * sp; c.vz = dz / L * sp; c.g = 14; c.drag = 1.2; c.w = 0.06 + speed * 0.004; c.st = 0.055; c.fd = 0.5; c.floor = 0.02; c.ease = E_LIN;
    }
  }
  B.sparks = function (x, y, z, nx, ny, nz, n, color) { sparkBurst(x, y, z, cnt(n), 5, nx || 0, ny || 0.4, nz || 0, 0.9, color, 0.32); };

  // flat flash cards sit a little in front of what they flash (toward the camera) so the fireball never hides them
  function flash(x, y, z, size, color, life, cell) {
    var red = reduce(), cam = IB.Render && IB.Render.camera;
    if (cam) {
      var dx = cam.position.x - x, dy = cam.position.y - y, dz = cam.position.z - z, d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1, o = Math.min(size * 0.3, d * 0.4);
      x += dx / d * o; y += dy / d * o; z += dz / d * o;
    }
    var c = card(cell === undefined ? C.burst : cell, M_BILL, x, y, z, life, size * 0.35, size * (red ? 0.8 : 1), color);
    c.ease = E_POP; c.a0 = red ? 0.45 : 1; c.fd = 0.35;
    return c;
  }

  /* the comic explosion: layered flash, toon fire puffs, ink smoke, sparks, embers, debris, ring, scorch, word,
     shake / hit-stop, and (later levels) a chain of secondary scrap pops */
  function explode(x, y, z, f, sMul, flags, partColor) {
    if (!B.ready) return;
    var I = B.I, S = f.S * (sMul || 1), sz = S * (0.88 + 0.12 * I), red = reduce(), i, c, p, a, e;
    // the floor under the blast: a deck or stair top on levels with walkable surfaces (zones.js), else the ground (0)
    var fy = IB.Zones && IB.Zones.floorY ? IB.Zones.floorY(x, z, y) : 0;
    var ground = y - fy < 1.7, big = S * I >= 1.6;
    // 1. flash: amber starburst, red cloud behind, speed lines and halftone dots for the big ones
    flash(x, y, z, sz * 1.8, PAL.amber, 0.16);
    c = flash(x, y, z, sz * 2.25, PAL.red, 0.17, C.cloud); c.t = -0.02;
    if (big) {
      c = card(C.lines, M_BILL, x, y, z, 0.16, sz * 2.2, sz * 3.6, PAL.ink); c.a0 = red ? 0.45 : 0.9; c.fd = 0.3;
      c = card(C.dots, M_BILL, x, y, z, 0.24, sz * 1.6, sz * 3.2, PAL.amber); c.a0 = red ? 0.4 : 0.85; c.fd = 0.4;
    }
    // 2. toon fire puffs
    var nf = Math.max(3, cnt((4 + 3.2 * S) * Math.pow(I, 0.8)));
    for (i = 0; i < nf; i++) {
      a = Math.random() * TAU; var el = rnd(-0.2, 1), rr = rnd(0.05, 0.42) * S;
      p = puff(P_FIRE, x + Math.cos(a) * rr, y + el * 0.3 * S + 0.05, z + Math.sin(a) * rr, rnd(0.3, 0.52) * sz * (i ? 1 : 1.35), rnd(0.36, 0.56), i * 0.012);
      p.vx = Math.cos(a) * rnd(1, 2.6) * S; p.vz = Math.sin(a) * rnd(1, 2.6) * S; p.vy = rnd(0.4, 2.4) * S;
    }
    // 3. ink smoke: billows out of the top of the fireball and climbs as a column after the fire is gone
    var ns = Math.max(2, cnt((3 + 2.6 * S) * Math.pow(I, 0.7)));
    for (i = 0; i < ns; i++) {
      a = Math.random() * TAU; rr = rnd(0.05, 0.45) * S;
      p = puff(P_SMOKE, x + Math.cos(a) * rr, y + rnd(0.25, 0.75) * S, z + Math.sin(a) * rr, rnd(0.4, 0.7) * sz, rnd(1.1, 1.7), rnd(0.05, 0.16) + i * 0.025);
      p.vx = Math.cos(a) * rnd(0.3, 1.1); p.vz = Math.sin(a) * rnd(0.3, 1.1); p.vy = rnd(1.4, 2.6) * Math.sqrt(S);
    }
    // 4. sparks + embers
    sparkBurst(x, y, z, cnt((8 + 7 * S) * I), 9 * Math.sqrt(S), 0, 0.35, 0, 1, undefined, 0.5);
    var ne = roomy() ? cnt(3 * S * I) : 0;
    for (i = 0; i < ne; i++) {
      c = card(C.ember, M_BILL, x + rnd(-0.3, 0.3) * S, y + rnd(0, 0.4) * S, z + rnd(-0.3, 0.3) * S, rnd(0.6, 1.1), 0.07, 0.03, Math.random() < 0.5 ? PAL.amber : 0xFFE15A);
      c.vx = rnd(-2.5, 2.5); c.vy = rnd(2, 5); c.vz = rnd(-2.5, 2.5); c.g = 5; c.drag = 1.5; c.ease = E_LIN;
    }
    // 5. debris: plates in the robot's colour, gears, bolts, springs, and the robot's own parts
    var nd = Math.round(f.debris * I * Math.sqrt(ps()) * rnd(0.8, 1.2)), pw = 2.6 + 1.6 * S;
    for (i = 0; i < nd; i++) {
      var k = Math.random();
      e = k < 0.38 ? debris(BIN.plate, x, y, z, pw, partColor || f.color, rnd(0.7, 1.15)) : k < 0.62 ? debris(BIN.gear, x, y, z, pw, 0xFFFFFF, rnd(0.7, 1.3)) :
        k < 0.88 ? debris(BIN.bolt, x, y, z, pw, 0xFFFFFF, rnd(0.8, 1.3)) : debris(BIN.spring, x, y, z, pw, 0xFFFFFF, rnd(0.8, 1.1));
    }
    if (f.binList) for (i = 0; i < f.nParts; i++) debris(f.binList[i % f.binList.length], x, y, z, pw * 0.8, 0xFFFFFF, 1);
    // 6. shock ring along the floor (an air ring when it blows up high)
    if (flags & F_RING) {
      if (ground) { c = card(C.ring, M_GROUND, x, fy + 0.05, z, 0.32, sz * 0.5, sz * 3.4, 0xFFF1D6); c.fd = 0.45; }
      else { c = card(C.ring, M_BILL, x, y, z, 0.26, sz * 0.4, sz * 2.8, 0xFFF1D6); c.fd = 0.4; }
      // dust kicked out along the floor
      if (ground) { var nk = cnt(3 + 2 * S); for (i = 0; i < nk; i++) { a = Math.random() * TAU; c = card(C.dust, M_BILL, x + Math.cos(a) * 0.4 * S, fy + 0.25, z + Math.sin(a) * 0.4 * S, rnd(0.6, 0.9), 0.3 * S, rnd(0.7, 1.1) * S, B.dustCol); c.vx = Math.cos(a) * 3.2 * S; c.vz = Math.sin(a) * 3.2 * S; c.vy = 0.4; c.drag = 3.5; c.fd = 0.45; c.a0 = 0.9; } }
    }
    // 7. scorch on the floor
    if ((flags & F_SCORCH) && ground && FX.decal) FX.decal(x, fy + 0.012, z, 0, 1, 0, 'scorch', 1.3 * sz + 0.3);
    // 8. the word
    if ((flags & F_WORD) && !(flags & F_QUIET) && f.words && Math.random() < B.wordChance(B.lvl, f.big))
      B.word(f.words[(Math.random() * f.words.length) | 0], x, y + 0.6 * S + 0.55, z, 1.2 + 0.6 * S + 0.12 * (I - 1), f.big);
    // 9. shake, hit-stop, screen ink
    if (!(flags & (F_QUIET | F_NOSHAKE))) feel(x, y, z, S);
    // 10. scrap chain: secondary pops ripple out of the wreck (cosmetic)
    if (!(flags & F_NOCHAIN) && f !== FLAV.pop && Math.random() < B.chainChance(B.lvl)) {
      var np = 1 + Math.floor(Math.random() * I + 0.3 * (I - 1));
      for (i = 0; i < np; i++) { a = Math.random() * TAU; var d = rnd(0.7, 1.9) * Math.max(0.8, S); event(1, x + Math.cos(a) * d, Math.max(0.3, y * 0.6), z + Math.sin(a) * d, 0.16 + i * rnd(0.1, 0.2), rnd(0.8, 1.2)); }
    }
    if (f.sound) sfx('boom', x, z, f.sound * 0.55, 1.25 - 0.15 * S);
  }
  B.explode = function (x, y, z, kind, sMul, quiet) { explode(x, y, z, FLAV[kind] || FLAV.crawler, sMul, F_WORD | F_SCORCH | F_RING | (quiet ? F_QUIET : 0)); };

  // camera feel: trauma by distance, a short hit-stop on big close blasts, screen ink / flash
  function feel(x, y, z, S) {
    var g = IB.Game; if (!g || g.mode !== 'play' || !g.player) return;
    var p = g.player, dx = p.x - x, dy = p.y + 1.5 - y, dz = p.z - z, d = Math.sqrt(dx * dx + dy * dy + dz * dz);
    var reach = 9 + 7 * S, k = Math.max(0, 1 - d / reach);
    if (k <= 0) return;
    if (g.addTrauma) g.addTrauma(Math.min(0.75, (0.12 + 0.3 * S) * k * k * (0.9 + 0.1 * B.I)));
    if (S >= 1.5 && d < 3 + 3 * S) g.hitstop = Math.max(g.hitstop || 0, 0.03 + 0.008 * Math.min(2.2, S));   // a beat of hit-stop on big close blasts
    if (d < 2.5 + 2 * S) Scr.kick(Math.min(1, (1 - d / (2.5 + 2 * S)) * 0.6 + 0.3 * S / 2));
  }

  // ---------------- words ----------------
  B.wordT = 9;
  B.word = function (id, x, y, z, size, force) {
    if (!B.ready) return;
    if (typeof id === 'string') { var nm = ALIAS[id] || id; id = W_ID[nm]; if (id === undefined) id = 0; }
    if (!force && B.wordT < 0.14) return;
    B.wordT = 0;
    var w = words[0], i;
    for (i = 0; i < WORD_CAP; i++) { if (!words[i].on) { w = words[i]; break; } if (words[i].t > w.t) w = words[i]; }
    w.on = true; w.t = 0; w.x = x; w.y = y; w.z = z; w.size = size || 2; w.id = id; w.tilt = rnd(-0.16, 0.16);
    var R = WRECT[id]; B.wordRect.setXYZW(w.idx, R[0], R[1], R[2], R[3]); B.wordRect.needsUpdate = true;
  };

  // ---------------- events (delayed pops, fireworks) ----------------
  function event(kind, x, y, z, t, s) {
    for (var i = 0; i < EVENT_CAP; i++) { var e = events[i]; if (!e.on) { e.on = true; e.kind = kind; e.x = x; e.y = y; e.z = z; e.t = t; e.s = s || 1; return e; } }
    return null;
  }
  var FW_COLS = [PAL.teal, PAL.bubblegum, PAL.amber, PAL.purple, 0x8ED2FF, PAL.green];
  function firework(x, y, z, s, first) {
    var col = FW_COLS[(Math.random() * FW_COLS.length) | 0], col2 = FW_COLS[(Math.random() * FW_COLS.length) | 0], i, c;
    flash(x, y, z, 2.2 * s, col, 0.18);
    c = card(C.ring, M_BILL, x, y, z, 0.4, 0.6 * s, 4.2 * s, col2); c.fd = 0.4;
    var n = cnt(16 + 6 * B.I);
    for (i = 0; i < n; i++) {
      var a = i / n * TAU + rnd(-0.1, 0.1), e = rnd(-0.9, 0.9), sp = rnd(5, 8) * s;
      c = card(i % 3 ? C.star : C.streak, i % 3 ? M_BILL : M_STREAK, x, y, z, rnd(0.8, 1.3), 0.32 * s, 0.12 * s, i % 2 ? col : col2);
      c.vx = Math.cos(a) * Math.cos(e) * sp; c.vy = Math.sin(e) * sp + 1; c.vz = Math.sin(a) * Math.cos(e) * sp; c.g = 3.2; c.drag = 1.8; c.w = 0.09; c.st = 0.06; c.ease = E_LIN; c.vr = rnd(-6, 6);
    }
    if (first) B.word(Math.random() < 0.5 ? 11 : 9, x, y + 1.2, z, 3.2, true);
    sfx('boom', x, z, 0.3, 1.7);
  }
  function confetti(x, y, z, n, spread, lift) {
    for (var i = 0; i < n; i++) {
      var c = card(Math.random() < 0.7 ? C.chip : C.star, M_BILL, x + rnd(-spread, spread), y, z + rnd(-0.5, 0.5), rnd(1.4, 2.2), rnd(0.1, 0.16), rnd(0.1, 0.16), FW_COLS[(Math.random() * FW_COLS.length) | 0]);
      c.vx = rnd(-2.5, 2.5); c.vy = rnd(3, 6.5) * (lift || 1); c.vz = rnd(-2.5, 2.5); c.g = 5.5; c.drag = 1.6; c.vr = rnd(-9, 9); c.fd = 0.75; c.ease = E_LIN; c.floor = 0.03;
    }
  }

  // ---------------- public effect hooks ----------------
  /* robot death; quiet = test / zone-wipe kills (no words, no shake) */
  B.robotDeath = function (r, quiet) {
    if (!B.ready) return;
    var v = IB.AI && IB.AI.VIS[r.type], f = FLAV[r.type] || FLAV.crawler, sMul = 1;
    if (!FLAV[r.type] && v) sMul = Math.max(0.9, Math.min(2.2, v.radius * 2.3));
    var y = r.y + (v ? (v.y0 + v.y1) * 0.5 : 0.5), fl = F_WORD | F_SCORCH | F_RING | (quiet ? F_QUIET : 0);
    if (r.type === 'drone' && r.y > 0.9) {
      // shot out of the air: a crackle, then it drops and blows up where it lands (see fallers)
      flash(r.x, y, r.z, 1.1, 0x8ED2FF, 0.1, C.cloud);
      sparkBurst(r.x, y, r.z, cnt(10 * B.I), 6, 0, 0.2, 0, 1, undefined, 0.35);
      var pf = puff(P_SMOKE, r.x, y, r.z, 0.35, 0.8, 0); pf.vy = 0.5;
      if (!quiet && Math.random() < 0.6) B.word(2, r.x, y + 0.6, r.z, 1.4);
      for (var i = 0; i < FALL_CAP; i++) { var fa = fallers[i]; if (fa.on) continue; fa.on = true; fa.x = r.x; fa.y = y; fa.z = r.z; fa.vy = 0; fa.t = 0; fa.smoke = 0; fa.quiet = !!quiet; fa.base = r.fy || 0; break; }
      return;
    }
    if (r.type === 'bomber' && !quiet) { flash(r.x, y, r.z, 1.2, PAL.paper, 0.08, C.cloud); return; }   // its own blast (projectiles) does the rest
    if (r.type === 'soldier') {
      explode(r.x, y, r.z, f, sMul, fl, r.tintHex);
      var hb = BIN['BOT_SOLDIER_Helm' + (r.helm || 'A')], he = debris(hb, r.x, r.y + 1.6, r.z, 1.5, r.tintHex, 1);
      he.vy = rnd(7, 9); he.wx = rnd(-20, 20); he.wz = rnd(-20, 20);
      if (r.maxShield > 0) { var sc = card(C.ring, M_BILL, r.x, y + 0.2, r.z, 0.3, 0.3, 2.6, 0x5FC2FF); sc.fd = 0.4; sparkBurst(r.x, y + 0.2, r.z, cnt(10), 6, 0, 0.4, 0, 1, 0x8ED2FF, 0.35); }
      return;
    }
    if (r.type === 'blader') {
      explode(r.x, y, r.z, f, sMul, fl);
      var we = debris(BIN[r.weaponId === 'eaxe' ? 'BOT_BLADER_Axe' : 'BOT_BLADER_Katana'], r.x, r.y + 0.9, r.z, 4, 0xFFFFFF, 1);
      we.vy = rnd(6, 8); we.wy = rnd(25, 40) * (Math.random() < 0.5 ? -1 : 1);
      if (r.weaponId === 'eaxe') { B.zap(r.x, y + 0.3, r.z, 1.4); sparkBurst(r.x, y, r.z, cnt(12), 7, 0, 0.3, 0, 1, 0x8ED2FF, 0.4); }
      return;
    }
    explode(r.x, y, r.z, f, sMul, fl);
  };
  /* a blast from IB.Projectiles (Bomber, canister, any splash weapon) */
  B.blast = function (x, y, z, R, srcType) {
    var f = srcType === 'canister' ? FLAV.canister : FLAV.blast;
    explode(x, y, z, f, R / 3.2, F_WORD | F_SCORCH | F_RING);
  };
  /* bullet hits a robot */
  B.robotHit = function (r, x, y, z, dx, dy, dz, zone, killed) {
    if (!B.ready) return;
    var core = zone === 'core' || zone === 'head', f = FLAV[r.type] || FLAV.crawler, c, i;
    sparkBurst(x, y, z, cnt(core ? 8 : 4), core ? 8 : 6, -dx, -dy, -dz, 0.9, undefined, core ? 0.38 : 0.28);
    flash(x - dx * 0.05, y - dy * 0.05, z - dz * 0.05, core ? 0.75 : 0.4, core ? PAL.amber : 0xFFF1D6, core ? 0.1 : 0.06, core ? C.burst : C.cloud);
    var nc = cnt(core ? 2 : 1);
    for (i = 0; i < nc; i++) { c = card(C.chip, M_BILL, x, y, z, rnd(0.4, 0.6), 0.07, 0.05, f.color); c.vx = -dx * 2 + rnd(-2, 2); c.vy = rnd(1.5, 3.5); c.vz = -dz * 2 + rnd(-2, 2); c.g = 14; c.vr = rnd(-14, 14); c.ease = E_LIN; c.floor = 0.03; }
    if (core) {
      c = card(C.ring, M_BILL, x, y, z, 0.14, 0.15, 0.85, PAL.amber); c.fd = 0.3;
      c = card(C.shine, M_BILL, x, y, z, 0.12, 0.2, 0.7, 0xFFE15A); c.ease = E_POP; c.vr = 6;
    }
  };
  /* bullet hits the world: sparks + chips + dust by surface (floor, metal gate, wall / prop) */
  B.impact = function (x, y, z, nx, ny, nz, box) {
    if (!B.ready) return;
    var metal = box && box.kind === 'gate', floor = !box && ny > 0.5, col = floor ? B.dustCol : B.wallCol, c, i;
    sparkBurst(x + nx * 0.03, y + ny * 0.03, z + nz * 0.03, cnt(metal ? 6 : 3), metal ? 6 : 4, nx, ny, nz, 0.75, undefined, 0.24);
    flash(x + nx * 0.04, y + ny * 0.04, z + nz * 0.04, metal ? 0.34 : 0.22, metal ? 0xFFE15A : 0xFFF1D6, 0.05, C.cloud);
    if (!metal) {
      var nchip = cnt(2);
      for (i = 0; i < nchip; i++) { c = card(C.chip, M_BILL, x + nx * 0.04, y + ny * 0.04, z + nz * 0.04, rnd(0.4, 0.65), rnd(0.05, 0.08), 0.05, col); c.vx = nx * 2.2 + rnd(-1.6, 1.6); c.vy = ny * 2.2 + rnd(1, 3); c.vz = nz * 2.2 + rnd(-1.6, 1.6); c.g = 14; c.vr = rnd(-16, 16); c.ease = E_LIN; c.floor = 0.03; }
      c = card(C.dust, M_BILL, x + nx * 0.08, y + ny * 0.08, z + nz * 0.08, rnd(0.45, 0.65), 0.1, rnd(0.38, 0.55), col); c.vx = nx * 0.6; c.vy = 0.35 + ny * 0.4; c.vz = nz * 0.6; c.drag = 2; c.a0 = 0.85; c.fd = 0.35;
    } else { c = card(C.shine, M_BILL, x + nx * 0.05, y + ny * 0.05, z + nz * 0.05, 0.08, 0.1, 0.4, 0xFFE15A); c.ease = E_POP; }
  };
  /* bullet tracer: a comic streak that flies down the shot line */
  B.tracer = function (ax, ay, az, bx, by, bz, def) {
    if (!B.ready) return;
    var dx = bx - ax, dy = by - ay, dz = bz - az, L = Math.sqrt(dx * dx + dy * dy + dz * dz); if (L < 0.5) return;
    var heavy = def && (def.cls === 'sniper' || def.id === 'handcannon'), tint = heavy ? 0xFFE15A : PAL.amber;
    if (def && IB.GunSkins) { var tr = IB.GunSkins.tierOf(def.id); if (tr !== 'gray') tint = parseInt(IB.GunSkins.feel(tr).tracer.slice(1), 16); }   // rarity tracer tint
    var c = card(C.streak, M_TRACER, ax, ay, az, 1, 1, 1, tint);
    c.ex = bx; c.ey = by; c.ez = bz; c.sp = heavy ? 320 : 230; c.seg = Math.min(L * 0.6, heavy ? 6 : 3.4); c.life = (L + c.seg) / c.sp; c.w = heavy ? 0.1 : 0.06; c.a0 = 0.95;
  };
  /* electric arc between two points (Lightning Rod, Electrify, shock DoT) */
  B.arc = function (ax, ay, az, bx, by, bz, color, life, width) {
    if (!B.ready) return;
    var dx = bx - ax, dy = by - ay, dz = bz - az, L = Math.sqrt(dx * dx + dy * dy + dz * dz); if (L < 0.05) return;
    var n = L > 3 ? 3 : L > 1.2 ? 2 : 1, px = ax, py = ay, pz = az, j = L * 0.12;
    for (var i = 1; i <= n; i++) {
      var f = i / n, qx = ax + dx * f + (i < n ? rnd(-j, j) : 0), qy = ay + dy * f + (i < n ? rnd(-j, j) : 0), qz = az + dz * f + (i < n ? rnd(-j, j) : 0);
      var c = card(Math.random() < 0.5 ? C.zig0 : C.zig1, M_SEG, px, py, pz, life || 0.16, width || 0.6, (width || 0.6) * 0.8, color === undefined ? 0x5FC2FF : color);
      c.ex = qx; c.ey = qy; c.ez = qz; c.flick = reduce() ? 0.09 : 0.035; c.fd = 0.5;
      px = qx; py = qy; pz = qz;
    }
  };
  B.zap = function (x, y, z, size, color) { if (!B.ready) return; flash(x, y, z, size || 0.5, color === undefined ? 0x5FC2FF : color, 0.08, C.burst); sparkBurst(x, y, z, cnt(4), 5, 0, 0.3, 0, 1, 0x8ED2FF, 0.25); };
  /* Lightning Rod: a fat bolt from the hit point into another robot */
  B.lightning = function (ax, ay, az, bx, by, bz) {
    if (!B.ready) return;
    B.arc(ax, ay, az, bx, by, bz, 0x5FC2FF, 0.24, 1.0);
    B.arc(ax, ay, az, bx, by, bz, 0x8ED2FF, 0.14, 0.55);
    B.zap(bx, by, bz, 0.8);
    var c = card(C.ring, M_BILL, bx, by, bz, 0.18, 0.2, 1.1, 0x5FC2FF); c.fd = 0.3;
  };
  /* Chain Reaction: a burst that shows its reach as a ring on the floor */
  B.chainBurst = function (x, z, R) {
    if (!B.ready) return;
    explode(x, 0.6, z, FLAV.chain, 1, F_RING | F_NOCHAIN | F_NOSHAKE | F_SCORCH);
    var c = card(C.ring, M_GROUND, x, 0.06, z, 0.38, R * 0.8, R * 2.6, PAL.amber); c.fd = 0.5; c.ease = E_OUT;
    c = card(C.dots, M_GROUND, x, 0.07, z, 0.3, R * 0.6, R * 2.0, PAL.amber); c.a0 = 0.7; c.fd = 0.3;
  };
  /* status effect visuals (status.js): a few per second per robot */
  B.statusFx = function (kind, r, x, y, z, rad, y0, y1) {
    if (!B.ready || !roomy()) return;
    var c;
    if (kind === 'shock') {
      sparkBurst(x, y, z, cnt(2), 3.5, x - r.x, 0.3, z - r.z, 1, Math.random() < 0.5 ? 0x8ED2FF : 0xFFFDF7, 0.2);
      if (Math.random() < 0.45) { var b = Math.random() * TAU; B.arc(x, y, z, r.x + Math.cos(b) * rad * 0.9, y0 + (y1 - y0) * Math.random(), r.z + Math.sin(b) * rad * 0.9, 0x5FC2FF, 0.1, 0.5); }
      if (Math.random() < 0.08) B.zap(x, y, z, 0.35);
    } else {
      // acid: drips fall off, bubbles rise and pop, steam sizzles off the top
      c = card(C.drip, M_BILL, x, y, z, rnd(0.45, 0.7), 0.1, 0.13, Math.random() < 0.7 ? 0x7BE34A : 0x3FAE2A); c.rot = 0; c.g = 9; c.vy = -0.4; c.ease = E_LIN; c.floor = 0.02; c.fd = 0.75;
      if (Math.random() < 0.4) { c = card(C.bubble, M_BILL, r.x + rnd(-rad, rad) * 0.7, y1, r.z + rnd(-rad, rad) * 0.7, rnd(0.35, 0.55), 0.04, 0.15, 0xC8FF8A); c.vy = 0.6; c.ease = E_POP; c.fd = 0.85; }
      if (Math.random() < 0.3) { c = card(C.dust, M_BILL, r.x + rnd(-rad, rad) * 0.5, y1 + 0.1, r.z + rnd(-rad, rad) * 0.5, rnd(0.6, 0.9), 0.1, rnd(0.3, 0.45), 0xD6F5B8); c.vy = 0.8; c.drag = 1; c.a0 = 0.7; c.fd = 0.3; }
    }
  };
  /* a robot's muzzle flash (ai.js fireBolt) */
  B.muzzle = function (x, y, z, size) { if (!B.ready) return; var c = flash(x, y, z, size || 0.4, PAL.amber, 0.06, C.burst); c.a0 = Math.min(c.a0, 0.95); };
  /* enemy bolt lands */
  B.boltHit = function (x, y, z, nx, ny, nz) { if (!B.ready) return; sparkBurst(x, y, z, cnt(4), 4.5, nx, ny, nz, 0.9, Math.random() < 0.5 ? PAL.red : PAL.amber, 0.24); flash(x, y, z, 0.32, PAL.red, 0.06, C.cloud); };
  /* gate shutter slams down */
  B.gateSlam = function (gate) {
    if (!B.ready || !gate) return;
    var w = gate.w || 3, n = cnt(4 + w * 1.5), c, i;
    for (i = 0; i < n; i++) {
      var x = gate.x + rnd(-w / 2, w / 2), side = Math.random() < 0.5 ? -1 : 1;
      c = card(C.dust, M_BILL, x, 0.2, gate.z + side * 0.4, rnd(0.6, 0.95), 0.25, rnd(0.6, 0.95), B.dustCol); c.vx = rnd(-0.6, 0.6); c.vz = side * rnd(1.6, 3); c.vy = rnd(0.2, 0.7); c.drag = 3; c.a0 = 0.95; c.fd = 0.45;
    }
    var nc = cnt(5); for (i = 0; i < nc; i++) { c = card(C.chip, M_BILL, gate.x + rnd(-w / 2, w / 2), 0.1, gate.z, rnd(0.5, 0.8), 0.07, 0.05, B.wallCol); c.vx = rnd(-1, 1); c.vz = rnd(-2.5, 2.5); c.vy = rnd(2, 4); c.g = 14; c.vr = rnd(-12, 12); c.ease = E_LIN; c.floor = 0.03; }
    sparkBurst(gate.x, 0.1, gate.z, cnt(6), 4, 0, 0.6, 0, 1.2, undefined, 0.3);
    var g = IB.Game;
    if (g && g.player && g.mode === 'play') {
      var d = Math.hypot(g.player.x - gate.x, g.player.z - gate.z);
      if (d < 26) B.word(8, gate.x, 1.5, gate.z, 1.8);
      if (d < 12 && g.addTrauma) g.addTrauma(0.18 * (1 - d / 12));
    }
  };
  /* gems spray out of a wreck */
  B.gemBurst = function (kind, x, y, z) {
    if (!B.ready) return;
    var col = kind === 'core' ? 0xC6EEFF : kind === 'shard' ? 0x3D7BFF : 0x58C8FF, c = card(C.star, M_BILL, x + rnd(-0.2, 0.2), y + 0.4, z + rnd(-0.2, 0.2), 0.42, 0.08, 0.32, col);
    c.ease = E_POP; c.vy = 1.2; c.vr = rnd(-5, 5);
    { c = card(C.shine, M_BILL, x, y + 0.5, z, 0.3, 0.1, 0.5, col); c.ease = E_POP; c.vr = 4; }
  };
  /* zone clear (confetti at the gate) / level clear (fireworks over the zone) */
  B.zoneClear = function (level, i, last) {
    if (!B.ready || !level || !level.zones[i]) return;
    var z = level.zones[i], gate = z.exitGate, k;
    confetti(gate.x, 2.8, gate.z + 0.6, cnt(26), (gate.w || 3) / 2);
    flash(gate.x, 3.2, gate.z + 0.4, 2.2, PAL.teal, 0.2);
    var c = card(C.ring, M_BILL, gate.x, 3.2, gate.z + 0.4, 0.4, 0.5, 4, PAL.amber); c.fd = 0.4;
    if (!last) return;
    // level clear: fireworks, mostly in front of the player (the rest over the exit gate), kept under the ceiling
    var g = IB.Game, p = g && g.player, cam = IB.Render.camera, env = level.theme && level.theme.env;
    var top = Math.min(9.5, env && env.ceiling ? Math.max(2.6, (env.ceiling.height || 4) - 0.9) : 9.5), lo = Math.min(top - 0.8, 3.8);
    var px = p ? p.x : gate.x, pz = p ? p.z : gate.z + 10, fx = 0, fz = -1;
    if (cam) { cam.getWorldDirection(_v); var fl = Math.hypot(_v.x, _v.z) || 1; fx = _v.x / fl; fz = _v.z / fl; }
    var n = 6 + Math.round(2 * B.I), ey = p ? p.y + 1.5 : 1.5;
    for (k = 0; k < n; k++) {
      var over = k % 3 === 2, side = rnd(-0.7, 0.7), dxs = fx * Math.cos(side) - fz * Math.sin(side), dzs = fz * Math.cos(side) + fx * Math.sin(side);
      var d = rnd(7, 13), y = Math.min(top, ey + rnd(1.5, 0.48 * d)), up = (y - ey) / d, L = Math.sqrt(1 + up * up);   // inside the view cone
      // keep it in open air in front of the camera: stop short of the first wall along the line of sight
      var h = level.world.ray(px, ey, pz, dxs / L, up / L, dzs / L, d * L);
      if (h) { d = Math.max(3, h.t / L - 1.5); y = ey + up * d; }
      var x = over ? gate.x + rnd(-5, 5) : px + dxs * d, zz = over ? gate.z + rnd(1, 4) : pz + dzs * d;
      event(2, x, over ? rnd(lo, top) : y, zz, 0.1 + k * rnd(0.16, 0.28), k === 0 ? 2 : 1);
    }
    // and a confetti shower over the player's head
    if (p) confetti(px + fx * 3, Math.min(top, 2.9), pz + fz * 3, cnt(40), 2.5, 0.6);
  };
  /* player gun: casings from the EJECT socket + a wisp of muzzle smoke (weapons.js fire) */
  var CASE_SKIP = { handcannon: true };
  B.onFire = function (ws, def) {
    if (!B.ready || !ws || !def) return;
    var Wp = IB.Weapons, m = ws.cur && Wp.models && Wp.models[ws.cur];
    if (m && !CASE_SKIP[def.id] && def.action !== 'revolver' && def.cls !== 'rocket') {
      if (m.eject === undefined) m.eject = m.mesh.getObjectByName('WPN_' + m.key + '_EJECT') || null;
      if (m.eject && Wp.vmRoot && Wp.vmRoot.visible) {
        m.eject.getWorldPosition(_v);
        var e = null; for (var i = 0; i < CASE_CAP; i++) if (!casings[i].on) { e = casings[i]; break; }
        if (!e) { e = casings[0]; for (i = 1; i < CASE_CAP; i++) if (casings[i].t > e.t) e = casings[i]; }
        var big = def.cls === 'sniper' || def.cls === 'rifle', shell = def.cls === 'shotgun';
        e.on = true; e.t = 0; e.x = _v.x; e.y = _v.y; e.z = _v.z;
        e.vx = rnd(0.9, 1.5); e.vy = rnd(1.1, 1.7); e.vz = rnd(-0.15, 0.35);
        e.rx = Math.random() * TAU; e.ry = 0; e.rz = Math.PI / 2; e.wx = rnd(-30, 30); e.wy = rnd(-10, 10); e.wz = rnd(15, 30);
        e.s = shell ? 1.5 : big ? 1.05 : 0.8;
        B.caseMesh.setColorAt(e.idx, _c.setHex(shell ? 0xF07060 : 0xFFFFFF)); B.caseMesh.instanceColor.needsUpdate = true;
      }
    }
    // muzzle smoke wisp in the world
    var cam = IB.Render.camera;
    // a revolver (def.action): every shot, and a puff 1.5x the size
    var rev = def.action === 'revolver';
    if (Wp.muzzleWorld && cam && roomy() && Math.random() < (rev ? 1 : def.fire === 'auto' ? 0.35 : 0.8)) {
      Wp.muzzleWorld(cam, _v);
      cam.getWorldDirection(_a); _v.addScaledVector(_a, 0.5);
      var c = card(C.dust, M_BILL, _v.x, _v.y, _v.z, rnd(0.35, 0.55) * (rev ? 1.5 : 1), 0.02, rnd(0.08, 0.13), 0xE9E4F0); c.vx = _a.x * 0.8; c.vy = 0.45; c.vz = _a.z * 0.8; c.drag = 2.5; c.a0 = 0.5; c.fd = 0.15;
    }
  };

  // ---------------- explosive canisters ----------------
  var CAN_SRC = { type: 'canister', x: 0, z: 0, proj: true };
  function hash2(a, b) { var h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return (h ^ (h >>> 16)) >>> 0; }
  function strHash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  var _tmpBoxes = [];
  function placeCans(level, L, planId) {
    var list = [], per = B.canistersPerZone(L), world = level.world, CN = B.CAN;
    if (!per) return list;
    level.zones.forEach(function (zn, zi) {
      var N = zn.nav; if (!N) return;
      var rng = rngFrom(hash2(strHash(planId || 'x'), zi + 1)), got = [];
      var open = function (i, j) { return i >= 0 && j >= 0 && i < N.nx && j < N.nz && !N.blocked[j * N.nx + i]; };
      var gates = [zn.exitGate, zn.entryGate];
      for (var tries = 0; tries < 500 && got.length < per; tries++) {
        var i = 4 + Math.floor(rng() * (N.nx - 8)), j = 4 + Math.floor(rng() * (N.nz - 8));
        if (!B.clearPatch(open, i, j, 3)) continue;
        var x = zn.ox + (i + 0.5) * 0.5, z = zn.oz + (j + 0.5) * 0.5, ok = true, k;
        if (Math.hypot(x - zn.entry.x, z - zn.entry.z) < CN.fromEntry) continue;
        for (k = 0; k < zn.spawns.length && ok; k++) if (Math.hypot(x - zn.spawns[k].x, z - zn.spawns[k].z) < CN.fromSpawn) ok = false;
        for (k = 0; k < gates.length && ok; k++) if (gates[k] && Math.hypot(x - gates[k].x, z - gates[k].z) < CN.fromGate) ok = false;
        for (k = 0; k < zn.pickups.length && ok; k++) if (Math.hypot(x - zn.pickups[k].x, z - zn.pickups[k].z) < 2) ok = false;
        for (k = 0; k < got.length && ok; k++) if (Math.hypot(x - got[k].x, z - got[k].z) < CN.gap) ok = false;
        if (!ok) continue;
        // nothing overhead or around it (desks, beds, shelves)
        world.query(x - 0.6, z - 0.6, x + 0.6, z + 0.6, _tmpBoxes);
        if (_tmpBoxes.length) continue;
        var cells = [];
        for (var dj = -1; dj <= 1; dj++) for (var di = -1; di <= 1; di++) cells.push((j + dj) * N.nx + (i + di));
        got.push({ x: x, z: z, zone: zi, cells: cells });
      }
      got.forEach(function (g) {
        g.box = world.add(g.x - 0.32, 0, g.z - 0.32, g.x + 0.32, 0.88, g.z + 0.32, 'canister', g.zone);
        list.push(g);
      });
    });
    return list;
  }
  B.levelStart = function (level, L) {
    B.lvl = L || 1; B.I = B.intensity(B.lvl);
    var th = level && level.theme;
    B.dustCol = new THREE.Color((th && th.floor && th.floor.color) || '#D9C9A8').lerp(new THREE.Color(PAL.paper), 0.35).getHex();
    B.wallCol = new THREE.Color((th && th.wall && th.wall.roof) || '#E9DFC8').lerp(new THREE.Color(PAL.cream), 0.3).getHex();
    if (!level) return;
    if (level.__cans === undefined) level.__cans = placeCans(level, B.lvl, level.plan && level.plan.id);
    var list = level.__cans, i;
    B.level = level;
    for (i = 0; i < CAN_CAP; i++) {
      var c = cans[i], g = list[i];
      c.on = !!g; c.def = g || null;
      if (!g) continue;
      c.x = g.x; c.z = g.z; c.zone = g.zone; c.box = g.box; c.hp = B.CAN.hp; c.state = 0; c.fuse = 0; c.fuse0 = 1; c.flash = 0; c.t = Math.random() * 10; c.hiss = 0;
      g.box.on = true; g.box.can = c;
      setCells(level, c, 1);
    }
  };
  function setCells(level, c, v) { var N = level.zones[c.zone] && level.zones[c.zone].nav; if (!N) return; var cells = c.def.cells; for (var k = 0; k < cells.length; k++) if (cells[k] >= 0 && cells[k] < N.blocked.length) N.blocked[cells[k]] = v; }
  function lightCan(c, fuse) {
    if (c.state === 2) return;
    if (c.state === 1) { c.fuse = Math.min(c.fuse, fuse); return; }
    c.state = 1; c.fuse = c.fuse0 = fuse;
    sfx('fuse', c.x, c.z, 0.8, 1.25);
    // fair warning: a red ring on the floor marks the blast reach (ring art radius = 0.383 x card size)
    if (fuse >= 0.3) { var rc = card(C.ring, M_GROUND, c.x, 0.05, c.z, fuse + 0.05, B.CAN.radius * 2.2, B.CAN.radius * 2.6, PAL.red); rc.a0 = 0.75; rc.fd = 0.85; rc.ease = E_LIN; rc.rot = 0; rc.vr = 1.2; }
  }
  function blowCan(c) {
    c.state = 2; c.box.on = false; setCells(B.level, c, 0);
    CAN_SRC.x = c.x; CAN_SRC.z = c.z;
    if (IB.Projectiles && IB.Projectiles.explode) IB.Projectiles.explode(c.x, 0.5, c.z, B.CAN.radius, B.CAN.dmgPlayer, B.CAN.dmgRobots * ((IB.AI && IB.AI.hpMul) || 1), CAN_SRC);
    for (var i = 0; i < 3; i++) debris(BIN.plate, c.x, 0.5, c.z, 6, PAL.red, 1.4);
  }
  /* a bullet / bolt hit a canister's box */
  B.hitCan = function (box, dmg) {
    var c = box && box.can; if (!c || !c.on || c.state === 2) return false;
    c.flash = 0.06;
    sparkBurst(c.x, 0.5, c.z, cnt(3), 4, 0, 0.5, 0, 1, undefined, 0.25);
    if (c.state === 0) { c.hp -= dmg; if (c.hp <= 0) lightCan(c, B.CAN.fuse); }
    return true;
  };
  /* a blast went off: canisters in reach light with a short fuse (chains ripple) */
  B.onBlast = function (x, y, z, R) {
    for (var i = 0; i < CAN_CAP; i++) {
      var c = cans[i]; if (!c.on || c.state === 2) continue;
      if (Math.hypot(c.x - x, c.z - z) < R + 0.35) lightCan(c, B.CAN.chainFuse * rnd(0.8, 1.3));
    }
  };
  B.canisters = function () { var out = []; for (var i = 0; i < CAN_CAP; i++) { var c = cans[i]; if (c.on) out.push({ x: c.x, z: c.z, zone: c.zone, state: ['intact', 'lit', 'gone'][c.state], hp: c.hp }); } return out; };

  // ---------------- screen ink (hurt splats, low-health ink, blast flash) ----------------
  /* Drawn on one 2D canvas over the game at the display's own resolution (capped), only while something shows.
     Splats are pre-rendered once as metaball ink: random blobs, tendrils (chains of shrinking discs) and loose
     droplets are blurred together and thresholded with a soft ramp, so the edges are smooth, gooey and anti-aliased
     at any size; then a deep ink body (a thin crimson rim on the red ones), a faint glossy highlight and a paper
     grain. Each hit throws a few in from the edges with a slap-in overshoot; drips run down out of them, slowing,
     each with a bead at its tip. Low health: an ink-and-crimson vignette with ink pooled at the corners that
     thumps with a heartbeat (faster as health falls). Death: a heavy slap of large splats that drip longer. */
  var INK = '#110D17', INK_RGB = [17, 13, 23];
  var Scr = B.Screen = { cv: null, ctx: null, w: 0, h: 0, k: 1, splats: [], spr: [], low: 0, flashA: 0, linesA: 0, dirty: false, lastHp: -1, wasAlive: true, vig: null, lines: null, lowT: 0, beat: 0 };
  var SPR = 384;   // sprite size (px); drawn up to ~0.45 of the screen's short side
  function inkBlobs(g, r, red) {
    var c = SPR / 2, k, a, j;
    g.fillStyle = '#000';
    // body: a cluster of overlapping discs
    var nb = 7 + ((r() * 5) | 0);
    for (k = 0; k < nb; k++) { a = r() * TAU; var d = r() * SPR * 0.12; g.beginPath(); g.arc(c + Math.cos(a) * d, c + Math.sin(a) * d, SPR * (0.06 + r() * 0.07), 0, TAU); g.fill(); }
    // tendrils thrown outward: chains of shrinking discs, a droplet beyond
    var nt = 4 + ((r() * 4) | 0);
    for (k = 0; k < nt; k++) {
      a = k / nt * TAU + (r() - 0.5) * 0.6;
      var len = SPR * (0.06 + r() * 0.17), w0 = SPR * (0.035 + r() * 0.03), steps = 8, bend = (r() - 0.5) * 0.7;
      for (j = 0; j <= steps; j++) {
        var f = j / steps, aa = a + bend * f * f, rr = SPR * 0.12 + len * f;
        g.beginPath(); g.arc(c + Math.cos(aa) * rr, c + Math.sin(aa) * rr, Math.max(1.5, w0 * (1 - f * 0.6)), 0, TAU); g.fill();
      }
      if (r() < 0.8) { var rd = SPR * 0.12 + len + SPR * (0.04 + r() * 0.05); g.beginPath(); g.arc(c + Math.cos(a + bend) * rd, c + Math.sin(a + bend) * rd, w0 * (0.5 + r() * 0.5), 0, TAU); g.fill(); }
    }
    // loose spray
    for (k = 0; k < 4; k++) { a = r() * TAU; var ds = SPR * (0.22 + r() * 0.08); g.beginPath(); g.arc(c + Math.cos(a) * ds, c + Math.sin(a) * ds, SPR * (0.025 + r() * 0.03), 0, TAU); g.fill(); }
    for (k = 0; k < 12; k++) { a = r() * TAU; var dd = SPR * (0.24 + r() * 0.2); g.beginPath(); g.arc(c + Math.cos(a) * dd, c + Math.sin(a) * dd, SPR * (0.006 + r() * r() * 0.016), 0, TAU); g.fill(); }
  }
  function splatSprite(seed, red) {
    var r = rngFrom(seed), S = SPR;
    var m = document.createElement('canvas'); m.width = m.height = S;
    var g = m.getContext('2d');
    // 1. mask: blobs blurred together (metaballs), thresholded below with a soft ramp
    var raw = document.createElement('canvas'); raw.width = raw.height = S;
    inkBlobs(raw.getContext('2d'), r, red);
    if ('filter' in g) { g.filter = 'blur(' + (S * 0.016).toFixed(1) + 'px)'; g.drawImage(raw, 0, 0); g.filter = 'none'; } else g.drawImage(raw, 0, 0);
    var img = g.getImageData(0, 0, S, S), d = img.data, i, x, y;
    var al = new Float32Array(S * S);
    for (i = 0; i < S * S; i++) { var v = d[i * 4 + 3] / 255; v = (v - 0.4) / 0.07; al[i] = v <= 0 ? 0 : v >= 1 ? 1 : v * v * (3 - 2 * v); }
    // 2. colour: deep ink, a crimson rim on the red ones (edge = where the soft mask is below its core), a glossy
    // highlight up-left inside the body, a paper grain
    var grain = rngFrom(seed * 7 + 3);
    for (y = 0; y < S; y++) for (x = 0; x < S; x++) {
      i = y * S + x; var A = al[i]; if (A <= 0) { d[i * 4 + 3] = 0; continue; }
      var inner = A, o = i * 4;
      // the raw blurred alpha says how deep inside the body this is (0.42 edge .. 1 core)
      var depth = Math.min(1, Math.max(0, (d[o + 3] / 255 - 0.4) / 0.5));
      var R = INK_RGB[0], G = INK_RGB[1], Bc = INK_RGB[2];
      if (red) { var rim = 1 - depth; R += 70 * rim * rim; G += 4 * rim; Bc += 8 * rim; }
      var hx = (x - S * 0.43) / (S * 0.1), hy = (y - S * 0.41) / (S * 0.05), h = Math.max(0, 1 - hx * hx - hy * hy);
      h = h * h * Math.max(0, depth - 0.4) / 0.6; R += 30 * h; G += 28 * h; Bc += 38 * h;
      var n = (grain() - 0.5) * 10;
      d[o] = R + n; d[o + 1] = G + n; d[o + 2] = Bc + n;
      d[o + 3] = 255 * inner * (0.96 + 0.04 * grain());
    }
    g.putImageData(img, 0, 0);
    return m;
  }
  Scr.init = function () {
    if (Scr.cv || typeof document === 'undefined') return;
    var cv = Scr.cv = document.createElement('canvas');
    cv.id = 'inkfx'; cv.setAttribute('aria-hidden', 'true');
    cv.style.cssText = 'position:fixed;left:0;top:0;width:100%;height:100%;pointer-events:none;display:none';
    var hurt = document.getElementById('hurt'), hud = document.getElementById('hud');
    if (hurt && hurt.parentNode) hurt.parentNode.insertBefore(cv, hurt.nextSibling);
    else if (hud && hud.parentNode) hud.parentNode.insertBefore(cv, hud);
    else document.body.appendChild(cv);
    Scr.ctx = cv.getContext('2d');
    for (var i = 0; i < 8; i++) Scr.spr.push(splatSprite(901 + i * 77, i % 3 === 0));
    for (i = 0; i < 14; i++) Scr.splats.push({ on: false, x: 0, y: 0, s: 1, rot: 0, t: 0, life: 1.6, spr: 0, drips: [] });
    Scr.resize();
    window.addEventListener('resize', Scr.resize);
  };
  Scr.resize = function () {
    if (!Scr.cv) return;
    var W = Math.max(1, window.innerWidth), H = Math.max(1, window.innerHeight);
    // the display's own pixels (smooth at any size), capped so a 4K screen does not fill a 4K canvas every frame
    Scr.k = Math.min(window.devicePixelRatio || 1, 1600 / Math.max(W, H));
    Scr.w = Scr.cv.width = Math.round(W * Scr.k); Scr.h = Scr.cv.height = Math.round(H * Scr.k);
    var w = Scr.w, h = Scr.h, m = Math.min(w, h), r = rngFrom(31), k;
    // low-health ink pooled at the corners and creeping along the edges (the vignette itself is drawn live)
    var v = Scr.vig = document.createElement('canvas'); v.width = w; v.height = h;
    var g = v.getContext('2d');
    var corners = [[0, 0], [w, 0], [0, h], [w, h]];
    for (k = 0; k < 16; k++) {
      var cn = corners[k % 4], s = m * (k < 4 ? 0.62 + r() * 0.12 : 0.26 + r() * 0.16), along = r();
      var cx = k < 4 ? cn[0] : k % 2 ? along * w : cn[0], cy = k < 4 ? cn[1] : k % 2 ? cn[1] : along * h;
      g.save(); g.translate(cx, cy); g.rotate(r() * TAU); g.globalAlpha = 0.95; g.drawImage(Scr.spr[k % Scr.spr.length], -s / 2, -s / 2, s, s); g.restore();
    }
    // impact lines: tapered ink wedges from the edges toward the centre
    var L = Scr.lines = document.createElement('canvas'); L.width = w; L.height = h;
    g = L.getContext('2d'); g.fillStyle = INK;
    for (k = 0; k < 44; k++) {
      var a = k / 44 * TAU + r() * 0.09, R1 = Math.hypot(w, h) * 0.6, R0 = m * (0.34 + r() * 0.16), ww = 0.008 + r() * 0.016;
      g.beginPath(); g.moveTo(w / 2 + Math.cos(a - ww) * R1, h / 2 + Math.sin(a - ww) * R1);
      g.quadraticCurveTo(w / 2 + Math.cos(a) * (R0 + (R1 - R0) * 0.3), h / 2 + Math.sin(a) * (R0 + (R1 - R0) * 0.3), w / 2 + Math.cos(a) * R0, h / 2 + Math.sin(a) * R0);
      g.quadraticCurveTo(w / 2 + Math.cos(a) * (R0 + (R1 - R0) * 0.3), h / 2 + Math.sin(a) * (R0 + (R1 - R0) * 0.3), w / 2 + Math.cos(a + ww) * R1, h / 2 + Math.sin(a + ww) * R1);
      g.fill();
    }
    Scr.dirty = true;
  };
  function addSplat(size, life, edge) {
    var sp = null, k;
    for (k = 0; k < Scr.splats.length; k++) if (!Scr.splats[k].on) { sp = Scr.splats[k]; break; }
    if (!sp) { sp = Scr.splats[0]; for (k = 1; k < Scr.splats.length; k++) if (Scr.splats[k].t > sp.t) sp = Scr.splats[k]; }
    var side = (Math.random() * 4) | 0, f = 0.08 + Math.random() * 0.84;
    sp.on = true; sp.t = 0; sp.life = life; sp.spr = (Math.random() * Scr.spr.length) | 0; sp.rot = Math.random() * TAU; sp.s = size;
    sp.x = side < 2 ? Scr.w * f : side === 2 ? 0 : Scr.w; sp.y = side === 0 ? 0 : side === 1 ? Scr.h : Scr.h * f;
    sp.x += (Scr.w / 2 - sp.x) * rnd(edge, edge + 0.12); sp.y += (Scr.h / 2 - sp.y) * rnd(edge, edge + 0.12);
    // drips: start on the lower part of the splat, run down, slowing; widths taper to a bead
    var nd = 1 + ((Math.random() * 3) | 0); sp.drips.length = 0;
    for (k = 0; k < nd; k++) sp.drips.push({ x: (Math.random() - 0.5) * size * 0.34, y0: size * (0.06 + Math.random() * 0.1), w: size * (0.03 + Math.random() * 0.025),
      len: size * (0.18 + Math.random() * 0.35) * Math.min(1.4, life / 1.8), sp: 0.5 + Math.random() * 0.7, wob: Math.random() * TAU });
    return sp;
  }
  Scr.hurt = function (amount, death) {
    var m = Math.min(Scr.w, Scr.h);
    if (death) { for (var j = 0; j < 6; j++) addSplat(m * (0.34 + Math.random() * 0.2), 3.2 + Math.random(), 0.04); Scr.dirty = true; return; }
    var n = Math.min(4, 1 + Math.floor(amount / 14));
    for (var i = 0; i < n; i++) addSplat(m * (0.2 + Math.random() * 0.14) * Math.min(1.7, 0.75 + amount / 35), 1.4 + Math.random() * 0.8, 0.02);
    Scr.dirty = true;
  };
  Scr.kick = function (k) { if (!Scr.cv) return; Scr.linesA = Math.max(Scr.linesA, 0.6 * k); if (!reduce()) Scr.flashA = Math.max(Scr.flashA, 0.5 * k); Scr.dirty = true; };
  Scr.clear = function () { Scr.splats.forEach(function (s) { s.on = false; }); Scr.flashA = Scr.linesA = 0; Scr.low = 0; Scr.lastHp = -1; Scr.dirty = true; };
  // a heartbeat: lub-dub, then rest (0..1)
  function heart(t) { var p = t % 1, a = Math.exp(-Math.pow((p - 0.06) / 0.045, 2)), b = Math.exp(-Math.pow((p - 0.26) / 0.06, 2)) * 0.6; return Math.max(a, b); }
  function drawDrip(ctx, s, dr, k, a) {
    // length eases out (runs quickly, then slows to a creep)
    var e = 1 - Math.pow(1 - Math.min(1, k * dr.sp * 1.6), 2.2), L = dr.len * e; if (L < 1) return;
    var x0 = dr.x, y0 = dr.y0, x1 = x0 + Math.sin(dr.wob + k * 2) * dr.w * 0.6, y1 = y0 + L, w = dr.w;
    ctx.beginPath();
    ctx.moveTo(x0 - w, y0 - w);
    ctx.bezierCurveTo(x0 - w * 0.75, y0 + L * 0.4, x1 - w * 0.45, y1 - L * 0.35, x1 - w * 0.42, y1);
    ctx.lineTo(x1 + w * 0.42, y1);
    ctx.bezierCurveTo(x1 + w * 0.45, y1 - L * 0.35, x0 + w * 0.75, y0 + L * 0.4, x0 + w, y0 - w);
    ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.arc(x1, y1 + w * 0.2, w * 0.78, 0, TAU); ctx.fill();   // the bead at the tip
  }
  Scr.update = function (dt, p) {
    if (!Scr.cv) return;
    var g = IB.Game, show = !!(g && g.mode === 'play' && p), frac = 1;
    if (show) {
      if (Scr.lastHp >= 0 && p.alive && p.health < Scr.lastHp - 0.5) Scr.hurt(Scr.lastHp - p.health);
      if (Scr.wasAlive && !p.alive) Scr.hurt(60, true);
      Scr.lastHp = p.alive ? p.health : -1; Scr.wasAlive = p.alive;
      frac = p.maxHp ? p.health / p.maxHp : 1;
      var want = p.alive && frac < 0.3 ? 0.55 + (0.3 - frac) * 1.5 : 0;
      Scr.lowT += dt; Scr.low += (want - Scr.low) * Math.min(1, dt * 3);
      Scr.beat += dt * (1.05 + Math.max(0, 0.3 - frac) * 2.2);   // ~63 bpm, faster as it falls
    } else { Scr.low = 0; Scr.lastHp = -1; Scr.wasAlive = true; }
    var any = Scr.low > 0.01 || Scr.flashA > 0.01 || Scr.linesA > 0.01, i, s, j;
    for (i = 0; i < Scr.splats.length; i++) if (Scr.splats[i].on) { any = true; break; }
    if (!show) any = false;
    if (!any) { if (Scr.dirty || Scr.cv.style.display !== 'none') { Scr.ctx.clearRect(0, 0, Scr.w, Scr.h); Scr.cv.style.display = 'none'; Scr.dirty = false; } return; }
    if (Scr.cv.style.display === 'none') Scr.cv.style.display = 'block';
    var ctx = Scr.ctx, W = Scr.w, H = Scr.h; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H);
    if (Scr.low > 0.01) {
      var hb = reduce() ? 0.3 : heart(Scr.beat), lo = Math.min(1, Scr.low);
      // vignette: deep ink at the rim through a crimson band, pulsing inward with each beat
      var R0 = Math.min(W, H) * (0.36 - 0.05 * hb * lo), R1 = Math.hypot(W, H) * 0.56;
      var grd = ctx.createRadialGradient(W / 2, H / 2, R0, W / 2, H / 2, R1);
      grd.addColorStop(0, 'rgba(50,4,12,0)'); grd.addColorStop(0.4, 'rgba(70,6,16,' + (0.12 + 0.12 * hb) * lo + ')');
      grd.addColorStop(0.75, 'rgba(34,5,12,' + (0.6 + 0.14 * hb) * lo + ')'); grd.addColorStop(1, 'rgba(17,13,23,' + 0.94 * lo + ')');
      ctx.globalAlpha = 1; ctx.fillStyle = grd; ctx.fillRect(0, 0, W, H);
      // ink pooled at the corners, swelling a touch with the beat
      var sc = 1 + 0.025 * hb;
      ctx.globalAlpha = Math.min(1, lo * (0.8 + 0.2 * hb));
      ctx.setTransform(sc, 0, 0, sc, W / 2 * (1 - sc), H / 2 * (1 - sc)); ctx.drawImage(Scr.vig, 0, 0); ctx.setTransform(1, 0, 0, 1, 0, 0);
    }
    ctx.fillStyle = INK;
    for (i = 0; i < Scr.splats.length; i++) {
      s = Scr.splats[i]; if (!s.on) continue;
      s.t += dt; var k = s.t / s.life; if (k >= 1) { s.on = false; continue; }
      // slap in (overshoot), hold, then fade
      var a = k < 0.05 ? k / 0.05 : k < 0.6 ? 1 : 1 - Math.pow((k - 0.6) / 0.4, 1.5);
      var q = Math.min(1, s.t / 0.14), sc2 = q < 1 ? 0.55 + 0.45 * (1 + 2.2 * Math.pow(q - 1, 3) + 1.2 * Math.pow(q - 1, 2)) : 1;
      ctx.globalAlpha = 0.94 * a;
      ctx.setTransform(1, 0, 0, 1, s.x, s.y);
      for (j = 0; j < s.drips.length; j++) drawDrip(ctx, s, s.drips[j], s.t / 2.2, a);
      ctx.rotate(s.rot);
      ctx.drawImage(Scr.spr[s.spr], -s.s * sc2 / 2, -s.s * sc2 / 2, s.s * sc2, s.s * sc2);
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    }
    if (Scr.linesA > 0.01) { ctx.globalAlpha = Scr.linesA; ctx.drawImage(Scr.lines, 0, 0); Scr.linesA = Math.max(0, Scr.linesA - dt * 4.5); }
    if (Scr.flashA > 0.01) { ctx.globalAlpha = Scr.flashA; ctx.fillStyle = '#FFFDF7'; ctx.fillRect(0, 0, W, H); Scr.flashA = Math.max(0, Scr.flashA - dt * 6); }
    ctx.globalAlpha = 1;
    Scr.dirty = true;
  };

  // ---------------- init ----------------
  B.init = function (scene) {
    if (B.ready) return;
    var R = IB.Render, A = IB.Assets, i;
    B.scene = scene;
    // cards
    var cardTex = R.canvasTex(1024, 1024, drawCards);
    var cg = new THREE.PlaneGeometry(1, 1);
    B.cardRect = instAttr(cg, 'aRect', CARD_CAP, 4); B.cardA = instAttr(cg, 'aA', CARD_CAP, 1);
    B.cardMesh = instanced(cg, cardMaterial(cardTex, false), CARD_CAP, scene); instColor(B.cardMesh, CARD_CAP);
    B.cardMesh.renderOrder = 6;
    for (i = 0; i < CARD_CAP; i++) cards.push(newCard());
    // words
    var wordTex = R.canvasTex(1024, 1024, drawWords);
    B.wordTex = wordTex;
    if (document.fonts && document.fonts.ready && !document.fonts.check('900 40px Archivo')) document.fonts.ready.then(function () { drawWords(wordTex.image.getContext('2d')); wordTex.needsUpdate = true; });
    var wg = new THREE.PlaneGeometry(1, 1);
    B.wordRect = instAttr(wg, 'aRect', WORD_CAP, 4); B.wordA = instAttr(wg, 'aA', WORD_CAP, 1);
    B.wordMesh = instanced(wg, cardMaterial(wordTex, true), WORD_CAP, scene); B.wordMesh.renderOrder = 20;
    for (i = 0; i < WORD_CAP; i++) words.push({ on: false, t: 0, x: 0, y: 0, z: 0, size: 2, id: 0, tilt: 0, idx: i });
    // toon puffs
    var pg = puffGeometry();
    B.puffP = instAttr(pg, 'aP', PUFF_CAP, 3);
    B.puffMesh = instanced(pg, puffMaterial(), PUFF_CAP, scene); instColor(B.puffMesh, PUFF_CAP);
    for (i = 0; i < PUFF_CAP; i++) puffs.push(newPuff());
    // debris
    var dmat = R.toonMaterial({});
    makeBin('gear', gearGeo(), dmat, 40, scene); makeBin('bolt', boltGeo(), dmat, 40, scene); makeBin('plate', plateGeo(), dmat, 48, scene); makeBin('spring', springGeo(), dmat, 16, scene);
    var pmat = A.palette && A.palette.bots ? R.toonMaterial({ map: A.palette.bots, baked: A.BAKED.bots }) : dmat;
    Object.keys(FLAV).forEach(function (k) {
      var f = FLAV[k]; if (!f.parts) return;
      f.binList = [];
      f.parts.forEach(function (name) { if (!A.has(name)) return; if (!BIN[name]) makeBin(name, A.get(name), pmat, 10, scene); f.binList.push(BIN[name]); });
      if (!f.binList.length) f.binList = null;
    });
    // casings (viewmodel scene)
    var cgeo = casingGeo();
    B.caseMesh = instanced(cgeo, R.toonMaterial({ uni: R.vmOutline }), CASE_CAP, R.vmScene); instColor(B.caseMesh, CASE_CAP);
    B.caseMesh.renderOrder = 12;
    for (i = 0; i < CASE_CAP; i++) casings.push({ on: false, t: 0, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, rx: 0, ry: 0, rz: 0, wx: 0, wy: 0, wz: 0, s: 1, idx: i });
    // canisters
    var kg = canisterGeo(); B.canFx = instAttr(kg, 'aFx', CAN_CAP, 2);
    B.canMesh = instanced(kg, R.toonMaterial({ fx: true }), CAN_CAP, scene);
    for (i = 0; i < CAN_CAP; i++) cans.push({ on: false, idx: i, state: 0, def: null, x: 0, z: 0, zone: 0, box: null, hp: 0, fuse: 0, fuse0: 1, flash: 0, t: 0, hiss: 0 });
    for (i = 0; i < EVENT_CAP; i++) events.push({ on: false, kind: 0, x: 0, y: 0, z: 0, t: 0, s: 1 });
    for (i = 0; i < FALL_CAP; i++) fallers.push({ on: false, x: 0, y: 0, z: 0, vy: 0, t: 0, smoke: 0, quiet: false, base: 0 });
    B.dustCol = 0xE6DCC8; B.wallCol = 0xF0E8D8;
    Scr.init();
    B.ready = true;
  };
  B.clear = function () {
    if (!B.ready) return;
    var i, b;
    for (i = 0; i < CARD_CAP; i++) cards[i].on = false; nCards = 0; cardHint = 0;
    for (i = 0; i < PUFF_CAP; i++) puffs[i].on = false; nPuffs = 0; puffHint = 0;
    for (i = 0; i < WORD_CAP; i++) words[i].on = false;
    for (i = 0; i < EVENT_CAP; i++) events[i].on = false;
    for (i = 0; i < FALL_CAP; i++) fallers[i].on = false;
    for (i = 0; i < CASE_CAP; i++) casings[i].on = false;
    for (b = 0; b < bins.length; b++) { bins[b].n = 0; for (i = 0; i < bins[b].cap; i++) bins[b].pool[i].on = false; }
    Scr.clear();
  };
  B.stats = function () {
    var dn = 0, i, b; for (b = 0; b < bins.length; b++) for (i = 0; i < bins[b].cap; i++) if (bins[b].pool[i].on) dn++;
    var wn = 0, en = 0, cs = 0; for (i = 0; i < WORD_CAP; i++) if (words[i].on) wn++; for (i = 0; i < EVENT_CAP; i++) if (events[i].on) en++; for (i = 0; i < CASE_CAP; i++) if (casings[i].on) cs++;
    return { cards: nCards, puffs: nPuffs, debris: dn, words: wn, events: en, casings: cs, intensity: B.I, level: B.lvl, cans: B.canisters().length, fallers: fallers.filter(function (f) { return f.on; }).length };
  };

  // ---------------- update ----------------
  // One small function per pool, and instance data written straight into the typed arrays (no three.js setters in
  // the loops): the functions stay optimised and no number gets boxed, so a full-screen brawl makes no garbage.
  function zero16(M, o) { for (var k = 0; k < 16; k++) M[o + k] = 0; }
  function updEvents(dE) {
    for (var i = 0; i < EVENT_CAP; i++) {
      var ev = events[i]; if (!ev.on) continue;
      ev.t -= dE; if (ev.t > 0) continue;
      ev.on = false;
      if (ev.kind === 1) explode(ev.x, ev.y, ev.z, FLAV.pop, ev.s, F_NOCHAIN | F_NOSHAKE | F_SCORCH | (Math.random() < 0.3 ? F_RING : 0));
      else if (ev.kind === 2) firework(ev.x, ev.y, ev.z, ev.s > 1.5 ? 1.3 : 1, ev.s > 1.5);
    }
  }
  function updFallers(dE) {
    for (var i = 0; i < FALL_CAP; i++) {
      var fa = fallers[i]; if (!fa.on) continue;
      fa.t += dE; fa.vy -= 16 * dE; fa.y += fa.vy * dE; fa.smoke -= dE;
      if (fa.smoke <= 0) {
        fa.smoke = 0.045;
        var p = puff(P_SMOKE, fa.x + rnd(-0.1, 0.1), fa.y + 0.15, fa.z + rnd(-0.1, 0.1), rnd(0.16, 0.26), 0.7, 0); p.vy = 0.4;
        if (Math.random() < 0.5) { var c = card(C.streak, M_STREAK, fa.x, fa.y, fa.z, 0.25, 0.05, 0.02, PAL.amber); c.vx = rnd(-3, 3); c.vy = rnd(0, 3); c.vz = rnd(-3, 3); c.g = 12; c.w = 0.05; c.st = 0.04; c.ease = E_LIN; }
      }
      if (fa.y <= fa.base + 0.3 || fa.t > 3) {   // base: the floor it falls onto (a deck, or the ground)
        fa.on = false;
        explode(fa.x, fa.base + 0.35, fa.z, FLAV.drone, 1, F_WORD | F_SCORCH | F_RING | (fa.quiet ? F_QUIET : 0));
      }
    }
  }
  function updCans(dt, dE) {
    var cm = B.canMesh, M = cm.instanceMatrix.array, FXA = B.canFx.array, cHi = -1, lvl = B.level, red = reduce();
    for (var i = 0; i < CAN_CAP; i++) {
      var c = cans[i], o = i * 16;
      if (!c.on || c.state === 2 || !lvl || !lvl.zones[c.zone] || !lvl.zones[c.zone].group.visible) { if (c.on && c.state !== 2) cHi = i; zero16(M, o); continue; }
      cHi = i; c.t += dt; c.flash = Math.max(0, c.flash - dE);
      var jit = 0, sc = 1, fl = c.flash > 0 ? 1 : 0;
      if (c.state === 1) {
        c.fuse -= dE; c.hiss -= dE;
        var ph = 1 - c.fuse / c.fuse0;
        fl = Math.sin(c.t * (red ? 9 : 30 + 40 * ph)) > 0 ? 1 : 0;   // Reduce flashing: a slow blink
        sc = 1 + 0.07 * ph + 0.03 * Math.sin(c.t * 70); jit = 0.04 * ph;
        if (c.hiss <= 0) { c.hiss = 0.03; var hc = card(C.streak, M_STREAK, c.x + 0.11, 0.95, c.z, 0.22, 0.05, 0.02, Math.random() < 0.5 ? PAL.amber : 0xFFFDF7); hc.vx = rnd(-1.5, 1.5); hc.vy = rnd(3, 5); hc.vz = rnd(-1.5, 1.5); hc.g = 10; hc.w = 0.045; hc.st = 0.04; hc.ease = E_LIN; }
        if (c.fuse <= 0) { blowCan(c); zero16(M, o); continue; }
      }
      var th = c.idx * 1.7 + (jit ? Math.sin(c.t * 80) * jit : 0), co = Math.cos(th) * sc, si = Math.sin(th) * sc, sy = sc * (1 + (sc - 1) * 0.5);
      M[o] = co; M[o + 1] = 0; M[o + 2] = -si; M[o + 3] = 0;
      M[o + 4] = 0; M[o + 5] = sy; M[o + 6] = 0; M[o + 7] = 0;
      M[o + 8] = si; M[o + 9] = 0; M[o + 10] = co; M[o + 11] = 0;
      M[o + 12] = c.x + (jit ? Math.sin(c.t * 97) * jit * 0.5 : 0); M[o + 13] = 0; M[o + 14] = c.z; M[o + 15] = 1;
      FXA[i * 2] = fl; FXA[i * 2 + 1] = 0;
    }
    cm.count = cHi + 1; cm.visible = cHi >= 0; cm.instanceMatrix.needsUpdate = true; B.canFx.needsUpdate = true;
  }
  function updPuffs(dE) {
    var pm = B.puffMesh, M = pm.instanceMatrix.array, CA = pm.instanceColor.array, PA = B.puffP.array, ex = _cam.x, ey = _cam.y, ez = _cam.z, hi = -1, s = 0, dis = 0, col = 0;
    for (var i = 0; i <= puffHi; i++) {
      var p = puffs[i]; if (!p.on) continue;
      var o = i * 16;
      hi = i; p.t += dE;
      if (p.t < 0) { zero16(M, o); continue; }
      var k = p.t / p.life;
      if (k >= 1) { freePuff(p); zero16(M, o); continue; }
      var dr = Math.max(0, 1 - p.drag * dE);
      p.vx *= dr; p.vz *= dr; p.vy = p.vy * dr + p.buoy * dE;
      p.x += p.vx * dE; p.y += p.vy * dE; p.z += p.vz * dE;
      if (p.kind === P_FIRE) {
        if (k < 0.14) { var e1 = k / 0.14 - 1; s = p.s1 * (0.3 + 0.8 * (1 + 2.7 * e1 * e1 * e1 + 1.7 * e1 * e1)); } else s = p.s1 * (1.08 - 0.3 * (k - 0.14) / 0.86);
        dis = k < 0.5 ? 0 : (k - 0.5) / 0.5 * 1.02;
        col = k < 0.07 ? 0 : k < 0.2 ? 1 : k < 0.38 ? 2 : k < 0.56 ? 3 : k < 0.74 ? 4 : 5;
      } else {
        s = p.s1 * (0.45 + 0.55 * (1 - (1 - k) * (1 - k)));
        dis = k < 0.4 ? 0 : (k - 0.4) / 0.6 * 1.02;
        col = k < 0.12 ? 6 : 7;
      }
      var ddx = p.x - ex, ddy = p.y - ey, ddz = p.z - ez;
      if (ddx * ddx + ddy * ddy + ddz * ddz < (s + 0.35) * (s + 0.35)) { zero16(M, o); continue; }   // never paint the whole screen
      zero16(M, o); M[o] = s; M[o + 5] = s * p.sq; M[o + 10] = s; M[o + 12] = p.x; M[o + 13] = p.y; M[o + 14] = p.z; M[o + 15] = 1;
      CA[i * 3] = RAMP[col * 3]; CA[i * 3 + 1] = RAMP[col * 3 + 1]; CA[i * 3 + 2] = RAMP[col * 3 + 2];
      PA[i * 3] = p.hl; PA[i * 3 + 1] = dis; PA[i * 3 + 2] = p.seed;
    }
    puffHi = hi; pm.count = hi + 1; pm.visible = hi >= 0;
    if (hi >= 0) { pm.instanceMatrix.needsUpdate = true; pm.instanceColor.needsUpdate = true; B.puffP.needsUpdate = true; pm.material.uniforms.uDot.value = 5.5 * (IB.Render.pixelRatio || 1); }
  }
  // fire ramp (paper, yellow, amber, tangerine, red, cooling ink) then smoke (two inks), as linear rgb triples
  var RAMP = new Float32Array(24);
  [PAL.paper, 0xFFE15A, PAL.amber, PAL.tangerine, PAL.red, 0x4A3A48, 0x4A3F55, 0x2A2433].forEach(function (h, i) { _c.setHex(h); RAMP[i * 3] = _c.r; RAMP[i * 3 + 1] = _c.g; RAMP[i * 3 + 2] = _c.b; });
  function updCards(dE, cam) {
    var mm = B.cardMesh, M = mm.instanceMatrix.array, CA = mm.instanceColor.array, AA = B.cardA.array, hi = -1;
    var me = cam.matrixWorld.elements, rx = me[0], ry = me[1], rz = me[2], ux = me[4], uy = me[5], uz = me[6], fx = me[8], fy = me[9], fz = me[10];
    var ex = _cam.x, ey = _cam.y, ez = _cam.z;
    for (var i = 0; i <= cardHi; i++) {
      var c = cards[i]; if (!c.on) continue;
      var o = i * 16;
      hi = i; c.t += dE;
      if (c.t < 0) { zero16(M, o); continue; }
      var k = c.t / c.life;
      if (k >= 1) { freeCard(c); zero16(M, o); continue; }
      var mode = c.mode;
      if (mode !== M_SEG && mode !== M_TRACER) {
        var dg = Math.max(0, 1 - c.drag * dE);
        c.vx *= dg; c.vz *= dg; c.vy = c.vy * dg - c.g * dE;
        c.x += c.vx * dE; c.y += c.vy * dE; c.z += c.vz * dE;
        if (c.y < c.floor) { c.y = c.floor; c.vy = Math.abs(c.vy) * 0.3; c.vx *= 0.5; c.vz *= 0.5; c.vr *= 0.5; }
      }
      c.rot += c.vr * dE;
      var s = c.ease === E_POP ? (k < 0.28 ? c.s0 + (c.s1 * 1.12 - c.s0) * (k / 0.28) : c.s1 * (1.12 - 0.5 * (k - 0.28) / 0.72)) :
        c.ease === E_LIN ? c.s0 + (c.s1 - c.s0) * k : c.s0 + (c.s1 - c.s0) * (1 - (1 - k) * (1 - k) * (1 - k));
      var a = c.a0 * (k < c.fd ? 1 : 1 - (k - c.fd) / (1 - c.fd));
      // basis: X (ax..), Y (bx..), Z (nx..), centre (px..)
      var ax, ay, az, bx, by, bz, nx, ny, nz, px, py, pz, cr, sr;
      if (mode === M_BILL) {
        cr = Math.cos(c.rot) * s; sr = Math.sin(c.rot) * s;
        ax = rx * cr + ux * sr; ay = ry * cr + uy * sr; az = rz * cr + uz * sr;
        bx = ux * cr - rx * sr; by = uy * cr - ry * sr; bz = uz * cr - rz * sr;
        nx = fx; ny = fy; nz = fz; px = c.x; py = c.y; pz = c.z;
      } else if (mode === M_GROUND) {
        cr = Math.cos(c.rot) * s; sr = Math.sin(c.rot) * s;
        ax = cr; ay = 0; az = -sr; bx = -sr; by = 0; bz = -cr; nx = 0; ny = 1; nz = 0; px = c.x; py = c.y; pz = c.z;
      } else {
        var len, wid;
        if (mode === M_STREAK) {
          var sp2 = Math.sqrt(c.vx * c.vx + c.vy * c.vy + c.vz * c.vz);
          if (sp2 > 1e-3) { c.dx = c.vx / sp2; c.dy = c.vy / sp2; c.dz = c.vz / sp2; }
          ax = c.dx; ay = c.dy; az = c.dz;
          len = Math.max(s * 2, s + sp2 * c.st); wid = c.w * (1 - k * 0.5);
          px = c.x - ax * len * 0.4; py = c.y - ay * len * 0.4; pz = c.z - az * len * 0.4;
        } else if (mode === M_SEG) {
          if (c.flick > 0) { c.ft -= dE; if (c.ft <= 0) { c.ft = c.flick; var cl = c.cell === C.zig0 ? C.zig1 : C.zig0; c.cell = cl; var Rr = RECT[cl], RA = B.cardRect.array; RA[i * 4] = Rr[0]; RA[i * 4 + 1] = Rr[1]; RA[i * 4 + 2] = Rr[2]; RA[i * 4 + 3] = Rr[3]; B.cardRect.needsUpdate = true; c.w = -c.w; } }
          ax = c.ex - c.x; ay = c.ey - c.y; az = c.ez - c.z; len = Math.sqrt(ax * ax + ay * ay + az * az);
          if (len < 1e-4) { zero16(M, o); continue; }
          ax /= len; ay /= len; az /= len; wid = c.w < 0 ? -s : s;
          px = (c.x + c.ex) * 0.5; py = (c.y + c.ey) * 0.5; pz = (c.z + c.ez) * 0.5;
        } else {   // tracer: a streak that flies down the shot line
          ax = c.ex - c.x; ay = c.ey - c.y; az = c.ez - c.z; var Lt = Math.sqrt(ax * ax + ay * ay + az * az) || 1;
          ax /= Lt; ay /= Lt; az /= Lt;
          var f1 = Math.min(Lt, c.t * c.sp), f0 = Math.max(0, f1 - c.seg);
          if (f0 >= Lt - 0.05) { zero16(M, o); continue; }
          var mid = (f0 + f1) * 0.5; len = f1 - f0; wid = c.w;
          px = c.x + ax * mid; py = c.y + ay * mid; pz = c.z + az * mid;
        }
        // face the camera around the axis: b = normalize(toCam x a), n = a x b
        var tx = ex - px, ty = ey - py, tz = ez - pz;
        bx = ty * az - tz * ay; by = tz * ax - tx * az; bz = tx * ay - ty * ax;
        var bl = Math.sqrt(bx * bx + by * by + bz * bz);
        if (bl < 1e-6) { bx = 0; by = 1; bz = 0; } else { bx /= bl; by /= bl; bz /= bl; }
        nx = ay * bz - az * by; ny = az * bx - ax * bz; nz = ax * by - ay * bx;
        if (len < 0.01) len = 0.01;
        ax *= len; ay *= len; az *= len; bx *= wid; by *= wid; bz *= wid;
      }
      M[o] = ax; M[o + 1] = ay; M[o + 2] = az; M[o + 3] = 0;
      M[o + 4] = bx; M[o + 5] = by; M[o + 6] = bz; M[o + 7] = 0;
      M[o + 8] = nx; M[o + 9] = ny; M[o + 10] = nz; M[o + 11] = 0;
      M[o + 12] = px; M[o + 13] = py; M[o + 14] = pz; M[o + 15] = 1;
      CA[i * 3] = c.r; CA[i * 3 + 1] = c.gg; CA[i * 3 + 2] = c.b;
      AA[i] = a;
    }
    cardHi = hi; mm.count = hi + 1; mm.visible = hi >= 0;
    if (hi >= 0) { mm.instanceMatrix.needsUpdate = true; mm.instanceColor.needsUpdate = true; B.cardA.needsUpdate = true; }
  }
  // words: pop 0.3 -> 1.2 -> 1.0, wobble, hold, shrink away
  function updWords(dE, cam) {
    var wm = B.wordMesh, M = wm.instanceMatrix.array, WA = B.wordA.array, hi = -1;
    var me = cam.matrixWorld.elements, rx = me[0], ry = me[1], rz = me[2], ux = me[4], uy = me[5], uz = me[6];
    for (var i = 0; i < WORD_CAP; i++) {
      var w = words[i], o = i * 16;
      if (!w.on) { zero16(M, o); continue; }
      w.t += dE; var tt = w.t;
      if (tt >= 0.82) { w.on = false; zero16(M, o); continue; }
      hi = i;
      var kk = tt < 0.09 ? 0.3 + tt / 0.09 * 0.92 : tt < 0.17 ? 1.22 - (tt - 0.09) / 0.08 * 0.22 : tt < 0.62 ? 1 : 1 - (tt - 0.62) / 0.2 * 0.85;
      w.y += dE * 0.35;
      var dxw = w.x - _cam.x, dyw = w.y - _cam.y, dzw = w.z - _cam.z, dw = Math.sqrt(dxw * dxw + dyw * dyw + dzw * dzw);
      var dk = Math.min(1, dw / 4.5) * Math.max(1, dw / 18), ww = w.size * 1.65 * kk * dk, wh = ww * (166 / 507);
      var rot = w.tilt + (tt < 0.2 ? Math.sin(tt * 60) * 0.05 : 0), co = Math.cos(rot), si = Math.sin(rot);
      M[o] = (rx * co + ux * si) * ww; M[o + 1] = (ry * co + uy * si) * ww; M[o + 2] = (rz * co + uz * si) * ww; M[o + 3] = 0;
      M[o + 4] = (ux * co - rx * si) * wh; M[o + 5] = (uy * co - ry * si) * wh; M[o + 6] = (uz * co - rz * si) * wh; M[o + 7] = 0;
      M[o + 8] = me[8]; M[o + 9] = me[9]; M[o + 10] = me[10]; M[o + 11] = 0;
      M[o + 12] = w.x; M[o + 13] = w.y; M[o + 14] = w.z; M[o + 15] = 1;
      WA[i] = tt < 0.62 ? 1 : 1 - (tt - 0.62) / 0.2;
    }
    wm.count = hi + 1; wm.visible = hi >= 0; wm.instanceMatrix.needsUpdate = true; B.wordA.needsUpdate = true;
  }
  function updBin(bin, dE) {
    var bm = bin.mesh, M = bm.instanceMatrix.array, hi = -1;
    if (!bin.n) { if (bm.visible) { bm.visible = false; bm.count = 0; } return; }
    for (var i = 0; i <= bin.hi; i++) {
      var e = bin.pool[i]; if (!e.on) continue;
      e.t += dE;
      if (e.t >= e.life) { e.on = false; bin.n--; zero16(M, i * 16); continue; }
      hi = i;
      e.vy -= 20 * dE; e.x += e.vx * dE; e.y += e.vy * dE; e.z += e.vz * dE;
      if (e.y < e.rest) {
        e.y = e.rest;
        if (e.vy < -1.5) { e.vy = -e.vy * 0.36; e.wx *= 0.6; e.wy *= 0.6; e.wz *= 0.6; e.vx *= 0.65; e.vz *= 0.65; }
        else { e.vy = 0; e.vx *= Math.max(0, 1 - 6 * dE); e.vz *= Math.max(0, 1 - 6 * dE); e.wx *= 0.85; e.wz *= 0.85; e.wy *= 0.9; e.smoke = -1; }
      }
      e.rx += e.wx * dE; e.ry += e.wy * dE; e.rz += e.wz * dE;
      if (e.smoke >= 0) { e.smoke -= dE; if (e.smoke <= 0 && e.t < 1 && roomy()) { e.smoke = 0.05; var c = card(C.dust, M_BILL, e.x, e.y, e.z, 0.5, 0.06, 0.2, 0x3A3346); c.vy = 0.3; c.a0 = 0.85; c.fd = 0.3; } }
      var shr = e.t > e.life - 0.3 ? (e.life - e.t) / 0.3 : 1;
      var ca = Math.cos(e.rx), sa = Math.sin(e.rx), cb = Math.cos(e.ry), sb = Math.sin(e.ry), cc = Math.cos(e.rz), sc2 = Math.sin(e.rz), sk = e.s * shr, o = i * 16;
      var ae = ca * cc, af = ca * sc2, be = sa * cc, bf = sa * sc2;   // Euler XYZ (three.js makeRotationFromEuler) x scale
      M[o] = cb * cc * sk; M[o + 1] = (af + be * sb) * sk; M[o + 2] = (bf - ae * sb) * sk; M[o + 3] = 0;
      M[o + 4] = -cb * sc2 * sk; M[o + 5] = (ae - bf * sb) * sk; M[o + 6] = (be + af * sb) * sk; M[o + 7] = 0;
      M[o + 8] = sb * sk; M[o + 9] = -sa * cb * sk; M[o + 10] = ca * cb * sk; M[o + 11] = 0;
      M[o + 12] = e.x; M[o + 13] = e.y; M[o + 14] = e.z; M[o + 15] = 1;
    }
    bin.hi = hi; bm.count = hi + 1; bm.visible = hi >= 0; bm.instanceMatrix.needsUpdate = true;
  }
  function updCasings(dt) {
    var csm = B.caseMesh, M = csm.instanceMatrix.array, hi = -1;
    for (var i = 0; i < CASE_CAP; i++) {
      var cs = casings[i]; if (!cs.on) { zero16(M, i * 16); continue; }
      cs.t += dt;
      if (cs.t > 0.6) { cs.on = false; zero16(M, i * 16); continue; }
      hi = i;
      cs.vy -= 7 * dt; cs.x += cs.vx * dt; cs.y += cs.vy * dt; cs.z += cs.vz * dt;
      cs.rx += cs.wx * dt; cs.ry += cs.wy * dt; cs.rz += cs.wz * dt;
      var ca = Math.cos(cs.rx), sa = Math.sin(cs.rx), cb = Math.cos(cs.ry), sb = Math.sin(cs.ry), cc = Math.cos(cs.rz), sc2 = Math.sin(cs.rz), sk = cs.s, o = i * 16;
      var ae = ca * cc, af = ca * sc2, be = sa * cc, bf = sa * sc2;   // Euler XYZ (three.js makeRotationFromEuler) x scale
      M[o] = cb * cc * sk; M[o + 1] = (af + be * sb) * sk; M[o + 2] = (bf - ae * sb) * sk; M[o + 3] = 0;
      M[o + 4] = -cb * sc2 * sk; M[o + 5] = (ae - bf * sb) * sk; M[o + 6] = (be + af * sb) * sk; M[o + 7] = 0;
      M[o + 8] = sb * sk; M[o + 9] = -sa * cb * sk; M[o + 10] = ca * cb * sk; M[o + 11] = 0;
      M[o + 12] = cs.x; M[o + 13] = cs.y; M[o + 14] = cs.z; M[o + 15] = 1;
    }
    csm.count = hi + 1; csm.visible = hi >= 0; csm.instanceMatrix.needsUpdate = true;
  }
  B.update = function (dt, cam, player) {
    if (!B.ready || !(dt >= 0)) return;
    var g = IB.Game, dE = dt;
    if (g && g.mode === 'play' && g.hitstop > 0) dE = dt * 0.2;   // effects crawl during a hit-stop
    if (g && g.mode !== 'play' && g.mode !== 'title') dE = g.mode === 'loading' || g.mode === 'results' ? dt : 0;   // paused / menus: frozen
    B.wordT += dt;
    cam.updateMatrixWorld(); _cam.setFromMatrixPosition(cam.matrixWorld);
    updEvents(dE); updFallers(dE); updCans(dt, dE); updPuffs(dE); updCards(dE, cam); updWords(dE, cam);
    for (var j = 0; j < bins.length; j++) updBin(bins[j], dE);
    updCasings(dt);
    Scr.update(dt, player);
  };

  // ---------------- FX hooks ----------------
  var baseInit = FX.init;
  FX.init = function (scene) { baseInit.apply(FX, arguments); B.init(scene); };
  var baseUpdate = FX.update;
  FX.update = function (dt, cam, player) { baseUpdate.apply(FX, arguments); if (cam) B.update(dt, cam, player); };
  var baseClear = FX.clear;
  FX.clear = function () { baseClear.apply(FX, arguments); B.clear(); };
  var baseDrop = FX.dropGem;
  FX.dropGem = function (kind, x, y, z) { var g = baseDrop.apply(FX, arguments); if (g) B.gemBurst(kind, x, y, z); return g; };
  // comic words now come from Boom's atlas (one draw call for all of them)
  FX.initWords = function () { FX.words = null; };
  FX.word = function (text, x, y, z, size) { B.word(text, x, y, z, size, true); };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
