/* Theme: NOVYX HQ (kit-techhq) -- the headquarters of a (made-up) laptop and software maker on floors 27 - 33 of a
   mid-rise glass tower, about 120 m over the street: lower than the Spire, so the streets, the traffic, the street trees
   and the neighbouring rooftops (roof gardens, plant rooms, solar arrays, a sports court, a crane) read below.
   Built by blender/fam_kit_techhq.py (palette, walls and fit-out) with techhq_props.py (furniture, labs, terrace) and
   techhq_city.py (skyline); zone layers by tools/techhq_zones.py.

   Architecture: each zone is a double-height floor (8 m) in a glass curtain wall (slim black mullions every 3 m with
   white aluminium fins outside, the slab line at 4 m, oak window benches); a mezzanine deck at 4 m ("@layer 4": slab
   3.6 - 4.0) runs along part of every zone, reached by oak stairs and, in the lobby, the bleacher stair. The
   corridors between the zones are the lift lobbies (lift doors with floor numbers, a gallery at 4 m, a stair door),
   and the exit is a glass lift car.
     techhq_lobby  floor 27, reception and showroom: reception desk and the giant NOVYX logo wall (its back is the
                   video wall of the demo stage), the bleacher stair facing the stage, display tables, plinths, pickup
                   lockers, glass briefing pods, an espresso bar; a U-shaped mezzanine with the museum line of laptops
     techhq_eng    floor 29, engineering: dev desks (sit-stand, multi-monitor), scrum boards, the service core with a
                   living green wall / whiteboards / oak / a brand supergraphic, the server closet, meeting pods,
                   phone booths, the hack lounge (arcade line, ping-pong, foosball, console sofa), the micro-kitchen
     techhq_lab    floor 33, hardware lab and design studio under a roof (layer 8 tiles; the zone plan says
                   ceiling: false): prototype benches, 3D printers, hinge-cycle rigs, drop towers, thermal chambers,
                   the anechoic chamber, design tables, material boards, a concept laptop on a turntable, the exploded
                   laptop hanging under a skylight; the executive deck (boardroom, offices) behind the glass wall onto
                   the roof terrace (decking, pergolas, sofas round fire tables, grass planters) open to the sky
   Outside (theme.below, zones.js buildCityBelow): each zone's tower skin from the street up past its roof (the lab is
   the top of a set-back, so its skin stops at the parapet), the street grid 120 m down with cars in the lanes and
   trees on the sidewalks, rooftop detail on the blocks near the tower, the skyline rows of the kit (mostly lower
   buildings, a few towers above us), and hazy towers on the horizon.

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells)
     floor plan / deck                                         @layer 0 (floor finishes)
       N / V oak stair [3,10] north / south   Z bleacher stair [10,10] (north)     q carpet tiles [4,4]   y epoxy [4,4]
       I column under the deck edge  (deck: u deck  r glass rail  i column over the edge  l downlight under the deck)
       R reception [6,3]   Y logo wall [14,2]   K demo stage [8,3]                 w decking [4,4]   z pavers [4,3]
       D display table [4,2]   d plinth   A shelves / pickup lockers [3,1]         @layer 8 (ceiling / roof)
       L lounge [4,3]   b beanbag   o planter   O tree planter [2,2]   p plant       ~ felt baffles [4,4]  : pendant
       M glass meeting pod [4,4]   m phone booth [2,2]   k kitchen counter run      ^ roof tile [4,4] (lab)
       C coffee bar [4,2]   X dev desks [4,2]   B scrum board [2,1]   Q server closet [6,4]   & exploded laptop [8,8]
       g arcade cabinet   T ping-pong [3,2]   F foosball [2,1]   H console lounge [4,3]
       J lab bench [4,2]   j 3D printer   W hinge-cycle rig [2,2]   U drop tower [2,2]   e thermal chamber
       c anechoic chamber [6,6]   x design table [4,2]   s material board [2,1]   t concept turntable [3,3]
       v terrace sofas [4,3]   ! fire table [2,2]   ? pergola [6,4]   = grass planter (run)   $ lamp post
       [ executive desk [4,3]   ] boardroom [8,6]   n sliding doorway in the lab's glass wall (wall.passage)
   Walls (facing: 'open'): perimeter cells get the curtain wall (a mullion module every 3 m, window benches mixed in),
   corner columns, the lift-core cladding by the gates, the terrace's glass windscreen where the floor inside is
   decking or pavers; inside: the lab's glass wall (doors 'n'), the service core's faces (green wall south, boards
   west, oak north, supergraphic east) and plain white cores at junctions. */
(function (IB) {
  'use strict';
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E' || ch === 'n'; }
  function gateCentre(grid, r) {
    var cache = grid._thqGate || (grid._thqGate = {});
    if (cache[r] === undefined) {
      var row = grid.rows ? grid.rows[r] || '' : '', a = -1, b = -1;
      for (var i = 0; i < row.length; i++) if (row[i] === 'G' || row[i] === 'E') { if (a < 0) a = i; b = i; }
      cache[r] = a < 0 ? null : (a + b + 1) / 2;
    }
    return cache[r];
  }
  // the zone's floor-finish layer (terrace decking / pavers mark the open-air part of the lab)
  function terrace(grid, c, r) {
    if (grid._thqL0 === undefined) { grid._thqL0 = null; (grid.layers || []).forEach(function (l) { if (Math.abs(l.y) < 0.001) grid._thqL0 = l; }); }
    var L = grid._thqL0; if (!L || r < 0 || c < 0 || r >= L.h || c >= L.w) return false;
    var ch = L.rows[r] ? L.rows[r][c] : '.';
    return ch === 'w' || ch === 'z';
  }
  var BOARDS = ['Wall_BoardA', 'Wall_BoardB'];
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var W = grid.w, Hh = grid.h, west = c === 0, east = c === W - 1, north = r === 0, south = r === Hh - 1;
    if ((west || east) && (north || south)) return terrace(grid, west ? 1 : W - 2, north ? 1 : Hh - 2) ? 'ScreenCorner' : 'WinCorner';
    if (west || east || north || south) {
      var ic = west ? 1 : east ? W - 2 : c, ir = north ? 1 : south ? Hh - 2 : r, inward = grid.at(ic, ir);
      if (wallish(inward) || face === 'corner' || face === 'none') return 'Core';   // an inner wall meets the facade
      if (north || south) { var g = gateCentre(grid, r); if (g !== null && Math.abs(c + 0.5 - g) < 2.6) return 'GateSide'; }
      if (terrace(grid, ic, ir)) return 'Screen';
      var k = ((north || south ? c : r) - 1) % 3;
      if (k === 1) return 'Win_M';
      return hash(c * 7 + 3, r * 13 + 1) < 0.3 ? 'Win_B' : 'Win_A';
    }
    if (grid.at(c, r) === 'n') return 'GlassDoor';
    if (face === 'corner' || face === 'none') return 'Core';
    if (terrace(grid, c, r - 1) || terrace(grid, c, r + 1)) return 'GlassWall';   // the lab's glass wall onto the terrace
    // the service core: a living wall facing south (the way in), boards west, oak north, the supergraphic east
    if (face === 'S') return 'Wall_Plant';
    if (face === 'W') return BOARDS[r % 2];
    if (face === 'N') return 'Wall_Oak';
    return 'Wall_Graphic';
  }

  // neighbouring buildings, one list per skyline piece (the Blender kit reads this block and builds them; zones.js
  // carries each down to the street with a shaft): [x along the row, front depth, width, depth, colour, window colour,
  // top (m above our floor), style]. Colours are kit palette colours. Most stand lower than us, a few rise above.
  var SKY = /*SKYLINE-BEGIN*/{
    Backdrop_RowA: [
      [-112, 10, 24, 20, '#C9876A', '#4E5F73', -38, 'brick'],
      [-80, 30, 22, 22, '#9DBFD8', '#4E5F73', 46, 'tower'],
      [-46, 8, 26, 22, '#E6E2DA', '#4E5F73', -22, 'garden'],
      [-12, 26, 24, 20, '#5B6E84', '#9DBFD8', -8, 'glass'],
      [22, 8, 22, 20, '#D8C3A0', '#4E5F73', -48, 'court'],
      [56, 30, 26, 22, '#9DBFD8', '#4E5F73', 28, 'tower'],
      [92, 8, 24, 20, '#E6E2DA', '#4E5F73', -30, 'solar'],
      [124, 34, 16, 16, '#C9876A', '#4E5F73', -14, 'crane']
    ],
    Backdrop_RowB: [
      [-114, 18, 24, 22, '#E6E2DA', '#4E5F73', -26, 'solar'],
      [-78, 6, 26, 20, '#C9876A', '#4E5F73', -44, 'brick'],
      [-42, 30, 22, 22, '#5B6E84', '#9DBFD8', 64, 'tower'],
      [-6, 6, 26, 22, '#D8C3A0', '#4E5F73', -34, 'court'],
      [30, 26, 24, 22, '#9DBFD8', '#4E5F73', -12, 'glass'],
      [66, 6, 22, 18, '#E6E2DA', '#4E5F73', -40, 'garden'],
      [100, 28, 24, 22, '#5B6E84', '#9DBFD8', 18, 'hotel']
    ]
  }/*SKYLINE-END*/;
  var BASE = -76;   // the pieces start here; the shafts below them run to the street

  // repaints (zones.js symbol option paint): palette cells of blender/fam_kit_techhq.py (index = place in the list)
  var VIOLET = 23, CORAL = 25, SUN = 26, MINT = 27;
  var FABRIC = { from: [VIOLET], to: [[VIOLET], [MINT], [CORAL]] };                 // lounge sofas in the brand fabrics
  var BAGS = { from: [VIOLET], to: [[VIOLET], [CORAL], [SUN], [MINT]] };           // beanbags
  var INNER = ['Wall_Plant', 'Wall_Oak', 'Wall_Graphic', 'GlassWall', 'GlassDoor'].concat(BOARDS);
  IB.registerTheme({
    id: 'techhq', name: 'NOVYX HQ', family: 'kit-techhq', prefix: 'KIT_TECHHQ_',
    palette: ['#6C4BFF', '#FF5A4E', '#FFC23C', '#2ED3A6'],
    env: {
      // a clear late morning: deep blue overhead, a pale blue-grey haze; haze, fog and the city's depth haze are one colour
      sky: ['#3F8FE6', '#D7E3EC'], fog: { color: '#D7E3EC', near: 110, far: 720, tierScale: true },
      sun: [0.36, 0.62, 0.7],
      far: 1300,
      clouds: { y: [70, 120], count: 5, scale: [2.2, 3.4], lanes: [70, 110], span: 300, speed: 0.8, axis: 'z' },
      ceiling: { height: 8.0, color: '#F3F1EC', light: 'CeilLight', every: 3 }   // lights: lift lobbies only (zones: 'plain' / false)
    },
    // light oak boards running east-west; terrazzo in the lift lobbies (carpet, epoxy and decking come from "@layer 0")
    floor: {
      color: '#E2CBA2', trail: '#E3E0DA', outside: '#D7E3EC',
      lines: [{ dir: 'x', every: 0.25, width: 0.012, color: '#CDB287', y: 0.008 }],
      trailLines: [{ dir: 'x', every: 1.5, width: 0.02, color: '#C9C4BB', y: 0.008 }, { dir: 'z', every: 1.5, width: 0.02, color: '#C9C4BB', y: 0.0105 }]
    },
    wall: { height: 8.0, roof: '#E9E6E0', facing: 'open', choose: chooseWall, passage: { ch: 'n', solid: [[2.7, 8.0]] } },
    symbols: {
      'N': { size: [3, 10], pieces: ['Stair'], face: 0, kind: 'step' },
      'V': { size: [3, 10], pieces: ['Stair'], face: Math.PI, kind: 'step' },
      'Z': { size: [10, 10], pieces: ['Landmark_Bleacher'], face: 0, kind: 'step' },
      'I': { pieces: ['Column_Lo'], kind: 'cover' },
      'R': { size: [6, 3], pieces: ['Landmark_Reception'], face: 0, kind: 'cover' },
      'Y': { size: [14, 2], pieces: ['Landmark_LogoWall'], face: 0, kind: 'wall' },
      'K': { size: [8, 3], pieces: ['Stage'], face: Math.PI, kind: 'step' },
      'D': { size: [4, 2], pieces: ['DisplayTable_A', 'DisplayTable_B'], flip: true, kind: 'cover' },
      'd': { pieces: ['Plinth_A', 'Plinth_B', 'Plinth_C'], rotate: 'random90', kind: 'cover' },
      'A': { size: [3, 1], pieces: ['Shelf_Acc', 'Lockers'], orient: 'wall', kind: 'cover' },
      'L': { size: [4, 3], pieces: ['Lounge'], flip: true, kind: 'cover', paint: FABRIC },
      'b': { pieces: ['BeanBag'], rotate: 'random90', kind: 'cover', paint: BAGS },
      'o': { pieces: ['Planter_A', 'Planter_B'], rotate: 'random90', kind: 'cover' },
      'O': { size: [2, 2], pieces: ['Planter_Tree'], kind: 'cover' },
      'p': { pieces: ['Plant_A', 'Plant_B'], rotate: 'random90', kind: 'cover' },
      'M': { size: [4, 4], pieces: ['Pod_A', 'Pod_B'], flip: true, kind: 'wall' },
      'm': { size: [2, 2], pieces: ['Booth'], orient: 'wall', kind: 'wall' },
      'k': { pieces: ['Counter_Plain', 'Counter_Espresso', 'Counter_Sink', 'Counter_Fridge', 'Counter_Snack', 'Counter_Plain', 'Counter_Fridge'], rotate: 'edge', sequence: true, kind: 'cover' },
      'C': { size: [4, 2], pieces: ['CoffeeBar'], flip: true, kind: 'cover' },
      'X': { size: [4, 2], pieces: ['DevDesk_A', 'DevDesk_B', 'DevDesk_C'], flip: true, kind: 'cover' },
      'B': { size: [2, 1], pieces: ['Scrum'], flip: true, kind: 'cover' },
      'Q': { size: [6, 4], pieces: ['ServerRoom'], orient: 'wall', kind: 'wall' },
      'g': { pieces: ['Arcade_A', 'Arcade_B'], rotate: 'edge', alternate: true, kind: 'cover' },
      'T': { size: [3, 2], pieces: ['PingPong'], flip: true, kind: 'cover' },
      'F': { size: [2, 1], pieces: ['Foosball'], flip: true, kind: 'cover' },
      'H': { size: [4, 3], pieces: ['GameLounge'], orient: 'wall', kind: 'cover' },
      'J': { size: [4, 2], pieces: ['LabBench_A', 'LabBench_B'], flip: true, kind: 'cover' },
      'j': { pieces: ['Printer3D'], rotate: 'edge', kind: 'cover' },
      'W': { size: [2, 2], pieces: ['HingeRig'], flip: true, kind: 'cover' },
      'U': { size: [2, 2], pieces: ['DropTower'], kind: 'cover' },
      'e': { pieces: ['TestChamber'], rotate: 'edge', kind: 'cover' },
      'c': { size: [6, 6], pieces: ['Anechoic'], face: 0, kind: 'wall' },
      'x': { size: [4, 2], pieces: ['DesignTable_A', 'DesignTable_B'], flip: true, kind: 'cover' },
      's': { size: [2, 1], pieces: ['MaterialBoard'], kind: 'cover' },
      't': { size: [3, 3], pieces: ['Landmark_Turntable'], kind: 'cover' },
      'v': { size: [4, 3], pieces: ['Terrace_Sofas'], flip: true, kind: 'cover' },
      '!': { size: [2, 2], pieces: ['FireTable'], kind: 'cover' },
      '?': { size: [6, 4], pieces: ['Pergola'], flip: true, kind: 'cover' },
      '=': { pieces: ['GrassPlanter_A', 'GrassPlanter_B'], rotate: 'run', alternate: true, kind: 'cover' },
      '$': { pieces: ['LampPost'], kind: 'cover' },
      '[': { size: [4, 3], pieces: ['ExecDesk'], face: 0, kind: 'cover' },
      ']': { size: [8, 6], pieces: ['Boardroom'], face: 0, kind: 'wall' },
      // mezzanine
      'u': { deck: { thick: 0.4, color: '#DCC294', edge: '#F4F2EE', under: '#F6F4EF', with: '*' } },
      'r': { pieces: ['Rail'], full: 'RailFull', links: 'ri', post: 'RailPost', kind: 'wall' },
      'i': { pieces: ['Column_Hi'], kind: 'cover' },
      'l': { pieces: ['UnderLight'], collide: false },
      // floor finishes (layer 0)
      'q': { size: [4, 4], pieces: ['Carpet_A', 'Carpet_B'], collide: false },
      'y': { size: [4, 4], pieces: ['Epoxy'], collide: false },
      'w': { size: [4, 4], pieces: ['Decking'], collide: false },
      'z': { size: [4, 3], pieces: ['Pavers'], collide: false },
      // ceiling / roof (layer 8): fittings hang from the ceiling plane; roof tiles and the skylight sit on it
      '~': { size: [4, 4], pieces: ['Baffles_A', 'Baffles_B'], collide: false },
      ':': { pieces: ['Pendant'], collide: false },
      '^': { size: [4, 4], pieces: ['RoofTile', 'RoofTile_Light'], collide: false },
      '&': { size: [8, 8], pieces: ['Landmark_Exploded'], collide: false }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.4, shutterHeight: 3.05 },
    // the lift lobbies: oak and white, lift doors with floor numbers, a gallery at 4 m, a stair door, a green wall
    trail: { wall: 'TrailWall', height: 8.0, variants: ['TrailWall_Lift', 'TrailWall_Lift', 'TrailWall_Plant', 'TrailWall_Stair'], end: 'TrailWall_Plant', endLift: 0.012 },   // lifted clear of the side walls' gallery ledges where they cross
    hatch: 'Hatch', stand: 'Stand',
    // skyline rows: count 4 lands due east, south, west and north of the level (rows A, B, A, B), each facing it
    backdrop: { ring: [
      { piece: 'Backdrop_RowA', pieces: ['Backdrop_RowA', 'Backdrop_RowB', 'Backdrop_RowA', 'Backdrop_RowB'], count: 4, radius: [56, 56], scale: [1, 1], squeezeX: 0.55, face: true }
    ] },
    skyline: SKY, skylineBase: BASE,
    // the city 120 m down (zones.js buildCityBelow)
    below: {
      depth: 120, haze: '#D7E3EC', hazeTop: 0.03, hazeBottom: 0.2, hazeDist: [160, 900, 0.85], hazeMax: 1,
      glass: '#53708E', facade: '#EEF0F2', roof: '#9C978F', street: '#5E5C60',
      blocks: ['#D8B892', '#C98F72', '#A9BCCB', '#DDD3C1', '#B9997E', '#93A6B8', '#E4C3A4', '#AFC0A6'],
      extent: 560, detail: 230, horizon: 1200,
      towerTop: [30, 22, 8.6, 26],           // zone towers (the lab is the set-back's top floor: its skin stops at the parapet)
      bridgeHole: [2.6, -1.15, 8.45],        // the openings in the skins where the lift lobbies join
      winBand: [4, 0.06, 0.97, 1.5, 0.05],   // our skin: floor-to-ceiling glass, slim slab bands and mullions
      topMax: -24,                           // city roofs stay this far below our floor (a mid-rise view: close detail)
      cars: { every: 7.5, colors: ['#F2F2EE', '#2C2F36', '#C8312C', '#3B6FB6', '#9AA2AC', '#F2C230', '#5F6B5A', '#1E2A44'] },
      trees: { every: 7, color: '#6FA352', dark: '#4C7F3E', radius: 230 },
      roofs: { radius: 260 },                // plant rooms, roof gardens, solar rows and skylights on the blocks near us
      shaftTop: BASE + 1,
      skyline: SKY,
      far: { count: 30, radius: [620, 1100], height: [-60, 120], width: [22, 56] }
    },
    budget: { prop: 3600, landmark: 7000, total: 90000 },
    allPieces: function () {
      var out = ['Win_A', 'Win_B', 'Win_M', 'WinCorner', 'ScreenCorner', 'Screen', 'GateSide', 'Core'].concat(INNER.filter(function (n, i) { return INNER.indexOf(n) === i; }),
        ['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Lift', 'TrailWall_Plant', 'TrailWall_Stair', 'CeilLight', 'Hatch', 'Stand',
          'Backdrop_RowA', 'Backdrop_RowB', 'Rail', 'RailFull', 'RailPost']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        var d = sym[ch]; (d.pieces || []).concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out;
    },
    levels: {
      techhq: {
        name: 'NOVYX HQ',
        intro: 'Thirty floors up at NOVYX. Clear the showroom, the engineering floor, then the hardware lab and the roof terrace.',
        zones: [
          // reception and showroom: both floors, the bleacher and the oak stairs; Gunners on the galleries
          { map: 'techhq_lobby', ceiling: 'plain', waves: [
            [['crawler', 22], ['gunner', 7]],
            [['crawler', 9], ['bomber', 2], ['gunner', 6], ['blader', 9]],
            [['crawler', 6], ['drone', 6], ['gunner', 5], ['soldier', 8]],
            [['crawler', 7], ['bomber', 2], ['gunner', 7], ['soldier', 8]]] },
          // engineering floor: desk rows for cover, Blade Bots round the core, Drones over the open floor
          { map: 'techhq_eng', ceiling: 'plain', waves: [
            [['crawler', 23], ['gunner', 7], ['drone', 3]],
            [['crawler', 7], ['bomber', 2], ['gunner', 7], ['blader', 9]],
            [['crawler', 6], ['drone', 7], ['gunner', 6], ['soldier', 8]],
            [['crawler', 7], ['bomber', 2], ['gunner', 7], ['blader', 7], ['soldier', 5]]] },
          // lab, exec deck and the terrace: Soldiers on the deck, Drones in the open air, a heavy last wave
          { map: 'techhq_lab', ceiling: false, waves: [
            [['crawler', 23], ['gunner', 10], ['drone', 3]],
            [['crawler', 7], ['bomber', 2], ['drone', 6], ['gunner', 4], ['soldier', 9]],
            [['crawler', 9], ['gunner', 9], ['drone', 6], ['blader', 10]],
            [['crawler', 10], ['gunner', 11], ['bomber', 2], ['drone', 5], ['soldier', 12], ['blader', 5]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
