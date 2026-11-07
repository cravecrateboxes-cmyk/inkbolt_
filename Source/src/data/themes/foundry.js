/* Theme: Titan Foundry (kit-foundry). The war foundry where the enemy builds what comes next: 30 m halls of indigo
   gunmetal plate over slate concrete plinths, stepped buttresses every 8 m with red beacons and stencilled bay numbers,
   a crane girder at 24 m, a glowing louvre band under the roof, crimson war banners (chevrons and stripes, no
   emblems); roof bays of deep plate girders with floodlight clusters, bridge cranes and long hanging banners. On the
   floor the NEW chassis in production: six-legged spider walkers riding a moving line through fitting tunnels, hounds
   and hover tanks on a second line, hover tanks and drone-carrier gunships riding an overhead monorail, weld cells,
   chassis jigs, test cells, a centipede crawler on its rack, spare reactor cores; the launch hall's rows of finished
   robots on dispatch pads. And the giants: the WARDEN titan (~24 m) as a bare frame on its jig under a goliath crane
   (zone 1), half armoured with its reactor glowing under a gantry walkway at 6 m that robots climb too (zone 2), and
   finished on its launch sled facing the sealed launch doors (zone 3); the STRIDER siege quad (~15 m) half built over
   its siege gun (zone 1) and finished (zone 3). Built by blender/fam_kit_foundry.py (+ foundry_bots.py,
   foundry_giants.py); zone layouts by tools/foundry_zones.py (src/data/zones/foundry_*.txt).

   Symbols (1 cell = 1 m; prefab sizes [x, z]):
     #  walls (zone edge only): buttress every 8 m, banner triples, bay numbers, pipes, ducts, panels, hoses; plain
        modules beside the gates, end modules beside the corners, flat backs behind the launch doors
     L  spider line [12, 8] (runs of 4: intake house + tunnel 1, tunnel 2, tunnel 3, dispatch house; moving line)
     U  hound / hover-tank line, same tiles
     W  weld cell [4, 4]    J  chassis jig [6, 4]    Q  test cell [6, 6]    K  centipede rack [10, 4]
     F  dispatch pad with a finished robot [4, 4]    R  spare reactor core [4, 4]
     p  armour plates [2, 2]   m  cannon shells [2, 2]   k  cable spool [2, 2]   l  limb rack [4, 2]   B  light mast [2, 2]
     c  crates   b  drums   x  carts / weld screens   g  jersey barrier   n  console
     T  titan frame bay [20, 14]   Y  titan armour bay with its gantry [24, 18]   Z  titan launch bay [20, 16]
     X  strider build bay [18, 18]   V  strider launch bay [18, 18]   D  launch door [18, 2] (against the south wall)
   Floor layer ("@layer 0", no collision): 1 lane line  2 hazard band  3 drain  4 oil  5 plate patch [2, 2]
     6 exit chevrons [2, 2]  8 launch rail  9 launch-lane paint  0 keep-clear box [2, 2]
     o  overhead monorail, wall to wall (cells; carriers ride it high over the floor and the lines, ports at the ends)
   Gantry layer ("@layer 6", zone 2): spawns and pickups standing on the bay's walkway decks. */
(function (IB) {
  'use strict';
  function gateDist(g, c, r) {   // cells from a north / south wall cell to the centre of that wall's gate
    if (r !== 0 && r !== g.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < g.w; x++) if (g.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  // the monorail ('o') lives in the zone's "@layer 0" overlay (it may pass over the lines)
  function railAt(g, c, r) {
    if (g.at(c, r) === 'o') return true;
    for (var i = 0; i < (g.layers || []).length; i++) if (g.layers[i].at(c, r) === 'o') return true;
    return false;
  }
  function hh(a, b) { var h = Math.sin(a * 12.9898 + b * 78.233) * 43758.5453; return h - Math.floor(h); }
  var SIDE = { S: 1, W: 2, N: 3, E: 4 };   // stencilled bay numbers: first digit = the wall, second = the bay
  // a war banner hangs over the three modules around u0 (u0 % 8 == 0) when all three are ordinary modules: away from
  // the gates, the corners, the launch doors and the monorail ports
  function bannerOK(g, face, c, r, u0, n) {
    var ns = face === 'S' || face === 'N', bay = Math.floor((u0 + 4) / 8);
    if (hh(bay * 7 + SIDE[face], n) >= 0.55 || u0 - 1 < 2 || u0 + 1 > n - 3) return false;
    if (ns) {
      if (gateDist(g, u0, r) < 6.0) return false;
      for (var k = -1; k <= 1; k++) if (g.at(u0 + k, r + (face === 'S' ? 1 : -1)) === 'D') return false;
    } else {
      for (var d = -3; d <= 3; d++) if (railAt(g, c + (face === 'E' ? 1 : -1), u0 + d)) return false;
    }
    return true;
  }
  /* Zone-edge wall modules. u runs along the wall (c on the north / south walls, r on the west / east walls); a
     buttress every 8 m (u % 8 == 4), in some bays a war banner over three modules (u % 8 == 7, 0, 1) and a two-digit
     bay number beside the buttress (u % 8 == 2, 3); pipes, ducts, panels and hoses between. The module's local +X runs
     toward +u on S / W faces and toward -u on N / E faces (the engine turns each module to face the room), so banner
     halves and digits swap there. Corner cells get the corner post, the cells beside them end modules whose details
     stop short of it, the cells beside a gate plain ones, the cells behind a launch door flat backs. */
  function chooseWall(c, r, horiz, corner, hash, g, face) {
    if (face === 'none' || face === 'corner') return 'Corner_' + (r < g.h / 2 ? 'N' : 'S') + (c < g.w / 2 ? 'W' : 'E');
    var ns = face === 'S' || face === 'N', u = ns ? c : r, n = ns ? g.w : g.h, plusHi = face === 'S' || face === 'W';
    var front = g.at(c + (face === 'E' ? 1 : face === 'W' ? -1 : 0), r + (face === 'S' ? 1 : face === 'N' ? -1 : 0));
    if (front === 'D') return 'Wall_Back';
    // beside a monorail port (the rail runs into the east / west wall): plain modules, the port covers them
    if (!ns) for (var dr = -2; dr <= 2; dr++) if (railAt(g, c + (face === 'E' ? 1 : -1), r + dr)) return 'Wall_Plain';
    if (u === 1) return plusHi ? 'Wall_EndL' : 'Wall_EndR';
    if (u === n - 2) return plusHi ? 'Wall_EndR' : 'Wall_EndL';
    var gd = gateDist(g, c, r);
    if (gd < 2.6) return 'Wall_GateIn';
    if (gd < 4.0) return 'Wall_Gate';
    var m = u % 8, bay = Math.floor((u + 4) / 8);
    if (m === 4 && u > 3 && u < n - 4 && gd > 4.6) return 'Pilaster';
    var banner = (m === 7 || m === 0 || m === 1) && bannerOK(g, face, c, r, m === 7 ? u + 1 : m === 1 ? u - 1 : u, n);
    if (banner) {
      if (m === 0) return 'Wall_BanM';
      return (m === 7) === plusHi ? 'Wall_BanL' : 'Wall_BanR';
    }
    if (m === 2 || m === 3) {
      var tens = (m === 2) === plusHi;
      return 'Wall_Num' + (tens ? SIDE[face] : bay % 10);
    }
    if (m === 5) return hh(bay, SIDE[face] * 3) < 0.5 ? 'Wall_Pipes' : 'Wall_Duct';
    if (m === 6) { var h6 = hh(bay * 3 + 1, SIDE[face]); return h6 < 0.3 ? 'Wall_Panel' : h6 < 0.5 ? 'Wall_Hose' : 'Wall_Plain'; }
    return 'Wall_Plain';
  }
  var WALLS = ['Wall_Plain', 'Wall_Pipes', 'Wall_Duct', 'Wall_Panel', 'Wall_Hose', 'Wall_BanL', 'Wall_BanM', 'Wall_BanR', 'Wall_Gate',
    'Wall_GateIn', 'Wall_Back', 'Wall_EndL', 'Wall_EndR', 'Pilaster', 'Corner_NW', 'Corner_NE', 'Corner_SW', 'Corner_SE'];
  for (var d = 0; d < 10; d++) WALLS.push('Wall_Num' + d);
  var BAYS = ['CeilBay', 'CeilBay_Crane', 'CeilBay', 'CeilBay', 'CeilBay_Banner', 'CeilBay', 'CeilBay_Crane'];
  // a moving chassis line: runs of [Line_Feed, Line_Mid, Line_Mid, Line_Out]; the chassis pop in inside the intake
  // house, change stage in the middle of each fitting tunnel (tile-local x = 3.5) and pop out inside the dispatch house
  function line(items) {
    return { size: [12, 8], pieces: ['Line_Feed', 'Line_Mid', 'Line_Out'], sequence: 'run', kind: 'wall',
      conveyor: { speed: 0.5, dir: 1, y: 0, spacing: 8.0, inset: 2.0, items: items, stations: { Line_Feed: 3.5, Line_Mid: 3.5 },
        cleat: 'Line_Slat', cleatEvery: 1.0, cleatY: 0.093 } };
  }
  // the giants: one prefab per bay, the titan / strider parts placed with it (`with`), each within the piece budget
  function bay(size, piece, parts, y) { var w = {}; w[piece] = parts; return { size: size, pieces: [piece], face: 0, kind: 'wall', y: y || 0, with: w }; }

  IB.registerTheme({
    id: 'foundry', name: 'Titan Foundry', family: 'kit-foundry', prefix: 'KIT_FOUNDRY_',
    palette: ['#3D4459', '#C8303A', '#F2B530', '#55E3F2'],
    env: {
      // sealed halls: no sky; a cold blue-grey haze that swallows the roof 30 m up; light from high in front
      sky: null, clear: '#4A5068', fog: { color: '#4A5068', near: 46, far: 185 }, clouds: false,
      sun: [0.32, 0.82, 0.47],
      ceiling: { height: 30.0, color: '#272B39', light: BAYS, every: 12, clear: 'TYZXVD', clearR: 7 }
    },
    // dark concrete with 2 m plate seams and 8 m expansion joints (decals on top come from the zone's "@layer 0")
    floor: {
      color: '#5B5F6F', trail: '#555968', outside: '#3A3E4C',
      lines: [{ dir: 'x', every: 2, width: 0.035, color: '#4D5060', y: 0.008 }, { dir: 'z', every: 2, width: 0.035, color: '#4D5060', y: 0.0105 },
        { dir: 'x', every: 8, width: 0.11, color: '#444756', y: 0.013 }, { dir: 'z', every: 8, width: 0.11, color: '#444756', y: 0.0155 }]
    },
    wall: { height: 30.4, roof: '#272B39', facing: 'open', choose: chooseWall, cols: true },   // cols: the buttresses collide
    symbols: {
      'L': line([['Spider_0', 'Spider_1', 'Spider_2', 'Spider_3']]),
      'U': line([['Hound_0', 'Hound_1'], ['Hover_0', 'Hover_1', 'Hover_2']]),
      'o': { pieces: ['ORail_Hang', 'ORail', 'ORail', 'ORail'], alternate: true, rotate: 'run', collide: false,
             conveyor: { speed: 0.8, dir: 'alt', y: 0, spacing: 9.0, inset: 2.5, ends: { start: 'ORail_PortIn', end: 'ORail_PortOut', at: 2.5 },
                         items: ['Carrier_Hover', 'Carrier_Gunship'] } },
      'W': { size: [4, 4], pieces: ['WeldCell_Spider', 'WeldCell_Hover'], flip: true, kind: 'cover' },
      'J': { size: [6, 4], pieces: ['Jig_Hover', 'Jig_Hound'], kind: 'cover' },
      'Q': { size: [6, 6], pieces: ['TestCell_Hound', 'TestCell_Spider'], sequence: true, kind: 'wall' },
      'K': { size: [10, 4], pieces: ['CentipedeRack'], flip: true, kind: 'cover' },
      'F': { size: [4, 4], pieces: ['Pad_Spider', 'Pad_Hound', 'Pad_Hover'], kind: 'cover' },
      'R': { size: [4, 4], pieces: ['ReactorCradle'], kind: 'cover' },
      'p': { size: [2, 2], pieces: ['Plates_Stack', 'Plates_Rack'], kind: 'cover' },
      'm': { size: [2, 2], pieces: ['Shells'], kind: 'cover' },
      'k': { size: [2, 2], pieces: ['Spool'], kind: 'cover' },
      'l': { size: [4, 2], pieces: ['LimbRack'], flip: true, kind: 'cover' },
      'B': { size: [2, 2], pieces: ['FloodTower'], flip: true, kind: 'cover' },
      'c': { pieces: ['Crate_Ammo', 'Crate_Bin'], h: 0.95, rotate: 'random90', stack: { piece: 'Crate_Lid', chance: 0.3, h: 0.5 }, kind: 'cover' },
      'b': { pieces: ['Drums_A', 'Drums_B'], h: 1.0, rotate: 'random90', kind: 'cover' },
      'x': { pieces: ['Cart_Gas', 'Cart_Chest', 'Cart_Screen'], h: 1.2, rotate: 'random90', sequence: true, kind: 'cover' },
      'g': { pieces: ['Barrier'], h: 0.85, rotate: 'run', kind: 'cover' },
      'n': { pieces: ['Console'], h: 1.2, rotate: 'random90', kind: 'cover' },
      'T': bay([20, 14], 'Landmark_Bay_Frame', ['Landmark_Titan_LegsFrame', 'Landmark_Titan_TorsoFrame']),
      'Y': bay([24, 18], 'Landmark_Bay_Armour', ['Landmark_Bay_ArmourDeck', 'Landmark_Titan_Legs', 'Landmark_Titan_TorsoHalf', 'Landmark_Titan_ArmL', 'Landmark_Titan_GunHung']),
      'Z': bay([20, 16], 'Landmark_Bay_Launch', ['Landmark_Titan_Legs', 'Landmark_Titan_Torso', 'Landmark_Titan_ArmL', 'Landmark_Titan_ArmGun'], 0.9),
      'X': bay([18, 18], 'Landmark_Bay_Strider', ['Landmark_Strider_Legs', 'Landmark_Strider_HullHalf']),
      'V': bay([18, 18], 'Landmark_Bay_StriderLaunch', ['Landmark_Strider_Legs', 'Landmark_Strider_Hull'], 0.9),
      'D': { size: [18, 2], pieces: ['Landmark_LaunchDoor1', 'Landmark_LaunchDoor2'], sequence: true, face: Math.PI, kind: 'wall' },
      // floor layer (no collision)
      '1': { pieces: ['Decal_Lane'], rotate: 'run', collide: false },
      '2': { pieces: ['Decal_Band'], rotate: 'run', collide: false },
      '3': { pieces: ['Decal_Drain'], collide: false },
      '4': { pieces: ['Decal_Oil'], rotate: 'random90', collide: false },
      '5': { size: [2, 2], pieces: ['Decal_Patch'], collide: false },
      '6': { size: [2, 2], pieces: ['Decal_Arrow'], face: 0, collide: false },
      '8': { pieces: ['Decal_Rail'], rotate: 'run', collide: false },
      '9': { pieces: ['Decal_LaneR'], rotate: -Math.PI / 2, collide: false },
      '0': { size: [2, 2], pieces: ['Decal_Grid'], collide: false }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 30.4, end: 'TrailWall', endYaw: Math.PI / 2, endLift: 0 },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: null,
    budget: { prop: 3800, landmark: 5600, total: 100000 },
    allPieces: function () {
      var out = WALLS.concat(BAYS, ['GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Stand']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        var S = sym[ch];
        S.pieces.concat(S.stack ? [S.stack.piece] : [], IB.conveyorPieces(S.conveyor)).forEach(function (n) { out.push(n); });
        if (S.with) Object.keys(S.with).forEach(function (k) { S.with[k].forEach(function (n) { out.push(n); }); });
      });
      return out.filter(function (n, i) { return out.indexOf(n) === i; });
    },
    levels: {
      foundry: {
        name: 'Titan Foundry',
        intro: 'They are building titans. Cut through the chassis hall, the armour hall and the launch hall before they wake.',
        zones: [
          // Chassis Hall: the titan frame and the strider bay to the north, the spider line across the middle
          { map: 'foundry_1', waves: [[['crawler', 21], ['gunner', 6]], [['crawler', 6], ['bomber', 5], ['gunner', 5], ['blader', 7]], [['crawler', 5], ['drone', 6], ['gunner', 5], ['soldier', 7]], [['crawler', 5], ['bomber', 5], ['gunner', 6], ['soldier', 8]]] },
          // Armour Hall: robots hold the titan's gantry walkway; drones over the hound line
          { map: 'foundry_2', waves: [[['crawler', 21], ['gunner', 6], ['drone', 4]], [['crawler', 6], ['bomber', 6], ['gunner', 6], ['blader', 7]], [['crawler', 6], ['drone', 6], ['gunner', 6], ['soldier', 7]], [['crawler', 5], ['bomber', 5], ['gunner', 6], ['blader', 7]]] },
          // Launch Hall: the finished titan and strider face the launch doors; the heaviest finale of the campaign so far
          { map: 'foundry_3', waves: [[['crawler', 22], ['gunner', 9]], [['crawler', 6], ['bomber', 6], ['drone', 6], ['soldier', 8]], [['crawler', 8], ['gunner', 8], ['drone', 6], ['blader', 7]], [['crawler', 9], ['gunner', 9], ['bomber', 8], ['drone', 5], ['soldier', 13]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
