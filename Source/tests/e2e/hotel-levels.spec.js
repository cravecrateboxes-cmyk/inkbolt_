// INKBOLT The Aurelian (plan 'hotel'): theme.below.levels -- every zone at its own height above the street.
// The outside (city, haze, street dressing, clouds) is one group lifted so the street lies levels[i] under the zone
// the player is nearest; in a service stair the switch happens halfway along it. Only the current and the next zone
// (and the stair between them) are drawn; the zone behind stands at another height. The Spire (no levels) keeps its
// outside at a fixed height and draws the zone behind. Also: the player walks into a suite through its doorway and
// up the lobby's grand stair onto the gallery.
// Run (after tools/build.py): node tests/e2e/hotel-levels.spec.js
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
async function load(pg, base, plan) {
  await pg.goto(base + '?autotest=1&plan=' + plan);
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 90000 });
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    IB.AI.spawn = function () { return null; }; IB.AI.robots.forEach(r => { r.on = false; });
    IB.Game.player.protect = 1e9;
    window.__walk = (pts, secs) => {   // steer the real Player.step along world points
      const G = IB.Game, p = G.player, dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      let k = 0, n = 0, top = 0;
      while (k < pts.length && n++ < secs * 60) {
        const dx = pts[k][0] - p.x, dz = pts[k][1] - p.z;
        if (Math.hypot(dx, dz) < 0.3) { k++; continue; }
        p.yaw = Math.atan2(-dx, -dz);
        IB.Player.step(p, inp, G.level.world, dt, null);
        top = Math.max(top, p.y);
      }
      return { done: k >= pts.length, x: p.x, z: p.z, y: p.y, top };
    };
  });
}

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error') logs.push(m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await load(pg, base, 'hotel');

  const r = await pg.evaluate(() => {
    const G = IB.Game, L = G.level, C = L.theme.below, Z = IB.Zones, out = {};
    const at = (x, z) => { G.player.x = x; G.player.z = z; Z.updateBelow(L, G.player); return L.belowGroup.position.y; };
    out.group = !!L.belowGroup && L.belowGroup.children.some(o => o.name === 'CityBelow');
    out.clouds = L.cloudMeshes.every(m => m.parent === L.belowGroup);
    out.lifts = L.zones.map(z => at(z.ox + z.w / 2, z.oz + z.h / 2));
    out.want = C.levels.map(v => C.depth - v);
    // in the first service stair: the lower zone's height until halfway, the upper zone's after it
    const z0 = L.zones[0], z1 = L.zones[1], top = z1.oz + z1.h, bottom = z0.oz;
    out.stair = [at(L.trails[0].x, bottom - 2), at(L.trails[0].x, top + 2)];
    // the street under the lobby: the city mesh's street plane (its lowest vertex) sits just under the lobby floor
    const city = L.belowGroup.children.find(o => o.name === 'CityBelow'), pos = city.geometry.attributes.position.array;
    let lo = 1e9; for (let i = 1; i < pos.length; i += 3) lo = Math.min(lo, pos[i]);
    at(z0.ox + 10, z0.oz + 10); out.street0 = lo + L.belowGroup.position.y;
    at(z1.ox + 10, z1.oz + 10); out.street1 = lo + L.belowGroup.position.y;
    // drawn zones: the current one and the next; the stair behind is hidden
    Z.setVisible(L, 1);
    out.vis1 = L.zones.map(z => z.group.visible); out.trails1 = L.trails.map(t => t.group.visible);
    Z.setVisible(L, 0);
    out.vis0 = L.zones.map(z => z.group.visible);
    return out;
  });
  check('the outside is one lifted group (city and clouds)', r.group && r.clouds);
  check('each zone lifts the street to its own height', r.lifts.every((v, i) => Math.abs(v - r.want[i]) < 1e-6), JSON.stringify(r.lifts));
  check('in a service stair the street drops halfway along it', Math.abs(r.stair[0] - r.want[0]) < 1e-6 && Math.abs(r.stair[1] - r.want[1]) < 1e-6, JSON.stringify(r.stair));
  check('the street lies just under the lobby floor and 86 m under floor 24', r.street0 > -1 && r.street0 < 0 && Math.abs(r.street1 + 86) < 0.5, r.street0.toFixed(2) + ' / ' + r.street1.toFixed(2));
  check('drawn: this zone and the next, not the one behind', JSON.stringify(r.vis1) === '[false,true,true]' && JSON.stringify(r.vis0) === '[true,true,false]', JSON.stringify([r.vis1, r.vis0, r.trails1]));
  check('the stair behind is not drawn', r.trails1[0] === false && r.trails1[1] === true);

  // walk: into the lobby's west stair foot and up onto the gallery; into a suite on floor 24 through its doorway
  const climb = await pg.evaluate(() => {
    const G = IB.Game, L = G.level, z = L.zones[0], p = G.player;
    p.x = z.ox + 18; p.z = z.oz + 23; p.y = 0; p.vx = p.vz = p.vy = 0;
    return __walk([[z.ox + 18, z.oz + 21], [z.ox + 18, z.oz + 9.5], [z.ox + 18, z.oz + 6]], 20);
  });
  check('up the grand stair onto the 4.5 m gallery', climb.done && Math.abs(climb.y - 4.5) < 0.1, JSON.stringify(climb));
  const suite = await pg.evaluate(() => {
    const G = IB.Game, L = G.level, z = L.zones[1], p = G.player;
    p.x = z.ox + 10; p.z = z.oz + 34; p.y = 0; p.vx = p.vz = p.vy = 0;
    // suite 5 (rows 30-35): doorway cells (7, 32-33); walk in and to the window
    return __walk([[z.ox + 9.5, z.oz + 33], [z.ox + 6.5, z.oz + 33], [z.ox + 3.5, z.oz + 33], [z.ox + 1.6, z.oz + 33.5]], 20);
  });
  check('into an open suite through its doorway, to the window', suite.done, JSON.stringify(suite));

  // the Spire keeps the old behaviour: no lifted group, the zone behind stays drawn
  await load(pg, base, 'spire');
  const sp = await pg.evaluate(() => { const L = IB.Game.level; IB.Zones.setVisible(L, 1); return { g: !!L.belowGroup, vis: L.zones.map(z => z.group.visible) }; });
  check('the Spire: no lifted group, the zone behind still drawn', !sp.g && JSON.stringify(sp.vis) === '[true,true,true]', JSON.stringify(sp));
  check('no page errors', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
