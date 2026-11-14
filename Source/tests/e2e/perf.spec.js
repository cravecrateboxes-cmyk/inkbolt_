// INKBOLT performance check. Run: node tests/e2e/perf.spec.js [path-to-html]
// Records draw calls, triangles and frame times (p50/p95) with scripted combat, plus a 40-robot stress case and a
// VFX stress case (mass robot wrecks, Bomber blasts and fireworks at once at full escalation).
// Note: headless Chromium renders with SwiftShader (CPU), so frame times here are far slower than real GPUs;
// draw calls and triangles are exact. Budget: 140 draw calls on phone settings, 230 on desktop (tactical look, plan
// section 6: the old 120 / 200 plus the post passes and the dressing meshes per zone).
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const TARGET = process.argv[2] || 'Play Inkbolt.html';
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-precise-memory-info'];
const VIEWS = [{ name: 'phone-upright', w: 390, h: 844, touch: true, budget: 140 }, { name: 'phone-sideways', w: 844, h: 390, touch: true, budget: 140 }, { name: 'desktop', w: 1920, h: 1080, touch: false, budget: 230 }];
let failures = 0;
function serve() { return new Promise(res => { const s = http.createServer((req, r) => { fs.readFile(path.join(ROOT, decodeURIComponent(req.url.split('?')[0])), (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': 'text/html' }); r.end(d); }); }).listen(0, () => res(s)); }); }
const pct = (a, p) => { const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(s.length * p))]; };

(async () => {
  const server = await serve();
  const url = 'http://localhost:' + server.address().port + '/' + encodeURI(TARGET) + '?autotest=1';
  const browser = await chromium.launch({ args: ARGS });
  const rows = [];
  for (const v of VIEWS) {
    const ctx = await browser.newContext({ viewport: { width: v.w, height: v.h }, hasTouch: v.touch, isMobile: v.touch, deviceScaleFactor: 1 });
    const pg = await ctx.newPage();
    await pg.goto(url);
    await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().alive >= 3, null, { timeout: +(process.env.LOAD_MS || 90000) });
    await pg.evaluate(() => { IB.Game.guard.on = false; IB.Game.player.protect = 999; });
    // scripted combat: fire Buzz at the nearest robot for 8 s while sampling frames
    const s = await pg.evaluate(() => new Promise(done => {
      const G = IB.Game, times = [], calls = [], tris = []; let last = performance.now(), t0 = last;
      IB.Weapons.slot(G.ws, 2);
      function tick(now) {
        times.push(now - last); last = now;
        const info = IB.Render.renderer.info.render; calls.push(info.calls); tris.push(info.triangles);
        const p = G.player; let best = null, bd = 1e9;
        IB.AI.robots.forEach(r => { if (r.on && r.state !== 'spawn') { const d = Math.hypot(r.x - p.x, r.z - p.z); if (d < bd) { bd = d; best = r; } } });
        if (best) { p.yaw = Math.atan2(-(best.x - p.x), -(best.z - p.z)); p.pitch = Math.atan2(best.y + 0.5 - 1.55, bd); }
        IB.Input.fire = true;
        if (now - t0 < 8000) requestAnimationFrame(tick); else { IB.Input.fire = false; done({ times, calls, tris, heap: performance.memory ? performance.memory.usedJSHeapSize : 0 }); }
      }
      requestAnimationFrame(tick);
    }));
    // stress: 40 robots in view
    const stress = await pg.evaluate(() => new Promise(done => {
      const G = IB.Game, z = G.level.zones[0], p = G.player;
      for (let i = 0; i < 40; i++) IB.AI.spawn('crawler', z.entry.x - 8 + (i % 10) * 1.8, z.entry.z - 8 - Math.floor(i / 10) * 2, 0, z.entry.x, z.entry.z, { pose: true });
      p.yaw = 0; p.pitch = -0.1;
      let n = 0, mx = 0, tr = 0;
      function tick() { const info = IB.Render.renderer.info.render; mx = Math.max(mx, info.calls); tr = Math.max(tr, info.triangles); if (++n < 30) requestAnimationFrame(tick); else done({ calls: mx, tris: tr, robots: IB.AI.robots.filter(r => r.on).length }); }
      requestAnimationFrame(tick);
    }));
    // VFX stress: 16 robot wrecks (all types), 4 Bomber blasts and the level-clear fireworks in view at once,
    // at full campaign intensity; worst draw calls over 40 frames and the JS heap swing while it plays out
    const vfx = await pg.evaluate(() => new Promise(done => {
      const G = IB.Game, z = G.level.zones[0], p = G.player, Bm = IB.Boom;
      p.x = z.entry.x; p.z = z.entry.z; p.yaw = 0; p.pitch = -0.05;
      if (Bm) { Bm.I = 2.2; Bm.lvl = 9; }
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      const types = ['crawler', 'gunner', 'bomber', 'drone'];
      for (let i = 0; i < 16; i++) IB.AI.spawn(types[i % 4], z.entry.x - 6 + (i % 8) * 1.7, z.entry.z - 8 - Math.floor(i / 8) * 2.5, 0, z.entry.x, z.entry.z, { pose: true });
      let n = 0, calls = 0, h0 = 1e12, h1 = 0;
      function tick() {
        if (n === 2) { IB.AI.robots.forEach(r => { if (r.on) IB.AI.kill(r, G.onKill); }); for (let k = 0; k < 4; k++) IB.Projectiles.explode(z.entry.x - 4 + k * 2.6, 0.5, z.entry.z - 11, 3, 0, 0, { type: 'bomber' }); if (Bm) Bm.zoneClear(G.level, 0, true); }
        calls = Math.max(calls, IB.Render.renderer.info.render.calls);
        if (performance.memory) { const m = performance.memory.usedJSHeapSize; h0 = Math.min(h0, m); h1 = Math.max(h1, m); }
        if (++n < 40) requestAnimationFrame(tick); else done({ calls, heapSwingMB: performance.memory ? +((h1 - h0) / 1048576).toFixed(1) : 0, s: Bm ? Bm.stats() : { cards: 0, puffs: 0 } });
      }
      requestAnimationFrame(tick);
    }));
    const row = { view: v.name, callsMax: Math.max(...s.calls), callsP50: pct(s.calls, 0.5), trisMax: Math.max(...s.tris), p50: +pct(s.times, 0.5).toFixed(1), p95: +pct(s.times, 0.95).toFixed(1),
      heapMB: +(s.heap / 1048576).toFixed(1), stressCalls: stress.calls, stressTris: stress.tris, stressRobots: stress.robots,
      vfxCalls: vfx.calls, vfxHeapSwingMB: vfx.heapSwingMB, vfxCards: vfx.s.cards, vfxPuffs: vfx.s.puffs };
    rows.push(row);
    const ok = row.callsMax <= v.budget && row.stressCalls <= v.budget && row.vfxCalls <= v.budget;
    console.log((ok ? 'PASS ' : 'FAIL ') + v.name + ' draw calls within ' + v.budget + '  ' + JSON.stringify(row));
    if (!ok) failures++;
    await ctx.close();
  }
  await browser.close(); server.close();
  fs.writeFileSync(path.join(__dirname, 'perf.json'), JSON.stringify(rows, null, 1));
  console.log(failures ? failures + ' FAILED' : 'ALL PASSED');
  process.exit(failures ? 1 : 0);
})();
