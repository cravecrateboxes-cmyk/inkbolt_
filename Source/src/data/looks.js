/* INKBOLT tactical look data (plan: Source/docs/tactical-look/PLAN.md, sections 4 and 6).
   Pure data + resolve(); loads in node for unit tests. A look = defaults <- family preset <- theme entry <- tier.
   Every map gets a correct look with no entry here: resolve() guesses the family from the theme's env (sky or not,
   fog brightness, sun height). A theme entry is tuning on top. Colours are display-referred [r, g, b] 0..1 unless
   named otherwise; light intensities are in the shader's linear light (section 5.4). */
(function (IB) {
  'use strict';
  var LOOKS = IB.LOOKS = {};

  LOOKS.defaults = {
    family: 'urban-ext', type: 'ext-day',
    sunI: 1.5, sunColor: null,                       // null: the theme's env.sunColor or white
    ambSky: [0.55, 0.66, 0.85], ambGround: [0.34, 0.30, 0.27], ambI: 0.40, ambFloor: 0.03,
    albSat: 0.96, albGain: 0.90, albCeil: 0.80,
    fog: { length: 160, far: null, color: null, sunGlow: [1.0, 0.86, 0.66] },   // length: metres to 63% haze at ground level
    ink: { color: '#0C0B10', px: 1.5, base: 0.0045, fade: [45, 110], vmPx: 1.3 },
    sky: { clouds: 0.5, sunDisc: true },
    floor: { cls: 1, gloss: 0.14 },                  // surface class of the code-built floor of this theme
    wet: 0, dust: null, exposure: 1.0,
    grade: { sat: 0.98, contrast: 0.20, lo: [0.96, 1.0, 1.06], hi: [1.05, 1.0, 0.94] },
    bloom: { amount: 0.5, knee: 0.35 }, vignette: 0.35, grain: 0.028,
    grid: { intensity: 1.0, radius: 13, emit: {} },  // emit: { cellName: multiplier }
    indoorAmb: 0.20
  };

  // section 4.4
  LOOKS.families = {
    'mil-ext': { type: 'ext-day', sunI: 1.6, ambI: 0.36, fog: { length: 230, sunGlow: [1.0, 0.84, 0.62] }, dust: 'wind',
      grade: { sat: 0.96, contrast: 0.22, lo: [0.95, 1.0, 1.07], hi: [1.06, 1.0, 0.92] } },
    'urban-ext': { type: 'ext-day', sunI: 1.5, ambI: 0.42, fog: { length: 260 },
      grade: { sat: 0.98, contrast: 0.20, lo: [0.95, 1.0, 1.07], hi: [1.03, 1.0, 0.97] } },
    'wild-ext': { type: 'ext-day', sunI: 1.4, ambI: 0.46, ambGround: [0.30, 0.34, 0.24], fog: { length: 150 }, dust: 'pollen',
      grade: { sat: 1.0, contrast: 0.18, lo: [0.97, 1.0, 1.04], hi: [1.03, 1.0, 0.96] } },
    'ind-int': { type: 'int-ind', ambI: 0.40, indoorAmb: 0.30, ambFloor: 0.025, fog: { length: 110 }, dust: 'beams',
      grade: { sat: 0.95, contrast: 0.22, lo: [0.94, 1.0, 1.08], hi: [1.06, 1.0, 0.92] }, floor: { cls: 1, gloss: 0.2 } },
    'dark-int': { type: 'int-dark', ambI: 0.34, indoorAmb: 0.20, ambFloor: 0.02, fog: { length: 55 }, dust: 'heavy', grid: { intensity: 0.55 },
      grade: { sat: 1.0, contrast: 0.28, lo: [0.93, 1.0, 1.09], hi: [1.05, 1.0, 0.93] }, bloom: { amount: 0.65, knee: 0.3 }, vignette: 0.42 },
    'civic-int': { type: 'int-lit', ambI: 0.50, indoorAmb: 0.55, ambFloor: 0.03, fog: { length: 320 },
      grade: { sat: 0.97, contrast: 0.18, lo: [0.98, 1.0, 1.03], hi: [1.02, 1.0, 0.98] }, floor: { cls: 10, gloss: 0.45 }, vignette: 0.28 },
    'giant-room': { type: 'int-lit', ambI: 0.55, indoorAmb: 0.60, ambSky: [0.80, 0.74, 0.66], ambGround: [0.40, 0.33, 0.27], ambFloor: 0.05,
      fog: { length: 420, sunGlow: [1.0, 0.88, 0.70] }, dust: 'motes', floor: { cls: 4, gloss: 0.22 },
      grade: { sat: 1.0, contrast: 0.16, lo: [0.99, 1.0, 1.02], hi: [1.04, 1.0, 0.95] }, vignette: 0.28 }
  };

  // section 8: family and scene type of every theme; pilots carry rough tuning (final tuning is Stage 10)
  LOOKS.themes = {
    mountains: { family: 'wild-ext', type: 'ext-snow', albCeil: 0.80, sunI: 0.85, ambI: 0.38, fog: { length: 170 }, floor: { cls: 13, gloss: 0.25 } },
    smallcity: { family: 'urban-ext', type: 'ext-day' },
    classroom: { family: 'giant-room', type: 'int-lit' },
    office: { family: 'civic-int', type: 'int-lit' },
    bedroom: { family: 'giant-room', type: 'int-lit', floor: { cls: 4, gloss: 0.24 }, ambI: 0.66, indoorAmb: 0.72, albSat: 1.0, grade: { sat: 1.06, contrast: 0.14 } },
    coalmine: { family: 'dark-int', type: 'int-dark' },
    castle: { family: 'urban-ext', type: 'ext-day', floor: { cls: 8, gloss: 0.08 } },
    city2: { family: 'urban-ext', type: 'ext-dusk' },
    factory: { family: 'ind-int', type: 'int-ind' },
    livingroom: { family: 'giant-room', type: 'int-lit' },
    garden: { family: 'wild-ext', type: 'ext-day', floor: { cls: 7, gloss: 0.06 } },
    factory2: { family: 'ind-int', type: 'int-ind' },
    island: { family: 'wild-ext', type: 'ext-day', floor: { cls: 6, gloss: 0.04 } },
    mall: { family: 'civic-int', type: 'int-lit', floor: { cls: 10, gloss: 0.40 }, ambI: 0.42, indoorAmb: 0.45, grid: { intensity: 0.72 }, grade: { sat: 1.0, contrast: 0.22 } },
    police: { family: 'ind-int', type: 'int-ind' },
    grove: { family: 'wild-ext', type: 'ext-day', floor: { cls: 6, gloss: 0.04 } },
    spire: { family: 'civic-int', type: 'int-lit' },
    foundry: { family: 'ind-int', type: 'int-ind' },
    parking: { family: 'ind-int', type: 'int-ind', wet: 0.5 },
    hotel: { family: 'civic-int', type: 'int-lit' },
    techhq: { family: 'civic-int', type: 'int-lit' },
    cargoship: { family: 'mil-ext', type: 'ext-day', floor: { cls: 3, gloss: 0.3 }, wet: 0.3 },
    datacenter: { family: 'ind-int', type: 'int-ind', floor: { cls: 10, gloss: 0.4 }, grid: { emit: {} } },
    downtown: { family: 'urban-ext', type: 'ext-day', floor: { cls: 12, gloss: 0.12 }, sunI: 1.35, ambI: 0.38 },
    highrise: { family: 'civic-int', type: 'int-lit' },
    gemmine: { family: 'dark-int', type: 'int-dark' },
    megastore: { family: 'ind-int', type: 'int-lit' },
    townhomes: { family: 'urban-ext', type: 'ext-day' },
    arctic: { family: 'dark-int', type: 'int-dark', floor: { cls: 13, gloss: 0.3 } },
    resort: { family: 'wild-ext', type: 'ext-day' },
    scrapyard: { family: 'mil-ext', type: 'ext-night', sky: { sunDisc: false }, sunI: 0.6, ambI: 0.25, wet: 0.5 },
    seabase: { family: 'dark-int', type: 'int-dark', wet: 0.4 },
    stronghold: { family: 'mil-ext', type: 'ext-dusk', sky: { sunDisc: false }, sunI: 1.5, ambI: 0.38, ambSky: [0.62, 0.60, 0.72], ambGround: [0.52, 0.40, 0.30], sunColor: '#FFD6AE', indoorAmb: 0.8, grid: { intensity: 2.0 }, floor: { cls: 1, gloss: 0.12 }, albSat: 1.0, fog: { length: 260, sunGlow: [1.0, 0.72, 0.48] } },
    airport: { family: 'civic-int', type: 'int-lit' },
    frontier: { family: 'wild-ext', type: 'ext-day' },
    academy: { family: 'civic-int', type: 'int-lit' },
    mossgarden: { family: 'wild-ext', type: 'ext-day' },
    pelagic: { family: 'mil-ext', type: 'ext-day', floor: { cls: 3, gloss: 0.3 } },
    icecream: { family: 'civic-int', type: 'int-lit', ambI: 0.70, indoorAmb: 0.70 },
    venetian: { family: 'urban-ext', type: 'ext-day' },
    metro: { family: 'dark-int', type: 'int-dark', wet: 0.2, ambI: 0.24, indoorAmb: 0.16, grid: { intensity: 0.36 }, floor: { cls: 10, gloss: 0.35 } },
    toyfactory: { family: 'ind-int', type: 'int-lit', ambI: 0.55, indoorAmb: 0.55 },
    airfield7: { family: 'mil-ext', type: 'ext-day', floor: { cls: 12, gloss: 0.12 } },
    riviera: { family: 'civic-int', type: 'int-lit' },
    observatory: { family: 'mil-ext', type: 'ext-dusk', sky: { sunDisc: false } },
    toytown: { family: 'urban-ext', type: 'ext-day' }
  };

  // section 6: what each tier draws. Tiers change quality, never the lighting design (hard rule 5).
  LOOKS.tiers = {
    high:   { shadow: 4096, shadowType: 'pcfsoft', shadowSpan: 70, detail: 2, normalDetail: true, flashes: 4, post: true, msaa: 4, bloom: 5, vignette: true, dust: 1, density: 1 },
    medium: { shadow: 2048, shadowType: 'pcf', shadowSpan: 70, detail: 1, normalDetail: true, flashes: 4, post: true, msaa: 2, bloom: 3, vignette: true, dust: 1, density: 0.75 },
    low:    { shadow: 1024, shadowType: 'basic', shadowSpan: 45, detail: 0, normalDetail: false, flashes: 2, post: false, msaa: 0, bloom: 0, vignette: false, dust: 0.4, density: 0.5 },
    potato: { shadow: 0, shadowType: 'none', shadowSpan: 0, detail: -1, normalDetail: false, flashes: 1, post: false, msaa: 0, bloom: 0, vignette: false, dust: 0, density: 0.25 }
  };

  function isObj(v) { return v && typeof v === 'object' && !Array.isArray(v); }
  function merge(dst, src) {
    if (!src) return dst;
    for (var k in src) {
      if (isObj(src[k])) dst[k] = merge(isObj(dst[k]) ? dst[k] : {}, src[k]);
      else if (Array.isArray(src[k])) dst[k] = src[k].slice();
      else if (src[k] !== undefined) dst[k] = src[k];
    }
    return dst;
  }
  function lum(hex) {
    var h = String(hex || '#888888').replace('#', ''), n = parseInt(h.length === 3 ? h.replace(/./g, '$&$&') : h, 16);
    return (0.2126 * ((n >> 16) & 255) + 0.7152 * ((n >> 8) & 255) + 0.0722 * (n & 255)) / 255;
  }

  // a theme with no entry (a future map): family and scene type from its env
  LOOKS.guess = function (env) {
    env = env || {};
    var fog = env.fog || {};
    if (!env.sky) {
      var l = lum(fog.color || env.clear);
      if (l < 0.28) return { family: 'dark-int', type: 'int-dark' };
      if (l < 0.55) return { family: 'ind-int', type: 'int-ind' };
      return { family: 'civic-int', type: 'int-lit' };
    }
    var s = env.sun || [0.42, 0.82, 0.38], L = Math.sqrt(s[0] * s[0] + s[1] * s[1] + s[2] * s[2]) || 1;
    var up = s[1] / L;
    if (lum(env.sky[0]) < 0.2) return { family: 'mil-ext', type: 'ext-night' };
    return { family: 'urban-ext', type: up < 0.5 ? 'ext-dusk' : 'ext-day' };
  };

  // defaults <- family <- theme (deep merge); env is the theme's env (used when the theme has no entry)
  LOOKS.resolve = function (themeId, env) {
    var t = LOOKS.themes[themeId] || LOOKS.guess(env);
    var fam = t.family || LOOKS.defaults.family;
    var out = merge(merge(merge({}, LOOKS.defaults), LOOKS.families[fam] || {}), t);
    out.family = fam; out.themeId = themeId; out.guessed = !LOOKS.themes[themeId];
    return out;
  };
  LOOKS.tier = function (name) { return LOOKS.tiers[name] || LOOKS.tiers.high; };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
