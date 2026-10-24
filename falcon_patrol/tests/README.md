# Tests of Falcon Patrol

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Each record file loads `original/bombardieri/falcon.prg`, the game file `$2000-$6000` of the base release. The C64 first runs to the READY prompt. Then the record file sets the PC to the entry `$4100` (SYS 16640).

The game reads joystick port 1 at `$DC01`. The keys LEFT ARROW, 1, CTRL, 2 and SPACE give the same bits, because they are in column 7 of the keyboard matrix. Claude made all recordings with scripted input. No person played them.

| Recording | What it does |
|---|---|
| `title` | The title screen and the title tune for 1500 frames. FIRE starts a game. Then the first refuel on the pad. |
| `keyboard` | SPACE starts a game. Then 150 random taps of LEFT ARROW, 1, CTRL, 2 and SPACE: take-offs, turns, missiles and crashes. |
| `random_flight` | Random joystick input for 15000 frames (seed 7): take-offs, crashes, game overs and new games. |
| `heavy_fire` | Random joystick input with short FIRE taps for 20000 frames (seed 1): many missiles, an empty AAM count and refuels. |
| `high_score` | A game with a score, a game over, the name entry and the title time-out. See the next section. |

### The test hook of `high_score`

No scripted session shot an enemy down. The kill test needs an enemy and a missile in the same character row, and the enemies leave row 0 only at random. Thus `high_score` writes these bytes when the main loop starts for the first time. Only this recording has them. The project knowledge, the source and the builds do not.

| Address | Bytes | Why |
|---|---|---|
| `$0012` | `00 01 07 05 00` | The score 01750. A score of 0 never goes into the high-score table. |
| `$001D` | `00` | No spare jet. The first crash ends the game. |

Then the jet leaves the pad and dives to the ground. The name entry reads the stick one time in each pass of its loop, about every 7 frames. Thus each step of the entry waits for the loop at `$4CDF` before it sets the stick. A hold of a fixed number of frames moves the cursor one or two letters. The steps enter the letters F and P, and then `_` ends the entry. After the entry the title runs for 4000 frames without FIRE.

## Replays

A replay on the default build uses `build/clean.prg`, the build of `src/main.asm`, with `build/symbols/clean.json`. The recordings load a program and set the PC, so they cannot start the loader. The checkpoint is `main_loop`. The state is the score, the lives, the AAM count and the GAS count. It is also the jet state, the speed and climb rate of the jet, and the map column.

## The start of the original

The game turns off the CIA 1 interrupts at `$4116`, but it never reads `$DC0D`. When the KERNAL timer runs out between the SEI at `$4100` and that store, the game hangs in its raster interrupt. A start from the READY prompt at `$E5D4` hits this window in the test machine. Thus `loader_title.json` and the screen runs start the original at `$EA81`, right after the KERNAL interrupt read `$DC0D`. The record files start at `$E5D4`. Their timing is different, and they miss the window.

| Test | What it does |
|---|---|
| `loader_title.json` | The clean loader starts with RUN, and the original file starts at `$4100`. At the first note of the title tune, the title screen, its colours, the VIC-II, the score and the lives are the same. |
