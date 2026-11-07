// INKBOLT Lagoon Island review shots: opens the island level, stages the camera at fixed spots in each zone (zone-local
// cell coordinates) and saves tests/e2e/review/island-*.png; prints the cross-piece z-fighting check and per-shot
// draw calls / triangles. Run after tools/build.py: node tests/e2e/island-shots.js [names...]
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const OUT = path.join(__dirname, 'review');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const D = Math.PI / 180;
// [name, zone, c, r, yaw (0 = north, + = turn left / west), pitch, eye height]
const SHOTS = [
  ['beach-start', 0, 31, 52, 0, -4, 1.55],
  ['beach-seawall', 0, 58, 26, -90 * 1 + 0, -3, 1.55],
  ['beach-shore', 0, 54, 44, -60, -6, 1.55],
  ['beach-huts', 0, 30, 18, 60, -6, 1.55],
  ['beach-west', 0, 12, 36, 120, -4, 1.55],
  ['beach-high', 0, 31, 50, 0, -22, 14],
  ['beach-gate', 0, 31, 8, 0, 0, 1.55],
  ['trail', 0, 31.5, -6, 0, -4, 1.55],
  ['lagoon-view', 1, 31, 40, 0, -6, 1.55],
  ['lagoon-sea', 1, 6, 30, 90, -3, 1.55],
  ['lagoon-lookout', 1, 44, 46, -30, -2, 1.55],
  ['lagoon-high', 1, 31, 50, 0, -24, 16],
  ['point-outpost', 2, 31, 34, 40, -6, 1.55],
  ['point-lighthouse', 2, 44, 18, -40, 6, 1.55],
  ['point-sea', 2, 58, 30, -90, -2, 1.55],
  ['point-high', 2, 31, 50, 0, -22, 16],
  ['exit', 2, 31.5, -10, 0, -4, 1.55],
  ['sky-high', 0, 31, 30, 180, -30, 60],
  ['dbg-dune', 0, 29, 41, 0, -35, 2.5]
];

function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

(async () => {
  const only = process.argv.slice(2);
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/' + encodeURIComponent('Play Inkbolt.html');
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&zcheck=1&plan=island');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && !document.getElementById('boot'), null, { timeout: 90000 });
  const info = await pg.evaluate(() => {
    const G = IB.Game, L = G.level;
    G.player.protect = 1e9; if (G.guard) G.guard.on = false;
    window.__q = null; window.requestAnimationFrame = cb => { window.__q = cb; return 1; };
    return { zfight: L.zfight, tris: L.zones.map(z => z.tris), total: L.tris, backdrop: L.root.children.filter(o => o.isMesh && o.geometry.index).map(m => m.geometry.index.count / 3) };
  });
  console.log('zfight:', info.zfight.length ? info.zfight.slice(0, 8).join(' | ') : 'clean', ' zone tris', info.tris.join(','), 'total', info.total, 'backdrop meshes', info.backdrop.map(Math.round).join(','));
  await pg.waitForFunction(() => !!window.__q, null, { timeout: 20000 });
  await pg.evaluate(() => {
    window.__now = performance.now();
    window.__step = n => { for (let i = 0; i < n; i++) { const cb = window.__q; window.__q = null; if (!cb) break; window.__now += 1000 / 60; cb(window.__now); } };
    IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
    IB.Game.level.zones.forEach(z => { z.queue.length = 0; z.plan = Object.assign({}, z.plan, { waves: [[]] }); z.wave = 0; });
    const hud = document.getElementById('hud'); if (hud) hud.style.display = 'none';
  });
  fs.mkdirSync(OUT, { recursive: true });
  for (const [name, zi, c, r, yaw, pitch, eye] of SHOTS) {
    if (only.length && !only.includes(name)) continue;
    const st = await pg.evaluate(o => {
      const G = IB.Game, z = G.level.zones[o.zi];
      IB.Zones.setVisible(G.level, o.zi);
      G.zone = o.zi;
      const p = G.player; p.x = z.ox + o.c + 0.5; p.z = z.oz + o.r + 0.5; p.y = 0; p.vx = p.vz = p.vy = 0;
      p.yaw = o.yaw; p.pitch = o.pitch;
      IB.Player.eyeY = () => o.eye;
      G.ws.hidden = true; IB.Input.fire = false; G.shake = 0; G.trauma = 0; G.roll = 0;
      window.__step(3);
      IB.Zones.setVisible(G.level, o.zi);
      for (let k = 0; k < 3; k++) {
        G.player.yaw = o.yaw; G.player.pitch = o.pitch; G.player.x = z.ox + o.c + 0.5; G.player.z = z.oz + o.r + 0.5;
        G.player.vx = G.player.vz = 0; G.roll = 0; G.ws.hidden = true;
        window.__step(1);
      }
      const i = IB.Render.renderer.info.render;
      return { calls: i.calls, tris: i.triangles };
    }, { zi, c, r, yaw: yaw * D, pitch: pitch * D, eye });
    await pg.screenshot({ path: path.join(OUT, 'island-' + name + '.png') });
    console.log(name, JSON.stringify(st));
  }
  if (logs.length) console.log('console:', logs.slice(0, 10).join(' | '));
  await browser.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); });
