/* INKBOLT theme registry. A theme = one Blender kit family + how ASCII zone symbols become kit pieces, plus its
   environment (sky or indoor ceiling, fog, floor) and its level plans. Each theme lives in its own file
   src/data/themes/<id>.js (bundled into themes.gen.js by tools/build.py) and calls IB.registerTheme(def).

   def = {
     id, name, family: 'kit-<id>', prefix: 'KIT_<ID>_',
     env: {
       sky: ['#top', '#horizon'] | null (indoor: no sky dome),   clear: '#hex' (background when sky is null),
       fog: { color: '#hex', near: 40, far: 120 },
       sun: [x, y, z] (light direction, optional),
       ceiling: null | { height: 4, color: '#hex', light: 'PieceName' (optional), every: 4 },
       clouds: true|false
     },
     floor: { color: '#hex', lines: [{ dir: 'x'|'z', every: 2, width: 0.05, color: '#hex', y: 0.01 }], trail: '#hex' },
     wall: { height: 3, roof: '#hex', faceOpen: bool,
             facing: 'open' (turn each module's +Z face toward its single open side: S/N/E/W; corners keep 0),
             pieces: ['Wall_A', ...] | choose: function (c, r, horiz, corner, hash, grid, face) -> name | null (no module) },
             (face = 'S'|'N'|'E'|'W' open side, 'corner' (two adjacent open sides) or 'none')
             (grid: {w, h, at(c, r)}; c/r = cell; modules face +/-Z and are turned 90 for vertical runs; with faceOpen the
              module's +Z face (= Blender -Y face) is turned toward the open side, so one-sided walls face the room)
     symbols: {                    // any ASCII symbol except the built-ins below
       '=': { pieces: [...], h: 1, rotate: 'run'|'random90'|<radians>, stack: { piece, chance, h }, collide: true },
       'K': { size: [w, d], pieces: [...], h: 1.4, flip: true },   // multi-cell prefab tiled over each block of K
                                                                  // (turn: <radians> turns every prefab, e.g. Math.PI)
       'p': { pieces: [...], collide: false }
     },
     gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2,     // 3 m wide opening, shutter rolls up; the frame
             dress: ['GateBooks'] (optional pieces placed with the frame) },
                                                                          // must close the trail end (|x| <= 2.5, full trail
                                                                          // wall height) and may carry _COL boxes
     trail: { wall: 'TrailWall', height: 2.6, variants: ['TrailWall_B', ...] },   // 1 m wall module along the trail;
                                                                          // optional variants are mixed in per module
     hatch: 'Hatch', stand: 'Crate',                                      // exit pad; what new weapons lean on
     backdrop: { ring: [{ piece, count, radius: [a, b], scale: [a, b], y: 0 }] } | null,
     allPieces: function () -> every piece name the theme can place (unit test checks they exist and fit budgets),
     budget: { prop: 1200, landmark: 4000, total: 60000 },
     levels: { '<planId>': { name, intro, zones: [{ map, waves }] } }    // registered into IB.LEVEL_PLANS
   }
   Built-in symbols (all themes): # wall (theme.wall), S spawn can, P entry, E entry gate, G exit gate,
   a ammo, h health, . floor.
   Collision: a piece node may carry empty children named <Piece>_COL<n> (Blender cube empties; position = box centre,
   scale = half extents); otherwise the cell (or prefab footprint) up to `h` is solid. Boxes may float (e.g. a bed
   frame): robots and the player walk under boxes whose bottom is above 1.2 m. */
(function (IB) {
  'use strict';
  IB.THEME_DEFS = IB.THEME_DEFS || {};
  IB.LEVEL_PLANS = IB.LEVEL_PLANS || {};
  IB.registerTheme = function (def) {
    def.prefix = def.prefix || ('KIT_' + def.id.toUpperCase() + '_');
    def.family = def.family || ('kit-' + def.id);
    IB.THEME_DEFS[def.id] = def;
    Object.keys(def.levels || {}).forEach(function (pid) {
      var L = def.levels[pid];
      L.id = pid; L.themeId = def.id;
      IB.LEVEL_PLANS[pid] = L;
    });
    return def;
  };
  // full kit name for a short piece name ('Crate' -> 'KIT_TOYTOWN_Crate'); names that already carry a prefix pass through
  IB.themePiece = function (theme, n) {
    if (IB.Assets && IB.Assets.geo && IB.Assets.geo[theme.prefix + n]) return theme.prefix + n;   // the theme's own piece wins over a common name
    return /^(KIT_|BOT_|WPN_|PICKUP_)/.test(n) || /^(SpawnCan|TrailArrow|Hill|Tree|Cloud_[ABC]|InkChunk_\d)$/.test(n) ? n : theme.prefix + n; };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
