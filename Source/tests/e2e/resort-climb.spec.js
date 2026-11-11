// INKBOLT Palmyra Cove Resort (plan 'resort'): the broken-limb / fallen-frond ramps and the tree platforms. The
// player walks up a ramp onto a platform 7.5 m up (zone 1 and zone 2), crosses a rope bridge to the next platform,
// is stopped by the platform rails, and a fall off a ramp only drops them to the sand (no damage); ground robots path
// to a ramp, climb it and reach a player on a platform. The render loop is paused and the real Player / AI code is
// stepped at a fixed 1/60 s (SwiftShader renders far slower than real time).
// Run (after tools/build.py): node tests/e2e/resort-climb.spec.js
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const TOP = 7.5;
let fails = 0;
function check(name, ok, info) { console.log((ok ? 'PASS ' : 'FAIL ') + name + (info ? '  ' + info : '')); if (!ok) fails++; }
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=resort');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
    window.__sim = (secs, zi) => {
      const G = IB.Game, p = G.player, dt = 1 / 60;
      const ctx = { player: p, world: G.level.world, level: G.level, activeZone: zi, hurt: G.hurt, shake: function () { }, onKill: function () { } };
      for (let i = 0; i < Math.round(secs * 60); i++) { IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, ctx); if (IB.Projectiles) IB.Projectiles.update(dt, ctx); IB.AI.updateCorpses(dt); }
    };
    // the player walks toward each way point in turn (zone-local metres); returns the path's lowest / highest y
    window.__route = (zi, pts, secs) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi], dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      let k = 0, lo = 1e9, hi = -1e9, n = 0;
      while (k < pts.length && n++ < secs * 60) {
        const tx = Z.ox + pts[k][0], tz = Z.oz + pts[k][1], dx = tx - p.x, dz = tz - p.z;
        if (Math.hypot(dx, dz) < 0.25) { k++; continue; }
        p.yaw = Math.atan2(-dx, -dz);
        IB.Player.step(p, inp, G.level.world, dt, null);
        lo = Math.min(lo, p.y); hi = Math.max(hi, p.y);
      }
      return { reached: k, of: pts.length, lo: +lo.toFixed(2), hi: +hi.toFixed(2), x: +(p.x - Z.ox).toFixed(2), y: +p.y.toFixed(2), z: +(p.z - Z.oz).toFixed(2), hp: p.health };
    };
    window.__place = (zi, x, z, y) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      p.protect = 0; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y; p.vx = p.vz = p.vy = 0;
    };
  });
  // nav: both zones have open cells on the 7.5 m platforms, and on the ramps between the ground and the platforms
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz; let up = 0, mid = 0;
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k]) { if (N.h[k] > 7.4) up++; else if (N.h[k] > 2 && N.h[k] < 6) mid++; }
    return { layers: N.layers, up, mid };
  }));
  check('both zones have a layered nav with open cells on the platforms and up the ramps', nav.every(n => n.layers > 1 && n.up > 250 && n.mid > 40), JSON.stringify(nav));
  // zone 1: up the broken limb (cols 61-62, rows 11-23, rising north) onto the treehouse platform
  let r = await pg.evaluate(() => { __place(0, 62.0, 26.0, 0); return __route(0, [[62.0, 24.0], [62.0, 11.0], [62.0, 8.5]], 30); });
  check('zone 1: the player walks up the broken limb onto the treehouse platform (7.5 m)', r.reached === 3 && Math.abs(r.y - TOP) < 0.05, JSON.stringify(r));
  const stay = await pg.evaluate(() => { __sim(2, 0); const p = IB.Game.player; return { y: +p.y.toFixed(3), floor: IB.Game.level.world.floorAt(p.x, p.z, p.y + 0.1) }; });
  check('standing on the platform holds (no sinking, no falling)', Math.abs(stay.y - TOP) < 0.01 && Math.abs(stay.floor - TOP) < 0.01, JSON.stringify(stay));
  // the rails: walking into the platform's north, east and south edges does not drop the player
  for (const [nm, s, g] of [['north', [52, 5], [52, 1]], ['east', [67.5, 9], [72, 9]], ['south', [57, 8.5], [57, 13]]]) {
    r = await pg.evaluate(([s, g]) => { __place(0, s[0], s[1], 7.5); return __route(0, [g], 3); }, [s, g]);
    check('zone 1: the platform rail (' + nm + ') keeps the player up', r.lo > TOP - 0.05, JSON.stringify(r));
  }
  // a fall off the side of the limb drops the player to the sand, unhurt
  r = await pg.evaluate(() => { __place(0, 62.0, 14.0, 5.7); const r = __route(0, [[66.0, 14.0]], 4); __sim(1.5, 0); const p = IB.Game.player; return Object.assign(r, { y: +p.y.toFixed(2), hp: p.health, max: p.maxHp }); });
  check('zone 1: falling off the limb lands on the ground with no damage', Math.abs(r.y) < 0.05 && r.hp === r.max, JSON.stringify(r));
  // zone 2: up the centre limb (cols 37-38, rows 35-47) to the CANOPY SUITE platform, across the rope bridge east
  r = await pg.evaluate(() => { __place(1, 37.9, 50.0, 0); return __route(1, [[37.9, 48.0], [37.9, 34.0], [37.9, 32.6]], 30); });
  check('zone 2: the player walks up the centre limb onto the platform', r.reached === 3 && Math.abs(r.y - TOP) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[42.5, 31.4], [48.4, 31.4], [48.4, 29.0], [63.6, 29.0], [65.5, 29.5]], 40));
  check('zone 2: the player crosses the rope bridge to the east platform at 7.5 m', r.reached === 5 && r.lo > TOP - 0.05 && Math.abs(r.y - TOP) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 55.0, 29.0, 7.5); return __route(1, [[55.0, 33.0]], 3); });
  check('zone 2: the bridge ropes keep the player on the bridge', r.lo > TOP - 0.05, JSON.stringify(r));
  // the frond ramp at the east platform (cols 49-61, rows 17-18, rising east)
  r = await pg.evaluate(() => { __place(1, 46.5, 18.0, 0); return __route(1, [[48.5, 18.0], [62.0, 18.0], [64.0, 19.5]], 30); });
  check('zone 2: the player walks up the eastward ramp onto the east platform', r.reached === 3 && Math.abs(r.y - TOP) < 0.05, JSON.stringify(r));
  // robots climb after the player
  async function chase(zi, deck, robots, secs, goal) {
    const list = await pg.evaluate(([zi, deck, robots]) => {
      __place(zi, deck[0], deck[1], deck[2]);
      IB.Game.player.protect = 1e9;
      const Z = IB.Game.level.zones[zi];
      return robots.map(([type, c, r]) => {
        const slot = __TEST__.spawnRobot(type, Z.ox + c + 0.5, Z.oz + r + 0.5);
        const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
        return [type, slot];
      });
    }, [zi, deck, robots]);
    let best = 0, last = null, t = 0;
    while (t < secs) {
      last = await pg.evaluate(([list, zi]) => { __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot], p = IB.Game.player; return { on: r.on, x: +r.x.toFixed(2), y: +r.y.toFixed(2), z: +r.z.toFixed(2), d: +Math.hypot(r.x - p.x, r.z - p.z).toFixed(2), state: r.state }; }, [list, zi]);
      t += 0.5; if (last.on && last.d < 4) best = Math.max(best, last.y);
      if (best > goal) break;
    }
    return { best, last, t };
  }
  let w = await chase(0, [57.0, 9.0, TOP], [['crawler', 40, 40]], 60, TOP - 0.1);
  check('zone 1: a Crawler from the pool deck climbs the limb and reaches the player (< 4 m) on the treehouse platform within 60 s', w.best > TOP - 0.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [10.0, 22.0, TOP], [['crawler', 60, 58]], 80, TOP - 0.1);
  check('zone 2: a Crawler from the far corner climbs and crosses a bridge to the player (< 4 m) on the west platform within 80 s', w.best > TOP - 0.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [24.0, 6.5, TOP], [['blader', 50, 60]], 80, TOP - 0.1);
  check('zone 2: a Blade Bot climbs to the player (< 4 m) on the north platform within 80 s', w.best > TOP - 0.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
