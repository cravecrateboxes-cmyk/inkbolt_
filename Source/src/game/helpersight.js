/* INKBOLT Handy Helpers sight (owner request): the player's helpers (robots turned rogue, ai.js r.rogue > 0) stay
   readable when he cannot see them.
     - Behind a wall, a crate or a floor (no line of sight from the camera to the robot's middle or its top): a blue
       ghost of the robot is drawn through whatever hides it: a soft fill with a bright rim, like a shadow outline.
     - Out of view (turned away, or off the side of the screen): a soft blue glow on the screen edge toward it, stronger
       the nearer it is. Turning that way shows it: in plain sight, or as the ghost if something is in the way.
   Robots built from instanced parts (ai.js AI.types) get a twin InstancedMesh per part that shares the part's
   geometry and draws only the hidden helpers' instances; the trooper rigs (trooperrig.js) get a skinned twin on the
   same skeleton. Twins are made on first use, so a run without helpers costs nothing.
   IB.HelperSight.update(G) runs every frame from game.js after the robots are posed, before the render. */
(function (IB) {
  'use strict';
  var HS = IB.HelperSight = { on: true, ghosts: 0, edges: 0 };
  var BLUE = new THREE.Color(0x3FA9FF), RANGE = 45, EDGE_RANGE = 32, MAX_EDGES = 4;
  var ZERO = new THREE.Matrix4().makeScale(0, 0, 0), _m = new THREE.Matrix4(), _v = new THREE.Vector3(), _cam = new THREE.Vector3();
  var twins = [], skinTwins = [], mats = null, edgeEls = [], edgeRoot = null;

  var GHOST_FRAG = [
    'uniform vec3 uCol; uniform float uPulse; varying vec3 vN; varying vec3 vV;',
    'void main() {',
    '  float rim = pow( 1.0 - abs( dot( normalize( vN ), normalize( vV ) ) ), 1.6 );',
    '  gl_FragColor = vec4( uCol * ( 0.8 + 0.6 * rim ), ( 0.16 + 0.62 * rim ) * uPulse );',
    '}'
  ].join('\n');
  function makeMats() {
    var uni = { uCol: { value: BLUE }, uPulse: { value: 1 } };
    var common = { uniforms: uni, transparent: true, depthTest: false, depthWrite: false, fragmentShader: GHOST_FRAG };
    var inst = new THREE.ShaderMaterial(Object.assign({}, common, {
      vertexShader: [
        'attribute vec3 aHull; varying vec3 vN; varying vec3 vV;',
        'void main() {',
        '  vec4 wp = modelMatrix * instanceMatrix * vec4( position, 1.0 );',
        '  vN = normalize( mat3( modelMatrix ) * mat3( instanceMatrix ) * normal ); vV = cameraPosition - wp.xyz;',
        '  gl_Position = projectionMatrix * viewMatrix * wp;',
        '  if ( dot( aHull, aHull ) > 0.0 ) gl_Position = vec4( 2.0, 2.0, 2.0, 1.0 );',   // the ink shell: not drawn
        '}'
      ].join('\n')
    }));
    var skin = new THREE.ShaderMaterial(Object.assign({}, common, {
      skinning: true,
      vertexShader: [
        '#include <common>', '#include <skinning_pars_vertex>',
        'attribute vec3 aHull; varying vec3 vN; varying vec3 vV;',
        'void main() {',
        '  #include <skinbase_vertex>', '  #include <beginnormal_vertex>', '  #include <skinnormal_vertex>',
        '  #include <begin_vertex>', '  #include <skinning_vertex>',
        '  vec4 wp = modelMatrix * vec4( transformed, 1.0 );',
        '  vN = normalize( mat3( modelMatrix ) * objectNormal ); vV = cameraPosition - wp.xyz;',
        '  gl_Position = projectionMatrix * viewMatrix * wp;',
        '  if ( dot( aHull, aHull ) > 0.0 ) gl_Position = vec4( 2.0, 2.0, 2.0, 1.0 );',
        '}'
      ].join('\n')
    }));
    mats = { inst: inst, skin: skin, uni: uni };
  }

  // the twin of one instanced part (made the first time a helper of that type hides)
  function twinOf(Pt) {
    if (Pt.ghost) return Pt.ghost;
    if (!mats) makeMats();
    var src = Pt.mesh, n = src.instanceMatrix.count;
    var g = new THREE.InstancedMesh(src.geometry, mats.inst, n);
    g.instanceMatrix.setUsage(THREE.DynamicDrawUsage); g.frustumCulled = false; g.renderOrder = 20; g.visible = false; g.count = 0;
    g.name = 'helperGhost';
    src.parent.add(g);
    Pt.ghost = g; twins.push(g);
    return g;
  }
  function skinTwin(mesh) {
    if (mesh.userData.ghost) return mesh.userData.ghost;
    if (!mats) makeMats();
    var g = new THREE.SkinnedMesh(mesh.geometry, mats.skin);
    g.bind(mesh.skeleton, mesh.bindMatrix);
    g.frustumCulled = false; g.renderOrder = 20; g.visible = false; g.name = 'helperGhost';
    mesh.add(g);   // follows the body (identity transform under it)
    mesh.userData.ghost = g; skinTwins.push(g);
    return g;
  }

  function hidden(r, v, world) {
    var c = (v.y0 + v.y1) * 0.5, t = v.y1;
    return !world.los(_cam.x, _cam.y, _cam.z, r.x, r.y + c, r.z) && !world.los(_cam.x, _cam.y, _cam.z, r.x, r.y + t, r.z);
  }

  // ---------------- edge glows (DOM: one soft blob per off-screen helper, on the screen border toward it)
  function edgeEl(i) {
    if (!edgeRoot) {
      edgeRoot = document.createElement('div'); edgeRoot.id = 'helperEdges'; edgeRoot.setAttribute('aria-hidden', 'true');
      edgeRoot.style.cssText = 'position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:4;';
      document.body.appendChild(edgeRoot);
    }
    while (edgeEls.length <= i) {
      var e = document.createElement('div');
      e.style.cssText = 'position:absolute;width:300px;height:300px;margin:-150px 0 0 -150px;border-radius:50%;opacity:0;' +
        'background:radial-gradient(closest-side,rgba(63,169,255,.55),rgba(63,169,255,.18) 55%,rgba(63,169,255,0));will-change:transform,opacity;';
      edgeRoot.appendChild(e); edgeEls.push(e);
    }
    return edgeEls[i];
  }

  HS.update = function (G) {
    var AI = IB.AI, R = IB.Render, ne = 0, ng = 0, i, k;
    for (i = 0; i < twins.length; i++) twins[i].visible = false;
    for (i = 0; i < skinTwins.length; i++) skinTwins[i].visible = false;
    var play = HS.on && G && G.mode === 'play' && !G.dead && G.level && AI && AI.robots && R && R.camera;
    if (play) {
      var cam = R.camera, world = G.level.world, W = window.innerWidth, H = window.innerHeight;
      cam.getWorldPosition(_cam);
      if (mats) mats.uni.uPulse.value = 0.85 + 0.15 * Math.sin(performance.now() * 0.005);
      for (i = 0; i < AI.robots.length; i++) {
        var r = AI.robots[i];
        if (!r.on || !(r.rogue > 0) || r.state === 'pose') continue;
        var T = AI.types[r.type], v = T && T.vis; if (!v) continue;
        var dx = r.x - _cam.x, dz = r.z - _cam.z, d = Math.hypot(dx, dz); if (d > RANGE) continue;
        // in view or not: the robot's middle in camera space
        _v.set(r.x, r.y + (v.y0 + v.y1) * 0.5, r.z).applyMatrix4(cam.matrixWorldInverse);
        var behind = _v.z > -0.1;
        var ndc = behind ? null : _v.clone().applyMatrix4(cam.projectionMatrix);
        var inView = ndc && Math.abs(ndc.x) < 1.02 && Math.abs(ndc.y) < 1.02;
        if (!inView) {
          if (d > EDGE_RANGE || ne >= MAX_EDGES) continue;
          // the edge point toward it: the camera-space direction (x right, y up), behind folds to the sides
          var ax = _v.x, ay = behind ? Math.min(0, _v.y) * 0.3 : _v.y;
          if (behind && Math.abs(ax) < 0.01) ax = 0.01;
          var s = Math.min((W * 0.5) / Math.max(1e-4, Math.abs(ax)), (H * 0.5) / Math.max(1e-4, Math.abs(ay)));
          var px = W * 0.5 + ax * s, py = H * 0.5 - ay * s;
          var e = edgeEl(ne++), a = 0.35 + 0.55 * (1 - d / EDGE_RANGE);
          e.style.transform = 'translate(' + px.toFixed(1) + 'px,' + py.toFixed(1) + 'px)'; e.style.opacity = a.toFixed(3);
          continue;
        }
        if (!hidden(r, v, world)) continue;
        // behind something: draw its ghost
        ng++;
        if (IB.TrooperRig && IB.TrooperRig.TYPES && IB.TrooperRig.TYPES[r.type]) {
          var Rg = IB.TrooperRig.live[r.type + r.slot];
          if (Rg) { var body = r.type === 'mech' && Rg.mech ? Rg.mech : Rg.mesh; if (body && body.visible) skinTwin(body).visible = true; }
        }
        for (k = 0; k < T.partList.length; k++) {
          var Pt = T.partList[k]; if (!Pt.fx || !Pt.mesh.visible) continue;   // light parts (lamps) have no ghost
          var g = twinOf(Pt);
          if (!g.visible) { g.visible = true; g.count = Pt.mesh.count; for (var z = 0; z < g.count; z++) g.setMatrixAt(z, ZERO); }
          for (var c = 0; c < Pt.count; c++) { var idx = r.slot * Pt.count + c; if (idx < g.count) { Pt.mesh.getMatrixAt(idx, _m); g.setMatrixAt(idx, _m); } }
          g.instanceMatrix.needsUpdate = true;
        }
      }
    }
    for (i = ne; i < edgeEls.length; i++) edgeEls[i].style.opacity = '0';
    HS.ghosts = ng; HS.edges = ne;
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
