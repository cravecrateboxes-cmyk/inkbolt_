// INKBOLT weapon loot glow review shots (game/wdrops.js): every tier at near / mid / far distance, standing in a beam,
// and filmstrips of a drop landing, the idle pulse, walking up to a drop, picking one up and two drops on one spot.
//   node Source/tests/e2e/lootglow-shots.js <outDir>
// Env: PLAN (default airfield7: a long open lane in zone 0), LOOK=classic adds &look=classic, TIER (default high), W / H (800 x 450),
// HTML (default Source/dev.html: the sources as they are, no build needed), ONLY=<scene names, comma separated>.
// The render loop is paused; every frame is stepped by hand (WeaponDrops.update at a fixed time, then one render) and
// read straight off the canvas, so the HUD never covers the glow and the filmstrip times are exact. Writes
// <outDir>/<scene>-<k>.png and <outDir>/shots.json (scene -> [{file, label, calls}]).
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const outDir = process.argv[2];
if (!outDir) { console.log('usage: node lootglow-shots.js <outDir>'); process.exit(2); }
const PLAN = process.env.PLAN || 'airfield7', TIER = process.env.TIER || 'high', HTML = process.env.HTML || 'Source/dev.html';
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
fs.mkdirSync(outDir, { recursive: true });

function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => {
        if (e) { r.writeHead(404); return r.end(); }
        r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.css') ? 'text/css' : 'application/octet-stream' });
        r.end(d);
      });
    }).listen(0, () => res(s));
  });
}

const TIERS = ['gray', 'green', 'blue', 'purple', 'orange'];
(async () => {
  const server = await serve();
  const q = '?autotest=1&plan=' + PLAN + (process.env.LOOK === 'classic' ? '&look=classic' : '');
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: +(process.env.W || 800), height: +(process.env.H || 450) }, deviceScaleFactor: 1 });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  pg.on('console', m => { if (m.type() === 'error') logs.push('console: ' + m.text()); });
  await pg.goto('http://localhost:' + server.address().port + '/' + encodeURI(HTML) + q);
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && !document.getElementById('boot'), null, { timeout: 300000 });
  await pg.evaluate((tier) => {
    IB.AI.spawn = function () { return null; }; IB.AI.robots.forEach(r => { r.on = false; });
    if (IB.Game.guard) IB.Game.guard.on = false;
    __TEST__.setTier(tier);
  }, TIER);
  await pg.waitForTimeout(1500);
  // stage: the lane runs from zone 0's entry into the zone (-z); drops stand in a row across it
  const lane = await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;   // the game loop stops here: frames are stepped by hand below
    const G = IB.Game, R = IB.Render, Z = IB.Zones, z = G.level.zones[0], p = G.player;
    G.settings.shake = false; G.trauma = 0; p.protect = 1e9; p.alive = true;
    G.level.zones.forEach(zz => { if (zz.queue) zz.queue.length = 0; zz.wave = zz.plan.waves.length - 1; });
    Z.setVisible(G.level, 0);
    if (IB.LightGrid && IB.LightGrid.ready) IB.LightGrid.bakeZoneNow(0);
    const open = (x, zz) => Z.isOpen(z, x, zz);
    // the longest straight open run along -z anywhere in the zone (room for the five-drop row), in 1 m steps
    let best = { x: z.entry.x, z0: z.entry.z, len: 0 };
    for (let x = z.ox + 5; x <= z.ox + z.w - 5; x += 1) {
      let run = 0;
      for (let zz = z.oz + z.h - 1; zz >= z.oz; zz -= 1) {
        if (open(x, zz) && open(x - 3.6, zz) && open(x + 3.6, zz) && open(x - 1.8, zz) && open(x + 1.8, zz)) { run++; if (run > best.len) best = { x, z0: zz + run - 1, len: run }; } else run = 0;
      }
    }
    const x0 = best.x, zRow = best.z0 - Math.max(4, Math.min(best.len - 2, 50)), zMax = best.z0;
    window.__lg = { t: 100, x0, zRow, zMax };
    window.__step = (dt, n) => {
      for (let i = 0; i < (n || 1); i++) {
        __lg.t += dt;
        IB.WeaponDrops.update(dt, __lg.t, G);
        IB.FX.update(dt, R.camera, p, 0, function () { });
      }
    };
    window.__cam = (x, zz, yaw, pitch) => {
      p.x = x; p.z = zz; p.yaw = yaw; p.pitch = pitch || 0; p.y = Z.floorY(x, zz, 1.2) || 0; p.vx = p.vz = p.vy = 0;
      R.camera.position.set(x, p.y + 1.55, zz); R.camera.rotation.set(p.pitch, yaw, 0); R.camera.updateMatrixWorld();
    };
    window.__shot = () => {
      if (IB.Look && IB.Look.update) IB.Look.update(1 / 60);
      R.render(false); R.render(false);   // settle per-frame caches (shadow refits), then count one plain frame
      R.renderer.info.reset();
      R.render(false);
      const calls = R.renderer.info.render.calls;
      return { url: R.renderer.domElement.toDataURL('image/png'), calls };
    };
    window.__clear = () => { IB.WeaponDrops.clear(); __step(1 / 60, 30); };
    window.__drop = (id, tier, x, zz) => IB.WeaponDrops.layDown({ id, tier, level: 1 }, x, zz, 0);
    window.__row = (zz) => ['gray', 'green', 'blue', 'purple', 'orange'].map((t, i) => __drop('vanguard', t, __lg.x0 + (i - 2) * 1.8, zz));
    return { x0, zRow, zMax, len: best.len, entry: [z.entry.x, z.entry.z] };
  });
  console.log('lane', JSON.stringify(lane));
  const index = {};
  async function shot(scene, k, label) {
    const r = await pg.evaluate(() => __shot());
    const file = scene + '-' + k + '.png';
    fs.writeFileSync(path.join(outDir, file), Buffer.from(r.url.split(',')[1], 'base64'));
    (index[scene] = index[scene] || []).push({ file, label, calls: r.calls });
  }
  const want = s => !ONLY || ONLY.includes(s);
  const t0 = Date.now();

  // draw calls: the same view with no drops and with the five-tier row in it
  if (want('calls')) {
    await pg.evaluate(() => { __clear(); __cam(__lg.x0, __lg.zRow + 10, 0, -0.05); __step(1 / 60, 2); });
    await shot('calls', 0, '0 drops');
    await pg.evaluate(() => { __row(__lg.zRow); __step(1 / 60, 60); });
    await shot('calls', 1, '5 drops');
    await pg.evaluate(() => { for (let k = 1; k <= 3; k++) __row(__lg.zRow - k * 2.5); __step(1 / 60, 60); });
    await shot('calls', 2, '20 drops');
  }
  // the five tiers, idle, at 4 / 10 / 22 / 45 m
  if (want('dist')) {
    await pg.evaluate(() => { __clear(); __row(__lg.zRow); __step(1 / 60, 90); });
    for (const [k, d] of [[0, 4], [1, 10], [2, 22], [3, 45]]) {
      const dd = Math.min(d, lane.zMax - lane.zRow);
      await pg.evaluate((d) => { __cam(__lg.x0, __lg.zRow + d, 0, d < 6 ? -0.12 : -0.03); __step(1 / 60, 1); }, dd);
      await shot('dist', k, dd + ' m');
    }
  }
  // standing next to and inside the orange beam, and looking down on the row
  if (want('near')) {
    await pg.evaluate(() => { __clear(); __row(__lg.zRow); __step(1 / 60, 90); });
    const ox = lane.x0 + 2 * 1.8;
    await pg.evaluate((ox) => { __cam(ox + 0.4, __lg.zRow + 1.6, 0.25, -0.35); __step(1 / 60, 1); }, ox); await shot('near', 0, '1.6 m');
    await pg.evaluate((ox) => { __cam(ox + 0.15, __lg.zRow + 0.3, 0.4, -0.1); __step(1 / 60, 1); }, ox); await shot('near', 1, 'in the beam');
    await pg.evaluate((ox) => { __cam(ox - 0.3, __lg.zRow + 3, 0.2, 0.55); __step(1 / 60, 1); }, ox); await shot('near', 2, 'looking up');
    await pg.evaluate(() => { __cam(__lg.x0, __lg.zRow + 2.4, 0, -1.0); __step(1 / 60, 1); }); await shot('near', 3, 'looking down');
  }
  // a blue and an orange gun land 5 m away: frames at fixed times after the drop
  if (want('spawn')) {
    await pg.evaluate(() => { __clear(); __cam(__lg.x0, __lg.zRow + 5, 0, -0.1); __step(1 / 60, 1); __drop('vanguard', 'blue', __lg.x0 - 1, __lg.zRow); __drop('vanguard', 'orange', __lg.x0 + 1, __lg.zRow); });
    let at = 0;
    for (const [k, t] of [[0, 0.017], [1, 0.067], [2, 0.133], [3, 0.2], [4, 0.3], [5, 0.45], [6, 0.7], [7, 1.0]].map(a => a)) {
      const n = Math.round((t - at) * 60); at += n / 60;
      await pg.evaluate((n) => __step(1 / 60, n), n);
      await shot('spawn', k, Math.round(at * 1000) + ' ms');
    }
  }
  // the idle pulse: an orange gun at 5 m over 2.8 s
  if (want('idle')) {
    await pg.evaluate(() => { __clear(); __cam(__lg.x0, __lg.zRow + 5, 0, -0.1); __drop('vanguard', 'orange', __lg.x0, __lg.zRow); __step(1 / 60, 120); });
    for (let k = 0; k < 8; k++) { await pg.evaluate(() => __step(1 / 60, 21)); await shot('idle', k, (k * 0.35).toFixed(2) + ' s'); }
  }
  // walking up to a purple gun from 30 m
  if (want('walk')) {
    await pg.evaluate(() => { __clear(); __drop('vanguard', 'purple', __lg.x0, __lg.zRow); __step(1 / 60, 90); });
    const ds = [30, 22, 16, 11, 7, 4.5, 2.6, 1.4].map(d => Math.min(d, lane.zMax - lane.zRow));
    for (let k = 0; k < ds.length; k++) {
      await pg.evaluate((d) => { __cam(__lg.x0 + 0.2, __lg.zRow + d, 0.05, d < 4 ? -0.3 : -0.06); __step(1 / 60, 12); }, ds[k]);
      await shot('walk', k, ds[k] + ' m');
    }
  }
  // E on a green gun at 2 m (taken through WeaponDrops.take), then frames after it
  if (want('pickup')) {
    await pg.evaluate(() => {
      __clear(); const G = IB.Game; G.slot.arsenal = G.slot.arsenal.filter(k => k !== 'vanguard');
      __cam(__lg.x0, __lg.zRow + 2.2, 0, -0.3); __drop('vanguard', 'green', __lg.x0, __lg.zRow); __drop('vanguard', 'purple', __lg.x0 + 2.2, __lg.zRow - 1.5); __step(1 / 60, 90);
    });
    await shot('pickup', 0, 'before');
    await pg.evaluate(() => { const d = IB.WeaponDrops.list.find(q => q.on && q.tier === 'green'); IB.WeaponDrops.take(d, IB.Game); });
    let at = 0;
    for (const [k, t] of [[1, 0.017], [2, 0.067], [3, 0.133], [4, 0.2], [5, 0.3], [6, 0.45], [7, 0.7]]) {
      const n = Math.round((t - at) * 60); at += n / 60;
      await pg.evaluate((n) => __step(1 / 60, n), n);
      await shot('pickup', k, '+' + Math.round(at * 1000) + ' ms');
    }
  }
  // a swap lays the old gun on the new one's spot: two drops on one spot (and a third beside), the camera strafing
  if (want('overlap')) {
    await pg.evaluate(() => { __clear(); __drop('vanguard', 'orange', __lg.x0, __lg.zRow); __drop('vanguard', 'blue', __lg.x0, __lg.zRow); __drop('vanguard', 'purple', __lg.x0 + 0.5, __lg.zRow - 0.4); __step(1 / 60, 90); });
    for (let k = 0; k < 6; k++) {
      await pg.evaluate((k) => { __cam(__lg.x0 - 1.5 + k * 0.6, __lg.zRow + 6, -0.25 + k * 0.1, -0.08); __step(1 / 60, 2); }, k);
      await shot('overlap', k, 'strafe ' + k);
    }
  }
  fs.writeFileSync(path.join(outDir, 'shots.json'), JSON.stringify({ plan: PLAN, tier: TIER, look: process.env.LOOK || 'on', lane, scenes: index }, null, 1));
  console.log('done', Math.round((Date.now() - t0) / 1000) + 's', Object.keys(index).map(k => k + ':' + index[k].length).join(' '), 'calls', JSON.stringify(index.calls ? index.calls.map(c => c.calls) : []), logs.slice(0, 4).join(' | '));
  await browser.close(); server.close();
  process.exit(logs.length ? 1 : 0);
})();
