// INKBOLT HUD / enemy-bar / loader review shots. Run: node tests/e2e/hud-shots.js [path-to-html]
// Writes tests/e2e/review/hud-*.png (combat HUD, hurt + reload + pickup, enemy health bars) and loader-*.png
// at phone upright, phone sideways and desktop. ONLY=hud,bars,loader and VIEWS=desktop narrow it down.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const TARGET = process.argv[2] || 'Play Inkbolt.html';
const OUT = path.join(__dirname, 'review');
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
const VIEW_ONLY = process.env.VIEWS ? process.env.VIEWS.split(',') : null;
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const VIEWS = [
  { name: 'phone', w: 390, h: 844, touch: true },
  { name: 'phone-sideways', w: 844, h: 390, touch: true },
  { name: 'desktop', w: 1920, h: 1080, touch: false }
];
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.css') ? 'text/css' : f.endsWith('.woff2') ? 'font/woff2' : 'text/javascript' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

// robots lined up in front of the player at several distances, some hurt; AI frozen so the frame holds still
async function arena(pg, o) {
  await pg.evaluate(() => { __TEST__.start(); __TEST__.forceWaves(); });
  await pg.waitForFunction(() => __TEST__.state().alive >= 3, null, { timeout: 60000 });
  await pg.waitForTimeout(1600);
  await pg.evaluate((o) => {
    const G = IB.Game, p = G.player, AI = IB.AI; p.protect = 999;
    AI.robots.forEach(r => { if (r.on && r.state !== 'pose') { r.on = false; r.state = 'off'; } });
    const fx = -Math.sin(p.yaw), fz = -Math.cos(p.yaw), rx = Math.cos(p.yaw), rz = -Math.sin(p.yaw);
    const spots = o.spots || [[-1.6, 5, 'crawler', 0.55], [1.4, 8, 'gunner', 0.3], [-3.5, 12, 'bomber', 1], [3.2, 15, 'drone', 0.7], [0.2, 21, 'gunner', 0.45], [-6, 26, 'crawler', 0.8]];
    spots.forEach(([side, fwd, type, frac, rogue], i) => {
      const x = p.x + fx * fwd + rx * side, z = p.z + fz * fwd + rz * side;
      const r = AI.spawn(type, x, z, G.zone || 0, p.x, p.z); if (!r) return;
      r.state = 'chase'; r.st = 0; r.y = r.hy || 0; r.yaw = Math.atan2(p.x - x, p.z - z);
      if (frac < 1) { r.hp = r.maxHp * Math.min(1, frac + 0.25); }
      r._shot = { frac };
      if (rogue && AI.makeRogue) { AI.makeRogue(r, 9); r.state = 'chase'; }   // Handy Helpers ally: teal bar
    });
    IB.AI.update = () => {}; IB.Projectiles.update = () => {};
    // let the bars register the robots, then hit them so the chip segment shows
    setTimeout(() => { AI.robots.forEach(r => { if (r.on && r._shot && r._shot.frac < 1) { r.hp = r.maxHp * r._shot.frac; } }); }, 250);
  }, o || {});
}

async function hudData(pg, o) {
  await pg.evaluate((o) => {
    const G = IB.Game, H = IB.HUD, p = G.player, noop = () => {};
    const hp = o.hp || 64;
    H.health(100, 100); H.health(hp, 100); H.health = noop; H.ammo = noop;
    H.weapon({ id: 'rivet', name: 'AR-22 Rivet', cls: 'rifle', mag: o.mag, magSize: 30, reserve: 150, reloading: !!o.reloading, reloadFrac: o.reloadFrac || 0 });
    if (o.mag !== undefined) H.weapon = noop;
    H.slots([{ slot: 1, cls: 'pistol', name: 'P-12 Warden', on: false }, { slot: 2, cls: 'smg', name: 'KV-9 Buzzsaw', on: false }, { slot: 3, cls: 'rifle', name: 'AR-22 Rivet', on: true }]); H.slots = noop;
    H.objective(o.objective || 'Clear the lot · 24 robots'); H.objective = noop;
    H.stamina(0.55, false); H.stamina = noop;
    H.feed('pistol', 'Crawler', 1, 'P-12 Warden'); H.feed('smg', 'Crawler', 1, 'KV-9 Buzzsaw'); H.feed('rifle', 'Gunner', 2, 'AR-22 Rivet');
    if (o.shield && IB.LootHUD) { IB.LootHUD.shield({ cur: 23, max: 34, charging: false }); IB.LootHUD.shield = noop; }
    if (o.hit) { H.hit('kill'); H.arc(0.9); H.arc(-2.2); H.damageFlash(0.45); }
    setTimeout(() => { H.tick = noop; }, 700);
  }, o);
}

const SHOTS = {
  hud: async pg => { await arena(pg); await hudData(pg, { mag: 22, shield: true, hit: true }); },
  'hud-hurt': async pg => {
    await arena(pg);
    await hudData(pg, { mag: 0, reloading: true, reloadFrac: 0.6, hp: 22, objective: 'Get to the hatch', shield: true });
    await pg.evaluate(() => { IB.HUD.pickup('KV-9 Buzzsaw', 'smg'); IB.HUD.stamina(0.3, true); });
  },
  bars: async pg => {
    await arena(pg, { spots: [[-1.1, 4.5, 'crawler', 0.35], [1.5, 7, 'gunner', 0.62], [-2.6, 10, 'bomber', 0.2], [2.6, 13, 'drone', 0.8], [0.4, 18, 'gunner', 0.5], [-4.5, 24, 'crawler', 0.9], [4.6, 9, 'crawler', 0.75, true]] });
    await hudData(pg, { mag: 18, shield: true });
  },
  loader: async pg => {
    await pg.evaluate(() => { __TEST__.start(); });
    await pg.waitForTimeout(300);
    await pg.evaluate(() => { IB.HUD.dim(1); IB.Menus.loading({ level: 2, name: 'Backyard', line: 'Level 1 cleared · 24 robots · 03:12 · +86 gems' }); IB.Menus.loadingProgress(0.7); });
    await pg.waitForTimeout(1800);
  }
};

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const server = await serve();
  const url = 'http://localhost:' + server.address().port + '/' + encodeURI(TARGET) + '?autotest=1&plan=greybox';
  const browser = await chromium.launch({ args: ARGS });
  let errors = 0;
  for (const v of VIEWS.filter(v => !VIEW_ONLY || VIEW_ONLY.includes(v.name))) {
    for (const name of Object.keys(SHOTS).filter(n => !ONLY || ONLY.includes(n))) {
      const ctx = await browser.newContext({ viewport: { width: v.w, height: v.h }, hasTouch: v.touch, isMobile: v.touch, deviceScaleFactor: 1 });
      const pg = await ctx.newPage(); const logs = [];
      pg.on('pageerror', e => logs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') logs.push(m.text()); });
      await pg.goto(url);
      await pg.waitForFunction(() => window.__TEST__ && IB.Game.mode === 'play', null, { timeout: 30000 });
      await SHOTS[name](pg);
      await pg.waitForTimeout(1100);
      const file = path.join(OUT, (name === 'loader' ? 'loader-' : name === 'bars' ? 'hud-bars-' : name + '-') + v.name + '.png');
      await pg.screenshot({ path: file, timeout: 120000 });
      const info = name === 'loader' ? '' : JSON.stringify(await pg.evaluate(() => IB.HPBars ? IB.HPBars.stats().shown : -1));
      console.log((logs.length ? 'ERR  ' : 'ok   ') + path.relative(ROOT, file) + (info ? '  bars=' + info : '') + (logs.length ? '  ' + logs.join(' | ') : ''));
      if (logs.length) errors++;
      await ctx.close();
    }
  }
  await browser.close(); server.close();
  process.exit(errors ? 1 : 0);
})();
