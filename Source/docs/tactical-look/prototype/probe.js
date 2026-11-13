const { chromium } = require('playwright');
const fs = require('fs');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
(async () => {
  const browser = await chromium.launch({ args: ARGS });
  const pg = await browser.newPage();
  const logs = [];
  pg.on('console', m => logs.push(m.type() + ': ' + m.text().slice(0, 300)));
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.setContent('<canvas id="c" width="256" height="256"></canvas>');
  await pg.addScriptTag({ path: '/home/user/inkbolt_/Source/vendor/three.min.js' });
  const out = await pg.evaluate(() => {
    const res = {};
    const r = new THREE.WebGLRenderer({ canvas: document.getElementById('c'), antialias: true });
    const gl = r.getContext();
    res.webgl2 = r.capabilities.isWebGL2;
    res.maxTex = r.capabilities.maxTextures; res.maxSamples = r.capabilities.maxSamples; res.maxTexSize = r.capabilities.maxTextureSize;
    res.ext = ['EXT_color_buffer_float', 'EXT_color_buffer_half_float', 'OES_texture_float_linear', 'OES_texture_half_float_linear', 'EXT_texture_filter_anisotropic'].map(e => e + ':' + !!gl.getExtension(e));
    const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2));
    const sc = new THREE.Scene(); sc.add(quad);
    const V = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4( position.xy, 0.0, 1.0 ); }';
    function read(rt) { const b = new Float32Array(4); try { r.readRenderTargetPixels(rt, 0, 0, 1, 1, b); } catch (e) { return 'ERR ' + e.message; } return Array.from(b).map(x => +x.toFixed(3)); }
    const frt = new THREE.WebGLRenderTarget(1, 1, { type: THREE.FloatType, format: THREE.RGBAFormat });
    // 1. sampler2DArray via DataTexture2DArray with mipmaps + linear filtering, layer picked per fragment
    try {
      const W = 4, D = 3, data = new Uint8Array(W * W * D * 4);
      for (let l = 0; l < D; l++) for (let i = 0; i < W * W; i++) { const o = (l * W * W + i) * 4; data[o] = l === 0 ? 255 : 0; data[o + 1] = l === 1 ? 255 : 0; data[o + 2] = l === 2 ? 255 : 0; data[o + 3] = 255; }
      const t = new THREE.DataTexture2DArray(data, W, W, D);
      t.format = THREE.RGBAFormat; t.type = THREE.UnsignedByteType; t.minFilter = THREE.LinearMipmapLinearFilter; t.magFilter = THREE.LinearFilter; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.generateMipmaps = true; t.needsUpdate = true;
      quad.material = new THREE.ShaderMaterial({ vertexShader: V, fragmentShader: 'precision highp sampler2DArray; uniform sampler2DArray tA; uniform float layer; varying vec2 vUv; void main(){ gl_FragColor = texture( tA, vec3( vUv * 3.0, layer ) ); }', uniforms: { tA: { value: t }, layer: { value: 1 } } });
      r.setRenderTarget(frt); r.render(sc, cam); res.array_layer1 = read(frt);
      quad.material.uniforms.layer.value = 2; r.render(sc, cam); res.array_layer2 = read(frt);
      // inside a patched MeshToonMaterial
      const g = new Uint8Array([255, 255, 255, 255]); const grad = new THREE.DataTexture(g, 1, 1, THREE.RGBAFormat); grad.needsUpdate = true;
      const tm = new THREE.MeshToonMaterial({ color: 0xffffff, gradientMap: grad });
      tm.onBeforeCompile = sh => { sh.uniforms.tA = { value: t }; sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nprecision highp sampler2DArray;\nuniform sampler2DArray tA;').replace('#include <dithering_fragment>', 'gl_FragColor = texture( tA, vec3( 0.5, 0.5, 0.0 ) );'); };
      const s2 = new THREE.Scene(); const m2 = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), tm); s2.add(m2); s2.add(new THREE.DirectionalLight(0xffffff, 1));
      const c2 = new THREE.OrthographicCamera(-1, 1, 1, -1, -1, 1);
      r.setRenderTarget(frt); r.render(s2, c2); res.array_in_toon = read(frt);
    } catch (e) { res.array_err = e.message; }
    // 2. multisampled half-float target with a depth texture, depth read back in a second pass
    try {
      const dt = new THREE.DepthTexture(64, 64); dt.type = THREE.UnsignedIntType; dt.format = THREE.DepthFormat;
      const ms = new THREE.WebGLMultisampleRenderTarget(64, 64, { type: THREE.HalfFloatType, format: THREE.RGBAFormat, depthBuffer: true, depthTexture: dt });
      ms.samples = 4;
      const s3 = new THREE.Scene(), c3 = new THREE.PerspectiveCamera(60, 1, 0.1, 100);
      const box = new THREE.Mesh(new THREE.BoxGeometry(50, 50, 1), new THREE.MeshBasicMaterial({ color: 0xff8000 })); box.position.z = -10; s3.add(box);
      r.setRenderTarget(ms); r.clear(); r.render(s3, c3);
      quad.material = new THREE.ShaderMaterial({ vertexShader: V, fragmentShader: 'uniform sampler2D tD; uniform sampler2D tC; varying vec2 vUv; void main(){ gl_FragColor = vec4( texture2D( tD, vec2( 0.5 ) ).r, texture2D( tC, vec2( 0.5 ) ).rgb ); }', uniforms: { tD: { value: dt }, tC: { value: ms.texture } } });
      r.setRenderTarget(frt); r.render(sc, cam); res.ms_depth_color = read(frt);
      res.glerr_ms = gl.getError();
      // expected depth for z=-9.5 with near .1 far 100: ndc -> (f/(f-n))*(1 - n/z)
      const n = 0.1, f = 100, z = 9.5; res.expect_depth = +(((f / (f - n)) * (1 - n / z))).toFixed(3);
    } catch (e) { res.ms_err = e.message; }
    // 3. same without multisampling
    try {
      const dt2 = new THREE.DepthTexture(64, 64); dt2.type = THREE.UnsignedIntType;
      const rt = new THREE.WebGLRenderTarget(64, 64, { type: THREE.HalfFloatType, format: THREE.RGBAFormat, depthBuffer: true, depthTexture: dt2 });
      const s3 = new THREE.Scene(), c3 = new THREE.PerspectiveCamera(60, 1, 0.1, 100);
      const box = new THREE.Mesh(new THREE.BoxGeometry(50, 50, 1), new THREE.MeshBasicMaterial({ color: 0xff8000 })); box.position.z = -10; s3.add(box);
      r.setRenderTarget(rt); r.clear(); r.render(s3, c3);
      quad.material = new THREE.ShaderMaterial({ vertexShader: V, fragmentShader: 'uniform sampler2D tD; uniform sampler2D tC; varying vec2 vUv; void main(){ gl_FragColor = vec4( texture2D( tD, vec2( 0.5 ) ).r, texture2D( tC, vec2( 0.5 ) ).rgb ); }', uniforms: { tD: { value: dt2 }, tC: { value: rt.texture } } });
      r.setRenderTarget(frt); r.render(sc, cam); res.plain_depth_color = read(frt);
    } catch (e) { res.plain_err = e.message; }
    res.glerr = gl.getError();
    return res;
  });
  console.log(JSON.stringify(out, null, 1));
  console.log(logs.filter(l => /error|warn/i.test(l)).slice(0, 10).join('\n'));
  await browser.close();
})();
