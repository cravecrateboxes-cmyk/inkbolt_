// INKBOLT Pelagic Airbase (plan 'pelagic'): the walk through both zones and the climbs. The player walks the flight
// deck from the operations block door past the ordnance carts and the flight line to the blast-fence gate, the trail,
// the hangar deck between the hangars to the exit gate and the hatch (no invisible walls, nothing blocks the way);
// climbs both stairs onto the helicopter dock (2.4 m), the island stair onto its gallery (3.6 m), into each hangar and
// up its mezzanine stair (3.0 m), and the approach-control tower stair onto its balcony (3.6 m); the rails and the
// zone bounds keep the player up there. Ground robots follow onto the dock, the island gallery, a mezzanine and the
// tower balcony. Run, rail, wall and span pieces are checked numerically to lie along their line of cells. The render
// loop is paused and the real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/pelagic-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=pelagic');
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
    // every gate open (the zones count as cleared for the walk)
    IB.Game.level.zones.forEach(z => { IB.Zones.setGate(z.exitGate, true, true); if (z.entryGate) IB.Zones.setGate(z.entryGate, true, true); });
  });
  // nav: open cells on the dock (2.4), the island gallery (3.6) in zone 1; the mezzanines (3.0) and the tower balcony
  // (3.6) in zone 2
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, h24: 0, h30: 0, h36: 0 };
    for (let k = 0; k < NC * (N.layers || 1); k++) if (!N.blocked[k] && N.h) {
      const h = N.h[k];
      if (Math.abs(h - 2.4) < 0.01) o.h24++; if (Math.abs(h - 3.0) < 0.01) o.h30++; if (Math.abs(h - 3.6) < 0.01) o.h36++;
    }
    return o;
  }));
  check('nav: zone 1 has open cells on the helicopter dock and the island gallery, zone 2 on the mezzanines and the tower balcony',
    nav[0].h24 > 500 && nav[0].h36 > 150 && nav[1].h30 > 150 && nav[1].h36 > 120, JSON.stringify(nav));

  // ---- the walk: ops block door -> apron -> blast-fence gate -> trail -> between the hangars -> exit gate -> hatch
  let r = await pg.evaluate(() => { __place(0, 24.5, 72.5, 0); return __route(0, [[23.0, 66.0], [23.0, 28.0], [25.5, 8.0], [25.5, 2.0], [25.5, -6.0], [25.5, -13.0]], 120); });
  check('walk zone 1: from the operations block door across the apron through the blast-fence gate onto the trail', r.reached === r.of && r.stuck === 0, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[37.5, 74.0], [37.5, 62.0], [31.5, 61.0], [31.5, 2.0], [31.5, -4.0], [31.5, -20.0]], 140));
  check('walk zone 2: the hangar deck between the hangars to the exit gate and the exit path', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit path leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));

  // ---- zone 1: the helicopter dock (both stairs), the island gallery
  r = await pg.evaluate(() => { __place(0, 8.0, 25.0, 0); return __route(0, [[8.0, 17.2], [3.0, 17.2]], 30); });
  check('zone 1: up the south stair onto the helicopter dock (2.4 m)', r.reached === 2 && Math.abs(r.y - 2.4) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 23.8, 10.0, 0); return __route(0, [[16.5, 10.0], [14.5, 10.0]], 30); });
  check('zone 1: up the east stair onto the helicopter dock (2.4 m)', r.reached === 2 && Math.abs(r.y - 2.4) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 3.0, 16.5, 2.4); return __route(0, [[3.0, 20.0]], 3); });
  check('zone 1: the dock rail keeps the player on the deck', r.lo > 2.35, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 39.5, 30.0, 0); return __route(0, [[42.0, 30.0], [42.0, 41.6], [42.0, 43.0], [49.0, 43.0], [49.6, 30.0]], 60); });
  check('zone 1: up the island stair onto the gallery (3.6 m) and round to the runway side', r.reached === r.of && Math.abs(r.y - 3.6) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 49.6, 30.0, 3.6); return __route(0, [[53.0, 30.0]], 3); });
  check('zone 1: the gallery rail keeps the player up', r.lo > 3.55, JSON.stringify(r));

  // ---- zone 2: into each hangar and up the mezzanine stair; the approach-control tower balcony
  r = await pg.evaluate(() => { __place(1, 10.5, 25.0, 0); return __route(1, [[10.5, 15.6], [10.0, 15.2], [10.0, 7.2], [6.0, 5.0]], 40); });
  check('zone 2: into hangar 1 and up its stair onto the mezzanine (3.0 m)', r.reached === r.of && Math.abs(r.y - 3.0) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 6.0, 5.5, 3.0); return __route(1, [[6.0, 9.0]], 3); });
  check('zone 2: the mezzanine rail keeps the player up', r.lo > 2.95, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 53.5, 25.0, 0); return __route(1, [[53.5, 15.6], [54.0, 15.2], [54.0, 7.2], [58.0, 5.0]], 40); });
  check('zone 2: into hangar 2 and up its stair onto the mezzanine (3.0 m)', r.reached === r.of && Math.abs(r.y - 3.0) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 54.0, 44.5, 0); return __route(1, [[54.0, 47.2], [54.0, 56.8], [56.0, 57.4], [59.5, 57.4], [59.5, 53.0]], 40); });
  check('zone 2: up the tower stair onto the balcony (3.6 m)', r.reached === r.of && Math.abs(r.y - 3.6) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 60.0, 54.0, 3.6); return __route(1, [[63.5, 54.0]], 3); });
  check('zone 2: the balcony rail keeps the player up', r.lo > 3.55, JSON.stringify(r));

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
  let w = await chase(0, [3.0, 15.0, 2.4], [['crawler', 20, 26]], 60, 2.3);
  check('zone 1: a Crawler from the apron climbs onto the helicopter dock to the player (< 4 m) within 60 s', w.best > 2.3, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(0, [49.6, 30.0, 3.6], [['crawler', 30, 46]], 70, 3.5);
  check('zone 1: a Crawler climbs the island stair to the player on the gallery (< 4 m) within 70 s', w.best > 3.5, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [6.0, 5.0, 3.0], [['blader', 20, 44]], 70, 2.9);
  check('zone 2: a Blade Bot climbs the hangar 1 mezzanine stair to the player (< 4 m) within 70 s', w.best > 2.9, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [59.5, 53.0, 3.6], [['crawler', 40, 44]], 70, 3.5);
  check('zone 2: a Crawler climbs the tower stair to the player on the balcony (< 4 m) within 70 s', w.best > 3.5, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));

  // ---- run / rail / span / wall pieces lie along their line of cells: the drawn vertices (outline shell left out)
  // inside each cell or block, in a height band, are long along the line and short across it
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, out = { checked: 0, bad: [] };
    function ext(zi, c0, r0, w, h, y0, y1) {
      const Z = L.zones[zi], e = [1e9, -1e9, 1e9, -1e9], x0 = Z.ox + c0, x1 = Z.ox + c0 + w, z0 = Z.oz + r0, z1 = Z.oz + r0 + h;
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
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, at = (c, r) => g.at(c, r), W = g.w - 1, H = g.h - 1;
      // the zone walls: deck-edge railings (with their net), blast fences, the barricade -- long along the wall
      for (let r = 3; r < H - 2; r++) {
        expect('edge-W', zi, 0, r, 1, 1, 0.3, 1.0, false, 0.9, 0.45);
        if (zi === 0) expect('edge-E', zi, W, r, 1, 1, 0.3, 1.0, false, 0.9, 0.45);
        else if (!(r >= 44 && r <= 46)) expect('fence-E', zi, W, r, 1, 1, 2.6, 3.5, false, 0.9, 0.6);
      }
      for (let c = 3; c < W - 2; c++) {
        const gN = g.rows[0].indexOf('G'), gS = g.rows[H].indexOf('E');
        if (Math.abs(c - gN - 1) > 3) expect(zi === 0 && c >= 52 ? 'barricade-N' : 'fence-N', zi, c, 0, 1, 1, 2.6, 3.5, true, 0.9, zi === 0 && c >= 52 ? 0.8 : 0.6);
        if (zi === 1 && Math.abs(c - gS - 1) > 3) expect('fence-S', zi, c, H, 1, 1, 2.6, 3.5, true, 0.9, 0.6);
        if (zi === 0 && c >= 52 && c < W) expect('fence-S', zi, c, H, 1, 1, 2.6, 3.5, true, 0.9, 0.6);
      }
      // arresting wires: along X across the runway
      for (let r = 1; r < H; r++) for (let c = 1; c < W; c++) if (at(c, r) === 'w' && at(c - 1, r) === 'w' && at(c + 1, r) === 'w') expect('wire', zi, c, r, 1, 1, 0.05, 0.2, true, 0.95, 0.2);
      // link runs on every grid (rails on the decks, the fuel line, the bund kerb): straight cells along their run
      [g].concat(g.layers || []).forEach(G => {
        const y = G === g ? 0 : G.y, ga = (c, r) => G.at(c, r);
        for (let r = 1; r < H; r++) for (let c = 1; c < W; c++) {
          const ch = ga(c, r); if (!'r~-'.includes(ch)) continue;
          const ew = ga(c - 1, r) === ch && ga(c + 1, r) === ch && ga(c, r - 1) !== ch && ga(c, r + 1) !== ch;
          const ns = ga(c, r - 1) === ch && ga(c, r + 1) === ch && ga(c - 1, r) !== ch && ga(c + 1, r) !== ch;
          if (!ew && !ns) continue;
          const band = ch === 'r' ? [y + 0.3, y + 1.1] : [y - 0.01, y + 0.5];
          expect(ch === 'r' ? 'rail' : ch === '~' ? 'fuel' : 'bund', zi, c, r, 1, 1, band[0], band[1], ew, 0.9, 0.7);
        }
      });
      // spans: the turned dock stair [6, 2] along X, the blast deflectors [8, 2] along X, benches / shelving along X
      const blocks = (G, ch) => { const seen = {}, res = []; for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) { if (G.at(c, r) !== ch || seen[c + ',' + r]) continue; let w = 0, h = 0; while (G.at(c + w, r) === ch) w++; while (G.at(c, r + h) === ch) h++; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen[(c + x) + ',' + (r + y)] = 1; res.push([c, r, w, h]); } return res; };
      blocks(g, 'U').forEach(([c, r, w, h]) => expect('stair-U', zi, c, r, w, h, 0.5, 2.0, true, 3.5, 2.0));
      blocks(g, 'D').forEach(([c, r, w, h]) => expect('jbd', zi, c, r, w, h, 0.3, 2.5, true, 7.5, 1.9));
      (g.layers || []).forEach(G => { blocks(G, 'z').forEach(([c, r, w, h]) => expect('bench', zi, c, r, w, h, 0.3, 1.5, true, 1.8, 0.85)); blocks(G, 'Q').forEach(([c, r, w, h]) => expect('shelf', zi, c, r, w, h, 0.3, 2.0, true, 2.8, 0.65)); });
    });
    return out;
  });
  check('run, rail, span and wall pieces lie along their line of cells (none a quarter turn off)', runs.checked > 400 && runs.bad.length === 0, runs.checked + ' checked ' + runs.bad.slice(0, 16).join(' | '));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
