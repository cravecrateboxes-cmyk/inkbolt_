/* Theme: Rustmoor Salvage (kit-scrapyard). A massive scrapyard at night among the remains of enormous abandoned war
   machines. Open sky (dark blue-black, a moon and stars drawn by backdrop.build), dark fog; the yard is lit by its own
   sodium floodlights (pools of light painted on the ground), cold blue glows from dead reactor cores and blinking red
   warning beacons (theme.glow: lenses, windows and cores drawn unlit; beacon domes in <Piece>_Blink companions that
   blink in two phase groups). Scrap bank walls (9.6 m) close every zone.
   Zone 1, the Stacks: the haul road from the entry to the exit past the weighbridge and its office (a stair to the
   railed roof at 3.15 m); west of it canyons of crushed-car bale stacks (tall and low stacks mixed, cross cuts) under a
   scrap mountain, the dead-tech piles (CRT monitors, toppled server racks, cable drums, e-waste) and the
   flattened-car stacks; a bale median splits the road into two lanes; north-east the car baler under the
   material-handling crane (its electromagnet holds a car over the charging box; operator platform at 2.4 m); east,
   wrecked giant limbs (a hand, a leg, a foot, a forearm) and broken giant guns (a rifle, a rotary cannon) lie among
   scrap mounds; floodlight towers throw pools of light.
   Zone 2, the Titan Graveyard: the kneeling dead titan (21 m, one knee down, its fist braced on the ground, slumped
   over the yard; walk between its legs to the exit), its torn-off arm and the salvage scaffold (decks at 3 and 6 m);
   the fallen torso lying on its side (walk in at the waist, past its glowing reactor, out at the neck); the ribcage
   frame with plating ramps up to decks at 3.0 and 5.4 m; the enormous head with three dead eye lenses; the colossal
   broken cannon; dead reactor cores among beacon posts; armour plates standing in the ground.
   Built by blender/fam_kit_scrapyard.py (sy_base / sy_stacks / sy_titans.py); zone layers by tools/scrapyard_zones.py.
   The forklift, the burnt / smashed car wrecks and the oil drums are kit-parking pieces (theme option `families`).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells):
     #  scrap bank wall (zone 1 rust and car scrap, zone 2 the graveyard's gunmetal and armour); corners: scrap lumps
     K  tall bale stack [2, 2] (2-4 crushed-car bales, car colours repainted per stack)   k  low bale stack [2, 2] (1-2)
     Q  flattened-car stack [2, 4]   H  scrap mountain [10, 10]   m  scrap mound [4, 4]   T  floodlight tower [2, 2]
     O  weighbridge office [8, 6] (door south, the scale window east, stair up the back to the roof deck)
     Z  the baler line [14, 12] with the material-handling crane (placed with it) south of it, the magnet over the box
     Y  giant hand [4, 4]   F  giant foot [4, 3]   L  giant leg [8, 3]   A  giant forearm [6, 3] (war paint per copy)
     R  giant broken rifle [10, 3]   N  giant rotary cannon [6, 3]
     M  CRT monitor pile [3, 3]   V  toppled server racks [4, 2]   D  cable drum [2, 2]   d  small cable spool
     x  e-waste stillage (stacks)   t  tyre stack   B  skip [4, 2]   j  jersey barrier (runs)
     W  car wreck [2, 4] (kit-parking)   X  forklift [2, 3] (kit-parking)   o  oil drums (kit-parking)
     I  the kneeling titan [22, 20] (Landmark_Titan + Landmark_TitanUpper)   J  the fallen torso [18, 10] (walk-through)
     q  the giant head [10, 10]   r  the ribcage with its ramps [18, 12]   C  the broken cannon [20, 4]
     U  dead reactor core [4, 4] (standing / split open)   n  salvage scaffold [12, 4]   e  the torn-off arm [12, 4]
     p  armour plates in the ground [3, 1]   b  warning beacon post
   "@layer 0" (no walls): w  the weighbridge deck [4, 10]   u  oil stain [2, 2]; on wall cells the wall codes the
     chooser reads: 1 RUSTMOOR SALVAGE sign, 2 DANGER sign, 3 a crushed car in the bank, 4 tyres, 5 a reactor leak,
     6 an armour plate, 7 titan fingers; 9 on the corner cell (0, 0) marks the graveyard (zone 2's banks).
   Light pools on the ground: each kind at its own height (wall lamps one kind per facing, towers, reactor glows). */
(function (IB) {
  'use strict';
  var SOLID = '#GE';
  function solid(grid, c, r) { return SOLID.indexOf(grid.at(c, r)) >= 0; }
  // same facing rule as zones.js buildWalls: the open side of a wall cell ('S','N','E','W', 'corner' or 'none')
  function faceOf(grid, c, r) {
    var oS = !solid(grid, c, r + 1), oN = !solid(grid, c, r - 1), oE = !solid(grid, c + 1, r), oW = !solid(grid, c - 1, r);
    var n = oS + oN + oE + oW;
    if (n === 0) return 'none';
    if (n === 1) return oS ? 'S' : oN ? 'N' : oE ? 'E' : 'W';
    return ((oS || oN) && (oE || oW)) ? 'corner' : (oS ? 'S' : 'E');
  }
  function codeAt(grid, c, r) {
    if (grid._syL0 === undefined) {
      grid._syL0 = null;
      (grid.layers || []).forEach(function (L) { if (L.y < 1) grid._syL0 = L; });
    }
    return grid._syL0 ? grid._syL0.at(c, r) : '.';
  }
  function isGrave(grid) { return codeAt(grid, 0, 0) === '9'; }
  // cells u-k .. u+k along the run are all straight wall with the same facing and no wall code
  function runOK(grid, c, r, F, k) {
    var along = F === 'S' || F === 'N';
    for (var d = -k; d <= k; d++) {
      var x = along ? c + d : c, y = along ? r : r + d;
      if (grid.at(x, y) !== '#' || faceOf(grid, x, y) !== F || (codeAt(grid, x, y) !== '.' && !(x === 0 && y === 0))) return false;
    }
    return true;
  }
  var CODE1 = { '1': 'Bank_Sign1', '2': 'Bank_Sign2', '3': 'Bank_Car', '4': 'Bank_Tyres' };
  var CODE2 = { '2': 'Grave_Sign', '4': 'Grave_Tyres', '5': 'Grave_Leak', '6': 'Grave_Plate', '7': 'Grave_Finger' };
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var F = face || faceOf(grid, c, r), code = codeAt(grid, c, r), u = (F === 'S' || F === 'N') ? c : r, g = isGrave(grid);
    var P = g ? 'Grave_' : 'Bank_';
    if (F === 'none' || F === 'corner') return P + (hash(c * 7 + 1, r * 5 + 3) < 0.5 ? 'Corner_A' : 'Corner_B');
    var coded = (g ? CODE2 : CODE1)[code];
    if (coded) return coded;
    // sodium lamps on brackets every 9 m on long straight runs (one pool height per facing, so facing pools never fight)
    if (u % 9 === 4 && runOK(grid, c, r, F, 3)) return P + 'Lamp' + F;
    var h = hash(c * 5 + 1, r * 11 + 7);
    if (g) return h < 0.08 ? 'Grave_Tyres' : h < 0.14 ? 'Grave_Plate' : h < 0.2 ? 'Grave_Finger' : (h < 0.6 ? 'Grave_A' : 'Grave_B');
    return h < 0.07 ? 'Bank_Tyres' : h < 0.12 ? 'Bank_Car' : ['Bank_A', 'Bank_B', 'Bank_C'][Math.min(2, Math.floor((h - 0.12) / 0.88 * 3))];
  }
  var WALLS = ['Bank_A', 'Bank_B', 'Bank_C', 'Bank_Tyres', 'Bank_Car', 'Bank_LampS', 'Bank_LampN', 'Bank_LampE', 'Bank_LampW',
    'Bank_Sign1', 'Bank_Sign2', 'Bank_Corner_A', 'Bank_Corner_B', 'Grave_A', 'Grave_B', 'Grave_Plate', 'Grave_Finger', 'Grave_Tyres',
    'Grave_LampS', 'Grave_LampN', 'Grave_LampE', 'Grave_LampW', 'Grave_Sign', 'Grave_Leak', 'Grave_Corner_A', 'Grave_Corner_B'];

  // palette cells (blender/sy_base.py order): the car paints 22-29; war paint bone 32/33, olive 34/35, crimson 36/37,
  // navy 38/39. Paint jobs move a piece's cells onto others per placed copy (zones.js symbol option `paint`).
  var CARS = [22, 23, 24, 25, 26, 27, 28, 29];
  var CAR_JOBS = [CARS, [24, 26, 22, 28, 23, 29, 25, 27], [27, 22, 29, 24, 28, 23, 26, 25], [25, 28, 26, 23, 29, 22, 27, 24],
    [29, 25, 23, 27, 22, 24, 28, 26], [26, 29, 28, 22, 24, 27, 23, 25]];
  var CAR_PAINT = { from: CARS, to: CAR_JOBS };
  var WAR = [32, 33, 34, 35, 36, 37];
  var WAR_PAINT = { from: WAR, to: [WAR, [32, 33, 38, 39, 36, 37], [34, 35, 32, 33, 38, 39], [32, 33, 36, 37, 34, 35]] };
  var KP = 'KIT_PARKING_';
  var SYMBOLS = {
    // ---- the Stacks
    'K': { size: [2, 2], pieces: ['Bales_2', 'Bales_3', 'Bales_4', 'Bales_3'], flip: true, paint: CAR_PAINT, kind: 'wall' },
    'k': { size: [2, 2], pieces: ['Bales_1', 'Bales_2', 'Bales_1'], flip: true, paint: CAR_PAINT, kind: 'cover' },
    'Q': { size: [2, 4], pieces: ['Pancakes_A', 'Pancakes_B'], flip: true, paint: CAR_PAINT, kind: 'cover' },
    'H': { size: [10, 10], pieces: ['Heap_A', 'Heap_B'], flip: true, kind: 'wall' },
    'm': { size: [4, 4], pieces: ['Mound_A', 'Mound_B'], flip: true, kind: 'cover' },
    'T': { size: [2, 2], pieces: ['FloodTower'], kind: 'wall' },
    'O': { size: [8, 6], pieces: ['Landmark_Office'], face: 0, kind: 'wall' },
    'Z': { size: [14, 12], pieces: ['Landmark_Baler'], face: 0, with: { Landmark_Baler: ['Landmark_Crane'] }, kind: 'wall' },
    'Y': { size: [4, 4], pieces: ['Hand'], flip: true, paint: WAR_PAINT, kind: 'cover' },
    'F': { size: [4, 3], pieces: ['Foot'], flip: true, paint: WAR_PAINT, kind: 'cover' },
    'L': { size: [8, 3], pieces: ['Leg'], flip: true, paint: WAR_PAINT, kind: 'cover' },
    'A': { size: [6, 3], pieces: ['Forearm'], flip: true, paint: WAR_PAINT, kind: 'cover' },
    'R': { size: [10, 3], pieces: ['Rifle'], flip: true, kind: 'cover' },
    'N': { size: [6, 3], pieces: ['Minigun'], flip: true, kind: 'cover' },
    'M': { size: [3, 3], pieces: ['Monitors_A', 'Monitors_B'], flip: true, kind: 'cover' },
    'V': { size: [4, 2], pieces: ['Racks'], flip: true, kind: 'cover' },
    'D': { size: [2, 2], pieces: ['CableDrum'], flip: true, kind: 'cover' },
    'd': { pieces: ['Spool_A', 'Spool_B'], rotate: 'random90', kind: 'cover' },
    'x': { pieces: ['Ewaste'], h: 0.92, rotate: 'random90', stack: { piece: 'Ewaste', chance: 0.35, h: 0.92 }, kind: 'cover' },
    't': { pieces: ['Tyres'], rotate: 'random90', kind: 'cover' },
    'B': { size: [4, 2], pieces: ['Skip_A', 'Skip_B'], flip: true, kind: 'cover' },
    'j': { pieces: ['Barrier_A', 'Barrier_B'], rotate: 'run', alternate: true, kind: 'cover' },
    'W': { size: [2, 4], pieces: [KP + 'Wreck_Burnt', KP + 'Wreck_Burnt_B'], flip: true, kind: 'cover' },
    'X': { size: [2, 3], pieces: [KP + 'Forklift'], flip: true, kind: 'cover' },
    'o': { pieces: [KP + 'Drums'], rotate: 'random90', kind: 'cover' },
    // ---- the Titan Graveyard
    'I': { size: [22, 20], pieces: ['Landmark_Titan'], face: 0, with: { Landmark_Titan: ['Landmark_TitanUpper'] }, kind: 'wall' },
    'J': { size: [18, 10], pieces: ['Landmark_Torso'], face: 0, kind: 'wall' },
    'q': { size: [10, 10], pieces: ['Landmark_Head'], face: 0, kind: 'wall' },
    'r': { size: [18, 12], pieces: ['Landmark_Ribs'], face: 0, kind: 'wall' },
    'C': { size: [20, 4], pieces: ['Landmark_Cannon'], flip: true, kind: 'cover' },
    'U': { size: [4, 4], pieces: ['Reactor_A', 'Reactor_B'], flip: true, kind: 'wall' },
    'n': { size: [12, 4], pieces: ['Scaffold'], face: 0, kind: 'wall' },
    'e': { size: [12, 4], pieces: ['Arm'], flip: true, kind: 'cover' },
    'p': { size: [3, 1], pieces: ['Plates_A', 'Plates_B'], flip: true, kind: 'cover' },
    'b': { pieces: ['BeaconPost'], rotate: 'random90', kind: 'cover' },
    // ---- "@layer 0": flat on the ground
    'w': { size: [4, 10], pieces: ['Weighbridge'], face: 0, collide: false },
    'u': { size: [2, 2], pieces: ['Oil_A', 'Oil_B'], flip: true, collide: false }
  };

  // glow companions (zones.js theme.glow): lamp lenses, lit windows, reactor cores and screens in <Piece>_Glow, the
  // warning beacons' domes in <Piece>_Blink (two phase groups, blinked by backdrop.build)
  var LIT = ['Bank_LampS', 'Bank_LampN', 'Bank_LampE', 'Bank_LampW', 'Grave_LampS', 'Grave_LampN', 'Grave_LampE', 'Grave_LampW',
    'Grave_Leak', 'GateFrame', 'TrailWall_Lamp', 'Hatch', 'FloodTower', 'Landmark_Office', 'Landmark_Baler', 'Landmark_Crane',
    'Landmark_TitanUpper', 'Landmark_Torso', 'Landmark_Ribs', 'Landmark_Cannon', 'Reactor_A', 'Reactor_B', 'Scaffold'];
  var BLINK = ['GateFrame', 'Hatch', 'FloodTower', 'Landmark_Office', 'Landmark_Baler', 'Landmark_Crane', 'Landmark_TitanUpper',
    'Landmark_Ribs', 'Reactor_A', 'Scaffold', 'BeaconPost'];
  var GLOW = {};
  LIT.forEach(function (n) { GLOW[n] = [{ piece: n + '_Glow' }]; });
  BLINK.forEach(function (n) { (GLOW[n] = GLOW[n] || []).push({ piece: n + '_Blink', groups: 2 }); });

  /* backdrop.build: the night. The ground beyond the yard, far scrap mountains all round, a dead titan standing far
     off and tower cranes on the skyline (their red lights blink), the moon and the stars (they follow the camera like
     the sky dome); the beacons of the yard blink. Everything here is level-wide (built once: nothing switches when the
     player crosses between the zones). */
  var MOON = [0.42, 0.36, -0.83];   // toward the north-east, low over the graveyard
  function backdrop(level, api) {
    var T = typeof THREE !== 'undefined' ? THREE : null;
    var x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
    level.zones.forEach(function (z) { x0 = Math.min(x0, z.ox); x1 = Math.max(x1, z.ox + z.w); z0 = Math.min(z0, z.oz); z1 = Math.max(z1, z.oz + z.h); });
    z0 -= 30; z1 += 6;   // the exit way and the hatch room run north of the last zone
    var cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, hw = (x1 - x0) / 2, hd = (z1 - z0) / 2;
    // the ground out to the fog
    api.geo.flat([[cx - hw - 260, cz - hd - 260], [cx + hw + 260, cz - hd - 260], [cx + hw + 260, cz + hd + 260], [cx - hw - 260, cz + hd + 260]], -0.02, '#1A1B22');
    // far scrap mountains: two rings round the yard (outside the walls, never inside a zone)
    for (var ring = 0; ring < 2; ring++) {
      var n = ring ? 22 : 16, off = ring ? 70 : 26;
      for (var i = 0; i < n; i++) {
        var a = (i + ring * 0.5) / n * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
        var k = Math.min((hw + off) / Math.max(1e-3, Math.abs(ca)), (hd + off) / Math.max(1e-3, Math.abs(sa)));
        var x = cx + ca * k, z = cz + sa * k, s = (ring ? 2.2 : 1.1) * (0.8 + 0.5 * api.hash(i, 31 + ring));
        api.add(i % 2 ? 'Backdrop_Heap_A' : 'Backdrop_Heap_B', x, -0.5 - 0.013 * (i + ring * n), z, Math.atan2(-(x - cx), -(z - cz)) + (api.hash(i, 7) - 0.5) * 0.6, s);
      }
    }
    var far = [['Backdrop_Titan', cx - hw - 95, z0 + 40, 0.6, 1.25], ['Backdrop_Titan', cx + hw + 120, cz + 30, -2.1, 1.4],
      ['Backdrop_Crane', cx + hw + 80, z0 - 10, 0.9, 1.0], ['Backdrop_Crane', cx - hw - 75, z1 - 60, 2.4, 1.1],
      ['Backdrop_Crane', cx - 40, z0 - 110, 0.2, 1.2]];
    far.forEach(function (f) { api.add(f[0], f[1], 0, f[2], f[3], f[4]); });
    if (!T || !IB.Assets || !IB.Assets.geo) return;
    var map = IB.Assets.mat['kit-scrapyard'].map, blinkMat = new T.MeshBasicMaterial({ map: map });
    var farBlink = [];
    far.forEach(function (f) {
      var gn = 'KIT_SCRAPYARD_' + f[0] + '_Blink';
      if (!IB.Assets.geo[gn]) return;
      var m = new T.Mesh(IB.Assets.get(gn), blinkMat);
      m.position.set(f[1], 0, f[2]); m.rotation.y = f[3]; m.scale.setScalar(f[4]);
      level.root.add(m); farBlink.push(m);
    });
    // the moon (a disc, its craters, a halo) and the stars, drawn behind everything (no fog), following the camera
    var sky = new T.Group(); sky.name = 'NightSky';
    var d = new T.Vector3(MOON[0], MOON[1], MOON[2]).normalize();
    var mk = function (r, col, op, add, seg) {
      var mm = new T.Mesh(new T.CircleGeometry(r, seg || 28), new T.MeshBasicMaterial({ color: col, fog: false, depthWrite: false, transparent: op < 1, opacity: op, blending: add ? T.AdditiveBlending : T.NormalBlending }));
      mm.renderOrder = -9; return mm;
    };
    var moon = new T.Group();
    var halo = mk(34, '#3A4A70', 0.35, true); halo.position.z = -0.3; moon.add(halo);
    var halo2 = mk(22, '#5A6E9C', 0.35, true); halo2.position.z = -0.2; moon.add(halo2);
    moon.add(mk(12, '#E6ECF4', 1));
    [[-3.5, 3.0, 2.4], [4.0, -1.5, 3.0], [-1.0, -5.0, 1.8], [5.5, 4.5, 1.3]].forEach(function (c) { var cr = mk(c[2], '#BFC8D6', 1, false, 12); cr.position.set(c[0], c[1], 0.1); moon.add(cr); });
    moon.position.copy(d.clone().multiplyScalar(270)); moon.lookAt(0, 0, 0);
    sky.add(moon);
    var N = 520, pos = new Float32Array(N * 3), col = new Float32Array(N * 3), c3 = new T.Color();
    for (i = 0; i < N; i++) {
      var u = api.hash(i, 101), v = api.hash(i, 103), el = Math.asin(0.08 + 0.92 * Math.pow(v, 0.8)), az = u * Math.PI * 2;
      var p = new T.Vector3(Math.cos(el) * Math.cos(az), Math.sin(el), Math.cos(el) * Math.sin(az));
      if (p.angleTo(d) < 0.16) p.y = -1;   // none in front of the moon
      p.multiplyScalar(280); pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z;
      var b = 0.45 + 0.55 * api.hash(i, 107);
      c3.setRGB(b * (0.85 + 0.15 * api.hash(i, 109)), b * 0.92, b);
      col[i * 3] = c3.r; col[i * 3 + 1] = c3.g; col[i * 3 + 2] = c3.b;
    }
    var sg = new T.BufferGeometry();
    sg.setAttribute('position', new T.BufferAttribute(pos, 3));
    sg.setAttribute('color', new T.BufferAttribute(col, 3));
    var stars = new T.Points(sg, new T.PointsMaterial({ size: 2.0, sizeAttenuation: false, vertexColors: true, fog: false, depthWrite: false }));
    stars.renderOrder = -9; stars.frustumCulled = false;
    sky.add(stars);
    level.root.add(sky);
    var blink = (level.glows || []).filter(function (G) { return /_Blink$/.test(G.piece); });
    api.tick(function (dt, t) {
      var cam = IB.Render && IB.Render.camera;
      if (cam) sky.position.copy(cam.position);
      for (var j = 0; j < blink.length; j++) blink[j].mesh.visible = ((t * 0.9 + blink[j].group * 0.5) % 1) < 0.55;
      var on = (t * 0.45 % 1) < 0.5;
      for (j = 0; j < farBlink.length; j++) farBlink[j].visible = on;
    });
  }

  var PIECES = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_B', 'TrailWall_Lamp', 'Hatch', 'Stand',
    'Backdrop_Heap_A', 'Backdrop_Heap_B', 'Backdrop_Titan', 'Backdrop_Crane', 'Backdrop_Titan_Blink', 'Backdrop_Crane_Blink',
    'Landmark_Crane', 'Landmark_TitanUpper']);
  var BORROWED = [];
  Object.keys(SYMBOLS).forEach(function (ch) {
    var d = SYMBOLS[ch];
    d.pieces.concat(d.stack ? [d.stack.piece] : []).forEach(function (n) {
      if (n.indexOf(KP) === 0) { if (BORROWED.indexOf(n) < 0) BORROWED.push(n); } else if (PIECES.indexOf(n) < 0) PIECES.push(n);
    });
  });
  Object.keys(GLOW).forEach(function (k) { GLOW[k].forEach(function (g) { if (PIECES.indexOf(g.piece) < 0) PIECES.push(g.piece); }); });

  IB.registerTheme({
    id: 'scrapyard', name: 'Rustmoor Salvage', family: 'kit-scrapyard', prefix: 'KIT_SCRAPYARD_', families: ['kit-parking'],
    palette: ['#7E4B31', '#FFB34D', '#52D8F0', '#FF3B2F'],
    env: {
      // night: a blue-black sky (stars and the moon from backdrop.build), dark blue fog; the light from the south-east
      // so the faces the player sees while pushing north stay readable
      sky: ['#05070F', '#1B2540'], fog: { color: '#18213A', near: 34, far: 128 },
      sun: [0.38, 0.8, 0.46], clouds: false, ceiling: null
    },
    floor: { color: '#30313A', trail: '#363741', outside: '#1A1B22' },
    wall: { height: 9.0, roof: '#2B2B32', facing: 'open', choose: chooseWall },
    symbols: SYMBOLS,
    glow: GLOW,
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', variants: ['TrailWall_B', 'TrailWall_Lamp'], height: 6.0 },
    hatch: 'Hatch', stand: 'Stand',
    backdrop: { build: backdrop },
    budget: { prop: 3200, landmark: 6000, total: 70000 },
    allPieces: function () { return PIECES.slice(); },
    // the kit-parking pieces this theme places (tests check they exist in fps-kit-parking.glb)
    parkingPieces: function () { return BORROWED.slice(); },
    levels: {
      scrapyard: {
        name: 'Rustmoor Salvage',
        intro: 'A scrapyard at night, among the dead war machines. Clear the Stacks, then the Titan Graveyard, and ride the hoist out.',
        zones: [
          // the Stacks: the haul road, the bale canyons, the baler under the crane, the limbs and guns
          { map: 'scrapyard_1', waves: [
            [['crawler', 22], ['gunner', 12], ['drone', 4]],
            [['crawler', 9], ['bomber', 2], ['gunner', 9], ['drone', 5], ['soldier', 6], ['blader', 3]],
            [['crawler', 9], ['drone', 6], ['gunner', 9], ['soldier', 6], ['blader', 3]],
            [['crawler', 9], ['bomber', 2], ['gunner', 9], ['drone', 5], ['blader', 3], ['soldier', 5]],
            [['crawler', 9], ['bomber', 1], ['gunner', 10], ['drone', 5], ['soldier', 5], ['blader', 3]]] },
          // the Titan Graveyard: the kneeling titan, the torso, the ribcage, the head, the cannon
          { map: 'scrapyard_2', waves: [
            [['crawler', 20], ['gunner', 11], ['drone', 5]],
            [['crawler', 9], ['bomber', 2], ['gunner', 9], ['drone', 5], ['blader', 3], ['soldier', 6]],
            [['crawler', 9], ['drone', 6], ['gunner', 9], ['soldier', 6], ['blader', 3]],
            [['crawler', 9], ['bomber', 2], ['gunner', 9], ['drone', 5], ['soldier', 5], ['blader', 3]],
            [['crawler', 9], ['bomber', 1], ['gunner', 10], ['drone', 5], ['soldier', 5], ['blader', 3]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
