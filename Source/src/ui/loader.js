/* INKBOLT between-levels loader: a black screen with one real-3D gear (and a small meshing pinion) turning slowly
   and rocking in space. Toon-metal shading: banded diffuse, hard studio reflection bands, a crisp specular glint and a
   glowing fresnel rim that runs teal -> amber across the gear, on deep ink-purple gunmetal; additive halo sprites
   behind fake a soft bloom. Its own small WebGL renderer on its own canvas (created once, reused every load; the
   game renderer keeps building the next level meanwhile). Caption: level number, name, a hairline progress bar.
     IB.Loader.show({level, name, line}) / .progress(0..1) / .hide(cb, ms) / .visible()
   menus.js keeps the public API (M.loading / M.loadingProgress / M.loadingHide) and forwards here. */
(function (IB) {
  'use strict';
  var L = IB.Loader = { on: false };
  var root = null, cv = null, rd = null, scene = null, cam = null, rig = null, big = null, pin = null, halo = null, halo2 = null, raf = 0;
  var t0 = 0, last = 0, fadeT = null, hideT = 0, failed = false, prog = 0, shown = 0;
  var N1 = 16, N2 = 9;   // teeth: big gear and pinion (same tooth size, so pitch radii follow N)

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  // ---------- gear geometry ----------
  // n teeth on pitch radius rp; tooth depth from the module; spokes cut as rounded annular sectors
  function gearShape(n, rp, spokes, hub) {
    var add = rp * 0.115, ded = rp * 0.13, ro = rp + add, ri = rp - ded, step = Math.PI * 2 / n;
    var s = new THREE.Shape(), first = true;
    for (var i = 0; i < n; i++) {
      var a = i * step;
      // root land, flank up, tip land, flank down (slight taper reads as an involute at this size)
      var pts = [[ri, a - step * 0.5], [ri, a - step * 0.27], [ro, a - step * 0.15], [ro, a + step * 0.15], [ri, a + step * 0.27]];
      for (var j = 0; j < pts.length; j++) {
        var x = Math.cos(pts[j][1]) * pts[j][0], y = Math.sin(pts[j][1]) * pts[j][0];
        if (first) { s.moveTo(x, y); first = false; } else s.lineTo(x, y);
      }
    }
    s.closePath();
    // bore
    var bore = new THREE.Path(); bore.absarc(0, 0, rp * hub, 0, Math.PI * 2, true); s.holes.push(bore);
    if (spokes) {
      var r0 = rp * 0.36, r1 = ri - rp * 0.15, span = Math.PI * 2 / spokes, web = 0.34;   // web: spoke width as a share of the span
      for (var k = 0; k < spokes; k++) {
        var a0 = k * span + span * web / 2, a1 = (k + 1) * span - span * web / 2;
        var h = new THREE.Path();
        h.absarc(0, 0, r1, a0, a1, false);
        h.absarc(0, 0, r0, a1, a0, true);
        h.closePath();
        s.holes.push(h);
      }
    }
    return s;
  }
  function gearGeo(n, rp, depth, spokes, hub) {
    var g = new THREE.ExtrudeGeometry(gearShape(n, rp, spokes, hub), { depth: depth, bevelEnabled: true, bevelThickness: depth * 0.22, bevelSize: rp * 0.025, bevelSegments: 2, curveSegments: 14, steps: 1 });
    g.translate(0, 0, -depth / 2);
    g.computeVertexNormals();
    return g;
  }

  // ---------- toon metal ----------
  var VS = [
    'varying vec3 vN; varying vec3 vV; varying vec3 vO;',
    'void main() {',
    '  vec4 mv = modelViewMatrix * vec4(position, 1.0);',
    '  vN = normalize(normalMatrix * normal); vV = -mv.xyz; vO = position;',
    '  gl_Position = projectionMatrix * mv;',
    '}'
  ].join('\n');
  var FS = [
    'uniform vec3 uBase; uniform vec3 uDeep; uniform vec3 uRimA; uniform vec3 uRimB; uniform vec3 uL; uniform float uT; uniform float uR; uniform float uFade;',
    'varying vec3 vN; varying vec3 vV; varying vec3 vO;',
    'void main() {',
    '  vec3 N = normalize(vN); vec3 V = normalize(vV); vec3 Lr = normalize(uL);',
    '  if (!gl_FrontFacing) N = -N;',
    '  float ndl = dot(N, Lr);',
    // three hard diffuse bands
    '  float d = ndl > 0.55 ? 1.0 : ndl > 0.05 ? 0.6 : 0.28;',
    '  vec3 c = mix(uDeep, uBase, d);',
    // studio reflection: hard bands on the reflected vector (polished metal, toon edition)
    '  vec3 Rv = reflect(-V, N);',
    '  float band = smoothstep(0.30, 0.34, Rv.y) - smoothstep(0.52, 0.56, Rv.y);',
    '  band += 0.55 * (smoothstep(-0.62, -0.58, Rv.y) - smoothstep(-0.44, -0.40, Rv.y));',
    '  c += band * mix(uBase, uRimA, 0.25) * 0.6;',
    // specular glint
    '  vec3 H = normalize(Lr + V);',
    '  float sp = pow(max(dot(N, H), 0.0), 70.0);',
    '  c += smoothstep(0.45, 0.55, sp) * vec3(1.0, 0.97, 0.9) * 0.9;',
    // glowing rim: teal on one side of the gear, amber on the other, slowly travelling round
    '  float fr = 1.0 - max(dot(N, V), 0.0);',
    '  float ang = atan(vO.y, vO.x) + uT * 0.35;',
    '  vec3 rc = mix(uRimA, uRimB, 0.5 + 0.5 * sin(ang));',
    '  c += rc * (pow(fr, 2.4) * 1.6 + smoothstep(0.62, 0.7, fr) * 0.9);',
    // tooth tips and the outer edge glow a touch (radius-based), the bore stays dark
    '  float rr = length(vO.xy) / uR;',
    '  c += rc * smoothstep(0.95, 1.1, rr) * 0.45;',
    '  c *= mix(0.55, 1.0, smoothstep(0.1, 0.35, rr));',
    '  gl_FragColor = vec4(c * uFade, 1.0);',
    '}'
  ].join('\n');
  function metal(base, deep, rimA, rimB, rp) {
    return new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: FS, side: THREE.DoubleSide, uniforms: {
      uBase: { value: new THREE.Color(base) }, uDeep: { value: new THREE.Color(deep) }, uRimA: { value: new THREE.Color(rimA) }, uRimB: { value: new THREE.Color(rimB) },
      uL: { value: new THREE.Vector3(-0.45, 0.75, 0.6) }, uT: { value: 0 }, uR: { value: rp }, uFade: { value: 1 } } });
  }
  function edges(g, ca, cb, op) {
    var e = new THREE.EdgesGeometry(g, 28), pos = e.attributes.position, col = new Float32Array(pos.count * 3), A = new THREE.Color(ca), B = new THREE.Color(cb), c = new THREE.Color();
    for (var i = 0; i < pos.count; i++) {
      c.copy(A).lerp(B, 0.5 + 0.5 * Math.sin(Math.atan2(pos.getY(i), pos.getX(i))));
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    }
    e.setAttribute('color', new THREE.BufferAttribute(col, 3));
    var m = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: op, blending: THREE.AdditiveBlending, depthWrite: false });
    var l = new THREE.LineSegments(e, m); l.userData.op = op; return l;
  }
  function glowTex(stops) {
    var c = document.createElement('canvas'); c.width = c.height = 128;
    var g = c.getContext('2d'), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    stops.forEach(function (s) { gr.addColorStop(s[0], s[1]); });
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(c);
  }
  function sprite(tex, size, op) {
    var m = new THREE.SpriteMaterial({ map: tex, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true, opacity: op });
    var s = new THREE.Sprite(m); s.scale.set(size, size, 1); s.renderOrder = -1; return s;
  }

  function build() {
    if (rd || failed) return !!rd;
    try {
      rd = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: false, powerPreference: 'low-power' });
    } catch (e) { failed = true; rd = null; return false; }
    rd.setClearColor(0x000000, 1);
    scene = new THREE.Scene();
    cam = new THREE.PerspectiveCamera(30, 1, 0.1, 50); cam.position.set(0, 0, 8.2);
    rig = new THREE.Group(); scene.add(rig);
    var rp1 = 1.25, rp2 = rp1 * N2 / N1;
    var g1 = gearGeo(N1, rp1, 0.34, 5, 0.17), g2 = gearGeo(N2, rp2, 0.26, 0, 0.26);
    big = new THREE.Mesh(g1, metal('#43357F', '#0A0716', '#29F0DE', '#FFB21E', rp1));
    pin = new THREE.Mesh(g2, metal('#C8852A', '#1E0F05', '#8A6CFF', '#29F0DE', rp2));
    // hub boss on the big gear
    var boss = new THREE.Mesh(new THREE.CylinderGeometry(rp1 * 0.3, rp1 * 0.3, 0.46, 6, 1), metal('#6B5BC0', '#0B0818', '#FFB21E', '#29F0DE', rp1 * 0.3));
    boss.rotation.x = Math.PI / 2; big.add(boss);
    // neon edging: the hard edges as additive lines, teal -> amber round the gear (purple -> teal on the pinion)
    big.add(edges(g1, '#29F0DE', '#FFB21E', 0.5)); pin.add(edges(g2, '#8A6CFF', '#29F0DE', 0.45));
    var dist = rp1 + rp2, th = -0.72;   // pinion sits up-right of the big gear, a little behind
    pin.position.set(Math.cos(th) * dist, Math.sin(th) * dist, -0.04);
    pin.userData.th = th;
    var grp = new THREE.Group(); grp.add(big); grp.add(pin); grp.position.set(-0.5, 0.44, 0);   // centres the pair
    rig.add(grp);
    halo = sprite(glowTex([[0, 'rgba(120,90,255,.6)'], [0.35, 'rgba(60,40,160,.24)'], [0.9, 'rgba(0,0,0,0)']]), 4.2, 0.9);
    halo2 = sprite(glowTex([[0, 'rgba(41,240,222,.55)'], [0.4, 'rgba(18,120,130,.16)'], [0.9, 'rgba(0,0,0,0)']]), 2.4, 0.7);
    halo.position.z = -1.5; halo2.position.set(0.9, -0.6, -1);
    scene.add(halo); scene.add(halo2);
    return true;
  }
  function size() {
    if (!rd) return;
    var w = cv.clientWidth || 300, h = cv.clientHeight || 300, pr = Math.min(2, window.devicePixelRatio || 1);
    if (cv.width !== Math.round(w * pr) || cv.height !== Math.round(h * pr)) { rd.setPixelRatio(pr); rd.setSize(w, h, false); }
    cam.aspect = w / h; cam.updateProjectionMatrix();
  }
  function frame(now) {
    if (!L.on) { raf = 0; return; }
    raf = requestAnimationFrame(frame);
    var t = (now - t0) / 1000, dt = Math.min(0.1, (now - last) / 1000); last = now;
    if (!rd) return;
    size();
    var spin = t * 0.55;   // slow: about one turn in 11 s
    big.rotation.z = -spin;
    pin.rotation.z = pin.userData.th + Math.PI - Math.PI / N2 + (pin.userData.th + spin) * N1 / N2;
    // the whole assembly rocks and tilts slowly in space
    rig.rotation.x = -0.42 + Math.sin(t * 0.7) * 0.16;
    rig.rotation.y = 0.5 + Math.sin(t * 0.45 + 0.6) * 0.34;
    rig.rotation.z = Math.sin(t * 0.33) * 0.05;
    // fade in (gear rises out of the dark), fade out on hide
    var k = Math.min(1, t / 0.6); k = k * k * (3 - 2 * k);
    var f = fadeT ? Math.max(0, 1 - (now - fadeT.at) / fadeT.ms) : 1;
    var a = k * f;
    rig.scale.setScalar(0.86 + 0.14 * k);
    [big, pin, big.children[0]].forEach(function (m) { m.material.uniforms.uT.value = t; m.material.uniforms.uFade.value = a; });
    big.children[1].material.opacity = big.children[1].userData.op * a * (0.8 + 0.2 * Math.sin(t * 2.1));
    pin.children[0].material.opacity = pin.children[0].userData.op * a;
    halo.material.opacity = (0.75 + Math.sin(t * 1.7) * 0.12) * a; halo2.material.opacity = (0.5 + Math.sin(t * 2.3 + 1) * 0.15) * a;
    rd.render(scene, cam);
    void dt;
  }

  L.show = function (d) {
    d = d || {};
    root = document.getElementById('loading'); if (!root) return;
    clearTimeout(hideT); fadeT = null;
    if (!cv) { cv = document.createElement('canvas'); cv.className = 'ldr-cv'; cv.setAttribute('aria-hidden', 'true'); }
    root.innerHTML = '<div class="ldr-stage"></div><div class="ldr-cap">' +
      '<span class="ldr-lv">Level <b>' + ('0' + (d.level || 1)).slice(-2) + '</b></span>' +
      '<h2 class="ldr-name">' + esc(d.name || '') + '</h2>' +
      (d.line ? '<p class="ldr-line">' + esc(d.line) + '</p>' : '') +
      '<div class="ldr-bar"><i id="ldFill"></i></div><span class="ldr-pct" id="ldPct">0%</span></div>';
    root.querySelector('.ldr-stage').appendChild(cv);
    root.className = 'ldr';
    root.hidden = false;
    root.setAttribute('role', 'status'); root.setAttribute('aria-label', 'Loading level ' + (d.level || 1));
    L.on = true; shown = performance.now(); t0 = last = shown;
    build(); size();
    if (!raf) raf = requestAnimationFrame(frame);
    L.progress(0);
  };
  L.progress = function (f) {
    if (!root || root.hidden) return;
    prog = Math.max(0, Math.min(1, f || 0));
    var fill = document.getElementById('ldFill'), pct = document.getElementById('ldPct');
    if (fill) fill.style.transform = 'scaleX(' + prog.toFixed(3) + ')';
    if (pct) pct.textContent = Math.round(prog * 100) + '%';
  };
  // fade out (ms, default 320); cb once gone
  L.hide = function (cb, ms) {
    if (!root || root.hidden) { if (cb) cb(); return; }
    ms = ms == null ? 320 : ms;
    L.progress(1);
    fadeT = { at: performance.now(), ms: ms };
    root.classList.add('out'); root.style.setProperty('--ldr-out', ms + 'ms');
    clearTimeout(hideT);
    hideT = setTimeout(function () {
      L.on = false; root.hidden = true; root.className = 'ldr'; root.innerHTML = ''; fadeT = null;
      if (cb) cb();
    }, ms + 20);
  };
  L.visible = function () { return !!root && !root.hidden; };
  L.elapsed = function () { return L.on ? performance.now() - shown : 0; };
})(window.IB = window.IB || {});
