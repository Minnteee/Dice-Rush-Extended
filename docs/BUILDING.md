# Building Dice Rush Extended

This page explains how the mod works and how to build it yourself, for example as a starting point for
your own DICE RUSH mod. The files of the original game are not part of this repository; you need your
own copy of DICE RUSH v1.0.0 (Full).

## How the mod is loaded

- DICE RUSH is a Godot 4.7.1 game. Godot reads `override.cfg` next to the game's exe at start-up.
  The mod's `override.cfg` registers `DiceRushExtended/boot.gd` as an extra autoload.
- `boot.gd` mounts `DiceRushExtended/DiceRushExtended.pck` with `ProjectSettings.load_resource_pack()`
  before the game scenes are loaded. The pack contains
  - the mod's own scripts, data, translations and art under `res://bdr/`, and
  - modified copies of a few original game scripts plus `.gd.remap` files, so the game loads the modified
    scripts instead of the original ones.
- The patched `main.gd` (the game scene) creates the mod's game controller
  (`src/bdr/game/bdr_game.gd`) in `_ready()`; the controller sets up all mod systems (shop, staff,
  talents, lucky cubes, tarot, events, achievements, coop, effects).
- Do not use a new `class_name` in mod scripts: global classes are registered from the game's own
  class list, so the mod uses `preload()` constants instead.
- **Dice Shaker** lives in `src/shaker/` and is packed under `res://shaker/`. The pack also replaces the
  start menu scene (`res://scenes/start_menu.tscn.remap` -> `res://shaker/menu/start_menu.tscn`): its
  script extends the (patched) start menu script, adds the DICE SHAKER button and switches the save card
  screen to the Dice Shaker save cards. The game mode itself is its own scene (`res://shaker/scenes/shaker.tscn`).

## Requirements

- Windows, Python 3.10 or newer.
- Your own copy of DICE RUSH v1.0.0 (Full).
- The original game scripts, recovered from the game with
  [GDRE Tools](https://github.com/GDRETools/gdsdecomp): put the scripts into `work/recovered/scripts/`
  and the assets into `work/recovered/assets/`. They are needed to apply the patches and are never
  published.
- `tools/packer/`: copy `Dice Rush.exe`, `libgodotsteam.windows.template_release.x86_64.dll` and
  `steam_api64.dll` from your game folder into this folder. The build packs the `.pck` file with the
  game's own engine, so the pack always matches the game's Godot version.
- For the art and sound generators: `pip install pillow numpy` (a virtual environment in `tools/venv/` works well).

## Build

```bat
python tools\build.py --release
```

1. `tools/apply_patches.py` applies `src/patches/<script>/` to the original scripts and writes the
   result to `src/game/scripts/` (generated, not in the repository).
2. `tools/shaker/make_shaker_data.py` writes the Dice Shaker game data (`src/shaker/data/shaker_data.json`)
   and its English and German texts from `tools/shaker/shaker_design.py` and `shaker_texts.py`.
3. `tools/i18n/build_i18n.py` builds the English and German texts (`src/bdr/i18n/en.json`, `de.json`)
   from `tools/i18n/strings*.py`. The other 29 languages are the JSON files in `src/bdr/i18n/` and
   `src/shaker/i18n/`; `tools/i18n/check_translations.py` and `tools/shaker/check_i18n.py` check that every
   language has every key and the same placeholders.
4. Everything is packed into `dist/DiceRushExtended/DiceRushExtended.pck`; `--release` also writes
   `dist/Dice-Rush-Extended-<version>.zip`.

Install options:

- `--install-game` copies the mod into your game folder. Set the folder with the environment variable
  `DICE_RUSH_DIR` or a file `tools/local_paths.json` like `{"game_dir": "C:/Games/DICE RUSH"}`.
- `--install-test` copies the mod and the test harness into `testgame/` (a copy of the game folder).

## Patch format (`src/patches/<script>/`)

Every `*.gd` file in `src/patches/main/` (and the other script folders) contains top-level blocks:

- a `func`, `var` or `const` with the same name as in the original script **replaces** the original one,
- other blocks are **added** (functions at the end, variables and constants after the original ones),
- a line `#@delete <name>` removes an original block,
- an optional `edits.py` defines `EDITS = [(old, new), ...]`: exact text replacements that must match
  exactly once.

## Other tools

| Tool | Purpose |
| --- | --- |
| `tools/catalog/make_dice_catalog.py` | the 100 dice (tiers, prices, payouts, effects, texts) -> `src/bdr/data/dice_catalog.json` |
| `tools/art/build_all.py` | re-generates all pixel art into `build/generated/bdr/art/` and checks it |
| `tools/shaker_art/gen_scene.py`, `gen_gauntlets.py`, `gen_tarot.py` | Dice Shaker pixel art (table, crystal ball, hands, gumball machine, 20 table designs, 30 gauntlets, 60 cards) -> `build/generated/shaker/art/` (needs Pillow and numpy) |
| `tools/shaker/gen_sounds.py` | the synthesised Dice Shaker sounds -> `build/generated/shaker/audio/` |
| `tools/shaker/econ_sim.py` | Dice Shaker balance simulation: when a player reaches 6 / 12 dice, the first legendary die, all tarot cards ... (`shaker_rules.py` is a 1:1 copy of the game's rules) |
| `src/testing/bdr_test_harness.gd`, `tools/bdr.py` | test harness: a TCP/JSON remote control (port 47811) for a test copy of the game |
| `tools/perf_move.py` | frame time measurement with many dice (needs the test harness) |
| `tools/make_screenshot.py` | makes the README screenshot with two coop instances (needs the test harness) |
| `tools/launch_test.ps1` | starts the test copy on a separate Windows virtual desktop (uses [VirtualDesktop](https://github.com/MScholtes/VirtualDesktop) in `tools/vdesk/`) |

## Credits

If you publish something that uses this mod's code or art, credit it as
"Dice Rush Extended by Minnteee" with a link to https://github.com/Minnteee (see `LICENSE`).
