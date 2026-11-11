/* Theme: Meridian International (kit-airport) -- a made-up airport, home of the made-up Skylark Air. Two zones:
   1 The Terminal (80 x 78 m, a 14 m hall): the landside check-in hall (four check-in islands of the made-up airlines
     Skylark Air, AeroVale, NorthStar and Coral Jet with bag belts running into their hoods, kiosks, the departures
     board, the information desk, trolleys), the AUTOMATED SECURITY checkpoint (a glass screen line with e-gates and
     roller shutters, X-ray lanes with trays riding the belts, body-scanner portals, walk-through sensor arches,
     rising bollards, camera domes and sensor gantries on the ceiling, emissive status lights), and airside: gates
     A1 - A3 with rows of seats along the glass, the Meridian Duty Free, the Skylark Lounge (bar, club chairs, a
     buffet) behind its glass wall, and the mezzanine at 4.5 m (escalators, a stair, the Skybean cafe) for high
     ground. Landmark: the glass curtain wall onto the apron, with the jet bridge at gate A3 and a Skylark twin-jet
     parked outside.
   2 Hangar 2 and its apron (72 x 74 m): the Meridian Aero maintenance hangar, a Skylark twin-jet on its gear with
     the port engine off (on its transport stand), work platforms at 2.6 m along the fuselage, the wings walkable,
     the tail deck at 5.2 m (climbable: scaffold stairs), jacks, tool cribs, workbenches; the 36 m door opening onto
     the apron with taxi lead-in lines, a tug, a baggage train, a fuel truck, a stairs truck (climbable), a belt
     loader, ULDs, blast fences; the ground-operations building closes the apron.
   Outside (backdrop.build): the apron 4.5 m under the departures floor, the parked jet and its jet bridge, more
   aircraft at remote stands and on the taxiway, the runway, the control tower, the fuel farm, cargo sheds, flat
   grass to the horizon; landside, the elevated departures road with taxis and cars; outward shells give the
   terminal, the hangar, the ops building and the corridor their outside faces.
   Built by blender/fam_kit_airport.py (ap_*.py); zone layers by tools/airport_zones.py. Cones, drums, the forklift
   and the cars are kit-parking pieces, palms and taxis kit-hotel, workbenches, tool chests, tyres and lockers
   kit-police (theme option `families`).

   A zone file has the floor plan and these layers: "@layer 0.01" (floor finishes, wall logos), "@layer 0.02" (floor
   marks, the engine on its stand), "@layer 0.025" (wall-art codes on wall cells and the zone code at (0, 0); no
   symbols), "@layer 4.5" (terminal mezzanine) or "@layer 2.6" and "@layer 5.2" (hangar work platforms), and
   "@layer 14" (ceiling / roof pieces hanging from the 14 m plane).
   Floor plan, terminal:
     I J K L check-in island of Skylark / AeroVale / NorthStar / Coral Jet [3,6] (a run north-south; bags ride north)
     k kiosk   j bench [4,1]   B departures board [10,2]   i information desk [4,2]   b belt barrier (runs)   t baggage trolley
     q glass screen (runs)   e e-gate bank [3,2]   X X-ray lane [3,2] (a run north-south, trays ride north)
     W body scanner [2,2]   A sensor arch [1,2]   o rising bollard   U roller shutter (up) [3,1]   Y shutter half down
     p supervisor podium   r repack bench [4,1]   C c Q V seat row [4,1] facing east / west / south / north
     g gate podium [3,1] (faces west)   v charging pillar   y flight-info pylon   d duty-free gondola [3,1]
     H wall shelving [3,1] (back to the wall)   f perfume island [2,2]   x cash desk [3,2]   z chocolate pyramid [2,2]
     R lounge bar [6,2] (back to the wall)   M club chairs [2,2] (face south)   m club chairs (face north)
     F sofa [3,1] (faces east)   T buffet [4,1] (back to the wall)   N lounge desk [3,1] (faces south)
     n lounge glass door [2,1] (in the glass line)   O tree column   l deck column   s stair [2,9] rising north
     1 escalator [2,9] rising north   3 palm (kit-hotel)   4 topiary (kit-hotel)
   Mezzanine (4.5): u deck   ' glass rail (runs)   0 the Skybean cafe [4,2] (back to the west wall)   Z cafe table [2,2]
   Floor plan, hangar and apron:
     @ the twin-jet (one cell: its centre)   % engine (one cell, 1.2 m up: on the pylon; also in layer 0.02 on its
     stand)   $ engine stand   & tripod jack   5 6 scaffold stair [2,6] rising north / south   : platform post
     ; tall post (to the tail deck)   D aircraft tug [2,4]   + baggage tractor [2,2]   = baggage cart [2,3]
     ~ fuel truck [3,7]   ^ stairs truck [2,6] (climbable)   < belt loader [2,6]   > ULD container [2,2]
     ? ground power unit [2,2]   | towbar [1,4]   [ tool crib [4,3] (back to the wall)   ] apron light mast
     { workbench   } tool chest   ( tyre stack   ) lockers   * cones   " drums   ` forklift [2,3]   , pallet stack [2,2]
   Platforms (2.6 / 5.2): w deck   \ yellow rail (runs)   (stairs and posts on the 2.6 layer stand on the deck)
   Floor finishes and marks (0.01 / 0.02): - yellow line (runs)   _ taxi lead-in line (runs)   þ terrazzo band (runs)   ç keep-clear hatch   ñ red hatch
     µ entrance mat [3,2]   ø lounge carpet [4,4]   å duty-free tile [4,4]   æ security vinyl [4,4]
     ë hangar epoxy [4,4]   ß stop bar [3,1]   ð stand number [3,2]   Ð MERIDIAN logo [10,1] (on the west wall)
     Þ MERIDIAN AERO logo [12,1] (back wall)   Ø GROUND OPERATIONS [10,1] (ops building)
   Ceiling / roof (14): Ä skylight strip [8,2]   Ö timber baffles [4,4]   Ü camera dome   Ê sensor gantry [2,8]
     À GATES  Á SECURITY  Â CHECK-IN  Ã TO HANGAR 2 [5,1] (hanging boards)   È Ì Í Î airline boards [5,1]
     Ò Ó Ô gate numbers A1 - A3 [2,1]   Ù DUTY FREE fascia [8,1]   Ú hangar roof bay [24,4]   Û door header [12,1]
   Wall-art codes (layer 0.025 on wall cells; never a symbol): ¹ fire point  ² ³ ¼ ½ lightbox ads  ¾ flight screens
     × restrooms  ÷ staff door  ¿ ¡ wayfinding  ¢ entrance doors (curtain wall)  £ jet-bridge door (curtain wall)
     § hangar column  © panel  ® safety board  ° blast-fence sign.  Zone codes at (0, 0): ¤ terminal, ¦ hangar.
   Walls (facing: 'open'): the terminal's south wall and the east wall north of row 40 are the curtain wall (a
   mullion every 3 m); other terminal walls are stone and white panels; cells next to a gate are concrete cores.
   The hangar's walls are lined steel (a column every 6 m), its front wall (row 44) is two-sided with the door
   pockets beside the opening, the apron has the blast fence (two-sided), the ops building closes the south. */
(function (IB) {
  'use strict';
  var R90 = Math.PI / 2, KP = 'KIT_PARKING_', KH = 'KIT_HOTEL_', KO = 'KIT_POLICE_';
  var GY = -4.5;                         // the apron outside lies 4.5 m under the zones' floors
  // the zone's wall-art layer ("@layer 0.025": art codes on wall cells and the zone code at (0, 0); never a symbol)
  function floorOf(grid) {
    if (grid._apF === undefined) {
      grid._apF = null;
      (grid.layers || []).forEach(function (l) { if (Math.abs(l.y - 0.025) < 0.001) grid._apF = l; });
    }
    return grid._apF;
  }
  var ART = {
    T: { '¹': 'WT_Fire', '²': 'WT_AdA', '³': 'WT_AdB', '¼': 'WT_AdC', '½': 'WT_AdD', '¾': 'WT_FIDS', '×': 'WT_WC', '÷': 'WT_Door',
      '¿': 'WT_WayA', '¡': 'WT_WayB', '¢': 'WG_Door', '£': 'WG_Bridge' },
    A: { '¹': 'WH_Fire', '§': 'WH_Col', '©': 'WH_Panel', '®': 'WH_Board', '°': 'WA_Sign' }
  };
  function nearGate(grid, c, r) {
    for (var d = -1; d <= 1; d += 2) { var ch = grid.at(c + d, r); if (ch === 'G' || ch === 'E') return true; }
    return false;
  }
  function glassCell(grid, c, r) { return r === grid.h - 1 || (c === grid.w - 1 && r <= 40); }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = floorOf(grid), Z = F && F.at(0, 0) === '¦' ? 'A' : 'T', code = F ? F.at(c, r) : '.', A = ART[Z];
    if (Z === 'T') {
      var glass = glassCell(grid, c, r);
      if (face === 'corner' || face === 'none') return glass && (c === grid.w - 1 || r === grid.h - 1) ? 'CornerG' : 'CornerT';
      if (nearGate(grid, c, r)) return 'WC';
      if (A.hasOwnProperty(code)) return A[code];
      if (glass) { var k = r === grid.h - 1 ? c : r; return k % 3 === 1 ? 'WG_M' : (hash(c, r) < 0.5 ? 'WG' : 'WG_B'); }
      return 'WT';
    }
    // hangar zone: lining (rows 0 - 43), the front wall (row 44), the apron fence, the ops building (last row)
    var part = r === grid.h - 1 ? 'O' : r === 44 ? 'F' : r > 44 ? 'A' : 'H';
    if (face === 'corner' || face === 'none') return { H: 'CornerH', F: 'CornerF', A: 'CornerA', O: 'CornerO' }[part];
    if (nearGate(grid, c, r)) return part === 'O' ? 'CornerO' : 'WC';
    if (part === 'F') {
      var gap = 0; for (var d = 1; d <= 3; d++) if (grid.at(c - d, r) === '.' || grid.at(c + d, r) === '.') { gap = d; break; }
      return gap ? (gap % 2 ? 'WF_DoorA' : 'WF_DoorB') : 'WF';
    }
    if (part === 'O') return 'WO';
    if (A.hasOwnProperty(code)) return A[code];
    return part === 'A' ? 'WA' : 'WH';
  }
  function flat(pieces, rot) { return { pieces: pieces, collide: false, rotate: rot || 0 }; }
  function sign(piece, w) { return { size: [w || 5, 1], pieces: [piece], collide: false }; }

  // paint jobs: the check-in islands' counter / accent colours per airline (cells gA = 30, gB = 31 of the kit);
  // goods on the duty-free shelves and in the bar: four product mixes over the goods cells (30 - 33)
  var C = { gA: 30, gB: 31, gC: 32, gD: 33, pPurple: 34, pPink: 35, pLime: 36, pOrange: 37, sky: 25, skyL: 26, sun: 27, navy: 28, coral: 29, wallW: 8, steel: 18, leather: 39, brass: 40 };
  function airline(a, b) { return { from: [C.gA, C.gB], to: [[a, b]] }; }
  var GOODS = { from: [C.gA, C.gB, C.gC, C.gD], to: [[30, 31, 32, 33], [34, 35, 36, 37], [29, 26, 32, 35], [37, 33, 34, 31], [35, 32, 30, 36]] };
  var ISL = ['Isl_End', 'Isl_Mid', 'Isl_Hood'];
  var BAGS = ['Bag_A', 'Bag_B', 'Bag_C', 'Bag_D'];
  function island(a, b) {
    return { size: [3, 6], pieces: ISL, sequence: 'run', kind: 'cover', paint: airline(a, b),
      conveyor: { speed: 0.45, dir: 1, y: 0.62, spacing: 2.2, inset: 0.6, items: BAGS } };
  }
  function seats(face) { return { size: [4, 1], pieces: ['Seats'], face: face, kind: 'cover' }; }
  function stair(face) { return { size: [2, 9], pieces: ['Stair'], face: face, kind: 'step' }; }
  function scaf(face) { return { size: [2, 6], pieces: ['Scaf'], face: face, kind: 'step' }; }

  var SYMBOLS = {
    // ---- terminal: check-in
    'I': island(C.sky, C.sun), 'J': island(C.coral, C.wallW), 'K': island(C.navy, C.skyL), 'L': island(C.sun, C.navy),
    'k': { pieces: ['Kiosk'], rotate: 'edge', kind: 'cover' },
    'B': { size: [10, 2], pieces: ['Board'], kind: 'cover' },
    'i': { size: [4, 2], pieces: ['InfoDesk'], face: 0, kind: 'cover' },
    'b': { pieces: ['BeltHalf'], full: 'BeltFull', links: 'b', post: 'BeltPost', kind: 'cover' },
    'j': { size: [4, 1], pieces: ['Bench'], kind: 'cover' },
    't': { pieces: ['Trolley', 'TrolleyB', 'Trolley'], rotate: 'random90', kind: 'cover', paint: { from: [C.gA, C.gB], to: [[C.sky, C.coral], [C.sun, C.navy]] } },
    // ---- terminal: automated security
    'q': { pieces: ['GlassHalf'], full: 'GlassFull', links: 'qneUY#', post: 'GlassPost', kind: 'wall' },
    'e': { size: [3, 2], pieces: ['EGate'], face: 0, kind: 'cover' },
    'X': { size: [3, 2], pieces: ['Xr_In', 'Xr_Tunnel', 'Xr_Out'], sequence: 'run', kind: 'cover',
      conveyor: { speed: 0.35, dir: 1, y: 0.86, spacing: 2.0, inset: 0.7, items: ['Tray_A', 'Tray_B', 'Tray_C', 'Tray_A'] } },
    'W': { size: [2, 2], pieces: ['Scanner'], face: 0, kind: 'cover' },
    'A': { size: [1, 2], pieces: ['Arch'], face: 0, kind: 'cover' },
    'o': { pieces: ['Bollard'], kind: 'cover' },
    'U': { size: [3, 1], pieces: ['ShutterUp'], kind: 'cover' },
    'Y': { size: [3, 1], pieces: ['ShutterHalf'], kind: 'cover' },
    'p': { pieces: ['Podium'], rotate: 'edge', kind: 'cover' },
    'r': { size: [4, 1], pieces: ['Repack'], kind: 'cover' },
    // ---- terminal: airside
    'C': seats(R90), 'c': seats(-R90), 'Q': seats(0), 'V': seats(Math.PI),
    'g': { size: [3, 1], pieces: ['GatePod'], face: -R90, kind: 'cover' },
    'v': { pieces: ['Charge'], kind: 'cover' },
    'y': { pieces: ['FIDS'], rotate: 'run', kind: 'cover' },
    'd': { size: [3, 1], pieces: ['Gondola'], kind: 'cover', paint: GOODS },
    'H': { size: [3, 1], pieces: ['Shelf'], orient: 'wall', kind: 'cover', paint: GOODS },
    'f': { size: [2, 2], pieces: ['Perfume'], kind: 'cover', paint: GOODS },
    'x': { size: [3, 2], pieces: ['CashDesk'], face: 0, kind: 'cover' },
    'z': { size: [2, 2], pieces: ['Choc'], kind: 'cover' },
    'R': { size: [6, 2], pieces: ['Bar'], orient: 'wall', kind: 'cover', paint: GOODS },
    'M': { size: [2, 2], pieces: ['Club'], face: R90, kind: 'cover' },
    'm': { size: [2, 2], pieces: ['Club'], face: 0, kind: 'cover' },
    'F': { size: [3, 1], pieces: ['Sofa'], face: R90, kind: 'cover' },
    'T': { size: [4, 1], pieces: ['Buffet'], orient: 'wall', kind: 'cover' },
    'N': { size: [3, 1], pieces: ['LoungeDesk'], face: 0, kind: 'cover' },
    'n': { size: [2, 1], pieces: ['LoungeDoor'], orient: 'span', kind: 'wall' },
    'O': { pieces: ['Column'], kind: 'cover' },
    'l': { pieces: ['DeckCol'], kind: 'cover' },
    's': stair(0), '1': { size: [2, 9], pieces: ['Escalator'], face: 0, kind: 'step' },
    '3': { pieces: [KH + 'Palm'], rotate: 'random90', kind: 'cover' },
    '4': { pieces: [KH + 'Topiary'], rotate: 'random90', kind: 'cover' },
    // ---- terminal mezzanine (layer 4.5)
    'u': { deck: { thick: 0.4, color: '#D8D3C8', edge: '#F2F1EC', under: '#E9E8E2', with: '*' } },
    "'": { pieces: ['GRailHalf'], full: 'GRailFull', links: "'", post: 'GRailPost', kind: 'wall' },
    '0': { size: [4, 2], pieces: ['Cafe'], face: R90, kind: 'cover' },
    'Z': { size: [2, 2], pieces: ['CafeTable'], kind: 'cover' },
    // ---- hangar and apron
    '@': { pieces: ['Jet_Body'], rotate: 0, kind: 'cover' },
    '%': { pieces: ['Engine'], rotate: 0, y: 1.2, kind: 'cover' },
    '$': { pieces: ['EngStand'], rotate: 0, kind: 'cover' },
    '&': { pieces: ['Jack'], kind: 'cover' },
    '5': scaf(0), '6': scaf(Math.PI),
    ':': { pieces: ['Post'], kind: 'cover' },
    ';': { pieces: ['Post2'], kind: 'cover' },
    'D': { size: [2, 4], pieces: ['Tug'], flip: true, kind: 'cover' },
    '+': { size: [2, 2], pieces: ['BagTractor'], face: Math.PI, kind: 'cover' },
    '=': { size: [2, 3], pieces: ['BagCart'], face: Math.PI, kind: 'cover', paint: { from: [C.gA, C.gB, C.gC, C.gD], to: [[30, 31, 32, 33], [35, 34, 37, 36], [32, 29, 30, 35]] } },
    '~': { size: [3, 7], pieces: ['FuelTruck'], flip: true, kind: 'cover' },
    '^': { size: [2, 6], pieces: ['StairTruck'], face: 0, kind: 'step' },
    '<': { size: [2, 6], pieces: ['BeltLoader'], flip: true, kind: 'cover' },
    '>': { size: [2, 2], pieces: ['ULD'], flip: true, kind: 'cover' },
    '?': { size: [2, 2], pieces: ['GPU'], flip: true, kind: 'cover' },
    '|': { size: [1, 4], pieces: ['Towbar'], face: 0, kind: 'cover' },
    '[': { size: [4, 3], pieces: ['ToolCrib'], orient: 'wall', kind: 'cover' },
    ']': { pieces: ['Mast'], kind: 'cover' },
    '{': { pieces: [KO + 'Workbench'], rotate: 'edge', kind: 'cover' },
    '}': { pieces: [KO + 'ToolChest'], rotate: 'edge', kind: 'cover' },
    '(': { pieces: [KO + 'Tyres'], rotate: 'random90', kind: 'cover' },
    ')': { pieces: [KO + 'Locker'], rotate: 'edge', kind: 'cover' },
    '*': { pieces: [KP + 'Cones'], rotate: 'random90', kind: 'cover' },
    '"': { pieces: [KP + 'Drums'], rotate: 'random90', kind: 'cover' },
    '`': { size: [2, 3], pieces: [KP + 'Forklift'], flip: true, kind: 'cover' },
    ',': { size: [2, 2], pieces: [KP + 'Pallets'], flip: true, kind: 'cover' },
    // ---- hangar work platforms (layers 2.6 and 5.2)
    'w': { deck: { thick: 0.12, color: '#9AA3AC', edge: '#F5C431', under: '#7E8892', with: '*' } },
    '\\': { pieces: ['YRailHalf'], full: 'YRailFull', links: '\\', post: 'YRailPost', kind: 'wall' },
    // ---- floor marks and wall logos (layer 0.01)
    '-': { pieces: ['F_Line'], rotate: 'run', collide: false },
    '_': { pieces: ['F_Taxi'], rotate: 'run', collide: false },
    'þ': { pieces: ['F_Band'], rotate: 'run', collide: false },
    'ç': flat(['F_Hatch']), 'ñ': flat(['F_Red']),
    'µ': { size: [3, 2], pieces: ['F_Mat'], collide: false },
    'ø': { size: [4, 4], pieces: ['F_Carpet'], collide: false }, 'å': { size: [4, 4], pieces: ['F_Tile'], collide: false },
    'æ': { size: [4, 4], pieces: ['F_Vinyl'], collide: false }, 'ë': { size: [4, 4], pieces: ['F_Epoxy'], collide: false },
    'ß': { size: [3, 1], pieces: ['F_Stop'], collide: false }, 'ð': { size: [3, 2], pieces: ['F_Stand'], face: Math.PI, collide: false },
    'Ð': { size: [10, 1], pieces: ['Logo_T'], face: R90, collide: false },
    'Þ': { size: [12, 1], pieces: ['Logo_H'], face: 0, collide: false },
    'Ø': { size: [10, 1], pieces: ['Logo_O'], face: Math.PI, collide: false },
    // ---- ceiling and roof (layer 14)
    'Ä': { size: [8, 2], pieces: ['Sky_Strip'], collide: false }, 'Ö': { size: [4, 4], pieces: ['Baffle'], collide: false },
    'Ü': flat(['Cam']), 'Ê': { size: [2, 8], pieces: ['Gantry'], collide: false },
    'À': sign('Sg_Gates'), 'Á': sign('Sg_Security'), 'Â': sign('Sg_CheckIn'), 'Ã': sign('Sg_Exit'),
    'È': sign('Sg_Sky'), 'Ì': sign('Sg_Vale'), 'Í': sign('Sg_North'), 'Î': sign('Sg_Coral'),
    'Ò': sign('Sg_A1', 2), 'Ó': sign('Sg_A2', 2), 'Ô': sign('Sg_A3', 2), 'Ù': sign('Sg_DF', 8),
    'Ú': { size: [24, 4], pieces: ['Roof_H', 'Roof_HL', 'Roof_H', 'Roof_HS', 'Roof_HL'], sequence: true, collide: false },
    'Û': { size: [12, 1], pieces: ['Hdr_A', 'Hdr_B', 'Hdr_C'], sequence: 'run', collide: false }
  };

  // glow companions (zones.js theme.glow): screens, status lights, lightboxes, lamps -- drawn unlit
  var GLOW = {
    WT_AdA: { piece: 'WT_AdA_LED' }, WT_AdB: { piece: 'WT_AdB_LED' }, WT_AdC: { piece: 'WT_AdC_LED' }, WT_AdD: { piece: 'WT_AdD_LED' },
    WT_FIDS: { piece: 'WT_FIDS_LED' }, WG_Door: { piece: 'WG_Door_LED' }, WG_Bridge: { piece: 'WG_Bridge_LED' },
    GateFrame: { piece: 'GateFrame_LED' }, CeilLight: { piece: 'CeilLight_LED' }, Roof_HL: { piece: 'Roof_HL_LED' },
    Isl_End: { piece: 'Isl_End_LED' }, Isl_Mid: { piece: 'Isl_Mid_LED' }, Isl_Hood: { piece: 'Isl_Hood_LED' },
    Kiosk: { piece: 'Kiosk_LED' }, Board: { piece: 'Board_LED' },
    EGate: { piece: 'EGate_LED', groups: 3 }, Xr_In: { piece: 'Xr_In_LED' }, Xr_Tunnel: { piece: 'Xr_Tunnel_LED' },
    Scanner: { piece: 'Scanner_LED', groups: 3 }, Arch: { piece: 'Arch_LED', groups: 2 }, Bollard: { piece: 'Bollard_LED', groups: 2 },
    ShutterUp: { piece: 'ShutterUp_LED' }, ShutterHalf: { piece: 'ShutterHalf_LED', groups: 2 }, Podium: { piece: 'Podium_LED' },
    Cam: { piece: 'Cam_LED', groups: 3 }, Gantry: { piece: 'Gantry_LED', groups: 2 },
    GatePod: { piece: 'GatePod_LED' }, Charge: { piece: 'Charge_LED' }, FIDS: { piece: 'FIDS_LED' }, CashDesk: { piece: 'CashDesk_LED' },
    Bar: { piece: 'Bar_LED' }, Cafe: { piece: 'Cafe_LED' }, Mast: { piece: 'Mast_LED' }
  };

  // ---------------------------------------------------------------- outside (zones.js backdrop.build)
  var THREE_ = function () { return (typeof window !== 'undefined' && window.THREE) || globalThis.THREE; };
  function buildOutside(level, api) {
    var THREE = THREE_(), zones = level.zones, theme = level.theme, g = api.geo, hash = api.hash;
    var Z1 = zones[0], Z2 = zones[1];
    var col = function (h) { return new THREE.Color(h); };
    // a vertical quad (a -> b along the ground, y0 .. y1) facing its outward normal n = [nx, nz]
    function wallQ(ax, az, bx, bz, y0, y1, c, n) {
      var b0 = g.pos.length / 3, cc = col(c);
      g._vert(ax, y0, az, n[0], 0, n[1], cc); g._vert(bx, y0, bz, n[0], 0, n[1], cc);
      g._vert(bx, y1, bz, n[0], 0, n[1], cc); g._vert(ax, y1, az, n[0], 0, n[1], cc);
      var ex = bx - ax, ez = bz - az, cr = ez * n[0] - ex * n[1];   // pick the winding that faces n
      if (cr < 0) g.idx.push(b0, b0 + 1, b0 + 2, b0, b0 + 2, b0 + 3); else g.idx.push(b0, b0 + 2, b0 + 1, b0, b0 + 3, b0 + 2);
    }
    // an outward shell: sides with optional holes (the corridors) along the north / south faces, a roof
    function shell(x0, z0, x1, z1, y0, y1, c, opt) {
      opt = opt || {};
      var holes = opt.holes || [];
      [['N', z0, -1], ['S', z1, 1]].forEach(function (F) {
        if (opt.skip && opt.skip.indexOf(F[0]) >= 0) return;
        var xs = [x0], hs = holes.filter(function (h) { return h.side === F[0]; });
        hs.forEach(function (h) { xs.push(h.x - h.w, h.x + h.w); }); xs.push(x1);
        for (var i = 0; i < xs.length; i += 2) wallQ(xs[i], F[1], xs[i + 1], F[1], y0, y1, (opt.face && opt.face[F[0]]) || c, [0, F[2]]);
        hs.forEach(function (h) { wallQ(h.x - h.w, F[1], h.x + h.w, F[1], h.top, y1, (opt.face && opt.face[F[0]]) || c, [0, F[2]]); });
      });
      if (!(opt.skip && opt.skip.indexOf('W') >= 0)) wallQ(x0, z0, x0, z1, y0, y1, (opt.face && opt.face.W) || c, [-1, 0]);
      if (!(opt.skip && opt.skip.indexOf('E') >= 0)) wallQ(x1, z0, x1, z1, y0, y1, (opt.face && opt.face.E) || c, [1, 0]);
      if (opt.roof) g.flat([[x0, z0], [x1, z0], [x1, z1], [x0, z1]], y1, col(opt.roof));
    }
    // glazed bands on an outward face (the curtain wall seen from outside): mullion stripes over a dark glass colour
    function glazing(ax, az, bx, bz, y0, y1, n, every) {
      var L = Math.hypot(bx - ax, bz - az), k, ux = (bx - ax) / L, uz = (bz - az) / L, o = 0.03;
      wallQ(ax + n[0] * o, az + n[1] * o, bx + n[0] * o, bz + n[1] * o, y0 + 0.3, y1 - 0.4, '#3E5F7C', n);
      for (k = every; k < L - 0.1; k += every) {
        var px = ax + ux * k + n[0] * 0.06, pz = az + uz * k + n[1] * 0.06;
        wallQ(px - ux * 0.06, pz - uz * 0.06, px + ux * 0.06, pz + uz * 0.06, y0 + 0.3, y1 - 0.4, '#2E3440', n);
      }
      [3.4, 7.0, 10.6].forEach(function (yy) { wallQ(ax + n[0] * 0.05, az + n[1] * 0.05, bx + n[0] * 0.05, bz + n[1] * 0.05, yy, yy + 0.1, '#2E3440', n); });
    }
    var bx0 = 1e9, bx1 = -1e9, bz0 = 1e9, bz1 = -1e9;
    zones.forEach(function (z) { bx0 = Math.min(bx0, z.ox); bx1 = Math.max(bx1, z.ox + z.w); bz0 = Math.min(bz0, z.oz); bz1 = Math.max(bz1, z.oz + z.h); });
    var cx = (bx0 + bx1) / 2, cz = (bz0 + bz1) / 2;
    // ---- ground: grass to the horizon, the apron concrete east of the terminal and round the hangar, the runway
    g.flat([[cx - 700, cz - 700], [cx + 700, cz - 700], [cx + 700, cz + 700], [cx - 700, cz + 700]], GY - 0.05, col('#86AE55'));
    var ax0 = bx0 - 70, ax1 = bx1 + 120, az0 = bz0 - 40, az1 = Z1.oz + Z1.h + 2;
    g.flat([[ax0, az0], [ax1, az0], [ax1, az1], [ax0, az1]], GY, col('#B9B7AF'));
    // apron joints and stand lines (painted strips)
    for (var jx = Math.ceil(ax0 / 7.5) * 7.5; jx < ax1; jx += 7.5) g.flat([[jx - 0.03, az0], [jx + 0.03, az0], [jx + 0.03, az1], [jx - 0.03, az1]], GY + 0.01, col('#A7A59D'));
    var X1 = Z1.ox + Z1.w;   // the terminal's east face (the curtain wall)
    var stands = [Z1.oz + 26.5, Z1.oz + 58, Z1.oz - 22, Z1.oz - 58];   // stand centre lines (z) east of the terminal
    stands.forEach(function (sz) {
      g.flat([[X1 + 2, sz - 0.12], [X1 + 50, sz - 0.12], [X1 + 50, sz + 0.12], [X1 + 2, sz + 0.12]], GY + 0.02, col('#F5C431'));
      g.flat([[X1 + 9, sz - 2.5], [X1 + 9.4, sz - 2.5], [X1 + 9.4, sz + 2.5], [X1 + 9, sz + 2.5]], GY + 0.02, col('#E04A3A'));
    });
    // the taxiway (asphalt, yellow centre line) and the runway (dark asphalt, white centre dashes, edge lines,
    // threshold bars) running north - south east of the stands
    var tx = X1 + 70, rx = X1 + 130;
    g.flat([[tx - 12, cz - 400], [tx + 12, cz - 400], [tx + 12, cz + 400], [tx - 12, cz + 400]], GY + 0.005, col('#6A6B6E'));
    g.flat([[tx - 0.15, cz - 400], [tx + 0.15, cz - 400], [tx + 0.15, cz + 400], [tx - 0.15, cz + 400]], GY + 0.015, col('#F5C431'));
    g.flat([[rx - 25, cz - 600], [rx + 25, cz - 600], [rx + 25, cz + 600], [rx - 25, cz + 600]], GY + 0.005, col('#55565A'));
    for (var rz = cz - 590; rz < cz + 590; rz += 50) g.flat([[rx - 0.45, rz], [rx + 0.45, rz], [rx + 0.45, rz + 30], [rx - 0.45, rz + 30]], GY + 0.015, col('#F4F2EA'));
    [-23.5, 23.5].forEach(function (o) { g.flat([[rx + o - 0.4, cz - 600], [rx + o + 0.4, cz - 600], [rx + o + 0.4, cz + 600], [rx + o - 0.4, cz + 600]], GY + 0.015, col('#F4F2EA')); });
    for (var tb = -21; tb <= 21; tb += 3.5) g.flat([[rx + tb - 0.9, cz - 560], [rx + tb + 0.9, cz - 560], [rx + tb + 0.9, cz - 530], [rx + tb - 0.9, cz - 530]], GY + 0.015, col('#F4F2EA'));
    for (var cn = -2; cn <= 2; cn++) {   // connectors from the apron to the taxiway
      var cz2 = cz + cn * 70;
      g.flat([[X1 + 50, cz2 - 10], [tx, cz2 - 10], [tx, cz2 + 10], [X1 + 50, cz2 + 10]], GY + 0.004, col('#6A6B6E'));
      g.flat([[X1 + 50, cz2 - 0.15], [tx, cz2 - 0.15], [tx, cz2 + 0.15], [X1 + 50, cz2 + 0.15]], GY + 0.016, col('#F5C431'));
    }
    // ---- the shells: the terminal (glass faces east and south), the corridors, the hangar, the ops building
    var T0 = { x0: Z1.ox - 0.6, z0: Z1.oz - 0.6, x1: Z1.ox + Z1.w + 0.6, z1: Z1.oz + Z1.h + 0.6 };
    var tr = level.trails[0];
    shell(T0.x0, T0.z0, T0.x1, T0.z1, GY, 14.6, '#E8E6DE', { roof: '#C9C6BE', holes: [{ side: 'N', x: tr.x, w: 2.6, top: 14.0 }] });
    glazing(T0.x1, Z1.oz, T0.x1, Z1.oz + 41, 0, 14.0, [1, 0], 3);
    glazing(T0.x0, T0.z1, T0.x1, T0.z1, 0, 14.0, [0, 1], 3);
    shell(tr.x - 2.6, tr.z1, tr.x + 2.6, tr.z0, GY, 14.0, '#DCDCD6', { skip: 'NS', roof: '#B9B7AF' });
    var H0 = { x0: Z2.ox - 0.6, z0: Z2.oz - 0.6, x1: Z2.ox + Z2.w + 0.6, z1: Z2.oz + 44.5 };
    shell(H0.x0, H0.z0, H0.x1, H0.z1, GY, 14.6, '#C9D1D6', { skip: 'S', roof: '#A3AEB5', holes: [{ side: 'N', x: level.hatch.x, w: 2.6, top: 14.0 }],
      face: { N: '#C9D1D6', W: '#C9D1D6', E: '#C9D1D6' } });
    // the hangar's arched roof above its parapet (a low gable seen from far), the apron's retaining wall, the ops block
    g.box(Z2.ox + Z2.w / 2, 15.3, Z2.oz + 22, Z2.w + 1.2, 1.4, 45, col('#A3AEB5'), { hull: false, noBottom: true });
    shell(Z2.ox - 0.6, Z2.oz + 44.5, Z2.ox + Z2.w + 0.6, Z2.oz + Z2.h - 1, GY, 0.0, '#9F9B92', { skip: 'NS' });
    shell(Z2.ox - 0.6, Z2.oz + Z2.h - 1, Z2.ox + Z2.w + 0.6, Z2.oz + Z2.h + 0.6, GY, 14.6, '#BDBAB2', { skip: 'N', roof: '#8F8C85',
      holes: [{ side: 'S', x: tr.x, w: 2.6, top: 14.0 }] });
    // ---- landside: the elevated departures road along the terminal's south face, its columns, taxis and cars
    var ry0 = T0.z1 + 0.2, ry1 = ry0 + 13;
    g.box(cx, -0.25, (ry0 + ry1) / 2, bx1 - bx0 + 160, 0.5, ry1 - ry0, col('#6A6B6E'), { hull: false, topTint: col('#5E6064') });
    g.flat([[bx0 - 80, ry0], [bx1 + 80, ry0], [bx1 + 80, ry0 + 4], [bx0 - 80, ry0 + 4]], 0.01, col('#CFC8BC'));   // the kerb
    g.flat([[bx0 - 80, ry1 - 0.3], [bx1 + 80, ry1 - 0.3], [bx1 + 80, ry1], [bx0 - 80, ry1]], 0.015, col('#F4F2EA'));
    for (var dx = bx0 - 80; dx < bx1 + 80; dx += 6) g.flat([[dx, ry0 + 8.4], [dx + 3, ry0 + 8.4], [dx + 3, ry0 + 8.6], [dx, ry0 + 8.6]], 0.015, col('#F4F2EA'));
    g.box(cx, 0.55, ry1 + 0.2, bx1 - bx0 + 160, 1.1, 0.4, col('#BDBAB2'), { hull: false });   // parapet
    for (var px = bx0 - 70; px < bx1 + 80; px += 18) g.box(px, GY / 2 - 0.25, (ry0 + ry1) / 2, 1.4, -GY - 0.5, 1.4, col('#BDBAB2'), { hull: false });
    // a parking structure beyond the road
    g.box(cx, 2.0, ry1 + 40, 120, 13, 50, col('#CFC8BC'), { hull: false });
    for (var lv = 0; lv < 4; lv++) g.box(cx, GY + 2.2 + lv * 3.4, ry1 + 14.9, 120.2, 0.9, 0.2, col('#5E6064'), { hull: false });
    g.box(cx, 8.7, ry1 + 14.9, 30, 1.2, 0.3, col('#1D2B4F'), { hull: false });
    // ---- pieces: aircraft, the jet bridge, the tower, the fuel farm, cargo sheds, cars and taxis on the kerb
    var parts = {};
    function put(name, m4, paint) {
      var full = IB.themePiece(theme, name), fam = IB.Assets.family[full];
      if (!fam) return;
      var geo = IB.Assets.placed(full, m4);
      if (paint) IB.Zones.repaint(geo, paint);
      (parts[fam] || (parts[fam] = [])).push(geo);
    }
    var _q = new THREE.Quaternion(), _up = new THREE.Vector3(0, 1, 0), _p = new THREE.Vector3(), _s = new THREE.Vector3();
    function M(x, y, z, yaw, s, sx) { _q.setFromAxisAngle(_up, yaw); _p.set(x, y, z); _s.set(sx || s || 1, s || 1, s || 1); return new THREE.Matrix4().compose(_p, _q, _s); }
    // an aircraft: the body, both engines (local x = +/-6, 1.2 m up, centred 2 m ahead of the body's centre)
    var LIVERY = [null, [[25, 29], [27, 28]], [[25, 28], [27, 26]], [[25, 37], [27, 8]]];   // Skylark, AeroVale, NorthStar, Coral
    function jet(x, z, yaw, livery, s) {
      s = s || 1;
      var paint = LIVERY[livery] || null, c = Math.cos(yaw), sn = Math.sin(yaw);
      put('Jet_Line', M(x, GY, z, yaw, s), paint);
      [-6, 6].forEach(function (ex) {
        var lx = ex * s, lz = 2.0 * s;   // three local (x, z) -> world (yaw about Y)
        put('Engine', M(x + lx * c + lz * sn, GY + 1.2 * s, z - lx * sn + lz * c, yaw, s), paint);
      });
    }
    // gate A3: nose-in at the curtain wall (nose 8 m out), the jet bridge from the rotunda to the forward door
    var a3z = Z1.oz + 26.5, noseX = X1 + 8.0, bodyX = noseX + 16.5;
    jet(bodyX, a3z, -Math.PI / 2, 0);
    // the forward door (local x +1.95 (port), body y -9.45: 7.05 m behind the nose) faces south (+Z) here; its sill
    // is 1.75 m under the departures floor. The rotunda stands at the curtain wall 9 m south of the jet's axis (the
    // gate's door, row 35), the tunnel runs from the rotunda's centre to the back of the cab, the cab's bellows (its
    // +X end) close on the door
    var doorX = noseX + 7.05, doorZ = a3z + 1.95, rot = { x: X1 + 0.65, z: a3z + 9.0 };
    put('Bk_Rotunda', M(rot.x, 0, rot.z, 0));
    var cabY = -1.75, cab = { x: doorX, z: doorZ + 1.75 };
    var P0 = { x: rot.x + 1.6, y: -0.15, z: rot.z }, P1 = { x: cab.x, y: cabY, z: cab.z + 1.2 };
    var tdx = P1.x - P0.x, tdz = P1.z - P0.z, tdy = P1.y - P0.y, tl = Math.hypot(tdx, tdz), tyaw = Math.atan2(-tdz, tdx);
    var tm = new THREE.Matrix4().compose(new THREE.Vector3(P0.x, P0.y, P0.z), new THREE.Quaternion().setFromAxisAngle(_up, tyaw), new THREE.Vector3(1, 1, 1));
    tm.multiply(new THREE.Matrix4().makeRotationZ(Math.atan2(tdy, tl))).multiply(new THREE.Matrix4().makeScale(Math.hypot(tl, tdy), 1, 1));
    put('Bk_Tunnel', tm);
    put('Bk_Drive', M(P0.x + tdx * 0.8, 0, P0.z + tdz * 0.8, tyaw));
    put('Bk_Cab', M(cab.x, cabY, cab.z, Math.PI / 2));
    // more aircraft: the next stands, remote stands, one on the taxiway, one lined up on the runway
    jet(bodyX + 2, Z1.oz + 58, -Math.PI / 2, 1);
    jet(bodyX, Z1.oz - 22, -Math.PI / 2, 2);
    jet(bodyX + 4, Z1.oz - 58, -Math.PI / 2, 3);
    jet(tx, cz + 60, Math.PI, 1);
    jet(rx, cz - 260, Math.PI, 0);
    jet(rx + 70, cz + 180, 0.4, 2, 0.9);
    // the control tower west of the hangar, the fuel farm and cargo sheds far north-east
    put('Bk_Tower', M(bx0 - 60, GY, Z2.oz + 10, 0.3));
    [[0, 0], [17, 4], [8, 18]].forEach(function (o) { put('Bk_Tank', M(bx1 + 60 + o[0], GY, bz0 - 70 + o[1], 0)); });
    put('Bk_Shed', M(bx1 + 20, GY, bz0 - 60, Math.PI));
    put('Bk_Shed', M(bx0 - 40, GY, bz0 - 50, Math.PI));
    put('Mast', M(X1 + 30, GY, Z1.oz + 42, 0));
    put('Mast', M(X1 + 30, GY, Z1.oz + 10, 0));
    put('Mast', M(X1 + 30, GY, Z1.oz - 40, 0));
    // landside traffic: taxis at the kerb, cars on the road
    var cars = [KH + 'Street_Taxi', KP + 'Sedan', KP + 'SUV', KH + 'Street_Taxi', KP + 'Hatchback', KP + 'Sedan', KH + 'Street_Taxi'];
    cars.forEach(function (n, i) {
      var lane = i % 3 === 0 ? ry0 + 5.2 : ry0 + 10.2, x = Z1.ox + 6 + i * 11 + hash(i, 3) * 3;
      put(n, M(x, 0, lane, i % 3 === 0 ? R90 : -R90));
    });
    put(KP + 'BoxTruck', M(Z1.ox - 12, 0, ry0 + 10.2, -R90));
    Object.keys(parts).forEach(function (fam) { level.root.add(new THREE.Mesh(IB.Assets.merge(parts[fam]), IB.Assets.mat[fam])); });
    // ---- the glows' life: status lights blink (camera domes, scanners, arches, bollards, half-down shutters)
    var blink = [];
    (level.glows || []).forEach(function (G) { if (G.def.groups) blink.push(G); });
    var RATE = { Cam_LED: 0.9, Scanner_LED: 0.6, Arch_LED: 1.4, Bollard_LED: 0.7, ShutterHalf_LED: 1.1, EGate_LED: 0.5, Gantry_LED: 1.7 };
    api.tick(function (dt, t) {
      for (var i = 0; i < blink.length; i++) {
        var b = blink[i], ph = (t * (RATE[b.piece] || 1) + b.group * 0.37 + b.zone * 0.11) % 1;
        b.mesh.visible = b.piece === 'Scanner_LED' || b.piece === 'EGate_LED' ? ph < 0.85 : ph < 0.55;
      }
    });
  }

  var WALLS = ['WT', 'CornerT', 'WG', 'WG_B', 'WG_M', 'CornerG', 'WC', 'CornerC', 'WH', 'CornerH', 'WF', 'WF_DoorA', 'WF_DoorB', 'CornerF',
    'WA', 'CornerA', 'WO', 'CornerO'];
  Object.keys(ART).forEach(function (S) { Object.keys(ART[S]).forEach(function (k) { var p = ART[S][k]; if (WALLS.indexOf(p) < 0) WALLS.push(p); }); });
  var OUTSIDE = ['Jet_Line', 'Engine', 'Bk_Rotunda', 'Bk_Tunnel', 'Bk_Drive', 'Bk_Cab', 'Bk_Tower', 'Bk_Tank', 'Bk_Shed', 'Mast'];
  var PIECES = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_C', 'Hatch', 'Stand', 'CeilLight']).concat(OUTSIDE);
  var BORROWED = [KH + 'Street_Taxi', KP + 'Sedan', KP + 'SUV', KP + 'Hatchback', KP + 'BoxTruck'];
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    if (d.deck) return;
    d.pieces.concat(d.full ? [d.full] : [], d.post ? [d.post] : [], d.conveyor ? d.conveyor.items : []).forEach(function (n) {
      if (/^KIT_/.test(n)) { if (BORROWED.indexOf(n) < 0) BORROWED.push(n); } else if (PIECES.indexOf(n) < 0) PIECES.push(n);
    });
  });
  Object.keys(GLOW).forEach(function (k) { [].concat(GLOW[k]).forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  IB.registerTheme({
    id: 'airport', name: 'Meridian International', family: 'kit-airport', prefix: 'KIT_AIRPORT_', families: ['kit-parking', 'kit-hotel', 'kit-police'],
    palette: ['#2C7BD9', '#F5C431', '#1D2B4F', '#F2F1EC'],
    env: {
      sky: ['#4F9FE6', '#D9EDF9'], fog: { color: '#D6E6F0', near: 70, far: 260 }, clouds: true,
      sun: [0.4, 0.85, 0.35],
      ceiling: { height: 14.0, color: '#FBF8F0', light: 'CeilLight', every: 8, clear: 'BIJKLXRqÄÖÊÀÁÂÃÈÌÍÎÒÓÔÙ', clearR: 1 }
    },
    // terrazzo with brass-coloured joints every 6 m
    floor: {
      color: '#D8D3C8', trail: '#CFCBC2', outside: '#B9B7AF',
      lines: [{ dir: 'x', every: 6, width: 0.03, color: '#B9AE98', y: 0.008 }, { dir: 'z', every: 6, width: 0.03, color: '#B9AE98', y: 0.0105 }]
    },
    wall: { height: 14.0, roof: '#C9C6BE', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.3, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall', 'TrailWall_C', 'TrailWall_B'], height: 14.0 },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: { build: buildOutside },
    budget: { prop: 3600, landmark: 6000, total: 110000 },
    allPieces: function () { return PIECES.slice(); },
    borrowed: function () { return BORROWED.slice(); },
    levels: {
      airport: {
        name: 'Meridian International',
        intro: 'Robots have taken the airport. Push through check-in and the automated security checkpoint to the gates, then out to Hangar 2.',
        zones: [
          // the terminal: check-in, security, the gates, the lounge, duty free, the mezzanine
          { map: 'airport_1', waves: [
            [['crawler', 22], ['gunner', 12], ['drone', 4]],
            [['crawler', 11], ['bomber', 2], ['gunner', 9], ['drone', 5], ['soldier', 6], ['blader', 4]],
            [['crawler', 10], ['drone', 6], ['gunner', 9], ['soldier', 6], ['blader', 3]],
            [['crawler', 10], ['bomber', 2], ['gunner', 9], ['drone', 5], ['blader', 3], ['soldier', 6]],
            [['crawler', 10], ['bomber', 1], ['gunner', 10], ['drone', 5], ['soldier', 5], ['blader', 3]]] },
          // Hangar 2 and the apron: the jet on its platforms, the GSE, the ops building
          { map: 'airport_2', waves: [
            [['crawler', 20], ['gunner', 11], ['drone', 5]],
            [['crawler', 11], ['bomber', 2], ['gunner', 9], ['drone', 5], ['blader', 4], ['soldier', 6]],
            [['crawler', 10], ['drone', 6], ['gunner', 9], ['soldier', 6], ['blader', 3]],
            [['crawler', 10], ['bomber', 2], ['gunner', 9], ['drone', 5], ['soldier', 6], ['blader', 3]],
            [['crawler', 10], ['bomber', 1], ['gunner', 10], ['drone', 5], ['soldier', 5], ['blader', 3]]], ceiling: false,
            floor: { color: '#B9B7AF', lines: [{ dir: 'x', every: 5, width: 0.03, color: '#A3A097', y: 0.008 }, { dir: 'z', every: 5, width: 0.03, color: '#A3A097', y: 0.0105 }] } }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
