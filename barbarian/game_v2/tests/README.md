# The tests of game_v2

The record files in this folder have only the keys of the c64-testing format. This page holds the notes of each file: the conditions of the test and the parts that the test does not compare. The project is Part 2, the story game, build V 05 10 87.

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Claude wrote the input as steps. No person played. Each record file starts `releases/fairlight/barbarian_p2_flt.prg`, the game file of BARBARIAN P2/FLT of the Fairlight release. The crack intro waits for a key, and a `press` of SPACE ends it. The coverage map of each recording starts at the game entry `$8009`.

Player 1 uses the joystick in port 2 (`$DC00`), and player 2 uses port 1 (`$DC01`). The game reads the keys through the keyboard matrix. The record files also give the CIA1 timers `$DC04` and `$DC06` as inputs, because the game reads them.

The recording `keys` ends in the pause loop [`read_keys_pause_wait` `$9463`](../src/input/keyboard.asm#L100).

| Recording | What it does | Checkpoints |
|---|---|---|
| `attract` | No input. The demo: the computer fights the computer for 15000 frames. | 1427 |
| `decapitation` | One player against opponent 7, no input. The record file aims at a decapitation, but in this build the computer kills the player with normal hits. The goblin drags the body away (**Observed**: `check_decapitation_begin` did not run). | 248 |
| `fight` | One player. Each joystick direction with and without fire, then no input to the end of the game. | 816 |
| `final_lose` | One player wins a bout against opponent 7. Then the player stands still, and the bolt of Drax kills him. | 201 |
| `final_win` | One player wins a bout against opponent 7. Then the player rolls and crouches under the bolts of Drax and reaches the princess. | 180 |
| `keys` | The steps press F3 (music or effects) two times, CTRL+V and F5 in the demo, then F1, F3 two times, F7, F5 and Q. The program calls `read_keys` 45 times and reads F5 at call 43. Then it stays in `read_keys_pause_wait`. Thus the recording ends in the F5 pause (**Observed**). | 45 |
| `win_bout` | One player wins a bout. The background changes for opponent 1, then no input to the end of the game. | 470 |

Some record files write bytes only for the test. The project knowledge, the source and the builds do not have these changes.

| Recording | Event | Why |
|---|---|---|
| `decapitation` | `opponent_index` = 7 after the first `main_loop` | The strongest computer opponent decapitates an idle player at once. |
| `win_bout`, `final_lose`, `final_win` | `fighter_energy+1` = 1 after the first `main_loop` | The opponent dies at the next hit, so the record files can win a bout with few steps. |
| `final_lose`, `final_win` | `opponent_index` = 7 after the winning hit | The win is against opponent 7, so the final stage follows. |

**Event points.** A `runUntil` step to an address is an event at the n-th arrival at that address. The record files wait for `main_loop` before each write. `final_lose` and `final_win` also wait for `$84A7` in `end_bout_final_stage`, the start of the final stage, and then for `main_loop` again. After an event, the record files count frames before the next input.

## Replays

A replay on the default build uses `build/clean_loader.prg` with `build/symbols/clean_loader.json`. The loader has no start screen. The replay counts from the game entry `$8009`, where the loader jumps to.

- The checkpoint is [`main_loop` `$80BB`](../src/main/main_loop.asm#L6). It runs one time in each pass of the game.
- The state is `fighter_energy` (2 bytes), `fighter_x` (2), `fighter_move` (2), `opponent_index`, `scene_index`, `bout_loser` and `final_stage`.
- The replay needs no pins.

```
node <c64-testing>/scripts/testing.ts replay tests/recordings/fight --checkpoint main_loop \
  --state fighter_energy:2 --state fighter_x:2 --state fighter_move:2 --state opponent_index \
  --state scene_index --state bout_loser --state final_stage \
  --rebuild build/clean_loader.prg --symbols build/symbols/clean_loader.json
```

All 7 recordings come from runs of the reference file, the FLT crack. They replay on the default build with the same state at each checkpoint (**Observed**, c64-re-tools 2.7.0-rc.1).

**Why the loader must keep the timer phase.** The game starts the CIA1 timers without a force load. Thus the phase of the timer interrupts comes from the state at the entry. A loader of rc.19 entered with another timer value, and the replays went one frame off after about 500 checkpoints. The loader of rc.20 waits for a raster line and loads the timers before it jumps to `$8009`. With this loader, all replays pass (**Observed**).
