// INKBOLT Zenith Command (plan 'highrise'), the roof zone (src/game/rooftops.js): open air between the buildings and
// the planks robots throw across it.
//   * the roof zone has its void, its plank sites (one plank laid from the start) and a nav grid with no surface in
//     the open air
//   * the player who walks off a roof edge where a plank lands falls and dies (the usual death flow, "The Long Drop")
//   * a robot that falls is wrecked; a drone over the open air stays up
//   * a soldier on the west roof (2 m down) throws a plank across the gap to the zone's own roof: it slams down, turns
//     walkable (floor under its middle, nav nodes along it) and the soldier crosses it to the player
//   * the player walks that plank onto the west roof and back without falling
//   * from the entry, the player reaches the exit door over the plank laid from the start
// The render loop is paused and the real Player / AI / Rooftops code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/highrise-roofs.spec.js
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
  await pg.goto(base + '?autotest=1&plan=highrise');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 90000 });
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const ZI = 2;
    window.__ctx = (zi) => { const G = IB.Game; return { player: G.player, world: G.level.world, level: G.level, activeZone: zi, hurt: function () { }, shake: function () { }, onKill: function () { } }; };
    const idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
    window.__sim = (secs, zi) => {
      const G = IB.Game, p = G.player, dt = 1 / 60, c = __ctx(zi);
      for (let i = 0; i < Math.round(secs * 60); i++) {
        if (p.alive) IB.Player.step(p, idle, G.level.world, dt, null);
        IB.AI.update(dt, c); IB.Rooftops.update(dt, c); IB.AI.updateCorpses(dt);
      }
    };
    // walk the player through zone-local waypoints (feet height tracked); stops early on death
    window.__route = (zi, pts, secs) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi], dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      let k = 0, lo = 1e9, hi = -1e9, n = 0; const c = __ctx(zi);
      while (k < pts.length && n++ < secs * 60 && p.alive) {
        const tx = Z.ox + pts[k][0], tz = Z.oz + pts[k][1], dx = tx - p.x, dz = tz - p.z;
        if (Math.hypot(dx, dz) < 0.3) { k++; continue; }
        p.yaw = Math.atan2(-dx, -dz);
        IB.Player.step(p, inp, G.level.world, dt, null);
        IB.Rooftops.update(dt, c);
        lo = Math.min(lo, p.y); hi = Math.max(hi, p.y);
      }
      return { reached: k, of: pts.length, lo: +lo.toFixed(2), hi: +hi.toFixed(2), x: +(p.x - Z.ox).toFixed(2), y: +p.y.toFixed(2), z: +(p.z - Z.oz).toFixed(2), alive: p.alive, dead: G.dead, killer: G.killer || null };
    };
    // the roof zone, quiet: no waves, the player alive and unhurt at a zone-local spot
    window.__place = (x, z, y) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[ZI];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      G.zone = ZI; Z.state = 'active';
      document.body.classList.remove('dead'); G.dead = false; p.alive = true;
      p.protect = 1e9; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y; p.vx = p.vz = p.vy = 0;
    };
    window.__spawn = (type, x, z, y) => {
      const Z = IB.Game.level.zones[ZI], r = IB.AI.spawn(type, Z.ox + x, Z.oz + z, ZI, Z.ox + x, Z.oz + z, { y: y });
      r.state = IB.AI.VIS[type].home; r.st = 0; r.thinkT = 0; r.gy = r.fy = y; r.y = y + (IB.AI.VIS[type].flying ? r.hy : 0);
      return [type, r.slot];
    };
    window.__bot = (b) => { const r = IB.AI.types[b[0]].slots[b[1]], Z = IB.Game.level.zones[ZI]; return { on: r.on, x: +(r.x - Z.ox).toFixed(2), z: +(r.z - Z.oz).toFixed(2), y: +r.y.toFixed(2), fy: +(r.fy || 0).toFixed(2), state: r.state }; };
    __TEST__.teleport(ZI);
  });

  // ---- the roof zone
  const info = await pg.evaluate(() => {
    const L = IB.Game.level, I = IB.Rooftops.info(L), Z = L.zones[2], N = Z.nav, NC = N.nx * N.nz, W = L.world;
    let voidNodes = 0;
    for (let k = 0; k < NC * (N.layers || 1); k++) if (!N.blocked[k] && N.h && N.h[k] < -100) voidNodes++;
    return { zones: I.map(q => q.zone), sites: I[0].sites.length, laid: I[0].sites.filter(s => s.laid).length, killY: I[0].killY,
      layers: N.layers || 1, voidNodes, gap: W.groundAt(Z.ox + 18, Z.oz + 40), roof: W.groundAt(Z.ox + 30, Z.oz + 45),
      west: W.floorAt(Z.ox + 8, Z.oz + 40, 0), east: W.floorAt(Z.ox + 65, Z.oz + 45, 5) };
  });
  check('the roof zone has open air, 8 plank sites (1 laid at the start), a layered nav with nothing to stand on in the gaps',
    info.zones.join() === '2' && info.sites === 8 && info.laid === 1 && info.layers > 1 && info.voidNodes === 0 && info.gap < -200 && info.roof === 0 &&
    Math.abs(info.west + 2) < 0.01 && Math.abs(info.east - 1.5) < 0.01, JSON.stringify(info));

  // ---- falls
  const fall = await pg.evaluate(() => { __place(23.5, 37.5, 0); return __route(2, [[17.5, 37.5], [14, 37.5]], 6); });
  check('walking off the roof edge into a gap: the player falls and dies (The Long Drop)', !fall.alive && fall.dead && fall.lo < -6 && /Drop/.test(fall.killer || ''), JSON.stringify(fall));
  const par = await pg.evaluate(() => { __place(22.5, 31.5, 0); return __route(2, [[17.5, 31.5]], 3); });
  check('a parapet keeps the player on the roof', par.alive && par.lo > -0.01 && par.x > 20.2, JSON.stringify(par));
  const rf = await pg.evaluate(() => {
    __place(38, 55, 0);
    const a = __spawn('soldier', 18, 30, 0), d = __spawn('drone', 18, 44, 0);
    __sim(3, 2);
    return { soldier: __bot(a), drone: __bot(d) };
  });
  check('a robot over open air falls and is wrecked; a drone over a gap stays up', !rf.soldier.on && rf.drone.on && rf.drone.y > 1.5, JSON.stringify(rf));

  // ---- a soldier on the west roof throws a plank across to the player's roof, then crosses it
  const before = await pg.evaluate(() => IB.Rooftops.info(IB.Game.level)[0].sites.map(s => s.laid));
  const throwRes = await pg.evaluate(() => {
    __place(30, 36, 0);
    const b = __spawn('soldier', 13.5, 36.5, -2);
    window.__thrower = b;
    let t = 0, laid = -1;
    while (t < 20 && laid < 0) {
      __sim(0.5, 2); t += 0.5;
      IB.Rooftops.info(IB.Game.level)[0].sites.forEach((s, i) => { if (s.laid && !s.start && laid < 0) laid = i; });
    }
    __sim(1.2, 2);   // the plank's swing and slam
    const I = IB.Rooftops.info(IB.Game.level)[0], s = I.sites[laid] || { ends: [{}, {}] };
    const mx = (s.ends[0].x + s.ends[1].x) / 2, mz = (s.ends[0].z + s.ends[1].z) / 2, Z = IB.Game.level.zones[2];
    const node = IB.Zones.navNode(Z, mx, mz, -1);
    return { t, laid, anim: s.anim, ends: s.ends.map(e => e.h), floorMid: +IB.Game.level.world.floorAt(mx, mz, 5).toFixed(2), node, bot: __bot(b) };
  });
  check('a soldier on the west roof throws a plank across the gap', throwRes.laid >= 0 && !before[throwRes.laid] && !throwRes.anim && throwRes.t < 15, JSON.stringify(throwRes));
  check('the plank is walkable: floor under its middle between the two roofs, a nav node on it', throwRes.floorMid > -2 && throwRes.floorMid < 0.5 && throwRes.node >= 0, JSON.stringify(throwRes));
  // the soldier comes out onto the plank to get its range (a gunner keeps 8 - 16 m); a blade bot from the west roof
  // runs the plank all the way to the player
  let cross = null, sol = null;
  const bl = await pg.evaluate(() => { window.__runner = __spawn('blader', 8.5, 44.5, -2); return __bot(__runner); });
  for (let t = 0; t < 40; t += 1) {
    cross = await pg.evaluate(() => { __sim(1, 2); const r = __bot(__runner), p = IB.Game.player, Z = IB.Game.level.zones[2]; r.d = +Math.hypot(r.x - (p.x - Z.ox), r.z - (p.z - Z.oz)).toFixed(2); return r; });
    if (!cross.on || (cross.x > 20.5 && Math.abs(cross.fy) < 0.5 && cross.d < 4)) break;
  }
  sol = await pg.evaluate(() => __bot(__thrower));
  check('the soldier comes out onto the plank, on its board', sol.on && sol.x > 16 && sol.fy > -2.05, JSON.stringify(sol));
  check('a blade bot from the west roof runs the plank onto the player\'s roof and reaches the player', cross.on && cross.x > 20.5 && Math.abs(cross.fy) < 0.5 && cross.d < 4, JSON.stringify(bl) + ' -> ' + JSON.stringify(cross));

  // ---- the player walks the plank both ways
  const walk = await pg.evaluate((i) => {
    const s = IB.Rooftops.info(IB.Game.level)[0].sites[i], Z = IB.Game.level.zones[2];
    const a = s.ends[0].h < s.ends[1].h ? s.ends[0] : s.ends[1], b = a === s.ends[0] ? s.ends[1] : s.ends[0];   // a: the west roof
    __place(b.x - Z.ox + 1.5, b.z - Z.oz, 0);
    const there = __route(2, [[a.x - Z.ox - 2.5, a.z - Z.oz]], 10);
    __sim(0.5, 2); there.y = +IB.Game.player.y.toFixed(2);
    const back = __route(2, [[b.x - Z.ox + 2.5, b.z - Z.oz]], 10);
    __sim(0.5, 2); back.y = +IB.Game.player.y.toFixed(2);
    return { there, back };
  }, throwRes.laid);
  check('the player walks the plank down onto the west roof and back up without falling',
    walk.there.reached === 1 && Math.abs(walk.there.y + 2) < 0.05 && walk.there.lo > -2.05 && walk.back.reached === 1 && Math.abs(walk.back.y) < 0.05 && walk.back.alive, JSON.stringify(walk));

  // ---- the exit: from the entry over the plank laid from the start to the door
  const ex = await pg.evaluate(() => {
    __place(38.5, 60.5, 0);
    const Z = IB.Game.level.zones[2], gx = Z.exitGate.x - Z.ox;
    return __route(2, [[38.5, 36.5], [34, 36.5], [34, 29], [34, 21], [34, 18.5], [gx, 18.5], [gx, 1.6]], 40);
  });
  check('from the entry the player reaches the exit door over the plank laid from the start', ex.reached === 7 && ex.alive && ex.lo > -0.05, JSON.stringify(ex));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
