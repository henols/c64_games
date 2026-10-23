# The tests

The scenario and run files in this folder have only the keys of the c64-testing formats. This page holds the notes of each file: the conditions of the test and the parts that the test does not compare.

## Scenarios: the original against the rebuild

Each scenario runs the original file and a rebuild side by side and compares them.

**The synchronization.** Two sides that run different code are in different raster phases after the same number of frames. The default build and the TBC intro are examples. Thus some scenarios stop each side at a fixed point before a checkpoint:

- `all_rooms_no_protection` stops at raster line 0 before each checkpoint. Without the stop, one side wrote the colours of the next band split and the other side did not (room 15).
- `no_protection` stops at raster line 0 before the 100 frames on the title, and again before the checkpoint. Without the stops, `title_countdown` and `irq_vector` were different by one interrupt.
- `title_options` writes each key at `$08C2`, the `lda key_ready` after `jsr scan_keyboard` in `title_menu_scan_keys`. A key that a step writes during `scan_keyboard` is lost, because the scanner writes `$FF` to `key_code` when no matrix key is down.

c64-re-tools 2.4 stops the sides at other cycles than 2.3, so these tests failed without the stops. The game bytes did not change.

**The leftover blocks.** Nine scenarios do not compare the leftover blocks that the game image leaves out. They also do not compare the 13 leftover ranges that `build/clean_loader.prg` does not load. Each byte of these ranges is an `exclude`. The nine scenarios are `title`, `title_options`, `demo`, `game_start`, `game_keys`, `room_change`, `lose_fall_game_over`, `wizard_and_ending` and `no_protection`. `leftovers_unused` covers these blocks.

- **`all_rooms`.** The test enters each room from the main loop at its start point (`spawn_a_x`/`spawn_a_y`). The checkpoint `_drawn` is 20 frames after the draw. The checkpoint `_later` is 200 frames after `_drawn`. At that time, the frame handler of the room and the enemies have run. The test does not compare the colour RAM. Its upper 4 bits are open bus. The low 4 bits were equal at each checkpoint (**Observed**: the run of 2026-10-21 on the stage loader). The screen compare includes the visible colours. It accepts 0.02 % of different pixels for the colour splits of room 15, as `all_rooms_no_protection` does.
- **`all_rooms_no_protection`.** The original is the TBC release (`original/bruce_lee_tbc.prg`). Its game bytes are the default build without the protection patches, because the default build has the TBC state of `CRACK_DIABOLO`, `FIX_RAM_TEST_BYTE` and `RUN_STATE`. The TBC intro shows the Datasoft title picture. It empties the key buffer at `$0870` and waits at `$0872` for a key. The steps are the steps of `all_rooms`, with `build/clean_loader.prg` (the default build, `PROTECTION` = 0).
  - The patched protection checks change the timing of the main loop. Thus the colour splits of `irq_game_colour_split` can occur a few pixels later on one raster line. This handler polls the raster and then writes `BGCOL0`-`BGCOL2`, one after the other.
  - The original also changes that line from frame to frame. In room 15 at raster line 169, 3 of 12 frames are different. Thus the screen compare accepts 0.02 % of different pixels (20 of 104448).
  - The test does not compare the colour RAM. Its upper 4 bits are open bus and change with the timing. The screen compare includes the visible colours.
- **`no_protection`.** The original is the TBC release, as in `all_rooms_no_protection`. The test does not compare the 47 bytes that the `PROTECTION` patches change, and it does not compare `$0000-$0002`. The rebuild side is `build/clean_loader.prg`, the default build. Its symbols are in `build/symbols/clean_loader.json`, which `generate --loader` writes with the labels of `src/loader.asm`, `src/main.asm` and `src/start_screen_stage.asm`.
- **`crack_leftover_a000` and `original_loader_stage_033c`.** The test does not compare the stack area `$01C0-$01FF`. Below the stack pointer, this area holds old return addresses from the crack intro. Their values change with the time when the host types SPACE.
- **`leftovers_unused`.** Both sides run the original file. At the game entry, the rebuild side fills the leftover blocks with `$A5`. The test does not compare the filled blocks, the stack area `$01C0-$01FF` and the I/O area.

## Recordings

The record files are in `record/`, and the recordings are in `recordings/`. `recordings/first-rooms` replays on `build/clean_loader.prg` with the symbols of `build/symbols/clean_loader.json`. The replay runs the rebuild to `loader_start_screen_wait` and sets the PC to `loader_start_screen_continue`. [PLAYTEST.md](PLAYTEST.md) is the checklist for a human playtest.
