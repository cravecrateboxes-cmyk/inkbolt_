// INKBOLT Glimmerdeep Colliery (plan 'gemmine'): the walkable decks. Both zones get a layered nav grid with open
// nodes on the raised conveyor catwalk (3 m, zone 1) and on the galleries (4.8 m), platforms / heart scaffold (2.4 m)
// and ledges (1.4 m) of the cavern; the player walks up the catwalk's west stair and the west gallery's south stair,
// the rails hold the player on the decks, and a Crawler from across the cavern climbs to the player on the gallery.
// The run pieces lie along their runs (rails, vent duct, lamp strings, conveyor): rays down onto each run cell hit the
// two rails / the duct / the bulb line where they belong. The render loop is paused and the real Player / AI code is
// stepped at a fixed 1/60 s (SwiftShader renders far slower than real time).
// Run (after tools/build.py): node tests/e2e/gemmine-decks.spec.js
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
  await pg.goto(base + '?autotest=1&plan=gemmine');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
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
  // ---- nav: open nodes at the deck heights
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, at = {};
    if (!N.layers) return { layers: 1 };
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k] && N.h[k] > 1.2) { const h = N.h[k].toFixed(1); at[h] = (at[h] || 0) + 1; }
    return { layers: N.layers, at };
  }));
  check('zone 1 has a layered nav with the catwalk deck at 3 m', nav[0].layers > 1 && (nav[0].at['3.0'] || 0) > 40, JSON.stringify(nav[0]));
  const z2 = nav[1].at || {};
  check('zone 2 has a layered nav with the galleries (4.8 m), platforms / scaffold (2.4 m) and ledges (1.4 m)',
    nav[1].layers > 1 && (z2['4.8'] || 0) > 100 && (z2['2.4'] || 0) > 80 && (z2['1.4'] || 0) > 80, JSON.stringify(z2));
  // every raised nav node (a deck, a stair step) is connected to the ground: a BFS over the layered nav (neighbours
  // within the 0.4 m step) from the zone's entry reaches them, so robots path everywhere the player can climb
  const reach = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, seen = new Uint8Array(NC * N.layers), q = [];
    const c0 = IB.Zones.navCell(z, z.entry.x, z.entry.z - 3);
    for (let L = 0; L < N.layers; L++) { const n = L * NC + c0; if (!N.blocked[n] && N.h[n] < 0.2) { seen[n] = 1; q.push(n); } }
    while (q.length) {
      const n = q.pop(), c = n % NC, i = c % N.nx, j = (c - i) / N.nx;
      [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([a, b]) => {
        const ii = i + a, jj = j + b; if (ii < 0 || jj < 0 || ii >= N.nx || jj >= N.nz) return;
        for (let L = 0; L < N.layers; L++) {
          const m = L * NC + jj * N.nx + ii;
          if (!seen[m] && !N.blocked[m] && Math.abs(N.h[m] - N.h[n]) <= 0.4) { seen[m] = 1; q.push(m); }
        }
      });
    }
    let up = 0, upSeen = 0, ground = 0, groundSeen = 0, eg = [];
    for (let k = 0; k < NC * N.layers; k++) {
      if (N.blocked[k]) continue;
      if (N.h[k] > 1.2) { up++; if (seen[k]) upSeen++; else if (eg.length < 4) { const c = k % NC; eg.push([(c % N.nx) * 0.5 + z.ox - z.ox, Math.floor(c / N.nx) * 0.5, +N.h[k].toFixed(2)]); } }
      else { ground++; if (seen[k]) groundSeen++; }
    }
    return { up, upSeen, ground, groundSeen, eg };
  }));
  reach.forEach((R, zi) => check('zone ' + (zi + 1) + ': raised nav nodes are reached from the entry over stairs and ramps (>= 97%)',
    R.up > 0 && R.upSeen >= 0.97 * R.up && R.groundSeen >= 0.97 * R.ground, JSON.stringify(R)));
  // ---- zone 1: up the catwalk's west stair (x 45 .. 49.5 along row 8 / 9) onto the deck, along it, the rails hold
  let r = await pg.evaluate(() => { __place(0, 44.4, 9.1, 0); return __route(0, [[45.3, 9.1], [49.9, 9.1], [55.0, 9.1], [59.0, 9.1]], 25); });
  check('the player walks up the catwalk stair and along the 3 m deck', r.reached === 4 && Math.abs(r.y - 3.0) < 0.05, JSON.stringify(r));
  for (const [name, g] of [['front rail', [55.0, 11.5]], ['belt rail', [55.0, 6.5]]]) {
    r = await pg.evaluate(([g]) => { __place(0, 55.0, 9.1, 3.0); return __route(0, [g], 3); }, [g]);
    check('the catwalk ' + name + ' keeps the player on the deck', r.lo > 2.95, JSON.stringify(r));
  }
  // ---- zone 2: up the west gallery's south stair (x 3 .. 5, rising north from row 40 to row 33) onto the 4.8 m deck
  r = await pg.evaluate(() => { __place(1, 4.0, 41.2, 0); return __route(1, [[4.0, 40.2], [4.0, 33.4], [4.0, 32.0], [2.0, 32.0], [2.0, 25.0]], 30); });
  check('the player walks up the gallery stair onto the 4.8 m deck and along it', r.reached === 5 && Math.abs(r.y - 4.8) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 2.0, 28.0, 4.8); return __route(1, [[6.5, 28.0]], 3); });
  check('the gallery rail (over the stair) keeps the player on the deck', r.lo > 4.75, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 4.0, 32.0, 4.8); return __route(1, [[7.0, 32.0]], 3); });
  check('the landing rail keeps the player on the deck', r.lo > 4.75, JSON.stringify(r));
  // ---- a Crawler from across the cavern climbs to the player on the gallery deck
  const list = await pg.evaluate(() => {
    __place(1, 2.0, 30.0, 4.8);
    const Z = IB.Game.level.zones[1];
    const slot = __TEST__.spawnRobot('crawler', Z.ox + 24.5, Z.oz + 40.5);
    const rb = IB.AI.types.crawler.slots[slot]; rb.state = IB.AI.VIS.crawler.home; rb.st = 0; rb.thinkT = 0; rb.zone = 1;
    return slot;
  });
  let best = 0, last = null, t = 0;
  while (t < 70) {
    last = await pg.evaluate((slot) => { __sim(0.5, 1); const rb = IB.AI.types.crawler.slots[slot]; return { on: rb.on, x: +rb.x.toFixed(2), y: +rb.y.toFixed(2), z: +rb.z.toFixed(2) }; }, list);
    t += 0.5; best = Math.max(best, last.on ? last.y : 0);
    if (best > 4.7) break;
  }
  check('a Crawler climbs a gallery stair to the player on the 4.8 m deck within 70 s', best > 4.7, 'max y ' + best.toFixed(2) + ' in ' + t + ' s ' + JSON.stringify(last));
  // ---- run pieces lie along their runs: rays straight down onto each run cell
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, ray = new THREE.Raycaster(), out = {};
    const meshes = []; L.root.traverse(o => { if (o.isMesh) meshes.push(o); });
    function hitY(x, z, y0) { ray.set(new THREE.Vector3(x, y0, z), new THREE.Vector3(0, -1, 0)); ray.far = y0 + 1; const h = ray.intersectObjects(meshes, false); return h.length ? h[0].point.y : null; }
    function scan(zi, li, ch, test) {
      const Z = L.zones[zi], G = Z.grid.layers[li]; let n = 0, bad = [];
      for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) {
        if (G.at(c, r) !== ch) continue;
        const vert = G.at(c, r - 1) === ch || G.at(c, r + 1) === ch, horiz = G.at(c - 1, r) === ch || G.at(c + 1, r) === ch;
        if (vert === horiz) continue;   // ends of crossing runs: no run direction to check
        n++;
        if (!test(Z.ox + c + 0.5, Z.oz + r + 0.5, vert)) bad.push(c + ',' + r);
      }
      return { n, bad: bad.length, eg: bad.slice(0, 4) };
    }
    // rails: across the run at +-0.3 the rail heads (0.15), between them the sleepers / ballast (lower)
    out.rails1 = scan(0, 0, '-', (x, z, v) => { const a = v ? hitY(x - 0.3, z + 0.12, 1) : hitY(x + 0.12, z - 0.3, 1), m = v ? hitY(x, z + 0.12, 1) : hitY(x + 0.12, z, 1); return a !== null && a > 0.13 && (m === null || m < 0.1); });
    out.rails2 = scan(1, 0, '-', (x, z, v) => { const a = v ? hitY(x - 0.3, z + 0.12, 1) : hitY(x + 0.12, z - 0.3, 1), m = v ? hitY(x, z + 0.12, 1) : hitY(x + 0.12, z, 1); return a !== null && a > 0.13 && (m === null || m < 0.1); });
    // vent duct (a tube along its run, open ends, axis at 8.1 m): a level ray across the run from 1.2 m out meets the
    // tube's side about 0.84 m on; a duct turned across its run would show the ray its open end and no wall in reach
    out.duct = scan(0, 1, 'v', (x, z, v) => {
      const o = v ? new THREE.Vector3(x - 1.2, 8.1, z + 0.2) : new THREE.Vector3(x + 0.2, 8.1, z - 1.2), d = v ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
      ray.set(o, d); ray.far = 1.2; const h = ray.intersectObjects(meshes, false);
      return h.length > 0 && h[0].distance > 0.72 && h[0].distance < 0.95;
    });
    return out;
  });
  for (const k of Object.keys(runs)) check('run pieces along their runs: ' + k, runs[k].n > 10 && runs[k].bad === 0, JSON.stringify(runs[k]));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
