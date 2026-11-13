// Baseline look shots: node base-shots.js <outDir> plan1 plan2 ...   (view model + HUD kept, no robots)
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = '/home/user/inkbolt_';
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const [outDir, ...plans] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
(async () => {
  const server = await new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI('Play Inkbolt.html');
  const browser = await chromium.launch({ args: ARGS });
  for (const plan of plans) {
    const t0 = Date.now();
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    const pg = await ctx.newPage();
    const logs = [];
    pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
    try {
      await pg.goto(base + '?autotest=1&plan=' + plan);
      await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 120000 });
      await pg.evaluate(() => { IB.AI.spawn = function () { return null; }; IB.AI.robots.forEach(r => { r.on = false; }); });
      const nz = await pg.evaluate(() => IB.Game.level.zones.length);
      for (let zi = 0; zi < Math.min(nz, 2); zi++) {
        await pg.evaluate(i => __TEST__.teleport(i), zi);
        await pg.waitForTimeout(600);
        const spots = await pg.evaluate((zi) => {
          const G = IB.Game, z = G.level.zones[zi], Z = IB.Zones, out = [];
          function open(x, zz) { return Z.isOpen(z, x, zz); }
          function near(tx, tz) { for (let r = 0; r < 14; r++) for (let a = 0; a < 16; a++) { const x = tx + Math.cos(a / 16 * 6.283) * r, zz = tz + Math.sin(a / 16 * 6.283) * r; if (open(x, zz) && open(x + 0.6, zz) && open(x - 0.6, zz) && open(x, zz + 0.6) && open(x, zz - 0.6)) return [x, zz]; } return [tx, tz]; }
          const e = z.entry;
          out.push({ n: 'entry', x: e.x, z: e.z - 1.5, yaw: 0 });
          const m = near(z.ox + z.w / 2, z.oz + z.h / 2); out.push({ n: 'mid', x: m[0], z: m[1], yaw: 0.7 }); out.push({ n: 'midback', x: m[0], z: m[1], yaw: 3.6 });
          const q = near(z.ox + z.w * 0.25, z.oz + z.h * 0.3); out.push({ n: 'q', x: q[0], z: q[1], yaw: -1.2 });
          return out;
        }, zi);
        for (const s of spots) {
          await pg.evaluate((a) => {
            const G = IB.Game, p = G.player; p.protect = 1e9; G.settings.shake = false; G.trauma = 0;
            IB.AI.robots.forEach(r => { r.on = false; });
            G.level.zones.forEach(z => { if (z.queue) z.queue.length = 0; z.wave = z.plan.waves.length - 1; });
            IB.Zones.setVisible(G.level, a.zi);
            p.x = a.s.x; p.z = a.s.z; p.y = IB.Zones.floorY(a.s.x, a.s.z, 1.2) || 0; p.vx = p.vz = p.vy = 0; p.yaw = a.s.yaw; p.pitch = -0.04;
          }, { s, zi });
          await pg.waitForTimeout(900);
          await pg.evaluate((a) => { const p = IB.Game.player; p.x = a.x; p.z = a.z; p.yaw = a.yaw; p.pitch = -0.04; }, s);
          await pg.waitForTimeout(250);
          await pg.screenshot({ path: path.join(outDir, plan + '-z' + zi + '-' + s.n + '.png'), timeout: 240000 });
        }
      }
      console.log(plan, 'ok', Math.round((Date.now() - t0) / 1000) + 's', logs.slice(0, 3).join(' | '));
    } catch (e) { console.log(plan, 'FAIL', e.message.slice(0, 200), logs.slice(0, 3).join(' | ')); }
    await ctx.close();
  }
  await browser.close(); server.close();
})();
