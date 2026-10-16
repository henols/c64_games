# Bruce Lee: the actor sprites

This page describes how *Bruce Lee* (Datasoft 1984, C64 release REV.2) stores the figures of Bruce Lee, Yamo and the Ninja, and how it turns them into hardware sprites. It covers:
- the 1-bit frame graphics [`frame_graphics`](../../src/sprite_data.asm#L167) [`$5D91-$68F8`](../reference/graphics.md#frame_graphics) (210 frames) and the frame tables that describe them;
- the per-actor tables: frame base, hardware sprites, colours;
- the frame address tables [`actor_frame_addr_lo`](../../src/actor_room_tables.asm#L9) [`$1167`](../reference/modules/actor_room_tables.md#actor_frame_addr_lo) / [`actor_frame_addr_hi`](../../src/actor_room_tables.asm#L38) [`$1239`](../reference/modules/actor_room_tables.md#actor_frame_addr_hi) (the collision masks made from the same frames);
- the renderer [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2584`](../reference/modules/sprite_render.md#draw_object_sprites), which copies the frames into the double-buffered sprite blocks [`sprite_blocks`](../../src/vic_bank2.asm#L6) [`$8180-$83FF`](../reference/modules/vic_bank2.md#sprite_blocks) in VIC bank 2;
- the sprite register update [`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$25E2`](../reference/modules/sprite_render.md#update_sprite_registers): positions, colours and the sprite pointers [`sprite_pointers`](../../src/vic_bank2.asm#L574) [`$8FF8`](../reference/modules/vic_bank2.md#sprite_pointers);
- the sprite buffer clears in `interrupts.asm`;
- a worked example of one pose, decoded byte by byte from the image;
- the Apple II source text leftover [`leftover_source_text`](../../src/sprite_data.asm#L6) [`$5900-$59A4`](../reference/modules/sprite_data.md#leftover_source_text).

Which pose an actor shows in which state is on [object_actions.md](object_actions.md). The actors themselves (spawning, the actor tables) are on [actors.md](actors.md). The use of the collision masks is on [combat_collision.md](combat_collision.md).

**Sources.**
- The generated source: [sprite_render.asm](../reference/modules/sprite_render.md) `$2584-$277F`, [sprite_data.asm](../reference/modules/sprite_data.md) `$5900-$68F8`, [vic_bank2.asm](../reference/modules/vic_bank2.md) `$8180-$8FFF`, [actor_room_tables.asm](../reference/modules/actor_room_tables.md) `$1166-$1385`, [interrupts.asm](../reference/modules/interrupts.md) `$1103-$1165`.
- The image `unpacked/image.bin` and the coverage map of all runs.
- The VICE snapshots of earlier runs (`rooms`, `r17_freeze`, `explore3`, `explore4`, `modes`, `room_events2`, `room_special`): the sprite blocks in them were compared with the decoder of section 4.
- The assets [assets/sprites/](../../assets/sprites/frames.json) (`frames.json`, the sheets) and [actor_frame_addr.json](../../assets/tables/actor_frame_addr.json).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of [`main_loop`](../../src/main_loop.asm#L6) [`$1BC2`](../reference/modules/main_loop.md#main_loop); at most one pass every 3 frames. A *frame* is one video frame: one run of the raster IRQ chain.
- An *actor* is one of the moving figures, numbered by the index into the actor tables: actor 0 = Bruce, actor 1 = Yamo, actor 2 = the Ninja (the actor numbers follow [`spawn_yamo`](../../src/actors.asm#L177) [`$0CD5`](../reference/modules/actors.md#spawn_yamo) and [`spawn_ninja`](../../src/actors.asm#L355) [`$0DF8`](../reference/modules/actors.md#spawn_ninja)).
- A *frame number* (0-209) indexes the frame tables. A *pose* (`$00-$44`, even) is a frame number relative to the actor's first frame. A pose shows two frames: the *body* (frame f, f even) and the *overlay* (frame f+1). The two layers are two hardware sprites at the same place.
- A *block* is a 64-byte VIC sprite data block. Block n is at `$8000` + 64·n in VIC bank 2; its sprite pointer value is n.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

---------------------------------------------------------------------------------------------

## 1. Overview

~~~mermaid
flowchart TB
  ML["main_loop $1BC2"] --> DOS["draw_object_sprites $2584"]
  ER["enter_room $2F8E"] --> DOS
  DOS --> GSB["get_sprite_block_ptr $2704"]
  DOS --> SFS["setup_frame_source $2719"]
  DOS --> CFS["copy_frame_to_sprite $26A0"]
  TAB["frame tables $59BD-$5D90"] -.-> SFS
  GFX["frame_graphics $5D91-$68F8"] -.-> CFS
  CFS -.-> BLK["sprite_blocks $8180-$83FF"]
  IRQ["irq_frame_top $48C1"] --> GFU["game_frame_update $15A8"]
  GFU --> USR["update_sprite_registers $25E2"]
  DOS -. "sprite_frame_shown = 0" .-> USR
  USR -.-> VIC["VIC X, Y, colour, $D010"]
  USR -.-> PTR["sprite_pointers $8FF8"]
~~~

| Node | Role |
|---|---|
| [`main_loop`](../../src/main_loop.asm#L6) [`$1BC2`](../reference/modules/main_loop.md#main_loop) | Calls [`draw_object_sprites`](../../src/sprite_render.asm#L6) once per pass, at [`main_loop`](../../src/main_loop.asm#L6) [`$1C2C`](../../src/main_loop.asm#L57), after [`update_actors`](../../src/actor_input.asm#L6) [`$179E`](../reference/modules/actor_input.md#update_actors) has chosen the poses. |
| [`enter_room`](../../src/background_touch.asm#L210) [`$2F8E`](../reference/modules/background_touch.md#enter_room) | Calls [`draw_object_sprites`](../../src/sprite_render.asm#L6) at [`enter_room`](../../src/background_touch.asm#L210) [`$2FCF`](../../src/background_touch.asm#L249) after [`draw_room`](../../src/room_draw.asm#L6), with the IRQs off. |
| [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2584`](../reference/modules/sprite_render.md#draw_object_sprites) | Copies the body and overlay frame of each active actor into the hidden buffer. |
| [`get_sprite_block_ptr`](../../src/sprite_render.asm#L237) [`$2704`](../reference/modules/sprite_render.md#get_sprite_block_ptr) | Points [`sprite_block_ptr`](../../src/constants.asm#L14) [`$0E`](../reference/variables.md#sprite_block_ptr) at the block of one hardware sprite in the hidden buffer. |
| [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2719`](../reference/modules/sprite_render.md#setup_frame_source) | Reads the five frame tables for one frame and patches the source address into the copy loops. |
| [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26A0`](../reference/modules/sprite_render.md#copy_frame_to_sprite) | Writes the frame rows into the block and clears the rest of it. |
| [`irq_frame_top`](../../src/raster_irq_game.asm#L6) [`$48C1`](../reference/modules/raster_irq_game.md#irq_frame_top) | The game raster IRQ at line `$FD`; it calls [`game_frame_update`](../../src/frame_update.asm#L6) [`$15A8`](../reference/modules/frame_update.md#game_frame_update), which calls [`update_sprite_registers`](../../src/sprite_render.asm#L60) at [`game_frame_update`](../../src/frame_update.asm#L6) [`$15BA`](../../src/frame_update.asm#L15). |
| [`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$25E2`](../reference/modules/sprite_render.md#update_sprite_registers) | Once per new drawing: writes X, Y and colour of the actor sprites, points sprites 0-4 at the drawn buffer and flips [`sprite_buffer_select`](../../src/sprite_render.asm#L331) [`$277D`](../reference/modules/sprite_render.md#sprite_buffer_select). |

**Code.** The game shows the actors as hi-res sprites, X-expanded, not Y-expanded: [`init_game_screen`](../../src/game_setup.asm#L6) [`$0763`](../reference/modules/game_setup.md#init_game_screen) writes 0 to [`YXPAND`](../../src/constants.asm#L162) [`$D017`](../reference/variables.md#YXPAND), [`SPBGPR`](../../src/constants.asm#L166) [`$D01B`](../reference/variables.md#SPBGPR) and [`SPMC`](../../src/constants.asm#L167) [`$D01C`](../reference/variables.md#SPMC) ([`init_game_screen`](../../src/game_setup.asm#L6) [`$07EF-$07F5`](../../src/game_setup.asm#L70)) and `$FF` to [`XXPAND`](../../src/constants.asm#L168) [`$D01D`](../reference/variables.md#XXPAND) ([`init_game_screen`](../../src/game_setup.asm#L6) [`$07FA`](../../src/game_setup.asm#L74)). One bit of a frame is 2 screen pixels wide and 1 line high.

---------------------------------------------------------------------------------------------

## 2. Where the data is

### 2.1 The catalogue

| Name | Address | Layout | Read by | Written by |
|---|---|---|---|---|
| [`leftover_source_text`](../../src/sprite_data.asm#L6) | `$5900-$59A4` | 165 bytes of Apple II assembler source text (section 11). | nothing | — |
| [`actor_type_frame_base`](../../src/sprite_data.asm#L29) | `$59A5-$59A7` | 3 bytes, per actor type: first frame number. Type 0 = 0 (Bruce Lee), type 1 = 140 (Ninja), type 2 = 70 (Yamo). | [`set_object_pose`](../../src/object_pose.asm#L311) [`$29B3`](../../src/object_pose.asm#L323) | — |
| [`actor_type_sprite_a`](../../src/sprite_data.asm#L32) | `$59A8-$59AA` | 3 bytes per actor type: `$04 $03 $06`, copied to `$EC`+actor by [`init_actor`](../../src/actors.asm#L6) [`$0B9A`](../../src/actors.asm#L15). | [`init_actor`](../../src/actors.asm#L6) | — |
| [`actor_type_sprite_b`](../../src/sprite_data.asm#L35) | `$59AB-$59AD` | 3 bytes per actor type: `$05 $00 $07` (0 = none), copied to `$EF`+actor by [`init_actor`](../../src/actors.asm#L6) [`$0BA4`](../../src/actors.asm#L19). | [`init_actor`](../../src/actors.asm#L6) | — |
| [`sprite_owner_slot`](../../src/sprite_data.asm#L38) | `$59AE-$59B2` | 5 bytes: value 3-7 of the two tables above → index into [`sprite_owner`](../../src/actor_vars.asm#L184) [`$4F40`](../reference/modules/actor_vars.md#sprite_owner). | [`set_actor_slot_owner`](../../src/actors.asm#L375) [`$0E21`](../reference/modules/actors.md#set_actor_slot_owner) | — |
| (unused) | `$59B3-$59BC` | `$01 $02 $04 $08 $10 $1E $1D $1B $17 $0F`: bit masks of sprites 0-4 and their inverse within 5 bits. Nothing reads them (Code). | — | — |
| [`frame_src_lo`](../../src/sprite_data.asm#L43) | `$59BD-$5A8E` | 210 bytes: low byte of the graphics address of frame f. | [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2719`](../reference/modules/sprite_render.md#setup_frame_source), [`build_frame_mask`](../../src/collision.asm#L64) [`$517E`](../reference/modules/collision.md#build_frame_mask) | — |
| [`frame_src_hi`](../../src/sprite_data.asm#L72) | `$5A8F-$5B60` | 210 bytes: high byte. 0 = the frame has no graphics. | [`setup_frame_source`](../../src/sprite_render.asm#L251), [`build_frame_mask`](../../src/collision.asm#L64) | — |
| [`frame_height`](../../src/sprite_data.asm#L101) | `$5B61-$5C32` | 210 bytes: the height value h (section 3). | [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2731`](../../src/sprite_render.asm#L260), [`build_frame_mask`](../../src/collision.asm#L64) | — |
| [`frame_colour`](../../src/sprite_data.asm#L130) | `$5C33-$5CBE` | 140 bytes, frames 0-139 only: the colour register value (`$F7` yellow, `$F5` green, `$F0` black; the VIC uses the low nibble). | [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$273E`](../../src/sprite_render.asm#L267) | — |
| [`frame_wide_flag`](../../src/sprite_data.asm#L150) | `$5CBF-$5D90` | 210 bytes: 0 = narrow (8 bits wide), non-zero (`$01` or `$55`) = wide (16 bits). | [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2742`](../../src/sprite_render.asm#L270), [`build_frame_mask`](../../src/collision.asm#L64) | — |
| [`frame_graphics`](../../src/sprite_data.asm#L167) | `$5D91-$68F8` | 2920 bytes of 1-bit rows (section 3). Frames share bytes. | [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) (through the patched operands), [`build_frame_mask`](../../src/collision.asm#L64) | — |
| [`actor_frame_addr_lo`](../../src/actor_room_tables.asm#L9) / [`actor_frame_addr_hi`](../../src/actor_room_tables.asm#L38) | `$1167-$1238` / `$1239-$130A` | 210 + 210 bytes: address of the 96-byte collision mask of frame f (section 8). | [`build_collision_masks`](../../src/collision.asm#L21) [`$512F`](../reference/modules/collision.md#build_collision_masks), [`build_frame_mask`](../../src/collision.asm#L64), [`actor_background_collision`](../../src/collision.asm#L149) [`$5212`](../reference/modules/collision.md#actor_background_collision) | — |
| [`sprite_block_addr_table`](../../src/sprite_render.asm#L281) | `$274F-$2762` | 10 words: block address of sprites 0-4 in buffer 0, then in buffer 1. | [`get_sprite_block_ptr`](../../src/sprite_render.asm#L237) [`$270E`](../../src/sprite_render.asm#L245) | — |
| [`sprite_pointer_table`](../../src/sprite_render.asm#L289) | `$2763-$276C` | 10 bytes: pointer values `$06-$0A` (buffer 0) and `$0B-$0F` (buffer 1). | [`show_sprite_buffer`](../../src/sprite_render.asm#L152) [`$268D`](../../src/sprite_render.asm#L159), [`actor_place_sprites`](../../src/actors.asm#L105) [`$0C59`](../../src/actors.asm#L113) | — |
| [`actor_body_sprite`](../../src/sprite_render.asm#L299) | `$276D-$276F` | 3 bytes, per actor: hardware sprite of the body: 0, 2, 4. | [`draw_object_sprites`](../../src/sprite_render.asm#L6), [`update_sprite_registers`](../../src/sprite_render.asm#L60), [`init_actor`](../../src/actors.asm#L6), [`remove_actor`](../../src/background_touch.asm#L280) | — |
| [`actor_overlay_sprite`](../../src/sprite_render.asm#L306) | `$2770-$2772` | 3 bytes, per actor: hardware sprite of the overlay: 1, 3, `$FF` (none). | the same | — |
| [`sprite_bit_mask`](../../src/sprite_render.asm#L313) / [`sprite_clear_mask`](../../src/sprite_render.asm#L322) | `$2773-$2777` / `$2778-$277C` | 5 bytes each: bit of sprite 0-4, and its inverse, for [`MSIGX`](../../src/constants.asm#L157) [`$D010`](../reference/variables.md#MSIGX) and [`SPENA`](../../src/constants.asm#L160) [`$D015`](../reference/variables.md#SPENA). | [`update_sprite_registers`](../../src/sprite_render.asm#L60), [`init_actor`](../../src/actors.asm#L6), [`remove_actor`](../../src/background_touch.asm#L280) | — |
| [`sprite_buffer_select`](../../src/sprite_render.asm#L331) | `$277D` | 0 or 1: the buffer that is drawn next. Image value 0. | [`get_sprite_block_ptr`](../../src/sprite_render.asm#L237), [`show_sprite_buffer`](../../src/sprite_render.asm#L152), [`actor_place_sprites`](../../src/actors.asm#L105) | [`show_sprite_buffer`](../../src/sprite_render.asm#L152) [`$269C`](../../src/sprite_render.asm#L166) |
| [`sprite_frame_shown`](../../src/sprite_render.asm#L334) | `$277E` | 0 = a new drawing waits for the IRQ; 1 = shown. Image value 1. | [`update_sprite_registers`](../../src/sprite_render.asm#L60) | [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25DE`](../../src/sprite_render.asm#L57), [`apply_sprite_registers`](../../src/sprite_render.asm#L64) [`$25E8`](../reference/modules/sprite_render.md#apply_sprite_registers) |
| [`sprite_bytes_left`](../../src/sprite_render.asm#L337) | `$277F` | Counter of the copy (section 5.4). | [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) | [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) |
| [`frame_src_narrow`](../../src/sprite_render.asm#L176) / [`frame_src_wide_a`](../../src/sprite_render.asm#L214) / [`frame_src_wide_b`](../../src/sprite_render.asm#L221) | `$26AB` / `$26E4` / `$26EE` | Operand words of the three `LDA $E000,X` of the copy loops. `$E000` is a placeholder. | the CPU | [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$271C-$272E`](../../src/sprite_render.asm#L253) |
| [`sprite_blocks`](../../src/vic_bank2.asm#L6) | `$8180-$83FF` | 10 blocks of 64 bytes, blocks 6-15 (section 6). | the VIC | [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) and the clears of section 7 |
| [`sprite_pointers`](../../src/vic_bank2.asm#L574) | `$8FF8-$8FFF` | 8 sprite pointers of the screen at `$8C00`. | the VIC | [`show_sprite_buffer`](../../src/sprite_render.asm#L152), [`actor_place_sprites`](../../src/actors.asm#L105), [`title_screen`](../../src/title.asm#L6) [`$05CC`](../../src/title.asm#L37), [`launch_fireball0`](../../src/fireballs.asm#L124) [`$4201`](../reference/modules/fireballs.md#launch_fireball0), [`launch_fireball1`](../../src/fireballs.asm#L138) [`$4220`](../reference/modules/fireballs.md#launch_fireball1) |

Per-actor variables of the renderer (3 bytes each, index = actor):

| Name | Address | Meaning |
|---|---|---|
| [`actor_frame_a`](../../src/actor_vars.asm#L212) | `$4F4E` | Frame number of the body. The overlay is frame [`actor_frame_a`](../../src/actor_vars.asm#L212) + 1. |
| [`actor_frame_rel_b`](../../src/actor_vars.asm#L205) | `$4F4B` | Pose + 1: the overlay frame relative to the actor's first frame. [`update_sprite_registers`](../../src/sprite_render.asm#L60) tests it for the X shift. |
| [`actor_x`](../../src/constants.asm#L85) / [`actor_y`](../../src/constants.asm#L86) | `$9E` / `$A1` | Position. Sprite X = 2 · [`actor_x`](../../src/constants.asm#L85), sprite Y = [`actor_y`](../../src/constants.asm#L86) + `$1D`. |
| [`actor_facing`](../../src/constants.asm#L87) | `$A4` | 0 = facing left, 1 = facing right. |
| [`actor_body_wide`](../../src/constants.asm#L100) / [`actor_overlay_wide`](../../src/constants.asm#L101) | `$D4` / `$D7` | The wide flag of the frame drawn last. |
| [`actor_body_colour`](../../src/constants.asm#L102) / [`actor_overlay_colour`](../../src/constants.asm#L103) | `$DA` / `$DD` | The colour of the frame drawn last. |
| [`actor_frame_height`](../../src/constants.asm#L104) | `$E0` | The height value of the frame drawn last. |
| [`actor_shown_x`](../../src/constants.asm#L93) | `$B9` | Copy of [`actor_x`](../../src/constants.asm#L85) taken when the registers are written. Nothing in this subsystem reads it. |

### 2.2 Actors, frames and hardware sprites

| Actor | Type (bits 7-6 of [`actor_flags`](../../src/constants.asm#L82) [`$95`](../reference/variables.md#actor_flags)) | Frames | Body sprite | Overlay sprite | Colours | Blocks, buffer 0 / 1 |
|---|---|---|---|---|---|---|
| 0 Bruce Lee | `$00` → type 0 | 0-69 | 0 | 1 | from [`frame_colour`](../../src/sprite_data.asm#L130): `$F7` yellow and `$F0` black | 6, 7 / 11, 12 |
| 1 Yamo | `$80` → type 2 | 70-139 | 2 | 3 | from [`frame_colour`](../../src/sprite_data.asm#L130): `$F5` green and `$F0` black | 8, 9 / 13, 14 |
| 2 Ninja | `$40` → type 1 | 140-209 | 4 | none | always `$F0` black ([`setup_frame_source`](../../src/sprite_render.asm#L251) [`$273A`](../../src/sprite_render.asm#L264)) | 10 / 15 |

- **Code.** [`set_object_pose`](../../src/object_pose.asm#L311) [`$29A1`](../reference/modules/object_pose.md#set_object_pose) sets [`actor_frame_a`](../../src/actor_vars.asm#L212) = [`actor_type_frame_base`](../../src/sprite_data.asm#L29)[type] + pose. The type is bits 7-6 of [`actor_flags`](../../src/constants.asm#L82), rotated into bits 1-0 (`$80` gives 2, `$40` gives 1).
- **Code.** Each actor has 35 poses (`$00-$44`), so 70 frames. The odd frames 141-209 of the Ninja have [`frame_src_hi`](../../src/sprite_data.asm#L72) = 0: no graphics. They are never drawn, because the Ninja has no overlay sprite.
- **Code.** [`frame_colour`](../../src/sprite_data.asm#L130) [`$5C33`](../reference/modules/sprite_data.md#frame_colour) has only 140 entries. A Ninja frame would index past it into [`frame_wide_flag`](../../src/sprite_data.asm#L150) [`$5CBF`](../reference/modules/sprite_data.md#frame_wide_flag), but [`setup_frame_source`](../../src/sprite_render.asm#L251) loads `$F0` for actor 2 and never reads the table then.
- **Code.** The renderer and [`update_sprite_registers`](../../src/sprite_render.asm#L60) use [`actor_body_sprite`](../../src/sprite_render.asm#L299) and [`actor_overlay_sprite`](../../src/sprite_render.asm#L306). The values 3-7 of [`actor_type_sprite_a`](../../src/sprite_data.asm#L32) / [`actor_type_sprite_b`](../../src/sprite_data.asm#L35) are not these hardware sprites: they select an entry of [`sprite_owner`](../../src/actor_vars.asm#L184) through [`sprite_owner_slot`](../../src/sprite_data.asm#L38) (see [combat_collision.md](combat_collision.md)). `frames.json` and `assets/README.md` call these values "VIC sprites" (4 and 5 for Bruce); the hardware sprites of Bruce are 0 and 1.
- **Conclusion.** A lower sprite number has priority on the VIC, so the body is in front of the overlay, Bruce is in front of Yamo and Yamo in front of the Ninja.

---------------------------------------------------------------------------------------------

## 3. The byte layout of a frame

A frame is a run of rows in [`frame_graphics`](../../src/sprite_data.asm#L167). It starts at [`frame_src_lo`](../../src/sprite_data.asm#L43)[f] + 256 · [`frame_src_hi`](../../src/sprite_data.asm#L72)[f]. It has no header: the size comes from [`frame_height`](../../src/sprite_data.asm#L101)[f] = h and [`frame_wide_flag`](../../src/sprite_data.asm#L150)[f].

| Frame kind | [`frame_wide_flag`](../../src/sprite_data.asm#L150) | Rows | Bytes per row | Bytes | Row r |
|---|---|---|---|---|---|
| Narrow | 0 | h + 1 | 1 | h + 1 | `src[r]` |
| Wide | `$01` or `$55` | h | 2 | 2·h | `src[2r]` (left 8 bits), `src[2r+1]` (right 8 bits) |
| None | — ([`frame_src_hi`](../../src/sprite_data.asm#L72) = 0) | 0 | — | 0 | — |

| Bit | Meaning |
|---|---|
| bit 7 of a byte | the leftmost pixel of the 8 |
| 1 | sprite colour (from [`frame_colour`](../../src/sprite_data.asm#L130), or black for the Ninja) |
| 0 | transparent |

- Row 0 is the top row of the sprite. The rows below the frame are cleared to 0 (section 5.4), so a frame hangs from the sprite top.
- A narrow frame fills column 0 of the 3-byte sprite row: 8 bits, 16 screen pixels. A wide frame fills columns 0 and 1: 16 bits, 32 screen pixels. Column 2 is always 0.
- Both facing directions are separate frames. Nothing mirrors a frame at run time (**Code**: no routine of the subsystem shifts or reverses the bits).

**Code, counts from the image.**
- 175 frames have graphics: 148 narrow and 27 wide. 35 frames have none (the odd Ninja frames).
- The wide frames are 4-7, 25, 29, 59, 63, 65, 67 (Bruce); 74-77, 94, 95, 98, 99, 128, 132, 133 (Yamo); 190, 194, 196, 198, 200, 202 (Ninja, flag `$55`).
- The frames use 125 different start addresses. They need 3791 bytes, but the area has 2920: frames share bytes. The even Bruce frames 0, 42, 44, ..., 54, for example, all start at `$663A`.
- The heights go up to 21 rows. One frame is taller: frame 129, Yamo's overlay of pose `$3A`, is narrow with h = 21 ([`frame_height+129`](../../src/sprite_data.asm#L101) [`$5BE2`](../reference/modules/sprite_data.md#frame_height)), so 22 rows. Its 22nd row is `$00`. Section 5.4 shows what the copy does with it.
- No frame reaches the bytes `$63C1-$63EA` (42 bytes). 30 more gaps of 1-4 bytes lie between frames.

---------------------------------------------------------------------------------------------

## 4. The decoder

The renderer as pseudo-code. The names are the names of the knowledge; `block` is the 64-byte sprite block, `src` is the frame graphics.

```
draw_object_sprites():                        ; $2584, once per pass
  for actor = 2 down to 0:                    ; $2586
    if actor_flags[actor] & 1 == 0: continue  ; inactive
    draw_layer(actor, actor_body_sprite[actor], actor_frame_a[actor],
               -> actor_body_wide, actor_body_colour)
    if actor == 2: continue                   ; the Ninja has one sprite
    if actor_overlay_sprite[actor] < 0: continue
    draw_layer(actor, actor_overlay_sprite[actor], actor_frame_a[actor] + 1,
               -> actor_overlay_wide, actor_overlay_colour)
  sprite_frame_shown = 0                      ; $25DE: the IRQ may show it now

draw_layer(actor, sprite, f):
  block = sprite_block_addr_table[sprite + 5*sprite_buffer_select]   ; $2704
  src   = frame_src_lo[f] | frame_src_hi[f] << 8                     ; $2719
  h     = frame_height[f];  actor_frame_height[actor] = h
  colour = $F0 if actor == 2 else frame_colour[f]
  wide  = frame_wide_flag[f]
  store wide and colour in the actor's variables
  copy_frame_to_sprite(block, src, h, wide)

copy_frame_to_sprite(block, src, h, wide):    ; $26A0
  if wide == 0:                               ; h+1 rows, column 0
    for r = h down to 0:
      block[3r] = src[r]
      if r > 0: block[3r-1] = 0; block[3r-2] = 0
    n = 3h + 1                                ; bytes written
  else:                                       ; h rows, columns 0 and 1
    for r = h-1 down to 0:
      block[3r+1] = src[2r+1]; block[3r] = src[2r]
      if r > 0: block[3r-1] = 0
    n = 3h - 1
  left = $3F - n                              ; sprite_bytes_left
  y = left XOR $3F                            ; = n while n <= $3F
  repeat:                                     ; clear_sprite_rest $26C6
    block[y] = 0; y += 1; left -= 1
  until left < 0                              ; clears offsets n..63
```

**Observed.** The decoder gives the same 64 bytes as the sprite blocks of the snapshots for 104 of 112 layers. The snapshots are those of the runs `rooms`, `r17_freeze`, `explore3`, `explore4`, `modes`, `room_events2` and `room_special`. The drawn buffer was taken as [`sprite_buffer_select`](../../src/sprite_render.asm#L331) when [`sprite_frame_shown`](../../src/sprite_render.asm#L334) = 0, else the other one. The 8 other layers are in 4 snapshots (`explore1/afterfire`, `explore2/after_right`, `explore2/room_start`, `rooms/room16`). **Conclusion:** they were taken at a moment when the blocks do not hold the current frames yet. In the three `explore` snapshots the sprite pointers are not those of the game (`$0F` in sprites 0 and 2-7). In `room16` Yamo's blocks do not match his current frame number, which fits a pose change after the last drawing.

---------------------------------------------------------------------------------------------

## 5. The step-by-step walk

### 5.1 [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2584`](../reference/modules/sprite_render.md#draw_object_sprites)

1. X = 2: start with the Ninja ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2584`](../reference/modules/sprite_render.md#draw_object_sprites)).
2. [`draw_actor_loop`](../../src/sprite_render.asm#L8) [`$2586`](../reference/modules/sprite_render.md#draw_actor_loop): store X in [`current_actor`](../../src/constants.asm#L40) [`$51`](../reference/variables.md#current_actor). Skip the actor when bit 0 of [`actor_flags`](../../src/constants.asm#L82) is clear ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$258C`](../../src/sprite_render.asm#L12)).
3. Body: [`get_sprite_block_ptr`](../../src/sprite_render.asm#L237) with A = [`actor_body_sprite`](../../src/sprite_render.asm#L299)[actor] ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2591`](../../src/sprite_render.asm#L14)).
4. [`setup_frame_source`](../../src/sprite_render.asm#L251) with X = [`actor_frame_a`](../../src/actor_vars.asm#L212)[actor] ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$2598`](../../src/sprite_render.asm#L17)). It returns Y = h, A = colour, X = wide flag.
5. Store the wide flag in [`actor_body_wide`](../../src/constants.asm#L100) and the colour in [`actor_body_colour`](../../src/constants.asm#L102) ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$259F-$25A2`](../../src/sprite_render.asm#L21)).
6. Y = 2·h + [`actor_frame_height`](../../src/constants.asm#L104)[actor] = 3·h: the offset of row h in the block ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25A4-$25A8`](../../src/sprite_render.asm#L24)). The carry after `ASL` is 0, because h ≤ 21.
7. Load [`actor_body_wide`](../../src/constants.asm#L100) (this sets Z) and call [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25AB`](../../src/sprite_render.asm#L29)).
8. Skip the overlay for actor 2 ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25B2`](../../src/sprite_render.asm#L32)) and when [`actor_overlay_sprite`](../../src/sprite_render.asm#L306) is negative ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25B7`](../../src/sprite_render.asm#L34)).
9. Overlay: the same steps with [`actor_overlay_sprite`](../../src/sprite_render.asm#L306), frame [`actor_frame_a`](../../src/actor_vars.asm#L212) + 1 (`INX` at [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25C0`](../../src/sprite_render.asm#L38)), [`actor_overlay_wide`](../../src/constants.asm#L101) and [`actor_overlay_colour`](../../src/constants.asm#L103) ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25B9-$25D4`](../../src/sprite_render.asm#L35)).
10. [`draw_next_actor`](../../src/sprite_render.asm#L52) [`$25D7`](../reference/modules/sprite_render.md#draw_next_actor): next actor down; loop while X ≥ 0.
11. Clear [`sprite_frame_shown`](../../src/sprite_render.asm#L334) ([`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25DE`](../../src/sprite_render.asm#L57)). Return.

**Code.** The overlay frame comes from [`actor_frame_a`](../../src/actor_vars.asm#L212) + 1, not from [`actor_frame_b`](../../src/actor_vars.asm#L219) [`$4F51`](../reference/modules/actor_vars.md#actor_frame_b). [`set_object_pose`](../../src/object_pose.asm#L311), [`init_actor`](../../src/actors.asm#L6) and [`spawn_yamo`](../../src/actors.asm#L177) always store [`actor_frame_b`](../../src/actor_vars.asm#L219) = [`actor_frame_a`](../../src/actor_vars.asm#L212) + 1, so both give the same frame.

### 5.2 [`get_sprite_block_ptr`](../../src/sprite_render.asm#L237) [`$2704`](../reference/modules/sprite_render.md#get_sprite_block_ptr)

1. A = hardware sprite (0-4). A = 2·A ([`get_sprite_block_ptr`](../../src/sprite_render.asm#L237) [`$2704`](../reference/modules/sprite_render.md#get_sprite_block_ptr)).
2. When [`sprite_buffer_select`](../../src/sprite_render.asm#L331) = 1, add 10 ([`get_sprite_block_ptr`](../../src/sprite_render.asm#L237) [`$270B`](../../src/sprite_render.asm#L242)): the second half of [`sprite_block_addr_table`](../../src/sprite_render.asm#L281).
3. Copy the word at that index into [`sprite_block_ptr`](../../src/constants.asm#L14) `$0E`/`$0F` ([`get_sprite_block_ptr`](../../src/sprite_render.asm#L237) [`$270E-$2716`](../../src/sprite_render.asm#L245)).

### 5.3 [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2719`](../reference/modules/sprite_render.md#setup_frame_source)

1. X = frame number. Store [`frame_src_lo`](../../src/sprite_data.asm#L43)[f] into the low operand bytes [`frame_src_narrow`](../../src/sprite_render.asm#L176), [`frame_src_wide_a`](../../src/sprite_render.asm#L214) and [`frame_src_wide_b`](../../src/sprite_render.asm#L221) ([`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2719-$2722`](../reference/modules/sprite_render.md#setup_frame_source)).
2. Store [`frame_src_hi`](../../src/sprite_data.asm#L72)[f] into their high bytes ([`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2725-$272E`](../../src/sprite_render.asm#L256)). The three `LDA $E000,X` of [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) now read the frame.
3. Y = [`frame_height`](../../src/sprite_data.asm#L101)[f] ([`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2731`](../../src/sprite_render.asm#L260)).
4. A = `$F0` when [`current_actor`](../../src/constants.asm#L40) = 2 ([`setup_frame_source`](../../src/sprite_render.asm#L251) [`$273A`](../../src/sprite_render.asm#L264)), else [`frame_colour`](../../src/sprite_data.asm#L130)[f] ([`setup_frame_source`](../../src/sprite_render.asm#L251) [`$273E`](../../src/sprite_render.asm#L267)). Push it.
5. Push [`frame_wide_flag`](../../src/sprite_data.asm#L150)[f] ([`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2742`](../../src/sprite_render.asm#L270)).
6. Store Y in [`actor_frame_height`](../../src/constants.asm#L104)[actor] ([`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2749`](../../src/sprite_render.asm#L274)). Pull X = wide flag and A = colour. Return.

The `RTS` at [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$274E`](../../src/sprite_render.asm#L279) is also the exit of [`select_object_pose`](../../src/object_pose.asm#L6) [`$2780`](../reference/modules/object_pose.md#select_object_pose) when the pose of the pass is already set.

### 5.4 [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26A0`](../reference/modules/sprite_render.md#copy_frame_to_sprite)

Entry: [`sprite_block_ptr`](../../src/constants.asm#L14) = block, Y = 3·h, X = [`current_actor`](../../src/constants.asm#L40), Z = (wide flag = 0).

Narrow frame:
1. [`sprite_bytes_left`](../../src/sprite_render.asm#L337) = `$3F` ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26A2`](../../src/sprite_render.asm#L171)). X = h ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26A7`](../../src/sprite_render.asm#L173)).
2. [`copy_narrow_row`](../../src/sprite_render.asm#L175) [`$26AA`](../reference/modules/sprite_render.md#copy_narrow_row): write `src[X]` to offset Y; count down [`sprite_bytes_left`](../../src/sprite_render.asm#L337).
3. X = X − 1. When X < 0, go to [`clear_sprite_rest`](../../src/sprite_render.asm#L193) ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26B3`](../../src/sprite_render.asm#L182)).
4. Write 0 to offsets Y−1 and Y−2 (columns 2 and 1 of the row above), count down twice ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26B5-$26C0`](../../src/sprite_render.asm#L183)).
5. Y = Y − 3; loop ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26C4`](../../src/sprite_render.asm#L191)).

Wide frame, [`copy_wide_frame`](../../src/sprite_render.asm#L204) [`$26D7`](../reference/modules/sprite_render.md#copy_wide_frame):
1. [`sprite_bytes_left`](../../src/sprite_render.asm#L337) = `$3F`. X = 2·h − 1 ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26DC-$26E0`](../../src/sprite_render.asm#L207)). Y = 3·h − 2: column 1 of row h − 1 ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26E1-$26E2`](../../src/sprite_render.asm#L211)).
2. [`copy_wide_row`](../../src/sprite_render.asm#L213) [`$26E3`](../reference/modules/sprite_render.md#copy_wide_row): write `src[X]` to offset Y (right byte), then `src[X−1]` to offset Y−1 (left byte) ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26E3-$26F0`](../../src/sprite_render.asm#L216)).
3. When X < 0, go to [`clear_sprite_rest`](../../src/sprite_render.asm#L193) ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26F6`](../../src/sprite_render.asm#L227)).
4. Write 0 to offset Y−2 (column 2 of the row above). Y = Y − 3; loop ([`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26F8-$2701`](../../src/sprite_render.asm#L228)).
5. The byte `$00` (BRK) at `$2703` after the loop is never executed: the loop always leaves at [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26F6`](../../src/sprite_render.asm#L227).

[`clear_sprite_rest`](../../src/sprite_render.asm#L193) [`$26C6`](../reference/modules/sprite_render.md#clear_sprite_rest):
1. Y = [`sprite_bytes_left`](../../src/sprite_render.asm#L337) XOR `$3F` = the count of bytes written ([`clear_sprite_rest`](../../src/sprite_render.asm#L193) [`$26C9`](../../src/sprite_render.asm#L195)).
2. [`clear_rest_loop`](../../src/sprite_render.asm#L198) [`$26CE`](../reference/modules/sprite_render.md#clear_rest_loop): write 0 at Y, Y = Y + 1, count down; loop while [`sprite_bytes_left`](../../src/sprite_render.asm#L337) ≥ 0.

**Code.** The routine writes all 64 bytes of the block, also byte 63, which the VIC does not show. Bytes written + bytes cleared = 64.

**Code (bug).** Frame 129 is narrow with h = 21. Its 22 rows need offsets 0-63: 64 bytes, one more than the counter allows. [`sprite_bytes_left`](../../src/sprite_render.asm#L337) ends at `$FF`, so step 1 of [`clear_sprite_rest`](../../src/sprite_render.asm#L193) gives Y = `$FF` XOR `$3F` = `$C0`. The loop writes one 0 at block + `$C0` and stops, because the counter is already negative.
- Frame 129 is Yamo's overlay (sprite 3) in pose `$3A`. [`select_object_pose`](../../src/object_pose.asm#L6) sets pose `$3A` at `$27ED` and `$2821`; the coverage shows that `$2821` ran, for an actor that the coverage does not name.
- Buffer 0 (block `$8240`): the 0 goes to `$8300`. That is byte 0 of block 12, the top-left byte of Bruce's overlay in buffer 1, which is the buffer on the screen at that time.
- Buffer 1 (block `$8380`): the 0 goes to `$8440`, inside [`title_font`](../../src/vic_bank2.asm#L124) [`$8400`](../reference/graphics.md#title_font). The image byte there is already `$00`.
- **Conclusion.** The visible effect is at most the loss of the top-left 8 bits of Bruce's overlay row 0, until the next drawing.

### 5.5 [`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$25E2`](../reference/modules/sprite_render.md#update_sprite_registers)

[`game_frame_update`](../../src/frame_update.asm#L6) calls it every frame. It does nothing while [`sprite_frame_shown`](../../src/sprite_render.asm#L334) ≠ 0.

1. When [`sprite_frame_shown`](../../src/sprite_render.asm#L334) ≠ 0, return ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$25E5`](../../src/sprite_render.asm#L62)).
2. [`apply_sprite_registers`](../../src/sprite_render.asm#L64) [`$25E8`](../reference/modules/sprite_render.md#apply_sprite_registers): set [`sprite_frame_shown`](../../src/sprite_render.asm#L334) (to 1). X = 2.
3. [`place_actor_loop`](../../src/sprite_render.asm#L67) [`$25ED`](../reference/modules/sprite_render.md#place_actor_loop): skip an inactive actor ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$25F3`](../../src/sprite_render.asm#L71); the branch lands on the `BEQ` at `$2634`, which jumps on to the next actor).
4. A = [`actor_x`](../../src/constants.asm#L85); copy it to [`actor_shown_x`](../../src/constants.asm#L93) ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$25F7`](../../src/sprite_render.asm#L73)).
5. When the body is wide and [`actor_facing`](../../src/constants.asm#L87) ≠ 1 (facing left), A = A − 8 ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$2603`](../../src/sprite_render.asm#L79)). That moves the sprite 16 pixels left.
6. A = 2·A. The carry is bit 8 of the X position: set or clear the body sprite's bit in [`MSIGX`](../../src/constants.asm#L157) with [`sprite_bit_mask`](../../src/sprite_render.asm#L313) / [`sprite_clear_mask`](../../src/sprite_render.asm#L322) ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$2606-$2618`](../../src/sprite_render.asm#L82)).
7. Write the X register [`SP0X`](../../src/constants.asm#L153) + 2·sprite ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$261F`](../../src/sprite_render.asm#L97)). Write [`actor_y`](../../src/constants.asm#L86) + `$1D` to the Y register ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$2627`](../../src/sprite_render.asm#L101)). Write [`actor_body_colour`](../../src/constants.asm#L102) to [`SP0COL`](../../src/constants.asm#L174) + sprite ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$262F`](../../src/sprite_render.asm#L104)).
8. For actor 2, go to the next actor ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$2634`](../../src/sprite_render.asm#L107)).
9. [`place_overlay_sprite`](../../src/sprite_render.asm#L108) [`$2636`](../reference/modules/sprite_render.md#place_overlay_sprite): A = [`actor_x`](../../src/constants.asm#L85). When [`actor_frame_rel_b`](../../src/actor_vars.asm#L205) is `$05`, `$3F`, `$43` or `$19`, A = A − 8 ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$264B`](../../src/sprite_render.asm#L120)). These are the overlays of poses `$04`, `$3E`, `$42` and `$18`. The facing does not count here.
10. The same register writes as steps 6-7 for [`actor_overlay_sprite`](../../src/sprite_render.asm#L306), with [`actor_overlay_colour`](../../src/constants.asm#L103) ([`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$264E-$2677`](../../src/sprite_render.asm#L123)).
11. [`place_next_actor`](../../src/sprite_render.asm#L146) [`$267A`](../reference/modules/sprite_render.md#place_next_actor): next actor; loop while X ≥ 0.
12. [`show_sprite_buffer`](../../src/sprite_render.asm#L152) [`$2682`](../reference/modules/sprite_render.md#show_sprite_buffer): Y = 4 for buffer 0 or 9 for buffer 1. Copy [`sprite_pointer_table`](../../src/sprite_render.asm#L289)[Y-4..Y] to [`sprite_pointers`](../../src/vic_bank2.asm#L574) 0-4 ([`show_sprite_buffer`](../../src/sprite_render.asm#L152) [`$268D-$2695`](../../src/sprite_render.asm#L159)).
13. Flip [`sprite_buffer_select`](../../src/sprite_render.asm#L331) ([`show_sprite_buffer`](../../src/sprite_render.asm#L152) [`$269C`](../../src/sprite_render.asm#L166)). Return.

- **Code.** The positions are written in the same IRQ as the pointers. A new picture and its position appear in the same frame.
- **Code.** [`actor_x`](../../src/constants.asm#L85) is in 2-pixel units, `$0D-$A3`, so the sprite X is 26-326. A shift of 8 units is 16 pixels: one narrow frame width on the screen.
- **Code.** [`init_actor`](../../src/actors.asm#L6) writes the positions and the two pointers of a new actor at once ([`actor_place_sprites`](../../src/actors.asm#L105) [`$0C4D`](../reference/modules/actors.md#actor_place_sprites)). It takes the pointers of the buffer in [`sprite_buffer_select`](../../src/sprite_render.asm#L331), the one that is drawn next. It always writes two pointers, body sprite and body sprite + 1. For the Ninja (sprite 4) that also sets the pointer of sprite 5 to `$0B` or `$10`. **Observed:** sprite 5's pointer is `$10` or `$0B` in the snapshots of the `rooms` run. [`init_actor`](../../src/actors.asm#L6) does not enable sprite 5, so nothing shows it.

---------------------------------------------------------------------------------------------

## 6. The sprite blocks and the double buffer

| Block | Address | Pointer | Buffer | Sprite | Layer | Other use |
|---|---|---|---|---|---|---|
| 6 | `$8180` | `$06` | 0 | 0 | Bruce body | |
| 7 | `$81C0` | `$07` | 0 | 1 | Bruce overlay | |
| 8 | `$8200` | `$08` | 0 | 2 | Yamo body | |
| 9 | `$8240` | `$09` | 0 | 3 | Yamo overlay | |
| 10 | `$8280` | `$0A` | 0 | 4 | Ninja | |
| 11 | `$82C0` | `$0B` | 1 | 0 | Bruce body | |
| 12 | `$8300` | `$0C` | 1 | 1 | Bruce overlay | |
| 13 | `$8340` | `$0D` | 1 | 2 | Yamo body | room 18: fireball 0, sprite 6 |
| 14 | `$8380` | `$0E` | 1 | 3 | Yamo overlay | room 18: fireball 1, sprite 7 |
| 15 | `$83C0` | `$0F` | 1 | 4 | Ninja | title: the TM sign, sprite 0 |

- **Code.** Room 18 has no enemies ([rooms_10_19.md](rooms_10_19.md)), so the fireballs can use Yamo's blocks of buffer 1. [`launch_fireball0`](../../src/fireballs.asm#L124) and [`launch_fireball1`](../../src/fireballs.asm#L138) set the pointers of sprites 6 and 7 to `$0D` and `$0E`.
- **Code.** On the title, [`title_screen`](../../src/title.asm#L6) [`$0584`](../reference/modules/title.md#title_screen) clears block 15 ([`title_screen`](../../src/title.asm#L6) [`$059F`](../../src/title.asm#L19)), copies the 12 bytes of [`tm_sprite_rows`](../../src/title_options.asm#L24) [`$0E40`](../reference/modules/title_options.md#tm_sprite_rows) into rows 4-7 of it ([`title_screen`](../../src/title.asm#L6) [`$05D1`](../../src/title.asm#L40)) and sets the pointer of sprite 0 to `$0F` ([`title_screen`](../../src/title.asm#L6) [`$05CC`](../../src/title.asm#L37)).

### 6.1 The state machine of the double buffer

~~~mermaid
stateDiagram-v2
  state "Drawing: sprite_frame_shown = 1" as Draw
  state "Waiting: sprite_frame_shown = 0" as Wait
  [*] --> Draw
  Draw --> Wait: draw_object_sprites ends
  Wait --> Draw: next frame IRQ, pointers to buffer S, S flips
  Draw --> Draw: frame IRQ, nothing to do
~~~

S is [`sprite_buffer_select`](../../src/sprite_render.asm#L331). The main loop draws into buffer S; the screen shows buffer 1 − S.

| State | Condition | Next state | Code |
|---|---|---|---|
| Drawing | [`draw_object_sprites`](../../src/sprite_render.asm#L6) has copied all frames into buffer S | Waiting | [`draw_object_sprites`](../../src/sprite_render.asm#L6) [`$25DE`](../../src/sprite_render.asm#L57) |
| Waiting | the next frame IRQ | Drawing; the sprites show buffer S; S = 1 − S | [`apply_sprite_registers`](../../src/sprite_render.asm#L64) [`$25E8`](../reference/modules/sprite_render.md#apply_sprite_registers), [`show_sprite_buffer`](../../src/sprite_render.asm#L152) [`$2682-$269C`](../reference/modules/sprite_render.md#show_sprite_buffer) |
| Drawing | a frame IRQ | Drawing (no register write) | [`update_sprite_registers`](../../src/sprite_render.asm#L60) [`$25E5`](../../src/sprite_render.asm#L62) |

- **Code.** [`sprite_frame_shown`](../../src/sprite_render.asm#L334) becomes 0 only after the last copy. An IRQ in the middle of a drawing does not flip, so the screen never shows a half-drawn buffer.
- **Conclusion.** The main loop waits for [`frame_countdown`](../../src/constants.asm#L34) [`$48`](../reference/variables.md#frame_countdown) at the end of each pass, and a pass lasts at least 3 frames. So the IRQ shows each drawing before the next one starts. If two drawings ever came without an IRQ between them, the second would write the same hidden buffer again, because only the IRQ flips [`sprite_buffer_select`](../../src/sprite_render.asm#L331).
- **Observed.** In the snapshots, [`sprite_pointers`](../../src/vic_bank2.asm#L574) 0-4 are `$06-$0A` when [`sprite_buffer_select`](../../src/sprite_render.asm#L331) = 1 and `$0B-$0F` when it is 0, with [`sprite_frame_shown`](../../src/sprite_render.asm#L334) = 1 (for example `rooms/room00` and `rooms/room01`).

---------------------------------------------------------------------------------------------

## 7. The sprite buffer clears

[`draw_object_sprites`](../../src/sprite_render.asm#L6) skips inactive actors, so their blocks keep the last picture. These routines clear blocks:

| Routine | Range | Blocks | Called from |
|---|---|---|---|
| [`init_game_screen`](../../src/game_setup.asm#L6) [`$07C2`](../../src/game_setup.asm#L50) | `$8180-$83FF` (one loop of 256 with three stores: `$8180`, `$8280`, `$8300`) | 6-15 | [`title_screen`](../../src/title.asm#L6), [`game_over`](../../src/game_over.asm#L67) and the two calls in `restart.asm` |
| [`clear_sprite_blocks_6_7_11_12`](../../src/interrupts.asm#L26) [`$111D`](../reference/modules/interrupts.md#clear_sprite_blocks_6_7_11_12) | `$8180-$81FF`, `$82C0-$833F` | 6, 7, 11, 12 (Bruce) | nothing. **Observed**: not executed in any coverage run |
| [`clear_sprite_blocks_8_9_13_14`](../../src/interrupts.asm#L43) [`$1131`](../reference/modules/interrupts.md#clear_sprite_blocks_8_9_13_14) | `$8200-$827F`, `$8340-$83BF` | 8, 9, 13, 14 (Yamo) | [`remove_actor`](../../src/background_touch.asm#L280) [`$303F`](../../src/background_touch.asm#L309) for actor 1 |
| [`clear_sprite_blocks_10_15`](../../src/interrupts.asm#L59) [`$1145`](../reference/modules/interrupts.md#clear_sprite_blocks_10_15) | `$8280-$82BF`, `$83C0-$83FF` | 10, 15 (Ninja) | [`remove_actor`](../../src/background_touch.asm#L280) [`$3045`](../../src/background_touch.asm#L312) for the other actors |
| [`room18_init`](../../src/room_init.asm#L279) [`$3611`](../../src/room_init.asm#L292) | `$8340-$83BF` | 13, 14 | room 18 entry (the fireball shapes) |
| [`title_screen`](../../src/title.asm#L6) [`$059F`](../../src/title.asm#L19) | `$83C0-$83FF` | 15 | the title (the TM sign) |

- **Code.** The three routines in `interrupts.asm` keep A and X (they push and pull them).
- **Conclusion.** [`init_actor`](../../src/actors.asm#L6) points a new actor's sprites at the hidden buffer and enables them at once. Because [`remove_actor`](../../src/background_touch.asm#L280) cleared both buffers of the old actor, the new sprites show nothing until the next drawing, instead of the last picture of the actor before.

---------------------------------------------------------------------------------------------

## 8. The frame address tables (collision masks)

[`actor_frame_addr_lo`](../../src/actor_room_tables.asm#L9) [`$1167`](../reference/modules/actor_room_tables.md#actor_frame_addr_lo) / [`actor_frame_addr_hi`](../../src/actor_room_tables.asm#L38) [`$1239`](../reference/modules/actor_room_tables.md#actor_frame_addr_hi) do not point at the frame graphics. They point at 96-byte masks that [`build_collision_masks`](../../src/collision.asm#L21) [`$512F`](../reference/modules/collision.md#build_collision_masks) builds once at init from the same frames. The masks are for the pixel collision with the background; [combat_collision.md](combat_collision.md) describes their use.

| Entry | Value | Meaning |
|---|---|---|
| even f | `$9000-$9F60` or `$C000-$CA80` | The mask of the pose: body f ORed with overlay f+1. 71 different masks: 42 in `$9000-$9FBF`, 29 in `$C000-$CADF`. Frames with the same body graphics share a mask (for example frames 0, 42, 44, ..., 54 at `$9000`). |
| odd f | `$CAE0` ([`mask_buffer`](../../src/constants.asm#L150)) | The overlay is built into this scratch mask first, then ORed into the even mask. |
| odd f | `$00E0` (high byte 0) | No overlay: the scratch mask is cleared instead (the Ninja). |

Mask layout (**Code**, [`build_frame_mask`](../../src/collision.asm#L64) [`$517E`](../reference/modules/collision.md#build_frame_mask)): 3 columns of 32 bytes, column k at mask + 32·k, row r of the frame in byte r of each column. Column 0 holds the high nibble of the row's (left) byte, column 1 the low nibble. [`double_nibble_bits`](../../src/collision.asm#L133) [`$51FF`](../reference/modules/collision.md#double_nibble_bits) doubles each bit into a `%11` pair, so 1 frame bit = 2 mask bits = 2 screen pixels. Rows after the frame are 0.

- **Code.** For a wide frame, [`build_frame_mask`](../../src/collision.asm#L64) reads the right byte but [`double_nibble_bits`](../../src/collision.asm#L133) works on [`nibble_bits`](../../src/constants.asm#L25) [`$1F`](../reference/variables.md#nibble_bits), which is empty by then. Column 2 is always 0: the mask has only the left 8 bits of a wide frame.
- **Code.** The masks in the upper area run from `$C000` to `$CADF`: the last mask is at `$CA80-$CADF`.

---------------------------------------------------------------------------------------------

## 9. A worked example: Bruce's start pose

[`init_actor`](../../src/actors.asm#L6) sets pose 2 ([`actor_frame_rel_a`](../../src/actor_vars.asm#L198) = 2, [`actor_frame_a`](../../src/actor_vars.asm#L212) = 2); [`spawn_yamo`](../../src/actors.asm#L177) and [`spawn_ninja`](../../src/actors.asm#L355) then change it, Bruce keeps it. For Bruce (base 0) that is body frame 2 and overlay frame 3. **Observed:** the `rooms` snapshots of rooms 1-3 show exactly these frames in Bruce's blocks.

The table bytes, read from the image:

| Table | Frame 2 | Frame 3 |
|---|---|---|
| [`frame_src_lo`](../../src/sprite_data.asm#L43) | [`frame_src_lo+2`](../../src/sprite_data.asm#L43) [`$59BF`](../reference/modules/sprite_data.md#frame_src_lo) = `$46` | [`frame_src_lo+3`](../../src/sprite_data.asm#L43) [`$59C0`](../reference/modules/sprite_data.md#frame_src_lo) = `$67` |
| [`frame_src_hi`](../../src/sprite_data.asm#L72) | [`frame_src_hi+2`](../../src/sprite_data.asm#L72) [`$5A91`](../reference/modules/sprite_data.md#frame_src_hi) = `$66` → source `$6646` | [`frame_src_hi+3`](../../src/sprite_data.asm#L72) [`$5A92`](../reference/modules/sprite_data.md#frame_src_hi) = `$66` → source `$6667` |
| [`frame_height`](../../src/sprite_data.asm#L101) | [`frame_height+2`](../../src/sprite_data.asm#L101) [`$5B63`](../reference/modules/sprite_data.md#frame_height) = `$0B`: h = 11 | [`frame_height+3`](../../src/sprite_data.asm#L101) [`$5B64`](../reference/modules/sprite_data.md#frame_height) = `$14`: h = 20 |
| [`frame_colour`](../../src/sprite_data.asm#L130) | [`frame_colour+2`](../../src/sprite_data.asm#L130) [`$5C35`](../reference/modules/sprite_data.md#frame_colour) = `$F7`: yellow | [`frame_colour+3`](../../src/sprite_data.asm#L130) [`$5C36`](../reference/modules/sprite_data.md#frame_colour) = `$F0`: black |
| [`frame_wide_flag`](../../src/sprite_data.asm#L150) | [`frame_wide_flag+2`](../../src/sprite_data.asm#L150) [`$5CC1`](../reference/modules/sprite_data.md#frame_wide_flag) = 0: narrow, 12 rows | [`frame_wide_flag+3`](../../src/sprite_data.asm#L150) [`$5CC2`](../reference/modules/sprite_data.md#frame_wide_flag) = 0: narrow, 21 rows |

Frame 2 is copied with Y = 3·11 = 33. The rows go to offsets 33, 30, ..., 0 of the block; every other byte is 0. In buffer 0 the block is `$8180` (sprite 0), in buffer 1 `$82C0`. Frame 3 goes with Y = 60 to `$81C0` or `$8300` (sprite 1).

| Row | Frame 2 byte | Block offset | Frame 3 byte | Block offset |
|---|---|---|---|---|
| 0 | `$6646` = `$00` | 0 | `$6667` = `$30` | 0 |
| 1 | `$6647` = `$10` | 3 | `$6668` = `$60` | 3 |
| 2 | `$6648` = `$30` | 6 | `$6669` = `$48` | 6 |
| 3 | `$6649` = `$28` | 9 | `$666A` = `$50` | 9 |
| 4 | `$664A` = `$38` | 12 | `$666B` = `$40` | 12 |
| 5 | `$664B` = `$38` | 15 | `$666C` = `$00` | 15 |
| 6 | `$664C` = `$30` | 18 | `$666D` = `$00` | 18 |
| 7 | `$664D` = `$70` | 21 | `$666E` = `$00` | 21 |
| 8 | `$664E` = `$78` | 24 | `$666F` = `$00` | 24 |
| 9 | `$664F` = `$6C` | 27 | `$6670` = `$11` | 27 |
| 10 | `$6650` = `$4E` | 30 | `$6671` = `$31` | 30 |
| 11 | `$6651` = `$38` | 33 | `$6672` = `$00` | 33 |
| 12-20 | — (cleared) | 36-60 = 0 | `$6673-$667B` = `$38 $38 $2C $24 $24 $24 $24 $66 $E7` | 36-60 |

Frame 2 writes 34 bytes (offsets 0-33) and the clear writes 30 (34-63). Frame 3 writes 61 bytes (0-60) and the clear writes 3 (61-63).

The two sprites on top of each other, with the X expansion (`YY` = a yellow bit of the body in front, `BB` = a black bit of the overlay, `..` = transparent; each bit is 2 screen pixels):

```
row  body overlay  screen (16 pixels)
 0    00    30     ....BBBB........
 1    10    60     ..BBBBYY........
 2    30    48     ..BBYYYYBB......
 3    28    50     ..BBYYBBYY......
 4    38    40     ..BBYYYYYY......
 5    38    00     ....YYYYYY......
 6    30    00     ....YYYY........
 7    70    00     ..YYYYYY........
 8    78    00     ..YYYYYYYY......
 9    6C    11     ..YYYYBBYYYY..BB
10    4E    31     ..YYBBBBYYYYYYBB
11    38    00     ....YYYYYY......
12    --    38     ....BBBBBB......
13    --    38     ....BBBBBB......
14    --    2C     ....BB..BBBB....
15    --    24     ....BB....BB....
16    --    24     ....BB....BB....
17    --    24     ....BB....BB....
18    --    24     ....BB....BB....
19    --    66     ..BBBB....BBBB..
20    --    E7     BBBBBB....BBBBBB
```

The body gives the face, the arms and the yellow top; the overlay gives the black hair, the hands and the trousers.

The registers, for Bruce at the spawn point of room 0 ([`room_spawn_x`](../../src/room_tables.asm#L156) [`$4BAE`](../reference/modules/room_tables.md#room_spawn_x) = `$1A`, [`room_spawn_y`](../../src/room_tables.asm#L161) [`$4BC2`](../reference/modules/room_tables.md#room_spawn_y) = `$C4`): both frames are narrow, so no X shift. Sprite X = 2 · `$1A` = `$34` (52), bit 0 of [`MSIGX`](../../src/constants.asm#L157) clear. Sprite Y = `$C4` + `$1D` = `$E1`. Colours: `$F7` to [`SP0COL`](../../src/constants.asm#L174) [`$D027`](../reference/variables.md#SP0COL) (sprite 0), `$F0` to `$D028` (sprite 1).

A wide frame for comparison: frame 5 (overlay of pose 4, [`frame_wide_flag+5`](../../src/sprite_data.asm#L150) [`$5CC4`](../reference/modules/sprite_data.md#frame_wide_flag) = `$01`, h = 12, source `$6725`). Its row 5 is the two bytes `$672F-$6730` = `$01 $F8`. They go to offsets 15 and 16, and offset 17 is 0: `..............############......` on the screen (32 pixels). Pose 4 faces left, so both sprites of the pose move 16 pixels left (steps 5 and 9 of section 5.5).

---------------------------------------------------------------------------------------------

## 10. The assets

The sheets of `tools/extract_assets.py`, made from the frame tables with the decoder of section 4. Top part of each sheet: the 35 poses, body and overlay together, 7 per row. Bottom part: the 70 single frames in frame order, 10 per row. The pose sheets place the overlay with the X shifts of section 5.5; `frames.json` gives the placement it used (`pair_facing_assumed`, `pair_offsets`).

Bruce Lee, frames 0-69 (yellow body, black overlay):

![Bruce Lee: the 35 poses and the 70 frames](../../assets/sprites/bruce.png)

Yamo, frames 70-139 (green body, black overlay):

![Yamo: the 35 poses and the 70 frames](../../assets/sprites/yamo.png)

The Ninja, frames 140-209 (black, no overlay):

![The Ninja: the 35 poses and the 70 frames](../../assets/sprites/ninja.png)

The title's TM sign, block 15 with rows 4-7 from [`tm_sprite_rows`](../../src/title_options.asm#L24) [`$0E40`](../reference/modules/title_options.md#tm_sprite_rows):

![The TM sign sprite of the title](../../assets/sprites/tm_sprite.png)

The reference draws [`frame_graphics`](../../src/sprite_data.asm#L167) [`$5D91-$68F8`](../reference/graphics.md#frame_graphics) as a plain bitmap: 8-byte cells, 40 per row. The frames are not visible as figures in it; it shows the density of the area and the free bytes. Hires:

![frame_graphics as raw 8x8 cells, hires](../reference/images/frame_graphics-hires.png)

The same bytes read as multicolour (not how the game shows them):

![frame_graphics as raw 8x8 cells, multicolour](../reference/images/frame_graphics-multicolour.png)

Data files:
- [frames.json](../../assets/sprites/frames.json): per frame the source address, height, wide flag, colour, actor, mask address, raw bytes and sheet position.
- [actor_frame_addr.json](../../assets/tables/actor_frame_addr.json): the 210 entries of [`actor_frame_addr_lo`](../../src/actor_room_tables.asm#L9) / [`actor_frame_addr_hi`](../../src/actor_room_tables.asm#L38).
- [tm_sprite.bin](../../assets/sprites/tm_sprite.bin): the 63 bytes of the TM sprite.

---------------------------------------------------------------------------------------------

## 11. The Apple II source text at `$5900`

[`leftover_source_text`](../../src/sprite_data.asm#L6) [`$5900-$59A4`](../reference/modules/sprite_data.md#leftover_source_text) sits in front of the frame tables. No code of the game refers to it (**Code**: no reference in the knowledge). The coverage shows reads of `$5900-$598F` in some run; which code read them is in section 13. Its bytes are ASCII with bit 7 set (`$8D` ends a line, `$A0` is a space); the spaces inside the `* CHAR` lines are `$20`. Decoded:

```
0F,$33,$FF,$FF
 DFB $FF,$0C,$03,$C3
* CHAR 97
 DFB $F0,$C0,$00,$00
 DFB $3F,$FC,$F0,$03
* CHAR 98
 DFB $FA,$FA,$FE,$FE
 DFB $FA,$3A,$BA,$AA
* CHAR 99
 DFB $FF,$CF,$F
```

- The text starts and ends in the middle of a line.
- **Conclusion.** It is a piece of an Apple II assembler source (`DFB` data lines, `*` comment lines, high-bit ASCII as Apple II editors store it): character definitions 97-99. It was left in memory when the C64 file was made. The knowledge names the assembler Merlin.

---------------------------------------------------------------------------------------------

## 12. Findings

| Finding | Evidence |
|---|---|
| Frame 129 (Yamo's overlay, pose `$3A`) has 22 rows. The copy writes 64 bytes, and [`clear_sprite_rest`](../../src/sprite_render.asm#L193) then writes one stray 0 at block + `$C0`: `$8300` (Bruce's overlay, buffer 1) or `$8440` (title font, already 0). | Code: [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) [`$26A0-$26D4`](../reference/modules/sprite_render.md#copy_frame_to_sprite), [`frame_height+129`](../../src/sprite_data.asm#L101) [`$5BE2`](../reference/modules/sprite_data.md#frame_height) = 21. The code that sets pose `$3A` ran for some actor (coverage of [`select_object_pose`](../../src/object_pose.asm#L6) [`$2821`](../../src/object_pose.asm#L94)); a run with Yamo in that pose is still open. |
| The Ninja's colour is fixed: [`setup_frame_source`](../../src/sprite_render.asm#L251) loads `$F0` for actor 2. [`frame_colour`](../../src/sprite_data.asm#L130) has only 140 entries, for Bruce and Yamo. | Code: [`setup_frame_source`](../../src/sprite_render.asm#L251) [`$2734-$273E`](../../src/sprite_render.asm#L261). |
| [`init_actor`](../../src/actors.asm#L6) writes a sprite pointer for sprite 5 when it places the Ninja (body sprite 4 + 1). Sprite 5 stays off. | Code: [`actor_place_sprites`](../../src/actors.asm#L105) [`$0C62-$0C66`](../../src/actors.asm#L116). Observed: pointer `$10`/`$0B` in the `rooms` snapshots. |
| The values 4-7 in [`actor_type_sprite_a`](../../src/sprite_data.asm#L32) / [`actor_type_sprite_b`](../../src/sprite_data.asm#L35) are [`sprite_owner`](../../src/actor_vars.asm#L184) slots, not the hardware sprites. The asset files call them VIC sprites. | Code: the renderer uses [`actor_body_sprite`](../../src/sprite_render.asm#L299) (0, 2, 4) and [`actor_overlay_sprite`](../../src/sprite_render.asm#L306) (1, 3, none). |
| A wide frame's right byte is not in its collision mask (column 2 of every mask is 0). | Code: [`build_frame_mask`](../../src/collision.asm#L64) [`$51EB-$51F4`](../../src/collision.asm#L120) and [`double_nibble_bits`](../../src/collision.asm#L133) [`$51FF`](../reference/modules/collision.md#double_nibble_bits). |
| [`clear_sprite_blocks_6_7_11_12`](../../src/interrupts.asm#L26) [`$111D`](../reference/modules/interrupts.md#clear_sprite_blocks_6_7_11_12) (Bruce's blocks) has no caller. | Code: no reference. Observed: not executed in any coverage run. |
| The call graph of [sprite_render.md](../reference/modules/sprite_render.md) shows a call from [`copy_frame_to_sprite`](../../src/sprite_render.asm#L169) to [`irq_handler`](../../src/interrupts.asm#L6) [`$1103`](../reference/modules/interrupts.md#irq_handler) and table arrows to the music jumps at `$E300-$E49E`. They come from the analyzer: the BRK byte at `$2703` and the placeholder operands `$E000`. The routine calls nothing. | Code: `$2703` is never executed; `$26AA`, `$26E3`, `$26ED` are patched by [`setup_frame_source`](../../src/sprite_render.asm#L251). |

---------------------------------------------------------------------------------------------

## 13. Still open

- Does the stray 0 of frame 129 ever show on the screen? A run in which Yamo reaches pose `$3A` (states `$13` or `$1B` of [`select_object_pose`](../../src/object_pose.asm#L6)) while the drawn buffer is 0, with a watchpoint on writes to `$8300` from `$26CE`, would answer it.
- [`spawn_ninja`](../../src/actors.asm#L355) [`$0DF8`](../reference/modules/actors.md#spawn_ninja) stores [`actor_frame_a`](../../src/actor_vars.asm#L212) = `$82` (frame 130, a Yamo frame) before any Ninja pose is set. Can a drawing show it in black before [`select_object_pose`](../../src/object_pose.asm#L6) runs for the Ninja? A breakpoint at [`draw_object_sprites`](../../src/sprite_render.asm#L6) in the pass in which [`try_spawn_ninja`](../../src/actors.asm#L315) spawns the Ninja, reading [`actor_frame_a+2`](../../src/actor_vars.asm#L212) [`$4F50`](../reference/modules/actor_vars.md#actor_frame_a), would answer it.
- Which code read `$5900-$598F` in the coverage runs? The reads are not from the renderer or the frame tables. A run with a read watchpoint on `$5900-$59A4` from the start of the loader would show it.
- The 42 bytes `$63C1-$63EA` that no frame uses: a frame that the C64 version dropped, or a gap of the original layout? Only an earlier release (Apple II, Atari) could tell.
