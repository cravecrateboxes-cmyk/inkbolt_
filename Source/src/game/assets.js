/* INKBOLT assets: loads the Blender GLBs (embedded base64 in the single-file build, assets/*.glb otherwise),
   de-quantizes attributes into plain float buffers, converts the _HULL outline direction to Y-up (aHull),
   and builds one toon material per family on its palette texture. */
(function (IB) {
  'use strict';
  var A = IB.Assets = { gltf: {}, geo: {}, node: {}, mat: {}, skinMat: {}, family: {}, palette: {} };
  // baked outline shell thickness per family (m), mirrored from blender/build_assets.py CFG
  A.BAKED = { common: 0.02, weapons: 0.0035, bots: 0.015, 'kit-toytown': 0.02 };
  A.FILES = IB.ASSET_FILES;

  function b64ToBuffer(s) {
    var bin = atob(s), n = bin.length, u = new Uint8Array(n);
    for (var i = 0; i < n; i++) u[i] = bin.charCodeAt(i);
    return u.buffer;
  }
  function fetchBuffer(fam) {
    if (IB.GLB_DATA && IB.GLB_DATA[fam]) return Promise.resolve(b64ToBuffer(IB.GLB_DATA[fam]));
    return fetch((IB.ASSET_BASE || 'assets/') + A.FILES[fam]).then(function (r) {
      if (!r.ok) throw new Error('missing asset ' + A.FILES[fam]);
      return r.arrayBuffer();
    });
  }
  // plain Float32 copy of any (interleaved / normalized) attribute
  function toFloat(attr) {
    var n = attr.count, s = attr.itemSize, out = new Float32Array(n * s), arr = attr.isInterleavedBufferAttribute ? attr.data.array : attr.array, k = 1;
    if (attr.normalized) k = arr instanceof Int8Array ? 1 / 127 : arr instanceof Uint8Array ? 1 / 255 : arr instanceof Int16Array ? 1 / 32767 : arr instanceof Uint16Array ? 1 / 65535 : 1;
    for (var i = 0; i < n; i++) {
      out[i * s] = attr.getX(i) * k;
      if (s > 1) out[i * s + 1] = attr.getY(i) * k;
      if (s > 2) out[i * s + 2] = attr.getZ(i) * k;
      if (s > 3) out[i * s + 3] = attr.getW(i) * k;
    }
    if (attr.normalized && arr instanceof Int8Array) for (var j = 0; j < out.length; j++) out[j] = Math.max(-1, out[j]);
    return out;
  }
  var HULL_SCALE = 3.0;   // quantize_glb.py stores _HULL / 3
  function prepGeometry(g) {
    var out = new THREE.BufferGeometry();
    out.setIndex(g.index ? new THREE.BufferAttribute(g.index.array.slice ? g.index.array.slice() : g.index.array, 1) : null);
    out.setAttribute('position', new THREE.BufferAttribute(toFloat(g.attributes.position), 3));
    out.setAttribute('normal', new THREE.BufferAttribute(toFloat(g.attributes.normal), 3));
    out.setAttribute('uv', new THREE.BufferAttribute(toFloat(g.attributes.uv), 2));
    var c = toFloat(g.attributes.color), cc = new Float32Array(g.attributes.color.count * 3);
    for (var i = 0, n = g.attributes.color.count, s = g.attributes.color.itemSize; i < n; i++) { cc[i * 3] = c[i * s]; cc[i * 3 + 1] = c[i * s + 1]; cc[i * 3 + 2] = c[i * s + 2]; }
    out.setAttribute('color', new THREE.BufferAttribute(cc, 3));
    // _HULL is written in Blender axes (Z-up): convert to Y-up (x, z, -y)
    var h = toFloat(g.attributes._hull), hh = new Float32Array(h.length);
    for (var k = 0; k < h.length; k += 3) { hh[k] = h[k] * HULL_SCALE; hh[k + 1] = h[k + 2] * HULL_SCALE; hh[k + 2] = -h[k + 1] * HULL_SCALE; }
    out.setAttribute('aHull', new THREE.BufferAttribute(hh, 3));
    if (g.attributes.skinIndex) {
      out.setAttribute('skinIndex', new THREE.BufferAttribute(toFloat(g.attributes.skinIndex), 4));
      out.setAttribute('skinWeight', new THREE.BufferAttribute(toFloat(g.attributes.skinWeight), 4));
    }
    out.computeBoundingSphere(); out.computeBoundingBox();
    return out;
  }

  function loadFamily(fam) {
    return fetchBuffer(fam).then(function (buf) {
      return new Promise(function (res, rej) {
        new THREE.GLTFLoader().parse(buf, '', function (gltf) { res(gltf); }, function (e) { rej(e); });
      });
    }).then(function (gltf) {
      A.gltf[fam] = gltf;
      var pal = null;
      gltf.scene.updateMatrixWorld(true);
      gltf.scene.traverse(function (o) {
        if (o.name) { A.node[o.name] = o; A.family[o.name] = fam; }
        if (o.isMesh) {
          if (!pal && o.material && o.material.map) pal = o.material.map;
          o.geometry = prepGeometry(o.geometry);
          A.geo[o.name] = o.geometry;
        }
      });
      // palette: exact hex colours, nearest sampling
      pal.encoding = THREE.LinearEncoding; pal.magFilter = pal.minFilter = THREE.NearestFilter; pal.generateMipmaps = false; pal.needsUpdate = true;
      A.palette[fam] = pal;
      A.mat[fam] = IB.Render.toonMaterial({ map: pal, baked: A.BAKED[fam] });
      gltf.scene.traverse(function (o) { if (o.isMesh) o.material = A.mat[fam]; });
      return gltf;
    });
  }

  A.load = function (families, progress) {
    var done = 0;
    return Promise.all(families.map(function (f) {
      return loadFamily(f).then(function (g) { done++; if (progress) progress(done / families.length); return g; });
    }));
  };

  A.has = function (name) { return !!A.geo[name]; };
  A.get = function (name) {
    var g = A.geo[name];
    if (!g) throw new Error('INKBOLT asset missing: ' + name);
    return g;
  };
  // socket position (local to its parent part), as a new Vector3
  A.socket = function (name) {
    var n = A.node[name];
    if (!n) throw new Error('INKBOLT socket missing: ' + name);
    return n.position.clone();
  };
  A.material = function (name) { return A.mat[A.family[name]]; };

  /* Geometry copy transformed by a matrix (position, normal and the outline direction). */
  var _n3 = new THREE.Matrix3(), _v = new THREE.Vector3();
  A.placed = function (name, m) {
    var g = A.get(name).clone();
    g.applyMatrix4(m);   // position + normal
    _n3.setFromMatrix4(m);
    var h = g.attributes.aHull, a = h.array;
    for (var i = 0; i < a.length; i += 3) {
      if (a[i] === 0 && a[i + 1] === 0 && a[i + 2] === 0) continue;
      _v.set(a[i], a[i + 1], a[i + 2]).applyMatrix3(_n3);
      a[i] = _v.x; a[i + 1] = _v.y; a[i + 2] = _v.z;
    }
    return g;
  };
  A.merge = function (list) {
    if (!list.length) return null;
    var g = THREE.BufferGeometryUtils.mergeBufferGeometries(list, false);
    list.forEach(function (x) { x.dispose(); });
    return g;
  };
})(window.IB = window.IB || {});
