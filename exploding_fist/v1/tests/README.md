# The tests of version I

The record files, scenarios and run files in this folder have only the keys of the c64-testing formats. This page holds the notes of each file: the conditions of the test and the parts that the test does not compare.

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Claude wrote the input as steps. No person played. Each record file starts `original/fist_v1_2010.prg`, the loader of the 2010 release. The loader shows the Melbourne House picture, plays the speech and loads the game. The coverage map of each recording starts at the game entry `$1158`.

Player 1 uses the joystick in port 2 (`$DC00`), and player 2 uses port 1 (`$DC01`). [`read_title_keys` `$1948`](../src/game/title_and_scene.asm#L6) reads the function keys from row 0 of the keyboard matrix. It acts only when the row value changes. The `press` steps push the keys of the matrix for 6 frames.

| Recording | What it does | Checkpoints |
|---|---|---|
| `demo` | No input. The attract demo plays its four bouts to `demo_exit`, and the title loop starts the next demo. | 8635 |
| `title_keys` | F3 two times (2 PLAYER, then 1 PLAYER), F7, F1 starts a 1-player game, and F5 ends the game and goes back to the title. | 987 |
| `one_player_moves` | The demo, then fire starts a 1-player game. The player does all 16 joystick moves until the game is over. | 9608 |
| `two_player` | F3 selects 2 PLAYER, and fire starts the game. Both joysticks move and attack in the four bouts. | 11594 |
| `cpu_ranks` | A 1-player game where the computer plays for player 1 against an idle opponent. 80610 frames, through all ranks and into the rank overflow. | 64935 |

One record file writes bytes only for the test. The project knowledge, the source and the builds do not have this change.

| Recording | Event | Why |
|---|---|---|
| `cpu_ranks` | `cpu_controlled` = 1, 0 at `$16BA`, after `game_one_player` sets it | The computer plays for player 1, and fighter 1 stands. |

**Event points.** A `runUntil` step to an address is an event at the n-th arrival at that address. The record files wait only one time for `read_title_keys`, at the first title. After that, they wait for `demo_exit` or `bout_frame_loop`, or they count frames.

**What `title_keys` shows.** Each key acts as the code tells. The run [`../runs/title_keys`](../runs/title_keys) does the same steps and keeps a screen and the mode bytes after each key. F3 changes `two_player_mode` to 1 and back to 0, and the panel shows 2 PLAYER and then 1 PLAYER. F7 changes nothing. F1 sets `in_game` and starts tune 2. F5 in the game jumps to `title_main_loop`, and the demo plays again (**Observed**).

## Replays

A replay on the default build uses `build/clean_loader.prg` with `build/symbols/clean_loader.json`. The replay runs the rebuild to `loader_start_screen_wait` and sets the PC to `loader_start_screen_continue`. Each record file holds its comparison:

- The checkpoint is [`frame_random_step` `$1613`](../src/game/init_bout_loop_1608.asm#L15). Each pass of the bout loop calls it one time, in the demo and in each game.
- The state is `fighter_x` (4 bytes: X and Y of both fighters), `fighter_move` (2), `half_points` (2), `stage_counter` (6 bytes, with the AI levels) and `game_mode`. It also has the panel `$CC00-$CCC7`: the scores, the clock, the rank and the mode text.
- The pins are `frame_random` and `ai_random`.

```
node <c64-testing>/scripts/testing.ts replay tests/recordings/cpu_ranks \
  --rebuild build/clean_loader.prg --symbols build/symbols/clean_loader.json
```

**Why the random bytes are pins.** `frame_random` steps one time in each pass of the bout loop, and the one-player game copies it into `ai_random`. The rebuild starts from its own loader, so the title can take a different number of passes before a game. The pins give the rebuild the random bytes of the original at each checkpoint. All other state must then agree.

All five recordings replay on the original. They also replay on the default build with the same state at each checkpoint (**Observed**, c64-re-tools 2.6.0-rc.19). Each replay reports `idleReads: 5`. These are reads of the rebuild loader before its start screen, and they do not change the result.

## Scenarios

A scenario runs the original and a rebuild side by side and compares them. These scenarios test what a replay cannot test.

- **`leftovers_unused`.** Both sides start the original loader. At the game entry, the rebuild side fills 36 unused ranges with `$A5`. These include the 26 leftover ranges (1029 bytes) that `build/clean_loader.prg` leaves out. The demo and a game then give the same state and the same screens.
- **`rank_overflow`.** Both sides start a 1-player game with the rank index 12 and stage 11, and the computer plays for player 1. The panel after the next promotion shows code bytes as rank text, the same on both sides. The project knowledge gives this test as the evidence of the rank overflow. `cpu_ranks` also plays into the overflow and compares the panel at each checkpoint.

## Runs with expected values

- **`start_screen`.** `build/clean_loader.prg` shows the Melbourne House picture of the 2010 loading stage, calls the tune at `$9000`, waits, and starts the game.
- **`bull_test`.** The original runs a demo bout. A stub at `$0200` then calls `dev_clear_part_ptrs`, `dev_setup_fighter0` and `dev_bull_test`. The bull runs at the white fighter, hits him and runs over him. No code of the game calls this test.

## The runs in `../runs/`

| Run | What it shows |
|---|---|
| `title_keys` | The steps of the recording `title_keys`, with a screen and the mode bytes after each key. |
| `loading_tune`, `loading_space_tune`, `stage_tune`, `loading_stage_rc3` | The coverage runs of the loading stage in the space `loading`: the picture, the speech and the tune at `$9000`. See [../../docs/loading_stage.md](../../docs/loading_stage.md). |
