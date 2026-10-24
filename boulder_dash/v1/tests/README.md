# Tests of Boulder Dash v1 (Micro Fun)

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Each record file loads `original/bd_obj_charsoft.prg` (the file `BD.OBJ` of the Charsoft disk, `$5000-$8D8E`). The C64 is at READY. Then the record file writes `$00` to `$5D`, the cave number. The value 0 means "no game yet", as after the boot of a release. Then the record file starts the program at its cold start `$8AB3`. Then it gives the input of the session.

| Recording | What it does |
|---|---|
| `cave_a` | F1 and fire start one player in cave A. Rockford walks a planned route, collects 12 diamonds and enters the exit. The bonus counts down and cave B starts. |
| `cave_tour` | Starts each of the 20 caves (A-P and the four intermissions) from the options screen and lets it run 500 frames without input. |
| `lives` | A boulder kills Rockford, then the time runs out, then RUN/STOP gives up the last life. Game over. |
| `options_two_players` | F3 cycles the player modes. The joystick selects the cave and the level. Two players play cave I on level 2 and give up each life with RUN/STOP. |
| `pause_restart` | 3000 title frames without input, then a game. SPACE pauses and resumes. F1 starts the program again. |
| `extras` | Two players with two joysticks. A bonus life at 500 points, a boulder push, player 2 on joystick port 2, and RESTORE. |
| `magic_wall` | Cave H with a falling boulder above the magic wall. The wall becomes active and runs until its time ends. |

Each step waits for a state of the game, not for a time. A move of Rockford waits until the target cell of the cave map (`$0850-$0BBF`) holds Rockford (`$38`). Thus a change of the timing does not break a recording.

The record files write these bytes. Only the recordings have them. The project knowledge, the source and the builds do not.

| Recording | Address | Bytes | Why |
|---|---|---|---|
| all | `$5D` | `00` | The cold start reads the cave number. A boot of a release leaves 0 there. |
| `cave_tour`, `magic_wall` | `$5D` | `01`-`14` | The cave to start. The options screen offers only the caves A, E, I and M. |
| `extras` | `$5F-$64` | `00 00 00 04 09 00` | The score 490. The first diamond gives 500 points and a bonus life. |
| `magic_wall` | `$0A8E` | `12` | A falling boulder at row 14, column 14 of cave H, above the magic wall. |

The game takes its random numbers from the CIA timers (`random_from_timers`). The recordings do not record the timers as input. With the timers, the cave reveal makes the busiest input site. Then the events of a record file wait for reads that do not come. Thus a replay on a rebuild can give other random numbers than the original. The amoeba, the boulder push, the reveal of a cave and the blink of Rockford use them.

## Replays

```
node <c64-testing>/scripts/testing.ts replay tests/recordings/cave_a --checkpoint scan_cave \
  --state '$0850:880' --state lives --state cave_number --state level --state score_digits:6 \
  --state diamonds_collected:2 --state exit_reached --state cave_end_state --state rockford_col:2 \
  --rebuild build/clean.prg --symbols build/symbols/clean.json
```

`scan_cave` runs one time in each tick of the game. The state is the cave map, the lives, the cave and the level. It also has the score, the diamonds, the exit flag, the end state and the position of Rockford. Build `build/clean.prg` with the c64-assembler skill (`build src main.asm`) first.
