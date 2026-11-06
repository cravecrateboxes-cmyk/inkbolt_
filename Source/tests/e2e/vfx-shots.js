// INKBOLT VFX review: plays scripted combat moments with deterministic frame stepping and saves screenshots
// to tests/e2e/review/vfx-*.png plus a contact sheet (vfx-sheet.png). Run: node tests/e2e/vfx-shots.js
// (ONLY=deaths,bomber,... re-shoots a subset; the sheet is always rebuilt from every vfx-*.png in review/).
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const TARGET = process.argv[2] || 'Play Inkbolt.html';
const OUT = path.join(__dirname, 'review');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.png') ? 'image/png' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

async function open(browser, base, plan, opts) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const pg = await ctx.newPage();
  pg.logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') pg.logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => pg.logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=' + plan);
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 60000 });
  // take over the frame loop: every __step(n) runs n frames of 1/60 s, so a shot lands on an exact moment
  await pg.evaluate(o => {
    const G = IB.Game;
    G.player.protect = 1e9; G.guard.on = false;
    if (o && o.tier) G.setTier(o.tier);
    window.__q = null; window.requestAnimationFrame = cb => { window.__q = cb; return 1; };
  }, opts || {});
  await pg.waitForFunction(() => !!window.__q, null, { timeout: 20000 });
  await pg.evaluate(() => {
    window.__now = performance.now();
    window.__step = (n) => { for (let i = 0; i < n; i++) { const cb = window.__q; window.__q = null; if (!cb) break; window.__now += 1000 / 60; cb(window.__now); } };
    // no waves: the scene is staged by hand
    IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
    IB.Game.level.zones.forEach(z => { z.queue.length = 0; z.plan = Object.assign({}, z.plan, { waves: [[]] }); z.wave = 0; });
    // stand on the most open patch of the zone and aim down its longest clear line
    const G = IB.Game, p = G.player, w = G.level.world, z = G.level.zones[G.zone], N = z.nav;
    const open = (i, j) => i >= 0 && j >= 0 && i < N.nx && j < N.nz && !N.blocked[j * N.nx + i];
    let bestC = null, bs = -1;
    for (let j = 8; j < N.nz - 8; j += 3) for (let i = 8; i < N.nx - 8; i += 3) {
      if (!open(i, j)) continue; let r = 2; while (r < 12 && IB.Boom.clearPatch(open, i, j, r + 2)) r += 2;
      const x = z.ox + (i + 0.5) * 0.5, zz = z.oz + (j + 0.5) * 0.5;
      if (Math.hypot(x - z.entry.x, zz - z.entry.z) < 5) continue;
      if (r > bs) { bs = r; bestC = { x: x, z: zz }; }
    }
    if (bestC) { p.x = bestC.x; p.z = bestC.z; }
    let best = 0, by = 0;
    for (let k = 0; k < 24; k++) { const yaw = k / 24 * Math.PI * 2, dx = -Math.sin(yaw), dz = -Math.cos(yaw); const h = w.ray(p.x, 0.6, p.z, dx, 0, dz, 40), h2 = w.ray(p.x, 1.5, p.z, dx, 0, dz, 40); const d = Math.min(h ? h.t : 40, h2 ? h2.t : 40); if (d > best) { best = d; by = yaw; } }
    p.yaw = by; p.pitch = -0.08;
    // step back so the open patch is in front of us
    const back = Math.min(3, best * 0.15); p.x += Math.sin(by) * back; p.z += Math.cos(by) * back;
    window.__ahead = (d, side) => { const dx = -Math.sin(p.yaw), dz = -Math.cos(p.yaw); return { x: p.x + dx * d - dz * (side || 0), z: p.z + dz * d + dx * (side || 0) }; };
    window.__spawn = (type, d, side, o) => {
      const a = __ahead(d, side); IB.AI.spawn(type, a.x, a.z, G.zone, p.x, p.z, Object.assign({ pose: true }, o || {}));
      const r = IB.AI.robots.filter(q => q.on && q.type === type).pop(); r.yaw = Math.atan2(p.x - r.x, p.z - r.z); return r;
    };
  });
  await pg.evaluate(() => __step(10));
  return pg;
}
async function shot(pg, name, frames) {
  if (frames) await pg.evaluate(n => __step(n), frames);
  const f = path.join(OUT, 'vfx-' + name + '.png');
  await pg.screenshot({ path: f, timeout: 180000 });
  console.log('saved', path.relative(ROOT, f), JSON.stringify(await pg.evaluate(() => IB.Boom.stats())), pg.logs.length ? 'LOGS ' + pg.logs.join(' | ') : '');
  return f;
}

const SCENES = {
  // robot wrecks on level 1 and on level 8: same kills, the late level is bigger, busier, and chains
  async deaths(browser, base) {
    const out = [];
    for (const [plan, tag] of [['mountains', 'l1'], ['tt3', 'l8']]) {
      const pg = await open(browser, base, plan);
      await pg.evaluate(() => { window.__r = [__spawn('crawler', 6.5, -1.6), __spawn('gunner', 8, 1.4), __spawn('crawler', 9.5, 0.2)]; });
      await pg.evaluate(() => __step(2));
      await pg.evaluate(() => { IB.AI.kill(__r[0], IB.Game.onKill); });
      out.push(await shot(pg, 'death-crawler-' + tag, 4));
      await pg.evaluate(() => { IB.AI.kill(__r[1], IB.Game.onKill); IB.AI.kill(__r[2], IB.Game.onKill); });
      out.push(await shot(pg, 'death-gunner-' + tag, 7));
      out.push(await shot(pg, 'death-smoke-' + tag, 16));
      await pg.context().close();
    }
    return out;
  },
  async bomber(browser, base) {
    const pg = await open(browser, base, 'office');
    await pg.evaluate(() => { const a = __ahead(7, 0.5); IB.Projectiles.explode(a.x, 0.45, a.z, 3, 0, 0, { type: 'bomber' }); });
    const a = await shot(pg, 'bomber-blast', 7);
    const b = await shot(pg, 'bomber-after', 14);
    const c = await shot(pg, 'bomber-smoke', 34);
    await pg.context().close();
    return [a, b, c];
  },
  async drone(browser, base) {
    const pg = await open(browser, base, 'tt1');
    await pg.evaluate(() => { window.__d = __spawn('drone', 7, 0); IB.Game.player.pitch = 0.12; });
    await pg.evaluate(() => __step(3));
    await pg.evaluate(() => IB.AI.kill(__d, IB.Game.onKill));
    const a = await shot(pg, 'drone-shot', 3);
    await pg.evaluate(() => { IB.Game.player.pitch = -0.12; });
    const b = await shot(pg, 'drone-impact', 37);
    await pg.context().close();
    return [a, b];
  },
  async canisters(browser, base) {
    const pg = await open(browser, base, 'tt2');
    const info = await pg.evaluate(() => {
      const G = IB.Game, p = G.player, cans = IB.Boom.canisters().filter(c => c.zone === G.zone);
      if (!cans.length) return null;
      // stand 7 m from the first canister, looking at it
      const c = cans[0], z = G.level.zones[c.zone]; let best = null;
      for (let k = 0; k < 48; k++) { const a = k / 16 * Math.PI * 2, R = 7 - Math.floor(k / 16) * 1.5, x = c.x + Math.cos(a) * R, zz = c.z + Math.sin(a) * R; const tx = c.x + Math.cos(a) * 0.5, tz = c.z + Math.sin(a) * 0.5; if (IB.Zones.isOpen(z, x, zz) && G.level.world.los(x, 1.5, zz, tx, 0.5, tz) && G.level.world.los(x, 0.45, zz, tx, 0.45, tz) && G.level.world.los(x, 1.5, zz, tx, 1.2, tz)) { best = { x: x, z: zz }; break; } }
      if (!best) best = { x: c.x, z: c.z + 7 };
      p.x = best.x; p.z = best.z; p.yaw = Math.atan2(-(c.x - p.x), -(c.z - p.z)); p.pitch = -0.12;
      window.__can = c; return { inZone: cans.length, all: IB.Boom.canisters().length };
    });
    console.log('canisters', JSON.stringify(info));
    if (!info) { await pg.context().close(); return []; }
    await pg.evaluate(() => { const r = __spawn('crawler', 6.2, 1.1); r.state = 'idle'; });
    await pg.evaluate(() => __step(4));
    const a = await shot(pg, 'canister-idle', 1);
    await pg.evaluate(() => { const c = __can, q = []; IB.Game.level.world.query(c.x - 0.1, c.z - 0.1, c.x + 0.1, c.z + 0.1, q); IB.Boom.hitCan(q.find(b => b.kind === 'canister'), 99); });
    const b = await shot(pg, 'canister-fuse', 16);
    const c = await shot(pg, 'canister-blast', 24);
    await pg.context().close();
    return [a, b, c];
  },
  async guns(browser, base) {
    const pg = await open(browser, base, 'smallcity');
    await pg.evaluate(() => { const G = IB.Game; G.player.pitch = -0.25; IB.Weapons.give(G.ws, 'buzz'); IB.Weapons.equip(G.ws, 'buzz', true); IB.Input.fire = true; });
    const a = await shot(pg, 'muzzle-smg', 9);
    await pg.evaluate(() => { const r = __spawn('gunner', 6, 0); IB.Game.player.pitch = -0.06; r.state = 'idle'; r.hp = 1e6; r.maxHp = 1e6; });
    const b = await shot(pg, 'hits-smg', 8);
    await pg.evaluate(() => { IB.Input.fire = false; });
    await pg.context().close();
    return [a, b];
  },
  async status(browser, base) {
    const pg = await open(browser, base, 'classroom');
    await pg.evaluate(() => {
      const a = __spawn('crawler', 5, -1.2), b = __spawn('gunner', 6, 1.2), c = __spawn('crawler', 7.5, 0.3);
      [a, b, c].forEach(r => { r.state = 'idle'; r.hp = r.maxHp = 1e6; });
      IB.Status.apply(a, 'shock', 5, 30); IB.Status.apply(b, 'acid', 5, 30); window.__s = [a, b, c];
    });
    await pg.evaluate(() => __step(20));
    await pg.evaluate(() => { const [a, b, c] = __s; IB.Boom.lightning(a.x, 0.6, a.z, c.x, 0.6, c.z); IB.Boom.lightning(c.x, 0.6, c.z, b.x, 0.7, b.z); IB.Boom.chainBurst(b.x, b.z, 3); });
    const s = await shot(pg, 'shock-acid-rod', 3);
    await pg.context().close();
    return [s];
  },
  async hurt(browser, base) {
    const pg = await open(browser, base, 'mountains');
    await pg.evaluate(() => { const G = IB.Game; G.player.protect = 0; __TEST__.damagePlayer(G.player.health - 18); G.player.protect = 1e9; });
    const a = await shot(pg, 'hurt-low', 40);
    await pg.context().close();
    return [a];
  },
  async clear(browser, base) {
    const pg = await open(browser, base, 'bedroom');
    await pg.evaluate(() => { const G = IB.Game, z = G.level.zones[G.zone], g = z.exitGate, p = G.player; p.x = g.x; p.z = g.z + 11; p.yaw = 0; p.pitch = 0.15; });
    await pg.evaluate(() => { __step(2); const G = IB.Game; IB.Boom.zoneClear(G.level, G.zone, true); });
    const a = await shot(pg, 'level-clear', 44);
    await pg.evaluate(() => { const G = IB.Game, z = G.level.zones[1] || G.level.zones[0], g = z.entryGate || z.exitGate, p = G.player; IB.Zones.setVisible(G.level, 1); p.x = g.x; p.z = g.z + 5; p.yaw = 0; p.pitch = -0.1; IB.Zones.setGate(g, true, true); IB.Zones.setGate(g, false); });
    const b = await shot(pg, 'gate-slam', 40);
    await pg.context().close();
    return [a, b];
  }
};

(async () => {
  const server = await serve();
  const port = server.address().port, base = 'http://localhost:' + port + '/' + encodeURI(TARGET);
  const browser = await chromium.launch({ args: ARGS });
  fs.mkdirSync(OUT, { recursive: true });
  const all = [];
  for (const [name, fn] of Object.entries(SCENES)) if (!process.env.ONLY || process.env.ONLY.split(',').includes(name)) all.push(...await fn(browser, base));
  {
    const order = ['death-crawler-l1', 'death-gunner-l1', 'death-smoke-l1', 'death-crawler-l8', 'death-gunner-l8', 'death-smoke-l8', 'bomber-blast', 'bomber-after', 'bomber-smoke',
      'drone-shot', 'drone-impact', 'canister-idle', 'canister-fuse', 'canister-blast', 'muzzle-smg', 'hits-smg', 'shock-acid-rod', 'hurt-low', 'level-clear', 'gate-slam'];
    const have = new Set(fs.readdirSync(OUT).filter(f => /^vfx-.*\.png$/.test(f) && f !== 'vfx-sheet.png').map(f => f.slice(4, -4)));
    all.length = 0; order.concat([...have].filter(n => !order.includes(n)).sort()).forEach(n => { if (have.has(n)) all.push(path.join(OUT, 'vfx-' + n + '.png')); });
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 100 } }); const pg = await ctx.newPage();
    const cells = all.map(f => '<figure><img src="http://localhost:' + port + '/' + path.relative(ROOT, f).split(path.sep).map(encodeURIComponent).join('/') + '"><figcaption>' + path.basename(f, '.png').replace('vfx-', '') + '</figcaption></figure>').join('');
    await pg.setContent('<style>body{margin:0;background:#15121C;font:700 18px Arial;color:#FFFDF7;display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:8px}figure{margin:0}img{width:100%;display:block;border:3px solid #FFFDF7}figcaption{padding:4px 2px}</style>' + cells);
    await pg.waitForLoadState('networkidle');
    await pg.screenshot({ path: path.join(OUT, 'vfx-sheet.png'), fullPage: true });
    console.log('saved sheet');
    await ctx.close();
  }
  await browser.close(); server.close();
})();
