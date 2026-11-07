// INKBOLT The Spire (plan 'spire'): the mezzanines. The player walks up the Sky Lobby's grand stair onto the 4.5 m
// deck and stays there; the deck's glass rail keeps the player from dropping into the atrium; ground robots path to
// the stairs / escalators and reach a player on the lobby deck and on the trading floor's west gallery; robots cross
// the Sky Garden to a player on the ground; the player walks a sky-bridge on its floor. The render loop is paused and
// the real Player / AI code is stepped at a fixed 1/60 s (SwiftShader renders far slower than real time).
// Run (after tools/build.py): node tests/e2e/spire-climb.spec.js
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
  const ctx = await browser.newContext({ viewport: { width: 960, height: 540 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=spire');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 90000 });
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
    window.__sim = (secs, zi) => {
      const G = IB.Game, p = G.player, dt = 1 / 60;
      const ctx = { player: p, world: G.level.world, level: G.level, activeZone: zi, hurt: G.hurt, shake: function () { }, onKill: function () { } };
      for (let i = 0; i < Math.round(secs * 60); i++) { IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, ctx); if (IB.Projectiles) IB.Projectiles.update(dt, ctx); IB.AI.updateCorpses(dt); }
    };
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
  // nav: the lobby and the trading floor have deck cells at 4.5 m
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz; let up = 0;
    if (N.layers) for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k] && Math.abs(N.h[k] - 4.5) < 0.01) up++;
    return { layers: N.layers || 1, up };
  }));
  check('the lobby and the trading floor have a layered nav with the 4.5 m deck open', nav[0].up > 1500 && nav[2].up > 1500, JSON.stringify(nav));
  // the player walks up the lobby's grand stair (cols 29-32, rows 8-17, rising north) onto the deck
  const up = await pg.evaluate(() => { __place(0, 31, 19.5, 0); return __route(0, [[31, 17.5], [31, 7.5], [31, 4]], 20); });
  check('the player walks up the grand stair onto the 4.5 m deck', up.reached === 3 && Math.abs(up.y - 4.5) < 0.05, JSON.stringify(up));
  const stay = await pg.evaluate(() => { __sim(2, 0); const p = IB.Game.player; return { y: +p.y.toFixed(3), floor: IB.Game.level.world.floorAt(p.x, p.z, p.y + 0.1) }; });
  check('standing on the deck holds (no sinking, no falling)', Math.abs(stay.y - 4.5) < 0.01 && Math.abs(stay.floor - 4.5) < 0.01, JSON.stringify(stay));
  // the glass rail on the deck edge (east deck, rail column 54) keeps the player out of the atrium
  const rail = await pg.evaluate(() => { __place(0, 56, 30, 4.5); return __route(0, [[48, 30]], 3); });
  check('the deck rail keeps the player on the deck', rail.lo > 4.45, JSON.stringify(rail));
  async function chase(zi, at, robots, secs, goal) {
    const list = await pg.evaluate(([zi, at, robots]) => {
      __place(zi, at[0], at[1], at[2]);
      const Z = IB.Game.level.zones[zi];
      return robots.map(([type, c, r]) => {
        const slot = __TEST__.spawnRobot(type, Z.ox + c + 0.5, Z.oz + r + 0.5);
        const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
        if (type === 'bomber') rb.def = Object.assign({}, rb.def, { range: -9 });
        return [type, slot];
      });
    }, [zi, at, robots]);
    let best = 0, last = null, t = 0, near = 99;
    while (t < secs) {
      last = await pg.evaluate(([list, zi]) => {
        __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot], p = IB.Game.player;
        return { on: r.on, x: +r.x.toFixed(2), y: +r.y.toFixed(2), z: +r.z.toFixed(2), state: r.state, d: Math.hypot(r.x - p.x, r.z - p.z) };
      }, [list, zi]);
      t += 0.5; best = Math.max(best, last.on ? last.y : 0); near = Math.min(near, last.d);
      if (best > goal && near < 4) break;
    }
    return { best, last, t, near };
  }
  let w = await chase(0, [57, 12, 4.5], [['crawler', 20, 40]], 70, 4.4);
  check('lobby: a Crawler from the ground floor climbs to the player on the east deck within 70 s', w.best > 4.4 && w.near < 4, 'max y ' + w.best.toFixed(2) + ' near ' + w.near.toFixed(1) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(2, [3.5, 24, 4.5], [['crawler', 20, 52]], 70, 4.4);
  check('trading floor: a Crawler climbs to the player on the west gallery within 70 s', w.best > 4.4 && w.near < 4, 'max y ' + w.best.toFixed(2) + ' near ' + w.near.toFixed(1) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(2, [42, 6, 4.5], [['bomber', 10, 52]], 70, 4.4);
  check('trading floor: a Bomber reaches the player on the executive deck within 70 s', w.best > 4.4 && w.near < 4, 'max y ' + w.best.toFixed(2) + ' near ' + w.near.toFixed(1) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [18, 44, 0], [['crawler', 44, 4]], 40, 99);
  check('garden: a Crawler crosses the garden to the player', w.near < 4, 'dist ' + w.near.toFixed(2) + ' ' + JSON.stringify(w.last));
  // the sky-bridge between the lobby and the garden: the player walks its length on the floor
  const br = await pg.evaluate(() => {
    const G = IB.Game, Z = G.level.zones[0], gx = Z.exitGate.x;
    __place(0, gx - Z.ox, 3, 0); G.level.zones[0].exitGate.open = 1; G.level.zones[0].exitGate.box.on = false;
    G.level.zones[1].entryGate.box.on = false;
    return __route(0, [[gx - Z.ox, -6], [gx - Z.ox, -11]], 10);
  });
  check('the player walks along the sky-bridge on its floor', br.reached === 2 && br.lo > -0.01 && br.hi < 0.05, JSON.stringify(br));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
