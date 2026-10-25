# The tests of version II

The record files, scenarios and run files in this folder have only the keys of the c64-testing formats. This page holds the notes of each file: the conditions of the test and the parts that the test does not compare.

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Claude wrote the input as steps. No person played. Each record file starts `original/fist_v2_scc.prg`, the loader of the SCC release. The loader shows the Melbourne House picture, plays the speech and loads the game. The coverage map of each recording starts at the game entry `$115A`.

Player 1 uses the joystick in port 2 (`$DC00`), and player 2 uses port 1 (`$DC01`). [`read_title_keys` `$1E64`](../src/game/title_and_scene.asm#L6) reads the function keys and DEL from row 0 of the keyboard matrix. It acts only when the row value changes. The `press` steps push the keys of the matrix.

| Recording | What it does | Checkpoints |
|---|---|---|
| `demo` | No input. The attract demo plays its four bouts to `demo_exit`, and the title loop starts the next demo. | 6581 |
| `title_keys` | F3 two times (2 PLAYER, then 1 PLAYER), F7 two times (KEYBOARD, then JOYSTICK) and DEL two times (samples off, then on). F1 starts a 1-player game, and F5 ends the game and goes back to the title. | 1190 |
| `f1_first_bout` | F1 starts a 1-player game. The recording ends at the start of the first bout. | 585 |
| `f1_one_player` | F1 starts a 1-player game, and the first seconds of the first bout play. | 307 |
| `keyboard` | F7 selects KEYBOARD, and fire starts a 1-player game. The player uses the keys Q W E A D Z X C and S. | 6666 |
| `one_player_moves` | Fire starts a 1-player game. The player does all 16 joystick moves until the game is over, and then types FIST and RETURN in the high score table. | 9262 |
| `two_player` | F3 selects 2 PLAYER, and fire starts the game. Both joysticks move and attack in the four bouts, and the judge shows the winner. | 11254 |
| `cpu_ranks` | A 1-player game where the computer plays for player 1 against an idle opponent. 80612 frames, through all ranks, the rank cap and the bull rounds. | 53394 |

One record file writes bytes only for the test. The project knowledge, the source and the builds do not have this change.

| Recording | Event | Why |
|---|---|---|
| `cpu_ranks` | `cpu_controlled` = 1, 0 at `$1BBD`, after `game_one_player` sets it | The computer plays for player 1, and fighter 1 stands. |

**Event points.** A `runUntil` step to an address is an event at the n-th arrival at that address. The record files wait only one time for `read_title_keys`, at the first title. After that, they wait for routines that run one time in each part, for example `demo_exit`, `bout_frame_loop` or `hs_name_entry`, or they count frames.

**What `title_keys` shows.** Each key acts as the code tells. The run [`../runs/title_keys`](../runs/title_keys) does the same steps and keeps a screen and the mode bytes after each key. F3 changes `two_player_mode` to 1 and back to 0. F7 changes `keyboard_control` to 1 and back to 0. DEL changes `samples_off` to 1 and back to 0. F1 sets `in_game` and starts tune 2. F5 in the game jumps to `title_main_loop`, and the demo plays again (**Observed**).

## Replays

A replay on the default build uses `build/clean_loader.prg` with `build/symbols/clean_loader.json`. The replay runs the rebuild to `loader_start_screen_wait` and sets the PC to `loader_start_screen_continue`. Each record file holds its comparison:

- The checkpoint is [`frame_random_step` `$1AFF`](../src/game/bout_loop_1af4.asm#L15). Each pass of the bout loop calls it one time, in the demo and in each game.
- The state is `fighter_x` (4 bytes: X and Y of both fighters), `fighter_move` (2), `half_points` (2), `stage_counter` (6 bytes, with the AI levels) and `game_mode`. It also has the panel `$CC00-$CCC7`: the scores, the clock, the rank and the mode text.
- The pins are `frame_random` and `ai_random`.

```
node <c64-testing>/scripts/testing.ts replay tests/recordings/cpu_ranks \
  --rebuild build/clean_loader.prg --symbols build/symbols/clean_loader.json
```

**Why the random bytes are pins.** `frame_random` steps one time in each pass of the bout loop, and the one-player game copies it into `ai_random`. The rebuild starts from its own loader, so the title can take a different number of passes before a game. The pins give the rebuild the random bytes of the original at each checkpoint. All other state must then agree.

**The protection patch keeps the cycles.** The `PROTECTION` patch at `$2CAE` is `LDA #$00` and `NOP`, 4 cycles. The check of the original, `LDA $DD0E`, also takes 4 cycles. Thus each scoring hit takes the same time on both sides (**Code**).

All eight recordings replay on the original. They also replay on the default build with the same state at each checkpoint (**Observed**, c64-re-tools 2.6.0-rc.19). Each replay reports `idleReads: 5`. These are reads of the rebuild loader before its start screen, and they do not change the result.

## Scenarios

**`leftovers_unused`.** Both sides start the original loader. At the game entry, the rebuild side fills the 20 leftover ranges (1451 bytes) that `build/clean_loader.prg` leaves out with `$A5`, and more unused ranges. The demo and a game then give the same state and the same screens.

## Runs with expected values

- **`start_screen`.** `build/clean_loader.prg` shows the Melbourne House picture of the 2010 loading stage, calls the tune at `$9000`, waits, and starts the game.
- **`protection_trap_original`.** The original starts with `$08` in `$DD0E`, as after a KERNAL reset. The first scoring hit of the demo goes to the trap, and 600 frames later the CPU executes in the fighter shape data.
- **`protection_trap_rebuild`.** The default build with the same `$08` in `$DD0E`. The patch passes the check, and the demo plays on.

## The runs in `../runs/`

| Run | What it shows |
|---|---|
| `title_keys` | The steps of the recording `title_keys`, with a screen and the mode bytes after each key. |
| `loading_tune`, `loading_space_tune`, `stage_tune`, `loading_stage_rc3` | The coverage runs of the loading stage in the space `loading`: the picture, the speech and the tune at `$9000`. See [../../docs/loading_stage.md](../../docs/loading_stage.md). |
