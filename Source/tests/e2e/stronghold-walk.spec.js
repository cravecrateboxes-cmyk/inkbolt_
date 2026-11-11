// INKBOLT Fort Highwatch (plan 'stronghold'): the player walks the outer works' switchbacks (ground -> 1.8 m landing ->
// terrace 1 at 3.6 m -> 5.4 m landing -> terrace 2 at 7.2 m) and the long ramp, is kept up by the terrace rails, climbs
// the steel stairs in the halls (hangar mezzanine, ops balcony, the terrace observation post), walks through a terrace
// doorway and along the trail tunnel from zone 1 into zone 2; ground robots climb the switchbacks and the stairs after
// the player. The render loop is paused and the real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/stronghold-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=stronghold');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
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
      return { reached: k, of: pts.length, lo: +lo.toFixed(2), hi: +hi.toFixed(2), x: +(p.x - Z.ox).toFixed(2), y: +p.y.toFixed(2), z: +(p.z - Z.oz).toFixed(2), hp: p.health };
    };
    window.__place = (zi, x, z, y) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      p.protect = 0; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y; p.vx = p.vz = p.vy = 0;
    };
  });
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, h = {};
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k]) { const y = Math.round(N.h[k] * 10) / 10; if (y > 0.5) h[y] = (h[y] || 0) + 1; }
    return { layers: N.layers, h };
  }));
  const at = (zi, y) => Object.keys(nav[zi].h).filter(k => Math.abs(k - y) < 0.06).reduce((a, k) => a + nav[zi].h[k], 0);
  check('zone 1 nav: open cells on terrace 1 (3.6), terrace 2 (7.2) and both landings (1.8, 5.4)', at(0, 3.6) > 600 && at(0, 7.2) > 300 && at(0, 1.8) > 20 && at(0, 5.4) > 20, JSON.stringify([at(0, 1.8), at(0, 3.6), at(0, 5.4), at(0, 7.2)]));
  check('zone 2 nav: open cells on the 2.4 m decks', at(1, 2.4) > 300, String(at(1, 2.4)));
  // zone 1: from the entry up switchback 1 onto terrace 1, then switchback 2 onto terrace 2
  let r = await pg.evaluate(() => { __place(0, 61.5, 61.5, 0); return __route(0, [[49.5, 32.0], [50.5, 30.0], [59.5, 30.0], [60.0, 28.0], [51.0, 28.0], [49.5, 27.5], [53.0, 24.0]], 60); });
  check('zone 1: the player climbs switchback 1 (east up to the landing, back west) onto terrace 1 (3.6 m)', r.reached === 7 && Math.abs(r.y - 3.6) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(0, [[52.5, 14.0], [61.5, 14.0], [62.0, 12.0], [53.0, 12.0], [51.5, 11.5], [51.5, 8.0]], 60));
  check('zone 1: the player climbs switchback 2 onto terrace 2 (7.2 m)', r.reached === 6 && Math.abs(r.y - 7.2) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __sim(2, 0); const p = IB.Game.player; return { y: +p.y.toFixed(3) }; });
  check('standing on terrace 2 holds', Math.abs(r.y - 7.2) < 0.01, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 67.0, 41.0, 0); return __route(0, [[67.0, 38.5], [67.0, 26.0], [67.0, 22.0]], 30); });
  check('zone 1: the player walks up the long ramp from the south onto terrace 1', r.reached === 3 && Math.abs(r.y - 3.6) < 0.05, JSON.stringify(r));
  for (const [nm, s, g, y] of [['terrace 1 west', [50.5, 18.0], [44.0, 18.0], 3.6], ['terrace 1 south', [64.0, 24.0], [64.0, 32.0], 3.6], ['terrace 2 south', [66.0, 8.0], [66.0, 14.0], 7.2], ['landing 1', [60.0, 29.0], [64.0, 29.0], 1.8]]) {
    r = await pg.evaluate(([s, g, y]) => { __place(0, s[0], s[1], y); return __route(0, [g], 3); }, [s, g, y]);
    check('zone 1: the ' + nm + ' rail keeps the player up', r.lo > y - 0.05, JSON.stringify(r));
  }
  // the trail: through the rock gate and the tunnel into zone 2 (gates open)
  r = await pg.evaluate(() => {
    const L = IB.Game.level; L.zones.forEach(z => { IB.Zones.setGate(z.exitGate, true, true); if (z.entryGate) IB.Zones.setGate(z.entryGate, true, true); });
    __place(0, 41.5, 4.0, 0); return __route(0, [[41.5, 1.0], [41.5, -12.0], [41.5, -18.0]], 30);
  });
  check('the trail: the player walks from zone 1 through the gate and the tunnel into zone 2', r.reached === 3 && Math.abs(r.y) < 0.05, JSON.stringify(r));
  // zone 2: the stairs and a terrace doorway
  for (const [nm, pts, y] of [['hangar mezzanine', [[67.0, 28.0], [67.0, 26.5], [67.0, 19.5], [69.5, 15.0]], 2.4], ['terrace observation post', [[7.0, 43.0], [7.0, 41.5], [7.0, 34.5], [6.0, 31.0]], 2.4],
    ['ops balcony', [[16.0, 17.0], [16.0, 18.5], [16.0, 25.5], [22.0, 27.0]], 2.4], ['north terrace doorway', [[10.0, 5.5], [13.0, 5.5], [18.0, 5.5]], 0],
    ['second terrace doorway', [[10.0, 14.5], [13.0, 14.5], [18.0, 14.5]], 0], ['barracks doorway', [[10.0, 41.5], [13.0, 41.5], [17.5, 41.5]], 0],
    ['south terrace doorway', [[10.0, 55.5], [13.0, 55.5], [17.0, 55.5]], 0], ['exit gate approach', [[38.0, 30.0], [39.5, 3.0], [39.5, 1.5]], 0]]) {
    r = await pg.evaluate(([pts]) => { __place(1, pts[0][0], pts[0][1], 0); return __route(1, pts.slice(1), 30); }, [pts]);
    check('zone 2: the player reaches the ' + nm + ' (' + y + ' m)', r.reached === pts.length - 1 && Math.abs(r.y - y) < 0.05, JSON.stringify(r));
  }
  // pieces line up with their cells (no sideways run / rail / fence pieces, long prefabs along their blocks): checked on
  // the placed collision boxes of every run cell and every long prefab block, in both zones and all layers
  const al = await pg.evaluate(() => {
    const L = IB.Game.level, W = L.world, T = L.theme, bad = [], o = []; let n = 0;
    const runs = '{=jrf', long = ['Y', '+', 'k', 'z', 'V', 'X', 'Q', 'T', 'J', 'F', 'g', '&', '>', '<', '^', 'u', 'v', 'B'];
    L.zones.forEach((Z, zi) => {
      const g = Z.grid;
      [g].concat(g.layers).forEach((G) => {
        const y0 = G.y || 0;
        const boxesAt = (x0, z0, x1, z1, names) => { W.query(Z.ox + x0, Z.oz + z0, Z.ox + x1, Z.oz + z1, o); return o.filter(b => names.indexOf(b.piece) >= 0 && b.y0 >= y0 - 0.05 && b.y0 < y0 + 0.5 && b.x0 < Z.ox + x1 && b.x1 > Z.ox + x0 && b.z0 < Z.oz + z1 && b.z1 > Z.oz + z0); };
        for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) {
          const ch = G.at(c, r); if (runs.indexOf(ch) < 0 || !T.symbols[ch]) continue;
          const d = T.symbols[ch], names = d.pieces.concat(d.full ? [d.full] : []).map(nm => IB.themePiece(T, nm));
          const ew = G.at(c - 1, r) === ch || G.at(c + 1, r) === ch, ns = G.at(c, r - 1) === ch || G.at(c, r + 1) === ch;
          if (ew === ns) continue;   // corners, crossings and lone cells
          const bx = boxesAt(c + 0.3, r + 0.3, c + 0.7, r + 0.7, names); n++;
          if (!bx.length) { bad.push(zi + ' ' + ch + ' no box at ' + c + ',' + r); continue; }
          bx.forEach(b => { const lx = b.x1 - b.x0, lz = b.z1 - b.z0; if (ew ? lx < lz : lz < lx) bad.push(zi + ' ' + ch + ' sideways at ' + c + ',' + r + ' ' + lx.toFixed(2) + 'x' + lz.toFixed(2)); });
        }
        long.forEach((ch) => {
          const d = T.symbols[ch]; if (!d || !d.size || d.size[0] === d.size[1]) return;
          const names = d.pieces.map(nm => IB.themePiece(T, nm));
          const seen = {};
          for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) {
            if (G.at(c, r) !== ch || seen[c + ',' + r]) continue;
            let w = 0; while (G.at(c + w, r) === ch) w++;
            let h = 0; while (G.at(c, r + h) === ch) h++;
            for (let a = 0; a < h; a++) for (let b2 = 0; b2 < w; b2++) seen[(c + b2) + ',' + (r + a)] = 1;
            const one = d.size[0] > d.size[1] ? [d.size[0], d.size[1]] : [d.size[1], d.size[0]];
            const alongX = w % one[0] === 0 && h % one[1] === 0 && !(w % one[1] === 0 && h % one[0] === 0 && h > w);
            const bx = boxesAt(c + 0.05, r + 0.05, c + w - 0.05, r + h - 0.05, names); n++;
            if (!bx.length) { bad.push(zi + ' ' + ch + ' no box in block at ' + c + ',' + r); continue; }
            let X0 = 1e9, X1 = -1e9, Z0 = 1e9, Z1 = -1e9;
            bx.forEach(b => { X0 = Math.min(X0, b.x0); X1 = Math.max(X1, b.x1); Z0 = Math.min(Z0, b.z0); Z1 = Math.max(Z1, b.z1); });
            if ((X1 - X0 > Z1 - Z0) !== (w > h) && w !== h) bad.push(zi + ' ' + ch + ' block ' + w + 'x' + h + ' at ' + c + ',' + r + ' boxes ' + (X1 - X0).toFixed(2) + 'x' + (Z1 - Z0).toFixed(2));
            if (X1 > Z.ox + c + w + 0.35 || X0 < Z.ox + c - 0.35 || Z1 > Z.oz + r + h + 0.35 || Z0 < Z.oz + r - 0.35) bad.push(zi + ' ' + ch + ' boxes leave the block at ' + c + ',' + r);
          }
        });
      });
    });
    return { n, bad };
  });
  check('runs, rails, fences and long prefabs lie along their cells (' + al.n + ' checked)', al.n > 200 && al.bad.length === 0, al.bad.slice(0, 6).join(' | '));
  async function chase(zi, deck, robots, secs, goal) {
    const list = await pg.evaluate(([zi, deck, robots]) => {
      __place(zi, deck[0], deck[1], deck[2]);
      IB.Game.player.protect = 1e9;
      const Z = IB.Game.level.zones[zi];
      return robots.map(([type, c, r]) => {
        const slot = __TEST__.spawnRobot(type, Z.ox + c + 0.5, Z.oz + r + 0.5);
        const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
        return [type, slot];
      });
    }, [zi, deck, robots]);
    let best = 0, last = null, t = 0;
    while (t < secs) {
      last = await pg.evaluate(([list, zi]) => { __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot], p = IB.Game.player; return { on: r.on, x: +r.x.toFixed(2), y: +r.y.toFixed(2), z: +r.z.toFixed(2), d: +Math.hypot(r.x - p.x, r.z - p.z).toFixed(2), state: r.state }; }, [list, zi]);
      t += 0.5; if (last.on && last.d < 4) best = Math.max(best, last.y);
      if (best > goal) break;
    }
    return { best, last, t };
  }
  let w = await chase(0, [60.0, 5.0, 7.2], [['crawler', 20, 40]], 90, 7.1);
  check('zone 1: a Crawler from the ledge climbs both switchbacks to the player (< 4 m) on terrace 2 within 90 s', w.best > 7.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [70.0, 8.0, 2.4], [['blader', 40, 40]], 60, 2.3);
  check('zone 2: a Blade Bot from the gallery climbs the stair to the player (< 4 m) on the hangar mezzanine within 60 s', w.best > 2.3, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
