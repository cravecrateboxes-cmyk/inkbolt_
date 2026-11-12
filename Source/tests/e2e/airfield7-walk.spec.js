// INKBOLT Airfield 7 (plan 'airfield7'): the walk through both zones and the climbs. The player walks the flight line
// from the main gate round the transport and across the apron, the taxiway and the runway (between the tank traps)
// to the gate in the north T-walls, the trail, then the hangar area's central road to the exit gate and the hatch (no
// invisible walls, nothing blocks the way); walks up the transport's ramp into the hold (1.2 m), up the control
// tower's stair onto its terrace (3.6 m), into the hardened aircraft shelter round the fighter, into the maintenance
// hangar and the ordnance igloo, and up the barracks stair onto the gallery (3.2 m); the rails keep the player up
// there. Ground robots follow into the hold, onto the tower terrace and onto the barracks gallery. Wall, barrier,
// run and span pieces are checked numerically to lie along their line of cells. The render loop is paused and the
// real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/airfield7-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=airfield7');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
    window.__sim = (secs, zi) => {
      const G = IB.Game, p = G.player, dt = 1 / 60;
      const ctx = { player: p, world: G.level.world, level: G.level, activeZone: zi, hurt: G.hurt, shake: function () { }, onKill: function () { } };
      for (let i = 0; i < Math.round(secs * 60); i++) { IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, ctx); if (IB.Projectiles) IB.Projectiles.update(dt, ctx); IB.AI.updateCorpses(dt); }
    };
    // walk toward each way point in turn (zone-local metres of zone zi; a point may lie outside it, on the trail)
    window.__route = (zi, pts, secs) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi], dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      let k = 0, lo = 1e9, hi = -1e9, n = 0, stuck = 0, last = [p.x, p.z];
      while (k < pts.length && n++ < secs * 60) {
        const tx = Z.ox + pts[k][0], tz = Z.oz + pts[k][1], dx = tx - p.x, dz = tz - p.z;
        if (Math.hypot(dx, dz) < 0.3) { k++; continue; }
        p.yaw = Math.atan2(-dx, -dz);
        IB.Player.step(p, inp, G.level.world, dt, null);
        lo = Math.min(lo, p.y); hi = Math.max(hi, p.y);
        if (n % 60 === 0) { if (Math.hypot(p.x - last[0], p.z - last[1]) < 0.2) stuck++; last = [p.x, p.z]; }
      }
      return { reached: k, of: pts.length, lo: +lo.toFixed(2), hi: +hi.toFixed(2), x: +(p.x - Z.ox).toFixed(2), y: +p.y.toFixed(2), z: +(p.z - Z.oz).toFixed(2), stuck };
    };
    window.__place = (zi, x, z, y) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      p.protect = 0; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y; p.vx = p.vz = p.vy = 0;
    };
    IB.Game.level.zones.forEach(z => { IB.Zones.setGate(z.exitGate, true, true); if (z.entryGate) IB.Zones.setGate(z.entryGate, true, true); });
  });
  // nav: open cells in the hold (1.2) and on the tower terrace (3.6) in zone 1, on the barracks gallery (3.2) in zone 2
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, h12: 0, h32: 0, h36: 0 };
    for (let k = 0; k < NC * (N.layers || 1); k++) if (!N.blocked[k] && N.h) {
      const h = N.h[k];
      if (Math.abs(h - 1.2) < 0.01) o.h12++; if (Math.abs(h - 3.2) < 0.01) o.h32++; if (Math.abs(h - 3.6) < 0.01) o.h36++;
    }
    return o;
  }));
  check('nav: zone 1 has open cells in the transport\'s hold and on the tower terrace, zone 2 on the barracks gallery',
    nav[0].h12 > 60 && nav[0].h36 > 150 && nav[1].h32 > 150, JSON.stringify(nav));

  // ---- the walk: the main gate -> round the transport -> the apron, taxiway, runway -> the north gate -> trail ->
  // the hangar area's road -> the exit gate -> the hatch
  let r = await pg.evaluate(() => { __place(0, 36.5, 76.0, 0); return __route(0, [[36.5, 73.5], [53.0, 73.5], [53.0, 45.0], [40.0, 40.0], [38.0, 38.0], [38.0, 3.0], [37.5, 1.5], [37.5, -6.0], [37.5, -11.0]], 160); });
  check('walk zone 1: from the main gate round the transport, across the apron, the taxiway and the runway to the north gate and onto the trail', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[35.5, 74.0], [35.5, 64.5], [36.0, 63.0], [36.0, 3.0], [35.5, 1.5], [35.5, -6.0], [35.5, -20.0]], 140));
  check('walk zone 2: the central road to the exit gate and the exit path', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit path leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));

  // ---- zone 1: up the ramp into the transport's hold; up the tower stair onto the terrace
  r = await pg.evaluate(() => { __place(0, 37.0, 72.0, 0); return __route(0, [[37.0, 66.0], [37.0, 55.0]], 30); });
  check('zone 1: up the transport\'s ramp into the hold (1.2 m)', r.reached === r.of && Math.abs(r.y - 1.2) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 37.0, 58.0, 1.2); return __route(0, [[39.5, 58.0]], 3); });
  check('zone 1: the hold walls keep the player inside', r.lo > 1.15 && r.x < 38.7, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 62.9, 54.5, 0); return __route(0, [[62.9, 52.6], [62.9, 42.3], [67.0, 42.3], [67.0, 49.5], [70.0, 49.5]], 60); });
  check('zone 1: up the tower stair onto the terrace (3.6 m) and round to its south side', r.reached === r.of && Math.abs(r.y - 3.6) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 70.0, 50.0, 3.6); return __route(0, [[70.0, 56.0]], 3); });
  check('zone 1: the terrace rail keeps the player up', r.lo > 3.55, JSON.stringify(r));

  // ---- zone 2: the shelter, the hangar, the igloo, the barracks gallery
  r = await pg.evaluate(() => { __place(1, 16.0, 36.0, 0); return __route(1, [[16.0, 30.5], [10.0, 28.5], [10.0, 8.0], [16.0, 6.0]], 50); });
  check('zone 2: into the hardened aircraft shelter and round the fighter to its back wall', r.reached === r.of && r.stuck === 0 && r.hi < 0.4, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 18.0, 66.0, 0); return __route(1, [[18.0, 48.5], [10.0, 48.5]], 40); });
  check('zone 2: into the maintenance hangar to the workshops', r.reached === r.of && r.stuck === 0 && r.hi < 0.4, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 52.5, 57.0, 0); return __route(1, [[56.0, 57.0], [65.0, 57.0]], 30); });
  check('zone 2: through the igloo door between the bomb racks', r.reached === r.of && r.stuck === 0 && r.hi < 0.4, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 42.5, 16.0, 0); return __route(1, [[42.5, 2.5], [45.0, 2.5], [45.0, 3.6], [45.0, 12.5], [45.0, 13.0], [55.0, 12.5]], 60); });
  check('zone 2: round the barracks and up its west stair onto the gallery (3.2 m)', r.reached === r.of && Math.abs(r.y - 3.2) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 55.0, 12.5, 3.2); return __route(1, [[55.0, 17.0]], 3); });
  check('zone 2: the gallery rail keeps the player up', r.lo > 3.15, JSON.stringify(r));

  // ---- robots follow
  async function chase(zi, at, robots, secs, goal) {
    const list = await pg.evaluate(([zi, at, robots]) => {
      __place(zi, at[0], at[1], at[2]);
      IB.Game.player.protect = 1e9;
      const Z = IB.Game.level.zones[zi];
      return robots.map(([type, c, r]) => {
        const slot = __TEST__.spawnRobot(type, Z.ox + c + 0.5, Z.oz + r + 0.5);
        const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
        return [type, slot];
      });
    }, [zi, at, robots]);
    let best = 0, last = null, t = 0;
    while (t < secs) {
      last = await pg.evaluate(([list, zi]) => { __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot], p = IB.Game.player; return { on: r.on, x: +r.x.toFixed(2), y: +r.y.toFixed(2), z: +r.z.toFixed(2), d: +Math.hypot(r.x - p.x, r.z - p.z).toFixed(2) }; }, [list, zi]);
      t += 0.5; if (last.on && last.d < 4) best = Math.max(best, last.y);
      if (best > goal) break;
    }
    return { best, last, t };
  }
  let w = await chase(0, [37.0, 56.0, 1.2], [['crawler', 44, 75]], 60, 1.1);
  check('zone 1: a Crawler from the apron walks up the ramp into the hold to the player (< 4 m) within 60 s', w.best > 1.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(0, [70.0, 49.5, 3.6], [['crawler', 56, 70]], 70, 3.5);
  check('zone 1: a Crawler climbs the tower stair to the player on the terrace (< 4 m) within 70 s', w.best > 3.5, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [55.0, 12.5, 3.2], [['blader', 36, 22]], 70, 3.1);
  check('zone 2: a Blade Bot climbs the barracks stair to the player on the gallery (< 4 m) within 70 s', w.best > 3.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [57.0, 12.0, 3.2], [['crawler', 30, 30]], 70, 3.1);
  check('zone 2: a Crawler climbs onto the barracks gallery to the player (< 4 m) within 70 s', w.best > 3.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));

  // ---- wall, barrier, run and span pieces lie along their line of cells: the drawn vertices (outline shell left out)
  // inside each cell or block, in a height band, are long along the line and short across it
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, out = { checked: 0, bad: [] };
    function ext(zi, c0, r0, w, h, y0, y1) {
      const Z = L.zones[zi], e = [1e9, -1e9, 1e9, -1e9], x0 = Z.ox + c0 - 0.02, x1 = Z.ox + c0 + w + 0.02, z0 = Z.oz + r0 - 0.02, z1 = Z.oz + r0 + h + 0.02;   // paint stands a few mm proud of a wall's inside face
      Z.meshes.forEach(m => {
        const P = m.geometry.attributes.position.array, H = m.geometry.attributes.aHull ? m.geometry.attributes.aHull.array : null;
        for (let i = 0; i < P.length; i += 3) {
          if (H && (H[i] || H[i + 1] || H[i + 2])) continue;
          const x = P[i], y = P[i + 1], z = P[i + 2];
          if (y < y0 || y > y1 || x < x0 || x > x1 || z < z0 || z > z1) continue;
          e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z);
        }
      });
      return [e[1] - e[0], e[3] - e[2]];
    }
    function expect(tag, zi, c0, r0, w, h, y0, y1, alongX, minAlong, maxAcross) {
      const [ex, ez] = ext(zi, c0, r0, w, h, y0, y1), along = alongX ? ex : ez, across = alongX ? ez : ex;
      out.checked++;
      if (!(along >= minAlong && across <= maxAcross)) out.bad.push(tag + '@' + zi + ':' + c0 + ',' + r0 + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
    }
    const blocks = (G, ch) => { const seen = {}, res = []; for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) { if (G.at(c, r) !== ch || seen[c + ',' + r]) continue; let w = 0, h = 0; while (G.at(c + w, r) === ch) w++; while (G.at(c, r + h) === ch) h++; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen[(c + x) + ',' + (r + y)] = 1; res.push([c, r, w, h]); } return res; };
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, at = (c, r) => g.at(c, r), W = g.w - 1, H = g.h - 1;
      const gN = g.rows[0].indexOf('G'), gS = g.rows[H].indexOf('E');
      // the zone walls: T-wall panels long along the wall (0.3 m thick at their cap course, 3.4 - 3.65 m), the
      // barriers on zone 1's side walls over the runway long along the wall too (their hazard band, 0.5 - 1.0 m)
      for (let r = 1; r < H; r++) for (const c of [0, W]) {
        const bar = zi === 0 && r >= 2 && r <= 26;
        if (bar) expect('barrier', zi, c, r, 1, 1, 0.5, 1.0, false, 0.95, 0.35);
        else if (!(zi === 0 && (r === 1 || r === 27))) expect('twall-side', zi, c, r, 1, 1, 3.4, 3.65, false, 0.95, 0.45);
      }
      for (let c = 1; c < W; c++) {
        if (Math.abs(c - gN - 1) > 3) expect('twall-N', zi, c, 0, 1, 1, 3.4, 3.65, true, 0.95, 0.45);
        if (Math.abs(c - gS - 1) > 3) expect('twall-S', zi, c, H, 1, 1, 3.4, 3.65, true, 0.95, 0.45);
      }
      // runs of borrowed pieces: jersey barriers and sandbags (rotate 'run') along X on their rows
      for (let r = 1; r < H; r++) for (let c = 1; c < W; c++) {
        const ch = at(c, r);
        if ((ch === 'j' || ch === '=') && at(c - 1, r) === ch && at(c + 1, r) === ch) expect(ch === 'j' ? 'jersey' : 'sandbags', zi, c, r, 1, 1, 0.15, 0.6, true, 0.9, 0.9);
      }
      // spans: the taxiway signs [2, 1] along X; on the hangar layer the benches / racks along their blocks
      ['n', 'm', 'v'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => expect('sign', zi, c, r, w, h, 0.5, 1.0, true, 1.8, 0.45)));
      (g.layers || []).forEach(G => {
        ['q', '1', '2', '3'].forEach(ch => blocks(G, ch).forEach(([c, r, w, h]) => expect('bench/rack ' + ch, zi, c, r, w, h, 0.3, 1.2, w > h, Math.max(w, h) - 0.3, 0.95)));
      });
    });
    return out;
  });
  check('wall, barrier, run and span pieces lie along their line of cells (none a quarter turn off)', runs.checked > 400 && runs.bad.length === 0, runs.checked + ' checked ' + runs.bad.slice(0, 16).join(' | '));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
