/* INKBOLT enemy health bars: a slim slanted bar floating just above each robot (Borderlands / modern-FPS style).
     Shows while a robot is hurt and within range, while it is under the crosshair, and for a few seconds after a hit;
     a robot at full health that is not targeted stays clean. The fill drains smoothly with a delayed "chip" segment
     (the damage just taken) that follows after a short hold; a shield / armour row sits on top when a robot has one
     (r.shield / r.maxShield); a white flash on every hit. The left tab carries the robot type's colour. Rogue robots
     (Handy Helpers, r.rogue > 0) fight for the player: their bar is teal ("ally"), the top row counts down their time.
   Rendering: ONE instanced quad mesh (one draw call for every bar), billboarded in the vertex shader, sized in screen
   pixels (world-sized up close, never smaller than a legible minimum far away), depth-tested so walls and crates
   cover it, drawn without depth writes and without fog. The fragment shader draws the frame, segments, chip and
   anti-aliased slanted ends from pixel coordinates, so it stays crisp at any distance. Per frame: one pass over the
   robot pool, a handful of typed-array writes, no allocation. Rides FX.update (after the camera is placed). */
(function (IB) {
  'use strict';
  var FX = IB.FX = IB.FX || {};
  var HB = IB.HPBars = { cap: 24, range: 30, shown: 0 };
  var MAX = 24;                     // bars drawn at once (closest / most relevant win); keeps a 40-robot swarm readable
  var mesh = null, geo = null, aPos, aVal, aMeta, aCol, uni = null, _v = null, _d = null, _c = null;
  var TYPE_COL = {};                // robot type -> THREE.Color of its tab
  var TOP = { crawler: 0.98, gunner: 1.12, bomber: 1.0, drone: 0.74, soldier: 1.98, blader: 1.02, mech: 1.98, grenadier: 1.98, hawk: 0.72 };   // model top above r.y (m); others: hit capsule top + 0.3
  var list = [], ALLY = null;                    // scratch: robots that want a bar this frame

  var VS = [
    'attribute vec3 iPos; attribute vec4 iVal; attribute vec4 iMeta; attribute vec3 iCol;',
    'uniform float uPx; uniform float uS;',
    'varying vec2 vP; varying vec2 vSz; varying vec4 vVal; varying vec4 vMeta; varying vec3 vCol;',
    'void main() {',
    '  vec4 mv = viewMatrix * vec4(iPos, 1.0);',
    '  float d = max(0.5, -mv.z);',
    // width: 0.9 m in the world (scaled per type), clamped to a pixel range so far bars stay legible, near ones calm
    '  float w = clamp(1.0 * iMeta.x * uPx / d, 64.0 * iMeta.x * uS, 132.0 * iMeta.x * uS);',
    '  float h = (iVal.z >= 0.0 ? 15.0 : 11.0) * uS * mix(1.0, 1.18, step(1.25, iMeta.x));',
    '  w = floor(w + 0.5); h = floor(h + 0.5);',
    '  vSz = vec2(w, h); vP = (position.xy + 0.5) * vSz;',
    '  vVal = iVal; vMeta = iMeta; vCol = iCol;',
    '  mv.xy += (position.xy + vec2(0.0, 0.5)) * vSz * (d / uPx) + vec2(0.0, 5.0 * uS * d / uPx);',   // anchor = bar bottom, 5 px clear
    '  mv.z += min(0.35, d * 0.1);',   // a little toward the camera: never sinks into its own robot
    '  gl_Position = projectionMatrix * mv;',
    '}'
  ].join('\n');

  var FS = [
    'uniform float uAA;',
    'varying vec2 vP; varying vec2 vSz; varying vec4 vVal; varying vec4 vMeta; varying vec3 vCol;',
    // coverage of the slanted parallelogram [x0, x1] x [y0, y1] (ends lean like "/"), with a 1 px soft edge
    'float para(vec2 p, float x0, float x1, float y0, float y1, float sl) {',
    '  float xs = p.x - (p.y - y0) * sl;',
    '  float a = clamp((xs - x0) / uAA + 0.5, 0.0, 1.0) * clamp((x1 - (y1 - y0) * sl - xs) / uAA + 0.5, 0.0, 1.0);',
    '  return a * clamp((p.y - y0) / uAA + 0.5, 0.0, 1.0) * clamp((y1 - p.y) / uAA + 0.5, 0.0, 1.0);',
    '}',
    'void main() {',
    '  vec2 p = vP; float W = vSz.x, H = vSz.y, sl = 0.75;',
    '  float hp = vVal.x, chip = vVal.y, sh = vVal.z, A = vVal.w, flash = vMeta.z, segs = vMeta.y;',
    // ink backing (comic outline) and a dark glass face
    '  float outer = para(p, 0.0, W, 0.0, H, sl);',
    '  if (outer <= 0.0) discard;',
    '  vec3 col = vec3(0.03, 0.025, 0.06); float al = 0.92;',
    '  float face = para(p, 2.0, W - 2.0, 2.0, H - 2.0, sl);',
    '  col = mix(col, vec3(0.10, 0.10, 0.16), face * 0.85);',
    // type tab at the left end
    '  float tab = para(p, 2.0, 6.5, 2.0, H - 2.0, sl);',
    '  col = mix(col, vCol, tab);',
    // rows: health (bottom) and, with a shield, a thinner shield row on top
    '  float x0 = 8.0, x1 = W - 2.5;',
    '  float hy1 = sh >= 0.0 ? H * 0.6 : H - 2.5;',
    '  float hRow = para(p, x0, x1, 2.5, hy1, sl);',
    '  float xs = p.x - (p.y - 2.5) * sl;',
    '  float iw = (x1 - x0) - (hy1 - 2.5) * sl;',
    '  float u = (xs - x0) / iw;',
    // segment gaps (1 px)
    '  float segW = iw / segs;',
    '  float gap = step(segW - 1.0, mod(xs - x0, segW)) * step(0.5, segs - 1.0) * step(xs - x0, iw - 2.0);',
    '  float topHi = smoothstep(2.5, hy1, p.y);',
    '  float ally = vMeta.w;',   // rogue robots (Handy Helpers) fight for the player: teal bar
    '  vec3 hpCol = mix(mix(vec3(0.93, 0.20, 0.17), vec3(1.0, 0.45, 0.36), topHi), mix(vec3(0.07, 0.72, 0.66), vec3(0.36, 0.95, 0.88), topHi), ally);',
    '  hpCol = mix(hpCol, vec3(1.0), flash * 0.75);',
    '  vec3 chipCol = vec3(1.0, 0.93, 0.72);',
    '  vec3 empty = vec3(0.11, 0.10, 0.16);',
    '  vec3 fill = u < hp ? hpCol : (u < chip ? chipCol : empty);',
    '  fill = mix(fill, fill * 0.35, gap);',
    '  col = mix(col, fill, hRow);',
    // shield row
    '  if (sh >= 0.0) {',
    '    float sy0 = hy1 + 1.0, sy1 = H - 2.5;',
    '    float sRow = para(p, x0 + (sy0 - 2.5) * sl, x1 + (sy0 - 2.5) * sl, sy0, sy1, sl);',
    '    float su = (p.x - (p.y - sy0) * sl - x0 - (sy0 - 2.5) * sl) / iw;',
    '    vec3 sc = su < sh ? mix(mix(vec3(0.27, 0.78, 1.0), vec3(0.92, 1.0, 0.98), ally), vec3(0.80, 0.96, 1.0), flash * 0.6) : vec3(0.12, 0.17, 0.26);',
    '    col = mix(col, sc, sRow);',
    '  }',
    // hairline highlight along the top edge (glassy)
    '  float rim = para(p, 2.0, W - 2.0, H - 3.0, H - 2.0, sl);',
    '  col = mix(col, col + vec3(0.18), rim * 0.6);',
    '  gl_FragColor = vec4(col, outer * A * mix(al, 1.0, max(hRow, tab)));',
    '}'
  ].join('\n');

  function init() {
    if (mesh || !IB.Render || !IB.Render.scene || typeof THREE === 'undefined') return !!mesh;
    var base = new THREE.PlaneBufferGeometry(1, 1);
    geo = new THREE.InstancedBufferGeometry();
    geo.setIndex(base.index); geo.setAttribute('position', base.attributes.position);
    aPos = new THREE.InstancedBufferAttribute(new Float32Array(MAX * 3), 3);
    aVal = new THREE.InstancedBufferAttribute(new Float32Array(MAX * 4), 4);
    aMeta = new THREE.InstancedBufferAttribute(new Float32Array(MAX * 4), 4);
    aCol = new THREE.InstancedBufferAttribute(new Float32Array(MAX * 3), 3);
    [aPos, aVal, aMeta, aCol].forEach(function (a) { a.setUsage(THREE.DynamicDrawUsage); });
    geo.setAttribute('iPos', aPos); geo.setAttribute('iVal', aVal); geo.setAttribute('iMeta', aMeta); geo.setAttribute('iCol', aCol);
    geo.instanceCount = 0;
    uni = { uPx: { value: 500 }, uS: { value: 1 }, uAA: { value: 1 } };
    var mat = new THREE.ShaderMaterial({ uniforms: uni, vertexShader: VS, fragmentShader: FS, transparent: true, depthWrite: false, depthTest: true, fog: false });
    mesh = new THREE.Mesh(geo, mat);
    mesh.frustumCulled = false; mesh.renderOrder = 20; mesh.visible = false; mesh.name = 'hpbars';
    IB.Render.scene.add(mesh);
    _v = new THREE.Vector3(); _d = new THREE.Vector3(); _c = new THREE.Color(); ALLY = new THREE.Color('#2EEAD8');
    return true;
  }
  function typeColor(r) {
    var c = TYPE_COL[r.type];
    if (!c) { c = TYPE_COL[r.type] = new THREE.Color((r.def && r.def.color) || '#C9CFD6'); }
    return c;
  }
  function stateOf(r) {
    var h = r._hb;
    if (!h) h = r._hb = { on: false, hp: 0, disp: 1, chip: 1, hold: 0, dmgT: 99, tgtT: 99, a: 0, flash: 0, dieT: 0, x: 0, y: 0, z: 0, sh: -1, k: 0, dist: 0 };
    return h;
  }
  function hudHidden() { var el = IB.HUD && IB.HUD.el && IB.HUD.el.hud; return !el || el.hidden; }

  // what the crosshair points at (one robot ray + one world ray a frame)
  function targeted(cam) {
    var AI = IB.AI, G = IB.Game; if (!AI || !AI.raycast) return null;
    cam.getWorldDirection(_d);
    var o = cam.position, rh = AI.raycast(o.x, o.y, o.z, _d.x, _d.y, _d.z, 70);
    if (!rh) return null;
    var r = rh.robot, t = rh.t;
    var w = G && G.level && G.level.world;
    if (w && w.ray) { var wh = w.ray(o.x, o.y, o.z, _d.x, _d.y, _d.z, t); if (wh && wh.t < t) return null; }
    return r;
  }

  HB.update = function (dt, cam) {
    var AI = IB.AI;
    if (!AI || !AI.robots || !cam || !init()) return;
    if (hudHidden() || !IB.Game || IB.Game.mode === 'title') { mesh.visible = false; geo.instanceCount = 0; HB.shown = 0; return; }
    var R = IB.Render, VIS = AI.VIS || {};
    uni.uPx.value = (R.height / 2) / Math.tan(cam.fov * Math.PI / 360);
    var phone = document.body.classList.contains('touch-on') || Math.min(R.width, R.height) < 520;
    uni.uS.value = phone ? 0.86 : (R.height > 1300 ? 1.25 : 1);
    uni.uAA.value = 1 / Math.max(1, R.pixelRatio || 1) + 0.25;
    var tgt = targeted(cam), cx = cam.position.x, cz = cam.position.z;
    list.length = 0;
    for (var i = 0; i < AI.robots.length; i++) {
      var r = AI.robots[i], h = r._hb;
      if (!r.on) {
        // killed: the bar empties and fades where the robot stood
        if (h && h.on) { h.on = false; h.dieT = h.a > 0.05 ? 0.35 : 0; h.disp = 0; }
        if (h && h.dieT > 0) { h.dieT -= dt; h.chip = Math.max(0, h.chip - dt * 3); h.flash = Math.max(0, h.flash - dt * 5); h.k = h.a * Math.max(0, h.dieT / 0.35); if (h.dieT > 0) list.push(r); }
        continue;
      }
      if (r.state === 'pose') continue;
      h = stateOf(r);
      var max = r.maxHp || 1, frac = Math.max(0, Math.min(1, r.hp / max));
      if (!h.on) { h.on = true; h.hp = r.hp; h.disp = h.chip = frac; h.dmgT = 99; h.tgtT = 99; h.a = 0; h.flash = 0; h.dieT = 0; }
      if (r.hp < h.hp - 1e-4) { h.dmgT = 0; h.flash = 1; h.hold = 0.55; h.chip = Math.max(h.chip, h.disp); }
      else if (r.hp > h.hp + 1e-4) { h.chip = h.disp = frac; }
      h.hp = r.hp;
      var hasSh = r.maxShield > 0, ally = r.rogue > 0;
      // a hit the shield soaked flashes the bar too (and keeps it up like any hit)
      if (hasSh && h.shv !== undefined && (r.shield || 0) < h.shv - 1e-4) { h.dmgT = 0; h.flash = 1; }
      h.shv = r.shield || 0;
      // the top row: shield / armour, or for a rogue (ally) the seconds it has left
      h.sh = ally ? (isFinite(AI.rogueTime) ? Math.max(0, Math.min(1, r.rogue / (AI.rogueTime || 15))) : -1) : hasSh ? Math.max(0, Math.min(1, (r.shield || 0) / r.maxShield)) : -1;
      h.ally = ally;
      h.dmgT += dt; h.tgtT = r === tgt ? 0 : h.tgtT + dt;
      h.disp += (frac - h.disp) * Math.min(1, dt * 16);
      if (h.hold > 0) h.hold -= dt; else h.chip = Math.max(h.disp, h.chip - dt * 0.9);
      h.flash = Math.max(0, h.flash - dt * 6);
      var v = VIS[r.type] || {}, by = r.y - (r.crouch || 0) * 0.12 + (TOP[r.type] || (v.y1 || 0.9) + 0.3) + 0.08;
      h.x = r.x; h.y = by; h.z = r.z;
      var dx = r.x - cx, dz = r.z - cz, dist = Math.sqrt(dx * dx + dz * dz);
      var hurt = frac < 0.999 || (hasSh && h.sh < 0.999);
      var want = r.state !== 'spawn' && (h.tgtT < 1.1 || h.dmgT < 3 || ((hurt || ally) && dist < HB.range));
      h.a = want ? Math.min(1, h.a + dt / 0.12) : Math.max(0, h.a - dt / 0.45);
      var far = Math.max(0, Math.min(1, (HB.range + 14 - dist) / 10));
      h.k = h.a * (h.tgtT < 1.1 || h.dmgT < 3 ? Math.max(far, 0.6) : far);
      h.dist = dist;
      if (h.k > 0.01) list.push(r);
    }
    // too many: keep the most relevant (targeted, just hit, nearest)
    if (list.length > MAX) list.sort(function (a, b) { return score(a) - score(b); });
    var n = Math.min(MAX, list.length), P = aPos.array, Vv = aVal.array, M = aMeta.array, C = aCol.array;
    for (var k = 0; k < n; k++) {
      var rb = list[k], s = rb._hb, def = rb.def || {};
      P[k * 3] = s.x; P[k * 3 + 1] = s.y; P[k * 3 + 2] = s.z;
      Vv[k * 4] = s.disp; Vv[k * 4 + 1] = Math.max(s.chip, s.disp); Vv[k * 4 + 2] = s.sh; Vv[k * 4 + 3] = s.k;
      var baseHp = def.hp || 30;
      M[k * 4] = Math.max(0.9, Math.min(1.7, 1 + 0.42 * Math.log(baseHp / 40) / Math.LN2));
      M[k * 4 + 1] = Math.max(2, Math.min(14, Math.round((rb.maxHp || baseHp) / 12)));
      M[k * 4 + 2] = s.flash; M[k * 4 + 3] = rb.on && s.ally ? 1 : 0;
      var tc = rb.on && s.ally ? ALLY : typeColor(rb); C[k * 3] = tc.r; C[k * 3 + 1] = tc.g; C[k * 3 + 2] = tc.b;
    }
    geo.instanceCount = n; mesh.visible = n > 0; HB.shown = n;
    if (n) {
      aPos.needsUpdate = aVal.needsUpdate = aMeta.needsUpdate = aCol.needsUpdate = true;
      aPos.updateRange.count = n * 3; aVal.updateRange.count = n * 4; aMeta.updateRange.count = n * 4; aCol.updateRange.count = n * 3;
    }
  };
  function score(r) { var h = r._hb; return (h.tgtT < 0.05 ? -1000 : 0) + (h.dmgT < 1 ? -500 : 0) + (h.dist || 0) + (r.on ? 0 : 200); }
  HB.clear = function () {
    if (IB.AI && IB.AI.robots) IB.AI.robots.forEach(function (r) { if (r._hb) { r._hb.on = false; r._hb.dieT = 0; r._hb.a = 0; } });
    if (mesh) { geo.instanceCount = 0; mesh.visible = false; } HB.shown = 0;
  };
  // test / tuning hook: what is on screen
  HB.stats = function () {
    var out = []; if (!IB.AI) return out;
    IB.AI.robots.forEach(function (r) { var h = r._hb; if (h && h.k > 0.01 && (r.on || h.dieT > 0)) out.push({ type: r.type, hp: +h.disp.toFixed(3), chip: +h.chip.toFixed(3), a: +h.k.toFixed(2) }); });
    return { shown: HB.shown, bars: out };
  };

  var baseUpdate = FX.update;
  if (baseUpdate && !baseUpdate._hb) {
    FX.update = function (dt, cam) { baseUpdate.apply(FX, arguments); HB.update(dt, cam); };
    FX.update._hb = true;
  }
  var baseClear = FX.clear;
  if (baseClear && !baseClear._hb) { FX.clear = function () { baseClear.apply(FX, arguments); HB.clear(); }; FX.clear._hb = true; }
})(window.IB = window.IB || {});
