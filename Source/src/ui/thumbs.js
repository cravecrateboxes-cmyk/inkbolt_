/* INKBOLT item pictures for the field kit: the real gun and gear meshes (IB.Assets, toon material + ink shell)
   rendered side on into transparent PNG data URLs with a thick comic ink contour, cropped to the drawing. Cached.
     IB.Thumbs.pic(kind, id, cls, fallback)  '<span class="cls" data-thumb="kind:id">' holding the picture when it is
                                             cached, else the fallback markup; the picture is then drawn in the
                                             background, one at a time, and swapped into every span still waiting
     IB.Thumbs.url(kind, id)                 the cached data URL, or null (not drawn yet / no model)
   kind 'gun': WPN_<ID> + its magazine, muzzle to the right ('<id>@<tier>': in that tier's rarity skin). kind 'gear': shield (GEAR_ShieldCell; 'shield.epic' etc.
   draws that rarity's own cell, IB.Loot.modelOf), grip, scope, acid / muzzle (GEAR_Acid), mag (GEAR_Mag),
   armor (GEAR_Vest).
   Drawn with the game's own renderer (no second GL context, the toon program the viewmodel already uses) into a small
   RGBA render target at 2x, read back asynchronously (WebGL2: pixel-pack buffer + fence, polled; the main thread
   never waits on the GPU), then scaled down on a 2D canvas. WebGL1 falls back to a synchronous read. */
(function (IB) {
  'use strict';
  var T = IB.Thumbs = { cache: {}, W: 420, H: 210 };
  var GEAR_NODE = { shield: 'GEAR_ShieldCell', grip: 'GEAR_Grip', scope: 'GEAR_Scope', acid: 'GEAR_Acid', shock: 'GEAR_Shock', blast: 'GEAR_Blast', void: 'GEAR_Void', muzzle: 'GEAR_Acid', mag: 'GEAR_Mag', armor: 'GEAR_Vest' };
  var VIEW = {
    shield: { yaw: -0.6, pitch: 0, tilt: -0.5, pad: 1.18, outline: 0.02, ink: 3 },
    armor: { yaw: -0.55, pitch: 0.22, pad: 1.18, outline: 0.02, ink: 3 },
    mag: { yaw: -0.75, pitch: 0.3, pad: 1.18, outline: 0.02, ink: 3 },
    def: { yaw: -0.5, pitch: 0.3, pad: 1.15, outline: 0.016, ink: 3 }
  };
  var SS = 2;   // supersampling: the render target is 2x the picture
  var scene = null, cam = null, uni = null, rt = null, mats = {}, queue = [], timer = 0, busy = false;
  var _v2 = null, _col = null;

  function setup() {
    if (scene) return true;
    if (!window.THREE || !IB.Render || !IB.Render.renderer || !IB.Render.toonMaterial) return false;
    scene = new THREE.Scene();
    cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 20);
    // one key light, like the viewmodel scene, so the toon program the guns already use is reused (no compile)
    var key = new THREE.DirectionalLight(0xffffff, 1.0); key.position.set(0.6, 0.9, 0.5); scene.add(key);
    // own outline uniforms: a fixed shell thickness in model metres (ortho camera: no distance term)
    uni = { uInk: { value: new THREE.Color(0x15121C) }, uOutBase: { value: 0.006 }, uOutK: { value: 0 }, px: 0 };
    rt = new THREE.WebGLRenderTarget(T.W * SS, T.H * SS, { format: THREE.RGBAFormat, depthBuffer: true, stencilBuffer: false });
    _v2 = new THREE.Vector2(); _col = new THREE.Color();
    return true;
  }
  function material(fam) {
    if (mats[fam]) return mats[fam];
    var A = IB.Assets;
    if (!A.palette[fam]) return null;
    mats[fam] = IB.Render.toonMaterial({ uni: uni, map: A.palette[fam], baked: (A.BAKED && A.BAKED[fam]) || 0 });
    return mats[fam];
  }
  // every 2D canvas here is CPU-side (willReadFrequently): no GPU-process round trip when the pixels are read back
  function canvas2d(w, h) { var c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
  function ctx(c) { return c.getContext('2d', { willReadFrequently: true }); }

  function webgl2(gl) { return typeof WebGL2RenderingContext !== 'undefined' && gl instanceof WebGL2RenderingContext; }
  /* render parts into the render target and copy the pixels out: on WebGL2 into a pixel-pack buffer (GPU side, read
     later), else synchronously. Returns {pbo} or {px}, or null. */
  function shoot(parts, fam, view, skin) {
    var mat = skin || material(fam), r = IB.Render.renderer, gl = r.getContext();
    if (!mat) return null;
    var root = new THREE.Group(), box = new THREE.Box3();
    parts.forEach(function (p) {
      var m = new THREE.Mesh(p.geo, mat);
      if (p.pos) m.position.copy(p.pos);
      m.frustumCulled = false; root.add(m);
    });
    root.rotation.set(view.pitch || 0, view.yaw || 0, 0, 'YXZ');
    // tilt: lean the top toward the camera (a world-space turn about the screen-horizontal axis, after yaw / pitch)
    var top = new THREE.Group(); top.rotation.z = view.tilt || 0; top.add(root);
    scene.add(top); top.updateMatrixWorld(true);
    box.setFromObject(root);
    var c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3());
    // camera on +X looking down -X: screen right is -Z (the muzzle), up is +Y
    var aspect = T.W / T.H, pad = view.pad || 1.1;
    var hw = Math.max(s.z / 2, s.y / 2 * aspect) * pad, hh = hw / aspect;
    cam.left = -hw; cam.right = hw; cam.top = hh; cam.bottom = -hh;
    cam.position.set(c.x + 5, c.y, c.z); cam.lookAt(c); cam.updateProjectionMatrix();
    uni.uOutBase.value = (view.outline || 0.012) * Math.max(s.y, s.z);
    var w = rt.width, h = rt.height, n = w * h * 4, job = { w: w, h: h };
    var prevRT = r.getRenderTarget(), prevAuto = r.autoClear, prevAlpha = r.getClearAlpha();
    r.getClearColor(_col);
    try {
      r.setRenderTarget(rt); r.autoClear = false; r.setClearColor(0x000000, 0); r.clear(true, true, true);
      r.render(scene, cam);
      if (webgl2(gl)) {
        job.pbo = gl.createBuffer();
        gl.bindBuffer(gl.PIXEL_PACK_BUFFER, job.pbo); gl.bufferData(gl.PIXEL_PACK_BUFFER, n, gl.STREAM_READ);
        gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, 0);
        gl.bindBuffer(gl.PIXEL_PACK_BUFFER, null);
      } else {
        job.px = new Uint8Array(n); r.readRenderTargetPixels(rt, 0, 0, w, h, job.px);
      }
    } finally {
      r.setRenderTarget(prevRT); r.setClearColor(_col, prevAlpha); r.autoClear = prevAuto;
      scene.remove(top);
    }
    return job;
  }
  function pixels(job) {
    if (job.px || !job.pbo) return job.px || null;
    var gl = IB.Render.renderer.getContext(), out = new Uint8Array(job.w * job.h * 4);
    gl.bindBuffer(gl.PIXEL_PACK_BUFFER, job.pbo); gl.getBufferSubData(gl.PIXEL_PACK_BUFFER, 0, out); gl.bindBuffer(gl.PIXEL_PACK_BUFFER, null);
    gl.deleteBuffer(job.pbo); job.pbo = null;
    return out;
  }

  // GL pixels (bottom-up, 2x) -> picture with a solid ink contour round the silhouette, cropped to the drawing
  function toUrl(px, w, h, inkPx) {
    var W = T.W, H = T.H;
    var big = canvas2d(w, h), bx = ctx(big), img = bx.createImageData(w, h), row = w * 4;
    for (var y = 0; y < h; y++) img.data.set(px.subarray((h - 1 - y) * row, (h - y) * row), y * row);
    bx.putImageData(img, 0, 0);
    var small = canvas2d(W, H), sx = ctx(small); sx.imageSmoothingQuality = 'high'; sx.drawImage(big, 0, 0, W, H);
    var out = canvas2d(W, H), ox = ctx(out);
    if (inkPx > 0) {
      var ink = canvas2d(W, H), ix = ctx(ink);
      ix.drawImage(small, 0, 0); ix.globalCompositeOperation = 'source-in'; ix.fillStyle = '#15121C'; ix.fillRect(0, 0, W, H);
      for (var a = 0; a < 16; a++) { var t = a / 16 * Math.PI * 2; ox.drawImage(ink, Math.cos(t) * inkPx, Math.sin(t) * inkPx); }
      ox.drawImage(ink, 0, inkPx + 1);   // heavier ink under the bottom edge
    }
    ox.drawImage(small, 0, 0);
    var d = ox.getImageData(0, 0, W, H).data, x0 = W, y0 = H, x1 = -1, y1 = -1;
    for (var yy = 0; yy < H; yy++) for (var xx = 0; xx < W; xx++) if (d[(yy * W + xx) * 4 + 3] > 8) { if (xx < x0) x0 = xx; if (xx > x1) x1 = xx; if (yy < y0) y0 = yy; if (yy > y1) y1 = yy; }
    if (x1 < 0) return null;
    var m = 3; x0 = Math.max(0, x0 - m); y0 = Math.max(0, y0 - m); x1 = Math.min(W - 1, x1 + m); y1 = Math.min(H - 1, y1 + m);
    var crop = canvas2d(x1 - x0 + 1, y1 - y0 + 1);
    ctx(crop).drawImage(out, x0, y0, crop.width, crop.height, 0, 0, crop.width, crop.height);
    return crop.toDataURL('image/png');
  }

  function parts(kind, id) {
    var A = IB.Assets;
    if (!A || !A.geo) return null;
    if (kind === 'gun') {
      // 'rivet@purple': that tier's rarity skin (src/game/gunskins.js); a bare id draws the Standard skin
      var at = String(id).indexOf('@'), gid = at > 0 ? id.slice(0, at) : String(id), tier = at > 0 ? id.slice(at + 1) : 'gray';
      var key = 'WPN_' + gid.toUpperCase();
      if (!A.geo[key]) return null;
      var list = [{ geo: A.geo[key] }], sock = A.node[key + '_MAG'];
      if (A.geo[key + '_Mag'] && sock) list.push({ geo: A.geo[key + '_Mag'], pos: sock.position });
      var skin = IB.GunSkins && setup() && IB.WEAPONS[gid] && IB.WEAPONS[gid].cls !== 'melee' ? IB.GunSkins.material(gid, tier, uni) : null;
      return { fam: 'weapons', skin: skin, list: list, view: { yaw: -0.22, pitch: 0.1, pad: 1.06, outline: 0.012, ink: 3 } };
    }
    // id: a type ('shield', 'mag'...), a slot ('muzzle'), or 'type.rarity' for a type with a model per rarity
    var dot = String(id).indexOf('.'), type = dot > 0 ? id.slice(0, dot) : id, n = GEAR_NODE[type];
    if (dot > 0 && IB.Loot && IB.Loot.modelOf) { var mn = IB.Loot.modelOf({ type: type, rarity: id.slice(dot + 1) }); if (mn && A.geo[mn]) n = mn; }
    if (!n || !A.geo[n]) return null;
    var gl = [{ geo: A.geo[n] }];
    if (A.geo[n + '_Glow']) gl.push({ geo: A.geo[n + '_Glow'] });   // muzzle cans: the glass core
    return { fam: 'gear', list: gl, view: VIEW[type] || VIEW.def };
  }
  function img(url) { return '<img class="pic" src="' + url + '" alt="" draggable="false">'; }
  function waiting(k) { return document.querySelector('[data-thumb="' + k + '"]'); }
  /* one batch: every waiting picture is rendered and copied GPU-side in one go, one fence for all of them (so the
     batch costs one GPU round trip, not one per picture), then each is finished on its own tick */
  function pump() {
    timer = 0;
    if (busy) return;
    var keys = [];
    while (queue.length) { var k = queue.shift(); if (!(k in T.cache) && waiting(k) && keys.indexOf(k) < 0) keys.push(k); }
    if (!keys.length || !setup()) return;
    var jobs = [];
    keys.forEach(function (k) {
      var i = k.indexOf(':'), p = parts(k.slice(0, i), k.slice(i + 1)), job = null;
      if (p) { try { job = shoot(p.list, p.fam, p.view, p.skin); } catch (e) { job = null; } }
      if (job) { job.k = k; job.ink = p.view.ink; jobs.push(job); } else T.cache[k] = null;
    });
    if (!jobs.length) { next(); return; }
    busy = true;
    var gl = IB.Render.renderer.getContext(), sync = webgl2(gl) ? gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0) : null;
    if (sync) gl.flush();
    function finishOne() {
      var job = jobs.shift();
      if (!job) { busy = false; next(); return; }
      var url = null;
      try { var px = pixels(job); url = px ? toUrl(px, job.w, job.h, job.ink) : null; } catch (e) { url = null; }
      T.cache[job.k] = url;
      if (url) document.querySelectorAll('[data-thumb="' + job.k + '"]').forEach(function (el) { el.innerHTML = img(url); });
      setTimeout(finishOne, 0);
    }
    (function poll() {
      if (sync) {
        var st = gl.clientWaitSync(sync, 0, 0);
        if (st === gl.TIMEOUT_EXPIRED) { setTimeout(poll, 20); return; }
        gl.deleteSync(sync);
      }
      finishOne();
    })();
  }
  function next() { if (queue.length && !timer) timer = setTimeout(pump, 30); }

  T.key = function (kind, id) { return (kind === 'gun' ? 'gun:' : 'gear:') + id; };
  T.url = function (kind, id) { return T.cache[T.key(kind, id)] || null; };
  T.pic = function (kind, id, cls, fallback) {
    var k = T.key(kind, id), u = T.cache[k];
    if (u === undefined && parts(kind, id)) {
      if (queue.indexOf(k) < 0) queue.push(k);
      if (!timer && !busy) timer = setTimeout(pump, 300);   // let the menu paint and answer input first
    }
    return '<span class="' + (cls || 'gpic') + '" data-thumb="' + k + '">' + (u ? img(u) : (fallback || '')) + '</span>';
  };
})(window.IB = window.IB || {});
