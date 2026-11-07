/* Theme: The Spire (kit-spire) -- a cluster of supertall towers ninety floors up, joined by glass sky-bridges, in the
   warm haze of a late afternoon. Built off the Office Skyscraper (kit-office): blender/fam_kit_spire.py reuses its kit
   class and furniture, the city far below comes from the same engine code (zones.js buildCityBelow), generalised.

   Architecture: every zone is a double-height floor (9 m) wrapped in a white steel DIAGRID curtain wall (diagonals
   crossing every 6 m, nodes at the floor beams, open glazing with glints); corners are mega-columns. The zones are three
   separate towers; the trail corridors between them (and the exit path) are glass sky-bridges hanging over the void.
     spire_lobby    Sky Lobby: a mezzanine ring at 4.5 m ("@layer 4.5"), grand stair + escalators, reception,
                    the Spire's architectural model under a suspended brass halo chandelier ("@layer 9" roof)
     spire_garden   Sky Garden: no flat ceiling (the zone plan says ceiling: false) -- a sloped glass roof of glazed
                    pyramids over cherry and maple trees, hedges, reflecting pools, a timber pergola and lawns
     spire_trading  Trading Floor: trading desks and video walls under a hanging ticker ring, the boardroom and
                    executive desks on a north mezzanine, a giant chrome lightning-bolt sculpture
   Outside (see theme.below and zones.js): the street grid 360 m down under a depth haze that runs into the horizon
   haze (no void below the skyline), every zone's tower drawn from the outside down to the street and up past the
   roof (so a zone that is not drawn still stands there, seen from the others), neighbouring supertalls (Blender
   pieces placed by the backdrop ring, carried down to the street by shafts in the city mesh), low clouds drifting
   below the floor between the towers and the skyline rows, and a far horizon of hazy towers.

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells)
     floor plan                                 @layer 4.5 (mezzanine)          @layer 9 (ceiling / roof)
       N / V escalator [2,10] north / south       u deck   r glass railing         ~ coffer [4,4]   : downlight
       Z / U grand stair [4,10] north / south     i column over the deck edge      H halo chandelier [8,8]
       I column under the deck edge               l downlight under the deck       Y ticker ring [8,8]
       R reception [6,3]   L lounge [4,3]         (props, S, a, h on the deck)     ^ glass roof pyramid [8,8]
       C Spire model sculpture [4,4]              @layer 0 (floor inlays)
       t security turnstile (run)   d totem         x star medallion [8,8]  - border band (run)  g lawn [4,4]
       o planter   O olive planter [2,2]            w timber deck [4,4]     q carpet [4,4]
       B bench [2,1]   p potted plant
       T tree [3,3] (cherry / maple)  = hedge (run)  W reflecting pool [4,4]  Q pergola [6,4]  j lamp  k boulder
       D trading desk [4,2]  M boardroom [8,6]  X executive desk [4,3]  A bolt sculpture [3,3]
   Walls (facing: 'open'): perimeter cells get the diagrid slice of their place in the 6 m bay (Dia_0..Dia_5, the
   slice index mirrored where the engine turns the module), mega-column corners, stone piers by the gates; inside,
   stone / walnut / video-wall / art modules on straight runs and plain cores at junctions. */
(function (IB) {
  'use strict';
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E'; }
  function gateCentre(grid, r) {
    var cache = grid._spireGate || (grid._spireGate = {});
    if (cache[r] === undefined) {
      var row = grid.rows ? grid.rows[r] || '' : '', a = -1, b = -1;
      for (var i = 0; i < row.length; i++) if (row[i] === 'G' || row[i] === 'E') { if (a < 0) a = i; b = i; }
      cache[r] = a < 0 ? null : (a + b + 1) / 2;
    }
    return cache[r];
  }
  var INNER = ['Wall_Stone', 'Wall_Wood', 'Wall_Stone', 'Wall_Art', 'Wall_Wood'];
  var SCREEN = ['Wall_ScreenA', 'Wall_ScreenB'];
  // the diagrid slice of a perimeter cell: bays of 6 run from the first cell after the corner; the engine turns
  // S-wall (face N) and W-wall (face E) modules so their local +X runs against the cell index, hence 5 - k there
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var W = grid.w, Hh = grid.h, west = c === 0, east = c === W - 1, north = r === 0, south = r === Hh - 1;
    if ((west || east) && (north || south)) return 'DiaCorner_' + (north ? 'N' : 'S') + (west ? 'W' : 'E');
    if (west || east || north || south) {
      var inward = west ? grid.at(1, r) : east ? grid.at(W - 2, r) : north ? grid.at(c, 1) : grid.at(c, Hh - 2);
      if (wallish(inward) || face === 'corner' || face === 'none') return 'Core';   // an inner wall meets the facade
      if (north || south) { var g = gateCentre(grid, r); if (g !== null && Math.abs(c + 0.5 - g) < 2.6) return 'GateSide'; }
      var k = ((north || south ? c : r) - 1) % 6;
      if (south || west) k = 5 - k;
      return 'Dia_' + k;
    }
    if (face === 'corner' || face === 'none') return 'Core';
    // a video wall where the zone asks for one (trading floor: inner walls next to a desk or the ticker), else stone
    if (grid._spireScreens === undefined) { var n = 0; for (var rr = 0; rr < Hh; rr++) if ((grid.rows[rr] || '').indexOf('D') >= 0) n++; grid._spireScreens = n > 0; }
    if (grid._spireScreens) return SCREEN[(c + r) % 2];
    return INNER[Math.floor(hash(c * 5 + 1, r * 11 + 7) * INNER.length) % INNER.length];
  }

  // neighbouring supertalls, one list per skyline piece (the Blender kit reads this block and builds the towers from
  // it; zones.js carries each one down to the street with a shaft): [x along the row, front depth, width, depth,
  // colour, window colour, top (m above our floor), style]. Colours are kit palette colours.
  var SKY = /*SKYLINE-BEGIN*/{
    Backdrop_RowA: [
      [-112, 12, 26, 22, '#D8C4A2', '#5A6E86', -48, 'deco'],
      [-76, 34, 20, 20, '#8FB3D1', '#5A6E86', 118, 'needle'],
      [-42, 8, 28, 24, '#E7E4DE', '#5A6E86', -26, 'helipad'],
      [-6, 44, 24, 24, '#4D6178', '#8FB3D1', 74, 'twist'],
      [30, 14, 22, 18, '#9CC7BE', '#5A6E86', 16, 'prism'],
      [66, 36, 26, 22, '#D8C4A2', '#5A6E86', 96, 'deco'],
      [102, 8, 22, 20, '#8FB3D1', '#5A6E86', -64, 'crane'],
      [126, 56, 16, 16, '#E7E4DE', '#5A6E86', 42, 'slab']
    ],
    Backdrop_RowB: [
      [-114, 22, 24, 24, '#8FB3D1', '#5A6E86', 60, 'prism'],
      [-74, 6, 28, 20, '#D8C4A2', '#5A6E86', -38, 'helipad'],
      [-36, 38, 22, 22, '#E7E4DE', '#5A6E86', 132, 'obelisk'],
      [2, 8, 26, 22, '#4D6178', '#8FB3D1', -12, 'garden'],
      [40, 32, 24, 24, '#9CC7BE', '#5A6E86', 88, 'twist'],
      [76, 6, 22, 18, '#D8C4A2', '#5A6E86', 22, 'deco'],
      [114, 30, 24, 22, '#8FB3D1', '#5A6E86', 104, 'needle']
    ]
  }/*SKYLINE-END*/;
  var BASE = -110;   // the pieces start here; the shafts below them run to the street

  IB.registerTheme({
    id: 'spire', name: 'The Spire', family: 'kit-spire', prefix: 'KIT_SPIRE_',
    palette: ['#EEF1F4', '#D9A84E', '#1F6F78', '#F3D7B6'],
    env: {
      // late afternoon ninety floors up: a deep blue zenith over a warm apricot haze; the haze, the fog and the
      // city's depth haze are one colour, so the horizon has no seam
      sky: ['#4F8FD6', '#F3D7B6'], fog: { color: '#F3D7B6', near: 120, far: 900, tierScale: true },
      sun: [-0.42, 0.42, 0.8],
      far: 1500,        // camera far plane: the street 360 m down and the haze ground out to the horizon
      clouds: { y: [-150, -70], count: 4, scale: [3.2, 5.0], lanes: [44, 76], span: 520, speed: 0.9, axis: 'z' },
      ceiling: { height: 9.0, color: '#F4EFE6', light: 'CeilStrip', every: 4 }   // lights: trails only (zones say ceiling 'plain')
    },
    // warm limestone, 1 m joints (rugs, lawns and decking come from each zone's "@layer 0" grid)
    floor: {
      color: '#E6DCCB', trail: '#DCD3C4', outside: '#F3D7B6',
      lines: [{ dir: 'x', every: 1, width: 0.025, color: '#D3C6B1', y: 0.008 }, { dir: 'z', every: 1, width: 0.025, color: '#D3C6B1', y: 0.0105 }]
    },
    wall: { height: 9.0, roof: '#E9E3D8', facing: 'open', choose: chooseWall },
    symbols: {
      'N': { size: [2, 10], pieces: ['Escalator'], face: 0, kind: 'step' },
      'V': { size: [2, 10], pieces: ['Escalator'], face: Math.PI, kind: 'step' },
      'Z': { size: [4, 10], pieces: ['GrandStair'], face: 0, kind: 'step' },
      'U': { size: [4, 10], pieces: ['GrandStair'], face: Math.PI, kind: 'step' },
      'I': { pieces: ['Column_Lo'], kind: 'cover' },
      'R': { size: [6, 3], pieces: ['Landmark_Reception'], kind: 'cover' },
      'L': { size: [4, 3], pieces: ['Lounge_A', 'Lounge_B'], flip: true, kind: 'cover' },
      'C': { size: [4, 4], pieces: ['Landmark_Model'], kind: 'cover' },
      't': { pieces: ['Turnstile'], h: 1.05, rotate: 'run', kind: 'cover' },
      'd': { pieces: ['Totem'], rotate: 'random90', kind: 'cover' },
      'o': { pieces: ['Planter', 'Planter_B'], rotate: 'random90', kind: 'cover' },
      'O': { size: [2, 2], pieces: ['OlivePlanter'], kind: 'cover' },
      'B': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
      'p': { pieces: ['Plant_Fig', 'Plant_Palm', 'Plant_Snake'], rotate: 'random90', kind: 'cover' },
      'T': { size: [3, 3], pieces: ['Tree_Cherry', 'Tree_Maple'], kind: 'cover' },
      '=': { pieces: ['Hedge_A', 'Hedge_B'], h: 1.15, rotate: 'run', alternate: true, kind: 'cover' },
      'W': { size: [4, 4], pieces: ['Pool'], kind: 'cover' },
      'Q': { size: [6, 4], pieces: ['Pergola'], flip: true, kind: 'cover' },
      'j': { pieces: ['Lamp'], kind: 'cover' },
      'k': { pieces: ['Boulder'], rotate: 'random90', kind: 'cover' },
      'D': { size: [4, 2], pieces: ['TradeDesk_A', 'TradeDesk_B'], kind: 'cover' },
      'M': { size: [8, 6], pieces: ['Boardroom'], flip: true, kind: 'wall' },
      'X': { size: [4, 3], pieces: ['Exec'], kind: 'cover' },
      'A': { size: [3, 3], pieces: ['Landmark_Bolt'], kind: 'cover' },
      // mezzanine
      'u': { deck: { thick: 0.4, color: '#E3D8C5', edge: '#EEF1F4', under: '#F4EFE6', with: '*' } },
      'r': { pieces: ['Rail'], full: 'RailFull', links: 'ri', post: 'RailPost', kind: 'wall' },
      'i': { pieces: ['Column_Hi'], kind: 'cover' },
      'l': { pieces: ['UnderLight'], collide: false },
      // floor inlays (layer 0)
      'x': { size: [8, 8], pieces: ['Inlay_Star'], collide: false },
      '-': { pieces: ['Inlay_Band'], rotate: 'run', collide: false },
      'g': { size: [4, 4], pieces: ['Lawn'], collide: false },
      'w': { size: [4, 4], pieces: ['Decking'], collide: false },
      'q': { size: [4, 4], pieces: ['Carpet'], collide: false },
      // ceiling / roof (layer 9): pieces hang from the ceiling plane; glass roof pyramids stand on it
      '~': { size: [4, 4], pieces: ['Coffer'], collide: false },
      ':': { pieces: ['Downlight'], collide: false },
      'H': { size: [8, 8], pieces: ['Landmark_Halo'], collide: false },
      'Y': { size: [8, 8], pieces: ['Landmark_Ticker'], collide: false },
      '^': { size: [8, 8], pieces: ['GlassRoof'], collide: false }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.5, shutterHeight: 3.05 },
    // the sky-bridges: 9 m glass walls on cross-braced white steel, a girder and half the deck slab under the floor
    trail: { wall: 'TrailWall', height: 9.0, variants: ['TrailWall', 'TrailWall_Plant', 'TrailWall_Sign'], end: 'TrailWall' },
    hatch: 'Hatch', stand: 'Stand',
    // skyline rows: count 4 lands due east, south, west and north of the level (rows A, B, A, B), each facing it,
    // rr = level half-length + 60, squeezeX puts the side rows ~90 m from the centre line
    backdrop: { ring: [
      { piece: 'Backdrop_RowA', pieces: ['Backdrop_RowA', 'Backdrop_RowB', 'Backdrop_RowA', 'Backdrop_RowB'], count: 4, radius: [60, 60], scale: [1, 1], squeezeX: 0.55, face: true }
    ] },
    skyline: SKY, skylineBase: BASE,
    // the city 360 m down (zones.js buildCityBelow), generalised from the office tower
    below: {
      depth: 360, haze: '#F3D7B6', hazeTop: 0.04, hazeBottom: 0.22, hazeDist: [200, 1100, 0.8], hazeMax: 1,
      glass: '#4F6F92', facade: '#E9EDF1', roof: '#9A8F86', street: '#6A6466',
      blocks: ['#D9B48E', '#C48C6E', '#9FB2C4', '#D8CDBA', '#B0927A', '#8E9FB2', '#E2B79A', '#A7B8A0'],
      extent: 640, detail: 240, horizon: 1400,   // detailed blocks inside `detail`, simple ones to `extent`, haze ground to `horizon`
      diagrid: [6, 9],                           // our towers: white steel diagrid (bay 6 m, 9 m per diamond) over dark glass
      towerTop: [72, 12, 140, 48],               // each zone's tower continues this far above the floor (the last: the exit core)
      bridges: true,                             // sky-bridges: no set-back blocks between the towers, open void below
      bridgeHole: [2.6, -1.15, 9.45],            // the openings in the towers' skins where the bridges join (girder to roof edge)
      shaftTop: BASE + 1,                        // shafts under the skyline pieces stop just inside their bases
      skyline: SKY,
      far: { count: 34, radius: [700, 1500], height: [-120, 160], width: [24, 60] }
    },
    budget: { prop: 3200, landmark: 6000, total: 90000 },
    allPieces: function () {
      var out = [];
      for (var k = 0; k < 6; k++) out.push('Dia_' + k);
      ['NW', 'NE', 'SE', 'SW'].forEach(function (s) { out.push('DiaCorner_' + s); });
      out = out.concat(['GateSide', 'Core'], INNER.filter(function (n, i) { return INNER.indexOf(n) === i; }), SCREEN,
        ['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Plant', 'TrailWall_Sign', 'CeilStrip', 'Hatch', 'Stand', 'Backdrop_RowA', 'Backdrop_RowB',
          'Rail', 'RailFull', 'RailPost']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        var d = sym[ch]; (d.pieces || []).concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out;
    },
    levels: {
      spire: {
        name: 'The Spire',
        intro: 'Ninety floors up. Take the sky lobby, cross the bridge to the garden, then the trading floor.',
        zones: [
          // Sky Lobby: both floors, the stair and escalators up; Gunners on the rail from the second wave
          { map: 'spire_lobby', ceiling: 'plain', waves: [
            [['crawler', 20], ['gunner', 6]],
            [['crawler', 5], ['bomber', 5], ['gunner', 5], ['blader', 6]],
            [['crawler', 5], ['drone', 5], ['gunner', 4], ['soldier', 6]],
            [['crawler', 5], ['bomber', 5], ['gunner', 5], ['soldier', 7]]] },
          // Sky Garden: trees and hedges, Drones under the glass roof, Blade Bots in the open lawns
          { map: 'spire_garden', ceiling: false, waves: [
            [['crawler', 21], ['gunner', 6], ['drone', 3]],
            [['crawler', 6], ['bomber', 5], ['gunner', 5], ['blader', 7]],
            [['crawler', 5], ['drone', 6], ['gunner', 5], ['soldier', 7]],
            [['crawler', 5], ['bomber', 5], ['gunner', 5], ['blader', 7]]] },
          // Trading Floor: desks for cover, Soldiers on the executive mezzanine, a heavy last wave
          { map: 'spire_trading', ceiling: 'plain', waves: [
            [['crawler', 22], ['gunner', 9]],
            [['crawler', 6], ['bomber', 6], ['drone', 5], ['soldier', 8]],
            [['crawler', 8], ['gunner', 8], ['drone', 5], ['blader', 7]],
            [['crawler', 9], ['gunner', 9], ['bomber', 8], ['drone', 4], ['soldier', 13]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
