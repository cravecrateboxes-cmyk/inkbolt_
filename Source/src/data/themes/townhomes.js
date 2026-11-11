/* Theme: Larkspur Glen (kit-townhomes) -- a gated town-house community at midday, overrun. Not Downtown's shop
   blocks nor Small City's main street: two- and three-storey town houses in rows (brick with bracketed cornices, lap
   siding under gable roofs and dormers, stucco under clay-tile front gables, modern brick-and-board houses with front
   garages), porches, stoops and small fenced front yards, rear garage lanes, the clubhouse and its pool, a playground
   and a park, and the stone-and-iron entrance with its gatehouse. Every row repaints its siding, stucco, brick, front
   doors and shutters per house (symbol option `paint`), so no two neighbours match.
     townhomes_1  The gated entrance: the approach road and its sign walls outside the community wall, the gate
                  across the boulevard (gatehouse on the island, boom barriers, the keypad call post, iron gates swung
                  open, a pedestrian gate: landmark), the boulevard's planted median, the clubhouse on Larkspur Lane
                  with its fenced pool deck (loungers, umbrellas), the mailbox kiosk, the first rows of town houses
                  either side of the Commons green that leads to the north gate, a rear garage lane behind each row.
     townhomes_2  Thistle Court: the court between two rows of town houses with a cul-de-sac turnaround at each end,
                  rear garage lanes with bins and parked cars, the lot under construction in the north row (scaffold,
                  framing, a skip, materials: landmark), the park with the playground, swings and the gazebo.
   Walk-in houses (1-6): open front and back doors, a furnished ground floor 0.32 m up (living room at the front,
   kitchen at the back), a stair along the party wall to the upper floor (3.32 m): an open front room with French
   doors onto the balcony over the porch -- a sniper perch over the street -- and a back bedroom. Robots follow the
   player up (walkable stairs, floors and balconies give the zones a layered nav grid). "@layer 0.32" / "@layer 3.32"
   hold pickups on those floors.
   Built by blender/fam_kit_townhomes.py (townhomes_*.py); layouts by tools/townhomes_zones.py. The parked cars and
   the wheelie bins are kit-parking pieces (option `families`), repainted per car.

   Symbols (1 cell = 1 m; prefab sizes are [x, z] cells; built-ins # P S a h G E)
     Town-house lots [6, 12], front to the south / north:  H U siding   J V stucco   K X brick   Q Y garage
       1 4 walk-in siding (+ Int_A)   2 5 walk-in stucco (+ Int_B)   3 6 walk-in brick (+ Int_C)   7 8 under construction
     R the gated entrance [17, 6] (zone 1 landmark)   N sign wall [8, 2]   c clubhouse [14, 11] (front north)
     O pool [12, 6] (a movement bound over the water)  l lounger [1, 2]   u patio table [2, 2]   k pool rules sign
     M mailbox kiosk [4, 3]   p playground [8, 6]   i swings [4, 2]   e see-saw [3, 1]   r spring rider   d sandbox [3, 3]
     Z gazebo [6, 6]   W skip [2, 4]   w lumber [2, 1]   x brick pallet   q cement mixer   % site toilet   & site sign [2, 1]
     @ median bed [3, 6]   A cul-de-sac island [6, 6]
     Runs (links, a post at ends and corners): F picket fence  I iron fence  L community wall  D hedge  f pool fence
       g j pool gate in an E-W / N-S fence line   y site fence
     s lamp  ] hydrant  m post box  v street sign  0 speed sign  9 kids-at-play sign  B bench [2, 1]  n litter bin
     $ transformer  [ AC unit  * grill  } urn  { basketball hoop  < recycling carts  > kid's bike  ? hose reel
     t tree  b columnar tree  z cherry in blossom  ) shrub  ( shrubs [2, 1]
     C parked car [3, 5]  T pickup / van [3, 6]  / wheelie bins [2, 1]   (kit-parking)
     Paint on the road (no collision): - | lane dash along X / Z   ` ! double yellow along X / Z   + ^ stop line X / Z
       ' crosswalk bar along X   o manhole
   "@layer 0" paving (no collision): , sidewalk   ; lawn   : driveway / lane apron   _ stepping-stone path
     = pool deck   ~ rubber mulch   " flower bed
   The wall ('#', the zone edge) is the community wall: coursed stone with an iron railing (2.3 m) inside, a tall
   hedge outside the gate; the cells beside a zone gate are left to the gate's piers. */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2;
  var KP = 'KIT_PARKING_';
  function kp(list) { return list.map(function (n) { return KP + n; }); }
  // house paint jobs: palette cells (blender/townhomes_base.py) sid 8, stu 9, brk 10, door 11, shut 12
  // -> [siding, stucco, brick, door, shutters]
  var HOUSE = { from: [8, 9, 10, 11, 12], to: [
    [8, 9, 10, 11, 12], [13, 18, 21, 23, 27], [14, 19, 22, 24, 12], [15, 20, 10, 25, 28], [16, 9, 21, 26, 27],
    [17, 18, 22, 27, 12], [13, 20, 10, 24, 28], [14, 9, 21, 11, 27], [15, 19, 22, 23, 12], [8, 18, 10, 26, 28],
    [16, 20, 21, 25, 12], [17, 19, 22, 11, 27]] };
  var PAINT = 48;   // kit-parking 'paint' cell; 49 blue 50 yellow 51 green 52 white 53 black 54 silver 55 orange 56 teal 57 purple 58 mint 59 brown
  var CAR = { from: [PAINT], to: [[48], [49], [52], [53], [54], [56], [57], [58], [59], [52], [54], [53], [49], [51]] };
  var CARS = kp(['Sedan', 'Hatchback', 'SUV', 'Sedan', 'SUV_Boot', 'Hatchback', 'Sports', 'SUV', 'CarCovered', 'Sedan_Door']);
  var WALK = { '1': ['Walk_Siding', 'Int_A'], '2': ['Walk_Stucco', 'Int_B'], '3': ['Walk_Brick', 'Int_C'],
    '4': ['Walk_Siding', 'Int_A'], '5': ['Walk_Stucco', 'Int_B'], '6': ['Walk_Brick', 'Int_C'] };
  function lot(piece, face) { return { size: [6, 12], pieces: [piece], face: face, kind: 'cover', paint: HOUSE }; }
  function walkIn(ch) {
    var w = WALK[ch], d = lot(w[0], '123'.indexOf(ch) >= 0 ? 0 : Math.PI), with_ = {};
    with_[w[0]] = [w[1] + '_GF', w[1] + '_UF'];
    d.with = with_;
    return d;
  }
  function flat(pieces, rot, alt) { return { pieces: pieces, collide: false, rotate: rot || 0, alternate: !!alt }; }
  function links(name, set, kind) { return { pieces: [name], full: name + 'Full', post: name + 'Post', links: set, kind: kind || 'cover' }; }

  var SYMBOLS = {
    // town houses
    'H': lot('House_Siding', 0), 'J': lot('House_Stucco', 0), 'K': lot('House_Brick', 0), 'Q': lot('House_Garage', 0),
    'U': lot('House_Siding', Math.PI), 'V': lot('House_Stucco', Math.PI), 'X': lot('House_Brick', Math.PI), 'Y': lot('House_Garage', Math.PI),
    '7': lot('Landmark_Build', 0), '8': lot('Landmark_Build', Math.PI),
    // landmarks and site
    'R': { size: [17, 6], pieces: ['Landmark_Gate'], face: 0, kind: 'cover' },
    'N': { size: [8, 2], pieces: ['EntrySign'], face: 0, kind: 'cover' },
    'c': { size: [14, 11], pieces: ['Clubhouse'], face: Math.PI, kind: 'cover' },
    'O': { size: [12, 6], pieces: ['Pool'], face: 0, kind: 'bound' },
    'l': { size: [1, 2], pieces: ['Lounger'], flip: true, kind: 'cover' },
    'u': { size: [2, 2], pieces: ['PatioTable'], flip: true, kind: 'cover' },
    'k': { pieces: ['PoolSign'], rotate: Math.PI, kind: 'cover' },
    'M': { size: [4, 3], pieces: ['MailKiosk'], face: Math.PI, kind: 'cover' },
    'p': { size: [8, 6], pieces: ['Playground'], face: 0, kind: 'cover' },
    'i': { size: [4, 2], pieces: ['Swings'], face: 0, kind: 'cover' },
    'e': { size: [3, 1], pieces: ['SeeSaw'], face: 0, kind: 'cover' },
    'r': { pieces: ['SpringRider'], rotate: 'random90', kind: 'cover' },
    'd': { size: [3, 3], pieces: ['Sandbox'], face: 0, kind: 'cover' },
    'Z': { size: [6, 6], pieces: ['Gazebo'], face: 0, kind: 'cover' },
    'W': { size: [2, 4], pieces: ['Skip'], flip: true, kind: 'cover' },
    'w': { size: [2, 1], pieces: ['Lumber'], flip: true, kind: 'cover' },
    'x': { pieces: ['Bricks'], rotate: 'random90', kind: 'cover' },
    'q': { pieces: ['Mixer'], rotate: 'random90', kind: 'cover' },
    '%': { pieces: ['SiteToilet'], rotate: 0, kind: 'cover' },
    '&': { size: [2, 1], pieces: ['SiteSign'], face: 0, kind: 'cover' },
    '@': { size: [3, 6], pieces: ['Median'], face: 0, kind: 'cover' },
    'A': { size: [6, 6], pieces: ['Island'], face: 0, kind: 'cover' },
    // runs
    'F': links('Picket', 'F'), 'I': links('Iron', 'I'), 'L': links('Wall', 'LR'), 'D': links('Hedge', 'D'),
    'f': links('PoolFence', 'fgj'), 'y': links('SiteFence', 'y'),
    'g': { pieces: ['PoolGate'], rotate: 0, kind: 'cover' }, 'j': { pieces: ['PoolGate'], rotate: R90, kind: 'cover' },
    // street furniture, yard props, trees
    's': { pieces: ['Lamp'], rotate: 0, kind: 'cover' },
    ']': { pieces: ['Hydrant'], rotate: 'random90', kind: 'cover' },
    'm': { pieces: ['PostBox'], rotate: 0, kind: 'cover' },
    'v': { pieces: ['StreetSign'], rotate: 0, kind: 'cover' },
    '0': { pieces: ['SpeedSign'], rotate: 0, kind: 'cover' },
    '9': { pieces: ['KidsSign'], rotate: 0, kind: 'cover' },
    'B': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
    'n': { pieces: ['TrashCan'], kind: 'cover' },
    '$': { pieces: ['Transformer'], rotate: 'random90', kind: 'cover' },
    '[': { pieces: ['ACUnit'], rotate: 'random90', kind: 'cover' },
    '*': { pieces: ['Grill'], kind: 'cover' },
    '}': { pieces: ['Urn'], kind: 'cover' },
    '{': { pieces: ['Hoop'], rotate: 'random90', kind: 'cover' },
    '<': { pieces: ['Carts'], rotate: 'random90', kind: 'cover' },
    '>': { pieces: ['KidBike'], rotate: 'random90', kind: 'cover' },
    '?': { pieces: ['HoseReel'], rotate: 'random90', kind: 'cover' },
    't': { pieces: ['Tree'], rotate: 'random90', kind: 'cover' },
    'b': { pieces: ['TreeB'], rotate: 'random90', kind: 'cover' },
    'z': { pieces: ['TreeC'], rotate: 'random90', kind: 'cover' },
    ')': { pieces: ['Shrub'], rotate: 'random90', kind: 'cover' },
    '(': { size: [2, 1], pieces: ['Shrubs'], flip: true, kind: 'cover' },
    // kit-parking vehicles and bins
    'C': { size: [3, 5], pieces: CARS, flip: true, kind: 'cover', paint: CAR },
    'T': { size: [3, 6], pieces: kp(['Pickup', 'Van', 'Pickup_B']), flip: true, kind: 'cover', paint: CAR },
    '/': { size: [2, 1], pieces: kp(['Bins']), flip: true, kind: 'cover' },
    // road paint
    '-': flat(['LaneW'], 0), '|': flat(['LaneW'], R90), '`': flat(['LaneY'], 0), '!': flat(['LaneY'], R90),
    '+': flat(['StopLine'], 0), '^': flat(['StopLine'], R90), "'": flat(['Zebra'], 0), 'o': flat(['Manhole']),
    // paving layer
    ',': flat(['Walk', 'WalkB'], 0, true), ';': flat(['Lawn', 'LawnB'], 0, true), ':': flat(['Drive']),
    '_': flat(['Path'], 0), '=': flat(['Deck']), '~': flat(['Mulch']), '"': flat(['Bed'], 0)
  };
  Object.keys(WALK).forEach(function (ch) { SYMBOLS[ch] = walkIn(ch); });

  /* the zone edge: the community wall (stone with an iron railing), a tall hedge south of the gate line on the
     approach (zone 1), stone piers on the corners; the cells either side of a zone gate are the gate's piers */
  function gateRow(grid) {
    if (grid._thGate === undefined) {
      grid._thGate = -1;
      for (var r = 0; r < grid.h && grid._thGate < 0; r++) if (grid.rows[r].indexOf('RRRRRRRRRRRRRRRRR') >= 0) grid._thGate = r;
    }
    return grid._thGate;
  }
  // the single-cell module a '#' cell would get, or null (gate piers), with its open side (zones.js buildWalls rules)
  var DIRS = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
  function solidAt(grid, c, r) { var ch = grid.at(c, r); return ch === '#' || ch === 'G' || ch === 'E'; }
  function faceAt(grid, c, r) {
    var oS = !solidAt(grid, c, r + 1), oN = !solidAt(grid, c, r - 1), oE = !solidAt(grid, c + 1, r), oW = !solidAt(grid, c - 1, r);
    var n = oS + oN + oE + oW;
    return n === 0 ? 'none' : n === 1 ? (oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W') : ((oS || oN) && (oE || oW) ? 'corner' : (oS ? 'S' : 'E'));
  }
  function single(c, r, grid, face) {
    for (var k = -1; k <= 1; k++) {
      var q1 = grid.at(c + k, r), q2 = grid.at(c, r + k);
      if (q1 === 'G' || q1 === 'E' || q2 === 'G' || q2 === 'E') return null;
    }
    if (face === 'corner' || face === 'none') return 'Perim_Pier';
    var g = gateRow(grid);
    return g >= 0 && r > g ? 'Perim_Hedge' : 'Perim';
  }
  /* straight runs of the stone wall are drawn two cells per module (Perim2 reaches over its neighbour on the module's
     local +X: east for a south-facing cell, west for north, north for east, south for west); cells pair by parity */
  var NEXT = { S: [1, 0], N: [-1, 0], E: [0, -1], W: [0, 1] };
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var me = single(c, r, grid, face);
    if (me !== 'Perim' || !NEXT[face]) return me;
    var n = NEXT[face], along = n[0] ? c : r, lead = (along % 2 === 0) === (n[0] + n[1] > 0);
    var pc = lead ? c + n[0] : c - n[0], pr = lead ? r + n[1] : r - n[1];
    var ok = grid.at(pc, pr) === '#' && faceAt(grid, pc, pr) === face && single(pc, pr, grid, face) === 'Perim';
    if (!ok) return 'Perim';
    return lead ? 'Perim2' : null;
  }

  IB.registerTheme({
    id: 'townhomes', name: 'Larkspur Glen', family: 'kit-townhomes', prefix: 'KIT_TOWNHOMES_', families: ['kit-parking'],
    palette: ['#9DB89A', '#B5523B', '#E9DCC0', '#2B3A67'],
    // midday: a clear blue sky, light haze, the sun high in the south-west
    env: { sky: ['#56A6EA', '#DCEFFA'], fog: { color: '#D3E5EF', near: 60, far: 170 }, sun: [-0.35, 0.86, 0.38], clouds: true, ceiling: null },
    floor: { color: '#5E616A', trail: '#B9AE9A', outside: '#78AE58' },
    wall: { height: 2.3, roof: '#9E8F76', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    // between the zones: a brick-walled garden path through an iron gateway
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_C'], height: 3.2 },
    hatch: 'Hatch', stand: 'Lumber',
    backdrop: {
      ring: [
        { piece: 'Backdrop_Trees', count: 16, radius: [14, 22], scale: [0.9, 1.25], face: true, squeezeX: 0.72 },
        { piece: 'Backdrop_Row', count: 12, radius: [28, 36], scale: [0.95, 1.1], face: true, squeezeX: 0.78 },
        { piece: 'Backdrop_Hill', count: 3, radius: [62, 72], scale: [1.0, 1.2], face: true, squeezeX: 0.8 }
      ]
    },
    budget: { prop: 3600, landmark: 6000, total: 60000 },
    allPieces: function () {
      var out = ['Perim', 'Perim2', 'Perim_Hedge', 'Perim_Pier', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch',
        'Backdrop_Trees', 'Backdrop_Row', 'Backdrop_Hill'];
      Object.keys(SYMBOLS).forEach(function (ch) {
        var d = SYMBOLS[ch];
        d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (n.indexOf(KP) !== 0 && out.indexOf(n) < 0) out.push(n); });
        Object.keys(d.with || {}).forEach(function (k) { d.with[k].forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); }); });
      });
      return out;
    },
    // the kit-parking pieces this theme places (tests check they exist in fps-kit-parking.glb)
    parkingPieces: function () {
      var out = [];
      Object.keys(SYMBOLS).forEach(function (ch) { SYMBOLS[ch].pieces.forEach(function (n) { if (n.indexOf(KP) === 0 && out.indexOf(n) < 0) out.push(n); }); });
      return out;
    },
    levels: {
      townhomes: {
        name: 'Larkspur Glen',
        intro: 'The robots took the gated estate overnight. Get through the gate, clear the clubhouse and the rows, then push on to Thistle Court. Use the houses: through the front, out the back, up to the balconies.',
        zones: [
          // the gated entrance: gunners behind the gatehouse and the cars, blade bots through the houses, drones over the pool
          { map: 'townhomes_1', waves: [
            [['crawler', 22], ['gunner', 8], ['drone', 4]],
            [['crawler', 12], ['bomber', 2], ['gunner', 6], ['blader', 6]],
            [['crawler', 10], ['drone', 6], ['gunner', 6], ['soldier', 7]],
            [['crawler', 16], ['bomber', 2], ['gunner', 7], ['soldier', 7], ['blader', 3]],
            [['crawler', 13], ['drone', 5], ['gunner', 8], ['soldier', 7], ['blader', 2]]] },
          // Thistle Court: soldiers on the scaffold and the balconies, blade bots down the garage lanes, a heavy last wave
          { map: 'townhomes_2', waves: [
            [['crawler', 20], ['gunner', 9], ['drone', 4], ['blader', 4]],
            [['crawler', 12], ['bomber', 2], ['gunner', 7], ['soldier', 7]],
            [['crawler', 12], ['drone', 6], ['gunner', 6], ['blader', 4], ['soldier', 4]],
            [['crawler', 13], ['bomber', 2], ['gunner', 8], ['soldier', 6], ['blader', 2]],
            [['crawler', 14], ['drone', 5], ['gunner', 8], ['soldier', 4], ['blader', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
