# The tests

The scenario and run files in this folder have only the keys of the c64-testing formats. This page holds the notes of each file: the conditions of the test and the parts that the test does not compare.

## Scenarios: the original against the rebuild

Each scenario runs the original file and a rebuild side by side and compares them.

**The synchronization.** Two sides that run different code are in different raster phases after the same number of frames. The default build and the TBC intro are examples. Thus some scenarios stop each side at a fixed point before a checkpoint:

- `all_rooms_no_protection` stops at raster line 0 before each checkpoint. Without the stop, one side wrote the colours of the next band split and the other side did not (room 15).
- `no_protection` and `boot_game_start` stop at raster line 0 before the 100 frames on the title, and again before the checkpoint. Without the stops, `title_countdown` and `irq_vector` were different by one interrupt.
- `title_options` writes each key at `$08C2`, the `lda key_ready` after `jsr scan_keyboard` in `title_menu_scan_keys`. A key that a step writes during `scan_keyboard` is lost, because the scanner writes `$FF` to `key_code` when no matrix key is down.

c64-re-tools 2.4 stops the sides at other cycles than 2.3, so these tests failed without the stops. The game bytes did not change.

**The leftover blocks.** These scenarios do not compare the leftover blocks that the game image leaves out: `title`, `title_options`, `demo`, `game_start`, `game_keys`, `room_change`, `lose_fall_game_over`, `wizard_and_ending`, `no_protection` and `boot_game_start`. `leftovers_unused` covers these blocks.

- **`all_rooms`.** The test enters each room from the main loop at its start point (`spawn_a_x`/`spawn_a_y`). The checkpoint `_drawn` is 20 frames after the draw. The checkpoint `_later` is 200 frames after `_drawn`. At that time, the frame handler of the room and the enemies have run.
- **`all_rooms_no_protection`.** The original is the TBC release (`original/bruce_lee_tbc.prg`). Its game bytes are the default build without the protection patches, because the default build has the TBC state of `CRACK_DIABOLO`, `FIX_RAM_TEST_BYTE` and `RUN_STATE`. The TBC intro shows the Datasoft title picture. It empties the key buffer at `$0870` and waits at `$0872` for a key. The steps are the steps of `all_rooms`, with `build/bruce_lee_loader.prg` (the default build, `PROTECTION` = 0).
  - The patched protection checks change the timing of the main loop. Thus the colour splits of `irq_game_colour_split` can occur a few pixels later on one raster line. This handler polls the raster and then writes `BGCOL0`-`BGCOL2`, one after the other.
  - The original also changes that line from frame to frame. In room 15 at raster line 169, 3 of 12 frames are different. Thus the screen compare accepts 0.02 % of different pixels (20 of 104448).
  - The test does not compare the colour RAM. Its upper 4 bits are open bus and change with the timing. The screen compare includes the visible colours, and `all_rooms` compares the colour RAM byte for byte.
- **`no_protection`.** The original is the TBC release, as in `all_rooms_no_protection`. The test does not compare the 47 bytes that the `PROTECTION` patches change, and it does not compare `$0000-$0002`. Build `build/bruce_lee_loader.prg` from `src/loader.asm` (the default build) first.
- **`boot_game_start`.** The original is the TBC release. Its intro shows the Datasoft title picture and waits at `$0872` for a key. The rebuild is `build/bruce_lee_boot_TBC.prg`: `src/boot.asm` built with `--release TBC`, so its game bytes are the TBC bytes. It shows the clean picture, and a key starts the loader.
  - Both sides get the same key. The original gets it at its wait `$0872`. The rebuild gets it 5 frames after `boot_wait` (`$08BF`), because `boot_wait` empties the key queue first.
  - Build `build/bruce_lee_boot_TBC.prg` first. The default build is different from TBC only in the 47 bytes of the `PROTECTION` patches.
- **`crack_leftover_a000` and `original_loader_stage_033c`.** The test does not compare the stack area `$01C0-$01FF`. Below the stack pointer, this area holds old return addresses from the crack intro. Their values change with the time when the host types SPACE.
- **`leftovers_unused`.** Both sides run the original file. At the game entry, the rebuild side fills the leftover blocks with `$A5`. The test does not compare the filled blocks, the stack area `$01C0-$01FF` and the I/O area.

## Runs with expected values

The three boot tests run `build/bruce_lee_boot.prg`. Build it from `src/boot.asm` (the default build) first.

- **`boot_title_picture`.** The picture is the clean Datasoft title picture of `src/title_picture.kla`. A key in the KERNAL queue stops the wait before the 10 seconds.
- **`boot_fire`.** The fire button of port 2 starts the game.
- **`boot_timeout`.** The boot waits 500 frames (PAL) from the start of the wait. 450 frames after the autostart, the picture still shows.

## Recordings

The record files are in `record/`, and the recordings are in `recordings/`. `recordings/first-rooms` replays on both loaders. [PLAYTEST.md](PLAYTEST.md) is the checklist for a human playtest.
