/* INKBOLT sun shadows (tactical look, Stage 3). One directional shadow map, rendered only when needed
   (autoUpdate off): at level start, when the player's snapped box centre moves, and on frames where a gate, door or
   lift is moving. The box is orthographic, centred on the player (snapped to an 8 m grid and to whole shadow
   texels in light space) with the light 220 m back along the theme's sun direction (IB.Look.sunDir; the moved
   light is never read back). Shadows fade out over the last 8 m of the box (shader, surface.js).
   Casters use a hull-less depth material: the inverted ink shell would otherwise shadow its own object (trap T1).
   Indoor themes (no sky) and the potato tier have no shadow map (the pass is skipped entirely). */
(function (IB) {
  'use strict';
  var Sh = IB.Shadows = { on: false, renders: 0 };
  var depthMats = {}, center = null, sig = -1, R = null, lastKey = '';

  function depthMat(skinned) {
    var k = skinned ? 's' : 'n';
    if (depthMats[k]) return depthMats[k];
    var m = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, skinning: !!skinned });
    m.onBeforeCompile = function (sh) {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec3 aHull;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nif ( dot( aHull, aHull ) > 0.0 ) gl_Position = vec4( 2.0, 2.0, 2.0, 1.0 );');
    };
    m.customProgramCacheKey = function () { return 'ibhullless' + k; };
    return (depthMats[k] = m);
  }
  Sh.depthMat = depthMat;

  var TYPES = { pcfsoft: 'PCFSoftShadowMap', pcf: 'PCFShadowMap', basic: 'BasicShadowMap' };

  // level start (after IB.Look.begin): decide on / off, mark casters and receivers, fit and render once
  Sh.begin = function (level) {
    R = IB.Render;
    R.sun.target.position.set(0, 0, 0); R.sun.target.updateMatrixWorld();   // R.applyEnv set sun.position = the direction
    var r = R.renderer, Look = IB.Look, L = Look.cur, T = IB.LOOKS.tier(R.tier), env = (level.theme || {}).env || {};
    Sh.on = !!(Look.on && Look.shadows && L && env.sky && T.shadow > 0);
    r.shadowMap.enabled = Sh.on; R.sun.castShadow = Sh.on;
    center = null; sig = -1; Sh.renders = 0;
    if (!Sh.on) return;
    r.shadowMap.autoUpdate = false;
    r.shadowMap.type = THREE[TYPES[T.shadowType]] || THREE.PCFShadowMap;
    var s = R.sun.shadow;
    if (s.mapSize.x !== T.shadow) { s.mapSize.set(T.shadow, T.shadow); if (s.map) { s.map.dispose(); s.map = null; } }
    s.bias = -0.0006; s.normalBias = 0.03; s.radius = 2.2;
    Sh.span = T.shadowSpan;
    Look.U.uShEdge.value = 8 / (2 * Sh.span);
    if (!R.sun.target.parent) R.scene.add(R.sun.target);
    var clouds = new Set(level.cloudMeshes || []);
    level.root.traverse(function (o) {
      if (!(o.isMesh || o.isInstancedMesh)) return;
      var m = o.material;
      if (!m || !m.userData || !m.userData.look || m.transparent) return;
      o.receiveShadow = true;
      if (clouds.has(o) || o.userData.noShadow) return;
      if (level.zones.some(function (z) { return z.ground === o; })) return;   // floors have nothing below them (trap T14)
      if (o.geometry && o.geometry.attributes.aHull) { o.castShadow = true; o.customDepthMaterial = depthMat(o.isSkinnedMesh); }
    });
    lastKey = R.tier;
    Sh.refit(true);
  };

  // centre the box on the player; re-render when the snapped centre changed (or force)
  var _c = new THREE.Vector3(), _r = new THREE.Vector3(), _u = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0);
  Sh.refit = function (force) {
    if (!Sh.on) return;
    var G = IB.Game, p = G.player, dir = IB.Look.sunDir, s = R.sun.shadow, span = Sh.span;
    var px = p ? p.x : 0, pz = p ? p.z : 0, py = p ? p.y : 0;
    var cx = Math.round(px / 8) * 8, cz = Math.round(pz / 8) * 8, cy = Math.round(py / 8) * 8;
    if (!force && center && center.x === cx && center.z === cz && center.y === cy) return;
    center = { x: cx, y: cy, z: cz };
    // snap to whole texels in light space so a refit never makes the edges swim
    _r.crossVectors(UP, dir); if (_r.lengthSq() < 1e-6) _r.set(1, 0, 0); _r.normalize();
    _u.crossVectors(dir, _r).normalize();
    var tex = 2 * span / s.mapSize.x;
    _c.set(cx, cy, cz);
    var a = Math.round(_c.dot(_r) / tex) * tex, b = Math.round(_c.dot(_u) / tex) * tex, d = _c.dot(dir);
    _c.copy(_r).multiplyScalar(a).addScaledVector(_u, b).addScaledVector(dir, d);
    R.sun.target.position.copy(_c); R.sun.target.updateMatrixWorld();
    R.sun.position.copy(_c).addScaledVector(dir, 220); R.sun.updateMatrixWorld();
    var cam = s.camera; cam.left = -span; cam.right = span; cam.top = span; cam.bottom = -span; cam.near = 1; cam.far = 520; cam.updateProjectionMatrix();
    Sh.dirty();
  };
  Sh.dirty = function () { if (Sh.on) { R.renderer.shadowMap.needsUpdate = true; Sh.renders++; } };

  // per frame (IB.Look.update): follow the player; re-render while gates, doors or lifts move
  Sh.update = function () {
    if (!Sh.on) return;
    if (R.tier !== lastKey) { lastKey = R.tier; Sh.begin(IB.Game.level); return; }
    Sh.refit(false);
    var level = IB.Game.level, v = 0;
    level.zones.forEach(function (z, i) {
      if (z.exitGate) v += z.exitGate.open * (i + 1);
      if (z.entryGate) v += z.entryGate.open * (i + 7);
      (z.doors || []).forEach(function (d, j) { v += (d.broken ? 3 : 0) + (d.open || 0) * (j + 1) * 0.37; });
    });
    (level.elevators || []).forEach(function (L, j) { var g = L.group || L.mesh; v += (L.open || 0) * 0.11 * (j + 1) + (g ? g.position.y * 0.013 : 0); });
    if (sig >= 0 && Math.abs(v - sig) > 1e-4) Sh.dirty();
    sig = v;
  };
  Sh.end = function () {
    Sh.on = false; center = null; sig = -1;
    if (R) { R.renderer.shadowMap.enabled = false; R.sun.castShadow = false; }
  };
})(window.IB = window.IB || {});
