# Tests of Hover Bovver

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Each record file loads `program/tfp_6000.prg`, the MAIN block `$6000-$9FFF` of the TFP capture. It starts the block at its entry `$8000` with a `registers` step, as the rebuild starts. Claude wrote the input as steps. No person played.

Hover Bovver reads the joystick of player 1 in port 1 and of player 2 in port 2. The setup screen reads F1, F3, F5 and F7 through the KERNAL key code `$C5`. Each record file gives `$DC00`, `$DC01` and `$D012` as input: the actors read the raster line `$D012` for random numbers at `$9585` and `$96B6`. Thus a replay gives the rebuild the same random numbers.

A tap of an F key on the setup screen must be longer than about 8 frames, because the setup loop has a delay. A tap of more than about 16 frames counts two times. The record files use 10 frames for F3 and F5, 25 frames for F1 and 40 frames for F7.

| Recording | What it does |
|---|---|
| `attract` | No input for 9000 frames: the title, the logo, the llama walk and the high-score screen. |
| `setup` | Fire opens the setup screen. F1 nine times (lawn 1-8 and back to 1), F3 and F5 two times each, then F7 and the first scenes of lawn 1. |
| `lawn1` | One player on lawn 1 with random moves and fire, to game over and the high-score entry. |
| `two_players` | Two players and two sticks, random moves on both ports, to game over. |
| `keys` | C= + M (music off and on) and C= + P (pause, then a key) during play. |
| `lawn8` | Entry lawn 8 (flower beds and the gardener), random moves to game over. |
| `lawns` | All 16 lawns and the wrap to lawn 1 at the maximum speed. |
| `events` | RESTORE in play, a high-score entry 1 of 9000, and DOG TOLERANCE near empty. |
| `overheat_bite` | The mower overheats. Then the fire button stays down until Rover catches the neighbour. |

Some record files write bytes that only a test needs. The project knowledge, the source and the builds do not have them.

| Recording | Address | Bytes | Why |
|---|---|---|---|
| `lawns` | `$0022` | `00 00` | The grass counter. The write at the start of each lawn ends the lawn at once, as the skip trainer of HF does. |
| `events` | `$4C01` | `30 30 30 39 30 30 30` | High-score entry 1 = 0009000, so that the final score goes below it. |
| `events` | `$002B` | `11` | DOG TOLERANCE near empty, so that Rover gets annoyed. |
| `overheat_bite` | `$07D0-$07DE`, `$002C` | 15 x `22`, `1E` | A full MOWER OVERLOAD scale on row 24. The cooling code reads the cells of the screen, so the write fills both. |

A record file can write or wait for an address only while the game reads its input. The intro scenes and the bonus screen read no input for more than 600 frames. Thus the writes come at the start of a lawn, after a wait of frames.

## Replays

A replay on the default build uses `build/clean.prg`, the build of `src/main.asm`, with `build/symbols/clean.json`. The recordings load a program and set the PC, so they cannot start the loader. The checkpoint is `main_loop`, and `attract_loop` for `attract`. The state is `lawn_number`, `grass_count` (2 bytes), `mower_lender`, `current_player`, `loyalty_bar`, `tolerance_bar`, `overload_bar`, `gordon_col` (2 bytes), `score_digits` (8 bytes) and the high-score table `$4C01` (50 bytes). The table starts at `$4C01`. The byte `$4C00` before it keeps RAM bytes of the start, and they are different on each side.

```
node <c64-testing>/scripts/testing.ts replay tests/recordings/lawns --checkpoint main_loop \
  --state lawn_number --state grass_count:2 --state mower_lender --state current_player \
  --state loyalty_bar --state tolerance_bar --state overload_bar --state gordon_col:2 \
  --state score_digits:8 --state '$4c01:50' \
  --rebuild build/clean.prg --symbols build/symbols/clean.json
```

## Scenario

`startup.json` starts the TFP file of the original (its BASIC does `SYS 32768`) and `build/clean_loader.prg`, the verified loader of the default build. Both run to `attract_loop`. Then the scenario compares the charset `$2000-$27FF`, the sprites `$3000-$3FFF`, the row tables `$0340` and `$0360`, the high-score table, the interrupt vectors and the VIC-II. At the high-score screen it compares the screen, the screen memory and the colour RAM.
