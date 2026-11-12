// INKBOLT Grand Hotel Riviera (plan 'riviera'): the walk through both zones and the climbs. The player walks the
// ground floor from the front doors along the runner, round the Imperial Staircase, through the palm court to the
// garden doors and the orangery passage, then the pool terrace to the north wing and the exit passage to the hatch
// (the routes are found by a search over the zone plan's open cells, so they also prove nothing blocks the way); climbs
// the Imperial Staircase (the central flight, the landing at 2.16 m, a side flight to the top landing at 4.5 m), crosses
// a bridge to the gallery and walks round its three arms and back over the other bridge; climbs both stairs of the spa
// podium onto the roof garden (4.5 m) and down again; wades into the infinity pool and the spa pool. The balustrades and
// the parapet keep the player up. Ground robots follow the player onto the gallery, onto the roof garden and into the
// pool. Run, rail and span pieces are checked numerically to lie along their line of cells. The render loop is paused and
// the real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/riviera-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=riviera');
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
    // a 4-connected path over the plan's open floor cells (their four neighbours open too), cell centres
    window.__path = (zi, from, to) => {
      const g = IB.Game.level.zones[zi].grid, W = g.w, H = g.h, OPEN = '.PahEGn';
      const free = (c, r) => [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]].every(([dc, dr]) => OPEN.indexOf(g.at(c + dc, r + dr)) >= 0);
      const key = (c, r) => r * W + c, prev = new Int32Array(W * H).fill(-2), q = [key(from[0], from[1])];
      prev[q[0]] = -1;
      while (q.length) {
        const k = q.shift(), c = k % W, r = (k - c) / W;
        if (c === to[0] && r === to[1]) break;
        [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dc, dr]) => { const c2 = c + dc, r2 = r + dr; if (c2 < 0 || r2 < 0 || c2 >= W || r2 >= H) return; const k2 = key(c2, r2); if (prev[k2] !== -2 || !(free(c2, r2) || (c2 === to[0] && r2 === to[1]))) return; prev[k2] = k; q.push(k2); });
      }
      const out = []; let k = key(to[0], to[1]);
      if (prev[k] === -2) return null;
      while (k >= 0) { const c = k % W; out.unshift([c + 0.5, (k - c) / W + 0.5]); k = prev[k]; }
      return out;
    };
    window.__place = (zi, x, z, y) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      p.protect = 0; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y; p.vx = p.vz = p.vy = 0;
    };
    IB.Game.level.zones.forEach(z => { IB.Zones.setGate(z.exitGate, true, true); if (z.entryGate) IB.Zones.setGate(z.entryGate, true, true); });
  });
  // nav: open cells on the gallery and the stair's top landings (4.5) in zone 1, on the roof garden (4.5) in zone 2
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, h45: 0, land: 0 };
    for (let k = 0; k < NC * (N.layers || 1); k++) if (!N.blocked[k] && N.h) {
      const h = N.h[k];
      if (Math.abs(h - 4.5) < 0.02) o.h45++; if (Math.abs(h - 2.16) < 0.02) o.land++;
    }
    return o;
  }));
  check('nav: zone 1 has open cells on the gallery and the stair landing, zone 2 on the roof garden', nav[0].h45 > 800 && nav[0].land > 60 && nav[1].h45 > 2000, JSON.stringify(nav));

  // ---- the walk: front doors -> lobby -> round the staircase -> palm court -> garden doors -> passage -> terrace ->
  // north wing -> exit passage -> hatch
  let r = await pg.evaluate(() => { __place(0, 36.5, 61.5, 0); const P = __path(0, [36, 61], [36, 1]); return P ? __route(0, P.concat([[36.5, -6.0], [36.5, -11.5]]), 200) : { none: true }; });
  check('walk zone 1: from the front doors through the lobby, round the staircase, through the palm court to the garden doors and the passage', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  r = await pg.evaluate(() => { const P = __path(1, [36, 66], [31, 1]); return P ? __route(1, [[36.5, 69.0]].concat(P, [[31.5, -4.0], [31.5, -20.0]]), 200) : { none: true }; });
  check('walk zone 2: across the pool terrace past the pools, the bar and the podium to the north wing and the exit passage', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit passage leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));

  // ---- zone 1: up the Imperial Staircase, over the west bridge, round the gallery, back over the east bridge
  r = await pg.evaluate(() => { __place(0, 36.5, 38.5, 0); return __route(0, [[36.5, 29.0]], 20); });
  check('zone 1: up the central flight onto the landing (2.16 m)', r.reached === r.of && Math.abs(r.y - 2.16) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(0, [[31.5, 29.0], [31.5, 35.0], [27.5, 35.0], [24.4, 35.0], [24.4, 25.4], [36.5, 25.4], [49.5, 25.4], [49.5, 35.0], [44.5, 35.0], [41.5, 35.0]], 120));
  check('zone 1: up a side flight to the top landing (4.5 m), the west bridge, round the gallery\'s three arms, back over the east bridge', r.reached === r.of && Math.abs(r.y - 4.5) < 0.05 && r.lo > 2.1, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 23.5, 42.0, 4.5); return __route(0, [[29.0, 42.0]], 3); });
  check('zone 1: the gallery\'s balustrade keeps the player up', r.lo > 4.45, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 36.5, 24.5, 4.5); return __route(0, [[36.5, 29.5]], 3); });
  check('zone 1: the north arm\'s balustrade over the landing keeps the player up', r.lo > 4.45, JSON.stringify(r));

  // ---- zone 2: up the west stair onto the roof garden, across it, down the south stair; the parapet
  r = await pg.evaluate(() => { __place(1, 49.0, 19.5, 0); return __route(1, [[51.5, 19.5], [61.5, 19.5], [62.5, 22.0], [62.5, 24.6], [60.5, 25.0], [60.5, 35.5], [65.5, 35.5], [65.5, 36.5]], 60); });
  check('zone 2: up the west stair into the roof garden (4.5 m) and across it to the head of the south stair', r.reached === r.of && Math.abs(r.y - 4.5) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[65.5, 40.0], [65.5, 46.5]], 30));
  check('zone 2: down the south stair to the terrace', r.reached === r.of && r.y < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 56.0, 30.0, 4.5); return __route(1, [[49.0, 30.0]], 3); });
  check('zone 2: the roof garden\'s parapet keeps the player up', r.lo > 4.45, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 60.0, 47.0, 0); return __route(1, [[60.0, 43.5]], 3); });
  check('zone 2: the podium\'s front is solid (no walking into the spa)', r.z > 44.4, JSON.stringify(r));

  // ---- zone 2: wading into the infinity pool and the spa pool, out again
  r = await pg.evaluate(() => { __place(1, 16.5, 28.5, 0); return __route(1, [[13.5, 28.5], [6.0, 28.5], [2.0, 28.5], [13.5, 28.5], [17.0, 28.5]], 30); });
  check('zone 2: over the coping into the infinity pool to its vanishing edge and out again', r.reached === r.of && r.lo < 0.05 && r.hi < 0.6, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 28.0, 8.0, 0); return __route(1, [[28.0, 10.5], [28.0, 13.0], [28.0, 8.0]], 20); });
  check('zone 2: into the spa pool and out again', r.reached === r.of && r.lo < 0.05, JSON.stringify(r));

  // ---- robots follow
  async function chase(zi, at, robots, secs, goal, near) {
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
    let best = -1, last = null, t = 0, close = 99;
    while (t < secs) {
      last = await pg.evaluate(([list, zi]) => { __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot], p = IB.Game.player; return { on: r.on, x: +(r.x - IB.Game.level.zones[zi].ox).toFixed(2), y: +r.y.toFixed(2), z: +(r.z - IB.Game.level.zones[zi].oz).toFixed(2), d: +Math.hypot(r.x - p.x, r.z - p.z).toFixed(2) }; }, [list, zi]);
      t += 0.5; if (last.on && last.d < (near || 4)) { best = Math.max(best, last.y); close = Math.min(close, last.d); }
      if (best > goal) break;
    }
    return { best, last, t, close };
  }
  let w = await chase(0, [23.5, 45.0, 4.5], [['crawler', 36, 52]], 80, 4.4);
  check('zone 1: a Crawler from the lobby climbs the Imperial Staircase to the player on the gallery (< 4 m) within 80 s', w.best > 4.4, JSON.stringify(w));
  w = await chase(1, [62.0, 10.0, 4.5], [['crawler', 40, 40]], 80, 4.4);
  check('zone 2: a Crawler from the terrace climbs to the player in the roof garden (< 4 m) within 80 s', w.best > 4.4, JSON.stringify(w));
  w = await chase(1, [70.0, 30.0, 4.5], [['blader', 66, 56]], 80, 4.4);
  check('zone 2: a Blade Bot from the lawn garden climbs the south stair to the player in the roof garden within 80 s', w.best > 4.4, JSON.stringify(w));
  w = await chase(1, [5.0, 30.0, 0], [['crawler', 30, 44]], 60, -0.5, 2.5);
  check('zone 2: a Crawler wades into the infinity pool to the player (< 2.5 m) within 60 s', w.close < 2.5, JSON.stringify(w));

  // ---- run / rail / span pieces lie along their line of cells: the drawn vertices (outline shell left out) inside
  // each cell or block, in a height band, are long along the line and short across it
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, out = { checked: 0, bad: [] };
    function ext(zi, c0, r0, w, h, y0, y1, alongX) {
      const Z = L.zones[zi], e = [1e9, -1e9, 1e9, -1e9], x0 = Z.ox + c0, x1 = Z.ox + c0 + w, z0 = Z.oz + r0, z1 = Z.oz + r0 + h;
      Z.meshes.forEach(m => {
        const P = m.geometry.attributes.position.array, H = m.geometry.attributes.aHull ? m.geometry.attributes.aHull.array : null;
        for (let i = 0; i < P.length; i += 3) {
          if (H && (H[i] || H[i + 1] || H[i + 2])) continue;
          const x = P[i], y = P[i + 1], z = P[i + 2];
          if (y < y0 || y > y1 || x < x0 || x > x1 || z < z0 || z > z1) continue;
          const a = alongX ? x : z, end = Math.min(Math.abs(a - (alongX ? x0 : z0)), Math.abs(a - (alongX ? x1 : z1))) < 0.005;
          if (alongX) { e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); if (!end) { e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z); } }
          else { e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z); if (!end) { e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); } }
        }
      });
      return [Math.max(0, e[1] - e[0]), Math.max(0, e[3] - e[2])];
    }
    function expect(tag, zi, c0, r0, w, h, y0, y1, alongX, minAlong, maxAcross) {
      const [ex, ez] = ext(zi, c0, r0, w, h, y0, y1, alongX), along = alongX ? ex : ez, across = alongX ? ez : ex;
      out.checked++;
      if (!(along >= minAlong && across <= maxAcross)) out.bad.push(tag + '@' + zi + ':' + c0 + ',' + r0 + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
    }
    const blocks = (G, ch) => { const seen = {}, res = []; for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) { if (G.at(c, r) !== ch || seen[c + ',' + r]) continue; let w = 0, h = 0; while (G.at(c + w, r) === ch) w++; while (G.at(c, r + h) === ch) h++; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen[(c + x) + ',' + (r + y)] = 1; res.push([c, r, w, h]); } return res; };
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, W = g.w - 1, H = g.h - 1;
      // the gallery's balustrades (layer 4.5): straight cells along their run (rail 0.94-1.03 m over the deck)
      (g.layers || []).forEach(G => {
        for (let r = 1; r < H; r++) for (let c = 1; c < W; c++) {
          if (G.at(c, r) !== 'r') continue;
          const lk = (cc, rr) => 'ri'.indexOf(G.at(cc, rr)) >= 0;
          const ew = lk(c - 1, r) && lk(c + 1, r) && !lk(c, r - 1) && !lk(c, r + 1), ns = lk(c, r - 1) && lk(c, r + 1) && !lk(c - 1, r) && !lk(c + 1, r);
          if (ew || ns) expect('rail', zi, c, r, 1, 1, G.y + 0.94, G.y + 1.04, ew, 0.95, 0.2);
        }
      });
      // spans: chair rows (seats), planters, coffee stations, banquettes, the wine wall, the pass, the roof stairs
      blocks(g, 'Y').forEach(([c, r, w, h]) => expect('chairs', zi, c, r, w, h, 0.4, 0.52, true, 5.3, 0.5));
      blocks(g, '{').forEach(([c, r, w, h]) => expect('planter', zi, c, r, w, h, 0.3, 0.6, w > h, 2.4, 0.85));
      blocks(g, 'C').forEach(([c, r, w, h]) => expect('coffee', zi, c, r, w, h, 0.75, 0.8, w > h, 3.8, 0.75));
      blocks(g, 'q').forEach(([c, r, w, h]) => expect('banquette', zi, c, r, w, h, 1.26, 1.33, w > h, 3.8, 0.25));
      blocks(g, 'V').forEach(([c, r, w, h]) => expect('winewall', zi, c, r, w, h, 1.5, 2.5, w > h, 2.6, 0.45));
      blocks(g, 'Z').forEach(([c, r, w, h]) => expect('pass', zi, c, r, w, h, 0.9, 1.0, w > h, 3.8, 0.75));
      blocks(g, '?').forEach(([c, r, w, h]) => expect('roofstair', zi, c, r, w, h, -0.01, 4.6, w > h, 7.9, 4.0));
    });
    return out;
  });
  check('run, rail and span pieces lie along their line of cells (none a quarter turn off)', runs.checked > 90 && runs.bad.length === 0, runs.checked + ' checked ' + runs.bad.slice(0, 16).join(' | '));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
