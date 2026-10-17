# Bruce Lee: jump tables and dispatch

Every place where the program chooses its next code from data: the CPU vectors, the chain of raster interrupt handlers, the two room RTS tables, the compare chains of the action states and of the keys, the jump tables of the music and effect players, the indirect jumps and the self-modified jumps. Each section gives the location, the index, how the code uses it and all entries with their targets.

## Scope

- Sources: `interrupt_entry.asm`, `hardware_vectors.asm`, `game_irq.asm`, `screen_raster_irqs.asm`, `room_dispatch.asm`, `lantern_pickup.asm`, `passage_open.asm`, `actor_timed_actions.asm`, `actor_hit_states.asm`, `enemy_ai_states.asm`, `status_and_keys.asm`, `title_menu.asm`, `pause_status_line.asm`, `music_player_state.asm`, `music_player.asm`, `sfx_voice1.asm`, `sfx_voice2.asm`, `sfx_voice3.asm`, `sfx_data.asm`.
- The decoded entries come from [the table reference](reference/tables.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *jump table* holds `JMP abs` instructions. An *RTS table* holds words of target - 1; the code pushes the word and executes `RTS`. A *compare chain* is a series of `CMP #` / `BNE` that selects a handler by a value.
- A *pass* is one run of [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) (every 3 frames). A *frame* is one raster interrupt at the bottom of the screen.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## 1. Overview

| Dispatch | Location | Index | Kind | Called by |
|---|---|---|---|---|
| CPU vectors | [`hw_nmi_vector`](../src/hardware_vectors.asm#L73) [`$FFFA-$FFFF`](reference/modules/hardware_vectors.md#hw_nmi_vector) | - | vectors | the CPU |
| IRQ handler | [`irq_vector`](../src/cold_start.asm#L31) [`$0408`](reference/modules/cold_start.md#irq_vector) | - | `JMP (ind)` at [`irq_dispatch`](../src/interrupt_entry.asm#L22) [`$1113`](reference/modules/interrupt_entry.md#irq_dispatch) | [`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry) |
| Room init | [`room_init_handlers`](../src/room_dispatch.asm#L19) [`$4E9C`](reference/modules/room_dispatch.md#room_init_handlers) | [`room`](../src/constants.asm#L32) * 2 | RTS table | [`room_init_dispatch`](../src/lantern_pickup.asm#L136) [`$33BD`](reference/modules/lantern_pickup.md#room_init_dispatch) |
| Room frame | [`room_frame_handlers`](../src/room_dispatch.asm#L28) [`$4EC4`](reference/modules/room_dispatch.md#room_frame_handlers) | [`room`](../src/constants.asm#L32) * 2 | RTS table | [`run_room_frame_handler`](../src/passage_open.asm#L18) [`$3A6F`](reference/modules/passage_open.md#run_room_frame_handler) |
| Action states | [`actor_continue_action`](../src/actor_timed_actions.asm#L14) [`$2008`](reference/modules/actor_timed_actions.md#actor_continue_action) | [`actor_state`](../src/constants.asm#L105),X | compare chain | [`actor_check_timer`](../src/actor_step.asm#L179) [`$1D77`](reference/modules/actor_step.md#actor_check_timer) |
| Game keys | [`handle_game_keys`](../src/status_and_keys.asm#L57) [`$1B29`](reference/modules/status_and_keys.md#handle_game_keys) | [`key_code`](../src/constants.asm#L137) | compare chain | [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) |
| Title keys | [`title_menu_handedness_keys`](../src/title_menu.asm#L107) [`$0956`](reference/modules/title_menu.md#title_menu_handedness_keys), [`title_menu_function_keys`](../src/title_menu.asm#L29) [`$08D2`](reference/modules/title_menu.md#title_menu_function_keys) | [`key_code`](../src/constants.asm#L137) | compare chain | [`title_menu_loop`](../src/title_menu.asm#L14) [`$08B1`](reference/modules/title_menu.md#title_menu_loop) |
| Demo abort | [`check_demo_abort`](../src/pause_status_line.asm#L7) [`$19B8`](reference/modules/pause_status_line.md#check_demo_abort) | fire, [`key_code`](../src/constants.asm#L137) | compare | [`main_loop`](../src/game_main_loop.asm#L23) [`$1BC2`](reference/modules/game_main_loop.md#main_loop) |
| Music API | [`music_api_stop`](../src/music_player_state.asm#L9) [`$E000-$E008`](reference/modules/music_player_state.md#music_api_stop) | entry * 3 | jump table | the game |
| Music internal | [`music_jump_stop`](../src/music_player.asm#L6) [`$E300-$E308`](reference/modules/music_player.md#music_jump_stop) | entry * 3 | jump table | API, playlist code |
| Music commands | [`music_cmd_jumps`](../src/music_player.asm#L446) [`$E5E8`](reference/modules/music_player.md#music_cmd_jumps) | [`music_cmd_offsets`](../src/music_player_state.asm#L163) [bits 4-6] | self-modified `BCC` into a jump table | [`music_voice_dispatch`](../src/music_player.asm#L430) [`$E5D7`](reference/modules/music_player.md#music_voice_dispatch) |
| Effect commands | [`sfx_voice1_cmd_jumps`](../src/sfx_voice1.asm#L52) [`$EB3A`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_jumps), [`sfx_voice2_cmd_jumps`](../src/sfx_voice2.asm#L52) [`$EFAA`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_jumps), [`sfx_voice3_cmd_jumps`](../src/sfx_voice3.asm#L52) [`$F0AA`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_jumps) | [`sfx_cmd_offsets`](../src/sfx_data.asm#L13) [command] | self-modified `BCC` into a jump table | the three effect players |
| Other indirect jumps | `$1110`, `$1117`, `$111A`, `$31A1` | - | `JMP (ind)` | section 9 |
| Zero-page RTS | `$0080` | - | `JSR`/`JMP` into zero page | [`cold_start`](../src/cold_start.asm#L22) [`$0440`](../src/cold_start.asm#L68), [`build_contact_masks`](../src/frame_builder.asm#L16) [`$517B`](../src/frame_builder.asm#L85) |

## 2. CPU vectors

The KERNAL ROM is switched out (`$01` = `$35`), so the CPU reads its vectors from the RAM at `$FFFA-$FFFF`.

| Vector | At | Value | Target |
|---|---|---|---|
| NMI | [`hw_nmi_vector`](../src/hardware_vectors.asm#L73) [`$FFFA`](reference/modules/hardware_vectors.md#hw_nmi_vector) | `$1116` | [`nmi_entry`](../src/interrupt_entry.asm#L25) [`$1116`](reference/modules/interrupt_entry.md#nmi_entry): `RTI`, so RESTORE does nothing |
| RESET | [`hw_reset_vector`](../src/hardware_vectors.asm#L75) [`$FFFC`](reference/modules/hardware_vectors.md#hw_reset_vector) | `$1116` | [`nmi_entry`](../src/interrupt_entry.asm#L25) [`$1116`](reference/modules/interrupt_entry.md#nmi_entry) |
| IRQ | [`hw_irq_vector`](../src/hardware_vectors.asm#L77) [`$FFFE`](reference/modules/hardware_vectors.md#hw_irq_vector) | `$1103` | [`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry) |

**Code.** The entries are in [the table reference](reference/tables.md#hw_nmi_vector).

## 3. The IRQ vector chain

[`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry) pushes A, X and Y. It tests the B flag of the stacked status with `AND #$00`, so the branch to `JMP (io1_dummy)` at `$1110` is never taken. Then [`irq_dispatch`](../src/interrupt_entry.asm#L22) [`$1113`](reference/modules/interrupt_entry.md#irq_dispatch) does `JMP (irq_vector)`. Each handler stores the address of the next handler in [`irq_vector`](../src/cold_start.asm#L31) [`$0408`](reference/modules/cold_start.md#irq_vector) / [`irq_vector_hi`](../src/cold_start.asm#L32) [`$0409`](reference/modules/cold_start.md#irq_vector_hi), sets the next raster line, and ends with `PLA`/`TAY`/`PLA`/`TAX`/`PLA`/`RTI`. **Code**

In the program image `$0408`/`$0409` hold `$29 $EF`: they are the operand bytes of the `AND #$EF` in [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start). Every screen setup stores a handler before it enables the raster interrupt. **Code**

~~~mermaid
flowchart LR
  subgraph T["Title and game over"]
    TF["irq_title_frame $152C line $FD"] --> TS["irq_title_split $1574 line $82"]
    TS --> TF
  end
  subgraph P["PLAYER n screen"]
    PS["irq_player_screen $14A4 line $63"] --> PS
  end
  subgraph G["Game screen"]
    GB["irq_game_bottom $48C1 line $FD"] --> GP["irq_game_playfield $491E line $40"]
    GP --> GC["irq_game_colour_split $4982 split lines"]
    GC --> GC
    GC --> GB
  end
~~~

The writers of [`irq_vector`](../src/cold_start.asm#L31):

| Store at | In | Next handler | Raster line |
|---|---|---|---|
| `$05DC` | [`show_title_screen`](../src/title_demo_start.asm#L83) [`$0584`](reference/modules/title_demo_start.md#show_title_screen) | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | `$FD` |
| `$18A4` | [`game_over`](../src/lose_fall_game_over.asm#L82) [`$188E`](reference/modules/lose_fall_game_over.md#game_over) | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | `$FD` |
| `$1551` | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) | `$82` |
| `$1585` | [`irq_title_split`](../src/screen_raster_irqs.asm#L121) [`$1574`](reference/modules/screen_raster_irqs.md#irq_title_split) | [`irq_title_frame`](../src/screen_raster_irqs.asm#L81) [`$152C`](reference/modules/screen_raster_irqs.md#irq_title_frame) | `$FD` |
| `$0F02` | [`show_player_screen`](../src/title_player_screens.asm#L71) [`$0EA7`](reference/modules/title_player_screens.md#show_player_screen) | [`irq_player_screen`](../src/screen_raster_irqs.asm#L10) [`$14A4`](reference/modules/screen_raster_irqs.md#irq_player_screen) (it stays installed and sets line `$63` again) | `$63` |
| `$083E` | [`init_game_irq`](../src/play_init.asm#L114) [`$082D`](reference/modules/play_init.md#init_game_irq) | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | `$FD` |
| `$48CD` | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) | `$40` |
| `$494B` | [`irq_game_playfield`](../src/game_irq.asm#L62) [`$491E`](reference/modules/game_irq.md#irq_game_playfield) | [`irq_game_colour_split`](../src/game_irq.asm#L117) [`$4982`](reference/modules/game_irq.md#irq_game_colour_split) | [`raster_split_lines`](../src/room_palettes.asm#L56) [0] |
| `$4977` | [`irq_chain_to_bottom`](../src/game_irq.asm#L108) [`$4975`](reference/modules/game_irq.md#irq_chain_to_bottom) | [`irq_game_bottom`](../src/game_irq.asm#L12) [`$48C1`](reference/modules/game_irq.md#irq_game_bottom) | `$FD` |

[`irq_arm_next_split`](../src/game_irq.asm#L89) [`$4953`](reference/modules/game_irq.md#irq_arm_next_split) sets the next split line from [`raster_split_lines`](../src/room_palettes.asm#L56). A line value of `$FD` ends the list; then [`irq_chain_to_bottom`](../src/game_irq.asm#L108) [`$4975`](reference/modules/game_irq.md#irq_chain_to_bottom) puts [`irq_game_bottom`](../src/game_irq.asm#L12) back. [`irq_game_colour_split`](../src/game_irq.asm#L117) keeps itself as the handler for the other split lines. **Code**

## 4. Room init handlers (RTS table)

- Table: [`room_init_handlers`](../src/room_dispatch.asm#L19) [`$4E9C-$4EC3`](reference/modules/room_dispatch.md#room_init_handlers), 20 words of target - 1, index = [`room`](../src/constants.asm#L32) * 2.
- Code: [`room_init_dispatch`](../src/lantern_pickup.asm#L136) [`$33BD`](reference/modules/lantern_pickup.md#room_init_dispatch) in [`setup_room_lanterns_and_init`](../src/lantern_pickup.asm#L79) [`$336E`](reference/modules/lantern_pickup.md#setup_room_lanterns_and_init) pushes [`room_init_handlers+1`](../src/room_dispatch.asm#L19),X and then [`room_init_handlers`](../src/room_dispatch.asm#L19),X, and executes `RTS`.
- Called once per room, by [`draw_room`](../src/draw_room.asm#L28) ([`$0B30`](../src/draw_room.asm#L223)), after the room is drawn.

| Room | At | Word | Target |
|---|---|---|---|
| 0 | `$4E9C` | `$33F4` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) |
| 1 | `$4E9E` | `$33F5` | [`room01_init`](../src/room_specific_init.asm#L9) [`$33F6`](reference/modules/room_specific_init.md#room01_init) |
| 2 | `$4EA0` | `$33F4` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) |
| 3 | `$4EA2` | `$33FB` | [`room03_init`](../src/room_specific_init.asm#L14) [`$33FC`](reference/modules/room_specific_init.md#room03_init) |
| 4 | `$4EA4` | `$3401` | [`room04_init`](../src/room_specific_init.asm#L22) [`$3402`](reference/modules/room_specific_init.md#room04_init) |
| 5 | `$4EA6` | `$3427` | [`room05_init`](../src/room_specific_init.asm#L48) [`$3428`](reference/modules/room_specific_init.md#room05_init) |
| 6 | `$4EA8` | `$33F4` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) |
| 7 | `$4EAA` | `$3460` | [`room07_init`](../src/room_specific_init.asm#L93) [`$3461`](reference/modules/room_specific_init.md#room07_init) |
| 8 | `$4EAC` | `$3477` | [`room08_init`](../src/room_specific_init.asm#L107) [`$3478`](reference/modules/room_specific_init.md#room08_init) |
| 9 | `$4EAE` | `$348E` | [`room09_init`](../src/room_specific_init.asm#L123) [`$348F`](reference/modules/room_specific_init.md#room09_init) |
| 10 | `$4EB0` | `$33F4` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) |
| 11 | `$4EB2` | `$33F4` | [`room_init_none`](../src/room_specific_init.asm#L6) [`$33F5`](reference/modules/room_specific_init.md#room_init_none) |
| 12 | `$4EB4` | `$34BC` | [`room12_init`](../src/room_specific_init.asm#L149) [`$34BD`](reference/modules/room_specific_init.md#room12_init) |
| 13 | `$4EB6` | `$34C2` | [`room13_init`](../src/room_specific_init.asm#L159) [`$34C3`](reference/modules/room_specific_init.md#room13_init) |
| 14 | `$4EB8` | `$358C` | [`room14_init`](../src/room_specific_init.asm#L249) [`$358D`](reference/modules/room_specific_init.md#room14_init) |
| 15 | `$4EBA` | `$3592` | [`room15_init`](../src/room_specific_init.asm#L255) [`$3593`](reference/modules/room_specific_init.md#room15_init) |
| 16 | `$4EBC` | `$359E` | [`room16_init`](../src/room_specific_init.asm#L264) [`$359F`](reference/modules/room_specific_init.md#room16_init) |
| 17 | `$4EBE` | `$35C3` | [`room17_init`](../src/room_specific_init.asm#L284) [`$35C4`](reference/modules/room_specific_init.md#room17_init) |
| 18 | `$4EC0` | `$35F9` | [`room18_init`](../src/room_specific_init.asm#L317) [`$35FA`](reference/modules/room_specific_init.md#room18_init) |
| 19 | `$4EC2` | `$425E` | [`room19_init`](../src/ending_room.asm#L7) [`$425F`](reference/modules/ending_room.md#room19_init) |

## 5. Room frame handlers (RTS table)

- Table: [`room_frame_handlers`](../src/room_dispatch.asm#L28) [`$4EC4-$4EEB`](reference/modules/room_dispatch.md#room_frame_handlers), 20 words of target - 1, index = [`room`](../src/constants.asm#L32) * 2.
- Code: [`run_room_frame_handler`](../src/passage_open.asm#L18) [`$3A6F`](reference/modules/passage_open.md#run_room_frame_handler) pushes the word and executes `RTS`. The handler returns to the caller of [`run_room_frame_handler`](../src/passage_open.asm#L18).
- Called by [`main_loop`](../src/game_main_loop.asm#L23) ([`$1C0A`](../src/game_main_loop.asm#L61)) on every pass, and once by [`draw_room`](../src/draw_room.asm#L28) ([`$0B40`](../src/draw_room.asm#L229)) at the end of the drawing.

| Room | At | Word | Target |
|---|---|---|---|
| 0 | `$4EC4` | `$3641` | [`room00_frame`](../src/room_frames_0_7.asm#L9) [`$3642`](reference/modules/room_frames_0_7.md#room00_frame) |
| 1 | `$4EC6` | `$3678` | [`room01_frame`](../src/room_frames_0_7.asm#L42) [`$3679`](reference/modules/room_frames_0_7.md#room01_frame) |
| 2 | `$4EC8` | `$36A5` | [`room02_frame`](../src/room_frames_0_7.asm#L75) [`$36A6`](reference/modules/room_frames_0_7.md#room02_frame) |
| 3 | `$4ECA` | `$3701` | [`room03_frame`](../src/room_frames_0_7.asm#L136) [`$3702`](reference/modules/room_frames_0_7.md#room03_frame) |
| 4 | `$4ECC` | `$375F` | [`room04_frame`](../src/room_frames_0_7.asm#L195) [`$3760`](reference/modules/room_frames_0_7.md#room04_frame) |
| 5 | `$4ECE` | `$38AA` | [`room05_frame`](../src/room_frames_0_7.asm#L378) [`$38AB`](reference/modules/room_frames_0_7.md#room05_frame) |
| 6 | `$4ED0` | `$39A9` | [`room06_frame`](../src/room_frames_0_7.asm#L519) [`$39AA`](reference/modules/room_frames_0_7.md#room06_frame) |
| 7 | `$4ED2` | `$39C2` | [`room07_frame`](../src/room_frames_0_7.asm#L542) [`$39C3`](reference/modules/room_frames_0_7.md#room07_frame) |
| 8 | `$4ED4` | `$3AD3` | [`room08_frame`](../src/room_frames_8_11.asm#L16) [`$3AD4`](reference/modules/room_frames_8_11.md#room08_frame) |
| 9 | `$4ED6` | `$3BB1` | [`room09_frame`](../src/room_frames_8_11.asm#L149) [`$3BB2`](reference/modules/room_frames_8_11.md#room09_frame) |
| 10 | `$4ED8` | `$3C8F` | [`room10_frame`](../src/room_frames_8_11.asm#L278) [`$3C90`](reference/modules/room_frames_8_11.md#room10_frame) |
| 11 | `$4EDA` | `$3CBF` | [`room11_frame`](../src/room_frames_8_11.asm#L318) [`$3CC0`](reference/modules/room_frames_8_11.md#room11_frame) |
| 12 | `$4EDC` | `$3E4B` | [`room12_frame`](../src/room_frames_12_17.asm#L11) [`$3E4C`](reference/modules/room_frames_12_17.md#room12_frame) |
| 13 | `$4EDE` | `$3E7B` | [`room13_frame`](../src/room_frames_12_17.asm#L41) [`$3E7C`](reference/modules/room_frames_12_17.md#room13_frame) |
| 14 | `$4EE0` | `$3ECB` | [`room14_frame`](../src/room_frames_12_17.asm#L88) [`$3ECC`](reference/modules/room_frames_12_17.md#room14_frame) |
| 15 | `$4EE2` | `$3EE5` | [`room15_frame`](../src/room_frames_12_17.asm#L106) [`$3EE6`](reference/modules/room_frames_12_17.md#room15_frame) |
| 16 | `$4EE4` | `$3F5A` | [`room16_frame`](../src/room_frames_12_17.asm#L166) [`$3F5B`](reference/modules/room_frames_12_17.md#room16_frame) |
| 17 | `$4EE6` | `$3F70` | [`room17_frame`](../src/room_frames_12_17.asm#L188) [`$3F71`](reference/modules/room_frames_12_17.md#room17_frame) |
| 18 | `$4EE8` | `$3CDB` | [`room18_frame`](../src/wizard_room.asm#L13) [`$3CDC`](reference/modules/wizard_room.md#room18_frame) |
| 19 | `$4EEA` | `$4271` | [`room19_frame`](../src/ending_room.asm#L27) [`$4272`](reference/modules/ending_room.md#room19_frame) |

The RTS of [`room_init_dispatch`](../src/lantern_pickup.asm#L136) makes static analyzers report many false jump targets (the analysis notes removed 36 of them). **Code**

## 6. Action state handlers (compare chain)

[`actor_action_step`](../src/actor_step.asm#L21) [`$1C5B`](reference/modules/actor_step.md#actor_action_step) runs one step of actor X. At [`actor_check_timer`](../src/actor_step.asm#L179) [`$1D77`](reference/modules/actor_step.md#actor_check_timer) a nonzero [`actor_timer`](../src/constants.asm#L110),X jumps to [`actor_continue_action`](../src/actor_timed_actions.asm#L14) [`$2008`](reference/modules/actor_timed_actions.md#actor_continue_action); a zero timer goes on to [`actor_read_input`](../src/actor_step.asm#L184) [`$1D7E`](reference/modules/actor_step.md#actor_read_input), which chooses a new action from the joystick with a chain of bit tests (no table). **Code**

[`actor_continue_action`](../src/actor_timed_actions.asm#L14) [`$2008`](reference/modules/actor_timed_actions.md#actor_continue_action) stores the timer in [`temp_y`](../src/constants.asm#L46) and compares [`actor_state`](../src/constants.asm#L105),X in this order:

| Order | Compare at | State | Handler |
|---|---|---|---|
| 1 | [`actor_continue_action`](../src/actor_timed_actions.asm#L14) [`$2008`](reference/modules/actor_timed_actions.md#actor_continue_action) | `$05` | jump up |
| 2 | [`act_check_kick_left`](../src/actor_timed_actions.asm#L48) [`$2048`](reference/modules/actor_timed_actions.md#act_check_kick_left) | `$0C` | flying kick left |
| 3 | [`act_check_kick_right`](../src/actor_timed_actions.asm#L85) [`$208D`](reference/modules/actor_timed_actions.md#act_check_kick_right) | `$0D` | flying kick right |
| 4 | [`act_check_jump_left`](../src/actor_timed_actions.asm#L121) [`$20D2`](reference/modules/actor_timed_actions.md#act_check_jump_left) | `$06` | jump left |
| 5 | [`act_check_jump_right`](../src/actor_timed_actions.asm#L161) [`$2120`](reference/modules/actor_timed_actions.md#act_check_jump_right) | `$07` | jump right |
| 6 | [`act_check_dying`](../src/actor_timed_actions.asm#L198) [`$216B`](reference/modules/actor_timed_actions.md#act_check_dying) | `$19` | dying; at the end [`lose_fall`](../src/lose_fall_game_over.asm#L14) [`$1818`](reference/modules/lose_fall_game_over.md#lose_fall) |
| 7 | [`act_check_ride`](../src/actor_timed_actions.asm#L214) [`$2180`](reference/modules/actor_timed_actions.md#act_check_ride) | `$17` | ride |
| 8 | [`act_check_yamo_appear`](../src/actor_timed_actions.asm#L315) [`$2235`](reference/modules/actor_timed_actions.md#act_check_yamo_appear) | `$10` | Yamo appears |
| 9 | [`act_check_punch`](../src/actor_timed_actions.asm#L349) [`$226A`](reference/modules/actor_timed_actions.md#act_check_punch) | `$11` | punch |
| 10 | [`act_check_ninja_strike`](../src/actor_timed_actions.asm#L407) [`$22BD`](reference/modules/actor_timed_actions.md#act_check_ninja_strike) | `$16` | Ninja strike |
| 11 | [`act_check_ai_chase`](../src/actor_timed_actions.asm#L442) [`$22F3`](reference/modules/actor_timed_actions.md#act_check_ai_chase) | `$14` | AI chase: [`ai_chase`](../src/enemy_ai_states.asm#L13) [`$22FA`](reference/modules/enemy_ai_states.md#ai_chase) |
| 12 | [`act_check_ai_back_off`](../src/enemy_ai_states.asm#L146) [`$23CD`](reference/modules/enemy_ai_states.md#act_check_ai_back_off) | `$15` | AI back off |
| 13 | [`act_check_yamo_pose`](../src/actor_hit_states.asm#L5) [`$2407`](reference/modules/actor_hit_states.md#act_check_yamo_pose) | `$12` | Yamo pose: only the timer runs |
| 14 | [`act_check_recoil`](../src/actor_hit_states.asm#L9) [`$240E`](reference/modules/actor_hit_states.md#act_check_recoil) | `$0F` | recoil |
| 15 | [`act_check_knocked_down`](../src/actor_hit_states.asm#L37) [`$2440`](reference/modules/actor_hit_states.md#act_check_knocked_down) | `$13` | knocked down |
| 16 | [`act_check_wall_bump`](../src/actor_hit_states.asm#L97) [`$24B3`](reference/modules/actor_hit_states.md#act_check_wall_bump) | `$18` | wall bump |
| - | [`actor_continue_state`](../src/actor_hit_states.asm#L143) [`$24F4`](reference/modules/actor_hit_states.md#actor_continue_state) | any other (0, `$1B`) | the state stays, the timer counts down |

Each handler ends in [`actor_continue_state`](../src/actor_hit_states.asm#L143) [`$24F4`](reference/modules/actor_hit_states.md#actor_continue_state) (state = A, timer = [`temp_y`](../src/constants.asm#L46) - 1) or in a setter that ends the action. **Code**

## 7. Key handlers (compare chains)

The key codes are the codes of [`scan_keyboard`](../src/keyboard_scan.asm#L24) [`$139E`](reference/modules/keyboard_scan.md#scan_keyboard) in [`key_code`](../src/constants.asm#L137). Bit 7 is the shift bit.

[`handle_game_keys`](../src/status_and_keys.asm#L57) [`$1B29`](reference/modules/status_and_keys.md#handle_game_keys) (each pass of a game, not in the demo). [`scan_keyboard`](../src/keyboard_scan.asm#L24) decodes only these four keys here ([`key_scan_mode`](../src/constants.asm#L142) = 1):

| Key | Code (AND `$7F`) | Compare at | Action |
|---|---|---|---|
| F1 | `$04` | [`handle_game_keys_new_key`](../src/status_and_keys.asm#L64) [`$1B37`](reference/modules/status_and_keys.md#handle_game_keys_new_key) | [`restart_to_title`](../src/title_demo_start.asm#L9) [`$050F`](reference/modules/title_demo_start.md#restart_to_title) |
| S | `$0D` | [`handle_game_keys_check_s`](../src/status_and_keys.asm#L73) [`$1B4A`](reference/modules/status_and_keys.md#handle_game_keys_check_s) | toggle [`title_music_off`](../src/room_enemy_tables.asm#L118), clear [`title_music_skip_count`](../src/title_menu.asm#L163) |
| SPACE | `$3C` | [`handle_game_keys_check_space`](../src/status_and_keys.asm#L82) [`$1B5C`](reference/modules/status_and_keys.md#handle_game_keys_check_space) | [`handle_game_keys_pause`](../src/status_and_keys.asm#L89) [`$1B65`](reference/modules/status_and_keys.md#handle_game_keys_pause) -> [`toggle_pause`](../src/pause_status_line.asm#L69) [`$1A22`](reference/modules/pause_status_line.md#toggle_pause) |
| V | `$1F` | [`handle_game_keys_check_space`](../src/status_and_keys.asm#L82) [`$1B5C`](reference/modules/status_and_keys.md#handle_game_keys_check_space) | [`toggle_credit_line`](../src/status_and_keys.asm#L94) [`$1B68`](reference/modules/status_and_keys.md#toggle_credit_line) |

[`title_menu_loop`](../src/title_menu.asm#L14) [`$08B1`](reference/modules/title_menu.md#title_menu_loop) (each pass of the title menu). First the handedness keys, with the shift bit:

| Key | Code | Compare at | Action |
|---|---|---|---|
| L | `$2A` | [`title_menu_handedness_keys`](../src/title_menu.asm#L107) [`$0956`](reference/modules/title_menu.md#title_menu_handedness_keys) | [`title_set_joy1_left_handed`](../src/title_menu.asm#L117) [`$0969`](reference/modules/title_menu.md#title_set_joy1_left_handed) |
| shift-L | `$AA` | [`title_menu_handedness_keys`](../src/title_menu.asm#L107) [`$0956`](reference/modules/title_menu.md#title_menu_handedness_keys) | [`title_set_joy2_left_handed`](../src/title_menu.asm#L125) [`$0979`](reference/modules/title_menu.md#title_set_joy2_left_handed) |
| R | `$11` | [`title_menu_handedness_keys`](../src/title_menu.asm#L107) [`$0956`](reference/modules/title_menu.md#title_menu_handedness_keys) | [`title_set_joy1_right_handed`](../src/title_menu.asm#L133) [`$0988`](reference/modules/title_menu.md#title_set_joy1_right_handed) |
| shift-R | `$91` | [`title_menu_handedness_keys`](../src/title_menu.asm#L107) [`$0956`](reference/modules/title_menu.md#title_menu_handedness_keys) | [`title_set_joy2_right_handed`](../src/title_menu.asm#L141) [`$0998`](reference/modules/title_menu.md#title_set_joy2_right_handed) |

Then [`title_menu_function_keys`](../src/title_menu.asm#L29) [`$08D2`](reference/modules/title_menu.md#title_menu_function_keys), without the shift bit:

| Key | Code | Action |
|---|---|---|
| F7 | `$03` | [`title_menu_start_game`](../src/title_menu.asm#L52) [`$08FC`](reference/modules/title_menu.md#title_menu_start_game) |
| F5 | `$06` | [`title_menu_toggle_opponent`](../src/title_menu.asm#L61) [`$0908`](reference/modules/title_menu.md#title_menu_toggle_opponent) |
| F3 | `$05` | [`title_menu_toggle_players`](../src/title_menu.asm#L81) [`$092C`](reference/modules/title_menu.md#title_menu_toggle_players) |

[`check_demo_abort`](../src/pause_status_line.asm#L7) [`$19B8`](reference/modules/pause_status_line.md#check_demo_abort) (each pass of the demo): fire on joystick port 1, or F1 (`$04`), goes to [`demo_abort_to_title`](../src/pause_status_line.asm#L24) [`$19DD`](reference/modules/pause_status_line.md#demo_abort_to_title), which waits for the fire button and jumps to [`restart_to_title`](../src/title_demo_start.asm#L9) [`$050F`](reference/modules/title_demo_start.md#restart_to_title). **Code**

## 8. Music and effect player tables

### 8.1 Music API and internal jumps

[`music_api_stop`](../src/music_player_state.asm#L9) [`$E000-$E008`](reference/modules/music_player_state.md#music_api_stop):

| Entry | At | Target |
|---|---|---|
| stop | `$E000` | [`music_jump_stop`](../src/music_player.asm#L6) [`$E300`](reference/modules/music_player.md#music_jump_stop) |
| start the playlist | `$E003` | [`music_jump_start_playlist`](../src/music_player.asm#L10) [`$E306`](reference/modules/music_player.md#music_jump_start_playlist) |
| play one frame | `$E006` | [`music_play_frame`](../src/music_player.asm#L279) [`$E49E`](reference/modules/music_player.md#music_play_frame) |

[`music_jump_stop`](../src/music_player.asm#L6) [`$E300-$E308`](reference/modules/music_player.md#music_jump_stop):

| Entry | At | Target |
|---|---|---|
| stop | `$E300` | [`music_stop`](../src/music_player.asm#L199) [`$E434`](reference/modules/music_player.md#music_stop) |
| start the current song | `$E303` | [`music_init_song`](../src/music_player.asm#L43) [`$E352`](reference/modules/music_player.md#music_init_song) |
| start the playlist | `$E306` | [`music_start_playlist`](../src/music_player.asm#L253) [`$E479`](reference/modules/music_player.md#music_start_playlist) |

[`music_start_song_x`](../src/music_player.asm#L226) [`$E455`](reference/modules/music_player.md#music_start_song_x) jumps to [`music_jump_start_song`](../src/music_player.asm#L8) [`$E303`](reference/modules/music_player.md#music_jump_start_song). **Code**

### 8.2 Music commands (self-modified branch)

[`music_voice_dispatch`](../src/music_player.asm#L430) [`$E5D7`](reference/modules/music_player.md#music_voice_dispatch) takes bits 4-6 of the command byte as the index into [`music_cmd_offsets`](../src/music_player_state.asm#L163) [`$E2D6`](reference/modules/music_player_state.md#music_cmd_offsets). It stores the offset in [`music_cmd_offset`](../src/music_player.asm#L442) [`$E5E7`](reference/modules/music_player.md#music_cmd_offset), the operand of the `BCC` at [`music_cmd_branch`](../src/music_player.asm#L441) [`$E5E6`](reference/modules/music_player.md#music_cmd_branch), clears C, and executes the branch. The branch lands in [`music_cmd_jumps`](../src/music_player.asm#L446) [`$E5E8`](reference/modules/music_player.md#music_cmd_jumps). **Code**

| Group | Commands | Offset | Lands at | Target |
|---|---|---|---|---|
| 0 | `$80-$8F` | `$00` | `$E5E8` | [`music_cmd_length`](../src/music_player.asm#L457) [`$E5FD`](reference/modules/music_player.md#music_cmd_length) |
| 1 | `$90-$9F` | `$03` | `$E5EB` | [`music_cmd_volume`](../src/music_player.asm#L470) [`$E617`](reference/modules/music_player.md#music_cmd_volume) |
| 2 | `$A0-$AF` | `$06` | `$E5EE` | [`music_cmd_voice_option`](../src/music_player.asm#L486) [`$E630`](reference/modules/music_player.md#music_cmd_voice_option) |
| 3 | `$B0-$BF` | `$09` | `$E5F1` | [`music_cmd_instrument`](../src/music_player.asm#L620) [`$E720`](reference/modules/music_player.md#music_cmd_instrument) |
| 4 | `$C0-$CF` | `$0C` | `$E5F4` | [`music_cmd_pulse_width`](../src/music_player.asm#L657) [`$E75E`](reference/modules/music_player.md#music_cmd_pulse_width) |
| 5 | `$D0-$DF` | `$0F` | `$E5F7` | [`music_cmd_filter`](../src/music_player.asm#L670) [`$E779`](reference/modules/music_player.md#music_cmd_filter) |
| 6 | `$E0-$EF` | `$12` | `$E5FA` | [`music_cmd_tempo`](../src/music_player.asm#L700) [`$E7B2`](reference/modules/music_player.md#music_cmd_tempo) |
| 7 | `$F0-$FE` | `$15` | `$E5FD` | [`music_cmd_length`](../src/music_player.asm#L457) [`$E5FD`](reference/modules/music_player.md#music_cmd_length) (the first byte after the table) |

[`music_cmd_offsets`](../src/music_player_state.asm#L163) has 17 entries (`$00` to `$30` in steps of 3); entries 8-16 are never used. `$FF` never reaches the dispatch: [`music_voice_read_command`](../src/music_player.asm#L421) [`$E5C3`](reference/modules/music_player.md#music_voice_read_command) handles it first. The image holds offset `$00` in the branch, a value left from the last command. **Code**

### 8.3 Effect commands (self-modified branch)

Each effect player reads the command byte (0-7), stores [`sfx_cmd_offsets`](../src/sfx_data.asm#L13) [`$EC03`](reference/modules/sfx_data.md#sfx_cmd_offsets) [command] in its branch operand and executes the `BCC`:

| Player | Store | Branch | Branch operand | Jump table |
|---|---|---|---|---|
| voice 1 | `$EB34` | [`sfx_voice1_cmd_branch`](../src/sfx_voice1.asm#L47) [`$EB38`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_branch) | [`sfx_voice1_cmd_offset`](../src/sfx_voice1.asm#L48) [`$EB39`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_offset) | [`sfx_voice1_cmd_jumps`](../src/sfx_voice1.asm#L52) [`$EB3A`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_jumps) |
| voice 2 | `$EFA4` | [`sfx_voice2_cmd_branch`](../src/sfx_voice2.asm#L47) [`$EFA8`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_branch) | [`sfx_voice2_cmd_offset`](../src/sfx_voice2.asm#L48) [`$EFA9`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_offset) | [`sfx_voice2_cmd_jumps`](../src/sfx_voice2.asm#L52) [`$EFAA`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_jumps) |
| voice 3 | `$F0A4` | [`sfx_voice3_cmd_branch`](../src/sfx_voice3.asm#L47) [`$F0A8`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_branch) | [`sfx_voice3_cmd_offset`](../src/sfx_voice3.asm#L48) [`$F0A9`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_offset) | [`sfx_voice3_cmd_jumps`](../src/sfx_voice3.asm#L52) [`$F0AA`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_jumps) |

| Command | Offset | Voice 1 target | Voice 2 target | Voice 3 target |
|---|---|---|---|---|
| 0 end | `$00` | [`sfx_voice1_cmd_end`](../src/sfx_voice1.asm#L95) [`$EB82`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_end) | [`sfx_voice2_cmd_end`](../src/sfx_voice2.asm#L95) [`$EFF2`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_end) | [`sfx_voice3_cmd_end`](../src/sfx_voice3.asm#L95) [`$F0F2`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_end) |
| 1 note | `$03` | [`sfx_voice1_cmd_note`](../src/sfx_voice1.asm#L113) [`$EBA2`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note) | [`sfx_voice2_cmd_note`](../src/sfx_voice2.asm#L113) [`$F012`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_note) | [`sfx_voice3_cmd_note`](../src/sfx_voice3.asm#L113) [`$F112`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_note) |
| 2 note, control | `$06` | [`sfx_voice1_cmd_note_control`](../src/sfx_voice1.asm#L118) [`$EBA9`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_control) | [`sfx_voice2_cmd_note_control`](../src/sfx_voice2.asm#L118) [`$F019`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_note_control) | [`sfx_voice3_cmd_note_control`](../src/sfx_voice3.asm#L118) [`$F119`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_note_control) |
| 3 note, ADSR, control | `$09` | [`sfx_voice1_cmd_note_adsr_control`](../src/sfx_voice1.asm#L124) [`$EBB3`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_adsr_control) | [`sfx_voice2_cmd_note_adsr_control`](../src/sfx_voice2.asm#L124) [`$F023`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_note_adsr_control) | [`sfx_voice3_cmd_note_adsr_control`](../src/sfx_voice3.asm#L124) [`$F123`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_note_adsr_control) |
| 4 note, ADSR, pulse, control | `$0C` | [`sfx_voice1_cmd_note_adsr_pulse_control`](../src/sfx_voice1.asm#L131) [`$EBC0`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_adsr_pulse_control) | [`sfx_voice2_cmd_note_adsr_pulse_control`](../src/sfx_voice2.asm#L131) [`$F030`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_note_adsr_pulse_control) | [`sfx_voice3_cmd_note_adsr_pulse_control`](../src/sfx_voice3.asm#L131) [`$F130`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_note_adsr_pulse_control) |
| 5 note, pulse, control | `$0F` | [`sfx_voice1_cmd_note_pulse_control`](../src/sfx_voice1.asm#L139) [`$EBD0`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_pulse_control) | [`sfx_voice2_cmd_note_pulse_control`](../src/sfx_voice2.asm#L139) [`$F040`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_note_pulse_control) | [`sfx_voice3_cmd_note_pulse_control`](../src/sfx_voice3.asm#L139) [`$F140`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_note_pulse_control) |
| 6 the same as 5 | `$12` | [`sfx_voice1_cmd_note_pulse_control`](../src/sfx_voice1.asm#L139) [`$EBD0`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_note_pulse_control) | [`sfx_voice2_cmd_note_pulse_control`](../src/sfx_voice2.asm#L139) [`$F040`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_note_pulse_control) | [`sfx_voice3_cmd_note_pulse_control`](../src/sfx_voice3.asm#L139) [`$F140`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_note_pulse_control) |
| 7 control | `$15` | [`sfx_voice1_cmd_control`](../src/sfx_voice1.asm#L147) [`$EBDD`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_control) | [`sfx_voice2_cmd_control`](../src/sfx_voice2.asm#L147) [`$F04D`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_control) | [`sfx_voice3_cmd_control`](../src/sfx_voice3.asm#L147) [`$F14D`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_control) |

[`sfx_cmd_offsets`](../src/sfx_data.asm#L13) has 14 entries; entries 8-13 would land past the jump tables, and no stream uses them. The image holds the branch offset `$FE` in the voice 1 player (`BCC` to itself); the player writes the offset before each use. **Code**

### 8.4 Effect stream table

[`sfx_stream_table`](../src/sfx_data.asm#L6) [`$EBE5`](reference/modules/sfx_data.md#sfx_stream_table) (index = effect * 2) is an address table, not a jump table. Its 15 entries are in [the table reference](reference/tables.md#sfx_stream_table).

## 9. Other indirect and computed jumps

| At | Instruction | In | Reached | Target |
|---|---|---|---|---|
| `$1113` | `JMP (irq_vector)` | [`irq_dispatch`](../src/interrupt_entry.asm#L22) [`$1113`](reference/modules/interrupt_entry.md#irq_dispatch) | each interrupt | the current raster handler (section 3) |
| `$1110` | `JMP (io1_dummy)` | [`irq_entry`](../src/interrupt_entry.asm#L10) [`$1103`](reference/modules/interrupt_entry.md#irq_entry) | never: the BRK test uses `AND #$00` | the bytes of the I/O area at `$DE00` |
| `$31A1` | `JMP (io1_dummy)` | [`update_high_score`](../src/score.asm#L65) [`$3184`](reference/modules/score.md#update_high_score) | only when three protection key pairs are equal | `$DE00` (open I/O): a crash |
| `$1117` | `JMP (hw_reset_vector)` | [`unused_jump_reset_vector`](../src/interrupt_entry.asm#L30) [`$1117`](reference/modules/interrupt_entry.md#unused_jump_reset_vector) | never: no code jumps here | [`nmi_entry`](../src/interrupt_entry.asm#L25) [`$1116`](reference/modules/interrupt_entry.md#nmi_entry) |
| `$111A` | `JMP (D6510)` | [`unused_jump_zero_vector`](../src/interrupt_entry.asm#L32) [`$111A`](reference/modules/interrupt_entry.md#unused_jump_zero_vector) | never | the word at `$0000` |
| `$0440` | `JSR $0080` | [`cold_start`](../src/cold_start.asm#L22) [`$0400`](reference/modules/cold_start.md#cold_start) | once at the start | the `RTS` that the loader leaves at `$0080` |
| `$517B` | `JMP $0080` | [`build_contact_masks`](../src/frame_builder.asm#L16) [`$512F`](reference/modules/frame_builder.md#build_contact_masks) ([`build_masks_done`](../src/frame_builder.asm#L76) [`$517B`](reference/modules/frame_builder.md#build_masks_done)) | once at the start | the same `RTS`: returns to [`cold_start`](../src/cold_start.asm#L22) |

The jump at `$31A1` and the zero-page `RTS` are parts of the copy protection ([protection.md](protection.md)). After [`init_game_variables`](../src/game_setup.asm#L18) [`$0F72`](reference/modules/game_setup.md#init_game_variables) clears the zero page, `$0080` is [`frame_count_256`](../src/constants.asm#L80). **Code**

Code that is changed at run time to jump or stop:

| Place | Change | Writer |
|---|---|---|
| [`music_cmd_offset`](../src/music_player.asm#L442) [`$E5E7`](reference/modules/music_player.md#music_cmd_offset) | branch offset of the music command dispatch | [`music_voice_dispatch`](../src/music_player.asm#L430) [`$E5D7`](reference/modules/music_player.md#music_voice_dispatch) |
| [`sfx_voice1_cmd_offset`](../src/sfx_voice1.asm#L48) [`$EB39`](reference/modules/sfx_voice1.md#sfx_voice1_cmd_offset), [`sfx_voice2_cmd_offset`](../src/sfx_voice2.asm#L48) [`$EFA9`](reference/modules/sfx_voice2.md#sfx_voice2_cmd_offset), [`sfx_voice3_cmd_offset`](../src/sfx_voice3.asm#L48) [`$F0A9`](reference/modules/sfx_voice3.md#sfx_voice3_cmd_offset) | branch offset of the effect command dispatch | the effect players |
| [`random_byte`](../src/interrupt_entry.asm#L89) [`$1159`](reference/modules/interrupt_entry.md#random_byte) | first opcode LDA becomes TXS (opcode $9A) | [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound), a failed protection check |
| [`step_sound_crash_point`](../src/actor_step.asm#L606) [`$1FFE`](reference/modules/actor_step.md#step_sound_crash_point) | CLC becomes TXS (opcode $9A), with X = 4 | [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound), a failed protection check |

### 9.1 Self-modified operands that are not jumps

For completeness, these instructions get their address operand at run time. They read or write data; none of them changes the flow.

| Operand | Instruction of | Writer |
|---|---|---|
| [`music_fetch_voice0_src`](../src/music_player.asm#L136) [`$E3DF`](reference/modules/music_player.md#music_fetch_voice0_src), [`music_fetch_voice1_src`](../src/music_player.asm#L141) [`$E3E3`](reference/modules/music_player.md#music_fetch_voice1_src), [`music_fetch_voice2_src`](../src/music_player.asm#L146) [`$E3E7`](reference/modules/music_player.md#music_fetch_voice2_src) | `LDA abs` of the music stream fetch | [`music_set_voice_pointers`](../src/music_player.asm#L53) [`$E360`](reference/modules/music_player.md#music_set_voice_pointers), [`music_read_byte`](../src/music_player.asm#L153) [`$E3EA`](reference/modules/music_player.md#music_read_byte) |
| [`spawn_yamo_prot_key_lo`](../src/actor_spawn.asm#L206) [`$0CD9`](reference/modules/actor_spawn.md#spawn_yamo_prot_key_lo), [`spawn_yamo_prot_pair_lo`](../src/actor_spawn.asm#L209) [`$0CDC`](reference/modules/actor_spawn.md#spawn_yamo_prot_pair_lo) | protection key read in [`spawn_yamo`](../src/actor_spawn.asm#L203) [`$0CD5`](reference/modules/actor_spawn.md#spawn_yamo) | [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound) |
| [`main_loop_prot_key_lo`](../src/game_main_loop.asm#L68) [`$1C14`](reference/modules/game_main_loop.md#main_loop_prot_key_lo), [`main_loop_prot_pair_lo`](../src/game_main_loop.asm#L70) [`$1C17`](reference/modules/game_main_loop.md#main_loop_prot_pair_lo) | protection key read in [`main_loop_protection_check`](../src/game_main_loop.asm#L67) [`$1C13`](reference/modules/game_main_loop.md#main_loop_protection_check) | [`actor_play_step_sound`](../src/actor_step.asm#L556) [`$1FC4`](reference/modules/actor_step.md#actor_play_step_sound) |
| [`reset_yamo_timer_src`](../src/actor_spawn.asm#L288) [`$0D56`](reference/modules/actor_spawn.md#reset_yamo_timer_src), [`reset_ninja_timer_src`](../src/actor_spawn.asm#L320) [`$0D86`](reference/modules/actor_spawn.md#reset_ninja_timer_src) | spawn timer reload | the spawn code (`$0D4B`, `$0D7B`) |
| [`copy_sprite_frame_narrow_src`](../src/actor_sprites.asm#L197), [`copy_sprite_frame_wide_src_a`](../src/actor_sprites.asm#L235), [`copy_sprite_frame_wide_src_b`](../src/actor_sprites.asm#L242) | sprite frame copy | the sprite code |
| [`animate_scrolling_chars_src`](../src/animated_chars.asm#L124) | animated characters | [`animate_scrolling_chars`](../src/animated_chars.asm#L12) |
| [`shift_mask_copy_src`](../src/background_contact.asm#L120) [`$52CC`](reference/modules/background_contact.md#shift_mask_copy_src), [`scan_col0_src`](../src/background_contact.asm#L228) [`$5381`](reference/modules/background_contact.md#scan_col0_src), [`scan_col1_src`](../src/background_contact.asm#L246) [`$539B`](reference/modules/background_contact.md#scan_col1_src), [`scan_col2_src`](../src/background_contact.asm#L264) [`$53B5`](reference/modules/background_contact.md#scan_col2_src) | background contact masks | `$523C`, `$5327`, `$5347`, `$536F` |

## 10. Findings

| Finding | Evidence |
|---|---|
| The program has five `JMP (ind)`. Only two can run: the IRQ dispatch, and `JMP (io1_dummy)` in [`update_high_score`](../src/score.asm#L65) after a failed protection check. The other three are never reached. | Code |
| The music and effect players dispatch commands through a self-modified `BCC` into a table of `JMP`; there is no `JMP (ind)` in the sound code. | Code |
| The action states and the keys use compare chains, not tables. | Code |
| [`irq_vector`](../src/cold_start.asm#L31) shares its two bytes with the operand of an instruction of [`cold_start`](../src/cold_start.asm#L22). | Code |

## 11. Still open

- Nothing about the dispatch is open. The meaning of each room handler and each action state is in the reference entries of the handlers.
