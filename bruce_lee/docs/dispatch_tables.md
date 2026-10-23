# Bruce Lee: how the program dispatches

Bruce Lee often selects the next piece of code from data. The raster interrupt selects the handler of the current screen. Each of the 20 rooms selects its own setup and its own logic. Actions in progress, keys and sound commands also select code. The program uses a different method for each of these places.

This page explains the methods, why each method fits its place, and how to read each one by hand. The decode entry by entry of every table is in [the table reference](reference/tables.md).

**Conventions.**
- Addresses are C64 addresses. Names are the names of the knowledge.
- A *jump table* is a row of `JMP abs` instructions. An *RTS table* is a row of words that each hold the target minus 1. The code pushes the word and executes `RTS`. A *compare chain* is a series of `CMP #` and a branch that selects a handler by a value. A *self-modified branch* is a `BCC` whose offset the code writes just before it executes it.
- A *pass* is one run of `main_loop`. A *frame* is one raster interrupt at the bottom of the screen.
- **Observed** marks a fact that a run showed. **Code** marks a fact from the code only. **Conclusion** marks an interpretation.

## How it works

The program has six kinds of dispatch. Each one sits where its form is the cheapest or the simplest for the data that selects it.

| Kind | Where | Selected by | Why this form |
|---|---|---|---|
| CPU vectors | `$FFFA-$FFFF` in RAM | the CPU | the game removes the KERNAL ROM from the memory map |
| One `JMP (ind)` through a variable | `irq_dispatch` | `irq_vector` | each handler names the next one |
| RTS tables | `room_init_handlers`, `room_frame_handlers` | `room` * 2 | 20 rooms, a dense index 0-19 |
| Compare chains | the action states, the keys | `actor_state`,X or `key_code` | a few sparse values, long handlers |
| Self-modified branch into a jump table | the music player, the three effect players | bits of the command byte | small, no vector, no stack |
| Jump tables called by address | the music player entry points | the caller | a fixed interface to a separate player |

The program has no other form of computed jump. **Code**

**Five `JMP (ind)`, and only two can run.** The program has five indirect jumps. Only two can execute: the IRQ dispatch, and `JMP (io1_dummy)` in `update_high_score` after a failed protection check. The other three are never reached. **Code**

**The sound code has no `JMP (ind)`.** The music player and the three effect players dispatch their commands through a self-modified `BCC` into a table of `JMP`. **Code**

**The action states and the keys use compare chains, not tables.** **Code**

### CPU vectors

The game removes the KERNAL ROM from the memory map (`$01` = `$35`). Thus the CPU reads its vectors from the RAM under the ROM, at [`hw_nmi_vector` `$FFFA`](../src/irq/hardware_vectors.asm#L7). NMI and RESET both point to [`nmi_entry` `$1116`](../src/irq/interrupt_entry.asm#L25), which is a single `RTI`, so the RESTORE key does nothing. IRQ points to `irq_entry`. The entries are in [the table reference](reference/tables.md#hw_nmi_vector). **Code**

### The IRQ vector chain

All interrupts are raster interrupts, and each screen needs a different handler at a different raster line. The program does not keep a table of handlers. Instead each handler stores the address of the next handler in a variable and sets the raster line where that handler runs. The full timing of the chain is on [interrupts.md](interrupts.md).

[`irq_entry` `$1103`](../src/irq/interrupt_entry.asm#L10) pushes A, X and Y. It tests the B flag of the stacked status with `AND #$00`, so the branch to `JMP (io1_dummy)` at `$1110` is never taken. Then [`irq_dispatch` `$1113`](../src/irq/interrupt_entry.asm#L22) does `JMP (irq_vector)`. Each handler ends with `PLA`/`TAY`/`PLA`/`TAX`/`PLA`/`RTI`. **Code**

**`irq_vector` shares its two bytes with an instruction of the cold start.** In the program image, [`irq_vector` `$0408`](../src/game/cold_start.asm#L31) and `irq_vector_hi` hold `$29 $EF`: the opcode and the operand of the `AND #$EF` in `cold_start`. The instruction runs once, and then the bytes are only a vector. Every screen setup stores a handler before it enables the raster interrupt, so the vector never holds the instruction bytes when an interrupt comes. **Code**

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

These routines write `irq_vector`:

| Writer | Next handler | Raster line |
|---|---|---|
| `show_title_screen`, `game_over` | `irq_title_frame` | `$FD` |
| `irq_title_frame` | `irq_title_split` | `$82` |
| `irq_title_split` | `irq_title_frame` | `$FD` |
| `show_player_screen` | `irq_player_screen`, which stays installed and sets line `$63` again | `$63` |
| `init_game_irq` | `irq_game_bottom` | `$FD` |
| `irq_game_bottom` | `irq_game_playfield` | `$40` |
| `irq_game_playfield` | `irq_game_colour_split` | `raster_split_lines` [0] |
| `irq_chain_to_bottom` | `irq_game_bottom` | `$FD` |

On the game screen the colour splits form a short list. [`irq_arm_next_split` `$4953`](../src/irq/game_irq.asm#L89) sets the next raster line from `raster_split_lines`. The value `$FD` ends the list, and then [`irq_chain_to_bottom` `$4975`](../src/irq/game_irq.asm#L108) stores `irq_game_bottom` in the vector again. For the other split lines `irq_game_colour_split` stays the handler. **Code**

### The room handlers: two RTS tables

Each of the 20 rooms has its own setup, for example the trapdoor counters, the moving ledges or the wizard. Each room also has its own logic on each pass, for example blinking lanterns, opening passages or the fireballs. The room number is a dense index from 0 to 19, so a table is the natural form. The program uses two RTS tables, both indexed by `room` * 2.

1. **The init handler runs once per room.** At the end of `draw_room`, `setup_room_lanterns_and_init` draws the lanterns and then continues directly into [`room_init_dispatch` `$33BD`](../src/room/lantern_pickup.asm#L136). It pushes the high byte and then the low byte of the word from `room_init_handlers`, and executes `RTS`. The handler's own `RTS` returns to `draw_room`. **Code**
2. **The frame handler runs on each pass.** `main_loop` calls [`run_room_frame_handler` `$3A6F`](../src/room/passage_open.asm#L18), which dispatches through `room_frame_handlers` in the same way. `draw_room` also ends with `JMP run_room_frame_handler`, so the frame handler runs once before the first pass and returns to the caller of `draw_room`. **Code**

The program uses `PHA`/`PHA`/`RTS` and not `JMP (ind)` for two reasons. The push needs no vector in memory. The handler returns with its own `RTS` directly to the caller of the dispatcher. **Conclusion**

To read an RTS table, add 1 to each word. The decoded tables are [`room_init_handlers`](reference/tables.md#room_init_handlers) and [`room_frame_handlers`](reference/tables.md#room_frame_handlers). Two things in them are easy to miss:

- **One init handler serves five rooms.** Rooms 0, 2, 6, 10 and 11 need no setup. Their entries all point to `room_init_none`, which is a single `RTS`. Every other room has its own init handler. **Code**
- **The frame handlers are in room order in memory, except room 18.** The handler of the wizard room, `room18_frame`, lies between the handlers of rooms 11 and 12, in its own source file `wizard_room.asm`. **Code**

The `RTS` of `room_init_dispatch` makes static analyzers report many false jump targets. **Code**

[rooms_catalogue.md](rooms_catalogue.md) describes each room handler, room by room.

### Compare chains: the action states

An actor in a timed action must continue that action on each step until its timer is 0. Examples of timed actions are a jump, a flying kick and a punch. [`actor_action_step` `$1C5B`](../src/actor/actor_step.asm#L21) runs one step of actor X. At `actor_check_timer`, a nonzero `actor_timer`,X jumps to [`actor_continue_action` `$2008`](../src/actor/actor_timed_actions.asm#L14). With a zero timer, the code continues at `actor_read_input`. It chooses a new action from the joystick with a chain of bit tests and no table. **Code**

`actor_continue_action` stores the timer in `temp_y` and compares `actor_state`,X with one state after the other. The code of each handler follows its compare directly. The chain continues through three source files: `actor_timed_actions.asm`, `enemy_ai_states.asm` and `actor_hit_states.asm`. The table gives the order of the compares. The reference does not give this order.

| Order | Compare at | State | Handler |
|---|---|---|---|
| 1 | `actor_continue_action` | `$05` | jump up |
| 2 | `act_check_kick_left` | `$0C` | flying kick left |
| 3 | `act_check_kick_right` | `$0D` | flying kick right |
| 4 | `act_check_jump_left` | `$06` | jump left |
| 5 | `act_check_jump_right` | `$07` | jump right |
| 6 | `act_check_dying` | `$19` | dying, at the end `lose_fall` |
| 7 | `act_check_ride` | `$17` | ride |
| 8 | `act_check_yamo_appear` | `$10` | Yamo appears |
| 9 | `act_check_punch` | `$11` | punch |
| 10 | `act_check_ninja_strike` | `$16` | Ninja strike |
| 11 | `act_check_ai_chase` | `$14` | AI chase: `ai_chase` |
| 12 | `act_check_ai_back_off` | `$15` | AI back off |
| 13 | `act_check_yamo_pose` | `$12` | Yamo pose: only the timer runs |
| 14 | `act_check_recoil` | `$0F` | recoil |
| 15 | `act_check_knocked_down` | `$13` | knocked down |
| 16 | `act_check_wall_bump` | `$18` | wall bump |
| - | `actor_continue_state` | any other (0, `$1B`) | the state stays, the timer counts down |

Each handler ends in [`actor_continue_state` `$24F4`](../src/actor/actor_hit_states.asm#L143) or in a setter that ends the action. `actor_continue_state` sets the state to A and the timer to `temp_y` - 1. **Code**

The state values are sparse (`$05` to `$19`, 16 of them in use), and each handler is long inline code. A table would need 21 entries for the range and a jump to code that is already in line. **Conclusion** The actions themselves are on [actors.md](actors.md).

### Compare chains: the keys

The keys work the same way. [`scan_keyboard` `$139E`](../src/input/keyboard_scan.asm#L24) puts the code of a new key in `key_code`. Bit 7 is the shift bit. Three places compare the code with the few keys that they accept. The game keys are also on [main_loop.md](main_loop.md).

[`handle_game_keys` `$1B29`](../src/game/status_and_keys.asm#L57) runs on each pass of a game, not in the demo. It sets `key_scan_mode` = 1, so `scan_keyboard` decodes only these four keys. The compare removes the shift bit first. **Code**

| Key | Code | Compare at | Action |
|---|---|---|---|
| F1 | `$04` | `handle_game_keys_new_key` | `restart_to_title` |
| S | `$0D` | `handle_game_keys_check_s` | toggle `title_music_off`, clear `title_music_skip_count` |
| SPACE | `$3C` | `handle_game_keys_check_space` | `handle_game_keys_pause`, then `toggle_pause` |
| V | `$1F` | `handle_game_keys_check_space` | `toggle_credit_line` |

Because only these four keys reach the chain, the `RTS` after the last compare never runs. **Code**

[`title_menu_loop` `$08B1`](../src/game/title_menu.asm#L14) runs on each pass of the title menu and decodes every key. It first jumps to `title_menu_handedness_keys`, which compares the code *with* the shift bit, so L and shift-L are different keys. Then [`title_menu_function_keys` `$08D2`](../src/game/title_menu.asm#L29) removes the shift bit and compares again. **Code**

| Key | Code | Action |
|---|---|---|
| L | `$2A` | `title_set_joy1_left_handed` |
| shift-L | `$AA` | `title_set_joy2_left_handed` |
| R | `$11` | `title_set_joy1_right_handed` |
| shift-R | `$91` | `title_set_joy2_right_handed` |
| F7 | `$03` | `title_menu_start_game` |
| F5 | `$06` | `title_menu_toggle_opponent` |
| F3 | `$05` | `title_menu_toggle_players` |

In the demo, [`check_demo_abort` `$19B8`](../src/game/pause_status_line.asm#L7) runs on each pass. Fire on joystick port 1, or the key F1 (`$04`), goes to `demo_abort_to_title`. It waits until the player releases fire, waits 6 frames and jumps to `restart_to_title`. **Code**

### Self-modified branches: the music and effect commands

The sound players read a stream of command bytes, and each command byte selects a handler. They do not use `JMP (ind)` or the stack. Each player does these steps:

1. It reads a branch offset from a table, with the command byte as the index.
2. It writes the offset into the operand of a `BCC`.
3. It clears the carry and executes the branch.

The branch lands on one `JMP` of a jump table right after it. The offsets are multiples of 3, the size of a `JMP`. The format of the streams is on [sound_music.md](sound_music.md). **Code**

**The music player.** [`music_voice_dispatch` `$E5D7`](../src/music/music_player_e38c.asm#L366) takes bits 4-6 of the command byte as the index into `music_cmd_offsets`. It stores the offset in `music_cmd_offset`, the operand of the `BCC` at [`music_cmd_branch` `$E5E6`](../src/music/music_player_e38c.asm#L377), and the branch lands in `music_cmd_jumps`. The decoded jump table is [`music_cmd_jumps`](reference/tables.md#music_cmd_jumps). **Code**

- **The commands `$F0-$FE` jump to the code after the table.** Group 7 has the offset `$15`, which lands on the first byte after the seven `JMP`, the start of `music_cmd_length`. So `$Fx` is a second note length command, the same as `$8x`. **Code**
- **`$FF` never reaches the dispatch.** `music_voice_read_command` handles it first: it ends the song. **Code**
- **The program uses only half of the offset table.** `music_cmd_offsets` has 17 entries (`$00` to `$30` in steps of 3). Bits 4-6 give only 0-7, so the program never reads entries 8-16. **Code**
- **The branch offset in the image depends on the release.** The SAEGER image holds the offset `$00` in the branch, a value that a run of the game left there before somebody saved the image. TBC and DC hold `$FE`, a `BCC` to itself, as before any run. The switch `RUN_STATE` gives the SAEGER value. The player writes the offset before each use, so the value does not matter. **Code**

**The effect players.** Each of the three effect players reads the command byte (0-7). It stores `sfx_cmd_offsets` [command] in its own branch operand. In the voice 1 player, [`sfx_voice1_update` `$EB03`](../src/sfx/sfx_voice1.asm#L19) does this. The three players are identical apart from the SID registers. Thus they have three jump tables with the same layout. The reference decodes them as [`sfx_voice1_cmd_jumps`](reference/tables.md#sfx_voice1_cmd_jumps), `sfx_voice2_cmd_jumps` and `sfx_voice3_cmd_jumps`. **Code**

- **Commands 5 and 6 are the same.** Both `JMP` go to the "note, pulse, control" handler. **Code**
- **The players never read entries 8-13 of the offset table.** `sfx_cmd_offsets` has 14 entries. Entries 8-13 would land past the jump tables, and no stream uses them. **Code**
- **The image holds `$FE` in all three branches**, a `BCC` to itself, in every release. The player writes the offset before each use. **Code**

`sfx_stream_table` (index = effect * 2) is an address table, not a jump table: it gives the start of each effect stream. Its 15 entries are in [the table reference](reference/tables.md#sfx_stream_table). **Code**

### Jump tables called by address: the music player entry points

The music player is a separate block at `$E000` and `$E300`. The game calls it only at fixed addresses, so the player starts with jump tables. [`music_api_stop` `$E000`](../src/music/music_player_state.asm#L7) holds three `JMP`: stop, start the playlist and play one frame. The game uses only these three.

The first two jump to the internal jump table at [`music_jump_stop` `$E300`](../src/music/music_player.asm#L7): stop, start the current song and start the playlist. Inside the player, `music_start_song_x` also jumps to `music_jump_start_song`, the second entry of the internal table. [The table reference](reference/tables.md#music_api_stop) decodes the entries. **Code**

### Jumps that belong to the copy protection

The other computed jumps are all parts of the copy protection, which [protection.md](protection.md) explains. **Code**

- **`JMP (io1_dummy)` in [`update_high_score` `$31A1`](../src/game/score.asm#L86).** It runs only when three protection key pairs are equal. It jumps through `$DE00`, the open I/O area, and the program crashes.
- **The `RTS` at `$0080`.** [`cold_start` `$0440`](../src/game/cold_start.asm#L68) does `JSR $0080` once at the start, and [`build_masks_done` `$517B`](../src/actor/frame_builder.asm#L76) ends `build_contact_masks` with `JMP $0080`. Both reach the `RTS` that the loader leaves at `$0080`. The second returns to `cold_start`. After `init_game_variables` clears the zero page, `$0080` is `frame_count_256`.
- **A planted `TXS`.** After a failed protection check, `actor_play_step_sound` writes `$9A` (`TXS`) over the first opcode of `random_byte`, and over the `CLC` at `step_sound_crash_point` with X = 4. When that code runs, `TXS` copies X into the stack pointer.

The switch `PROTECTION` = 0 (the default build) removes these jumps from the program:

- The `JSR $0080` becomes `NOP`.
- The `JMP $0080` becomes `RTS`.
- The `JMP (io1_dummy)` becomes a plain `JMP`.
- The program skips the two checks that plant `TXS`. **Code**

The three remaining indirect jumps are never reached. `JMP (io1_dummy)` at `$1110` in `irq_entry` is behind the B flag test that is always false. `unused_jump_reset_vector` (`JMP (hw_reset_vector)`, which would reach `nmi_entry`) and `unused_jump_zero_vector` (`JMP ($0000)`) follow `nmi_entry`, and no code jumps to them. **Code**

### Self-modified operands that are not jumps

For completeness, the program also writes the address operand of these instructions at run time. They read or write data, and none of them changes the flow of the program. **Code**

| Purpose | Operands | Writer |
|---|---|---|
| music stream read (`LDA abs`) | `music_fetch_voice0_src`, `music_fetch_voice1_src`, `music_fetch_voice2_src` | `music_set_voice_pointers`, `music_read_byte` |
| protection key read in `spawn_yamo` | `spawn_yamo_prot_key_lo`, `spawn_yamo_prot_pair_lo` | `actor_play_step_sound` |
| protection key read in `main_loop_protection_check` | `main_loop_prot_key_lo`, `main_loop_prot_pair_lo` | `actor_play_step_sound` |
| spawn timer reload | `reset_yamo_timer_src`, `reset_ninja_timer_src` | the spawn code at `$0D4B` and `$0D7B` |
| sprite frame copy | `copy_sprite_frame_narrow_src`, `copy_sprite_frame_wide_src_a`, `copy_sprite_frame_wide_src_b` | the sprite code |
| animated characters | `animate_scrolling_chars_src` | `animate_scrolling_chars` |
| background contact masks | `shift_mask_copy_src`, `scan_col0_src`, `scan_col1_src`, `scan_col2_src` | the code at `$523C`, `$5327`, `$5347` and `$536F` |

## Worked examples

Each example decodes bytes of the SAEGER image by hand.

### A CPU vector

The six bytes at `$FFFA` are `16 11 16 11 03 11`. Read as three little-endian words, they give NMI = `$1116`, RESET = `$1116` and IRQ = `$1103`. The byte at `$1116` is `$40`, an `RTI`. **Code**

### The IRQ entry

The bytes at `$1103` are `48 8A 48 98 48 BA BD 04 01 29 00 F0 03 6C 00 DE 6C 08 04`:

1. `48 8A 48 98 48`: `PHA`, `TXA`, `PHA`, `TYA`, `PHA`.
2. `BA BD 04 01`: `TSX`, `LDA $0104,X`, the stacked status.
3. `29 00 F0 03`: `AND #$00`, `BEQ +3`. The result is always 0, so the branch is always taken.
4. `6C 00 DE`: `JMP ($DE00)`, skipped.
5. `6C 08 04`: `JMP ($0408)`, through `irq_vector`.

The two bytes at `$0408` are `29 EF`. As an instruction they are the `AND #$EF` of the cold start. As a vector they point to `$EF29`. No interrupt uses that address, because a screen setup stores a handler first. **Code**

### An RTS table entry

The first four bytes of `room_init_handlers` at `$4E9C` are `F4 33 F5 33`. For room 0 the word is `$33F4`. `room_init_dispatch` pushes `$33`, then `$F4`. `RTS` pulls `$33F4` and adds 1, so the CPU continues at `$33F5`, `room_init_none`, which is a single `RTS`. For room 1 the word is `$33F5`, and the CPU continues at `$33F6`, `room01_init`, one byte after `room_init_none`. **Code**

### A compare chain

Bruce punches: `actor_state` = `$11` and `actor_timer` = 4. `actor_check_timer` sees a nonzero timer and jumps to `actor_continue_action`. The value fails the compares with `$05`, `$0C`, `$0D`, `$06`, `$07`, `$19`, `$17` and `$10`, and matches the ninth compare at `act_check_punch`. The punch code runs, and `actor_continue_state` writes the state back with the timer 3. **Code**

### A self-modified branch

The music bytes at `$E5D7` are `A8 4A 4A 4A 4A 29 07 AA BD D6 E2 8D E7 E5 18 90 00 4C FD E5`. Take the command `$C3` (pulse width):

1. `A8`: `TAY` keeps the command.
2. `4A 4A 4A 4A 29 07`: four `LSR` and `AND #$07` give bits 4-6, here 4.
3. `AA BD D6 E2`: `TAX`, `LDA $E2D6,X`. The offset table at `$E2D6` starts `00 03 06 09 0C`, so A = `$0C`.
4. `8D E7 E5 18`: `STA $E5E7`, the operand of the branch, and `CLC`.
5. `90 0C`: `BCC` to `$E5E8` + `$0C` = `$E5F4`, the fifth `JMP` of `music_cmd_jumps`, which goes to `music_cmd_pulse_width`.

The effect players work the same way. In the voice 1 player the bytes `BD 03 EC 8D 39 EB 18 90 FE` load from `sfx_cmd_offsets` at `$EC03` (`00 03 06 09 ...`), store at `$EB39` and branch. Command 3 gives the offset `$09`, so the branch lands at `$EB3A` + `$09` = `$EB43`, the `JMP` to `sfx_voice1_cmd_note_adsr_control`. **Code**

### A jump table called by address

The nine bytes at `$E000` are `4C 00 E3 4C 06 E3 4C 9E E4`: `JMP $E300`, `JMP $E306` and `JMP $E49E`. So a `JSR $E003` (start the playlist) continues at `$E306`, the third entry of the internal table, and from there to `music_start_playlist`. **Code**

## Still open

- How many false jump targets the `RTS` dispatch gives a static analyzer. Earlier analysis notes said that the analysis removed 36 of them, but those notes are no longer in the project. A new pass of c64-static-analysis can count them again.
