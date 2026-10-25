# The fighters (game_v1)

This page explains how the two barbarians move and how the program draws them in Part 2, build V 05 05 87. The joystick or the computer gives a direction for each fighter. A table of rows changes the direction into a *move*. Each move plays a list of *poses*, one pose in each pass of the main loop. The program builds each pose from 9 body pieces, draws it into a work bitmap, and adds a few hardware sprites. The page also tells how a fighter moves on the floor and how the two fighters turn after they pass each other. The last part is the idle move of a player who does nothing.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of `main_loop`. The loop has no frame wait. A pass takes about 10 frames in the attract recording (**Observed**). A *frame* is one raster interrupt at line `$FA`, 50 times each second on a PAL C64.
- Fighter 0 is player 1 (joystick port 2). Fighter 1 is the computer opponent. A variable of a fighter is a pair of bytes: +0 for fighter 0, +1 for fighter 1.
- *Facing* 0: the fighter looks to the right. *Facing* 1: the fighter looks to the left. *Forward* is the side that the fighter looks to. *Back* is the other side.
- A *column* is one unit of `fighter_x`: one bitmap cell, 8 hires pixels or 4 multicolour pixels. `fighter_x` is the left column of the fighter image.
- A *move* is a value of `fighter_move`. The program keeps bit 7 set, so move `$04` is the value `$84`. This page writes the move number without bit 7, except where the code compares the full value.
- A *sequence* is the list of pose numbers of a move. A *pose* is a value of `fighter_pose`: the number of a pose record.
- A *piece* is one 64-byte block of `fighter_pieces`, in sprite format. A *sprite part* is one hardware sprite that a pose record adds to the bitmap image.
- A *locked* move ignores the joystick and the computer until its last pose.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The main loop does the work of the fighters in a fixed order. The input comes first, then the drawing, then the checks. [`main_loop` `$80BB`](../src/main/main_loop.asm#L6) calls these routines in each pass (**Code**):

~~~mermaid
flowchart TB
  A["Joystick of player 1 (read_joysticks)"] --> C["Select the move (find_move_row, start_new_move)"]
  B["Computer opponent (ai_choose_moves)"] --> C
  C --> D["Erase the fighters: copy the background (restore_work_bitmap)"]
  D --> E["Next pose of each fighter (animate_fighters)"]
  E --> F["Build the pose image and draw it (build_pose_image, draw_fighter)"]
  F --> G["Set the sprite parts (draw_fighter_sprites)"]
  G --> H["Show the work bitmap (show_work_bitmap)"]
  H --> I["Turn after a pass (check_turn_around)"]
  I --> J["Idle move of player 1 (check_player_idle)"]
~~~

1. **The input.** [`read_joysticks` `$860F`](../src/input/joystick.asm#L6) reads the joystick of each human fighter. `ai_choose_moves` gives a joystick value to each computer fighter ([ai.md](ai.md)). Both paths then use the same routines to select the next move. (**Code**)
2. **The erase.** `restore_work_bitmap` copies the saved background of the fight area into the work bitmap. This erases the fighters of the last pass. (**Code**)
3. **The poses.** [`animate_fighters` `$893A`](../src/fighter/animate.asm#L6) steps the sequence of each fighter by one pose. For each new pose, it builds the image, moves the fighter and draws the image into the work bitmap. (**Code**)
4. **The sprite parts.** `draw_fighter_sprites` sets the hardware sprites of both poses. (**Code**)
5. **The screen.** `show_work_bitmap` copies the work bitmap to the screen bitmap. The fighters thus come to the screen in one copy, not piece by piece. (**Code**, **Conclusion**)
6. **The checks.** `check_turn_around` starts the turn of both fighters after they pass each other. `check_hits` finds the hits ([combat.md](combat.md)). `check_player_idle` starts the idle move. (**Code**)

The hit test runs after the drawing, so a hit changes the move in the next pass. Each step of a sequence shows one pose for one pass. A sequence of 4 poses thus takes 4 passes, about 0.8 second (**Code**, **Conclusion** from the pass time).

### The joystick

[`read_joystick` `$861C`](../src/input/joystick.asm#L17) reads `$DC00` (port 2) for fighter 0 and `$DC01` (port 1) for fighter 1. It inverts the bits, so a 1 bit is a closed contact. It keeps bits 0-4: up, down, left, right and fire. (**Code**)

The routine reads no joystick in these cases (**Code**):

- During the demo, the walk-in, the time-out, the set-up, the turn, and after a fighter loses (`bout_loser` bit 7).
- While the fighter does the death move `$1B`, the decapitation move `$08` or the winner move `$13`. These values are in `moves_no_control`.

`read_joysticks` reads the fighters from `two_players` down to 0. Part 2 always writes 0 to `two_players`, so the program reads only port 2. The code for port 1 stays, but it never runs in Part 2 (**Code**). [../../docs/development.md](../../docs/development.md) tells why Part 1 and Part 2 share this code.

[`joystick_to_direction` `$8655`](../src/input/joystick.asm#L48) stores the 5 bits in `fighter_input`. Then it finds the direction among 9 values. The list for facing 0 is `joystick_dirs_0`. The list for facing 1, `joystick_dirs_1`, gives left and right in the other order. Thus index 1 is always "forward" (**Code**):

| Index | Direction | Facing 0 | Facing 1 |
|---|---|---|---|
| 0 | none | `$00` | `$00` |
| 1 | forward | `$08` right | `$04` left |
| 2 | back | `$04` left | `$08` right |
| 3 | down | `$02` | `$02` |
| 4 | up | `$01` | `$01` |
| 5 | down + forward | `$0A` | `$06` |
| 6 | up + forward | `$09` | `$05` |
| 7 | down + back | `$06` | `$0A` |
| 8 | up + back | `$05` | `$09` |

The computer always uses the list for facing 0. Its joystick values are thus "forward" and "back" values, not "left" and "right" values (**Code**).

A value outside the list, for example up and down together, gives index `$FF`. `start_new_move` then reads the byte 255 bytes after the start of the row. A normal joystick cannot close two opposite contacts, and each computer value is in the list. Thus this case does not occur (**Code**, **Conclusion**).

### The move selection rows

[`find_move_row` `$8663`](../src/input/joystick.asm#L60) selects a row of 9 next moves. `move_rows_no_fire` gives the row number for each move without fire. `move_rows_fire` gives it with fire. The rows are in [`move_select_rows` `$CE3A`](../src/input/move_select.asm#L27), 9 bytes each. The direction index selects the byte in the row. (**Code**)

The table gives each row with its moves, as the values of the bytes. A value with bit 7 set starts a locked move (**Code**):

| Row | Used in moves | none | fwd | back | down | up | down-fwd | up-fwd | down-back | up-back |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | most moves, no fire | `$00` | `$01` | `$02` | `$97` | `$84` | `$91` | `$8A` | `$92` | `$90` |
| 1 | `$05`, `$06`, no fire | `$94` | `$94` | `$94` | `$86` | `$94` | `$91` | `$94` | `$92` | `$94` |
| 2 | `$07`, `$09`, no fire | as row 0 | | | | | | | | |
| 3 | `$08`, `$0D`, `$12-$15`, `$1A`, `$1B`, no fire | `$00` | `$01` | `$02` | `$86` | `$84` | `$91` | `$8A` | `$92` | `$90` |
| 4 | `$0A`, no fire | `$96` | `$01` | `$02` | `$97` | `$84` | `$91` | `$8A` | `$92` | `$90` |
| 5 | `$11`, with or without fire | `$98` | `$98` | `$98` | `$86` | `$98` | `$98` | `$98` | `$98` | `$98` |
| 6 | `$17`, no fire | `$86` for each direction | | | | | | | | |
| 7 | `$18`, no fire | `$00` | `$01` | `$02` | `$00` | `$84` | `$00` | `$8A` | `$92` | `$90` |
| 8 | most moves, with fire | `$00` | `$89` | `$87` | `$97` | `$8B` | `$8C` | `$8F` | `$8E` | `$83` |
| 9 | `$05`, `$06`, with fire | `$94` | `$94` | `$94` | `$85` | `$94` | `$94` | `$94` | `$94` | `$94` |
| 10 | `$17`, with fire | `$85` for each direction | | | | | | | | |
| 11 | `$18`, with fire | `$00` | `$89` | `$87` | `$97` | `$8B` | `$8C` | `$8F` | `$8E` | `$00` |

The rows make some moves depend on the move before them (**Code**):

- **Down starts with a step.** From the stance, "down" gives move `$17`, one locked pose. In the next pass, each input without fire gives the crouch `$06`, and each input with fire gives the low thrust `$05`.
- **The crouch holds.** In `$05` or `$06`, "down" keeps the crouch, and fire + down gives `$05` again. The rolls start from the crouch too. Each other input gives `$14`, one pose that rises from the crouch.
- **A roll ends low.** After the forward roll `$11`, each input except "down" gives `$18`, a pose that rises from the roll.
- **Fire alone is the stance.** Fire with no direction gives move `$00` in rows 8 and 11.

[`start_new_move` `$868D`](../src/input/joystick.asm#L84) starts the new move only when the current move is not locked and the new move is different. It writes the full row byte to `fighter_move_lock`, so bit 7 of the byte locks the new move. It also writes the first pose of the new sequence to `fighter_pose`. (**Code**)

### The moves

The code has 30 moves, `$00-$1D`. [`move_seq_ptrs` `$BC87`](../src/fighter/move_sequences.asm#L6) has one pointer for each move. The column "Start" comes from the rows above and from the code that writes `fighter_move`. The column "Attack poses" comes from `attack_poses` of the hit test. The names of the attacks are a **Conclusion** from the images of the poses. The other facts are **Code**.

| Move | Start | Sequence (poses) | Command | Attack poses | What the poses show |
|---|---|---|---|---|---|
| `$00` | none, fire alone | `$00` | loop | | stance |
| `$01` | forward | `$01 $02 $03 $33` | loop | | walk forward |
| `$02` | back | `$37 $36 $35 $34` | loop | | walk back |
| `$03` | fire + up-back | `$04 $05 $06 $07` | loop | `$05`, `$07` | low sword swing |
| `$04` | up | `$08 $09 $38 $00` | loop | | jump |
| `$05` | fire, in the crouch | `$0A $0B $0C $5A $39` | loop | `$0C` | low thrust from the crouch |
| `$06` | after `$17`, or down in the crouch | `$3A` | loop | | crouch |
| `$07` | fire + back | `$0E $0F $10 $19 $1A $45 $19` | loop | `$1A` | sword round the head, then a cut at neck height |
| `$08` | hit reaction | `$11 $11 $11 $12 $12 $12 $13 $14` | hold | | body without a head falls |
| `$09` | fire + forward | `$55 $16 $17 $3D $44` | loop | `$17` | thrust at body height |
| `$0A` | up + forward | `$3F $18` | hold | | sword high: a guard |
| `$0B` | fire + up | `$41 $42 $43 $45 $3C` | loop | `$43` | thrust at head height |
| `$0C` | fire + down-forward | `$1B $1C $46 $00` | loop | `$1C` | kick |
| `$0D` | hit reaction | `$1D $1E $00` | loop | | staggers back |
| `$0E` | fire + down-back | `$58 $1F $20 $49 $48` | loop | `$20` | sword swing |
| `$0F` | fire + up-forward | `$32 $22 $4A` | loop | `$22` | overhead cut |
| `$10` | up + back | `$50 $4B $51` | hold | | sword in front: a guard |
| `$11` | down + forward | `$23 $24 $25 $26` | loop | `$24`, `$25`, `$26` | forward roll |
| `$12` | down + back | `$29 $2B $2C $2D` | loop | | back roll |
| `$13` | the winner, bout end | `$3C $00 $2F $2F $30 $31`×5 `$30 $2F $2F` | hold | | turns to the player and raises a fist |
| `$14` | other input in the crouch | `$3B` | loop | | rises from the crouch |
| `$15` | no code starts it | `$3E` | loop | | (not used) |
| `$16` | no input after `$0A` | `$40` | loop | | lowers the guard |
| `$17` | down, from the stance | `$0D` | loop | | step into the crouch |
| `$18` | input after `$11` | `$28` | loop | | rises after the roll |
| `$19` | hit reaction | `$4C $4D $4E $4F` | loop | | falls back, lies, gets up |
| `$1A` | idle timer 0 | `$52 $53 $54 $53 $54 $53 $54` | next move `$00` | | idle: looks at the player |
| `$1B` | energy 0 | `$0D $56 $56 $56 $57 $21 $59` | hold | | death fall |
| `$1C` | the winner, near a loser | `$1B $1C $46 $00` | next move `$13` | | kick, then the winner move |
| `$1D` | after a pass, or the winner at bout end | `$0E $0F $10` | next move `$00` | | turn |

Only move `$07` decapitates. The hit records of its attack pose `$1A` give the reaction `$88` ([combat.md](combat.md)). The turn `$1D` starts with the same three poses as move `$07` (**Code**).

Nothing starts move `$15`. No row, hit record or routine writes `$95` to `fighter_move`. Its pose `$3E` uses the same record as pose `$0D` (**Code**). Thus the move is a leftover (**Conclusion**).

### The move sequences

[`animate_fighter` `$8963`](../src/fighter/animate.asm#L32) reads the byte at `fighter_move_step` in the sequence. A byte below `$FF` is a pose number. The routine stores it in `fighter_pose` and adds 1 to the step. When the next byte is `$FF`, this pose is the last one, and the routine clears `fighter_move_lock`. Thus a locked move becomes free when it shows its last pose. (**Code**)

After the last pose, `$FF` and a command byte follow (**Code**):

| Command | Effect | Used in |
|---|---|---|
| 0 | Start the sequence again (loop). | most moves |
| 1 | Write 1 to `fighter_move` and stop. | no sequence |
| 2 | Go to the step in the next byte. | no sequence |
| 3 | Start the move in the next byte. Move `$1D` also changes the facing. | `$1A`, `$1C`, `$1D` |
| 4 or more | Show the last pose again (hold). | `$08`, `$0A`, `$10`, `$13`, `$1B` |

No run executed the commands 1 and 2 (**Observed**, the coverage of the recordings). Command 1 writes `$01` without bit 7, so the next joystick test always sees a different move (**Code**).

A loop repeats a held attack. The lock clears at the last pose, but the row gives the same move for the same input. Thus `start_new_move` does not start it again, and command 0 plays it from the first pose (**Code**). A hold keeps the last pose until the input changes the move. The death, the decapitation and the winner move also hold, and `moves_no_control` stops the joystick for them (**Code**).

`animate_fighters` animates fighter 1 first and fighter 0 second, so fighter 0 is in front. When fighter 1 does one of the moves in `moves_fighter0_first` (`$1B`, `$08`, `$0B`, `$07`), fighter 0 goes first, so fighter 1 is in front. In the final stage, only fighter 0 moves. During the set-up, nothing moves. (**Code**)

At 7 pairs of move and step, the routine also requests the sound of a sword swing ([sound.md](sound.md)) (**Code**).

### The idle move

[`check_player_idle` `$86C2`](../src/input/idle.asm#L6) looks at each human fighter outside the demo. When the joystick gives no direction and no fire, it waits for `fighter_idle_timer` to reach 0. Then it starts move `$1A`. Each input, and the start of the idle move, writes `$FF` to the timer again. (**Code**)

The interrupt decreases the timer once a frame in `count_down_timers`. Thus the player stands still for 255 frames, about 5.1 seconds, before the idle move starts. The move repeats every 5.1 seconds while the player does nothing. (**Code**)

The idle move is not locked, so each direction ends it at once. `start_new_move` has one special case for it: while the move is `$9A` and the direction is "none", the move continues. Without this case, row 3 would give the stance at once. The poses `$52-$54` change only the upper body: the fighter turns to the player. At the end, command 3 starts the stance `$00`. (**Code**, the description of the poses is a **Conclusion**)

### The pose records and the composition buffer

[`pose_ptrs` `$BD80`](../src/fighter/poses.asm#L6) has one pointer for each pose `$00-$5A`. The 91 poses use 71 different records. For example, poses `$39` and `$3A` use the record of pose `$0B`. (**Code**)

A fighter image is a grid of 3 × 3 pieces. Each piece has the sprite format: 21 lines of 3 bytes, in multicolour. Thus the image is 9 bytes wide and 63 lines high, 36 × 63 multicolour pixels. [`fighter_pieces` `$0840`](../src/graphics/fighter_pieces.asm#L9) holds the pieces `$01-$EF` at `$0800` + 64 × number. Piece 0 means an empty place in the grid. (**Code**)

![The fighter pieces $01-$EF](reference/images/fighter_pieces-multicolour.png)

The 239 fighter pieces at `$0840-$43FF`, in the pattern colours of the reference.

[`build_pose_image` `$8A2C`](../src/fighter/pose_image.asm#L17) makes the image of a pose in the composition buffer at `$05CA-$0800`. The buffer is in the screen RAM of the C64 at power-on. The game shows its screen at `$4400`, so this area is free. (**Code**)

1. `clear_pose_buffer` writes 0 to the full buffer.
2. For each of the 9 places, the routine reads the piece number from bytes 0-8 of the pose record. `part_dest_ptrs` gives the start of the place in the buffer. `part_byte_offsets` gives the buffer offset of each of the 63 bytes.
3. It copies only the bytes that are not 0. Thus two pieces can share the bytes at their edges.
4. When the fighter has facing 1, `mirror_pose_buffer` mirrors the image. It reverses the 9 bytes of each line and changes each byte through `mirror_table`. That table reverses the order of the 4 pixel pairs of a byte.

The program builds `mirror_table` and `mask_table` at the start with `build_mirror_table` and `build_mask_table`. A bitmap image thus needs no second copy for the other facing. (**Code**)

### Drawing into the work bitmap

The fight area of the screen is the character rows 14-21 of the bitmap. The work bitmap at [`work_bitmap` `$A678`](../src/data/work_bitmap.asm#L6) is a copy of these 8 rows, 320 bytes each. `save_fight_background` keeps the background without fighters at `$B098` for the erase. (**Code**)

[`draw_fighter` `$8B59`](../src/fighter/draw.asm#L6) copies the composition buffer into the work bitmap at the column `fighter_x`. Each byte of the buffer fills one cell column of one bitmap line. `mask_table` gives `%11` for each pixel pair `%00`, so the background stays where the fighter has no pixel. (**Code**)

```
mask = mask_table[b]            ; %11 where the pixel pair of b is %00
work = (work AND mask) OR b
```

Three facts of the drawing (**Code**):

- **The last line is not drawn.** The loop stops after 62 lines (`draw_row` < `$3E`). Line 62 of the buffer never reaches the screen. A run with a pose that has pixels in that line can show it (see **Still open**).
- **The edges are hidden.** `restore_work_bitmap` and `show_work_bitmap` copy only 256 bytes of each row, the columns 4-35. A fighter in the columns 0-3 or 36-39 is in the work bitmap, but not on the screen. The fighters start the walk-in at the columns 0 and `$1F`, thus partly out of view (**Conclusion**).
- **The loser can leave the screen.** After a fighter loses, `draw_fighter_clip` draws only the columns below 40. The goblin can thus drag the body past the right edge without a wrap into the next row (**Conclusion**, [combat.md](combat.md)).

### The sprite parts

The work bitmap is only 64 lines high. A jump or a raised sword goes higher than the fight area. The pose records thus add hardware sprites: [`draw_fighter_sprites` `$8FCC`](../src/sprites/fighter_sprites.asm#L6) sets them in each pass, fighter 1 first, from sprite 7 down. It switches off each lower sprite that has no animation of its own. (**Code**)

A pose record has 0 to 3 sprite parts of 4 bytes: shape, colour, Y position and X offset. There are two kinds (**Code**):

- **The torso of the opponent.** The first sprite part of each pose has a shape of `$33` or more. Its pointer is `$53-$7F`, the frames of `sprite_frames_mirrored`. Bit 7 of its colour byte is 0, so the sprite is single colour, in `fighter_colours` of `opponent_index`. Its Y position is near `$B0`. In a picture made from the bytes, the sprite covers the chest of the fighter (**Conclusion**).
- **The parts above the fight area.** The poses `$08`, `$09`, `$0E-$10`, `$1F`, `$31`, `$38` and `$48` have more sprite parts. They have a shape below `$33`, colour `$8C` (multicolour, grey) and Y position `$8D`. The fight area starts at sprite Y `$A2`, so such a sprite covers the 21 lines above it (**Conclusion**). For facing 1, `set_fighter_sprite` adds `$0D` to the pointer, the mirrored copy.

For fighter 0, the routine skips the first sprite part when its shape is `$33` or more. Each pose with sprite parts has such a first part. Thus player 1 never shows the torso sprite, and only the opponent has a colour of its level (**Code**). The 8 colours for the opponents 0-7 are purple, green, orange, blue, cyan, red, brown and black (**Code**).

![The torso frames $53-$7F](reference/images/sprite_frames_mirrored-hires.png)

The 45 shared torso frames at `$54C0-$5FFF`, in hires pattern colours.

`set_sprite_x` gives the X position: column × 8 + offset + `$18`. For facing 1, the offset is `$30` minus the offset of the record. A fighter at column `$1E` or more gets no sprite parts. (**Code**)

The torso frames have only one copy. When fighter 1 turns, `mirror_shared_sprites` mirrors all 45 frames in place, in the next pass (**Code**). After each bout, [`end_bout_reset` `$842A`](../src/combat/end_of_bout.asm#L37) writes facing 1 for fighter 1. When fighter 1 lost and the frames show the mirror image, it does EOR `#$81` on `sprite_mirror_state`. This requests the mirror back. `quit_to_demo` also mirrors the frames back (**Code**). One case stays: in the demo, fighter 0 loses while fighter 1 faces right. Then fighter 1 starts the next bout with facing 1 and mirrored torso frames (**Conclusion**, see **Still open**).

### Movement on the floor

The sequence does not hold the movement. Each pose record holds it in byte 9 (direction bits) and byte 10 (step in columns). [`move_fighter` `$8AA7`](../src/fighter/move.asm#L6) moves the fighter when the pose starts. For facing 1, `facing_step_mask` changes bits 2 and 3 with `EOR #$0C`, so the bits are always "forward" and "back" for facing 0. (**Code**)

| Bit | Facing 0 | Facing 1 |
|---|---|---|
| 3 | X increases (forward) | X decreases (forward) |
| 2 | X decreases (back) | X increases (back) |

Examples: each walk pose moves 1 column, so a walk cycle of 4 poses moves 4 columns. The forward roll moves 1 + 4 + 2 + 4 = 11 columns forward. The back roll moves 1 + 3 + 5 + 2 = 11 columns back. The jump has no movement. (**Code**)

`step_fighter_left` and `step_fighter_right` limit the column (**Code**):

| Facing | Forward limit | Back limit |
|---|---|---|
| 0 (right) | column `$1F` | column 3 |
| 1 (left) | column 0 | column `$1C` |

Thus a fighter can walk forward to the edge of the work bitmap. When it walks back, it stops 3 columns from the edge (**Code**).

After each step, [`get_fighter_gap` `$8B24`](../src/fighter/move.asm#L82) calculates the gap from the facing of fighter 0. A negative gap means that the fighters passed each other. Then `move_fighter` moves the fighter back by the gap, so the fighters stop at gap 0. (**Code**)

### The turn

One case lets the fighters pass. When a fighter rolls forward (`$91`) and the other fighter jumps (`$84`), `get_fighter_gap` writes `$84` to `turn_request`. The routine then does not move the roller back, and the roller goes under the jumper. (**Code**)

[`check_turn_around` `$90B3`](../src/combat/turn_around.asm#L6) waits for the jumper to show pose `$00`, the last pose of the jump. Then it starts the turn `$1D` for both fighters. While bit 7 of `turn_request` is 1, no joystick and no computer input changes a move. (**Code**)

At the end of the turn, command 3 changes `fighter_facing` and writes it to `turn_request`, which clears bit 7. It adds `turn_column_adjust` to the column: +3 for the new facing 0, -3 for the new facing 1. The image of a pose is not in the middle of its 9 columns, and this correction keeps the body in place (**Code**, **Conclusion**). When fighter 1 turns, the routine sets bit 7 of `sprite_mirror_state` for the torso frames (**Code**).

## The data

**The sequence of a move**: pose numbers, then `$FF`, then a command byte, and for commands 2 and 3 one more byte. `move_seq_ptrs` at `$BC87` has 30 words. (**Code**)

**The pose record**, 12 bytes and 4 bytes for each sprite part (**Code**):

| Byte | Meaning |
|---|---|
| 0-8 | Piece numbers of the 3 × 3 grid, top row first, left to right. 0 is no piece. |
| 9 | Direction bits: bit 3 forward, bit 2 back (facing 0). 0 is no movement. |
| 10 | Step in columns. |
| 11 | Number of sprite parts, 0-3. |
| 12 + 4n | Shape: sprite pointer minus `$20`. Below `$33`, facing 1 adds `$0D`. |
| 13 + 4n | Colour. Bit 7 set: multicolour, colour in bits 0-3. Bit 7 clear: single colour from `fighter_colours`. |
| 14 + 4n | Y position of the sprite. |
| 15 + 4n | X offset in hires pixels from the left of the image, for facing 0. |

**The variables of a fighter** that this page uses (**Code**):

- `fighter_move`: the move, bit 7 set. `fighter_move_lock`: bit 7 is 1 for a locked move.
- `fighter_move_step`: the index in the sequence. `fighter_pose`: the pose of this pass.
- `fighter_input`: the 5 joystick bits of this pass, 1 = closed.
- `fighter_x`: the left column, 0-`$1F`. `fighter_facing`: 0 or 1.
- `fighter_idle_timer`: frames until the idle move.

**The buffers** (**Code**):

| Range | Use |
|---|---|
| `$05CA-$0800` | Composition buffer: 63 lines of 9 bytes. |
| `$A678-$B077` | Work bitmap: 8 rows of 320 bytes, the columns 4-35 shown. |
| `$B078-$BA77` | Saved background: 8 rows of 320 bytes. The game uses only columns 4-35, 256 bytes in each row at `$B098-$BA57`. |
| `$02AA-$03A9` | `mirror_table`. |
| `$03AA-$04A9` | `mask_table`. |

## The state machine of a move

`start_new_move` changes the move. It refuses to change a locked move. [`animate_fighter_command` `$89C1`](../src/fighter/animate.asm#L83) acts at the end of a sequence.

~~~mermaid
stateDiagram-v2
  state "Free move (stance, walk, idle)" as Free
  state "Locked move: plays its poses" as Locked
  state "Last pose: lock clear" as Last
  state "Holding the last pose" as Hold
  state "No control (death, decapitation, winner)" as NoCtl
  [*] --> Free
  Free --> Locked: new input, row byte with bit 7
  Free --> Free: new input, row byte without bit 7
  Locked --> Last: next byte is $FF
  Last --> Locked: same input, command 0 loops
  Last --> Free: new input
  Last --> Hold: command 4 or more
  Hold --> Free: new input
  Locked --> NoCtl: hit, energy 0 or bout end
  NoCtl --> [*]: bout ends
~~~

A hit can start a reaction move in each state. The diagram does not show these lines (**Code**).

| State | Condition | Next state | Code |
|---|---|---|---|
| Free | input gives a different row byte | the new move, locked when bit 7 | `start_new_move` |
| Idle `$1A` | direction "none" | no change | `start_new_move` |
| Locked | the next sequence byte is `$FF` | lock clear | `animate_fighter` |
| Last pose | command 0 | first pose of the same move | `animate_fighter_command` |
| Last pose | command 3 | the move in the next byte | `animate_fighter_next_move` |
| Last pose | command 4 or more | last pose again | `animate_fighter_hold` |
| Any | the hit record gives a reaction | reaction move, locked | `check_attack_hit` |
| Any | energy 0 | `$1B`, loser set | `apply_hit_damage` |
| Turn request | jumper shows pose `$00` | `$1D` for both fighters | `check_turn_around` |
| Idle timer 0 | no input | `$1A` | `check_player_idle` |

## The worked example: a walk pose of the opponent

Fighter 1 faces left at column `$14` and walks forward. Its sequence `$01` shows pose `$01`. These are the bytes of `pose_01` at `$BE46` (**Code**):

| Bytes | Meaning |
|---|---|
| `$01 $02 $00` | Top row: pieces `$01` and `$02`, the right place is empty. |
| `$07 $08 $00` | Middle row: pieces `$07` and `$08`. |
| `$09 $0A $00` | Bottom row: pieces `$09` and `$0A`. |
| `$08` | Direction bits: bit 3, forward. |
| `$01` | Step: 1 column. |
| `$01` | One sprite part. |
| `$33 $02 $B0 $0E` | Shape `$33`, colour byte `$02`, Y `$B0`, X offset `$0E`. |

The program does these steps in one pass (**Code**):

1. `animate_fighter` reads pose `$01` and takes the record from entry 1 of `pose_ptrs`.
2. `build_pose_image` copies piece `$07` from `$0800` + 64 × 7 = `$09C0` to place 3, at `$0687` in the buffer. It copies the other pieces in the same way.
3. The fighter has facing 1, so `mirror_pose_buffer` mirrors the 63 lines. The empty right column of pieces becomes the left column.
4. `move_fighter` changes the direction bits: `$08` EOR `$0C` = `$04`, bit 2. With facing 1, bit 2 means "X decreases", so the fighter goes to column `$13`. The gap check follows.
5. `draw_fighter` draws the buffer at column `$13`: the work bitmap address is `$A678` + 8 × `$13` = `$A710`.
6. `draw_fighter_sprites` takes the sprite part. The pointer is `$33` + `$20` = `$53`, so the facing adds nothing. Bit 7 of the colour byte is 0, so the colour is `fighter_colours` for the opponent, for example `$04` (purple) for opponent 0.
7. `set_sprite_x` mirrors the offset: `$30` - `$0E` = `$22`. The X position is `$13` × 8 + `$22` + `$18` = `$98` + `$3A` = `$D2`. The Y position is `$B0`.

For fighter 0 with the same pose, `draw_fighter_sprites` skips the sprite part, because the shape is `$33` and the record has only one part (**Code**).

## Still open

- Does line 62 of a pose ever have pixels? A script that reads the pieces of the bottom row of each pose record can tell it. A screen capture of such a pose can show the missing line.
- The torso frames after a demo bout that fighter 0 loses while fighter 1 faces right. A watchpoint on `sprite_mirror_state` during the attract recording can find such a bout. A screen capture of the next bout shows the torso sprite.
- The pass time in a bout. The 10 frames come from the attract recording. A run that counts the passes of `main_loop` during the fight recording can give the time of one pose in a bout.
- Does the computer ever roll under a jump? A run with a watchpoint on `turn_request` during the attract recording can show it.
