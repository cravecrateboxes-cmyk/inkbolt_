// INKBOLT Mosswood Gardens (plan 'mossgarden'): the walk through both zones and the climbs. The player walks the
// entry axis, round the fountain, up the grand stair onto the terrace (2.34 m), along it and down the east stair to
// the exit path, the gate and the trail; in zone 2 past the reflecting pool, over the stone bridge, up the mound path
// onto the folly's plinth (3.54 m) and on to the exit gate and the hatch (no invisible walls, nothing blocks the way).
// The terrace balustrade keeps the player up there, the stream can be waded. Ground robots follow: up the stairs onto
// the terrace, up the mound to the folly, onto the bridge. Run, rail, span and wall pieces lie along their line of
// cells (checked on the drawn vertices). The render loop is paused and the real Player / AI code is stepped at 1/60 s.
// Run (after tools/build.py): node tests/e2e/mossgarden-walk.spec.js
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
const TER = 2.34, MOUND = 3.0;

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=mossgarden');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 180000 });
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
      p.protect = 0; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y === undefined ? G.level.world.floorAt(Z.ox + x, Z.oz + z, 50) : y; p.vx = p.vz = p.vy = 0;
    };
    IB.Game.level.zones.forEach(z => { IB.Zones.setGate(z.exitGate, true, true); if (z.entryGate) IB.Zones.setGate(z.entryGate, true, true); });
  });
  // nav: open cells on the terrace (zone 1), the mound's plateau, the folly plinth and the bridge crowns (zone 2)
  const nav = await pg.evaluate(([TER, MOUND]) => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, terrace: 0, plateau: 0, plinth: 0, bridge: 0 };
    for (let k = 0; k < NC * (N.layers || 1); k++) if (!N.blocked[k]) {
      const h = N.h ? N.h[k] : 0;
      if (Math.abs(h - TER) < 0.02) o.terrace++; if (Math.abs(h - MOUND) < 0.02) o.plateau++; if (Math.abs(h - MOUND - 0.54) < 0.02) o.plinth++; if (Math.abs(h - 0.9) < 0.02) o.bridge++;
    }
    return o;
  }), [TER, MOUND]);
  check('nav: zone 1 has open cells on the terrace, zone 2 on the mound plateau, the folly plinth and the bridges',
    nav[0].terrace > 800 && nav[1].plateau > 40 && nav[1].plinth > 30 && nav[1].bridge > 20, JSON.stringify(nav));

  // ---- the walk: entry axis -> round the fountain -> grand stair -> terrace -> east stair -> exit path -> gate -> trail
  let r = await pg.evaluate(() => { __place(0, 35.5, 67.5, 0); return __route(0, [[35.5, 50.0], [42.5, 46.5], [43.0, 31.0], [35.5, 29.0], [35.5, 17.5], [35.5, 11.5]], 90); });
  check('walk zone 1: the entry axis, round the fountain, up the grand stair onto the terrace (2.34 m)', r.reached === r.of && r.stuck === 0 && Math.abs(r.y - TER) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(0, [[42.5, 11.5], [43.5, 6.5], [49.5, 6.5], [52.0, 8.6], [56.5, 9.4], [60.6, 9.0], [61.5, 4.0], [61.5, 1.0], [61.5, -6.0], [61.5, -13.0]], 90));
  check('walk zone 1: along the terrace, down the east stair, the exit path through the gate onto the trail', r.reached === r.of && r.stuck === 0 && r.lo > -0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[17.5, 69.5], [17.5, 67.5], [13.6, 62.0], [13.3, 52.0], [13.6, 42.6], [15.6, 38.4], [17.5, 37.2], [17.5, 34.5]], 90));
  check('walk zone 2: through the entry gate, past the reflecting pool onto the stone bridge (0.9 m)', r.reached === r.of && r.stuck === 0 && Math.abs(r.y - 0.9) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[17.5, 31.5], [19.6, 28.4], [23.6, 25.4], [26.0, 21.0], [25.4, 16.6], [22.4, 15.4], [19.6, 15.5]], 60));
  check('walk zone 2: off the bridge, up the mound path onto the folly plinth (3.54 m)', r.reached === r.of && r.stuck === 0 && Math.abs(r.y - MOUND - 0.54) < 0.06, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[22.4, 13.0], [24.8, 8.6], [30.4, 5.6], [36.0, 3.2], [37.5, 1.0], [37.5, -6.0], [37.5, -14.0]], 80));
  check('walk zone 2: down the exit path to the exit gate and the exit path', r.reached === r.of && r.stuck === 0, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit path leads on toward the hatch', hatch.d < 10, JSON.stringify(hatch));

  // ---- the terrace's balustrade keeps the player up; the side stair; the stream can be waded; into the glasshouse
  r = await pg.evaluate(([TER]) => { __place(0, 25.5, 11.0, TER); return __route(0, [[25.5, 14.5]], 3); }, [TER]);
  check('zone 1: the balustrade keeps the player on the terrace', r.lo > TER - 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 9.5, 18.0, 0); return __route(0, [[9.5, 16.0], [9.5, 11.0], [6.0, 11.0]], 30); });
  check('zone 1: up the side stair from the rose walk onto the terrace', r.reached === r.of && Math.abs(r.y - 2.34) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 49.0, 40.0, 0); return __route(0, [[52.5, 40.0], [56.0, 41.0], [59.0, 43.0], [59.0, 46.5]], 40); });
  check('zone 1: through the glasshouse west door, past the lily pool, out of the south door', r.reached === r.of && r.stuck === 0, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 8.0, 40.0, 0); return __route(1, [[8.0, 30.0]], 20); });
  check('zone 2: the stream can be waded (no wall along it)', r.reached === 1 && r.stuck === 0, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 60.5, 26.5, 0); return __route(1, [[60.5, 24.0], [60.5, 21.5]], 15); });
  check('zone 2: in through the maze arch', r.reached === r.of && r.stuck === 0, JSON.stringify(r));

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
  let w = await chase(0, [24.0, 7.0, TER], [['crawler', 27, 22]], 70, TER - 0.1);
  check('zone 1: a Crawler from the parterres climbs a stair to the player on the terrace (< 4 m) within 70 s', w.best > TER - 0.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [17.5, 15.5 - 2.6, MOUND + 0.54], [['crawler', 36, 41]], 80, MOUND + 0.4);
  check('zone 2: a Crawler from the meadow crosses the stream and climbs the mound to the player on the folly (< 4 m) within 80 s', w.best > MOUND + 0.4, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [17.5, 34.5, 0.9], [['blader', 9, 46]], 60, 0.8);
  check('zone 2: a Blade Bot reaches the player on the bridge crown (< 4 m) within 60 s', w.best > 0.8, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));

  // ---- run / rail / span / wall pieces lie along their line of cells: the drawn vertices (outline shell left out)
  // inside each cell or block, in a height band, are long along the line and short across it
  const runs = await pg.evaluate(([TER]) => {
    const L = IB.Game.level, out = { checked: 0, bad: [], side: 0 };
    // vertices in the cell / block (the line's own axis inclusive, the cross axis 2 cm inset so a neighbour's edge
    // on the cell boundary does not count), in a height band; returns the extents and the centre's offset
    function ext(zi, c0, r0, w, h, y0, y1, alongX) {
      const Z = L.zones[zi], e = [1e9, -1e9, 1e9, -1e9], mx = alongX ? -0.001 : 0.02, mz = alongX ? 0.02 : -0.001;
      const x0 = Z.ox + c0 + mx, x1 = Z.ox + c0 + w - mx, z0 = Z.oz + r0 + mz, z1 = Z.oz + r0 + h - mz;
      Z.meshes.forEach(m => {
        const P = m.geometry.attributes.position.array, H = m.geometry.attributes.aHull ? m.geometry.attributes.aHull.array : null;
        for (let i = 0; i < P.length; i += 3) {
          if (H && (H[i] || H[i + 1] || H[i + 2])) continue;
          const x = P[i], y = P[i + 1], z = P[i + 2];
          if (y < y0 || y > y1 || x < x0 || x > x1 || z < z0 || z > z1) continue;
          e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z);
        }
      });
      return [e[1] - e[0], e[3] - e[2], (e[0] + e[1]) / 2 - (x0 + x1) / 2, (e[2] + e[3]) / 2 - (z0 + z1) / 2];
    }
    function expect(tag, zi, c0, r0, w, h, y0, y1, alongX, minAlong, maxAcross) {
      const [ex, ez] = ext(zi, c0, r0, w, h, y0, y1, alongX), along = alongX ? ex : ez, across = alongX ? ez : ex;
      out.checked++;
      if (!(along >= minAlong && across <= maxAcross)) out.bad.push(tag + '@' + c0 + ',' + r0 + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
    }
    const blocks = (g, ch) => { const seen = {}, res = []; for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) { if (g.at(c, r) !== ch || seen[c + ',' + r]) continue; let w = 0, h = 0; while (g.at(c + w, r) === ch) w++; while (g.at(c, r + h) === ch) h++; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen[(c + x) + ',' + (r + y)] = 1; res.push([c, r, w, h]); } return res; };
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, at = (c, r) => g.at(c, r);
      for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
        const ch = at(c, r), H = { l: [0.6, 0.62], m: [1.25, 0.84], H: [2.7, 0.94] }[ch];
        if (H) {   // hedges: a straight run cell carries the full module along its run
          const lk = ch === 'H' ? 'H&' : ch, is = (dc, dr) => lk.indexOf(at(c + dc, r + dr)) >= 0;
          const ew = is(-1, 0) && is(1, 0) && !is(0, -1) && !is(0, 1), ns = is(0, -1) && is(0, 1) && !is(-1, 0) && !is(1, 0);
          if (ew || ns) expect('hedge-' + ch, zi, c, r, 1, 1, -0.01, H[0] + 0.01, ew, 0.99, H[1] + 0.02);
        }
        if (ch === 'B' || ch === '|') {   // balustrade top rail along the ring, on the garden side of the cell
          const ew = ch === 'B', [ex, ez, ox, oz] = ext(zi, c, r, 1, 1, TER + 0.8, TER + 1.0, ch === 'B');
          out.checked++;
          if (!((ew ? ex : ez) >= 0.4 && (ew ? ez : ex) <= 0.4)) out.bad.push('rail@' + c + ',' + r + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
          if ((ew ? oz : ox) > 0.15) out.side++; else out.bad.push('rail side@' + c + ',' + r + ' ' + ox.toFixed(2) + ',' + oz.toFixed(2));
        }
      }
      // garden wall modules face the garden: the mortar course on their front (1.3 m up) lies along the wall, on the
      // zone side of the wall cell (a module turned a quarter would put it across the cell)
      function wallFace(c, r, dx, dz) {
        if ('NIWT!$'.indexOf(at(c + dx, r + dz)) >= 0) return;   // a wall-backed prop stands against this cell
        const Z = L.zones[zi], e = [1e9, -1e9, 1e9, -1e9];
        Z.meshes.forEach(m => {
          const P = m.geometry.attributes.position.array, H = m.geometry.attributes.aHull ? m.geometry.attributes.aHull.array : null;
          for (let i = 0; i < P.length; i += 3) {
            if (H && (H[i] || H[i + 1] || H[i + 2])) continue;
            const x = P[i] - Z.ox - c, y = P[i + 1], z = P[i + 2] - Z.oz - r;
            if (y < 1.29 || y > 1.345 || x < -0.001 || x > 1.001 || z < -0.001 || z > 1.001) continue;
            e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z);
          }
        });
        out.checked++;
        const ok = dz ? (e[3] - e[2] < 0.02 && (e[2] - 0.5) * dz > 0.38) : (e[1] - e[0] < 0.02 && (e[0] - 0.5) * dx > 0.38);
        if (!ok) out.bad.push('wall@' + c + ',' + r + ' ' + e.map(v => v.toFixed(2)).join(','));
      }
      for (let c = 4; c < g.w - 4; c++) { if (Math.abs(c + 0.5 - (zi ? 37.5 : 61.5)) > 4) wallFace(c, 0, 0, 1); if (Math.abs(c + 0.5 - (zi ? 17.5 : 35.5)) > 4) wallFace(c, g.h - 1, 0, -1); }
      for (let r = 4; r < g.h - 4; r++) { wallFace(0, r, 1, 0); wallFace(g.w - 1, r, -1, 0); }
      // prefabs with a long side: rose arches and the maze arch span X; wall fountains and benches lie along their block;
      // the bridges carry their walk along Z; the glasshouse runs along X; the shed's ridge along its block (Z)
      blocks(g, 'R').forEach(([c, r, w, h]) => expect('rosearch', zi, c, r, w, h, 2.6, 3.2, true, 2.5, 0.9));
      blocks(g, '&').forEach(([c, r, w, h]) => expect('mazearch', zi, c, r, w, h, 3.0, 3.4, true, 1.5, 0.95));
      const base = (c, r, w, h) => L.world.groundAt(Z.ox + c + w / 2, Z.oz + r + h / 2);
      ['w', 'W'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => expect('wallfountain', zi, c, r, w, h, 1.9, 2.45, w > h, 2.4, 0.5)));
      ['j', 'k', '<', '>'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => { if (w * h !== 2) return; const b = base(c, r, w, h); expect('bench', zi, c, r, w, h, b + 0.55, b + 0.9, w > h, 1.7, 0.4); }));
      blocks(g, 'D').forEach(([c, r, w, h]) => expect('bridge', zi, c, r, w, h, 0.16, 0.2, false, 4.4, 3.2));
      blocks(g, 'X').forEach(([c, r, w, h]) => expect('glasshouse', zi, c, r, w, h, 3.62, 3.74, true, 13.5, 10.1));
      blocks(g, '$').forEach(([c, r, w, h]) => expect('shed', zi, c, r, w, h, 3.3, 3.4, false, 4.5, 0.6));
    });
    return out;
  }, [TER]);
  check('run, rail, span and wall pieces lie along their line of cells (none a quarter turn off), balustrades on the garden side',
    runs.checked > 600 && runs.bad.length === 0 && runs.side > 30, runs.checked + ' checked, ' + runs.side + ' rails outward ' + runs.bad.slice(0, 6).join(' | '));

  // ---- the stream flows and the lumenbell pods pulse
  const anim = await pg.evaluate(() => {
    const L = IB.Game.level; let mat = null;
    L.root.traverse(o => { if (o.name === 'Stream') mat = o.material; });
    const pod = (L.glows || []).find(g => g.piece === 'GlowPod_Glow');
    const t0 = mat ? mat.uniforms.uT.value : null;
    IB.Zones.updateClouds(L, 0.7);
    const c1 = pod && pod.mesh.material.color.r;
    IB.Zones.updateClouds(L, 0.9);
    return { stream: mat ? mat.uniforms.uT.value - t0 : null, pod: pod ? Math.abs(pod.mesh.material.color.r - c1) : null };
  });
  check('the stream flows and the lumenbell pods pulse', anim.stream > 1 && anim.pod > 0.001, JSON.stringify(anim));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
