# The tests

The record files, scenarios and run files in this folder have only the keys of the c64-testing formats of c64-re-tools 2.7. A scenario names its two sides `reference` and `rebuild`. The reference is a release file in `../releases/`, so a PASS tells about that crack file only. This page holds the notes of each file: the conditions of the test and the parts that the test does not compare.

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Claude wrote the input as steps. No person played. Each record file starts `releases/bruce_lee.prg`, the game file of the SAEGER release. A `press` of SPACE ends the crack intro. The press is input, not an event, so the first event comes after the game entry `$0400`. The coverage map of each recording starts at `$0400`.

Bruce Lee reads joystick port 1 for player 1 and port 2 for player 2. It reads the keys through its own matrix scanner [`scan_keyboard` `$139E`](../src/input/keyboard_scan.asm#L24). The `press` steps push the keys of the matrix. Thus the scanner runs in the recordings: `title_options` runs all four handedness routines, and `game_keys` runs the S and V handlers.

| Recording | What it does | Checkpoints |
|---|---|---|
| `title-play` | The title, then fire on port 1 and the first seconds of play in room 0. | 84 |
| `title_options` | F3, F5, L, R, shift-L, shift-R, F3, F5 and L on the title. | 7 |
| `demo` | The attract demo to its end at the first lost fall, the title, the next demo, and fire ends it. | 670 |
| `game_keys` | SPACE pauses and resumes. SPACE pauses again, and fire ends the pause. V two times, S two times, and F1 goes back to the title. | 385 |
| `first-rooms` | A game start, room 1 and back to room 0, and fights with the Ninja. | 1074 |
| `game_over` | No input. The enemies take all falls, the PLAYER screens follow, then the game over and the title. | 2239 |
| `all_rooms` | Each of the 20 rooms, with 400 frames of random moves in each room. | 2943 |
| `two_players` | Two players (F3). Random moves of player 1 on port 1 and of player 2 on port 2, turn by turn. | 2372 |
| `yamo_player` | The Yamo of player 2 (F5). Random moves on both ports. | 2071 |

Some record files write bytes or set the PC only for the test. The project knowledge, the source and the builds do not have these changes.

| Recording | Event | Why |
|---|---|---|
| `first-rooms` | `next_room` = 1, `current_actor` = 0, then PC = `change_room` with A = 16 and Y = 146 | Bruce goes into room 1 at once. |
| `all_rooms` | PC = `place_bruce_at_room_start` with X = the room | This entry of the game puts Bruce at the start of room X. No code of the game calls it. |
| `all_rooms` | `falls_left` = 4 before each room | The game does not end during the tour. |

**Event points.** A `runUntil` step to an address is an event at the n-th arrival at that address. Thus the record files wait only for routines that run one time for each part, for example `start_attract_demo`, `show_title_screen` or `main_loop`. They do not wait for `title_menu_loop` after the first title. That loop polls the keys, and the default build runs it a different number of times in one title.

**Keys on a shared site.** A replay gives the n-th read of each read site the value of the n-th read in the recording. `scan_keyboard` is one read site for the title and for the demo. The default build starts from its loader at another raster phase. Thus its title loop reads the keys a different number of times. A key that the recording presses after a long title thus arrives at another time on the rebuild. For this reason `demo` ends the second demo with fire, not with F1. Fire on port 1 has a read site of its own in `check_demo_abort`. The run `demo_f1_abort` covers F1 in the demo.

## Replays

A replay on the default build uses `build/clean_loader.prg` with `build/symbols/clean_loader.json`. The replay runs the rebuild to `loader_start_screen_wait` and sets the PC to `loader_start_screen_continue`. Each record file holds its comparison:

- The checkpoint is [`main_loop` `$1BC2`](../src/game/game_main_loop.asm#L23), and [`title_menu_option_changed` `$0916`](../src/game/title_menu.asm#L68) for `title_options`.
- The state is `falls_left` (3 bytes: falls, room, lanterns left), `score`, `actor_x` (with `actor_y`), `actor_state` and `actor_energy`. Some recordings add items, for example `game_screen` (1000 bytes in `all_rooms`), `pause_state`, `demo_input_ptr` or `current_player`.
- The pins are `random_ptr` and the stack page `$0100-$01FF`.

```
node <c64-testing>/scripts/testing.ts replay tests/recordings/all_rooms \
  --rebuild build/clean_loader.prg --symbols build/symbols/clean_loader.json
```

**Why the stack page is a pin.** [`random_byte` `$1159`](../src/irq/interrupt_entry_1131.asm#L45) reads `(random_ptr),Y` with a high byte of 0. Thus it reads zero page and the stack page. The stack page holds the return addresses of old interrupts, and the RAM pattern of the start. These bytes are different on the two sides. `main_loop` runs at the top level of the program, so no code uses the stack page at the checkpoint. **Observed**: without the pin, `first-rooms` put the Ninja at another place at checkpoint 789. With the pin, all 1074 checkpoints are equal.

**Why the patches keep the cycles.** The replays pass only when the default build has the timing of SAEGER. Some `PROTECTION` patches run often. Check 5 runs in each frame, check 8 in each pass of room 10, and checks 10 and 11 on each footstep. These patches take the same number of cycles as the passing path of SAEGER. **Observed**: with a check 5 that was 1 cycle shorter, `all_rooms` failed at the entry of room 5 (checkpoint 817). The default build started `draw_room` 1 cycle earlier there, on the other side of raster line 256. Then the raster interrupt stopped for a different time during the draw (see [docs/interrupts.md](../docs/interrupts.md)), and the rebuild lost one pass of frames.

All nine recordings replay on `releases/bruce_lee.prg`. They also replay on the default build with the same state at each checkpoint, 11845 checkpoints in all (**Observed**, c64-re-tools 2.7.0-rc.1).

## Scenarios

A scenario runs the reference and a rebuild side by side and compares them. These scenarios test what a replay cannot test.

**The leftover blocks.** The game image holds blocks that the game does not use (see [docs/development.md](../docs/development.md)). Three scenarios run `releases/bruce_lee.prg` on both sides, and the rebuild side gets junk in the blocks at the game entry. The title, the demo and the game then give the same memory and the same screens.

- **`leftovers_unused`.** The rebuild side fills each leftover block with `$A5`. The test does not compare the filled blocks, the stack area `$01C0-$01FF` and the I/O area.
- **`crack_leftover_a000`.** The rebuild side fills `$A000-$A9FF`: the copy of the crack relocator and the duplicated `$CF00` and `$E000` pages.
- **`crack_leftover_033c`.** The rebuild side fills `$033C-$03FE`: the encoded last stage of the protected loader, which the crack relocator copied there.
- The last two tests do not compare the stack area `$01C0-$01FF`. Below the stack pointer, this area holds old return addresses of the crack intro. Their values change with the time of the SPACE key.

**`no_protection`.** The reference is the TBC release (`releases/bruce_lee_tbc.prg`). Its game bytes are the default build without the protection patches, because the default build has the TBC state of `CRACK_DIABOLO`, `FIX_RAM_TEST_BYTE` and `RUN_STATE`. The rebuild is `build/clean_loader.prg`. At the game entry, the test destroys the protection data of the rebuild: `$00` = `$2F`, `$02` = 0, `$0080` = 0 and the `$CF00` page = 0. The test plays the title, the demo and room 0, and enters rooms 2, 5 and 10. It does not compare the bytes of the 13 `PROTECTION` patch ranges, `$0000-$0002` and the leftover bytes that `build/clean_loader.prg` does not load. The test stops each side at raster line 0 before each checkpoint, because `title_countdown` and `irq_vector` were different by one interrupt without the stops.

## Runs with expected values

These run files test the loader of the default build alone.

- **`start_screen`.** `build/clean_loader.prg` shows the Datasoft title picture without the TBC text, waits, and starts the game after a key.
- **`start_screen_fire`.** The fire button of port 2 also ends the wait.
- **`start_screen_waits`.** Without a key or a fire button, the loader keeps the picture and does not start the game.

## The runs in `../runs/`

| Run | What it shows |
|---|---|
| `loading_tbc_intro` | The TBC intro with the Datasoft title picture, the source of the start screen. |
| `room_change_freeze` | The steps of `all_rooms` up to room 15 with the moves of the first record file. Bruce leaves room 15 for room 13. `draw_room` switches the screen off on raster line 306 and on again on line 282. The raster compare line then stays at 320, and the game stops. The traces `moves01.json` and `moves02.json` hold the two writes to `$D011`. |
| `demo_f1_abort` | F1 ends the second attract demo, and fire ends the third. The coverage map starts at the game entry. |

## Old files for the evidence of the knowledge

The project knowledge gives some files as evidence of old revisions, and keeps the SHA-256 of each file. `link --check` of c64-docs fails when such a file is missing. Thus these files stay, although no test runs them:

- **`boot_game_start.json` and `boot_title_picture.json`.** They tested the hand-written boot `src/boot.asm` of 2026-10-18. The generated loader replaced the boot on 2026-10-21. The files have the formats of c64-re-tools 2.7, but they cannot run, because their programs `build/bruce_lee_boot.prg` and `build/bruce_lee_boot_TBC.prg` are gone. The knowledge comment at `$0872` of the space `loading` gives them as evidence.
  - `boot_title_picture` ran the default boot. The clean picture showed, and a key started `cold_start` and the title.
  - `boot_game_start` compared the TBC boot build with the TBC release. Both sides got the same key: TBC at its wait `$0872`, and the boot 5 frames after its key wait at `$08BF`. The title screen, the menu state and the memory were the same, except the leftover blocks.
- **`../original/`.** It holds the `image.json` of the captures of SAEGER, TBC, DC and the TBC intro, and a copy of `bruce_lee_tbc.prg`. The release files are in `../releases/`.

[PLAYTEST.md](PLAYTEST.md) is the checklist for a human playtest.
