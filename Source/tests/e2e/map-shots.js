// INKBOLT map review screenshots: node tests/e2e/map-shots.js <plan> <shots.json> [outDir] [page]
// shots.json: [{ "name": "lines-1", "zone": 0, "x": 20, "z": 30, "eye": 1.55, "yaw": 0, "pitch": 0, "wait": 600 }]
//   x / z in zone-local cells; yaw 0 looks north, pi/2 looks west; eye = camera height (m) for high shots;
//   "debug": true logs frame times and the camera, "hide": 'all' | n hides a zone's moving-line meshes (all / the n-th)
// PROBE=<frames> logs frame times and draw stats where the level starts. The page loads with ?zcheck=1 and prints the
// cross-piece z-fighting list. No robots spawn, the view model is hidden; a shot goes to <outDir>/<plan>-<name>.png.
const { chromium } = require('playwright');
const path = require('path');
const http = require('http');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const [plan, shotsFile, outDir = path.join(__dirname, 'review'), page = 'Play Inkbolt.html'] = process.argv.slice(2);
const shots = JSON.parse(fs.readFileSync(shotsFile, 'utf8'));

(async () => {
  const server = await new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI(page);
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&zcheck=1&plan=' + plan);
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 60000 });
  // no robots in the review shots (their spawn effects crawl in software GL): nothing spawns, nobody is left on
  await pg.evaluate(() => {
    IB.AI.spawn = function () { return null; }; IB.AI.robots.forEach(r => { r.on = false; });
    const r0 = IB.Render.render; IB.Render.render = function () { return r0.call(this, false); };   // no view model
  });
  const info = await pg.evaluate(() => ({ zfight: IB.Game.level.zfight, zones: IB.Game.level.zones.map(z => [z.ox, z.oz, z.w, z.h, z.tris,
    (z.lineMeshes || []).map(M => M.mesh.count + 'x' + M.mesh.geometry.index.count / 3)]), tris: IB.Game.level.tris }));
  console.log('zfight', info.zfight.length, info.zfight.slice(0, 80).join(' | '));
  console.log('zones', JSON.stringify(info.zones), 'tris', info.tris);
  if (process.env.PROBE) {   // frame times and draw stats where the level starts
    const r = await pg.evaluate((process_n) => new Promise(done => {
      const t = []; let last = performance.now(), n = 0;
      function f() { const now = performance.now(); t.push(now - last); last = now; if (++n < +process_n) requestAnimationFrame(f); else done({ t: t.map(x => Math.round(x)), info: IB.Render.renderer.info.render, progs: IB.Render.renderer.info.programs.length, alive: IB.AI.alive(), lines: IB.Game.level.zones.map(z => (z.lines || []).length) }); }
      requestAnimationFrame(f);
    }), process.env.PROBE);
    console.log('probe', JSON.stringify(r));
  }
  let curZone = 0;
  for (const s of shots) {
    if ((s.zone || 0) !== curZone) {
      await pg.evaluate(i => __TEST__.teleport(i), s.zone || 0);
      await pg.waitForTimeout(800);
      curZone = s.zone || 0;
    }
    await pg.evaluate((s) => {
      const G = IB.Game, z = G.level.zones[s.zone || 0], p = G.player;
      // no robots in the shots: switch them off quietly (no blasts, no shake) and keep the waves from coming
      p.protect = 1e9; G.settings.shake = false; G.trauma = 0; G.shake = 0;
      IB.AI.robots.forEach(r => { r.on = false; });
      G.level.zones.forEach(z => { if (z.queue) z.queue.length = 0; z.wave = z.plan.waves.length - 1; });
      IB.Zones.setVisible(G.level, s.zone || 0);
      p.x = z.ox + s.x; p.z = z.oz + s.z; p.y = s.feet || 0; p.vx = p.vz = p.vy = 0;
      p.yaw = s.yaw || 0; p.pitch = s.pitch || 0;
      const eye = s.eye || 1.55;
      if (!IB.Player._eye0) IB.Player._eye0 = IB.Player.eyeY;
      IB.Player.eyeY = s.eye ? () => eye : IB.Player._eye0;
      if (G.ws) G.ws.hidden = true;
    }, s);
    await pg.waitForTimeout(s.wait || 700);
    await pg.evaluate((s) => { const p = IB.Game.player, z = IB.Game.level.zones[s.zone || 0]; p.x = z.ox + s.x; p.z = z.oz + s.z; p.yaw = s.yaw || 0; p.pitch = s.pitch || 0; }, s);
    await pg.waitForTimeout(150);
    if (s.hide) await pg.evaluate((h) => { IB.Game.level.zones.forEach(z => (z.lineMeshes || []).forEach((M, i) => { M.mesh.visible = !(h === 'all' || h === i); })); }, s.hide);
    if (s.debug) console.log('frames', JSON.stringify(await pg.evaluate(() => new Promise(done => {
      const t = []; let last = performance.now(), n = 0;
      setTimeout(() => done({ timeout: t }), 8000);
      function f() { const now = performance.now(); t.push(Math.round(now - last)); last = now; if (++n < 5) requestAnimationFrame(f); else done({ t, cam: IB.Render.camera.position.toArray(), rot: IB.Render.camera.rotation.x, mode: IB.Game.mode, dead: IB.Game.dead, pitch: IB.Game.player.pitch, rec: IB.Game.ws.recoilP, lk: IB.Game.player.landKick, tr: IB.Game.trauma, alive: IB.AI.alive() }); }
      requestAnimationFrame(f);
    }))));
    const file = path.join(outDir, plan + '-' + s.name + '.png');
    await pg.screenshot({ path: file, timeout: 240000 });
    const st = await pg.evaluate(() => __TEST__.state());
    console.log('shot', file, 'calls', st.calls, 'tris', st.triangles);
    if (s.debug) console.log(JSON.stringify(await pg.evaluate(() => { const c = IB.Render.camera; return { pos: c.position.toArray(), rot: [c.rotation.x, c.rotation.y, c.rotation.z], st: __TEST__.state() }; })));
  }
  if (logs.length) console.log('LOGS', logs.slice(0, 10).join(' | '));
  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
