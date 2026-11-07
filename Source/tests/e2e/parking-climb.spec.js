// INKBOLT Deep Park (plan 'parking'): moving between the car park's levels. The player walks up a 16 m car ramp from
// the floor onto the deck (3.6 m) and back down without hopping off the fine stair blocks, climbs a stair flight, is
// kept on the ramp and on the deck by the kerb rails, walks the split level of zone 2 (floor -> 1.8 m platform ->
// deck by half ramps) and the dock steps of zone 3; robots path up and down the ramps after the player: a Crawler and
// a Bomber from the floor to the deck, a Crawler from the deck down to the floor, a Crawler onto the zone 2 platform
// and onto the zone 3 loading dock. Sight lines cross the levels (deck rail to the floor below). The render loop is
// paused and the real Player / AI code is stepped at a fixed 1/60 s (SwiftShader renders far slower than real time).
// Run (after tools/build.py): node tests/e2e/parking-climb.spec.js
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

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=parking');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 90000 });
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
    window.__sim = (secs, zi) => {
      const G = IB.Game, p = G.player, dt = 1 / 60;
      const ctx = { player: p, world: G.level.world, level: G.level, activeZone: zi, hurt: G.hurt, shake: function () { }, onKill: function () { } };
      for (let i = 0; i < Math.round(secs * 60); i++) { IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, ctx); if (IB.Projectiles) IB.Projectiles.update(dt, ctx); IB.AI.updateCorpses(dt); }
    };
    // the player walks toward each way point in turn (zone-local metres): lowest / highest y, frames off the ground,
    // the largest drop of the eye in one frame
    window.__route = (zi, pts, secs, sprint) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi], dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: !!sprint, jumpPressed: false, slidePressed: false, crouch: false };
      let k = 0, lo = 1e9, hi = -1e9, n = 0, air = 0, eye = IB.Player.eyeY(p, false), jolt = 0;
      while (k < pts.length && n++ < secs * 60) {
        const tx = Z.ox + pts[k][0], tz = Z.oz + pts[k][1], dx = tx - p.x, dz = tz - p.z;
        if (Math.hypot(dx, dz) < 0.25) { k++; continue; }
        p.yaw = Math.atan2(-dx, -dz);
        IB.Player.step(p, inp, G.level.world, dt, null);
        if (!p.onGround) air++;
        const e = IB.Player.eyeY(p, false); jolt = Math.max(jolt, Math.abs(e - eye)); eye = e;
        lo = Math.min(lo, p.y); hi = Math.max(hi, p.y);
      }
      return { reached: k, of: pts.length, lo: +lo.toFixed(2), hi: +hi.toFixed(2), air, jolt: +jolt.toFixed(3), x: +(p.x - Z.ox).toFixed(2), y: +p.y.toFixed(2), z: +(p.z - Z.oz).toFixed(2) };
    };
    window.__place = (zi, x, z, y) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      G.zone = zi;
      p.protect = 1e9; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y; p.vx = p.vz = p.vy = 0; p.onGround = true; p.ease = 0;
    };
  });
  // nav: every zone has open cells on the deck (3.6 m); zone 2 on the platform (1.8 m), zone 3 on the dock (1.2 m)
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, out = { layers: N.layers, deck: 0, platform: 0, dock: 0 };
    for (let k = 0; k < NC * N.layers; k++) {
      if (N.blocked[k]) continue;
      if (Math.abs(N.h[k] - 3.6) < 0.01) out.deck++; else if (Math.abs(N.h[k] - 1.8) < 0.01) out.platform++; else if (Math.abs(N.h[k] - 1.2) < 0.01) out.dock++;
    }
    return out;
  }));
  check('every zone has a layered nav with open deck cells (3.6 m)', nav.every(n => n.layers > 1 && n.deck > 1500), JSON.stringify(nav));
  check('zone 2 has an open platform level (1.8 m), zone 3 an open dock (1.2 m)', nav[1].platform > 600 && nav[2].dock > 150, JSON.stringify(nav.map(n => [n.platform, n.dock])));

  // zone 1: up the west car ramp (floor at its south foot, the deck's north band at its top) and back down
  let r = await pg.evaluate(() => { __place(0, 18.5, 29.6, 0); return __route(0, [[18.5, 27.5], [18.5, 12.2], [18.5, 10.5]], 20); });
  check('the player walks up the 16 m ramp onto the deck', r.reached === 3 && Math.abs(r.y - 3.6) < 0.02, JSON.stringify(r));
  check('... smoothly: no frames in the air, the eye never jumps more than 6 cm in a frame', r.air <= 2 && r.jolt < 0.06, JSON.stringify(r));
  r = await pg.evaluate(() => __route(0, [[18.5, 12.2], [18.5, 28.0], [18.5, 29.3]], 20));
  check('and back down the ramp to the floor', r.reached === 3 && Math.abs(r.y) < 0.02, JSON.stringify(r));
  check('... staying on the ramp (no hopping off each step, no jolts)', r.air <= 2 && r.jolt < 0.06, JSON.stringify(r));
  r = await pg.evaluate(() => __route(0, [[18.5, 27.5], [18.5, 12.2], [18.5, 10.5]], 20, true));
  check('sprinting up the ramp works too', r.reached === 3 && Math.abs(r.y - 3.6) < 0.02, JSON.stringify(r));
  // the ramp's guard rails: pushing sideways halfway up does not drop the player off the ramp
  for (const [name, gx] of [['west', 14.0], ['east', 23.0]]) {
    const q = await pg.evaluate(([gx]) => { __place(0, 18.5, 20.0, 1.9); __sim(0.5, 0); return __route(0, [[gx, 20.0]], 3); }, [gx]);
    check('the ramp rail (' + name + ') keeps the player on the ramp', q.lo > 1.5 && q.x > 16.5 && q.x < 20.5, JSON.stringify(q));
  }
  // the stair flight from the entry plaza to the west deck band
  r = await pg.evaluate(() => { __place(0, 7.5, 50.5, 0); return __route(0, [[7.5, 49.2], [7.5, 41.0], [7.5, 38.5]], 15); });
  check('the player climbs the stair flight onto the west deck', r.reached === 3 && Math.abs(r.y - 3.6) < 0.02, JSON.stringify(r));
  // the deck-edge rail over the void
  r = await pg.evaluate(() => { __place(0, 11.0, 24.5, 3.6); return __route(0, [[18.0, 24.5]], 3); });
  check('the deck-edge rail keeps the player on the deck', r.lo > 3.55 && r.x < 14.5, JSON.stringify(r));
  // sight across the levels: from the deck rail down onto the void floor
  const los = await pg.evaluate(() => { const Z = IB.Game.level.zones[0], w = IB.Game.level.world; return w.los(Z.ox + 14.0, 3.6 + 1.55, Z.oz + 25, Z.ox + 24, 0.8, Z.oz + 34); });
  check('a player on the deck edge sees the void floor below', los, String(los));

  // zone 2: floor -> half ramp -> platform -> half ramp -> deck
  r = await pg.evaluate(() => { __place(1, 12.5, 48.5, 0); return __route(1, [[12.5, 47.4], [12.5, 38.0], [12.5, 36.0], [8.5, 30.0], [8.5, 22.6], [5.5, 22.4], [5.5, 13.0], [5.5, 11.0]], 30); });
  check('zone 2: the player walks up the half ramp to the platform and on up to the deck', r.reached === 8 && Math.abs(r.y - 3.6) < 0.02, JSON.stringify(r));
  // zone 3: up the dock steps onto the loading dock
  r = await pg.evaluate(() => { __place(2, 8.0, 12.0, 0); return __route(2, [[8.0, 10.6], [8.0, 6.5], [8.0, 4.5]], 12); });
  check('zone 3: the player climbs the dock steps onto the loading dock (1.2 m)', r.reached === 3 && Math.abs(r.y - 1.2) < 0.02, JSON.stringify(r));

  // robots chase the player between the levels
  async function chase(zi, at, robots, secs, goal, below) {
    const list = await pg.evaluate(([zi, at, robots]) => {
      __place(zi, at[0], at[1], at[2]);
      const Z = IB.Game.level.zones[zi];
      return robots.map(([type, c, r, y]) => {
        const slot = __TEST__.spawnRobot(type, Z.ox + c + 0.5, Z.oz + r + 0.5);
        const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
        if (y) { rb.fy = rb.gy = rb.y = y; rb.sy = y; }
        if (type === 'bomber') rb.def = Object.assign({}, rb.def, { range: -9 });   // no fuse: we only watch it climb
        return [type, slot];
      });
    }, [zi, at, robots]);
    let best = below ? 99 : 0, last = null, t = 0;
    while (t < secs) {
      last = await pg.evaluate(([list, zi]) => { __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot], p = IB.Game.player; return { on: r.on, x: +(r.x - IB.Game.level.zones[zi].ox).toFixed(2), y: +r.y.toFixed(2), z: +(r.z - IB.Game.level.zones[zi].oz).toFixed(2), state: r.state, d: +Math.hypot(r.x - p.x, r.z - p.z).toFixed(2) }; }, [list, zi]);
      t += 0.5;
      if (last.on) best = below ? Math.min(best, last.y) : Math.max(best, last.y);
      if (below ? (best < goal && last.d < 4) : best > goal) break;
    }
    return { best, last, t };
  }
  let w = await chase(0, [25.5, 9.5, 3.6], [['crawler', 10, 46]], 70, 3.5);
  check('a Crawler from the entry plaza paths up a ramp to the player on the deck within 70 s', w.best > 3.5, 'max y ' + w.best + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(0, [41.5, 30.5, 3.6], [['bomber', 25, 34]], 70, 3.5);
  check('a Bomber from the void floor reaches the player on the east deck within 70 s', w.best > 3.5, 'max y ' + w.best + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  const foot = await pg.evaluate(() => { const r = IB.AI.robots.find(q => q.on && q.type === 'bomber'); return r ? { y: r.y, fy: r.fy, gy: r.gy } : null; });
  check('its foot height follows the floor under it', foot && Math.abs(foot.gy - foot.fy) < 0.35, JSON.stringify(foot));
  w = await chase(0, [25.5, 34.5, 0], [['crawler', 9, 24, 3.6]], 70, 0.1, true);
  check('a Crawler on the deck comes down to the player on the floor within 70 s', w.best < 0.1 && w.last.d < 4, 'min y ' + w.best + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [10.5, 30.5, 1.8], [['crawler', 40, 50]], 70, 1.7);
  check('zone 2: a Crawler from the far floor reaches the player on the split-level platform', w.best > 1.7, 'max y ' + w.best + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(2, [12.5, 3.5, 1.2], [['crawler', 25, 40]], 70, 1.1);
  check('zone 3: a Crawler from the floor climbs onto the loading dock to the player', w.best > 1.1, 'max y ' + w.best + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
