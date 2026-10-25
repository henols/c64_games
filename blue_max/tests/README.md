# Tests of Blue Max

## Recordings

The recordings in `recordings/` come from the record files in `record/`. Each record file loads `original/anonymous/bluem_1.prg`, the game file `.BLUEM 1` of the anonymous release (`$2800-$804B`). The C64 of a recording has no disk drive. Thus the record file does the work of the starter `.BLUEM 2` with `write` steps. It writes the identity table 00..FF at `$1000`, the routine `STA $FC / LDA $FB / RTS` at `$0200`, the bytes `05 16 04` at `$0100` and the starter bytes at `$033C-$0437`. Then a `registers` step starts the game at its entry `$4000`. Claude wrote the input as steps. No person played.

Blue Max reads the joystick in port 2 (`$DC00`) and the keys F1, F3, F5, F7 and SPACE from the keyboard matrix. The random numbers mix the raster line `$D012` into `random_seed` (`$D9`). The records do not record `$D012`, because a wait loop of the interrupt reads it. A replay pins `random_seed` at each checkpoint in its place.

| Recording | What it does |
|---|---|
| `title_options` | The title for 1200 frames, then F1 (options), F3 and F5 on each line, F1 again. |
| `flight` | Take-off, then 7000 frames of random moves, shots and bombs until the end of the game. Fire starts a new game. |
| `pause` | Take-off and flight. F7 stops the game two times, and F7 starts it again. |
| `options_play` | Gravity on, PILOT CONTROL and a higher skill level, then a take-off with the stick pulled the other way and a long flight with crashes. |
| `crash` | A crash off the runway at low speed, a restart and a crash at the end of the runway. |
| `landing` | Take-off, flight to the first airfield, landing on the runway, refuel and rearm, take-off again, more flight. |
| `demo` | The title for 6000 frames: the tune ends and the demo mode flies the plane. |
| `space_pause` | SPACE in flight: GAME IN PAUSE until fire, two times. Then F7. |

The landing needs exact timing, because the plane must touch down at the near end of the runway. The record file gives frame counts that a test run measured with the play-time counter `$408B`.

## Replays

A replay on the default build uses `build/clean.prg`, the build of `src/main.asm`, with `build/symbols/clean.json`. The recordings load a program and set the PC, so they do not start the loader. The checkpoint is `main_loop`, and `title_screen_wait` for `title_options`. The state is `speed`, `altitude`, `fuel`, `bombs`, `plane_state`, `map_section`, `plane_x` and the score digits at `$40BE` (5 bytes). The pin is `random_seed`.

```
node <c64-testing>/scripts/testing.ts replay tests/recordings/landing --checkpoint main_loop \
  --state speed --state altitude --state fuel --state bombs --state plane_state \
  --state map_section --state plane_x --state '$40be:5' --pin random_seed \
  --rebuild build/clean.prg --symbols build/symbols/clean.json
```

All eight recordings replay on the original. They also replay on the default build with the same state at each checkpoint. The counts of checkpoints are: title_options 1755656, demo 3333, flight 10228, pause 3122, space_pause 1326, options_play 5394, crash 1468 and landing 6301.

## The scenario

`junk_loader_leftovers.json` compares two runs of `.BLUEM 1`. The original side gets the bytes of the anonymous release in `$0400-$07E7` (the help screen), `$0801-$0BFD` (the BASIC boot) and `$804D-$8149` (zeros). The rebuild side gets junk there. The title, the start and a flight give the same memory and the same screens. Thus the capture of the program leaves out these three ranges.

## The runs

The folders in `../runs/` hold runs that write game variables to reach the parts that the recordings do not reach. Each folder has the run file, the results, the screens and a coverage map. The project knowledge has each coverage map.

| Run | What it writes and shows |
|---|---|
| `city_west` | `map_section` = 2 and `invincible` = 1 after take-off: the city sections 2, 6 and 7. |
| `city_water` | `targets_left` = 0, `map_section` = 3 and `invincible` = 1: the sections 3, 4 and 5 with the special targets. |
| `mission_end` | The landing of the `landing` recording, with the three special targets cleared at touchdown: the mission ends. |
| `rank_10000` | Score 10000 before a crash. |
| `rank_20000` | Score 25000, skill level 2, gravity on and 6 targets hit before a crash. |
| `f3_check` | F3 in flight: the anonymous release fails the loader check and the game ends. |
| `damage` | All four damage flags set in flight. |
| `service_repair` | The landing with all four damage flags set at touchdown. The plane then stays on the runway. |
| `screens` | The screens of the documentation: title, demo, options, runway, flight and pause. |
