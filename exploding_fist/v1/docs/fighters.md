# The fighters (version I)

## What it does

Two fighters stand on the floor of the scene. A fighter can do only the moves of the game. The poses, the time and the movement of each move never change. In each pass, the program gets a requested move for each fighter. It comes from the joystick, from the AI, or from the hit test after a hit. A state machine then decides if the fighter can start the requested move now. For example, a sweep starts only from a held crouch, and "back" becomes a block when the opponent attacks. Each move plays an animation script with the pose, the time and the movement of each step. The shape builder draws each pose from 9 sprite parts.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of the bout frame loop. The loop waits for raster line `$FD`, so a pass is one video frame (1/50 second on a PAL C64).
- An *exchange* is one run of `bout_loop`: from the start positions until a fighter falls or the time ends.
- Fighter 0 is player 1 (white, joystick port 2). Fighter 1 is player 2 or the computer (red, joystick port 1). A variable of a fighter is a pair of bytes: +0 for fighter 0, +1 for fighter 1.
- *Facing* 0: the fighter looks to the right. *Facing* 1: the fighter looks to the left. *Forward* is the side that the fighter looks to. *Back* is the other side.
- A *unit* of `fighter_x` is 2 pixels.
- A *move* is a value of `fighter_move`. An *animation* is a script of `anim_script_table`. The animation of a move has the number of the move.
- A *step* is 4 bytes of a script. A *frame* is a value of `fighter_frame`: one pose of 9 sprite parts.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The bout frame loop calls [`fighter_update` `$2233`](../src/fighter_moves.asm#L6) one time for each fighter in each pass, first for fighter 1 and then for fighter 0. The routine does the full work of one pass for one fighter. (**Code**)

~~~mermaid
flowchart TB
  A["Hit test of the attack (hit_check)"] --> B["Requested move: hit reaction, AI or joystick"]
  B --> C["Back becomes a block, down-forward becomes $18 (move_fix_input)"]
  C --> D["Change the move (move_update_state)"]
  D --> E["Select the animation (move_start_anim)"]
  E --> F["Step the script and move the fighter (anim_update)"]
  F -->|"new step"| G["Build the 9 sprites of the frame (shape_build)"]
  F --> H["End of the script (move_anim_end)"]
  G --> H
  H --> I["Select the front fighter (front_fighter)"]
~~~

1. **The hit test.** `hit_check` tests if the attack of this fighter hits the opponent. A hit writes a hit reaction into `hit_reaction` of the opponent. [combat.md](combat.md) explains the hit test. (**Code**)
2. **The requested move.** [`fighter_get_input` `$225F`](../src/fighter_moves.asm#L30) writes `fighter_input`. A hit reaction of this fighter has priority over all other input. Else a computer fighter gets its move from `ai_update` ([ai.md](ai.md)), and a human fighter gets it from the joystick. (**Code**)
3. **The input fix-up.** [`move_fix_input` `$23E4`](../src/fighter_moves.asm#L269) changes two requests. "Back" becomes a block when the opponent attacks in range. "Down-forward" becomes move `$18` when the fighter is not in a crouch. (**Code**)
4. **The move.** [`move_update_state` `$22B7`](../src/fighter_moves.asm#L72) changes `fighter_move` by the rules of the state machine below. (**Code**)
5. **The animation.** [`move_start_anim` `$2438`](../src/fighter_moves.asm#L317) starts the animation of a new move. For a held pose, it writes 0 to `anim_number` for this pass, so the script stops and the fighter does not move. Then it jumps to the script stepper. (**Code**)
6. **The end of a script.** [`move_anim_end` `$2381`](../src/fighter_moves.asm#L206) acts on `anim_finished`. A finished hit reaction writes `bout_knockdown`, and this ends the exchange. A finished move holds its end pose or returns to the stance. (**Code**)
7. **The front fighter.** The fighter in `front_fighter` gets the sprites 0-2, and these sprites have priority over the other fighter. An attack move puts this fighter in front. A back kick (move `$11`) puts the opponent in front. While sprites 0-2 touch another sprite, the priority does not change. (**Code**)

The priority test reads the collision register `$D01E`, and this read clears the register. Fighter 1 makes the first read of each pass. Thus the read for fighter 0 sees only the collisions after that read (**Conclusion**, see **Still open**).

### The joystick

[`joystick_read_move` `$2270`](../src/fighter_moves.asm#L41) reads `$DC00` (port 2) for fighter 0 and `$DC01` (port 1) for fighter 1. Before the read, it writes 0 to `$DC02`, and after the read, it writes `$FF` again. With port A as an input, the keyboard scan does not pull the joystick bits low (**Conclusion**). The routine keeps bits 0-4: up, down, left, right and fire. A closed contact gives a 0 bit. (**Code**)

The table [`joystick_move_table` `$2297`](../src/fighter_moves.asm#L66) has 32 entries, one for each value of the 5 bits. Its directions are for facing 0. For a fighter with facing 1, the routine changes bits 2 and 3 with `EOR #$0C` before the table read. Thus "forward" in the table is always the side that the fighter looks to. (**Code**)

| Bits 0-3 | Direction (facing 0) | Without fire: value, move | With fire: value, move |
|---|---|---|---|
| `%1111` | centre | `$1F` → `$01` stance | `$0F` → `$01` stance |
| `%1110` | up | `$1E` → `$05` jump | `$0E` → `$0E` flying kick |
| `%1101` | down | `$1D` → `$04` crouch | `$0D` → `$0A` foot sweep |
| `%1100` | up + down | `$1C` → `$01` | `$0C` → `$01` |
| `%1011` | left (back) | `$1B` → `$03` walk back | `$0B` → `$11` back kick |
| `%1010` | up + left (up + back) | `$1A` → `$09` forward somersault | `$0A` → `$0F` roundhouse |
| `%1001` | down + left (down + back) | `$19` → `$08` backward somersault | `$09` → `$10` back sweep |
| `%1000` | up + down + left | `$18` → `$01` | `$08` → `$01` |
| `%0111` | right (forward) | `$17` → `$02` walk forward | `$07` → `$0C` mid kick |
| `%0110` | up + right (up + forward) | `$16` → `$06` high punch | `$06` → `$0D` high kick |
| `%0101` | down + right (down + forward) | `$15` → `$07` punch from the crouch (`$18` outside a crouch) | `$05` → `$0B` low kick |
| `%0100` | up + down + right | `$14` → `$01` | `$04` → `$01` |
| `%0011` | left + right | `$13` → `$01` | `$03` → `$01` |
| `%0010` | left + right + up | `$12` → `$01` | `$02` → `$01` |
| `%0001` | left + right + down | `$11` → `$01` | `$01` → `$01` |
| `%0000` | all four | `$10` → `$01` | `$00` → `$01` |

The names of the moves are a **Conclusion**, see the next section. The table gives 16 moves: 8 directions without fire and 8 directions with fire. Fire alone and all other values give the stance. The table never gives the moves `$12-$18`. The state machine and the input fix-up make them. (**Code**)

The facing change has a special case. The routine does not change bits 2 and 3 when both are 1 (no left and no right). When both are 0 (left and right together), the `EOR` makes them 1. Thus "up + left + right" gives the stance with facing 0, but a jump with facing 1. A joystick cannot close the left and the right contact together, so a player does not see this (**Code**, **Conclusion**).

### The moves

The code has 25 moves, `$00-$18`. Each move table in `entry_and_tables.asm` has one byte for each move. The joystick, the frames, the time, the movement and the end of each move come from the code. The names are a **Conclusion** from the poses, the blocks and the joystick. Move `$00` has no script and no input gives it. (**Code**)

| Move | Request (facing 0) | Frames of the script | Passes | dx (units) | End |
|---|---|---|---|---|---|
| `$00` none | none | no script (pointer `$0000`) | - | - | - |
| `$01` stance | centre, fire alone | `$00` | 1 | 0 | stance |
| `$02` walk forward | forward | `$01 $02 $03 $00 $33 $30 $31 $32 $03 $00` | 61 | +38 | switch |
| `$03` walk back | back | `$03 $02 $01 $00 $32 $31 $30 $33 $01 $00` | 61 | -38 | switch |
| `$04` crouch | down | `$0C` | 15 | 0 | hold |
| `$05` jump | up | `$19 $09 $19` | 39 | 0 | stance |
| `$06` high punch | up + forward | `$06 $07` | 9 | +6 | hold |
| `$07` punch from the crouch | down + forward, in a held crouch | `$0D` | 2 | 0 | hold |
| `$08` backward somersault | down + back | `$19 $17 $16 $20 $15 $14 $19` | 63 | -39 | stance |
| `$09` forward somersault | up + back | `$19 $14 $15 $20 $16 $17 $19` | 61 | +39 | stance |
| `$0A` foot sweep | fire + down, in a held crouch | `$0F $10` | 14 | 0 | hold |
| `$0B` low kick | fire + down + forward | `$04 $08` | 7 | 0 | hold |
| `$0C` mid kick | fire + forward | `$04 $18 $05` | 12 | 0 | hold |
| `$0D` high kick | fire + up + forward | `$04 $1E $0B` | 13 | 0 | hold |
| `$0E` flying kick | fire + up | `$19 $04 $09 $0A $3A $09 $19` | 45 | +10 | stance |
| `$0F` roundhouse | fire + up + back | `$11 $22 $12` | 17 | 0 | hold |
| `$10` back sweep | fire + down + back, in a held crouch | `$34 $39` | 13 | -19 | hold |
| `$11` back kick | fire + back, after a held about turn | `$1C $1D $1F $24` | 20 | 0 | hold |
| `$12` about turn | fire + back, from the stance | `$1B` | 6 | 0 | hold |
| `$13` low block | back, against a low attack in range | `$23` | 2 | 0 | hold |
| `$14` high block | back, against a high attack in range | `$0E` | 2 | 0 | hold |
| `$15` return from the back kick | release of a held back kick | `$04 $18`, played backwards | 20 | 0 | hold |
| `$16` knock-down | hit reaction | `$29 $2A $2B $2C` | 119 | -28 | stance |
| `$17` bow at the start | the start of an exchange | `$1A $21 $1A` | 72 | -6 | stance |
| `$18` low punch | down + forward, not in a crouch | `$06 $13` | 7 | +6 | hold |

The column "End" is the value of [`move_return_flags` `$115B`](../src/entry_and_tables.asm#L9) for the move:

- **switch** (`$80`): a new request changes the move at once, in the middle of the script. Only the two walks have this value.
- **stance** (`$01`): the script always plays to its end, then the fighter returns to the stance.
- **hold** (`$00`): at the end, the fighter holds the end pose while the request stays the same. A new request plays the script backwards to its start (a *retract*).

The 11 attacks are `$06`, `$07`, `$0A-$11` and `$18`. They have a 1 in [`move_attack_flags` `$1174`](../src/entry_and_tables.asm#L15). [`move_counter_moves` `$118D`](../src/entry_and_tables.asm#L21) gives the move that answers each attack. The table below also gives the hit frame from `move_hit_frames` and the points from `move_score_values`. The reaction of the opponent comes from `hit_check`, for fighters that face each other. (**Code**)

| Attack | Hit frame | Answer | Points | Reaction of the opponent |
|---|---|---|---|---|
| `$06` high punch | `$07` | `$14` high block | 800 | `$16` |
| `$07` punch from the crouch | `$0D` | `$13` low block | 800 | `$1B` |
| `$0A` foot sweep | `$10` | `$05` jump | 400 | `$16` |
| `$0B` low kick | `$08` | `$13` low block | 200 | `$16` |
| `$0C` mid kick | `$05` | `$13` low block | 200 | `$1B` |
| `$0D` high kick | `$0B` | `$14` high block | 800 | `$16` |
| `$0E` flying kick | `$0A` | `$14` high block | 1000 | `$16` |
| `$0F` roundhouse | `$12` | `$14` high block | 800 | `$1A` |
| `$10` back sweep | `$39` | `$05` jump | 800 | `$1A` |
| `$11` back kick | `$24` | `$14` high block | 1000 | `$16` |
| `$18` low punch | `$13` | `$13` low block | 600 | `$1B` |

A player cannot block the two sweeps. `move_fix_input` makes no block against `$0A` and `$10`, so "back" stays a walk back. Only the AI uses their answer, the jump `$05`. (**Code**)

The hit reactions `$1A` and `$1B` are moves too, but they are outside the 25 entries of the tables. A read of `move_attack_flags` for them gets 0 from the next table, and the hit reaction path never reads `move_return_flags`. Thus the short tables have no effect (**Code**, **Conclusion**).

### Facts of the moves that a reader does not expect

- **A low attack from the stance starts with a crouch.** A request `$07`, `$0A` or `$10` in the stance gives the crouch `$04`. The attack starts only when the crouch holds its end pose, after 15 passes (0.3 second). (**Code**)
- **Down-forward gives two moves.** In a held crouch, it gives `$07`. In each other move, `move_fix_input` changes it to `$18`, a low punch with a step forward. (**Code**)
- **"Back" is a block only against an attack in progress.** The opponent must be in an attack move that does not retract and does not hold its end pose. `hit_range_test` must also say "in range". In each other case, "back" is a walk back. (**Code**)
- **A human fighter turns only through the back kick.** The about turn `$12` alone does not change `fighter_facing`. Only a back kick `$11` that retracts changes it: this happens when the player releases fire + back before the kick holds its end pose. After a held back kick, the move `$15` returns to the stance with the old facing. The AI changes `fighter_facing` itself ([ai.md](ai.md)). (**Code**)
- **A hit freezes the fighter before the fall.** During `knockdown_delay` passes, the move does not change and the pose holds. The bout set-up writes 8 to `knockdown_delay` for each exchange. Then the reaction starts and writes `$50` to `fighter_y`, so a fighter that is hit in the air falls from the floor line. (**Code**)
- **The bow at the start moves the fighters apart.** Script `$17` moves the fighter 7 units back, then 1 unit forward. Fighter 0 starts at x `$3E` and fighter 1 at x `$5A`, so after the bow they stand at `$38` and `$60`. (**Code**)

### The animation scripts

[`anim_script_table` `$7720`](../src/anim_scripts.asm#L6) has one word for each animation `$00-$1E`. The word points to the script. A script is a list of steps of 4 bytes: the delay in passes, the frame, dx and dy. dx and dy have a sign. The table has no length field. [`anim_setup` `$30DE`](../src/anim_step.asm#L123) takes the length from the low byte of the next word minus the low byte of this word. Entry `$1E` is only the end mark of script `$1D`. (**Code**)

The animations `$19-$1D` belong to no move of the joystick. `$19` is the bow after a won exchange (`start_bow_anim`). `$1A` and `$1B` are hit reactions. `$1C` and `$1D` show the bull of the unused bonus test. (**Code**)

`anim_setup` prepares an animation. It writes 0 to `anim_finished`, dx and dy, 1 to the delay, and the animation number to `anim_started`. For forward play, it writes `$FC` (-4) to `anim_step_offset`. For reverse play, it writes the length. Thus the first step of a forward play is at offset 0, and the first step of a reverse play is the last step. (**Code**)

[`anim_update` `$3026`](../src/anim_step.asm#L6) calls [`anim_step` `$3035`](../src/anim_step.asm#L17) in each pass while `anim_number` is not 0:

1. It decreases `anim_frame_delay`. While the delay is not 0, it only moves the fighter with the dx and dy of the current step.
2. At 0, it goes to the next step: offset +4 forward, or offset -4 in reverse play.
3. When forward play reaches the length, or reverse play is at offset 0, the script ends. The routine writes 0 to `anim_number` and 1 to `anim_finished`. The last frame stays on the screen.
4. Else it reads the 4 bytes of the new step, calls `shape_build` for the new frame, and moves the fighter.

dx and dy are speeds, not distances. [`anim_apply_move` `$30A0`](../src/anim_step.asm#L82) adds them in each pass of the step, also in the pass that loads the step. Thus a step moves the fighter by delay × dx units. The walk forward has its dx only in steps of 1 pass and moves 38 units (76 pixels) in 61 passes. (**Code**)

The routine adds dy to `fighter_y` and writes `fighter_y` × 2 to `sprite_y`. For dx, it adds when `fighter_facing` EOR `anim_reverse` is 0, and subtracts when it is 1. Thus dx is always "forward", and a reverse play moves the fighter back to its start. dy has no such change. A reverse play of a script with dy would move the fighter the wrong way. No script with dy plays backwards. Only moves with the end "hold" get `anim_reverse` = 1, and no script of these moves has a dy (**Code**). The bug thus has no effect (**Conclusion**).

### The X limits

After the new X is in the accumulator, [`anim_check_x_limits` `$30B5`](../src/anim_step.asm#L95) decides if it stores it. For a frame below `$3B`, it stores the new X only when it is in `$0C-$94`. Else `fighter_x` keeps its old value, and the frame still changes. Then the routine writes `fighter_x` × 2 to `sprite_x_lo`, and the carry to `sprite_x_msb`. (**Code**)

The test drops the full movement of the pass. It does not move the fighter to the limit. For example, the first step of the knock-down `$16` has dx -29 in one pass. Fighter 0 at x `$20` gets `$03`, which is below `$0C`, so the fighter stays at `$20` and loses all the knock-back. A movement below 0 gives a value in `$EF-$FF`, so the test also refuses it. (**Code**)

The frames `$3B` and higher have no X limits. Only the bull of the unused bonus test uses them, so the bull can run in from outside the limits. The test `tests/bull_test.json` starts this code from a stub and shows the bull. (**Observed**)

![The bull of the unused bonus test runs at the white fighter](images/bull_test_charge.png)

The bull of [`dev_bull_test` `$138F`](../src/dev_bull_test.asm#L42) in the run [bull_test.json](../tests/bull_test.json).

### The frames and the shape builder

A fighter is 3 × 3 sprites: 72 × 63 pixels, or 36 × 63 multicolour pixels. There are 72 frames, `$00-$47`. The frames `$00-$3A` are the fighter, `$3B-$42` the bull, and no script uses `$43-$47`. Frame `$3A` is a copy of frame `$0A` with other hit zones. The flying kick holds its kick with it after the hit frame `$0A`. (**Code**)

[`shape_build` `$316D`](../src/shape_build.asm#L37) builds the frame of a fighter. It does 4 things:

1. It changes `draw_buffer` to the other buffer of the fighter. There are 4 buffers of 9 sprites at `$C040`, `$C280`, `$C4C0` and `$C700`, two for each fighter.
2. For slot n (0-8), it reads part p from the frame part table n at [`frame_parts_top_left` `$7AE0`](../src/frame_part_tables.asm#L6) + n × `$48`. Slots 0-2 are the top row, from left to right. Part 0 is an empty slot with sprite pointer 0, the blank sprite at `$C000`.
3. It copies the 64 bytes of part p from `$8000` + p × 64. `shape_part_page_table` gives the page and `shape_part_lo` gives the low byte. For facing 1, [`shape_build_mirrored` `$33E7`](../src/shape_build_mirror.asm#L6) copies the columns in the other order, and each byte goes through `shape_mirror_table`, which reverses the four 2-bit pixels.
4. At the end, it copies the 9 new pointers to `fighter_part_ptrs`. The raster interrupt reads them at line 0, so the screen never shows a half-built frame.

The shape builder runs only when a new step starts. For 8 frames of the jumps and somersaults, it also selects 3 fixed shadow sprites for a fourth row on the floor. [graphics.md](graphics.md) and [interrupts.md](interrupts.md) explain the parts, the shadows and the sprite rows. (**Code**)

![The 255 fighter parts at $8040-$BFFF](reference/images/fighter_f02_parts-multicolour.png)

The fighter parts `$01-$FF` of M.SHAPES, in the pattern colours of the reference.

## The data

**The script table.** `anim_script_table` at `$7720`: 31 words, animation `$00-$1E`. Word 0 is `$0000` (no script). Word `$1E` points to the end of script `$1D`. The scripts are at `$775E-$79AD`. (**Code**)

**The step of a script**, 4 bytes:

| Byte | Name | Meaning |
|---|---|---|
| 0 | delay | Passes of the step, `$01-$FF`. |
| 1 | frame | The value for `fighter_frame`, `$00-$42`. |
| 2 | dx | Signed X speed in units per pass. "Forward" for a positive value. |
| 3 | dy | Signed Y speed per pass. Negative is up. The values are 0, ±2 and ±8. |

**The move tables**, one byte for each move `$00-$18`, in `entry_and_tables.asm`:

| Table | Address | Meaning |
|---|---|---|
| `move_return_flags` | `$115B` | End of the move: `$80` switch, `$01` stance, `$00` hold. |
| `move_attack_flags` | `$1174` | 1 for the 11 attacks. |
| `move_counter_moves` | `$118D` | The block or the jump that answers the attack. |
| `move_reach_types` | `$11A6` | Reach type: 1 for the attacks to the back `$0F` and `$10`. 21 bytes. |
| `move_full_reach` | `$11BB` | Reach of a full point. |
| `move_half_reach` | `$11D4` | Reach of a half point. |
| `move_hit_frames` | `$1202` | The frame of the attack that does the hit test. |
| `move_hit_zone_facing` | `$121B` | Words: the hit-zone table of the attack, fighters face each other. |
| `move_hit_zone_same_facing` | `$124D` | Words: the hit-zone table of the attack, fighters face the same way. |
| `move_score_values` | `$12A3` | Points of a full point, in hundreds. |

[combat.md](combat.md) explains the reach and the hit zones. (**Code**)

**The variables of a fighter** that this page uses (**Code**):

- `fighter_move`: the move. `fighter_input`: the request of this pass.
- `pose_held`: 1 while the end pose holds. `anim_reverse`: 1 during a retract.
- `anim_number` and `anim_started`: the animation.
- `fighter_frame` and `fighter_facing`: the pose and its side.
- `fighter_x`: `$0C-$94`. `fighter_y`: `$50` on the floor.

## The state machine of a move

[`move_update_state` `$22B7`](../src/fighter_moves.asm#L72) compares the request with the move in each pass. When they are the same, nothing changes. [`move_anim_end` `$2381`](../src/fighter_moves.asm#L206) makes the changes at the end of a script. The first diagram shows the moves. The second diagram shows the life of one move with the end "hold".

~~~mermaid
stateDiagram-v2
  state "Bow ($17)" as Bow
  state "Stance ($01)" as Stance
  state "Walk ($02, $03)" as Walk
  state "Crouch ($04)" as Crouch
  state "Low attack ($07, $0A, $10)" as Low
  state "Move to its end ($05, $08, $09, $0E)" as Auto
  state "Held move (attacks, blocks)" as Held
  state "About turn ($12)" as Turn
  state "Back kick ($11)" as Kick
  state "Return ($15)" as Ret
  state "Hit: frozen pose" as Frozen
  state "Fall ($16, $1A, $1B)" as Fall
  [*] --> Bow
  Bow --> Stance: script ends
  Stance --> Walk: forward or back
  Walk --> Stance: script ends
  Stance --> Crouch: down or a low attack
  Crouch --> Low: low attack, crouch held
  Crouch --> Stance: new request, retract ends
  Low --> Stance: retract, then crouch backwards
  Stance --> Auto: up, somersault, flying kick
  Auto --> Stance: script ends
  Stance --> Held: attack or block
  Held --> Stance: retract ends
  Stance --> Turn: fire + back
  Turn --> Kick: fire + back, turn held
  Kick --> Ret: new request, kick held
  Kick --> Stance: retract ends, facing changes
  Ret --> Stance: script ends
  Frozen --> Fall: delay is 0
  Fall --> [*]: script ends, exchange ends
~~~

Each state can go to "Hit: frozen pose" when the hit test of the opponent writes a hit reaction. The diagram does not show these lines. (**Code**)

~~~mermaid
stateDiagram-v2
  state "Running (forward)" as Run
  state "Holding the end pose (pose_held = 1)" as Hold
  state "Retracting (anim_reverse = 1)" as Retract
  [*] --> Run: new move
  Run --> Hold: script ends, request is the same
  Run --> Retract: new request
  Hold --> Retract: new request
  Retract --> [*]: offset 0, stance or crouch
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Any move | `fighter_input` is `$16`, `$1A` or `$1B`, `knockdown_delay` > 0 | Frozen pose: delay - 1, `pose_held` = 1 | `move_hit_delay` |
| Frozen pose | `knockdown_delay` = 0 | Move = reaction, `fighter_y` = `$50`, `anim_reverse` = 0 | `move_start_hit_reaction` |
| Fall `$16`, `$1A`, `$1B` | script ends | `bout_knockdown` = reaction, the exchange ends | `anim_end_clear` |
| Stance `$01` | request `$11` | About turn `$12` | `move_start_turn` |
| Stance `$01` | request `$07`, `$0A` or `$10` | Crouch `$04` | `move_crouch_first` |
| Stance `$01` | other new request | Move = request | `move_take_input` |
| Crouch `$04` | request `$07`, `$0A` or `$10`, `pose_held` = 1 | Move = request | `move_crouch_attack` |
| About turn `$12` | request `$07`, `$0A` or `$10` | Retract | `move_cancel_turn` |
| About turn `$12` | request `$11`, `pose_held` = 1 | Back kick `$11` | `move_check_turn` |
| Back kick `$11` | new request, `pose_held` = 1 | `$15` in reverse play | `move_check_back_kick` |
| Walk `$02`, `$03` | new request | Move = request (`$12` for `$11`) | `move_switch_walk` |
| End "hold" | new request | Retract: `anim_reverse` = 1 | `move_retract` |
| End "stance" | new request | No change, the script plays on | `move_clear_hold` |
| End "hold" | forward script ends | `pose_held` = 1 | `anim_end_hold` |
| End "stance" or "switch" | forward script ends | Stance `$01` | `anim_end_to_stand` |
| Back kick `$11` | retract ends | Stance `$01`, `fighter_facing` changes | `anim_end_after_retract` |
| `$07`, `$0A`, `$10` | retract ends | Crouch `$04` in reverse play | `anim_end_rise_crouch` |
| Other move | retract ends | Stance `$01` | `anim_end_stand` |

In a move other than the stance and the crouch, a low attack request does nothing: the move plays on. Only in the about turn does it cause a retract, and no run executed that path (`src/not_executed.json`, `$232D-$2331`). The walk branch for request `$11` (`$237C`) also has no coverage. (**Code**, **Observed**)

## The worked example: the jump

The jump is move and animation `$05`. Its word is entry 5 of [`anim_script_table` `$7720`](../src/anim_scripts.asm#L6), and its script is [`script_jump` `$780E`](../src/anim_scripts.asm#L68). These are the bytes of the source `anim_scripts.asm`:

| Address | Bytes | Meaning |
|---|---|---|
| `$772A` | `$0E $78` | Entry 5: the script is at `$780E`. |
| `$772C` | `$22 $78` | Entry 6: the next script is at `$7822`. The length is `$22` - `$0E` = `$14`, 20 bytes, 5 steps. |
| `$780E` | `$06 $19 $00 $00` | Step 0: 6 passes, frame `$19`, no movement. |
| `$7812` | `$01 $09 $00 $F8` | Step 1: 1 pass, frame `$09`, dy -8. |
| `$7816` | `$19 $09 $00 $00` | Step 2: 25 passes, frame `$09`, no movement. |
| `$781A` | `$01 $19 $00 $08` | Step 3: 1 pass, frame `$19`, dy +8. |
| `$781E` | `$06 $19 $00 $00` | Step 4: 6 passes, frame `$19`, no movement. |

The passes of the jump, from the pass with the request "up" (**Code**):

1. **Pass 1.** The stance changes to move `$05`. `move_start_anim` sees a new move and writes 0 to `anim_started`. `anim_setup` writes offset `$FC`, delay 1 and length `$14`. `anim_step` decreases the delay to 0, adds 4 to the offset, and loads step 0 at offset 0. `shape_build` draws frame `$19`.
2. **Passes 2-6.** The delay counts from 6 to 1. Frame `$19` stays, and dx and dy are 0.
3. **Pass 7.** Step 1 loads: frame `$09`. dy -8 changes `fighter_y` from `$50` to `$48`, and `sprite_y` from `$A0` to `$90`. The fighter is now 16 raster lines above the floor. Frame `$09` is in `shape_row4_frames`, so the fighter gets a shadow on the floor.
4. **Passes 8-32.** Step 2 holds frame `$09` in the air for 25 passes.
5. **Pass 33.** Step 3 loads frame `$19`, and dy +8 returns `fighter_y` to `$50`.
6. **Passes 34-39.** Step 4 shows frame `$19` on the floor.
7. **Pass 40.** The delay is 0, and the offset `$14` is the length. `anim_step` ends the script. In the same pass, `move_anim_end` reads `$01` from `move_return_flags` for move `$05` and changes the move to the stance `$01`.

The jump takes 40 passes, 0.8 second, and the fighter is in the air for 26 passes. When the player holds "up", pass 41 starts the next jump at once. The jump is never retracted, because its end is "stance". (**Code**)

## Still open

- The distance of the somersaults. The code adds dx in each pass of a step, so `$08` moves 39 units back and `$09` 39 units forward. The comments of the knowledge at `script_down_back` and `script_up_back` say 5 units, which is the sum of the dx bytes. A run that reads `fighter_x` before and after move `$08` in [one_player_moves.json](../tests/record/one_player_moves.json) can decide this.
- What the player sees at the end of a back kick. Does a released back kick show a turn, and does a held one show the old facing? A run that holds fire + back for 30 passes, then for 10 passes, with a screen capture after each, can show it.
- The priority test with `$D01E`. Does the read for fighter 0 always get 0 when the sprites overlap? A run with a read watchpoint on `$D01E` at `fighter_update` for X = 0 and X = 1 can show it.
- The about turn cancel (`$232D`) and the walk to the about turn (`$237C`). A run with fire + down during the about turn, and with fire + back during a walk, can execute them.
