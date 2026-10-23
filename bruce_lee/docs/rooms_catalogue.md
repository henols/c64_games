# Bruce Lee: the room catalogue

The game has 20 rooms. Rooms 0-3 are the garden, rooms 4-9 are the caves and rooms 10-17 are the castle. Room 18 is the wizard, and room 19 is the congratulations room. Each room has a map and two handlers. The init handler sets up the room one time when Bruce enters. The frame handler runs on each pass and changes the room: lanterns open passages, trapdoors open, hazards move and the wizard fights.

This page gives each room one section of the same form. The section tells what the room does in the game and shows its screenshot. Then it gives the entries of the room in the per-room tables, the setup, the behaviour and the exits. The page ends with the conditions by which one room changes another room.

The handlers come from the RTS tables [`room_init_handlers` `$4E9C`](../src/room/room_dispatch.asm#L19) and [`room_frame_handlers` `$4EC4`](../src/room/room_dispatch.asm#L28). The page [rooms.md](rooms.md) explains what all rooms share: the tables, the map format, `draw_room`, the lanterns, the passages and the hazards.

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of `main_loop` (3 frames). An *even pass* has `pass_parity` = 0.
- "L7 C31" is the cell at text line 7, column 31. Text line L uses screen rows 2L-1 and 2L. The map fills lines 2-12.
- A *tile* is a message of [`print_message` `$17E2`](../src/actor/actor_driver_text.asm#L59). "Tile $13" is message $13. A *code* is the character code of the upper row of a cell.
- An *exit marker N* is a cell with code N (2-5). It uses the exit tables of set N ([exits](rooms.md#exits)). An example is "marker 3 at L12 C19-21 to room 5 at ($2C, $32)". The destination is room 5, Bruce's entry X is $2C and his entry Y is $32.
- A room is *cleared* when its [`room_lanterns_left` `$002A`](../src/constants.asm#L29) + room is 0. "Lantern L4 C11" is the lantern record with that position. The first byte of the record is its state: 1 = present, 0 = taken.
- The *room state bytes* `room_state_a` to `room_state_e` (`$4E97-$4E9B`) are five scratch bytes. Each room uses them for its own timers, counters and flags. `room_init_clear_vars` sets them to 0 at each room entry, before the init handler runs.
- A *one-shot event* is an action that a frame handler does one time per visit. A room state byte is its flag ([the one-shot events](rooms.md#the-one-shot-events)). `draw_room` draws the map again at each visit. So the handler draws the change again at each visit while its condition is true.
- **Observed** marks a fact that a run showed (the screenshots, the coverage runs, the runs of the analysis). **Code** marks a fact from the code only. **Conclusion** marks an interpretation.
- We took each screenshot about 250 frames after Bruce entered the room.

## Room 0: the garden with the ox statue

Room 0 is the start room. Bruce starts here at a game start and after each completed game loop. **Observed.** The room opens nothing. It changes only when room 6 is cleared: then the mouth of the statue moves. **Code.**

![Room 0](images/rooms/room00.png)

The screenshot shows snow mountains and an ox statue on a pedestal at the left. A blue lattice is in the middle and a pagoda is at the right. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_00`, 272 bytes, 440 cells |
| Colours | fill $FE, charset $38 (`charset_rooms_0_9`), `room_palette_r0_3`, splits $78, $97 |
| Start A / B | $1A, $C4 / $9F, $62 |
| Enemies | Ninja $68 / $A0 (side $02), Yamo $F0 / $EE (side $80) |
| Lanterns | 6, `lantern_list_room0` |
| Handlers | `room_init_none`, `room00_frame` |

**The setup.** None (`room_init_none`).

**The behaviour.** [`room00_frame` `$3642`](../src/room/room_frames_0_7.asm#L9) waits until room 6 is cleared. Then it moves the mouth of the statue at L9 C7 on even passes. It shows tile $1D with sound $81 for one step, then tile $1E for 6 steps. `room_state_a` is the timer. `room_state_b` tells which tile is on the screen. **Code**. This code never ran in the coverage.

~~~mermaid
stateDiagram-v2
  state "Still (room 6 has lanterns)" as Still
  state "Mouth A: tile $1D" as A
  state "Mouth B: tile $1E" as B
  [*] --> Still
  Still --> A: room 6 cleared, even pass
  A --> B: next even pass
  B --> A: 6 even passes later, sound $81
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Still | `room_lanterns_left+6` <> 0 | Still | `room00_frame` |
| Still / Mouth B | even pass, `room_state_a` goes below 0, `room_state_b` = 0 | Mouth A: sound $81, tile $1D at L9 C7, `room_state_b` = 1 | `room00_frame` |
| Mouth A | next even pass, `room_state_b` = 1 | Mouth B: tile $1E, `room_state_b` = 0, `room_state_a` = 5 | `room00_frame_mouth_b` |

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L8 C39 | room 1 at ($10, $92) | - |
| 5 | L5 C39 | room 1 at ($0F, $62) | - |

Bruce enters from room 1 (markers 2 and 4). He also enters from room 19, where [`place_bruce_at_room_start` `$3217`](../src/room/room_misc_support.asm#L11) with X = 0 starts the next game loop.

## Room 1: the pagodas and the first trapdoor

Room 1 is the way down from the garden. Bruce must clear the three garden rooms 0, 1 and 2. Then a trapdoor opens in the floor of room 1 and drops Bruce into room 5, the first cave. **Code.**

![Room 1](images/rooms/room01.png)

The screenshot shows two pagoda buildings at the left and the right, and a blue lattice in the middle. The trapdoor is in the floor below the lattice. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_01`, 309 bytes |
| Colours | fill $FE, charset $38, `room_palette_r0_3`, splits $78, $97 |
| Start A / B | $18, $62 / $95, $92 |
| Enemies | Ninja $78 / $A0 (side $02), Yamo $EE / $EE (side $80) |
| Lanterns | 6, `lantern_list_room1` |
| Handlers | `room01_init`, `room01_frame` |

**The setup.** [`room01_init` `$33F6`](../src/room/room_specific_init.asm#L9) sets `room_state_a` = 3. This byte counts the steps of the trapdoor.

**The behaviour.** [`room01_frame` `$3679`](../src/room/room_frames_0_7.asm#L42) opens the trapdoor at L12 C17-21 in 4 steps. It does a step on an even pass when these conditions are true:

- Rooms 0, 1 and 2 are cleared.
- Room 6 still has lanterns.

At each step the handler decrements `room_state_a` and draws tile $10 + `room_state_a`. So it draws tiles $12, $11, $10 and $0F. [`play_open_sound` `$424F`](../src/room/wizard_fireballs.asm#L183) plays at the first step. The open trapdoor (tile $0F, codes $22 $22 $03 $03 $03) holds exit marker 3 at C19-21. **Code**. This code never ran in the coverage.

~~~mermaid
stateDiagram-v2
  state "Closed (3)" as S3
  state "Step 1: tile $12 (2)" as S2
  state "Step 2: tile $11 (1)" as S1
  state "Step 3: tile $10 (0)" as S0
  state "Open: tile $0F ($FF)" as Open
  [*] --> S3: room01_init
  S3 --> S2: even pass and condition, sound $8A
  S2 --> S1: even pass and condition
  S1 --> S0: even pass and condition
  S0 --> Open: even pass and condition
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| any step 0-3 | odd pass | same | `room01_frame` |
| any step 0-3 | `room_lanterns_left+6` = 0 (room 6 cleared) | same: the trapdoor stays as it is | `room01_frame` |
| step N | rooms 0, 1, 2 cleared, room 6 not cleared, even pass | `room_state_a` - 1, tile $10 + `room_state_a` at L12 C17 | `room01_frame_draw_trapdoor` |
| Open ($FF) | - | Open | the `bmi` test |

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L8 C0 | room 0 at ($A0, $92) | - |
| 3 | L12 C19-21 (trapdoor) | room 5 at ($2C, $32) | rooms 0, 1, 2 cleared and room 6 not cleared |
| 4 | L5 C0 | room 0 at ($A1, $62) | - |
| 5 | L5 C39 | room 2 at ($10, $62) | - |

Bruce enters from rooms 0 and 2, and from room 5 (marker 5 at ($58, $66)). **Conclusion:** the trapdoor is the first way down. After room 6 is cleared, the trapdoor stays closed at a new visit to room 1. Then the way back to room 5 is the top opening of room 5.

## Room 2: the second statue

Room 2 is the end of the garden. Its right wall opens to room 3 only after room 6 is cleared. Then its statue's mouth also moves, as in room 0. The frame handler also has a copy protection check. **Code.**

![Room 2](images/rooms/room02.png)

The screenshot shows pagoda roofs with a ladder at the left, a blue lattice in the middle and a second ox statue at the right. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_02`, 351 bytes |
| Colours | fill $FE, charset $38, `room_palette_r0_3`, splits $78, $97 |
| Start A / B | $30, $C4 / $96, $C4 |
| Enemies | Ninja $78 / $A0 (side 0), Yamo $EE / $EE (side 0) |
| Lanterns | 10, `lantern_list_room2` |
| Handlers | `room_init_none`, `room02_frame` |

**The setup.** None (`room_init_none`).

**The behaviour.** [`room02_frame` `$36A6`](../src/room/room_frames_0_7.asm#L75) does three things on each pass:

1. **The copy protection check.** The handler loops forever if [`D6510` `$0000`](../src/constants.asm#L7) does not hold $EF. The original loader leaves this value there. The check passed in all runs of the coverage. **Observed.** It is check 6 of [protection.md](protection.md). The default build (`PROTECTION` = 0) replaces it with code that always passes. **Code.**
2. **The right wall opens.** When room 6 is cleared, the handler opens the wall one time (`room_state_b`). It calls `play_open_sound`, then draws tile $1A (codes $00 $00 $05) at L11 C37 and tile $07 (codes $11 $11 $11) at L12 C37. Exit marker 5 then shows at L11 C39. **Code.**
3. **The statue's mouth moves.** When room 6 is cleared, the mouth at L9 C33 moves as the mouth of room 0 does. `room_state_c` is the timer, and `room_state_a` tells which tile is on the screen. **Code.**

Steps 2 and 3 never ran in the coverage.

~~~mermaid
stateDiagram-v2
  state "Closed (room 6 has lanterns)" as Closed
  state "Opened: tiles $1A, $07" as Opened
  state "Mouth A: tile $1D" as A
  state "Mouth B: tile $1E" as B
  [*] --> Closed
  Closed --> Opened: room 6 cleared
  Opened --> A: even pass
  A --> B: next even pass
  B --> A: 6 even passes later, sound $81
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Closed | `room_lanterns_left+6` = 0, `room_state_b` = 0 | Opened: sound $8A, tiles $1A and $07 | `room02_frame` |
| Opened / Mouth B | even pass, `room_state_c` goes below 0, `room_state_a` = 0 | Mouth A: sound $81, tile $1D at L9 C33 | `room02_frame_mouth` |
| Mouth A | next even pass | Mouth B: tile $1E, `room_state_c` = 5 | `room02_frame_mouth_b` |

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 4 | L5 C0 | room 1 at ($A1, $62) | - |
| 5 | L11 C39 (tile $1A) | room 3 at ($10, $C4) | room 6 cleared |

Bruce enters from room 1 (marker 5) and room 3 (marker 4).

## Room 3: the towers and the moving ledges

Room 3 is the way from the garden down to the castle. Its trapdoor opens when Bruce takes the two lanterns of the room. The trapdoor drops Bruce into room 10. Two ledges change places all the time. The room has no enemies. **Code.**

![Room 3](images/rooms/room03.png)

The screenshot shows white towers with blue vines, a lattice in the middle and spikes in the floor. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_03`, 382 bytes |
| Colours | fill $FE, charset $38, `room_palette_r0_3`, splits $62, $97 |
| Start A / B | $20, $C0 / $38, $C4 |
| Enemies | none (`room_no_enemies` = $FF) |
| Lanterns | 2, `lantern_list_room3`: L10 C29, L10 C38 |
| Handlers | `room03_init`, `room03_frame` |

**The setup.** [`room03_init` `$33FC`](../src/room/room_specific_init.asm#L14) sets `room_state_a` = 3. This byte counts the steps of the trapdoor.

**The behaviour.** [`room03_frame` `$3702`](../src/room/room_frames_0_7.asm#L136) runs two machines:

1. **The trapdoor** at L12 C29-33. When room 3 is cleared ([`room_lanterns_left+3` `$002D`](../src/constants.asm#L29) = 0), the trapdoor opens in 4 steps on even passes. The steps are the same as in room 1: tiles $12, $11, $10 and $0F, with sound $8A at the first step. The open trapdoor holds marker 3 at C31-33. **Code**. This code never ran in the coverage.
2. **The ledges** of line 6. `room_state_c` counts 33 passes. Then `room_state_b` toggles, and two tiles change places between C9-15 and C21-27. Tile $06 has 7 cells of code $4B, and tile $60 has 7 cells of code $09. **Observed** (coverage).

The trapdoor machine is the machine of room 1 with the condition "room 3 cleared". The ledges have this machine:

~~~mermaid
stateDiagram-v2
  state "Phase 1: $60 at C9, $06 at C21" as P1
  state "Phase 0: $06 at C9, $60 at C21" as P0
  [*] --> P1: first pass (room_state_c 0 -> $FF)
  P1 --> P0: 33 passes
  P0 --> P1: 33 passes
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Phase 0 (`room_state_b` = 0) | `room_state_c` goes below 0 | Phase 1: `room_state_b` = 1, tile $60 at L6 C9, tile $06 at L6 C21, `room_state_c` = $20 | `room03_frame_ledges_phase_b` |
| Phase 1 (`room_state_b` = 1) | `room_state_c` goes below 0 | Phase 0: `room_state_b` = 0, tile $06 at L6 C9, tile $60 at L6 C21, `room_state_c` = $20 | `room03_frame_swap_ledges` |
| either | `room_state_c` >= 0 after the decrement | same | `room03_frame_ledges_wait` |

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L12 C31-33 (trapdoor) | room 10 at ($10, $B0) | room 3 cleared |
| 4 | L11 C0 | room 2 at ($A1, $C5) | - |
| 5 | none | (room 0 at ($10, $62)) | no marker: not used |

Bruce enters from room 2 (marker 5, after room 6 is cleared) and from room 10 (marker 2).

## Room 4: the dark cave with the blinking lanterns

Room 4 is a dark cave with two blinking lanterns. Bruce can take a lantern only while it is lit. When Bruce takes a lantern, the handler erases the cells below it and stops a slider. The way to room 7 is at the bottom left. **Code.**

![Room 4](images/rooms/room04.png)

The screenshot shows a dark blue cave with a moving purple column in the middle and two lattice windows. The two lanterns at the top blink. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_04`, 359 bytes, 442 cells |
| Colours | fill $FC, charset $38, `room_palette_r4_6`, no split |
| Start A / B | $94, $B4 / $96, $B4 |
| Enemies | Ninja $70 / $70 (side $80), Yamo $C0 / $EE (side $80) |
| Lanterns | 2, `lantern_list_room4`: L4 C11 (lantern 1), L4 C28 (lantern 2, `lantern_list_room4+4`) |
| Handlers | `room04_init`, `room04_frame` |

The map decodes to two cells more than the play area holds. This is [the map overflow](rooms.md#map-sizes-and-the-overflow).

**The setup.** [`room04_init` `$3402`](../src/room/room_specific_init.asm#L22) sets `room_state_d` = $1F. So lantern 2 blinks half a period after lantern 1. The handler puts slider 0 at L11 C1, slider 1 at L7 C11 and slider 2 at L7 C26. It sets [`slider_timer` `$0077`](../src/constants.asm#L70) = $FF, $FF and $F4.

**The behaviour.** [`room04_frame` `$3760`](../src/room/room_frames_0_7.asm#L195) runs on each pass. **Observed** (coverage), but not the steps after Bruce takes a lantern.

1. **Lantern 1 blinks** while it is present. `room_state_c` increments. At 32 the handler draws tile $34 (lit, code $13, Bruce can take it) at L4 C11. At 64 it draws tile $36 (dark, code $66, Bruce cannot take it), and the counter starts again at 0.
2. **Lantern 1 taken.** One time (`room_state_a`), the handler plays sound $8A. It draws tile $16 (4 blanks) at L8 C11 and L9 C11, and it erases slider 1 (frame 6).
3. **Lantern 2 blinks** in the same way, with `room_state_d` and tiles $35 / $37 at L4 C28.
4. **Lantern 2 taken.** One time (`room_state_b`), the handler sets `anim_chars_direction` = 0 and [`anim_chars_speed_step` `$4321`](../src/game/options_and_patterns.asm#L53) = 7. So the moving column starts again. Then it plays sound $8A, draws tile $16 at L8 C25 and L9 C25, and erases slider 2.
5. **The sliders** run: slider 0 (look B), slider 1 while lantern 1 is present, and slider 2 while lantern 2 is present. See [sliders](rooms.md#sliders).
6. [`animate_scrolling_chars` `$2C70`](../src/room/animated_chars.asm#L12) moves the purple column.

~~~mermaid
stateDiagram-v2
  state "Map look" as Map
  state "Lit: tile $34" as Lit
  state "Dark: tile $36" as Dark
  state "Taken" as Taken
  state "Opened: barrier removed" as Opened
  [*] --> Map
  Map --> Lit: counter = 32
  Lit --> Dark: counter = 64, counter = 0
  Dark --> Lit: counter = 32
  Lit --> Taken: Bruce takes the lantern
  Taken --> Opened: same pass, one time
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Map look / Dark | `lantern_list_room4` = 1, `room_state_c` reaches $20 | Lit: tile $34 at L4 C11 | `room04_frame` |
| Lit | `room_state_c` reaches $40 | Dark: tile $36, `room_state_c` = 0 | `room04_frame_lantern1_check_dark` |
| Lit | Bruce touches code $13 (`check_lantern_pickup`) | Taken: record state 0 | `collect_lantern` |
| Taken | `room_state_a` = 0 | Opened: sound $8A, tile $16 at L8 C11 and L9 C11, slider 1 erased | `room04_frame_lantern1_taken` |

The same table applies to lantern 2, with `room_state_d`, tiles $35 / $37, `room_state_b`, column 25 and slider 2.

**Why Bruce cannot take a dark lantern.** The dark tiles have codes $66 / $67. These codes are not lantern codes. **Code.**

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L4 C39 | room 5 at ($10, $C2) | - |
| 3 | L12 C1-4 | room 7 at ($1F, $32) | - |

Bruce enters from room 5 (marker 2).

## Room 5: the blue cave

Room 5 is the centre of the caves. Bruce comes here through the trapdoor of room 1. The lanterns of room 5 open the way to room 4 at the left and the passages at the right. After room 6 is cleared, they can also open a way up to room 1. **Code.**

![Room 5](images/rooms/room05.png)

The screenshot shows a blue cave with lattice towers in the middle and a moving purple column at the right. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_05`, 347 bytes |
| Colours | fill $FC, charset $38, `room_palette_r4_6`, no split |
| Start A / B | $22, $51 / $28, $C2 |
| Enemies | Ninja $18 / $0C (side $80), Yamo $C0 / $60 (side $02) |
| Lanterns | 10, `lantern_list_room5` |
| Handlers | `room05_init`, `room05_frame` |

**The setup.** [`room05_init` `$3428`](../src/room/room_specific_init.asm#L48) does three things:

1. **The copy protection check.** The handler loops forever if [`prot_loader_mark` `$0002`](../src/constants.asm#L9) does not hold $32. The original loader leaves this value there. The check passed in the coverage. **Observed.** It is check 7 of [protection.md](protection.md). The default build (`PROTECTION` = 0) replaces it. **Code.**
2. It sets colour RAM $FC (colour 12) for L2 C34-36. Tile $19 shows there later.
3. It puts slider 0 at L9 C27, slider 1 at L10 C27 and slider 2 at L5 C1. It sets `slider_timer` = $FF, $FC and $F8.

**The behaviour.** [`room05_frame` `$38AB`](../src/room/room_frames_0_7.asm#L378) runs three one-shot events. Then it runs the sliders and `animate_scrolling_chars`. **Code**. The event of lantern L10 C2 ran in the coverage. **Observed.**

| Event | Flag | Condition | Action |
|---|---|---|---|
| Right passages | `room_state_c` | lantern L10 C26 (`lantern_list_room5+$20`) taken | `open_passage` at L10 C25 and L10 C26, slider 1 erased |
| Left exit | `room_state_d` | lantern L10 C2 (`lantern_list_room5+$18`) taken | `open_passage` at L10 C0, tile $15 (code $02, marker 2) at L11 C0 |
| Top exit | `room_state_e` | room 6 cleared and lantern L3 C28 (`lantern_list_room5+8`) or L3 C38 (`lantern_list_room5+$10`) taken | tile $19 (codes $61 $05 $63) at L2 C34, `open_passage` at L3 C30 and L6 C32 |

The sliders are these:

- Slider 0 at L9 C27-28.
- Slider 1 at L10 C27-28, while lantern L10 C26 is present.
- Slider 2 at L5 C1-2, with look B.

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 (tile $15) | room 4 at ($9C, $51) | lantern L10 C2 taken |
| 3 | L4 C39 | room 6 at ($10, $40) | - |
| 4 | L7 C39 | room 6 at ($10, $74) | - |
| 5 | L2 C35 (tile $19) | room 1 at ($58, $66) | room 6 cleared, lantern L3 C28 or L3 C38 taken |

Bruce enters from room 1 (trapdoor), room 4 (marker 2) and room 6 (marker 2). The openings at L3 C30 and L6 C32 can block the way to markers 3 and 4 before room 6 is cleared. This question is open ([still open](rooms.md#still-open)).

## Room 6: the temple

Room 6 is the key of the first part of the game. When Bruce clears it, four other rooms change:

- The statues of rooms 0 and 2 move.
- The right wall of room 2 opens to room 3.
- The trapdoor of room 1 stays closed.
- The top exit of room 5 can open.

In room 6, the handler opens a passage to room 5. **Code.**

![Room 6](images/rooms/room06.png)

The screenshot shows a blue room with a big temple building, a striped wall at the left and a moving purple column at the right. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_06`, 330 bytes |
| Colours | fill $FC, charset $38, `room_palette_r4_6`, no split |
| Start A / B | $86, $B3 / $81, $72 |
| Enemies | Ninja $30 / $30 (side $02), Yamo $A0 / $EE (side 0) |
| Lanterns | 8, `lantern_list_room6` |
| Handlers | `room_init_none`, `room06_frame` |

**The setup.** None (`room_init_none`).

**The behaviour.** When room 6 is cleared, [`room06_frame` `$39AA`](../src/room/room_frames_0_7.asm#L519) opens a passage at L5 C1 one time. It uses `room_state_a` as the flag and [`open_passage_ledge` `$3AA0`](../src/room/passage_open.asm#L54) to draw. Then it runs [`update_burst_traps` `$3228`](../src/room/room_misc_support.asm#L33) and `animate_scrolling_chars`. **Code.**

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L6 C0 | room 5 at ($A0, $80) | **Conclusion:** behind the wall that the passage at L5 C1 opens when room 6 is cleared |
| 3, 4, 5 | none | (rooms 5, 2, 0) | no marker: not used |

Bruce enters from room 9 (marker 4 at ($9D, $C7)) and room 5 (markers 3 and 4).

## Room 7: the orange cave with the lantern rows

Room 7 is the cave below room 4. Its two rows of lanterns open the passages to room 8. A runner moves along the floor. The runner moves in the opposite direction when Bruce takes the two lanterns of line 9. **Code.**

![Room 7](images/rooms/room07.png)

The screenshot shows an orange cave with two levels of buildings and a long floor at the bottom. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_07`, 234 bytes, 442 cells |
| Colours | fill $FF, charset $38, `room_palette_r7_9`, no split |
| Start A / B | $1C, $44 / $1F, $74 |
| Enemies | Ninja $50 / $18 (side $02), Yamo $B0 / $C0 (side $80) |
| Lanterns | 13, `lantern_list_room7`: 5 on line 2, 6 on line 5, 2 on line 9 |
| Handlers | `room07_init`, `room07_frame` |

The map decodes to two cells more than the play area holds. This is [the map overflow](rooms.md#map-sizes-and-the-overflow).

**The setup.** [`room07_init` `$3461`](../src/room/room_specific_init.asm#L93) puts the runner at L11 C5 (`runner_col` = `runner_old_col` = 5, `runner_row` = 11). It puts slider 0 at L4 C34 with `slider_timer` = $FF.

**The behaviour.** [`room07_frame` `$39C3`](../src/room/room_frames_0_7.asm#L542) runs on each pass. **Observed** (coverage), but not the second passage and not the runner to the left.

1. `update_burst_traps` moves the burst traps.
2. When Bruce has the 5 lanterns of line 2, one time (`room_state_a`): [`open_passage_ledge` `$3AA0`](../src/room/passage_open.asm#L54) at L2 C33. The handler then stops for this pass.
3. When Bruce has the 6 lanterns of line 5, one time (`room_state_b`): `open_passage_ledge` at L5 C38. The handler then stops for this pass.
4. Slider 0 runs at L4 C34-36 (look B).
5. The runner of line 11 moves right (C5-35) while lantern L9 C2 (`lantern_list_room7+$2C`) or L9 C3 (`lantern_list_room7+$30`) is present. When Bruce has both, [`room07_frame_runner_left` `$3A51`](../src/room/room_frames_0_7.asm#L614) moves it left (C36-5).

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L6 C39 | room 8 at ($0F, $46) | **Conclusion:** reached through the passage at L5 C38 |
| 4 | L10 C39 | room 8 at ($10, $C0) | - |
| 2, 5 | none | (room 0) | no marker: not used |

Bruce enters from room 4 (marker 3) and room 8 (markers 2 and 4).

## Room 8: the twin columns

Room 8 is the cave between rooms 7 and 9. It has no enemies. Five one-shot events open its passages, and three of these events test the lanterns of rooms 7 and 9. **Code.**

![Room 8](images/rooms/room08.png)

The screenshot shows an orange cave with two moving purple columns. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_08`, 384 bytes |
| Colours | fill $FA, charset $38, `room_palette_r7_9`, no split |
| Start A / B | $14, $46 / 0, 0 |
| Enemies | none |
| Lanterns | 4, `lantern_list_room8`: L3 C15, L3 C24, L7 C6 (+8), L7 C33 (+12) |
| Handlers | `room08_init`, `room08_frame` |

**The setup.** [`room08_init` `$3478`](../src/room/room_specific_init.asm#L107) puts slider 0 at L5 C6 (timer $FF) and slider 1 at L5 C27 (timer $F2).

**The behaviour.** [`room08_frame` `$3AD4`](../src/room/room_frames_8_11.asm#L16) runs five one-shot events. Then it runs slider 0 (L5 C6-11), slider 1 (L5 C27-32) and `animate_scrolling_chars`. **Code**. The events never ran in the coverage.

| Event | Flag | Condition | Action |
|---|---|---|---|
| 1 | `room_state_c` | room 7 cleared and lantern L7 C6 (`lantern_list_room8+8`) taken | `open_passage` at L7 C14 |
| 2 | `room_state_d` | lanterns L3 C15 and L3 C24 taken | if lantern L7 C33 (`lantern_list_room8+$C`) is present, `anim_chars_direction` = 1 and speed curve restart. Then `open_passage` at L7 C25 |
| 3 | `room_state_e` | room 8 cleared and room 9 lanterns L10 C27 (`lantern_list_room9+8`) and L10 C28 (`lantern_list_room9+$C`) taken | `open_passage_ledge_b` at L2 C38 |
| 4 | `room_state_a` | lantern L7 C6 taken | `open_passage` at L10 C1 |
| 5 | `room_state_b` | rooms 7 and 8 cleared | `open_passage` at L10 C38 |

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L3 C0 | room 7 at ($A0, $74) | - |
| 3 | L3 C39 | room 9 at ($10, $53) | **Conclusion:** reached through the passage at L2 C38 (event 3) |
| 4 | L11 C0 | room 7 at ($A1, $B5) | **Conclusion:** reached through the passage at L10 C1 (event 4) |
| 5 | L11 C39 | room 9 at ($0F, $C6) | **Conclusion:** reached through the passage at L10 C38 (event 5) |

Bruce enters from room 7 (markers 3 and 4) and room 9 (markers 2 and 3).

## Room 9: the slopes

Room 9 is the last cave. When Bruce clears it, an opening at the top leads to room 6, the temple. The lanterns of room 9 also change the direction of the moving column and the runner. The room has no enemies. **Code.**

![Room 9](images/rooms/room09.png)

The screenshot shows an orange cave with purple slopes and a moving column at the right. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_09`, 327 bytes |
| Colours | fill $FA, charset $38, `room_palette_r7_9`, no split |
| Start A / B | $12, $C6 / 0, 0 |
| Enemies | none |
| Lanterns | 5, `lantern_list_room9`: L2 C32, L7 C15 (+4), L10 C27 (+8), L10 C28 (+12), L10 C32 |
| Handlers | `room09_init`, `room09_frame` |

**The setup.** [`room09_init` `$348F`](../src/room/room_specific_init.asm#L123) sets colour RAM $FA (colour 10) for L2 C35-38. Tile $18 shows there later. The handler puts the runner at L12 C4. It puts slider 0 at L5 C16 (timer $FC) and slider 1 at L6 C16 (timer $FF).

**The behaviour.** [`room09_frame` `$3BB2`](../src/room/room_frames_8_11.asm#L149) runs three one-shot events. **Code**. The events never ran in the coverage. The runner to the right and the sliders ran. **Observed.**

| Event | Flag | Condition | Action |
|---|---|---|---|
| 1 | `room_state_c` | lantern L2 C32 (`lantern_list_room9`) taken | `anim_chars_direction` = 1, speed curve restart |
| 2 | `room_state_a` | lantern L7 C15 (`lantern_list_room9+4`) taken | `open_passage` at L7 C23. Then direction 0, restart |
| 3 | `room_state_b` | room 9 cleared | direction 0, restart, sound $8A, tile $18 (codes $61 $04 $04 $63) at L2 C35 |

After the events, the handler runs these parts:

1. The runner of line 12 moves right (C4-24) while lantern L10 C27 or L10 C28 is present. Else it moves left.
2. Slider 0 (L5 C16-20) and slider 1 (L6 C16-20) run, both with look B.
3. `animate_scrolling_chars` moves the column.

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L4 C0 | room 8 at ($A0, $47) | - |
| 3 | L11 C0 | room 8 at ($A0, $C0) | - |
| 4 | L2 C36-37 (tile $18) | room 6 at ($9D, $C7) | room 9 cleared |

Bruce enters from room 8 (markers 3 and 5).

## Room 10: the castle hall

Room 10 is the first room of the castle, below the trapdoor of room 3. Two of its lanterns open the passage to room 11. Its frame handler also has a copy protection check. When the check fails, it damages three room maps. **Code.**

![Room 10](images/rooms/room10.png)

The screenshot shows a grey castle hall with three floors, with Yamo (green) and the Ninja (black). **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_10`, 372 bytes, 442 cells |
| Colours | fill $F9, charset $3A (`charset_rooms_10_19`), `room_palette_r10_12_14_16`, split $56 |
| Start A / B | $34, $8C / $96, $5C |
| Enemies | Ninja $08 / $0C (side $02), Yamo $30 / $30 (side $80) |
| Lanterns | 3, `lantern_list_room10`: L4 C1, L7 C30 (+4), L10 C30 |
| Handlers | `room_init_none`, `room10_frame` |

The map decodes to two cells more than the play area holds. This is [the map overflow](rooms.md#map-sizes-and-the-overflow).

**The setup.** None (`room_init_none`).

**The behaviour.** [`room10_frame` `$3C90`](../src/room/room_frames_8_11.asm#L278) does three things on each pass:

1. When Bruce has lanterns L4 C1 and L7 C30, one time (`room_state_a`): [`open_passage_dark` `$3AB4`](../src/room/passage_open.asm#L69) at L4 C38. **Code.**
2. **The copy protection check** ([`room10_frame_protection_check` `$3CA7`](../src/room/room_frames_8_11.asm#L289)). If `D6510` does not hold $EF, the handler writes $80 to the first byte of `room_map_00`, `room_map_05` and `room_map_01`. Then it jumps to `show_title_screen`. After that, those three rooms show as empty. The check passed in the coverage. **Observed.** It is check 8 of [protection.md](protection.md). The default build (`PROTECTION` = 0) never damages the maps. **Code.**
3. `update_burst_traps` moves the burst traps.

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 | room 3 at ($A0, $C4) | - |
| 3 | L5 C39 | room 11 at ($10, $C4) | **Conclusion:** reached through the passage at L4 C38 |

Bruce enters from room 3 (trapdoor) and room 11 (marker 2).

## Room 11: the three pits

Room 11 is the crossroads of the castle. Its three pits lead down to rooms 12, 14 and 16. After Bruce clears those three rooms, room 11 sends him to room 13. The room has no enemies. **Code.**

![Room 11](images/rooms/room11.png)

The screenshot shows a purple room with a climbing column at the left and three pits in the middle. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_11`, 247 bytes |
| Colours | fill $FB, charset $3A, `room_palette_r11`, no split |
| Start A / B | $40, $4C / 0, 0 |
| Enemies | none |
| Lanterns | 3, `lantern_list_room11`: L3 C18, L3 C21, L10 C7 (+8) |
| Handlers | `room_init_none`, `room11_frame` |

**The setup.** None (`room_init_none`). But [`draw_room` `$09BC`](../src/room/draw_room.asm#L28) has a rule for room 11. When rooms 12, 14 and 16 are cleared, it sends Bruce to the start of room 13 (`place_bruce_at_room_start` with X = 13). **Code**. This code never ran in the coverage.

**The behaviour.** When Bruce takes lantern L10 C7 (`lantern_list_room11+8`), [`room11_frame` `$3CC0`](../src/room/room_frames_8_11.asm#L318) starts the moving column again, one time (`room_state_a`). It sets `anim_chars_direction` = 0 and starts the speed curve again. Then it runs `update_burst_traps` and `animate_scrolling_chars`. **Code.**

**The links to other rooms.** In room 11, [`check_exit_edge` `$30D4`](../src/actor/touch_effects.asm#L154) allows an exit at all places, not only at a screen edge. So the three pits of line 7 are exits. **Code.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 | room 10 at ($A0, $5A) | - |
| 3 | L7 C9-12 (left pit) | room 12 at ($10, $5C) | - |
| 4 | L7 C18-21 (middle pit) | room 14 at ($10, $5E) | - |
| 5 | L7 C27-30 (right pit) | room 16 at ($10, $5C) | - |
| - | room entry | room 13 | rooms 12, 14, 16 cleared |

Bruce enters from room 10 (marker 3), room 12 (marker 3), room 14 (marker 3) and room 16 (marker 3).

## Room 12: the hall with the ramps

Room 12 is the hall below the left pit of room 11. Its passages lead back up to room 11 and on to room 14. The passage to room 11 opens only after two conditions: room 12 is cleared, and Bruce has two lanterns of room 14. **Code.**

![Room 12](images/rooms/room12.png)

The screenshot shows a grey hall with three floors and blue ramps. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_12`, 387 bytes |
| Colours | fill $F9, charset $3A, `room_palette_r10_12_14_16`, split $56 |
| Start A / B | $18, $5C / $70, $5C |
| Enemies | Ninja $04 / $04 (side $80), Yamo $20 / $20 (side $80) |
| Lanterns | 3, `lantern_list_room12`: L4 C36, L7 C36, L10 C36 (+8) |
| Handlers | `room12_init`, `room12_frame` |

**The setup.** [`room12_init` `$34BD`](../src/room/room_specific_init.asm#L149) sets `room_state_a` = 1. So the handler draws the first passage on two passes.

**The behaviour.** [`room12_frame` `$3E4C`](../src/room/room_frames_12_17.asm#L11) does three things on each pass. **Code.**

1. When Bruce has lantern L10 C36 (`lantern_list_room12+8`), the handler calls [`open_passage_dark` `$3AB4`](../src/room/passage_open.asm#L69) at L10 C38. The flag is `room_state_a`.
2. The second passage needs two conditions. Room 12 must be cleared, and the room 14 lanterns L10 C9 (`lantern_list_room14+8`) and L10 C30 (`lantern_list_room14+$C`) must be taken. Then, one time (`room_state_b`), the handler calls `open_passage_dark` at L7 C38.
3. `update_burst_traps` moves the burst traps.

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L8 C39 | room 11 at ($34, $BE) | **Conclusion:** reached through the passage at L7 C38 |
| 4 | L11 C39 | room 14 at ($10, $BE) | **Conclusion:** reached through the passage at L10 C38 |

Bruce enters from room 11 (left pit) and room 14 (marker 4).

## Room 13: the falling room

Bruce falls through room 13 from the top, after rooms 12, 14 and 16 are cleared. Each of three height bands gives 500 points one time per player and game loop. Floor movers run along the floors. The room has no enemies and no lanterns. **Code.**

![Room 13](images/rooms/room13.png)

The screenshot shows a blue room with four long floors. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_13`, 128 bytes, 442 cells |
| Colours | fill $FA, charset $3A, `room_palette_r13`, no split |
| Start A / B | $98, $32 / 0, 0 |
| Enemies | none (the delay columns hold values, but the flag disables them) |
| Lanterns | 0, `lantern_list_room13` (dummy record) |
| Handlers | `room13_init`, `room13_frame` |

The map decodes to two cells more than the play area holds. This is [the map overflow](rooms.md#map-sizes-and-the-overflow).

**The setup.** [`room13_init` `$34C3`](../src/room/room_specific_init.asm#L159) fills the 10 slots of the floor movers ([hazards](rooms.md#hazards)). Some values depend on `game_loop_count`, so the later game loops have longer tracks. Also, [`actor_calc_tile_pos` `$1C39`](../src/game/game_main_loop.asm#L91) adds 4 to the Y of the actors in room 13 before it calculates the line. **Code.**

**The behaviour.** [`room13_frame` `$3E7C`](../src/room/room_frames_12_17.asm#L41) runs on each pass. **Observed** (coverage: the lowest band and the movers ran).

1. The handler sets X = `current_player` * 4.
2. Bruce's `actor_y` selects a band: $64-$89 is band 0, $8A-$B5 is band 1, and $B6 or more is band 2. Above $64, the handler does nothing.
3. If [`room13_band_bonus` `$014B`](../src/constants.asm#L145) + X + band is 1, the handler sets it to 0. The player gets 500 points ([`add_score` `$3175`](../src/game/score.asm#L52) with $01 at byte 1 and $F4 at byte 2). The pass stops there.
4. Else [`update_floor_movers` `$104B`](../src/game/game_setup.asm#L169) moves the movers on even passes. Only sprites 0 and 1 (Bruce) stay on.

~~~mermaid
stateDiagram-v2
  state "Bonus there (flag 1)" as There
  state "Bonus given (flag 0)" as Given
  [*] --> There: init_game_variables
  There --> Given: Bruce Y in the band, +500
  Given --> There: room19_frame (next game loop)
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Bonus there | `actor_y` in the band of the flag | Bonus given, 500 points | `room13_frame_award_bonus` |
| Bonus given | `room19_frame` starts the next game loop | Bonus there (4 flags of the current player = 1) | `room19_frame_rearm_loop` |

Each player has 4 flags (`$014B-$014E` and `$014F-$0152`). Room 13 uses 3 of them. **Code.**

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C39 | room 15 at ($10, $C3) | - |
| - | entry | from room 11 at start A ($98, $32) | rooms 12, 14, 16 cleared |

Bruce enters from room 11 (the `draw_room` rule) and from room 15 (marker 2 at ($A0, $C4)).

## Room 14: the hall with the two ramps

Room 14 is the hall below the middle pit of room 11, between rooms 12 and 16. The lanterns of line 7 open its passage to room 11. The lanterns of line 10 open a passage in room 12. **Code.**

![Room 14](images/rooms/room14.png)

The screenshot shows a grey hall with blue ramps at the two sides, with Yamo in a fight with Bruce. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_14`, 366 bytes |
| Colours | fill $F9, charset $3A, `room_palette_r10_12_14_16`, split $56 |
| Start A / B | $18, $5C / $92, $BE |
| Enemies | Ninja $08 / $08 (side $02), Yamo $20 / $30 (side 0) |
| Lanterns | 4, `lantern_list_room14`: L7 C9, L7 C30 (+4), L10 C9 (+8), L10 C30 (+12) |
| Handlers | `room14_init`, `room14_frame` |

**The setup.** [`room14_init` `$358D`](../src/room/room_specific_init.asm#L249) sets `room_state_a` = 1. So the handler draws the passage on two passes.

**The behaviour.** When Bruce has lanterns L7 C9 and L7 C30, [`room14_frame` `$3ECC`](../src/room/room_frames_12_17.asm#L88) opens a passage at L4 C38. The flag is `room_state_a`, and [`open_passage_dark` `$3AB4`](../src/room/passage_open.asm#L69) draws the passage. Then the handler runs `update_burst_traps`. **Code.**

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L5 C39 | room 11 at ($50, $BE) | **Conclusion:** reached through the passage at L4 C38 |
| 4 | L11 C0 | room 12 at ($A0, $BE) | - |
| 5 | L11 C39 | room 16 at ($10, $BE) | - |

Bruce enters from room 11 (middle pit), room 12 (marker 4) and room 16 (marker 4).

## Room 15: the tower

Room 15 is the tower between the falling room and the hall of sliders. Its lanterns open the walls of the tower in three steps. The last step comes when the room is cleared, and it opens the right wall to room 17. **Code.**

![Room 15](images/rooms/room15.png)

The screenshot shows a dark tower with ladders in the middle, under a blue sky, with a stone wall and a white fence. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_15`, 168 bytes |
| Colours | fill $FC, charset $3A, `room_palette_r15`, splits $B6, $C7 (3 bands) |
| Start A / B | $1C, $C3 / $7A, $C4 |
| Enemies | Ninja $08 / $08 (side 0), Yamo $30 / $50 (side 0) |
| Lanterns | 6, `lantern_list_room15`: L3 C19, L3 C21 (+4), L4 C14 (+8), L4 C26, L6 C13 (+16), L6 C27 |
| Handlers | `room15_init`, `room15_frame` |

**The setup.** [`room15_init` `$3593`](../src/room/room_specific_init.asm#L255) sets `room_state_a`, `room_state_b` and `room_state_c` = 1. So the handler draws each opening on two passes.

**The behaviour.** [`room15_frame` `$3EE6`](../src/room/room_frames_12_17.asm#L106) runs three one-shot events. **Code.**

| Event | Flag | Condition | Action |
|---|---|---|---|
| 1 | `room_state_a` | lantern L3 C19 (`lantern_list_room15`) taken | tile $57 (blank) at L3 C17, tile $58 (code $2F) at L4 C17, sound $8A |
| 2 | `room_state_b` | lanterns L3 C21, L4 C14 and L6 C13 (`lantern_list_room15+4`, `+8`, `+$10`) taken | tiles $57 / $58 at L3 / L4 C23, sound $8A |
| 3 | `room_state_c` | room 15 cleared | tile $59 (codes $2F) at L9 C37, tiles $5A and $5B (codes $00 $00 $03) at L8 and L7 C37, sound $8A |

Events 1 and 2 open the walls of the tower at line 3 (code $45 at C17, code $43 at C23). They also put a floor cell at line 4. Event 3 opens the right wall at C39 and puts exit marker 3 at L7 C39 and L8 C39. **Code** (map cells).

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 | room 13 at ($A0, $C4) | - |
| 3 | L7-8 C39 (tiles $5A, $5B) | room 17 at ($10, $B3) | room 15 cleared |

Bruce enters from room 13 (marker 2) and room 17 (marker 2).

## Room 16: the hall with the extra fall

Room 16 is the hall below the right pit of room 11. It holds the extra fall: an item that gives the player one more fall, up to 5 times in a game. When the room is cleared, a passage opens back to room 11. **Code.**

![Room 16](images/rooms/room16.png)

The screenshot shows a grey hall with three floors. The yellow item at the right of the lowest floor is the extra fall. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_16`, 305 bytes |
| Colours | fill $F9, charset $3A, `room_palette_r10_12_14_16`, split $56 |
| Start A / B | $18, $5C / $81, $8E |
| Enemies | Ninja $08 / $08 (side $80), Yamo $20 / $30 (side $02) |
| Lanterns | 2, `lantern_list_room16`: L4 C32, L7 C5 |
| Handlers | `room16_init`, `room16_frame` |

**The setup.** [`room16_init` `$359F`](../src/room/room_specific_init.asm#L264) sets colour RAM $FF (colour 15) for the extra-fall item (screen rows 19-22, columns 36-37). When `extra_fall_pickups_left` + `current_player` is 0, the handler erases the item with `draw_room16_bonus_taken`. **Code.**

**The behaviour.** When room 16 is cleared, [`room16_frame` `$3F5B`](../src/room/room_frames_12_17.asm#L166) opens a passage at L7 C1 one time. The flag is `room_state_a`, and [`open_passage_dark` `$3AB4`](../src/room/passage_open.asm#L69) draws the passage. Then the handler runs `update_burst_traps`. **Code.**

**The extra fall.** The frame handler does not control the item. [`handle_touched_tile` `$2E89`](../src/actor/background_touch.asm#L61) sends codes $2D and $2E in room 16 to [`collect_room16_bonus` `$2FD6`](../src/actor/touch_effects.asm#L8). That routine accepts only Bruce, and only at `actor_y` $A0 or more. Then it does these steps:

1. It decrements [`extra_fall_pickups_left` `$4E95`](../src/room/lantern_lists.asm#L109) + player. The value is 5 at a game start.
2. It adds one fall to `falls_left`.
3. It plays sound $8E and erases the item.

The map draws the item again at the next visit while the count is not 0. So a player can take it up to 5 times. **Code**. This code never ran in the coverage.

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L8 C0 | room 11 at ($80, $BE) | **Conclusion:** reached through the passage at L7 C1 |
| 4 | L11 C0 | room 14 at ($A0, $BE) | - |

Bruce enters from room 11 (right pit) and room 14 (marker 5).

## Room 17: the hall of sliders

Room 17 is the last room before the wizard. Three sliders run along long tracks, and a runner moves on line 5. The colour of screen row 3 blinks. The two lanterns of the room fill gaps in the floor. The room has no enemies. **Code.**

![Room 17](images/rooms/room17.png)

The screenshot shows a grey and yellow room with orange floors, three long slider tracks and pillars. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_17`, 259 bytes, 442 cells |
| Colours | fill $FF, charset $3A, `room_palette_r17`, no split |
| Start A / B | $18, $B4 / 0, 0 |
| Enemies | none |
| Lanterns | 2, `lantern_list_room17`: L10 C38, L11 C31 (+4) |
| Handlers | `room17_init`, `room17_frame` |

The map decodes to two cells more than the play area holds. This is [the map overflow](rooms.md#map-sizes-and-the-overflow).

**The setup.** [`room17_init` `$35C4`](../src/room/room_specific_init.asm#L284) does these steps:

1. It sets colour RAM $FF (colour 15) at screen row 19, column 38. This is the cell of lantern L10 C38.
2. It sets `room_state_a` and `room_state_b` = 1.
3. It puts the runner at L5 C11.
4. It puts sliders 0, 1 and 2 at L3, L7 and L9, column 8, with `slider_timer` = $F8, $F1 and $EA.

**The behaviour.** [`room17_frame` `$3F71`](../src/room/room_frames_12_17.asm#L188) runs on each pass. **Observed** (coverage), but not the two lantern events.

1. `room_state_c` counts 11 passes. Then [`room17_frame_colour_loop` `$3F86`](../src/room/room_frames_12_17.asm#L198) toggles bit 1 of the colour in the colour RAM of screen row 3, columns 8-35.
2. The runner of line 5 moves right on every second pass (`room_state_d`), from C11 to C27.
3. When Bruce takes lantern L10 C38 (`lantern_list_room17`), the handler draws tile $5D (codes $44 $44) at L10 C37. It does this one time, with `room_state_a` tested by `beq`.
4. When Bruce takes lantern L11 C31 (`lantern_list_room17+4`), the handler draws tile $5C (codes $49 $49 $49) at L10 C24. It does this one time (`room_state_b`). The tile fills the gap of line 10 between the code $49 cells at C23 and C27. **Code** (map cells).
5. `update_burst_traps` moves the burst traps.
6. The three sliders run in one loop ([sliders](rooms.md#sliders)).

The runner moves on every second pass:

~~~mermaid
stateDiagram-v2
  state "Step (room_state_d 0 -> $FF -> 1)" as Step
  state "Skip (room_state_d 1 -> 0)" as Skip
  [*] --> Step: room_init_clear_vars
  Step --> Skip: next pass
  Skip --> Step: next pass
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Step | `room_state_d` - 1 is negative | `room_state_d` = 1, runner one column right | `room17_frame_runner_rearm` |
| Skip | `room_state_d` - 1 = 0 | no move | `room17_frame_runner` |

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L10 C0 | room 15 at ($A0, $93) | - |
| 3 | L3 C39 | room 18 at ($10, $C6) | - |

Bruce enters from room 15 (marker 3) and room 18 (marker 2, until the wizard is defeated).

## Room 18: the wizard

Room 18 is the fight with the wizard. Two fireballs fall from the wizard, and they kill Bruce when they touch him. The eyes of the wizard follow Bruce. The room has one lantern. When Bruce takes it, the wizard is defeated and the player gets 3000 points. After the defeat sequence, the exit to room 19 opens. The way back to room 17 closes. **Code.** **Observed** in a run of the analysis.

![Room 18](images/rooms/room18.png)

The screenshot shows the face of the wizard at the top of the room, above a purple platform. Bruce enters at the bottom left. **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_18`, 336 bytes, 442 cells |
| Colours | fill $FE, charset $3C (`charset_wizard`), `room_palette_r18`, no split |
| Start A / B | $18, $C6 / 0, 0 |
| Enemies | none |
| Lanterns | 1, `lantern_list_room18`: L11 C37 |
| Handlers | `room18_init`, `room18_frame` |

The map decodes to two cells more than the play area holds. This is [the map overflow](rooms.md#map-sizes-and-the-overflow).

**The setup.** [`room18_init` `$35FA`](../src/room/room_specific_init.asm#L317) does these steps. **Code.**

1. It sets colour RAM $FE (colour 14) for the full play area.
2. It clears the fireball sprite data at `$8340-$83BF`.
3. It sets no Y expansion and X expansion for all 8 sprites.
4. It sets `room_state_a` = 1 (wizard present) and `room_state_b` = 1 (animation timer).
5. It makes the two fireballs inactive ([`fireball_active` `$432E`](../src/game/fireball_text_score_vars.asm#L8) = 0, 0). Fireball 0 starts at once, and fireball 1 starts after 16 passes ([`fireball_respawn_delay` `$4330`](../src/game/fireball_text_score_vars.asm#L12) = 0 and $10).
6. It writes 6 and 7 to `fireball_unused_init`. No code reads these bytes.

**The behaviour.** [`room18_frame` `$3CDC`](../src/room/wizard_room.asm#L13) has three states. The wizard alive ran in the coverage. The defeat ran in a run of the analysis: the wizard flashes and disappears, and the score increases by 3000. **Observed.**

**Deadly characters do not kill in room 18.** [`touch_deadly_tile` `$304B`](../src/actor/touch_effects.asm#L75) returns at once in this room. **Code.**

1. **Wizard alive** (`room_state_a` = 1, the lantern is present). [`update_fireballs` `$4133`](../src/room/wizard_fireballs.asm#L13) moves the fireballs. The sprite-sprite collision register can show sprite 0 or 1 (Bruce) with sprite 6 or 7 (a fireball). If Bruce is not dying, [`set_actor_hazard_death` `$407D`](../src/room/room_hazard_draw.asm#L37) then kills him.
2. **The face.** Every 8 passes (`room_state_b`), the handler sets the gaze `room_state_c` from `actor_x` ([`wizard_face_zone_x` `$4A89`](../src/room/room_tables.asm#L13)). The gaze is 2 when `actor_x` >= $76, 1 when `actor_x` >= $3A, else 0. The handler draws tile $38 + gaze at L2 C16. The face toggles (`room_state_d`) between two frames at L3 / L4 C18: tiles $41/$44 + gaze and tiles $3B/$3E + gaze (`draw_wizard_face_top`, `draw_wizard_face_bottom`).
3. **Lantern taken** (the first pass with the record state 0). The handler sets `room_state_a` = 0 and calls [`clear_fireball_sprites` `$423F`](../src/room/wizard_fireballs.asm#L171). It switches off sprites 5-7 and draws tile $61 (code $06) at L11 C0. It gives 3000 points, sets the gaze to 1 and sets `room_state_b` = $50.
4. **Defeat sequence** ([`room18_wizard_defeated` `$3DAF`](../src/room/wizard_room.asm#L134), for `room_state_b` passes). The handler puts random colours on the wizard area of colour RAM, with colour 0 on the last pass. It sets [`room_vmcsb` `$00F2`](../src/constants.asm#L117) = $3E (`charset_wizard_flash`). While more than 16 passes remain, it sets $3C at random, so the charset flickers. It plays sound $8B and toggles the four wizard parts (tiles $47-$4E).
5. **Wizard gone** ([`room18_wizard_gone` `$3D9B`](../src/room/wizard_room.asm#L115), `room_state_b` = 0). On each pass, the handler draws tile $5E (codes $00 $00 $03) at L11 C37 and tile $5F (codes $5A $5A) at L12 C38. This is the open exit where the lantern was.

~~~mermaid
stateDiagram-v2
  state "Present (a = 1)" as Present
  state "Defeat sequence (a = 0, b > 0)" as Defeat
  state "Gone (a = 0, b = 0)" as Gone
  [*] --> Present: room18_init
  Present --> Present: fireballs, face every 8 passes
  Present --> Defeat: lantern L11 C37 taken, +3000
  Defeat --> Defeat: b - 1, flash, sound $8B
  Defeat --> Gone: b = 0
  Gone --> Gone: exit tiles $5E, $5F
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Present | `lantern_list_room18` = 1 | Present: `update_fireballs`, hit test, face | `room18_frame_fireballs` |
| Present | `lantern_list_room18` = 0 | Defeat: `room_state_a` = 0, `room_state_b` = $50, sprites 5-7 off, tile $61 at L11 C0, +3000 | `room18_frame_wizard_alive` |
| Defeat | `room_state_b` <> 0 | Defeat: colours, charset flicker, sound $8B, parts, `room_state_b` - 1 | `room18_wizard_defeated` |
| Defeat | `room_state_b` = 0 | Gone | `room18_wizard_defeated` |
| Gone | every pass | Gone: tiles $5E, $5F | `room18_wizard_gone` |

**The flash charset stays.** The last pass of the sequence leaves `room_vmcsb` = $3E. So after the defeat, the room shows with [`charset_wizard_flash` `$B800`](../src/constants.asm#L203), the expanded [`room_charset_d` `$9C00`](../src/graphics/room_charset_d.asm#L8). No code resets it until the next `draw_room`. **Code.**

**The links to other rooms.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 | room 17 at ($A0, $44) | until the wizard is defeated: tile $61 (code $06) replaces the marker |
| 3 | L11 C39 (tile $5E) | room 19 at ($10, $96) | the defeat sequence is over |
| 4, 5 | lines 2-9, inside the wizard graphics | (entry X 0: room 0 at (0, 0)) | not known if Bruce can get there |

Bruce enters from room 17 (marker 3). It is not known if Bruce can get to markers 4 and 5 in the wizard graphics ([still open](rooms.md#still-open)).

## Room 19: congratulations

Room 19 ends a game loop. It shows "** CONGRATULATIONS **" for about 22 seconds. Then it starts the next game loop in room 0, with all lanterns back. The room has no enemies, no lanterns and no exits. **Code.** **Observed** (coverage).

![Room 19](images/rooms/room19.png)

The screenshot shows a castle of blue and white bricks with arches. The status line is blank, and line 0 shows "** CONGRATULATIONS **". **Observed.**

**The data.**

| Table | Value |
|---|---|
| Map | `room_map_19`, 416 bytes |
| Colours | fill $FF, charset $3A, `room_palette_r19`, no split |
| Start A / B | $12, $95 / 0, 0 |
| Enemies | none |
| Lanterns | 0, `lantern_list_room19` (dummy record) |
| Handlers | `room19_init`, `room19_frame` |

**The setup.** [`room19_init` `$425F`](../src/room/ending_room.asm#L7) sets [`title_countdown` `$0049`](../src/constants.asm#L35) = $0458 frames. The interrupt decrements it, so it lasts about 22 seconds on PAL. The handler writes 40 zero bytes in screen row 0, so the status line is blank.

**The behaviour.** [`room19_frame` `$4272`](../src/room/ending_room.asm#L27) shows random colours until the countdown is 0. Then it starts the next game loop. **Observed** (coverage: both states ran).

~~~mermaid
stateDiagram-v2
  state "Shimmer (countdown <> 0)" as Shimmer
  state "Next game loop" as Next
  [*] --> Shimmer: room19_init
  Shimmer --> Shimmer: random colours, CONGRATULATIONS
  Shimmer --> Next: title_countdown = 0
  Next --> [*]: place_bruce_at_room_start, room 0
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Shimmer | `title_countdown` <> 0 | Shimmer: a random colour (0-7, multicolour) in colour RAM screen rows 17-24, columns 4-32. Tile 4 "** CONGRATULATIONS **" at L0 C10 | `room19_frame_shimmer` |
| Shimmer | `title_countdown` = 0 | Next game loop | `room19_frame` |
| Next game loop | - | `game_loop_count` + 1, 4 flags of `room13_band_bonus` of the current player = 1, `reset_lantern_counts`, `reset_all_lanterns`, `reset_unvisited_rooms`, `place_bruce_at_room_start` with X = 0 | `room19_frame` |

**What the next game loop changes.** `reset_unvisited_rooms` marks rooms 1-19 as not visited for the current player. So each first visit gives 2000 points again. When `game_loop_count` is not 0, both spawn timers are 3 in all rooms. The floor movers of room 13 then also have longer tracks. **Code.**

**The links to other rooms.** Bruce enters from room 18 (marker 3). He leaves to room 0 (start A).

## Dependencies between rooms

Most rooms open their passages with their own lanterns. The table gives the conditions by which one room changes another room. It also gives the `draw_room` rule for room 11 and the special case of room 18. These conditions put the rooms in a fixed order of play. Room 6 opens the garden, the three halls below room 11 open room 13, and room 19 resets all rooms. **Code.**

| Room | Depends on | Condition | Effect | Code |
|---|---|---|---|---|
| 0 | room 6 | cleared | statue mouth at L9 C7 moves | `room00_frame` |
| 1 | rooms 0, 1, 2 | cleared | trapdoor opens, marker 3 to room 5 | `room01_frame` |
| 1 | room 6 | not cleared | trapdoor can open (cleared: stays closed) | `room01_frame` |
| 2 | room 6 | cleared | floor opening with marker 5 to room 3, statue mouth at L9 C33 | `room02_frame` |
| 5 | room 6 | cleared, with lantern L3 C28 or L3 C38 of room 5 taken | top opening, marker 5 to room 1 | `room05_frame` |
| 8 | room 7 | cleared, with lantern L7 C6 of room 8 taken | passage at L7 C14 | `room08_frame` |
| 8 | room 9 | lanterns L10 C27, L10 C28 taken, with room 8 cleared | passage at L2 C38 (to marker 3, room 9) | `room08_frame` |
| 8 | room 7 | cleared, with room 8 cleared | passage at L10 C38 (to marker 5, room 9) | `room08_frame` |
| 11 | rooms 12, 14, 16 | cleared | entering room 11 leads to room 13 | `draw_room` |
| 12 | room 14 | lanterns L10 C9, L10 C30 taken, with room 12 cleared | passage at L7 C38 (to marker 3, room 11) | `room12_frame` |
| 13 | room 19 | next game loop | band bonus flags set again | `room19_frame` |
| all | room 19 | next game loop | lanterns, lantern counts and visit flags reset, `game_loop_count` + 1 | `room19_frame` |
| all but 18 | room 18 | - | deadly characters kill in all rooms but room 18 | `touch_deadly_tile` |

### The order of play

**Conclusion.** These conditions and the exit tables give an order of play. No run played through this order. The diagrams show the first way into each room. The [exit tables](rooms.md#exits) give the ways back.

The first diagram shows the garden and the caves. Bruce must do these steps:

1. Clear the garden to get down to room 5.
2. Clear the caves to room 9 to get to room 6.
3. Clear room 6 to open the way from room 2 to room 3.

~~~mermaid
flowchart LR
  R0["Room 0"] --> R1["Room 1"] --> R2["Room 2"]
  R1 -- "trapdoor: 0, 1, 2 cleared" --> R5["Room 5"]
  R5 -- "lantern L10 C2" --> R4["Room 4"]
  R4 --> R7["Room 7"] --> R8["Room 8"] --> R9["Room 9"]
  R9 -- "9 cleared" --> R6["Room 6"]
  R6 -- "6 cleared" --> R5
  R5 -- "6 cleared" --> R1
  R2 -- "6 cleared" --> R3["Room 3"]
~~~

The second diagram shows the castle and the end. Bruce goes from room 3 down to the castle. He goes through the three halls below room 11 to room 13. Then he goes up through the tower to the wizard.

~~~mermaid
flowchart LR
  R3["Room 3"] -- "3 cleared" --> R10["Room 10"] --> R11["Room 11"]
  R11 --> R12["Room 12"]
  R11 --> R14["Room 14"]
  R11 --> R16["Room 16"]
  R11 -- "12, 14, 16 cleared" --> R13["Room 13"]
  R13 --> R15["Room 15"]
  R15 -- "15 cleared" --> R17["Room 17"] --> R18["Room 18"]
  R18 -- "wizard defeated" --> R19["Room 19"]
  R19 -- "next game loop" --> R0["Room 0"]
~~~
