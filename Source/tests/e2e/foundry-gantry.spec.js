// INKBOLT Titan Foundry (plan 'foundry'): the armour hall's gantry walkway at 6 m round the half-built titan, and the
// buttresses' collision. The player walks up the west stair onto the back landing and is held there; the rails keep
// the player on the deck (toward the titan and over the stairwell); ground robots path to a stair, climb it and reach
// a player on the walkway; a buttress stops the player like the wall it stands out from. The render loop is paused and
// the real Player / AI code is stepped at a fixed 1/60 s (SwiftShader renders far slower than real time).
// Run (after tools/build.py): node tests/e2e/foundry-gantry.spec.js
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
// the armour bay 'Y' (tools/foundry_zones.py): cells 18..41 x 4..21, centre (30, 13); bay frame x east, y north = -z
const BAY = { cx: 30, cz: 13 };
const at = (x, y) => [BAY.cx + x, BAY.cz - y];   // bay-local (x, Blender y) -> zone-local game (x, z)

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 960, height: 540 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=foundry');
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
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz; let up = 0;
    if (!N.layers) return { layers: 1, up: 0 };
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k] && N.h[k] > 5.9) up++;
    return { layers: N.layers, up };
  }));
  check('the armour hall has a layered nav with open cells on the 6 m walkway', nav[1].layers > 1 && nav[1].up > 200, JSON.stringify(nav));
  // the player walks up the west stair (it rises north beside the west wing) onto the back landing
  const S = at(-11.0, -9.6), T = at(-11.0, 3.4), L = at(-11.0, 6.4);   // (the landing's spawn can stands at -9.5, 5.5)
  const climb = await pg.evaluate(([S, pts]) => { __place(1, S[0], S[1], 0); return __route(1, pts, 30); }, [S, [at(-11.0, -8.6), T, L]]);
  check('the player walks up the stair onto the 6 m walkway', climb.reached === 3 && Math.abs(climb.y - 6) < 0.05, JSON.stringify(climb));
  const stay = await pg.evaluate(() => { __sim(2, 1); const p = IB.Game.player; return { y: +p.y.toFixed(3), floor: IB.Game.level.world.floorAt(p.x, p.z, p.y + 0.1) }; });
  check('standing on the walkway holds (no sinking, no falling)', Math.abs(stay.y - 6) < 0.01 && Math.abs(stay.floor - 6) < 0.01, JSON.stringify(stay));
  // along the west wing to the front bridge and across it, staying at 6 m
  const walk = await pg.evaluate(([pts]) => __route(1, pts, 40), [[at(-9.0, 5.0), at(-9.0, -7.7), at(9.0, -7.7), at(9.0, 2.0)]]);
  check('the player walks the wing, the front bridge and the far wing at 6 m', walk.reached === 4 && walk.lo > 5.95, JSON.stringify(walk));
  // the rails: toward the titan from a wing, off the front of the bridge, off the landing's back edge
  for (const [name, s, g] of [['wing inner', [-9.0, 0.0], [-5.0, 0.0]], ['bridge front', [0.0, -7.6], [0.0, -11.0]], ['landing back', [-11.0, 6.5], [-11.0, 9.5]], ['stairwell', [-9.0, -4.0], [-12.0, -4.0]]]) {
    const r = await pg.evaluate(([s, g]) => { __place(1, s[0], s[1], 6); return __route(1, [g], 3); }, [at(...s), at(...g)]);
    check('the walkway rail (' + name + ') keeps the player on the deck', r.lo > 5.95, JSON.stringify(r));
  }
  // robots: ground robots path to a stair, climb it and reach the player on the landing
  async function chase(zi, deck, robots, secs, goal) {
    const list = await pg.evaluate(([zi, deck, robots]) => {
      __place(zi, deck[0], deck[1], deck[2]);
      const Z = IB.Game.level.zones[zi];
      return robots.map(([type, c, r]) => {
        const slot = __TEST__.spawnRobot(type, Z.ox + c + 0.5, Z.oz + r + 0.5);
        const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
        if (type === 'bomber') rb.def = Object.assign({}, rb.def, { range: -9 });
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
  const D = at(-10.5, 5.5);
  let w = await chase(1, [D[0], D[1], 6], [['crawler', 12, 34]], 60, 5.9);
  check('a Crawler climbs a stair to the player on the gantry within 60 s', w.best > 5.9, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  const E = at(10.5, 5.5);
  w = await chase(1, [E[0], E[1], 6], [['bomber', 30, 50]], 70, 5.9);
  check('a Bomber from across the hall climbs to the player on the east landing within 70 s', w.best > 5.9, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  // a buttress collides: walking east into the one on the east wall at row 36 (zone 1) stops the player in front of it
  const b = await pg.evaluate(() => { __place(0, 55.5, 36.5, 0); return __route(0, [[58.8, 36.5]], 3); });
  check('a buttress stops the player (its face 1.32 m out from the wall face at x 59)', b.x < 57.4, JSON.stringify(b));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
