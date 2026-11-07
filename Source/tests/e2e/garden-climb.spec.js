// INKBOLT walkable surfaces: robots climb playgrounds. On the Wide Garden Playground level (plan 'garden') the
// player stands on a play deck and ground robots spawned on the lawn must path up the stairs / ramps / bridges
// (layered nav + flow field, zones.js) and climb onto the deck (r.y > 1 m) within a time limit; a Drone keeps flying;
// existing single-layer levels keep a single-layer nav. The render loop is paused and the real Player / AI / projectile
// code is stepped at a fixed 1/60 s (SwiftShader renders far slower than real time), so limits are in game seconds.
// Run (after tools/build.py): node tests/e2e/garden-climb.spec.js
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
async function open(browser, base, plan) {
  const ctx = await browser.newContext({ viewport: { width: 960, height: 540 } });
  const pg = await ctx.newPage();
  pg.logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') pg.logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => pg.logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=' + plan);
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 90000 });
  // pause the render loop; __sim(secs, zone) steps the player, the robots and their bolts at 1/60 s
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    window.__sim = (secs, zi) => {
      const G = IB.Game, p = G.player, dt = 1 / 60, idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      const ctx = { player: p, world: G.level.world, level: G.level, activeZone: zi, hurt: G.hurt, shake: function () { }, onKill: function () { } };
      for (let i = 0; i < Math.round(secs * 60); i++) { IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, ctx); if (IB.Projectiles) IB.Projectiles.update(dt, ctx); IB.AI.updateCorpses(dt); }
    };
    // the player walks forward (yaw: 0 = north, PI / 2 = west) for secs; returns the highest y reached
    window.__walk = (secs, yaw) => {
      const G = IB.Game, p = G.player, dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      let top = p.y; p.yaw = yaw;
      for (let i = 0; i < Math.round(secs * 60); i++) { IB.Player.step(p, inp, G.level.world, dt, null); top = Math.max(top, p.y); }
      return top;
    };
  });
  return pg;
}
// stage: no waves, the player (invulnerable) on a deck at map cell (c, r) of zone zi standing at height y,
// robots of the given types spawned awake at map cells, chasing
async function stage(pg, zi, deck, robots) {
  return pg.evaluate(([zi, deck, robots]) => {
    const G = IB.Game, p = G.player, Z = G.level.zones[zi];
    IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
    G.level.zones.forEach(z => { z.queue.length = 0; z.plan = Object.assign({}, z.plan, { waves: [[]] }); z.wave = 0; });
    p.protect = 1e9; p.health = p.maxHp;
    p.x = Z.ox + deck[0] + 0.5; p.z = Z.oz + deck[1] + 0.5; p.y = deck[2]; p.vx = p.vz = p.vy = 0;
    return robots.map(([type, c, r]) => {
      const x = Z.ox + c + 0.5, z = Z.oz + r + 0.5, slot = __TEST__.spawnRobot(type, x, z);
      const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
      return [type, slot];
    });
  }, [zi, deck, robots]);
}
// step the game in 0.25 s slices for up to secs game seconds; best[i] = the highest r.y robot i reached
async function watch(pg, list, secs, zi, goal) {
  const best = {};
  let last = null, t = 0;
  while (t < secs) {
    last = await pg.evaluate(([list, zi]) => { __sim(0.25, zi); return list.map(([type, slot]) => { const r = IB.AI.types[type].slots[slot]; return { type, on: r.on, x: +r.x.toFixed(2), y: +r.y.toFixed(2), z: +r.z.toFixed(2), fy: +r.fy.toFixed(2), state: r.state }; }); }, [list, zi || 0]);
    t += 0.25;
    last.forEach((r, i) => { best[i] = Math.max(best[i] || 0, r.on ? r.y : 0); });
    if (list.every((_, i) => best[i] > (goal || 1.0))) break;
  }
  return { best, last, secs: t };
}

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  console.log('# walkable surfaces: robots climb the playgrounds (plan garden)');
  const pg = await open(browser, base, 'garden');
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz; let deck = 0; for (let k = 0; k < NC * (N.layers || 1); k++) if (!N.blocked[k] && N.h[k] > 1.0) deck++;
    return { layers: N.layers || 1, deckCells: deck };
  }));
  check('garden zones have a layered nav with walkable deck cells', nav.every(n => n.layers >= 2 && n.deckCells > 20), JSON.stringify(nav));
  const walk = await pg.evaluate(() => IB.Game.level.world.boxes.filter(b => b.walk).length);
  check('playground pieces bring walkable collision boxes', walk > 100, String(walk));
  // the player walks up the play tower's stairs (from the south) and up its climbing wall (from the east)
  const up = await pg.evaluate(() => {
    const G = IB.Game, p = G.player, Z = G.level.zones[0], cx = Z.ox + 14, cz = Z.oz + 22;
    IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
    p.protect = 1e9; p.x = cx; p.z = cz + 4.5; p.y = 0; p.vx = p.vz = p.vy = 0;
    const stairs = __walk(2.5, 0), onDeck = { y: p.y, z: p.z - cz };
    p.x = cx + 4.2; p.z = cz - 1.0; p.y = 0; p.vx = p.vz = p.vy = 0;
    const wall = __walk(2.5, Math.PI / 2);
    return { stairs, onDeck, wall };
  });
  check('the player walks up the stairs onto the deck', up.stairs > 2.05 && Math.abs(up.onDeck.y - 2.1) < 0.05, JSON.stringify(up));
  check('the player climbs the climbing wall onto the deck', up.wall > 2.05, JSON.stringify(up));
  // a Crawler on the lawn, the player up on the play tower's deck (zone 1: tower block at map 9..18 x 17..26)
  let list = await stage(pg, 0, [14, 20, 2.1], [['crawler', 21, 35]]);
  const pre = await pg.evaluate(() => { const p = IB.Game.player; return { y: p.y, floor: IB.Game.level.world.floorAt(p.x, p.z, p.y + 0.1) }; });
  check('the player stands on the deck (2.1 m)', Math.abs(pre.y - 2.1) < 0.05 && Math.abs(pre.floor - 2.1) < 0.01, JSON.stringify(pre));
  let w = await watch(pg, list, 20, 0, 2.0);
  check('a Crawler walks up the stairs onto the play tower deck (y > 1 m, then the 2.1 m deck) within 20 s', w.best[0] > 2.0, 'max y ' + (w.best[0] || 0).toFixed(2) + ' in ' + w.secs.toFixed(2) + ' s ' + JSON.stringify(w.last));
  const smooth = await pg.evaluate(() => { const r = IB.AI.robots.find(q => q.on && q.type === 'crawler'); return r ? { y: r.y, fy: r.fy, gy: r.gy } : null; });
  check('its foot height follows the floor under it', smooth && Math.abs(smooth.gy - smooth.fy) < 0.35, JSON.stringify(smooth));
  // the player stays on the deck after a few seconds of crawler bites (invulnerable): the crawler bites up there
  // a Bomber from the far side of the play area, and a Drone that keeps flying (zone 1)
  list = await stage(pg, 0, [14, 20, 2.1], [['bomber', 6, 39]]);
  await pg.evaluate(() => { IB.AI.robots.forEach(r => { if (r.on && r.type === 'bomber') r.def = Object.assign({}, r.def, { range: -9 }); }); });   // no fuse: we only watch it climb
  w = await watch(pg, list, 25, 0, 2.0);
  check('a Bomber paths round to the stairs and climbs onto the deck within 25 s', w.best[0] > 1.0, 'max y ' + (w.best[0] || 0).toFixed(2) + ' ' + JSON.stringify(w.last));
  const dr = await stage(pg, 0, [14, 20, 2.1], [['drone', 27, 30]]);
  await pg.evaluate(() => __sim(3, 0));
  const d = await pg.evaluate(([t, s]) => { const r = IB.AI.types[t].slots[s]; return { on: r.on, y: r.y, hy: r.hy }; }, dr[0]);
  check('a Drone keeps hovering at its height', d.on && Math.abs(d.y - d.hy) < 0.6, JSON.stringify(d));
  // the big fort (zone 2): get there, then a Crawler climbs to the lookout (2.7 m) over a bridge
  list = await stage(pg, 1, [29, 26, 2.7], [['crawler', 8, 30]]);
  w = await watch(pg, list, 30, 1, 2.6);
  check('a Crawler climbs the fort and crosses a bridge to the 2.7 m lookout within 30 s', w.best[0] > 2.6, 'max y ' + (w.best[0] || 0).toFixed(2) + ' in ' + w.secs + ' s ' + JSON.stringify(w.last));
  // the pirate ship (zone 3): up the gangplank to the main deck (1.2 m) and the steps to the poop deck (2.1 m)
  list = await stage(pg, 2, [10, 14, 2.1], [['crawler', 40, 27]]);
  w = await watch(pg, list, 30, 2, 2.0);
  check('a Crawler boards the pirate ship and climbs to the poop deck within 30 s', w.best[0] > 2.0, 'max y ' + (w.best[0] || 0).toFixed(2) + ' in ' + w.secs + ' s ' + JSON.stringify(w.last));
  // death on a deck: the corpse lies on the deck, the gems drop onto it
  const corpse = await pg.evaluate(([t, s]) => { const r = IB.AI.types[t].slots[s]; const fy = r.fy; __TEST__.wreck(t, s); return fy; }, list[0]);
  await pg.evaluate(() => __sim(0.4, 2));
  const cy = await pg.evaluate(() => { const T = IB.AI.types.crawler; const c = T.corpses.filter(q => q.on).map(q => q.y); return c; });
  check('a robot wrecked on a deck leaves its corpse on the deck', corpse > 1 && cy.length > 0 && cy.every(y => y > corpse - 0.1), 'deck ' + corpse.toFixed(2) + ' corpses ' + JSON.stringify(cy));
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.slice(0, 4).join(' | '));
  await pg.context().close();
  // an existing level keeps its single-layer nav and ground robots
  const pf = await open(browser, base, 'factory');
  const f = await pf.evaluate(() => ({ layers: IB.Game.level.zones.map(z => z.nav.layers || 1), walk: IB.Game.level.world.walkN, tris: IB.Game.level.zones.map(z => z.tris) }));
  check('factory (no walkable pieces) keeps a single-layer nav', f.layers.every(l => l === 1) && f.walk === 0, JSON.stringify(f));
  await pf.context().close();
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
