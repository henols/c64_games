# Combat: the hit test and the points (version II)

A fighter scores when the hit frame of an attack meets a frame of the opponent at the correct distance. The game then forces a hit reaction on the opponent, plays a sample, and ends the exchange when the reaction animation ends. The exchange handler of the game mode then adds the points. Version II uses the hit test and the scoring of version I without a change. It adds the samples of the hit reactions and a copy-protection check that runs on each scoring hit. The two-player game, the one-player game and the demo count the same hits in different ways. The full list of the changes from version I is on [versions.md](../../docs/versions.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- *Fighter 0* is player 1 (white). *Fighter 1* is player 2 or the computer (red). X selects the fighter, and `opponent_index` holds the other fighter.
- A *pass* is one run of the frame loop of `bout_loop`. It runs one time each frame, at raster line `$FD`.
- An *exchange* is one run of `bout_loop`: from the start positions to a fall or to the end of the time. A *bout* is the fight of 30 seconds in one scene. It has one or more exchanges.
- A *half point* is one half yin-yang symbol. A *full point* is two half points. Four half points win a bout of the one-player game.
- The *distance* is the x of the opponent minus the x of the attacker, in the direction that the attacker faces. The *extent* is the byte of the hit-zone table for the frame of the opponent.
- *Forward* is the direction that the fighter faces.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

~~~mermaid
flowchart TB
  A["Attack shows its hit frame (hit_check)"] --> B["Hit-zone byte for the opponent frame"]
  B -->|"$80 or distance out of the window"| M["Miss: nothing changes"]
  B -->|"in the window"| C["Full point (2) or half point (1)"]
  C --> D["Record the scoring move (hit_record)"]
  D --> P{"CIA2 control A = 0?"}
  P -->|"no"| T["Trap: false return address"]
  P -->|"yes"| R["Hit reaction and sample for the opponent"]
  R --> W["8 frames frozen, then the fall animation"]
  W --> E["End of the exchange (bout_knockdown)"]
  E --> S["Points, yin-yangs, score (exchange handler)"]
~~~

The fighter update calls the hit test first, before it reads the input. Thus a hit in a pass comes before the move of that pass. The steps of one hit are these, in the order of the code:

1. **The hit frame.** [`hit_check` `$2B70`](../src/hit_test.asm#L6) tests the move of fighter X. The move must have the attack flag, a new forward animation step, no held pose, and the hit frame of the move. Thus the test runs one time for each attack, in the frame where the attack shows its hit frame. (**Code**)
2. **The target extent.** [`hit_test` `$2B8E`](../src/hit_test.asm#L23) selects the hit-zone table of the move. One table is for fighters that face each other. A second table is for fighters that face the same way. The byte for the frame of the opponent is the extent. `$80` means that the attack cannot hit this frame. (**Code**)
3. **The reach window.** The routine compares the distance with the extent and the two reach values of the move. A distance near the extent gives a full point. A distance a little farther from the extent gives a half point. Each other distance is a miss, also a distance that is too short. (**Code**)
4. **The point.** `hit_full_point` and `hit_half_point` write 2 or 1 into `hit_points` of the attacker. In the two-player game, they also draw the yin-yang symbol at once. (**Code**)
5. **The record.** [`hit_record` `$2CA8`](../src/hit_test.asm#L175) writes the move into `scoring_move`. Then the CIA2 check runs (see the section below). Then the routine selects the hit reaction of the opponent and starts its sample. (**Code**)

Version I has the same code for the hit test. The hit-zone tables are the same 1298 bytes. The full description of the hit-zone tables and of the reach window is on [../../v1/docs/combat.md](../../v1/docs/combat.md). (**Code**)

The code for fighters that face the same way is a mirror of the normal code. It swaps the sign of the distance and the two rules of the reach type. No run of version I executed this code. The runs of version II executed it, and only the trap and the last return of `hit_range_test` have no coverage. (**Observed**, coverage)

### The reach window

The reach type of the move selects the side of the window. The table below gives the two rules. *d* is the distance + `$80`, and *e* is the extent + `$80`. The `$80` makes an unsigned compare possible. (**Code**)

| Reach type | Full point | Half point |
|---|---|---|
| 0 | e - full reach <= d <= e | e - half reach <= d < e - full reach |
| not 0 | e <= d < e + full reach | e + full reach <= d < e + half reach |

The reach type also selects the reaction. Only the roundhouse `$0F` and the back sweep `$10` have the reach type 1 among the attacks. (**Code**)

### The hit reactions and the samples

`hit_record` selects one of three reaction moves for the opponent and writes it into `hit_reaction`. The input routine of the opponent then uses this move in place of the joystick, the keyboard or the computer. Version II starts a sample with each reaction. Version I has no sample calls here. (**Code**)

| Reaction | When | Sample at the hit | Sample at the fall |
|---|---|---|---|
| `$16` | Facing each other: reach type 0, all other attacks. Same facing: reach type not 0. | 0 (0.08 s) | 3 at frame `$2C` |
| `$1A` | Facing each other: reach type not 0. Same facing: reach type 0. | 1 (0.46 s) | 3 at frame `$28` |
| `$1B` | Facing each other: the moves `$07`, `$0C` and `$18`. | 1 (0.46 s) | none |

[`sfx_play_sample_0` `$3158`](../src/sfx_sample_player.asm#L44) and [`sfx_play_sample_1` `$315E`](../src/sfx_sample_player.asm#L49) start the samples. [`move_start_hit_reaction` `$29CD`](../src/fighter_moves.asm#L21) starts sample 3 when the fall reaches frame `$2C` or `$28`. A new sample stops the sample that plays, because the start code stops the CIA1 timers first. The start code also clears all SID registers. The DEL key on the title screen sets `samples_off`, and then no sample starts. (**Code**)

The samples are in the assets: [sample 0](assets/sample0_knockdown.wav), [sample 1](assets/sample1_hit.wav) and [sample 3](assets/sample3_floor.wav). The start of an attack plays [sample 2](assets/sample2_attack.wav). The sample player is on [sound_music.md](sound_music.md). (**Observed**, render)

The bull round plays sample 1 for the reaction `$16`, not sample 0. The bull uses its own reach test and not this code (see the section about the bull). (**Code**)

## The CIA2 check in hit_record

Version II has a copy-protection check in the middle of `hit_record`. [`protect_cia2_check` `$2CAE`](../src/hit_test.asm#L180) reads `CI2CRA`, the control register A of CIA2 at `$DD0E`. The game never writes this register. The original loader leaves the value 0 there. A load through the KERNAL leaves `$08` there. (**Code**)

The check runs on each scoring hit, after the write of `scoring_move` and before the reaction. When the value is 0, the hit continues as normal. When the register has any bit at 1, [`protect_cia2_trap` `$2CB3`](../src/hit_test.asm#L194) pushes the value and `opponent_index` on the stack. Then it jumps into `anim_update` with X = `$4E`. The last RTS of `anim_update` pulls the two bytes. The CPU then continues at the register value * 256 + `opponent_index` + 1, for example `$0801`. (**Code**)

A test started the original with `$DD0E` = `$08`. At the first scoring hit of the demo, the CPU executed graphics data as code, at `$902C` after 600 frames. The panel showed no yin-yang, and the clock stopped at 27. The rebuild with `PROTECTION` = 0 continued to play, with yin-yangs and the clock at 21. The scenarios are [protection_trap_original.json](../tests/protection_trap_original.json) and [protection_trap_rebuild.json](../tests/protection_trap_rebuild.json). (**Observed**)

![The original after the trap: no yin-yang, and the clock stops at 27.](images/protection_trap_original.png)

The check is late and the failure is far from the check. Thus a cracker sees a crash in the animation code, not a test of a register. The default rebuild replaces the 3 bytes `LDA CI2CRA` with `LDA #$00` and a NOP. Version I has no such check. The full description is on [protection.md](../../docs/protection.md). (**Conclusion**, **Code**)

## The end of an exchange

The hit freezes the opponent before the fall. [`move_update_state` `$29B4`](../src/fighter_moves.asm#L6) decrements `knockdown_delay` from 8 to 0 and holds the pose. Then it starts the reaction animation. When the animation ends, `move_anim_end` copies the reaction into `bout_knockdown`, and `bout_loop` stops. (**Code**)

The clock does not run while a fighter has a hit reaction. `bout_loop` calls `timer_tick` only when both `hit_reaction` bytes are 0. Thus the fall takes no time from the bout. (**Code**)

The exchange handler then tests `hit_reaction` of the two fighters. Each reaction has bit 4 set. An EOR of the two bytes finds a hit of exactly one fighter. When both fighters hit in the same pass, the exchange gives no points to either fighter. (**Code**)

**Conclusion.** A double hit needs the hit frames of the two attacks in the same pass. Fighter 1 updates first, so fighter 0 can still score in that pass. After that pass, the hit fighter holds its pose, and its next hit test does not run.

## The points

Each game mode has its own exchange handler. The three handlers use the same hit data in different ways. (**Code**)

| Mode | Handler | Half points | Score | End of the bout |
|---|---|---|---|---|
| Two players | `bout_2p_exchanges` | Not counted. The yin-yang shows only during the exchange. | Both players | The end of the time |
| One player | `bout_1p_exchanges` | Both fighters | Player 1 only | 4 half points, or the end of the time |
| Demo | `bout_demo_exchanges` | Both fighters | None | 4 half points, or the end of the time |

[`score_add_move` `$206C`](../src/score_and_judge.asm#L173) reads the value of `scoring_move` in `move_score_values`. The value is in hundreds. A half point gives half of the value. The routine then calls `score_add_100` one time for each hundred. (**Code**)

[`add_half_points` `$1D5F`](../src/game_modes.asm#L321) adds `hit_points` to `half_points` and draws the yin-yang symbols for 1 to 4 half points. At 4 half points the fighter wins the bout and bows. A win before the end of the time adds 100 points for each second that remains (`time_bonus_count`). (**Code**)

In the one-player game, the hits of the computer give half points but no score. Only the score of player 1 goes to the high score table. (**Code**)

## The tie break and its bug

At the end of the time, the one-player game compares the half points. When they are equal, it compares `bout_hit_value` of the two fighters. Each hit adds the value of its move to this sum, and a half point adds half of the value. The higher sum wins, and the judge shows the winner. Equal sums give a draw: both fighters bow, and the bout starts again in the same scene. The recordings executed the tie break and the draw. (**Code**, **Observed** coverage)

[`bout_hit_value_add` `$2169`](../src/timer_and_texts.asm#L59) has a bug from version I. It reads `hit_points` without X, so it uses the last hit of fighter 0 for both fighters. For fighter 1 the code makes these errors (**Code**):

- When the last hit of fighter 0 was a full point, a half point of the computer counts the full value.
- When the last hit of fighter 0 was a half point, a full point of the computer counts half of the value.

Only `hit_test` writes `hit_points`. Thus the value of fighter 0 can come from an earlier bout or from the demo. (**Code**)

**Conclusion.** The bug changes only the tie break of the one-player game. A player who scores full points makes the hits of the computer count more in the tie break. The bout result by half points does not change, because `add_half_points` uses `hit_points` with X.

## The bull has its own reach test

The bull round does not call the fighter update, and thus no hit test, no `hit_record` and no CIA2 check run there. [`bull_reach_test` `$139D`](../src/bull_round.asm#L105) compares the distance from fighter 0 to the bull with `bull_reach_by_frame`, one byte for each frame of fighter 0. A hit forces the reaction `$16` on fighter 0, with sample 1. The fighter stops the bull with frame `$0D` of the crouch punch at a distance of `$19` to `$1D`. The details are on [bull_round.md](bull_round.md). (**Code**)

## The data

The attack moves and their entries in the move tables follow. The names come from the knowledge. "—" marks a move with no name in the knowledge. The joystick column gives the direction after the swap for the facing, from `joystick_move_table`. The move `$18` comes from `$07` when the fighter does not crouch. (**Code**)

| Move | Joystick | Name | Hit frame | Reach type | Full reach | Half reach | Full / half points | Reaction, facing each other |
|---|---|---|---|---|---|---|---|---|
| `$06` | up + forward | high punch | `$07` | 0 | 2 | 7 | 800 / 400 | `$16` |
| `$07` | down + forward, from a crouch | crouch punch | `$0D` | 0 | 2 | 8 | 800 / 400 | `$1B` |
| `$0A` | fire + down | foot sweep | `$10` | 0 | 3 | 10 | 400 / 200 | `$16` |
| `$0B` | fire + down + forward | low kick | `$08` | 0 | 1 | 6 | 200 / 100 | `$16` |
| `$0C` | fire + forward | — | `$05` | 0 | 2 | 8 | 200 / 100 | `$1B` |
| `$0D` | fire + up + forward | — | `$0B` | 0 | 2 | 5 | 800 / 400 | `$16` |
| `$0E` | fire + up | flying kick | `$0A` | 0 | 2 | 5 | 1000 / 500 | `$16` |
| `$0F` | fire + up + back | roundhouse | `$12` | 1 | 4 | 8 | 800 / 400 | `$1A` |
| `$10` | fire + down + back | back sweep | `$39` | 1 | 3 | 10 | 800 / 400 | `$1A` |
| `$11` | fire + back | back kick | `$24` | 0 | 3 | 8 | 1000 / 500 | `$16` |
| `$18` | down + forward, standing | low punch | `$13` | 0 | 2 | 8 | 600 / 300 | `$1B` |

The table `move_reach_types` has only 21 bytes. The move `$18` reads its reach type from the first bytes of `move_full_reach`, which are 0. (**Code**)

## The worked example

The low kick `$0B` hits an opponent that stands in frame `$00` and faces the attacker. The values come from the tables in [`entry_and_tables.asm`](../src/entry_and_tables.asm) and [`hit_zone_tables.asm`](../src/hit_zone_tables.asm). (**Code**)

1. `move_hit_zone_facing` for `$0B` points to `hitzone_fire_down_fwd`. Its byte for frame `$00` is `$0B`. Thus e = `$0B` + `$80` = `$8B`.
2. The reach type of `$0B` is 0. The full reach is 1, and the half reach is 6.
3. Full point: `$8A` <= d <= `$8B`. This is a distance of 10 or 11.
4. Half point: `$85` <= d < `$8A`. This is a distance of 5 to 9.
5. A distance below 5 or above 11 is a miss.
6. A full point gives 2 × 100 = 200 points. A half point gives 100 points. The opponent gets the reaction `$16` and sample 0.

## Still open

- Does a double hit in the same pass occur in play, and does the game show it correctly? — A run that puts the hit frames of both fighters in the same pass, with a breakpoint at `hit_record`.
- The value of `hit_points` of fighter 0 before its first hit after the start. — A run that reads `$6E` at the entry and at the first hit of the computer.
