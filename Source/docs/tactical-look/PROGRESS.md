# Tactical look: progress log

Plan: `PLAN.md` in this folder. Base commit `5cfa145` (the plan was written against it; the plan itself is `631f21a`).
Branch `claude/charming-heisenberg-f3j35w`. One line per finished step, the measured gate numbers, and decisions.

## Standing decisions

- **Future maps.** The game will grow past 45 maps. Nothing in the look may need hand work per map to be correct:
  a new theme gets a family preset from `looks.js` (an explicit entry, or a guess from its env: sky/ceiling, fog,
  sun colour), its kit's palette cells get surface classes from the name rules in `surface_classes.py`, its
  lamps become lights automatically, and `look-shots.js` shoots any plan with an automatic 8-spot recipe. A
  per-theme entry in `looks.js` is tuning on top, never a requirement. Unit tests check that every theme in
  the campaign resolves.
- Map content detail (more "working detail" per map) is an ongoing separate effort driven by tester reports;
  this job builds the systems (dressing, decals, kit detail) that make that cheap, and does Stage 11 for the
  pilots.

## Stage 0. Safety net and tools

- 0.1 This file.
- 0.2 `tests/e2e/look-shots.js`: plans from argv, `LOOK=classic|on`, `TIER` (default high, the auto tier guard is
  switched off for shots), `ZONES`, `VM=0`, `HTML`, `EXTRA`, `ONLY`. Spots from `look-spots.json`, else an automatic
  8-spot recipe (z0 long / wall / floor / up / aim, z1 long / back / wall) that works on any map, so future maps
  need no hand-picked spots. Aim shots hold the right mouse button. Waits for the light volume to finish the zone.
- 0.3 `tests/e2e/look-sheet.py`, 0.4 `tests/e2e/look-metrics.py` (`--check`, `--md`), scene types per plan in
  `look-spots.json` (all 46 themes, from section 8).
- 0.5 `tests/e2e/hud-lock.spec.js`: file lock (15 protected files vs `5cfa145`), HUD pixel lock at 1280x720,
  1920x1080, 844x390 touch, enemy-bar lock (only the bars drawn, through the real render path). Baselines in
  `tests/e2e/review/hud-lock/` from the untouched build. Two runs of the check on the untouched build: 0 pixels
  differ on all three HUD views and on the 3,180 bar pixels (fully deterministic).
- Extra tool: `tests/e2e/look-diag.js` prints post mode, shadow state, light volume (size, lights per zone, bake ms),
  look family, page errors; `EVAL=` evaluates an expression in the page.
- 0.6 Classic baseline: the untouched build is kept as `Source/dist/look/base.html` (ignored) so baselines can be
  re-shot at any time. Shots in `Source/dist/look/s0-base/`.
