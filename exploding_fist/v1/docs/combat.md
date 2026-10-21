# Combat: hits and points (version I)

A fight in Exploding Fist is a series of exchanges. Each exchange ends with the hit reaction of a fighter or with the time-up. The game does not use the sprite collision to decide a hit. It tests one moment of each attack: the shape frame where the kick or punch is at full extension. At that moment, a table tells how far the attack reaches into the pose of the opponent. The distance between the fighters then gives a full point, a half point or a miss. The hit fighter shows a hit reaction. After the reaction, the game adds the points and the score.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one PAL video frame (50 each second). The bout loop runs the two fighters one time in each frame.
- A *shape frame* is the pose number in `fighter_frame` ($00-$47). A *target frame* is the shape frame of the opponent at the hit test.
- A *move* is the number in `fighter_move` ($00-$18). The *attack moves* are the 11 moves with the attack flag: $06, $07, $0A-$11 and $18.
- An *exchange* is one run of `bout_loop`, from the start positions to the end of a hit reaction or the time-up. A *bout* is the exchanges of one 30-second clock.
- *d* is the distance between the fighters in units of 2 pixels. The code measures it in the facing direction of the attacker. A positive d means "in front of the attacker".
- *E* is the target extent: the byte of the hit-zone table for the target frame.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

~~~mermaid
flowchart TB
  A["Each frame: update fighter 1, then fighter 0 (fighter_update)"] --> B{"Attack move at its hit frame? (hit_check)"}
  B -- no --> Z["No test"]
  B -- yes --> C{"Facings differ?"}
  C -- yes --> D["Hit-zone table of the move (move_hit_zone_facing)"]
  C -- no --> E["Same-facing table (move_hit_zone_same_facing)"]
  D --> F["E = table byte of the target frame"]
  E --> F
  F --> G{"E = $80, or d outside the window?"}
  G -- yes --> Z
  G -- no --> H["hit_points = 2 or 1"]
  H --> I["Reaction move for the opponent (hit_record)"]
~~~

[`hit_check` `$2459`](../src/hit_test.asm#L6) runs at the start of [`fighter_update` `$2233`](../src/fighter_moves.asm#L6), before the fighter reads its input. It starts the test only when all of these conditions are true (**Code**):

1. The move has the attack flag in `move_attack_flags`. Walks, jumps, blocks and somersaults never hit.
2. `anim_frame_tick` is 1: the animation started a new step in the last frame. Thus the test runs one time for each step, not in each frame that the pose shows.
3. `anim_reverse` is 0. An attack that retracts does not hit.
4. `pose_held` is 0. A fighter that holds its end pose, or that a hit froze, does not hit.
5. `fighter_frame` is the hit frame of the move in `move_hit_frames`.

The hit frame is in the last step of ten attack scripts. Moves $0E and $10 show the hit frame in two steps in a row, so their test can run two times, at two positions (**Code**). The flying kick $0E holds its kick after the hit frame $0A in shape frame $3A. Frame $3A is a copy of frame $0A with other hit zones, so the held pose does not start more tests (**Code**).

Then [`hit_test` `$2477`](../src/hit_test.asm#L23) does the test itself:

1. It compares `fighter_facing` of the two fighters. When the facings differ, it takes the word of the move in `move_hit_zone_facing`. When they are the same, it takes the word in `move_hit_zone_same_facing`. The pointer goes into `hit_zone_ptr`.
2. It reads E from the table with the target frame as the index. The value $80 means that this pose cannot be hit by this attack. The test ends without a hit.
3. It calculates d. For facing 0 (the fighter looks right), d = opponent x - own x. For facing 1, d = own x - opponent x. It adds $80 to E and to d, so that one unsigned compare can test signed values.
4. It compares d with the reach window of the move (see the next section). A full point sets `hit_points` of the attacker to 2. A half point sets it to 1.
5. In the two-player game, `hit_full_point` and `hit_half_point` draw the yin-yang of the attacker at once.
6. [`hit_record` `$2591`](../src/hit_test.asm#L175) writes the move into `scoring_move` and the reaction move into `hit_reaction` of the opponent.

A miss changes nothing, and the attacker gets no penalty (**Code**).

### The reach window

Two tables give the size of the window for each move: `move_full_reach` (F) and `move_half_reach` (H). The reach type in `move_reach_types` selects the side of E where the window lies. The code at `hit_test` gives these windows when the facings differ (**Code**):

| Reach type | Full point | Half point | Miss |
|---|---|---|---|
| 0 (nine attacks) | E - F <= d <= E | E - H <= d < E - F | d > E (too far) or d < E - H (too close) |
| 1 (moves $0F and $10) | E <= d < E + F | E + F <= d < E + H | d < E or d >= E + H |

The reach type is 0 for nine attack moves and 1 for the attacks $0F and $10. The moves $03 and $09 also have reach type 1, but they are no attacks. `move_reach_types` has only 21 bytes, so the move $18 reads the first byte of `move_full_reach`, which is 0 (**Code**).

For reach type 0, E is the far limit. **Conclusion:** E is the distance where the foot or the fist just touches the body in that pose. An attack scores a full point only at full extension, in a window of F + 1 units. Nearer, it scores a half point. A fighter that stands too near gets no point at all. An example is the high kick $0D with F = 2 and H = 5. A full point needs d in E-2..E, and a half point needs d in E-5..E-3 (**Code**).

For reach type 1, the extents of the facing tables are negative, from -35 to -9. Thus the attacks $0F and $10 hit an opponent behind the attacker. With facings that differ, the two fighters then stand back to back (**Code**). The coverage shows that such a hit landed in the run `cov_1p_lose`: `hit_reaction_1a` ran, but the same-facing path did not run in that run (**Observed**).

### The same-facing path

When both fighters look the same way, the attacker looks at the back of the opponent, or the opponent stands behind the attacker. [`hit_same_facing_zone` `$252D`](../src/hit_test.asm#L120) is a mirror of the normal test. It changes the sign of d, and it uses the window of reach type 1 for reach type 0, and the other way. The 11 same-facing tables agree with this: their extents are negative for the forward attacks and positive for $0F and $10 (**Code**).

The first four study runs did not reach this path. The coverage of the recordings `one_player_moves`, `two_player` and `cpu_ranks` shows that `hit_test_same_facing` and `hit_same_facing_zone` ran, so the game read the same-facing tables (**Observed**). A same-facing hit landed in `one_player_moves` and `two_player`: `hit_reaction_same_facing` ran (**Observed**). The window of reach type 1 in this path (`$2580-$2590`) never ran. The source comment "No run executed this path" at `hit_test_same_facing` is older than the recordings. The recordings are in [tests/record](../tests/record).

### The hit reaction

`hit_record` chooses the reaction move of the opponent from the move of the attacker. In the three reaction moves $16, $1A and $1B, bit 4 is 1. The scoring code uses that bit (**Code**).

| Reaction | Moves that give it | Shape frames | Movement | Length of the animation |
|---|---|---|---|---|
| $16 | $06, $0A, $0B, $0D, $0E, $11 (facings differ) | $29-$2C | -29, +6, -9, +4: 28 units back in all | 119 frames |
| $1A | $0F, $10 (facings differ). Every same-facing hit of reach type 0 | $25-$28 | none | 115 frames |
| $1B | $07, $0C, $18 (facings differ) | $2D-$2F | none | 100 frames |

The same-facing path gives $16 for reach type 1, but that branch never ran (**Observed**). The length is the sum of the step delays of the animation scripts $16, $1A and $1B (**Code**).

The reaction does not start at once. [`fighter_get_input` `$225F`](../src/fighter_moves.asm#L30) puts `hit_reaction` into the input of the hit fighter. Then `move_update_state` freezes the pose with `pose_held` for 8 frames (`knockdown_delay`, 8 for each exchange). After that, the fighter changes to the reaction move. When the reaction animation ends, `move_anim_end` writes the move into `bout_knockdown`, and the exchange ends (**Code**). The bout clock stops while a fighter has a hit reaction (**Code**).

**Conclusion:** both fighters can hit in one exchange. `bout_loop` updates fighter 1 first, and `hit_check` of fighter 0 runs before fighter 0 reads its reaction input. In that case the scoring code gives no point to either fighter (see below).

### The range test and the blocks

[`hit_range_test` `$25D3`](../src/hit_test.asm#L213) answers a different question: is the attack of the opponent near enough to block? `move_fix_input` and `ai_update` call it. A human blocks with "back" while the opponent attacks. The computer uses the same test (**Code**). Details of the blocks are on [fighters.md](fighters.md) and [ai.md](ai.md).

The test uses d without the $80 offset, measured in the facing direction of the defender (**Code**):

- Facings differ: "in range" when the move of the opponent has reach type 0 and d is -17 to 19 ($EF-$FF or $00-$13).
- Same facing: "in range" when the move of the opponent has reach type 1 and -d is 3 to 31. The "in range" result of this branch (`$2632-$2634`) never ran (**Observed**).

Thus the back attacks $0F and $10 are never "in range" when the facings differ. "Back" does not block them, and the range test of the computer also gives "out of range" for them (**Code**).

A block works only through the hit-zone tables. The counter move in `move_counter_moves` is $13 (low block, shape frame $23), $14 (high block, shape frame $0E) or $05 (jump). For each attack that a block answers, the facing table has $80 at the shape frame of that block. For the sweeps $0A and $10, the table has $80 at the jump frame $09 (**Code**). The one exception is $0F: its table has -28 at frame $0E, but the range test never starts that block (**Code**).

### The points and the score

The game adds the points after the exchange, not at the hit. Each mode handler calls `bout_loop` and then tests `hit_reaction` of both fighters. It takes the EOR of bit 4: the result is 1 only when exactly one fighter was hit. When both fighters were hit, nobody gets a point (**Code**).

- **One player** ([`bout_1p_exchanges` `$175F`](../src/game_modes.asm#L171)): the fighter that hit gets `hit_points` added to `half_points`. A half point adds 1, a full point adds 2. At 4 half points the bout ends at once with a win. Only player 1 gets score: `score_add_move`. Both fighters get the tie-break value: `bout_hit_value_add` (**Code**).
- **Demo** (`bout_demo_exchanges`): the same half points, but no score and no tie break (**Code**).
- **Two players** (`bout_2p_exchanges`): no half points. Each exchange gives score to the fighter that hit. The yin-yang shows from the hit until the end of the exchange. Then the code clears the yin-yang cells. A bout always lasts 30 seconds, and after 4 bouts the higher score wins (**Code**).

[`add_half_points` `$1843`](../src/game_modes.asm#L298) draws the symbols: a whole yin-yang for 2 half points, a half yin-yang for 1. It returns carry set at 4 or more. A full point at 3 half points gives 5, which also wins (**Code**).

[`score_add_move` `$1B1A`](../src/score_and_timer.asm#L118) reads `move_score_values` at `scoring_move`. The value is in hundreds of points. For a half point, it halves the value with LSR. All values are even, so the half is exact. Then it calls `score_add_100` that number of times. The first points change the tens digit from a space to 0 (**Code**). After a one-player win, `time_bonus_count` adds 100 points for each second that remains on the clock (**Code**).

### The tie break and its bug

When the clock reaches 0 in the one-player game, `bout_1p_exchanges` compares the half points. More half points win. With the same half points, the higher `bout_hit_value` wins. With the same value, the bout is a draw: both fighters bow and the bout starts again (**Code**).

`bout_hit_value` is the sum of the score values of the hits of a fighter in the bout, in hundreds, with half for a half point. [`bout_hit_value_add` `$1C1C`](../src/panel_texts.asm#L9) has a bug here: `LDY hit_points` has no `,X`. Thus the value of fighter 1 (the computer) uses the hit points of fighter 0 to select full or half (**Code**).

`hit_points` of fighter 0 keeps the result of the last hit of fighter 0. Only the hit test writes it, so the value can come from an earlier exchange, bout or game (**Code**). **Conclusion:** the bug can change the result of a time-up. An example from the tables:

1. Player 1 scores a full point with the low kick $0B (value 2). `bout_hit_value` of fighter 0 = 2, and `hit_points` of fighter 0 = 2.
2. The computer scores two half points with $0B. Each must add 1, but the bug reads `hit_points` = 2 and adds 2.
3. At time-up both fighters have 2 half points. The tie break compares 2 with 4, and the computer wins. Without the bug, the bout is a draw.

The reverse also occurs: after a half point of player 1, a full point of the computer counts only half (**Conclusion**).

## The data

### The move tables

`move_hit_frames`, `move_reach_types`, `move_full_reach`, `move_half_reach` and `move_score_values` are tables with one byte for each move, at `$1174-$12BB`. The table shows the values of the attack moves (**Code**). The joystick column gives the direction for a fighter that looks right.

| Move | Joystick | Hit frame | Reach type | F | H | Score full / half | Reaction | Counter |
|---|---|---|---|---|---|---|---|---|
| $06 | up + forward | $07 | 0 | 2 | 7 | 800 / 400 | $16 | $14 |
| $07 | down + forward from a crouch | $0D | 0 | 2 | 8 | 800 / 400 | $1B | $13 |
| $0A | fire + down | $10 | 0 | 3 | 10 | 400 / 200 | $16 | $05 |
| $0B | fire + down + forward | $08 | 0 | 1 | 6 | 200 / 100 | $16 | $13 |
| $0C | fire + forward | $05 | 0 | 2 | 8 | 200 / 100 | $1B | $13 |
| $0D | fire + up + forward | $0B | 0 | 2 | 5 | 800 / 400 | $16 | $14 |
| $0E | fire + up | $0A | 0 | 2 | 5 | 1000 / 500 | $16 | $14 |
| $0F | fire + up + back | $12 | 1 | 4 | 8 | 800 / 400 | $1A | $14 |
| $10 | fire + down + back | $39 | 1 | 3 | 10 | 800 / 400 | $1A | $05 |
| $11 | fire + back, after the turn | $24 | 0 | 3 | 8 | 1000 / 500 | $16 | $14 |
| $18 | down + forward from a stand | $13 | 0 | 2 | 8 | 600 / 300 | $1B | $13 |

The pointer words of the hit-zone tables, [`move_hit_zone_facing` `$121B`](../src/entry_and_tables.asm#L55) and `move_hit_zone_same_facing`, have 25 entries. The entries of the moves without an attack point to `$0000`, but `hit_check` never reaches the test for those moves (**Code**).

### The hit-zone tables

The 22 tables are at [`hitzone_up_fwd` `$7200`](../src/hit_zone_tables.asm#L6). Each table has 59 bytes, one for each target frame $00-$3A (**Code**):

| Byte | Meaning |
|---|---|
| `$80` | The attack cannot hit the opponent in this pose. |
| other | E, a signed distance in units of 2 pixels: the limit of the reach window. |

| Range | Contents |
|---|---|
| `$7200-$7488` | 11 tables for facings that differ, read through `move_hit_zone_facing` |
| `$7489-$7711` | 11 tables for the same facing, read through `move_hit_zone_same_facing` |

The order in memory is move $06, $07, $0A-$0F, $18, $11, $10 in both sets, not the order of the moves. **Conclusion:** the move $18 and the order of $10 and $11 changed after the authors made the tables. The details are on [../../docs/development.md](../../docs/development.md).

Each table can hit between 24 and 39 of the 59 target frames. The other bytes are $80 (**Code**):

- In all 22 tables, the frames of the hit reactions ($25-$2F) are $80. A fighter in a hit reaction cannot be hit again.
- In the facing tables, the block that answers an attack is $80 (see the range test above).
- In the same-facing tables, the block frames $23 and $0E have extents for nearly all attacks. **Conclusion:** a block does not protect the back of a fighter.

The tables have no entries for the shape frames $3B-$47. These are the frames of the unused bull and of an unused figure. A hit test against such a frame reads the first bytes of the next table. No animation script of the game uses these frames for a fighter (**Code**).

## The state machine of a hit

This diagram shows the fighter that the opponent hits. `move_update_state` and `move_anim_end` make each change.

~~~mermaid
stateDiagram-v2
  state "Fights (hit_reaction = 0)" as Fight
  state "Frozen (knockdown_delay > 0)" as Frozen
  state "Reacts (move $16, $1A or $1B)" as Fall
  [*] --> Fight
  Fight --> Frozen: the hit test of the opponent hits
  Frozen --> Fall: knockdown_delay = 0
  Fall --> [*]: the reaction animation ends, bout_knockdown is set
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Fights | `hit_record` writes `hit_reaction` | Frozen | `fighter_get_input`, `move_update_state` |
| Frozen | `knockdown_delay` = 0, after 8 frames | Reacts | `move_update_state` |
| Reacts | `anim_finished` = 1 | end of the exchange | `move_anim_end` |

## The worked example

The mid kick, move $0C (fire + forward), against an opponent in the stance, shape frame $00. The bytes come from the source (**Code**).

| Address | Table | Index | Byte | Meaning |
|---|---|---|---|---|
| `$1180` | `move_attack_flags` | $0C | $01 | an attack |
| `$120E` | `move_hit_frames` | $0C | $05 | the hit frame is $05, the third step of the script |
| `$11B2` | `move_reach_types` | $0C | $00 | reach type 0 |
| `$11C7` | `move_full_reach` | $0C | $02 | F = 2 |
| `$11E0` | `move_half_reach` | $0C | $08 | H = 8 |
| `$1233` | `move_hit_zone_facing` | $0C | $72EC | `hitzone_fire_fwd` |
| `$72EC` | `hitzone_fire_fwd` | frame $00 | $0E | E = 14 for the stance |
| `$72FA` | `hitzone_fire_fwd` | frame $0E | $0D | E = 13 for the high block |
| `$730F` | `hitzone_fire_fwd` | frame $23 | $80 | the low block cannot be hit |
| `$1199` | `move_counter_moves` | $0C | $13 | the low block answers this kick |
| `$12AF` | `move_score_values` | $0C | $02 | 200 points |

[`hitzone_fire_fwd` `$72EC`](../src/hit_zone_tables.asm#L46) gives E = 14 for the stance. With F = 2 and H = 8, the windows are:

| d | Result | Score |
|---|---|---|
| 15 or more | miss, too far | 0 |
| 12-14 | full point, `hit_points` = 2 | 200 |
| 6-11 | half point, `hit_points` = 1 | 100 |
| 5 or less | miss, too near | 0 |

A worked case: fighter 0 at x = $3E looks right, and fighter 1 stands at x = $4A in shape frame $00.

1. `hit_target_extent` = $0E + $80 = $8E. `fighter_distance` = ($4A - $3E) + $80 = $8C.
2. $8C < $8E, so the code goes to `hit_try_full_reach`. The carry is clear after the compare.
3. $8C + $02 = $8E. This is not less than $8E, so the hit is a full point. `hit_points` of fighter 0 = 2.
4. `hit_record` writes $0C into `scoring_move`. The reach type is 0 and the move is $0C, so `hit_reaction` of fighter 1 = $1B.
5. After the hit reaction, `score_add_move` adds 2 x 100 = 200 points, and `add_half_points` adds 2 half points: one whole yin-yang.

With fighter 1 at x = $46, `fighter_distance` = $88. $88 + 2 = $8A is less than $8E, but $88 + 8 = $90 is not. The kick scores a half point and 100 points. At the start positions, x = $3E and $5A, d is 28: the kick misses. If fighter 1 holds the low block (shape frame $23), the byte $80 stops the test at every distance. The high block (shape frame $0E) gives E = 13, so the mid kick hits it at d = 11-13 for a full point.

## Still open

- **The demo after F3.** With `two_player_mode` = 1, `hit_full_point` and `hit_half_point` also draw a yin-yang at the hit in the demo, at the offset of `yin_yang_fighter_offsets`. Does the panel show a wrong symbol? Run: press F3 on the title, wait for the demo, and capture the panel at a hit.
- **A double hit.** The code gives no point when both fighters are hit in one exchange. No run showed one. Run: a watchpoint on `hit_reaction` of both fighters in the recording `two_player`.
- **`hit_points` before the first hit.** No code clears `hit_points` ($63/$64). Which value does the tie break read when player 1 has no hit yet? Run: read $63 at the entry and at the first time-up.
- **The tie-break bug in play.** No run reached a time-up with the same half points. Run: a one-player bout with the hits of the worked example in the bug section, then let the clock reach 0.
- **Shape frames above $3A.** The study notes report reads of frame-table entries for frames above $47 in the run past the rank overflow. Does a hit test then read past the 59 bytes of a table? Run: the recording `cpu_ranks` with a watchpoint on `fighter_frame` for values above $3A.
- **Back to back.** Which moves put the fighters back to back, so that $0F and $10 hit? Run: the recording `one_player_moves` with a breakpoint at `hit_reaction_1a`.
