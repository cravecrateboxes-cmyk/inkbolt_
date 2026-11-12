// INKBOLT Ca' Doranza (plan 'venetian'): the walk through both zones and the climbs. The player walks the campo from
// the lane portal past the stalls and the fountain to the bridge portal, over the bridge, through the courtyard (the
// cloister's south range, the garden, the north range) to the main portal, the exit lane and the hatch (no invisible
// walls, nothing blocks the way); climbs the stair inside Caffe Zanetto onto its roof terrace (3.6 m), the loggia's
// stair onto its terrace (3.6 m), the grand staircase onto the cloister's upper walk (4.32 m) and round all four
// ranges, both service stairs onto the walk; the balustrades keep the player up there. Ground robots follow onto the
// cafe terrace, the loggia terrace and the upper walk (by the grand staircase and by a service stair). Run, rail,
// span and wall pieces are checked numerically to lie along their line of cells. The render loop is paused and the
// real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/venetian-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=venetian');
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
  // nav: open cells on the cafe and loggia terraces (3.6) in zone 1, on the upper walk (4.32) in zone 2
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, h36: 0, h432: 0 };
    for (let k = 0; k < NC * (N.layers || 1); k++) if (!N.blocked[k] && N.h) {
      const h = N.h[k];
      if (Math.abs(h - 3.6) < 0.01) o.h36++; if (Math.abs(h - 4.32) < 0.01) o.h432++;
    }
    return o;
  }));
  check('nav: zone 1 has open cells on the cafe and loggia terraces, zone 2 on the cloister\'s upper walk', nav[0].h36 > 300 && nav[1].h432 > 600, JSON.stringify(nav));

  // ---- the walk: lane portal -> campo -> bridge portal -> bridge -> courtyard -> main portal -> lane -> hatch
  let r = await pg.evaluate(() => { __place(0, 19.5, 68.5, 0); return __route(0, [[19.5, 60.0], [19.5, 40.0], [27.5, 26.0], [27.5, 10.0], [37.5, 7.0], [37.5, 1.5], [37.5, -6.0], [37.5, -11.5]], 140); });
  check('walk zone 1: from the lane portal up the campo past the fountain to the bridge portal and over the bridge', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[33.5, 72.5], [33.5, 62.0], [28.5, 56.0], [28.5, 47.0], [28.5, 17.0], [33.5, 10.0], [33.5, 2.0], [33.5, -4.0], [33.5, -20.0]], 160));
  check('walk zone 2: the forecourt, under the cloister and across the garden, the north court, the main portal, the lane', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit lane leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));

  // ---- zone 1: into Caffe Zanetto and up its stair onto the roof terrace; the loggia's stair onto its terrace
  r = await pg.evaluate(() => { __place(0, 12.0, 15.0, 0); return __route(0, [[9.6, 15.0], [8.2, 15.0], [8.2, 19.15], [2.0, 19.15], [2.0, 16.0], [6.0, 13.0]], 50); });
  check('zone 1: into Caffe Zanetto and up its stair onto the roof terrace (3.6 m)', r.reached === r.of && Math.abs(r.y - 3.6) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 6.0, 14.0, 3.6); return __route(0, [[10.0, 14.0]], 3); });
  check('zone 1: the cafe terrace balustrade keeps the player up', r.lo > 3.55, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 64.5, 60.0, 0); return __route(0, [[64.5, 52.6], [63.3, 52.6], [62.4, 54.0], [55.0, 54.0]], 40); });
  check('zone 1: up the loggia\'s stair onto its roof terrace (3.6 m)', r.reached === r.of && Math.abs(r.y - 3.6) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 55.0, 54.0, 3.6); return __route(0, [[55.0, 59.5]], 3); });
  check('zone 1: the loggia balustrade keeps the player up', r.lo > 3.55, JSON.stringify(r));

  // ---- zone 2: the grand staircase onto the upper walk and round the four ranges; the service stairs
  r = await pg.evaluate(() => { __place(1, 33.0, 57.0, 0); return __route(1, [[33.0, 46.4], [33.0, 44.0], [17.0, 44.0], [17.0, 19.5], [49.5, 19.5], [49.5, 44.0], [36.0, 44.0]], 90); });
  check('zone 2: up the grand staircase onto the upper walk (4.32 m) and round all four ranges', r.reached === r.of && Math.abs(r.y - 4.32) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 17.0, 30.0, 4.32); return __route(1, [[12.5, 30.0]], 3); });
  check('zone 2: the walk\'s balustrade keeps the player up', r.lo > 4.27, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 59.5, 32.0, 0); return __route(1, [[52.2, 32.0], [50.0, 32.0]], 30); });
  check('zone 2: up the east service stair onto the walk', r.reached === r.of && Math.abs(r.y - 4.32) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 7.5, 32.0, 0); return __route(1, [[14.8, 32.0], [16.8, 32.0]], 30); });
  check('zone 2: up the west service stair onto the walk', r.reached === r.of && Math.abs(r.y - 4.32) < 0.05, JSON.stringify(r));

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
  let w = await chase(0, [5.0, 13.0, 3.6], [['crawler', 20, 30]], 70, 3.5);
  check('zone 1: a Crawler from the campo climbs the cafe stair to the player on the terrace (< 4 m) within 70 s', w.best > 3.5, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(0, [54.5, 54.0, 3.6], [['crawler', 44, 46]], 70, 3.5);
  check('zone 1: a Crawler climbs the loggia stair to the player on its terrace (< 4 m) within 70 s', w.best > 3.5, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [20.0, 44.0, 4.32], [['crawler', 33, 62]], 70, 4.2);
  check('zone 2: a Crawler from the forecourt climbs the grand staircase to the player on the walk (< 4 m) within 70 s', w.best > 4.2, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [49.5, 26.0, 4.32], [['blader', 60, 22]], 70, 4.2);
  check('zone 2: a Blade Bot from the service yard climbs to the player on the east range (< 4 m) within 70 s', w.best > 4.2, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));

  // ---- run / rail / span / wall pieces lie along their line of cells: the drawn vertices (outline shell left out)
  // inside each cell or block, in a height band, are long along the line and short across it
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, out = { checked: 0, bad: [] };
    // vertices on the box's two end planes (along the line) count for the length only: a neighbour's end face (a
    // quoin's side over a lower house) lies in that plane and must not count as depth
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
      // the zone walls: house fronts (a window band at 1.5-2.5 m or the plain front) and the quay balustrade
      for (let r = 4; r < H - 3; r++) {
        expect(zi === 1 ? 'garden-W' : 'house-W', zi, 0, r, 1, 1, 0.0, 0.55, false, 0.95, 0.4);
        expect('house-E', zi, W, r, 1, 1, 0.0, 0.55, false, 0.95, 0.4);
      }
      for (let c = 4; c < W - 3; c++) {
        const gN = g.rows[0].indexOf('G'), gS = g.rows[H].indexOf('E');
        if (Math.abs(c - gN - 1) > 3) expect(zi === 0 ? 'quay-N' : 'house-N', zi, c, 0, 1, 1, zi === 0 ? 0.3 : 0.0, zi === 0 ? 1.0 : 0.55, true, 0.95, zi === 0 ? 0.3 : 0.4);
        // (the canal wing in zone 2 is a whole cell deep: its court front and, behind, its canal face)
        if (Math.abs(c - gS - 1) > 3) expect('house-S', zi, c, H, 1, 1, 0.0, 0.55, true, 0.95, zi === 1 ? 1.0 : 0.4);
      }
      // link runs on every grid (balustrades on the terraces and the walk, hedges): straight cells along their run
      [g].concat(g.layers || []).forEach(G => {
        const y = G === g ? 0 : G.y, ga = (c, r) => G.at(c, r);
        for (let r = 1; r < H; r++) for (let c = 1; c < W; c++) {
          const ch = ga(c, r); if (!'rH'.includes(ch)) continue;
          const ew = ga(c - 1, r) === ch && ga(c + 1, r) === ch && ga(c, r - 1) !== ch && ga(c, r + 1) !== ch;
          const ns = ga(c, r - 1) === ch && ga(c, r + 1) === ch && ga(c - 1, r) !== ch && ga(c + 1, r) !== ch;
          if (!ew && !ns) continue;
          if ((g.layers || []).some(Lw => Lw.at(c, r) === 'W')) continue;   // under the roof loggia its columns stand beside the rail
          expect(ch === 'r' ? 'rail' : 'hedge', zi, c, r, 1, 1, y - 0.01, y + 1.05, ew, 0.95, ch === 'r' ? 0.3 : 0.7);
        }
        // the cloister arches: the spandrel (3.0-3.9 m) runs along its line between the two columns
        blocks(G, 'A').forEach(([c, r, w, h]) => expect('arch-A', zi, c, r, w, h, 3.0, 3.9, true, 1.9, 0.5));
        blocks(G, 'V').forEach(([c, r, w, h]) => expect('arch-V', zi, c, r, w, h, 3.0, 3.9, false, 1.9, 0.5));
      });
      // spans: benches and planters along their long side, the service stairs along their run
      blocks(g, 'i').forEach(([c, r, w, h]) => expect('stair-i', zi, c, r, w, h, -0.01, 5.5, true, 5.9, 2.1));
      blocks(g, 'j').forEach(([c, r, w, h]) => expect('stair-j', zi, c, r, w, h, -0.01, 5.5, true, 5.9, 2.1));
      blocks(g, 'p').forEach(([c, r, w, h]) => expect('planter', zi, c, r, w, h, 0.3, 0.9, w > h, 1.8, 0.75));
      blocks(g, 'B').forEach(([c, r, w, h]) => expect('bench', zi, c, r, w, h, 0.2, 0.5, w > h, 1.8, 0.55));
    });
    return out;
  });
  check('run, rail, span and wall pieces lie along their line of cells (none a quarter turn off)', runs.checked > 600 && runs.bad.length === 0, runs.checked + ' checked ' + runs.bad.slice(0, 16).join(' | '));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
