/* Theme: The Aurelian (kit-hotel) -- a grand hotel tower, climbed zone by zone: the street-level lobby, the ballroom
   floor halfway up, the penthouse and sky deck on the roof. blender/fam_kit_hotel.py builds the kit (hotel_*.py),
   tools/hotel_zones.py the zone maps. The city outside is the office tower's / the Spire's (zones.js buildCityBelow)
   with one generic option added: below.levels gives every zone its own height above the street, so the street drops
   away as the player climbs (the outside is lifted when the player is halfway along each service stair).

   Architecture: 9 m floors (double height), stone and gilt. Facades: on the lobby and the ballroom floor 3 m bays of
   a fluted stone pier and an arched bronze window pair (Win_A / Win_B: each cell is one half of the arch), the
   lobby's street front with two revolving doors under the hotel's name; the guest wing's suite windows; on the roof
   floor-to-ceiling bronze glazing with fins. Inside: two-sided panelled walls (walnut wainscot, silk, gilt mouldings,
   sconces, oil paintings, mirrors), bronze lift doors with floor dials, gilt-framed doorways. The service stairs
   between the zones (the trails) are back-of-house corridors: painted block, a drop ceiling, service lifts, hose
   reels and the stencilled floor the stair climbs to (trail.byTrail: 24, 56, ROOF).
     hotel_lobby     Ground floor: the Grand Lobby: a gallery at 4.5 m ("@layer 4.5") on three sides reached by two
                     grand stairs, the reception, the Gilt Bar, lounges, a piano, the flower table on the marble
                     medallion under the great chandelier; the street outside the revolving doors
     hotel_ballroom  Floor 24: the Crystal Ballroom (bandstand, dance floor, banquet tables, chandeliers), a corridor
                     of seven open suites on the west (King, Twin, Salon; walk in, fight through), the foyer on the
                     east windows, the lift lobby on the south, back-of-house on the north
     hotel_sky       Floor 56: the penthouse (bedroom with a fireplace, living rooms, dining, piano, telescopes) and
                     the sky deck under a glass roof: the round sky bar, the infinity pool, cabanas, olives, parasols
   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells)
     floor plan                                     @layer 4.5 (gallery)       @layer 0 (floor)          @layer 9
       Z grand stair [4,10] (rises north)             m deck  r balustrade       x medallion [7,7]         ~ coffer [4,4]
       I column under the gallery edge                i column over the edge     - border band   _ runner [3,1] : downlight
       R reception [6,4]   Q concierge [3,2]          ; light under the deck     ! lobby carpet [4,4]       H chandelier [5,5]
       X the Gilt Bar [8,4]   b bar stool             (L w p O S a h on it)      + corridor carpet [4,4]    Y chandelier [3,3]
       L lounge [4,3] (A / B, upholstery repainted)                              & penthouse carpet [4,4]   ^ glass roof [7,7]
       K grand piano [3,3]   F flower table [3,3]                                % dance floor [3,3]
       c luggage cart   j bell captain   p palm   t topiary                      $ teak deck [4,4]
       O ottoman [2,1]   k console [2,1]   w writing desk [2,1] (both on a wall)
       T banquet table [3,3]   D bandstand [9,4]   e easel   y housekeeping cart [2,1]   v room-service trolley [2,1]
       M / N / W suite [6,6] (King / Twin / Salon; front to the doorway)   n doorway (wall.passage)
       B pool [10,4]   l lounger [1,2]   u parasol   A cabana [3,3]   V sky bar [7,7]   f fire table [2,2]
       o olive [2,2]   = hedge (run)   J living room [5,4]   d dining [5,3]   z four-poster [4,4]   q telescope
       g fireplace [3,1] (on a wall)
     @layer 0.01: 1-6 the suites' brass number plates (on the corridor wall beside each door)
   Walls (facing: 'open'): see chooseWall. */
(function (IB) {
  'use strict';
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E' || ch === 'n'; }
  function kind(grid) {
    if (!grid._hotel) { var s = grid.rows.join(''); grid._hotel = s.indexOf('V') >= 0 ? 'sky' : s.indexOf('D') >= 0 ? 'ball' : 'lobby'; }
    return grid._hotel;
  }
  function gateC(grid, r) {
    var cache = grid._hotelGate || (grid._hotelGate = {});
    if (cache[r] === undefined) {
      var row = grid.rows ? grid.rows[r] || '' : '', a = -1, b = -1;
      for (var i = 0; i < row.length; i++) if (row[i] === 'G' || row[i] === 'E') { if (a < 0) a = i; b = i; }
      cache[r] = a < 0 ? null : (a + b + 1) / 2;
    }
    return cache[r];
  }
  var INNER = ['Wall_Sconce', 'Wall_Plain', 'Wall_Art', 'Wall_Sconce', 'Wall_Mirror', 'Wall_Plain', 'Wall_Art'];
  var SUITE = 'MNW';
  // panelled walls in a rhythm along the run: a pair of sconces every 4 m, a painting or a mirror between them
  function panel(a, hash, c, r) {
    var k = ((a % 4) + 4) % 4;
    if (k === 0) return 'Wall_Sconce';
    if (k === 2) { var h = hash(c * 5 + 1, r * 11 + 7); return h < 0.45 ? 'Wall_Art' : h < 0.7 ? 'Wall_Mirror' : 'Wall_Plain'; }
    return 'Wall_Plain';
  }
  /* The 3 m bays of a facade or a lift wall: a pier, then an arch pair (the two cells' partner sides). N / S walls run
     from the gate outward (the gate, the gate portal's post, then piers and pairs), E / W walls from the north corner.
     Returns { pos: 'side' | 'pier' | 'pair', partner: +1 | -1 along the wall (+c on N / S, +r on E / W), bay } */
  function bay(c, r, grid, ns) {
    if (ns) {
      var g = gateC(grid, r), m = g === null ? grid.w / 2 : g, d = c + 0.5 - m, ad = Math.abs(d);
      if (g !== null && ad < 2.6) return { pos: 'side' };
      var t = Math.round(ad - (g !== null ? 3 : 0.5)), k = ((t % 3) + 3) % 3;
      return k === 0 ? { pos: 'pier', bay: Math.floor(t / 3) } : { pos: 'pair', partner: (k === 1 ? 1 : -1) * (d > 0 ? 1 : -1), bay: Math.floor(t / 3) };
    }
    var k2 = (r - 1) % 3;
    return k2 === 0 ? { pos: 'pier', bay: Math.floor((r - 1) / 3) } : { pos: 'pair', partner: k2 === 1 ? 1 : -1, bay: Math.floor((r - 1) / 3) };
  }
  // the engine turns an edge module to face the room: on the S and W walls its local +X runs against c / r
  function half(b, south, west) { return (b.partner > 0) !== (south || west) ? '_A' : '_B'; }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var W = grid.w, Hh = grid.h, west = c === 0, east = c === W - 1, north = r === 0, south = r === Hh - 1, K = kind(grid);
    var ch = grid.at(c, r);
    if (ch === 'n') {   // doorway: the jamb on the end(s) of the run (local -X / +X: +c / -c on E-W runs, +r / -r on N-S runs)
      var along = wallish(grid.at(c - 1, r)) || wallish(grid.at(c + 1, r));
      var lo = along ? grid.at(c - 1, r) !== 'n' : grid.at(c, r + 1) !== 'n', hi = along ? grid.at(c + 1, r) !== 'n' : grid.at(c, r - 1) !== 'n';
      return lo ? 'Door_L' : hi ? 'Door_R' : 'Door_M';
    }
    if ((west || east) && (north || south)) return 'Core';
    if (west || east || north || south) {
      var inward = west ? grid.at(1, r) : east ? grid.at(W - 2, r) : north ? grid.at(c, 1) : grid.at(c, Hh - 2);
      if (wallish(inward) || face === 'corner' || face === 'none') return 'Core';
      if (K === 'ball' && west && SUITE.indexOf(inward) >= 0) return 'SuiteWin';
      var ns = north || south, b = bay(c, r, grid, ns);
      if (b.pos === 'side') return null;   // the gate portal's posts stand there
      if (b.pos === 'pair') {   // a half whose partner cell is a pier (an inner wall meets the facade there) stands alone
        var pc = ns ? c + b.partner : c, pr = ns ? r : r + b.partner;
        var pin = west ? grid.at(1, pr) : east ? grid.at(W - 2, pr) : north ? grid.at(pc, 1) : grid.at(pc, Hh - 2);
        if (wallish(pin) || wallish(grid.at(pc, pr)) === false) b = { pos: 'pier', bay: b.bay };
      }
      var inner = (K === 'lobby' && north) || (K === 'ball' && ns) || (K === 'sky' && north);
      if (K === 'sky' && !inner) return (ns ? Math.abs(c + 0.5 - W / 2) : r) % 4 < 1 ? 'SkyFin' : 'SkyGlass';
      if (inner) {   // interior lift walls: lift pairs in the bays, panels on the piers (the ballroom's north wall: panels)
        if (b.pos === 'pier' || (K === 'ball' && north) || K === 'sky' || b.bay < 1 || b.bay > 2) return panel(ns ? c : r, hash, c, r);
        return 'Lift' + half(b, south, west);
      }
      if (b.pos === 'pier') return 'Pier';
      if (K === 'lobby' && south && b.bay === 1) return 'Revolve' + half(b, south, west);
      return 'Win' + half(b, south, west);
    }
    if (face === 'corner' || face === 'none') return 'Core';
    // the guest wing: no module inside the suite band (each suite piece draws its own walls); sconces beside doors
    if (K === 'ball' && c >= 1 && c <= 6 && [grid.at(c, r - 1), grid.at(c, r + 1)].every(function (q) { return wallish(q) || SUITE.indexOf(q) >= 0; })) return null;
    var vert = wallish(grid.at(c, r - 1)) || wallish(grid.at(c, r + 1));
    if (corner || !(horiz || vert)) return 'Core';
    if (grid.at(c - 1, r) === 'n' || grid.at(c + 1, r) === 'n' || grid.at(c, r - 1) === 'n' || grid.at(c, r + 1) === 'n') return 'Wall_Sconce';
    return panel(horiz ? c : r, hash, c, r);
  }

  // upholstery: palette cells (blender/hotel_base.py order, BASE first) wine 21 -> emerald 24 / navy 26 / teal 28
  var FABRIC = { from: [21], to: [[21], [24], [26], [28]] };
  function suite(name) { return { size: [6, 6], pieces: [name], orient: 'open', kind: 'cover' }; }
  function plate(n) { return { size: [1, 1], pieces: ['Plaque_' + n], orient: 'wall', collide: false }; }
  // the street outside the lobby (street level, in the lifted outside group): sidewalk, the entrance canopy, cabs, lamps
  function street(level, api) {
    var C = this.below || IB.THEME_DEFS.hotel.below, D = C.depth, z0 = level.zones[0], gx = z0.entryGate ? z0.entryGate.x : z0.ox + z0.w / 2;
    var y = -D, front = z0.oz + z0.h + 0.6, side = 7, x0 = z0.ox - 0.6 - side, x1 = z0.ox + z0.w + 0.6 + side;
    var walk = new THREE.Color('#B9B2A4'), kerb = new THREE.Color('#8E877C');
    api.geo.flat([[x0, front], [x1, front], [x1, front + 7], [x0, front + 7]], y + 0.15, walk);
    api.geo.flat([[x0, front + 7], [x1, front + 7], [x1, front + 7.3], [x0, front + 7.3]], y + 0.16, kerb);
    [-1, 1].forEach(function (s) {
      var sx = s < 0 ? x0 : x1 - side;
      api.geo.flat([[sx, z0.oz - 6], [sx + side, z0.oz - 6], [sx + side, front], [sx, front]], y + 0.15, walk);
    });
    api.add('Street_Canopy', gx, y, front, 0);
    api.add('Street_Taxi', gx - 7.5, y, front + 9.2, Math.PI / 2);
    api.add('Street_Taxi', gx + 13, y, front + 9.2, -Math.PI / 2);
    for (var k = -2; k <= 2; k++) if (k) api.add('Street_Lamp', gx + k * 11, y + 0.15, front + 6.6, 0);
    for (var j = 0; j < 4; j++) { api.add('Street_Lamp', x0 + 1.2, y + 0.15, front - 8 - j * 12, Math.PI / 2); api.add('Street_Lamp', x1 - 1.2, y + 0.15, front - 8 - j * 12, Math.PI / 2); }
  }

  IB.registerTheme({
    id: 'hotel', name: 'The Aurelian', family: 'kit-hotel', prefix: 'KIT_HOTEL_',
    palette: ['#922A3C', '#F0C24E', '#2F7F60', '#F3ECDF'],
    env: {
      // golden hour: a deep blue zenith over an amber haze; the haze, the fog and the city's depth haze are one colour
      sky: ['#3F6FB4', '#F2CDA0'], fog: { color: '#F2CDA0', near: 110, far: 900, tierScale: true },
      sun: [-0.5, 0.36, 0.79],
      far: 1500,
      // clouds drift below the sky deck: at the lobby they are high overhead, from the roof you look down on them
      clouds: { y: [-80, -42], count: 6, scale: [2.4, 3.6], lanes: [55, 80], span: 300, speed: 0.8, axis: 'z' },
      ceiling: { height: 9.0, color: '#F4EBDC' }   // the zones' "@layer 9" grids hang the fittings
    },
    // honed marble, 1 m joints (carpets, the medallion and the dance floor come from each zone's "@layer 0" grid);
    // the service stairs: sealed concrete
    floor: {
      color: '#EFE5D3', trail: '#B7B0A3', outside: '#F2CDA0',
      lines: [{ dir: 'x', every: 1, width: 0.025, color: '#DDD0BA', y: 0.008 }, { dir: 'z', every: 1, width: 0.025, color: '#DDD0BA', y: 0.0105 }]
    },
    wall: { height: 9.0, roof: '#E6DCCB', facing: 'open', choose: chooseWall, cols: true,
      passage: { ch: 'n', solid: [[2.7, 9.0]] } },   // doorways: open below the 2.7 m lintel
    symbols: {
      'Z': { size: [4, 10], pieces: ['GrandStair'], face: 0, kind: 'step' },
      'I': { pieces: ['Column_Lo'], kind: 'cover' },
      'R': { size: [6, 4], pieces: ['Landmark_Reception'], orient: 'wall', kind: 'cover' },
      'Q': { size: [3, 2], pieces: ['Concierge'], kind: 'cover' },
      'X': { size: [8, 4], pieces: ['Landmark_Bar'], orient: 'wall', kind: 'cover' },
      'b': { pieces: ['Stool'], rotate: 'random90', kind: 'cover' },
      'L': { size: [4, 3], pieces: ['Lounge_A', 'Lounge_B'], flip: true, paint: FABRIC, kind: 'cover' },
      'K': { size: [3, 3], pieces: ['Piano'], flip: true, kind: 'cover' },
      'F': { size: [3, 3], pieces: ['Landmark_Flowers'], kind: 'cover' },
      'c': { pieces: ['LuggageCart'], rotate: 'random90', kind: 'cover' },
      'j': { pieces: ['BellStand'], rotate: 0, kind: 'cover' },
      'p': { pieces: ['Palm'], rotate: 'random90', kind: 'cover' },
      't': { pieces: ['Topiary'], kind: 'cover' },
      'O': { size: [2, 1], pieces: ['Ottoman'], paint: FABRIC, kind: 'cover' },
      'k': { size: [2, 1], pieces: ['Console'], orient: 'wall', kind: 'cover' },
      'w': { size: [2, 1], pieces: ['WritingDesk'], orient: 'wall', kind: 'cover' },
      'T': { size: [3, 3], pieces: ['Banquet'], kind: 'cover' },
      'D': { size: [9, 4], pieces: ['Landmark_Stage'], orient: 'wall', kind: 'cover' },
      'e': { pieces: ['Easel'], rotate: Math.PI / 2, kind: 'cover' },
      'y': { size: [2, 1], pieces: ['HKCart'], flip: true, kind: 'cover' },
      'v': { size: [2, 1], pieces: ['RSTrolley'], flip: true, kind: 'cover' },
      'M': suite('Suite_King'), 'N': suite('Suite_Twin'), 'W': suite('Suite_Salon'),
      'B': { size: [10, 4], pieces: ['Landmark_Pool'], kind: 'cover' },
      'l': { size: [1, 2], pieces: ['Lounger'], kind: 'cover' },
      'u': { pieces: ['Umbrella'], rotate: 'random90', kind: 'cover' },
      'A': { size: [3, 3], pieces: ['Cabana'], orient: 'wall', kind: 'cover' },
      'V': { size: [7, 7], pieces: ['Landmark_SkyBar'], kind: 'cover' },
      'f': { size: [2, 2], pieces: ['FireTable'], kind: 'cover' },
      'o': { size: [2, 2], pieces: ['Olive'], kind: 'cover' },
      '=': { pieces: ['Hedge'], rotate: 'run', kind: 'cover' },
      'J': { size: [5, 4], pieces: ['PentLiving'], kind: 'cover' },
      'd': { size: [5, 3], pieces: ['PentDining'], kind: 'cover' },
      'z': { size: [4, 4], pieces: ['PentBed'], orient: 'wall', kind: 'cover' },
      'q': { pieces: ['Telescope'], rotate: 'random90', kind: 'cover' },
      'g': { size: [3, 1], pieces: ['Fireplace'], orient: 'wall', kind: 'cover' },
      // gallery
      'm': { deck: { thick: 0.4, color: '#E7DCC8', edge: '#CF9F43', under: '#F4EBDC', with: '*' } },
      'r': { pieces: ['Rail'], full: 'RailFull', links: 'ri', post: 'RailPost', kind: 'wall' },
      'i': { pieces: ['Column_Hi'], kind: 'cover' },
      ';': { pieces: ['UnderLight'], collide: false },
      // floors (layer 0) and the suites' plates (layer 0.01)
      'x': { size: [7, 7], pieces: ['Inlay_Medallion'], collide: false },
      '-': { pieces: ['Inlay_Band'], rotate: 'run', collide: false },
      '_': { size: [3, 1], pieces: ['Runner'], collide: false },
      '!': { size: [4, 4], pieces: ['Carpet_Lobby'], collide: false },
      '+': { size: [4, 4], pieces: ['Carpet_Corridor'], collide: false },
      '&': { size: [4, 4], pieces: ['Carpet_Pent'], collide: false },
      '%': { size: [3, 3], pieces: ['Parquet'], collide: false },
      '$': { size: [4, 4], pieces: ['Deck'], collide: false },
      '1': plate(1), '2': plate(2), '3': plate(3), '4': plate(4), '5': plate(5), '6': plate(6),
      // ceiling / roof (layer 9): pieces hang from the ceiling plane; the glass roof stands on it
      '~': { size: [4, 4], pieces: ['Coffer'], collide: false },
      ':': { pieces: ['Downlight'], collide: false },
      'H': { size: [5, 5], pieces: ['Landmark_Chandelier'], collide: false },
      'Y': { size: [3, 3], pieces: ['Chandelier'], collide: false },
      '^': { size: [7, 7], pieces: ['GlassRoof'], collide: false }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    // the service stairs: back-of-house corridors; each one is stencilled with the floor it climbs to
    trail: { wall: 'TrailWall', height: 9.0, variants: ['TrailWall', 'TrailWall_Pipe', 'TrailWall_Hose', 'TrailWall_Lift'], end: 'TrailEnd',
      byTrail: [
        { variants: ['TrailWall', 'TrailWall_Pipe', 'TrailWall_F24', 'TrailWall_Lift', 'TrailWall', 'TrailWall_Hose'] },
        { variants: ['TrailWall', 'TrailWall_F56', 'TrailWall_Lift', 'TrailWall', 'TrailWall_Pipe', 'TrailWall_Hose'] },
        { variants: ['TrailWall', 'TrailWall_FR', 'TrailWall_Pipe', 'TrailWall', 'TrailWall_Hose', 'TrailWall_Lift'] }
      ] },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: { build: street },
    // the city round the tower (zones.js buildCityBelow), each zone at its own height above the street
    below: {
      depth: 196, levels: [0.45, 86, 196],      // the lobby a step above the street, floor 24, floor 56 (the roof)
      haze: '#F2CDA0', hazeTop: 0.02, hazeBottom: 0.24, hazeDist: [160, 1100, 0.8], hazeMax: 1,
      glass: '#4D6A88', facade: '#DCCBAA', setback: '#CDBB98', roof: '#9A8F86', street: '#5F5A5E', linkRoof: '#8F857C',
      blocks: ['#D9B48E', '#C48C6E', '#9FB2C4', '#D8CDBA', '#B0927A', '#8E9FB2', '#E2B79A', '#A7B8A0'],
      extent: 640, detail: 260, horizon: 1400,
      // the tower: the podium round the lobby rises 20 m over its floor, the ballroom wing 40 m; the sky deck is the
      // roof. Between the wings (round the service stairs) the link blocks close 10 m over the lower floor, the crown
      // over the exit stair stands 9 m either side of it
      towerTop: [20, 40, -0.06], linkTop: 10, crownHalf: 9,
      far: { count: 34, radius: [650, 1150], height: [-120, 140], width: [24, 60] }
    },
    budget: { prop: 3600, landmark: 6000, total: 100000 },
    allPieces: function () {
      var out = ['Win_A', 'Win_B', 'Revolve_A', 'Revolve_B', 'Pier', 'Core', 'Lift_A', 'Lift_B', 'SuiteWin', 'SkyGlass', 'SkyFin',
        'Door_L', 'Door_M', 'Door_R', 'GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Pipe', 'TrailWall_Hose', 'TrailWall_Lift',
        'TrailWall_F24', 'TrailWall_F56', 'TrailWall_FR', 'TrailEnd', 'Hatch', 'Stand', 'Rail', 'RailFull', 'RailPost', 'Street_Canopy', 'Street_Taxi', 'Street_Lamp'];
      INNER.forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        var d = sym[ch]; (d.pieces || []).concat(d.full ? [d.full] : [], d.post ? [d.post] : []).forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out;
    },
    levels: {
      hotel: {
        name: 'The Aurelian',
        intro: 'A grand hotel overrun. Clear the lobby, then take the service stairs up: the ballroom floor, then the roof.',
        zones: [
          // the Grand Lobby: Blade Bots across the marble, Gunners on the gallery from the start
          { map: 'hotel_lobby', ceiling: 'plain', label: 'The Grand Lobby', waves: [
            [['crawler', 22], ['gunner', 6]],
            [['crawler', 6], ['bomber', 2], ['gunner', 6], ['blader', 8]],
            [['crawler', 7], ['drone', 5], ['gunner', 5], ['soldier', 9]],
            [['crawler', 6], ['bomber', 2], ['gunner', 6], ['soldier', 6], ['blader', 4]]] },
          // Floor 24: the ballroom's tables, the suites to fight through, Drones in the 9 m halls
          { map: 'hotel_ballroom', ceiling: 'plain', label: 'Floor 24', waves: [
            [['crawler', 22], ['gunner', 6], ['drone', 3]],
            [['crawler', 7], ['bomber', 2], ['gunner', 6], ['blader', 10]],
            [['crawler', 7], ['drone', 6], ['gunner', 6], ['soldier', 9]],
            [['crawler', 7], ['bomber', 2], ['gunner', 6], ['blader', 7], ['soldier', 5]]] },
          // Floor 56: the sky deck under glass, Drones over the pool, a heavy last wave in the penthouse
          { map: 'hotel_sky', ceiling: false, label: 'Floor 56', waves: [
            [['crawler', 22], ['gunner', 8], ['drone', 3], ['soldier', 1]],
            [['crawler', 6], ['bomber', 2], ['drone', 6], ['soldier', 8]],
            [['crawler', 8], ['gunner', 8], ['drone', 6], ['blader', 8]],
            [['crawler', 10], ['gunner', 10], ['bomber', 2], ['drone', 5], ['soldier', 11], ['blader', 5]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
