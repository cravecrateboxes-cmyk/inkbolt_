// INKBOLT screenshot check (section 9). Run: node tests/e2e/screens.spec.js [path-to-html]
// Captures every built screen at phone upright, phone sideways and desktop, rotates while open,
// and checks: no horizontal overflow, buttons inside the viewport/safe area, tap targets >= 48 px on touch.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const TARGET = process.argv[2] || 'Play Inkbolt.html';
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;   // e.g. ONLY=hud-combat,loading for a quick pass
const VIEW_ONLY = process.env.VIEWS ? process.env.VIEWS.split(',') : null;
const OUT = path.join(__dirname, 'screens');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const VIEWS = [
  { name: 'phone-upright', w: 390, h: 844, touch: true, rot: { w: 844, h: 390 } },
  { name: 'phone-sideways', w: 844, h: 390, touch: true, rot: { w: 390, h: 844 } },
  { name: 'desktop', w: 1920, h: 1080, touch: false }
];
let failures = 0;
const report = [];
function check(name, ok, info) { const line = (ok ? 'PASS ' : 'FAIL ') + name + (info ? '  ' + info : ''); console.log(line); report.push(line); if (!ok) failures++; }

function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'text/javascript' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

// combat HUD with fake weapon/radar data. game.js keeps calling HUD.ammo/slots/health every frame, so those are
// pinned for the screenshot (the page is thrown away after).
async function combatHud(pg, o) {
  await pg.evaluate(() => { __TEST__.start(); __TEST__.forceWaves(); });
  await pg.waitForFunction(() => __TEST__.state().alive >= 1, null, { timeout: 30000 });
  await pg.evaluate((o) => {
    const G = IB.Game, H = IB.HUD, p = G.player; G.player.protect = 99;
    const live = IB.AI.robots.filter(r => r.on);
    if (live[0]) { live[0].x = p.x + 1.2; live[0].z = p.z - 6; }
    const hp = o.hp || 64, noop = () => {};
    H.health(hp, 100); H.health = noop; H.ammo = noop;
    H.weapon({ id: 'rivet', name: 'AR-22 Rivet', cls: 'rifle', mag: o.mag, magSize: 30, reserve: 150, reloading: !!o.reloading, reloadFrac: o.reloadFrac || 0 });
    H.slots([{ slot: 1, cls: 'pistol', name: 'P-12 Warden', on: false }, { slot: 2, cls: 'smg', name: 'KV-9 Buzzsaw', on: false }, { slot: 3, cls: 'rifle', name: 'AR-22 Rivet', on: true }]); H.slots = noop;
    H.objective(o.objective || 'Clear the lot · 24 robots');
    const L = G.level, zi = G.zone || 0;
    H.radar({ px: p.x, pz: p.z, yaw: p.yaw, range: 30,
      robots: live.map((r, i) => ({ x: r.x, z: r.z, alert: i % 2 === 0 })),
      gates: L.zones.map(z => ({ x: z.exitGate.x, z: z.exitGate.z, open: z.exitGate.open > 0.5 })),
      pickups: [{ x: p.x - 6, z: p.z + 4, kind: 'health' }, { x: p.x + 8, z: p.z + 2, kind: 'ammo' }],
      exit: L.hatch ? { x: L.hatch.x, z: L.hatch.z } : null });
    H.stamina(0.55, false);
    H.feed('pistol', 'Crawler', 1, 'P-12 Warden'); H.feed('smg', 'Crawler', 1, 'KV-9 Buzzsaw');
    // late events land ~0.3 s before the capture; HUD timers are then frozen so swiftshader frame times can't expire them
    const late = () => { H.feed('rifle', 'Gunner', 2, 'AR-22 Rivet'); H.hit('kill'); H.arc(0.9); H.damageFlash(0.45); H.tick = noop; };
    if (o.late !== false) setTimeout(late, 600); else { H.feed('rifle', 'Gunner', 2, 'AR-22 Rivet'); }
  }, o);
}

// screen setup steps, run in the page
const SCREENS = {
  title: async pg => { await pg.evaluate(() => __TEST__.title()); },
  hud: async pg => {
    await pg.evaluate(() => __TEST__.start());
    await pg.waitForFunction(() => __TEST__.state().alive >= 3, null, { timeout: 20000 });
    await pg.evaluate(() => { const G = IB.Game; G.player.protect = 99; const r = IB.AI.robots.find(r => r.on); if (r) { r.x = G.player.x + 1.2; r.z = G.player.z - 6; } IB.HUD.feed('pistol', 'Crawler', 1); IB.HUD.feed('smg', 'Crawler', 1); IB.HUD.hit('core'); IB.HUD.arc(0.6); });
  },
  // the new HUD API driven with fake data (game.js may not call all of it yet): weapon plate, slots with names, objective,
  // radar from the live robots, stamina, kill feed with weapon names, kill confirm, damage arc and hurt flash.
  'hud-combat': async pg => { await combatHud(pg, { mag: 6 }); },
  // reload progress, new-weapon banner, low health, sliding stamina
  'hud-pickup': async pg => {
    await combatHud(pg, { mag: 0, reloading: true, reloadFrac: 0.6, hp: 22, objective: 'Get to the hatch', late: false });
    await pg.evaluate(() => { IB.HUD.pickup('KV-9 Buzzsaw', 'smg'); IB.HUD.stamina(0.3, true); });
  },
  // walking into the exit waypath: the dim overlay at 0.6
  dim: async pg => { await combatHud(pg, { mag: 24, late: false, objective: 'Follow the arrows to the gate' }); await pg.evaluate(() => IB.HUD.dim(0.6)); },
  // between-levels loading screen
  loading: async pg => {
    await pg.evaluate(() => __TEST__.start()); await pg.waitForTimeout(300);
    await pg.evaluate(() => { IB.HUD.dim(1); IB.Menus.loading({ level: 2, name: 'Backyard', line: 'Bins have taken the lawn. Watch the fence line.', palette: ['#7FD36B', '#FFFFFF', '#FF8A3D', '#B98A5A'] }); IB.Menus.loadingProgress(0.62); });
  },
  eliminated: async pg => { await pg.evaluate(() => __TEST__.start()); await pg.waitForTimeout(300); await pg.evaluate(() => __TEST__.damagePlayer(500)); },
  pause: async pg => { await pg.evaluate(() => __TEST__.start()); await pg.waitForTimeout(300); await pg.evaluate(() => __TEST__.pause()); },
  settings: async pg => { await pg.evaluate(() => { __TEST__.title(); __TEST__.menu('settings'); }); },
  'reset-confirm': async pg => { await pg.evaluate(() => { __TEST__.title(); __TEST__.menu('settings'); __TEST__.menu('reset'); }); },
  results: async pg => {
    await pg.evaluate(() => { __TEST__.start(); });
    await pg.waitForTimeout(300);
    await pg.evaluate(() => { const G = IB.Game; G.slot.gems = 1234567; G.level.zones.forEach(z => { z.state = 'cleared'; }); __TEST__.teleport('hatch'); });
    await pg.waitForFunction(() => __TEST__.state().complete, null, { timeout: 10000 });
  },
  fail: async pg => { await pg.evaluate(() => { __TEST__.start(); }); await pg.waitForTimeout(300); await pg.evaluate(() => { IB.Game.run.retries = 0; __TEST__.damagePlayer(500); }); await pg.waitForFunction(() => /Out of retries/.test(document.getElementById('overlay').textContent), null, { timeout: 10000 }); }
};

async function autoChecks(pg, label, touch) {
  const r = await pg.evaluate((touch) => {
    const W = innerWidth, H = innerHeight, out = { overflow: document.documentElement.scrollWidth > W || document.body.scrollWidth > W, outside: [], small: [], hiddenOpen: [] };
    // an open overlay / loading screen must really be on screen (guards against class-name collisions hiding it)
    ['overlay', 'loading'].forEach(id => { const el = document.getElementById(id); if (el && !el.hidden) { const cs = getComputedStyle(el); if (cs.visibility !== 'visible' || +cs.opacity < 0.5 || cs.display === 'none') out.hiddenOpen.push(id); } });
    const sel = '#overlay .btn, #overlay .seg button, #overlay .switch, #overlay .range' + (touch ? ', #touch .tbtn:not([hidden]), #hud:not([hidden]) .pausebtn' : '');
    const ov = document.getElementById('overlay');
    document.querySelectorAll(sel).forEach(el => {
      if (el.closest('[hidden]')) return;
      const b = el.getBoundingClientRect(); if (!b.width) return;
      const name = (el.textContent || el.id || el.className).trim().slice(0, 24);
      // overlay scrolls: judge vertical position against the scrollable content, horizontal against the viewport
      const top = b.top + (ov.contains(el) ? ov.scrollTop : 0), bottom = top + b.height, maxH = ov.contains(el) ? Math.max(H, ov.scrollHeight) : H;
      if (b.left < -0.5 || b.right > W + 0.5 || top < -0.5 || bottom > maxH + 0.5) out.outside.push(name);
      const min = el.classList.contains('switch') || el.classList.contains('range') ? 44 : 48;
      if (touch && (b.height < min - 0.5 || b.width < min - 0.5)) out.small.push(name + ' ' + Math.round(b.width) + 'x' + Math.round(b.height));
    });
    return out;
  }, touch);
  check(label + ' no horizontal overflow', !r.overflow);
  check(label + ' open overlays visible', r.hiddenOpen.length === 0, r.hiddenOpen.join(', '));
  check(label + ' buttons inside viewport', r.outside.length === 0, r.outside.join(', '));
  if (touch) check(label + ' tap targets >= 48 px', r.small.length === 0, r.small.join(', '));
}

(async () => {
  const server = await serve();
  const url = 'http://localhost:' + server.address().port + '/' + encodeURI(TARGET) + '?autotest=1&plan=greybox';
  const browser = await chromium.launch({ args: ARGS });
  for (const v of VIEWS.filter(v => !VIEW_ONLY || VIEW_ONLY.includes(v.name))) {
    const dir = path.join(OUT, v.name); fs.mkdirSync(dir, { recursive: true });
    for (const name of Object.keys(SCREENS).filter(n => !ONLY || ONLY.includes(n))) {
      const ctx = await browser.newContext({ viewport: { width: v.w, height: v.h }, hasTouch: v.touch, isMobile: v.touch, deviceScaleFactor: 1 });
      const pg = await ctx.newPage(); const logs = [];
      pg.on('pageerror', e => logs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') logs.push(m.text()); });
      await pg.goto(url);
      await pg.waitForFunction(() => window.__TEST__ && IB.Game.mode === 'play', null, { timeout: 30000 });
      await SCREENS[name](pg);
      await pg.waitForTimeout(900);
      await pg.screenshot({ path: path.join(dir, name + '.png') });
      await autoChecks(pg, v.name + '/' + name, v.touch);
      if (v.rot) {
        await pg.setViewportSize({ width: v.rot.w, height: v.rot.h });
        await pg.waitForTimeout(600);
        await pg.screenshot({ path: path.join(dir, name + '-rotated.png') });
        await autoChecks(pg, v.name + '/' + name + ' rotated', v.touch);
      }
      check(v.name + '/' + name + ' no page errors', logs.length === 0, logs.join(' | '));
      await ctx.close();
    }
  }
  await browser.close(); server.close();
  fs.writeFileSync(path.join(OUT, 'report.txt'), report.join('\n') + '\n');
  console.log('\n' + (failures ? failures + ' FAILED' : 'ALL PASSED') + '  screenshots in ' + OUT);
  process.exit(failures ? 1 : 0);
})();
