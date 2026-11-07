// INKBOLT Redwood Hollow (plan 'grove'): the climbable redwoods and the 9 m walkways. The player walks up a redwood's
// staircase (it wraps the trunk: south flight east, east flight north, north flight west) onto its platform, crosses
// a plank bridge to the next tree and is stopped by the platform rails; ground robots path to the stairs, climb them
// and reach a player on a platform, and cross a bridge to another tree. The render loop is paused and the real
// Player / AI code is stepped at a fixed 1/60 s (SwiftShader renders far slower than real time).
// Run (after tools/build.py): node tests/e2e/grove-climb.spec.js
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
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
// tree footprints (top-left cell) and bridges in the zone files (tools/grove_zones.py)
const Z1 = { A: [5, 24], B: [37, 24], C: [12, 5], D: [31, 5] };
const Z3 = { A: [3, 18], B: [21, 18], C: [39, 18] };

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 960, height: 540 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=grove');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 90000 });
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
      return { reached: k, of: pts.length, lo: +lo.toFixed(2), hi: +hi.toFixed(2), x: +(p.x - Z.ox).toFixed(2), y: +p.y.toFixed(2), z: +(p.z - Z.oz).toFixed(2) };
    };
    window.__place = (zi, x, z, y) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      p.protect = 1e9; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y; p.vx = p.vz = p.vy = 0;
    };
  });
  // nav: every zone has walkable surfaces at the 9 m level (platforms and bridges)
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz; let up = 0;
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k] && N.h[k] > 8.9) up++;
    return { layers: N.layers, up };
  }));
  check('every zone has a layered nav with open cells at the 9 m walkway level', nav.every(n => n.layers > 1 && n.up > 300), JSON.stringify(nav));
  // the player climbs tree A of zone 1: up the south flight eastward, the east flight north, the north flight west
  const c = (t, dx, dz) => [t[0] + 4 + dx, t[1] + 4 + dz];   // tree centre (Blender x, -y) -> zone-local game x, z
  const climb = await pg.evaluate(([A, pts]) => { __place(0, A[0] + 4 - 5.0, A[1] + 4 + 2.6, 0); return __route(0, pts, 30); },
    [Z1.A, [c(Z1.A, -4.2, 2.6), c(Z1.A, 2.6, 2.6), c(Z1.A, 2.6, -2.6), c(Z1.A, -1.0, -2.6), c(Z1.A, -2.5, 0.0)]]);
  check('the player walks up the staircase onto the 9 m platform', climb.reached === 5 && Math.abs(climb.y - 9) < 0.05, JSON.stringify(climb));
  // ... and stays there
  const stay = await pg.evaluate(() => { __sim(2, 0); const p = IB.Game.player; return { y: +p.y.toFixed(3), floor: IB.Game.level.world.floorAt(p.x, p.z, p.y + 0.1) }; });
  check('standing on the platform holds (no sinking, no falling)', Math.abs(stay.y - 9) < 0.01 && Math.abs(stay.floor - 9) < 0.01, JSON.stringify(stay));
  // across the bridge to tree B (east), staying at 9 m
  const cross = await pg.evaluate(([pts]) => __route(0, pts, 40), [[c(Z1.A, -2.5, 3.0), c(Z1.A, 3.0, 3.0), c(Z1.A, 3.3, 0.3), c(Z1.B, -3.0, 0.3), c(Z1.B, -2.5, 2.5)]]);
  check('the player crosses the bridge to the next redwood at 9 m', cross.reached === 5 && cross.lo > 8.95 && Math.abs(cross.y - 9) < 0.05, JSON.stringify(cross));
  // the rails: walking at the platform's south and west edges and into the stairwell rail does not drop the player
  for (const [name, start, goal] of [['south', [-1.5, 1.0], [-1.5, 6.0]], ['west', [-1.5, 2.5], [-6.0, 2.5]], ['stairwell', [2.5, 0.5], [2.5, -3.5]]]) {
    const r = await pg.evaluate(([A, s, g]) => { __place(0, A[0] + 4 + s[0], A[1] + 4 + s[1], 9); return __route(0, [[A[0] + 4 + g[0], A[1] + 4 + g[1]]], 3); }, [Z1.B, start, goal]);
    check('the platform rail (' + name + ') keeps the player on the platform', r.lo > 8.95, JSON.stringify(r));
  }
  // robots: a Crawler from the ground climbs to the player on tree A's platform
  async function chase(zi, deck, robots, secs, goal) {
    const list = await pg.evaluate(([zi, deck, robots]) => {
      __place(zi, deck[0], deck[1], deck[2]);
      const Z = IB.Game.level.zones[zi];
      return robots.map(([type, c, r]) => {
        const slot = __TEST__.spawnRobot(type, Z.ox + c + 0.5, Z.oz + r + 0.5);
        const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
        if (type === 'bomber') rb.def = Object.assign({}, rb.def, { range: -9 });   // no fuse: we only watch it climb
        return [type, slot];
      });
    }, [zi, deck, robots]);
    let best = 0, last = null, t = 0;
    while (t < secs) {
      last = await pg.evaluate(([list, zi]) => { __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot]; return { on: r.on, x: +r.x.toFixed(2), y: +r.y.toFixed(2), z: +r.z.toFixed(2), state: r.state }; }, [list, zi]);
      t += 0.5; best = Math.max(best, last.on ? last.y : 0);
      if (best > goal) break;
    }
    return { best, last, t };
  }
  let w = await chase(0, [Z1.A[0] + 4 - 2.5, Z1.A[1] + 4, 9], [['crawler', 18, 40]], 60, 8.9);
  check('a Crawler climbs the redwood staircase to the player on the 9 m platform within 60 s', w.best > 8.9, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(0, [Z1.B[0] + 4 - 2.5, Z1.B[1] + 4, 9], [['bomber', 4, 40]], 70, 8.9);
  check('a Bomber from across the zone climbs to the player on the far redwood within 70 s', w.best > 8.9, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  const smooth = await pg.evaluate(() => { const r = IB.AI.robots.find(q => q.on && q.type === 'bomber'); return r ? { y: r.y, fy: r.fy, gy: r.gy } : null; });
  check('its foot height follows the floor under it', smooth && Math.abs(smooth.gy - smooth.fy) < 0.35, JSON.stringify(smooth));
  // zone 3: a Crawler to the player on the middle tree of the three-tree skyway
  w = await chase(2, [Z3.B[0] + 4 - 2.5, Z3.B[1] + 4, 9], [['crawler', 8, 33]], 70, 8.9);
  check('zone 3: a Crawler reaches the player on the middle redwood within 70 s', w.best > 8.9, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  // the hills: a Crawler on the far side of zone 2 walks over them to a player on the ground
  w = await chase(1, [25, 44, 0], [['crawler', 44, 3]], 30, 99);
  const near = await pg.evaluate(() => { const r = IB.AI.robots.find(q => q.on && q.type === 'crawler'), p = IB.Game.player; return r ? Math.hypot(r.x - p.x, r.z - p.z) : 99; });
  check('zone 2: a Crawler crosses the hills to the player', near < 4, 'dist ' + near.toFixed(2) + ' ' + JSON.stringify(w.last));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
