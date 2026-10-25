# The tests of practice_v1

The record files in this folder have only the keys of the c64-testing format. This page holds the notes of each file: the conditions of the test and the parts that the test does not compare. The project is Part 1, Combat Practice, build V 05 05 87.

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Claude wrote the input as steps. No person played. Each record file starts `original/rdi/barbarian_part1_rdi.prg`, the game file of PART 1 of the Raw Deal Inc. release. The crack intro waits for a key, and a `press` of SPACE ends it. The coverage map of each recording starts at the game entry `$8009`.

Player 1 uses the joystick in port 2 (`$DC00`), and player 2 uses port 1 (`$DC01`). The game reads the keys through the keyboard matrix. The record files also give the CIA1 timers `$DC04` and `$DC06` as inputs, because the game reads them.

| Recording | What it does | Checkpoints |
|---|---|---|
| `attract` | No input. The demo: the computer fights the computer for 15000 frames. | 1489 |
| `decapitation` | The steps aim at one player against opponent 7, with no input. The F1 press gave a two-player game (**Observed**). No decapitation came. | 327 |
| `fight` | Each joystick direction with and without fire on port 2, then no input to the end. The F1 press gave a two-player game (**Observed**). | 917 |
| `keys` | The steps press F3 (music or effects) two times, CTRL+V and F5 in the demo, then F1, F3 two times, F7, F5 and Q. F5 pauses the demo, so F1 and F7 come during the pause. The recording ends in a pause, and F1, F7 and Q have no effect (**Observed**). | 87 |
| `two_decap` | Two players. Player 1 walks in and cuts off the head of player 2 (fire and back). The goblin drags the body away. | 290 |
| `two_players` | Two players. Player 1 does each move, then player 2 does each move, then no input. The bout ends with a decapitation (**Observed**). | 744 |
| `two_win` | Two players. Player 1 wins a bout against player 2, then the time bonus counts. | 346 |
| `win_bout` | Player 1 wins a bout against a fighter with energy 1. The F1 press gave a two-player game (**Observed**). Thus the background does not change. | 556 |

**F1 in part 1.** F1 toggles one and two players in each pass while the key is down. Thus the mode after a press depends on the number of passes during the press. The same steps can give the other mode in the other build. The table gives the mode that each recording really played (**Observed**: the code after the `two_players` test of `add_time_bonus` ran or did not run).

Some record files write bytes only for the test. The project knowledge, the source and the builds do not have these changes.

| Recording | Event | Why |
|---|---|---|
| `decapitation` | `opponent_index` = 7 after the first `main_loop` | The strongest computer opponent decapitates an idle player at once. |
| `win_bout`, `two_win` | `fighter_energy+1` = 1 after the first `main_loop` | The opponent dies at the next hit, so the record files can win a bout with few steps. |

**Event points.** A `runUntil` step to an address is an event at the n-th arrival at that address. The record files wait for `main_loop` before each write. After an event, the record files count frames before the next input.

## Replays

A replay on the default build uses `build/clean_loader.prg` with `build/symbols/clean_loader.json`. The loader has no start screen. The replay counts from the game entry `$8009`, where the loader jumps to.

- The checkpoint is `main_loop` `$80BB`. It runs one time in each pass of the game.
- The state is `fighter_energy` (2 bytes), `fighter_x` (2), `fighter_move` (2), `opponent_index`, `scene_index`, `bout_loser` and `final_stage`.
- The replay needs no pins.

```
node <c64-testing>/scripts/testing.ts replay tests/recordings/fight --checkpoint main_loop \
  --state fighter_energy:2 --state fighter_x:2 --state fighter_move:2 --state opponent_index \
  --state scene_index --state bout_loser --state final_stage \
  --rebuild build/clean_loader.prg --symbols build/symbols/clean_loader.json
```

All 8 recordings replay on the original. They also replay on the default build with the same state at each checkpoint (**Observed**, c64-re-tools 2.6.0-rc.20).

**Why the loader must keep the timer phase.** The game starts the CIA1 timers without a force load. Thus the phase of the timer interrupts comes from the state at the entry. A loader of rc.19 entered with another timer value, and the replays went one frame off after about 500 checkpoints. The loader of rc.20 waits for a raster line and loads the timers before it jumps to `$8009`. With this loader, all replays pass (**Observed**).

## The runs in `../runs/`

These runs give the screens of the documentation. A run does the steps of a record file on the original, but it does not replay the recorded input. Thus the computer can fight in another way than in the recording.

| Run | What it shows |
|---|---|
| `screens_two_players` | The `two_players` steps with a screen each 400 frames: the sunset, the scene change and the forest. |
