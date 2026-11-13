// Tactical look diagnostics: node Source/tests/e2e/look-diag.js <plan> [plan ...]
// Prints per plan: post mode, shadow state, light volume (size, lights per zone, bake ms), look family, page errors.
// Env: EXTRA=<query string>, EVAL=<js expression evaluated in the page, printed as JSON>.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const plans = process.argv.slice(2);
(async () => {
  const server = await new Promise(res => { const s = http.createServer((req, r) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'text/javascript' }); r.end(d); }); }).listen(0, () => res(s)); });
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI(process.env.HTML || 'Play Inkbolt.html') + '?autotest=1' + (process.env.EXTRA ? '&' + process.env.EXTRA : '');
  const browser = await chromium.launch({ args: ARGS });
  for (const plan of plans) {
    const pg = await browser.newPage({ viewport: { width: 640, height: 360 } });
    const logs = [];
    pg.on('pageerror', e => logs.push('pageerror: ' + e.message.slice(0, 300)));
    pg.on('console', m => { if (m.type() === 'error' || /^\[look\]/.test(m.text())) logs.push(m.type() + ': ' + m.text().slice(0, 400)); });
    try {
      await pg.goto(base + '&plan=' + plan);
      await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 150000 });
      await pg.waitForTimeout(1500);
      const info = await pg.evaluate((ev) => {
        const L = IB.Look, out = { look: L.on, family: L.cur && L.cur.family, type: L.cur && L.cur.type, guessed: L.cur && L.cur.guessed,
          post: IB.Post && { on: IB.Post.on, mode: IB.Post.mode, w: IB.Post.w, h: IB.Post.h },
          shadows: IB.Shadows && { on: IB.Shadows.on, renders: IB.Shadows.renders },
          grid: IB.LightGrid && IB.LightGrid.info(), calls: __TEST__.state().calls, tris: __TEST__.state().triangles, errors: IB.Game.errors.slice(0, 5) };
        if (ev) { try { out.eval = eval(ev); } catch (e) { out.eval = 'ERR ' + e.message; } }
        return out;
      }, process.env.EVAL || '');
      console.log(plan, JSON.stringify(info));
    } catch (e) { console.log(plan, 'FAIL', e.message.slice(0, 200)); }
    if (logs.length) console.log('  logs:', logs.slice(0, 6).join('\n  '));
    await pg.close();
  }
  await browser.close(); server.close();
})();
