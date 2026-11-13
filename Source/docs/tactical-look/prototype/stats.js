const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = '/home/user/inkbolt_';
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
(async () => {
  const server = await new Promise(res => { const s = http.createServer((req, r) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); }); }).listen(0, () => res(s)); });
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI('Play Inkbolt.html');
  const browser = await chromium.launch({ args: ARGS });
  for (const plan of process.argv.slice(2)) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    const pg = await ctx.newPage();
    try {
      await pg.goto(base + '?autotest=1&plan=' + plan);
      await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 180000 });
      await pg.evaluate(() => { IB.AI.spawn = function () { return null; }; IB.AI.robots.forEach(r => { r.on = false; }); IB.Game.guard.on = false; });
      await pg.waitForTimeout(2500);
      const r = await pg.evaluate(() => {
        const G = IB.Game, L = G.level, s = __TEST__.state(); let meshes = 0, mats = new Set();
        L.root.traverse(o => { if (o.isMesh || o.isInstancedMesh) { meshes++; mats.add(o.material.uuid); } });
        const gl = IB.Render.renderer.getContext();
        return { calls: s.calls, tris: s.triangles, levelTris: L.tris, zones: L.zones.map(z => [z.w, z.h, z.tris, z.meshes.length]), meshes, mats: mats.size, programs: IB.Render.renderer.info.programs.length,
          glows: L.glows.length, texMem: IB.Render.renderer.info.memory.textures, geoMem: IB.Render.renderer.info.memory.geometries, tier: s.tier, heapMB: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) : 0 };
      });
      console.log(plan, JSON.stringify(r));
    } catch (e) { console.log(plan, 'FAIL', e.message.slice(0, 120)); }
    await ctx.close();
  }
  await browser.close(); server.close();
})();
