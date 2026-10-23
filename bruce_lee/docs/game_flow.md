# Bruce Lee: the game flow and the map of the rooms

In Bruce Lee, the title screen plays the attract demo when nobody plays, and F7 or fire starts a game. In a game, Bruce walks through 20 rooms and leaves each room at an exit marker on the edge of the screen. When he dies, he loses a fall, and in a two-player game the other player then gets the joystick. After the wizard of room 18, room 19 congratulates the player, and the game starts again in room 0, harder than before. This page follows that cycle from the cold start to the next game loop. It also decodes the four sets of exit tables into the map of the rooms, with the condition that opens each way.

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *frame* is one PAL frame (1/50 s). A *pass* is one run of [`main_loop` `$1BC2`](../src/game/game_main_loop.asm#L23) (at least 3 frames).
- *Room play* is `main_loop` with [`game_mode` `$0104`](../src/constants.asm#L130) = 1. The *demo* is the same loop with `game_mode` = 0.
- A *fall* is a life. [`falls_left` `$0028`](../src/constants.asm#L27) counts them ("FALLS" on the status line).
- A room is *cleared* when it has no lanterns left: [`room_lanterns_left` `$002A`](../src/constants.asm#L29) + room = 0.
- An *exit marker* is a map character 2, 3, 4 or 5 (the top character of a cell). Marker N uses the exit tables of set N.
- A *cell* is a double-height map character. Cell row R is screen rows 2R-1 and 2R (rows 0 and 1 are the status line). Cell columns are 0-39.
- *Entry X/Y* is the position of Bruce in the new room, in actor units. Sprite X = 2 * X. Sprite Y = Y + `$1D`.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

~~~mermaid
flowchart TB
  A["Cold start: build the tables and charsets"] --> B["Title screen and options"]
  B -->|"2400 frames without a key"| C["Attract demo"]
  C -->|"fire, F1 or a lost fall"| B
  B -->|"F7 or fire"| D["PLAYER n screen"]
  D --> E["Room play"]
  E -->|"exit marker at the edge"| F["Room change"]
  F --> E
  E -->|"lost fall"| G["Next turn or game over"]
  G -->|"a player has falls"| D
  G -->|"no falls left"| B
  E -->|"wizard defeated"| H["Room 19: congratulations"]
  H -->|"next game loop, room 0"| E
~~~

The cold start runs one time. [`cold_start` `$0400`](../src/game/cold_start.asm#L22) builds the random table, the fonts, the charsets and the contact masks. Then it continues into [`restart_to_title` `$050F`](../src/game/title_demo_start.asm#L9). The restart is also the way back to the title when the player presses F1 in a game. It resets the stack, stops the music and prepares the game variables. Then it goes to the title screen of [`show_title_screen` `$0584`](../src/game/title_demo_start.asm#L83). **Code**

The title has a countdown, [`title_countdown` `$0049`](../src/constants.asm#L35), of 2400 frames. Each option key (F3, F5, L, R, shift-L, shift-R) starts the countdown again. When the countdown reaches 0, [`start_attract_demo` `$0531`](../src/game/title_demo_start.asm#L32) saves the options and starts the demo. **Code**

The demo plays room 0 with one player against a computer Yamo, and `game_mode` = 0. Bruce moves by the joystick input of a recording, [`demo_input_stream` `$F300`](../src/input/demo_input.asm#L12). Fire on port 1 or F1 stops the demo and goes to the restart. When Bruce loses a fall in the demo, the title shows again with its tune. **Code**

F7 or fire on port 1 starts a game. `title_menu_start_game` waits until the player releases fire, waits 16 more frames and returns. Then `show_title_screen` continues into [`start_new_game` `$070E`](../src/game/title_demo_start.asm#L283). It sets player 1, shows the PLAYER 1 screen, draws room 0 with [`draw_room` `$09BC`](../src/room/draw_room.asm#L28) and starts the main loop. From here the game is room play, one pass after another. Room play stops when Bruce leaves the room or loses a fall, or when the player presses F1. **Code**

A run from the cold start snapshot (PAL) showed the timing of these steps. **Observed**

- `restart_to_title` ran 79 frames after `cold_start`, and `show_title_screen` 2 frames later.
- `start_attract_demo` ran 2394 frames after a `title_countdown` of `$095C`.
- The demo ended about 1714 frames after `start_attract_demo`: Bruce was knocked out (`actor_state` = `$13`) and [`check_actor_knockouts_bruce` `$2D79`](../src/actor/actor_helpers.asm#L33) jumped to `lose_fall`. At that time `demo_input_ptr` was `$F539`: the demo read 569 bytes of `demo_input_stream`.
- With F7 written into `key_code` (`key_ready` = 1) on the title, `start_new_game` ran after 15 frames. The PLAYER 1 screen lasted 64 frames, `draw_room` followed, and the first pass of `main_loop` came 5 frames later.

![The attract demo](images/screens/demo.png)

The attract demo in room 0. It plays with the recorded input of `demo_input_stream`.

### A lost fall and two players

When Bruce dies or is knocked out, the current player loses a fall. In a two-player game the turn then passes to the other player, so the players take turns after every lost fall, not after every game. Each player has his own block of variables, which the game swaps on each change of the player. [`lose_fall` `$1818`](../src/game/lose_fall_game_over.asm#L14) does the work in this order:

1. It silences the sound. In the demo it goes to the title.
2. It decrements `falls_left`. Below 0, it goes to [`game_over` `$188E`](../src/game/lose_fall_game_over.asm#L82).
3. [`next_turn` `$182A`](../src/game/lose_fall_game_over.asm#L23) sets `actor_energy` of all three actors to `$24`, and clears `enemy_follow_x` and the fireball sprites.
4. With two players (`option_two_players` = 1) and the other player not out ([`inactive_player_state` `$439F`](../src/game/fireball_text_score_vars_4392.asm#L24), the parked `falls_left`, >= 0), `current_player` changes. **Code**
5. `show_player_screen` shows PLAYER 1 or PLAYER 2.
6. On a change of the player, [`next_turn_swap_block_loop` `$1862`](../src/game/lose_fall_game_over.asm#L52) swaps the player block `$0028-$0043` with `inactive_player_state`. The block holds `falls_left`, `room`, `room_lanterns_left`, `game_loop_count` and the score. `swap_player_lanterns` swaps the lantern flags of all rooms. The swap also includes `bonus_fall_next_score`.
7. `reset_play_state` draws the game screen and spawns Bruce. [`place_bruce_at_room_start` `$3217`](../src/room/room_misc_support.asm#L11) puts him at the start point of his room (`spawn_a_x`, `spawn_a_y`) and enters the room.

![The PLAYER 2 screen](images/screens/player2_screen.png)

The PLAYER 2 screen of a two-player game: the turn passed to player 2 after a lost fall.

**Conclusion.** Each player keeps his own room, lanterns, falls, score and game loop. After the game over of one player, the other player plays on alone: `game_over` goes to `next_turn`, which changes `current_player` and swaps the blocks.

![The game over screen](images/screens/game_over.png)

The game over screen of `game_over`: GAME OVER, PLAYER 1 and the score in big digits.

### The next game loop

Room 19 is the congratulations room. When its countdown ends, [`room19_frame` `$4272`](../src/room/ending_room.asm#L27) adds 1 to [`game_loop_count` `$0040`](../src/constants.asm#L30), puts all lanterns back and sends Bruce to room 0 for the next loop. A `game_loop_count` above 0 makes the game harder in these places. **Code**

| Effect | Code |
|---|---|
| Yamo and the Ninja come at once in every room: both spawn timers = 3 | `draw_room` |
| Yamo respawns after 3 passes | `update_yamo_spawn` |
| An enemy pauses only 1 step after an attack | `actor_recover` |
| After an enemy hits, it pauses a short time (not `$18` steps) | `apply_fight_hits` |
| An idle enemy pauses only a short time | `wake_idle_enemies` |
| The floor movers of room 13 get longer tracks | `room13_init` |
| All lanterns are back, the first-visit bonus (2000 points) and the room 13 height bonuses of the current player are back | `room19_frame` |

### How Bruce leaves a room

An exit is not a line at the edge of the screen. It is an exit marker in the room map that Bruce must touch while he stands at an edge and moves outward. The marker number selects one of four sets of exit tables, and the current room selects the entry in the set. [`handle_touched_tile` `$2E89`](../src/actor/background_touch.asm#L61) checks the 3 characters under and beside each actor, on two cell rows. A character 2, 3, 4 or 5 jumps to `take_exit2`, `take_exit3`, `take_exit4` or `take_exit5`. Each one first asks [`check_exit_edge` `$30D4`](../src/actor/touch_effects.asm#L154) whether the actor may leave. **Code**

| Edge | Condition of `check_exit_edge` |
|---|---|
| Left | `actor_x` < `$10` and the actor moves left |
| Right | `actor_x` > `$A1` and the actor moves right |
| Bottom | `actor_y` > `$C5` and the actor falls (state `$0E`) |
| Top | `actor_y` < `$31` and the actor moves up |
| Room 11 | always allowed (the three doors are in the middle of the room) |

Then the handler reads the tables of its set with X = `room`. It writes the new room to `next_room` and loads the entry X and Y into the registers. An entry X of 0 means "no exit". Then `take_exit2`, `take_exit3` and `take_exit4` continue into the handler of the next set, which checks the edge again. `take_exit5` has no next set, so it enters the room even with X = 0. **Code**

~~~text
N = touched character (2, 3, 4 or 5)          ; handle_touched_tile
loop:
  if not check_exit_edge(actor): stop        ; carry set: no exit
  next_room = exitN_dest_room[room]
  y = exitN_entry_y[room]; x = exitN_entry_x[room]
  if x == 0 and N < 5: N = N + 1; goto loop  ; fall through to the next set
  enter_room(x, y)                           ; Bruce: change_room; enemy: remove_actor
~~~

When an enemy takes an exit, `enter_room` only removes the enemy. When Bruce takes an exit, [`change_room` `$2F9A`](../src/actor/background_touch.asm#L234) stores his entry position and the new room. Each enemy that was in the room keeps its energy and gets Bruce's entry position in `enemy_follow_x` and `enemy_follow_y`, so it can follow him. Then the game resets the stack, `draw_room` draws the new room and the main loop starts again. **Code**

Two other ways change the room without an exit. When Bruce hits a wall and has no move history left, `act_wall_bump_still_in` enters the same room again at its start point. When Bruce enters room 11 and rooms 12, 14 and 16 are clear, `draw_room` sends him to room 13. **Code**

## The exit tables

Twelve tables of 20 bytes hold the exits, one byte for each room. Each set N (2 to 5) has three tables: the new room, the entry X and the entry Y. An entry X of 0 means that the set has no exit in that room. **Code**

| Table | Address | Size | Entry |
|---|---|---|---|
| `exit2_dest_room` / `exit3_dest_room` / `exit4_dest_room` / `exit5_dest_room` | `$4B5E` / `$4B72` / `$4B86` / `$4B9A` | 20 bytes each | the new room, index = current room |
| `exit2_entry_x` / `exit3_entry_x` / `exit4_entry_x` / `exit5_entry_x` | `$4BFE` / `$4C26` / `$4C4E` / `$4C76` | 20 bytes each | Bruce's X in the new room, 0 = no exit |
| `exit2_entry_y` / `exit3_entry_y` / `exit4_entry_y` / `exit5_entry_y` | `$4C12` / `$4C3A` / `$4C62` / `$4C8A` | 20 bytes each | Bruce's Y in the new room |

### All entries

Each cell gives the new room (entry X, entry Y). "-" means that the entry X is 0.

| Room | Marker 2 | Marker 3 | Marker 4 | Marker 5 |
|---|---|---|---|---|
| 0 | 1 (`$10`, `$92`) | - | - | 1 (`$0F`, `$62`) |
| 1 | 0 (`$A0`, `$92`) | 5 (`$2C`, `$32`) | 0 (`$A1`, `$62`) | 2 (`$10`, `$62`) |
| 2 | - | - | 1 (`$A1`, `$62`) | 3 (`$10`, `$C4`) |
| 3 | - | 10 (`$10`, `$B0`) | 2 (`$A1`, `$C5`) | 0 (`$10`, `$62`) |
| 4 | 5 (`$10`, `$C2`) | 7 (`$1F`, `$32`) | - | - |
| 5 | 4 (`$9C`, `$51`) | 6 (`$10`, `$40`) | 6 (`$10`, `$74`) | 1 (`$58`, `$66`) |
| 6 | 5 (`$A0`, `$80`) | 5 (`$A0`, `$66`) | 2 (`$16`, `$51`) | 0 (`$20`, `$51`) |
| 7 | 0 (`$30`, `$51`) | 8 (`$0F`, `$46`) | 8 (`$10`, `$C0`) | 0 (`$20`, `$51`) |
| 8 | 7 (`$A0`, `$74`) | 9 (`$10`, `$53`) | 7 (`$A1`, `$B5`) | 9 (`$0F`, `$C6`) |
| 9 | 8 (`$A0`, `$47`) | 8 (`$A0`, `$C0`) | 6 (`$9D`, `$C7`) | - |
| 10 | 3 (`$A0`, `$C4`) | 11 (`$10`, `$C4`) | - | - |
| 11 | 10 (`$A0`, `$5A`) | 12 (`$10`, `$5C`) | 14 (`$10`, `$5E`) | 16 (`$10`, `$5C`) |
| 12 | - | 11 (`$34`, `$BE`) | 14 (`$10`, `$BE`) | - |
| 13 | 15 (`$10`, `$C3`) | - | - | - |
| 14 | - | 11 (`$50`, `$BE`) | 12 (`$A0`, `$BE`) | 16 (`$10`, `$BE`) |
| 15 | 13 (`$A0`, `$C4`) | 17 (`$10`, `$B3`) | - | - |
| 16 | - | 11 (`$80`, `$BE`) | 14 (`$A0`, `$BE`) | - |
| 17 | 15 (`$A0`, `$93`) | 18 (`$10`, `$C6`) | - | - |
| 18 | 17 (`$A0`, `$44`) | 19 (`$10`, `$96`) | - | - |
| 19 | - | - | - | - |

### The exits in play

A table entry counts only when its marker is on the screen. Most markers are in the room map (decoded from [`room_map_ptr_lo` `$4B34`](../src/room/room_tables.asm#L69) and `room_map_ptr_hi`). The frame handler of the room ([`room_frame_handlers` `$4EC4`](../src/room/room_dispatch.asm#L28)) draws the other markers later. Many map markers stand behind a wall. A passage that the room code opens makes them reachable.

The map decode and the handler code give the table below. **Code** The screen of room 6 in a run (`rooms/room06.vsf`) showed only marker 2, at cell row 6, column 0. **Observed** The handler of each room is on [rooms_catalogue.md](rooms_catalogue.md).

| Room | Marker | Place (cell row, column) | Leads to | Condition | Code |
|---|---|---|---|---|---|
| 0 | 2 | 8, 39 (right) | 1 | none | map |
| 0 | 5 | 5, 39 (right) | 1 | none | map |
| 1 | 2 | 8, 0 (left) | 0 | none | map |
| 1 | 4 | 5, 0 (left) | 0 | none | map |
| 1 | 5 | 5, 39 (right) | 2 | none | map |
| 1 | 3 | 12, 19-21 (trapdoor in the floor) | 5 | rooms 0, 1 and 2 cleared while room 6 is not cleared | `room01_frame`, `msg_trapdoor_open_4` |
| 2 | 4 | 5, 0 (left) | 1 | none | map |
| 2 | 5 | 11, 39 (floor, right) | 3 | room 6 cleared | `room02_frame`, `msg_room2_gap_top` |
| 3 | 4 | 11, 0 (left) | 2 | none | map |
| 3 | 3 | 12, 31-33 (trapdoor) | 10 | room 3 cleared | `room03_frame`, `msg_trapdoor_open_4` |
| 4 | 2 | 4, 39 (right) | 5 | none | map |
| 4 | 3 | 12, 1-4 (floor) | 7 | none | map |
| 5 | 3 | 4, 39 (right) | 6 | none | map |
| 5 | 4 | 7, 39 (right) | 6 | none | map |
| 5 | 2 | 11, 0 (left) | 4 | lantern of row 10, column 2 taken: passage at column 0 and the marker | `room05_frame`, `msg_room5_gap_edge` |
| 5 | 5 | 2, 35 (top) | 1 | room 6 cleared and the lantern of row 3, column 28 or 38 taken | `room05_frame`, `msg_room5_opening` |
| 6 | 2 | 6, 0 (left) | 5 | room 6 cleared opens the passage at row 5, column 1 | `room06_frame`, `open_passage_ledge` |
| 7 | 3 | 6, 39 (right) | 8 | the 6 lanterns of row 5 taken open the passage at row 5, column 38 | `room07_frame` |
| 7 | 4 | 10, 39 (right) | 8 | none | map |
| 8 | 2 | 3, 0 (left) | 7 | none | map |
| 8 | 4 | 11, 0 (left) | 7 | the lantern of row 7, column 6 taken opens the passage at row 10, column 1 | `room08_frame` |
| 8 | 3 | 3, 39 (right) | 9 | room 8 cleared and two lanterns of row 10 in room 9 taken open the passage at row 2, column 38 | `room08_frame` |
| 8 | 5 | 11, 39 (right) | 9 | rooms 7 and 8 cleared open the passage at row 10, column 38 | `room08_frame` |
| 9 | 2 | 4, 0 (left) | 8 | none | map |
| 9 | 3 | 11, 0 (left) | 8 | none | map |
| 9 | 4 | 2, 36-37 (top) | 6 | room 9 cleared | `room09_frame`, `msg_room9_opening` |
| 10 | 2 | 11, 0 (left) | 3 | none | map |
| 10 | 3 | 5, 39 (right) | 11 | lanterns of row 4, column 1 and row 7, column 30 taken open the passage at row 4, column 38 | `room10_frame`, `open_passage_dark` |
| 11 | 2 | 11, 0 (left) | 10 | none | map |
| 11 | 3 | 7, 9-12 (door) | 12 | none | map |
| 11 | 4 | 7, 18-21 (door) | 14 | none | map |
| 11 | 5 | 7, 27-30 (door) | 16 | none | map |
| 12 | 4 | 11, 39 (right) | 14 | lantern of row 10, column 36 taken opens the passage at row 10, column 38 | `room12_frame` |
| 12 | 3 | 8, 39 (right) | 11 | room 12 cleared and two lanterns of row 10 in room 14 taken open the passage at row 7, column 38 | `room12_frame` |
| 13 | 2 | 11, 39 (right) | 15 | none | map |
| 14 | 4 | 11, 0 (left) | 12 | none | map |
| 14 | 5 | 11, 39 (right) | 16 | none | map |
| 14 | 3 | 5, 39 (right) | 11 | the two lanterns of row 7 taken open the passage at row 4, column 38 | `room14_frame` |
| 15 | 2 | 11, 0 (left) | 13 | none | map |
| 15 | 3 | 7-8, 39 (right) | 17 | room 15 cleared | `room15_frame`, `msg_room15_ladder_mid`, `msg_room15_ladder_top` |
| 16 | 4 | 11, 0 (left) | 14 | none | map |
| 16 | 3 | 8, 0 (left) | 11 | room 16 cleared opens the passage at row 7, column 1 | `room16_frame` |
| 17 | 2 | 10, 0 (left) | 15 | none | map |
| 17 | 3 | 3, 39 (right, top) | 18 | none | map |
| 18 | 2 | 11, 0 (left) | 17 | closed when Bruce takes the lantern of the wizard: character 6 replaces the marker | map, then `room18_frame`, `msg_wizard_left_marker` |
| 18 | 3 | 11, 39 (right) | 19 | the defeat sequence of the wizard is over | `room18_wizard_gone`, `msg_wizard_exit_top` |
| 11 | - | - | 13 | entering room 11 with rooms 12, 14 and 16 cleared | `draw_room` |
| 19 | - | - | 0 | the countdown of the room ends (next game loop) | `room19_frame` |

**Unused exits.** Six entries of the exit tables have no marker in any room map, and no room code draws their marker. They are marker 5 in room 3, markers 3, 4 and 5 in room 6, and markers 2 and 5 in room 7. The map decode and the room code show this. **Code** The screen of room 6 in a run showed only its marker 2. **Observed** So the game never uses these six entries. **Conclusion**

**The way back from the wizard closes.** Room 18 has two exits. Marker 2 at the left edge (cell row 11, column 0) goes to room 17. Marker 3 at the right edge goes to room 19. When Bruce takes the lantern of the wizard, [`room18_frame` `$3CDC`](../src/room/wizard_room.asm#L13) draws message `$61`, `msg_wizard_left_marker`, at row 11, column 0. Its cell code `$06` replaces marker 2, so the way back to room 17 closes.

The way forward opens only after the defeat sequence of `$50` passes. Then [`room18_wizard_gone` `$3D9B`](../src/room/wizard_room.asm#L115) draws `msg_wizard_exit_top`, with marker 3 at column 39, on every pass. **Code** (the runs did not reach this code). After the defeat of the wizard, Bruce can leave room 18 only to room 19. **Conclusion**

### The map of the rooms

The first part of the game is rooms 0 to 10. Labels give the side of the exit and the condition that opens it. "x2" means two exits between the same rooms.

~~~mermaid
flowchart LR
  R0["room 0"] -->|right x2| R1["room 1"]
  R1 -->|left x2| R0
  R1 -->|right| R2["room 2"]
  R2 -->|left| R1
  R1 -->|trapdoor: rooms 0-2 cleared, room 6 not| R5["room 5"]
  R2 -->|floor: room 6 cleared| R3["room 3"]
  R3 -->|left| R2
  R5 -->|top: room 6 cleared + lantern| R1
  R5 -->|right x2| R6["room 6"]
  R6 -->|left: room 6 cleared| R5
  R5 -->|left: lantern| R4["room 4"]
  R4 -->|right| R5
  R4 -->|floor| R7["room 7"]
  R7 -->|right x2| R8["room 8"]
  R8 -->|left x2| R7
  R8 -->|right x2: passages| R9["room 9"]
  R9 -->|left x2| R8
  R9 -->|top: room 9 cleared| R6
  R3 -->|trapdoor: room 3 cleared| R10["room 10"]
  R10 -->|left| R3
~~~

The second part is rooms 10 to 19, and the way back to room 0 for the next game loop.

~~~mermaid
flowchart LR
  R10["room 10"] -->|right: 2 lanterns| R11["room 11"]
  R11 -->|left| R10
  R11 -->|door| R12["room 12"]
  R11 -->|door| R14["room 14"]
  R11 -->|door| R16["room 16"]
  R12 -->|right| R11
  R12 -->|right| R14
  R14 -->|left| R12
  R14 -->|right| R11
  R14 -->|right| R16
  R16 -->|left| R14
  R16 -->|left: cleared| R11
  R11 -->|rooms 12, 14, 16 cleared| R13["room 13"]
  R13 -->|right| R15["room 15"]
  R15 -->|left| R13
  R15 -->|right: cleared| R17["room 17"]
  R17 -->|left| R15
  R17 -->|right| R18["room 18"]
  R18 -->|left, until the lantern| R17
  R18 -->|right: wizard defeated| R19["room 19"]
  R19 -->|next game loop| R0["room 0"]
~~~

**Conclusion.** The way through the game has these parts:

1. Rooms 0, 1 and 2, then down to room 5 and room 6.
2. Back through room 2 to room 3, when room 6 is clear.
3. From room 5 to rooms 4, 7, 8 and 9.
4. From room 3, when it is clear, down to rooms 10 and 11.
5. Room 11 is a hub with three doors to rooms 12, 14 and 16. When these three rooms are clear, room 11 sends Bruce to room 13, the falling room.
6. From room 13 to rooms 15 and 17, the wizard in room 18 and the congratulations in room 19.

**Conclusion.** The first time, Bruce can come to room 5 only through the trapdoor of room 1. The other ways into room 5 start in rooms 4 and 6, and Bruce can come to those rooms only through room 5. So room 6 is never clear before the trapdoor opens the first time. After Bruce clears room 6, the trapdoor stays closed on a later visit of room 1. Then the way from room 5 back to room 1 is the top opening of room 5.

### The rooms

A run took each image about 250 frames after Bruce entered the room.

| | | | |
|---|---|---|---|
| ![room 0](images/rooms/room00.png) room 0 | ![room 1](images/rooms/room01.png) room 1 | ![room 2](images/rooms/room02.png) room 2 | ![room 3](images/rooms/room03.png) room 3 |
| ![room 4](images/rooms/room04.png) room 4 | ![room 5](images/rooms/room05.png) room 5 | ![room 6](images/rooms/room06.png) room 6 | ![room 7](images/rooms/room07.png) room 7 |
| ![room 8](images/rooms/room08.png) room 8 | ![room 9](images/rooms/room09.png) room 9 | ![room 10](images/rooms/room10.png) room 10 | ![room 11](images/rooms/room11.png) room 11 |
| ![room 12](images/rooms/room12.png) room 12 | ![room 13](images/rooms/room13.png) room 13 | ![room 14](images/rooms/room14.png) room 14 | ![room 15](images/rooms/room15.png) room 15 |
| ![room 16](images/rooms/room16.png) room 16 | ![room 17](images/rooms/room17.png) room 17 | ![room 18](images/rooms/room18.png) room 18 | ![room 19](images/rooms/room19.png) room 19 |

## The state machine of the program

The whole program is one state machine, from the load to the next game loop. A state is a part of the code. A transition is a jump to the next part, or a fall-through into it. The demo and the game use the same part, the main loop, and `game_mode` tells them apart. **Conclusion**

The first diagram is the title and the demo. A game starts from the title.

~~~mermaid
stateDiagram-v2
  state "Cold start (cold_start)" as Cold
  state "Restart (restart_to_title)" as Restart
  state "Title (show_title_screen, title_menu_loop)" as Title
  state "Demo (start_attract_demo)" as Demo
  state "New game (start_new_game)" as NewGame
  [*] --> Cold
  Cold --> Restart
  Restart --> Title
  Title --> Demo: title_countdown = 0
  Demo --> Restart: fire port 1 or F1
  Demo --> Title: Bruce loses a fall
  Title --> NewGame: F7 or fire port 1
~~~

The second diagram is a game, from the PLAYER n screen to the game over or the next game loop.

~~~mermaid
stateDiagram-v2
  state "PLAYER n (show_player_screen)" as Player
  state "Room play (main_loop)" as Play
  state "Room change (change_room)" as Change
  state "Paused (toggle_pause)" as Paused
  state "Lost fall (lose_fall)" as Lose
  state "Next turn (next_turn)" as Turn
  state "Game over (game_over)" as Over
  state "Room 19 (room19_frame)" as Congrats
  [*] --> Player
  Player --> Play: room 0
  Play --> Change: exit marker at the edge
  Change --> Play
  Play --> Paused: SPACE, fire, idle
  Paused --> Play: SPACE or fire
  Play --> Lose: Bruce dies or is knocked out
  Lose --> Turn: falls left
  Lose --> Over: no falls left
  Turn --> Player
  Over --> Turn: other player has falls
  Over --> [*]: title after 318 frames
  Play --> Congrats: exit of room 18
  Congrats --> Play: countdown 0, room 0, next loop
  Play --> [*]: F1, restart
~~~

The table has more transitions than the diagrams. Examples are the restart of a room after a wall bump, the room 11 shortcut and the protection check of room 10. In room play and in the pause, F1 restarts the program through [`handle_game_keys` `$1B29`](../src/game/status_and_keys.asm#L57). The protection check of [`room10_frame_protection_check` `$3CA7`](../src/room/room_frames_8_11.asm#L289) is on [protection.md](protection.md), and the pause is on [interrupts.md](interrupts.md). **Code**

| State | Condition | Next state | Code |
|---|---|---|---|
| (load) | the loader jumps to the entry | Cold start | `cold_start` |
| Cold start | random table, fonts, charsets and contact masks built | Restart | `cold_start` falls into `restart_to_title` |
| Restart | always: stack reset, music stopped, `init_game_variables`, `reset_play_state` | Title | `restart_to_title` jumps to `show_title_screen` |
| Title | `title_countdown` = 0 (2400 frames without an option key) | Demo | `title_menu_loop` jumps to `start_attract_demo` |
| Title | F3, F5, L, R, shift-L, shift-R | Title (option changed, countdown restarted) | `title_menu_option_changed` |
| Title | F7, or fire on port 1 | New game | `title_menu_start_game`: fire released, 16 frames, RTS, then `show_title_screen` falls into `start_new_game` |
| Demo | always: options saved, one player and a computer Yamo, `game_mode` = 0, room 0 | Room play (demo) | `start_attract_demo` jumps to `main_loop` |
| Demo | fire on port 1 or F1 | Restart | `check_demo_abort`, `demo_abort_to_title` |
| Demo | Bruce loses a fall (`game_mode` = 0) | Title, with the title tune (`title_music_skip_count` = 0) | `lose_fall` jumps to `show_title_screen` |
| New game | always: `current_player` = 0, music stopped | PLAYER n | `start_new_game` calls `show_player_screen` |
| PLAYER n | 64 frames (128 with two players) | Room play, room 0 | `start_new_game`: `init_game_variables`, `reset_play_state`, `draw_room`, `main_loop` |
| Room play | Bruce touches an exit marker at the matching screen edge | Room change | `handle_touched_tile`, `take_exit2`..`take_exit5`, `check_exit_edge`, `enter_room` |
| Room change | always: enemies remember their energy and follow, stack reset, room drawn | Room play | `change_room`: `draw_room`, then `main_loop` |
| Room change | the new room is 11 and rooms 12, 14 and 16 are cleared | Room change to room 13 | `draw_room` calls `place_bruce_at_room_start` with X = 13 |
| Room play | Bruce bumps into a wall with no move history left | Room change to the same room, start position | `act_wall_bump_still_in` jumps to `enter_room` |
| Room play | SPACE, fire of the current player while paused, or 32768 frames without input | Paused | `toggle_pause`, `check_pause_fire`, `frame_update` |
| Room play | Bruce's dying state `$19` ends, or Bruce's energy is below 0 (knocked out) | Lost fall | `act_dying_lose_fall`, `check_actor_knockouts_bruce` |
| Lost fall | `falls_left` - 1 >= 0 | Next turn | `lose_fall_count` falls into `next_turn` |
| Lost fall | `falls_left` - 1 < 0 | Game over | `lose_fall_count`: BMI `game_over` |
| Next turn | always: energy `$24` for all actors. With two players and the other player not out, `current_player` changes | PLAYER n, then room play in the room of the (new) player | `next_turn`, `show_player_screen`, `next_turn_enter_room`: `reset_play_state`, `place_bruce_at_room_start` |
| Game over | after 254 frames, two players and the other player has falls (`inactive_player_state` >= 0) | Next turn | `game_over_wait` jumps to `next_turn` |
| Game over | 254 + 64 frames, no other player | Title | `game_over_to_title` jumps to `show_title_screen` |
| Room play (room 18) | the wizard defeat sequence is over and Bruce takes the right exit (marker 3) | Room change to room 19 | `room18_wizard_gone` draws the exit, then `take_exit3` |
| Room 19 | `title_countdown` = 0 (1112 frames after `room19_init`) | Room play, room 0, next game loop | `room19_frame`: `game_loop_count` + 1, `reset_lantern_counts`, `reset_all_lanterns`, `reset_unvisited_rooms`, `place_bruce_at_room_start` with X = 0 |
| Room play, paused | F1 | Restart | `handle_game_keys` jumps to `restart_to_title` |
| Room play (room 10) | protection: `D6510` is not `$EF` | Title, with the maps of rooms 0, 1 and 5 damaged | `room10_frame_protection_check` |

## The worked example: the right exit of room 0

Room 0 has its marker 2 at cell row 8, column 39, at the right edge of the floor. This is the way that Bruce takes when he walks right from the start of a game. **Code**

1. Bruce walks right. When the characters beside him include the marker, `handle_touched_tile` jumps to [`take_exit2` `$2F3C`](../src/actor/background_touch.asm#L178).
2. `check_exit_edge` finds that room 0 is not room 11, that `actor_x` is above `$A1` and that Bruce moves right. It returns with carry clear: he may leave.
3. With X = `room` = 0, the handler reads the first byte of each table of set 2 (below).
4. The entry X is not 0, so `enter_room` runs. Bruce is actor 0, so it goes to `change_room`: `actor_x` = `$10`, `actor_y` = `$92`, `room` = 1. In sprite units that is X = 2 * `$10` = `$20` and Y = `$92` + `$1D` = `$AF`, at the left edge of room 1.

The bytes come from [`exit2_dest_room` `$4B5E`](../src/room/room_tables.asm#L78), [`exit2_entry_x` `$4BFE`](../src/room/room_tables.asm#L121) and [`exit2_entry_y` `$4C12`](../src/room/room_tables.asm#L126), each at offset 0 for room 0. The way back is the marker 2 of room 1, at cell row 8, column 0, at offset 1 of the same tables.

| Address | Table | Byte | Meaning |
|---|---|---|---|
| `$4B5E` | `exit2_dest_room` + 0 | `$01` | room 0 leads to room 1 |
| `$4C12` | `exit2_entry_y` + 0 | `$92` | Bruce enters at Y = `$92` |
| `$4BFE` | `exit2_entry_x` + 0 | `$10` | Bruce enters at X = `$10`. Not 0, so the exit exists |
| `$4B5F` | `exit2_dest_room` + 1 | `$00` | room 1 leads back to room 0 |
| `$4C13` | `exit2_entry_y` + 1 | `$92` | at the same height, Y = `$92` |
| `$4BFF` | `exit2_entry_x` + 1 | `$A0` | at the right edge of room 0, X = `$A0` |

The entry positions are just inside the edge limits of `check_exit_edge`. X = `$10` is not below the left limit `$10`, and X = `$A0` is not above the right limit `$A1`. So Bruce does not leave the new room again at once. He must walk farther outward to go back. **Conclusion**

## Still open

- How does Bruce reach the marker 3 of room 17 at cell row 3, column 39 (top right)? Are the tiles of [`room17_frame` `$3F71`](../src/room/room_frames_12_17.asm#L188) (row 10, columns 24 and 37) part of that way? A playthrough run of room 17 with the lanterns taken can answer it.
- Room 18 has the characters 4 and 5 in the picture of the wizard (cell rows 2-9). Its marker 4 and 5 entries are 0, so [`take_exit5` `$2F7B`](../src/actor/background_touch.asm#L210) would enter room 0 at X = 0, Y = 0. [`check_exit_edge` `$30D4`](../src/actor/touch_effects.asm#L154) probably never allows it there. A run with Bruce at the top edge of room 18 can check it.
