const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = '/home/user/inkbolt_';
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const PAL = JSON.parse(fs.readFileSync(path.join(__dirname, 'palettes.json'), 'utf8')).palettes;
(async () => {
  const server = await new Promise(res => { const s = http.createServer((req, r) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); }); }).listen(0, () => res(s)); });
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI('Play Inkbolt.html');
  const browser = await chromium.launch({ args: ARGS });
  for (const plan of process.argv.slice(2)) {
    const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
    const pg = await ctx.newPage();
    try {
      await pg.goto(base + '?autotest=1&plan=' + plan);
      await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 180000 });
      await pg.evaluate(() => { IB.AI.spawn = function () { return null; }; IB.AI.robots.forEach(r => { r.on = false; }); IB.Game.guard.on = false; });
      await pg.addScriptTag({ path: path.join(__dirname, 'proto.js') });
      const r = await pg.evaluate((pal) => {
        IBLook.pal = pal; IBLook.cfg = { gridI: 1 };
        // uniforms are created by apply(); only the bake is timed here, so stub the uniform sink
        const out = [];
        const U = { uGrid: { value: null }, uGridR: { value: new THREE.Vector4() }, uGridI: { value: 0 } };
        IBLook.apply({ post: false, grid: false }, pal);
        IB.Game.level.zones.forEach((z, i) => { const t0 = performance.now(); const g = IBLook.buildGrid(i, { gridI: 1 }); out.push({ zone: i, ms: Math.round(performance.now() - t0), lights: g.lights, w: g.w, h: g.h }); });
        return out;
      }, PAL);
      console.log(plan, JSON.stringify(r));
    } catch (e) { console.log(plan, 'FAIL', e.message.slice(0, 200)); }
    await ctx.close();
  }
  await browser.close(); server.close();
})();
