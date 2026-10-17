# Bruce Lee: the room catalogue

One section for each of the 20 rooms. Each section has the screenshot, the entries of the room in each per-room
table, the init handler, the frame handler and the links to other rooms. The page [rooms.md](rooms.md) explains
the tables, the map format, [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room), the lanterns, the passages and the hazards that the rooms share.

**Conventions.**

- Addresses are C64 addresses. Names are the names of the knowledge.
- A *pass* is one run of [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) (3 frames). An *even pass* has [`pass_parity`](../src/constants.asm#L76) [`$007B`](reference/variables.md#pass_parity) = 0.
- "L7 C31" is the cell at text line 7, column 31. Text line L uses screen rows 2L-1 and 2L; the map fills lines
  2-12.
- A *tile* is a message of [`print_message`](../src/actor_driver_text.asm#L59) [`$17E2`](reference/modules/actor_driver_text.md#print_message), "tile $13" is message $13. A *code* is the character code of
  the upper row of a cell.
- An *exit marker N* is a cell with code N (2-5). It uses the exit tables of set N (rooms.md, section 2.2). "Marker
  3 at L12 C19-21 to room 5 at ($2C, $32)" means: destination room 5, Bruce's entry X = $2C and Y = $32.
- A room is *cleared* when its [`room_lanterns_left`](../src/constants.asm#L33) [`$002A`](reference/variables.md#room_lanterns_left) + room is 0. "Lantern L4 C11" is the lantern record
  with that position; its state byte is the first byte of the record.
- **Observed** marks a fact that a run showed (screenshots, the coverage runs, the runs of the analysis notes).
  **Code** marks a fact from the code only. **Conclusion** marks an interpretation.
- Every screenshot was taken about 250 frames after Bruce entered the room.

## Room 0: the garden with the ox statue

![Room 0](images/rooms/room00.png)

The screenshot shows the first room: snow mountains, an ox statue on a pedestal at the left, a blue lattice in the
middle and a pagoda at the right. Bruce starts here at a game start and after each completed game loop.
**Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_00`](../src/room_maps_00_04.asm#L18) [`$68F9`](reference/modules/room_maps_00_04.md#room_map_00), 272 bytes, 440 cells |
| Colours | fill $FE, charset $38 ([`charset_rooms_0_9`](../src/constants.asm#L204) [`$A000`](reference/variables.md#charset_rooms_0_9)), [`room_palette_r0_3`](../src/room_palettes.asm#L29) [`$47C8`](reference/modules/room_palettes.md#room_palette_r0_3), splits $78, $97 |
| Start A / B | $1A, $C4 / $9F, $62 |
| Enemies | yes; Ninja $68 / $A0, side $02; Yamo $F0 / $EE, side $80 |
| Lanterns | 6, [`lantern_list_room0`](../src/lantern_lists.asm#L21) [`$4D0C`](reference/modules/lantern_lists.md#lantern_list_room0) |
| Handlers | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none), [`room00_frame`](../src/room_frames_0_7.asm#L9) [`$3642`](reference/modules/room_frames_0_7.md#room00_frame) |

**Setup.** None.

**Behaviour.** [`room00_frame`](../src/room_frames_0_7.asm#L9) waits until room 6 is cleared. Then the mouth of the statue at L9 C7 moves on even
passes. [`room_state_a`](../src/room_dispatch.asm#L7) is the timer and [`room_state_b`](../src/room_dispatch.asm#L9) the shown frame. **Code**; never executed in the coverage.

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
| Still | [`room_lanterns_left+6`](../src/constants.asm#L33) [`$0030`](reference/variables.md#room_lanterns_left) <> 0 | Still | [`room00_frame`](../src/room_frames_0_7.asm#L9) [`$3642`](reference/modules/room_frames_0_7.md#room00_frame) |
| Still / Mouth B | even pass, [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) goes below 0, [`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b) = 0 | Mouth A: sound $81, tile $1D at L9 C7, [`room_state_b`](../src/room_dispatch.asm#L9) = 1 | [`room00_frame`](../src/room_frames_0_7.asm#L9) |
| Mouth A | next even pass, [`room_state_b`](../src/room_dispatch.asm#L9) = 1 | Mouth B: tile $1E, [`room_state_b`](../src/room_dispatch.asm#L9) = 0, [`room_state_a`](../src/room_dispatch.asm#L7) = 5 | [`room00_frame_mouth_b`](../src/room_frames_0_7.asm#L28) [`$3667`](reference/modules/room_frames_0_7.md#room00_frame_mouth_b) |

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L8 C39 | room 1 at ($10, $92) | - |
| 5 | L5 C39 | room 1 at ($0F, $62) | - |

Entered from room 1 (markers 2 and 4) and from room 19 ([`place_bruce_at_room_start`](../src/room_misc_support.asm#L11) [`$3217`](reference/modules/room_misc_support.md#place_bruce_at_room_start) with X = 0).

## Room 1: the pagodas and the first trapdoor

![Room 1](images/rooms/room01.png)

Two pagoda buildings left and right, a blue lattice in the middle. The trapdoor is in the floor below the lattice.
**Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_01`](../src/room_maps_00_04.asm#L55) [`$6A09`](reference/modules/room_maps_00_04.md#room_map_01), 309 bytes |
| Colours | fill $FE, charset $38, [`room_palette_r0_3`](../src/room_palettes.asm#L29), splits $78, $97 |
| Start A / B | $18, $62 / $95, $92 |
| Enemies | yes; Ninja $78 / $A0, side $02; Yamo $EE / $EE, side $80 |
| Lanterns | 6, [`lantern_list_room1`](../src/lantern_lists.asm#L26) [`$4D25`](reference/modules/lantern_lists.md#lantern_list_room1) |
| Handlers | [`room01_init`](../src/room_specific_init.asm#L9) [`$33F6`](reference/modules/room_specific_init.md#room01_init), [`room01_frame`](../src/room_frames_0_7.asm#L42) [`$3679`](reference/modules/room_frames_0_7.md#room01_frame) |

**Setup.** [`room01_init`](../src/room_specific_init.asm#L9) sets [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) = 3 (the trapdoor step counter).

**Behaviour.** On even passes, when rooms 0, 1 and 2 are cleared and room 6 still has lanterns, [`room01_frame`](../src/room_frames_0_7.asm#L42) opens
the trapdoor at L12 C17-21 in 4 steps: tile $10 + [`room_state_a`](../src/room_dispatch.asm#L7) after each decrement, so tiles $12, $11, $10, $0F.
[`play_open_sound`](../src/wizard_fireballs.asm#L183) [`$424F`](reference/modules/wizard_fireballs.md#play_open_sound) at the first step. The open trapdoor (tile $0F, codes $22 $22 $03 $03 $03) holds exit marker
3 at C19-21. **Code**; never executed in the coverage.

~~~mermaid
stateDiagram-v2
  state "Closed (3)" as S3
  state "Step 1: tile $12 (2)" as S2
  state "Step 2: tile $11 (1)" as S1
  state "Step 3: tile $10 (0)" as S0
  state "Open: tile $0F ($FF)" as Open
  [*] --> S3: room01_init $33F6
  S3 --> S2: even pass and condition, sound $8A
  S2 --> S1: even pass and condition
  S1 --> S0: even pass and condition
  S0 --> Open: even pass and condition
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| any step 0-3 | odd pass | same | [`room01_frame`](../src/room_frames_0_7.asm#L42) [`$3679`](reference/modules/room_frames_0_7.md#room01_frame) |
| any step 0-3 | [`room_lanterns_left+6`](../src/constants.asm#L33) [`$0030`](reference/variables.md#room_lanterns_left) = 0 (room 6 cleared) | same: the trapdoor stays as it is | [`room01_frame`](../src/room_frames_0_7.asm#L42) |
| step N | rooms 0, 1, 2 cleared, room 6 not cleared, even pass | [`room_state_a`](../src/room_dispatch.asm#L7) - 1, tile $10 + [`room_state_a`](../src/room_dispatch.asm#L7) at L12 C17 | [`room01_frame_draw_trapdoor`](../src/room_frames_0_7.asm#L59) [`$369B`](reference/modules/room_frames_0_7.md#room01_frame_draw_trapdoor) |
| Open ($FF) | - | Open | the `bmi` test |

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L8 C0 | room 0 at ($A0, $92) | - |
| 3 | L12 C19-21 (trapdoor) | room 5 at ($2C, $32) | rooms 0, 1, 2 cleared and room 6 not cleared |
| 4 | L5 C0 | room 0 at ($A1, $62) | - |
| 5 | L5 C39 | room 2 at ($10, $62) | - |

Entered from rooms 0 and 2, and from room 5 (marker 5 at ($58, $66)). **Conclusion:** the trapdoor is the first way
down. Once room 6 is cleared, a new visit to room 1 leaves the trapdoor closed, and the way back to room 5 is the top
opening of room 5.

## Room 2: the second statue

![Room 2](images/rooms/room02.png)

Pagoda roofs with a ladder at the left, a blue lattice in the middle and a second ox statue at the right. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_02`](../src/room_maps_00_04.asm#L97) [`$6B3E`](reference/modules/room_maps_00_04.md#room_map_02), 351 bytes |
| Colours | fill $FE, charset $38, [`room_palette_r0_3`](../src/room_palettes.asm#L29), splits $78, $97 |
| Start A / B | $30, $C4 / $96, $C4 |
| Enemies | yes; Ninja $78 / $A0, side 0; Yamo $EE / $EE, side 0 |
| Lanterns | 10, [`lantern_list_room2`](../src/lantern_lists.asm#L31) [`$4D3E`](reference/modules/lantern_lists.md#lantern_list_room2) |
| Handlers | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none), [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) |

**Setup.** None.

**Behaviour.** [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame):

1. Copy protection: it loops forever unless [`D6510`](../src/constants.asm#L11) [`$0000`](reference/variables.md#D6510) holds $EF, a value that the original loader leaves.
   The copy-protection page describes the checks. **Observed** (coverage: the check passed in all runs).
2. When room 6 is cleared, one time ([`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b)): [`play_open_sound`](../src/wizard_fireballs.asm#L183), tile $1A (codes $00 $00 $05) at L11
   C37 and tile $07 (codes $11 $11 $11) at L12 C37. The right wall opens and exit marker 5 appears at L11 C39.
3. When room 6 is cleared: the statue mouth at L9 C33 moves like the mouth of room 0, with [`room_state_c`](../src/room_dispatch.asm#L11) [`$4E99`](reference/modules/room_dispatch.md#room_state_c)
   as the timer and [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) as the frame ([`room02_frame_mouth`](../src/room_frames_0_7.asm#L106) [`$36CF`](reference/modules/room_frames_0_7.md#room02_frame_mouth), [`room02_frame_mouth_b`](../src/room_frames_0_7.asm#L121) [`$36F0`](reference/modules/room_frames_0_7.md#room02_frame_mouth_b)
   ). **Code**; steps 2 and 3 were never executed in the coverage.

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
| Closed | [`room_lanterns_left+6`](../src/constants.asm#L33) [`$0030`](reference/variables.md#room_lanterns_left) = 0, [`room_state_b`](../src/room_dispatch.asm#L9) = 0 | Opened: sound $8A, tiles $1A and $07 | [`room02_frame`](../src/room_frames_0_7.asm#L75) |
| Opened / Mouth B | even pass, [`room_state_c`](../src/room_dispatch.asm#L11) goes below 0, [`room_state_a`](../src/room_dispatch.asm#L7) = 0 | Mouth A: sound $81, tile $1D at L9 C33 | [`room02_frame_mouth`](../src/room_frames_0_7.asm#L106) [`$36CF`](reference/modules/room_frames_0_7.md#room02_frame_mouth) |
| Mouth A | next even pass | Mouth B: tile $1E, [`room_state_c`](../src/room_dispatch.asm#L11) = 5 | [`room02_frame_mouth_b`](../src/room_frames_0_7.asm#L121) [`$36F0`](reference/modules/room_frames_0_7.md#room02_frame_mouth_b) |

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 4 | L5 C0 | room 1 at ($A1, $62) | - |
| 5 | L11 C39 (tile $1A) | room 3 at ($10, $C4) | room 6 cleared |

Entered from room 1 (marker 5) and room 3 (marker 4).

## Room 3: the towers and the moving ledges

![Room 3](images/rooms/room03.png)

White towers with blue vines, a lattice in the middle and spikes in the floor. Enemy-free. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_03`](../src/room_maps_00_04.asm#L144) [`$6C9D`](reference/modules/room_maps_00_04.md#room_map_03), 382 bytes |
| Colours | fill $FE, charset $38, [`room_palette_r0_3`](../src/room_palettes.asm#L29), splits $62, $97 |
| Start A / B | $20, $C0 / $38, $C4 |
| Enemies | none ([`room_no_enemies`](../src/room_tables.asm#L164) [`$4C9E`](reference/modules/room_tables.md#room_no_enemies) = $FF) |
| Lanterns | 2, [`lantern_list_room3`](../src/lantern_lists.asm#L38) [`$4D67`](reference/modules/lantern_lists.md#lantern_list_room3): L10 C29, L10 C38 |
| Handlers | [`room03_init`](../src/room_specific_init.asm#L14) [`$33FC`](reference/modules/room_specific_init.md#room03_init), [`room03_frame`](../src/room_frames_0_7.asm#L136) [`$3702`](reference/modules/room_frames_0_7.md#room03_frame) |

**Setup.** [`room03_init`](../src/room_specific_init.asm#L14) sets [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) = 3 (the trapdoor step counter).

**Behaviour.** [`room03_frame`](../src/room_frames_0_7.asm#L136) [`$3702`](reference/modules/room_frames_0_7.md#room03_frame) runs two machines. **Code**; the trapdoor never ran in the coverage, the
ledges did (**Observed**).

1. The trapdoor at L12 C29-33: when room 3 is cleared, 4 steps on even passes, like room 1 (tiles $12, $11, $10,
   $0F; sound $8A at the first step; [`room03_frame_draw_trapdoor`](../src/room_frames_0_7.asm#L149) [`$371C`](reference/modules/room_frames_0_7.md#room03_frame_draw_trapdoor)). The open trapdoor holds marker 3 at
   C31-33.
2. The ledges of line 6: [`room_state_c`](../src/room_dispatch.asm#L11) [`$4E99`](reference/modules/room_dispatch.md#room_state_c) counts 33 passes. Then [`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b) toggles, and tile $06
   (7 cells of code $4B) and tile $60 (7 cells of code $09) swap places between C9-15 and C21-27.

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
| Phase 0 ([`room_state_b`](../src/room_dispatch.asm#L9) = 0) | [`room_state_c`](../src/room_dispatch.asm#L11) goes below 0 | Phase 1: [`room_state_b`](../src/room_dispatch.asm#L9) = 1, tile $60 at L6 C9, tile $06 at L6 C21, [`room_state_c`](../src/room_dispatch.asm#L11) = $20 | [`room03_frame_ledges_phase_b`](../src/room_frames_0_7.asm#L174) [`$374B`](reference/modules/room_frames_0_7.md#room03_frame_ledges_phase_b) |
| Phase 1 ([`room_state_b`](../src/room_dispatch.asm#L9) = 1) | [`room_state_c`](../src/room_dispatch.asm#L11) goes below 0 | Phase 0: [`room_state_b`](../src/room_dispatch.asm#L9) = 0, tile $06 at L6 C9, tile $60 at L6 C21, [`room_state_c`](../src/room_dispatch.asm#L11) = $20 | [`room03_frame_swap_ledges`](../src/room_frames_0_7.asm#L160) [`$372C`](reference/modules/room_frames_0_7.md#room03_frame_swap_ledges) |
| either | [`room_state_c`](../src/room_dispatch.asm#L11) >= 0 after the decrement | same | [`room03_frame_ledges_wait`](../src/room_frames_0_7.asm#L158) [`$372B`](reference/modules/room_frames_0_7.md#room03_frame_ledges_wait) |

The trapdoor machine is the one of room 1, with the condition "room 3 cleared" ([`room_lanterns_left+3`](../src/constants.asm#L33) [`$002D`](reference/variables.md#room_lanterns_left) = 0).

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L12 C31-33 (trapdoor) | room 10 at ($10, $B0) | room 3 cleared |
| 4 | L11 C0 | room 2 at ($A1, $C5) | - |
| 5 | none | (room 0 at ($10, $62)) | no marker: not used |

Entered from room 2 (marker 5 after room 6 is cleared) and from room 10 (marker 2).

## Room 4: the dark cave with the blinking lanterns

![Room 4](images/rooms/room04.png)

A dark blue cave with a moving purple column in the middle and two lattice windows. The two lanterns at the top
blink. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_04`](../src/room_maps_00_04.asm#L197) [`$6E1B`](reference/modules/room_maps_00_04.md#room_map_04), 359 bytes, 442 cells (rooms.md, section 9) |
| Colours | fill $FC, charset $38, [`room_palette_r4_6`](../src/room_palettes.asm#L33) [`$47D1`](reference/modules/room_palettes.md#room_palette_r4_6), no split |
| Start A / B | $94, $B4 / $96, $B4 |
| Enemies | yes; Ninja $70 / $70, side $80; Yamo $C0 / $EE, side $80 |
| Lanterns | 2, [`lantern_list_room4`](../src/lantern_lists.asm#L41) [`$4D70`](reference/modules/lantern_lists.md#lantern_list_room4): L4 C11 (lantern 1), L4 C28 (lantern 2, [`lantern_list_room4+4`](../src/lantern_lists.asm#L41) [`$4D74`](reference/modules/lantern_lists.md#lantern_list_room4)) |
| Handlers | [`room04_init`](../src/room_specific_init.asm#L22) [`$3402`](reference/modules/room_specific_init.md#room04_init), [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) |

**Setup.** [`room04_init`](../src/room_specific_init.asm#L22) [`$3402`](reference/modules/room_specific_init.md#room04_init): [`room_state_d`](../src/room_dispatch.asm#L13) [`$4E9A`](reference/modules/room_dispatch.md#room_state_d) = $1F (lantern 2 blinks half a period after lantern 1);
slider 0 at L11 C1, slider 1 at L7 C11, slider 2 at L7 C26; [`slider_timer`](../src/constants.asm#L74) [`$0077`](reference/variables.md#slider_timer) = $FF, $FF, $F4.

**Behaviour.** [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame), every pass. **Observed** (coverage) except the "taken" steps.

1. Lantern 1 blinks while present: [`room_state_c`](../src/room_dispatch.asm#L11) [`$4E99`](reference/modules/room_dispatch.md#room_state_c) + 1; at 32 tile $34 (lit, code $13, can be taken) at L4
   C11; at 64 tile $36 (dark, code $66, cannot be taken) and the counter restarts at 0.
2. Lantern 1 taken, one time ([`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a)): sound $8A, tile $16 (4 blanks) at L8 C11 and L9 C11, slider 1
   erased (frame 6).
3. Lantern 2 blinks the same way with [`room_state_d`](../src/room_dispatch.asm#L13) and tiles $35 / $37 at L4 C28.
4. Lantern 2 taken, one time ([`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b)): [`anim_chars_direction`](../src/constants.asm#L64) [`$0065`](reference/variables.md#anim_chars_direction) = 0 and
   [`anim_chars_speed_step`](../src/options_and_patterns.asm#L53) [`$4321`](reference/modules/options_and_patterns.md#anim_chars_speed_step) = 7 (the moving column restarts), sound $8A, tile $16 at L8 C25 and L9 C25,
   slider 2 erased.
5. Sliders 0 (look B), 1 (while lantern 1 is present) and 2 (while lantern 2 is present). See rooms.md, section 8.1.
6. [`animate_scrolling_chars`](../src/animated_chars.asm#L12) [`$2C70`](reference/modules/animated_chars.md#animate_scrolling_chars).

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
| Map look / Dark | [`lantern_list_room4`](../src/lantern_lists.asm#L41) [`$4D70`](reference/modules/lantern_lists.md#lantern_list_room4) = 1, [`room_state_c`](../src/room_dispatch.asm#L11) reaches $20 | Lit: tile $34 at L4 C11 | [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) |
| Lit | [`room_state_c`](../src/room_dispatch.asm#L11) reaches $40 | Dark: tile $36, [`room_state_c`](../src/room_dispatch.asm#L11) = 0 | [`room04_frame_lantern1_check_dark`](../src/room_frames_0_7.asm#L207) [`$377B`](reference/modules/room_frames_0_7.md#room04_frame_lantern1_check_dark) |
| Lit | Bruce touches code $13 ([`check_lantern_pickup`](../src/lantern_pickup.asm#L15) [`$331C`](reference/modules/lantern_pickup.md#check_lantern_pickup)) | Taken: record state 0 | [`collect_lantern`](../src/background_touch.asm#L142) [`$2F04`](reference/modules/background_touch.md#collect_lantern) |
| Taken | [`room_state_a`](../src/room_dispatch.asm#L7) = 0 | Opened: sound $8A, tile $16 at L8 C11 and L9 C11, slider 1 erased | [`room04_frame_lantern1_taken`](../src/room_frames_0_7.asm#L216) [`$378D`](reference/modules/room_frames_0_7.md#room04_frame_lantern1_taken) |

The same table holds for lantern 2 with [`room_state_d`](../src/room_dispatch.asm#L13), tiles $35 / $37, [`room_state_b`](../src/room_dispatch.asm#L9), column 25 and slider 2.
The dark tiles have codes $66 / $67; these are not lantern codes, so a dark lantern cannot be taken. **Code.**

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L4 C39 | room 5 at ($10, $C2) | - |
| 3 | L12 C1-4 | room 7 at ($1F, $32) | - |

Entered from room 5 (marker 2).

## Room 5: the blue cave

![Room 5](images/rooms/room05.png)

A blue cave with lattice towers in the middle and a moving purple column at the right. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_05`](../src/room_maps_05_09.asm#L7) [`$6F82`](reference/modules/room_maps_05_09.md#room_map_05), 347 bytes |
| Colours | fill $FC, charset $38, [`room_palette_r4_6`](../src/room_palettes.asm#L33), no split |
| Start A / B | $22, $51 / $28, $C2 |
| Enemies | yes; Ninja $18 / $0C, side $80; Yamo $C0 / $60, side $02 |
| Lanterns | 10, [`lantern_list_room5`](../src/lantern_lists.asm#L44) [`$4D79`](reference/modules/lantern_lists.md#lantern_list_room5) |
| Handlers | [`room05_init`](../src/room_specific_init.asm#L48) [`$3428`](reference/modules/room_specific_init.md#room05_init), [`room05_frame`](../src/room_frames_0_7.asm#L378) [`$38AB`](reference/modules/room_frames_0_7.md#room05_frame) |

**Setup.** [`room05_init`](../src/room_specific_init.asm#L48) [`$3428`](reference/modules/room_specific_init.md#room05_init):

1. Copy protection: it loops forever unless [`prot_loader_mark`](../src/constants.asm#L13) [`$0002`](reference/variables.md#prot_loader_mark) holds $32. **Observed** (coverage: passed).
2. Colour RAM $FC for L2 C34-36 (where tile $19 appears later).
3. Slider 0 at L9 C27, slider 1 at L10 C27, slider 2 at L5 C1; [`slider_timer`](../src/constants.asm#L74) = $FF, $FC, $F8.

**Behaviour.** [`room05_frame`](../src/room_frames_0_7.asm#L378) [`$38AB`](reference/modules/room_frames_0_7.md#room05_frame). Three one-shot events (rooms.md, section 5.1), then the sliders and
[`animate_scrolling_chars`](../src/animated_chars.asm#L12). **Code**; the event of lantern L10 C2 ran in the coverage (**Observed**).

| Event | Flag | Condition | Action |
|---|---|---|---|
| Right passages | [`room_state_c`](../src/room_dispatch.asm#L11) [`$4E99`](reference/modules/room_dispatch.md#room_state_c) | lantern L10 C26 ([`lantern_list_room5+$20`](../src/lantern_lists.asm#L44) [`$4D99`](reference/modules/lantern_lists.md#lantern_list_room5)) taken | [`open_passage`](../src/passage_open.asm#L42) [`$3A8A`](reference/modules/passage_open.md#open_passage) at L10 C25 and L10 C26, slider 1 erased |
| Left exit | [`room_state_d`](../src/room_dispatch.asm#L13) [`$4E9A`](reference/modules/room_dispatch.md#room_state_d) | lantern L10 C2 ([`lantern_list_room5+$18`](../src/lantern_lists.asm#L44) [`$4D91`](reference/modules/lantern_lists.md#lantern_list_room5)) taken | [`open_passage`](../src/passage_open.asm#L42) at L10 C0, tile $15 (code $02, marker 2) at L11 C0 |
| Top exit | [`room_state_e`](../src/room_dispatch.asm#L15) [`$4E9B`](reference/modules/room_dispatch.md#room_state_e) | room 6 cleared and lantern L3 C28 ([`lantern_list_room5+8`](../src/lantern_lists.asm#L44) [`$4D81`](reference/modules/lantern_lists.md#lantern_list_room5)) or L3 C38 ([`lantern_list_room5+$10`](../src/lantern_lists.asm#L44) [`$4D89`](reference/modules/lantern_lists.md#lantern_list_room5)) taken | tile $19 (codes $61 $05 $63) at L2 C34, [`open_passage`](../src/passage_open.asm#L42) at L3 C30 and L6 C32 |

Sliders: 0 at L9 C27-28, 1 at L10 C27-28 while lantern L10 C26 is present, 2 at L5 C1-2 (look B).

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 (tile $15) | room 4 at ($9C, $51) | lantern L10 C2 taken |
| 3 | L4 C39 | room 6 at ($10, $40) | - |
| 4 | L7 C39 | room 6 at ($10, $74) | - |
| 5 | L2 C35 (tile $19) | room 1 at ($58, $66) | room 6 cleared, lantern L3 C28 or L3 C38 taken |

Entered from room 1 (trapdoor), room 4 (marker 2) and room 6 (marker 2).

## Room 6: the temple

![Room 6](images/rooms/room06.png)

A blue room with a big temple building, a striped wall at the left and a moving purple column at the right.
**Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_06`](../src/room_maps_05_09.asm#L54) [`$70DD`](reference/modules/room_maps_05_09.md#room_map_06), 330 bytes |
| Colours | fill $FC, charset $38, [`room_palette_r4_6`](../src/room_palettes.asm#L33), no split |
| Start A / B | $86, $B3 / $81, $72 |
| Enemies | yes; Ninja $30 / $30, side $02; Yamo $A0 / $EE, side 0 |
| Lanterns | 8, [`lantern_list_room6`](../src/lantern_lists.asm#L51) [`$4DA2`](reference/modules/lantern_lists.md#lantern_list_room6) |
| Handlers | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none), [`room06_frame`](../src/room_frames_0_7.asm#L519) [`$39AA`](reference/modules/room_frames_0_7.md#room06_frame) |

**Setup.** None.

**Behaviour.** [`room06_frame`](../src/room_frames_0_7.asm#L519) [`$39AA`](reference/modules/room_frames_0_7.md#room06_frame): when room 6 is cleared, one time ([`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a)):
[`open_passage_ledge`](../src/passage_open.asm#L54) [`$3AA0`](reference/modules/passage_open.md#open_passage_ledge) at L5 C1. Then [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps) and [`animate_scrolling_chars`](../src/animated_chars.asm#L12) [`$2C70`](reference/modules/animated_chars.md#animate_scrolling_chars).
**Code.**

Clearing room 6 is the key of the first part of the game: it changes rooms 0, 1, 2 and 5. **Code.**

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L6 C0 | room 5 at ($A0, $80) | **Conclusion:** behind the wall that the passage at L5 C1 opens when room 6 is cleared |
| 3, 4, 5 | none | (rooms 5, 2, 0) | no marker: not used |

Entered from room 9 (marker 4 at ($9D, $C7)) and room 5 (markers 3 and 4).

## Room 7: the orange cave with the lantern rows

![Room 7](images/rooms/room07.png)

An orange cave with two levels of buildings and a long floor at the bottom. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_07`](../src/room_maps_05_09.asm#L101) [`$7227`](reference/modules/room_maps_05_09.md#room_map_07), 234 bytes, 442 cells (rooms.md, section 9) |
| Colours | fill $FF, charset $38, [`room_palette_r7_9`](../src/room_palettes.asm#L35) [`$47D4`](reference/modules/room_palettes.md#room_palette_r7_9), no split |
| Start A / B | $1C, $44 / $1F, $74 |
| Enemies | yes; Ninja $50 / $18, side $02; Yamo $B0 / $C0, side $80 |
| Lanterns | 13, [`lantern_list_room7`](../src/lantern_lists.asm#L57) [`$4DC3`](reference/modules/lantern_lists.md#lantern_list_room7): 5 on line 2, 6 on line 5, 2 on line 9 |
| Handlers | [`room07_init`](../src/room_specific_init.asm#L93) [`$3461`](reference/modules/room_specific_init.md#room07_init), [`room07_frame`](../src/room_frames_0_7.asm#L542) [`$39C3`](reference/modules/room_frames_0_7.md#room07_frame) |

**Setup.** [`room07_init`](../src/room_specific_init.asm#L93) [`$3461`](reference/modules/room_specific_init.md#room07_init): the runner at L11 C5 ([`runner_col`](../src/constants.asm#L69) [`$006E`](reference/variables.md#runner_col) = [`runner_old_col`](../src/constants.asm#L71) [`$0070`](reference/variables.md#runner_old_col) = 5,
[`runner_row`](../src/constants.asm#L70) [`$006F`](reference/variables.md#runner_row) = 11); slider 0 at L4 C34 with [`slider_timer`](../src/constants.asm#L74) = $FF.

**Behaviour.** [`room07_frame`](../src/room_frames_0_7.asm#L542) [`$39C3`](reference/modules/room_frames_0_7.md#room07_frame), every pass. **Observed** (coverage) except the second passage and the left
runner.

1. [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps).
2. The 5 lanterns of line 2 taken, one time ([`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a)): [`open_passage_ledge`](../src/passage_open.asm#L54) [`$3AA0`](reference/modules/passage_open.md#open_passage_ledge) at L2 C33, and
   the handler returns for this pass.
3. The 6 lanterns of line 5 taken, one time ([`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b)): [`open_passage_ledge`](../src/passage_open.asm#L54) at L5 C38, and return.
4. Slider 0 at L4 C34-36 (look B).
5. The runner of line 11: right (C5-35) while lantern L9 C2 ([`lantern_list_room7+$2C`](../src/lantern_lists.asm#L57) [`$4DEF`](reference/modules/lantern_lists.md#lantern_list_room7)) or L9 C3
   ([`lantern_list_room7+$30`](../src/lantern_lists.asm#L57) [`$4DF3`](reference/modules/lantern_lists.md#lantern_list_room7)) is present; left (C36-5) when both are taken ([`room07_frame_runner_left`](../src/room_frames_0_7.asm#L614) [`$3A51`](reference/modules/room_frames_0_7.md#room07_frame_runner_left)
   ).

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L6 C39 | room 8 at ($0F, $46) | **Conclusion:** reached through the passage at L5 C38 |
| 4 | L10 C39 | room 8 at ($10, $C0) | - |
| 2, 5 | none | (room 0) | no marker: not used |

Entered from room 4 (marker 3) and room 8 (markers 2 and 4).

## Room 8: the twin columns

![Room 8](images/rooms/room08.png)

An orange cave with two moving purple columns. Enemy-free. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_08`](../src/room_maps_05_09.asm#L134) [`$7311`](reference/modules/room_maps_05_09.md#room_map_08), 384 bytes |
| Colours | fill $FA, charset $38, [`room_palette_r7_9`](../src/room_palettes.asm#L35), no split |
| Start A / B | $14, $46 / 0, 0 |
| Enemies | none |
| Lanterns | 4, [`lantern_list_room8`](../src/lantern_lists.asm#L65) [`$4DF8`](reference/modules/lantern_lists.md#lantern_list_room8): L3 C15, L3 C24, L7 C6 (+8), L7 C33 (+12) |
| Handlers | [`room08_init`](../src/room_specific_init.asm#L107) [`$3478`](reference/modules/room_specific_init.md#room08_init), [`room08_frame`](../src/room_frames_8_11.asm#L16) [`$3AD4`](reference/modules/room_frames_8_11.md#room08_frame) |

**Setup.** [`room08_init`](../src/room_specific_init.asm#L107) [`$3478`](reference/modules/room_specific_init.md#room08_init): slider 0 at L5 C6 (timer $FF), slider 1 at L5 C27 (timer $F2).

**Behaviour.** [`room08_frame`](../src/room_frames_8_11.asm#L16) [`$3AD4`](reference/modules/room_frames_8_11.md#room08_frame): five one-shot events, the sliders 0 (L5 C6-11) and 1 (L5 C27-32), then
[`animate_scrolling_chars`](../src/animated_chars.asm#L12). **Code**; the events never ran in the coverage.

| Event | Flag | Condition | Action |
|---|---|---|---|
| 1 | [`room_state_c`](../src/room_dispatch.asm#L11) [`$4E99`](reference/modules/room_dispatch.md#room_state_c) | room 7 cleared and lantern L7 C6 ([`lantern_list_room8+8`](../src/lantern_lists.asm#L65) [`$4E00`](reference/modules/lantern_lists.md#lantern_list_room8)) taken | [`open_passage`](../src/passage_open.asm#L42) at L7 C14 |
| 2 | [`room_state_d`](../src/room_dispatch.asm#L13) [`$4E9A`](reference/modules/room_dispatch.md#room_state_d) | lanterns L3 C15 and L3 C24 taken | if lantern L7 C33 ([`lantern_list_room8+$C`](../src/lantern_lists.asm#L65) [`$4E04`](reference/modules/lantern_lists.md#lantern_list_room8)) is present: [`anim_chars_direction`](../src/constants.asm#L64) = 1, speed curve restart; [`open_passage`](../src/passage_open.asm#L42) at L7 C25 |
| 3 | [`room_state_e`](../src/room_dispatch.asm#L15) [`$4E9B`](reference/modules/room_dispatch.md#room_state_e) | room 8 cleared and room 9 lanterns L10 C27 ([`lantern_list_room9+8`](../src/lantern_lists.asm#L69) [`$4E11`](reference/modules/lantern_lists.md#lantern_list_room9)) and L10 C28 ([`lantern_list_room9+$C`](../src/lantern_lists.asm#L69) [`$4E15`](reference/modules/lantern_lists.md#lantern_list_room9)) taken | [`open_passage_ledge_b`](../src/passage_open.asm#L61) [`$3AAA`](reference/modules/passage_open.md#open_passage_ledge_b) at L2 C38 |
| 4 | [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) | lantern L7 C6 taken | [`open_passage`](../src/passage_open.asm#L42) at L10 C1 |
| 5 | [`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b) | rooms 7 and 8 cleared | [`open_passage`](../src/passage_open.asm#L42) at L10 C38 |

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L3 C0 | room 7 at ($A0, $74) | - |
| 3 | L3 C39 | room 9 at ($10, $53) | **Conclusion:** reached through the passage at L2 C38 (event 3) |
| 4 | L11 C0 | room 7 at ($A1, $B5) | **Conclusion:** reached through the passage at L10 C1 (event 4) |
| 5 | L11 C39 | room 9 at ($0F, $C6) | **Conclusion:** reached through the passage at L10 C38 (event 5) |

Entered from room 7 (markers 3 and 4) and room 9 (markers 2 and 3).

## Room 9: the slopes

![Room 9](images/rooms/room09.png)

An orange cave with purple slopes and a moving column at the right. Enemy-free. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_09`](../src/room_maps_05_09.asm#L185) [`$7491`](reference/modules/room_maps_05_09.md#room_map_09), 327 bytes |
| Colours | fill $FA, charset $38, [`room_palette_r7_9`](../src/room_palettes.asm#L35), no split |
| Start A / B | $12, $C6 / 0, 0 |
| Enemies | none |
| Lanterns | 5, [`lantern_list_room9`](../src/lantern_lists.asm#L69) [`$4E09`](reference/modules/lantern_lists.md#lantern_list_room9): L2 C32, L7 C15 (+4), L10 C27 (+8), L10 C28 (+12), L10 C32 |
| Handlers | [`room09_init`](../src/room_specific_init.asm#L123) [`$348F`](reference/modules/room_specific_init.md#room09_init), [`room09_frame`](../src/room_frames_8_11.asm#L149) [`$3BB2`](reference/modules/room_frames_8_11.md#room09_frame) |

**Setup.** [`room09_init`](../src/room_specific_init.asm#L123) [`$348F`](reference/modules/room_specific_init.md#room09_init): colour RAM $FA for L2 C35-38 (where tile $18 appears later); the runner at L12
C4; slider 0 at L5 C16 (timer $FC), slider 1 at L6 C16 (timer $FF).

**Behaviour.** [`room09_frame`](../src/room_frames_8_11.asm#L149) [`$3BB2`](reference/modules/room_frames_8_11.md#room09_frame). **Code**; the events never ran in the coverage, the right runner and the
sliders did (**Observed**).

| Event | Flag | Condition | Action |
|---|---|---|---|
| 1 | [`room_state_c`](../src/room_dispatch.asm#L11) [`$4E99`](reference/modules/room_dispatch.md#room_state_c) | lantern L2 C32 ([`lantern_list_room9`](../src/lantern_lists.asm#L69) [`$4E09`](reference/modules/lantern_lists.md#lantern_list_room9)) taken | [`anim_chars_direction`](../src/constants.asm#L64) = 1, speed curve restart |
| 2 | [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) | lantern L7 C15 ([`lantern_list_room9+4`](../src/lantern_lists.asm#L69) [`$4E0D`](reference/modules/lantern_lists.md#lantern_list_room9)) taken | [`open_passage`](../src/passage_open.asm#L42) at L7 C23; direction 0, restart |
| 3 | [`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b) | room 9 cleared | direction 0, restart; sound $8A; tile $18 (codes $61 $04 $04 $63) at L2 C35 |

Then the runner of line 12 (right C4-24 while lantern L10 C27 or L10 C28 is present, else left), slider 0 (L5
C16-20) and slider 1 (L6 C16-20), both look B, and [`animate_scrolling_chars`](../src/animated_chars.asm#L12).

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L4 C0 | room 8 at ($A0, $47) | - |
| 3 | L11 C0 | room 8 at ($A0, $C0) | - |
| 4 | L2 C36-37 (tile $18) | room 6 at ($9D, $C7) | room 9 cleared |

Entered from room 8 (markers 3 and 5).

## Room 10: the castle hall

![Room 10](images/rooms/room10.png)

A grey castle hall with three floors. The screenshot shows Yamo (green) and the Ninja (black). **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_10`](../src/room_maps_10_14.asm#L9) [`$75D8`](reference/modules/room_maps_10_14.md#room_map_10), 372 bytes, 442 cells (rooms.md, section 9) |
| Colours | fill $F9, charset $3A ([`charset_rooms_10_19`](../src/constants.asm#L205) [`$A800`](reference/variables.md#charset_rooms_10_19)), [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37) [`$47D7`](reference/modules/room_palettes.md#room_palette_r10_12_14_16), split $56 |
| Start A / B | $34, $8C / $96, $5C |
| Enemies | yes; Ninja $08 / $0C, side $02; Yamo $30 / $30, side $80 |
| Lanterns | 3, [`lantern_list_room10`](../src/lantern_lists.asm#L73) [`$4E1E`](reference/modules/lantern_lists.md#lantern_list_room10): L4 C1, L7 C30 (+4), L10 C30 |
| Handlers | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none), [`room10_frame`](../src/room_frames_8_11.asm#L278) [`$3C90`](reference/modules/room_frames_8_11.md#room10_frame) |

**Setup.** None.

**Behaviour.** [`room10_frame`](../src/room_frames_8_11.asm#L278) [`$3C90`](reference/modules/room_frames_8_11.md#room10_frame):

1. Lanterns L4 C1 and L7 C30 taken, one time ([`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a)): [`open_passage_dark`](../src/passage_open.asm#L69) [`$3AB4`](reference/modules/passage_open.md#open_passage_dark) at L4 C38.
2. Copy protection ([`room10_frame_protection_check`](../src/room_frames_8_11.asm#L289) [`$3CA7`](reference/modules/room_frames_8_11.md#room10_frame_protection_check)): when [`D6510`](../src/constants.asm#L11) [`$0000`](reference/variables.md#D6510) is not $EF, it writes $80 to the
   first byte of [`room_map_00`](../src/room_maps_00_04.asm#L18) [`$68F9`](reference/modules/room_maps_00_04.md#room_map_00), [`room_map_05`](../src/room_maps_05_09.asm#L7) [`$6F82`](reference/modules/room_maps_05_09.md#room_map_05) and [`room_map_01`](../src/room_maps_00_04.asm#L55) [`$6A09`](reference/modules/room_maps_00_04.md#room_map_01) (those rooms then draw
   empty) and jumps to [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen). **Observed** (coverage: passed).
3. [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps).

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 | room 3 at ($A0, $C4) | - |
| 3 | L5 C39 | room 11 at ($10, $C4) | **Conclusion:** reached through the passage at L4 C38 |

Entered from room 3 (trapdoor) and room 11 (marker 2).

## Room 11: the three pits

![Room 11](images/rooms/room11.png)

A purple room with a climbing column at the left and three pits in the middle. Enemy-free. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_11`](../src/room_maps_10_14.asm#L59) [`$774C`](reference/modules/room_maps_10_14.md#room_map_11), 247 bytes |
| Colours | fill $FB, charset $3A, [`room_palette_r11`](../src/room_palettes.asm#L40) [`$47DD`](reference/modules/room_palettes.md#room_palette_r11), no split |
| Start A / B | $40, $4C / 0, 0 |
| Enemies | none |
| Lanterns | 3, [`lantern_list_room11`](../src/lantern_lists.asm#L76) [`$4E2B`](reference/modules/lantern_lists.md#lantern_list_room11): L3 C18, L3 C21, L10 C7 (+8) |
| Handlers | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none), [`room11_frame`](../src/room_frames_8_11.asm#L318) [`$3CC0`](reference/modules/room_frames_8_11.md#room11_frame) |

**Setup.** None. But [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) has a rule for room 11: when rooms 12, 14 and 16 are cleared, it sends
Bruce to the start of room 13 instead ([`place_bruce_at_room_start`](../src/room_misc_support.asm#L11) [`$3217`](reference/modules/room_misc_support.md#place_bruce_at_room_start) with X = 13). **Code**; never executed in
the coverage.

**Behaviour.** [`room11_frame`](../src/room_frames_8_11.asm#L318) [`$3CC0`](reference/modules/room_frames_8_11.md#room11_frame): lantern L10 C7 ([`lantern_list_room11+8`](../src/lantern_lists.asm#L76) [`$4E33`](reference/modules/lantern_lists.md#lantern_list_room11)) taken, one time
([`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a)): [`anim_chars_direction`](../src/constants.asm#L64) = 0, speed curve restart. Then [`update_burst_traps`](../src/room_misc_support.asm#L33) and
[`animate_scrolling_chars`](../src/animated_chars.asm#L12). **Code.**

**Links.** In room 11 [`check_exit_edge`](../src/touch_effects.asm#L154) [`$30D4`](reference/modules/touch_effects.md#check_exit_edge) allows an exit anywhere, so the three pits of line 7 are exits.

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 | room 10 at ($A0, $5A) | - |
| 3 | L7 C9-12 (left pit) | room 12 at ($10, $5C) | - |
| 4 | L7 C18-21 (middle pit) | room 14 at ($10, $5E) | - |
| 5 | L7 C27-30 (right pit) | room 16 at ($10, $5C) | - |
| - | room entry | room 13 | rooms 12, 14, 16 cleared |

Entered from room 10 (marker 3), room 12 (marker 3), room 14 (marker 3) and room 16 (marker 3).

## Room 12: the hall with the ramps

![Room 12](images/rooms/room12.png)

A grey hall with three floors and blue ramps. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_12`](../src/room_maps_10_14.asm#L93) [`$7843`](reference/modules/room_maps_10_14.md#room_map_12), 387 bytes |
| Colours | fill $F9, charset $3A, [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37), split $56 |
| Start A / B | $18, $5C / $70, $5C |
| Enemies | yes; Ninja $04 / $04, side $80; Yamo $20 / $20, side $80 |
| Lanterns | 3, [`lantern_list_room12`](../src/lantern_lists.asm#L79) [`$4E38`](reference/modules/lantern_lists.md#lantern_list_room12): L4 C36, L7 C36, L10 C36 (+8) |
| Handlers | [`room12_init`](../src/room_specific_init.asm#L149) [`$34BD`](reference/modules/room_specific_init.md#room12_init), [`room12_frame`](../src/room_frames_12_17.asm#L11) [`$3E4C`](reference/modules/room_frames_12_17.md#room12_frame) |

**Setup.** [`room12_init`](../src/room_specific_init.asm#L149) [`$34BD`](reference/modules/room_specific_init.md#room12_init): [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) = 1, so the first passage is drawn on two passes.

**Behaviour.** [`room12_frame`](../src/room_frames_12_17.asm#L11) [`$3E4C`](reference/modules/room_frames_12_17.md#room12_frame). **Code.**

1. Lantern L10 C36 ([`lantern_list_room12+8`](../src/lantern_lists.asm#L79) [`$4E40`](reference/modules/lantern_lists.md#lantern_list_room12)) taken ([`room_state_a`](../src/room_dispatch.asm#L7)): [`open_passage_dark`](../src/passage_open.asm#L69) [`$3AB4`](reference/modules/passage_open.md#open_passage_dark) at L10 C38.
2. Room 12 cleared and the room 14 lanterns L10 C9 ([`lantern_list_room14+8`](../src/lantern_lists.asm#L84) [`$4E52`](reference/modules/lantern_lists.md#lantern_list_room14)) and L10 C30
   ([`lantern_list_room14+$C`](../src/lantern_lists.asm#L84) [`$4E56`](reference/modules/lantern_lists.md#lantern_list_room14)) taken, one time ([`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b)): [`open_passage_dark`](../src/passage_open.asm#L69) at L7 C38.
3. [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps).

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L8 C39 | room 11 at ($34, $BE) | **Conclusion:** reached through the passage at L7 C38 |
| 4 | L11 C39 | room 14 at ($10, $BE) | **Conclusion:** reached through the passage at L10 C38 |

Entered from room 11 (left pit) and room 14 (marker 4).

## Room 13: the falling room

![Room 13](images/rooms/room13.png)

A blue room with four long floors. Bruce falls through it from the top. Enemy-free; no lanterns. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_13`](../src/room_maps_10_14.asm#L147) [`$79C6`](reference/modules/room_maps_10_14.md#room_map_13), 128 bytes, 442 cells (rooms.md, section 9) |
| Colours | fill $FA, charset $3A, [`room_palette_r13`](../src/room_palettes.asm#L42) [`$47E0`](reference/modules/room_palettes.md#room_palette_r13), no split |
| Start A / B | $98, $32 / 0, 0 |
| Enemies | none (the delay columns hold values, but the flag disables them) |
| Lanterns | 0, [`lantern_list_room13`](../src/lantern_lists.asm#L82) [`$4E45`](reference/modules/lantern_lists.md#lantern_list_room13) (dummy record) |
| Handlers | [`room13_init`](../src/room_specific_init.asm#L159) [`$34C3`](reference/modules/room_specific_init.md#room13_init), [`room13_frame`](../src/room_frames_12_17.asm#L41) [`$3E7C`](reference/modules/room_frames_12_17.md#room13_frame) |

**Setup.** [`room13_init`](../src/room_specific_init.asm#L159) [`$34C3`](reference/modules/room_specific_init.md#room13_init) fills the floor mover slots (rooms.md, section 8.2). Several values depend on
[`game_loop_count`](../src/constants.asm#L34) [`$0040`](reference/variables.md#game_loop_count). [`actor_calc_tile_pos`](../src/game_main_loop.asm#L91) [`$1C39`](reference/modules/game_main_loop.md#actor_calc_tile_pos) adds 4 to the Y of the actors in room 13 before it computes
the line. **Code.**

**Behaviour.** [`room13_frame`](../src/room_frames_12_17.asm#L41) [`$3E7C`](reference/modules/room_frames_12_17.md#room13_frame), every pass. **Observed** (coverage: the lowest band and the movers ran).

1. X = [`current_player`](../src/constants.asm#L14) [`$0003`](reference/variables.md#current_player) * 4. Bruce's [`actor_y`](../src/constants.asm#L95) [`$00A1`](reference/variables.md#actor_y) selects a band: $64-$89 band 0, $8A-$B5 band 1,
   $B6 or more band 2. Above $64 nothing.
2. When [`room13_band_bonus`](../src/constants.asm#L149) [`$014B`](reference/variables.md#room13_band_bonus) + X + band is 1, it becomes 0 and the player gets 500 points ([`add_score`](../src/score.asm#L52) [`$3175`](reference/modules/score.md#add_score) with
   $01 at byte 1 and $F4 at byte 2). The pass ends there.
3. Else: [`update_floor_movers`](../src/game_setup.asm#L169) [`$104B`](reference/modules/game_setup.md#update_floor_movers) on even passes, and only sprites 0 and 1 (Bruce) stay on.

~~~mermaid
stateDiagram-v2
  state "Bonus there (flag 1)" as There
  state "Bonus given (flag 0)" as Given
  [*] --> There: init_game_variables $0F72
  There --> Given: Bruce Y in the band, +500
  Given --> There: room19_frame $4272 (next game loop)
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Bonus there | [`actor_y`](../src/constants.asm#L95) in the band of the flag | Bonus given, 500 points | [`room13_frame_award_bonus`](../src/room_frames_12_17.asm#L70) [`$3EAF`](reference/modules/room_frames_12_17.md#room13_frame_award_bonus) |
| Bonus given | [`room19_frame`](../src/ending_room.asm#L27) starts the next game loop | Bonus there (4 flags of the current player = 1) | [`room19_frame_rearm_loop`](../src/ending_room.asm#L39) [`$4283`](reference/modules/ending_room.md#room19_frame_rearm_loop) |

Each player has 4 flags (`$014B-$014E` and `$014F-$0152`); room 13 uses 3. **Code.**

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C39 | room 15 at ($10, $C3) | - |
| - | entry | from room 11 at start A ($98, $32) | rooms 12, 14, 16 cleared |

Entered from room 11 (the [`draw_room`](../src/draw_room.asm#L28) rule) and from room 15 (marker 2 at ($A0, $C4)).

## Room 14: the hall with the two ramps

![Room 14](images/rooms/room14.png)

A grey hall with blue ramps at both sides. The screenshot shows Yamo fighting Bruce. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_14`](../src/room_maps_10_14.asm#L166) [`$7A46`](reference/modules/room_maps_10_14.md#room_map_14), 366 bytes |
| Colours | fill $F9, charset $3A, [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37), split $56 |
| Start A / B | $18, $5C / $92, $BE |
| Enemies | yes; Ninja $08 / $08, side $02; Yamo $20 / $30, side 0 |
| Lanterns | 4, [`lantern_list_room14`](../src/lantern_lists.asm#L84) [`$4E4A`](reference/modules/lantern_lists.md#lantern_list_room14): L7 C9, L7 C30 (+4), L10 C9 (+8), L10 C30 (+12) |
| Handlers | [`room14_init`](../src/room_specific_init.asm#L249) [`$358D`](reference/modules/room_specific_init.md#room14_init), [`room14_frame`](../src/room_frames_12_17.asm#L88) [`$3ECC`](reference/modules/room_frames_12_17.md#room14_frame) |

**Setup.** [`room14_init`](../src/room_specific_init.asm#L249) [`$358D`](reference/modules/room_specific_init.md#room14_init): [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) = 1 (the passage is drawn on two passes).

**Behaviour.** [`room14_frame`](../src/room_frames_12_17.asm#L88) [`$3ECC`](reference/modules/room_frames_12_17.md#room14_frame): lanterns L7 C9 and L7 C30 taken ([`room_state_a`](../src/room_dispatch.asm#L7)): [`open_passage_dark`](../src/passage_open.asm#L69) [`$3AB4`](reference/modules/passage_open.md#open_passage_dark)
at L4 C38. Then [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps). **Code.**

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L5 C39 | room 11 at ($50, $BE) | **Conclusion:** reached through the passage at L4 C38 |
| 4 | L11 C0 | room 12 at ($A0, $BE) | - |
| 5 | L11 C39 | room 16 at ($10, $BE) | - |

Entered from room 11 (middle pit), room 12 (marker 4) and room 16 (marker 4). The lanterns of line 10 also open a
passage in room 12.

## Room 15: the tower

![Room 15](images/rooms/room15.png)

A dark tower with ladders in the middle, under a blue sky, with a stone wall and a white fence. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_15`](../src/room_maps_15_19.asm#L7) [`$7BB4`](reference/modules/room_maps_15_19.md#room_map_15), 168 bytes |
| Colours | fill $FC, charset $3A, [`room_palette_r15`](../src/room_palettes.asm#L44) [`$47E3`](reference/modules/room_palettes.md#room_palette_r15), splits $B6, $C7 (3 bands) |
| Start A / B | $1C, $C3 / $7A, $C4 |
| Enemies | yes; Ninja $08 / $08, side 0; Yamo $30 / $50, side 0 |
| Lanterns | 6, [`lantern_list_room15`](../src/lantern_lists.asm#L88) [`$4E5B`](reference/modules/lantern_lists.md#lantern_list_room15): L3 C19, L3 C21 (+4), L4 C14 (+8), L4 C26, L6 C13 (+16), L6 C27 |
| Handlers | [`room15_init`](../src/room_specific_init.asm#L255) [`$3593`](reference/modules/room_specific_init.md#room15_init), [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame) |

**Setup.** [`room15_init`](../src/room_specific_init.asm#L255) [`$3593`](reference/modules/room_specific_init.md#room15_init): [`room_state_a`](../src/room_dispatch.asm#L7), [`room_state_b`](../src/room_dispatch.asm#L9), [`room_state_c`](../src/room_dispatch.asm#L11) = 1 (each opening is drawn on two
passes).

**Behaviour.** [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame), three events. **Code.**

| Event | Flag | Condition | Action |
|---|---|---|---|
| 1 | [`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a) | lantern L3 C19 ([`lantern_list_room15`](../src/lantern_lists.asm#L88) [`$4E5B`](reference/modules/lantern_lists.md#lantern_list_room15)) taken | tile $57 (blank) at L3 C17, tile $58 (code $2F) at L4 C17, sound $8A |
| 2 | [`room_state_b`](../src/room_dispatch.asm#L9) [`$4E98`](reference/modules/room_dispatch.md#room_state_b) | lanterns L3 C21, L4 C14 and L6 C13 ([`lantern_list_room15+4`](../src/lantern_lists.asm#L88) [`$4E5F`](reference/modules/lantern_lists.md#lantern_list_room15), `+8` `$4E63`, `+$10` `$4E6B`) taken | tiles $57 / $58 at L3 / L4 C23, sound $8A |
| 3 | [`room_state_c`](../src/room_dispatch.asm#L11) [`$4E99`](reference/modules/room_dispatch.md#room_state_c) | room 15 cleared | tile $59 (codes $2F) at L9 C37, tiles $5A and $5B (codes $00 $00 $03) at L8 and L7 C37, sound $8A |

Events 1 and 2 open the walls of the tower (code $45 at C17, code $43 at C23) at line 3 and lay a floor cell at
line 4. Event 3 removes the right wall at C39 and puts exit marker 3 at L7 C39 and L8 C39. **Code** (map cells).

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 | room 13 at ($A0, $C4) | - |
| 3 | L7-8 C39 (tiles $5A, $5B) | room 17 at ($10, $B3) | room 15 cleared |

Entered from room 13 (marker 2) and room 17 (marker 2).

## Room 16: the hall with the extra fall

![Room 16](images/rooms/room16.png)

A grey hall with three floors. The yellow item at the right of the lowest floor is the extra fall. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_16`](../src/room_maps_15_19.asm#L31) [`$7C5C`](reference/modules/room_maps_15_19.md#room_map_16), 305 bytes |
| Colours | fill $F9, charset $3A, [`room_palette_r10_12_14_16`](../src/room_palettes.asm#L37), split $56 |
| Start A / B | $18, $5C / $81, $8E |
| Enemies | yes; Ninja $08 / $08, side $80; Yamo $20 / $30, side $02 |
| Lanterns | 2, [`lantern_list_room16`](../src/lantern_lists.asm#L93) [`$4E74`](reference/modules/lantern_lists.md#lantern_list_room16): L4 C32, L7 C5 |
| Handlers | [`room16_init`](../src/room_specific_init.asm#L264) [`$359F`](reference/modules/room_specific_init.md#room16_init), [`room16_frame`](../src/room_frames_12_17.asm#L166) [`$3F5B`](reference/modules/room_frames_12_17.md#room16_frame) |

**Setup.** [`room16_init`](../src/room_specific_init.asm#L264) [`$359F`](reference/modules/room_specific_init.md#room16_init): colour RAM $FF for the extra-fall item (screen rows 19-22, columns 36-37). When
[`extra_fall_pickups_left`](../src/lantern_lists.asm#L109) [`$4E95`](reference/modules/lantern_lists.md#extra_fall_pickups_left) + [`current_player`](../src/constants.asm#L14) is 0, it erases the item ([`draw_room16_bonus_taken`](../src/touch_effects.asm#L26) [`$2FEF`](reference/modules/touch_effects.md#draw_room16_bonus_taken)).
**Code.**

**Behaviour.** [`room16_frame`](../src/room_frames_12_17.asm#L166) [`$3F5B`](reference/modules/room_frames_12_17.md#room16_frame): room 16 cleared, one time ([`room_state_a`](../src/room_dispatch.asm#L7) [`$4E97`](reference/modules/room_dispatch.md#room_state_a)): [`open_passage_dark`](../src/passage_open.asm#L69) [`$3AB4`](reference/modules/passage_open.md#open_passage_dark)
at L7 C1. Then [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps). **Code.**

**The extra fall.** [`handle_touched_tile`](../src/background_touch.asm#L61) [`$2E89`](reference/modules/background_touch.md#handle_touched_tile) sends codes $2D and $2E in room 16 to [`collect_room16_bonus`](../src/touch_effects.asm#L8) [`$2FD6`](reference/modules/touch_effects.md#collect_room16_bonus):
only Bruce, and only at [`actor_y`](../src/constants.asm#L95) $A0 or more. It decrements [`extra_fall_pickups_left`](../src/lantern_lists.asm#L109) + player (5 at a game start),
adds one fall to [`falls_left`](../src/constants.asm#L31) [`$0028`](reference/variables.md#falls_left), plays sound $8E and erases the item. The map draws the item again at the next visit
while the count is not 0, so a player can take it up to 5 times. **Code**; never executed in the coverage.

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 3 | L8 C0 | room 11 at ($80, $BE) | **Conclusion:** reached through the passage at L7 C1 |
| 4 | L11 C0 | room 14 at ($A0, $BE) | - |

Entered from room 11 (right pit) and room 14 (marker 5).

## Room 17: the hall of sliders

![Room 17](images/rooms/room17.png)

A grey and yellow room with orange floors, three long slider tracks and pillars. Enemy-free. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_17`](../src/room_maps_15_19.asm#L75) [`$7D8D`](reference/modules/room_maps_15_19.md#room_map_17), 259 bytes, 442 cells (rooms.md, section 9) |
| Colours | fill $FF, charset $3A, [`room_palette_r17`](../src/room_palettes.asm#L48) [`$47EC`](reference/modules/room_palettes.md#room_palette_r17), no split |
| Start A / B | $18, $B4 / 0, 0 |
| Enemies | none |
| Lanterns | 2, [`lantern_list_room17`](../src/lantern_lists.asm#L96) [`$4E7D`](reference/modules/lantern_lists.md#lantern_list_room17): L10 C38, L11 C31 (+4) |
| Handlers | [`room17_init`](../src/room_specific_init.asm#L284) [`$35C4`](reference/modules/room_specific_init.md#room17_init), [`room17_frame`](../src/room_frames_12_17.asm#L188) [`$3F71`](reference/modules/room_frames_12_17.md#room17_frame) |

**Setup.** [`room17_init`](../src/room_specific_init.asm#L284) [`$35C4`](reference/modules/room_specific_init.md#room17_init): colour RAM $FF at screen row 19, column 38 (the lantern L10 C38);
[`room_state_a`](../src/room_dispatch.asm#L7) and [`room_state_b`](../src/room_dispatch.asm#L9) = 1; the runner at L5 C11; sliders 0, 1, 2 at L3, L7, L9, column 8, with
[`slider_timer`](../src/constants.asm#L74) = $F8, $F1, $EA.

**Behaviour.** [`room17_frame`](../src/room_frames_12_17.asm#L188) [`$3F71`](reference/modules/room_frames_12_17.md#room17_frame), every pass. **Observed** (coverage) except the two lantern events.

1. [`room_state_c`](../src/room_dispatch.asm#L11) [`$4E99`](reference/modules/room_dispatch.md#room_state_c) counts 11 passes. Then the colour RAM of screen row 3, columns 8-35, toggles bit 1 of its
   colour ([`room17_frame_colour_loop`](../src/room_frames_12_17.asm#L198) [`$3F86`](reference/modules/room_frames_12_17.md#room17_frame_colour_loop)).
2. The runner of line 5 moves right on every second pass ([`room_state_d`](../src/room_dispatch.asm#L13) [`$4E9A`](reference/modules/room_dispatch.md#room_state_d)), C11-27.
3. Lantern L10 C38 ([`lantern_list_room17`](../src/lantern_lists.asm#L96) [`$4E7D`](reference/modules/lantern_lists.md#lantern_list_room17)) taken, one time ([`room_state_a`](../src/room_dispatch.asm#L7), test `beq`): tile $5D (codes $44
   $44) at L10 C37.
4. Lantern L11 C31 ([`lantern_list_room17+4`](../src/lantern_lists.asm#L96) [`$4E81`](reference/modules/lantern_lists.md#lantern_list_room17)) taken, one time ([`room_state_b`](../src/room_dispatch.asm#L9)): tile $5C (codes $49 $49 $49)
   at L10 C24. It fills the gap of line 10 between the code $49 cells at C23 and C27. **Code** (map cells).
5. [`update_burst_traps`](../src/room_misc_support.asm#L33) [`$3228`](reference/modules/room_misc_support.md#update_burst_traps).
6. The three sliders in one loop (rooms.md, section 8.1).

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
| Step | [`room_state_d`](../src/room_dispatch.asm#L13) - 1 is negative | [`room_state_d`](../src/room_dispatch.asm#L13) = 1, runner one column right | [`room17_frame_runner_rearm`](../src/room_frames_12_17.asm#L207) [`$3F93`](reference/modules/room_frames_12_17.md#room17_frame_runner_rearm) |
| Skip | [`room_state_d`](../src/room_dispatch.asm#L13) - 1 = 0 | no move | [`room17_frame_runner`](../src/room_frames_12_17.asm#L203) [`$3F8C`](reference/modules/room_frames_12_17.md#room17_frame_runner) |

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L10 C0 | room 15 at ($A0, $93) | - |
| 3 | L3 C39 | room 18 at ($10, $C6) | - |

Entered from room 15 (marker 3) and room 18 (marker 2, until the wizard is defeated).

## Room 18: the wizard

![Room 18](images/rooms/room18.png)

The wizard's face fills the top of the room above a purple platform. Bruce enters at the bottom left. Enemy-free;
two fireballs fall from the wizard. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_18`](../src/room_maps_15_19.asm#L113) [`$7E90`](reference/modules/room_maps_15_19.md#room_map_18), 336 bytes, 442 cells (rooms.md, section 9) |
| Colours | fill $FE, charset $3C ([`charset_wizard`](../src/constants.asm#L206) [`$B000`](reference/variables.md#charset_wizard)), [`room_palette_r18`](../src/room_palettes.asm#L50) [`$47EF`](reference/modules/room_palettes.md#room_palette_r18), no split |
| Start A / B | $18, $C6 / 0, 0 |
| Enemies | none |
| Lanterns | 1, [`lantern_list_room18`](../src/lantern_lists.asm#L99) [`$4E86`](reference/modules/lantern_lists.md#lantern_list_room18): L11 C37 |
| Handlers | [`room18_init`](../src/room_specific_init.asm#L317) [`$35FA`](reference/modules/room_specific_init.md#room18_init), [`room18_frame`](../src/wizard_room.asm#L13) [`$3CDC`](reference/modules/wizard_room.md#room18_frame) |

**Setup.** [`room18_init`](../src/room_specific_init.asm#L317) [`$35FA`](reference/modules/room_specific_init.md#room18_init): colour RAM $FE for the whole play area; clears the fireball sprite data
`$8340-$83BF`; no Y expansion and X expansion for all 8 sprites; [`room_state_a`](../src/room_dispatch.asm#L7) = 1 (wizard present), [`room_state_b`](../src/room_dispatch.asm#L9)
= 1 (animation timer); [`fireball_active`](../src/fireball_text_score_vars.asm#L8) [`$432E`](reference/modules/fireball_text_score_vars.md#fireball_active) = 0, 0; [`fireball_respawn_delay`](../src/fireball_text_score_vars.asm#L12) [`$4330`](reference/modules/fireball_text_score_vars.md#fireball_respawn_delay) = 0 and $10;
[`fireball_unused_init`](../src/fireball_text_score_vars.asm#L23) [`$4336`](reference/modules/fireball_text_score_vars.md#fireball_unused_init) = 6, 7 (never read). **Code.**

**Behaviour.** [`room18_frame`](../src/wizard_room.asm#L13) [`$3CDC`](reference/modules/wizard_room.md#room18_frame). Deadly characters do not kill in room 18 ([`touch_deadly_tile`](../src/touch_effects.asm#L75) [`$304B`](reference/modules/touch_effects.md#touch_deadly_tile)
returns). **Code**; the wizard alive ran in the coverage (**Observed**); the defeat ran in a run of the analysis
(**Observed**: the wizard flashes and disappears, score +3000).

1. **Wizard alive** ([`room_state_a`](../src/room_dispatch.asm#L7) = 1, the lantern present): [`update_fireballs`](../src/wizard_fireballs.asm#L13) [`$4133`](reference/modules/wizard_fireballs.md#update_fireballs). When the sprite-sprite
   collision register shows sprite 0 or 1 (Bruce) with sprite 6 or 7 (a fireball), and Bruce is not dying,
   [`set_actor_hazard_death`](../src/room_hazard_draw.asm#L37) [`$407D`](reference/modules/room_hazard_draw.md#set_actor_hazard_death). Every 8 passes ([`room_state_b`](../src/room_dispatch.asm#L9)): the gaze [`room_state_c`](../src/room_dispatch.asm#L11) = 2 when [`actor_x`](../src/constants.asm#L94) [`$009E`](reference/variables.md#actor_x)
   >= $76, 1 when >= $3A, else 0 ([`wizard_face_zone_x`](../src/room_tables.asm#L13) [`$4A89`](reference/modules/room_tables.md#wizard_face_zone_x)); tile $38 + gaze at L2 C16; the face toggles
   ([`room_state_d`](../src/room_dispatch.asm#L13)) between tiles $41/$44 + gaze and $3B/$3E + gaze at L3 / L4 C18 ([`draw_wizard_face_top`](../src/wizard_room.asm#L98) [`$3D81`](reference/modules/wizard_room.md#draw_wizard_face_top),
   [`draw_wizard_face_bottom`](../src/wizard_room.asm#L106) [`$3D8E`](reference/modules/wizard_room.md#draw_wizard_face_bottom)).
2. **Lantern taken** (first pass with the record state 0): [`room_state_a`](../src/room_dispatch.asm#L7) = 0, [`clear_fireball_sprites`](../src/wizard_fireballs.asm#L171) [`$423F`](reference/modules/wizard_fireballs.md#clear_fireball_sprites),
   sprites 5-7 off, tile $61 (code $06) at L11 C0, 3000 points, gaze 1, [`room_state_b`](../src/room_dispatch.asm#L9) = $50.
3. **Defeat sequence** ([`room18_wizard_defeated`](../src/wizard_room.asm#L134) [`$3DAF`](reference/modules/wizard_room.md#room18_wizard_defeated), [`room_state_b`](../src/room_dispatch.asm#L9) passes): random colours on the wizard
   area of colour RAM (colour 0 on the last pass); [`room_vmcsb`](../src/constants.asm#L121) [`$00F2`](reference/variables.md#room_vmcsb) = $3E ([`charset_wizard_flash`](../src/constants.asm#L207) [`$B800`](reference/variables.md#charset_wizard_flash)),
   or $3C at random while more than 16 passes are left; sound $8B; the four wizard parts toggle (tiles $47-$4E).
4. **Wizard gone** ([`room18_wizard_gone`](../src/wizard_room.asm#L115) [`$3D9B`](reference/modules/wizard_room.md#room18_wizard_gone), [`room_state_b`](../src/room_dispatch.asm#L9) = 0), every pass: tile $5E (codes $00 $00 $03) at
   L11 C37 and tile $5F (codes $5A $5A) at L12 C38.

~~~mermaid
stateDiagram-v2
  state "Present (a = 1)" as Present
  state "Defeat sequence (a = 0, b > 0)" as Defeat
  state "Gone (a = 0, b = 0)" as Gone
  [*] --> Present: room18_init $35FA
  Present --> Present: fireballs, face every 8 passes
  Present --> Defeat: lantern L11 C37 taken, +3000
  Defeat --> Defeat: b - 1, flash, sound $8B
  Defeat --> Gone: b = 0
  Gone --> Gone: exit tiles $5E, $5F
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Present | [`lantern_list_room18`](../src/lantern_lists.asm#L99) [`$4E86`](reference/modules/lantern_lists.md#lantern_list_room18) = 1 | Present: [`update_fireballs`](../src/wizard_fireballs.asm#L13), hit test, face | [`room18_frame_fireballs`](../src/wizard_room.asm#L45) [`$3D1D`](reference/modules/wizard_room.md#room18_frame_fireballs) |
| Present | [`lantern_list_room18`](../src/lantern_lists.asm#L99) = 0 | Defeat: [`room_state_a`](../src/room_dispatch.asm#L7) = 0, [`room_state_b`](../src/room_dispatch.asm#L9) = $50, sprites 5-7 off, tile $61 at L11 C0, +3000 | [`room18_frame_wizard_alive`](../src/wizard_room.asm#L18) [`$3CE4`](reference/modules/wizard_room.md#room18_frame_wizard_alive) |
| Defeat | [`room_state_b`](../src/room_dispatch.asm#L9) <> 0 | Defeat: colours, charset flicker, sound $8B, parts, [`room_state_b`](../src/room_dispatch.asm#L9) - 1 | [`room18_wizard_defeated`](../src/wizard_room.asm#L134) [`$3DAF`](reference/modules/wizard_room.md#room18_wizard_defeated) |
| Defeat | [`room_state_b`](../src/room_dispatch.asm#L9) = 0 | Gone | [`room18_wizard_defeated`](../src/wizard_room.asm#L134) |
| Gone | every pass | Gone: tiles $5E, $5F | [`room18_wizard_gone`](../src/wizard_room.asm#L115) [`$3D9B`](reference/modules/wizard_room.md#room18_wizard_gone) |

The last pass of the sequence leaves [`room_vmcsb`](../src/constants.asm#L121) = $3E, so after the defeat the room shows with
[`charset_wizard_flash`](../src/constants.asm#L207) [`$B800`](reference/variables.md#charset_wizard_flash) (the expanded [`room_charset_d`](../src/room_charset_d.asm#L8) [`$9C00`](reference/graphics.md#room_charset_d)). Nothing sets it back until the next
[`draw_room`](../src/draw_room.asm#L28). **Code.**

**Links.**

| Marker | Place | To | Condition |
|---|---|---|---|
| 2 | L11 C0 | room 17 at ($A0, $44) | until the wizard is defeated: tile $61 (code $06) replaces the marker |
| 3 | L11 C39 (tile $5E) | room 19 at ($10, $96) | the defeat sequence is over |
| 4, 5 | lines 2-9, inside the wizard graphics | (entry X 0: room 0 at (0, 0)) | rooms.md, section 10 |

Entered from room 17 (marker 3).

## Room 19: congratulations

![Room 19](images/rooms/room19.png)

A castle of blue and white bricks with arches. The status line is blank and line 0 shows "** CONGRATULATIONS **".
Enemy-free; no lanterns, no exits. **Observed.**

| Table | Value |
|---|---|
| Map | [`room_map_19`](../src/room_maps_15_19.asm#L158) [`$7FE0`](reference/modules/room_maps_15_19.md#room_map_19), 416 bytes |
| Colours | fill $FF, charset $3A, [`room_palette_r19`](../src/room_palettes.asm#L52) [`$47F2`](reference/modules/room_palettes.md#room_palette_r19), no split |
| Start A / B | $12, $95 / 0, 0 |
| Enemies | none |
| Lanterns | 0, [`lantern_list_room19`](../src/lantern_lists.asm#L101) [`$4E8B`](reference/modules/lantern_lists.md#lantern_list_room19) (dummy record) |
| Handlers | [`room19_init`](../src/ending_room.asm#L7) [`$425F`](reference/modules/ending_room.md#room19_init), [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame) |

**Setup.** [`room19_init`](../src/ending_room.asm#L7) [`$425F`](reference/modules/ending_room.md#room19_init): [`title_countdown`](../src/constants.asm#L39) [`$0049`](reference/variables.md#title_countdown) = $0458 frames (the interrupt counts it down: about 22
seconds on PAL); 40 zero bytes in screen row 0 (the status line goes blank).

**Behaviour.** [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame). **Observed** (coverage: both states ran).

~~~mermaid
stateDiagram-v2
  state "Shimmer (countdown <> 0)" as Shimmer
  state "Next game loop" as Next
  [*] --> Shimmer: room19_init $425F
  Shimmer --> Shimmer: random colours, CONGRATULATIONS
  Shimmer --> Next: title_countdown = 0
  Next --> [*]: place_bruce_at_room_start, room 0
~~~

| State | Condition | Next state | Code |
|---|---|---|---|
| Shimmer | [`title_countdown`](../src/constants.asm#L39) <> 0 | Shimmer: a random colour (0-7, multicolour) in colour RAM screen rows 17-24, columns 4-32; tile 4 "** CONGRATULATIONS **" at L0 C10 | [`room19_frame_shimmer`](../src/ending_room.asm#L49) [`$4298`](reference/modules/ending_room.md#room19_frame_shimmer) |
| Shimmer | [`title_countdown`](../src/constants.asm#L39) = 0 | Next game loop | [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame) |
| Next game loop | - | [`game_loop_count`](../src/constants.asm#L34) [`$0040`](reference/variables.md#game_loop_count) + 1; 4 flags of [`room13_band_bonus`](../src/constants.asm#L149) [`$014B`](reference/variables.md#room13_band_bonus) of the current player = 1; [`reset_lantern_counts`](../src/game_setup.asm#L242) [`$10C5`](reference/modules/game_setup.md#reset_lantern_counts); [`reset_all_lanterns`](../src/lantern_pickup.asm#L147) [`$33CA`](reference/modules/lantern_pickup.md#reset_all_lanterns); [`reset_unvisited_rooms`](../src/game_setup.asm#L268) [`$10E0`](reference/modules/game_setup.md#reset_unvisited_rooms); [`place_bruce_at_room_start`](../src/room_misc_support.asm#L11) with X = 0 | [`room19_frame`](../src/ending_room.asm#L27) |

[`reset_unvisited_rooms`](../src/game_setup.asm#L268) marks rooms 1-19 unvisited for the current player, so each first visit gives 2000 points
again. A nonzero [`game_loop_count`](../src/constants.asm#L34) makes both spawn timers 3 in every room and gives the room 13 movers longer
tracks. **Code.**

**Links.** Entered from room 18 (marker 3). Leaves to room 0 (start A).

## Dependencies between rooms

The table lists each condition that a room tests on another room, and the rule of [`draw_room`](../src/draw_room.asm#L28). **Code.**

| Room | Depends on | Condition | Effect | Code |
|---|---|---|---|---|
| 0 | room 6 | cleared | statue mouth at L9 C7 moves | [`room00_frame`](../src/room_frames_0_7.asm#L9) [`$3642`](reference/modules/room_frames_0_7.md#room00_frame) |
| 1 | rooms 0, 1, 2 | cleared | trapdoor opens, marker 3 to room 5 | [`room01_frame`](../src/room_frames_0_7.asm#L42) [`$3679`](reference/modules/room_frames_0_7.md#room01_frame) |
| 1 | room 6 | not cleared | trapdoor can open (cleared: stays closed) | [`room01_frame`](../src/room_frames_0_7.asm#L42) |
| 2 | room 6 | cleared | floor opening, marker 5 to room 3; statue mouth at L9 C33 | [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) |
| 5 | room 6 | cleared, with lantern L3 C28 or L3 C38 of room 5 taken | top opening, marker 5 to room 1 | [`room05_frame`](../src/room_frames_0_7.asm#L378) [`$38AB`](reference/modules/room_frames_0_7.md#room05_frame) |
| 8 | room 7 | cleared, with lantern L7 C6 of room 8 taken | passage at L7 C14 | [`room08_frame`](../src/room_frames_8_11.asm#L16) [`$3AD4`](reference/modules/room_frames_8_11.md#room08_frame) |
| 8 | room 9 | lanterns L10 C27, L10 C28 taken, with room 8 cleared | passage at L2 C38 (to marker 3, room 9) | [`room08_frame`](../src/room_frames_8_11.asm#L16) |
| 8 | room 7 | cleared, with room 8 cleared | passage at L10 C38 (to marker 5, room 9) | [`room08_frame`](../src/room_frames_8_11.asm#L16) |
| 11 | rooms 12, 14, 16 | cleared | entering room 11 leads to room 13 | [`draw_room`](../src/draw_room.asm#L28) [`$09BC`](reference/modules/draw_room.md#draw_room) |
| 12 | room 14 | lanterns L10 C9, L10 C30 taken, with room 12 cleared | passage at L7 C38 (to marker 3, room 11) | [`room12_frame`](../src/room_frames_12_17.asm#L11) [`$3E4C`](reference/modules/room_frames_12_17.md#room12_frame) |
| 13 | room 19 | next game loop | band bonus flags set again | [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame) |
| all | room 19 | next game loop | lanterns, lantern counts and visit flags reset; [`game_loop_count`](../src/constants.asm#L34) + 1 | [`room19_frame`](../src/ending_room.asm#L27) |
| all but 18 | room 18 | - | deadly characters kill everywhere but in room 18 | [`touch_deadly_tile`](../src/touch_effects.asm#L75) [`$304B`](reference/modules/touch_effects.md#touch_deadly_tile) |

**Conclusion.** The order of play that these conditions and the exit tables give (not played through in a run):

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
  R3 -- "3 cleared" --> R10["Room 10"] --> R11["Room 11"]
  R11 --> R12["Room 12"]
  R11 --> R14["Room 14"]
  R11 --> R16["Room 16"]
  R11 -- "12, 14, 16 cleared" --> R13["Room 13"]
  R13 --> R15["Room 15"]
  R15 -- "15 cleared" --> R17["Room 17"] --> R18["Room 18"]
  R18 -- "wizard defeated" --> R19["Room 19"]
  R19 -- "next game loop" --> R0
~~~

The diagram shows the first way into each room. The exit tables of section 2.2 of rooms.md give the ways back.
