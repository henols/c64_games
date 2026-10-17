# Bruce Lee: the rooms

The game has 20 rooms. Each room is one screen. This page describes how the program stores a room, how it draws a
room, how a room runs its own code, and the hazards and lanterns that the rooms share. The page
[rooms_catalogue.md](rooms_catalogue.md) describes each room one by one.

**Scope.**

- The per-room tables: map pointers, colours, charset, raster palettes, exits and entry positions, start points,
  enemy timing, enemy-free rooms, lantern counts, lantern lists and the room aux blocks.
- The run-length map format, with a worked example from [`room_map_00`](../src/room_maps_00_04.asm#L18) [`$68F9`](reference/modules/room_maps_00_04.md#room_map_00).
- [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) step by step.
- The room init and room frame dispatch tables ([`room_init_handlers`](../src/room_dispatch.asm#L19) [`$4E9C`](reference/modules/room_dispatch.md#room_init_handlers), [`room_frame_handlers`](../src/room_dispatch.asm#L28) [`$4EC4`](reference/modules/room_dispatch.md#room_frame_handlers)).
- The lanterns: record format, pickup, redraw, reset, and the passages that open.
- The hazards: sliders, runners (and the room 13 floor movers), burst traps and the deadly characters.
- The map overflow bug of rooms 4, 7, 10, 13, 17 and 18.

**Sources.** `src/draw_room.asm`, `src/room_tables.asm`, `src/room_palettes.asm`, `src/room_enemy_tables.asm`,
`src/lantern_lists.asm`, `src/lantern_pickup.asm`, `src/room_dispatch.asm`, `src/room_specific_init.asm`,
`src/room_frames_0_7.asm`, `src/room_frames_8_11.asm`, `src/room_frames_12_17.asm`, `src/wizard_room.asm`,
`src/ending_room.asm`, `src/passage_open.asm`, `src/room_hazard_draw.asm`, `src/room_misc_support.asm`,
`src/background_touch.asm`, `src/touch_effects.asm`, `src/draw_helpers.asm`. The screenshots in `images/rooms/` come
from emulator runs, about 250 frames after Bruce entered each room.

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop). A pass takes 3 frames ([`frame_countdown`](../src/constants.asm#L38) [`$0048`](reference/variables.md#frame_countdown) = 3). An *even pass*
  is a pass with [`pass_parity`](../src/constants.asm#L76) [`$007B`](reference/variables.md#pass_parity) = 0; the main loop toggles it before it calls the room frame handler.
- A *cell* is one double-height character: character code c in the upper screen row, c+$80 in the row below.
- A *text line* L is a row of cells. Line 0 is the status line (screen row 0). Line L (1-12) uses screen rows
  2L-1 and 2L. The map fills lines 2-12 (screen rows 3-24). A *column* is 0-39. "L7 C31" is the cell at text
  line 7, column 31.
- A *tile* is a message of [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message): a string of cells drawn at a text line and a column. The room
  code calls messages tiles. "Tile $13" means message number $13 in [`message_ptrs`](../src/messages.asm#L11) [`$43BE`](reference/modules/messages.md#message_ptrs).
- An *exit marker* is a cell with code 2, 3, 4 or 5 (code AND $7F). Marker N uses the exit tables of set N.
- A room is *cleared* when [`room_lanterns_left`](../src/constants.asm#L33) [`$002A`](reference/variables.md#room_lanterns_left) + room = 0.
- **Observed** marks a fact that a run showed (the coverage runs, the room screenshots, the runs of the analysis
  notes). **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## 1. Overview

A room change, a game start, the demo start and the restart after a lost fall all end in [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room).
[`draw_room`](../src/draw_room.asm#L28) draws the map, redraws the taken lanterns, runs the room init handler and then runs the room frame
handler one time. After that [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) runs the room frame handler once per pass.

~~~mermaid
flowchart TB
  CR["change_room $2F9A"] --> DR["draw_room $09BC"]
  PB["place_bruce_at_room_start $3217"] --> ER["enter_room $2F8E"] --> CR
  SG["start_new_game $070E"] --> DR
  SD["start_attract_demo $0531"] --> DR
  DR --> MAP["draw_room_next_code $0AD7 (map decoder)"]
  MAP --> SL["setup_room_lanterns_and_init $336E"]
  SL --> CV["room_init_clear_vars $33B3"]
  CV --> ID["room_init_dispatch $33BD"]
  ID --> INIT["roomNN_init (room_init_handlers $4E9C)"]
  DR --> RF["run_room_frame_handler $3A6F"]
  ML["main_loop $1BC2"] --> RF
  RF --> FR["roomNN_frame (room_frame_handlers $4EC4)"]
  ML --> BT["check_background_touch $2E39"]
  BT --> HT["handle_touched_tile $2E89"]
  HT --> TX["take_exit2..5 $2F3C-$2F7B"] --> ER
  HT --> CL["collect_lantern $2F04"] --> CP["check_lantern_pickup $331C"]
~~~

| Node | Role |
|---|---|
| [`change_room`](../src/background_touch.asm#L234) [`$2F9A`](reference/modules/background_touch.md#change_room) | Bruce leaves the room: stores his entry X/Y, sets [`room`](../src/constants.asm#L32) [`$0029`](reference/variables.md#room), removes the enemies, draws the new room. |
| [`place_bruce_at_room_start`](../src/room_misc_support.asm#L11) [`$3217`](reference/modules/room_misc_support.md#place_bruce_at_room_start) | Enters room X at its start point A. Used by [`lose_fall`](../src/lose_fall_game_over.asm#L14) [`$1818`](reference/modules/lose_fall_game_over.md#lose_fall), the room 11 rule of [`draw_room`](../src/draw_room.asm#L28), and [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame). |
| [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) | Draws the room and resets the per-room state (section 4). |
| [`setup_room_lanterns_and_init`](../src/lantern_pickup.asm#L79) [`$336E`](reference/modules/lantern_pickup.md#setup_room_lanterns_and_init) | Redraws the taken lanterns, clears [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) .. [`room_state_e`](../src/room_dispatch.asm#L15) [`$4E9B`](reference/modules/room_dispatch.md#room_state_e), jumps to the init handler. |
| [`run_room_frame_handler`](../src/passage_open.asm#L18) [`$3A6F`](reference/modules/passage_open.md#run_room_frame_handler) | Jumps to the frame handler of the room (section 5). |
| [`check_background_touch`](../src/background_touch.asm#L10) [`$2E39`](reference/modules/background_touch.md#check_background_touch) | Each pass: the characters under each actor (exits, lanterns, deadly characters, traps). |

## 2. The per-room tables

All per-room tables have 20 entries, index = [`room`](../src/constants.asm#L32) [`$0029`](reference/variables.md#room) (0-19). **Code**.

| Name | Address | Layout | Readers | Writers |
|---|---|---|---|---|
| [`room_map_ptr_lo`](../src/room_tables.asm#L69) / [`room_map_ptr_hi`](../src/room_tables.asm#L73) | `$4B34` / `$4B49` | 21 bytes each: low and high bytes of the map address. Entry 20 repeats [`room_map_19`](../src/room_maps_15_19.asm#L158) [`$7FE0`](reference/modules/room_maps_15_19.md#room_map_19) and is not used. | [`draw_room`](../src/draw_room.asm#L28) | - |
| [`room_colour_fill`](../src/room_palettes.asm#L13) | `$47A0` | 1 byte: colour RAM value of the play area. Bit 3 = multicolour, bits 0-2 = colour of the %11 pixels. | [`draw_room`](../src/draw_room.asm#L28) | - |
| [`room_palette_ptr`](../src/room_palettes.asm#L75) | `$480B` | 1 word: address of the band palette records (3 bytes BGCOL0, BGCOL1, BGCOL2 per band). | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | - |
| [`room_split_list_ptr`](../src/room_palettes.asm#L82) | `$4833` | 1 word: address of the raster split list (raster lines, end $FD). | [`irq_game_bottom`](../src/game_irq.asm#L12) | - |
| [`room_aux_ptr`](../src/room_tables.asm#L26) | `$4AA8` | 1 word: address of a 20-byte block. No effect (section 2.6). | [`draw_room`](../src/draw_room.asm#L28) | - |
| [`exit2_dest_room`](../src/room_tables.asm#L78) .. [`exit5_dest_room`](../src/room_tables.asm#L95) | `$4B5E`, `$4B72`, `$4B86`, `$4B9A` | 1 byte: destination room of exit marker 2, 3, 4, 5. | [`take_exit2`](../src/background_touch.asm#L178) .. [`take_exit5`](../src/background_touch.asm#L210) | - |
| [`exit2_entry_x`](../src/room_tables.asm#L121) .. [`exit5_entry_x`](../src/room_tables.asm#L151) | `$4BFE`, `$4C26`, `$4C4E`, `$4C76` | 1 byte: Bruce's X in the new room. 0 = no exit for this marker. | [`take_exit2`](../src/background_touch.asm#L178) .. [`take_exit5`](../src/background_touch.asm#L210) | - |
| [`exit2_entry_y`](../src/room_tables.asm#L126) .. [`exit5_entry_y`](../src/room_tables.asm#L156) | `$4C12`, `$4C3A`, `$4C62`, `$4C8A` | 1 byte: Bruce's Y in the new room. | [`take_exit2`](../src/background_touch.asm#L178) .. [`take_exit5`](../src/background_touch.asm#L210) | - |
| [`spawn_a_x`](../src/room_tables.asm#L101) / [`spawn_a_y`](../src/room_tables.asm#L106) | `$4BAE` / `$4BC2` | Start point A: Bruce's start position, and one enemy start point. | [`place_bruce_at_room_start`](../src/room_misc_support.asm#L11), [`spawn_actor`](../src/actor_spawn.asm#L20) [`$0B8E`](reference/modules/actor_spawn.md#spawn_actor) | - |
| [`spawn_b_x`](../src/room_tables.asm#L111) / [`spawn_b_y`](../src/room_tables.asm#L116) | `$4BD6` / `$4BEA` | Start point B: the other enemy start point. | [`spawn_actor`](../src/actor_spawn.asm#L20) | - |
| [`room_no_enemies`](../src/room_tables.asm#L164) | `$4C9E` | $FF = no Yamo and no Ninja in the room, 0 = enemies. | [`draw_room`](../src/draw_room.asm#L28), [`main_loop`](../src/game_main_loop.asm#L23) | - |
| [`ninja_room_delay`](../src/room_enemy_tables.asm#L75) / [`ninja_respawn_delay`](../src/room_enemy_tables.asm#L81) | `$130B` / `$131F` | Passes before the Ninja first appears / appears again. | [`draw_room`](../src/draw_room.asm#L28), [`update_ninja_spawn`](../src/actor_spawn.asm#L355) [`$0DB1`](reference/modules/actor_spawn.md#update_ninja_spawn), [`reset_spawn_timer`](../src/actor_spawn.asm#L274) [`$0D42`](reference/modules/actor_spawn.md#reset_spawn_timer) | - |
| [`ninja_spawn_side`](../src/room_enemy_tables.asm#L87) | `$1333` | Ninja start point; only tested for 0. | [`spawn_actor`](../src/actor_spawn.asm#L20) | - |
| [`yamo_room_delay`](../src/room_enemy_tables.asm#L94) / [`yamo_respawn_delay`](../src/room_enemy_tables.asm#L100) | `$1347` / `$135B` | Passes before Yamo first appears / appears again. | [`draw_room`](../src/draw_room.asm#L28), [`update_yamo_spawn`](../src/actor_spawn.asm#L238) [`$0D0F`](reference/modules/actor_spawn.md#update_yamo_spawn), [`reset_spawn_timer`](../src/actor_spawn.asm#L274) | - |
| [`yamo_spawn_side`](../src/room_enemy_tables.asm#L107) | `$136F` | Start point of Yamo (and of the Ninja): 0 = random; else 3 times in 4 bit 7 selects (clear = A, set = B). | [`spawn_actor`](../src/actor_spawn.asm#L20) | - |
| [`room_lantern_count_init`](../src/lantern_counts.asm#L7) | `$4CCE` | Lanterns of the room at a game start. | [`reset_lantern_counts`](../src/game_setup.asm#L242) [`$10C5`](reference/modules/game_setup.md#reset_lantern_counts) | - |
| [`lantern_list_ptr`](../src/lantern_lists.asm#L13) | `$4CE2` | 21 words: address of the lantern list of the room (entry 20 = [`lantern_list_spare`](../src/lantern_lists.asm#L104) [`$4E90`](reference/modules/lantern_lists.md#lantern_list_spare), not used). | [`check_lantern_pickup`](../src/lantern_pickup.asm#L15), [`setup_room_lanterns_and_init`](../src/lantern_pickup.asm#L79), [`reset_room_lanterns`](../src/lantern_pickup.asm#L160) [`$33DA`](reference/modules/lantern_pickup.md#reset_room_lanterns), [`swap_player_lanterns`](../src/game_setup.asm#L96) [`$0FED`](reference/modules/game_setup.md#swap_player_lanterns) | - |
| [`room_init_handlers`](../src/room_dispatch.asm#L19) | `$4E9C` | 1 word: init handler address - 1 (RTS table). | [`room_init_dispatch`](../src/lantern_pickup.asm#L136) [`$33BD`](reference/modules/lantern_pickup.md#room_init_dispatch) | - |
| [`room_frame_handlers`](../src/room_dispatch.asm#L28) | `$4EC4` | 1 word: frame handler address - 1 (RTS table). | [`run_room_frame_handler`](../src/passage_open.asm#L18) [`$3A6F`](reference/modules/passage_open.md#run_room_frame_handler) | - |

The RAM variables per room:

| Name | Address | Layout | Readers | Writers |
|---|---|---|---|---|
| [`room_lanterns_left`](../src/constants.asm#L33) | `$002A-$003D` | 1 byte per room: lanterns not yet taken. | room frame handlers, [`draw_room`](../src/draw_room.asm#L28) | [`reset_lantern_counts`](../src/game_setup.asm#L242), [`check_lantern_pickup`](../src/lantern_pickup.asm#L15) |
| [`room_unvisited`](../src/constants.asm#L152) | `$0300-$0327` | 1 byte per room and player at room*2 + [`current_player`](../src/constants.asm#L14) [`$0003`](reference/variables.md#current_player): 1 = not yet visited. | [`draw_room`](../src/draw_room.asm#L28) | [`init_game_variables`](../src/game_setup.asm#L18) [`$0F72`](reference/modules/game_setup.md#init_game_variables), [`reset_unvisited_rooms`](../src/game_setup.asm#L268) [`$10E0`](reference/modules/game_setup.md#reset_unvisited_rooms), [`draw_room`](../src/draw_room.asm#L28) |
| [`room_state_a`](../src/room_dispatch.asm#L7) .. [`room_state_e`](../src/room_dispatch.asm#L15) | `$4E97-$4E9B` | Five scratch bytes of the current room: timers, step counters and one-shot flags. | room handlers | [`room_init_clear_vars`](../src/lantern_pickup.asm#L128), room handlers |

### 2.1 Graphics of each room

[`draw_room`](../src/draw_room.asm#L28) sets [`room_vmcsb`](../src/constants.asm#L121) [`$00F2`](reference/variables.md#room_vmcsb) (the VMCSB value that the raster interrupt writes for the play area): $38 =
[`charset_rooms_0_9`](../src/constants.asm#L204) [`$A000`](reference/variables.md#charset_rooms_0_9) for rooms 0-9, $3C = [`charset_wizard`](../src/constants.asm#L206) [`$B000`](reference/variables.md#charset_wizard) for room 18, $3A =
[`charset_rooms_10_19`](../src/constants.asm#L205) [`$A800`](reference/variables.md#charset_rooms_10_19) for the others. The cold start expands the charset sources [`room_charset_a`](../src/room_charset_a.asm#L12) [`$9000`](reference/graphics.md#room_charset_a),
[`room_charset_b`](../src/room_charset_b.asm#L6) [`$9400`](reference/graphics.md#room_charset_b), [`room_charset_c`](../src/room_charset_c.asm#L6) [`$9800`](reference/graphics.md#room_charset_c) and [`room_charset_d`](../src/room_charset_d.asm#L8) [`$9C00`](reference/graphics.md#room_charset_d) into these charsets. The raster
interrupt copies 12 bytes from [`room_palette_ptr`](../src/room_palettes.asm#L75) and the split list from [`room_split_list_ptr`](../src/room_palettes.asm#L82) every frame, so a
room can have up to 4 colour bands. **Code.** The background colours in the table match the screenshots
(**Observed**).

| Room | Map | Bytes | Colour fill | Charset | Palette records | Split lines | Bands BGCOL0, BGCOL1, BGCOL2 |
|---|---|---|---|---|---|---|---|
| 0 | [`room_map_00`](../src/room_maps_00_04.asm#L18) [`$68F9`](reference/modules/room_maps_00_04.md#room_map_00) | 272 | $FE | $38 | [`room_palette_r0_3`](../src/room_palettes.asm#L29) [`$47C8`](reference/modules/room_palettes.md#room_palette_r0_3) | [`split_list_r0`](../src/room_palettes.asm#L60) [`$47F9`](reference/modules/room_palettes.md#split_list_r0): $78, $97 | 11,1,14 / 11,2,1 / 12,2,1 |
| 1 | [`room_map_01`](../src/room_maps_00_04.asm#L55) [`$6A09`](reference/modules/room_maps_00_04.md#room_map_01) | 309 | $FE | $38 | [`room_palette_r0_3`](../src/room_palettes.asm#L29) | [`split_list_r1`](../src/room_palettes.asm#L62) [`$47FC`](reference/modules/room_palettes.md#split_list_r1): $78, $97 | as room 0 |
| 2 | [`room_map_02`](../src/room_maps_00_04.asm#L97) [`$6B3E`](reference/modules/room_maps_00_04.md#room_map_02) | 351 | $FE | $38 | [`room_palette_r0_3`](../src/room_palettes.asm#L29) | [`split_list_r2`](../src/room_palettes.asm#L64) [`$47FF`](reference/modules/room_palettes.md#split_list_r2): $78, $97 | as room 0 |
| 3 | [`room_map_03`](../src/room_maps_00_04.asm#L144) [`$6C9D`](reference/modules/room_maps_00_04.md#room_map_03) | 382 | $FE | $38 | [`room_palette_r0_3`](../src/room_palettes.asm#L29) | [`split_list_r3`](../src/room_palettes.asm#L66) [`$4802`](reference/modules/room_palettes.md#split_list_r3): $62, $97 | as room 0 |
| 4 | [`room_map_04`](../src/room_maps_00_04.asm#L197) [`$6E1B`](reference/modules/room_maps_00_04.md#room_map_04) | 359 | $FC | $38 | [`room_palette_r4_6`](../src/room_palettes.asm#L33) [`$47D1`](reference/modules/room_palettes.md#room_palette_r4_6) | [`split_list_none`](../src/room_palettes.asm#L68) [`$4805`](reference/modules/room_palettes.md#split_list_none) | 6,14,1 |
| 5 | [`room_map_05`](../src/room_maps_05_09.asm#L7) [`$6F82`](reference/modules/room_maps_05_09.md#room_map_05) | 347 | $FC | $38 | [`room_palette_r4_6`](../src/room_palettes.asm#L33) | none | 6,14,1 |
| 6 | [`room_map_06`](../src/room_maps_05_09.asm#L54) [`$70DD`](reference/modules/room_maps_05_09.md#room_map_06) | 330 | $FC | $38 | [`room_palette_r4_6`](../src/room_palettes.asm#L33) | none | 6,14,1 |
| 7 | [`room_map_07`](../src/room_maps_05_09.asm#L101) [`$7227`](reference/modules/room_maps_05_09.md#room_map_07) | 234 | $FF | $38 | [`room_palette_r7_9`](../src/room_palettes.asm#L35) [`$47D4`](reference/modules/room_palettes.md#room_palette_r7_9) | none | 8,9,1 |
| 8 | [`room_map_08`](../src/room_maps_05_09.asm#L134) [`$7311`](reference/modules/room_maps_05_09.md#room_map_08) | 384 | $FA | $38 | [`room_palette_r7_9`](../src/room_palettes.asm#L35) | none | 8,9,1 |
| 9 | [`room_map_09`](../src/room_maps_05_09.asm#L185) [`$7491`](reference/modules/room_maps_05_09.md#room_map_09) | 327 | $FA | $38 | [`room_palette_r7_9`](../src/room_palettes.asm#L35) | none | 8,9,1 |
| 10 | [`room_map_10`](../src/room_maps_10_14.asm#L9) [`$75D8`](reference/modules/room_maps_10_14.md#room_map_10) | 372 | $F9 | $3A | [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37) [`$47D7`](reference/modules/room_palettes.md#room_palette_r10_12_14_16) | [`split_list_r10_12_14_16`](../src/room_palettes.asm#L70) [`$4806`](reference/modules/room_palettes.md#split_list_r10_12_14_16): $56 | 6,14,11 / 12,14,11 |
| 11 | [`room_map_11`](../src/room_maps_10_14.asm#L59) [`$774C`](reference/modules/room_maps_10_14.md#room_map_11) | 247 | $FB | $3A | [`room_palette_r11`](../src/room_palettes.asm#L40) [`$47DD`](reference/modules/room_palettes.md#room_palette_r11) | none | 4,14,11 |
| 12 | [`room_map_12`](../src/room_maps_10_14.asm#L93) [`$7843`](reference/modules/room_maps_10_14.md#room_map_12) | 387 | $F9 | $3A | [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37) | $56 | 6,14,11 / 12,14,11 |
| 13 | [`room_map_13`](../src/room_maps_10_14.asm#L147) [`$79C6`](reference/modules/room_maps_10_14.md#room_map_13) | 128 | $FA | $3A | [`room_palette_r13`](../src/room_palettes.asm#L42) [`$47E0`](reference/modules/room_palettes.md#room_palette_r13) | none | 14,6,1 |
| 14 | [`room_map_14`](../src/room_maps_10_14.asm#L166) [`$7A46`](reference/modules/room_maps_10_14.md#room_map_14) | 366 | $F9 | $3A | [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37) | $56 | 6,14,11 / 12,14,11 |
| 15 | [`room_map_15`](../src/room_maps_15_19.asm#L7) [`$7BB4`](reference/modules/room_maps_15_19.md#room_map_15) | 168 | $FC | $3A | [`room_palette_r15`](../src/room_palettes.asm#L44) [`$47E3`](reference/modules/room_palettes.md#room_palette_r15) | [`split_list_r15`](../src/room_palettes.asm#L72) [`$4808`](reference/modules/room_palettes.md#split_list_r15): $B6, $C7 | 14,6,11 / 12,14,1 / 15,8,12 |
| 16 | [`room_map_16`](../src/room_maps_15_19.asm#L31) [`$7C5C`](reference/modules/room_maps_15_19.md#room_map_16) | 305 | $F9 | $3A | [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37) | $56 | 6,14,11 / 12,14,11 |
| 17 | [`room_map_17`](../src/room_maps_15_19.asm#L75) [`$7D8D`](reference/modules/room_maps_15_19.md#room_map_17) | 259 | $FF | $3A | [`room_palette_r17`](../src/room_palettes.asm#L48) [`$47EC`](reference/modules/room_palettes.md#room_palette_r17) | none | 12,8,11 |
| 18 | [`room_map_18`](../src/room_maps_15_19.asm#L113) [`$7E90`](reference/modules/room_maps_15_19.md#room_map_18) | 336 | $FE | $3C | [`room_palette_r18`](../src/room_palettes.asm#L50) [`$47EF`](reference/modules/room_palettes.md#room_palette_r18) | none | 0,14,4 |
| 19 | [`room_map_19`](../src/room_maps_15_19.asm#L158) [`$7FE0`](reference/modules/room_maps_15_19.md#room_map_19) | 416 | $FF | $3A | [`room_palette_r19`](../src/room_palettes.asm#L52) [`$47F2`](reference/modules/room_palettes.md#room_palette_r19) | none | 6,2,1 |

A split line is the raster line where the next band starts; the colours change 3 lines later. The colour of a
band record is the low nibble of each byte.

![The 128 tiles of room_charset_a, used by rooms 0-9](reference/images/room_charset_a-multicolour.png)

The image shows the source charset of rooms 0-9 in multicolour, before the cold start doubles each tile in height.

### 2.2 Exits and entry positions

[`check_background_touch`](../src/background_touch.asm#L10) [`$2E39`](reference/modules/background_touch.md#check_background_touch) reads 3 characters of the actor's text line and 3 of the line below.
[`handle_touched_tile`](../src/background_touch.asm#L61) [`$2E89`](reference/modules/background_touch.md#handle_touched_tile) tests them in the order 5, 2, 3, 4 and jumps to [`take_exit5`](../src/background_touch.asm#L210) [`$2F7B`](reference/modules/background_touch.md#take_exit5),
[`take_exit2`](../src/background_touch.asm#L178) [`$2F3C`](reference/modules/background_touch.md#take_exit2), [`take_exit3`](../src/background_touch.asm#L189) [`$2F51`](reference/modules/background_touch.md#take_exit3) or [`take_exit4`](../src/background_touch.asm#L199) [`$2F66`](reference/modules/background_touch.md#take_exit4). **Code.**

1. [`check_exit_edge`](../src/touch_effects.asm#L154) [`$30D4`](reference/modules/touch_effects.md#check_exit_edge) allows the exit (carry clear) only at a screen edge, moving toward it: left
   [`actor_x`](../src/constants.asm#L94) [`$009E`](reference/variables.md#actor_x) < $10 after a move left, right [`actor_x`](../src/constants.asm#L94) > $A1 after a move right, bottom [`actor_y`](../src/constants.asm#L95) [`$00A1`](reference/variables.md#actor_y) >
   $C5 while falling (state $0E), top [`actor_y`](../src/constants.asm#L95) < $31 after a move up. In room 11 an exit is always allowed.
2. `take_exitN` loads [`next_room`](../src/constants.asm#L42) [`$004E`](reference/variables.md#next_room) = exitN_dest_room[room], Y = exitN_entry_y[room], A =
   exitN_entry_x[room].
3. When the entry X is 0, the code falls through into `take_exit(N+1)`. So a marker with entry X 0 acts as the next
   marker. [`take_exit5`](../src/background_touch.asm#L210) does not test the entry X.
4. [`enter_room`](../src/background_touch.asm#L222) [`$2F8E`](reference/modules/background_touch.md#enter_room): an enemy is only removed ([`remove_actor`](../src/touch_effects.asm#L38) [`$3001`](reference/modules/touch_effects.md#remove_actor)). For Bruce, [`change_room`](../src/background_touch.asm#L234) [`$2F9A`](reference/modules/background_touch.md#change_room)
   stores the position, sets [`room`](../src/constants.asm#L32), saves each active enemy's energy in [`enemy_follow_energy`](../src/constants.asm#L90) [`$008F`](reference/variables.md#enemy_follow_energy) and Bruce's
   entry point in [`enemy_follow_x`](../src/constants.asm#L88) [`$008B`](reference/variables.md#enemy_follow_x) / [`enemy_follow_y`](../src/constants.asm#L89) [`$008D`](reference/variables.md#enemy_follow_y) (the enemy comes back at that point), removes
   the enemies, restarts the spawn timers, resets the stack, calls [`draw_room`](../src/draw_room.asm#L28) and [`build_actor_sprites`](../src/actor_sprites.asm#L12) [`$2584`](reference/modules/actor_sprites.md#build_actor_sprites)
   and jumps to [`main_loop`](../src/game_main_loop.asm#L23).

The four exit sets, all 20 entries (destination room, entry X, entry Y; "-" = entry X 0):

| Room | Marker 2 | Marker 3 | Marker 4 | Marker 5 |
|---|---|---|---|---|
| 0 | 1, $10, $92 | - | - | 1, $0F, $62 |
| 1 | 0, $A0, $92 | 5, $2C, $32 | 0, $A1, $62 | 2, $10, $62 |
| 2 | - | - | 1, $A1, $62 | 3, $10, $C4 |
| 3 | - | 10, $10, $B0 | 2, $A1, $C5 | 0, $10, $62 |
| 4 | 5, $10, $C2 | 7, $1F, $32 | - | - |
| 5 | 4, $9C, $51 | 6, $10, $40 | 6, $10, $74 | 1, $58, $66 |
| 6 | 5, $A0, $80 | 5, $A0, $66 | 2, $16, $51 | 0, $20, $51 |
| 7 | 0, $30, $51 | 8, $0F, $46 | 8, $10, $C0 | 0, $20, $51 |
| 8 | 7, $A0, $74 | 9, $10, $53 | 7, $A1, $B5 | 9, $0F, $C6 |
| 9 | 8, $A0, $47 | 8, $A0, $C0 | 6, $9D, $C7 | - |
| 10 | 3, $A0, $C4 | 11, $10, $C4 | - | - |
| 11 | 10, $A0, $5A | 12, $10, $5C | 14, $10, $5E | 16, $10, $5C |
| 12 | - | 11, $34, $BE | 14, $10, $BE | - |
| 13 | 15, $10, $C3 | - | - | - |
| 14 | - | 11, $50, $BE | 12, $A0, $BE | 16, $10, $BE |
| 15 | 13, $A0, $C4 | 17, $10, $B3 | - | - |
| 16 | - | 11, $80, $BE | 14, $A0, $BE | - |
| 17 | 15, $A0, $93 | 18, $10, $C6 | - | - |
| 18 | 17, $A0, $44 | 19, $10, $96 | - | - (0, $00, $00) |
| 19 | - | - | - | - (0, $00, $00) |

The markers are cells of the maps or cells of tiles that the room code draws later. The catalogue gives the place
of each marker. Some table entries have no marker in the map and none in a tile of the room code: room 3 marker 5,
room 6 markers 3, 4 and 5, room 7 markers 2 and 5. **Code** (decode of the 20 maps and of the tiles that the
handlers draw). **Conclusion:** these exits cannot be used.

### 2.3 Start points and enemies

| Room | Start A (X, Y) | Start B (X, Y) | No enemies | Ninja first / again | Ninja side | Yamo first / again | Yamo side |
|---|---|---|---|---|---|---|---|
| 0 | $1A, $C4 | $9F, $62 | 0 | $68 / $A0 | $02 | $F0 / $EE | $80 |
| 1 | $18, $62 | $95, $92 | 0 | $78 / $A0 | $02 | $EE / $EE | $80 |
| 2 | $30, $C4 | $96, $C4 | 0 | $78 / $A0 | 0 | $EE / $EE | 0 |
| 3 | $20, $C0 | $38, $C4 | $FF | 0 / 0 | 0 | 0 / 0 | 0 |
| 4 | $94, $B4 | $96, $B4 | 0 | $70 / $70 | $80 | $C0 / $EE | $80 |
| 5 | $22, $51 | $28, $C2 | 0 | $18 / $0C | $80 | $C0 / $60 | $02 |
| 6 | $86, $B3 | $81, $72 | 0 | $30 / $30 | $02 | $A0 / $EE | 0 |
| 7 | $1C, $44 | $1F, $74 | 0 | $50 / $18 | $02 | $B0 / $C0 | $80 |
| 8 | $14, $46 | 0, 0 | $FF | 0 / 0 | 0 | 0 / 0 | 0 |
| 9 | $12, $C6 | 0, 0 | $FF | 0 / 0 | 0 | 0 / 0 | 0 |
| 10 | $34, $8C | $96, $5C | 0 | $08 / $0C | $02 | $30 / $30 | $80 |
| 11 | $40, $4C | 0, 0 | $FF | 0 / 0 | 0 | 0 / 0 | 0 |
| 12 | $18, $5C | $70, $5C | 0 | $04 / $04 | $80 | $20 / $20 | $80 |
| 13 | $98, $32 | 0, 0 | $FF | $12 / $08 | 0 | $C0 / $EE | 0 |
| 14 | $18, $5C | $92, $BE | 0 | $08 / $08 | $02 | $20 / $30 | 0 |
| 15 | $1C, $C3 | $7A, $C4 | 0 | $08 / $08 | 0 | $30 / $50 | 0 |
| 16 | $18, $5C | $81, $8E | 0 | $08 / $08 | $80 | $20 / $30 | $02 |
| 17 | $18, $B4 | 0, 0 | $FF | $12 / $08 | 0 | $C0 / $EE | 0 |
| 18 | $18, $C6 | 0, 0 | $FF | 0 / 0 | 0 | 0 / 0 | 0 |
| 19 | $12, $95 | 0, 0 | $FF | 0 / 0 | 0 | 0 / 0 | 0 |

- **Enemy-free rooms.** [`room_no_enemies`](../src/room_tables.asm#L164) [`$4C9E`](reference/modules/room_tables.md#room_no_enemies) is $FF for rooms 3, 8, 9, 11, 13, 17, 18 and 19. [`draw_room`](../src/draw_room.asm#L28)
  copies it to [`room_no_enemy_flag`](../src/constants.asm#L75) [`$007A`](reference/variables.md#room_no_enemy_flag). While it is nonzero, [`main_loop`](../src/game_main_loop.asm#L23) skips [`tick_spawn_timers`](../src/actor_spawn.asm#L341) [`$0DA4`](reference/modules/actor_spawn.md#tick_spawn_timers),
  [`update_yamo_spawn`](../src/actor_spawn.asm#L238) and [`update_ninja_spawn`](../src/actor_spawn.asm#L355), and skips [`check_fight_collisions`](../src/fight_hits.asm#L14) [`$29C3`](reference/modules/fight_hits.md#check_fight_collisions). Rooms 13 and 17 have delay
  values, but the flag makes them unused. **Code.**
- **Delays.** The units are passes. [`draw_room`](../src/draw_room.asm#L28) loads [`ninja_spawn_timer`](../src/constants.asm#L57) [`$005D`](reference/variables.md#ninja_spawn_timer) and [`yamo_spawn_timer`](../src/constants.asm#L58) [`$005E`](reference/variables.md#yamo_spawn_timer) from the "first"
  columns. When [`game_loop_count`](../src/constants.asm#L34) [`$0040`](reference/variables.md#game_loop_count) is not 0 (the game was completed once), both are 3. When player 2 controls
  Yamo, Yamo's timer is 8. **Code.**
- **Sides.** [`spawn_actor`](../src/actor_spawn.asm#L20) [`$0B8E`](reference/modules/actor_spawn.md#spawn_actor) tests [`ninja_spawn_side`](../src/room_enemy_tables.asm#L87) for 0 but takes the side bit from [`yamo_spawn_side`](../src/room_enemy_tables.asm#L107)
  (the Ninja path at [`spawn_actor_ninja_side`](../src/actor_spawn.asm#L103) [`$0C2A`](reference/modules/actor_spawn.md#spawn_actor_ninja_side)). **Code.** **Conclusion:** probably a slip of the original
  program; the rebuild keeps it.

### 2.4 Lantern counts

[`room_lantern_count_init`](../src/lantern_counts.asm#L7) [`$4CCE`](reference/modules/lantern_counts.md#room_lantern_count_init): 6, 6, 10, 2, 2, 10, 8, 13, 4, 5, 3, 3, 3, 0, 4, 6, 2, 2, 1, 0 (90 lanterns).
[`reset_lantern_counts`](../src/game_setup.asm#L242) [`$10C5`](reference/modules/game_setup.md#reset_lantern_counts) copies them to [`room_lanterns_left`](../src/constants.asm#L33) [`$002A`](reference/variables.md#room_lanterns_left) at a game start ([`init_game_variables`](../src/game_setup.asm#L18))
and when room 19 starts the next game loop. Each count equals the number of records in the room's lantern list.
**Code.**

### 2.5 Lantern lists

See section 6 for the format and the code. All 20 lists:

| Room | List | Lanterns | Replacement codes |
|---|---|---|---|
| 0 | [`lantern_list_room0`](../src/lantern_lists.asm#L21) [`$4D0C`](reference/modules/lantern_lists.md#lantern_list_room0) | L7 C31, L7 C38, L10 C2, L10 C25, L10 C29, L10 C38 | $9F $92 $9F $9F $92 $92 |
| 1 | [`lantern_list_room1`](../src/lantern_lists.asm#L26) [`$4D25`](reference/modules/lantern_lists.md#lantern_list_room1) | L7 C9, L7 C30, L10 C6, L10 C15, L10 C24, L10 C32 | $9E $9F $92 $9E $9F $92 |
| 2 | [`lantern_list_room2`](../src/lantern_lists.asm#L31) [`$4D3E`](reference/modules/lantern_lists.md#lantern_list_room2) | L7 C5, L7 C9, L7 C22, L7 C26, L7 C30, L10 C5, L10 C9, L10 C15, L10 C21, L10 C27 | $92 $9E $9F $9E $9F $9E $9F $9E $9F $9E |
| 3 | [`lantern_list_room3`](../src/lantern_lists.asm#L38) [`$4D67`](reference/modules/lantern_lists.md#lantern_list_room3) | L10 C29, L10 C38 | $9E $9F |
| 4 | [`lantern_list_room4`](../src/lantern_lists.asm#L41) [`$4D70`](reference/modules/lantern_lists.md#lantern_list_room4) | L4 C11, L4 C28 | $9E $9F |
| 5 | [`lantern_list_room5`](../src/lantern_lists.asm#L44) [`$4D79`](reference/modules/lantern_lists.md#lantern_list_room5) | L3 C2, L3 C6, L3 C28, L3 C32, L3 C38, L6 C30, L10 C2, L10 C23, L10 C26, L10 C30 | $9E $9E $9F $9E $9F $9F $9E $9F $9F $9E |
| 6 | [`lantern_list_room6`](../src/lantern_lists.asm#L51) [`$4DA2`](reference/modules/lantern_lists.md#lantern_list_room6) | L5 C8, L5 C10, L5 C14, L5 C22, L5 C26, L5 C28, L9 C6, L9 C30 | $9F $9E $9F $9F $9F $9E $9F $9E |
| 7 | [`lantern_list_room7`](../src/lantern_lists.asm#L57) [`$4DC3`](reference/modules/lantern_lists.md#lantern_list_room7) | L2 C3, L2 C12, L2 C13, L2 C25, L2 C26, L5 C5, L5 C6, L5 C12, L5 C13, L5 C25, L5 C26, L9 C2, L9 C3 | $9E $9F alternating |
| 8 | [`lantern_list_room8`](../src/lantern_lists.asm#L65) [`$4DF8`](reference/modules/lantern_lists.md#lantern_list_room8) | L3 C15, L3 C24, L7 C6, L7 C33 | $9F $9F $9E $9F |
| 9 | [`lantern_list_room9`](../src/lantern_lists.asm#L69) [`$4E09`](reference/modules/lantern_lists.md#lantern_list_room9) | L2 C32, L7 C15, L10 C27, L10 C28, L10 C32 | $9F $9E $9E $9F $9E |
| 10 | [`lantern_list_room10`](../src/lantern_lists.asm#L73) [`$4E1E`](reference/modules/lantern_lists.md#lantern_list_room10) | L4 C1, L7 C30, L10 C30 | $9F $9F $9F |
| 11 | [`lantern_list_room11`](../src/lantern_lists.asm#L76) [`$4E2B`](reference/modules/lantern_lists.md#lantern_list_room11) | L3 C18, L3 C21, L10 C7 | $9E $9F $9F |
| 12 | [`lantern_list_room12`](../src/lantern_lists.asm#L79) [`$4E38`](reference/modules/lantern_lists.md#lantern_list_room12) | L4 C36, L7 C36, L10 C36 | $9E $9E $9E |
| 13 | [`lantern_list_room13`](../src/lantern_lists.asm#L82) [`$4E45`](reference/modules/lantern_lists.md#lantern_list_room13) | dummy record 01 00 00 00 | - |
| 14 | [`lantern_list_room14`](../src/lantern_lists.asm#L84) [`$4E4A`](reference/modules/lantern_lists.md#lantern_list_room14) | L7 C9, L7 C30, L10 C9, L10 C30 | $9F $9E $9F $9E |
| 15 | [`lantern_list_room15`](../src/lantern_lists.asm#L88) [`$4E5B`](reference/modules/lantern_lists.md#lantern_list_room15) | L3 C19, L3 C21, L4 C14, L4 C26, L6 C13, L6 C27 | $9F $9E $9E $9F $9E $9F |
| 16 | [`lantern_list_room16`](../src/lantern_lists.asm#L93) [`$4E74`](reference/modules/lantern_lists.md#lantern_list_room16) | L4 C32, L7 C5 | $9E $9F |
| 17 | [`lantern_list_room17`](../src/lantern_lists.asm#L96) [`$4E7D`](reference/modules/lantern_lists.md#lantern_list_room17) | L10 C38, L11 C31 | $9E $9E |
| 18 | [`lantern_list_room18`](../src/lantern_lists.asm#L99) [`$4E86`](reference/modules/lantern_lists.md#lantern_list_room18) | L11 C37 | $9E |
| 19 | [`lantern_list_room19`](../src/lantern_lists.asm#L101) [`$4E8B`](reference/modules/lantern_lists.md#lantern_list_room19) | dummy record 01 00 00 00 | - |

The room code reads the state byte of single records by offset, for example [`lantern_list_room5+$20`](../src/lantern_lists.asm#L44) [`$4D99`](reference/modules/lantern_lists.md#lantern_list_room5) is the
lantern at L10 C26. The catalogue names each record that a handler tests.

### 2.6 The room aux blocks

[`room_aux_ptr`](../src/room_tables.asm#L26) [`$4AA8`](reference/modules/room_tables.md#room_aux_ptr) points each room at a block in `$4AD0-$4B33`: [`room_aux_r0_3`](../src/room_tables.asm#L33) [`$4AD0`](reference/modules/room_tables.md#room_aux_r0_3), [`room_aux_r4_6`](../src/room_tables.asm#L38) [`$4AE4`](reference/modules/room_tables.md#room_aux_r4_6)
, [`room_aux_r7_9`](../src/room_tables.asm#L40) [`$4AE9`](reference/modules/room_tables.md#room_aux_r7_9), [`room_aux_r10_12_14_16`](../src/room_tables.asm#L42) [`$4AEE`](reference/modules/room_tables.md#room_aux_r10_12_14_16), [`room_aux_r11`](../src/room_tables.asm#L46) [`$4AFD`](reference/modules/room_tables.md#room_aux_r11), [`room_aux_r13`](../src/room_tables.asm#L48) [`$4B02`](reference/modules/room_tables.md#room_aux_r13),
[`room_aux_r15`](../src/room_tables.asm#L51) [`$4B0C`](reference/modules/room_tables.md#room_aux_r15), [`room_aux_r17`](../src/room_tables.asm#L55) [`$4B1B`](reference/modules/room_tables.md#room_aux_r17), [`room_aux_r18`](../src/room_tables.asm#L58) [`$4B25`](reference/modules/room_tables.md#room_aux_r18), [`room_aux_r19`](../src/room_tables.asm#L60) [`$4B2A`](reference/modules/room_tables.md#room_aux_r19). The blocks are
groups of 5 bytes (for example $04,$00,$06,$88,$0E), and a block runs into the next ones. [`draw_room`](../src/draw_room.asm#L28) copies 20
bytes to [`room_band_colours`](../src/constants.asm#L150) [`$0153`](reference/variables.md#room_band_colours). [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) overwrites `$0153-$015E` every frame from
[`room_palette_ptr`](../src/room_palettes.asm#L75), and no code reads `$015F-$0166`. **Code**, and **Observed** in a trace of the analysis (a
store to `$0153` every frame). **Conclusion:** dead data, perhaps an older form of the band palettes.

## 3. The map format

**Where the data is.** [`room_map_ptr_lo`](../src/room_tables.asm#L69) [`$4B34`](reference/modules/room_tables.md#room_map_ptr_lo) / [`room_map_ptr_hi`](../src/room_tables.asm#L73) [`$4B49`](reference/modules/room_tables.md#room_map_ptr_hi) give the map of each room. The maps
are [`room_map_00`](../src/room_maps_00_04.asm#L18) [`$68F9`](reference/modules/room_maps_00_04.md#room_map_00) to [`room_map_19`](../src/room_maps_15_19.asm#L158) [`$7FE0`](reference/modules/room_maps_15_19.md#room_map_19) (`$68F9-$817F`), one after the other. [`draw_room`](../src/draw_room.asm#L28) decodes them
from [`draw_room_next_code`](../src/draw_room.asm#L178) [`$0AD7`](reference/modules/draw_room.md#draw_room_next_code).

**The byte layout.** A map is a stream of codes:

| Byte | Meaning |
|---|---|
| $80 | End of the map. |
| $81-$FF | Literal run: the next (byte AND $7F) bytes are cells. |
| $01-$7F | Repeat run: the next byte is a cell, drawn (byte) times. |
| $00 | Would repeat 256 times. No map uses it. |

A cell byte:

| Bits | Meaning |
|---|---|
| 0-6 | Character code c. Upper screen row c, lower screen row c OR $80. |
| 7 | 1 = colour RAM $F8 for both rows (multicolour, colour 0) through [`map_tile_set_black`](../src/draw_room.asm#L262) [`$0B5F`](reference/modules/draw_room.md#map_tile_set_black); 0 = the cell keeps [`room_colour_fill`](../src/room_palettes.asm#L13). |

The cells fill 40 columns per text line, from line 2 (screen row 3, `$8C78`) to line 12. One map gives 440 cells.

**The decoder** ([`draw_room`](../src/draw_room.asm#L28) [`$0AAF-$0B2F`](../src/draw_room.asm#L159)):

```
data_ptr   = map of room
top        = $8C78  ; screen row 3        colour_top    = $D878
bottom     = $8CA0  ; screen row 4        colour_bottom = $D8A0
column_counter = 39
loop:
  code = *data_ptr
  if code >= $80:
      n = code & $7F
      if n == 0: goto done
      data_ptr++
      repeat n times: put(*data_ptr); data_ptr++
  else:
      n = code; data_ptr++
      repeat n times: put(*data_ptr)
      data_ptr++
put(b):
  if b & $80: colour RAM at colour_top and colour_bottom = $F8; b = b & $7F
  *top = b; *bottom = b | $80
  top++, bottom++, colour_top++, colour_bottom++
  room_draw_step_cell: column_counter--; if it passes 0: column_counter = 39, all four pointers += 40
done:
  setup_room_lanterns_and_init
```

[`room_draw_step_cell`](../src/draw_helpers.asm#L9) [`$485B`](reference/modules/draw_helpers.md#room_draw_step_cell) adds 40 after each 40 cells, because the per-cell increments have already crossed one
screen row, and a cell is two rows high. **Code.**

### 3.1 Worked example: the first two lines of room 0

The bytes of [`room_map_00`](../src/room_maps_00_04.asm#L18) [`$68F9`](reference/modules/room_maps_00_04.md#room_map_00), decoded by hand. Line 2 starts at screen `$8C78` / `$8CA0` and colour RAM
`$D878` / `$D8A0`. Line 3 starts at `$8CC8` / `$8CF0`. Every cell byte with bit 7 set makes the cell's colour RAM $F8.

| Address | Bytes | Code | Cells |
|---|---|---|---|
| `$68F9` | 16 89 | repeat 22 | line 2, columns 0-21: cell $89 = char $09 (top), $89 (bottom), black |
| `$68FB` | 8D | literal 13 | - |
| `$68FC-$6908` | 8A A3 B5 B3 B5 B6 8A A3 B3 B5 A3 B5 B6 | 13 cells | line 2, columns 22-34: chars $0A $23 $35 $33 $35 $36 $0A $23 $33 $35 $23 $35 $36, all black |
| `$6909` | 05 89 | repeat 5 | line 2, columns 35-39: char $09, black. Line 2 is full (40 cells). |
| `$690B` | 84 A3 B3 B4 B3 | literal 4 | line 3, columns 0-3: chars $23 $33 $34 $33, black |
| `$6910` | 02 B4 | repeat 2 | line 3, columns 4-5: char $34, black |
| `$6912` | 86 B3 B4 B5 B6 A3 8C | literal 6 | line 3, columns 6-11: chars $33 $34 $35 $36 $23 $0C, black |
| `$6919` | 02 B4 | repeat 2 | line 3, columns 12-13: char $34, black |
| `$691B` | 88 B5 B6 8A A3 B5 B6 8A 8E | literal 8 | line 3, columns 14-21: chars $35 $36 $0A $23 $35 $36 $0A $0E, black |
| `$6924` | 03 00 | repeat 3 | line 3, columns 22-24: char $00, room colour $FE |
| `$6926` | 82 07 37 | literal 2 | line 3, columns 25-26: chars $07 $37, room colour |
| `$6929` | 03 00 | repeat 3 | line 3, columns 27-29: char $00 |
| `$692B` | 83 07 00 07 | literal 3 | line 3, columns 30-32: chars $07 $00 $07 |
| `$692F` | 02 00 | repeat 2 | line 3, columns 33-34: char $00 |
| `$6931` | 85 8B B6 89 8A 8E | literal 5 | line 3, columns 35-39: chars $0B $36 $09 $0A $0E, black. Line 3 is full. |

For example the first cell writes $09 to `$8C78`, $89 to `$8CA0` and $F8 to `$D878` and `$D8A0`. The cell of
column 22 in line 3 writes $00 to `$8CDE` and $80 to `$8D06` and leaves the colour RAM at $FE. The map ends with
$80 at `$6A08` after 440 cells. **Code** (the decode of the image bytes).

![Room 0 about 250 frames after Bruce entered it](images/rooms/room00.png)

The screenshot shows room 0: the top lines are the sky and the mountains of this map.

### 3.2 Map sizes

| Rooms | Bytes | Cells |
|---|---|---|
| 0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 16, 19 | see section 2.1 | 440 |
| 4, 7, 10, 13, 17, 18 | see section 2.1 | 442 (section 9) |

## 4. [`draw_room`](../src/draw_room.asm#L28) step by step

[`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room). Callers: [`change_room`](../src/background_touch.asm#L234) [`$2F9A`](reference/modules/background_touch.md#change_room), [`start_new_game`](../src/title_demo_start.asm#L283) [`$070E`](reference/modules/title_demo_start.md#start_new_game), [`start_attract_demo`](../src/title_demo_start.asm#L32) [`$0531`](reference/modules/title_demo_start.md#start_attract_demo).
**Code**, and **Observed** for all 20 rooms (the room screenshots).

1. `$09BC`: screen off ([`SCROLY`](../src/constants.asm#L222) bit 4 = 0). Saves the enable bits of sprites 0-4 in [`saved_sprite_enable`](../src/constants.asm#L37) [`$0047`](reference/variables.md#saved_sprite_enable)
   and switches all sprites off.
2. [`draw_room_clear_top_row`](../src/draw_room.asm#L39) [`$09D4`](reference/modules/draw_room.md#draw_room_clear_top_row): 40 spaces in status line 0 of [`game_screen`](../src/constants.asm#L199) [`$8C00`](reference/variables.md#game_screen).
3. [`draw_room_fill_colours`](../src/draw_room.asm#L46) [`$09E1`](reference/modules/draw_room.md#draw_room_fill_colours): fills colour RAM `$D878-$DBFF` (screen rows 3-24) with
   [`room_colour_fill`](../src/room_palettes.asm#L13) [`$47A0`](reference/modules/room_palettes.md#room_colour_fill) + room.
4. [`clear_fireball_sprites`](../src/wizard_fireballs.asm#L171) [`$423F`](reference/modules/wizard_fireballs.md#clear_fireball_sprites), [`stop_all_sounds`](../src/sound_request.asm#L63) [`$255E`](reference/modules/sound_request.md#stop_all_sounds).
5. **Room 11 rule** (`$09F6`): in room 11, when [`room_lanterns_left`](../src/constants.asm#L33) of rooms 12, 14 and 16 are all 0, it
   restores the sprites and jumps to [`place_bruce_at_room_start`](../src/room_misc_support.asm#L11) [`$3217`](reference/modules/room_misc_support.md#place_bruce_at_room_start) with X = 13. The player enters room 13
   instead (and [`draw_room`](../src/draw_room.asm#L28) runs again for room 13). Not executed in the coverage.
6. **First-visit bonus** ([`draw_room_first_visit_check`](../src/draw_room.asm#L68) [`$0A0E`](reference/modules/draw_room.md#draw_room_first_visit_check)): X = room*2 + [`current_player`](../src/constants.asm#L14) [`$0003`](reference/variables.md#current_player). When
   [`room_unvisited`](../src/constants.asm#L152) [`$0300`](reference/variables.md#room_unvisited) + X is 1, it is cleared (LSR) and [`add_score`](../src/score.asm#L52) [`$3175`](reference/modules/score.md#add_score) adds $07 at byte 1 and $D0 at
   byte 2: 2000 points. [`init_game_variables`](../src/game_setup.asm#L18) marks all rooms but room 0 unvisited for both players.
7. **Reset** ([`draw_room_reset_state`](../src/draw_room.asm#L82) [`$0A2A`](reference/modules/draw_room.md#draw_room_reset_state)): clears [`actor_move_queue`](../src/constants.asm#L178) [`$4F57`](reference/variables.md#actor_move_queue) (132 bytes), [`room_time`](../src/constants.asm#L86) [`$0087`](reference/variables.md#room_time)
   , [`anim_chars_direction`](../src/constants.asm#L64) [`$0065`](reference/variables.md#anim_chars_direction); [`anim_chars_speed_step`](../src/options_and_patterns.asm#L53) [`$4321`](reference/modules/options_and_patterns.md#anim_chars_speed_step) = 7.
8. [`room_no_enemy_flag`](../src/constants.asm#L75) [`$007A`](reference/variables.md#room_no_enemy_flag) = [`room_no_enemies`](../src/room_tables.asm#L164) + room. When it is nonzero, [`enemy_follow_x`](../src/constants.asm#L88) [`$008B`](reference/variables.md#enemy_follow_x) (both
   bytes) = 0, so no enemy follows Bruce into the room.
9. [`draw_room_load_spawn_timers`](../src/draw_room.asm#L101) [`$0A4E`](reference/modules/draw_room.md#draw_room_load_spawn_timers): the spawn timers from [`ninja_room_delay`](../src/room_enemy_tables.asm#L75) [`$130B`](reference/modules/room_enemy_tables.md#ninja_room_delay) and [`yamo_room_delay`](../src/room_enemy_tables.asm#L94) [`$1347`](reference/modules/room_enemy_tables.md#yamo_room_delay)
   ; 3 for both when [`game_loop_count`](../src/constants.asm#L34) [`$0040`](reference/variables.md#game_loop_count) is not 0; Yamo 8 when player 2 controls Yamo.
10. [`draw_room_reset_bruce`](../src/draw_room.asm#L119) [`$0A6B`](reference/modules/draw_room.md#draw_room_reset_bruce): Bruce's [`actor_contact`](../src/constants.asm#L102) [`$00B6`](reference/variables.md#actor_contact) = 1, [`actor_timer`](../src/constants.asm#L110) [`$00CE`](reference/variables.md#actor_timer) = 4, [`actor_state`](../src/constants.asm#L105) [`$00BF`](reference/variables.md#actor_state)
    = 0, [`actor_step_delay`](../src/constants.asm#L136) [`$0106`](reference/variables.md#actor_step_delay) = 0; the three [`burst_trap_timer`](../src/constants.asm#L180) [`$4FDE`](reference/variables.md#burst_trap_timer) slots = 0.
11. [`draw_room_copy_room_record`](../src/draw_room.asm#L140) [`$0A93`](reference/modules/draw_room.md#draw_room_copy_room_record): copies the room aux block (section 2.6).
12. [`draw_room_set_charset`](../src/draw_room.asm#L155) [`$0AAD`](reference/modules/draw_room.md#draw_room_set_charset): [`room_vmcsb`](../src/constants.asm#L121) [`$00F2`](reference/variables.md#room_vmcsb) = $38, $3A or $3C (section 2.1).
13. The map decoder (section 3), from [`draw_room_next_code`](../src/draw_room.asm#L178) [`$0AD7`](reference/modules/draw_room.md#draw_room_next_code) to [`draw_room_done`](../src/draw_room.asm#L222) [`$0B30`](reference/modules/draw_room.md#draw_room_done).
14. [`setup_room_lanterns_and_init`](../src/lantern_pickup.asm#L79) [`$336E`](reference/modules/lantern_pickup.md#setup_room_lanterns_and_init):
    1. Walks the lantern list of the room. For each record with state 0 (taken) it draws the replacement code:
       code AND $7F in the upper row and code OR $80 in the lower row of the cell ([`set_text_row_pointers`](../src/pause_status_line.asm#L117) [`$1A67`](reference/modules/pause_status_line.md#set_text_row_pointers)
       gives the line address; the lower row is +40).
    2. [`room_init_clear_vars`](../src/lantern_pickup.asm#L128) [`$33B3`](reference/modules/lantern_pickup.md#room_init_clear_vars): [`room_state_a`](../src/room_dispatch.asm#L7) .. [`room_state_e`](../src/room_dispatch.asm#L15) = 0.
    3. [`room_init_dispatch`](../src/lantern_pickup.asm#L136) [`$33BD`](reference/modules/lantern_pickup.md#room_init_dispatch): pushes [`room_init_handlers`](../src/room_dispatch.asm#L19) + room*2 (high byte, then low byte) and does
       RTS. The init handler returns to [`draw_room`](../src/draw_room.asm#L28).
15. Screen on, sprites 0-4 back on.
16. JMP [`run_room_frame_handler`](../src/passage_open.asm#L18) [`$3A6F`](reference/modules/passage_open.md#run_room_frame_handler): the frame handler runs one time before the main loop. Its RTS returns to
    the caller of [`draw_room`](../src/draw_room.asm#L28).

## 5. The room dispatch tables

Both tables are RTS tables: 20 words, entry = handler address - 1, index = room*2. **Code.**

```
room_init_dispatch ($33BD):        run_room_frame_handler ($3A6F):
  lda room                           lda room
  asl                                asl
  tax                                tax
  lda room_init_handlers+1,x         lda room_frame_handlers+1,x
  pha                                pha
  lda room_init_handlers,x           lda room_frame_handlers,x
  pha                                pha
  rts                                rts
```

[`room_init_dispatch`](../src/lantern_pickup.asm#L136) runs once per room entry, from [`draw_room`](../src/draw_room.asm#L28). [`run_room_frame_handler`](../src/passage_open.asm#L18) runs from [`draw_room`](../src/draw_room.asm#L28)
(once) and from [`main_loop`](../src/game_main_loop.asm#L23) (each pass). **Observed** (coverage: the warps into all 20 rooms ran every entry of both
tables).

| Room | [`room_init_handlers`](../src/room_dispatch.asm#L19) [`$4E9C`](reference/modules/room_dispatch.md#room_init_handlers) entry | Init handler | [`room_frame_handlers`](../src/room_dispatch.asm#L28) [`$4EC4`](reference/modules/room_dispatch.md#room_frame_handlers) entry | Frame handler |
|---|---|---|---|---|
| 0 | `$4E9C` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) | `$4EC4` | [`room00_frame`](../src/room_frames_0_7.asm#L9) [`$3642`](reference/modules/room_frames_0_7.md#room00_frame) |
| 1 | `$4E9E` | [`room01_init`](../src/room_specific_init.asm#L9) [`$33F6`](reference/modules/room_specific_init.md#room01_init) | `$4EC6` | [`room01_frame`](../src/room_frames_0_7.asm#L42) [`$3679`](reference/modules/room_frames_0_7.md#room01_frame) |
| 2 | `$4EA0` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) | `$4EC8` | [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) |
| 3 | `$4EA2` | [`room03_init`](../src/room_specific_init.asm#L14) [`$33FC`](reference/modules/room_specific_init.md#room03_init) | `$4ECA` | [`room03_frame`](../src/room_frames_0_7.asm#L136) [`$3702`](reference/modules/room_frames_0_7.md#room03_frame) |
| 4 | `$4EA4` | [`room04_init`](../src/room_specific_init.asm#L22) [`$3402`](reference/modules/room_specific_init.md#room04_init) | `$4ECC` | [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) |
| 5 | `$4EA6` | [`room05_init`](../src/room_specific_init.asm#L48) [`$3428`](reference/modules/room_specific_init.md#room05_init) | `$4ECE` | [`room05_frame`](../src/room_frames_0_7.asm#L378) [`$38AB`](reference/modules/room_frames_0_7.md#room05_frame) |
| 6 | `$4EA8` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) | `$4ED0` | [`room06_frame`](../src/room_frames_0_7.asm#L519) [`$39AA`](reference/modules/room_frames_0_7.md#room06_frame) |
| 7 | `$4EAA` | [`room07_init`](../src/room_specific_init.asm#L93) [`$3461`](reference/modules/room_specific_init.md#room07_init) | `$4ED2` | [`room07_frame`](../src/room_frames_0_7.asm#L542) [`$39C3`](reference/modules/room_frames_0_7.md#room07_frame) |
| 8 | `$4EAC` | [`room08_init`](../src/room_specific_init.asm#L107) [`$3478`](reference/modules/room_specific_init.md#room08_init) | `$4ED4` | [`room08_frame`](../src/room_frames_8_11.asm#L16) [`$3AD4`](reference/modules/room_frames_8_11.md#room08_frame) |
| 9 | `$4EAE` | [`room09_init`](../src/room_specific_init.asm#L123) [`$348F`](reference/modules/room_specific_init.md#room09_init) | `$4ED6` | [`room09_frame`](../src/room_frames_8_11.asm#L149) [`$3BB2`](reference/modules/room_frames_8_11.md#room09_frame) |
| 10 | `$4EB0` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) | `$4ED8` | [`room10_frame`](../src/room_frames_8_11.asm#L278) [`$3C90`](reference/modules/room_frames_8_11.md#room10_frame) |
| 11 | `$4EB2` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) | `$4EDA` | [`room11_frame`](../src/room_frames_8_11.asm#L318) [`$3CC0`](reference/modules/room_frames_8_11.md#room11_frame) |
| 12 | `$4EB4` | [`room12_init`](../src/room_specific_init.asm#L149) [`$34BD`](reference/modules/room_specific_init.md#room12_init) | `$4EDC` | [`room12_frame`](../src/room_frames_12_17.asm#L11) [`$3E4C`](reference/modules/room_frames_12_17.md#room12_frame) |
| 13 | `$4EB6` | [`room13_init`](../src/room_specific_init.asm#L159) [`$34C3`](reference/modules/room_specific_init.md#room13_init) | `$4EDE` | [`room13_frame`](../src/room_frames_12_17.asm#L41) [`$3E7C`](reference/modules/room_frames_12_17.md#room13_frame) |
| 14 | `$4EB8` | [`room14_init`](../src/room_specific_init.asm#L249) [`$358D`](reference/modules/room_specific_init.md#room14_init) | `$4EE0` | [`room14_frame`](../src/room_frames_12_17.asm#L88) [`$3ECC`](reference/modules/room_frames_12_17.md#room14_frame) |
| 15 | `$4EBA` | [`room15_init`](../src/room_specific_init.asm#L255) [`$3593`](reference/modules/room_specific_init.md#room15_init) | `$4EE2` | [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame) |
| 16 | `$4EBC` | [`room16_init`](../src/room_specific_init.asm#L264) [`$359F`](reference/modules/room_specific_init.md#room16_init) | `$4EE4` | [`room16_frame`](../src/room_frames_12_17.asm#L166) [`$3F5B`](reference/modules/room_frames_12_17.md#room16_frame) |
| 17 | `$4EBE` | [`room17_init`](../src/room_specific_init.asm#L284) [`$35C4`](reference/modules/room_specific_init.md#room17_init) | `$4EE6` | [`room17_frame`](../src/room_frames_12_17.asm#L188) [`$3F71`](reference/modules/room_frames_12_17.md#room17_frame) |
| 18 | `$4EC0` | [`room18_init`](../src/room_specific_init.asm#L317) [`$35FA`](reference/modules/room_specific_init.md#room18_init) | `$4EE8` | [`room18_frame`](../src/wizard_room.asm#L13) [`$3CDC`](reference/modules/wizard_room.md#room18_frame) |
| 19 | `$4EC2` | [`room19_init`](../src/ending_room.asm#L7) [`$425F`](reference/modules/ending_room.md#room19_init) | `$4EEA` | [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame) |

What each handler does is in the catalogue. The handlers share a few helpers:

| Helper | What it does |
|---|---|
| [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message) | Draws tile A at text line X, column Y. |
| [`open_passage`](../src/passage_open.asm#L42) [`$3A8A`](reference/modules/passage_open.md#open_passage) and its variants | Open a wall (section 7). |
| [`draw_slider0`](../src/room_hazard_draw.asm#L46) [`$4086`](reference/modules/room_hazard_draw.md#draw_slider0) .. [`draw_slider2_alt`](../src/room_hazard_draw.asm#L82) [`$40B4`](reference/modules/room_hazard_draw.md#draw_slider2_alt) | Draw a slider frame (section 8.1). |
| [`draw_runner_step`](../src/room_hazard_draw.asm#L9) [`$404E`](reference/modules/room_hazard_draw.md#draw_runner_step), [`draw_runner_step_alt`](../src/room_hazard_draw.asm#L21) [`$4063`](reference/modules/room_hazard_draw.md#draw_runner_step_alt) | Move a runner one cell (section 8.2). |
| [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps) | Animate the burst traps (section 8.3). |
| [`animate_scrolling_chars`](../src/animated_chars.asm#L12) [`$2C70`](reference/modules/animated_chars.md#animate_scrolling_chars) | Scroll the patterns of characters $61-$63 (the moving columns that an actor can ride). Rooms 4, 5, 6, 8, 9, 11. |
| [`play_open_sound`](../src/wizard_fireballs.asm#L183) [`$424F`](reference/modules/wizard_fireballs.md#play_open_sound) | Sound $8A, used when something opens. |

### 5.1 The one-shot events

Most handlers do an action one time per visit with this pattern:

```
lda room_state_x
bmi skip          ; $FF: already done
<condition>       ; Z = 1 when the event must happen
bne skip
dec room_state_x  ; 0 -> $FF
<action>          ; draw tiles, play a sound
```

[`room_init_clear_vars`](../src/lantern_pickup.asm#L128) sets the flag to 0 at each room entry, so the action happens again at each visit while its
condition holds. The map is drawn new at each visit, so the tile changes are not kept: the handler draws them again.
An init value 1 makes the action run on two passes (rooms 12, 14, 15). An init value 3 gives 4 steps (the trapdoors
of rooms 1 and 3). Room 17 uses the opposite test (`beq` on a flag that the init sets to 1): one time. **Code.**

~~~mermaid
stateDiagram-v2
  state "Armed (room_state = 0)" as Armed
  state "Done (room_state = $FF)" as Done
  [*] --> Armed: room_init_clear_vars $33B3
  Armed --> Done: condition true, action drawn
  Done --> [*]: next room entry
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Armed (0) | the lanterns of the condition are taken | Done ($FF), tiles drawn | the room frame handler |
| Done ($FF) | - | Done | the `bmi` test |
| any | room entry | Armed | [`room_init_clear_vars`](../src/lantern_pickup.asm#L128) [`$33B3`](reference/modules/lantern_pickup.md#room_init_clear_vars) |

## 6. Lanterns

### 6.1 The record format

[`lantern_list_ptr`](../src/lantern_lists.asm#L13) [`$4CE2`](reference/modules/lantern_lists.md#lantern_list_ptr) points each room at a list of 4-byte records, ended by $FF. **Code.**

| Byte | Meaning |
|---|---|
| +0 | State: 1 = present, 0 = taken, $FF = end of the list. |
| +1 | Replacement code: drawn in the cell after the pickup (code AND $7F upper row, code OR $80 lower row). $9E, $9F or $92. |
| +2 | Column (0-39). |
| +3 | Text line. |

In the map, a lantern is a cell with character $13 or $14 (lower rows $93/$94). [`handle_touched_tile`](../src/background_touch.asm#L61) also takes
character $31 as a lantern. Rooms 13 and 19 have one dummy record (01 00 00 00) and a count of 0; it could match
only at line 0, column 0. **Code.**

Worked example, [`lantern_list_room3`](../src/lantern_lists.asm#L38) [`$4D67`](reference/modules/lantern_lists.md#lantern_list_room3): `01 9E 1D 0A` `01 9F 26 0A` `FF`. Record 0: present, replacement $9E
(upper row $1E, lower row $9E), column $1D = 29, line $0A = 10. Record 1: present, replacement $9F, column 38, line
10. Then the end byte. **Code.**

### 6.2 Pickup

1. [`check_background_touch`](../src/background_touch.asm#L10) [`$2E39`](reference/modules/background_touch.md#check_background_touch) (each pass) gets the cell column [`actor_cell_col`](../src/constants.asm#L117) [`$00E6`](reference/variables.md#actor_cell_col) and line
   [`actor_cell_row`](../src/constants.asm#L118) [`$00E9`](reference/variables.md#actor_cell_row) of each actor ([`actor_calc_tile_pos`](../src/game_main_loop.asm#L91) [`$1C39`](reference/modules/game_main_loop.md#actor_calc_tile_pos)) and checks 3 characters of that line and
   3 of the next line.
2. [`handle_touched_tile`](../src/background_touch.asm#L61) [`$2E89`](reference/modules/background_touch.md#handle_touched_tile): a lantern character ($13, $14, $31) counts only when [`touch_tile_gate`](../src/constants.asm#L47) [`$0053`](reference/variables.md#touch_tile_gate)
   (bit 1 of [`actor_contact`](../src/constants.asm#L102)) is set. Then [`collect_lantern`](../src/background_touch.asm#L142) [`$2F04`](reference/modules/background_touch.md#collect_lantern).
3. [`collect_lantern`](../src/background_touch.asm#L142): only Bruce (X = 0). It calls [`check_lantern_pickup`](../src/lantern_pickup.asm#L15) [`$331C`](reference/modules/lantern_pickup.md#check_lantern_pickup) with Y = column.
4. [`check_lantern_pickup`](../src/lantern_pickup.asm#L15) walks the list of the room. A record matches when its state is not 0, its column equals
   Y and its line equals the actor's [`actor_cell_row`](../src/constants.asm#L118) ([`lantern_match`](../src/constants.asm#L56) [`$005C`](reference/variables.md#lantern_match) starts at 1 and is halved for each
   failed test). On a match: state = 0, [`room_lanterns_left`](../src/constants.asm#L33) + room - 1, A = replacement code AND $7F, carry clear.
   No match: carry set, nothing happens.
5. [`collect_lantern`](../src/background_touch.asm#L142) draws the replacement code over the touched cell (upper and lower row), adds 125 points
   ([`add_score`](../src/score.asm#L52) with A = $7D, X = 2) and plays sound $8E.

The room frame handlers test the state bytes and [`room_lanterns_left`](../src/constants.asm#L33) on the next passes and open passages
(section 7). **Observed** (coverage: the pickup ran; the "no match" path never ran).

### 6.3 Redraw, reset and two players

- **Redraw.** The map always shows every lantern. [`setup_room_lanterns_and_init`](../src/lantern_pickup.asm#L79) [`$336E`](reference/modules/lantern_pickup.md#setup_room_lanterns_and_init) draws the replacement code
  over each taken lantern after the map is drawn (section 4, step 14).
- **Reset.** [`reset_all_lanterns`](../src/lantern_pickup.asm#L147) [`$33CA`](reference/modules/lantern_pickup.md#reset_all_lanterns) sets the state of every record of rooms 19..0 to 1
  ([`reset_room_lanterns`](../src/lantern_pickup.asm#L160) [`$33DA`](reference/modules/lantern_pickup.md#reset_room_lanterns), [`next_lantern_record`](../src/passage_open.asm#L6) [`$3A63`](reference/modules/passage_open.md#next_lantern_record)). It runs at a game start and when room 19 starts
  the next game loop. It also sets the dummy records of rooms 13 and 19 to 1.
- **Two players.** The lists hold the lanterns of the current player. [`swap_player_lanterns`](../src/game_setup.asm#L96) [`$0FED`](reference/modules/game_setup.md#swap_player_lanterns) exchanges the
  state bytes of all records with [`parked_lantern_flags`](../src/constants.asm#L153) [`$0340`](reference/variables.md#parked_lantern_flags) when the turn passes to the other player.
  [`fill_parked_lanterns`](../src/game_setup.asm#L83) [`$0FE2`](reference/modules/game_setup.md#fill_parked_lanterns) sets the parked flags to 1 at a game start. Not executed in the coverage.
- **Flames.** [`flicker_lantern_flames`](../src/room_hazard_draw.asm#L96) [`$40BC`](reference/modules/room_hazard_draw.md#flicker_lantern_flames) (each pass, all rooms) writes random pixels into bytes 2-3 of the
  flame characters $93, $94, $B1 (and $86, $E7 in [`charset_rooms_0_9`](../src/constants.asm#L204) [`$A000`](reference/variables.md#charset_rooms_0_9)) in both room charsets.

### 6.4 What the lanterns open

| Room | Condition | Effect |
|---|---|---|
| 0 | room 6 cleared | statue mouth at L9 C7 moves |
| 1 | rooms 0, 1, 2 cleared and room 6 not cleared | trapdoor L12 C17-21, marker 3 to room 5 |
| 2 | room 6 cleared | floor opening L11-12 C37-39, marker 5 to room 3; statue mouth at L9 C33 |
| 3 | room 3 cleared | trapdoor L12 C29-33, marker 3 to room 10 |
| 4 | lantern L4 C11 / L4 C28 taken | barrier at lines 8-9 removed, slider 1 / 2 stops |
| 5 | L10 C26 taken | passages L10 C25, L10 C26 |
| 5 | L10 C2 taken | passage L10 C0 and marker 2 to room 4 |
| 5 | room 6 cleared and L3 C28 or L3 C38 taken | opening L2 C34 with marker 5 to room 1, passages L3 C30, L6 C32 |
| 6 | room 6 cleared | passage L5 C1 |
| 7 | the 5 lanterns of line 2 taken | passage L2 C33 |
| 7 | the 6 lanterns of line 5 taken | passage L5 C38 |
| 7 | both lanterns of line 9 taken | the runner of line 11 turns left |
| 8 | room 7 cleared and L7 C6 taken | passage L7 C14 |
| 8 | L3 C15 and L3 C24 taken | passage L7 C25 |
| 8 | room 8 cleared and room 9 lanterns L10 C27, L10 C28 taken | passage L2 C38 |
| 8 | L7 C6 taken | passage L10 C1 |
| 8 | rooms 7 and 8 cleared | passage L10 C38 |
| 9 | L7 C15 taken | passage L7 C23 |
| 9 | room 9 cleared | opening L2 C35, marker 4 to room 6 |
| 9 | L10 C27 and L10 C28 taken | the runner of line 12 turns left |
| 10 | L4 C1 and L7 C30 taken | passage L4 C38 |
| 11 | rooms 12, 14, 16 cleared | entering room 11 leads to room 13 ([`draw_room`](../src/draw_room.asm#L28)) |
| 12 | L10 C36 taken | passage L10 C38 |
| 12 | room 12 cleared and room 14 lanterns L10 C9, L10 C30 taken | passage L7 C38 |
| 14 | L7 C9 and L7 C30 taken | passage L4 C38 |
| 15 | L3 C19 taken | opening at column 17, lines 3-4 |
| 15 | L3 C21, L4 C14, L6 C13 taken | opening at column 23, lines 3-4 |
| 15 | room 15 cleared | opening at column 37-39, lines 7-9, marker 3 to room 17 |
| 16 | room 16 cleared | passage L7 C1 |
| 17 | L10 C38 taken | tile $5D at L10 C37 |
| 17 | L11 C31 taken | tile $5C at L10 C24 |
| 18 | L11 C37 taken | the wizard is defeated; later marker 3 to room 19 |

**Code.**

## 7. Passages

A passage opens a wall that is one column wide and three lines high. Input: A = top line R, Y = column C.
[`draw_passage_cell`](../src/passage_open.asm#L80) [`$3ACA`](reference/modules/passage_open.md#draw_passage_cell) draws one tile at ([`passage_row`](../src/constants.asm#L67) [`$006C`](reference/variables.md#passage_row), [`passage_col`](../src/constants.asm#L68) [`$006D`](reference/variables.md#passage_col)) and moves one line
down. **Code.**

| Routine | Sound | Lines R, R+1 | Line R+2 | Used in |
|---|---|---|---|---|
| [`open_passage`](../src/passage_open.asm#L42) [`$3A8A`](reference/modules/passage_open.md#open_passage) | $8A | tile $13 (code $00) | tile $14 (code $3E) | rooms 5, 8, 9 |
| [`open_passage_ledge`](../src/passage_open.asm#L54) [`$3AA0`](reference/modules/passage_open.md#open_passage_ledge) | $8A | tile $13 | tile $17 (code $11) | rooms 6, 7 |
| [`open_passage_ledge_b`](../src/passage_open.asm#L61) [`$3AAA`](reference/modules/passage_open.md#open_passage_ledge_b) | $8A | tile $13 | tile $2D (code $11) | room 8 |
| [`open_passage_dark`](../src/passage_open.asm#L69) [`$3AB4`](reference/modules/passage_open.md#open_passage_dark) | $8A | tile $63 (code $07) | tile $64 (code $0E) | rooms 10, 12, 14, 16 |

Tiles $13 and $14 are drawn with [`charset_rooms_0_9`](../src/constants.asm#L204); [`open_passage_dark`](../src/passage_open.asm#L69) uses the codes of
[`charset_rooms_10_19`](../src/constants.asm#L205). Several passages open the way to an exit marker in the map behind the wall, for example
the passage of room 10 at L4 C38 is next to marker 3 at L5 C39. **Conclusion** (from the map cells).

## 8. Hazards

The hazards are cells that kill. [`handle_touched_tile`](../src/background_touch.asm#L61) [`$2E89`](reference/modules/background_touch.md#handle_touched_tile) sends these characters (upper row code) to
[`touch_deadly_tile`](../src/touch_effects.asm#L75) [`$304B`](reference/modules/touch_effects.md#touch_deadly_tile) when [`touch_tile_gate`](../src/constants.asm#L47) is set: $0F, $40, $64, $54-$5A except $57, $71-$7C, and $66 in
rooms 10-19. [`touch_deadly_tile`](../src/touch_effects.asm#L75) does nothing in room 18. Otherwise it plays sound $8C; an enemy is removed
([`remove_actor`](../src/touch_effects.asm#L38) [`$3001`](reference/modules/touch_effects.md#remove_actor)) and Bruce dies ([`set_actor_hazard_death`](../src/room_hazard_draw.asm#L37) [`$407D`](reference/modules/room_hazard_draw.md#set_actor_hazard_death): [`actor_state`](../src/constants.asm#L105) = $19, [`actor_timer`](../src/constants.asm#L110) =
$10). **Code.**

### 8.1 Sliders

A slider is a small object that appears at a start column, slides right one column per pass to an end column, and
fades out. Rooms 4, 5, 7, 8, 9 and 17 have up to three: slot n uses [`slider_col`](../src/constants.asm#L72) [`$0071`](reference/variables.md#slider_col) + n, [`slider_row`](../src/constants.asm#L73) [`$0074`](reference/variables.md#slider_row)
+ n and [`slider_timer`](../src/constants.asm#L74) [`$0077`](reference/variables.md#slider_timer) + n. The init handler sets them; the frame handler runs the state machine on
every pass. **Code.** **Observed** in room 4 (a run of the analysis: a small white dotted object appears at the
start column, moves right and fades).

The drawing: [`draw_slider0`](../src/room_hazard_draw.asm#L46) [`$4086`](reference/modules/room_hazard_draw.md#draw_slider0), [`draw_slider1`](../src/room_hazard_draw.asm#L53) [`$4090`](reference/modules/room_hazard_draw.md#draw_slider1), [`draw_slider2`](../src/room_hazard_draw.asm#L60) [`$409A`](reference/modules/room_hazard_draw.md#draw_slider2) draw tile $1F + frame (look A:
tiles $1F-$25). [`draw_slider0_alt`](../src/room_hazard_draw.asm#L68) [`$40A4`](reference/modules/room_hazard_draw.md#draw_slider0_alt), [`draw_slider1_alt`](../src/room_hazard_draw.asm#L75) [`$40AC`](reference/modules/room_hazard_draw.md#draw_slider1_alt), [`draw_slider2_alt`](../src/room_hazard_draw.asm#L82) [`$40B4`](reference/modules/room_hazard_draw.md#draw_slider2_alt) add 7 (look B:
tiles $26-$2C). Frame 6 is blank. The upper codes of the frames are $54-$5A, so a slider kills (except frame code
$57).

~~~mermaid
stateDiagram-v2
  state "Waiting (timer < 0)" as Wait
  state "Appear (timer 0-2)" as Appear
  state "Move (timer 3, column < end)" as Move
  state "At end (timer 3, column = end)" as End
  state "Fade (timer 4-6)" as Fade
  state "Reset (timer 7)" as Reset
  [*] --> Wait: init handler
  Wait --> Appear: timer reaches 0
  Appear --> Move: timer = 3
  Move --> Move: column + 1, timer = 2
  Move --> End: column = end
  End --> Fade
  Fade --> Reset: timer = 7
  Reset --> Wait: timer = wait value, column = start
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Waiting | [`slider_timer`](../src/constants.asm#L74) + 1 is still negative | Waiting | [`room04_frame_slider0`](../src/room_frames_0_7.asm#L281) [`$3811`](reference/modules/room_frames_0_7.md#room04_frame_slider0) (and the same code in each room) |
| Waiting | [`slider_timer`](../src/constants.asm#L74) + 1 = 0 | Appear: frame 0 | [`room04_frame_slider0_frame`](../src/room_frames_0_7.asm#L284) [`$3815`](reference/modules/room_frames_0_7.md#room04_frame_slider0_frame) |
| Appear | timer 1, 2 | frame 1, 2 drawn | [`room04_frame_slider0_draw`](../src/room_frames_0_7.asm#L290) [`$381F`](reference/modules/room_frames_0_7.md#room04_frame_slider0_draw) |
| Appear / Move | timer = 3, column < end | frame 6 at the old column, column + 1, timer = 2, frame 2 at the new column | [`room04_frame_slider0_step`](../src/room_frames_0_7.asm#L293) [`$3825`](reference/modules/room_frames_0_7.md#room04_frame_slider0_step) |
| Move | timer = 3, column >= end | At end: frame 3 | [`room04_frame_slider0_step`](../src/room_frames_0_7.asm#L293) |
| At end / Fade | timer 4, 5, 6 | frames 4, 5, 6 (6 = blank) | [`room04_frame_slider0_draw`](../src/room_frames_0_7.asm#L290) |
| Fade | timer = 7 | Waiting: timer = wait value, column = start | [`room04_frame_slider0_reset`](../src/room_frames_0_7.asm#L303) [`$3838`](reference/modules/room_frames_0_7.md#room04_frame_slider0_reset) |

The timer counts up from the wait value, so a wait value $A0 waits 96 passes. All sliders:

| Room | Slot | Line | Columns | Look | First timer | Wait value | Extra condition |
|---|---|---|---|---|---|---|---|
| 4 | 0 | 11 | 1-3 | B | $FF | $A0 (96) | - |
| 4 | 1 | 7 | 11-12 | A | $FF | $E4 (28) | while lantern L4 C11 is present |
| 4 | 2 | 7 | 26-27 | A | $F4 | $E4 (28) | while lantern L4 C28 is present |
| 5 | 0 | 9 | 27-28 | A | $FF | $E0 (32) | - |
| 5 | 1 | 10 | 27-28 | A | $FC | $E0 (32) | while lantern L10 C26 is present |
| 5 | 2 | 5 | 1-2 | B | $F8 | $E2 (30) | - |
| 7 | 0 | 4 | 34-36 | B | $FF | $E0 (32) | - |
| 8 | 0 | 5 | 6-11 | A | $FF | $DA (38) | - |
| 8 | 1 | 5 | 27-32 | A | $F2 | $DA (38) | - |
| 9 | 0 | 5 | 16-20 | B | $FC | $C0 (64) | - |
| 9 | 1 | 6 | 16-20 | B | $FF | $C0 (64) | - |
| 17 | 0 | 3 | 8-35 | A | $F8 | $C8 (56) | - |
| 17 | 1 | 7 | 8-37 | A | $F1 | $CA (54) | - |
| 17 | 2 | 9 | 8-37 | A | $EA | $CA (54) | - |

Room 17 runs its three slots in one loop ([`room17_frame_slider_loop`](../src/room_frames_12_17.asm#L248) [`$3FDC`](reference/modules/room_frames_12_17.md#room17_frame_slider_loop), index [`temp_counter`](../src/constants.asm#L41) [`$004C`](reference/variables.md#temp_counter)). When a
lantern of room 4 or room 5 that guards a slider is taken, the handler draws frame 6 (blank) and the slider no
longer runs.

### 8.2 Runners and floor movers

A runner is one deadly cell that moves one column per update along a track. [`draw_runner_step`](../src/room_hazard_draw.asm#L9) [`$404E`](reference/modules/room_hazard_draw.md#draw_runner_step) plays sound
$89 ([`play_runner_sound`](../src/room_hazard_draw.asm#L32) [`$4078`](reference/modules/room_hazard_draw.md#play_runner_sound)), draws tile $1C (track, code $65) at [`runner_old_col`](../src/constants.asm#L71) [`$0070`](reference/variables.md#runner_old_col) and tile $1B
(runner, code $64, deadly) at [`runner_col`](../src/constants.asm#L69) [`$006E`](reference/variables.md#runner_col), both in line [`runner_row`](../src/constants.asm#L70) [`$006F`](reference/variables.md#runner_row). [`draw_runner_step_alt`](../src/room_hazard_draw.asm#L21) [`$4063`](reference/modules/room_hazard_draw.md#draw_runner_step_alt)
uses tiles $55 (code $67) and $54 (code $66, deadly in rooms 10-19). **Code.**

| Room | Line | Start column | Moves | Range | Direction |
|---|---|---|---|---|---|
| 7 | 11 | 5 | every pass | right: 5-35, then 5; left: 36-5, then 36 | right while lantern L9 C2 or L9 C3 is present, left when both are taken |
| 9 | 12 | 4 | every pass | right: 4-24, then 4; left: 24-5, then 24 | right while lantern L10 C27 or L10 C28 is present |
| 17 | 5 | 11 | every second pass ([`room_state_d`](../src/room_dispatch.asm#L13)) | right: 11-27, then 11 | always right |

**Floor movers of room 13.** [`room13_init`](../src/room_specific_init.asm#L159) [`$34C3`](reference/modules/room_specific_init.md#room13_init) fills 10 slots: [`mover_dir`](../src/constants.asm#L143) [`$010F`](reference/variables.md#mover_dir) (0 off, $02 left, $82
right), [`mover_col`](../src/constants.asm#L144) [`$0119`](reference/variables.md#mover_col), [`mover_row`](../src/constants.asm#L145) [`$0123`](reference/variables.md#mover_row), [`mover_old_col`](../src/constants.asm#L146) [`$012D`](reference/variables.md#mover_old_col), [`mover_min_col`](../src/constants.asm#L147) [`$0137`](reference/variables.md#mover_min_col),
[`mover_wrap_col`](../src/constants.asm#L148) [`$0141`](reference/variables.md#mover_wrap_col). [`update_floor_movers`](../src/game_setup.asm#L169) [`$104B`](reference/modules/game_setup.md#update_floor_movers) (from [`room13_frame`](../src/room_frames_12_17.asm#L41) on even passes) moves slots 8..0 one
column: a left mover below [`mover_min_col`](../src/constants.asm#L147) restarts at [`mover_wrap_col`](../src/constants.asm#L148); a right mover at [`mover_wrap_col`](../src/constants.asm#L148)
restarts at [`mover_min_col`](../src/constants.asm#L147). It draws with [`draw_runner_step`](../src/room_hazard_draw.asm#L9), or with [`draw_runner_step_alt`](../src/room_hazard_draw.asm#L21) on lines 5 and 10.
**Observed** (coverage).

| Slot | Line | Direction | Start column | Min column | Wrap column |
|---|---|---|---|---|---|
| 0 | 7 | left | 33 | 20 (18) | 33 |
| 1 | 10 | left | 19 (21) | 6 | 19 (21) |
| 2 | 12 | left | 2 | 2 | 33 (37) |
| 3 | - | off | - | - | - |
| 4 | 12 | left | 22 | 2 | 33 (37) |
| 5 | 5 | right | 6 | 6 | 34 (38) |
| 6 | 5 | right | 22 | 6 | 34 (38) |
| 7 | 7 | right | 6 (2) | 6 (2) | 20 (18) |
| 8 | 10 | right | 20 (22) | 20 (22) | 34 (38) |
| 9 | - | off | - | - | - |

The values in brackets apply when [`game_loop_count`](../src/constants.asm#L34) [`$0040`](reference/variables.md#game_loop_count) is not 0: later game loops have longer tracks.

### 8.3 Burst traps

A burst trap is a floor cell with character $60. Rooms 6, 7, 10, 11, 12, 14, 16 and 17 call [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps)
from their frame handler. **Code**; **Observed** (coverage: the trap stages ran).

1. [`touch_trap_tile`](../src/touch_effects.asm#L101) [`$306B`](reference/modules/touch_effects.md#touch_trap_tile): an actor touches character $60 whose colour RAM (AND 7) is not 5. A free slot n gets
   [`burst_trap_timer`](../src/constants.asm#L180) [`$4FDE`](reference/variables.md#burst_trap_timer) + n = 1, [`burst_trap_row`](../src/constants.asm#L182) [`$4FE4`](reference/variables.md#burst_trap_row) + n = line - 1, [`burst_trap_col`](../src/constants.asm#L181) [`$4FE1`](reference/variables.md#burst_trap_col) + n =
   column - 1. The colour RAM of the cell becomes $FD, so the cell does not trigger again. With all 3 slots busy
   nothing happens.
2. [`update_burst_traps`](../src/room_misc_support.asm#L33) increments each active slot every pass and acts on the value before the increment:

~~~mermaid
stateDiagram-v2
  state "Free (timer 0)" as Free
  state "Armed (timer 1-7)" as Armed
  state "Small burst (8)" as Small
  state "Large burst (12)" as Large
  state "Small again (16)" as Small2
  state "Debris (20)" as Debris
  [*] --> Free
  Free --> Armed: touch_trap_tile $306B
  Armed --> Small: timer = 8
  Small --> Large: timer = 12
  Large --> Small2: timer = 16
  Small2 --> Debris: timer = 20
  Debris --> Free: timer = 24
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Free | an actor touches an armed $60 cell | Armed, timer 1 | [`touch_trap_tile`](../src/touch_effects.asm#L101) [`$306B`](reference/modules/touch_effects.md#touch_trap_tile) |
| Armed | timer = $08 | sound $8D ([`play_burst_sound`](../src/room_misc_support.asm#L122) [`$32CC`](reference/modules/room_misc_support.md#play_burst_sound)), tiles $2F/$30 (codes $71-$76) at (row, col) and (row+1, col) | [`update_burst_traps_active`](../src/room_misc_support.asm#L41) [`$3236`](reference/modules/room_misc_support.md#update_burst_traps_active), [`update_burst_traps_draw_small`](../src/room_misc_support.asm#L48) [`$3240`](reference/modules/room_misc_support.md#update_burst_traps_draw_small) |
| Small burst | timer = $0C | tiles $31/$32 (codes $77-$7C) | [`update_burst_traps_stage_large`](../src/room_misc_support.asm#L63) [`$3260`](reference/modules/room_misc_support.md#update_burst_traps_stage_large) |
| Large burst | timer = $10 | tiles $2F/$30 again | [`update_burst_traps_stage_small2`](../src/room_misc_support.asm#L79) [`$3282`](reference/modules/room_misc_support.md#update_burst_traps_stage_small2) |
| Small again | timer = $14 | tile $00 (blank) on the row, tile $33 (codes $7D $60 $7D) below; colour $F8 on the $60 cell: armed again | [`update_burst_traps_stage_small2`](../src/room_misc_support.asm#L79) [`$3282`](reference/modules/room_misc_support.md#update_burst_traps_stage_small2) |
| Debris | timer = $18 | timer = 0, slot free | [`update_burst_traps_stage_free`](../src/room_misc_support.asm#L110) [`$32BB`](reference/modules/room_misc_support.md#update_burst_traps_stage_free) |

The burst codes $71-$7C kill on contact. The burst is 3 cells wide and 2 lines high, with the trap cell in the
middle of its lower line.

## 9. The map overflow bug

The maps of rooms 4, 7, 10, 13, 17 and 18 decode to 442 cells, two more than the 440 cells of lines 2-12. Each of
these maps ends with a repeat run of cell $00 ($02 $00, or $03 $00 in room 17) before the $80 end code. **Code**
(decode of the 20 maps).

The two extra cells are line 13, columns 0 and 1:

| Write | Address | Value | What is there |
|---|---|---|---|
| upper row | `$8FE8-$8FE9` | $00 | screen row 25: the spare bytes after the screen, before the sprite pointers at `$8FF8` |
| lower row | `$9010-$9011` | $80 | the contact mask of actor frame 0 (`$9000`), column 0, rows 16-17 |
| colour RAM | - | - | not written: the cells have bit 7 clear |

The contact masks are built once by the cold start. So the first visit of one of these rooms changes the mask bytes
of Bruce's frame 0 at `$9010-$9011` from $0C, $0C to $80, $80 for the rest of the session. **Observed** (run of the
analysis: after a visit to room 4, 7 or 10 the mask reads `0F 0C 80 80 0C 3C` instead of `0F 0C 0C 0C 0C 3C`).
**Conclusion:** the effect is small: the background contact test of that frame sees one pixel pair more and two
less in one column. The rebuild keeps the bug, because the source is identical to the program.

## 10. Still open

- What the sliders and runners are in game terms (sparks, flames?). The names are neutral. A close screenshot of
  room 4 and room 17 can answer it.
- Room 18 has exit markers 4 and 5 in the wizard graphics (lines 2-9). Their entry X is 0, so [`take_exit5`](../src/background_touch.asm#L210) would
  send Bruce to room 0 at X = 0, Y = 0. [`check_exit_edge`](../src/touch_effects.asm#L154) allows this only at the top edge after a move up, or at
  the right edge (column 38 of line 2). Whether Bruce can reach these cells needs a run that climbs in room 18.
- Whether the openings of room 5 at L3 C30 and L6 C32 block the way to the markers 3 and 4 at L4 C39 and L7 C39
  before room 6 is cleared. A run with Bruce in room 5 and lanterns of room 6 left can answer it.
- What the room aux blocks were meant for.
