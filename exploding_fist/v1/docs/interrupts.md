# The interrupt chain (version I)

Each frame, a chain of raster interrupts splits the screen and multiplies the sprites. The top five text rows show the score panel, and the rest of the screen shows the scene bitmap. Each fighter is a block of 3 x 3 multicolour sprites, but the VIC-II has only 8 sprites. Thus the game shows each fighter with 3 sprites and moves them down two times in each frame. An NMI from CIA 2 changes the background colour to yellow for the floor. The last interrupt of the frame calls the music driver.

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one PAL frame, 312 raster lines of 63 cycles. The chain uses only the lines `$00-$FF`.
- A *handler* is one raster IRQ routine of the chain. Each handler writes the raster line and the address of the next handler.
- *Group A* is sprites 0-2 and *group B* is sprites 3-5. Group A shows `front_fighter`. Sprites 0-2 have priority over sprites 3-5, so the front fighter is in front.
- A *row* is one row of 3 sprites of a fighter. Row 1 is at Y, row 2 at Y+`$15` and row 3 at Y+`$2A`. *Row 4* is the floor shadow of a fighter in the air, at Y `$DA`.
- *Y* is the sprite Y of a group (`group_y`). `$A0` is the Y of a fighter on the ground.
- The *gap* is the difference between the Y of group A and the Y of group B.
- A *layout* is one of the 7 orders of the row handlers.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The chain starts again at line 0 of each frame. The frame-start handler does most of the work. It plans the sprite rows of the frame and writes the values into the operands of the later handlers. The later handlers are short. Each one loads its immediate operands, writes them to the VIC and continues the chain.

~~~mermaid
flowchart TB
  S["Line $00: plan the frame, show sprite row 1 (irq_frame_start)"]
  B["Line $5A: bitmap on, scene colour, start CIA2 timer B (irq_bitmap_on)"]
  R2["Row 2 handlers: line Y+$14 of each group"]
  R3["Row 3 handlers: line Y+$29 of each group"]
  N["About line $B8: yellow floor colour (nmi_floor_colour)"]
  R4["Line $D9: shadow row or nothing (row4_irq_vector)"]
  E["Line $FF: text mode, panel colour, music (irq_frame_end)"]
  S --> B --> R2 --> R3 --> R4 --> E --> S
  B -. "NMI after 5820 cycles" .-> N
~~~

1. **The frame starts at line 0.** [`irq_frame_start` `$2A66`](../src/sprite_mux_plan.asm#L6) sets `irq_bitmap_on` as the next handler at line `$5A`. Then it plans the sprite rows and selects one of the 7 layouts. It writes row 1 of both groups directly to the VIC. The section [The frame-start handler](#the-frame-start-handler) gives the steps. (**Code**)
2. **The bitmap starts under the panel.** [`irq_bitmap_on` `$2869`](../src/irq_screen_split.asm#L6) runs at line `$5A`, the last line of text row 4. It sets the first row handler, waits with four NOPs and writes `$3B` to `$D011` (bitmap mode). It writes the scene background colour and starts CIA 2 timer B. (**Code**)
3. **The row handlers move the sprites down.** Each row handler runs at the last line of a sprite row. It writes the new Y and three new sprite pointers for one group or for both groups. The layout gives 2, 3 or 4 row handlers. (**Code**)
4. **The NMI colours the floor.** CIA 2 timer B counts 5820 cycles and then gives an NMI. [`nmi_floor_colour` `$28A5`](../src/irq_screen_split.asm#L69) writes 7 (yellow) to `$D021`. (**Code**)
5. **The shadow row follows at line `$D9`.** The last row handler continues to the handler in `row4_irq_vector`. That handler shows the shadow of a fighter in the air, or it does nothing. (**Code**)
6. **The frame ends at line `$FF`.** [`irq_frame_end` `$2994`](../src/irq_screen_split.asm#L310) sets `irq_frame_start` at line 0 and writes `$1B` to `$D011` (text mode). It writes `panel_bg_colour` to `$D021` and calls [`music_play_frame` `$09A5`](../src/music_driver.asm#L6). Thus the music driver runs one time in each frame. See [sound_music.md](sound_music.md). (**Code**)

The NMI and the row handlers run in the same raster lines. A raster IRQ cannot interrupt the NMI, but the NMI can interrupt a row handler. The NMI handler saves only A, and it changes only `$D021`. (**Code**) **Conclusion**: the authors used a CIA 2 NMI for the floor colour. The raster chain is busy with the sprite rows in the lines `$B4-$D9`. The timer gives the colour change at the same line in each layout.

The game code of the frame runs outside the interrupts. [`bout_frame_loop` `$15AA`](../src/init_bout_loop.asm#L208) waits until the raster line is `$FD` or more. Then it updates the two fighters while the handlers interrupt it. See [game_flow.md](game_flow.md). (**Code**)

## The timeline of one frame

This timeline is for the most common case: both fighters stand on the ground. Both groups have Y `$A0`, so the planner selects layout 1. The text rows start at line `$33` because the vertical scroll of `$D011` is 3.

| Line | Decimal | Event | Handler |
|---|---|---|---|
| `$00` | 0 | Next handler at `$5A`. Sprite multicolours, groups, shadow handler, layout, operands, row 1 pointers, Y, colours and X. | `irq_frame_start` |
| `$33-$5A` | 51-90 | Text rows 0-4: the score panel in text mode, background `panel_bg_colour` (3). | none |
| `$5A` | 90 | Next handler at `$B4`. Bitmap mode, scene background colour, CIA 2 timer B starts (5820 cycles). | `irq_bitmap_on` |
| `$5B` | 91 | Text row 5: the scene bitmap starts. | none |
| `$A0` | 160 | The VIC starts sprite row 1 of both fighters (Y `$A0`). | none |
| `$B4` | 180 | Sprites 0-5 to Y `$B5`, six row 2 pointers. Next handler at `$C9`. | `irq_ab_row2` |
| about `$B8` | about 184 | NMI of CIA 2 timer B: background 7, yellow. | `nmi_floor_colour` |
| `$BB` | 187 | Text row 17: the floor starts. | none |
| `$C9` | 201 | Sprites 0-5 to Y `$CA`, six row 3 pointers. Next handler at `$D9`. | `irq_ab_row3` |
| `$D9` | 217 | No shadow row. Next handler at `$FF`. | `irq_no_row4` |
| `$FF` | 255 | Text mode, panel colour, music driver. Next handler at `$00`. | `irq_frame_end` |

The line of the NMI is an estimate from the code. The code of `irq_bitmap_on` before the timer start takes about 80 cycles, and line `$5B` is a bad line. Thus the timer starts near the start of line `$5C`. 5820 cycles are 92.4 lines, so the NMI comes at about line `$B8`, three lines above the floor. (**Conclusion**)

## The frame-start handler

`irq_frame_start` is the longest handler of the chain. It runs at line 0, above the visible screen. **Conclusion**: it must end before line `$5A`, or `irq_bitmap_on` starts late. It plans the rows of the frame and writes the plan into the operands of the other handlers. The steps, in the order of the code:

1. **It continues the chain first.** It acknowledges the raster IRQ in `$D019` and sets `irq_bitmap_on` at line `$5A`. Then it saves Y and X on the stack. (**Code**)
2. **It sets the sprite multicolours.** `$D025` = 0 (black) and `$D026` = `$0A` (light red). The third colour of each fighter, `fighter_colour`, comes in step 7. (**Code**)
3. **It puts the fighters in the groups.** It writes `front_fighter` into `group_a_fighter` and the other fighter into `group_b_fighter`. Then [`mux_copy_group_pos` `$2AAA`](../src/sprite_mux_plan.asm#L44) copies `sprite_y`, `sprite_x_lo` and `sprite_x_msb` of each fighter into `group_y`, `group_x_lo` and `group_x_msb`. (**Code**)
4. **It selects the shadow handler.** It compares the Y of each group with `$A0` and writes one of four handler addresses into `row4_irq_vector`. Then [`mux_patch_row4_ptrs` `$2B00`](../src/sprite_mux_plan.asm#L91) copies the shadow pointers into the row 4 handlers. When both groups are at `$A0`, it does not copy them. (**Code**)
5. **It selects the layout.** [`mux_choose_layout` `$2B40`](../src/sprite_mux_plan.asm#L119) calculates the gap and jumps to the code of one of the 7 layouts. The section [The 7 layouts](#the-7-layouts) gives them. (**Code**)
6. **It patches the row handlers.** The layout code calls the patch routines for the row pointers. Then it writes the next handler address, the next raster line and the new Y into each handler of the chain. (**Code**)
7. **It shows sprite row 1.** [`mux_set_row1` `$2E5A`](../src/sprite_mux_plan.asm#L500) writes the pointers of parts 0-2 of each group to `$CFF8-$CFFD`. It also writes the Y, the colours, the X of the three columns and the X bit 8 of each group. Then it restores X and Y and returns with RTI. (**Code**)

The row 1 values go directly to the VIC, because the VIC shows row 1 later in the frame, at line Y. Rows 2 and 3 use the same sprites, so they cannot go to the VIC at line 0. Thus the handler writes them into the operands of the row handlers. (**Code**)

The three columns of a group are at X, X+`$18` and X+`$30`. When an addition carries, the column passes X 255. Then `mux_set_row1` uses index 2 or 3 into `mux_msb_bits_a` or `mux_msb_bits_b` in place of `group_x_msb`. These tables give the bit 8 mask for sprites 0-2 and 3-5. The AND `#$C0` keeps the X bit 8 of sprites 6 and 7, which the game does not use. (**Code**)

The handler has five `CLI` / `SEI` pairs, one after the stack saves and four in `mux_set_row1`. The source comment says that a pending IRQ can start between the two instructions. In the final game, only the raster IRQ is on, and its next line is `$5A`. (**Code**) **Conclusion**: the pairs are windows for the CIA 1 sample IRQ of an earlier build. In version I, no IRQ can use them.

### Which fighter is in front

`front_fighter` selects the fighter of group A. [`fighter_set_priority` `$224C`](../src/fighter_moves.asm#L16) sets it to a fighter in an attack move, or to the opponent of a fighter in move `$11`. The frame-start handler reads it again in each frame. Thus the two fighters can change groups from one frame to the next. Then the planner gives the groups their new pointers, Y, X and colours. (**Code**)

## The 7 layouts

A group needs one IRQ at the last line of row 1 and one at the last line of row 2. The IRQ of a row runs at line Y+`$14` and writes the new Y, Y+`$15`. Two groups at different Y need four row IRQs in the order of their lines. The order depends on which group is higher and on the gap.

The source comment at `mux_choose_layout` explains why only 7 layouts are necessary. The sprite Y is `fighter_y` x 2, and all animation steps change `fighter_y` by an even value. Thus the gap is always a multiple of 4. (**Code**) The animation scripts are on [fighters.md](fighters.md).

| Layout | Code | Condition | Chain after `irq_bitmap_on` | Patch routines |
|---|---|---|---|---|
| 1 | `mux_layout_same_y` | Gap 0 | `irq_ab_row2` (Y+`$14`), `irq_ab_row3` (Y+`$29`) | `mux_patch_ab_row2`, `mux_patch_ab_row3` |
| 2 | `mux_layout_a_interleave` | A higher, gap 4-`$10` | `irq_a_row2`, `irq_b_row2`, `irq_a_row3`, `irq_b_row3` | a row 2, b row 2, a row 3, b row 3 |
| 3 | `mux_layout_b_interleave` | B higher, gap 4-`$10` | `irq_b_row2`, `irq_a_row2`, `irq_b_row3`, `irq_a_row3` | b row 2, a row 2, b row 3, a row 3 |
| 4 | `mux_layout_a_gap14` | A higher, gap `$14` | `irq_a_row2`, `irq_b2_a3` (A+`$28`), `irq_b_row3` | a row 2, `mux_patch_b2_a3`, b row 3 |
| 5 | `mux_layout_b_gap14` | B higher, gap `$14` | `irq_b_row2`, `irq_a2_b3` (B+`$28`), `irq_a_row3` | b row 2, `mux_patch_a2_b3`, a row 3 |
| 6 | `mux_layout_a_apart` | A higher, gap `$18` or more | `irq_a_row2`, `irq_a_row3`, `irq_b_row2`, `irq_b_row3` | a row 2, a row 3, b row 2, b row 3 |
| 7 | `mux_layout_b_apart` | B higher, gap `$18` or more | `irq_b_row2`, `irq_b_row3`, `irq_a_row2`, `irq_a_row3` | b row 2, b row 3, a row 2, a row 3 |

In the table, "a row 2" is `mux_patch_a_row2`, and so on. Each chain then continues to the handler in `row4_irq_vector` at line `$D9`, and that handler continues to `irq_frame_end` at line `$FF`. (**Code**)

~~~mermaid
flowchart TB
  G{"Gap of group A and group B"}
  G -->|"0"| L1["Layout 1: both groups in one handler for each row"]
  G -->|"4 to $10"| L23["Layout 2 or 3: rows 2 and 3 of A and B alternate"]
  G -->|"$14"| L45["Layout 4 or 5: one combined handler for row 2 and row 3"]
  G -->|"$18 or more"| L67["Layout 6 or 7: all rows of the higher group first"]
~~~

**A gap of `$14` puts two IRQs one line apart.** Example: group A is `$14` lines higher than group B. Then row 2 of B starts at A+`$29`, and row 3 of A starts at A+`$2A`. A second IRQ cannot start one line after the first. Thus [`irq_b2_a3` `$27BD`](../src/irq_sprite_rows.asm#L602) runs at line A+`$28` and writes both rows. [`irq_a2_b3` `$2813`](../src/irq_sprite_rows.asm#L717) does the same when B is higher. Each one writes the first set of pointers, waits with three NOPs, and then writes the second set. (**Code**) The coverage of the runs includes the code of both combined handlers, so the gap `$14` occurs in play. (**Observed**)

**The test for a gap of `$16` does nothing.** After each gap subtraction, the code has `CMP #$16` and `BNE` to the next instruction (`mux_a_above_gap_test`, `mux_b_above_gap_test`). The branch offset is 0, so both paths are the same. (**Code**) A gap of `$16` cannot occur, because the gap is a multiple of 4. **Conclusion**: an earlier version had two more layouts for the gap `$16`. The two unused patch routines `mux_unused_patch_b3_a2` and `mux_unused_patch_a3_b2` fit that case. They are the patch routines of the combined handlers with the two rows exchanged. Nothing calls them.

The layouts 2, 3, 6 and 7 give 8 IRQs in a frame. The layouts 4 and 5 give 7, and layout 1 gives 6. (**Code**)

## The self-modified operands

All row handlers have the same form. Each value that changes from frame to frame is the operand of an `LDA #`. The source gives each operand a name with `name = * + 1` on the line before the `LDA`. The name is `<handler>_<what>`:

| Suffix | Meaning | Handlers |
|---|---|---|
| `_y` | The new Y of the row | the 6 single-row handlers |
| `_a_y`, `_b_y` | The new Y of group A, of group B | `irq_b2_a3`, `irq_a2_b3` |
| `_next_line` | The raster line of the next handler | all row handlers and `irq_bitmap_on` |
| `_next_lo`, `_next_hi` | The address of the next handler | all row handlers and `irq_bitmap_on` |
| `_ptr_left`, `_ptr_mid`, `_ptr_right` | The 3 sprite pointers of one group | the single-group row and row 4 handlers |
| `_a_ptr_*`, `_b_ptr_*` | The pointers of group A, of group B | the combined handlers and `irq_ab_row4` |

This is [`irq_a_row2` `$2635`](../src/irq_sprite_rows.asm#L6) without the `RUN_STATE` patches of the source:

~~~asm
irq_a_row2
        bit VICIRQ
        bmi irq_a_row2_vic
        jmp sfx_sample_irq              ; Not a VIC IRQ: a CIA1 IRQ for the sample player
irq_a_row2_vic
        pha
irq_a_row2_y = * + 1
        lda #$00                        ; Patched: row 2 Y of group A (group_y + $15)
        sta SP0Y
        sta SP1Y
        sta SP2Y
        lda #$01
        sta VICIRQ                      ; $d019: sources raster
irq_a_row2_next_line = * + 1
        lda #$00                        ; Patched: raster line of the next handler
        sta RASTER
irq_a_row2_next_lo = * + 1
        lda #$00                        ; Patched: next handler, low byte
        sta hw_irq_vector
irq_a_row2_ptr_left = * + 1
        lda #$00                        ; Patched: sprite pointer, part 3 of the group A fighter
        sta sprite_pointers
irq_a_row2_ptr_mid = * + 1
        lda #$00                        ; Patched: sprite pointer, part 4 of the group A fighter
        sta $cff9
irq_a_row2_ptr_right = * + 1
        lda #$00                        ; Patched: sprite pointer, part 5 of the group A fighter
        sta $cffa
irq_a_row2_next_hi = * + 1
        lda #$00                        ; Patched: next handler, high byte
        sta $ffff
        pla
        rti
~~~

Two groups of code write these operands. The layout code writes `_y`, `_next_line`, `_next_lo` and `_next_hi`. It also writes `irq_bitmap_on_next_line`, `irq_bitmap_on_next_lo` and `irq_bitmap_on_next_hi`. The patch routines in `sprite_mux_patch.asm` write the pointers. For example, [`mux_patch_a_row2` `$2F0C`](../src/sprite_mux_patch.asm#L6) copies the pointers of parts 3-5 of the group A fighter from `fighter_part_ptrs` into `irq_a_row2_ptr_left`, `irq_a_row2_ptr_mid` and `irq_a_row2_ptr_right`. The row 3 routines copy parts 6-8. (**Code**)

The six single-row handlers write the low byte of the next address before the pointers and the high byte after them. The vector at `$FFFE` has a wrong value between the two writes. No IRQ can come in that time, because the handler runs with the I flag set. (**Code**)

`irq_b_row2` and `irq_b_row3` have one NOP before the pointer writes. `irq_bitmap_on` has four NOPs before the `$D011` write. (**Code**) **Conclusion**: these NOPs move the writes to a cycle where the VIC already read the old value. The VIC reads the pointers of sprites 3-5 later in the line than the pointers of sprites 0-2.

### The shadow row

The four row 4 handlers run at line `$D9` and continue to `irq_frame_end` at line `$FF`. Their next line and next address are constant. `irq_frame_start` selects one of them from the Y of the groups (**Code**):

| Group A at `$A0` | Group B at `$A0` | Handler | Sprites at Y `$DA` |
|---|---|---|---|
| yes | yes | `irq_no_row4` | none |
| yes | no | `irq_b_row4` | 3-5 |
| no | yes | `irq_a_row4` | 0-2 |
| no | no | `irq_ab_row4` | 0-5 |

The shadow pointers come from `row4_ptr_left`, `row4_ptr_mid` and `row4_ptr_right`. The shape builder sets them for 8 frames in the air. They point directly to pre-drawn shadow sprites at `$D540-$DEFF`, so no copy is necessary. (**Code**) The shape builder is on [graphics.md](graphics.md).

![The shadow sprites for facing 0, in multicolour](reference/images/shadow_facing0-multicolour.png)

The image shows the shadow sprites of facing 0, at `$D540-$D7BF`.

## The vectors and the CIA set-up

The game switches the KERNAL ROM off. Thus the CPU reads the vectors at `$FFFA-$FFFF` from RAM. [`init_vectors_cias` `$1459`](../src/init_bout_loop.asm#L51) writes them one time at the start (**Code**):

| Vector | Address | Value | Meaning |
|---|---|---|---|
| NMI | `$FFFA` | `nmi_floor_colour` | The floor colour NMI of CIA 2 timer B. |
| RESET | `$FFFC` | `reset_vector_rti` | An RTI byte. |
| IRQ | `$FFFE` | `irq_frame_start` | The first handler. Each handler then writes the next one. |

**The RESET vector points to an RTI byte.** [`reset_vector_rti` `$14A6`](../src/init_bout_loop.asm#L87) is one `RTI`. A reset switches the KERNAL ROM on, so the CPU reads the reset vector of the ROM and never this one. (**Code**) No run executed the byte. (**Observed**)

**The NMI handler does nothing for RESTORE.** `nmi_floor_colour` reads `$DD0D` with `BIT`. When bit 7 is 0, CIA 2 did not cause the NMI, and the handler only returns. Thus the RESTORE key does nothing that a player can see. (**Code**)

`init_vectors_cias` does these steps:

1. `SEI`. `$01` = `$07`, with the ROMs on.
2. `$DC0D` = `$7F`: CIA 1 gives no IRQ. Then one `CLI` / `SEI` pair.
3. `$D01A` = 1: the VIC gives only the raster IRQ.
4. `$01` = `$05`: RAM everywhere, with I/O at `$D000`.
5. The IRQ vector and the RESET vector.
6. `$DD0D` = `$7F`, then the NMI vector, then `$DD0D` = `$82`: CIA 2 gives an NMI only for timer B.
7. The timer B latch of CIA 2 = `$16BC` (5820 cycles).
8. `$DC02` = 0: port A of CIA 1 is an input, for the joystick read.

(**Code**) **Conclusion**: the `CLI` / `SEI` pair of step 2 lets a pending KERNAL interrupt end while the KERNAL ROM is still on.

The routine ends with the I flag set, and `init_vic_screen` then writes `$FF` to `$D012`. The first `CLI` is in [`bout_loop` `$1590`](../src/init_bout_loop.asm#L196). Thus the chain starts in the first bout, and its first IRQ runs `irq_frame_start` at line `$FF`. From then on, the chain runs at its normal lines. (**Code**)

**The timer B start each frame.** `irq_bitmap_on` writes the latch `$16BC` again and then `$09` to `$DD0F`. Bit 0 starts the timer and bit 3 selects one-shot mode. The timer does not run at this time, so the write of the high byte of the latch also loads the counter. After the NMI, the timer stops again until the next frame. (**Code**)

**The scene background colour.** `irq_bitmap_on` writes `irq_bitmap_on_bg_colour` to `$D021`. The operand is 1 (white). [`scene_draw_if_new` `$1A63`](../src/title_and_scene.asm#L173) writes 3 into it while it draws a new scene, and 1 again at the end. (**Code**)

## The test at the start of each handler

All 15 raster handlers start with the same three instructions:

~~~asm
        bit VICIRQ                      ; $D019: bit 7 = the VIC caused the IRQ
        bmi <handler>_vic
        jmp sfx_sample_irq              ; Not a VIC IRQ
~~~

When bit 7 of `$D019` is 0, the IRQ did not come from the VIC. Then the handler jumps to [`sfx_sample_irq` `$29C8`](../src/sfx_sample_player.asm#L6), a 1-bit sample player on CIA 1 timer B. But `init_vectors_cias` stops all CIA 1 interrupts, and the VIC gives only the raster IRQ. Thus no handler can take the jump. (**Code**) No run executed one of the 15 `JMP` instructions or the sample player. (**Observed**)

The test costs 7 cycles in each IRQ, so 42 to 56 cycles in each frame. (**Code**) **Conclusion**: an earlier build played a sample on the CIA 1 IRQ and the raster IRQ together. The sample player, its set-up and the 15 jumps stayed in the game after the music replaced the sample. The sample player and its old data are on [sound_music.md](sound_music.md). The history is on [../../docs/development.md](../../docs/development.md).

## Worked example: a frame in the SHADOW release

The SHADOW release is a memory dump of a game that ran. Thus its row handlers hold the operands of the last frames before the dump. The `RUN_STATE` switch of the source gives these values. In the R2010 release, the operands of the row handlers and of `irq_bitmap_on` are 0. The row 4 pointers are `$4A`, `$4B` and `$4C`. (**Observed**, byte compare of the releases)

The operands of `irq_bitmap_on` and of the two `irq_ab_*` handlers give the last frame (**Observed**, bytes of SHADOW):

| Operand | Value | Meaning |
|---|---|---|
| `irq_bitmap_on_next_line` | `$B4` | `$A0` + `$14`: both groups on the ground |
| `irq_bitmap_on_next_lo/hi` | `$1B`, `$27` | `irq_ab_row2`: layout 1 |
| `irq_ab_row2_y` | `$B5` | `$A0` + `$15` |
| `irq_ab_row2_a_ptr_*` | `$00`, `$20`, `$21` | Parts 3-5 of group A: part 3 empty, then pointers `$20` and `$21` |
| `irq_ab_row2_b_ptr_*` | `$0D`, `$0E`, `$00` | Parts 3-5 of group B: part 5 empty |
| `irq_ab_row2_next_line` | `$C9` | `$A0` + `$29` |
| `irq_ab_row2_next_lo/hi` | `$6C`, `$27` | `irq_ab_row3` |
| `irq_ab_row3_y` | `$CA` | `$A0` + `$2A` |
| `irq_ab_row3_next_line` | `$D9` | The shadow handler line |
| `irq_ab_row3_next_lo/hi` | `$75`, `$29` | `irq_no_row4`: no fighter in the air |

The pointers of group A are in `$1C-$24`, the sprite buffer at `$C700`. The pointers of group B are in `$0A-$12`, the buffer at `$C280`. The bout set-up gives `draw_buffer` 0 to fighter 0 and 2 to fighter 1, and `shape_build` changes only bit 0. Thus buffers 0 and 1 belong to fighter 0, and buffers 2 and 3 to fighter 1. (**Code**) **Conclusion**: in the last frame, fighter 1 was in front, in group A.

The other handlers hold older plans, and each plan is complete:

- **Layout 3.** `irq_b_row2_y` = `$A5` and `irq_b_row2_next_line` = `$B4` give group B at Y `$90` and group A at Y `$A0`. The chain continues through `irq_a_row2`, `irq_b_row3` and `irq_a_row3` to `irq_b_row4`, the shadow of group B.
- **Layout 4.** `irq_b2_a3_b_y` = `$B5` and `irq_b2_a3_a_y` = `$B6` give group A at Y `$8C` and group B at Y `$A0`, a gap of `$14`.
- **Layout 5.** `irq_a2_b3_a_y` = `$B5` and `irq_a2_b3_b_y` = `$B6` give group B at Y `$8C` and group A at Y `$A0`.

(**Observed**, bytes of SHADOW) The `irq_a_row4_ptr_*` operands are `$66`, `$67` and `$00`. These pointers are the shadow of frame 9 for facing 0 in `shadow_facing0_b`. (**Observed**)

**Conclusion**: the start values of the operands have no effect. The planner writes each operand of a handler in the same frame, before the chain reaches that handler. Thus `RUN_STATE` changes the bytes of the program, but not its behaviour.

## Still open

- The line of the floor NMI. Stop at `nmi_floor_colour` and read `$D012`. Compare the result with the estimate `$B8` and with text row 17 at line `$BB`. Look at the scene pixels with colour %00 in the lines between them.
- The end of `irq_frame_start`. Measure the last line of the handler with the most work, layout 2 with both shadows. The handler must end before line `$5A`.
- The shadow row of a fighter at Y `$9C`. Row 3 of that fighter shows until line `$DA`, and the shadow row needs the same sprites at Y `$DA`. Put a fighter at `fighter_y` = `$4E` and look at the shadow.
- The read of `$3004`. The coverage maps of the agent notes show a read of `$3004`, inside `mux_unused_patch_a3_b2`. **Conclusion**: `mux_set_row1` reads `mux_msb_bits_b` with an index of `$FC`. Set a read watchpoint on `$3004` from the start and read X and `group_x_msb`.
