/* INKBOLT platform layer (Plat): CrazyGames SDK v3 / Poki SDK v2 / plain. Round 1: plain build only
   (no SDK, ads = false); hooks are already called at the right points so the SDK wiring drops in. */
(function (IB) {
  'use strict';
  var P = window.Plat = IB.Plat = { name: 'plain', ads: false, sdk: null, lastMidgame: -1e9, log: [] };
  var platform = window.__PLATFORM__ || 'plain';
  function note(ev) { P.log.push(ev); if (P.log.length > 50) P.log.shift(); }

  P.init = function () {
    note('init');
    try {
      if (platform === 'crazygames' && window.CrazyGames && window.CrazyGames.SDK) { P.name = 'crazygames'; P.sdk = window.CrazyGames.SDK; P.ads = true; return P.sdk.init ? P.sdk.init() : Promise.resolve(); }
      if (platform === 'poki' && window.PokiSDK) { P.name = 'poki'; P.sdk = window.PokiSDK; P.ads = true; return P.sdk.init(); }
    } catch (e) { P.ads = false; }
    return Promise.resolve();
  };
  P.loaded = function () { note('loaded'); try { if (P.name === 'poki') P.sdk.gameLoadingFinished(); if (P.name === 'crazygames' && P.sdk.game) P.sdk.game.loadingStop && P.sdk.game.loadingStop(); } catch (e) { /* ignore */ } };
  P.start = function () { if (P.playing) return; P.playing = true; note('start'); try { if (P.name === 'poki') P.sdk.gameplayStart(); if (P.name === 'crazygames') P.sdk.game.gameplayStart(); } catch (e) { /* ignore */ } };
  P.stop = function () { if (!P.playing) return; P.playing = false; note('stop'); try { if (P.name === 'poki') P.sdk.gameplayStop(); if (P.name === 'crazygames') P.sdk.game.gameplayStop(); } catch (e) { /* ignore */ } };
  P.happy = function () { note('happy'); try { if (P.name === 'crazygames') P.sdk.game.happytime(); } catch (e) { /* ignore */ } };
  P.midgame = function () { note('midgame'); return Promise.resolve(false); };
  P.rewarded = function () { note('rewarded'); return Promise.resolve(false); };
})(window.IB = window.IB || {});
