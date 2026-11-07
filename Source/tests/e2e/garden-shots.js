// INKBOLT Wide Garden Playground review: screenshots of each garden from fixed spots (overviews, the playgrounds from
// the ground, from their decks, the gates) -> tests/e2e/review/garden-*.png, plus the z-fighting report.
// Run (after tools/build.py): node tests/e2e/garden-shots.js [ONLY=name,name]
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const OUT = path.join(__dirname, 'review');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}
// [name, zone, map column, map row, eye height (m above the floor) | null, yaw (0 = north, + = turn left), pitch, standY]
const SHOTS = [
  ['lawns-overview', 0, 27, 49, 16, 0.0, -0.42, 0],
  ['lawns-tower', 0, 24, 33, null, 0.75, 0.02, 0],
  ['lawns-deck', 0, 14, 21, null, -2.3, -0.25, 2.1],
  ['lawns-fountain', 0, 46, 40, null, 0.45, -0.02, 0],
  ['lawns-gate', 0, 27, 6, null, 0.0, 0.05, 0],
  ['fort-overview', 1, 29, 50, 18, 0.0, -0.45, 0],
  ['fort-ground', 1, 20, 40, null, -0.35, 0.1, 0],
  ['fort-under', 1, 22, 27, null, -1.57, 0.05, 0],
  ['fort-deck', 1, 29, 26, null, 0.6, -0.2, 2.7],
  ['fort-gazebo', 1, 22, 15, null, 1.0, -0.05, 0],
  ['cove-overview', 2, 29, 49, 18, 0.25, -0.42, 0],
  ['cove-ship', 2, 18, 28, null, 0.4, 0.05, 0],
  ['cove-shipdeck', 2, 12, 14, null, -1.4, -0.15, 2.1],
  ['cove-tower', 2, 41, 30, null, 0.0, 0.08, 0],
  ['trail', 0, 27, 2, null, 0.0, 0.0, 0]
];

(async () => {
  const only = process.env.ONLY ? process.env.ONLY.split(',') : null;
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&zcheck=1&plan=garden');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 90000 });
  const info = await pg.evaluate(() => {
    const G = IB.Game;
    G.player.protect = 1e9; if (G.guard) G.guard.on = false;
    IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
    G.level.zones.forEach(z => { z.queue.length = 0; z.plan = Object.assign({}, z.plan, { waves: [[]] }); z.wave = 0; });
    return { zfight: G.level.zfight, tris: G.level.zones.map(z => z.tris), layers: G.level.zones.map(z => z.nav.layers || 1) };
  });
  console.log('zfight', JSON.stringify(info.zfight), 'zone tris', info.tris.join(','), 'nav layers', info.layers.join(','));
  fs.mkdirSync(OUT, { recursive: true });
  for (const [name, zi, c, r, eye, yaw, pitch, standY] of SHOTS) {
    if (only && !only.includes(name)) continue;
    await pg.evaluate(([zi, c, r, eye, yaw, pitch, standY]) => {
      const G = IB.Game, p = G.player, z = G.level.zones[zi];
      G.level.zones.forEach(q => { q.group.visible = true; });
      G.level.trails.forEach(t => { t.group.visible = true; });
      p.x = z.ox + c + 0.5; p.z = z.oz + r + 0.5; p.y = standY; p.vx = p.vz = p.vy = 0; p.yaw = yaw; p.pitch = pitch;
      IB.Player.__eye = IB.Player.__eye || IB.Player.eyeY;
      IB.Player.eyeY = eye ? (pp) => pp.y + eye : IB.Player.__eye;
    }, [zi, c, r, eye, yaw, pitch, standY]);
    await pg.waitForTimeout(900);
    const pos = await pg.evaluate(() => [IB.Game.player.x.toFixed(1), IB.Game.player.y.toFixed(2), IB.Game.player.z.toFixed(1)]);
    await pg.screenshot({ path: path.join(OUT, 'garden-' + name + '.png') });
    console.log('shot', name, pos.join(','));
  }
  if (logs.length) console.log('LOGS', logs.slice(0, 10).join('\n'));
  await browser.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); });
