/* INKBOLT - save slots and settings (brief section 5.14). Pure, no DOM.
   backend: localStorage-like {getItem(k), setItem(k, v), removeItem(k), keys()}. */
(function (IB) {
  'use strict';

  var PREFIX = 'inkbolt.';
  var SLOTS = 3;
  var SETTINGS_KEY = PREFIX + 'settings';
  var DEFAULT_SETTINGS = {
    sfx: true, mouseSens: 1.0, touchSens: 1.0, fov: 100, invertY: false, graphics: 'auto',
    shake: true, headBob: true, reduceFlash: false
  };

  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function isObj(o) { return o !== null && typeof o === 'object' && !Array.isArray(o); }

  function slotKey(id) { return PREFIX + 'slot' + id; }
  // loot inventory (core/loot.js repairs items deeply; this only guarantees the shape). armor: the worn vest
  // (saves from before vests have none: it is added empty)
  function defaultGear() { return { inv: [], shield: null, armor: null, attach: {}, next: 1, found: 0 }; }

  function defaultSlot(id, seed, savedAt) {
    return {
      v: 1, id: id, level: 1, highest: 0, xp: 0, gems: 0, upgrades: {},
      // arsenal = every gun owned, loadout = the guns carried in key order, skills = {skillId: rank}
      // (skill points are not stored: they are derived from `highest`, see core/skills.js)
      arsenal: [], loadout: [], skills: {},   // empty arsenal: the level plan's start guns are handed out
      stats: { kills: 0, deaths: 0, time: 0, coreHits: 0 },
      best: {},
      gear: defaultGear(),
      seed: seed >>> 0, saved: savedAt
    };
  }

  // Fill missing fields of a v:1 slot; unknown future versions are kept untouched.
  function migrate(obj) {
    if (!isObj(obj)) return null;
    var v = obj.v === undefined ? 1 : obj.v;
    if (typeof v !== 'number' || v > 1) return obj;
    var d = defaultSlot(obj.id || 1, obj.seed || 0, obj.saved || 0);
    var out = {};
    var k;
    for (k in d) out[k] = d[k];
    for (k in obj) out[k] = obj[k];
    out.v = 1;
    ['upgrades', 'stats', 'best'].forEach(function (f) {
      if (!isObj(obj[f])) out[f] = d[f];
      else if (f === 'stats') {
        var s = {};
        for (var sk in d.stats) s[sk] = d.stats[sk];
        for (sk in obj.stats) s[sk] = obj.stats[sk];
        out.stats = s;
      }
    });
    if (!isObj(obj.gear)) out.gear = defaultGear();
    else {
      var g = defaultGear();
      for (k in obj.gear) g[k] = obj.gear[k];
      if (!Array.isArray(g.inv)) g.inv = [];
      if (!isObj(g.attach)) g.attach = {};
      if (typeof g.next !== 'number') g.next = 1;
      out.gear = g;
    }
    if (typeof out.level !== 'number' || out.level < 1) out.level = 1;
    if (typeof out.highest !== 'number' || out.highest < 0) out.highest = 0;
    if (typeof out.gems !== 'number' || out.gems < 0) out.gems = 0;
    if (typeof out.seed !== 'number') out.seed = 0;
    if (typeof out.saved !== 'number') out.saved = 0;
    // loadout: the brief's class map {pistol: 'pip', smg: 'buzz'} (older saves) becomes the ordered list
    // (the game trims it to the 2- or 3-gun limit when a level starts)
    var lo = Array.isArray(obj.loadout) ? obj.loadout : (Array.isArray(obj.owned) ? obj.owned : []).concat(
      isObj(obj.loadout) ? Object.keys(obj.loadout).map(function (c) { return obj.loadout[c]; }) : []);
    lo = lo.filter(function (id) { return typeof id === 'string'; });
    var ars = (Array.isArray(obj.arsenal) ? obj.arsenal : []).concat(Array.isArray(obj.owned) ? obj.owned : [], lo);
    out.arsenal = ars.filter(function (id, i) { return typeof id === 'string' && ars.indexOf(id) === i; });
    out.loadout = lo.filter(function (id, i) { return lo.indexOf(id) === i && out.arsenal.indexOf(id) >= 0; });
    if (!out.loadout.length && out.arsenal.length) out.loadout = [out.arsenal[0]];
    // skills: spent must never exceed what the progress has earned; a broken tree is reset (points refunded)
    // (a save from before the six-row tree holds old skill ids: the whole tree is refunded and the game says so once)
    if (!isObj(out.skills)) out.skills = {};
    // player XP: a save from before XP levelling starts at the LV its progress gave (1 + highest level cleared)
    if (IB.Skills && !(typeof obj.xp === 'number' && obj.xp >= 0)) out.xp = IB.Skills.xpForLevel(1 + (out.highest || 0));
    if (IB.Skills) { var san = IB.Skills.sanitize(out.skills, IB.Skills.gained(out)); out.skills = san.skills; if (san.reset) out.skillsRefunded = true; }
    return out;
  }

  function memoryBackend() {
    var m = new Map();
    return {
      getItem: function (k) { return m.has(k) ? m.get(k) : null; },
      setItem: function (k, v) { m.set(k, String(v)); },
      removeItem: function (k) { m.delete(k); },
      keys: function () { return Array.from(m.keys()); },
      _map: m
    };
  }

  function ago(ms) {
    var s = Math.max(0, ms) / 1000;
    if (s < 60) return 'just now';
    var m = Math.floor(s / 60);
    if (m < 60) return m + ' min ago';
    var h = Math.floor(m / 60);
    if (h < 24) return h + ' h ago';
    var d = Math.floor(h / 24);
    return d === 1 ? '1 day ago' : d + ' days ago';
  }

  function create(backend, now) {
    var clock = now || Date.now;

    function get(k) { try { return backend.getItem(k); } catch (e) { return null; } }
    function set(k, v) { try { backend.setItem(k, v); return true; } catch (e) { return false; } }
    function del(k) { try { backend.removeItem(k); } catch (e) { /* ignore */ } }
    function parse(raw) {
      if (raw === null || raw === undefined) return null;
      try { var o = JSON.parse(raw); return isObj(o) ? o : null; } catch (e) { return null; }
    }

    // Main key, falling back to .bak when the main value is corrupt. Missing main -> null.
    function read(key) {
      var raw = get(key);
      if (raw === null || raw === undefined) return null;
      var o = parse(raw);
      if (o) return o;
      return parse(get(key + '.bak'));
    }

    // Keeps the previous (valid) value as .bak, then writes the new one.
    function write(key, obj) {
      var prev = get(key);
      if (prev !== null && prev !== undefined && parse(prev)) set(key + '.bak', prev);
      return set(key, JSON.stringify(obj));
    }

    function validId(id) { return id === 1 || id === 2 || id === 3; }

    function load(id) {
      if (!validId(id)) return null;
      var s = migrate(read(slotKey(id)));
      if (s) s.id = id;
      return s;
    }

    function save(slot) {
      if (!slot || !validId(slot.id)) throw new Error('save: slot id must be 1, 2 or 3');
      slot.saved = clock();
      write(slotKey(slot.id), slot);
      return slot;
    }

    function newSlot(id, seed) {
      var sd = seed === undefined ? Math.floor(Math.random() * 0x7fffffff) : seed;
      return defaultSlot(id, sd, clock());
    }

    function listSlots() {
      var out = [];
      for (var i = 1; i <= SLOTS; i++) out.push(load(i));
      return out;
    }

    function freeSlot() {
      for (var i = 1; i <= SLOTS; i++) if (!load(i)) return i;
      return null;
    }

    function remove(id) {
      del(slotKey(id));
      del(slotKey(id) + '.bak');
    }

    function newest() {
      var best = null;
      listSlots().forEach(function (s) { if (s && (!best || s.saved > best.saved)) best = s; });
      return best;
    }

    function loadSettings() {
      var s = clone(DEFAULT_SETTINGS);
      var o = read(SETTINGS_KEY);
      if (o) for (var k in DEFAULT_SETTINGS) if (o[k] !== undefined && typeof o[k] === typeof DEFAULT_SETTINGS[k]) s[k] = o[k];
      // settings v2: the old 85 default becomes the new 100 default (a field of view the player chose is kept)
      if (o && !o.sv && o.fov === 85) s.fov = DEFAULT_SETTINGS.fov;
      s.fov = Math.max(60, Math.min(130, s.fov));
      return s;
    }

    function saveSettings(s) {
      var out = clone(DEFAULT_SETTINGS);
      for (var k in DEFAULT_SETTINGS) if (s && s[k] !== undefined) out[k] = s[k];
      out.sv = 2;
      write(SETTINGS_KEY, out);
      return out;
    }

    function resetAll() {
      var ks = [];
      try { ks = backend.keys() || []; } catch (e) { ks = []; }
      ks.filter(function (k) { return String(k).indexOf(PREFIX) === 0; }).forEach(del);
      // Also clear the known keys in case keys() is incomplete.
      for (var i = 1; i <= SLOTS; i++) remove(i);
      del(SETTINGS_KEY); del(SETTINGS_KEY + '.bak');
    }

    return {
      listSlots: listSlots, load: load, save: save, newSlot: newSlot, freeSlot: freeSlot,
      remove: remove, newest: newest, loadSettings: loadSettings, saveSettings: saveSettings,
      resetAll: resetAll, migrate: migrate, slotKey: slotKey
    };
  }

  IB.Saves = {
    create: create, memoryBackend: memoryBackend, ago: ago, migrate: migrate,
    defaultGear: defaultGear, DEFAULT_SETTINGS: DEFAULT_SETTINGS, PREFIX: PREFIX, SLOTS: SLOTS, slotKey: slotKey
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
