# Bruce Lee: the rooms

The game has 20 rooms, and each room is one screen. The program keeps each room as a small packed map and one entry in each per-room table: colours, exits, start points and lanterns. When Bruce walks into a room, the program draws the map and puts back the lanterns that he took. Then the code of the room takes control: an init handler runs once, and a frame handler runs on each pass. The frame handlers open passages when Bruce takes lanterns, and move the sliders, runners and burst traps that kill him. This page explains what the rooms share, and [rooms_catalogue.md](rooms_catalogue.md) describes each room one by one.

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of the main loop [`main_loop` `$1BC2`](../src/game/game_main_loop.asm#L23). A pass takes 3 frames (`frame_countdown` = 3). An *even pass* is a pass with `pass_parity` = 0. The main loop toggles it before it calls the room frame handler.
- A *cell* is one double-height character: character code c in the upper screen row, c+$80 in the row below. A *code* is the character code of the upper row.
- A *text line* L is a row of cells. Line 0 is the status line (screen row 0). Line L (1-12) uses screen rows 2L-1 and 2L. The map fills lines 2-12 (screen rows 3-24). A *column* is 0-39. "L7 C31" is the cell at text line 7, column 31.
- A *tile* is a message of `print_message`: a string of cells at a text line and a column. The room code calls messages tiles. "Tile $13" is message number $13 in `message_ptrs`.
- An *exit marker* is a cell with code 2, 3, 4 or 5. Marker N uses the exit tables of set N.
- A room is *cleared* when its entry in `room_lanterns_left` is 0.
- **Observed** marks a fact that a run showed (the coverage runs, the room screenshots, the runs of the analysis notes). **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

Each way into a room ends in the same routine, [`draw_room` `$09BC`](../src/room/draw_room.asm#L28). There are four ways: Bruce walks through an exit, a new game starts, the demo starts, or Bruce starts again after a lost fall. `draw_room` builds the full screen, resets the state of the old room, and runs the two handlers of the new room. After that, the main loop runs the frame handler of the room once per pass. The main loop also reads the cells under each actor to find exits, lanterns and deadly cells. **Code.**

~~~mermaid
flowchart TB
  S["New game, demo, restart after a fall"] --> D
  E["Bruce touches an exit marker"] --> C["Leave the room (change_room)"]
  C --> D["Draw the room (draw_room)"]
  D --> M["Decode the map"]
  M --> L["Put back the taken lanterns"]
  L --> I["Room init handler"]
  I --> F1["Room frame handler, one time"]
  F1 --> P["Main loop: one pass"]
  P --> F["Room frame handler"]
  P --> T["Read the cells under each actor"]
  T --> E
  T --> X["Take a lantern, or die on a deadly cell"]
~~~

`draw_room` draws the map only once per visit. The frame handler draws each later change over the map, with tiles. Thus a room forgets its changes when Bruce leaves it. At the next visit, the handler sees the same taken lanterns and draws the same changes again (see [The one-shot events](#the-one-shot-events)). **Code.**

### Entering and leaving a room

An exit is a cell of the map with code 2, 3, 4 or 5. Each code selects one of four exit sets. Each set has three tables: the destination room, and Bruce's X and Y in that room. So a room has a maximum of four different exits. **Code.**

On each pass, [`check_background_touch` `$2E39`](../src/actor/background_touch.asm#L10) reads 3 characters of the actor's text line and 3 characters of the line below. [`handle_touched_tile` `$2E89`](../src/actor/background_touch.asm#L61) tests them for the markers in the order 5, 2, 3, 4. It jumps to `take_exit5`, `take_exit2`, `take_exit3` or `take_exit4`. Then these steps occur. **Code.**

1. [`check_exit_edge` `$30D4`](../src/actor/touch_effects.asm#L154) allows the exit only at a screen edge, when the actor moves toward that edge:
   - left: `actor_x` < $10 after a move left
   - right: `actor_x` > $A1 after a move right
   - bottom: `actor_y` > $C5 while the actor falls (state $0E)
   - top: `actor_y` < $31 after a move up

   In room 11, the code always allows an exit.
2. The exit routine loads `next_room` with the destination room of its set. It loads Y with the entry Y and A with the entry X.
3. When the entry X is 0, the code continues into the routine of the next set. Thus a marker with entry X 0 acts as the next marker. `take_exit5` does not test the entry X.
4. [`enter_room` `$2F8E`](../src/actor/background_touch.asm#L222) only removes an enemy that walks into an exit. For Bruce, [`change_room` `$2F9A`](../src/actor/background_touch.asm#L234) stores the position and sets `room`.
5. `change_room` saves the energy of each active enemy in `enemy_follow_energy`. It saves Bruce's entry point in `enemy_follow_x` / `enemy_follow_y`. An enemy that follows Bruce comes back at that point.
6. `change_room` removes the enemies, restarts the spawn timers and resets the stack. It calls `draw_room` and `build_actor_sprites`, and jumps to `main_loop`.

The other way into a room is [`place_bruce_at_room_start` `$3217`](../src/room/room_misc_support.asm#L11). It puts Bruce at start point A of room X and enters the room through `enter_room`. `lose_fall` uses it after a lost fall. `room19_frame` uses it at the end of a game loop. `draw_room` uses it for the room 11 rule below. **Code.**

### Drawing a room

The screen stays off while `draw_room` works. The steps below are in the order of the code. **Code**, and **Observed** for all 20 rooms (the room screenshots).

1. Disables the screen. Saves the enable bits of sprites 0-4 in `saved_sprite_enable` and disables all sprites.
2. Writes 40 spaces in the status line. Fills the colour RAM of the play area (`$D878-$DBFF`, screen rows 3-24) with the colour from `room_colour_fill`. Clears the fireball sprites and stops the sound effects.
3. **The room 11 rule.** In room 11, when rooms 12, 14 and 16 are all cleared, the code enables the sprites again. It jumps to `place_bruce_at_room_start` with X = 13. Bruce enters room 13 instead, and `draw_room` runs again for room 13. The coverage did not run this code.
4. **The first-visit bonus.** The flag of the room and the current player is `room_unvisited` + room*2 + `current_player`. When the flag is 1, the code clears it and calls [`add_score` `$3175`](../src/game/score.asm#L52) two times. The two calls add $07 at score byte 1 and $D0 at byte 2, which is 2000 points. `init_game_variables` marks all rooms but room 0 unvisited for both players.
5. **The reset of the old room.** Clears `actor_move_queue` (132 bytes), `room_time` and `anim_chars_direction`. Sets `anim_chars_speed_step` = 7.
6. **The enemies.** Copies the entry of the room in `room_no_enemies` to `room_no_enemy_flag`. When the flag is not 0, it clears both bytes of `enemy_follow_x`. Then no enemy follows Bruce into the room. It loads the spawn timers from `ninja_room_delay` and `yamo_room_delay`. Both timers are 3 when `game_loop_count` is not 0. Yamo's timer is 8 when player 2 controls Yamo.
7. **Bruce.** Sets `actor_contact` = 1 (on the floor), `actor_timer` = 4, `actor_state` = 0 and `actor_step_delay` = 0. Clears the three slots of `burst_trap_timer`.
8. Copies the room aux block to `room_band_colours` (see [The room aux blocks](#the-room-aux-blocks)).
9. Sets the charset of the room in `room_vmcsb`: $38, $3A or $3C (see [Graphics of each room](#graphics-of-each-room)).
10. Decodes the map, from [`draw_room_next_code` `$0AD7`](../src/room/draw_room.asm#L178) to `draw_room_done` (see [The map format](#the-map-format)).
11. Calls [`setup_room_lanterns_and_init` `$336E`](../src/room/lantern_pickup.asm#L79). This routine draws the replacement code over each taken lantern. It clears the five scratch bytes of the room with `room_init_clear_vars`. It runs the init handler through `room_init_dispatch`. The init handler returns to `draw_room`.
12. Enables the screen and sprites 0-4 again.
13. Jumps to `run_room_frame_handler`. Thus the frame handler runs one time before the main loop starts. Its RTS returns to the caller of `draw_room`.

### The room handlers

Each room has an init handler and a frame handler. Two tables of 20 words hold them: [`room_init_handlers` `$4E9C`](../src/room/room_dispatch.asm#L19) and [`room_frame_handlers` `$4EC4`](../src/room/room_dispatch.asm#L28). Both are RTS tables. Each entry is the handler address minus 1, and the index is room*2. The two dispatch routines are the same code with a different table. **Code.**

[`room_init_dispatch` `$33BD`](../src/room/lantern_pickup.asm#L136) runs once per room entry, from `draw_room`. [`run_room_frame_handler` `$3A6F`](../src/room/passage_open.asm#L18) runs once from `draw_room`, and then from `main_loop` on each pass. **Code**, and **Observed** (the coverage: the warps into all 20 rooms ran every entry of both tables).

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

Rooms 0, 2, 6, 10 and 11 have no init code. Their entry is `room_init_none`. The reference lists [each entry of both tables](reference/tables.md#room_init_handlers), and the catalogue tells what each handler does.

A handler keeps its state in five scratch bytes, `room_state_a` to `room_state_e` (`$4E97-$4E9B`). These bytes hold timers, step counters and one-shot flags. `room_init_clear_vars` sets them to 0 at each room entry. **Code.**

The handlers share some helpers. **Code.**

- `print_message` draws the changes as tiles.
- The passage routines open walls (see [Passages](#passages)).
- The slider, runner and burst trap routines move the hazards (see [Hazards](#hazards)).
- `play_open_sound` plays sound $8A when something opens.
- `animate_scrolling_chars` scrolls the patterns of characters $61-$63 in rooms 4, 5, 6, 8, 9 and 11. These characters are the moving columns that an actor can ride.

### Lanterns

Bruce must take the lanterns to open the way to the next rooms. There are 90 lanterns. Each room has a list of its lanterns, and each record holds a state byte. The state is 1 while the lantern is there, and 0 after Bruce takes it (see [Lantern lists](#lantern-lists) for the format). The map always shows every lantern. The list tells which lanterns are gone. **Code.**

In the map, a lantern is a cell with character $13 or $14 (lower rows $93 / $94). Bruce takes a lantern in these steps. **Observed** (coverage: the pickup ran, but the "no match" path never ran).

1. On each pass, `check_background_touch` gets the cell column `actor_cell_col` and line `actor_cell_row` of each actor. It checks 3 characters of that line and 3 characters of the next line.
2. `handle_touched_tile` accepts a lantern character ($13, $14 or $31) only when `touch_tile_gate` is set. This gate is bit 1 of `actor_contact`. Then the routine calls [`collect_lantern` `$2F04`](../src/actor/background_touch.asm#L142).
3. `collect_lantern` works only for Bruce (X = 0). It calls [`check_lantern_pickup` `$331C`](../src/room/lantern_pickup.asm#L15) with Y = the column.
4. `check_lantern_pickup` examines each record of the list of the room. A record matches when its state is not 0, its column equals Y, and its line equals `actor_cell_row`. `lantern_match` starts at 1, and the routine halves it for each failed test.
5. On a match, the state becomes 0, and the entry of the room in `room_lanterns_left` decreases by 1. The routine returns the replacement code AND $7F, with carry clear. With no match, it returns carry set, and nothing occurs.
6. `collect_lantern` draws the replacement code over the touched cell, in the upper and the lower row. It adds 125 points (`add_score` with A = $7D, X = 2) and plays sound $8E.

On the next passes, the room frame handlers test the state bytes and `room_lanterns_left`, and open the passages. The catalogue tells what the lanterns open in each room. **Code.** The effects are:

- passages in a wall
- trapdoors and openings that show an exit marker
- sliders that stop
- runners that turn
- in room 11, the way to room 13.

The other parts of the lantern code:

- **Redraw.** After the map, `setup_room_lanterns_and_init` draws the replacement code over each taken lantern. It writes code AND $7F in the upper row and code OR $80 in the lower row. `set_text_row_pointers` gives the line address, and the lower row is 40 bytes after it. **Code.**
- **Reset.** [`reset_all_lanterns` `$33CA`](../src/room/lantern_pickup.asm#L147) sets the state of each record to 1, from room 19 to room 0. It uses `reset_room_lanterns` and `next_lantern_record`. It runs at a game start, and when room 19 starts the next game loop. It also sets the dummy records of rooms 13 and 19 to 1. **Code.**
- **Two players.** The lists hold the lanterns of the current player. When the turn goes to the other player, [`swap_player_lanterns` `$0FED`](../src/game/game_setup.asm#L96) exchanges the state bytes of all records with `parked_lantern_flags`. `fill_parked_lanterns` sets the parked flags to 1 at a game start. The coverage did not run this code. **Code.**
- **Flames.** On each pass in all rooms, `flicker_lantern_flames` writes random pixels into bytes 2-3 of the flame characters. These characters are $93, $94 and $B1 in both room charsets, and also $86 and $E7 in `charset_rooms_0_9`. **Code.**

### Passages

A passage is a wall, one column wide and three lines high, that opens when Bruce takes the correct lanterns. The passage routines get the top line R in A and the column C in Y. [`draw_passage_cell` `$3ACA`](../src/room/passage_open.asm#L80) draws one tile at (`passage_row`, `passage_col`) and moves one line down. Each routine plays sound $8A. It draws two tiles of one type, and a third tile of a different type at the bottom. **Code.**

| Routine | Lines R, R+1 | Line R+2 | Used in |
|---|---|---|---|
| `open_passage` | tile $13 (code $00) | tile $14 (code $3E) | rooms 5, 8, 9 |
| `open_passage_ledge` | tile $13 | tile $17 (code $11) | rooms 6, 7 |
| `open_passage_ledge_b` | tile $13 | tile $2D (code $11) | room 8 |
| `open_passage_dark` | tile $63 (code $07) | tile $64 (code $0E) | rooms 10, 12, 14, 16 |

Tiles $13 and $14 use the codes of `charset_rooms_0_9`, and `open_passage_dark` uses the codes of `charset_rooms_10_19`. Several passages open the way to an exit marker in the map behind the wall. For example, the passage of room 10 at L4 C38 is next to marker 3 at L5 C39. **Conclusion** (from the map cells).

### Hazards

The hazards are cells that kill. When `touch_tile_gate` is set, `handle_touched_tile` sends these codes to [`touch_deadly_tile` `$304B`](../src/actor/touch_effects.asm#L75):

- $0F, $40 and $64
- $54-$5A, but not $57
- $71-$7C
- $66, only in rooms 10-19.

`touch_deadly_tile` does nothing in room 18. In the other rooms, it plays sound $8C. It removes an enemy with `remove_actor`. Bruce dies through [`set_actor_hazard_death` `$407D`](../src/room/room_hazard_draw.asm#L37), which sets `actor_state` = $19 and `actor_timer` = $10. **Code.**

The rooms make three types of moving hazards from these codes. The frame handler draws each hazard again on its passes, so the deadly code moves over the map.

**Sliders.** A slider is a small object that appears at a start column. It moves right one column per pass to an end column, and then it fades. Each of rooms 4, 5, 7, 8, 9 and 17 has one to three sliders. **Code.** **Observed** in room 4 (a run of the analysis: a small white dotted object appears at the start column, moves right and fades).

[`draw_slider0` `$4086`](../src/room/room_hazard_draw.asm#L46), `draw_slider1` and `draw_slider2` draw tile $1F + frame (look A: tiles $1F-$25). `draw_slider0_alt` to `draw_slider2_alt` add 7 (look B: tiles $26-$2C). Frame 6 is blank. The upper codes of the frames are $54-$5A. Thus a slider kills, but not in the frame with code $57. [Sliders](#sliders) gives the states. **Code.**

**Runners.** A runner is one deadly cell that moves one column per update along a track. [`draw_runner_step` `$404E`](../src/room/room_hazard_draw.asm#L9) plays sound $89 with `play_runner_sound`. It draws tile $1C (the track, code $65) at `runner_old_col`, in line `runner_row`. It draws tile $1B (the runner, code $64, deadly) at `runner_col`, in the same line. `draw_runner_step_alt` uses tiles $55 (code $67) and $54 (code $66, deadly in rooms 10-19). **Code.**

| Room | Line | Start column | Moves | Range | Direction |
|---|---|---|---|---|---|
| 7 | 11 | 5 | every pass | right: 5-35, then 5 / left: 36-5, then 36 | right while lantern L9 C2 or L9 C3 is present, left when both are taken |
| 9 | 12 | 4 | every pass | right: 4-24, then 4 / left: 24-5, then 24 | right while lantern L10 C27 or L10 C28 is present |
| 17 | 5 | 11 | every second pass (`room_state_d`) | right: 11-27, then 11 | always right |

**Burst traps.** A burst trap is a floor cell with character $60. When an actor touches it, it bursts some passes later into deadly cells. [Burst traps](#burst-traps) gives the states. **Code.**

**The floor movers of room 13.** Room 13 has 10 runner slots, and 8 of them are in use. [`room13_init` `$34C3`](../src/room/room_specific_init.asm#L159) fills the slots in `mover_dir` (0 off, $02 left, $82 right), `mover_col`, `mover_row`, `mover_old_col`, `mover_min_col` and `mover_wrap_col`. `room13_frame` calls [`update_floor_movers` `$104B`](../src/game/game_setup.asm#L169) on even passes. **Observed** (coverage).

`update_floor_movers` moves slots 8 to 0 by one column each. A left mover that goes below its minimum column starts again at its wrap column. A right mover at its wrap column starts again at its minimum column. The routine draws with `draw_runner_step`, or with `draw_runner_step_alt` on lines 5 and 10. **Observed** (coverage).

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

The values in brackets apply when `game_loop_count` is not 0. In the later game loops, the tracks are longer. **Code.**

## The data

### The per-room tables

All per-room tables have 20 entries, one for each room, and the index is `room` (0-19). The reference gives the address of each table, and decodes the tables of addresses. **Code.**

| Table | Each entry | Read by |
|---|---|---|
| `room_map_ptr_lo` / `room_map_ptr_hi` | Low and high byte of the map address. Entry 20 repeats `room_map_19` and is not used. | `draw_room` |
| `room_colour_fill` | Colour RAM value of the play area. Bit 3 = multicolour, bits 0-2 = the colour of the %11 pixels. | `draw_room` |
| `room_palette_ptr` | Address of the band palette records: 3 bytes BGCOL0, BGCOL1, BGCOL2 per band. | `irq_game_bottom` |
| `room_split_list_ptr` | Address of the raster split list: raster lines, ended by $FD. | `irq_game_bottom` |
| `room_aux_ptr` | Address of a 20-byte block that has no effect. | `draw_room` |
| `exit2_dest_room` .. `exit5_dest_room` | Destination room of exit marker 2, 3, 4, 5. | `take_exit2` .. `take_exit5` |
| `exit2_entry_x` .. `exit5_entry_x` | Bruce's X in the new room. 0 = no exit for this marker. | `take_exit2` .. `take_exit5` |
| `exit2_entry_y` .. `exit5_entry_y` | Bruce's Y in the new room. | `take_exit2` .. `take_exit5` |
| `spawn_a_x` / `spawn_a_y` | Start point A: Bruce's start position, and one enemy start point. | `place_bruce_at_room_start`, `spawn_actor` |
| `spawn_b_x` / `spawn_b_y` | Start point B: the other enemy start point. | `spawn_actor` |
| `room_no_enemies` | $FF = no Yamo and no Ninja in the room, 0 = enemies. | `draw_room` |
| `ninja_room_delay` / `ninja_respawn_delay` | Passes before the Ninja first appears / appears again. | `draw_room`, `update_ninja_spawn`, `reset_spawn_timer` |
| `ninja_spawn_side` | Start point of the Ninja. Only tested for 0. | `spawn_actor` |
| `yamo_room_delay` / `yamo_respawn_delay` | Passes before Yamo first appears / appears again. | `draw_room`, `update_yamo_spawn`, `reset_spawn_timer` |
| `yamo_spawn_side` | Start point of Yamo (and of the Ninja): 0 = random. Else, 3 times in 4, bit 7 selects it (clear = A, set = B). | `spawn_actor` |
| `room_lantern_count_init` | Lanterns of the room at a game start. | `reset_lantern_counts` |
| `lantern_list_ptr` | 21 words: address of the lantern list of the room. Entry 20 is `lantern_list_spare` and is not used. | `check_lantern_pickup`, `setup_room_lanterns_and_init`, `reset_room_lanterns`, `swap_player_lanterns` |
| `room_init_handlers` | Init handler address - 1 (RTS table). | `room_init_dispatch` |
| `room_frame_handlers` | Frame handler address - 1 (RTS table). | `run_room_frame_handler` |

No code writes these tables. RAM holds the state of the rooms:

| Variable | Each entry | Written by |
|---|---|---|
| `room_lanterns_left` | 1 byte per room: lanterns not yet taken. | `reset_lantern_counts`, `check_lantern_pickup` |
| `room_unvisited` | 1 byte per room and player at room*2 + `current_player`: 1 = not yet visited. | `init_game_variables`, `reset_unvisited_rooms`, `draw_room` |
| `room_state_a` .. `room_state_e` | Five scratch bytes of the current room: timers, step counters and one-shot flags. | `room_init_clear_vars`, the room handlers |

### Graphics of each room

A room has one charset, one colour for the play area, and a maximum of four colour bands from top to bottom. `draw_room` sets [`room_vmcsb` `$00F2`](../src/constants.asm#L117), the VMCSB value that the raster interrupt writes for the play area. **Code.**

- $38 = `charset_rooms_0_9` for rooms 0-9
- $3C = `charset_wizard` for room 18
- $3A = `charset_rooms_10_19` for the other rooms

The cold start builds these charsets from four sources of 128 tiles each. **Code.**

- `room_charset_a` for rooms 0-9
- `room_charset_b` for rooms 10-17 and 19
- `room_charset_c` for room 18
- `room_charset_d` for room 18 after Bruce defeats the wizard (`charset_wizard_flash`, $3E)

On each frame, the raster interrupt [`irq_game_bottom` `$48C1`](../src/irq/game_irq.asm#L12) copies 12 bytes from the palette records of `room_palette_ptr`. It also copies the split list of `room_split_list_ptr`. Thus a room can have a maximum of 4 colour bands. A split line is the raster line where the next band starts. The colours change 3 lines later. The colour in a band record is the low nibble of each byte. **Code.**

The background colours in the table agree with the screenshots. **Observed.**

| Room | Map bytes | Colour fill | Charset | Palette records | Split lines | Bands BGCOL0, BGCOL1, BGCOL2 |
|---|---|---|---|---|---|---|
| 0 | 272 | $FE | $38 | `room_palette_r0_3` | `split_list_r0`: $78, $97 | 11,1,14 / 11,2,1 / 12,2,1 |
| 1 | 309 | $FE | $38 | `room_palette_r0_3` | `split_list_r1`: $78, $97 | as room 0 |
| 2 | 351 | $FE | $38 | `room_palette_r0_3` | `split_list_r2`: $78, $97 | as room 0 |
| 3 | 382 | $FE | $38 | `room_palette_r0_3` | `split_list_r3`: $62, $97 | as room 0 |
| 4 | 359 | $FC | $38 | `room_palette_r4_6` | `split_list_none` | 6,14,1 |
| 5 | 347 | $FC | $38 | `room_palette_r4_6` | none | 6,14,1 |
| 6 | 330 | $FC | $38 | `room_palette_r4_6` | none | 6,14,1 |
| 7 | 234 | $FF | $38 | `room_palette_r7_9` | none | 8,9,1 |
| 8 | 384 | $FA | $38 | `room_palette_r7_9` | none | 8,9,1 |
| 9 | 327 | $FA | $38 | `room_palette_r7_9` | none | 8,9,1 |
| 10 | 372 | $F9 | $3A | `room_palette_r10_12_14_16` | `split_list_r10_12_14_16`: $56 | 6,14,11 / 12,14,11 |
| 11 | 247 | $FB | $3A | `room_palette_r11` | none | 4,14,11 |
| 12 | 387 | $F9 | $3A | `room_palette_r10_12_14_16` | $56 | 6,14,11 / 12,14,11 |
| 13 | 128 | $FA | $3A | `room_palette_r13` | none | 14,6,1 |
| 14 | 366 | $F9 | $3A | `room_palette_r10_12_14_16` | $56 | 6,14,11 / 12,14,11 |
| 15 | 168 | $FC | $3A | `room_palette_r15` | `split_list_r15`: $B6, $C7 | 14,6,11 / 12,14,1 / 15,8,12 |
| 16 | 305 | $F9 | $3A | `room_palette_r10_12_14_16` | $56 | 6,14,11 / 12,14,11 |
| 17 | 259 | $FF | $3A | `room_palette_r17` | none | 12,8,11 |
| 18 | 336 | $FE | $3C | `room_palette_r18` | none | 0,14,4 |
| 19 | 416 | $FF | $3A | `room_palette_r19` | none | 6,2,1 |

### Exits

The four exit sets, all 20 entries. Each cell gives the destination room, the entry X and the entry Y. "-" means entry X 0. **Code.**

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

The markers are cells of the maps, or cells of tiles that the room code draws later. The catalogue gives the place of each marker. Some entries have no marker, in the map or in a tile of the room code:

- room 3, marker 5
- room 6, markers 3, 4 and 5
- room 7, markers 2 and 5.

**Code** (decode of the 20 maps and of the tiles that the handlers draw). **Conclusion:** Bruce cannot use these exits.

### Start points and enemies

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

- **Enemy-free rooms.** [`room_no_enemies` `$4C9E`](../src/room/room_tables.asm#L164) is $FF for rooms 3, 8, 9, 11, 13, 17, 18 and 19. `draw_room` copies it to `room_no_enemy_flag`. While the flag is not 0, `main_loop` skips `tick_spawn_timers`, `update_yamo_spawn`, `update_ninja_spawn` and `check_fight_collisions`. Rooms 13 and 17 have delay values, but the flag makes them unused. **Code.**
- **Delays.** The units are passes. `draw_room` loads `ninja_spawn_timer` and `yamo_spawn_timer` from the "first" columns. When `game_loop_count` is not 0, both timers are 3. This occurs after a player completes the game one time. When player 2 controls Yamo, Yamo's timer is 8. **Code.**
- **Sides.** [`spawn_actor` `$0B8E`](../src/actor/actor_spawn.asm#L20) tests `ninja_spawn_side` for 0. But on the Ninja path at `spawn_actor_ninja_side`, it takes the side bit from `yamo_spawn_side`. **Code.** **Conclusion:** this is probably a slip of the original program. The rebuild keeps it.

### Lantern lists

[`lantern_list_ptr` `$4CE2`](../src/room/lantern_lists.asm#L13) points each room to a list of 4-byte records. A $FF byte ends the list. **Code.**

| Byte | Meaning |
|---|---|
| +0 | State: 1 = present, 0 = taken, $FF = end of the list. |
| +1 | Replacement code: drawn in the cell after the pickup (code AND $7F upper row, code OR $80 lower row). $9E, $9F or $92. |
| +2 | Column (0-39). |
| +3 | Text line. |

For example, [`lantern_list_room3` `$4D67`](../src/room/lantern_lists.asm#L38) holds `01 9E 1D 0A` `01 9F 26 0A` `FF`. Record 0 is present, with replacement $9E (upper row $1E, lower row $9E), at column $1D = 29 and line $0A = 10. Record 1 is present, with replacement $9F, at column 38 and line 10. The end byte follows. **Code.**

[`room_lantern_count_init` `$4CCE`](../src/room/lantern_counts.asm#L7) holds the number of lanterns of each room, 90 lanterns in total. `reset_lantern_counts` copies the counts to `room_lanterns_left` at a game start (`init_game_variables`). It also copies them when room 19 starts the next game loop. Each count equals the number of records in the list of the room. Rooms 13 and 19 have one dummy record (01 00 00 00) and a count of 0. The dummy record could match only at line 0, column 0. **Code.**

| Room | Count | Lanterns | Replacement codes |
|---|---|---|---|
| 0 | 6 | L7 C31, L7 C38, L10 C2, L10 C25, L10 C29, L10 C38 | $9F $92 $9F $9F $92 $92 |
| 1 | 6 | L7 C9, L7 C30, L10 C6, L10 C15, L10 C24, L10 C32 | $9E $9F $92 $9E $9F $92 |
| 2 | 10 | L7 C5, L7 C9, L7 C22, L7 C26, L7 C30, L10 C5, L10 C9, L10 C15, L10 C21, L10 C27 | $92 $9E $9F $9E $9F $9E $9F $9E $9F $9E |
| 3 | 2 | L10 C29, L10 C38 | $9E $9F |
| 4 | 2 | L4 C11, L4 C28 | $9E $9F |
| 5 | 10 | L3 C2, L3 C6, L3 C28, L3 C32, L3 C38, L6 C30, L10 C2, L10 C23, L10 C26, L10 C30 | $9E $9E $9F $9E $9F $9F $9E $9F $9F $9E |
| 6 | 8 | L5 C8, L5 C10, L5 C14, L5 C22, L5 C26, L5 C28, L9 C6, L9 C30 | $9F $9E $9F $9F $9F $9E $9F $9E |
| 7 | 13 | L2 C3, L2 C12, L2 C13, L2 C25, L2 C26, L5 C5, L5 C6, L5 C12, L5 C13, L5 C25, L5 C26, L9 C2, L9 C3 | $9E $9F alternating |
| 8 | 4 | L3 C15, L3 C24, L7 C6, L7 C33 | $9F $9F $9E $9F |
| 9 | 5 | L2 C32, L7 C15, L10 C27, L10 C28, L10 C32 | $9F $9E $9E $9F $9E |
| 10 | 3 | L4 C1, L7 C30, L10 C30 | $9F $9F $9F |
| 11 | 3 | L3 C18, L3 C21, L10 C7 | $9E $9F $9F |
| 12 | 3 | L4 C36, L7 C36, L10 C36 | $9E $9E $9E |
| 13 | 0 | dummy record 01 00 00 00 | - |
| 14 | 4 | L7 C9, L7 C30, L10 C9, L10 C30 | $9F $9E $9F $9E |
| 15 | 6 | L3 C19, L3 C21, L4 C14, L4 C26, L6 C13, L6 C27 | $9F $9E $9E $9F $9E $9F |
| 16 | 2 | L4 C32, L7 C5 | $9E $9F |
| 17 | 2 | L10 C38, L11 C31 | $9E $9E |
| 18 | 1 | L11 C37 | $9E |
| 19 | 0 | dummy record 01 00 00 00 | - |

The list of room N is `lantern_list_roomN`. The room code reads the state byte of single records at an offset. For example, `lantern_list_room5+$20` (`$4D99`) is the lantern at L10 C26. The catalogue names each record that a handler tests.

### The room aux blocks

[`room_aux_ptr` `$4AA8`](../src/room/room_tables.asm#L26) points each room to a block in `$4AD0-$4B33`, from `room_aux_r0_3` to `room_aux_r19`. The rooms share the blocks in the same groups as the palettes. The blocks are groups of 5 bytes, for example $04,$00,$06,$88,$0E, and a block runs into the next blocks. `draw_room` copies 20 bytes to `room_band_colours` (`$0153-$0166`). But on each frame, `irq_game_bottom` writes `$0153-$015E` again from `room_palette_ptr`. No code reads `$015F-$0166`.

**Code**, and **Observed** in a trace of the analysis (a store to `$0153` on each frame). **Conclusion:** dead data, perhaps an older form of the band palettes.

## The map format

A map is a run-length coded stream of cells. It fills the play area from line 2 to line 12: 11 lines of 40 cells, 440 cells in total. A long row of the same cell, for example sky or floor, takes only 2 bytes. Room 13 takes 128 bytes, and room 19 takes 416 bytes. **Code.**

### Where the data is

[`room_map_ptr_lo` `$4B34`](../src/room/room_tables.asm#L69) and `room_map_ptr_hi` give the map of each room. The maps [`room_map_00` `$68F9`](../src/room/room_maps_00_04.asm#L18) to `room_map_19` follow one after the other in `$68F9-$817F`. `draw_room` decodes them, from `draw_room_next_code`. **Code.**

### The byte layout

A map is a stream of codes:

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
| 7 | 1 = colour RAM $F8 for both rows (multicolour, colour 0) through `map_tile_set_black`. 0 = the cell keeps the colour of `room_colour_fill`. |

The cells fill 40 columns per text line, from line 2 (screen row 3, `$8C78`) to line 12. **Code.**

### The decoder

The decoder is the end of `draw_room`, from [`draw_room_next_code` `$0AD7`](../src/room/draw_room.asm#L178). It keeps four pointers: the upper and lower screen row of the cell, and the same two rows in colour RAM. **Code.**

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

[`room_draw_step_cell` `$485B`](../src/room/draw_helpers.asm#L9) adds 40 to all four pointers after each 40 cells. The steps of the cells already moved the pointers across one screen row. A cell is two rows high, so one more row moves them to the next text line. **Code.**

The decoder does not count the cells. It stops only at the $80 code. A map with too many cells writes past the end of the play area (see [Map sizes and the overflow](#map-sizes-and-the-overflow)). **Code.**

**The protection can empty three maps.** The protection check of room 10 can fail. Then [`room10_frame_protection_check` `$3CA7`](../src/room/room_frames_8_11.asm#L289) writes $80 into the first byte of `room_map_00`, `room_map_05` and `room_map_01`. The decoder stops at once, so these rooms show empty in each later game. With `PROTECTION` = 0, the default build, the check never fails. See [protection.md](protection.md). **Code.**

### A worked example: the first two lines of room 0

These are the bytes of `room_map_00`, decoded by hand. Line 2 starts at screen `$8C78` / `$8CA0` and colour RAM `$D878` / `$D8A0`. Line 3 starts at `$8CC8` / `$8CF0`. Each cell byte with bit 7 set makes the colour RAM of its cell $F8. The table calls this colour "black".

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

Thus the first cell writes $09 to `$8C78`, $89 to `$8CA0`, and $F8 to `$D878` and `$D8A0`. The cell of column 22 in line 3 writes $00 to `$8CDE` and $80 to `$8D06`. It does not change the colour RAM, which stays $FE. The map ends with $80 at `$6A08`, after 440 cells. **Code** (the decode of the image bytes).

![Room 0 about 250 frames after Bruce entered it](images/rooms/room00.png)

The screenshot shows room 0. The top lines are the sky and the mountains of this map. **Observed.**

### Map sizes and the overflow

Fourteen maps decode to exactly 440 cells: rooms 0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 16 and 19. [Graphics of each room](#graphics-of-each-room) gives the bytes of each map. **Code** (decode of the 20 maps).

**Six rooms write 2 bytes into a contact mask.** The maps of rooms 4, 7, 10, 13, 17 and 18 decode to 442 cells, two more than the 440 cells of lines 2-12. Each of these maps ends with a repeat run of cell $00 before the $80 end code. The run is $02 $00, or $03 $00 in room 17. The two extra cells are line 13, columns 0 and 1. **Code** (decode of the 20 maps).

| Write | Address | Value | What is there |
|---|---|---|---|
| upper row | `$8FE8-$8FE9` | $00 | screen row 25: the spare bytes after the screen, before the sprite pointers at `$8FF8` |
| lower row | `$9010-$9011` | $80 | the contact mask of actor frame 0 (`$9000`), column 0, rows 16-17 |
| colour RAM | - | - | not written: the cells have bit 7 clear |

The cold start builds the contact masks only one time. Thus the first visit of one of these rooms changes the mask bytes of Bruce's frame 0 at `$9010-$9011`. The bytes change from $0C, $0C to $80, $80 for the remainder of the session. **Observed** (a run of the analysis: after a visit to room 4, 7 or 10, the mask reads `0F 0C 80 80 0C 3C` and not `0F 0C 0C 0C 0C 3C`).

**Conclusion:** the effect is small. The background contact test of that frame sees one pixel pair more and two less in one column. The rebuild keeps the bug, because the source is identical to the program.

### The assets

The maps use the room charsets. The reference shows the four charset sources in hires and multicolour on [the graphics page](reference/graphics.md#room_charset_a).

![The 128 tiles of room_charset_a, used by rooms 0-9](reference/images/room_charset_a-multicolour.png)

The image shows the source charset of rooms 0-9 in multicolour, before the cold start doubles the height of each tile.

The screenshots of all 20 rooms are in `images/rooms/` (`room00.png` to `room19.png`). They come from emulator runs, about 250 frames after Bruce entered each room. The catalogue shows each screenshot in the section of its room. The project has no script that decodes the maps to images.

## The state machines

### The one-shot events

Most frame handlers do an action one time per visit, for example they open a passage when Bruce takes a lantern. They all use the same pattern. The flag is one of the scratch bytes [`room_state_a` `$4E97`](../src/room/room_dispatch.asm#L7) to `room_state_e`:

```
lda room_state_x
bmi skip          ; $FF: already done
<condition>       ; Z = 1 when the event must happen
bne skip
dec room_state_x  ; 0 -> $FF
<action>          ; draw tiles, play a sound
```

[`room_init_clear_vars` `$33B3`](../src/room/lantern_pickup.asm#L128) sets the flag to 0 at each room entry. Thus the action occurs again at each visit while its condition is true. The program draws the map again at each visit and does not keep the tile changes. So the handler draws them again. **Code.**

An init value 1 makes the action run on two passes (rooms 12, 14, 15). An init value 3 gives 4 steps (the trapdoors of rooms 1 and 3). Room 17 uses the opposite test, `beq` on a flag that the init sets to 1, and does the action one time. **Code.**

~~~mermaid
stateDiagram-v2
  state "Armed (room_state = 0)" as Armed
  state "Done (room_state = $FF)" as Done
  [*] --> Armed: room_init_clear_vars
  Armed --> Done: condition true, action drawn
  Done --> [*]: next room entry
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Armed (0) | the lanterns of the condition are taken | Done ($FF), tiles drawn | the room frame handler |
| Done ($FF) | - | Done | the `bmi` test |
| any | room entry | Armed | `room_init_clear_vars` |

### Sliders

Each slider has a slot n with three bytes: [`slider_col` `$0071`](../src/constants.asm#L68) + n, `slider_row` + n and `slider_timer` + n. The init handler sets them, and the frame handler runs the state machine on each pass. The timer counts up from a negative wait value to 0. Then it counts the frames of the slider. Thus a wait value $A0 waits 96 passes. **Code.**

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
| Waiting | `slider_timer` + 1 is still negative | Waiting | `room04_frame_slider0` (and the same code in each room) |
| Waiting | `slider_timer` + 1 = 0 | Appear: frame 0 | `room04_frame_slider0_frame` |
| Appear | timer 1, 2 | frame 1, 2 drawn | `room04_frame_slider0_draw` |
| Appear / Move | timer = 3, column < end | frame 6 at the old column, column + 1, timer = 2, frame 2 at the new column | `room04_frame_slider0_step` |
| Move | timer = 3, column >= end | At end: frame 3 | `room04_frame_slider0_step` |
| At end / Fade | timer 4, 5, 6 | frames 4, 5, 6 (6 = blank) | `room04_frame_slider0_draw` |
| Fade | timer = 7 | Waiting: timer = wait value, column = start | `room04_frame_slider0_reset` |

All sliders:

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

Room 17 runs its three slots in one loop, [`room17_frame_slider_loop` `$3FDC`](../src/room/room_frames_12_17.asm#L248), with the index in `temp_counter`. Some lanterns of rooms 4 and 5 guard a slider. When Bruce takes such a lantern, the handler draws frame 6 (blank), and the slider stops. **Code.**

### Burst traps

A burst trap is a floor cell with character $60. Rooms 6, 7, 10, 11, 12, 14, 16 and 17 call [`update_burst_traps` `$3228`](../src/room/room_misc_support.asm#L33) from their frame handler. A maximum of three traps can burst at the same time. **Code**, and **Observed** (coverage: the trap stages ran).

1. [`touch_trap_tile` `$306B`](../src/actor/touch_effects.asm#L101) runs when an actor touches character $60. The colour RAM of the cell (AND 7) must not be 5.
2. A free slot n gets `burst_trap_timer` + n = 1, `burst_trap_row` + n = line - 1 and `burst_trap_col` + n = column - 1.
3. The colour RAM of the cell becomes $FD, so the cell does not trigger again. When all 3 slots are busy, nothing occurs.
4. `update_burst_traps` increments each active slot on each pass. It acts on the value before the increment.

~~~mermaid
stateDiagram-v2
  state "Free (timer 0)" as Free
  state "Armed (timer 1-7)" as Armed
  state "Small burst (8)" as Small
  state "Large burst (12)" as Large
  state "Small again (16)" as Small2
  state "Debris (20)" as Debris
  [*] --> Free
  Free --> Armed: touch_trap_tile
  Armed --> Small: timer = 8
  Small --> Large: timer = 12
  Large --> Small2: timer = 16
  Small2 --> Debris: timer = 20
  Debris --> Free: timer = 24
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Free | an actor touches an armed $60 cell | Armed, timer 1 | `touch_trap_tile` |
| Armed | timer = $08 | sound $8D (`play_burst_sound`), tiles $2F/$30 (codes $71-$76) at (row, col) and (row+1, col) | `update_burst_traps_active`, `update_burst_traps_draw_small` |
| Small burst | timer = $0C | tiles $31/$32 (codes $77-$7C) | `update_burst_traps_stage_large` |
| Large burst | timer = $10 | tiles $2F/$30 again | `update_burst_traps_stage_small2` |
| Small again | timer = $14 | tile $00 (blank) on the row, tile $33 (codes $7D $60 $7D) below, colour $F8 on the $60 cell: armed again | `update_burst_traps_stage_small2` |
| Debris | timer = $18 | timer = 0, slot free | `update_burst_traps_stage_free` |

The burst codes $71-$7C kill on contact. The burst is 3 cells wide and 2 lines high. The trap cell is in the middle of its lower line. **Code.**

## Still open

- What are the sliders and runners in game terms (sparks, flames?). The names are neutral. A close screenshot of room 4 and room 17 can answer it.
- Room 18 has exit markers 4 and 5 in the wizard graphics (lines 2-9). Their entry X is 0, so `take_exit5` would send Bruce to room 0 at X = 0, Y = 0. `check_exit_edge` allows this only at the top edge after a move up, or at the right edge (column 38 of line 2). Can Bruce get to these cells? A run that climbs in room 18 can answer it.
- Room 5 has openings at L3 C30 and L6 C32, and markers 3 and 4 at L4 C39 and L7 C39. Do the openings block the way to the markers while room 6 has lanterns left? A run with Bruce in room 5 and lanterns of room 6 left can answer it.
- What were the room aux blocks for?
