// INKBOLT: the levels 35+ robots under ?look=classic (and the single-file Play build unless DEV=1): spawn a Jet
// Trooper (pods open), a Rocket Soldier and a kusarigama Blade Bot, step and draw a few frames, no console errors.
// Run (after tools/build.py): node tests/e2e/jets-classic.js
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
(async () => {
  const srv = await new Promise(res => { const s = http.createServer((req, r) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' }); r.end(d); }); }).listen(0, () => res(s)); });
  const page = process.env.DEV ? 'Source/dev.html' : 'Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const pg = await (await browser.newContext({ viewport: { width: 480, height: 270 } })).newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto('http://localhost:' + srv.address().port + '/' + page + '?autotest=1&plan=greybox&look=classic');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 300000 });
  const out = await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const G = IB.Game, p = G.player; IB.AI.setLevel(36);
    const sp = (t, dx, dz) => { const s = __TEST__.spawnRobot(t, p.x + dx, p.z + dz), r = IB.AI.types[t].slots[s]; r.zone = G.zone; r.state = IB.AI.VIS[t].home; return r; };
    const j = sp('jet', 1, 8), k = sp('rocketeer', -2, 9), b = sp('blader', 2, 5); b.weaponId = 'kusari';
    j.vcool = 0; p.protect = 99;
    const c = { player: p, world: G.level.world, level: G.level, activeZone: G.zone, hurt: function () { }, shake: function () { }, onKill: G.onKill };
    for (let i = 0; i < 180; i++) { IB.AI.update(1 / 60, c); IB.Projectiles.update(1 / 60, c); if (i % 10 === 0) { IB.AI.sync(); IB.TrooperRig.sync(0.16); IB.Render.render(false); } }
    return { look: IB.Look ? IB.Look.on : null, jet: j.on, pod: +j.pod.toFixed(2), rl: !!(IB.TrooperRig.live['rocketeer' + k.slot] || {}).rl, km: b.km, rockets: IB.EnemyRockets.fired };
  });
  console.log(JSON.stringify(out));
  console.log(logs.length ? 'ERRORS ' + logs.slice(0, 4).join(' | ') : 'no console errors');
  await browser.close(); srv.close();
  process.exit(logs.length || out.look ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
