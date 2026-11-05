// INKBOLT screenshot check (section 9). Run: node tests/e2e/screens.spec.js [path-to-html]
// Captures every built screen at phone upright, phone sideways and desktop, rotates while open,
// and checks: no horizontal overflow, buttons inside the viewport/safe area, tap targets >= 48 px on touch.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const TARGET = process.argv[2] || 'Play Inkbolt.html';
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

// screen setup steps, run in the page
const SCREENS = {
  title: async pg => { await pg.evaluate(() => __TEST__.title()); },
  hud: async pg => {
    await pg.evaluate(() => __TEST__.start());
    await pg.waitForFunction(() => __TEST__.state().alive >= 3, null, { timeout: 20000 });
    await pg.evaluate(() => { const G = IB.Game; G.player.protect = 99; const r = IB.AI.robots.find(r => r.on); if (r) { r.x = G.player.x + 1.2; r.z = G.player.z - 6; } IB.HUD.feed('pistol', 'Crawler', 1); IB.HUD.feed('smg', 'Crawler', 1); IB.HUD.hit('core'); IB.HUD.arc(0.6); });
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
    const W = innerWidth, H = innerHeight, out = { overflow: document.documentElement.scrollWidth > W || document.body.scrollWidth > W, outside: [], small: [] };
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
  check(label + ' buttons inside viewport', r.outside.length === 0, r.outside.join(', '));
  if (touch) check(label + ' tap targets >= 48 px', r.small.length === 0, r.small.join(', '));
}

(async () => {
  const server = await serve();
  const url = 'http://localhost:' + server.address().port + '/' + encodeURI(TARGET) + '?autotest=1';
  const browser = await chromium.launch({ args: ARGS });
  for (const v of VIEWS) {
    const dir = path.join(OUT, v.name); fs.mkdirSync(dir, { recursive: true });
    for (const name of Object.keys(SCREENS)) {
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
