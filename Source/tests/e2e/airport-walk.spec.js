// INKBOLT Meridian International (theme 'airport'): walks the level the way a player does (held W, yaw toward each
// waypoint): check-in -> the security shutter -> the concourse -> duty free -> the exit gate -> the service corridor
// -> the apron -> the hangar; climbs the escalator onto the mezzanine and comes down the stair; climbs the scaffold
// stairs onto the work platforms, walks the wing, climbs to the tail deck at 5.2 m; climbs the stairs truck. Checks
// that robots can path to the same high ground (the layered nav grid's flow field from each zone's entry reaches the
// mezzanine, the docks, the wing, the tail deck and the stairs-truck platform), and that every run piece (glass screens,
// glass and scaffold rails, belt barriers) and the lounge door lies along its line of cells (collision boxes).
// Run (after tools/build.py): node tests/e2e/airport-walk.spec.js
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
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

(async () => {
  const server = await serve();
  const browser = await chromium.launch({ args: ARGS });
  const pg = await (await browser.newContext({ viewport: { width: 640, height: 360 } })).newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error') logs.push(m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto('http://localhost:' + server.address().port + '/Source/dev.html?autotest=1&plan=airport');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 90000 });
  // the explosive canisters the game scatters on open floor are not part of the map: switched off for the walk
  await pg.evaluate(() => { IB.Game.player.protect = 1e9; IB.Game.settings.shake = false; IB.Game.level.world.boxes.forEach(b => { if (b.kind === 'canister') b.on = false; }); });

  // ---- runs along their line of cells: each Full module's box is long along the run, a door along its wall line
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, bad = [], n = { q: 0, "'": 0, '\\': 0, b: 0, n: 0 };
    const FULL = { KIT_AIRPORT_GlassFull: 'q', KIT_AIRPORT_GRailFull: "'", KIT_AIRPORT_YRailFull: '\\', KIT_AIRPORT_BeltFull: 'b' };
    L.world.boxes.forEach(b => {
      const z = L.zones[b.zone]; if (!z) return;
      const ch = FULL[b.piece], door = b.piece === 'KIT_AIRPORT_LoungeDoor';
      if (!ch && !door) return;
      const c = Math.floor((b.x0 + b.x1) / 2 - z.ox), r = Math.floor((b.z0 + b.z1) / 2 - z.oz), ex = b.x1 - b.x0, ez = b.z1 - b.z0;
      if (door) {   // the door's glass line runs east - west (its jambs / lintel: wide along x or thin posts)
        n.n++; if (ez > 0.2) bad.push('door box ' + c + ',' + r);
        return;
      }
      const grids = [z.grid].concat(z.grid.layers.filter(l => Math.abs(l.y - (b.y0)) < 0.3));
      const G = grids.find(g => g.at(c, r) === ch); if (!G) { bad.push('no ' + ch + ' cell under ' + b.piece + ' at ' + c + ',' + r); return; }
      n[ch]++;
      const ew = G.at(c - 1, r) === ch && G.at(c + 1, r) === ch, ns = G.at(c, r - 1) === ch && G.at(c, r + 1) === ch;
      if (ew && !(ex > 4 * ez)) bad.push(ch + ' east-west run, box ' + ex.toFixed(2) + ' x ' + ez.toFixed(2) + ' at ' + c + ',' + r);
      if (ns && !(ez > 4 * ex)) bad.push(ch + ' north-south run, box ' + ex.toFixed(2) + ' x ' + ez.toFixed(2) + ' at ' + c + ',' + r);
    });
    return { n, bad };
  });
  check('run pieces lie along their line of cells (glass, rails, belts) and the lounge door along its glass line', runs.bad.length === 0 && runs.n.q > 20 && runs.n["'"] > 10 && runs.n['\\'] > 10 && runs.n.b > 10 && runs.n.n > 0,
    JSON.stringify(runs.n) + ' ' + runs.bad.slice(0, 5).join(' | '));

  // ---- robots reach the high ground: the flow field from the zone's entry covers each perch
  const reach = await pg.evaluate(() => {
    const L = IB.Game.level, Z = IB.Zones, out = [];
    const perch = [[0, 'mezzanine (cafe deck)', 6.5, 16.5, 4.5], [0, 'escalator landing', 15.5, 16.5, 4.5], [0, 'mezzanine south end', 8.5, 29.5, 4.5],
      [1, 'west forward dock', 31.5, 30.5, 2.6], [1, 'east forward dock', 39.5, 30.5, 2.6], [1, 'starboard wing', 28, 20.3, 2.5],
      [1, 'port wing', 43, 20.3, 2.5], [1, 'west aft dock', 31.5, 15.5, 2.6], [1, 'east aft dock', 38.5, 20.5, 2.6], [1, 'tail deck', 38.5, 10.5, 5.2],
      [1, 'stairs-truck platform', 53, 54.2, 2.6]];
    [0, 1].forEach(zi => {
      const z = L.zones[zi];
      Z.flowField(z, z.entry.x, z.entry.z, 0);
      perch.filter(p => p[0] === zi).forEach(p => {
        const node = Z.navNode(z, z.ox + p[2], z.oz + p[3], p[4]);
        const h = node >= 0 && z.nav.h ? z.nav.h[node] : null;
        out.push({ name: p[1], node, h: h === null ? null : +h.toFixed(2), d: node >= 0 ? z.nav.dist[node] : -1 });
      });
    });
    return out;
  });
  reach.forEach(r => check('robots path to the ' + r.name, r.node >= 0 && r.d > 0 && r.d < 32767 && Math.abs(r.h - 2.6) < 3, JSON.stringify(r)));

  // ---- the walk
  async function clearZone(zi) {
    const t0 = Date.now();
    while (Date.now() - t0 < 40000) {
      if ((await pg.evaluate(() => __TEST__.state().zones))[zi] === 'cleared') return true;
      await pg.evaluate(() => { __TEST__.forceWaves(); __TEST__.killZone(); }); await pg.waitForTimeout(250);
    }
    return false;
  }
  async function walk(zi, pts, label) {
    await pg.keyboard.down('KeyW');
    let ok = true, info = '';
    for (const [x, z, y] of pts) {
      const t0 = Date.now(); let done = false;
      while (Date.now() - t0 < 25000) {
        const s = await pg.evaluate((a) => {
          const G = IB.Game, zn = G.level.zones[a.zi], p = G.player, tx = zn.ox + a.x, tz = zn.oz + a.z;
          p.yaw = Math.atan2(-(tx - p.x), -(tz - p.z)); p.pitch = 0; p.protect = 1e9;
          return { d: Math.hypot(tx - p.x, tz - p.z), y: p.y, x: p.x - zn.ox, z: p.z - zn.oz };
        }, { zi, x, z });
        if (s.d < 0.6) { done = y === undefined || Math.abs(s.y - y) < 0.35; info = 'at ' + x + ',' + z + ' y ' + s.y.toFixed(2); break; }
        info = 'stuck near ' + s.x.toFixed(1) + ',' + s.z.toFixed(1) + ' y ' + s.y.toFixed(2) + ' heading for ' + x + ',' + z;
        await pg.waitForTimeout(60);
      }
      if (!done) { ok = false; break; }
    }
    await pg.keyboard.up('KeyW');
    check(label, ok, info);
    return ok;
  }
  check('zone 1 cleared', await clearZone(0));
  await walk(0, [[39.5, 70], [32.5, 66], [32.5, 52], [39.5, 51], [39.5, 47], [37.5, 45.5], [37.5, 38], [39.5, 34], [41.5, 25], [41.5, 4], [39.5, 2]],
    'zone 1: from the check-in hall through the security shutter, the concourse and duty free to the exit gate');
  await walk(0, [[39.5, 3], [41.5, 4], [41.5, 25], [26.5, 33], [17, 33], [14, 31], [14, 29.6], [14, 18, 4.5], [8.5, 18, 4.5], [4, 30, 4.5], [4, 42, 0]],
    'zone 1: up the escalator onto the mezzanine, along it, down the stair');
  await walk(0, [[4, 44], [5, 47.5], [22, 47.5], [37.5, 45.5], [37.5, 38], [37.5, 33], [41.5, 25], [41.5, 4], [39.5, 2], [39.5, -1], [39.5, -11]], 'zone 1 -> the service corridor');
  const t1 = Date.now();
  while (Date.now() - t1 < 15000 && (await pg.evaluate(() => IB.Game.zone)) !== 1) {
    await pg.evaluate(() => { IB.Game.player.yaw = 0; });
    await pg.keyboard.down('KeyW'); await pg.waitForTimeout(150); await pg.keyboard.up('KeyW');
  }
  check('entered zone 2 through its gate', (await pg.evaluate(() => IB.Game.zone)) === 1);
  check('zone 2 cleared', await clearZone(1));
  await walk(1, [[35.5, 66], [35.5, 46], [31, 43.5], [31, 42.4], [31, 33, 2.6], [31.5, 26, 2.6], [31.5, 21.5], [31.5, 15.5, 2.6]],
    'zone 2: across the apron into the hangar, up the scaffold stair to the starboard dock, over the wing to the aft dock');
  await walk(1, [[31.5, 20], [31.5, 30, 2.6], [31, 34.5, 2.6], [31, 43.5, 0], [37, 44], [40, 43], [40, 42.4], [40, 30, 2.6], [39.5, 21.5],
    [38.5, 20.5, 2.6], [40, 19.4, 2.6], [40, 12.5, 5.2], [38.5, 10.5, 5.2]], 'zone 2: down, up the port stair, over the wing, up to the tail deck at 5.2 m');
  // off the tail deck back to the floor: drop down, then the stairs truck from its back (north) end
  await pg.evaluate(() => { const z = IB.Game.level.zones[1], p = IB.Game.player; p.x = z.ox + 53; p.z = z.oz + 45.5; p.y = 0; p.vx = p.vz = p.vy = 0; });
  await walk(1, [[53, 47.5], [53, 54.2, 2.6]], 'zone 2: up the stairs truck to its platform');
  await walk(1, [[53, 47.5, 0], [51.5, 44], [51.5, 30], [51.5, 4], [35.5, 4], [35.5, 1.5]], 'zone 2: down again and through the hangar to the exit gate');
  check('no page errors', logs.length === 0, logs.slice(0, 3).join(' | '));
  await browser.close(); server.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
